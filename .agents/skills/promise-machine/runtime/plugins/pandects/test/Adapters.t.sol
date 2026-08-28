// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {CorpusObserver} from "../adapters/CorpusBase.sol";
import {PathIndependenceProbe} from "../adapters/foundry/PathIndependenceProbe.sol";
import {ICreditObservables} from "../src/ICreditObservables.sol";
import {DrivenClaimHaircutEchidna, ObservedQueueJumpedEchidna} from "../src/campaigns/Adapters.sol";
import {FeeFromQueuedCampaign} from "../src/campaigns/Specimens.sol";
import {Sound} from "../specimens/Sound.sol";
import {CompoundsPerStep} from "../specimens/CompoundsPerStep.sol";
import {QueueJumped} from "../specimens/QueueJumped.sol";

/// @title The adapters, against targets they did not build.
/// @notice Three claims. An observing adapter judges a target nobody routed
/// calls through, and offers no pair law. A driving adapter offers them, and
/// one fires. And the ninth law, which no adapter can carry, is reachable
/// through a probe that takes both systems.
/// A target that reports the core observables and has no withdrawal queue.
/// Plenty of credit systems have none, and the corpus is meant to stay useful
/// for them rather than narrowing to systems shaped like the reference.
contract NoQueue is ICreditObservables {
    address public asset;

    function totalAssets() external pure returns (uint256) {
        return 0;
    }

    function totalDebt() external pure returns (uint256) {
        return 0;
    }

    function totalLenderClaims() external pure returns (uint256) {
        return 0;
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

    function observedAt() external pure returns (uint256) {
        return 0;
    }
}

contract AdaptersTest {
    uint256 internal constant PRINCIPAL = 100_000;
    uint256 internal constant HALF_SPAN = 182.5 days;
    uint256 internal constant WHOLE_SPAN = 365 days;

    // -- the observing adapter ----------------------------------------------

    /// @notice A target driven by somebody else, judged anyway.
    /// @dev The specimen is built here and handed over. Nothing routes its
    /// calls through the adapter, and the one-state laws still decide.
    function test_the_observer_judges_a_target_it_does_not_front() external {
        QueueJumped system = new QueueJumped();
        CorpusObserver observer = new CorpusObserver(ICreditObservables(address(system)));

        require(observer.coreHolds(), "a sound state was reported as violated");
        require(observer.queueHolds(), "an ordered queue was reported as violated");

        system.deposit(2);
        system.reserve(1);
        system.reserve(1);
        system.payClaim(1);

        require(observer.coreHolds(), "the conservation laws were dragged down with it");
        require(!observer.queueHolds(), "the observer missed a queue paid out of turn");
    }

    /// @notice The observer offers no pair law, and this is how that is checked.
    /// @dev Not a comment: the selector is absent from the deployed code, so
    /// the call reverts. An observer that answered here would answer for every
    /// target forever, because nothing gave it a past to compare with.
    function test_the_observer_offers_no_pair_law() external {
        CorpusObserver observer =
            new CorpusObserver(ICreditObservables(address(new Sound())));
        (bool ok, ) = address(observer).staticcall(
            abi.encodeWithSignature("successionHolds()")
        );
        require(!ok, "the observer answered a question it cannot have an answer to");
    }

    /// @notice And the reasons come back in the laws' own words.
    function test_the_observer_carries_a_reason_for_every_verdict() external {
        QueueJumped system = new QueueJumped();
        system.deposit(2);
        system.reserve(1);
        system.reserve(1);
        system.payClaim(1);
        CorpusObserver observer = new CorpusObserver(ICreditObservables(address(system)));
        string[6] memory details = observer.explainOneState();
        for (uint256 i = 0; i < 6; i++) {
            require(bytes(details[i]).length > 0, "a verdict without a detail");
        }
        require(
            keccak256(bytes(details[3]))
                == keccak256("a claim was paid while an older one was still owed"),
            "the reason is not the one the law gives"
        );
    }

    /// @notice A target with no queue still gets the reasons it can have.
    /// @dev `explainOneState` reads all six and reverts here, which is the
    /// documented limit. `explainCore` is the three that had an answer, and the
    /// point is that they are reachable rather than taken down with the other
    /// two.
    function test_a_queueless_target_still_gets_the_core_reasons() external {
        CorpusObserver observer =
            new CorpusObserver(ICreditObservables(address(new NoQueue())));

        (bool everything, ) = address(observer).staticcall(
            abi.encodeWithSignature("explainOneState()")
        );
        require(!everything, "a queue was read off a target that has none");

        string[3] memory core = observer.explainCore();
        for (uint256 i = 0; i < 3; i++) {
            require(bytes(core[i]).length > 0, "a law that could judge gave no reason");
        }
        require(observer.coreHolds(), "an empty system was reported as violated");
    }

    // -- the driving adapter -------------------------------------------------

    /// @notice A succession law fires through the adapter that fronted the call.
    function test_the_driver_catches_a_claim_written_down() external {
        DrivenClaimHaircutEchidna driven = new DrivenClaimHaircutEchidna();

        require(driven.successionHolds(), "a pair law fired before any call was made");

        driven.deposit(1);
        driven.reserve(1);
        require(driven.successionHolds(), "a pair law fired on a sound transition");

        driven.haircut(0, 1);
        require(!driven.successionHolds(), "the driver missed a claim written down");

        string[3] memory why = driven.explainSuccession();
        require(
            keccak256(bytes(why[2]))
                == keccak256("a recorded claim's owed amount changed"),
            "the reason is not the one the law gives"
        );
    }

    /// @notice The engine prefix is present, and answers.
    /// @notice Both prefixes, for the law the harness was last extended for.
    /// @dev The two wrappers are separate functions delegating to the same
    /// internal judgement, so one of them can be wired to the wrong law and only
    /// a campaign under that one engine would notice. Asserting both here means a
    /// mistake in either shows up in the deterministic suite, where the
    /// counterexample already is.
    function test_both_prefixes_answer_for_the_new_law() external {
        FeeFromQueuedCampaign campaign = new FeeFromQueuedCampaign();
        require(
            campaign.echidna_pooled_claims_cover_open_batches(),
            "a sound state was reported as violated"
        );
        require(
            campaign.property_pooled_claims_cover_open_batches(),
            "a sound state was reported as violated"
        );

        campaign.deposit(2);
        campaign.borrow(1);
        campaign.reserve(2);
        campaign.accrueFee(1);

        require(
            !campaign.echidna_pooled_claims_cover_open_batches(),
            "the campaign missed the fee taken from a queued batch"
        );
        require(
            !campaign.property_pooled_claims_cover_open_batches(),
            "the campaign missed it under the other prefix"
        );
        require(
            campaign.echidna_value_conserved(),
            "an unrelated law was dragged down"
        );
        require(
            campaign.echidna_reserves_backed(),
            "an unrelated law was dragged down"
        );
    }

    function test_the_echidna_entry_points_answer() external {
        ObservedQueueJumpedEchidna observed = new ObservedQueueJumpedEchidna();
        require(observed.echidna_value_conserved(), "a sound state was reported as violated");
        require(observed.echidna_queue_order_preserved(), "an ordered queue was reported as violated");
        observed.deposit(2);
        observed.reserve(1);
        observed.reserve(1);
        observed.payClaim(1);
        require(!observed.echidna_queue_order_preserved(), "the campaign missed the jump");
        require(observed.echidna_value_conserved(), "an unrelated law was dragged down");
    }

    /// @notice A driver whose entry points forgot `records` reports holding.
    /// @dev The failure mode this cannot prevent, made visible instead. The
    /// succession laws return true because nothing gave them a past, which is
    /// indistinguishable from them holding -- so the count is what tells the two
    /// apart, and an integrator has something to assert on.
    function test_a_driver_that_recorded_nothing_says_so() external {
        DrivenClaimHaircutEchidna driven = new DrivenClaimHaircutEchidna();

        require(driven.successionHolds(), "an unexercised pair law reported a violation");
        require(!driven.successionExercised(), "nothing was called and it claims otherwise");
        require(driven.recordedCalls() == 0, "a call was recorded before any was made");

        string[3] memory why = driven.explainSuccession();
        require(
            keccak256(bytes(why[0]))
                == keccak256("no call was recorded, so no transition was judged"),
            "the adapter did not say that it judged nothing"
        );

        driven.deposit(1);
        require(driven.successionExercised(), "a recorded call was not counted");
        require(driven.recordedCalls() == 1, "the count is not one after one call");
    }

    // -- the probe -----------------------------------------------------------

    /// @notice The ninth law, reached through the only shape that can carry it.
    function test_the_probe_catches_compounding_and_clears_the_reference() external {
        PathIndependenceProbe probe = new PathIndependenceProbe(2);
        require(probe.tolerance() == 1, "the bound is not n-1 for two subdivisions");

        (Sound soundCoarse, Sound soundFine) = race(new Sound(), new Sound());
        (bool sound, ) = probe.check(soundCoarse, soundFine);
        require(sound, "the reference was reported as path dependent");

        (Sound coarse, Sound fine) = race(new CompoundsPerStep(), new CompoundsPerStep());
        (bool broken, string memory why) = probe.check(coarse, fine);
        require(!broken, "the probe missed a system that compounds");
        require(bytes(why).length > 0, "a verdict without a detail");
    }

    /// @notice A probe built for the wrong run is wrong, and says nothing.
    /// @dev The hazard belongs to the law and the caller meets it here, so it
    /// is asserted here too.
    function test_a_probe_built_for_the_wrong_run_passes_a_broken_system() external {
        PathIndependenceProbe generous = new PathIndependenceProbe(1000);
        (Sound coarse, Sound fine) = race(new CompoundsPerStep(), new CompoundsPerStep());
        (bool held, ) = generous.check(coarse, fine);
        require(held, "the bound did not widen with the count, so this proves nothing");
    }

    function race(Sound coarse, Sound fine) internal returns (Sound, Sound) {
        coarse.deposit(PRINCIPAL);
        coarse.borrow(PRINCIPAL);
        fine.deposit(PRINCIPAL);
        fine.borrow(PRINCIPAL);
        coarse.advance(WHOLE_SPAN);
        fine.advance(HALF_SPAN);
        fine.advance(HALF_SPAN);
        return (coarse, fine);
    }
}
