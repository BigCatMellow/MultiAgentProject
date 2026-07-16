# Review Record: TASK-087

## Header

```text
task_id:      TASK-087
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
| 1 | App launches as its own window, not a plain browser tab | PASS | `run-command-center-app.sh` now dispatches to `app/window.py`; wrapper starts/reuses the localhost server, opens GTK/WebKit, and falls back to Firefox. `bash -n` and in-memory Python compilation passed. |
| 2 | Chat feed shows live hcom messages and agent presence, updating automatically | PASS | Live `GET /api/chat?limit=3` returned hcom messages; `GET /api/presence` returned active room agents; `chat.js` polls chat every 2s and presence every 8s. |
| 3 | Sending requires type text + Enter, with server-side @mention parsing and broadcast fallback | PASS | `chat.html/js` exposes one textarea composer; Enter submits, Shift+Enter newline. `hcom send --help` confirms recipient-less broadcast is supported. Server-side `MENTION_RE` is authoritative. |
| 4 | Sends are attributed to external operator identity `command-center`, never an agent identity | PASS | Claude's event `16453` and reviewer smoke event `16493` both show `from=command-center`, `sender_kind=external`; reviewer POST returned `sent_as=command-center`. |
| 5 | Server stays localhost-only with same-origin POST guard; hcom.db opened read-only | PASS | Live server at `127.0.0.1:8765`; launcher hardcodes host `127.0.0.1`; cross-origin POST returned 403; invalid sends return 400; app read connection rejected write attempt with `OperationalError attempt to write a readonly database`. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/app/server.py`
- `/home/home/Projects/CommandCenterUI/app/window.py`
- `/home/home/Projects/CommandCenterUI/run-command-center-app.sh`
- `/home/home/Projects/CommandCenterUI/CommandCenterUI.desktop`
- `/home/home/Projects/CommandCenterUI/README.md`
- `/home/home/Projects/CommandCenterUI/src/chat.html`
- `/home/home/Projects/CommandCenterUI/src/chat.js`
- `/home/home/Projects/CommandCenterUI/src/chat.css`
- `/home/home/Projects/CommandCenterUI/artifacts/task087-validation.md`
- `MAP_System/tasks/TASK-087.json`

## Forbidden Changes

- No hidden/headless helper or background assistant added.
- No raw hcom DB writes; sends go through `hcom send`, reads use SQLite `mode=ro`.
- No agent impersonation for chat sends; attribution is external `command-center`.
- No default LAN exposure; launcher and wrapper use `127.0.0.1`.

## Security Second Pass

Scope: TASK-087 changes the write-capable send surface by adding `/api/chat/send`, defaulting to external `command-center` attribution, and reading `~/.hcom/hcom.db`.

- Authentication/attribution: chat sends use `hcom send --from command-center`, producing `sender_kind=external`. This avoids sending as `claude-*` or `codex-*` agent identities.
- CSRF/drive-by exposure: cross-origin browser POST with `Origin: http://evil.example` returned HTTP 403 before send handling. Same-origin POST is required for browser-originated sends.
- Injection: hcom invocation uses `subprocess.run([...])` argument lists, not shell strings. Message text follows `--`, so shell metacharacters are not interpreted by the server.
- Mention parsing: server-side `MENTION_RE` controls recipients; client regex is only autocomplete/display.
- hcom DB access: `hcom_connect()` uses `file:...hcom.db?mode=ro`; a write probe failed with readonly database.
- Path traversal: static file serving remains constrained under `SRC_DIR` via `relative_to`.
- Failure modes: malformed `since`/`limit`, empty text, bad `reply_to`, and cross-origin POSTs return 400/403 without sending.

Residual risk: no-Origin/no-Referer local POSTs are still accepted by the same-origin helper. This remains a localhost/local-process risk rather than browser CSRF; local processes with this user account can already invoke `hcom send` directly. Not blocking.

## Verification Commands

```bash
python3 MAP_System/migration/export_to_files.py --db MAP_System/map.db
python3 - <<'PY'
from pathlib import Path
for path in ['/home/home/Projects/CommandCenterUI/app/server.py','/home/home/Projects/CommandCenterUI/app/window.py']:
    compile(Path(path).read_text(), path, 'exec')
PY
bash -n /home/home/Projects/CommandCenterUI/run-command-center-app.sh /home/home/Projects/CommandCenterUI/launch-command-center-ui.sh
desktop-file-validate /home/home/Projects/CommandCenterUI/CommandCenterUI.desktop
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_events.py
python3 MAP_System/scripts/validate_shared_state.py
```
