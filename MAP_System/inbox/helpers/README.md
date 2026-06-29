# Helper Agent Notes

This directory stores durable notes for temporary command-center helper agents.

Use one file per helper tag:

```text
helper-research-01.md
helper-review-ui.md
helper-langgraph.md
```

Each note should include:

- helper tag;
- provider or tool, such as Codex, Claude, or Antigravity;
- terminal mode and command-center reachability;
- owning core agent;
- thread ID when the helper is part of a multi-message exchange;
- assigned task or question;
- relevant input paths;
- findings, decisions, and handoff notes;
- whether the helper is active, stopped, or replaced.

The helper process can come and go. This note is the memory that lets a future helper resume the same scope.

Do not run helpers or assistants in an unreachable background mode. Headless
`hcom` is allowed only when the AI Command Center can inspect and interact with
the active helper session.

When a helper talks directly to a non-owning core agent, record the exchange in
the helper note or link to the inbox thread. Summarize the result back to the
owning core agent.
