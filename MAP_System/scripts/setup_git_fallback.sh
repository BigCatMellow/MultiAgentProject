#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Normal root Git is available."
  echo "Use: git status"
  echo "Or:  MAP_System/scripts/map-git status"
  exit 0
fi

echo "No root Git repository found at $ROOT." >&2
echo "Run: git -C \"$ROOT\" init -b main" >&2
exit 1
