<!-- hpom: file: shared/liveness-state.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: TASK-158 liveness_reaper.py -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Liveness State

Generated 2026-07-14T06:00:48Z by `scripts/liveness_reaper.py`. Read-only
snapshot -- mission-control and other consumers should treat this as
derived state, not a second source of truth for agent status.

| Agent | State | Active Task | Lane | Evidence |
|---|---|---|---|---|
| antigravity | suspect | - | core | status:available;no_hcom_data |
| bigboss | suspect | - | core | status:available;no_hcom_data |
| claude | suspect | - | core | status:available;no_hcom_data |
| claude-lab-magi | suspect | - | core | status:available;no_hcom_data |
| claude-lab-valo | suspect | - | core | status:available;no_hcom_data |
| claude-lab-vino | suspect | - | core | status:available;no_hcom_data |
| claude-lab-zaro | standby | - | core | status:standby |
| claude-lab-zera | suspect | - | core | status:available;no_hcom_data |
| codex | suspect | - | core | status:available;no_hcom_data |
| codex-lab-dino | suspect | - | core | status:available;no_hcom_data |
| codex-lab-lema | suspect | - | core | status:available;no_hcom_data |
| codex-lab-limo | standby | - | core | status:standby |
| codex-lab-mozu | alive | - | core | hcom:active |
| codex-lab-muva | suspect | - | core | status:available;no_hcom_data |
| codex-lab-neko | suspect | - | core | status:available;no_hcom_data |
| codex-lab-veto | suspect | - | core | status:available;no_hcom_data |
| gemini | standby | - | core | status:standby |
