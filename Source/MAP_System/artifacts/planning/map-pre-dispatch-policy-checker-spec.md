# MAP Pre-Dispatch Policy Checker Spec (TASK-156, Wave 8)

Status: draft-active
Owner: command-center
Built by: TASK-156

## Purpose

The pre-dispatch policy checker decides whether a task may be assigned before
an agent starts work. It applies existing MAP authority rules at the assignment
boundary instead of waiting for review to catch an unsafe assignment.

This is a design artifact only. TASK-156 does not implement the checker.

## Inputs

The checker reads:

- `AGENT_PERMISSION_LEVELS.md` for tier capabilities;
- `DESTRUCTIVE_ACTION_POLICY.md` for hard-to-reverse action gates;
- `DECISION_CLASSES.md` for decision authority class;
- `DECISION_AUTHORITY_SYSTEM.md` for who may make decisions binding;
- `SECURITY_PERMISSIONS_SYSTEM.md` for trust-boundary crossings;
- `RISK_SYSTEM.md` and risk class/severity metadata for escalation;
- task packet fields: `task_id`, `task_type`, `role`, `owner`,
  `required_agent`, `output_paths`, `description`, `acceptance_criteria`,
  `task_tier`, `risk_class`, `decision_class`, `destructive_action`, and
  `requires_operator_approval`.

Missing policy metadata should not silently downgrade risk. If the checker
cannot classify the assignment, it returns `require_approval` for core agents
and `reject` for helpers/local assistants when the task crosses authority,
machine, network, or destructive boundaries.

## Outputs

The checker emits exactly one decision:

| Decision | Meaning |
|---|---|
| `allow` | Assignment is within the worker's tier, task scope, decision authority, and risk rules. |
| `require_approval` | Assignment might be valid, but needs command-center or owning core-agent approval before work starts. |
| `reject` | Assignment violates a hard capability or authority boundary. |

Result record fields:

| Field | Meaning |
|---|---|
| `task_id` | Task being assigned. |
| `candidate_worker` | Agent/helper/local lane proposed for assignment. |
| `worker_tier` | HPOM/permission tier. |
| `decision` | `allow`, `require_approval`, or `reject`. |
| `reasons` | Short rule IDs explaining the result. |
| `approval_authority` | `command-center`, `owning-core-agent`, or null. |
| `required_evidence` | Approval, decision ID, repair record, risk entry, or validator output needed before dispatch. |
| `checked_at` | UTC timestamp. |

## Rule Order

Evaluate from hard stops to softer gates:

1. **Worker capability**: reject if the worker tier can never perform the
   task shape.
2. **Ownership and output scope**: require approval or reject if the task
   writes outside declared output paths or another active task's owned paths.
3. **Destructive action**: require explicit pre-assignment approval for any
   destructive operation.
4. **Decision authority**: require command-center for `AUTHORITY` and
   `POLICY`; allow core agents only for in-scope `ARCHITECTURE`,
   `OWNERSHIP`, and ordinary `SCOPE` decisions.
5. **Trust-boundary crossing**: require approval for new external-service
   integration, secrets exposure, machine-wide process changes, or writes
   outside the repo boundary.
6. **Risk class/severity**: require approval for `SECURITY` or `STRUCTURAL`;
   allow or warn for lower-risk work according to tier.
7. **Task tier/local lane**: apply TASK-153 tiering rules for helper/local
   suitability.

The highest-severity applicable rule wins. For example, a helper may be able
to draft a recommendation, but if the task is final review or destructive
execution, the result is `reject`.

## Tier Behavior

| Worker tier | Allowed by default | Requires approval | Rejected |
|---|---|---|---|
| Tier 0 command-center | any assignment | none by checker | none by checker |
| Tier 1 core agent | own task outputs, architecture/ownership decisions in scope, normal shell/research | destructive actions, AUTHORITY/POLICY proposals, structural/security risks | acting outside explicit workspace/scope |
| Tier 2 visible helper | bounded read/review/draft work delegated by core | scoped writes explicitly delegated by owning core | final approval, final decision, broad rewrite, destructive operation |
| Tier 3 local assistant | draft-only summaries/checks | none; core must convert draft to task output | shell, network, canonical mutation, approval, decision |
| Tier 4 local Aider wrapper | named-file edits under wrapper constraints | none; wrapper handles baseline gates | broad file scope, unsafe flags, decisions, destructive operations |

## Destructive-Action Gate

Destructive-action checks happen before assignment.

If `destructive_action=true` or description/command metadata indicates a
hard-to-reverse action, the checker returns:

- `require_approval` for Tier 1 core agents, with required evidence naming
  the specific operator instruction or decision;
- `reject` for helpers, local assistants, and Aider lanes;
- `allow` only for command-center or for a narrow class already authorized by
  a valid decision.

The gate should trigger on deletion, force push, hard reset, service restart,
dependency downgrade/removal, safety-check bypass flags, shared-commit rewrite,
or any action marked hard to undo by `DESTRUCTIVE_ACTION_POLICY.md`.

## Decision-Class Gate

| Decision class | Core agent dispatch | Helper/local dispatch |
|---|---|---|
| `ARCHITECTURE` | allow if inside approved scope | helper may draft/review; local draft only |
| `OWNERSHIP` | allow if not reassigning another active owner without evidence | helper/local may not finalize |
| `SCOPE` | allow if inside existing project scope; require approval if expanding unsupervised touch surface | helper/local may draft only |
| `AUTHORITY` | require command-center approval before binding | reject final decision; draft only if delegated |
| `POLICY` | require command-center approval before binding | reject final decision; draft only if delegated |

The checker distinguishes assignment to draft a proposal from assignment to
make a binding decision. Final decision tasks require an approver whose tier
matches `DECISION_AUTHORITY_SYSTEM.md`.

## Risk Gate

Risk metadata should include class and severity when known.

Rules:

- `SECURITY` class or `STRUCTURAL` severity: require command-center approval
  unless the task is a bounded read-only investigation.
- `BLOCKING`: allow core-agent mechanical mitigation; require approval if the
  mitigation needs judgment beyond existing policy.
- `DRIFT`: allow core agents; helpers may inspect/draft; local only when the
  lane is explicitly draft-safe.
- unknown risk on a trust-boundary crossing: require approval for core agents,
  reject for helpers/local.

## Runner And Agent-Loop Integration

Runner should call the checker before recommending a claim, helper, or local
lane. Agent loops should call it immediately before claiming in case policy
changed after runner route calculation.

Recommended route effects:

- `allow`: task may appear in `ready_tasks` or helper recommendations.
- `require_approval`: task appears in an approval/gate route with the required
  authority and evidence.
- `reject`: task is removed from dispatch and flagged for reclassification,
  task rewrite, or owner reassignment.

Every non-allow result should be visible in mission-control/attention state
so blocked assignments do not look like missing work.

## Validation Path

Implementation tasks should add tests that:

- Tier 2 helpers cannot receive final review, final decision, broad rewrite,
  or destructive-operation assignments.
- Tier 3 local assistants cannot receive shell/network/canonical write tasks.
- Tier 1 core agents receive `require_approval` for destructive actions and
  AUTHORITY/POLICY decisions.
- Missing risk metadata on trust-boundary crossings fails conservatively.
- Existing safe architecture/documentation tasks still return `allow`.
