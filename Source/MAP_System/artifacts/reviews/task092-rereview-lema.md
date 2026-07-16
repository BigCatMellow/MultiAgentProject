# Rereview Record: TASK-092

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
APPROVED
```

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Agent messages gain one-sentence plain-English gists produced by the local Ollama model, appearing within ~30s without blocking chat delivery | PASS | `app/server.py` queues eligible messages during `/api/chat` and the `Summarizer` thread calls local Ollama at `http://127.0.0.1:11434/api/generate` by default with `llama3.2:3b`. Live `/api/chat?limit=20` returned normally while `/api/summaries?since=0` returned cached summaries. |
| 2 | Original verbatim text always one click away and clearly distinguished from the paraphrase; operator/system messages never paraphrased | PASS | `src/chat.js` renders summaries only when `msg.sender_kind === "instance"` and keeps the original in a `≈ summarized · show original` toggle. Rework fixed the blocking finding: `Summarizer.eligible()` now requires `msg.get("sender_kind") == "instance"` before any message can be queued. Direct predicate checks returned false for `[hcom-launcher]`/system, `command-center`/external, and another external sender; true only for a long instance message. |
| 3 | Feature degrades gracefully when Ollama is down; sidebar toggle disables it entirely | PASS | `Summarizer._worker()` catches model failures and leaves raw messages in place when no summary exists. `src/chat.html` exposes the sidebar checkbox and `src/chat.js` persists `localStorage.gists`, skips summary polling when disabled, and re-renders bubbles raw. |
| 4 | Summaries cached per event id; each message summarized at most once across restarts | PASS | `runtime/summaries.json` is keyed by hcom event id, `Summarizer.get()` reads by id, and `Summarizer.enqueue()` skips ids already cached, queued, or failed twice. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/README.md`
- `/home/home/Projects/CommandCenterUI/app/server.py`
- `/home/home/Projects/CommandCenterUI/src/chat.css`
- `/home/home/Projects/CommandCenterUI/src/chat.html`
- `/home/home/Projects/CommandCenterUI/src/chat.js`
- `/home/home/Projects/CommandCenterUI/runtime/summaries.json`
- `MAP_System/artifacts/reviews/task092-review-lema.md`
- `MAP_System/tasks/TASK-092.json`
- `MAP_System/workflow/task_graph.json`

## Forbidden Changes

- No new POST/write surface for summaries.
- No client-controlled Ollama endpoint.
- No paraphrasing of operator, external, launcher, or system messages.
- No replacement of verbatim hcom message text as the source of record.
- No local-model authority over review, approval, or task completion.

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
GET /api/chat?limit=20       -> ok, includes instance messages with summaries
GET /api/summaries?since=0   -> ok, summary cache available
POST /api/summaries          -> 404 not found
```

Direct eligibility checks:

```text
[hcom-launcher] / system       -> False
command-center / external      -> False
other-operator / external      -> False
lema / instance, long message   -> True
lema / instance, short message  -> False
```
