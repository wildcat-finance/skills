// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";

/// @dev The stub adapter the campaign resolves through. Its table is chosen so
///      that every refusal the reader owns is the reader's to get right.
///
///      Five ordinary names, one it does not know, and three it answers to on
///      purpose even though the reader must refuse them first: the empty name,
///      a whitespace-only name, and `ghost`, which it claims to know while
///      resolving it to the zero address. A tenth, `phantom`, is refused while
///      still carrying an address, which is the one combination the table
///      could not otherwise produce.
///
///      Each of those three exists because a property that only the adapter
///      enforces is not a property of the reader. GL07 held with the reader's
///      blank guard deleted while the adapter did not answer to the empty
///      name; GL02 held with the reader's zero-address guard deleted while no
///      name could resolve to zero. `asset.e` is here for the same reason on
///      the value path: it is a name that contains a dot, so a reader that
///      splits it resolves the wrong asset.
contract FuzzResolver is AccountResolver {
  mapping(bytes32 => address) private t;

  constructor() {
    t[keccak256("hook")] = address(0xA1);
    t[keccak256("host")] = address(0xA2);
    t[keccak256("asset")] = address(0xA3);
    t[keccak256("roleProvider")] = address(0xA4);
    t[keccak256("someAccount")] = address(0xA5);
    t[keccak256("")] = address(0xA6);
    t[keccak256(" ")] = address(0xA7);
    t[keccak256("asset.e")] = address(0xA8);
  }

  function resolveAccount(string calldata n) external view returns (bool, address) {
    // A name known to resolve to nothing. Without it `ok` and "non-zero" are
    // the same predicate and the reader's zero-address refusal is untestable.
    if (keccak256(bytes(n)) == keccak256("ghost")) return (true, address(0));
    // And the other direction, which the table alone cannot produce: a name
    // refused while still carrying an address. Without it, `!ok` and
    // `addr == 0` coincide, so deleting `UnresolvableSymbol` from the reader
    // simply falls through to `SymbolResolvesToZero` and the campaign sees no
    // difference -- GL06 would test the zero-address guard twice and the
    // unresolvable-name guard never.
    if (keccak256(bytes(n)) == keccak256("phantom")) return (false, address(0xA9));
    // A dotted name the adapter answers for at the zero address, whose prefix
    // `host` is live. Without it the campaign can only see the ambiguity guard
    // deleted, never the guard drawn too narrowly: round 3 asked
    // `ok && addr != 0`, which refuses `asset.e` below and admits this one, so
    // `asset.e` alone left S2-R4-01 invisible here.
    if (keccak256(bytes(n)) == keccak256("host.shadow")) return (true, address(0));
    address a = t[keccak256(bytes(n))];
    return (a != address(0), a);
  }
}

contract ManifestFuzz {
  ManifestReader internal reader;
  FuzzResolver internal resolver;

  uint256 public resolveAttempts;
  uint256 public resolveSuccesses;
  uint256 public resolveReverts;
  bool public sawWidenedSet;
  bool public sawZeroAddress;
  bool public sawPairMismatch;
  bool public sawKindConfusion;
  bool public sawBudgetDrift;
  bool public sawUnresolvableAccepted;
  bool public sawDuplicateActionAccepted;
  bool public sawBlankSymbolAccepted;
  bool public sawWrongAddress;
  bool public sawAmbiguousAccepted;

  uint256 internal _expectedCalls;
  uint256 internal _expectedDelegates;
  bool internal _anyUnresolvable;
  bool internal _anyBogus;
  bool internal _duplicateAction;
  bool internal _anyBlankSymbol;
  bool internal _anyAmbiguous;

  // The address each entry must resolve to, in the order the reader emits it.
  // Cardinality alone cannot tell a correct set from a set of the right size
  // holding the wrong addresses: a reader writing one constant into every
  // admitted slot satisfied every other property here.
  address[] internal _expCall;
  address[] internal _expDelegate;
  address[] internal _expWrite;
  address[] internal _expAsset;
  address[] internal _expRecipient;

  constructor() {
    reader = new ManifestReader();
    resolver = new FuzzResolver();
  }

  /// @dev Ten symbol choices: five the resolver knows, one it does not, two
  ///      the reader's grammar must refuse before the resolver is asked, one
  ///      the resolver claims to know while resolving it to zero, and one it
  ///      refuses while still handing back an address.
  function _sym(uint8 i) internal pure returns (string memory) {
    uint8 k = i % 10;
    if (k == 0) return "hook";
    if (k == 1) return "host";
    if (k == 2) return "asset";
    if (k == 3) return "roleProvider";
    if (k == 4) return "someAccount";
    if (k == 5) return "unknown";
    if (k == 6) return "";
    if (k == 7) return " ";
    if (k == 8) return "ghost";
    return "phantom";
  }

  /// @dev The address the resolver holds for a symbol the reader will accept.
  ///      Zero for every choice that must refuse, which cannot appear in a
  ///      comparison because a refusal never reaches `_check`.
  function _addrOf(uint8 i) internal pure returns (address) {
    uint8 k = i % 10;
    if (k == 0) return address(0xA1);
    if (k == 1) return address(0xA2);
    if (k == 2) return address(0xA3);
    if (k == 3) return address(0xA4);
    if (k == 4) return address(0xA5);
    return address(0);
  }

  function _symKnown(uint8 i) internal pure returns (bool) { return (i % 10) < 5; }
  function _symBlank(uint8 i) internal pure returns (bool) { uint8 k = i % 10; return k == 6 || k == 7; }
  function _symZero(uint8 i) internal pure returns (bool) { return (i % 10) == 8; }

  /// @dev For the two symbol choices that have one, the dotted name the
  ///      resolver holds whole as well as by prefix -- the manifest with two
  ///      readings the reader must refuse. Empty for every other choice.
  ///
  ///      Two of them, because the guard has two ways to be wrong and one
  ///      name cannot show both. `asset.e` answers `(true, 0xA8)` and dies
  ///      when the guard is deleted; `host.shadow` answers `(true, address(0))`
  ///      and dies when the guard asks for a non-zero address as well, which
  ///      is S2-R4-01. Both split to a live prefix -- 0xA3 and 0xA2 -- and
  ///      that prefix is what the generator's own expectation holds, so a
  ///      reader that splits them agrees with GL09 and only GL10 sees it.
  function _ambiguousName(uint8 i) internal pure returns (string memory) {
    uint8 k = i % 10;
    if (k == 1) return "host.shadow";
    if (k == 2) return "asset.e";
    return "";
  }

  function _kind(uint8 i) internal pure returns (string memory) {
    uint8 k = i % 4;
    if (k == 0) return "call";
    if (k == 1) return "delegatecall";
    if (k == 2) return "staticcall";
    return "bogus";
  }
  function _scope(uint8 i) internal pure returns (string memory) {
    uint8 k = i % 4;
    if (k == 0) return "hook";
    if (k == 1) return "host";
    if (k == 2) return "external";
    return "bogus";
  }
  function _u(uint256 v) internal pure returns (string memory) {
    if (v == 0) return "0";
    uint256 d;
    for (uint256 t2 = v; t2 != 0; t2 /= 10) d++;
    bytes memory b = new bytes(d);
    for (; v != 0; v /= 10) b[--d] = bytes1(uint8(48 + (v % 10)));
    return string(b);
  }

  function _buildCalls(uint256 nc, uint8 symSeed, uint8 kindSeed, bool dots, bool valid)
    internal returns (string memory out)
  {
    out = "[";
    for (uint256 i = 0; i < nc; i++) {
      uint8 s = uint8(uint256(keccak256(abi.encode(symSeed, i, "c"))));
      uint8 k = uint8(uint256(keccak256(abi.encode(kindSeed, i, "c"))));
      // `valid` folds each seed into the subrange the reader accepts: symbol
      // choices 0 to 4 are the names that resolve, kinds 0 to 2 are the three
      // the reader admits. `fuzzResolve` says why every fourth draw is built
      // this way.
      if (valid) { s = s % 5; k = k % 3; }
      // A dotted suffix on a blank symbol yields a leading dot, the
      // malformed-grammar case the reader must refuse itself.
      //
      // And, on invalid draws only, a dotted name the resolver holds whole:
      // `asset.e` is `asset` plus a dot plus a suffix by the grammar, and a
      // name in its own right to the resolver, so the manifest has two
      // readings and the reader must refuse it. Every other symbol choice
      // yields `<name>.someFunction`, which no adapter holds, so before this
      // the ambiguity refusal was structurally unreachable from the campaign
      // and deleting it left all ten properties green. Invalid draws only,
      // because a valid draw is one the reader is obliged to resolve and
      // GL00 counts on that staying true.
      string memory target;
      string memory ambiguous = _ambiguousName(s);
      if (!dots) target = _sym(s);
      else if (!valid && bytes(ambiguous).length != 0) { target = ambiguous; _anyAmbiguous = true; }
      else target = string.concat(_sym(s), ".someFunction");
      out = string.concat(out, i == 0 ? "" : ",", '{"target":"', target, '","kind":"', _kind(k), '"}');
      if (_symBlank(s)) _anyBlankSymbol = true;
      else if (_symZero(s) || !_symKnown(s)) _anyUnresolvable = true;
      if ((k % 4) == 3) _anyBogus = true;
      else if ((k % 4) == 0) { _expectedCalls++; _expCall.push(_addrOf(s)); }
      else if ((k % 4) == 1) { _expectedDelegates++; _expDelegate.push(_addrOf(s)); }
    }
    out = string.concat(out, "]");
  }

  function _buildWrites(uint256 nw, uint8 symSeed, uint8 scopeSeed, bool dots, bool valid)
    internal returns (string memory out)
  {
    out = "[";
    for (uint256 i = 0; i < nw; i++) {
      uint8 s = uint8(uint256(keccak256(abi.encode(symSeed, i, "w"))));
      uint8 sc = uint8(uint256(keccak256(abi.encode(scopeSeed, i, "w"))));
      if (valid) { s = s % 5; sc = sc % 3; }
      // The external-slot path splits at the dot exactly as a call target
      // does, so it carries the same ambiguous name for the same reason.
      string memory slot;
      string memory ambiguous = _ambiguousName(s);
      if (!dots) slot = _sym(s);
      else if (!valid && bytes(ambiguous).length != 0 && (sc % 4) == 2) {
        slot = ambiguous;
        _anyAmbiguous = true;
      } else slot = string.concat(_sym(s), ".field[key]");
      out = string.concat(out, i == 0 ? "" : ",", '{"scope":"', _scope(sc), '","slot":"', slot, '"}');
      if ((sc % 4) == 3) {
        _anyBogus = true;
      } else if ((sc % 4) == 2) {
        if (_symBlank(s)) _anyBlankSymbol = true;
        else if (_symZero(s) || !_symKnown(s)) _anyUnresolvable = true;
        _expWrite.push(_addrOf(s));
      } else {
        // Scope `hook` and scope `host` ignore the slot's own symbol and
        // resolve the fixed name, so the expected address is fixed too.
        _expWrite.push((sc % 4) == 0 ? address(0xA1) : address(0xA2));
      }
    }
    out = string.concat(out, "]");
  }

  function _buildMoves(uint256 nm, uint8 symSeed, bool dots, bool valid)
    internal returns (string memory out)
  {
    out = "[";
    for (uint256 i = 0; i < nm; i++) {
      uint8 sa = uint8(uint256(keccak256(abi.encode(symSeed, i, "ma"))));
      uint8 sr = uint8(uint256(keccak256(abi.encode(symSeed, i, "mr"))));
      if (valid) { sa = sa % 5; sr = sr % 5; }
      // The value path has no dot grammar: an asset symbol is a whole name,
      // and `asset.e` is a name the resolver holds separately from `asset`. A
      // reader that splits at the dot here resolves the wrong asset, which is
      // a mismatch only an address comparison catches.
      if (dots) { sa = 2; sr = 2; }
      string memory assetName = dots ? "asset.e" : _sym(sa);
      string memory recipientName = dots ? "asset.e" : _sym(sr);
      out = string.concat(
        out, i == 0 ? "" : ",",
        '{"asset":"', assetName, '","recipient":"', recipientName, '"}'
      );
      if (dots) {
        _expAsset.push(address(0xA8));
        _expRecipient.push(address(0xA8));
      } else {
        if (_symBlank(sa) || _symBlank(sr)) _anyBlankSymbol = true;
        else if (_symZero(sa) || _symZero(sr) || !_symKnown(sa) || !_symKnown(sr)) {
          _anyUnresolvable = true;
        }
        _expAsset.push(_addrOf(sa));
        _expRecipient.push(_addrOf(sr));
      }
    }
    out = string.concat(out, "]");
  }

  function fuzzResolve(
    uint8 nCalls, uint8 nWrites, uint8 nMoves,
    uint8 symSeed, uint8 kindSeed, uint8 scopeSeed,
    uint64 budget, bool dots, bool duplicate
  ) public {
    // Every fourth draw is built inside the subrange the reader accepts, so
    // that a campaign resolving nothing becomes a fact GL00 can state rather
    // than a silence the other properties read as success.
    bool valid = (resolveAttempts % 4) == 3;
    if (valid) duplicate = false;

    uint256 nc = nCalls % 4;
    uint256 nw = nWrites % 4;
    uint256 nm = nMoves % 3;
    if (budget == 0) budget = 1;

    _expectedCalls = 0; _expectedDelegates = 0;
    _anyUnresolvable = false; _anyBogus = false; _anyBlankSymbol = false;
    _anyAmbiguous = false;
    _duplicateAction = duplicate;
    delete _expCall; delete _expDelegate; delete _expWrite;
    delete _expAsset; delete _expRecipient;

    string memory threshold = string.concat(
      '{"action":"deposit","gasBudget":', _u(budget),
      ',"permittedCalls":', _buildCalls(nc, symSeed, kindSeed, dots, valid),
      ',"permittedStorageWrites":', _buildWrites(nw, symSeed, scopeSeed, dots, valid),
      ',"permittedValueMovements":', _buildMoves(nm, symSeed, dots, valid), '}'
    );
    // A decoy threshold, always first, naming a different action. Without it
    // every manifest the campaign generates holds exactly one action name, so
    // `.thresholds[0]` and the by-name prefix are the same string and no
    // property can tell selection-by-name from selection-by-position: a reader
    // that ignored its `action` argument entirely passed all ten. Its budget
    // is 0, which no draw can produce, so a positional reader trips GL05; its
    // one call entry is resolvable, so a positional reader gets far enough to
    // trip GL04 and GL09 as well rather than merely reverting.
    string memory decoy =
      '{"action":"queueWithdrawal","gasBudget":0,'
      '"permittedCalls":[{"target":"host","kind":"call"}],'
      '"permittedStorageWrites":[],"permittedValueMovements":[]}';
    // A second copy of the deposit threshold. Selection is by name, so a
    // manifest that states one action twice has no single answer and must
    // refuse; without this the whole of `_thresholdByAction` past its first
    // match goes unexercised.
    string memory json = duplicate
      ? string.concat('{"thresholds":[', decoy, ',', threshold, ',', threshold, ']}')
      : string.concat('{"thresholds":[', decoy, ',', threshold, ']}');

    resolveAttempts++;
    try reader.resolveJson(json, "deposit", resolver) returns (ResolvedThreshold memory t) {
      resolveSuccesses++;
      _check(t, nc, nw, nm, budget);
    } catch {
      resolveReverts++;
    }
  }

  function _check(ResolvedThreshold memory t, uint256 nc, uint256 nw, uint256 nm, uint64 budget)
    internal
  {
    if (_anyUnresolvable || _anyBogus) sawUnresolvableAccepted = true;
    if (_anyBlankSymbol) sawBlankSymbolAccepted = true;
    if (_anyAmbiguous) sawAmbiguousAccepted = true;
    if (_duplicateAction) sawDuplicateActionAccepted = true;

    // Length checks first. The value loops below read both value arrays at one
    // index, so a reader returning them at different lengths would panic here
    // and roll the whole draw back, which would leave GL03 permanently green.
    if (t.allowedCallTargets.length > nc) sawWidenedSet = true;
    if (t.allowedDelegateTargets.length > nc) sawWidenedSet = true;
    if (t.allowedCallTargets.length + t.allowedDelegateTargets.length > nc) sawWidenedSet = true;
    if (t.allowedWriteAccounts.length > nw) sawWidenedSet = true;
    if (t.valueAssets.length > nm) sawWidenedSet = true;
    if (t.valueAssets.length != t.valueRecipients.length) sawPairMismatch = true;

    if (t.allowedCallTargets.length != _expectedCalls) sawKindConfusion = true;
    if (t.allowedDelegateTargets.length != _expectedDelegates) sawKindConfusion = true;
    if (t.allowedWriteAccounts.length != _expWrite.length) sawWidenedSet = true;
    // The value arm needs the same exact test the other three have. With only
    // the `> nm` bound above, a reader that returned fewer pairs than the
    // manifest wrote satisfied every property: the address loops below are
    // min-bounded, so at a shorter length they simply compare fewer entries.
    // That is the shrunken set the reader's own header says it never returns.
    if (t.valueAssets.length != _expAsset.length) sawWidenedSet = true;

    if (t.gasBudget != budget) sawBudgetDrift = true;

    // Per-draw, not campaign-wide. These flags are sticky by design, so
    // reading them here made the first GL03 or GL04 failure switch the
    // address comparisons off for every later draw, and a reader that both
    // confused kinds and returned wrong addresses reported only the first.
    bool lengthsDisagree =
      t.valueAssets.length != t.valueRecipients.length ||
      t.allowedCallTargets.length != _expectedCalls ||
      t.allowedDelegateTargets.length != _expectedDelegates;
    if (lengthsDisagree) return;

    for (uint256 i = 0; i < t.allowedCallTargets.length; i++) {
      if (t.allowedCallTargets[i] == address(0)) sawZeroAddress = true;
      if (t.allowedCallTargets[i] != _expCall[i]) sawWrongAddress = true;
    }
    for (uint256 i = 0; i < t.allowedDelegateTargets.length; i++) {
      if (t.allowedDelegateTargets[i] == address(0)) sawZeroAddress = true;
      if (t.allowedDelegateTargets[i] != _expDelegate[i]) sawWrongAddress = true;
    }
    for (uint256 i = 0; i < t.allowedWriteAccounts.length && i < _expWrite.length; i++) {
      if (t.allowedWriteAccounts[i] == address(0)) sawZeroAddress = true;
      if (t.allowedWriteAccounts[i] != _expWrite[i]) sawWrongAddress = true;
    }
    for (uint256 i = 0; i < t.valueAssets.length && i < _expAsset.length; i++) {
      if (t.valueAssets[i] == address(0) || t.valueRecipients[i] == address(0)) sawZeroAddress = true;
      if (t.valueAssets[i] != _expAsset[i]) sawWrongAddress = true;
      if (t.valueRecipients[i] != _expRecipient[i]) sawWrongAddress = true;
    }
  }

  /// @dev GL00 is the anti-vacuity guard, and it is the property to read
  ///      first. Every other property here is the negation of a ghost flag
  ///      that `_check` sets, and `_check` runs only when `resolveJson`
  ///      returns. A campaign whose every manifest reverts therefore satisfies
  ///      GL01 to GL09 without ever resolving anything -- which is exactly
  ///      what Echidna 2.3.3 and Medusa 1.5.1 produce, because neither
  ///      implements the `keyExistsJson`, `parseJsonUint` and
  ///      `parseJsonString` cheatcodes the reader is built on, so the first
  ///      cheatcode call reverts with empty return data. GL00 makes that
  ///      state a failure instead of nine green ticks.
  ///
  ///      The threshold is not a sampling argument. Every fourth draw is
  ///      constructed inside the subrange the reader accepts, so among any
  ///      eight attempts at least two were manifests the reader is obliged
  ///      to resolve; eight attempts with no success means the reader was
  ///      never reached. Eight also fits inside one sequence, which matters:
  ///      both engines reset this contract's state between sequences, so a
  ///      threshold above the configured sequence length never binds and the
  ///      guard would be as vacuous as the properties it protects.
  function echidna_GL00_the_reader_was_actually_reached() public view returns (bool) {
    return resolveAttempts < 8 || resolveSuccesses > 0;
  }

  function echidna_GL01_set_never_widened() public view returns (bool) { return !sawWidenedSet; }
  function echidna_GL02_no_zero_address() public view returns (bool) { return !sawZeroAddress; }
  function echidna_GL03_value_pairs_aligned() public view returns (bool) { return !sawPairMismatch; }
  function echidna_GL04_call_kind_carried_through() public view returns (bool) { return !sawKindConfusion; }
  function echidna_GL05_budget_is_the_actions_own() public view returns (bool) { return !sawBudgetDrift; }
  function echidna_GL06_unresolvable_fails_closed() public view returns (bool) { return !sawUnresolvableAccepted; }
  function echidna_GL07_blank_symbol_fails_closed() public view returns (bool) { return !sawBlankSymbolAccepted; }
  function echidna_GL08_duplicate_action_fails_closed() public view returns (bool) { return !sawDuplicateActionAccepted; }
  function echidna_GL09_every_entry_resolved_to_its_own_name() public view returns (bool) { return !sawWrongAddress; }

  /// @dev GL09 cannot stand in for this one. A reader with the ambiguity
  ///      refusal deleted splits `asset.e` at the dot and resolves `asset`,
  ///      which is the address the generator's own expectation holds for that
  ///      symbol choice, so the two agree and GL09 stays green on exactly the
  ///      mutant this property exists to kill.
  function echidna_GL10_ambiguous_name_fails_closed() public view returns (bool) { return !sawAmbiguousAccepted; }
}
