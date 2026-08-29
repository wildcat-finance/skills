// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";

/// @dev The stub adapter the campaign resolves through. It answers to the
///      five manifest names, and -- deliberately -- to the empty name as
///      well.
///
///      The empty name matters. GL07 asserts that a manifest carrying an
///      empty account symbol never resolves, and that refusal is meant to be
///      the *reader's*: S2-R1-03 was raised precisely because leaving it to
///      the adapter makes fail-closed behaviour the adapter's decision. An
///      adapter that does not know the empty name refuses it first, so the
///      reader's own guard is never the thing under test and GL07 holds even
///      with that guard deleted. Answering to the empty name with a live
///      address puts the guard back under test.
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
  }
  function resolveAccount(string calldata n) external view returns (bool, address) {
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

  uint256 internal _expectedCalls;
  uint256 internal _expectedDelegates;
  bool internal _anyUnresolvable;
  bool internal _anyBogus;
  bool internal _duplicateAction;
  bool internal _anyBlankSymbol;

  constructor() {
    reader = new ManifestReader();
    resolver = new FuzzResolver();
  }

  /// @dev Eight symbol choices: five the resolver knows, one it does not,
  ///      and two the reader's own grammar must refuse before the resolver is
  ///      ever asked -- the empty name and a whitespace-only name. The
  ///      resolver answers to both of those with a live address, so refusing
  ///      them is the reader's decision to get right, not the adapter's.
  function _sym(uint8 i) internal pure returns (string memory) {
    uint8 k = i % 8;
    if (k == 0) return "hook";
    if (k == 1) return "host";
    if (k == 2) return "asset";
    if (k == 3) return "roleProvider";
    if (k == 4) return "someAccount";
    if (k == 5) return "unknown";
    if (k == 6) return "";
    return " ";
  }
  function _symKnown(uint8 i) internal pure returns (bool) { return (i % 8) < 5; }
  function _symBlank(uint8 i) internal pure returns (bool) { return (i % 8) >= 6; }
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
      // choices 0 to 4 are the names the resolver knows, kinds 0 to 2 are the
      // three the reader admits. `fuzzResolve` says why every fourth draw is
      // built this way.
      if (valid) { s = s % 5; k = k % 3; }
      // A dotted suffix on an EMPTY symbol yields a leading dot, the
      // malformed-grammar case the reader must refuse itself.
      string memory target = dots ? string.concat(_sym(s), ".someFunction") : _sym(s);
      out = string.concat(out, i == 0 ? "" : ",", '{"target":"', target, '","kind":"', _kind(k), '"}');
      // Both shapes of the empty case reduce to the empty symbol: a bare
      // empty target, and an empty target carrying a dotted suffix, whose
      // symbol is the text before the first `.`. Now that the resolver
      // answers to the empty name, "empty" and "unresolvable" are disjoint
      // and each must be flagged as itself.
      if (_symBlank(s)) _anyBlankSymbol = true;
      else if (!_symKnown(s)) _anyUnresolvable = true;
      if ((k % 4) == 3) _anyBogus = true;
      else if ((k % 4) == 0) _expectedCalls++;
      else if ((k % 4) == 1) _expectedDelegates++;
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
      string memory slot = dots ? string.concat(_sym(s), ".field[key]") : _sym(s);
      out = string.concat(out, i == 0 ? "" : ",", '{"scope":"', _scope(sc), '","slot":"', slot, '"}');
      if ((sc % 4) == 3) _anyBogus = true;
      else if ((sc % 4) == 2) {
        if (_symBlank(s)) _anyBlankSymbol = true;
        else if (!_symKnown(s)) _anyUnresolvable = true;
      }
    }
    out = string.concat(out, "]");
  }

  function _buildMoves(uint256 nm, uint8 symSeed, bool valid) internal returns (string memory out) {
    out = "[";
    for (uint256 i = 0; i < nm; i++) {
      uint8 sa = uint8(uint256(keccak256(abi.encode(symSeed, i, "ma"))));
      uint8 sr = uint8(uint256(keccak256(abi.encode(symSeed, i, "mr"))));
      if (valid) { sa = sa % 5; sr = sr % 5; }
      out = string.concat(out, i == 0 ? "" : ",", '{"asset":"', _sym(sa), '","recipient":"', _sym(sr), '"}');
      if (_symBlank(sa) || _symBlank(sr)) _anyBlankSymbol = true;
      else if (!_symKnown(sa) || !_symKnown(sr)) _anyUnresolvable = true;
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
    _duplicateAction = duplicate;

    string memory threshold = string.concat(
      '{"action":"deposit","gasBudget":', _u(budget),
      ',"permittedCalls":', _buildCalls(nc, symSeed, kindSeed, dots, valid),
      ',"permittedStorageWrites":', _buildWrites(nw, symSeed, scopeSeed, dots, valid),
      ',"permittedValueMovements":', _buildMoves(nm, symSeed, valid), '}'
    );
    // A second threshold naming the same action. Selection is by name, so a
    // manifest that states one action twice has no single answer and must
    // refuse; without this the campaign only ever sees one threshold and the
    // whole of `_thresholdByAction` past its first match goes unexercised.
    string memory json = duplicate
      ? string.concat('{"thresholds":[', threshold, ',', threshold, ']}')
      : string.concat('{"thresholds":[', threshold, ']}');

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
    if (_duplicateAction) sawDuplicateActionAccepted = true;

    for (uint256 i = 0; i < t.allowedCallTargets.length; i++) {
      if (t.allowedCallTargets[i] == address(0)) sawZeroAddress = true;
    }
    for (uint256 i = 0; i < t.allowedDelegateTargets.length; i++) {
      if (t.allowedDelegateTargets[i] == address(0)) sawZeroAddress = true;
    }
    for (uint256 i = 0; i < t.allowedWriteAccounts.length; i++) {
      if (t.allowedWriteAccounts[i] == address(0)) sawZeroAddress = true;
    }
    for (uint256 i = 0; i < t.valueAssets.length; i++) {
      if (t.valueAssets[i] == address(0) || t.valueRecipients[i] == address(0)) sawZeroAddress = true;
    }

    if (t.allowedCallTargets.length > nc) sawWidenedSet = true;
    if (t.allowedDelegateTargets.length > nc) sawWidenedSet = true;
    if (t.allowedCallTargets.length + t.allowedDelegateTargets.length > nc) sawWidenedSet = true;
    if (t.allowedWriteAccounts.length > nw) sawWidenedSet = true;
    if (t.valueAssets.length > nm) sawWidenedSet = true;

    if (t.valueAssets.length != t.valueRecipients.length) sawPairMismatch = true;

    // The kind carried through: each set holds exactly its own kind's entries.
    if (t.allowedCallTargets.length != _expectedCalls) sawKindConfusion = true;
    if (t.allowedDelegateTargets.length != _expectedDelegates) sawKindConfusion = true;

    if (t.gasBudget != budget) sawBudgetDrift = true;
  }

  /// @dev GL00 is the anti-vacuity guard, and it is the property to read
  ///      first. Every other property here is the negation of a ghost flag
  ///      that `_check` sets, and `_check` runs only when `resolveJson`
  ///      returns. A campaign whose every manifest reverts therefore satisfies
  ///      GL01 to GL07 without ever resolving anything -- which is exactly
  ///      what Echidna 2.3.3 and Medusa 1.5.1 produce, because neither
  ///      implements the `keyExistsJson`, `parseJsonUint` and
  ///      `parseJsonString` cheatcodes the reader is built on, so the first
  ///      cheatcode call reverts with empty return data. GL00 makes that
  ///      state a failure instead of eight green ticks.
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
}
