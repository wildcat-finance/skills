// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {CorpusObserver} from "../adapters/CorpusBase.sol";
import {PathIndependenceProbe} from "../adapters/foundry/PathIndependenceProbe.sol";
import {ICreditObservables} from "../src/ICreditObservables.sol";
import {Law} from "../src/Law.sol";
import {Observation, Observe} from "../src/Observation.sol";
import {PairLaw} from "../src/PairLaw.sol";
import {ValueConserved} from "../src/laws/ValueConserved.sol";
import {ReservesBackedByClaims} from "../src/laws/ReservesBackedByClaims.sol";
import {HeldAssetsPartitioned} from "../src/laws/HeldAssetsPartitioned.sol";
import {QueueOrderPreserved} from "../src/laws/QueueOrderPreserved.sol";
import {ReservesCoverPayableClaims} from "../src/laws/ReservesCoverPayableClaims.sol";
import {PooledClaimsCoverOpenBatches} from "../src/laws/PooledClaimsCoverOpenBatches.sol";
import {DebtFallsOnlyAgainstPayment} from "../src/laws/DebtFallsOnlyAgainstPayment.sol";
import {NoAccrualAtRest} from "../src/laws/NoAccrualAtRest.sol";
import {RecordedClaimNeverShrinks} from "../src/laws/RecordedClaimNeverShrinks.sol";
import {WildcatMarketModel} from "../integrations/wildcat/WildcatMarketModel.sol";
import {WildcatMarketCampaign} from "../src/campaigns/Wildcat.sol";

/// @title The corpus against a design it was not written for.
/// @notice Every law so far has been proven against a specimen built to break
/// it. That proves a law is a law. It does not touch the claim the corpus
/// actually makes, which is that the same economic facts hold across codebases
/// sharing nothing else.
///
/// This is the first codebase. What is being tested is not that the laws hold
/// -- though they do -- but that the applicability contract says the right
/// things about a design nobody wrote them for. Two cases carry that:
/// `queue-order-preserved` is true here at a unit the corpus does not name, and
/// `path-independent` is true here only under a condition.
contract WildcatTest {
    event log_named_uint(string key, uint256 val);

    Law internal conserved;
    Law internal backed;
    Law internal partitioned;
    Law internal ordered;
    Law internal covered;
    Law internal pooled;
    PairLaw internal falls;
    PairLaw internal atRest;
    PairLaw internal shrinks;

    uint256 internal constant WHOLE_SPAN = 365 days;
    uint256 internal constant HALF_SPAN = 182.5 days;

    function setUp() public {
        conserved = new ValueConserved();
        backed = new ReservesBackedByClaims();
        partitioned = new HeldAssetsPartitioned();
        ordered = new QueueOrderPreserved();
        covered = new ReservesCoverPayableClaims();
        pooled = new PooledClaimsCoverOpenBatches();
        falls = new DebtFallsOnlyAgainstPayment();
        atRest = new NoAccrualAtRest();
        shrinks = new RecordedClaimNeverShrinks();
    }

    /// A market with lenders in, a borrower out, time passed and a batch open.
    function market() internal returns (WildcatMarketModel model) {
        model = new WildcatMarketModel();
        model.deposit(100_000);
        model.borrow(50_000);
        model.advance(WHOLE_SPAN);
        model.requestWithdrawal(10_000);
        model.payBatch(4_000);
        model.repay(1_000);
    }

    function holds(Law law, ICreditObservables on) internal view returns (bool ok) {
        (ok, ) = law.check(on);
    }

    // -- the laws the model claims -------------------------------------------

    /// @notice Law by law, rather than in aggregate.
    /// @dev An aggregate assertion passes when four laws hold and one is never
    /// reached. Each of these is its own line so a failure names the law.
    function test_the_model_holds_every_one_state_law_it_claims() external {
        WildcatMarketModel model = market();
        require(holds(conserved, model), "the model stopped conserving value");
        require(holds(backed, model), "the model reserved beyond its claims");
        require(holds(partitioned, model), "the model promised the same asset twice");
        require(holds(ordered, model), "the model paid a batch out of turn");
        require(holds(covered, model), "the model declared more payable than it holds");
        require(holds(pooled, model), "the model owed its batches more than its pool");
    }

    /// @notice The succession laws, across every operation the design has.
    function test_no_transition_of_the_model_breaks_a_succession_law() external {
        WildcatMarketModel model = new WildcatMarketModel();
        Observation memory earlier = Observe.takeWithQueue(model);
        Observation memory later;

        model.deposit(100_000);
        later = Observe.takeWithQueue(model);
        assertSuccession(earlier, later);

        earlier = later;
        model.borrow(50_000);
        later = Observe.takeWithQueue(model);
        assertSuccession(earlier, later);

        earlier = later;
        model.advance(WHOLE_SPAN);
        later = Observe.takeWithQueue(model);
        assertSuccession(earlier, later);

        earlier = later;
        model.requestWithdrawal(10_000);
        later = Observe.takeWithQueue(model);
        assertSuccession(earlier, later);

        earlier = later;
        model.payBatch(4_000);
        later = Observe.takeWithQueue(model);
        assertSuccession(earlier, later);

        earlier = later;
        model.repay(1_000);
        later = Observe.takeWithQueue(model);
        assertSuccession(earlier, later);

        earlier = later;
        model.accrueFee(500);
        later = Observe.takeWithQueue(model);
        assertSuccession(earlier, later);
    }

    function assertSuccession(Observation memory earlier, Observation memory later)
        internal
        view
    {
        (bool a, ) = falls.check(earlier, later);
        (bool b, ) = atRest.check(earlier, later);
        (bool c, ) = shrinks.check(earlier, later);
        require(a, "debt fell further than assets rose");
        require(b, "debt rose while the clock stood still");
        require(c, "a recorded batch was written down");
    }

    // -- the unit the corpus does not name ------------------------------------

    /// @notice Order between batches, and no order at all inside one.
    /// @dev The finding this integration exists for. Two lenders requesting in
    /// the same cycle join one batch, and a payment against that batch settles
    /// part of both. Read as a per-lender promise the law would be false here:
    /// neither lender is ahead of the other and neither is paid in full. Read
    /// as a per-batch promise it is exactly what the design guarantees, and
    /// that is what holds.
    function test_a_batch_paid_pro_rata_does_not_break_the_ordering() external {
        WildcatMarketModel model = new WildcatMarketModel();
        model.deposit(100_000);
        model.requestWithdrawal(10_000);
        model.requestWithdrawal(10_000);

        require(model.claimCount() == 1, "two requests in one cycle made two batches");
        (uint256 owed, uint256 paid) = model.claimAt(0);
        require(owed == 20_000 && paid == 0, "the batch did not pool both requests");

        model.payBatch(5_000);
        (, paid) = model.claimAt(0);
        require(paid == 5_000, "the batch was not paid into");
        require(holds(ordered, model), "a partly paid batch was read as a jump");
    }

    /// @notice And a newer batch waits for an older one.
    function test_an_older_batch_is_settled_first() external {
        WildcatMarketModel model = new WildcatMarketModel();
        model.deposit(100_000);
        model.requestWithdrawal(10_000);
        model.payBatch(1_000);
        model.requestWithdrawal(10_000);

        require(model.claimCount() == 2, "a paid batch stayed open for new requests");
        model.payBatch(500);

        (, uint256 firstPaid) = model.claimAt(0);
        (, uint256 secondPaid) = model.claimAt(1);
        require(firstPaid == 1_500, "the older batch was not the one paid");
        require(secondPaid == 0, "the newer batch was paid ahead of the older one");
        require(holds(ordered, model), "the law disagreed with the payment order");
    }

    /// @notice A law the corpus has that this design does not satisfy.
    /// @dev Found by Echidna against the shipped adapter, not by reading. The
    /// law says a recorded claim keeps its owed amount. A Wildcat batch
    /// accumulates while it is open: a second request in the same cycle joins
    /// the batch and the amount owed on it rises.
    ///
    /// Neither side is wrong. For a queue of individual claims, an amount that
    /// changes after the fact is the defect the law was written for. For a
    /// batched design, an open batch is not yet a claim that has been recorded
    /// -- it is a claim still being assembled -- and the law starts applying
    /// when the batch closes.
    ///
    /// Asserted rather than described, because a limitation nobody has watched
    /// happen is a limitation people assume was handled.
    function test_an_open_batch_grows_and_the_claim_law_refuses_it() external {
        WildcatMarketModel model = new WildcatMarketModel();
        model.deposit(100_000);
        model.requestWithdrawal(10_000);

        Observation memory earlier = Observe.takeWithQueue(model);
        model.requestWithdrawal(5_000);
        Observation memory later = Observe.takeWithQueue(model);

        require(earlier.queue[0].owed == 10_000, "the batch did not open at 10000");
        require(later.queue[0].owed == 15_000, "the second request did not join it");

        (bool held, string memory why) = shrinks.check(earlier, later);
        require(!held, "the law accepted an owed amount that changed");
        require(
            keccak256(bytes(why))
                == keccak256("a recorded claim's owed amount changed"),
            "the law refused it for some other reason"
        );
    }

    /// @notice And once a batch is closed, the law holds over it.
    /// @dev Which is what makes this a condition rather than a rejection. A
    /// batch stops accepting requests as soon as anything is paid out of it,
    /// and from that moment its owed amount is fixed.
    function test_a_closed_batch_satisfies_the_claim_law() external {
        WildcatMarketModel model = new WildcatMarketModel();
        model.deposit(100_000);
        model.requestWithdrawal(10_000);
        model.payBatch(1_000);

        Observation memory earlier = Observe.takeWithQueue(model);
        model.requestWithdrawal(5_000);
        model.payBatch(1_000);
        Observation memory later = Observe.takeWithQueue(model);

        require(later.queue.length == 2, "the closed batch took another request");
        require(later.queue[0].owed == 10_000, "a closed batch changed amount");

        (bool held, ) = shrinks.check(earlier, later);
        require(held, "the law refused a design that keeps closed batches fixed");
    }

    // -- the law that holds under a condition ----------------------------------

    /// @notice Path independence, while the market is solvent.
    /// @dev Base interest is linear on principal, so the span costs the same
    /// however it is cut up, to within the bound the law derives.
    function test_a_solvent_market_is_path_independent() external {
        PathIndependenceProbe probe = new PathIndependenceProbe(2);

        WildcatMarketModel coarse = solvent();
        WildcatMarketModel fine = solvent();
        coarse.advance(WHOLE_SPAN);
        fine.advance(HALF_SPAN);
        fine.advance(HALF_SPAN);

        require(!coarse.penalised() && !fine.penalised(), "the markets went delinquent");
        (bool held, ) = probe.check(coarse, fine);
        require(held, "a solvent market was reported as path dependent");
    }

    /// @notice And not, once the penalty is running.
    /// @dev The condition, watched rather than described. The grace timer moves
    /// when the market is poked, so a market crossing into delinquency mid-span
    /// owes a different penalty depending on how often somebody updated it.
    /// This is not a defect in the design and not a defect in the law: it is a
    /// design the law does not describe once that rate is on, and the
    /// applicability note is where that is written down.
    function test_a_penalised_market_is_not_path_independent() external {
        PathIndependenceProbe probe = new PathIndependenceProbe(2);

        WildcatMarketModel coarse = delinquent();
        WildcatMarketModel fine = delinquent();
        coarse.advance(WHOLE_SPAN);
        fine.advance(HALF_SPAN);
        fine.advance(HALF_SPAN);

        require(fine.penalised(), "the subdivided market never reached the penalty");
        (bool held, ) = probe.check(coarse, fine);
        require(!held, "the two runs agreed, so the condition is not real");
    }

    /// A market with plenty of liquidity behind its obligations.
    function solvent() internal returns (WildcatMarketModel model) {
        model = new WildcatMarketModel();
        model.deposit(100_000);
        model.borrow(10_000);
    }

    /// A market short of the liquidity it owes, with its grace period intact.
    /// @dev The grace has to be unspent, because that is where the path
    /// dependence lives. A market already past it charges the penalty for every
    /// step whatever the subdivision, and the two runs would agree.
    function delinquent() internal returns (WildcatMarketModel model) {
        model = new WildcatMarketModel();
        model.deposit(100_000);
        model.borrow(100_000);
        model.requestWithdrawal(100_000);
        require(model.delinquent(), "the market did not go delinquent");
        require(!model.penalised(), "the grace period was already spent");
    }

    // -- through the adapters, not a harness written for it ---------------------

    function test_the_model_runs_through_the_shipped_adapter() external {
        WildcatMarketCampaign campaign = new WildcatMarketCampaign();
        require(campaign.echidna_value_conserved(), "conservation failed at rest");

        campaign.deposit(100_000);
        campaign.borrow(50_000);
        campaign.advance(WHOLE_SPAN);
        campaign.requestWithdrawal(10_000);
        campaign.payBatch(4_000);

        require(campaign.successionExercised(), "the adapter recorded nothing");
        require(campaign.echidna_value_conserved(), "conservation failed");
        require(campaign.echidna_reserves_backed(), "reserve backing failed");
        require(campaign.echidna_held_partitioned(), "the partition failed");
        require(campaign.echidna_queue_order_preserved(), "the ordering failed");
        require(campaign.echidna_reserves_cover_payable(), "the cover failed");
        require(campaign.echidna_debt_falls_only_against_payment(), "the payment law failed");
        require(campaign.echidna_no_accrual_at_rest(), "the rest law failed");
        require(campaign.echidna_recorded_claim_never_shrinks(), "the claim law failed");
        emit log_named_uint("recordedCalls", campaign.recordedCalls());
    }

    // -- what the design actually does ------------------------------------------

    /// @notice Liquidity a borrower may take is not everything unreserved.
    /// @dev The reserve ratio is the part of this design a model without it
    /// gets wrong, and it is why `held-assets-partitioned` is not trivially
    /// satisfied here.
    function test_the_borrower_cannot_take_the_required_reserve() external {
        WildcatMarketModel model = new WildcatMarketModel();
        model.deposit(100_000);
        model.borrow(100_000);
        require(model.totalAssets() == 20_000, "the reserve was lent out");
        require(model.borrowableAssets() == 0, "more was offered than is held");
        require(holds(partitioned, model), "the partition broke");
    }

    /// @notice Delinquency arrives with the request, not with the borrowing.
    /// @dev Worth asserting in that order, because it is the order that makes
    /// the design what it is. Borrowing cannot cause delinquency: the reserve
    /// is subtracted before the borrower is offered anything. What causes it is
    /// a lender asking to leave a market whose liquidity has already gone out
    /// the door, which no amount of care at borrow time can prevent.
    function test_delinquency_arrives_with_the_request() external {
        WildcatMarketModel model = new WildcatMarketModel();
        model.deposit(100_000);
        model.borrow(100_000);
        require(!model.delinquent(), "borrowing within the reserve caused delinquency");

        model.requestWithdrawal(100_000);
        require(model.delinquent(), "a market that cannot pay a request was not delinquent");
        require(!model.penalised(), "the penalty started inside the grace period");

        model.advance(1 days);
        require(!model.penalised(), "the penalty started inside the grace period");
        model.advance(30 days);
        require(model.penalised(), "the penalty never started");
    }

    /// @notice The fee cap, in the state where it used to leak.
    /// @dev The applicability notes state this with figures, so the figures are
    /// asserted here rather than described. A market holding a fifth of what one
    /// open batch is owed permitted a fee of four fifths of it while the cap was
    /// taken against the earmark, because an earmark cannot exceed what is held.
    /// Taken against the batches instead, the permitted fee is nothing: every
    /// unit of the pool is already spoken for.
    function test_a_delinquent_market_can_take_no_fee_from_a_queued_batch() external {
        WildcatMarketModel model = new WildcatMarketModel();
        model.deposit(1_000);
        model.borrow(1_000);
        model.requestWithdrawal(1_000);

        require(model.delinquent(), "the market that cannot pay was not delinquent");
        require(model.totalAssets() == 200, "the market did not keep the reserve");
        require(model.totalLenderClaims() == 1_000, "the pool is not owed 1000");
        (uint256 owed, uint256 paid) = model.claimAt(0);
        require(owed == 1_000 && paid == 0, "the batch is not owed 1000 unpaid");
        require(holds(pooled, model), "the pool started below its own batch");

        model.accrueFee(type(uint256).max);

        require(model.accruedFees() == 0, "a fee was taken out of a queued batch");
        require(model.totalLenderClaims() == 1_000, "the pool shrank");
        require(holds(pooled, model), "the fee put the pool below its own batch");
        require(holds(conserved, model), "the fee stopped conserving value");
        require(holds(backed, model), "the fee left reserves beyond claims");
    }
}
