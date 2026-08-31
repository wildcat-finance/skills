![Lazarus](./assets/characters/lazarus.png)

# Lazarus

<!-- marketplace-context:start -->
## In one line

Lazarus captures the finite historical Ethereum state and exact RPC evidence one application test needs, proves the state-backed part, and replays only recorded requests.

**Current frontier.** Receipt witnesses reconstruct receiptsRoot offline and prove one scoped receipt payload plus its consensus-log projection; transaction hashes and unrelated RPC results remain recorded evidence, while empty blocks still have no receipt-witness representation.

**Next Fiat job.** Use /hexaemeron:fiat to accept an empty ordered receipt witness only when the verified header carries Ethereum's empty trie root, derive zero receipt-trie-proved relations without a target receipt or filtered-log request, and preserve the shipped non-empty Goldfinch relation plus every legacy format. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Start here

Use Lazarus when a test depends on historical Ethereum state or RPC behaviour
that may no longer be available. It captures a finite fixed-block fixture,
verifies the supported proof relations offline, and replays only the exact
requests the fixture contains.

The current release can reconstruct a declared receipt trie for represented
receipt payloads and log projections. Empty blocks have no receipt witness,
and recorded transaction hashes, calls, traces, or provider statements do not
become proved merely because they are in the fixture.

## Place in the collective

Lazarus preserves one test's finite chain boundary. Alexandria preserves wider
lending-data captures, while Berean may consume fixed-block reads in a grounded
agent release. Ariadne can bind a verified Lazarus preservation release to its
state-fixture evidence. Those hand-offs preserve Lazarus's evidence classes:
the scoped consensus receipt and log projection can be receipt-trie proved,
while transaction hashes, calls, traces and unrelated RPC fields cannot.

Synkrisis is meant for comparison across validated run-observation records,
not for comparing Lazarus fixtures or strengthening their evidence classes.
It writes a cohort and findings for those records alone.

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
versioned plan, header, RPC record, proof record, receipt-witness record,
chain-anchor record and manifest formats. It
writes canonical JSON and JSONL, confines fixture paths, derives exact request
keys, verifies component digests, recomputes the header hash, traverses
EIP-1186 proofs, reconstructs a declared receipt trie, checks captured code and
serves exact requests over loopback.

## How it works

Capture fixes a block, records exact JSON-RPC requests and responses, and binds
the fixture to a deterministic manifest. Account and storage claims must pass
EIP-1186 trie-proof checks against the captured header; contract code must match
the proved code hash. A plan-v3 receipt witness can reconstruct `receiptsRoot`
from every ordered consensus receipt and prove its target receipt payload plus
the declared filtered-log projection. Transaction hashes, calls, traces and all
other RPC result fields remain recorded evidence.

Replay verifies the fixture before opening a loopback server. An uncaptured
request returns a stable `-32070` error describing the missing plan entry, and
there is no provider fallback. The checked-in Goldfinch examples preserve the
original recorded-RPC fixture and separately demonstrate the receipt-root
relation, mutation rejection and deterministic release rebuilding without a
network.

## What it ships

- finite, bounded capture from one fixed historical block;
- canonical JSON and JSONL formats with versioned, digest-pinned schemas;
- offline header, account, storage, code, receipt-trie and manifest verification;
- exact-request JSON-RPC replay over loopback, including batches and
  notifications; and
- fixed Goldfinch v0 and v1 demonstrations, including a preservation release
  for each evidence boundary.

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
- **Receipt-trie-proved relations** reconstruct the captured header's
  `receiptsRoot` from the full ordered consensus receipt sequence, then prove
  one scoped target receipt payload and its declared consensus-log projection.
  Transaction hashes are not part of this proof.
- **Header-bound data** is internally consistent with the named header. That
  does not prove on its own that the header belongs to Ethereum's canonical
  chain.
- **Recorded RPC evidence** preserves exact response decorations, unrelated
  receipt and log fields, calls or traces without describing them as proved.

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
set to equal the plan-v2 or plan-v3 anchor declarations, shares one request, byte and elapsed-time budget across
all clients, brackets one fixed block, verifies captured proofs and code,
removes provider error prose, scans for every provider secret and atomically
finalises a deterministic fixture. `verify` repeats all
format, digest, header, state-trie, receipt-trie and code checks without a
network. `replay` is the local exact-request server: it verifies before binding, returns a
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

[`examples/goldfinch-v1`](./examples/goldfinch-v1) uses the same captured raw
sources with a plan-v3 receipt witness. It reconstructs all 224 receipts at the
same block, proves target index `0xbf` with 110 consensus logs, proves the exact
five-log projection, and ships a state-fixture/v2 release. Run its fail-closed
offline demonstration with:

```bash
python3 plugins/lazarus/examples/goldfinch-v1/demo.py
```

The demo verifies and deterministically rebuilds the statement and release,
rejects one-byte receipt, index, log, root, count and release mutations, denies
network access, and shows that a coherent transaction-hash rewrite changes
neither `receiptsRoot` nor either proved relation. See the
[receipt inclusion proof guide](./docs/receipt-inclusion-proofs.md) for the
operator boundary and exact verification commands.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
```

The CI job selects the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version),
installs the fully resolved `requirements.lock` environment, and then runs both
suites.
