# MAP Emergence Preflight Spec (TASK-153, Wave 5)

Status: draft-active
Owner: command-center
Built by: TASK-153

## Purpose

Emergence can notice useful ideas, but it must not silently redirect a task.
Preflight suggestions are bounded recommendations shown before or during task
shaping. They help agents discover relevant capabilities and prior ideas
without turning every suggestion into scope creep.

## Preflight Passes

### Capability Pass

Question: "Does MAP already have a capability or pattern that should be used?"

Inputs:

- task title/description;
- acceptance criteria;
- output paths;
- `shared/subsystem-apis.md`;
- relevant system files named by the context packet;
- local-helper guide when local lanes are considered.

Output:

- candidate capability;
- source path;
- confidence;
- reason;
- whether it changes scope.

### Coverage Pass

Question: "Is there an existing insight, idea, repair, or review finding that
warns about this shape of work?"

Inputs:

- `emergence/INDEX.md`;
- recent promoted ideas;
- repair records for matching drift;
- task review findings for similar files;
- Round 5 learning-guard evidence when local/helper learning is involved.

Output:

- suggestion;
- source artifact;
- confidence;
- suggested action;
- "must not silently add" flag.

## Suggestion Confidence

| Confidence | Meaning | Allowed use |
|---|---|---|
| `high` | Directly matches task files, acceptance criteria, or subsystem API. | May be added to context or checklist by core owner. |
| `medium` | Pattern match, similar prior task, or related insight. | May be mentioned as a candidate; core owner decides. |
| `low` | Loose association or speculative analogy. | Capture as an insight if useful; do not affect task scope. |

## When Suggestions Must Not Be Silently Added

Suggestions require explicit core-owner or command-center handling when they:

- add output paths;
- change acceptance criteria;
- change authority or policy;
- introduce a new dependency;
- require external research;
- change local/helper routing;
- touch security, budget, publication, or destructive-action policy;
- conflict with the task's context packet exclusions.

If any of these are true, the suggestion becomes either:

- an hcom request to the operator;
- a follow-on task;
- an emergence insight/idea;
- a note in the review record.

It does not become hidden scope.

## Output Shape

```json
{
  "task_id": "TASK-NNN",
  "capability_pass": [
    {
      "suggestion": "Use scripts/validate_task_mirrors.py",
      "source": "MAP_System/shared/subsystem-apis.md",
      "confidence": "high",
      "scope_change": false
    }
  ],
  "coverage_pass": [
    {
      "suggestion": "Watch for duplicate state copies",
      "source": "MAP_System/repairs/...",
      "confidence": "medium",
      "must_not_silently_add": true
    }
  ]
}
```

## Governance

Emergence preflight is advisory. It can inform a dispatch packet, but only
promoted ideas or approved task changes alter project scope. This preserves
the Emergence System rule: notice freely, act carefully, promote deliberately.
