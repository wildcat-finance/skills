# X-Ray Report

> Wildcat V2 | 13621 nSLOC | bea503c (`detached HEAD`) | Foundry | 26/09/26

## 1. Protocol Overview

What it does: Wildcat markets lend underlying ERC20 assets to an admitted borrower while accounting for transferable, interest-bearing lender claims and queued withdrawals.

- Users: Lenders supply and transfer claims; the borrower draws liquidity and funds repayments; executors can update accounting and claim paid withdrawals.
- Core flow: Deposit → borrow/repay → queue scaled claims → settle a batch → execute a normalized payment.
- Key mechanism: Scaled balances share an accrual factor; hook callbacks impose admission and term policy.
- Token model: The market token rebases through its scale factor; Wildcat4626Wrapper issues non-rebasing shares backed by market-token scaled balances.
- Admin model: ArchController ownership governs registration. Separate SphereX admin/operator slots govern protection configuration; ownership transfer does not transfer those roles. Borrower and hooks authority govern market and access operations.

See the [architecture diagram](architecture.svg). Named candidate verification inputs match these source bytes; candidate mainnet deployment is not established by the input ledger.

### Contracts in Scope

| Subsystem | Key contracts | nSLOC | Role |
| --- | --- | ---: | --- |
| Hooks and factories | HooksFactory / HooksFactoryRevolving; OpenTermHooks / FixedTermHooks / PeriodicTermHooks | 3595 | Deployment, admission and term policy |
| Registry, sanctions and guards | WildcatArchController / SanctionsSentinel / SanctionsEscrow / BorrowerIdentityRegistry; ReentrancyGuard / SphereX | 1160 | Registration, custody, identity and execution gates |
| Read-only lenses | MarketLens / Core / Live / Aggregator | 1939 | Read-only derived views |
| Libraries and types | FeeMath / MarketState / MarketEvents / HooksConfig | 2450 | Accounting, dispatch and typed state |
| Markets | WildcatMarket / Base / Config / Token / Withdrawals / Revolving | 1488 | Scaled balances, accrual, borrowing and withdrawals |
| Providers | AccessList / Merkle / token role providers and factories | 943 | Credential eligibility and administration |
| Wrappers | Wildcat4626Wrapper / Wildcat4626WrapperFactory | 736 | Non-rebasing shares of market-token claims |

The header retains the enumerator's exact 13621 nSLOC across all 108 source files. The subsystem rows exclude interface-only declarations; their 1310 nSLOC remain in the source manifest and enumeration evidence. Vendored dependencies are outside those totals; inherited Solady actions are included in the callable map.

### How it fits together

The core trick: a lender's scaled claim persists while accrued interest changes its normalized value; batch payment burns the scaled debt and reserves a normalized withdrawal claim.

### Deposit and transfer

```text
WildcatMarket.deposit → _depositUpTo → OpenTermHooks / FixedTermHooks / PeriodicTermHooks.onDeposit
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
HooksFactory / HooksFactoryRevolving → stored template/initcode → hook.onCreateMarket → market constructor
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
| Hooks administrator | Trusted admission-policy authority | Manages providers and lender restrictions; named term setters add their own conditions. |
| Registered role provider | Bounded credential authority | Grants/revokes access; pull and validation responses cross a separate code boundary. |
| Withdrawal executor / repayment payer | Bounded by destination and accounting | May act for another claimant or repay another borrower's market; receives no arbitrary claim destination. |

Operational borrower, registered principal, hooks administrator and registry-account administrator are separate authorities. Source code does not establish live signer arrangements, multisig membership or external engine policy.

See [entry-points.md](entry-points.md) for the complete permissionless and restricted action maps.

**Adversary ranking**

1. Borrower or privileged-account compromise: those actors control credit drawdown, registration or lender-admission policy.
2. Lender or token operator: balance movement and withdrawal timing meet shared accounting.
3. External hook, credential or token implementation: the market relies on code and return values outside its own storage.
4. Transaction scheduler: block timing and action order determine batch expiry and accrued state.

### Trust Boundaries

- Borrower authority: [src/market/WildcatMarket.sol:118](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L118) permits immediate borrowing within source-defined reserves; repayment capacity remains an external credit question.
- Registration and engines: Owner-controlled registration is separate from SphereX configuration roles in [src/spherex/SphereXConfig.sol:142](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXConfig.sol#L142). These setters have no operational delay; SphereX callbacks can reject guarded actions at [src/spherex/SphereXProtectedRegisteredBase.sol:278](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXProtectedRegisteredBase.sol#L278).
- Admission and terms: [src/access/BaseAccessControls.sol:940](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L940) accepts credentials through configured providers; term hooks also constrain forced sanctions queues.
- Custody: [src/market/WildcatMarketWithdrawals.sol:286](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L286) separates the caller, claimant and possible escrow recipient.

No common protocol pause modifier was found on the reviewed action set; closure and external SphereX rejection have distinct, narrower semantics.

### Key attack surfaces

- **Scaled-account and batch settlement** [I-1](invariants.md#i-1), [I-2](invariants.md#i-2), [I-3](invariants.md#i-3): [src/market/WildcatMarketBase.sol:722](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L722) crosses accrual, batch expiry and claim reservations; trace the rounding at each conversion.

- **Wrapper and market rounding** [X-2](invariants.md#x-2): [src/vault/Wildcat4626Wrapper.sol:316](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L316) measures market-token movement around share issuance; compare previews, transfers and redemption paths.

- **Hook configuration and remembered access** [I-5](invariants.md#i-5), [I-7](invariants.md#i-7), [I-8](invariants.md#i-8): [src/access/OpenTermHooks.sol:189](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L189) stores minimums separately from callback configuration; check creation and later administration together.

- **Sanctions custody and term policy** [X-1](invariants.md#x-1): [src/market/WildcatMarket.sol:280](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L280) uses the ordinary queue hook before custody can move to escrow.

- **Temporary reserve timing** [I-6](invariants.md#i-6): [src/access/MarketConstraintHooks.sol:196](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/MarketConstraintHooks.sol#L196) changes caller-keyed temporary reserves only when an APR callback executes.

- **Borrower transfer and identity** [I-10](invariants.md#i-10): [src/market/WildcatMarketBase.sol:384](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L384) resolves the pending principal again; compare registry changes with existing market and escrow identity.

- **Revolving debt attribution** [I-2](invariants.md#i-2): [src/market/WildcatMarketRevolving.sol:98](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketRevolving.sol#L98) distinguishes explicit repayment from donated liquidity; trace inherited accrual and close paths.

- Periodic timing policy: [src/access/PeriodicTermHooks.sol:140](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L140) retains four mainnet duration decisions; review their relation to withdrawal windows and delayed APR activation.

### Protocol-Type Concerns

- Finite accrual fields: FeeMath stores scaleFactor in uint112 and timestamps in uint32; [src/libraries/FeeMath.sol:1](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/FeeMath.sol#L1) supplies the arithmetic, while lifetime estimates in specifications remain spec claims.
- Explicit payment versus liquidity: [src/market/WildcatMarket.sol:163](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L163) emits DebtRepaid for an explicit payer action; a raw ERC20 donation has different attribution.

### Temporal risk profile

- Initialization: [src/market/WildcatMarketBase.sol:235](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L235) reads construction parameters from its caller; deployed factory/initcode identity must come from separate evidence.
- **Closure** [I-4](invariants.md#i-4): [src/market/WildcatMarket.sol:183](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L183) settles queued scaled debt and fixes the closed-state rates before later claims continue.

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

> [Full invariant map](invariants.md): 375 enforced guards; 10 single-contract properties; 3 cross-contract properties; 1 economic property. Each inferred block names its source derivation and enforcement limit.

## 4. Documentation Quality

| Aspect | Status | Notes |
| --- | --- | --- |
| README | Present | Repository orientation; it does not establish deployed code equality. |
| NatSpec | 2124 annotation markers detected | Count over src files; presence is separate from correctness. |
| Specifications | Present | Fresh extraction and source hashes retained in doc-inputs and the role extraction record. |
| Inline comments | Present | Accounting, packed state and assembly intent are documented; claims were checked against source before promotion. |

Candidate specifications document floor rounding, identity and event attribution; the recorded audit-scope freeze differs from this commit, and complete finding/retest lineage was not reconstructed. Source-only event mapping retains emitter and canonical ABI topics; off-chain role attribution still needs the accepted event-decision and deployment evidence.

## 5. Test Analysis

| Metric | Value | Source |
| --- | --- | --- |
| Test files | 82 | File enumeration |
| Test functions | 698 | File enumeration |
| Line coverage | Unavailable | Default solc compilation and --ir-minimum Yul compilation failed |
| Branch coverage | Unavailable | No completed coverage execution |

### Test Depth

| Category | Count | Evidence limit |
| --- | ---: | --- |
| Test functions (unit/integration not individually partitioned) | 698 | Names detected, no pass claim |
| Stateless fuzz | 31 | Function-name scan |
| Foundry invariants | 9 | Function-name scan |
| Formal verification | 0 | No Certora/Halmos/HEVM signals in the prescribed scan |

### Gaps

- No Echidna/Medusa, formal-verification or fork-test signals were detected by the prescribed enumeration.
- Coverage cannot be quantified: default compilation reports Stack too deep at script/deploy/v2-5/02-deploy-hooks-factory-standard.s.sol:342; the IR fallback reports a six-slot var_deployments/var_result Yul stack excess. Exact commands and logs are retained.

## 6. Developer & Git History

> Normal development history: 715 source-touching commits among 1428 ancestors of detached HEAD `bea503c2736d47de7fd34130c64f10783dc35b39`, spanning 1529 days.

### Contributors

| Recorded author name | All-history commits | Source lines added | Share of source additions |
| --- | ---: | ---: | ---: |
| d1ll0n | 871 | +29210 | 61.0% |
| Dave Coleman | 281 | +14756 | 30.8% |
| Dr Laurence E. Day | 177 | +2610 | 5.5% |
| Jack McSweeney | 10 | +653 | 1.4% |
| Jack | 4 | +486 | 1.0% |
| jtriley.eth | 1 | +136 | 0.3% |
| Tim Clancy | 1 | +15 | 0.0% |

Names are Git author labels, not verified people; identical names from several email identities are aggregated here. Source-addition shares and all-history commit counts have different denominators.

### Review & Process Signals

| Signal | Value | Interpretation |
| --- | --- | --- |
| Merge commits | 112 of 1428 | Merge topology does not prove independent review |
| History dates | 2022-06-29 → 2026-09-05 | Ancestors of this pin only |
| Source activity in final 30-day window | 67 | Window ends at the pin's latest commit |
| Test co-change | 26.2% | Source commits that also change test files; not coverage |
| Fix-scored commits without test-file changes | 10.0% | Heuristic subset; not proof of absent tests |

### File Hotspots

| Current file | Modifications | Scope |
| --- | ---: | --- |
| src/market/WildcatMarketBase.sol | 89 | Current source path; historical modifications |
| src/market/WildcatMarket.sol | 75 | Current source path; historical modifications |
| src/market/WildcatMarketWithdrawals.sol | 67 | Current source path; historical modifications |
| src/market/WildcatMarketConfig.sol | 58 | Current source path; historical modifications |
| src/interfaces/IMarketEventsAndErrors.sol | 38 | Current source path; historical modifications |
| src/HooksFactory.sol | 36 | Current source path; historical modifications |
| src/IHooksFactory.sol | 28 | Current source path; historical modifications |

### Security-Relevant Commits

The script scores message/diff features for navigation; historical subjects do not establish a present vulnerability or completed repair. The full scored list is retained with the pin.

| Commit | Date | Historical subject | Score | Leading script signal |
| --- | --- | --- | ---: | --- |
| [fa3b76c](https://github.com/wildcat-finance/v2-protocol/commit/fa3b76c4db20f796e7697ce01c20cf71623d736e) | 2026-07-13 | fix: 4626 wrapped shares escrowed on sanction | 17 | bug fix |
| [5a17f02](https://github.com/wildcat-finance/v2-protocol/commit/5a17f02dd9deee930f57bbe100efb7386f90b2a2) | 2023-11-29 | rm SphereX wrapped ReentrancyGuard and Ownable | 17 | explicit security language |
| [66dc10d](https://github.com/wildcat-finance/v2-protocol/commit/66dc10d1a74d02836172783b18959f74addc7029) | 2026-09-03 | fix(market): reject overflowing withdrawal expiries | 15 | explicit security language |
| [8eb2e86](https://github.com/wildcat-finance/v2-protocol/commit/8eb2e86293faabb56d475f741d3873814cddc209) | 2026-08-15 | fix: A-01 remediation | 15 | bug fix |
| [9eeb8f8](https://github.com/wildcat-finance/v2-protocol/commit/9eeb8f895a4bc315cfbf2d8584beb8e3b986687f) | 2026-08-15 | audit: fix proposals | 14 | bug fix |
| [7c5deb6](https://github.com/wildcat-finance/v2-protocol/commit/7c5deb6b59c9ccc176390048edca5d86521f3f02) | 2026-07-14 | fix: 4626 sanction fix, more deploy scripting | 14 | bug fix |
| [8caf671](https://github.com/wildcat-finance/v2-protocol/commit/8caf671a8c594169da12ca0c4af6e44630aae5fc) | 2026-07-13 | fix: withdrawals at close batch expiry can misallocate repay capital | 14 | bug fix |
| [f2e83a7](https://github.com/wildcat-finance/v2-protocol/commit/f2e83a729d646813e92965bce604246e053b6493) | 2026-07-07 | fix: 4626 roudning issues | 14 | bug fix |

### Dangerous area evolution

| Heuristic area | Commits | Example paths |
| --- | ---: | --- |
| access_control | 167 | src/HooksFactory.sol, src/HooksFactoryRevolving.sol, src/WildcatArchController.sol |
| fund_flows | 291 | src/HooksFactory.sol, src/HooksFactoryRevolving.sol, src/IHooksFactory.sol |
| signatures | 172 | src/HooksFactory.sol, src/HooksFactoryRevolving.sol, src/IHooksFactory.sol |
| state_machines | 245 | src/access/BaseAccessControls.sol, src/access/FixedTermHooks.sol, src/access/OpenTermHooks.sol |

Keyword matches under oracle/liquidation headings are not evidence that this credit core implements a price oracle or liquidation mechanism.

### Forked Dependencies

The pin includes 3 Git submodules. Inherited Solady Ownable/ERC20 behavior is read and hash-bound. LibERC20 is an internalized transfer helper and SphereX is adapted source; mixed pragma scans alone do not establish a departure from upstream behavior.

### Technical debt markers

| Source | Marker | Text |
| --- | --- | --- |
| [src/access/PeriodicTermHooks.sol:140](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L140) | TODO | FOR MAINNET: Finalize the minimum period duration with the team. |
| [src/access/PeriodicTermHooks.sol:143](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L143) | TODO | FOR MAINNET: Finalize the maximum period duration with the team. |
| [src/access/PeriodicTermHooks.sol:146](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L146) | TODO | FOR MAINNET: Finalize the minimum withdrawal window duration with the team. |
| [src/access/PeriodicTermHooks.sol:149](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L149) | TODO | FOR MAINNET: Finalize the maximum initial withdrawal window delay with the team. |

### Security Observations

- Source concentration: d1ll0n accounts for 61.0% of recorded source additions.
- Recent activity: 67 source commits fall in the final 30-day window; 11 omit a test-file change in the same commit.
- Accounting history: MarketBase and withdrawal source remain among the current-file hotspots.
- Evidence separation: neither merge counts nor fix-scored subjects establish review completion or deployed behavior.

### Cross-Reference Synthesis

- Accounting priority: repeated MarketBase/Withdrawals edits coincide with the scaled settlement and claim paths in I-1 through I-3.
- Access priority: hook/provider and engine change history supplies reading order for the documented trust boundaries.
- Execution limit: the detected tests inform the structural rubric; failed coverage remains an independent tool result.

## X-Ray Verdict

EXPOSED: The source-only rubric rates roles without an operational timelock as FRAGILE, then lowers one tier for four unresolved timing-policy TODOs.

This tier describes the template's structural evidence rubric; it is not a security, deployment or credit-solvency verdict. Tests reach its HARDENED presence threshold, documentation includes specifications, and live multisig arrangements were not established.

Structural facts:

1. 108 source files contain 13621 enumerated nSLOC.
2. The source action inventory contains 269 callable contract/signature contexts and 29 separate constructors.
3. The scan detects 698 test functions, 31 stateless fuzz functions and 9 Foundry invariant functions.
4. Both attempted coverage modes fail before producing coverage metrics.
