// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IMarketEventsAndErrors} from "../vendor/interfaces/IMarketEventsAndErrors.sol";

/// @dev A deliberately wrong answer. It emits a `Transfer`-shaped log whose
///      topic0 is the declared selector with its lowest bit flipped, and the
///      declared indexed topics and data region otherwise, so the comparison
///      against the mirror-emit reference must fail on `topic0` and on no
///      earlier field. The wrong constant is derived from the declaration,
///      not read from the assembly emitter.
contract WrongTopic0Specimen {
  function specimen_Transfer(address from, address to, uint256 value) external {
    bytes32 topic0 = IMarketEventsAndErrors.Transfer.selector ^ bytes32(uint256(1));
    assembly {
      mstore(0, value)
      log3(0, 0x20, topic0, from, to)
    }
  }
}
