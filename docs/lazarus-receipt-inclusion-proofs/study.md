# Study: prove receipts against the captured header's `receiptsRoot`

Assuming, unless corrected:

- The delivery is limited to open held job [#383](https://github.com/wildcat-finance/skills/issues/383) and the exact Lazarus evolution-ledger entry it mirrors.
- The fixed Goldfinch block, transaction receipt, and filtered log request are the first working case. The design may be reusable, but success does not require proving every kind of receipt ever accepted by Ethereum.
- A receipt-trie proof covers consensus receipt fields only. RPC decorations such as `from`, `to`, `contractAddress`, `gasUsed`, and `effectiveGasPrice` remain recorded provider responses unless another proof covers them.
- Existing `goldfinch-v0`, manifest-v1, release-v1, and Ariadne state-fixture/v1 bytes remain valid and unchanged. New claims use new registered format versions.
- The source RPC records remain `recorded_rpc` evidence even when a derived relation is proved from them. The new relation receives its own evidence class rather than rewriting source provenance.
- The capture command may make one more bounded standard RPC request for the fixed block. Verification and release checks remain offline.
- Completion includes the ledger-mandated cold read and reconciliation of mutable first-party marketplace prose; it does not include unrelated held jobs or audit leads.

## 1. Problem statement

Lazarus preserves the Goldfinch fixture's block header, one transaction receipt, and one block-hash-and-address `eth_getLogs` response. The verifier recomputes the header hash, so the header's `receiptsRoot` is bound to the captured block. It does not reconstruct the receipts trie. The named receipt and its five selected logs therefore still rest on the RPC provider's response even though the fixture already holds the commitment that can check them.

The prototype must add an offline, fail-closed path from an ordered set of block receipts to the captured `receiptsRoot`. It must then bind two exact derived claims:

1. the target transaction's consensus receipt payload and all 110 receipt logs occupy transaction index `0xbf` in that trie; and
2. filtering all proved block logs by the existing block hash and Goldfinch address yields exactly the five recorded `eth_getLogs` entries, in Ethereum log order.

For the fixed block `0xc7da16` (`0x41119192...2cfc`), the header lists 224 transaction hashes and the target hash is `0xa46a744d...ce699`. Success means a fresh, versioned fixture and release verify offline; a one-byte receipt, index, log, or root mutation fails; old examples still verify byte-for-byte; and Ariadne can state the new proof count without presenting ordinary RPC fields as proved.

The implementation is accepted only when these commands are green from the repository root in the locked dependency environment:

```text
python3 plugins/lazarus/tests/run_tests.py --elenchus-report .hexaemeron/lazarus-elenchus-report.json
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
python3 -m unittest discover -s tests
python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/examples/goldfinch-v1
python3 plugins/lazarus/scripts/lazarus.py verify-release plugins/lazarus/examples/goldfinch-v1-release
python3 scripts/promise_machine.py check
```

The runbook must also name the exact Ariadne capture and `verify` commands after it selects the new statement path, and the final proof must include the repository-required prose checks over every changed document.

## 2. Prior art

### Repository code and records

- Lazarus already verifies account and storage Merkle-Patricia proofs in `plugins/lazarus/scripts/lazarus_lib/trieproof.py`, encodes RLP in `rlp.py`, binds the complete header including `receiptsRoot` in `header.py`, derives evidence counts in `manifest.py`, and checks release-to-fixture equality in `release.py`. Receipt work should reuse those bounded readers, hash functions, and registry patterns rather than introduce a second trie stack.
- `plugins/lazarus/examples/goldfinch-v0/plan.json` fixes the block hash, receipt transaction hash, and exact `eth_getLogs` filter. Its manifest reports `proof_backed: 2`, `header_bound: 1`, and `recorded_rpc: 4`. The receipt record has 110 logs; the separate filtered record has five logs, all drawn from that receipt.
- Ariadne state-fixture/v1 already carries a `state_root` plus evidence counts. Its schema, predicate module, capture adapter, and conformance fixtures form one interface and must move together for a state-fixture/v2 receipt-root claim.
- [Lazarus evolution ledger](../../plugins/lazarus/skills/lazarus/EVOLUTION.md) names this exact frontier and says no other recorded RPC response moves into a proved class. [Ariadne evolution ledger](../../plugins/ariadne/skills/ariadne/EVOLUTION.md) has a different held frontier; this delivery changes only the state-fixture interface needed by #383 and must not claim that frontier.

### Last two merged delivery pull requests

- [PR #623, “Record structured multi-provider Lazarus chain anchors”](https://github.com/wildcat-finance/skills/pull/623), merged 2026-08-25 at integration commit `e2200b6...`, kept receipts and logs in `recorded_rpc` and carried #383 forward. It also kept canonical-chain and provider-independence claims outside the evidence boundary.
- [PR #227, “Lazarus: the first end-to-end Goldfinch preservation release”](https://github.com/wildcat-finance/skills/pull/227), merged 2026-08-20 at `569f4a3...`, established release binding, count recomputation, and the rule that a release cannot silently upgrade a manifest. Its audit and delivery notes state that receipts and logs were recorded, not trie-proved. The old release digest is therefore historical evidence, not a file to regenerate.

### Audit records and read mode

The whole-set synopsis check passed before this study: `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check "$TARGET"` exited 0.

- [Root audit](../../audit/AUDIT.md) was read through its verified [synopsis](../../audit/AUDIT_SYNOPSIS.md): source SHA-256 `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`, synopsis SHA-256 `b9fe6925729395a72433e0f5918ddba785cc1905b2acc8926a94a6a23b1bc6e6`. Relevant rounds 123 to 142 cover Ariadne state-fixture work; rounds 143 to 162 cover the Goldfinch release. Prior fixes require a nonzero committed root when a proved count is positive, parity between schema and predicate code, bounded component paths, and manifest/release count cross-checks. Older fixture omissions remain unknown rather than being inferred.
- [Fiat-386 audit](../../audit/rounds/fiat-386-record-a-structured-multi-provider-chain-anc.md) was read through its verified synopsis: source SHA-256 `e1da4b8ebfd08d7d6d0a1a3470c86034b8080139f41b1134bb3dc69c952abad2`, synopsis SHA-256 `c21dcbd056fde4bbab7ec93aa1159df20a863ccf484feab2266a8f378030a3e3`. Three rounds reported no finding. Its carried constraints are secret handling, shared RPC budgets, atomic finalisation, and release compatibility.
- [Ariadne audit](../../plugins/ariadne/audit/AUDIT.md) was read through its verified synopsis: source SHA-256 `d8d13eb238b6e270fb9f89ec11fea797b4a3aa27025b5a62a7f36ac2642617af`, synopsis SHA-256 `53aacbb59bc9bc1455ce580ce484cbcb16802f7faa41b2b12f65c3ce614d1b4a`. Its 21 initial rounds contain no receipt-specific finding; the applicable result is to retain its input, schema, replay, and gate boundaries.

### Organisation and outside sources

No other first-party implementation proves receipt inclusion. Ariadne consumes Lazarus evidence after release; it must not reconstruct chain state itself. This is the named marketplace hand-off.

The official Execution API defines [`eth_getBlockReceipts`](https://ethereum.github.io/execution-apis/api/methods/eth_getBlockReceipts/) for one block and [`debug_getRawReceipts`](https://ethereum.github.io/execution-apis/api/methods/debug_getRawReceipts/) as a debug-namespace alternative. [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) fixes trie keys as `rlp(transactionIndex)` and distinguishes legacy RLP receipts from typed envelopes; [EIP-658](https://eips.ethereum.org/EIPS/eip-658) replaces the pre-Byzantium intermediate-state field with status. The study pins the consulted Execution APIs tree at `7c58b324fb924e1da18e089890bb2c25cc45c143` and the consulted EIPs tree at `ac450a4ab2f37387385ee9c54b62f518d97e6cc9`.

One bounded observation against `https://ethereum-rpc.publicnode.com` on 2026-08-26 found that `eth_getBlockReceipts` accepted the fixed block hash and returned 224 receipts in 579,013 response bytes over 0.566927 seconds. Receipt `0xbf` contained the expected 110 logs. This records feasibility for one provider at one time; it is not a service, latency, or availability promise.

## 3. Constraints and non-goals

The run starts from synced `main` at `5489863196006d8e8b45799d74b56208cac65e4d` in the dedicated Fiat worktree. That commit is the implementation and audit baseline; later base advancement is handled only through Fiat's signed integration-sync transition.

**Always:**

- Bind the witness to the already hash-checked header and compare the recomputed root to its exact `receiptsRoot`.
- Require one receipt for every header transaction, with unique contiguous indices, matching block hash, matching block number, and matching transaction hash at each index.
- Encode receipt consensus data canonically: legacy `[status-or-root, cumulativeGasUsed, logsBloom, logs]`, or a supported EIP-2718 type byte followed by its defined RLP payload. Reject booleans, non-canonical quantities, unknown fields needed for encoding, unsupported receipt types, and ambiguous pre-Byzantium data.
- Preserve ordered logs, including address, topics, data, transaction index, and log index links. Compare the recorded filtered result as an exact ordered projection of the proved full-block log set.
- Keep raw receipt and log RPC records classified as `recorded_rpc`; add a distinct derived class, provisionally `receipt_trie_proved`, for relations established by the witness.
- Use new registered versions for every changed wire shape. Readers for old plan, manifest, release, and Ariadne statement versions remain available and their fixtures remain unchanged.
- Share existing byte, count, depth, timeout, and atomic-write controls. A partial capture must not replace a valid fixture or release.
- Before ledger completion, cold-read and reconcile all mutable first-party marketplace prose, record what was read, and run the applicable Imprimatur, Brevitas, Phylax, Ephoros, and Hypomnema checks named by repository policy.

**Ask first:**

- Changing the issue's evidence boundary, renaming an existing evidence class, rewriting a published release, adding a runtime dependency, or treating a provider quorum as canonical-chain proof.
- Supporting receipt formats outside those required by the fixed block when that support changes the receipt decoder's accepted inputs or trust boundary.
- Moving an unrelated Ariadne, Lazarus, or framework lead into this delivery.

**Never:**

- Claim that `receiptsRoot` proves RPC-only decorations, canonical-chain selection, provider independence, transaction execution, or any RPC response outside the named receipt and exact log filter.
- Accept a target-only proof as evidence that a filtered log response is complete for the block.
- Fetch from the network during fixture verification, release verification, Ariadne verification, or test replay.
- Make success depend on `debug_*`, archive-node policy, ambient credentials, or an unpinned package.
- Close #383, advance either evolution ledger, publish an issue/comment, push, or merge from the study phase.

## 4. Design options

### Option A: compact proof for the target receipt

Capture the target receipt plus the trie nodes on its path. This has the smallest fixture delta and directly proves membership at index `0xbf`. It cannot prove that the five-address-filtered logs are complete, because unseen receipts may contain another matching log. Adding non-membership arguments for every other possible matching log is not expressible as one compact receipt-membership path.

### Option B: full ordered block-receipt witness (chosen)

Capture `eth_getBlockReceipts` by the fixed block hash, validate the returned set against all 224 header transactions, encode every consensus receipt, and rebuild the hexary receipts trie. Store a versioned witness containing the bounded source fields needed for offline reconstruction. After the root matches, derive the target receipt relation and the exact filter relation from the proved set.

This design spends fixture size and one bounded capture request to obtain both membership and filtered-log completeness. The observed JSON response was about 579 KB, within the repository's existing bounded-artifact model. It also uses the already pinned `rlp` and `trie` packages in tests while keeping production verification within Lazarus's existing RLP/trie code. The trade is accepted because completeness is the issue's second half; omitting it would leave the log claim on the provider's word.

### Option C: raw receipts from the debug namespace

Capture `debug_getRawReceipts` and rebuild the trie from byte strings. This avoids translating JSON fields back into consensus receipt bytes, but it shifts capture onto an optional debug method, still requires ordered transaction/index binding and log decoding, and weakens provider portability. Keep this as a diagnostic fallback, not the delivered interface.

### Option D: replay every transaction in the block

Re-execute the block and derive receipts locally. That could produce the same root without trusting receipt RPC bytes, but it imports an execution client, historical state, fork rules, and a much larger preservation boundary. It is outside #383.

The selected wire plan is `plan-v3` plus `receipt-witness-v1`, `manifest-v2`, and `release-v2`; Ariadne receives state-fixture/v2 with `chain.receipts_root` and `evidence.receipt_trie_proved`. Names are provisional until the runbook confirms no registry collision. A positive receipt-trie count requires a nonzero `receipts_root`; a zero count does not borrow authority from `state_root`. The Lazarus writer version moves because it emits new formats, while every legacy reader remains pinned.

## 5. Risk register seed

```risk-register
receipt-set-completeness | provider can omit, duplicate, or reorder block receipts | require exactly one contiguous index and matching transaction hash for every header transaction before trie construction
receipt-rlp-encoding | JSON receipt fields can be translated into different bytes than consensus encoded | use canonical quantity and byte decoders plus root-vector tests against the captured header
typed-receipt-prefix | a typed receipt can be encoded as legacy RLP or accepted under an unknown type | prefix supported EIP-2718 receipts exactly once and reject unrecognised types
header-root-binding | a valid witness can be paired with a different stored header | recompute the header hash and compare both block identity and receiptsRoot in one verification path
transaction-index-binding | a receipt can be valid at one trie key but attributed to another transaction | compare index, transaction hash, block hash, and header transaction slot before insertion
log-query-completeness | target membership alone cannot show an address-filtered result is exhaustive | filter the complete proved receipt set and compare the full ordered result byte-for-byte
metadata-overclaim | RPC-only decorations can inherit the receipt proof label | define consensus fields and derived relations explicitly and keep decorations recorded_rpc
evidence-count-upgrade | a manifest or Ariadne statement can claim proof without a verified relation | derive counts from verified components and require a nonzero receipts root for a positive count
legacy-format-compatibility | new schemas can silently reinterpret a published v0 fixture or release | register new versions and run unchanged legacy fixtures through old readers
provider-response-bounds | full-block receipt JSON can exhaust time, bytes, nesting, or count limits | apply shared request budgets and cap bytes, depth, receipt count, logs, topics, and field lengths before allocation
atomic-capture | interruption can leave a mixed old-and-new fixture | validate in staging and replace the destination only after every digest and root check passes
release-binding | a release can carry a witness or count absent from its source fixture | recompute fixture digest, component inventory, evidence counts, and statement inputs during verify-release
ariadne-schema-parity | state-fixture schema and predicate code can disagree about receipt fields | add paired acceptance and rejection vectors to schema-agreement and conformance tests
marketplace-prose-drift | registries and public prose can describe the old evidence classes after code moves | cold-read the mutable first-party surfaces and gate the exact changed bytes before ledger completion
```

## 6. Glossary seeds

- **Receipt consensus payload:** The four-item receipt payload committed by Ethereum: status or pre-Byzantium root, cumulative gas used, logs bloom, and ordered logs.
- **Typed receipt envelope:** An EIP-2718 receipt type byte followed by that type's receipt payload; the envelope bytes, not an RLP list wrapping them, are stored as the trie value.
- **Legacy receipt:** A receipt whose trie value is the RLP encoding of the receipt payload without a type prefix.
- **Receipt key:** `rlp(transactionIndex)`, used as the key in the receipts Merkle-Patricia trie.
- **Receipt witness:** The bounded, versioned, ordered receipt data from which the offline verifier reconstructs every trie value and the root.
- **Receipt-trie-proved relation:** A derived statement whose receipt or filtered logs were checked against the captured header's `receiptsRoot`.
- **Recorded RPC:** A preserved provider response whose bytes and request are bound to the fixture but whose truth is not established by an Ethereum state or receipt commitment.
- **Filtered-log completeness:** Equality between the recorded `eth_getLogs` output and the ordered projection obtained by applying the same block/address/topics filter to every proved receipt log in that block.
- **RPC decoration:** A receipt response field not included in the consensus receipt payload, such as sender, destination, effective gas price, or contract address.
- **Historical release:** A published fixture/release pair whose bytes and digest stay fixed after a new format is introduced.

## 7. Sources

The implementation and runbook should use these pinned or repository-local sources:

- [Issue #383](https://github.com/wildcat-finance/skills/issues/383) and the exact [Lazarus evolution entry](../../plugins/lazarus/skills/lazarus/EVOLUTION.md).
- [Lazarus skill contract](../../plugins/lazarus/skills/lazarus/SKILL.md), [Ariadne skill contract](../../plugins/ariadne/skills/ariadne/SKILL.md), and the suite [Promise Machine](../../PROMISE_MACHINE.md).
- Lazarus verifier, header, RLP, trie-proof, manifest, release, binding, capture, records, schema, and version modules under `plugins/lazarus/scripts/lazarus_lib/`.
- Ariadne state-fixture predicate and capture modules, their schemas, and their conformance/schema-agreement tests under `plugins/ariadne/`.
- Existing Goldfinch plan, fixture, release, and audit records described in section 2.
- Execution APIs commit `7c58b324fb924e1da18e089890bb2c25cc45c143`: [`eth_getBlockReceipts`](https://ethereum.github.io/execution-apis/api/methods/eth_getBlockReceipts/) and [`debug_getRawReceipts`](https://ethereum.github.io/execution-apis/api/methods/debug_getRawReceipts/).
- EIPs commit `ac450a4ab2f37387385ee9c54b62f518d97e6cc9`: [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) and [EIP-658](https://eips.ethereum.org/EIPS/eip-658).
- Exact runtime pins already present in Lazarus: `eth-hash[pycryptodome]==0.7.1`, `jsonschema==4.25.1`, `rlp==4.1.0`, and `trie==3.1.0`; Python floor 3.11.

The ambient interpreter observed during study was Python 3.12.3 and lacked the locked `Crypto` module. That is an environment fact, not license to loosen the lock; implementation tests run in the repository's installed locked environment.

## 8. Signals, and the questions behind them

[Ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) applies because capture runs unattended against an external RPC endpoint and a failure must be diagnosable from preserved output.

Operators need answers to four questions without exposing receipt bodies or credentials:

1. Which fixed block, transaction index, and transaction hash was being checked?
2. Did capture stop on transport, response bounds, receipt-set binding, receipt encoding, root equality, filtered-log equality, staging, or release binding?
3. What were the bounded counts: header transactions, returned receipts, encoded receipts, total logs, selected logs, and derived proof relations?
4. Which format versions, expected root, computed root, fixture digest, and release digest took part?

The command should emit one structured terminal result with a correlation identifier carried through capture, witness construction, fixture verification, release verification, and Ariadne capture. Counters belong at those boundaries; values that expose credentials, full receipt data, log data, or provider response bodies do not. A mismatch is an error with the stage and safe identifiers. Alerts are warranted only for a scheduled capture/release job that fails or cannot complete atomically, not for an expected rejection in a mutation test.

## 9. Boundaries, per capability

[Phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) governs the off-chain inputs and subprocess/file boundaries.

- **RPC capability:** The endpoint, headers, and JSON response are untrusted. Use the repository secret path and redaction rules, fixed method allowlist, fixed block hash, shared timeout/request/byte budgets, strict JSON decoding, and no debug-method fallback. Do not interpolate provider data into a shell command.
- **Receipt decoder:** Quantities, hex bytes, arrays, receipt types, log counts, topic counts, and nesting are hostile inputs. Decode through bounded canonical helpers, reject duplicate/unknown structural ambiguity, and allocate only after limits pass.
- **Evidence promotion:** A provider response becomes receipt-trie-proved only after header identity, full-set transaction binding, canonical encoding, root equality, and exact query projection all pass. Any failed stage leaves the source recorded and the proved count at zero.
- **Filesystem:** Build the witness, manifest, statement, and release in a staging directory under the destination parent; reject symlink/path escape; fsync or use the repository's established atomic replacement path; retain the last valid artefact on failure.
- **Release and Ariadne:** Both consume local verified files. They may recompute digests and counts but must not fetch, infer a canonical chain, or upgrade a v1 statement. Schema/module/capture parity is checked with shared vectors.
- **Dependencies and subprocesses:** Add no package. Invoke repository scripts with argument arrays in tests; retain exact dependency pins and Python floor. Generated test reports stay within the worktree and are size-bounded.
- **Marketplace prose:** Treat public manifests and prose as release inputs. Discover the mutable first-party set from repository-owned registries, cold-read it, edit only claims affected by the new class/version, and run the mandated prose/tree checks on exact bytes.

## 10. The budget, or its absence

[Metron](../../plugins/hexaemeron/skills/metron/SKILL.md) does not authorise a speed or size improvement here because #383 names an evidence gap, not a performance regression. There is no before/after performance claim to accept.

Safety budgets still apply: one added fixed-block request, bounded response bytes, at most the header transaction count in receipts, bounded logs/topics/field lengths, existing network timeout/retry limits, and no network work during verification. The 579,013-byte, 0.566927-second public-node observation is a feasibility datum only. The runbook must record the exact existing limits it reuses before code and add a limit only when the full 224-receipt fixture cannot fit. If a limit changes, measure the same capture and offline verify commands before and after, record hardware/provider/date, and keep the change only if it remains bounded and does not weaken rejection tests.

## 11. The fail-closed posture

[Elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md) owns each observed failure from reproduction through regression guard. No mismatch is downgraded to recorded proof.

Capture stops before publication on a missing/extra/duplicate receipt, non-contiguous index, header/transaction/block mismatch, non-canonical quantity, unsupported receipt type, malformed bloom/log, witness limit breach, receipts-root mismatch, target-receipt mismatch, filtered-log mismatch, derived-count mismatch, digest mismatch, or staging error. Verification rejects the same conditions offline. Ariadne rejects a positive `receipt_trie_proved` count without a nonzero `receipts_root`, an unlisted component, or a source fixture/release that does not bind that count. Legacy readers reject new versions they do not know; new readers preserve the old version's meaning.

Each cause receives the smallest deterministic mutation test: alter one status byte, type prefix, trie index, transaction hash, address/topic/data byte, log order, root nibble, manifest count, release component, or Ariadne field and show the relevant command fails. The unchanged fixture is the paired green case. Lazarus failures are recorded by `python3 plugins/lazarus/tests/run_tests.py --elenchus-report .hexaemeron/lazarus-elenchus-report.json`; Ariadne schema and predicate mutations run through its conformance and schema-agreement tests. When a new failure appears, preserve the artefact and exact command, localise the first disagreeing stage, fix that cause, then add the mutation to the permanent suite.

## 12. Decisions and their homes

[Hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) applies because this work changes public evidence vocabulary and versioned interfaces.

- Record the chosen full-witness design, its filtered-log completeness reason, the consensus/RPC-field boundary, version transition, and rejected compact/debug/re-execution designs in a new non-colliding ADR under `docs/decisions/`. The runbook finds the next ADR number; the study does not reserve one.
- Keep this study and its runbook under `.hexaemeron/` for the receipted delivery. Put durable operator and format guidance in Lazarus documentation, with the exact capture/verify commands and failure meanings.
- Document state-fixture/v2 beside Ariadne's existing state-fixture specification, including independent `state_root` and `receipts_root` rules, schema examples, and replay limits.
- Explain code-level reasons only where a future maintainer could otherwise weaken canonical encoding, evidence promotion, atomic publication, or legacy-version dispatch. Comments should name the receipt-root rule or historical constraint, not restate an assignment.
- Update Lazarus and Ariadne version ledgers only through their canonical Promise Machine transitions after implementation, audit, prose gates, release verification, and readback succeed. #383 closes only through the repository's merge workflow.
- Record the complete mutable first-party marketplace prose inventory and its reconciliation result in the delivery evidence. Unrelated stale prose becomes a correctly queued lead; it is not silently folded into #383.

### Amendment -- 2026-08-26

**What changed.** The proof boundary is narrowed to what the header's `receiptsRoot` actually commits. A receipt-trie-proved relation may establish the canonical receipt payload at a trie index and the ordered consensus log tuples `(address, topics, data)` inside that payload. The fixed block hash and number come from the verified header; transaction index and block-global log index are derived from the proved trie key and ordered receipt/log positions. The header's RPC `transactions[]` hash list, receipt and log `transactionHash` fields, and every other RPC-only decoration remain `recorded_rpc`: the header hash commits `transactionsRoot`, but this delivery neither captures transaction bodies nor reconstructs that trie, so it cannot bind a transaction hash to receipt index `0xbf`. Plan-v3 may retain the target hash as a recorded lookup label and may require recorded sources to agree with one another, but the receipt witness must not present that hash as a receipt-root field. Filtered-log completeness compares the full ordered proved consensus projection and its derivable positions with the corresponding fields in the recorded `eth_getLogs` result; transaction-hash equality is recorded consistency, not part of the proved relation. The two derived relations remain the consensus receipt payload at index `0xbf` and the complete five-entry consensus-log projection. The original `receipt-set-completeness` control is therefore satisfied by unique contiguous receipt indices plus reconstruction of the exact committed root, not by unproved transaction-hash equality; the original `transaction-index-binding` control proves the payload at its trie key while explicitly retaining hash attribution as recorded. Step 1 must remove proof-bearing transaction-hash fields and claims from the new schemas, helpers, tests, ADR, and tracked specification copies. Steps 2 through 5 must use this same scoped relation in verification, capture, manifest/release/Ariadne evidence, the Goldfinch demonstration, and public prose.

**Why.** Warden finding `S1-R1-01` demonstrated a coherent witness rewrite that changed every target transaction-hash decoration while preserving all receipt trie values and `receiptsRoot`; its consensus projection SHA-256 was `9fa074210f311ce216f30d332a9fa87307298c2961f57de0b70024a279243273`. Ethereum receipt values contain status or root, cumulative gas used, logs bloom, and ordered consensus logs, but no transaction hash. Adding a transaction-trie proof would require full typed transaction bodies, canonical transaction encoding, another capture and verification boundary, and a different success claim. That is materially larger than issue #383's receipts-root frontier and is rejected here in favour of an explicit recorded-RPC qualification.

**Steps touched.** Steps 1, 2, 3, 4, and 5.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry broken; exit broken. Step 3: entry broken; exit broken. Step 4: entry broken; exit broken. Step 5: entry broken; exit broken.
