"""Compare two gate-checkable Probitas evidence files without widening them.

The caller assigns the roles ``prior`` and ``current``.  Evidence schema 2 does
not establish when a collection happened, so this module reports file
differences and never turns them into a claim that activity happened between
two times.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from . import formatting, gates, registry, render, sanitise, statement
from .evidence import (
    COVERAGE_SOURCES,
    COVERAGE_STATUSES,
    PROVENANCE_TIERS,
    Coverage,
    Evidence,
    Gap,
    Record,
)


DELTA_SCHEMA = "probitas-evidence-delta/v1"
# A pretty-printed 20,000-record collector output is already about 9 MiB, and
# the shipped Euler v1 adapter permits 50,000 logs.  Keep enough room for that
# authored envelope; record and JSON-tree limits remain the tighter controls.
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
MAX_JSON_DEPTH = 32
# Fifty thousand full Euler-style records can carry more than 1.1 million
# scalar/container nodes while remaining below the byte ceiling.
MAX_JSON_ITEMS = 2_000_000
MAX_TOKEN_DECIMALS = 255
# Collection itself has no smaller subject-count boundary.  The byte and tree
# ceilings necessarily stop this list first, so comparison does not invent an
# incompatible 256-address schema for otherwise gate-checkable collector output.
MAX_ADDRESSES = MAX_JSON_ITEMS
MAX_RECORDS = 50_000
MAX_COVERAGE_ROWS = 256
MAX_GAPS = 2_048


class DeltaError(ValueError):
    """An evidence input is malformed, unsafe, or not comparable."""


class DeltaGateError(DeltaError):
    """One input cannot produce a dossier that passes all five gates."""


def read_evidence(path, role):
    """Read one regular evidence file once, under the comparison size cap."""
    if os.fspath(path) == "-":
        raise DeltaError(f"{role} evidence must name a file, not stdin")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        handle = os.fdopen(descriptor, "rb")
    except (OSError, ValueError):
        os.close(descriptor)
        raise
    with handle:
        status = os.fstat(handle.fileno())
        if not stat.S_ISREG(status.st_mode):
            raise DeltaError(f"{role} evidence is not a regular file")
        if status.st_size > MAX_EVIDENCE_BYTES:
            raise DeltaError(
                f"{role} evidence exceeds the {MAX_EVIDENCE_BYTES}-byte limit"
            )
        data = handle.read(MAX_EVIDENCE_BYTES + 1)
    if len(data) > MAX_EVIDENCE_BYTES:
        raise DeltaError(
            f"{role} evidence exceeds the {MAX_EVIDENCE_BYTES}-byte limit"
        )
    return data


def compare(prior_bytes, current_bytes, prior_name="prior", current_name="current"):
    """Return one deterministic, source-preserving comparison object.

    Exit-code policy belongs to the CLI: a :class:`DeltaGateError` maps to 1;
    every other malformed or non-comparable input maps to 2.
    """
    prior, prior_gates = _checked_side(prior_bytes, prior_name)
    current, current_gates = _checked_side(current_bytes, current_name)

    if prior["subject"]["entity"] != current["subject"]["entity"]:
        raise DeltaError("prior and current evidence name different entities")
    if prior["subject"]["addresses"] != current["subject"]["addresses"]:
        raise DeltaError(
            "prior and current evidence use different address or provenance scopes"
        )

    return {
        "schema": DELTA_SCHEMA,
        "tool": {"name": "probitas", "version": statement.skill_version()},
        "subject": prior["subject"],
        "inputs": {
            "prior": _input_binding(prior_bytes, prior, prior_gates),
            "current": _input_binding(current_bytes, current, current_gates),
        },
        "coverage": _coverage_delta(prior["coverage"], current["coverage"]),
        "gaps": _gap_delta(prior["gaps"], current["gaps"]),
        "records": _record_delta(prior["records"], current["records"]),
        "limitations": {
            "ordering": "operator-designated",
            "chronology_established": False,
            "causation_established": False,
            "newly_present_establishes_new_activity": False,
            "no_longer_reproduced_establishes_reversal_or_resolution": False,
            "closed_gap_establishes_clean_history": False,
            "completeness_established": False,
            "credit_score_produced": False,
            "underwriting_decision_produced": False,
            "wildcat_decision_produced": False,
            "unchanged_records_included": False,
            "replaces_current_dossier": False,
        },
    }


def to_json(comparison):
    """Serialise a comparison deterministically for automation or replay."""
    return json.dumps(
        comparison,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ) + "\n"


def render_markdown(comparison):
    """Render the human Borrower Change Report from one comparison object."""
    entity = _display(comparison["subject"]["entity"], max_length=120)
    prior = comparison["inputs"]["prior"]
    current = comparison["inputs"]["current"]
    on_record = comparison["records"]["on_record"]
    inferred = comparison["records"]["inferred"]

    lines = [
        f"# Borrower change report: {entity}",
        "",
        "`prior` and `current` are roles chosen by the operator. The evidence "
        "does not independently establish chronological order.",
        "The comparison does not independently establish causation.",
        "",
        "## Input checks",
        "",
        "| Role | Run | Collected at | SHA-256 | Bytes | Generated dossier gates |",
        "| --- | --- | --- | --- | ---: | --- |",
        _input_row("prior", prior),
        _input_row("current", current),
        "",
        "### Address scope",
        "",
        _address_scope(comparison["subject"]["addresses"]),
        "",
        "## Coverage changes",
        "",
        _coverage_markdown(comparison["coverage"]),
        "",
        "## Gaps",
        "",
        _gaps_markdown(comparison["gaps"]),
        "",
        "## Record differences",
        "",
        _record_sections(on_record),
        "",
        "## Interpretation boundary",
        "",
        "A newly present record may be a backfill or wider coverage, not new "
        "activity. A record no longer reproduced may be a source regression, "
        "not a reversed event. It does not establish debt resolution. A closed "
        "gap means only that current evidence no longer reports it. Unchanged "
        "records are omitted, so this report does not replace the current "
        "dossier. This report makes no score, completeness claim, underwriting "
        "decision, or Wildcat verdict.",
        "",
        "## Addresses not declared",
        "",
        _record_sections(inferred),
        "",
    ]
    return "\n".join(lines)


def write_output(path, body):
    """Atomically replace the requested output with UTF-8 report bytes."""
    output = Path(path)
    data = body.encode("utf-8")
    descriptor = None
    temporary = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{output.name}.tmp-", dir=output.parent
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def output_aliases_input(output, *inputs):
    """Return true when an output path would replace either evidence input."""
    output = os.fspath(output)
    if output == "-":
        return False
    output_real = os.path.realpath(os.path.abspath(output))
    for source in inputs:
        source_real = os.path.realpath(os.path.abspath(os.fspath(source)))
        if output_real == source_real:
            return True
        try:
            if os.path.exists(output) and os.path.samefile(output, source):
                return True
        except OSError:
            continue
    return False


def _decode_strict(data, name):
    if not isinstance(data, bytes):
        raise DeltaError(f"{name} evidence must be bytes")
    if len(data) > MAX_EVIDENCE_BYTES:
        raise DeltaError(f"{name} evidence exceeds the {MAX_EVIDENCE_BYTES}-byte limit")

    def no_duplicates(pairs):
        found = {}
        for key, value in pairs:
            if key in found:
                raise DeltaError(f"{name} evidence contains a duplicate JSON key")
            found[key] = value
        return found

    try:
        decoded = data.decode("utf-8")
        payload = json.loads(decoded, object_pairs_hook=no_duplicates)
    except DeltaError:
        raise
    except UnicodeDecodeError as error:
        raise DeltaError(f"{name} evidence is not UTF-8") from error
    except json.JSONDecodeError as error:
        raise DeltaError(f"{name} evidence is not valid JSON") from error
    except RecursionError as error:
        raise DeltaError(f"{name} evidence exceeds the JSON depth limit") from error
    except ValueError as error:
        raise DeltaError(f"{name} evidence contains an invalid JSON value") from error
    _bounded_tree(payload, name)
    _reject_surrogates(payload, name)
    return payload


def _bounded_tree(value, name):
    stack = [(value, 0)]
    visited = 0
    while stack:
        node, depth = stack.pop()
        visited += 1
        if visited > MAX_JSON_ITEMS:
            raise DeltaError(f"{name} evidence exceeds the JSON item limit")
        if depth > MAX_JSON_DEPTH:
            raise DeltaError(f"{name} evidence exceeds the JSON depth limit")
        if isinstance(node, dict):
            stack.extend((item, depth + 1) for item in node.values())
        elif isinstance(node, list):
            stack.extend((item, depth + 1) for item in node)


def _reject_surrogates(value, name):
    stack = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in node):
                raise DeltaError(f"{name} evidence contains a Unicode surrogate")
        elif isinstance(node, dict):
            stack.extend(node.keys())
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)


def _checked_side(data, name):
    parsed = _decode_strict(data, name)
    canonical = _rehydrate(parsed, name)
    try:
        document = render.render(canonical)
        results = gates.check(document, canonical)
    except (KeyError, OSError, OverflowError, TypeError, ValueError) as error:
        raise DeltaError(f"{name} evidence cannot be rendered safely") from error
    failed = [result for result in results if not result.passed]
    if failed:
        detail = ", ".join(
            f"gate {result.number} ({result.name})" for result in failed
        )
        raise DeltaGateError(f"{name} evidence failed its generated dossier: {detail}")
    return canonical, results


def _rehydrate(payload, name):
    _keys(payload, {"schema", "run", "subject", "records", "coverage", "gaps"}, name)
    if type(payload.get("schema")) is not int or payload["schema"] != 2:
        raise DeltaError(f"{name} is not a schema 2 Probitas evidence file")

    run = _mapping(payload["run"], f"{name} run")
    _keys(run, {"id", "collected_at"}, f"{name} run")
    if run["id"] is not None and not isinstance(run["id"], str):
        raise DeltaError(f"{name} run id must be text or null")
    if run["collected_at"] is not None and not isinstance(
        run["collected_at"], (str, int)
    ):
        raise DeltaError(f"{name} collected_at must be text, an integer, or null")
    if isinstance(run["collected_at"], bool):
        raise DeltaError(f"{name} collected_at must not be a boolean")

    subject = _mapping(payload["subject"], f"{name} subject")
    _keys(subject, {"entity", "addresses"}, f"{name} subject")
    entity = subject["entity"]
    if not isinstance(entity, str) or not entity.strip():
        raise DeltaError(f"{name} subject entity is invalid")
    if len(entity) > 120 or sanitise.strip_controls(entity) != entity:
        raise DeltaError(f"{name} subject entity is not bounded safe text")

    addresses = []
    seen_addresses = set()
    address_items = _bounded_list(
        subject["addresses"], f"{name} address", MAX_ADDRESSES
    )
    for index, item in enumerate(address_items):
        label = f"{name} address {index}"
        item = _mapping(item, label)
        _keys(item, {"address", "provenance"}, label)
        try:
            address = sanitise.address(item["address"])
        except ValueError as error:
            raise DeltaError(f"{label} is invalid") from error
        if address != item["address"]:
            raise DeltaError(f"{label} is not canonical lowercase text")
        provenance = item["provenance"]
        if provenance not in PROVENANCE_TIERS:
            raise DeltaError(f"{label} has an unknown provenance tier")
        if address in seen_addresses:
            raise DeltaError(f"{name} subject repeats an address")
        seen_addresses.add(address)
        addresses.append((address, provenance))

    try:
        rebuilt = Evidence(
            entity=entity,
            addresses=addresses,
            run_id=run["id"],
            collected_at=run["collected_at"],
        )
    except (TypeError, ValueError) as error:
        raise DeltaError(f"{name} subject is invalid") from error
    if rebuilt.entity != entity:
        raise DeltaError(f"{name} subject entity is not canonical text")

    record_keys = {
        "venue", "address", "provenance", "claim", "values", "source",
        "source_kind", "observed_at", "block",
    }
    required_record_keys = record_keys - {"observed_at", "block"}
    known_venues = {venue.id for venue in registry.all_venues()}
    record_items = _bounded_list(payload["records"], f"{name} record", MAX_RECORDS)
    for index, item in enumerate(record_items):
        label = f"{name} record {index}"
        item = _mapping(item, label)
        _keys(item, record_keys, label, optional={"observed_at", "block"})
        if not required_record_keys.issubset(item):
            raise DeltaError(f"{label} is missing a required field")
        if not isinstance(item["venue"], str):
            raise DeltaError(f"{label} venue must be text")
        if item["venue"] not in known_venues:
            raise DeltaError(f"{label} names an unknown venue")
        _optional_timestamp(item.get("observed_at"), f"{label} observed_at")
        _optional_nonnegative_integer(item.get("block"), f"{label} block")
        try:
            record = Record(
                venue=item["venue"],
                address=item["address"],
                provenance=item["provenance"],
                claim=item["claim"],
                values=item["values"],
                source=item["source"],
                observed_at=item.get("observed_at"),
                block=item.get("block"),
            )
        except (TypeError, ValueError) as error:
            raise DeltaError(f"{label} is invalid") from error
        if item.get("source_kind") != record.source_kind:
            raise DeltaError(f"{label} source kind disagrees with its citation")
        if rebuilt.addresses.get(record.address) != record.provenance:
            raise DeltaError(f"{label} provenance disagrees with its subject address")
        if item != record.to_dict():
            raise DeltaError(f"{label} is not canonical evidence")
        _validate_render_bounds(record, label)
        rebuilt.add_record(record)

    coverage_keys = {
        "venue", "status", "source", "endpoint", "block_range", "note",
        "records", "releases",
    }
    seen_coverage = set()
    coverage_items = _bounded_list(
        payload["coverage"], f"{name} coverage row", MAX_COVERAGE_ROWS
    )
    for index, item in enumerate(coverage_items):
        label = f"{name} coverage row {index}"
        item = _mapping(item, label)
        _keys(item, coverage_keys, label)
        if not isinstance(item["venue"], str):
            raise DeltaError(f"{label} venue must be text")
        if item["venue"] not in known_venues:
            raise DeltaError(f"{label} names an unknown venue")
        if item["status"] not in COVERAGE_STATUSES:
            raise DeltaError(f"{label} has an unknown status")
        if item["source"] not in COVERAGE_SOURCES:
            raise DeltaError(f"{label} has an unknown source route")
        if isinstance(item["records"], bool) or not isinstance(item["records"], int):
            raise DeltaError(f"{label} record count is not an integer")
        if item["records"] < 0:
            raise DeltaError(f"{label} record count is negative")
        for field in ("endpoint", "block_range", "note", "releases"):
            if item[field] is not None and not isinstance(item[field], str):
                raise DeltaError(f"{label} {field} must be text or null")
        try:
            coverage = Coverage(**item)
        except (TypeError, ValueError) as error:
            raise DeltaError(f"{label} is invalid") from error
        if item != coverage.to_dict():
            raise DeltaError(f"{label} is not canonical evidence")
        key = (coverage.venue, coverage.source)
        if key in seen_coverage:
            raise DeltaError(f"{name} coverage repeats a venue and source route")
        seen_coverage.add(key)
        rebuilt.add_coverage(coverage)

    gap_subjects = set()
    gap_items = _bounded_list(payload["gaps"], f"{name} gap", MAX_GAPS)
    for index, item in enumerate(gap_items):
        label = f"{name} gap {index}"
        item = _mapping(item, label)
        _keys(item, {"subject", "reason"}, label)
        try:
            gap = Gap(**item)
        except (TypeError, ValueError) as error:
            raise DeltaError(f"{label} is invalid") from error
        if item != gap.to_dict():
            raise DeltaError(f"{label} is not canonical evidence")
        if gap.subject in gap_subjects:
            raise DeltaError(f"{name} repeats a gap subject")
        gap_subjects.add(gap.subject)
        rebuilt.add_gap(gap)

    observed = {
        row.venue
        for row in rebuilt.coverage
        if row.status in ("checked", "empty")
    }
    required_gaps = {
        f"{row.venue} borrowing history"
        for row in rebuilt.coverage
        if row.status == "error"
        or (
            row.status in ("unimplemented", "unconfigured")
            and row.venue not in observed
        )
    }
    missing_gaps = sorted(required_gaps - gap_subjects)
    if missing_gaps:
        raise DeltaError(f"{name} coverage failure has no negative-space gap")

    return rebuilt.to_dict()


def _keys(value, expected, label, optional=frozenset()):
    value = _mapping(value, label)
    actual = set(value)
    required = set(expected) - set(optional)
    if not required.issubset(actual) or not actual.issubset(set(expected)):
        raise DeltaError(f"{label} has missing or unexpected fields")


def _mapping(value, label):
    if not isinstance(value, dict):
        raise DeltaError(f"{label} is not an object")
    return value


def _list(value, label):
    if not isinstance(value, list):
        raise DeltaError(f"{label} is not a list")
    return value


def _bounded_list(value, label, limit):
    values = _list(value, f"{label}s")
    if len(values) > limit:
        raise DeltaError(f"{label} count exceeds the {limit} limit")
    return values


def _optional_nonnegative_integer(value, label):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DeltaError(f"{label} is not a non-negative integer")


def _optional_timestamp(value, label):
    _optional_nonnegative_integer(value, label)
    if value is None:
        return
    try:
        formatting.timestamp(value)
    except (OSError, OverflowError, ValueError) as error:
        raise DeltaError(f"{label} is outside the supported date range") from error


def _validate_render_bounds(record, label):
    raw = record.values.get("token_decimals")
    if raw is None:
        return
    if not isinstance(raw, str) or not raw.isascii() or not raw.isdigit():
        raise DeltaError(f"{label} token decimals are not an unsigned integer")
    if int(raw) > MAX_TOKEN_DECIMALS:
        raise DeltaError(
            f"{label} token decimals exceed the {MAX_TOKEN_DECIMALS} limit"
        )


def _input_binding(data, payload, results):
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "run": payload["run"],
        "gates": [
            {
                "number": result.number,
                "name": result.name,
                "passed": result.passed,
                "detail": result.detail,
            }
            for result in results
        ],
    }


def _fingerprint(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record_anchor(record):
    return (
        record["venue"],
        record["address"],
        record["claim"],
        record["source"],
    )


def _cancel_exact(prior, current):
    prior_count = Counter(_fingerprint(record) for record in prior)
    current_count = Counter(_fingerprint(record) for record in current)
    values = {
        _fingerprint(record): record
        for record in list(prior) + list(current)
    }
    prior_left = []
    current_left = []
    for identity in sorted(set(prior_count) | set(current_count)):
        common = min(prior_count[identity], current_count[identity])
        prior_left.extend([values[identity]] * (prior_count[identity] - common))
        current_left.extend([values[identity]] * (current_count[identity] - common))
    return prior_left, current_left


def _record_delta(prior, current):
    prior_left, current_left = _cancel_exact(prior, current)
    prior_by_anchor = defaultdict(list)
    current_by_anchor = defaultdict(list)
    for record in prior_left:
        prior_by_anchor[_record_anchor(record)].append(record)
    for record in current_left:
        current_by_anchor[_record_anchor(record)].append(record)

    raw = {
        "newly_present": [],
        "no_longer_reproduced": [],
        "revised": [],
        "observation_refreshed": [],
    }
    for anchor in sorted(set(prior_by_anchor) | set(current_by_anchor)):
        before = sorted(prior_by_anchor.get(anchor, []), key=_fingerprint)
        after = sorted(current_by_anchor.get(anchor, []), key=_fingerprint)
        if len(before) == 1 and len(after) == 1:
            pair = {"prior": before[0], "current": after[0]}
            if _without_observation_time(before[0]) == _without_observation_time(after[0]):
                raw["observation_refreshed"].append(pair)
            else:
                raw["revised"].append(pair)
            continue
        raw["no_longer_reproduced"].extend(before)
        raw["newly_present"].extend(after)

    output = {
        "on_record": {key: [] for key in raw},
        "inferred": {key: [] for key in raw},
    }
    for category, entries in raw.items():
        for entry in entries:
            record = entry["current"] if isinstance(entry, dict) and "current" in entry else entry
            tier = "inferred" if record["provenance"] == "inferred" else "on_record"
            output[tier][category].append(entry)
    return output


def _without_observation_time(record):
    return {key: value for key, value in record.items() if key != "observed_at"}


def _coverage_delta(prior, current):
    prior_rows = {(row["venue"], row["source"]): row for row in prior}
    current_rows = {(row["venue"], row["source"]): row for row in current}
    added = []
    removed = []
    changed = []
    for key in sorted(set(prior_rows) | set(current_rows)):
        before = prior_rows.get(key)
        after = current_rows.get(key)
        if before is None:
            added.append(after)
        elif after is None:
            removed.append(before)
        elif before != after:
            changed.append({"prior": before, "current": after})
    return {"added": added, "removed": removed, "changed": changed}


def _gap_delta(prior, current):
    prior_gaps = {gap["subject"]: gap for gap in prior}
    current_gaps = {gap["subject"]: gap for gap in current}
    opened = []
    closed = []
    reason_changed = []
    unchanged = []
    for subject in sorted(set(prior_gaps) | set(current_gaps)):
        before = prior_gaps.get(subject)
        after = current_gaps.get(subject)
        if before is None:
            opened.append(after)
        elif after is None:
            closed.append(before)
        elif before != after:
            reason_changed.append({"prior": before, "current": after})
        else:
            unchanged.append(after)
    return {
        "opened": opened,
        "closed": closed,
        "reason_changed": reason_changed,
        "unchanged": unchanged,
    }


def _input_row(role, binding):
    run = binding.get("run") or {}
    run_id_value = run.get("id")
    collected_value = run.get("collected_at")
    run_id = _wire_display(run_id_value, max_length=120)
    collected = _wire_display(collected_value, max_length=120)
    gate_status = "; ".join(
        f"{gate['number']} {_display(gate['name'])}: "
        f"{'pass' if gate['passed'] else 'FAIL'}"
        for gate in binding["gates"]
    )
    return (
        f"| {role} | {run_id} | {collected} | `{binding['sha256']}` | "
        f"{binding['bytes']} | {gate_status} |"
    )


def _address_scope(addresses):
    lines = [
        "| Address | Provenance |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| `{item['address']}` | {item['provenance']} |" for item in addresses
    )
    return "\n".join(lines)


def _coverage_markdown(changes):
    rows = []
    for row in changes["added"]:
        rows.append(("added", row["venue"], row["source"], "--", _coverage_brief(row)))
    for row in changes["removed"]:
        rows.append(("removed", row["venue"], row["source"], _coverage_brief(row), "--"))
    for pair in changes["changed"]:
        rows.append(
            (
                "changed",
                pair["current"]["venue"],
                pair["current"]["source"],
                _coverage_brief(pair["prior"]),
                _coverage_brief(pair["current"]),
            )
        )
    if not rows:
        return "_No coverage rows changed._"
    lines = [
        "| Change | Venue | Source route | Prior | Current |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| {} | {} | {} | {} | {} |".format(
            kind,
            _display(venue),
            _display(source),
            before,
            after,
        )
        for kind, venue, source, before, after in rows
    )
    return "\n".join(lines)


def _coverage_brief(row):
    fields = ("status", "block_range", "records", "releases", "endpoint", "note")
    return "; ".join(
        f"{field}={_wire_display(row[field], max_length=400)}"
        for field in fields
    )


def _gaps_markdown(changes):
    if not any(changes.values()):
        return "_No gaps were reported by either input._"
    lines = []
    for heading, key in (
        ("Opened", "opened"),
        ("Closed", "closed"),
        ("Reason changed", "reason_changed"),
        ("Still open", "unchanged"),
    ):
        lines.extend([f"### {heading}", ""])
        entries = changes[key]
        if not entries:
            lines.extend(["_None._", ""])
            continue
        if key == "reason_changed":
            for pair in entries:
                subject = _wire_display(pair["current"]["subject"], max_length=200)
                before = _wire_display(pair["prior"]["reason"], max_length=400)
                after = _wire_display(pair["current"]["reason"], max_length=400)
                lines.append(f"- **{subject}:** {before} → {after}")
        else:
            for gap in entries:
                subject = _wire_display(gap["subject"], max_length=200)
                reason = _wire_display(gap["reason"], max_length=400)
                lines.append(f"- **{subject}:** {reason}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _record_sections(changes):
    lines = []
    for heading, key in (
        ("Newly present", "newly_present"),
        ("Revised", "revised"),
        ("Observation refreshed", "observation_refreshed"),
        ("No longer reproduced", "no_longer_reproduced"),
    ):
        lines.extend([f"### {heading}", ""])
        entries = changes[key]
        if not entries:
            lines.extend(["_None._", ""])
        elif key in ("revised", "observation_refreshed"):
            lines.extend([_paired_record_table(entries), ""])
        else:
            lines.extend([_record_table(entries), ""])
    return "\n".join(lines).rstrip()


def _record_table(records):
    lines = [
        "| Observed (UTC / Unix) | Block | Venue | Address | Provenance | Claim | Values | Source kind | Source |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(_record_row(record) for record in records)
    return "\n".join(lines)


def _paired_record_table(pairs):
    lines = [
        "| Change | Role | Observed (UTC / Unix) | Block | Venue | Address | Provenance | Claim | Values | Source kind | Source |",
        "| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, pair in enumerate(pairs, 1):
        lines.append(_record_row(pair["prior"], side="prior", change=index))
        lines.append(_record_row(pair["current"], side="current", change=index))
    return "\n".join(lines)


def _record_row(record, side=None, change=None):
    cells = []
    if side is not None:
        cells.extend([str(change), side])
    cells.extend(
        [
            _observed_at(record.get("observed_at")),
            str(record.get("block") if record.get("block") is not None else "--"),
            _display(record["venue"]),
            f"`{record['address']}`",
            _display(record["provenance"]),
            _wire_display(record["claim"]),
            _record_values(record["values"]),
            _display(record["source_kind"]),
            _full_citation(record),
        ]
    )
    return "| " + " | ".join(cells) + " |"


def _full_citation(record):
    """Render the complete validated source, including transaction hashes."""
    source = record["source"]
    if record["source_kind"] == "url":
        return f"[source]({source})"
    return f"`{source}`"


def _record_values(values):
    parts = []
    for key, value in sorted(values.items()):
        clean_key = _display(key, max_length=80)
        literal = json.dumps(value, ensure_ascii=True)
        clean_value = _display(literal, max_length=4096)
        parts.append(f"{clean_key}={clean_value}")
    return "; ".join(parts) or "--"


def _wire_display(value, max_length=sanitise.MAX_LENGTH):
    literal = json.dumps(value, ensure_ascii=True, sort_keys=True)
    digest_source = value if isinstance(value, str) else literal
    return _display(literal, max_length=max_length, digest_source=digest_source)


def _display(value, max_length=sanitise.MAX_LENGTH, digest_source=None):
    """Render hostile text safely without collapsing distinct hidden values."""
    raw = "" if value is None else str(value)
    clean = sanitise.clean(raw, max_length=max_length)
    if clean != raw:
        digest_text = raw if digest_source is None else str(digest_source)
        digest = hashlib.sha256(digest_text.encode("utf-8")).hexdigest()
        return f"{clean} (text SHA-256: `{digest}`)"
    return clean


def _observed_at(value):
    if value is None:
        return "--"
    return f"{formatting.timestamp(value)} (`{value}`)"
