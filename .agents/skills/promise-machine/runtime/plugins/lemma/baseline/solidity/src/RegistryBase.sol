// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Wildcat Labs
pragma solidity ^0.8.20;

import { IRegistry } from "./IRegistry.sol";

/// @title Shared registry storage and access control
/// @notice Inherited by the concrete registry. Not deployed directly.
abstract contract RegistryBase is IRegistry {
    /// @notice The account permitted to create entries.
    address public immutable admin;

    /// @notice Upper bound on entries, fixed at construction.
    uint256 public immutable capacity;

    /// @notice Human-readable label for this deployment.
    string public label;

    mapping(bytes32 => Position) internal _entries;
    uint256 internal _total;

    /// @notice Thrown when a caller is not the admin.
    error NotAdmin(address caller);

    /// @param admin_ The account permitted to create entries.
    /// @param capacity_ Upper bound on entries.
    constructor(address admin_, uint256 capacity_) {
        admin = admin_;
        capacity = capacity_;
    }

    /// @dev Reverts unless the caller is the admin.
    modifier onlyAdmin() {
        if (msg.sender != admin) revert NotAdmin(msg.sender);
        _;
    }

    /// @inheritdoc IRegistry
    function entry(bytes32 id) external view returns (Position memory position) {
        position = _entries[id];
    }

    /// @inheritdoc IRegistry
    function total() external view returns (uint256) {
        return _total;
    }
}
