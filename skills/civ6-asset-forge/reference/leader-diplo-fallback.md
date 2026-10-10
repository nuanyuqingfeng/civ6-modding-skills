# 领袖外交表情差分（fallback_images）数据契约

> **地位**：外交回退立绘（fallback）是每位领袖**必须制作**的根本步骤——无论领袖有没有外交语音、
> 无论是否进入纸片模型（类别④）分支，fallback 都必须制作。它是外交场景里纸片模型缺失或未加载时
> 引擎回退显示的立绘。纸片模型（类别④）才是可选扩展，其判定门见 `SKILL.md` 五bis。

## 定位

外交回退立绘（`fallback_images`）与三维纸片模型（类别④）是**两套资源**：前者是给官方
Leader_Fallback 机制按外交状态换图，后者是完整 3D 纸片注册链，二者不混用纹理类别与流程。
本文只覆盖前者的**数据契约**；注册链的通用机制（`.dds/.tex → xlp/artdef → Art.xml → .civ6proj`
幂等补注册）与校验顺序按 `SKILL.md` 对应章节执行，本文不重复。

## 条目数据形态

领袖条目的 `fallback_images` 为可选对象，键为外交状态名，值为图片槽（其余字段省略）：

```json
{
  "fallback_images": {
    "DEFAULT": { "path": "< neutral.png >" },
    "HAPPY": { "path": "< happy.png >" },
    "ENRAGED": { "path": "< angry.png >" }
  }
}
```

- `DEFAULT` 优先用显式图片，缺省沿用 `images.diplo_foreground`；**声明差分时必须提供默认图**，
  未声明的状态交由 `DEFAULT` 回退；空映射或省略整个字段 = 不启用差分。
- 同一张图可用于多个状态，各状态保留独立资源名。
- 无效状态名、空路径、缺失默认图或源文件都按错误处理，不得静默跳过。

## 外交状态名（官方枚举，全拼）

状态名单一来源为游戏官方枚举（本机 `civ6-modding/database/DebugGameplay.sqlite` 实测均为全拼）：

`DEFAULT`、`DECLARE_WAR_FROM_AI`、`DECLARE_WAR_FROM_HUMAN`、`DEFEAT`、`ENRAGED`、`FIRST_MEET`、
`HAPPY`、`HAPPY_IDLE`、`HAPPY_NEGATIVE`、`HAPPY_POSITIVE`、`KUDOS`、`NEUTRAL`、`NEUTRAL_GREETING`、
`NEUTRAL_NEGATIVE`、`NEUTRAL_POSITIVE`、`NEUTRAL_TO_HAPPY`、`NEUTRAL_TO_UNHAPPY`、`UNHAPPY`、
`UNHAPPY_IDLE`、`UNHAPPY_NEGATIVE`、`UNHAPPY_POSITIVE`、`UNHAPPY_TO_NEUTRAL`、`WARNING`

> 各状态实际触发条件能否在目标对局中呈现，需实机确认；本文只保证命名与官方枚举一致。

## 资源命名与导出规格

| 项 | 约定 |
|---|---|
| 默认图资源名 | `FALLBACK_NEUTRAL_<领袖标识>`（领袖 Type 去掉 `LEADER_` 前缀） |
| 差分状态资源名 | `FALLBACK_STATE_<状态>__LEADER_<领袖标识>`（双下划线分隔状态与领袖名） |
| 导出尺寸 | 960×960；仅给 `path` 时等比居中适配画布，显式 `scale/offset/canvas` 按图片槽排版 |
| 纹理类别 | `Leader_Fallback`（官方 3D 回退类；与类别⑤ UI 立绘的 `UserInterface` 不同类，不得混写） |
| XLP / ArtDef | `LeaderFallbackImages.xlp`（官方实名，SDK `Civ6/DLC/Expansion1/pantry/XLPs/` 实测）/ `FallbackLeaders.artdef`（官方实名，SDK pantry 与游戏 `Base/ArtDefs` 实测）；文件名不加工程前缀 |
| 透明度 | 保留 alpha；`FALLBACK_` 前缀在此为官方语义（本机制就是官方回退），与 SKILL.md 命名空间铁律（禁止第三方 UI 适配借用官方前缀）不冲突 |

## 与工程注册链的衔接

差分声明属于**领袖条目数据**，最终由条目导出流程生成 PNG → DDS/TEX → XLP → ArtDef；
手写 XLP/ArtDef 之前先确认条目数据已声明完整。交付前按 `SKILL.md` 验证顺序核对
（`verify_tex_class.py` 核对 `.tex` 类别为 `Leader_Fallback`）。

## 来源

飞花白 LeaderFallbacks 模板（经 ModTools 5.4 知识库转述，MIT）——状态名已按官方枚举
（DebugGameplay.sqlite 实测）使用全拼；资源命名、尺寸与类别规格同源。
游戏内表现不视为已验证，需实机验收。
