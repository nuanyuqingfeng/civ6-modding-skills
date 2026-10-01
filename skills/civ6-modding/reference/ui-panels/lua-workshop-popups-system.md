# 弹窗系统总览 — 7种弹窗模式

> **来源**：`Popups/EventPopup.*`, `EraComplete.*`, `BoostUnlocked.*`, `TechCivicCompleted.*`, `NaturalWonder.*`, `WonderBuilt.*`, `ProjectBuilt.*`
> **地位**：7种系统弹窗覆盖了游戏所有通知弹窗的完整模式。

---

## 弹窗架构对比

| 弹窗 | 优先级 | 锁机制 | 多模式 | 自动关闭 |
|------|--------|--------|--------|----------|
| EventPopup | Medium | UIManager | 单按钮/A/B选择 | 否（用户点按钮） |
| EraComplete | High | ExclusivePopupMgr | 仅展示 | 是（AlphaAnim反向播放） |
| BoostUnlocked | Low | UIManager | 科技/市政双模式 | 否 |
| TechCivicCompleted | Low | UIManager | 科技/市政双模式 | 否 |
| NaturalWonder | High | ExclusivePopupMgr | 仅展示 | 否 |
| WonderBuilt | High | ExclusivePopupMgr | 仅展示 | 否（含重播按钮） |
| ProjectBuilt | High | ExclusivePopupMgr | 仅展示 | 否 |

---

## 弹窗风格

### 电影化覆盖层（全屏暗背景 + 动画头部+底部）
**NaturalWonder / WonderBuilt / ProjectBuilt / EraComplete**

```
Image × 8 ← 暗角遮罩
AlphaAnim(HeaderAlpha) + SlideAnim(HeaderSlide)
  Grid(HeaderGrid)
    Label(WonderCompletedHeader) ← 标题
AlphaAnim(QuoteAlpha) + SlideAnim(QuoteSlide)
  Container(QuoteContainer)
    名称/图标/引用文字
```

### 居中面板（有游戏可见背景）
**BoostUnlocked / TechCivicCompleted**

```
Grid(DropShadow) + Image(Parchment_Pattern, Tile)
  Grid(PopupFrame)
    标题栏 + 图标/仪表 + 描述 + 底部按钮
```

### 混合型（全屏遮罩 + 居中窗口）
**EventPopup**

```
Box ← 全屏暗色遮罩
AlphaAnim + SlideAnim
  DropShadow → Window(EventPopupFrame)
    标题区 + 描述区 + 图像区 + 效果滚动区 + 按钮栈
```

---

## 队列系统

### UIManager 队列（EventPopup / BoostUnlocked / TechCivicCompleted）

```lua
-- 入队
local canShow = UI.CanShowPopup(PopupPriority.Low)
if canShow then
    UIManager:QueuePopup(ContextPtr, priority, {DelayShow=true})
else
    table.insert(m_kQueuedPopups, entry)  -- 缓存
end

-- 出队
OnClose() → ShowNextQueuedPopup() ← 从队列取下一个
```

### ExclusivePopupManager 队列（电影化弹窗）

```lua
m_kPopupMgr = ExclusivePopupManager:new("WonderBuilt")
m_kPopupMgr:Lock(context, priority, params)  -- 阻止其他弹窗
-- ... 展示 ...
m_kPopupMgr:Unlock()  -- 释放锁
```

---

## 解锁图标系统（EventPopup + TechCivicCompleted 共用）

```xml
<Instance Name="UnlockInstance">
  <Container ID="Top" Size="45,45">
    <Image Texture="CompletedPopup_IconSlot">
      <Button ID="UnlockIcon" Style="UnlockFrames" NoStateChange="1" Anchor="C,C">
        <Image ID="Icon" Size="38,38" Texture="Controls_Blank" Anchor="C,C"/>
      </Button>
    </Image>
  </Container>
</Instance>
```

Lua 填充：
```lua
PopulateUnlockablesForTech(playerId, index, unlockIM, callback)
-- IconManager:FindIconAtlas(iconName, 38) → SetTexture
```

---

## 弹窗触发源

| 弹窗 | Game Event | Lua Event |
|------|-----------|-----------|
| EventPopup | `Events.EventPopupRequest` | `LuaEvents.EventPopupRequest` |
| EraComplete | `Events.PlayerEraChanged` | — |
| BoostUnlocked | — | `LuaEvents.NotificationPanel_ShowTechBoost/CivicBoost` |
| TechCivicCompleted | — | `LuaEvents.NotificationPanel_ShowTechDiscovered/CivicDiscovered` |
| NaturalWonder | `Events.NaturalWonderRevealed` | — |
| WonderBuilt | `Events.WonderCompleted` | — |
| ProjectBuilt | `Events.CityProjectCompletedNarrative` | — |

## 多人游戏守卫

- **NaturalWonder / WonderBuilt / ProjectBuilt**：全多人游戏禁用
- **EraComplete**：检查 `CAPABILITY_ERAS`
- **BoostUnlocked / TechCivicCompleted**：热座时 `OnLocalPlayerTurnEnd` 关闭
- **EventPopup**：无守卫
