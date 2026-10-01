# PopupDialog — 标准弹窗框架

> **来源**：`Popups/PopupDialog.xml`(61行) + `Popups/PopupDialog.lua`(561行)
> **地位**：所有游戏内弹窗的共享基础框架。通过 `Include` + `MakeInstance` 模式被所有面板复用。

---

## XML 结构（控件树）

```xml
<Include File="PopupDialog">
  <!-- 根实例 -->
  <Instance Name="PopupDialog">
    <Box ID="PopupRoot" Color="0,0,0,150" Size="parent,parent" ConsumeMouse="1" Hidden="1">
      <AlphaAnim ID="PopupAlphaIn" AlphaBegin="0" AlphaEnd="1" Speed="3" Function="Root" Cycle="Once">
        <SlideAnim ID="PopupSlideIn" Start="0,-20" End="0,0" Speed="3" Function="Root" Cycle="Once">
          <Grid Style="DropShadow2" Size="auto,auto" Anchor="C,C" Color="255,255,255,200" AutoSizePadding="25,25">
            <Grid ID="PopupBox" Style="WindowFrameTitle" Size="560,auto" Anchor="C,C" AutoSizePadding="0,10">
              <Container Size="parent,38">
                <Label ID="PopupTitle" Style="WindowHeader" Anchor="C,C" />
              </Container>
              <Stack ID="PopupStack" Size="parent,100" Anchor="C,T" Offset="0,50"
                     StackGrowth="Bottom" StackPadding="30" />
            </Grid>
          </Grid>
        </SlideAnim>
      </AlphaAnim>
    </Box>
  </Instance>
</Include>
```

**层次**：半透明遮罩 → 淡入动画 → 滑入动画 → 外框阴影 → 窗口框架 → 标题栏 + 内容区

---

## 内容模板（可实例化的 Instance）

| Instance 名 | 顶层控件 ID | 尺寸 | 说明 |
|-------------|------------|------|------|
| `PopupButtonInstance` | `Button` | 220×41 | 标准按钮（MainButton 样式） |
| `PopupButtonInstanceRed` | `Button` | 220×41 | 红色警告按钮 |
| `PopupButtonInstanceGreen` | `Button` | 220×41 | 绿色确认按钮 |
| `PopupTextInstance` | `Text` | auto | 正文标签（BodyTextDark18, WrapWidth=430, 居中） |
| `PopupRowInstance` | `Row` | auto | 按钮行容器（StackGrowth=Right, StackPadding=10） |
| `PopupCountDownInstance` | `Anim`(AlphaAnim) | 50×50 | 脉动倒计时（FontNormal40, Alpha 1→0.5） |
| `PopupCheckboxInstance` | `Check` | 340×24 | 复选框（CheckBoxPopupControl 样式） |
| `PopupEditboxInstance` | `EditBoxRoot` | auto | 标签 + 编辑框组合（MaxLength=32） |

---

## Lua API

### 构造函数

```lua
local dlg = PopupDialog:new("MyID", myControls)  -- myControls 可选，默认 Controls
```

### 便捷对话框（一行搞定）

```lua
PopupDialog:new("id"):ShowOkDialog("保存成功", function() end)
PopupDialog:new("id"):ShowOkCancelDialog("确定删除？", onOk, onCancel)
PopupDialog:new("id"):ShowYesNoDialog("要宣战吗？", onYes, onNo)
```

### 标准生命周期

```lua
local dlg = PopupDialog:new("myDialog")

-- 构建内容（必须在 Open() 之前）
dlg:AddTitle("标题文本")
dlg:AddText("正文内容")
dlg:AddButton("确定", onConfirm, PopupDialog.COMMAND_CONFIRM)
dlg:AddButton("取消", onCancel, PopupDialog.COMMAND_CANCEL)
dlg:AddCheckBox("不再显示", false, onCheckChanged)
dlg:AddEditBox("输入名称", onCommit, onStringChanged)
dlg:AddCountDown(10, onTimeout)

-- 显示
dlg:Open()

-- 程序化触发按钮
dlg:ActivateCommand(PopupDialog.COMMAND_CONFIRM)  -- 回车键

-- 查询编辑框
local text = dlg:GetEditBoxText("optionalCommand")

-- 关闭（用户回调中自动调用 Close）
dlg:Close()  -- = SetHide(true) + Reset()
```

### 按钮回调模式

每个按钮点击后**先关闭弹窗再执行回调**：

```lua
local closeAndCallback = function()
    self:Close()
    if callback then callback() end
end
pButtonControl:RegisterCallback(Mouse.eLClick, closeAndCallback)
```

### SetSize

```lua
dlg:SetSize(600, 300)  -- 默认 560×auto
-- 必须在 Open() 之前调用
```

### 命令系统

| 命令常量 | 触发方式 |
|----------|---------|
| `PopupDialog.COMMAND_CONFIRM` (`"_CMD_CONFIRM"`) | 回车键 |
| `PopupDialog.COMMAND_CANCEL` (`"_CMD_CANCEL"`) | ESC 键 |
| `PopupDialog.COMMAND_DEFAULT` (`"_CMD_DEFAULT"`) | 回车或 ESC（优先级最低） |

---

## 面板复用方式

```xml
<!-- 面板 XML 中 -->
<Include File="PopupDialog" />
<MakeInstance Name="PopupDialog" />
```

后 PopupDialog 的所有控件（PopupRoot, PopupAlphaIn, PopupSlideIn, PopupTitle, PopupStack）成为面板 Controls 的一部分。

---

## PopupDialogInGame — 世界层弹窗

`PopupDialogInGame` 类将内容推送到世界层弹窗管理器（`InGamePopup.lua`），而非自己渲染。

```lua
local dlg = PopupDialogInGame:new("myIngame")
dlg:AddText("消息内容")
dlg:AddConfirmButton("确定", onOk)
dlg:Open()  -- 触发 LuaEvents.OnRaisePopupInGame
```

与 `PopupDialog` 的 API 一致，但渲染在世界层而非屏幕中心。

---

## InstanceManager 使用

PopupDialog 内部维护 5 个 IM：

| IM | 实例名 | 父控件 |
|----|--------|--------|
| TextIM | PopupTextInstance | PopupStack |
| RowStackIM | PopupRowInstance | PopupStack |
| CountDownIM | PopupCountDownInstance | (独立) |
| CheckBoxIM | PopupCheckboxInstance | PopupStack |
| EditBoxIM | PopupEditboxInstance | PopupStack |
