// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.22;

import {IERC20} from "./vendor/interfaces/IERC20.sol";
import {IMarketEventsAndErrors} from "./vendor/interfaces/IMarketEventsAndErrors.sol";
import {ISphereXProtectedRegisteredBase} from "./vendor/interfaces/ISphereXProtectedRegisteredBase.sol";
import {IWildcatArchController} from "./vendor/interfaces/IWildcatArchController.sol";
import {SphereXConfig} from "./vendor/spherex/SphereXConfig.sol";
import {SphereXProtectedRegisteredBase} from "./vendor/spherex/SphereXProtectedRegisteredBase.sol";
import {AuthRole} from "./vendor/interfaces/WildcatStructsAndEnums.sol";

/// @dev The mirror-emit oracle for V1. It declares no event of its own: every
///      log comes from the compiler's `emit` of a declaration in the fetched
///      closure, qualified by the declaring type. There is one external
///      function per pair of an emitter and a same-named declaration in the
///      #1962 table, `docs/kickoff/1962/emitters.json`, named
///      `mirror_<DeclaringType>_<Event>`, so every one of its 37 rows has its
///      own reference. Arguments are typed exactly as declared. Nothing is
///      emitted during construction.
contract MirrorEmitReference {
  function mirror_IERC20_Transfer(address from, address to, uint256 value) external {
    emit IERC20.Transfer(from, to, value);
  }

  function mirror_IMarketEventsAndErrors_Transfer(
    address from,
    address to,
    uint256 value
  ) external {
    emit IMarketEventsAndErrors.Transfer(from, to, value);
  }

  function mirror_IERC20_Approval(address owner, address spender, uint256 value) external {
    emit IERC20.Approval(owner, spender, value);
  }

  function mirror_IMarketEventsAndErrors_Approval(
    address owner,
    address spender,
    uint256 value
  ) external {
    emit IMarketEventsAndErrors.Approval(owner, spender, value);
  }

  function mirror_IMarketEventsAndErrors_MaxTotalSupplyUpdated(uint256 assets) external {
    emit IMarketEventsAndErrors.MaxTotalSupplyUpdated(assets);
  }

  function mirror_IMarketEventsAndErrors_AnnualInterestBipsUpdated(
    uint256 annualInterestBipsUpdated
  ) external {
    emit IMarketEventsAndErrors.AnnualInterestBipsUpdated(annualInterestBipsUpdated);
  }

  function mirror_IMarketEventsAndErrors_ReserveRatioBipsUpdated(
    uint256 reserveRatioBipsUpdated
  ) external {
    emit IMarketEventsAndErrors.ReserveRatioBipsUpdated(reserveRatioBipsUpdated);
  }

  function mirror_IMarketEventsAndErrors_SanctionedAccountAssetsSentToEscrow(
    address account,
    address escrow,
    uint256 amount
  ) external {
    emit IMarketEventsAndErrors.SanctionedAccountAssetsSentToEscrow(account, escrow, amount);
  }

  function mirror_IMarketEventsAndErrors_Deposit(
    address account,
    uint256 assetAmount,
    uint256 scaledAmount
  ) external {
    emit IMarketEventsAndErrors.Deposit(account, assetAmount, scaledAmount);
  }

  function mirror_IMarketEventsAndErrors_Borrow(uint256 assetAmount) external {
    emit IMarketEventsAndErrors.Borrow(assetAmount);
  }

  function mirror_IMarketEventsAndErrors_DebtRepaid(address from, uint256 assetAmount) external {
    emit IMarketEventsAndErrors.DebtRepaid(from, assetAmount);
  }

  function mirror_IMarketEventsAndErrors_MarketClosed(uint256 timestamp) external {
    emit IMarketEventsAndErrors.MarketClosed(timestamp);
  }

  function mirror_IMarketEventsAndErrors_FeesCollected(uint256 assets) external {
    emit IMarketEventsAndErrors.FeesCollected(assets);
  }

  function mirror_IMarketEventsAndErrors_StateUpdated(
    uint256 scaleFactor,
    bool isDelinquent
  ) external {
    emit IMarketEventsAndErrors.StateUpdated(scaleFactor, isDelinquent);
  }

  function mirror_IMarketEventsAndErrors_InterestAndFeesAccrued(
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

  function mirror_IMarketEventsAndErrors_AuthorizationStatusUpdated(
    address account,
    AuthRole role
  ) external {
    emit IMarketEventsAndErrors.AuthorizationStatusUpdated(account, role);
  }

  function mirror_IMarketEventsAndErrors_WithdrawalBatchExpired(
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

  function mirror_IMarketEventsAndErrors_WithdrawalBatchCreated(uint256 expiry) external {
    emit IMarketEventsAndErrors.WithdrawalBatchCreated(expiry);
  }

  function mirror_IMarketEventsAndErrors_WithdrawalBatchClosed(uint256 expiry) external {
    emit IMarketEventsAndErrors.WithdrawalBatchClosed(expiry);
  }

  function mirror_IMarketEventsAndErrors_WithdrawalBatchPayment(
    uint256 expiry,
    uint256 scaledAmountBurned,
    uint256 normalizedAmountPaid
  ) external {
    emit IMarketEventsAndErrors.WithdrawalBatchPayment(
      expiry,
      scaledAmountBurned,
      normalizedAmountPaid
    );
  }

  function mirror_IMarketEventsAndErrors_WithdrawalQueued(
    uint256 expiry,
    address account,
    uint256 scaledAmount,
    uint256 normalizedAmount
  ) external {
    emit IMarketEventsAndErrors.WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount);
  }

  function mirror_IMarketEventsAndErrors_WithdrawalExecuted(
    uint256 expiry,
    address account,
    uint256 normalizedAmount
  ) external {
    emit IMarketEventsAndErrors.WithdrawalExecuted(expiry, account, normalizedAmount);
  }

  function mirror_IMarketEventsAndErrors_SanctionedAccountWithdrawalSentToEscrow(
    address account,
    address escrow,
    uint32 expiry,
    uint256 amount
  ) external {
    emit IMarketEventsAndErrors.SanctionedAccountWithdrawalSentToEscrow(
      account,
      escrow,
      expiry,
      amount
    );
  }

  function mirror_ISphereXProtectedRegisteredBase_ChangedSpherexOperator(
    address oldSphereXAdmin,
    address newSphereXAdmin
  ) external {
    emit ISphereXProtectedRegisteredBase.ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
  }

  function mirror_IWildcatArchController_ChangedSpherexOperator(
    address oldSphereXAdmin,
    address newSphereXAdmin
  ) external {
    emit IWildcatArchController.ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
  }

  function mirror_SphereXConfig_ChangedSpherexOperator(
    address oldSphereXAdmin,
    address newSphereXAdmin
  ) external {
    emit SphereXConfig.ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
  }

  function mirror_SphereXProtectedRegisteredBase_ChangedSpherexOperator(
    address oldSphereXAdmin,
    address newSphereXAdmin
  ) external {
    emit SphereXProtectedRegisteredBase.ChangedSpherexOperator(oldSphereXAdmin, newSphereXAdmin);
  }

  function mirror_ISphereXProtectedRegisteredBase_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) external {
    emit ISphereXProtectedRegisteredBase.ChangedSpherexEngineAddress(
      oldEngineAddress,
      newEngineAddress
    );
  }

  function mirror_IWildcatArchController_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) external {
    emit IWildcatArchController.ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
  }

  function mirror_SphereXConfig_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) external {
    emit SphereXConfig.ChangedSpherexEngineAddress(oldEngineAddress, newEngineAddress);
  }

  function mirror_SphereXProtectedRegisteredBase_ChangedSpherexEngineAddress(
    address oldEngineAddress,
    address newEngineAddress
  ) external {
    emit SphereXProtectedRegisteredBase.ChangedSpherexEngineAddress(
      oldEngineAddress,
      newEngineAddress
    );
  }

  function mirror_IWildcatArchController_SpherexAdminTransferStarted(
    address currentAdmin,
    address pendingAdmin
  ) external {
    emit IWildcatArchController.SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
  }

  function mirror_SphereXConfig_SpherexAdminTransferStarted(
    address currentAdmin,
    address pendingAdmin
  ) external {
    emit SphereXConfig.SpherexAdminTransferStarted(currentAdmin, pendingAdmin);
  }

  function mirror_IWildcatArchController_SpherexAdminTransferCompleted(
    address oldAdmin,
    address newAdmin
  ) external {
    emit IWildcatArchController.SpherexAdminTransferCompleted(oldAdmin, newAdmin);
  }

  function mirror_SphereXConfig_SpherexAdminTransferCompleted(
    address oldAdmin,
    address newAdmin
  ) external {
    emit SphereXConfig.SpherexAdminTransferCompleted(oldAdmin, newAdmin);
  }

  function mirror_IWildcatArchController_NewAllowedSenderOnchain(address sender) external {
    emit IWildcatArchController.NewAllowedSenderOnchain(sender);
  }

  function mirror_SphereXConfig_NewAllowedSenderOnchain(address sender) external {
    emit SphereXConfig.NewAllowedSenderOnchain(sender);
  }
}
