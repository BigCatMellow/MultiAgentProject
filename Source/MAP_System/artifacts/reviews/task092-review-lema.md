# Review Record: TASK-092

## Header

```text
task_id:      TASK-092
reviewer:     codex-lab-lema
review_date:  2026-07-02
task_owner:   claude-lab-zaro
```

Reviewer != owner. Independence check passes.

## Verdict

```text
CHANGES_REQUESTED
```

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Agent messages gain one-sentence plain-English gists produced by local Ollama, appearing asynchronously without blocking chat delivery | PASS | `app/server.py` starts a background `Summarizer` thread, queues eligible messages during `/api/chat`, calls `http://127.0.0.1:11434/api/generate` by default with `llama3.2:3b`, and live `/api/summaries?since=0` returned cached summaries while `/api/chat?limit=5` continued returning normally. |
| 2 | Original verbatim text is one click away and clearly distinguished from the paraphrase | PASS | `src/chat.js` renders `msg.summary` as `.gist`, then a `≈ summarized · show original` button, then the original `msg.text` in a hidden `.raw-text` block; `src/chat.css` has `[hidden] { display: none !important; }` so the toggle remains reliable. |
| 3 | Operator/system messages are never paraphrased | FAIL | `Summarizer.eligible()` only excludes `OPERATOR_NAME` and `[hcom-events]`; it does not require `sender_kind == "instance"`. Any long non-default external sender or system sender such as `[hcom-launcher]` would be eligible, which violates the task's agent-only rule. |
| 4 | Feature degrades gracefully when Ollama is down; sidebar toggle disables it entirely | PASS | Failures are caught in `Summarizer._worker()` and raw messages remain the default when no `summary` exists. `src/chat.html` exposes the sidebar checkbox and `src/chat.js` persists `localStorage.gists`, bypasses summary polling when disabled, and re-renders raw bubbles. |
| 5 | Summaries are cached per event id and each message summarized at most once across restarts | PASS | `runtime/summaries.json` exists, is keyed by hcom event id, and `Summarizer.enqueue()` skips ids already cached, queued, or failed twice. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/README.md`
- `/home/home/Projects/CommandCenterUI/app/server.py`
- `/home/home/Projects/CommandCenterUI/src/chat.css`
- `/home/home/Projects/CommandCenterUI/src/chat.html`
- `/home/home/Projects/CommandCenterUI/src/chat.js`
- `/home/home/Projects/CommandCenterUI/runtime/summaries.json`
- `MAP_System/tasks/TASK-092.json`
- `MAP_System/workflow/task_graph.json`

## Forbidden Changes

- No new POST/write surface for summaries.
- No client-controlled Ollama endpoint.
- No replacement of verbatim hcom message text as the source of record.
- No local-model authority over review, approval, or task completion.

## Required Fix

Require agent-instance messages before a summary is generated or displayed.
Recommended server-side fix:

```python
if msg.get("sender_kind") != "instance":
    return False
```

Recommended UI defense-in-depth: only render a `msg.summary` when
`msg.sender_kind === "instance"` in addition to the existing operator check.

## Verification

```bash
python3 MAP_System/migration/export_to_files.py --db MAP_System/map.db
python3 MAP_System/scripts/map_task.py show TASK-092
node --check /home/home/Projects/CommandCenterUI/src/chat.js
python3 - <<'PY'
import ast
from pathlib import Path
ast.parse(Path('/home/home/Projects/CommandCenterUI/app/server.py').read_text(encoding='utf-8'))
print('server.py ast-ok')
PY
```

Live endpoint checks:

```text
GET /api/chat?limit=5        -> ok, includes messages and operator
GET /api/summaries?since=0   -> ok, includes cached summaries
POST /api/summaries          -> 404 not found
```

Note: no `/home/home/Projects/CommandCenterUI/artifacts/task092-validation.md`
artifact was present during review.
