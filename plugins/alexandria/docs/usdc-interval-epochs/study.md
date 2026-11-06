# Transaction-position implementation epochs

Assuming, unless corrected:

1. Issue #1503 authorises the exact held Alexandria job and its Fiat delivery.
2. The target remains the Ethereum USDC Comet and its preserved EIP-1967 evidence. No new live capture or provider capability is required.
3. The preserved upgrade event marks the announced implementation boundary. It cannot prove which implementation emitted another event in the same transaction.
4. Existing raw evidence and released identifiers remain immutable. A new representation receives a new identifier.

## 1. Problem and proving path

A reader currently assigns every proxy log in an upgrade block to the replacement implementation. `discover_epochs` divides the interval at whole blocks, although `eth_getLogs` supplies transaction and log positions. The first half of such a block can therefore receive the wrong code identity.

The prototype succeeds when a new epoch receipt records block, transaction index and log index at every upgrade boundary; a proxy log in an earlier transaction remains with the preceding implementation; and a later transaction belongs to the replacement. An unplaceable preserved log must refuse. `usdc_interval.py check` must reproduce the result entirely from the release. The upgrade event is a boundary announcement, not a claim about the executing implementation of that event.

A synthetic upgrade-block demonstration must include a proxy log before the upgrade, the upgrade, and a proxy log in a later transaction. Its expected ownership is written as literal evidence, independent of the implementation. An executable regression must fail by assertion on the parent implementation and pass on the fixed implementation. The complete plugin suite runs with `python3.14 plugins/alexandria/tests/run_tests.py`; the demonstration's exact command belongs in the final runbook step.

## 2. Prior art and carried evidence

Repository baseline: `plugins/alexandria/scripts/alexandria_lib/interval.py:682` constructs block epochs; `:773` validates whole-block tiling; `:980` extracts upgrades and refuses two in one block; `:1038` declares opening reads. `plugins/alexandria/scripts/usdc_interval.py:254` owns the opening phase and `:448` feeds only upgrade records into discovery. The offline checker replays that same source evidence. `plugins/alexandria/schemas/interval-receipt-v1.schema.json` fixes the released v1 shape.

The last two merged subject pull requests were read through GitHub: [#1448](https://github.com/wildcat-finance/skills/pull/1448), merged 2026-09-07T07:50:56Z, and [#1446](https://github.com/wildcat-finance/skills/pull/1446), merged 2026-09-07T07:31:33Z. The former closes #1350; the latter records the positional defect as the next job. Its live capture has 93 logs, and upgrade block 25,904,935 holds only the upgrade at transaction index 193 and log index 524. Those bytes do not instantiate the defect.

The whole-tree `audit_synopsis.py --check .` completed with exit 0 before synopsis use. The authoritative in-scope sources are `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.md` and `audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.md`; their complete sibling synopses were read. The Alexandria Compound Phase 0 entry of `audit/AUDIT_SYNOPSIS.md` was also read against authoritative `audit/AUDIT.md`. Other skills' audit records and Alexandria's unrelated index and statement records do not change this collector boundary. Each synopsis preserves its source digest, finding identifiers and statuses, Covered, Not checked, Elenchus verdict and Leads not pursued. The root legacy entry's missing audit-schema, covered, not-checked and elenchus-verdict fields remain unknown.

In #1350, S2-R1-01, W3-R1-01, W3-R2-01, W3-R3-01/02, W3-R4-01/02/03/04/05, W3-R5-01/02/03, W3-R6-01/02/03, W3-R7-01 and W4-R1-01 were fixed. W1 through W5 were fixed prose findings. Their guards remain obligations: committed-offset reading; typed records; request/response agreement; exact shard counts and hashes; address/range checks; duplicate refusal; shared envelope validation; and endpoint confinement. The latest rounds retain their original unguarded prose verdict and all Not checked limitations; this study does not upgrade them to implementation evidence.

The #395 open S1-R1-07 and S6-R1-03 describe the old portable payload ceiling, subsequently owned by framework #949; that packaging history is outside this change. S2-R1-04 and S5-R1-04 are historical runbook mismatches and remain historical. S5-R1-05's absent runtime-code evidence was answered by #1350; its prior open status stays in the source. Two-upgrades-per-block refusal and the MAX_EPOCHS limit remain supported restrictions. Root Phase 0 S1-R1-01 through S1-R1-04 were fixed; this run does not reopen registry, witness or module-origin work.

PR #1448's carryover is disposed of explicitly. `epoch-attribution-by-transaction` is this run. `untestable-release-labels` (#1442), `unconsumed-release-components` (#1443), `refusal-receipt-status-field` (#1444) and `socket-confinement-evidence` (#1445) stay with those issues and are non-goals. `sources-coverage-refresh` belongs to integration's generated refresh. `runbook-files-field-accuracy` remains the earlier immutable record; this run names its own files exactly. `second-transport-independent-derivation` and `epoch-boundary-headers-not-re-asked` retain the prior design's boundaries. `brevitas-signals-on-changed-markdown` remains a prior baseline observation.

Organisational siblings already separate recorded RPC evidence from proof and preserve transaction witnesses in Compound Phase 0. Reusing those concepts does not activate Lazarus or Tabularium and does not add proof or credit mapping here. Outside the repository, [ERC-1967](https://eips.ethereum.org/EIPS/eip-1967) defines the implementation slot and recommends upgrade events. Its reference code also shows why a slot-changing execution and an event's position are distinct. [Ethereum JSON-RPC](https://ethereum.org/developers/docs/apis/json-rpc/) exposes log coordinates and block-scoped storage reads; a block slot read supplies no intermediate transaction state.

## 3. Constraints and non-goals

The starting tree is `41a21f8e065ce086d3ec4355c057b2623b28f205`, base ref `main`, on the controller's exact derived worktree. The required interpreter is Python 3.14.6 from `.python-version`; `/opt/homebrew/bin/python3.14` reports that version. The existing plugin baseline completed 642 tests in 50.511 seconds with exit 0, recorded by Fiat at `/private/tmp/alexandria-epoch-baseline.log`. This is a baseline, not a performance result for the change.

Always run the checked runner with the actual diff and required scopes, the plugin suite, Imprimatur on new prose, portable sync/check, and Horos scan plus `--census --write` before the commit gate. Stage census output. The parent owns Linux portability checks, signing, controller receipts and publication.

Ask first for a new dependency, public ABI or storage-layout change, CI change, widened trust boundary, or alteration of released digests. None is selected here. The requested derived receipt revision is part of the authorised attribution change. Never change preserved raw bytes, key material, vendored code, or a failing test merely to pass.

Non-goals: multiple upgrades within one block or transaction; implementation inference for non-upgrade events inside an upgrade transaction; a first-block upgrade with no preceding implementation evidence; new archive reads, methods or network paths; transaction-state proofs; event interpretation; new markets; previously filed sibling work. Each unsupported case refuses positional attribution instead of guessing.

## 4. Candidate constructions and selection

`block-only` keeps the current whole-block split. It preserves the input protocol but assigns the before-upgrade specimen to the new implementation and accepts ambiguous same-transaction emissions.

`position-boundary` orders boundaries by `(block, transaction_index, log_index)` and preserves the current opening-read protocol. A block slot read confirms the one announced upgrade in that block. An initial slot read supports the initial epoch only when no upgrade occurs in the interval's first block. Two upgrades in one block still refuse: the one final slot word cannot independently confirm both. Ordinary proxy logs in an upgrade transaction refuse regardless of whether their log index precedes or follows the upgrade announcement. This costs supported scope while keeping the inference within preserved evidence.

`design/build_design_evidence.py` executes both small models against five before/boundary/after specimens and two ambiguous specimens. It records their actual outputs and derives protocol counts from each construction. Both declare zero extra RPC methods and zero extra release components; these are design counts, not measured production time or memory. Only `position-boundary` satisfies both correctness and refusal gates. `design_evidence.py --transition design-lock` exits 0 under `unique-frontier`. The checked matrix covers correctness, recovery, compatibility, time and space. Its model checks select a construction and establish no production conformance.

The exact representation is a new `alexandria-interval-receipt/v2` with a closed positional epoch schema. Each epoch adds `start_position` and `end_position`, the latter exclusive. Each position is exactly `{block_number, transaction_index, log_index}`, with decimal-string block number and integer or null indexes. The first starts at interval-start before all logs; the last ends at interval-end-plus-one before all logs. Use explicit nullable transaction/log indexes for block-edge sentinels; require both null together, never invented negative indexes. Interior boundaries carry non-negative transaction and log indexes plus the transaction hash and block hash from the preserved upgrade. Adjacent positions match exactly. Retain `start_block`, `end_block`, `start_hash` and `end_hash` as the block envelope. Its start block equals `start_position.block_number`; its end block equals `end_position.block_number` for an interior boundary and one less for a block-edge sentinel. The hashes name those envelope blocks. A block containing an interior boundary belongs to both envelopes, so whole-block tiling is no longer their validator. Extend each non-null `upgrade` with `transaction_index`; its coordinates must equal `start_position`.

Discovery must receive all preserved proxy logs rather than discarding ordinary events before it runs. Validate canonical coordinates, strict ordering, unique positions, transaction-index/hash agreement within a block, and consistent block hashes. Within each block, transaction indexes never decrease and block-wide log indexes strictly increase even across different transactions. Reject missing, bool, negative, malformed, duplicated, inconsistent or out-of-range positions. A shared attribution operation places each accepted log in exactly one epoch and refuses every ordinary proxy log in the boundary transaction. Expose per-log ownership in a v2 `log_attributions` array. Each row contains exactly `block_number`, `block_hash`, `transaction_hash`, `transaction_index`, `log_index`, `epoch_index` and `kind`. Blocks are decimal strings, indexes are non-negative integers, `epoch_index` is zero-based, and `kind` is `proxy-log` or `upgrade-boundary`. Rows follow the validated log order. A plan omitting logs retains the existing omission gap and an empty attribution array; it cannot claim coverage of unpreserved logs or exclude unseen upgrades. `check` compares the array with fresh derivation rather than merely counting epochs. The upgrade announcement itself records the new boundary without claiming a delegatecall emitter.

Production `build` emits v2 by default. Existing v1 release verification retains its explicitly block-only meaning and immutable schema. It cannot claim positional attribution even for logs earlier in an upgrade block. The fixture-specific reconstruction path may project the new derivation to the historical v1 receipt only to reproduce the old demonstration's exact release; do not add a general public legacy-build flag just to satisfy a fixture. Preserve the old expected identifiers and all raw fixture bytes. A separate v2 demonstration and expectation record the new identifier. The stronger result belongs to that new release.

Four production conformance criteria remain pending at integration: `production-attribution`, `legacy-release-identity`, `offline-rederivation`, and `resume-and-refusal`. Their exact resolver is `python3.14 .hexaemeron/design/conformance.py <criterion>` and their selected-candidate report is `reports/conformance/position-boundary-<criterion>.json`. Step 1 must implement the executable harness; a report is written only after its command executes the named assertions. The runbook may require these earlier but must not change the accepted design record. Rejected-candidate conformance remains pending and is never reported as run.

## 5. Risk register

```risk-register
before-upgrade-log | a proxy log earlier in the upgrade block | it belongs to the preceding implementation in v2
transaction-ambiguity | ordinary proxy events inside the upgrade transaction | refuse both before and after the announcement without execution evidence
first-block-upgrade | an end-of-block initial slot read | refuse positional discovery when no preceding implementation is preserved
multiple-upgrades | more than one upgrade in a block | refuse without collapsing the events into a block-keyed mapping
coordinate-shape | provider log positions and hashes | reject missing, bool, negative, duplicate, contradictory and unordered coordinates
position-tiling | adjacent epoch starts and exclusive ends | every accepted log has exactly one owner and sentinels cannot create gaps
slot-code-binding | upgrade announcement and preserved slot and runtime bytes | retain every existing address, hash and code comparison
all-log-paths | collect, build and offline check | every preserved proxy log reaches the same attribution rule
legacy-scope | old v1 releases and new v2 receipts | preserve old bytes and identifiers and never advertise v1 as positional
forged-attribution | internally rebound release components | check re-derives ownership from journals and refuses a moved boundary or owner
restart-evidence | journal offsets and opening replay | interruption preserves the existing committed-prefix rule and raw journal identity
bounded-derivation | maximum logs, epochs and journal sizes | retain existing caps and avoid per-log copies of entire journals
```

## 6. Glossary

An implementation epoch is the interval of supported positions assigned to one implementation and code digest. A position is block number, transaction index and block-wide log index. An exclusive end belongs to the next epoch. A block-edge sentinel denotes a position before all logs in that block. An upgrade announcement is preserved boundary evidence. An attribution is a bounded inference from those records, not execution proof.

## 7. Source inventory

Primary pointers are the ledger, runtime contract, current implementation and v1 schema named above; the two merged PRs; the source-bound audit synopses; ERC-1967 and Ethereum JSON-RPC. `plugins/alexandria/examples/usdc-interval-live-v0` holds the immutable live source and expectation. `plugins/alexandria/examples/usdc-interval-v0` holds the synthetic baseline. `plugins/alexandria/docs/usdc-interval-live-study.md` and its runbook preserve the earlier design.

The new study, design generator, model observations and selection reports live under `.hexaemeron` until Step 1 commits repository copies under `plugins/alexandria/docs/usdc-interval-epochs/`. Controller files themselves stay controller-owned. Every path in the runbook must name whether it is a committed source, an exact working copy, or a produced report.

## 8. Signals and on-call questions

Follow `plugins/hexaemeron/skills/ephoros/SKILL.md`. Which preserved log cannot be placed? The refusal identifies a bounded block, transaction index, log index and reason. Which receipt semantics were checked? The check result identifies v1 block-only or v2 positional meaning. Can the operator resume? Existing checkpoint and error receipts retain their codes and committed ranges. Add no endpoint, response dump or high-cardinality telemetry label.

## 9. Trust boundaries

Follow `plugins/hexaemeron/skills/phylax/SKILL.md`. Log fields are untrusted structured input and require typed validation before indexing or comparison. A digest-bound receipt can still contain an invented ownership declaration; only replay establishes agreement. Existing no-follow paths, byte limits and response-envelope checks remain in place. No new network capability or dependency is selected. Boundary/refusal evidence belongs in controlled error messages and tests, without provider exception text.

## 10. Performance budget

Follow `plugins/hexaemeron/skills/metron/SKILL.md`. No speed or memory improvement is claimed, and the new construction adds zero RPC methods and zero release components. Keep the existing limits, derive sorted ownership in a bounded pass, and avoid copying full journals per epoch. Production duration and peak memory remain unmeasured. If implementation changes a performance-sensitive path beyond this bounded derivation, record a same-workload baseline before that change; the 642-test run does not substitute for a workload measurement.

## 11. Failure and guards

Follow `plugins/hexaemeron/skills/elenchus/SKILL.md`. Missing or inconsistent coordinates, unsupported upgrade histories, mismatched code and any unresolved selected conformance report stop their dependent transition. Recovery is inspection, a correctly scoped new capture, or a new release; verification never edits evidence. The mandatory guard uses a literal before-upgrade log and asserts its old ownership. The old implementation must produce an assertion failure, not an import error or a fabricated failure count. Offline tampering guards rebuild self-consistent manifests through the real ingest and check path.

The conformance harness must cover before/after placement, upgrade-at-last-block, first-block refusal, both same-transaction ordinary-log refusals, multi-upgrade refusal, malformed coordinates and contradictory hash/index pairs. Compatibility must reproduce the historical live and synthetic release identifiers and demonstrate that a v1 result makes no positional promise. Resume evidence reuses interrupted collection and checks journal byte identity. Actual command exits, zero skips and report paths are returned to Fiat.

## 12. Decisions and their homes

Follow `plugins/hexaemeron/skills/hypomnema/SKILL.md`. The new receipt version, its exclusive-end semantics and v1 compatibility are expensive to reverse and belong in `plugins/alexandria/docs/usdc-interval-epochs/decision.md`, linked from the collector document and schema index. That record must explain the same-transaction and first-block refusals and why multiple upgrades remain unsupported. Keep implementation field comments next to the positional validator; the collector document owns operator recovery and evidence scope.

Step 1 commits study, runbook, design record, model reports and a future conformance harness with the existing toolchain. The implementation step owns the new representation, all-log derivation and backwards reader. The last step demonstrates both versions, runs pending conformance, updates the frontier and generated source coverage, and cold-reads and reconciles all mutable first-party marketplace prose under the shared versioning contract. No implementation, receipt, commit or publication was performed by Surveyor.

### Amendment -- 2026-09-08

**What changed.** The standing home for the selected design is `plugins/alexandria/skills/alexandria/EVOLUTION.md`. Step 1 adds a prose-only decision section recording the selected positional construction, rejected block-only alternative, compatibility and refusal reasons; no version, frontier header or history row changes until Step 3. The previously proposed `plugins/alexandria/docs/usdc-interval-epochs/decision.md` will not be created. Collector and schema prose point to the ledger. The selected candidate and every criterion remain unchanged.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | position-boundary
record | plugins/alexandria/skills/alexandria/EVOLUTION.md
```

**Why.** Hypomnema assigns a governed skill's decision to its existing ledger and requires this bridge before a study ships. A second decision file would create two standing homes.

**Steps touched.** Step 1 records and checks the ledger bridge. Step 2 documents the interface against that ledger. Step 3 appends the one earned evolution row as planned.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
