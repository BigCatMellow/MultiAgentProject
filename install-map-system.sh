#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
TEMPLATE_ROOT="$REPO_ROOT/MAP_System/templates/install"
BIN_DIR="${MAP_INSTALL_BIN_DIR:-$HOME/.local/bin}"
WEZTERM_DIR="${MAP_INSTALL_WEZTERM_DIR:-$HOME/.config/wezterm}"
DESKTOP_DIR="${MAP_INSTALL_DESKTOP_DIR:-$HOME/.local/share/applications}"
STATE_DIR="${MAP_INSTALL_STATE_DIR:-$HOME/.local/state/map-install}"
BACKUP_DIR="$STATE_DIR/backups/$(date +%Y%m%d-%H%M%S)"
HCOM_VENV="${MAP_INSTALL_HCOM_VENV:-$HOME/.local/share/hcom-venv}"
HCOM_PACKAGE="${MAP_INSTALL_HCOM_PACKAGE:-hcom}"
PROJECTS_DIR="${MAP_INSTALL_PROJECTS_DIR:-$HOME/Projects}"
COMMAND_CENTER_UI_DIR="${MAP_INSTALL_COMMAND_CENTER_UI_DIR:-$PROJECTS_DIR/CommandCenterUI}"

DRY_RUN=1
YES=0
SKIP_APT=0
SKIP_HCOM=0
SKIP_WEZTERM=0
SKIP_DESKTOP=0
SKIP_VENV=0

export PATH="$BIN_DIR:$PATH"

usage() {
  cat <<EOF
Usage: ./install-map-system.sh [options]

Fresh-install bootstrap for the MAP AI Command Center.

Options:
  --dry-run          Show planned actions only (default)
  --yes             Apply changes and install files
  --skip-apt        Do not attempt apt package installation
  --skip-hcom       Do not install hcom when missing
  --skip-wezterm    Do not install WezTerm when missing
  --skip-desktop    Do not install desktop launcher entries
  --skip-venv       Do not create/update MAP_System/.venv
  --help            Show this help

Environment overrides:
  MAP_INSTALL_BIN_DIR       default: $HOME/.local/bin
  MAP_INSTALL_WEZTERM_DIR   default: $HOME/.config/wezterm
  MAP_INSTALL_DESKTOP_DIR   default: $HOME/.local/share/applications
  MAP_INSTALL_STATE_DIR     default: $HOME/.local/state/map-install
  MAP_INSTALL_HCOM_VENV     default: $HOME/.local/share/hcom-venv
  MAP_INSTALL_HCOM_PACKAGE  default: hcom
  MAP_INSTALL_PROJECTS_DIR  default: $HOME/Projects
  MAP_INSTALL_COMMAND_CENTER_UI_DIR
                            default: $HOME/Projects/CommandCenterUI
EOF
}

log() {
  printf '%s\n' "$*"
}

plan() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] %s\n' "$*"
  else
    printf '%s\n' "$*"
  fi
}

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] %s\n' "$*"
  else
    "$@"
  fi
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

backup_existing() {
  target="$1"
  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    return 0
  fi
  rel="${target#$HOME/}"
  backup="$BACKUP_DIR/$rel"
  plan "Back up $target to $backup"
  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$(dirname "$backup")"
    cp -a "$target" "$backup"
  fi
}

render_template() {
  src="$1"
  dst="$2"
  mode="$3"
  tmp="$(mktemp)"
  sed \
    -e "s|__PROJECT_DIR__|$REPO_ROOT|g" \
    -e "s|__HOME__|$HOME|g" \
    -e "s|__LOCAL_BIN__|$BIN_DIR|g" \
    -e "s|__COMMAND_CENTER_UI_DIR__|$COMMAND_CENTER_UI_DIR|g" \
    "$src" > "$tmp"

  if [ -e "$dst" ] && cmp -s "$tmp" "$dst"; then
    plan "Keep unchanged $dst"
    rm -f "$tmp"
    return 0
  fi

  backup_existing "$dst"
  plan "Install $dst"
  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$(dirname "$dst")"
    install -m "$mode" "$tmp" "$dst"
  fi
  rm -f "$tmp"
}

install_bin_template() {
  name="$1"
  render_template "$TEMPLATE_ROOT/bin/$name" "$BIN_DIR/$name" 0755
}

install_wezterm_template() {
  name="$1"
  render_template "$TEMPLATE_ROOT/wezterm/$name" "$WEZTERM_DIR/$name" 0644
}

install_desktop_template() {
  name="$1"
  render_template "$TEMPLATE_ROOT/desktop/$name" "$DESKTOP_DIR/$name" 0644
}

install_command_center_ui_bundle() {
  src="$TEMPLATE_ROOT/command-center-ui"
  dst="$COMMAND_CENTER_UI_DIR"
  if [ ! -d "$src" ]; then
    log "CommandCenterUI bundle not found at $src; skipping."
    return 0
  fi

  backup_existing "$dst"
  plan "Install bundled CommandCenterUI to $dst"
  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$dst" "$dst/runtime"
    cp -a "$src/." "$dst/"
    chmod +x "$dst/run-command-center-app.sh" "$dst/launch-command-center-ui.sh"
    cat > "$dst/CommandCenterUI.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=AI Command Center
Comment=Chat with and monitor the AI Command Center Lab
Exec=$COMMAND_CENTER_UI_DIR/run-command-center-app.sh
Terminal=false
Categories=Utility;
EOF
  fi
}

install_packages() {
  if [ "$SKIP_APT" -eq 1 ]; then
    log "Skipping apt dependency installation."
    return 0
  fi

  if ! command_exists apt-get; then
    log "apt-get not found; skipping Debian/Ubuntu package installation."
    return 0
  fi

  packages="git python3 python3-venv python3-pip curl ca-certificates ripgrep desktop-file-utils gnupg"
  plan "Ensure OS packages: $packages"
  if [ "$DRY_RUN" -eq 0 ]; then
    sudo apt-get update
    sudo apt-get install -y $packages
  fi
}

install_hcom() {
  if [ "$SKIP_HCOM" -eq 1 ]; then
    log "Skipping hcom installation."
    return 0
  fi

  if command_exists hcom; then
    log "hcom already present: $(command -v hcom)"
    return 0
  fi

  if ! command_exists python3; then
    log "python3 is required before hcom can be installed."
    return 1
  fi

  plan "Install hcom from PyPI package '$HCOM_PACKAGE' into $HCOM_VENV"
  plan "Link $BIN_DIR/hcom to $HCOM_VENV/bin/hcom"
  if [ "$DRY_RUN" -eq 0 ]; then
    python3 -m venv "$HCOM_VENV"
    "$HCOM_VENV/bin/python" -m pip install --upgrade pip
    "$HCOM_VENV/bin/python" -m pip install --upgrade "$HCOM_PACKAGE"
    mkdir -p "$BIN_DIR"
    backup_existing "$BIN_DIR/hcom"
    ln -sfn "$HCOM_VENV/bin/hcom" "$BIN_DIR/hcom"
  fi
}

install_wezterm() {
  if [ "$SKIP_WEZTERM" -eq 1 ]; then
    log "Skipping WezTerm installation."
    return 0
  fi

  if command_exists wezterm; then
    log "WezTerm already present: $(command -v wezterm)"
    return 0
  fi

  if [ "$SKIP_APT" -eq 1 ]; then
    log "WezTerm missing, but --skip-apt was set."
    return 0
  fi

  if ! command_exists apt-get; then
    log "WezTerm automatic install currently supports Debian/Ubuntu-style apt systems. See MAP_System/docs/fresh-install.md for other platforms."
    return 0
  fi

  plan "Install WezTerm using the official WezTerm APT repository"
  if [ "$DRY_RUN" -eq 0 ]; then
    tmp_key="$(mktemp)"
    curl -fsSL https://apt.fury.io/wez/gpg.key -o "$tmp_key"
    sudo gpg --yes --dearmor -o /usr/share/keyrings/wezterm-fury.gpg "$tmp_key"
    rm -f "$tmp_key"
    printf '%s\n' 'deb [signed-by=/usr/share/keyrings/wezterm-fury.gpg] https://apt.fury.io/wez/ * *' | sudo tee /etc/apt/sources.list.d/wezterm.list >/dev/null
    sudo chmod 644 /usr/share/keyrings/wezterm-fury.gpg
    sudo apt-get update
    sudo apt-get install -y wezterm
  fi
}

install_venv() {
  if [ "$SKIP_VENV" -eq 1 ]; then
    log "Skipping MAP_System/.venv setup."
    return 0
  fi

  if [ ! -d "$REPO_ROOT/MAP_System/.venv" ]; then
    plan "Create MAP_System/.venv"
    run python3 -m venv "$REPO_ROOT/MAP_System/.venv"
  fi

  if [ -f "$REPO_ROOT/MAP_System/requirements.txt" ]; then
    plan "Install MAP_System Python requirements"
    if [ "$DRY_RUN" -eq 0 ]; then
      "$REPO_ROOT/MAP_System/.venv/bin/python" -m pip install -r "$REPO_ROOT/MAP_System/requirements.txt"
    fi
  else
    log "No MAP_System/requirements.txt found; leaving venv package set unchanged."
  fi
}

install_command_center_files() {
  for name in \
    ai \
    ai-command-center \
    ai-command-center-lab \
    ai-command-center-lab-codex \
    ai-command-center-lab-claude \
    ai-command-center-lab-librarian \
    ai-command-center-lab-shell \
    ai-command-center-lab-health \
    ai-command-center-lab-status \
    ai-command-center-monitor \
    command-center-ui \
    project-updater \
    ai-inbox \
    agent-status \
    agent-screens \
    agent-tabs \
    agent-deck \
    langgraph-run \
    start-agents; do
    install_bin_template "$name"
  done

  install_wezterm_template ai-command-center-lab.lua

  if [ "$SKIP_DESKTOP" -eq 0 ]; then
    for name in \
      ai-command-center-lab.desktop \
      ai-command-center-monitor.desktop \
      command-center-ui.desktop \
      project-updater.desktop \
      agent-tabs.desktop; do
      install_desktop_template "$name"
    done
    if command_exists update-desktop-database; then
      plan "Refresh desktop launcher database"
      run update-desktop-database "$DESKTOP_DIR"
    fi
  fi
}

print_check() {
  label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf '  ok      %s\n' "$label"
  else
    printf '  manual  %s\n' "$label"
  fi
}

health_summary() {
  log ""
  log "Post-install checks:"
  print_check "git" command_exists git
  print_check "python3" command_exists python3
  print_check "ripgrep (rg)" command_exists rg
  print_check "hcom CLI" command_exists hcom
  print_check "WezTerm" command_exists wezterm
  print_check "Codex CLI" command_exists codex
  print_check "Claude CLI" command_exists claude
  print_check "Gemini CLI" command_exists gemini
  if [ -f "$COMMAND_CENTER_UI_DIR/run-command-center-app.sh" ]; then
    printf '  ok      CommandCenterUI bundle\n'
  else
    printf '  manual  CommandCenterUI bundle\n'
  fi
  if [ -f "$REPO_ROOT/Projects/ProjectUpdater/app/index.html" ]; then
    printf '  ok      ProjectUpdater app\n'
  else
    printf '  manual  ProjectUpdater app\n'
  fi

  log ""
  log "Manual prerequisites that still require user action:"
  log "  - hcom first-run configuration if this is a brand-new user account"
  log "  - WezTerm manual install only on non-apt platforms"
  log "  - Codex/Claude/Gemini CLIs installed and authenticated if those agents will be used"
  log "  - Optional local model stack such as Ollama, only when a task needs it"

  log ""
  log "Try next:"
  log "  command-center-ui"
  log "  project-updater"
  log "  ai-command-center-lab"
  log "  ai status"
  log "  ai tell \"fresh install check\""
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --yes)
      DRY_RUN=0
      YES=1
      ;;
    --skip-apt)
      SKIP_APT=1
      ;;
    --skip-hcom)
      SKIP_HCOM=1
      ;;
    --skip-wezterm)
      SKIP_WEZTERM=1
      ;;
    --skip-desktop)
      SKIP_DESKTOP=1
      ;;
    --skip-venv)
      SKIP_VENV=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ "$YES" -eq 0 ]; then
  log "Running in dry-run mode. Re-run with --yes to install."
fi

if [ ! -d "$TEMPLATE_ROOT" ]; then
  printf 'Missing install templates: %s\n' "$TEMPLATE_ROOT" >&2
  exit 1
fi

log "MAP repo: $REPO_ROOT"
log "User bin: $BIN_DIR"
log "WezTerm config: $WEZTERM_DIR"
log "Desktop launchers: $DESKTOP_DIR"
log "hcom venv: $HCOM_VENV"
log "CommandCenterUI: $COMMAND_CENTER_UI_DIR"
log ""

install_packages
install_hcom
install_wezterm
install_venv
install_command_center_ui_bundle
install_command_center_files
health_summary
