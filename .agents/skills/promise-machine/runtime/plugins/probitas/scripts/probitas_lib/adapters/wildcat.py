"""Wildcat: what a borrower did in markets whose terms they set themselves.

This is the venue the whole tool is for. Every other lending market is
overcollateralised, which means the collateral answered the question and the
borrower's conduct never had to. Wildcat markets are the public record of a
counterparty choosing a reserve ratio, a grace period and a rate, and then
either holding to them or not.

The subgraph carries all of it and every event carries a transaction hash, so
gate 3 is satisfied by construction here rather than by effort.

Two things to be careful about, both flagged in the study's risk register.
`timeDelinquent` is signed and runs negative while a market is healthy, so
reading it as a duration invents a delinquency. And an unexpected response
shape raises rather than returning nothing, because a schema change at the
venue would otherwise pass every test and quietly empty every real dossier.
"""

import json
import os

from .. import endpoints, sanitise
from ..evidence import Coverage, Record
from ..graphql import GraphQLError, post

VENUE = "wildcat"

PAGE = 100
NESTED_PAGE = 100

# A venue answering a full page every time would page for ever. Stopping at a
# silent cap would put a partial history under a coverage row reading
# `checked`, so hitting the ceiling raises instead: better a loud failure than
# a quiet half-record.
MAX_PAGES = 200

_MARKET_FIELDS = """
  id
  name
  symbol
  borrower
  createdAt
  isClosed
  isDelinquent
  isIncurringPenalties
  timeDelinquent
  delinquencyGracePeriod
  delinquencyFeeBips
  reserveRatioBips
  originalReserveRatioBips
  annualInterestBips
  totalBorrowed
  totalRepaid
  totalDelinquencyFeesAccrued
  asset { symbol decimals }
  deployedEvent { transactionHash blockNumber blockTimestamp }
  marketClosedEvent { transactionHash blockNumber blockTimestamp }
"""

_DELINQUENCY_FIELDS = (
    "isDelinquent blockTimestamp blockNumber transactionHash "
    "liquidityCoverageRequired totalAssets"
)
_BORROW_FIELDS = "assetAmount blockTimestamp blockNumber transactionHash"
_REPAYMENT_FIELDS = "assetAmount blockTimestamp blockNumber transactionHash"
_BATCH_FIELDS = (
    "expiry totalNormalizedRequests normalizedAmountPaid isExpired isClosed "
    "expiration { transactionHash blockNumber blockTimestamp }"
)

MARKETS_QUERY = """
query Markets($borrowers: [Bytes!]!, $skip: Int!, $first: Int!, $nested: Int!) {
  markets(
    first: $first
    skip: $skip
    where: { borrower_in: $borrowers }
    orderBy: createdAt
    orderDirection: asc
  ) {
    %s
    delinquencyRecords(first: $nested, orderBy: blockTimestamp) { %s }
    borrowRecords(first: $nested, orderBy: blockTimestamp) { %s }
    repaymentRecords(first: $nested, orderBy: blockTimestamp) { %s }
    withdrawalBatches(first: $nested, orderBy: expiry) { %s }
  }
}
""" % (
    _MARKET_FIELDS,
    _DELINQUENCY_FIELDS,
    _BORROW_FIELDS,
    _REPAYMENT_FIELDS,
    _BATCH_FIELDS,
)

_COLLECTIONS = {
    "delinquencyRecords": _DELINQUENCY_FIELDS,
    "borrowRecords": _BORROW_FIELDS,
    "repaymentRecords": _REPAYMENT_FIELDS,
    "withdrawalBatches": _BATCH_FIELDS,
}

_COLLECTION_ORDER = {
    "delinquencyRecords": "blockTimestamp",
    "borrowRecords": "blockTimestamp",
    "repaymentRecords": "blockTimestamp",
    "withdrawalBatches": "expiry",
}

COLLECTION_QUERY = """
query Collection($market: ID!, $skip: Int!, $first: Int!) {
  market(id: $market) {
    %s(first: $first, skip: $skip, orderBy: %s) { %s }
  }
}
"""


class WildcatShapeError(GraphQLError):
    """The subgraph answered, but not with the shape this adapter reads."""


def _require(mapping, key, where):
    if not isinstance(mapping, dict) or key not in mapping:
        raise WildcatShapeError(f"{where} has no {key!r}; the subgraph schema moved")
    return mapping[key]


def _integer(mapping, key, where):
    value = _require(mapping, key, where)
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise WildcatShapeError(f"{where}.{key} is not an integer: {value!r}") from error


def _boolean(mapping, key, where):
    """A flag off the network, or a shape error.

    `bool()` on anything that is not a boolean is where this goes wrong.
    A field that turns from `false` into a string reads as true, so a healthy
    market reports as delinquent and a batch that expired unpaid reports as
    settled and drops out of the dossier entirely. The truthiness of a value
    the venue sent is not evidence of anything.
    """
    value = _require(mapping, key, where)
    if not isinstance(value, bool):
        raise WildcatShapeError(f"{where}.{key} is not a boolean: {value!r}")
    return value


def _address(mapping, key, where):
    """An address off the network, or a shape error.

    Everything this adapter refuses raises the same exception, so a caller
    catches one thing rather than guessing which layer complained.
    """
    value = _require(mapping, key, where)
    try:
        return sanitise.address(value)
    except ValueError as error:
        raise WildcatShapeError(f"{where}.{key} is not an address: {value!r}") from error


def _hash(mapping, key, where):
    value = _require(mapping, key, where)
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise WildcatShapeError(f"{where}.{key} is not a transaction hash: {value!r}")
    return value


def _load_fixture(directory):
    path = os.path.join(directory, "wildcat.json")
    if not os.path.exists(path):
        raise WildcatShapeError(f"no wildcat fixture at {path}")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _fetch_markets(endpoint, borrowers, timeout):
    """Page through the borrower's markets, then top up any truncated list.

    A nested list that comes back exactly full might have more behind it.
    Silently keeping the first hundred would put a partial history under a
    coverage row saying `checked`, which is the failure gate 2 exists to
    prevent, so each full list gets paged out on its own.
    """
    markets = []
    for page_number in range(MAX_PAGES):
        data = post(
            endpoint,
            MARKETS_QUERY,
            {
                "borrowers": borrowers,
                "skip": page_number * PAGE,
                "first": PAGE,
                "nested": NESTED_PAGE,
            },
            timeout=timeout,
        )
        page = _require(data, "markets", "response")
        if not isinstance(page, list):
            raise WildcatShapeError("markets is not a list; the subgraph schema moved")
        markets.extend(page)
        if len(page) < PAGE:
            break
    else:
        raise WildcatShapeError(
            f"markets did not run out after {MAX_PAGES} pages; refusing to "
            "report a history that may be incomplete"
        )

    for market in markets:
        for collection, fields in _COLLECTIONS.items():
            existing = _require(market, collection, "market")
            if len(existing) < NESTED_PAGE:
                continue
            market[collection] = _fetch_collection(
                endpoint, market["id"], collection, fields, timeout
            )
    return markets


def _fetch_collection(endpoint, market_id, collection, fields, timeout):
    query = COLLECTION_QUERY % (collection, _COLLECTION_ORDER[collection], fields)
    out = []
    for page_number in range(MAX_PAGES):
        data = post(
            endpoint,
            query,
            {"market": market_id, "skip": page_number * PAGE, "first": PAGE},
            timeout=timeout,
        )
        market = _require(data, "market", "response")
        page = _require(market, collection, "market")
        out.extend(page)
        if len(page) < PAGE:
            return out
    raise WildcatShapeError(
        f"{collection} for {market_id} did not run out after {MAX_PAGES} pages; "
        "refusing to report a history that may be incomplete"
    )


def _market_records(market, provenance):
    """Turn one market into records. Every one of them carries a hash."""
    address = _address(market, "borrower", "market")
    # A market id is an address, and it reaches the dossier as a value. Taking
    # the venue's word for its shape would let a bad response put arbitrary
    # text in a table cell.
    market_id = _address(market, "id", "market")
    deployed = _require(market, "deployedEvent", "market")
    deployed_hash = _hash(deployed, "transactionHash", "deployedEvent")
    deployed_at = _integer(deployed, "blockTimestamp", "deployedEvent")
    deployed_block = _integer(deployed, "blockNumber", "deployedEvent")

    def record(claim, values, source, observed_at=None, block=None):
        return Record(
            venue=VENUE,
            address=address,
            provenance=provenance,
            claim=claim,
            values=values,
            source=source,
            observed_at=observed_at,
            block=block,
        )

    asset = _require(market, "asset", "market")
    records = [
        # The terms the borrower chose. Cited to the transaction that created
        # the market, which is what makes the market identifiable at all.
        record(
            "market_terms",
            {
                "market": market_id,
                "market_name": sanitise.clean(_require(market, "name", "market")),
                "token_symbol": sanitise.clean(_require(asset, "symbol", "asset")),
                "token_decimals": _integer(asset, "decimals", "asset"),
                "reserve_ratio_bips": _integer(market, "originalReserveRatioBips", "market"),
                "annual_interest_bips": _integer(market, "annualInterestBips", "market"),
                "grace_period_seconds": _integer(market, "delinquencyGracePeriod", "market"),
                "delinquency_fee_bips": _integer(market, "delinquencyFeeBips", "market"),
            },
            deployed_hash,
            observed_at=deployed_at,
            block=deployed_block,
        ),
        record(
            "market_standing",
            {
                "market": market_id,
                "is_closed": _boolean(market, "isClosed", "market"),
                "is_delinquent_now": _is_delinquent_now(market),
                "incurring_penalties_now": _boolean(
                    market, "isIncurringPenalties", "market"
                ),
                "total_borrowed": _integer(market, "totalBorrowed", "market"),
                "total_repaid": _integer(market, "totalRepaid", "market"),
                "penalty_interest_accrued": _integer(
                    market, "totalDelinquencyFeesAccrued", "market"
                ),
            },
            deployed_hash,
            observed_at=deployed_at,
            block=deployed_block,
        ),
    ]

    # `_require` rather than `.get`: a renamed field would otherwise read as
    # "this market was never closed" for every market at once, which is the
    # divergence the issue says has to raise.
    closed = _require(market, "marketClosedEvent", "market")
    if closed:
        records.append(
            record(
                "market_closed",
                {"market": market_id},
                _hash(closed, "transactionHash", "marketClosedEvent"),
                observed_at=_integer(closed, "blockTimestamp", "marketClosedEvent"),
                block=_integer(closed, "blockNumber", "marketClosedEvent"),
            )
        )

    grace = _integer(market, "delinquencyGracePeriod", "market")
    entered_at = None
    # Sorted here rather than trusted from the query. Pairing an entry with a
    # cure is arithmetic on two timestamps, and out-of-order input turns that
    # into a wrong number of seconds attached to a named borrower.
    delinquency_records = sorted(
        _require(market, "delinquencyRecords", "market"),
        key=lambda entry: _integer(entry, "blockTimestamp", "delinquencyRecord"),
    )
    for entry in delinquency_records:
        where = "delinquencyRecord"
        delinquent = _boolean(entry, "isDelinquent", where)
        at = _integer(entry, "blockTimestamp", where)
        values = {
            "market": market_id,
            "liquidity_required": _integer(entry, "liquidityCoverageRequired", where),
            "assets_held": _integer(entry, "totalAssets", where),
        }
        if delinquent:
            # Keep the first entry, not the last. A repeated entry with no cure
            # between them would otherwise move the start forward and report a
            # shorter delinquency than the borrower actually ran.
            if entered_at is None:
                entered_at = at
            claim = "delinquency_entered"
        else:
            claim = "delinquency_cured"
            if entered_at is not None:
                values["seconds_delinquent"] = at - entered_at
                values["past_grace_period"] = (at - entered_at) > grace
                entered_at = None
        records.append(
            record(
                claim,
                values,
                _hash(entry, "transactionHash", where),
                observed_at=at,
                block=_integer(entry, "blockNumber", where),
            )
        )

    for entry in _require(market, "borrowRecords", "market"):
        records.append(_amount_record(record, market_id, entry, "borrow", "borrowRecord"))
    for entry in _require(market, "repaymentRecords", "market"):
        records.append(
            _amount_record(record, market_id, entry, "repayment", "repaymentRecord")
        )

    for batch in _require(market, "withdrawalBatches", "market"):
        where = "withdrawalBatch"
        if not _boolean(batch, "isExpired", where) or _boolean(
            batch, "isClosed", where
        ):
            continue
        expiration = _require(batch, "expiration", where)
        if not expiration:
            # Expired with no expiry event indexed. Reporting it without a
            # citation would break gate 3, and reporting nothing would hide it,
            # so it goes out cited to the market that owns it.
            source, at, block = deployed_hash, deployed_at, deployed_block
        else:
            source = _hash(expiration, "transactionHash", "expiration")
            at = _integer(expiration, "blockTimestamp", "expiration")
            block = _integer(expiration, "blockNumber", "expiration")
        records.append(
            record(
                "withdrawal_batch_expired_unpaid",
                {
                    "market": market_id,
                    "expiry": _integer(batch, "expiry", where),
                    "requested": _integer(batch, "totalNormalizedRequests", where),
                    "paid": _integer(batch, "normalizedAmountPaid", where),
                },
                source,
                observed_at=at,
                block=block,
            )
        )

    return records


def _amount_record(record, market_id, entry, claim, where):
    return record(
        claim,
        {"market": market_id, "amount": _integer(entry, "assetAmount", where)},
        _hash(entry, "transactionHash", where),
        observed_at=_integer(entry, "blockTimestamp", where),
        block=_integer(entry, "blockNumber", where),
    )


def _is_delinquent_now(market):
    """Read the delinquency flags without inventing one.

    `timeDelinquent` is a signed counter that runs down while a market is
    healthy and is routinely negative on live markets. `isDelinquent` is the
    flag that means what it says, so it is the one that decides, and
    `timeDelinquent` is only ever read as a number of seconds when it is
    positive.
    """
    return _boolean(market, "isDelinquent", "market")


def seconds_delinquent(market):
    """The current delinquency in seconds, or zero when the market is healthy."""
    value = _integer(market, "timeDelinquent", "market")
    return value if value > 0 else 0


def adapter(addresses, config):
    """Run the Wildcat venue. Returns (records, coverage)."""
    config = config or {}
    network = config.get("wildcat_network", endpoints.DEFAULT_WILDCAT_NETWORK)
    deployment = endpoints.WILDCAT_DEPLOYMENTS.get(network)
    if deployment is None:
        raise WildcatShapeError(f"unknown Wildcat network: {network}")

    borrowers = sorted(addresses)
    fixtures = config.get("fixtures")

    if fixtures:
        markets = _require(_load_fixture(fixtures), "markets", "fixture")
        name = os.path.basename(os.path.normpath(fixtures)) or "unnamed"
        endpoint = "fixture:" + sanitise.clean(name, max_length=60)
        block_range = "fixture"
    else:
        endpoint = deployment["endpoint"]
        markets = _fetch_markets(
            endpoint, borrowers, config.get("timeout", 30)
        )
        block_range = f"{deployment['start_block']}-latest"

    records = []
    for market in markets:
        borrower = _address(market, "borrower", "market")
        if borrower not in addresses:
            # The venue answered about someone the operator did not ask about.
            raise WildcatShapeError(
                f"subgraph returned a market for {borrower}, which is not a "
                "subject address"
            )
        records.extend(_market_records(market, addresses[borrower]))

    return records, Coverage(
        venue=VENUE,
        status="checked" if markets else "empty",
        endpoint=endpoint,
        block_range=block_range,
        note=(
            # Name the network. Wildcat is deployed on Plasma as well and this
            # run queried one of them, so a row that says only "checked" would
            # let a reader take it for all of them.
            f"{network} only; {len(markets)} market(s) across "
            f"{len(borrowers)} address(es)"
            if markets
            else f"{network} only; no markets found for any subject address"
        ),
    )
