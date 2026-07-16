# MAP Fresh Installer

This folder is the easy-download entry point for a new PC.

Use `install.sh` when you do not already have the full MAP repository cloned.
It installs the minimum clone prerequisites, clones or updates:

```text
https://github.com/BigCatMellow/MultiAgentProject
```

Then it runs the full repo installer:

```text
Source/MAP-System-Installer.run
```

Raw download URL:

```text
https://raw.githubusercontent.com/BigCatMellow/MultiAgentProject/main/Installer/install.sh
```

## Quick Start

```bash
chmod +x install.sh
./install.sh
```

Default install location:

```text
~/Projects/MultiAgentProject
```

Override it:

```bash
MAP_REPO_DIR="$HOME/MAP/MultiAgentProject" ./install.sh
```

## What The Full Installer Adds

- MAP repository checkout.
- hcom, installed user-locally when missing.
- WezTerm, installed through the official APT repo on Debian/Ubuntu systems.
- MAP Python venv.
- `ai`, `ai tell`, lab launchers, monitor helpers, and graph runner commands.
- CommandCenterUI bundled app and `command-center-ui` launcher.
- ProjectUpdater and `project-updater` launcher.
- Desktop launchers.

Credentials still require user action: Codex, Claude, Gemini, and any model/API
provider login cannot be safely automated.
