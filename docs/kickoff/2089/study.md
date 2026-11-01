# Wildcat fee-event canonical meaning study

Assuming, unless corrected:

1. The target is issue #2089 in `wildcat-finance/skills`, starting from `main` at `8b4e137917d754a7b7c3d5e74d141c0bedf70aa2`. Python is the pinned `3.14.6`; production stays stdlib-only.
2. Fee collection maps as its own `fee-collection` family. The market is the only emitted party; neither a fee recipient nor a payer is inferred. A protocol fee change is `pool-state`, with its basis-point value retained as decoded native state.
3. The controller's compatibility decision requires adapter `1.1.0` for fee semantics and retained `1.0.0` reconstruction. Later #2090 and #2091 versions add their own features without changing any earlier version's result. This supersedes #2087's choice to extend `1.0.0` in place.
4. Public records of retained evidence carry release identifiers, digests and pass or refuse outcomes only. Private paths, raw payloads, addresses, transaction identities and capture-derived counts stay local. The retained staging trees are supplied through the existing V1/V2 staging variables.
5. User authorization covers this Fiat delivery through merge. Product edits await the controller's accepted runbook and applicable inventory checks. This study changes no product and records no receipt.

## 1. Problem statement

`FeesCollected(uint256)` in both Wildcat generations and `ProtocolFeeBipsUpdated(uint256)` in V2 decode but remain `unsupported-canonical-meaning`. Canonical consumers consequently cannot interpret those actions without reading native logs themselves.

A working prototype builds and verifies a new immutable schema-3 release under adapter `1.1.0`. `wildcat-v1.fees-collected` and `wildcat-v2.fees-collected` have family `fee-collection`, party `pool`, and one `assets` amount from native `assets`, in underlying base units. They retain `attribution:fees-collected:recipient`. Missing asset context retains null plus `attribution:fees-collected:asset`. `wildcat-v2.protocol-fee-bips-updated` has family `pool-state`, party `pool`, no amount, and the original `protocolFeeBips` in the decoded mapping record and native log. It retains `attribution:protocol-fee-bips-updated:actor`. V1's factory fee-configuration event stays unsupported.

The proving path is `python3 plugins/tabularium/tests/prove_wildcat_fees.py --candidate versioned-native --criterion retained-conformance --report .hexaemeron/design-reports/versioned-native-retained-conformance.json`, after the product and two public constructed specimens exist. The final controller is the separately invoked successor `plugins/tabularium/scripts/tabularium.py`, through real build and verify calls. The demonstration records positive fee rows and negative malformed-log, missing-asset, altered-release and unsupported-version outcomes. Those observations establish bounded execution, not criterion sufficiency or complete protocol coverage.

Acceptance is executable through the planned proof runner's `semantic-conformance`, `schema-parity`, `legacy-conformance` and `retained-conformance` criteria. They respectively establish the exact three mappings and negative cases; Python/JSON Schema agreement; byte-identical reconstruction of every committed old release and a constructed old fee-containing release; and complete inventory verification plus exact mapping of every actually present target log, with per-generation absent-signature outcomes recorded separately. The retained criterion requires at least one actual retained target log across the two inputs; an entirely empty target set refuses. It does not establish positive execution for an absent signature or satisfy the issue's disputed historical-positive acceptance by itself. The final repository gate is `python3 scripts/run_checks.py --base 8b4e137917d754a7b7c3d5e74d141c0bedf70aa2 --scope root --scope tabularium --scope repo-lints --format json`.

## 2. Prior art

The current mapper consists of `plugins/tabularium/scripts/tabularium_lib/wildcat_rules.py`, `wildcat_rows.py`, `wildcat_validation.py` and the pinned concrete ABI table `wildcat_abi.py`. It has twenty-five generation-and-role-qualified primary tuples. The existing market `Borrow` uses party `pool` and an underlying `assets` amount; `MarketClosed` keeps its timestamp in native state with no amount. Those establish the shape this issue requests. `wildcat_release.py` currently reconstructs using the running mapper, and `release_v2.py` currently compares the manifest version to a single module constant. That is insufficient for a changed interpretation of an externally published fee-containing release.

`plugins/tabularium/docs/release-policy.md` and the Tabularium skill require published source, canonical and coverage bytes to remain immutable; changed interpretations need a version and a new directory. Existing Aave/Euler schema-2 and schema-3 releases provide the old/new release precedent. All six committed Wildcat release inventories were inspected: none contains either fee signature. That local absence does not establish absence from externally published releases. A constructed old fee-containing release is therefore a required compatibility control.

The two most recent merged Tabularium PRs were read: [#2120](https://github.com/wildcat-finance/skills/pull/2120) constructs V2 wrapper contexts and carries no remaining task; its limitation remains that no retained release establishes wrapper-subject coverage. [#2111](https://github.com/wildcat-finance/skills/pull/2111) fixes draft-to-assigned-ADR lookup and carries nothing; new specification guards must accept both draft and assigned ADR homes. The feature predecessor [#2105](https://github.com/wildcat-finance/skills/pull/2105) was also read. Its carryover #2103 stays open for the general safe-path runner issue; this run guards its own new runners. #1926 retains the Probitas batch-status boundary. The two-burns wording, custody-parent links, reproduction-refusal composition and inherited count prose remain exactly the scoped decisions #2105 records; this fee mapping changes none of them.

`audit_synopsis.py --check .` exited zero for the whole discovered source set before the current synopsis views were consulted. The source remains authoritative. The plugin audit and runs 1378, 1997 and 2087 are the fee adapter's prior evidence; schema run 1362 remains authoritative for the shared schema validator. The digest-bound source-view inventory in item 11 records every one of those paths. Findings and status remain in those views, including every `Covered`, `Not checked`, `Elenchus verdict`, `Leads not pursued` and missing legacy field. The present study does not turn historical unguarded or inconclusive verdicts into guarded results.

Plugin audit findings `E1-R1-01` to `E1-R1-03`, `E1-R2-01`, `E1-R3-01`, `E1-R3-02`, `E1-R4-01`, `S2-R1-01`, `S3-R1-01`, `S3-R2-01`, `S3-R2-02` and `S4-R1-01` are fixed; legacy coverage and verdict fields remain unknown where absent. Run 1378's subject binding, disposition spelling and executor-plan findings are fixed, with inconclusive Elenchus verdicts retained. Run 1997's harness-freshness finding is fixed; its unguarded verdict and timestamp exclusions remain. Run 2087's `S3-R1-01` wording and `S4-R1-01` vacuous retained success are fixed; its bare runner imports still explain the open #2103. The new retained fee resolver must refuse empty coverage instead of inheriting a universal-over-empty success. Schema run 1362's accepted scope/documentation choices and existing runner limits remain outside this fee delivery; no existing report or frozen runner is rewritten.

Outside the repository, primary ABI evidence is the pinned V1 and V2 source declarations already embedded in `wildcat_abi.py`: V1 commit `da74452aa7d1a0f024d99efd22cc6d950a8116b7` and V2 commit `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`. V1 declares `FeesCollected(uint256 assets)`; V2 declares it and `ProtocolFeeBipsUpdated(uint256 protocolFeeBips)`. Neither fee log declares a recipient. No new compiler run or chain-state proof is claimed.

A current local custody check rebuilt both retained raw releases only after their full staging manifests verified. `.hexaemeron/design/retained-availability.json` records the result: V1 release `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69` contains no `FeesCollected`; V2 release `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3` contains `FeesCollected` and no `ProtocolFeeBipsUpdated`. V1 protocol-fee updates are outside the requested mapping. These are checked local retained availability observations, not new collection or mapped conformance. The missing V1 fee and V2 state-update specimens block positive retained acceptance for those signatures; constructed specimens cannot fill that evidence class.

## 3. Constraints and non-goals

Keep canonical schema 3 and every published release file unchanged. The fee implementation introduces adapter version `1.1.0`, preserves `1.0.0`, and routes verification by the release's declared supported version. New builds default to `1.1.0`; an explicit `--adapter-version 1.0.0` supports old reproduction. Old example rebuild programs request their original version explicitly. Version is propagated through mapping selection, row provenance, capture and coverage, validation, and reconstruction. Unknown versions and combinations of an old version with new fee rules refuse. This dispatch is scoped to Wildcat; other adapters retain their existing behavior. Here `1.0.0` means the exact starting-tree interpretation, including already landed batch and wrapper-context support. Earlier releases used that same token before those additions; version alone cannot distinguish those older recipe eras, so universal pre-starting-tree reconstruction is not established by this change.

Always preserve native source selectors, generation/role/ABI qualification, attribution gaps and evidence classes; run selected checks before each push; use the written-record sequence; regenerate portable copies, Promise Machine pins and Horos metadata through their owners when required. Package versions advance on each changed step; the ledger generation is resolved against the integration base. The adapter mapping version is separate from the package and skill versions.

Ask first only for a newly proposed dependency, a new schema envelope, a live collection request, private capture publication or a broader downstream change. The user already authorizes this issue's mapping-version dispatch and merge. Never edit retained source, republish old release bytes, infer a fee recipient from a transfer, classify fees as repayment or withdrawal, mutate controller state as a worker, or claim a check that did not run.

Non-goals are V1 factory fee-configuration interpretation, parameter updates owned by #2090, sanctions events owned by #2091, accrual/accounting replay, downstream dossier rebuilds, wrapper-history expansion, timestamps, causal joins between co-occurring actions, borrower identity, publisher authentication and independent Ethereum proof.

## 4. Design options

Three candidates were executed as bounded representation and version-dispatch models in `.hexaemeron/design/fee_probe.py`. They do not exercise product conformance.

`versioned-native` adds fee-collection and pool-state meanings under `1.1.0` while `1.0.0` retains its old dispositions. Its trade is explicit version dispatch through the existing pipeline and both validators.

`in-place-native` appends the same meanings to the existing `1.0.0` mapper. It changes the canonical and coverage bytes of an old fee-containing release, so it fails the legacy reconstruction gate even though committed specimens happen to contain no fee logs.

`repayment-reuse` versions the change but uses the repayment family/action for collected fees. It reduces vocabulary additions and fails native separation because fee collection is its own action.

The closed matrix at `.hexaemeron/design-evidence.json` has selection gates for native separation, legacy reconstruction and missing-context gaps. Two comparative count metrics measure peer lookups and auxiliary records in the model. Both are zero for each candidate: no cross-event join or retained companion inventory is needed. The matrix covers correctness, compatibility, recovery, time and space. All fifteen selection commands exited zero. `unique-frontier` selects `versioned-native` because the other two candidates fail a selection gate.

Four conformance criteria remain pending for each candidate. The selected candidate's `semantic-conformance`, `schema-parity` and `legacy-conformance` resolve after Step 2 and block `step:3`; `retained-conformance` resolves after Step 3 and blocks `integration`. Each names the exact proof command and future report. The retained report is a qualified mapping/rebuild result over present target events and verified inventories. Its observation sidecar records whether each generation contains `FeesCollected` and whether V2 contains `ProtocolFeeBipsUpdated`; absence never becomes a positive observation. It requires at least one target event across both sources, so all-empty retained controls refuse. The separate issue acceptance gap remains an integration stop until the user resolves it or new preserved positives arrive. No selection score stands in for implementation evidence.

The selected mapping adds only these rule ids: `wildcat-v1.fees-collected.v1`, `wildcat-v2.fees-collected.v1` and `wildcat-v2.protocol-fee-bips-updated.v1`. The old rules keep their identifiers. Version-qualified schema branches admit new fee actions only for `1.1.0`; the old branch semantics remain available for `1.0.0`. `protocolFeeBips` stays an integer string in native decoded values, with no percentage conversion or invented asset leg.

## 5. Risk register seed

```risk-register
version-dispatch | manifest through reconstruction | the declared supported version controls rows, rules, provenance and coverage without silent upgrade
legacy-bytes | published release directories | every committed old release and an old fee-containing control reconstructs byte-identically
fee-separation | canonical action vocabulary | fee collection never becomes repayment or withdrawal
recipient-gap | amount-only fee log | pool is the sole party and recipient remains unknown
missing-asset | market context to asset amount | null asset retains its named attribution gap
native-state | protocol-fee update to canonical row | the Bips value stays native state and amounts stay empty
schema-closure | Python tuples and JSON Schema | generation, role, version, party and amount mutations agree on refusal
abi-shape | preserved journal bytes | malformed topic/data shapes refuse and unknown signatures remain gaps
native-order | log inventory and transaction positions | distinct reordered actions map independently while conflicting or edited positions refuse
verify-bytes | generated release to copied raw source | edits to any generated artefact refuse even after digest rebinding
runner-safepath | declared Elenchus runner | sibling imports resolve under safe-path mode before any report is accepted
retained-nonempty | private custody to qualified mapping report | both inventories verify, all present targets map, at least one target executes, and absent signatures stay explicit
report-custody | reports and temporary releases | fresh no-follow outputs only and retained public observations contain digests plus outcomes
partial-output | versioned release installation | failed builds leave no accepted partial release and preserve source bytes
```

## 6. Glossary seeds

`fees-collected`: the native market fee amount action; its ultimate recipient is unestablished.

`protocol-fee-bips-updated`: V2 native state update; no cash-flow amount.

`mapping version`: immutable interpretation selected by build or manifest verification, distinct from package version.

`legacy reconstruction`: rerunning the old mapping version against preserved raw evidence to obtain the old complete release bytes.

`retained conformance`: a checked observation on named preserved releases with no completeness or authenticity claim.

## 7. Sources

Issue [#2089](https://github.com/wildcat-finance/skills/issues/2089) provides the required semantics and acceptance. PRs [#2120](https://github.com/wildcat-finance/skills/pull/2120), [#2111](https://github.com/wildcat-finance/skills/pull/2111) and [#2105](https://github.com/wildcat-finance/skills/pull/2105) provide predecessor changes and carryover. The open runner observation is [#2103](https://github.com/wildcat-finance/skills/issues/2103).

Starting-tree sources are pinned at [the exact starting commit](https://github.com/wildcat-finance/skills/tree/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2). Within it, source paths are `plugins/tabularium/scripts/tabularium_lib/wildcat_abi.py`, `wildcat_rows.py`, `wildcat_rules.py`, `wildcat_validation.py`, `wildcat_release.py`, `release_v2.py`, `plugins/tabularium/docs/release-policy.md`, `plugins/tabularium/schemas/canonical-event-v3.json` and `coverage-manifest-v3.json`. The raw-custody builder and its byte pins are under `plugins/alexandria/examples/wildcat-v1-interval-v0/` and `wildcat-v2-interval-v0/`. The existing no-payload retained resolver is `plugins/tabularium/tests/wildcat_batch_retained.py`.

Pinned primary ABI sources are [V1 market events](https://github.com/wildcat-finance/wildcat-protocol/blob/da74452aa7d1a0f024d99efd22cc6d950a8116b7/src/interfaces/IMarketEventsAndErrors.sol) and [V2 market events](https://github.com/wildcat-finance/v2-protocol/blob/a70f297fbd1b1ab597e0e9a3458a2d13a34b4657/src/interfaces/IMarketEventsAndErrors.sol). The study relies on the already retained declaration bytes and digest bindings, without claiming a fresh upstream fetch.

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/ephoros/SKILL.md) owns the signal contract. Which interpretation rebuilt this release? Capture, provenance and coverage retain the exact version in Step 2. Why was a fee not mapped? Source dispositions retain canonical or decode gaps. Did retained acceptance exercise both generations? Step 3 reports per-generation pass or named refusal with source digests. No unattended service, alert or telemetry deployment is introduced.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/phylax/SKILL.md) owns controls. Preserved journal ingress keeps current bounded decode and source verification. Caller-selected version admits only a closed supported registry. Release verification selects the preserved version and rechecks every byte. New reporters use fresh bounded no-follow leaves and refuse occupied outputs before creating sidecars. The private retained path is operator supplied, manifest checked, copied only to private temporary custody and removed after execution. No network, subprocess input interpreter, credential or dependency is added to the mapper.

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/metron/SKILL.md) owns measurement. There is no latency or throughput claim: the three native mappings add constant work per log, and the selection model records zero peer lookups and zero auxiliary records. Existing record, input-byte and output-byte caps remain. No unmeasured speed improvement is an acceptance condition.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/elenchus/SKILL.md) owns the failure and guard procedure. Malformed admitted ABI, conflicting identities, unsupported version, old-version/new-rule combinations, altered output bytes, missing custody, an entirely empty retained target set and unsafe report paths stop their dependent transition. Missing asset or recipient evidence remains a named gap. The current product defects recorded by the scoped audits are fixed and guarded. The existing bare imports named by #2103 belong to old frozen runners; this run creates its own safe-path runners and does not claim to fix those old interfaces. Safe-path execution, refusal of an entirely empty target set and explicit per-signature retained availability are scaffold regression requirements, not invented present defects requiring parent-red inoculation. The explicit no-known-findings inventory below binds that scoped assessment to the current source views.

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
      "id": "timestamps-1997",
      "path": "audit/rounds/fiat-1997-bind-wildcat-archive-timestamps-to-preserve.synopsis.md",
      "source_sha256": "3200d6c9bc7c37b5cc9831b7f49c1dca7a48920e69ac04107cee9296311b99e3",
      "view_sha256": "772e1c372c4192972f5287f526c6d70135aa2446ae7efbac8868e3f9ec204249"
    },
    {
      "id": "batches-2087",
      "path": "audit/rounds/fiat-2087-wildcat-withdrawal-batch-canonical-meaning.synopsis.md",
      "source_sha256": "24cf81c7b2c258ade1907295bab375460717590566bc00dc5d1868025560c51c",
      "view_sha256": "663baae0623da10f544026072a0ba8accec36b0c2211b40100511acc88f45062"
    },
    {
      "id": "schema-1362",
      "path": "audit/rounds/fiat-1362-tabularium-canonical-event-v3-and-coverage.synopsis.md",
      "source_sha256": "b27678d5bb3ce2deb6e9b8c38415073cd385870fadd39bfbb83ee501545934ec",
      "view_sha256": "067690f8e6def8e79e09b55caf8c4a77b04ecf34f5560f5b481f019aac1b763f"
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
        "id": "timestamps-1997",
        "source_sha256": "3200d6c9bc7c37b5cc9831b7f49c1dca7a48920e69ac04107cee9296311b99e3",
        "view_sha256": "772e1c372c4192972f5287f526c6d70135aa2446ae7efbac8868e3f9ec204249"
      },
      {
        "id": "batches-2087",
        "source_sha256": "24cf81c7b2c258ade1907295bab375460717590566bc00dc5d1868025560c51c",
        "view_sha256": "663baae0623da10f544026072a0ba8accec36b0c2211b40100511acc88f45062"
      },
      {
        "id": "schema-1362",
        "source_sha256": "b27678d5bb3ce2deb6e9b8c38415073cd385870fadd39bfbb83ee501545934ec",
        "view_sha256": "067690f8e6def8e79e09b55caf8c4a77b04ecf34f5560f5b481f019aac1b763f"
      }
    ],
    "consuming_step": 1,
    "surveyor_assertion": "no-known-findings"
  }
}
```

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/8b4e137917d754a7b7c3d5e74d141c0bedf70aa2/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns records. The versioned dispatch, independent fee family, pool-only parties, recipient/asset gaps and native-only Bips state are expensive to reverse. Step 1 records them in `docs/decisions/drafts/version-wildcat-fee-native-events.md`; integration assigns its number. The existing assigned-ADR lookup convention from #2111 applies.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | versioned-native
record | docs/decisions/drafts/version-wildcat-fee-native-events.md
```

Three ordered steps are sufficient. Step 1 creates immutable thin proof and step-report runners, their safe-path imports, focused scaffold regression tests, the frozen specification bundle under `docs/kickoff/2089/`, and the decision draft. It maps nothing. Step 2 implements supported-version dispatch, the three mappings, Python/schema parity, version-qualified legacy rebuilds, constructed fee specimens for both generations, the guide and ledger generation. It resolves semantic, schema and legacy conformance before Step 3. Step 3 executes retained conformance and the successor build/verify demonstration, records sanitized reproduction evidence, and runs final checks before integration. Each step has one focused report and the checked repository runner as its exit proof.

The two new public specimens live at `plugins/tabularium/examples/wildcat-v1-fees-v0/` and `wildcat-v2-fees-v0/`. They include ordinary fee rows, missing-asset context and co-occurring independent actions. V2 includes a protocol-fee update. Malformed controls live in tests rather than pretending a refused release is a published specimen. Retained inputs are local evidence already in custody; availability and signature presence are separate from final mapped conformance. A missing historical positive required by the literal issue stops full acceptance until the user decides the interpretation, even when constructed controls and the qualified retained mapping criterion pass. The current retained sources already have that gap: V1 fee collection and V2 protocol-fee updates need separately preserved observations or an explicit acceptance clarification before integration. The product and constructed conformance can be completed while that source gap is resolved; no report may invent a positive observation for the absent event.

Study state: all twelve sections are present and the selection record is closed, so the runbook can be derived. Integration is blocked on the named retained-signature gap; conformance remains scheduled at its named stop points. The runbook must consume the no-known-findings assessment in Step 1 and bind the exact design digest before any product work. The next action is deriving that runbook.
