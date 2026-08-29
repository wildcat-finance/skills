// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `conservation/reserves-backed-by-claims/v1`, and by
/// nothing else.
///
/// The defect is one line: reserving checks the assets held and forgets to
/// check what anybody actually claimed. The system starves the borrower of
/// liquidity it is charging them for, against withdrawals nobody requested.
contract OverReserved is Sound {
    function reserve(uint256 amount) external override {
        uint256 value = bounded(amount);
        if (value > held) {
            value = held;
        }
        reserved = value;
    }
}
