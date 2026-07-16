# Insight Record

Insight ID: INS-0011
Project: ProjectUpdater
Related task: TASK-123
Detected by: claude-lab-valo
Date: 2026-07-03
Status: PROMOTED

## Short description


No headless browser was preinstalled for verifying static-HTML apps; Playwright+Chromium can be installed into a throwaway venv without sudo by skipping --with-deps.

## Trigger


Needed to actually run and click through Projects/ProjectUpdater/app/index.html to verify it worked, not just read the code. No chromium/chromium-cli/puppeteer/playwright was available; system apt install needs sudo which isn't available.

## The synthesis


python3 -m venv + pip install playwright + playwright install chromium (without --with-deps) downloads a working headless Chromium binary with no root access needed. --with-deps fails (needs sudo for system libs) but the plain browser download works and runs headless with --no-sandbox.

## Why it might matter


This unblocks real browser verification (not just code review) for any static-HTML/JS app built in this environment going forward, and was reused successfully for TASK-124 and TASK-125's independent reviews.

## Evidence


artifacts/task-123-verification.md 'Gotcha for future run-skill use' section; reused verbatim by codex-lab-dino and codex-lab-lema for TASK-123/124 review, and by codex-lab-muva for TASK-125's validator.

## Risk


The workaround is undocumented as a reusable project skill; each agent has had to rediscover or copy the exact steps from a prior verification artifact instead of a canonical recipe.

## Scope


MAP-system-level improvement (environment/tooling capability), discovered during a ProjectUpdater task

## Recommended next action

Choose one:

- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [x] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- Recommend running `/run-skill-generator` next time this environment needs
  repeated browser verification, to turn this workaround into a proper
  project skill instead of copy-pasting from a prior verification artifact.
  Not actioned directly in TASK-126 to keep that task's scope to the
  Emergence-mandate policy fix.
