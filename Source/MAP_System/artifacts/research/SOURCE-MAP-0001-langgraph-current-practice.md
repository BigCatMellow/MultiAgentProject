# Source Map

Source Map ID: SOURCE-MAP-0001
Related brief: BRIEF-0001
Owner: claude-lab-magi
Date: 2026-07-04
Status: OPEN

## Candidate sources

| # | Source | Type | Locator | Why relevant | Status |
|---|---|---|---|---|---|
| 1 | LangChain Docs: Interrupts | doc | https://docs.langchain.com/oss/python/langgraph/interrupts | Official current guidance on `interrupt()`, checkpointer requirement, `interrupt_before`/`interrupt_after` | used |
| 2 | LangChain Changelog | doc | https://changelog.langchain.com/announcements/langgraph-1-0-is-now-generally-available | Confirms LangGraph 1.0 GA status and stability commitment (no breaking changes until 2.0) | used |
| 3 | LangGraph GitHub Releases | repo | https://github.com/langchain-ai/langgraph/releases | Primary source for version history relative to installed `1.2.7` | used |
| 4 | GitHub Issue #6363: breaking change in langgraph-prebuilt 1.0.2 | forum/repo | https://github.com/langchain-ai/langgraph/issues/6363 | Documents a real breaking-change incident from an unpinned dependency, relevant to MAP's unpinned `requirements.txt` | used |
| 5 | LangChain Reference: BaseCheckpointSaver | doc | https://reference.langchain.com/python/langgraph.checkpoint/base/BaseCheckpointSaver | Authoritative list of methods a custom checkpointer must implement, to check `MapSqliteSaver` against | used |
| 6 | LangChain Forum: custom BaseCheckpointSaver implementation | community | https://forum.langchain.com/t/how-to-implement-custom-basecheckpointsaver/1606 | Practitioner-level confirmation of the same required-method list from #5 (independent corroboration) | used |
| 7 | `MAP_System/graph/runner.py` (local) | repo | MAP_System/graph/runner.py | The actual usage under review | used |
| 8 | `MAP_System/db/checkpointer.py` (local) | repo | MAP_System/db/checkpointer.py | The actual custom checkpointer under review | used |
| 9 | `MAP_System/requirements.txt` (local) | repo | MAP_System/requirements.txt | Confirms `langgraph` and `langchain-core` are unpinned | used |
| 10 | installed package metadata | api-response | `pip show langgraph` in `MAP_System/.venv` | Ground truth for the actually-installed version (1.2.7) vs. whatever `requirements.txt` would resolve to on a fresh install | used |

## Coverage check

- [x] At least one PRIMARY-candidate source identified (official docs #1, #2,
      GitHub releases #3, and authoritative reference #5)
- [x] Sources span more than one independent origin (official LangChain docs,
      GitHub repo/issues, independent forum corroboration, and local
      ground-truth files/installed package are all different origins)
- [x] Any known authoritative source (official docs, spec, source code) is
      included — official docs (#1, #5), GitHub releases (#3), and MAP's own
      source (#7-9) are all covered

## Notes

- Did not include general blog/tutorial posts (Medium/dev.to articles returned
  by the search) as primary evidence — they corroborate the official-docs
  claims about interrupt/checkpointer behavior but are not cited as
  standalone sources in the Claim Evidence Matrix, per the PRIMARY-first
  standard in `RESEARCH_SYSTEM.md`.
