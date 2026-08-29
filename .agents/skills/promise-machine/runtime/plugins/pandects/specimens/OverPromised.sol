// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `conservation/held-assets-partitioned/v1`, and by nothing
/// else.
///
/// The defect is that borrowable liquidity is recorded rather than derived, and
/// reserving forgets to reduce it. The same asset is offered to the borrower
/// and promised to a departing lender, and whichever of them arrives second
/// finds it gone.
contract OverPromised is Sound {
    uint256 internal promised;

    function borrowableAssets() external view override returns (uint256) {
        return promised;
    }

    function deposit(uint256 amount) external override {
        uint256 value = bounded(amount);
        held += value;
        claims += value;
        promised += value;
    }

    function borrow(uint256 amount) external override {
        uint256 value = bounded(amount);
        if (value > promised) {
            value = promised;
        }
        if (value > held) {
            value = held;
        }
        held -= value;
        promised -= value;
        principal += value;
    }
}
