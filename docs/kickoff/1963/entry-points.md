# Entry Point Map

> Wildcat V1 | 69 entry points (62 state-changing, 7 creation) | 21 permissionless | 25 role-gated | 16 admin-only | 7 initialization

**Scope.** Seven concrete contexts: `WildcatMarket`, `WildcatMarketController`, `WildcatMarketControllerFactory` and `WildcatArchController` from core commit `da74452aa7d1a0f024d99efd22cc6d950a8116b7`; `WildcatSanctionsSentinel` and `WildcatSanctionsEscrow` deployed from sentinel commit `6164ddd4c75ef6da2181e5623b99795b9829e31c` (licence-line change only relative to da74452a); `MarketLens` from a verified input that matches no single commit (closest `488b30d08c73a93be3e4bf99128c774997411d3a`, 40 of 46 in-tree files). Counts are per context: `changeSphereXEngine(address)` from `SphereXProtectedRegisteredBase` is counted once in each of `WildcatMarket`, `WildcatMarketController` and `WildcatMarketControllerFactory`, and the five solady `Ownable` actions are counted in `WildcatArchController`. Read paths (148 view actions) are excluded. Contexts are not deployed-address counts; the accepted registry holds 16 V1 entries. `file:line` references read da74452a; paths are relative to `src/` unless they start with `lib/`.

Abbreviations used below:

- **[accrual]** = `WildcatMarketBase._getUpdatedState()`: accrues interest and fees to an expired batch's expiry and then to `block.timestamp` (`FeeMath.updateScaleFactorAndFees()`), processes an expired pending batch (`_processExpiredWithdrawalBatch()`), and pays the pending batch from available liquidity (`_applyWithdrawalBatchPayment()`).
- **[write]** = `WildcatMarketBase._writeState()`: recomputes `isDelinquent`, stores `_state`, emits `StateUpdated`.
- **[SphereX]** = `sphereXGuardExternal`: when the contract's engine slot is nonzero, `ISphereXEngine.sphereXValidatePre` runs before the body and `sphereXValidatePost` after it; either may revert the call.

---

## Protocol Flow Paths

### Setup (arch-controller owner, SphereX admin)

`WildcatArchController` constructor → `WildcatSanctionsSentinel` constructor → `WildcatMarketControllerFactory` constructor → `registerControllerFactory()` → `setProtocolFeeConfiguration()` → `registerBorrower()`
`[setup above]` → `MarketLens` constructor  ◄── exactly one factory registered
`changeSphereXOperator()` → `changeSphereXEngine()` → `updateSphereXEngineOnRegisteredContracts()`  ◄── operator is `address(0)` until the admin sets it

### Borrower

`[setup above]` → `WildcatMarketControllerFactory.deployController()` → `WildcatMarketController.deployMarket()`  ◄── asset not blacklisted; origination-fee allowance to the controller
`[setup above]` → `WildcatMarketControllerFactory.deployControllerAndMarket()`  (same end state in one call)
`[market deployed]` → `authorizeLenders()` / `authorizeLendersAndUpdateMarkets()`
`[lender deposit below]` → `WildcatMarket.borrow()`  ◄── assets above `liquidityRequired()`; borrower not Chainalysis-flagged
                     ├─→ `WildcatMarketController.setAnnualInterestBips()`  ◄── a cut raises the reserve ratio until it is reset or cancelled; reset is allowed from 2 weeks after the latest renewing cut
                     │        └─→ `resetReserveRatio()` (any caller)  ◄── expiry passed; market not below its current requirement
                     ├─→ `repay()` / `repayOutstandingDebt()` / `repayDelinquentDebt()` (any payer)
                     └─→ `WildcatMarketController.closeMarket()` → `WildcatMarket.closeMarket()`  ◄── no unpaid batches; borrower allowance for any shortfall

### Lender

`[authorisation above]` → `WildcatMarket.deposit()` / `depositUpTo()` → `transfer()` / `transferFrom()`
`[deposit above]` → `queueWithdrawal()`  ◄── at least `WithdrawOnly`
                     └─→ [batch expiry passes] → `executeWithdrawal()` / `executeWithdrawals()` (any caller)  ◄── batch paid in full or part
                                                    └─→ unpaid remainder → `repayAndProcessUnpaidWithdrawalBatches()` → `executeWithdrawal()`

### Maintenance (any caller)

`[market deployed]` → `updateState()`; `collectFees()`  ◄── accrued fees and assets beyond unclaimed withdrawals
`[borrower changed lender set]` → `WildcatMarketController.updateLenderAuthorization()`

### Sanctions (any caller unless noted)

[Chainalysis flags account, no borrower override] → `nukeFromOrbit()` → `WildcatSanctionsSentinel.createEscrow()` (called by the market) → market tokens held by `WildcatSanctionsEscrow`
`[blocked above]` → [flag lifted, or borrower calls `overrideSanction()`] → `stunningReversal()` → `WildcatSanctionsEscrow.releaseEscrow()`

---

## Permissionless

Entry points with no caller restriction. `transfer` and `transferFrom` refuse only `Blocked` accounts, and `approve` refuses none; `overrideSanction` and `removeSanctionOverride` write only the caller's own row. Sorted by value flow: value in, value out, market-token movement, no movement.

### `WildcatMarket.repay(uint256)`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any payer (borrower by convention; NatSpec `market/WildcatMarket.sol:187-194` asks others not to use it) |
| Parameters | amount (user-controlled) |
| Guards | `amount != 0` (`:197`); reverts on a closed market after the transfer and event (G-11, `:202`) |
| Call chain | `→ SafeTransferLib.safeTransferFrom(asset, msg.sender, market, amount) → [accrual] → [write]` |
| State modified | market state via [accrual]; no repayment ledger (repayment raises `totalAssets()` only) |
| Value flow | Tokens: caller → market |
| Reentrancy guard | yes |

### `WildcatMarket.repayOutstandingDebt()`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any payer |
| Parameters | none; amount = `totalDebts().satSub(totalAssets())` (protocol-derived) |
| Guards | reverts `NullRepayAmount` when that amount is zero (G-9); reverts on a closed market (G-10) |
| Call chain | `→ [accrual] → WildcatMarket._repay() → SafeTransferLib.safeTransferFrom() → [write]` |
| State modified | market state via [accrual] |
| Value flow | Tokens: caller → market (outstanding debt) |
| Reentrancy guard | yes |

### `WildcatMarket.repayDelinquentDebt()`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any payer |
| Parameters | none; amount = `liquidityRequired().satSub(totalAssets())` (protocol-derived) |
| Guards | reverts `NullRepayAmount` when that amount is zero (G-9); reverts on a closed market (G-10) |
| Call chain | `→ [accrual] → WildcatMarket._repay() → SafeTransferLib.safeTransferFrom() → [write]` |
| State modified | market state via [accrual] |
| Value flow | Tokens: caller → market (delinquent shortfall) |
| Reentrancy guard | yes |

### `WildcatMarket.repayAndProcessUnpaidWithdrawalBatches(uint256,uint256)`

| Aspect | Detail |
|--------|--------|
| Visibility | public, nonReentrant, [SphereX] |
| Caller | Any payer or keeper |
| Parameters | repayAmount (user-controlled, may be 0), maxBatches (user-controlled) |
| Guards | reverts on a closed market (G-31); checked `totalAssets() - (normalizedUnclaimedWithdrawals + accruedProtocolFees)` (G-32); `unpaidBatches.first()` on empty queue cannot be reached because `numBatches` is capped by the queue length (`market/WildcatMarketWithdrawals.sol:246`) |
| Call chain | `→ SafeTransferLib.safeTransferFrom() (if repayAmount > 0) → [accrual] → _processUnpaidWithdrawalBatch() × ≤ maxBatches → _applyWithdrawalBatchPayment() → FIFOQueue.shift() → [write]` |
| State modified | `batches[expiry]`, `unpaidBatches`, `scaledPendingWithdrawals`, `scaledTotalSupply`, `normalizedUnclaimedWithdrawals` |
| Value flow | Tokens: caller → market when repayAmount > 0 |
| Reentrancy guard | yes |

### `WildcatArchController.requestOwnershipHandover()`

| Aspect | Detail |
|--------|--------|
| Visibility | public payable (solady `Ownable`, `lib/solady/src/auth/Ownable.sol:154`) |
| Caller | Any prospective owner |
| Parameters | none |
| Guards | none |
| Call chain | `→ Ownable handover slot write` |
| State modified | handover expiry for `msg.sender` = `block.timestamp + 48 hours` |
| Value flow | ETH: `msg.value`, if any, stays in the arch controller |
| Reentrancy guard | no |

### `WildcatArchController.cancelOwnershipHandover()`

| Aspect | Detail |
|--------|--------|
| Visibility | public payable (`lib/solady/src/auth/Ownable.sol:170`) |
| Caller | Any caller; with nothing pending it clears a zero slot and still emits the event |
| Parameters | none |
| Guards | none |
| Call chain | `→ Ownable handover slot clear` |
| State modified | clears `msg.sender`'s handover |
| Value flow | ETH: `msg.value`, if any, stays in the arch controller |
| Reentrancy guard | no |

### `WildcatMarket.collectFees()`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any caller; proceeds always go to the immutable `feeRecipient` |
| Parameters | none |
| Guards | `accruedProtocolFees != 0` (G-4); `withdrawableProtocolFees(totalAssets()) != 0` (G-5); arithmetic underflow when `totalAssets()` is below `normalizedUnclaimedWithdrawals` |
| Call chain | `→ [accrual] → MarketStateLib.withdrawableProtocolFees() → SafeTransferLib.safeTransfer(asset, feeRecipient, fees) → [write]` |
| State modified | `accruedProtocolFees -= withdrawableFees` |
| Value flow | Tokens: market → `feeRecipient` |
| Reentrancy guard | yes |

### `WildcatMarket.executeWithdrawal(address,uint32)`

| Aspect | Detail |
|--------|--------|
| Visibility | public, nonReentrant, [SphereX] |
| Caller | Any caller on the account's behalf |
| Parameters | accountAddress (user-controlled), expiry (user-controlled) |
| Guards | `expiry < block.timestamp` (G-28); newly withdrawable amount nonzero (G-29); checked unclaimed decrement (G-30) |
| Call chain | `→ [accrual] → _executeWithdrawal() → WildcatSanctionsSentinel.isSanctioned() → (sanctioned) _blockAccount() → WildcatSanctionsSentinel.createEscrow() (market-token and asset escrows) → SafeTransferLib.safeTransfer() → [write]` |
| State modified | `accountStatuses[expiry][account].normalizedAmountWithdrawn`, `normalizedUnclaimedWithdrawals`; when sanctioned: account role → `Blocked`, its scaled balance → escrow |
| Value flow | Tokens: market → account, or → the account's asset escrow when the sentinel reports it sanctioned |
| Reentrancy guard | yes |

### `WildcatMarket.executeWithdrawals(address[],uint32[])`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any caller |
| Parameters | accountAddresses (user-controlled), expiries (user-controlled) |
| Guards | array lengths equal (`market/WildcatMarketWithdrawals.sol:162`); per pair as `executeWithdrawal` |
| Call chain | `→ [accrual] → _executeWithdrawal() × n → [write]` |
| State modified | as `executeWithdrawal`, per pair |
| Value flow | Tokens: market → each account or its asset escrow |
| Reentrancy guard | yes |

### `WildcatSanctionsEscrow.releaseEscrow()`

| Aspect | Detail |
|--------|--------|
| Visibility | public |
| Caller | Any caller |
| Parameters | none (borrower, account, asset are immutables) |
| Guards | `canReleaseEscrow()`: sentinel no longer reports the account sanctioned for the borrower (G-76); for a market-token escrow the market's transfer also requires the account not `Blocked`, so `stunningReversal` must run first; an empty market-token escrow reverts `NullTransferAmount` |
| Call chain | `→ WildcatSanctionsSentinel.isSanctioned() → IERC20(asset).balanceOf(escrow) → SafeTransferLib.safeTransfer(asset, account, balance) (→ WildcatMarket.transfer() when the asset is a market)` |
| State modified | none in the escrow; the asset's balances |
| Value flow | Tokens: escrow → account (whole balance) |
| Reentrancy guard | no |

### `WildcatMarket.transfer(address,uint256)`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any holder not `Blocked` |
| Parameters | to (user-controlled), amount (user-controlled, normalized) |
| Guards | neither side `Blocked` (G-15); nonzero scaled amount (G-23); checked balance (G-25); no lender role or sanctions check on either side |
| Call chain | `→ WildcatMarketToken._transfer() → [accrual] → _getAccount(from), _getAccount(to) → [write]` |
| State modified | `_accounts[from].scaledBalance`, `_accounts[to].scaledBalance` |
| Value flow | Market tokens: caller → to; no underlying moves |
| Reentrancy guard | yes |

### `WildcatMarket.transferFrom(address,address,uint256)`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any spender with allowance |
| Parameters | from (user-controlled), to (user-controlled), amount (user-controlled) |
| Guards | allowance ≥ amount unless unlimited (G-24); as `transfer` |
| Call chain | `→ WildcatMarketToken._approve() (unless allowance is max) → _transfer()` |
| State modified | `allowance[from][msg.sender]`; scaled balances |
| Value flow | Market tokens: from → to |
| Reentrancy guard | yes |

### `WildcatMarket.nukeFromOrbit(address)`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any caller |
| Parameters | accountAddress (user-controlled) |
| Guards | sentinel reports the account sanctioned for this borrower (G-18) |
| Call chain | `→ WildcatSanctionsSentinel.isSanctioned() → [accrual] → _blockAccount() → WildcatSanctionsSentinel.createEscrow(borrower, account, market) → [write]` |
| State modified | account role → `Blocked` (no-op if already blocked); scaled balance moved to `_accounts[escrow]` |
| Value flow | Market tokens: account → its escrow; no underlying moves |
| Reentrancy guard | yes |

### `WildcatMarket.approve(address,uint256)`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any address (including `Blocked` accounts) |
| Parameters | spender (user-controlled), amount (user-controlled) |
| Guards | none beyond the modifiers |
| Call chain | `→ WildcatMarketToken._approve()` |
| State modified | `allowance[msg.sender][spender]` |
| Value flow | None |
| Reentrancy guard | yes |

### `WildcatMarket.updateState()`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any keeper |
| Parameters | none |
| Guards | none beyond the modifiers |
| Call chain | `→ [accrual] → [write]` |
| State modified | `scaleFactor`, `accruedProtocolFees`, `timeDelinquent`, `lastInterestAccruedTimestamp`, batch payment fields, `unpaidBatches`, `isDelinquent` |
| Value flow | None |
| Reentrancy guard | yes |

### `WildcatMarket.stunningReversal(address)`

| Aspect | Detail |
|--------|--------|
| Visibility | external, nonReentrant, [SphereX] |
| Caller | Any caller |
| Parameters | accountAddress (user-controlled) |
| Guards | sentinel no longer reports the account sanctioned (G-19); account is `Blocked` (G-20) |
| Call chain | `→ WildcatSanctionsSentinel.isSanctioned()` |
| State modified | `_accounts[account].approval`: `Blocked` → `WithdrawOnly`; no accrual or `[write]` |
| Value flow | None |
| Reentrancy guard | yes |

### `WildcatMarketController.resetReserveRatio(address)`

| Aspect | Detail |
|--------|--------|
| Visibility | external, [SphereX] |
| Caller | Any keeper |
| Parameters | market (user-controlled; only markets with a stored record pass) |
| Guards | temporary record exists (G-45); expiry reached (G-46); transitively the market refuses the decrease while below its current requirement (G-21); no caller or controlled-market check |
| Call chain | `→ WildcatMarket.setReserveRatioBips(original) → [accrual] → [write]` |
| State modified | `temporaryExcessReserveRatio[market]` deleted; market `reserveRatioBips` restored |
| Value flow | None |
| Reentrancy guard | no (the market call is nonReentrant) |

### `WildcatMarketController.updateLenderAuthorization(address,address[])`

| Aspect | Detail |
|--------|--------|
| Visibility | external, [SphereX] |
| Caller | Any caller |
| Parameters | lender (user-controlled), markets (user-controlled; each must be controlled, G-36) |
| Guards | each market controlled; transitively reverts if the lender is `Blocked` in a listed market (G-15) |
| Call chain | `→ WildcatMarket.updateAccountAuthorizations([lender], _authorizedLenders.contains(lender)) → [accrual] → [write]` |
| State modified | lender's role per market: `DepositAndWithdraw` if in the controller set; otherwise `DepositAndWithdraw` → `WithdrawOnly` (other roles unchanged) |
| Value flow | None |
| Reentrancy guard | no (the market call is nonReentrant) |

### `WildcatSanctionsSentinel.createEscrow(address,address,address)`

| Aspect | Detail |
|--------|--------|
| Visibility | public |
| Caller | Any caller (markets call it while blocking) |
| Parameters | borrower, account, asset (all user-controlled; borrower not checked against any registry) |
| Guards | returns the existing escrow when code exists at the create2 address (`WildcatSanctionsSentinel.sol:129`) |
| Call chain | `→ getEscrowAddress() → new WildcatSanctionsEscrow{salt}() → WildcatSanctionsEscrow constructor → tmpEscrowParams()` |
| State modified | `tmpEscrowParams` (set, then reset); `sanctionOverrides[borrower][escrow] = true` when created |
| Value flow | None |
| Reentrancy guard | no |

### `WildcatSanctionsSentinel.overrideSanction(address)`

| Aspect | Detail |
|--------|--------|
| Visibility | public |
| Caller | Any caller; effective only where the caller is a market's borrower |
| Parameters | account (user-controlled) |
| Guards | none; the row key is `msg.sender` |
| Call chain | none |
| State modified | `sanctionOverrides[msg.sender][account] = true` |
| Value flow | None |
| Reentrancy guard | no |

### `WildcatSanctionsSentinel.removeSanctionOverride(address)`

| Aspect | Detail |
|--------|--------|
| Visibility | public |
| Caller | Any caller; effective only where the caller is a market's borrower |
| Parameters | account (user-controlled) |
| Guards | none; the row key is `msg.sender` |
| Call chain | none |
| State modified | `sanctionOverrides[msg.sender][account] = false` |
| Value flow | None |
| Reentrancy guard | no |

---

## Role-Gated

Entry points restricted to a role, a contract caller, or an internal `msg.sender` check. Compact tables (69 entry points exceed the 30-row threshold for per-function blocks).

### Authorised lender (market account role)

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatMarket | `deposit(uint256)` | [SphereX]; nonReentrant in `_depositUpTo`; `DepositAndWithdraw` via `_getAccountWithRole` (a `Null` role is granted when the controller lists the caller); unsanctioned branch: not closed (G-1), nonzero scaled amount (G-2); whole amount accepted (G-3). Sanctioned caller: the branch blocks the caller without a role check; it completes only when `amount == 0` (G-3), otherwise the call reverts | [accrual]; caller `scaledBalance` and `scaledTotalSupply` +s; role write; or, sanctioned with `amount == 0`: role → `Blocked`, balance → escrow | Tokens: caller → market (unsanctioned branch); market tokens caller → escrow (sanctioned, `amount == 0`) |
| WildcatMarket | `depositUpTo(uint256)` | as `deposit`, without G-3; the sanctioned branch completes for any amount | [accrual]; balances +s and role write, or (sanctioned) role → `Blocked` and balance → escrow | Tokens: caller → market (unsanctioned branch); market tokens caller → escrow (sanctioned branch) |
| WildcatMarket | `queueWithdrawal(uint256)` | nonReentrant; [SphereX]; at least `WithdrawOnly` (G-16); nonzero scaled amount (G-26); checked balance (G-27) | [accrual]; balance −s; `accountStatuses`, batch `scaledTotalAmount`, `scaledPendingWithdrawals` +s; opens a batch at `block.timestamp + withdrawalBatchDuration` when none is pending; may pay part at once | Market tokens: caller → withdrawal batch; no underlying moves |

### Market borrower (market immutable `borrower`)

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatMarket | `borrow(uint256)` | `onlyBorrower` (G-13); nonReentrant; [SphereX]; borrower not Chainalysis-flagged (G-6); not closed (G-7); amount ≤ `borrowableAssets` (G-8) | [accrual]; [write] recomputes `isDelinquent` | Tokens: market → borrower |

### Controller borrower (controller immutable `borrower`)

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatMarketController | `authorizeLenders(address[])` | `onlyBorrower` (G-35); [SphereX] | `_authorizedLenders` add; markets unchanged until synced | None |
| WildcatMarketController | `authorizeLendersAndUpdateMarkets(address[],address[])` | G-35; [SphereX]; each market controlled (G-36, inline); a listed lender `Blocked` in a listed market reverts (G-15) | `_authorizedLenders` add; low-level `updateAccountAuthorizations(lenders, true)` on each listed market | None |
| WildcatMarketController | `deauthorizeLenders(address[])` | G-35; [SphereX] | `_authorizedLenders` remove; markets unchanged until synced | None |
| WildcatMarketController | `deauthorizeLendersAndUpdateMarkets(address[],address[])` | G-35; [SphereX]; each market controlled; a listed lender `Blocked` in a listed market reverts (G-15) | `_authorizedLenders` remove; `updateAccountAuthorizations(lenders, false)` on each listed market | None |
| WildcatMarketController | `closeMarket(address)` | G-35; `onlyControlledMarket` (G-36); [SphereX]; not already closed (G-41); market side: no unpaid batches (G-12) | market: APR 0, `isClosed`, reserve 10000, `timeDelinquent` 0 | Tokens: borrower → market (shortfall, `transferFrom` by the market) or market → borrower (excess) |
| WildcatMarketController | `setAnnualInterestBips(address,uint16)` | G-35; G-36; [SphereX]; not closed (G-43); within bounds (G-44); transitively the market's reserve-ratio checks (G-21, G-22) | `temporaryExcessReserveRatio[market]`; market `reserveRatioBips` (raised on a cut below the recorded original, restored when the new rate is not below it) and `annualInterestBips` | None |
| WildcatMarketController | `setMaxTotalSupply(address,uint256)` | G-35; G-36; [SphereX]; not closed (G-42); no bound against current supply; the market reverts above `uint128` | market `maxTotalSupply` | None |

### Registered borrower (arch-controller registry) or deploying factory

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatMarketController | `deployMarket(address,string,string,uint128,uint16,uint16,uint32,uint16,uint32)` | [SphereX]; caller is the borrower and a registered borrower, or the controller factory (G-37); asset not blacklisted (G-38); non-empty prefixes and parameter bounds (G-39); no market at the create2 address (G-40); this controller registered in the arch controller (else `NotController`) | `_tmpMarketParameters` (set, reset); `create2` market; arch `registerMarket`; `_controlledMarkets` add | Tokens: origination fee borrower → fee recipient when configured (pulled from `borrower`, not `msg.sender`) |
| WildcatMarketControllerFactory | `deployController()` | [SphereX]; caller registered (G-50); no controller yet (G-51); this factory registered in the arch controller (else `NotControllerFactory`) | `_tmpMarketBorrowerParameter` (set, reset); `create2` controller (salt = caller); arch `registerController`; `_deployedControllers` add | None |
| WildcatMarketControllerFactory | `deployControllerAndMarket(string,string,address,uint128,uint16,uint16,uint32,uint16,uint32)` | as `deployController` (including `NotControllerFactory`), then every `deployMarket` check with the factory as caller | controller and market deployed and registered | Tokens: origination fee borrower → fee recipient when configured |

### Market's controller contract (market immutable `controller`)

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatMarket | `closeMarket()` | `onlyController` (G-14); nonReentrant; [SphereX]; no unpaid batches (G-12) | [accrual]; APR 0, `isClosed = true`, reserve 10000, `timeDelinquent = 0`; [write] | Tokens: borrower → market (`totalDebts − totalAssets`) or market → borrower (excess) |
| WildcatMarket | `setAnnualInterestBips(uint16)` | G-14; nonReentrant; [SphereX] | [accrual]; `annualInterestBips` | None |
| WildcatMarket | `setMaxTotalSupply(uint256)` | G-14; nonReentrant; [SphereX]; `toUint128` | [accrual]; `maxTotalSupply` | None |
| WildcatMarket | `setReserveRatioBips(uint16)` | G-14; nonReentrant; [SphereX]; decrease refused while below the current requirement (G-21); increase refused if it creates delinquency (G-22) | [accrual]; `reserveRatioBips` | None |
| WildcatMarket | `updateAccountAuthorizations(address[],bool)` | G-14; nonReentrant; [SphereX]; each account not `Blocked` (G-15) | [accrual]; `authorize`: role → `DepositAndWithdraw`; else `DepositAndWithdraw` → `WithdrawOnly` | None |

### Arch controller contract (SphereX operator of registered contracts)

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatMarket | `changeSphereXEngine(address)` | `msg.sender == _archController` (G-73); no engine validation here | SphereX engine slot | None |
| WildcatMarketController | `changeSphereXEngine(address)` | G-73 | SphereX engine slot | None |
| WildcatMarketControllerFactory | `changeSphereXEngine(address)` | G-73 | SphereX engine slot | None |

### Registry callers (registered factory, registered controller)

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatArchController | `registerController(address)` | caller is a registered factory (G-59); not already registered (G-60) | `_controllers` add; engine `addAllowedSenderOnChain` when an engine is set | None |
| WildcatArchController | `registerMarket(address)` | caller is a registered controller (G-62); not already registered (G-63) | `_markets` add; engine `addAllowedSenderOnChain` when set | None |

### Pending SphereX admin

| Contract | Function | Guards | State modified | Value flow |
|----------|----------|--------|----------------|------------|
| WildcatArchController | `acceptSphereXAdminRole()` | caller is the pending SphereX admin (G-71) | SphereX admin = caller; pending slot cleared | None |

---

## Admin-Only

| Contract | Function | Role | Parameters | State Modified |
|----------|----------|------|------------|----------------|
| WildcatArchController | `registerBorrower(address)` | owner (G-65) | borrower | `_borrowers` add (G-53) |
| WildcatArchController | `removeBorrower(address)` | owner | borrower | `_borrowers` remove (G-54); existing markets keep working; the borrower's new controllers and borrower-initiated `deployMarket` revert (`NotRegisteredBorrower`) |
| WildcatArchController | `addBlacklist(address)` | owner | asset | `_assetBlacklist` add (G-55); affects new deployments only |
| WildcatArchController | `removeBlacklist(address)` | owner | asset | `_assetBlacklist` remove (G-56) |
| WildcatArchController | `registerControllerFactory(address)` | owner | factory | `_controllerFactories` add (G-57); engine `addAllowedSenderOnChain` when set |
| WildcatArchController | `removeControllerFactory(address)` | owner | factory | `_controllerFactories` remove (G-58) |
| WildcatArchController | `removeController(address)` | owner | controller | `_controllers` remove (G-61); the controller can no longer register markets |
| WildcatArchController | `removeMarket(address)` | owner | market | `_markets` remove (G-64); the market keeps operating |
| WildcatArchController | `transferOwnership(address)` (payable) | owner | newOwner ≠ 0 (G-66) | owner; `msg.value` retained |
| WildcatArchController | `renounceOwnership()` (payable) | owner | none | owner = 0; `msg.value` retained |
| WildcatArchController | `completeOwnershipHandover(address)` (payable) | owner | pendingOwner with unexpired request (G-67) | owner = pendingOwner; `msg.value` retained |
| WildcatMarketControllerFactory | `setProtocolFeeConfiguration(address,address,uint80,uint16)` | arch-controller owner (G-48); [SphereX] | feeRecipient, originationFeeAsset, originationFeeAmount, protocolFeeBips (G-49) | `_protocolFeeConfiguration`, applied to markets deployed afterwards |
| WildcatArchController | `transferSphereXAdminRole(address)` | SphereX admin (G-68) | newAdmin | pending SphereX admin |
| WildcatArchController | `changeSphereXOperator(address)` | SphereX admin (G-68) | newSphereXOperator | SphereX operator slot |
| WildcatArchController | `changeSphereXEngine(address)` | SphereX operator (G-69) | newSphereXEngine (interface-checked, G-72) | arch controller's own engine slot; registered contracts keep theirs |
| WildcatArchController | `updateSphereXEngineOnRegisteredContracts(address[],address[],address[])` | SphereX operator or admin (G-70) | factories, controllers, markets (each must be registered, G-52) | each listed contract's engine slot (low-level `changeSphereXEngine`); engine `addAllowedSenderOnChain` per contract when set |

---

## Initialization

Seven creation actions, one per context.

| Context | Constructor | Deployed by | Guards | State written |
|---------|-------------|-------------|--------|---------------|
| WildcatArchController | `constructor()` | deployer | none | owner, SphereX admin = deployer; operator and engine = `address(0)` (`WildcatArchController.sol:61-63`) |
| WildcatSanctionsSentinel | `constructor(address,address)` | deployer | none | `archController`, `chainalysisSanctionsList` immutables; `tmpEscrowParams` placeholders |
| WildcatMarketControllerFactory | `constructor(address,address,(uint32,uint32,uint16,uint16,uint16,uint16,uint32,uint32,uint16,uint16))` | deployer | G-47 | arch controller, sentinel and constraint immutables; two init-code storage contracts (controller and market creation code); engine copied from the arch controller |
| WildcatMarketController | `constructor()` | factory `create2`, salt = borrower | none of its own | borrower, sentinel, market init-code, constraint immutables from the factory (X-5); engine from the factory |
| WildcatMarket | `constructor()` (no ABI constructor row; implicit creation) | controller `create2` | none of its own | immutables and initial `MarketState` (`scaleFactor = RAY`, open) from the controller (X-4); `decimals` from the asset; engine from the controller |
| WildcatSanctionsEscrow | `constructor()` | sentinel `create2` | none of its own | `sentinel = msg.sender`; borrower, account, asset from `tmpEscrowParams` (X-6) |
| MarketLens | `constructor(address)` | deployer | exactly one registered factory (G-77) | `archController`, `controllerFactory` immutables |

---

## External Calls and Dynamic Callees

| Callee | Called from | Nature |
|--------|-------------|--------|
| Underlying ERC20 (arbitrary, chosen at `deployMarket`) | `WildcatMarket` deposits, `borrow`, repayments, `collectFees`, executions, `closeMarket` (solady `SafeTransferLib`); `totalAssets()` (assembly `balanceOf`); market constructor (`decimals`); `deployMarket` (`queryName`, `querySymbol`); `WildcatSanctionsEscrow.releaseEscrow` | token transfers and metadata; asset events are outside this map |
| Origination-fee asset | `WildcatMarketController.deployMarket` (`safeTransferFrom(borrower, feeRecipient, amount)`) | token transfer |
| Chainalysis sanctions list (immutable in the sentinel) | `WildcatSanctionsSentinel.isFlaggedByChainalysis` / `isSanctioned`, reached from market deposits, `borrow`, `nukeFromOrbit`, `stunningReversal`, executions and `releaseEscrow` | view query deciding sanctioned branches |
| SphereX engine (per-contract slot) | every [SphereX] function (`sphereXValidatePre`/`Post`); `WildcatArchController` registrations and engine updates (`addAllowedSenderOnChain`); `changeSphereXEngine` on the arch controller (`supportsInterface`) | may revert guarded calls; emits its own events outside this map |
| Caller-named markets | `WildcatMarketController.authorizeLendersAndUpdateMarkets`, `deauthorizeLendersAndUpdateMarkets` (assembly `call`), `updateLenderAuthorization`, `resetReserveRatio`, `MarketLens` queries | controlled-market check on the first three; `resetReserveRatio` succeeds only for markets with a stored record |
| Caller-named registered contracts | `WildcatArchController.updateSphereXEngineOnRegisteredContracts` (`_callWith` low-level call) | registry membership checked (G-52) |
| Caller-named `(borrower, account, asset)` | `WildcatSanctionsSentinel.createEscrow` | no registry check |

## Action index

Generated from `linkage.json` by `evidence/producers/assemble_bundle.py`. One row per scoped state-changing or creation action; the 148 read paths are listed in `actions.json`.

| Action id | Disposition | Events |
| --- | --- | --- |
| `MarketLensMixed:MarketLens:creation:constructor(address)` | eventless | 0 |
| `WildcatArchController:WildcatArchController:creation:constructor()` | mapped | 4 |
| `WildcatArchController:WildcatArchController:state-changing:acceptSphereXAdminRole()` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:addBlacklist(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:cancelOwnershipHandover()` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:changeSphereXEngine(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:changeSphereXOperator(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:completeOwnershipHandover(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:registerBorrower(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:registerController(address)` | conditional | 2 |
| `WildcatArchController:WildcatArchController:state-changing:registerControllerFactory(address)` | conditional | 2 |
| `WildcatArchController:WildcatArchController:state-changing:registerMarket(address)` | conditional | 2 |
| `WildcatArchController:WildcatArchController:state-changing:removeBlacklist(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:removeBorrower(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:removeController(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:removeControllerFactory(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:removeMarket(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:renounceOwnership()` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:requestOwnershipHandover()` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:transferOwnership(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:transferSphereXAdminRole(address)` | mapped | 1 |
| `WildcatArchController:WildcatArchController:state-changing:updateSphereXEngineOnRegisteredContracts(address[],address[],address[])` | conditional | 4 |
| `WildcatMarketControllerFactory:WildcatMarket:creation:constructor()` | mapped | 2 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:approve(address,uint256)` | mapped | 1 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:borrow(uint256)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:changeSphereXEngine(address)` | mapped | 1 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:closeMarket()` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:collectFees()` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:deposit(uint256)` | conditional | 15 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:depositUpTo(uint256)` | conditional | 15 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:executeWithdrawal(address,uint32)` | conditional | 16 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:executeWithdrawals(address[],uint32[])` | conditional | 16 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:nukeFromOrbit(address)` | conditional | 12 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:queueWithdrawal(uint256)` | conditional | 13 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:repay(uint256)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:repayAndProcessUnpaidWithdrawalBatches(uint256,uint256)` | conditional | 11 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:repayDelinquentDebt()` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:repayOutstandingDebt()` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:setAnnualInterestBips(uint16)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:setMaxTotalSupply(uint256)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:setReserveRatioBips(uint16)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:stunningReversal(address)` | mapped | 1 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:transfer(address,uint256)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:transferFrom(address,address,uint256)` | conditional | 9 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:updateAccountAuthorizations(address[],bool)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarket:state-changing:updateState()` | conditional | 7 |
| `WildcatMarketControllerFactory:WildcatMarketController:creation:constructor()` | mapped | 2 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:authorizeLenders(address[])` | conditional | 1 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:authorizeLendersAndUpdateMarkets(address[],address[])` | conditional | 9 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:changeSphereXEngine(address)` | mapped | 1 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:closeMarket(address)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:deauthorizeLenders(address[])` | conditional | 1 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:deauthorizeLendersAndUpdateMarkets(address[],address[])` | conditional | 9 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:deployMarket(address,string,string,uint128,uint16,uint16,uint32,uint16,uint32)` | conditional | 5 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:resetReserveRatio(address)` | conditional | 9 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:setAnnualInterestBips(address,uint16)` | conditional | 13 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:setMaxTotalSupply(address,uint256)` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarketController:state-changing:updateLenderAuthorization(address,address[])` | conditional | 8 |
| `WildcatMarketControllerFactory:WildcatMarketControllerFactory:creation:constructor(address,address,(uint32,uint32,uint16,uint16,uint16,uint16,uint32,uint32,uint16,uint16))` | mapped | 2 |
| `WildcatMarketControllerFactory:WildcatMarketControllerFactory:state-changing:changeSphereXEngine(address)` | mapped | 1 |
| `WildcatMarketControllerFactory:WildcatMarketControllerFactory:state-changing:deployController()` | conditional | 5 |
| `WildcatMarketControllerFactory:WildcatMarketControllerFactory:state-changing:deployControllerAndMarket(string,string,address,uint128,uint16,uint16,uint32,uint16,uint32)` | conditional | 10 |
| `WildcatMarketControllerFactory:WildcatMarketControllerFactory:state-changing:setProtocolFeeConfiguration(address,address,uint80,uint16)` | mapped | 1 |
| `WildcatSanctionsSentinel:WildcatSanctionsEscrow:creation:constructor()` | eventless | 0 |
| `WildcatSanctionsSentinel:WildcatSanctionsEscrow:state-changing:releaseEscrow()` | conditional | 9 |
| `WildcatSanctionsSentinel:WildcatSanctionsSentinel:creation:constructor(address,address)` | eventless | 0 |
| `WildcatSanctionsSentinel:WildcatSanctionsSentinel:state-changing:createEscrow(address,address,address)` | conditional | 2 |
| `WildcatSanctionsSentinel:WildcatSanctionsSentinel:state-changing:overrideSanction(address)` | mapped | 1 |
| `WildcatSanctionsSentinel:WildcatSanctionsSentinel:state-changing:removeSanctionOverride(address)` | mapped | 1 |
