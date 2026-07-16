# Insight Record

Insight ID: INS-0020
Project: Riftbound
Related task: NONE
Detected by: claude-lab-fimo
Date: 2026-07-06
Status: RAW

## Short description

- obs: When a derived dataset looks ambiguous, one targeted check of the primary source can convert a flagged ambiguity into a confirmed rule — flagging is the fallback, not the first move

## Trigger

- src: Sivir - Battle Mistress's 'when you recycle a rune' trigger looked unbuildably narrow from the card export (2 enabler cards); one pdftotext grep of the rules PDF found core rule 163.2.b — Basic Runes pay Power by recycling themselves — turning the trigger into 'every Power cost' and unlocking the whole deck design

## The synthesis

- synth: When a derived dataset looks ambiguous, one targeted check of the primary source can convert a flagged ambiguity into a confirmed rule — flagging is the fallback, not the first move

## Why it might matter

- why: [[emergence/insights/INS-0018-when-a-rules-heavy-generative-task-hits-a-genuinely-ambiguous-so]] established that flagging genuine ambiguity beats guessing; this adds the prior step: several apparent ambiguities in this project were actually gaps in the derived export (missing tag column, truncated signature texts, unstated core rules) that the primary source resolves in seconds when it is locally available

## Evidence

- ev: Rule 163.2.b confirmed via pdftotext on Riftbound_Core_Rules_RUP3_Staging.pdf; sivir-gold-rush-synergy.md cites the rule number. Contrast: the Ivern deck's Cat/Dog tag gap could NOT be resolved from local sources (tags absent from both export and rules text) and stayed explicitly flagged per [[emergence/insights/INS-0018-when-a-rules-heavy-generative-task-hits-a-genuinely-ambiguous-so]]

## Risk

- risk: Acting without promotion could bypass HPOM governance.

## Scope

- scope: Only the files and artifacts named in this record.

## Recommended next action

- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- note:
