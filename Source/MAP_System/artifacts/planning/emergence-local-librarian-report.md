# TASK-181 Local Librarian Report

- task_id: TASK-181
- owner: codex-lab-nivo
- purpose: test lower-tier/local librarian help for compacting historical emergence records after TASK-180 compacted new templates and the generated index.
- target_scope: active/non-closed emergence records first; closed/promoted audit-history records deferred.

## Local helper runs

- model: `gemma3:4b`
- scope: draft compact rewrites for 8 active records.
- output: `MAP_System/artifacts/planning/emergence-local-librarian-compaction.md`
- helper_note: `MAP_System/inbox/helpers/task-181-gemma3-4b-2026-07-14T124413Z.md`
- result: rejected for direct application.
- reason: output focused on two records, drifted into task advice, did not produce replacement markdown, and included terminal control artifacts.

- model: `qwen2.5-coder:3b`
- scope: draft full rewrites for `IDEA-0009` and `INS-0008`.
- output: `MAP_System/artifacts/planning/emergence-local-librarian-batch1.md`
- result: failed.
- reason: `ollama run` timed out after 180s; no helper note/output was produced.

- model: `llama3.2:1b`
- scope: draft full rewrite for `IDEA-0009` only.
- output: `MAP_System/artifacts/planning/emergence-local-librarian-batch2.md`
- helper_note: `MAP_System/inbox/helpers/task-181-llama3-2-1b-2026-07-14T124920Z.md`
- result: partially useful, not directly applied.
- accepted: high-level section grouping was usable as a cue.
- rejected: changed header syntax, dropped checkbox markers, kept long prose in places, and included terminal control artifacts.

## Applied core integration

- file: `MAP_System/emergence/ideas/IDEA-0009-rns-should-ignore-superseded-and-disposable-sessions.md`
- action: core-agent compact rewrite using the local helper's rough section grouping only.
- preserved: ID, project, source, owner, date, status, headings, checked decisions, recommendation, lifecycle meaning, and evidence references.
- changed: prose body sections converted to compact key/value bullets.

## Tooling findings

- finding: `local_runner.py` emitted `HELPER_INVOKED`, which is not a canonical MAP event type.
- action: changed future helper invocation events to canonical `PROGRESS`; updated the two TASK-181 helper events already written.
- verification: `python3 MAP_System/scripts/validate_events.py --fail-on-new` passed with `new_warnings=0`.

- finding: `MAP_System/artifacts/reviews/task180-review-mira.md` contained generic example wikilinks that `librarian.py validate` correctly treated as broken.
- action: changed those examples to plain wording without altering the review verdict.
- verification: `python3 MAP_System/scripts/librarian.py validate` passed with `finding_count=0`.

## Deferred

- Remaining active records are not rewritten in this task.
- Reason: local models were not reliable enough for broad canonical rewrites without heavy core correction.
- Recommended next step: use a deterministic MAP-side compacting command or smaller supervised batches, with local models limited to review/diff suggestions until prompt/runtime quality improves.
