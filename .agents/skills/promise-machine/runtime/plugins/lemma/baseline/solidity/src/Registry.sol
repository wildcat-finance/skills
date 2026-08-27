// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Wildcat Labs
pragma solidity ^0.8.20;

import { RegistryBase } from "./RegistryBase.sol";
import { MathLib } from "./MathLib.sol";

/// @title Registry
/// @notice Concrete registry. Entries are created by the admin and retired by owners.
contract Registry is RegistryBase {
    using MathLib for uint256;

    /// @notice Fee applied on creation, in fixed-point.
    uint256 public fee;

    /// @notice Emitted when an entry is retired.
    event EntryRetired(bytes32 indexed id);

    /// @notice Thrown when capacity would be exceeded.
    error AtCapacity(uint256 capacity);

    constructor(address admin_, uint256 capacity_, uint256 fee_)
        RegistryBase(admin_, capacity_)
    {
        fee = fee_;
    }

    /// @notice Create a new entry.
    /// @param id The identifier to assign.
    /// @param amount The amount to record against the entry.
    /// @return charged The fee charged on creation.
    function create(bytes32 id, uint128 amount)
        external
        onlyAdmin
        returns (uint256 charged)
    {
        if (_entries[id].owner != address(0)) revert DuplicateEntry(id);
        if (_total >= capacity) revert AtCapacity(capacity);
        charged = uint256(amount).mulUp(fee);
        _entries[id] = Position({
            owner: msg.sender,
            amount: amount,
            createdAt: uint64(block.timestamp),
            status: Status.Active
        });
        unchecked { ++_total; }
        emit EntryCreated(id, msg.sender);
    }

    /// @notice Retire an entry you own.
    function retire(bytes32 id) external {
        Position storage p = _entries[id];
        if (p.owner != msg.sender) revert NotAdmin(msg.sender);
        p.status = Status.Retired;
        emit EntryRetired(id);
    }

    /// @notice Set the creation fee.
    function setFee(uint256 fee_) external onlyAdmin {
        fee = fee_;
    }
}
