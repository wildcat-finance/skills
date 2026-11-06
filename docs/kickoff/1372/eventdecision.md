# Proposed indexed-actor event revision: pin and decision

Issue: https://github.com/wildcat-finance/skills/issues/1485, a prerequisite
child of https://github.com/wildcat-finance/skills/issues/1372.

Dr Laurence E. Day, maintainer, decided this on 2026-09-17 by answering four
structured questions in the delivery session. The
[decision comment](https://github.com/wildcat-finance/skills/issues/1485#issuecomment-5714361463)
reproduces each question, every option offered and the option selected.
The delivery session posted it from his account; it is not a separate GitHub
review. [`evidence/decision.json`](evidence/decision.json) preserves the same
answers and binds that comment's 4,020 bytes by SHA-256.

Shoggoth prepared the source comparison as Surveyor under Protasis. The
reviewer is the independent agent the decision-maker chose; its report names the
digests it checked and sits in [`evidence/review.json`](evidence/review.json)
and the body of the pull request that adds this record.
[`eventdecision.json`](eventdecision.json) carries the pin, the semantics and
the signature delta in a form #1372 can read.
[`evidence/sources.json`](evidence/sources.json) holds both commits, their file
digests and the build inputs, and
[`evidence/commands.json`](evidence/commands.json) holds the commands and their
results. Every Solidity path and line below is at
`bea503c2736d47de7fd34130c64f10783dc35b39` unless it is marked as the base.

## Decisions

| Question | Selected | Recommended when asked |
| --- | --- | --- |
| Which SHA does the record pin as the proposed candidate? | `release/v2.5` @ `bea503c2` | `release/v2.5` @ `bea503c2` |
| Is the revision intended to ship to production? | Pursue | Pursue |
| How should the record treat the actor semantics read from the emit sites? | Ratify all six as intended | Ratify all six as intended |
| Who should the record name as its reviewer? | Independent agent | Independent agent |

No part of this decision is inferred from the presence of a branch. Seven branch
heads carry the revision; the decision selects one and states why the other six
are not it.

## The two sources

Both are in `wildcat-finance/v2-protocol`:

- Deployed base: ref `main`, commit
  `f5a26146987926f4811b72a795d662813dedfe85`, tip dated 2026-08-19.
- Proposed candidate: ref `release/v2.5`, commit
  `bea503c2736d47de7fd34130c64f10783dc35b39`, tip dated 2026-09-05.

The base is the registry row `wildcat-v2-ethereum-mainnet` approved for #1372
and #1363 in [`../1359/targets.md`](../1359/targets.md). That registry excludes
unreleased Wildcat code, so it supplies the base and nothing else; selecting
the candidate is this record's job.

`deployments/sepolia/source-v2-5-4.txt` at
`1263de7ef41ba7f3b4ca2aa6d614640ad31113ef` pins
`contract_source_commit=bea503c2736d47de7fd34130c64f10783dc35b39` with solc
0.8.25, EVM version `cancun`, 44 optimizer runs and `via_ir` on, and deploys it
to Sepolia as release `v2-5-4` on chain 11155111. That is a testnet deployment.
Nothing here establishes an Ethereum mainnet deployment.

Every branch head was read for `event Borrow(address indexed borrower, uint256
assetAmount);`. Seven carry it. The six that were not selected:

| Ref | Commit | Relation to the selected commit | Why not |
| --- | --- | --- | --- |
| `deploy/sepolia-v2.5.4` | `1263de7e` | descendant by 2 commits | its 57 changed paths are all under `deployments/`, `docs/`, `script/`, `scripts/` and `package.json`, so it adds no Solidity; the next ceremony supersedes the branch |
| `fiat/147-replace-spherex-on-the-events-data-model-gen` | `77ac6f30` | ancestor by 84 commits | introduced the revision, but predates the v2.5 natspec and later release fixes |
| `feat/v2.5-singleton-role-provider` | `99bb8584` | diverged, 9 ahead and 209 behind | carries the revision on an unmerged feature branch |
| `codex/issue-128-singleton-hook-specialisation` | `e88e799b` | diverged, 9 ahead and 209 behind | stacked on the branch above, and unmerged with it |
| `experiment/gas-optimization-sweep` | `f0260b8f` | diverged, 43 ahead and 174 behind | carries the revision on a branch its own tip calls an experiment |
| `feat-mv2-adapter` | `a263fe61` | diverged, 4 ahead and 74 behind | an open adapter draft, whose pull request targets `release/v2.5` rather than the reverse |

`deploy/sepolia-v2.5.4` has the latest tip of the seven, at 2026-09-07, so the
selected commit is the newest carrier that contributes Solidity of its own.
`release/v2.6` at `dec36d22` is an ancestor of the selected commit by 232
commits and is not a carrier: its indexed-actor signatures match the deployed
base, although it does drop `SanctionedAccountAssetsSentToEscrow` and add
`WrapperRegistered`. The branch name does not order the release line.

## Actor semantics per transition

Six transitions are ratified: draw, repay, close, fee collection, configuration
and borrower transfer. The table has twelve rows because configuration covers
three events and transfer covers three, and because `Deposit` and
`WrapperRegistered` are listed for contrast rather than ratified. Each row is
read from the emit site, not from the parameter name. Four classes are
distinguished: payer, debtor, caller and registry-derived owner.

| Transition | Event field | Address emitted | Gate on the entry points | Class |
| --- | --- | --- | --- | --- |
| Deposit | `Deposit.account` | `msg.sender` (`src/market/WildcatMarket.sol:70`) | `hooks.onDeposit` at `:61` only; `depositUpTo` at `:85` and `deposit` at `:94` are otherwise ungated | caller |
| Draw | `Borrow.borrower` | `msg.sender` (`:139`, read at `:121`) | `onlyBorrower` (`:118`) | debtor |
| Repay | `DebtRepaid.from` | `msg.sender` (`:152`, `:167`, `src/market/WildcatMarketWithdrawals.sol:354`) | none on `repay` (`:163`) or `repayAndProcessUnpaidWithdrawalBatches` (`WildcatMarketWithdrawals.sol:346`); `closeMarket` also reaches `:152` through `_repay` at `:195` | payer |
| Close | `MarketClosed.borrower` | `msg.sender` (`:274`) | `onlyBorrower` (`:183`) | debtor |
| Fee collection | `FeesCollected.collector` | `msg.sender` (`:111`) | none (`:101`) | caller |
| Deposit cap | `MaxTotalSupplyUpdated.caller` | `msg.sender` (`src/market/WildcatMarketConfig.sol:125`) | `onlyBorrower` (`:115`) | caller |
| APR and reserve ratio | `AnnualInterestAndReserveRatioBipsUpdated.caller` | `msg.sender` (`WildcatMarketConfig.sol:161`, `WildcatMarket.sol:267`) | `onlyBorrower` on `setAnnualInterestAndReserveRatioBips` (`WildcatMarketConfig.sol:176`) and `closeMarket` (`WildcatMarket.sol:183`); none on `executePendingAnnualInterestBipsReduction` (`WildcatMarketConfig.sol:202`) | caller |
| Protocol fee | `ProtocolFeeBipsUpdated.caller` | `msg.sender` (`WildcatMarketConfig.sol:242`) | reverts unless the caller is the factory (`:231`) | caller |
| Wrapper | `WrapperRegistered.wrapper` | the registered wrapper (`WildcatMarketConfig.sol:67`) | reverts unless the caller is `wrapperFactory` (`:64`) | not an actor field |
| Transfer requested | `BorrowerTransferRequested` | `msg.sender` and `borrowerPrincipal()` (`src/market/WildcatMarketBase.sol:485`, read at `:489`) | `onlyBorrower` (`:474`) | debtor and registry-derived owner |
| Transfer cancelled | `BorrowerTransferCancelled` | `msg.sender` and `borrowerPrincipal()` (`:502`, read at `:505`) | `onlyBorrower` (`:496`) | debtor and registry-derived owner |
| Transfer completed | `BorrowerTransferred` | `pendingBorrower()` and the principal validated at `:518` (`:530`) | reverts unless the caller is the pending borrower (`:515`) | debtor and registry-derived owner |

Four readings matter to a consumer:

- Repay is permissionless, so `DebtRepaid.from` is the payer. It is the debtor
  only when the debtor happened to pay.
- `collectFees` is permissionless, so `FeesCollected.collector` carries no role.
  The separate `feeRecipient` field is the immutable configured recipient that
  received the assets.
- The three configuration events name the caller, and what that caller can be
  differs per event. `ProtocolFeeBipsUpdated.caller` is always the factory.
  `MaxTotalSupplyUpdated.caller` is always the operational borrower, because its
  one entry point is gated. `AnnualInterestAndReserveRatioBipsUpdated.caller` is
  an arbitrary address on the third path, which the source at
  `WildcatMarketConfig.sol:199` documents as permissionless. That path still
  reverts at `:205` unless the hook enables it, so it is unreachable on a
  non-periodic market, and the hook rather than the caller supplies the new rate.
- `borrowerPrincipal()` is the address registered in the ArchController. It is
  indexed once, as `BorrowerTransferred.newBorrowerPrincipal`, and is ordinary
  data on the request and cancel events, so the transfer lifecycle cannot be
  filtered by principal across all three events.

`onlyBorrower` is at `src/market/WildcatMarketBase.sol:348`; `borrower()` and
`borrowerPrincipal()` are at `:176` and `:181`.

## Signature delta

Five events gained an actor, two were replaced by one new event, six are new,
two were removed, and two are unchanged. That is the seventeen rows below.

| Event | Base signature | Candidate signature |
| --- | --- | --- |
| `MaxTotalSupplyUpdated` | `(uint256)` | `(address,uint256,uint256)` |
| `ProtocolFeeBipsUpdated` | `(uint256)` | `(address,uint256,uint256)` |
| `AnnualInterestBipsUpdated` | `(uint256)` | replaced |
| `ReserveRatioBipsUpdated` | `(uint256)` | replaced |
| `AnnualInterestAndReserveRatioBipsUpdated` | absent | `(address,uint256,uint256,uint256,uint256)` |
| `Borrow` | `(uint256)` | `(address,uint256)` |
| `MarketClosed` | `(uint256)` | `(address,uint256)` |
| `FeesCollected` | `(uint256)` | `(address,address,uint256)` |
| `SanctionedAccountAssetsSentToEscrow` | `(address,address,uint256)` | removed |
| `AccountSanctioned` | `(address)` | removed |
| `WrapperRegistered` | absent | `(address)` |
| `BorrowerTransferRequested` | absent | `(address,address,address,address,address,address)` |
| `BorrowerTransferCancelled` | absent | `(address,address,address,address)` |
| `BorrowerTransferred` | absent | `(address,address,address,address)` |
| `DrawnAmountUpdated` | absent | `(uint256,uint256)` |
| `Deposit` | `(address,uint256,uint256)` | unchanged |
| `DebtRepaid` | `(address,uint256)` | unchanged |

`Deposit` and `DebtRepaid` are byte-identical in both declaration and emitter
body across the two commits. They are the two events inside this delta that
already carried an indexed actor. Outside it, `Transfer`, `Approval`, the two
surviving sanctioned account events, `WithdrawalQueued` and `WithdrawalExecuted`
carry unchanged indexed actors. The four remaining withdrawal batch events index
only `expiry`, which is not an actor.

Every topic0 is in [`eventdecision.json`](eventdecision.json). The emitters in
`src/libraries/MarketEvents.sol` are hand-written assembly with the topic hash
as a literal, so each literal was checked against `cast keccak` of the signature
declared for it: 22 cases, no mismatch. That establishes that those emitters
agree with their declarations at each commit. It does not establish that either
surface is correct or complete. `WrapperRegistered` is the one changed event
emitted by an ordinary Solidity `emit`, so it carries no literal to check.

Each `emitted_at` in the JSON names the `function emit_X(` header rather than
the `logN` line that holds the literal.

`AccountSanctioned` is declared at the base in
`src/interfaces/IMarketEventsAndErrors.sol:127` with no emitter in
`src/libraries/MarketEvents.sol`. That reading covers the event files alone and
is not a claim that nothing emits it.

`src/spherex/SphereXProtectedEvents.sol` differs between the two commits on one
line: `pragma solidity ^0.8.20;` at the base becomes `pragma solidity 0.8.25;`
at the candidate. Its five emitters are otherwise identical. The SphereX removal
on the same release line is a separate change and is outside this record.

## Consumers

| Consumer | What it takes from here | Preserved |
| --- | --- | --- |
| [#1372](https://github.com/wildcat-finance/skills/issues/1372) | the candidate commit, the signature delta and the ratified semantics; it audits the diff at that head | audit scope and emitter paths |
| [#1363](https://github.com/wildcat-finance/skills/issues/1363) | both commits, as the two-commit pair its entry-point maps diff | audit scope and emitter paths |
| [#1381](https://github.com/wildcat-finance/skills/issues/1381) | the five events that have a topic0 at each commit and gained a topic: `MaxTotalSupplyUpdated`, `ProtocolFeeBipsUpdated`, `Borrow` and `MarketClosed` from `log1` to `log2`, and `FeesCollected` from `log1` to `log3` | none stated |
| [#1406](https://github.com/wildcat-finance/skills/issues/1406) | the candidate commit as the source of its proposed mode | none stated |

#1363, #1381 and #1406 are tied to this record by their rows in
[`../1359/targets.json`](../1359/targets.json); #1372's tie is the parent
relation rather than a registry row.

The emitter paths preserved for #1363 and #1372 are
`src/interfaces/IMarketEventsAndErrors.sol`,
`src/interfaces/IWildcatMarketRevolving.sol`, `src/libraries/MarketEvents.sol`,
`src/market/WildcatMarket.sol`, `src/market/WildcatMarketBase.sol`,
`src/market/WildcatMarketConfig.sol`, `src/market/WildcatMarketRevolving.sol`
and `src/market/WildcatMarketWithdrawals.sol`.

## What this does not establish

The candidate is deployed on Sepolia and nowhere else. This record pins two
sources and records a decision. It does not audit the diff, which is #1372's
work. The ratified semantics say what each emit site passes, not that the
candidate is free of defects. A pursue decision is the maintainer's statement of
intent. It is not a merge, a release or a mainnet deployment.
