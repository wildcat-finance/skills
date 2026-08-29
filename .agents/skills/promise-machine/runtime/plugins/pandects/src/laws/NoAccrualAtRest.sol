// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Observation} from "../Observation.sol";
import {PairLaw} from "../PairLaw.sol";

/// @title Interest needs time to exist.
/// @notice Between two observations that describe the same moment, debt rises
/// only against held assets leaving. Borrowing raises debt with no time
/// passing and moves assets out the door to do it. Interest raises debt with
/// nothing moving, and cannot happen at a standstill.
///
/// The naive statement -- that nothing changes when no time passes -- is false
/// of every correct system, which is worth saying plainly because it is the
/// easy version to write. A deposit, a borrowing, a repayment and a fee all
/// land within one block and all move the numbers. Time is not what makes them
/// legitimate; the assets moving is. So the law watches the one quantity that
/// has no business moving on its own, and admits every rise that was paid for
/// in liquidity.
///
/// Interest compounding on a read, a rate applied on a call rather than on a
/// duration, an accrual that runs twice for one block: each shows up here as
/// debt appearing while the clock stands still and nothing leaving to explain
/// it.
///
/// This law says nothing about pairs at different times. It holds on them, and
/// says so, because a pair spanning real time is a state of the world rather
/// than a mistake by whoever built the pair. That is the opposite of what
/// `accrual/path-independent/v1` does with a pair it cannot judge, and the
/// asymmetry is deliberate: there, an ill-formed pair is a harness error, and
/// holding would hide it.
///
/// Exact, with no tolerance. Two subtractions and a comparison.
contract NoAccrualAtRest is PairLaw {
    function id() external pure override returns (string memory) {
        return "accrual/no-accrual-at-rest/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "At equal observation times, debt rises only against held assets leaving.";
    }

    function check(Observation memory earlier, Observation memory later)
        external
        pure
        override
        returns (bool held, string memory detail)
    {
        if (earlier.observedAt != later.observedAt) {
            return (true, "time passed between the observations");
        }
        if (later.totalDebt <= earlier.totalDebt) {
            return (true, "debt did not rise while time stood still");
        }
        uint256 rise = later.totalDebt - earlier.totalDebt;
        uint256 left = earlier.totalAssets > later.totalAssets
            ? earlier.totalAssets - later.totalAssets
            : 0;
        if (left >= rise) {
            return (true, "debt rose no further than held assets left");
        }
        return (false, "debt rose while time stood still and assets stayed");
    }
}
