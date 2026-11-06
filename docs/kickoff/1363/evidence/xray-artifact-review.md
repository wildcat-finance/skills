# Issue 1363 artifact review

Status: changes required. This reviews the staged X-Ray artifacts; it is not a Fiat Warden receipt.
## Checks

Both compiler action inventories reconcile: 141 deployed and 269 candidate actions. Source hashes cover all 62/108 Solidity files, and all 551 guard predicates match their cited source.
All 121 distinct retained event signature/topic pairs recompute with cast keccak. Final-byte review remains pending while the producer revises the bundle.

## Limits

Coverage: all action IDs, source-file hashes, quoted guards and retained event topics were checked. Source semantics were reviewed through the action rows, raw facts and targeted source reads covering the reported corrections, I-1 through I-10 write sites, borrower transfer, market-token accounting, wrapper accounting and provider authority. This is an artifact review, not exhaustive security testing. Both initial diagrams were visually readable without clipped nodes; their revised bytes need another inspection. Final execution, manifest and literal-diff records were still being assembled and have no approval in this record.

## Findings

[High] F1: Concrete market-creation callbacks are incorrectly marked eventless.
Location: IHooks.onCreateMarket dispatches to OpenTermHooks, FixedTermHooks and PeriodicTermHooks; source details and all 5 action IDs are in the machine record.
Mechanism: The helper traversal stops at the abstract declaration before resolving the runtime override.
Impact: MinimumDepositUpdated, FixedTermUpdated and PeriodicTermUpdated disappear from the action rows.
Fix: Resolve the virtual override, retain its conditions and emitter context, and reconcile factory joins.

[Medium] F2: The readiness reports give the ArchController owner separate SphereX powers.
Location: candidate src/WildcatArchController.sol:99; src/spherex/SphereXConfig.sol:142 and src/spherex/SphereXConfig.sol:150; the deployed pin has the same role split.
Mechanism: Ownable owner, SphereX admin and SphereX operator use independent storage; ownership transfer does not move the SphereX roles.
Impact: The actor table attributes engine changes to the wrong authority.
Fix: Name registry ownership and SphereX admin/operator authority separately, including diagram actor labels.

[Medium] F3: The deployed default coverage failure is misreported.
Location: deployed x-ray/coverage.log; src/spherex/SphereXProtectedRegisteredBase.sol:153.
Mechanism: Default coverage fails Solar analysis on unresolved symbol locals; only the IR fallback reports Yul stack depth.
Impact: The report obscures the recorded failure and the execution record could inherit that error.
Fix: Record default Solar failure and the 3-slot IR failure separately; candidate default is solc stack depth and candidate IR is 6-slot Yul depth.

[Medium] F4: Queue-hook effects omit term restrictions and describe a reverted credential clear as persistent.
Location: deployed src/access/FixedTermHooks.sol:306; candidate src/access/FixedTermHooks.sol:371 and src/access/PeriodicTermHooks.sol:580; all 5 queue callbacks need the persistence correction.
Mechanism: Fixed-term queueing requires maturity; periodic queueing requires an open window unless closed. Failed credential validation reverts the outer callback.
Impact: The map understates successful-call conditions and overstates durable credential changes.
Fix: Apply the role-specific replacement text in the machine record and retain only successful refresh/grant effects.

[Medium] F5: I-1 uses an intermediate storage-write boundary.
Location: candidate src/market/WildcatMarket.sol:66 and src/market/WildcatMarket.sol:73; deployed src/market/WildcatMarket.sol:78 and src/market/WildcatMarket.sol:85.
Mechanism: Account storage is written before aggregate state is persisted.
Impact: The identity does not hold after every individual write.
Fix: State the identity at completion of each successful external call, after paired account and aggregate writes.

[Medium] F6: Inherited Solady citations use the protocol repository for gitlink contents.
Location: both entry-points.md files; lib/solady/src/auth/Ownable.sol:154 and lib/solady/src/tokens/ERC20.sol:193.
Mechanism: The protocol commit stores a gitlink rather than those nested blobs.
Impact: The rendered source links cannot resolve to the cited source bytes.
Fix: Link Vectorized/solady at submodule commit 2ba1cc1eaa3bffd5c093d94f76ef1b87b167ff3c.

[Low] F7: Several flow labels and the APR execution flag need precision.
Location: both entry-points.md flow sections; candidate src/types/HooksConfig.sol:291 and src/market/WildcatMarketConfig.sol:202.
Mechanism: The provider calls hook.grantRole; the user calls the market before the periodic hook; dedicated APR execution has its own flag. Repayment methods are alternative funding paths.
Impact: The abbreviated paths can imply the wrong call target, required predecessor or enabled callback.
Fix: Name both sides of callback calls, use Bit_Enabled_ExecutePendingAnnualInterestBipsReduction, and branch repay versus repayAndProcessUnpaidWithdrawalBatches.

[Medium] F8: One semantic-change reason cites an unreachable local difference.
Location: comparison.json, HooksFactory:pushProtocolFeeBipsUpdates(address); deployed src/HooksFactory.sol:673 and candidate src/HooksFactory.sol:878.
Mechanism: This overload always supplies start=0; the new invalid-range branch cannot run, and returning before an empty loop adds no access, effect, value-flow or event change.
Impact: The stated evidence does not support this changed classification.
Fix: Mark the local wrapper unchanged, or cite the changed named market callee with its conditional scope and both source locations.
