// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";
import {JanusHarness} from "../src/JanusHarness.sol";
import {Vm} from "../src/Vm.sol";
import {WildcatHostModel, MockAsset} from "../src/wildcat/WildcatHostModel.sol";
import {WildcatHostAdapter} from "../src/wildcat/WildcatHostAdapter.sol";
import {MockRoleProvider} from "../src/wildcat/MockRoleProvider.sol";
import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";
import {
  ReentryHook,
  GasGriefHook,
  ValueRedirectHook,
  IAsset,
  ExternalRegistry,
  StorageMutationHook,
  StaleAuthHook
} from "../src/hostile/HostileHooks.sol";

contract HostileHooksTest is JanusBase, JanusHarness {
  string constant MANIFEST = "manifests/wildcat-open-term.json";

  MockAsset asset;
  WildcatHostModel model;
  MockRoleProvider provider;
  WildcatHostAdapter adapter;
  ManifestReader manifestReader;
  address lender = address(0xBEEF);

  function setUp() public {
    asset = new MockAsset();
    model = new WildcatHostModel(asset);
    provider = new MockRoleProvider();
    adapter = new WildcatHostAdapter(model, asset, address(provider));
    manifestReader = new ManifestReader();
    model.setBorrower(address(adapter));
    asset.mint(lender, 1_000_000);
    vm.prank(lender);
    asset.approve(address(model), type(uint256).max);
  }

  /// @dev The manifest's threshold for one action, resolved through the host
  ///      adapter. The hostile verdicts take their gate inputs from here for
  ///      the same reason the honest ones do: a hostile hook caught by a
  ///      hand-written set proves only that the literal was narrow enough, not
  ///      that the manifest was.
  function _threshold(string memory action) internal view returns (ResolvedThreshold memory) {
    return manifestReader.resolveFile(MANIFEST, action, AccountResolver(address(adapter)));
  }

  function _deposit(uint256 amount) internal returns (DriveResult memory) {
    return _drive(adapter, "deposit", lender, abi.encode(lender, amount, bytes("")));
  }

  function test_reentry_hook_caught_by_gate6() external {
    model.setHook(address(new ReentryHook()));
    DriveResult memory r = _deposit(100);
    assertTrue(r.reverted, "gate6: the re-entering deposit is blocked");
    assertEq(
      bytes4(r.revertData),
      WildcatHostModel.Reentrancy.selector,
      "gate6: blocked by the host reentrancy guard"
    );
  }

  function test_gas_grief_hook_caught_by_gate5() external {
    model.setHook(address(new GasGriefHook()));
    _deposit(100);
    uint256 budget = _threshold("deposit").gasBudget;
    assertTrue(
      model.lastHookGasUsed() > budget,
      "gate5: the hook consumed more than the manifest budget"
    );
  }

  /// @dev The budget gate 5 enforces is the driven action's own, and this is
  ///      what shows the selection is by name here rather than by position.
  ///      Every other resolution in this file asks for `deposit`, so a helper
  ///      that ignored its argument and always resolved `deposit` would change
  ///      no result -- which was true until this test existed. The manifest
  ///      gives two different budgets to compare: 2000000 on deposit and
  ///      1000000 on the rate-setting action.
  ///      It installs a hook first because resolution is all or nothing: the
  ///      deposit threshold's `permittedStorageWrites` are scope `hook`, so
  ///      reading its budget still resolves the `hook` symbol and a host with
  ///      no hook installed refuses with `SymbolResolvesToZero`. That is the
  ///      fail-closed posture working, not an obstacle to route around.
  function test_the_resolved_budget_is_the_actions_own_not_the_first() external {
    model.setHook(address(new ReentryHook()));
    uint256 deposit = _threshold("deposit").gasBudget;
    uint256 rates = _threshold("setAnnualInterestAndReserveRatioBips").gasBudget;
    assertEq(deposit, uint256(2000000), "deposit carries its own budget");
    assertEq(rates, uint256(1000000), "and the rate action carries a different one");
    assertTrue(deposit != rates, "so the two are not the same read");
  }

  function test_value_redirect_hook_caught_by_gate2() external {
    asset.mint(address(model), 500);
    ValueRedirectHook hook = new ValueRedirectHook(IAsset(address(asset)), address(model), 500);
    model.setHook(address(hook));
    vm.prank(address(model));
    asset.approve(address(hook), type(uint256).max);

    uint256 hookBefore = asset.balanceOf(address(hook));
    DriveResult memory r = _deposit(100);
    assertTrue(!r.reverted, "the redirecting deposit reports success");

    assertTrue(
      r.valueAfter != r.valueBefore + 100,
      "gate2: market value did not move by exactly the deposit"
    );
    assertTrue(asset.balanceOf(address(hook)) > hookBefore, "gate2: value moved to the hook");
  }

  function test_storage_mutation_hook_caught_by_gate1() external {
    ExternalRegistry registry = new ExternalRegistry();
    StorageMutationHook hook = new StorageMutationHook(registry);
    model.setHook(address(hook));

    DriveResult memory r = _deposit(100);
    assertTrue(!r.reverted, "the mutating deposit reports success");

    ResolvedThreshold memory t = _threshold("deposit");
    assertTrue(
      !_gate1_hookCallsWithinAllowed(r.delta, address(hook), t.allowedCallTargets),
      "gate1: the call to the external registry is caught against the manifest's own set"
    );

    // The registry's storage was written by the hook's subtree. The storage
    // scope check catches it independently of the call-target check: only the
    // hook's own storage is a permitted write scope here.
    // The manifest's deposit threshold permits hook-scope writes only, so the
    // resolved write set is the hook's own address, resolved through the
    // adapter rather than written here. The registry is not in it.
    model.setHook(address(hook)); // the resolved `hook` symbol is this hook
    ResolvedThreshold memory w = _threshold("deposit");
    assertEq(w.allowedWriteAccounts.length, 2, "both hook-scope writes resolved");
    assertEq(w.allowedWriteAccounts[0], address(hook), "and both name the hook itself");
    // Both assertions below read one local, so a set swapped in here is
    // swapped in both. Rejection alone does not say the resolved set was the
    // one used -- any set missing the registry rejects, including a wrong one
    // -- and the pair is what pins it: this exact set rejects, and this exact
    // set plus the registry accepts. A different set fails the second half.
    address[] memory scopes = w.allowedWriteAccounts;
    assertTrue(
      !_gate1_hookStorageWithinScopes(r.delta, address(hook), scopes),
      "gate1: the hook-caused write to external storage is caught"
    );

    address[] memory widened = new address[](scopes.length + 1);
    for (uint256 i; i < scopes.length; ++i) widened[i] = scopes[i];
    widened[scopes.length] = address(registry);
    assertTrue(
      _gate1_hookStorageWithinScopes(r.delta, address(hook), widened),
      "gate1: the registry is the only account the resolved scopes are missing"
    );
  }

  function test_stale_auth_hook_caught_by_gate3() external {
    StaleAuthHook hook = new StaleAuthHook();
    model.setHook(address(hook));
    hook.grant(lender, block.timestamp + 1000);

    DriveResult memory d = _deposit(100);
    assertTrue(!d.reverted, "the lender deposits while credentialled");

    vm.warp(block.timestamp + 5000);
    DriveResult memory q = _drive(
      adapter,
      "queueWithdrawal",
      lender,
      abi.encode(lender, uint32(1000), uint256(100), bytes(""))
    );
    assertTrue(q.reverted, "gate3: the lender is stranded on exit after the credential lapses");
    assertEq(
      bytes4(q.revertData),
      StaleAuthHook.NotApprovedLender.selector,
      "gate3: the exit is blocked by the stale credential check, not an unrelated revert"
    );
  }

  function test_run_emits_findings_and_requires_sequences() external {
    Finding[] memory findings = new Finding[](5);
    findings[0] = Finding(6, "deposit", "ReentryHook", "re-entered queueWithdrawal from onDeposit");
    findings[1] = Finding(5, "deposit", "GasGriefHook", "consumed gas beyond the manifest budget");
    findings[2] = Finding(2, "deposit", "ValueRedirectHook", "drained market assets while reporting success");
    findings[3] = Finding(1, "deposit", "StorageMutationHook", "called an external registry not in the manifest");
    findings[4] = Finding(3, "queueWithdrawal", "StaleAuthHook", "stranded a known lender after credential lapse");

    string memory path = "out/findings.test.json";
    _writeFindings(path, "wildcat-v2.5", "wildcat-open-term", 5, findings);

    string memory json = vm.readFile(path);
    assertEq(vm.parseJsonUint(json, ".sequences"), uint256(5), "findings record the sequence count");
    assertEq(vm.parseJsonUint(json, ".findings[3].gate"), uint256(1), "the storage-mutation finding is gate 1");

    vm.expectRevert(JanusHarness.NoSequencesExercised.selector);
    this.exerciseZero();
  }

  function exerciseZero() external pure {
    _requireExercised(0);
  }

  /// @dev A finding field that tries to inject JSON is escaped, so it cannot
  ///      rewrite or hide another field.
  function test_findings_json_escapes_injection() external {
    Finding[] memory findings = new Finding[](1);
    findings[0] = Finding(1, "deposit", "Evil", 'x","gate":9999,"hidden":"');

    string memory path = "out/findings.inject.json";
    _writeFindings(path, "wildcat-v2.5", "wildcat-open-term", 1, findings);
    string memory json = vm.readFile(path);

    // The gate is still 1; the injected 9999 did not override it.
    assertEq(vm.parseJsonUint(json, ".findings[0].gate"), uint256(1), "the injected gate did not take effect");
  }
}

/// @dev A handler that keeps the reentry hook in a stateful fuzz loop: every
///      driven deposit must be blocked by the host guard. If one ever landed,
///      the invariant would see it.
contract ReentryHandler {
  Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);
  WildcatHostModel public model;
  MockAsset public asset;
  address public lender = address(0xBEEF);
  bool public everLanded;
  bool public sawNonGuardRevert;

  constructor() {
    asset = new MockAsset();
    model = new WildcatHostModel(asset);
    model.setHook(address(new ReentryHook()));
    asset.mint(lender, type(uint128).max);
    vm.prank(lender);
    asset.approve(address(model), type(uint256).max);
  }

  function poke(uint256 amount) external {
    amount = (amount % 1000) + 1;
    try model.deposit(lender, amount, "") {
      everLanded = true;
    } catch (bytes memory data) {
      // The block must be the reentrancy guard. If the guard were removed, the
      // re-entering queueWithdrawal would revert for a different reason (a
      // balance underflow), which this flag would catch, so the invariant
      // genuinely exercises gate 6 rather than an incidental revert.
      if (bytes4(data) != WildcatHostModel.Reentrancy.selector) sawNonGuardRevert = true;
    }
  }
}

contract ReentryInvariantTest is JanusBase {
  ReentryHandler handler;

  function setUp() public {
    handler = new ReentryHandler();
  }

  /// @dev Restrict the invariant engine to the handler, so the fuzzer drives
  ///      only `poke` and cannot repoint the model's hook or mint through the
  ///      other deployed contracts.
  function targetContracts() public view returns (address[] memory addrs) {
    addrs = new address[](1);
    addrs[0] = address(handler);
  }

  function invariant_reentry_never_lands() external view {
    assertTrue(!handler.everLanded(), "a re-entering deposit was never allowed to land");
    assertTrue(
      !handler.sawNonGuardRevert(),
      "every blocked deposit was blocked by the reentrancy guard, so the invariant exercises gate 6"
    );
  }
}
