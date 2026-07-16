# Research Summary

Summary ID: SUMMARY-0001
Related brief: BRIEF-0001
Related claim matrix: CLAIM-MATRIX-0001
Related assumption register: ASSUMPTIONS-0001
Owner: claude-lab-magi
Date: 2026-07-04
Status: FINAL

## Question

Is MAP's LangGraph usage (`graph/runner.py`, installed `langgraph==1.2.7`)
aligned with current upstream practice for the patterns it uses, or has
guidance moved somewhere MAP hasn't followed?

## Answer

Mostly yes, and better than a typical from-scratch implementation. MAP's use
of `StateGraph`, `Command`, and `interrupt()` in `graph/runner.py` follows
the current officially-documented pattern exactly: `interrupt()` is only
reachable through a code path that requires `--thread-id`, at which point a
checkpointer (`MapSqliteSaver`) is constructed and passed to
`build_graph(checkpointer=...)` — this matches the official rule that
`interrupt()` requires a checkpointer to resume correctly. Gate resumption
uses `Command(resume=...)`, the current recommended mechanism. The installed
version (1.2.7) is a stable post-1.0-GA release, inside LangGraph's own
stated no-breaking-changes-until-2.0 window, and MAP does not use the one
module (`langgraph.prebuilt`) that is being deprecated/superseded.

Two real, concrete gaps were found, both minor:

1. **`requirements.txt` pins nothing.** `langgraph` and `langchain-core` are
   listed with no version constraint at all. This doesn't match current
   practice for a library that ships frequent releases, and it's the exact
   risk class that caused a real incident upstream (an unpinned/loosely
   constrained companion package shipped a breaking change independent of
   the core package's own stability guarantee). MAP isn't hit by that
   specific incident today, but an unpinned install is gambling on that not
   recurring instead of relying on LangGraph's actual stated contract
   (stable until 2.0).

2. **`MapSqliteSaver` (the custom checkpointer) doesn't implement
   `delete_thread()`,** one of the methods current official reference docs
   list for a complete custom checkpointer. MAP never calls it today, so
   this has zero live impact, but it's a latent gap if MAP later adopts any
   thread-lifecycle tooling.

Neither gap is a currently-active bug. Both are "tighten before it bites,"
not "fix because something is broken."

## Confidence

- [x] HIGH — answer rests on PRIMARY sources (official LangChain docs,
      GitHub releases, and direct reads of MAP's own code), with one MEDIUM-
      confidence sub-claim (the v2 streaming API description) isolated in the
      Assumption Register rather than blended into the overall confidence.

## Confidence decays after

Time-sensitive. Re-verify if `MAP_System/requirements.txt` or the installed
`langgraph` version changes, or after the next MAP renewal cycle, whichever
comes first — LangGraph is actively developed and the 1.0 stability window
is a promise about 1.x->2.0, not a promise nothing changes within 1.x.

## Open questions

- Assumption #2 (does an un-overridden `delete_thread()` matter) — open,
  low priority, only worth resolving if MAP adopts thread-lifecycle tooling.
- Assumption #1 (exact shape of the `version="v2"` invoke/stream API) — open,
  zero priority unless a future task wants that feature.

## Downstream effect

- [ ] Feeds a decision — no new DEC-NNN needed; this is a tuning
      recommendation, not a policy or architecture change.
- [x] Feeds a task — handed to **TASK-144** (codex-lab-veto, MAP renewal /
      structural assessment coordinator) as an input packet. Recommended
      concrete action for that task's cleanup batch: pin
      `MAP_System/requirements.txt` to `langgraph>=1.0,<2.0` and
      `langchain-core>=1.0,<2.0` (or the narrowest range that still matches
      the installed `1.2.7`), matching LangGraph's own stated stability
      contract instead of floating unpinned. Optionally add a one-line
      `delete_thread()` no-op override to `MapSqliteSaver` with a comment
      noting it's unused today, if TASK-144's cleanup batch wants to close
      that gap preemptively rather than defer it.
- [ ] Informational only — no immediate downstream action

## Notes

- This is the first artifact set to actually exercise
  `MAP_System/templates/research/` end to end, per DEC-027's stated trigger
  condition (a genuine external/current-practice question). The process
  worked as designed: it forced explicit sourcing instead of relying on
  training-data recall for a fast-moving library, and it surfaced two real,
  bounded, non-urgent findings rather than either "nothing to report" or
  invented busywork.
