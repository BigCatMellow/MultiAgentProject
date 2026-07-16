# Claim Evidence Matrix

Matrix ID: CLAIM-MATRIX-0001
Related brief: BRIEF-0001
Owner: claude-lab-magi
Date: 2026-07-04
Status: OPEN

## Claims

| # | Claim | Source(s) | Locator | Source rating | Confidence | Notes |
|---|---|---|---|---|---|---|
| 1 | `interrupt()` requires a checkpointer to work correctly (resume state is lost without one) | Source 1 | docs.langchain.com/oss/python/langgraph/interrupts | PRIMARY | HIGH | |
| 2 | `runner.py` only enables `interrupt`/resume (`--approve`/`--reject`) when a `--thread-id` is supplied, at which point it constructs `MapSqliteSaver` and passes it to `build_graph(checkpointer=...)` | Source 7 | MAP_System/graph/runner.py:690-697 | PRIMARY | HIGH | Local code read directly, not recalled |
| 3 | `Command(goto=...)` / `Command(resume=...)` is the current recommended mechanism for interrupt-based routing and resuming | Source 1 | docs.langchain.com/oss/python/langgraph/interrupts | PRIMARY | HIGH | Matches `runner.py`'s own `Command(resume={...})` call at line 706 |
| 4 | LangGraph reached 1.0 GA with a stated commitment to no breaking changes before 2.0 | Source 2, Source 3 | changelog.langchain.com/announcements/langgraph-1-0-is-now-generally-available; github.com/langchain-ai/langgraph/releases | PRIMARY | HIGH | Two independent first-party sources agree |
| 5 | Installed MAP version (`langgraph==1.2.7`) is a post-1.0 release, inside the stated no-breaking-changes window | Source 10, Source 3 | `pip show langgraph` in MAP_System/.venv; GitHub releases | PRIMARY | HIGH | |
| 6 | `MAP_System/requirements.txt` pins neither `langgraph` nor `langchain-core` to any version or range | Source 9 | MAP_System/requirements.txt:3-4 | PRIMARY | HIGH | Local file read directly |
| 7 | A real breaking change previously shipped via an unpinned/loosely-pinned companion package (`langgraph-prebuilt==1.0.2`), independent of the core `langgraph` package's own stability guarantee | Source 4 | github.com/langchain-ai/langgraph/issues/6363 | SECONDARY | MEDIUM | Confirms the general risk class (unpinned deps + companion-package churn); MAP does not import `langgraph.prebuilt` so this specific incident does not directly hit MAP today (see Assumption Register) |
| 8 | `BaseCheckpointSaver` custom implementations are expected to implement `get_tuple`, `put`, `put_writes`, `list`, and (for thread cleanup) `delete_thread` | Source 5, Source 6 | reference.langchain.com/python/langgraph.checkpoint/base/BaseCheckpointSaver; forum.langchain.com thread | PRIMARY (corroborated by COMMUNITY) | HIGH | |
| 9 | `MapSqliteSaver` implements `get_tuple`, `put`, `put_writes`, and `list`, but does not implement `delete_thread` | Source 8 | MAP_System/db/checkpointer.py (methods list) | PRIMARY | HIGH | Local code read directly |
| 10 | MAP's runner/agent_loop code paths never call `delete_thread`, `ainvoke`/`astream`, or the async checkpointer methods | Source 7, Source 8 | grep of MAP_System/graph/runner.py and MAP_System/scripts/agent_loop.py | PRIMARY | HIGH | Absence-of-use confirmed by direct search, not inferred |
| 11 | LangGraph's `langgraph.prebuilt` module is being superseded by functionality moving into `langchain.agents`, and MAP does not import `langgraph.prebuilt` anywhere | Source 3 (deprecation note), Source 7/8 (grep, no import found) | GitHub releases notes; grep of MAP_System | PRIMARY | HIGH | So this specific deprecation has zero current impact on MAP |
| 12 | A newer opt-in typed output/streaming API (`version="v2"` on `invoke`/`stream`) exists but is not required — old-style output remains supported | Search summary of LangChain changelog (March 2026 entry) | changelog.langchain.com/oss/python/releases/changelog | SECONDARY | MEDIUM | Not independently re-verified against the primary changelog page directly (search-summarized); treated as MEDIUM, not HIGH, and flagged as an assumption to revisit if MAP later depends on stream/invoke output shape |

## Unsourced claims used downstream

- None. Claim 12's slightly weaker sourcing is carried into the Assumption
  Register (ASSUMPTIONS-0001) rather than presented as HIGH confidence.

## Notes

- Claims 2, 6, 9, 10 are local-code claims verified by direct file read/grep
  in this session, not recalled from training data — the standard the
  Research System asks for on anything checkable.
