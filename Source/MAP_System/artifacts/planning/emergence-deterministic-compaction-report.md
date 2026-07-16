# TASK-183 Deterministic Emergence Compaction Report

Date: 2026-07-14
Owner: codex-lab-nivo
Task: TASK-183

## Summary

Implemented `map_emergence.py compact`, a deterministic command that converts existing emergence record body sections into the compact bullet style introduced by the current emergence templates. The command has a dry-run default, an explicit `--apply` write mode, named-target resolution by artifact ID/path, and `--all-active` scope for non-closed emergence artifacts.

## Command behavior

- `python3 MAP_System/scripts/map_emergence.py compact INS-0008 SYN-0001 --json`
  reports whether each target would change without writing files.
- `python3 MAP_System/scripts/map_emergence.py compact --all-active --apply`
  applies compact conversion to every active emergence record.
- Closed statuses are skipped by `--all-active`: `ADOPTED`, `APPROVED`, `ARCHIVED`, `DISMISSED`, `PARKED`, `PROMOTED`, `PROMOTED_TO_TASK`, `REJECTED`, `SUPERSEDED`, `WITHDRAWN`.
- Section headings, header fields, statuses, checkboxes, and selected decision state are preserved.
- Known prose sections are converted to short labels such as `obs`, `src`, `synth`, `why`, `ev`, `risk`, `idea`, `gap`, `now`, `gain`, `cost`, `test`, `combo`, `opens`, and `why-hidden`.
- Synthesis piece subsections keep their `### Piece ...` headings and receive stable `a`, `b`, `c` labels.
- Existing compact bullets and checklist bullets are recognized so repeated runs are idempotent.
- Resolvable MAP-local markdown references are wikilinked during compaction using the existing emergence reference resolver.

## Records changed

Active records compacted or verified by `--all-active`:

- `MAP_System/emergence/insights/INS-0008-ei-should-proactively-surface-operator-friction-affordances.md`
- `MAP_System/emergence/insights/INS-0009-e-i-should-proactively-scout-operator-workflow-friction-instead-.md`
- `MAP_System/emergence/insights/INS-0017-turn-by-turn-self-audited-card-game-simulation-naming-every-card.md`
- `MAP_System/emergence/insights/INS-0018-when-a-rules-heavy-generative-task-hits-a-genuinely-ambiguous-so.md`
- `MAP_System/emergence/insights/INS-0019-a-100-line-domain-validator-written-at-the-start-of-a-generative.md`
- `MAP_System/emergence/insights/INS-0020-when-a-derived-dataset-looks-ambiguous-one-targeted-check-of-the.md`
- `MAP_System/emergence/synthesis/SYN-0001-two-readers-one-truth.md`
- `MAP_System/emergence/ideas/IDEA-0009-rns-should-ignore-superseded-and-disposable-sessions.md`

`INS-0017` through `INS-0020` already had compact prose sections from earlier template changes; this task normalized their empty `Notes` placeholders from a bare `-` to `- note:`. `IDEA-0009` was included because its corroborating evidence section was active, MAP-side, and already within the emergence lane.

## Why not local-model direct rewrites

TASK-181 tested lower-tier/local librarian helpers and found them useful for discovery but not reliable enough for direct rewriting of durable emergence records. The helper outputs needed core review to avoid semantic drift. For TASK-183, the safer path was a deterministic MAP-side transform that labels and joins existing text mechanically without summarizing, inventing content, or changing lifecycle decisions.

## Verification

- `python3 MAP_System/tests/test_map_emergence.py`: passed after adding compact-command regression coverage.
- `python3 MAP_System/scripts/map_emergence.py compact --all-active --json`: all active targets report `changed: false` after apply.
- `python3 MAP_System/scripts/map_emergence.py validate`: `OK emergence artifacts valid (44 checked)`.
- `python3 MAP_System/scripts/map_emergence.py stale`: `No emergence stale/content findings.`
- `python3 MAP_System/scripts/librarian.py validate`: `finding_count: 0`.
- `python3 MAP_System/scripts/validate_events.py --fail-on-new`: `errors=0`, `new_warnings=0` with legacy warnings only.
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_mirrors.py`: passed.
- `bash MAP_System/scripts/run_tests.sh`: `SUMMARY pass=54 fail=0 total=54`.
