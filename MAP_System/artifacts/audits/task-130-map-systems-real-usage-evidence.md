# TASK-130 MAP Systems Real-Usage Evidence

Task: TASK-130
Parent: TASK-129
Owner: codex-lab-muva
Status: findings-only

## Scope

This note gathers evidence for actual use of the MAP systems built in
TASK-103 through TASK-126. It distinguishes operational use from documentation
mentions, task build records, review prose, and template existence.

No fixes were made to system documents, templates, validators, runtime scripts,
or project source files.

## Evidence Commands

Representative searches used:

- `rg -n "RESEARCH_SYSTEM|Research Brief|Source Map|Claim Evidence Matrix|Assumption Register|Research Summary|templates/research|research/" MAP_System Projects Guidelines`
- `rg -n "SELF_REPAIR_SYSTEM|Repair Record|Health Check|HEALTH-|REPAIR-|templates/repairs|repairs/" MAP_System Projects Guidelines`
- `rg -n "CONTEXT_SYSTEM|CONTEXT_PACKET|Context Packet|Required Context|Forbidden Context|templates/CONTEXT_PACKET_TEMPLATE" MAP_System Projects Guidelines`
- `find . -path './Projects/Backups' -prune -o -path './MAP_System/archive' -prune -o -path './MAP_System/tasks' -prune -o -path './MAP_System/workflow/task_graph.json' -prune -o -path './MAP_System/events/events.jsonl' -prune -o -type f \( -name '*RISK_REGISTER*' -o -name 'CONTEXT-*' -o -name 'BRIEF-*' -o -name 'SOURCE-*' -o -name 'SUMMARY-*' -o -name 'ASSUMPTION-*' -o -name 'CLAIM-*' -o -name 'HEALTH-*' -o -name 'REPAIR-*' -o -name 'RETRO-*' \) -print`
- `rg -n "^## DEC-|Class:|Applies-To:|CLASS" MAP_System/shared/decisions.md MAP_System/DECISION_CLASSES.md MAP_System/DECISION_AUTHORITY_SYSTEM.md`
- `rg -n "Emergence capture considered|REQUIRED_CHECKS|release checklist|artifacts/releases|Rollback|Migration|retirement" MAP_System/scripts/release_task.py MAP_System/artifacts/releases MAP_System/CHANGE_CONTROL_SYSTEM.md`

I ignored `Projects/Backups/`, `MAP_System/archive/`, task JSON, graph mirrors,
and event-log mentions when deciding whether a system had operational use.

## Summary Matrix

| System | Operational usage evidence | Status |
|---|---|---|
| Research | Validator and templates exist; no copied MAP research brief/source/evidence/summary artifacts found beyond README/template/build mentions. ProjectUpdater explicitly said no research brief was needed. | documented/validated, not yet exercised |
| Self-Repair | `HEALTH-0001-map-system-self-application-review.md` and current `REPAIR-0001` through `REPAIR-0004` records exist; runner repair drove TASK-116, risk-validator repair drove TASK-120, and TASK-129 added cross-link and repair-ID collision records. | genuinely used |
| Context | Validator and template exist; no real `CONTEXT-*` packet artifact found outside tests/templates. | documented/validated, not yet exercised |
| Decision/Authority | DEC-018 through DEC-026 use `Class:` in `Applies-To`; no DEC after DEC-026 exists yet to prove post-adoption ongoing use. | used during adoption; no post-DEC-026 sample yet |
| Human Interface | `HUMAN_INTERFACE_SYSTEM.md` exists; CommandCenterUI artifact folder has README/repair note, but live dashboard integration remains open in backlog. | mostly specification |
| Risk | `shared/RISK_REGISTER.md`, `Projects/ProjectUpdater/risks/RISK_REGISTER.md`, `validate_risk_registers.py`, focused tests, and run_tests integration exist. | genuinely used |
| Security/Permissions | Security Second Pass appears in several reviews; destructive-action policy/permission docs are referenced, but no structured security artifact or validator exists. | partially used as review convention |
| Change Control | Release checklists exist for many tasks; `release_task.py` enforces required checklist items, including DEC-026 emergence capture. | genuinely used and mechanically enforced |
| Project Bootstrapping | ProjectUpdater was bootstrapped with `shared/project-brief.md`, `shared/requirements.md`, `shared/unresolved-questions.md`, and `risks/RISK_REGISTER.md`; event log says it followed `NEW_PROJECT_WIZARD.md`. | genuinely used once |
| Archive/Retention | Archive/retention docs are linked and release notes mention retirement semantics; no post-adoption archive/retention action found beyond existing archive folders and documentation. | mostly specification |
| Retrospective/Learning | RETRO-0001 is embedded in `RETROSPECTIVE_SYSTEM.md` and produced a task-authoring guide fix; no standalone copied retrospective record found from the template. | used once, storage pattern weak |
| Emergence enforcement (DEC-026) | ProjectUpdater emergence folders now exist; ProjectUpdater insights/idea were backfilled centrally; `release_task.py` now blocks release without `Emergence capture considered`. | genuinely used and mechanically enforced |

## Findings

### Research System

Evidence:

- `MAP_System/templates/research/` contains the six expected templates.
- `MAP_System/scripts/validate_research_artifacts.py` and
  `MAP_System/tests/test_validate_research_artifacts.py` exist.
- `MAP_System/artifacts/research/` contains only `README.md`.
- `Projects/ProjectUpdater/shared/unresolved-questions.md` explicitly states no
  external-dependency research brief was needed at bootstrap.

Conclusion: Research is documented and validator-backed, but there is no real
copied Research Brief / Source Map / Claim Evidence Matrix / Assumption
Register / Research Summary artifact in active MAP use yet.

### Self-Repair System

Evidence:

- `MAP_System/repairs/HEALTH-0001-map-system-self-application-review.md`
  exists and was used by TASK-120.
- `MAP_System/repairs/REPAIR-0001-runner-released-dependency-drift.md` drove
  TASK-116.
- `MAP_System/repairs/REPAIR-0003-risk-validator-placeholder-regex-false-positive.md`
  records the risk-validator HPOM-header false positive fixed during TASK-120.
- `MAP_System/repairs/REPAIR-0002-one-way-cross-link-gaps-between-11-systems.md`
  records TASK-129's cross-link gap findings.
- `MAP_System/repairs/REPAIR-0004-repair-record-id-collision.md` records the
  duplicate repair-ID cleanup that moved the risk-validator record to
  `REPAIR-0003`.
- `MAP_System/scripts/validate_repair_artifacts.py` and focused tests exist.

Conclusion: Self-Repair has real operational use beyond its build task.

### Context System

Evidence:

- `MAP_System/templates/CONTEXT_PACKET_TEMPLATE.md` exists.
- `MAP_System/scripts/validate_context_packets.py`,
  `MAP_System/tests/test_validate_context_packets.py`, and
  `MAP_System/artifacts/tests/task-109-context-validator.md` exist.
- Search for active `CONTEXT-*` packet artifacts found only the system doc,
  template, validator, tests, and test evidence.

Conclusion: Context is validated as a structure, but no task appears to have
created and used an actual context packet yet.

### Decision / Authority System

Evidence:

- `DECISION_CLASSES.md` says class belongs in `Applies-To` or a dedicated
  `Class:` line.
- DEC-018 through DEC-026 include class tags in `Applies-To`, for example
  `Class: AUTHORITY`, `Class: ARCHITECTURE`, and `Class: POLICY`.
- No DEC-027 or later decision exists yet.

Conclusion: The class convention was used during the system adoption sequence,
but there is not yet a post-adoption decision to prove the habit is continuing.

### Human Interface System

Evidence:

- `MAP_System/HUMAN_INTERFACE_SYSTEM.md` defines the operator dashboard content
  contract.
- `MAP_System/artifacts/command-center-ui/README.md` and
  `standalone-ui-map-db-repair-2026-07-02.md` exist.
- `MAP_System/shared/improvement-backlog.md` still lists live hcom/MAP state
  wiring to CommandCenterUI as open.

Conclusion: Human Interface is mainly a specification today. Evidence of live
operator dashboard enforcement was not found in this slice.

### Risk System

Evidence:

- `MAP_System/shared/RISK_REGISTER.md` exists.
- `Projects/ProjectUpdater/risks/RISK_REGISTER.md` exists and contains
  `RISK-0001`.
- `MAP_System/scripts/validate_risk_registers.py` is in `run_tests.sh`.
- `MAP_System/emergence/ideas/IDEA-0015-*` references ProjectUpdater
  `RISK-0001` as the source of an export/import mitigation idea.

Conclusion: Risk has real use in MAP itself and in ProjectUpdater, plus
validator coverage.

### Security / Permissions System

Evidence:

- `SECURITY_PERMISSIONS_SYSTEM.md`, `AGENT_PERMISSION_LEVELS.md`, and
  `DESTRUCTIVE_ACTION_POLICY.md` exist.
- Multiple reviews include a `Security Second Pass` section, including
  `task119-review-lema.md`, `task120-review-dino.md`, and others.
- `shared/approval-calibration.md` and `shared/hpom.md` reference destructive,
  external, publication, and broad Git actions as approval boundaries.
- No structured security-permission validator or destructive-action log was
  found.

Conclusion: Security is partially operational as a review convention and
approval boundary, but not mechanically enforced beyond existing review and
tool-approval behavior.

### Change Control System

Evidence:

- `MAP_System/scripts/release_task.py` defines `REQUIRED_CHECKS`.
- `MAP_System/artifacts/releases/` contains task release checklists.
- `MAP_System/artifacts/releases/task-126-release-checklist.md` includes
  `- [x] Emergence capture considered`.
- `CHANGE_CONTROL_SYSTEM.md` points to release records, rollback notes,
  migration notes, and retirement rules.

Conclusion: Change Control is one of the strongest operational systems: it is
used repeatedly and has a mechanical release gate.

### Project Bootstrapping System

Evidence:

- `Projects/ProjectUpdater/events/events.jsonl` records bootstrap per
  `MAP_System/NEW_PROJECT_WIZARD.md`.
- ProjectUpdater has `shared/project-brief.md`, `shared/requirements.md`,
  `shared/unresolved-questions.md`, and `risks/RISK_REGISTER.md`.
- After DEC-026/TASK-126, ProjectUpdater also has `insights/`, `ideas/`,
  `experiments/`, and `synthesis/` folders.

Conclusion: Project Bootstrapping was exercised by ProjectUpdater, though this
is only one post-adoption project sample.

### Archive / Retention System

Evidence:

- `ARCHIVE_RETENTION_SYSTEM.md` exists and distinguishes archive statuses from
  Change Control retirement.
- Release/review records mention retirement semantics, including TASK-100 and
  TASK-117 materials.
- No post-adoption active archive operation or retention cadence artifact was
  found in this slice.

Conclusion: Archive/Retention is mostly specification at present, with
conceptual use around RETIRED tasks but little direct operational evidence.

### Retrospective / Learning System

Evidence:

- `RETROSPECTIVE_SYSTEM.md` embeds RETRO-0001 for TASK-103 through TASK-117.
- `templates/RETROSPECTIVE_TEMPLATE.md` exists.
- `shared/improvement-backlog.md` and `notes/task-authoring-guide.md` reference
  the RETRO-0001 finding and applied fix.
- Search found no standalone `RETRO-*` file outside the system doc/template.

Conclusion: Retrospective was used once and produced a real process fix, but
the storage pattern is weak because the only completed retrospective is
embedded in the system document rather than filed as a reusable record.

### Emergence Enforcement

Evidence:

- `MAP_System/emergence/insights/INS-0011`, `INS-0012`, `INS-0013`, and
  `ideas/IDEA-0015-*` are ProjectUpdater-related.
- `Projects/ProjectUpdater/{insights,ideas,experiments,synthesis}/README.md`
  files exist after TASK-126.
- `MAP_System/scripts/release_task.py` now requires `Emergence capture
  considered`.
- `task-126-release-checklist.md` passed that new gate.

Conclusion: E/I has moved from optional capture to mechanically enforced
release consideration, with ProjectUpdater as the first backfilled sample.

## Suggested TASK-129 Routing

These are not fixes applied by TASK-130.

1. Consider a follow-up task to require or at least prompt a real Context
   Packet for large architecture/audit tasks.
2. Consider a follow-up task to store retrospectives as standalone records
   under a predictable folder, leaving summaries/cross-links in the system doc.
3. Consider a follow-up task to define the first required Research System
   exercise, or explicitly record that Research is only required when external
   facts are involved.
4. Consider a follow-up task for Human Interface live-state wiring, because it
   remains specification-heavy.
5. Consider adding a lightweight security/destructive-action evidence artifact
   only if reviews begin making substantive security decisions that need durable
   traceability.
