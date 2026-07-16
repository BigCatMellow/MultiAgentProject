# Source Evaluation

Evaluation ID: SOURCE-EVAL-0001
Related brief: BRIEF-0001
Related source map: SOURCE-MAP-0001
Owner: claude-lab-magi
Date: 2026-07-04
Status: OPEN

## Ratings

| # | Source (from Source Map) | Rating | Publish/retrieved date | Rationale |
|---|---|---|---|---|
| 1 | LangChain Docs: Interrupts | PRIMARY | retrieved 2026-07-04 | First-party official documentation for the exact API `runner.py` uses |
| 2 | LangChain Changelog (1.0 GA) | PRIMARY | retrieved 2026-07-04 | First-party official release announcement |
| 3 | LangGraph GitHub Releases | PRIMARY | retrieved 2026-07-04 | Canonical version/release history, first-party repo |
| 4 | GitHub Issue #6363 | SECONDARY | opened ~Oct 2025, retrieved 2026-07-04 | First-party repo issue tracker, but an individual bug report/discussion rather than settled official guidance; used only to support the general "unpinned deps can break" claim, not a specific version claim about MAP |
| 5 | LangChain Reference: BaseCheckpointSaver | PRIMARY | retrieved 2026-07-04 | Official API reference, canonical for required-method claims |
| 6 | LangChain Forum thread | COMMUNITY | retrieved 2026-07-04 | Practitioner discussion; used only as corroboration of #5, not as sole support for any claim |
| 7 | `graph/runner.py` (local) | PRIMARY | as committed, checked 2026-07-04 | Ground truth for MAP's actual code |
| 8 | `db/checkpointer.py` (local) | PRIMARY | as committed, checked 2026-07-04 | Ground truth for MAP's actual code |
| 9 | `requirements.txt` (local) | PRIMARY | as committed, checked 2026-07-04 | Ground truth for MAP's declared dependency constraints |
| 10 | installed package metadata (`pip show`) | PRIMARY | checked 2026-07-04 | Ground truth for the currently-running version |

## Flags

- [x] Any claim relies only on `COMMUNITY` or `UNVERIFIED` sources — none;
      source #6 (COMMUNITY) is only ever used to corroborate a PRIMARY source
      (#5), never as sole support.
- [ ] Any source disagrees with another source on a used claim — none found.

## Low-confidence claims (COMMUNITY/UNVERIFIED-only support)

- None. Every claim used downstream has at least one PRIMARY source.

## Contradictions

- None found between sources #1-#10.

## Notes

- No STALE rating was needed: all external sources were retrieved live on
  2026-07-04, matching the current date, and the installed-package check (#10)
  is a live command, not recalled knowledge.
