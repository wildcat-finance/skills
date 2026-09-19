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
import hashlib
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
from tabularium_lib import verifier  # noqa: E402


JSONSCHEMA_ABSENT = "jsonschema is not installed"

SHIPPED_RELEASES = (
    "aave-v4-v0",
    "aave-v4-v1",
    "euler-v1-v0",
    "euler-v1-v1",
    "euler-v2-v0",
    "euler-v2-v1",
)

LEGACY_RELEASES = ("aave-v4-v0", "euler-v1-v0", "euler-v2-v0")

SUPERSEDING_RELEASES = ("aave-v4-v1", "euler-v1-v1", "euler-v2-v1")

# One row per supersession: the superseded directory, its successor, and the
# release identifier each one carries.
SUPERSESSION = (
    (
        "aave-v4-v0",
        "aave-v4-v1",
        "aave-v4-mainnet-credit-window-v0",
        "aave-v4-mainnet-credit-window-v1",
    ),
    (
        "euler-v1-v0",
        "euler-v1-v1",
        "euler-v1-borrow-block-14531589-v0",
        "euler-v1-borrow-block-14531589-v1",
    ),
    (
        "euler-v2-v0",
        "euler-v2-v1",
        "euler-v2-owner-activity-1786933919-v0",
        "euler-v2-owner-activity-1786933919-v1",
    ),
)

RELEASE_DATA_FILES = ("source.json", "capture.json", "events.jsonl", "coverage.json")

# The commit the three v0 releases were published at.  The design this step
# implements keeps those bytes where they are rather than migrating them, so
# the digests below are the thing that would break if a v1 build ever wrote
# into a v0 directory.  They are recorded here rather than read from Git so
# the assertion holds in a checkout with no history.
PUBLISHED_COMMIT = "1d131b98a78c888b571f302e5b4c899aa2e47caf"

PUBLISHED_V0_DIGESTS = {
    "aave-v4-v0/source.json":
        "1d88fdb5bca293995fd02e5a59f060d74541c80405e7bf1987544e5f334a8744",
    "aave-v4-v0/capture.json":
        "3cd14d1852561ec2aa9f498f37d6156b74ce321ec0965e81264925c4ba2e24ee",
    "aave-v4-v0/events.jsonl":
        "490d3f6399f84af8a81a5401b3cc92bf7ecfbe98a6bb02f07215b9099625ccf7",
    "aave-v4-v0/coverage.json":
        "b1538b633f1dfcfcc493afd033a52b4b199350b3a2221afb3c627a289d9de793",
    "euler-v1-v0/source.json":
        "1241cbed85189e79f9b0f8418e6838b297b4b661ad3e9f2d8a86903e22a6e790",
    "euler-v1-v0/capture.json":
        "59cd57ad5d8c54e1fd97cd4e62d37e31ac0d157ee5fa8f396c00be042c25041a",
    "euler-v1-v0/events.jsonl":
        "4034622f8b34147dead8a87d7c16b2a7c7197ed6417809fec41716a8028552aa",
    "euler-v1-v0/coverage.json":
        "ba4c5c127449b9be257069d302b442484fbd5d83023798eb9247aa893a45d301",
    "euler-v2-v0/source.json":
        "10f5c8e8242ef3745fbd69c4d8aed458f31b165fc4526f638e76df59a69a18cc",
    "euler-v2-v0/capture.json":
        "bcf2c85907243ccb40bc79234e30457d2e7e8b7dc3addc32d7301f804c772b9e",
    "euler-v2-v0/events.jsonl":
        "f563baa00c737384a3901f1bb3a7ae977f68f52a813eae9d02071eb2f4d0a5fe",
    "euler-v2-v0/coverage.json":
        "9892768315484ff05771e998f301b30daebd079a445e4226c9e55b12323c2a4b",
}

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


def release_digests(name):
    """The SHA-256 of each data file of one release directory, by file name."""
    directory = EXAMPLES / name
    return {
        file_name: hashlib.sha256((directory / file_name).read_bytes()).hexdigest()
        for file_name in RELEASE_DATA_FILES
    }


def release_published_digests(name):
    """The published digest of each data file of one release, where recorded."""
    return {
        file_name: PUBLISHED_V0_DIGESTS["%s/%s" % (name, file_name)]
        for file_name in RELEASE_DATA_FILES
        if "%s/%s" % (name, file_name) in PUBLISHED_V0_DIGESTS
    }


def document_observation(name):
    """One release's manifest and rows against the schema its version names.

    A release states its envelope in `schema_version`, so this validates it
    against that version's schema file rather than the current one.  A release
    with no rows is refused here rather than counted as agreement, because an
    empty ledger validates against anything.
    """
    manifest, rows = release_documents(name)
    version = manifest["schema_version"]
    manifest_fields = schema_refusal_fields(coverage_schema(version), manifest)
    schema = event_schema(version)
    adapter_module = release_v2.ADAPTERS[manifest["versions"]["adapter"]["name"]]
    refused = []
    for index, row in enumerate(rows, start=1):
        fields = schema_refusal_fields(schema, row)
        library_field = library_refusal_field(row, adapter_module, version, index)
        if fields or library_field is not None or row["schema_version"] != version:
            refused.append(
                {
                    "index": index,
                    "library_field": library_field,
                    "row_schema_version": row["schema_version"],
                    "schema_fields": fields,
                }
            )
    return {
        "manifest_fields": manifest_fields,
        "refused_rows": refused,
        "release": manifest["release"],
        "rows": len(rows),
        "schema_version": version,
        "source_directory": name,
        "agreed": bool(rows) and not manifest_fields and not refused,
    }


def verification_observation(name, expected_schema_version, expected_digests=None):
    """What `verify` did with one release, and whether its bytes still match.

    `verify` reads local bytes only.  `expected_digests` is the published
    digest of each data file where one is recorded; a release whose bytes have
    moved is a disagreement even when it verifies internally, which is the
    whole point of a superseding release.
    """
    observation = {
        "digest_drift": [],
        "release": None,
        "reason": None,
        "rows": None,
        "schema_version": None,
        "source_directory": name,
        "verified": False,
    }
    for file_name, digest in sorted((expected_digests or {}).items()):
        actual = hashlib.sha256((EXAMPLES / name / file_name).read_bytes()).hexdigest()
        if actual != digest:
            observation["digest_drift"].append(
                {"expected": digest, "file": file_name, "observed": actual}
            )
    try:
        report = verifier.verify(EXAMPLES / name / "coverage.json")
    except TabulariumError as exc:
        observation["reason"] = str(exc)
        observation["agreed"] = False
        return observation
    observation["release"] = report.release
    observation["rows"] = report.rows
    observation["schema_version"] = report.schema_version
    observation["verified"] = True
    observation["agreed"] = (
        report.schema_version == expected_schema_version
        and not observation["digest_drift"]
    )
    return observation
