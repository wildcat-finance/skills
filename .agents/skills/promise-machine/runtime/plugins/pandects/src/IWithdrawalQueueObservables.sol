// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

/// @title What a system with a withdrawal queue additionally exposes.
/// @notice An extension, deliberately kept out of `ICreditObservables`. A
/// system with no queue would have to implement a claim count, a claim
/// accessor and a payable bound that all mean nothing, and an observable that
/// means nothing is worse than an absent one: it reports zero, and zero reads
/// like an answer.
///
/// A law that needs this says so in its applicability, and a target that does
/// not implement it reverts on the read. That is the limit `Law` already
/// states: the state could not be observed, the law has no opinion, and the
/// harness counts a revert. It is not a violation and it is not a pass.
///
/// The queue is an ordering over recorded claims, not over lenders. Two claims
/// from the same lender are two entries, and a system that merges them has
/// changed what it owes on each, which is the subject of a law.
interface IWithdrawalQueueObservables {
    /// @notice How many withdrawal claims the system has recorded.
    /// @dev Recorded, not outstanding. A claim paid in full stays in the count
    /// and stays at its index, because the laws over this interface compare
    /// claims across two observations by index, and a queue that renumbers
    /// itself makes that comparison meaningless.
    function claimCount() external view returns (uint256);

    /// @notice One recorded claim.
    /// @param index Position in the queue, oldest first.
    /// @return owed The amount recorded against this claim when it was made.
    /// @return paid How much of that has since been handed over.
    function claimAt(uint256 index)
        external
        view
        returns (uint256 owed, uint256 paid);

    /// @notice The exclusive bound of the claims the system declares payable.
    /// @dev Claims at indices below this are ones the system says it can
    /// settle now. It is a declaration rather than a derivation, which is
    /// precisely why it is worth a law: a system that declares more payable
    /// than it has set aside has promised something it cannot do, and only the
    /// declaration makes that visible from outside.
    function payableThrough() external view returns (uint256);
}
