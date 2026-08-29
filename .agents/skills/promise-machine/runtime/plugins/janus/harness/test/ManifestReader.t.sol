// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";
import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";
import {ManifestFuzz} from "../adapters/ManifestFuzz.sol";

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

/// @dev A stub adapter that answers to every name, including the empty one,
///      with a live address. It exists so the empty-symbol and staticcall
///      refusals are shown to be the reader's own, not something the reader
///      is delegating to a well-behaved adapter.
contract OmniResolver is AccountResolver {
  address public constant ANY = address(0xBEEF);

  function resolveAccount(string calldata) external pure returns (bool ok, address addr) {
    return (true, ANY);
  }
}

/// @dev A stub adapter that knows `USDC` at a live address and answers for
///      `USDC.e` with `(true, address(0))` -- the one answer shape the round 3
///      ambiguity guard read as an absence. It is not a contrived shape: it is
///      what `ZeroResolver` here and `ghost` in the fuzz suite both model, and
///      the reader raises `SymbolResolvesToZero` for it everywhere else.
contract KnowsTheWholeNameAsZero is AccountResolver {
  function resolveAccount(string calldata n) external pure returns (bool, address) {
    if (keccak256(bytes(n)) == keccak256("USDC.e")) return (true, address(0));
    if (keccak256(bytes(n)) == keccak256("USDC")) return (true, address(0xC0));
    if (keccak256(bytes(n)) == keccak256("hook")) return (true, address(0xA1));
    return (false, address(0));
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

  // -- Guards added by the step 2 round 1 audit ----------------------------

  /// @dev S2-R1-01. A `call` permit must not stand in for a `delegatecall`
  ///      permit: a delegatecall runs the target's code in the hook's own
  ///      storage context, so folding the two kinds into one address set
  ///      would grant the target the hook's entire state. Without the split
  ///      this fails, because roleProvider appears in the delegate set.
  function test_call_permit_does_not_admit_a_delegatecall() external view {
    ResolvedThreshold memory t = reader.resolveFile(MANIFEST, "deposit", stub);
    assertEq(t.allowedCallTargets.length, 1, "the call entry is admitted as a call");
    assertEq(t.allowedCallTargets[0], PROVIDER, "and resolves to the provider");
    assertEq(t.allowedDelegateTargets.length, 0, "no delegatecall was permitted, so none is admitted");
  }

  /// @dev S2-R1-01, the mirror: a `delegatecall` permit must not admit a
  ///      plain call either. The two sets are disjoint in both directions.
  function test_delegatecall_permit_does_not_admit_a_plain_call() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider","kind":"delegatecall"}]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedDelegateTargets.length, 1, "the delegatecall entry is admitted as one");
    assertEq(t.allowedDelegateTargets[0], PROVIDER, "and resolves to the provider");
    assertEq(t.allowedCallTargets.length, 0, "no plain call was permitted, so none is admitted");
  }

  /// @dev S2-R1-01. A staticcall entry still admits nothing to either set.
  function test_staticcall_admits_nothing_to_either_call_set() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider.getCredential","kind":"staticcall"}]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedCallTargets.length, 0, "staticcall admits no plain call");
    assertEq(t.allowedDelegateTargets.length, 0, "staticcall admits no delegatecall");
  }

  /// @dev S2-R1-02. A manifest that names one action twice has no single
  ///      answer. Selection is by name, so letting array position decide
  ///      which of two same-named thresholds wins would reintroduce exactly
  ///      the positional dependence `_thresholdByAction` exists to remove.
  ///      Without the fix this fails: the first, permissive entry is returned.
  function test_duplicate_action_name_reverts() external {
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.DuplicateActionInManifest.selector, "deposit")
    );
    reader.resolveJson(
      '{"thresholds":['
      '{"action":"deposit","gasBudget":30000000,"permittedStorageWrites":[],'
      '"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider","kind":"call"}]},'
      '{"action":"deposit","gasBudget":1,"permittedStorageWrites":[],'
      '"permittedValueMovements":[],"permittedCalls":[]}]}',
      "deposit",
      stub
    );
  }

  /// @dev S2-R1-03. A target whose first character is `.` has an empty
  ///      account symbol. The reader owns its symbol grammar, so it refuses
  ///      rather than asking the adapter about the empty name. Driven with an
  ///      adapter that answers to every name including the empty one, so
  ///      without the fix this fails by admitting 0xBEEF.
  function test_empty_account_symbol_reverts() external {
    OmniResolver omni = new OmniResolver();
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, ""));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":".getCredential","kind":"call"}]}]}',
      "deposit",
      omni
    );
  }

  /// @dev S2-R1-03, the storage path: an `external` scope whose slot string
  ///      begins with `.` has the same empty symbol and refuses the same way.
  function test_empty_symbol_in_an_external_slot_reverts() external {
    OmniResolver omni = new OmniResolver();
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, ""));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[{"scope":"external","slot":".counter[market]"}],'
      '"permittedValueMovements":[],"permittedCalls":[]}]}',
      "deposit",
      omni
    );
  }

  // -- Guards added by the step 2 round 2 audit -----------------------------

  /// @dev S2-R2-03. The round 1 guard refused only the zero-length symbol, so
  ///      a target of ` ` or ` .field` still reached the adapter as a name.
  ///      That is the same class the guard was installed to close: neither is
  ///      a name the manifest author wrote, and an adapter that trims before
  ///      looking a name up admits it. Driven with an adapter that answers to
  ///      every name, so without the fix this admits 0xBEEF.
  function test_whitespace_only_symbol_reverts() external {
    OmniResolver omni = new OmniResolver();
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, " "));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":" ","kind":"call"}]}]}',
      "deposit",
      omni
    );
  }

  /// @dev S2-R2-03, the leading-whitespace shape: ` .getCredential` splits at
  ///      the dot into the symbol ` `, which is blank for the same reason.
  function test_whitespace_before_the_dot_reverts() external {
    OmniResolver omni = new OmniResolver();
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, " "));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":" .getCredential","kind":"call"}]}]}',
      "deposit",
      omni
    );
  }

  /// @dev S2-R2-03, the storage path, and a tab rather than a space so the
  ///      guard is shown to be about whitespace and not about one byte. The
  ///      slot carries the two characters `\` and `t`, which is how a tab is
  ///      written inside a JSON string; the parser hands the reader a real
  ///      tab.
  function test_tab_only_symbol_in_an_external_slot_reverts() external {
    OmniResolver omni = new OmniResolver();
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, "\t"));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[{"scope":"external","slot":"\\t.counter[market]"}],'
      '"permittedValueMovements":[],"permittedCalls":[]}]}',
      "deposit",
      omni
    );
  }

  /// @dev S2-R2-05. Enumerating four whitespace bytes was not enough: a
  ///      vertical tab, a form feed and a NUL are all writable into a manifest
  ///      as JSON escapes, none is a name, and each reached the adapter under
  ///      the narrower test. The guard now refuses every byte at or below
  ///      ASCII space.
  function test_control_byte_only_symbols_revert() external {
    OmniResolver omni = new OmniResolver();
    // Named, not bare. A bare `expectRevert` here accepted any refusal, so it
    // stopped distinguishing the blank guard from every other guard the reader
    // grew afterwards: narrowing `_isBlank` back to four whitespace bytes left
    // this test green because the dotted names below refuse for a different
    // reason. The escape and the byte it decodes to are both named.
    string[3] memory escapes = ["\\u000b", "\\u000c", "\\u0000"];
    bytes1[3] memory bytesOf = [bytes1(0x0b), bytes1(0x0c), bytes1(0x00)];
    for (uint256 i = 0; i < escapes.length; i++) {
      bytes memory raw = new bytes(1);
      raw[0] = bytesOf[i];
      // Dotless, so the symbol is the whole written name and the only guard
      // that can refuse it is the blank guard.
      vm.expectRevert(
        abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, string(raw))
      );
      reader.resolveJson(
        string.concat(
          '{"thresholds":[{"action":"deposit","gasBudget":7,'
          '"permittedStorageWrites":[],"permittedValueMovements":[],'
          '"permittedCalls":[{"target":"',
          escapes[i],
          '","kind":"call"}]}]}'
        ),
        "deposit",
        omni
      );
      // And dotted, where the grammar takes the prefix: still the blank guard,
      // which runs before the reader asks the adapter anything.
      vm.expectRevert(
        abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, string(raw))
      );
      reader.resolveJson(
        string.concat(
          '{"thresholds":[{"action":"deposit","gasBudget":7,'
          '"permittedStorageWrites":[],"permittedValueMovements":[],'
          '"permittedCalls":[{"target":"',
          escapes[i],
          '.getCredential","kind":"call"}]}]}'
        ),
        "deposit",
        omni
      );
    }
  }

  /// @dev S2-R2-06. A value movement's asset name carries no suffix in the
  ///      schema, so a dot in it is part of the name. Splitting at it bound
  ///      the permit to a different asset than the manifest wrote: with an
  ///      adapter holding both, "USDC.e" resolved to canonical USDC.
  function test_a_dotted_asset_name_is_not_split() external {
    StubResolver both = new StubResolver();
    both.set("USDC", address(0xC0));
    both.set("USDC.e", address(0xCE));
    both.set("hook", HOOK);
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedCalls":[],'
      '"permittedValueMovements":[{"asset":"USDC.e","recipient":"hook"}]}]}',
      "deposit",
      both
    );
    assertEq(t.valueAssets[0], address(0xCE), "the bridged asset, not the canonical one");
    assertEq(t.valueRecipients[0], HOOK, "and the recipient is unchanged");
  }

  /// @dev S2-R2-06, the refusal direction: an adapter that does not hold the
  ///      dotted name refuses it rather than falling back to the prefix.
  function test_a_dotted_asset_name_has_no_prefix_fallback() external {
    StubResolver only = new StubResolver();
    only.set("USDC", address(0xC0));
    only.set("hook", HOOK);
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.UnresolvableSymbol.selector, "USDC.e")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedCalls":[],'
      '"permittedValueMovements":[{"asset":"USDC.e","recipient":"hook"}]}]}',
      "deposit",
      only
    );
  }

  // -- Unknown kinds and scopes -------------------------------------------------

  /// @dev S2-R3-07. Neither refusal had a unit test: admitting an unknown kind
  ///      silently, or treating it as a plain call, failed only the fuzz
  ///      invariant. Both are register line over-permit-by-category, and the
  ///      fuzz suite is the one artefact this round proved can go vacuous.
  function test_unknown_call_kind_reverts() external {
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.UnknownCallKind.selector, "weird"));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider","kind":"weird"}]}]}',
      "deposit",
      stub
    );
  }

  /// @dev The kind check is case-sensitive and exact, so a near-miss spelling
  ///      refuses rather than falling into the nearest admitting branch.
  function test_a_near_miss_call_kind_reverts_rather_than_being_admitted() external {
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.UnknownCallKind.selector, "Call"));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider","kind":"Call"}]}]}',
      "deposit",
      stub
    );
  }

  function test_unknown_storage_scope_reverts() external {
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.UnknownStorageScope.selector, "global"));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedCalls":[],"permittedValueMovements":[],'
      '"permittedStorageWrites":[{"scope":"global","slot":"anything"}]}]}',
      "deposit",
      stub
    );
  }

  // -- Dotted account names on the two paths the grammar splits ----------------

  /// @dev S2-R3-01. be6987b7 stopped the value path splitting `USDC.e`, on the
  ///      reasoning that the dot is part of the name. The call-target and
  ///      external-slot paths still split, so the same string bound the permit
  ///      to `USDC` there -- one resolver, one string, two different accounts.
  ///      Where the adapter knows the whole written name, the reader now
  ///      refuses instead of choosing a prefix.
  function test_a_dotted_call_target_the_adapter_knows_whole_is_ambiguous() external {
    StubResolver both = new StubResolver();
    both.set("USDC", address(0xC0));
    both.set("USDC.e", address(0xCE));
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.AmbiguousAccountSymbol.selector, "USDC.e")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"USDC.e","kind":"call"}]}]}',
      "deposit",
      both
    );
  }

  function test_a_dotted_external_slot_the_adapter_knows_whole_is_ambiguous() external {
    StubResolver both = new StubResolver();
    both.set("USDC", address(0xC0));
    both.set("USDC.e", address(0xCE));
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.AmbiguousAccountSymbol.selector, "USDC.e")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedCalls":[],"permittedValueMovements":[],'
      '"permittedStorageWrites":[{"scope":"external","slot":"USDC.e"}]}]}',
      "deposit",
      both
    );
  }

  /// @dev The refusal is narrow. A function suffix is not a name any adapter
  ///      holds, so the ordinary grammar is untouched -- this is the shipped
  ///      manifest's own shape.
  function test_a_function_suffix_is_not_ambiguous() external view {
    ResolvedThreshold memory t = reader.resolveFile(MANIFEST, "deposit", stub);
    assertEq(t.allowedCallTargets.length, 1, "roleProvider.validateCredential still resolves");
    assertEq(t.allowedCallTargets[0], PROVIDER, "and still to the prefix account");
  }

  /// @dev And a dotted name the adapter does not hold whole is not ambiguous
  ///      either: there is only one reading, so the grammar keeps it.
  function test_a_dotted_name_the_adapter_does_not_hold_is_not_ambiguous() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider.someFunction","kind":"call"}]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedCallTargets[0], PROVIDER, "one reading, so the prefix stands");
  }

  /// @dev The blank guard still precedes the ambiguity question, so a leading
  ///      dot is the reader's own refusal and the adapter is never asked.
  function test_a_leading_dot_is_still_blank_not_ambiguous() external {
    OmniResolver omni = new OmniResolver();
    vm.expectRevert(abi.encodeWithSelector(ManifestReader.EmptyAccountSymbol.selector, ""));
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":".getCredential","kind":"call"}]}]}',
      "deposit",
      omni
    );
  }

  /// @dev The boundary the blank guard must not cross: a symbol that merely
  ///      contains whitespace is still a name, and stays the adapter's call.
  function test_a_name_containing_a_space_is_still_a_name() external {
    OmniResolver omni = new OmniResolver();
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"role provider","kind":"call"}]}]}',
      "deposit",
      omni
    );
    assertEq(t.allowedCallTargets.length, 1, "a name with a space in it is still a name");
    assertEq(t.allowedCallTargets[0], omni.ANY(), "and the adapter decides it");
  }

  // -- Guards added by the step 2 round 4 audit ----------------------------

  /// @dev S2-R4-01. The round 3 guard asked `whole && wholeAddr != address(0)`,
  ///      so an adapter answering `(true, address(0))` for the whole written
  ///      name was read as knowing no such name and the reader split the
  ///      string anyway. That is the whole of S2-R3-01 surviving in the one
  ///      corner the guard did not cover: the permit bound to `USDC`, an
  ///      account this manifest does not name.
  function test_a_dotted_call_target_known_whole_at_zero_is_still_ambiguous() external {
    KnowsTheWholeNameAsZero r = new KnowsTheWholeNameAsZero();
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.AmbiguousAccountSymbol.selector, "USDC.e")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"USDC.e","kind":"call"}]}]}',
      "deposit",
      r
    );
  }

  /// @dev S2-R4-01, the external-slot path, which splits for the same reason.
  function test_a_dotted_external_slot_known_whole_at_zero_is_still_ambiguous() external {
    KnowsTheWholeNameAsZero r = new KnowsTheWholeNameAsZero();
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.AmbiguousAccountSymbol.selector, "USDC.e")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedCalls":[],"permittedValueMovements":[],'
      '"permittedStorageWrites":[{"scope":"external","slot":"USDC.e"}]}]}',
      "deposit",
      r
    );
  }

  /// @dev S2-R4-01, stated as the property rather than as three cases: one
  ///      string through one resolver must not resolve to two different
  ///      accounts depending on which path carries it. Before the fix the
  ///      value path refused this manifest and the other two returned 0xC0.
  ///      Both refusals are named, and neither is the silent substitution.
  function test_one_string_one_resolver_never_yields_two_accounts() external {
    KnowsTheWholeNameAsZero r = new KnowsTheWholeNameAsZero();
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.SymbolResolvesToZero.selector, "USDC.e")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedCalls":[],'
      '"permittedValueMovements":[{"asset":"USDC.e","recipient":"hook"}]}]}',
      "deposit",
      r
    );
  }

  /// @dev The prefix is resolved before the ambiguity question is asked, so a
  ///      prefix the adapter refuses reports its own refusal rather than being
  ///      masked by a second reading. `ZeroResolver` answers for every name,
  ///      including the whole dotted one, so under the reversed order this
  ///      would report AmbiguousAccountSymbol instead.
  function test_a_broken_prefix_reports_its_own_refusal_not_ambiguity() external {
    ZeroResolver zero = new ZeroResolver();
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.SymbolResolvesToZero.selector, "roleProvider")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider.getCredential","kind":"call"}]}]}',
      "deposit",
      zero
    );
  }

  // -- Guards added by the step 2 round 5 audit ----------------------------

  /// @dev S2-R5-01. The round 4 guard asked the adapter about exactly one
  ///      competing reading, the whole written string, which is only the last
  ///      of them. A name carrying two dots has an intermediate reading as
  ///      well, and it is the one the shipped manifest's own shape produces:
  ///      every dotted target here is `account.function`, so a dotted *account*
  ///      written with its function suffix is `account.part.function`. With an
  ///      adapter holding `USDC` at 0xC0 and `USDC.e` at 0xCE, the guard fired
  ///      on `USDC.e` and was silent on `USDC.e.transfer`, which bound the
  ///      permit to canonical 0xC0 -- the bridged token the manifest named was
  ///      not permitted and a token it never named was. That is the whole of
  ///      S2-R3-01 surviving one dot further out.
  function test_a_multi_dot_call_target_known_at_an_inner_prefix_is_ambiguous() external {
    StubResolver bridged = new StubResolver();
    bridged.set("USDC", address(0xC0));
    bridged.set("USDC.e", address(0xCE));
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.AmbiguousAccountSymbol.selector, "USDC.e.transfer")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"USDC.e.transfer","kind":"call"}]}]}',
      "deposit",
      bridged
    );
  }

  /// @dev S2-R5-01, the external-slot path, which splits at the same dot for
  ///      the same reason and carried the same silence.
  function test_a_multi_dot_external_slot_known_at_an_inner_prefix_is_ambiguous() external {
    StubResolver bridged = new StubResolver();
    bridged.set("USDC", address(0xC0));
    bridged.set("USDC.e", address(0xCE));
    vm.expectRevert(
      abi.encodeWithSelector(
        ManifestReader.AmbiguousAccountSymbol.selector,
        "USDC.e.balances[lender]"
      )
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedCalls":[],"permittedValueMovements":[],'
      '"permittedStorageWrites":[{"scope":"external","slot":"USDC.e.balances[lender]"}]}]}',
      "deposit",
      bridged
    );
  }

  /// @dev S2-R5-01 composed with S2-R4-01: the intermediate reading is one the
  ///      adapter answers for at the zero address. `ok` alone is still the
  ///      question, at every dot rather than only at the last, so this refuses
  ///      for the same reason the single-dot form does.
  function test_a_multi_dot_target_known_at_an_inner_prefix_at_zero_is_ambiguous() external {
    KnowsTheWholeNameAsZero r = new KnowsTheWholeNameAsZero();
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.AmbiguousAccountSymbol.selector, "USDC.e.transfer")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"USDC.e.transfer","kind":"call"}]}]}',
      "deposit",
      r
    );
  }

  /// @dev The false-fail direction, which the widened guard must not cross: a
  ///      multi-dot name with only one live reading keeps it. Neither
  ///      `roleProvider.v2` nor the whole string is a name this adapter holds,
  ///      so the grammar's prefix stands exactly as it does for a single dot.
  function test_a_multi_dot_name_with_one_reading_still_resolves_to_its_prefix() external view {
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider.v2.validateCredential","kind":"call"}]}]}',
      "deposit",
      stub
    );
    assertEq(t.allowedCallTargets.length, 1, "one reading, so the name resolves");
    assertEq(t.allowedCallTargets[0], PROVIDER, "and it is the grammar's own prefix");
  }

  /// @dev And the shipped manifest is untouched by the widening: its dotted
  ///      targets are `account.function` against an adapter holding neither the
  ///      whole string nor any inner prefix.
  function test_the_shipped_manifest_still_resolves_under_the_widened_guard() external view {
    ResolvedThreshold memory t = reader.resolveFile(MANIFEST, "deposit", stub);
    assertEq(t.allowedCallTargets.length, 1, "roleProvider.validateCredential still resolves");
    assertEq(t.allowedCallTargets[0], PROVIDER, "and still to the prefix account");
  }

  /// @dev S2-R5-02, the round 4 lead decided rather than left open. Where the
  ///      adapter knows the whole dotted name and *not* the grammar's prefix,
  ///      the reader reports `UnresolvableSymbol(prefix)` and does not fall
  ///      back to the reading the adapter does hold. That refusal is the
  ///      reader's own and is deliberate: a fallback would make which string
  ///      the grammar reads as the account depend on what the adapter happens
  ///      to contain, which is the same delegation of the reader's grammar to
  ///      the adapter that the blank guard exists to prevent. Fail-closed and
  ///      the adapter never gets to widen the reading; the cost, stated rather
  ///      than hidden, is that the named symbol is one the author did not
  ///      write.
  function test_a_name_known_only_whole_still_refuses_at_its_prefix() external {
    StubResolver onlyWhole = new StubResolver();
    onlyWhole.set("USDC.e", address(0xCE));
    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.UnresolvableSymbol.selector, "USDC")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"USDC.e","kind":"call"}]}]}',
      "deposit",
      onlyWhole
    );
  }

  /// @dev The same decision on the value path, from the other side: there the
  ///      whole string *is* the name, so the identical adapter resolves it.
  ///      The two paths disagree about the outcome kind and that is the design;
  ///      what they never do is bind the name to two different addresses, which
  ///      is what the property below states in general.
  function test_a_name_known_only_whole_resolves_on_the_value_path() external {
    StubResolver onlyWhole = new StubResolver();
    onlyWhole.set("USDC.e", address(0xCE));
    onlyWhole.set("hook", HOOK);
    ResolvedThreshold memory t = reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedCalls":[],'
      '"permittedValueMovements":[{"asset":"USDC.e","recipient":"hook"}]}]}',
      "deposit",
      onlyWhole
    );
    assertEq(t.valueAssets[0], address(0xCE), "the value path reads the whole name");
  }
}

/// @dev The invariant fuzz suite in `adapters/ManifestFuzz.sol` is written for
///      Echidna and Medusa, but neither engine implements the JSON cheatcodes
///      `ManifestReader` is built on: under both, every generated manifest
///      reverts with empty return data before the reader resolves anything, so
///      GL01 to GL09 hold without being tested and only GL00 fails. Foundry's
///      invariant engine does carry those cheatcodes, so this contract drives
///      the same generator and asserts all eleven properties where they can fail.
///
///      Importing the suite here has a second effect worth stating: the suite
///      lives outside `src` and `test`, so `forge test` did not compile it and
///      a compile break inside it was invisible to this run. The import ends
///      that.
/// @dev A derived generator that can set each ghost flag directly.
///
///      The eleven property functions are the suite's engine-facing surface, and
///      nothing could catch a mistake inside one of them: under Foundry they
///      were not called at all, and under Echidna and Medusa they are called
///      but hold vacuously. Asserting through them fixes half of that -- an
///      inverted property fails at once -- but a property that returns `true`
///      unconditionally, or reads a neighbour's ghost, still agrees with the
///      truth on every clean run, because a correct reader never sets a ghost.
///      The only way to tell those apart is to set the ghost and look.
contract ManifestFuzzGhostProbe is ManifestFuzz {
  function forceWidenedSet() external { sawWidenedSet = true; }
  function forceZeroAddress() external { sawZeroAddress = true; }
  function forcePairMismatch() external { sawPairMismatch = true; }
  function forceKindConfusion() external { sawKindConfusion = true; }
  function forceBudgetDrift() external { sawBudgetDrift = true; }
  function forceUnresolvableAccepted() external { sawUnresolvableAccepted = true; }
  function forceBlankSymbolAccepted() external { sawBlankSymbolAccepted = true; }
  function forceDuplicateActionAccepted() external { sawDuplicateActionAccepted = true; }
  function forceWrongAddress() external { sawWrongAddress = true; }
  function forceAmbiguousAccepted() external { sawAmbiguousAccepted = true; }
  function forcePathDisagreement() external { sawPathDisagreement = true; }
}

/// @dev Each of GL01 to GL09 is shown to report its own ghost and no other:
///      set one flag, and exactly one property goes false.
contract ManifestFuzzPropertyTest is JanusBase {
  ManifestFuzzGhostProbe fuzz;

  function setUp() external {
    fuzz = new ManifestFuzzGhostProbe();
  }

  /// @dev The nine properties as a bitmap, so "exactly one went false" is one
  ///      comparison rather than nine.
  function _live() internal view returns (uint256 bits) {
    if (!fuzz.echidna_GL01_set_never_widened()) bits |= 1 << 1;
    if (!fuzz.echidna_GL02_no_zero_address()) bits |= 1 << 2;
    if (!fuzz.echidna_GL03_value_pairs_aligned()) bits |= 1 << 3;
    if (!fuzz.echidna_GL04_call_kind_carried_through()) bits |= 1 << 4;
    if (!fuzz.echidna_GL05_budget_is_the_actions_own()) bits |= 1 << 5;
    if (!fuzz.echidna_GL06_unresolvable_fails_closed()) bits |= 1 << 6;
    if (!fuzz.echidna_GL07_blank_symbol_fails_closed()) bits |= 1 << 7;
    if (!fuzz.echidna_GL08_duplicate_action_fails_closed()) bits |= 1 << 8;
    if (!fuzz.echidna_GL09_every_entry_resolved_to_its_own_name()) bits |= 1 << 9;
    if (!fuzz.echidna_GL10_ambiguous_name_fails_closed()) bits |= 1 << 10;
    if (!fuzz.echidna_GL11_paths_agree_on_one_name()) bits |= 1 << 11;
  }

  function test_every_property_holds_before_any_ghost_is_set() external view {
    assertEq(_live(), 0, "a fresh generator violates nothing");
    assertTrue(fuzz.echidna_GL00_the_reader_was_actually_reached(), "and GL00 holds at zero attempts");
  }

  function test_gl01_reports_a_widened_set_and_nothing_else() external {
    fuzz.forceWidenedSet();
    assertEq(_live(), 1 << 1, "only GL01");
  }

  function test_gl02_reports_a_zero_address_and_nothing_else() external {
    fuzz.forceZeroAddress();
    assertEq(_live(), 1 << 2, "only GL02");
  }

  function test_gl03_reports_a_pair_mismatch_and_nothing_else() external {
    fuzz.forcePairMismatch();
    assertEq(_live(), 1 << 3, "only GL03");
  }

  function test_gl04_reports_kind_confusion_and_nothing_else() external {
    fuzz.forceKindConfusion();
    assertEq(_live(), 1 << 4, "only GL04");
  }

  function test_gl05_reports_budget_drift_and_nothing_else() external {
    fuzz.forceBudgetDrift();
    assertEq(_live(), 1 << 5, "only GL05");
  }

  function test_gl06_reports_an_accepted_unresolvable_and_nothing_else() external {
    fuzz.forceUnresolvableAccepted();
    assertEq(_live(), 1 << 6, "only GL06");
  }

  function test_gl07_reports_an_accepted_blank_symbol_and_nothing_else() external {
    fuzz.forceBlankSymbolAccepted();
    assertEq(_live(), 1 << 7, "only GL07");
  }

  function test_gl08_reports_an_accepted_duplicate_action_and_nothing_else() external {
    fuzz.forceDuplicateActionAccepted();
    assertEq(_live(), 1 << 8, "only GL08");
  }

  function test_gl09_reports_a_wrong_address_and_nothing_else() external {
    fuzz.forceWrongAddress();
    assertEq(_live(), 1 << 9, "only GL09");
  }

  function test_gl10_reports_an_accepted_ambiguous_name_and_nothing_else() external {
    fuzz.forceAmbiguousAccepted();
    assertEq(_live(), 1 << 10, "only GL10");
  }

  function test_gl11_reports_a_path_disagreement_and_nothing_else() external {
    fuzz.forcePathDisagreement();
    assertEq(_live(), 1 << 11, "only GL11");
  }
}

contract ManifestFuzzInvariantTest is JanusBase {
  ManifestFuzz fuzz;

  function setUp() public {
    fuzz = new ManifestFuzz();
  }

  /// @dev Drive only the generator; the reader and the stub resolver it
  ///      deploys are reached through it, never directly.
  function targetContracts() public view returns (address[] memory addrs) {
    addrs = new address[](1);
    addrs[0] = address(fuzz);
  }

  /// @dev Asserted through the ten property functions, not through the ghost
  ///      getters behind them. Reading the getters directly left the nine
  ///      `echidna_GL01` to `echidna_GL09` bodies executed by nothing that
  ///      could fail: Foundry never called them, and under Echidna and Medusa
  ///      they run but hold vacuously, so inverting one, or pointing it at the
  ///      wrong ghost, changed no result anywhere. They are the suite's
  ///      engine-facing surface, so they are what this asserts.
  function invariant_manifest_resolution_holds() external view {
    assertTrue(
      fuzz.echidna_GL00_the_reader_was_actually_reached(),
      "GL00: the generator reached the reader, so the nine ghosts below were actually tested"
    );
    assertTrue(fuzz.echidna_GL01_set_never_widened(), "GL01: no resolved set is wider than the manifest entries behind it");
    assertTrue(fuzz.echidna_GL02_no_zero_address(), "GL02: no resolved set carries the zero address");
    assertTrue(fuzz.echidna_GL03_value_pairs_aligned(), "GL03: the value asset and recipient sets stay the same length");
    assertTrue(fuzz.echidna_GL04_call_kind_carried_through(), "GL04: each call set holds exactly its own kind's entries");
    assertTrue(fuzz.echidna_GL05_budget_is_the_actions_own(), "GL05: the gas budget is the named action's own");
    assertTrue(fuzz.echidna_GL06_unresolvable_fails_closed(), "GL06: an unresolvable symbol or unknown kind or scope never resolves");
    assertTrue(fuzz.echidna_GL07_blank_symbol_fails_closed(), "GL07: a manifest carrying a blank account symbol never resolves");
    assertTrue(fuzz.echidna_GL08_duplicate_action_fails_closed(), "GL08: a manifest naming one action twice never resolves");
    assertTrue(fuzz.echidna_GL09_every_entry_resolved_to_its_own_name(), "GL09: every entry resolved to the address its own name holds");
    assertTrue(fuzz.echidna_GL10_ambiguous_name_fails_closed(), "GL10: a manifest carrying a name with two readings never resolves");
    assertTrue(fuzz.echidna_GL11_paths_agree_on_one_name(), "GL11: no one name bound to two different accounts across the three paths");
  }

  /// @dev And the getters behind them, so a property function that ignored its
  ///      own ghost is caught from the other side too.
  function invariant_every_ghost_flag_agrees_with_its_property() external view {
    assertEq(fuzz.echidna_GL01_set_never_widened(), !fuzz.sawWidenedSet(), "GL01 reads its own ghost");
    assertEq(fuzz.echidna_GL02_no_zero_address(), !fuzz.sawZeroAddress(), "GL02 reads its own ghost");
    assertEq(fuzz.echidna_GL03_value_pairs_aligned(), !fuzz.sawPairMismatch(), "GL03 reads its own ghost");
    assertEq(fuzz.echidna_GL04_call_kind_carried_through(), !fuzz.sawKindConfusion(), "GL04 reads its own ghost");
    assertEq(fuzz.echidna_GL05_budget_is_the_actions_own(), !fuzz.sawBudgetDrift(), "GL05 reads its own ghost");
    assertEq(fuzz.echidna_GL06_unresolvable_fails_closed(), !fuzz.sawUnresolvableAccepted(), "GL06 reads its own ghost");
    assertEq(fuzz.echidna_GL07_blank_symbol_fails_closed(), !fuzz.sawBlankSymbolAccepted(), "GL07 reads its own ghost");
    assertEq(fuzz.echidna_GL08_duplicate_action_fails_closed(), !fuzz.sawDuplicateActionAccepted(), "GL08 reads its own ghost");
    assertEq(fuzz.echidna_GL09_every_entry_resolved_to_its_own_name(), !fuzz.sawWrongAddress(), "GL09 reads its own ghost");
    assertEq(fuzz.echidna_GL10_ambiguous_name_fails_closed(), !fuzz.sawAmbiguousAccepted(), "GL10 reads its own ghost");
    assertEq(fuzz.echidna_GL11_paths_agree_on_one_name(), !fuzz.sawPathDisagreement(), "GL11 reads its own ghost");
  }

  /// @dev The anti-vacuity guard, deterministic rather than sampled: the nine
  ///      nine properties above are all negated ghost flags, so a generator
  ///      that never reaches the reader satisfies every one of them. This drives a
  ///      fixed sequence of 256 draws and requires that some of them resolved.
  ///      About one manifest in sixteen resolves, so 256 fixed draws clear the
  ///      bar by a wide margin; it is the test that fails first if the JSON
  ///      cheatcodes stop working or the generator degenerates.
  function test_the_generator_actually_reaches_the_reader() external {
    for (uint256 i = 0; i < 256; i++) {
      bytes32 h = keccak256(abi.encode(i));
      fuzz.fuzzResolve(
        uint8(uint256(h)),
        uint8(uint256(h) >> 8),
        uint8(uint256(h) >> 16),
        uint8(uint256(h) >> 24),
        uint8(uint256(h) >> 32),
        uint8(uint256(h) >> 40),
        uint64(uint256(h) >> 48),
        (uint256(h) >> 112) & 1 == 1,
        (uint256(h) >> 120) & 1 == 1
      );
    }
    assertEq(fuzz.resolveAttempts(), 256, "every draw was attempted");
    assertTrue(fuzz.resolveSuccesses() > 0, "some generated manifest resolved, so the ghost checks ran");
    assertTrue(fuzz.resolveReverts() > 0, "and some refused, so the fail-closed paths ran too");
  }

  /// @dev GL00 as the external engines see it. Under Echidna and Medusa this
  ///      is the property that fails; here it is shown to hold once the
  ///      generator has actually resolved something.
  function test_gl00_holds_once_the_reader_has_been_reached() external {
    assertTrue(fuzz.echidna_GL00_the_reader_was_actually_reached(), "GL00 holds before any attempt");
    for (uint256 i = 0; i < 256; i++) {
      bytes32 h = keccak256(abi.encode(i));
      fuzz.fuzzResolve(
        uint8(uint256(h)),
        uint8(uint256(h) >> 8),
        uint8(uint256(h) >> 16),
        uint8(uint256(h) >> 24),
        uint8(uint256(h) >> 32),
        uint8(uint256(h) >> 40),
        uint64(uint256(h) >> 48),
        (uint256(h) >> 112) & 1 == 1,
        (uint256(h) >> 120) & 1 == 1
      );
    }
    assertTrue(fuzz.echidna_GL00_the_reader_was_actually_reached(), "and holds after the reader was reached");
  }

  /// @dev GL11's coverage claim, made deterministically here rather than as a
  ///      counter threshold on the property itself. GL11 compares the three
  ///      paths against each other, so it is silent unless a draw binds a name
  ///      on at least two of them; a table where nothing binds twice would let
  ///      it hold for the same reason an unreached reader lets GL01 hold.
  ///
  ///      Every name in `_pathName` is driven once. Two of the eight bind on
  ///      more than one path -- `asset`, dot-free and identical everywhere,
  ///      and `roleProvider.getCredential`, whose suffix is documentation the
  ///      call and slot paths both discard -- and `asset.e` binds on the value
  ///      path alone, which is the S2-R5-01 shape GL10 rather than GL11 is
  ///      responsible for. The assertion is on the two-path count, because
  ///      that is the number GL11's comparisons actually require.
  function test_gl11_draws_actually_bind_on_more_than_one_path() external {
    uint256 boundOnTwo;
    for (uint8 k = 0; k < 8; k++) {
      uint256 before = fuzz.agreementBinds();
      fuzz.fuzzPathAgreement(k);
      if (fuzz.agreementBinds() > before) boundOnTwo++;
    }
    assertEq(fuzz.agreementDraws(), 8, "every name in the table was drawn");
    assertTrue(boundOnTwo >= 2, "at least two names bound, so GL11's comparisons ran");
    assertTrue(fuzz.echidna_GL11_paths_agree_on_one_name(), "and the reader agreed with itself on all of them");
  }
}
