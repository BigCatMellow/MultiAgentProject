# TASK-133 ProjectUpdater Management Operations Evidence

Owner: codex-lab-dino
Date: 2026-07-03

## Scope

Implemented the operator-requested ProjectUpdater management operations:

- edit existing projects;
- delete projects with confirmation;
- add/change multiple project goals;
- store a project folder/reference path;
- expose a project-card action for opening the stored folder reference.

Per the operator's scope correction relayed during TASK-133, the app keeps this
fully static: it opens the stored folder path through a `file://` URL only. It
does not generate/copy shell commands and does not try to execute a local
Command Center Lab process from browser JavaScript.

## Data Compatibility

Existing `localStorage` project records with only a `goal` string are migrated
in place to:

```json
{
  "goal": "Primary goal",
  "goals": ["Primary goal"],
  "referencePath": ""
}
```

The single `goal` field is still maintained for compatibility with existing
rendering and saved data.

## Verification

Commands:

```bash
python3 -m py_compile Projects/ProjectUpdater/scripts/validate_project_updater.py
node --check /tmp/project_updater_task133.js
/tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py
```

Browser validator result:

```text
ok=true
failures=[]
```

Covered behavior:

- seeded dashboard/filter counts still work;
- add project persists after reload;
- edit project persists name, area, goals, next action, reference path, status,
  priority, progress, and reminder window;
- multiple goals persist as an array while the compatibility `goal` field tracks
  the first goal;
- open-folder action exposes the stored reference path through the static app;
- delete confirmation removes the project and related notes;
- Quick Note status/progress update and note persistence still work;
- desktop/mobile visible controls remain labeled;
- no browser console errors.
