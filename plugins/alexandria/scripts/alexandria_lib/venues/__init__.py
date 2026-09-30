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

`OPENING_TOPICS` declares, per venue, the first topics of the only logs its
opening phase and `evidence_gaps` read: the proxy's `Upgraded(address)`
announcements for the single-proxy plan, the HooksFactory's `MarketDeployed`
logs for Wildcat V2, and none for Wildcat V1. A `log_walk.LogWalk` built with a
venue's topics keeps those logs as it checks every other one, and
`opening_logs` returns them. The walk matches the first topic alone, so for
Wildcat V2 it also keeps a `MarketDeployed`-topic log from any other declared
subject; `market_deploy_report` skips those, and they count toward the limit.
A release holding more than `log_walk.MAX_OPENING_LOGS` (`MAX_SUBJECTS` times
`MAX_EPOCHS`, 1,048,576) refuses by name, so what the opening phase is handed
stays bounded whatever the release's log count.
"""

from __future__ import annotations

from .. import log_walk
from ..errors import AlexandriaError
from ..interval import UPGRADED_TOPIC
from . import compound_v3, wildcat_v1, wildcat_v2

_MODULES = (compound_v3, wildcat_v1, wildcat_v2)

VENUES = {module.VENUE: module for module in _MODULES}

OPENING_TOPICS = {
    compound_v3.VENUE: (UPGRADED_TOPIC,),
    wildcat_v1.VENUE: (),
    wildcat_v2.VENUE: (wildcat_v2.MARKET_DEPLOYED_TOPIC,),
}


def opening_topics(venue: str) -> tuple:
    """The first topics of the logs one registered venue's opening phase and gaps read."""
    if venue not in OPENING_TOPICS or venue not in VENUES:
        raise AlexandriaError(
            f"the venue {str(venue)[:64]!r} declares no opening logs, so no walk can collect them"
        )
    return OPENING_TOPICS[venue]


def opening_logs(walk) -> list:
    """The opening logs a finished walk kept, in plan order, or a refusal above the limit."""
    if not walk.finished:
        raise AlexandriaError("the log walk has not finished, so its opening logs are not settled")
    if walk.opening_count > log_walk.MAX_OPENING_LOGS:
        raise AlexandriaError(
            f"the preserved logs hold {walk.opening_count} opening logs, above the "
            f"{log_walk.MAX_OPENING_LOGS}-log opening-log limit"
        )
    return list(walk.opening)
