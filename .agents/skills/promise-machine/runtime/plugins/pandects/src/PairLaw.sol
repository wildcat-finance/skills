// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Observation} from "./Observation.sol";

/// @title One executable law over a pair of observations.
/// @notice The same contract as `Law` in every respect that matters -- it
/// judges rather than reverts, it carries an id and a statement, and it
/// returns the reason with the verdict. It differs in arity, and only because
/// the facts differ in arity.
///
/// Conservation is a fact about one state: the sums agree or they do not, and
/// no history is needed to say which. Accrual is not. "Debt falls only against
/// payment" cannot be violated by any single state, however wrong that state
/// is, because the violation is in the transition. Bending the one-state shape
/// to cover it would mean a law holding its own history in storage, which
/// makes the law stateful, order-dependent and impossible to point at a
/// recorded state after the fact.
///
/// So there are two shapes and there is no third. Both are checked by the same
/// tooling, both appear in the same catalogue, and a reader has to know which
/// one a law is only when they call it.
///
/// The two observations are not always a before and an after. Three of these
/// laws compare a system with its own past; one compares two systems advanced
/// differently over the same span. Each says which it means in its
/// applicability.
///
/// Handed a pair it cannot judge, a law follows one rule, and it is worth
/// stating here once rather than three times in three files. Ask whose mistake
/// the pair is. A pair that spans real time, or that shows a system somewhere
/// this law says nothing about, is a state of the world: hold, and say why.
/// A pair nobody could have meant -- two runs that never reached the same
/// moment, a queue law handed observations with no queue in them -- is a
/// mistake by whoever built it: refuse, and say why. Holding there would
/// report a comparison nobody made, which is the silence this corpus exists to
/// prevent, arriving from the harness instead of from the system.
abstract contract PairLaw {
    /// @notice Stable identifier, matching this law's entry in the catalogue.
    function id() external pure virtual returns (string memory);

    /// @notice The law in one sentence, as a reader would state it.
    function statement() external pure virtual returns (string memory);

    /// @notice Judge a pair of observations.
    /// @param earlier The first observation.
    /// @param later The second.
    /// @return held True when the law holds for this pair.
    /// @return detail What was compared, and what the values were.
    /// @dev `view` rather than `pure`, because a law may carry a bound. Only
    /// one does, and the alternative was a second entry point holding the real
    /// law while `check` answered a different question with a default bound.
    /// A law with two doors, one of which is wrong, is worse than a law that
    /// declares it might read something.
    function check(Observation memory earlier, Observation memory later)
        external
        view
        virtual
        returns (bool held, string memory detail);
}
