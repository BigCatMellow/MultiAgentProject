# Review — TASK-019: Software Project Workflow Template

Reviewer: codex  
Date: 2026-06-19  
Verdict: APPROVED

## Acceptance Criteria

| Criterion | Result |
|---|---|
| Defines task_types with role, acceptance criteria shape, and review requirement | PASS |
| Defines stage sequence: spec -> implement -> test -> review -> release | PASS |
| Each stage specifies owner role and gates | PASS |
| Template is self-contained for copying into a new project | PASS |
| Includes worked example task | PASS |

## Verification

```bash
python3 -c "import yaml; data=yaml.safe_load(open('MAP_System/workflow/templates/software_project.yaml')); ..."
```

Parsed keys:

```text
['project', 'stages', 'task_types', 'approval_gates', 'review_standard']
['spec', 'implement', 'test', 'review', 'release']
['spec_task', 'implementation_task', 'test_task', 'review_task', 'release_task']
```

No BLOCKER or REQUIRED findings.
