// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";
import {JanusHarness} from "../src/JanusHarness.sol";
import {IWildcatHook} from "../src/wildcat/IWildcatHook.sol";
import {WildcatHostModel, MockAsset} from "../src/wildcat/WildcatHostModel.sol";
import {HonestAccessHook} from "../src/wildcat/HonestAccessHook.sol";
import {WildcatHostAdapter} from "../src/wildcat/WildcatHostAdapter.sol";

/// @dev A hook that reverts on deposit with a custom error, to prove the model
///      bubbles the exact revert bytes and rolls the action back (gate 4).
contract RevertingProbe is IWildcatHook {
  error Refused();

  function onDeposit(address, uint256, MarketState calldata, bytes calldata) external pure override {
    revert Refused();
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}

  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}

  function onSetAnnualInterestAndReserveRatioBips(
    uint16 a,
    uint16 r,
    MarketState calldata,
    bytes calldata
  ) external pure override returns (uint16, uint16) {
    return (a, r);
  }
}

/// @dev A hook whose value-returning callback returns only 32 bytes, to prove
///      the model enforces the >=0x40 return contract.
contract ShortReturnProbe is IWildcatHook {
  function onDeposit(address, uint256, MarketState calldata, bytes calldata) external override {}

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}

  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}

  function onSetAnnualInterestAndReserveRatioBips(
    uint16,
    uint16,
    MarketState calldata,
    bytes calldata
  ) external pure override returns (uint16, uint16) {
    assembly {
      return(0, 0x20)
    }
  }
}

/// @dev A hook that re-enters a different host action from its deposit
///      callback, to prove the model's global guard blocks cross-action
///      re-entry (gate 6).
contract ReentryProbe is IWildcatHook {
  function onDeposit(address lender, uint256, MarketState calldata, bytes calldata) external override {
    WildcatHostModel(msg.sender).queueWithdrawal(lender, uint32(1), 1, "");
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}

  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}

  function onSetAnnualInterestAndReserveRatioBips(
    uint16 a,
    uint16 r,
    MarketState calldata,
    bytes calldata
  ) external pure override returns (uint16, uint16) {
    return (a, r);
  }
}

/// @dev A neutral call sink and a one-hop forwarder, to build a laundering
///      path the hook routes a forbidden call through.
contract Sink {
  function ping() external {}
}

contract Forwarder {
  function forward(address sink) external {
    Sink(sink).ping();
  }
}

/// @dev A hook that, on deposit, calls an allowed forwarder which calls a
///      forbidden sink. Its direct callee is permitted, so only causal-subtree
///      attribution catches the laundered call.
contract LaunderProbe is IWildcatHook {
  address immutable fwd;
  address immutable sink;

  constructor(address fwd_, address sink_) {
    fwd = fwd_;
    sink = sink_;
  }

  function onDeposit(address, uint256, MarketState calldata, bytes calldata) external override {
    Forwarder(fwd).forward(sink);
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}

  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}

  function onSetAnnualInterestAndReserveRatioBips(
    uint16 a,
    uint16 r,
    MarketState calldata,
    bytes calldata
  ) external pure override returns (uint16, uint16) {
    return (a, r);
  }
}

/// @dev A benign hook that reads host state through a staticcall on deposit. A
///      read is not an effect, so gate 1 must not reject it even though the
///      host is not in the permitted call set.
contract HostReadHook is IWildcatHook {
  uint256 public seen;

  function onDeposit(address, uint256, MarketState calldata, bytes calldata) external override {
    seen = WildcatHostModel(msg.sender).scaledTotalSupply();
  }

  function onQueueWithdrawal(address, uint32, uint256, MarketState calldata, bytes calldata) external override {}
  function onTransfer(address, address, address, uint256, MarketState calldata, bytes calldata) external override {}
  function onSetAnnualInterestAndReserveRatioBips(uint16 a, uint16 r, MarketState calldata, bytes calldata)
    external pure override returns (uint16, uint16) { return (a, r); }
}

contract WildcatConformanceTest is JanusBase, JanusHarness {
  string constant MANIFEST = "manifests/wildcat-open-term.json";

  MockAsset asset;
  WildcatHostModel model;
  HonestAccessHook honest;
  WildcatHostAdapter adapter;
  address lender = address(0xBEEF);

  function setUp() public {
    asset = new MockAsset();
    model = new WildcatHostModel(asset);
    honest = new HonestAccessHook();
    adapter = new WildcatHostAdapter(model, asset, address(0));
    model.setBorrower(address(adapter));
    model.setHook(address(honest));

    asset.mint(lender, 1_000_000);
    vm.prank(lender);
    asset.approve(address(model), type(uint256).max);
    honest.grant(lender, block.timestamp + 1000);
  }

  function _depositParams(uint256 amount) internal view returns (bytes memory) {
    return abi.encode(lender, amount, bytes(""));
  }

  // ----------------------------- Honest gates ---------------------------- //

  function test_gate1_and_gate2_honest_deposit() external {
    uint256 hookAssetBefore = asset.balanceOf(address(honest));
    DriveResult memory r = _drive(adapter, "deposit", lender, _depositParams(100));
    assertTrue(!r.reverted, "honest deposit does not revert");

    assertTrue(_deltaHasEffects(r.delta), "the drive produced observable effects, so the gate is not vacuous");

    address[] memory allowed = new address[](0); // the honest hook calls nothing
    assertTrue(
      _gate1_hookCallsWithinAllowed(r.delta, address(honest), allowed),
      "gate1: the hook made no call outside the permitted set"
    );

    assertEq(_hookValueMoved(r.delta, address(honest)), uint256(0), "gate2: the hook moved no value");
    assertEq(asset.balanceOf(address(honest)), hookAssetBefore, "gate2: the hook's asset balance is unchanged");
    assertEq(r.valueAfter - r.valueBefore, uint256(100), "gate2: market value rose by exactly the deposit");
  }

  function test_gate5_honest_hook_within_manifest_gas_budget() external {
    _drive(adapter, "deposit", lender, _depositParams(100));
    uint256 budget = vm.parseJsonUint(vm.readFile(MANIFEST), ".thresholds[0].gasBudget");
    assertTrue(model.lastHookGasUsed() <= budget, "gate5: the hook stayed within the manifest budget");
    assertTrue(model.lastHookGasUsed() > 0, "gate5: a real hook gas figure was recorded");
  }

  function test_gate3_exit_liveness_after_lapse_and_provider_removal() external {
    // The lender deposits and becomes a known lender.
    DriveResult memory d = _drive(adapter, "deposit", lender, _depositParams(100));
    assertTrue(!d.reverted, "deposit succeeds while credentialled");

    // The credential lapses and the provider is removed.
    vm.warp(block.timestamp + 5000);
    honest.removeProvider(lender);

    // The exit stays open: queue then execute both succeed.
    DriveResult memory q = _drive(
      adapter,
      "queueWithdrawal",
      lender,
      abi.encode(lender, uint32(1000), uint256(100), bytes(""))
    );
    assertTrue(!q.reverted, "gate3: a known lender queues after lapse and provider removal");

    DriveResult memory e = _drive(adapter, "executeWithdrawal", lender, abi.encode(lender, uint32(1000)));
    assertTrue(!e.reverted, "gate3: the queued withdrawal executes");
    assertEq(asset.balanceOf(lender), uint256(1_000_000), "gate3: the lender recovered its assets");
  }

  function test_gate1_catches_a_call_laundered_through_an_allowed_forwarder() external {
    Sink sink = new Sink();
    Forwarder fwd = new Forwarder();
    LaunderProbe probe = new LaunderProbe(address(fwd), address(sink));
    model.setHook(address(probe));

    DriveResult memory r = _drive(adapter, "deposit", lender, _depositParams(100));
    assertTrue(!r.reverted, "the laundering deposit itself does not revert");

    // The forwarder is permitted; the sink it calls is not. Immediate-accessor
    // attribution would miss the sink call; the causal subtree catches it.
    address[] memory allowed = new address[](1);
    allowed[0] = address(fwd);
    assertTrue(
      !_gate1_hookCallsWithinAllowed(r.delta, address(probe), allowed),
      "gate1: a forbidden call laundered one hop through an allowed target is caught"
    );
  }

  function test_gate1_does_not_reject_a_host_read() external {
    // A hook that reads host state via a staticcall makes no effect. Gate 1
    // must pass it even with an empty permitted-call set: reads are not
    // enumerated effects, and the host is not swept in as a laundering relay.
    HostReadHook reader = new HostReadHook();
    model.setHook(address(reader));
    honest.grant(lender, block.timestamp + 1000); // not used by the reader, harmless

    DriveResult memory r = _drive(adapter, "deposit", lender, _depositParams(100));
    assertTrue(!r.reverted, "the host-reading deposit succeeds");

    address[] memory allowed = new address[](0);
    assertTrue(
      _gate1_hookCallsWithinAllowed(r.delta, address(reader), allowed),
      "gate1: a staticcall read of host state is not a forbidden effect"
    );
  }

  function test_gate7_adapter_names_its_scope() external view {
    // Passing this suite is scoped to this adapter's host; the adapter is the
    // thing every result is limited to.
    assertEq(adapter.host(), address(model), "gate7: the adapter names the host it speaks for");
    assertEq(adapter.hook(), address(honest), "gate7: the adapter names the hook under test");
  }

  // ------------------------------- Fidelity ------------------------------ //

  function test_fidelity_hook_revert_bubbles_and_rolls_back() external {
    RevertingProbe probe = new RevertingProbe();
    model.setHook(address(probe));

    uint256 lenderBefore = asset.balanceOf(lender);
    DriveResult memory r = _drive(adapter, "deposit", lender, _depositParams(100));

    assertTrue(r.reverted, "gate4: a hook revert reverts the action");
    assertEq(bytes4(r.revertData), RevertingProbe.Refused.selector, "gate4: the exact revert bytes bubble");
    // Full rollback: neither market value nor lender balance moved.
    assertEq(r.valueAfter, r.valueBefore, "gate4: market value fully rolled back");
    assertEq(asset.balanceOf(lender), lenderBefore, "gate4: lender balance fully rolled back");
  }

  function test_fidelity_value_return_shorter_than_0x40_reverts() external {
    ShortReturnProbe probe = new ShortReturnProbe();
    model.setHook(address(probe));

    DriveResult memory r = _drive(
      adapter,
      "setAnnualInterestAndReserveRatioBips",
      address(adapter),
      abi.encode(uint16(500), uint16(3000), bytes(""))
    );
    assertTrue(r.reverted, "fidelity: a return shorter than 0x40 bytes reverts, as the market requires");
  }

  function test_fidelity_reentry_into_another_action_is_blocked() external {
    ReentryProbe probe = new ReentryProbe();
    model.setHook(address(probe));

    DriveResult memory r = _drive(adapter, "deposit", lender, _depositParams(100));
    assertTrue(r.reverted, "gate6: a callback re-entering another action is blocked by the host guard");
    assertEq(
      bytes4(r.revertData),
      WildcatHostModel.Reentrancy.selector,
      "gate6: the block is the reentrancy guard, bubbled through the hook call"
    );
  }
}
