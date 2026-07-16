# MAP Multi-Project Readiness Audit (TASK-157, Wave 9)

Status: draft-active
Owner: command-center
Built by: TASK-157

## Purpose

MAP is intended to be reusable across projects, but most current validation is
root-MAP-centric. This audit separates global MAP state from project-local
state and checks the reusable-system claim against Pathwell plus another
project shape.

## Project Shapes Reviewed

| Shape | Example | Notes |
|---|---|---|
| Reusable MAP system | `MAP_System/` | Owns framework rules, validators, task engine, shared decisions. |
| Story project with local MAP | `Projects/Pathwell/` | Has story files plus `Projects/Pathwell/MAP_System/` local task state. |
| Control-plane app/project | CommandCenterUI / future app repo | External or adjacent project that may read MAP state and eventually trigger actions. |

## Global vs. Project-Local State

Global MAP-system state:

- framework rules: `MAP_System/AGENTS.md`, permission, risk, research,
  repair, decision, and security systems;
- reusable validators and scripts under `MAP_System/scripts/`;
- reusable task engine schema and migration code;
- root MAP task graph for framework work;
- global agent roster/status when agents are shared across projects;
- global decisions that define authority or MAP-wide policy.

Project-local state:

- project `AGENTS.md`;
- project task graph, events, handoffs, and shared facts;
- project requirements, constraints, acceptance criteria, and decisions;
- project-specific artifacts, chapters, story canon, or app source;
- project-level risk register and repairs when the exposure is not MAP-wide.

Ambiguous/shared state:

- hcom roster and session availability;
- cost budgets and paid model limits;
- helper capacity;
- operator attention queue;
- CommandCenterUI mission-control views.

Ambiguous state needs explicit scope fields: `system`, `project`, `task`,
`agent`, or `global`.

## Pathwell Fit

Pathwell demonstrates that MAP needs project isolation:

- root `docs/project-map.md` points story work to `Projects/Pathwell/`;
- Pathwell has its own `Projects/Pathwell/MAP_System/AGENTS.md`;
- Pathwell has project-local tasks and events;
- story context lives in `Story_Files/` and should not be treated as reusable
  MAP framework truth;
- Pathwell emergence artifacts are creative discovery until promoted.

Risks:

- root MAP agents may accidentally read Pathwell creative notes as approved
  MAP system requirements;
- reusable MAP validators may be run against the wrong task graph;
- global helper/agent status may obscure project-local ownership;
- shared hcom messages may leak project-specific context into unrelated work.

Needed controls:

- every route/validator command should display the target root;
- project-local task operations should use the project-local scripts/database;
- handoffs should state project ID and root path;
- CommandCenterUI should make active project scope a first-class field.

## Control-Plane App Fit

CommandCenterUI or another app-shaped project differs from Pathwell:

- it may have source code outside root MAP;
- it may read MAP state but should not become canonical writer by default;
- it has runtime/deployment state that is neither Pathwell story state nor MAP
  framework state;
- it can become a high-risk control plane if intervention buttons mutate task
  or agent state.

Needed controls:

- canonical repo path validation;
- read-only UI mode until backend policy checks exist;
- all write actions call sanctioned MAP commands/helpers;
- deployment/environment secrets remain outside durable MAP files;
- UI state includes project scope and stale-data indicators.

## Resource Contention

Cross-project contention points:

- core agent attention;
- helper tab capacity;
- paid model budget;
- local/Ollama availability;
- git operation lock if projects share a repo or worktree;
- operator approvals and hcom request queue;
- filesystem roots and artifact naming.

Recommended policy:

- budget counters include project scope;
- helper limits count global active helpers and project-local helper caps;
- git locks are per repository/worktree, not globally overbroad;
- operator request queue groups by project and severity;
- task output paths must be rooted under the active project.

## Readiness Gaps

1. Runner output does not yet make multi-project scope prominent enough for a
   UI/control-plane operator.
2. Validators are strong for root MAP but need fixture coverage proving they
   do not cross into Pathwell-local state accidentally.
3. Cost and helper-capacity policies need project-scoped counters.
4. CommandCenterUI write controls need a backend policy contract before
   multi-project intervention.
5. Handoffs and compressed context need project/root identifiers treated as
   required fields.

## Recommendation

MAP is structurally ready to host multiple projects only when project scope is
explicit in runner output, hcom handoffs, budgets, helper allocation, and UI
state. Until then, multi-project work should remain conservative: one active
project scope per agent turn, explicit root path in handoffs, and validators
run from the intended project root.
