// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IMarketEventsAndErrors} from "../vendor/interfaces/IMarketEventsAndErrors.sol";

/// @dev A deliberately wrong answer. It emits a `Transfer` log with the
///      declared topic0 and topic count, the two indexed topics in the wrong
///      order, and a data region of the declared length whose bytes are the
///      bitwise complement of the declared value, so the comparison against
///      the mirror-emit reference must fail on `topic1` and on no earlier
///      field: a comparison that checked the data bytes before the indexed
///      topics would name the wrong field. The constant is derived from the
///      declaration, not read from the assembly emitter.
contract WrongIndexedTopicSpecimen {
  function specimen_Transfer(address from, address to, uint256 value) external {
    bytes32 topic0 = IMarketEventsAndErrors.Transfer.selector;
    assembly {
      mstore(0, not(value))
      log3(0, 0x20, topic0, to, from)
    }
  }
}
