// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `accrual/no-accrual-at-rest/v1`, and by nothing else.
///
/// The defect is interest charged on a call rather than on a duration. The
/// clock does not move and the borrower owes more anyway, which is the shape of
/// every accrual that runs from a state update instead of from elapsed time:
/// two transactions in one block, an accrual triggered by a read, a rate
/// applied once per interaction.
///
/// Conservation holds throughout, because the interest is credited to lenders
/// exactly as it is charged to borrowers. The system takes from the borrower
/// and gives to the lender, keeps nothing, and its books balance the whole way.
contract AccruesAtRest is Sound {
    function poke(uint256 amount) external {
        uint256 value = bounded(amount) % 1e6;
        interest += value;
        claims += value;
    }
}
