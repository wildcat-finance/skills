// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `claims/recorded-claim-never-shrinks/v1`, and by nothing
/// else.
///
/// The defect is that a recorded claim can be written down after the fact. The
/// amount taken off the claim is moved into fees and the earmark is recomputed,
/// so the books balance, reserves stay within claims, and the queue stays in
/// order. Every single-state law in the corpus is satisfied.
///
/// The lender asked to leave, was told a number, and the number changed. That
/// is visible only by comparing the queue with the queue as it was, which is
/// the entire reason the claims family needs a law over a pair.
contract ClaimHaircut is Sound {
    function haircut(uint256 index, uint256 amount) external {
        if (owedAt.length == 0) {
            return;
        }
        uint256 i = index % owedAt.length;
        uint256 unpaid = owedAt[i] - paidAt[i];
        uint256 value = bounded(amount);
        if (value > unpaid) {
            value = unpaid;
        }
        if (value > claims) {
            value = claims;
        }
        owedAt[i] -= value;
        claims -= value;
        fees += value;
        reserved = earmark();
    }
}
