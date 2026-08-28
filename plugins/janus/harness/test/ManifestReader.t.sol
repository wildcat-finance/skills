// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";
import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";

/// @dev A stub adapter local to this test: a name table the tests fill. An
///      unset name reports `ok = false`, which is how a real adapter refuses
///      a symbol it does not know.
contract StubResolver is AccountResolver {
  mapping(bytes32 => address) private table;

  function set(string memory name, address addr) external {
    table[keccak256(bytes(name))] = addr;
  }

  function resolveAccount(string calldata name) external view returns (bool ok, address addr) {
    addr = table[keccak256(bytes(name))];
    ok = addr != address(0);
  }
}

/// @dev A stub adapter that claims to know every name but resolves each to
///      the zero address, for the zero-address refusal path.
contract ZeroResolver is AccountResolver {
  function resolveAccount(string calldata) external pure returns (bool ok, address addr) {
    return (true, address(0));
  }
}

/// @dev The manifest reader's contract: thresholds are selected by action
///      name, the symbol grammar is the text before the first `.`, staticcall
///      entries admit nothing state-changing, and everything unresolvable
///      fails closed. Exercised against the shipped wildcat-open-term.json
///      and inline manifest JSON.
contract ManifestReaderTest is JanusBase {
  string constant MANIFEST = "manifests/wildcat-open-term.json";

  address constant HOOK = address(0xA1);
  address constant HOST = address(0xA2);
  address constant ASSET = address(0xA3);
  address constant PROVIDER = address(0xA4);
  address constant EXTERNAL_ACCOUNT = address(0xA5);

  ManifestReader reader;
  StubResolver stub;

  function setUp() external {
    reader = new ManifestReader();
    stub = new StubResolver();
    stub.set("hook", HOOK);
    stub.set("host", HOST);
    stub.set("asset", ASSET);
    stub.set("roleProvider", PROVIDER);
    stub.set("someAccount", EXTERNAL_ACCOUNT);
  }

  // -- Threshold selection ---------------------------------------------------

  function test_threshold_is_selected_by_action_name_not_position() external view {
    // setAnnualInterestAndReserveRatioBips is the manifest's last threshold;
    // a positional [0] read would see deposit's shape instead.
    ResolvedThreshold memory t = reader.resolveFile(
      MANIFEST,
      "setAnnualInterestAndReserveRatioBips",
      stub
    );
    assertEq(t.gasBudget, 1_000_000, "the rate threshold's own budget, not deposit's");
    assertEq(t.allowedCallTargets.length, 0, "the rate threshold permits no calls");
    assertEq(t.allowedWriteAccounts.length, 1, "the rate threshold permits one write scope");
    assertEq(t.allowedWriteAccounts[0], HOOK, "the hook-scope write resolves to the hook");
  }

  function test_gas_budget_is_the_named_actions_own() external view {
    ResolvedThreshold memory deposit = reader.resolveFile(MANIFEST, "deposit", stub);
    ResolvedThreshold memory rate = reader.resolveFile(
      MANIFEST,
      "setAnnualInterestAndReserveRatioBips",
      stub
    );
    assertEq(deposit.gasBudget, 2_000_000, "deposit carries its declared budget");
    assertEq(rate.gasBudget, 1_000_000, "the rate action carries its own, different budget");
  }

  function test_missing_action_reverts() external {
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.ActionNotInManifest.selector, "borrow"));
    reader.resolveFile(MANIFEST, "borrow", stub);
  }

  // -- Symbol grammar ----------------------------------------------------------

  function test_account_symbol_is_the_text_before_the_first_dot() external view {
    // deposit permits roleProvider.getCredential (staticcall) and
    // roleProvider.validateCredential (call); the call entry's symbol is
    // roleProvider and the function suffix is documentation.
    ResolvedThreshold memory t = reader.resolveFile(MANIFEST, "deposit", stub);
    assertEq(t.allowedCallTargets.length, 1, "one state-changing call entry on deposit");
    assertEq(t.allowedCallTargets[0], PROVIDER, "the symbol before the dot resolves");
  }

  function test_target_without_a_dot_is_its_own_symbol() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider","kind":"call"}]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedCallTargets.length, 1, "the dotless target is admitted");
    assertEq(t.allowedCallTargets[0], PROVIDER, "the whole dotless target is the symbol");
  }

  // -- Scope resolution --------------------------------------------------------

  function test_scope_hook_and_host_resolve_through_the_adapter() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[{"scope":"hook","slot":"lenderStatus[lender]"},'
      '{"scope":"host","slot":"state.scaledTotalSupply"}],'
      '"permittedCalls":[],"permittedValueMovements":[]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedWriteAccounts.length, 2, "both write scopes resolve");
    assertEq(t.allowedWriteAccounts[0], HOOK, "scope hook resolves to the adapter's hook");
    assertEq(t.allowedWriteAccounts[1], HOST, "scope host resolves to the adapter's host");
  }

  function test_scope_external_resolves_its_slot_prefix() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[{"scope":"external","slot":"someAccount.counter[market]"}],'
      '"permittedCalls":[],"permittedValueMovements":[]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedWriteAccounts.length, 1, "the external write resolves");
    assertEq(t.allowedWriteAccounts[0], EXTERNAL_ACCOUNT, "the slot's symbol prefix resolves");
  }

  function test_value_movements_resolve_to_address_pairs() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedCalls":[],'
      '"permittedValueMovements":[{"asset":"asset","recipient":"host"}]}]}',
      "deposit",
      stub
    );
    assertEq(t.valueAssets.length, 1, "one movement pair");
    assertEq(t.valueRecipients.length, 1, "pairs stay pairwise");
    assertEq(t.valueAssets[0], ASSET, "the asset symbol resolves");
    assertEq(t.valueRecipients[0], HOST, "the recipient symbol resolves");
  }

  // -- The staticcall reading ---------------------------------------------------

  function test_staticcall_entry_admits_nothing_state_changing() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider.getCredential","kind":"staticcall"}]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedCallTargets.length, 0, "a staticcall entry admits no state-changing call");
  }

  function test_staticcall_entry_symbol_must_still_resolve() external {
    // Fail-closed uniformity: a misnamed staticcall entry aborts rather than
    // being skipped silently.
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.UnresolvableSymbol.selector, "misnamed")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"misnamed.getCredential","kind":"staticcall"}]}]}',
      "deposit",
      stub
    );
  }

  // -- Fail-closed resolution -----------------------------------------------------

  function test_unresolvable_symbol_reverts() external {
    StubResolver empty = new StubResolver();
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.UnresolvableSymbol.selector, "roleProvider")
    );
    reader.resolveFile(MANIFEST, "deposit", empty);
  }

  function test_zero_address_resolution_reverts() external {
    ZeroResolver zero = new ZeroResolver();
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.SymbolResolvesToZero.selector, "roleProvider")
    );
    reader.resolveFile(MANIFEST, "deposit", zero);
  }
}
