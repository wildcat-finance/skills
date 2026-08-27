// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {Vm} from "./Vm.sol";

/// @dev The trust root of the suite. It records the real effects that occur
///      across a driven action, so a later gate can compare them with the
///      manifest. It records faithfully and does not judge: attribution of an
///      effect to the hook and comparison against a manifest belong to the
///      gate engine. What it guarantees is that a delta it returns was taken
///      from a real recording; a missed recording fails closed rather than
///      reading as a clean, effect-free threshold.
abstract contract StateDeltaRecorder {
  Vm private constant _vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

  error RecordingNotStarted();
  error RecordingAlreadyStarted();

  struct StorageWriteObs {
    address account;
    bytes32 slot;
  }

  struct CallObs {
    address target;
    address accessor;
    Vm.AccountAccessKind kind;
    uint256 value;
    uint64 depth;
  }

  struct Delta {
    bool taken;
    uint256 gasUsed;
    StorageWriteObs[] writes;
    CallObs[] calls;
  }

  bool private _recording;

  function _beginRecording() internal {
    // A second begin while one is open would reset Foundry's state-diff buffer
    // and silently drop everything recorded so far. Fail closed on both misuse
    // directions, not only the missing-begin one.
    if (_recording) revert RecordingAlreadyStarted();
    _recording = true;
    _vm.startStateDiffRecording();
  }

  /// @dev Close a recording and flatten the account accesses into observed
  ///      storage writes and external calls. `gasUsed` is measured by the
  ///      caller around the driven action. Reverts if no recording is open, so
  ///      a harness that forgot to start one cannot mistake silence for a clean
  ///      threshold.
  function _endRecording(uint256 gasUsed) internal returns (Delta memory delta) {
    if (!_recording) revert RecordingNotStarted();
    _recording = false;

    Vm.AccountAccess[] memory accesses = _vm.stopAndReturnStateDiff();

    uint256 writeCount;
    uint256 callCount;
    for (uint256 i; i < accesses.length; ++i) {
      Vm.AccountAccess memory a = accesses[i];
      if (a.reverted) continue;
      if (_reachesAccount(a.kind)) ++callCount;
      for (uint256 j; j < a.storageAccesses.length; ++j) {
        Vm.StorageAccess memory s = a.storageAccesses[j];
        if (s.isWrite && !s.reverted) ++writeCount;
      }
    }

    delta.taken = true;
    delta.gasUsed = gasUsed;
    delta.writes = new StorageWriteObs[](writeCount);
    delta.calls = new CallObs[](callCount);

    uint256 w;
    uint256 c;
    for (uint256 i; i < accesses.length; ++i) {
      Vm.AccountAccess memory a = accesses[i];
      if (a.reverted) continue;
      if (_reachesAccount(a.kind)) {
        delta.calls[c++] = CallObs({
          target: a.account,
          accessor: a.accessor,
          kind: a.kind,
          value: a.value,
          depth: a.depth
        });
      }
      for (uint256 j; j < a.storageAccesses.length; ++j) {
        Vm.StorageAccess memory s = a.storageAccesses[j];
        if (s.isWrite && !s.reverted) {
          delta.writes[w++] = StorageWriteObs({account: s.account, slot: s.slot});
        }
      }
    }
  }

  /// @dev Account accesses that reach another account and belong in the calls
  ///      list: the four message-call kinds plus create and selfdestruct, both
  ///      of which carry a target address and can move value. Leaving create
  ///      and selfdestruct out let a hook move value invisibly by deploying
  ///      with an endowment or sweeping its balance.
  function _reachesAccount(Vm.AccountAccessKind kind) private pure returns (bool) {
    return
      kind == Vm.AccountAccessKind.Call ||
      kind == Vm.AccountAccessKind.StaticCall ||
      kind == Vm.AccountAccessKind.DelegateCall ||
      kind == Vm.AccountAccessKind.CallCode ||
      kind == Vm.AccountAccessKind.Create ||
      kind == Vm.AccountAccessKind.SelfDestruct;
  }

  /// @dev Whether a kind moves fresh value. A delegatecall inherits the
  ///      enclosing call's value, so summing it would double-count; a
  ///      staticcall can move none. Create and selfdestruct do move value.
  function _movesValue(Vm.AccountAccessKind kind) internal pure returns (bool) {
    return
      kind == Vm.AccountAccessKind.Call ||
      kind == Vm.AccountAccessKind.CallCode ||
      kind == Vm.AccountAccessKind.Create ||
      kind == Vm.AccountAccessKind.SelfDestruct;
  }

  /// @dev Whether the delta records any write to `account`. The gate engine
  ///      uses helpers like this to test the observed delta against a manifest.
  function _wroteTo(Delta memory delta, address account) internal pure returns (bool) {
    for (uint256 i; i < delta.writes.length; ++i) {
      if (delta.writes[i].account == account) return true;
    }
    return false;
  }

  /// @dev Whether the delta records an external call to `target`.
  function _calledInto(Delta memory delta, address target) internal pure returns (bool) {
    for (uint256 i; i < delta.calls.length; ++i) {
      if (delta.calls[i].target == target) return true;
    }
    return false;
  }

  /// @dev The total ETH value moved by the recorded accesses, counting only the
  ///      kinds that move fresh value so an inherited delegatecall value is not
  ///      double-counted.
  function _valueMoved(Delta memory delta) internal pure returns (uint256 total) {
    for (uint256 i; i < delta.calls.length; ++i) {
      if (_movesValue(delta.calls[i].kind)) total += delta.calls[i].value;
    }
  }
}
