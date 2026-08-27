// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

/// @dev The minimal Foundry cheatcode surface Janus needs, declared in-tree so
///      the harness carries no external Solidity dependency. Every signature
///      matches the Foundry `Vm` interface at the canonical cheatcode address;
///      Janus uses only this subset.
interface Vm {
  struct Log {
    bytes32[] topics;
    bytes data;
    address emitter;
  }

  // State-diff recording. One recording captures storage writes, external call
  // targets and kinds, and value movements across a driven action, which are
  // four of the effect classes the state-delta recorder must observe.
  enum AccountAccessKind {
    Call,
    DelegateCall,
    CallCode,
    StaticCall,
    Create,
    SelfDestruct,
    Resume,
    Balance,
    Extcodesize,
    Extcodehash,
    Extcodecopy
  }
  struct ChainInfo {
    uint256 forkId;
    uint256 chainId;
  }
  struct StorageAccess {
    address account;
    bytes32 slot;
    bool isWrite;
    bytes32 previousValue;
    bytes32 newValue;
    bool reverted;
  }
  struct AccountAccess {
    ChainInfo chainInfo;
    AccountAccessKind kind;
    address account;
    address accessor;
    bool initialized;
    uint256 oldBalance;
    uint256 newBalance;
    bytes deployedCode;
    uint256 value;
    bytes data;
    bool reverted;
    StorageAccess[] storageAccesses;
    uint64 depth;
  }
  function startStateDiffRecording() external;
  function stopAndReturnStateDiff() external returns (AccountAccess[] memory accountAccesses);

  // Storage-access recording, for the state-delta recorder.
  function record() external;
  function accesses(
    address target
  ) external returns (bytes32[] memory readSlots, bytes32[] memory writeSlots);

  // Event recording, for observing emitted logs across a threshold.
  function recordLogs() external;
  function getRecordedLogs() external returns (Log[] memory logs);

  // State snapshots, for revert-behaviour and rollback gates.
  function snapshotState() external returns (uint256 snapshotId);
  function revertToState(uint256 snapshotId) external returns (bool success);

  // Filesystem, scoped by fs_permissions, for manifests and findings.
  function readFile(string calldata path) external view returns (string memory data);
  function writeFile(string calldata path, string calldata data) external;
  function exists(string calldata path) external view returns (bool);

  // JSON parsing, for reading a manifest.
  function parseJson(string calldata json) external pure returns (bytes memory abiEncoded);
  function parseJson(
    string calldata json,
    string calldata key
  ) external pure returns (bytes memory abiEncoded);
  function parseJsonUint(string calldata json, string calldata key) external pure returns (uint256);
  function parseJsonBool(string calldata json, string calldata key) external pure returns (bool);
  function parseJsonAddress(
    string calldata json,
    string calldata key
  ) external pure returns (address);
  function parseJsonString(
    string calldata json,
    string calldata key
  ) external pure returns (string memory);
  function parseJsonKeys(
    string calldata json,
    string calldata key
  ) external pure returns (string[] memory keys);

  // Identities and balances, for driving sequences.
  function addr(uint256 privateKey) external pure returns (address keyAddr);
  function deal(address account, uint256 newBalance) external;
  function prank(address sender) external;
  function startPrank(address sender) external;
  function stopPrank() external;
  function warp(uint256 newTimestamp) external;

  // Expectations, for asserting a threshold reverts as declared.
  function expectRevert() external;
  function expectRevert(bytes4 revertData) external;
  function expectRevert(bytes calldata revertData) external;
}
