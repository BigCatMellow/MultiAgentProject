# TASK-125 ProjectUpdater Validator Evidence

Task: TASK-125
Owner: codex-lab-muva
Date: 2026-07-03
Status: submitted evidence

## Scope

Added a reusable browser regression validator for the standalone ProjectUpdater
app:

```text
Projects/ProjectUpdater/scripts/validate_project_updater.py
```

The validator does not change app behavior, app storage schema, or introduce a
server/build step. It loads `Projects/ProjectUpdater/app/index.html` directly
from `file://`, seeds deterministic localStorage test data, and exercises the
real UI through Playwright.

## Checks Covered

- Dashboard active/stale/due-soon counts compute from real dates.
- Stale reminder banner appears for seeded stale projects.
- Projects filters include Open, Stale, Due soon, On track, Finished,
  Archived, and All.
- Stale, Due soon, Finished, and Archived filters show the expected seeded
  projects.
- Filter chips update `aria-pressed`.
- Add Project flow persists across reload.
- Quick Note flow persists note, progress/status changes, and archived state
  across reload.
- Archived project appears under Archived and disappears from Open.
- Priority segmented control updates `aria-pressed`.
- Mobile-width layout hides sidebar and exposes keyboard-accessible
  `#mobileViewNav`.
- Visible form controls have programmatic labels.
- Browser console reports no errors.

## Verification

Command:

```bash
/tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py
```

Result:

```json
{
  "ok": true,
  "failures": [],
  "evidence": {
    "desktop_status": "3 active projects · 1 stale · 1 due soon",
    "filters": [
      "Open",
      "Stale",
      "Due soon",
      "On track",
      "Finished",
      "Archived",
      "All"
    ],
    "filter_aria_after_stale": {
      "Open": "false",
      "Stale": "true"
    },
    "priority_aria_after_high": [
      ["Low", "false"],
      ["Medium", "false"],
      ["High", "true"]
    ],
    "archived_due_status_after_reload": "Archived",
    "notes_for_due_after_reload": 1,
    "mobile": {
      "mobile_nav_visible": true,
      "sidebar_visible": false,
      "options": [
        "Dashboard",
        "Projects",
        "Quick Note",
        "Add Project"
      ]
    },
    "visible_unlabeled_controls_desktop": [],
    "visible_unlabeled_controls_mobile": [],
    "console_errors": []
  }
}
```

Additional verification:

```bash
python3 -m py_compile Projects/ProjectUpdater/scripts/validate_project_updater.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
```

Both passed.

## Notes

The root MAP virtualenv does not currently include Playwright. The validator is
therefore documented with the Playwright environment already used by TASK-123
and TASK-124 review:

```bash
/tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py
```
