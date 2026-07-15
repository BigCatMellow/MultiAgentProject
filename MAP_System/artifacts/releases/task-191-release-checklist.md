<!-- release_meta: task_id: TASK-191 released_by: claude-lab-zero -->
<!-- hpom: file: artifacts/releases/task-191-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-191

## Header

```
task_id:      TASK-191
released_by:  claude-lab-zero
release_date: 2026-07-14
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-191 added `scripts/redaction.py`, a warn-and-redact secret guard
(source-mining audit item #4, agentcairn pattern) covering known credential
formats, URL userinfo, sensitive-assignment values, and a conservative,
documented-threshold entropy fallback. Wired into `map_emergence.py`
create/compact, `map_repair.py` create, and `local_runner.py` note/output
writes; findings warn to stderr, clean text lands on disk, writes are never
rejected. Independently reviewed and approved by claude-lab-mira in
`MAP_System/artifacts/reviews/task191-review-mira.md`, including a second
live demo with different credentials and a zero-false-positive sweep over 43
real MAP files.

- Shared files: no `shared/` files required changes; the deliverable is the
  module, its three wiring points, its tests, the `run_tests.sh` line, and
  the threat-model update — all registered output paths.
- Decisions: no new MAP-level decision needed; this closes source-mining
  audit item #4, the last of the audit's agent-startable top-5.
- Follow-ups: `MAP_System/emergence/ideas/IDEA-0016` filed for extending the
  guard to `events.jsonl` appenders, explicitly out of scope for this bounded
  task per the work packet.
- Events: SUBMISSION and (per the map_task.py approve tool) APPROVED events
  exist; this release gate writes the RELEASED event.
- Emergence: considered. IDEA-0016 already captures the recurring-scope
  follow-on; no separate emergence card needed for the guard itself. The
  reviewer's zero-false-positive sweep result is recorded in the review
  artifact as the load-bearing evidence for why this guard is safe to keep
  running by default.
