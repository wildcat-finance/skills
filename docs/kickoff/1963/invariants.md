# Invariant Map

> Wildcat V1 | 78 guards | 51 inferred (35 single-contract, 12 cross-contract, 4 economic) | 12 not enforced on-chain

**Source identity.** Every `file:line` below reads core commit `da74452aa7d1a0f024d99efd22cc6d950a8116b7` of `wildcat-finance/wildcat-protocol`. `WildcatSanctionsSentinel` and `WildcatSanctionsEscrow` were deployed from sentinel commit `6164ddd4c75ef6da2181e5623b99795b9829e31c`; `git diff` between the two commits changes only the SPDX licence line of those files, so their line numbers match. `MarketLens` has no single matching commit (closest `488b30d08c73a93be3e4bf99128c774997411d3a`, 40 of 46 in-tree files); its reads here use the da74452a bytes. Paths are relative to `src/` unless they start with `lib/`. This map describes code; it does not establish that the protocol is safe.

---

## 1. Enforced Guards (Reference)

Per-call preconditions. Heading IDs below (`G-N`) are anchor targets from x-ray.md attack surfaces. Checked-arithmetic rows quote the statement whose underflow reverts.

#### G-1
`if (state.isClosed) { revert_DepositToClosedMarket(); }` · `market/WildcatMarket.sol:52` · Closure fixes debts at settlement, so the unsanctioned deposit branch refuses new principal afterwards.

#### G-2
`if (scaledAmount == 0) revert_NullMintAmount();` · `market/WildcatMarket.sol:61` · Stops an asset transfer that would mint no scaled claim at the current scale factor.

#### G-3
`if (amount != actualAmount) { revert_MaxSupplyExceeded(); }` · `market/WildcatMarket.sol:113` · Makes `deposit` all-or-nothing against the `maximumDeposit` clamp; a zero `amount` equals the sanctioned branch's implicit zero return, so that branch commits.

#### G-4
`if (state.accruedProtocolFees == 0) { revert_NullFeeAmount(); }` · `market/WildcatMarket.sol:123` · Keeps `collectFees` from running with nothing owed to the fee recipient.

#### G-5
`if (withdrawableFees == 0) { revert_InsufficientReservesForFeeWithdrawal(); }` · `market/WildcatMarket.sol:127` · Fees are paid only from assets beyond paid-but-unclaimed withdrawals (see I-22).

#### G-6
`if (IWildcatSanctionsSentinel(sentinel).isFlaggedByChainalysis(borrower)) { revert_BorrowWhileSanctioned(); }` · `market/WildcatMarket.sol:145` · A borrower on the Chainalysis list cannot draw funds; borrower overrides are not consulted here.

#### G-7
`if (state.isClosed) { revert_BorrowFromClosedMarket(); }` · `market/WildcatMarket.sol:150` · Closed markets are settled; no further principal leaves to the borrower.

#### G-8
`if (amount > borrowable) { revert_BorrowAmountTooHigh(); }` · `market/WildcatMarket.sol:154` · Holds `totalAssets() - amount >= liquidityRequired()` at borrow time (reserve ratio, withdrawals, fees).

#### G-9
`if (amount == 0) { revert_NullRepayAmount(); }` · `market/WildcatMarket.sol:163` · `repayOutstandingDebt` and `repayDelinquentDebt` refuse when the computed debt is zero.

#### G-10
`if (state.isClosed) { revert_RepayToClosedMarket(); }` · `market/WildcatMarket.sol:166` · After closure the settlement in `closeMarket` is the only repayment path.

#### G-11
`if (state.isClosed) { revert_RepayToClosedMarket(); }` · `market/WildcatMarket.sol:202` · Same boundary for `repay`, checked after its transfer, so the whole call reverts.

#### G-12
`if (_withdrawalData.unpaidBatches.length() > 0) { revert_CloseMarketWithUnpaidWithdrawals(); }` · `market/WildcatMarket.sol:218` · Closure cannot strand expired batches that were only partly paid.

#### G-13
`if (msg.sender != borrower) revert_NotApprovedBorrower();` · `market/WildcatMarketBase.sol:126` · Only the market's immutable borrower may `borrow`.

#### G-14
`if (msg.sender != controller) revert_NotController();` · `market/WildcatMarketBase.sol:131` · Market configuration and closure pass through the deploying controller, which applies the borrower's bounds.

#### G-15
`if (account.approval == AuthRole.Blocked) { revert_AccountBlocked(); }` · `market/WildcatMarketBase.sol:146` · Blocked accounts cannot send, receive, queue, or be re-authorised. `stunningReversal` and `_blockAccount` read the stored role without this check, and `_executeWithdrawal` reads no role, so a `Blocked` account that is no longer sanctioned still receives executed withdrawals.

#### G-16
`if (uint256(account.approval) < uint256(requiredRole)) { revert_NotApprovedLender(); }` · `market/WildcatMarketBase.sol:207` · Deposits need `DepositAndWithdraw`; withdrawal queueing needs at least `WithdrawOnly`.

#### G-17
`iszero(and(eq(returndatasize(), 0x20), staticcall(gas(), assetAddress, 0x1c, 0x24, 0, 0x20)))` · `market/WildcatMarketBase.sol:261-263` · `totalAssets()` reverts unless the asset's `balanceOf` returns exactly one word, so liquidity math never reads a malformed balance.

#### G-18
`if (!IWildcatSanctionsSentinel(sentinel).isSanctioned(borrower, accountAddress)) { revert_BadLaunchCode(); }` · `market/WildcatMarketConfig.sol:82` · The permissionless `nukeFromOrbit` blocks only accounts the sentinel reports sanctioned for this borrower.

#### G-19
`if (IWildcatSanctionsSentinel(sentinel).isSanctioned(borrower, accountAddress)) { revert_NotReversedOrStunning(); }` · `market/WildcatMarketConfig.sol:96` · The permissionless `stunningReversal` unblocks only accounts no longer reported sanctioned.

#### G-20
`if (account.approval != AuthRole.Blocked) { revert_AccountNotBlocked(); }` · `market/WildcatMarketConfig.sol:101` · Reversal applies only to Blocked accounts, so it cannot promote a Null account directly.

#### G-21
`if (state.liquidityRequired() > totalAssets()) { revert_InsufficientReservesForOldLiquidityRatio(); }` · `market/WildcatMarketConfig.sol:184` · A reserve-ratio decrease is refused while the market is under its current requirement.

#### G-22
`if (state.liquidityRequired() > totalAssets()) { revert_InsufficientReservesForNewLiquidityRatio(); }` · `market/WildcatMarketConfig.sol:190` · A reserve-ratio increase is refused when it would make the market delinquent immediately.

#### G-23
`if (scaledAmount == 0) { revert_NullTransferAmount(); }` · `market/WildcatMarketToken.sol:75` · Transfers that round to zero scaled units are refused.

#### G-24
`uint256 newAllowance = allowed - amount;` · `market/WildcatMarketToken.sol:57` · Checked subtraction: `transferFrom` cannot exceed a finite allowance.

#### G-25
`fromAccount.scaledBalance -= scaledAmount;` · `market/WildcatMarketToken.sol:80` · Checked subtraction: a sender cannot move more scaled balance than it holds (feeds I-1).

#### G-26
`if (scaledAmount == 0) { revert_NullBurnAmount(); }` · `market/WildcatMarketWithdrawals.sol:86` · Withdrawal requests that round to zero scaled units are refused.

#### G-27
`account.scaledBalance -= scaledAmount;` · `market/WildcatMarketWithdrawals.sol:97` · Checked subtraction: a lender cannot queue more than its balance (feeds I-1).

#### G-28
`if (expiry >= block.timestamp) { revert_WithdrawalBatchNotExpired(); }` · `market/WildcatMarketWithdrawals.sol:182` · Execution waits for batch expiry, matching the strict `timestamp > expiry` test in `hasPendingExpiredBatch`.

#### G-29
`if (normalizedAmountWithdrawn == 0) { revert_NullWithdrawalAmount(); }` · `market/WildcatMarketWithdrawals.sol:197` · An execution must pay something new, so a lender's share cannot be claimed twice.

#### G-30
`state.normalizedUnclaimedWithdrawals -= normalizedAmountWithdrawn;` · `market/WildcatMarketWithdrawals.sol:202` · Checked subtraction: executions cannot pay out more than has been reserved for batches (feeds I-4).

#### G-31
`if (state.isClosed) { revert_RepayToClosedMarket(); }` · `market/WildcatMarketWithdrawals.sol:237` · `repayAndProcessUnpaidWithdrawalBatches` follows the closed-market repayment boundary.

#### G-32
`uint256 availableLiquidity = totalAssets() - (state.normalizedUnclaimedWithdrawals + state.accruedProtocolFees);` · `market/WildcatMarketWithdrawals.sol:242-243` · Checked subtraction: unpaid batches are paid only from assets beyond unclaimed withdrawals and fees; the call reverts when assets are below that sum.

#### G-33
`if (arr.startIndex == arr.nextIndex) { revert FIFOQueueOutOfBounds(); }` · `libraries/FIFOQueue.sol:24` · `first()` on an empty unpaid-batch queue reverts; `shift()` repeats the check at `:63`.

#### G-34
`if (_reentrancyGuard != _NOT_ENTERED) { revert NoReentrantCalls(); }` · `ReentrancyGuard.sol:83` · One guard slot covers every `nonReentrant` market function and every `nonReentrantView` getter, so token callbacks cannot re-enter those functions or read those getters mid-update. `totalAssets()`, `previousState()`, `withdrawableProtocolFees()`, `maxTotalSupply()`, `annualInterestBips()`, `reserveRatioBips()` and `allowance` carry no guard.

#### G-35
`if (msg.sender != borrower) { revert CallerNotBorrower(); }` · `WildcatMarketController.sol:118` · The controller's lender and market-management functions belong to its immutable borrower.

#### G-36
`if (!_controlledMarkets.contains(market)) { revert NotControlledMarket(); }` · `WildcatMarketController.sol:125` · A controller acts only on markets it deployed; the same check repeats inline at `:254`, `:288` and `:329`.

#### G-37
`if (msg.sender == borrower) { if (!IWildcatArchController(_archController).isRegisteredBorrower(msg.sender)) { revert NotRegisteredBorrower(); } } else if (msg.sender != address(controllerFactory)) { revert CallerNotBorrowerOrControllerFactory(); }` · `WildcatMarketController.sol:458-464` · New markets need a borrower still registered in the arch controller, or the factory acting within `deployControllerAndMarket`.

#### G-38
`if (IWildcatArchController(_archController).isBlacklistedAsset(asset)) { revert UnderlyingNotPermitted(); }` · `WildcatMarketController.sol:466` · The owner's asset blacklist applies at deployment only.

#### G-39
`if or(lt(value, min), gt(value, max)) { mstore(0, errorSelector) revert(0, 4) }` · `WildcatMarketController.sol:782` · Via `enforceParameterConstraints` (`:583-612`), each new market's APR, delinquency fee, batch duration, reserve ratio and grace period must lie within the controller's immutable bounds.

#### G-40
`if (market.code.length != 0) { revert MarketAlreadyDeployed(); }` · `WildcatMarketController.sol:511` · One market per `(asset, namePrefix, symbolPrefix)` salt per controller.

#### G-41
`if (WildcatMarket(market).isClosed()) { revertWithSelector(MarketAlreadyClosed.selector); }` · `WildcatMarketController.sol:626` · Closure runs once.

#### G-42
`if (WildcatMarket(market).isClosed()) { revertWithSelector(CapacityChangeOnClosedMarket.selector); }` · `WildcatMarketController.sol:641` · Capacity is frozen after closure.

#### G-43
`if (WildcatMarket(market).isClosed()) { revertWithSelector(AprChangeOnClosedMarket.selector); }` · `WildcatMarketController.sol:690` · The zero APR written at closure cannot be raised again.

#### G-44
`assertValueInRange(annualInterestBips, MinimumAnnualInterestBips, MaximumAnnualInterestBips, AnnualInterestBipsOutOfBounds.selector);` · `WildcatMarketController.sol:694-699` · Borrower APR changes stay within the controller's bounds (feeds I-6).

#### G-45
`if (tmp.expiry == 0) { revertWithSelector(AprChangeNotPending.selector); }` · `WildcatMarketController.sol:763` · `resetReserveRatio` needs an active temporary ratio; markets this controller never recorded always fail here.

#### G-46
`if (block.timestamp < tmp.expiry) { revertWithSelector(ExcessReserveRatioStillActive.selector); }` · `WildcatMarketController.sol:766` · The raised reserve ratio after an APR cut holds until its expiry.

#### G-47
`if (constraints.minimumAnnualInterestBips > constraints.maximumAnnualInterestBips || constraints.maximumAnnualInterestBips > 10000 || constraints.minimumDelinquencyFeeBips > constraints.maximumDelinquencyFeeBips || constraints.maximumDelinquencyFeeBips > 10000 || constraints.minimumReserveRatioBips > constraints.maximumReserveRatioBips || constraints.maximumReserveRatioBips > 10000 || constraints.minimumDelinquencyGracePeriod > constraints.maximumDelinquencyGracePeriod || constraints.minimumWithdrawalBatchDuration > constraints.maximumWithdrawalBatchDuration) { revert InvalidConstraints(); }` · `WildcatMarketControllerFactory.sol:75-86` · Fixes consistent, at-most-100% bounds for every controller this factory deploys.

#### G-48
`if (msg.sender != IWildcatArchController(_archController).owner()) { revert CallerNotArchControllerOwner(); }` · `WildcatMarketControllerFactory.sol:128` · Fee configuration follows the arch controller's current owner.

#### G-49
`if ((protocolFeeBips > 0 && nullFeeRecipient) || (hasOriginationFee && nullFeeRecipient) || (hasOriginationFee && nullOriginationFeeAsset) || protocolFeeBips > 10000) { revert InvalidProtocolFeeConfiguration(); }` · `WildcatMarketControllerFactory.sol:221-228` · Fees always have a recipient, origination fees an asset, and the protocol fee is at most 100% of interest.

#### G-50
`if (!IWildcatArchController(_archController).isRegisteredBorrower(msg.sender)) { revert NotRegisteredBorrower(); }` · `WildcatMarketControllerFactory.sol:353` · Only registered borrowers get a controller.

#### G-51
`if (controller.code.length != 0) { revert ControllerAlreadyDeployed(); }` · `WildcatMarketControllerFactory.sol:368` · One controller per borrower per factory (salt is the borrower).

#### G-52
`if (!set.contains(account)) {` · `WildcatArchController.sol:126` · Engine updates reach only contracts still registered in the named set.

#### G-53
`if (!_borrowers.add(borrower)) { revert BorrowerAlreadyExists(); }` · `WildcatArchController.sol:158` · Registry adds are idempotence-checked.

#### G-54
`if (!_borrowers.remove(borrower)) { revert BorrowerDoesNotExist(); }` · `WildcatArchController.sol:165` · Registry removals must name a member.

#### G-55
`if (!_assetBlacklist.add(asset)) { revert AssetAlreadyBlacklisted(); }` · `WildcatArchController.sol:201` · Blacklist adds are idempotence-checked.

#### G-56
`if (!_assetBlacklist.remove(asset)) { revert AssetNotBlacklisted(); }` · `WildcatArchController.sol:208` · Blacklist removals must name a member.

#### G-57
`if (!_controllerFactories.add(factory)) { revert ControllerFactoryAlreadyExists(); }` · `WildcatArchController.sol:246` · Factory registration is idempotence-checked.

#### G-58
`if (!_controllerFactories.remove(factory)) { revert ControllerFactoryDoesNotExist(); }` · `WildcatArchController.sol:254` · Factory removal must name a member.

#### G-59
`if (!_controllerFactories.contains(msg.sender)) { revert NotControllerFactory(); }` · `WildcatArchController.sol:290` · Only registered factories register controllers.

#### G-60
`if (!_controllers.add(controller)) { revert ControllerAlreadyExists(); }` · `WildcatArchController.sol:297` · Controller registration is idempotence-checked.

#### G-61
`if (!_controllers.remove(controller)) { revert ControllerDoesNotExist(); }` · `WildcatArchController.sol:305` · Controller removal must name a member.

#### G-62
`if (!_controllers.contains(msg.sender)) { revert NotController(); }` · `WildcatArchController.sol:341` · Only registered controllers register markets.

#### G-63
`if (!_markets.add(market)) { revert MarketAlreadyExists(); }` · `WildcatArchController.sol:348` · Market registration is idempotence-checked.

#### G-64
`if (!_markets.remove(market)) { revert MarketDoesNotExist(); }` · `WildcatArchController.sol:356` · Market removal must name a member.

#### G-65
`if iszero(eq(caller(), sload(not(_OWNER_SLOT_NOT)))) {` · `lib/solady/src/auth/Ownable.sol:117` · `onlyOwner` for the arch controller's blacklist actions, borrower registration and removal, factory registration and removal, controller and market removal, `transferOwnership`, `renounceOwnership` and `completeOwnershipHandover`. `registerController` is factory-only, `registerMarket` is controller-only, and `requestOwnershipHandover` and `cancelOwnershipHandover` take any caller.

#### G-66
`if iszero(shl(96, newOwner)) {` · `lib/solady/src/auth/Ownable.sol:139` · `transferOwnership` refuses the zero address; `renounceOwnership` is the explicit path to it.

#### G-67
`if gt(timestamp(), sload(handoverSlot)) {` · `lib/solady/src/auth/Ownable.sol:192` · A handover completes only while the pending owner's request is unexpired (48 hours from `requestOwnershipHandover`).

#### G-68
`if (msg.sender != sphereXAdmin()) { revert_SphereXAdminRequired(); }` · `spherex/SphereXConfig.sol:59` · SphereX admin controls the operator and its own transfer.

#### G-69
`if (msg.sender != sphereXOperator()) { revert_SphereXOperatorRequired(); }` · `spherex/SphereXConfig.sol:66` · Only the operator sets the arch controller's engine.

#### G-70
`if (msg.sender != sphereXOperator() && msg.sender != sphereXAdmin()) { revert_SphereXOperatorOrAdminRequired(); }` · `spherex/SphereXConfig.sol:73` · Operator or admin may push the engine to registered contracts.

#### G-71
`if (msg.sender != pendingSphereXAdmin()) { revert_SphereXNotPendingAdmin(); }` · `spherex/SphereXConfig.sol:121` · Two-step SphereX admin transfer.

#### G-72
`if (newSphereXEngine != address(0) && !ISphereXEngine(newSphereXEngine).supportsInterface(type(ISphereXEngine).interfaceId)) { revert_SphereXNotEngine(); }` · `spherex/SphereXConfig.sol:154-159` · The arch controller's engine is interface-checked; registered contracts do not repeat the check (`SphereXProtectedRegisteredBase.sol:109-111`).

#### G-73
`if (msg.sender != _archController) { revert_SphereXOperatorRequired(); }` · `spherex/SphereXProtectedRegisteredBase.sol:66` · Only the immutable arch controller changes a market's, controller's or factory's engine.

#### G-74
`if iszero(and(eq(mload(0), 0x20), call(gas(), engineAddress, 0, add(pointer, 28), size, 0, 0x40))) {` · `spherex/SphereXProtectedRegisteredBase.sol:172-177` · When an engine is set, `sphereXValidatePre` runs before every `sphereXGuardExternal` body and its revert aborts the call.

#### G-75
`if iszero(call(gas(), sphereXEngineAddress, 0, add(slotBefore, 28), calldataSize, 0, 0)) {` · `spherex/SphereXProtectedRegisteredBase.sol:266` · `sphereXValidatePost` runs after the body with before/after storage values and can revert it.

#### G-76
`if (!canReleaseEscrow()) revert CanNotReleaseEscrow();` · `WildcatSanctionsEscrow.sol:35` · Escrowed value leaves only once the sentinel no longer reports the account sanctioned for the escrow's borrower.

#### G-77
`require(factories.length == 1, 'should only have one factory');` · `lens/MarketLens.sol:16` · The lens pins exactly one factory at construction (see X-12).

#### G-78
`if iszero(deployment) { mstore(0x00, 0x30116425) revert(0x1c, 0x04) }` · `libraries/LibStoredInitCode.sol:118-121` · A failed create2 reverts, so the precomputed addresses registered by the factory and controller always hold code (see X-11).

---

## 2. Inferred Invariants (Single-Contract)

Inferred invariants are derived from structural analysis of the source code. Each block below cites one of five extraction methods in its `Derivation` field:

- **Δ-pair (delta-pair) analysis**: two or more storage variables in the same function body that change by equal-and-opposite amounts, implying a conservation law.
- **Guard lift**: a `require` / `if-revert` on a storage variable, promoted to a global property after checking every write site of that variable. Any unguarded write site makes the lifted invariant On-chain=**No**.
- **State-machine edge**: a storage variable that moves through discrete values with no reverse path.
- **Temporal predicate**: a check tied to `block.timestamp` or a stored deadline.
- **NatSpec-stated global property**: a developer-asserted property, then confirmed or contradicted by the structural scan.

Categories: `Conservation` · `Bound` · `Ratio` · `StateMachine` · `Temporal`. Definitions at the end of this section. Each market holds its own `MarketState _state`; market blocks hold per market.

---

#### I-1

`Conservation` · On-chain: **Yes**

> `_state.scaledTotalSupply == Σ_a _accounts[a].scaledBalance + _state.scaledPendingWithdrawals`

**Derivation**: Δ-pair: `market/WildcatMarket.sol:71` ↔ `market/WildcatMarket.sol:78` (deposit, +s/+s); `market/WildcatMarketWithdrawals.sol:97` ↔ `market/WildcatMarketWithdrawals.sol:116` (queue, −s balance/+s pending); `market/WildcatMarketBase.sol:622` ↔ `market/WildcatMarketBase.sol:628` (batch payment, −b pending/−b supply); `market/WildcatMarketToken.sol:80` ↔ `market/WildcatMarketToken.sol:84` (transfer); `market/WildcatMarketBase.sol:165` ↔ `market/WildcatMarketBase.sol:172` (block moves balance to escrow). Write-site enumeration: `scaledBalance` is written only at those five pairs; `scaledTotalSupply` only at `:78` and `:628`; `scaledPendingWithdrawals` only at `:116` and `:622` (`:653`/`:659` are in the `pure` view helper).

**If violated**: normalized `totalSupply()` would disagree with holder balances plus queued amounts, and `liquidityRequired` would price reserves on the wrong base.

---

#### I-2

`Conservation` · On-chain: **Yes**

> `_state.scaledPendingWithdrawals == Σ_e (batches[e].scaledTotalAmount − batches[e].scaledAmountBurned)` over the pending batch and every unpaid batch.

**Derivation**: Δ-pair: `market/WildcatMarketWithdrawals.sol:115` ↔ `market/WildcatMarketWithdrawals.sol:116` (queue); `market/WildcatMarketBase.sol:620` ↔ `market/WildcatMarketBase.sol:622` (payment). Batches are persisted after each payment at `market/WildcatMarketBase.sol:471`, `:597`, `market/WildcatMarketWithdrawals.sol:127` and `:278`; state is persisted by `_writeState` in the same call.

**If violated**: `availableLiquidityForPendingBatch` (`libraries/Withdrawal.sol:54`) would reserve the wrong amount for earlier batches.

---

#### I-3

`Conservation` · On-chain: **Yes**

> For every expiry `e`: `Σ_a accountStatuses[e][a].scaledAmount == batches[e].scaledTotalAmount`.

**Derivation**: Δ-pair: `market/WildcatMarketWithdrawals.sol:114` ↔ `market/WildcatMarketWithdrawals.sol:115`; these are the only writers of either field.

**If violated**: pro-rata execution (I-21) would promise more or less than the batch was paid.

---

#### I-4

`Conservation` · On-chain: **Yes**

> `_state.normalizedUnclaimedWithdrawals == Σ_e batches[e].normalizedAmountPaid − Σ_{e,a} accountStatuses[e][a].normalizedAmountWithdrawn`

**Derivation**: Δ-pair: `market/WildcatMarketBase.sol:621` ↔ `market/WildcatMarketBase.sol:625` (+paid on both); `market/WildcatMarketWithdrawals.sol:201` ↔ `market/WildcatMarketWithdrawals.sol:202` (status advanced by the delta computed at `:195`, unclaimed reduced by the same delta; checked, G-30). No other writer of the three fields.

**If violated**: `liquidityRequired`, `totalDebts` and fee withdrawal (I-22) would reserve the wrong amount for paid batches.

---

#### I-5

`Bound` · On-chain: **Yes**

> For every `(e, a)`: `accountStatuses[e][a].normalizedAmountWithdrawn ≤ ⌊batches[e].normalizedAmountPaid × accountStatuses[e][a].scaledAmount / batches[e].scaledTotalAmount⌋`

**Derivation**: guard-lift: `uint128 normalizedAmountWithdrawn = newTotalWithdrawn - status.normalizedAmountWithdrawn;` (checked, `market/WildcatMarketWithdrawals.sol:195`) + write sites: the field's only writer is `market/WildcatMarketWithdrawals.sol:201` (sets it to `newTotalWithdrawn`); `normalizedAmountPaid` only increases (`market/WildcatMarketBase.sol:621`) and `scaledAmount` changes only before expiry (`:114`).

**If violated**: an account could execute the same share twice.

---

#### I-6

`Bound` · On-chain: **No**

> `annualInterestBips ∈ [MinimumAnnualInterestBips, MaximumAnnualInterestBips]` of the market's controller.

**Derivation**: guard-lift: `if or(lt(value, min), gt(value, max))` (G-39, applied at `WildcatMarketController.sol:583-588`) and G-44 (`WildcatMarketController.sol:694-699`) + write sites: `market/WildcatMarketBase.sol:103` (constructor, bounded at deploy), `market/WildcatMarketConfig.sol:161` (reachable only from `WildcatMarketController.sol:758`, bounded), `market/WildcatMarket.sol:224` (**unguarded**: `closeMarket` writes 0).

**If violated**: a closed market reports an APR below the controller minimum; open markets stay within bounds.

---

#### I-7

`Bound` · On-chain: **Yes**

> `reserveRatioBips ≤ 10000`

**Derivation**: guard-lift: `constraints.maximumReserveRatioBips > 10000` refused (G-47, `WildcatMarketControllerFactory.sol:81`) + write sites: `market/WildcatMarketBase.sol:104` (constructor, bounded by G-39); `market/WildcatMarketConfig.sol:188` reached from `WildcatMarketController.sol:749` (value `max(min(10000, doubleRelativeDiff), originalReserveRatioBips)`, `:666-668`; NatSpec `:648-653` states the 100% cap), `:755` and `:771` (restore a recorded original); `market/WildcatMarket.sol:226` (exactly 10000).

**If violated**: `bipMul` in `liquidityRequired` would require more than 100% of outstanding supply.

---

#### I-8

`Bound` · On-chain: **No**

> `reserveRatioBips ∈ [MinimumReserveRatioBips, MaximumReserveRatioBips]` of the market's controller.

**Derivation**: guard-lift: G-39 at deploy (`WildcatMarketController.sol:601-606`) + write sites: `WildcatMarketController.sol:749` (**unguarded against the maximum**: the temporary ratio can reach 10000), `market/WildcatMarket.sol:226` (**unguarded**: 10000 at closure); `:755`/`:771` restore a bounded original.

**If violated**: during a temporary ratio or after closure the ratio exceeds the controller's configured maximum; the effect is a higher reserve requirement.

---

#### I-9

`Bound` · On-chain: **No**

> Normalized `totalSupply() ≤ maxTotalSupply`.

**Derivation**: guard-lift: `amount = MathUtils.min(amount, state.maximumDeposit());` (`market/WildcatMarket.sol:57`; `maximumDeposit = maxTotalSupply.satSub(totalSupply)`, `libraries/MarketState.sol:59-61`) + write sites: `maxTotalSupply` at `market/WildcatMarketBase.sol:95` and `market/WildcatMarketConfig.sol:148` (**no comparison with supply**); supply grows through `libraries/FeeMath.sol:171` with no cap. NatSpec: `market/WildcatMarketConfig.sol:140-141`: "this only limits deposits and does not affect interest accrual".

**If violated**: by design, only new deposits are capped; `maximumDeposit` saturates to zero.

---

#### I-10

`StateMachine` · On-chain: **Yes**

> `isClosed` is a one-shot latch.

**Derivation**: edge: `false@market/WildcatMarketBase.sol:94 → true@market/WildcatMarket.sol:225`; `:225` is the only assignment (write-site grep), and the controller refuses a second closure (G-41).

**If violated**: closed-market guards (G-1, G-7, G-10, G-11, G-31, G-42, G-43) would lose their meaning.

---

#### I-11

`StateMachine` · On-chain: **Yes**

> An account leaves `Blocked` only to `WithdrawOnly`, and only when the sentinel no longer reports it sanctioned.

**Derivation**: edge: `Blocked@market/WildcatMarketBase.sol:161 → WithdrawOnly@market/WildcatMarketConfig.sol:105` (after G-19, G-20). Every other role writer loads the account through `_getAccount`, which reverts on `Blocked` (G-15): `market/WildcatMarketConfig.sol:127-133`, `market/WildcatMarketBase.sol:198-203`, `market/WildcatMarketToken.sol:79-85`.

**If violated**: a blocked account could regain deposit rights or receive transfers without reversal.

---

#### I-12

`StateMachine` · On-chain: **No**

> An account holds `WithdrawOnly` only after having held `DepositAndWithdraw`.

**Derivation**: NatSpec: `market/WildcatMarketConfig.sol:116-120`: "Requires that the lender *had* full access (i.e. they were previously authorized) before dropping them down to WithdrawOnly, else arbitrary accounts could grant themselves Withdraw." Structural scan: `WithdrawOnly` writers are `market/WildcatMarketConfig.sol:131` (from `DepositAndWithdraw`) and **`market/WildcatMarketConfig.sol:105` (from `Blocked`)**. `Blocked` is entered from any non-Blocked role, including `Null`, at `market/WildcatMarketBase.sol:157-161` via `market/WildcatMarket.sol:48-49` (no role check on the sanctioned branch), `market/WildcatMarketConfig.sol:86` and `market/WildcatMarketWithdrawals.sol:205`.

**If violated**: an account never authorised by the borrower reaches `WithdrawOnly` through a sanction and a later reversal or borrower override.

---

#### I-13

`StateMachine` · On-chain: **Yes**

> At most one pending withdrawal batch exists; `pendingWithdrawalExpiry` cycles `0 → expiry → 0`.

**Derivation**: edge: `0@market/WildcatMarketWithdrawals.sol:105 → block.timestamp + withdrawalBatchDuration@market/WildcatMarketWithdrawals.sol:106-108 → 0@market/WildcatMarketBase.sol:595` (after expiry, in `_processExpiredWithdrawalBatch`). No other writer (`:518` is in the view path).

**If violated**: two batches would compete for the same reservation in `availableLiquidityForPendingBatch`.

---

#### I-14

`StateMachine` · On-chain: **Yes**

> An expired batch joins `unpaidBatches` only while `scaledAmountBurned < scaledTotalAmount`, and leaves it, oldest first, only once fully paid.

**Derivation**: edge: `expired@market/WildcatMarketBase.sol:589-590 (push) → paid@market/WildcatMarketWithdrawals.sol:281-282 (shift)`; `libraries/FIFOQueue.sol:55-68` are the only queue writers used (`shiftN` at `:70` has no caller in `src/`).

**If violated**: `closeMarket` (G-12) could proceed with an unpaid batch, or a paid batch could keep consuming liquidity.

---

#### I-15

`Temporal` · On-chain: **Yes**

> A batch's withdrawals execute only after its expiry, and a batch is treated as expired only strictly after it.

**Derivation**: temporal: `if (expiry >= block.timestamp) { revert_WithdrawalBatchNotExpired(); }` (`market/WildcatMarketWithdrawals.sol:182`) and `result := and(gt(expiry, 0), gt(timestamp(), expiry))` (`libraries/MarketState.sol:134`).

**If violated**: execution could read a batch before its final payment at expiry.

---

#### I-16

`Temporal` · On-chain: **Yes**

> `lastInterestAccruedTimestamp` never decreases; an expired batch is accrued to its expiry before accrual to `block.timestamp`.

**Derivation**: temporal: `if (expiry != lastInterestAccruedTimestamp)` (`market/WildcatMarketBase.sol:422`) then `if (block.timestamp != lastInterestAccruedTimestamp)` (`:443`); both accrual paths compute `timestamp - state.lastInterestAccruedTimestamp` with checked subtraction (`libraries/FeeMath.sol:36`, `:64`); sole writer `libraries/FeeMath.sol:172`.

**If violated**: the batch would be priced at a scale factor that includes interest past its expiry.

---

#### I-17

`Temporal` · On-chain: **Yes**

> The delinquency penalty for an interval uses the `isDelinquent` flag stored at the start of that interval.

**Derivation**: temporal: `if (state.isDelinquent)` (`libraries/FeeMath.sol:97`) reads the flag that only `_writeState` writes (`market/WildcatMarketBase.sol:553-554`) at the end of the previous state-writing call; `timeDelinquent` writers: `libraries/FeeMath.sol:100`, `:115`, `market/WildcatMarket.sol:229` (reset to 0 at closure).

**If violated**: penalties would follow the post-interval state rather than the state that held during it.

---

#### I-18

`Ratio` · On-chain: **Yes**

> `liquidityRequired = normalize(bipMul(scaledTotalSupply − scaledPendingWithdrawals, reserveRatioBips) + scaledPendingWithdrawals) + accruedProtocolFees + normalizedUnclaimedWithdrawals`, and `isDelinquent = liquidityRequired > totalAssets()` is snapshotted after every in-call edit and transfer.

**Derivation**: guard-lift: formula at `libraries/MarketState.sol:87-98`; snapshot at `market/WildcatMarketBase.sol:553` inside `_writeState`, which every state-changing market path calls last (after `safeTransfer`/`safeTransferFrom` in `borrow`, `collectFees`, `closeMarket`, deposits and executions). Inputs' write sites are enumerated in I-1, I-2, I-4 and I-7.

**If violated**: the delinquency flag feeding I-17 would describe a state other than the stored one.

---

#### I-19

`Ratio` · On-chain: **Yes**

> Per accrual interval, `protocolFee = scaledTotalSupply.rayMul(scaleFactor.rayMul(protocolFeeBips.bipMul(baseInterestRay)))` using the scale factor from before that interval's update.

**Derivation**: guard-lift: formula at `libraries/FeeMath.sol:46-50`, executed before the scale-factor write at `:168-171`; `accruedProtocolFees` write sites: `libraries/FeeMath.sol:50` (+) and `market/WildcatMarket.sol:130` (−, bounded by I-22).

**If violated**: fees would be charged on interest already folded into the scale factor.

---

#### I-20

`Ratio` · On-chain: **Yes**

> `scaleFactor' = scaleFactor + scaleFactor.rayMul(baseInterestRay + delinquencyFeeRay)`; the scale factor starts at `RAY` and never decreases.

**Derivation**: guard-lift: sole writer `libraries/FeeMath.sol:171` (unsigned delta from `:169`), initial value `market/WildcatMarketBase.sol:105`.

**If violated**: normalized balances could shrink between updates.

---

#### I-21

`Ratio` · On-chain: **Yes**

> `newTotalWithdrawn = ⌊normalizedAmountPaid × scaledAmount / scaledTotalAmount⌋`, read from the stored batch after `_getUpdatedState` has persisted this call's payments.

**Derivation**: guard-lift: formula at `market/WildcatMarketWithdrawals.sol:191-193` (`MathUtils.mulDiv` floors, `libraries/MathUtils.sol:173-184`); ordering: `_getUpdatedState` (`:151`, `:167`) writes the batch at `market/WildcatMarketBase.sol:471` / `:597` before `_executeWithdrawal` reads it at `:186`.

**If violated**: execution would pay from a stale batch or round in the lender's favour.

---

#### I-22

`Bound` · On-chain: **Yes**

> Protocol fees are never paid out of paid-but-unclaimed withdrawal assets: `withdrawableFees = min(totalAssets − normalizedUnclaimedWithdrawals, accruedProtocolFees)`.

**Derivation**: guard-lift: `uint256 totalAvailableAssets = totalAssets - state.normalizedUnclaimedWithdrawals;` (checked) and `min(..., state.accruedProtocolFees)` (`libraries/MarketState.sol:109-110`) + write sites of `accruedProtocolFees`: `libraries/FeeMath.sol:50`, `market/WildcatMarket.sol:130` (only after this bound).

**If violated**: `collectFees` could spend assets reserved for executed batches.

---

#### I-23

`Bound` · On-chain: **Yes**

> A batch payment never exceeds that batch's owed amount nor the assets left after unclaimed withdrawals and accrued fees.

**Derivation**: guard-lift: `scaledAmountBurned = MathUtils.min(scaledAvailableLiquidity, scaledAmountOwed).toUint104();` (`market/WildcatMarketBase.sol:617`) + every caller's `availableLiquidity`: `libraries/Withdrawal.sol:54-58` (pending or expiring batch, used at `market/WildcatMarketBase.sol:468`, `:576`, `market/WildcatMarketWithdrawals.sol:121`; also reserves every other batch's owed amount) and `market/WildcatMarketWithdrawals.sol:242-243` (unpaid batches; does **not** reserve the pending batch, so older batches take priority).

**If violated**: burned supply would exceed what the batch asked for, or a payment would draw on reserved assets.

---

#### I-24

`Bound` · On-chain: **Yes**

> `unpaidBatches.startIndex ≤ unpaidBatches.nextIndex`

**Derivation**: guard-lift: `if (startIndex == arr.nextIndex) { revert FIFOQueueOutOfBounds(); }` (`libraries/FIFOQueue.sol:63`) + write sites: `push` increments `nextIndex` (`:58`), `shift` increments `startIndex` after the check (`:67`); `shiftN` (`:72`) is unused.

**If violated**: `length()` (`:39`) would underflow and `closeMarket`'s G-12 check would misread the queue.

---

#### I-25

`StateMachine` · On-chain: **Yes**

> A controller's `_controlledMarkets` only grows; membership is a one-shot latch per market.

**Derivation**: edge: `absent → member@WildcatMarketController.sol:517`; no `remove` call on the set exists in `src/`.

**If violated**: `onlyControlledMarket` (G-36) would stop covering a market the controller deployed.

---

#### I-26

`Temporal` · On-chain: **Yes**

> A temporary excess reserve ratio can be reset only at or after its stored expiry; activation and deeper cuts set that expiry to `block.timestamp + 2 weeks`, while an update whose rate is at or above the market's current rate keeps the previous expiry.

**Derivation**: temporal: `if (block.timestamp < tmp.expiry)` (`WildcatMarketController.sol:766`); expiry writes: `uint32 expiry = uint32(block.timestamp + 2 weeks);` (`:722`), `expiry = tmp.expiry;` (`:737-739`), stored at `:747-748`.

**If violated**: the borrower could cut the APR without the reserve requirement staying raised for the stated window.

---

#### I-27

`StateMachine` · On-chain: **Yes**

> `temporaryExcessReserveRatio[market]` cycles `none → active → none`; the original APR and ratio are recorded only on activation and reused while active.

**Derivation**: edge: `expiry 0@WildcatMarketController.sol:707 → nonzero@:747-748 → 0@:754 (cancel) or @:772 (reset)`; originals written only at `:732-733`.

**If violated**: a later cut would compute its temporary ratio from an already-reduced APR.

---

#### I-28

`StateMachine` · On-chain: **Yes**

> One controller per borrower per factory, and one market per `(asset, namePrefix, symbolPrefix)` per controller.

**Derivation**: edge: `no code → code@WildcatMarketControllerFactory.sol:371` guarded by G-51 (salt = borrower, `:361`); `no code → code@WildcatMarketController.sol:514` guarded by G-40 (salt from `_deriveSalt`, `:543-559`).

**If violated**: registry and lens lookups by computed address (`computeControllerAddress`, `computeMarketAddress`) would be ambiguous.

---

#### I-29

`StateMachine` · On-chain: **Yes**

> Transient deployment parameters return to placeholder values within the deploying call.

**Derivation**: edge: `_tmpMarketBorrowerParameter: address(1) → msg.sender@WildcatMarketControllerFactory.sol:358 → address(1)@:373`; `_tmpMarketParameters: placeholders → parameters@WildcatMarketController.sol:503 → placeholders@:519 (:411-423)`; `tmpEscrowParams: (1,1,1) → (borrower, account, asset)@WildcatSanctionsSentinel.sol:131 → (1,1,1)@:141`.

**If violated**: a later constructor could read the previous deployment's parameters (see X-4, X-5, X-6).

---

#### I-30

`Bound` · On-chain: **Yes**

> `_protocolFeeConfiguration.protocolFeeBips ≤ 10000`, and any nonzero fee has a nonzero recipient (and origination asset).

**Derivation**: guard-lift: G-49 (`WildcatMarketControllerFactory.sol:221-228`) + write sites: the only writer is `:229`.

**If violated**: new markets could charge more than 100% of interest as protocol fee or send fees to `address(0)`.

---

#### I-31

`StateMachine` · On-chain: **Yes**

> A market enters the arch registry only through a controller registered at that moment, and a controller only through a registered factory; removals are owner-only and do not reach deployed contracts.

**Derivation**: edge: `absent → member@WildcatArchController.sol:348` behind G-62 (`:341`); `absent → member@:297` behind G-59 (`:290`); removals at `:305`, `:356` behind `onlyOwner` (G-65).

**If violated**: the registry would list contracts no registered deployer produced.

---

#### I-32

`Bound` · On-chain: **Yes**

> The SphereX operator of every registered contract is the immutable arch controller.

**Derivation**: NatSpec: `spherex/SphereXProtectedRegisteredBase.sol:15-16`: "In this version, the WildcatArchController deployment is the SphereX operator. There is no admin because the arch controller address can not be modified." Structural scan: `_archController` is `immutable` (`:36`), assigned in constructors (`market/WildcatMarketBase.sol:117`, `WildcatMarketController.sol:95`, `WildcatMarketControllerFactory.sol:73`); `sphereXOperator()` returns it (`:94-96`).

**If violated**: another address could swap a market's engine.

---

#### I-33

`Bound` · On-chain: **No**

> Every escrow created by the sentinel stays sanction-overridden for its borrower.

**Derivation**: NatSpec: `WildcatSanctionsSentinel.sol:118-119`: "The escrow contract is added to the set of sanction override addresses for `borrower` so that it can not be blocked." Structural scan of `sanctionOverrides` writes: `:137` (true, escrow), `:97` (true, `msg.sender` row), **`:105` (false, `msg.sender` row: the borrower can clear its own escrow's override)**.

**If violated**: an escrow address that the Chainalysis list flags would become blockable in that borrower's markets.

---

#### I-34

`Bound` · On-chain: **Yes**

> A caller can write sanction overrides only in its own `msg.sender` row, except that `createEscrow` writes `[borrower][escrow]` where `escrow` is the create2 address of `(borrower, account, asset)`.

**Derivation**: guard-lift: write sites `WildcatSanctionsSentinel.sol:97`, `:105` (key `msg.sender`) and `:137` (key `borrower`, value address from `getEscrowAddress`, `:126`, `:148-174`).

**If violated**: a third party could whitelist an arbitrary address for another borrower.

---

#### I-35

`Bound` · On-chain: **Yes**

> An escrow's `borrower`, `account` and `asset` never change, and a release always sends the whole balance to `account`.

**Derivation**: guard-lift: G-76 (`WildcatSanctionsEscrow.sol:35`) + write sites: immutables assigned only in the constructor (`:17-20`); `releaseEscrow` transfers `balance()` to `account` (`:37-41`).

**If violated**: escrowed value could reach an address other than the blocked account.

---

**Categories:**
- **Conservation**: two or more storage variables change by equal-and-opposite amounts in the same function body.
- **Bound**: a guard on a storage variable, lifted to a global property and checked at every write site; On-chain=**No** if any write site lacks it.
- **Ratio**: a storage variable defined as a formula of other storage variables, with snapshot ordering noted.
- **StateMachine**: a variable moving through discrete values with guards preventing reversal.
- **Temporal**: a condition on `block.timestamp` or a stored deadline.

---

## 3. Inferred Invariants (Cross-Contract)

Trust assumptions that span contract boundaries. Each block cites both caller-side and callee-side code, both inside scope.

---

#### X-1

On-chain: **No**

> The market's stored lender role matches the controller's current lender set.

**Caller side**: `market/WildcatMarketBase.sol:200-207`: the market queries `isAuthorizedLender` only while the stored role is `Null`; a stored `DepositAndWithdraw` is used without re-query.

**Callee side**: `WildcatMarketController.sol:308-317` (`deauthorizeLenders`) and `:221-230` (`authorizeLenders`) change `_authorizedLenders` without touching markets (NatSpec `:217-219`, `:304-306`: "Must call `updateLenderAuthorization` to apply changes"); `:271-299` updates only the markets the borrower lists.

**If violated**: a lender removed from the controller set keeps deposit rights in every market not yet synced.

---

#### X-2

On-chain: **No**

> When a temporary reserve ratio ends (cancel or expiry), the market accepts the restored original ratio.

**Caller side**: `WildcatMarketController.sol:755` (cancel) and `:771` (`resetReserveRatio`) call `setReserveRatioBips(original)`.

**Callee side**: `market/WildcatMarketConfig.sol:183-186` refuses a decrease while `liquidityRequired() > totalAssets()` under the current ratio; the market's assets and requirement move independently through `borrow`, accrual and batch payments.

**If violated**: while the market is under its raised requirement, the temporary ratio outlives its expiry and an APR increase that would cancel it reverts.

---

#### X-3

On-chain: **Yes**

> `WildcatMarket.isClosed()` read by the controller reflects the market's latch.

**Caller side**: `WildcatMarketController.sol:626`, `:641`, `:690`.

**Callee side**: sole writer `market/WildcatMarket.sol:225`, reachable only through `onlyController` (`:217`).

**If violated**: the controller could change a closed market's terms.

---

#### X-4

On-chain: **Yes**

> A market's constructor reads the parameters of its own deployment from the deploying controller.

**Caller side**: `market/WildcatMarketBase.sol:85` (`IWildcatMarketController(msg.sender).getMarketParameters()`).

**Callee side**: `WildcatMarketController.sol:503` writes `_tmpMarketParameters` before `create2` at `:514` and resets it at `:519`; `getMarketParameters` (`:387-409`) adds the immutable borrower, sentinel, arch controller and current engine.

**If violated**: a market would be initialised with another deployment's asset, name or terms.

---

#### X-5

On-chain: **Yes**

> A controller's immutable `borrower` is the address that called the factory.

**Caller side**: `WildcatMarketController.sol:93-96`.

**Callee side**: `WildcatMarketControllerFactory.sol:358` (set to `msg.sender`), `:371` (`create2`), `:373` (reset).

**If violated**: the controller would serve a different borrower than the registry checked at G-50.

---

#### X-6

On-chain: **Yes**

> An escrow's constructor reads its own `(borrower, account, asset)` from the sentinel.

**Caller side**: `WildcatSanctionsEscrow.sol:18-19`.

**Callee side**: `WildcatSanctionsSentinel.sol:131` (set), `:133` (`new ... { salt }`), `:141` (reset).

**If violated**: escrowed value would be releasable to the wrong account.

---

#### X-7

On-chain: **No**

> Once `canReleaseEscrow()` is true, `releaseEscrow()` can move the escrowed balance.

**Caller side**: `WildcatSanctionsEscrow.sol:34-44` calls `asset.safeTransfer(account, balance())`; for market-token escrows the asset is the market (`market/WildcatMarketBase.sol:166-172`).

**Callee side**: `market/WildcatMarketToken.sol:83` loads the recipient through `_getAccount`, which reverts on `Blocked` (`market/WildcatMarketBase.sol:146`); the account stays `Blocked` until someone calls `stunningReversal` (`market/WildcatMarketConfig.sol:95-108`).

**If violated**: a released-in-principle escrow reverts on release until the account is reversed in the market.

---

#### X-8

On-chain: **Yes**

> Sanction checks in a market are keyed by that market's immutable borrower, and only that address can override them.

**Caller side**: `market/WildcatMarket.sol:48`, `market/WildcatMarketConfig.sol:82`, `:96`, `market/WildcatMarketWithdrawals.sol:204` call `isSanctioned(borrower, ·)`; `borrower` is immutable (`market/WildcatMarketBase.sol:33`, `:110`).

**Callee side**: `WildcatSanctionsSentinel.sol:85-87` combines the override row with Chainalysis; override writes are keyed by `msg.sender` (`:97`, `:105`) or restricted to escrow addresses (I-34).

**If violated**: a third party could unblock or shield accounts in another borrower's markets.

---

#### X-9

On-chain: **No**

> Every registered contract runs the arch controller's current SphereX engine.

**Caller side**: engines are copied at construction: `WildcatMarketControllerFactory.sol:100` (from the arch controller), `:293` (factory → controller), `WildcatMarketController.sol:408` (controller → market).

**Callee side**: `spherex/SphereXConfig.sol:143-147` changes only the arch controller's own slot; propagation happens only for contracts listed in `updateSphereXEngineOnRegisteredContracts` (`WildcatArchController.sol:73-114`) that are still registered (G-52).

**If violated**: contracts keep an older engine (or none); removed contracts can no longer be updated at all.

---

#### X-10

On-chain: **Yes**

> A market's fee recipient and protocol fee are fixed at deployment.

**Caller side**: `WildcatMarketController.sol:496-501` reads `getProtocolFeeConfiguration()` once per deployment; the market stores both as immutables (`market/WildcatMarketBase.sol:112-113`).

**Callee side**: `WildcatMarketControllerFactory.sol:229` rewrites the configuration for later deployments only; NatSpec `:170-172`: "`protocolFeeBips` and `feeRecipient` are immutable once a market is deployed."

**If violated**: the arch controller owner could re-route fees of live markets.

---

#### X-11

On-chain: **Yes**

> The addresses registered for new controllers and markets are the addresses `create2` deployed.

**Caller side**: `WildcatMarketController.sol:510-517` and `WildcatMarketControllerFactory.sol:362-375` register the precomputed address and ignore `create2`'s return value.

**Callee side**: `libraries/LibStoredInitCode.sol:108-123` reverts when `create2` fails (G-78); the init-code hash is computed from the same bytes the factory stores (`WildcatMarketControllerFactory.sol:108-110`, `:118-120`).

**If violated**: the registry would list an address without code.

---

#### X-12

On-chain: **No**

> `MarketLens.controllerFactory` is the arch controller's registered factory.

**Caller side**: `lens/MarketLens.sol:13-18` stores the single factory at construction; `lens/ControllerData.sol:44-49` derives controller addresses and fee data from it.

**Callee side**: `WildcatArchController.sol:245-258` adds and removes factories afterwards.

**If violated**: lens reads describe a factory the registry no longer lists, or miss a second one (read paths only).

---

## 4. Economic Invariants

Higher-order properties derived from combinations of §2 and §3 invariants.

---

#### E-1

On-chain: **Yes**

> A borrow never leaves the market below its liquidity requirement, and assets reserved for paid withdrawals and accrued fees are never borrowable.

**Follows from**: `I-18` + `I-1` + `I-4` (with guard G-8).

**If violated**: the borrower could draw assets owed to lenders who have already been paid into a batch.

---

#### E-2

On-chain: **Yes**

> Each withdrawal batch pays its lenders pro rata to their queued scaled amounts and never more than the batch was paid.

**Follows from**: `I-3` + `I-5` + `I-21` + `I-23`.

**If violated**: one lender's execution would consume another's share.

---

#### E-3

On-chain: **No**

> Only lenders the borrower currently authorises can add principal to a market.

**Follows from**: `X-1` + `I-12`.

**If violated**: deauthorised lenders (X-1) keep depositing until a sync, and accounts that reached `WithdrawOnly` without authorisation (I-12) can still queue withdrawals.

---

#### E-4

On-chain: **No**

> Queued withdrawals rank ahead of protocol fees.

**Follows from**: `I-22` + `I-23`.

**If violated**: by construction only paid-but-unclaimed withdrawals outrank fees; accrued fees are reserved ahead of pending and unpaid batch amounts (`libraries/Withdrawal.sol:57`, `market/WildcatMarketWithdrawals.sol:242-243`).

---

**Counts.** 78 guards (§1); 35 single-contract invariants (I-1 to I-35); 12 cross-contract invariants (X-1 to X-12); 4 economic invariants (E-1 to E-4). On-chain=No blocks: I-6, I-8, I-9, I-12, I-33, X-1, X-2, X-7, X-9, X-12, E-3, E-4 (12).
