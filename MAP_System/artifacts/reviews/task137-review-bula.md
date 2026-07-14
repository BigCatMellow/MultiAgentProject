# Review: TASK-137 Remove ProjectUpdater Areas Sidebar Section

task_id: TASK-137
reviewer: bula (visible helper, tag helper-review-task-137, spawned by codex-lab-neko)
task_owner: codex-lab-neko
implementation_author: claude-lab-vino (authored the `app/index.html` Areas-removal edit; codex-lab-neko added validator assertions and submitted)

## Verdict

APPROVED

## Independence Note

`claude-lab-vino` declined to review because they authored the `app/index.html`
Areas-removal edit before `codex-lab-neko` added validator assertions and
submitted the task (self-review conflict). I am an independent helper with no
prior authorship on this task's output paths.

## Acceptance Criteria

| # | Status | Evidence |
|---|---|---|
| 1 | PASS | `Projects/ProjectUpdater/app/index.html` sidebar (`#sidebar`, lines ~300-320) now has only two `.sb-heading` groups, "Views" and "Attention". No "Areas" heading, no `#areaList` element, and no dead `renderAreas`-style code remain (grep for `Areas`/`areaList`/`renderAreas` returns nothing). Validator confirms `sidebar_headings` == `["VIEWS", "ATTENTION"]` and `#areaList` count is 0. |
| 2 | PASS | Project area data and rendering remain intact: seed/demo data still carries `area` (lines 400-407), the add/edit forms still have `#newArea`/`#editArea` fields (lines 594, 858, 892), and project cards still render the `.pill.area` badge (line 465) and list-view area text (line 472). Search still filters by `p.area` (line 571). |
| 3 | PASS | Ran `/tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py` independently (not just trusting the submission log): result `"ok": true`, `"failures": []`, zero console errors, mobile and desktop checks all passed, and the new area-specific assertions (`"Areas" not in sidebar_headings`, `#areaList` count == 0) passed. |

## Forbidden Changes Check

- No server, listener, endpoint, or network-facing component was added — pure
  static client-side HTML/CSS/JS edit inside `Projects/ProjectUpdater/app/index.html`.
- No changes outside the task's declared `output_paths`
  (`Projects/ProjectUpdater/app/index.html`, `Projects/ProjectUpdater/scripts/validate_project_updater.py`).
  Confirmed via `git status --short -- Projects/ProjectUpdater/` and diff review.
- No project area data was removed or migrated: `area` field, seed/demo project
  `area` values, `#newArea`/`#editArea` form fields, `.pill.area` card badges,
  and area-based search filtering are all unchanged.
- No destructive `localStorage` schema change (`projectUpdater.v1` store key
  and shape unchanged; validator's persistence/edit/delete checks pass).
- No unrelated dead-code removal beyond the Areas sidebar section and its
  rendering path.

## Files Reviewed

- `MAP_System/tasks/TASK-137.json`
- `Projects/ProjectUpdater/app/index.html`
- `Projects/ProjectUpdater/scripts/validate_project_updater.py`
- `MAP_System/events/events.jsonl` (TASK-137 entries)
- `MAP_System/inbox/helpers/helper-review-task-137.md`

## Findings

None. No BLOCKER, REQUIRED, RECOMMENDED, or OPTIONAL findings.

## Verification

- `/tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py` — passed, `ok: true`, 0 failures, 0 console errors (independent re-run, not reused output).
- `grep -n -i area Projects/ProjectUpdater/app/index.html` — confirmed no leftover "Areas" sidebar heading, no `areaList` id, no dead area-shortcut rendering; remaining hits are all legitimate (CSS pill styling, seed data, form fields, badges, search filter).
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py` — passed.

## Notes

This is a purely static, client-side UI change (no server/listener/write-capable
component added), so the AGENTS.md security second-pass requirement does not
apply.
