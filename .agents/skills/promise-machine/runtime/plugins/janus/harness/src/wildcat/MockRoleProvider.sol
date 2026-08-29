// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IRoleProviderCalls} from "./IRoleProvider.sol";

/// @dev A stand-in for a Wildcat role provider, carrying only the two
///      credential entry points the shipped manifest names as permitted call
///      targets: `roleProvider.getCredential` and
///      `roleProvider.validateCredential`.
///
///      The split between them is the reason both are here rather than one.
///      `getCredential` reads and is declared `staticcall` in the manifest;
///      `validateCredential` may write and is declared `call`. A harness that
///      modelled only one of them could not tell a reader that folds the two
///      call kinds together from one that keeps them apart, which is the
///      distinction `ResolvedThreshold` carries two separate sets for.
///
///      It is deliberately not an access-control model. Credentials are set
///      directly by `grant`, with no admin, no expiry policy and no provider
///      registry, because this exists to be a call target with the right shape
///      and not to be the thing under test. `HonestAccessHook` holds the
///      credential behaviour the gates actually measure.
contract MockRoleProvider is IRoleProviderCalls {
  /// @dev Credential expiry per account, as a unix timestamp. Zero means no
  ///      credential, which is what an unknown account reads as.
  mapping(address => uint32) public expiryOf;

  /// @dev Counts calls to `validateCredential`, so a test can show the
  ///      state-changing entry point was actually reached rather than
  ///      inferring it from a return value the view path could also produce.
  uint256 public validations;

  function grant(address account, uint32 expiry) external {
    expiryOf[account] = expiry;
  }

  /// @dev The read path. Returns the stored expiry without touching state, so
  ///      it is reachable under `staticcall`.
  function getCredential(address account) external view override returns (uint32 timestamp) {
    return expiryOf[account];
  }

  /// @dev The write path. Returns the same expiry and records that it ran, so
  ///      it is not reachable under `staticcall` -- which is the property that
  ///      makes the manifest's two call kinds observably different.
  function validateCredential(
    address account,
    bytes calldata
  ) external override returns (uint32 timestamp) {
    validations++;
    return expiryOf[account];
  }
}
