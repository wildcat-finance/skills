// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {Vm} from "./Vm.sol";

/// @dev The name-resolution seam between the manifest reader and one host
///      adapter. `ok` is false for a name the adapter does not know; a known
///      name must resolve to a non-zero address or the reader refuses it.
interface AccountResolver {
  function resolveAccount(string calldata name) external view returns (bool ok, address addr);
}

/// @dev One manifest threshold resolved to concrete gate inputs: the
///      state-changing call targets the hook may reach, the accounts whose
///      storage it may write, the (asset, recipient) pairs it may move value
///      along, and the gas budget of the named action.
struct ResolvedThreshold {
  address[] allowedCallTargets;
  address[] allowedWriteAccounts;
  address[] valueAssets;
  address[] valueRecipients;
  uint256 gasBudget;
}

/// @dev Turns one manifest file plus one host adapter into the gate inputs
///      for a named action, failing closed.
///
///      Symbol grammar: the account symbol of a call target or an external
///      storage slot is the text before the first `.`; the suffix (a function
///      name such as `getCredential`, or a slot expression) is documentation
///      and is never resolved. A target with no `.` is its own symbol.
///      Storage scope `hook` resolves the symbol `hook` and scope `host` the
///      symbol `host`, both through the adapter; scope `external` resolves
///      the symbol prefix of its slot string.
///
///      Staticcall reading: a `staticcall` kind entry never admits a
///      state-changing call to its target. Only kinds `call` and
///      `delegatecall` enter the state-changing allowed set; gate 1 never
///      treats a read as an effect, and letting a staticcall entry admit
///      state-changing calls would widen the permit beyond what the manifest
///      said. Every entry's symbol, staticcall included, must still resolve,
///      so a misnamed entry aborts instead of vanishing.
///
///      Fail-closed posture: an action the manifest does not carry, a symbol
///      the adapter cannot resolve, and a resolution to the zero address each
///      revert with a named error. The reader never returns a default,
///      shrunken, or widened set.
contract ManifestReader {
  Vm private constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

  error ActionNotInManifest(string action);
  error UnresolvableSymbol(string symbol);
  error SymbolResolvesToZero(string symbol);
  error UnknownStorageScope(string scope);
  error UnknownCallKind(string kind);

  /// @dev Resolve the named action's threshold from a manifest file, read
  ///      through the scoped filesystem cheatcode.
  function resolveFile(
    string memory path,
    string memory action,
    AccountResolver resolver
  ) external view returns (ResolvedThreshold memory t) {
    return _resolve(vm.readFile(path), action, resolver);
  }

  /// @dev Resolve the named action's threshold from manifest JSON already in
  ///      hand; the file entry point above is this over `vm.readFile`.
  function resolveJson(
    string memory json,
    string memory action,
    AccountResolver resolver
  ) external view returns (ResolvedThreshold memory t) {
    return _resolve(json, action, resolver);
  }

  function _resolve(
    string memory json,
    string memory action,
    AccountResolver resolver
  ) private view returns (ResolvedThreshold memory t) {
    string memory prefix = _thresholdByAction(json, action);
    t.gasBudget = vm.parseJsonUint(json, string.concat(prefix, ".gasBudget"));
    t.allowedCallTargets = _resolveCalls(json, prefix, resolver);
    t.allowedWriteAccounts = _resolveStorageWrites(json, prefix, resolver);
    (t.valueAssets, t.valueRecipients) = _resolveValueMovements(json, prefix, resolver);
  }

  /// @dev Select a threshold by action name, never by position. A manifest
  ///      without the named action refuses; nothing falls back to
  ///      `.thresholds[0]`.
  function _thresholdByAction(
    string memory json,
    string memory action
  ) private view returns (string memory prefix) {
    for (uint256 i = 0; vm.keyExistsJson(json, _indexed(".thresholds", i)); i++) {
      prefix = _indexed(".thresholds", i);
      if (_eq(vm.parseJsonString(json, string.concat(prefix, ".action")), action)) {
        return prefix;
      }
    }
    revert ActionNotInManifest(action);
  }

  function _resolveCalls(
    string memory json,
    string memory prefix,
    AccountResolver resolver
  ) private view returns (address[] memory targets) {
    string memory base = string.concat(prefix, ".permittedCalls");
    uint256 length = _arrayLength(json, base);
    targets = new address[](length);
    uint256 admitted = 0;
    for (uint256 i = 0; i < length; i++) {
      string memory entry = _indexed(base, i);
      string memory symbol = _symbolOf(vm.parseJsonString(json, string.concat(entry, ".target")));
      address addr = _resolveSymbol(symbol, resolver);
      string memory kind = vm.parseJsonString(json, string.concat(entry, ".kind"));
      if (_eq(kind, "call") || _eq(kind, "delegatecall")) {
        targets[admitted++] = addr;
      } else if (!_eq(kind, "staticcall")) {
        revert UnknownCallKind(kind);
      }
      // A staticcall entry resolves (so a misnamed one aborts) but admits
      // nothing into the state-changing allowed set.
    }
    targets = _shrink(targets, admitted);
  }

  function _resolveStorageWrites(
    string memory json,
    string memory prefix,
    AccountResolver resolver
  ) private view returns (address[] memory accounts) {
    string memory base = string.concat(prefix, ".permittedStorageWrites");
    uint256 length = _arrayLength(json, base);
    accounts = new address[](length);
    for (uint256 i = 0; i < length; i++) {
      string memory entry = _indexed(base, i);
      string memory scope = vm.parseJsonString(json, string.concat(entry, ".scope"));
      string memory symbol;
      if (_eq(scope, "hook")) {
        symbol = "hook";
      } else if (_eq(scope, "host")) {
        symbol = "host";
      } else if (_eq(scope, "external")) {
        symbol = _symbolOf(vm.parseJsonString(json, string.concat(entry, ".slot")));
      } else {
        revert UnknownStorageScope(scope);
      }
      accounts[i] = _resolveSymbol(symbol, resolver);
    }
  }

  function _resolveValueMovements(
    string memory json,
    string memory prefix,
    AccountResolver resolver
  ) private view returns (address[] memory assets, address[] memory recipients) {
    string memory base = string.concat(prefix, ".permittedValueMovements");
    uint256 length = _arrayLength(json, base);
    assets = new address[](length);
    recipients = new address[](length);
    for (uint256 i = 0; i < length; i++) {
      string memory entry = _indexed(base, i);
      assets[i] = _resolveSymbol(
        _symbolOf(vm.parseJsonString(json, string.concat(entry, ".asset"))),
        resolver
      );
      recipients[i] = _resolveSymbol(
        _symbolOf(vm.parseJsonString(json, string.concat(entry, ".recipient"))),
        resolver
      );
    }
  }

  function _resolveSymbol(
    string memory symbol,
    AccountResolver resolver
  ) private view returns (address addr) {
    bool ok;
    (ok, addr) = resolver.resolveAccount(symbol);
    if (!ok) revert UnresolvableSymbol(symbol);
    if (addr == address(0)) revert SymbolResolvesToZero(symbol);
  }

  /// @dev The account symbol: the text before the first `.`, or the whole
  ///      string when it carries none.
  function _symbolOf(string memory name) private pure returns (string memory) {
    bytes memory b = bytes(name);
    for (uint256 i = 0; i < b.length; i++) {
      if (b[i] == ".") {
        bytes memory head = new bytes(i);
        for (uint256 j = 0; j < i; j++) {
          head[j] = b[j];
        }
        return string(head);
      }
    }
    return name;
  }

  function _shrink(
    address[] memory arr,
    uint256 n
  ) private pure returns (address[] memory out) {
    out = new address[](n);
    for (uint256 i = 0; i < n; i++) {
      out[i] = arr[i];
    }
  }

  function _arrayLength(string memory json, string memory key) private view returns (uint256 n) {
    while (vm.keyExistsJson(json, _indexed(key, n))) {
      n++;
    }
  }

  function _indexed(string memory base, uint256 i) private pure returns (string memory) {
    return string.concat(base, "[", _utoa(i), "]");
  }

  function _utoa(uint256 v) private pure returns (string memory) {
    if (v == 0) return "0";
    uint256 digits = 0;
    for (uint256 t = v; t != 0; t /= 10) {
      digits++;
    }
    bytes memory b = new bytes(digits);
    for (; v != 0; v /= 10) {
      b[--digits] = bytes1(uint8(48 + (v % 10)));
    }
    return string(b);
  }

  function _eq(string memory a, string memory b) private pure returns (bool) {
    return keccak256(bytes(a)) == keccak256(bytes(b));
  }
}
