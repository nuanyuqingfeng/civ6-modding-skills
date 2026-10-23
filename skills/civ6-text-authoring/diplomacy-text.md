# 类 4 —— 外交文本规范

> 覆盖 `LOC_DIPLO_*` `LOC_DIPLOMACY_*` `LOC_DIPLOACTION_*` `LOC_GOSSIP*` `LOC_EMERGENCY_*`（语料 3,748 条）
> 语料：`reference/catalog/diplomacy.tsv` ｜ 查询：`zh_corpus.sqlite` `WHERE Category='diplomacy'`

## 1. tag 语法（`LOC_DIPLO_*` 主干）

```
LOC_DIPLO_ <ACTION> [ _<SUBTYPE> ] _<DIRECTION>_<LEADER>_<TO>
      │        │            │            │         │
      │        │            │            │         └ TO    : ANY / 具体对象
      │        │            │            └ LEADER: LEADER_<领袖Type> | ANY
      │        │            └ DIRECTION: FROM_AI | FROM_HUMAN | FROM_UNIT | EXIT | CHOICE_POSITIVE/NEGATIVE/STOP_ASKING
      │        └ SUBTYPE : FRIEND | WAR | ALLIANCE | BORDERS | …
      └ ACTION  : FIRST_MEET | GREETING | KUDO | WARNING | DENOUNCE | DECLARE | MAKE | OPEN | DELEGATION | DEFEAT | …
```

官方范式（**腕税款 = `ANY`，个性化台词 = `LEADER_<X>`，引擎按领袖回退到 `ANY`**）：

```
LOC_DIPLO_FIRST_MEET_ANY_ANY                 = 您好旅行者。我想，您现在知道什么是伟大了吧！        （通用回退）
LOC_DIPLO_FIRST_MEET_LEADER_ABRAHAM_LINCOLN_ANY = 我是总统亚伯拉罕·林肯，我的国家虽然年轻，却构建在梦想之上。
LOC_DIPLO_GREETING_LEADER_AMBIORIX_ANY       = 幸会。
LOC_DIPLO_KUDO_EXIT_LEADER_AMBIORIX_ANY      = 好一支大军！哈哈！看看他们呐！
LOC_DIPLO_DEFEAT_FROM_AI_LEADER_AMBIORIX_ANY = 居然有这般神力！看来我之前小看了你。我败了，理应给与你应得的尊重。
```

> ★ **必须提供 `ANY` 兜底**：任何 `LEADER_<X>` 台词缺失时引擎回退到 `ANY`；只写个性化、漏 `ANY` → 缺领袖时显示 tag 原文。

## 2. 动作词表（ACTION / SUBTYPE）

| ACTION | 含义 | 常见 SUBTYPE |
|---|---|---|
| `FIRST_MEET` | 首次相遇 | — |
| `GREETING` | 日常问候/开场 | — |
| `KUDO` | 称赞（满足其议程时） | — |
| `WARNING` | 警告（违反其议程时） | — |
| `DENOUNCE` | 谴责 | `REASON_*` |
| `DECLARE` | 宣布关系 | `FRIEND` / `WAR` |
| `MAKE` | 提议 | `ALLIANCE` / `DECLARE_FRIEND` |
| `OPEN` | 开放边界 | `BORDERS` |
| `DELEGATION` | 派遣代表团 | — |
| `RENEW` | 续约 | — |
| `INTEL` | 情报交换 | — |
| `DEFEAT` | 战败致辞 | — |
| `GRIEVANCE` | 不满记录 | `LOG_*` |

## 3. 句式与口吻规范

1. **领袖第一人称对玩家说话**（`FROM_AI_*`）：用「我 / 您」，语气符合领袖性格（林肯庄重、安比奥里克斯狂放）。
2. **通用回退句保持中性**：`ANY` 版本不带领袖特征，只作兜底，简短（「幸会。」「您请讲。」）。
3. **CHOICE 三态成套**：每次提议配
   `_CHOICE_POSITIVE`（同意台词）/ `_CHOICE_NEGATIVE`（拒绝台词）/ 必要时 `_CHOICE_STOP_ASKING`。
   ```
   LOC_DIPLO_MAKE_ALLIANCE_CHOICE_POSITIVE = 我们很高兴让全世界知道我们是盟友。
   LOC_DIPLO_MAKE_ALLIANCE_CHOICE_NEGATIVE = 对不起，我们目前无法作出结盟的承诺。
   ```
4. **议题理由（REASON）用括号被动句**（第三人称，描述触发原因）：
   ```
   LOC_DIPLO_DENOUNCE_REASON_FROM_AI_LEADER_ANY_REASON_AGENDA_ANGEVIN_EMPIRE = （您与其相邻的城市人口过少。）
   ```
5. **议程解释挂 `_AGENDA_EXPLANATION`**（KUDO/WARNING 共用句式，带 `{Name}`/`{Agenda}` 占位）：
   ```
   LOC_DIPLO_WARNING_AGENDA_EXPLANATION = [NEWLINE]（您已违反{Name}的议程——{Agenda}）
   LOC_DIPLO_KUDO_AGENDA_EXPLANATION    = [NEWLINE]（您已满足{Name}的议程——{Agenda}）
   ```
6. **占位符**：`{1_CivName}` `{1_CityName}` `{1_TypeEmergency}` 等，与事件/引擎传参一致；不要写死文明名。

## 4. 关联家族（其余外交子系统）

| tag 族 | 用途 | 范式 |
|---|---|---|
| `LOC_DIPLOMACY_*` | **通知**（顶部通知条） | `LOC_DIPLOMACY_KUDO_NOTIFICATION_MESSAGE_INITIAL`=收到一条信息 / `..._SUMMARY_INITIAL`={1_name}给您发送了一条信息。 |
| `LOC_DIPLOACTION_*` | **外交动作 UI**（同盟、协定面板） | `LOC_DIPLOACTION_ALLIANCE_DESCRIPTION` / `_NAME` / `_TAB_TOOLTIP` |
| `LOC_GOSSIPDESC_*` | **流言描述**（注意是 `GOSSIPDESC` 非 `GOSSIP`） | `LOC_GOSSIPDESC_ALLIED`=联盟 / `LOC_GOSSIPDESC_CONQUER_CITY`=城市征服 |
| `LOC_EMERGENCY_*` | **世界议会紧急状况** | `LOC_EMERGENCY_CLIMATE_ACCORDS_NAME`=气候协议 / `LOC_EMERGENCY_COMPLETED`={1_TypeEmergency}结束 |
| `LOC_DIPLO_STATE_*` | 外交状态名 | `LOC_DIPLO_STATE_ALLIED_NAME`=结盟 / `..._DENOUNCED_NAME`=谴责 |

## 5. 与议程文本的分工

- **议程的偏好描述**（`LOC_AGENDA_*_DESCRIPTION`：「喜欢…。讨厌…。」）→ 归 [leader-trait-text.md](leader-trait-text.md)。
- **议程触发后的外交台词**（KUDO/WARNING/DENOUNCE 的具体句子）→ 归本类。
- 两者经同一 `AgendaType` 串联：改议程时**两处都要动**，且好感链（`agonize` 系 Modifier）数值与描述一致。

## 6. 校验清单

- [ ] 每个 `LEADER_<X>` 台词都有同 ACTION 的 `ANY` 兜底
- [ ] 提议类三态（POSITIVE/NEGATIVE）成套
- [ ] `REASON_*` 用括号被动句；`AGENDA_EXPLANATION` 含 `{Name}`/`{Agenda}`
- [ ] 占位符名与引擎事件参数一致
- [ ] 跑 `check_text_refs.py`
