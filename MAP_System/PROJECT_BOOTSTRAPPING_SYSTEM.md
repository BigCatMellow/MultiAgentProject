<!-- hpom: file: PROJECT_BOOTSTRAPPING_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-115 build, amended TASK-126 (Emergence capacity requirement) -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Project Bootstrapping System

Status: active
Decision: DEC-023
Owner: command-center
Built by: TASK-115

## What this is

`notes/brain-organization-guide.md` already defines a strong folder
layout for a new project brain. This file adds the workflow around that
layout: what a new project must establish before its first task is
written, so a project does not begin life as a folder of tasks with no
stated intent, assumptions, or risk posture underneath them.

## Core principle

```
No new project should begin with only tasks.
It should begin with intent, assumptions, research needs, quality standards, risks, decision paths, and Emergence capacity.
```

## Relationship to brain-organization-guide.md

`notes/brain-organization-guide.md` remains the source of truth for
folder layout (`shared/`, `tasks/`, `workflow/`, `notes/`, `templates/`,
`artifacts/`, `handoffs/`, `inbox/`, `events/`, `archive/`). This system
does not redefine that layout — it defines the content that must exist
inside `shared/` before the project is considered bootstrapped, and
points to `NEW_PROJECT_WIZARD.md` for the step-by-step process.

## What a new project must establish before its first task

| Requirement | Lives in | Why it matters |
|---|---|---|
| Intent | `shared/project-brief.md` | What is this project for, and what does done look like |
| Assumptions | an initial `RESEARCH_SYSTEM.md`-style Assumption Register, or a note in `shared/unresolved-questions.md` if none exist yet | Prevents early architecture from resting on unverified claims |
| Research needs | at least one Research Brief if the project depends on external facts (an API, a library, a domain) not yet verified | Per `RESEARCH_SYSTEM.md` — do not let the first task assume facts it hasn't checked |
| Quality standards | `shared/requirements.md` and/or `templates/project-quality-standards.md` | What "acceptable" means for this project specifically |
| Risks | an initial `RISK_SYSTEM.md`-style register entry for any known SECURITY/DATA/AVAILABILITY exposure the project starts with | Do not wait for an incident to start tracking a known risk |
| Decision paths | a note in `shared/decisions.md` (or a pointer to the MAP-system one) naming which decisions are project-local vs. need command-center, per `DECISION_AUTHORITY_SYSTEM.md` | Prevents ad-hoc authority disputes once work starts |
| Emergence capacity | `insights/`, `ideas/`, `experiments/`, and `synthesis/` folders (empty is fine) per `emergence/README.md`'s project-level layout | Per DEC-026/TASK-126: an entire project shipped (ProjectUpdater, TASK-123–125) without a single Emergence artifact even though real insights surfaced, because nothing required the folders to exist or capture to be considered |

A project may start small — a one-paragraph brief and an empty risk
register are fine — but each of these seven should exist in some form,
not be silently absent. Emergence capture is not a one-time bootstrap
checkbox like the other six — see "Ongoing Emergence capture" below.

## Ongoing Emergence capture (not just at bootstrap)

Unlike the other six requirements, Emergence is not "write it once and
move on." Per `emergence/README.md`'s rule ("notice freely, act
carefully, promote deliberately"), every task in the project should ask,
before submission: *did anything happen here worth capturing as an
insight or idea?* Sometimes the honest answer is no — that is a valid
answer, not a box to fake.

This is enforced mechanically, not just documented: `CHANGE_CONTROL_SYSTEM.md`'s
release-record convention and `scripts/release_task.py` require an
"Emergence capture considered" line in every release checklist before a
task can be marked `RELEASED` (see DEC-026). A checklist can say "considered,
nothing worth capturing" — the gate is that the question was asked, not
that an artifact was forced into existence.

## Bootstrap workflow

See `NEW_PROJECT_WIZARD.md` for the concrete step-by-step checklist. In
summary:

```
Copy brain-organization-guide.md's folder layout
  → Write shared/project-brief.md (intent)
  → Write shared/requirements.md (quality standards)
  → Log known assumptions and research needs
  → Log known risks, even if the register starts empty
  → State decision paths (project-local vs. command-center)
  → Create empty insights/ideas/experiments/synthesis folders
  → Only then write the first task
  → Consider Emergence capture at every task's submission, not just at bootstrap
```

## When to skip steps

A trivial or throwaway project (a scratch experiment, a one-off script)
does not need the full bootstrap — use judgment per
`shared/hpom.md`'s routing questions. But a project that will accumulate
multiple tasks, multiple agents, or outlive one session should not skip
this, even informally.

## Relationship to other systems

```
Research System supplies the assumption/research-needs step.
Risk System supplies the initial risk register.
Decision/Authority System supplies the decision-paths step.
Context System governs what a new agent reads first when joining the project.
Emergence System supplies ongoing insight/idea capture, gated at release time by Change Control.
```

- **`RESEARCH_SYSTEM.md`**: a new project's first Research Brief, if any,
  should follow that system's format directly rather than an ad-hoc note.
- **`RISK_SYSTEM.md`**: a new project's initial risk register uses
  `templates/RISK_REGISTER_TEMPLATE.md`, even if it starts with zero or
  one entries.
- **`DECISION_AUTHORITY_SYSTEM.md`**: the decision-paths step is where a
  new project states, up front, which decision classes it expects to make
  locally versus escalate — avoiding the ambiguity this system exists to
  prevent.
- **`CONTEXT_SYSTEM.md`**: once bootstrapped, a new project should get its
  own default context stack (mirroring the MAP-system one in
  `notes/context-routing-guide.md`) so agents joining later read the six
  bootstrap artifacts first.
- **`emergence/README.md`**: source of the project-level insight/idea/
  experiment/synthesis folder layout this system now requires at
  bootstrap.
- **`CHANGE_CONTROL_SYSTEM.md`**: source of the mechanical "Emergence
  capture considered" release-checklist gate that keeps this from being
  a bootstrap-only, easily-forgotten step.

## Related files

- `NEW_PROJECT_WIZARD.md` [[NEW_PROJECT_WIZARD]] — the step-by-step bootstrap checklist
- `notes/brain-organization-guide.md` [[brain-organization-guide]] — the folder layout this system
  assumes and extends
- `RESEARCH_SYSTEM.md` [[RESEARCH_SYSTEM]] — source of the assumptions/research-needs step
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — source of the initial risk register
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — source of the decision-paths step
- `CONTEXT_SYSTEM.md` [[CONTEXT_SYSTEM]] — how a new project's context stack should look
  once bootstrapped
- `emergence/README.md` [[emergence/README]] — the project-level Emergence folder layout this
  system requires at bootstrap
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — the mechanical release-checklist gate that
  keeps Emergence capture from being forgotten after bootstrap
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as a secondary gap
