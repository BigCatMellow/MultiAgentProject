<!-- hpom: file: shared/approval-calibration.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-02 -->
<!-- hpom: verified_against: TASK-064 full MAP system report -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Approval Calibration

Purpose: reduce needless hand-holding without weakening MAP safety.

## Ask Command-Center

Use hcom `--intent request` when the answer changes authority, risk, or scope:

- destructive file or Git operations;
- external publication or push;
- canonical repo choice;
- privacy, credentials, or scope risks;
- story canon/product intent decisions;
- tool approval prompts;
- unresolved ownership conflict.

## Continue Autonomously

Use hcom `--intent inform` and keep working when:

- the operator already set direction;
- the work is inside the claimed task;
- changes are non-destructive and local to owned output paths;
- validation/review can catch quality issues;
- the choice is an implementation detail rather than user intent.

## Use Peer Review

Ask the other core agent to review when:

- you implemented a substantive deliverable;
- the work changes validators, gates, scripts, or policy;
- the result could affect future agent behavior.

## Stop For Ownership

Do not edit when:

- another active task owns the same output path;
- two agents are about to create the same task ID;
- a repo-global operation is already locked by another owner.

