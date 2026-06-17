#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GIT_DIR="$ROOT/.map-git"

if [[ -d "$ROOT/.git" ]] && mountpoint -q "$ROOT/.git"; then
  echo "Detected .git mount point; using .map-git as the repository directory."
fi

if [[ ! -d "$GIT_DIR" ]]; then
  git init --bare "$GIT_DIR"
  git --git-dir="$GIT_DIR" --work-tree="$ROOT" config core.bare false
  git --git-dir="$GIT_DIR" --work-tree="$ROOT" config core.worktree "$ROOT"
  git --git-dir="$GIT_DIR" --work-tree="$ROOT" symbolic-ref HEAD refs/heads/main
fi

echo "Git fallback is ready."
echo "Use: MAP_System/scripts/map-git status"
