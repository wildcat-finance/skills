// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Observation, Observe} from "../../src/Observation.sol";
import {DebtFallsOnlyAgainstPayment} from "../../src/laws/DebtFallsOnlyAgainstPayment.sol";
import {NoAccrualAtRest} from "../../src/laws/NoAccrualAtRest.sol";
import {AccrualPathIndependent} from "../../src/laws/AccrualPathIndependent.sol";
import {Sound} from "../../specimens/Sound.sol";
import {DebtForgiven} from "../../specimens/DebtForgiven.sol";
import {AccruesAtRest} from "../../specimens/AccruesAtRest.sol";
import {CompoundsPerStep} from "../../specimens/CompoundsPerStep.sol";

/// @title The counterexamples for the accrual family.
/// @notice One reduced sequence per law, replayable with no fuzzer, no seed
/// and no engine. This is the corpus's third requirement: a law that has only
/// ever been argued for is not reduced, and a failure nobody can reproduce on
/// demand is a story rather than a finding.
///
/// These differ from the conservation counterexamples in one way that matters.
/// A conservation counterexample is a state, so replaying it means reaching
/// that state. An accrual counterexample is a transition, so replaying it means
/// holding an observation, letting the system move, and comparing. The
/// snapshot is the thing that makes it replayable at all.
contract AccrualCounterexamples {
    uint256 internal constant PRINCIPAL = 100_000;
    uint256 internal constant HALF_SPAN = 182.5 days;
    uint256 internal constant WHOLE_SPAN = 365 days;

    /// `DebtForgiven.deposit(1)`, `borrow(1)`, `accrueFee(1)`, `forgive(1)`.
    /// Four calls, and four is the floor: the write-off is charged against
    /// fees, fees come from claims, claims come from a deposit, and there is no
    /// debt to forgive without a borrowing.
    ///
    /// Debt goes from one to nothing while held assets stay at nothing. The
    /// books balance on both sides of the transition, which is why no
    /// conservation law sees it.
    function test_debt_falls_only_against_payment_counterexample() external {
        DebtForgiven target = new DebtForgiven();
        target.deposit(1);
        target.borrow(1);
        target.accrueFee(1);

        Observation memory earlier = Observe.take(target);
        require(earlier.totalDebt == 1, "debt is not 1");
        require(earlier.totalAssets == 0, "held is not 0");
        require(earlier.accruedFees == 1, "fees is not 1");

        target.forgive(1);
        Observation memory later = Observe.take(target);
        require(later.totalDebt == 0, "debt is not 0");
        require(later.totalAssets == 0, "held moved, so nothing was forgiven");

        DebtFallsOnlyAgainstPayment law = new DebtFallsOnlyAgainstPayment();
        (bool held, ) = law.check(earlier, later);
        require(!held, "the counterexample no longer reproduces");
    }

    /// `AccruesAtRest.poke(1)`, one call, from an empty system. Nothing has
    /// been deposited, nothing borrowed, and the borrower owes a unit anyway.
    ///
    /// The shortest counterexample in the corpus, and the point of it is that
    /// the state it produces is perfectly consistent: one owed, one claimed,
    /// the books balanced. Only the clock says otherwise.
    function test_no_accrual_at_rest_counterexample() external {
        AccruesAtRest target = new AccruesAtRest();

        Observation memory earlier = Observe.take(target);
        require(earlier.totalDebt == 0, "debt is not 0");

        target.poke(1);
        Observation memory later = Observe.take(target);
        require(later.observedAt == earlier.observedAt, "the clock moved");
        require(later.totalDebt == 1, "debt is not 1");
        require(later.totalAssets == earlier.totalAssets, "assets moved");

        NoAccrualAtRest law = new NoAccrualAtRest();
        (bool held, ) = law.check(earlier, later);
        require(!held, "the counterexample no longer reproduces");
    }

    /// Two `CompoundsPerStep` systems, each `deposit(100000)` and
    /// `borrow(100000)`. One is advanced 365 days once; the other 182.5 days
    /// twice. Six calls across two systems, which is the floor for a law whose
    /// pair is two systems.
    ///
    /// The arithmetic, so the bound can be checked rather than believed. The
    /// sound reference accrues 9999 over the single step and 4999 twice over
    /// the subdivided one, a gap of exactly one unit: the bound for two
    /// subdivisions is `n - 1`, and one is where truncation actually lands. The
    /// compounding specimen accrues 4999 and then 5249, because its second step
    /// charges on the first step's interest, for a gap of 249.
    ///
    /// One unit is the arithmetic. Two hundred and forty-nine is a defect.
    function test_accrual_path_independent_counterexample() external {
        AccrualPathIndependent law = new AccrualPathIndependent(2);
        require(law.tolerance() == 1, "the bound is not one unit");

        Sound soundCoarse = new Sound();
        Sound soundFine = new Sound();
        (Observation memory a, Observation memory b) = race(soundCoarse, soundFine);
        require(a.totalDebt == PRINCIPAL + 9999, "the single step did not accrue 9999");
        require(b.totalDebt == PRINCIPAL + 9998, "the subdivided run did not accrue 9998");
        (bool soundHeld, ) = law.check(a, b);
        require(soundHeld, "the sound reference stopped being path independent");

        CompoundsPerStep coarse = new CompoundsPerStep();
        CompoundsPerStep fine = new CompoundsPerStep();
        (Observation memory c, Observation memory d) = race(coarse, fine);
        require(c.totalDebt == PRINCIPAL + 9999, "the single step did not accrue 9999");
        require(d.totalDebt == PRINCIPAL + 10248, "the subdivided run did not accrue 10248");

        (bool held, ) = law.check(c, d);
        require(!held, "the counterexample no longer reproduces");
    }

    function race(Sound coarse, Sound fine)
        internal
        returns (Observation memory, Observation memory)
    {
        coarse.deposit(PRINCIPAL);
        coarse.borrow(PRINCIPAL);
        fine.deposit(PRINCIPAL);
        fine.borrow(PRINCIPAL);

        coarse.advance(WHOLE_SPAN);
        fine.advance(HALF_SPAN);
        fine.advance(HALF_SPAN);

        return (Observe.take(coarse), Observe.take(fine));
    }
}
