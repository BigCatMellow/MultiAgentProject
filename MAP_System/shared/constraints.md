<!-- hpom: file: shared/constraints.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Constraints

- Work inside this repository unless the user explicitly approves external changes.
- Do not rely on the existing `.git`, `.codex`, or `.agents` directories for writable state; they are currently read-only or non-standard in this workspace.
- Avoid destructive commands and broad rewrites.
- Keep generated scaffolding simple enough for both Codex and Claude Code to inspect manually.
- Push back on designs that increase fragility, hide ownership, erase history, or add process without improving agent behavior.
