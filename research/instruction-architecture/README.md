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

build the closed development cases, five immutable arm controls and their
deterministic evidence, then replay without writing:

```text
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py build-development --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --output tests/fixtures/instruction-architecture/evidence/development
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py replay --cohort development --evidence tests/fixtures/instruction-architecture/evidence/development
```

refresh the immutable WAI1 and Noema control snapshot only from a checkout that
contains all three pinned commits:

```text
uv run --no-project --python "$(cat .python-version)" python research/instruction-architecture/benchmark.py snapshot-controls
```

## neutral development contract

all five arms receive the same ten source-bound development cases for order,
scope, negation, exception, literal, alias, unknown, refusal, recovery and
authority. the task and representation enter the prompt; the source-span
expectation, scorer state, candidate id and competing labels do not. exact
canonical source bytes define authority and deterministic exact-source
recovery. raw fallback can preserve that recovery but is not a native mapping;
semantic and behavioural success belong to the later model experiment.
the ten verified scenario closures contain 64 canonical paths and 938,614
exact-unique bytes (51.6004% of the corpus), 16 logical skills, every observed
construct, document class, authority tier and size decile, and all five shared
suite/router contracts. none of their 68 physical paths belongs to the sealed
holdout.

raw covers all 191 physical files and 2,290,450 bytes. WAI1 invokes the merged
checker over its exact three reviewed envelopes: 11,170 current native bytes,
with 2,279,280 bytes in 194 fallback ranges. every WAI1 prompt that uses a
compact carries the one bound decoder bootstrap. its seven fallback cases
recover their exact target source bytes; its three native cases retain valid
reviewed model mappings and codec round trips but do not carry the target prose,
so they record exact source unavailable rather than inventing recovery. that is
not a semantic or behavioural failure. Noema binds 140 immutable product and
review artifacts. three of its four source identities are stale; the exact
Sapheneia binding contributes 10 full-corpus native ranges and 655 bytes. a
native Noema prompt carries the product's kernel, alias dictionary and operation
slice as one immutable first-use bundle. that source is in the sealed holdout,
so Noema has zero native development-case mappings. its historical 40-span,
3,173-byte synthetic mechanism result is reported separately and never enters
current coverage or later behavioural success.

the simple control has 174 exact whole-file content nodes and 17 duplicate
aliases, with no section or permission semantics. the distinct section graph
has 1,471 canonical Markdown nodes, source-owned authority tiers, explicit
parent dependencies and 17 exact-content aliases; its 1,896 physical coverage
ranges preserve 2,071,863 Markdown bytes natively and keep all 15 non-Markdown
inputs and 218,587 bytes as raw fallback. conservative selection includes all
sections of each loader-reachable canonical file plus transitive parents, so
its source content equals the simple arm and its component metadata is overhead,
not a compression claim. every claimed source projection round-trips.

`evidence/development/artifact-inventory.json` is the publication point for 15
payloads across controls, cases, hostile specimens, hostile execution and
evidence. all 12 hostile specimens execute against all five arms and retain 60
content-addressed refusal rows. resource evidence binds both Python sources the
workbench executes, derives their union of standard-library imports from the
AST, refuses any external Python import and records bounded Git as its one
out-of-process runtime dependency. the workbench-source digest zeroes only the
inventory-digest literal to avoid a cryptographic self-reference; its enclosing
commit binds the literal itself. it reconciles 13,803,445 payload bytes plus the
2,409-byte inventory to the complete 13,805,854-byte generated publication. the
separate control snapshot publishes a 67,069-byte manifest and 2,095,430 unique
object bytes. command results emit the observed wall times and peak RSS, while
Step 3 owns repeated p50/p95 samples. replay checks the inventory twice,
rebuilds from the frozen source and checked control snapshot, and requires every
payload byte to match. the
holdout stays unopened and no holdout task, answer or model output is accessed.

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

WAI1 and Noema use a distinct content-addressed control snapshot inside the
Step-2 fixture boundary. its frozen manifest maps all 172 admitted
commit-and-path identities to 157 unique objects and binds each object by byte
length, SHA-256 and its Git blob id. the snapshot root must contain only
`manifest.json` and `objects`, and the object directory must contain exactly
those 157 names before and after verification. refresh refuses an unowned root
or object entry before its first write, then rereads and identity-checks the
closed publication without deleting anything. when a pinned commit exists,
replay also requires its complete admitted path inventory, every `commit:path` blob id and
every Git blob byte to equal the snapshot. snapshot-only use is admitted solely
when that exact commit is absent and Git reports the repository as shallow.
missing commits in a complete repository, ambiguous probes, path or inventory
drift, malformed manifests, and object size, digest or blob-id drift refuse. no
runtime fetch or history expansion is attempted.

the supplemental parent-classification test resolves one immutable commit and
loads its test and benchmark blobs only from that object's verified blob ids.
for Step-2 harness compatibility it reads the dependency declaration from the
exact parent test, admits live divergence only for those two code paths, and
checks the remaining 12 Step-1 study, runbook, schema and fixture dependencies
against their raw Git blob identities under an 8 MiB per-file cap. a live
dependency-list rebind, index flag, stat cache, attribute or clean filter cannot
stand in for byte equality. this narrows the test harness, not Step-1 authority;
it is test evidence, not a second source authority or a production loader.

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

## Step 3 selection and sealed gates

the current development proxy frontier is `simple` alone. it is a provisional
nominee, not a final architecture: raw/no-change and simple remain valid
winners, WAI1 is excluded from nomination after three exact-source failures,
and behavioural plus native cache evidence can retain a frontier or select
none. detailed results and record placement are in
[`research-report.md`](../../docs/instruction-architecture/research-report.md).

Step 3 freezes two answer-free packets. the behavioural packet contains 224
contiguous five-arm pair blocks: 1,120 repeat-condition/model/case/arm tuples;
one tuple is one atomic credit reservation covering both allowed attempts. the
native packet keeps cache-shaped raw and simple as mandatory baselines and
compares complete logical-context high-water with cumulative fresh-token churn
separately for each runtime, model and tokenizer. cached tokens count in full
for logical context, no cross-tokenizer pooling or dollar weighting is allowed,
and missing native telemetry remains unknown.

```text
uv run --no-project --python "$(cat .python-version)" python3 research/instruction-architecture/benchmark.py aggregate-development --evidence tests/fixtures/instruction-architecture/evidence/development --output tests/fixtures/instruction-architecture/development-selection.json
uv run --no-project --python "$(cat .python-version)" python3 research/instruction-architecture/benchmark.py freeze-experiment --selection tests/fixtures/instruction-architecture/development-selection.json --seal tests/fixtures/instruction-architecture/holdout-seal.json --output tests/fixtures/instruction-architecture/evidence/frozen
uv run --no-project --python "$(cat .python-version)" python3 research/instruction-architecture/benchmark.py freeze-native-gate --selection tests/fixtures/instruction-architecture/development-selection.json --runtime-manifest tests/fixtures/instruction-architecture/native-runtime-manifest.json --output tests/fixtures/instruction-architecture/evidence/frozen/native
uv run --no-project --python "$(cat .python-version)" python3 research/instruction-architecture/benchmark.py verify-native-preregistration --preregistration tests/fixtures/instruction-architecture/native-deployment-preregistration.json --commitment tests/fixtures/instruction-architecture/native-lifecycle-packet-commitment.json --no-session
```

the no-call preflights use public catalog metadata, the official credit balance
endpoint and isolated local authentication probes. they do not dispatch a paid
model request or launch an answer-producing native session. at the frozen
2026-09-03 observation the complete conservative gross bound is
`$4,435.75397516800` under the `$4,500.00` ceiling, and the next two-attempt
tuple reserves `$0.38103308400` against `$57.118449467` proved available credit.
