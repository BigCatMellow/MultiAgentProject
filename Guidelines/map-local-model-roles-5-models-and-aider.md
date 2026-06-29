# MAP Local Model Roles: 5 Local Models + Aider

This file explains how to use five local Ollama models and Aider inside the MAP system.

The goal is not to replace paid models. The goal is to reduce paid-token use by assigning low-risk, repetitive, local work to small models running on the Linux Mint machine.

## Machine Assumption

This setup assumes a Linux Mint system running mostly in CPU-only mode.

Expected hardware profile:

- Intel integrated graphics
- no NVIDIA or AMD AI-capable GPU
- about 15 GB system RAM
- Ollama running in CPU-only mode

Because of that, this setup favors small models.

---

# Quick Role Summary

| Tool / Model | Type | Best MAP Role |
|---|---|---|
| `llama3.2:3b` | Model | Main project-brain summarizer and general MAP assistant |
| `llama3.2:1b` | Model | Fast fallback summarizer for very light tasks |
| `qwen2.5-coder:3b` | Model | Main local coding, JSON, schema, and validation helper |
| `qwen2.5-coder:1.5b` | Model | Fast fallback code/JSON helper |
| `gemma3:4b` | Model | Acceptance criteria, markdown cleanup, and structured writing |
| Aider | Tool | Terminal coding assistant that can use `qwen2.5-coder:3b` through Ollama |

---

# Important Distinction

The models are the local “brains.”

Aider is not a model. Aider is a tool that lets a model work inside a real code/project folder.

Plain version:

```text
Ollama runs the model.
qwen2.5-coder:3b provides the code reasoning.
Aider connects that model to your files and Git workflow.
```

So Aider should be treated as the MAP coding workbench, not as a sixth model.

---

# 1. `llama3.2:3b`

## Best Role

`llama3.2:3b` should be the main general-purpose MAP assistant.

Use it when the task is mostly about reading, summarizing, explaining, classifying, or orienting around project information.

It is the best default local model for the MAP project brain.

## Best Uses

Use `llama3.2:3b` for:

- summarizing `shared/current-state.md`;
- summarizing `shared/memory-map.md`;
- reading recent `events/events.jsonl` entries;
- explaining what a task is asking for;
- identifying blocked tasks;
- creating short session summaries;
- extracting unresolved questions;
- comparing a task against the current project state;
- giving a plain-English overview of the MAP system.

## MAP Agent Names

Possible agent names:

- `MAP-Summarizer`
- `MAP-Orientation-Agent`
- `MAP-Event-Digest-Agent`
- `MAP-Status-Reader`
- `MAP-Project-Brain-Assistant`

## Good Prompt Example

```text
You are MAP-Summarizer.

Read the provided MAP files and produce a short summary with these sections:

1. Current project state
2. Recently completed work
3. Blocked or risky tasks
4. Open questions
5. Suggested next action

Do not invent information. If something is unclear, say so.
```

## What Not to Use It For

Do not rely on `llama3.2:3b` for:

- complex architecture decisions;
- large code changes;
- final review of important work;
- difficult debugging;
- security-sensitive judgment;
- deciding whether a major system design is correct.

Use it to prepare information before a paid model or human does the final judgment.

---

# 2. `llama3.2:1b`

## Best Role

`llama3.2:1b` should be the fast fallback assistant.

Use it when speed matters more than depth.

It is useful for very small tasks where a bigger model would be wasteful or slow.

## Best Uses

Use `llama3.2:1b` for:

- very short summaries;
- quick classification of task type;
- extracting titles or headings;
- turning event entries into one-line summaries;
- identifying whether a file looks like a task, note, decision, or review;
- creating quick bullet-point digests;
- rewriting short text for clarity.

## MAP Agent Names

Possible agent names:

- `MAP-Fast-Summarizer`
- `MAP-Quick-Classifier`
- `MAP-Light-Digest-Agent`
- `MAP-Event-One-Liner`

## Good Prompt Example

```text
You are MAP-Quick-Classifier.

Classify this item as one of:

- REQUIREMENT
- DECISION
- TASK
- UNRESOLVED_QUESTION
- EVENT
- REVIEW
- UNKNOWN

Return only the label and one short reason.
```

## What Not to Use It For

Do not rely on `llama3.2:1b` for:

- nuanced reasoning;
- long documents;
- code edits;
- acceptance criteria for complex tasks;
- final review;
- interpreting vague or conflicting requirements.

This is a speed tool, not a reasoning tool.

---

# 3. `qwen2.5-coder:3b`

## Best Role

`qwen2.5-coder:3b` should be the main technical helper.

Use it when the task involves code, JSON, schemas, scripts, SQLite, file paths, or validation logic.

This is the main local model to connect to Aider.

## Best Uses

Use `qwen2.5-coder:3b` for:

- repairing malformed task JSON;
- checking task files against `templates/task.json`;
- writing small Python scripts;
- editing validation scripts;
- checking whether `output_paths` are too broad;
- creating SQLite helper commands;
- writing file-path validation logic;
- generating simple test cases;
- explaining small code files;
- fixing syntax errors;
- helping create MAP scripts such as `validate_task.py`, `claim_task.py`, or `log_event.py`.

## MAP Agent Names

Possible agent names:

- `MAP-JSON-Repair-Agent`
- `MAP-Validator-Agent`
- `MAP-Script-Helper`
- `MAP-SQLite-Helper`
- `MAP-Code-Edit-Agent`
- `MAP-Path-Checker`

## Good Prompt Example

```text
You are MAP-Validator-Agent.

Review this task JSON against the MAP task template.

Check for:
- missing objective;
- missing input_paths;
- missing output_paths;
- missing dependencies;
- missing acceptance_criteria;
- invalid JSON;
- output paths that are too broad.

Return:
1. PASS or FAIL
2. Missing fields
3. Unsafe fields
4. Suggested corrected JSON

Do not change the task objective unless required for valid JSON.
If the correct value cannot be inferred, write NEEDS_HUMAN_DECISION.
```

## What Not to Use It For

Do not rely on `qwen2.5-coder:3b` for:

- high-level product decisions;
- final architectural judgment;
- large multi-file refactors;
- human policy decisions;
- interpreting vague user intent without review;
- final approval before merging important work.

It is a helper for technical structure, not the final authority.

---

# 4. `qwen2.5-coder:1.5b`

## Best Role

`qwen2.5-coder:1.5b` should be the fast technical fallback.

Use it when `qwen2.5-coder:3b` is too slow, or when the task is simple enough that the larger coder model is unnecessary.

## Best Uses

Use `qwen2.5-coder:1.5b` for:

- detecting invalid JSON;
- checking whether required keys exist;
- fixing small syntax issues;
- formatting JSON;
- writing tiny shell commands;
- explaining a short code snippet;
- checking file extensions;
- identifying broad or risky output paths;
- creating small regex or path-matching examples.

## MAP Agent Names

Possible agent names:

- `MAP-Fast-JSON-Checker`
- `MAP-Light-Code-Helper`
- `MAP-Syntax-Repair-Agent`
- `MAP-Path-Sanity-Checker`

## Good Prompt Example

```text
You are MAP-Fast-JSON-Checker.

Check this JSON for:
- valid syntax;
- missing required keys;
- empty arrays;
- empty strings.

Return:
1. VALID or INVALID
2. Errors found
3. Minimal corrected JSON if possible

Do not rewrite the meaning.
```

## What Not to Use It For

Do not rely on `qwen2.5-coder:1.5b` for:

- writing larger scripts;
- database design;
- complex validation logic;
- multi-file code edits;
- final code review;
- broad reasoning about architecture.

This is a quick technical checker, not the main coder.

---

# 5. `gemma3:4b`

## Best Role

`gemma3:4b` should be the writing and criteria helper.

Use it when the task needs clean wording, pass/fail criteria, markdown cleanup, or structured documentation.

This model is useful when the output should be readable and organized.

## Best Uses

Use `gemma3:4b` for:

- drafting acceptance criteria;
- rewriting vague task descriptions;
- cleaning markdown structure;
- improving headings;
- removing repeated wording;
- converting loose notes into structured notes;
- drafting review comments;
- summarizing decisions;
- writing clearer unresolved questions;
- formatting documentation without changing meaning.

## MAP Agent Names

Possible agent names:

- `MAP-Acceptance-Criteria-Agent`
- `MAP-Markdown-Cleanup-Agent`
- `MAP-Review-Draft-Agent`
- `MAP-Decision-Log-Agent`
- `MAP-Documentation-Helper`

## Good Prompt Example

```text
You are MAP-Acceptance-Criteria-Agent.

Turn this task description into binary acceptance criteria.

Rules:
- Each criterion must be objectively checkable.
- Mention exact files when possible.
- Avoid vague words like "better", "improved", or "cleaner" unless they are defined.
- Include a criterion that no files outside output_paths are modified.
- If the task is too vague, return NEEDS_HUMAN_DECISION.

Return only a markdown list.
```

## Markdown Cleanup Prompt

```text
You are MAP-Markdown-Cleanup-Agent.

Clean this markdown file.

Rules:
- Preserve meaning.
- Do not add new decisions.
- Do not remove unresolved questions.
- Improve headings and spacing.
- Remove obvious duplication.
- Keep the document concise.
- Flag anything that looks like a decision but is not listed in shared/decisions.md.
```

## What Not to Use It For

Do not rely on `gemma3:4b` for:

- coding;
- schema repair;
- SQLite logic;
- final review of technical work;
- major architecture decisions;
- tasks requiring exact file-state reasoning.

It is best for structured writing and clarity.

---

# 6. Aider

## What Aider Is

Aider is a terminal coding assistant.

It is not a model.

Aider connects a model to a project folder so the model can help edit files. In this MAP setup, Aider should mainly use `qwen2.5-coder:3b`.

Use Aider when you want the local coding model to work with actual files instead of just answering in chat.

## Best MAP Role

Aider should be the local MAP coding workbench.

Use it for narrow, controlled edits where the target files are clear.

## Best Uses

Use Aider for:

- editing one task JSON file;
- repairing malformed JSON;
- writing small Python scripts;
- updating validation scripts;
- creating simple SQLite helper scripts;
- fixing syntax errors;
- adding small tests;
- editing files listed in a task's `output_paths`;
- making narrow documentation edits when the files are specified.

## Aider Agent Name

Possible agent names:

- `MAP-Aider-Code-Agent`
- `MAP-Local-Code-Worker`
- `MAP-Task-Implementation-Helper`
- `MAP-Validation-Script-Worker`

## Recommended Model

Use:

```text
qwen2.5-coder:3b
```

Fallback:

```text
qwen2.5-coder:1.5b
```

## Basic Command

Run from the MAP folder:

```bash
cd ~/Downloads/MultiAgentProject/MAP_System
aider --model ollama_chat/qwen2.5-coder:3b
```

Fallback:

```bash
cd ~/Downloads/MultiAgentProject/MAP_System
aider --model ollama_chat/qwen2.5-coder:1.5b
```

## Safer Usage Rule

Before using Aider, make sure Git is initialized and clean:

```bash
git status
```

If the project is not in Git yet:

```bash
git init
git add .
git commit -m "Baseline before local AI edits"
```

Then use Aider only for narrow work.

## Good Aider Prompt Example

```text
You are working in the MAP system.

Task:
Create scripts/validate_task.py.

Rules:
- Read templates/task.json before coding.
- Validate required fields.
- Reject empty output_paths.
- Reject empty acceptance_criteria.
- Reject output_paths that are too broad, such as ".", "/", "shared/", or the project root.
- Print clear errors.
- Do not modify files outside scripts/validate_task.py.
```

## Bad Aider Prompt Example

```text
Improve the MAP system.
```

That is too broad.

## What Not to Use Aider For

Do not use Aider for:

- vague tasks;
- whole-project rewrites;
- editing many files at once;
- changing architecture without a task;
- final approval;
- unsupervised large refactors;
- modifying `shared/` project truth unless the task explicitly allows it.

Aider should be treated like a useful local junior coding assistant: helpful, but supervised.

---

# Recommended Division of Labor

## Use Local Models For

Local models should handle cheap, repetitive work:

- summarize files;
- clean markdown;
- draft acceptance criteria;
- check task metadata;
- repair simple JSON;
- write small scripts;
- identify missing task fields;
- create event summaries;
- prepare information for paid review.

## Use Paid Models For

Paid models should handle higher-risk work:

- architecture review;
- final approval;
- difficult debugging;
- major refactors;
- complex reasoning;
- conflicting requirements;
- security-sensitive decisions;
- deciding whether a local model's output is correct.

---

# Suggested MAP Workflow

A good low-cost workflow:

```text
1. llama3.2:3b summarizes the task and relevant project files.
2. qwen2.5-coder:3b checks the task JSON structure.
3. gemma3:4b drafts acceptance criteria.
4. qwen2.5-coder:3b suggests narrow output_paths.
5. Aider applies narrow approved edits using qwen2.5-coder:3b.
6. A human or paid model reviews anything uncertain.
7. The final task enters the normal MAP validation/claim/review workflow.
```

This keeps the local models doing work they are good at while preventing them from becoming the final authority on important decisions.

---

# Quick Reference

| Need | Use |
|---|---|
| Summarize project state | `llama3.2:3b` |
| Fast tiny summary | `llama3.2:1b` |
| Summarize event logs | `llama3.2:3b` or `llama3.2:1b` |
| Explain a task | `llama3.2:3b` |
| Repair task JSON | `qwen2.5-coder:3b` |
| Fast JSON syntax check | `qwen2.5-coder:1.5b` |
| Write validation scripts | `qwen2.5-coder:3b` through Aider |
| Check schemas | `qwen2.5-coder:3b` |
| Draft acceptance criteria | `gemma3:4b` |
| Clean markdown | `gemma3:4b` |
| Draft review comments | `gemma3:4b` |
| Edit actual project files | Aider with `qwen2.5-coder:3b` |
| Final architecture review | Paid model or human |
| Final code review | Paid model or human |
| Major refactor | Paid model or human-supervised agent |

---

# Installation Commands

## Pull local MAP models

```bash
# Primary local models
ollama pull llama3.2:3b
ollama pull qwen2.5-coder:3b
ollama pull gemma3:4b

# Fallback models
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:1.5b

# Show installed models
ollama list
```

## Install Aider

```bash
sudo apt update
sudo apt install -y pipx python3-venv
pipx ensurepath
pipx install aider-chat
```

After `pipx ensurepath`, you may need to close and reopen Terminal.

## Run Aider with Ollama

```bash
cd ~/Downloads/MultiAgentProject/MAP_System
aider --model ollama_chat/qwen2.5-coder:3b
```

Fallback:

```bash
cd ~/Downloads/MultiAgentProject/MAP_System
aider --model ollama_chat/qwen2.5-coder:1.5b
```

---

# Practical Rule

Use local models and Aider as assistants, not authorities.

They are useful for reducing paid-token waste, especially on boring support work. They should not be trusted as the final reviewer for important architecture or code decisions.
