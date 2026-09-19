"""Shared paths, fixture loading and validator parity for Tabularium tests.

The parity helpers here are the single description of what "both validators
refuse the same field" means.  `test_schemas.py` and
`prove_schema_v3.py` both read it from here, so the suite and the design
reporter cannot drift apart and disagree about a fixture.

`jsonschema` is optional.  It is imported through `import_jsonschema`, once
per call and never at module import, so a caller can hide the module and see
the same refusal an uninstalled host would produce.
"""

import copy
import json
from pathlib import Path
import re
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
SCHEMAS = PLUGIN_ROOT / "schemas"
EXAMPLES = PLUGIN_ROOT / "examples"
SCHEMA_V3_FIXTURES = FIXTURES / "schema-v3"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from tabularium_lib import CURRENT_EVENT_SCHEMA, TabulariumError  # noqa: E402
from tabularium_lib import release_v2  # noqa: E402


JSONSCHEMA_ABSENT = "jsonschema is not installed"

SHIPPED_RELEASES = ("aave-v4-v0", "euler-v1-v0", "euler-v2-v0")

REJECTION_FIXTURES = (
    ("unknown-value", "provenance.mapping_rule"),
    ("wrong-version", "schema_version"),
    ("malformed-provenance", "provenance.source_selector"),
)

_REQUIRED = re.compile(r"^'(?P<name>[^']+)' is a required property$")
_UNEXPECTED = re.compile(r"'(?P<name>[^']+)'[^()]*was unexpected")
_NAMED_FIELD = re.compile(r"\bfield (?P<name>[A-Za-z_][A-Za-z0-9_.]*)")


class JsonschemaAbsent(Exception):
    """The optional `jsonschema` package is not importable."""


def import_jsonschema():
    """Return the `jsonschema` module, or refuse with the one named reason."""
    try:
        import jsonschema
    except ImportError:
        raise JsonschemaAbsent(JSONSCHEMA_ABSENT) from None
    return jsonschema


def minimal_snapshot():
    value = json.loads((FIXTURES / "minimal-snapshot.json").read_text())
    return copy.deepcopy(value)


def load_schema(name):
    """One versioned schema document from the plugin's `schemas/` directory."""
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def event_schema(version):
    return load_schema("canonical-event-v%d.json" % version)


def coverage_schema(version):
    return load_schema("coverage-manifest-v%d.json" % version)


def load_rejection_fixture(name):
    """One committed rejection fixture, read as data and never executed."""
    path = SCHEMA_V3_FIXTURES / (name + ".json")
    return json.loads(path.read_text(encoding="utf-8"))


def release_documents(name):
    """The manifest and canonical rows of one shipped release directory."""
    directory = EXAMPLES / name
    manifest = json.loads((directory / "coverage.json").read_text(encoding="utf-8"))
    rows = []
    for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines():
        if line:
            rows.append(json.loads(line))
    return manifest, rows


def _error_field(error):
    """The dotted field one validation error names, missing key included."""
    parts = [str(part) for part in error.absolute_path]
    if error.validator == "required":
        match = _REQUIRED.match(error.message)
        if match is not None:
            parts.append(match.group("name"))
    elif error.validator == "additionalProperties":
        match = _UNEXPECTED.search(error.message)
        if match is not None:
            parts.append(match.group("name"))
    return ".".join(parts)


def _leaves(errors):
    """Flatten `oneOf` and `anyOf` errors down to the ones naming a field."""
    flattened = []
    for error in errors:
        if error.context:
            flattened.extend(_leaves(error.context))
        else:
            flattened.append(error)
    return flattened


def schema_refusal_fields(schema, document):
    """The fields `jsonschema` names when refusing one document.

    An empty list means the document validated.  Errors raised by the schema's
    own keywords are preferred; only where every error comes from a `oneOf` or
    `anyOf` branch does this descend into the branch errors, because a branch
    that failed on `venue` says nothing about the document's real defect.
    """
    jsonschema = import_jsonschema()
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = list(validator.iter_errors(document))
    direct = [error for error in errors if not error.context]
    chosen = direct if direct else _leaves(errors)
    return sorted({_error_field(error) for error in chosen})


def library_refusal_field(row, adapter_module, schema_version, index=1):
    """The field `validate_event_row` names, or None where it admits the row."""
    try:
        release_v2.validate_event_row(
            copy.deepcopy(row), adapter_module, schema_version, index
        )
    except TabulariumError as exc:
        match = _NAMED_FIELD.search(str(exc))
        if match is None:
            return str(exc)
        return match.group("name")
    return None


def parity_observation(row, expected_field, schema_version=CURRENT_EVENT_SCHEMA):
    """Record what each validator did with one row, and whether they agreed.

    Agreement means both refused and both named `expected_field` and nothing
    else.  A row only one validator refuses is a disagreement, never a pass.
    """
    adapter_module = release_v2.ADAPTERS[row["venue"]]
    schema_fields = schema_refusal_fields(event_schema(schema_version), row)
    library_field = library_refusal_field(row, adapter_module, schema_version)
    return {
        "expected_field": expected_field,
        "library_field": library_field,
        "schema_fields": schema_fields,
        "schema_version": schema_version,
        "venue": row["venue"],
        "agreed": schema_fields == [expected_field] and library_field == expected_field,
    }


def parity_disagreement(observation):
    """One line saying how the two validators differed, for a refusal message."""
    return (
        "jsonschema named %s and validate_event_row named %r; the fixture "
        "names %r" % (
            observation["schema_fields"],
            observation["library_field"],
            observation["expected_field"],
        )
    )
