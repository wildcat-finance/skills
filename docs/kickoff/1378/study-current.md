# Wildcat V1/V2 canonical adapter study

Assuming, unless corrected:

1. The user’s explicit “Fiat 1378” authorises this issue’s deployed Ethereum-mainnet V1/V2 adapter and its receipted delivery. The issue’s existing scope and maintainer decisions define the requirements.
2. The exact starting tree is `b4af9c748a764287ccb9978937021e45cc81fc2d`, on `fiat/1378-wildcat-v1-v2-canonical-adapter`, at `issue/16777231-1274979708`. The supported interpreter is Python `3.14.6`.
3. Preserved provider records remain recorded evidence. Neither source maps, emitter campaigns, provider agreement nor offline reproduction establish chain finality, complete historical activity, settlement or identity.
4. Compiler/source inputs use the accepted historical Lemma `0.2.1` format. Its successful pinned reproduction does not claim current Lemma-schema conformance. The labelled mixed V1 lens input remains outside whole-tree exact-commit acceptance.

## 1. Problem, user and proving path

Build `canonical-event-v3` releases for the deployed Wildcat V1 and V2 generations so researchers can inspect lender actions and pool debt activity without converting an unobserved actor into a factual borrower. Tabularium owns these mappings; Alexandria owns input preservation; Probitas owns later declared-address dossiers. Issue #1386 owns accounting replay and #1387 owns function-to-adapter reconciliation.

A working prototype consumes one verified Alexandria Wildcat release, emits a self-contained new canonical release, and makes `verify coverage.json` reproduce its rows and coverage offline. It preserves every mapped native log, selector, generation, emitter role and mapping rule. Every scoped native event receives an explicit mapped, unsupported-canonical-meaning or unsupported-decode disposition. Attribution gaps coexist with successfully decoded pool records.

The final demo uses the actual successor CLI `python3 plugins/tabularium/scripts/tabularium.py wildcat-canonical --alexandria-release DIR --release ID --out NEW_DIR`, then `python3 plugins/tabularium/scripts/tabularium.py verify NEW_DIR/coverage.json`. These are proposed implementation interfaces, unavailable at the starting tree. Step 4 runs them on synthetic public fixtures and both admitted private captures, with sockets disabled, retained argv and observed exit codes. It then alters a copied release’s party, amount shape, selector, mapping class and source bytes separately and records the expected refusal. The demo establishes only these bounded observations.

```success-criteria
{
  "schema": "protasis-success-criteria/v1",
  "criteria": [
    {
      "id": "checked-scaffold",
      "claim": "The scaffold supplies focused subprocess-free reporters and binds the checked source-view inventory without claiming a historical failure was reproduced.",
      "step": 1,
      "command": "python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json"
    },
    {
      "id": "native-semantics",
      "claim": "The Wildcat adapters retain actual parties, pool-only draw/closure, payer/debtor distinction and wrapper instrument meaning with a disposition for every scoped native event.",
      "step": 2,
      "command": "python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json"
    },
    {
      "id": "schema-parity",
      "claim": "JSON Schema and Python accept the same Wildcat tuples and refuse malformed rows while preserving all older adapter tuples and shipped release bytes.",
      "step": 2,
      "command": "python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json"
    },
    {
      "id": "reproducible-public-releases",
      "claim": "Both synthetic generation releases rebuild and verify offline with exact selectors, explicit attribution/decode gaps and complete native records.",
      "step": 3,
      "command": "python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json"
    },
    {
      "id": "offline-demonstration",
      "claim": "The final demonstration binds the executed successor controller commands, positive self-contained rebuild and named hostile refusals; private capture outputs remain outside Git.",
      "step": 4,
      "command": "python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json"
    }
  ]
}
```

The checked runner selects the union of requested scope and actual changed paths. The source-bound tests behind each criterion must assert its behavior; invoking that runner alone does not establish a claim absent such tests. Step 1 scaffolds reporters and records the no-current-assignment disposition, Step 2 implements semantics and validators, Step 3 ships constructed releases, and Step 4 demonstrates offline reproduction.

## 2. Prior art and carried work

The starting implementation’s `plugins/tabularium/scripts/tabularium_lib/wildcat_view.py` already verifies Alexandria releases, resolves nested RPC responses, validates market ABI, derives bounded deployment bindings and separates repayment payer. Its `tabularium-wildcat-view/v1` output intentionally omits deposits, withdrawal queues/executions and most transfers. Projection from that view cannot meet #1378’s denominator. Reuse its checked readers and helpers deliberately; do not reuse ignored-log decisions as canonical coverage.

Existing Aave/Euler adapters, `release_v2.py`, `builder.py`, `verifier.py`, and the v3 JSON Schemas supply the reproducible-release path. Existing v0/v1 release bytes and admitted tuples stay fixed. The Compound Phase 1 held frontier remains unchanged. The organisation’s V1/V2 source maps, deployment registry, emitter checks and accepted corpus supply qualified event identities and limitations. External references are the Solidity ABI event specification, ERC-20 and ERC-4626, cited in item 7; those standards do not override Wildcat’s deployed source semantics.

The last two merged subject PRs were read: [#2001](https://github.com/wildcat-finance/skills/pull/2001), merge `367f5c4998cff46776e02978e9469b5c37ba8781`, and [#1977](https://github.com/wildcat-finance/skills/pull/1977), merge `1f772fc01bb50c90fe0f254fec8ed088fbe6ab13`. This run consumes #1977’s `arch-interface-event-variants` and `v1-fidelity-report-link`: four conflicting `IWildcatArchController` variants remain interface-only and cannot substitute for emitted concrete ABI declarations. Consume the accepted V1 fidelity report with its ABI-clean-argument limits. #2001’s adapter reconciliation stays with #1387; checker limits with #1998; diagram arrows with #1993; Hypomnema walk with #1663; ADR allocation with #1782. They remain open and are non-goals here.

Surveyor and its research delegate read all eleven in-scope checked synopsis views below after `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero for the whole source set. The authoritative sources remain the source column. The exact headings, finding tables/status, `Covered`, `Not checked`, `Elenchus verdict`, `Leads not pursued` and missing legacy markers are retained in `.hexaemeron/design-reports/audit-reading-index.json`; its source and view hashes bind every field. These are synopsis reads, not claims of direct source reads.

| Authoritative source | Read view | SHA-256 of view |
| --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | `82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee` |
| `plugins/tabularium/audit/AUDIT.md` | `plugins/tabularium/audit/AUDIT_SYNOPSIS.md` | `2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c` |
| `audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.md` | `audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.synopsis.md` | `0f4179c49c2a7136019941fb1badc62046a625ff94c8fa3a17760d32b55b1d7c` |
| `audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.md` | `audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.synopsis.md` | `4354f3b452be3217b1a9980d3deb4f663e4acaf12a51d38ff41ba827053ddb02` |
| `audit/rounds/fiat-1362-tabularium-canonical-event-v3-and-coverage.md` | `audit/rounds/fiat-1362-tabularium-canonical-event-v3-and-coverage.synopsis.md` | `067690f8e6def8e79e09b55caf8c4a77b04ecf34f5560f5b481f019aac1b763f` |
| `audit/rounds/fiat-1363-entry-point-maps-at-two-pinned-wildcat-v2-c.md` | `audit/rounds/fiat-1363-entry-point-maps-at-two-pinned-wildcat-v2-c.synopsis.md` | `28711061a123f3991feaa36d3e82e0cc774539220ebc2482ccfebb478bbc9c17` |
| `audit/rounds/fiat-1366-remaining-venue-event-conformance.md` | `audit/rounds/fiat-1366-remaining-venue-event-conformance.synopsis.md` | `78aed7e77ab989d8ce2f9b9b983eedafd43485899128c53589bb24c7e9db6d10` |
| `audit/rounds/fiat-1366-validate-solidity-event-ast-and-abi-agreeme.md` | `audit/rounds/fiat-1366-validate-solidity-event-ast-and-abi-agreeme.synopsis.md` | `7054866e841a6eab63e2a14c7d678a55af17fa33a241cb30a6dc0531076e3936` |
| `audit/rounds/fiat-1374-bind-the-sealed-wildcat-captures-to-dataset.md` | `audit/rounds/fiat-1374-bind-the-sealed-wildcat-captures-to-dataset.synopsis.md` | `1c64e9b59e0ba0e07cd51f9dc8ca1b8db653cb70a9f27050463ef95e55b2782e` |
| `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md` | `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.synopsis.md` | `0399cd2ef2ab8bc38c163a25ccf63dc6ebc6ebaa266e269669efdb080ea8d5a2` |
| `audit/rounds/fiat-1963-wildcat-v1-entry-points-and-event-linkage.md` | `audit/rounds/fiat-1963-wildcat-v1-entry-points-and-event-linkage.synopsis.md` | `7b4f33d1fb21c0213984c8ccc6aee4ca8992c410d791120024dd9827956381c7` |

The reusable Tabularium input/write failure classes all have recorded fixes. Eight reusable classes inform focused regression specimens during adapter work; they are recorded fixed and do not justify a new parent-failure claim. Schema #1362’s `S1-R1-03` broad-runner failure remains historically open: the new focused reporter must avoid subprocesses. Its old missing/unknown-key gap `S3-R1-03` was accepted then cured by #1760; current source checks both key sets. Forty-nine current schema tests passed during this research. #1759’s portable scripts and #1942’s suite roster stay open outside this adapter.

The #1963 V1 map’s thirteen findings are recorded fixed. Preserve `S2-R1-02`: closing can leave an expired, unprocessed withdrawal batch unpaid. Preserve `S2-R1-03`: only concrete emitted signatures and correct input-local references count. V2 map coverage attempts failed; no protocol coverage or runtime-execution result is inherited. Static and differential emitter results establish their named log shape and ABI-clean vectors only; dirty `uint32` expiry at timestamp plus duration reaching `2^32`, complete reachability and off-chain decoder correctness remain unestablished.

Capture #1731’s logless-transaction trace gap, V1 opening parity, V1 deploy-log-free market-list derivation, unknown deployment blocks, equivalent source checkout ambiguity and zero observed Sentinel logs stay visible. #1831, #1442 and #1445 remain open. Provider agreement does not erase positional/finality limitations. Withdrawn #1354’s audit source is absent from this tree and the independently accepted #1359 Wildcat subset supplies no historical Fiat audit receipt. Their bounded accepted evidence may be consumed; neither missing audit is described as clear. Broader remaining-venue corpus work stays with #1359/#1983, outside this issue.

## 3. Constraints, admitted inputs and non-goals

Start from `b4af9c748a764287ccb9978937021e45cc81fc2d`; preserve Python `3.14.6`, stdlib production code, offline verification, installed sibling path confinement and the root checked-runner/commit gates. JSON-Schema parity uses the test dependency already selected by the repository; missing required parity execution fails the gate rather than silently skipping it. No new runtime dependency is needed. The starting checked-runner baseline selected eleven checks and exited zero: root 2,635 tests with seven skips, Tabularium 252 and Probitas 528. `.hexaemeron/baseline-checks.json` binds that executed-result summary to the starting SHA; skips are retained, not described as executed checks.

Fresh Git-blob recovery of preserved archives from `skills-secretsauce` at `32aca579219e5be4c89dfb23c4de76457fe86d03` produced the exact accepted bytes. It was not a fresh chain capture. `.hexaemeron/capture-admission.json`, SHA-256 `0ddc6bd2cc35ee9359bb1b15fd3036b8ba2805611e1e63ad9327a7e24b9796d8`, records both rebuilt/independently verified releases and zero exits:

| Generation | Archive SHA-256 / bytes | Verified release / interval | Local release |
| --- | --- | --- | --- |
| V1 | `25322e603679a24a4d9410f24aca07696cdf83ed0349b9f86b900d246b76a687` / 4,323,015 | `eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69` / 18,743,513 to 22,074,622 | `/private/tmp/fiat-1378-inputs-zwov3lzg/v1-demo/release` |
| V2 | `0407fecac64ff15c23d298044cd2498180ceea2900bb6807330c104b348bd90a` / 37,920,375 | `2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3` / 21,866,550 to 26,022,093 | `/private/tmp/fiat-1378-inputs-zwov3lzg/v2-demo/release` |

`python3 .hexaemeron/capture-inventory.py` examined the admitted journal/registry inputs: V1 has 1,941 native logs across 38 role/topic contexts; V2 has 74,088 across 42. No duplicated native log identity occurred in this finite inventory. `.hexaemeron/design-reports/capture-native-inventory.json` records source manifests and counts. It checks no new semantic mapping and proves no chain history. Independent source/log review in `/private/tmp/fiat-1378-corpus-qu0ll99s/native-context-review.json` preserves 250 V1 market Transfer logs: 95 mints, 69 account-to-pool moves and 86 burns. V2 has 12,741: 5,125 mints, 3,327 account-to-pool moves, 3,894 burns and 395 between nonzero endpoints. These are token-claim transfers; no generic debt-transfer meaning is admitted. No wrapper or sanctioned-withdrawal companion logs occurred in these finite captures. Their source-admitted semantics therefore require labelled synthetic positive/refusal specimens; capture absence does not clear them.

The accepted corpus is `/private/tmp/fiat-1378-corpus-qu0ll99s/bundle`, archive SHA-256 `c2933988f0619b2874c5880211ef0f6d3586f3a463515b317ff8a7f609785fe1`, 21,728,910 bytes. `/private/tmp/fiat-1378-corpus-qu0ll99s/source-admission.json` admits all 15 original inputs: four V1 and eleven V2, 4,209 chunks and 3,928 verbatim quotation projections. Two historical Lemma `0.2.1` rebuilds reproduced the accepted chunk bytes/build IDs across ten partitions. `/private/tmp/fiat-1378-corpus-qu0ll99s/pinned-verification.json`, SHA-256 `1472da329964f35b95642936e9194438fb9af26d4f24650318f6d238cb849b8c`, passed provenance/schema checks, 382 event declarations and 249 interface events. Accepted provenance paths and compiler invocation relocate; accepted originals remain unchanged. No current Lemma `0.5.1` schema result is claimed.

V1 market/factory/core input sources bind to `da74452aa7d1a0f024d99efd22cc6d950a8116b7` and four equivalent commits; the Sentinel input binds `6164ddd4c75ef6da2181e5623b99795b9829e31c`. `MarketLensMixed` is the accepted no-whole-tree-match partition; its original SHA-256 is `fe06195c86502900d64692619da8e1275ebc7720087e59d81b2c8dd651648377`. It supplies no guessed market party. V2 capture registry pin `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` and source comparison pin `f5a26146987926f4811b72a795d662813dedfe85` remain distinct. `targets.json` and `source-match-1590.json` bind the named emitter/interface/hook-base blobs across those deployed epochs; do not turn that relation into whole-estate equivalence.

Excluded: unreleased V2.5 candidate `bea503c2736d47de7fd34130c64f10783dc35b39`; #1358’s V2.5 hook work under the maintainer’s deployed-V1/V2 scope decision; accounting/state replay, balances, interest allocation, current standing, lifetime totals, full repayment, identity/score, new capture/provider access, and Compound frontier changes. Private archives/corpus/output ledgers never enter Git. Public fixtures are constructed and labelled as such.

## 4. Candidate designs and chosen representation

The three executable selection probes consume the actual accepted linkage bytes and the seventeen declared primary event contexts, not asserted grades:

| Candidate | Trade | Observed selection result |
| --- | --- | --- |
| `role-qualified` | Dispatch by generation, registered emitter role and deployed signature; retain full journals and source bindings | Retains all 17 contexts; 15 ms for 170,000 dispatch queries; 1,947 encoded dispatch bytes; source identities round-trip |
| `topic-only` | Smaller dispatch table; signature keys collapse role/generation | Retains signatures but fails role/generation equality; 11 ms; 892 bytes |
| `view-projection` | Reuses existing bounded view output; fewer contexts | Drops 11 primary contexts; retained contexts preserve generation/role; 15 ms; 541 bytes |

`python3 .hexaemeron/design-probe.py --candidate CANDIDATE --criterion CRITERION --report PATH` produced each of the fifteen selection reports plus source-bound observations. Timing is one measured dispatch micro-experiment rounded upward to integer milliseconds, not full-release performance. Space is encoded dispatch size, not peak RSS. Recovery demonstrates source descriptor digest rechecking, not crash recovery. `.hexaemeron/design-evidence.json` has three candidates, eight criteria and all 24 cells. The design-lock checker returned clean: the two incomplete candidates fail hard gates, leaving `role-qualified` as the unique frontier. Pending semantic/schema checks stop `step:3`; pending release reproduction stops `integration`.

Implement separate `wildcat-v1` and `wildcat-v2` adapter identities with shared bounded helpers. Identify emitter role from the verified registry and code/source epoch, then validate concrete deployed ABI arity/indexing/data words. A topic alone cannot identify an instrument. Use one log-to-row selector; retain the complete original native log unchanged. Keep native ordering by block, transaction index and log index. A second provider copy is reconciliation evidence, not another event.

The new `wildcat-canonical` build creates a fresh release directory containing preserved raw Alexandria bytes at `source/raw-release/`, a `source.json` descriptor, `capture.json`, `events.jsonl` and `coverage.json`. The descriptor binds the raw release manifest/component digests and embeds reproducible mapping provenance: source signature/topic0, concrete ABI/source location, recorded evidence class, inferred context, supporting selectors and limitations. Canonical `provenance` retains its closed v3 fields; `supporting_selectors` points to the class-qualified descriptor records. No factual borrower party is inferred into an amount-only event. `verify coverage.json` dispatches to the registered Wildcat adapter, rechecks the copied raw release through Alexandria, validates the descriptor/class inventory and reproduces all canonical/coverage bytes. It uses no external absolute input path after release creation.

Add only Wildcat-qualified v3 tuple branches for `deposit`, `exit-queue`, `exit-execute`, `transfer` and `pool-state`, alongside borrowing/repayment. Existing schema-2 paths, schema-3 adapter tuples, cardinality and meaning remain fixed. `wildcat-v1.market-closed` and `wildcat-v2.market-closed` alone admit `amounts: []`; the timestamp remains decoded provenance/native state, never an asset amount or zero placeholder. Pool-only rows keep the observed emitter as party role `pool`. New tuple branches and Python checks must enforce those exact conditions; a missing quantity on any financial event or old adapter remains refused. The new adapter/mapping versions establish a new interpretation; no earlier published release is rewritten.

The primary mapping catalogue is:

| Generation / role | Deployed signature | Canonical meaning and actual party | Exact quantity / limitation |
| --- | --- | --- | --- |
| V1/V2 market | `Deposit(address,uint256,uint256)` | qualified deposit; indexed account is depositor and minted-token account | emitted normalized assets and scaled shares; scaled shares have no asset token; matching mint Transfer is retained as token issuance, not another capital deposit |
| V1/V2 market | `WithdrawalQueued(uint256,address,uint256,uint256)` | exit queue; indexed account is withdrawing account, expiry is batch identity | emitted requested normalized/scaled claim, no assets paid at queue |
| V1/V2 market | `WithdrawalExecuted(uint256,address,uint256)` | exit execution; indexed account is claim account, not executor | emitted normalized assets; account may be paid through sanctions escrow, so primary event alone does not establish ultimate cash recipient |
| V1/V2 market | `Transfer(address,address,uint256)` | market-token transfer; emitted from/to, retaining zero-address mint/burn | emitted normalized market-token claim; no underlying cash movement or fresh capital inference |
| V1/V2 market | `Borrow(uint256)` | pool draw; observed `pool` party only | emitted asset amount; borrower actor absent, registry debtor context is `inferred` and separately sourced |
| V1/V2 market | `DebtRepaid(address,uint256)` | repayment; indexed `from` is `payer`, observed pool is debtor facility | emitted asset amount; payer may differ from registry-inferred debtor; no complete-settlement conclusion |
| V1/V2 market | `MarketClosed(uint256)` | pool-state closure; observed `pool` party only | emitted timestamp and empty financial amount list; no closing actor, settlement amount or full repayment; V1 expired-unprocessed batch limitation retained |
| V2 wrapper | `Deposit(address,address,uint256,uint256)` | wrapper deposit; emitted `by`/`owner`, instrument is wrapper | assets are wrapped market tokens, shares are wrapper shares; underlying pool financing is not established |
| V2 wrapper | `Withdraw(address,address,address,uint256,uint256)` | wrapper withdrawal; emitted caller/receiver/owner remain distinct | assets are market tokens returned by wrapper, not underlying pool withdrawal; retain wrapper identity |
| V2 wrapper | `Transfer(address,address,uint256)` | wrapper-share transfer; emitted from/to and wrapper instrument | wrapper-share units; never relabel as the pool’s lender or underlying cash flow |

These grouped rows cover seven market signatures per generation and three V2 wrapper signatures, the seventeen checked contexts. `SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)` is a decoded routing companion, not another withdrawal or payment. An unambiguous same-market/transaction/account/expiry/amount join may retain its emitted escrow address separately from the withdrawal account, with both native selectors and the join’s inference class. The primary account remains beneficiary; the escrow is recipient only where the companion supplies it. Missing or ambiguous routing remains unsupported. The complete companion log stays preserved with a supporting-record disposition and explicit coverage explanation; never count its amount as a second cash withdrawal. `SanctionedAccountAssetsSentToEscrow(address,address,uint256)` concerns market-token seizure/routing, not repayment or underlying cash.

A market Transfer can be a deposit mint, queue account-to-market move, batch-payment market-to-zero burn, ordinary holder transfer or sanctioned account-to-escrow move. Wrapper Transfer likewise preserves share mint/burn/transfer endpoints. Keep exact endpoints and native meaning; do not infer independent funding or settlement from every token move. A wrapper address in a pool log remains that address’s party; no look-through to its shareholders is attempted. Asset context comes from the verified registry/deployment with its inference/source class, not arbitrary ERC-20 metadata.

Every other preserved scoped role/topic gets its own disposition row. Known administrative, approval, batch aggregate, state/accrual and sanctions events retain decoded values only where a concrete accepted ABI supplies them, plus `unsupported-canonical-meaning` and the stated absent actor/state claim. Unknown role/signature or absent ABI receives `unsupported-decode`; its raw bytes remain preserved and its exact count enters coverage. Malformed bytes claiming a supported deployed topic are a fatal input error, not an unsupported escape. Do not map unreached conflicting interface variants. Do not infer default or settlement from batch/StateUpdated events.

`coverage.unsupported_events` uses documented qualified keys `attribution:<action>:<role>`, `canonical:<role>:<signature>` and `decode:<role>:<topic0>`, each with a count and explicit descriptor explanation. Attribution entries may overlap included pool/payer rows; they are not omitted-event counts and must not be summed as such. Mapped-primary, supporting-routing, unsupported-canonical-meaning and unsupported-decode dispositions partition the native denominator; primary canonical counts and support counts remain separately documented. Preserve original capture coverage and gaps verbatim in descriptor/source scope; successful mapping never upgrades them.

## 5. Risk register

```risk-register
source-epoch | registry/code epoch to event definition | wrong generation, concrete ABI or unreleased actor signature refuses
party-strengthening | native fields to canonical parties | pool-only draw/closure cannot emit factual borrower; payer stays distinct
wrapper-collapse | registry role to instrument and party | wrapper-market Transfer collision and wrap/unwrap units retain their own instrument
quantity-shape | native ABI to amount legs | normalized/scaled/cash units stay separate; closure timestamp is not money; no zero placeholders
selector-reuse | recorded journals to event identity | each mapped log has one unique selector and conflicting duplicate/block metadata refuses
nested-response | preserved response string to native record | UTF-8 response digest is checked before nested JSON selector resolution
coverage-gap | native event denominator to coverage | every role/topic disposed; decode and attribution gaps remain distinct and raw gaps survive
abi-bounds | untrusted log fields to decoder | topic count, address padding, word width, arity and dynamic offset budgets refuse malformed input
path-alias | input/raw-copy/output paths | no links, FIFOs, escapes or evidence-clobbering alias; bounds checked before reads
partial-output | release creation and interruption | fresh staging plus atomic completion; no partial directory verifies; source bytes remain unchanged
sibling-import | installed Alexandria API loading | loaded module paths resolve under the installed sibling; no arbitrary import substitution
schema-compatibility | Wildcat tuple admission to old readers | old tuple/cardinality checks and all six shipped Aave/Euler rebuilds still pass
private-custody | raw captures/corpus to public Git | constructed fixtures only; public reports expose digests/counts rather than private bytes
report-truth | reporter execution to Fiat evidence | exact argv/source/report binding, subprocess-free focused runner and actual exits retained
prose-boundary | mapping explanation to downstream claim | no identity, settlement, chain-proof, current-standing or accounting claim
```

## 6. Glossary seeds

`pool`: observed emitting market address, not an observed borrower actor.
`payer`: emitted repayment sender; it may differ from the debtor.
`registry-inferred debtor`: a source-bound instance context, not a field of the debt event or verified human identity.
`scaled claim`: protocol accounting units; no state conversion is performed here.
`wrapper instrument`: share token issued by the wrapper, distinct from its wrapped market token and the pool’s underlying asset.
`unsupported attribution`: absent party evidence on a decoded event.
`unsupported decode`: no accepted definition for the native role/signature; preserved raw bytes remain.
`source selector`: ordered nested journal/response/log reference, with component and response digests.

## 7. Sources

The source tree pointers below are pinned to the starting Skills commit. Repository paths are identifiers, not relative Markdown links.

- `plugins/tabularium/skills/tabularium/SKILL.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/tabularium/skills/tabularium/SKILL.md).
- `plugins/tabularium/docs/wildcat-archive.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/tabularium/docs/wildcat-archive.md).
- `plugins/tabularium/docs/adding-an-adapter.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/tabularium/docs/adding-an-adapter.md).
- `plugins/tabularium/docs/release-policy.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/tabularium/docs/release-policy.md).
- `plugins/tabularium/schemas/canonical-event-v3.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/tabularium/schemas/canonical-event-v3.json).
- `plugins/tabularium/schemas/coverage-manifest-v3.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/tabularium/schemas/coverage-manifest-v3.json).
- `docs/kickoff/1963/README.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1963/README.md).
- `docs/kickoff/1963/sources.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1963/sources.json).
- `docs/kickoff/1963/linkage.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1963/linkage.json).
- `docs/kickoff/1963/denominator-inputs.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1963/denominator-inputs.json).
- `docs/kickoff/1363/README.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1363/README.md).
- `docs/kickoff/1363/linkage.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1363/linkage.json).
- `docs/kickoff/1361/emitters.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1361/emitters.md).
- `docs/kickoff/1962/emitters.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1962/emitters.json).
- `docs/kickoff/1359/targets.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1359/targets.json).
- `docs/kickoff/1359/evidence/source-match-1590.json`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1359/evidence/source-match-1590.json).
- `docs/kickoff/1374/capture.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/kickoff/1374/capture.md).
- `docs/hermes-rule-corpus/emitter-fidelity-1597.md`: [starting-tree source](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/docs/hermes-rule-corpus/emitter-fidelity-1597.md).

Primary external references: [Solidity ABI events](https://docs.soliditylang.org/en/latest/abi-spec.html#events), [ERC-20](https://eips.ethereum.org/EIPS/eip-20), and [ERC-4626](https://eips.ethereum.org/EIPS/eip-4626), read on 3 October 2026. The immutable deployed ABI/source inputs decide this adapter’s concrete events. Live issue [#1378](https://github.com/wildcat-finance/skills/issues/1378) and its maintainer comments define the deployed-V1/V2 scope; [#1386](https://github.com/wildcat-finance/skills/issues/1386) and [#1387](https://github.com/wildcat-finance/skills/issues/1387) keep their downstream boundaries.

Local admission/report paths in item 3 identify fresh input verification. The accepted Git-blob recovery is custody evidence; no R2 publication or deployment is performed here.

## 8. Signals and on-call questions

[Ephoros](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/hexaemeron/skills/ephoros/SKILL.md) owns the signal contract. This is an offline CLI, with no daemon or alert service. Step 2’s bounded JSON build/verify summaries answer: which generation/release failed and at which gate; how many native events were mapped, decoded-but-unsupported or not decoded; which actors remain unsupported; and whether all raw/canonical bytes were reproduced. Bind release/adapter/mapping versions, input/output digests, counts and explicit error class. Do not log whole private payloads, provider credentials or party labels inferred from user context.

## 9. Trust boundaries and controls

[Phylax](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary/control contract. Step 2 accepts filesystem paths, raw JSON/RPC records, registry declarations and sibling modules; it opens no network, subprocess, credential or model-output boundary. Preserve upstream verification and byte budgets before decode, with no-follow regular-file handling, duplicate-key/type/numeric/ABI limits, bounded nested selectors and installed sibling resolution. Step 3/4 writes only new staging outputs outside the inputs, refuses existing conflicting output and atomically marks a complete release. Reverification recomputes rather than trusts generated descriptors. Tests cover interrupted writes, source mutation, role ambiguity and manifest aliases.

## 10. Performance budget and measurement

[Metron](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/hexaemeron/skills/metron/SKILL.md) owns performance claims. No speed target is promised. Existing input caps are 512 MiB across components and 500,000 records per journal class; inherited source bounds must remain or become narrower. Canonical output gets a declared bounded cap of 256 MiB, independently checked before publication. The admitted V2 raw input contains 211,784,316 staging bytes and 74,088 logs, so an unqualified 128 MiB whole-release cap would reject required preserved inputs.

Step 4 records actual build/verify durations, input/output bytes and row counts using `python3 plugins/tabularium/tests/prove_wildcat_v3.py --candidate role-qualified --criterion release-reproduction --report .hexaemeron/design-reports/role-qualified-release-reproduction.json`. This command is created in Step 1. Selection’s 15 ms/1,947-byte dispatch observations establish only that experiment. They supply no throughput, peak-RSS, whole-release speedup or distribution claim.

## 11. Fail-closed posture and historical guards

[Elenchus](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/hexaemeron/skills/elenchus/SKILL.md) owns reproduction, cause and fixed/guarded classification. Stop the dependent build/receipt on source/release/registry mismatch, unbound epoch, malformed supported ABI, duplicated identity, conflicting metadata, missing required input, absent/stale report, unsupported schema, unsafe path/output, or differing offline rebuild. Missing actor evidence produces an explicit attribution gap and a pool/payer row where supported; it never permits a guessed borrower.

The inventory below binds all eleven current source views and records no current product-blocking assignment. The reused product defects are already fixed at the starting tree. No fresh parent failure was established, and absence of a new adapter/module would not reproduce one. Historical runner `S1-R1-03` stays explicitly open in its original run and outside this adapter’s repair claim. Step 1 supplies a new focused subprocess-free reporter; Step 2 supplies genuine final-green regression specimens for the historical input/write classes and new semantics. Copied scalar reports, broad suite aliases and missing-module failures cannot stand in for evidence. Any current failure discovered later requires Elenchus and an append-only study/runbook repair before its dependent transition. The no-known-findings assertion concerns new assignments within this scope, not audit completeness or an absence of historical open records.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "root",
      "path": "audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d",
      "view_sha256": "82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee"
    },
    {
      "id": "tabularium",
      "path": "plugins/tabularium/audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7",
      "view_sha256": "2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c"
    },
    {
      "id": "capture-usdc",
      "path": "audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.synopsis.md",
      "source_sha256": "213d75ae346bbd6060aa330162179a215ec7f034dec961ce020404b37e47146e",
      "view_sha256": "0f4179c49c2a7136019941fb1badc62046a625ff94c8fa3a17760d32b55b1d7c"
    },
    {
      "id": "emitter-v2",
      "path": "audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.synopsis.md",
      "source_sha256": "5a9ed2250779a10b7247992f71c8f713d20eb765b1d840109a6c03f822283a58",
      "view_sha256": "4354f3b452be3217b1a9980d3deb4f663e4acaf12a51d38ff41ba827053ddb02"
    },
    {
      "id": "schema-v3",
      "path": "audit/rounds/fiat-1362-tabularium-canonical-event-v3-and-coverage.synopsis.md",
      "source_sha256": "b27678d5bb3ce2deb6e9b8c38415073cd385870fadd39bfbb83ee501545934ec",
      "view_sha256": "067690f8e6def8e79e09b55caf8c4a77b04ecf34f5560f5b481f019aac1b763f"
    },
    {
      "id": "map-v2",
      "path": "audit/rounds/fiat-1363-entry-point-maps-at-two-pinned-wildcat-v2-c.synopsis.md",
      "source_sha256": "cdcbf90d4204251ab4536678e97e122c48032cfc4ad81e4f50e0ae3bf90db88a",
      "view_sha256": "28711061a123f3991feaa36d3e82e0cc774539220ebc2482ccfebb478bbc9c17"
    },
    {
      "id": "corpus-remaining",
      "path": "audit/rounds/fiat-1366-remaining-venue-event-conformance.synopsis.md",
      "source_sha256": "41880e3f6e2afabbecfdd202004aace2d01d8faa1dff56e1ce51ebc92fe5cf58",
      "view_sha256": "78aed7e77ab989d8ce2f9b9b983eedafd43485899128c53589bb24c7e9db6d10"
    },
    {
      "id": "corpus-wildcat",
      "path": "audit/rounds/fiat-1366-validate-solidity-event-ast-and-abi-agreeme.synopsis.md",
      "source_sha256": "dc05542f73c92bb3225c3ae43cf58a04a42143fb84566f3ffcba3075df1325d6",
      "view_sha256": "7054866e841a6eab63e2a14c7d678a55af17fa33a241cb30a6dc0531076e3936"
    },
    {
      "id": "dataset-binding",
      "path": "audit/rounds/fiat-1374-bind-the-sealed-wildcat-captures-to-dataset.synopsis.md",
      "source_sha256": "396fab30a3fc1b7970913bdb3de0d13447af526f1f0b297520b50a07c7a0f4a9",
      "view_sha256": "1c64e9b59e0ba0e07cd51f9dc8ca1b8db653cb70a9f27050463ef95e55b2782e"
    },
    {
      "id": "capture-wildcat",
      "path": "audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.synopsis.md",
      "source_sha256": "ff1b2a5396722ec03925962ac9f2aa63ce6e70e058cf1f8d4e4e61963d0c9820",
      "view_sha256": "0399cd2ef2ab8bc38c163a25ccf63dc6ebc6ebaa266e269669efdb080ea8d5a2"
    },
    {
      "id": "map-v1",
      "path": "audit/rounds/fiat-1963-wildcat-v1-entry-points-and-event-linkage.synopsis.md",
      "source_sha256": "c12d8b8456d0df0c4692504f003d4ba896818e08dc2bf2b3caefda31321e061e",
      "view_sha256": "7b4f33d1fb21c0213984c8ccc6aee4ca8992c410d791120024dd9827956381c7"
    }
  ],
  "findings": [],
  "no_known_findings": {
    "source_views": [
      {
        "id": "root",
        "source_sha256": "d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d",
        "view_sha256": "82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee"
      },
      {
        "id": "tabularium",
        "source_sha256": "1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7",
        "view_sha256": "2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c"
      },
      {
        "id": "capture-usdc",
        "source_sha256": "213d75ae346bbd6060aa330162179a215ec7f034dec961ce020404b37e47146e",
        "view_sha256": "0f4179c49c2a7136019941fb1badc62046a625ff94c8fa3a17760d32b55b1d7c"
      },
      {
        "id": "emitter-v2",
        "source_sha256": "5a9ed2250779a10b7247992f71c8f713d20eb765b1d840109a6c03f822283a58",
        "view_sha256": "4354f3b452be3217b1a9980d3deb4f663e4acaf12a51d38ff41ba827053ddb02"
      },
      {
        "id": "schema-v3",
        "source_sha256": "b27678d5bb3ce2deb6e9b8c38415073cd385870fadd39bfbb83ee501545934ec",
        "view_sha256": "067690f8e6def8e79e09b55caf8c4a77b04ecf34f5560f5b481f019aac1b763f"
      },
      {
        "id": "map-v2",
        "source_sha256": "cdcbf90d4204251ab4536678e97e122c48032cfc4ad81e4f50e0ae3bf90db88a",
        "view_sha256": "28711061a123f3991feaa36d3e82e0cc774539220ebc2482ccfebb478bbc9c17"
      },
      {
        "id": "corpus-remaining",
        "source_sha256": "41880e3f6e2afabbecfdd202004aace2d01d8faa1dff56e1ce51ebc92fe5cf58",
        "view_sha256": "78aed7e77ab989d8ce2f9b9b983eedafd43485899128c53589bb24c7e9db6d10"
      },
      {
        "id": "corpus-wildcat",
        "source_sha256": "dc05542f73c92bb3225c3ae43cf58a04a42143fb84566f3ffcba3075df1325d6",
        "view_sha256": "7054866e841a6eab63e2a14c7d678a55af17fa33a241cb30a6dc0531076e3936"
      },
      {
        "id": "dataset-binding",
        "source_sha256": "396fab30a3fc1b7970913bdb3de0d13447af526f1f0b297520b50a07c7a0f4a9",
        "view_sha256": "1c64e9b59e0ba0e07cd51f9dc8ca1b8db653cb70a9f27050463ef95e55b2782e"
      },
      {
        "id": "capture-wildcat",
        "source_sha256": "ff1b2a5396722ec03925962ac9f2aa63ce6e70e058cf1f8d4e4e61963d0c9820",
        "view_sha256": "0399cd2ef2ab8bc38c163a25ccf63dc6ebc6ebaa266e269669efdb080ea8d5a2"
      },
      {
        "id": "map-v1",
        "source_sha256": "c12d8b8456d0df0c4692504f003d4ba896818e08dc2bf2b3caefda31321e061e",
        "view_sha256": "7b4f33d1fb21c0213984c8ccc6aee4ca8992c410d791120024dd9827956381c7"
      }
    ],
    "consuming_step": 1,
    "surveyor_assertion": "no-known-findings"
  }
}
```

New semantic regressions also need focused cases: wrong actor on amount-only draw/closure, third-party repayment, executor-versus-account withdrawal, wrapper-party/instrument collapse, mint/deposit double capital, closure timestamp-as-money, changed mapping inference class, unreleased indexed-actor signature, unknown-role/topic disposition, malformed supported ABI, and source-selector tampering. An accounting replay assertion belongs to #1386, outside these guards.

## 12. Decisions and durable homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/b4af9c748a764287ccb9978937021e45cc81fc2d/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns the decision/record contract. The costly decisions are role-qualified native dispatch, pool/actual-party representation, the narrowly qualified quantity-free closure form, and the self-contained raw-input/class descriptor. Record them in `docs/decisions/drafts/keep-wildcat-canonical-events-bound-to-native-roles.md` before the relevant implementation. Merge allocates its ADR number; no guessed number enters the study.

Copy the receipted study/runbook/design evidence and reports to `docs/kickoff/1378/` in Step 1, then keep public mapping semantics, source pins, unsupported key definitions and recovery commands there. The adapter user guide lives at `plugins/tabularium/docs/wildcat-canonical.md`; constructed public releases live at `plugins/tabularium/examples/wildcat-v1-v0/` and `plugins/tabularium/examples/wildcat-v2-v0/`. Their READMEs identify constructed capture status and immutable release versions. New module comments explain only source-dependent decisions. Runtime privacy/custody output remains local. Warden’s record stays at the controller’s `audit/rounds/fiat-1378-wildcat-v1-v2-canonical-adapter.md`.

Readiness: twelve of twelve study sections are complete, design lock is checked, and selection evidence is closed. Semantic/schema/release conformance remains scheduled at its named stop points. The next authorised action is deriving the source-bound runbook; no product implementation or delivery is claimed by this study.

### Amendment -- 2026-10-03

**What changed.** The study now joins the selected role-qualified design to its standing decision record. The design choice, evidence, criteria and stop points are unchanged.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | role-qualified
record | adr/keep-wildcat-canonical-events-bound-to-native-roles
```

**Why.** Step 1 ships this study. Hypomnema requires the explicit bridge from its selected design to the decision record.

**Steps touched.** Step 1 copies the amended study and checks its bridge. Steps 2, 3 and 4 retain their existing implementation and verification requirements.

**Still holding.**
Step 1: entry holds; exit holds.
Step 2: entry holds; exit holds.
Step 3: entry holds; exit holds.
Step 4: entry holds; exit holds.


### Amendment -- 2026-10-03

**What changed.** Step 1 also repairs the replacement-object positive control in `plugins/hexaemeron/tests/test_fiat_starting_commit_bindings.py`. Only that temporary fixture observation may remove inherited `GIT_NO_REPLACE_OBJECTS`; the value is restored before the explicit native-object check and controller verification. Controller code, its closed environment, design selection and adapter boundaries stay fixed.

**Why.** The required implementation-admission suite failed at the existing test's line 404. The exact test failed under the pinned controller's closed environment and passed under the ambient environment. Its fixture inherited `GIT_NO_REPLACE_OBJECTS=1`, so ordinary Git could not observe the replacement object that the positive control requires. The subsequent protected read must still reject replacement bytes.

**Steps touched.** Step 1's Files and Tests include this fixture repair and its ambient/closed-environment reproduction. The earlier no-current-assignment record remains a statement about the original inventory; this newly observed failure carries separate evidence.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
