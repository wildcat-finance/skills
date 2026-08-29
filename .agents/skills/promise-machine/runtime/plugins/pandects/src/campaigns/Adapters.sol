// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {CorpusEchidna, DrivenCorpusEchidna} from "../../adapters/echidna/CorpusEchidna.sol";
import {CorpusMedusa, DrivenCorpusMedusa} from "../../adapters/medusa/CorpusMedusa.sol";
import {ICreditObservables} from "../ICreditObservables.sol";
import {ClaimHaircut} from "../../specimens/ClaimHaircut.sol";
import {QueueJumped} from "../../specimens/QueueJumped.sol";

/// @title The adapters, pointed at a target they did not build.
/// @dev Under `src/` for the same reason `Specimens.sol` is: crytic-compile
/// skips `test/` when it builds a Foundry project, and a harness the engine
/// cannot see is a campaign that quietly tests nothing. It is also what makes
/// the adapters compile at all -- they are abstract, so nothing checks them
/// until something concrete extends them.
///
/// Each of these is what an integrator writes: a few lines naming their system
/// and their entry points. The laws arrive with the base.
///
/// One engine per contract. The prefixes are fixed by Echidna and Medusa, and a
/// contract carrying both would answer every question twice.

/// @notice `QueueJumped` observed rather than fronted. `queue_order_preserved`
/// is expected to fail once the specimen has paid out of turn, and it fails
/// through an adapter that never saw the call that did it -- which is the whole
/// case for the observing form.
contract ObservedQueueJumpedEchidna is CorpusEchidna {
    QueueJumped internal immutable system = new QueueJumped();

    function target() public view override returns (ICreditObservables) {
        return system;
    }

    function deposit(uint256 amount) external {
        system.deposit(amount);
    }

    function reserve(uint256 amount) external {
        system.reserve(amount);
    }

    function payClaim(uint256 amount) external {
        system.payClaim(amount);
    }
}

/// @notice `ClaimHaircut` fronted, so the succession laws have a past to read.
/// `recorded_claim_never_shrinks` is expected to fail. Every entry point below
/// carries `records`, which is the entire mechanism.
contract DrivenClaimHaircutEchidna is DrivenCorpusEchidna {
    ClaimHaircut internal immutable system = new ClaimHaircut();

    function target() public view override returns (ICreditObservables) {
        return system;
    }

    function deposit(uint256 amount) external records {
        system.deposit(amount);
    }

    function reserve(uint256 amount) external records {
        system.reserve(amount);
    }

    function haircut(uint256 index, uint256 amount) external records {
        system.haircut(index, amount);
    }
}

/// @notice The observing adapter under Medusa's prefix.
contract ObservedQueueJumpedMedusa is CorpusMedusa {
    QueueJumped internal immutable system = new QueueJumped();

    function target() public view override returns (ICreditObservables) {
        return system;
    }

    function deposit(uint256 amount) external {
        system.deposit(amount);
    }

    function reserve(uint256 amount) external {
        system.reserve(amount);
    }

    function payClaim(uint256 amount) external {
        system.payClaim(amount);
    }
}

/// @notice The driving adapter under Medusa's prefix.
contract DrivenClaimHaircutMedusa is DrivenCorpusMedusa {
    ClaimHaircut internal immutable system = new ClaimHaircut();

    function target() public view override returns (ICreditObservables) {
        return system;
    }

    function deposit(uint256 amount) external records {
        system.deposit(amount);
    }

    function reserve(uint256 amount) external records {
        system.reserve(amount);
    }

    function haircut(uint256 index, uint256 amount) external records {
        system.haircut(index, amount);
    }
}
