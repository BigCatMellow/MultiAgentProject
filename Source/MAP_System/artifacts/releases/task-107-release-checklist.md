# Release Checklist: TASK-107

## Header

```text
task_id:      TASK-107
released_by:  claude-lab-valo
release_date: 2026-07-03
review_record: MAP_System/artifacts/reviews/task107-review-dino.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-107 builds the MAP Context System per
`Guidelines/MAP_repo_systems_gap_review.md` priority #3: context packet
format, required/optional/forbidden context by task type, stale-context
handling, token-budget rules, local-summarizer role, and compression
rules. Governs (does not replace) `notes/context-routing-guide.md`.

Delivered:

- `MAP_System/CONTEXT_SYSTEM.md`
- `MAP_System/templates/CONTEXT_PACKET_TEMPLATE.md`
- `DEC-017` in `shared/decisions.md`
- Cross-linked with Research System, Self-Repair System, and the existing
  context-routing guide

First review (dino) found one REQUIRED finding: a reference to a
nonexistent `notes/AGENTS.md` file. Fixed to point at `AGENTS.md` and
`shared/memory-map.md`; re-reviewed to `!LGTM` / APPROVED. A transient
output-path collision with concurrently-built TASK-108 is resolved by this
release (TASK-108 now also has an explicit `depends_on TASK-107`).

## Verification

```text
validate_shared_state.py: 18 checked, 0 failures, 0 warnings
validate_decisions.py: 18 decisions checked, 0 failures
validate_task_graph.py: passed (post-approval)
test_exporter_invariants.py: PASS
full MAP suite (scripts/run_tests.sh): pass=29 fail=0 total=29
runner route before approval: review (no-self-review honored; dino reviewed twice)
```
