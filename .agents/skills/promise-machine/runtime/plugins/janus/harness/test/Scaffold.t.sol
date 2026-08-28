// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {JanusBase} from "../src/JanusBase.sol";

/// @dev The scaffold proof: the harness compiles, the minimal `Vm` interface
///      links against the cheatcode address, and the test base asserts. The
///      gates arrive in later steps; this only shows the project stands up.
contract ScaffoldTest is JanusBase {
  function test_harness_compiles_and_base_asserts() external pure {
    assertEq(uint256(2), uint256(2), "arithmetic base holds");
    assertTrue(true, "assertion base holds");
  }

  function test_cheatcode_handle_is_the_canonical_address() external pure {
    assertEq(
      address(vm),
      0x7109709ECfa91a80626fF3989D68f67F5b1DD12D,
      "vm points at the canonical cheatcode address"
    );
  }
}
