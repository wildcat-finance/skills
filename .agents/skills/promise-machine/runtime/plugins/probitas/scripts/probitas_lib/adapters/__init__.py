"""The adapter protocol, and the rule that keeps a failure visible.

An adapter is a callable:

    adapter(addresses, config) -> (records, coverage)

`addresses` is a mapping of lowercase address to provenance tier. `config` is a
mapping the operator supplied: endpoints, credentials, block ranges. It returns
a list of `Record` and one `Coverage` row.

`run_adapter` wraps the call so that an adapter which raises still produces a
coverage row, with status `error` and the reason attached. An adapter that
vanishes on failure would leave a venue silently missing from the table, and
a missing venue reads to a lender exactly like a venue that came back clean.
"""

from ..evidence import Coverage


def run_adapter(venue_id, adapter, addresses, config):
    """Call an adapter and return (records, coverage), whatever it does."""
    try:
        records, coverage = adapter(addresses, config)
    except Exception as error:  # deliberately broad: see the module docstring
        return [], Coverage(
            venue=venue_id,
            status="error",
            note=f"{type(error).__name__}: {error}",
            records=0,
        )

    if coverage is None:
        raise ValueError(f"adapter for {venue_id} returned no coverage row")
    coverage.records = len(records)
    return list(records), coverage


def unchecked_coverage(venue):
    """The coverage row for a venue nobody checked.

    Gate 2 in one function. An unimplemented venue and one whose credential the
    operator never supplied are different gaps, and the dossier says which.
    """
    if venue.implemented:
        return Coverage(
            venue=venue.id,
            status="unconfigured",
            note=(
                f"adapter exists but was not run: {venue.auth} required "
                "and none was supplied"
            ),
        )
    return Coverage(
        venue=venue.id,
        status="unimplemented",
        note=venue.note,
    )
