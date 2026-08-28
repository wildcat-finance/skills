// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {CorpusBase, CorpusDriver} from "../CorpusBase.sol";

/// @title The corpus under the prefix Echidna reads.
/// @notice The same laws the Foundry adapter asks about, asked through
/// `echidna_`. The prefix is an engine's contract rather than a style choice,
/// so it is answered here rather than argued with.
///
/// A property function returns only a boolean. When one fails, replay the
/// sequence and call `explainOneState` or `explainSuccession` for the reason in
/// the law's own words, rather than deriving it from a call trace.
abstract contract CorpusEchidna is CorpusBase {
    function hasWithdrawalQueue() public view virtual returns (bool) {
        return true;
    }

    function echidna_value_conserved() external view returns (bool) {
        return judge(conserved);
    }

    function echidna_reserves_backed() external view returns (bool) {
        return judge(backed);
    }

    function echidna_held_partitioned() external view returns (bool) {
        return judge(partitioned);
    }

    function echidna_queue_order_preserved() external view returns (bool) {
        return !hasWithdrawalQueue() || judge(ordered);
    }

    function echidna_reserves_cover_payable() external view returns (bool) {
        return !hasWithdrawalQueue() || judge(covered);
    }

    function echidna_pooled_claims_cover_open_batches() external view returns (bool) {
        return !hasWithdrawalQueue() || judge(pooled);
    }
}

/// @title The same, plus the succession laws, for a target you front.
/// @notice Extend this, write your protocol's entry points, and put `records`
/// on every one that changes state. Echidna calls those entry points; the
/// snapshot happens on the way in.
abstract contract DrivenCorpusEchidna is CorpusEchidna, CorpusDriver {
    function echidna_debt_falls_only_against_payment() external view returns (bool) {
        return judgePair(falls);
    }

    function echidna_no_accrual_at_rest() external view returns (bool) {
        return judgePair(atRest);
    }

    function echidna_recorded_claim_never_shrinks() external view returns (bool) {
        return judgePair(shrinks);
    }
}
