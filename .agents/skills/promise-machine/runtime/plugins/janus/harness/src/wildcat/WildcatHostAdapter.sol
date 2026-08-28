// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {HostAdapter} from "../HostAdapter.sol";
import {WildcatHostModel, MockAsset} from "./WildcatHostModel.sol";

/// @dev The Wildcat host adapter. It drives the v2.5 market model's actions,
///      reads the value gate 2 conserves, and classifies addresses so a gate
///      can tell a call to a role provider from a call back into the host.
///      Every result is scoped to this adapter; passing its suite says nothing
///      about another host's callback model (gate 7).
contract WildcatHostAdapter is HostAdapter {
  enum Category {
    Hook,
    Host,
    Asset,
    RoleProvider,
    Unknown
  }

  WildcatHostModel public immutable model;
  MockAsset public immutable asset;
  address public immutable roleProvider;

  constructor(WildcatHostModel model_, MockAsset asset_, address roleProvider_) {
    model = model_;
    asset = asset_;
    roleProvider = roleProvider_;
  }

  function host() external view override returns (address) {
    return address(model);
  }

  function hook() external view override returns (address) {
    return model.hook();
  }

  function rollbackRule() external pure override returns (RollbackRule) {
    return RollbackRule.Full;
  }

  function valueSnapshot() external view override returns (uint256 total) {
    return asset.balanceOf(address(model));
  }

  function roles() external view override returns (address[] memory r) {
    r = new address[](1);
    r[0] = model.borrower();
  }

  function categoryOf(address account) external view returns (Category) {
    if (account == model.hook()) return Category.Hook;
    if (account == address(model)) return Category.Host;
    if (account == address(asset)) return Category.Asset;
    if (account == roleProvider) return Category.RoleProvider;
    return Category.Unknown;
  }

  function driveAction(
    string calldata action,
    address caller,
    bytes calldata params
  ) external override {
    bytes32 tag = keccak256(bytes(action));
    if (tag == keccak256("deposit")) {
      (address lender, uint256 amount, bytes memory extra) = abi.decode(
        params,
        (address, uint256, bytes)
      );
      model.deposit(lender, amount, extra);
    } else if (tag == keccak256("queueWithdrawal")) {
      (address lender, uint32 expiry, uint256 scaled, bytes memory extra) = abi.decode(
        params,
        (address, uint32, uint256, bytes)
      );
      model.queueWithdrawal(lender, expiry, scaled, extra);
    } else if (tag == keccak256("executeWithdrawal")) {
      (address lender, uint32 expiry) = abi.decode(params, (address, uint32));
      model.executeWithdrawal(lender, expiry);
    } else if (tag == keccak256("transfer")) {
      (address from, address to, uint256 scaled, bytes memory extra) = abi.decode(
        params,
        (address, address, uint256, bytes)
      );
      model.transfer(from, to, scaled, extra);
    } else if (tag == keccak256("setAnnualInterestAndReserveRatioBips")) {
      (uint16 apr, uint16 rr, bytes memory extra) = abi.decode(params, (uint16, uint16, bytes));
      model.setAnnualInterestAndReserveRatioBips(apr, rr, extra);
    } else {
      revert("unknown action");
    }
    caller; // caller identity is not needed by this host's modeled actions
  }
}
