// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

/// @title The economic roles a law is allowed to read.
/// @notice A law names roles, never implementations. That is not a style
/// preference: a property written against `market.totalSupply()` is a property
/// about one codebase, and the corpus exists because the same economic facts
/// hold across codebases that share nothing else.
///
/// A target implements this directly, or a thin adapter does it on the target's
/// behalf. The adapter is the only place a protocol's own names appear.
///
/// Every quantity is denominated in `asset()` and expressed in that asset's own
/// units. No value is scaled, normalised or converted, because a law that
/// depends on a conversion depends on whoever wrote it.
interface ICreditObservables {
    /// @notice The asset every other quantity here is denominated in.
    function asset() external view returns (address);

    /// @notice Assets the system holds and can account for right now.
    /// @dev What is held, not what is owed or promised. A system that has lent
    /// out its deposits holds less than its lenders may eventually claim, and
    /// that difference is the point of most of the corpus.
    function totalAssets() external view returns (uint256);

    /// @notice Principal plus accrued interest currently owed by borrowers.
    function totalDebt() external view returns (uint256);

    /// @notice What lenders may eventually withdraw, accrued to now.
    /// @dev Including claims already queued and not yet paid. A claim that has
    /// been recorded and not paid is still owed, and a system that drops it
    /// from this number is the subject of a law.
    function totalLenderClaims() external view returns (uint256);

    /// @notice Assets earmarked against recorded withdrawal claims.
    /// @dev Reserved assets are held by the system and unavailable to the
    /// borrower. A system with no withdrawal queue reports zero.
    function reservedAssets() external view returns (uint256);

    /// @notice Assets a borrower may currently take.
    /// @dev Never includes reserved assets. The separation is a law, so this
    /// function exists to let the law read both sides of it.
    function borrowableAssets() external view returns (uint256);

    /// @notice Fees accrued to a protocol or operator and not yet paid out.
    function accruedFees() external view returns (uint256);

    /// @notice The time the observations above describe.
    /// @dev Read from the target rather than from `block.timestamp` so a law
    /// can be checked against a recorded state as well as a live one.
    function observedAt() external view returns (uint256);
}
