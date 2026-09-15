// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IMarketEventsAndErrors} from "../vendor/interfaces/IMarketEventsAndErrors.sol";

/// @dev A deliberately wrong answer. It emits a `Transfer` log with the
///      declared topic0 and indexed topics and a data region of the declared
///      length whose bytes are the bitwise complement of the declared value,
///      so the comparison against the mirror-emit reference must fail on
///      `data bytes` and on no earlier field, `data length` included.
contract WrongDataSpecimen {
  function specimen_Transfer(address from, address to, uint256 value) external {
    bytes32 topic0 = IMarketEventsAndErrors.Transfer.selector;
    assembly {
      mstore(0, not(value))
      log3(0, 0x20, topic0, from, to)
    }
  }
}
