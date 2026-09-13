// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {Vm, VM_ADDRESS} from "../src/Vm.sol";
import {LogComparison} from "../src/LogComparison.sol";
import {AssemblyEmitWrapper} from "../src/AssemblyEmitWrapper.sol";
import {MirrorEmitReference} from "../src/MirrorEmitReference.sol";
import {WrongTopic0Specimen} from "../src/specimens/WrongTopic0Specimen.sol";
import {WrongDataSpecimen} from "../src/specimens/WrongDataSpecimen.sol";
import {WrongTopicCountSpecimen} from "../src/specimens/WrongTopicCountSpecimen.sol";
import {WrongIndexedTopicSpecimen} from "../src/specimens/WrongIndexedTopicSpecimen.sol";
import {WrongDataLengthSpecimen} from "../src/specimens/WrongDataLengthSpecimen.sol";

/// @dev The emitter-fidelity differential suite: 27 fuzz cases, one per
///      assembly emitter, each recording exactly two logs in one window and
///      pairing them by position (index 0 the assembly, index 1 the
///      reference). Every case fuzzes over the emitter's own parameter types.
///      The fuzzer's dictionary is not relied on for ABI edge values: two
///      fixed companion cases drive every emitter at all-zero and at all-max
///      arguments through the same pairing helpers, so those values are
///      reached on every run rather than when a seed happens to hit them.
///      Expected logs come only from the compiler's `emit` of the vendored
///      declarations; no topic, arity or data offset is written here.
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
  ///      so no construction-time log can enter a pair.
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

  /// @dev Fetch the window: exactly two logs, the first from the assembly
  ///      wrapper and the second from the reference, then compare them.
  function _comparePair() internal {
    Vm.Log[] memory logs = vm.getRecordedLogs();
    require(logs.length == 2, "recorded log count");
    require(logs[0].emitter == address(wrapper), "log 0 is not the assembly");
    require(logs[1].emitter == address(mirror), "log 1 is not the reference");
    LogComparison.compare(logs[0], logs[1]);
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

  // ---- per-emitter helpers, shared by the fuzz and companion cases -------

  function _pair_Transfer(address from, address to, uint256 value) internal {
    vm.recordLogs();
    wrapper.assembly_Transfer(from, to, value);
    mirror.mirror_Transfer(from, to, value);
    _comparePair();
  }

  function _pair_Approval(address owner, address spender, uint256 value) internal {
    vm.recordLogs();
    wrapper.assembly_Approval(owner, spender, value);
    mirror.mirror_Approval(owner, spender, value);
    _comparePair();
  }

  function _pair_MaxTotalSupplyUpdated(uint256 assets) internal {
    vm.recordLogs();
    wrapper.assembly_MaxTotalSupplyUpdated(assets);
    mirror.mirror_MaxTotalSupplyUpdated(assets);
    _comparePair();
  }

  function _pair_ProtocolFeeBipsUpdated(uint256 protocolFeeBips) internal {
    vm.recordLogs();
    wrapper.assembly_ProtocolFeeBipsUpdated(protocolFeeBips);
    mirror.mirror_ProtocolFeeBipsUpdated(protocolFeeBips);
    _comparePair();
  }

  function _pair_AnnualInterestBipsUpdated(uint256 bips) internal {
    vm.recordLogs();
    wrapper.assembly_AnnualInterestBipsUpdated(bips);
    mirror.mirror_AnnualInterestBipsUpdated(bips);
    _comparePair();
  }

  function _pair_ReserveRatioBipsUpdated(uint256 bips) internal {
    vm.recordLogs();
    wrapper.assembly_ReserveRatioBipsUpdated(bips);
    mirror.mirror_ReserveRatioBipsUpdated(bips);
    _comparePair();
  }

  function _pair_SanctionedAccountAssetsSentToEscrow(
    address account,
    address escrow,
    uint256 amount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
    mirror.mirror_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
    _comparePair();
  }

  /// @dev The emitter takes `uint32 expiry` where the declaration takes
  ///      `uint256 expiry`. The domain is the emitter's (`uint32`), and the
  ///      value is widened explicitly to the declared type for the reference.
  function _pair_SanctionedAccountAssetsQueuedForWithdrawal(
    address account,
    uint32 expiry,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_SanctionedAccountAssetsQueuedForWithdrawal(
      account,
      expiry,
      scaledAmount,
      normalizedAmount
    );
    mirror.mirror_SanctionedAccountAssetsQueuedForWithdrawal(
      account,
      uint256(expiry), // explicit widening: emitter uint32 -> declared uint256
      scaledAmount,
      normalizedAmount
    );
    _comparePair();
  }

  function _pair_Deposit(address account, uint256 assetAmount, uint256 scaledAmount) internal {
    vm.recordLogs();
    wrapper.assembly_Deposit(account, assetAmount, scaledAmount);
    mirror.mirror_Deposit(account, assetAmount, scaledAmount);
    _comparePair();
  }

  function _pair_Borrow(uint256 assetAmount) internal {
    vm.recordLogs();
    wrapper.assembly_Borrow(assetAmount);
    mirror.mirror_Borrow(assetAmount);
    _comparePair();
  }

  function _pair_DebtRepaid(address from, uint256 assetAmount) internal {
    vm.recordLogs();
    wrapper.assembly_DebtRepaid(from, assetAmount);
    mirror.mirror_DebtRepaid(from, assetAmount);
    _comparePair();
  }

  function _pair_MarketClosed(uint256 timestamp) internal {
    vm.recordLogs();
    wrapper.assembly_MarketClosed(timestamp);
    mirror.mirror_MarketClosed(timestamp);
    _comparePair();
  }

  function _pair_FeesCollected(uint256 assets) internal {
    vm.recordLogs();
    wrapper.assembly_FeesCollected(assets);
    mirror.mirror_FeesCollected(assets);
    _comparePair();
  }

  function _pair_StateUpdated(uint256 scaleFactor, bool isDelinquent) internal {
    vm.recordLogs();
    wrapper.assembly_StateUpdated(scaleFactor, isDelinquent);
    mirror.mirror_StateUpdated(scaleFactor, isDelinquent);
    _comparePair();
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
    mirror.mirror_InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
    _comparePair();
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
    mirror.mirror_WithdrawalBatchExpired(
      expiry,
      scaledTotalAmount,
      scaledAmountBurned,
      normalizedAmountPaid
    );
    _comparePair();
  }

  function _pair_WithdrawalBatchCreated(uint256 expiry) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalBatchCreated(expiry);
    mirror.mirror_WithdrawalBatchCreated(expiry);
    _comparePair();
  }

  function _pair_WithdrawalBatchClosed(uint256 expiry) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalBatchClosed(expiry);
    mirror.mirror_WithdrawalBatchClosed(expiry);
    _comparePair();
  }

  function _pair_WithdrawalBatchPayment(
    uint256 expiry,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
    mirror.mirror_WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
    _comparePair();
  }

  function _pair_WithdrawalQueued(
    uint256 expiry,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
    mirror.mirror_WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
    _comparePair();
  }

  function _pair_WithdrawalExecuted(
    uint256 expiry,
    address account,
    uint256 normalizedAmount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_WithdrawalExecuted(expiry, account, normalizedAmount);
    mirror.mirror_WithdrawalExecuted(expiry, account, normalizedAmount);
    _comparePair();
  }

  function _pair_SanctionedAccountWithdrawalSentToEscrow(
    address account,
    address escrow,
    uint32 expiry,
    uint256 amount
  ) internal {
    vm.recordLogs();
    wrapper.assembly_SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
    mirror.mirror_SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
    _comparePair();
  }

  function _pair_ChangedSpherexOperator(address oldAdmin, address newAdmin) internal {
    vm.recordLogs();
    wrapper.assembly_ChangedSpherexOperator(oldAdmin, newAdmin);
    mirror.mirror_ChangedSpherexOperator(oldAdmin, newAdmin);
    _comparePair();
  }

  function _pair_ChangedSpherexEngineAddress(address oldEngine, address newEngine) internal {
    vm.recordLogs();
    wrapper.assembly_ChangedSpherexEngineAddress(oldEngine, newEngine);
    mirror.mirror_ChangedSpherexEngineAddress(oldEngine, newEngine);
    _comparePair();
  }

  function _pair_SpherexAdminTransferStarted(address currentAdmin, address pendingAdmin) internal {
    vm.recordLogs();
    wrapper.assembly_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    mirror.mirror_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    _comparePair();
  }

  function _pair_SpherexAdminTransferCompleted(address oldAdmin, address newAdmin) internal {
    vm.recordLogs();
    wrapper.assembly_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    mirror.mirror_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    _comparePair();
  }

  function _pair_NewAllowedSenderOnchain(address sender) internal {
    vm.recordLogs();
    wrapper.assembly_NewAllowedSenderOnchain(sender);
    mirror.mirror_NewAllowedSenderOnchain(sender);
    _comparePair();
  }

  // ---- the 27 fuzz cases ---------------------------------------------------
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

  function test_emit_ProtocolFeeBipsUpdated_indexed0(uint256 protocolFeeBips) external {
    _pair_ProtocolFeeBipsUpdated(protocolFeeBips);
  }

  function test_emit_AnnualInterestBipsUpdated_indexed0(uint256 bips) external {
    _pair_AnnualInterestBipsUpdated(bips);
  }

  function test_emit_ReserveRatioBipsUpdated_indexed0(uint256 bips) external {
    _pair_ReserveRatioBipsUpdated(bips);
  }

  function test_emit_SanctionedAccountAssetsSentToEscrow_indexed1(
    address account,
    address escrow,
    uint256 amount
  ) external {
    _pair_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
  }

  /// @dev Fuzzed over the emitter's `uint32 expiry`; see the pairing helper
  ///      for the explicit widening to the declared `uint256`.
  function test_emit_SanctionedAccountAssetsQueuedForWithdrawal_indexed1(
    address account,
    uint32 expiry,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    _pair_SanctionedAccountAssetsQueuedForWithdrawal(account, expiry, scaledAmount, normalizedAmount);
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

  function test_emit_WithdrawalBatchExpired_indexed1(
    uint256 expiry,
    uint256 scaledTotalAmount,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    _pair_WithdrawalBatchExpired(expiry, scaledTotalAmount, scaledAmountBurned, normalizedAmountPaid);
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

  function test_emit_ChangedSpherexOperator_indexed0(address oldAdmin, address newAdmin) external {
    _pair_ChangedSpherexOperator(oldAdmin, newAdmin);
  }

  function test_emit_ChangedSpherexEngineAddress_indexed0(
    address oldEngine,
    address newEngine
  ) external {
    _pair_ChangedSpherexEngineAddress(oldEngine, newEngine);
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

  /// @dev Every emitter at all-zero arguments (`address(0)`, `0`, `false`).
  function _pairEveryEmitter(address a, address b, uint256 x, uint256 y, uint32 e, bool f) internal {
    _pair_Transfer(a, b, x);
    _pair_Approval(a, b, x);
    _pair_MaxTotalSupplyUpdated(x);
    _pair_ProtocolFeeBipsUpdated(x);
    _pair_AnnualInterestBipsUpdated(x);
    _pair_ReserveRatioBipsUpdated(x);
    _pair_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _pair_SanctionedAccountAssetsQueuedForWithdrawal(a, e, x, y);
    _pair_Deposit(a, x, y);
    _pair_Borrow(x);
    _pair_DebtRepaid(a, x);
    _pair_MarketClosed(x);
    _pair_FeesCollected(x);
    _pair_StateUpdated(x, f);
    _pair_InterestAndFeesAccrued(x, y, x, y, x, y);
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

  function test_edge_every_emitter_at_zero() external {
    _pairEveryEmitter(address(0), address(0), 0, 0, 0, false);
  }

  function test_edge_every_emitter_at_max() external {
    _pairEveryEmitter(
      address(type(uint160).max),
      address(type(uint160).max),
      type(uint256).max,
      type(uint256).max,
      type(uint32).max,
      true
    );
  }

  // ---- rejection specimens: the comparison is proved able to fail ----------

  function _rejects(address specimen, string memory expectedField) internal {
    vm.recordLogs();
    (bool ok, ) = specimen.call(
      abi.encodeWithSignature("specimen_Transfer(address,address,uint256)", address(1), address(2), 3)
    );
    require(ok, "specimen call");
    mirror.mirror_Transfer(address(1), address(2), 3);
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
  ///      one of the 27, with and without a dirtied scratch space, and the
  ///      zero slot at `0x60` still holds zero after each emitter.
  function test_memory_free_pointer_unchanged_across_every_emitter(
    address a,
    address b,
    uint256 x,
    uint256 y,
    uint32 e,
    bool f
  ) external {
    _freePointerSweep(a, b, x, y, e, f);
    wrapper.setDirtyScratch(true);
    _freePointerSweep(a, b, x, y, e, f);
  }

  function _freePointerSweep(address a, address b, uint256 x, uint256 y, uint32 e, bool f) internal {
    wrapper.assembly_Transfer(a, b, x);
    _requireFreePointerUnchanged("Transfer moved 0x40");
    wrapper.assembly_Approval(a, b, x);
    _requireFreePointerUnchanged("Approval moved 0x40");
    wrapper.assembly_MaxTotalSupplyUpdated(x);
    _requireFreePointerUnchanged("MaxTotalSupplyUpdated moved 0x40");
    wrapper.assembly_ProtocolFeeBipsUpdated(x);
    _requireFreePointerUnchanged("ProtocolFeeBipsUpdated moved 0x40");
    wrapper.assembly_AnnualInterestBipsUpdated(x);
    _requireFreePointerUnchanged("AnnualInterestBipsUpdated moved 0x40");
    wrapper.assembly_ReserveRatioBipsUpdated(x);
    _requireFreePointerUnchanged("ReserveRatioBipsUpdated moved 0x40");
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _requireFreePointerUnchanged("SanctionedAccountAssetsSentToEscrow moved 0x40");
    wrapper.assembly_SanctionedAccountAssetsQueuedForWithdrawal(a, e, x, y);
    _requireFreePointerUnchanged("SanctionedAccountAssetsQueuedForWithdrawal moved 0x40");
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
  ///      emitter is driven twice in
  ///      one window, clean then dirty, and the two logs are compared with the
  ///      same field-by-field helper: the dirty log at index 1 is held to the
  ///      clean log at index 0, so a scratch byte that leaked into the data
  ///      region or a topic fails on the field it reached.
  function test_memory_dirtied_scratch_does_not_change_the_recorded_log(
    address a,
    address b,
    uint256 x,
    uint256 y,
    uint32 e,
    bool f
  ) external {
    _scratch_Transfer(a, b, x);
    _scratch_Approval(a, b, x);
    _scratch_MaxTotalSupplyUpdated(x);
    _scratch_ProtocolFeeBipsUpdated(x);
    _scratch_AnnualInterestBipsUpdated(x);
    _scratch_ReserveRatioBipsUpdated(x);
    _scratch_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _scratch_SanctionedAccountAssetsQueuedForWithdrawal(a, e, x, y);
    _scratch_Deposit(a, x, y);
    _scratch_Borrow(x);
    _scratch_DebtRepaid(a, x);
    _scratch_MarketClosed(x);
    _scratch_FeesCollected(x);
    _scratch_StateUpdated(x, f);
    _scratch_InterestAndFeesAccrued(x, y, x, y, x, y);
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

  /// @dev Switch to a dirtied scratch space; the caller emits once more and
  ///      the two logs of the window are compared, clean first.
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

  function _scratch_Transfer(address a, address b, uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_Transfer(a, b, x);
    _dirty();
    wrapper.assembly_Transfer(a, b, x);
    _compareCleanAgainstDirty("Transfer");
  }

  function _scratch_Approval(address a, address b, uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_Approval(a, b, x);
    _dirty();
    wrapper.assembly_Approval(a, b, x);
    _compareCleanAgainstDirty("Approval");
  }

  function _scratch_MaxTotalSupplyUpdated(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_MaxTotalSupplyUpdated(x);
    _dirty();
    wrapper.assembly_MaxTotalSupplyUpdated(x);
    _compareCleanAgainstDirty("MaxTotalSupplyUpdated");
  }

  function _scratch_ProtocolFeeBipsUpdated(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_ProtocolFeeBipsUpdated(x);
    _dirty();
    wrapper.assembly_ProtocolFeeBipsUpdated(x);
    _compareCleanAgainstDirty("ProtocolFeeBipsUpdated");
  }

  function _scratch_AnnualInterestBipsUpdated(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_AnnualInterestBipsUpdated(x);
    _dirty();
    wrapper.assembly_AnnualInterestBipsUpdated(x);
    _compareCleanAgainstDirty("AnnualInterestBipsUpdated");
  }

  function _scratch_ReserveRatioBipsUpdated(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_ReserveRatioBipsUpdated(x);
    _dirty();
    wrapper.assembly_ReserveRatioBipsUpdated(x);
    _compareCleanAgainstDirty("ReserveRatioBipsUpdated");
  }

  function _scratch_SanctionedAccountAssetsSentToEscrow(address a, address b, uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _dirty();
    wrapper.assembly_SanctionedAccountAssetsSentToEscrow(a, b, x);
    _compareCleanAgainstDirty("SanctionedAccountAssetsSentToEscrow");
  }

  function _scratch_SanctionedAccountAssetsQueuedForWithdrawal(
    address a,
    uint32 e,
    uint256 x,
    uint256 y
  ) internal {
    _cleanWindow();
    wrapper.assembly_SanctionedAccountAssetsQueuedForWithdrawal(a, e, x, y);
    _dirty();
    wrapper.assembly_SanctionedAccountAssetsQueuedForWithdrawal(a, e, x, y);
    _compareCleanAgainstDirty("SanctionedAccountAssetsQueuedForWithdrawal");
  }

  function _scratch_Deposit(address a, uint256 x, uint256 y) internal {
    _cleanWindow();
    wrapper.assembly_Deposit(a, x, y);
    _dirty();
    wrapper.assembly_Deposit(a, x, y);
    _compareCleanAgainstDirty("Deposit");
  }

  function _scratch_Borrow(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_Borrow(x);
    _dirty();
    wrapper.assembly_Borrow(x);
    _compareCleanAgainstDirty("Borrow");
  }

  function _scratch_DebtRepaid(address a, uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_DebtRepaid(a, x);
    _dirty();
    wrapper.assembly_DebtRepaid(a, x);
    _compareCleanAgainstDirty("DebtRepaid");
  }

  function _scratch_MarketClosed(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_MarketClosed(x);
    _dirty();
    wrapper.assembly_MarketClosed(x);
    _compareCleanAgainstDirty("MarketClosed");
  }

  function _scratch_FeesCollected(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_FeesCollected(x);
    _dirty();
    wrapper.assembly_FeesCollected(x);
    _compareCleanAgainstDirty("FeesCollected");
  }

  function _scratch_StateUpdated(uint256 x, bool f) internal {
    _cleanWindow();
    wrapper.assembly_StateUpdated(x, f);
    _dirty();
    wrapper.assembly_StateUpdated(x, f);
    _compareCleanAgainstDirty("StateUpdated");
  }

  function _scratch_InterestAndFeesAccrued(
    uint256 a,
    uint256 b,
    uint256 c,
    uint256 d,
    uint256 e,
    uint256 f
  ) internal {
    _cleanWindow();
    wrapper.assembly_InterestAndFeesAccrued(a, b, c, d, e, f);
    _dirty();
    wrapper.assembly_InterestAndFeesAccrued(a, b, c, d, e, f);
    _compareCleanAgainstDirty("InterestAndFeesAccrued");
  }

  function _scratch_WithdrawalBatchExpired(uint256 a, uint256 b, uint256 c, uint256 d) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchExpired(a, b, c, d);
    _dirty();
    wrapper.assembly_WithdrawalBatchExpired(a, b, c, d);
    _compareCleanAgainstDirty("WithdrawalBatchExpired");
  }

  function _scratch_WithdrawalBatchCreated(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchCreated(x);
    _dirty();
    wrapper.assembly_WithdrawalBatchCreated(x);
    _compareCleanAgainstDirty("WithdrawalBatchCreated");
  }

  function _scratch_WithdrawalBatchClosed(uint256 x) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchClosed(x);
    _dirty();
    wrapper.assembly_WithdrawalBatchClosed(x);
    _compareCleanAgainstDirty("WithdrawalBatchClosed");
  }

  function _scratch_WithdrawalBatchPayment(uint256 a, uint256 b, uint256 c) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalBatchPayment(a, b, c);
    _dirty();
    wrapper.assembly_WithdrawalBatchPayment(a, b, c);
    _compareCleanAgainstDirty("WithdrawalBatchPayment");
  }

  function _scratch_WithdrawalQueued(uint256 x, address a, uint256 y, uint256 z) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalQueued(x, a, y, z);
    _dirty();
    wrapper.assembly_WithdrawalQueued(x, a, y, z);
    _compareCleanAgainstDirty("WithdrawalQueued");
  }

  function _scratch_WithdrawalExecuted(uint256 x, address a, uint256 y) internal {
    _cleanWindow();
    wrapper.assembly_WithdrawalExecuted(x, a, y);
    _dirty();
    wrapper.assembly_WithdrawalExecuted(x, a, y);
    _compareCleanAgainstDirty("WithdrawalExecuted");
  }

  function _scratch_SanctionedAccountWithdrawalSentToEscrow(
    address a,
    address b,
    uint32 e,
    uint256 x
  ) internal {
    _cleanWindow();
    wrapper.assembly_SanctionedAccountWithdrawalSentToEscrow(a, b, e, x);
    _dirty();
    wrapper.assembly_SanctionedAccountWithdrawalSentToEscrow(a, b, e, x);
    _compareCleanAgainstDirty("SanctionedAccountWithdrawalSentToEscrow");
  }

  function _scratch_ChangedSpherexOperator(address a, address b) internal {
    _cleanWindow();
    wrapper.assembly_ChangedSpherexOperator(a, b);
    _dirty();
    wrapper.assembly_ChangedSpherexOperator(a, b);
    _compareCleanAgainstDirty("ChangedSpherexOperator");
  }

  function _scratch_ChangedSpherexEngineAddress(address a, address b) internal {
    _cleanWindow();
    wrapper.assembly_ChangedSpherexEngineAddress(a, b);
    _dirty();
    wrapper.assembly_ChangedSpherexEngineAddress(a, b);
    _compareCleanAgainstDirty("ChangedSpherexEngineAddress");
  }

  function _scratch_SpherexAdminTransferStarted(address a, address b) internal {
    _cleanWindow();
    wrapper.assembly_SpherexAdminTransferStarted(a, b);
    _dirty();
    wrapper.assembly_SpherexAdminTransferStarted(a, b);
    _compareCleanAgainstDirty("SpherexAdminTransferStarted");
  }

  function _scratch_SpherexAdminTransferCompleted(address a, address b) internal {
    _cleanWindow();
    wrapper.assembly_SpherexAdminTransferCompleted(a, b);
    _dirty();
    wrapper.assembly_SpherexAdminTransferCompleted(a, b);
    _compareCleanAgainstDirty("SpherexAdminTransferCompleted");
  }

  function _scratch_NewAllowedSenderOnchain(address a) internal {
    _cleanWindow();
    wrapper.assembly_NewAllowedSenderOnchain(a);
    _dirty();
    wrapper.assembly_NewAllowedSenderOnchain(a);
    _compareCleanAgainstDirty("NewAllowedSenderOnchain");
  }
}
