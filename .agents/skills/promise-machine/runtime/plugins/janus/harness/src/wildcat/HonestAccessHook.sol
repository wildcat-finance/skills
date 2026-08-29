// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IWildcatHook} from "./IWildcatHook.sol";
import {IRoleProviderCalls} from "./IRoleProvider.sol";

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

  /// @dev Optional. When set, `onDeposit` makes the `validateCredential` call
  ///      the manifest declares, so the honest example exercises a non-empty
  ///      resolved permit set rather than passing gate 1 by calling nothing.
  ///      A hook that calls nothing satisfies any permitted-call set, including
  ///      a wrong one, so the empty case cannot tell a correct set from a
  ///      broken one.
  ///
  ///      Left unset the hook behaves exactly as before, which is what keeps
  ///      the hostile suite and the gate 3 liveness path unchanged: neither
  ///      needs a provider and neither should grow a dependency on one.
  IRoleProviderCalls public roleProvider;

  mapping(address => bool) public approved;
  mapping(address => uint256) public credentialExpiry;
  mapping(address => bool) public knownLender;

  constructor() {
    admin = msg.sender;
  }

  /// @dev Point the hook at a role provider. Set once and only forward, so a
  ///      test cannot silently swap the account a resolved permit names.
  function setRoleProvider(IRoleProviderCalls provider) external {
    require(address(roleProvider) == address(0), "provider set");
    roleProvider = provider;
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
    // The manifest permits this call on deposit; making it is what gives the
    // honest path a non-empty resolved set to be checked against. The return
    // value is deliberately unused: this hook's own credential decision is
    // already made above, and consuming the provider's answer here would make
    // the hook's behaviour depend on a contract the gates treat as external.
    if (address(roleProvider) != address(0)) {
      roleProvider.validateCredential(lender, "");
    }
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
