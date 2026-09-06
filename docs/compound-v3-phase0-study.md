# Compound v3 Phase 0 study

Issue: https://github.com/wildcat-finance/skills/issues/68

## Problem

Alexandria and Tabularium specified a Compound v3 preservation pipeline but
had no executable Compound path or preserved witness. Phase 0 had to show that
a pinned deployment tree can become a deterministic registry, that the chosen
Ethereum endpoint can read old state and traces, that nested Comet calls and
ordered storage writes can be retained, and that an offline consumer can
rebuild one raw transaction into call and signed-principal facts.

The working prototype is an Alexandria release at
`plugins/alexandria/examples/compound-v3-phase0-v0/` and a Tabularium witness
at `plugins/tabularium/examples/compound-v3-phase0-v0/`. It proves one fixed
method corpus. It does not prove a complete market interval, an independent
chain boundary or continued provider availability.

## Measured evidence

The production registry is pinned to `compound-finance/comet` commit
`f766f51583c23acc33b2a7824654ef2029a96804`, tree
`1101bf195fce18dc1feb3e56c992adfddac27b0e`, and deployments tree
`cf2dc2381d00a3c60563f4b5aa486412ddd40d62`. It contains 28 production markets
on 10 chains. Ethereum USDC names Comet proxy
`0xc3d688B66703497DAA19211EEdff47f25384cdc3`, Bulker
`0xa397a8C2086C554B531c02E29f3291c9704B00c7`, and base token
`0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`.

`CometStorage.sol` packs global indexes into slot 0. `userBasic` is mapping
slot 5, and its low 104 bits hold a signed two's-complement principal. The
account slot is `keccak256(pad32(account) || pad32(5))` using Ethereum Keccak,
not FIPS SHA3-256.

Read-only probes on 17 August 2026 used the public endpoint documented by
Wildcat's `market_history` repository. It reported
`reth/v1.11.3-d6324d6/x86_64-unknown-linux-gnu`, chain ID 1, and finalized block
25,774,949 with hash
`0x6c0c64f7fee455de134925db00f2f5c9b01710fa47d4d0dae7aaa86eaa35c8e2`.
That is one provider's report, not independent finality evidence.

The old transaction
`0x10a4ec0d64fc459c9945098601a8115c9268fd9a4742cae509ec15adaf1f9f03`
at block 15,412,361 proves this endpoint returned historical code, storage,
`eth_call`, flat traces, call traces, prestate diffs and opcode logs. Its call
tree contains a nested Comet `supplyFrom`, and its opcode result contains 3,716
steps and 11 `SSTORE` operations.

The recent transaction
`0x8c02ef7830078c22e8221b91a77c757e95f7e373adcccf132fb128136f224ad3`
at block 25,766,757 calls the pinned Bulker. It contains ordered Comet calls at
paths `[0]` and `[1]`, 20,747 opcode steps and 22 `SSTORE` operations. Account
`0x56105c17bef06455e1066f7c455ff28f15c7283e` maps to slot
`0xcd0f529d81158ba9167238f24519db12c14ccee8db94d025c74b9a693804a040`.
The transaction creates that slot and finishes with signed principal
`-6349137978`. Tabularium retains every relevant repeated write before
reporting the initial and final packed values.

The earlier specification also asked Phase 0 to find a base transfer between
two borrowers. A scan of successful top-level USDC Comet `transfer` and
`transferFrom` calls plus sampled internal calls found no verified mined
example with debt on both sides. That is not proof that no example exists. The
repository carries a clearly labelled synthetic hostile fixture from
Compound's pinned transfer scenario, while mined-instance discovery remains a
Phase 1 task.

## Constraints

- Collection is an explicit network command; Alexandria's existing five
  commands remain offline.
- The endpoint comes only from an environment variable. URL, query,
  credentials and transport headers are never preserved.
- Every request and raw response is digest-bound with Alexandria's 64 MiB
  component ceiling and added request, redirect, depth and node bounds.
- `prestateTracer` supplies transaction-start state. `block - 1` is not an
  acceptable substitute when the transaction is not first in its block.
- Implementation and layout are resolved at each transaction block.
  `DELEGATECALL` writes are attributed to proxy storage.
- Compound Phase 0 facts stay outside Euler's canonical-event v2 and coverage
  v2. Phase 1 owns a new canonical schema version.
- Existing Alexandria, Aave v4 and Euler truth bytes, vendored Pashov prose,
  historical audit bodies, legal attribution and the Lazarus fixture digest
  remain unchanged.

## Options

A logs-only adapter was rejected because base transfers and zero crossings can
change signed principal without enough log evidence. A full resumable harvester
was deferred because it adds epochs, journals, reorg handling and independent
reconciliation before the method is proved. A general multi-client trace
normalizer was also deferred because this corpus measures one Reth format.

The selected design keeps collection and interpretation separate but lands
them together. Alexandria pins the registry and preserves a bounded old/recent
corpus. Tabularium verifies that release, retains logical call paths and ordered
proxy-storage writes, computes the mapping slot with Ethereum Keccak, decodes
the signed `int104`, and emits a non-canonical execution witness.

## Risks and refusals

The verifier rejects wrong transaction-start state, SHA3/Keccak confusion,
invalid signed-width decoding, implementation/storage-address confusion,
missing or reordered trace locators, old/current implementation drift,
unexpected runtime code, unbounded JSON, endpoint disclosure and changed
published bytes. Coverage is `partial` and evidence is `recorded-rpc`.

The release does not claim chain proof, provider independence, market-history
completeness, account identity, a Wildcat verdict, or a mined debt-to-debt
transfer. Errors are preserved as evidence but never counted as successful
method proof.

## Sources

- `plugins/alexandria/docs/compound-v3-harvest.md`
- `plugins/tabularium/docs/compound-v3-preservation.md`
- `plugins/tabularium/docs/release-policy.md`
- Compound Comet commit `f766f51583c23acc33b2a7824654ef2029a96804`,
  especially `deployments/`, `hardhat.config.ts` and `contracts/CometStorage.sol`
- Geth built-in tracer documentation:
  https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers
- `wildcat-finance/mono` commit
  `a15d7af0eb34835739d0ba006cec2fd32cda7e00`, hosted-data gateway notes
- `wildcat-finance/market_history` README for the public endpoint
- Exact live JSON-RPC bytes preserved in the checked-in Alexandria release
