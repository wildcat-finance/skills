// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../../src/ICreditObservables.sol";
import {IWithdrawalQueueObservables} from "../../src/IWithdrawalQueueObservables.sol";

/// @title A reduced model of a Wildcat market.
/// @notice Reduced, not faithful. This is a model written to be read, not a
/// reimplementation, and nothing here should be mistaken for the market
/// contracts. What it keeps is the shape the corpus has to survive: withdrawals
/// pooled into batches rather than queued as individual claims, a reserve the
/// borrower may not touch, delinquency, and a penalty rate that runs on top of
/// the base one while a market is delinquent.
///
/// Four things about that shape matter to the laws.
///
/// **Withdrawals are batched.** A request joins the batch open in the current
/// cycle. A batch is paid pro rata, so within one batch no lender is ahead of
/// another; batches are paid oldest first. That is why the queue extension here
/// exposes batches rather than lenders, and why the applicability note for
/// `claims/queue-order-preserved/v1` says which unit it means. Read as a
/// per-lender promise the law is false of this design. Read as a per-batch one
/// it is exactly what the design guarantees.
///
/// **Liquidity is not all borrowable.** The borrower may take held assets less
/// what is reserved against unpaid batches and less the required reserve on
/// outstanding claims. A market that cannot cover both is delinquent.
///
/// **Base interest is linear on principal.** It accrues on what was borrowed
/// and never on interest already accrued, so a span costs the same however it
/// is cut up.
///
/// **Penalty interest is not.** It runs only while the market has been
/// delinquent longer than the grace period, and the grace timer advances when
/// the market is poked. A market that crosses into delinquency mid-span accrues
/// a different penalty depending on how often somebody updated it, which is
/// path dependence in the plain sense. `accrual/path-independent/v1` therefore
/// holds here while the market is solvent and does not hold once penalty
/// accrual is running -- a condition rather than a yes or a no, and the reason
/// the applicability contract has a shape at all.
contract WildcatMarketModel is ICreditObservables, IWithdrawalQueueObservables {
    uint256 internal constant CEILING = 1e30;

    /// @dev A tenth per 365 days, and the same again as penalty. Both are rates
    /// on a duration rather than charges on a call.
    uint256 internal constant BASE_RATE = 3_170_979_198;
    uint256 internal constant PENALTY_RATE = 3_170_979_198;
    uint256 internal constant RATE_SCALE = 1e18;

    /// @dev What fraction of outstanding claims the borrower must leave behind,
    /// in hundredths. Twenty per cent, which is a plausible figure and not a
    /// claim about any real market.
    uint256 internal constant RESERVE_RATIO = 20;

    /// @dev How long a market may be delinquent before the penalty starts.
    uint256 internal constant GRACE = 7 days;

    /// @dev Bounded so a fuzzer spends its calls on sequences rather than on
    /// overflow reverts, which carry no verdict.
    uint256 internal constant MAX_STEP = 365 days;
    uint256 internal constant MAX_BATCHES = 8;

    address public constant asset =
        address(uint160(uint256(keccak256("pandects.wildcat.model.asset"))));

    uint256 internal clock;
    uint256 internal held;
    uint256 internal principal;
    uint256 internal interest;
    uint256 internal claims;
    uint256 internal fees;

    /// @dev How long this market has been short of its required liquidity.
    uint256 internal delinquentFor;

    uint256[] internal batchOwed;
    uint256[] internal batchPaid;

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

    /// @notice Assets set aside against batches that have not been paid.
    function reservedAssets() external view returns (uint256) {
        return reserved();
    }

    /// @notice What the borrower may actually take.
    /// @dev Held assets, less what is reserved against unpaid batches, less the
    /// reserve the borrower must leave on outstanding claims. This is the
    /// quantity a borrower cares about and the one a naive model gets wrong by
    /// reporting everything not already spoken for.
    function borrowableAssets() external view returns (uint256) {
        uint256 spoken = reserved() + requiredReserve();
        return held > spoken ? held - spoken : 0;
    }

    function observedAt() external view returns (uint256) {
        return clock;
    }

    // -- the withdrawal batches ----------------------------------------------

    /// @notice How many batches this market has opened.
    /// @dev Batches, not lenders. A batch pools every request made in its cycle
    /// and is paid pro rata, so there is no ordering inside one to report.
    function claimCount() external view returns (uint256) {
        return batchOwed.length;
    }

    function claimAt(uint256 index)
        external
        view
        returns (uint256 owed, uint256 paid)
    {
        return (batchOwed[index], batchPaid[index]);
    }

    /// @notice How far down the batches this market can settle now.
    function payableThrough() external view returns (uint256) {
        return payableCount();
    }

    /// @dev The same answer, reachable from inside. `payBatch` uses this rather
    /// than the observable so that a market which ever declared payability
    /// differently would still pay in the order it actually can -- the
    /// declaration is what a law checks, and code that read its own declaration
    /// could never disagree with it.
    function payableCount() internal view returns (uint256) {
        uint256 covered = reserved();
        uint256 through;
        for (uint256 i = 0; i < batchOwed.length; i++) {
            uint256 unpaid = batchOwed[i] - batchPaid[i];
            if (unpaid > covered) {
                break;
            }
            covered -= unpaid;
            through++;
        }
        return through;
    }

    // -- what the market owes itself -----------------------------------------

    function unpaidBatches() internal view returns (uint256) {
        uint256 total;
        for (uint256 i = 0; i < batchOwed.length; i++) {
            total += batchOwed[i] - batchPaid[i];
        }
        return total;
    }

    function reserved() internal view returns (uint256) {
        uint256 outstanding = unpaidBatches();
        uint256 ceiling = claims < held ? claims : held;
        return outstanding < ceiling ? outstanding : ceiling;
    }

    /// @notice The reserve the borrower must leave on claims not yet requested.
    function requiredReserve() internal view returns (uint256) {
        uint256 unrequested = claims > unpaidBatches() ? claims - unpaidBatches() : 0;
        return (unrequested * RESERVE_RATIO) / 100;
    }

    /// @notice Whether the market is short of the liquidity it owes.
    /// @dev Against what is owed on unpaid batches, not against what has been
    /// set aside. Those differ exactly when the market is in trouble: `reserved`
    /// cannot exceed what is held, because a market cannot earmark assets it
    /// does not have, so comparing held against it would make delinquency
    /// almost unreachable and the penalty rate decorative.
    function delinquent() public view returns (bool) {
        return held < unpaidBatches() + requiredReserve();
    }

    /// @notice Whether the penalty rate is running.
    function penalised() public view returns (bool) {
        return delinquentFor > GRACE;
    }

    // -- the operations -------------------------------------------------------

    function deposit(uint256 amount) external {
        uint256 value = bounded(amount);
        held += value;
        claims += value;
    }

    function borrow(uint256 amount) external {
        uint256 spoken = reserved() + requiredReserve();
        uint256 available = held > spoken ? held - spoken : 0;
        uint256 value = bounded(amount);
        if (value > available) {
            value = available;
        }
        held -= value;
        principal += value;
    }

    function repay(uint256 amount) external {
        uint256 owed = principal + interest;
        uint256 value = bounded(amount);
        if (value > owed) {
            value = owed;
        }
        if (value > interest) {
            principal -= value - interest;
            interest = 0;
        } else {
            interest -= value;
        }
        held += value;
    }

    /// @notice Move the clock and charge for the time.
    /// @dev Two rates, and only one of them is path independent. The base rate
    /// runs on principal for the whole step. The penalty runs only for the part
    /// of the step after the grace period had already been exhausted, and
    /// whether that is any of it depends on when this was last called.
    function advance(uint256 elapsed) external {
        uint256 step = elapsed % (MAX_STEP + 1);
        uint256 accrued = (principal * BASE_RATE * step) / RATE_SCALE;

        if (penalised()) {
            accrued += (principal * PENALTY_RATE * step) / RATE_SCALE;
        }

        clock += step;
        interest += accrued;
        claims += accrued;

        // Recomputed after the accrual, because accruing raises claims and can
        // itself tip a market into delinquency.
        if (delinquent()) {
            delinquentFor += step;
        } else {
            delinquentFor = 0;
        }
    }

    /// @notice Take a protocol fee out of what lenders are owed.
    /// @dev Capped against what the open batches are owed, not against what has
    /// been set aside. Those two differ exactly when the market is in trouble,
    /// as `delinquent` says, and a cap taken against the earmark lets the fee
    /// reach value already promised to lenders waiting in a batch. On a market
    /// holding 200 against a batch owed 1000, the earmark cap permitted a fee of
    /// 800; this one permits nothing, because nothing is unrequested.
    function accrueFee(uint256 amount) external {
        uint256 spoken = unpaidBatches();
        uint256 available = claims > spoken ? claims - spoken : 0;
        uint256 value = bounded(amount);
        if (value > available) {
            value = available;
        }
        claims -= value;
        fees += value;
    }

    /// @notice Request a withdrawal, joining the batch open in this cycle.
    /// @dev Bounded by claims not already requested, and deliberately not by
    /// what the market holds. A lender may ask to leave a market that cannot
    /// pay them; that is the situation the whole design is built around, and a
    /// model that refused the request would have no way to reach it.
    function requestWithdrawal(uint256 amount) external {
        uint256 requested = unpaidBatches();
        uint256 ceiling = claims > requested ? claims - requested : 0;
        uint256 value = bounded(amount);
        if (value > ceiling) {
            value = ceiling;
        }
        if (value == 0) {
            return;
        }
        if (batchOwed.length == 0 || batchPaid[batchOwed.length - 1] > 0) {
            if (batchOwed.length >= MAX_BATCHES) {
                return;
            }
            batchOwed.push(value);
            batchPaid.push(0);
            return;
        }
        // The open batch is the newest one nobody has been paid from yet.
        // Joining it is what makes this a batch rather than a queue.
        batchOwed[batchOwed.length - 1] += value;
    }

    /// @notice Pay the oldest batch the market can settle.
    /// @dev Pro rata within the batch is not modelled per lender, because the
    /// laws read amounts rather than lenders. What matters here is that a
    /// partial payment lands on the oldest unpaid batch and never on a newer
    /// one, which is the promise `claims/queue-order-preserved/v1` checks.
    function payBatch(uint256 amount) external {
        uint256 through = payableCount();
        for (uint256 i = 0; i < through; i++) {
            uint256 unpaid = batchOwed[i] - batchPaid[i];
            if (unpaid == 0) {
                continue;
            }
            uint256 value = bounded(amount);
            if (value > unpaid) {
                value = unpaid;
            }
            if (value > held) {
                value = held;
            }
            if (value > claims) {
                value = claims;
            }
            batchPaid[i] += value;
            held -= value;
            claims -= value;
            return;
        }
    }
}
