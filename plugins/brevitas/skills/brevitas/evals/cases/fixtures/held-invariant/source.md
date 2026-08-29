// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../ICreditObservables.sol";
import {IWithdrawalQueueObservables} from "../IWithdrawalQueueObservables.sol";
import {Law} from "../Law.sol";

/// @title Nobody is paid ahead of somebody who has been waiting longer.
/// @notice No claim receives payment while an older claim is still owed
/// something. A withdrawal queue is a promise about order as much as about
/// amount, and a queue that pays out of order under partial liquidity is the
/// mechanism by which whoever is quickest, best connected or first to notice
/// gets out and the rest do not.
///
/// A single state is enough to see this, which is why it is a `Law` rather
/// than a `PairLaw`: partial payment is recorded against the claim, so a queue
/// carrying an unpaid entry ahead of a partly paid one is already evidence.
/// Nothing about the history is needed.
///
/// The law reads the queue extension by casting the target, which is the
/// corpus's only way to ask a target for more than the core observables while
/// keeping one law shape. A target with no queue reverts on the read, and that
/// is the limit `Law` already states: the state could not be observed and the
/// law has no opinion. It is not silence dressed as a pass, because the
/// harness counts the revert.
///
/// The traversal is unbounded, and that is a limit rather than an oversight.
/// This reads every recorded claim, one external call each, so against a system
/// with a long enough queue it runs out of gas and reverts -- and a revert is
/// no verdict. There is no partial answer available: the property is about the
/// whole queue, and a law that read half of it and held would be reporting on
/// half a system. The applicability says so, and a target that queues more than
/// can be read in one call needs an adapter that pages, not a law that guesses.
///
/// Exact, with no tolerance. Comparisons only.
contract QueueOrderPreserved is Law {
    function id() external pure override returns (string memory) {
        return "claims/queue-order-preserved/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "No withdrawal claim is paid while an older claim is still owed something.";
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
        bool anOlderClaimIsStillOwed = false;
        for (uint256 i = 0; i < count; i++) {
            (uint256 owed, uint256 paid) = queue.claimAt(i);
            if (anOlderClaimIsStillOwed && paid > 0) {
                return (false, "a claim was paid while an older one was still owed");
            }
            if (paid < owed) {
                anOlderClaimIsStillOwed = true;
            }
        }
        return (true, "no claim was paid ahead of an older one");
    }
}
