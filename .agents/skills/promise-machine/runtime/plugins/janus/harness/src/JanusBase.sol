// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {Vm} from "./Vm.sol";

/// @dev The Janus test base. It carries no external dependency: the cheatcode
///      handle and a small set of `require`-based assertions are all a Janus
///      test contract needs. A failing assertion reverts, which Foundry reports
///      as a failed test, so no DSTest `failed()` flag is used.
abstract contract JanusBase {
  Vm internal constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

  function assertTrue(bool condition, string memory message) internal pure {
    require(condition, message);
  }

  function assertEq(uint256 a, uint256 b, string memory message) internal pure {
    require(a == b, message);
  }

  function assertEq(address a, address b, string memory message) internal pure {
    require(a == b, message);
  }

  function assertEq(bytes32 a, bytes32 b, string memory message) internal pure {
    require(a == b, message);
  }

  function assertEq(bool a, bool b, string memory message) internal pure {
    require(a == b, message);
  }
}
