// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";
import {JanusHarness} from "../src/JanusHarness.sol";
import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";
import {WildcatHostModel, MockAsset} from "../src/wildcat/WildcatHostModel.sol";
import {HonestAccessHook} from "../src/wildcat/HonestAccessHook.sol";
import {WildcatHostAdapter} from "../src/wildcat/WildcatHostAdapter.sol";
import {MockRoleProvider} from "../src/wildcat/MockRoleProvider.sol";

/// @dev The disagreement this run exists to pin: a hook whose behaviour is
///      fixed, judged against two manifests that differ in one entry, giving
///      two different verdicts. Steps 2 to 4 built the machinery; this asserts
///      that the machinery answers to the manifest and not to anything else.
///
///      Three claims, and they are separable on purpose. The refusal shows an
///      omitted entry is caught. The permit shows the same hook against the
///      shipped manifest is admitted, which is what stops the refusal being
///      explained by the hook simply failing everything. The fail-closed abort
///      shows an unresolvable symbol stops the run rather than quietly
///      producing a smaller set, which is the direction a gate cannot catch
///      because a permit that never existed rejects everything.
contract ManifestDisagreementTest is JanusBase, JanusHarness {
  string constant SHIPPED = "manifests/wildcat-open-term.json";
  string constant OMITTED = "manifests/fixtures/wildcat-open-term-omitted-call.json";
  string constant UNKNOWN = "manifests/fixtures/wildcat-open-term-unknown-symbol.json";

  MockAsset asset;
  WildcatHostModel model;
  HonestAccessHook honest;
  MockRoleProvider provider;
  WildcatHostAdapter adapter;
  ManifestReader manifestReader;
  address lender = address(0xBEEF);

  function setUp() public {
    asset = new MockAsset();
    model = new WildcatHostModel(asset);
    honest = new HonestAccessHook();
    provider = new MockRoleProvider();
    adapter = new WildcatHostAdapter(model, asset, address(provider));
    manifestReader = new ManifestReader();
    model.setBorrower(address(adapter));
    model.setHook(address(honest));
    honest.setRoleProvider(provider);

    asset.mint(lender, 1_000_000);
    vm.prank(lender);
    asset.approve(address(model), type(uint256).max);
    honest.grant(lender, block.timestamp + 1000);
  }

  function _resolve(
    string memory manifest,
    string memory action
  ) internal view returns (ResolvedThreshold memory) {
    return manifestReader.resolveFile(manifest, action, AccountResolver(address(adapter)));
  }

  /// @dev One deposit, driven once, judged twice. The hook is identical in both
  ///      verdicts and so is the recorded delta; the only thing that differs is
  ///      which file the permitted set came from.
  function _honestDeposit() internal returns (DriveResult memory r) {
    r = _drive(adapter, "deposit", lender, abi.encode(lender, uint256(100), bytes("")));
    assertTrue(!r.reverted, "the deposit itself succeeds under either manifest");
    assertEq(uint256(provider.validations()), 1, "and the hook made the provider call");
  }

  // ------------------------------- Refusal -------------------------------- //

  /// @dev The refusal. `wildcat-open-term-omitted-call.json` is the shipped
  ///      manifest with one entry removed: deposit no longer permits
  ///      `roleProvider.validateCredential`. The hook still makes that call, so
  ///      gate 1 catches it.
  ///
  ///      The fixture is valid under the schema, checked by
  ///      `janus.py validate`, so the refusal comes from the gate rather than
  ///      from a malformed file the reader could not parse. It keeps the
  ///      `staticcall` entry, so the difference between the two manifests is
  ///      one permitted state-changing call and nothing else.
  function test_an_omitted_call_entry_is_refused() external {
    DriveResult memory r = _honestDeposit();

    ResolvedThreshold memory omitted = _resolve(OMITTED, "deposit");
    assertEq(omitted.allowedCallTargets.length, 0, "the fixture permits no state-changing call");

    assertTrue(
      !_gate1_hookCallsWithinAllowed(r.delta, address(honest), omitted.allowedCallTargets),
      "gate1: the provider call is not permitted by this manifest"
    );
  }

  // -------------------------------- Permit -------------------------------- //

  /// @dev The permit, and the half that makes the refusal mean something. The
  ///      same hook, the same delta, judged against the shipped manifest, is
  ///      admitted. Without this the refusal above would be equally consistent
  ///      with a gate that rejects everything.
  function test_the_declared_call_entry_is_admitted() external {
    DriveResult memory r = _honestDeposit();

    ResolvedThreshold memory shipped = _resolve(SHIPPED, "deposit");
    assertEq(shipped.allowedCallTargets.length, 1, "the shipped manifest permits one call");
    assertEq(shipped.allowedCallTargets[0], address(provider), "and it is the role provider");

    assertTrue(
      _gate1_hookCallsWithinAllowed(r.delta, address(honest), shipped.allowedCallTargets),
      "gate1: the same call is permitted by the shipped manifest"
    );
  }

  /// @dev The two verdicts stated as one disagreement, so the pair cannot drift
  ///      apart into two tests that happen to pass for unrelated reasons. One
  ///      delta, two manifests, opposite answers.
  function test_one_delta_two_manifests_two_verdicts() external {
    DriveResult memory r = _honestDeposit();

    bool underShipped = _gate1_hookCallsWithinAllowed(
      r.delta,
      address(honest),
      _resolve(SHIPPED, "deposit").allowedCallTargets
    );
    bool underOmitted = _gate1_hookCallsWithinAllowed(
      r.delta,
      address(honest),
      _resolve(OMITTED, "deposit").allowedCallTargets
    );

    assertTrue(underShipped, "admitted where the entry is declared");
    assertTrue(!underOmitted, "refused where it is omitted");
    assertTrue(underShipped != underOmitted, "so the manifest is what decides");
  }

  // ------------------------------ Fail-closed ----------------------------- //

  /// @dev The fail-closed abort, and the direction no gate can report. A
  ///      manifest naming a symbol the adapter cannot resolve does not yield a
  ///      smaller permitted set: resolution reverts with the reader's own named
  ///      error and the run stops.
  ///
  ///      A silently shrunken set is the dangerous outcome rather than the
  ///      merely wrong one, because a permit that never existed rejects
  ///      everything, so a gate reading it would report a pass for a hook doing
  ///      nothing and a catch for a hook doing anything, and neither verdict
  ///      would be about the manifest the author wrote.
  function test_an_unresolvable_symbol_aborts_rather_than_shrinking_the_set() external {
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.UnresolvableSymbol.selector, "treasury")
    );
    manifestReader.resolveFile(UNKNOWN, "deposit", AccountResolver(address(adapter)));
  }

  /// @dev And the fixture is otherwise a manifest this adapter resolves, so the
  ///      abort above is attributable to the one unknown symbol rather than to
  ///      the file being unusable. Its other actions resolve.
  function test_the_unknown_symbol_fixture_resolves_its_other_actions() external view {
    ResolvedThreshold memory rates = _resolve(UNKNOWN, "setAnnualInterestAndReserveRatioBips");
    assertEq(rates.gasBudget, uint256(1000000), "the rest of the fixture is a working manifest");
    assertEq(rates.allowedCallTargets.length, 0, "and that action permits no calls");
  }
}
