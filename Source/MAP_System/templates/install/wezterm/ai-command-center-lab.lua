local wezterm = require("wezterm")
local act = wezterm.action

local project_dir = os.getenv("PROJECT_DIR") or "__PROJECT_DIR__"
local local_bin = "__LOCAL_BIN__"

local function tab(window, pane, title, argv)
  local new_tab, _, _ = window:mux_window():spawn_tab({
    cwd = project_dir,
    args = argv,
  })
  new_tab:set_title(title)
end

wezterm.on("gui-startup", function(cmd)
  local _, pane, window = wezterm.mux.spawn_window({
    workspace = "ai-command-center-lab",
    cwd = project_dir,
    args = { local_bin .. "/ai-command-center-lab-shell" },
  })
  window:gui_window():set_title("AI Command Center Lab")
  tab(window:gui_window(), pane, "Codex Lab", { local_bin .. "/ai-command-center-lab-codex" })
  tab(window:gui_window(), pane, "Claude Lab", { local_bin .. "/ai-command-center-lab-claude" })
  tab(window:gui_window(), pane, "Librarian", { local_bin .. "/ai-command-center-lab-librarian" })
  tab(window:gui_window(), pane, "Monitor", { local_bin .. "/ai-command-center-monitor" })
end)

return {
  automatically_reload_config = true,
  window_close_confirmation = "NeverPrompt",
  enable_tab_bar = true,
  hide_tab_bar_if_only_one_tab = false,
  use_fancy_tab_bar = false,
  tab_bar_at_bottom = false,
  font_size = 11.0,
  color_scheme = "Builtin Solarized Dark",
  keys = {
    { key = "1", mods = "CTRL", action = act.ActivateTab(0) },
    { key = "2", mods = "CTRL", action = act.ActivateTab(1) },
    { key = "3", mods = "CTRL", action = act.ActivateTab(2) },
    { key = "4", mods = "CTRL", action = act.ActivateTab(3) },
    { key = "5", mods = "CTRL", action = act.ActivateTab(4) },
  },
}

