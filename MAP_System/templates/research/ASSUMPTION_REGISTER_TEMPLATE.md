# Assumption Register

Register ID: ASSUMPTIONS-0001
Related brief: BRIEF-0001
Owner: <agent-name>
Date: <YYYY-MM-DD>
Status: OPEN

Anything treated as true without a source belongs here, not silently in
code, task descriptions, or decisions.

## Assumptions

| # | Assumption | Why assumed instead of verified | Blast radius if wrong | Resolves by | Status |
|---|---|---|---|---|---|
| 1 | <what is assumed> | <time pressure / no available source / low stakes / etc> | <what breaks and how badly> | <who/what can verify: command-center, a specific source, a test> | OPEN / RESOLVED / ACCEPTED |
| 2 | | | | | |

## Gating rule

Assumptions that gate a `BLOCKER`/`REQUIRED` review finding, or that
underlie security- or network-facing work, must reach `RESOLVED` (verified)
or `ACCEPTED` (explicit command-center sign-off) before release. They may
not be carried indefinitely as silent `OPEN`.

## Notes

-
