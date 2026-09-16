// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IMarketEventsAndErrors} from "./vendor/interfaces/IMarketEventsAndErrors.sol";
import {SphereXConfig} from "./vendor/spherex/SphereXConfig.sol";

/// @dev The mirror-emit oracle. It declares no event of its own: every log it
///      produces comes from the compiler's `emit` of a declaration imported
///      from the fetched closure, qualified by the declaring type, so a
///      change to a declaration changes this reference with it. One external
///      function per declared event, arguments typed exactly as declared.
///      Nothing is emitted during construction.
contract MirrorEmitReference {
  // ---- IMarketEventsAndErrors --------------------------------------------

  function mirror_Transfer(address from, address to, uint256 value) external {
    emit IMarketEventsAndErrors.Transfer(from, to, value);
  }

  function mirror_Approval(address owner, address spender, uint256 value) external {
    emit IMarketEventsAndErrors.Approval(owner, spender, value);
  }

  function mirror_MaxTotalSupplyUpdated(uint256 assets) external {
    emit IMarketEventsAndErrors.MaxTotalSupplyUpdated(assets);
  }

  function mirror_ProtocolFeeBipsUpdated(uint256 protocolFeeBips) external {
    emit IMarketEventsAndErrors.ProtocolFeeBipsUpdated(protocolFeeBips);
  }

  function mirror_AnnualInterestBipsUpdated(uint256 annualInterestBipsUpdated) external {
    emit IMarketEventsAndErrors.AnnualInterestBipsUpdated(annualInterestBipsUpdated);
  }

  function mirror_ReserveRatioBipsUpdated(uint256 reserveRatioBipsUpdated) external {
    emit IMarketEventsAndErrors.ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
  }

  function mirror_SanctionedAccountAssetsSentToEscrow(
    address account,
    address escrow,
    uint256 amount
  ) external {
    emit IMarketEventsAndErrors.SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
  }

  function mirror_SanctionedAccountAssetsQueuedForWithdrawal(
    address account,
    uint256 expiry,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    emit IMarketEventsAndErrors.SanctionedAccountAssetsQueuedForWithdrawal(
      account,
      expiry,
      scaledAmount,
      normalizedAmount
    );
  }

  function mirror_Deposit(address account, uint256 assetAmount, uint256 scaledAmount) external {
    emit IMarketEventsAndErrors.Deposit(account, assetAmount, scaledAmount);
  }

  function mirror_Borrow(uint256 assetAmount) external {
    emit IMarketEventsAndErrors.Borrow(assetAmount);
  }

  function mirror_DebtRepaid(address from, uint256 assetAmount) external {
    emit IMarketEventsAndErrors.DebtRepaid(from, assetAmount);
  }

  function mirror_MarketClosed(uint256 timestamp) external {
    emit IMarketEventsAndErrors.MarketClosed(timestamp);
  }

  function mirror_FeesCollected(uint256 assets) external {
    emit IMarketEventsAndErrors.FeesCollected(assets);
  }

  function mirror_StateUpdated(uint256 scaleFactor, bool isDelinquent) external {
    emit IMarketEventsAndErrors.StateUpdated(scaleFactor, isDelinquent);
  }

  function mirror_InterestAndFeesAccrued(
    uint256 fromTimestamp,
    uint256 toTimestamp,
    uint256 scaleFactor,
    uint256 baseInterestRay,
    uint256 delinquencyFeeRay,
    uint256 protocolFees
  ) external {
    emit IMarketEventsAndErrors.InterestAndFeesAccrued(
      fromTimestamp,
      toTimestamp,
      scaleFactor,
      baseInterestRay,
      delinquencyFeeRay,
      protocolFees
    );
  }

  function mirror_WithdrawalBatchExpired(
    uint256 expiry,
    uint256 scaledTotalAmount,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    emit IMarketEventsAndErrors.WithdrawalBatchExpired(
      expiry,
      scaledTotalAmount,
      scaledAmountBurned,
      normalizedAmountPaid
    );
  }

  function mirror_WithdrawalBatchCreated(uint256 expiry) external {
    emit IMarketEventsAndErrors.WithdrawalBatchCreated(expiry);
  }

  function mirror_WithdrawalBatchClosed(uint256 expiry) external {
    emit IMarketEventsAndErrors.WithdrawalBatchClosed(expiry);
  }

  function mirror_WithdrawalBatchPayment(
    uint256 expiry,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    emit IMarketEventsAndErrors.WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid);
  }

  function mirror_WithdrawalQueued(
    uint256 expiry,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    emit IMarketEventsAndErrors.WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
  }

  function mirror_WithdrawalExecuted(
    uint256 expiry,
    address account,
    uint256 normalizedAmount
  ) external {
    emit IMarketEventsAndErrors.WithdrawalExecuted(expiry, account, normalizedAmount);
  }

  function mirror_SanctionedAccountWithdrawalSentToEscrow(
    address account,
    address escrow,
    uint32 expiry,
    uint256 amount
  ) external {
    emit IMarketEventsAndErrors.SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount);
  }

  // ---- SphereXConfig -------------------------------------------------------

  function mirror_ChangedSpherexOperator(address oldSphereXAdmin, address newSphereXAdmin) external {
    emit SphereXConfig.ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
  }

  function mirror_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) external {
    emit SphereXConfig.ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
  }

  function mirror_SpherexAdminTransferStarted(address currentAdmin, address pendingAdmin) external {
    emit SphereXConfig.SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
  }

  function mirror_SpherexAdminTransferCompleted(address oldAdmin, address newAdmin) external {
    emit SphereXConfig.SpherexAdminTransferCompleted(oldAdmin, newAdmin);
  }

  function mirror_NewAllowedSenderOnchain(address sender) external {
    emit SphereXConfig.NewAllowedSenderOnchain(sender);
  }
}
