# Assumption Register

Register ID: ASSUMPTIONS-0001
Related brief: BRIEF-0001
Owner: claude-lab-magi
Date: 2026-07-04
Status: OPEN

## Assumptions

| # | Assumption | Why assumed instead of verified | Blast radius if wrong | Resolves by | Status |
|---|---|---|---|---|---|
| 1 | The March 2026 "type-safe streaming/invoke `version=\"v2\"`" feature described in a search-engine summary of the LangChain changelog is accurately described (not a search-tool paraphrase error) | Retrieved via WebSearch summary, not a direct WebFetch of the changelog page itself; time-boxed research effort did not re-fetch the primary page directly | Low: MAP does not currently use this feature at all, so being wrong about its exact shape has no present effect. Only matters if a future task adopts `version="v2"` | Direct `WebFetch` of `https://docs.langchain.com/oss/python/releases/changelog` before any task actually adopts `version="v2"` | ACCEPTED (low stakes, not blocking this research's conclusion) |
| 2 | `MapSqliteSaver`'s missing `delete_thread()` override will not silently break anything, because nothing in MAP's current code calls it and the base class provides some default/no-op behavior rather than requiring every subclass to override it for basic `invoke`/interrupt-resume use | Confirmed by grep that MAP never calls thread deletion (claim 10, HIGH confidence), but did not read `BaseCheckpointSaver`'s exact source to confirm what happens if something upstream (e.g. a future LangGraph Studio/CLI integration) calls `delete_thread` on `MapSqliteSaver` | Medium: if MAP ever adopts a LangGraph tool that manages thread lifecycle (cleanup jobs, Studio integration), an un-overridden `delete_thread` could raise `NotImplementedError` or silently no-op depending on the base class's default, leaving orphaned checkpoint rows in `map.db` | A follow-up task, only if/when MAP adopts thread-lifecycle tooling: read `BaseCheckpointSaver.delete_thread`'s base implementation and add an explicit override if needed | OPEN |
| 3 | The `langgraph-prebuilt` breaking-change incident (claim 7) does not affect MAP today | Grep-confirmed `langgraph.prebuilt` is not imported anywhere in MAP_System (claim 11, HIGH), so the specific incident's mechanism doesn't apply now — but `pip`'s dependency resolver could still install a version of `langgraph-prebuilt` as a transitive dependency of `langgraph` itself, even if MAP's own code never imports it | Low-medium: a transitive install of an incompatible `langgraph-prebuilt` version alongside an unpinned `langgraph` could still cause an environment-level `pip install` failure or runtime import error in the venv, even without MAP code touching `prebuilt` directly | Pin `langgraph` (and ideally `langchain-core`) to a version range in `requirements.txt`, e.g. `langgraph>=1.0,<2.0`, so LangGraph's own stated no-breaking-changes-before-2.0 guarantee (claim 4) is the actual contract MAP relies on, not "whatever happens to resolve today" | OPEN — recommended fix, see Research Summary |

## Gating rule

None of these assumptions gate a BLOCKER/REQUIRED review finding or
security/network-facing work, so none require RESOLVED status before this
research packet is handed off. #3 is the one worth acting on soon (see
Research Summary downstream effect).

## Notes

- Kept the register short and specific rather than padding it — the honest
  state here is "mostly verified, two low-stakes gaps," which is itself a
  useful signal that MAP's actual LangGraph usage was already careful.
