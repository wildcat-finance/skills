"""The one table the interval collector dispatches a plan's venue through.

Each module below names its own venue in a `VENUE` constant and its epoch
model in `EPOCH_MODEL`, and supplies `validate_registry`, `gaps` and
`evidence_gaps` for that venue's deployment registry. A venue whose epoch
model is not the collector's own `eip1967-proxy` also supplies
`opening_phase`, the opening reads and epoch derivation it owns. That phase
may also supply `preliminary_reads`, the opening reads the collector makes
before any shard, and it supplies `first_code_rows`, which `evidence_gaps`
takes as its fourth argument under a subject-set plan. `VENUES`
is built from those constants rather than restated as a second list, so a
venue cannot be registered in one place and left out of another the way
`plugins/tabularium/scripts/tabularium.py`'s argparse `choices` tuple drifted
from `tabularium_lib/release_v2.py`'s adapter dict: add a module to
`_MODULES` and its own `VENUE` name is the only place its identity is
spelled.
"""

from __future__ import annotations

from . import compound_v3, wildcat_v2

_MODULES = (compound_v3, wildcat_v2)

VENUES = {module.VENUE: module for module in _MODULES}
