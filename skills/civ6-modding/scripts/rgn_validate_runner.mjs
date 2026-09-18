#!/usr/bin/env node
/**
 * rgn_validate 离线执行器 v2 — 核心判定逻辑提取自 @dsh-external/dsh-rgn-tools 的
 * src/index.ts（D:\documents\Deepseek_WorkPlace\dsh-rgn-tools），仅剥离 cordis/dsh-tools 运行时依赖。
 *
 * v2 新增"实跑模式"（默认）：把基础库快照到临时文件 → 真实执行项目 SQL（两遍：先全量 DDL 再其余语句）
 * → 直接查库取定义/引用全集做比对。根治 `INSERT INTO ... SELECT '字面量' || 列 ...` 动态拼接的
 * 定义识别盲区；附带语法校验能力（缺分号/缺表等会作为执行错误报告）。
 * `--static` 回退 v1 纯文本解析路径。
 *
 * 用法: node rgn_validate_runner.mjs [目录=cwd] [文件模式=*.sql] [checkNaming=true] [--base <基础库>] [--static]
 * 依赖: Node ≥ 22（内置 node:sqlite）
 */
import { DatabaseSync } from 'node:sqlite'
import * as fs from 'node:fs'
import * as path from 'node:path'
import * as os from 'node:os'

// ─────────────────────────── CLI ───────────────────────────
const argv = process.argv.slice(2)
const flags = { base: null, staticMode: false }
const pos = []
for (let i = 0; i < argv.length; i++) {
  const a = argv[i]
  if (a === '--base') flags.base = argv[++i] ?? null
  else if (a === '--static') flags.staticMode = true
  else pos.push(a)
}
const SCRIPT_DIR = import.meta.dirname
const DEFAULT_BASE = path.resolve(SCRIPT_DIR, '..', 'database', 'DebugGameplay.sqlite')
// 基础库关键表官方列断言：参考库被手工加列时，执行期会"侥幸成功"导致校验器失明。
// 这里对高流量表做列断言；全量漂移检查见 database/scripts/audit_schema_drift.py。
const BASE_SCHEMA_ASSERTIONS = {
  DynamicModifiers: ['ModifierType', 'CollectionType', 'EffectType'],
  Modifiers: ['ModifierId', 'ModifierType', 'RunOnce', 'NewOnly', 'Permanent', 'Repeatable', 'OwnerRequirementSetId', 'SubjectRequirementSetId', 'OwnerStackLimit', 'SubjectStackLimit'],
  ModifierArguments: ['ModifierId', 'Name', 'Type', 'Value', 'Extra', 'SecondExtra'],
  Types: ['Type', 'Hash', 'Kind'],
}
const dir = pos[0]?.trim() || process.cwd()
const pattern = pos[1]?.trim() || '*.sql'
const checkNaming = pos[2] !== 'false'

// ─────────────────────── 判定启发式（与插件 src/index.ts 一致） ───────────────────────
const IDENT_RE = /^[A-Z][A-Z0-9_]*$/
const SKIP_COLS = new Set(['Kind', 'Name', 'Description', 'Icon', 'Color', 'Text', 'Value', 'Amount', 'Percent', 'Score', 'UnitType_Right', 'UnitType_Left'])
const SUBJECT_SUFFIXES = ['RGN', 'QYQXP', 'CTTH', 'CTRL', 'CCN', 'PHB']
const FREE_NAMED_PREFIXES = ['CIVILIZATION_', 'LEADER_', 'TRAIT_']

function isFreeNamedValue(value) {
  return FREE_NAMED_PREFIXES.some(p => value.startsWith(p))
}

const DEF_COLS = {
  Modifiers: 'ModifierId',
  RequirementSets: 'RequirementSetId',
  Requirements: 'RequirementId',
  LocalizedText: 'Tag',
  Properties: 'Key',
}
const SUBJECT_TABLES = new Set([
  'Types', 'Buildings', 'Units', 'Resources', 'Districts', 'Improvements', 'Projects', 'Projects_XP1',
  'GreatWorks', 'GreatWorkObjectTypes', 'GreatPeople', 'Governors', 'Beliefs', 'Civilizations', 'Leaders',
  'Traits', 'UnitAbilities', 'UnitPromotions', 'Technologies', 'Civics', 'GameModes', 'DynamicModifiers',
  'Colors', 'Notifications', 'Tags',
])
const REF_TABLES = new Set([
  'ModifierArguments', 'TraitModifiers', 'BuildingModifiers', 'TypeTags', 'RequirementArguments',
  'RequirementSetRequirements', 'UnitAbilityModifiers', 'Improvement_ValidResources',
  'Resource_ValidTerrains', 'Resource_YieldChanges', 'Resource_Harvests', 'Resource_ValidFeatures',
  'DistrictModifiers', 'Adjacency_YieldChanges', 'District_Adjacencies', 'GreatWork_YieldChanges',
  'GreatWork_ValidSubTypes', 'Project_GreatPersonPoints', 'Improvement_ValidBuildUnits',
  'Project_YieldConversions', 'ProjectCompletionModifiers', 'Players',
])

function isDefiningPosition(table, col, dcol) {
  if (DEF_COLS[table] === col) return true
  if (col === 'Type' && SUBJECT_TABLES.has(table)) return true
  if (col === dcol && !REF_TABLES.has(table)) return true
  return false
}

function defColOf(cols) {
  for (const c of cols) {
    if (SKIP_COLS.has(c)) continue
    if (/Type$/.test(c) || /Id$/.test(c) || c === 'Key' || c === 'Tag') return c
  }
  return null
}

function domainOf(col) {
  if (SKIP_COLS.has(col)) return null
  if (col === 'SubjectRequirementSetId' || col === 'OwnerRequirementSetId') return 'RequirementSetId'
  if (/Type$/.test(col) || /^Prereq/.test(col)) return 'Type'
  if (/Id$/.test(col) || col === 'Key') return col
  if (col === 'PropertyKey') return 'Key'
  if (col === 'Tag') return 'Tag'
  return null
}

function goodIdent(v) {
  return typeof v === 'string' && v !== 'NULL' && IDENT_RE.test(v.trim()) ? v.trim() : null
}

// ─────────────────────────── 通用工具 ───────────────────────────
function listSqlFiles(dir_, pattern_) {
  const files = fs.readdirSync(dir_).filter(f => {
    if (!f.toLowerCase().endsWith('.sql')) return false
    if (pattern_ === '*.sql') return true
    const re = new RegExp('^' + pattern_.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*') + '$', 'i')
    return re.test(f)
  }).sort()
  return files
}

/** 引号/注释感知的语句切分，返回 [{sql, line}]（line 为语句首行行号） */
function splitStatements(sql) {
  const out = []
  const n = sql.length
  let buf = [], startLine = 1, line = 1, started = false, i = 0
  const push = ch => {
    if (!started) { startLine = line; started = true }
    buf.push(ch)
  }
  while (i < n) {
    const c = sql[i]
    if (c === "'") { // 字符串字面量（'' 转义）
      push(c); i++
      while (i < n) {
        if (sql[i] === "'") {
          if (sql[i + 1] === "'") { push("''"); i += 2; continue }
          push("'"); i++; break
        }
        if (sql[i] === '\n') line++
        push(sql[i]); i++
      }
      continue
    }
    if (c === '-' && sql[i + 1] === '-') { // 行注释
      while (i < n && sql[i] !== '\n') { push(sql[i]); i++ }
      continue
    }
    if (c === '/' && sql[i + 1] === '*') { // 块注释
      push('/*'); i += 2
      while (i < n && !(sql[i] === '*' && sql[i + 1] === '/')) {
        if (sql[i] === '\n') line++
        push(sql[i]); i++
      }
      push('*/'); i += 2
      continue
    }
    if (c === ';') {
      const s = buf.join('').trim()
      if (s) out.push({ sql: s, line: startLine })
      buf = []; started = false; i++
      continue
    }
    if (c === '\n') line++
    push(c); i++
  }
  const s = buf.join('').trim()
  if (s) out.push({ sql: s, line: startLine })
  return out
}

/** 语句有效头部（跳过前导注释/空白），用于 DDL 分类 */
function stmtHead(stmtSql) {
  const m = stmtSql.match(/^(?:\s|--[^\n]*\n|\/\*[\s\S]*?\*\/)*([A-Za-z]+)/)
  return m ? m[1].toUpperCase() : ''
}

function schemaTables(db) {
  const map = new Map()
  let rows = []
  try {
    rows = db.prepare(`SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`).all()
  } catch { return map }
  for (const r of rows) {
    try {
      map.set(r.name, db.prepare(`PRAGMA table_info("${r.name.replace(/"/g, '""')}")`).all().map(c => c.name))
    } catch { /* 跳过异常表 */ }
  }
  return map
}

/**
 * 遍历 schema 的全部表×列，收集定义域/引用域的值集合。
 * refTablesLimit：仅对这些表收集引用列（null=不收集引用）；自定义表的非主键列视为内部载荷不检查。
 */
function collectDefsRefs(db, schema, refTablesLimit) {
  const defs = new Map(), refs = new Map(), typeValues = new Set()
  const add = (m, k, v) => {
    let s = m.get(k)
    if (!s) { s = new Set(); m.set(k, s) }
    s.add(v)
  }
  for (const [table, cols] of schema) {
    const dcol = defColOf(cols)
    const isRefTable = refTablesLimit ? refTablesLimit.has(table) : true
    for (const col of cols) {
      const roleDef = isDefiningPosition(table, col, dcol)
      const dom = domainOf(col)
      if (!roleDef && !(isRefTable && dom)) continue
      let rows = []
      try {
        rows = db.prepare(`SELECT DISTINCT "${col.replace(/"/g, '""')}" AS v FROM "${table.replace(/"/g, '""')}" WHERE "${col.replace(/"/g, '""')}" IS NOT NULL`).all()
      } catch { continue }
      for (const r of rows) {
        const v = goodIdent(r.v)
        if (!v) continue
        if (roleDef) {
          add(defs, dom, v)
          if (table === 'Types' && dom === 'Type') typeValues.add(v)
        } else if (dom) {
          add(refs, dom, v)
        }
      }
    }
  }
  return { defs, refs, typeValues }
}

// ─────────────────────────── 实跑模式 ───────────────────────────
function materializeBase(basePath, tmpPath) {
  if (basePath && fs.existsSync(basePath)) {
    try {
      const src = new DatabaseSync(basePath, { readOnly: true })
      try {
        src.exec(`VACUUM INTO '${tmpPath.replace(/'/g, "''")}'`)
        return { ok: true, how: 'vacuum-into' }
      } finally { src.close() }
    } catch {
      try { fs.copyFileSync(basePath, tmpPath); return { ok: true, how: 'file-copy' } } catch { /* fallthrough */ }
    }
  }
  return { ok: false, how: 'none' }
}

function locateInFiles(fileTexts, value) {
  const needle = `'${value}'`
  for (const ft of fileTexts) {
    const idx = ft.sql.indexOf(needle)
    if (idx >= 0) return `${ft.file}:${ft.sql.slice(0, idx).split('\n').length}`
  }
  return ''
}

function runExecMode() {
  const L = []
  if (!fs.existsSync(dir)) return `目录不存在: ${dir}`
  const files = listSqlFiles(dir, pattern)
  if (!files.length) return `目录 ${dir} 下没有匹配 ${pattern} 的 SQL 文件`

  const basePath = flags.base || DEFAULT_BASE
  const tmpPath = path.join(os.tmpdir(), `rgn_validate_work_${process.pid}_${Date.now()}.sqlite`)
  const mat = materializeBase(basePath, tmpPath)
  let db = null
  const execIssues = []
  try {
    // 游戏 SQLite 允许双引号字符串字面量（Colors_RGN 的 "COLOR_X" 写法）；node:sqlite 默认禁用，开启以对齐游戏语义
    const dqsOpts = { enableDoubleQuotedStringLiterals: true }
    db = mat.ok ? new DatabaseSync(tmpPath, dqsOpts) : new DatabaseSync(':memory:', dqsOpts)
    db.exec('PRAGMA foreign_keys = OFF') // node:sqlite 默认强制外键；游戏装载环境并不启用，校验器自己负责引用检查
    // 文本类扫描：DebugGameplay 属 gameplay 库，不含 LocalizedText；预建空表让 Text 目录获得语法校验能力
    try { db.exec('CREATE TABLE IF NOT EXISTS LocalizedText (Tag TEXT, Language TEXT, Text TEXT)') } catch { /* 已存在则忽略 */ }
    // 基线：原始 schema、原始定义/引用/Type 集
    const schemaBase = schemaTables(db)
    // 基础库 schema 断言（防参考库被手工加列后校验器失明）
    const baseSchemaWarnings = []
    for (const [t, expected] of Object.entries(BASE_SCHEMA_ASSERTIONS)) {
      const got = schemaBase.get(t)
      if (!got) { baseSchemaWarnings.push(`基础库缺表 ${t}`); continue }
      const same = got.length === expected.length && expected.every((c, i) => got[i] === c)
      if (!same) baseSchemaWarnings.push(`基础库 ${t} 列异常：[${got.join(', ')}]，官方应为 [${expected.join(', ')}]`)
    }
    const before = collectDefsRefs(db, schemaBase, schemaBase)
    const baseTypes = new Set(before.typeValues)

    // 读入项目文件全文（供静态回退定位与悬空溯源）
    const fileTexts = files.map(f => ({ file: f, sql: fs.readFileSync(path.join(dir, f), 'utf8') }))

    // 两遍执行：先跨文件全量 CREATE（自建表可能被排在前面的文件引用），再按文件序执行其余语句
    const ddl = [], rest = []
    for (const ft of fileTexts) {
      for (const st of splitStatements(ft.sql)) {
        ;(stmtHead(st.sql).startsWith('CREATE') ? ddl : rest).push({ file: ft.file, ...st })
      }
    }
    let okCount = 0
    const runStmt = st => {
      try { db.exec(st.sql); okCount++ } catch (e) {
        execIssues.push(`${st.file}:${st.line} ${String(e.message).slice(0, 100)}`)
      }
    }
    ddl.forEach(runStmt)
    // 显式列存在性预检：基础库若被污染，执行期可能"侥幸成功"；这里按实际库 schema 先拦一次
    const liveSchema = schemaTables(db)
    const insertColumnIssue = sql => {
      const m = sql.match(/^\s*INSERT\s+(?:OR\s+(?:REPLACE|IGNORE)\s+)?INTO\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)["`\]]?\s*\(([^)]*)\)/i)
      if (!m) return null
      const cols = liveSchema.get(m[1])
      if (!cols) return null
      const unknown = m[2].split(',').map(s => s.trim().replace(/^["`\[]|["`\]]$/g, '')).filter(Boolean)
        .filter(c => !cols.includes(c))
      return unknown.length ? { table: m[1], unknown, cols } : null
    }
    rest.forEach(st => {
      const bad = insertColumnIssue(st.sql)
      if (bad) {
        execIssues.push(`${st.file}:${st.line} INSERT INTO ${bad.table}: unknown column(s) ${bad.unknown.join(', ')} (table has: ${bad.cols.join(', ')})`)
        return
      }
      runStmt(st)
    })

    // 执行后：定义全集（含自定义表）、引用全集（仅基础库既有表——自定义表非主键列是内部载荷）
    const schemaAfter = schemaTables(db)
    const after = collectDefsRefs(db, schemaAfter, schemaBase)
    const defsUnion = new Set()
    for (const s of after.defs.values()) for (const v of s) defsUnion.add(v)

    // 项目新增引用 = 全部引用 − 基线引用
    const newRefDomains = []
    let newRefCount = 0
    for (const [dom, set] of after.refs) {
      const b = before.refs.get(dom)
      const fresh = [...set].filter(v => !b || !b.has(v))
      if (fresh.length) { newRefDomains.push([dom, fresh]); newRefCount += fresh.length }
    }

    const dangling = []
    for (const [dom, vals] of newRefDomains) {
      for (const v of vals) {
        if (dom === 'Tag' && v.startsWith('LOC_')) continue
        if (defsUnion.has(v)) continue
        dangling.push({ dom, value: v })
      }
    }
    dangling.sort((x, y) => x.value.localeCompare(y.value))

    // 命名规范：Types 表中项目新增的 Type
    const namingIssues = []
    if (checkNaming) {
      for (const v of after.typeValues) {
        if (baseTypes.has(v)) continue
        if (isFreeNamedValue(v)) continue
        if (v.startsWith('MOD_')) {
          namingIssues.push(`主题 Type 以 MOD_ 开头（AGENTS.md 禁止）: ${v}`)
        } else if (!SUBJECT_SUFFIXES.some(s => v.includes(`_${s}`))) {
          if (/^(MOMENT_|KIND_|PLAYER_|GAME_|GLOBAL_|STANDARD_|UNIFORM_)/.test(v)) continue
          namingIssues.push(`主题 Type 缺少 _RGN / _QYQXP / 领袖缩写后缀: ${v}`)
        }
      }
      namingIssues.sort()
    }

    // ── 报告 ──
    L.push(`═══ rgn_validate 报告（实跑模式）═══`)
    L.push(`目录: ${dir} | 文件: ${files.length} 个 | 基础库: ${mat.ok ? '已快照 ' + path.basename(basePath) : '缺失 ⚠'}${mat.ok && mat.how !== 'vacuum-into' ? '（复制回退）' : ''}`)
    if (!mat.ok) {
      // 缺基础库时若照旧输出"✅ 未发现悬空引用"，会把"只做了项目内自洽检查"误读成"引用全部闭合"
      // —— 而本库被 .gitignore 排除、新克隆的仓库里本就没有（见 SKILL.md「查询三级阶梯」L1）。
      L.push('')
      L.push('⚠⚠ 基础库缺失：未加载任何官方参考库，本次结果**仅**代表「项目文件之间的自洽性」，')
      L.push('    无法判定对原版 ID 的悬空引用。**不要把本报告当作发布前校验结论。**')
      L.push(`    期望路径: ${basePath}`)
      L.push('    修复：① 把官方 DebugGameplay 参考库放到该路径；② 或显式指定 `--base <基础库路径>`。')
      L.push('    该库为何不在仓库内、以及如何得到它，见 SKILL.md「查询三级阶梯」与 `database/README.md`。')
    }
    if (baseSchemaWarnings.length) {
      L.push(`⚠ 基础库 schema 异常（跑 database/scripts/audit_schema_drift.py 排查）:`)
      for (const w of baseSchemaWarnings) L.push(`  - ${w}`)
    }
    const defTotal = [...after.defs.values()].reduce((a, s) => a + s.size, 0)
    const newDefs = []
    for (const [dom, set] of after.defs) {
      const b = before.defs.get(dom)
      const n = [...set].filter(v => !b || !b.has(v)).length
      if (n) newDefs.push(`${dom}=${n}`)
    }
    L.push(`执行: ${okCount} 条语句成功${execIssues.length ? `，${execIssues.length} 条失败` : ''}`)
    L.push(`定义: 库内共 ${defTotal} 个标识符，其中项目新增 ${newDefs.join(', ') || '0'}`)
    L.push(`引用: 项目新增去重引用 ${newRefCount} 个，悬空 ${dangling.length} 个`)

    if (execIssues.length) {
      L.push('')
      L.push(`── 执行错误（语句级容错，已跳过）──`)
      for (const e of execIssues.slice(0, 15)) L.push(`✗ ${e}`)
      if (execIssues.length > 15) L.push(`… 还有 ${execIssues.length - 15} 条未显示`)
    }
    if (dangling.length) {
      L.push('')
      L.push('── 悬空引用（项目新增引用在整库定义域中未命中）──')
      for (const d of dangling.slice(0, 40)) {
        L.push(`⚠ [${d.dom}] ${d.value}${locateInFiles(fileTexts, d.value) ? ' — ' + locateInFiles(fileTexts, d.value) : ''}`)
      }
      if (dangling.length > 40) L.push(`… 还有 ${dangling.length - 40} 条未显示`)
      const defVals = [...defsUnion]
      const suggestions = []
      for (const d of dangling.slice(0, 20)) {
        let best = '', bestDist = 3
        for (const dv of defVals) {
          if (Math.abs(dv.length - d.value.length) > 2) continue
          let dist = 0
          for (let i = 0; i < Math.min(dv.length, d.value.length); i++) if (dv[i] !== d.value[i]) dist++
          dist += Math.abs(dv.length - d.value.length)
          if (dist < bestDist) { bestDist = dist; best = dv }
        }
        if (best) suggestions.push(`  疑似笔误: ${d.value} → ${best}（距离 ${bestDist}）`)
      }
      if (suggestions.length) {
        L.push('')
        L.push('── 拼写建议（编辑距离 ≤2）──')
        L.push(...suggestions.slice(0, 10))
      }
      // 悬空的是 Modifier/Effect/Requirement 类标识符时，多半是「凭记忆拼了个不存在的东西」。
      // 追加可执行的下一步指引：去官方库里搜现成实现，而不是继续猜。
      const doms = new Set(dangling.map(d => String(d.dom || '')))
      if ([...doms].some(x => /Modifier|Effect|Requirement|Trait|Ability/i.test(x))) {
        L.push('')
        L.push('── 下一步：先搜原版怎么实现的，别继续猜 ──')
        L.push('  node scripts/rgn_validate_runner.mjs 只能告诉你「引用不闭合」；')
        L.push('  要查「这个效果原版用哪个 ModifierType / 参数填什么 / 挂在什么条件下」：')
        L.push('    python database/scripts/search_impl.py --modifier <关键词>     # 按关键词反查现成实现')
        L.push('    python database/scripts/search_impl.py --object <对象名>       # 从对象侧列全部 Modifier 链')
        L.push('    python database/scripts/query_effect_args.py --effect <EFFECT_X>  # 该 Effect 的参数取值域')
        L.push('  原版几乎总有同类效果可照抄，照抄的链路一定是对的。')
      }
    } else {
      L.push(mat.ok
        ? '✅ 未发现悬空引用（项目新增引用全部闭合）'
        : '⚠ 项目内引用闭合，但**未经基础库对照**（见开头告警）——不能据此判定悬空引用为 0')
    }
    if (namingIssues.length) {
      L.push('')
      L.push(`── 命名规范建议（${namingIssues.length} 条，非阻断）──`)
      L.push(...namingIssues.slice(0, 15))
      if (namingIssues.length > 15) L.push(`… 还有 ${namingIssues.length - 15} 条`)
    }
    L.push('')
    L.push('说明: 实跑模式在基础库快照上执行项目 SQL 后查库比对；执行错误多为基础库缺少引擎专属表所致，已逐语句容错。')
    return L.join('\n')
  } finally {
    try { db?.close() } catch { /* ignore */ }
    for (const p of [tmpPath, tmpPath + '-wal', tmpPath + '-shm']) {
      try { fs.unlinkSync(p) } catch { /* ignore */ }
    }
  }
}

// ─────────────────────────── 静态模式（v1 路径原样保留） ───────────────────────────
function parseInserts(sql) {
  const out = []
  const stmtRe = /INSERT\s+(?:OR\s+\w+\s+)?INTO\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(([^)]*)\))?\s*VALUES\s*([\s\S]*?)(?=;|$)/gi
  let m
  while ((m = stmtRe.exec(sql)) !== null) {
    const line = sql.slice(0, m.index).split('\n').length
    const table = m[1]
    const cols = m[2] ? m[2].split(',').map(c => c.trim().replace(/^"|"$/g, '')) : []
    const body = m[3]
    const rowRe = /\(((?:[^'()]|'(?:[^']|'')*')*)\)/g
    let rm
    const rows = []
    while ((rm = rowRe.exec(body)) !== null) {
      const inner = rm[1]
      const cells = []
      const cellRe = /'(?:[^']|'')*'|[^,]+/g
      let cm
      while ((cm = cellRe.exec(inner)) !== null) {
        let c = cm[0].trim()
        if (c.startsWith("'") && c.endsWith("'")) c = c.slice(1, -1).replace(/''/g, "'")
        cells.push(c)
      }
      rows.push(cells)
    }
    if (rows.length) out.push({ table, cols, rows, line })
  }
  return out
}

const baseCache = new Map()

function buildBaseIndex(db) {
  const colTables = new Map()
  const typeSet = new Set()
  const tables = db.prepare(`SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`).all()
  for (const t of tables) {
    try {
      const cols = db.prepare(`PRAGMA table_info("${t.name}")`).all()
      for (const c of cols) {
        const arr = colTables.get(c.name)
        if (arr) arr.push(t.name)
        else colTables.set(c.name, [t.name])
      }
    } catch { /* 跳过异常表 */ }
  }
  try {
    const rows = db.prepare(`SELECT Type FROM Types`).all()
    for (const r of rows) if (typeof r.Type === 'string') typeSet.add(r.Type)
  } catch { /* Types 表可能不存在 */ }
  return { colTables, typeSet }
}

function getBaseIndex(dbPath) {
  if (!dbPath || !fs.existsSync(dbPath)) return null
  try {
    const st = fs.statSync(dbPath)
    const key = `${dbPath}:${st.size}:${st.mtimeMs}`
    const hit = baseCache.get(key)
    if (hit) return hit
    let db = null
    try { db = new DatabaseSync(dbPath, { readOnly: true }) } catch { try { db = new DatabaseSync(dbPath) } catch { return null } }
    try {
      const idx = buildBaseIndex(db)
      baseCache.clear()
      baseCache.set(key, idx)
      return idx
    } finally { db.close() }
  } catch {
    return null
  }
}

function probeBase(base, db, domain, refCol, value) {
  if (domain === 'Type') {
    if (base.typeSet.has(value)) return true
    const refTables = base.colTables.get(refCol) ?? []
    for (const t of refTables) {
      try {
        const r = db.prepare(`SELECT 1 FROM "${t}" WHERE "${refCol}" = ? LIMIT 1`).get(value)
        if (r) return true
      } catch { /* 继续 */ }
    }
    const typeTables = base.colTables.get('Type') ?? []
    for (const t of typeTables) {
      try {
        const r = db.prepare(`SELECT 1 FROM "${t}" WHERE Type = ? LIMIT 1`).get(value)
        if (r) return true
      } catch { /* 继续 */ }
    }
    return false
  }
  const tables = base.colTables.get(domain) ?? []
  for (const t of tables) {
    try {
      const r = db.prepare(`SELECT 1 FROM "${t}" WHERE "${domain}" = ? LIMIT 1`).get(value)
      if (r) return true
    } catch { /* 继续 */ }
  }
  return false
}

function runStaticMode() {
  const L = []
  const config = { projectDataDir: dir, baseDbPath: flags.base || DEFAULT_BASE }
  if (!fs.existsSync(dir)) return `目录不存在: ${dir}`
  const files = listSqlFiles(dir, pattern)
  if (!files.length) return `目录 ${dir} 下没有匹配 ${pattern} 的 SQL 文件`

  const defs = new Map()
  const typeDefs = []
  const allStatements = []

  for (const f of files) {
    const sql = fs.readFileSync(path.join(dir, f), 'utf8')
    for (const ins of parseInserts(sql)) {
      allStatements.push({ file: f, line: ins.line, table: ins.table, cols: ins.cols, rows: ins.rows })
      const dcol = ins.cols.length ? defColOf(ins.cols) : null
      for (const row of ins.rows) {
        if (!ins.cols.length) continue
        for (let i = 0; i < ins.cols.length; i++) {
          const col = ins.cols[i]
          if (col !== dcol) continue
          const v = row[i]?.trim()
          if (!v || !IDENT_RE.test(v) || v === 'NULL') continue
          const domain = /Type$/.test(col) ? 'Type' : (/Id$/.test(col) ? col : (col === 'Key' ? 'Key' : col === 'Tag' ? 'Tag' : null))
          if (!domain) continue
          let s = defs.get(domain)
          if (!s) { s = new Set(); defs.set(domain, s) }
          s.add(v)
          if (domain === 'Type' && !v.startsWith('KIND_')) typeDefs.push({ file: f, line: ins.line, table: ins.table, value: v })
        }
      }
    }
  }

  const dangling = []
  const checked = new Set()

  const base = getBaseIndex(config.baseDbPath)
  let baseDb = null
  if (base) {
    try { baseDb = new DatabaseSync(config.baseDbPath, { readOnly: true }) } catch { try { baseDb = new DatabaseSync(config.baseDbPath) } catch { baseDb = null } }
  }

  for (const st of allStatements) {
    if (!st.cols.length) continue
    const dcol = defColOf(st.cols)
    for (const row of st.rows) {
      for (let i = 0; i < st.cols.length; i++) {
        const col = st.cols[i]
        if (isDefiningPosition(st.table, col, dcol)) continue
        const domain = domainOf(col)
        if (!domain) continue
        const v = row[i]?.trim()
        if (!v || !IDENT_RE.test(v) || v === 'NULL') continue
        if (domain === 'Tag' && v.startsWith('LOC_')) continue

        const key = `${domain}:${v}`
        if (checked.has(key)) continue
        checked.add(key)

        const own = defs.get(domain)
        if (own?.has(v)) continue
        if (base && baseDb) {
          if (probeBase(base, baseDb, domain, col, v)) continue
        } else if (/^LOC_/.test(v) || /^(KIND_|EFFECT_|MODIFIER_|REQSET_|REQ_|TRAIT_|ABILITY_|UNIT_|BUILDING_|RESOURCE_|DISTRICT_|IMPROVEMENT_|PROJECT_|BELIEF_|GOVERNOR_|GREATWORK_|RELIGION_|CIVIC_|TECH_|PLAYER_|GAME_|PROMOTION_|XP_|MOD_|RGN_)/.test(v)) {
          continue
        }
        dangling.push({ file: st.file, line: st.line, col, table: st.table, value: v, reason: '未在本项目定义' })
      }
    }
  }
  baseDb?.close()

  const namingIssues = []
  if (checkNaming) {
    for (const t of typeDefs) {
      if (base && base.typeSet.has(t.value)) continue
      if (isFreeNamedValue(t.value)) continue
      if (t.value.startsWith('MOD_')) {
        namingIssues.push(`${t.file}:${t.line} 主题 Type 以 MOD_ 开头（AGENTS.md 禁止）: ${t.value}`)
      } else if (!SUBJECT_SUFFIXES.some(s => t.value.includes(`_${s}`))) {
        if (/^(MOMENT_|KIND_|PLAYER_|GAME_|GLOBAL_|STANDARD_|UNIFORM_)/.test(t.value)) continue
        namingIssues.push(`${t.file}:${t.line} 主题 Type 缺少 _RGN / _QYQXP / 领袖缩写后缀: ${t.value}`)
      }
    }
  }

  L.push(`═══ rgn_validate 报告（静态模式）═══`)
  L.push(`目录: ${dir} | 文件: ${files.length} 个 | 基础库: ${base ? '已对照 ' + path.basename(config.baseDbPath) : '缺失 ⚠（仅项目内检查，不能判定对原版 ID 的悬空引用）'}`)
  const defTotal = [...defs.entries()].reduce((acc, [d, s]) => acc + s.size, 0)
  L.push(`定义: ${defTotal} 个标识符（域: ${[...defs.entries()].map(([d, s]) => `${d}=${s.size}`).join(', ')}）`)
  L.push(`引用: 已扫描 ${checked.size} 个去重标识符引用，悬空 ${dangling.length} 个`)

  if (dangling.length) {
    L.push('')
    L.push('── 悬空引用（未在本项目定义，基础库也未命中；注意：不识别 SELECT 动态拼接）──')
    for (const d of dangling.slice(0, 40)) {
      L.push(`⚠ ${d.file}:${d.line} [${d.table}.${d.col}] ${d.value} — ${d.reason}`)
    }
    if (dangling.length > 40) L.push(`… 还有 ${dangling.length - 40} 条未显示`)
  } else {
    L.push('✅ 未发现悬空引用（项目内定义域内全部闭合）' + (base ? '' : '（⚠ 未对照基础库，见上方说明）'))
  }

  if (namingIssues.length) {
    L.push('')
    L.push(`── 命名规范建议（${namingIssues.length} 条，非阻断）──`)
    L.push(...namingIssues.slice(0, 15))
    if (namingIssues.length > 15) L.push(`… 还有 ${namingIssues.length - 15} 条`)
  }

  L.push('')
  L.push('说明: 静态模式仅解析 VALUES 字面量行；SELECT 拼接生成的定义请改用实跑模式（去掉 --static）。')
  return L.join('\n')
}

// ─────────────────────────── 入口 ───────────────────────────
const t0 = Date.now()
const report = flags.staticMode ? runStaticMode() : runExecMode()
console.log(report)
if (!flags.staticMode) console.error(`(耗时 ${((Date.now() - t0) / 1000).toFixed(1)}s)`)
