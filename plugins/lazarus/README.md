# Lazarus

<!-- marketplace-context:start -->
## In one line

Lazarus captures the finite historical Ethereum state and exact RPC evidence one application test needs, proves the state-backed part, and replays only recorded requests.

**Current frontier.** Receipts and logs are recorded RPC evidence only; nothing proves them against the captured header's receiptsRoot.

**Next Fiat job.** Use /hexaemeron:fiat to prove the fixture's recorded transaction receipt and its logs against the captured header's receiptsRoot, so receipt evidence stops resting on the provider's word, and carry the resulting evidence class through the manifest, the verifier, the release and the Ariadne state-fixture predicate without moving any other recorded RPC response into a proved class. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Lazarus preserves one test's finite chain boundary. Alexandria preserves wider
lending-data captures, while Berean may consume fixed-block reads in a grounded
agent release. Ariadne can bind a verified Lazarus preservation release to its
state-fixture evidence. None of those hand-offs promotes receipts, logs, calls,
or traces into state proofs; that distinction remains Lazarus's boundary.

Lazarus preserves the finite part of historical Ethereum state and RPC
evidence that one application test needs. A fixture binds an explicit capture
plan, a fixed block header, exact JSON-RPC records and EIP-1186 account and
storage proofs into deterministic files. Replay answers only requests present
in that fixture and fails closed on a miss.

A preservation release goes one step further: the fixture, a statement somebody
else wrote about it, and a document binding the two, written only if the fixture
verifies and the statement survives being held to what that verification
recomputed. See [docs/preservation-release.md](docs/preservation-release.md).

The current build implements finite capture and offline verification for the
versioned plan, header, RPC record, proof record, chain-anchor record and
manifest formats. It
writes canonical JSON and JSONL, confines fixture paths, derives exact request
keys, verifies component digests, recomputes the header hash, traverses
EIP-1186 proofs, checks captured code and serves exact requests over loopback.

## How it works

Capture fixes a block, records exact JSON-RPC requests and responses, and binds
the fixture to a deterministic manifest. Account and storage claims must pass
EIP-1186 trie-proof checks against the captured header; contract code must match
the proved code hash. Receipts, log queries, calls and traces remain labelled as
recorded RPC evidence. They are not promoted into state proofs.

Replay verifies the fixture before opening a loopback server. An uncaptured
request returns a stable `-32070` error describing the missing plan entry, and
there is no provider fallback. The checked-in Goldfinch example exercises
proof-backed code and storage, a receipt, a log query, a deliberate miss, proof
mutation rejection and byte-for-byte manifest rebuilding without a network.

## What it ships

- finite, bounded capture from one fixed historical block;
- canonical JSON and JSONL formats with versioned, digest-pinned schemas;
- offline header, account, storage, code and manifest verification;
- exact-request JSON-RPC replay over loopback, including batches and
  notifications; and
- 414 tests plus a proof-checked Goldfinch demonstration.

## Day to day

**Developers.** An old integration test depends on an archive endpoint that is
slow, costly or gone. Capture the exact historical state and responses the test
uses, commit the fixture, and run the same requests locally with a visible miss
for anything the plan omitted.

**Security and audit.** A historical fixture claims an account balance, code
hash or storage value. Run `verify` to check the trie path against the named
header and keep ordinary RPC evidence outside that proof boundary.

## Evidence boundary

- **Proof-backed state** is checked through an EIP-1186 proof against the
  captured header's `stateRoot`. Captured code is checked against the proved
  `codeHash`.
- **Header-bound data** is internally consistent with the named header. That
  does not prove on its own that the header belongs to Ethereum's canonical
  chain.
- **Recorded RPC evidence** preserves an exact response, receipt, log query,
  call or trace without describing it as a state proof.

Multi-provider anchors are a fourth, separately counted observation surface.
Plan v2 declares opaque source IDs and runtime environment-variable mappings;
each source records only its UTC observation time and matching chain, height
and hash. Matching records prove neither canonical-chain membership nor
provider independence. See [the chain-anchor guide](./docs/chain-anchors.md).

The [study](./docs/study.md) records the prior-art research and selected exact
request cassette design. The [runbook](./docs/runbook.md) divides the prototype
into six reviewable steps.

## Capture and offline commands

The implemented entrypoints are:

```bash
python3 scripts/lazarus.py capture \
  --plan <plan-v2.json> --rpc-url <primary-url> \
  --anchor-rpc-env archive-a=ARCHIVE_A_RPC \
  --anchor-rpc-env archive-b=ARCHIVE_B_RPC \
  --out <fixture>
python3 scripts/lazarus.py validate schemas
python3 scripts/lazarus.py validate plan <plan.json>
python3 scripts/lazarus.py build-manifest <fixture> \
  --component plan.json --component header.json \
  --chain-id 0x1 --block-number <quantity> --block-hash <hash>
python3 scripts/lazarus.py verify <fixture>
python3 scripts/lazarus.py replay <fixture>
```

`capture` is the only command that receives provider URLs. The primary URL
keeps its legacy argument; each anchor argument carries only a source ID and
environment-variable name, never the URL value. Capture requires the mapping
set to equal plan v2, shares one request, byte and elapsed-time budget across
all clients, brackets one fixed block, verifies captured proofs and code,
removes provider error prose, scans for every provider secret and atomically
finalises a deterministic fixture. `verify` repeats all
format, digest, header, trie and code checks without a network. `replay` is the
local exact-request server: it verifies before binding, returns a
stable capture-plan fragment for a miss and has no provider fallback.

[`examples/multi-provider-anchor-v0`](./examples/multi-provider-anchor-v0) is a
synthetic plan-v2 fixture with two matching recorded observations. Verify it
offline with:

```bash
python3 scripts/lazarus.py verify examples/multi-provider-anchor-v0
```

The result reports `chain-anchor-records: 2`; both canonical-chain and provider
independence claims remain false.

## Goldfinch demonstration

[`examples/goldfinch-v0`](./examples/goldfinch-v0) is a checked-in Ethereum
mainnet fixture for a Goldfinch market at block `0xc7da16`. It carries a
proof-backed account, contract code and storage slot, plus the named receipt
and a five-log query as recorded RPC evidence. Run the complete test without a
provider:

```bash
python3 plugins/lazarus/examples/goldfinch-v0/demo.py
```

The demo verifies before replay, reads the four committed results through
ordinary loopback JSON-RPC, observes a `-32070` miss for slot `0x1`, rejects a
one-nibble proof mutation and rebuilds the same manifest bytes.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
```

The CI job installs the fully resolved `requirements.lock` environment under
supported Python versions before running both suites.
