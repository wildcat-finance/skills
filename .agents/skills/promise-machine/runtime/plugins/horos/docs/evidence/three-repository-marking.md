# Evidence bundle: the three-repository marking

The reopened frontier's last job: Horos stopped being a tool that could
mark repositories and became the tool that has marked them. Each of the
three home repositories now carries a graded boundary, a candidates
report, a census and the adoption stanza, scanned under the git-tracked
universe with the refined classifier, on 2026-08-18.

## The skills repository

- Marked in place on this run's own branch; the boundary lives at
  [.horos/boundary.json](../../../../.horos/boundary.json) and the stanza
  in `AGENTS.md`
- 15 hard entries binding 114,151 bytes, 35 candidates; `check .`
  verifies clean from the root. The count includes this bundle's own
  marking copies, which quote generation markers and therefore classify as
  sinks themselves; check caught that drift during the close, exactly as
  designed.

## wildcat-finance/v2-protocol

- Commit `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, marked through
  [v2-protocol#134](https://github.com/wildcat-finance/v2-protocol/pull/134)
- Boundary copy: [v2-protocol.boundary.json](./v2-protocol.boundary.json)
- 2 hard entries binding 9,885,998 bytes (88.6% of the tree), zero
  candidates remaining. The refined grades initially left the 9.7 MB of
  solc output in `deployments/` as 38 geometry-only candidates; the pull
  request carries the one-line `.gitattributes` promotion
  (`deployments/** linguist-generated`) the candidates report exists to
  propose, converting them to hard attribute evidence under review.

## wildcat-finance/wildcat-app-v2

- Commit `9b8b6d5d6db06428c5b539f267623277b65315cd`, marked through
  [wildcat-app-v2#360](https://github.com/wildcat-finance/wildcat-app-v2/pull/360)
- Boundary copy: [wildcat-app-v2.boundary.v2.json](./wildcat-app-v2.boundary.v2.json)
- 13 hard entries binding 13,407,224 bytes (78.6% of the tree), 117
  advisory candidates (the SVG family, null-byte binaries without
  signatures, and small blobs). The pull request promotes the single-line
  legal-entity dataset to hard attribute evidence the same way. Against
  the schema-1 capture of the same commit, the hard set now carries its
  grades, its universe and its corroborations on every entry.

Both product pull requests await their repositories' own review gates;
this run does not merge past them, and maturity does not pretend they
merged.

## Machine-readable capture lines

The consistency test parses these against the committed boundary copies
and the repository's own boundary.

<!-- marking:skills_entries 15 -->
<!-- marking:skills_hard_bytes 114151 -->
<!-- marking:v2p_commit c7be4039f8f383a9dda4e45f63331c17d63f9ed9 -->
<!-- marking:v2p_entries 2 -->
<!-- marking:v2p_hard_bytes 9885998 -->
<!-- marking:app_commit 9b8b6d5d6db06428c5b539f267623277b65315cd -->
<!-- marking:app_entries 13 -->
<!-- marking:app_hard_bytes 13407224 -->
