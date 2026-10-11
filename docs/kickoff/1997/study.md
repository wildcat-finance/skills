# Wildcat archive event timestamps

Assuming, unless corrected:
1. Issue #1997 is one producer-to-consumer timestamp delivery. New bounded V1/V2 captures must preserve headers for selected-event blocks; existing immutable releases remain readable.
2. Recorded provider headers establish recorded timestamps, not canonical-chain membership, finality, publisher identity or independently proved events.
3. The prototype uses constructed V1/V2 transports and the available retained intervals. No fleet recapture, provider credential change or private payload publication is required.
4. The source starting ref is `21c151b7fe0cb80589c2ba8713678dfaee52354d`; packet `base_ref=main` resolves to that pinned study base. Installed Fiat 6.78.1 remains the controller; the receipted source's 6.84.1 gap is an administrative limit, not permission to replace it.

## 1. Problem statement

Probitas archive records currently set `observed_at=None`. Tabularium declares every archive timestamp unsupported. Alexandria V1/V2 opening reads preserve the interval's first header and subject-first headers, while shard journals preserve shard-end headers. Most selected event blocks have no preserved timestamp.

For a researcher reading an archive dossier, a working prototype dates each supported `market_terms`, `market_closed`, `borrow` and `repayment` record from a preserved header at that event's exact block number and hash. Missing, wrong-number, wrong-hash, malformed or conflicting evidence leaves that record undated with a specific gap. Neither zero, a neighbouring timestamp nor the native `MarketClosed` argument substitutes for the block timestamp.

Success criteria are checked by the future `plugins/tabularium/tests/prove_wildcat_timestamps.py` runner, with `--case` and `--report`:
- `capture`: new opted-in V1/V2 fixture captures retain one bounded header response per distinct selected-event block; duplicate events do not cause duplicate header requests; interrupted capture and resume retain source-bound bytes.
- `mapping`: offline Tabularium joins exact number/hash, retains nested response/component provenance, and records row-local support. Wrong hash, missing header, wrong number, duplicate conflict and malformed timestamp cases remain unsupported or visibly refused by the owning input validator.
- `consumer`: Probitas receives integer epoch seconds and timestamp references for supported rows; unsupported rows retain absent dates and per-record reasons. Dossier verification preserves the field and gap.
- `integration`: bounded V1/V2 capture-to-view-to-dossier demonstrations, legacy release verification and negative controls pass. The controller and source command are named in the report; tests establish those observations only.

## 2. Prior art

The last merged change to the archive route is [PR #1904](https://github.com/wildcat-finance/skills/pull/1904), commit `16d64a439`: offline archive semantics, four record families, native amounts and explicit unsupported state. It carries subgraph retirement to #1896. [PR #2075](https://github.com/wildcat-finance/skills/pull/2075) is the latest adjacent Wildcat event delivery: canonical events and offline reproduction; #1386 and #1387 remain downstream. Its canonical SafePath guard verdict remains inconclusive, and unlocalized historical Hex/native failures remain unknown. No cause or retrospective guard is inferred here. The canonical transaction timestamp is a separate schema boundary and stays outside this delivery.

The shared collector's two recent merged deliveries were also read: [PR #2069](https://github.com/wildcat-finance/skills/pull/2069) preserves Aave-specific venue/epoch behaviour and carries transaction-index reconciliation to #1958 and independent venue work to #2004-#2007; none enters this Wildcat timestamp change. [PR #1912](https://github.com/wildcat-finance/skills/pull/1912) binds each physical journal to reconciliation bytes while preserving legacy identifiers and explicit absent-binding gaps. Its V2 historical checkpoint has no staging digest; this run does not upgrade that unknown. Exact fetched records are in `.hexaemeron/reports/pr-2069.json` and `pr-1912.json`.

Alexandria's subject-specific opening is in `plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v1.py` and `wildcat_v2.py`. `usdc_interval.py` derives and replays an exact opening-read sequence. Unconditionally appending event reads to that sequence would invalidate old releases. Existing `boundary-blocks` journals and `epoch-evidence` headers are reusable only when they exactly match a row.

Whole-set `audit_synopsis.py --check .` returned 0 before synopsis use. The six authoritative sources and corresponding views captured in `.hexaemeron/reports/audit-reading.json` are the Tabularium and Probitas plugin audit logs and rounds for #1731, #1374, #1384 and #1378. The record preserves each complete synopsis, source/view digests, every finding id/status, Covered, Not checked, Elenchus verdict and Leads not pursued. Sources remain authoritative; absent legacy fields remain unknown.

Carry forward the fixed mechanisms: #1731 `W9-R1-03` binds checkpoint and journal bytes on resume; `W9-R2-02` closes handles after deferred receipt-write failure; `W9-R1-05` preserves targeted-trace coverage gaps. Tabularium `E1-R1-03`, `E1-R3-02` and `S4-R1-01` require timestamp/hash/source consistency; `S2-R1-01` preserves source/output separation; `S3-R2-02` refuses nonregular ingress. Existing guards remain active; the new timestamp test matrix covers the newly added boundary. #1384's provider-message and custody-digest repairs remain in place. Its earlier environment-limited Elenchus verdicts are not strengthened.

Outstanding historical prose and environment items stay named: #1731's `W8-R1-01` provider-class wording/gate-command-budget limit belongs to #1762; `W7-R1-01` is historical runbook arithmetic, not timestamp product work. #1374's spaced-path reporter expectation remains an audit lead, not a new timestamp defect. Probitas's accepted action-tag pinning, key-name personal-data guard, English-number sieve, bare-URL citation limit and withdrawal-expiry citation remain unchanged. #1384's tree-dependent tests, missing-field demo traceback and unbudgeted proof timings remain outside this delivery. No newly assigned unresolved audit finding requires a product inoculation in this scope; the issue's current missing timestamp is the implementation target.

Measured retained inputs: current `make_wildcat_view` verified V1 release `eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`, 144 archive rows in 117 distinct event blocks, and V2 release `2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`, 1,997 rows in 1,940 blocks. The separate digest-checked native-log census contains 390/15,155 distinct log blocks; only 8/95 have matching preserved opening or shard-boundary headers. These populations differ: the larger counts cover every native log, not only mapped archive families. Evidence is in `archive-census.json` and `retained-census.json` under `.hexaemeron/reports/`.

Lazarus #1384 committed plan metadata names fixed anchors V1 22074622 and V2 26022093. The V1 anchor occurs among retained native log blocks; the V2 anchor does not. Fixture payloads were not located by the bounded local search and no fixture verification was run. Their exact header contents and timestamp contribution remain unknown; a single fixed anchor cannot supply all 117/1,940 archive event blocks. ADR-110 retains Miskatonic custody; no payload is copied into this repository.

Outside the organisation, Ethereum JSON-RPC `eth_getBlockByNumber(number,false)` supplies recorded header number/hash/timestamp. No external timestamp API, subgraph interpolation or proof upgrade is needed.

## 3. Constraints and non-goals

Use Python 3.14.6 observed in this shell and the repository's existing stdlib/declared dependencies. Worktree fingerprint `issue/16777234-1428265077` was verified before these writes. Keep the raw release immutable and all current legacy receipt/journal rules intact.

Always: retain native event bytes, complete RPC envelopes, selector/digest evidence and unsupported-field reasons; run the timestamp runner plus repository selected checks before admission; preserve existing audit history and signed source boundaries. Ask first: new external dependency, CI policy change, fleet recapture, public private-payload release or wider chain/venue coverage. The user already authorized the bounded timestamp feature, including its additive opt-in capture representation. Never: persist secrets/raw provider errors, rewrite a released digest, delete a failing guard, invent a timestamp or claim an unrun check.

Non-goals: canonical schema-3 transaction timestamps, state replay, delinquency duration, batch status, lender balances, subgraph retirement, current standing, borrower identity, chain proof, settlement, provider independence and universal performance claims. Existing raw captures receive no silent retrofit.

## 4. Design options

`existing-only` joins preserved headers without collection. It has no new input surface but leaves most future records undated and fails the future-coverage selection gate.

`collector-journal` is selected. New Wildcat plans opt into a bounded, additive event-header journal/component whose exact format/version marker distinguishes its request/coverage obligations. Existing plans without that marker retain their existing opening sequence and component inventory. After selected logs are known, the producer deduplicates block number/hash pairs, reuses matching captured headers where possible and collects each remaining header once. Request count, response bytes, journal partitions and elapsed limits remain explicit; the new feature cannot bypass the transport or aggregate budgets. An opted-in incomplete journal is never labelled complete. A new capture marker and complete inventory must bind checkpoint/resume and offline verification.

Tabularium indexes verified opening, boundary and optional event headers by exact number/hash. It derives integer timestamps, source selectors/digests and row-local support; duplicate contradictory candidates cannot be resolved by last-write-wins. Probitas carries the derived date and timestamp reference into each record while preserving unsupported rows and capture gaps. Old releases without the optional journal remain valid and only supply the dates their available headers support.

`external-sidecar` captures separately supplied supplements, allowing old-release enrichment but introducing another independently supplied input and custody join. It loses the extra-supply-boundaries metric to the integrated journal. Sidecar recapture is deferred; nothing prevents a later scoped delivery.

`.hexaemeron/design-evidence.json` covers all three candidates and correctness, time, space, compatibility and recovery. Eighteen selection reports ran their recorded command. The executable proposal model deduplicates four observations into three requests and demonstrates missing/wrong-hash lookups; source assertions expose the unchanged legacy opening and current absent consumer date. Its bounds and immutable recovery are model observations, not production implementation evidence. The extra supplied input count is 0 for the integrated journal and 1 for sidecar. `unique-frontier` selects `collector-journal`; active installed `design_evidence.py --transition design-lock` returned 0. Production conformance remains pending at integration, resolved by the timestamp runner's integration command into the selected candidate's closed report. The runner must emit the declared `protasis-design-report/v1` report when used as that resolver, separately from its audit test-counter report.

## 5. Risk register

```risk-register
legacy-opening | plan and exact opening-read replay | absent opt-in keeps old requests and releases valid
header-identity | raw event and header join | require exact block number and hash before supplying a date
header-conflict | repeated preserved headers | reject ambiguity instead of selecting first or last
quantity-shape | timestamp decoding | malformed, boolean, negative, oversized or unbounded values never become dates
missing-evidence | row-local timestamp support | missing or mismatched headers retain unsupported reason and absent date
request-budget | event-driven header fanout | deduplicate block pairs and enforce declared request byte time and partition limits
capture-resume | checkpoint and journal identity | interrupted work cannot relabel incomplete headers complete or reuse changed bytes
capture-secrets | transport failure and diagnostics | provider URL credentials and raw provider errors never persist
source-reference | nested RPC response and dossier record | component response selectors and digests identify the supplying header
evidence-class | provider records to dossier | recorded timestamp stays recorded and no chain proof is inferred
release-compatibility | opted-in format and offline check | validate new inventory without requiring it in old releases
consumer-gaps | supported and unsupported mixed rows | retain per-record dates and gaps through render and verification
output-alias | capture view report and evidence paths | outputs cannot replace preserved source or follow links
report-truth | tests and design conformance reports | report executed counts exits source command and limitations accurately
```

## 6. Glossary seeds

Event block: block number/hash pair carried by a selected native log.
Header timestamp: unsigned epoch seconds from the matching preserved RPC header.
Timestamp support: row-local admission of a date with its header reference, or an explicit unsupported reason.
Event-header journal: opted-in bounded raw component containing the exact header requests and responses required by selected logs.
Legacy release: release without the new opt-in marker, verified under its existing inventory/opening rules.
Recorded: provider bytes retained and checked internally; no canonical-chain claim.

## 7. Sources

The issue is [#1997](https://github.com/wildcat-finance/skills/issues/1997). Prior deliveries are [#1904](https://github.com/wildcat-finance/skills/pull/1904) and [#2075](https://github.com/wildcat-finance/skills/pull/2075).

Source files at the starting commit are `plugins/alexandria/scripts/usdc_interval.py`, `plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v1.py`, `wildcat_v2.py`, `plugins/tabularium/scripts/tabularium_lib/wildcat_view.py`, `plugins/probitas/scripts/probitas_lib/wildcat_archive.py`, `plugins/probitas/scripts/probitas_lib/evidence.py` and their existing fixture/tests. They are reachable from the [pinned source tree](https://github.com/wildcat-finance/skills/tree/21c151b7fe0cb80589c2ba8713678dfaee52354d).

Preservation scope is in `plugins/lazarus/examples/wildcat-boundary-v0/plans.json` and `docs/decisions/ADR-110-keep-wildcat-boundary-fixtures-in-miskatonic-custody.md` at the same pinned tree. The audit sources/views and source-bound census reports are identified in section 2. Ethereum's method is documented in the [JSON-RPC reference](https://ethereum.org/en/developers/docs/apis/json-rpc/#eth_getblockbynumber).

## 8. Signals and on-call questions

Follow [Ephoros](https://github.com/wildcat-finance/skills/blob/21c151b7fe0cb80589c2ba8713678dfaee52354d/plugins/hexaemeron/skills/ephoros/SKILL.md). Capture asks: how many distinct event blocks require headers, which failed, and which limits stopped progress? Reuse bounded existing progress/error records with block identity and fixed refusal codes. View/dossier asks: how many records have dates and which remain unsupported? Expose bounded counts and row-local reasons in existing outputs and verification reports. No background service or telemetry exporter is added.

## 9. Trust boundaries

Follow [Phylax](https://github.com/wildcat-finance/skills/blob/21c151b7fe0cb80589c2ba8713678dfaee52354d/plugins/hexaemeron/skills/phylax/SKILL.md). Network responses cross the existing bounded transport into a versioned journal; enforce exact RPC envelope/request relation, quantity/hash shape, interval scope and existing credential sanitation. Files cross release admission into an offline view through confined regular-file inventory/digest readers. The date crosses into Probitas only with its matching source reference; no identity or stronger evidence class follows. New optional journal admission never weakens old source/output safety.

## 10. Performance budget

Follow [Metron](https://github.com/wildcat-finance/skills/blob/21c151b7fe0cb80589c2ba8713678dfaee52354d/plugins/hexaemeron/skills/metron/SKILL.md). This is no speed optimization. Added requests are bounded by distinct selected-event blocks lacking reusable matching headers, rather than number of records or interval width. The fixture runner's capture case measures requested block count, retained bytes and peak bounded collection size, before/after on identical fixture inputs. Existing time/component/aggregate limits stay authoritative. Do not promise historical wall-clock bounds from the 117/1,940 retained block counts; provider latency and full capture run were not measured.

## 11. Fail-closed posture

Follow [Elenchus](https://github.com/wildcat-finance/skills/blob/21c151b7fe0cb80589c2ba8713678dfaee52354d/plugins/hexaemeron/skills/elenchus/SKILL.md). A malformed opted-in capture stops positive verification. Missing/mismatched timestamp evidence blocks the date on that row, preserving the usable native record and explicit gap where the underlying release remains valid. Structural raw-release violations still refuse the whole owning operation. Guards must fail on the unfixed source through the exact runner with one `{report}` argument, then pass on the signed fixed tree; environment errors remain inconclusive. The runner must initialize sibling imports before SafePath-sensitive imports and distinguish test-counter evidence from design reports.

## 12. Decisions and homes

Follow [Hypomnema](https://github.com/wildcat-finance/skills/blob/21c151b7fe0cb80589c2ba8713678dfaee52354d/plugins/hexaemeron/skills/hypomnema/SKILL.md). Record additive opt-in event-header preservation and legacy compatibility in `docs/decisions/drafts/preserve-wildcat-event-block-timestamps.md`. Its trade is a bounded producer extension against a new sidecar input; its evidence boundary retains provider-recorded class and per-row unsupported dates. Update `plugins/alexandria/docs/usdc-interval-collector.md` and `plugins/tabularium/docs/wildcat-archive.md` with marker, inventory, counts, recovery and exact timestamp semantics; Probitas's venue reference explains mixed supported/unsupported dates. Keep private custody paths in local evidence only. No release relocation, payload publication or standing interpretation is decided here.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | collector-journal
record | adr/preserve-wildcat-event-block-timestamps
```
