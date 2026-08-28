// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Observation, Observe} from "../src/Observation.sol";
import {PairLaw} from "../src/PairLaw.sol";
import {DebtFallsOnlyAgainstPayment} from "../src/laws/DebtFallsOnlyAgainstPayment.sol";
import {NoAccrualAtRest} from "../src/laws/NoAccrualAtRest.sol";
import {AccrualPathIndependent} from "../src/laws/AccrualPathIndependent.sol";
import {RecordedClaimNeverShrinks} from "../src/laws/RecordedClaimNeverShrinks.sol";
import {Sound} from "../specimens/Sound.sol";
import {MintedClaims} from "../specimens/MintedClaims.sol";
import {OverReserved} from "../specimens/OverReserved.sol";
import {OverPromised} from "../specimens/OverPromised.sol";
import {DebtForgiven} from "../specimens/DebtForgiven.sol";
import {AccruesAtRest} from "../specimens/AccruesAtRest.sol";
import {CompoundsPerStep} from "../specimens/CompoundsPerStep.sol";
import {ClaimHaircut} from "../specimens/ClaimHaircut.sol";
import {QueueJumped} from "../specimens/QueueJumped.sol";
import {PayableBeyondReserves} from "../specimens/PayableBeyondReserves.sol";

/// @title The diagonal, for the laws that judge a pair.
/// @notice Three of these laws compare a system with its own past. They are
/// checked the same way the one-state diagonal is: each fails exactly the
/// specimen written for it and holds against every other, including against
/// every transition a correct system can make.
///
/// The fourth is different in kind and is tested apart from the other three.
/// `accrual/path-independent/v1` compares two systems advanced differently
/// over the same span, so a before-and-after pair of one system is not
/// something it can judge -- and it says so rather than holding, which is
/// asserted below.
contract PairsTest {
    using Observe for Sound;

    DebtFallsOnlyAgainstPayment internal falls;
    NoAccrualAtRest internal atRest;
    RecordedClaimNeverShrinks internal shrinks;
    AccrualPathIndependent internal path;

    uint256 internal constant FALLS = 0;
    uint256 internal constant AT_REST = 1;
    uint256 internal constant SHRINKS = 2;
    uint256 internal constant COUNT = 3;
    uint256 internal constant NOTHING = type(uint256).max;

    /// @dev Two subdivisions, so the bound is one unit. Small on purpose: a
    /// generous bound would let a compounding system slip through, and the
    /// point of the bound is that it is derived rather than chosen.
    uint256 internal constant SUBDIVISIONS = 2;

    /// @dev Large enough that the truncation the bound describes is visible.
    /// At this principal the sound reference lands exactly on the bound, one
    /// unit apart, which is the strongest evidence available that the bound is
    /// the arithmetic rather than a margin somebody picked.
    uint256 internal constant PRINCIPAL = 100_000;

    /// @dev Half a year each, so two of them make the single step below.
    uint256 internal constant HALF_SPAN = 182.5 days;
    uint256 internal constant WHOLE_SPAN = 365 days;

    function setUp() public {
        falls = new DebtFallsOnlyAgainstPayment();
        atRest = new NoAccrualAtRest();
        shrinks = new RecordedClaimNeverShrinks();
        path = new AccrualPathIndependent(SUBDIVISIONS);
    }

    function succession() internal view returns (PairLaw[COUNT] memory) {
        return [PairLaw(falls), PairLaw(atRest), PairLaw(shrinks)];
    }

    function assertPairDiagonal(
        Observation memory earlier,
        Observation memory later,
        uint256 breaks
    ) internal view {
        PairLaw[COUNT] memory all = succession();
        for (uint256 i = 0; i < COUNT; i++) {
            (bool held, ) = all[i].check(earlier, later);
            if (i == breaks) {
                require(!held, "the law written for this specimen did not catch it");
            } else {
                require(held, "a law caught a transition it was not written for");
            }
        }
    }

    /// Every transition a correct system can make, each one judged.
    function assertEveryTransitionHolds(Sound target) internal {
        // Deliberately not a loop over an operation list: each call needs its
        // own argument, and a table of selectors would put the harness between
        // the law and the thing it judges.
        Observation memory earlier = Observe.takeWithQueue(target);
        Observation memory later;

        target.deposit(1000);
        later = Observe.takeWithQueue(target);
        assertPairDiagonal(earlier, later, NOTHING);

        earlier = later;
        target.borrow(400);
        later = Observe.takeWithQueue(target);
        assertPairDiagonal(earlier, later, NOTHING);

        earlier = later;
        target.advance(HALF_SPAN);
        later = Observe.takeWithQueue(target);
        assertPairDiagonal(earlier, later, NOTHING);

        earlier = later;
        target.repay(50);
        later = Observe.takeWithQueue(target);
        assertPairDiagonal(earlier, later, NOTHING);

        earlier = later;
        target.accrueFee(20);
        later = Observe.takeWithQueue(target);
        assertPairDiagonal(earlier, later, NOTHING);

        earlier = later;
        target.reserve(30);
        later = Observe.takeWithQueue(target);
        assertPairDiagonal(earlier, later, NOTHING);

        earlier = later;
        target.payClaim(10);
        later = Observe.takeWithQueue(target);
        assertPairDiagonal(earlier, later, NOTHING);
    }

    // -- the sound reference ------------------------------------------------

    function test_no_transition_of_the_sound_reference_breaks_a_pair_law() external {
        assertEveryTransitionHolds(new Sound());
    }

    // -- the diagonal -------------------------------------------------------

    function test_debt_forgiven_breaks_the_payment_law_alone() external {
        DebtForgiven target = new DebtForgiven();
        target.deposit(1);
        target.borrow(1);
        target.accrueFee(1);
        Observation memory earlier = Observe.takeWithQueue(target);
        target.forgive(1);
        assertPairDiagonal(earlier, Observe.takeWithQueue(target), FALLS);
    }

    function test_accrues_at_rest_breaks_the_rest_law_alone() external {
        AccruesAtRest target = new AccruesAtRest();
        Observation memory earlier = Observe.takeWithQueue(target);
        target.poke(1);
        assertPairDiagonal(earlier, Observe.takeWithQueue(target), AT_REST);
    }

    function test_claim_haircut_breaks_the_claim_law_alone() external {
        ClaimHaircut target = new ClaimHaircut();
        target.deposit(1);
        target.reserve(1);
        Observation memory earlier = Observe.takeWithQueue(target);
        target.haircut(0, 1);
        assertPairDiagonal(earlier, Observe.takeWithQueue(target), SHRINKS);
    }

    // -- every other specimen, against every transition ----------------------

    function test_the_one_state_specimens_break_no_pair_law() external {
        assertEveryTransitionHolds(new MintedClaims());
        assertEveryTransitionHolds(new OverReserved());
        assertEveryTransitionHolds(new OverPromised());
    }

    function test_the_other_pair_specimens_break_no_pair_law_in_passing() external {
        assertEveryTransitionHolds(new CompoundsPerStep());
        assertEveryTransitionHolds(new QueueJumped());
        assertEveryTransitionHolds(new PayableBeyondReserves());
    }

    // -- path independence ---------------------------------------------------

    /// Two systems from the same start, advanced over the same span by
    /// different routes.
    function race(Sound coarse, Sound fine)
        internal
        returns (Observation memory, Observation memory)
    {
        coarse.deposit(PRINCIPAL);
        coarse.borrow(PRINCIPAL);
        fine.deposit(PRINCIPAL);
        fine.borrow(PRINCIPAL);

        coarse.advance(WHOLE_SPAN);
        for (uint256 i = 0; i < SUBDIVISIONS; i++) {
            fine.advance(HALF_SPAN);
        }
        return (Observe.take(coarse), Observe.take(fine));
    }

    function test_the_sound_reference_is_path_independent() external {
        (Observation memory coarse, Observation memory fine) =
            race(new Sound(), new Sound());
        (bool held, ) = path.check(coarse, fine);
        require(held, "linear accrual on principal was not path independent");
    }

    function test_compounding_per_step_breaks_path_independence_alone() external {
        (Observation memory coarse, Observation memory fine) =
            race(new CompoundsPerStep(), new CompoundsPerStep());
        (bool held, ) = path.check(coarse, fine);
        require(!held, "compounding was not caught by the path-independence law");
    }

    function test_no_other_specimen_breaks_path_independence() external {
        Sound[6] memory coarse = [
            Sound(new MintedClaims()),
            Sound(new OverReserved()),
            Sound(new OverPromised()),
            Sound(new DebtForgiven()),
            Sound(new AccruesAtRest()),
            Sound(new QueueJumped())
        ];
        Sound[6] memory fine = [
            Sound(new MintedClaims()),
            Sound(new OverReserved()),
            Sound(new OverPromised()),
            Sound(new DebtForgiven()),
            Sound(new AccruesAtRest()),
            Sound(new QueueJumped())
        ];
        for (uint256 i = 0; i < 6; i++) {
            (Observation memory a, Observation memory b) = race(coarse[i], fine[i]);
            (bool held, ) = path.check(a, b);
            require(held, "path independence caught a specimen it was not written for");
        }
    }

    /// @notice The bound at its edge, and one unit past it.
    /// @dev Built by hand rather than by running a system, because the claim is
    /// about the law's arithmetic and not about any particular target. Two
    /// subdivisions truncate at most once each against a single truncation the
    /// other way, so the widest honest gap is one unit.
    function test_the_bound_holds_at_its_edge_and_not_beyond() external view {
        require(path.tolerance() == SUBDIVISIONS - 1, "the bound is not n-1");

        Observation memory a;
        Observation memory b;
        a.observedAt = 1000;
        b.observedAt = 1000;
        a.totalDebt = 500;

        b.totalDebt = 500 + path.tolerance();
        (bool atEdge, ) = path.check(a, b);
        require(atEdge, "a gap of exactly the bound was reported as a violation");

        b.totalDebt = 500 + path.tolerance() + 1;
        (bool beyond, ) = path.check(a, b);
        require(!beyond, "a gap one unit past the bound was not reported");
    }

    /// @notice A bound built for the wrong run gives the wrong verdict.
    /// @dev The hazard this law cannot defend against, shown failing in both
    /// directions rather than described. Nothing in either observation says how
    /// many steps the subdivided run took, so the count is part of the
    /// question: a law deployed with the wrong one is answering about a run
    /// nobody made, and it does so without any sign that it has.
    function test_a_bound_built_for_the_wrong_run_is_wrong_in_both_directions()
        external
    {
        (Observation memory coarse, Observation memory fine) =
            race(new CompoundsPerStep(), new CompoundsPerStep());

        // The compounding specimen ran in two steps. Asked with the count it
        // used, the law catches it.
        (bool correct, ) = path.check(coarse, fine);
        require(!correct, "the law built for this run did not catch it");

        // Asked with a count far larger than the run used, the same gap fits
        // inside the bound and the same defect passes.
        AccrualPathIndependent generous = new AccrualPathIndependent(1000);
        (bool tooWide, ) = generous.check(coarse, fine);
        require(tooWide, "the bound did not widen with the count, so this proves nothing");

        // And the sound reference, path independent to within one unit, is
        // reported as violated by a law built for a single step.
        (Observation memory a, Observation memory b) = race(new Sound(), new Sound());
        AccrualPathIndependent mean = new AccrualPathIndependent(1);
        (bool tooTight, ) = mean.check(a, b);
        require(!tooTight, "a correct system was not misjudged by a bound that is too tight");
    }

    /// @notice A pair it cannot judge is refused, not held.
    /// @dev The asymmetry with `no-accrual-at-rest` is deliberate and worth a
    /// test rather than a comment. A pair spanning real time is a state of the
    /// world, and that law holds on it. Two runs that never reached the same
    /// moment are a mistake by whoever built the pair, and holding there would
    /// report a comparison nobody made.
    function test_a_pair_at_different_times_is_refused() external view {
        Observation memory a;
        Observation memory b;
        a.observedAt = 1000;
        b.observedAt = 1001;
        a.totalDebt = 500;
        b.totalDebt = 500;
        (bool held, ) = path.check(a, b);
        require(!held, "two runs at different moments were compared anyway");

        (bool restHeld, ) = atRest.check(a, b);
        require(restHeld, "a pair spanning real time was treated as a mistake");
    }

    // -- what a pair law must not do -----------------------------------------

    /// @notice A queue law handed observations nobody read the queue into
    /// refuses rather than holds.
    function test_an_unobserved_queue_is_refused() external {
        Sound target = new Sound();
        Observation memory earlier = Observe.take(target);
        Observation memory later = Observe.take(target);
        (bool held, string memory detail) = shrinks.check(earlier, later);
        require(!held, "a law about the queue held on a pair with no queue in it");
        require(bytes(detail).length > 0, "a verdict without a detail");
    }

    /// @notice A law that does not need the queue is judgeable without one.
    /// @dev The other half of the applicability claim, and the half nothing
    /// asserted. `recorded-claim-never-shrinks` refuses a pair with no queue in
    /// it, which is above. The two accrual laws must do the opposite: read a
    /// pair taken with `Observe.take`, decide, and never touch the queue at
    /// all. Their independence from it is visible in the signature, and a
    /// signature is not evidence -- a law could read `queueObserved` and refuse,
    /// exactly as its neighbour does, and nothing here would have noticed.
    function test_the_laws_that_need_no_queue_judge_a_pair_without_one() external {
        Sound target = new Sound();
        target.deposit(1000);
        target.borrow(400);

        Observation memory earlier = Observe.take(target);
        require(!earlier.queueObserved, "the queue was read after all");

        // A repayment: debt falls, held assets rise by the same, both laws hold.
        target.repay(100);
        Observation memory later = Observe.take(target);
        (bool paidBack, ) = falls.check(earlier, later);
        (bool atRestHeld, ) = atRest.check(earlier, later);
        require(paidBack, "a repayment was read as an unpaid fall in debt");
        require(atRestHeld, "a repayment was read as accrual at rest");

        // And they decide the other way on a pair with no queue in it either,
        // so the passes above are verdicts rather than a law declining to look.
        //
        // Built field by field rather than copied from `later`. A memory struct
        // assigned to another memory variable shares its storage, so mutating
        // the second mutates the first, and the law would have been handed one
        // observation twice -- which holds, and proves nothing at all.
        Observation memory before;
        Observation memory after_;
        before.totalAssets = later.totalAssets;
        before.totalDebt = later.totalDebt;
        before.observedAt = later.observedAt;
        after_.totalAssets = later.totalAssets;
        after_.totalDebt = later.totalDebt - 1;
        after_.observedAt = later.observedAt;

        (bool caught, ) = falls.check(before, after_);
        require(!caught, "a fall with nothing arriving was not caught");

        after_.totalDebt = later.totalDebt + 1;
        (bool rose, ) = atRest.check(before, after_);
        require(!rose, "debt appearing at rest was not caught");

        require(!before.queueObserved && !after_.queueObserved, "a queue crept in");
    }

    function test_every_pair_law_carries_an_identifier_and_a_statement() external view {
        PairLaw[COUNT] memory all = succession();
        for (uint256 i = 0; i < COUNT; i++) {
            require(bytes(all[i].id()).length > 0, "a law with no id");
            require(bytes(all[i].statement()).length > 0, "a law with no statement");
        }
        require(bytes(path.id()).length > 0, "a law with no id");
        require(bytes(path.statement()).length > 0, "a law with no statement");
    }
}
