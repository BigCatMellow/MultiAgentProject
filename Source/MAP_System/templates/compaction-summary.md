# Compaction Summary: [date-or-scope]

## Header

- Date: `[YYYY-MM-DD]`
- Thread: `[THREAD-... | none]`
- Compactor: `[agent-id]`
- Reviewer: `[agent-id | pending]`
- Scope: `[tasks | dates | event range | phase]`
- Status: `[draft | reviewed | applied]`

## Sources

- `[path]` - `[raw events | task | handoff | review | decision | artifact]`

## Tasks

- `TASK-NNN`
  - Status: `[DONE | APPROVED | other]`
  - Outcome: `[terse result]`
  - Canonical output: `[path | none]`

## Outcomes

- `[durable fact future agents need]`

## Decisions

- `DEC-NNN` - `[preserved | superseded | added]` - `[short label]`

## Questions

- Closed: `[question]` -> `[answer/path | none]`
- Open: `[question]` -> `[shared/unresolved-questions.md | task | none]`

## Follow-Ups

- `[priority]` - `[action]` - `[owner/task/path]`

## Active Updates

- `[path]` - `[updated | trimmed | linked | unchanged]` - `[short note]`

## Archive Links

- Raw detail: `[path]`
- Prior compaction: `[path | none]`
- Related thread: `[path | none]`

## Exceptions

- `[conflict, uncertainty, or review need | none]`
