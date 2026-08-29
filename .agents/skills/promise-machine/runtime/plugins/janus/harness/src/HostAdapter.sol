// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

/// @dev The seam between the Janus harness and one host. An adapter exposes a
///      host's actions, the value that must be conserved, and the economic
///      roles the gates watch, and it limits every result to that host. The
///      harness drives ordinary and hostile sequences through `driveAction`
///      and records the state delta around each call; the adapter does not
///      record anything itself.
abstract contract HostAdapter {
  /// @dev The host's declared behaviour on hook revert, host revert, and
  ///      partial batch failure. `Full` means the whole action rolls back.
  enum RollbackRule {
    Full,
    None
  }

  /// @dev The host contract the harness drives (for Wildcat, the market model).
  function host() external view virtual returns (address);

  /// @dev The hook installed on the host for this run.
  function hook() external view virtual returns (address);

  /// @dev The rollback rule the host declares, matched against the manifest.
  function rollbackRule() external view virtual returns (RollbackRule);

  /// @dev Perform one host action, the threshold the harness records around.
  ///      `action` is a manifest action name, `caller` is the address the
  ///      action runs as, and `params` is adapter-specific encoded arguments.
  ///      A revert bubbles unchanged so the harness can observe it.
  function driveAction(
    string calldata action,
    address caller,
    bytes calldata params
  ) external virtual;

  /// @dev A single comparable quantity standing for the value the host owes or
  ///      holds across its economic roles, read independently of any call's
  ///      return value. Gate 2 diffs this across a threshold.
  function valueSnapshot() external view virtual returns (uint256 total);

  /// @dev The economic roles whose balances the gates watch.
  function roles() external view virtual returns (address[] memory);

  /// @dev Resolve one manifest account symbol to a concrete address on this
  ///      host. This is the seam `ManifestReader` resolves through, and it is
  ///      the adapter's job rather than the reader's because only the host
  ///      knows which contract a name like `roleProvider` stands for.
  ///
  ///      `ok` is false for a name this adapter does not hold. A name it does
  ///      hold answers `ok` true and returns the address it has, including
  ///      `address(0)` when that name is present but unconfigured. The two
  ///      answers are kept apart on purpose: the reader raises
  ///      `UnresolvableSymbol` for the first and `SymbolResolvesToZero` for
  ///      the second, and collapsing them into one would make a name nobody
  ///      configured indistinguishable from a name nobody has ever heard of.
  ///
  ///      Resolution is by name, never by category. An adapter that answered
  ///      for a class of addresses would let a permit written for one symbol
  ///      admit every address sharing its kind, which is the widening the
  ///      manifest exists to prevent.
  function resolveAccount(
    string calldata name
  ) external view virtual returns (bool ok, address addr);
}
