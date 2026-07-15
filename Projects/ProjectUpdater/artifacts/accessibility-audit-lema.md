# Accessibility / Responsive Audit

task_context: TASK-123 follow-up audit
auditor: codex-lab-lema
date: 2026-07-03
scope: read-only assessment of `Projects/ProjectUpdater/app/index.html`

## Summary

The ProjectUpdater implementation is keyboard reachable on desktop and its
main color palette is mostly contrast-safe, but it has two accessibility gaps
that should be fixed in a follow-up task:

- REQUIRED: mobile widths below 900px hide the only persistent navigation for
  Dashboard, Projects, Quick Note, and Add Project.
- REQUIRED: form controls and stateful controls lack programmatic labels and
  ARIA state, so screen-reader users do not get the same structure/state as
  sighted users.

No edits were made in this audit.

## Checks Run

```text
Static read:
- app/index.html CSS, generated controls, form markup, ARIA/label usage

Browser checks:
- Playwright/Chromium at 1280px, 820px, and 390px
- Tab sequence sampling on desktop
- computed contrast spot checks for theme tokens
```

## Findings

### REQUIRED: Mobile navigation disappears below 900px

Evidence:

- `app/index.html` has `@media (max-width: 900px) { ... #sidebar { display: none; } }`.
- Browser check at 820px and 390px reported `#sidebar` as `display: none` and
  `visible_sidebar_buttons: 0`.
- At those widths, the persistent buttons visible from the initial dashboard
  were only `+ New`, `Update now`, and project-card `Mark visited` actions.

Impact:

The non-functional requirement says the app should be responsive down to a
phone-width viewport. Hiding the sidebar removes the normal path to Dashboard,
Projects, Quick Note, and Add Project. Some views can still be reached by
indirect paths (`+ New`, search, stale banner), but there is no complete
alternate navigation model.

Required fix:

Add a mobile navigation affordance that exposes all core views below 900px.
Acceptable approaches include a compact top nav, segmented view switcher, or a
menu button that opens the existing view list. It should be keyboard reachable
and visible on phone-width screens.

### REQUIRED: Form controls need programmatic labels and control state

Evidence:

- Static scan found `label_count: 0` and `aria_count: 0`.
- Inputs/selects/textareas are visually preceded by `.fl` divs, but those divs
  are not associated with controls via `<label for="...">` or `aria-labelledby`.
- The Projects filter chips, sidebar view buttons, and priority segmented
  buttons show selected state only through CSS classes (`.on`).

Impact:

Keyboard users can reach the controls, but assistive technology does not get
reliable names or selected-state semantics for the app's dynamic controls.

Required fix:

Use real labels or `aria-labelledby` for form controls. Add state semantics for
stateful buttons, for example `aria-pressed` on filter chips and priority
buttons, and `aria-current="page"` or equivalent state on active view nav
buttons. Keep native `<button>`, `<input>`, `<select>`, and `<textarea>`
elements where possible.

### RECOMMENDED: Add deliberate focus styling

Evidence:

- Desktop Tab sampling reached search, `+ New`, sidebar buttons, dashboard
  action buttons, and project buttons.
- The active element retained browser default `outline: auto 1px`; the app has
  no explicit `:focus-visible` styling.

Impact:

Keyboard navigation is technically visible in Chromium, but the default outline
is thin against a visually dense dark UI and may vary by browser.

Recommended fix:

Add a high-contrast `:focus-visible` rule for buttons, links, form controls,
filter chips, and sidebar items.

### PASS: Primary color contrast is mostly acceptable

Spot-check results:

```text
text #F4F1E8 on bg1 #07111C: 16.81
muted rgba(..., .62) on bg2: 4.79
accent #3E8FC2 on bg2: 4.56
stale #CA8E7A on bg2: 5.91
healthy #A2CDB5 on bg2: 9.20
dark #07111C on accent #3E8FC2: 5.35
```

Note:

`--muted-2` at 45% opacity computes below 4.5:1 against several dark
backgrounds. It appears mostly used for secondary status/help text. If any
`--muted-2` text becomes essential instruction text, increase contrast.

## Follow-Up

Opened a follow-up MAP task depending on TASK-123 for the required fixes,
scoped to `Projects/ProjectUpdater/app/index.html`.
