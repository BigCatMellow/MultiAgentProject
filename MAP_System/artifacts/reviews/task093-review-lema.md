# Review Record: TASK-093

## Header

```text
task_id:      TASK-093
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
| 1 | Each chat message has an ergonomic quote/reply affordance that sends hcom `reply_to` with visible quoted context in the composer and feed | PASS | `src/chat.js` adds per-message `reply` buttons, a composer reply chip, and sends `body.reply_to` through `/api/chat/send`; `app/server.py` forwards it as `hcom send --reply-to`. Live `GET /api/chat?limit=1&since=17611` returned message `17612` with `reply_to: "17263"` and quote context for message `17263`. |
| 2 | Attention inbox lists open operator-action messages, including hcom `intent=request` and direct operator mentions, with jump-to-message and reply actions | PASS | `app/server.py` exposes read-only `GET /api/attention`, filters to `sender_kind == "instance"`, `intent == "request"`, mentions of `command-center`/`bigboss`, not answered by a `reply_to`, and live senders. `src/chat.js` renders the "Needs you" list, click-to-jump, reply start, and client-side dismiss. Live `/api/attention` returned current unresolved operator-addressed request items. |
| 3 | Original message text remains the source of record; quotes are presentation/context and cannot silently alter hcom history | PASS | Quotes are fetched from read-only hcom DB rows by event id in `attach_quotes()` and rendered via `textContent`; the send path stores only `reply_to` plus operator-authored body. No mutation of historical hcom messages was added. |
| 4 | Feature works with existing polling and does not add an unsafe write endpoint beyond the existing guarded chat send path | PASS | `do_POST` remains limited to `/api/hcom/send`, `/api/chat/send`, `/api/lab/start`, and `/api/term/inject`; `POST /api/attention` returns 404. Same-origin rejection for `/api/chat/send` still returns 403. Invalid `reply_to` returns 400. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/README.md`
- `/home/home/Projects/CommandCenterUI/app/server.py`
- `/home/home/Projects/CommandCenterUI/src/chat.css`
- `/home/home/Projects/CommandCenterUI/src/chat.html`
- `/home/home/Projects/CommandCenterUI/src/chat.js`
- `MAP_System/tasks/TASK-093.json`
- `MAP_System/tasks/TASK-094.json`
- `MAP_System/workflow/task_graph.json`

## Forbidden Changes

- No new write-capable attention endpoint.
- No hidden server-side dismissal or mutation of hcom history.
- No bypass of existing same-origin checks for chat sends.
- No new broad command execution or approval surface.

## Notes

The attention inbox intentionally keeps old unanswered requests from currently
live senders visible until replied to or client-dismissed. That matches the
submitted live-senders-only rule; it may surface historical unresolved operator
decisions, which is useful for TASK-094's follow-up approval center.

## Verification

```bash
python3 MAP_System/migration/export_to_files.py --db MAP_System/map.db
node --check /home/home/Projects/CommandCenterUI/src/chat.js
python3 - <<'PY'
import ast
from pathlib import Path
ast.parse(Path('/home/home/Projects/CommandCenterUI/app/server.py').read_text(encoding='utf-8'))
print('server.py ast-ok')
PY
python3 MAP_System/scripts/validate_shared_state.py
```

Live endpoint checks:

```text
GET /api/chat?limit=1&since=17611 -> message 17612 includes reply_to 17263 and quote context
GET /api/attention                -> ok, returns unresolved request items
POST /api/attention               -> 404 not found
POST /api/chat/send bad reply_to  -> 400
POST /api/chat/send evil Origin   -> 403
```
