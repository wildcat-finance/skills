// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";
import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";
import {WildcatHostModel, MockAsset} from "../src/wildcat/WildcatHostModel.sol";
import {HonestAccessHook} from "../src/wildcat/HonestAccessHook.sol";
import {WildcatHostAdapter} from "../src/wildcat/WildcatHostAdapter.sol";
import {MockRoleProvider} from "../src/wildcat/MockRoleProvider.sol";

/// @dev Step 3's subject: the adapter's name table, and the reader resolving
///      through it rather than through a stub. Step 2 proved the reader's
///      grammar against inline resolvers; this proves the one resolver the
///      Wildcat host actually ships, so the two halves are joined by something
///      executed rather than by assertion.
contract WildcatAdapterTest is JanusBase {
  string constant MANIFEST = "manifests/wildcat-open-term.json";

  MockAsset asset;
  WildcatHostModel model;
  HonestAccessHook honest;
  MockRoleProvider provider;
  WildcatHostAdapter adapter;
  ManifestReader reader;

  function setUp() public {
    asset = new MockAsset();
    model = new WildcatHostModel(asset);
    honest = new HonestAccessHook();
    provider = new MockRoleProvider();
    adapter = new WildcatHostAdapter(model, asset, address(provider));
    model.setBorrower(address(adapter));
    model.setHook(address(honest));
    reader = new ManifestReader();
  }

  function _resolver() internal view returns (AccountResolver) {
    return AccountResolver(address(adapter));
  }

  // ---------------------------- The name table --------------------------- //

  /// @dev All four names at once, each against the address the adapter holds
  ///      rather than against a literal, so the test cannot pass by agreeing
  ///      with a constant that drifted from the deployment.
  function test_the_four_names_resolve_to_the_adapters_own_addresses() external view {
    (bool okHook, address hookAddr) = adapter.resolveAccount("hook");
    assertTrue(okHook, "hook is a name this adapter holds");
    assertEq(hookAddr, address(honest), "hook is the installed hook");

    (bool okHost, address hostAddr) = adapter.resolveAccount("host");
    assertTrue(okHost, "host is a name this adapter holds");
    assertEq(hostAddr, address(model), "host is the market model");

    (bool okAsset, address assetAddr) = adapter.resolveAccount("asset");
    assertTrue(okAsset, "asset is a name this adapter holds");
    assertEq(assetAddr, address(asset), "asset is the market asset");

    (bool okProvider, address providerAddr) = adapter.resolveAccount("roleProvider");
    assertTrue(okProvider, "roleProvider is a name this adapter holds");
    assertEq(providerAddr, address(provider), "roleProvider is the provider");
  }

  /// @dev The four are distinct. Without this, a table that returned the same
  ///      address for every name would satisfy each assertion above only if
  ///      the fixtures happened to differ, and would satisfy a weaker suite
  ///      that checked `ok` alone.
  function test_the_four_names_resolve_to_four_different_addresses() external view {
    (, address h) = adapter.resolveAccount("hook");
    (, address s) = adapter.resolveAccount("host");
    (, address a) = adapter.resolveAccount("asset");
    (, address p) = adapter.resolveAccount("roleProvider");
    assertTrue(h != s && h != a && h != p, "hook shares no address");
    assertTrue(s != a && s != p, "host shares no address");
    assertTrue(a != p, "asset and roleProvider differ");
  }

  /// @dev An unknown name answers `ok` false, and the reader turns that into
  ///      its own refusal.
  function test_an_unknown_symbol_is_not_resolved() external {
    (bool ok, address addr) = adapter.resolveAccount("borrower");
    assertTrue(!ok, "borrower is not a name in the table");
    assertEq(addr, address(0), "and it carries no address");

    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.UnresolvableSymbol.selector, "borrower")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"borrower.pay","kind":"call"}]}]}',
      "deposit",
      _resolver()
    );
  }

  /// @dev The table never answers for a category. `categoryOf` classifies the
  ///      asset and the host, but no name resolves to an address merely
  ///      because it shares a kind with one, and a name that is a category's
  ///      own label is still not in the table.
  function test_a_category_label_is_not_a_name() external view {
    (bool ok, ) = adapter.resolveAccount("Asset");
    assertTrue(!ok, "the table is not case-insensitive and not category-keyed");
    (bool unknown, ) = adapter.resolveAccount("Unknown");
    assertTrue(!unknown, "and the Unknown category is not a resolvable name");
  }

  /// @dev A name the adapter holds whose address is unconfigured answers `ok`
  ///      true at the zero address, and the reader raises
  ///      `SymbolResolvesToZero` rather than `UnresolvableSymbol`. Keeping the
  ///      two apart is what lets a reader tell a missing configuration from a
  ///      name nobody has heard of; `WildcatConformance.t.sol` builds the
  ///      adapter this way today, so the path is live in the suite.
  function test_a_held_name_at_the_zero_address_refuses_as_zero_not_unknown() external {
    MockAsset a2 = new MockAsset();
    WildcatHostModel m2 = new WildcatHostModel(a2);
    WildcatHostAdapter unconfigured = new WildcatHostAdapter(m2, a2, address(0));
    m2.setHook(address(new HonestAccessHook()));

    (bool ok, address addr) = unconfigured.resolveAccount("roleProvider");
    assertTrue(ok, "the name is held even with nothing configured behind it");
    assertEq(addr, address(0), "and it answers with the zero it holds");

    vm.expectRevert(
      abi.encodeWithSelector(ManifestReader.SymbolResolvesToZero.selector, "roleProvider")
    );
    reader.resolveJson(
      '{"thresholds":[{"action":"deposit","gasBudget":7,'
      '"permittedStorageWrites":[],"permittedValueMovements":[],'
      '"permittedCalls":[{"target":"roleProvider.getCredential","kind":"call"}]}]}',
      "deposit",
      AccountResolver(address(unconfigured))
    );
  }

  /// @dev The "mirrors categoryOf" claim in the adapter's own header, checked
  ///      rather than asserted. The two tables encode the same four deployment
  ///      facts in opposite directions -- name to address here, address to
  ///      kind there -- and nothing else makes them agree, so either can drift
  ///      from the other silently. This pins the correspondence at all four
  ///      names.
  ///
  ///      It is the correspondence that is checked, not the implementation.
  ///      `resolveAccount` deliberately does not call `categoryOf`, because
  ///      answering by category is the widening this step exists to avoid; the
  ///      point is that two independent tables still describe one deployment.
  function test_every_held_name_classifies_as_its_matching_category() external view {
    (, address h) = adapter.resolveAccount("hook");
    assertTrue(
      adapter.categoryOf(h) == WildcatHostAdapter.Category.Hook,
      "hook resolves to something categoryOf calls the hook"
    );
    (, address s) = adapter.resolveAccount("host");
    assertTrue(
      adapter.categoryOf(s) == WildcatHostAdapter.Category.Host,
      "host resolves to something categoryOf calls the host"
    );
    (, address a) = adapter.resolveAccount("asset");
    assertTrue(
      adapter.categoryOf(a) == WildcatHostAdapter.Category.Asset,
      "asset resolves to something categoryOf calls the asset"
    );
    (, address p) = adapter.resolveAccount("roleProvider");
    assertTrue(
      adapter.categoryOf(p) == WildcatHostAdapter.Category.RoleProvider,
      "roleProvider resolves to something categoryOf calls the role provider"
    );
  }

  /// @dev And the other direction of the same claim: a name the table refuses
  ///      does not classify as one of the four kinds either, so "not in the
  ///      table" and "not a known category" agree on the addresses that
  ///      matter. `borrower` is the interesting case -- the host genuinely has
  ///      one, `roles()` returns it, and neither table names it.
  function test_a_name_the_table_refuses_is_not_a_known_category() external view {
    (bool ok, ) = adapter.resolveAccount("borrower");
    assertTrue(!ok, "borrower is not in the table");
    assertTrue(
      adapter.categoryOf(model.borrower()) == WildcatHostAdapter.Category.Unknown,
      "and the borrower address is not one of the four kinds"
    );
  }

  /// @dev The hook's provider is set once and only forward. Without a test the
  ///      guard was a line no mutant could kill: deleting it changed nothing
  ///      anywhere, which is the same dead-guard shape as S2-R4-03 and
  ///      S2-R6-01. It is worth keeping rather than deleting, because a
  ///      swapped provider would silently move the account a resolved permit
  ///      names, so it is exercised here instead.
  function test_the_hooks_role_provider_is_set_once() external {
    HonestAccessHook hook = new HonestAccessHook();
    hook.setRoleProvider(provider);
    assertEq(address(hook.roleProvider()), address(provider), "the first set takes");

    MockRoleProvider other = new MockRoleProvider();
    vm.expectRevert(bytes("provider set"));
    hook.setRoleProvider(other);
    assertEq(address(hook.roleProvider()), address(provider), "and the second is refused");
  }

  // ------------------- The reader against the real adapter ---------------- //

  /// @dev The step's goal in one test: the shipped manifest, resolved through
  ///      the shipped adapter, yields the concrete addresses the model was
  ///      deployed with. `deposit` names `roleProvider.validateCredential` as
  ///      a `call` and `roleProvider.getCredential` as a `staticcall`, so the
  ///      state-changing set carries the provider once and not twice.
  function test_the_shipped_manifest_resolves_through_the_shipped_adapter() external view {
    ResolvedThreshold memory t = reader.resolveFile(MANIFEST, "deposit", _resolver());
    assertEq(t.allowedCallTargets.length, 1, "one state-changing call target");
    assertEq(t.allowedCallTargets[0], address(provider), "and it is the role provider");
    assertEq(t.allowedDelegateTargets.length, 0, "the manifest permits no delegatecall");
  }

  // --------------------------- The mock provider -------------------------- //

  /// @dev Both credential entry points the manifest names, and the difference
  ///      between them. `getCredential` is reachable under `staticcall`;
  ///      `validateCredential` is not, because it writes -- which is what
  ///      makes the manifest's two call kinds observably different rather
  ///      than a distinction only the schema believes in.
  function test_the_provider_answers_both_credential_calls() external {
    address lender = address(0xBEEF);
    provider.grant(lender, uint32(block.timestamp + 1000));

    assertEq(
      uint256(provider.getCredential(lender)),
      block.timestamp + 1000,
      "the read path returns the granted expiry"
    );

    assertEq(uint256(provider.validations()), 0, "the write path has not run yet");
    assertEq(
      uint256(provider.validateCredential(lender, "")),
      block.timestamp + 1000,
      "the write path returns the same expiry"
    );
    assertEq(uint256(provider.validations()), 1, "and it recorded that it ran");

    // Twice, so the counter is shown to count rather than to latch. A latch
    // satisfies every assertion above and cannot report a second call.
    provider.validateCredential(lender, "");
    assertEq(uint256(provider.validations()), 2, "a second call is counted, not latched");

    // An account with no credential reads zero rather than reverting, so the
    // absence of a credential is a value the caller decides on and not an
    // error this stand-in raises on its behalf.
    assertEq(uint256(provider.getCredential(address(0xDEAD))), 0, "no credential is zero");
  }

  /// @dev The direction that makes the kinds different rather than merely
  ///      named differently: a static call into `validateCredential` fails,
  ///      while the same static call into `getCredential` succeeds.
  function test_only_the_read_path_survives_a_staticcall() external {
    address lender = address(0xBEEF);
    provider.grant(lender, uint32(block.timestamp + 1000));

    (bool readOk, ) = address(provider).staticcall(
      abi.encodeWithSelector(MockRoleProvider.getCredential.selector, lender)
    );
    assertTrue(readOk, "getCredential is reachable under staticcall");

    (bool writeOk, ) = address(provider).staticcall(
      abi.encodeWithSelector(MockRoleProvider.validateCredential.selector, lender, bytes(""))
    );
    assertTrue(!writeOk, "validateCredential is not");
  }
}
