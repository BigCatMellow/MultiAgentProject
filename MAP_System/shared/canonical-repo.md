<!-- hpom: file: shared/canonical-repo.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-02 -->
<!-- hpom: verified_against: TASK-065 / DEC-012 canonical repo remediation -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Canonical Repository Status

Status: current operating rule until command-center explicitly changes it.
Decision: DEC-012.

## Canonical Local Repo

Use this repo as canonical for current MAP work:

```text
/home/home/Downloads/MultiAgentProject
```

Reason:

- This is where the current validated MAP, Pathwell, CommandCenterUI, DarkMellow,
  emergence, audit, and report work happened.
- It has the current task graph and latest submitted audit/report tasks.
- The `/home/home/Projects/MultiAgentProject` copy is a risky hybrid of stale
  git history and manually copied newer files.
- DEC-012 approved this path as canonical after command-center delegated
  remediation decisions via hcom #14454.

## Non-Canonical Copy

Do not push, publish, or use this as a sync source until reconciled:

```text
/home/home/Projects/MultiAgentProject
```

Allowed:

- read-only inspection;
- explicit reconciliation task after command-center review.

Not allowed without a dedicated task and Git operation lock:

- `git add`, `git commit`, `git push`, reset, rebase, or broad sync from that
  location;
- copying Pathwell chapters into it as a partial sync.

## Git Operation Rule

Repository-global operations require a Git operation owner/lock before action.
Use `MAP_System/scripts/git_operation_lock.py`.
