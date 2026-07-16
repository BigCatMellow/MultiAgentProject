# TASK-036 Local Assistant Health Test

Task: `TASK-036`
Date: 2026-06-29
Owner: `codex-live`

## Implemented

- Added `MAP_System/scripts/local_assistant_health.py`.
- Added `ai local-health` and `ai local-assistant-health` command-center aliases.
- The command is read-only:
  - does not start Ollama;
  - does not start Aider;
  - does not launch helpers;
  - does not register local models as core agents.

## Checks

Command:

```bash
python3 MAP_System/scripts/local_assistant_health.py --json --timeout 2
```

Observed:

- `status`: `ok`
- `runtime_status`: `helper-capability-only`
- `core_agent_status`: `not-registered`
- `starts_sessions`: `false`
- `ollama`: reachable
- Required models available:
  - `llama3.2:3b`
  - `llama3.2:1b`
  - `qwen2.5-coder:3b`
  - `qwen2.5-coder:1.5b`
  - `gemma3:4b`
- `aider`: available
- Aider version: `aider 0.86.2`

Command:

```bash
PROJECT_DIR=/home/home/Downloads/MultiAgentProject MAP_System/scripts/ai-command-center-cli local-health
```

Observed:

- printed the same read-only health summary;
- did not add local assistant start wrappers.

Command:

```bash
python3 -m py_compile MAP_System/scripts/local_assistant_health.py
python3 MAP_System/scripts/validate_task_graph.py
```

Observed:

- py_compile passed;
- task graph validation passed.

## Policy Check

`MAP_System/shared/current-state.md` still states local Ollama models and Aider
are helper capabilities, not registered core agents.

## Improvements Checked

Implemented: HPOM can now cheaply inspect local assistant capability before
assigning work, reducing subscription-token waste.

Recommended: add wrappers only after a specific local-assistant task proves a
manual workflow is useful and visible.

Not changed: local models are not core agents; no local assistant session launch
command was added.
