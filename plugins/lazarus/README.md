# Lazarus

<!-- marketplace-context:start -->
## In one line

Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests.

**Try something else when.** Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence.

**Current frontier.** Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented.

**Next Fiat job.** Use /hexaemeron:fiat to bind a Lazarus fixture through an Ariadne state-fixture predicate in the first end-to-end Goldfinch preservation release without upgrading recorded RPC evidence into proof-backed state. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Lazarus preserves the finite part of historical Ethereum state and RPC
evidence that one application test needs. A fixture binds an explicit capture
plan, a fixed block header, exact JSON-RPC records and EIP-1186 account and
storage proofs into deterministic files. Replay answers only requests present
in that fixture and fails closed on a miss.

The current build implements finite capture and offline verification for the
versioned plan, header, RPC record, proof record and manifest formats. It
writes canonical JSON and JSONL, confines fixture paths, derives exact request
keys, verifies component digests, recomputes the header hash, traverses
EIP-1186 proofs, checks captured code and serves exact requests over loopback.

## Evidence boundary

- **Proof-backed state** is checked through an EIP-1186 proof against the
  captured header's `stateRoot`. Captured code is checked against the proved
  `codeHash`.
- **Header-bound data** is internally consistent with the named header. That
  does not prove on its own that the header belongs to Ethereum's canonical
  chain.
- **Recorded RPC evidence** preserves an exact response, receipt, log query,
  call or trace without describing it as a state proof.

The [study](./docs/study.md) records the prior-art research and selected exact
request cassette design. The [runbook](./docs/runbook.md) divides the prototype
into six reviewable steps.

## Capture and offline commands

The implemented entrypoints are:

```bash
python3 scripts/lazarus.py capture \
  --plan <plan.json> --rpc-url <url> --out <fixture>
python3 scripts/lazarus.py validate schemas
python3 scripts/lazarus.py validate plan <plan.json>
python3 scripts/lazarus.py build-manifest <fixture> \
  --component plan.json --component header.json \
  --chain-id 0x1 --block-number <quantity> --block-hash <hash>
python3 scripts/lazarus.py verify <fixture>
python3 scripts/lazarus.py replay <fixture>
```

`capture` is the only command that receives a provider URL. It brackets one
fixed block, verifies the captured proofs and code, removes provider error
prose and atomically finalises a deterministic fixture. `verify` repeats all
format, digest, header, trie and code checks without a network. `replay` is the
local exact-request server: it verifies before binding, returns a
stable capture-plan fragment for a miss and has no provider fallback.

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
