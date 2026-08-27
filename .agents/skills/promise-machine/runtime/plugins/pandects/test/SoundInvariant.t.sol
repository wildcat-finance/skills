// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Law} from "../src/Law.sol";
import {ValueConserved} from "../src/laws/ValueConserved.sol";
import {ReservesBackedByClaims} from "../src/laws/ReservesBackedByClaims.sol";
import {HeldAssetsPartitioned} from "../src/laws/HeldAssetsPartitioned.sol";
import {QueueOrderPreserved} from "../src/laws/QueueOrderPreserved.sol";
import {ReservesCoverPayableClaims} from "../src/laws/ReservesCoverPayableClaims.sol";
import {PooledClaimsCoverOpenBatches} from "../src/laws/PooledClaimsCoverOpenBatches.sol";
import {Sound} from "../specimens/Sound.sol";

/// @title The sound reference, under search.
/// @notice The diagonal in `Corpus.t.sol` checks each law against a state that
/// somebody chose. This checks the sound reference against states nobody chose:
/// any sequence of deposits, borrowings, repayments, fees and reservations the
/// fuzzer can reach.
///
/// Only `Sound` is a target. The laws are deployed in the constructor rather
/// than in `setUp`, because Foundry fuzzes what `setUp` creates and the laws
/// have nothing to call.
///
/// The broken specimens are deliberately absent. An invariant harness cannot
/// assert that something eventually fails, so the proof that a law catches its
/// specimen lives in the diagonal and in the campaigns recorded in
/// `audit/AUDIT.md`.
///
/// Only the one-state laws are here. A pair law needs the state as it was
/// before the last call, and a Foundry invariant runs after the call with no
/// way to have taken a snapshot before it. The campaign harness in
/// `src/campaigns/Specimens.sol` records one on the way into every entry point,
/// which is what lets Echidna and Medusa search the pair laws; under Foundry
/// they are covered deterministically in `test/Pairs.t.sol`, transition by
/// transition.
contract SoundInvariantTest {
    Sound internal target;
    Law internal conserved;
    Law internal backed;
    Law internal partitioned;
    Law internal ordered;
    Law internal covered;
    Law internal pooled;

    constructor() {
        conserved = new ValueConserved();
        backed = new ReservesBackedByClaims();
        partitioned = new HeldAssetsPartitioned();
        ordered = new QueueOrderPreserved();
        covered = new ReservesCoverPayableClaims();
        pooled = new PooledClaimsCoverOpenBatches();
    }

    function setUp() public {
        target = new Sound();
    }

    function invariant_value_is_conserved() public view {
        (bool held, ) = conserved.check(target);
        require(held, "the sound reference stopped conserving value");
    }

    function invariant_reserves_are_backed_by_claims() public view {
        (bool held, ) = backed.check(target);
        require(held, "the sound reference reserved beyond its claims");
    }

    function invariant_held_assets_stay_partitioned() public view {
        (bool held, ) = partitioned.check(target);
        require(held, "the sound reference promised the same asset twice");
    }

    function invariant_the_queue_stays_in_order() public view {
        (bool held, ) = ordered.check(target);
        require(held, "the sound reference paid a claim out of turn");
    }

    function invariant_reserves_cover_what_is_payable() public view {
        (bool held, ) = covered.check(target);
        require(held, "the sound reference declared more payable than it held");
    }

    /// The one this harness matters most for. Both of the reference's fee and
    /// reservation caps were corrected so this holds, and a hand-derived state
    /// is a poor way to check a cap: what has to be true is that no sequence
    /// reaches a pool below what the queue is owed.
    function invariant_pooled_claims_cover_open_batches() public view {
        (bool held, ) = pooled.check(target);
        require(held, "the sound reference owed its queue more than its pool");
    }
}
