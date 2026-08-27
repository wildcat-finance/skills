// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../ICreditObservables.sol";
import {IWithdrawalQueueObservables} from "../IWithdrawalQueueObservables.sol";
import {Law} from "../Law.sol";

/// @title What the queue is still owed, the pool still owes.
/// @notice Pooled lender claims never fall below the total still owed on open
/// withdrawal batches. A lender who has asked to leave has a number recorded
/// against them, and that number is already a liability of the pool. A system
/// whose pooled claim drops beneath the sum of those numbers has stopped owing
/// something it had already written down.
///
/// A fee is how a system gets there, and this law does not mention fees. It
/// cannot: nothing a target reports says a fee was taken, so a law that named
/// one would need the harness to tell it, and a law that trusts the harness is a
/// law about the harness. What is observable is the state a fee leaves behind,
/// and that state is enough. The fee is capped against what is not already
/// queued, or the cap leaks.
///
/// Distinct from the two laws that come nearest, and the distinction is the
/// whole reason this exists.
/// `conservation/reserves-backed-by-claims/v1` bounds reserved assets from above
/// by the pooled claim. `claims/reserves-cover-payable/v1` bounds them from
/// below by what is outstanding on the payable prefix. Compose the two and you
/// get the pooled claim covering the payable prefix, which is weaker than this,
/// because payability is declared against what has actually been set aside: an
/// illiquid system declares fewer batches payable, the prefix shrinks to meet
/// the reserves, and the batches behind it stay owed with nothing bounding them.
/// That gap is where the value goes.
///
/// Not conservation restated either. Conservation moves value from claims to
/// fees and both sides of the equality agree afterwards, which is why it holds
/// across exactly the transition this law refuses.
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
contract PooledClaimsCoverOpenBatches is Law {
    function id() external pure override returns (string memory) {
        return "claims/pooled-claims-cover-open-batches/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "Pooled lender claims cover everything still owed on open withdrawal batches.";
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

        uint256 outstanding;
        for (uint256 i = 0; i < count; i++) {
            (uint256 owed, uint256 paid) = queue.claimAt(i);
            // A claim paid beyond what it was owed contributes nothing, and the
            // subtraction is skipped rather than performed: `owed - paid` would
            // underflow and revert, which under fail_on_revert = false is
            // silence exactly where a system is behaving strangely. That defect
            // is named by `claims/reserves-cover-payable/v1`, which leaves it
            // uncovered for the same reason this law does. Folding it in here
            // would make this law broader than its statement, and a law broader
            // than its statement is what the diagonal exists to fail.
            if (paid >= owed) {
                continue;
            }
            // Summed unchecked with the overflow reported, for the reason given
            // in ValueConserved: reverting here would be silence exactly where
            // the numbers are furthest wrong.
            uint256 next;
            unchecked {
                next = outstanding + (owed - paid);
            }
            if (next < outstanding) {
                return (false, "the open batches sum to more than can be counted");
            }
            outstanding = next;
        }

        if (outstanding <= target.totalLenderClaims()) {
            return (true, "pooled claims cover what the open batches are owed");
        }
        return (false, "pooled claims are below what the open batches are owed");
    }
}
