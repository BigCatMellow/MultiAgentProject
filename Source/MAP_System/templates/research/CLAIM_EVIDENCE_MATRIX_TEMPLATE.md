# Claim Evidence Matrix

Matrix ID: CLAIM-MATRIX-0001
Related brief: BRIEF-0001
Owner: <agent-name>
Date: <YYYY-MM-DD>
Status: OPEN

One row per claim. Each claim must be independently checkable — do not
bundle multiple assertions into one row.

## Claims

| # | Claim | Source(s) | Locator | Source rating | Confidence | Notes |
|---|---|---|---|---|---|---|
| 1 | <single checkable assertion> | <source name from Source Map> | <URL/file/section/line> | PRIMARY/SECONDARY/COMMUNITY/UNVERIFIED/STALE | HIGH/MEDIUM/LOW | <contradiction, caveat, or blank> |
| 2 | | | | | | |

Confidence guide:

- `HIGH` — PRIMARY source, no contradiction, not date-sensitive or recently
  verified.
- `MEDIUM` — SECONDARY source, or PRIMARY but date-sensitive and aging.
- `LOW` — COMMUNITY/UNVERIFIED source, or unresolved contradiction.

## Unsourced claims used downstream

<Anything used in the Research Summary without a row above must instead go
in the Assumption Register — do not leave orphaned claims here.>

## Notes

-
