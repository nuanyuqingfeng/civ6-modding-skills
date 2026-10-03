#!/usr/bin/env node
// FireTuner 线协议客户端（Python 不可用时的等价入口）。
// 与 scripts/tuner_exec.py 同协议、同语义：持久帧缓冲、每命令唯一结束标记、
// 迟帧重同步、自动补齐结束标记。协议细节见 SKILL.md。
//
// 用法：
//   node tuner_node.js check
//   node tuner_node.js exec --context gamecore|ingame [--state 名字|索引] --code <Lua>
//   node tuner_node.js exec --state InGame --file <Lua 文件> [--timeout 秒]
//
// 退出码：0 成功；1 连接失败或状态缺失；2 Lua 报错；3 超时；4 连接被对端关闭。

const net = require("net");
const fs = require("fs");

const HOST = "127.0.0.1";
const PORT = 4318;
const SENTINEL = "---END---";
const MAX_FRAME = 16 * 1024 * 1024;

let nonce = 0;

// 连接断开时把所有等待者按失败唤醒：调用方据此区分「读超时」与「对端关闭」，
// null 不会被当成一帧继续解包。
function failWaiters(sock, reason) {
  const ws = sock.waiters.splice(0);
  for (const w of ws) {
    clearTimeout(w.timer);
    w.reject(new Error(reason));
  }
}

function createConn(host, port) {
  return new Promise((resolve, reject) => {
    const sock = net.createConnection({ host, port });
    sock.buf = Buffer.alloc(0);
    sock.frames = [];
    sock.waiters = [];
    // 上一条命令超时后遗留的结束标记：下一条命令先等它到达并整段丢弃，
    // 否则迟到的输出行会被下一条命令当成自己的输出。
    sock.pendingToken = null;
    sock.on("data", (chunk) => {
      sock.buf = Buffer.concat([sock.buf, chunk]);
      while (sock.buf.length >= 8) {
        const len = sock.buf.readInt32LE(0);
        if (len < 0 || len > MAX_FRAME) {
          failWaiters(sock, "closed");
          return;
        }
        if (sock.buf.length < 8 + len) break;
        const tag = sock.buf.readInt32LE(4);
        const payload = sock.buf.subarray(8, 8 + len).toString("utf8").replace(/\0+$/, "");
        sock.buf = sock.buf.subarray(8 + len);
        const w = sock.waiters.shift();
        if (w) { clearTimeout(w.timer); w.resolve({ tag, payload }); }
        else sock.frames.push({ tag, payload });
      }
    });
    sock.on("error", (e) => { failWaiters(sock, "closed"); reject(e); });
    sock.on("close", () => failWaiters(sock, "closed"));
    sock.on("connect", () => resolve(sock));
  });
}

// 宽容读：读超时与对端关闭都返回 null（握手期探测用）。
function nextFrame(sock, timeoutMs) {
  if (sock.frames.length) return Promise.resolve(sock.frames.shift());
  return new Promise((resolve) => {
    const w = {
      timer: null,
      resolve: (f) => { clearTimeout(w.timer); resolve(f); },
      reject: () => { clearTimeout(w.timer); resolve(null); },
    };
    w.timer = setTimeout(() => {
      const i = sock.waiters.indexOf(w);
      if (i >= 0) sock.waiters.splice(i, 1);
      resolve(null);
    }, timeoutMs);
    sock.waiters.push(w);
  });
}

// 严格读：读超时抛 Error("timeout")，对端关闭抛 Error("closed")。
// 不足一帧的残字节留在缓冲里，任何一次读超时都不会让后续帧错位。
function readFrame(sock, timeoutMs) {
  if (sock.frames.length) return Promise.resolve(sock.frames.shift());
  return new Promise((resolve, reject) => {
    const w = {
      timer: null,
      resolve: (f) => { clearTimeout(w.timer); resolve(f); },
      reject,
    };
    w.timer = setTimeout(() => {
      const i = sock.waiters.indexOf(w);
      if (i >= 0) sock.waiters.splice(i, 1);
      reject(new Error("timeout"));
    }, timeoutMs);
    sock.waiters.push(w);
  });
}

function sendMsg(sock, tag, payload) {
  const data = Buffer.concat([Buffer.from(payload, "utf8"), Buffer.from([0])]);
  const header = Buffer.alloc(8);
  header.writeInt32LE(data.length, 0);
  header.writeInt32LE(tag, 4);
  sock.write(Buffer.concat([header, data]));
}

// print 帧取净文本；非 print 帧返回 null。
function frameText(payload) {
  if (!payload.startsWith("O")) return null;
  const sep = payload.indexOf(": ", 2);
  const text = sep >= 0 ? payload.slice(sep + 2) : payload.replace(/^O\0*/, "").trim();
  return text.trim();
}

async function handshake(sock, timeoutMs = 8000) {
  sock.frames.length = 0;
  sendMsg(sock, 4, "APP:");
  const app = await nextFrame(sock, timeoutMs);
  sendMsg(sock, 4, "LSQ:");
  const lsq = await nextFrame(sock, timeoutMs);
  const states = {};
  if (lsq) {
    const entries = lsq.payload.split("\0").map((s) => s.trim()).filter(Boolean);
    let i = 0;
    while (i + 1 < entries.length) {
      const idx = parseInt(entries[i], 10);
      if (!isNaN(idx)) { states[entries[i + 1]] = idx; i += 2; }
      else i += 1;
    }
  }
  return { identity: app ? app.payload : "", states };
}

// 上一条命令超时后，先等它的结束标记到达并把这段输出整段丢弃。
// 标记唯一，因此只有那个特定标记才算对齐；始终等不到就按连接失效处理，
// 避免把上一条命令的输出错记到本条命令名下。
async function resync(sock, timeoutMs) {
  const stale = sock.pendingToken;
  if (stale === null) return;
  sock.pendingToken = null;
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const remain = deadline - Date.now();
    if (remain <= 0) throw new Error("closed");
    let msg;
    try {
      msg = await readFrame(sock, remain);
    } catch (e) {
      if (e.message === "timeout") throw new Error("closed");
      throw e;
    }
    if (frameText(msg.payload) === stale) return;
  }
}

async function execute(sock, stateIndex, code, timeoutMs = 10000) {
  const token = SENTINEL + (++nonce);
  await resync(sock, timeoutMs);
  const full = code + (/[^\n]/.test(code) || !code ? (code.includes("\n") ? "\n" : " ") : "") +
    'print("' + token + '")';
  sock.frames.length = 0;
  sendMsg(sock, 3, "CMD:" + stateIndex + ":" + full);

  const lines = [];
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const remain = deadline - Date.now();
    if (remain <= 0) {
      sock.pendingToken = token;
      const e = new Error("timeout");
      e.lines = lines;
      throw e;
    }
    let msg;
    try {
      msg = await readFrame(sock, remain);
    } catch (err) {
      if (err.message === "timeout") {
        sock.pendingToken = token;
        const e = new Error("timeout");
        e.lines = lines;
        throw e;
      }
      throw err;
    }
    if (msg.payload.startsWith("ERR:")) {
      const e = new Error(msg.payload);
      e.lua = true;
      e.lines = lines;
      throw e;
    }
    const text = frameText(msg.payload);
    if (text !== null) {
      if (text === token) break;
      // 迟到的结束帧（本命令之外的一切 ---END--- 变体）丢弃，不计入本次输出
      if (text.startsWith(SENTINEL)) continue;
      lines.push(text);
    }
  }
  return lines;
}

function resolveState(states, key) {
  if (key === null || key === undefined) return null;
  if (Object.prototype.hasOwnProperty.call(states, key)) return states[key];
  if (/^\d+$/.test(key)) {
    const idx = parseInt(key, 10);
    if (Object.values(states).includes(idx)) return idx;
  }
  return null;
}

function parseArgs(argv) {
  const out = { cmd: argv[0] || null };
  for (let i = 1; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--context") out.context = argv[++i];
    else if (a === "--state") out.state = argv[++i];
    else if (a === "--code") out.code = argv[++i];
    else if (a === "--file") out.file = argv[++i];
    else if (a === "--timeout") out.timeout = parseFloat(argv[++i]);
    else if (a === "--host") out.host = argv[++i];
    else if (a === "--port") out.port = parseInt(argv[++i], 10);
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const host = args.host || HOST;
  const port = args.port || PORT;

  let sock;
  try {
    sock = await createConn(host, port);
  } catch (e) {
    console.error("[FAIL] 无法连接 " + host + ":" + port + " —— " + e.message);
    console.error("检查项：游戏是否已启动？EnableTuner 是否开启？FireTuner GUI 是否已关闭？");
    return 1;
  }

  try {
    const { identity, states } = await handshake(sock);
    if (args.cmd === "check") {
      console.log("[OK] 已连接：" + identity);
      for (const [name, idx] of Object.entries(states).sort((a, b) => a[1] - b[1])) {
        console.log("  [" + idx + "] " + name);
      }
      if (states.GameCore_Tuner !== undefined && states.InGame !== undefined) {
        console.log("[OK] 对局进行中（gamecore=" + states.GameCore_Tuner +
                    ", ingame=" + states.InGame + "），可以执行测试。");
        return 0;
      }
      console.log("[WAIT] 已连上但缺少 GameCore_Tuner/InGame —— 当前在主菜单，请读档进入对局。");
      return 1;
    }

    if (args.cmd !== "exec") {
      console.error("用法：tuner_node.cjs check | exec --context gamecore|ingame "
                  + "[--state 名字|索引] --code <Lua> | --file <路径> [--timeout 秒]");
      return 1;
    }

    let code = args.code;
    if (args.file) code = fs.readFileSync(args.file, "utf8").replace(/^\uFEFF/, "");
    if (code === undefined) {
      console.error("[FAIL] 需要 --code 或 --file");
      return 1;
    }

    const key = args.state || (args.context === "gamecore" || !args.context
      ? "GameCore_Tuner" : "InGame");
    const idx = resolveState(states, key);
    if (idx === null) {
      console.error("[FAIL] 未找到状态 " + key + "。若在主菜单请先读档进对局。");
      return 1;
    }

    const timeoutMs = (args.timeout || 10) * 1000;
    const lines = await execute(sock, idx, code, timeoutMs);
    for (const ln of lines) console.log(ln);
    return 0;
  } catch (e) {
    for (const ln of e.lines || []) console.log(ln);
    if (e.lua) {
      console.error("[LUA ERROR] " + e.message);
      return 2;
    }
    if (e.message === "timeout") {
      console.error("[TIMEOUT] 未收到哨兵");
      return 3;
    }
    console.error("[CLOSED] " + e.message);
    return 4;
  } finally {
    sock.destroy();
  }
}

main().then((rc) => process.exit(rc));
