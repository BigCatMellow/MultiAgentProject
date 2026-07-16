# Work Packet: TASK-205 — ProjectUpdater full backup Export/Import

- Task: TASK-205 (READY, owner codex-lab-nivo). First software-delivery slice
  under DEC-028. Claim it before editing: announce "taking TASK-205" then
  `claim_task('TASK-205','codex-lab-nivo')`.
- Reviewer: a Claude core agent (assigned by gune after you submit). NOT gune.

## Context / the real problem

ProjectUpdater's existing **"Export status"** button (`exportStatus()`, line
~1081) is a **lossy** snapshot for other tools to read — it drops `id`, `goal`,
`nextAction`, `points`, `streak`, `reminderDays`, `lastVisited`, `dueDate`. It
CANNOT restore state, so it does not mitigate the localStorage data-loss risk.
IDEA-0015's real intent is backup/restore. Build that as a SEPARATE pair of
controls; leave "Export status" untouched.

Key anchors in `Projects/ProjectUpdater/app/index.html` (single self-contained
file, no build step):
- `STORE_KEY = 'projectUpdater.v1'` (line ~339)
- `load()` ~417, `save(data)` ~431 (writes `JSON.stringify(data)` to STORE_KEY)
- `normalizeData(data)` ~367 (the sanitizer both load and import must use)
- `db` = the full in-memory model; `render()` re-renders from it
- Export-button markup ~295; `exportStatus()` ~1081

## What to build

1. **Export backup** (full fidelity): serialize the COMPLETE model — the entire
   `db` object (all projects with every field) — as pretty JSON and download it
   (reuse the Blob/anchor pattern from `exportStatus()`). Suggested envelope:
   `{ "format": "projectUpdater.backup.v1", "exportedAt": <iso>, "data": <db> }`.
   Filename e.g. `project-updater-backup.json`.

2. **Import backup**: a file input (hidden `<input type="file" accept="application/json">`
   triggered by a button). On file select:
   - read the file text, `JSON.parse` inside try/catch;
   - accept either the `{format,data}` envelope or a raw db object;
   - run the parsed data through `normalizeData(...)` (do NOT bypass it);
   - **confirm-overwrite guard**: `if (!confirm('Replace all current projects
     with the imported backup? This cannot be undone.')) return;`
   - on success: `save(normalized)`, update `db`, `render()`, and show a status
     message; on malformed/invalid JSON: show an error and leave existing data
     UNTOUCHED (fail safe — never corrupt current state).

3. Place the two new controls near the existing Export button; keep styling
   consistent with the existing buttons.

## Verification (write into the artifact)

Create `Projects/ProjectUpdater/artifacts/task-projectupdater-backup-verification.md`
documenting a round-trip: export backup → change/delete a project (and edit a
field like `goal`/`points`) → import the backup → confirm the FULL state is
restored identically, including the fields the lossy status export drops. Note
how you exercised it (browser steps or a headless check). Also confirm malformed
-file handling leaves data intact.

## Must-not
- Do not touch `exportStatus()` / "Export status" button.
- Do not change `STORE_KEY` or the data schema.
- No build tools, frameworks, servers, or external deps — stays a single
  index.html openable directly.
- Do not edit files outside the two in `output_paths`.
- Do not self-approve or release. Submit for review when done.

## When done
- `python3 MAP_System/scripts/validate_task_mirrors.py` (report the line).
- `submit_task('TASK-205','codex-lab-nivo')` to move it to SUBMITTED.
- Reply to @gune: "TASK-205 submitted" + the two files + round-trip result.
  gune assigns the Claude reviewer.
