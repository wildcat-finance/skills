// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `accrual/path-independent/v1`, and by nothing else.
///
/// The defect is one line: interest is charged on principal plus the interest
/// already accrued, so each step charges for the last one. Every rule about
/// direction still holds -- debt rises only with time, falls only against
/// payment -- and a single observation of this system is indistinguishable from
/// a correct one.
///
/// What it costs a borrower depends on how often somebody pokes the contract.
/// Two borrowers on identical terms owe different amounts because one of them
/// happened to be in a busier market, and neither can read that off the terms
/// they agreed to.
contract CompoundsPerStep is Sound {
    function accrualBase() internal view override returns (uint256) {
        return principal + interest;
    }
}
