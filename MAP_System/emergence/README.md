<!-- hpom: file: emergence/README.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: TASK-052 emergence CLI implementation -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Emergence System

## What this is

The Emergence System is the creative discovery layer of MAP.

HPOM governs safe execution:
```
How does work move safely from task to review to release?
```

The Emergence System governs creative discovery:
```
What new thing is becoming possible because of the work?
```

## Core principle

```
Ideas are allowed to emerge freely.
Only promoted ideas are allowed to change the project.
```

An agent may notice and capture an idea.
An agent may not silently redirect the project because of that idea.

## The three layers

| Layer | Question | System |
|---|---|---|
| Execution | How do we move work safely? | HPOM |
| Discovery | What is becoming possible? | Emergence System |
| Governance | What becomes real? | Human Owner + Decision process |

## How emergence connects to HPOM

```
Insight → Synthesis → Idea → Experiment → Promotion → HPOM Task → Review → Release
```

The Emergence System creates candidates. HPOM executes approved work.

## The emergence loop

```
Observe → Connect → Synthesize → Name → Test → Promote
```

1. Observe what exists.
2. Notice patterns, tensions, combinations, gaps, or repeated problems.
3. Synthesize a new idea from existing material.
4. Name the idea clearly.
5. Test whether the idea is useful.
6. Promote it into a task, decision, project, or artifact if it survives.

## Artifact types

| Artifact | What it is | Status range |
|---|---|---|
| Insight | Something noticed | RAW → PROMOTED / DISMISSED |
| Synthesis | Two things combined into a third | CLARIFIED → PROMOTED |
| Idea | A possible thing to build or change | CANDIDATE → PROMOTED_TO_TASK |
| Experiment | A small safe test of an idea | PROPOSED → ADOPTED / REJECTED |
| Promotion | An idea becoming real work | PROPOSED → APPROVED |

## Folder structure

```
MAP_System/emergence/
  README.md               ← this file
  SYNTHESIS_METHODS.md    ← how to combine ideas
  IDEA_PROMOTION_RULES.md ← what qualifies an idea for promotion
  CREATIVE_REVIEW.md      ← quality standards and do-not-derail rules
  INDEX.md                ← running registry of active artifacts

  templates/
    INSIGHT_TEMPLATE.md
    SYNTHESIS_NOTE_TEMPLATE.md
    IDEA_CARD_TEMPLATE.md
    EXPERIMENT_TEMPLATE.md
    PROMOTION_RECORD_TEMPLATE.md

  insights/               ← MAP-system-level insight records
  synthesis/              ← MAP-system-level synthesis notes
  ideas/                  ← MAP-system-level idea cards
  experiments/            ← MAP-system-level experiment records
  promotions/             ← promotion records for ideas entering HPOM
```

Project-level folders live at:
```
Projects/<PROJECT>/
  insights/
  synthesis/
  ideas/
  experiments/
```

## Command-line capture

Use `MAP_System/scripts/map_emergence.py` for routine Command Center Lab
capture. The script creates artifacts from templates, assigns the next ID,
rebuilds `INDEX.md`, and validates that raw template placeholders are not left
behind.

Create an insight:

```bash
python3 MAP_System/scripts/map_emergence.py insight \
  "Short concrete observation" \
  --owner codex-lab-zanu \
  --related-task TASK-052
```

Create a follow-up idea:

```bash
python3 MAP_System/scripts/map_emergence.py idea \
  "Possible bounded improvement" \
  --owner codex-lab-zanu \
  --source INS-0001
```

Promote an idea into a proposal record:

```bash
python3 MAP_System/scripts/map_emergence.py promote IDEA-0001 \
  --owner command-center \
  --summary "Promote the bounded idea into HPOM shaping"
```

Maintain and check the registry:

```bash
python3 MAP_System/scripts/map_emergence.py list
python3 MAP_System/scripts/map_emergence.py rebuild-index
python3 MAP_System/scripts/map_emergence.py validate
```

For automation that needs every field explicit, use
`create <insight|synthesis|idea|experiment|promotion> --summary ...`.

Promotion records remain proposals until the approval fields are completed.
Creating a promotion record does not authorize implementation by itself; the
work still enters HPOM through normal task, review, and release gates.

## Agent rule

```
Notice freely.
Act carefully.
Promote deliberately.
```

If assigned work creates a useful new possibility, capture it in an insight record.
Do not act on it unless the task scope allows it or it has been promoted.

## Related files

- `SYNTHESIS_METHODS.md` — how to do synthesis
- `IDEA_PROMOTION_RULES.md` — promotion criteria
- `CREATIVE_REVIEW.md` — quality and safety rules
- `INDEX.md` — active artifact registry
- `MAP_System/shared/hpom.md` — the execution system this feeds into
- `MAP_System/shared/decisions.md` — where promoted ideas land as decisions
