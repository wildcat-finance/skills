// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../ICreditObservables.sol";
import {Law} from "../Law.sol";

/// @title Held assets are partitioned, not double counted.
/// @notice What is reserved against withdrawals and what a borrower may take
/// are drawn from the same held assets, and together they never exceed them.
/// A system that offers the borrower liquidity it has already promised to a
/// departing lender has sold the same asset twice, and whichever of them
/// arrives second finds it gone.
///
/// Exact, with no tolerance. Nothing here divides.
contract HeldAssetsPartitioned is Law {
    function id() external pure override returns (string memory) {
        return "conservation/held-assets-partitioned/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "Reserved assets plus borrowable assets never exceed assets held.";
    }

    function check(ICreditObservables target)
        external
        view
        override
        returns (bool held, string memory detail)
    {
        uint256 reserved = target.reservedAssets();
        uint256 borrowable = target.borrowableAssets();
        uint256 assets = target.totalAssets();

        // Unchecked with the overflow reported, for the reason given in
        // ValueConserved: a revert here would be silence where the numbers are
        // furthest wrong.
        uint256 committed;
        unchecked {
            committed = reserved + borrowable;
        }
        if (committed < reserved) {
            return (false, "reserved plus borrowable overflows");
        }
        if (committed <= assets) {
            return (true, "reserved and borrowable fit within assets held");
        }
        return (false, "reserved plus borrowable exceeds assets held");
    }
}
