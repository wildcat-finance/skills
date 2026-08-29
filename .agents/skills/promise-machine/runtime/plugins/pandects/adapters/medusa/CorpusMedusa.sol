// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {CorpusBase, CorpusDriver} from "../CorpusBase.sol";

/// @title The corpus under the prefix Medusa defaults to.
/// @notice The same laws the Echidna adapter asks about, asked through
/// `property_`. Two files rather than one because the prefixes are fixed by the
/// engines and a contract carrying both would answer every question twice; an
/// integrator picks the engine they run.
///
/// The convention detector is answered here rather than obeyed: `property_` is
/// what Medusa looks for, and a harness that renamed it to satisfy a linter
/// would be a harness Medusa never calls.
// slither-disable-start naming-convention
abstract contract CorpusMedusa is CorpusBase {
    function hasWithdrawalQueue() public view virtual returns (bool) {
        return true;
    }

    function property_value_conserved() external view returns (bool) {
        return judge(conserved);
    }

    function property_reserves_backed() external view returns (bool) {
        return judge(backed);
    }

    function property_held_partitioned() external view returns (bool) {
        return judge(partitioned);
    }

    function property_queue_order_preserved() external view returns (bool) {
        return !hasWithdrawalQueue() || judge(ordered);
    }

    function property_reserves_cover_payable() external view returns (bool) {
        return !hasWithdrawalQueue() || judge(covered);
    }

    function property_pooled_claims_cover_open_batches() external view returns (bool) {
        return !hasWithdrawalQueue() || judge(pooled);
    }
}

/// @title The same, plus the succession laws, for a target you front.
abstract contract DrivenCorpusMedusa is CorpusMedusa, CorpusDriver {
    function property_debt_falls_only_against_payment() external view returns (bool) {
        return judgePair(falls);
    }

    function property_no_accrual_at_rest() external view returns (bool) {
        return judgePair(atRest);
    }

    function property_recorded_claim_never_shrinks() external view returns (bool) {
        return judgePair(shrinks);
    }
}
// slither-disable-end naming-convention
