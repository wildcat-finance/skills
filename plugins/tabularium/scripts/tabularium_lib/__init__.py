"""Standard-library implementation of the Tabularium prototype."""

from .core import TabulariumError


# Schema 2 stays readable because a published release is immutable under
# plugins/tabularium/docs/release-policy.md: the v0 ledgers keep their bytes,
# so the only way they can still verify is for this build to read schema 2.
SUPPORTED_EVENT_SCHEMAS = frozenset({2, 3})
CURRENT_EVENT_SCHEMA = 3


def check_event_schema(version, where):
    """Refuse a canonical event schema version this build does not handle."""
    if isinstance(version, bool) or not isinstance(version, int) or version not in SUPPORTED_EVENT_SCHEMAS:
        raise TabulariumError(
            "unsupported %s %r; this build reads %s"
            % (where, version, ", ".join(str(item) for item in sorted(SUPPORTED_EVENT_SCHEMAS)))
        )
    return version
