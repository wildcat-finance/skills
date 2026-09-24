"""Select a borrower's facts from Tabularium's verified Wildcat archive view."""

import importlib
from pathlib import Path
import sys
import textwrap

from . import sanitise
from .evidence import Coverage, EvidenceError, Gap, Record


def _view_api():
    scripts = Path(__file__).resolve().parents[3] / "tabularium" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        module = importlib.import_module("tabularium_lib.wildcat_view")
        core = importlib.import_module("tabularium_lib.core")
    except ImportError as error:
        raise EvidenceError("Wildcat archives require the sibling Tabularium plugin") from error
    finally:
        sys.path.remove(str(scripts))
    for item in (module, core):
        if not getattr(item, "__file__", None) or not Path(item.__file__).resolve().is_relative_to(scripts):
            raise EvidenceError("loaded Tabularium API is outside the sibling plugin")
    return module.make_wildcat_view, core.TabulariumError


def _reference(values, prefix, source):
    for name in ("component", "component_sha256", "capture_id", "evidence_class",
                 "journal_selector", "response_sha256", "selector"):
        values[f"{prefix}_{name}"] = source[name]


def output_path(output, releases):
    """Keep consumer output outside preserved inputs, including linked paths."""
    target = Path(output).absolute()
    if any(part.is_symlink() for part in (target, *target.parents)):
        raise EvidenceError("Wildcat evidence output must not use a symlink path")
    target = target.resolve()
    if any(target.is_relative_to(Path(root).resolve()) for root in releases):
        raise EvidenceError("Wildcat evidence output must be outside every preserved release")
    if target.exists() and target.stat().st_nlink > 1:
        raise EvidenceError("Wildcat evidence output must not be a hard-linked file")
    return target


def collect(release_paths, evidence):
    """Read one release per generation, without calling the subgraph adapter."""
    if not 1 <= len(release_paths) <= 2:
        raise EvidenceError("supply at most one Wildcat release per generation")
    make_view, view_error = _view_api()
    views = []
    try:
        for path in release_paths:
            views.append(make_view(path))
    except (view_error, OSError) as error:
        raise EvidenceError(f"Wildcat archive: {error}") from error
    if len({view["venue"] for view in views}) != len(views):
        raise EvidenceError("multiple Wildcat releases for one generation are not supported")
    total = 0
    for view in views:
        count = 0
        for row in view["records"]:
            borrower = row["borrower"]
            if borrower not in evidence.addresses:
                continue
            values = dict(row["values"])
            for key in ("market_name", "market_symbol"):
                if key in values:
                    values[key] = sanitise.clean(values[key], max_length=200)
            binding = view["bindings"][row["market"]]
            values.update({
                "archive_release": view["release_id"], "archive_venue": view["venue"],
                "mapping": view["format"], "source_commit": view["source_commit"],
                "registry_sha256": view["registry_sha256"],
                "borrower_class": row["borrower_class"], "borrower_rule": binding["rule"],
            })
            for evidence_class, key in (("directly-observed", "observed_fields"),
                                        ("derived-from-recorded-evidence", "derived_fields")):
                fields = sorted(field for field, value in row["field_classes"].items() if value == evidence_class)
                if fields:
                    values[key] = ",".join(fields)
            _reference(values, "event", row["source"])
            _reference(values, "binding", binding["source"])
            _reference(values, "deployment", binding["deployment_source"])
            log = row["native"]
            values["transaction_hash"] = log["transactionHash"]
            values["log_index"] = str(int(log["logIndex"], 16))
            values["block_hash"] = log["blockHash"]
            evidence.add_record(Record(
                venue="wildcat", address=borrower, provenance=evidence.addresses[borrower],
                claim=row["claim"], values=values,
                source=(f"doc:{view['release_id']}:{row['source']['component']}:"
                        f"{row['source']['journal_selector']}:{row['source']['selector']}"),
                block=int(log["blockNumber"], 16), observed_at=None,
            ))
            count += 1
        bounds = view["interval"]
        total += count
        for family, fields in view["unsupported_fields"].items():
            reasons = {}
            for field, reason in fields.items():
                reasons.setdefault(reason, []).append(field)
            for index, (reason, names) in enumerate(reasons.items(), 1):
                suffix = f" ({index})" if len(reasons) > 1 else ""
                evidence.add_gap(Gap(
                    subject=f"{view['venue']} {family.replace('_', ' ')}{suffix}",
                    reason="Unsupported: " + ", ".join(names) + ". " + reason,
                ))
        evidence.add_gap(Gap(
            subject=f"{view['venue']} historical coverage",
            reason=(f"Only blocks {bounds['start']}-{bounds['end']} and {len(view['selected_markets'])} "
                    f"selected markets were inspected. {len(view['unattributed_markets'])} markets lack "
                    "a borrower binding. Amounts remain raw units. Recorded provider evidence is not "
                    "independently proved chain state; no state replay or default conclusion is supplied."),
        ))
        raw_gaps = sorted({gap for coverage in view["raw_capture_coverage"].values()
                           for gap in coverage.get("gaps", [])})
        for index, gap in enumerate(raw_gaps, 1):
            for part, chunk in enumerate(textwrap.wrap(gap, width=330, break_long_words=False, break_on_hyphens=False), 1):
                evidence.add_gap(Gap(subject=f"{view['venue']} raw capture limitation {index}.{part}",
                                     reason="Raw archive producer: " + chunk))
    evidence.add_coverage(Coverage(
        venue="wildcat", source="archive", status="checked",
        records=total, releases=[view["release_id"] for view in views],
        block_range="; ".join(f"{v['venue']} {v['interval']['start']}-{v['interval']['end']}" for v in views),
        note=("Finite preserved intervals; deployment terms and native amounts only. "
              "Coverage remains partial; zero records means no attributable facts in this selection."),
    ))
