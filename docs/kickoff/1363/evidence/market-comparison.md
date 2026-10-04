# Market source comparison

Pinned reads: deployed `f5a26146987926f4811b72a795d662813dedfe85`; candidate `bea503c2736d47de7fd34130c64f10783dc35b39`. Every location below belongs to the named pin. This is source-extraction evidence, not an audit verdict.

| Coverage | Deployed | Candidate |
| --- | ---: | ---: |
| Market files / source lines | 5 / 1,714 | 6 / 2,430 |
| Function declarations, including helpers/views | 70 | 104 |
| Direct state-changing public/external definitions | 20 | 26 |
| Runtime actions after inheritance | 37 | 85 |
| Constructors, excluded from callable count | 1 | 2 |

Both pins also inherit `changeSphereXEngine(address)` (`0x4c6c848f`), gated by the immutable ArchController: deployed `src/spherex/SphereXProtectedRegisteredBase.sol:113`; candidate `src/spherex/SphereXProtectedRegisteredBase.sol:109`.

| Added candidate selector | Definition | Runtime context |
| --- | --- | --- |
| `requestBorrowerTransfer(address)` / `0xde4d1558` | `src/market/WildcatMarketBase.sol:474` | Base and every derived market contract |
| `cancelBorrowerTransfer()` / `0xc40944c7` | `src/market/WildcatMarketBase.sol:496` | Base and every derived market contract |
| `acceptBorrowerTransfer()` / `0x90c14376` | `src/market/WildcatMarketBase.sol:513` | Base and every derived market contract |
| `registerWrapper(address)` / `0xd2595f1d` | `src/market/WildcatMarketConfig.sol:63` | Config, Market, Revolving |
| `executePendingAnnualInterestBipsReduction()` / `0x09b70bc7` | `src/market/WildcatMarketConfig.sol:202` | Config, Market, Revolving |
| `queueWithdrawalScaled(uint256)` / `0x5ee883f8` | `src/market/WildcatMarketWithdrawals.sol:184` | Withdrawals, Market, Revolving |

- `nukeFromOrbit(address)` (`0xdcd549d4`) calls empty Base `_blockAccount` in Config-only runtime and the balance-queueing override in full Market runtime. Candidate Revolving inherits the full override. Deployed: `src/market/WildcatMarketBase.sol:393`, `src/market/WildcatMarket.sol:298`; candidate: `src/market/WildcatMarketBase.sol:661`, `src/market/WildcatMarket.sol:280`.
- Candidate Revolving adds no mutating selector. Its overrides affect inherited borrow (`0xc5ebeaec`), repay (`0x371fd8e6`), combined repay/process (`0x6731ba6d`), close (`0xc511ed5e`) and accrual paths. `DrawnAmountUpdated` occurs only when `_drawnAmount` changes. Candidate: `src/market/WildcatMarketRevolving.sol:82`, `:98`, `:113`, `:118`, `:173`.
- Candidate separates operational borrower from principal. Borrower authority reads the operational address; lender sanctions and escrow creation use the current principal. Deployed uses immutable borrower. Deployed: `src/market/WildcatMarketBase.sol:49`, `:254`, `:754`; candidate: `src/market/WildcatMarketBase.sol:175`, `:180`, `:348`, `:553`, `:1113`. Repayment payer and withdrawal executor remain separate identities.
- Candidate deposits, transfers and normalized withdrawal queues use floor conversion; settlement uses `maxScaledSettleable` and skips zero burn. Deployed uses `scaleAmount`. Deployed: `src/market/WildcatMarket.sol:67`, `src/market/WildcatMarketToken.sol:79`, `src/market/WildcatMarketWithdrawals.sol:139`, `src/market/WildcatMarketBase.sol:661`; candidate: the corresponding files at `:55`, `:98`, `:169`, `:1016`.
- Candidate stores a capped asset checkpoint for pending batches and uses it on expiry before recomputing delinquency. Deployed expiry uses current assets. Deployed: `src/market/WildcatMarketBase.sol:616`; candidate: `src/market/WildcatMarketBase.sol:745`, `:748`, `:868`, `:965`.
- Candidate execute-withdrawal hook includes expiry; deployed hook does not. Forced sanctions queues and multi-execute supply empty hook extraData at both pins. Deployed: `src/types/HooksConfig.sol:382`, `src/market/WildcatMarket.sol:305`, `src/market/WildcatMarketWithdrawals.sol:223`; candidate: `src/types/HooksConfig.sol:431`, `src/market/WildcatMarket.sol:292`, `src/market/WildcatMarketWithdrawals.sol:278`.
- Candidate changes Borrow, MarketClosed, FeesCollected and term-update event ABIs; JSON event catalogs match assembly topics to declarations. Deployed: `src/libraries/MarketEvents.sol:31`, `:45`, `:52`, `:91`, `:105`, `:112`; candidate: `src/libraries/MarketEvents.sol:31`, `:48`, `:65`, `:111`, `:133`, `:140`.

Root joins still required: exact hook authorization/return semantics, sentinel escrow event effects, identity-registry guarantees, wrapper-factory validation and ERC20/SphereX external effects. `registerWrapper` itself checks caller and empty stored slot but accepts zero; its factory path needs the cross-system disposition (`candidate src/market/WildcatMarketConfig.sol:64`). All local event paths, conditional branches, source digests and action dispositions are in the two market-facts JSON files. Constructors and external-event uncertainty are explicit. AST compilation supplies enumeration only; these files claim no passing runtime tests.
