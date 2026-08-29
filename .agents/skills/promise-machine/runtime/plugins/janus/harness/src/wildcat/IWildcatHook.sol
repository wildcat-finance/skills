// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

/// @dev The subset of the Wildcat v2.5 `IHooks` surface the host model calls.
///      Signatures mirror src/access/IHooks.sol at the v2.5 anchor commit
///      9716e78. Only the reactive hooks the maintained templates actually
///      enable are modeled: deposit, queueWithdrawal, transfer, and the one
///      value-returning hook. `intermediateState` is reduced to the fields a
///      conformance hook reads.
interface IWildcatHook {
  struct MarketState {
    uint256 scaledTotalSupply;
    uint256 scaledPendingWithdrawals;
    uint32 pendingWithdrawalExpiry;
    uint16 annualInterestBips;
    uint16 reserveRatioBips;
    bool isClosed;
  }

  /// @dev Called before a deposit's effects are applied. IHooks.sol:47.
  function onDeposit(
    address lender,
    uint256 scaledAmount,
    MarketState calldata intermediateState,
    bytes calldata extraData
  ) external;

  /// @dev Called after pendingWithdrawalExpiry is set but before the balance is
  ///      debited. The documented queueWithdrawal state exception. IHooks.sol:54.
  function onQueueWithdrawal(
    address lender,
    uint32 expiry,
    uint256 scaledAmount,
    MarketState calldata intermediateState,
    bytes calldata extraData
  ) external;

  /// @dev Called before a transfer's effects are applied. IHooks.sol:73.
  function onTransfer(
    address caller,
    address from,
    address to,
    uint256 scaledAmount,
    MarketState calldata intermediateState,
    bytes calldata extraData
  ) external;

  /// @dev The one value-returning hook: the market applies the returned pair
  ///      within its own bounds. IHooks.sol:118, HooksConfig.sol:741-808.
  function onSetAnnualInterestAndReserveRatioBips(
    uint16 annualInterestBips,
    uint16 reserveRatioBips,
    MarketState calldata intermediateState,
    bytes calldata extraData
  ) external returns (uint16 updatedAnnualInterestBips, uint16 updatedReserveRatioBips);
}
