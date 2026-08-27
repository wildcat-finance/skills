// SPDX-License-Identifier: MIT
// A fixture market contract for the Horos Solidity outliner.
pragma solidity ^0.8.20;

import { IERC20 } from "./interfaces/IERC20.sol";
import "./libraries/MathUtils.sol";

type Duration is uint32;

using MathUtils for uint256;

error MarketClosed(address market);

struct LenderStatus {
    bool isBlockedFromDeposits;
    uint256 scaledBalance;
}

enum MarketState {
    Open,
    Delinquent,
    Closed
}

uint256 constant BIP = 1e4;

interface IMarketEvents {
    event Borrow(uint256 assetAmount);
    event DebtRepaid(address indexed from, uint256 assetAmount);
}

abstract contract MarketBase is IMarketEvents {
    IERC20 public immutable asset;
    uint256 public totalSupply = 0;
    mapping(address => LenderStatus) internal _lenders;

    modifier onlyOpen() {
        if (state() == MarketState.Closed) revert MarketClosed(address(this));
        _;
    }

    constructor(IERC20 _asset) {
        asset = _asset;
    }

    function state() public view virtual returns (MarketState);

    receive() external payable {}

    function borrow(
        uint256 assetAmount
    ) external onlyOpen returns (uint256 normalized) {
        string memory tag = "function fake() public { // not a declaration";
        normalized = assetAmount.bipMul(BIP);
        unchecked {
            totalSupply += normalized;
        }
        emit Borrow(assetAmount);
        assembly {
            mstore(0x00, normalized)
        }
        return normalized;
    }
}

library MarketMath {
    function rayDiv(uint256 x, uint256 y) internal pure returns (uint256) {
        return (x * 1e27) / y;
    }
}

contract Market is MarketBase {
    constructor(IERC20 _asset) MarketBase(_asset) {}

    function state() public pure override returns (MarketState) {
        return MarketState.Open;
    }
}
