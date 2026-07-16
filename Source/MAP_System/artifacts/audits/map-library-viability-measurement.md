# MAP Library Viability Measurement Plan (TASK-154, Wave 6)

Status: draft-active
Owner: command-center
Built by: TASK-154

## Purpose

The Library layer should exist only if it reduces context cost without hiding
needed detail or introducing stale summaries. This measurement plan defines
the minimum evidence before building or adopting a Library/tool layer.

## Non-Negotiable Design Shape

A viable Library layer must ship as the full design:

1. compact summaries;
2. links to full detail;
3. event-driven staleness invalidation.

A summary-only implementation is explicitly forbidden because the 6.13
materials identify stale/lossy summaries as worse than no Library layer.

## Metrics

### Compression Ratio

```text
compression_ratio = source_tokens / summary_tokens
```

Measure on representative MAP files:

- system specs such as `RESEARCH_SYSTEM.md` and `CONTEXT_SYSTEM.md`;
- long planning artifacts;
- review records;
- event digests;
- task graph/task records.

Report median, p90, and worst-case ratio. High compression is not useful if
the detail-needed rate rises.

### Detail-Needed Rate

```text
detail_needed_rate =
  count(tasks where agent opened full source after reading summary)
  / count(tasks where summary was used)
```

Track why detail was needed:

- summary omitted acceptance-critical detail;
- summary was stale;
- source conflict required exact wording;
- task required code/path/line references;
- reviewer needed full evidence.

A healthy Library should reduce default reads while preserving easy expansion
to full detail. A high detail-needed rate means summaries are too lossy or
poorly routed.

### File Churn

```text
file_churn_rate =
  changed_library_source_files / measured_time_window
```

Also track:

- churn by folder (`shared/`, `artifacts/planning/`, `tasks/`, `events/`);
- mean time from source change to summary invalidation;
- stale-summary reads before invalidation;
- summaries invalidated but not regenerated.

High churn raises the cost of summary maintenance and makes event-driven
invalidation more important.

### Staleness Invalidation

Required checks:

- every summary records source path and source content hash or mtime;
- every source write emits or is discoverable through an event/export signal;
- summary status can be `fresh`, `stale`, `missing`, or `unknown`;
- stale summaries are not used as authoritative context;
- readers can jump from summary to full source.

Measure:

```text
stale_read_rate =
  stale_summary_reads / all_summary_reads
```

Target: zero known stale reads for decision, review, repair, and policy tasks.

## Measurement Procedure

1. Select 20-30 representative MAP files across shared systems, planning,
   reviews, tasks, and events.
2. Produce draft summaries with full-source links and source hashes.
3. Run normal MAP tasks/reviews for one cycle using summaries as optional
   first-read context.
4. Log whether agents opened full sources and why.
5. Mutate a controlled subset of source files and verify summaries are marked
   stale before reuse.
6. Compare token cost, detail-needed rate, and missed-detail incidents against
   normal direct-file reading.

## Adoption Threshold

Do not adopt or build the Library layer unless measurement shows:

- meaningful context-token reduction on real MAP tasks;
- low missed-detail rate;
- zero known stale-summary reads for high-authority work;
- summary regeneration cost is lower than repeated direct reads;
- failure modes are covered by validators or repair records.

## Tool Evaluation Inputs

TASK-154's research summary evaluates tool candidates as patterns, not
adoption decisions:

- `iurykrieger/claude-bedrock` for Obsidian/wikilink librarian mechanics;
- `ccf/agentcairn` for local-first cross-agent memory and provenance;
- `Knowledge-graph-driver-RAG` hop-limit/token-budget pattern for bounded
  graph traversal;
- `WenyuChiou/agent-collab-skills` acceptance gate for outcome/review gating;
- `milisp/codexia` for worktree/control-plane lessons.

Any future adoption task must run this measurement plan first or justify why a
candidate bypasses it.
