# Review Record: TASK-088

## Header

```text
task_id:      TASK-088
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
| 1 | Composer/sidebar remain visible; only message feed scrolls | PASS | `chat.css` now sets `html, body { height: 100%; overflow: hidden; }`, `.shell { height: 100vh; overflow: hidden; }`, `.sidebar { min-height: 0; overflow-y: auto; }`, `.room { min-height: 0; }`, and `.feed { flex: 1; min-height: 0; overflow-y: auto; }`. Live `/chat.css` on `127.0.0.1:8765` serves these rules. |
| 2 | F5/Ctrl+R reloads page inside WebKit window | PASS | `window.py` imports `Gdk`, connects `key-press-event`, checks `Gdk.KEY_F5`, `Ctrl+r`, and `Ctrl+R`, then calls `view.reload_bypass_cache()`. In-memory Python compilation passed. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/src/chat.css`
- `/home/home/Projects/CommandCenterUI/app/window.py`
- `MAP_System/tasks/TASK-088.json`
- `MAP_System/workflow/task_graph.json`

## Forbidden Changes

- No server send-surface changes.
- No hcom DB access changes.
- No launcher identity or attribution changes.
- No hidden/headless helper added.

## Verification

```bash
python3 MAP_System/migration/export_to_files.py --db MAP_System/map.db
python3 - <<'PY'
from pathlib import Path
compile(Path('/home/home/Projects/CommandCenterUI/app/window.py').read_text(), '/home/home/Projects/CommandCenterUI/app/window.py', 'exec')
PY
bash -n /home/home/Projects/CommandCenterUI/run-command-center-app.sh /home/home/Projects/CommandCenterUI/launch-command-center-ui.sh
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_events.py
python3 MAP_System/scripts/validate_shared_state.py
```

Live asset check:

- `GET /chat.css` returned 200 and included the scrollframe rules.
