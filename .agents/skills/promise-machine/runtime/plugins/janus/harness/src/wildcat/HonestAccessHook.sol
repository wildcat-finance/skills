// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IWildcatHook} from "./IWildcatHook.sol";

/// @dev An honest access-control hook shaped like the Wildcat OpenTermHooks
///      template. It gates deposits, queued withdrawals and transfers on a
///      credential, keeps a monotone known-lender bit so a lender who once
///      qualified can always exit, writes only its own storage, makes no
///      external call, moves no value, and returns the APR and reserve pair
///      unchanged. It is the baseline the hostile hooks are measured against:
///      it passes every applicable gate.
contract HonestAccessHook is IWildcatHook {
  error NotApprovedLender();

  address public immutable admin;

  mapping(address => bool) public approved;
  mapping(address => uint256) public credentialExpiry;
  mapping(address => bool) public knownLender;

  constructor() {
    admin = msg.sender;
  }

  /// @dev Stand-in for a role provider granting a credential.
  function grant(address lender, uint256 expiry) external {
    approved[lender] = true;
    credentialExpiry[lender] = expiry;
  }

  /// @dev Stand-in for provider removal: the credential stops validating, but
  ///      the monotone known-lender bit is deliberately left untouched, which
  ///      is what keeps the exit open.
  function removeProvider(address lender) external {
    approved[lender] = false;
  }

  function _hasCredential(address lender) internal view returns (bool) {
    return approved[lender] && block.timestamp <= credentialExpiry[lender];
  }

  function onDeposit(
    address lender,
    uint256,
    MarketState calldata,
    bytes calldata
  ) external override {
    if (!knownLender[lender] && !_hasCredential(lender)) revert NotApprovedLender();
    knownLender[lender] = true;
  }

  function onQueueWithdrawal(
    address lender,
    uint32,
    uint256,
    MarketState calldata,
    bytes calldata
  ) external view override {
    // Monotone: a known lender always clears this, so the exit stays open even
    // after the credential lapses or the provider is removed.
    if (!knownLender[lender] && !_hasCredential(lender)) revert NotApprovedLender();
  }

  function onTransfer(
    address,
    address,
    address to,
    uint256,
    MarketState calldata,
    bytes calldata
  ) external override {
    if (!knownLender[to] && !_hasCredential(to)) revert NotApprovedLender();
    knownLender[to] = true;
  }

  function onSetAnnualInterestAndReserveRatioBips(
    uint16 annualInterestBips,
    uint16 reserveRatioBips,
    MarketState calldata,
    bytes calldata
  ) external pure override returns (uint16, uint16) {
    return (annualInterestBips, reserveRatioBips);
  }
}
