"""Readers that turn something already on disk into a statement.

Four so far: a Foundry build, a dataset release, a grounded-agent release, and a
Lazarus state fixture. A
capture reads what a tool already wrote down rather than re-running it, so what ends
up in the statement is what was actually produced.

`tree.py` holds the directory walk the dataset and state-fixture captures share. It
is shared because it was written twice before, and the second copy of a path helper
in this package was where a traversal defect had already been found.
"""

from . import dataset, foundry, grounded_agent, state_fixture, tree

__all__ = ["dataset", "foundry", "grounded_agent", "state_fixture", "tree"]
