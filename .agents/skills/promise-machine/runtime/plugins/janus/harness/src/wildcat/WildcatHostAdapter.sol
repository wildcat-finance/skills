// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {HostAdapter} from "../HostAdapter.sol";
import {AccountResolver} from "../ManifestReader.sol";
import {WildcatHostModel, MockAsset} from "./WildcatHostModel.sol";

/// @dev The Wildcat host adapter. It drives the v2.5 market model's actions,
///      reads the value gate 2 conserves, and classifies addresses so a gate
///      can tell a call to a role provider from a call back into the host.
///      Every result is scoped to this adapter; passing its suite says nothing
///      about another host's callback model (gate 7).
contract WildcatHostAdapter is HostAdapter, AccountResolver {
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

  /// @dev The name table `ManifestReader` resolves through. Four names, each
  ///      answering with exactly the address this adapter holds for it.
  ///
  ///      It mirrors `categoryOf` and runs in the opposite direction, and the
  ///      asymmetry between them is deliberate. `categoryOf` maps an address
  ///      to a kind, which is a many-to-one question; this maps a name to one
  ///      address. Building this out of `categoryOf` -- answering `asset` for
  ///      anything classified `Asset`, say -- would let a permit the manifest
  ///      wrote for one symbol admit every address sharing its category, and
  ///      widening a permit by category is the failure this table exists to
  ///      avoid. So `host` and `asset` never enter a set written for `hook`,
  ///      and no name resolves to more than the one address it names.
  ///
  ///      `roleProvider` answers `ok` true even when it holds `address(0)`,
  ///      because this adapter does have that name; it is the configuration
  ///      that is missing, not the name. The reader then raises
  ///      `SymbolResolvesToZero` rather than `UnresolvableSymbol`, and the two
  ///      stay distinguishable. `WildcatConformance.t.sol` constructs this
  ///      adapter with a zero role provider today, so that path is reachable
  ///      in the suite rather than hypothetical.
  ///
  ///      An unknown name answers `(false, address(0))`. Nothing is guessed
  ///      from the string and no prefix or suffix is stripped here: the reader
  ///      owns the symbol grammar and hands this table a finished symbol.
  ///
  ///      The contract declares `AccountResolver` rather than merely happening
  ///      to match it. Without the declaration this adapter satisfied the
  ///      interface by convention and the compiler had nothing to check, which
  ///      put the protection exactly the wrong way round: every stub resolver
  ///      in the tests declares the interface and would fail to compile on a
  ///      signature drift, while the one resolver that ships would compile
  ///      through it and revert at run time on every call the reader made.
  function resolveAccount(
    string calldata name
  ) external view override(HostAdapter, AccountResolver) returns (bool ok, address addr) {
    bytes32 tag = keccak256(bytes(name));
    if (tag == keccak256("hook")) return (true, model.hook());
    if (tag == keccak256("host")) return (true, address(model));
    if (tag == keccak256("asset")) return (true, address(asset));
    if (tag == keccak256("roleProvider")) return (true, roleProvider);
    return (false, address(0));
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
