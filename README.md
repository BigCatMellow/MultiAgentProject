# MultiAgentProject

MAP is a local AI command-center workspace for coordinating agent sessions,
durable task files, hcom messaging, CommandCenterUI, and ProjectUpdater.

The GitHub repo is split into two top-level folders so a fresh install is easy
to find:

| Folder | Purpose |
|---|---|
| `Installer/` | Small bootstrap folder for a new PC. Download this if you only want the installer. |
| `Source/` | Full MAP source tree, including `MAP_System`, ProjectUpdater, CommandCenterUI installer templates, and the full installer. |

## Quick Install

On a fresh Linux PC, run:

```bash
curl -L https://raw.githubusercontent.com/BigCatMellow/MultiAgentProject/main/Installer/install.sh -o install-map.sh
chmod +x install-map.sh
./install-map.sh
```

Default install location:

```text
~/Projects/MultiAgentProject
```

Use a different location:

```bash
MAP_REPO_DIR="$HOME/MAP/MultiAgentProject" ./install-map.sh
```

## What The Installer Does

The bootstrap in `Installer/install.sh` installs minimal clone prerequisites,
clones or updates this repository, then runs:

```text
Source/MAP-System-Installer.run
```

The full installer sets up:

- hcom, installed user-locally when missing.
- WezTerm on Debian/Ubuntu-style systems through the official APT repo.
- MAP Python virtual environment.
- `ai`, `ai tell`, lab launchers, monitor helpers, and graph runner commands.
- CommandCenterUI bundled app plus `command-center-ui`.
- ProjectUpdater plus `project-updater`.
- Desktop launchers.

Credentials still require user action. Codex, Claude, Gemini, and model/API
provider logins cannot be safely automated by the installer.

## Preview First

To see what would happen without changing the machine:

```bash
curl -L https://raw.githubusercontent.com/BigCatMellow/MultiAgentProject/main/Installer/install.sh -o install-map.sh
chmod +x install-map.sh
./install-map.sh --dry-run
```

## After Install

Common commands:

```bash
command-center-ui
project-updater
ai-command-center-lab
ai status
ai tell "fresh install check"
```

## Full Source

Browse the full source here:

```text
Source/
```

Important source paths:

- `Source/MAP_System/` - reusable MAP system.
- `Source/Projects/ProjectUpdater/` - ProjectUpdater app.
- `Source/MAP_System/templates/install/command-center-ui/` - bundled CommandCenterUI.
- `Source/install-map-system.sh` - full installer implementation.
- `Source/MAP_System/docs/fresh-install.md` - detailed install guide.

