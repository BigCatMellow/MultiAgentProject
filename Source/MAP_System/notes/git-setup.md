# Git Setup

## Status

- Root Git status: `normal`
- Remote: `https://github.com/BigCatMellow/MultiAgentProject.git`
- Branch: `main`
- Aider compatibility: `normal-root-git`

## Commands

Use normal Git from the canonical workspace root:

```bash
cd /home/home/Projects/MultiAgentProject
```

```bash
git status
git add .
git commit -m "Describe the change"
git push origin main
```

Agents may also use the compatibility wrapper:

```bash
MAP_System/scripts/map-git status
```

`MAP_System/scripts/map-git` now delegates to normal root Git.

## Restart Note

Before the next major MAP work session:

- inspect `git status`;
- review the cleanup/restructure diff;
- make a baseline commit;
- push to `origin/main` when the baseline is acceptable.

Aider should start from that committed baseline for anything beyond a narrow
single-file helper edit.

## History

The project previously used `.map-git` because root `.git` was blocked. That
fallback Git database has been promoted to normal `.git` so Aider and standard
Git tooling can operate from the canonical Projects repo. DEC-014 superseded
the older Downloads-path guidance; see `shared/canonical-repo.md`.

Preserved local backups:

- `.git-empty-2026-06-28/`
- `MAP_System/.git-unused-2026-06-28/`
