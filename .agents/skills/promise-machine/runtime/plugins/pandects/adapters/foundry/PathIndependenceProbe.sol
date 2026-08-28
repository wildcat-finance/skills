// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../../src/ICreditObservables.sol";
import {Observation, Observe} from "../../src/Observation.sol";
import {AccrualPathIndependent} from "../../src/laws/AccrualPathIndependent.sol";

/// @title The ninth law, which no campaign can carry.
/// @notice `accrual/path-independent/v1` compares two systems started
/// identically and advanced over the same span by different routes. An adapter
/// fronts one target; routing calls through it buys a past to read, not a
/// second system. So this is not an adapter and not a campaign property. It is
/// a probe, and the caller supplies both systems, because only they can build
/// two instances of their own from the same start.
///
/// Deploy it with the subdivision count the fine run actually used. Nothing in
/// either observation reveals a mismatch, so a probe built for the wrong count
/// compares against the wrong bound and gives no sign that it has. That hazard
/// belongs to the law and is documented there; this contract is where a caller
/// meets it.
contract PathIndependenceProbe {
    AccrualPathIndependent public immutable law;

    constructor(uint256 subdivisions) {
        law = new AccrualPathIndependent(subdivisions);
    }

    /// @notice The widest gap the law accepts, for the count it was built with.
    function tolerance() external view returns (uint256) {
        return law.tolerance();
    }

    /// @notice Judge two systems that should have reached the same moment.
    /// @param coarse The system advanced once across the whole span.
    /// @param fine The system advanced across the same span in equal steps.
    /// @return held True when the two agree on debt within the bound.
    /// @return detail What was compared, and what it decided.
    function check(ICreditObservables coarse, ICreditObservables fine)
        external
        view
        returns (bool held, string memory detail)
    {
        Observation memory a = Observe.take(coarse);
        Observation memory b = Observe.take(fine);
        return law.check(a, b);
    }
}
