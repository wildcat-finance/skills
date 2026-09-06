# Issue 1360 study: empty-block receipt witness

Status: ready for runbook

Target: `wildcat-finance/skills` at base ref `main`, observed at `3cc0ad7f521985e46cf29f364a20e19fa99b64dd` on 2026-09-06.

Assuming, unless corrected:

1. The prototype keeps `plan-v3`, `receipt-witness-v1`, `manifest-v2`, and `release-v2`; it widens the two receipt-aware input shapes without changing the meaning of any already-valid non-empty document.
2. A plan selects the empty branch by containing only `block_receipts_request` in `receipt_witness`. A witness selects it by carrying a verified header and `receipts: []` while omitting `target_receipt` and `filtered_logs`.
3. The empty branch is valid if and only if the captured header's verified `receipts_root` equals the canonical Ethereum empty trie root `0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421` and the named block-receipts response is the empty array.
4. A valid empty witness derives exactly zero `receipt_trie_proved` relations. Zero is truthful evidence cardinality, not missing verification.
5. Ethereum genesis block 0 is the receipt-less demonstration fixture. Its live RPC observation chooses reproducible source material but does not add a canonical-chain or provider-independence claim.
6. Existing non-empty receipt fixtures and releases remain byte-valid and retain their two-relation semantics.

## 1. Problem statement

Lazarus can prove receipt inclusion for a non-empty block, but its plan and witness schemas require a target receipt and log filter, `receipt_trie_root` rejects an empty list, the relation verifier assumes a target exists, and manifest validation rejects a zero receipt-proof count. That makes a real Ethereum block with no receipts unrepresentable even when the verified header commits to the canonical empty trie.

Build the narrow empty branch for Lazarus fixture authors and offline verifiers. A working prototype accepts exactly the empty shape described in the assumptions, binds it to the captured header's empty `receiptsRoot`, derives zero receipt-trie relations, refuses an empty receipt set under any non-empty root, and leaves every existing non-empty artefact green.

The demonstration path is a checked-in `plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1/` fixture verified offline by:

```sh
python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1
```

Acceptance is testable by these commands from the target root with the repository's pinned Python environment active:

```sh
python3 plugins/lazarus/scripts/lazarus.py validate schemas
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -p 'test_empty_receipts.py' -v
python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v
python3 scripts/run_checks.py
```

The focused test must cover the four truth-table cases: empty set plus empty root accepts; empty set plus non-empty root refuses; non-empty set plus its computed root keeps the existing path; non-empty set plus a mismatched root refuses. It must also prove the plan/witness branch shapes, zero derived relations, manifest and release propagation, and unchanged non-empty samples.

## 2. Prior art

### Repository implementation

- `plugins/lazarus/schemas/plan-v3.json:173` defines `receipt_witness` and currently requires the block receipts request, target receipt lookup, target transaction index, and filtered logs request.
- `plugins/lazarus/schemas/receipt-witness-v1.json:7` requires the header, receipts, target receipt, and filtered logs; its receipts array has `minItems: 1` at line 40.
- `plugins/lazarus/scripts/lazarus_lib/receipts.py:92` has the receipt-set root function, and line 119 begins the non-empty relation verifier.
- `plugins/lazarus/scripts/lazarus_lib/trieproof.py:11` defines `EMPTY_TRIE_ROOT = keccak(b"\x80")`; `trie_root([])` already returns it through the branch at line 85.
- `plugins/lazarus/scripts/lazarus_lib/capture.py:374` derives the current target-scoped receipt witness, while its capture accounting already starts `receipt_trie_proved` at zero at line 584.
- `plugins/lazarus/scripts/lazarus_lib/manifest.py:330` currently refuses `receipt_trie_proved <= 0`, so the manifest semantic check must distinguish a proved empty set from absent receipt evidence.
- `plugins/lazarus/tests/test_receipts.py:152` already guards the low-level empty-trie constant. Existing receipt, schema, capture, manifest, verifier, release, binding, and preservation-release tests are the compatibility surface.
- `plugins/lazarus/docs/receipt-inclusion-proofs.md` documents only the current target-scoped, exactly-two-relation model and must document the new zero-relation branch without weakening the existing claim.

### Last two merged changes to the shipped receipt path

- [PR #665](https://github.com/wildcat-finance/skills/pull/665), merged 2026-08-27, shipped the receipt inclusion path from issue #383. Its final audit explicitly left “the empty-block successor” not checked. This study takes only that named successor forward; transaction-trie expansion, canonical-chain claims, provider-independence claims, and hosted publication remain out of scope.
- [PR #1183](https://github.com/wildcat-finance/skills/pull/1183), merged 2026-09-04, moved the maintained receipt fixture to the Aave v4 capture and extended receipt type support. It left no empty-block implementation. Its explicit carry-over issue #1139 concerns a distinct post-integration observation and is not folded into issue #1360.

### Audit evidence

The in-scope audit source is `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.md`. The verified reading view actually read was `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.synopsis.md`, after this whole-set currency check exited zero:

```sh
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

The view identifies source SHA-256 `23e316c03615e182de70ddacab0401b1870f69ceb4d8ad1207939bb99eaa546f`; the view file's SHA-256 is `58da1473ee8a19c78b1b065c7166a14c8f0f21930a25851d05f7eac56c05bb42`. It preserves each round's finding ids and statuses, `Covered`, `Not checked`, `Elenchus verdict`, and `Leads not pursued`. The final round records all 14 receipt and release lanes reviewed, no admissible unresolved in-scope lead, and the empty-block successor explicitly not checked. Earlier findings about receipt metadata, hostile diagnostic payloads, staging cleanup, and stale public evidence were fixed and guarded; their controls stay in force. The final round's Elenchus verdict is `null` because it had no new finding, not because the earlier guard evidence disappeared.

No other in-scope audit source was found. The Lazarus root `audit/AUDIT.md` records the current audit surface but does not replace the per-run source above.

### External protocol and implementation references

- [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) defines typed transaction-receipt envelopes and preserves legacy receipt encoding.
- [Ethereum Merkle Patricia Trie documentation](https://ethereum.org/en/developers/docs/data-structures-and-encoding/patricia-merkle-trie/) describes the trie commitment model used by the header roots.
- [Ethereum execution APIs](https://github.com/ethereum/execution-apis) define the JSON-RPC block and receipt response surface.
- [go-ethereum core/types/block.go](https://github.com/ethereum/go-ethereum/blob/master/core/types/block.go) exposes the canonical empty-receipts derivation used by a production execution client.

A 2026-09-06 read-only call to `https://ethereum-rpc.publicnode.com` observed block 0 hash `0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3`, `receiptsRoot` `0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421`, zero transactions, and `eth_getBlockReceipts("0x0") == []`. These are source-selection observations, not a promise that this provider is canonical or continuously available.

## 3. Constraints and non-goals

The starting ref is `main` at `3cc0ad7f521985e46cf29f364a20e19fa99b64dd`. The toolchain is Python `3.14.6` from `.python-version`; `pyproject.toml` requires `==3.14.*`; Lazarus uses its pinned requirements and stdlib `unittest` entry points. JSON documents remain closed and versioned under the existing schemas.

Always:

- preserve every currently valid non-empty `plan-v3`, `receipt-witness-v1`, `manifest-v2`, and `release-v2` document;
- validate the truth table at schema and semantic layers and keep hostile-input diagnostics bounded;
- run the focused tests, complete Lazarus suite, root checks, offline fixture demo, design-transition checks, and applicable prose checks before handoff;
- keep capture and verification fail closed when the named RPC response, header identity, root, plan branch, or witness branch disagree.

Ask first:

- before adding a dependency, a network provider requirement, hosted CI, a new schema/release version, or a public API;
- before widening proof authority to transaction hashes, canonical-chain membership, provider independence, or transaction-trie evidence;
- before changing the stored fixture source away from Ethereum genesis or rewriting any digest-bound existing artefact.

Never:

- ingest credentials, persist provider secrets, invoke shell interpolation on RPC data, or read Horos-classified sinks without a demonstrated need;
- weaken, delete, or restamp an existing non-empty fixture merely to make the empty branch pass;
- turn zero relations into a positive count, treat an absent witness as a proved empty set, or accept an empty receipt array under a non-empty root;
- claim a command ran when it did not, mutate the Fiat controller during this study, or commit, push, publish, merge, or close the issue from the study phase.

Non-goals are transaction-trie proofs, transaction-hash attribution, new receipt encodings, canonical-chain or finality proof, provider quorum, broader fixture-release redesign, performance optimisation, dependency changes, marketplace publication, and unrelated Lazarus or Ariadne work.

## 4. Design options

The authoritative selection interface is `.hexaemeron/design-evidence.json`. Its 15 selection reports live under `.hexaemeron/reports/selection/`; each is a closed `protasis-design-report/v1` record produced by an exit-zero command. The design-lock check selected `shape-discriminated` by the `unique-frontier` rule.

| Candidate | Construction | Trade |
| --- | --- | --- |
| `shape-discriminated` | Keep existing versions. The plan's `receipt_witness` contains only `block_receipts_request`; the witness has header plus `receipts: []` and omits target/filter objects. Existing full shapes retain the non-empty branch. | Smallest compatible change and zero extra discriminator fields, but semantic code must keep the two closed shapes aligned. |
| `explicit-mode` | Keep existing versions and add an explicit empty/scoped mode field to both plan and witness. | Easier local branching, but duplicates a discriminator already expressed by closed object shape and creates two fields that can disagree. |
| `new-format` | Add new plan, witness, manifest, and release versions dedicated to empty blocks. | Strong version separation, but expands conversion, binding, documentation, and rollback surface for one additional cardinality. |

All three pass the empty truth-table gate, require one receipt RPC request for the empty branch, and preserve existing fixtures without edits. `shape-discriminated` adds zero discriminator fields and has a two-file schema rollback surface. `explicit-mode` adds two discriminator fields with the same two-file rollback surface. `new-format` adds zero discriminator fields but creates four rollback files. The selected candidate uniquely dominates the other survivors across the comparative metrics.

The selected implementation must define mutually exclusive closed branches rather than make target fields independently optional:

```design-bridge
schema | hypomnema-design-bridge/v1
decision | shape-discriminated
record | docs/decisions/drafts/empty-receipt-witness-shapes.md
```

- empty plan: only `block_receipts_request`;
- scoped plan: all four current fields;
- empty witness: `schema_version`, verified `header`, and `receipts: []` only;
- scoped witness: all five current fields with at least one receipt;
- empty semantic result: computed root equals both the verified header root and the canonical empty trie root, with `relations: 0` and no target or filter projection;
- scoped semantic result: unchanged current verification and relation count;
- any mixed shape, root mismatch, missing named response, non-array result, or non-empty response on the empty branch: refusal.

The remaining conformance gates are intentionally pending. `nonempty-root-empty-witness-refused` blocks Step 2, `genesis-empty-fixture-verifies` blocks Step 3, and `existing-formats-stay-green` blocks integration. Their exact resolver commands and future report paths are recorded in the design evidence.

## 5. Risk register seed

The audit loop must enumerate these concerns. Existing receipt-path controls are inherited, not reopened by silence.

```risk-register
empty-root-binding | the boundary between the verified captured header and an empty receipt set | an empty witness is accepted only when computed and header roots equal the canonical empty trie root
empty-set-completeness | the named block-receipts RPC response entering capture | only a bounded literal empty array proves the empty set; absence, null, errors, and partial responses refuse
branch-shape-parity | the plan and witness schema-to-semantic boundary | exactly the empty pair or scoped pair is accepted and every mixed shape refuses
evidence-count-zero | verifier output entering manifest, release, and attestation accounting | zero receipt-trie relations is retained only for a successfully verified empty witness and is never confused with missing evidence
nonempty-regression | existing receipt fixtures and releases crossing widened schemas | all previously valid scoped documents stay valid and preserve current digest and two-relation behaviour
rpc-surface-minimisation | untrusted provider methods and payloads | the empty branch uses only the named block-receipts request and keeps existing count, byte, depth, and diagnostic bounds
manifest-report-shape | verifier report fields consumed by manifests and callers | empty and scoped reports are explicit, closed, deterministic, and cannot overclaim target or filtered-log proof
fixture-provenance | live genesis observations entering a checked-in offline fixture | source RPC records are pinned and verified while canonical-chain and provider-independence claims remain absent
atomic-fixture-write | capture output and release files on the local filesystem | existing staging, containment, bounded cleanup, digest, and atomic-publication controls remain effective
marketplace-prose-drift | public Lazarus claims and examples | documentation states the zero-relation empty branch without weakening or generalising the scoped proof claim
```

## 6. Glossary seeds

- **Canonical empty trie root:** `keccak256(rlp.encode(b""))`, represented here as `0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421`.
- **Empty branch:** The plan/witness shape that requests and carries the complete zero-receipt set and has no target or filter.
- **Scoped branch:** The existing non-empty shape that proves one target index and one exact log-filter projection from the ordered receipt set.
- **Receipt witness:** The closed consensus projection used to reconstruct and bind the ordered receipts trie to a verified block header.
- **Verified header:** The captured header whose identity and commitments have passed Lazarus's existing header verification path.
- **Receipt-trie-proved relation:** A relation counted only after the receipt trie and its claimed target/filter projection have been verified; an empty set has zero such projections.
- **Recorded RPC:** Provider output retained as evidence but not promoted beyond the consensus fields the proof actually binds.
- **Receipt-less fixture:** A deterministic offline fixture whose verified block has the canonical empty receipt root and whose named receipt response is empty.
- **Selection report:** A closed, hashed `protasis-design-report/v1` record for one candidate and one selection criterion.
- **Conformance gate:** A pending design criterion whose exact resolver must pass before its named step or integration transition opens.

## 7. Sources

- Controller topic: `empty-block receipt witness`; issue [#1360](https://github.com/wildcat-finance/skills/issues/1360), read 2026-09-06.
- Target instructions: `AGENTS.md`; reading boundary: `.horos/boundary.json`; root contract: `PROMISE_MACHINE.md`.
- Lazarus instructions and scope: `plugins/lazarus/AGENTS.md`, `plugins/lazarus/skills/lazarus/SKILL.md`, and `plugins/lazarus/skills/lazarus/EVOLUTION.md`.
- Current schemas: `plugins/lazarus/schemas/plan-v3.json`, `receipt-witness-v1.json`, `manifest-v2.json`, and `release-v2.json`.
- Current implementation: `plugins/lazarus/scripts/lazarus_lib/receipts.py`, `trieproof.py`, `capture.py`, `verifier.py`, `manifest.py`, `release.py`, and `binding.py`.
- Current tests and samples: `plugins/lazarus/tests/test_receipts.py`, `test_schemas.py`, `test_capture.py`, `test_verifier.py`, `test_manifest.py`, `test_release.py`, `test_binding.py`, `test_preservation_release.py`, and `support.py`.
- Current documentation: `plugins/lazarus/docs/receipt-inclusion-proofs.md` and `plugins/lazarus/docs/preservation-release.md`.
- Prior delivery: [PR #665](https://github.com/wildcat-finance/skills/pull/665) and [PR #1183](https://github.com/wildcat-finance/skills/pull/1183), including their complete bodies and changed-file diffs.
- Audit source and verified reading view: `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.md` and its sibling `.synopsis.md`, with the hashes recorded in section 2.
- External references: [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718), [Ethereum MPT documentation](https://ethereum.org/en/developers/docs/data-structures-and-encoding/patricia-merkle-trie/), [Ethereum execution APIs](https://github.com/ethereum/execution-apis), and [go-ethereum block types](https://github.com/ethereum/go-ethereum/blob/master/core/types/block.go).
- Design selection: `.hexaemeron/design-evidence.json` and `.hexaemeron/reports/selection/*.json`.

## 8. Signals, and the questions behind them

[Ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns the signal contract. The implementation does not create an unattended service, so no metrics backend or alert is warranted. Deterministic verifier and capture outputs must nevertheless answer these operator questions:

1. Did this run select the empty or scoped branch? The schema/semantic verification step emits the witness mode and schema versions.
2. Which root and cardinality were actually checked? The receipt verification step emits the header root, computed root, receipt count, and derived relation count.
3. If the run refused, was the failure shape, RPC completeness, root binding, or downstream accounting? The failing step emits a bounded stable error category without provider-controlled values.
4. Did the offline demonstration touch the network? The final demo reports denied network use under the existing fixture-verification boundary.

These fields belong in existing bounded JSON events or verifier reports; raw receipt bodies, URLs, credentials, and absolute host paths do not.

## 9. Boundaries, per capability

[Phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary and control contract.

| Capability | Worth taking | Closing control |
| --- | --- | --- |
| JSON Schema ingestion | A closed empty or scoped plan/witness document | Bounded parser and schema limits, `oneOf`-style exclusive shapes, value-free diagnostics, and refusal of mixed or additional fields |
| JSON-RPC capture | One named `eth_getBlockReceipts` result for the already-scoped block | Existing request-count, response-size, nesting, method, block-identity, and source snapshot controls; the empty branch accepts only `[]` |
| Header-to-receipt verification | A root commitment and ordered receipt cardinality | Recompute the trie root, compare it with the verified header, and require the canonical empty root specifically for cardinality zero |
| Manifest/release propagation | A deterministic zero or positive evidence count tied to verified mode | Recompute rather than trust counts, bind files by digest, and retain existing atomic staging and release verification |
| Local fixture write | A reproducible receipt-less test fixture | Contained destination, private staging, bounded descriptor-anchored cleanup, atomic publication, and offline re-verification |
| Documentation | The exact widened claim | Imprimatur plus tests that pin the empty/scoped distinction; no canonical-chain, provider-independence, or target-proof claim for the empty branch |

No subprocess, dependency-installation, credential, or new secret boundary is opened by this design. If implementation introduces one, the runbook must stop for amendment rather than silently inherit this answer.

## 10. The budget, or its absence

[Metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns performance budgets and measurement. There is no runtime speed target: this is a correctness and representability change, the chosen empty branch processes zero receipt payloads, and no performance improvement is claimed.

The existing safety budgets remain binding: one receipt RPC request for the empty path, existing response byte/depth/count limits, and no additional discriminator fields. The design selection measured those structural counts in its closed reports. If implementation changes runtime complexity or claims a speed effect, record a same-environment baseline and candidate using:

```sh
/usr/bin/time -lp python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1
```

Run it at least five times per revision in the same pinned environment and compare medians; no threshold is authorised by this study.

## 11. The fail-closed posture

[Elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md) owns failure triage and the guard rule. Stop capture or verification on a mixed plan/witness shape, absent or duplicated named request, non-array or non-empty result on the empty branch, malformed receipt data, unverified header, root mismatch, zero count without a proved empty witness, positive relation count for the empty branch, digest mismatch, partial fixture, or any attempt to promote recorded-only metadata.

The primary reduced counterexample is `receipts: []` paired with any verified non-empty `receipts_root`; it must fail without requiring a network call. A second guard pairs an empty-root header with a mixed target/filter shape and must fail at the earliest responsible layer. Fixes follow the existing test naming convention in a focused `plugins/lazarus/tests/test_empty_receipts.py`; each confirmed defect gets a minimal test that fails against the step entry ref and passes only with the cause corrected. The complete Lazarus suite and root checks remain the regression boundary.

## 12. Decisions and their homes

[Hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a durable record and where they live.

- The expensive decision is to evolve `plan-v3` and `receipt-witness-v1` through two exclusive shapes instead of adding explicit modes or new format versions. Record it in a new non-colliding file under `docs/decisions/` before the schema change lands; the record cites `.hexaemeron/design-evidence.json` and names the compatibility and rollback trade.
- The exact empty/scoped proof semantics, zero-relation meaning, and refusal truth table belong in `plugins/lazarus/docs/receipt-inclusion-proofs.md`, adjacent to the current two-relation claim.
- The reproducible capture and verification command, source block identity, provider observation boundary, and fixture digest belong with `plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1/` and its demo-facing documentation.
- The completed prototype and verification evidence belong in the existing Lazarus evolution ledger at `plugins/lazarus/skills/lazarus/EVOLUTION.md`; it must not claim publication or canonical-chain evidence that was not produced.
- The phase inputs remain at `.hexaemeron/study.md`, `.hexaemeron/design-evidence.json`, and the later `.hexaemeron/runbook.md`. The runbook binds the selected design record by SHA-256 before Step 1 and carries each conformance gate to its named transition.

No separate operational runbook is warranted because no unattended service or alert is introduced. If later work makes this a scheduled capture, that is a new decision and boundary, not an implied extension of this prototype.
