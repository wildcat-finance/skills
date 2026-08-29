// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ClaimRecord, Observation} from "../Observation.sol";
import {PairLaw} from "../PairLaw.sol";

/// @title A claim written down is never written down smaller.
/// @notice Once a withdrawal claim is recorded, the amount it is owed does not
/// change and the payment against it never runs backwards. A lender who asked
/// to leave has a number attached to their name, and a system that quietly
/// reduces it has taken something without paying for it.
///
/// The pooled total is the wrong place to look for this. Lender claims fall
/// legitimately every time a fee is taken, so a law over `totalLenderClaims`
/// either admits fees -- and then says only that value went somewhere, which
/// is conservation restated -- or refuses them, and fails against every
/// correct system. What is actually invariant is the individual record, which
/// is why this law needs the queue extension and the conservation family
/// does not.
///
/// Three ways to break it, all of them things real systems have done: rewrite
/// an entry downwards under a haircut, drop an entry so the queue gets shorter,
/// or renumber the queue so index three is a different claim than it was. The
/// third is why the extension documents that a paid claim keeps its index; a
/// queue that compacts itself makes every comparison here meaningless, and
/// this law would report the compaction rather than miss it.
///
/// Exact, with no tolerance. Comparisons only.
contract RecordedClaimNeverShrinks is PairLaw {
    function id() external pure override returns (string memory) {
        return "claims/recorded-claim-never-shrinks/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "A recorded claim keeps its owed amount and never loses payment already made.";
    }

    function check(Observation memory earlier, Observation memory later)
        external
        pure
        override
        returns (bool held, string memory detail)
    {
        if (!earlier.queueObserved || !later.queueObserved) {
            // Not a violation by the system, and not a pass either. Reported
            // as a violation because the alternative is holding on a
            // comparison nobody made: whoever built this pair asked for the
            // core observables and then asked a question only the queue can
            // answer.
            return (false, "the withdrawal queue was not observed");
        }
        if (later.queue.length < earlier.queue.length) {
            return (false, "a recorded claim was dropped from the queue");
        }
        for (uint256 i = 0; i < earlier.queue.length; i++) {
            ClaimRecord memory was = earlier.queue[i];
            ClaimRecord memory now_ = later.queue[i];
            if (now_.owed != was.owed) {
                return (false, "a recorded claim's owed amount changed");
            }
            if (now_.paid < was.paid) {
                return (false, "payment already made against a claim was reversed");
            }
        }
        return (true, "every recorded claim kept its amount and its payment");
    }
}
