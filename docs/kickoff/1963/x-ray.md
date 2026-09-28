# X-Ray Report

> Wildcat V1 | 4754 nSLOC | da74452 (`detached HEAD`) | Foundry | 28/09/26

---

## 1. Protocol Overview

**What it does:** Each market lends one arbitrary ERC20 to a single pre-registered borrower without collateral, records lender claims as scaled balances that grow at a borrower-set APR, and settles exits through time-boxed withdrawal batches.

- **Users**: Lenders authorised by the borrower deposit, transfer, queue and execute withdrawals; registered borrowers deploy a controller and markets, borrow, repay and set terms; any caller can update state, execute withdrawals, collect fees to the fee recipient and block or unblock sanctioned accounts.
- **Core flow**: `deposit` → `borrow` → `queueWithdrawal` → batch expiry → `executeWithdrawal`; repayments restore liquidity and pay batches.
- **Key mechanism**: a ray scale factor accrues linear interest plus a delinquency penalty at each state write; the liquidity requirement is the reserve ratio of non-pending supply plus pending and paid withdrawals plus protocol fees, and a market below it is delinquent.
- **Token model**: every market is its own rebasing ERC20 (`balanceOf` = scaled balance × scale factor); `WildcatSanctionsEscrow` contracts hold market tokens or assets of blocked accounts.
- **Admin model**: the `WildcatArchController` owner (solady `Ownable`) curates borrowers, factories, controllers, markets, an asset blacklist and, through the factory, fee terms for new markets; a SphereX admin and operator install a call-validation engine; the borrower sets market terms within controller bounds. No proxies, pause or timelock.

For a visual overview of the protocol's architecture, see the [architecture diagram](architecture.svg).

### Scope and Source Identity

- **Contexts (7)**: `WildcatMarket`, `WildcatMarketController`, `WildcatMarketControllerFactory` and `WildcatArchController` from core commit `da74452aa7d1a0f024d99efd22cc6d950a8116b7`; `WildcatSanctionsSentinel` and `WildcatSanctionsEscrow` deployed from sentinel commit `6164ddd4c75ef6da2181e5623b99795b9829e31c`, whose `src/` diff against da74452a changes only SPDX licence lines; `MarketLens` from a verified input that matches no single commit (closest `488b30d08c73a93be3e4bf99128c774997411d3a`, 40 of 46 in-tree files; that commit's `src/` differs from da74452a only in licence lines, and the six differing lens-input files could not be inspected here).
- **Equivalent core commits**: `ebb6cecc4e72ea90187bc10006f8aa35d7ae2da9`, `e9552f0e8a093e214dd69947dc689023df09ff20`, `e962bf37866483a3573016a3087331c5de9f0929` and `016d0658d6d442b8f42e3bb68f01fae43c150307` carry the same core sources as da74452a; which of the five the deployer checked out could not be determined.
- **Registry**: the accepted registry holds 16 V1 entries (7 markets, 3 controllers, 2 init-code storage contracts among them); contexts are not deployed-address counts.
- **Excluded**: Wildcat V2 and v2.5 sources, `test/`, `script/` and `scripts/`. **External**: underlying ERC20 assets, the Chainalysis sanctions list, the SphereX engine, and controllers or markets named by callers at runtime.
- **Measured tree**: enumeration, git analysis and every `file:line` read the da74452a checkout; paths are relative to `src/` unless they start with `lib/`. This report describes code; it does not establish that the protocol is safe.

### Contracts in Scope

| Subsystem | Key Contracts | nSLOC | Role |
|-----------|--------------|------:|------|
| Markets | WildcatMarket, WildcatMarketBase, WildcatMarketConfig, WildcatMarketToken, WildcatMarketWithdrawals, ReentrancyGuard | 910 | Scaled balances, accrual, borrowing, withdrawal batches, sanctions blocking |
| Controllers and factory | WildcatMarketController, WildcatMarketControllerFactory | 806 | Per-borrower controller, market deployment, lender set, term bounds, fee configuration |
| Registry | WildcatArchController | 296 | Borrower, factory, controller, market and asset-blacklist registry; SphereX configuration |
| Sanctions | WildcatSanctionsSentinel, WildcatSanctionsEscrow | 113 | Chainalysis checks, borrower overrides, create2 escrows |
| SphereX protection | SphereXProtectedRegisteredBase, SphereXConfig, SphereXProtectedErrors, SphereXProtectedEvents | 343 | Engine slot, pre/post validation hooks, admin/operator roles |
| Libraries | MarketState, FeeMath, Withdrawal, FIFOQueue, MathUtils, SafeCastLib, LibStoredInitCode, StringQuery, MarketEvents, MarketErrors, Errors, BoolUtils | 1104 | State math, fees, batches, casting, init-code storage, events and errors |
| Read-only lens | MarketLens, MarketData, ControllerData, ArchControllerData, TokenData, SliceParameters | 653 | View aggregation |

The header's 4754 nSLOC is the enumerator total over all 46 `src/` files (run with GNU grep; the first run under macOS BSD grep reported 0, see evidence). The rows above sum to 4225; the remaining 529 nSLOC are interfaces (`src/interfaces/`, 500) and `spherex/ISphereXEngine.sol` (29). Vendored solady and OpenZeppelin code is excluded from nSLOC; the inherited solady `Ownable` actions are in the entry-point map.

### How It Fits Together

The core trick: one scale factor converts every lender's fixed scaled balance into a growing normalized claim, and withdrawal batches burn scaled supply only as assets are set aside for them.

### Deposit and borrow

```text
WildcatMarket.deposit / depositUpTo
├─ WildcatMarketBase._getUpdatedState()        ← accrue, settle expired batch, pay pending batch
├─ WildcatSanctionsSentinel.isSanctioned(borrower, caller)
│   └─ sanctioned: _blockAccount() → WildcatSanctionsSentinel.createEscrow()   *no role check; returns 0*
├─ asset.safeTransferFrom(caller → market)     *credits `amount` after the `maximumDeposit` cap, not the balance received*
├─ _getAccountWithRole(caller, DepositAndWithdraw) → WildcatMarketController.isAuthorizedLender()  *only while role is Null*
└─ scaledBalance += s; scaledTotalSupply += s → _writeState()   *isDelinquent recomputed*
WildcatMarket.borrow (borrower) → isFlaggedByChainalysis → borrowableAssets = totalAssets − liquidityRequired → safeTransfer
```

### Withdrawal batches

```text
WildcatMarket.queueWithdrawal
├─ scaledBalance −= s; batch.scaledTotalAmount += s; scaledPendingWithdrawals += s
├─ new batch expiry = now + withdrawalBatchDuration (one pending batch at a time)
└─ _applyWithdrawalBatchPayment()  *burns scaled supply, moves assets into normalizedUnclaimedWithdrawals*
[expiry passes] → next _getUpdatedState(): accrue to expiry → pay → unpaid remainder pushed to FIFO queue
WildcatMarket.executeWithdrawal (any caller)
└─ share = paid × scaledAmount / scaledTotalAmount (floor) → asset to account, or to its escrow if sanctioned
WildcatMarket.repayAndProcessUnpaidWithdrawalBatches → pays unpaid batches oldest first
```

### Controller and deployment

```text
WildcatMarketControllerFactory.deployController (registered borrower) → create2(salt = borrower) → WildcatArchController.registerController
WildcatMarketController.deployMarket (borrower or factory)
├─ isBlacklistedAsset / enforceParameterConstraints
├─ origination fee: safeTransferFrom(borrower → feeRecipient)
├─ create2 WildcatMarket  *constructor reads controller.getMarketParameters()*
└─ WildcatArchController.registerMarket → SphereX engine addAllowedSenderOnChain (if set)
WildcatMarketController.setAnnualInterestBips → (cut) temporary reserve ratio until reset or cancelled; reset allowed from 2 weeks after the latest renewing cut → WildcatMarket.setReserveRatioBips
```

### Sanctions and escrow

```text
WildcatMarket.nukeFromOrbit (any caller) → sentinel.isSanctioned → _blockAccount → createEscrow(borrower, account, market)
WildcatMarket.stunningReversal (any caller) → not sanctioned → Blocked → WithdrawOnly
WildcatSanctionsEscrow.releaseEscrow (any caller) → canReleaseEscrow → asset.safeTransfer(account, balance)
                                                   *market-token escrows need the account un-Blocked first*
```

---

## 2. Threat & Trust Model

### Protocol Threat Profile

> Protocol classified as: **Lending/Borrowing** (undercollateralised, fixed-rate credit) with **rebasing share-token** characteristics

Signals: `borrow`, three repayment paths, `annualInterestBips`, reserve ratio, delinquency fee and grace period; lender claims are scaled balances converted by a scale factor. No collateral, oracle price or liquidation exists, so oracle manipulation and liquidation MEV from the lending profile do not apply; credit risk sits with the named borrower.

### Actors & Adversary Model

| Actor | Trust Level | Capabilities |
|-------|-------------|-------------|
| Arch-controller owner | Trusted | Instant: register/remove borrowers, factories, controllers, markets; asset blacklist; fee configuration for new markets via the factory. `transferOwnership` is single-step; a 48-hour handover path also exists. No timelock. |
| SphereX admin | Trusted | Instant: appoint the operator, transfer admin (two-step), push the arch controller's engine to registered contracts. |
| SphereX operator | Trusted | Instant: set the arch controller's engine (interface-checked) and push it to listed registered contracts. |
| Borrower | Bounded (controller bounds on APR, fee, duration, ratio, grace; registered by owner) | Borrow up to `borrowableAssets`; APR changes within bounds (a cut raises the reserve ratio until it is reset or cancelled; reset is allowed from 2 weeks after the latest renewing cut); `maxTotalSupply` without a supply bound; lender set; closure; sanction overrides for its markets. |
| Lender | Bounded (borrower authorisation; `Blocked` by sanctions) | Deposit with `DepositAndWithdraw`; queue with `WithdrawOnly` or better; transfer market tokens while not `Blocked`. |
| Market controller (contract) | Bounded (immutable per market) | Only caller of market closure, APR, capacity, reserve ratio and authorisation setters. |
| Fee recipient | Bounded (immutable per market) | Receives `collectFees` proceeds; any caller triggers it. |

**Adversary Ranking**

1. **Borrower acting against lenders**: the named counterparty controls terms, lender admission, closure timing and sanction overrides for its own markets.
2. **Compromised arch-controller owner or SphereX admin/operator**: instant registry and engine powers reach every registered contract.
3. **Sanctioned or blocked account holders**: sanctions branches, escrows and reversals form a separate state machine reachable by any caller.
4. **Adversarial or non-standard underlying token**: any non-blacklisted ERC20 can back a market, and liquidity math trusts its `balanceOf`.
5. **Lender-versus-lender rounding and ordering**: batch settlement order and half-up conversions decide who absorbs dust and shortfalls.

See [entry-points.md](entry-points.md) for the full permissionless entry point map (21 permissionless, 25 role-gated, 16 admin-only, 7 creation).

### Trust Boundaries

- **Owner → registry**: no timelock; the worst instant action is removing borrowers, factories or controllers, which stops new deployments but leaves deployed markets running; a removed factory or controller can no longer receive engine updates, and a market only after `removeMarket` (`WildcatArchController.sol:126`, `:157-360`). *Git signal: access-control area touched by 73 commits.*
- **SphereX admin/operator → every registered contract**: no delay on `updateSphereXEngineOnRegisteredContracts` (`WildcatArchController.sol:73-114`); registered contracts accept the engine unvalidated (`spherex/SphereXProtectedRegisteredBase.sol:113-117`) and it gates every guarded call, including withdrawals and repayments.
- **Borrower → market terms**: controller bounds apply to APR and deployment parameters (`WildcatMarketController.sol:567-613`, `:694-699`), but `setMaxTotalSupply` is unbounded (`:637-645`) and the borrower's sentinel overrides apply to all its markets (`WildcatSanctionsSentinel.sol:96-107`).
- **Sentinel → Chainalysis list**: immutable oracle address (`WildcatSanctionsSentinel.sol:16`, `:77-79`); its answers decide blocking, escrow routing and release with no fallback.
- **Market → underlying asset**: `totalAssets()` is a raw `balanceOf` (`market/WildcatMarketBase.sol:251-271`); every liquidity and delinquency figure inherits the token's behaviour.

### Key Attack Surfaces

- **Sanctioned branch of the deposit path** &nbsp;&#91;[I-12](invariants.md#i-12), [G-3](invariants.md#g-3)&#93;: `WildcatMarket._depositUpTo:48-50` blocks the caller with no role check and returns 0, and `deposit:111-115` accepts that 0 when `amount == 0`. Worth confirming which callers are meant to reach this branch.

- **Controller lender set versus stored market roles** &nbsp;&#91;[X-1](invariants.md#x-1), [E-3](invariants.md#e-3)&#93;: `authorizeLenders`/`deauthorizeLenders` (`WildcatMarketController.sol:221-230`, `:308-317`) leave markets untouched, and markets re-read the set only for `Null` roles (`market/WildcatMarketBase.sol:200-204`). Worth tracing the window before `updateLenderAuthorization`.

- **Sanctions checks cover a subset of paths** &nbsp;&#91;[X-8](invariants.md#x-8), [I-11](invariants.md#i-11)&#93;: `_transfer` (`market/WildcatMarketToken.sol:71-89`) and `queueWithdrawal` (`market/WildcatMarketWithdrawals.sol:82-131`) check only the stored `Blocked` role. Worth tracing what a flagged but unblocked holder can still move.

- **Reversal grants `WithdrawOnly` without prior authorisation** &nbsp;&#91;[I-12](invariants.md#i-12), [I-11](invariants.md#i-11)&#93;: `stunningReversal` (`market/WildcatMarketConfig.sol:95-108`) differs from the NatSpec at `:116-120` for accounts that entered `Blocked` from `Null`. Worth confirming against the admission model.

- **Escrow creation and release ordering** &nbsp;&#91;[X-7](invariants.md#x-7), [I-33](invariants.md#i-33), [I-34](invariants.md#i-34)&#93;: `createEscrow` (`WildcatSanctionsSentinel.sol:121-142`) takes a caller-chosen borrower key, the borrower can clear an escrow's override (`:104-107`), and market-token releases need `stunningReversal` first. Worth tracing escrow liveness.

- **Temporary reserve-ratio lifecycle** &nbsp;&#91;[X-2](invariants.md#x-2), [I-26](invariants.md#i-26), [I-27](invariants.md#i-27), [I-8](invariants.md#i-8)&#93;: `setAnnualInterestBips` keeps an elapsed `tmp.expiry` when the new rate is at or above the current one (`WildcatMarketController.sol:737-739`), and both restore paths hit G-21. Worth checking the ratio's lifetime under delinquency.

- **Batch settlement ordering and rounding** &nbsp;&#91;[I-2](invariants.md#i-2), [I-4](invariants.md#i-4), [I-21](invariants.md#i-21), [I-23](invariants.md#i-23), [E-2](invariants.md#e-2)&#93;: `_getUpdatedState` (`market/WildcatMarketBase.sol:414-475`) settles an expired batch at its expiry rate, then accrues to now; a pending batch is paid only in an update where no batch expired; conversions round half-up (`libraries/MathUtils.sol:138-166`). Worth tracing scale/normalize round trips at batch boundaries.

- **Delinquency interval attribution** &nbsp;&#91;[I-17](invariants.md#i-17), [I-18](invariants.md#i-18)&#93;: `updateTimeDelinquentAndGetPenaltyTime` (`libraries/FeeMath.sol:89-123`) applies the stored flag to the whole elapsed interval, refreshed only by state writes such as permissionless `updateState`. Worth checking how call timing shifts penalty time.

- **Fee seniority over queued withdrawals** &nbsp;&#91;[E-4](invariants.md#e-4), [I-22](invariants.md#i-22), [G-32](invariants.md#g-32)&#93;: `availableLiquidityForPendingBatch` (`libraries/Withdrawal.sol:47-59`) reserves accrued fees ahead of batch amounts, and `collectFees` (`market/WildcatMarket.sol:121-134`) is permissionless. Worth confirming the intended priority when assets are short.

- **SphereX admin/operator compromise** &nbsp;&#91;[X-9](invariants.md#x-9), [G-74](invariants.md#g-74), [G-75](invariants.md#g-75)&#93;: an installed engine runs before and after every guarded function (`spherex/SphereXProtectedRegisteredBase.sol:151-272`) and can revert it; installation takes effect at once, with no delay. Worth scoping what an engine can block or observe.

- **Arch-controller owner operational powers**: registry, blacklist and fee-configuration actions are instant (`WildcatArchController.sol:157-360`, `WildcatMarketControllerFactory.sol:212-241`), and `transferOwnership` is single-step (`lib/solady/src/auth/Ownable.sol:136`).

- **Arbitrary underlying assets** &nbsp;&#91;[G-17](invariants.md#g-17)&#93;: `deployMarket` (`WildcatMarketController.sol:447-533`) accepts any non-blacklisted ERC20 and deposits credit `amount` after the `maximumDeposit` cap, not the balance actually received (`market/WildcatMarket.sol:57-78`). Worth checking fee-on-transfer, rebasing and blocklisting behaviour against the liquidity math.

- **Closure settlement** &nbsp;&#91;[I-10](invariants.md#i-10), [G-12](invariants.md#g-12), [I-6](invariants.md#i-6)&#93;: `closeMarket` (`market/WildcatMarket.sol:217-242`) pulls any shortfall from the borrower by `transferFrom` or returns the excess, then zeroes APR and sets a 100% reserve. Worth tracing a pending unexpired batch across closure.

- **Lens read paths** &nbsp;&#91;[X-12](invariants.md#x-12)&#93;: `MarketLens` pins one factory at construction (`lens/MarketLens.sol:13-18`), and `getPaginatedArchControllerData` passes `SliceParameters(0, 0)` whatever its arguments (`:36-57`), returning empty lists. Worth confirming integrators do not rely on either.

### Upgrade Architecture Concerns

- **No proxy or upgrade path**: every context is deployed as immutable bytecode; the only post-deployment behavioural hook is each contract's SphereX engine slot (X-9).

### Protocol-Type Concerns

**As a Lending/Borrowing protocol:**
- Interest is linear within an interval and compounds only at state writes (`libraries/MathUtils.sol:30-39`, `libraries/FeeMath.sol:142-173`), so scale growth depends on update frequency.
- The protocol fee is charged on base interest over the whole scaled supply, including amounts pending withdrawal, at the pre-update scale factor (`libraries/FeeMath.sol:40-51`).
- With no collateral or liquidation, the only on-chain enforcement is the delinquency fee after `delinquencyGracePeriod` (`libraries/FeeMath.sol:53-71`).

**As a rebasing share token** *(secondary)*:
- `balanceOf` normalizes with half-up `rayMul` (`market/WildcatMarketToken.sol:16-21`) and transfers re-scale with half-up `rayDiv` (`:73`); worth checking full-balance transfers and queues at boundary scale factors.

### Temporal Risk Profile

**Deployment & Initialization:**
- `WildcatArchController` starts with SphereX operator and engine at `address(0)` (`WildcatArchController.sol:61`); engine management needs the admin to appoint an operator first.
- The factory copies the arch engine once at construction (`WildcatMarketControllerFactory.sol:100`); later engine changes need an explicit push (X-9).
- `MarketLens` construction reverts unless exactly one factory is registered (`lens/MarketLens.sol:16`).

**Market Stress:**
- Expired shortfalls queue FIFO (`market/WildcatMarketBase.sol:589-590`) and block closure (G-12); the only pressure on the borrower is the delinquency fee.

**Deprecation:**
- Registry removal leaves markets live (`WildcatArchController.sol:355-360`) and outside engine updates (G-52); lender allowances and escrow balances persist with no forced migration.

### Composability & Dependency Risks

**Dependency Risk Map:**

> **Underlying ERC20**, via `WildcatMarket` deposits, `borrow`, repayments, `collectFees`, executions, `closeMarket`, `totalAssets()`
> - Assumes: exact-amount transfers; balance changes only through transfers; 32-byte `balanceOf`
> - Validates: solady `SafeTransferLib` return handling; `totalAssets()` return size (G-17)
> - Mutability: defined by the token
> - On failure: revert

> **Chainalysis sanctions list**, via `WildcatSanctionsSentinel.isFlaggedByChainalysis` / `isSanctioned`
> - Assumes: accurate, available `isSanctioned(address)`
> - Validates: NONE
> - Mutability: external list; address immutable in the sentinel
> - On failure: revert of every path that consults the sentinel (deposits, `borrow`, executions, blocking, reversal, escrow release)

> **SphereX engine**, via `sphereXGuardExternal` on markets, controllers and factory; `addAllowedSenderOnChain` from the arch controller
> - Assumes: engine answers with a 32-byte-headed slot array and accepts post-validation
> - Validates: `supportsInterface` on the arch controller only (G-72)
> - Mutability: SphereX operator/admin, instant
> - On failure: revert (fail-closed) of the guarded call

> **Asset metadata**, via `queryName`/`querySymbol` (`libraries/StringQuery.sol:33-104`) and `decimals()` at market construction
> - Assumes: string or bytes32 name/symbol of at most 32 bytes
> - Validates: return size (`:47-61`)
> - Mutability: defined by the token
> - On failure: `deployMarket` reverts

**Token Assumptions** *(unvalidated only)*:
- Fee-on-transfer tokens: assumes received = sent; impact if violated: scaled claims exceed `totalAssets()` from the first deposit (`market/WildcatMarket.sol:64-78`).
- Rebasing or balance-reducing tokens: assumes `balanceOf` moves only by transfers; impact if violated: delinquency and batch payments follow the token's balance (`market/WildcatMarketBase.sol:251-271`).
- Blocklisting tokens: assumes transfers to lenders succeed; impact if violated: `executeWithdrawal` reverts for a token-blocklisted, sentinel-unsanctioned lender (`market/WildcatMarketWithdrawals.sol:219`).

**Shared State Exposure**:
- All markets share one sentinel and therefore one Chainalysis oracle; registered contracts share whatever engine the operator pushes.

---

## 3. Invariants

> ### Full invariant map: **[invariants.md](invariants.md)**
>
> A dedicated reference file contains the complete invariant analysis; do not look here for the catalog.
>
> - **78 Enforced Guards** (`G-1` … `G-78`): per-call preconditions with `Check` / `Location` / `Purpose`
> - **35 Single-Contract Invariants** (`I-1` … `I-35`): Conservation, Bound, Ratio, StateMachine, Temporal
> - **12 Cross-Contract Invariants** (`X-1` … `X-12`): caller/callee pairs that cross scope boundaries
> - **4 Economic Invariants** (`E-1` … `E-4`): higher-order properties deriving from `I-N` + `X-N`
>
> Every inferred block cites a concrete Δ-pair, guard-lift + write-sites, state edge, temporal predicate, or NatSpec quote. The **On-chain=No** blocks (12) are the high-signal ones; each is simultaneously an invariant and a potential bug. Attack-surface bullets above cross-link directly into the relevant blocks.

---

## 4. Documentation Quality

| Aspect | Status | Notes |
|--------|--------|-------|
| README | Present | `README.md` (137 lines): early design notes and a cloc table naming files absent at da74452a (for example `src/Escrow.sol`, `src/MarketLens.sol`); no claims from it are used here |
| NatSpec | ~264 tags | Source-read count of `@notice/@dev/@param/@return/@title/@author`; the enumerator's figure (46) counts files, not tags. Densest in `market/WildcatMarketBase.sol` (37); no `@invariant` tags |
| Spec/Whitepaper | Missing | No spec in the repository |
| Inline Comments | Adequate | Market, fee and controller logic explain intent; registry and lens are sparse. The arch controller does not inherit `IWildcatArchController`: six of the interface's ten registry event declarations match what it emits, `MarketAdded` and `ControllerAdded` differ only in `indexed`, and `AssetBlacklisted()`/`AssetPermitted()` never occur because the emitted versions take an address |

---

## 5. Test Analysis

| Metric | Value | Source |
|--------|-------|--------|
| Test files | 51 | File scan (always reliable) |
| Test functions | 370 | File scan (always reliable) |
| Line coverage | Unavailable: default `forge coverage` compiled (Solc 0.8.28) then failed in solar analysis: unresolved symbol `locals` at `src/spherex/SphereXProtectedRegisteredBase.sol:153:39` | Coverage tool (requires compilation) |
| Branch coverage | Unavailable: `forge coverage --ir-minimum` failed to compile: Yul stack too deep by 1 slot at `test/helpers/ExpectedBalances.sol:710` | Coverage tool (requires compilation) |

51 test files with 370 test functions detected; coverage metrics unavailable because both attempts failed (evidence: `evidence/coverage-default.log`, `evidence/coverage-ir-minimum.log`). Coverage failure does not mean tests are absent.

### Test Depth

| Category | Count | Contracts Covered |
|----------|-------|-------------------|
| Unit | 370 (all `test*` functions) | Broad: controller (46), withdrawals (38), market (32), arch controller (32), config (29), libraries, lens, sentinel, escrow, SphereX config |
| Integration | 6 | `WildcatArchControllerIntegration.t.sol` (source read) |
| Stateless Fuzz | 8 | `testFuzz*` in `EscrowTest.sol` (5) and `SentinelTest.sol` (3); source read also finds 83 parameterised `test*` functions in 13 files that the enumerator does not count |
| Stateful Fuzz (Foundry) | 8 | Enumerator count; source read: the 3 live `invariant_` functions (`test/InvariantTests.sol`) target a solmate `MockERC20` handler, and the other 5 matches are commented out |
| Stateful Fuzz (Echidna) | 0 | none |
| Stateful Fuzz (Medusa) | 0 | none |
| Formal Verification (Certora) | 0 | none |
| Formal Verification (Halmos) | 0 | none |
| Formal Verification (HEVM) | 0 | none |

### Gaps

- No stateful invariant campaign targets a Wildcat contract (source read of `test/InvariantTests.sol`); the conservation properties I-1 to I-4 are not exercised as invariants.
- No formal verification (Certora, Halmos, HEVM all 0) for the scale-factor and batch arithmetic.
- No fork tests (0); line and branch coverage not measured on this host.

---

## 6. Developer & Git History

> Repo shape: normal_dev: 660 commits (365 touching `src/`) from 2022-06-29 to 2023-11-30. Analyzed branch: `detached HEAD` at `da74452` (`da74452aa7d1a0f024d99efd22cc6d950a8116b7`). Sentinel commit `6164ddd4c75ef6da2181e5623b99795b9829e31c` descends from it and changes only licence lines; it was not analysed separately.

### Contributors

| Author | Commits | Source Lines (+/-) | % of Source Changes |
|--------|--------:|--------------------|--------------------:|
| d1ll0n | 487 | +21357 / -15308 | 89.1% |
| Dr Laurence E. Day | 150 | +2479 / -1294 | 10.3% |
| jtriley.eth | 1 | +136 / -0 | 0.6% |
| Dillon Kellar | 22 | +0 / -0 | 0.0% |

Line counts and percentages are the enumerator's `src/` numstat over all history, including files later deleted; the git analysis script reports d1ll0n at 87.2% of source lines added. Single-developer dominance: one identity authored about 89% of source additions.

### Review & Process Signals

| Signal | Value | Assessment |
|--------|-------|------------|
| Unique contributors | 4 | Small team (4 author identities) |
| Merge commits | 34 of 660 (5.2%) | Some pull-request merges; most commits land directly |
| Repo age | 2022-06-29 → 2023-11-30 | 519 days |
| Recent source activity (30d before HEAD) | 92 commits | Late burst: 81 of 92 without test-file changes |
| Test co-change rate | 14.8% | Share of source-changing commits that also modify test files (co-modification, not coverage) |

### File Hotspots

| File | Modifications | Note |
|------|-------------:|------|
| `src/market/WildcatMarketBase.sol` | 44 | Accrual, batch processing, blocking |
| `src/market/WildcatMarketWithdrawals.sol` | 34 | Queue, execution, unpaid batches |
| `src/market/WildcatMarket.sol` | 33 | Deposit, borrow, repay, close |
| `src/market/WildcatMarketConfig.sol` | 30 | Sanctions and setters |
| `src/WildcatMarketController.sol` | 22 | Deployment, lender set, temporary reserve ratio |
| `src/WildcatSanctionsSentinel.sol` | 13 | Overrides and escrows |
| `src/market/WildcatMarketToken.sol` | 12 | Transfers |

Counts are per path over all history (enumerator `git_hotspots`); the top path overall, `src/WMVault.sol` (50), no longer exists at HEAD.

### Security-Relevant Commits

**Score** = weighted sum of fix-like signals in a commit: message keywords, diff patterns (deletes code, changes guards, touches access control or accounting) and change shape. **10+ warrants a manual diff.**

| SHA | Date | Subject | Score | Key Signal |
|-----|------|---------|------:|------------|
| 5a17f02 | 2023-11-29 | rm SphereX wrapped ReentrancyGuard and Ownable | 17 | removes runtime guards; loosens access control (files since deleted) |
| 980c194 | 2023-11-14 | Update temporary reserve ratio rules. fixes #64, resolves issues from #56 | 14 | bug fix in `WildcatMarketController.sol`; includes tests |
| 95c8129 | 2023-11-29 | Inherit SphereXProtectedRegisteredBase and original ReentrancyGuard, add arch controller query | 13 | 3 security domains in `WildcatMarketBase.sol`; no test change |
| 255d932 | 2023-11-28 | add reentrancy guard with minimal spherex | 13 | security language; file since deleted |
| 054d194 | 2023-08-31 | fix return params for _calculateCurrentState. rm use of increase/decrease fns | 12 | bug fix in `WildcatMarketToken.sol`; no test change |
| 30d57b1 | 2023-08-31 | move most of the withdrawal library into WildcatMarketWithdrawals | 12 | fund-flow restructuring; no test change |
| 3e0d7af | 2023-09-28 | fix transfer to wrong address | 11 | bug fix in `WildcatMarketWithdrawals.sol`; no test change |
| a295565 | 2023-11-30 | lint:fix | 11 | broad touch incl. sentinel and escrow; includes tests |

### Dangerous Area Evolution

| Security Area | Commits | Key Files |
|--------------|--------:|-----------|
| fund_flows | 127 | `WildcatMarketController.sol`, `market/WildcatMarket.sol`, `market/WildcatMarketWithdrawals.sol` |
| state_machines | 100 | `market/WildcatMarketBase.sol`, `market/WildcatMarketConfig.sol`, `lens/MarketData.sol` |
| access_control | 73 | `WildcatArchController.sol`, `WildcatMarketController.sol`, `spherex/SphereXConfig.sol` |
| signatures | 6 | `libraries/MathUtils.sol` (keyword match; no signature verification exists in scope) |

### Forked Dependencies

| Library | Path | Upstream | Status | Notes |
|---------|------|----------|--------|-------|
| SphereX protected base | `src/spherex/` | SphereX `SphereXProtectedBase` | Internalized | Modified: admin removed, arch controller fixed as operator, engine unvalidated on registered contracts (`SphereXProtectedRegisteredBase.sol:9-21`); detected by source read, not by the script |
| ReentrancyGuard | `src/ReentrancyGuard.sol` | Seaport (0age) | Internalized | Modifier and constants added (`:4-11`) |
| solady, OpenZeppelin | `lib/solady`, `lib/openzeppelin-contracts` | Solady v0.0.124, OZ v4.9.3 | Submodule | `Ownable`, `SafeTransferLib`, `LibBit`, `EnumerableSet` used; script notes only pragma-range differences |

### Technical Debt Markers

| File:Line | Type | Text | Author | Date |
|-----------|------|------|--------|------|
| `src/libraries/FIFOQueue.sol:10` | @todo | make array tightly packed for gas efficiency | d1ll0n | 2023-08-09 |
| `src/spherex/SphereXProtectedRegisteredBase.sol:213` | @todo | could put `valuesBefore` before `storageSlots` and reuse | d1ll0n | 2023-11-27 |

The git analysis script reported 0 markers (it matches upper-case tags); both lower-case `@todo` notes above are gas or memory-layout notes found by source read.

### Security Observations

- **Single-developer concentration**: d1ll0n authored 89.1% of source additions (enumerator numstat).
- **Late burst before HEAD**: 92 source commits in the final 30 days, 81 without test changes, including SphereX integration and `609ab9d` (removed the `maxTotalSupply >= totalSupply` check).
- **Guard and access-control churn**: `5a17f02` (score 17) and `95c8129` (13) swapped reentrancy and ownership wrappers on 2023-11-29, the day before HEAD.
- **Hotspots are the market core**: the four `market/` files hold 141 of the listed modifications.
- **Fix commits without test changes**: script `fix_without_test_rate` 0.8 (file co-modification, not coverage).
- **Internalized SphereX fork**: `src/spherex/` diverges from upstream by design; upstream fixes do not propagate.

### Cross-Reference Synthesis

- **`WildcatMarketBase.sol` is the top current hotspot (44) and hosts I-1, I-2, I-4, I-12 and I-18** → accrual and blocking logic is the highest-leverage review target.
- **`980c194` (temporary reserve-ratio rules) + late `609ab9d` (capacity bound removed)** → X-2, I-26 and I-9 cover the controller paths most recently rewritten.
- **SphereX integration landed in the final four days (`f78f376` 2023-11-27 → `a5c5ea1` 2023-11-30)** → the engine surface (X-9, G-74, G-75) has the least history behind it.
- **`22c2eb6` removed the registered-market requirement for escrow creation** → `createEscrow` is permissionless (I-34), feeding the escrow-ordering surface.

---

## X-Ray Verdict

**FRAGILE**: roles and boundaries are explicit, but every owner, SphereX and borrower operation executes instantly with no timelock or pause, which caps the access-control signal.

Tier inputs: Tests ADEQUATE or better by enumeration (unit + stateless fuzz + 8 `invariant_` matches; the live invariants target a mock token); Docs ADEQUATE (NatSpec present, no spec); Access Control FRAGILE (roles exist, no timelock). The two `@todo` notes are not in security-critical logic, so no tier drop.

**Structural facts:**
1. 4754 nSLOC across 46 `src/` files (4225 outside interfaces) in 7 subsystems; 7 concrete contexts with 62 state-changing and 7 creation actions.
2. 0 proxies; the only mutable behavioural hook after deployment is each contract's SphereX engine slot.
3. 51 test files and 370 test functions; both coverage attempts failed to produce metrics.
4. One author identity wrote 89.1% of source additions; 34 of 660 commits are merges.
5. 92 source-touching commits in the 30 days before HEAD, 81 of them without test-file changes.
