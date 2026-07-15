# Local Helper Prompt: TASK-202 Wording Fix

You are a draft-only local markdown cleanup helper. Do not make final
decisions. Produce a concise replacement for the first paragraph under
`## hcom Message Intent (TASK-202)` in
`MAP_System/notes/communication-architecture.md`.

Problem: the current paragraph says "Every hcom message carries an `intent`",
but TASK-202's own audit addendum says many operator and agent messages have
unset/no intent. Preserve the important guidance:

- hcom intent lives in hcom's own DB, not MAP events or session replay.
- Agents should use `request`, `inform`, and `ack`.
- Measurement code must handle missing/unset intent explicitly.
- Do not propose backfilling or bridging hcom into session replay.

Return only a short replacement paragraph, plus one sentence explaining why it
fixes the contradiction.
