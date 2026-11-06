"""The Compound v3 (Comet) venue: registry validation and its coverage gap.

`validate_registry` is the unedited function `compound_registry.py` already
defines, re-exported rather than wrapped, so this venue's format check and
its pinned-byte check stay exactly what they were before dispatch existed.
`gaps` is the Compound-specific coverage-gap sentence `usdc_interval.py`
computed inline before this step; its wording is unchanged word for word.
"""

from __future__ import annotations

from ..compound_registry import validate_registry

VENUE = "compound-v3"
# The collector's own EIP-1967 opening reads and upgrade-log epochs serve this
# venue, so it supplies no `opening_phase` of its own.
EPOCH_MODEL = "eip1967-proxy"


def gaps(registry, plan=None) -> list[str]:
    """The one coverage gap a Compound registry component always carries."""
    others = [
        f"{entry['network']}/{entry['market']}"
        for entry in registry["entries"]
        if not (entry["network"] == "mainnet" and entry["market"] == "usdc")
    ]
    return [
        f"{len(others)} of the {len(registry['entries'])} registry entries at the pin "
        "were not collected; this release covers the Ethereum USDC Comet only"
    ]


def evidence_gaps(plan, registry, logs, first_code=None) -> list[str]:
    """This venue adds nothing to an evidence scope's gaps; its releases are unchanged."""
    return []
