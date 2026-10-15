#!/usr/bin/env node
/** rgn_validate --scope-check 回归测试：临时 git 仓库构造 baseline -> 误用改动 -> 恢复正确 */
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import { spawnSync } from 'node:child_process'

const SCRIPT_DIR = import.meta.dirname
const RUNNER = path.resolve(SCRIPT_DIR, 'rgn_validate_runner.mjs')

const BASELINE = `INSERT OR REPLACE INTO Types (Type, Kind) VALUES
('TRAIT_SCOPE_TEST', 'KIND_TRAIT'),
('MODIFIER_SCOPE_CUSTOM_UNITS', 'KIND_MODIFIER'),
('MODIFIER_SCOPE_CUSTOM_OWNER', 'KIND_MODIFIER');

INSERT OR REPLACE INTO Traits (TraitType, Name, Description) VALUES
('TRAIT_SCOPE_TEST', 'LOC_SCOPE_TEST', 'LOC_SCOPE_TEST');

INSERT OR REPLACE INTO DynamicModifiers (ModifierType, CollectionType, EffectType) VALUES
('MODIFIER_SCOPE_CUSTOM_UNITS', 'COLLECTION_PLAYER_UNITS', 'EFFECT_ADJUST_UNIT_IGNORE_RIVERS'),
('MODIFIER_SCOPE_CUSTOM_OWNER', 'COLLECTION_OWNER', 'EFFECT_ADJUST_UNIT_IGNORE_RIVERS');

INSERT OR REPLACE INTO Modifiers (ModifierId, ModifierType) VALUES
('MOD_SCOPE_TRAIT_OK', 'MODIFIER_PLAYER_UNITS_ADJUST_IGNORE_RIVERS'),
('MOD_SCOPE_ABILITY_OK', 'MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_SHORES'),
('MOD_SCOPE_CUSTOM_TRAIT', 'MODIFIER_SCOPE_CUSTOM_UNITS');

INSERT OR REPLACE INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_SCOPE_TEST', 'MOD_SCOPE_TRAIT_OK'),
('TRAIT_SCOPE_TEST', 'MOD_SCOPE_CUSTOM_TRAIT');

INSERT OR REPLACE INTO UnitAbilityModifiers (UnitAbilityType, ModifierId) VALUES
('ABILITY_IGNORE_CROSSING_RIVERS_COST', 'MOD_SCOPE_ABILITY_OK');
`

const WRONG = BASELINE
  .replace("('MOD_SCOPE_TRAIT_OK', 'MODIFIER_PLAYER_UNITS_ADJUST_IGNORE_RIVERS')", "('MOD_SCOPE_TRAIT_OK', 'MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_RIVERS')")
  .replace("('MOD_SCOPE_ABILITY_OK', 'MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_SHORES')", "('MOD_SCOPE_ABILITY_OK', 'MODIFIER_PLAYER_UNITS_ADJUST_IGNORE_SHORES')")
  .replace("('MOD_SCOPE_CUSTOM_TRAIT', 'MODIFIER_SCOPE_CUSTOM_UNITS')", "('MOD_SCOPE_CUSTOM_TRAIT', 'MODIFIER_SCOPE_CUSTOM_OWNER')")

function run(cwd, dataDir) {
  return spawnSync(process.execPath, [RUNNER, dataDir, '--scope-check'], { cwd, encoding: 'utf8' })
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg)
}

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'rgn-scope-'))
const dataDir = path.join(root, 'Data')
fs.mkdirSync(dataDir)
const sqlPath = path.join(dataDir, 'Modifiers.sql')

function git(args) {
  const r = spawnSync('git', args, { cwd: root, encoding: 'utf8' })
  assert(r.status === 0, `git ${args.join(' ')} 失败: ${r.stderr}`)
}

try {
  fs.writeFileSync(sqlPath, BASELINE)
  git(['init'])
  git(['config', 'user.name', 'Scope Test'])
  git(['config', 'user.email', 'scope@test.local'])
  git(['add', 'Data/Modifiers.sql'])
  git(['commit', '-m', 'baseline'])

  fs.writeFileSync(sqlPath, WRONG)
  const bad = run(root, dataDir)
  assert(bad.status === 1, `误用改动应 exit 1，实际 ${bad.status}`)
  assert(bad.stdout.includes('[trait] MOD_SCOPE_TRAIT_OK 使用 MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_RIVERS'), '未抓到 trait 官方单复数误用')
  assert(bad.stdout.includes('[ability] MOD_SCOPE_ABILITY_OK 使用 MODIFIER_PLAYER_UNITS_ADJUST_IGNORE_SHORES'), '未抓到 ability 官方单复数误用')
  assert(bad.stdout.includes('[trait] MOD_SCOPE_CUSTOM_TRAIT 使用 MODIFIER_SCOPE_CUSTOM_OWNER'), '未抓到既有自建 ModifierType 误用')

  fs.writeFileSync(sqlPath, BASELINE)
  const good = run(root, dataDir)
  assert(good.status === 0, `恢复正确后应 exit 0，实际 ${good.status}`)
  console.log('rgn_validate --scope-check 回归通过')
} finally {
  fs.rmSync(root, { recursive: true, force: true })
}
