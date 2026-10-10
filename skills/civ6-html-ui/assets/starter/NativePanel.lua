-- Layout/lifecycle sample only. Rename events and connect real project data.
-- Open with LuaEvents.DemoPanel_Open(); no LaunchBar entry is created here.
local m_Selected = false;
local m_Open = false;

local function Refresh()
  Controls.Selection:SetHide(not m_Selected);
  Controls.ConfirmButton:SetDisabled(not m_Selected);
  Controls.Status:SetText(Locale.Lookup(m_Selected and "LOC_DEMO_SELECTED" or "LOC_DEMO_SELECT_HINT"));
  Controls.DescriptionScroll:CalculateInternalSize();
end

local function Close()
  if not m_Open then return; end
  UIManager:DequeuePopup(ContextPtr);
  ContextPtr:SetHide(true);
  m_Open = false;
end

local function Open()
  if Game.GetLocalPlayer() == -1 then return; end
  -- Add this project's eligibility check before queuing the popup.
  m_Selected = false;
  Refresh();
  if not m_Open then
    UIManager:QueuePopup(ContextPtr, PopupPriority.Current);
    m_Open = true;
  end
end

local function Confirm()
  if not m_Open or not m_Selected then return; end
  Close();
  -- Only a local UI event. Connect the verified gameplay request separately.
  LuaEvents.DemoPanel_Confirmed();
end

local function OnInput(input)
  if m_Open and input:GetMessageType() == KeyEvents.KeyUp and input:GetKey() == Keys.VK_ESCAPE then
    Close();
    return true;
  end
  return false;
end

local function Shutdown()
  LuaEvents.DemoPanel_Open.Remove(Open);
  Close();
end

Controls.CardButton:RegisterCallback(Mouse.eLClick, function() m_Selected = not m_Selected; Refresh(); end);
Controls.ConfirmButton:RegisterCallback(Mouse.eLClick, Confirm);
Controls.CloseButton:RegisterCallback(Mouse.eLClick, Close);
ContextPtr:SetInputHandler(OnInput, true);
ContextPtr:SetShutdown(Shutdown);
LuaEvents.DemoPanel_Open.Add(Open);
ContextPtr:SetHide(true);
Refresh();
