---
name: tabularium
description: >
  Build or verify a reproducible release of sourced on-chain credit events,
  with venue-native records, mapping provenance and explicit coverage. Use
  when the user names Tabularium, asks to preserve a credit-event record, or
  wants to rebuild or verify a Tabularium release offline. This version maps
  preserved Goldfinch, Euler v1 and Euler V2 credit events and rebuilds a
  non-canonical Compound v3 Phase 0 execution witness. Do not use it to collect
  live data, infer who controls an address, rate a counterparty, authenticate a
  publisher or claim an independently proved chain boundary.
metadata:
  version: "0.3.0"
---

<p align="center">
  <img src="../../assets/characters/tabularium.png" width="1200">
</p>

# Tabularium

## Frontier

Tabularium owns its own credit-event release frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events while keeping the source, mapping, coverage, and gaps beside them.

**Current frontier.** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

Tabularium turns preserved venue records into a common event ledger without
discarding what the venue said or the rule used to interpret it.

Alexandria is the upstream archive and narrow-view provider. Probitas may use a
verified Tabularium release in a counterparty dossier, and Ariadne may bind its
digest to evidence. Those downstream uses do not authorise Tabularium to
collect live data, flatten venue meaning, rate a borrower, or hide unsupported
coverage.

`$SKILL_DIR` is the directory holding this file. The tool lives at
`$SKILL_DIR/../../scripts/tabularium.py`; resolve it from where you loaded this
skill.

## Day to day

**Developers.** A hosted indexer is still answering, but it will not do so for
ever. Preserve the response and its capture boundary now, then build a release
whose bytes another person can reproduce after the endpoint is gone.

**Security and audit.** A dataset arrives with a digest and a claim that it was
built from a named source. `verify` checks the paths, digests, counts, mapping
versions and source selectors, then rebuilds the canonical bytes instead of
trusting the claim.

**Finance.** Borrow and repayment records from different venues need to be
compared without pretending they have identical meanings. Every row keeps its
venue-qualified action and complete native record, so the common family does
not become a verdict about the borrower.

## Start with the checked-in releases

The built prototype ships
[`goldfinch-v0`](../../examples/goldfinch-v0/README.md): unchanged source and
capture bytes, 511 canonical rows, a coverage manifest, a data dictionary and
a temporary rebuild demonstration.

It also ships [`euler-v1-v0`](../../examples/euler-v1-v0/README.md), a
one-block canonical-proxy release, and
[`euler-v2-v0`](../../examples/euler-v2-v0/README.md), a fixed owner/second
activity release from the Euler V3 API. `Euler V2` names the protocol
generation; `Euler V3` names the hosted API. Keep those fields separate.

From the repository root:

```bash
python3 plugins/tabularium/examples/goldfinch-v0/rebuild.py
python3 plugins/tabularium/examples/euler-v1-v0/rebuild.py
python3 plugins/tabularium/examples/euler-v2-v0/rebuild.py
python3 plugins/tabularium/examples/compound-v3-phase0-v0/rebuild.py
```

The demonstration copies the inputs to a fresh temporary directory, builds
there, makes all four release files read-only, verifies them offline and
requires the canonical and coverage bytes to match the committed release. It
does not rewrite the example.

## Build and verify

Keep the four files of any release together and select its adapter explicitly.
Goldfinch remains the default for old commands:

```bash
python3 scripts/tabularium.py build \
  --adapter <goldfinch|euler-v1|euler-v2> \
  --source <release-dir>/source.json \
  --capture-manifest <release-dir>/capture.json \
  --out <release-dir>/events.jsonl \
  --manifest <release-dir>/coverage.json \
  --release <release-id>

python3 scripts/tabularium.py verify <release-dir>/coverage.json
```

`build` checks the capture's source digest, byte count, adapter and declared
scope before it writes anything. Venue validation then checks the preserved
source response. It rejects
duplicate source identifiers, unsafe numeric values, paths outside the release
directory and outputs that alias preserved input.

The Goldfinch adapter maps `borrows` to `goldfinch.borrow` and `repays` to
`goldfinch.repay`. Each row carries the complete native entity, a stable source
selector, the source contract, adapter version and mapping rule. The builder
reports `_meta`, `callableLoans`, `creditLines` and `tranchedPools` as
unsupported rather than treating silence as coverage.

Euler v1 maps canonical proxy Borrow, Repay and Liquidation logs. Euler V2
maps borrow, repay, liquidation, debt socialisation, debt transfer and interest
accrual from the V3 API without flattening those actions. Owner and sub-account
remain separate, liquidation amount legs remain separate, and every row keeps
its complete source record.

`verify` reads only local files and writes nothing. It checks the source,
capture and canonical digests and byte counts; confines every declared path;
checks supported schema, adapter and mapping versions; reconciles the capture
with source metadata; requires one ordered selector per mapped entity; and
rebuilds the expected JSONL from source. Exit 0 means those checks passed.

## Compound v3 Phase 0 witness

This non-canonical path consumes Alexandria's verified checked-in raw release.
It does not write a canonical event or coverage-v2 row:

```bash
python3 scripts/tabularium.py compound-witness \
  --alexandria-release <alexandria-release> \
  --out facts.jsonl --manifest witness.json
python3 scripts/tabularium.py verify-compound-witness \
  --alexandria-release <alexandria-release> \
  --facts facts.jsonl --manifest witness.json
```

The witness binds the Alexandria release and component digests, pinned Comet
commit, proxy implementation and code. It rebuilds ordered successful Comet
calls, relevant proxy-storage writes and one packed signed-principal
transition. Unknown implementations, layouts, call shapes, relevant writes,
source selectors or changed bytes are refused. This proves only the recorded
method for one transaction; Compound canonical mapping and interval coverage
remain Phase 1 work.

## What the result means

A Goldfinch repayment row means the source recorded a repayment amount. It
does not by itself prove that every obligation was paid, the facility closed or
the borrower's whole debt was settled.

The capture boundary is what the named hosted indexer or public RPC reported.
Neither the boundary nor each event is independently proved against Ethereum
here.

The release is unsigned. A passing offline verification establishes internal
consistency among the local files and the implemented mapping. It does not
establish publisher identity or authenticity. Do not turn the result into an
identity claim, counterparty score or chain-proof claim.

## Adding or correcting an interpretation

Read the [adapter guide](../../docs/adding-an-adapter.md) before adding a venue.
A new adapter must validate its source, keep venue meaning qualified, retain
the native record, name its provenance, declare unsupported collections and
ship fixtures that hold the mapping against drift.

Read the [release policy](../../docs/release-policy.md) before correcting a
mapping. Published source, canonical and coverage bytes are immutable. A
changed schema, adapter or mapping rule gets a new version and a new release
directory that names what it supersedes.

The [Euler preservation study](../../docs/euler-preservation-study.md) records
the source and version boundary. Its
[runbook](../../docs/euler-preservation-runbook.md) records the atomic delivery
and verification gates.

The Euler study also records the `Euler V3` naming boundary: in the preserved
evidence, V2 is the protocol generation and V3 is the hosted API name. Do not
invent a separate protocol generation without new primary evidence.

## What this never does

- No live collection. The command accepts preserved local files and reaches no
  network.
- No path escape. Absolute paths, parent traversal, symlinks, aliased files and
  artefacts outside the release directory are refused.
- No digest-only verification. The verifier rebuilds canonical bytes and
  checks one-to-one source selectors.
- No rewriting raw evidence. The native source stays beside its interpretation.
- No semantic flattening. Venue-qualified actions do not become universal
  claims about repayment, delinquency or default.
- No identity inference, rating, publisher-authenticity claim or independent
  chain-proof claim.

If a build, verification, source check or test did not run, say so plainly and
do not describe it as successful.

## Promise Machine contract

### tabularium-release-build

- Promise: A successful `build` writes venue-qualified canonical events and coverage whose rows deterministically map one-to-one from the validated preserved source under the named adapter and mapping versions.
- Evidence: The preserved source and capture manifest, source digest and count checks, adapter and mapping rules, complete native records, ordered selectors, canonical JSONL and coverage manifest.
- Evidence classes: recorded, checked, recomputed
- Boundary: The release reports the preserved source's declared boundary and unsupported collections; it does not prove source completeness, canonical-chain status, repayment completion, identity or creditworthiness.
- Authorises: Creation of a new immutable versioned event release for offline verification.
- Consequence: 2
- Refuses: Aliasing or rewriting source evidence, flattening venue meaning, accepting duplicate or missing selectors, hiding unsupported records or changing published release bytes.
- Recovery: Correct the source capture or mapping in a new versioned release, rebuild into a fresh directory and verify it.
- Exceptions: none

### tabularium-release-verification

- Promise: A successful `verify` recomputes the named release's source, capture and canonical digests, counts, schema and mapping versions, selectors and expected JSONL from local files.
- Evidence: The complete release directory, coverage manifest, source and capture bytes, adapter implementation, rebuilt canonical records and zero-exit verification report.
- Evidence classes: checked, recomputed, recorded
- Boundary: Verification establishes internal consistency and implemented mapping only; it does not authenticate a publisher, independently prove the chain boundary or turn venue records into a counterparty verdict.
- Authorises: With separate publisher authority, publication or downstream use of the exact verified release with its coverage and unsupported records visible.
- Consequence: 3
- Refuses: Publication after a digest, path, count, version, selector or rebuild mismatch, or description of an unsigned release as authentic or chain-proved.
- Recovery: Inspect the named mismatch, preserve published bytes, build a superseding release when interpretation changes and rerun offline verification.
- Exceptions: none

### tabularium-compound-witness

- Promise: A successful `compound-witness` followed by `verify-compound-witness` reproduces the ordered calls, relevant proxy writes and signed-principal transition for the one named verified Alexandria transaction witness.
- Evidence: The verified Alexandria release and component digests, pinned Comet commit, implementation and code bindings, emitted facts and witness manifest, and passing witness verification.
- Evidence classes: recorded, checked, recomputed
- Boundary: The Phase 0 witness is non-canonical and covers one transaction and method; it is not a coverage-v2 row, interval release, canonical mapping or independent chain proof.
- Authorises: Use of the checked facts as bounded implementation evidence while Phase 1 canonical mapping remains absent.
- Consequence: 1
- Refuses: Generalising to another transaction, implementation, layout, call shape or interval, or publishing the witness as canonical Tabularium credit events.
- Recovery: Repair or recapture the Alexandria witness, update the named implementation method deliberately and rerun both witness commands.
- Exceptions: none
