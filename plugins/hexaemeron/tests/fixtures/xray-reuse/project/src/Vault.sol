// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Base} from "./Base.sol";

contract Vault is Base {
    function deposit(uint256 amount) external {
        total += amount;
    }
}
