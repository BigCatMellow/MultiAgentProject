# Insight Record

Insight ID: INS-0017
Project: Riftbound
Related task: NONE
Detected by: claude-lab-lori
Date: 2026-07-04
Status: RAW

## Short description

- obs: Turn-by-turn self-audited card game simulation (naming every card, citing rule numbers inline) surfaces real rules ambiguities and card-level bugs that reading the rulebook alone misses

## Trigger

- src: Building 5 decks then running 8 simulated games across them for the Riftbound TCG lab project

## The synthesis

- synth: Turn-by-turn self-audited card game simulation (naming every card, citing rule numbers inline) surfaces real rules ambiguities and card-level bugs that reading the rulebook alone misses

## Why it might matter

- why: Static rules-reading builds a plausible mental model, but only sequencing real turns against a specific deck's actual card texts exposes where that model is wrong or incomplete; 8 games across 10 decks produced roughly a dozen distinct confirmed findings plus one explicitly-flagged unresolved question, none of which were predictable in advance

## Evidence

- ev: Live play found a genuine card-design bug (Get Excited! whiffs completely if it is the last card in hand), a Mech-tribal deck's own support cards turned out not to be Mechs themselves (Legend/champion buffs did nothing for 3 rounds), and a specific rules ambiguity in how Reckoner's Arena's hold-trigger interacts with Hunt's combined conquer-or-hold phrasing -- none of which surfaced from the initial full rules-PDF read alone

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
