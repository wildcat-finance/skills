// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {DrivenCorpusEchidna} from "../../adapters/echidna/CorpusEchidna.sol";
import {DrivenCorpusMedusa} from "../../adapters/medusa/CorpusMedusa.sol";
import {ICreditObservables} from "../ICreditObservables.sol";
import {WildcatMarketModel} from "../../integrations/wildcat/WildcatMarketModel.sol";

/// @title The Wildcat model, driven through the step 4 adapters.
/// @dev No harness written specially for it. These are the same adapters an
/// integrator extends, and the point of the integration is that the corpus
/// arrives whole rather than being re-derived for each design.
///
/// Under `src/` because crytic-compile skips `test/`.
///
/// `path-independent` is absent, as it is from every campaign: it compares two
/// markets advanced by different routes. For this design that absence carries
/// more than usual, because the law is conditional here --
/// `test/Wildcat.t.sol` holds it while the market is solvent and watches it
/// fail once the penalty is running.
///
/// `recorded_claim_never_shrinks` is expected to fail here, and the failure is
/// the finding rather than a defect. A batch accumulates while it is open, so
/// the amount owed on it rises, and the law says a recorded claim keeps its
/// amount. Echidna found it against this contract after the applicability notes
/// had already claimed the law held.
/// `integrations/wildcat/APPLICABILITY.md` is where that is settled.
contract WildcatMarketCampaign is DrivenCorpusEchidna {
    WildcatMarketModel internal immutable market = new WildcatMarketModel();

    function target() public view override returns (ICreditObservables) {
        return market;
    }

    function deposit(uint256 amount) external records {
        market.deposit(amount);
    }

    function borrow(uint256 amount) external records {
        market.borrow(amount);
    }

    function repay(uint256 amount) external records {
        market.repay(amount);
    }

    function advance(uint256 elapsed) external records {
        market.advance(elapsed);
    }

    function accrueFee(uint256 amount) external records {
        market.accrueFee(amount);
    }

    function requestWithdrawal(uint256 amount) external records {
        market.requestWithdrawal(amount);
    }

    function payBatch(uint256 amount) external records {
        market.payBatch(amount);
    }
}

/// @notice The same market, under the prefix Medusa reads.
contract WildcatMarketCampaignMedusa is DrivenCorpusMedusa {
    WildcatMarketModel internal immutable market = new WildcatMarketModel();

    function target() public view override returns (ICreditObservables) {
        return market;
    }

    function deposit(uint256 amount) external records {
        market.deposit(amount);
    }

    function borrow(uint256 amount) external records {
        market.borrow(amount);
    }

    function repay(uint256 amount) external records {
        market.repay(amount);
    }

    function advance(uint256 elapsed) external records {
        market.advance(elapsed);
    }

    function accrueFee(uint256 amount) external records {
        market.accrueFee(amount);
    }

    function requestWithdrawal(uint256 amount) external records {
        market.requestWithdrawal(amount);
    }

    function payBatch(uint256 amount) external records {
        market.payBatch(amount);
    }
}
