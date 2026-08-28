// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `claims/queue-order-preserved/v1`, and by nothing else.
///
/// The defect is that payment goes to the newest claim the system can settle
/// rather than the oldest. Nothing is created, nothing is destroyed, no claim
/// is written down and the reserves still cover what is declared payable. The
/// only thing wrong is who gets paid.
///
/// This is the shape of a queue that pays whoever is quickest to ask, or
/// whoever the operator picks. Under full liquidity nobody notices, because
/// everyone is paid; it matters exactly when there is not enough to go round,
/// which is the state a system is in when the ordering was the thing being
/// relied on.
contract QueueJumped is Sound {
    function payClaim(uint256 amount) external override {
        uint256 through = payableCount();
        for (uint256 i = through; i > 0; i--) {
            uint256 index = i - 1;
            uint256 unpaid = owedAt[index] - paidAt[index];
            if (unpaid == 0) {
                continue;
            }
            settle(index, amount, unpaid);
            return;
        }
    }
}
