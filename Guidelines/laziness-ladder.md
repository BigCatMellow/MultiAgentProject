# Laziness Ladder — Code Compression

Before writing a single line of code, walk the laziness ladder from rung 1 upward. Stop the moment a rung solves the problem. Never skip safety. Never skip input validation. Compress everything else.

---

## The Six-Rung Laziness Ladder

Walk top-to-bottom. Stop at the first rung that works.

### Rung 1 — YAGNI (Delete the Requirement)
Ask: does this feature actually need to exist right now?

- Is it speculative ("might be useful later")?
- Is it a nice-to-have with no concrete use case yet?
- Can the caller handle it themselves?

If yes to any → **don't build it.** Write nothing. The best code is no code.

---

### Rung 2 — Native Platform
Ask: does the OS, shell, browser, or runtime already do this?

- File I/O → `fs`, `open()`, `cat`, `cp`
- HTTP → `fetch`, `curl`, `urllib`
- Date/time → `Date`, `datetime`, `date` CLI
- JSON → built into every modern runtime
- Crypto → `crypto` module, `openssl` CLI
- Process management → `subprocess`, `child_process`, `&&`

If it's a shell one-liner or a single runtime API call → **use it. Write nothing custom.**

---

### Rung 3 — Standard Library
Ask: does the language's own stdlib cover this?

- Python: `pathlib`, `json`, `re`, `shutil`, `itertools`, `collections`, `hashlib`, `csv`, `sqlite3`
- Node: `path`, `fs/promises`, `crypto`, `url`, `stream`, `util`
- Browser: `URLSearchParams`, `FormData`, `AbortController`, `ResizeObserver`, `IntersectionObserver`

If stdlib has it → **use it.** Do not install a package for something `pathlib.Path` already handles.

---

### Rung 4 — Installed Dependency
Ask: is there already a package in this project that handles this?

Check `package.json`, `requirements.txt`, `go.mod`, etc. **before** importing anything new. If lodash is already in the project, don't write your own `groupBy`. If `dayjs` is installed, don't write your own date formatter.

Using an already-installed dep costs zero new surface area.

---

### Rung 5 — Single Expression
Ask: can the entire solution fit on one line without sacrificing clarity?

- Ternary over `if/else` for simple value selection
- Array methods chained over a loop-and-accumulate pattern
- Destructuring over multiple assignment lines
- Template literals over string concatenation
- Nullish coalescing / optional chaining over guard blocks

If it's genuinely one clean expression → **write it inline.** No helper function needed.

---

### Rung 6 — Minimal Custom Code
All five rungs above failed. Now write code — but apply the minimum surface area rule:

- **Solve exactly the problem at hand.** No generalization, no extensibility hooks, no config parameters you don't currently use.
- **No abstraction layers** unless two or more callsites already exist.
- **No class** when a function works. No function when an expression works.
- **No comments** explaining what the code does — only comments explaining *why* a non-obvious choice was made.
- Validate inputs at the boundary. Fail loudly. Return the minimum viable data shape.

---

## What Never Gets Compressed

Two things are exempt from the ladder and must always be written in full:

**Safety** — Auth checks, permission guards, rate limiting, data sanitization, CORS headers. Never skip or stub these.

**Input validation** — Validate all external data at every entry point (API inputs, file reads, user input, env vars). Type-check, range-check, shape-check. Throw or return an error immediately on bad input before any processing begins.

These are not "overhead." They are load-bearing. Compress around them, not through them.

---

## Anti-Patterns (Rung Violations)

| Violation | Correct Rung |
|---|---|
| Writing a JSON parser | Rung 2 — it's in every runtime |
| `npm install uuid` for a one-off ID | Rung 2 — `crypto.randomUUID()` |
| Writing `flatten(arr)` | Rung 5 — `arr.flat()` |
| Writing `_.groupBy` without lodash installed | Rung 5 — one-liner with `reduce` |
| Adding a `config` object "for flexibility" | Rung 6 violation — YAGNI |
| Helper function with one callsite | Rung 5/6 — inline it |
| 40-line class with two methods | Rung 6 — two functions |
| Downloading a 2MB library to left-pad a string | Rung 3/5 — `str.padStart()` |

---

## Code Output Format

When returning code changes, apply the same compression logic to the *output* itself:

**Prefer diffs over full rewrites** when the delta is under ~75% of the file. A diff communicates exactly what changed and costs far fewer tokens than re-emitting a file the reader already has.

```diff
@@ src/auth.py L45-52 @@
-    if user.session_expired():
-        return Redirect("/login")
+    if user.session_expired() or tokens.invalidated(user.id):
+        metrics.emit("auth_fail")
+        return Redirect("/login?reason=expired")
```

Full rewrite is appropriate when: the file is small, the delta genuinely exceeds ~75%, or the reader doesn't have the original context.

In a multi-agent pipeline, pair the diff with a `!PATCH` token (MATOCP §4): `!PATCH src/auth.py` followed by the UDS block. This lets downstream agents apply the change without re-reading the whole file.

---

## Quick Checklist

Before committing any new code:

- [ ] Does this feature need to exist at all? (Rung 1)
- [ ] Did I check the runtime/OS first? (Rung 2)
- [ ] Did I check the stdlib? (Rung 3)
- [ ] Did I check existing deps? (Rung 4)
- [ ] Can it be a single expression? (Rung 5)
- [ ] If custom: is this the minimum surface area? (Rung 6)
- [ ] Are safety and validation fully intact regardless of compression?
