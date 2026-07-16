#!/usr/bin/env bash
set -euo pipefail

HCOM="/home/home/.local/bin/hcom"
PROJECT_DIR="/home/home/Downloads/MultiAgentProject"

cd "$PROJECT_DIR"

# Launch agents via hcom so they use the configured terminal (wezterm-tab).
# wezterm-tab is a managed terminal — hcom can open and close the tab,
# which means agents get a visible tab for approval prompts rather than
# running silently headless.
"$HCOM" 1 claude --tag claude
sleep 0.5
"$HCOM" 1 codex --tag codex
sleep 0.5
"$HCOM" 1 gemini --tag gemini
