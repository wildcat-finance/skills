// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Sound} from "./Sound.sol";

/// @title A deliberately broken credit system. Do not deploy this.
/// @notice Caught by `conservation/value-conserved/v1`, and by nothing else.
///
/// The defect is one line: a deposit credits the lender twice while the system
/// receives once. Value appears on the right-hand side that never arrived on
/// the left, which is the shape of every accounting bug that pays the first
/// lender out with the second lender's money.
contract MintedClaims is Sound {
    function deposit(uint256 amount) external override {
        uint256 value = bounded(amount);
        held += value;
        claims += value * 2;
    }
}
