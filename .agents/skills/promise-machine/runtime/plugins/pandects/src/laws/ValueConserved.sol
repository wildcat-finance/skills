// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../ICreditObservables.sol";
import {Law} from "../Law.sol";

/// @title Value is conserved across the system.
/// @notice What the system holds, plus what its borrowers owe, is exactly what
/// its lenders may claim plus the fees it has accrued. Value does not appear
/// and does not vanish.
///
/// The equality is the point. A system that writes down a defaulted debt
/// without writing down the claims against it has made value disappear from
/// one side and not the other, and this is the law that says so. A system that
/// credits a lender without receiving anything has made value appear.
///
/// Exact, with no tolerance. Nothing here divides, so nothing here rounds.
contract ValueConserved is Law {
    function id() external pure override returns (string memory) {
        return "conservation/value-conserved/v1";
    }

    function statement() external pure override returns (string memory) {
        return
            "Assets held plus debt owed equals lender claims plus accrued fees.";
    }

    function check(ICreditObservables target)
        external
        view
        override
        returns (bool held, string memory detail)
    {
        uint256 assets = target.totalAssets();
        uint256 debt = target.totalDebt();
        uint256 claims = target.totalLenderClaims();
        uint256 fees = target.accruedFees();

        // Both sums are computed unchecked and their overflow reported rather
        // than reverted. In 0.8 an overflow reverts, and a revert carries no
        // verdict to a campaign running with fail_on_revert = false, so a law
        // that overflowed would fall silent exactly where the numbers went
        // furthest wrong. No honest credit system holds 2^255 of anything, so
        // the overflow is itself the finding.
        uint256 owed;
        uint256 promised;
        unchecked {
            owed = assets + debt;
            promised = claims + fees;
        }
        if (owed < assets) {
            return (false, "assets plus debt overflows");
        }
        if (promised < claims) {
            return (false, "claims plus fees overflows");
        }
        if (owed == promised) {
            return (true, "held plus owed equals claimed plus accrued");
        }
        return (false, "held plus owed differs from claimed plus accrued");
    }
}
