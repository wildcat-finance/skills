// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Vault} from "./Vault.sol";

contract Router {
    Vault public immutable vault;

    constructor(Vault target) {
        vault = target;
    }

    function route(uint256 amount) external {
        vault.deposit(amount);
    }
}
