# Halt-Authority Window Runbook

Use the bounded halt-authority window when the operator wants MAP validators
to stop dispatch on real validator violations for a short measurement period.
The shipped default is disabled.

## Enable

Edit `MAP_System/workflow/runtime_policy.yaml`:

```yaml
runtime_policy:
  halt_authority_window:
    enabled_until: "2026-07-22T00:00:00Z"
    granted_by: bigboss
    scope: [layer1, protocol]
```

That one YAML change is the operator switch. Use a future ISO timestamp and
include only the validator scopes being measured. `scope: [layer1]` enables
only Layer 1 halt authority; `scope: [protocol]` enables only protocol halt
authority; `scope: [layer1, protocol]` enables both.

## Expire Or Disable

The window passively expires when `enabled_until` is in the past. To disable it
immediately, set:

```yaml
runtime_policy:
  halt_authority_window:
    enabled_until: null
    granted_by: null
    scope: []
```

No daemon or cleanup command is required.

## Behavior

When the window is inactive, validators keep their existing telemetry-only
default: violations report normally but do not write `shared/halt-state.json`.

When the window is active for the validator scope, a validator violation writes
a `repair_only` halt through `halt_state.py` with `clear_requires: operator`.
Each halt or would-halt decision appends a `PROGRESS` event whose JSON summary
has `kind: validator_halt_authority` and `adjudication: pending`, so later
review can classify true positives, false positives, or waivers.
