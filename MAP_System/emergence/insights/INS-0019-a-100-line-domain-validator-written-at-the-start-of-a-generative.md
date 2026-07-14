# Insight Record

Insight ID: INS-0019
Project: Riftbound
Related task: NONE
Detected by: claude-lab-fimo
Date: 2026-07-05
Status: RAW

## Short description

- obs: A 100-line domain validator written at the start of a generative batch immediately caught legality bugs in already-released artifacts that two agents' manual cross-review had approved

## Trigger

- src: Before building 3 more Riftbound decks, wrote scripts/validate_decks.py; its first run found the released Rumble deck at 5 signature cards (limit 3, incl. Jhin's Curtain Call) and the Kha'Zix deck running Sivir's signature On the Hunt — both previously hand-verified by two agents

## The synthesis

- synth: A 100-line domain validator written at the start of a generative batch immediately caught legality bugs in already-released artifacts that two agents' manual cross-review had approved

## Why it might matter

- why: Manual review verified what it knew to check (counts, name/ID pairs) but silently skipped a rule neither author had operationalized (signature champion-tag matching); encoding rules as a script forces enumerating them, and the enumeration itself surfaced the gap

## Evidence

- ev: validate_decks.py first run: FAIL rumble-mech-tribal (5 sigs), WARN khazix (Sivir sig); it also caught 3 illegal signatures in my own new Vi deck. All 20 decks now pass. Signature ownership inferred from card-ID adjacency (each signature is printed directly after its Legend)

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
