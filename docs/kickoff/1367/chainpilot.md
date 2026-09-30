# Two-chain Lazarus pilot: draft plan and compatibility matrix

Issue: https://github.com/wildcat-finance/skills/issues/1486, a prerequisite
child of https://github.com/wildcat-finance/skills/issues/1367.

**Status: draft.** Lazarus has not reviewed it, and three items below still
need a decision from the maintainer. Nothing here is a capture: no fixture was
built, and the checks only read chain data.

## Decision and custody

- **Decision.** Dr Laurence E. Day decided on 2026-09-30 that Base (chain ID
  8453) is the second chain, after Ethereum mainnet, because it is the second
  largest chain by stablecoin activity. He also said venue capture on other
  chains is out of focus. The
  [decision comment](https://github.com/wildcat-finance/skills/issues/1486#issuecomment-5904174727)
  records both.
- **Producer.** Claude Code, in the delivery session of 2026-09-30, from Skills
  `87b1dd072124dc75ba83df4ca1ee5e6c1ccf57ba`.
- **Reviewer.** Lazarus review: not done. No reviewer is named yet.
- **Evidence.** [`evidence/`](evidence/) holds the scripts and their output.
  `evidence/SHA256SUMS` lists each file's SHA-256, and its own SHA-256 is
  `a8c1bfbecab902aadddfb4aef12f4766dbea1d0e1e655c50c01b4f37c40bb7f6`.
  The scripts run from a Lazarus checkout at the revision above. They read
  Ethereum from `ALEXANDRIA_COMPOUND_RPC_URL` with `ALEXANDRIA_RPC_BEARER`, and
  Base from `LAZARUS_BASE_RPC` and `LAZARUS_BASE_RPC_RECEIPTS`. The Base runs
  used public routes that need no key. `probe_window.out` is a dated observation
  of 2026-09-30 06:17 UTC and moves with the chain head; a rerun reproduced the
  other check outputs byte for byte. No credential or URL is recorded.

## The pilot

- **Ethereum**, chain ID `0x1`: fixed block 26,022,093 (`0x18d10cd`), hash
  `0x1cfd09b6dfaa2af921e367d94f24e2b1e6b7f910a7a6f4276576f09aeb3f5cb9`,
  timestamp 1789947863. Provenance: the Wildcat V2 pin used across the Skills
  issues.
- **Base**, chain ID `0x2105` (8453): fixed block 51,579,258 (`0x313097a`), hash
  `0x0366446fd6fca93d511f0dd1700076670f0608a1dc73e6be2bd1329f217f611d`,
  timestamp 1789947863. Provenance: the last Base block not after the Ethereum
  block's timestamp.

Both headers recompute to their hash (see the matrix). That is a header-bound
result only. Lazarus already declines to call a self-consistent header
canonical, and nothing here ties the Base block to an L1 batch or output root.

**Accounts and slots**, on each chain, proposed:

| Account | Ethereum | Base | Slots | Why |
| --- | --- | --- | --- | --- |
| Multicall3 | `0xcA11bde05977b3631167028862bE2a173976CA11` | same address | none | same address, same code (3,808 bytes, code hash `0xd5c15df6…`) |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | same address | none | same address, different code (code hashes `0xc67d1657…` and `0xa67739ab…`) |
| USDC proxy | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` | `0x833589fCD6eDb6E08f4C7C32D4f71b54bDA02913` | `0x10d6a54a4754c8869d6886b5f5d7fbfa5b4522237ea5c60d11bc4e7a1ff9390b`, `0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3` | different address, same two slot keys |

**Exact requests**, per chain, each required:

1. `eth_chainId []`. The request bytes are identical on both chains; the
   results are `0x1` and `0x2105`.
2. `eth_getBlockByNumber ["0x18d10cd", false]` on both chains. It is the same
   request and it returns two different blocks, `0x1cfd09b6…` and
   `0xf9a59c28…`. It also brackets the Ethereum pin. The Base pin needs
   `["0x313097a", false]`.
3. `eth_getProof [account, slots, block]` for each account.
4. `eth_getCode [account, block]` for each account.
5. `eth_getBlockReceipts [block]`. On Ethereum it feeds the receipt witness if
   one is wanted; on Base it is recorded RPC evidence only (decision 3).

The checks selected the block by number. Lazarus prefers an EIP-1898 hash
selector and falls back to the number; the hash form was not tried on Base.

That is 9 requests per chain, 10 with a closing header read. The planned
records total about 0.65 MB for Ethereum and 0.70 MB for Base
(`evidence/sizes.out`).

**Cross-chain cases** the fixture must carry:

- Same address, same code: Multicall3.
- Same address, different code: Permit2. A proof from one chain must not
  verify for the other.
- Same request, different answer: requests 1 and 2.
- Same slot keys, different accounts: the USDC proxies.

**Mixed-block negative cases** that must be refused:

- A Base proof checked against Ethereum's state root or block hash. All six
  were refused in `evidence/proof_test.out`.
- A result recorded at block N+1 and filed under block N.
- A plan hash that the provider contradicts.
- A result with no block identity.
- A receipt witness declared for chain 8453 while the verifier does not support
  it.

## Compatibility matrix

Checked on 2026-09-30 against `plugins/lazarus` at the revision above. "Works"
means Lazarus's own code ran unmodified on the data, except as stated.

| Lazarus part | Base result | Evidence |
| --- | --- | --- |
| `chain_id` constant | **Blocks.** `"0x1"` is a constant in `plan-v1`, `plan-v2`, `plan-v3`, `header-v1`, `manifest-v1`, `manifest-v2` and `anchor-record-v1`. Chain anchors call `eth_chainId` and require `0x1` (`docs/chain-anchors.md:49`). | `schemas/plan-v3.json:30`, `schemas/header-v1.json:10` |
| Header hash | **Works.** `verify_header` recomputed the hash of 20 Base headers from 2,356,365 to the pin and of the Ethereum pin. The Base headers take every shape seen: 16, 17, 20 and 21 fields, with `extraData` of 0, 9 and 17 bytes. The documents carried `chain_id` `0x1` in memory only, to get past the constant. | `evidence/header_test.out`, 21 of 21 |
| Header fields | Base matches what the verifier expects. At 51,000,000, 51,500,000 and the pin, `withdrawalsRoot` equals the storage hash of the L2ToL1MessagePasser predeploy (`0x4200…0016`). At six blocks from 12,000,000 to the pin, `parentBeaconBlockRoot` equals the `parentBeaconBlockRoot` of the block's L1 origin. The pin's `extraData` is 17 bytes, under the verifier's 32. | `evidence/probe_window.out`, `evidence/roots_test.out` |
| EIP-1186 proofs | **Works.** `verify_proof_record` passed for Multicall3, Permit2 and the USDC proxy with two slots, on both chains. | `evidence/proof_test.out`, 6 of 6 |
| Receipt witness | **Blocks.** Every Base block holds a deposit receipt of type `0x7e`, and Lazarus refuses it: `unsupported receipt type` (`receipts.py:30,46`). The pilot leaves it unsupported (decision 3). | `evidence/receipts_test.out`, 7 of 7 blocks |
| Chain anchors | **Blocks** for the reason in the first row. | `docs/chain-anchors.md` |
| Request identity | **Needs work.** Replay keys are method and parameters, so requests 1 and 2 would collide in a two-chain fixture. A chain-qualified key is an implementation requirement for #1367. Not tested here. | `skills/lazarus/SKILL.md` |
| Proof availability | **Time limit.** The public Base route served `eth_getProof` for the last 30.01 days only, and the second route refused it at once ("distance to target block exceeds maximum proof window"). The pin stays provable there until about 2026-10-21; decision 4 preserves its responses. Headers and receipts were served at every age tested, though the first route refuses `eth_getBlockReceipts` (HTTP 403) and only the second serves it. | `evidence/probe_window.out`, `evidence/receipts_test.out` |

**The deposit receipt.** In the seven Base blocks sampled, a receipt trie built
from the RPC receipts reproduced the header's `receiptsRoot` only with this
payload, behind the type byte `0x7e`:

- blocks 10,000,000 to the pin (five blocks): `rlp([status, cumulativeGasUsed, logsBloom, logs, depositNonce, depositReceiptVersion])`;
- blocks 2,357,105 and 5,000,000: the first four fields only, although the RPC
  already returns `depositNonce`.

The change lies between 5,000,000 and 10,000,000 and was not located. The same
code rebuilt Ethereum's pin root with its `0x0`, `0x2`, `0x3` and `0x4`
receipts, so the method itself reproduces a known root.

## Decisions

1. **Caps.** Proposed, none of them measured as limits: 64 requests in all, 4
   MiB per component, 16 MiB in total, 300 seconds. The planned records are
   about 1.4 MB together.
2. **Subject or venue scope. Decided: subject-scoped.** Dr Laurence E. Day
   accepted the producer's proposal in the delivery session on 2026-09-30
   ("Sure"): three accounts per chain, and no venue slice in the pilot. The
   sizing of Aave V3 on Base, about 243 GB of logs and traces, shows a whole
   venue is not a finite fixture (note on #1486). One 2,000-block window near
   block 50,000,000 held 999 logs in 187 transactions, about 0.73 MB of log
   responses, which is the size of slice a later venue decision would weigh.
3. **Receipt witness on chain 8453. Decided: unsupported for the pilot.** Dr
   Laurence E. Day delegated the choice to the producer in the delivery session
   on 2026-09-30 ("your call"), and the producer chose to leave the witness
   unsupported. On chain 8453 the receipts stay recorded RPC evidence and no
   receipt-trie-proved relation is claimed; a plan that declares a receipt
   witness for chain 8453 must be refused, which is the last mixed-block negative
   case above. Reasons: #1367 asks for multi-block and multi-chain plans, which
   headers and proofs already show; the maintainer has narrowed venue capture to
   mainnet, so no Base relation needs a receipt proof now; and a witness would
   add a chain-specific rule that changes by era. The work is cheap to add later:
   the pin's 165 receipts are preserved (decision 4) and rebuild the header's
   `receiptsRoot` with the six-field payload, so adding `0x7e` becomes a
   separate step with its own test.
4. **Base block and timing. Decided.** Dr Laurence E. Day answered a structured
   question in the delivery session on 2026-09-30 and chose to keep block
   51,579,258 and preserve its raw responses now, over enabling Base on the team
   Alchemy app or moving to a newer block. The question and all three options
   are in the body of the pull request that adds this record.
   [`evidence/base-pin-51579258/`](evidence/base-pin-51579258/) holds ten exact
   request and response pairs: the chain ID, the pinned header, a second header
   at the same block number, proofs and code for the three accounts, and the
   block's 165 receipts. Its `manifest.json` records both digests of each pair.
   `evidence/verify_base_pin.py` checks every digest and then runs Lazarus's
   header and proof verifiers and the receipts-root rebuild on the stored bytes
   without a connection (`evidence/verify_base_pin.out`, all pass). The files
   are not a Lazarus fixture: they are not capture-plan requests, and no plan
   version that admits chain 8453 exists yet.
5. **Secret references.** Names such as `LAZARUS_RPC_ETH` and
   `LAZARUS_RPC_BASE`, passed to `--anchor-rpc-env`. Base is not enabled on the
   team Alchemy app and Wildcat's gateway has no Base route, so a Base provider
   with a long proof window has to be chosen.
6. **Reviewer.** Who reviews this for Lazarus.

## What this does not establish

- That either block is on its chain's canonical history, or that any two
  providers are independent.
- That the Base header fields or receipts follow the OP Stack specification.
  The checks compare them with the chain's own data.
- The Isthmus `withdrawalsRoot` rule at blocks before 51,000,000, where the
  public route serves no proof.
- Any behaviour of Lazarus plan v4, which does not exist yet.
