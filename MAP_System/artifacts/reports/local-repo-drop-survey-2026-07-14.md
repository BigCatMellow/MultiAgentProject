# Report: Local Repo Drop Survey (2026-07-14)

Related: `BRIEF-0002`/`SUMMARY-0002` (TASK-154), `MAP-Repo-Review-List.md`
Owner: claude-lab-zera
Status: exploratory triage, not a formal 6-document Research System pass —
scope and stakes here are "survey what's useful," not "decide to adopt."
Note: filed under `artifacts/reports/`, not `artifacts/research/`, since it
doesn't fit the Research System's required artifact-prefix set (BRIEF/
SOURCE-MAP/SOURCE-EVAL/CLAIM-MATRIX/ASSUMPTIONS/SUMMARY) — confirmed via
`validate_research_artifacts.py` rejecting a `NOTE-` prefix in that
directory.

## What Happened

The operator downloaded real source (not just READMEs) for most of the
candidates named in `Guidelines/6.13/MAP-Repo-Review-List.md` into
`/home/home/Projects/MultiAgentProject/repo/`. This upgrades TASK-154's
research from secondary-source (web pages) to primary-source (actual code)
for several candidates, and adds candidates the original TASK-154 brief
didn't cover.

## Confidence Upgrade On Existing Candidates

`SUMMARY-0002` rated its `claude-bedrock`/`agentcairn` findings MEDIUM
confidence specifically because "confidence is medium because four
candidate repository pages were checked directly... but claims still
require local MAP measurement." Real source is now available locally,
which resolves the "was this a web page or the real thing" caveat but does
NOT resolve the still-open one: none of this has been measured against
real MAP content yet (Gap-Register's #1 priority, unchanged).

- **`claude-bedrock`** (Claude Code plugin, not a library): confirms
  `SUMMARY-0002`'s read — 8 skills, 7 entity types, single write point
  (`/bedrock:preserve`), read-only healthcheck, dedup/compress step,
  bidirectional wikilinks. This is a **product**, not something MAP could
  import; the value is architectural precedent, same conclusion as before.
- **`agentcairn`** (Python package + plugin): confirms and *strengthens*
  the earlier read. Notable specifics not visible from a web page: the
  index (DuckDB) is explicitly disposable/rebuildable while the vault
  (Markdown) is the source of truth — the same shape as MAP's own
  SQLite-canonical / file-mirror-derived split, independently converged on.
  Also has **redaction before every write** (regex + entropy + URL-credential
  scrubbing) — MAP has no equivalent anywhere in its emergence/event-capture
  path, worth flagging as a security gap for any future MAP knowledge
  pipeline that ingests external content. Ships a reproducible benchmark
  harness with explicit caveats rather than one cherry-picked number —
  matches MAP's own "measure, don't assume" ethos closely enough to be
  worth reading the benchmark methodology directly if the Library layer is
  ever built.

## New Candidates Not In The Original TASK-154 Brief

- **`callimachus`** (Tauri/Rust/React desktop app, not a library): indexes
  agent conversation history across 11 coding tools into local SQLite with
  hybrid search, distills decisions/gotchas/TODOs, links threads to git
  commits by file-overlap, and has an explicit **"Review conflicts" pass
  that flags contradicting decisions**. This last piece is a striking
  precedent for MAP's own unbuilt trace-reconstruction/causal-chain goal
  (gap-plan increment 3, TASK-170) — it's essentially a productized answer
  to "one view explains why a decision was made," built for a different
  problem (developer session history) but the same underlying need. Worth
  a closer read of its thread-to-commit linking heuristic (file-overlap +
  time-window, on-device, no LLM) if MAP ever wants automatic trace
  reconstruction instead of manual `trace_id` tagging.
- **`graphify`**: tree-sitter AST-based code-to-knowledge-graph tool,
  deterministic (no LLM) for code, tags every edge `EXTRACTED` vs
  `INFERRED`. The EXTRACTED/INFERRED distinction is a clean, adoptable
  idea for MAP's own emergence system (already distinguishes "outward"
  vs "inward" but doesn't tag individual claims by provenance the way this
  does).
- **`headroom`, `caveman`, `codeburn`**: token-compression / cost-tracking
  tools already named in `MAP-Repo-Review-List.md`'s "Token Compression"
  section — not yet reviewed at code level this pass; lower priority since
  MAP's Library-layer viability measurement (compression ratio on real MAP
  docs) is the actual blocking prerequisite, not which external tool
  performs compression. (Since this note was drafted, `codex-lab-mozu`'s
  TASK-171 audit covered these directly — see
  `artifacts/audits/repo-reference-map-runtime-audit.md`.)
- **`MemOS`, `Memori`, `mem0`, `EverOS`**: general agent-memory frameworks,
  not reviewed at code level this pass — same reasoning as above, and
  `SUMMARY-0002` already concluded `agentcairn`/`claude-bedrock` are the
  closer architectural fits for MAP's specific wikilink/Markdown plan.
  (Also covered by TASK-171.)
- **`MetaGPT`, `haystack`**: orchestration/retrieval-pipeline frameworks,
  not reviewed at code level this pass — `MAP-Repo-Review-List.md` already
  flagged `MetaGPT` as "a different layer than MAP" and `haystack` as
  "read for structure, not necessarily to adopt"; nothing in this drop
  changes that framing. (Also covered by TASK-171.)
- **`agents-observe`, `impeccable`, `awesome-claude-code`**: observability
  dashboard, UI design language, and curated list respectively — outside
  the Library-layer question entirely; noted for completeness, not
  reviewed further here. (Also covered by TASK-171.)

## What This Does NOT Change

- **No adoption decision.** Consistent with TASK-154's own rule ("Task
  makes no adoption decision without a Research Summary and measurement
  plan"), this note does not recommend integrating any of these.
- **The blocking prerequisite is unchanged**: `map-library-viability-measurement.md`
  (compression ratio, detail-needed rate, file churn on *real* MAP docs)
  still has to run before any Library-layer task, regardless of which
  external tool inspires the design.
- **These are large, real dependencies.** Several ship native binaries,
  Rust/Tauri apps, or non-trivial Python packages — installing any of them
  for real use would need the same operator approval this session already
  established as the norm for external package installs (see the pending
  `textual` request).

## Recommended Next Step (Not Started Here)

If the operator wants deeper investment: pick ONE candidate concept (most
likely `agentcairn`'s vault/index split, or `callimachus`'s decision-conflict
detection) and scope a bounded follow-on Research System task with a real
Claim Evidence Matrix, since this note deliberately skipped that ceremony
for speed. Otherwise, this survey stands as-is until the Library-layer
measurement work actually starts. See also `codex-lab-mozu`'s TASK-171
runtime-cluster audit for the complementary lane (compression, memory
frameworks, orchestration, observability, cost/yield accounting).
