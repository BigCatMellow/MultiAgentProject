<!-- hpom: file: risks/RISK_REGISTER.md -->
<!-- hpom: project: ProjectUpdater -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: bootstrap -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Risk Register — ProjectUpdater

Per `MAP_System/RISK_SYSTEM.md`. Use
`MAP_System/templates/RISK_REGISTER_TEMPLATE.md` for further entries.

# Risk Register Entry

Risk ID: RISK-0001
Project: ProjectUpdater
Class: DATA
Severity: COSMETIC
Owner: claude-lab-valo
Date opened: 2026-07-03
Last reviewed: 2026-07-03
Status: ACCEPTED

## Description

All project/note data lives in browser `localStorage`. Clearing browser
data, using a different browser/device, or private/incognito mode loses
all data with no recovery.

## Trigger / likelihood

User clears site data, switches browsers, or uses private browsing.
Moderate likelihood for a personal single-device tool; low blast radius
since the data is low-stakes personal task tracking, not financial or
otherwise critical.

## Blast radius if realized

Loss of tracked projects/notes; user re-enters data manually. No
irreversible external effect.

## Current mitigation

None beyond browser persistence itself. Explicitly accepted rather than
mitigated, since adding sync/export would add a server dependency the
project brief's non-goals rule out.

## Escalation

- [ ] SECURITY or STRUCTURAL — escalated to command-center: N/A
- [ ] BLOCKING, core-agent-mitigable — handled directly, logged below
- [x] DRIFT/COSMETIC — tracked, no escalation required

## Acceptance (if Status: ACCEPTED)

- Decision class (per `MAP_System/DECISION_CLASSES.md`): SCOPE (accepting
  no-sync as within the stated non-goals)
- Approved by: claude-lab-valo (within the project brief's own stated
  non-goals; no new command-center decision needed)
- Linked decision: NONE — covered by the project brief's non-goals section

## Review history

| Date | Reviewed by | Notes |
|---|---|---|
| 2026-07-03 | claude-lab-valo | Opened and accepted at project bootstrap |

## Notes

- A future "export/import JSON" button would mitigate this cheaply
  without adding a server; noted as a possible follow-up, not required
  for the completion condition in `shared/project-brief.md`.
