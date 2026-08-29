"""Translate Alexandria query evidence without adding credit conclusions."""

from __future__ import annotations

from .query import query


SUPPORTED_VENUES = {"clearpool", "goldfinch"}


def translate(index_path, addresses):
    """Return neutral constructor arguments for Probitas Record and Coverage.

    Each coverage row names its releases as a field as well as inside its
    note. The note is prose, and a Probitas gate that wanted to require an
    archive row to name its provenance would otherwise have to parse it.
    """
    result = query(index_path, addresses)
    records = []
    for item in result["events"]:
        row = item["row"]
        if row["venue"] not in SUPPORTED_VENUES:
            continue
        records.append(_event(item))
    for item in result["observations"]:
        row = item["row"]
        if row["venue"] not in SUPPORTED_VENUES:
            continue
        records.append(_observation(item))

    coverage = []
    gaps = []
    by_venue = {}
    for item in result["coverage"]:
        if item["venue"] not in SUPPORTED_VENUES:
            continue
        by_venue.setdefault(item["venue"], []).append(item)
    for venue, items in sorted(by_venue.items()):
        records_count = sum(item["records"] for item in items)
        all_covered = all(item["status"] == "covered" for item in items)
        status = ("checked" if records_count else "empty") if all_covered else "error"
        if not all_covered:
            failed = ",".join(
                f"{item['chain'] or 'unspecified'}={item['status']}"
                for item in items if item["status"] != "covered"
            )
            gaps.append({
                "reason": (
                    f"Alexandria coverage was incomplete ({failed}); zero rows cannot "
                    "be read as an empty history"
                ),
                "subject": f"{venue} borrowing history",
            })
        captures = [capture for item in items for capture in item["captures"]]
        evidence = sorted({
            capture["capture"]["evidence_class"] for capture in captures
        })
        release_ids = sorted({capture["release_id"] for capture in captures})
        capture_ids = sorted({capture["capture"]["id"] for capture in captures})
        chain_status = ",".join(
            f"{item['chain'] or 'unspecified'}={item['status']}" for item in items
        )
        coverage.append({
            "block_range": _block_range(captures),
            "endpoint": "Alexandria index",
            "releases": release_ids,
            "note": (
                f"archive-backed coverage {chain_status}; evidence "
                f"{','.join(evidence) if evidence else 'none'}; releases "
                f"{','.join(release_ids) if release_ids else 'none'}; captures "
                f"{','.join(capture_ids) if capture_ids else 'none'}"
            ),
            "records": records_count,
            "status": status,
            "venue": venue,
        })
    return {"coverage": coverage, "gaps": gaps, "records": records}


def _event(item):
    row = item["row"]
    transaction = row.get("transaction", {})
    source = transaction.get("hash") or _document_source(item)
    values = _provenance_values(item)
    for index, amount in enumerate(row["amounts"], start=1):
        suffix = "" if index == 1 else f"_{index}"
        values[f"amount{suffix}"] = amount["base_units"]
        values[f"amount_role{suffix}"] = amount["role"]
        asset = amount["asset"]
        if "symbol" in asset:
            values[f"token_symbol{suffix}"] = asset["symbol"]
        if "address" in asset:
            values[f"token_address{suffix}"] = asset["address"]
        values[f"token_decimals{suffix}"] = asset["decimals"]
    values["action"] = row["action"]
    values["facility"] = row["facility"]["id"]
    claim = {
        "borrowing": "borrow",
        "repayment": "repayment",
        "liquidation": "liquidation",
    }[row["event_family"]]
    return {
        "address": row["subject"].rsplit(":", 1)[1],
        "block": transaction.get("block_number"),
        "claim": claim,
        "observed_at": transaction.get("timestamp"),
        "source": source,
        "values": values,
        "venue": row["venue"],
    }


def _observation(item):
    row = item["row"]
    observation = row["observation"]
    values = _provenance_values(item)
    values.update({
        "facility": row["facility"]["id"],
        "observation_method": observation["method"],
        "observation_property": observation["property"],
        "observation_unit": observation["unit"],
        "observation_value": observation["value"],
    })
    if "terms" in row:
        values["maturity"] = row["terms"]["maturity_timestamp"]
    boundary = observation["at"]
    return {
        "address": row["subject"].rsplit(":", 1)[1],
        "block": boundary.get("block_number"),
        "claim": "position_observation",
        "observed_at": boundary.get("timestamp"),
        "source": _document_source(item),
        "values": values,
        "venue": row["venue"],
    }


def _provenance_values(item):
    provenance = item["row"]["provenance"]
    return {
        "alexandria_release_id": item["release_id"],
        "alexandria_row_id": item["row_id"],
        "capture_id": provenance["capture_id"],
        "component": provenance["component"],
        "component_sha256": provenance["component_sha256"],
        "adapter_version": provenance["adapter_version"],
        "context_selectors": ",".join(provenance.get("context_selectors", [])),
        "evidence_class": provenance["evidence_class"],
        "mapping_rule": provenance["mapping_rule"],
        "source_identity": provenance["source_identity"],
        "source_release_id": provenance["source_release_id"],
        "source_selector": provenance["source_selector"],
    }


def _document_source(item):
    return f"doc:alexandria {item['release_id']} {item['row_id']}"


def _block_range(captures):
    values = []
    for item in captures:
        interval = item["capture"]["scope"]["interval"]
        if interval["kind"] == "block-range":
            values.append(f"{interval['start']}-{interval['end']}")
        else:
            values.append(f"snapshot {interval['observed_at']}")
    return ", ".join(sorted(set(values))) or None
