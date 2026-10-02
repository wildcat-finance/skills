# Two-chain Lazarus pilot: draft plan and compatibility matrix

Issue: https://github.com/wildcat-finance/skills/issues/1486, a prerequisite
child of https://github.com/wildcat-finance/skills/issues/1367.

**Status: draft.** An independent agent has reviewed it
([`evidence/review.md`](evidence/review.md)) and all six decisions below are
made. Nothing here is a capture: no fixture was built, and the checks only read
chain data.

## Decision and custody

- **Decision.** Dr Laurence E. Day decided on 2026-09-30 that Base (chain ID
  8453) is the second chain, after Ethereum mainnet. His stated reason is that
  Base is the second largest chain by stablecoin activity, which this record
  does not check. He also said venue capture on other chains is out of focus. The
  [decision comment](https://github.com/wildcat-finance/skills/issues/1486#issuecomment-5904174727)
  records both.
- **Producer.** Claude Code, in the delivery session of 2026-09-30, from Skills
  `87b1dd072124dc75ba83df4ca1ee5e6c1ccf57ba`.
- **Reviewer.** An independent agent, chosen by Dr Laurence E. Day on 2026-09-30
  (decision 6): a fresh Sonnet 5.5 agent with no shared context, run on commit
  `8b5eec010`. Its report is [`evidence/review.md`](evidence/review.md), and the
  Review section below answers each defect.
- **Evidence.** [`evidence/`](evidence/) holds the scripts and their output.
  `evidence/SHA256SUMS` lists each file's SHA-256, and its own SHA-256 is
  `b93cf3a783c125d64377daf756c9a8ff11c83b3787c7ccab88b43abfaf6ad197`.
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
  issues. The hash is in
  `plugins/lazarus/examples/wildcat-boundary-v0/probe-v2.json:97` and
  `plugins/ariadne/examples/wildcat-datasets-v0/preserved/v2/coverage.json:33`.
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

That is 9 requests on Ethereum and 10 on Base, where the same-number header
read is the extra one; a closing header read adds one to each. The planned
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
| `chain_id` constant | **Blocks.** `"0x1"` is a constant in `plan-v1`, `plan-v2`, `plan-v3`, `header-v1`, `manifest-v1`, `manifest-v2` and `anchor-record-v1`. Chain anchors call `eth_chainId` and require `0x1` (`docs/chain-anchors.md:51`). `network` is the constant `ethereum-mainnet` in `plan-v1`, `plan-v2` and `plan-v3`, and `capture.py:936` writes a literal `"chain_id": "0x1"`. | `schemas/plan-v3.json:30,33`, `schemas/header-v1.json:10`, `plan-v1.json:16`, `plan-v2.json:32`, `capture.py:936` |
| Header hash | **Works.** `verify_header` recomputed the hash of 20 Base headers from 2,356,365 to the pin and of the Ethereum pin, each against the hash its node returned. The Ethereum pin constant comes from the repo files cited above. The Base headers take every shape seen: 16, 17, 20 and 21 fields, with `extraData` of 0, 9 and 17 bytes. The documents carried `chain_id` `0x1` in memory only, to get past the constant. | `evidence/header_test.out`, 21 of 21 |
| Header fields | **Observed; Lazarus checks neither rule.** At 51,000,000, 51,500,000 and the pin, `withdrawalsRoot` equals the storage hash of the L2ToL1MessagePasser predeploy (`0x4200…0016`). At six blocks from 12,000,000 to the pin, `parentBeaconBlockRoot` equals the `parentBeaconBlockRoot` of the block's L1 origin. The pin's `extraData` is 17 bytes, under the verifier's cap of 32 (`header.py:104-105`). `roots_test.out` prints `False` for `withdrawalsRoot` at 12,000,000 and 30,000,000, where the field is the empty-trie root before Isthmus, and at 35,000,000, 41,000,000 and 47,500,000, where the route served no proof. The `True` results are in `probe_window.out`. | `evidence/probe_window.out`, `evidence/roots_test.out` |
| EIP-1186 proofs | **Works.** `verify_proof_record` passed for Multicall3, Permit2 and the USDC proxy with two slots, on both chains. | `evidence/proof_test.out`, 6 of 6 |
| Receipt witness | **Blocks.** Each of the 7 sampled Base blocks holds a deposit receipt of type `0x7e`, and Lazarus refuses it: `unsupported receipt type` (`receipts.py:30,46-47`). The pilot leaves it unsupported (decision 3). | `evidence/receipts_test.out`, 7 of 7 blocks |
| Chain anchors | **Blocks** for the reason in the first row. | `docs/chain-anchors.md` |
| Request identity | **Needs work.** Replay keys are method and parameters, so requests 1 and 2 would collide in a two-chain fixture. A chain-qualified key is an implementation requirement for #1367. Not tested here. | `skills/lazarus/SKILL.md` |
| Proof availability | **Time limit.** The public Base route served `eth_getProof` for the last 30.01 days only, and the second route refused it at once ("distance to target block exceeds maximum proof window"). The pin stays provable there until about 2026-10-21 00:00 UTC, give or take 10 minutes; decision 4 preserves its responses. A reviewer's rerun found 30.011 days. Headers and receipts were served at every age tested, though the first route refuses `eth_getBlockReceipts` (HTTP 403) and only the second serves it. No evidence file keeps the two refusal messages. | `evidence/probe_window.out`, `evidence/receipts_test.out` |

**The deposit receipt.** In the seven Base blocks sampled, a receipt trie built
from the RPC receipts reproduced the header's `receiptsRoot` only with this
payload, behind the type byte `0x7e`:

- blocks 10,000,000 to the pin (five blocks): `rlp([status, cumulativeGasUsed, logsBloom, logs, depositNonce, depositReceiptVersion])`;
- blocks 2,357,105 and 5,000,000: the first four fields only, although the RPC
  already returns `depositNonce`.

The change lies between 5,000,000 and 10,000,000 and was not located. The same
code rebuilt Ethereum's pin root with its `0x0`, `0x2`, `0x3` and `0x4`
receipts, so the method itself reproduces a known root. The rebuild uses the scripts' own
encoder on top of Lazarus's RLP and trie code, because Lazarus refuses `0x7e`.

## Decisions

1. **Caps. Decided.** Dr Laurence E. Day accepted the producer's proposal in
   the delivery session on 2026-09-30 ("yes"): 64 requests in all, 4 MiB per
   component, 16 MiB in total and 300 seconds. None is a measured limit. The plan
   needs 9 requests on Ethereum and 10 on Base and about 1.4 MB of records, and its largest
   record is the Base receipts at 0.62 MB.
2. **Subject or venue scope. Decided: subject-scoped.** Dr Laurence E. Day
   accepted the producer's proposal in the delivery session on 2026-09-30
   ("Sure"): three accounts per chain, and no venue slice in the pilot. The
   sizing of Aave V3 on Base, about 243 GB of logs and traces, shows a whole
   venue is not a finite fixture
   ([note on #1486](https://github.com/wildcat-finance/skills/issues/1486#issuecomment-5904490053)).
   One 2,000-block window from block 50,000,000 held 999 logs in 187
   transactions, about 0.73 MB of log responses, which is the size of slice a
   later venue decision would weigh. Both figures come from the delivery
   session's sizing run and this folder keeps no output for them.
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
5. **Secret references. Decided.** Dr Laurence E. Day chose `LAZARUS_RPC_ETHEREUM`
   and `LAZARUS_RPC_BASE` in the delivery session on 2026-09-30: one environment
   variable per chain, named for the plugin and not a provider. Anchor sources
   follow `LAZARUS_ANCHOR_<CHAIN>_<SOURCE>`, passed through `--anchor-rpc-env`.
   No URL or key is written to a record. The pin no longer needs a Base provider
   (decision 4). A capture of a newer Base block will: the team Alchemy app had
   Base disabled and Wildcat's gateway had no Base route when read on
   2026-09-30, and this folder keeps no output for either.
6. **Reviewer. Decided: an independent agent.** Dr Laurence E. Day chose it in
   the delivery session on 2026-09-30 from three options: an independent agent,
   himself, or no named reviewer for now. The report is
   [`evidence/review.md`](evidence/review.md).

## Review

The reviewer found no high-severity defect, five medium and seven low. Numbers,
digests and preserved bytes matched on every rerun it made. It did not check the
Ethereum gateway reads, the decision comment or the pull request body. Its report
is [`evidence/review.md`](evidence/review.md).

| Defect | Severity | Disposition |
| --- | --- | --- |
| 1. Matrix row missed `network` and `capture.py:936` | medium | Fixed: both named in the first row. |
| 2. "Every Base block" from 7 samples | medium | Fixed: "each of the 7 sampled". |
| 3. Request count wrong for Base | medium | Fixed: 9 on Ethereum, 10 on Base. |
| 4. Sizing, window, Alchemy and gateway claims had no file | medium | Marked as session observations with no output kept; the sizing links to its note. No file added. |
| 5. "Base matches what the verifier expects" | medium | Fixed: observed, and Lazarus checks neither rule; the `False` lines are explained. |
| 6. Wrong line for `0x1` in `chain-anchors.md` | low | Fixed: line 51. |
| 7. `receipts.py` message line | low | Fixed: `46-47`. |
| 8. Proof-window edge imprecise | low | Fixed: 2026-10-21 00:00 UTC, give or take 10 minutes. |
| 9. "Route serves no proof before 51,000,000" | low | Fixed: not tested below 51,000,000. |
| 10. Receipts rebuild is the scripts' own code | low | Fixed: stated beside the deposit receipt. |
| 11. Stablecoin reason stated as fact | low | Fixed: attributed to the decision-maker. |
| 12. Ethereum pin hash not compared in the evidence | low | Fixed: the hash is cited to two repo files. |

The reviewer's gaps are listed next as requirements.

## Requirements for #1367

These follow from the matrix and the review. Each is implementation work, not a
capability this record supplies.

- Generalise the Ethereum-only constants: `chain_id` in seven schemas, `network`
  in three plan schemas and the literal at `capture.py:936`. Fixtures that
  verify today must still verify.
- Make the replay request identity chain-qualified: `records.py:24-30` hashes the
  method and parameters only.
- Define chain anchors for an L2. `docs/chain-anchors.md:51` requires `0x1`, and
  nothing says which sources could anchor a Base block.
- Require one provider per chain to serve `eth_getProof` inside its proof window
  and `eth_getBlockReceipts`. `capture` takes a single `--rpc-url`
  (`lazarus.py:68`), and the Base checks needed two routes.
- Add a path from preserved exact responses to a fixture. The pin's responses
  exist and no plan version admits chain 8453.
- State the two-chain fixture layout and how replay picks a chain. Review
  consumers of the chain ID such as `binding.py:693-697`, plan version bumps and
  Promise Machine re-pins.
- Decide how later OP Stack header fields are admitted, and add receipt type
  `0x7e` as its own step (decision 3).

**Pilot done when** a plan version that admits both chains verifies a fixture
spanning them offline, every cross-chain case and negative case above behaves as
stated, and a fixture that verifies today still does. This follows #1367's own
done condition.

## What this does not establish

- That either block is on its chain's canonical history, or that any two
  providers are independent.
- That the Base header fields or receipts follow the OP Stack specification.
  The checks compare them with the chain's own data.
- The Isthmus `withdrawalsRoot` rule at blocks before 51,000,000, which were not
  tested.
- Anything the Ethereum gateway supplied, which the independent reviewer could
  not rerun: the pin header, the three Ethereum proofs and the L1-origin
  comparison.
- Any behaviour of Lazarus plan v4, which does not exist yet.
