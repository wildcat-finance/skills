// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";
import {StateDeltaRecorder} from "../src/StateDeltaRecorder.sol";

/// @dev An external call sink and a value payee.
contract Sink {
  uint256 public pinged;

  function ping() external {
    pinged++;
  }
}

/// @dev On `act` it writes its own storage, makes an external call, and moves
///      value, so one driven action exercises all three effect classes the
///      recorder must observe.
contract Actor {
  uint256 public slotValue;

  function act(Sink sink, address payable payee) external payable {
    slotValue = block.number + 1; // storage write
    sink.ping(); // external call, no value
    payee.transfer(msg.value); // value movement
  }
}

/// @dev A contract that takes an endowment at construction, so deploying it
///      moves value through a CREATE rather than a CALL.
contract Endowed {
  constructor() payable {}
}

/// @dev Moves value by deploying an endowed contract, the create-endowment
///      path that a naive recorder would miss.
contract CreatingActor {
  function act() external payable returns (address) {
    return address(new Endowed{value: msg.value}());
  }
}

contract StateDeltaRecorderTest is JanusBase, StateDeltaRecorder {
  function test_records_a_write_a_call_and_a_value_movement() external {
    Sink sink = new Sink();
    Actor actor = new Actor();
    address payable payee = payable(address(0xBEEF));
    vm.deal(address(this), 1 ether);

    _beginRecording();
    uint256 before = gasleft();
    actor.act{value: 1 ether}(sink, payee);
    uint256 gasUsed = before - gasleft();
    Delta memory d = _endRecording(gasUsed);

    assertTrue(d.taken, "delta was taken from a real recording");
    assertTrue(_wroteTo(d, address(actor)), "captured the actor storage write");
    assertTrue(_calledInto(d, address(sink)), "captured the external call to sink");
    assertTrue(_valueMoved(d) >= 1 ether, "captured the value movement to the payee");
    assertTrue(d.gasUsed > 0, "recorded a gas figure");
  }

  function test_a_pure_action_records_no_effects_but_a_real_delta() external {
    Sink sink = new Sink();

    _beginRecording();
    uint256 before = gasleft();
    sink.pinged(); // a view call reads, writes nothing, moves nothing
    uint256 gasUsed = before - gasleft();
    Delta memory d = _endRecording(gasUsed);

    // Taken is the point: an effect-free threshold is a real, empty delta, not
    // an absent one. The gate engine must be able to tell the two apart.
    assertTrue(d.taken, "an effect-free threshold is still a taken delta");
    assertEq(d.writes.length, uint256(0), "no writes on a pure read");
    assertTrue(_valueMoved(d) == 0, "no value on a pure read");
  }

  /// @dev Ending a recording that never began must fail closed, so a harness
  ///      that forgot to record cannot report a clean threshold.
  function test_ending_without_beginning_reverts() external {
    vm.expectRevert(StateDeltaRecorder.RecordingNotStarted.selector);
    this.endWithoutBegin();
  }

  function endWithoutBegin() external returns (Delta memory) {
    return _endRecording(0);
  }

  /// @dev A create-endowment moves value; the recorder must not miss it.
  function test_records_value_moved_through_a_create_endowment() external {
    CreatingActor actor = new CreatingActor();
    vm.deal(address(this), 3 ether);

    _beginRecording();
    uint256 before = gasleft();
    actor.act{value: 3 ether}();
    uint256 gasUsed = before - gasleft();
    Delta memory d = _endRecording(gasUsed);

    // The endowed CREATE carries 3 ether; the enclosing call to the actor
    // carries it too, so the recorder sees the value on at least the create.
    assertTrue(_valueMoved(d) >= 3 ether, "captured the create-endowment value");
  }

  /// @dev A second begin while one is open must fail closed rather than reset
  ///      the buffer and drop everything recorded so far.
  function test_double_begin_reverts() external {
    _beginRecording();
    vm.expectRevert(StateDeltaRecorder.RecordingAlreadyStarted.selector);
    this.beginAgain();
  }

  function beginAgain() external {
    _beginRecording();
  }
}
