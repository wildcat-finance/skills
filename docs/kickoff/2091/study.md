# Study: Wildcat sanctioned-account asset routing joins (#2091)

Assuming, unless corrected: this issue admits two supporting joins, while #2090 owns `AccountSanctioned`. The controller requests merge delivery. Work starts at `8b4e137917d754a7b7c3d5e74d141c0bedf70aa2` on `fiat/2091-wildcat-sanctioned-account-asset-routing-jo`. #2089 and #2090 are independent runs; their unmerged work supplies no starting evidence here. The reserved mapping version for this issue is `1.3.0`; integration must compose supported `1.0.0`, `1.1.0` and `1.2.0` interpretations if their deliveries have landed. This reservation is a controller coordination decision, not evidence that those versions exist on this starting ref.

## 1. Problem statement

Downstream consumers cannot distinguish a sanctioned-account queue or market-token transfer when the canonical ledger leaves its companion unsupported. Add a qualified explanation to the existing primary row, keeping one primary per native queue or transfer. The user is a consumer that must not interpret native logs independently.

A working prototype maps V2 `SanctionedAccountAssetsQueuedForWithdrawal(address,uint256,uint256,uint256)` to exactly one `WithdrawalQueued(uint256,address,uint256,uint256)` using generation, market, transaction, account, expiry, scaled amount and normalized amount. V1 declares no queued companion and receives no invented V1 mapping. For both generations whose ABI declares `SanctionedAccountAssetsSentToEscrow(address,address,uint256)`, match exactly one market `Transfer(address,address,uint256)` using generation, market, transaction, account/from, escrow/to and amount/value. Require exactly one companion as well as exactly one primary per complete key. Neither an extra primary nor an extra companion may be resolved by input order.

A successful join carries `join-inference`, a stable rule, both selectors and the complete conditions in a new mapping-only `routing_joins` list on the primary and supporting companion records. Under `1.3.0`, every mapping record carries that deterministic list, empty when it has no new relation; each entry has exactly `evidence_class`, `rule`, `primary_selector`, `companion_selector` and `conditions`. Queue conditions contain generation, market, transaction hash, account, expiry, scaled amount and normalized amount; transfer conditions contain generation, market, transaction hash, account/from, escrow/to and amount/value. Keep the existing singular `join` unchanged for execution escrow and batch-burn relations. A hostile transfer matching both a new routing companion and an existing burn relation preserves both, with all counterpart selectors and no overwritten evidence. Add the counterpart selector to their mapping supporting selectors and the companion selector to the primary event's provenance. Existing primary parties and amounts remain exact: queue claims stay claims; transfers stay market-token claims. Do not introduce a sanction-status party, executor, underlying cash flow or identity claim. A companion is `supporting-routing` even when unmatched, and creates no event. An unmatched or ambiguous companion carries a stable named routing gap and a limitation; its preserved record remains available. Ordinary primary rows without these companions acquire no speculative sanction gap. The rule ids are `same-market-transaction-account-expiry-scaled-normalized` and `same-market-transaction-account-escrow-amount`. Queue condition keys are exactly `generation`, `market`, `transaction_hash`, `account`, `expiry`, `scaled_amount` and `normalized_amount`; transfer condition keys are exactly `generation`, `market`, `transaction_hash`, `account`, `escrow` and `amount`. Each unmatched companion uses `routing:sanctioned-assets-queued-for-withdrawal:missing-primary` or `routing:sanctioned-assets-sent-to-escrow:missing-primary`. If either matching group cardinality exceeds one, use that prefix with `ambiguous-match` instead. Count one routing gap per unmatched companion; these coverage counts overlap preserved source records and are never extra omitted events.

Success criteria, executed by the future proof interface:

- `semantic-conformance`: public constructed positive queue V2 and transfer V1/V2 joins; missing match, duplicate primary, duplicate companion, every changed key field, wrong role/generation, simultaneous batch-burn plus sanctions routing on one transfer, and record-order permutation controls. Assert one primary per source, reciprocal selectors, unchanged financial units and named unmatched gaps. `python3 plugins/tabularium/tests/prove_wildcat_sanctions.py --candidate unique-key --criterion semantic-conformance --report .hexaemeron/reports/unique-key-semantic-conformance.json`.
- `release-compatibility`: immutable old examples verify and reproduce, current specimens rebuild and move, and rebinding superficial digests cannot bless changed join, selectors, parties, units, coverage, disposition or raw bytes. `python3 plugins/tabularium/tests/prove_wildcat_sanctions.py --candidate unique-key --criterion release-compatibility --report .hexaemeron/reports/unique-key-release-compatibility.json`.
- `retained-coverage`: verify both named retained staging inventories, rebuild their Alexandria releases, build and verify current canonical outputs, and report each target signature as exercised or absent. A present target with zero eligible primary matches or any unexplained gap fails. Absence is checked coverage, never a positive join. `python3 plugins/tabularium/tests/prove_wildcat_sanctions.py --candidate unique-key --criterion retained-coverage --report .hexaemeron/reports/unique-key-retained-coverage.json`.

Fiat controls the final demonstration at Step 3. Run the three commands through the controller's success-criteria execution path with actual source commands, plus named absent-custody and hostile-input refusals. This demonstrates the observed cases; it does not establish criterion sufficiency or historical completeness.

## 2. Prior art

The current mapper at `plugins/tabularium/scripts/tabularium_lib/wildcat_rows.py` already joins withdrawal execution to escrow routing by full key and unique cardinality. Its batch-payment join has a different, source-bound adjacency rule. Reuse the first pattern's one-to-one rule; do not copy batch adjacency into sanctions joins. An additive mapping-only `routing_joins` list and existing supporting selectors express the new relations while preserving the existing singular `join`, without schema 4 or a new canonical action. `wildcat_abi.py` pins concrete ABI context before topics; generation and role remain admission requirements.

Read the merged bodies of [PR #2105](https://github.com/wildcat-finance/skills/pull/2105) and [PR #2104](https://github.com/wildcat-finance/skills/pull/2104), the last two merged deliveries for the Wildcat canonical mapping/reproduction subject. #2105 carries #2103 (safe-path runner imports) and #1926 (Probitas batch status); this run guards its new runners against the first, and leaves #1926 with Probitas. Its two-burns wording, Hypomnema supplied-scope issue, operator-owned custody ancestors, refusal-composition evidence and inherited capture counts remain bounded as recorded. #2104's vacuity fix requires a present batch-payment specimen before calling a batch join exercised; this run applies that distinction separately to constructed positives and retained absence. Neither PR authorises widening private capture publication. The more recent wrapper delivery touches upstream context; this run consumes its accepted context without changing that collector or registry.

Whole-set `audit_synopsis.py --check .` exited 0 before reading the verified synopsis views: `plugins/tabularium/audit/AUDIT_SYNOPSIS.md`, `audit/rounds/fiat-1378-wildcat-v1-v2-canonical-adapter.synopsis.md`, `audit/rounds/fiat-2087-wildcat-withdrawal-batch-canonical-meaning.synopsis.md` and the wrapper source's `audit/rounds/fiat-2092-wildcat-v2-wrapper-instances-as-capture-sub.synopsis.md`. These are synopsis reads, not direct authoritative-source reads. Every source remains authoritative; their headers bind its digest. Legacy missing `Covered`, `Not checked` and Elenchus fields remain unknown. All historical findings retain their recorded fixed status; prior `inconclusive` verdicts remain inconclusive. Section 11 records two applicable historical failure classes as new-run regression obligations; it claims no unresolved known finding on this pinned product surface. Historical root/Hex failures, caller-controlled module ordering and provider/chain/identity limits establish no new current finding. Wrapper payload and shallow-clone budget guards remain outside this issue; tests here must not introduce a Git-history dependency.

Outside this repository, the pinned V1 implementation normalizes the same scaled balance for the transfer and escrow event at `_blockAccount`. The pinned V2 `_blockAccount` queues the full balance and then emits its queued companion; `_queueWithdrawal` can emit batch-payment logs before returning. This defeats a required adjacency reading. V2's ABI still declares the escrow-asset event, but its current `_blockAccount` path uses queued withdrawal. A constructed V2 escrow specimen exercises the declared ABI branch and proves no historical emission.

## 3. Constraints and non-goals

Use the exact Python `3.14.6` recorded by `.python-version`, stdlib unittest, the existing checked runner and existing JSON schema tooling. Add no dependency, live RPC collection, new source proof or network behavior to Tabularium. The raw release and native evidence classes remain unchanged. The release policy requires a new versioned interpretation and fresh output directories; published source, capture, canonical and coverage bytes remain immutable and verifiable.

Reserve adapter `1.3.0` for the new joins. Build new releases using that interpretation. Verification must select the supported exact version declared by the release and recompute through the corresponding feature set; refuse unknown versions. Keep old semantics byte-identical by explicit feature gates, without copying an opaque duplicate mapper. Schema version stays 3. Old versions must reject forged new joins, while the new version must reject erased required joins or rewritten `supporting-routing` dispositions. Shared schema validation may admit the supported historical versions, but verification still proves the exact release interpretation.

Always: preserve unrelated dirty work; run `python3 scripts/run_checks.py` before push; run the complete Tabularium suite and written-record sequence; update generated metadata through its owner. Ask first: a dependency, Solidity/public ABI change, CI change, private publication or rewritten historical release. Never: publish private payloads or capture-derived counts, alter raw evidence, use missing metadata as zero, guess an ambiguous join, or claim a command ran without its result.

Non-goals: #2090's status/configuration meaning, #2089's fee meaning, historical capture expansion, wrapper collection, identity, independent Ethereum proof, settlement, underlying cash movement, accounting, sanctions-law interpretation, compiler reruns and runtime-code equivalence. Required fields and conservative match rules are a recorded inference over native logs.

## 4. Design options

`unique-key` indexes primary and companion logs by complete native identity and joins only a one-to-one group. It retains bounded indexes and rejects ambiguity in either direction. `first-match` reduces index storage but incorrectly joins duplicated primaries or companions. `adjacent-only` saves an index but omits valid joins separated by emitted batch events and can select one companion from an ambiguous group.

`.hexaemeron/design-evidence.json` is the closed selection interface. `.hexaemeron/design/sanctions_model.py` executed all 15 resolved cells, yielding one frontier survivor, `unique-key`. The model uses finite labelled tuples, all changed fields, duplicates on both sides, absent matches and reordered input. Its 32-pair work counters are 96 key operations and 64 retained index slots for `unique-key`, 528 comparisons and 0 index slots for `first-match`, and 1,024 comparisons and 0 index slots for `adjacent-only`. These are counts from this model, not production time or memory measurements. Correctness and recovery gates remove the two cheaper-storage candidates. Compatibility at selection establishes only a stable primary denominator in the model; actual release compatibility remains pending at `step:3`.

The future proof runner has the exact candidate and criterion choices from the record. Conformance for rejected candidates may remain pending because no transition selects them; do not fabricate production evidence for them. Production semantic conformance and compatibility block Step 3, and retained coverage blocks integration. `design_evidence.py .hexaemeron/design-evidence.json --transition design-lock` must exit 0 before receipt.

## 5. Risk register seed

```risk-register
full-key | primary and companion grouping | every declared native field and generation market transaction is in the match key
one-to-one | join cardinality | duplicate primaries or companions leave gaps and no arbitrary pairing
v2-only-queue | generation and concrete ABI | queue routing is admitted only where the ABI declares it
role-bound | emitter context | a wrapper or unregistered token transfer cannot satisfy a market join
unit-bound | amount equality | scaled and normalized claims stay distinct and escrow transfer equality uses market-token units
supporting-only | native disposition and canonical denominator | each sanctions companion remains supporting-routing and emits no second action
selector-bound | mapping records and event provenance | both selectors resolve to the joined raw logs with reciprocal supporting evidence
named-gap | missing or mutated match | each unmatched companion remains preserved with a stable gap and limitation
version-dispatch | immutable release verification | old versions reproduce exact bytes and new semantics cannot be downgraded silently
verify-rebuild | adversarial output edits | rebinding digests never blesses changed conditions selectors parties units or dispositions
retained-absence | evidence reporting | absent target signatures are reported as absence and never described as exercised joins
safe-path | registered proof and audit runners | all new runners resolve imports under PYTHONSAFEPATH and isolated Python before their bytes freeze
private-custody | retained staging and public reports | validate complete inventory and publish only identifiers digests and bounded booleans
partial-output | fresh release publication | existing atomic writer and refusal cleanup stay effective
scope-composition | concurrent issue integration | signed merge of prior deliveries reruns every overlapping version and semantic gate
```

## 6. Glossary seeds

Primary: the existing canonical queue or market-token transfer row.
Companion: a sanctions log that explains routing without another canonical action.
Unique key: one complete native tuple with exactly one primary and one companion.
Join inference: a declared relation over two preserved selectors, with its exact conditions.
Retained absence: verified finite input contains no target signature; no join was exercised.

## 7. Sources

Repository paths below refer to starting commit `8b4e137917d754a7b7c3d5e74d141c0bedf70aa2` unless a source's own digest says otherwise.

- [Issue #2091](https://github.com/wildcat-finance/skills/issues/2091), its current body and carryover to #2090; [#2103](https://github.com/wildcat-finance/skills/issues/2103) records the runner import failure.
- [Mapper](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/tabularium/scripts/tabularium_lib/wildcat_rows.py), `wildcat_rules.py`, `wildcat_validation.py`, `wildcat_release.py`, `wildcat_abi.py`, canonical schema and `test_wildcat_v3_semantics.py` / `test_wildcat_v3_releases.py` / `wildcat_v3_fixtures.py` supply the existing envelope and custody pattern.
- [Release policy](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/tabularium/docs/release-policy.md) and [canonical guide](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/tabularium/docs/wildcat-canonical.md) set immutability and evidence limits.
- [Pinned V1 base](https://github.com/wildcat-finance/wildcat-protocol/blob/da74452aa7d1a0f024d99efd22cc6d950a8116b7/src/market/WildcatMarketBase.sol#L143-L163) establishes equal normalized claim units for asset escrow routing.
- [Pinned V2 market](https://github.com/wildcat-finance/v2-protocol/blob/a70f297fbd1b1ab597e0e9a3458a2d13a34b4657/src/market/WildcatMarket.sol#L298-L319) and [V2 queue implementation](https://github.com/wildcat-finance/v2-protocol/blob/a70f297fbd1b1ab597e0e9a3458a2d13a34b4657/src/market/WildcatMarketWithdrawals.sol#L79-L117) establish queued fields and possible intervening batch emission. These pinned primary sources were freshly fetched; no compiler or chain operation ran.
- `.hexaemeron/design/sanctions_model.py`, its 15 report files, and `.hexaemeron/reports/retained-inventory.json` hold this study's executed observations. The retained probe uses `wildcat_batch_retained.py` to check staging inventories and rebuild the original raw releases; it records target presence booleans, identifiers and manifest digests, with no capture-derived counts. The probe completed successfully for both generations and found neither target signature in either verified finite input. These are fresh local retained observations, not fetched chain data or positive historical join evidence.

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/ephoros/SKILL.md) governs signal content. This finite offline CLI has no unattended service or pager. An operator needs to know which companion did not match, whether a key was absent or ambiguous, and which interpretation `verify` replayed. Step 2 emits stable gap identifiers, source selectors and limitations in the existing descriptor; coverage aggregates gaps without turning them into omitted-row counts. Step 3 records criterion, input digest, version and exit in reports. Private reports must not expose staging paths or native values.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/phylax/SKILL.md) governs external data and filesystem handling. Treat raw logs, references, descriptors and report paths as data; preserve existing exact ABI bounds, count caps, source-selector uniqueness, root confinement, no-follow path handling and fresh atomic publication. Indexes cannot exceed the admitted native record cap. Retained inputs are operator-named local directories validated against the complete staging manifest, not trusted by pathname alone. Use source-bound imports for fixed local reporters, argument arrays for subprocesses, bounded output and no shell interpretation. No credential access or runtime network call is introduced.

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/metron/SKILL.md) governs performance claims. There is no throughput or latency target and no claimed optimization. The existing 500,000-record admission cap bounds extra index references. Selection counters are recomputed with `python3 .hexaemeron/design/sanctions_model.py --candidate unique-key --criterion key-work --report .hexaemeron/reports/unique-key-key-work.json` and its `index-slots` counterpart. The final resolver records actual elapsed behavior only if measured; it must not call these model counts a production benchmark.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/elenchus/SKILL.md) owns failure reproduction and guards. Malformed supported ABI, duplicate source identity, unsafe custody, unsupported interpretation or changed generated bytes refuse the dependent transition. Missing or ambiguous valid companions remain explicit mapped coverage gaps. A present but unmatched target cannot pass a retained positive assertion. An absent target may pass an explicit absence check only when its input was verified and the public constructed positive proves the branch separately. Missing retained custody refuses integration by variable name, rather than substituting constructed fixtures.

Two historical classes require regression controls in Step 1; neither is an unresolved current defect in this issue's product surface. `kf-2091-retained-vacuity` derives from #2087 S4-R1-01: test the result classifier with absent, positive, missing-primary and ambiguous constructed observations so a present unexercised target cannot be labelled exercised. `kf-2091-safe-path` derives from #2092 S1-R1-01 and #2103: run each new reporter with `PYTHONSAFEPATH=1` and isolated Python before freezing its parser bytes. These regression controls protect this issue's new interfaces; repairing unrelated old runners remains #2103. Tests must distinguish assertion failure, infrastructure error, skipped cases and an actual guard result.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "tabularium",
      "path": "plugins/tabularium/audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7",
      "view_sha256": "2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c"
    },
    {
      "id": "canonical-1378",
      "path": "audit/rounds/fiat-1378-wildcat-v1-v2-canonical-adapter.synopsis.md",
      "source_sha256": "ae0efffe971b1ae9070961e8e67f5ce3f164b107330fae56764b6ac8f0bdfaff",
      "view_sha256": "4d75001072001c5a7a041e9aa4be94bc4aa15157bc11e18040c4e625ee6cdb89"
    },
    {
      "id": "batch-2087",
      "path": "audit/rounds/fiat-2087-wildcat-withdrawal-batch-canonical-meaning.synopsis.md",
      "source_sha256": "24cf81c7b2c258ade1907295bab375460717590566bc00dc5d1868025560c51c",
      "view_sha256": "663baae0623da10f544026072a0ba8accec36b0c2211b40100511acc88f45062"
    },
    {
      "id": "wrapper-2092",
      "path": "audit/rounds/fiat-2092-wildcat-v2-wrapper-instances-as-capture-sub.synopsis.md",
      "source_sha256": "123460dbcbfe24baf2bed441811e808482bc7936212206a974964d8bfbb5dbee",
      "view_sha256": "9be187f837394daf66c1240b83d96777ea410d5e393a2e5373ce7d77a823dfa1"
    }
  ],
  "findings": [],
  "no_known_findings": {
    "source_views": [
      {
        "id": "tabularium",
        "source_sha256": "1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7",
        "view_sha256": "2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c"
      },
      {
        "id": "canonical-1378",
        "source_sha256": "ae0efffe971b1ae9070961e8e67f5ce3f164b107330fae56764b6ac8f0bdfaff",
        "view_sha256": "4d75001072001c5a7a041e9aa4be94bc4aa15157bc11e18040c4e625ee6cdb89"
      },
      {
        "id": "batch-2087",
        "source_sha256": "24cf81c7b2c258ade1907295bab375460717590566bc00dc5d1868025560c51c",
        "view_sha256": "663baae0623da10f544026072a0ba8accec36b0c2211b40100511acc88f45062"
      },
      {
        "id": "wrapper-2092",
        "source_sha256": "123460dbcbfe24baf2bed441811e808482bc7936212206a974964d8bfbb5dbee",
        "view_sha256": "9be187f837394daf66c1240b83d96777ea410d5e393a2e5373ce7d77a823dfa1"
      }
    ],
    "consuming_step": 1,
    "surveyor_assertion": "no-known-findings"
  }
}
```

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/hypomnema/SKILL.md) governs durable explanations. The expensive decisions are full-key one-to-one joins, supporting-only companions, qualified gaps, immutable interpretation dispatch and conditional retained absence. The study creates `docs/decisions/drafts/join-wildcat-sanctioned-account-assets.md`, with numbering assigned at integration; Step 1 commits its checked bytes. Public specification copies live under `docs/kickoff/2091/`; fresh specimens under `plugins/tabularium/examples/wildcat-v1-sanctions-v0/` and `wildcat-v2-sanctions-v0/`; semantic limitations live in `plugins/tabularium/docs/wildcat-canonical.md`. Retained public records contain identifiers, digests and booleans only. The controller's existing audit path owns audit history.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | unique-key
record | docs/decisions/drafts/join-wildcat-sanctioned-account-assets.md
```

Runbook recommendation: three steps. Step 1 scaffolds the fixed proof runner `plugins/tabularium/tests/prove_wildcat_sanctions.py` and audit reporter `plugins/tabularium/tests/emit_wildcat_sanctions_report.py`, supporting helper and scaffold tests, the two scaffold regression controls, public specification bundle, decision draft and required package version surfaces. Step 2 implements complete-key joins, gaps, reciprocal selectors, interpretation dispatch, version/schema admission, semantic and compatibility tests and guide; resolve both `step:3` gates on the committed tree. Step 3 publishes constructed fixtures for each admitted generation, executes the three source-bound demonstration criteria on constructed and verified retained inputs, exercises refusal controls, and records reproduction. Every step runs the checked runner with root, Tabularium and repository lint scope; integration composes the prior deliveries with their signed ancestry and reruns every affected gate.

Readiness: 12 of 12 study sections complete. Selection evidence is closed; production implementation, public specimens and conformance remain pending at their named transitions. The next action is deriving the runbook, then checking its design lock and the source-bound no-known-findings claim before any product edit.
