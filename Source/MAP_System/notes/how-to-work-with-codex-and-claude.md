# How Codex And Claude Code Should Collaborate Here

Use Codex and Claude Code as interchangeable workers with different strengths, not as permanent personalities.

Recommended loop:

1. Human or coordinator creates a task in `tasks/` and `workflow/task_graph.json`.
2. One agent claims or is assigned the task.
3. The agent reads only relevant shared docs and input paths.
4. The agent writes artifacts to the task's output paths.
5. The agent creates a handoff or review request.
6. The other agent reviews the artifact against the task acceptance criteria.
7. Required fixes become a revision task or a changes-requested handoff.
8. Approved work is integrated and the next blocked tasks are unlocked.

Avoid asking both agents to edit the same file at the same time unless one of them is explicitly reviewing a diff.

