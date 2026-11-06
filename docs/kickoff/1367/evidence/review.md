# Independent review of chainpilot.md at 8b5eec010

Reviewer: a fresh general-purpose agent (Sonnet 5.5) with no shared context, run on 2026-09-30 against a detached checkout of commit `8b5eec010`. Its brief was read-only work, no credentials, and a verdict of CONFIRMED, NOT CONFIRMED or CANNOT CHECK for each claim. The report below is saved as returned. One closing line that named a local scratch directory is omitted, and the two provider names in the proof-availability bullets are replaced by "first route" and "second route". The Review section of `chainpilot.md` answers each defect. The section labels are headings here, not bold text; the words are unchanged.

## Overall

No high-severity defects. Every numeric claim I could recompute matched, and the digests and preserved bytes check out. Five medium and several low wording or evidence-scope defects remain, listed below.

## Matrix

- `chain_id` constant: CONFIRMED. Exactly seven schemas carry `{"const":"0x1"}` (`plan-v1/v2/v3`, `header-v1.json:10`, `manifest-v1/v2`, `anchor-record-v1.json:55`). `plan-v3.json:30` is correct. The row is incomplete (defect 1).
- Header hash: CONFIRMED for Base. My rerun of the 20 Base rows is byte-identical to `header_test.out` lines 2-21. The Ethereum pin row CANNOT CHECK (no gateway).
- Header fields: PARTLY CONFIRMED.
  - Live on Base, `withdrawalsRoot` equals the L2ToL1MessagePasser `storageHash` at 51,000,000, 51,500,000 and the pin.
  - `header.py:104` has the 32-byte `extraData` cap, and the pin's is 17 bytes.
  - `L1Block.number()` at the pin returns 26,022,078, which matches `roots_test.out`.
  - The `parentBeaconBlockRoot` comparison needs Ethereum: CANNOT CHECK.
- EIP-1186 proofs: CONFIRMED for Base. `verify_base_pin.py` passes 3 of 3 offline. The 3 Ethereum proofs CANNOT CHECK.
- Receipt witness: CONFIRMED. My rerun of all 7 Base rows is byte-identical to `receipts_test.out`. `receipts.py:47` raises "unsupported receipt type", and `:30` is the allowlist.
- Chain anchors: CONFIRMED. `anchor-record-v1.json:55` is a `0x1` constant, and `docs/chain-anchors.md:51` says the chain "must be `0x1`".
- Request identity: CONFIRMED by code. `records.py:24-30` hashes method and params only, and `records.py:62` refuses duplicate keys. The record correctly says this was not tested.
- Proof availability: CONFIRMED.
  - Rerun probe at about 12:22 UTC: head 51,990,800, oldest served 50,694,304, a distance of 1,296,496 blocks (30.011 days).
  - That puts the pin's window end at 2026-10-21T00:00:55Z.
  - The second route returned "distance to target block exceeds maximum proof window" for `eth_getProof`.
  - The first route returned HTTP 403 for `eth_getBlockReceipts`.

## Numbers and digests

- 21 of 21 headers: 20 Base recomputed again; the Ethereum one CANNOT CHECK.
- 6 of 6 proofs: Base offline pass; the 3 Ethereum proofs CANNOT CHECK.
- 6 of 6 negatives: reproduced offline. I used the Ethereum state root and block hash from `plugins/lazarus/examples/wildcat-boundary-v0/probe-v2.json` and `plugins/ariadne/examples/wildcat-datasets-v0/preserved/v2/coverage.json:33`.
- 7 of 7 receipts roots: reproduced. The six-field payload matches from 10,000,000 and the four-field payload at 2,357,105 and 5,000,000.
- `sizes.out` totals (653,725 and 697,825 B) sum from their components, and the 9 requests per chain arithmetic holds (1+1+3+3+1).
- `probe_window.out` arithmetic holds: 1,296,286 blocks is 30.0066 days, and 20.73 days remain.
- `verify_base_pin.py base-pin-51579258` exits 0. Its output is identical to `verify_base_pin.out`.
- All 10 request/response pairs match `manifest.json`, and `shasum -c SHA256SUMS` reports no failures.
- `SHA256SUMS` lists 37 files, with none missing or extra. Its own digest is `a8c1bfbe…40b7f6`, as cited.
- The header hash is `0x0366446f…f611d`.
- A live header fetch returned 13,167 bytes identical to `02-header.response.json`, so the response was not re-serialised.
- All 10 request files equal the canonical compact JSON rebuilt from the manifest, and every `response_bytes` value matches its file. Responses 01-09 end in a newline and response 10 does not.
- Base block 51,579,259 has timestamp 1789947865, which supports "last block not after" the Ethereum timestamp.
- The Ethereum pin's hash, timestamp (1789947863) and 216 transactions appear in the repo example files cited above.

## Defects, ranked

1. Medium, `chainpilot.md:99`. The "Blocks" row omits two more Ethereum-only constants. `network: "ethereum-mainnet"` is at `plan-v1.json:16`, `plan-v2.json:32` and `plan-v3.json:33`. A literal `"chain_id": "0x1"` is at `capture.py:936`. Fix: name both in the row.
2. Medium, `:103`. "Every Base block holds a deposit receipt" is universal, but the evidence is 7 sampled blocks. Fix: "Each of the 7 sampled".
3. Medium, `:70`. "9 requests per chain, 10 with a closing header read" does not fit Base. Base needs both `0x18d10cd` and `0x313097a`, which is 10 requests (the manifest has 10), or 11 with a closing read. Fix: state Ethereum 9 and Base 10.
4. Medium, `:129-131` and `:148,160-161`. The 243 GB figure, the 999 logs in 187 transactions, the 0.73 MB and the Alchemy and gateway statements have no file in `evidence/`. No pool address or block window is named either. Fix: add the script and output, or mark them unverified.
5. Medium, `:101`. "Base matches what the verifier expects" is wrong, because Lazarus checks neither the `withdrawalsRoot` rule nor the L1-origin `parentBeaconBlockRoot`. `roots_test.out:1-5` also prints `False` (proofs unserved), and the record cites that file as support. Fix: call these observations not checked by Lazarus, and annotate those lines.
6. Low, `:99`. `chain-anchors.md:49` does not contain `0x1`. Fix: cite line 51.
7. Low, `:103`. `receipts.py:46` is the condition. The message is at `:47`.
8. Low, `:106`. The probe's own projection is 2026-10-20 23:53:55 UTC, and my rerun gives 2026-10-21 00:00:55 UTC. The window edge shifted by 210 blocks (about 7 minutes) between probes. Fix: "about 2026-10-21 00:00 UTC, ±10 min". The 403 and the proof-window error string are in no evidence file.
9. Low, `:171`. "Blocks before 51,000,000, where the route serves no proof" is inaccurate. Proofs were served from 50,683,549, and I found 50,694,304 later. Fix: "not tested below 51,000,000".
10. Low, `:154-155`. The receipts-root rebuild is `verify_base_pin.py`'s own code, not Lazarus's, because Lazarus refuses `0x7e`.
11. Low, `:12-13`. "Second largest chain by stablecoin activity" is stated as fact with no source. Fix: attribute it to the decision comment.
12. Low, `:42`. `header_test.py` never compares the Ethereum pin's recomputed hash to `0x1cfd09b6…`, and the hash appears in no evidence file.

I found no internal inconsistency in who decided what. Three open items (Decisions 1, 5, 6) match "three items below".

## Item 4 scan

The evidence folder holds no URL, credential, bearer token, absolute user path or provider host name. What it does hold:
- `common.py:5,8,14,23`: env var names `ALEXANDRIA_COMPOUND_RPC_URL` and `ALEXANDRIA_RPC_BEARER`, and the `"Bearer "` header code, with no value.
- `common.py:13` and `preserve_base_pin.py:29`: a `curl/8.7.1` user-agent string.
- `05-code-multicall3.response.json` and `09-code-usdc.response.json`: a Solidity metadata `ipfs` key inside decoded bytecode.
- The manifest `route` fields read "primary" and "receipts".

## Gaps

- No done condition or acceptance run for the pilot.
- `lazarus.py:68` takes a single `--rpc-url`, but the Base set used two routes. The chosen provider must serve both `eth_getProof` inside the window and `eth_getBlockReceipts`; Decision 5 names only the proof window.
- Nothing says how the preserved bytes become a fixture if the window closes (about 2026-10-21) before a provider is chosen.
- Schema versioning and downstream consumers of chain ID (for example `binding.py:693-697`) are not listed. Neither are version bumps or Promise Machine re-pins.
- Fixture layout for two chains is not stated.
- Replay chain selection is not stated.
- Which sources could anchor an L2 is not stated.
- Policy for new OP header fields in future forks is not stated.

## Not checked

- All Ethereum reads: the pin header, proofs, sizes, receipts and the L1-origin comparison.
- The decision comment, the "Sure" and "your call" quotes, and the pull-request body.
- The Wildcat gateway and Alchemy claims.
- The Base live reruns of `proof_test.py` and `sizes.py`. I checked the proofs offline instead.
- The hash-selector form on Base.
- Repository lints and `run_checks.py`.
