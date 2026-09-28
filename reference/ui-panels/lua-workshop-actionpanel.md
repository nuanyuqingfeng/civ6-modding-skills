# ActionPanel — 结束回合按钮 + 动画系统

> **来源**：`ActionPanel.xml`(238行) + `ActionPanel.lua`(1367行)
> **地位**：右下角结束回合按钮，Civ6中**动画控件最密集**的面板——AlphaAnim+SlideAnim+FlipAnim+Meter全覆盖。

---

## XML 结构

```
Context
  Stack(NotificationStack) ← 通知堆叠
  Container ← 根视觉容器 (R,B)
    Image(ActionPanel_LittleGear.dds) ← 装饰齿轮
    Image(ActionPanel_WoodenRim.dds) ← 木框装饰
    FlipAnim(TickerAnim) ← 回合指示器帧动画 (52×60, 10帧, 5列)
    
    AlphaAnim(OverflowHandleAlpha) + SlideAnim(OverflowHandleSlide)
    
    AlphaAnim(TurnBlockerAlpha4~2) + SlideAnim(TurnBlockerSlide4~2)
      ← 3个阻塞图标卡位，每个=AlphaAnim+SlideAnim+Image+Button
    
    AlphaAnim(TurnBlockerContainerAlpha) + SlideAnim(TurnBlockerContainerSlide)
      Grid(OverflowContainer) + Stack(OverflowStack)
    
    AlphaAnim(OverflowAlpha) + SlideAnim(OverflowSlide)
      ← 溢出勾选组
    
    Button(EndTurnButtonLabel) ← 结束回合标签
    
    BoxButton(EndTurnButton) ← 主按钮热区 (108×108, 透明)
      Image(CurrentTurnBlockerIcon) ← 当前阻塞图标 (100×100)
      AlphaAnim×4 ← 科学/生产/免费科技/结束回合闪烁动画
    
    Meter(TurnTimerMeter) ← 回合计时器 (95×95)
    
    Tutorial×10 ← 教程覆盖层
```

## 实例

| 实例名 | 根控件 | 用途 |
|--------|--------|------|
| `TurnBlockerInstance` | GridButton `TurnBlockerButton` (210×50) | 阻塞项按钮 |
| `EraPipInstance` | Image `PipImage` | 时代标记点 |

## Lua 核心模式

### InstanceManager
```lua
m_overflowIM = InstanceManager:new("TurnBlockerInstance", "TurnBlockerButton", Controls.OverflowStack)
```
动态创建阻塞按钮：`ResetInstances()` → `GetInstance()` → 设置图标+回调。

### 动画控制（核心模式）

**显示动画**（AlphaAnim + SlideAnim 并行）：
```lua
kAlphaControl:SetHide(false)
kAlphaControl:SetToBeginning()
kSlideControl:SetToBeginning()
kAlphaControl:Play()
kSlideControl:Play()
```

**隐藏动画**（反向播放）：
```lua
kAlphaControl:Reverse()
kSlideControl:Reverse()
kAlphaControl:Play()
kSlideControl:Play()
```

**动画结束回调**（反向播完后隐藏）：
```lua
function OnAnimEnd(kControl)
    if kControl:IsReversing() then
        kControl:SetHide(true)
    end
end
Controls.TurnBlockerAlpha4:RegisterEndCallback(OnAnimEnd)
```

### FlipAnim 控制
```lua
Controls.TickerAnim:SetToBeginning()
Controls.TickerAnim:Play()
```

### BoxButton 透明热区
```xml
<BoxButton ID="EndTurnButton" Anchor="R,B" Offset="11,28"
           Size="108,108" Color="0,0,0,0" NoStateChange="1">
    <Image ID="CurrentTurnBlockerIcon" Size="100,100" Texture="Notifications100" />
    <AlphaAnim ... /> ← 4个闪烁动画叠加
</BoxButton>
```
按钮本身完全透明，内部叠放图标+4个AlphaAnim闪烁层。点击热区由BoxButton注册回调。

### DoEndTurn 流程
```
DoEndTurn():
  没有阻塞 → UI.RequestAction(ACTION_ENDTURN)
  有阻塞：
    UNITS类 → UI.SelectNextReadyUnit()
    其他 → 查找Notification → LuaEvents.ActionPanel_ActivateNotification()
```

### 事件注册摘要

**游戏事件**（18个）：`EndTurnBlockingChanged`, `CityProductionChanged`, `CityCommandStarted`, `UnitOperationSegmentComplete`, `LocalPlayerTurnBegin/End`, `NotificationAdded/Dismissed`, `TurnTimerUpdated`等

**LuaEvents**：`AutoPlayStart/End`, `Tutorial_SlowNextTurnEnable`, `ProductionPanel_IsQueueOpen`, `EndGameMenu_StartObserverMode`

---

## 关键控件用法索引

| 控件类型 | ID | 模式 |
|---------|-----|------|
| AlphaAnim+SlideAnim并行 | TurnBlockerAlpha4/Slide4 等 | 弹入弹出阻塞按钮 |
| FlipAnim | TickerAnim | 帧动画 (10帧, 5列, Speed=30, Cycle=OneBounce) |
| Meter | TurnTimerMeter | 回合计时器 (Speed=0=瞬间跳变) |
| BoxButton | EndTurnButton | 透明热区 (Color=0,0,0,0, NoStateChange=1) |
| Tutorial | TutSelectEndTurnAction 等 | 教程覆盖层 (TriggerBy) |
