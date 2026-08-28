// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Wildcat Labs
pragma solidity ^0.8.20;

/// @title Fixed-point helpers
/// @notice Rounding-explicit arithmetic used across the registry.
library MathLib {
    /// @notice Scaling factor for all fixed-point values in this library.
    uint256 internal constant ONE = 1e18;

    /// @notice Multiply two fixed-point values, rounding down.
    /// @param a Left operand.
    /// @param b Right operand.
    /// @return result The product, truncated.
    function mulDown(uint256 a, uint256 b) internal pure returns (uint256 result) {
        result = (a * b) / ONE;
    }

    /// @notice Multiply two fixed-point values, rounding up.
    function mulUp(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 raw = a * b;
        return raw == 0 ? 0 : ((raw - 1) / ONE) + 1;
    }

    /// @dev Saturating subtraction. Never reverts.
    function subFloor(uint256 a, uint256 b) internal pure returns (uint256) {
        return a > b ? a - b : 0;
    }
}
