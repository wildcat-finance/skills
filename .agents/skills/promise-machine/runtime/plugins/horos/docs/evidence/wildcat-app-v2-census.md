# Evidence bundle: two recorded censuses

The census exists to answer two questions from a record instead of a guess:
is a tree worth walking, and which extractor is worth building next. This
bundle records the first two answers, one per Wildcat repository, captured
2026-08-18 with the census as shipped in this delivery.

## wildcat-app-v2

- Commit: `9b8b6d5d6db06428c5b539f267623277b65315cd`
- Census: [wildcat-app-v2-census.json](./wildcat-app-v2-census.json)
- 1,113 files (aggregated directories included), 17,053,779 bytes across 23 filetypes

The readable weight after the boundary is almost entirely the two mapped
languages: `.tsx` (1,779,083 bytes, none in the boundary) and `.ts`
(916,197 bytes, none in the boundary). The largest readable filetypes the
map verb cannot open are small: `.json` outside the boundary is 88,864
bytes, `.md` 27,545, `.mjs` 12,156, `.prisma` 10,926. **No third extractor
is justified by this tree.**

## v2-protocol

- Commit: `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`
- Census: [v2-protocol-census.json](./v2-protocol-census.json)
- 236 files (aggregated directories included), 11,158,346 bytes across 10 filetypes

The boundary already holds 87.0% of the tree (the deployments JSON and the
lockfile). Of what remains readable, `.sol` is 1,162,544 bytes across 151
files, 87.6% of the readable weight, and the map verb cannot open any of
it. **The census makes Solidity the leading extractor candidate.** One
tree does not earn a build: the maintainer's direction is to census more
protocol and UI repositories first, and the marketplace already holds
prior art for whenever the evidence accumulates (Lemma's Solidity chunker
walks the same comment-and-string discipline the TypeScript lexer uses).

## Machine-readable capture lines

The consistency test parses these against the committed census documents.

<!-- census1:commit 9b8b6d5d6db06428c5b539f267623277b65315cd -->
<!-- census1:total_files 1113 -->
<!-- census1:total_bytes 17053779 -->
<!-- census1:tsx_bytes 1779083 -->
<!-- census1:tsx_boundary_bytes 0 -->
<!-- census2:commit c7be4039f8f383a9dda4e45f63331c17d63f9ed9 -->
<!-- census2:total_files 236 -->
<!-- census2:total_bytes 11158346 -->
<!-- census2:sol_bytes 1162544 -->
<!-- census2:sol_boundary_bytes 0 -->
