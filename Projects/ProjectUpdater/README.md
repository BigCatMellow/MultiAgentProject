# ProjectUpdater

A small, self-contained personal project-tracker web app: dashboard,
project list, quick-note capture, and an add-project form, with
stale/due-soon detection so projects don't silently go idle.

No server, no build step. Open `app/index.html` in a browser. Data
persists in the browser's `localStorage`.

Command Center integration is available through command URLs. From the MAP
workspace, use:

```sh
ai project new "Name" --goal "Finished state" --next-action "First step"
ai project update "Name" --progress 50 --status "In progress"
ai project note "Name" "What changed"
```

These commands open ProjectUpdater with an encoded `#cc=...` command. When
Command Center is running, they target its embedded same-origin ProjectUpdater
route; use `--target standalone` to force the file-backed standalone app. The
app then applies the change inside the browser that owns that `localStorage`.

See `shared/project-brief.md` for the objective and completion condition,
and `MAP_System/NEW_PROJECT_WIZARD.md` for the bootstrap process this
project followed.
