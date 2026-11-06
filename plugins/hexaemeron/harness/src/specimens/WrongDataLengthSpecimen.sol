// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IMarketEventsAndErrors} from "../vendor/interfaces/IMarketEventsAndErrors.sol";

/// @dev A deliberately wrong answer. It emits a `Transfer` log with the
///      declared topic0 and indexed topics and a data region one word longer
///      than declared, whose first word is the declared value, so the
///      comparison against the mirror-emit reference must fail on
///      `data length` and on no earlier field, `data bytes` included. The
///      constant is derived from the declaration, not read from the assembly
///      emitter.
contract WrongDataLengthSpecimen {
  function specimen_Transfer(address from, address to, uint256 value) external {
    bytes32 topic0 = IMarketEventsAndErrors.Transfer.selector;
    assembly {
      mstore(0, value)
      mstore(0x20, 0)
      log3(0, 0x40, topic0, from, to)
    }
  }
}
