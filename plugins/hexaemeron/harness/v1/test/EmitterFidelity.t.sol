// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.22;

import {Vm, VM_ADDRESS} from "../src/Vm.sol";
import {LogComparison} from "../src/LogComparison.sol";
import {AssemblyEmitWrapper} from "../src/AssemblyEmitWrapper.sol";
import {MirrorEmitReference} from "../src/MirrorEmitReference.sol";
import {AuthRole} from "../src/vendor/interfaces/WildcatStructsAndEnums.sol";
import {WrongTopic0Specimen} from "../src/specimens/WrongTopic0Specimen.sol";
import {WrongDataSpecimen} from "../src/specimens/WrongDataSpecimen.sol";
import {WrongTopicCountSpecimen} from "../src/specimens/WrongTopicCountSpecimen.sol";
import {WrongIndexedTopicSpecimen} from "../src/specimens/WrongIndexedTopicSpecimen.sol";
import {WrongDataLengthSpecimen} from "../src/specimens/WrongDataLengthSpecimen.sol";

/// @dev The V1 emitter-fidelity differential suite (#1964): 26 fuzz cases,
///      one per assembly emitter in `wildcat-finance/wildcat-protocol` at
///      `da74452aa7d1a0f024d99efd22cc6d950a8116b7`. Each case records the
///      assembly log first and then one reference log per same-named
///      declaration, and holds the assembly log to every reference, so each
///      row of the #1962 table is compared in the case for its emitter. Every
///      case fuzzes over the emitter's own parameter types. Fixed companion
///      cases drive every emitter at all-zero, all-one, high-bit and
///      all-maximum arguments and at every `AuthRole` member, so those values
///      are reached on every run. Expected logs come only from the compiler's
///      `emit` of the fetched declarations; no topic, arity or data offset is
///      written here.
contract EmitterFidelityTest {
  Vm internal constant vm = Vm(VM_ADDRESS);

  AssemblyEmitWrapper internal wrapper;
  MirrorEmitReference internal mirror;
  WrongTopic0Specimen internal wrongTopic0;
  WrongDataSpecimen internal wrongData;
  WrongTopicCountSpecimen internal wrongTopicCount;
  WrongIndexedTopicSpecimen internal wrongIndexedTopic;
  WrongDataLengthSpecimen internal wrongDataLength;

  /// @dev The recording window opens in every case, after this deployment,
  ///      so no construction-time log can enter a comparison.
  function setUp() public {
    wrapper = new AssemblyEmitWrapper();
    mirror = new MirrorEmitReference();
    wrongTopic0 = new WrongTopic0Specimen();
    wrongData = new WrongDataSpecimen();
    wrongTopicCount = new WrongTopicCountSpecimen();
    wrongIndexedTopic = new WrongIndexedTopicSpecimen();
    wrongDataLength = new WrongDataLengthSpecimen();
  }

  // ---- pairing -----------------------------------------------------------

  /// @dev Fetch the window: the assembly log first, then exactly one
  ///      reference log per declaration, and hold the assembly log to each.
  function _compareAgainstEachDeclaration(uint256 declarations) internal {
    Vm.Log[] memory logs = vm.getRecordedLogs();
    require(logs.length == 1 + declarations, "recorded log count");
    require(logs[0].emitter == address(wrapper), "log 0 is not the assembly");
    for (uint256 i = 1; i < logs.length; i++) {
      require(logs[i].emitter == address(mirror), "a later log is not the reference");
      LogComparison.compare(logs[0], logs[i]);
    }
  }

  /// @dev The comparison, exposed externally so a rejection can be caught.
  function compareExternally(Vm.Log memory actual, Vm.Log memory expected) external pure {
    LogComparison.compare(actual, expected);
  }

  /// @dev Free memory pointer after the wrapper's last call equals the one
  ///      before it, and the zero slot at `0x60` still holds zero.
  function _requireFreePointerUnchanged(string memory which) internal view {
    require(wrapper.freePointerBefore() == wrapper.freePointerAfter(), which);
    require(wrapper.zeroSlotAfter() == 0, string(abi.encodePacked(which, " (zero slot)")));
  }

  /// @dev Fold a drawn byte onto the members of `AuthRole`.
  function _role(uint8 raw) internal pure returns (AuthRole) {
    return AuthRole(raw % (uint8(type(AuthRole).max) + 1));
  }

  // ---- per-emitter helpers, shared by the fuzz and companion cases -------

  function _pair_Transfer(address from, address to, uint256 value) internal {
    vm.recordLogs();
    wrapper.assembly_Transfer(from, to, value);
    mirror.mirror_IERC20_Transfer(from, to, value);
    mirror.mirror_IMarketEventsAndErrors_Transfer(from, to, value);
    _compareAgainstEachDeclaration(2);
  }

  function _pair_Approval(address owner, address spender, uint256 value) internal {
    vm.recordLogs();
    wrapper.assembly_Approval(owner, spender, value);
    mirror.mirror_IERC20_Approval(owner, spender, value);
    mirror.mirror_IMarketEventsAndErrors_Approval(owner, spender, value);
    _compareAgainstEachDeclaration(2);
  }

  function _pair_MaxTotalSupplyUpdated(uint256 assets) internal {
    vm.recordLogs();
    wrapper.assembly_MaxTotalSupplyUpdated(assets);
    mirror.mirror_IMarketEventsAndErrors_MaxTotalSupplyUpdated(assets);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_AnnualInterestBipsUpdated(uint256 annualInterestBipsUpdated) internal {
    vm.recordLogs();
    wrapper.assembly_AnnualInterestBipsUpdated(annualInterestBipsUpdated);
    mirror.mirror_IMarketEventsAndErrors_AnnualInterestBipsUpdated(annualInterestBipsUpdated);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_ReserveRatioBipsUpdated(uint256 reserveRatioBipsUpdated) internal {
    vm.recordLogs();
    wrapper.assembly_ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
    mirror.mirror_IMarketEventsAndErrors_ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_SanctionedAccountAssetsSentToEscrow(
    address account,
    address escrow,
    uint256 amount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
    mirror.mirror_IMarketEventsAndErrors_SanctionedAccountAssetsSentToEscrow(
      account,
      escrow,
      amount
    );
    _compareAgainstEachDeclaration(1);
  }

  function _pair_Deposit(address account, uint256 assetAmount, uint256 scaledAmount) internal {
    vm.recordLogs();
    wrapper.assembly_Deposit(account, assetAmount, scaledAmount);
    mirror.mirror_IMarketEventsAndErrors_Deposit(account, assetAmount, scaledAmount);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_Borrow(uint256 assetAmount) internal {
    vm.recordLogs();
    wrapper.assembly_Borrow(assetAmount);
    mirror.mirror_IMarketEventsAndErrors_Borrow(assetAmount);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_DebtRepaid(address from, uint256 assetAmount) internal {
    vm.recordLogs();
    wrapper.assembly_DebtRepaid(from, assetAmount);
    mirror.mirror_IMarketEventsAndErrors_DebtRepaid(from, assetAmount);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_MarketClosed(uint256 timestamp) internal {
    vm.recordLogs();
    wrapper.assembly_MarketClosed(timestamp);
    mirror.mirror_IMarketEventsAndErrors_MarketClosed(timestamp);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_FeesCollected(uint256 assets) internal {
    vm.recordLogs();
    wrapper.assembly_FeesCollected(assets);
    mirror.mirror_IMarketEventsAndErrors_FeesCollected(assets);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_StateUpdated(uint256 scaleFactor, bool isDelinquent) internal {
    vm.recordLogs();
    wrapper.assembly_StateUpdated(scaleFactor, isDelinquent);
    mirror.mirror_IMarketEventsAndErrors_StateUpdated(scaleFactor, isDelinquent);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_InterestAndFeesAccrued(
    uint256 fromTimestamp,
    uint256 toTimestamp,
    uint256 scaleFactor,
    uint256 baseInterestRay,
    uint256 delinquencyFeeRay,
    uint256 protocolFees
  ) internal {
    vm.recordLogs();
    wrapper.assembly_InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
    mirror.mirror_IMarketEventsAndErrors_InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
    _compareAgainstEachDeclaration(1);
  }

  function _pair_AuthorizationStatusUpdated(address account, AuthRole role) internal {
    vm.recordLogs();
    wrapper.assembly_AuthorizationStatusUpdated(account, role);
    mirror.mirror_IMarketEventsAndErrors_AuthorizationStatusUpdated(account, role);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_WithdrawalBatchExpired(
    uint256 expiry,
    uint256 scaledTotalAmount,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalBatchExpired(
      expiry,
      scaledTotalAmount,
      scaledAmountBurned,
      normalizedAmountPaid
    );
    mirror.mirror_IMarketEventsAndErrors_WithdrawalBatchExpired(
      expiry,
      scaledTotalAmount,
      scaledAmountBurned,
      normalizedAmountPaid
    );
    _compareAgainstEachDeclaration(1);
  }

  function _pair_WithdrawalBatchCreated(uint256 expiry) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalBatchCreated(expiry);
    mirror.mirror_IMarketEventsAndErrors_WithdrawalBatchCreated(expiry);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_WithdrawalBatchClosed(uint256 expiry) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalBatchClosed(expiry);
    mirror.mirror_IMarketEventsAndErrors_WithdrawalBatchClosed(expiry);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_WithdrawalBatchPayment(
    uint256 expiry,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
    mirror.mirror_IMarketEventsAndErrors_WithdrawalBatchPayment(
      expiry,
      scaledAmountBurned,
      normalizedAmountPaid
    );
    _compareAgainstEachDeclaration(1);
  }

  function _pair_WithdrawalQueued(
    uint256 expiry,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
    mirror.mirror_IMarketEventsAndErrors_WithdrawalQueued(
      expiry,
      account,
      scaledAmount,
      normalizedAmount
    );
    _compareAgainstEachDeclaration(1);
  }

  function _pair_WithdrawalExecuted(
    uint256 expiry,
    address account,
    uint256 normalizedAmount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalExecuted(expiry, account, normalizedAmount);
    mirror.mirror_IMarketEventsAndErrors_WithdrawalExecuted(expiry, account, normalizedAmount);
    _compareAgainstEachDeclaration(1);
  }

  function _pair_SanctionedAccountWithdrawalSentToEscrow(
    address account,
    address escrow,
    uint32 expiry,
    uint256 amount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
    mirror.mirror_IMarketEventsAndErrors_SanctionedAccountWithdrawalSentToEscrow(
      account,
      escrow,
      expiry,
      amount
    );
    _compareAgainstEachDeclaration(1);
  }

  function _pair_ChangedSpherexOperator(address oldSphereXAdmin, address newSphereXAdmin) internal {
    vm.recordLogs();
    wrapper.assembly_ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
    mirror.mirror_ISphereXProtectedRegisteredBase_ChangedSpherexOperator(
      oldSphereXAdmin,
      newSphereXAdmin
    );
    mirror.mirror_IWildcatArchController_ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
    mirror.mirror_SphereXConfig_ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
    mirror.mirror_SphereXProtectedRegisteredBase_ChangedSpherexOperator(
      oldSphereXAdmin,
      newSphereXAdmin
    );
    _compareAgainstEachDeclaration(4);
  }

  function _pair_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) internal {
    vm.recordLogs();
    wrapper.assembly_ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
    mirror.mirror_ISphereXProtectedRegisteredBase_ChangedSpherexEngineAddress(
      oldEngineAddress,
      newEngineAddress
    );
    mirror.mirror_IWildcatArchController_ChangedSpherexEngineAddress(
      oldEngineAddress,
      newEngineAddress
    );
    mirror.mirror_SphereXConfig_ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
    mirror.mirror_SphereXProtectedRegisteredBase_ChangedSpherexEngineAddress(
      oldEngineAddress,
      newEngineAddress
    );
    _compareAgainstEachDeclaration(4);
  }

  function _pair_SpherexAdminTransferStarted(address currentAdmin, address pendingAdmin) internal {
    vm.recordLogs();
    wrapper.assembly_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    mirror.mirror_IWildcatArchController_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    mirror.mirror_SphereXConfig_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    _compareAgainstEachDeclaration(2);
  }

  function _pair_SpherexAdminTransferCompleted(address oldAdmin, address newAdmin) internal {
    vm.recordLogs();
    wrapper.assembly_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    mirror.mirror_IWildcatArchController_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    mirror.mirror_SphereXConfig_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    _compareAgainstEachDeclaration(2);
  }

  function _pair_NewAllowedSenderOnchain(address sender) internal {
    vm.recordLogs();
    wrapper.assembly_NewAllowedSenderOnchain(sender);
    mirror.mirror_IWildcatArchController_NewAllowedSenderOnchain(sender);
    mirror.mirror_SphereXConfig_NewAllowedSenderOnchain(sender);
    _compareAgainstEachDeclaration(2);
  }

  // ---- the 26 fuzz cases ---------------------------------------------------
  // The label after the event name is the declaration's indexed count.

  function test_emit_Transfer_indexed2(address from, address to, uint256 value) external {
    _pair_Transfer(from, to, value);
  }

  function test_emit_Approval_indexed2(address owner, address spender, uint256 value) external {
    _pair_Approval(owner, spender, value);
  }

  function test_emit_MaxTotalSupplyUpdated_indexed0(uint256 assets) external {
    _pair_MaxTotalSupplyUpdated(assets);
  }

  function test_emit_AnnualInterestBipsUpdated_indexed0(
    uint256 annualInterestBipsUpdated
  ) external {
    _pair_AnnualInterestBipsUpdated(annualInterestBipsUpdated);
  }

  function test_emit_ReserveRatioBipsUpdated_indexed0(uint256 reserveRatioBipsUpdated) external {
    _pair_ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
  }

  function test_emit_SanctionedAccountAssetsSentToEscrow_indexed1(
    address account,
    address escrow,
    uint256 amount
  ) external {
    _pair_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
  }

  function test_emit_Deposit_indexed1(
    address account,
    uint256 assetAmount,
    uint256 scaledAmount
  ) external {
    _pair_Deposit(account, assetAmount, scaledAmount);
  }

  function test_emit_Borrow_indexed0(uint256 assetAmount) external {
    _pair_Borrow(assetAmount);
  }

  function test_emit_DebtRepaid_indexed1(address from, uint256 assetAmount) external {
    _pair_DebtRepaid(from, assetAmount);
  }

  function test_emit_MarketClosed_indexed0(uint256 timestamp) external {
    _pair_MarketClosed(timestamp);
  }

  function test_emit_FeesCollected_indexed0(uint256 assets) external {
    _pair_FeesCollected(assets);
  }

  function test_emit_StateUpdated_indexed0(uint256 scaleFactor, bool isDelinquent) external {
    _pair_StateUpdated(scaleFactor, isDelinquent);
  }

  function test_emit_InterestAndFeesAccrued_indexed0(
    uint256 fromTimestamp,
    uint256 toTimestamp,
    uint256 scaleFactor,
    uint256 baseInterestRay,
    uint256 delinquencyFeeRay,
    uint256 protocolFees
  ) external {
    _pair_InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
  }

  /// @dev `role` is fuzzed as a `uint8` folded onto the enum's members, so
  ///      every drawn value is a valid `AuthRole`.
  function test_emit_AuthorizationStatusUpdated_indexed1(address account, uint8 rawRole) external {
    _pair_AuthorizationStatusUpdated(account, _role(rawRole));
  }

  function test_emit_WithdrawalBatchExpired_indexed1(
    uint256 expiry,
    uint256 scaledTotalAmount,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    _pair_WithdrawalBatchExpired(
      expiry,
      scaledTotalAmount,
      scaledAmountBurned,
      normalizedAmountPaid
    );
  }

  function test_emit_WithdrawalBatchCreated_indexed1(uint256 expiry) external {
    _pair_WithdrawalBatchCreated(expiry);
  }

  function test_emit_WithdrawalBatchClosed_indexed1(uint256 expiry) external {
    _pair_WithdrawalBatchClosed(expiry);
  }

  function test_emit_WithdrawalBatchPayment_indexed1(
    uint256 expiry,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    _pair_WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
  }

  function test_emit_WithdrawalQueued_indexed2(
    uint256 expiry,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    _pair_WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
  }

  function test_emit_WithdrawalExecuted_indexed2(
    uint256 expiry,
    address account,
    uint256 normalizedAmount
  ) external {
    _pair_WithdrawalExecuted(expiry, account, normalizedAmount);
  }

  function test_emit_SanctionedAccountWithdrawalSentToEscrow_indexed1(
    address account,
    address escrow,
    uint32 expiry,
    uint256 amount
  ) external {
    _pair_SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
  }

  function test_emit_ChangedSpherexOperator_indexed0(
    address oldSphereXAdmin,
    address newSphereXAdmin
  ) external {
    _pair_ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
  }

  function test_emit_ChangedSpherexEngineAddress_indexed0(
    address oldEngineAddress,
    address newEngineAddress
  ) external {
    _pair_ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
  }

  function test_emit_SpherexAdminTransferStarted_indexed0(
    address currentAdmin,
    address pendingAdmin
  ) external {
    _pair_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
  }

  function test_emit_SpherexAdminTransferCompleted_indexed0(
    address oldAdmin,
    address newAdmin
  ) external {
    _pair_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
  }

  function test_emit_NewAllowedSenderOnchain_indexed0(address sender) external {
    _pair_NewAllowedSenderOnchain(sender);
  }

  // ---- fixed companions: ABI edge values on every run ----------------------

  function _pairEveryEmitter(
    address a,
    address b,
    uint256 x,
    uint256 y,
    uint32 e,
    bool f,
    AuthRole r
  ) internal {
    _pair_Transfer(a, b, x);
    _pair_Approval(a, b, x);
    _pair_MaxTotalSupplyUpdated(x);
    _pair_AnnualInterestBipsUpdated(x);
    _pair_ReserveRatioBipsUpdated(x);
    _pair_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _pair_Deposit(a, x, y);
    _pair_Borrow(x);
    _pair_DebtRepaid(a, x);
    _pair_MarketClosed(x);
    _pair_FeesCollected(x);
    _pair_StateUpdated(x, f);
    _pair_InterestAndFeesAccrued(x, y, x, y, x, y);
    _pair_AuthorizationStatusUpdated(a, r);
    _pair_WithdrawalBatchExpired(x, y, x, y);
    _pair_WithdrawalBatchCreated(x);
    _pair_WithdrawalBatchClosed(x);
    _pair_WithdrawalBatchPayment(x, y, x);
    _pair_WithdrawalQueued(x, a, y, x);
    _pair_WithdrawalExecuted(x, a, y);
    _pair_SanctionedAccountWithdrawalSentToEscrow(a, b, e, x);
    _pair_ChangedSpherexOperator(a, b);
    _pair_ChangedSpherexEngineAddress(a, b);
    _pair_SpherexAdminTransferStarted(a, b);
    _pair_SpherexAdminTransferCompleted(a, b);
    _pair_NewAllowedSenderOnchain(a);
  }

  /// @dev Every emitter at all-zero arguments (`address(0)`, `0`, `false`, `AuthRole.Null`).
  function test_edge_every_emitter_at_zero() external {
    _pairEveryEmitter(address(0), address(0), 0, 0, 0, false, AuthRole.Null);
  }

  /// @dev Every emitter at one in every word.
  function test_edge_every_emitter_at_one() external {
    _pairEveryEmitter(address(1), address(1), 1, 1, 1, true, AuthRole.Blocked);
  }

  /// @dev Every emitter with only the top bit of each type set: bit 159 of
  ///      an address, bit 255 of a `uint256` and bit 31 of a `uint32`.
  function test_edge_every_emitter_at_high_bit() external {
    _pairEveryEmitter(
      address(uint160(1) << 159),
      address(uint160(1) << 159),
      uint256(1) << 255,
      uint256(1) << 255,
      uint32(1) << 31,
      true,
      AuthRole.WithdrawOnly
    );
  }

  /// @dev Every emitter at the maximum of each type.
  function test_edge_every_emitter_at_max() external {
    _pairEveryEmitter(
      address(type(uint160).max),
      address(type(uint160).max),
      type(uint256).max,
      type(uint256).max,
      type(uint32).max,
      true,
      type(AuthRole).max
    );
  }

  /// @dev `AuthorizationStatusUpdated` at every member of `AuthRole`.
  function test_edge_every_auth_role() external {
    for (uint8 i = 0; i <= uint8(type(AuthRole).max); i++) {
      _pair_AuthorizationStatusUpdated(address(0xa11ce), AuthRole(i));
    }
  }

  // ---- the narrowing call-site pattern -------------------------------------

  /// @dev `WildcatMarketWithdrawals.sol:106` narrows `block.timestamp +
  ///      withdrawalBatchDuration` to `uint32` and passes it to two emitters
  ///      whose parameter is `uint256`. Under this profile the value reaching
  ///      the log is the truncated `uint32`, whatever the wide value was: the
  ///      log agrees with the `uint32` the market stores. The reference emits
  ///      the truncated value widened back to `uint256`.
  function test_narrowing_call_site_reaches_the_log_truncated(
    uint256 wide,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    uint256 truncated = uint256(uint32(wide));
    vm.recordLogs();
    wrapper.narrowed_WithdrawalBatchCreated(wide);
    mirror.mirror_IMarketEventsAndErrors_WithdrawalBatchCreated(truncated);
    _compareAgainstEachDeclaration(1);
    vm.recordLogs();
    wrapper.narrowed_WithdrawalQueued(wide, account, scaledAmount, normalizedAmount);
    mirror.mirror_IMarketEventsAndErrors_WithdrawalQueued(
      truncated,
      account,
      scaledAmount,
      normalizedAmount
    );
    _compareAgainstEachDeclaration(1);
  }

  // ---- rejection specimens: the comparison is proved able to fail ----------

  function _rejects(address specimen, string memory expectedField) internal {
    vm.recordLogs();
    (bool ok, ) = specimen.call(
      abi.encodeWithSignature("specimen_Transfer(address,address,uint256)", address(1), address(2), 3)
    );
    require(ok, "specimen call");
    mirror.mirror_IMarketEventsAndErrors_Transfer(address(1), address(2), 3);
    Vm.Log[] memory logs = vm.getRecordedLogs();
    require(logs.length == 2, "recorded log count");
    require(logs[0].emitter == specimen, "log 0 is not the specimen");
    require(logs[1].emitter == address(mirror), "log 1 is not the reference");
    try this.compareExternally(logs[0], logs[1]) {
      revert("comparison accepted a wrong answer");
    } catch Error(string memory reason) {
      require(
        keccak256(bytes(reason)) == keccak256(bytes(expectedField)),
        string(abi.encodePacked("rejected on the wrong field: ", reason))
      );
    }
  }

  function test_rejects_wrong_topic0_specimen() external {
    _rejects(address(wrongTopic0), "topic0");
  }

  function test_rejects_wrong_data_bytes_specimen() external {
    _rejects(address(wrongData), "data bytes");
  }

  function test_rejects_wrong_topic_count_specimen() external {
    _rejects(address(wrongTopicCount), "topic count");
  }

  function test_rejects_wrong_indexed_topic_specimen() external {
    _rejects(address(wrongIndexedTopic), "topic1");
  }

  function test_rejects_wrong_data_length_specimen() external {
    _rejects(address(wrongDataLength), "data length");
  }

  // ---- memory: the free pointer and the scratch space ----------------------

  /// @dev The free memory pointer at `0x40`, read in the calling frame
  ///      immediately before and after each emitter, is unchanged for every
  ///      one of the 26, with and without a dirtied scratch space, and the
  ///      zero slot at `0x60` still holds zero after each emitter.
  function test_memory_free_pointer_unchanged_across_every_emitter(
    address a,
    address b,
    uint256 x,
    uint256 y,
    uint32 e,
    bool f,
    uint8 rawRole
  ) external {
    _freePointerSweep(a, b, x, y, e, f, _role(rawRole));
    wrapper.setDirtyScratch(true);
    _freePointerSweep(a, b, x, y, e, f, _role(rawRole));
  }

  function _freePointerSweep(
    address a,
    address b,
    uint256 x,
    uint256 y,
    uint32 e,
    bool f,
    AuthRole r
  ) internal {
    wrapper.assembly_Transfer(a, b, x);
    _requireFreePointerUnchanged("Transfer moved 0x40");
    wrapper.assembly_Approval(a, b, x);
    _requireFreePointerUnchanged("Approval moved 0x40");
    wrapper.assembly_MaxTotalSupplyUpdated(x);
    _requireFreePointerUnchanged("MaxTotalSupplyUpdated moved 0x40");
    wrapper.assembly_AnnualInterestBipsUpdated(x);
    _requireFreePointerUnchanged("AnnualInterestBipsUpdated moved 0x40");
    wrapper.assembly_ReserveRatioBipsUpdated(x);
    _requireFreePointerUnchanged("ReserveRatioBipsUpdated moved 0x40");
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _requireFreePointerUnchanged("SanctionedAccountAssetsSentToEscrow moved 0x40");
    wrapper.assembly_Deposit(a, x, y);
    _requireFreePointerUnchanged("Deposit moved 0x40");
    wrapper.assembly_Borrow(x);
    _requireFreePointerUnchanged("Borrow moved 0x40");
    wrapper.assembly_DebtRepaid(a, x);
    _requireFreePointerUnchanged("DebtRepaid moved 0x40");
    wrapper.assembly_MarketClosed(x);
    _requireFreePointerUnchanged("MarketClosed moved 0x40");
    wrapper.assembly_FeesCollected(x);
    _requireFreePointerUnchanged("FeesCollected moved 0x40");
    wrapper.assembly_StateUpdated(x, f);
    _requireFreePointerUnchanged("StateUpdated moved 0x40");
    wrapper.assembly_InterestAndFeesAccrued(x, y, x, y, x, y);
    _requireFreePointerUnchanged("InterestAndFeesAccrued moved 0x40");
    wrapper.assembly_AuthorizationStatusUpdated(a, r);
    _requireFreePointerUnchanged("AuthorizationStatusUpdated moved 0x40");
    wrapper.assembly_WithdrawalBatchExpired(x, y, x, y);
    _requireFreePointerUnchanged("WithdrawalBatchExpired moved 0x40");
    wrapper.assembly_WithdrawalBatchCreated(x);
    _requireFreePointerUnchanged("WithdrawalBatchCreated moved 0x40");
    wrapper.assembly_WithdrawalBatchClosed(x);
    _requireFreePointerUnchanged("WithdrawalBatchClosed moved 0x40");
    wrapper.assembly_WithdrawalBatchPayment(x, y, x);
    _requireFreePointerUnchanged("WithdrawalBatchPayment moved 0x40");
    wrapper.assembly_WithdrawalQueued(x, a, y, x);
    _requireFreePointerUnchanged("WithdrawalQueued moved 0x40");
    wrapper.assembly_WithdrawalExecuted(x, a, y);
    _requireFreePointerUnchanged("WithdrawalExecuted moved 0x40");
    wrapper.assembly_SanctionedAccountWithdrawalSentToEscrow(a, b, e, x);
    _requireFreePointerUnchanged("SanctionedAccountWithdrawalSentToEscrow moved 0x40");
    wrapper.assembly_ChangedSpherexOperator(a, b);
    _requireFreePointerUnchanged("ChangedSpherexOperator moved 0x40");
    wrapper.assembly_ChangedSpherexEngineAddress(a, b);
    _requireFreePointerUnchanged("ChangedSpherexEngineAddress moved 0x40");
    wrapper.assembly_SpherexAdminTransferStarted(a, b);
    _requireFreePointerUnchanged("SpherexAdminTransferStarted moved 0x40");
    wrapper.assembly_SpherexAdminTransferCompleted(a, b);
    _requireFreePointerUnchanged("SpherexAdminTransferCompleted moved 0x40");
    wrapper.assembly_NewAllowedSenderOnchain(a);
    _requireFreePointerUnchanged("NewAllowedSenderOnchain moved 0x40");
  }

  /// @dev A dirtied scratch space before each emitter call (a non-zero
  ///      pattern over `0x00`..`0x3f` and the pointer word at `0x40` moved,
  ///      as the wrapper describes) does not change the recorded log. Every
  ///      emitter is driven twice in one window, clean then dirty, and the
  ///      dirty log at index 1 is held to the clean log at index 0 with the
  ///      same field-by-field helper, so a scratch byte that leaked into the
  ///      data region or a topic fails on the field it reached.
  function test_memory_dirtied_scratch_does_not_change_the_recorded_log(
    address a,
    address b,
    uint256 x,
    uint256 y,
    uint32 e,
    bool f,
    uint8 rawRole
  ) external {
    AuthRole r = _role(rawRole);
    _scratch_Transfer(a, b, x);
    _scratch_Approval(a, b, x);
    _scratch_MaxTotalSupplyUpdated(x);
    _scratch_AnnualInterestBipsUpdated(x);
    _scratch_ReserveRatioBipsUpdated(x);
    _scratch_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _scratch_Deposit(a, x, y);
    _scratch_Borrow(x);
    _scratch_DebtRepaid(a, x);
    _scratch_MarketClosed(x);
    _scratch_FeesCollected(x);
    _scratch_StateUpdated(x, f);
    _scratch_InterestAndFeesAccrued(x, y, x, y, x, y);
    _scratch_AuthorizationStatusUpdated(a, r);
    _scratch_WithdrawalBatchExpired(x, y, x, y);
    _scratch_WithdrawalBatchCreated(x);
    _scratch_WithdrawalBatchClosed(x);
    _scratch_WithdrawalBatchPayment(x, y, x);
    _scratch_WithdrawalQueued(x, a, y, x);
    _scratch_WithdrawalExecuted(x, a, y);
    _scratch_SanctionedAccountWithdrawalSentToEscrow(a, b, e, x);
    _scratch_ChangedSpherexOperator(a, b);
    _scratch_ChangedSpherexEngineAddress(a, b);
    _scratch_SpherexAdminTransferStarted(a, b);
    _scratch_SpherexAdminTransferCompleted(a, b);
    _scratch_NewAllowedSenderOnchain(a);
  }

  /// @dev Open a window with a clean scratch space; the caller emits once.
  function _cleanWindow() internal {
    wrapper.setDirtyScratch(false);
    vm.recordLogs();
  }

  /// @dev Switch to a dirtied scratch space; the caller emits once more.
  function _dirty() internal {
    wrapper.setDirtyScratch(true);
  }

  function _compareCleanAgainstDirty(string memory name) internal {
    Vm.Log[] memory logs = vm.getRecordedLogs();
    require(logs.length == 2, string(abi.encodePacked(name, ": recorded log count")));
    require(logs[0].emitter == address(wrapper), "log 0 is not the wrapper");
    require(logs[1].emitter == address(wrapper), "log 1 is not the wrapper");
    LogComparison.compare(logs[1], logs[0]);
    wrapper.setDirtyScratch(false);
  }

  function _scratch_Transfer(address from, address to, uint256 value) internal {
    _cleanWindow();
    wrapper.assembly_Transfer(from, to, value);
    _dirty();
    wrapper.assembly_Transfer(from, to, value);
    _compareCleanAgainstDirty("Transfer");
  }

  function _scratch_Approval(address owner, address spender, uint256 value) internal {
    _cleanWindow();
    wrapper.assembly_Approval(owner, spender, value);
    _dirty();
    wrapper.assembly_Approval(owner, spender, value);
    _compareCleanAgainstDirty("Approval");
  }

  function _scratch_MaxTotalSupplyUpdated(uint256 assets) internal {
    _cleanWindow();
    wrapper.assembly_MaxTotalSupplyUpdated(assets);
    _dirty();
    wrapper.assembly_MaxTotalSupplyUpdated(assets);
    _compareCleanAgainstDirty("MaxTotalSupplyUpdated");
  }

  function _scratch_AnnualInterestBipsUpdated(uint256 annualInterestBipsUpdated) internal {
    _cleanWindow();
    wrapper.assembly_AnnualInterestBipsUpdated(annualInterestBipsUpdated);
    _dirty();
    wrapper.assembly_AnnualInterestBipsUpdated(annualInterestBipsUpdated);
    _compareCleanAgainstDirty("AnnualInterestBipsUpdated");
  }

  function _scratch_ReserveRatioBipsUpdated(uint256 reserveRatioBipsUpdated) internal {
    _cleanWindow();
    wrapper.assembly_ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
    _dirty();
    wrapper.assembly_ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
    _compareCleanAgainstDirty("ReserveRatioBipsUpdated");
  }

  function _scratch_SanctionedAccountAssetsSentToEscrow(
    address account,
    address escrow,
    uint256 amount
  ) internal {
    _cleanWindow();
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
    _dirty();
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
    _compareCleanAgainstDirty("SanctionedAccountAssetsSentToEscrow");
  }

  function _scratch_Deposit(address account, uint256 assetAmount, uint256 scaledAmount) internal {
    _cleanWindow();
    wrapper.assembly_Deposit(account, assetAmount, scaledAmount);
    _dirty();
    wrapper.assembly_Deposit(account, assetAmount, scaledAmount);
    _compareCleanAgainstDirty("Deposit");
  }

  function _scratch_Borrow(uint256 assetAmount) internal {
    _cleanWindow();
    wrapper.assembly_Borrow(assetAmount);
    _dirty();
    wrapper.assembly_Borrow(assetAmount);
    _compareCleanAgainstDirty("Borrow");
  }

  function _scratch_DebtRepaid(address from, uint256 assetAmount) internal {
    _cleanWindow();
    wrapper.assembly_DebtRepaid(from, assetAmount);
    _dirty();
    wrapper.assembly_DebtRepaid(from, assetAmount);
    _compareCleanAgainstDirty("DebtRepaid");
  }

  function _scratch_MarketClosed(uint256 timestamp) internal {
    _cleanWindow();
    wrapper.assembly_MarketClosed(timestamp);
    _dirty();
    wrapper.assembly_MarketClosed(timestamp);
    _compareCleanAgainstDirty("MarketClosed");
  }

  function _scratch_FeesCollected(uint256 assets) internal {
    _cleanWindow();
    wrapper.assembly_FeesCollected(assets);
    _dirty();
    wrapper.assembly_FeesCollected(assets);
    _compareCleanAgainstDirty("FeesCollected");
  }

  function _scratch_StateUpdated(uint256 scaleFactor, bool isDelinquent) internal {
    _cleanWindow();
    wrapper.assembly_StateUpdated(scaleFactor, isDelinquent);
    _dirty();
    wrapper.assembly_StateUpdated(scaleFactor, isDelinquent);
    _compareCleanAgainstDirty("StateUpdated");
  }

  function _scratch_InterestAndFeesAccrued(
    uint256 fromTimestamp,
    uint256 toTimestamp,
    uint256 scaleFactor,
    uint256 baseInterestRay,
    uint256 delinquencyFeeRay,
    uint256 protocolFees
  ) internal {
    _cleanWindow();
    wrapper.assembly_InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
    _dirty();
    wrapper.assembly_InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
    _compareCleanAgainstDirty("InterestAndFeesAccrued");
  }

  function _scratch_AuthorizationStatusUpdated(address account, AuthRole role) internal {
    _cleanWindow();
    wrapper.assembly_AuthorizationStatusUpdated(account, role);
    _dirty();
    wrapper.assembly_AuthorizationStatusUpdated(account, role);
    _compareCleanAgainstDirty("AuthorizationStatusUpdated");
  }

  function _scratch_WithdrawalBatchExpired(
    uint256 expiry,
    uint256 scaledTotalAmount,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchExpired(
      expiry,
      scaledTotalAmount,
      scaledAmountBurned,
      normalizedAmountPaid
    );
    _dirty();
    wrapper.assembly_WithdrawalBatchExpired(
      expiry,
      scaledTotalAmount,
      scaledAmountBurned,
      normalizedAmountPaid
    );
    _compareCleanAgainstDirty("WithdrawalBatchExpired");
  }

  function _scratch_WithdrawalBatchCreated(uint256 expiry) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchCreated(expiry);
    _dirty();
    wrapper.assembly_WithdrawalBatchCreated(expiry);
    _compareCleanAgainstDirty("WithdrawalBatchCreated");
  }

  function _scratch_WithdrawalBatchClosed(uint256 expiry) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchClosed(expiry);
    _dirty();
    wrapper.assembly_WithdrawalBatchClosed(expiry);
    _compareCleanAgainstDirty("WithdrawalBatchClosed");
  }

  function _scratch_WithdrawalBatchPayment(
    uint256 expiry,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
    _dirty();
    wrapper.assembly_WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
    _compareCleanAgainstDirty("WithdrawalBatchPayment");
  }

  function _scratch_WithdrawalQueued(
    uint256 expiry,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
    _dirty();
    wrapper.assembly_WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
    _compareCleanAgainstDirty("WithdrawalQueued");
  }

  function _scratch_WithdrawalExecuted(
    uint256 expiry,
    address account,
    uint256 normalizedAmount
  ) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalExecuted(expiry, account, normalizedAmount);
    _dirty();
    wrapper.assembly_WithdrawalExecuted(expiry, account, normalizedAmount);
    _compareCleanAgainstDirty("WithdrawalExecuted");
  }

  function _scratch_SanctionedAccountWithdrawalSentToEscrow(
    address account,
    address escrow,
    uint32 expiry,
    uint256 amount
  ) internal {
    _cleanWindow();
    wrapper.assembly_SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
    _dirty();
    wrapper.assembly_SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
    _compareCleanAgainstDirty("SanctionedAccountWithdrawalSentToEscrow");
  }

  function _scratch_ChangedSpherexOperator(
    address oldSphereXAdmin,
    address newSphereXAdmin
  ) internal {
    _cleanWindow();
    wrapper.assembly_ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
    _dirty();
    wrapper.assembly_ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
    _compareCleanAgainstDirty("ChangedSpherexOperator");
  }

  function _scratch_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) internal {
    _cleanWindow();
    wrapper.assembly_ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
    _dirty();
    wrapper.assembly_ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
    _compareCleanAgainstDirty("ChangedSpherexEngineAddress");
  }

  function _scratch_SpherexAdminTransferStarted(
    address currentAdmin,
    address pendingAdmin
  ) internal {
    _cleanWindow();
    wrapper.assembly_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    _dirty();
    wrapper.assembly_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    _compareCleanAgainstDirty("SpherexAdminTransferStarted");
  }

  function _scratch_SpherexAdminTransferCompleted(address oldAdmin, address newAdmin) internal {
    _cleanWindow();
    wrapper.assembly_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    _dirty();
    wrapper.assembly_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    _compareCleanAgainstDirty("SpherexAdminTransferCompleted");
  }

  function _scratch_NewAllowedSenderOnchain(address sender) internal {
    _cleanWindow();
    wrapper.assembly_NewAllowedSenderOnchain(sender);
    _dirty();
    wrapper.assembly_NewAllowedSenderOnchain(sender);
    _compareCleanAgainstDirty("NewAllowedSenderOnchain");
  }
}
