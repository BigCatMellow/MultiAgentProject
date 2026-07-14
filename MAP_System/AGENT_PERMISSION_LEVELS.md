<!-- hpom: file: AGENT_PERMISSION_LEVELS.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-112 build -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Agent Permission Levels

Companion to `SECURITY_PERMISSIONS_SYSTEM.md`. Maps `shared/hpom.md`'s
authority tiers onto concrete read/write/execute/network permissions.

| Tier | Worker | Read | Write | Shell execute | Network | Destructive actions |
|---|---|---|---|---|---|---|
| 0 | command-center / human | Everything | Everything | Anything | Anything | Any, at own discretion |
| 1 | core agents (Codex, Claude) | Everything | Own task's `output_paths`; shared/index files it touches, registered upfront | Read-only and mechanical repair commands freely; anything state-changing per `DESTRUCTIVE_ACTION_POLICY.md` | Research/verification calls freely; new external-service integration requires a decision | Only per `DESTRUCTIVE_ACTION_POLICY.md` confirmation rules |
| 2 | visible temporary helpers | Everything | Scoped to the owning core agent's explicit instruction; no unsupervised write to `shared/` or `tasks/` | Read-only by default; state-changing commands only if the owning core agent explicitly delegates | Research/verification calls if scoped by the task | None — escalate to owning core agent |
| 3 | local assistants / Ollama | Everything | Draft-only; output is not committed until a core agent reviews it | None | None by default | None |
| 4 | Aider with local model | Named files only | Named files only, after baseline checks (`aider_wrapper.py`) | None beyond the wrapper's own git operations | None | None — `FORBIDDEN_AIDER_FLAGS` blocks broad/unsafe flags |

## Reading this table

- "Write" access is always bounded by MAP's existing ownership rule
  (`AGENTS.md` DEC-003, one owner per active task) — a Tier 1 agent's
  broad write permission does not override another task's active
  ownership.
- "Shell execute" distinguishes read-only/mechanical commands (safe by
  default) from state-changing ones (git push, deletions, service
  restarts, config changes) which fall under
  `DESTRUCTIVE_ACTION_POLICY.md`.
- "Network" distinguishes calling an existing, already-approved external
  service from standing up a new integration, which is a decision (see
  `SECURITY_PERMISSIONS_SYSTEM.md` External Service Policy).

## Related files

- `SECURITY_PERMISSIONS_SYSTEM.md` [[SECURITY_PERMISSIONS_SYSTEM]] — the trust-boundary model this table
  implements
- `DESTRUCTIVE_ACTION_POLICY.md` [[DESTRUCTIVE_ACTION_POLICY]] — what counts as destructive at Tier 1
- `shared/hpom.md` [[hpom]] — the base authority tiers
