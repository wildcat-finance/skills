# X-Ray Report

> Wildcat V2 | 7522 nSLOC | f5a2614 (`detached HEAD`) | Foundry | 26/09/26

## 1. Protocol Overview

What it does: Wildcat markets lend underlying ERC20 assets to an admitted borrower while accounting for transferable, interest-bearing lender claims and queued withdrawals.

- Users: Lenders supply and transfer claims; the borrower draws liquidity and funds repayments; executors can update accounting and claim paid withdrawals.
- Core flow: Deposit → borrow/repay → queue scaled claims → settle a batch → execute a normalized payment.
- Key mechanism: Scaled balances share an accrual factor; hook callbacks impose admission and term policy.
- Token model: The market token rebases through its scale factor; Wildcat4626Wrapper issues non-rebasing shares backed by market-token scaled balances.
- Admin model: ArchController ownership governs registration. Separate SphereX admin/operator slots govern protection configuration; ownership transfer does not transfer those roles. Borrower and hooks authority govern market and access operations.

See the [architecture diagram](architecture.svg). This is the accepted deployed-comparison commit. Only the verification inputs named by the target ledger are matched to deployed evidence; the entire commit is not certified as every deployed market.

### Contracts in Scope

| Subsystem | Key contracts | nSLOC | Role |
| --- | --- | ---: | --- |
| Hooks and factories | HooksFactory; OpenTermHooks / FixedTermHooks | 1821 | Deployment, admission and term policy |
| Registry, sanctions and guards | WildcatArchController / SanctionsSentinel / SanctionsEscrow; ReentrancyGuard / SphereX | 864 | Registration, custody, identity and execution gates |
| Read-only lenses | MarketLens | 830 | Read-only derived views |
| Libraries and types | FeeMath / MarketState / MarketEvents / HooksConfig | 2239 | Accounting, dispatch and typed state |
| Markets | WildcatMarket / Base / Config / Token / Withdrawals | 1009 | Scaled balances, accrual, borrowing and withdrawals |
| Wrappers | Wildcat4626Wrapper / Wildcat4626WrapperFactory | 316 | Non-rebasing shares of market-token claims |

The header retains the enumerator's exact 7522 nSLOC across all 62 source files. The subsystem rows exclude interface-only declarations; their 443 nSLOC remain in the source manifest and enumeration evidence. Vendored dependencies are outside those totals; inherited Solady actions are included in the callable map.

### How it fits together

The core trick: a lender's scaled claim persists while accrued interest changes its normalized value; batch payment burns the scaled debt and reserves a normalized withdrawal claim.

### Deposit and transfer

```text
WildcatMarket.deposit → _depositUpTo → OpenTermHooks / FixedTermHooks.onDeposit
├─ asset.transferFrom(caller, market) — underlying moves before the paired scaled-account/supply writes
└─ WildcatMarketToken.transfer → hook.onTransfer → scaled from/to balance writes
```

### Withdrawal and sanctions

```text
queueWithdrawal → hook.onQueueWithdrawal → account balance becomes queued scaled debt
├─ _applyWithdrawalBatchPayment → burn scaled supply and reserve normalized claims
└─ executeWithdrawal → hook.onExecuteWithdrawal → claimant or WildcatSanctionsEscrow
```

### Wrapping

```text
Wildcat4626Wrapper.deposit / mint → WildcatMarketToken.transferFrom → measured scaled balance change
└─ withdraw / redeem → burn wrapper shares → WildcatMarketToken.transfer
```

### Deployment

```text
HooksFactory → stored template/initcode → hook.onCreateMarket → market constructor
└─ WildcatArchController.registerMarket → factory discovery events
```

Stored initcode must be bound separately before assigning the named constructor to a deployed address.

## 2. Threat & Trust Model

### Protocol threat profile

> **Uncollateralized lending** with **tokenized claim wrapping** and **external admission-policy hooks**.

There is no collateral liquidation price oracle in the reviewed lending core; sanctions and credentials are separate external data dependencies.

### Actors & Adversary Model

| Actor | Trust level | Capabilities |
| --- | --- | --- |
| Lender / market-token holder | Bounded by balances, sanctions and hooks | Deposits, transfers and queues claims; timing and access checks constrain withdrawal paths. |
| Borrower | Bounded market authority | Draws available liquidity, changes terms and closes a funded market; operational setters have no timelock. |
| ArchController owner | Trusted registration authority | Changes registered actors/factories immediately; ownership handover expiry is not an action delay. |
| SphereX admin / operator | Separate protection authorities | Admin changes the operator; operator changes the engine; either can propagate the engine to registered contracts. Ownable transfers do not change these slots. |
| Hooks borrower | Trusted admission-policy authority | Manages providers and lender restrictions; named term setters add their own conditions. |
| Registered role provider | Bounded credential authority | Grants/revokes access; pull and validation responses cross a separate code boundary. |
| Withdrawal executor / repayment payer | Bounded by destination and accounting | May act for another claimant or repay another borrower's market; receives no arbitrary claim destination. |

The market borrower is immutable; the hooks borrower is fixed at hook creation and controls its provider and market-policy setters. Source code does not establish live signer arrangements, multisig membership or external engine policy.

See [entry-points.md](entry-points.md) for the complete permissionless and restricted action maps.

**Adversary ranking**

1. Borrower or privileged-account compromise: those actors control credit drawdown, registration or lender-admission policy.
2. Lender or token operator: balance movement and withdrawal timing meet shared accounting.
3. External hook, credential or token implementation: the market relies on code and return values outside its own storage.
4. Transaction scheduler: block timing and action order determine batch expiry and accrued state.

### Trust Boundaries

- Borrower authority: [src/market/WildcatMarket.sol:146](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L146) permits immediate borrowing within source-defined reserves; repayment capacity remains an external credit question.
- Registration and engines: Owner-controlled registration is separate from SphereX configuration roles in [src/spherex/SphereXConfig.sol:141](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXConfig.sol#L141). These setters have no operational delay; SphereX callbacks can reject guarded actions at [src/spherex/SphereXProtectedRegisteredBase.sol:282](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXProtectedRegisteredBase.sol#L282).
- Admission and terms: [src/access/BaseAccessControls.sol:712](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L712) accepts credentials through configured providers; term hooks also constrain forced sanctions queues.
- Custody: [src/market/WildcatMarketWithdrawals.sol:230](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L230) separates the caller, claimant and possible escrow recipient.

No common protocol pause modifier was found on the reviewed action set; closure and external SphereX rejection have distinct, narrower semantics.

### Key attack surfaces

- **Scaled-account and batch settlement** [I-1](invariants.md#i-1), [I-2](invariants.md#i-2), [I-3](invariants.md#i-3): [src/market/WildcatMarketBase.sol:406](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L406) crosses accrual, batch expiry and claim reservations; trace the rounding at each conversion.

- **Wrapper and market rounding** [X-2](invariants.md#x-2): [src/vault/Wildcat4626Wrapper.sol:216](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L216) measures market-token movement around share issuance; compare previews, transfers and redemption paths.

- **Hook configuration and remembered access** [I-5](invariants.md#i-5), [I-7](invariants.md#i-7), [I-8](invariants.md#i-8): [src/access/OpenTermHooks.sol:175](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L175) stores minimums separately from callback configuration; check creation and later administration together.

- **Sanctions custody and term policy** [X-1](invariants.md#x-1): [src/market/WildcatMarket.sol:298](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L298) uses the ordinary queue hook before custody can move to escrow.

- **Temporary reserve timing** [I-6](invariants.md#i-6): [src/access/MarketConstraintHooks.sol:204](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/MarketConstraintHooks.sol#L204) changes caller-keyed temporary reserves only when an APR callback executes.

### Protocol-Type Concerns

- Finite accrual fields: FeeMath stores scaleFactor in uint112 and timestamps in uint32; [src/libraries/FeeMath.sol:1](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/FeeMath.sol#L1) supplies the arithmetic, while lifetime estimates in specifications remain spec claims.
- Explicit payment versus liquidity: [src/market/WildcatMarket.sol:188](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L188) emits DebtRepaid for an explicit payer action; a raw ERC20 donation has different attribution.

### Temporal risk profile

- Initialization: [src/market/WildcatMarketBase.sol:157](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L157) reads construction parameters from its caller; deployed factory/initcode identity must come from separate evidence.
- **Closure** [I-4](invariants.md#i-4): [src/market/WildcatMarket.sol:212](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L212) settles queued scaled debt and fixes the closed-state rates before later claims continue.

### Composability & Dependency Risks

> Underlying ERC20: via LibERC20 and the market.
> - Assumes: balances and transfer amounts describe the accounting asset; fee-on-transfer or rebasing behavior is not normalized by an actual-received deposit check.
> - Validates: low-level call success and return shape; token availability and mutable implementation remain external.
> - On failure: the call reverts and its logs roll back.

> Hook and credential implementations: via HooksConfig and BaseAccessControls.
> - Assumes: configured addresses implement the intended admission/term behavior.
> - Validates: enabled callback return shape and local policy checks; pull probes have explicit fallback behavior.
> - On failure: callback revert rejects the host action; credential paths can try another provider according to the cited implementation.

> Sanctions list: via WildcatSanctionsSentinel.
> - Assumes: external list responses represent the desired sanctions policy.
> - Validates: local borrower/principal override namespace; raw borrower checks bypass those overrides.
> - On failure: the relevant read or action reverts.

> SphereX engine: via SphereXProtectedRegisteredBase.
> - Assumes: the configured external engine implements pre/post validation.
> - Mutability: ArchController controls the engine target; a zero engine bypasses its validation path.
> - On failure: a guarded operation reverts; other actions do not acquire a general pause.

## 3. Invariants

> [Full invariant map](invariants.md): 176 enforced guards; 8 single-contract properties; 2 cross-contract properties; 1 economic property. Each inferred block names its source derivation and enforcement limit.

## 4. Documentation Quality

| Aspect | Status | Notes |
| --- | --- | --- |
| README | Present | Repository orientation; it does not establish deployed code equality. |
| NatSpec | 419 annotation markers detected | Count over src files; presence is separate from correctness. |
| Specifications | Present | Fresh extraction and source hashes retained in doc-inputs and the role extraction record. |
| Inline comments | Present | Accounting, packed state and assembly intent are documented; claims were checked against source before promotion. |

Core-Behavior.md says a supply cap stops withdrawals, while Terminology.md and deposit code apply it to deposits; treat that sentence as a documentation conflict. Source-only event mapping retains emitter and canonical ABI topics; off-chain role attribution still needs the accepted event-decision and deployment evidence.

## 5. Test Analysis

| Metric | Value | Source |
| --- | --- | --- |
| Test files | 72 | File enumeration |
| Test functions | 602 | File enumeration |
| Line coverage | Unavailable | Default Solar analysis and --ir-minimum Yul compilation failed |
| Branch coverage | Unavailable | No completed coverage execution |

### Test Depth

| Category | Count | Evidence limit |
| --- | ---: | --- |
| Test functions (unit/integration not individually partitioned) | 602 | Names detected, no pass claim |
| Stateless fuzz | 21 | Function-name scan |
| Foundry invariants | 8 | Function-name scan |
| Formal verification | 0 | No Certora/Halmos/HEVM signals in the prescribed scan |

### Gaps

- No Echidna/Medusa, formal-verification or fork-test signals were detected by the prescribed enumeration.
- Coverage cannot be quantified: default Solar analysis reports an unresolved locals symbol at src/spherex/SphereXProtectedRegisteredBase.sol:153:39; the IR fallback reports a three-slot var_market Yul stack excess. Exact commands and logs are retained.

## 6. Developer & Git History

> Normal development history: 592 source-touching commits among 1093 ancestors of detached HEAD `f5a26146987926f4811b72a795d662813dedfe85`, spanning 1512 days.

### Contributors

| Recorded author name | All-history commits | Source lines added | Share of source additions |
| --- | ---: | ---: | ---: |
| d1ll0n | 869 | +28854 | 89.9% |
| Dr Laurence E. Day | 179 | +2610 | 8.1% |
| Jack | 1 | +486 | 1.5% |
| jtriley.eth | 1 | +136 | 0.4% |
| Tim Clancy | 1 | +15 | 0.0% |

Names are Git author labels, not verified people; identical names from several email identities are aggregated here. Source-addition shares and all-history commit counts have different denominators.

### Review & Process Signals

| Signal | Value | Interpretation |
| --- | --- | --- |
| Merge commits | 69 of 1093 | Merge topology does not prove independent review |
| History dates | 2022-06-29 → 2026-08-19 | Ancestors of this pin only |
| Source activity in final 30-day window | 0 | Window ends at the pin's latest commit |
| Test co-change | 15.2% | Source commits that also change test files; not coverage |
| Fix-scored commits without test-file changes | 70.0% | Heuristic subset; not proof of absent tests |

### File Hotspots

| Current file | Modifications | Scope |
| --- | ---: | --- |
| src/market/WildcatMarketBase.sol | 67 | Current source path; historical modifications |
| src/market/WildcatMarket.sol | 64 | Current source path; historical modifications |
| src/market/WildcatMarketWithdrawals.sol | 56 | Current source path; historical modifications |
| src/market/WildcatMarketConfig.sol | 49 | Current source path; historical modifications |
| src/interfaces/IMarketEventsAndErrors.sol | 25 | Current source path; historical modifications |

### Security-Relevant Commits

The script scores message/diff features for navigation; historical subjects do not establish a present vulnerability or completed repair. The full scored list is retained with the pin.

| Commit | Date | Historical subject | Score | Leading script signal |
| --- | --- | --- | ---: | --- |
| [5a17f02](https://github.com/wildcat-finance/v2-protocol/commit/5a17f02dd9deee930f57bbe100efb7386f90b2a2) | 2023-11-29 | rm SphereX wrapped ReentrancyGuard and Ownable | 17 | explicit security language |
| [cbfa7c3](https://github.com/wildcat-finance/v2-protocol/commit/cbfa7c387e38cfab7ba0366f9f6af9971025c869) | 2025-02-04 | Remove minimumDeposit & allow closure before term if allowTermReduction enabled | 13 | unclassified |
| [b7e2f23](https://github.com/wildcat-finance/v2-protocol/commit/b7e2f234b2a887146cd5df5054a43435d89ee7a0) | 2024-08-29 | map markets to their hooks templates, add slice query for hooks templates and add bulk update function for protocol fees | 13 | unclassified |
| [a8409c5](https://github.com/wildcat-finance/v2-protocol/commit/a8409c5ec6fcf15edfad57eda78682f58e8278c0) | 2024-03-30 | Temporary fixes to get code to compile | 13 | bug fix |
| [95c8129](https://github.com/wildcat-finance/v2-protocol/commit/95c81293c8672d90343a616913626bd93ae41c64) | 2023-11-29 | Inherit SphereXProtectedRegisteredBase and original ReentrancyGuard, add arch controller query | 13 | explicit security language |
| [255d932](https://github.com/wildcat-finance/v2-protocol/commit/255d932dcecc5a0504b45d59ebedd2cc62f01526) | 2023-11-28 | add reentrancy guard with minimal spherex | 13 | explicit security language |
| [c7be403](https://github.com/wildcat-finance/v2-protocol/commit/c7be4039f8f383a9dda4e45f63331c17d63f9ed9) | 2026-04-01 | feat(4626-wrapper): 4626 style market debt token wrapper | 12 | feature addition |
| [054d194](https://github.com/wildcat-finance/v2-protocol/commit/054d194703393ba66480bf741b5a92f4c15af59f) | 2023-08-31 | fix return params for _calculateCurrentState. rm use of increase/decrease fns | 12 | bug fix |

### Dangerous area evolution

| Heuristic area | Commits | Example paths |
| --- | ---: | --- |
| access_control | 101 | src/HooksFactory.sol, src/WildcatArchController.sol, src/access/BaseAccessControls.sol |
| fund_flows | 202 | src/HooksFactory.sol, src/IHooksFactory.sol, src/WildcatSanctionsEscrow.sol |
| signatures | 78 | src/access/IRoleProvider.sol, src/libraries/MathUtils.sol, src/market/WildcatMarketBase.sol |
| state_machines | 180 | src/access/BaseAccessControls.sol, src/access/FixedTermHooks.sol, src/access/OpenTermHooks.sol |

Keyword matches under oracle/liquidation headings are not evidence that this credit core implements a price oracle or liquidation mechanism.

### Forked Dependencies

The pin includes 6 Git submodules. Inherited Solady Ownable/ERC20 behavior is read and hash-bound. LibERC20 is an internalized transfer helper and SphereX is adapted source; mixed pragma scans alone do not establish a departure from upstream behavior.

The debt-marker scan found zero uppercase markers; that does not mean there are no lowercase todo comments or unresolved design questions.

### Security Observations

- Source concentration: d1ll0n accounts for 89.9% of recorded source additions.
- Recent activity: 0 source commits fall in the final 30-day window; 0 omit a test-file change in the same commit.
- Accounting history: MarketBase and withdrawal source remain among the current-file hotspots.
- Evidence separation: neither merge counts nor fix-scored subjects establish review completion or deployed behavior.

### Cross-Reference Synthesis

- Accounting priority: repeated MarketBase/Withdrawals edits coincide with the scaled settlement and claim paths in I-1 through I-3.
- Access priority: hook/provider and engine change history supplies reading order for the documented trust boundaries.
- Execution limit: the detected tests inform the structural rubric; failed coverage remains an independent tool result.

## X-Ray Verdict

FRAGILE: The source-only rubric rates the access layer as FRAGILE because roles exist without a protocol-enforced operational timelock.

This tier describes the template's structural evidence rubric; it is not a security, deployment or credit-solvency verdict. Tests reach its HARDENED presence threshold, documentation includes specifications, and live multisig arrangements were not established.

Structural facts:

1. 62 source files contain 7522 enumerated nSLOC.
2. The source action inventory contains 141 callable contract/signature contexts and 13 separate constructors.
3. The scan detects 602 test functions, 21 stateless fuzz functions and 8 Foundry invariant functions.
4. Both attempted coverage modes fail before producing coverage metrics.
