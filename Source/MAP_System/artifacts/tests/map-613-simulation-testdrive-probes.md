# MAP 6.13 Simulation-TestDrive Acceptance Probes (TASK-149, Wave 2)

Status: draft-active
Owner: command-center
Built by: TASK-149
Source: `Guidelines/6.13/MAP-Simulation-TestDrive.md` (lines 141-162)

## Purpose

The Simulation-TestDrive document names two probes as "the two highest-signal
probes" for telling fastest whether MAP is living by its two core design
principles or just documented to. This artifact converts them from narrative
checklist rows into concrete, runnable acceptance tests, as flagged during
the 6.13 peripheral-doc corroboration pass.

## Probe 1 — Coordination Via Shared State, Not Messages (Principle 1)

Source row: "Coordination via shared state, not messages | Principle 1 |
Check: how much hcom traffic is really point-to-point?"

### Acceptance Test

```bash
hcom events --last 200 --type message > /tmp/hcom-sample.jsonl
python3 - <<'PY'
import json
lines = [json.loads(l) for l in open("/tmp/hcom-sample.jsonl") if l.strip()]
point_to_point = sum(1 for e in lines if e.get("to") and not e.get("to", "").endswith("-"))
broadcast_or_group = len(lines) - point_to_point
print(f"point_to_point={point_to_point} broadcast_or_group={broadcast_or_group} total={len(lines)}")
PY
```

Cross-reference against the same window's task/event-file mirror updates
(`git log --since=<window> --name-only -- MAP_System/tasks/ MAP_System/events/`).

**Pass condition:** the ratio of durable shared-state writes (task files,
events, decisions) to point-to-point hcom messages should not be trivially
small — i.e. hcom is being used for live coordination/attention, and durable
outcomes are landing in shared state, not only in chat history. This session
(TASK-147/148/149 review-and-build sequence) is itself a live data point:
every substantive decision (claims, approvals, findings) was written to
`map.db`/task files/events/review records, with hcom used for live
coordination and attention, matching the intended pattern.

**Fail condition:** if most durable-seeming decisions (task ownership
changes, approvals, findings) exist ONLY in hcom transcript and never reach
`map.db`, task files, or `events.jsonl`, Principle 1 is not actually being
followed regardless of documentation.

## Probe 2 — Can The Validator Actually Halt? (Principle 2 / Jidoka)

Source row: "Validator with Jidoka halt authority | Phase 3 | Likely gap:
can your validator halt, or only log?"

### Acceptance Test

```bash
python3 MAP_System/scripts/validate_task_mirrors.py; echo "exit=$?"
python3 MAP_System/scripts/validate_events.py --fail-on-new; echo "exit=$?"
python3 MAP_System/scripts/validate_shared_state.py; echo "exit=$?"
```

Then attempt a downstream action that should be blocked by a validator
failure — e.g. run `python3 MAP_System/scripts/map_task.py approve <task>
--reviewer <id>` against a task with a known task-mirror drift (deliberately
introduced in a disposable fixture, not canonical state) and confirm the
approve command itself refuses (as observed live in this task: `map_task.py
approve` runs `validate_task_mirrors` internally and would block on drift).

**Pass condition (current status, as verified live in TASK-147/148/149):**
`validate_task_mirrors.py`, `validate_events.py --fail-on-new`, and
`validate_shared_state.py` all exit non-zero on a real violation, and
`map_task.py approve`/`release_task.py` call these validators internally,
so a drifted or non-canonical state actually blocks the pipeline action, not
just prints a warning. This is a genuine halt, not a log-only check —
confirmed by this session's own TASK-147 review cycle (a real REQUIRED
finding blocked APPROVED status until fixed).

**Fail condition:** if any of these validators can be bypassed (e.g. an
agent manually sets task status to APPROVED in the JSON file without going
through `map_task.py approve`, or if `--fail-on-new` is never actually run
before a merge), the halt authority is documented but not enforced.

**Known partial gap (Wave 4, not yet built):** these are structural/mirror
validators, not the semantic output-correctness validator (Gap-Register 2a)
or the MATOCP/hcom protocol validator. Those do not yet exist as blocking
gates — Wave 4 is the task that closes this fully. This probe currently
passes for structural/mirror integrity only.

## Result Summary (as of this task, 2026-07-13)

| Probe | Status | Evidence |
|---|---|---|
| 1 — Shared state over messages | Likely holding, informally confirmed | This session's task claims/approvals/findings all landed in `map.db`/task files/events/review records; hcom used for live coordination, not as the durable record. Formal measurement (the hcom-volume script above run against a real historical window) is a follow-on, not done here. |
| 2 — Validator can halt | Partially confirmed | Structural/mirror validators (task mirrors, event schema, shared-state HPOM fields) demonstrably block real pipeline actions (`map_task.py approve`) — verified live via TASK-147's REQUIRED finding. The semantic/protocol validator from Wave 4 does not exist yet. |

## Related Files

- `Guidelines/6.13/MAP-Simulation-TestDrive.md`
- `MAP_System/artifacts/planning/map-613-master-implementation-plan.md` [[map-613-master-implementation-plan]] (Wave 4)
- `MAP_System/scripts/validate_task_mirrors.py`
- `MAP_System/scripts/validate_events.py`
- `MAP_System/scripts/validate_shared_state.py`
- `MAP_System/artifacts/reviews/task147-review-zera.md` [[task147-review-zera]]
