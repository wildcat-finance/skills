// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "./ICreditObservables.sol";

/// @title One executable law.
/// @notice A law judges a state and says what it decided. It does not revert
/// to signal a failure, and the reason is the harness rather than taste.
///
/// A stateful campaign runs with `fail_on_revert = false`, because a credit
/// system reverts constantly and correctly: a withdrawal past the queue, a
/// borrow past the reserve, a repayment of more than is owed. Under that
/// setting a revert carries no verdict, so a law using `require` to mean
/// "violated" would report nothing at all and be counted as silence. Silence
/// read as assent is what this corpus exists to prevent. A law therefore
/// returns `false` to mean violated, and never reverts to mean it.
///
/// The converse is a limit rather than a guarantee, and worth stating exactly.
/// If the target reverts on a read, the law reverts with it. That is neither a
/// violation nor a pass: the state could not be observed, the law has no
/// opinion, and the harness counts a revert. What an unobservable state means
/// is the adapter's decision, not this contract's.
///
/// `detail` is for the reader who finds the failure six months later. It says
/// which quantities were compared and what they were, because a counterexample
/// without the numbers is a bug report nobody can act on.
abstract contract Law {
    /// @notice Stable identifier, matching this law's entry in the catalogue.
    /// @dev The catalogue carries the statement, applicability and specimen;
    /// this ties the executing component to that entry. A test fails when one
    /// exists without the other, so a law cannot be documented without being
    /// executable or executable without being documented.
    function id() external pure virtual returns (string memory);

    /// @notice The law in one sentence, as a reader would state it.
    function statement() external pure virtual returns (string memory);

    /// @notice Judge one observed state.
    /// @param target The system under test, or an adapter over it.
    /// @return held True when the law holds for this state.
    /// @return detail What was compared, and what the values were.
    function check(ICreditObservables target)
        external
        view
        virtual
        returns (bool held, string memory detail);
}
