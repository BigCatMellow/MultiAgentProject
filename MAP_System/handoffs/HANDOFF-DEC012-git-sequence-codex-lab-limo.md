# HANDOFF: DEC-012 Git Sequence

Task ID: DEC-012 follow-through / post TASK-065 batch
Sender: codex-lab-limo
Intended recipient: command-center or next core agent with git write approval
Status: BLOCKED_BY_APPROVAL_LIMIT
Date: 2026-07-02

## Completed Before Blocker

- TASK-065 submitted.
- TASK-075 reviewed and APPROVED.
- TASK-078 reviewed and APPROVED.
- PROMO-0004 and PROMO-0005 approved by codex-lab-limo.
- PROMO-0001 structured approval fields corrected during TASK-075 review.
- Final validators passed:
  - `MAP_System/scripts/run_tests.sh`: `pass=18 fail=0 total=18`
  - `validate_task_graph.py`: pass
  - `validate_shared_state.py`: pass
  - `validate_decisions.py`: pass
  - `map_emergence.py validate`: pass
  - `map_emergence.py stale`: no findings
  - `validate_events.py`: 0 errors, 33 expected historical warnings
  - `validate_review.py`: TASK-075 and TASK-078 review records pass

## Blocker

DEC-012 next step is a single clean commit in canonical repo A:

`/home/home/Downloads/MultiAgentProject`

Staging requires writing `.git/index.lock`, which is outside this session's
writable sandbox. Escalation for `git add .gitignore MAP_System` was rejected
because this Codex session hit its usage/approval limit. The git-operation lock
was released after the failed escalation.

## Safe Commit Scope

Stage only:

- `.gitignore`
- `MAP_System/`

Do not stage:

- `Projects/`

Reason: `Projects/` is untracked/private material. `Projects/Pathwell/` and
`Projects/Backups/` are explicitly ignored; `Projects/DarkMellow/` is also
untracked and should not be swept into the MAP remediation commit without a
separate task/decision.

## Suggested Commands

From `/home/home/Downloads/MultiAgentProject`, with git write approval:

```bash
python3 MAP_System/scripts/git_operation_lock.py acquire \
  --owner <agent-or-operator> \
  --operation "commit-and-push validated MAP remediation batch from canonical repo A" \
  --repo /home/home/Downloads/MultiAgentProject \
  --stop-condition "Stop on validation failure, remote rejection, or staged private Projects content"

git add .gitignore MAP_System
git diff --cached --name-only
git commit -m "Remediate MAP audit findings"
git push origin main

python3 MAP_System/scripts/git_operation_lock.py release --owner <agent-or-operator>
```

Before commit, verify `git diff --cached --name-only` contains no path under
`Projects/`.

## Remaining DEC-012 Steps After Push

1. Preserve B's `Projects/Pathwell/` and `Projects/Backups/`.
2. Freeze or reclone `/home/home/Projects/MultiAgentProject` from remote.
3. Restore/refresh B's private `Projects/Pathwell/` copy from canonical A via
   file sync, not git.
4. Resume Pathwell two-repo sync only after the above is complete.
