# instruction architecture workbench

this directory is a research boundary, not a production loader. agent-facing
Markdown and immutable structured references at
`a2b634d8e039af988bf30c8316defccf70071d8d` remain authoritative. the Step 1
commands inventory that source, prove agent/prompt and mandatory-executable
loader edges, preserve reference-only authority without invented reachability,
classify every physical byte and seal disjoint development and holdout cohorts.

generate the baseline:

```text
python3 research/instruction-architecture/benchmark.py build-baseline
```

verify it without rewriting anything:

```text
python3 research/instruction-architecture/benchmark.py verify-profiles --profiles tests/fixtures/instruction-architecture/invocation-profiles.json
python3 research/instruction-architecture/benchmark.py verify-corpus --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
python3 research/instruction-architecture/benchmark.py verify-loader --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
python3 research/instruction-architecture/benchmark.py verify-partition --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
python3 research/instruction-architecture/benchmark.py verify-seal --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
```

every accepted JSON record is canonical UTF-8 with duplicate keys and
non-finite numbers refused. object fields are closed by the validator and the
companion schema. source reads are bounded regular-file reads matched against
the fixed Git blob. when a shallow checkout does not contain that commit, the
reader accepts only checkout bytes whose size, source digest and evidence spans
match the inventory-bound manifest, profile ledger and loader graph. this
fallback is unavailable in a non-shallow repository and does not fetch.
Git runs from a closed set of absolute system-owned paths, with lazy fetch,
global and system configuration, prompts and ambient environment disabled.
writes use a same-directory temporary file, `fsync`, atomic replacement and a
complete reread. the six JSON records and
reconciliation are published before `artifact-inventory.json`; that last write
is the logical generation commit. every verifier checks the inventory's seven
byte identities, rereads the unchanged inventory and consumes only the bytes it
already checked, so interruption or concurrent publication refuses instead of
accepting a mixed generation.

the source-owned ledger expands 519 bounded invocation profiles across all 31
selectable canonical skills. each profile has two repository roots, two
isolated Agent Skills roots and one standalone-plugin root: 1,038 + 1,038 +
519 = 2,595 scenarios. the paired checkout roots distinguish absent and
GitHub-contributor credentials; standalone has no suite credential lookup.
each closure starts at its actual route, binds one profile, and must equal the
profile's full required-document union plus the route contract. source spans,
worker bundles, fixed inputs and mutually exclusive branch products are
validated independently of graph construction. all 5,049 required-document
obligations carry their own path, byte span and digests, and a test-owned
oracle reconstructs the full profile and route grammar without calling the
production builder or validator. six schemas and six human-reference Markdown
files have zero production reachability. X-Ray and Solidity Auditor's local
`VERSION` files are fixed agent inputs, never executed structured data.

the holdout seal names membership and case-slot classes, but contains no task,
answer, scorer key or model output. do not add those fields before the frozen
experiment opens the envelope.
