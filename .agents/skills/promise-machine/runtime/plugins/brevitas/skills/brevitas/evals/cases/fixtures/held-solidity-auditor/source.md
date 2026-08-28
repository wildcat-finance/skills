// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `claims/pooled-claims-cover-open-batches/v1`, and by
/// nothing else.
///
/// The defect is one clause. The fee is capped against what has been set aside
/// rather than against what the open batches are owed. Those two figures agree
/// while the system holds enough to earmark its whole queue, and part company
/// the moment it does not, because an earmark cannot exceed what is held. So the
/// leak opens exactly when the system is illiquid, which is the case
/// undercollateralised credit is for, and it widens with the shortfall.
///
/// This is the cap the reference itself carried until the law existed to name
/// it. Its own comment argued the right principle -- value earmarked against a
/// recorded withdrawal has been promised to a lender who asked for it -- and
/// then measured against the earmark instead of against the promise.
///
/// Everything else stays satisfied, which is why this needed a law of its own.
/// The books balance, because the value moves from claims to fees and
/// conservation sees both sides. Reserves stay within claims. The partition
/// holds, the queue stays in order, and payability is still derived from what
/// has actually been set aside, so the system never declares more payable than
/// it reserved. Debt does not move, so neither accrual law has anything to say.
/// Each recorded claim keeps its own owed and paid amounts untouched: nobody's
/// number was rewritten. The pool behind every one of those numbers is simply
/// smaller than their sum.
contract FeeFromQueued is Sound {
    /// @dev The reference measures the fee against what the open batches are
    /// owed. This measures it against the earmark, and takes the difference out
    /// of value that was already promised.
    function accrueFee(uint256 amount) external override {
        uint256 available = claims > reserved ? claims - reserved : 0;
        uint256 value = bounded(amount);
        if (value > available) {
            value = available;
        }
        claims -= value;
        fees += value;
    }
}
