# InstanceManager — 动态控件克隆系统

> **来源**：`InstanceManager.lua`(343行) + `Instances/CivicUnlockIcon` + `Instances/CivilizationIcon` + `Instances/LeaderIcon`
> **地位**：Civ6 UI 最核心的复用模式——所有动态列表、按钮组、图标行都基于此。

---

## InstanceManager 类

### 构造函数

```lua
local im = InstanceManager:new(instanceName, rootControlName, ParentControl)
```

| 参数 | 说明 |
|------|------|
| `instanceName` | XML 中 `<Instance Name="xxx">` 的模板名 |
| `rootControlName` | 模板内顶层控件的 ID。克隆后通过 `inst.rootControlName` 访问 |
| `ParentControl` | （可选）释放时实例挂回的父控件 |

内部维护两个池：
- `m_AvailableInstances` — 空闲实例栈（LIFO）
- `m_AllocatedInstances` — 已借出实例

### 核心方法

**创建/获取实例**：
```lua
local inst = im:GetInstance(parent)  -- parent 可选，指定新父控件
-- 优先从空闲池取，没有则新建。自动 SetHide(false)
```

**释放实例**：
```lua
im:ReleaseInstance(inst)             -- 归还到空闲池
im:ReleaseInstanceByParent(parent)   -- 按父控件查找并释放
```

**查找**：
```lua
local inst = im:FindInstanceByControl(control)  -- 根据控件反查实例
local inst = im:GetAllocatedInstance(i)         -- 按索引取
```

**重置**：
```lua
im:ResetInstances()   -- 全部归池，隐藏。调用 OnResetting() 钩子
im:DestroyInstances() -- 全部销毁。调用 OnDestroying() 钩子（仅关机时用）
```

### 标准使用模式

```lua
-- 1. 创建 IM（通常在 OnInit/LateInitialize）
m_MyIM = InstanceManager:new("MyInstance", "RootButton", Controls.MyStack)

-- 2. 批量填充数据
function PopulateList(dataList)
    m_MyIM:ResetInstances()
    for _, data in ipairs(dataList) do
        local inst = m_MyIM:GetInstance()
        inst.RootButton:SetText(data.name)
        inst.RootButton:RegisterCallback(Mouse.eLClick, function()
            OnClick(data.id)
        end)
    end
end
```

---

## GenerationalInstanceManager

与 InstanceManager 的区别：不池化，按顺序生成。适合布局中必须按序排列的场景。

```lua
local im = GenerationalInstanceManager:new("ItemInstance", "Top", Controls.Stack)
local inst = im:GetInstance()  -- 始终按 m_NextInstanceIndex 递增
im:ResetInstances()             -- 隐藏全部，游标归 1
```

---

## PullDownInstanceManager

继承 GenerationalInstanceManager，专用于 PullDown 控件。

```lua
-- BuildInstance 调用 m_ParentControl:BuildEntry() 而非 ContextPtr:BuildInstanceForControl()
-- ParentControl 必须是一个 PullDown 控件
```

---

## XML Instance 模板写法

```xml
<Instance Name="MyItem">
    <GridButton ID="RootButton" Style="ButtonControl" Size="200,32" Anchor="L,T">
        <Stack StackGrowth="Right">
            <Image ID="Icon" StretchMode="None" Size="22,22" Anchor="C,C" />
            <Label ID="NameLabel" Style="FontNormal14" Anchor="L,C" />
            <Label ID="ValueLabel" Style="FontNormal14" Anchor="R,C" />
        </Stack>
        <Button ID="RemoveBtn" Anchor="R,T" Texture="Controls_RemoveDeal"
               Size="22,22" Hidden="1" />
    </GridButton>
</Instance>
```

**规则**：
- 模板内所有控件 ID 在克隆后成为 `inst.xxx` 访问
- **不是全局 `Controls.xxx`**——模板 ID 只在实例作用域内有效
- 根控件 ID = `InstanceManager:new()` 的第二个参数

---

## Instance Lua 包装类模式（推荐）

官方 Instances/ 目录中的最佳实践是将 Instance 包装为一个 Lua 类：

```lua
-- Step 1: 静态工厂
function MyClass.GetInstance(instanceManager, parent)
    local ui = instanceManager:GetInstance(parent)
    return MyClass:AttachInstance(ui)
end

-- Step 2: 附加
function MyClass:AttachInstance(instance)
    setmetatable(instance, {__index = self})  -- 类方法合并到控件 table
    self.Controls = instance                    -- 保存引用
    self:Reset()
    return instance
end

-- Step 3: 数据填充
function MyClass:Populate(data)
    self.Controls.NameLabel:SetText(data.name)
    self.Controls.Icon:SetTexture(data.texX, data.texY, data.sheet)
    self.Controls.RootButton:SetToolTipString(data.tooltip)
    self.Controls.RootButton:RegisterCallback(Mouse.eLClick, function()
        OnClick(data.id)
    end)
end

-- Step 4: 重置
function MyClass:Reset()
    self.Controls.RemoveBtn:SetHide(true)
end
```

### 真实案例：CivilizationIcon

```lua
-- 不同尺寸变体共享同一类
local civIconIM = InstanceManager:new("CivilizationIcon44", "CivIconBacking", parent)

function CivilizationIcon:GetInstance(instanceManager, uiNewParent)
    local instance = instanceManager:GetInstance(uiNewParent)
    return CivilizationIcon:AttachInstance(instance)
end

-- 数据填充
function CivilizationIcon:UpdateIconFromPlayerID(playerID)
    local civIcon = "ICON_" .. civTypeName
    local ox, oy, sheet = IconManager:FindIconAtlas(civIcon, self.Controls.CivIcon:GetSizeX())
    self.Controls.CivIcon:SetTexture(ox, oy, sheet)
    self:ColorCivIcon(playerID, showCivIcon)
    self:SetLeaderTooltip(playerID, details)
end
```

---

## 图标解析模式

```lua
-- 方式一：直接 SetIcon（纹理名已知）
self.Controls.Portrait:SetIcon("ICON_CIVILIZATION_ROME")

-- 方式二：IconManager 查询（需要获取图集中的纹理坐标）
local ox, oy, sheet = IconManager:FindIconAtlas(iconName, pixelSize)
self.Controls.Icon:SetTexture(ox, oy, sheet)
```

---

## 常见注意事项

- **ResetInstances 后旧引用失效**——不要持有跨 Reset 的实例引用
- **闭包捕获 data**——按钮回调中捕获数据快照，而非引用
- **ReleaseInstance 验证管理器归属**：`inst.m_InstanceManager == self`——防止跨管理器误释
- **ReleaseInstanceByParent 存在 bug**（第128行，`instance` vs `iter` 变量错误——但不太可能遇到，因为通常用 ResetInstances）
- **每个实例上自动设置 `m_InstanceManager`** 以追踪归属
