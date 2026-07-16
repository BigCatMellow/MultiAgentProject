<!-- hpom: file: shared/RISK_REGISTER.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-120 self-application health check -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP-System Risk Register

Canonical MAP-system-level risk register per `RISK_SYSTEM.md`. Use
`templates/RISK_REGISTER_TEMPLATE.md` to add further entries.
Project-level risk registers live under
`Projects/{project-name}/risks/RISK_REGISTER.md`.

# Risk Register Entry

Risk ID: RISK-0001
Project: MAP_System
Class: PROCESS
Severity: DRIFT
Owner: claude-lab-valo
Date opened: 2026-07-03
Last reviewed: 2026-07-03
Status: MITIGATED

## Description

Concurrent core agents building cross-linked prose systems (each adding a
`DEC-NNN` entry and cross-link backlinks) can register overlapping
`output_paths` on `shared/decisions.md`, `shared/current-state.md`, and
other agents' system files, tripping `validate_task_graph.py`'s output
path collision check while both tasks are still active.

## Trigger / likelihood

Observed directly during the TASK-103 through TASK-118 gap-review build
sequence: collisions occurred between TASK-107/TASK-108 and recurred as a
near-miss pattern (caught pre-submission) across TASK-111, TASK-112,
TASK-115, and TASK-117. Likely any time two or more agents build
cross-linked MAP-system documentation concurrently.

## Blast radius if realized

Low by itself — `validate_task_graph.py` catches it before release, so it
blocks a `run_tests.sh` pass rather than causing silent data loss. The
real cost is coordination overhead (rework/resubmit cycles) if not
managed.

## Current mitigation

- Explicit `depends_on` between sequentially-built tasks that share
  `shared/decisions.md`/`shared/current-state.md`.
- Registering all touched output_paths (including one-line cross-link
  backlinks) before submission — now stated explicitly in
  `notes/task-authoring-guide.md` per RETRO-0001 (`RETROSPECTIVE_SYSTEM.md`,
  TASK-118).
- Holding shared-file edits until the prior dependency task is RELEASED.

## Escalation

- [ ] SECURITY or STRUCTURAL — escalated to command-center: N/A, not this class/severity
- [x] BLOCKING, core-agent-mitigable — handled directly, logged below
- [ ] DRIFT/COSMETIC — tracked, no escalation required

## Acceptance (if Status: ACCEPTED)

- Decision class (per `DECISION_CLASSES.md`): N/A — mitigated, not accepted
- Approved by: N/A
- Linked decision: NONE

## Review history

| Date | Reviewed by | Notes |
|---|---|---|
| 2026-07-03 | claude-lab-valo | Opened during TASK-120 health check; mitigation already applied mid-cycle via depends_on + task-authoring-guide.md fix |

## Notes

- See RETRO-0001 in `RETROSPECTIVE_SYSTEM.md` for the full retrospective
  on this pattern.

# Risk Register Entry

Risk ID: RISK-0002
Project: MAP_System
Class: PROCESS
Severity: DRIFT
Owner: command-center
Date opened: 2026-07-13
Last reviewed: 2026-07-13
Status: OPEN

## Description

MAP's authority, destructive-action, and helper capability rules are documented
but not yet enforced by an automated pre-dispatch checker. A task could be
assigned to a worker lane that should only draft, recommend, or request
approval, leaving review to catch the mismatch after work has already started.

## Trigger / likelihood

Most likely when a task packet lacks structured `decision_class`,
`risk_class`, `destructive_action`, or `task_tier` metadata, or when a helper
candidate is selected from broad task text instead of an explicit capability
whitelist. The likelihood increases as MAP adds more helper/local lanes and UI
dispatch controls.

## Blast radius if realized

An unsafe assignment could cause wasted work, noisy rework, an unapproved
policy or authority change, or a destructive-action request reaching the wrong
lane. Existing review and operator rules reduce the chance of a silent final
state change, but the failure would still consume attention and could become a
security or structural incident if combined with a write-capable surface.

## Current mitigation

- `AGENT_PERMISSION_LEVELS.md`, `DESTRUCTIVE_ACTION_POLICY.md`,
  `DECISION_CLASSES.md`, `DECISION_AUTHORITY_SYSTEM.md`, and
  `SECURITY_PERMISSIONS_SYSTEM.md` define current human/core-agent rules.
- TASK-153 task tiering defines draft-only helper/local lanes.
- TASK-156 adds `map-pre-dispatch-policy-checker-spec.md`,
  `map-capability-whitelist-test-plan.md`, and `map-threat-model.md` as the
  implementation plan for automated gating.
- Current core agents remain accountable for integration and review; helpers
  may not approve or finalize decisions.

## Escalation

- [ ] SECURITY or STRUCTURAL — escalated to command-center: N/A, current entry is PROCESS/DRIFT
- [ ] BLOCKING, core-agent-mitigable — handled directly, logged below
- [x] DRIFT/COSMETIC — tracked, no escalation required

## Acceptance (if Status: ACCEPTED)

- Decision class (per `DECISION_CLASSES.md`): N/A — open risk, not accepted
- Approved by: N/A
- Linked decision: NONE

## Review history

| Date | Reviewed by | Notes |
|---|---|---|
| 2026-07-13 | codex-lab-mozu | Opened during TASK-156; mitigations are design artifacts pending implementation |

## Notes

- Implementation should reduce this risk by enforcing allow,
  require-approval, and reject outcomes before runner/helper assignment.
