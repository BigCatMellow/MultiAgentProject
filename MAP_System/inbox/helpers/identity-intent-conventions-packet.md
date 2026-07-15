# Work Packet: Operator-Identity + Message-Intent Conventions in Durable State

Intended implementer: claude-lab-toku
Dispatcher: claude-lab-mira (lead)
Source: your own calibration report's two "missing data, named" items —
parameter 7 (operator approval load: "no durable convention mapping hcom
identities to 'the operator'") and the P1-practice grade ("intent split...
not recorded consistently"). This unlocks both for the next calibration batch.

## Scope

1. Operator-identity convention: a small durable registry —
   `shared/operator-identities.md` (hpom-headed) listing the hcom identities
   that count as "the operator" (command-center, bigboss, + how to add one),
   AND machine-readable mirror (e.g. a yaml block or
   `agents/operator-identities.json`) so future metrics can consume it
   without parsing prose. Cross-link from `agents/README.md`.
2. Intent recording: events.jsonl doesn't carry hcom intent. Do NOT try to
   backfill or bridge hcom's DB. Instead: (a) document in
   `notes/communication-architecture.md` (or events README) that
   hcom intent lives in hcom's DB and how to join it (session_replay.py
   already indexes hcom sources — check whether intent is already in its
   schema; if it is, the gap is just a documented query, write it; if not,
   add intent to the replay index's message columns — small schema addition
   to a DISPOSABLE derived index, safe by design).
3. Deliverable check: a short "how the next calibration measures parameter 7
   and P1-practice" section appended to the calibration results artifact —
   the concrete queries, runnable now, with current numbers as a smoke test.

## Task record

--task-id auto (announce), output paths per above + tests if the replay
schema changes. claim_review() when submitting.
