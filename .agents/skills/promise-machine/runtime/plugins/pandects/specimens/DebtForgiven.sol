// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `accrual/debt-falls-only-against-payment/v1`, and by
/// nothing else.
///
/// The defect is that debt can be written off. The write-off is charged against
/// fees the protocol has already accrued, so nothing here breaks conservation:
/// the left side falls by exactly what the right side falls by, and every
/// single-state law in the corpus is satisfied at every moment.
///
/// That is what makes it worth a specimen. A system can lose a borrower's debt
/// and balance its own books perfectly, and no observation of one state will
/// ever say so. Only the transition shows it, and only against the assets that
/// did not arrive.
contract DebtForgiven is Sound {
    function forgive(uint256 amount) external {
        uint256 owed = principal + interest;
        uint256 value = bounded(amount);
        if (value > owed) {
            value = owed;
        }
        if (value > fees) {
            value = fees;
        }
        if (value > interest) {
            principal -= value - interest;
            interest = 0;
        } else {
            interest -= value;
        }
        fees -= value;
    }
}
