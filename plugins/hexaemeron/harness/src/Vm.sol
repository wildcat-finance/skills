// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

/// @dev The Foundry cheatcode surface this harness uses, declared in-tree in
///      the Janus pattern because the profile admits no library (`libs = []`)
///      and so no forge-std. Only log recording is declared: the suite reads
///      no file, writes no file and shells out to nothing.
interface Vm {
  struct Log {
    bytes32[] topics;
    bytes data;
    address emitter;
  }

  function recordLogs() external;

  function getRecordedLogs() external returns (Log[] memory logs);
}

/// @dev The canonical cheatcode address, `address(uint160(uint256(keccak256("hevm cheat code"))))`.
address constant VM_ADDRESS = 0x7109709ECfa91a80626fF3989D68f67F5b1DD12D;
