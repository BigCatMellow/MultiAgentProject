# MultiAgentProject

MAP is a local AI command-center system. It gives one operator a durable,
file-backed workspace for running multiple AI coding agents, tracking their
work as tasks, coordinating them through hcom messages, and keeping the current
state visible through terminal and graphical command-center tools.

In short: MAP is the operating layer around your AI agents. It remembers what
is being worked on, who owns each task, what was decided, what still needs
review, and how to restart the whole setup on a fresh PC.

## What MAP Does

### Summary

MAP turns a loose set of AI terminals into a coordinated local system:

- It stores tasks, decisions, handoffs, reviews, events, and current state in
  durable files under `MAP_System/`.
- It uses hcom so agents and the operator can message, observe, spawn, and
  coordinate without relying on chat memory alone.
- It provides launchers for Codex, Claude, monitor tabs, health checks,
  CommandCenterUI, and ProjectUpdater.
- It keeps a SQLite-backed task graph and file mirrors so work can survive
  context resets, agent restarts, and machine moves.
- It includes an installer that rebuilds the command-center environment on a
  fresh Linux PC.

### Detailed View

MAP is built around a few practical ideas:

**Durable state instead of memory**

Agents do not rely only on conversation history. Important state is written to
files: task records, shared decisions, current-state notes, handoffs, event
logs, review artifacts, release checklists, and helper notes. This makes the
system recoverable after a model context reset or a terminal restart.

**Task ownership and review flow**

Work is tracked as MAP tasks. A task has an owner, status, acceptance criteria,
output paths, and validation evidence. The task graph and SQLite database help
prevent duplicate ownership and make it clear which tasks are ready, in
progress, submitted, approved, or released.

**Agent coordination**

MAP uses hcom as the live communication layer. Agents can send progress
updates, request operator decisions, inspect terminal screens, and coordinate
with other agents. The installed `ai` command wraps common actions like
`ai status`, `ai inbox`, `ai tell`, `ai codex`, and `ai claude`.

**Visible command center**

The system can open a WezTerm lab workspace with tabs for a shell, Codex,
Claude, librarian/helper work, and a monitor. The monitor is meant to keep
attention on useful progress and actual operator decisions, not routine noise.

**Graphical UI**

CommandCenterUI is bundled with the installer. It provides a local graphical
view for hcom chat, agent presence, MAP state, operator attention items,
terminal prompts, and ProjectUpdater access.

**Project tracking**

ProjectUpdater is included as a local app for tracking projects, goals,
references, notes, and project status. CommandCenterUI can open it and read
explicit status exports without taking ownership of browser-local data.

**Fresh install and portability**

The installer rebuilds the MAP environment on a new Linux machine. It installs
or checks hcom, WezTerm, Python venvs, user-local command scripts, desktop
launchers, CommandCenterUI, and ProjectUpdater. Machine-specific paths are
generated at install time instead of being hard-coded from the original PC.

**Safety boundaries**

MAP separates routine progress from decisions that need the operator. It
records decisions, avoids destructive actions unless explicitly approved, and
keeps credentials manual. Codex, Claude, Gemini, and API/model-provider logins
still require the user because those credentials should not be bundled into an
installer.

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
