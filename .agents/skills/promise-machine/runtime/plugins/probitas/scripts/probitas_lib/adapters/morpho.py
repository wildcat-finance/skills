"""Morpho Blue: what a borrower did where the collateral answered for them.

This venue reads differently from Wildcat and the dossier has to respect the
difference. Morpho is overcollateralised, so nobody was relying on the
borrower's word: a liquidation says a price moved against a position and the
protocol closed it, not that a counterparty walked away from an obligation.
Reporting one as a default would be exactly the wrong claim about a named
person's company, and the gates exist to stop that kind of thing rather than to
wave it through.

The one signal here that does bear on conduct is bad debt. When a liquidation
does not cover what was owed, lenders lost money, and that is worth a record of
its own rather than a footnote on the liquidation.

Second adapter, so it is also the test of whether the interface was worth
having. It touches nothing outside this file, the registry, and the CLI's
adapter table.
"""

import json
import os

from .. import endpoints, sanitise
from ..evidence import Coverage, Record
from ..graphql import GraphQLError, post

VENUE = "morpho-blue"

PAGE = 100
MAX_PAGES = 200

MAINNET_CHAIN_ID = 1

# Borrowing-side only. Supplying to a market says nothing about whether this
# counterparty repays what they take.
CLAIMS = {
    "Borrow": "borrow",
    "Repay": "repayment",
    "Liquidation": "liquidation",
}

# Deliberately ignored, and listed rather than assumed. A type that is in
# neither table is a type this adapter has never seen, which means the venue
# changed its vocabulary; that raises. Skipping it quietly would make a
# borrower with a history read as one with none, which is the same shape as a
# clean record.
IGNORED = frozenset(
    {"Supply", "Withdraw", "SupplyCollateral", "WithdrawCollateral"}
)

TRANSACTIONS_QUERY = """
query Transactions($users: [String!], $chain: [Int!], $first: Int!, $skip: Int!) {
  marketTransactions(
    first: $first
    skip: $skip
    where: { userAddress_in: $users, chainId_in: $chain, type_in: [Borrow, Repay, Liquidation] }
    orderBy: Timestamp
    orderDirection: Asc
  ) {
    items {
      txHash
      timestamp
      blockNumber
      type
      user { address }
      market {
        marketId
        loanAsset { symbol decimals }
        collateralAsset { symbol decimals }
      }
      data {
        __typename
        ... on MarketTransactionTransferData { assets shares }
        ... on MarketTransactionLiquidationData {
          repaidAssets
          seizedAssets
          badDebtAssets
        }
      }
    }
    pageInfo { count countTotal }
  }
}
"""


class MorphoShapeError(GraphQLError):
    """The API answered, but not with the shape this adapter reads."""


def _require(mapping, key, where):
    if not isinstance(mapping, dict) or key not in mapping:
        raise MorphoShapeError(f"{where} has no {key!r}; the API schema moved")
    return mapping[key]


def _integer(mapping, key, where):
    """An integer, and never a float rounded into one.

    The API returns some amounts as JSON numbers and others as strings.
    `int(1.5)` is 1 without complaint, which in a document about money is how a
    wrong figure gets a citation attached to it.
    """
    value = _require(mapping, key, where)
    if isinstance(value, bool) or isinstance(value, float):
        raise MorphoShapeError(f"{where}.{key} is not a whole number: {value!r}")
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise MorphoShapeError(f"{where}.{key} is not an integer: {value!r}") from error


def _hash(mapping, key, where):
    value = _require(mapping, key, where)
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise MorphoShapeError(f"{where}.{key} is not a transaction hash: {value!r}")
    return value


def _market_id(market):
    value = _require(market, "marketId", "market")
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise MorphoShapeError(f"market.marketId is not a market id: {value!r}")
    return value


def _load_fixture(directory):
    path = os.path.join(directory, "morpho.json")
    if not os.path.exists(path):
        raise MorphoShapeError(f"no morpho fixture at {path}")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _fetch(endpoint, addresses, timeout):
    items = []
    for page in range(MAX_PAGES):
        data = post(
            endpoint,
            TRANSACTIONS_QUERY,
            {
                "users": sorted(addresses),
                "chain": [MAINNET_CHAIN_ID],
                "first": PAGE,
                "skip": page * PAGE,
            },
            timeout=timeout,
        )
        block = _require(data, "marketTransactions", "response")
        page_items = _require(block, "items", "marketTransactions")
        if not isinstance(page_items, list):
            raise MorphoShapeError("items is not a list; the API schema moved")
        items.extend(page_items)
        if len(page_items) < PAGE:
            return items
    raise MorphoShapeError(
        f"transactions did not run out after {MAX_PAGES} pages; refusing to "
        "report a history that may be incomplete"
    )


def _records(item, addresses):
    where = "transaction"
    kind = _require(item, "type", where)
    if kind in IGNORED:
        return []
    claim = CLAIMS.get(kind)
    if claim is None:
        raise MorphoShapeError(
            f"unknown transaction type {kind!r}; the venue changed its "
            "vocabulary and this adapter would drop the record in silence"
        )

    user = _require(item, "user", where)
    try:
        address = sanitise.address(_require(user, "address", "user"))
    except ValueError as error:
        raise MorphoShapeError(f"user.address is not an address: {error}") from error
    if address not in addresses:
        raise MorphoShapeError(
            f"the API returned a transaction for {address}, which is not a "
            "subject address"
        )

    market = _require(item, "market", where)
    asset = _require(market, "loanAsset", "market")
    data = _require(item, "data", where)
    source = _hash(item, "txHash", where)
    at = _integer(item, "timestamp", where)
    block = _integer(item, "blockNumber", where)

    shared = {
        "market": _market_id(market),
        "token_symbol": sanitise.clean(_require(asset, "symbol", "loanAsset")),
        "token_decimals": _integer(asset, "decimals", "loanAsset"),
    }

    def record(claim_name, values):
        return Record(
            venue=VENUE,
            address=address,
            provenance=addresses[address],
            claim=claim_name,
            values=dict(shared, **values),
            source=source,
            observed_at=at,
            block=block,
        )

    if claim == "liquidation":
        bad_debt = _integer(data, "badDebtAssets", "liquidationData")
        # What was repaid is denominated in the loan asset and what was seized
        # in the collateral asset, and the two have different decimals. Filing
        # both under one scale puts a number in the dossier that can be wrong
        # by twelve orders of magnitude.
        collateral = _require(market, "collateralAsset", "market")
        seized = {
            "seized_collateral": _integer(data, "seizedAssets", "liquidationData")
        }
        if collateral:
            seized["collateral_symbol"] = sanitise.clean(
                _require(collateral, "symbol", "collateralAsset")
            )
            seized["collateral_decimals"] = _integer(
                collateral, "decimals", "collateralAsset"
            )
        out = [
            record(
                "liquidation",
                dict(
                    seized,
                    repaid=_integer(data, "repaidAssets", "liquidationData"),
                    collateralised=True,
                ),
            )
        ]
        if bad_debt > 0:
            # The one thing here that bears on conduct. The collateral did not
            # cover the debt, so lenders lost money, and that deserves its own
            # line rather than a number inside a liquidation.
            out.append(record("bad_debt", {"amount": bad_debt}))
        return out

    return [record(claim, {"amount": _integer(data, "assets", "transferData")})]


def adapter(addresses, config):
    """Run the Morpho Blue venue. Returns (records, coverage)."""
    config = config or {}
    fixtures = config.get("fixtures")

    if fixtures:
        payload = _load_fixture(fixtures)
        items = _require(payload, "items", "fixture")
        if not isinstance(items, list):
            raise MorphoShapeError("items is not a list; the fixture is malformed")
        name = os.path.basename(os.path.normpath(fixtures)) or "unnamed"
        endpoint = "fixture:" + sanitise.clean(name, max_length=60)
        block_range = "fixture"
    else:
        endpoint = endpoints.MORPHO_BLUE_ENDPOINT
        items = _fetch(endpoint, addresses, config.get("timeout", 30))
        block_range = f"{endpoints.MORPHO_BLUE_FIRST_MARKET_BLOCK}-latest"

    records = []
    for item in items:
        records.extend(_records(item, addresses))

    return records, Coverage(
        venue=VENUE,
        status="checked" if records else "empty",
        endpoint=endpoint,
        block_range=block_range,
        note=(
            # Mainnet only. Morpho runs on other chains and this adapter does
            # not look at them, so the row says which chain it speaks for
            # rather than letting a reader assume all of them.
            f"ethereum mainnet only; {len(records)} record(s) across "
            f"{len(addresses)} address(es)"
            if records
            else "ethereum mainnet only; no borrowing activity found for any "
            "subject address"
        ),
    )
