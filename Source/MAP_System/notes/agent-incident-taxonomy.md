<!-- hpom: file: notes/agent-incident-taxonomy.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: gune E/I research wave 2026-07-15 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Agent Incident Taxonomy

A standing reference naming the failure modes MAP should watch for in `events.jsonl` and RnS runs, providing shared vocabulary for future eval and observability work.

## Incident Classes

| Incident Class | What It Looks Like in MAP | Existing Coverage | Gap |
|---|---|---|---|
| Tool-call failure | A script/gate/CLI call errors or returns wrong exit code | Partly caught by `run_tests.sh`, gate exit checks | No structured incident tag in events.jsonl. |
| Context truncation | Agent loses earlier task/claim state, re-derives wrong | Brain-compaction + SYN-0001 (one-state-two-readers) mitigate | No detector. |
| Runaway loop | Agent retries/repeats without progress (e.g. re-review dupes) | RnS + limit-watcher + announce-before-claim | No loop counter. |
| Silent stop / idle | Session stops without handoff | Limit-watcher reports, declared-idle (TASK-084) | Covered, keep. |

This taxonomy seeds IDEA-0018's eval discipline.
