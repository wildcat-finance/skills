# Evidence bundle: the TypeScript marking on its default branch

The three-repository marking left wildcat-app-v2 with an open pull
request and said so. This bundle records where that pull request went,
what the default branch carries now, and what `horos check` says about
it under the classifier as it ships today. Captured 2026-09-08 against
`horos-v12.3.3`.

## Where the marking landed

[wildcat-app-v2#360](https://github.com/wildcat-finance/wildcat-app-v2/pull/360)
merged into `develop` on 2026-08-19 as
`b15b9e459648ba9be92f90e61eecdbda9875e3fc`, carrying `.gitattributes`,
the three `.horos` artefacts and the AGENTS.md stanza. It reached the
default branch `main` on 2026-08-20 inside
`01191ed39f06b4445f79fd00ab470fcc70d2d8e8`, an aggregation of `develop`.
Nothing was merged again to establish this; the two commits were read
back from the repository.

At `main` today, `564a189bb9cdc9394b3fd4f444531a261ada99b3`:

- [.horos/boundary.json](./wildcat-app-v2.boundary.main.json): schema 2,
  tracked universe, 13 hard entries binding 13,407,206 bytes
- `.horos/candidates.json`: schema 2, 117 advisory candidates
- `.horos/census.json`: 1,123 files, 17,089,542 bytes across 23 filetypes
- `AGENTS.md`: the adoption stanza, byte for byte the text `scan --write`
  prints today

The boundary committed on `main` is not the copy this repository froze at
marking time. [wildcat-app-v2.boundary.v2.json](./wildcat-app-v2.boundary.v2.json)
records the scan of `9b8b6d5d6db06428c5b539f267623277b65315cd` at 1,041
files walked; the pull request was regenerated against a later `develop`
before it merged, so `main` carries 1,051 and a lockfile 18 bytes larger.
Both are the same 13 entries.

## What the check says

`horos check .` under `horos-v12.3.3`, each commit read at a clean tree:

| Commit | Drifted paths | Exit |
| --- | --- | --- |
| `b15b9e45` merge of #360 | 1 | 1 |
| `01191ed3` aggregation to `main` | 2 | 1 |
| `564a189b` `main` today | 2 | 1 |

Two causes, and only two:

1. `prisma/migrations/migration_lock.toml` carries the evidence string
   `marker 'do not edit' in the first 4096 bytes`. Since `horos-v10.3.3`
   a marker binds only on a comment-led line, so the classifier now
   writes `marker 'do not edit' on a comment-led line in the first 4096
   bytes` for the same file. The entry is otherwise identical. This is
   the classifier moving, not the tree.
2. `counts.files_walked` reads 1,051 against a rescan's 1,053. Two
   tracked files arrived after the boundary was written. This is the tree
   moving, and it is the drift the gate exists to name.

At the merge commit the first cause is the whole difference: `counts` and
every entry matched. The marking was current for the tree it described on
the day it landed.

The rescan is committed beside the boundary as
[wildcat-app-v2.boundary.main-rescan.json](./wildcat-app-v2.boundary.main-rescan.json),
so the two causes are checkable here rather than only reproducible there.

## The gate that is not there

`main` runs `commitlint.yml`, `release-please.yml` and `vercel-purge.yml`.
None of them calls `horos check`, so nothing in that repository notices
either drift. A boundary an agent consults without checking is only worth
what its last regeneration was worth.

The workflow that closes it is in
[the CI recipe](../adoption/ci.md), which was run against
`564a189b` with the artefacts regenerated: `boundary matches the tree`,
exit 0. It is not committed in wildcat-app-v2, and this run opened no
pull request there.

## Stale-boundary rejection

The gate was made to fail on purpose, twice, at `564a189b` with the
boundary freshly regenerated and green:

- a new tracked file carrying a generation marker: exit 1, two drifted
  paths, `src/__horos_stale_demo.ts: evidenced by the tree but missing
  from the boundary` beside the `counts` move from 1,054 to 1,055
- one byte changed by hand in a committed entry: exit 1, one drifted
  path, `package-lock.json: entry changed`

Both restore to exit 0 by regenerating. Neither can be silenced by
editing the boundary, because the boundary is the thing being compared.

## What this does not establish

That the gate runs in wildcat-app-v2. No workflow was committed there, no
CI run exists on any of the three commits, and the issue's default-branch
condition is unmet. The check results above were produced locally against
clean checkouts of the public repository, and they are evidence about
those exact trees under that exact classifier version, not about a run
GitHub performed.

## Machine-readable capture lines

The consistency test parses these against the two committed boundary
documents.

<!-- cigate:commit 564a189bb9cdc9394b3fd4f444531a261ada99b3 -->
<!-- cigate:merge_commit b15b9e459648ba9be92f90e61eecdbda9875e3fc -->
<!-- cigate:aggregation_commit 01191ed39f06b4445f79fd00ab470fcc70d2d8e8 -->
<!-- cigate:entries 13 -->
<!-- cigate:hard_bytes 13407206 -->
<!-- cigate:committed_files_walked 1051 -->
<!-- cigate:rescan_files_walked 1053 -->
<!-- cigate:drifted_paths 2 -->
<!-- cigate:candidates 117 -->
