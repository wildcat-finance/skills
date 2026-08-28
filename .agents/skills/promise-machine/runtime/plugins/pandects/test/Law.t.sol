// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../src/ICreditObservables.sol";
import {Law} from "../src/Law.sol";

/// A target whose numbers are whatever the test sets them to.
contract Observable is ICreditObservables {
    address public asset;
    uint256 public totalAssets;
    uint256 public totalDebt;
    uint256 public totalLenderClaims;
    uint256 public reservedAssets;
    uint256 public borrowableAssets;
    uint256 public accruedFees;
    uint256 public observedAt;

    function set(uint256 held, uint256 claims) external {
        totalAssets = held;
        totalLenderClaims = claims;
    }
}

/// A target that will not answer. Not a law failing: a state nobody can see.
contract Unobservable is ICreditObservables {
    function asset() external pure returns (address) {
        revert("no");
    }

    function totalAssets() external pure returns (uint256) {
        revert("no");
    }

    function totalDebt() external pure returns (uint256) {
        revert("no");
    }

    function totalLenderClaims() external pure returns (uint256) {
        revert("no");
    }

    function reservedAssets() external pure returns (uint256) {
        revert("no");
    }

    function borrowableAssets() external pure returns (uint256) {
        revert("no");
    }

    function accruedFees() external pure returns (uint256) {
        revert("no");
    }

    function observedAt() external pure returns (uint256) {
        revert("no");
    }
}

/// Not a shipped law. The shape a law has, exercised here so the base is
/// tested before any law depends on it.
contract SampleLaw is Law {
    function id() external pure override returns (string memory) {
        return "sample/held-covers-claims/v1";
    }

    function statement() external pure override returns (string memory) {
        return "Assets held cover the claims recorded against them.";
    }

    function check(ICreditObservables target)
        external
        view
        override
        returns (bool held, string memory detail)
    {
        uint256 assets = target.totalAssets();
        uint256 claims = target.totalLenderClaims();
        if (assets >= claims) {
            return (true, "assets cover claims");
        }
        return (false, "assets below claims");
    }
}

contract LawTest {
    SampleLaw internal law;
    Observable internal target;

    function setUp() public {
        law = new SampleLaw();
        target = new Observable();
    }

    function test_a_law_holding_returns_true_with_its_detail() external {
        SampleLaw sample = new SampleLaw();
        Observable observable = new Observable();
        observable.set(100, 90);
        (bool held, string memory detail) = sample.check(observable);
        require(held, "law should hold");
        require(bytes(detail).length > 0, "a verdict without a detail");
    }

    /// The decision the base exists to enforce: violated is a return value,
    /// never a revert, because a revert carries no verdict to the harness.
    function test_a_law_violated_returns_false_rather_than_reverting() external {
        SampleLaw sample = new SampleLaw();
        Observable observable = new Observable();
        observable.set(90, 100);
        (bool held, string memory detail) = sample.check(observable);
        require(!held, "law should be violated");
        require(bytes(detail).length > 0, "a verdict without a detail");
    }

    /// The stated limit: an unobservable target takes the law down with it,
    /// and that is a revert rather than a pass.
    function test_an_unobservable_target_reverts_rather_than_passing() external {
        SampleLaw sample = new SampleLaw();
        Unobservable unobservable = new Unobservable();
        (bool ok, ) = address(sample).staticcall(
            abi.encodeWithSelector(sample.check.selector, address(unobservable))
        );
        require(!ok, "reading an unobservable target should not succeed");
    }

    function test_a_law_carries_its_identifier_and_statement() external {
        SampleLaw sample = new SampleLaw();
        require(bytes(sample.id()).length > 0, "no id");
        require(bytes(sample.statement()).length > 0, "no statement");
    }
}
