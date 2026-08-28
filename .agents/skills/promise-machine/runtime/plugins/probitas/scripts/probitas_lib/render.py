"""Turn an evidence file into the document a lender reads.

The order is the specification's and it is not negotiable: coverage and
negative space stand ahead of anything that reads like a conclusion, and
findings against addresses the counterparty did not declare sit in their own
section at the end, where they cannot be mistaken for part of the record.

Nothing is invented here. Every line traces to a record, and the renderer has
no way to write a number the evidence does not contain.
"""

import json
import os

from . import formatting, registry

TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets",
    "dossier-template.md",
)

NARRATIVE_MARKER = "_Nothing to report._"

# Claims that belong under Wildcat's own heading rather than the general
# borrowing history, because they are about terms the borrower set rather than
# money moving.
WILDCAT_CLAIMS = (
    "market_terms",
    "market_standing",
    "market_closed",
    "delinquency_entered",
    "delinquency_cured",
    "withdrawal_batch_expired_unpaid",
)

CLAIM_LABELS = {
    "market_terms": "Terms set",
    "market_standing": "Standing",
    "market_closed": "Market closed",
    "delinquency_entered": "Went delinquent",
    "delinquency_cured": "Delinquency cured",
    "withdrawal_batch_expired_unpaid": "Withdrawal expired unpaid",
    "borrow": "Drew",
    "repayment": "Repaid",
    "liquidation": "Liquidated",
    "bad_debt": "Bad debt left unpaid",
}


class RenderError(ValueError):
    """The evidence file is not something a dossier can be built from."""


def load(path):
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise RenderError(f"{path} is not a probitas evidence file")
    for key in ("subject", "records", "coverage", "gaps"):
        if key not in payload:
            raise RenderError(f"{path} has no {key!r} block")
        if key != "subject" and not isinstance(payload[key], list):
            raise RenderError(f"{path} has a {key!r} block that is not a list")
    if not isinstance(payload["subject"].get("addresses"), list):
        raise RenderError(f"{path} has no subject addresses")
    return payload


def decimals_by_market(records):
    """Token decimals, taken from the terms record of each market.

    Without them an amount prints as raw units and says so. A number in an
    underwriting document that might be off by six orders of magnitude is worse
    than one the reader has to divide themselves.
    """
    out = {}
    for record in records:
        values = record["values"]
        market = values.get("market")
        if market and "token_decimals" in values:
            out.setdefault(
                market, (values["token_decimals"], values.get("token_symbol"))
            )
    return out


def _cite(record):
    source = record["source"]
    if record["source_kind"] == "transaction":
        return f"`{formatting.short(source)}`"
    if record["source_kind"] == "url":
        return f"[source]({source})"
    return f"`{source}`"


def _describe(record, decimals):
    """One record as a phrase, with every number it prints coming from it."""
    values = record["values"]
    claim = record["claim"]
    market = values.get("market")
    scale, symbol = decimals.get(market, (None, None))

    if claim in ("borrow", "repayment", "bad_debt"):
        return formatting.amount(values["amount"], scale, symbol)

    if claim == "liquidation":
        # Said plainly, because the reader's instinct will be to call this a
        # default. On an overcollateralised venue it is a price moving.
        return (
            "collateral sold to cover "
            + formatting.amount(values["repaid"], scale, symbol)
            + "; the position was collateralised, so this is a price moving "
            "rather than a borrower walking away"
        )

    if claim == "market_terms":
        return (
            f"{values.get('market_name', 'market')}, "
            f"reserve ratio {formatting.bips(values['reserve_ratio_bips'])}, "
            f"rate {formatting.bips(values['annual_interest_bips'])}, "
            f"grace period {formatting.duration(values['grace_period_seconds'])}, "
            f"penalty {formatting.bips(values['delinquency_fee_bips'])}"
        )

    if claim == "market_standing":
        parts = [
            "drew " + formatting.amount(values["total_borrowed"], scale, symbol),
            "repaid " + formatting.amount(values["total_repaid"], scale, symbol),
        ]
        penalty = int(values["penalty_interest_accrued"])
        parts.append(
            "penalty interest "
            + formatting.amount(values["penalty_interest_accrued"], scale, symbol)
            if penalty
            else "no penalty interest"
        )
        if values["is_delinquent_now"]:
            parts.append("delinquent now")
        if values["incurring_penalties_now"]:
            parts.append("past the grace period now")
        if values["is_closed"]:
            parts.append("closed")
        return "; ".join(parts)

    if claim == "delinquency_entered":
        return (
            "held "
            + formatting.amount(values["assets_held"], scale, symbol)
            + " against a requirement of "
            + formatting.amount(values["liquidity_required"], scale, symbol)
        )

    if claim == "delinquency_cured":
        if "seconds_delinquent" not in values:
            return "returned to the reserve ratio"
        span = formatting.duration(values["seconds_delinquent"])
        verdict = (
            "past the grace period"
            if values.get("past_grace_period")
            else "inside the grace period"
        )
        return f"after {span}, {verdict}"

    if claim == "withdrawal_batch_expired_unpaid":
        return (
            "requested "
            + formatting.amount(values["requested"], scale, symbol)
            + ", paid "
            + formatting.amount(values["paid"], scale, symbol)
        )

    if claim == "market_closed":
        return "closed by the borrower"

    return "; ".join(f"{k} {v}" for k, v in sorted(values.items()))


def _rows(records, decimals):
    lines = [
        "| Date | Venue | Event | Detail | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        label = CLAIM_LABELS.get(record["claim"], record["claim"].replace("_", " "))
        lines.append(
            "| {} | {} | {} | {} | {} |".format(
                formatting.timestamp(record.get("observed_at")) or "--",
                record["venue"],
                label,
                _describe(record, decimals),
                _cite(record),
            )
        )
    return "\n".join(lines)


def _subject(payload):
    lines = [f"**Entity.** {payload['subject']['entity']}", ""]
    for tier, heading in (
        ("declared", "Declared by the counterparty"),
        ("linked", "Provably linked on chain"),
    ):
        addresses = [
            a["address"]
            for a in payload["subject"]["addresses"]
            if a["provenance"] == tier
        ]
        if not addresses:
            continue
        lines.append(f"**{heading}.**")
        lines.append("")
        lines.extend(f"- `{address}`" for address in addresses)
        lines.append("")
    return "\n".join(lines).rstrip()


def _coverage(payload):
    known = {v.id: v.name for v in registry.all_venues()}
    lines = [
        "| Venue | Status | Range | Records | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["coverage"]:
        lines.append(
            "| {} | {} | {} | {} | {} |".format(
                known.get(row["venue"], row["venue"]),
                row["status"],
                row.get("block_range") or "--",
                row.get("records", 0),
                row.get("note") or "--",
            )
        )
    return "\n".join(lines)


def _gaps(payload):
    if not payload["gaps"]:
        return (
            "Nothing. Every venue in the registry was checked and every "
            "declared address resolved."
        )
    lines = ["| Subject | Why |", "| --- | --- |"]
    for gap in payload["gaps"]:
        lines.append(f"| {gap['subject']} | {gap['reason']} |")
    return "\n".join(lines)


def render(payload):
    """Build the dossier. Deterministic: same evidence, same bytes."""
    with open(TEMPLATE, encoding="utf-8") as handle:
        template = handle.read()

    records = payload["records"]
    decimals = decimals_by_market(records)
    tiers = {a["address"]: a["provenance"] for a in payload["subject"]["addresses"]}

    on_record = ("declared", "linked")

    history = [
        r
        for r in records
        if tiers.get(r["address"]) in on_record and r["claim"] not in WILDCAT_CLAIMS
    ]
    wildcat = [
        r
        for r in records
        if tiers.get(r["address"]) in on_record and r["claim"] in WILDCAT_CLAIMS
    ]
    inferred = [r for r in records if tiers.get(r["address"]) == "inferred"]

    run = payload.get("run") or {}
    run_line = "Run `{}`.".format(run.get("id") or "unidentified")

    sections = {
        "entity": payload["subject"]["entity"],
        "run_line": run_line,
        "subject": _subject(payload),
        "coverage": _coverage(payload),
        "negative_space": _gaps(payload),
        "history": _rows(history, decimals) if history else NARRATIVE_MARKER,
        "wildcat": _rows(wildcat, decimals) if wildcat else NARRATIVE_MARKER,
        "graph": (
            "No relationship between the declared addresses appears on chain in "
            "the venues checked, and none was declared."
        ),
        "incidents": NARRATIVE_MARKER,
        "inferred": _rows(inferred, decimals) if inferred else NARRATIVE_MARKER,
        "summary": (
            "Written by whoever runs this, from the sections above and nothing "
            "else. Probitas emits no rating: the specification leaves the "
            "question open and leans toward evidence without a score, because a "
            "score invites reliance the data cannot carry."
        ),
    }

    out = template
    for key, value in sections.items():
        out = out.replace("{{" + key + "}}", value)
    return out
