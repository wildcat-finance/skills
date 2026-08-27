# Evidence bundle: wildcat-app-v2, second capture

The same tree as [the first capture](./wildcat-app-v2.md), rescanned after
the text-asset and migration-SQL rules landed. The first capture is
immutable evidence behind the `horos-v1.1.0` ledger row; this one records
what the two new rules changed, and nothing else changed.

## The capture

- Repository: `wildcat-finance/wildcat-app-v2`
- Commit: `9b8b6d5d6db06428c5b539f267623277b65315cd`, identical to the first
  capture; the clone was not touched between the two
- Captured: 2026-08-18
- Tool: `horos` with the two rule classes of this run, released as
  `horos-v2.1.0`
- Boundary document: [wildcat-app-v2-rules.boundary.json](./wildcat-app-v2-rules.boundary.json)

## The totals

Classified bytes rose from 13,696,504 to 14,199,753 of 17,053,779: **83.3%
of readable bytes**, up from 80.3%. Entries rose from 16 to 130. The delta
is exactly the two rule families and nothing else: 97 SVG text assets
(204,371 bytes, every SVG outside the Storybook build) and 17 migration SQL
files (298,878 bytes). No entry from the first capture moved or vanished,
and no hand-written TypeScript or TSX joined the boundary.

| Category | Bytes | Change from the first capture |
| --- | --- | --- |
| generated | 7,866,067 | up 298,878: the migration SQL |
| binary | 2,598,609 | unchanged |
| lockfile | 1,895,425 | unchanged |
| blob | 1,635,281 | unchanged |
| asset | 204,371 | new category: the 97 SVGs |

## What still stays readable

About 2.85 MB, all of it unevidenced by the current rules: hand-written
source, configuration, prose, and the machine-regular-but-hand-committed
files (the MUI theme, GraphQL query strings) the fail-open contract leaves
alone.

## Machine-readable capture lines

The consistency test parses these against the committed boundary document,
as it does for the first capture.

<!-- evidence2:commit 9b8b6d5d6db06428c5b539f267623277b65315cd -->
<!-- evidence2:total_bytes 17053779 -->
<!-- evidence2:classified_bytes 14199753 -->
<!-- evidence2:entries 130 -->
<!-- evidence2:files_walked 1041 -->
<!-- evidence2:files_skipped_unreadable 0 -->
<!-- evidence2:bytes_generated 7866067 -->
<!-- evidence2:bytes_binary 2598609 -->
<!-- evidence2:bytes_lockfile 1895425 -->
<!-- evidence2:bytes_blob 1635281 -->
<!-- evidence2:bytes_asset 204371 -->
