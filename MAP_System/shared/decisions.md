# Decisions

## DEC-001: Use File-Backed State First

Status: approved

Use JSON, Markdown, and JSONL files for the first collaboration layer. This keeps the system inspectable by both Codex and Claude Code before adding SQLite or a service runtime.

## DEC-002: LangGraph Is The Orchestrator

Status: approved

LangGraph should route task states, review loops, and human pauses. It should not be the canonical database, artifact store, or full project memory.

## DEC-003: One Owner Per Active Task

Status: approved

Each active task has one owner. Other agents may review, comment, or continue after a handoff, but should not silently edit the same owned output paths.

