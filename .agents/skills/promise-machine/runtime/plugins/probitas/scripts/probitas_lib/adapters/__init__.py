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


def adapter_source(config):
    """Which route backed this call: the network, or a fixture directory.

    An adapter does not decide this and does not need to know it. Whether a
    response arrived over the wire or out of a directory is a fact about how
    the operator invoked the run, so the caller stamps it in one place rather
    than four adapters each reading the same config key.
    """
    return "fixtures" if config.get("fixtures") else "live"


def run_adapter(venue_id, adapter, addresses, config):
    """Call an adapter and return (records, coverage), whatever it does."""
    source = adapter_source(config)
    try:
        records, coverage = adapter(addresses, config)
    except Exception as error:  # deliberately broad: see the module docstring
        return [], Coverage(
            venue=venue_id,
            status="error",
            note=f"{type(error).__name__}: {error}",
            records=0,
            source=source,
        )

    if coverage is None:
        raise ValueError(f"adapter for {venue_id} returned no coverage row")
    coverage.records = len(records)
    coverage.source = source
    return list(records), coverage


ADAPTER_ROUTES = ("live", "fixtures")

ARCHIVE_NOTE = "venue was not harvested into the selected Alexandria index"


def unchecked_coverage(venue, routes):
    """The coverage row for a venue no requested route answered for.

    Gate 2 in one function. An unimplemented venue and one whose credential the
    operator never supplied are different gaps, and the dossier says which.

    A run may ask for more than one route, and then "unconfigured" alone does
    not tell a reader whether an adapter went unrun or an archive simply never
    held this venue. The note names each requested route only when there is
    more than one; a single-route run keeps the sentence it has always
    printed, because those are the words a reader of an existing dossier
    already knows.
    """
    status = "unconfigured" if venue.implemented else "unimplemented"
    adapter = next((route for route in routes if route in ADAPTER_ROUTES), None)
    archive = "archive" in routes

    base = (
        f"adapter exists but was not run: {venue.auth} required "
        "and none was supplied"
    ) if venue.implemented else venue.note

    if adapter is not None and not archive:
        return Coverage(venue=venue.id, status=status, note=base, source="none")

    if adapter is None and archive:
        return Coverage(
            venue=venue.id,
            status=status,
            endpoint="Alexandria index",
            note=ARCHIVE_NOTE,
            source="none",
        )

    # More than one route was asked for, so the note says what each of them
    # did not do -- after the venue's own description rather than instead of
    # it. Gate 4 reads this note as the gap's reason, and a union dossier
    # whose negative space said only "no adapter ships for it" would tell a
    # reader less about the hole than a single-route one does.
    reasons = []
    if adapter is not None:
        reasons.append(
            f"no {adapter} adapter ran for it"
            if venue.implemented
            else "no adapter ships for it"
        )
    if archive:
        reasons.append(ARCHIVE_NOTE)
    return Coverage(
        venue=venue.id,
        status=status,
        note=f"{base} Not reached by this run: " + "; ".join(reasons) + ".",
        source="none",
    )
