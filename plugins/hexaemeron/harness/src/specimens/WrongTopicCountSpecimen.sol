// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IMarketEventsAndErrors} from "../vendor/interfaces/IMarketEventsAndErrors.sol";

/// @dev A deliberately wrong answer. It emits a `Transfer`-shaped log with the
///      declared topic0, only the first of the two declared indexed topics,
///      and a data region one word longer than declared, so the comparison
///      against the mirror-emit reference must fail on `topic count` and on
///      no earlier field: a comparison that checked the data length before
///      the topic count would name the wrong field. The constant is derived
///      from the declaration, not read from the assembly emitter.
contract WrongTopicCountSpecimen {
  function specimen_Transfer(address from, address, uint256 value) external {
    bytes32 topic0 = IMarketEventsAndErrors.Transfer.selector;
    assembly {
      mstore(0, value)
      mstore(0x20, 0)
      log2(0, 0x40, topic0, from)
    }
  }
}
