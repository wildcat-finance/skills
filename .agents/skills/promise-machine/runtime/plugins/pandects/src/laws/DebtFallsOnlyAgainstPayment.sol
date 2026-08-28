// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Observation} from "../Observation.sol";
import {PairLaw} from "../PairLaw.sol";

/// @title Debt goes down only when assets come in.
/// @notice What a borrower owes falls only against the system receiving at
/// least as much. Debt that shrinks with nothing arriving has been forgiven,
/// written off, or lost to an accounting error, and from outside those three
/// look identical.
///
/// The observable form matters. "Debt never decreases between repayments"
/// cannot be checked, because nothing a target reports says a repayment
/// happened; a law written that way would need the harness to tell it, and a
/// law that trusts the harness is a law about the harness. What is observable
/// is that held assets rose by at least the fall, which is what a repayment
/// looks like from outside and what a write-off does not.
///
/// The law is one-directional on purpose. It says nothing about debt rising:
/// interest does that legitimately, and `accrual/no-accrual-at-rest/v1` is
/// where rising debt is constrained.
///
/// Exact, with no tolerance. Two subtractions and a comparison.
contract DebtFallsOnlyAgainstPayment is PairLaw {
    function id() external pure override returns (string memory) {
        return "accrual/debt-falls-only-against-payment/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "Debt falls only against held assets rising by at least the fall.";
    }

    function check(Observation memory earlier, Observation memory later)
        external
        pure
        override
        returns (bool held, string memory detail)
    {
        if (later.totalDebt >= earlier.totalDebt) {
            return (true, "debt did not fall between the two observations");
        }
        uint256 fall = earlier.totalDebt - later.totalDebt;
        uint256 arrived = later.totalAssets > earlier.totalAssets
            ? later.totalAssets - earlier.totalAssets
            : 0;
        if (arrived >= fall) {
            return (true, "debt fell no further than held assets rose");
        }
        return (false, "debt fell further than held assets rose");
    }
}
