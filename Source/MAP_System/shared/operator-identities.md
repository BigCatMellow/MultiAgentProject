<!-- hpom: file: shared/operator-identities.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: TASK-202 -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Operator Identities

Durable registry of which hcom identities count as "the operator" (a human,
not an agent), for use by any measurement or metric that needs to attribute
messages, approvals, or directives to the operator specifically —
`agents/README.md`'s human/relay identity note was the only place this fact
lived before this file, and it was prose-only, not something a script could
consume. See `map-real-parameter-calibration-results-2026-07-14.md`'s
"operator approval load" section for the first consumer.

Machine-readable mirror: `agents/operator-identities.json`.

## Registry

| hcom identity | Channel | Evidence |
|---|---|---|
| `bigboss` | Direct terminal — the operator typing straight into an hcom-connected session | `agents/README.md`: "Human / relay identities: `bigboss` is the operator." (F6 semantics, TASK-082) |
| `command-center` | CommandCenterUI web app relay — the operator's messages typed into the CommandCenterUI chat, sent under this fixed identity | `CommandCenterUI/app/server.py`: `OPERATOR_NAME = os.environ.get("COMMAND_CENTER_UI_OPERATOR", "command-center")` — every message the UI sends to hcom uses this identity |

Both identities represent the same human operator through different
channels; a message from either should be treated as an operator message,
not an agent message, when computing operator-attention or approval-load
metrics.

## How To Add An Identity

An hcom identity belongs in this registry only if it represents the human
operator directly — not an agent, not a tool, not a relay an agent controls
on the operator's behalf (e.g. `antigravity`'s `operator_relay_only` reason
in `agents/status.json` means agents ask the operator to relay to it, which
is the opposite direction and does not belong here).

To add one:

1. Confirm the identity is operator-controlled with concrete evidence (a
   code path, a config default, or a durable statement from the operator
   themselves) — not inference from message volume or tone.
2. Add a row to the table above with the channel and evidence.
3. Add the matching entry to `agents/operator-identities.json`.
4. Update `last_verified` in this file's header.

## Known Non-Operator Identities (for contrast)

- `claude`, `codex`: capability identities (DEC-008), not sessions or people.
- `antigravity`: reachable only via operator relay (`operator_relay_only`),
  i.e. an agent the operator can be asked to forward to — not the operator.
- `map-task`: a tool artifact (`scripts/map_task.py ensure_agent()`), not an
  agent or a person.
- `[hcom-events]`: hcom's own system notification sender, not a person.

## Related Files

- `agents/README.md` [[agents/README]] — the original prose note this file formalizes
- `map-real-parameter-calibration-results-2026-07-14.md` [[map-real-parameter-calibration-results-2026-07-14]] — first consumer (parameter 7)
