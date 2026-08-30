// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {StateDeltaRecorder} from "./StateDeltaRecorder.sol";
import {HostAdapter} from "./HostAdapter.sol";
import {Vm} from "./Vm.sol";

/// @dev The gate engine. It drives one action through a host adapter, records
///      the delta around it, and offers the checks a conformance test uses to
///      compare the delta against a manifest. It attributes an effect to the
///      hook by the recorded accessor: a call the hook made is one whose
///      accessor is the hook address, which is how gate 1 tells the hook's own
///      calls apart from the host's.
abstract contract JanusHarness is StateDeltaRecorder {
  Vm private constant _hvm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

  error NoSequencesExercised();

  struct DriveResult {
    bool reverted;
    bytes revertData;
    Delta delta;
    uint256 valueBefore;
    uint256 valueAfter;
  }

  /// @dev One conformance finding, the unit the reports render.
  struct Finding {
    uint256 gate;
    string action;
    string hook;
    string detail;
  }

  /// @dev Drive an action and record the state delta around it. A revert is
  ///      caught so the harness can inspect the delta and the rollback rather
  ///      than aborting the test.
  function _drive(
    HostAdapter adapter,
    string memory action,
    address caller,
    bytes memory params
  ) internal returns (DriveResult memory result) {
    result.valueBefore = adapter.valueSnapshot();
    _beginRecording();
    try adapter.driveAction(action, caller, params) {
      result.reverted = false;
    } catch (bytes memory data) {
      result.reverted = true;
      result.revertData = data;
    }
    result.delta = _endRecording(0);
    result.valueAfter = adapter.valueSnapshot();
  }

  /// @dev The hook's causal subtree, by call-frame depth. The recorder lists
  ///      account accesses in DFS pre-order, so the calls the hook made are the
  ///      contiguous run after the host-to-hook entry frame with a strictly
  ///      greater depth, up to where the depth returns to the entry. Depth is
  ///      the field that tells the hook's descendants apart from the host's own
  ///      sibling calls: attributing by the immediate accessor would miss a
  ///      laundered call one hop out, while attributing by a naive
  ///      accessor-closure would wrongly sweep in the host's base-action calls
  ///      once a hook merely read host state.
  function _hookAttributed(
    Delta memory delta,
    address hookAddr
  ) internal pure returns (bool[] memory attributed) {
    uint256 n = delta.calls.length;
    attributed = new bool[](n);
    for (uint256 i; i < n; ++i) {
      if (delta.calls[i].target != hookAddr) continue; // a host-to-hook entry
      uint64 entryDepth = delta.calls[i].depth;
      for (uint256 j = i + 1; j < n; ++j) {
        if (delta.calls[j].depth <= entryDepth) break; // subtree closed
        attributed[j] = true;
      }
    }
  }

  /// @dev The number of state-changing calls the hook caused. Static calls are
  ///      reads, not effects, so they do not count.
  function _hookCallCount(Delta memory delta, address hookAddr) internal pure returns (uint256 n) {
    bool[] memory attributed = _hookAttributed(delta, hookAddr);
    for (uint256 i; i < attributed.length; ++i) {
      if (attributed[i] && _isStateChanging(delta.calls[i].kind)) ++n;
    }
  }

  /// @dev Gate 1, calls: every state-changing call the hook caused, anywhere in
  ///      its causal subtree, targets an allowed address. A static call is a
  ///      read and is never an effect, so a hook may read any address; only a
  ///      call that could change state is enumerated.
  ///
  ///      `allowed` is the manifest's own set. `ManifestReader` selects the
  ///      threshold by action name and resolves each `permittedCalls` target
  ///      through the host adapter's name table, so the addresses compared here
  ///      are the ones the manifest wrote rather than a literal a test author
  ///      chose. A `staticcall` entry resolves and admits nothing, which is why
  ///      the manifest can name a read target without widening this set.
  ///
  ///      Passing a literal is still possible and two engine-mechanics tests do
  ///      it deliberately, to construct a permitted forwarder and an empty set
  ///      that the manifest does not describe. Every conformance verdict takes
  ///      its set from resolution.
  function _gate1_hookCallsWithinAllowed(
    Delta memory delta,
    address hookAddr,
    address[] memory allowed
  ) internal pure returns (bool) {
    bool[] memory attributed = _hookAttributed(delta, hookAddr);
    for (uint256 i; i < delta.calls.length; ++i) {
      if (!attributed[i] || !_isStateChanging(delta.calls[i].kind)) continue;
      if (!_inSet(delta.calls[i].target, allowed)) return false;
    }
    return true;
  }

  /// @dev Gate 1, storage: the hook may write only storage the manifest lists.
  ///      A write to any account outside `allowedWriteAccounts` that the hook
  ///      caused, meaning the written account is one its subtree made a
  ///      state-changing call into, is a storage effect the manifest did not
  ///      enumerate.
  ///
  ///      `allowedWriteAccounts` is resolved rather than assembled. A
  ///      `permittedStorageWrites` entry of scope `hook` resolves the symbol
  ///      `hook` through the adapter, scope `host` resolves `host`, and scope
  ///      `external` resolves its slot expression's account prefix. The hook's
  ///      own address therefore reaches this gate because the manifest said
  ///      `hook`, not because a test passed it in.
  ///
  ///      The granularity is account, not slot. A manifest entry naming
  ///      `lenderStatus[lender]` contributes only the account that holds it, so
  ///      two hook-scope entries resolve to the same address twice and a permit
  ///      written per slot is enforced per account. That is the stated
  ///      non-goal this matches: `StorageWriteObs.slot` is recorded and never
  ///      compared here.
  function _gate1_hookStorageWithinScopes(
    Delta memory delta,
    address hookAddr,
    address[] memory allowedWriteAccounts
  ) internal pure returns (bool) {
    bool[] memory attributed = _hookAttributed(delta, hookAddr);
    for (uint256 w; w < delta.writes.length; ++w) {
      address acct = delta.writes[w].account;
      if (_inSet(acct, allowedWriteAccounts)) continue;
      // A write the hook caused: the written account is one its subtree called.
      for (uint256 i; i < delta.calls.length; ++i) {
        if (attributed[i] && _isStateChanging(delta.calls[i].kind) && delta.calls[i].target == acct) {
          return false;
        }
      }
    }
    return true;
  }

  /// @dev The fresh value the hook caused to move, across its causal subtree,
  ///      counting only kinds that move fresh value.
  function _hookValueMoved(Delta memory delta, address hookAddr) internal pure returns (uint256 v) {
    bool[] memory attributed = _hookAttributed(delta, hookAddr);
    for (uint256 i; i < delta.calls.length; ++i) {
      if (attributed[i] && _movesValue(delta.calls[i].kind)) v += delta.calls[i].value;
    }
  }

  function _isStateChanging(Vm.AccountAccessKind kind) internal pure returns (bool) {
    return kind != Vm.AccountAccessKind.StaticCall;
  }

  function _inSet(address needle, address[] memory set) private pure returns (bool) {
    for (uint256 i; i < set.length; ++i) {
      if (set[i] == needle) return true;
    }
    return false;
  }

  /// @dev Whether a recording captured any effect at all. A gate for an action
  ///      expected to do something must assert this, so it cannot pass
  ///      vacuously on an action that reverted or did nothing.
  function _deltaHasEffects(Delta memory delta) internal pure returns (bool) {
    return delta.writes.length > 0 || delta.calls.length > 0;
  }

  /// @dev A conformance run must have exercised at least one sequence; a run
  ///      that drove nothing is a failure, not a vacuous pass.
  function _requireExercised(uint256 sequences) internal pure {
    if (sequences == 0) revert NoSequencesExercised();
  }

  /// @dev Render a findings set to the report interchange JSON and write it
  ///      through the scoped filesystem cheatcode. The Python reporter renders
  ///      the human and SARIF outputs from this file.
  function _writeFindings(
    string memory path,
    string memory host,
    string memory manifest,
    uint256 sequences,
    Finding[] memory findings
  ) internal {
    _hvm.writeFile(path, _findingsJson(host, manifest, sequences, findings));
  }

  function _findingsJson(
    string memory host,
    string memory manifest,
    uint256 sequences,
    Finding[] memory findings
  ) internal pure returns (string memory json) {
    string memory arr = "[";
    for (uint256 i; i < findings.length; ++i) {
      arr = string.concat(
        arr,
        i == 0 ? "" : ",",
        '{"gate":',
        _uintToString(findings[i].gate),
        ',"action":"',
        _escape(findings[i].action),
        '","hook":"',
        _escape(findings[i].hook),
        '","detail":"',
        _escape(findings[i].detail),
        '"}'
      );
    }
    arr = string.concat(arr, "]");
    json = string.concat(
      '{"host":"',
      host,
      '","manifest":"',
      manifest,
      '","sequences":',
      _uintToString(sequences),
      ',"findings":',
      arr,
      "}"
    );
  }

  /// @dev Escape a string for embedding in a JSON string literal, so a field
  ///      carrying a quote, backslash, or control character cannot end the
  ///      literal early and inject or hide a field. The reporter parses the
  ///      result, so an unescaped quote would let one field rewrite another.
  function _escape(string memory input) internal pure returns (string memory) {
    bytes memory b = bytes(input);
    bytes memory out;
    for (uint256 i; i < b.length; ++i) {
      bytes1 c = b[i];
      if (c == '"') {
        out = abi.encodePacked(out, '\\"');
      } else if (c == "\\") {
        out = abi.encodePacked(out, "\\\\");
      } else if (uint8(c) < 0x20) {
        // Control characters, including newline and tab, as \u00XX.
        out = abi.encodePacked(out, "\\u00", _hexNibble(uint8(c) >> 4), _hexNibble(uint8(c) & 0x0f));
      } else {
        out = abi.encodePacked(out, c);
      }
    }
    return string(out);
  }

  function _hexNibble(uint8 nibble) private pure returns (bytes1) {
    return bytes1(nibble < 10 ? 48 + nibble : 87 + nibble);
  }

  function _uintToString(uint256 value) internal pure returns (string memory) {
    if (value == 0) return "0";
    uint256 temp = value;
    uint256 digits;
    while (temp != 0) {
      digits++;
      temp /= 10;
    }
    bytes memory buffer = new bytes(digits);
    while (value != 0) {
      digits -= 1;
      buffer[digits] = bytes1(uint8(48 + (value % 10)));
      value /= 10;
    }
    return string(buffer);
  }
}
