---
name: lazarus
description: >
  Capture, verify and replay the finite part of historical Ethereum state and
  exact JSON-RPC evidence required by an application test. Use when an archive
  endpoint or old protocol may disappear and the user needs a deterministic,
  proof-checked fixture with a fail-closed local replay boundary. Never use it
  to describe transaction hashes, calls, traces or unrelated RPC fields as
  proof-backed evidence.
metadata:
  version: "2.2.0"
---

# Lazarus

## Frontier

Lazarus owns its own state-fixture preservation frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Lazarus captures the finite historical Ethereum state and exact RPC evidence one application test needs, proves the state-backed part, and replays only recorded requests.

**Current frontier.** Receipt witnesses reconstruct receiptsRoot offline and prove one scoped receipt payload plus its consensus-log projection; transaction hashes and unrelated RPC results remain recorded evidence, while empty blocks still have no receipt-witness representation.
<!-- marketplace-context:end -->

Lazarus turns a finite historical Ethereum capture plan into a deterministic
fixture and calls its exact JSON-RPC answers back into a local test after the
original provider is gone.

Alexandria preserves broader lending-data captures; Berean may consume
fixed-block reads in a grounded-agent release; Ariadne may bind a verified
preservation release to its evidence. Those hand-offs preserve the distinction
between receipt-trie-proved consensus payloads and recorded RPC decorations.

`$SKILL_DIR` is the directory holding this file. The command lives at
`$SKILL_DIR/../../scripts/lazarus.py`; resolve it from where you loaded this
skill. This build implements finite capture plus the offline format, manifest
and proof-verification layer, with exact verified replay over loopback.

## Day to day

**Protocol engineering.** A fork test depends on a paid archive endpoint and
one old block. Its declared reads become a reviewable fixture, and an
unexpected read becomes a visible miss instead of a hidden provider call.

**Research.** A closed venue's state needs to remain inspectable after its
front end and hosted data disappear. The fixture keeps the block, finite
coverage and evidence classes together.

**Security.** An incident test needs stable historical inputs. Account and
storage values are checked against the captured state root. A declared full
receipt witness may prove the target consensus receipt payload and its scoped
log projection against `receiptsRoot`; transaction hashes, calls, traces and
unrelated fields remain recorded evidence.

**Archiving.** A fixture has to outlive the people who made it. A preservation
release ships the fixture, a statement about it and the document binding them,
so a stranger can check that the statement describes that fixture and does not
claim more than it holds.

## Available offline commands

The current build validates versioned documents and binds their bytes in a
manifest:

```bash
python3 scripts/lazarus.py capture \
  --plan <plan-v2.json> --rpc-url <primary-url> \
  --anchor-rpc-env <source-id>=<environment-variable> \
  --out <fixture-directory>
python3 scripts/lazarus.py validate schemas
python3 scripts/lazarus.py validate plan <plan.json>
python3 scripts/lazarus.py build-manifest <fixture-directory> \
  --component plan.json --component header.json \
  --chain-id 0x1 --block-number <quantity> --block-hash <hash>
python3 scripts/lazarus.py verify <fixture-directory>
python3 scripts/lazarus.py replay <fixture-directory>
python3 scripts/lazarus.py release <fixture-directory> \
  --statement <statement.json> --out <release-directory>
python3 scripts/lazarus.py verify-release <release-directory>
```

`verify` checks schema versions, safe paths, canonical manifest bytes and every
declared component length and SHA-256 digest. It then recomputes the
fork-appropriate header hash; verifies EIP-1186 account and storage inclusion
or absence against the header state root; checks response fields against the
decoded leaves; and hashes captured code against the proved `codeHash`. It
also reconstructs a declared ordered receipt witness and checks its scoped
target receipt and filtered-log relations. It reports separate proof-backed,
receipt-trie-proved, header-bound and recorded-RPC evidence counts.

`release` writes a preservation release: the verified fixture, a statement
somebody else wrote about it, and a document binding the two. The statement is
held to the counts verification recomputed rather than to the ones the manifest
claims, which is the only place that disagreement is visible, and nothing is
written unless both the fixture and the statement pass. `verify-release` reads
one back from its bytes years later. Neither reaches a network, and neither
signs anything. See
[docs/preservation-release.md](../../docs/preservation-release.md).

Read the checked-in
[study](../../docs/study.md) for the selected design and the
[runbook](../../docs/runbook.md) for implementation status.

`capture` resolves and brackets the plan's fixed number and expected hash. It
prefers EIP-1898 hash selectors for proofs and code, safely falls back to the
fixed number, checks the closing header, verifies the complete fixture and
only then atomically finalises the output directory. Required request or proof
failures leave no fixture. Optional provider failures retain only a stable
sanitised error. URL credentials, query values, bearer tokens, cookies and raw
provider errors are not fixture material.

For plan v2 or v3, repeat `--anchor-rpc-env SOURCE_ID=ENV_VAR` once for every
sorted source declared by the plan. The source set must match exactly. Capture reads
only those explicitly named, non-empty environment variables and never places
their URL values in argv, output, diagnostics or fixture bytes. One client per
source shares the primary request, response-byte, component-byte, total-byte
and elapsed-time limits. Each records only a local UTC observation time and the
matching mainnet chain ID, fixed number and expected block hash. Any mapping,
transport, identity, schema, limit, secret-scan or final verification failure
removes the stage and leaves no destination. The operator contract and example
are in [the chain-anchor guide](../../docs/chain-anchors.md).

`replay` verifies the fixture in the same process before binding to
`127.0.0.1`. It answers only exact method-and-parameter matches, preserves the
caller's identifier, handles single requests, batches and notifications, and
returns error `-32070` with a capture-plan fragment on a miss. It rejects
write and unsupported methods and has no provider client or fallback setting.

## Fixture boundary

A fixture separates four classes rather than lending one class the strength
of another:

1. **Proof-backed state.** Account and storage values verify through EIP-1186
   against the captured header's `stateRoot`; code verifies against the proved
   `codeHash`.
2. **Receipt-trie-proved relations.** A plan-v3 witness supplies every ordered
   consensus receipt. Verification reconstructs the header's `receiptsRoot`,
   then checks one target consensus receipt payload and its declared
   consensus-log projection. Transaction hashes are excluded.
3. **Header-bound data.** The header hash and fields are checked internally.
   An external chain anchor is still required to call that header canonical.
4. **Recorded RPC evidence.** Exact method, parameters and result or sanitised
   error bytes are preserved. Transaction hashes, calls, traces and any
   receipt or log field outside the scoped consensus relation stay here.

Chain anchors are separately counted recorded observations. Distinct source
IDs are operator labels, not proof of separate provider ownership or
infrastructure. Matching records do not establish canonical-chain membership
or provider independence; both report fields remain false.

Replay is exact request replay, not arbitrary EVM execution from a partial
world state. Object member order is canonicalised for a request key; values,
array order, omitted fields, quantities and block selectors remain exact.

## What capture must require

- An explicit Ethereum mainnet plan whose effective form fixes one block
  number and expected block hash.
- Exact JSON-RPC method and parameter pairs, required or optional status and
  expected evidence class.
- A finite list of account addresses and sorted, unique 32-byte storage slots.
- For plan v3, one full ordered receipt request, one target receipt lookup,
  its exact transaction index and one fixed-block filtered-log request.
- Limits for requests, components, time and bytes.
- A second matching header read when number-based provider fallback is used.

Provider credentials are runtime inputs. They never enter output, diagnostics
or digest material.

## What verify must establish

- Built-in schema versions and their registered bytes.
- Safe relative component paths, exact lengths and SHA-256 digests.
- The fork-appropriate header hash and expected block identity.
- Account and storage inclusion or absence proofs against the header state
  root, response values against decoded leaves and code against `codeHash`.
- For plan v3, the full ordered consensus receipt sequence against the header
  receipts root, the target consensus payload and exact filtered-log relation.
- Separate counts for proof-backed, receipt-trie-proved, header-bound and
  recorded evidence.
- Exact plan-v2 or plan-v3 anchor coverage and agreement, reported separately
  without a canonical-chain or provider independence claim.

A self-consistent header is not proof that it belongs to Ethereum's canonical
chain. Report the expected hash and its external provenance without upgrading
the local check.

## What replay must guarantee

Replay verifies the fixture in the same process before binding to loopback. It
has no capture URL and no fallback provider. A request absent from the fixture
returns the stable Lazarus miss error and a capture-plan fragment. It never
invents a zero value or leaves loopback to answer a miss.

## What this never does

- Replace an archive node or capture unbounded state.
- Execute arbitrary `eth_call` from partial state in the first format.
- Prove a transaction hash or a receipt or log field outside the scoped
  consensus payload and projection checked against `receiptsRoot`.
- Treat client trace output as portable proof.
- Capture pending state, subscriptions or write methods.
- Hold a private key, sign a transaction or make an Ariadne publisher claim.
- Claim proof-backed status for any value that did not pass the offline trie
  and code checks.

## Promise Machine contract

### lazarus-fixture-capture

- Promise: A successful `capture` atomically writes a finite fixed-block fixture only after resolving the expected block, collecting the declared requests and proofs, closing the block bracket and passing complete local verification.
- Evidence: The explicit plan, exact runtime anchor mapping, opening and closing headers, exact sanitised RPC records, source-sorted anchor records, EIP-1186 proofs, optional ordered receipt witness, manifest, shared limits, union provider-secret scan and the in-process successful verification result.
- Evidence classes: recorded, checked, recomputed, proved: EIP-1186 account and storage relation; proved: receipt-trie consensus receipt and scoped log-projection relation
- Boundary: Only account and storage values and code with the named state proof relation, plus a consensus receipt payload and scoped consensus-log projection accepted through a reconstructed `receiptsRoot`, are proof-backed. Transaction hashes, calls, traces and unrelated RPC fields remain recorded evidence. Matching anchor records remain recorded observations and establish neither canonical-chain membership nor provider independence.
- Authorises: Installation of the verified fixture as a durable finite historical test input.
- Consequence: 2
- Refuses: Finalising after an incomplete or duplicate anchor mapping, absent or empty named environment value, provider transport or identity disagreement, required request, proof, block bracket, shared limit, credential-sanitisation, secret scan or verification failure, or retaining a provider URL or raw provider error as evidence.
- Recovery: Inspect the stable failure, amend the finite plan or provider input, discard the temporary output and perform a fresh capture.
- Exceptions: none

### lazarus-fixture-verification

- Promise: A successful `verify` recomputes the fixture's schemas, canonical manifest, component digests, header hash, state proofs, optional receipt-trie relations, response values and evidence-class counts from local bytes.
- Evidence: The fixture tree, registered schema bytes, manifest, header, proof, RPC, optional receipt-witness and anchor records, recomputed hashes, exact plan-to-anchor coverage and the complete verification report.
- Evidence classes: checked, recomputed, proved: EIP-1186 account and storage relation; proved: receipt-trie consensus receipt and scoped log-projection relation
- Boundary: Verification does not prove canonical-chain membership, provider independence, transaction-hash attribution, receipt or log fields outside the declared consensus relation, trace portability or facts outside the finite manifest.
- Authorises: Use of the verified fixture and its separately counted evidence classes in the named offline test or preservation workflow.
- Consequence: 1
- Refuses: Calling a component proof-backed when its trie or code check failed, or using a missing, extra, escaped, changed or schema-unknown component.
- Recovery: Inspect the named component or proof failure, restore the captured bytes or recapture the finite plan and rerun verification.
- Exceptions: none

### lazarus-exact-replay

- Promise: A running `replay` verifies the fixture before binding to loopback and answers only exact recorded method-and-parameter keys without provider fallback.
- Evidence: The in-process verification result, recomputed request-key table, loopback binding, exact response record and stable miss response for an absent request.
- Evidence classes: checked, recomputed, recorded
- Boundary: Replay is not arbitrary EVM execution, an archive service or permission to answer writes, subscriptions, unsupported methods or unrecorded variants.
- Authorises: Supplying the exact verified responses to a local application test within the loopback replay session.
- Consequence: 2
- Refuses: Binding beyond loopback, leaving the fixture for a miss, inventing a zero, accepting a near-match or serving a write method.
- Recovery: Use the emitted capture-plan fragment to extend the finite plan, capture and verify a new fixture, then restart replay.
- Exceptions: none

### lazarus-preservation-release

- Promise: A successful `release` followed by `verify-release` binds the verified fixture bytes to a separately supplied statement whose evidence counts do not exceed those recomputed from the fixture.
- Evidence: The verified fixture, supplied statement, binding document, release-tree digests, recomputed evidence counts and passing release verification.
- Evidence classes: recorded, checked, recomputed
- Boundary: The release is unsigned, reaches no network and does not establish publisher identity, canonical-chain status, transaction-hash attribution or any statement claim beyond the binding checked here.
- Authorises: With separate publisher authority, publication or archival hand-off of the exact preservation release as inspectable evidence.
- Consequence: 3
- Refuses: Writing or publishing when the fixture or statement fails, the binding mismatches, the statement upgrades evidence counts or signature identity is merely assumed.
- Recovery: Repair or replace the statement, recapture the fixture when its evidence is insufficient, build a new release directory and verify it before publication.
- Exceptions: none
