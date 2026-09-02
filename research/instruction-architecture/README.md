# instruction architecture workbench

this directory is a research boundary, not a production loader. agent-facing
Markdown and immutable structured references at
`a2b634d8e039af988bf30c8316defccf70071d8d` remain authoritative. the Step 1
commands inventory that source, prove agent/prompt and mandatory-executable
loader edges, preserve reference-only authority without invented reachability,
classify every physical byte and seal disjoint development and holdout cohorts.

## commands

generate the baseline:

```text
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py build-baseline
```

verify it without rewriting anything:

```text
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py verify-profiles --profiles tests/fixtures/instruction-architecture/invocation-profiles.json
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py verify-corpus --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py verify-loader --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py verify-partition --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py verify-seal --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
```

## source and publication boundary

every accepted JSON record is canonical UTF-8 with an object root and closed
fields; duplicate keys, non-finite numbers, depth above 64, more than 1,000,000
structural tokens, numbers above 640 characters and files above 8 MiB refuse.
source reads are descriptor-relative, no-follow, single-link regular-file
reads with identity rechecks and a 2 MiB per-file cap. repository paths are
canonical printable-ASCII POSIX relatives no longer than 1,024 bytes, and the
frozen tree admits at most 10,000 paths. Markdown preflights cap a source at 2
MiB, physical lines and line length at 16,384, and link openers, fence events
and list depth at 4,096 before expansion.

the fixed Git object is the source authority. only its exact typed
`missing` response in an independently shallow repository enables the checkout
fallback. those checkout bytes must match the sizes, source and span digests
bound by inventory SHA-256
`7e8566c5e9148ca151323636f51d7d69d7ff0215fb937619eefd4b621fc5bcb9`.
a probe failure, ambiguous output, non-shallow absence or coherent replacement
refuses. Git runs from a closed set of absolute system-owned paths with lazy
fetch, replacement objects, global and system configuration, prompts and the
ambient environment disabled. stdin is capped at 4 KiB, stdout at 4 MiB,
stderr at 64 KiB and each process at 20 seconds.

the supplemental parent-classification test resolves one immutable commit,
loads its test and benchmark blobs from that object and checks all 13 live
study, runbook, schema and fixture dependencies against their raw Git blob
identities under an 8 MiB per-file cap. index flags, stat caches, attributes
and clean filters cannot stand in for byte equality. this is test evidence,
not a second source authority or a production loader.

writes use a same-directory single-link temporary file, `fsync`, atomic
replacement, parent-directory `fsync` and a complete identity-bound reread.
the six JSON records and reconciliation publish before
`artifact-inventory.json`; that eighth output is the logical generation commit.
every verifier checks the inventory's seven payload identities, rereads the
unchanged inventory and consumes only cached checked bytes. interruption,
replacement or concurrent publication therefore refuses instead of accepting
a mixed generation.

## corpus and loader graph

the corpus contains 191 physical files and 2,290,450 bytes, or 174 files and
1,819,006 bytes after exact whole-file deduplication. the partition contains
1,473,235 governed-operative, 345,771 exact-literal-or-evidence and 471,444
generated-duplicate bytes; human-only and unsupported are both zero.

the source-owned ledger expands 519 bounded invocation profiles across all 31
selectable canonical skills. each profile has two repository roots, two
isolated Agent Skills roots and one standalone-plugin root: 1,038 + 1,038 +
519 = 2,595 scenarios. the graph has 19 host roots, 332 host edges, 337
scenario edges and 12 reference-only records. the paired checkout roots
distinguish absent and GitHub-contributor credentials; standalone has no suite
credential lookup.
each closure starts at its actual route, binds one profile, and must equal the
profile's full required-document union plus the route contract. source spans,
worker bundles, fixed inputs and mutually exclusive branch products are
validated independently of graph construction. all 5,084 required-document
obligations carry their own path, byte span and digests, and a test-owned
oracle reconstructs the full profile and route grammar without calling the
production builder or validator. six schemas and six human-reference Markdown
files have zero production reachability. X-Ray and Solidity Auditor's local
`VERSION` files and the suite `.python-version` pin are fixed agent inputs,
never executed structured data. the pin is present in exactly 11 source-bounded
profiles and their 55 route-and-credential variants.

## holdout

development contains 143 paths and 1,455,202 exact-unique bytes. holdout
metadata names 31 paths and 363,804 bytes with commitment
`44b7226513c393c14386faaa8ef1994c5bd5028530cd0e302ea8481b46edee35`.
the seal names membership and case-slot classes, but contains no task, answer,
scorer key or model output. do not add those fields before the frozen
experiment opens the envelope. this workbench supplies evidence for the later
raw Markdown, WAI1, Noema, simple-control and new-candidate comparison; it does
not choose or integrate an architecture.
