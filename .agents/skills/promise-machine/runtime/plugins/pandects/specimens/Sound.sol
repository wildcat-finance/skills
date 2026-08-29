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

    // -- the withdrawal queue -----------------------------------------------

    function claimCount() external view returns (uint256) {
        return owedAt.length;
    }

    function claimAt(uint256 index)
        external
        view
        returns (uint256 owed, uint256 paid)
    {
        return (owedAt[index], paidAt[index]);
    }

    /// @notice How far down the queue this system says it can settle now.
    /// @dev Derived here from what has actually been set aside, which is what
    /// makes the reference hold `claims/reserves-cover-payable/v1`. It is
    /// `virtual` because the specimen for that law declares payability without
    /// looking at the reserves, and the whole point of the law is that the
    /// declaration can be wrong.
    function payableThrough() external view virtual returns (uint256) {
        return payableCount();
    }

    /// @notice The honest answer, used by `payClaim` whatever the observable says.
    function payableCount() internal view returns (uint256) {
        uint256 covered = reserved;
        uint256 through;
        for (uint256 i = 0; i < owedAt.length; i++) {
            uint256 unpaid = owedAt[i] - paidAt[i];
            if (unpaid > covered) {
                break;
            }
            covered -= unpaid;
            through++;
        }
        return through;
    }

    function unpaidTotal() internal view returns (uint256) {
        uint256 total;
        for (uint256 i = 0; i < owedAt.length; i++) {
            total += owedAt[i] - paidAt[i];
        }
        return total;
    }

    /// @notice What the system earmarks: everything queued, within what it has.
    function earmark() internal view returns (uint256) {
        uint256 outstanding = unpaidTotal();
        uint256 ceiling = claims < held ? claims : held;
        return outstanding < ceiling ? outstanding : ceiling;
    }

    // -- the operations -----------------------------------------------------

    function deposit(uint256 amount) external virtual {
        uint256 value = bounded(amount);
        held += value;
        claims += value;
    }

    function borrow(uint256 amount) external virtual {
        uint256 available = held > reserved ? held - reserved : 0;
        uint256 value = bounded(amount);
        if (value > available) {
            value = available;
        }
        held -= value;
        principal += value;
    }

    function repay(uint256 amount) external virtual {
        uint256 owed = principal + interest;
        uint256 value = bounded(amount);
        if (value > owed) {
            value = owed;
        }
        // Interest first, then principal. Which order a system chooses is a
        // policy question and no law in the corpus has an opinion on it; what
        // matters here is that both reduce debt against assets arriving.
        if (value > interest) {
            principal -= value - interest;
            interest = 0;
        } else {
            interest -= value;
        }
        held += value;
    }

    /// @notice What interest is charged on.
    /// @dev Principal, and never interest already accrued. Virtual because the
    /// specimen for path independence changes exactly this and nothing else.
    function accrualBase() internal view virtual returns (uint256) {
        return principal;
    }

    /// @notice Move the system's clock forward and charge for the time.
    function advance(uint256 elapsed) external virtual {
        uint256 step = elapsed % (MAX_STEP + 1);
        uint256 accrued = (accrualBase() * RATE * step) / RATE_SCALE;
        clock += step;
        interest += accrued;
        claims += accrued;
    }

    /// @notice Take a fee out of what lenders are owed.
    /// @dev The one operation that separates held assets from claims, which is
    /// what lets a state exist where reserving more than is claimed is still
    /// within the assets held.
    ///
    /// The fee is capped at the claims the open batches are not already owed.
    /// Value recorded against a withdrawal has been promised to a lender who
    /// asked for it, and a protocol that takes its fee out of that is taking
    /// money it already owed to somebody leaving.
    ///
    /// The cap measures against the queue rather than against the earmark, and
    /// the difference is the whole of `claims/pooled-claims-cover-open-batches/v1`.
    /// An earmark cannot exceed what is held, so in an illiquid system it sits
    /// below what the batches are owed, and a cap taken against it lets the fee
    /// reach the shortfall. `specimens/FeeFromQueued.sol` is this function with
    /// `unpaidTotal()` swapped back for `reserved`, and it is the only thing
    /// that specimen changes.
    function accrueFee(uint256 amount) external virtual {
        uint256 queued = unpaidTotal();
        uint256 available = claims > queued ? claims - queued : 0;
        uint256 value = bounded(amount);
        if (value > available) {
            value = available;
        }
        claims -= value;
        fees += value;
    }

    /// @notice Record a withdrawal claim and earmark held assets against it.
    /// @dev Bounded by the pooled claim the open batches are not already owed,
    /// and deliberately not by what the system holds. A lender may ask to leave
    /// a system that cannot pay them, which is the state the corpus exists for,
    /// and a reference that refused the request could never reach it. That is
    /// the same bound `WildcatMarketModel.requestWithdrawal` already used.
    ///
    /// Bounding by the pooled claim alone, as this once did, let one pool be
    /// queued twice: two requests each within the pool, together beyond it,
    /// recording more owed than the system owes in total.
    function reserve(uint256 amount) external virtual {
        uint256 ceiling = claims > unpaidTotal() ? claims - unpaidTotal() : 0;
        uint256 value = bounded(amount);
        if (value > ceiling) {
            value = ceiling;
        }
        if (value > 0 && owedAt.length < MAX_CLAIMS) {
            owedAt.push(value);
            paidAt.push(0);
        }
        reserved = earmark();
    }

    /// @notice Hand assets to the oldest claim the system can settle.
    /// @dev Virtual because the specimen for queue order pays a different one.
    function payClaim(uint256 amount) external virtual {
        uint256 through = payableCount();
        for (uint256 i = 0; i < through; i++) {
            uint256 unpaid = owedAt[i] - paidAt[i];
            if (unpaid == 0) {
                continue;
            }
            settle(i, amount, unpaid);
            return;
        }
    }

    /// @notice Pay one claim, within everything that bounds it.
    function settle(uint256 index, uint256 amount, uint256 unpaid) internal {
        uint256 value = bounded(amount);
        if (value > unpaid) {
            value = unpaid;
        }
        if (value > reserved) {
            value = reserved;
        }
        if (value > held) {
            value = held;
        }
        if (value > claims) {
            value = claims;
        }
        paidAt[index] += value;
        held -= value;
        claims -= value;
        reserved -= value;
    }
}
