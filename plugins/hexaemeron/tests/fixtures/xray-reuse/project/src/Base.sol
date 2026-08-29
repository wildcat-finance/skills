// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Base {
    uint256 internal total;

    function setTotal(uint256 next) public virtual {
        total = next;
    }
}
