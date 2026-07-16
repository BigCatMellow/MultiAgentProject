# Review Record: TASK-123

## Header

```text
task_id:      TASK-123
reviewer:     codex-lab-dino
review_date:  2026-07-03
task_owner:   claude-lab-valo
```

Reviewer != owner. Independence check passes.

## Verdict

```text
CHANGES_REQUESTED
```

## Findings

| Severity | File | Finding | Required Action |
|---|---|---|---|
| REQUIRED | `Projects/ProjectUpdater/app/index.html:426` | The Projects filter bar omits the required `Archived` filter. `shared/requirements.md:17` requires the Projects view to be filterable by `Open / Stale / Due soon / Finished / Archived / All`, and `shared/project-brief.md:22` also names `archived`. The implementation has an `active === 'archived'` branch at `app/index.html:442`, but the rendered `filters` array only exposes `Open`, `Stale`, `Due soon`, `On track`, `Finished`, and `All`. Browser verification confirmed that after archiving a project through Quick Note, the project is hidden from Open and visible in All, but there is no Archived chip to select. | Add an `Archived` filter chip wired to `key: 'archived'`, then rerun the browser scenario: archive a project via Quick Note, open Projects, select Archived, confirm the archived project appears there and remains hidden from Open. |

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `Projects/ProjectUpdater/app/index.html` exists and implements Dashboard, Projects, Quick Note, and Add Project views matching the dark-theme visual design | PARTIAL | `app/index.html` exists and all four views render. Screenshot review shows the dark theme and layout match the design direction. Required Projects filter coverage is incomplete because `Archived` is not exposed. |
| 2 | Stale detection and due-soon detection compute against real current dates, not hardcoded sample values | PASS | `daysIdle()`, `daysUntilDue()`, `isStale()`, and `isDue()` compute from `Date.now()`, `lastVisited`, `reminderDays`, and `dueDate`. No hardcoded stale/due counts found. |
| 3 | Adding a project, saving a note, and marking a project visited persist to localStorage and survive reload | PASS | Code paths `createProject()`, `saveNote()`, and `markVisited()` all mutate `db` and call `save(db)`. Valo's Playwright artifact reports add/note/reload persistence; my browser check also archived via Quick Note without console errors. |
| 4 | App runs standalone by opening `index.html` with no server/build step | PASS | Reviewed and exercised via `file://.../Projects/ProjectUpdater/app/index.html` in Playwright/Chromium. No server or build step was used. |
| 5 | Manually exercised end-to-end per `shared/requirements.md` quality bar before submission | PARTIAL | `artifacts/task-123-verification.md` documents broad end-to-end exercise. The Archived filter path required by the same requirements file was missed and needs rework. |

## Files Reviewed

- `Projects/ProjectUpdater/AGENTS.md`
- `Projects/ProjectUpdater/README.md`
- `Projects/ProjectUpdater/app/index.html`
- `Projects/ProjectUpdater/artifacts/task-123-verification.md`
- `Projects/ProjectUpdater/artifacts/screenshots/pu_1_dashboard.png`
- `Projects/ProjectUpdater/artifacts/screenshots/pu_4_after_reload.png`
- `Projects/ProjectUpdater/risks/RISK_REGISTER.md`
- `Projects/ProjectUpdater/shared/project-brief.md`
- `Projects/ProjectUpdater/shared/requirements.md`
- `Projects/ProjectUpdater/shared/unresolved-questions.md`
- `MAP_System/tasks/TASK-123.json`

## Verification

```bash
node --check /tmp/projectupdater-script.js
/tmp/pw_venv/bin/python - <<'PY'
from pathlib import Path
from playwright.sync_api import sync_playwright
url = Path('Projects/ProjectUpdater/app/index.html').resolve().as_uri()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    page.set_default_timeout(5000)
    errors = []
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
    page.goto(url)
    page.locator('.sb-item[data-view="projects"]').first.click()
    labels = page.locator('.filter-chip').all_inner_texts()
    page.locator('.sb-item[data-view="note"]').first.click()
    page.locator('#noteProject').select_option(index=0)
    selected = page.locator('#noteProject option:checked').inner_text().replace('⚠ ', '')
    page.locator('#noteText').fill('Archive path review note')
    page.locator('#noteStatus').select_option('Archived')
    page.locator('#saveNoteBtn').click()
    page.locator('.sb-item[data-view="projects"]').first.click()
    labels_after = page.locator('.filter-chip').all_inner_texts()
    page.get_by_text('All', exact=True).click()
    all_text = page.locator('#content').inner_text()
    page.get_by_text('Open', exact=True).click()
    open_text = page.locator('#content').inner_text()
    print({
        'initial_filters': labels,
        'after_filters': labels_after,
        'archived_project_visible_in_all': selected in all_text,
        'archived_project_hidden_from_open': selected not in open_text,
        'console_errors': errors,
    })
    browser.close()
PY
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py
```

Results:

```text
node --check: PASS
browser filters before/after archive: ['Open', 'Stale', 'Due soon', 'On track', 'Finished', 'All']
archived_project_visible_in_all: True
archived_project_hidden_from_open: True
console_errors: []
task graph: PASS
events: errors=0 warnings=33 historical warnings
```

## Notes

The implementation is close. The required fix appears localized because the
existing `active === 'archived'` branch already filters archived projects; the
missing piece is the user-visible filter control and follow-up verification.
