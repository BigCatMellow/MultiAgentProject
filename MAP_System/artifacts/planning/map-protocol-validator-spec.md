# MAP Protocol Validator Spec (TASK-152, Wave 4)

Status: draft-active
Owner: command-center
Built by: TASK-152
Companion: `map-semantic-validator-spec.md`, `map-validator-halt-state-spec.md`

## Purpose

Splits hcom/MATOCP **protocol compliance** validation from **semantic
output-correctness** validation (`map-semantic-validator-spec.md`). This is
the fix for the gap TASK-147's review flagged and TASK-152's own acceptance
criteria requires: MAP has no independent validator that checks whether an
hcom message actually follows the communication protocol, as distinct from
whether the work described in the message is correct.

## Scope

The protocol validator checks the **shape and process** of an hcom message,
never the substance of the work it describes:

- Does the message carry a required `--intent`?
- If the message is a MATOCP token form (`!ACK`, `!LGTM`, `!ERR`, `!REQ`,
  `!WARN`, `!NOTE` per `AGENTS.md`'s Communication section), is the token
  form well-formed (matches one of the defined shapes)?
- Does an operator-decision-shaped message (per
  `ORCHESTRATION_ENTRYPOINT_SYSTEM.md`'s Request format: Issue/Options/
  Recommendation/Needed) actually include those four parts?
- Does a broadcast-to-multiple-agents message get a scope-claiming follow-up
  from the first responder, per `AGENTS.md`'s Broadcast Coordinator
  Convention?

## Known Spec Discrepancy (found during this task, must be resolved before building)

`AGENTS.md`'s Communication section defines a 6-token MATOCP subset (`!ACK`,
`!LGTM`, `!ERR`, `!REQ`, `!WARN`, `!NOTE`). `Guidelines/llm-communication-rules.md`
defines a full v3.2 MATOCP spec with 17 tokens across the core matrix and two
extension sections (`!STATE`, `!FIX`, `!PATCH`, `!EXEC`, `!EOF`, `!ASK`,
`!REVERT`, `!LOCK`, `!UNLOCK`, `!HALT`, `!DEF`, plus the session lexicon).
These are not the same protocol — a validator built against one will reject
or silently ignore tokens defined only in the other. **Building this
validator against the wrong reference document produces false positives on
day one.**

This must be resolved as a scope decision before implementation, not
silently by picking one:

- **Option A**: `AGENTS.md`'s 6-token subset is the actual operative spec
  (it's what agents in this repo have been using in practice, based on hcom
  transcripts observed this session — `!ACK`, `!NOTE`, `!REQ` all appear;
  extension tokens like `!LOCK`/`!HALT` do not). Validate against it; treat
  `llm-communication-rules.md`'s fuller version as aspirational/future.
- **Option B**: Adopt the full v3.2 spec now, updating `AGENTS.md` to match,
  and validate against the fuller matrix.
- **Recommendation**: Option A. The 6-token subset is what's actually in
  live use (confirmed by grepping this session's own hcom traffic); adopting
  17 tokens the moment a validator ships would immediately generate
  violations for a protocol nobody has been following. If the fuller spec's
  extension tokens (`!LOCK`/`!UNLOCK` for file coordination, `!HALT` for
  operator interrupt) are wanted, adopt them as a deliberate, separate
  decision with an operator sign-off, not as a validator side effect.

## False-Positive Adjudication

Per `AGENTS.md`'s Review Standard and `SELF_REPAIR_SYSTEM.md`'s severity
model, every protocol-validator finding gets an adjudication field, not just
a binary pass/fail:

| Adjudication | Meaning | Who decides |
|---|---|---|
| `true_positive` | Message genuinely violates the operative protocol (Option A subset, or whatever scope decision is made above) | Validator flags; reviewing core agent confirms |
| `false_positive` | Message is fine; validator misfired (e.g. flagged a legitimate `!NOTE` escape-hatch use as non-conforming) | Core agent overrides, logs the override as calibration data per `map-semantic-validator-spec.md`'s feedback-loop pattern |
| `waived` | Message technically violates but the violation is accepted (e.g. operator direct message under one of `ORCHESTRATION_ENTRYPOINT_SYSTEM.md`'s Direct Message Policy exceptions) | Core agent or operator, cited exception |

Track violation type, sender, thread, task, and adjudication per the master
plan's Wave 4 item 2 (compliance telemetry) — this is what lets the protocol
validator improve over time instead of staying a fixed rule list.

## Non-Goals

- Does not check whether the work described is correct — that's the
  semantic validator's job.
- Does not block dispatch by itself in this version — see
  `map-validator-halt-state-spec.md` for when protocol violations become
  blocking vs. advisory-only (telemetry).
- Does not retroactively re-validate the 821+ existing `events.jsonl` lines
  or historical hcom transcripts; applies going forward only.

## Related Files

- `AGENTS.md` [[AGENTS]] (Communication section, Broadcast Coordinator Convention)
- `Guidelines/llm-communication-rules.md`
- `MAP_System/ORCHESTRATION_ENTRYPOINT_SYSTEM.md` [[ORCHESTRATION_ENTRYPOINT_SYSTEM]]
- `MAP_System/artifacts/planning/map-semantic-validator-spec.md` [[map-semantic-validator-spec]]
- `MAP_System/artifacts/planning/map-613-master-implementation-plan.md` [[map-613-master-implementation-plan]] (Wave 4)
