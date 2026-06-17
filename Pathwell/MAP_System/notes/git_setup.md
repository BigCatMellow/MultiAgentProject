# Git Setup

This workspace currently has `.git` occupied by a read-only tmpfs mount point. Normal `git status` cannot work until that mount is removed by the host environment.

To keep the project usable now, this repo uses a separate Git directory:

```bash
MAP_System/scripts/setup_git_fallback.sh
MAP_System/scripts/map-git status
MAP_System/scripts/map-git add .
MAP_System/scripts/map-git commit -m "Initial MAP collaboration scaffold"
```

`MAP_System/scripts/map-git` is a thin wrapper around:

```bash
git --git-dir=.map-git --work-tree=.
```

If the `.git` mount is later removed, you can convert to normal Git by moving or cloning from `.map-git`, or by creating a fresh `.git` repository and committing the current working tree.

## Suggested Agent Rule

Agents should use `MAP_System/scripts/map-git` in this workspace unless normal `git status` starts working.
