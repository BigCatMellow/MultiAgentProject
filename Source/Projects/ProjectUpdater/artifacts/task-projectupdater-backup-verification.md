# TASK-205 ProjectUpdater Backup Verification

Date: 2026-07-15
Agent: codex-lab-nivo

## Scope

Verified the new full-fidelity backup path in `Projects/ProjectUpdater/app/index.html`:

- `Export backup` downloads `project-updater-backup.json`.
- The backup uses the envelope `format: "projectUpdater.backup.v1"` with `data` containing the complete in-memory model.
- `Import backup` accepts the envelope, runs the imported model through `normalizeData(...)`, confirms overwrite, saves to `STORE_KEY`, and re-renders through the existing status path.
- Malformed JSON fails safe and leaves the current localStorage payload unchanged.

The existing lossy `Export status` path remains separate and unchanged.

## Automated Round Trip

I ran a bounded Node-based browser stub against the actual HTML script. The check loaded `app/index.html`, seeded `localStorage` with a full model, captured the backup download payload, cleared the current model, imported the captured backup, and compared the restored `STORE_KEY` JSON to the original seed.

Seeded project fields included the fields omitted by the lossy status export:

- `id`
- `goal`
- `nextAction`
- `points`
- `streak`
- `reminderDays`
- `lastVisited`
- `dueDate`

Result:

```json
{
  "ok": true,
  "filename": "project-updater-backup.json",
  "restoredProjects": 1,
  "restoredNotes": 1,
  "preservedFields": [
    "id",
    "goal",
    "nextAction",
    "points",
    "streak",
    "reminderDays",
    "lastVisited",
    "dueDate"
  ]
}
```

The exact restored storage JSON matched the original seeded model after:

1. Export backup.
2. Replace the current model with `{ "projects": [], "notes": [] }`.
3. Import the captured backup JSON.
4. Read `localStorage["projectUpdater.v1"]`.

## Malformed JSON Check

The same run attempted to import `{bad json` after the successful restore. The import raised the error path and the previously restored `localStorage["projectUpdater.v1"]` string remained byte-identical. No partial save occurred.

## Notes

Playwright is not installed in the MAP virtualenv in this session, so I did not add browser dependencies for this single-file change. The Node check still executed the actual app script with DOM, `Blob`, `FileReader`, `localStorage`, and `confirm` stubs and exercised the export/import functions directly.
