# Release-Path Smoke Checklist

Status: ACTIVE REVIEW GUIDE (checklist, not a mandatory gate — see PROMO-0005)
Source insight: `emergence/insights/INS-0005-release-reviews-must-inspect-every-user-visible-acquisition-path.md`
Source idea: `emergence/ideas/IDEA-0005-add-a-release-path-smoke-checklist-for-user-facing-packages.md`
Promotion: `emergence/promotions/PROMO-0005-release-path-checklist.md`
Detected by: codex-lab-maki (TASK-059)
Promoted by: claude-lab-rose (TASK-078)
Date: 2026-07-02

## When to use

Run this checklist for any task that publishes something a user acquires and
runs on their own machine: installers, scripts, archives, desktop launchers,
theme packages, release ZIPs, or download links.

Skip it for purely internal artifacts, source-only changes, and read-only
documentation.

## The failure this prevents

DarkMellow (TASK-058/059/061): the installer bug was fixed in the source
tree, reviewed, and released — but the wallpaper bug persisted on the user's
other machine, because the repo root still contained a stale dated ZIP whose
bundled installer had **no wallpaper logic at all**. A user following the most
visible download path got a broken install regardless of the fix. Source-tree
review validated the code; nobody had walked the acquisition path.

> Review what the user downloads, not just what the repo contains.

## Checklist

Walk each item as the user would, ideally against the live remote (GitHub),
not the local working tree:

1. **Enumerate every acquisition path.** Release ZIPs/tarballs, "download"
   buttons, raw-file links in READMEs, desktop files, install one-liners.
   Each path is a separate thing to verify.
2. **Open each archive and inspect what is actually inside it.** Does the
   bundled installer/script match the current fixed version? Stale archives
   that predate a fix are the canonical failure.
3. **Check every README/INSTALL doc against current behavior.** A doc that
   describes an older installer actively misleads users toward the broken
   path (DarkMellow's README.txt contradicted README.md).
4. **Verify all referenced assets exist at the paths the installer uses.**
   Wallpapers, icons, fonts, .desktop Exec targets.
5. **Confirm against the live remote.** `gh api` or a fresh clone — the
   local tree can be ahead of what users can actually reach.
6. **Check post-install verification.** Does the installer tell the user
   whether it worked (or at least fail loudly), or does it exit silently on
   missing schemas/paths?
7. **Retire stale artifacts explicitly.** Old release files should be deleted
   from user-visible locations and preserved under `artifacts/retired/` (or
   equivalent) for audit — not left where a user can grab them.

## Output

Record the walk in the task's release checklist or validation artifact: which
acquisition paths were checked, against which remote/commit, and what was
retired or corrected.

## Gate status

This is a recommended checklist. Making it a required release-gate condition
(enforced by `release_task.py`) changes MAP governance and remains a Human
Owner decision, per the source idea card.
