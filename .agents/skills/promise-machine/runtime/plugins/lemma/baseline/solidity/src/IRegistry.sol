// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Wildcat Labs
pragma solidity ^0.8.20;

/// @title Registry interface
/// @notice Read-side view of the registry.
interface IRegistry {
    /// @notice Emitted when an entry is created.
    /// @param id The identifier assigned to the entry.
    /// @param owner The account that controls the entry.
    event EntryCreated(bytes32 indexed id, address indexed owner);

    /// @notice Thrown when an identifier is already taken.
    error DuplicateEntry(bytes32 id);

    /// @notice Status an entry may hold.
    enum Status { Pending, Active, Retired }

    /// @notice A stored entry.
    struct Position {
        address owner;
        uint128 amount;
        uint64 createdAt;
        Status status;
    }

    /// @notice Return the entry stored under `id`.
    /// @param id The identifier to look up.
    /// @return position The stored entry.
    function entry(bytes32 id) external view returns (Position memory position);

    /// @notice Total number of entries ever created.
    function total() external view returns (uint256);
}
