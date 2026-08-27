# Evidence bundle: wildcat-app-v2

One recorded scan against one named tree. The remote moves, so this is a
capture, not a gate: the numbers below are machine-checked against the
committed boundary document beside this file, never re-derived from the
network.

## The capture

- Repository: `wildcat-finance/wildcat-app-v2`
- Commit: `9b8b6d5d6db06428c5b539f267623277b65315cd`
- Captured: 2026-08-18, from a fresh shallow clone
- Tool: `horos-v0.1.0`, `scan --json`, unmodified
- Boundary document: [wildcat-app-v2.boundary.json](./wildcat-app-v2.boundary.json)

## The totals

The tree held 17,053,779 bytes outside `.git`. The scan walked 1,041 files,
skipped none as unreadable, and classified 13,696,504 bytes as token sinks:
**80.3% of readable bytes**, through 16 evidence-bearing entries. The first
Horos study asked for at least 60% on this tree; the live capture gives
80.3%, and no hand-written TypeScript or TSX file under `src/` was excluded.

| Category | Bytes | What it caught |
| --- | --- | --- |
| generated | 7,567,189 | the checked-in Storybook build (7,567,063 by directory name) and a marker-bearing migration lockfile |
| binary | 2,598,609 | nine image assets and a favicon, each by null byte |
| lockfile | 1,895,425 | `package-lock.json` by name |
| blob | 1,635,281 | the single-line legal-entity dataset (1,448,802), a single-line jurisdictions file (20,102), and a minified-geometry MLA document (166,377) |

Every entry quotes the evidence that earned it; the sixteen are listed in
the boundary document verbatim.

## What stayed readable, honestly

Fail-open classification keeps anything unevidenced readable, and two
families a person would call sinks stayed readable here: 97 SVG text assets
(204,371 bytes) outside the Storybook build, and 17 machine-emitted prisma
migration SQL files (298,878 bytes) carrying no generation marker. Together
they are 503,249 bytes, about 15% of what remains readable after the scan.
They are the evidence behind the ledger's next held job.

## Machine-readable capture lines

The consistency test parses these and asserts each against the committed
boundary document, so this prose cannot drift from the evidence.

<!-- evidence:commit 9b8b6d5d6db06428c5b539f267623277b65315cd -->
<!-- evidence:total_bytes 17053779 -->
<!-- evidence:classified_bytes 13696504 -->
<!-- evidence:entries 16 -->
<!-- evidence:files_walked 1041 -->
<!-- evidence:files_skipped_unreadable 0 -->
<!-- evidence:bytes_generated 7567189 -->
<!-- evidence:bytes_binary 2598609 -->
<!-- evidence:bytes_lockfile 1895425 -->
<!-- evidence:bytes_blob 1635281 -->
