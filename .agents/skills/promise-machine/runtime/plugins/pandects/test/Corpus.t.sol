// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../src/ICreditObservables.sol";
import {IWithdrawalQueueObservables} from "../src/IWithdrawalQueueObservables.sol";
import {Law} from "../src/Law.sol";
import {ValueConserved} from "../src/laws/ValueConserved.sol";
import {ReservesBackedByClaims} from "../src/laws/ReservesBackedByClaims.sol";
import {HeldAssetsPartitioned} from "../src/laws/HeldAssetsPartitioned.sol";
import {QueueOrderPreserved} from "../src/laws/QueueOrderPreserved.sol";
import {ReservesCoverPayableClaims} from "../src/laws/ReservesCoverPayableClaims.sol";
import {PooledClaimsCoverOpenBatches} from "../src/laws/PooledClaimsCoverOpenBatches.sol";
import {Sound} from "../specimens/Sound.sol";
import {MintedClaims} from "../specimens/MintedClaims.sol";
import {OverReserved} from "../specimens/OverReserved.sol";
import {OverPromised} from "../specimens/OverPromised.sol";
import {DebtForgiven} from "../specimens/DebtForgiven.sol";
import {AccruesAtRest} from "../specimens/AccruesAtRest.sol";
import {CompoundsPerStep} from "../specimens/CompoundsPerStep.sol";
import {ClaimHaircut} from "../specimens/ClaimHaircut.sol";
import {QueueJumped} from "../specimens/QueueJumped.sol";
import {PayableBeyondReserves} from "../specimens/PayableBeyondReserves.sol";
import {FeeFromQueued} from "../specimens/FeeFromQueued.sol";

/// A state at the arithmetic limit. Not a catalogue specimen: it exists to
/// prove a law reports rather than reverts where the numbers are furthest
/// wrong, which is exactly where a reverting law would fall silent.
contract Extreme is ICreditObservables {
    address public asset;

    function totalAssets() external pure returns (uint256) {
        return type(uint256).max;
    }

    function totalDebt() external pure returns (uint256) {
        return type(uint256).max;
    }

    function totalLenderClaims() external pure returns (uint256) {
        return type(uint256).max;
    }

    function accruedFees() external pure returns (uint256) {
        return type(uint256).max;
    }

    function reservedAssets() external pure returns (uint256) {
        return type(uint256).max;
    }

    function borrowableAssets() external pure returns (uint256) {
        return type(uint256).max;
    }

    function observedAt() external view returns (uint256) {
        return block.timestamp;
    }
}

/// A queue at the arithmetic limit. Not a catalogue specimen either: `Extreme`
/// implements no queue, so it can reach the summing branch of a conservation law
/// and cannot reach the summing branch of a queue law. This one can.
contract ExtremeQueue is ICreditObservables, IWithdrawalQueueObservables {
    address public asset;

    function totalAssets() external pure returns (uint256) {
        return type(uint256).max;
    }

    function totalDebt() external pure returns (uint256) {
        return 0;
    }

    function totalLenderClaims() external pure returns (uint256) {
        return type(uint256).max;
    }

    function accruedFees() external pure returns (uint256) {
        return 0;
    }

    function reservedAssets() external pure returns (uint256) {
        return 0;
    }

    function borrowableAssets() external pure returns (uint256) {
        return 0;
    }

    function observedAt() external view returns (uint256) {
        return block.timestamp;
    }

    /// @dev Two claims, each owed everything there is. Their unpaid amounts sum
    /// past the word, which is the only way to ask a queue law what it does when
    /// its own addition cannot hold the answer.
    function claimCount() external pure returns (uint256) {
        return 2;
    }

    function claimAt(uint256) external pure returns (uint256 owed, uint256 paid) {
        return (type(uint256).max, 0);
    }

    /// @dev Nothing declared payable, so this fixture asks one question only.
    function payableThrough() external pure returns (uint256) {
        return 0;
    }
}

/// @title The diagonal, for the laws that judge one state.
/// @notice Every one-state law against every specimen. The claim being tested
/// is not that the laws pass: it is that each law fails exactly the specimen
/// written to break it and holds against the others.
///
/// A law that catches a specimen it was not written for is broader than its
/// statement claims, and this suite fails. A law that catches nothing may be a
/// tautology, and this suite fails. Those two failures are the reason the
/// corpus requires a specimen at all.
///
/// Four specimens here are expected to break nothing. Their defects live in
/// transitions rather than states, and no observation of one moment can show
/// them; that is the whole reason `PairLaw` exists, and `test/Pairs.t.sol` is
/// where they are caught. Asserting here that they hold every one-state law is
/// half of what makes them independent.
contract CorpusTest {
    ValueConserved internal conserved;
    ReservesBackedByClaims internal backed;
    HeldAssetsPartitioned internal partitioned;
    QueueOrderPreserved internal ordered;
    ReservesCoverPayableClaims internal covered;
    PooledClaimsCoverOpenBatches internal pooled;

    uint256 internal constant CONSERVED = 0;
    uint256 internal constant BACKED = 1;
    uint256 internal constant PARTITIONED = 2;
    uint256 internal constant ORDERED = 3;
    uint256 internal constant COVERED = 4;
    uint256 internal constant POOLED = 5;
    uint256 internal constant COUNT = 6;

    /// No one-state law is expected to catch this specimen.
    uint256 internal constant NOTHING = type(uint256).max;

    function setUp() public {
        conserved = new ValueConserved();
        backed = new ReservesBackedByClaims();
        partitioned = new HeldAssetsPartitioned();
        ordered = new QueueOrderPreserved();
        covered = new ReservesCoverPayableClaims();
        pooled = new PooledClaimsCoverOpenBatches();
    }

    function laws() internal view returns (Law[COUNT] memory) {
        return [
            Law(conserved),
            Law(backed),
            Law(partitioned),
            Law(ordered),
            Law(covered),
            Law(pooled)
        ];
    }

    /// Every law against one target, as a list of which held.
    function verdicts(ICreditObservables target)
        internal
        view
        returns (bool[COUNT] memory out)
    {
        Law[COUNT] memory all = laws();
        for (uint256 i = 0; i < COUNT; i++) {
            (bool held, ) = all[i].check(target);
            out[i] = held;
        }
    }

    function assertDiagonal(ICreditObservables target, uint256 breaks) internal view {
        bool[COUNT] memory held = verdicts(target);
        for (uint256 i = 0; i < COUNT; i++) {
            if (i == breaks) {
                require(!held[i], "the law written for this specimen did not catch it");
            } else {
                require(held[i], "a law caught a specimen it was not written for");
            }
        }
    }

    // -- the sound reference ------------------------------------------------

    function test_the_sound_reference_holds_every_law() external {
        Sound target = new Sound();
        target.deposit(100);
        target.borrow(30);
        target.advance(86400);
        target.accrueFee(10);
        target.reserve(20);
        target.payClaim(5);
        assertDiagonal(target, NOTHING);
    }

    function test_a_sound_system_at_rest_holds_every_law() external {
        Sound target = new Sound();
        assertDiagonal(target, NOTHING);
    }

    // -- the diagonal -------------------------------------------------------

    function test_minted_claims_breaks_conservation_alone() external {
        MintedClaims target = new MintedClaims();
        target.deposit(100);
        assertDiagonal(target, CONSERVED);
    }

    function test_over_reserved_breaks_reserve_backing_alone() external {
        OverReserved target = new OverReserved();
        target.deposit(100);
        target.accrueFee(60);
        target.reserve(80);
        assertDiagonal(target, BACKED);
    }

    function test_over_promised_breaks_the_partition_alone() external {
        OverPromised target = new OverPromised();
        target.deposit(100);
        target.reserve(50);
        assertDiagonal(target, PARTITIONED);
    }

    function test_queue_jumped_breaks_the_ordering_alone() external {
        QueueJumped target = new QueueJumped();
        target.deposit(2);
        target.reserve(1);
        target.reserve(1);
        target.payClaim(1);
        assertDiagonal(target, ORDERED);
    }

    function test_payable_beyond_reserves_breaks_the_cover_alone() external {
        PayableBeyondReserves target = new PayableBeyondReserves();
        target.deposit(2);
        target.borrow(1);
        target.reserve(1);
        target.reserve(1);
        assertDiagonal(target, COVERED);
    }

    /// `deposit(100)`, `borrow(50)`, `reserve(100)`, `reserve(100)`,
    /// `accrueFee(...)`. The borrow leaves the system holding half what it owes,
    /// so its earmark stops short of the queue, and the fee takes the shortfall
    /// out of value two lenders were already promised.
    function test_fee_from_queued_breaks_the_pooled_cover_alone() external {
        FeeFromQueued target = new FeeFromQueued();
        target.deposit(100);
        target.borrow(50);
        target.reserve(100);
        target.reserve(100);
        target.accrueFee(type(uint256).max);
        assertDiagonal(target, POOLED);
    }

    // -- the specimens no one-state law can see -----------------------------

    function test_debt_forgiven_holds_every_one_state_law() external {
        DebtForgiven target = new DebtForgiven();
        target.deposit(1);
        target.borrow(1);
        target.accrueFee(1);
        target.forgive(1);
        assertDiagonal(target, NOTHING);
    }

    function test_accrues_at_rest_holds_every_one_state_law() external {
        AccruesAtRest target = new AccruesAtRest();
        target.poke(1);
        assertDiagonal(target, NOTHING);
    }

    function test_compounds_per_step_holds_every_one_state_law() external {
        CompoundsPerStep target = new CompoundsPerStep();
        target.deposit(1000);
        target.borrow(1000);
        target.advance(31536000);
        target.advance(31536000);
        assertDiagonal(target, NOTHING);
    }

    function test_claim_haircut_holds_every_one_state_law() external {
        ClaimHaircut target = new ClaimHaircut();
        target.deposit(1);
        target.reserve(1);
        target.haircut(0, 1);
        assertDiagonal(target, NOTHING);
    }

    // -- what a law must not do ---------------------------------------------

    /// @notice Reporting rather than reverting, where the numbers are worst.
    /// @dev Only the three conservation laws are asked. `Extreme` reports the
    /// core observables and implements no withdrawal queue, so the two queue
    /// laws revert on the read rather than on the arithmetic. That is the
    /// documented limit and not the thing this test is about: an unobservable
    /// state produces no verdict, and the harness counts the revert.
    function test_no_law_reverts_at_the_arithmetic_limit() external {
        Extreme target = new Extreme();
        Law[3] memory summing = [Law(conserved), Law(backed), Law(partitioned)];
        for (uint256 i = 0; i < 3; i++) {
            (bool ok, ) = address(summing[i]).staticcall(
                abi.encodeWithSelector(Law.check.selector, address(target))
            );
            require(ok, "a law reverted where the numbers are furthest wrong");
        }
    }

    /// @notice A law asked about a state it cannot observe reverts, and says
    /// nothing.
    /// @dev Worth asserting rather than assuming. The three queue laws reach
    /// past the core observables, and the corpus's answer to a target that
    /// cannot answer is a revert -- neither a violation nor a pass. A law that
    /// returned `true` here would be reporting that a system with no queue
    /// keeps its queue in order.
    function test_a_queue_law_over_a_target_with_no_queue_reverts() external {
        Extreme target = new Extreme();
        Law[3] memory queueLaws = [Law(ordered), Law(covered), Law(pooled)];
        for (uint256 i = 0; i < 3; i++) {
            (bool ok, ) = address(queueLaws[i]).staticcall(
                abi.encodeWithSelector(Law.check.selector, address(target))
            );
            require(!ok, "a queue law claimed a verdict it could not have");
        }
    }

    /// @notice Overflow is a verdict, and only for the laws that add.
    /// @dev Worth separating from the revert test above, because the two are
    /// different claims. Both laws that sum report the overflow as a
    /// violation. The law that only compares holds, and correctly so: at the
    /// limit, reserved really is no greater than claims. A test asserting all
    /// three were violated would have been asserting something false.
    function test_a_sum_that_overflows_is_reported_as_a_violation() external {
        Extreme target = new Extreme();
        (bool conservedHeld, ) = conserved.check(target);
        (bool partitionedHeld, ) = partitioned.check(target);
        (bool backedHeld, ) = backed.check(target);
        require(!conservedHeld, "an overflowing sum was not reported");
        require(!partitionedHeld, "an overflowing sum was not reported");
        require(backedHeld, "a comparison that holds was reported as violated");
    }

    /// @notice A queue law's own addition overflowing is a verdict too.
    /// @dev Separate from the test above because `Extreme` has no queue, so it
    /// can never reach this branch. Two claims each owed everything there is sum
    /// past the word, and the law reports that rather than reverting on it --
    /// which is the whole argument for summing unchecked: in 0.8 the addition
    /// would revert, and a revert under fail_on_revert = false is silence
    /// exactly where the numbers have gone furthest wrong.
    function test_a_queue_law_reports_its_own_overflow() external {
        ExtremeQueue target = new ExtremeQueue();
        (bool ok, bytes memory returned) = address(pooled).staticcall(
            abi.encodeWithSelector(Law.check.selector, address(target))
        );
        require(ok, "the law reverted instead of reporting the overflow");
        (bool held, string memory detail) = abi.decode(returned, (bool, string));
        require(!held, "an overflowing queue sum was not reported");
        require(
            keccak256(bytes(detail))
                == keccak256(bytes("the open batches sum to more than can be counted")),
            "the overflow was reported with the wrong reason"
        );
    }

    function test_every_law_returns_a_detail_whichever_way_it_decides() external {
        Sound sound = new Sound();
        MintedClaims broken = new MintedClaims();
        broken.deposit(100);
        Law[COUNT] memory all = laws();
        for (uint256 i = 0; i < COUNT; i++) {
            (, string memory onSound) = all[i].check(sound);
            (, string memory onBroken) = all[i].check(broken);
            require(bytes(onSound).length > 0, "a verdict without a detail");
            require(bytes(onBroken).length > 0, "a verdict without a detail");
        }
    }

    function test_every_law_carries_an_identifier_and_a_statement() external view {
        Law[COUNT] memory all = laws();
        for (uint256 i = 0; i < COUNT; i++) {
            require(bytes(all[i].id()).length > 0, "a law with no id");
            require(bytes(all[i].statement()).length > 0, "a law with no statement");
        }
    }
}
