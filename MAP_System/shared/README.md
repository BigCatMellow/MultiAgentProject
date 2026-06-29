<!-- hpom: file: shared/README.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Shared

This directory is MAP's canonical operating memory: durable facts that should be
true now.

Read this directory before relying on historical artifacts. When files here
conflict with old reviews, old test notes, or old handoffs, prefer `shared/`
unless a current task says otherwise.

## Key Files

- `current-state.md` - live capabilities, active risks, and known health issues.
- `memory-map.md` - where MAP stores different kinds of memory.
- `architecture.md` - concise current architecture overview.
- `project-brief.md` - objective and completion condition.
- `requirements.md` - current requirements and capabilities.
- `constraints.md` - safety and workspace boundaries.
- `decisions.md` - approved decisions.
- `unresolved-questions.md` - open questions that still need decisions.
- `improvement-backlog.md` - known improvements that need intentional follow-up.
- `glossary.md` - shared terms.

## What Belongs Here

- Current project truth.
- Approved decisions and unresolved questions.
- Requirements, constraints, and vocabulary.
- Short status documents that future agents should trust first.

## What Does Not Belong Here

- One-off review notes.
- Test transcripts.
- Draft implementation plans.
- Long historical context that is only relevant to one completed task.
