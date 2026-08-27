// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {
    AccruesAtRestCampaign,
    FeeFromQueuedCampaign,
    MintedClaimsCampaign
} from "../src/campaigns/Specimens.sol";

/// @title The reason a campaign gives, after it fails.
/// @notice A property function can only say no. `explain` is where the reason
/// lives, and this asserts that replaying a failing sequence and calling it
/// returns the law's own words rather than something the harness invented.
contract ExplainTest {
    /// The positions `explain` returns, one-state first and then pair, named
    /// rather than written as numerals at each use. They were numerals until a
    /// tenth law was inserted in the middle of the one-state group and every
    /// pair-law index moved by one, which a reader of `details[6]` had no way to
    /// notice.
    uint256 internal constant CONSERVED = 0;
    uint256 internal constant BACKED = 1;
    uint256 internal constant PARTITIONED = 2;
    uint256 internal constant ORDERED = 3;
    uint256 internal constant COVERED = 4;
    uint256 internal constant POOLED = 5;
    uint256 internal constant FALLS = 6;
    uint256 internal constant AT_REST = 7;
    uint256 internal constant SHRINKS = 8;
    uint256 internal constant WIDTH = 9;

    function test_explain_names_the_quantities_that_disagreed() external {
        MintedClaimsCampaign campaign = new MintedClaimsCampaign();
        campaign.deposit(1);
        string[WIDTH] memory details = campaign.explain();
        require(bytes(details[CONSERVED]).length > 0, "no reason given");
        require(
            keccak256(bytes(details[CONSERVED]))
                == keccak256("held plus owed differs from claimed plus accrued"),
            "the reason is not the one the law gives"
        );
    }

    /// @notice The same, for a law that judges a transition rather than a state.
    /// @dev Worth its own case. A pair law's reason has to survive the harness
    /// holding one of the two observations in storage between calls, and a
    /// harness that lost the earlier one would still return a string -- just
    /// the wrong one.
    function test_explain_carries_the_reason_a_pair_law_gave() external {
        AccruesAtRestCampaign campaign = new AccruesAtRestCampaign();
        campaign.poke(1);
        string[WIDTH] memory details = campaign.explain();
        require(
            keccak256(bytes(details[AT_REST]))
                == keccak256("debt rose while time stood still and assets stayed"),
            "the reason is not the one the law gives"
        );
    }

    /// @notice Before any call, a pair law has nothing to compare and says so.
    function test_explain_is_empty_for_the_pair_laws_before_the_first_call()
        external
    {
        AccruesAtRestCampaign campaign = new AccruesAtRestCampaign();
        string[WIDTH] memory details = campaign.explain();
        require(bytes(details[CONSERVED]).length > 0, "a one-state law gave no reason");
        require(bytes(details[POOLED]).length > 0, "a one-state law gave no reason");
        require(
            bytes(details[FALLS]).length == 0,
            "a pair law judged a pair it did not have"
        );
    }

    /// @notice And the reason for the law this harness was last extended for.
    /// @dev The point of widening `explain` rather than leaving it at eight. A
    /// campaign that falsifies the new property and then reports eight reasons,
    /// none of them this law's, sends the reader back to the call trace to work
    /// out what the law had actually compared.
    function test_explain_carries_the_reason_the_new_law_gave() external {
        FeeFromQueuedCampaign campaign = new FeeFromQueuedCampaign();
        campaign.deposit(2);
        campaign.borrow(1);
        campaign.reserve(2);
        campaign.accrueFee(1);
        string[WIDTH] memory details = campaign.explain();
        require(
            keccak256(bytes(details[POOLED]))
                == keccak256("pooled claims are below what the open batches are owed"),
            "the reason is not the one the law gives"
        );
    }
}
