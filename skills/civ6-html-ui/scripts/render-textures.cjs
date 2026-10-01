#!/usr/bin/env node
'use strict';
// Local authoring renderer: Node >=22, Edge/Chromium, no npm packages.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawn } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

function options(argv) {
  const opts = { replace: false };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help') { opts.help = true; continue; }
    if (arg === '--replace') { opts.replace = true; continue; }
    if (!['--html', '--out', '--browser'].includes(arg) || !argv[i + 1] || argv[i + 1].startsWith('--')) {
      throw new Error(`Invalid argument: ${arg}`);
    }
    opts[arg.slice(2)] = path.resolve(argv[++i]);
  }
  if (opts.help) return opts;
  for (const key of ['html', 'out', 'browser']) if (!opts[key]) throw new Error(`Missing --${key}`);
  for (const key of ['html', 'browser']) if (!fs.statSync(opts[key]).isFile()) throw new Error(`Not a file: ${opts[key]}`);
  if (fs.existsSync(opts.out) && (!fs.statSync(opts.out).isDirectory() || fs.lstatSync(opts.out).isSymbolicLink())) {
    throw new Error('Output must be a real directory, not a symlink');
  }
  if (Number(process.versions.node.split('.')[0]) < 22 || typeof WebSocket === 'undefined') throw new Error('Node.js 22+ with native WebSocket is required');
  return opts;
}

function validateSpecs(specs) {
  if (!specs || typeof specs !== 'object' || Array.isArray(specs) || !Object.keys(specs).length) {
    throw new Error('window.textureSpecs must be a nonempty object');
  }
  const names = new Set();
  for (const [name, size] of Object.entries(specs)) {
    if (!/^UI_[A-Za-z0-9_]+$/.test(name) || name.trim() !== name || names.has(name.toLowerCase())) throw new Error(`Invalid/duplicate texture: ${name}`);
    names.add(name.toLowerCase());
    if (!Array.isArray(size) || size.length !== 2 || size.some(v => !Number.isInteger(v) || v < 1 || v > 8192)) {
      throw new Error(`Invalid dimensions for ${name}: ${JSON.stringify(size)}`);
    }
  }
}

async function render(opts) {
  const tempRoot = fs.realpathSync(os.tmpdir());
  const profile = fs.mkdtempSync(path.join(tempRoot, 'civ6-html-ui-'));
  let proc, socket, send, exited = false, spawnError;
  const pending = new Map(), failures = [];
  let seq = 0;
  try {
    proc = spawn(opts.browser, ['--headless=new', '--no-first-run', '--no-default-browser-check',
      '--disable-extensions', '--disable-background-networking', '--remote-debugging-address=127.0.0.1',
      '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'],
    { windowsHide: true, stdio: 'ignore' });
    proc.on('error', error => { spawnError = error; });
    proc.on('exit', () => { exited = true; });
    let port;
    const startupDeadline = Date.now() + 20000;
    while (Date.now() < startupDeadline) {
      if (spawnError) throw spawnError;
      if (exited) throw new Error('Browser exited before opening its debugging endpoint');
      const portFile = path.join(profile, 'DevToolsActivePort');
      if (fs.existsSync(portFile)) { port = Number(fs.readFileSync(portFile, 'utf8').split('\n')[0]); break; }
      await delay(100);
    }
    if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Browser startup timed out');
    const response = await fetch(`http://127.0.0.1:${port}/json`, { signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error(`CDP listing failed: ${response.status}`);
    const target = (await response.json()).find(t => t.type === 'page');
    if (!target) throw new Error('No page target in the isolated browser');
    socket = new WebSocket(target.webSocketDebuggerUrl);
    const rejectAll = reason => {
      for (const item of pending.values()) { clearTimeout(item.timer); item.reject(reason); }
      pending.clear();
    };
    socket.addEventListener('close', () => rejectAll(new Error('CDP connection closed')));
    socket.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.id && pending.has(message.id)) {
        const item = pending.get(message.id); pending.delete(message.id); clearTimeout(item.timer);
        if (message.error) item.reject(new Error(JSON.stringify(message.error)));
        else item.resolve(message.result);
      }
      if (message.method === 'Network.loadingFailed') failures.push(message.params.errorText);
      if (message.method === 'Network.responseReceived' && message.params.response.status >= 400) {
        failures.push(`${message.params.response.status}: ${message.params.response.url}`);
      }
      if (message.method === 'Runtime.exceptionThrown') failures.push(JSON.stringify(message.params.exceptionDetails));
    });
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('CDP connection timed out')), 10000);
      socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
      socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('CDP connection error')); }, { once: true });
    });
    send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++seq;
      const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 20000);
      pending.set(id, { resolve, reject, timer });
      try { socket.send(JSON.stringify({ id, method, params })); }
      catch (error) { pending.delete(id); clearTimeout(timer); reject(error); }
    });
    const evaluate = async expression => {
      const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
      if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
      return result.result.value;
    };
    await send('Page.enable');
    await send('Runtime.enable');
    await send('Network.enable');
    await send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
    await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
    const url = pathToFileURL(opts.html); url.searchParams.set('export', '1');
    const navigation = await send('Page.navigate', { url: url.href });
    if (navigation.errorText) throw new Error(navigation.errorText);
    let ready = false;
    const readyDeadline = Date.now() + 20000;
    while (Date.now() < readyDeadline) {
      if (failures.length) throw new Error(`Page failed: ${failures.join('; ')}`);
      ready = await evaluate('document.readyState === "complete" && typeof window.renderTexture === "function"');
      if (ready) break;
      await delay(100);
    }
    if (!ready) throw new Error('HTML did not expose renderTexture before the timeout');
    const specs = await evaluate('window.textureSpecs'); validateSpecs(specs);
    fs.mkdirSync(opts.out, { recursive: true });
    for (const file of [...Object.keys(specs).map(name => `${name}.png`), 'texture_manifest.json']) {
      const destination = path.join(opts.out, file);
      if (fs.existsSync(destination)) {
        if (!opts.replace) throw new Error(`Output exists; use --replace to regenerate: ${destination}`);
        if (!fs.lstatSync(destination).isFile()) throw new Error(`Refusing non-regular output: ${destination}`);
      }
    }
    const staged = path.join(profile, 'rendered-textures');
    fs.mkdirSync(staged);
    await evaluate(`(() => { const s = document.createElement('style');
      s.textContent = '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}';
      document.head.appendChild(s); })()`);
    for (const [name, [width, height]] of Object.entries(specs)) {
      await send('Emulation.setDeviceMetricsOverride', { width: Math.max(400, width), height: Math.max(200, height), deviceScaleFactor: 1, mobile: false });
      await evaluate(`window.renderTexture(${JSON.stringify(name)})`);
      await evaluate(`(async () => {
        await document.fonts.ready;
        await Promise.all([...document.images].map(image => image.decode()));
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      })()`);
      const rect = await evaluate(`(() => {
        const element = document.querySelector('#texture'); if (!element) throw Error('Missing #texture');
        const r = element.getBoundingClientRect();
        return { x:r.x, y:r.y, width:r.width, height:r.height, dpr:devicePixelRatio };
      })()`);
      if (rect.x !== 0 || rect.y !== 0 || rect.width !== width || rect.height !== height || rect.dpr !== 1) {
        throw new Error(`Export rectangle mismatch for ${name}: ${JSON.stringify(rect)}, expected 0,0,${width},${height}, DPR=1`);
      }
      if (failures.length) throw new Error(`Asset/page errors: ${failures.join('; ')}`);
      const shot = await send('Page.captureScreenshot', {
        format: 'png', captureBeyondViewport: true, clip: { x: 0, y: 0, width, height, scale: 1 }
      });
      const png = Buffer.from(shot.data, 'base64');
      if (png.length < 24 || png.toString('hex', 0, 8) !== '89504e470d0a1a0a' || png.readUInt32BE(16) !== width || png.readUInt32BE(20) !== height) {
        throw new Error(`Screenshot dimensions invalid: ${name}`);
      }
      fs.writeFileSync(path.join(staged, `${name}.png`), png, { flag: 'wx' });
      process.stdout.write(`${name}: ${width}x${height}\n`);
    }
    // Rendering/asset failures cannot replace a subset of an earlier valid batch.
    for (const name of Object.keys(specs)) {
      const destination = path.join(opts.out, `${name}.png`);
      if (fs.existsSync(destination) && !fs.lstatSync(destination).isFile()) {
        throw new Error(`Refusing non-regular output: ${destination}`);
      }
      fs.copyFileSync(path.join(staged, `${name}.png`), destination, opts.replace ? 0 : fs.constants.COPYFILE_EXCL);
    }
    fs.writeFileSync(path.join(opts.out, 'texture_manifest.json'), JSON.stringify(specs, null, 2) + '\n', { flag: opts.replace ? 'w' : 'wx' });
    process.stdout.write(`Rendered ${Object.keys(specs).length} textures to ${opts.out}\n`);
  } finally {
    if (send && socket && socket.readyState === WebSocket.OPEN) {
      try { await send('Browser.close'); } catch { /* Browser may close before replying. */ }
    }
    if (socket) socket.close();
    if (proc && !exited && !spawnError) {
      for (let i = 0; i < 30 && !exited; i++) await delay(100);
      if (!exited) { proc.kill(); for (let i = 0; i < 20 && !exited; i++) await delay(100); }
    }
    // Delete only this run's verified direct child of the resolved temp root.
    if ((!proc || exited || spawnError) && fs.existsSync(profile)) {
      const resolved = fs.realpathSync(profile);
      if (path.dirname(resolved) === tempRoot && path.basename(resolved).startsWith('civ6-html-ui-')) {
        try { fs.rmSync(resolved, { recursive: true, maxRetries: 3, retryDelay: 100 }); }
        catch { process.stderr.write(`Browser profile remains at ${resolved}\n`); }
      }
    }
  }
}

(async () => {
  const opts = options(process.argv.slice(2));
  if (opts.help) {
    process.stdout.write('node render-textures.cjs --html design/index.html --out design/textures --browser <Edge/Chromium executable> [--replace]\n');
  } else await render(opts);
})().catch(error => { process.stderr.write(`Render failed: ${error.message}\n`); process.exitCode = 1; });
