# Indexed-actor event decision for issue 1372

Issue: https://github.com/wildcat-finance/skills/issues/1485, a prerequisite
child of https://github.com/wildcat-finance/skills/issues/1372.

Decision: **pursue**, with `wildcat-finance/v2-protocol` tag v2.5.4, commit
`bea503c2736d47de7fd34130c64f10783dc35b39`, as the interim candidate.
Dr Laurence E. Day (`laurenceday`), protocol maintainer, selected it in the
delivery session on 2026-09-17, on the basis of Dave Coleman's 2026-09-16
statement about the v2.5 release line. The existence of `release/v2.5`, the
v2.5.4 tag or the `deploy/sepolia-v2.5.4` branch played no part in it.

Shoggoth prepared this record as Surveyor under Protasis. Dr Laurence E. Day
is the reviewer and reviews the pull request before it merges.
[`evidence/decision.json`](evidence/decision.json) holds the question, the
selected option and the statement's digest.
[`evidence/source-comparison.json`](evidence/source-comparison.json) holds every
commit, digest, declaration, emit site and cited line below.

## Decision

- Pursue the indexed-actor event model on the v2.5 line.
- The pin is interim. Dave Coleman stated that v2.5.4 is the latest Sepolia
  deployment and the top of the line, and that the next release will most
  likely change events because MarketClosed needs adjustment.
- Before #1372, #1363, #1381 or #1406 uses a result at `bea503c2` as a merge
  gate, it checks the line's current top. A successor head needs a new pin and
  a new #1372 audit.
- Candidate-merge acceptance in #1372 and #1406 applies to the pinned head.
  The disposable-comparison limit for a declined candidate does not apply.
- The rest of the statement describes unreleased work outside the event surface
  and stays out of this record. `decision.json` binds the relayed text by
  SHA-256 `730cf0c77b5e6629532614489595ac41c319d011e6ce35148622027929c51c34`.

## Two sources

Repository: https://github.com/wildcat-finance/v2-protocol

- Deployed: commit `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`, tree
  `0bfd98ed7a475fa0e6ef6b0268212cf5ca4782a2`, tag v2.0.0. Selected by the
  #1482 registry row `wildcat-v2-ethereum-mainnet`, source relation `deployed`.
- Candidate: commit `bea503c2736d47de7fd34130c64f10783dc35b39`, tree
  `fb835bf2ac89b616fa9bbdbe771b6554d916f26a`, tag v2.5.4 and the
  `release/v2.5` head. Selected by this decision.

v2.0.0 is an ancestor of v2.5.4. v2.5.4 is not on `main` (`f5a26146`). The
head of v2-protocol PR #116 (`4cd92a3f`, V25-ORG-04, the events data model) is
an ancestor of v2.5.4. `deploy/sepolia-v2.5.4` (`1263de7e`) has the same `src`
tree, `2f8baba6599506903f28bb74bfbc8140433b0627`. `src/` grows from 60
to 108 files: all 60 are modified and 48 are added, for 11,186 insertions and
1,549 deletions.

The deployed side comes from `docs/kickoff/1359/targets.json` at skills
`9599fa46e8e2c5436a0dae4327c8e5b72f5159a9`, SHA-256
`9e0d3c88c76ec727ea8aabe67fb8ac0648b039ef1fa9836a6a7f2f2ae4d4ca98`. Its row
`wildcat-v2-ethereum-mainnet` lists #1485 as a consumer, with the boundary
"The registry supplies only the deployed comparison base." The row is
`blocked` on #1590, which still binds deployed emitter epochs. The four
emitter files at `a70f297f` are byte-identical to those at the row's emitter
pin, `f5a26146`.

## Actor roles

Caller is `msg.sender`. Debtor is the market's `borrower()`. Payer is the
address whose assets enter the market. Registry-derived owner is
`borrowerIdentityRegistry.resolveBorrower(borrower())`: a registered borrower
resolves to itself, a Borrower Account to its principal. Line numbers are at
v2.5.4 unless marked v2.0.0.

| Transition | v2.0.0 event | v2.5.4 event |
| --- | --- | --- |
| borrow, `WildcatMarket.sol:118`, `onlyBorrower` | `Borrow(uint256 assetAmount)`, v2.0.0 `:165` | `Borrow(address indexed borrower, uint256 assetAmount)`, `:139` |
| repay, `:163`, and `repayAndProcessUnpaidWithdrawalBatches`, `WildcatMarketWithdrawals.sol:346`; any caller | `DebtRepaid(address indexed from, uint256 assetAmount)` | unchanged, `:167` and `WildcatMarketWithdrawals.sol:354` |
| close, `:183`, `onlyBorrower` | `MarketClosed(uint256 timestamp)`, v2.0.0 `:292` | `MarketClosed(address indexed borrower, uint256 timestamp)`, `:274` |
| fee collection, `:101`, any caller | `FeesCollected(uint256 assets)`, v2.0.0 `:135` | `FeesCollected(address indexed collector, address indexed feeRecipient, uint256 assets)`, `:111` |
| revolving drawn amount, `WildcatMarketRevolving.sol:118` | none | `DrawnAmountUpdated(uint256 previousDrawnAmount, uint256 newDrawnAmount)`, `:122` |
| borrower transfer, `WildcatMarketBase.sol:474`, `:496`, `:513` | none | `BorrowerTransferRequested`, `BorrowerTransferCancelled`, `BorrowerTransferred`, `:485`, `:502`, `:530` |
| market deployment, `HooksFactory.sol:779` | `MarketDeployed` with no borrower field, v2.0.0 `HooksFactory.sol:555` | `MarketDeployed` with `borrower`, `borrowerPrincipal`, `borrowerIdentityRegistry`, `HooksFactory.sol:656`, `HooksFactoryRevolving.sol:705` |
| registry owner change, `WildcatBorrowerIdentityRegistry.sol:160` | none | `BorrowerAccountPrincipalTransferred(address indexed account, address indexed previousPrincipal, address indexed newPrincipal)`, `:172` |
| debt terms, `WildcatMarketConfig.sol` | `MaxTotalSupplyUpdated(uint256)`, `AnnualInterestBipsUpdated(uint256)`, `ReserveRatioBipsUpdated(uint256)`, `ProtocolFeeBipsUpdated(uint256)` | caller-indexed forms with previous and new values, `:125`, `:161`, `:242` |

Each proposed actor, and the existing `DebtRepaid.from` for contrast:

| Field | Value | Caller | Debtor | Payer | Registry-derived owner |
| --- | --- | --- | --- | --- | --- |
| `Borrow.borrower`, indexed | `msg.sender`, `WildcatMarket.sol:121` | yes | yes, by `onlyBorrower` | no | not logged |
| `DebtRepaid.from`, indexed, unchanged | `msg.sender` | yes | not logged; any address may repay | yes | not logged |
| `MarketClosed.borrower`, indexed | `msg.sender` | yes | yes, by `onlyBorrower` | pays any shortfall, logged in `DebtRepaid` | not logged |
| `FeesCollected.collector`, indexed | `msg.sender` | yes | no | no; the market pays | no |
| `FeesCollected.feeRecipient`, indexed | the market's fee recipient | not by construction | no | no; it receives | no |
| `BorrowerTransferRequested.borrower`, `BorrowerTransferCancelled.borrower`, indexed | `msg.sender` | yes | yes, current | no | no; the stored principal is a payload field |
| `BorrowerTransferred.previousBorrower`, indexed | `borrower()` before the transfer | no | yes, before | no | no |
| `BorrowerTransferred.newBorrower`, indexed | the pending borrower, which must be `msg.sender`, `WildcatMarketBase.sol:515` | yes | yes, after | no | no |
| `BorrowerTransferred.newBorrowerPrincipal`, indexed | `resolveBorrower(newBorrower)` at acceptance, stored at `:528` | no | no | no | yes |
| `MarketDeployed.borrower` | the deployment caller, `HooksFactory.sol:733` | yes | yes, initial | no | no |
| `MarketDeployed.borrowerPrincipal` | `_resolveBorrowerPrincipal(msg.sender)`, `HooksFactory.sol:786` | no | no | no | yes, at deployment |
| `MarketDeployed.borrowerIdentityRegistry` | the registry address | no | no | no | no; it names the registry |
| `BorrowerAccountPrincipalTransferred.account`, indexed | the Borrower Account | no | yes when it is a market's `borrower()` | no | no |
| `BorrowerAccountPrincipalTransferred.newPrincipal`, indexed | the accepting caller, `WildcatBorrowerIdentityRegistry.sol:162` | yes | no | no | yes |
| `MaxTotalSupplyUpdated.caller`, indexed | `msg.sender` | yes | yes, by `onlyBorrower` | no | no |
| `AnnualInterestAndReserveRatioBipsUpdated.caller`, indexed | `msg.sender` | yes | only through `setAnnualInterestAndReserveRatioBips` or `closeMarket`; `executePendingAnnualInterestBipsReduction`, `WildcatMarketConfig.sol:202`, admits any caller | no | no |
| `ProtocolFeeBipsUpdated.caller`, indexed | `msg.sender`, which must be the factory, `WildcatMarketConfig.sol:231` | yes | no | no | no |

Gaps the actor fields leave:

- No borrow, repay or close log carries the registry-derived owner. The market
  writes its stored `borrowerPrincipal()` only at deployment,
  `WildcatMarketBase.sol:291`, and at an accepted borrower transfer, `:528`. A
  registry principal transfer emits no market event, so the stored value can
  differ from `resolveBorrower(borrower())`.
- `DrawnAmountUpdated` changes revolving debt on borrow, repay and close and
  has no actor field. Attribution depends on another log in the same
  transaction.
- A close surplus leaves by `safeTransfer`, `WildcatMarket.sol:200` and v2.0.0
  `:227`. No market event carries that amount at either commit.
- Every changed declaration has a new topic0: `Borrow` `0xb848ae6b…` becomes
  `0xcbc04eca…`, `MarketClosed` `0x9dc30b8e…` becomes `0xcd125386…`, and
  `FeesCollected` `0x860c0aa5…` becomes `0x9bcb6d1f…`. A decoder keyed on
  v2.0.0 topic0 values does not match the candidate events. Logs the deployed
  contracts emitted stay amount-only for borrow, close and fee collection.
  Consumers must not use a candidate field to fill a party those logs lack.

## Event surface

Declarations under `src/`, parsed from text: 72 distinct at v2.0.0 and 105 at
v2.5.4. By name, 37 are added, 20 changed, 38 unchanged and 4 removed:
`AccountSanctioned`, `AnnualInterestBipsUpdated`, `ReserveRatioBipsUpdated` and
`SanctionedAccountAssetsSentToEscrow`. No changed name keeps its topic0. The 14
changed names outside the tables above are hooks, access-control and factory
events declared in `src/access/` and `src/IHooksFactory.sol`, and each gains an
administrator or caller field. `event_changes` lists every declaration and
topic0. The emitter library has 27
functions at v2.0.0 and 29 at v2.5.4, and each hard-coded topic0 and `logN`
topic count agrees with its declaration. That comparison does not replace the
separate emitter-versus-declaration report #1361 owes for the candidate.

## Scope for #1363 and #1372

At the candidate, the emitters are `src/libraries/MarketEvents.sol` and
`src/spherex/SphereXProtectedEvents.sol`, and the market declarations are in
`src/interfaces/IMarketEventsAndErrors.sol`. Debt-event emit sites are in
`src/market/WildcatMarket.sol`, `WildcatMarketBase.sol`,
`WildcatMarketConfig.sol`, `WildcatMarketRevolving.sol`,
`WildcatMarketToken.sol` and `WildcatMarketWithdrawals.sol`, plus
`src/HooksFactory.sol`, `src/HooksFactoryRevolving.sol` and
`src/WildcatBorrowerIdentityRegistry.sol`. `files` gives the blob, SHA-256 and
byte count of each at both commits. #1371 still owns the named-file audit
scope.

## Consumers

| Consumer | Takes | Boundary |
| --- | --- | --- |
| [#1372](https://github.com/wildcat-finance/skills/issues/1372) | both commits, the decision, the scope paths | audits `bea503c2` exactly; a successor head needs its own audit before any merge-gate use |
| [#1363](https://github.com/wildcat-finance/skills/issues/1363) | both commits | its two reports are at these commits; a successor needs a new candidate report |
| [#1381](https://github.com/wildcat-finance/skills/issues/1381) | the candidate and its indexed actors | prices topics at `bea503c2`; whether the cost is accepted stays a separate maintainer decision |
| [#1406](https://github.com/wildcat-finance/skills/issues/1406) | both commits and the actor tables | candidate mode checks each debt transition against the tables; `DrawnAmountUpdated` has no actor to check |
| [#1378](https://github.com/wildcat-finance/skills/issues/1378) | the deployed-side boundary | deployed logs stay amount-only; the candidate is a separate subject |
| [#1361](https://github.com/wildcat-finance/skills/issues/1361) | the candidate commit | owes the candidate its own emitter-versus-declaration report |
| `plugins/hexaemeron/harness`, from #1354 | nothing yet | its emitters come from `f5a26146`, byte-identical to v2.0.0; a candidate mode needs a `bea503c2` pin |

## Check it

```bash
git clone https://github.com/wildcat-finance/v2-protocol.git
git -C v2-protocol rev-parse 'v2.0.0^{commit}' 'v2.5.4^{commit}'
git -C v2-protocol merge-base --is-ancestor v2.0.0 v2.5.4
git -C v2-protocol rev-parse bea503c2:src 1263de7e:src
git -C v2-protocol diff --shortstat v2.0.0 v2.5.4 -- src
git -C v2-protocol show bea503c2:src/market/WildcatMarket.sol | sed -n 139p
cast keccak 'Borrow(address,uint256)'
python3 scripts/kickoff_targets.py check
```

Results on 2026-09-17: the tags resolve to `a70f297f…` and `bea503c2…`; the
ancestry check exits 0; both `src` trees are `2f8baba6…`; the diff reports
`108 files changed, 11186 insertions(+), 1549 deletions(-)`; line 139 reads
`emit_Borrow(currentBorrower, amount);`; `cast keccak` prints
`0xcbc04eca7e9da35cb1393a6135a199ca52e450d5e9251cbd99f7847d33a36750`; the
registry check prints `kickoff-targets: clean; 58 consumers, 17 targets (0
resolved, 0 candidate, 9 blocked, 8 excluded), 0 pending decision(s)` and exits 0.
Run the last command from the skills repository with the interpreter in
`.python-version`, 3.14.6.

## Method

Source reads used `git show`, `git ls-tree` and `git rev-parse` at the two
commits, with no build, compiler or RPC call. Event declarations were parsed
from text with comments removed; user-defined value types resolve to their
underlying type, and topic0 is keccak256 of the canonical signature. This is a
text parse, not a compiled ABI. Roles were read from the cited lines, and all
68 `file:line` citations in `source-comparison.json` were checked against their
commit before the file was written. GitHub reads at 2026-09-17T04:01:49Z
confirmed both commits, both tags and the `release/v2.5` head.

## Evidence boundary

This record establishes the maintainer's pursue decision and interim pin as
recorded, and the source-level declarations, emitter constants, emit sites and
actor roles at two commits. It does not establish that v2.5.4 or a successor is
or will be deployed on any mainnet, which deployed markets' emitter epochs equal
v2.0.0 (#1590), compiled ABI or bytecode equality, the audit status or safety
of either commit, the gas cost of the added topics (#1381), or the successor
release's events.

## Files

- [`evidence/decision.json`](evidence/decision.json): SHA-256
  `630ffc2efef0bc5b1630959d13eda781e7fa083f9d3e5ca116e005caf4bf34bc`.
- [`evidence/source-comparison.json`](evidence/source-comparison.json): SHA-256
  `c8c56338d4556bf08ce6e86500e4c1e24516727d9c410782f44f764678f55b5a`.
