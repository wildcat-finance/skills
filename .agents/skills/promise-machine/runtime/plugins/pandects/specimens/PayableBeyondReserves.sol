// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `claims/reserves-cover-payable/v1`, and by nothing else.
///
/// The defect is one line: the system declares every recorded claim payable,
/// whatever it has actually set aside. It still pays in order, still pays only
/// what it holds, and every other law in the corpus is satisfied at every
/// moment -- because the defect is not in what it does, it is in what it says.
///
/// A lender reading the declaration stops looking for liquidity elsewhere. The
/// system has moved the risk of not getting out onto them without telling them,
/// and the only observable that carries the lie is the declaration itself.
/// This is why `payableThrough` is declared rather than derived: a figure
/// computed from the reserves could not be wrong, and could not be checked.
contract PayableBeyondReserves is Sound {
    function payableThrough() external view override returns (uint256) {
        return owedAt.length;
    }
}
