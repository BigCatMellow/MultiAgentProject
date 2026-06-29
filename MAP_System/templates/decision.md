# Decision Entry Template

Copy the block below into `shared/decisions.md` as the next `## DEC-NNN` entry.
All fields are required by `validate_decisions.py`.

```md
## DEC-NNN: [Decision Title]

Status: approved
Owner: [agent-id or command-center]
Date: YYYY-MM-DD
Applies-To: [scope — which tasks, files, processes, or agents this governs]
Reason: [one or two sentences on why this decision was made]
Supersedes: NONE
Superseded-By: NONE

[Optional: additional context, consequences, or tradeoffs.]
```

## Field Guide

| Field | Required | Notes |
|---|---|---|
| `Status` | YES | `approved`, `proposed`, or `superseded by DEC-NNN` |
| `Owner` | YES | Agent or role responsible for this decision |
| `Date` | YES | ISO date: `YYYY-MM-DD` |
| `Applies-To` | YES | Scope statement — what does this govern? |
| `Reason` | YES | Why was this decision made? |
| `Supersedes` | YES | `NONE` or `DEC-NNN` this replaces |
| `Superseded-By` | YES | `NONE` or `DEC-NNN` that replaces this |
