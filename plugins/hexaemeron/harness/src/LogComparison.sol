// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {Vm} from "./Vm.sol";

/// @dev Field-by-field comparison of two recorded logs. Every field is its own
///      assertion with its own revert message, so a divergence names the field
///      that moved: `topic count` before any topic, `topic0`, then `topic1`,
///      `topic2`, ... for as many indexed topics as the arrays hold (no
///      ceiling: a `log4` pair compares `topic3` the same way), then `data
///      length` before `data bytes`. The emitter address is not compared,
///      because the two logs come from two contracts by construction.
library LogComparison {
  function compare(Vm.Log memory actual, Vm.Log memory expected) internal pure {
    require(actual.topics.length == expected.topics.length, "topic count");
    require(actual.topics.length > 0, "topic0 absent");
    require(actual.topics[0] == expected.topics[0], "topic0");
    for (uint256 i = 1; i < expected.topics.length; i++) {
      require(actual.topics[i] == expected.topics[i], topicName(i));
    }
    require(actual.data.length == expected.data.length, "data length");
    require(keccak256(actual.data) == keccak256(expected.data), "data bytes");
  }

  /// @dev `topic<i>` for any `i`, built without a digit ceiling.
  function topicName(uint256 index) internal pure returns (string memory) {
    return string(abi.encodePacked("topic", decimal(index)));
  }

  function decimal(uint256 value) internal pure returns (string memory) {
    if (value == 0) return "0";
    uint256 digits;
    for (uint256 v = value; v != 0; v /= 10) digits++;
    bytes memory out = new bytes(digits);
    for (uint256 v = value; v != 0; v /= 10) {
      out[--digits] = bytes1(uint8(48 + (v % 10)));
    }
    return string(out);
  }
}
