# LangGraph Dependency Notes

This bootstrap does not install packages.

When the human approves dependency installation, the implementation task can use:

```bash
python3 -m pip install -r requirements.txt
```

The first real LangGraph implementation should keep these boundaries:

- read canonical tasks from `workflow/task_graph.json` or the future SQLite task board;
- use graph nodes for routing, review loops, and human pauses;
- write durable updates back to project files or SQLite;
- do not hide project truth inside transient graph state.

