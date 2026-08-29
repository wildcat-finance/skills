// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../src/ICreditObservables.sol";
import {Law} from "../src/Law.sol";
import {Observation, Observe} from "../src/Observation.sol";
import {PairLaw} from "../src/PairLaw.sol";
import {ValueConserved} from "../src/laws/ValueConserved.sol";
import {ReservesBackedByClaims} from "../src/laws/ReservesBackedByClaims.sol";
import {HeldAssetsPartitioned} from "../src/laws/HeldAssetsPartitioned.sol";
import {QueueOrderPreserved} from "../src/laws/QueueOrderPreserved.sol";
import {ReservesCoverPayableClaims} from "../src/laws/ReservesCoverPayableClaims.sol";
import {PooledClaimsCoverOpenBatches} from "../src/laws/PooledClaimsCoverOpenBatches.sol";
import {DebtFallsOnlyAgainstPayment} from "../src/laws/DebtFallsOnlyAgainstPayment.sol";
import {NoAccrualAtRest} from "../src/laws/NoAccrualAtRest.sol";
import {RecordedClaimNeverShrinks} from "../src/laws/RecordedClaimNeverShrinks.sol";

/// @title The corpus, over a target somebody else supplies.
/// @notice `src/campaigns/Specimens.sol` binds one harness to one specimen,
/// which is what proving a law needs and no use to somebody who has a protocol.
/// This is the other direction: the laws, and an address.
///
/// Two shapes come out of that, and the difference is a limit rather than a
/// convenience. A one-state law reads a target and judges what it finds, so
/// `CorpusObserver` can hold any address and ask. A pair law needs the state as
/// it was before the last call, and nothing observes a call it does not sit in
/// front of, so `CorpusDriver` gets the calls routed through it.
///
/// An observer that offered the pair laws would report them holding, always,
/// for the same reason a law that never fires reports holding. That is what
/// this corpus exists to refuse, so the observer does not offer them.
///
/// Neither offers `accrual/path-independent/v1`. It compares two systems
/// advanced over the same span by different routes, and an adapter fronts one
/// target; routing calls through it buys a past, not a second system. The
/// probe in `adapters/foundry/PathIndependenceProbe.sol` takes both, because
/// only the caller can build two instances of their own system from the same
/// start.
abstract contract CorpusBase {
    Law internal immutable conserved = new ValueConserved();
    Law internal immutable backed = new ReservesBackedByClaims();
    Law internal immutable partitioned = new HeldAssetsPartitioned();
    Law internal immutable ordered = new QueueOrderPreserved();
    Law internal immutable covered = new ReservesCoverPayableClaims();
    Law internal immutable pooled = new PooledClaimsCoverOpenBatches();

    /// @notice The system under test, or an adapter over it.
    function target() public view virtual returns (ICreditObservables);

    // slither-disable-next-line unused-return
    function judge(Law law) internal view returns (bool ok) {
        (ok, ) = law.check(target());
    }

    /// @notice The one-state laws that need no withdrawal queue.
    /// @dev Separated because a target with no queue reverts on the other two,
    /// and a revert is no verdict. An integrator whose system has no queue asks
    /// for these three and gets three answers rather than three reverts.
    function coreHolds() public view returns (bool) {
        return judge(conserved) && judge(backed) && judge(partitioned);
    }

    /// @notice The one-state laws that read the withdrawal queue.
    /// @dev Reverts against a target that does not implement
    /// `IWithdrawalQueueObservables`. That is the documented limit and not a
    /// verdict: the state could not be observed.
    function queueHolds() public view returns (bool) {
        return judge(ordered) && judge(covered) && judge(pooled);
    }

    /// @notice Why the three laws that need no queue decided as they did.
    /// @dev Separate from `explainOneState` for the same reason `coreHolds` is
    /// separate from `queueHolds`. A target with no withdrawal queue reverts on
    /// the last two reads, and a single five-part explanation would take the
    /// three answers down with them: an integrator whose system has no queue
    /// would be told nothing at all, including about the laws that were happy
    /// to judge it.
    function explainCore() public view returns (string[3] memory details) {
        // slither-disable-start unused-return
        (, details[0]) = conserved.check(target());
        (, details[1]) = backed.check(target());
        (, details[2]) = partitioned.check(target());
        // slither-disable-end unused-return
    }

    /// @notice Why each one-state law decided as it did.
    /// @dev Reverts against a target with no withdrawal queue. Use
    /// `explainCore` there; it is the same three answers this would have given
    /// before the queue reads took it down.
    ///
    /// The width of the returned array is the count of one-state laws in the
    /// catalogue, and `ShippedAdapterTests` in `tests/test_documents.py` reads
    /// this signature and holds it to that count. Nothing in Solidity can: the
    /// width and the catalogue are two copies of one number, and a test written
    /// against either alone would be wrong the same way the file it checks is.
    function explainOneState() public view returns (string[6] memory details) {
        // slither-disable-start unused-return
        (, details[0]) = conserved.check(target());
        (, details[1]) = backed.check(target());
        (, details[2]) = partitioned.check(target());
        (, details[3]) = ordered.check(target());
        (, details[4]) = covered.check(target());
        (, details[5]) = pooled.check(target());
        // slither-disable-end unused-return
    }
}

/// @title The corpus over a target nobody routes calls through.
/// @notice Point it at an address and the one-state laws run, whatever else is
/// driving that contract. This is the form to reach for when the system under
/// test is already deployed, already driven by somebody else's harness, or
/// simply not yours to front.
///
/// It offers no pair law, and that is the whole design. See `CorpusBase`.
contract CorpusObserver is CorpusBase {
    ICreditObservables internal immutable system;

    constructor(ICreditObservables target_) {
        system = target_;
    }

    function target() public view override returns (ICreditObservables) {
        return system;
    }
}

/// @title The corpus over a target whose calls come through here.
/// @notice Extend this, write your protocol's entry points, and put `records`
/// on every one that changes state. That modifier is the entire mechanism: it
/// snapshots the system on the way in, so a pair law has a past to compare
/// with.
///
/// The entry points are yours to write because they are yours to name. A base
/// cannot proxy a surface it has never seen, and one that tried would need
/// either an ABI it cannot know or a fallback that forwards calldata blindly --
/// which would forward the call that breaks a law without ever recording the
/// state before it.
///
/// A state-changing entry point without `records` is not an error the compiler
/// can catch. It shows as pair laws that hold through the call and say nothing,
/// which reads exactly like a system that is behaving.
abstract contract CorpusDriver is CorpusBase {
    PairLaw internal immutable falls = new DebtFallsOnlyAgainstPayment();
    PairLaw internal immutable atRest = new NoAccrualAtRest();
    PairLaw internal immutable shrinks = new RecordedClaimNeverShrinks();

    /// @notice The system as it was immediately before the last recorded call.
    Observation internal previous;

    /// @notice How many calls this adapter has recorded a state for.
    /// @dev Public because a pair law that was never given a past reports
    /// holding, and nothing about that verdict distinguishes it from a law that
    /// held. An integrator who forgets `records` on an entry point sees three
    /// green properties and a system that was never judged.
    ///
    /// This is the number that tells them apart. Assert it is rising in your
    /// own harness, or read it after a campaign: zero recorded calls means the
    /// succession laws searched nothing, whatever they reported.
    uint256 public recordedCalls;

    modifier records() {
        remember();
        _;
    }

    /// @dev Field by field, and the queue entry by entry. A whole-struct
    /// assignment from memory to storage needs the IR pipeline, and turning
    /// that on would change how everybody consuming this corpus compiles.
    function remember() internal {
        Observation memory found = Observe.takeWithQueue(target());
        recordedCalls++;
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

    /// @dev Vacuously true before the first recorded call. An engine evaluates
    /// properties against the starting state, where there is no past to compare
    /// with, and a violation reported there would be a report about the harness.
    // slither-disable-next-line unused-return
    function judgePair(PairLaw law) internal view returns (bool ok) {
        if (!previous.queueObserved) {
            return true;
        }
        (ok, ) = law.check(previous, Observe.takeWithQueue(target()));
    }

    function successionHolds() public view returns (bool) {
        return judgePair(falls) && judgePair(atRest) && judgePair(shrinks);
    }

    /// @notice Whether the succession laws have judged anything at all.
    /// @dev `successionHolds` returning true means one of two things, and this
    /// says which. Read them together or the first one is worth nothing.
    function successionExercised() public view returns (bool) {
        return recordedCalls > 0;
    }

    /// @notice Why each pair law decided as it did, across the last call.
    function explainSuccession() public view returns (string[3] memory details) {
        if (!previous.queueObserved) {
            details[0] = "no call was recorded, so no transition was judged";
            details[1] = details[0];
            details[2] = details[0];
            return details;
        }
        Observation memory now_ = Observe.takeWithQueue(target());
        // slither-disable-start unused-return
        (, details[0]) = falls.check(previous, now_);
        (, details[1]) = atRest.check(previous, now_);
        (, details[2]) = shrinks.check(previous, now_);
        // slither-disable-end unused-return
    }
}
