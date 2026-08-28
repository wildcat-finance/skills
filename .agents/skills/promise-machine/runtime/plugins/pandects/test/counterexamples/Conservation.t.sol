// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ValueConserved} from "../../src/laws/ValueConserved.sol";
import {ReservesBackedByClaims} from "../../src/laws/ReservesBackedByClaims.sol";
import {HeldAssetsPartitioned} from "../../src/laws/HeldAssetsPartitioned.sol";
import {MintedClaims} from "../../specimens/MintedClaims.sol";
import {OverReserved} from "../../specimens/OverReserved.sol";
import {OverPromised} from "../../specimens/OverPromised.sol";

/// @title The counterexamples for the conservation family.
/// @notice One reduced sequence per law, replayable with no fuzzer, no seed
/// and no engine. This is the corpus's sixth requirement: a law that has only
/// ever been argued for is not reduced, and a failure nobody can reproduce on
/// demand is a story rather than a finding.
///
/// Each sequence below is the shortest that reaches the violation. They were
/// derived by hand and then checked against the engines, which is how two of
/// them came to be smaller than they were: Echidna reduced the first and third
/// to a single unit of value where the hand-written versions moved a hundred.
/// Echidna and Medusa both reproduce all three, and `audit/AUDIT.md` records
/// the campaigns.
contract ConservationCounterexamples {
    /// `MintedClaims.deposit(1)`, one call. Reduced by Echidna from the
    /// hand-written `deposit(100)`.
    /// Held rises by one and claims by two, so the right-hand side gains value
    /// the left never received.
    function test_value_conserved_counterexample() external {
        MintedClaims target = new MintedClaims();
        target.deposit(1);

        require(target.totalAssets() == 1, "held is not 1");
        require(target.totalLenderClaims() == 2, "claims is not 2");

        ValueConserved law = new ValueConserved();
        (bool held, ) = law.check(target);
        require(!held, "the counterexample no longer reproduces");
    }

    /// `OverReserved.deposit(2)`, `accrueFee(1)`, `reserve(2)`, three calls.
    /// The fee is what separates claims from held assets: without it there is
    /// no state where reserving beyond claims still fits inside the assets, and
    /// this law could not be broken alone. Echidna found the same three-call
    /// shape at magnitudes near the ceiling; this is that shape at its floor.
    function test_reserves_backed_by_claims_counterexample() external {
        OverReserved target = new OverReserved();
        target.deposit(2);
        target.accrueFee(1);
        target.reserve(2);

        require(target.totalLenderClaims() == 1, "claims is not 1");
        require(target.reservedAssets() == 2, "reserved is not 2");

        ReservesBackedByClaims law = new ReservesBackedByClaims();
        (bool held, ) = law.check(target);
        require(!held, "the counterexample no longer reproduces");
    }

    /// `OverPromised.deposit(1)`, `reserve(1)`, two calls. Reduced by Echidna
    /// from the hand-written hundreds.
    /// Borrowable stays at one because it is recorded rather than derived, so
    /// one reserved and one offered are drawn from one held.
    function test_held_assets_partitioned_counterexample() external {
        OverPromised target = new OverPromised();
        target.deposit(1);
        target.reserve(1);

        require(target.reservedAssets() == 1, "reserved is not 1");
        require(target.borrowableAssets() == 1, "borrowable is not 1");

        HeldAssetsPartitioned law = new HeldAssetsPartitioned();
        (bool held, ) = law.check(target);
        require(!held, "the counterexample no longer reproduces");
    }
}
