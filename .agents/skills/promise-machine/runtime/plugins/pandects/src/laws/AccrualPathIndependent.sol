// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Observation} from "../Observation.sol";
import {PairLaw} from "../PairLaw.sol";

/// @title The same span accrues the same interest, however it is cut up.
/// @notice Two systems start identically. One is advanced once across a span;
/// the other is advanced across the same span in `subdivisions` equal steps.
/// Under linear accrual on principal they owe the same at the end, and the
/// only thing that can separate them is integer truncation.
///
/// This is the law that catches accrual charged per call rather than per
/// second, and interest quietly compounding because each step accrues on a
/// balance the previous step already grew. Both are invisible in a single
/// state and invisible across one transition. They show up only when the same
/// elapsed time is reached by two different routes, which is why this law is
/// the one differential law in the corpus: its pair is two systems, not one
/// system and its past.
///
/// One thing this law cannot check, and it is the sharpest edge on it. Nothing
/// in either observation says how many steps the subdivided run took. The
/// bound comes from `subdivisions`, fixed when the law is deployed, and a law
/// built for two steps shown a run of eight compares against a bound five
/// sixths too small; built for a thousand and shown two, it accepts a gap
/// hundreds of times wider than the arithmetic allows. Both are silent, and no
/// reading of the two observations can tell them apart.
///
/// So the number is part of the question rather than part of the answer. Deploy
/// the law with the count the run actually used, or the verdict is about a run
/// nobody made. The applicability says so and `test/Pairs.t.sol` shows both
/// mistakes producing wrong verdicts, because a hazard nobody has watched fail
/// is a hazard people assume is handled.
///
/// A pair at different observation times is refused rather than held. That is
/// the opposite of `accrual/no-accrual-at-rest/v1`, and the difference is
/// whose mistake it is. A pair spanning real time is something the world does;
/// a pair of runs that did not reach the same moment is something the harness
/// did, and a law that held there would report success for a comparison nobody
/// made.
///
/// The bound is the one tolerance in the corpus, and it names its arithmetic
/// rather than being fitted to a test. Let the exact interest for one step be
/// `x`. The subdivided run accrues `n * floor(x)`; the single run accrues
/// `floor(n * x)`. The gap between those is at most `n - 1`, because each of
/// the `n` truncations discards less than one unit and the single truncation
/// discards less than one in the other direction. So `n - 1` units, exactly,
/// for `n` subdivisions.
contract AccrualPathIndependent is PairLaw {
    /// @notice How many steps the subdivided run was advanced in.
    uint256 public immutable subdivisions;

    constructor(uint256 subdivisions_) {
        subdivisions = subdivisions_;
    }

    function id() external pure override returns (string memory) {
        return "accrual/path-independent/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "One long step and the same span in equal small steps agree on debt, within one unit per step less one.";
    }

    /// @notice The widest gap this law accepts.
    /// @dev Zero subdivisions describes no subdivided run at all, so the two
    /// observations must agree exactly. Written as a floor rather than a
    /// rejection because a law does not revert to mean anything.
    function tolerance() public view returns (uint256) {
        return subdivisions == 0 ? 0 : subdivisions - 1;
    }

    function check(Observation memory earlier, Observation memory later)
        external
        view
        override
        returns (bool held, string memory detail)
    {
        if (earlier.observedAt != later.observedAt) {
            return (
                false,
                "the two runs did not reach the same moment, so nothing was compared"
            );
        }
        uint256 gap = earlier.totalDebt > later.totalDebt
            ? earlier.totalDebt - later.totalDebt
            : later.totalDebt - earlier.totalDebt;
        if (gap <= tolerance()) {
            return (true, "the two runs agree on debt within the bound");
        }
        return (false, "the two runs disagree on debt beyond truncation");
    }
}
