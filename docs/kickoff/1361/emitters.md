# Emitter declarations

Schema `wildcat.emitter-declarations.v1`. Source `wildcat-finance/v2-protocol` at commit `f5a26146987926f4811b72a795d662813dedfe85`; compiler output at `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` (tag `v2.0.0`).

Mismatch classes: `topic0`, `log-arity`, `indexed-order`, `data-length`, `data-order`, `parameter-count`, `anonymous-declared`; a class found against a build's ABI is prefixed `abi:<contract>:`.

## Regenerating this table

```sh
python3 scripts/emitter_declarations.py build --from-git <clone> --out docs/kickoff/1361/emitters.json --markdown docs/kickoff/1361/emitters.md
```

Verify without writing:

```sh
python3 scripts/emitter_declarations.py check --from-git <clone> --table docs/kickoff/1361/emitters.json
```

## Scope and limits

This is a static text comparison of source declarations, assembly emitters and compiler ABI output. It runs no target code and makes no claim about runtime behaviour, deployed bytecode identity or capture completeness. The Fizz differential harness landed in [PR #1601](https://github.com/wildcat-finance/skills/pull/1601) is supplemental runtime evidence for the emitters it covers, never proof for this table.

The deployed market and factory take their SphereX event declarations from `SphereXProtectedRegisteredBase.sol`, not from `SphereXConfig.sol`. `SphereXConfig.sol` enters only the MarketLens build and the V2 tree's `WildcatArchController.sol`, which is not the deployed arch controller.

## Builds

| Contract | Address | Standard input SHA-256 | Output SHA-256 |
| --- | --- | --- | --- |
| WildcatMarket | `0xac3216fa28f81b8fae150fb5626ca79c7a570daf` | `f9a92fe4072d8f44406448377730c4b38b908571fa3db6b8ff3a81719e801346` | `d1a748bff6dec5a52571e432288d967fe40b9787b98b223fe68a6b812d4b8281` |
| HooksFactory | `0xdd7dd3b5076cf89440d05585ff56d246386207be` | `63dabbfdd5b7c140c314a0892baa639e217b0a15b20a51e604ecd2bd10ad4309` | `fea058a27a5bea99ceb4032ad711b285247ade23ff56efca2361114e1e256598` |

## Summary

| Count | Value |
| --- | --- |
| abi_checked_rows | 32 |
| binding_differs | [] |
| compared_rows | 38 |
| declarations_without_emitter | 48 |
| emitters | 27 |
| mismatch_rows | 0 |
| rows | 38 |
| unreviewed | 0 |

## Rows

| Emitter | Declaration | Signature | topic0 | logN | Indexed | Data bytes | ABI checked | Reached by | Status | Classes | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `emit_Transfer` (src/libraries/MarketEvents.sol:11) | `IERC20.Transfer` (src/interfaces/IERC20.sol:5) | `Transfer(address,address,uint256)` | `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` | 3 | [0, 1] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_Transfer` (src/libraries/MarketEvents.sol:11) | `IMarketEventsAndErrors.Transfer` (src/interfaces/IMarketEventsAndErrors.sol:81) | `Transfer(address,address,uint256)` | `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` | 3 | [0, 1] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_Approval` (src/libraries/MarketEvents.sol:18) | `IERC20.Approval` (src/interfaces/IERC20.sol:6) | `Approval(address,address,uint256)` | `0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925` | 3 | [0, 1] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_Approval` (src/libraries/MarketEvents.sol:18) | `IMarketEventsAndErrors.Approval` (src/interfaces/IMarketEventsAndErrors.sol:83) | `Approval(address,address,uint256)` | `0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925` | 3 | [0, 1] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_MaxTotalSupplyUpdated` (src/libraries/MarketEvents.sol:31) | `IMarketEventsAndErrors.MaxTotalSupplyUpdated` (src/interfaces/IMarketEventsAndErrors.sol:85) | `MaxTotalSupplyUpdated(uint256)` | `0xf2672935fc79f5237559e2e2999dbe743bf65430894ac2b37666890e7c69e1af` | 1 | [] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_ProtocolFeeBipsUpdated` (src/libraries/MarketEvents.sol:38) | `IMarketEventsAndErrors.ProtocolFeeBipsUpdated` (src/interfaces/IMarketEventsAndErrors.sol:87) | `ProtocolFeeBipsUpdated(uint256)` | `0x4b34705283cdb9398d0e50b216b8fb424c6d4def5db9bfadc661ee3adc6076ee` | 1 | [] | 32 | WildcatMarket | none | compared | none | called from no bound deployed build |
| `emit_AnnualInterestBipsUpdated` (src/libraries/MarketEvents.sol:45) | `IMarketEventsAndErrors.AnnualInterestBipsUpdated` (src/interfaces/IMarketEventsAndErrors.sol:89) | `AnnualInterestBipsUpdated(uint256)` | `0xff7b6c8be373823323d3c5d99f5d027dd409dce5db54eae511bbdd5546b75037` | 1 | [] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_ReserveRatioBipsUpdated` (src/libraries/MarketEvents.sol:52) | `IMarketEventsAndErrors.ReserveRatioBipsUpdated` (src/interfaces/IMarketEventsAndErrors.sol:91) | `ReserveRatioBipsUpdated(uint256)` | `0x72877a153052500f5edbb2f9da96a0f45d671d4b4555fdf8628a709dc4eab43a` | 1 | [] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_SanctionedAccountAssetsSentToEscrow` (src/libraries/MarketEvents.sol:59) | `IMarketEventsAndErrors.SanctionedAccountAssetsSentToEscrow` (src/interfaces/IMarketEventsAndErrors.sol:93) | `SanctionedAccountAssetsSentToEscrow(address,address,uint256)` | `0x571e706c2f09ae0632313e5f3ae89fffdedfc370a2ea59a07fb0d8091147645b` | 2 | [0] | 64 | WildcatMarket | none | compared | none | called from no bound deployed build; sub-word values `escrow` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_SanctionedAccountAssetsQueuedForWithdrawal` (src/libraries/MarketEvents.sol:67) | `IMarketEventsAndErrors.SanctionedAccountAssetsQueuedForWithdrawal` (src/interfaces/IMarketEventsAndErrors.sol:99) | `SanctionedAccountAssetsQueuedForWithdrawal(address,uint256,uint256,uint256)` | `0xe12b220b92469ae28fb0d79de531f94161431be9f073b96b8aad3effb88be6fa` | 2 | [0] | 96 | WildcatMarket | WildcatMarket | compared | none | emitter parameter `expiry` is `uint32` where the declaration says `uint256`; recorded, not graded; sub-word values `expiry` (`uint32`) are written by mstore as full words; their cleaning is not graded |
| `emit_Deposit` (src/libraries/MarketEvents.sol:83) | `IMarketEventsAndErrors.Deposit` (src/interfaces/IMarketEventsAndErrors.sol:106) | `Deposit(address,uint256,uint256)` | `0x90890809c654f11d6e72a28fa60149770a0d11ec6c92319d6ceb2bb0a4ea1a15` | 2 | [0] | 64 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_Borrow` (src/libraries/MarketEvents.sol:91) | `IMarketEventsAndErrors.Borrow` (src/interfaces/IMarketEventsAndErrors.sol:108) | `Borrow(uint256)` | `0xb848ae6b1253b6cb77e81464128ce8bd94d3d524fea54e801e0da869784dca33` | 1 | [] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_DebtRepaid` (src/libraries/MarketEvents.sol:98) | `IMarketEventsAndErrors.DebtRepaid` (src/interfaces/IMarketEventsAndErrors.sol:110) | `DebtRepaid(address,uint256)` | `0xe8b606ac1e5df7657db58d297ca8f41c090fc94c5fd2d6958f043e41736e9fa6` | 2 | [0] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_MarketClosed` (src/libraries/MarketEvents.sol:105) | `IMarketEventsAndErrors.MarketClosed` (src/interfaces/IMarketEventsAndErrors.sol:112) | `MarketClosed(uint256)` | `0x9dc30b8eda31a6a144e092e5de600955523a6a925cc15cc1d1b9b4872cfa6155` | 1 | [] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_FeesCollected` (src/libraries/MarketEvents.sol:112) | `IMarketEventsAndErrors.FeesCollected` (src/interfaces/IMarketEventsAndErrors.sol:114) | `FeesCollected(uint256)` | `0x860c0aa5520013080c2f65981705fcdea474d9f7c3daf954656ed5e65d692d1f` | 1 | [] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_StateUpdated` (src/libraries/MarketEvents.sol:119) | `IMarketEventsAndErrors.StateUpdated` (src/interfaces/IMarketEventsAndErrors.sol:116) | `StateUpdated(uint256,bool)` | `0x9385f9ff65bcd2fb81cece54b27d4ec7376795fc4dcff686e370e347b0ed86c0` | 1 | [] | 64 | WildcatMarket | WildcatMarket | compared | none | sub-word values `isDelinquent` (`bool`) are written by mstore as full words; their cleaning is not graded |
| `emit_InterestAndFeesAccrued` (src/libraries/MarketEvents.sol:127) | `IMarketEventsAndErrors.InterestAndFeesAccrued` (src/interfaces/IMarketEventsAndErrors.sol:118) | `InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)` | `0x18247a393d0531b65fbd94f5e78bc5639801a4efda62ae7b43533c4442116c3a` | 1 | [] | 192 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_WithdrawalBatchExpired` (src/libraries/MarketEvents.sol:157) | `IMarketEventsAndErrors.WithdrawalBatchExpired` (src/interfaces/IMarketEventsAndErrors.sol:133) | `WithdrawalBatchExpired(uint256,uint256,uint256,uint256)` | `0x9262dc39b47cad3a0512e4c08dda248cb345e7163058f300bc63f56bda288b6e` | 2 | [0] | 96 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_WithdrawalBatchCreated` (src/libraries/MarketEvents.sol:173) | `IMarketEventsAndErrors.WithdrawalBatchCreated` (src/interfaces/IMarketEventsAndErrors.sol:141) | `WithdrawalBatchCreated(uint256)` | `0x5c9a946d3041134198ebefcd814de7748def6576efd3d1b48f48193e183e89ef` | 2 | [0] | 0 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_WithdrawalBatchClosed` (src/libraries/MarketEvents.sol:179) | `IMarketEventsAndErrors.WithdrawalBatchClosed` (src/interfaces/IMarketEventsAndErrors.sol:144) | `WithdrawalBatchClosed(uint256)` | `0xcbdf25bf6e096dd9030d89bb2ba2e3e7adb82d25a233c3ca3d92e9f098b74e55` | 2 | [0] | 0 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_WithdrawalBatchPayment` (src/libraries/MarketEvents.sol:185) | `IMarketEventsAndErrors.WithdrawalBatchPayment` (src/interfaces/IMarketEventsAndErrors.sol:146) | `WithdrawalBatchPayment(uint256,uint256,uint256)` | `0x5272034725119f19d7236de4129fdb5093f0dcb80282ca5edbd587df91d2bd89` | 2 | [0] | 64 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_WithdrawalQueued` (src/libraries/MarketEvents.sol:197) | `IMarketEventsAndErrors.WithdrawalQueued` (src/interfaces/IMarketEventsAndErrors.sol:152) | `WithdrawalQueued(uint256,address,uint256,uint256)` | `0xecc966b282a372469fa4d3e497c2ac17983c3eaed03f3f17c9acf4b15591663e` | 3 | [0, 1] | 64 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_WithdrawalExecuted` (src/libraries/MarketEvents.sol:216) | `IMarketEventsAndErrors.WithdrawalExecuted` (src/interfaces/IMarketEventsAndErrors.sol:159) | `WithdrawalExecuted(uint256,address,uint256)` | `0xd6cddb3d69146e96ebc2c87b1b3dd0b20ee2d3b0eadf134e011afb434a3e56e6` | 3 | [0, 1] | 32 | WildcatMarket | WildcatMarket | compared | none | none |
| `emit_SanctionedAccountWithdrawalSentToEscrow` (src/libraries/MarketEvents.sol:229) | `IMarketEventsAndErrors.SanctionedAccountWithdrawalSentToEscrow` (src/interfaces/IMarketEventsAndErrors.sol:165) | `SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)` | `0x0d0843a0fcb8b83f625aafb6e42f234ac48c6728b207d52d97cfa8fbd34d498f` | 2 | [0] | 96 | WildcatMarket | WildcatMarket | compared | none | sub-word values `escrow` (`address`), `expiry` (`uint32`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexOperator` (src/spherex/SphereXProtectedEvents.sol:4) | `ISphereXProtectedRegisteredBase.ChangedSpherexOperator` (src/interfaces/ISphereXProtectedRegisteredBase.sol:7) | `ChangedSpherexOperator(address,address)` | `0x2ac55ae7ba47db34b5334622acafeb34a65daf143b47019273185d64c73a35a5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldSphereXAdmin` (`address`), `newSphereXAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexOperator` (src/spherex/SphereXProtectedEvents.sol:4) | `IWildcatArchController.ChangedSpherexOperator` (src/interfaces/IWildcatArchController.sol:15) | `ChangedSpherexOperator(address,address)` | `0x2ac55ae7ba47db34b5334622acafeb34a65daf143b47019273185d64c73a35a5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldSphereXAdmin` (`address`), `newSphereXAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexOperator` (src/spherex/SphereXProtectedEvents.sol:4) | `SphereXConfig.ChangedSpherexOperator` (src/spherex/SphereXConfig.sol:42) | `ChangedSpherexOperator(address,address)` | `0x2ac55ae7ba47db34b5334622acafeb34a65daf143b47019273185d64c73a35a5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldSphereXAdmin` (`address`), `newSphereXAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexOperator` (src/spherex/SphereXProtectedEvents.sol:4) | `SphereXProtectedRegisteredBase.ChangedSpherexOperator` (src/spherex/SphereXProtectedRegisteredBase.sol:58) | `ChangedSpherexOperator(address,address)` | `0x2ac55ae7ba47db34b5334622acafeb34a65daf143b47019273185d64c73a35a5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldSphereXAdmin` (`address`), `newSphereXAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexEngineAddress` (src/spherex/SphereXProtectedEvents.sol:12) | `ISphereXProtectedRegisteredBase.ChangedSpherexEngineAddress` (src/interfaces/ISphereXProtectedRegisteredBase.sol:9) | `ChangedSpherexEngineAddress(address,address)` | `0xf33499cccaa0611882086224cc48cd82ef54b66a4d2edf4ed67108dd516896d5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldEngineAddress` (`address`), `newEngineAddress` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexEngineAddress` (src/spherex/SphereXProtectedEvents.sol:12) | `IWildcatArchController.ChangedSpherexEngineAddress` (src/interfaces/IWildcatArchController.sol:17) | `ChangedSpherexEngineAddress(address,address)` | `0xf33499cccaa0611882086224cc48cd82ef54b66a4d2edf4ed67108dd516896d5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldEngineAddress` (`address`), `newEngineAddress` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexEngineAddress` (src/spherex/SphereXProtectedEvents.sol:12) | `SphereXConfig.ChangedSpherexEngineAddress` (src/spherex/SphereXConfig.sol:43) | `ChangedSpherexEngineAddress(address,address)` | `0xf33499cccaa0611882086224cc48cd82ef54b66a4d2edf4ed67108dd516896d5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldEngineAddress` (`address`), `newEngineAddress` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_ChangedSpherexEngineAddress` (src/spherex/SphereXProtectedEvents.sol:12) | `SphereXProtectedRegisteredBase.ChangedSpherexEngineAddress` (src/spherex/SphereXProtectedRegisteredBase.sol:59) | `ChangedSpherexEngineAddress(address,address)` | `0xf33499cccaa0611882086224cc48cd82ef54b66a4d2edf4ed67108dd516896d5` | 1 | [] | 64 | HooksFactory, WildcatMarket | HooksFactory, WildcatMarket | compared | none | sub-word values `oldEngineAddress` (`address`), `newEngineAddress` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_SpherexAdminTransferStarted` (src/spherex/SphereXProtectedEvents.sol:20) | `IWildcatArchController.SpherexAdminTransferStarted` (src/interfaces/IWildcatArchController.sol:19) | `SpherexAdminTransferStarted(address,address)` | `0x5778f1547abbbb86090a43c32aec38334b31df4beeb6f8f3fa063f593b53a526` | 1 | [] | 64 | none | none | compared | none | called from no bound deployed build; sub-word values `currentAdmin` (`address`), `pendingAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_SpherexAdminTransferStarted` (src/spherex/SphereXProtectedEvents.sol:20) | `SphereXConfig.SpherexAdminTransferStarted` (src/spherex/SphereXConfig.sol:44) | `SpherexAdminTransferStarted(address,address)` | `0x5778f1547abbbb86090a43c32aec38334b31df4beeb6f8f3fa063f593b53a526` | 1 | [] | 64 | none | none | compared | none | called from no bound deployed build; sub-word values `currentAdmin` (`address`), `pendingAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_SpherexAdminTransferCompleted` (src/spherex/SphereXProtectedEvents.sol:28) | `IWildcatArchController.SpherexAdminTransferCompleted` (src/interfaces/IWildcatArchController.sol:21) | `SpherexAdminTransferCompleted(address,address)` | `0x67ebaebcd2ca5a91a404e898110f221747e8d15567f2388a34794aab151cf3e6` | 1 | [] | 64 | none | none | compared | none | called from no bound deployed build; sub-word values `oldAdmin` (`address`), `newAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_SpherexAdminTransferCompleted` (src/spherex/SphereXProtectedEvents.sol:28) | `SphereXConfig.SpherexAdminTransferCompleted` (src/spherex/SphereXConfig.sol:45) | `SpherexAdminTransferCompleted(address,address)` | `0x67ebaebcd2ca5a91a404e898110f221747e8d15567f2388a34794aab151cf3e6` | 1 | [] | 64 | none | none | compared | none | called from no bound deployed build; sub-word values `oldAdmin` (`address`), `newAdmin` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_NewAllowedSenderOnchain` (src/spherex/SphereXProtectedEvents.sol:36) | `IWildcatArchController.NewAllowedSenderOnchain` (src/interfaces/IWildcatArchController.sol:23) | `NewAllowedSenderOnchain(address)` | `0x6de0a1fd3a59e5479e6480ba65ef28d4f3ab8143c2c631bbfd9969ab39074797` | 1 | [] | 32 | none | none | compared | none | called from no bound deployed build; sub-word values `sender` (`address`) are written by mstore as full words; their cleaning is not graded |
| `emit_NewAllowedSenderOnchain` (src/spherex/SphereXProtectedEvents.sol:36) | `SphereXConfig.NewAllowedSenderOnchain` (src/spherex/SphereXConfig.sol:46) | `NewAllowedSenderOnchain(address)` | `0x6de0a1fd3a59e5479e6480ba65ef28d4f3ab8143c2c631bbfd9969ab39074797` | 1 | [] | 32 | none | none | compared | none | called from no bound deployed build; sub-word values `sender` (`address`) are written by mstore as full words; their cleaning is not graded |

## Mismatches

None.

## Unreviewed

None.

## Declarations with no assembly emitter

| declaration | declared_at | signature |
| --- | --- | --- |
| IHooksFactoryEventsAndErrors.HooksInstanceDeployed | src/IHooksFactory.sol:45 | HooksInstanceDeployed(address,address) |
| IHooksFactoryEventsAndErrors.HooksTemplateAdded | src/IHooksFactory.sol:46 | HooksTemplateAdded(address,string,address,address,uint80,uint16) |
| IHooksFactoryEventsAndErrors.HooksTemplateDisabled | src/IHooksFactory.sol:54 | HooksTemplateDisabled(address) |
| IHooksFactoryEventsAndErrors.HooksTemplateFeesUpdated | src/IHooksFactory.sol:55 | HooksTemplateFeesUpdated(address,address,address,uint80,uint16) |
| IHooksFactoryEventsAndErrors.MarketDeployed | src/IHooksFactory.sol:63 | MarketDeployed(address,address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256,uint256) |
| WildcatArchController.MarketAdded | src/WildcatArchController.sol:42 | MarketAdded(address,address) |
| WildcatArchController.MarketRemoved | src/WildcatArchController.sol:43 | MarketRemoved(address) |
| WildcatArchController.ControllerFactoryAdded | src/WildcatArchController.sol:45 | ControllerFactoryAdded(address) |
| WildcatArchController.ControllerFactoryRemoved | src/WildcatArchController.sol:46 | ControllerFactoryRemoved(address) |
| WildcatArchController.BorrowerAdded | src/WildcatArchController.sol:48 | BorrowerAdded(address) |
| WildcatArchController.BorrowerRemoved | src/WildcatArchController.sol:49 | BorrowerRemoved(address) |
| WildcatArchController.AssetBlacklisted | src/WildcatArchController.sol:51 | AssetBlacklisted(address) |
| WildcatArchController.AssetPermitted | src/WildcatArchController.sol:52 | AssetPermitted(address) |
| WildcatArchController.ControllerAdded | src/WildcatArchController.sol:54 | ControllerAdded(address,address) |
| WildcatArchController.ControllerRemoved | src/WildcatArchController.sol:55 | ControllerRemoved(address) |
| BaseAccessControls.RoleProviderUpdated | src/access/BaseAccessControls.sol:22 | RoleProviderUpdated(address,uint32,uint24,uint24) |
| BaseAccessControls.RoleProviderAdded | src/access/BaseAccessControls.sol:28 | RoleProviderAdded(address,uint32,uint24,uint24) |
| BaseAccessControls.RoleProviderRemoved | src/access/BaseAccessControls.sol:34 | RoleProviderRemoved(address,uint24,uint24) |
| BaseAccessControls.AccountBlockedFromDeposits | src/access/BaseAccessControls.sol:39 | AccountBlockedFromDeposits(address) |
| BaseAccessControls.AccountUnblockedFromDeposits | src/access/BaseAccessControls.sol:40 | AccountUnblockedFromDeposits(address) |
| BaseAccessControls.AccountAccessGranted | src/access/BaseAccessControls.sol:41 | AccountAccessGranted(address,address,uint32) |
| BaseAccessControls.AccountAccessRevoked | src/access/BaseAccessControls.sol:46 | AccountAccessRevoked(address) |
| BaseAccessControls.AccountMadeFirstDeposit | src/access/BaseAccessControls.sol:47 | AccountMadeFirstDeposit(address,address) |
| BaseAccessControls.NameUpdated | src/access/BaseAccessControls.sol:48 | NameUpdated(string) |
| FixedTermHooks.MinimumDepositUpdated | src/access/FixedTermHooks.sol:44 | MinimumDepositUpdated(address,uint128) |
| FixedTermHooks.FixedTermUpdated | src/access/FixedTermHooks.sol:45 | FixedTermUpdated(address,uint32) |
| MarketConstraintHooks.TemporaryExcessReserveRatioActivated | src/access/MarketConstraintHooks.sol:22 | TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256) |
| MarketConstraintHooks.TemporaryExcessReserveRatioUpdated | src/access/MarketConstraintHooks.sol:29 | TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256) |
| MarketConstraintHooks.TemporaryExcessReserveRatioCanceled | src/access/MarketConstraintHooks.sol:36 | TemporaryExcessReserveRatioCanceled(address) |
| MarketConstraintHooks.TemporaryExcessReserveRatioExpired | src/access/MarketConstraintHooks.sol:38 | TemporaryExcessReserveRatioExpired(address) |
| OpenTermHooks.MinimumDepositUpdated | src/access/OpenTermHooks.sol:37 | MinimumDepositUpdated(address,uint128) |
| IMarketEventsAndErrors.AccountSanctioned | src/interfaces/IMarketEventsAndErrors.sol:127 | AccountSanctioned(address) |
| IWildcatArchController.BorrowerAdded | src/interfaces/IWildcatArchController.sol:101 | BorrowerAdded(address) |
| IWildcatArchController.BorrowerRemoved | src/interfaces/IWildcatArchController.sol:103 | BorrowerRemoved(address) |
| IWildcatArchController.AssetPermitted | src/interfaces/IWildcatArchController.sol:124 | AssetPermitted() |
| IWildcatArchController.AssetBlacklisted | src/interfaces/IWildcatArchController.sol:126 | AssetBlacklisted() |
| IWildcatArchController.MarketAdded | src/interfaces/IWildcatArchController.sol:147 | MarketAdded(address,address) |
| IWildcatArchController.MarketRemoved | src/interfaces/IWildcatArchController.sol:149 | MarketRemoved(address) |
| IWildcatArchController.ControllerFactoryAdded | src/interfaces/IWildcatArchController.sol:55 | ControllerFactoryAdded(address) |
| IWildcatArchController.ControllerFactoryRemoved | src/interfaces/IWildcatArchController.sol:57 | ControllerFactoryRemoved(address) |
| IWildcatArchController.ControllerAdded | src/interfaces/IWildcatArchController.sol:78 | ControllerAdded(address,address) |
| IWildcatArchController.ControllerRemoved | src/interfaces/IWildcatArchController.sol:80 | ControllerRemoved(address) |
| IWildcatSanctionsEscrow.EscrowReleased | src/interfaces/IWildcatSanctionsEscrow.sol:5 | EscrowReleased(address,address,uint256) |
| IWildcatSanctionsSentinel.SanctionOverride | src/interfaces/IWildcatSanctionsSentinel.sol:11 | SanctionOverride(address,address) |
| IWildcatSanctionsSentinel.SanctionOverrideRemoved | src/interfaces/IWildcatSanctionsSentinel.sol:13 | SanctionOverrideRemoved(address,address) |
| IWildcatSanctionsSentinel.NewSanctionsEscrow | src/interfaces/IWildcatSanctionsSentinel.sol:5 | NewSanctionsEscrow(address,address,address) |
| Wildcat4626Wrapper.TokensSwept | src/vault/Wildcat4626Wrapper.sol:101 | TokensSwept(address,address,uint256) |
| Wildcat4626WrapperFactory.WrapperDeployed | src/vault/Wildcat4626WrapperFactory.sol:17 | WrapperDeployed(address,address) |

## Not reached by any deployed build

A row here compared cleanly against its declaration but its emitter is never called from a source file bound into a listed build; the source-level dead-code and unused-slot cases named in the study belong here.

| Emitter | Declaration | Declared at |
| --- | --- | --- |
| `emit_ProtocolFeeBipsUpdated` (src/libraries/MarketEvents.sol:38) | `IMarketEventsAndErrors.ProtocolFeeBipsUpdated` | src/interfaces/IMarketEventsAndErrors.sol:87 |
| `emit_SanctionedAccountAssetsSentToEscrow` (src/libraries/MarketEvents.sol:59) | `IMarketEventsAndErrors.SanctionedAccountAssetsSentToEscrow` | src/interfaces/IMarketEventsAndErrors.sol:93 |
| `emit_SpherexAdminTransferStarted` (src/spherex/SphereXProtectedEvents.sol:20) | `IWildcatArchController.SpherexAdminTransferStarted` | src/interfaces/IWildcatArchController.sol:19 |
| `emit_SpherexAdminTransferStarted` (src/spherex/SphereXProtectedEvents.sol:20) | `SphereXConfig.SpherexAdminTransferStarted` | src/spherex/SphereXConfig.sol:44 |
| `emit_SpherexAdminTransferCompleted` (src/spherex/SphereXProtectedEvents.sol:28) | `IWildcatArchController.SpherexAdminTransferCompleted` | src/interfaces/IWildcatArchController.sol:21 |
| `emit_SpherexAdminTransferCompleted` (src/spherex/SphereXProtectedEvents.sol:28) | `SphereXConfig.SpherexAdminTransferCompleted` | src/spherex/SphereXConfig.sol:45 |
| `emit_NewAllowedSenderOnchain` (src/spherex/SphereXProtectedEvents.sol:36) | `IWildcatArchController.NewAllowedSenderOnchain` | src/interfaces/IWildcatArchController.sol:23 |
| `emit_NewAllowedSenderOnchain` (src/spherex/SphereXProtectedEvents.sol:36) | `SphereXConfig.NewAllowedSenderOnchain` | src/spherex/SphereXConfig.sol:46 |

## Source files

| Path | Ref | Blob | Bytes | SHA-256 | In builds |
| --- | --- | --- | --- | --- | --- |
| `deployments/mainnet/HooksFactory-0xdd7dd3b5076cf89440d05585ff56d246386207be/output.json` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | `0eeb618a73b196b458f99c3cb1039ddc04d1402d` | 168209 | `fea058a27a5bea99ceb4032ad711b285247ade23ff56efca2361114e1e256598` | compiler-output |
| `deployments/mainnet/HooksFactory-0xdd7dd3b5076cf89440d05585ff56d246386207be/standard-input.json` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | `34d238ea60b2f3205195f9d8cf942f3a46c08272` | 161751 | `63dabbfdd5b7c140c314a0892baa639e217b0a15b20a51e604ecd2bd10ad4309` | standard-input |
| `deployments/mainnet/WildcatMarket-0xac3216fa28f81b8fae150fb5626ca79c7a570daf/output.json` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | `ef18536250430f3adbac855dbd4ef4fa68cddd5e` | 242841 | `d1a748bff6dec5a52571e432288d967fe40b9787b98b223fe68a6b812d4b8281` | compiler-output |
| `deployments/mainnet/WildcatMarket-0xac3216fa28f81b8fae150fb5626ca79c7a570daf/standard-input.json` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | `0f86f94ad1165975a2812b3acfd0a333c5d0724f` | 224443 | `f9a92fe4072d8f44406448377730c4b38b908571fa3db6b8ff3a81719e801346` | standard-input |
| `src/HooksFactory.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `b524f9e49474ac9ed57989c758bba8850c93265b` | 24468 | `f3a2ca3b4f9f239a07eb924ea1e4db73eeb44867a782ca48e4d59c157b8eada9` | HooksFactory=equal, WildcatMarket=absent |
| `src/IHooksFactory.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `6e883a21b21a39b6989d9f0331bd7e91c12b04e7` | 9790 | `deb205c5968ee7ae139623b7ffb50d454d4c3f34362cc92ee21ef6802ac047f8` | HooksFactory=equal, WildcatMarket=equal |
| `src/ReentrancyGuard.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `f754e51382059d4ebf63663dd77262a5a286fadc` | 3102 | `f2098aacf8a3e6e4cf676664af8df623d8bf8364ea71f13eed7ce6f4dde64f96` | HooksFactory=equal, WildcatMarket=equal |
| `src/WildcatArchController.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `53cd99641e7f0bcb3b05d506d891a3b47e41a4df` | 12740 | `28cbc8201d75bb7eb63aafcc06bece69acf353ce74bf9a491f2796cb61f1d7b9` | HooksFactory=absent, WildcatMarket=absent |
| `src/WildcatSanctionsEscrow.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `375a857bb6b1488af9772dd0031c85ae52e89532` | 1362 | `4b99b2334124067b45624f2632c6273a9162d7050c17d8b508b95a953b077e33` | HooksFactory=absent, WildcatMarket=equal |
| `src/WildcatSanctionsSentinel.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `b2e46dfcf192eecced786630322b869f90cd610b` | 6702 | `41e34f67e71218445a88055d1c5ca8744e20c84787e629b943d2d9dc86dca0b1` | HooksFactory=absent, WildcatMarket=equal |
| `src/access/BaseAccessControls.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `acb94765c627584ec9de9a4c0bd1fe87087e2b56` | 30742 | `9850505ebbc026be35e45a3426c52298be2c5a823f4bc6e27ed8fc581e240fa4` | HooksFactory=absent, WildcatMarket=absent |
| `src/access/FixedTermHooks.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `9f6b82ee45b9a9be38b152e794f76c7988ee689c` | 17366 | `03436e22b1585d82ade2e418ea25e72d717d4f64e247130edc7c1d02db0e1502` | HooksFactory=absent, WildcatMarket=absent |
| `src/access/IHooks.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `14e80db27ffcd53597d1aefef4e9d3082c253659` | 3169 | `b7c2028d5670c62fbbe43805f36576b638e6cced3507e773b8d158e66dcc193c` | HooksFactory=equal, WildcatMarket=equal |
| `src/access/IRoleProvider.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `904b886f6d22798451b9f83ee347eeafd5422866` | 652 | `b9db5bedf9e21d487767e1b786444f5366f5473baac3b71e9f34020789142950` | HooksFactory=absent, WildcatMarket=absent |
| `src/access/IRoleProviderFactory.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `24dfcc80d10024e2542bfd5093e301f0d2af7bc4` | 172 | `4ea3f2fdf1943df3b7a6d9ba64981fd4393f1e13f4c881134ad10ed2ab92c082` | HooksFactory=absent, WildcatMarket=absent |
| `src/access/MarketConstraintHooks.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `e1c429a7c2bce61cb994518ea9ef85400bb6aac0` | 11007 | `02e4c9b0e4c52c126691643d682dd01c32c88a5b48745ebf6dc3c526cd6eb46c` | HooksFactory=absent, WildcatMarket=absent |
| `src/access/OpenTermHooks.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `49ca9a5cba7f9cb85556ef58556dc5fab33fa9ed` | 14212 | `abe128fa4fddc24a44eb05e93b404fe1d18f973b0f1f4587313b13592d057b89` | HooksFactory=absent, WildcatMarket=absent |
| `src/access/ProviderStructs.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `89422c373f95ef5e250f128cfd89cbf53495612d` | 1405 | `49816d230642f580ca2544afc780ff6be33299ce9e1dcfa48c7b5b4540099dde` | HooksFactory=absent, WildcatMarket=absent |
| `src/interfaces/IChainalysisSanctionsList.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `901f5c2e257072041be8cc2f7d05d3177d778dae` | 167 | `ebd33a4e47c71e14837bec78ffebec82c32faf72b4efeb0a1453bfe94ca6c3f5` | HooksFactory=absent, WildcatMarket=equal |
| `src/interfaces/IERC20.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `9ee5c3aecc25e36414b022353b3126524d3049bc` | 1075 | `f55382c591dcf77a6b324455a4c714a9469a212da25a178f63a56e7616df455e` | HooksFactory=absent, WildcatMarket=equal |
| `src/interfaces/IMarketEventsAndErrors.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `dd6d3838b2990610b7914bc3f49103c082fd2784` | 4271 | `b70cdb05567a8e64a3e41f3f5658af93de8d7bc9b869be18b94d144fad9298b5` | HooksFactory=absent, WildcatMarket=equal |
| `src/interfaces/ISphereXProtectedRegisteredBase.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `8e9078e846875d8de0df1979f726a6a9af9c1b64` | 505 | `9b543f7d14aaee5812c201383f68f05ba6655fccfeef270bd0e1052be688a3fa` | HooksFactory=absent, WildcatMarket=absent |
| `src/interfaces/IWildcatArchController.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `2ee945fb20874de2da96c79b0dc5fe0056132268` | 5503 | `f87a7b647177b0993f5920599423df8b6a4494c8ae262743ef0cc333f412cd36` | HooksFactory=equal, WildcatMarket=absent |
| `src/interfaces/IWildcatSanctionsEscrow.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `47c122005656394404ae82f97667bb822d24bdc6` | 621 | `109ed484bf5914a3513a790f31a0c5286a71d630d32c076c87a26e22cb0130af` | HooksFactory=absent, WildcatMarket=equal |
| `src/interfaces/IWildcatSanctionsSentinel.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `5d4ab7049bffce99ee72532272011f3066a1325f` | 2506 | `c1dbda0ffc1b14b3e8c5941f6355ba2f980a3871cf5de9275e9942d5371ee13a` | HooksFactory=absent, WildcatMarket=equal |
| `src/interfaces/WildcatStructsAndEnums.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `0a929dee1732eb6358de87bf2e50d9d33647a328` | 2112 | `2294014bc8f3b2dda6f84d95c010edd367cc92441fba1095f0939cf7ebd12c00` | HooksFactory=equal, WildcatMarket=equal |
| `src/lens/HooksConfigData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `2cd77f855a3ef318e6384b996055f1aa56235002` | 4319 | `ff146246ff0f7cae0024ce8126374eb03324894c059266da59c1426b065ec966` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/HooksDataForBorrower.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `43afa17bf64d61c88f8c57e81deffe0e88f4cbea` | 1252 | `4d1f00cccd7fdac85bf048432e1b7b8c0deeaf15d96216b03930db79006abefd` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/HooksInstanceData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `190577366ad788db2c136e20173f947c35e0d585` | 2144 | `3d40886ad23cbdbc89e1bd769977d4bf4786dfb9e413393fb7d91f079f7bc546` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/HooksTemplateData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `87bab02295740dce8640f81529bb2597f2aeca3f` | 2348 | `51db529b2e3b50e5ed4d0613ab1a5180b1bcf0f17d2ebb202cdda286013d09fc` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/LenderAccountData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `43f25720fec908170a0d3f00cfcb538f4c99c0a7` | 2511 | `71af773813fb3b618edf6289a8e37e6667dbc48497bc12dbd781f7d2fce296fc` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/MarketData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `efc54fd226eb814244d68bb5d6b72699a3703dbb` | 7444 | `14a85a4d2c68ca55e3a391d5209297befb602e12c9c275c977e71fe47c32e388` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/MarketLens.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `9419637f9c4bf9098a48b822fa5818281a6439c0` | 9076 | `22284bfb5277a9dc1198f0849e9a7080a14634653a878afd7f7f2acf7b13307f` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/RoleProviderData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `4042a0536f69091799c47d9c1d87c987f16f5938` | 837 | `8b97b93b415610e8f0747755f7dca68e9334c21d869a74397ac30c23f97cf97c` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/TokenData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `93e4c9f1a1041fb7c4acb9b7881007ac289d80a9` | 898 | `68a50aeec81b2f3172666b227d64b699147b6f572a9babb6b6d9fe5b189a6f4e` | HooksFactory=absent, WildcatMarket=absent |
| `src/lens/WithdrawalBatchData.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `2db8792199a3522d42ee9752cfe5329d1d741d56` | 3336 | `87e25dea080ddbe1225ddc4ba3914de74f0123cd00aedbd42eca1a1d50f93c4e` | HooksFactory=absent, WildcatMarket=absent |
| `src/libraries/BoolUtils.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `0bc92966a016577244934b70240e4e65977cc17d` | 411 | `b8e5c7e4a38ff68bded5e234b6966cdf9d6e94da9976015f1bcda69e74e18336` | HooksFactory=absent, WildcatMarket=equal |
| `src/libraries/Errors.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `ca399b94286f8c62ea6f5bbf1f3094afe882effa` | 1938 | `16f5464fc6d5eda8b1ab693866f35e25d0917e1145f791b9bbb255facad87e9a` | HooksFactory=equal, WildcatMarket=equal |
| `src/libraries/FIFOQueue.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `e8d0dde5839cc36dfb22bab494d8a3683e9eac0e` | 2298 | `7805eaa4c77f475ac11d6e055cd5b90c08219fce0d39fdd395a3fa12cb1505a0` | HooksFactory=absent, WildcatMarket=equal |
| `src/libraries/FeeMath.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `2b509d01927eb1e346c6fee615772eaebc27f331` | 6537 | `4c81fce68038e7ee049540b71e69682b765fc692a6b27820d5b6e64df9aa060c` | HooksFactory=equal, WildcatMarket=equal |
| `src/libraries/FunctionTypeCasts.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `adacced764868dafb316912eb046eb27381f4703` | 1774 | `489ebcef5ea5700013c4a24897adddbced1fc1679f9d0d59028198d85b3f7f7c` | HooksFactory=absent, WildcatMarket=equal |
| `src/libraries/LibERC20.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `f58ce02065cb5a05a32f55b2737d1be8e072b767` | 8250 | `1ee751f665bc41b99e9c04ed41ba692c70d8cd84eb90355bf44b12aa725b40b8` | HooksFactory=equal, WildcatMarket=equal |
| `src/libraries/LibStoredInitCode.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `3c7c123d5cd257b188b692f0e938f7f2aece17dc` | 6616 | `cb26fdfe045cfd08ac082fef7ab47371f5b1f0a7e821a2f6dd5ee7be374885b8` | HooksFactory=equal, WildcatMarket=absent |
| `src/libraries/MarketErrors.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `bc14a5621d0ae7c0067db1e1e08dec9c6d15892d` | 8026 | `02ae442a9323b350330a88af1774937aed7543e2c8a3711aebc4be74a476c6d1` | HooksFactory=absent, WildcatMarket=equal |
| `src/libraries/MarketEvents.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `80d93961d74cfa36feee0fe34a423c989d9ca034` | 6728 | `bffeeebe2e4847a1beebdb40285e94f2838691320cc4f5958e5314d95bc83b57` | HooksFactory=absent, WildcatMarket=equal |
| `src/libraries/MarketState.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `b326ae14bfce093a060404f079106d9b18930391` | 4938 | `1aa122075f0c45098599aff3df10fe86744d168a8bbe61a12570116739a67b8c` | HooksFactory=equal, WildcatMarket=equal |
| `src/libraries/MathUtils.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `856cce0d3773819901da330ee1159e49a128a5a8` | 6984 | `6d75952ae99e472d73706d2f9277ead1fb77b8c6adc374c47491ccba1ad9c843` | HooksFactory=equal, WildcatMarket=equal |
| `src/libraries/SafeCastLib.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `5645851a9016850322ce314c70273caa07d4ebf9` | 4074 | `844e319a8e2494fa03a74696ffa8b4507205229aa68bf1fb253edc5d6f86645d` | HooksFactory=equal, WildcatMarket=equal |
| `src/libraries/StringQuery.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `d4147ddea2dda9f7cb63fccb075df596a60486aa` | 2793 | `3f6e72a74c8b3abaf353fd49408aaf56de3a067135a4a5cdd52e6bf98cedf7cb` | HooksFactory=equal, WildcatMarket=equal |
| `src/libraries/Withdrawal.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `24d7c6a088deb2721cc11bc2d88ad9804b41f6fc` | 1938 | `a116c5d96e2bdd5739c460410356ced92bc1b3ea07e15ab4e85b525231c1cb5c` | HooksFactory=absent, WildcatMarket=equal |
| `src/market/WildcatMarket.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `833069e2d5667f87c5c18dac5deac1d584e0d177` | 11010 | `e208fce7c2d9126df9a400f4d4aee7e47f0a767a710826a3b679f924c923d39f` | HooksFactory=absent, WildcatMarket=equal |
| `src/market/WildcatMarketBase.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `3c72d0245bacf52c71ce0bd39628df1a5bc50b92` | 29065 | `f84d6137bccb554b25e9563362d5a0155579f89e4f9073d95df80b14a318353a` | HooksFactory=absent, WildcatMarket=equal |
| `src/market/WildcatMarketConfig.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `25d0b1801fe93b1fa2c1ba2cebd6f311913290b0` | 7126 | `4249e124541a9abbb8e6d0dac3342c0b68f3c8a9530ce944ebece84335f858d0` | HooksFactory=absent, WildcatMarket=equal |
| `src/market/WildcatMarketToken.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `509ecbcbe6f3a26e3fc5d3f6edac42efedba81b7` | 3095 | `db26f7b46e6800afc7c441ea3a39e53337aae272e03fe49d0890ea256c52d098` | HooksFactory=absent, WildcatMarket=equal |
| `src/market/WildcatMarketWithdrawals.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `54a57958f689ff9ac90fee63f6797e5f2f3cc70b` | 12472 | `f1428b3eb479bba19b6b332c75953ed8d236ef72abb2d17f4c0bc933b73c22d4` | HooksFactory=absent, WildcatMarket=equal |
| `src/spherex/ISphereXEngine.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `b0f6e995669b39dee51f6960c18398e71f8cd351` | 1743 | `d8bac27866724e09ce86178b82f8c1b08c8b12914e8eb47049692e9d6af1ea92` | HooksFactory=equal, WildcatMarket=equal |
| `src/spherex/SphereXConfig.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `1656e5bc5844d2bec95ea454d1577996c80770b0` | 7681 | `35bb7a0506954ebdd456a1c031019b6cf663d91fc3930d072d406f505753f324` | HooksFactory=absent, WildcatMarket=absent |
| `src/spherex/SphereXProtectedErrors.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `0c4d4c85d7b992a2c335a24da8ee14fd34404c5c` | 643 | `36197d5139992a311be1907852eeeee51b47e3d415996afc1919639259c14884` | HooksFactory=equal, WildcatMarket=equal |
| `src/spherex/SphereXProtectedEvents.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `d5415f1c37cc0df2fea1febe6ab1a861b49d02a4` | 1262 | `dd23117fb016168192f69385cab25d50ab7c86e8dcfbdba2c35ba64eee3e9f63` | HooksFactory=equal, WildcatMarket=equal |
| `src/spherex/SphereXProtectedRegisteredBase.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `fec029bfa09934cad39970912eadfd124a6259a0` | 13725 | `37ad1987d58b3aa4219919010bcd6300057065cecf568b1d052fe5dd32025ec2` | HooksFactory=equal, WildcatMarket=equal |
| `src/types/HooksConfig.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `cb515d62cd9e0ac4c2cb1459ed514bfb9de7c35d` | 36475 | `ed5734a684ca96f502294930de30885c2fa9d924948a4a1a75aa628b5b3512e2` | HooksFactory=equal, WildcatMarket=equal |
| `src/types/LenderStatus.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `3fe92d1504af21db34ae913823bd5660016739d8` | 2464 | `ef09bcf403273d4f7c3e7088d8e07169b28e7f7a8e9811a1c797ad51f14915fb` | HooksFactory=absent, WildcatMarket=absent |
| `src/types/RoleProvider.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `610009035e200acb511c708b5231295908bd216c` | 5628 | `f562a23fd737795428b5dcd190993505b51f4abf4ebaf2dc499ca5ea9133715f` | HooksFactory=absent, WildcatMarket=absent |
| `src/types/TransientBytesArray.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `183b92f3b9543cd8e23bbd92b0d98a0951273c90` | 3987 | `385b76f7fa3a051cd128cf68033c730930111e0621191163dd8d34a18d0b90fe` | HooksFactory=equal, WildcatMarket=absent |
| `src/vault/Wildcat4626Wrapper.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `b75edbc6538af259eebba026af1a2e9f358f8824` | 17456 | `9dc65f4e614cce819b5c6ec57344dc50447304c146bc1297952ebdaeba6dfb00` | HooksFactory=absent, WildcatMarket=absent |
| `src/vault/Wildcat4626WrapperFactory.sol` | `f5a26146987926f4811b72a795d662813dedfe85` | `769ac86bf76f4b6c11a0612dd7fd5f54af9e6399` | 1428 | `29aaccff079597cb02a03124ad343ae75aaedff1e82853e458585df2db5d777e` | HooksFactory=absent, WildcatMarket=absent |
