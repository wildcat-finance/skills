# Wildcat parameter, access and controller canonical events

Assuming, unless corrected:

1. The starting tree is `main` at `8b4e137917d754a7b7c3d5e74d141c0bedf70aa2`, Python is exactly `3.14.6`, production remains stdlib-only, and the user authorised #2090 through Fiat integration and merge.
2. The issue's first four groups mean the concrete ABI declarations at the starting tree: 29 generation, emitter-role and signature contexts, represented by 58 concrete-ABI entries. Hooks templates are distinct from hooks instances. No role enum, new-value-versus-difference interpretation, or market for a marketless hooks event is established.
3. Retained inputs are local preserved Alexandria releases, rebuilt only from the two operator-provided staging trees. The public record carries release identifiers, digests and pass/refuse booleans only. Retained payloads, paths, counts and observed/absent signature inventories remain private.
4. The orchestrator reserved adapter `1.1.0` for #2089, `1.2.0` for this issue and `1.3.0` for #2091. This independent run implements `1.2.0` parameter/access meanings against the starting tree and retains `1.0.0`; integration after #2089 composes fee meanings into `1.2.0` while retaining the exact `1.1.0` capability set. Unmerged sibling code is no evidence here.
5. Historical positives can be claimed only for signatures actually present in retained inputs. If the user's literal acceptance requires a positive retained observation for every signature absent from those captures, integration stops until the user accepts explicit missingness or supplies additional evidence. Constructed events never cure historical absence.

## 1. Problem statement

Issue [#2090](https://github.com/wildcat-finance/skills/issues/2090) asks Tabularium to give native canonical meaning to market parameter and access changes, V1 controller authorisations and temporary reserves, and V2 hooks-instance configuration/access changes. Those logs currently decode but stay `unsupported-canonical-meaning`. Consumers that cannot interpret native logs have to quarantine transactions containing them.

A working prototype maps every applicable ABI context in the first four groups on public constructed specimens. It maps every observed applicable retained record, preserves each numeric/string value under the exact ABI field name in `mapping_records[].decoded`, identifies emitted markets and affected accounts, and supplies a signature-specific reason for every unsupported event in the final group. Every new state row has empty financial `amounts`. Native values carry no new-value, delta, role-label, standing or accounting interpretation.

The demonstration controller is `plugins/tabularium/tests/prove_wildcat_parameters.py`. Its `mapping-conformance`, `schema-compatibility` and `retained-conformance` criteria run real tests or retained rebuilds and write `protasis-design-report/v1` reports. The final proving path rebuilds and verifies both new public specimens, verifies the historical examples under their recorded adapter version, executes the retained criterion with operator-supplied staging variables and runs `python3 scripts/run_checks.py --base 8b4e137917d754a7b7c3d5e74d141c0bedf70aa2 --scope root --scope tabularium --scope repo-lints --format json`. Report freshness and exact argv belong to the proof runner. A true result establishes only those bounded observations.

Success criteria:

- `mapping-conformance` proves all 29 required contexts map, their concrete variants decode, exact native fields survive, account/market parties match emitted addresses, no context-only market or role label appears, final-group reasons are signature-specific, and malformed or wrong-role events refuse or remain named gaps.
- `schema-compatibility` proves Python/schema parity, exact action/role/party/amount cardinalities, rejected version mixtures and unknown keys, byte-identical historical example rebuilds and verification under `1.0.0`, and new `1.2.0` releases in fresh directories.
- `retained-conformance` revalidates and rebuilds both retained raw releases, maps and verifies new canonical releases, checks every observed required signature and all observed final-group dispositions, and refuses a generation with no required target record. A private inventory records historical absences. User acceptance of absent historical positives remains a separate integration prerequisite.
- Mutation tests change/reorder canonical rows, decoded native fields, parties, rules, selectors and coverage after rebinding superficial digests; verification refuses semantic mismatches. Reordering the input container alone is permitted because native block, transaction and log positions define order; changing those positions must change the rebuilt result or refuse.

The runbook should contain three steps: scaffold the proof/report interfaces and public design evidence; deliver the versioned mapping, closed schemas and public constructed specimens; then deliver the retained resolver and final demonstration. These are phases of one adapter extension, not separate user-facing modules.

## 2. Prior art

`wildcat_abi.py` already binds concrete historical ABI layouts to generation, emitter role, source input and source declarations. `.hexaemeron/design/event-inventory.json` is a generated inventory of those starting-tree declarations. `wildcat_rows.py` preserves every decoded record, raw log, source selector, context, disposition and limitation. `_primary` currently maps 25 baseline contexts; `wildcat_validation.py` and the two schema files close that vocabulary. No new ABI or live collection is needed.

`wildcat_release.py` verifies a copied raw release and reconstructs all four semantic release files. Its `_outputs` currently always uses the current adapter, which makes an adapter bump alone strand old releases. The selected design adds explicit supported-version dispatch and leaves raw evidence and all published release bytes unchanged. `docs/release-policy.md` requires a new interpretation version and a new release directory. `ADR-111` records native roles; `ADR-124` keeps event-block timestamps separate. `mapping_records[].decoded` is the existing home for native state, so the canonical envelope gains no generic state object.

The last two merged pull requests touching Tabularium were read: [#2120](https://github.com/wildcat-finance/skills/pull/2120), merged at this starting commit, adds declared V2 wrapper contexts and carries no work; [#2111](https://github.com/wildcat-finance/skills/pull/2111), merge `50d78f7d2f5fc8fa6dab3cc2fc2dc1b81346b098`, makes the bridge-record test follow the numbered ADR and carries no work. The relevant batch implementation and retained evidence in [#2097](https://github.com/wildcat-finance/skills/pull/2097) and [#2104](https://github.com/wildcat-finance/skills/pull/2104) were also read. Their adjacent-burn meaning, reserved-assets qualification and public/private custody boundary remain fixed. This run does not reopen #1386 or #1387, infer downstream accounting or rerun #1378's checkout-bound saved admission.

Audit reading used verified synopses after the whole-set `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero. The authoritative sources are `plugins/tabularium/audit/AUDIT.md`, `audit/rounds/fiat-1378-wildcat-v1-v2-canonical-adapter.md` and `audit/rounds/fiat-2087-wildcat-withdrawal-batch-canonical-meaning.md`; the matching `.synopsis.md` views were read, with the plugin source's `AUDIT_SYNOPSIS.md` name. The generated views preserve finding ids/status, Covered, Not checked, Elenchus verdict and Leads not pursued. Missing legacy fields remain unknown. Earlier generic Euler defects stay fixed regression coverage; they do not authorise changes outside this adapter.

Relevant history: #1378 `S2-R1-01` fixed constructed subjects that did not exactly match emitter contexts; `S2-R1-02` fixed the `supporting-routing` spelling. Its `S4-R1-01` and `S4-R2-01` fixed an executor's unsafe identities and relative serialized source root; this run does not change or reuse that executor. #2087 `S3-R1-01` fixed a public description of the two-burns case; `S4-R1-01` fixed a vacuous retained-conformance success. Those source defects are fixed on the starting tree. The earlier reporter's bare sibling import made canonical Elenchus inconclusive under `PYTHONSAFEPATH=1`; the new scaffold must insert its explicit sibling path before import and test safe-path execution. Neither that historical verdict nor an unknown original broad-check failure becomes a clean result here. Existing staging-path ancestor-link and reporter sidecar-order leads inform the new private resolver and create-only writer tests.

Both operator-supplied staging trees were validated against the public manifests and rebuilt through the public Alexandria builders during study research. `.hexaemeron/design-reports/retained-input-check.json` records only the raw identifiers, inventory digest and non-vacuous booleans. The per-signature inventory remains in private custody and confirms that literal all-signature historical positives are unavailable from these inputs. This is an evidence-availability result, not new-mapping conformance.

External prior art is the exact Wildcat V1/V2 source declarations already retained by `wildcat_abi.py`, including FixedTermHooks' two concrete variants and OpenTermHooks. This run uses those source-bound ABI meanings and introduces no outside service, package, financial interpretation or fresh compiler claim.

## 3. Constraints and non-goals

The exact base and interpreter are in the assumptions. The package begins at `0.6.4`, the governed skill ledger at `tabularium-v0.7.0`, and the baseline Wildcat adapter at `1.0.0`; these are independent axes. Each product step follows the package-release gate across both host manifests, both marketplaces and the propagation test. The interpretation extension earns the next governed generation after the integration base while preserving the held Compound Phase 1 frontier. The runbook should use `next-generation-after-integration-base` rather than predict a concrete governed target that concurrent runs may consume.

Always: preserve published canonical/source/capture/coverage bytes and modes, exact ABI names, unsupported scope, prior rules, evidence classes and path safety; regenerate owner-produced portable and Horos artefacts before recording green; run local selected checks before push. Ask first: widening publication rights for retained material, replacing an absent retained positive with an invented capture, changing queue/frontier ownership, or changing the user's historical-acceptance interpretation. Never: invent role enums, market/account parties, financial conversions, borrower identity, sanctions standing, complete access policy, chain proof or publisher authenticity.

No Solidity changes, ABI compiler rerun, RPC collection, access-policy replay, downstream Probitas changes, fee accrual semantics or sanctions cash-flow semantics belong to this issue. #2089 and #2091 own the two latter deliveries. Independent development must not import their unmerged changes. At integration, the signed base's previously delivered meanings are preserved by capability union and the affected schema/verification tests rerun.

## 4. Design options

`native-fields` adds a closed table keyed by generation, concrete admitted role and signature. It gives each event a venue-qualified state action, empty amounts, emitter party, only emitted additional parties, and unchanged decoded native values. Marketless hooks remain scoped to the hooks instrument. Its trade is that downstream readers must keep native role codes, basis-point values and timestamps uninterpreted.

`contextual-projection` adds interpreted authorisation names, converts parameter values and fills a market from context or neighbouring records. Its trade is stronger-looking rows based on questions the issue explicitly leaves unchecked. The selection probe rejects those assumptions.

The closed `.hexaemeron/design-evidence.json` selects `native-fields` under `unique-frontier`. Five selection criteria cover correctness (`source-bound-fields`), time (`unbounded-lookups`, a count of additional contextual searches), space (`auxiliary-state`, a count of additional contextual indexes), compatibility (`legacy-replay-plan`) and recovery (`fresh-output`). `.hexaemeron/design/selection_probe.py` executes a finite policy model for each candidate/criterion and emits ten exact reports. The count metrics describe the design model; they measure no production wall time or peak resident memory. Three conformance criteria remain pending with exact resolvers: mapping and schema block `step:3`, retained evidence blocks `integration`.

All new actions use `pool-state`, a new role-qualified instrument and empty amounts. Market emitters carry `pool`; controller and hooks-instance emitters carry `controller` and `hooks-instance` respectively. Add `pool` only when a non-market event emits `market`, and `affected-account` only from `account`, `accountAddress` or the ABI decoder's exact empty-string key `""` for unnamed V1 lender events. Preserve `providerAddress` as `role-provider` when emitted. A market emitter establishes its own market identity without borrowing a separate context. A hooks/controller record that emits no market names no pool party even when context knows associated markets. Its limitation records this scope.

New action suffixes come from the native event name in kebab case. Market suffixes are `annual-interest-bips-updated`, `max-total-supply-updated`, `reserve-ratio-bips-updated`, `authorization-status-updated` and `account-sanctioned`, applicable only where declared. Controller suffixes begin `controller-`; hooks-instance suffixes begin `hooks-`. Mapping rules are `<generation>.<suffix>.v1`. Closed schemas and validators enforce those exact tables and declared versions; neither shared topic text nor a known selector admits another role.

The exact required inventory and final-group reason table follow. Every changed value remains in `decoded` under its ABI name. `AnnualInterestBipsUpdated` preserves `annualInterestBipsUpdated`, `ReserveRatioBipsUpdated` preserves `reserveRatioBipsUpdated`, and `MaxTotalSupplyUpdated` preserves `assets`. No field is renamed to a normalised parameter or represented as an amount.

### Required event inventory

| Generation | Role | Signature | Exact native fields |
| --- | --- | --- | --- |
| `wildcat-v1` | `controller` | `LenderAuthorized(address)` | `""` |
| `wildcat-v1` | `controller` | `LenderDeauthorized(address)` | `""` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioCanceled(address)` | `market` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioExpired(address)` | `market` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v1` | `market` | `AnnualInterestBipsUpdated(uint256)` | `annualInterestBipsUpdated` |
| `wildcat-v1` | `market` | `AuthorizationStatusUpdated(address,uint8)` | `account`, `role` |
| `wildcat-v1` | `market` | `MaxTotalSupplyUpdated(uint256)` | `assets` |
| `wildcat-v1` | `market` | `ReserveRatioBipsUpdated(uint256)` | `reserveRatioBipsUpdated` |
| `wildcat-v2` | `hooks-instance` | `AccountAccessGranted(address,address,uint32)` | `providerAddress`, `accountAddress`, `credentialTimestamp` |
| `wildcat-v2` | `hooks-instance` | `AccountAccessRevoked(address)` | `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `AccountBlockedFromDeposits(address)` | `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `AccountMadeFirstDeposit(address,address)` | `market`, `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `AccountUnblockedFromDeposits(address)` | `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `FixedTermUpdated(address,uint32)` | `market`, `fixedTermEndTime` |
| `wildcat-v2` | `hooks-instance` | `MinimumDepositUpdated(address,uint128)` | `market`, `newMinimumDeposit` |
| `wildcat-v2` | `hooks-instance` | `NameUpdated(string)` | `name` |
| `wildcat-v2` | `hooks-instance` | `RoleProviderAdded(address,uint32,uint24,uint24)` | `providerAddress`, `timeToLive`, `pullProviderIndex`, `pushProviderIndex` |
| `wildcat-v2` | `hooks-instance` | `RoleProviderRemoved(address,uint24,uint24)` | `providerAddress`, `pullProviderIndex`, `pushProviderIndex` |
| `wildcat-v2` | `hooks-instance` | `RoleProviderUpdated(address,uint32,uint24,uint24)` | `providerAddress`, `timeToLive`, `pullProviderIndex`, `pushProviderIndex` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioCanceled(address)` | `market` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioExpired(address)` | `market` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v2` | `market` | `AccountSanctioned(address)` | `account` |
| `wildcat-v2` | `market` | `AnnualInterestBipsUpdated(uint256)` | `annualInterestBipsUpdated` |
| `wildcat-v2` | `market` | `MaxTotalSupplyUpdated(uint256)` | `assets` |
| `wildcat-v2` | `market` | `ReserveRatioBipsUpdated(uint256)` | `reserveRatioBipsUpdated` |

### Specific unsupported reasons

| Signature | Recorded reason |
| --- | --- |
| `AssetBlacklisted(address)` | Registry asset blacklist mutation does not establish a market balance or borrower credit event. |
| `AssetPermitted(address)` | Registry asset permission does not establish a deployment, market use or balance. |
| `BorrowerAdded(address)` | Registry borrower admission supplies no individual market action or borrowing amount. |
| `BorrowerRemoved(address)` | Registry borrower removal supplies no repayment, market closure or debt balance. |
| `ChangedSpherexEngineAddress(address,address)` | SphereX engine replacement is administration; no credit-state effect is inferred from the engine addresses. |
| `ChangedSpherexOperator(address,address)` | SphereX operator replacement is administration; no access or credit action is inferred from operator addresses. |
| `ControllerAdded(address,address)` | Registry controller registration supplies no market-specific parameter or access change. |
| `ControllerFactoryAdded(address)` | Controller-factory registration supplies no deployed-controller or market event. |
| `ControllerFactoryRemoved(address)` | Controller-factory removal does not prove closure of its existing controllers or markets. |
| `ControllerRemoved(address)` | Controller deregistration does not prove repayment or closure of its markets. |
| `ERC20Transferred(address,address,uint256)` | Fee-recipient token transfer is treasury movement; its unnamed fields establish no market or borrower attribution. |
| `ETHTransferred(address,uint256)` | Fee-recipient ETH transfer is treasury movement and names no market or debt obligation. |
| `HooksInstanceDeployed(address,address)` | Hook deployment identifies instance and template but establishes no market-specific access decision. |
| `HooksTemplateAdded(address,string,address,address,uint80,uint16)` | Template registration and fees describe factory configuration without an affected market action. |
| `HooksTemplateDisabled(address)` | Template disabling does not establish removal or changed access for existing hook instances. |
| `HooksTemplateFeesUpdated(address,address,address,uint80,uint16)` | Template fee configuration identifies no collected fee or affected-market cash movement. |
| `MarketAdded(address,address)` | Registry market registration alone establishes no funding or credit transition. |
| `MarketDeployed(address,address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256,uint256)` | Deployment terms describe initial configuration; this event is retained as context and no funded-market action is inferred. |
| `MarketDeployed(address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256)` | Deployment terms describe initial configuration; this event is retained as context and no funded-market action is inferred. |
| `MarketRemoved(address)` | Registry market removal does not prove closure, settlement or repayment. |
| `NewAllowedSenderOnchain(address)` | SphereX sender admission identifies no market credit action or lender-access decision. |
| `NewController(address,address)` | Controller creation identifies borrower and controller but supplies no market-specific credit action. |
| `OwnerChanged(address,address)` | Fee-recipient ownership mutation names no market or debt obligation. |
| `OwnershipHandoverCanceled(address)` | Cancelled registry ownership request describes no completed ownership or credit transition. |
| `OwnershipHandoverRequested(address)` | Requested registry ownership handover establishes no completed ownership or credit transition. |
| `OwnershipTransferred(address,address)` | Registry ownership transfer names administrative owners without an affected market action. |
| `RecipientChanged(address,address)` | Fee-recipient beneficiary configuration names no realised payment or market obligation. |
| `SpherexAdminTransferCompleted(address,address)` | Completed SphereX administrator transfer identifies administrators without a credit-state transition. |
| `SpherexAdminTransferStarted(address,address)` | Started SphereX administrator transfer is a pending administrative change with no market credit action. |
| `UpdateProtocolFeeConfiguration(address,uint16,address,uint256)` | Controller-factory fee configuration describes terms without proving fee accrual, collection or a market payment. |
| `WrapperDeployed(address,address)` | Wrapper deployment identifies a wrapper and market without a deposit, withdrawal or token transfer. |

The last group remains `unsupported-canonical-meaning` with its original `canonical:<role>:<signature>` gap. Its limitation names the exact signature and the corresponding reason. V1 `MarketDeployed(address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256)` is included even though its emitter is the controller. This table does not excuse a generic fallback for a recognised last-group signature in another admitted role. Hooks-template declarations remain distinct unsupported template events and gain no hooks-instance meaning.

Versioned build selects a supported adapter version explicitly, defaulting to `1.2.0`; verification selects only from the recorded supported version and still rederives every byte. `1.0.0` retains its old rule set, generic limitations and exact output. A release cannot declare `1.0.0` and smuggle in new actions. Unknown versions refuse before output. Historical rebuild scripts may pass `1.0.0` explicitly; published release files are immutable. New public roots are `wildcat-v1-parameters-v0` and `wildcat-v2-parameters-v0`, with constructed providers/contexts and repeating-byte fixture addresses, no retained material. They include all 29 required contexts, concrete-variant tests and hostile empty, maximum-width, zero-address and reordered controls.

## 5. Risk register seed

```risk-register
abi-denominator | first four issue groups to concrete ABI variants | all 29 generation-role-signature contexts and every declaring concrete variant are covered
native-values | decoded ABI values to parameter meaning | exact ABI names and values survive with no conversion or new-value-versus-difference assertion
role-enum | AuthorizationStatusUpdated role to access policy | role stays the emitted uint8 value and no enum label or permission is invented
marketless-hooks | hooks/controller scope to pool parties | no market party is inferred for an event emitting none
affected-parties | emitted address fields to canonical parties | emitter, affected account, emitted market and provider are exact and no zero field is silently dropped
role-dispatch | shared signature to emitter role | hooks-template, controller, market and hooks-instance stay distinct
unsupported-reason | final-group known signature to coverage | each signature carries its own reason and canonical gap under the new version
version-replay | adapter selection to published releases | old bytes verify and rebuild under 1.0.0 and mixed/unknown versions refuse
schema-parity | new state rows to validators | Python and JSON Schema agree on action, instrument, party roles, empty amounts and version
semantic-rebuild | edited or reordered release bytes to verification | re-bound superficial hashes do not conceal changed rows, fields, selectors or coverage
retained-vacuity | absent historical logs to success | each retained generation exercises a target record and absent signatures remain private missingness
private-custody | retained evidence to public reports | only release ids, digests and pass/refuse booleans leave private custody
safe-reporters | fresh reports and sibling imports to evidence | safe-path imports work, report and sidecar leaves are checked before writes, failures write no success
partial-output | release construction to published output | fresh atomic directory completion and preserved input checks remain intact
sibling-composition | signed integration base to versioned capabilities | prior fee meanings survive in 1.1.0 and 1.2.0 without importing unmerged source
```

## 6. Glossary seeds

Native state: unchanged decoded ABI field/value, retained beside the native log. Affected account: address named by the event, with no identity or policy conclusion. Hooks instance: the concrete deployed hook emitter; a template is a different role. Marketless event: an event with no emitted market field. Signature-specific gap: unsupported coverage paired with a reason for that exact ABI signature. Adapter version: interpretation capability selector, independent of package and governed-skill versions. Constructed specimen: synthetic evidence of mapper behaviour, carrying its fixture qualification.

## 7. Sources

Repository paths below are pinned to the starting commit through [the source tree](https://github.com/wildcat-finance/skills/tree/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2): `plugins/tabularium/scripts/tabularium_lib/wildcat_abi.py`, `wildcat_rules.py`, `wildcat_rows.py`, `wildcat_validation.py`, `wildcat_release.py`, `wildcat_source.py`; `plugins/tabularium/schemas/canonical-event-v3.json` and `coverage-manifest-v3.json`; `plugins/tabularium/docs/release-policy.md` and `wildcat-canonical.md`; `plugins/tabularium/tests/wildcat_batch_retained.py`, `wildcat_v3_fixtures.py` and `wildcat_v3_registry_fixture.py`; the three authoritative audit sources and their verified views named in section 2. The issue and four pull requests are linked there. The study's generated ABI inventory and policy probe are design evidence, not a new source authority.

The discipline contracts are pinned in the same tree: `plugins/hexaemeron/skills/ephoros/SKILL.md`, `phylax/SKILL.md`, `metron/SKILL.md`, `elenchus/SKILL.md` and `hypomnema/SKILL.md`. They own the rules cited by sections 8 through 12; this study does not duplicate them.

## 8. Signals, and the questions behind them

Ephoros applies to the new proof/report interfaces. Which mapping ran? Record candidate, criterion, actual command and exit. Did retained evidence exercise the target or was a generation empty? Emit only its bounded pass/refuse result publicly and retain the private denominator. Why did verification fail? Preserve the named semantic/version/path refusal without native payload. Steps 1 and 3 supply those signals. No daemon, metrics service or alerting system is introduced.

## 9. Boundaries, per capability

Phylax applies to untrusted raw logs and copied release files, operator-controlled staging paths, public constructed fixture inputs, and create-only report/output destinations. Existing bounded ABI decoding, source verification, source selectors, regular/no-follow path checks and atomic publication remain the controls. The retained resolver validates both staging trees before mapping, works in a fresh private directory outside the repository, removes scratch on every outcome and never serialises private exception payloads. Report writers refuse pre-existing or linked leaves before invoking resolvers. No credential or network capability is added.

## 10. The budget, or its absence

No performance improvement or wall-time budget is requested. Time and space selection metrics count contextual work in the design model only. The implementation uses bounded table dispatch per decoded record and existing record/output caps; it introduces no transaction-wide search or retained contextual index. Metron applies if implementation adds such a search or makes a performance claim; until then the evidence is structural and carries no speed claim.

## 11. The fail-closed posture

Malformed accepted ABI logs, incompatible roles or versions, changed raw or release bytes, duplicate selectors, unsafe paths, absent staging custody, vacuous retained generations and missing conformance reports stop their dependent transition. Inspecting inputs and rebuilding a fresh version remain available. Elenchus owns new observed failures: preserve the failure, reproduce it and add a source-bound assertion guard before claiming a fix. A child import failure or missing safe report stays inconclusive. The historical fixed source defects remain regression obligations; no unresolved applicable source defect on this starting tree is asserted. The source-bound empty inventory below records that narrower conclusion and consumes Step 1.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "tabularium-history",
      "path": "plugins/tabularium/audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7",
      "view_sha256": "2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c"
    },
    {
      "id": "wildcat-adapter",
      "path": "audit/rounds/fiat-1378-wildcat-v1-v2-canonical-adapter.synopsis.md",
      "source_sha256": "ae0efffe971b1ae9070961e8e67f5ce3f164b107330fae56764b6ac8f0bdfaff",
      "view_sha256": "4d75001072001c5a7a041e9aa4be94bc4aa15157bc11e18040c4e625ee6cdb89"
    },
    {
      "id": "wildcat-batches",
      "path": "audit/rounds/fiat-2087-wildcat-withdrawal-batch-canonical-meaning.synopsis.md",
      "source_sha256": "24cf81c7b2c258ade1907295bab375460717590566bc00dc5d1868025560c51c",
      "view_sha256": "663baae0623da10f544026072a0ba8accec36b0c2211b40100511acc88f45062"
    }
  ],
  "findings": [],
  "no_known_findings": {
    "source_views": [
      {
        "id": "tabularium-history",
        "source_sha256": "1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7",
        "view_sha256": "2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c"
      },
      {
        "id": "wildcat-adapter",
        "source_sha256": "ae0efffe971b1ae9070961e8e67f5ce3f164b107330fae56764b6ac8f0bdfaff",
        "view_sha256": "4d75001072001c5a7a041e9aa4be94bc4aa15157bc11e18040c4e625ee6cdb89"
      },
      {
        "id": "wildcat-batches",
        "source_sha256": "24cf81c7b2c258ade1907295bab375460717590566bc00dc5d1868025560c51c",
        "view_sha256": "663baae0623da10f544026072a0ba8accec36b0c2211b40100511acc88f45062"
      }
    ],
    "consuming_step": 1,
    "surveyor_assertion": "no-known-findings"
  }
}
```

## 12. Decisions and their homes

The expensive decisions are native-state-only meaning, marketless emitter scope, closed action/party/schema vocabulary and explicit adapter-version replay. Record them in `docs/decisions/drafts/keep-wildcat-parameter-events-as-native-state.md` during Step 1, then let integration assign its ADR number. `plugins/tabularium/docs/wildcat-canonical.md` owns user-facing meanings and the version compatibility table. `docs/kickoff/2090/` owns immutable public study/runbook/design evidence and the final bounded reproduction; private retained payloads and signature inventories never enter that bundle.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | native-fields
record | docs/decisions/drafts/keep-wildcat-parameter-events-as-native-state.md
```

Twelve of twelve study sections are answered. Design-lock checks the complete matrix and selects `native-fields`. Product conformance, final demonstration, sibling integration and the user's decision about absent historical positives remain due; this study establishes none of those results.
