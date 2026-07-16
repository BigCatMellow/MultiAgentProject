# MAP Fresh Install

This document describes how to bring up the MAP AI Command Center from a fresh clone on a new Linux workstation.

The repo-owned executable-style bootstrap is:

```bash
./MAP-System-Installer.run
```

That wrapper runs the main installer with `--yes`. If you want to preview first, run:

```bash
./install-map-system.sh --dry-run
./install-map-system.sh --yes
```

The default mode is `--dry-run`. It prints planned changes without writing to the user profile. Use `--yes` only after reviewing the plan.

## What The Installer Covers

The installer is intentionally user-local and non-destructive:

- Detects the repo path dynamically from the location of `install-map-system.sh`.
- Installs missing base OS packages on Debian/Ubuntu-style systems when `--yes` is used.
- Installs missing `hcom` into `~/.local/share/hcom-venv` from the PyPI package and links `~/.local/bin/hcom`.
- Installs missing WezTerm through the official WezTerm APT repository on Debian/Ubuntu-style systems.
- Installs command-center scripts into `~/.local/bin`.
- Installs the bundled CommandCenterUI app into `~/Projects/CommandCenterUI` by default.
- Installs `command-center-ui` and `project-updater` launch commands.
- Installs the WezTerm lab config into `~/.config/wezterm/ai-command-center-lab.lua`.
- Installs desktop launchers into `~/.local/share/applications`.
- Creates or updates `MAP_System/.venv` when Python venv support is available.
- Checks core command availability: `git`, `python3`, `rg`, `hcom`, `wezterm`, `codex`, `claude`, and `gemini`.
- Backs up any overwritten user-local file under `~/.local/state/map-install/backups/<timestamp>/`.

The installed command surface includes:

- `ai`
- `ai tell "message"`
- `ai codex "message"`
- `ai claude "message"`
- `ai helper ...`
- `ai-command-center`
- `ai-command-center-lab`
- `ai-command-center-monitor`
- `command-center-ui`
- `project-updater`
- `langgraph-run`
- `agent-status`
- `agent-screens`
- `agent-tabs`
- `agent-deck`
- `start-agents`

## What Still Needs The User

Some pieces still need human action because they depend on credentials, account policy, or unsupported OS packaging:

- `hcom` may need first-run configuration on a brand-new user account after installation.
- WezTerm must be installed manually on non-apt platforms unless you extend the installer for that platform.
- CommandCenterUI is bundled, but optional local summarization needs Ollama and the configured model if you want relay cards instead of raw messages.
- Codex, Claude, and Gemini CLIs must be installed and authenticated if those agents will be used.
- Optional local model tools such as Ollama should be installed only when a task needs them.

The installer intentionally does not enter API keys, browser logins, or model-provider credentials.

References for upstream installers:

- hcom: https://pypi.org/project/hcom/
- WezTerm Linux install: https://wezterm.org/install/linux.html

After installing or authenticating any external tool, re-run:

```bash
./install-map-system.sh --dry-run
```

The post-install check will show which tools are still missing.

## Common Setup Flow

From a fresh clone:

```bash
cd ~/Projects/MultiAgentProject
./install-map-system.sh --dry-run
./MAP-System-Installer.run
```

Open the lab:

```bash
ai-command-center-lab
```

Open the graphical CommandCenterUI:

```bash
command-center-ui
```

Open ProjectUpdater directly:

```bash
project-updater
```

Check hcom/MAP status:

```bash
ai status
ai inbox
langgraph-run
```

Send a command-center message:

```bash
ai tell "fresh install check"
```

## Installer Options

```bash
./install-map-system.sh --dry-run
./install-map-system.sh --yes
./install-map-system.sh --yes --skip-apt
./install-map-system.sh --yes --skip-hcom
./install-map-system.sh --yes --skip-wezterm
./install-map-system.sh --yes --skip-desktop
./install-map-system.sh --yes --skip-venv
```

Use environment overrides when a machine needs non-standard locations:

```bash
MAP_INSTALL_BIN_DIR="$HOME/bin" ./install-map-system.sh --yes
MAP_INSTALL_WEZTERM_DIR="$HOME/.config/wezterm" ./install-map-system.sh --yes
MAP_INSTALL_DESKTOP_DIR="$HOME/.local/share/applications" ./install-map-system.sh --yes
MAP_INSTALL_HCOM_VENV="$HOME/.local/share/hcom-venv" ./install-map-system.sh --yes
MAP_INSTALL_HCOM_PACKAGE="hcom" ./install-map-system.sh --yes
MAP_INSTALL_PROJECTS_DIR="$HOME/Projects" ./install-map-system.sh --yes
MAP_INSTALL_COMMAND_CENTER_UI_DIR="$HOME/Projects/CommandCenterUI" ./install-map-system.sh --yes
```

## Safety Notes

The installer does not remove files. When it needs to replace an existing command-center file, it copies the old file to the backup directory first.

The installer does not migrate old hard-coded paths in unrelated files. It generates new user-local scripts and configs from templates using the current clone path.

The installer does not launch background local model helpers. Local/Ollama helper work should only be started for a clear bounded task and should report results through hcom or a durable MAP artifact.

CommandCenterUI is installed from the bundled source under `MAP_System/templates/install/command-center-ui/`. The installed `command-center-ui` launcher exports `COMMAND_CENTER_UI_WORKSPACE` to this MAP checkout before starting the UI. ProjectUpdater is not a separate download; it ships in this repository under `Projects/ProjectUpdater/`.

## Troubleshooting

If `ai-command-center-lab` says `hcom` is missing, re-run the installer and verify:

```bash
./install-map-system.sh --yes
hcom --version
hcom list
```

If the lab does not open on a Debian/Ubuntu-style system, re-run the installer and verify WezTerm:

```bash
./install-map-system.sh --yes
wezterm --version
```

If MAP Python commands fail, rebuild the venv:

```bash
rm -rf MAP_System/.venv
./install-map-system.sh --yes --skip-apt
```

If desktop launchers do not appear immediately, log out and back in, or start the lab from the terminal with:

```bash
ai-command-center-lab
```

If CommandCenterUI does not find MAP state, start it through the installed launcher so the workspace variable is set:

```bash
command-center-ui
```

If ProjectUpdater does not open, verify the app exists in the clone:

```bash
test -f Projects/ProjectUpdater/app/index.html
```
