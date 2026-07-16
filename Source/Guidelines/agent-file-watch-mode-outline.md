# Agent File-Watching Mode: Token-Efficient Design Outline

## Purpose

This document explains how an AI coding agent should use a **file-watching / listening mode** without wasting tokens.

The core rule is simple:

> The file watcher should listen locally.  
> The AI model should only be called when there is a meaningful change that requires reasoning.

A good design separates the cheap part from the expensive part:

| Component | Job | Uses AI Tokens? |
|---|---|---:|
| File watcher | Watches files for changes | No |
| Change filter | Ignores irrelevant files | No |
| Diff generator | Finds what changed | No |
| Router | Decides which agent should care | Usually no |
| AI agent | Reviews, edits, explains, or acts | Yes |

The watcher can stay active all day.  
The AI should not.

---

# 1. Core Principle

## Do not make the AI “wait”

The AI model should not be sitting in a loop asking:

```text
Did anything change?
Did anything change?
Did anything change?
```

That is wasteful.

Instead, use a local process to watch files. The local process should wake the AI only when needed.

Correct pattern:

```text
File changes locally
    ↓
Watcher detects change
    ↓
Watcher filters junk
    ↓
Watcher creates a diff
    ↓
Only the relevant diff is sent to the AI
```

Incorrect pattern:

```text
Every 30 seconds:
    AI reads the project
    AI checks whether anything changed
    AI thinks about whether to act
```

---

# 2. Recommended Architecture

Use this pipeline:

```text
Filesystem Watcher
    ↓
Ignore Rules
    ↓
Debounce / Batch Changes
    ↓
Diff Generator
    ↓
Change Classifier
    ↓
Agent Router
    ↓
Specific Agent Action
    ↓
Write Result / Report
```

## Component Responsibilities

### 2.1 Filesystem Watcher

The watcher observes file changes using local OS events.

Examples:

- Linux: `inotify`
- macOS: `fswatch`, `watchman`, `fsevents`
- Windows: `ReadDirectoryChangesW`, `watchdog`
- Cross-platform: Node `chokidar`, Python `watchdog`

The watcher itself must not call the AI.

Its only job is to detect file changes.

---

### 2.2 Ignore Rules

The watcher should ignore files and folders that do not need AI review.

Common ignores:

```gitignore
.git/
node_modules/
vendor/
dist/
build/
coverage/
.cache/
.tmp/
logs/
*.log
*.lock
*.map
*.min.js
*.pyc
__pycache__/
.DS_Store
```

Also ignore generated files unless the project specifically requires checking them.

Examples of generated files:

- compiled JavaScript
- build artifacts
- bundled files
- minified files
- package lockfiles, unless dependency changes matter
- generated documentation
- cache folders

---

### 2.3 Debounce / Batch Changes

Many editors save files in bursts.

A single user save can produce multiple filesystem events:

```text
file changed
file renamed
temp file created
file changed again
```

Do not call the AI for every event.

Use a debounce window.

Recommended default:

```text
Wait 2–5 seconds after the last change before acting.
```

Example:

```text
Change detected at 10:00:00
Another change at 10:00:02
Another change at 10:00:03

Wait until 10:00:08
Then process all changes together.
```

This reduces duplicate AI calls.

---

### 2.4 Diff Generator

The agent should not reread the entire repository after every change.

Instead, generate a focused diff.

Preferred input to the AI:

```diff
- old line
+ new line
```

or:

```text
Changed file: src/auth/login.ts
Reasonable context: 30 lines around changed sections
```

Avoid sending:

```text
Here is the entire project again.
```

Full files should only be sent when:

- the file is small,
- the diff is confusing without context,
- the change affects the entire file,
- the agent explicitly needs the full file to avoid mistakes.

---

### 2.5 Change Classifier

Before calling an AI model, classify the change locally if possible.

Examples:

| Change Type | Likely Action |
|---|---|
| `.md` documentation change | Documentation agent |
| `.css` / theme change | UI/style agent |
| test file changed | Test-review agent |
| config changed | Build/devops agent |
| source code changed | Code-review agent |
| lockfile changed | Dependency/security agent |
| generated file changed | Usually ignore |

The classifier should answer:

```text
Does this change need AI reasoning?
Which agent should receive it?
How much context is needed?
```

---

### 2.6 Agent Router

Route changes to the smallest useful agent.

Do not send every change to every agent.

Bad:

```text
Every agent reviews every file change.
```

Better:

```text
CSS changed → UI agent only.
Auth code changed → security/code agent.
README changed → documentation agent.
Tests changed → testing agent.
```

If multiple agents need to act, run them in a controlled order.

Example:

```text
1. Code agent reviews implementation.
2. Test agent checks coverage.
3. Documentation agent updates docs only if behavior changed.
4. Project manager agent summarizes final result.
```

---

# 3. Token Control Rules

## 3.1 Never Poll With the AI

The AI must not repeatedly check for changes.

Bad:

```text
Every minute, ask the AI to inspect the project.
```

Good:

```text
Local watcher waits.
AI is called only after meaningful file changes.
```

---

## 3.2 Send Diffs, Not Whole Projects

Default to sending:

- changed filename
- change type
- diff
- nearby context
- relevant project rules
- specific task for the agent

Avoid sending:

- entire repo
- unrelated files
- long chat history
- old summaries unless needed
- generated files

---

## 3.3 Keep Agent Memory Compact

The agent should maintain a short project state file instead of relying on a huge chat history.

Recommended files:

```text
.agent/state.md
.agent/decisions.md
.agent/tasks.md
.agent/watch-log.md
```

These files should be concise.

Example:

```md
## Current Project State

- App type: React + Node
- Main goal: improve coverage scheduler UI
- Important rule: avoid changing output format unless asked
- Last completed task: added absence modal search
- Known risk: print layout breaks if cell widths change
```

---

## 3.4 Use Escalation Rules

The agent should only request more context when necessary.

Example escalation ladder:

```text
Level 1: Diff only
Level 2: Diff + surrounding functions
Level 3: Full changed file
Level 4: Related files
Level 5: Wider project scan
```

The agent should start at the lowest useful level.

---

# 4. Event Payload Format

When the watcher wakes an agent, send a structured message.

Example:

```json
{
  "event_type": "file_change",
  "changed_files": [
    {
      "path": "src/components/AbsenceModal.tsx",
      "change_type": "modified",
      "language": "typescript",
      "diff": "...",
      "context": "User changed absence modal search behavior."
    }
  ],
  "ignored_files": [
    "dist/bundle.js",
    ".cache/state.json"
  ],
  "agent_role": "code_reviewer",
  "task": "Review the changed code for bugs, regressions, and missing edge cases. Do not rewrite unrelated code.",
  "token_policy": {
    "prefer_diff_only": true,
    "ask_for_more_context_only_if_required": true,
    "do_not_scan_repo_unless_necessary": true
  }
}
```

---

# 5. Agent Behavior Rules

The agent must follow these rules when activated.

## 5.1 Act Only on the Change

The agent should focus on the changed files and the requested task.

It should not wander into unrelated improvements unless the change reveals a serious issue.

Bad:

```text
The CSS changed, so I rewrote the data model.
```

Good:

```text
The CSS changed. I reviewed layout impact and found one possible print issue.
```

---

## 5.2 Be Explicit About Scope

The agent should state what it reviewed.

Example:

```text
Reviewed:
- src/components/AbsenceModal.tsx
- diff only
- no full project scan performed

Found:
- Search now ignores archived substitutes.
- Possible issue: empty search returns no results instead of all results.
```

---

## 5.3 Do Not Invent Context

If the diff is insufficient, the agent should say so.

Example:

```text
The diff alone is not enough to confirm this. I need the parent function or the full file.
```

Do not guess.

---

## 5.4 Do Not Auto-Edit Without Permission Rules

The agent should know whether it is allowed to edit files.

Recommended modes:

| Mode | Behavior |
|---|---|
| `review_only` | Report issues, do not change files |
| `safe_edit` | Fix obvious local issues only |
| `full_edit` | May edit related files if needed |
| `recommend_only` | Suggest changes, no implementation |

Default should be:

```text
safe_edit
```

This prevents unnecessary broad rewrites.

---

# 6. File Watch Rules

## 6.1 Watch These By Default

```text
src/
app/
components/
lib/
server/
client/
tests/
docs/
scripts/
config/
```

## 6.2 Usually Ignore These

```text
.git/
node_modules/
dist/
build/
coverage/
.cache/
logs/
tmp/
vendor/
```

## 6.3 Be Careful With These

Some files are important but noisy.

```text
package-lock.json
pnpm-lock.yaml
yarn.lock
poetry.lock
Cargo.lock
go.sum
```

Only send lockfile changes to the AI when:

- dependencies changed,
- security review is needed,
- builds started failing,
- the lockfile changed unexpectedly.

---

# 7. Suggested Agent Instructions

Use this as the core instruction for the listening agent:

```md
You are operating in file-watch mode.

You are not responsible for constantly checking the project. A local watcher will notify you only when meaningful files change.

When activated:

1. Review only the provided changed files, diffs, and relevant context.
2. Do not scan the entire repository unless the provided context is insufficient.
3. Prefer the smallest possible context needed to answer correctly.
4. If a change is irrelevant to your role, say so and stop.
5. If you need more context, ask for the specific file or function you need.
6. Do not make unrelated improvements.
7. Do not rewrite code outside the changed area unless required.
8. Clearly separate:
   - what changed,
   - what you checked,
   - what you found,
   - what you changed or recommend.
9. Avoid repeated model calls while idle.
10. Never poll for file changes yourself.
```

---

# 8. Example Workflows

## 8.1 Documentation Change

```text
README.md changed
    ↓
Watcher detects change
    ↓
Diff generated
    ↓
Documentation agent receives diff
    ↓
Agent checks clarity, accuracy, and missing setup steps
```

The code agent should not be called.

---

## 8.2 Source Code Change

```text
src/auth/login.ts changed
    ↓
Watcher detects change
    ↓
Diff generated
    ↓
Code-review agent receives diff
    ↓
Security agent receives diff only if auth/security-sensitive logic changed
```

The documentation agent should only be called if user-facing behavior changed.

---

## 8.3 CSS / Theme Change

```text
theme.css changed
    ↓
Watcher detects change
    ↓
UI agent receives diff
    ↓
Agent checks spacing, layout, accessibility, and regressions
```

The database agent should not be called.

---

## 8.4 Test Change

```text
coverage.test.ts changed
    ↓
Test agent receives diff
    ↓
Agent checks test usefulness, missing cases, and false positives
```

The implementation agent should only be called if the test reveals a likely code issue.

---

# 9. Failure Modes to Avoid

## 9.1 AI Polling Loop

Problem:

```text
The AI wakes every minute and checks for changes.
```

Why this is bad:

- wastes tokens
- creates unnecessary logs
- can produce fake work
- may cause accidental edits

Fix:

```text
Use local file events. Only call AI after real changes.
```

---

## 9.2 Whole-Repo Re-Reads

Problem:

```text
Every small save sends the whole repository to the AI.
```

Why this is bad:

- expensive
- slow
- increases confusion
- makes the agent more likely to edit unrelated files

Fix:

```text
Send diff first. Escalate only if needed.
```

---

## 9.3 Every Agent Sees Every Change

Problem:

```text
CSS change goes to code, docs, tests, database, and PM agents.
```

Why this is bad:

- multiplies token use
- produces conflicting advice
- creates unnecessary work

Fix:

```text
Use routing rules.
```

---

## 9.4 No Debounce

Problem:

```text
One save triggers five AI calls.
```

Why this is bad:

- duplicate reviews
- wasted tokens
- inconsistent responses

Fix:

```text
Wait 2–5 seconds and batch changes.
```

---

## 9.5 Acting on Generated Files

Problem:

```text
Agent reviews dist/bundle.js after every build.
```

Why this is bad:

- generated files are noisy
- changes are usually not human-authored
- diffs are huge

Fix:

```text
Ignore generated files by default.
```

---

# 10. Minimal Implementation Plan

## Step 1: Add Ignore Rules

Create:

```text
.agentignore
```

Example:

```gitignore
.git/
node_modules/
dist/
build/
coverage/
.cache/
logs/
*.log
*.map
*.min.js
```

---

## Step 2: Add a Watcher

Use a simple watcher script.

The watcher should:

```text
1. Detect changed files.
2. Ignore files from .agentignore.
3. Wait 2–5 seconds.
4. Batch changes.
5. Generate diffs.
6. Route the event to the correct agent.
```

---

## Step 3: Add a Routing Table

Example:

```yaml
routes:
  - match: ["*.md"]
    agent: "documentation_agent"

  - match: ["*.css", "*.scss"]
    agent: "ui_agent"

  - match: ["*.test.ts", "*.spec.ts"]
    agent: "test_agent"

  - match: ["src/auth/**", "src/security/**"]
    agent: "security_agent"

  - match: ["src/**", "app/**", "lib/**"]
    agent: "code_agent"
```

---

## Step 4: Add Agent Modes

Example:

```yaml
agents:
  code_agent:
    mode: safe_edit
    max_context: diff_plus_function

  documentation_agent:
    mode: safe_edit
    max_context: changed_file

  security_agent:
    mode: review_only
    max_context: diff_plus_related_files

  test_agent:
    mode: safe_edit
    max_context: diff_plus_test_file
```

---

## Step 5: Add Logs

The system should keep a short local log.

Example:

```md
# Watch Log

## 2026-06-22 18:15
Changed:
- src/auth/login.ts

Agent:
- code_agent

Action:
- Reviewed diff only
- Found missing null check
- Applied safe local fix
```

Do not send the whole log to the AI every time.

Only send relevant recent entries.

---

# 11. Agent Output Format

The agent should respond in a predictable format.

```md
## Scope

Reviewed:
- `src/auth/login.ts`
- diff only

Did not review:
- full repository
- unrelated files

## Finding

Brief explanation of issue or confirmation that no issue was found.

## Action Taken

State what was changed, or say:

No file changes made.

## Need More Context?

State exactly what is needed, if anything.
```

---

# 12. Checklist

Before calling the AI, confirm:

```text
[ ] Did a meaningful file change occur?
[ ] Is the file not ignored?
[ ] Have rapid duplicate events been batched?
[ ] Can this be handled without AI?
[ ] Is the diff smaller than the full file?
[ ] Is only the relevant agent being called?
[ ] Is the task specific?
[ ] Is the agent forbidden from polling?
[ ] Is the agent forbidden from broad unrelated edits?
```

Before the agent acts, confirm:

```text
[ ] Do I understand the change?
[ ] Do I know my role?
[ ] Am I reviewing only the relevant files?
[ ] Is the provided context enough?
[ ] Am I avoiding unrelated changes?
[ ] Am I using the smallest context needed?
[ ] Am I clear about what I did and did not review?
```

---

# 13. Final Design Rule

A good listening-mode agent is not an AI that constantly listens.

It is:

```text
A local watcher that listens constantly,
plus an AI agent that acts only when needed.
```

The watcher protects tokens.

The router protects attention.

The diff protects context size.

The agent protects project quality.
