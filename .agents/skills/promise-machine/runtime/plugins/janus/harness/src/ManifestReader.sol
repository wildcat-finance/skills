// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {Vm} from "./Vm.sol";

/// @dev The name-resolution seam between the manifest reader and one host
///      adapter. `ok` is false for a name the adapter does not know; a known
///      name must resolve to a non-zero address or the reader refuses it.
interface AccountResolver {
  function resolveAccount(string calldata name) external view returns (bool ok, address addr);
}

/// @dev One manifest threshold resolved to concrete gate inputs: the targets
///      the hook may reach with a plain `call`, the separate targets it may
///      reach with a `delegatecall`, the accounts whose storage it may write,
///      the (asset, recipient) pairs it may move value along, and the gas
///      budget of the named action.
///
///      The two call sets are deliberately not merged. A `delegatecall` runs
///      the target's code in the hook's own storage context, so admitting one
///      because the manifest permitted a plain `call` to the same address
///      would hand that address the hook's entire state -- a strictly wider
///      permit than the manifest wrote.
struct ResolvedThreshold {
  address[] allowedCallTargets;
  address[] allowedDelegateTargets;
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
///      The grammar stops there. A value movement's `asset` and `recipient`
///      carry no suffix in the schema, so their whole string is the name and
///      the dot is part of it: `USDC.e` is the bridged token, not `USDC`.
///
///      That reading also constrains the two paths the grammar does apply to.
///      A dot is an ordinary character in an account name, so `USDC.e` as a
///      call target or an external slot would bind the permit to `USDC` --
///      the same substitution, on the paths that split. The reader cannot
///      tell a suffix from a dotted name by looking, so it asks the adapter
///      about every other reading the string has -- one per dot after the
///      grammar's own, and the whole string last. If the adapter knows any of
///      them the manifest is ambiguous and the reader refuses rather than
///      choosing a prefix the author may not have meant. Asking only about
///      the whole string is not enough: `USDC.e.transfer` is a dotted account
///      carrying an ordinary function suffix, and its live reading is the
///      intermediate one. A real suffix is not a name an adapter holds, so
///      `roleProvider.getCredential` is unaffected.
///
///      Staticcall reading: a `staticcall` kind entry never admits a
///      state-changing call to its target. Only kinds `call` and
///      `delegatecall` enter the state-changing allowed set; gate 1 never
///      treats a read as an effect, and letting a staticcall entry admit
///      state-changing calls would widen the permit beyond what the manifest
///      said. Every entry's symbol, staticcall included, must still resolve,
///      so a misnamed entry aborts instead of vanishing.
///
///      Fail-closed posture: an action the manifest does not carry, a
///      duplicated action name, a symbol the adapter cannot resolve, a blank
///      account symbol, and a resolution to the zero address each revert with
///      a named error. The reader never returns a default or shrunken set,
///      and never admits an entry the manifest did not write.
///
///      Blank means empty or nothing but ASCII whitespace. Both arise the
///      same way, from a target or slot the grammar cannot take a name out
///      of -- `.getCredential`, or ` .field` -- and neither is a name the
///      manifest author wrote. Asking the adapter about one would make
///      failing closed the adapter's decision rather than the reader's,
///      which is what this guard exists to prevent.
///
///      Granularity boundary, stated because the header would otherwise read
///      stricter than the reader is: resolution is account-granular. A slot
///      expression such as `lenderStatus[lender]` contributes only its
///      account, and a target's function suffix contributes only its account,
///      so a permit the manifest wrote at slot or function granularity is
///      enforced at whole-account granularity. Gate 1 compares accounts and
///      never `StorageWriteObs.slot`, which is the stated non-goal this
///      matches. Call *kind* is the one dimension that is carried through,
///      because `call` and `delegatecall` differ in whose storage changes.
contract ManifestReader {
  Vm private constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

  error ActionNotInManifest(string action);
  error DuplicateActionInManifest(string action);
  /// @dev Raised for a symbol that is empty or nothing but ASCII whitespace.
  error EmptyAccountSymbol(string name);
  error UnresolvableSymbol(string symbol);
  error SymbolResolvesToZero(string symbol);
  error UnknownStorageScope(string scope);
  /// @dev Raised for a written name that carries a dot and whose whole string
  ///      the adapter also knows, so the grammar's prefix and the name the
  ///      manifest wrote are two different accounts.
  error AmbiguousAccountSymbol(string name);
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
    (t.allowedCallTargets, t.allowedDelegateTargets) = _resolveCalls(json, prefix, resolver);
    t.allowedWriteAccounts = _resolveStorageWrites(json, prefix, resolver);
    (t.valueAssets, t.valueRecipients) = _resolveValueMovements(json, prefix, resolver);
  }

  /// @dev Select a threshold by action name, never by position. A manifest
  ///      without the named action refuses; nothing falls back to
  ///      `.thresholds[0]`.
  ///
  ///      The scan does not stop at the first match. Two thresholds carrying
  ///      the same action name are accepted by the schema and by
  ///      `janus.py validate`, and returning the first would let array
  ///      position decide which permission set is in force -- position being
  ///      exactly what selection by name exists to avoid. A manifest that
  ///      states an action twice has no single answer, so it refuses.
  function _thresholdByAction(
    string memory json,
    string memory action
  ) private view returns (string memory prefix) {
    bool found = false;
    for (uint256 i = 0; vm.keyExistsJson(json, _indexed(".thresholds", i)); i++) {
      string memory candidate = _indexed(".thresholds", i);
      if (_eq(vm.parseJsonString(json, string.concat(candidate, ".action")), action)) {
        if (found) revert DuplicateActionInManifest(action);
        found = true;
        prefix = candidate;
      }
    }
    if (!found) revert ActionNotInManifest(action);
  }

  /// @dev Resolve `permittedCalls` into two disjoint sets, one per admitting
  ///      kind. Folding them together would make a `call` permit stand in for
  ///      a `delegatecall` permit, and those are not the same grant: a plain
  ///      call changes the target's storage, a delegatecall changes the
  ///      hook's. The manifest distinguishes them, so the resolved threshold
  ///      does too.
  function _resolveCalls(
    string memory json,
    string memory prefix,
    AccountResolver resolver
  ) private view returns (address[] memory targets, address[] memory delegateTargets) {
    string memory base = string.concat(prefix, ".permittedCalls");
    uint256 length = _arrayLength(json, base);
    targets = new address[](length);
    delegateTargets = new address[](length);
    uint256 admitted = 0;
    uint256 delegated = 0;
    for (uint256 i = 0; i < length; i++) {
      string memory entry = _indexed(base, i);
      address addr = _resolveDotted(
        vm.parseJsonString(json, string.concat(entry, ".target")),
        resolver
      );
      string memory kind = vm.parseJsonString(json, string.concat(entry, ".kind"));
      if (_eq(kind, "call")) {
        targets[admitted++] = addr;
      } else if (_eq(kind, "delegatecall")) {
        delegateTargets[delegated++] = addr;
      } else if (!_eq(kind, "staticcall")) {
        revert UnknownCallKind(kind);
      }
      // A staticcall entry resolves (so a misnamed one aborts) but admits
      // nothing into either state-changing allowed set.
    }
    targets = _shrink(targets, admitted);
    delegateTargets = _shrink(delegateTargets, delegated);
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
      if (_eq(scope, "hook")) {
        accounts[i] = _resolveSymbol("hook", resolver);
      } else if (_eq(scope, "host")) {
        accounts[i] = _resolveSymbol("host", resolver);
      } else if (_eq(scope, "external")) {
        accounts[i] = _resolveDotted(
          vm.parseJsonString(json, string.concat(entry, ".slot")),
          resolver
        );
      } else {
        revert UnknownStorageScope(scope);
      }
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
      // No `_symbolOf` here. The schema gives `asset` and `recipient` no
      // suffix to strip -- unlike a call target's function name and an
      // external slot's expression, both of which the schema documents -- so
      // a dot in one of these is part of the name. Splitting `USDC.e` bound
      // the permit to canonical `USDC` instead: an asset the manifest did not
      // name, chosen by the reader.
      assets[i] = _resolveSymbol(vm.parseJsonString(json, string.concat(entry, ".asset")), resolver);
      recipients[i] = _resolveSymbol(
        vm.parseJsonString(json, string.concat(entry, ".recipient")),
        resolver
      );
    }
  }

  /// @dev Resolve a written name on one of the two paths the dot grammar
  ///      applies to: a call target's `account.function`, or an external
  ///      slot's `account.expression`.
  ///
  ///      The grammar reads the prefix as the account and the suffix as
  ///      documentation. But a dot is also an ordinary character in an account
  ///      name -- which is exactly why the value path resolves its strings
  ///      whole, and why `USDC.e` is the bridged token there. On these two
  ///      paths the same string would silently bind to `USDC`: a permit on an
  ///      account the manifest did not name, chosen by the reader. That is the
  ///      defect the value path was fixed for, and it lives here too.
  ///
  ///      The reader cannot tell the two readings apart from the string alone,
  ///      so it asks. If the adapter knows the whole written name as well, the
  ///      manifest is ambiguous and the reader refuses instead of choosing.
  ///      A suffix that is genuinely documentation -- `roleProvider.getCredential`
  ///      -- is not a name any adapter holds, so nothing changes for it.
  ///
  ///      Two details of that question decide whether it can be answered
  ///      wrongly, and both are ordering.
  ///
  ///      The prefix is resolved first. `_resolveSymbol` is where a name the
  ///      adapter refuses, or answers for at the zero address, becomes the
  ///      reader's own named refusal; asking the ambiguity question ahead of
  ///      it would let `AmbiguousAccountSymbol` stand in for
  ///      `UnresolvableSymbol` and `SymbolResolvesToZero` and report the
  ///      second reading of a name whose first reading was already broken.
  ///
  ///      And the question is `ok` alone, not `ok` with a non-zero address.
  ///      A known name resolving to zero is a refusal this reader raises --
  ///      `SymbolResolvesToZero` exists for exactly that answer -- not an
  ///      absence it may read as "no second reading". Treating it as an
  ///      absence left the whole of S2-R3-01 alive in that corner: with an
  ///      adapter holding `USDC` at 0xC0 and answering `(true, address(0))`
  ///      for `USDC.e`, the value path refused the manifest and these two
  ///      paths bound the permit to 0xC0 -- one string, one resolver, two
  ///      different accounts, which is the defect the guard was added for.
  ///
  ///      The third detail is which names are asked about, and it is where the
  ///      question was drawn too narrowly again. A written name does not have
  ///      two readings; it has one per dot, plus the whole string. Asking only
  ///      about the whole string closes the guard on a name the adapter is
  ///      unlikely to hold and leaves it open on the shape this manifest
  ///      actually writes: every dotted target here is `account.function`, so
  ///      a dotted *account* written with its function suffix is
  ///      `account.part.function`, and the reading the author meant is the
  ///      intermediate one. With `USDC` at 0xC0 and `USDC.e` at 0xCE,
  ///      `USDC.e` refused and `USDC.e.transfer` bound the permit to 0xC0 --
  ///      the bridged token the manifest named unpermitted, and one it never
  ///      named permitted instead. So every dot boundary beyond the grammar's
  ///      own is asked about, and the whole string is simply the last of them.
  function _resolveDotted(
    string memory written,
    AccountResolver resolver
  ) private view returns (address addr) {
    string memory symbol = _symbolOf(written);
    // No blank guard of its own. This function used to carry one, because it
    // asked the adapter about `written` before resolving the prefix and a
    // malformed `.getCredential` had to be the reader's refusal rather than
    // the adapter's. Resolving the prefix first moves that guarantee into
    // `_resolveSymbol`, whose first act is the same blank check, so a copy
    // here is a line no mutant can kill -- deleting it changed nothing in the
    // whole suite. The ordering is what keeps the adapter from being asked
    // about a blank symbol; the duplicate only looked like it did.
    addr = _resolveSymbol(symbol, resolver);
    _refuseASecondReading(written, bytes(symbol).length, resolver);
  }

  /// @dev Refuse a written name that has more than one reading. The grammar's
  ///      own reading is the text before the first dot, and it has already
  ///      been resolved; every other reading ends at a later dot, or is the
  ///      whole string. If the adapter answers `ok` for any of them the
  ///      manifest is ambiguous and the reader refuses rather than choosing.
  ///
  ///      `head` is the grammar's prefix length rather than the prefix itself,
  ///      so a dot-free name is the single comparison `head == b.length` and
  ///      needs no string equality. That case returns before any candidate is
  ///      built, which is what keeps `hook`, `host` and a bracketed slot
  ///      expression from ever reaching the adapter twice.
  function _refuseASecondReading(
    string memory written,
    uint256 head,
    AccountResolver resolver
  ) private view {
    bytes memory b = bytes(written);
    if (head == b.length) return; // no dot: the grammar has the only reading
    for (uint256 i = head + 1; i <= b.length; i++) {
      if (i != b.length && b[i] != ".") continue;
      bytes memory candidate = new bytes(i);
      for (uint256 j = 0; j < i; j++) {
        candidate[j] = b[j];
      }
      (bool known, ) = resolver.resolveAccount(string(candidate));
      if (known) revert AmbiguousAccountSymbol(written);
    }
  }

  function _resolveSymbol(
    string memory symbol,
    AccountResolver resolver
  ) private view returns (address addr) {
    // A blank symbol is not a name the adapter should be asked about. It
    // arises from a malformed target or slot the grammar cannot take a name
    // out of -- a leading `.`, or whitespace ahead of one -- and whether it
    // then fails closed would be the adapter's decision, not the reader's.
    // The reader owns its own grammar, so it refuses here. Whitespace counts:
    // ` ` is no more a name the manifest author wrote than `` is, and an
    // adapter that trims a name before looking it up would admit it.
    if (_isBlank(symbol)) revert EmptyAccountSymbol(symbol);
    bool ok;
    (ok, addr) = resolver.resolveAccount(symbol);
    if (!ok) revert UnresolvableSymbol(symbol);
    if (addr == address(0)) revert SymbolResolvesToZero(symbol);
  }

  /// @dev True for a symbol that is not a name at all: no bytes, or nothing
  ///      above ASCII space. That covers the empty string, runs of spaces, and
  ///      every C0 control byte -- tab, line feed, vertical tab, form feed,
  ///      carriage return and NUL among them, each of which a JSON escape can
  ///      put into a manifest and none of which a manifest author writes as a
  ///      name. Enumerating four of them was not enough: 0x0B, 0x0C and 0x00
  ///      all reached the adapter as names under the narrower test.
  ///
  ///      Multi-byte whitespace is deliberately not folded in. Every byte of a
  ///      multi-byte UTF-8 sequence is at least 0xC0 or between 0x80 and 0xBF,
  ///      so this decides on bytes without decoding, and a symbol carrying any
  ///      byte above 0x20 is a name the adapter may answer about or refuse.
  function _isBlank(string memory s) private pure returns (bool) {
    bytes memory b = bytes(s);
    for (uint256 i = 0; i < b.length; i++) {
      if (uint8(b[i]) > 0x20) return false;
    }
    return true;
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
