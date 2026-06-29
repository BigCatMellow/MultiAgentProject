# Agent Quickstart

Use this checklist when starting a new AI-agent session in this workspace.

## 1. Identify the Work Area

- Reusable agent framework, scripts, databases, task graph, or workflow policy:
  work in `MAP_System/`.
- Pathwell manuscript, story notes, reviews, or Pathwell task records:
  work in `Projects/Pathwell/`.
- General AI operating guidance:
  read from `Guidelines/`, but do not treat it as a task board.

## 2. Read the Right Instructions

- Always read root `AGENTS.md`.
- For reusable MAP work, read `MAP_System/AGENTS.md`.
- For Pathwell work, read `Projects/Pathwell/AGENTS.md` and then
  `Projects/Pathwell/MAP_System/AGENTS.md` if you are touching its task system.

## 3. Find Current State

- Reusable MAP tasks: `MAP_System/tasks/`
- Reusable MAP project truth: `MAP_System/shared/`
- Reusable MAP event log: `MAP_System/events/events.jsonl`
- Pathwell tasks: `Projects/Pathwell/MAP_System/tasks/`
- Pathwell project truth: `Projects/Pathwell/MAP_System/shared/`
- Pathwell story source: `Projects/Pathwell/Story_Files/` and `Projects/Pathwell/Chapters/`

## 4. Work Durably

Record non-trivial progress in the relevant MAP files:

- task JSON in `tasks/`
- append-only event records in `events/events.jsonl`
- handoff packets in `handoffs/`
- review or planning artifacts in `artifacts/`
- unresolved questions in `shared/unresolved-questions.md`

## 5. Verify Before Handing Off

- Run the relevant validator when task graph files change.
- Prefer focused tests or scripts for code changes.
- Summarize changed files, verification, and any remaining risk.
