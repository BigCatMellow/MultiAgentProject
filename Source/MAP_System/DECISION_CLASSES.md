<!-- hpom: file: DECISION_CLASSES.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-108 build -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Decision Classes

Companion to `DECISION_AUTHORITY_SYSTEM.md`. Classify every decision before
recording it in `shared/decisions.md`, so the authority-check step has
something concrete to check against.

## Classes

| Class | Question it answers | Example | Minimum approval |
|---|---|---|---|
| `ARCHITECTURE` | How is a system built or structured? | DEC-002 (LangGraph is the orchestrator), DEC-015 (adopt Research System) | Core agent, propose-and-record |
| `OWNERSHIP` | Who owns what, and what can be reassigned? | DEC-003 (one owner per active task) | Core agent, propose-and-record |
| `SCOPE` | What is in or out of bounds for a piece of work? | canonical repo path (DEC-014) | Core agent if inside an already-approved project; command-center if it changes what any agent may touch unsupervised |
| `AUTHORITY` | Who may act, decide, or approve, and at what tier? | this file, `shared/hpom.md` tier changes | Command-center required |
| `POLICY` | A MAP-wide rule that applies across all projects, not one task | security second-pass rule, review severities | Command-center required |

## How to classify

Ask, in order:

1. Does this change who may decide things, or what tier an agent operates
   at? → `AUTHORITY`.
2. Does this change a rule that applies across all of MAP, not just the
   current task or project? → `POLICY`.
3. Does this change what is or is not in bounds for current work? →
   `SCOPE`.
4. Does this change who owns what? → `OWNERSHIP`.
5. Otherwise, if it changes how something is built or structured →
   `ARCHITECTURE`.

If a decision plausibly fits two classes, use the higher-approval class
(`AUTHORITY` > `POLICY` > `SCOPE` > `OWNERSHIP` > `ARCHITECTURE`) and note
both in the decision entry.

## Recording the class

When adding a `DEC-NNN` entry to `shared/decisions.md`, include the class
in the `Applies-To` line or a dedicated `Class:` line so future readers
(and `validate_decisions.py`, if extended) can see the classification
without re-deriving it.

## Related files

- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — the approval routing this table feeds
- `shared/decisions.md` [[decisions]] — where classified decisions are recorded
- `shared/hpom.md` [[hpom]] — the authority tiers underlying approval levels
