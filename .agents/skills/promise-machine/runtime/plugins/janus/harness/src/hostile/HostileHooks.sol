// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IWildcatHook} from "../wildcat/IWildcatHook.sol";
import {WildcatHostModel} from "../wildcat/WildcatHostModel.sol";

/// @dev The five hostile reference hooks, one per failure class the gates own.
///      Each is a real, non-conformant hook that the matching gate must catch;
///      shipping one whose gate does not catch it would be a hole in the suite.
///      A no-op body is given for the callbacks a hook does not exercise.

/// @dev Gate 6: re-enters a different host action from its callback. The host's
///      global reentrancy guard blocks it, so the action reverts.
contract ReentryHook is IWildcatHook {
  function onDeposit(address lender, uint256, MarketState calldata, bytes calldata) external override {
    WildcatHostModel(msg.sender).queueWithdrawal(lender, uint32(1), 1, "");
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}
  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}
  function onSetAnnualInterestAndReserveRatioBips(uint16 a, uint16 r, MarketState calldata, bytes calldata)
    external pure override returns (uint16, uint16) { return (a, r); }
}

/// @dev Gate 5: consumes far more gas than the manifest budget by writing many
///      cold storage slots. The call succeeds, so only a gas gate catches it.
contract GasGriefHook is IWildcatHook {
  mapping(uint256 => uint256) private junk;

  function onDeposit(address, uint256, MarketState calldata, bytes calldata) external override {
    for (uint256 i; i < 400; ++i) {
      junk[i] = i + 1;
    }
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}
  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}
  function onSetAnnualInterestAndReserveRatioBips(uint16 a, uint16 r, MarketState calldata, bytes calldata)
    external pure override returns (uint16, uint16) { return (a, r); }
}

interface IAsset {
  function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/// @dev Gate 2: given an allowance it should never have, it pulls the host's
///      assets to itself while reporting success, so value conservation must be
///      checked from balances, not from the call's return.
contract ValueRedirectHook is IWildcatHook {
  IAsset public immutable asset;
  address public immutable market;
  uint256 public immutable amount;

  constructor(IAsset asset_, address market_, uint256 amount_) {
    asset = asset_;
    market = market_;
    amount = amount_;
  }

  function onDeposit(address, uint256, MarketState calldata, bytes calldata) external override {
    asset.transferFrom(market, address(this), amount);
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}
  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}
  function onSetAnnualInterestAndReserveRatioBips(uint16 a, uint16 r, MarketState calldata, bytes calldata)
    external pure override returns (uint16, uint16) { return (a, r); }
}

/// @dev A shared external contract a hook has no business touching.
contract ExternalRegistry {
  mapping(bytes32 => uint256) public value;

  function set(bytes32 key, uint256 val) external {
    value[key] = val;
  }
}

/// @dev Gate 1: mutates external state by calling a registry the manifest does
///      not list among permitted call targets.
contract StorageMutationHook is IWildcatHook {
  ExternalRegistry public immutable registry;

  constructor(ExternalRegistry registry_) {
    registry = registry_;
  }

  function onDeposit(address lender, uint256, MarketState calldata, bytes calldata) external override {
    registry.set(keccak256(abi.encode(lender)), 1);
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}
  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}
  function onSetAnnualInterestAndReserveRatioBips(uint16 a, uint16 r, MarketState calldata, bytes calldata)
    external pure override returns (uint16, uint16) { return (a, r); }
}

/// @dev Gate 3: an access hook with no monotone known-lender bit. It re-checks
///      the live credential on withdrawal, so once a credential lapses a lender
///      who deposited can no longer exit. The failure shows only on the exit
///      path, never on entry.
contract StaleAuthHook is IWildcatHook {
  error NotApprovedLender();

  mapping(address => bool) public approved;
  mapping(address => uint256) public credentialExpiry;

  function grant(address lender, uint256 expiry) external {
    approved[lender] = true;
    credentialExpiry[lender] = expiry;
  }

  function removeProvider(address lender) external {
    approved[lender] = false;
  }

  function _hasCredential(address lender) internal view returns (bool) {
    return approved[lender] && block.timestamp <= credentialExpiry[lender];
  }

  function onDeposit(address lender, uint256, MarketState calldata, bytes calldata) external view override {
    if (!_hasCredential(lender)) revert NotApprovedLender();
  }

  function onQueueWithdrawal(address lender, uint32, uint256, MarketState calldata, bytes calldata)
    external view override {
    // No monotone bit: a lapsed credential strands a lender who already
    // deposited. This is the liveness violation gate 3 exists to catch.
    if (!_hasCredential(lender)) revert NotApprovedLender();
  }

  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}
  function onSetAnnualInterestAndReserveRatioBips(uint16 a, uint16 r, MarketState calldata, bytes calldata)
    external pure override returns (uint16, uint16) { return (a, r); }
}
