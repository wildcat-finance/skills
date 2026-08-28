"""Predicates, registered into the default registry when this package loads.

Importing for a side effect is usually a smell. Here it is the mechanism: a
predicate is a module that declares its own shape and checks, and registering
on import is what makes `ariadne predicates` and `verify` see it without a
table somebody has to remember to update.
"""

from .. import registry
from . import dataset, solidity_release, state_fixture

state_fixture_v2 = state_fixture.V2

registry.DEFAULT.register(solidity_release)
registry.DEFAULT.register(dataset)
registry.DEFAULT.register(state_fixture)
registry.DEFAULT.register(state_fixture_v2)

__all__ = ["dataset", "solidity_release", "state_fixture", "state_fixture_v2"]
