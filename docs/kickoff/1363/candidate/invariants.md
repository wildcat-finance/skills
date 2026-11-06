# Properties of `src/market/` and the hooks

> Wildcat V2 | bea503c2736d47de7fd34130c64f10783dc35b39 | 375 guards | 14 inferred properties

These are source-derived properties and explicit limits. On-chain “Yes” means the cited source paths enforce the bounded statement; no runtime property campaign result is claimed.

## 1. Enforced Guards (Reference)

Exact rejection predicates appear below. Multiline predicates retain their source whitespace; each has a source location and purpose.

#### G-1

`msg.sender != IWildcatArchController(_archController).owner()` · [src/HooksFactory.sol:197](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L197) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-2

`!success || returnData.length != 0x20` · [src/HooksFactory.sol:209](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L209) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-3

`principal == address(0)` · [src/HooksFactory.sol:211](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L211) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-4

`_templateDetails[hooksTemplate].exists` · [src/HooksFactory.sol:228](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L228) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-5

`(protocolFeeBips > 0 && nullFeeRecipient) ||
      (hasOriginationFee && nullFeeRecipient) ||
      (hasOriginationFee && nullOriginationFeeAsset) ||
      protocolFeeBips > 1_000` · [src/HooksFactory.sol:264](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L264) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-6

`!_templateDetails[hooksTemplate].exists` · [src/HooksFactory.sol:281](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L281) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-7

`!_templateDetails[hooksTemplate].exists` · [src/HooksFactory.sol:311](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L311) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-8

`getHooksTemplateForInstance[hooksInstance] == address(0)` · [src/HooksFactory.sol:441](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L441) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-9

`previousAdministrator == newAdministrator ||
      newAdministrator == address(0) ||
      getHooksAdministrator[hooksInstance] != previousAdministrator ||
      IHooksAdministrator(hooksInstance).administrator() != newAdministrator ||
      IHooksAdministrator(hooksInstance).pendingAdministrator() != address(0) ||
      !IWildcatArchController(_archController).isRegisteredBorrower(newAdministrator)` · [src/HooksFactory.sol:445](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L445) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-10

`indexToRemove >= previousCount || previousHooksInstances[indexToRemove] != hooksInstance` · [src/HooksFactory.sol:460](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L460) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-11

`!template.exists` · [src/HooksFactory.sol:493](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L493) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-12

`!template.enabled` · [src/HooksFactory.sol:496](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L496) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-13

`iszero(hooksInstance)` · [src/HooksFactory.sol:522](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L522) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-14

`bytes20(salt) == bytes20(0)` · [src/HooksFactory.sol:622](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L622) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-15

`gt(length, 0x3f)` · [src/HooksFactory.sol:636](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L636) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-16

`IWildcatArchController(_archController).isBlacklistedAsset(parameters.asset)` · [src/HooksFactory.sol:691](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L691) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-17

`address(bytes20(runtimeParams.salt)) != msg.sender` · [src/HooksFactory.sol:696](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L696) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-18

`runtimeParams.originationFeeAsset != templateDetails.originationFeeAsset ||
      runtimeParams.originationFeeAmount != templateDetails.originationFeeAmount` · [src/HooksFactory.sol:701](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L701) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-19

`market.code.length != 0` · [src/HooksFactory.sol:758](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L758) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-20

`LibStoredInitCode.create2WithStoredInitCode(marketInitCodeStorage, runtimeParams.salt) != market` · [src/HooksFactory.sol:762](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L762) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-21

`hooksTemplate == address(0)` · [src/HooksFactory.sol:789](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L789) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-22

`!templateDetails.exists` · [src/HooksFactory.sol:815](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L815) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-23

`!details.exists` · [src/HooksFactory.sol:842](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L842) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-24

`marketStartIndex > marketEndIndex` · [src/HooksFactory.sol:849](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L849) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-25

`iszero(call(gas(), market, 0, setProtocolFeeBipsCalldataPointer, 0x24, 0, 0))` · [src/HooksFactory.sol:868](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactory.sol#L868) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-26

`msg.sender != IWildcatArchController(_archController).owner()` · [src/HooksFactoryRevolving.sol:222](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L222) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-27

`!success || returnData.length != 0x20` · [src/HooksFactoryRevolving.sol:234](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L234) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-28

`principal == address(0)` · [src/HooksFactoryRevolving.sol:236](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L236) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-29

`_templateDetails[hooksTemplate].exists` · [src/HooksFactoryRevolving.sol:252](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L252) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-30

`(protocolFeeBips > 0 && nullFeeRecipient) ||
      (hasOriginationFee && nullFeeRecipient) ||
      (hasOriginationFee && nullOriginationFeeAsset) ||
      protocolFeeBips > 1_000` · [src/HooksFactoryRevolving.sol:288](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L288) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-31

`!_templateDetails[hooksTemplate].exists` · [src/HooksFactoryRevolving.sol:308](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L308) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-32

`!_templateDetails[hooksTemplate].exists` · [src/HooksFactoryRevolving.sol:336](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L336) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-33

`getHooksTemplateForInstance[hooksInstance] == address(0)` · [src/HooksFactoryRevolving.sol:469](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L469) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-34

`previousAdministrator == newAdministrator ||
      newAdministrator == address(0) ||
      getHooksAdministrator[hooksInstance] != previousAdministrator ||
      IHooksAdministrator(hooksInstance).administrator() != newAdministrator ||
      IHooksAdministrator(hooksInstance).pendingAdministrator() != address(0) ||
      !IWildcatArchController(_archController).isRegisteredBorrower(newAdministrator)` · [src/HooksFactoryRevolving.sol:473](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L473) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-35

`indexToRemove >= previousCount || previousHooksInstances[indexToRemove] != hooksInstance` · [src/HooksFactoryRevolving.sol:488](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L488) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-36

`!template.exists` · [src/HooksFactoryRevolving.sol:521](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L521) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-37

`!template.enabled` · [src/HooksFactoryRevolving.sol:524](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L524) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-38

`iszero(hooksInstance)` · [src/HooksFactoryRevolving.sol:550](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L550) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-39

`bytes20(salt) == bytes20(0)` · [src/HooksFactoryRevolving.sol:650](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L650) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-40

`gt(length, 0x3f)` · [src/HooksFactoryRevolving.sol:664](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L664) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-41

`marketData.length != _MARKET_DATA_LENGTH` · [src/HooksFactoryRevolving.sol:683](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L683) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-42

`version != _MARKET_DATA_VERSION` · [src/HooksFactoryRevolving.sol:688](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L688) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-43

`decodedCommitmentFeeBips > _MAX_COMMITMENT_FEE_BIPS` · [src/HooksFactoryRevolving.sol:691](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L691) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-44

`!templateDetails.exists` · [src/HooksFactoryRevolving.sol:741](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L741) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-45

`IWildcatArchController(_archController).isBlacklistedAsset(parameters.asset)` · [src/HooksFactoryRevolving.sol:745](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L745) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-46

`address(bytes20(runtimeParams.salt)) != msg.sender` · [src/HooksFactoryRevolving.sol:750](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L750) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-47

`runtimeParams.originationFeeAsset != templateDetails.originationFeeAsset ||
      runtimeParams.originationFeeAmount != templateDetails.originationFeeAmount` · [src/HooksFactoryRevolving.sol:755](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L755) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-48

`market.code.length != 0` · [src/HooksFactoryRevolving.sol:813](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L813) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-49

`LibStoredInitCode.create2WithStoredInitCode(marketInitCodeStorage, runtimeParams.salt) !=
      market` · [src/HooksFactoryRevolving.sol:817](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L817) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-50

`hooksTemplate == address(0)` · [src/HooksFactoryRevolving.sol:852](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L852) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-51

`!details.exists` · [src/HooksFactoryRevolving.sol:909](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L909) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-52

`marketStartIndex > marketEndIndex` · [src/HooksFactoryRevolving.sol:916](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L916) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-53

`iszero(call(gas(), market, 0, setProtocolFeeBipsCalldataPointer, 0x24, 0, 0))` · [src/HooksFactoryRevolving.sol:935](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/HooksFactoryRevolving.sol#L935) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-54

`_reentrancyGuard` · [src/ReentrancyGuard.sol:43](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/ReentrancyGuard.sol#L43) · Purpose: Protects the checked accounting or external-return boundary.

#### G-55

`tload(_REENTRANCY_GUARD_SLOT)` · [src/ReentrancyGuard.sol:67](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/ReentrancyGuard.sol#L67) · Purpose: Protects the checked accounting or external-return boundary.

#### G-56

`iszero(call(gas(), target, 0, add(data, 0x20), mload(data), 0, 0))` · [src/WildcatArchController.sol:172](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L172) · Purpose: Protects registration and controller authority.

#### G-57

`!_borrowers.add(borrower)` · [src/WildcatArchController.sol:185](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L185) · Purpose: Protects registration and controller authority.

#### G-58

`!_borrowers.remove(borrower)` · [src/WildcatArchController.sol:193](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L193) · Purpose: Protects registration and controller authority.

#### G-59

`!_assetBlacklist.add(asset)` · [src/WildcatArchController.sol:237](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L237) · Purpose: Protects registration and controller authority.

#### G-60

`!_assetBlacklist.remove(asset)` · [src/WildcatArchController.sol:245](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L245) · Purpose: Protects registration and controller authority.

#### G-61

`!_controllerFactories.add(factory)` · [src/WildcatArchController.sol:290](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L290) · Purpose: Protects registration and controller authority.

#### G-62

`!_controllerFactories.remove(factory)` · [src/WildcatArchController.sol:299](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L299) · Purpose: Protects registration and controller authority.

#### G-63

`!_controllerFactories.contains(msg.sender)` · [src/WildcatArchController.sol:340](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L340) · Purpose: Protects registration and controller authority.

#### G-64

`!_controllers.add(controller)` · [src/WildcatArchController.sol:350](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L350) · Purpose: Protects registration and controller authority.

#### G-65

`!_controllers.remove(controller)` · [src/WildcatArchController.sol:359](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L359) · Purpose: Protects registration and controller authority.

#### G-66

`!_controllers.contains(msg.sender)` · [src/WildcatArchController.sol:400](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L400) · Purpose: Protects registration and controller authority.

#### G-67

`!_markets.add(market)` · [src/WildcatArchController.sol:410](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L410) · Purpose: Protects registration and controller authority.

#### G-68

`!_markets.remove(market)` · [src/WildcatArchController.sol:419](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatArchController.sol#L419) · Purpose: Protects registration and controller authority.

#### G-69

`archController_ == address(0) || archController_.code.length == 0` · [src/WildcatBorrowerIdentityRegistry.sol:27](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L27) · Purpose: Protects borrower identity resolution and registration state.

#### G-70

`msg.sender != _archControllerOwner()` · [src/WildcatBorrowerIdentityRegistry.sol:38](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L38) · Purpose: Protects borrower identity resolution and registration state.

#### G-71

`!_accountFactories.contains(msg.sender)` · [src/WildcatBorrowerIdentityRegistry.sol:45](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L45) · Purpose: Protects borrower identity resolution and registration state.

#### G-72

`accountFactory == address(0) || accountFactory.code.length == 0` · [src/WildcatBorrowerIdentityRegistry.sol:54](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L54) · Purpose: Protects borrower identity resolution and registration state.

#### G-73

`!_accountFactories.add(accountFactory)` · [src/WildcatBorrowerIdentityRegistry.sol:57](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L57) · Purpose: Protects borrower identity resolution and registration state.

#### G-74

`!_accountFactories.remove(accountFactory)` · [src/WildcatBorrowerIdentityRegistry.sol:66](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L66) · Purpose: Protects borrower identity resolution and registration state.

#### G-75

`start > end` · [src/WildcatBorrowerIdentityRegistry.sol:84](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L84) · Purpose: Protects borrower identity resolution and registration state.

#### G-76

`principal == address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:103](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L103) · Purpose: Protects borrower identity resolution and registration state.

#### G-77

`account == address(0) || account == principal || account.code.length == 0` · [src/WildcatBorrowerIdentityRegistry.sol:104](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L104) · Purpose: Protects borrower identity resolution and registration state.

#### G-78

`principalOf[account] != address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:107](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L107) · Purpose: Protects borrower identity resolution and registration state.

#### G-79

`_isRegisteredBorrower(account) || principalOf[principal] != address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:111](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L111) · Purpose: Protects borrower identity resolution and registration state.

#### G-80

`!_isRegisteredBorrower(principal)` · [src/WildcatBorrowerIdentityRegistry.sol:114](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L114) · Purpose: Protects borrower identity resolution and registration state.

#### G-81

`msg.sender != currentPrincipal` · [src/WildcatBorrowerIdentityRegistry.sol:131](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L131) · Purpose: Protects borrower identity resolution and registration state.

#### G-82

`msg.sender != currentPrincipal` · [src/WildcatBorrowerIdentityRegistry.sol:146](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L146) · Purpose: Protects borrower identity resolution and registration state.

#### G-83

`cancelledPendingPrincipal == address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:149](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L149) · Purpose: Protects borrower identity resolution and registration state.

#### G-84

`msg.sender != newPrincipal` · [src/WildcatBorrowerIdentityRegistry.sol:162](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L162) · Purpose: Protects borrower identity resolution and registration state.

#### G-85

`borrower == address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:176](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L176) · Purpose: Protects borrower identity resolution and registration state.

#### G-86

`principal != address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:180](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L180) · Purpose: Protects borrower identity resolution and registration state.

#### G-87

`principal == address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:183](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L183) · Purpose: Protects borrower identity resolution and registration state.

#### G-88

`principalOf[principal] != address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:184](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L184) · Purpose: Protects borrower identity resolution and registration state.

#### G-89

`!_isRegisteredBorrower(principal)` · [src/WildcatBorrowerIdentityRegistry.sol:185](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L185) · Purpose: Protects borrower identity resolution and registration state.

#### G-90

`start > end` · [src/WildcatBorrowerIdentityRegistry.sol:233](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L233) · Purpose: Protects borrower identity resolution and registration state.

#### G-91

`principal == address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:246](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L246) · Purpose: Protects borrower identity resolution and registration state.

#### G-92

`newPrincipal == address(0) ||
      newPrincipal == account ||
      newPrincipal == currentPrincipal` · [src/WildcatBorrowerIdentityRegistry.sol:255](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L255) · Purpose: Protects borrower identity resolution and registration state.

#### G-93

`_isRegisteredBorrower(account) || principalOf[newPrincipal] != address(0)` · [src/WildcatBorrowerIdentityRegistry.sol:262](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L262) · Purpose: Protects borrower identity resolution and registration state.

#### G-94

`!_isRegisteredBorrower(newPrincipal)` · [src/WildcatBorrowerIdentityRegistry.sol:265](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L265) · Purpose: Protects borrower identity resolution and registration state.

#### G-95

`iszero(staticcall(gas(), controller, 0x1c, 0x04, 0, 0x20))` · [src/WildcatBorrowerIdentityRegistry.sol:276](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L276) · Purpose: Protects borrower identity resolution and registration state.

#### G-96

`lt(returndatasize(), 0x20)` · [src/WildcatBorrowerIdentityRegistry.sol:284](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L284) · Purpose: Protects borrower identity resolution and registration state.

#### G-97

`shr(160, controllerOwner)` · [src/WildcatBorrowerIdentityRegistry.sol:288](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L288) · Purpose: Protects borrower identity resolution and registration state.

#### G-98

`iszero(staticcall(gas(), controller, 0x1c, 0x24, 0, 0x20))` · [src/WildcatBorrowerIdentityRegistry.sol:301](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L301) · Purpose: Protects borrower identity resolution and registration state.

#### G-99

`lt(returndatasize(), 0x20)` · [src/WildcatBorrowerIdentityRegistry.sol:310](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L310) · Purpose: Protects borrower identity resolution and registration state.

#### G-100

`gt(isRegistered, 1)` · [src/WildcatBorrowerIdentityRegistry.sol:314](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L314) · Purpose: Protects borrower identity resolution and registration state.

#### G-101

`start > end` · [src/WildcatBorrowerIdentityRegistry.sol:325](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatBorrowerIdentityRegistry.sol#L325) · Purpose: Protects borrower identity resolution and registration state.

#### G-102

`!canReleaseEscrow()` · [src/WildcatSanctionsEscrow.sol:43](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatSanctionsEscrow.sol#L43) · Purpose: Protects sanctions custody and release conditions.

#### G-103

`iszero(staticcall(gas(), sanctionsList, 0x1c, 0x24, 0, 0x20))` · [src/WildcatSanctionsSentinel.sol:88](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatSanctionsSentinel.sol#L88) · Purpose: Protects sanctions custody and release conditions.

#### G-104

`lt(returndatasize(), 0x20)` · [src/WildcatSanctionsSentinel.sol:98](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatSanctionsSentinel.sol#L98) · Purpose: Protects sanctions custody and release conditions.

#### G-105

`gt(isFlagged, 1)` · [src/WildcatSanctionsSentinel.sol:102](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatSanctionsSentinel.sol#L102) · Purpose: Protects sanctions custody and release conditions.

#### G-106

`msg.sender != administrator` · [src/access/BaseAccessControls.sol:156](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L156) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-107

`inputs.roleProviderFactory == address(0) && inputs.newProviderInputs.length > 0` · [src/access/BaseAccessControls.sol:173](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L173) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-108

`newAdministrator == address(0) || newAdministrator == administrator` · [src/access/BaseAccessControls.sol:205](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L205) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-109

`!IWildcatArchController(archController).isRegisteredBorrower(newAdministrator)` · [src/access/BaseAccessControls.sol:209](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L209) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-110

`cancelledPendingAdministrator == address(0)` · [src/access/BaseAccessControls.sol:233](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L233) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-111

`msg.sender != newAdministrator` · [src/access/BaseAccessControls.sol:246](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L246) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-112

`providerAddress == address(0)` · [src/access/BaseAccessControls.sol:289](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L289) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-113

`provider.isNull()` · [src/access/BaseAccessControls.sol:386](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L386) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-114

`callingProvider.isNull()` · [src/access/BaseAccessControls.sol:595](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L595) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-115

`callingProvider.isNull()` · [src/access/BaseAccessControls.sol:608](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L608) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-116

`accounts.length != roleGrantedTimestamps.length` · [src/access/BaseAccessControls.sol:610](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L610) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-117

`roleGrantedTimestamp == 0 || roleGrantedTimestamp > block.timestamp` · [src/access/BaseAccessControls.sol:623](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L623) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-118

`newExpiry < block.timestamp` · [src/access/BaseAccessControls.sol:630](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L630) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-119

`!((status.lastProvider == msg.sender).or(newExpiry > oldExpiry))` · [src/access/BaseAccessControls.sol:642](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L642) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-120

`msg.sender != status.lastProvider` · [src/access/BaseAccessControls.sol:666](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L666) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-121

`administrator_ != administrator` · [src/access/FixedTermHooks.sol:170](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L170) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-122

`hooksData.length < 32` · [src/access/FixedTermHooks.sol:171](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L171) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-123

`fixedTermEndTime < block.timestamp || (fixedTermEndTime - block.timestamp) > MaximumLoanTerm` · [src/access/FixedTermHooks.sol:178](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L178) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-124

`!hookedMarket.depositRequiresAccess` · [src/access/FixedTermHooks.sol:206](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L206) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-125

`!hookedMarket.transfersDisabled && !hookedMarket.transferRequiresAccess` · [src/access/FixedTermHooks.sol:207](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L207) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-126

`!hookedMarket.isHooked` · [src/access/FixedTermHooks.sol:246](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L246) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-127

`newMinimumDeposit > 0 && !_depositHookEnabled[market]` · [src/access/FixedTermHooks.sol:247](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L247) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-128

`!hookedMarket.isHooked` · [src/access/FixedTermHooks.sol:260](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L260) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-129

`!hookedMarket.allowTermReduction && newFixedTermEndTime <= hookedMarket.fixedTermEndTime` · [src/access/FixedTermHooks.sol:261](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L261) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-130

`newFixedTermEndTime > hookedMarket.fixedTermEndTime` · [src/access/FixedTermHooks.sol:263](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L263) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-131

`!market.isHooked` · [src/access/FixedTermHooks.sol:283](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L283) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-132

`!market.isHooked` · [src/access/FixedTermHooks.sol:296](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L296) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-133

`!market.isHooked` · [src/access/FixedTermHooks.sol:333](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L333) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-134

`status.isBlockedFromDeposits` · [src/access/FixedTermHooks.sol:339](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L339) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-135

`MathUtils.mulDiv(market.minimumDeposit, RAY, state.scaleFactor) > scaledAmount` · [src/access/FixedTermHooks.sol:347](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L347) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-136

`market.depositRequiresAccess.and(!hasValidCredential)` · [src/access/FixedTermHooks.sol:361](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L361) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-137

`!market.isHooked` · [src/access/FixedTermHooks.sol:379](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L379) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-138

`market.fixedTermEndTime > block.timestamp` · [src/access/FixedTermHooks.sol:380](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L380) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-139

`!isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)` · [src/access/FixedTermHooks.sol:386](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L386) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-140

`!market.isHooked` · [src/access/FixedTermHooks.sol:417](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L417) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-141

`market.transfersDisabled` · [src/access/FixedTermHooks.sol:419](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L419) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-142

`toStatus.isBlockedFromDeposits` · [src/access/FixedTermHooks.sol:431](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L431) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-143

`market.transferRequiresAccess.and(!hasValidCredential)` · [src/access/FixedTermHooks.sol:439](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L439) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-144

`!market.isHooked` · [src/access/FixedTermHooks.sol:470](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L470) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-145

`!(market.allowTermReduction || market.allowClosureBeforeTerm)` · [src/access/FixedTermHooks.sol:472](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L472) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-146

`(hookedMarket.fixedTermEndTime > block.timestamp) &&
      (annualInterestBips < intermediateState.annualInterestBips)` · [src/access/FixedTermHooks.sol:517](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L517) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-147

`msg.sender != factory` · [src/access/IHooks.sol:44](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/IHooks.sol#L44) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-148

`or(lt(value, min), gt(value, max))` · [src/access/MarketConstraintHooks.sol:82](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/MarketConstraintHooks.sol#L82) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-149

`administrator_ != administrator` · [src/access/OpenTermHooks.sol:131](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L131) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-150

`!hookedMarket.depositRequiresAccess` · [src/access/OpenTermHooks.sol:149](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L149) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-151

`!hookedMarket.transfersDisabled && !hookedMarket.transferRequiresAccess` · [src/access/OpenTermHooks.sol:150](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L150) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-152

`!hookedMarket.isHooked` · [src/access/OpenTermHooks.sol:191](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L191) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-153

`newMinimumDeposit > 0 && !_depositHookEnabled[market]` · [src/access/OpenTermHooks.sol:192](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L192) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-154

`!market.isHooked` · [src/access/OpenTermHooks.sol:207](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L207) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-155

`!market.isHooked` · [src/access/OpenTermHooks.sol:220](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L220) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-156

`!market.isHooked` · [src/access/OpenTermHooks.sol:257](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L257) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-157

`status.isBlockedFromDeposits` · [src/access/OpenTermHooks.sol:263](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L263) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-158

`MathUtils.mulDiv(market.minimumDeposit, RAY, state.scaleFactor) > scaledAmount` · [src/access/OpenTermHooks.sol:271](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L271) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-159

`market.depositRequiresAccess.and(!hasValidCredential)` · [src/access/OpenTermHooks.sol:285](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L285) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-160

`!market.isHooked` · [src/access/OpenTermHooks.sol:303](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L303) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-161

`!isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)` · [src/access/OpenTermHooks.sol:306](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L306) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-162

`!market.isHooked` · [src/access/OpenTermHooks.sol:336](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L336) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-163

`market.transfersDisabled` · [src/access/OpenTermHooks.sol:338](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L338) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-164

`toStatus.isBlockedFromDeposits` · [src/access/OpenTermHooks.sol:350](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L350) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-165

`market.transferRequiresAccess.and(!hasValidCredential)` · [src/access/OpenTermHooks.sol:358](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L358) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-166

`administrator_ != administrator` · [src/access/PeriodicTermHooks.sol:252](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L252) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-167

`hooksData.length < 0x60` · [src/access/PeriodicTermHooks.sol:253](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L253) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-168

`!hookedMarket.depositRequiresAccess` · [src/access/PeriodicTermHooks.sol:295](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L295) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-169

`!hookedMarket.transfersDisabled && !hookedMarket.transferRequiresAccess` · [src/access/PeriodicTermHooks.sol:296](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L296) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-170

`!hookedMarket.isHooked` · [src/access/PeriodicTermHooks.sol:336](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L336) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-171

`newMinimumDeposit > 0 && !hookedMarket.depositHookEnabled` · [src/access/PeriodicTermHooks.sol:337](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L337) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-172

`!hookedMarket.isHooked` · [src/access/PeriodicTermHooks.sol:354](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L354) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-173

`hookedMarket.isClosed` · [src/access/PeriodicTermHooks.sol:355](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L355) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-174

`_isWithdrawalWindowOpen(hookedMarket, block.timestamp)` · [src/access/PeriodicTermHooks.sol:356](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L356) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-175

`annualInterestBips >= IMarketApr(market).annualInterestBips()` · [src/access/PeriodicTermHooks.sol:366](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L366) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-176

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:404](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L404) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-177

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:417](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L417) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-178

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:444](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L444) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-179

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:463](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L463) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-180

`periodDuration < MinimumPeriodDuration || periodDuration > MaximumPeriodDuration` · [src/access/PeriodicTermHooks.sol:508](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L508) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-181

`withdrawalWindowDuration < MinimumWithdrawalWindowDuration ||
      withdrawalWindowDuration >= periodDuration` · [src/access/PeriodicTermHooks.sol:512](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L512) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-182

`firstWithdrawalWindowStart > currentTimestamp + MaximumInitialWithdrawalWindowDelay` · [src/access/PeriodicTermHooks.sol:521](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L521) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-183

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:541](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L541) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-184

`status.isBlockedFromDeposits` · [src/access/PeriodicTermHooks.sol:547](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L547) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-185

`MathUtils.mulDiv(market.minimumDeposit, RAY, state.scaleFactor) > scaledAmount` · [src/access/PeriodicTermHooks.sol:556](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L556) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-186

`market.depositRequiresAccess.and(!hasValidCredential)` · [src/access/PeriodicTermHooks.sol:570](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L570) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-187

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:588](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L588) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-188

`!state.isClosed && !_isWithdrawalWindowOpen(market, block.timestamp)` · [src/access/PeriodicTermHooks.sol:589](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L589) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-189

`!isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)` · [src/access/PeriodicTermHooks.sol:596](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L596) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-190

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:627](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L627) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-191

`market.transfersDisabled` · [src/access/PeriodicTermHooks.sol:629](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L629) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-192

`toStatus.isBlockedFromDeposits` · [src/access/PeriodicTermHooks.sol:641](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L641) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-193

`market.transferRequiresAccess.and(!hasValidCredential)` · [src/access/PeriodicTermHooks.sol:649](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L649) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-194

`!market.isHooked` · [src/access/PeriodicTermHooks.sol:678](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L678) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-195

`pendingAprChange.proposalTimestamp == 0` · [src/access/PeriodicTermHooks.sol:712](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L712) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-196

`pendingAprChange.annualInterestBips != annualInterestBips` · [src/access/PeriodicTermHooks.sol:713](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L713) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-197

`annualInterestBips >= intermediateState.annualInterestBips` · [src/access/PeriodicTermHooks.sol:716](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L716) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-198

`block.timestamp < responseWindowEnd` · [src/access/PeriodicTermHooks.sol:727](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L727) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-199

`block.timestamp >=
      pendingAprChange.responseWindowStart +
        uint256(hookedMarket.periodDuration) *
        AprReductionProposalValidityPeriods` · [src/access/PeriodicTermHooks.sol:729](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L729) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-200

`intermediateState.scaledPendingWithdrawals != 0` · [src/access/PeriodicTermHooks.sol:736](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L736) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-201

`!hookedMarket.isHooked` · [src/access/PeriodicTermHooks.sol:750](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L750) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-202

`!hookedMarket.isHooked` · [src/access/PeriodicTermHooks.sol:776](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L776) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-203

`iszero(success)` · [src/lens/HooksConfigData.sol:105](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/HooksConfigData.sol#L105) · Purpose: Protects the checked accounting or external-return boundary.

#### G-204

`lt(size, 0x40)` · [src/lens/HooksConfigData.sol:114](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/HooksConfigData.sol#L114) · Purpose: Protects the checked accounting or external-return boundary.

#### G-205

`iszero(eq(mload(ptr), 0x20))` · [src/lens/HooksConfigData.sol:117](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/HooksConfigData.sol#L117) · Purpose: Protects the checked accounting or external-return boundary.

#### G-206

`lt(paddedLength, length)` · [src/lens/HooksConfigData.sol:126](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/HooksConfigData.sol#L126) · Purpose: Protects the checked accounting or external-return boundary.

#### G-207

`gt(paddedLength, sub(size, 0x40))` · [src/lens/HooksConfigData.sol:129](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/HooksConfigData.sol#L129) · Purpose: Protects the checked accounting or external-return boundary.

#### G-208

`iszero(success)` · [src/lens/MarketData.sol:133](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/MarketData.sol#L133) · Purpose: Protects the checked accounting or external-return boundary.

#### G-209

`lt(size, 0x40)` · [src/lens/MarketData.sol:141](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/MarketData.sol#L141) · Purpose: Protects the checked accounting or external-return boundary.

#### G-210

`iszero(eq(mload(ptr), 0x20))` · [src/lens/MarketData.sol:144](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/MarketData.sol#L144) · Purpose: Protects the checked accounting or external-return boundary.

#### G-211

`lt(size, 0x60)` · [src/lens/MarketData.sol:151](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/MarketData.sol#L151) · Purpose: Protects the checked accounting or external-return boundary.

#### G-212

`!_isV2Market(address(market))` · [src/lens/MarketData.sol:164](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/MarketData.sol#L164) · Purpose: Protects the checked accounting or external-return boundary.

#### G-213

`iszero(success)` · [src/lens/MarketLens.sol:62](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/lens/MarketLens.sol#L62) · Purpose: Protects the checked accounting or external-return boundary.

#### G-214

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          or(eq(mload(0x00), 1), iszero(returndatasize())), // Returned 1 or nothing.
          call(gas(), token, 0, 0x1c, 0x64, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:60](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/LibERC20.sol#L60) · Purpose: Protects the checked accounting or external-return boundary.

#### G-215

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          or(eq(mload(0x00), 1), iszero(returndatasize())), // Returned 1 or nothing.
          call(gas(), token, 0, 0x10, 0x44, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:84](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/LibERC20.sol#L84) · Purpose: Protects the checked accounting or external-return boundary.

#### G-216

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          gt(returndatasize(), 0x1f), // At least 32 bytes returned.
          staticcall(gas(), token, 0x1c, 0x24, 0x34, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:106](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/LibERC20.sol#L106) · Purpose: Protects the checked accounting or external-return boundary.

#### G-217

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          or(eq(mload(0x00), 1), iszero(returndatasize())), // Returned 1 or nothing.
          call(gas(), token, 0, 0x10, 0x44, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:120](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/LibERC20.sol#L120) · Purpose: Protects the checked accounting or external-return boundary.

#### G-218

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          gt(returndatasize(), 0x1f), // At least 32 bytes returned.
          staticcall(gas(), token, 0x1c, 0x24, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:142](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/LibERC20.sol#L142) · Purpose: Protects the checked accounting or external-return boundary.

#### G-219

`iszero(
        and(
          and(eq(returndatasize(), 0x20), lt(mload(0), 0x100)),
          staticcall(gas(), token, 0x1c, 0x04, 0, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:167](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/LibERC20.sol#L167) · Purpose: Protects the checked accounting or external-return boundary.

#### G-220

`or(iszero(status), iszero(or(isBytes32, gt(returndatasize(), 0x5f))))` · [src/libraries/StringQuery.sol:48](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/StringQuery.sol#L48) · Purpose: Protects the checked accounting or external-return boundary.

#### G-221

`returndatasize()` · [src/libraries/StringQuery.sol:51](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/libraries/StringQuery.sol#L51) · Purpose: Protects the checked accounting or external-return boundary.

#### G-222

`(token == asset).or(token == address(this))` · [src/market/WildcatMarket.sol:33](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L33) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-223

`state.isClosed` · [src/market/WildcatMarket.sol:49](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L49) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-224

`scaledAmount == 0` · [src/market/WildcatMarket.sol:56](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L56) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-225

`amount != actualAmount` · [src/market/WildcatMarket.sol:96](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L96) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-226

`state.accruedProtocolFees == 0` · [src/market/WildcatMarket.sol:103](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L103) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-227

`withdrawableFees == 0` · [src/market/WildcatMarket.sol:106](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L106) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-228

`_flaggedBorrowerIdentity(currentBorrower, currentPrincipal) != address(0)` · [src/market/WildcatMarket.sol:123](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L123) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-229

`state.isClosed` · [src/market/WildcatMarket.sol:128](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L128) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-230

`amount > borrowable` · [src/market/WildcatMarket.sol:131](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L131) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-231

`amount == 0` · [src/market/WildcatMarket.sol:148](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L148) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-232

`state.isClosed` · [src/market/WildcatMarket.sol:149](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L149) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-233

`amount == 0` · [src/market/WildcatMarket.sol:164](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L164) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-234

`state.isClosed` · [src/market/WildcatMarket.sol:170](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L170) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-235

`state.isClosed` · [src/market/WildcatMarket.sol:186](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L186) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-236

`state.scaledPendingWithdrawals != 0` · [src/market/WildcatMarket.sol:261](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L261) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-237

`iszero(
        and(
          eq(returndatasize(), _MARKET_PARAMETERS_SIZE),
          staticcall(
            gas(),
            caller(),
            0x1c,
            0x04,
            marketParametersPointer,
            _MARKET_PARAMETERS_SIZE
          )
        )
      )` · [src/market/WildcatMarketBase.sol:217](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L217) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-238

`parameters.borrower == address(0)` · [src/market/WildcatMarketBase.sol:241](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L241) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-239

`shr(160, registryArchController)` · [src/market/WildcatMarketBase.sol:320](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L320) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-240

`iszero(validRegistry)` · [src/market/WildcatMarketBase.sol:328](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L328) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-241

`parameters.borrowerPrincipal == address(0) ||
      !IWildcatArchController(archController_).isRegisteredBorrower(parameters.borrowerPrincipal)` · [src/market/WildcatMarketBase.sol:336](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L336) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-242

`xor(caller(), _borrower)` · [src/market/WildcatMarketBase.sol:353](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L353) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-243

`flaggedIdentity != address(0)` · [src/market/WildcatMarketBase.sol:377](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L377) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-244

`iszero(newBorrower)` · [src/market/WildcatMarketBase.sol:399](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L399) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-245

`iszero(staticcall(gas(), identityRegistry, 0x1c, 0x24, 0, 0x20))` · [src/market/WildcatMarketBase.sol:416](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L416) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-246

`lt(returndatasize(), 0x20)` · [src/market/WildcatMarketBase.sol:427](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L427) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-247

`shr(160, newBorrowerPrincipal)` · [src/market/WildcatMarketBase.sol:431](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L431) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-248

`xor(newBorrowerPrincipal, expectedPrincipal)` · [src/market/WildcatMarketBase.sol:444](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L444) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-249

`and(
        eq(newBorrower, currentBorrower),
        eq(newBorrowerPrincipal, currentBorrowerPrincipal)
      )` · [src/market/WildcatMarketBase.sol:458](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L458) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-250

`cancelledPendingBorrower == address(0)` · [src/market/WildcatMarketBase.sol:498](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L498) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-251

`msg.sender != newBorrower` · [src/market/WildcatMarketBase.sol:515](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L515) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-252

`_isSanctioned(accountAddress)` · [src/market/WildcatMarketBase.sol:545](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L545) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-253

`iszero(
        and(eq(returndatasize(), 0x20), staticcall(gas(), _sentinel, 0x1c, 0x44, 0, 0x20))
      )` · [src/market/WildcatMarketBase.sol:563](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L563) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-254

`iszero(
        and(eq(returndatasize(), 0x20), staticcall(gas(), sentinelAddress, 0x1c, 0x24, 0, 0x20))
      )` · [src/market/WildcatMarketBase.sol:1102](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1102) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-255

`iszero(
        and(eq(returndatasize(), 0x20), call(gas(), sentinelAddress, 0, 0x1c, 0x64, 0, 0x20))
      )` · [src/market/WildcatMarketBase.sol:1126](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1126) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-256

`msg.sender != wrapperFactory` · [src/market/WildcatMarketConfig.sol:64](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L64) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-257

`registeredWrapper() != address(0)` · [src/market/WildcatMarketConfig.sol:65](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L65) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-258

`accountAddress != address(0) && accountAddress == registeredWrapper()` · [src/market/WildcatMarketConfig.sol:97](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L97) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-259

`!_isSanctioned(accountAddress)` · [src/market/WildcatMarketConfig.sol:100](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L100) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-260

`state.isClosed` · [src/market/WildcatMarketConfig.sol:119](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L119) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-261

`_annualInterestBips > BIP` · [src/market/WildcatMarketConfig.sol:138](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L138) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-262

`_reserveRatioBips > BIP` · [src/market/WildcatMarketConfig.sol:142](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L142) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-263

`state.liquidityRequired() > currentTotalAssets` · [src/market/WildcatMarketConfig.sol:148](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L148) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-264

`state.liquidityRequired() > currentTotalAssets` · [src/market/WildcatMarketConfig.sol:155](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L155) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-265

`state.isClosed` · [src/market/WildcatMarketConfig.sol:181](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L181) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-266

`state.isClosed` · [src/market/WildcatMarketConfig.sol:204](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L204) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-267

`!hooks.useOnExecutePendingAnnualInterestBipsReduction()` · [src/market/WildcatMarketConfig.sol:205](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L205) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-268

`_annualInterestBips >= currentAnnualInterestBips` · [src/market/WildcatMarketConfig.sol:213](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L213) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-269

`msg.sender != factory` · [src/market/WildcatMarketConfig.sol:231](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L231) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-270

`_protocolFeeBips > 1_000` · [src/market/WildcatMarketConfig.sol:232](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L232) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-271

`state.isClosed` · [src/market/WildcatMarketConfig.sol:234](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L234) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-272

`_protocolFeeBips > 0 && feeRecipient == address(0)` · [src/market/WildcatMarketConfig.sol:235](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L235) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-273

`iszero(staticcall(gas(), caller(), 0x1c, 0x04, 0, 0x20))` · [src/market/WildcatMarketRevolving.sol:34](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketRevolving.sol#L34) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-274

`or(lt(returndatasize(), 0x20), shr(16, mload(0)))` · [src/market/WildcatMarketRevolving.sol:45](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketRevolving.sol#L45) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-275

`scaledAmount == 0` · [src/market/WildcatMarketToken.sol:100](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketToken.sol#L100) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-276

`expiry >= block.timestamp` · [src/market/WildcatMarketWithdrawals.sol:69](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L69) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-277

`_withdrawalData.batches[expiry].scaledTotalAmount != 0` · [src/market/WildcatMarketWithdrawals.sol:117](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L117) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-278

`scaledAmount == 0` · [src/market/WildcatMarketWithdrawals.sol:170](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L170) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-279

`amount == 0` · [src/market/WildcatMarketWithdrawals.sol:190](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L190) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-280

`scaledAmount == 0` · [src/market/WildcatMarketWithdrawals.sol:222](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L222) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-281

`accountAddresses.length != expiries.length` · [src/market/WildcatMarketWithdrawals.sol:270](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L270) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-282

`expiry == state.pendingWithdrawalExpiry` · [src/market/WildcatMarketWithdrawals.sol:293](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L293) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-283

`normalizedAmountWithdrawn == 0` · [src/market/WildcatMarketWithdrawals.sol:305](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L305) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-284

`state.isClosed` · [src/market/WildcatMarketWithdrawals.sol:358](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L358) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-285

`account == address(0)` · [src/providers/AccessListRoleProvider.sol:52](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/AccessListRoleProvider.sol#L52) · Purpose: Protects credential issuance, validation or provider administration.

#### G-286

`!_members.add(account)` · [src/providers/AccessListRoleProvider.sol:53](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/AccessListRoleProvider.sol#L53) · Purpose: Protects credential issuance, validation or provider administration.

#### G-287

`!_members.remove(account)` · [src/providers/AccessListRoleProvider.sol:68](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/AccessListRoleProvider.sol#L68) · Purpose: Protects credential issuance, validation or provider administration.

#### G-288

`start > end` · [src/providers/AccessListRoleProvider.sol:88](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/AccessListRoleProvider.sol#L88) · Purpose: Protects credential issuance, validation or provider administration.

#### G-289

`expectedProvider.code.length != 0` · [src/providers/AccessListRoleProviderFactory.sol:36](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/AccessListRoleProviderFactory.sol#L36) · Purpose: Protects credential issuance, validation or provider administration.

#### G-290

`token_.code.length == 0` · [src/providers/ERC1155RoleProvider.sol:27](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC1155RoleProvider.sol#L27) · Purpose: Protects credential issuance, validation or provider administration.

#### G-291

`!skipInterfaceCheck &&
      (!_supportsERC165(token_) || !_supportsInterface(token_, ERC1155_INTERFACE_ID))` · [src/providers/ERC1155RoleProvider.sol:29](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC1155RoleProvider.sol#L29) · Purpose: Protects credential issuance, validation or provider administration.

#### G-292

`expectedProvider.code.length != 0` · [src/providers/ERC1155RoleProviderFactory.sol:35](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC1155RoleProviderFactory.sol#L35) · Purpose: Protects credential issuance, validation or provider administration.

#### G-293

`token_.code.length == 0` · [src/providers/ERC20RoleProvider.sol:22](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC20RoleProvider.sol#L22) · Purpose: Protects credential issuance, validation or provider administration.

#### G-294

`minBalance_ == 0` · [src/providers/ERC20RoleProvider.sol:23](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC20RoleProvider.sol#L23) · Purpose: Protects credential issuance, validation or provider administration.

#### G-295

`expectedProvider.code.length != 0` · [src/providers/ERC20RoleProviderFactory.sol:35](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC20RoleProviderFactory.sol#L35) · Purpose: Protects credential issuance, validation or provider administration.

#### G-296

`vault_.code.length == 0` · [src/providers/ERC4626AssetsRoleProvider.sol:23](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC4626AssetsRoleProvider.sol#L23) · Purpose: Protects credential issuance, validation or provider administration.

#### G-297

`minAssets_ == 0` · [src/providers/ERC4626AssetsRoleProvider.sol:24](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC4626AssetsRoleProvider.sol#L24) · Purpose: Protects credential issuance, validation or provider administration.

#### G-298

`expectedProvider.code.length != 0` · [src/providers/ERC4626AssetsRoleProviderFactory.sol:35](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC4626AssetsRoleProviderFactory.sol#L35) · Purpose: Protects credential issuance, validation or provider administration.

#### G-299

`token_.code.length == 0` · [src/providers/ERC5192RoleProvider.sol:36](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC5192RoleProvider.sol#L36) · Purpose: Protects credential issuance, validation or provider administration.

#### G-300

`!skipInterfaceCheck &&
      (!_supportsERC165(token_) ||
        !_supportsInterface(token_, ERC721_INTERFACE_ID) ||
        !_supportsInterface(token_, ERC5192_INTERFACE_ID))` · [src/providers/ERC5192RoleProvider.sol:38](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC5192RoleProvider.sol#L38) · Purpose: Protects credential issuance, validation or provider administration.

#### G-301

`token_.code.length == 0` · [src/providers/ERC5484RoleProvider.sol:37](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC5484RoleProvider.sol#L37) · Purpose: Protects credential issuance, validation or provider administration.

#### G-302

`allowedBurnAuthMask_ == 0 || allowedBurnAuthMask_ > 0x0f` · [src/providers/ERC5484RoleProvider.sol:38](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC5484RoleProvider.sol#L38) · Purpose: Protects credential issuance, validation or provider administration.

#### G-303

`!skipInterfaceCheck &&
      (!_supportsERC165(token_) ||
        !_supportsInterface(token_, ERC721_INTERFACE_ID) ||
        !_supportsInterface(token_, ERC5484_INTERFACE_ID))` · [src/providers/ERC5484RoleProvider.sol:42](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC5484RoleProvider.sol#L42) · Purpose: Protects credential issuance, validation or provider administration.

#### G-304

`token_.code.length == 0` · [src/providers/ERC721RoleProvider.sol:26](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC721RoleProvider.sol#L26) · Purpose: Protects credential issuance, validation or provider administration.

#### G-305

`!skipInterfaceCheck &&
      (!_supportsERC165(token_) || !_supportsInterface(token_, ERC721_INTERFACE_ID))` · [src/providers/ERC721RoleProvider.sol:28](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC721RoleProvider.sol#L28) · Purpose: Protects credential issuance, validation or provider administration.

#### G-306

`expectedProvider.code.length != 0` · [src/providers/ERC721RoleProviderFactory.sol:35](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ERC721RoleProviderFactory.sol#L35) · Purpose: Protects credential issuance, validation or provider administration.

#### G-307

`msg.sender != administrator` · [src/providers/ManagedRoleProvider.sol:14](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ManagedRoleProvider.sol#L14) · Purpose: Protects credential issuance, validation or provider administration.

#### G-308

`administrator_ == address(0)` · [src/providers/ManagedRoleProvider.sol:20](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ManagedRoleProvider.sol#L20) · Purpose: Protects credential issuance, validation or provider administration.

#### G-309

`newAdministrator == address(0) || newAdministrator == administrator` · [src/providers/ManagedRoleProvider.sol:30](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ManagedRoleProvider.sol#L30) · Purpose: Protects credential issuance, validation or provider administration.

#### G-310

`cancelledPendingAdministrator == address(0)` · [src/providers/ManagedRoleProvider.sol:45](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ManagedRoleProvider.sol#L45) · Purpose: Protects credential issuance, validation or provider administration.

#### G-311

`msg.sender != newAdministrator` · [src/providers/ManagedRoleProvider.sol:56](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/ManagedRoleProvider.sol#L56) · Purpose: Protects credential issuance, validation or provider administration.

#### G-312

`expectedProvider.code.length != 0` · [src/providers/MerkleRoleProviderFactory.sol:36](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/providers/MerkleRoleProviderFactory.sol#L36) · Purpose: Protects credential issuance, validation or provider administration.

#### G-313

`msg.sender != sphereXAdmin()` · [src/spherex/SphereXConfig.sol:73](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXConfig.sol#L73) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-314

`msg.sender != sphereXOperator()` · [src/spherex/SphereXConfig.sol:80](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXConfig.sol#L80) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-315

`msg.sender != sphereXOperator() && msg.sender != sphereXAdmin()` · [src/spherex/SphereXConfig.sol:87](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXConfig.sol#L87) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-316

`msg.sender != pendingSphereXAdmin()` · [src/spherex/SphereXConfig.sol:131](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXConfig.sol#L131) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-317

`newSphereXEngine != address(0) &&
      !ISphereXEngine(newSphereXEngine).supportsInterface(type(ISphereXEngine).interfaceId)` · [src/spherex/SphereXConfig.sol:159](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXConfig.sol#L159) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-318

`msg.sender != _archController` · [src/spherex/SphereXProtectedRegisteredBase.sol:69](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXProtectedRegisteredBase.sol#L69) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-319

`iszero(
        and(eq(mload(0), 0x20), call(gas(), engineAddress, 0, add(pointer, 28), size, 0, 0x40))
      )` · [src/spherex/SphereXProtectedRegisteredBase.sol:168](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXProtectedRegisteredBase.sol#L168) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-320

`iszero(call(gas(), sphereXEngineAddress, 0, add(slotBefore, 28), calldataSize, 0, 0))` · [src/spherex/SphereXProtectedRegisteredBase.sol:262](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/spherex/SphereXProtectedRegisteredBase.sol#L262) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-321

`iszero(call(gas(), target, 0, calldataPointer, calldataSize, 0, 0))` · [src/types/HooksConfig.sol:106](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/types/HooksConfig.sol#L106) · Purpose: Protects the checked accounting or external-return boundary.

#### G-322

`or(
          lt(returndatasize(), 0x40),
          iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0x40))
        )` · [src/types/HooksConfig.sol:820](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/types/HooksConfig.sol#L820) · Purpose: Protects the checked accounting or external-return boundary.

#### G-323

`eq(outOfPlaceEncoding, lt(length, 32))` · [src/types/TransientBytesArray.sol:30](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/types/TransientBytesArray.sol#L30) · Purpose: Protects the checked accounting or external-return boundary.

#### G-324

`marketAddress == address(0)` · [src/vault/Wildcat4626Wrapper.sol:95](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L95) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-325

`msg.sender != _readMarketAddress(IWildcatMarketToken.wrapperFactory.selector)` · [src/vault/Wildcat4626Wrapper.sol:98](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L98) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-326

`currentBorrower == address(0)` · [src/vault/Wildcat4626Wrapper.sol:102](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L102) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-327

`_readMarketAddress(IWildcatMarketToken.borrowerPrincipal.selector) == address(0)` · [src/vault/Wildcat4626Wrapper.sol:103](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L103) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-328

`sentinel == address(0)` · [src/vault/Wildcat4626Wrapper.sol:107](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L107) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-329

`assets == 0` · [src/vault/Wildcat4626Wrapper.sol:321](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L321) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-330

`assets > limit` · [src/vault/Wildcat4626Wrapper.sol:324](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L324) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-331

`expectedShares == 0` · [src/vault/Wildcat4626Wrapper.sol:329](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L329) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-332

`shares != expectedShares` · [src/vault/Wildcat4626Wrapper.sol:345](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L345) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-333

`shares == 0` · [src/vault/Wildcat4626Wrapper.sol:360](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L360) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-334

`assets == 0 || shares > _convertToSharesDown(assets, scaleFactor)` · [src/vault/Wildcat4626Wrapper.sol:364](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L364) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-335

`expectedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:374](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L374) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-336

`mintedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:390](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L390) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-337

`assets == 0` · [src/vault/Wildcat4626Wrapper.sol:408](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L408) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-338

`shares == 0` · [src/vault/Wildcat4626Wrapper.sol:413](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L413) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-339

`burnedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:433](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L433) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-340

`shares == 0` · [src/vault/Wildcat4626Wrapper.sol:448](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L448) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-341

`assets == 0` · [src/vault/Wildcat4626Wrapper.sol:457](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L457) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-342

`burnedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:473](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L473) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-343

`account == address(this)` · [src/vault/Wildcat4626Wrapper.sol:484](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L484) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-344

`!_isSanctioned(account)` · [src/vault/Wildcat4626Wrapper.sol:485](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L485) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-345

`iszero(call(gas(), marketAddress, 0, freeMemoryPointer, calldatasize(), 0, 0))` · [src/vault/Wildcat4626Wrapper.sol:491](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L491) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-346

`msg.sender != _readMarketAddress(IWildcatMarketToken.borrower.selector)` · [src/vault/Wildcat4626Wrapper.sol:517](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L517) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-347

`token == address(0) || to == address(0)` · [src/vault/Wildcat4626Wrapper.sol:520](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L520) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-348

`scaledBefore <= expectedScaled` · [src/vault/Wildcat4626Wrapper.sol:529](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L529) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-349

`amount == 0` · [src/vault/Wildcat4626Wrapper.sol:536](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L536) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-350

`sweptScaled != strandedScaled` · [src/vault/Wildcat4626Wrapper.sol:545](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L545) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-351

`amount == 0` · [src/vault/Wildcat4626Wrapper.sol:548](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L548) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-352

`iszero(staticcall(gas(), marketAddress, add(pointer, 0x1c), 0x04, pointer, 0x20))` · [src/vault/Wildcat4626Wrapper.sol:573](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L573) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-353

`lt(returndatasize(), 0x20)` · [src/vault/Wildcat4626Wrapper.sol:582](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L582) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-354

`iszero(staticcall(gas(), marketAddress, add(pointer, 0x1c), 0x24, pointer, 0x20))` · [src/vault/Wildcat4626Wrapper.sol:601](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L601) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-355

`lt(returndatasize(), 0x20)` · [src/vault/Wildcat4626Wrapper.sol:607](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L607) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-356

`shr(160, word)` · [src/vault/Wildcat4626Wrapper.sol:675](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L675) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-357

`iszero(staticcall(gas(), sentinel, add(pointer, 0x1c), 0x44, pointer, 0x20))` · [src/vault/Wildcat4626Wrapper.sol:792](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L792) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-358

`lt(returndatasize(), 0x20)` · [src/vault/Wildcat4626Wrapper.sol:799](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L799) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-359

`gt(isSanctioned_, 1)` · [src/vault/Wildcat4626Wrapper.sol:803](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L803) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-360

`iszero(staticcall(gas(), sentinel, add(pointer, 0x1c), 0x64, pointer, 0x20))` · [src/vault/Wildcat4626Wrapper.sol:860](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L860) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-361

`lt(returndatasize(), 0x20)` · [src/vault/Wildcat4626Wrapper.sol:865](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L865) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-362

`shr(160, escrow)` · [src/vault/Wildcat4626Wrapper.sol:872](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L872) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-363

`!_canReceiveMarketTokens()` · [src/vault/Wildcat4626Wrapper.sol:923](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L923) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-364

`scaledBacking < shareSupply` · [src/vault/Wildcat4626Wrapper.sol:957](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L957) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-365

`_isSanctioned(account)` · [src/vault/Wildcat4626Wrapper.sol:978](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L978) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-366

`_isSanctioned(account, principal)` · [src/vault/Wildcat4626Wrapper.sol:984](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L984) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-367

`to != escrow` · [src/vault/Wildcat4626Wrapper.sol:1000](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L1000) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-368

`toIsSanctioned` · [src/vault/Wildcat4626Wrapper.sol:1004](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L1004) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-369

`!success || data.length < 0x20` · [src/vault/Wildcat4626WrapperFactory.sol:82](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L82) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-370

`market == address(0)` · [src/vault/Wildcat4626WrapperFactory.sol:143](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L143) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-371

`_wrapperForMarket[market] != address(0)` · [src/vault/Wildcat4626WrapperFactory.sol:145](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L145) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-372

`address(v1Factory) == address(0)` · [src/vault/Wildcat4626WrapperFactory.sol:150](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L150) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-373

`rounding != FloorRounding` · [src/vault/Wildcat4626WrapperFactory.sol:155](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L155) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-374

`!archController.isRegisteredMarket(market)` · [src/vault/Wildcat4626WrapperFactory.sol:157](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L157) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-375

`_validateTransferPolicy(market)` · [src/vault/Wildcat4626WrapperFactory.sol:158](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L158) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

## 2. Inferred Invariants (Single-Contract)

#### I-1

`Conservation` · On-chain: **Yes**

> In the full market runtime, scaledTotalSupply equals the sum of account scaled balances plus scaledPendingWithdrawals at the end of each successful external call, after all paired storage writes complete.

Derivation: Δ-pair: [src/market/WildcatMarket.sol:66](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L66) and [src/market/WildcatMarket.sol:73](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L73) add the same deposit amount; [src/market/WildcatMarketWithdrawals.sol:130](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L130) and [src/market/WildcatMarketWithdrawals.sol:140](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L140) move it from account to pending; [src/market/WildcatMarketBase.sol:1023](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1023) through [src/market/WildcatMarketBase.sol:1031](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1031) burn pending and total equally. Transfer writes at [src/market/WildcatMarketToken.sol:105](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketToken.sol#L105) and [src/market/WildcatMarketToken.sol:109](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketToken.sol#L109) conserve the account sum. Batched write-site search found these durable writers; constructor fields start at zero, and pure simulation helpers do not persist their memory copies.

If violated: The aggregate market-token claim would differ from allocated account and queued balances.

#### I-2

`Conservation` · On-chain: **Yes**

> A successful batch payment increases normalizedUnclaimedWithdrawals and that batch normalizedAmountPaid by the same amount, while reducing pending and total scaled supply by the same burn.

Derivation: Δ-pair: [src/market/WildcatMarketBase.sol:1024](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1024) and [src/market/WildcatMarketBase.sol:1028](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1028); paired scaled reductions at [src/market/WildcatMarketBase.sol:1025](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1025) and [src/market/WildcatMarketBase.sol:1031](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1031) occur in _applyWithdrawalBatchPayment without an external call between the writes.

If violated: Reserved claim accounting would diverge from the batch payment record.

#### I-3

`Ratio` · On-chain: **Yes**

> For each successful withdrawal claim, the recorded total is floor(batch.normalizedAmountPaid × status.scaledAmount / batch.scaledTotalAmount), evaluated before updating the claim; the paid increment is the checked difference from its prior total.

Derivation: Δ-pair and ratio: [src/market/WildcatMarketWithdrawals.sol:299](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L299) computes newTotalWithdrawn; [src/market/WildcatMarketWithdrawals.sol:303](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L303) subtracts the old storage value before [src/market/WildcatMarketWithdrawals.sol:315](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L315) assigns it and subtracts the same increment from normalizedUnclaimedWithdrawals. This is the only durable claim-total assignment; the getter copies storage to memory.

If violated: An account could receive a payment inconsistent with its scaled share of the paid batch.

#### I-4

`StateMachine` · On-chain: **Yes**

> A full market can transition from open to closed once; no scoped action reopens it.

Derivation: edge: constructor isClosed=false at [src/market/WildcatMarketBase.sol:265](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L265) → closeMarket isClosed=true at [src/market/WildcatMarket.sol:205](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarket.sol#L205). closeMarket rejects an already closed state; all state-write sites preserve this field except that transition.

If violated: The close settlement assumptions could be reused after operations resume.

#### I-5

`StateMachine` · On-chain: **Yes**

> For each account/market pair in these concrete templates, once isKnownLenderOnMarket becomes true it remains true. Credential revocation and deposit blocks do not reset it.

Derivation: edge: false → true; [src/access/BaseAccessControls.sol:982](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L982). All write sites: [src/access/BaseAccessControls.sol:982](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/BaseAccessControls.sol#L982). Full bodies and batched rg over all scoped files locate exactly one assignment to this mapping; it stores true only.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-6

`Temporal` · On-chain: **Yes**

> Passing temporary reserve expiry alone does not remove the stored record; a subsequent APR callback must take a cancellation/expiry branch.

Derivation: temporal: tmp.expiry > 0 and block.timestamp >= tmp.expiry; [src/access/MarketConstraintHooks.sol:218](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/MarketConstraintHooks.sol#L218), [src/access/MarketConstraintHooks.sol:232](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/MarketConstraintHooks.sol#L232), [src/access/MarketConstraintHooks.sol:278](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/MarketConstraintHooks.sol#L278). All write sites: [src/access/MarketConstraintHooks.sol:232](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/MarketConstraintHooks.sol#L232), [src/access/MarketConstraintHooks.sol:278](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/MarketConstraintHooks.sol#L278). Only delete/update sites are in onSetAnnualInterestAndReserveRatioBips.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-7

`Bound` · On-chain: **Yes**

> A stored positive minimumDeposit implies the deposit callback was enabled at creation.

Derivation: guard-lift: positive minimumDeposit requires the immutable deposit callback; exact setter rejection predicate is newMinimumDeposit > 0 && !_depositHookEnabled[market]; [src/access/OpenTermHooks.sol:123](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L123), [src/access/OpenTermHooks.sol:189](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L189). All write sites: [src/access/OpenTermHooks.sol:176](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L176), [src/access/OpenTermHooks.sol:177](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L177), [src/access/OpenTermHooks.sol:194](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/OpenTermHooks.sol#L194). Creation forces the deposit flag for a positive minimum and records it. The only later minimum setter rejects a positive value when that flag is absent.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-8

`Bound` · On-chain: **Yes**

> A stored positive minimumDeposit implies the deposit callback was enabled at creation.

Derivation: guard-lift: positive minimumDeposit requires the immutable deposit callback; exact setter rejection predicate is newMinimumDeposit > 0 && !_depositHookEnabled[market]; [src/access/FixedTermHooks.sol:162](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L162), [src/access/FixedTermHooks.sol:244](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L244). All write sites: [src/access/FixedTermHooks.sol:231](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L231), [src/access/FixedTermHooks.sol:232](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L232), [src/access/FixedTermHooks.sol:249](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/FixedTermHooks.sol#L249). Creation forces the deposit flag for a positive minimum and records it. The only later minimum setter rejects a positive value when that flag is absent.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-9

`Bound` · On-chain: **Yes**

> A stored positive minimumDeposit implies the deposit callback was enabled at creation.

Derivation: guard-lift: positive minimumDeposit requires the immutable deposit callback; exact setter rejection predicate is newMinimumDeposit > 0 && !hookedMarket.depositHookEnabled; [src/access/PeriodicTermHooks.sol:245](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L245), [src/access/PeriodicTermHooks.sol:334](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L334). All write sites: [src/access/PeriodicTermHooks.sol:321](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L321), [src/access/PeriodicTermHooks.sol:340](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/access/PeriodicTermHooks.sol#L340). Creation forces the deposit flag for a positive minimum and records it. The only later minimum setter rejects a positive value when that flag is absent.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-10

`StateMachine` · On-chain: **Yes**

> A successful market borrower acceptance clears both pending fields and replaces the operational borrower and its revalidated principal atomically.

Derivation: edge: pending actor at [src/market/WildcatMarketBase.sol:514](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L514) → cleared pending slots and replacement borrower/principal at [src/market/WildcatMarketBase.sol:525](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L525). Request writes both pending fields at [src/market/WildcatMarketBase.sol:483](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L483); cancel clears both at [src/market/WildcatMarketBase.sol:500](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L500). Acceptance rechecks the stored expected principal in [src/market/WildcatMarketBase.sol:384](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L384). These are all writers of the pending address slots.

If violated: Market authority and its sanctions identity could disagree with the accepted transfer.

## 3. Inferred Invariants (Cross-Contract)

#### X-1

On-chain: **Yes**

> Withdrawal execution routes a sanctioned claimant to an escrow bound to the principal/borrower, account and underlying token; successful release pays that bound account.

Caller side: [src/market/WildcatMarketWithdrawals.sol:318](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketWithdrawals.sol#L318) selects escrow instead of the claimant; [src/market/WildcatMarketBase.sol:1113](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketBase.sol#L1113) supplies the borrower identity and underlying asset.

Callee side: [src/WildcatSanctionsSentinel.sol:135](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatSanctionsSentinel.sol#L135) creates the deterministic escrow and constructor input; [src/WildcatSanctionsEscrow.sol:21](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/WildcatSanctionsEscrow.sol#L21) fixes the account and token, and releaseEscrow reads the release predicate before paying that account.

If violated: Sanctions custody could be associated with a different account or token.

#### X-2

On-chain: **Yes**

> Successful wrapper deposit/mint accounting is checked against the actual change in the wrapped market scaled balance, under the generation-specific rounding convention.

Caller side: [src/vault/Wildcat4626Wrapper.sol:316](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626Wrapper.sol#L316) measures market scaled balances across transferFrom and compares minted shares; mint has its own measured path in the same source file.

Callee side: [src/market/WildcatMarketToken.sol:91](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketToken.sol#L91) updates market account scaled balances using floor conversion. The external asset must actually be the named in-scope market for this paired property.

If violated: Wrapper share issuance would diverge from the scaled market claims received.

#### X-3

On-chain: **Yes**

> The named wrapper factory creates a nonzero wrapper before setting the market registration; the market admits only its immutable wrapperFactory and a currently empty slot.

Caller side: [src/vault/Wildcat4626WrapperFactory.sol:160](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/vault/Wildcat4626WrapperFactory.sol#L160) creates the contract and calls registerWrapper at line 162.

Callee side: [src/market/WildcatMarketConfig.sol:63](https://github.com/wildcat-finance/v2-protocol/blob/bea503c2736d47de7fd34130c64f10783dc35b39/src/market/WildcatMarketConfig.sol#L63) checks caller and empty slot before assigning it. The market body alone accepts zero; the nonzero property is limited to this factory path.

If violated: A wrapper address could be inconsistent with the generation and factory selected by the market.

## 4. Economic Invariants

#### E-1

On-chain: **Yes**

> Batch payment converts interest-bearing scaled debt to normalized claim reserves; claiming reduces those reserves by the increment recorded as withdrawn.

Follows from: I-1 + I-2 + I-3; executeWithdrawal subtracts the same increment from normalizedUnclaimedWithdrawals before transferring it. This is claim bookkeeping, not a guarantee of borrower solvency.

If violated: Queued scaled debt and paid normalized claims could be counted inconsistently.
