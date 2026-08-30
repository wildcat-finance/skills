// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../src/ICreditObservables.sol";
import {IWithdrawalQueueObservables} from "../src/IWithdrawalQueueObservables.sol";

/// @title A small credit system that holds every law in the corpus.
/// @notice Not a specimen. This is the reference the broken ones inherit from,
/// so that each of those differs by exactly one function and the defect is the
/// diff rather than a paragraph claiming there is one.
///
/// The model is the smallest thing that can be got wrong in the ways credit is
/// got wrong: deposits create claims, borrowing moves held assets into debt,
/// time turns principal into interest, repayment moves assets back, a fee moves
/// value from lenders to the protocol, and a withdrawal request records a claim
/// and earmarks assets against it.
///
/// Every operation preserves conservation by construction:
///
/// - `deposit` adds to held assets and to claims, one on each side.
/// - `borrow` and `repay` move between held assets and debt, both on the left.
/// - `advance` adds interest to debt and to claims, one on each side.
/// - `accrueFee` moves between claims and fees, both on the right.
/// - `reserve` records a claim and marks held assets; it moves nothing.
/// - `payClaim` hands assets to a departing lender and retires their claim.
///
/// Two things about time. The clock is the system's own rather than the
/// block's, because `observedAt` exists so a law can be checked against a
/// recorded state as well as a live one, and a reference that read
/// `block.timestamp` could never be advanced deliberately. And interest accrues
/// on principal alone, never on interest already accrued, which is what makes
/// the same span cost the same however it is cut up. A reference that
/// compounded would fail `accrual/path-independent/v1`, and the specimen that
/// does compound differs from this file by one line.
///
/// Amounts are bounded so a fuzzer spends its calls on sequences rather than on
/// overflow reverts, which carry no verdict.
contract Sound is ICreditObservables, IWithdrawalQueueObservables {
    uint256 internal constant CEILING = 1e30;

    /// @dev Scaled by `RATE_SCALE` and applied per second, so a span costs the
    /// same whether it is charged once or in pieces. What matters is that it is
    /// a rate on a duration rather than a charge on a call. The figure is a
    /// tenth per 365 days, chosen to be recognisable and small enough that the
    /// specimen which compounds can run a fuzzer's worth of years without
    /// reaching an overflow, since an overflow reverts and a revert carries no
    /// verdict.
    uint256 internal constant RATE = 3_170_979_198;
    uint256 internal constant RATE_SCALE = 1e18;

    /// @dev A single advance is capped so that a fuzzer cannot reach a span
    /// where the accrual arithmetic overflows, which would revert and carry no
    /// verdict.
    uint256 internal constant MAX_STEP = 365 days;

    /// @dev The queue is bounded because every observation of it is copied into
    /// memory and, in the campaign harness, into storage. That is a harness
    /// cost rather than an economic claim: no credit system has eight
    /// withdrawals in it and no more.
    uint256 internal constant MAX_CLAIMS = 8;

    /// @dev A placeholder. These specimens model units of one asset rather
    /// than a token, and reporting a zero address would be an observable
    /// saying the quantities are denominated in nothing.
    address public constant asset = address(uint160(uint256(keccak256("pandects.specimen.asset"))));

    uint256 internal clock;
    uint256 internal held;
    uint256 internal principal;
    uint256 internal interest;
    uint256 internal claims;
    uint256 internal fees;
    uint256 internal reserved;

    uint256[] internal owedAt;
    uint256[] internal paidAt;

    function bounded(uint256 amount) internal pure returns (uint256) {
        return amount % CEILING;
    }

    // -- the core observables -----------------------------------------------

    function totalAssets() external view returns (uint256) {
        return held;
    }

    function totalDebt() external view returns (uint256) {
        return principal + interest;
    }

    function totalLenderClaims() external view returns (uint256) {
        return claims;
    }

    function accruedFees() external view returns (uint256) {
        return fees;
    }

    function reservedAssets() external view returns (uint256) {
        return reserved;
    }

    /// @notice What a borrower may take: held assets that are not spoken for.
    /// @dev Virtual because a specimen breaks the partition by recording this
    /// rather than deriving it, which is the defect worth having a specimen for.
    function borrowableAssets() external view virtual returns (uint256) {
        return held > reserved ? held - reserved : 0;
    }

    function observedAt() external view returns (uint256) {
        return clock;
    }
