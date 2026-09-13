// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {
  emit_Transfer,
  emit_Approval,
  emit_MaxTotalSupplyUpdated,
  emit_ProtocolFeeBipsUpdated,
  emit_AnnualInterestBipsUpdated,
  emit_ReserveRatioBipsUpdated,
  emit_SanctionedAccountAssetsSentToEscrow,
  emit_SanctionedAccountAssetsQueuedForWithdrawal,
  emit_Deposit,
  emit_Borrow,
  emit_DebtRepaid,
  emit_MarketClosed,
  emit_FeesCollected,
  emit_StateUpdated,
  emit_InterestAndFeesAccrued,
  emit_WithdrawalBatchExpired,
  emit_WithdrawalBatchCreated,
  emit_WithdrawalBatchClosed,
  emit_WithdrawalBatchPayment,
  emit_WithdrawalQueued,
  emit_WithdrawalExecuted,
  emit_SanctionedAccountWithdrawalSentToEscrow
} from "./vendor/libraries/MarketEvents.sol";
import {
  emit_ChangedSpherexOperator,
  emit_ChangedSpherexEngineAddress,
  emit_SpherexAdminTransferStarted,
  emit_SpherexAdminTransferCompleted,
  emit_NewAllowedSenderOnchain
} from "./vendor/spherex/SphereXProtectedEvents.sol";

/// @dev The external face of the 27 assembly emitters. Each free function is
///      internal to its caller, so a recorded log is attributable only when
///      the call that emits it is itself external; this contract gives every
///      emitter one such call, typed exactly as the emitter declares its
///      parameters. Nothing is emitted during construction.
///
///      Two memory observations ride in the calling frame, because that is
///      the only frame the free functions share: the free memory pointer at
///      `0x40` is read immediately before and after the emitter and stored,
///      and when `dirtyScratch` is set the scratch space `0x00`..`0x5f` is
///      dirtied first. Dirtying writes a non-zero pattern over `0x00`..`0x3f`
///      and moves the pointer at `0x40` one word up after writing the pattern
///      into the word it vacates, so the slot no longer holds the value the
///      compiler left there while memory stays well formed for the code that
///      runs after the emitter. Storage writes touch no memory.
contract AssemblyEmitWrapper {
  bool public dirtyScratch;
  uint256 public freePointerBefore;
  uint256 public freePointerAfter;

  uint256 internal constant SCRATCH_PATTERN =
    0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef;

  function setDirtyScratch(bool on) external {
    dirtyScratch = on;
  }

  function _enter() internal {
    if (dirtyScratch) {
      assembly {
        mstore(0x00, SCRATCH_PATTERN)
        mstore(0x20, not(SCRATCH_PATTERN))
        let fmp := mload(0x40)
        mstore(fmp, SCRATCH_PATTERN)
        mstore(0x40, add(fmp, 0x20))
      }
    }
    uint256 before;
    assembly {
      before := mload(0x40)
    }
    freePointerBefore = before;
  }

  function _leave() internal {
    uint256 afterCall;
    assembly {
      afterCall := mload(0x40)
    }
    freePointerAfter = afterCall;
  }

  // ---- MarketEvents.sol ----------------------------------------------------

  function assembly_Transfer(address from, address to, uint256 value) external {
    _enter();
    emit_Transfer(from, to, value);
    _leave();
  }

  function assembly_Approval(address owner, address spender, uint256 value) external {
    _enter();
    emit_Approval(owner, spender, value);
    _leave();
  }

  function assembly_MaxTotalSupplyUpdated(uint256 assets) external {
    _enter();
    emit_MaxTotalSupplyUpdated(assets);
    _leave();
  }

  function assembly_ProtocolFeeBipsUpdated(uint256 protocolFeeBips) external {
    _enter();
    emit_ProtocolFeeBipsUpdated(protocolFeeBips);
    _leave();
  }

  function assembly_AnnualInterestBipsUpdated(uint256 annualInterestBipsUpdated) external {
    _enter();
    emit_AnnualInterestBipsUpdated(annualInterestBipsUpdated);
    _leave();
  }

  function assembly_ReserveRatioBipsUpdated(uint256 reserveRatioBipsUpdated) external {
    _enter();
    emit_ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
    _leave();
  }

  function assembly_SanctionedAccountAssetsSentToEscrow(
    address account,
    address escrow,
    uint256 amount
  ) external {
    _enter();
    emit_SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
    _leave();
  }

  function assembly_SanctionedAccountAssetsQueuedForWithdrawal(
    address account,
    uint32 expiry,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    _enter();
    emit_SanctionedAccountAssetsQueuedForWithdrawal(account, expiry, scaledAmount, normalizedAmount);
    _leave();
  }

  function assembly_Deposit(address account, uint256 assetAmount, uint256 scaledAmount) external {
    _enter();
    emit_Deposit(account, assetAmount, scaledAmount);
    _leave();
  }

  function assembly_Borrow(uint256 assetAmount) external {
    _enter();
    emit_Borrow(assetAmount);
    _leave();
  }

  function assembly_DebtRepaid(address from, uint256 assetAmount) external {
    _enter();
    emit_DebtRepaid(from, assetAmount);
    _leave();
  }

  function assembly_MarketClosed(uint256 _timestamp) external {
    _enter();
    emit_MarketClosed(_timestamp);
    _leave();
  }

  function assembly_FeesCollected(uint256 assets) external {
    _enter();
    emit_FeesCollected(assets);
    _leave();
  }

  function assembly_StateUpdated(uint256 scaleFactor, bool isDelinquent) external {
    _enter();
    emit_StateUpdated(scaleFactor, isDelinquent);
    _leave();
  }

  function assembly_InterestAndFeesAccrued(
    uint256 fromTimestamp,
    uint256 toTimestamp,
    uint256 scaleFactor,
    uint256 baseInterestRay,
    uint256 delinquencyFeeRay,
    uint256 protocolFees
  ) external {
    _enter();
    emit_InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
    _leave();
  }

  function assembly_WithdrawalBatchExpired(
    uint256 expiry,
    uint256 scaledTotalAmount,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    _enter();
    emit_WithdrawalBatchExpired(expiry, scaledTotalAmount, scaledAmountBurned, normalizedAmountPaid);
    _leave();
  }

  function assembly_WithdrawalBatchCreated(uint256 expiry) external {
    _enter();
    emit_WithdrawalBatchCreated(expiry);
    _leave();
  }

  function assembly_WithdrawalBatchClosed(uint256 expiry) external {
    _enter();
    emit_WithdrawalBatchClosed(expiry);
    _leave();
  }

  function assembly_WithdrawalBatchPayment(
    uint256 expiry,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    _enter();
    emit_WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
    _leave();
  }

  function assembly_WithdrawalQueued(
    uint256 expiry,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    _enter();
    emit_WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
    _leave();
  }

  function assembly_WithdrawalExecuted(
    uint256 expiry,
    address account,
    uint256 normalizedAmount
  ) external {
    _enter();
    emit_WithdrawalExecuted(expiry, account, normalizedAmount);
    _leave();
  }

  function assembly_SanctionedAccountWithdrawalSentToEscrow(
    address account,
    address escrow,
    uint32 expiry,
    uint256 amount
  ) external {
    _enter();
    emit_SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
    _leave();
  }

  // ---- SphereXProtectedEvents.sol -----------------------------------------

  function assembly_ChangedSpherexOperator(
    address oldSphereXAdmin,
    address newSphereXAdmin
  ) external {
    _enter();
    emit_ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
    _leave();
  }

  function assembly_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) external {
    _enter();
    emit_ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
    _leave();
  }

  function assembly_SpherexAdminTransferStarted(
    address currentAdmin,
    address pendingAdmin
  ) external {
    _enter();
    emit_SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
    _leave();
  }

  function assembly_SpherexAdminTransferCompleted(address oldAdmin, address newAdmin) external {
    _enter();
    emit_SpherexAdminTransferCompleted(oldAdmin, newAdmin);
    _leave();
  }

  function assembly_NewAllowedSenderOnchain(address sender) external {
    _enter();
    emit_NewAllowedSenderOnchain(sender);
    _leave();
  }
}
