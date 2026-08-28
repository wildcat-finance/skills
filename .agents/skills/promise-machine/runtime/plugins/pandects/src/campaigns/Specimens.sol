// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Law} from "../Law.sol";
import {Observation, Observe} from "../Observation.sol";
import {PairLaw} from "../PairLaw.sol";
import {ValueConserved} from "../laws/ValueConserved.sol";
import {ReservesBackedByClaims} from "../laws/ReservesBackedByClaims.sol";
import {HeldAssetsPartitioned} from "../laws/HeldAssetsPartitioned.sol";
import {QueueOrderPreserved} from "../laws/QueueOrderPreserved.sol";
import {ReservesCoverPayableClaims} from "../laws/ReservesCoverPayableClaims.sol";
import {PooledClaimsCoverOpenBatches} from "../laws/PooledClaimsCoverOpenBatches.sol";
import {DebtFallsOnlyAgainstPayment} from "../laws/DebtFallsOnlyAgainstPayment.sol";
import {NoAccrualAtRest} from "../laws/NoAccrualAtRest.sol";
import {RecordedClaimNeverShrinks} from "../laws/RecordedClaimNeverShrinks.sol";
import {Sound} from "../../specimens/Sound.sol";
import {MintedClaims} from "../../specimens/MintedClaims.sol";
import {OverReserved} from "../../specimens/OverReserved.sol";
import {OverPromised} from "../../specimens/OverPromised.sol";
import {DebtForgiven} from "../../specimens/DebtForgiven.sol";
import {AccruesAtRest} from "../../specimens/AccruesAtRest.sol";
import {CompoundsPerStep} from "../../specimens/CompoundsPerStep.sol";
import {ClaimHaircut} from "../../specimens/ClaimHaircut.sol";
import {QueueJumped} from "../../specimens/QueueJumped.sol";
import {PayableBeyondReserves} from "../../specimens/PayableBeyondReserves.sol";
import {FeeFromQueued} from "../../specimens/FeeFromQueued.sol";

/// @title Campaign entry points, for the engines that are not Foundry.
/// @dev Under `src/` rather than `test/` because crytic-compile skips `test/`
/// when it builds a Foundry project, and a harness the engine cannot see is a
/// campaign that quietly tests nothing.
/// @notice One harness per specimen, exposing the operations a fuzzer may call
/// and one property per law.
///
/// Both prefixes are declared on every harness. Echidna looks for `echidna_`
/// and Medusa defaults to `property_`, so a harness carrying only one of them
/// is a harness that silently does nothing under the other engine. Each pair
/// delegates to the same internal function, so the two engines are asked the
/// same question.
///
/// Nine of these eleven are expected to fail one property, and the expectation is
/// the point: a campaign that reports every property holding against a contract
/// built to break one has not searched hard enough, and the failure is the
/// evidence that the law is a law. `audit/AUDIT.md` records what each engine
/// found.
///
/// The pair laws need the state as it was before the last call, so every
/// mutating entry point takes a snapshot on the way in. That is the whole of
/// the mechanism: `previous` is the system one call ago, the property compares
/// it with the system now, and an engine that has made no call yet finds
/// `previous` unobserved and every pair property holding vacuously.
///
/// `accrual/path-independent/v1` is absent, and its absence is not an
/// oversight. It compares two systems advanced over the same span by different
/// routes, and a campaign drives one system along one route. It is covered
/// deterministically in `test/Pairs.t.sol` and reduced in
/// `test/counterexamples/Accrual.t.sol`.
abstract contract Campaign {
    Law internal immutable conserved = new ValueConserved();
    Law internal immutable backed = new ReservesBackedByClaims();
    Law internal immutable partitioned = new HeldAssetsPartitioned();
    Law internal immutable ordered = new QueueOrderPreserved();
    Law internal immutable covered = new ReservesCoverPayableClaims();
    Law internal immutable pooled = new PooledClaimsCoverOpenBatches();

    PairLaw internal immutable falls = new DebtFallsOnlyAgainstPayment();
    PairLaw internal immutable atRest = new NoAccrualAtRest();
    PairLaw internal immutable shrinks = new RecordedClaimNeverShrinks();

    /// @notice The system as it was immediately before the last call.
    Observation internal previous;

    function target() internal view virtual returns (Sound);

    /// @notice Record the state on the way in, so a pair law has a past to read.
    modifier records() {
        remember();
        _;
    }

    /// @dev Field by field, and the queue entry by entry. A whole-struct
    /// assignment from memory to storage needs the IR pipeline, and turning
    /// that on for the repository would change how every consumer of this
    /// corpus compiles in order to save nine lines here.
    function remember() internal {
        Observation memory found = Observe.takeWithQueue(target());
        previous.totalAssets = found.totalAssets;
        previous.totalDebt = found.totalDebt;
        previous.totalLenderClaims = found.totalLenderClaims;
        previous.reservedAssets = found.reservedAssets;
        previous.borrowableAssets = found.borrowableAssets;
        previous.accruedFees = found.accruedFees;
        previous.observedAt = found.observedAt;
        previous.payableThrough = found.payableThrough;
        previous.queueObserved = true;
        while (previous.queue.length > found.queue.length) {
            previous.queue.pop();
        }
        for (uint256 i = 0; i < found.queue.length; i++) {
            if (i < previous.queue.length) {
                previous.queue[i] = found.queue[i];
            } else {
                previous.queue.push(found.queue[i]);
            }
        }
    }

    function deposit(uint256 amount) external records {
        target().deposit(amount);
    }

    function borrow(uint256 amount) external records {
        target().borrow(amount);
    }

    function repay(uint256 amount) external records {
        target().repay(amount);
    }

    function advance(uint256 elapsed) external records {
        target().advance(elapsed);
    }

    function accrueFee(uint256 amount) external records {
        target().accrueFee(amount);
    }

    function reserve(uint256 amount) external records {
        target().reserve(amount);
    }

    function payClaim(uint256 amount) external records {
        target().payClaim(amount);
    }

    // A law returns a verdict and a reason. A property function may return
    // only the verdict, and `explain` wants only the reason, so each site here
    // takes one half on purpose. Disabled at each site rather than repository
    // wide, so the next thing this detector catches is read rather than
    // filtered out along with these.

    // slither-disable-next-line unused-return
    function judge(Law law) internal view returns (bool ok) {
        (ok, ) = law.check(target());
    }

    /// @dev Vacuously true before the first call. An engine evaluates
    /// properties against the starting state, where there is no previous
    /// observation to compare with, and reporting a violation there would be
    /// reporting on the harness rather than on the system.
    // slither-disable-next-line unused-return
    function judgePair(PairLaw law) internal view returns (bool ok) {
        if (!previous.queueObserved) {
            return true;
        }
        (ok, ) = law.check(previous, Observe.takeWithQueue(target()));
    }

    /// @notice Why each law decided as it did, in this state.
    /// @dev Every law builds a detail string saying which quantities it
    /// compared and what they were, for the reader who finds the failure
    /// later. A property function may return only a boolean, so the harness
    /// cannot carry that string out through one, and emitting it would make
    /// the property non-view, which is not what an engine expects to call.
    ///
    /// This is where it goes instead. Replay a failing sequence, call this,
    /// and the reason arrives with the numbers in it rather than having to be
    /// worked out again from the call trace.
    /// The width is the count of laws this harness carries, one-state first and
    /// then pair, and `ShippedAdapterTests` holds it to the catalogue. A reason
    /// missing here is the one thing this function exists to prevent, arriving in
    /// the function itself.
    function explain() external view returns (string[9] memory details) {
        Observation memory now_ = Observe.takeWithQueue(target());
        // slither-disable-start unused-return
        (, details[0]) = conserved.check(target());
        (, details[1]) = backed.check(target());
        (, details[2]) = partitioned.check(target());
        (, details[3]) = ordered.check(target());
        (, details[4]) = covered.check(target());
        (, details[5]) = pooled.check(target());
        if (previous.queueObserved) {
            (, details[6]) = falls.check(previous, now_);
            (, details[7]) = atRest.check(previous, now_);
            (, details[8]) = shrinks.check(previous, now_);
        }
        // slither-disable-end unused-return
    }

    function echidna_value_conserved() external view returns (bool) {
        return judge(conserved);
    }

    function echidna_reserves_backed() external view returns (bool) {
        return judge(backed);
    }

    function echidna_held_partitioned() external view returns (bool) {
        return judge(partitioned);
    }

    function echidna_queue_order_preserved() external view returns (bool) {
        return judge(ordered);
    }

    function echidna_reserves_cover_payable() external view returns (bool) {
        return judge(covered);
    }

    function echidna_pooled_claims_cover_open_batches() external view returns (bool) {
        return judge(pooled);
    }

    function echidna_debt_falls_only_against_payment() external view returns (bool) {
        return judgePair(falls);
    }

    function echidna_no_accrual_at_rest() external view returns (bool) {
        return judgePair(atRest);
    }

    function echidna_recorded_claim_never_shrinks() external view returns (bool) {
        return judgePair(shrinks);
    }

    // Medusa looks for `property_` by default. The prefix is an engine's
    // contract rather than a style choice, so the convention detector is
    // answered here rather than obeyed.
    // slither-disable-start naming-convention
    function property_value_conserved() external view returns (bool) {
        return judge(conserved);
    }

    function property_reserves_backed() external view returns (bool) {
        return judge(backed);
    }

    function property_held_partitioned() external view returns (bool) {
        return judge(partitioned);
    }

    function property_queue_order_preserved() external view returns (bool) {
        return judge(ordered);
    }

    function property_reserves_cover_payable() external view returns (bool) {
        return judge(covered);
    }

    function property_pooled_claims_cover_open_batches() external view returns (bool) {
        return judge(pooled);
    }

    function property_debt_falls_only_against_payment() external view returns (bool) {
        return judgePair(falls);
    }

    function property_no_accrual_at_rest() external view returns (bool) {
        return judgePair(atRest);
    }

    function property_recorded_claim_never_shrinks() external view returns (bool) {
        return judgePair(shrinks);
    }
    // slither-disable-end naming-convention
}

/// Every law is expected to hold here, under any sequence.
contract SoundCampaign is Campaign {
    Sound internal immutable system = new Sound();

    function target() internal view override returns (Sound) {
        return system;
    }
}

/// `value_conserved` is expected to fail. The others are expected to hold.
contract MintedClaimsCampaign is Campaign {
    MintedClaims internal immutable system = new MintedClaims();

    function target() internal view override returns (Sound) {
        return system;
    }
}

/// `reserves_backed` is expected to fail. The others are expected to hold.
contract OverReservedCampaign is Campaign {
    OverReserved internal immutable system = new OverReserved();

    function target() internal view override returns (Sound) {
        return system;
    }
}

/// `held_partitioned` is expected to fail. The others are expected to hold.
contract OverPromisedCampaign is Campaign {
    OverPromised internal immutable system = new OverPromised();

    function target() internal view override returns (Sound) {
        return system;
    }
}

/// `debt_falls_only_against_payment` is expected to fail once `forgive` has
/// something to write off. The others are expected to hold.
contract DebtForgivenCampaign is Campaign {
    DebtForgiven internal immutable system = new DebtForgiven();

    function target() internal view override returns (Sound) {
        return system;
    }

    function forgive(uint256 amount) external records {
        system.forgive(amount);
    }
}

/// `no_accrual_at_rest` is expected to fail on the first `poke`. The others
/// are expected to hold.
contract AccruesAtRestCampaign is Campaign {
    AccruesAtRest internal immutable system = new AccruesAtRest();

    function target() internal view override returns (Sound) {
        return system;
    }

    function poke(uint256 amount) external records {
        system.poke(amount);
    }
}

/// Every property here is expected to hold, and that is the finding. The
/// defect this specimen carries is path independence, which no single campaign
/// can see; `test/Pairs.t.sol` is where it is caught. A harness reporting all
/// clear against a contract known to be broken is the sharpest illustration in
/// the corpus of why a passing campaign is not evidence.
contract CompoundsPerStepCampaign is Campaign {
    CompoundsPerStep internal immutable system = new CompoundsPerStep();

    function target() internal view override returns (Sound) {
        return system;
    }
}

/// `recorded_claim_never_shrinks` is expected to fail. The others are expected
/// to hold.
contract ClaimHaircutCampaign is Campaign {
    ClaimHaircut internal immutable system = new ClaimHaircut();

    function target() internal view override returns (Sound) {
        return system;
    }

    function haircut(uint256 index, uint256 amount) external records {
        system.haircut(index, amount);
    }
}

/// `queue_order_preserved` is expected to fail. The others are expected to hold.
contract QueueJumpedCampaign is Campaign {
    QueueJumped internal immutable system = new QueueJumped();

    function target() internal view override returns (Sound) {
        return system;
    }
}

/// `reserves_cover_payable` is expected to fail. The others are expected to hold.
contract PayableBeyondReservesCampaign is Campaign {
    PayableBeyondReserves internal immutable system = new PayableBeyondReserves();

    function target() internal view override returns (Sound) {
        return system;
    }
}

/// `pooled_claims_cover_open_batches` is expected to fail once the market is
/// illiquid and a fee has been charged. The others are expected to hold.
///
/// Reaching it needs four calls in one sequence: a deposit, a borrow, a
/// withdrawal request for more than what is left held, and a fee. The request is
/// the one an earlier draft of this comment left out, and the property cannot be
/// reached without it: without a recorded claim nothing is owed, and without a claim larger
/// than what is held the earmark covers it and the cap does not leak. Echidna
/// shrinks its own sequence to those four.
contract FeeFromQueuedCampaign is Campaign {
    FeeFromQueued internal immutable system = new FeeFromQueued();

    function target() internal view override returns (Sound) {
        return system;
    }
}
