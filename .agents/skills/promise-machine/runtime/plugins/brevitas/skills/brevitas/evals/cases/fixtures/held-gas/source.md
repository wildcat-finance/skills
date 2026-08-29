// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "./ICreditObservables.sol";
import {IWithdrawalQueueObservables} from "./IWithdrawalQueueObservables.sol";

/// @notice One recorded withdrawal claim, as observed.
struct ClaimRecord {
    uint256 owed;
    uint256 paid;
}

/// @notice Every quantity a target reports, taken at one moment.
/// @dev A snapshot rather than a live target, because the laws that need two
/// observations need to hold the earlier one after the system has moved past
/// it. A law handed two targets could only ever compare two systems; a law
/// handed two observations can compare one system with its own past.
///
/// `queueObserved` is a claim about the reading, not about the system. False
/// means nobody looked, which is why it is here rather than being inferred
/// from an empty array: a queue with no claims and a queue nobody read are
/// different things, and a law that confuses them would pass on the second.
struct Observation {
    uint256 totalAssets;
    uint256 totalDebt;
    uint256 totalLenderClaims;
    uint256 reservedAssets;
    uint256 borrowableAssets;
    uint256 accruedFees;
    uint256 observedAt;
    bool queueObserved;
    uint256 payableThrough;
    ClaimRecord[] queue;
}

/// @title Reading a target into an observation.
library Observe {
    /// @notice The core observables, and nothing else.
    function take(ICreditObservables target)
        internal
        view
        returns (Observation memory found)
    {
        found.totalAssets = target.totalAssets();
        found.totalDebt = target.totalDebt();
        found.totalLenderClaims = target.totalLenderClaims();
        found.reservedAssets = target.reservedAssets();
        found.borrowableAssets = target.borrowableAssets();
        found.accruedFees = target.accruedFees();
        found.observedAt = target.observedAt();
    }

    /// @notice The core observables and the withdrawal queue.
    /// @dev Reads every recorded claim, one external call each, so a long
    /// enough queue exhausts the gas and reverts. That is the same limit the
    /// queue laws carry and it is deliberate: a partial snapshot would let a
    /// law about the whole queue return a verdict about part of one.
    ///
    /// Reverts if the target does not implement the queue extension. That
    /// is the intended behaviour and the same limit `Law` states: an
    /// unobservable state produces no verdict rather than a false one. Take
    /// the core observables instead when the target may have no queue.
    function takeWithQueue(ICreditObservables target)
        internal
        view
        returns (Observation memory found)
    {
        found = take(target);
        IWithdrawalQueueObservables queue =
            IWithdrawalQueueObservables(address(target));
        uint256 count = queue.claimCount();
        found.queue = new ClaimRecord[](count);
        for (uint256 i = 0; i < count; i++) {
            (uint256 owed, uint256 paid) = queue.claimAt(i);
            found.queue[i] = ClaimRecord({owed: owed, paid: paid});
        }
        found.payableThrough = queue.payableThrough();
        found.queueObserved = true;
    }
}
