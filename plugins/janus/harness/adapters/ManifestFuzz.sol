// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {AccountResolver, ManifestReader, ResolvedThreshold} from "../src/ManifestReader.sol";

contract FuzzResolver is AccountResolver {
  mapping(bytes32 => address) private t;
  constructor() {
    t[keccak256("hook")] = address(0xA1);
    t[keccak256("host")] = address(0xA2);
    t[keccak256("asset")] = address(0xA3);
    t[keccak256("roleProvider")] = address(0xA4);
    t[keccak256("someAccount")] = address(0xA5);
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
  bool public sawEmptySymbolAccepted;

  uint256 internal _expectedCalls;
  uint256 internal _expectedDelegates;
  bool internal _anyUnresolvable;
  bool internal _anyBogus;
  bool internal _anyEmptySymbol;

  constructor() {
    reader = new ManifestReader();
    resolver = new FuzzResolver();
  }

  function _sym(uint8 i) internal pure returns (string memory) {
    uint8 k = i % 7;
    if (k == 0) return "hook";
    if (k == 1) return "host";
    if (k == 2) return "asset";
    if (k == 3) return "roleProvider";
    if (k == 4) return "someAccount";
    if (k == 5) return "unknown";
    return "";
  }
  function _symKnown(uint8 i) internal pure returns (bool) { return (i % 7) < 5; }
  function _symEmpty(uint8 i) internal pure returns (bool) { return (i % 7) == 6; }
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

  function _buildCalls(uint256 nc, uint8 symSeed, uint8 kindSeed, bool dots)
    internal returns (string memory out)
  {
    out = "[";
    for (uint256 i = 0; i < nc; i++) {
      uint8 s = uint8(uint256(keccak256(abi.encode(symSeed, i, "c"))));
      uint8 k = uint8(uint256(keccak256(abi.encode(kindSeed, i, "c"))));
      // A dotted suffix on an EMPTY symbol yields a leading dot, the
      // malformed-grammar case the reader must refuse itself.
      string memory target = dots ? string.concat(_sym(s), ".someFunction") : _sym(s);
      out = string.concat(out, i == 0 ? "" : ",", '{"target":"', target, '","kind":"', _kind(k), '"}');
      if (_symEmpty(s) && dots) _anyEmptySymbol = true;
      else if (!_symKnown(s)) _anyUnresolvable = true;
      if (!dots && _symEmpty(s)) _anyEmptySymbol = true;
      if ((k % 4) == 3) _anyBogus = true;
      else if ((k % 4) == 0) _expectedCalls++;
      else if ((k % 4) == 1) _expectedDelegates++;
    }
    out = string.concat(out, "]");
  }

  function _buildWrites(uint256 nw, uint8 symSeed, uint8 scopeSeed, bool dots)
    internal returns (string memory out)
  {
    out = "[";
    for (uint256 i = 0; i < nw; i++) {
      uint8 s = uint8(uint256(keccak256(abi.encode(symSeed, i, "w"))));
      uint8 sc = uint8(uint256(keccak256(abi.encode(scopeSeed, i, "w"))));
      string memory slot = dots ? string.concat(_sym(s), ".field[key]") : _sym(s);
      out = string.concat(out, i == 0 ? "" : ",", '{"scope":"', _scope(sc), '","slot":"', slot, '"}');
      if ((sc % 4) == 3) _anyBogus = true;
      else if ((sc % 4) == 2) {
        if (_symEmpty(s)) _anyEmptySymbol = true;
        else if (!_symKnown(s)) _anyUnresolvable = true;
      }
    }
    out = string.concat(out, "]");
  }

  function _buildMoves(uint256 nm, uint8 symSeed) internal returns (string memory out) {
    out = "[";
    for (uint256 i = 0; i < nm; i++) {
      uint8 sa = uint8(uint256(keccak256(abi.encode(symSeed, i, "ma"))));
      uint8 sr = uint8(uint256(keccak256(abi.encode(symSeed, i, "mr"))));
      out = string.concat(out, i == 0 ? "" : ",", '{"asset":"', _sym(sa), '","recipient":"', _sym(sr), '"}');
      if (_symEmpty(sa) || _symEmpty(sr)) _anyEmptySymbol = true;
      else if (!_symKnown(sa) || !_symKnown(sr)) _anyUnresolvable = true;
    }
    out = string.concat(out, "]");
  }

  function fuzzResolve(
    uint8 nCalls, uint8 nWrites, uint8 nMoves,
    uint8 symSeed, uint8 kindSeed, uint8 scopeSeed,
    uint64 budget, bool dots
  ) public {
    uint256 nc = nCalls % 4;
    uint256 nw = nWrites % 4;
    uint256 nm = nMoves % 3;
    if (budget == 0) budget = 1;

    _expectedCalls = 0; _expectedDelegates = 0;
    _anyUnresolvable = false; _anyBogus = false; _anyEmptySymbol = false;

    string memory json = string.concat(
      '{"thresholds":[{"action":"deposit","gasBudget":', _u(budget),
      ',"permittedCalls":', _buildCalls(nc, symSeed, kindSeed, dots),
      ',"permittedStorageWrites":', _buildWrites(nw, symSeed, scopeSeed, dots),
      ',"permittedValueMovements":', _buildMoves(nm, symSeed), '}]}'
    );

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
    if (_anyEmptySymbol) sawEmptySymbolAccepted = true;

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

  function echidna_GL01_set_never_widened() public view returns (bool) { return !sawWidenedSet; }
  function echidna_GL02_no_zero_address() public view returns (bool) { return !sawZeroAddress; }
  function echidna_GL03_value_pairs_aligned() public view returns (bool) { return !sawPairMismatch; }
  function echidna_GL04_call_kind_carried_through() public view returns (bool) { return !sawKindConfusion; }
  function echidna_GL05_budget_is_the_actions_own() public view returns (bool) { return !sawBudgetDrift; }
  function echidna_GL06_unresolvable_fails_closed() public view returns (bool) { return !sawUnresolvableAccepted; }
  function echidna_GL07_empty_symbol_fails_closed() public view returns (bool) { return !sawEmptySymbolAccepted; }
}
