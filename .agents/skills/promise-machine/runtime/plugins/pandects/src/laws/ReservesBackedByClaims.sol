// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../ICreditObservables.sol";
import {Law} from "../Law.sol";

/// @title Nothing is reserved that nobody has claimed.
/// @notice Assets earmarked against withdrawal claims never exceed the claims
/// recorded. Reserving more than is owed is not a conservative error: it takes
/// liquidity away from the borrower, which is the thing the borrower is paying
/// for, and it does so without anyone having asked.
///
/// Independent of the other two conservation laws by construction. A state can
/// break this while conserving value and while keeping its held assets within
/// their partition, which is what the diagonal in `test/Corpus.t.sol` asserts.
///
/// Exact, with no tolerance. This is a comparison and nothing else.
contract ReservesBackedByClaims is Law {
    function id() external pure override returns (string memory) {
        return "conservation/reserves-backed-by-claims/v1";
    }

    function statement() external pure override returns (string memory) {
        return "Assets reserved never exceed the lender claims recorded.";
    }

    function check(ICreditObservables target)
        external
        view
        override
        returns (bool held, string memory detail)
    {
        uint256 reserved = target.reservedAssets();
        uint256 claims = target.totalLenderClaims();
        if (reserved <= claims) {
            return (true, "reserved is within recorded claims");
        }
        return (false, "reserved exceeds recorded claims");
    }
}
