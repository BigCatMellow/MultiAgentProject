<!-- hpom: file: shared/canonical-repo.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-02 -->
<!-- hpom: verified_against: TASK-090 post-restart reconciliation / DEC-014 / hcom #17759 -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: DEC-012 canonical path section -->
<!-- hpom: superseded_by: NONE -->

# Canonical Repository Status

Status: current operating rule until command-center explicitly changes it.
Decision: DEC-014. Supersedes the path-specific rule from DEC-012.

## Canonical Local Repo

Use this repo as canonical for current MAP work:

```text
/home/home/Projects/MultiAgentProject
```

Reason:

- TASK-079 completed the prior repo reconciliation work that DEC-012 required.
- The previous canonical path, `/home/home/Downloads/MultiAgentProject`, is no
  longer the live working path.
- Current live command-center sessions, task work, RnS watcher state, and
  recent authorized pushes are operating from
  `/home/home/Projects/MultiAgentProject`.
- Operator hcom #17759 instructed agents to stop waiting and keep working when
  work remains; TASK-090 applies that confirmation to refresh this stale shared
  state.
- DEC-014 records the updated canonical path.

## Retired Path

Do not use this old path as authority for current MAP work:

```text
/home/home/Downloads/MultiAgentProject
```

If it exists again later, treat it as a non-canonical clone or archive until a
new explicit decision says otherwise.

## Git Operation Rule

Repository-global operations require a Git operation owner/lock before action.
Use `MAP_System/scripts/git_operation_lock.py`.

Normal task-scoped commits and pushes from the canonical Projects repo are
allowed when the task owner has staged only owned paths, validators pass, and
the usual MAP review/release rules are followed.
