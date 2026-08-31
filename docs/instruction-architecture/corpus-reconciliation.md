# instruction architecture corpus reconciliation

source: `a2b634d8e039af988bf30c8316defccf70071d8d`

the framework-74 corpus contains 106 physical files and
1,545,537 physical bytes. exact whole-file deduplication leaves
89 files and 1,074,093 bytes. these are
repository denominators, not prompt-size or semantic-compression claims.

## inventory

| class | files |
| --- | ---: |
| canonical skill contracts | 32 |
| runtime contracts | 18 |
| Promise Machine contracts | 18 |
| linked Markdown references | 38 |

the sole exact duplicate family is the root Promise Machine contract and its
17 generated plugin copies. that family accounts for
471,444 bytes removed by exact
deduplication. similar prose is not deduplicated.

## loader evidence

`loader-graph.json` records 19 roots and 105
edges. every edge cites a source path, exact byte range, source digest and span
digest. unconditional runtime loads and conditional selection or reference
loads remain distinct. a file's presence creates no edge. fixtures and
`distribution/skills-runtime/` are outside this corpus.

## byte classes

the partition is gapless over every physical source byte. generated Promise
Machine copies are `generated_duplicate`; fenced command and data blocks are
`exact_literal_or_evidence`; all remaining canonical Markdown stays in the
conservative `governed_operative_semantics` class. no prose is discarded as
human-only and no byte is treated as a saving through uncertainty.

## cohorts

the development cohort holds 27
logical skills and 859,273 exact-unique
bytes (0.799999). the sealed holdout holds
five logical skills and 214,820 exact-unique
bytes (0.200001). memberships are disjoint.
the development set covers every shared root and runtime contract, all ten
file-size deciles and every construct class recorded in `cohorts.json`.

`holdout-seal.json` commits the selection method, seed, membership and 16-slot
case envelope. it contains no prompt, expected answer, scorer key or model
output. later work may open that envelope once; Step 1 does not score it.

## refusal boundary

all four verification commands rebuild from the fixed Git ref and compare the
live source bytes before accepting an artefact. a path, byte, digest, loader
span, partition range, cohort member or commitment that drifts refuses with
the failed predicate. current prompt and scenario-reachable denominators remain
unmeasured until the later arm and case builders exist.
