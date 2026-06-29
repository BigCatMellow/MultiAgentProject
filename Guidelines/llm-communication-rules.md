# Multi-Agent Token-Optimized Communication Protocol (MATOCP)
## Version: 3.2 (Revised)
## Target Agents: Gemini Core, Claude Code, OpenAI Codex

---

## 1. Rationale

Verbose agent-to-agent exchanges — greetings, hedges, restated context — cost tokens and add little signal for a machine reader. The fix is mundane, and borrowed from ordinary distributed-systems practice: structured payloads instead of prose for routine status, diffs instead of full-file rewrites for small changes, and full natural language reserved for moments something actually needs to be reasoned about, not just logged.

This version drops the earlier claims about attention mechanisms and "context window decay." Those describe model internals that no one outside the model provider can verify or tune for, and invoking them doesn't make the protocol work any better. The real case for compression is simpler: fewer tokens cost less, and structured data is less ambiguous than prose. That's justification enough on its own.

---

## 2. Core Directives

- **Phatic suppression.** Drop greetings, hedges, and restated context. Acknowledge with `!ACK`, not a sentence.
- **State over history.** Carry context via `STATE_SNAPSHOT`, not replayed transcripts, wherever the runtime supports state injection.
- **Mandatory diagnosis.** Every failure (`!ERR`, `!FIX`) carries a reason — short is fine, absent is not. This replaces the old rule banning explanation outright, which contradicted `!ERR`'s own requirement for a trace.
- **Escape hatch.** If nothing in Section 4 fits cleanly, emit one plain-language line prefixed `!NOTE` rather than force-fitting a token or failing silently. This is the only sanctioned exit from the shorthand grammar.
- **Monomorphism, with the above exception.** Outside reason fields and `!NOTE`, outputs follow the layouts in Sections 3 and 4.

---

## 3. Wire Formats

### 3.1 State payload: YAML, quoted where ambiguous

Bare scalars are fine for identifiers and paths. Quote anything a YAML parser could misread as a different type: `yes/no/true/false/on/off`, numbers with leading or trailing zeros, version strings, anything date-shaped. A silently miscoerced value in a code-editing pipeline costs more than the bytes saved by dropping the quotes.

```yaml
task_id: 89a2
status: triage
target: src/auth.py
impact: "regression_l12"
version: "1.10"
```

If your tokenizer doesn't reward YAML much over compact (single-line, no-whitespace) JSON for your actual payload shapes, JSON is a fine substitute — it sidesteps the type-coercion risk entirely. Measure on real payloads rather than assuming.

### 3.2 Code changes: Unified Diff Standard (UDS)

Full-file rewrites only above roughly a 75% delta threshold; otherwise a compressed diff.

```diff
@@ src/auth.py L45-52 @@
-    if user.session_expired():
-        return Redirect("/login")
+    if user.session_expired() or tokens.invalidated(user.id):
+        metrics.emit("auth_fail")
+        return Redirect("/login?reason=expired")
```

If a diff doesn't apply cleanly — context lines have drifted — agents emit `!REQ [target_path] @ current_contents` rather than guessing at an offset.

---

## 4. Operational Shorthand Matrix

| Token | Syntax | Target | Definition |
| --- | --- | --- | --- |
| `!ACK` | `!ACK [task_id]` | All agents | Confirms parse and state lock. |
| `!STATE` | `!STATE\n[YAML payload]` | Orchestrator | Overwrites execution parameters. |
| `!ERR` | `!ERR [code] reason="[text]"` | Validation | Failure with a mandatory short reason. A raw trace may follow if useful, but the reason itself is never optional. |
| `!FIX` | `!FIX [target] reason="[text]"` | Implementation | States what was actually wrong, before the patch that follows. Referenced in Section 2 of the prior draft but never defined in its matrix — defined here. |
| `!REQ` | `!REQ [asset_id] @ [property]` | Dependency fetch | Halts downstream steps pending missing state. |
| `!LGTM` | `!LGTM` | Review | Terminal pass. |
| `!PATCH` | `!PATCH [target_path]\n[UDS diff]` | Implementation | Inline diff substitution. |
| `!EXEC` | `!EXEC [runtime] c="[cmd]"` | Runner | Test, build, or validation trigger. |
| `!NOTE` | `!NOTE [text, ≤200 chars]` | Any | Escape hatch for anything the other tokens don't cleanly cover. |
| `!EOF` | `!EOF` | Context end | Releases the loop back to the user terminal. |

### 4.1 Extension Tokens

Not every new situation needs a new token. The test: a token earns its place when it names a genuinely different *kind* of message; a variant of an existing one — severity, confidence, a flag — belongs as a field instead, not a new verb. The six below pass that test.

| Token | Syntax | Target | Definition |
| --- | --- | --- | --- |
| `!ASK` | `!ASK [task_id] reason="[text]"` | Human | Blocks for an actual human decision. Distinct from `!REQ`: REQ polls another agent for missing state and can be auto-resolved; ASK can't be, without defeating its purpose. |
| `!WARN` | `!WARN [code] reason="[text]"` | Validation | Non-blocking caution — a pass with a caveat. Sits between `!LGTM` and `!ERR`. |
| `!REVERT` | `!REVERT [target_path] [task_id]` | Implementation | Explicit rollback of a prior `!PATCH`/`!FIX`, with provenance, instead of burying the undo inside another generic patch. |
| `!LOCK` | `!LOCK [target_path]` | Coordination | Claims exclusive editing rights to a path until `!UNLOCK` or `!EOF`. Matters once more than one agent might touch the same file. |
| `!UNLOCK` | `!UNLOCK [target_path]` | Coordination | Releases a path claimed by `!LOCK`. |
| `!HALT` | `!HALT [task_id] reason="[text]"` | Human | The one human-originated token in the matrix — interrupts an in-flight loop immediately. No matching RESUME: control is already back with you, same as after `!EOF`; a plain message restarts things. |

`!HALT` closes a real gap in the prior version: every other token flows agent-outward, and there was no defined way for a human to interrupt mid-run without breaking the grammar entirely.

The variant cases get fields, not tokens:

```
!PATCH src/billing/charge.py sensitive=true
@@ L88 @@
...
!FIX retry_logic.py reason="exponential backoff missing" confidence=medium
```

`sensitive=true` on `!PATCH` forces human review regardless of any `!LGTM` that follows. `confidence=` on `!FIX`/`!PATCH` (`high`/`medium`/`low`) lets triage prioritize the shaky ones first.

### 4.2 Session Lexicon

The matrix above is frozen — every agent is expected to already know it, the same way SQL keywords stay reserved regardless of what you name your tables. But a fixed list is never actually complete; Section 4.1 only exists because the original ten weren't enough, and the next gap is just as inevitable. Rather than treating every gap as a reason to edit this file, the protocol needs a way to coin terms at runtime — bounded, so it doesn't quietly rebuild the verbosity problem it was meant to solve.

**Convention.** Core and extension tokens are always uppercase (`!PATCH`, `!HALT`). A lowercase token (`!btx`, `!regen_icons`) is session-local: not in this spec, looked up in the running lexicon instead. Casing alone disambiguates "you should already know this" from "check the dictionary" — no extra punctuation needed.

**Minting.** `!DEF [lowercase_token] reason="[short definition]"` adds an entry to the lexicon. It's core grammar itself — frozen, uppercase — since the *ability* to mint is universal even though what gets minted isn't.

**The lexicon.** A flat map carried inside `STATE_SNAPSHOT`, not a separate file requiring its own fetch — anything not already in the snapshot might as well not exist for token-cost purposes.

```yaml
lexicon:
  btx:
    def: "billing transaction object, src/billing/models.py"
    defined_by: claude_code
    task_id: 89a2
    last_used: 91f0
```

**Guardrails**, because a dictionary that only grows is the same disease in a new shape:

- Check the lexicon before minting. Reuse beats redefinition.
- Don't mint for a one-off. If you won't need the term again this run, `!NOTE` it instead — `!DEF` is for things that recur.
- Prune on idle. An entry unused for some number of tasks (or past `!EOF`) drops from the snapshot rather than riding along indefinitely.
- Promote, don't accumulate. A term that earns reuse across multiple sessions is the signal to graduate it into the next spec version as a real uppercase token — exactly how `!ASK` and `!HALT` got here. The lexicon just lets that happen without a human re-editing this file every time.

---

## 5. Expected Savings — Illustrative, Not Benchmarked

These are hand-picked before/after pairs, not a measured benchmark. Treat the percentages as illustrative; real savings depend on what's actually being communicated, and shrink wherever `!NOTE` gets used.

| Verbose | MATOCP |
| --- | --- |
| "I checked the codebase and found the database timeout error is caused by a missing parameter on line 112 of db_pool.js. Adding timeout: 5000 to fix it." | `!FIX db_pool.js reason="missing timeout param, L112"` then `!PATCH db_pool.js` with the one-line diff. |
| "That looks correct. All 14 unit tests passed. We can move on." | `!LGTM` / `!EXEC npm c="test" -> PASS(14)` |
| "Could you clarify what API version we're targeting?" | `!REQ deployment @ api_version` |

---

## 6. Shared Rationale, Not a Side Channel

The prior draft split a human-readable "telemetry" line off the end of the payload and had the orchestrator strip it before forwarding to the next agent. That's removed here: it meant the next agent in the chain knew less than the human watching the terminal, which works against good decisions downstream and makes multi-agent failures harder to trace.

The reason fields from Section 4 now travel with the payload to every reader, human and agent alike. A visually distinct line is still fine for a terminal dashboard:

```
!PATCH src/main.go
@@ L12 @@
- fmt.Println("init")
+ log.Info().Msg("initialized core engine")
___
Replaced default logger with structured zerolog at init.
```

— but the `___` line is a display convention for the renderer, not a forwarding boundary. It still goes downstream.

---

## Changelog

### v3.2 (from v3.1)

- Added Section 4.2 (Session Lexicon): lowercase tokens for session-local terms, looked up in a running dictionary rather than the frozen matrix.
- Added `!DEF` as the frozen, uppercase token for minting new lexicon entries.
- Lexicon travels inside `STATE_SNAPSHOT` rather than requiring a separate fetch.
- Added guardrails (reuse-before-minting, no one-off definitions, pruning idle entries, promotion path into future spec versions) so the lexicon can't quietly re-create the original verbosity problem.

### v3.1 (from v3.0)

- Added `!ASK`, `!WARN`, `!REVERT`, `!LOCK`, `!UNLOCK`, `!HALT` as Extension Tokens (Section 4.1).
- Added `sensitive=` and `confidence=` as fields on `!PATCH`/`!FIX` instead of minting a token per variant.
- `!HALT` is the first human-originated token in the matrix; everything else previously flowed agent-outward only.

### v3.0 (from v2.2)

- Removed the attention-heads / context-decay framing in favor of a plain cost-and-ambiguity rationale.
- Replaced the blanket ban on explaining failures with a mandatory, length-capped reason field on `!ERR` / `!FIX`.
- Defined `!FIX`, which the prior draft referenced in prose but never specified in the matrix.
- Added `!NOTE` as a sanctioned escape hatch.
- Added YAML quoting guidance for type-ambiguous scalars; noted JSON as a fallback.
- Removed the scrub-before-forwarding behavior; rationale now travels with the payload to all readers.
- Reframed the savings table as illustrative rather than benchmarked.
