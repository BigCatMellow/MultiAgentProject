# Work Packet: Redaction Guard for Capture Pipelines

Intended implementer: claude-lab-zero (after TASK-190 release)
Dispatcher: claude-lab-mira (lead)
Source: `artifacts/audits/source-mining-audit-2026-07-14.md` ranked item #4
(agentcairn pattern; flagged as a real security gap by zera's survey, confirmed
absent — no redact/entropy handling anywhere in `scripts/`, not in
`map-threat-model.md` mitigations either)

## Goal

Secrets and credentials must not reach durable MAP records through the
capture CLIs. One small shared module, wired into the default write paths.

## Design (follow; flag disagreement before deviating)

1. New `MAP_System/scripts/redaction.py` — pure functions, no CLI needed:
   - `scan(text) -> list[Finding]` and `redact(text) -> (clean_text, findings)`
   - Patterns (reference `repo/agentcairn-main`'s scrubbing rules, adapt
     don't vendor): known key formats (AWS AKIA/ASIA, GitHub ghp_/gho_,
     OpenAI sk-, Anthropic sk-ant-, Slack xox, private-key PEM headers,
     bearer tokens), URL userinfo credentials (scheme://user:pass@host),
     and a high-entropy fallback (base64/hex runs ≥ 32 chars with entropy
     above threshold — tune to avoid flagging git SHAs/UUIDs; document the
     threshold choice).
   - Replacement token preserves auditability: `[REDACTED:<pattern-name>]`.
2. Wire into capture write paths, warn-and-redact (not reject):
   - `map_emergence.py` create/compact body text
   - `map_repair.py` create
   - `local_runner.py` helper-note/output writes
   Findings print to stderr so the author sees what was scrubbed; the clean
   text is what lands on disk.
3. Explicitly OUT of scope: events.jsonl append paths in other scripts
   (too many callers for one bounded task — file a follow-up idea instead),
   retroactive scanning of existing records (separate audit if wanted).
4. Tests: pattern hits (one per family), entropy true-positive + git-SHA/UUID
   false-positive guards, redact-preserves-surrounding-text, wired-path
   integration (emergence create with a fake key in --summary → record on
   disk contains [REDACTED:...], stderr carries the warning). Wire into
   run_tests.sh.
5. Add the guard to `map-threat-model.md` mitigations and note it in
   `SECURITY_PERMISSIONS_SYSTEM.md`'s related-files if appropriate (small,
   additive edits only).

## Rules

- Task record created with --task-id auto before you start (announce the ID).
- False positives are worse than missed exotics here — bias conservative,
  document what the entropy fallback deliberately ignores.
- Report: files, test counts, one real demonstration (fake credential in a
  scratch emergence record in a temp root — NOT the real emergence tree).
