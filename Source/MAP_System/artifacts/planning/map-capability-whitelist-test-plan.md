# MAP Capability Whitelist Test Plan (TASK-156, Wave 8)

Status: draft-active
Owner: command-center
Built by: TASK-156

## Purpose

This plan defines tests for the pre-dispatch capability whitelist. It proves
that helpers and local lanes cannot be assigned work outside their authority
before a task begins.

This is a test design artifact. TASK-156 does not implement the tests.

## Test Target

Future implementation should expose a deterministic checker function or CLI
that accepts a task packet plus candidate worker and returns:

```json
{
  "decision": "allow | require_approval | reject",
  "reasons": ["RULE_ID"],
  "approval_authority": "command-center | owning-core-agent | null"
}
```

Tests should exercise the checker directly, then add runner/agent-loop tests
showing the same result blocks assignment.

## Required Deny Cases

| Case | Candidate | Expected |
|---|---|---|
| final review approval | Tier 2 helper | `reject` |
| final decision recording | Tier 2 helper | `reject` |
| broad architecture ownership | Tier 2 helper | `reject` unless task is explicitly draft/review only |
| broad multi-file rewrite | Tier 2 helper | `reject` without owning core delegation and declared paths |
| destructive operation | Tier 2 helper | `reject` |
| destructive operation | Tier 3 local assistant | `reject` |
| canonical MAP mutation | Tier 3 local assistant | `reject` |
| shell/network task | Tier 3 local assistant | `reject` |
| AUTHORITY/POLICY finalization | Tier 1 core agent | `require_approval` |
| destructive action by Tier 1 | Tier 1 core agent | `require_approval` |

The test names should include the denied capability so failures are readable:
`test_helper_cannot_take_final_review`, `test_local_cannot_mutate_canonical_state`,
and so on.

## Required Allow Cases

| Case | Candidate | Expected |
|---|---|---|
| read-only review draft | Tier 2 helper | `allow` with owning core agent |
| acceptance-criteria draft | Tier 3 local assistant | `allow` only as draft/local lane |
| architecture spec inside existing scope | Tier 1 core agent | `allow` |
| mechanical validation run | Tier 1 core agent | `allow` |
| command-center destructive action | Tier 0 | `allow` |

Allow tests prevent the checker from becoming a blanket blocker that stops
useful bounded work.

## Approval Cases

These should return `require_approval`, not `reject`, because the assignment
may be valid after the right authority signs off:

- Tier 1 core agent performing a destructive action;
- Tier 1 core agent drafting an AUTHORITY/POLICY change for command-center;
- Tier 1 core agent crossing a network boundary for a new external-service
  integration;
- unresolved `SECURITY` or `STRUCTURAL` risk mitigation;
- SCOPE decision that expands unsupervised touch surface.

Each test should assert the `approval_authority` and `required_evidence`
fields, not just the high-level decision.

## Runner Tests

Runner integration tests should prove:

- rejected helper/local assignments do not appear in helper recommendations;
- `require_approval` assignments route to an approval/gate state;
- allowed tasks remain in `ready_tasks`;
- policy-check reasons are included in route state or attention output;
- unavailable policy metadata produces conservative gating, not silent allow.

## Agent-Loop Tests

Agent-loop tests should prove:

- a task that was `allow` at route time but becomes `require_approval` before
  claim is not claimed;
- rejected tasks are not claimed even if they are `READY`;
- blocked-dispatch events include rule IDs and required authority;
- no helper/local lane can bypass runner by direct claim.

## Fixture Matrix

Minimum fixture fields:

- `task_id`
- `task_type`
- `role`
- `description`
- `output_paths`
- `task_tier`
- `decision_class`
- `risk_class`
- `risk_severity`
- `destructive_action`
- `required_agent` or candidate lane

Fixtures should include both explicit metadata and text-derived fallback cases
so the checker can be tested before all task packets are fully enriched.

## Regression Invariants

- Helpers never approve, release, or make final decisions.
- Local assistants never run shell, network, or canonical writes.
- Destructive actions are gated before assignment.
- AUTHORITY/POLICY decisions require command-center before becoming binding.
- Unknown risk on a trust-boundary crossing is not treated as safe.
- Existing bounded review and draft lanes still work.
