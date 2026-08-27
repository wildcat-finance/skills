// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {CorpusBase, CorpusDriver} from "../CorpusBase.sol";

/// @title The one-state laws as Foundry invariants.
/// @notice Written once and inherited by both adapters below, so the two differ
/// in what they can reach rather than in which laws they ask about.
///
/// The three laws that need no withdrawal queue are separate from the three that
/// do, because a target without one reverts on the read and a revert is no
/// verdict. An integrator with no queue wants three answers, not three reverts,
/// so `hasWithdrawalQueue` stands the others down.
abstract contract OneStateInvariants is CorpusBase {
    /// @notice Whether the target implements `IWithdrawalQueueObservables`.
    /// @dev True by default. A corpus that assumed the smaller interface would
    /// quietly skip three laws for every system that does have a queue, and
    /// quietly skipping is the failure this corpus is about.
    function hasWithdrawalQueue() public view virtual returns (bool) {
        return true;
    }

    function invariant_value_is_conserved() public view {
        (bool held, string memory why) = conserved.check(target());
        require(held, why);
    }

    function invariant_reserves_are_backed_by_claims() public view {
        (bool held, string memory why) = backed.check(target());
        require(held, why);
    }

    function invariant_held_assets_stay_partitioned() public view {
        (bool held, string memory why) = partitioned.check(target());
        require(held, why);
    }

    function invariant_the_queue_stays_in_order() public view {
        if (!hasWithdrawalQueue()) {
            return;
        }
        (bool held, string memory why) = ordered.check(target());
        require(held, why);
    }

    function invariant_reserves_cover_what_is_payable() public view {
        if (!hasWithdrawalQueue()) {
            return;
        }
        (bool held, string memory why) = covered.check(target());
        require(held, why);
    }

    function invariant_pooled_claims_cover_open_batches() public view {
        if (!hasWithdrawalQueue()) {
            return;
        }
        (bool held, string memory why) = pooled.check(target());
        require(held, why);
    }
}

/// @title The corpus over a target you do not front.
/// @notice Extend this, create your system in `setUp`, and return it from
/// `target()`. Foundry fuzzes what `setUp` creates, so the system is built
/// there rather than handed in at construction.
///
/// One-state laws only. Nothing here sits in front of the calls, so there is no
/// past to read, and a pair law offered from here would report holding for
/// every target forever.
abstract contract CorpusInvariants is OneStateInvariants {}

/// @title The same, plus the succession laws, for a target you do front.
/// @notice Extend this when the calls go through your harness. Write your
/// protocol's entry points and put `records` on every one that changes state.
///
/// Foundry fuzzes the entry points you write, which is the point: the snapshot
/// happens on the way in, so every call the fuzzer makes is one the succession
/// laws get to judge.
///
/// A state-changing entry point without `records` is not an error the compiler
/// can catch. It shows as pair laws holding through the call and saying
/// nothing, which reads exactly like a system that is behaving.
abstract contract DrivenCorpusInvariants is OneStateInvariants, CorpusDriver {
    function invariant_debt_falls_only_against_payment() public view {
        require(judgePair(falls), "debt fell further than held assets rose");
    }

    function invariant_no_accrual_at_rest() public view {
        require(judgePair(atRest), "debt rose while time stood still");
    }

    function invariant_recorded_claims_never_shrink() public view {
        require(judgePair(shrinks), "a recorded claim was written down");
    }
}
