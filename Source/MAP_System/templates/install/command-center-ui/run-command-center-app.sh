#!/usr/bin/env bash
set -euo pipefail

# Launches the AI Command Center as its own window (GTK/WebKit, firefox
# fallback), starting the localhost server if needed. Use --server-only to
# run just the backend (old behavior, e.g. for headless/service use).

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
host="127.0.0.1"
port="${COMMAND_CENTER_UI_PORT:-8765}"

if [[ "${1:-}" == "--server-only" ]]; then
  agent_name="${COMMAND_CENTER_UI_AGENT_NAME:-browser}"
  echo "CommandCenterUI server: http://$host:$port/"
  exec python3 "$root/app/server.py" --host "$host" --port "$port" --agent-name "$agent_name"
fi

exec python3 "$root/app/window.py"
