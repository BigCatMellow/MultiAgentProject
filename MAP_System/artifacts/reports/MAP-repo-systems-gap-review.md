# MAP Repository Systems Gap Review

## Scope

Repository reviewed:

```text
BigCatMellow/MultiAgentProject
```

Purpose of this review:

```text
Compare the current repository state against the MAP systems list and identify what still needs to be built, formalized, or hardened.
```

This review is based on inspecting the GitHub repository structure and key MAP files. It does not include a local runtime test.

---

# Executive Summary

MAP is farther along than the earlier missing-systems list assumed.

The repository already has substantial implementation or documentation for:

```text
HPOM / execution routing
task claiming
review and release gates
SQLite-backed task coordination
LangGraph runner
autonomous claim loop
emergence system
local helper / Ollama policy
memory map
context routing
brain compaction
event validation
metrics dashboard
git operation lock
agent availability tracking
```

The most important missing or under-formalized system is:

```text
MAP Research System
```

The system is already strong at moving work safely, recording decisions, reviewing outputs, and capturing ideas. Its biggest weakness is now knowledge acquisition:

```text
How does MAP know what is true before it builds on it?
```

That is the gap the Research System should fill.

---

# Repository State Observed

The root repository separates:

```text
MAP_System/          Reusable multi-agent project system
Projects/Pathwell/   Active project using MAP
Projects/Backups/    Backups and snapshots
Guidelines/          General AI collaboration rules
docs/                Human and agent navigation docs
launchers/           Local agent terminal launchers
archive/             Retired scratch files
```

The root README identifies `MAP_System/` as the reusable system and `Projects/Pathwell/` as the active project using it.

The root agent instructions route work clearly:

```text
Reusable system work → MAP_System/
Pathwell work        → Projects/Pathwell/
```

The repo already has durable-file coordination as a core principle:

```text
task records
shared notes
handoffs
events
review artifacts
inbox notes
```

---

# Current System Comparison

| System | Status | Notes |
|---|---:|---|
| HPOM / execution model | Strong / active | HPOM is defined as the assignment and routing layer over MAP. |
| Task claiming / ownership | Strong / active | SQLite-backed task claiming exists through `MAP_System/map.db` and `MAP_System/db/claims.py`. |
| Review / release gates | Strong / active | READY, review, release, no-self-review, conflict freeze, shared-state metadata, decision log, task ID allocation, and other gates are active. |
| Emergence System | Strong / active | Full emergence layer exists with insights, synthesis, ideas, experiments, promotions, templates, index, and CLI support. |
| Local agent / Ollama token-saving system | Good / partial-to-strong | Local models are helper capabilities only, used for summaries, classification, checklist results, drafts, recommendations, and diff suggestions. |
| Memory System | Partial / strong notes | `shared/memory-map.md` defines canonical memory, historical memory, and read order, but there is not a standalone `MEMORY_SYSTEM.md`. |
| Context System | Partial / strong guide | `notes/context-routing-guide.md` exists and is useful, but context is important enough to formalize as a system. |
| Decision / Authority System | Partial / strong decision log | Decisions are well-recorded, but authority classes and decision rights should be formalized separately. |
| Self-Repair System | Partial | Repair behavior exists through health checks, validation, improvement backlog, stale reports, and runbooks, but there is no formal module yet. |
| Research System | Missing / highest priority | Research exists only as an artifact category, not a process. No formal source evaluation, assumption register, or claim evidence matrix. |
| Risk System | Partial | Risk appears in review severity, security rules, current-state issues, and backlog, but not as a formal risk system. |
| Security / Permissions System | Partial | Security second-pass rule exists; handler execution safety is tracked as open. Needs formal permission model. |
| Orchestration System | Strong / active | LangGraph runner, autonomous loop, hcom helper routing, agent availability, and route-around-unavailable-agent behavior exist. |
| Human Interface System | Partial / planned | CommandCenterUI prototype exists; live hcom/MAP state wiring is still open. |
| Change Control System | Partial | Git wrapper, git operation lock, canonical repo decisions, and release-path checklist exist; full change-control policy still missing. |
| Project Bootstrapping System | Partial | `brain-organization-guide.md` provides a strong new-project structure, but no formal bootstrap wizard/workflow exists. |
| Archive / Retention System | Partial | Brain compaction guide exists and is useful, but archive/retention could be formalized. |
| Retrospective / Learning System | Weak / implied | Improvement backlog and compaction exist, but no formal retrospective loop exists. |

---

# What Is Already Strong

## 1. HPOM / Execution

HPOM is not just an idea in the repo. It is already defined as the assignment layer over MAP.

It answers questions like:

```text
Who or what should do this work?
Is this safe for a local assistant?
Does this need a core agent?
Does this need human approval?
Would a helper add value, or just burn tokens?
```

The repo also defines authority tiers:

```text
Tier 0: command-center / human
Tier 1: core agents
Tier 2: visible temporary helpers
Tier 3: local assistants / Ollama
Tier 4: Aider with local model
```

This means MAP already has a working structure for assigning work by fit instead of availability.

---

## 2. Task Claiming

The repo uses SQLite-backed task claiming through:

```text
MAP_System/map.db
MAP_System/db/claims.py
```

Agents are instructed not to manually edit task JSON files to claim work.

The task files remain human-readable mirrors of SQLite state.

This is a strong design because it prevents multiple agents from silently claiming the same task.

---

## 3. Review and Release Gates

The current state file says the following gates are active:

```text
READY promotion
No-self-review
Review gate
Release gate
Conflict freeze
Shared-state metadata
Decision log
Metrics dashboard
Task ID allocation
Event log report
Emergence stale report
Git operation lock
```

This means MAP already has a real gate structure.

Earlier we were treating pass/fail gates as mostly theoretical; the repository shows many of them are already implemented or at least operationally active.

---

## 4. Emergence System

The Emergence System is already formalized.

It has:

```text
README.md
SYNTHESIS_METHODS.md
IDEA_PROMOTION_RULES.md
CREATIVE_REVIEW.md
INDEX.md
templates/
insights/
synthesis/
ideas/
experiments/
promotions/
```

It also has a CLI:

```bash
python3 MAP_System/scripts/map_emergence.py insight "Short observation"
python3 MAP_System/scripts/map_emergence.py idea "Possible improvement"
python3 MAP_System/scripts/map_emergence.py promote IDEA-0001
python3 MAP_System/scripts/map_emergence.py validate
```

The important rule is already present:

```text
Notice freely.
Act carefully.
Promote deliberately.
```

This matches the desired “blue + yellow = green” capability.

The system can capture creative discoveries without letting them silently redirect the project.

---

## 5. Local Agent / Ollama Policy

The repo already has a useful local-model helper guide.

Local assistants are clearly limited to:

```text
summary
classification
checklist-result
draft
recommendation
diff-suggestion
```

They are denied:

```text
final-decision
approved-review
task-completion-claim
unbounded-rewrite
architecture-change
```

This means the token-saving philosophy is already captured:

```text
Local agents prepare, compress, check, and draft.
Core agents decide, integrate, approve, and resolve.
```

---

## 6. Memory and Context Hygiene

MAP already has a strong memory map.

It distinguishes:

```text
canonical operating memory
operating runbooks
runtime/workflow context
historical memory
```

It also tells agents not to load the entire Markdown tree by default.

The context routing guide already defines:

```text
default context stack
common read sets
when to stop reading
when to follow more links
priority order during conflicts
```

This is a strong foundation for a formal Context System.

---

# Biggest Gaps

## 1. Research System

This is the highest-priority missing system.

The repo has places where research artifacts can live, but it does not yet have a formal research process.

Missing pieces:

```text
research question format
source map
source quality ratings
claim extraction rules
claim evidence matrix
assumption register
contradiction handling
date-sensitivity rules
research summary format
research-to-decision workflow
```

This matters because MAP can currently do work safely once it has project truth, but it does not yet strongly define how truth is discovered.

The Research System should answer:

```text
What do we need to know before we act?
How do we know it is true?
What assumptions are we making?
What sources are authoritative?
What claims are still uncertain?
```

Recommended file:

```text
MAP_System/RESEARCH_SYSTEM.md
```

Recommended project folders:

```text
Projects/<PROJECT_NAME>/research/
  briefs/
  sources/
  evidence/
  assumptions/
  summaries/
```

Recommended templates:

```text
RESEARCH_BRIEF_TEMPLATE.md
SOURCE_MAP_TEMPLATE.md
SOURCE_EVALUATION_TEMPLATE.md
CLAIM_EVIDENCE_MATRIX_TEMPLATE.md
ASSUMPTION_REGISTER_TEMPLATE.md
RESEARCH_SUMMARY_TEMPLATE.md
```

Core rule:

```text
Do not let assumptions become architecture.
Do not let unsourced claims become project truth.
Do not let outdated knowledge guide current decisions.
```

---

## 2. Formal Self-Repair System

Self-repair already exists in pieces:

```text
repair checklist
known health issues
improvement backlog
event validation
agent reconciliation
emergence stale report
shared-state validation
task graph validation
metrics dashboard
```

But it does not yet appear to have a formal module with:

```text
repair severity levels
repair records
health check reports
automatic repair permissions
repair escalation rules
verification plans
follow-up prevention rules
```

Recommended file:

```text
MAP_System/SELF_REPAIR_SYSTEM.md
```

Recommended folders:

```text
MAP_System/repairs/
Projects/<PROJECT_NAME>/repairs/
Projects/<PROJECT_NAME>/health/
```

Core rule:

```text
MAP can repair structure automatically.
MAP can propose repairs to authority.
MAP cannot silently rewrite its own authority.
```

---

## 3. Context System

The context routing guide is already useful, but context is important enough to be promoted into a formal system.

The Context System should define:

```text
context packet format
required context by task type
optional context
forbidden context loading
stale context handling
token-budget rules
local summarizer role
context compression rules
```

Recommended file:

```text
MAP_System/CONTEXT_SYSTEM.md
```

Recommended template:

```text
MAP_System/templates/CONTEXT_PACKET_TEMPLATE.md
```

Core rule:

```text
Every task should have a context packet, not a context dump.
```

---

## 4. Decision / Authority System

The decision log is strong, but authority rights should be formalized separately.

The system should answer:

```text
Who can decide what?
What requires human approval?
What can a core agent decide?
What can a helper recommend only?
What can a local model never decide?
How are decisions superseded?
How are decisions promoted from proposals?
```

Recommended files:

```text
MAP_System/DECISION_AUTHORITY_SYSTEM.md
MAP_System/DECISION_CLASSES.md
MAP_System/AUTHORITY_HIERARCHY.md
```

Core rule:

```text
Agents may recommend decisions.
Only the proper authority may make them binding.
```

---

## 5. Human Interface System

The repo already has a CommandCenterUI prototype or related work, but live MAP/hcom state wiring is still open.

The Human Interface System should define what the operator sees without reading the whole repository.

It should surface:

```text
current dashboard
pending decisions
blocked tasks
review queue
open repairs
open research questions
recent insights
agent availability
next recommended actions
```

Recommended file:

```text
MAP_System/HUMAN_INTERFACE_SYSTEM.md
```

Recommended project file:

```text
Projects/<PROJECT_NAME>/DASHBOARD.md
```

Core rule:

```text
The human should see decisions, risks, and next actions — not raw system noise.
```

---

# Secondary Gaps

## Risk System

Risk is present, but scattered.

It appears in:

```text
review severity levels
security second-pass rules
current-state health issues
improvement backlog
constraints
```

A formal Risk System should define:

```text
risk classes
risk severity
risk register
risk owners
risk review cadence
risk escalation
risk acceptance
```

Recommended file:

```text
MAP_System/RISK_SYSTEM.md
```

Recommended project file:

```text
Projects/<PROJECT_NAME>/risks/RISK_REGISTER.md
```

---

## Security / Permissions System

Security rules exist in pieces.

The repo already has a security second-pass rule for network-facing or write-capable outputs.

Still missing:

```text
agent permission levels
read/write/delete boundaries
shell command permissions
network access policy
secret handling
destructive action policy
external service policy
trust boundary model
```

Recommended files:

```text
MAP_System/SECURITY_PERMISSIONS_SYSTEM.md
MAP_System/AGENT_PERMISSION_LEVELS.md
MAP_System/DESTRUCTIVE_ACTION_POLICY.md
```

Core rule:

```text
Agents should have the least permission needed to complete the task.
```

---

## Change Control System

Current pieces:

```text
normal Git
map-git wrapper
git operation lock
canonical repo decisions
release-path smoke checklist
```

Missing formal pieces:

```text
change request format
release record
rollback notes
changelog policy
diff review requirement
migration notes
version tags
artifact retirement rules
```

Recommended file:

```text
MAP_System/CHANGE_CONTROL_SYSTEM.md
```

Recommended project folder:

```text
Projects/<PROJECT_NAME>/changes/
  CHANGELOG.md
  RELEASES.md
  ROLLBACK_NOTES.md
```

---

## Project Bootstrapping System

The repo already has a strong brain organization guide.

That guide provides a project brain layout with:

```text
AGENTS.md
README.md
shared/
tasks/
workflow/
notes/
templates/
artifacts/
handoffs/
inbox/
events/
archive/
```

But there is no formal new-project wizard or bootstrap workflow.

Recommended files:

```text
MAP_System/PROJECT_BOOTSTRAPPING_SYSTEM.md
MAP_System/NEW_PROJECT_WIZARD.md
```

Recommended template folder:

```text
MAP_System/templates/PROJECT_STARTER_PACK/
```

Core rule:

```text
No new project should begin with only tasks.
It should begin with intent, assumptions, research needs, quality standards, risks, and decision paths.
```

---

## Archive / Retention System

The brain compaction guide is already good.

It defines:

```text
when to compact
what to preserve
what to archive
what active memory should stay concise
what raw history should not be deleted
```

This could be promoted into:

```text
MAP_System/ARCHIVE_RETENTION_SYSTEM.md
```

It should define:

```text
archive statuses
retention rules
compaction cadence
how to mark stale artifacts
how to distinguish history from current truth
```

Core rule:

```text
Do not delete useful history, but do not let old history pretend to be current truth.
```

---

## Retrospective / Learning System

This is still weak.

The improvement backlog captures known improvements, and emergence captures insights. But there is no clear end-of-cycle retrospective system.

A Retrospective System should ask:

```text
What worked?
What failed?
What caused rework?
What did agents misunderstand?
What rules were unclear?
What should become a validator?
What should become a template change?
What should become a decision?
```

Recommended file:

```text
MAP_System/RETROSPECTIVE_SYSTEM.md
```

Recommended project folder:

```text
Projects/<PROJECT_NAME>/retrospectives/
```

Core rule:

```text
Every repeated failure should become a process improvement, validator, template change, or decision.
```

---

# Updated Priority Order

Given the actual repo state, this is the recommended next build sequence.

## 1. Research System

Build first.

Reason:

```text
It prevents assumptions, stale knowledge, and weak sources from becoming project truth.
```

Suggested first deliverables:

```text
MAP_System/RESEARCH_SYSTEM.md
MAP_System/research/README.md
MAP_System/templates/research/RESEARCH_BRIEF_TEMPLATE.md
MAP_System/templates/research/ASSUMPTION_REGISTER_TEMPLATE.md
MAP_System/templates/research/CLAIM_EVIDENCE_MATRIX_TEMPLATE.md
```

---

## 2. Self-Repair System

Build second.

Reason:

```text
The repo already has many repair behaviors. Formalizing them will reduce drift and make health checks more coherent.
```

Suggested first deliverables:

```text
MAP_System/SELF_REPAIR_SYSTEM.md
MAP_System/templates/REPAIR_RECORD_TEMPLATE.md
MAP_System/templates/HEALTH_CHECK_REPORT_TEMPLATE.md
MAP_System/repairs/README.md
```

---

## 3. Context System

Build third.

Reason:

```text
It connects memory, research, local agents, token savings, and task quality.
```

Suggested first deliverables:

```text
MAP_System/CONTEXT_SYSTEM.md
MAP_System/templates/CONTEXT_PACKET_TEMPLATE.md
```

---

## 4. Decision / Authority System

Build fourth.

Reason:

```text
As MAP gains more autonomous behavior, it needs clearer authority boundaries.
```

Suggested first deliverables:

```text
MAP_System/DECISION_AUTHORITY_SYSTEM.md
MAP_System/DECISION_CLASSES.md
```

---

## 5. Human Interface System

Build fifth.

Reason:

```text
The operator needs a control surface that summarizes decisions, risks, blocked work, reviews, repairs, and next actions.
```

Suggested first deliverables:

```text
MAP_System/HUMAN_INTERFACE_SYSTEM.md
Projects/<PROJECT_NAME>/DASHBOARD.md
```

---

# Updated MAP Architecture

The repo currently supports or implies this architecture:

```text
MAP
├── HPOM
│   └── worker-fit routing, task execution, review, release
│
├── Emergence System
│   └── insight, synthesis, ideas, experiments, promotion
│
├── Local Helper System
│   └── Ollama/Aider support for summaries, checks, drafts, and diff suggestions
│
├── Memory System
│   └── durable project memory, current state, decisions, and historical context
│
├── Context System
│   └── task-specific context loading and context pruning
│
├── Orchestration System
│   └── LangGraph runner, autonomous claim loop, helper routing
│
├── Review / Release Gate System
│   └── READY, review, release, conflict, decision, shared-state, metrics gates
│
└── Improvement / Maintenance Layer
    └── backlog, compaction, health checks, stale reports
```

The missing or under-formalized future architecture should add:

```text
Research System
Self-Repair System
Decision / Authority System
Risk System
Security / Permissions System
Human Interface System
Change Control System
Project Bootstrapping System
Archive / Retention System
Retrospective System
```

---

# Practical Recommendation

Do not rebuild what already exists.

The next move should be to create the Research System as a clean standalone MAP module that plugs into the existing system.

It should not replace HPOM, Emergence, Memory, or Context.

It should feed them.

Recommended flow:

```text
Research Question
→ Research Brief
→ Source Map
→ Claim Evidence Matrix
→ Assumption Register
→ Research Summary
→ Decision or HPOM Task
```

Relationship to other systems:

```text
Research verifies facts.
Emergence creates new possibilities from those facts.
HPOM executes approved work based on those facts.
Self-Repair detects when facts become stale or contradictory.
Memory stores the verified result.
Context loads the right verified result for the next task.
```

---

# Final Assessment

MAP is no longer just a file-backed multi-agent experiment.

It already has the core of a durable operating system for agent work.

Current strength:

```text
execution
coordination
review
release
emergence
local helper boundaries
memory hygiene
context routing
task claiming
validation
```

Current weakness:

```text
research discipline
formal self-repair
formal authority boundaries
formal risk and security model
operator dashboard
```

Highest-value next system:

```text
MAP Research System
```

Reason:

```text
The system can already move work.
Now it needs a stronger way to know what is true before work begins.
```
