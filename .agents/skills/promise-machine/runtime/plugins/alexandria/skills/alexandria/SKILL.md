---
name: alexandria
description: >
  Preserve heterogeneous lending-protocol captures by digest and expose a
  narrow, source-bound credit view for Tabularium and Probitas. Use when the
  user names Alexandria or asks to archive lending data for reproducible,
  address-scoped credit research. Raw release and registered Goldfinch and
  Clearpool derivation, disposable indexing, address queries and a checked-in
  offline demonstration, unsigned in-toto release statements and a bounded
  Compound v3 Phase 0 method proof are available.
metadata:
  version: "0.3.0"
---

<p align="center">
  <img src="../../assets/characters/alexandria.png" width="1200">
</p>

# Alexandria

## Frontier

Alexandria owns its own preservation and credit-view frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Alexandria preserves heterogeneous lending captures byte for byte, then exposes only the source-bound credit view a reviewed mapping can defend.

**Current frontier.** Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
<!-- marketplace-context:end -->

Alexandria is the archive and catalogue behind durable lending-protocol
research. Raw captures remain unchanged. Tabularium owns their interpretation
as venue-qualified credit events, and Probitas may consume those events in a
dossier. Ariadne may bind a finished release to its evidence. Lazarus is the
neighbouring specialist for the finite historical Ethereum state and exact RPC
traffic one application test needs; it does not replace Alexandria's dataset
boundary.

`$SKILL_DIR` is the directory holding this file. The command lives at
`$SKILL_DIR/../../scripts/alexandria.py`; resolve it from where you loaded this
skill.

## Day to day

**Research.** A protocol endpoint or hosted indexer may disappear. Preserve
the exact response, its capture scope and its gaps before the only cheap copy
is gone.

**Credit.** A counterparty record needs events, position observations and an
account of the venues and intervals checked. An empty result without coverage
is not a clean history.

**Data engineering.** Raw GraphQL responses, chain logs and replay fixtures
do not need one payload schema. Bind their bytes in one manifest, then build a
small, versioned credit view that points back to them.

## Raw releases

Prepare a capture plan using the contracts under
`$SKILL_DIR/../../schemas/`. Every component path is relative to the plan's
directory. Every component has a `public`, `restricted` or `private` access
class and a `permitted`, `restricted`, `prohibited` or `unknown` redistribution
class. Give every capture a venue, an `eip155` chain, a non-secret source
reference, an evidence and finality class, a full-dataset or subject-scoped
boundary and counted coverage or a stated gap. Then ingest it:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" ingest \
  --plan capture-plan.json --output release
```

Ingest reads only the plan and its confined local source files. It copies raw
bytes unchanged into digest-derived paths, writes through a temporary sibling
directory and installs the release atomically. It refuses absolute paths,
traversal, symlinks and replacement of a different release. Record the
`sha256:...` release ID printed on success.

Verify before using or moving a release:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" verify release
```

Verification is offline and read-only. It checks canonical manifest bytes,
release identity, object paths, byte counts, digests, component access and
redistribution classes, capture source, scope, evidence and finality classes,
collection counts, declared gaps, correction links and exact release-tree
membership. It does not establish publisher identity, source completeness or
chain finality.

Emit a deterministic statement only after verification:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" statement release \
  --output release-statement.json
```

The output must be outside and must not alias the release. The command emits a
canonical unsigned in-toto Statement v1 with one logical release subject, one
subject per manifest component, exact component metadata, and every capture's
declared scope, coverage status and counts, unsupported collections and gaps.
It includes one passed Alexandria offline-verification claim bound to the
release digest and an empty command list.
Canonical statement bytes above Ariadne's default 8 MiB bounded-input limit are
refused before the output path is prepared. A successful output therefore stays
inside Ariadne's default reader bound.

The statement is not a DSSE envelope and Alexandria does not run cosign. It
does not authenticate a publisher or prove provider completeness, consensus
finality or canonical-chain membership. Ariadne can inspect the statement and
run its core gates, but this predicate is unregistered, signatures remain
unchecked, and gates 2 and 5 remain unchecked.

Derive the narrow Tabularium view into a new release:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" derive raw-release \
  --output derived-release
python3 "$SKILL_DIR/../../scripts/alexandria.py" verify derived-release
```

Derivation first verifies the input and never changes it. Registered
Goldfinch and Clearpool mappings emit deterministic credit events and, where
the source supplies position state, observations. Every row names the raw
release, component digest, source and context selectors, mapping rule, adapter
version and evidence class. Verification resolves those selectors, reruns the
mappings and reconciles row, family, subject and coverage counts. Capture
renames do not change row IDs, and repayment legs remain neutral source
amounts unless the native record supplies a principal and interest split.
Derivation stops above 100,000 rows or 64 MiB for either JSONL file.

Rebuild the disposable address index and query it:

```bash
python3 "$SKILL_DIR/../../scripts/alexandria.py" index derived-release \
  --output alexandria.sqlite
python3 "$SKILL_DIR/../../scripts/alexandria.py" query \
  --index alexandria.sqlite --address 0x...
```

Indexing verifies every derived release, refuses to write inside one and
retains the derived release, raw release, component, capture and row
identities. Querying opens SQLite read-only, checks its exact schema and
logical digest, then matches every indexed partition to its release. Equivalent
rows shared by cumulative releases appear once. Conflicting content under one
row ID is refused.

A zero-row result is empty only when complete capture scope covers every
requested address, venue, chain and time boundary and the mapping has no
unsupported source records.

Probitas can consume that evidence only when the operator passes its explicit
`--alexandria-index` option. The translation retains the original venue and
evidence class, combines per-chain coverage conservatively and keeps registry
venues absent from the archive visible as gaps. It does not infer people,
defaults, full repayment or a current balance.

To exercise the whole path without a network, run the fixed demonstration from
the repository root:

```bash
output="$(mktemp -d)/credit-history-v0"
python3 plugins/alexandria/examples/credit-history-v0/demo.py build --output "$output"
python3 plugins/alexandria/examples/credit-history-v0/demo.py verify "$output"
```

The plan pins existing Goldfinch and Clearpool files by digest. The result is a
reproducibility fixture, not a production corpus. Its Goldfinch source remains
provider-reported and its Clearpool source remains subject-scoped with unknown
finality.

## Compound v3 Phase 0

The [Compound method-proof example](../../examples/compound-v3-phase0-v0/README.md)
pins all 28 production Comet deployments at one upstream commit and preserves
two Ethereum USDC transactions. Its checker binds old-state access, nested
calls, the proxy implementation and code, transaction-start storage, ordered
storage writes and a provider-reported finalized boundary.

Generate the fixed registry from a local pinned checkout, or build and check a
captured source tree offline:

```bash
python3 "$SKILL_DIR/../../scripts/compound_v3_phase0.py" registry \
  --comet-repository <comet-checkout> --output registry.json
python3 "$SKILL_DIR/../../scripts/compound_v3_phase0.py" build \
  --input <captured-input> --output <release>
python3 "$SKILL_DIR/../../scripts/compound_v3_phase0.py" check <release>
```

The separate `capture` subcommand is networked. It requires
`ALEXANDRIA_COMPOUND_RPC_URL`, omits the endpoint and headers from the release,
and collects only the fixed corpus. Do not describe the result as an interval
history, chain proof or independent finality check.

The [Compound v3 harvest specification](../../docs/compound-v3-harvest.md)
describes the resumable, reconciled production collector that remains to be
built. Tabularium owns the separate canonical mapping.

Read the [study](../../docs/study.md) for the selected construction and the
[runbook](../../docs/runbook.md) for the implementation boundaries.

## Settled boundary

1. Raw objects retain their exact bytes and native shapes.
2. Release manifests bind components to capture scope and coverage.
3. Tabularium mappings own the meaning of derived credit events and position
   observations.
4. SQLite is a disposable address index, not release evidence.
5. Probitas retains the original venue on every archive-backed record and
   keeps unharvested venue coverage visible.
6. Lazarus fixtures may support selected observations but are not a universal
   archive payload.

A digest can establish that bytes match a manifest. It does not establish who
published them, that an indexer captured a complete chain history, or that a
reported block is canonical. Those claims require separate evidence.

## Promise Machine contract

### alexandria-raw-release

- Promise: A successful `ingest` followed by `verify` preserves the named local source bytes and binds them to the canonical manifest, release identity, declared capture boundary, coverage and gaps.
- Evidence: The capture plan, copied objects, canonical manifest, printed release id and a passing `alexandria.py verify` result for the same release directory.
- Evidence classes: recorded, checked, recomputed
- Boundary: The result does not establish publisher identity, source completeness, chain finality or any fact outside the declared capture scope.
- Authorises: Retention or hand-off of the verified raw release as a bounded preservation artefact.
- Consequence: 2
- Refuses: Installing, moving or describing a release as verified when a source path, digest, byte count, scope, coverage declaration or tree-membership check is absent or fails.
- Recovery: Inspect the named verification failure, repair the plan or source set, ingest into a new output directory and rerun verification.
- Exceptions: none

### alexandria-derived-view

- Promise: A successful `derive` followed by `verify` reproduces every emitted credit event and observation from a verified raw release under the named registered mapping and reconciles its selectors and counts.
- Evidence: The verified raw release, adapter and mapping versions, derived JSONL, coverage records and a passing verification that reruns the mapping.
- Evidence classes: recorded, checked, recomputed
- Boundary: The view preserves venue and evidence classes; it does not infer default, full repayment, current balance, source completeness or universal event meaning.
- Authorises: Use of the verified derived release as bounded input to Tabularium or an explicitly archive-backed Probitas collection.
- Consequence: 2
- Refuses: Using rows whose source selectors do not resolve, whose counts conflict, whose mapping is unknown or whose raw release did not verify.
- Recovery: Inspect the failed selector, mapping or count, correct the adapter or source release without changing published evidence, derive a new release and verify it.
- Exceptions: none

### alexandria-release-statement

- Promise: A successful `statement` emits a canonical unsigned in-toto Statement v1 that exactly projects a verified Alexandria release, every component digest and every capture's declared scope, coverage and gaps.
- Evidence: The verified release, canonical statement bytes, exact release and component subject set, Alexandria predicate projection and successful command receipt for the same logical release digest.
- Evidence classes: recorded, checked, recomputed
- Boundary: The output has no DSSE envelope or signature check, the Alexandria predicate is unregistered in Ariadne, and the result does not establish publisher identity, provider completeness, consensus finality or canonical-chain membership.
- Authorises: Hand-off of the unsigned statement bytes for Ariadne core-gate inspection or downstream signing without upgrading their evidence claims.
- Consequence: 1
- Refuses: Emitting from a release that does not verify, emitting bytes above Ariadne's default bounded-input limit, writing inside or through an alias of that release, omitting or changing a subject or predicate field, or describing unchecked signatures or predicate-owned gates as passed.
- Recovery: Inspect the verification, projection or output-confinement failure, repair the release or choose a safe external output, rerun `statement` and retain only the successful replacement.
- Exceptions: none

### alexandria-address-query

- Promise: A successful `index` and `query` returns only rows from verified derived partitions whose identities and logical digest match the disposable index.
- Evidence: The verified derived releases, SQLite schema and logical digest checks, partition identities and the exact query result for the requested address.
- Evidence classes: checked, recomputed
- Boundary: SQLite is not release evidence, and zero rows does not mean a clean history unless complete declared coverage spans every requested address, venue, chain and time boundary with no unsupported records.
- Authorises: Presentation or downstream use of the source-bound query result with its coverage and gaps kept visible.
- Consequence: 1
- Refuses: Querying a mutable or mismatched index, collapsing conflicting rows, or presenting an uncovered zero-row result as absence of activity.
- Recovery: Rebuild the disposable index from verified releases, rerun the query and report any remaining coverage gap instead of a clean result.
- Exceptions: none

### alexandria-compound-method-proof

- Promise: A successful Compound Phase 0 `check` binds the fixed registry and captured transaction witness to the named Comet revision, proxy implementation, code, old-state reads, calls and ordered writes under the implemented method.
- Evidence: The pinned registry, captured input, built release and passing `compound_v3_phase0.py check` result, including the proof-checked state relation and separately labelled provider records.
- Evidence classes: recorded, checked, recomputed, proved: EIP-1186 state relation
- Boundary: The result covers the fixed corpus and implemented method only; it is not an interval history, independent canonical-chain proof, canonical Tabularium mapping or proof of receipts, logs or traces.
- Authorises: Use of the checked Phase 0 witness as bounded method evidence for the named transactions.
- Consequence: 1
- Refuses: Generalising the witness to another deployment, transaction, interval, implementation, layout or evidence class.
- Recovery: Inspect the named registry, implementation, state, call, write or selector mismatch, recapture under an amended fixed plan and rerun the check.
- Exceptions: none
