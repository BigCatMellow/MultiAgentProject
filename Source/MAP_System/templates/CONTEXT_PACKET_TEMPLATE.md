# Context Packet

Packet ID: CONTEXT-0001
Anchor: <TASK_ID / DEC_ID / research question — one line>
Assembled by: <agent-name>
Date: <YYYY-MM-DD>

See `MAP_System/CONTEXT_SYSTEM.md` for the rules this packet follows.

## Required

<Files that must be read before acting. Name the file and why it is
required for this anchor.>

- `path` — <why required>

## Optional (trigger-gated)

<Files to read only if a specific condition below is met. Do not read
these by default.>

- `path` — read if: <trigger condition>

## Excluded

<Files deliberately not loaded for this packet, and why. This is not a
list of every file in the repo — only ones a reader might reasonably
expect to see included.>

- `path` — excluded because: <reason>

## Staleness check

- [ ] No file in Required is marked superseded
- [ ] `shared/current-state.md` does not conflict with anything in Required
- [ ] Any STATE_SNAPSHOT/handoff used here is treated as orientation, not
      authoritative, if older than this session

## Notes

-
