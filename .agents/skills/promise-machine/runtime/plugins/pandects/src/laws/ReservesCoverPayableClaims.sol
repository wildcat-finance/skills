// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../ICreditObservables.sol";
import {IWithdrawalQueueObservables} from "../IWithdrawalQueueObservables.sol";
import {Law} from "../Law.sol";

/// @title What the system says it can pay, it has set aside.
/// @notice Everything still owed on the claims the system declares payable is
/// covered by the assets it has reserved. A declaration of payability is a
/// statement a lender acts on: they stop looking for liquidity elsewhere, they
/// stop pricing the risk of not getting out, and a system that declares more
/// than it holds has moved that risk onto them without telling them.
///
/// This is why `payableThrough` is a declaration rather than something derived
/// from the reserves. A derived figure cannot be wrong and therefore cannot be
/// checked; the law exists precisely to compare what a system says with what it
/// has.
///
/// Distinct from `conservation/reserves-backed-by-claims/v1`, which bounds
/// reserves from above against the pooled total. This bounds them from below
/// against a named subset. A system can satisfy either alone.
///
/// The traversal is unbounded, and that is a limit rather than an oversight.
/// This reads every recorded claim, one external call each, so against a system
/// with a long enough queue it runs out of gas and reverts -- and a revert is
/// no verdict. There is no partial answer available: the property is about the
/// whole queue, and a law that read half of it and held would be reporting on
/// half a system. The applicability says so, and a target that queues more than
/// can be read in one call needs an adapter that pages, not a law that guesses.
///
/// Exact, with no tolerance. A sum and a comparison.
contract ReservesCoverPayableClaims is Law {
    function id() external pure override returns (string memory) {
        return "claims/reserves-cover-payable/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "Reserved assets cover everything still owed on the claims declared payable.";
    }

    function check(ICreditObservables target)
        external
        view
        override
        returns (bool held, string memory detail)
    {
        IWithdrawalQueueObservables queue =
            IWithdrawalQueueObservables(address(target));
        uint256 count = queue.claimCount();
        uint256 through = queue.payableThrough();
        if (through > count) {
            // Marginally broader than the statement, and deliberately so. The
            // alternative is reading past the end of the queue, which reverts,
            // and a revert is no verdict: the loudest possible nonsense in a
            // declaration would produce the quietest possible result.
            return (false, "more claims were declared payable than exist");
        }

        uint256 outstanding;
        for (uint256 i = 0; i < through; i++) {
            (uint256 owed, uint256 paid) = queue.claimAt(i);
            // A claim paid beyond what it was owed contributes nothing here.
            // It is a defect, and no law in the corpus covers it yet; folding
            // it into this one would make this law catch something its
            // statement does not describe, and a law broader than its
            // statement is the thing the diagonal exists to fail.
            if (paid >= owed) {
                continue;
            }
            // Summed unchecked with the overflow reported, for the reason
            // given in ValueConserved: reverting here would be silence exactly
            // where the numbers are furthest wrong.
            uint256 next;
            unchecked {
                next = outstanding + (owed - paid);
            }
            if (next < outstanding) {
                return (false, "the payable claims sum to more than can be counted");
            }
            outstanding = next;
        }

        if (outstanding <= target.reservedAssets()) {
            return (true, "reserves cover what is declared payable");
        }
        return (false, "more is declared payable than is reserved");
    }
}
