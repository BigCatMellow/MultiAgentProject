# Review: TASK-139 Fix CommandCenterUI ProjectUpdater open/status runtime

task_id: TASK-139
task_owner: codex-lab-neko
reviewer: claude-lab-vino
date: 2026-07-04

## Verdict

APPROVED

No BLOCKER or REQUIRED findings.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | Live curl of `GET /api/project-updater/status` on the running server (which was restarted after this diff landed, so it's serving current code) returns 200, `app_exists: true`. |
| 2 | PASS | `src/chat.html`'s file-anchor was replaced with a real `<button id="project-updater-open">`; `chat.js`'s click handler now POSTs to the new same-origin `/api/project-updater/open` endpoint instead of relying on a `file://` navigation (which browsers commonly block from an http(s) origin). Live curl: same-origin POST → `{"ok": true, "opened": ".../ProjectUpdater/app/index.html"}`. |
| 3 | PASS | `open_project_updater()` (`app/server.py`) launches only the fixed module-level constant `PROJECT_UPDATER_APP` via `subprocess.Popen(["xdg-open", str(PROJECT_UPDATER_APP)], ...)` — argv list form (no shell), no request-body field is read into the command at all, so there is no user-suppliable path or command-injection surface. `read_project_updater_status()` is unchanged from TASK-135 and still only reads the fixed export file path; no browser localStorage access (not possible from a Python backend regardless). |
| 4 | PASS | `python3 -c "import ast; ast.parse(...)"` on `server.py`: OK. `node --check src/chat.js`: OK. Live endpoint behavior verified directly (see Verification). `validate_task_graph.py`: pass. `validate_events.py`: errors=0, warnings=33 (unchanged baseline). `run_tests.sh`: 33/33 pass. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/app/server.py` (diff)
- `/home/home/Projects/CommandCenterUI/src/chat.js` (diff)
- `/home/home/Projects/CommandCenterUI/src/chat.html` (diff)
- `/home/home/Projects/CommandCenterUI/src/chat.css` (diff)
- `/home/home/Projects/CommandCenterUI/README.md` (diff)

## Security Review (network-facing/write-capable change, per IDEA-0004's second-pass convention)

- **Command injection**: not possible — `subprocess.Popen` is called with a list argv (`["xdg-open", str(PROJECT_UPDATER_APP)]`), not `shell=True`, and the single argument is a fixed `Path` constant computed from `WORKSPACE`, never from the request body or query string. The POST handler doesn't even look at `payload` for this route (`open_project_updater()` takes no arguments).
- **CSRF / cross-origin trigger**: the new route is gated by the same `same_origin_request()` check already used by every other write endpoint (`/api/hcom/send`, `/api/chat/send`, etc.) — no new trust boundary was introduced, it reuses the existing one. Verified live: same-origin POST succeeds (`ok: true`), a POST with `Origin: http://evil.example.com` is rejected with `403`.
- **GET-triggerable side effect**: the open action is POST-only. `GET /api/project-updater/open` returns `404` (not present in `do_GET`'s route table at all), so it can't be triggered by a passive cross-origin `<img>`/`<link>` GET the way a GET-based action could be.
- **Path/argument exposure**: the endpoint returns the absolute local path in its JSON response (`opened`, and `app_path`/`app_url` from the status endpoint) — this is same-origin-only information about the local ProjectUpdater install path, consistent with what TASK-135 already exposed; not a new disclosure.
- **Payload size guard**: the existing `Content-Length > 12000` rejection in `do_POST` applies uniformly to this route too, since the check happens before the path dispatch.

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-vino` is not task owner `codex-lab-neko`, and I have no authorship stake in this diff.
- PASS: output_paths match what was touched.
- PASS: no new non-localhost dependency; `xdg-open` is a local desktop-launcher call, not a network call.
- PASS: `chat.js` still uses `textContent` assignment (not `innerHTML`) for all export/status-derived strings — unchanged from TASK-135, still safe.

## Verification

- `python3 -c "import ast; ast.parse(open('app/server.py').read())"` — OK.
- `node --check src/chat.js` — OK.
- Confirmed the currently-running CommandCenterUI server (PID started 23:08:41, after this diff's files were last modified at 23:06-23:07) is actually serving this code, then ran live checks against it:
  - `GET /api/project-updater/status` → 200, `app_exists: true`.
  - `POST /api/project-updater/open` with a matching `Origin` header → 200, `{"ok": true, "opened": ".../index.html"}` (this did launch the real local ProjectUpdater HTML file via `xdg-open` as a side effect of verification — expected and harmless, matches the reviewed behavior exactly).
  - `POST /api/project-updater/open` with `Origin: http://evil.example.com` → 403.
  - `GET /api/project-updater/open` → 404.
- `bash MAP_System/scripts/run_tests.sh` — 33/33 pass.
- `python3 MAP_System/scripts/validate_task_graph.py` — pass.
- `python3 MAP_System/scripts/validate_events.py` — errors=0, warnings=33 (unchanged).

## Notes

This closes the runtime bug from the operator's report (server needed restarting to
pick up TASK-135's original code, plus `file://` navigation from an `http://`
origin doesn't reliably work in modern browsers — the new same-origin POST +
`xdg-open` approach sidesteps that entirely). No further action needed on my
side; the server currently running already has this code loaded and verified live.
