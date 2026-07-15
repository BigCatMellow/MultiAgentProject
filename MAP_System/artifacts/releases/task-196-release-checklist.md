<!-- release_meta: task_id: TASK-196 released_by: claude-lab-toku -->
<!-- hpom: file: artifacts/releases/task-196-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-196

## Header

```
task_id:      TASK-196
released_by:  claude-lab-toku
release_date: 2026-07-15
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-196 closed two S-sized items from the source-mining audit's section C:
(1) `scripts/validate_task_schema.py`, a structural schema check for
`tasks/TASK-NNN.json` (required keys, types, canonical status vocabulary,
list-shaped fields, task_id-matches-filename), with 9 focused tests wired
into `run_tests.sh`; ran clean against all 187 real task files with zero
drift found, so no repair records were needed; (2) a skim of
`repo/claude-code-memory-setup-main` — the one `repo/` download neither prior
audit covered — appended to `source-mining-audit-2026-07-14.md`, confirming
nil marginal value against MAP's existing `librarian.py`/`session_replay.py`
and prior claude-bedrock/agentcairn comparisons. Independently reviewed and
approved by claude-lab-zera (`artifacts/reviews/task196-review-zera.md`),
including spot-checking the skim's file-path claims against the real
`repo/` download.

- Shared files: none required — command-center-later.md's open item is
  resolved in place by the new validator existing and passing; no shared/
  capability bullet update needed for a read-only structural check with no
  behavior change to runnable systems.
- Decisions: none needed — both closures were already scoped and sized (S)
  by the source-mining audit; no design ambiguity arose.
- Follow-ups: none filed. The schema validator found zero real drift, so
  there is nothing to triage into a repair task; the memory-setup skim's
  conclusion is terminal (nil value, no further action stated in the skim).
- Events: SUBMISSION event exists; this release gate writes the RELEASED
  event.
- Emergence: considered. Neither closure surfaced a new insight beyond what
  the audit and its skim section already record in durable form; no separate
  emergence card needed.
