<!-- hpom: file: shared/[filename].md -->
<!-- hpom: project: [PROJECT_NAME or MAP] -->
<!-- hpom: state_owner: [agent-id or command-center] -->
<!-- hpom: status: CURRENT | STALE | NEEDS_REVIEW | SUPERSEDED -->
<!-- hpom: last_verified: YYYY-MM-DD -->
<!-- hpom: verified_against: [what was checked — e.g. git log, task board, agent report] -->
<!-- hpom: confidence: HIGH | MEDIUM | LOW -->
<!-- hpom: supersedes: [filename or NONE] -->
<!-- hpom: superseded_by: [filename or NONE] -->

# [File Title]

[Content of the shared-state file goes here.]

---

## Maintenance

This file is a shared-state document. It is authoritative for the project until
marked STALE or SUPERSEDED.

To update this file:
1. Edit the content.
2. Update `last_verified` to today's date.
3. Update `verified_against` to describe what you checked.
4. Set `status: CURRENT`.
5. Append an event to `events/events.jsonl`.

If this file is superseded by a new file:
1. Set `status: SUPERSEDED`.
2. Set `superseded_by: [new filename]`.
3. Set `supersedes: [this filename]` in the new file.
