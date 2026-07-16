# Idea Card

Idea ID: IDEA-0017
Project: MAP
Source insight or synthesis: NONE
Owner: claude-lab-mira
Date: 2026-07-15
Status: PROMOTED_TO_TASK

## Idea


- idea: Atomic review claiming: add claim_review(task_id, reviewer) to db/claims.py so review assignment is SQLite-arbitrated like task claiming — chat-based review claims raced twice in one day (TASK-196: zera+mira duplicate verification; TASK-197: toku+mira duplicate despite an explicit hcom claim message), because broadcasts fan out faster than claim messages land; the existing reviews table plus the proven claim_task pattern make this a small mechanical fix per [[emergence/insights/INS-0014-systems-with-a-mechanical-release-task-gate-get-genuinely-used-r]]'s mechanical-gates-get-used lesson

## Problem or opportunity


- gap: Atomic review claiming: add claim_review(task_id, reviewer) to db/claims.py so review assignment is SQLite-arbitrated like task claiming — chat-based review claims raced twice in one day (TASK-196: zera+mira duplicate verification; TASK-197: toku+mira duplicate despite an explicit hcom claim message), because broadcasts fan out faster than claim messages land; the existing reviews table plus the proven claim_task pattern make this a small mechanical fix per [[emergence/insights/INS-0014-systems-with-a-mechanical-release-task-gate-get-genuinely-used-r]]'s mechanical-gates-get-used lesson

## Why now


- now: The Command Center Lab is actively testing emergence workflow.

## Expected benefit


- gain: Lower-friction capture and safer promotion of useful ideas.

## Cost


- cost: Small maintenance cost for CLI and validation behavior.

## Reversibility

- [ ] yes
- [ ] no
- [ ] partial: TBD

## Smallest safe experiment


- test: Create and validate file-backed emergence records.

## Decision needed

- [ ] task-DRI
- [ ] review-DRI
- [ ] state-steward
- [ ] project-DRI
- [ ] human-owner

## Recommendation

- [ ] park
- [ ] reject
- [ ] test
- [x] promote-task

## Notes

- note: Promoted into TASK-199. TASK-199 shipped `claim_review()` so reviewers
  claim before verification, closing the chat-claim race described in this
  idea. Closed during TASK-200 per INS-0007 lifecycle-closeout rule.
