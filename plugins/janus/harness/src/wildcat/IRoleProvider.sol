// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

/// @dev The two credential entry points the shipped manifest names as
///      permitted call targets on `roleProvider`: `getCredential`, declared a
///      `staticcall`, and `validateCredential`, declared a `call`.
///
///      It sits in its own file so the hook that makes these calls and the
///      provider that answers them can both declare it without depending on
///      each other. That is not a style preference. Declared inside either one,
///      the other would reach it through an unchecked cast, and an unchecked
///      cast is what S3-R3-01 recorded one step earlier: the shipped adapter
///      matched `AccountResolver` without declaring it, five test doubles did
///      declare it, and a signature drift therefore broke the doubles while
///      letting the production contract through to a run-time revert. A shared
///      file lets the compiler check both sides.
interface IRoleProviderCalls {
  function getCredential(address account) external view returns (uint32);

  function validateCredential(address account, bytes calldata data) external returns (uint32);
}
