<!-- hpom: file: NEW_PROJECT_WIZARD.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-115 build, amended TASK-126 (Emergence capacity requirement) -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP New Project Wizard

Step-by-step checklist for bootstrapping a new project under
`Projects/<PROJECT_NAME>/`. See `PROJECT_BOOTSTRAPPING_SYSTEM.md` for the
reasoning behind each step.

## Steps

1. **Create the folder layout** per `notes/brain-organization-guide.md`:
   `AGENTS.md`, `README.md`, `shared/`, `tasks/`, `workflow/`, `notes/`,
   `templates/`, `artifacts/`, `handoffs/`, `inbox/`, `events/`, `archive/`.
2. **Write `shared/project-brief.md`** — objective and completion
   condition. Copy `templates/project-brief.md`-equivalent structure from
   the MAP-system one if unsure of shape.
3. **Write `shared/requirements.md`** — quality standards specific to this
   project. If none are known yet, state that explicitly rather than
   leaving the file empty and undocumented.
4. **Log known assumptions and research needs.** If the project depends
   on facts not yet verified (an external API, a library's behavior, a
   domain constraint), open a Research Brief per `RESEARCH_SYSTEM.md`
   under `Projects/<PROJECT_NAME>/research/briefs/`. If there are no
   research needs yet, say so in `shared/unresolved-questions.md`.
5. **Log known risks.** Create
   `Projects/<PROJECT_NAME>/risks/RISK_REGISTER.md` using
   `templates/RISK_REGISTER_TEMPLATE.md`, even if it starts with zero
   entries — the file existing is the signal that risk is being tracked
   from day one.
6. **State decision paths.** Add a short note (in `shared/decisions.md`
   or a project-specific equivalent) naming which decision classes this
   project expects to make locally (per `DECISION_CLASSES.md`) versus
   escalate to command-center.
7. **Create Emergence capacity.** Create empty
   `Projects/<PROJECT_NAME>/insights/`, `ideas/`, `experiments/`, and
   `synthesis/` folders per `emergence/README.md`'s project-level layout
   — even before the first insight exists, so the folders are there when
   one surfaces. See DEC-026/TASK-126: this step was added after an
   entire project (ProjectUpdater) shipped without a single Emergence
   artifact because nothing required it.
8. **Only then write the first task** in `tasks/`, following
   `notes/task-authoring-guide.md`.
9. **Consider Emergence capture at every task's submission, not just at
   bootstrap.** Before marking a task's release checklist complete, ask:
   did anything happen here worth an `INS-NNNN` insight or `IDEA-NNNN`
   card? Use `MAP_System/scripts/map_emergence.py insight`/`idea`
   `--project <PROJECT_NAME>` if so. "Nothing worth capturing" is a valid
   answer — but it must be a considered answer, not a skipped step. This
   is mechanically required: `scripts/release_task.py` blocks release
   without an "Emergence capture considered" line in the release
   checklist (per `CHANGE_CONTROL_SYSTEM.md`).

## Skip conditions

Skip steps 3-7 for a genuinely trivial or throwaway project (see
`shared/hpom.md` routing questions). Do not skip them for anything
expected to accumulate multiple tasks, multiple agents, or span more than
one session. Step 9 (per-task Emergence consideration) is never skipped
once a project has any release-gated task, regardless of project size —
it costs one line in a checklist, not a new folder or document.

## Verification

A bootstrapped project should be able to answer, without reading any
task file:

- What is this project trying to do? (`project-brief.md`)
- What does good work look like here? (`requirements.md`)
- What do we not yet know? (research briefs / unresolved-questions.md)
- What could go wrong? (risk register)
- Who decides what? (decision-paths note)
- Where would an insight or idea go if one surfaced? (`insights/`/`ideas/`
  folders existing, even empty)

If any of these six questions has no answer, the bootstrap is incomplete.

## Related files

- `PROJECT_BOOTSTRAPPING_SYSTEM.md` [[PROJECT_BOOTSTRAPPING_SYSTEM]] — the reasoning behind this checklist
- `notes/brain-organization-guide.md` [[brain-organization-guide]] — the folder layout this wizard
  populates
- `RESEARCH_SYSTEM.md` [[RESEARCH_SYSTEM]], `RISK_SYSTEM.md`, `DECISION_AUTHORITY_SYSTEM.md` —
  the systems steps 4-6 draw from
- `emergence/README.md` [[emergence/README]] — the layout and CLI for steps 7 and 9
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — the release-checklist gate enforcing step 9
