# Properties of `src/market/` and the hooks

> Wildcat V2 | f5a26146987926f4811b72a795d662813dedfe85 | 176 guards | 11 inferred properties

These are source-derived properties and explicit limits. On-chain “Yes” means the cited source paths enforce the bounded statement; no runtime property campaign result is claimed.

## 1. Enforced Guards (Reference)

Exact rejection predicates appear below. Multiline predicates retain their source whitespace; each has a source location and purpose.

#### G-1

`msg.sender != IWildcatArchController(_archController).owner()` · [src/HooksFactory.sol:147](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L147) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-2

`_templateDetails[hooksTemplate].exists` · [src/HooksFactory.sol:165](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L165) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-3

`(protocolFeeBips > 0 && nullFeeRecipient) ||
      (hasOriginationFee && nullFeeRecipient) ||
      (hasOriginationFee && nullOriginationFeeAsset) ||
      protocolFeeBips > 1_000` · [src/HooksFactory.sol:200](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L200) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-4

`!_templateDetails[hooksTemplate].exists` · [src/HooksFactory.sol:220](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L220) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-5

`!_templateDetails[hooksTemplate].exists` · [src/HooksFactory.sol:239](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L239) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-6

`!IWildcatArchController(_archController).isRegisteredBorrower(msg.sender)` · [src/HooksFactory.sol:316](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L316) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-7

`!template.exists` · [src/HooksFactory.sol:343](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L343) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-8

`!template.enabled` · [src/HooksFactory.sol:346](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L346) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-9

`iszero(hooksInstance)` · [src/HooksFactory.sol:372](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L372) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-10

`gt(length, 0x3f)` · [src/HooksFactory.sol:460](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L460) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-11

`IWildcatArchController(_archController).isBlacklistedAsset(parameters.asset)` · [src/HooksFactory.sol:481](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L481) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-12

`!(address(bytes20(salt)) == msg.sender || bytes20(salt) == bytes20(0))` · [src/HooksFactory.sol:486](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L486) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-13

`originationFeeAsset != templateDetails.originationFeeAsset ||
      originationFeeAmount != templateDetails.originationFeeAmount` · [src/HooksFactory.sol:491](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L491) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-14

`market.code.length != 0` · [src/HooksFactory.sol:543](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L543) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-15

`!IWildcatArchController(_archController).isRegisteredBorrower(msg.sender)` · [src/HooksFactory.sol:578](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L578) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-16

`hooksTemplate == address(0)` · [src/HooksFactory.sol:583](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L583) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-17

`!IWildcatArchController(_archController).isRegisteredBorrower(msg.sender)` · [src/HooksFactory.sol:607](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L607) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-18

`!templateDetails.exists` · [src/HooksFactory.sol:611](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L611) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-19

`!details.exists` · [src/HooksFactory.sol:639](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L639) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-20

`iszero(call(gas(), market, 0, setProtocolFeeBipsCalldataPointer, 0x24, 0, 0))` · [src/HooksFactory.sol:660](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/HooksFactory.sol#L660) · Purpose: Protects deployment parameters, registration or factory authority.

#### G-21

`_reentrancyGuard` · [src/ReentrancyGuard.sol:64](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/ReentrancyGuard.sol#L64) · Purpose: Protects the checked accounting or external-return boundary.

#### G-22

`tload(_REENTRANCY_GUARD_SLOT)` · [src/ReentrancyGuard.sol:93](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/ReentrancyGuard.sol#L93) · Purpose: Protects the checked accounting or external-return boundary.

#### G-23

`iszero(call(gas(), target, 0, add(data, 0x20), mload(data), 0, 0))` · [src/WildcatArchController.sol:146](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L146) · Purpose: Protects registration and controller authority.

#### G-24

`!_borrowers.add(borrower)` · [src/WildcatArchController.sol:158](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L158) · Purpose: Protects registration and controller authority.

#### G-25

`!_borrowers.remove(borrower)` · [src/WildcatArchController.sol:165](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L165) · Purpose: Protects registration and controller authority.

#### G-26

`!_assetBlacklist.add(asset)` · [src/WildcatArchController.sol:201](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L201) · Purpose: Protects registration and controller authority.

#### G-27

`!_assetBlacklist.remove(asset)` · [src/WildcatArchController.sol:208](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L208) · Purpose: Protects registration and controller authority.

#### G-28

`!_controllerFactories.add(factory)` · [src/WildcatArchController.sol:244](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L244) · Purpose: Protects registration and controller authority.

#### G-29

`!_controllerFactories.remove(factory)` · [src/WildcatArchController.sol:252](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L252) · Purpose: Protects registration and controller authority.

#### G-30

`!_controllerFactories.contains(msg.sender)` · [src/WildcatArchController.sol:288](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L288) · Purpose: Protects registration and controller authority.

#### G-31

`!_controllers.add(controller)` · [src/WildcatArchController.sol:295](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L295) · Purpose: Protects registration and controller authority.

#### G-32

`!_controllers.remove(controller)` · [src/WildcatArchController.sol:303](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L303) · Purpose: Protects registration and controller authority.

#### G-33

`!_controllers.contains(msg.sender)` · [src/WildcatArchController.sol:339](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L339) · Purpose: Protects registration and controller authority.

#### G-34

`!_markets.add(market)` · [src/WildcatArchController.sol:346](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L346) · Purpose: Protects registration and controller authority.

#### G-35

`!_markets.remove(market)` · [src/WildcatArchController.sol:354](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatArchController.sol#L354) · Purpose: Protects registration and controller authority.

#### G-36

`!canReleaseEscrow()` · [src/WildcatSanctionsEscrow.sol:35](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatSanctionsEscrow.sol#L35) · Purpose: Protects sanctions custody and release conditions.

#### G-37

`msg.sender != borrower` · [src/access/BaseAccessControls.sol:88](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L88) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-38

`providerAddress == address(0)` · [src/access/BaseAccessControls.sol:151](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L151) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-39

`provider.isNull()` · [src/access/BaseAccessControls.sol:208](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L208) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-40

`callingProvider.isNull()` · [src/access/BaseAccessControls.sol:373](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L373) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-41

`callingProvider.isNull()` · [src/access/BaseAccessControls.sol:390](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L390) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-42

`accounts.length != roleGrantedTimestamps.length` · [src/access/BaseAccessControls.sol:392](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L392) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-43

`newExpiry < block.timestamp` · [src/access/BaseAccessControls.sol:408](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L408) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-44

`!((status.lastProvider == msg.sender).or(newExpiry > oldExpiry))` · [src/access/BaseAccessControls.sol:420](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L420) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-45

`msg.sender != status.lastProvider` · [src/access/BaseAccessControls.sol:441](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L441) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-46

`deployer != borrower` · [src/access/FixedTermHooks.sol:164](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L164) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-47

`hooksData.length < 32` · [src/access/FixedTermHooks.sol:165](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L165) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-48

`fixedTermEndTime < block.timestamp || (fixedTermEndTime - block.timestamp) > MaximumLoanTerm` · [src/access/FixedTermHooks.sol:172](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L172) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-49

`!hookedMarket.isHooked` · [src/access/FixedTermHooks.sol:222](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L222) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-50

`!hookedMarket.isHooked` · [src/access/FixedTermHooks.sol:229](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L229) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-51

`!hookedMarket.allowTermReduction && newFixedTermEndTime <= hookedMarket.fixedTermEndTime` · [src/access/FixedTermHooks.sol:230](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L230) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-52

`newFixedTermEndTime > hookedMarket.fixedTermEndTime` · [src/access/FixedTermHooks.sol:232](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L232) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-53

`!market.isHooked` · [src/access/FixedTermHooks.sol:270](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L270) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-54

`status.isBlockedFromDeposits` · [src/access/FixedTermHooks.sol:276](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L276) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-55

`market.minimumDeposit > normalizedAmount` · [src/access/FixedTermHooks.sol:280](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L280) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-56

`market.depositRequiresAccess.and(!hasValidCredential)` · [src/access/FixedTermHooks.sol:293](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L293) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-57

`!market.isHooked` · [src/access/FixedTermHooks.sol:314](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L314) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-58

`market.fixedTermEndTime > block.timestamp` · [src/access/FixedTermHooks.sol:315](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L315) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-59

`!isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)` · [src/access/FixedTermHooks.sol:321](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L321) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-60

`!market.isHooked` · [src/access/FixedTermHooks.sol:361](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L361) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-61

`market.transfersDisabled` · [src/access/FixedTermHooks.sol:363](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L363) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-62

`toStatus.isBlockedFromDeposits` · [src/access/FixedTermHooks.sol:371](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L371) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-63

`market.transferRequiresAccess.and(!hasValidCredential)` · [src/access/FixedTermHooks.sol:379](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L379) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-64

`!market.isHooked` · [src/access/FixedTermHooks.sol:410](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L410) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-65

`!(market.allowTermReduction || market.allowClosureBeforeTerm)` · [src/access/FixedTermHooks.sol:412](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L412) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-66

`(hookedMarket.fixedTermEndTime > block.timestamp) &&
      (annualInterestBips < intermediateState.annualInterestBips)` · [src/access/FixedTermHooks.sol:447](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L447) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-67

`msg.sender != factory` · [src/access/IHooks.sol:31](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/IHooks.sol#L31) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-68

`or(lt(value, min), gt(value, max))` · [src/access/MarketConstraintHooks.sol:64](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/MarketConstraintHooks.sol#L64) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-69

`deployer != borrower` · [src/access/OpenTermHooks.sol:135](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L135) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-70

`!hookedMarket.isHooked` · [src/access/OpenTermHooks.sol:177](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L177) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-71

`!market.isHooked` · [src/access/OpenTermHooks.sol:216](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L216) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-72

`status.isBlockedFromDeposits` · [src/access/OpenTermHooks.sol:222](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L222) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-73

`market.minimumDeposit > normalizedAmount` · [src/access/OpenTermHooks.sol:226](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L226) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-74

`market.depositRequiresAccess.and(!hasValidCredential)` · [src/access/OpenTermHooks.sol:239](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L239) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-75

`!isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)` · [src/access/OpenTermHooks.sol:261](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L261) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-76

`!market.isHooked` · [src/access/OpenTermHooks.sol:300](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L300) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-77

`market.transfersDisabled` · [src/access/OpenTermHooks.sol:302](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L302) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-78

`toStatus.isBlockedFromDeposits` · [src/access/OpenTermHooks.sol:310](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L310) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-79

`market.transferRequiresAccess.and(!hasValidCredential)` · [src/access/OpenTermHooks.sol:318](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L318) · Purpose: Protects hook policy, credential state or the authority needed to change it.

#### G-80

`!isV2` · [src/lens/MarketData.sol:88](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/lens/MarketData.sol#L88) · Purpose: Protects the checked accounting or external-return boundary.

#### G-81

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          or(eq(mload(0x00), 1), iszero(returndatasize())), // Returned 1 or nothing.
          call(gas(), token, 0, 0x1c, 0x64, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:60](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/LibERC20.sol#L60) · Purpose: Protects the checked accounting or external-return boundary.

#### G-82

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          or(eq(mload(0x00), 1), iszero(returndatasize())), // Returned 1 or nothing.
          call(gas(), token, 0, 0x10, 0x44, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:84](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/LibERC20.sol#L84) · Purpose: Protects the checked accounting or external-return boundary.

#### G-83

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          gt(returndatasize(), 0x1f), // At least 32 bytes returned.
          staticcall(gas(), token, 0x1c, 0x24, 0x34, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:106](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/LibERC20.sol#L106) · Purpose: Protects the checked accounting or external-return boundary.

#### G-84

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          or(eq(mload(0x00), 1), iszero(returndatasize())), // Returned 1 or nothing.
          call(gas(), token, 0, 0x10, 0x44, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:120](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/LibERC20.sol#L120) · Purpose: Protects the checked accounting or external-return boundary.

#### G-85

`iszero(
        and(
          // The arguments of `and` are evaluated from right to left.
          gt(returndatasize(), 0x1f), // At least 32 bytes returned.
          staticcall(gas(), token, 0x1c, 0x24, 0x00, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:142](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/LibERC20.sol#L142) · Purpose: Protects the checked accounting or external-return boundary.

#### G-86

`iszero(
        and(
          and(eq(returndatasize(), 0x20), lt(mload(0), 0x100)),
          staticcall(gas(), token, 0x1c, 0x04, 0, 0x20)
        )
      )` · [src/libraries/LibERC20.sol:167](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/LibERC20.sol#L167) · Purpose: Protects the checked accounting or external-return boundary.

#### G-87

`or(iszero(status), iszero(or(isBytes32, gt(returndatasize(), 0x5f))))` · [src/libraries/StringQuery.sol:38](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/StringQuery.sol#L38) · Purpose: Protects the checked accounting or external-return boundary.

#### G-88

`returndatasize()` · [src/libraries/StringQuery.sol:42](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/StringQuery.sol#L42) · Purpose: Protects the checked accounting or external-return boundary.

#### G-89

`xor(returndatasize(), expectedReturndataSize)` · [src/libraries/StringQuery.sol:78](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/libraries/StringQuery.sol#L78) · Purpose: Protects the checked accounting or external-return boundary.

#### G-90

`(token == asset).or(token == address(this))` · [src/market/WildcatMarket.sol:38](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L38) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-91

`state.isClosed` · [src/market/WildcatMarket.sol:61](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L61) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-92

`scaledAmount == 0` · [src/market/WildcatMarket.sol:68](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L68) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-93

`amount != actualAmount` · [src/market/WildcatMarket.sol:119](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L119) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-94

`state.accruedProtocolFees == 0` · [src/market/WildcatMarket.sol:127](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L127) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-95

`withdrawableFees == 0` · [src/market/WildcatMarket.sol:130](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L130) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-96

`_isFlaggedByChainalysis(borrower)` · [src/market/WildcatMarket.sol:150](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L150) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-97

`state.isClosed` · [src/market/WildcatMarket.sol:155](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L155) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-98

`amount > borrowable` · [src/market/WildcatMarket.sol:158](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L158) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-99

`amount == 0` · [src/market/WildcatMarket.sol:169](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L169) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-100

`state.isClosed` · [src/market/WildcatMarket.sol:170](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L170) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-101

`amount == 0` · [src/market/WildcatMarket.sol:189](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L189) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-102

`state.isClosed` · [src/market/WildcatMarket.sol:195](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L195) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-103

`state.isClosed` · [src/market/WildcatMarket.sol:215](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L215) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-104

`state.scaledPendingWithdrawals != 0` · [src/market/WildcatMarket.sol:287](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L287) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-105

`iszero(
        and(
          eq(returndatasize(), 0x260),
          staticcall(gas(), caller(), 0x1c, 0x04, marketParametersPointer, 0x260)
        )
      )` · [src/market/WildcatMarketBase.sol:146](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L146) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-106

`xor(caller(), _borrower)` · [src/market/WildcatMarketBase.sol:227](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L227) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-107

`_isSanctioned(accountAddress)` · [src/market/WildcatMarketBase.sol:246](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L246) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-108

`iszero(
        and(eq(returndatasize(), 0x20), staticcall(gas(), _sentinel, 0x1c, 0x44, 0, 0x20))
      )` · [src/market/WildcatMarketBase.sol:264](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L264) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-109

`iszero(
        and(eq(returndatasize(), 0x20), staticcall(gas(), sentinelAddress, 0x1c, 0x24, 0, 0x20))
      )` · [src/market/WildcatMarketBase.sol:744](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L744) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-110

`iszero(
        and(eq(returndatasize(), 0x20), call(gas(), sentinelAddress, 0, 0x1c, 0x64, 0, 0x20))
      )` · [src/market/WildcatMarketBase.sol:767](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L767) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-111

`!_isSanctioned(accountAddress)` · [src/market/WildcatMarketConfig.sol:83](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L83) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-112

`state.isClosed` · [src/market/WildcatMarketConfig.sol:105](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L105) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-113

`state.isClosed` · [src/market/WildcatMarketConfig.sol:128](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L128) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-114

`_annualInterestBips > BIP` · [src/market/WildcatMarketConfig.sol:138](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L138) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-115

`_reserveRatioBips > BIP` · [src/market/WildcatMarketConfig.sol:142](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L142) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-116

`state.liquidityRequired() > totalAssets()` · [src/market/WildcatMarketConfig.sol:147](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L147) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-117

`state.liquidityRequired() > totalAssets()` · [src/market/WildcatMarketConfig.sol:154](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L154) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-118

`msg.sender != factory` · [src/market/WildcatMarketConfig.sol:165](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L165) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-119

`_protocolFeeBips > 1_000` · [src/market/WildcatMarketConfig.sol:166](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L166) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-120

`state.isClosed` · [src/market/WildcatMarketConfig.sol:168](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketConfig.sol#L168) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-121

`scaledAmount == 0` · [src/market/WildcatMarketToken.sol:81](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketToken.sol#L81) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-122

`expiry >= block.timestamp` · [src/market/WildcatMarketWithdrawals.sol:55](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L55) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-123

`scaledAmount == 0` · [src/market/WildcatMarketWithdrawals.sol:140](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L140) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-124

`scaledAmount == 0` · [src/market/WildcatMarketWithdrawals.sol:164](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L164) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-125

`accountAddresses.length != expiries.length` · [src/market/WildcatMarketWithdrawals.sol:215](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L215) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-126

`expiry == state.pendingWithdrawalExpiry` · [src/market/WildcatMarketWithdrawals.sol:237](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L237) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-127

`normalizedAmountWithdrawn == 0` · [src/market/WildcatMarketWithdrawals.sol:249](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L249) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-128

`state.isClosed` · [src/market/WildcatMarketWithdrawals.sol:291](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L291) · Purpose: Protects market balances, accounting or the authority needed to change them.

#### G-129

`msg.sender != sphereXAdmin()` · [src/spherex/SphereXConfig.sol:59](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXConfig.sol#L59) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-130

`msg.sender != sphereXOperator()` · [src/spherex/SphereXConfig.sol:66](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXConfig.sol#L66) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-131

`msg.sender != sphereXOperator() && msg.sender != sphereXAdmin()` · [src/spherex/SphereXConfig.sol:73](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXConfig.sol#L73) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-132

`msg.sender != pendingSphereXAdmin()` · [src/spherex/SphereXConfig.sol:121](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXConfig.sol#L121) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-133

`newSphereXEngine != address(0) &&
      !ISphereXEngine(newSphereXEngine).supportsInterface(type(ISphereXEngine).interfaceId)` · [src/spherex/SphereXConfig.sol:155](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXConfig.sol#L155) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-134

`msg.sender != _archController` · [src/spherex/SphereXProtectedRegisteredBase.sol:66](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXProtectedRegisteredBase.sol#L66) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-135

`iszero(
        and(eq(mload(0), 0x20), call(gas(), engineAddress, 0, add(pointer, 28), size, 0, 0x40))
      )` · [src/spherex/SphereXProtectedRegisteredBase.sol:172](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXProtectedRegisteredBase.sol#L172) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-136

`iszero(call(gas(), sphereXEngineAddress, 0, add(slotBefore, 28), calldataSize, 0, 0))` · [src/spherex/SphereXProtectedRegisteredBase.sol:266](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/spherex/SphereXProtectedRegisteredBase.sol#L266) · Purpose: Protects engine configuration or validation of a guarded market action.

#### G-137

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:300](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L300) · Purpose: Protects the checked accounting or external-return boundary.

#### G-138

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:362](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L362) · Purpose: Protects the checked accounting or external-return boundary.

#### G-139

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:420](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L420) · Purpose: Protects the checked accounting or external-return boundary.

#### G-140

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:485](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L485) · Purpose: Protects the checked accounting or external-return boundary.

#### G-141

`iszero(call(gas(), target, 0, add(ptr, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:534](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L534) · Purpose: Protects the checked accounting or external-return boundary.

#### G-142

`iszero(call(gas(), target, 0, add(ptr, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:584](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L584) · Purpose: Protects the checked accounting or external-return boundary.

#### G-143

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:633](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L633) · Purpose: Protects the checked accounting or external-return boundary.

#### G-144

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:687](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L687) · Purpose: Protects the checked accounting or external-return boundary.

#### G-145

`or(
          lt(returndatasize(), 0x40),
          iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0x40))
        )` · [src/types/HooksConfig.sol:762](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L762) · Purpose: Protects the checked accounting or external-return boundary.

#### G-146

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:824](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L824) · Purpose: Protects the checked accounting or external-return boundary.

#### G-147

`iszero(call(gas(), target, 0, add(cdPointer, 0x1c), size, 0, 0))` · [src/types/HooksConfig.sol:874](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/HooksConfig.sol#L874) · Purpose: Protects the checked accounting or external-return boundary.

#### G-148

`eq(outOfPlaceEncoding, lt(length, 32))` · [src/types/TransientBytesArray.sol:28](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/types/TransientBytesArray.sol#L28) · Purpose: Protects the checked accounting or external-return boundary.

#### G-149

`marketAddress == address(0)` · [src/vault/Wildcat4626Wrapper.sol:52](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L52) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-150

`owner == address(0)` · [src/vault/Wildcat4626Wrapper.sol:56](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L56) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-151

`sentinel == address(0)` · [src/vault/Wildcat4626Wrapper.sol:58](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L58) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-152

`assets == 0` · [src/vault/Wildcat4626Wrapper.sol:221](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L221) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-153

`assets > limit` · [src/vault/Wildcat4626Wrapper.sol:224](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L224) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-154

`expectedShares == 0` · [src/vault/Wildcat4626Wrapper.sol:228](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L228) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-155

`shares < expectedShares` · [src/vault/Wildcat4626Wrapper.sol:236](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L236) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-156

`shares == 0` · [src/vault/Wildcat4626Wrapper.sol:249](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L249) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-157

`assets == 0 || shares > _convertToSharesHalfUp(assets, scaleFactor)` · [src/vault/Wildcat4626Wrapper.sol:253](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L253) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-158

`numerator <= halfSf` · [src/vault/Wildcat4626Wrapper.sol:260](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L260) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-159

`expectedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:265](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L265) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-160

`mintedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:273](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L273) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-161

`assets == 0` · [src/vault/Wildcat4626Wrapper.sol:287](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L287) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-162

`shares == 0` · [src/vault/Wildcat4626Wrapper.sol:291](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L291) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-163

`burnedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:305](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L305) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-164

`shares == 0` · [src/vault/Wildcat4626Wrapper.sol:318](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L318) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-165

`assets == 0` · [src/vault/Wildcat4626Wrapper.sol:326](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L326) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-166

`burnedShares != shares` · [src/vault/Wildcat4626Wrapper.sol:336](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L336) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-167

`msg.sender != marketOwner` · [src/vault/Wildcat4626Wrapper.sol:344](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L344) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-168

`token == address(0) || to == address(0)` · [src/vault/Wildcat4626Wrapper.sol:345](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L345) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-169

`scaledBefore <= expectedScaled` · [src/vault/Wildcat4626Wrapper.sol:351](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L351) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-170

`amount == 0` · [src/vault/Wildcat4626Wrapper.sol:356](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L356) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-171

`sweptScaled != strandedScaled` · [src/vault/Wildcat4626Wrapper.sol:362](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L362) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-172

`amount == 0` · [src/vault/Wildcat4626Wrapper.sol:365](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L365) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-173

`_isSanctioned(account)` · [src/vault/Wildcat4626Wrapper.sol:433](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L433) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-174

`market == address(0)` · [src/vault/Wildcat4626WrapperFactory.sol:29](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626WrapperFactory.sol#L29) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-175

`existing != address(0)` · [src/vault/Wildcat4626WrapperFactory.sol:32](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626WrapperFactory.sol#L32) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

#### G-176

`!archController.isRegisteredMarket(market)` · [src/vault/Wildcat4626WrapperFactory.sol:34](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626WrapperFactory.sol#L34) · Purpose: Protects wrapper share accounting and the boundary to the wrapped market.

## 2. Inferred Invariants (Single-Contract)

#### I-1

`Conservation` · On-chain: **Yes**

> In the full market runtime, scaledTotalSupply equals the sum of account scaled balances plus scaledPendingWithdrawals at the end of each successful external call, after all paired storage writes complete.

Derivation: Δ-pair: [src/market/WildcatMarket.sol:78](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L78) and [src/market/WildcatMarket.sol:85](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L85) add the same deposit amount; [src/market/WildcatMarketWithdrawals.sol:104](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L104) and [src/market/WildcatMarketWithdrawals.sol:114](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L114) move it from account to pending; [src/market/WildcatMarketBase.sol:667](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L667) through [src/market/WildcatMarketBase.sol:675](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L675) burn pending and total equally. Transfer writes at [src/market/WildcatMarketToken.sol:86](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketToken.sol#L86) and [src/market/WildcatMarketToken.sol:90](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketToken.sol#L90) conserve the account sum. Batched write-site search found these durable writers; constructor fields start at zero, and pure simulation helpers do not persist their memory copies.

If violated: The aggregate market-token claim would differ from allocated account and queued balances.

#### I-2

`Conservation` · On-chain: **Yes**

> A successful batch payment increases normalizedUnclaimedWithdrawals and that batch normalizedAmountPaid by the same amount, while reducing pending and total scaled supply by the same burn.

Derivation: Δ-pair: [src/market/WildcatMarketBase.sol:668](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L668) and [src/market/WildcatMarketBase.sol:672](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L672); paired scaled reductions at [src/market/WildcatMarketBase.sol:669](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L669) and [src/market/WildcatMarketBase.sol:675](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L675) occur in _applyWithdrawalBatchPayment without an external call between the writes.

If violated: Reserved claim accounting would diverge from the batch payment record.

#### I-3

`Ratio` · On-chain: **Yes**

> For each successful withdrawal claim, the recorded total is floor(batch.normalizedAmountPaid × status.scaledAmount / batch.scaledTotalAmount), evaluated before updating the claim; the paid increment is the checked difference from its prior total.

Derivation: Δ-pair and ratio: [src/market/WildcatMarketWithdrawals.sol:243](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L243) computes newTotalWithdrawn; [src/market/WildcatMarketWithdrawals.sol:247](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L247) subtracts the old storage value before [src/market/WildcatMarketWithdrawals.sol:253](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L253) assigns it and subtracts the same increment from normalizedUnclaimedWithdrawals. This is the only durable claim-total assignment; the getter copies storage to memory.

If violated: An account could receive a payment inconsistent with its scaled share of the paid batch.

#### I-4

`StateMachine` · On-chain: **Yes**

> A full market can transition from open to closed once; no scoped action reopens it.

Derivation: edge: constructor isClosed=false at [src/market/WildcatMarketBase.sol:185](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L185) → closeMarket isClosed=true at [src/market/WildcatMarket.sol:232](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarket.sol#L232). closeMarket rejects an already closed state; all state-write sites preserve this field except that transition.

If violated: The close settlement assumptions could be reused after operations resume.

#### I-5

`StateMachine` · On-chain: **Yes**

> For each account/market pair in these concrete templates, once isKnownLenderOnMarket becomes true it remains true. Credential revocation and deposit blocks do not reset it.

Derivation: edge: false → true; [src/access/BaseAccessControls.sol:752](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L752). All write sites: [src/access/BaseAccessControls.sol:752](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/BaseAccessControls.sol#L752). Full bodies and batched rg over all scoped files locate exactly one assignment to this mapping; it stores true only.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-6

`Temporal` · On-chain: **Yes**

> Passing temporary reserve expiry alone does not remove the stored record; a subsequent APR callback must take a cancellation/expiry branch.

Derivation: temporal: tmp.expiry > 0 and block.timestamp >= tmp.expiry; [src/access/MarketConstraintHooks.sol:226](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/MarketConstraintHooks.sol#L226), [src/access/MarketConstraintHooks.sol:240](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/MarketConstraintHooks.sol#L240), [src/access/MarketConstraintHooks.sol:285](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/MarketConstraintHooks.sol#L285). All write sites: [src/access/MarketConstraintHooks.sol:240](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/MarketConstraintHooks.sol#L240), [src/access/MarketConstraintHooks.sol:285](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/MarketConstraintHooks.sol#L285). Only delete/update sites are in onSetAnnualInterestAndReserveRatioBips.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-7

`Bound` · On-chain: **No**

> A stored positive minimumDeposit implies a deposit callback is enabled.

Derivation: guard-lift: positive minimumDeposit requires the immutable deposit callback; the setter has no equivalent callback-enable predicate; [src/access/OpenTermHooks.sol:127](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L127), [src/access/OpenTermHooks.sol:175](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L175). All write sites: [src/access/OpenTermHooks.sol:168](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L168), [src/access/OpenTermHooks.sol:178](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/OpenTermHooks.sol#L178). Creation enables deposit for a positive initial minimum; later setter stores a positive minimum without checking immutable callback enablement.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

#### I-8

`Bound` · On-chain: **No**

> A stored positive minimumDeposit implies a deposit callback is enabled.

Derivation: guard-lift: positive minimumDeposit requires the immutable deposit callback; the setter has no equivalent callback-enable predicate; [src/access/FixedTermHooks.sol:156](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L156), [src/access/FixedTermHooks.sol:220](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L220). All write sites: [src/access/FixedTermHooks.sol:213](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L213), [src/access/FixedTermHooks.sol:223](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/access/FixedTermHooks.sol#L223). Creation enables deposit for a positive initial minimum; later setter stores a positive minimum without checking immutable callback enablement.

If violated: The stated admission, term or remembered-lender relation would no longer describe the stored policy.

## 3. Inferred Invariants (Cross-Contract)

#### X-1

On-chain: **Yes**

> Withdrawal execution routes a sanctioned claimant to an escrow bound to the principal/borrower, account and underlying token; successful release pays that bound account.

Caller side: [src/market/WildcatMarketWithdrawals.sol:256](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketWithdrawals.sol#L256) selects escrow instead of the claimant; [src/market/WildcatMarketBase.sol:754](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketBase.sol#L754) supplies the borrower identity and underlying asset.

Callee side: [src/WildcatSanctionsSentinel.sol:121](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatSanctionsSentinel.sol#L121) creates the deterministic escrow and constructor input; [src/WildcatSanctionsEscrow.sol:17](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/WildcatSanctionsEscrow.sol#L17) fixes the account and token, and releaseEscrow reads the release predicate before paying that account.

If violated: Sanctions custody could be associated with a different account or token.

#### X-2

On-chain: **Yes**

> Successful wrapper deposit/mint accounting is checked against the actual change in the wrapped market scaled balance, under the generation-specific rounding convention.

Caller side: [src/vault/Wildcat4626Wrapper.sol:216](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/vault/Wildcat4626Wrapper.sol#L216) measures market scaled balances across transferFrom and compares minted shares; mint has its own measured path in the same source file.

Callee side: [src/market/WildcatMarketToken.sol:72](https://github.com/wildcat-finance/v2-protocol/blob/f5a26146987926f4811b72a795d662813dedfe85/src/market/WildcatMarketToken.sol#L72) updates market account scaled balances using half-up conversion. The external asset must actually be the named in-scope market for this paired property.

If violated: Wrapper share issuance would diverge from the scaled market claims received.

## 4. Economic Invariants

#### E-1

On-chain: **Yes**

> Batch payment converts interest-bearing scaled debt to normalized claim reserves; claiming reduces those reserves by the increment recorded as withdrawn.

Follows from: I-1 + I-2 + I-3; executeWithdrawal subtracts the same increment from normalizedUnclaimedWithdrawals before transferring it. This is claim bookkeeping, not a guarantee of borrower solvency.

If violated: Queued scaled debt and paid normalized claims could be counted inconsistently.
