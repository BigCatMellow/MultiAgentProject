#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${MAP_REPO_URL:-https://github.com/BigCatMellow/MultiAgentProject.git}"
REPO_DIR="${MAP_REPO_DIR:-$HOME/Projects/MultiAgentProject}"
BRANCH="${MAP_REPO_BRANCH:-main}"

DRY_RUN=0
SKIP_APT=0

usage() {
  cat <<EOF
Usage: ./install.sh [options] [-- extra installer args]

Bootstrap MAP on a fresh PC by cloning/updating the repository and running
Source/MAP-System-Installer.run.

Options:
  --dry-run       Show actions and pass --dry-run to the repo installer
  --skip-apt      Do not install clone prerequisites with apt
  --help          Show this help

Environment:
  MAP_REPO_URL      default: $REPO_URL
  MAP_REPO_DIR      default: $REPO_DIR
  MAP_REPO_BRANCH   default: $BRANCH
EOF
}

log() {
  printf '%s\n' "$*"
}

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] %s\n' "$*"
  else
    "$@"
  fi
}

ensure_clone_prereqs() {
  if command -v git >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
    return 0
  fi

  if [ "$SKIP_APT" -eq 1 ]; then
    log "Missing git or python3, and --skip-apt was set."
    return 1
  fi

  if ! command -v apt-get >/dev/null 2>&1; then
    log "Missing git or python3. Install them first, then rerun this script."
    return 1
  fi

  run sudo apt-get update
  run sudo apt-get install -y git python3 ca-certificates
}

clone_or_update_repo() {
  if [ -d "$REPO_DIR/.git" ]; then
    log "Updating existing checkout: $REPO_DIR"
    run git -C "$REPO_DIR" fetch origin "$BRANCH"
    run git -C "$REPO_DIR" checkout "$BRANCH"
    run git -C "$REPO_DIR" pull --ff-only origin "$BRANCH"
    return 0
  fi

  if [ -e "$REPO_DIR" ]; then
    log "Target exists but is not a git checkout: $REPO_DIR"
    return 1
  fi

  run mkdir -p "$(dirname "$REPO_DIR")"
  run git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
}

run_repo_installer() {
  installer="$REPO_DIR/Source/MAP-System-Installer.run"
  if [ ! -x "$installer" ]; then
    log "Installer not found or not executable: $installer"
    return 1
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    run "$installer" --dry-run "$@"
  else
    run "$installer" "$@"
  fi
}

extra_args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --skip-apt)
      SKIP_APT=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      extra_args=("$@")
      break
      ;;
    *)
      extra_args+=("$1")
      ;;
  esac
  shift
done

log "MAP repo URL: $REPO_URL"
log "MAP repo dir: $REPO_DIR"
log "MAP branch: $BRANCH"

ensure_clone_prereqs
clone_or_update_repo
run_repo_installer "${extra_args[@]}"
