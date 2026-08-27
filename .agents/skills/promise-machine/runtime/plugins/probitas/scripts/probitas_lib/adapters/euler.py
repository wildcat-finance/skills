"""Euler v2 credit events from the keyless V3 Data API.

The public Goldsky subgraph is deliberately a current-state index.  It cannot
tell a borrower who never borrowed from one who borrowed and repaid, so this
adapter does not use it for findings.  The account activity endpoint is an
event ledger with an explicit chain coverage boundary; the liquidation
endpoint supplies the two independently-scaled legs of a liquidation.

Euler accounts are EVC owners with up to 256 subaccounts.  Every finding is
therefore filed under the owner returned by the account-scoped endpoint, while
the subaccount remains in the values attached to the finding.
"""

from collections import defaultdict
from datetime import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .. import endpoints, sanitise
from ..evidence import Coverage, Record

VENUE = "euler"
CHAIN_ID = 1
PAGE = 100
MAX_PAGES = 200
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_CURSOR_LENGTH = 2048

EVENT_TYPES = (
    "borrow",
    "debt_socialized",
    "interest_accrued",
    "liquidation",
    "pull_debt",
    "repay",
)
CLAIMS = {
    "borrow": "borrow",
    "repay": "repayment",
    "debt_socialized": "bad_debt",
    "pull_debt": "borrow",
}
IGNORED = frozenset({"interest_accrued"})
EXPECTED_CATEGORIES = {
    "borrow": "borrowing",
    "repay": "borrowing",
    "interest_accrued": "borrowing",
    "debt_socialized": "borrowing",
    "pull_debt": "borrowing",
    "liquidation": "liquidations",
}


class EulerShapeError(ValueError):
    """The V3 service answered, but not with a complete shape we can cite."""


def _require(mapping, key, where):
    if not isinstance(mapping, dict) or key not in mapping:
        raise EulerShapeError(f"{where} has no {key!r}; the V3 schema moved")
    return mapping[key]


def _mapping(value, where):
    if not isinstance(value, dict):
        raise EulerShapeError(f"{where} is not an object")
    return value


def _list(value, where):
    if not isinstance(value, list):
        raise EulerShapeError(f"{where} is not a list")
    return value


def _text(mapping, key, where):
    value = _require(mapping, key, where)
    if not isinstance(value, str) or not value.strip():
        raise EulerShapeError(f"{where}.{key} is not non-empty text: {value!r}")
    return value


def _integer(mapping, key, where, *, maximum=None):
    value = _require(mapping, key, where)
    if isinstance(value, bool) or isinstance(value, float):
        raise EulerShapeError(f"{where}.{key} is not a whole number: {value!r}")
    if isinstance(value, str):
        if not value.isdigit():
            raise EulerShapeError(f"{where}.{key} is not an integer: {value!r}")
        integer = int(value)
    elif isinstance(value, int):
        integer = value
    else:
        raise EulerShapeError(f"{where}.{key} is not an integer: {value!r}")
    if integer < 0 or (maximum is not None and integer > maximum):
        raise EulerShapeError(f"{where}.{key} is outside the accepted range: {value!r}")
    return integer


def _address_value(value, where):
    if not isinstance(value, str):
        raise EulerShapeError(f"{where} is not an address: {value!r}")
    try:
        return sanitise.address(value)
    except ValueError as error:
        raise EulerShapeError(f"{where} is not an address: {error}") from error


def _address(mapping, key, where):
    return _address_value(_require(mapping, key, where), f"{where}.{key}")


def _hash(mapping, key, where):
    value = _text(mapping, key, where)
    if len(value) != 66 or not value.startswith("0x"):
        raise EulerShapeError(f"{where}.{key} is not a transaction hash: {value!r}")
    try:
        int(value[2:], 16)
    except ValueError as error:
        raise EulerShapeError(
            f"{where}.{key} is not a transaction hash: {value!r}"
        ) from error
    return value.lower()


def _timestamp(mapping, key, where):
    value = _text(mapping, key, where)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise EulerShapeError(f"{where}.{key} is not an ISO timestamp: {value!r}") from error
    if parsed.tzinfo is None:
        raise EulerShapeError(f"{where}.{key} has no timezone: {value!r}")
    return int(parsed.timestamp())


def _subaccount(owner, account, index, where):
    """Check the EVC XOR subaccount relation rather than trusting a label."""
    if index > 255:
        raise EulerShapeError(f"{where}.subAccountIndex exceeds 255")
    owner_bytes = bytes.fromhex(owner[2:])
    account_bytes = bytes.fromhex(account[2:])
    if owner_bytes[:-1] != account_bytes[:-1] or owner_bytes[-1] ^ index != account_bytes[-1]:
        raise EulerShapeError(
            f"{where}.account is not subaccount {index} of owner {owner}"
        )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EulerShapeError(f"Euler V3 redirected unexpectedly ({code})")


def _request_json(path, *, params=None, body=None, timeout=30):
    base = endpoints.EULER_V3_ENDPOINT.rstrip("/")
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    if urllib.parse.urlparse(url).scheme != "https":
        raise EulerShapeError("Euler V3 endpoint must use HTTPS")
    payload = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Accept": "application/json",
        # Euler's edge rejects Python's default urllib user agent even though
        # the V3 API is keyless.  Name the client; no credential is involved.
        "User-Agent": "Probitas/1.0 (+https://github.com/wildcat-finance/skills)",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url,
        data=payload,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            length = response.headers.get("Content-Length")
            if length and length.isdigit() and int(length) > MAX_RESPONSE_BYTES:
                raise EulerShapeError("Euler V3 response is larger than 2 MiB")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
        raise EulerShapeError(f"Euler V3 request failed: {error}") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise EulerShapeError("Euler V3 response is larger than 2 MiB")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EulerShapeError("Euler V3 response is not valid JSON") from error


def _load_fixture(directory, name):
    path = os.path.join(directory, name)
    if not os.path.exists(path):
        raise EulerShapeError(f"no Euler fixture at {path}")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _coverage(page, where):
    meta = _mapping(_require(page, "meta", where), f"{where}.meta")
    if _text(meta, "source", f"{where}.meta") != "v3-ponder":
        raise EulerShapeError(f"{where}.meta.source is not v3-ponder")
    has_more = _require(meta, "hasMore", f"{where}.meta")
    if not isinstance(has_more, bool):
        raise EulerShapeError(f"{where}.meta.hasMore is not boolean")
    cursor = _require(meta, "nextCursor", f"{where}.meta")
    if has_more:
        if not isinstance(cursor, str) or not cursor or len(cursor) > MAX_CURSOR_LENGTH:
            raise EulerShapeError(f"{where}.meta.nextCursor is not a usable cursor")
    elif cursor is not None:
        raise EulerShapeError(f"{where}.meta.nextCursor must be null on the last page")

    coverage = _mapping(_require(meta, "coverage", f"{where}.meta"), f"{where}.meta.coverage")
    if _text(coverage, "status", f"{where}.meta.coverage") != "complete":
        raise EulerShapeError(f"{where}.meta.coverage is not complete")
    if _list(_require(coverage, "missingCategories", f"{where}.meta.coverage"), f"{where}.meta.coverage.missingCategories"):
        raise EulerShapeError(f"{where}.meta.coverage has missing categories")
    chains = _list(_require(coverage, "chains", f"{where}.meta.coverage"), f"{where}.meta.coverage.chains")
    if len(chains) != 1:
        raise EulerShapeError(f"{where}.meta.coverage must contain exactly mainnet")
    chain = _mapping(chains[0], f"{where}.meta.coverage.chains[0]")
    if _integer(chain, "chainId", f"{where}.meta.coverage.chains[0]") != CHAIN_ID:
        raise EulerShapeError(f"{where}.meta.coverage is not Ethereum mainnet")
    if _text(chain, "status", f"{where}.meta.coverage.chains[0]") != "complete":
        raise EulerShapeError(f"{where}.meta.coverage mainnet is not complete")
    if _list(_require(chain, "missingCategories", f"{where}.meta.coverage.chains[0]"), f"{where}.meta.coverage.chains[0].missingCategories"):
        raise EulerShapeError(f"{where}.meta.coverage mainnet has missing categories")
    start = _integer(chain, "indexedFromBlock", f"{where}.meta.coverage.chains[0]")
    end = _integer(chain, "indexedToBlock", f"{where}.meta.coverage.chains[0]")
    if start > end:
        raise EulerShapeError(f"{where}.meta.coverage has a reversed block range")
    return has_more, cursor, start, end


def _fetch_events(addresses, timeout):
    events = []
    ranges = []
    seen_ids = set()
    for owner in sorted(addresses):
        cursor = None
        seen_cursors = set()
        for page_number in range(MAX_PAGES):
            params = {
                "chainId": str(CHAIN_ID),
                "eventType": ",".join(EVENT_TYPES),
                "limit": str(PAGE),
            }
            if cursor is not None:
                params["cursor"] = cursor
            page = _request_json(
                f"/v3/activity/accounts/{owner}/events",
                params=params,
                timeout=timeout,
            )
            data = _list(_require(page, "data", "events response"), "events response.data")
            has_more, next_cursor, start, end = _coverage(page, "events response")
            ranges.append((start, end))
            for item in data:
                event_id = _text(_mapping(item, "event"), "id", "event")
                if event_id in seen_ids:
                    raise EulerShapeError(f"duplicate activity event id {event_id!r}")
                seen_ids.add(event_id)
                events.append(item)
            if not has_more:
                break
            if next_cursor in seen_cursors:
                raise EulerShapeError("activity pagination repeated a cursor")
            seen_cursors.add(next_cursor)
            cursor = next_cursor
        else:
            raise EulerShapeError(
                f"activity did not run out after {MAX_PAGES} pages for {owner}"
            )
    return events, ranges


def _liquidation_meta(page, requested_offset, where):
    meta = _mapping(_require(page, "meta", where), f"{where}.meta")
    total = _integer(meta, "total", f"{where}.meta")
    offset = _integer(meta, "offset", f"{where}.meta")
    limit = _integer(meta, "limit", f"{where}.meta")
    if offset != requested_offset or limit <= 0 or limit > PAGE:
        raise EulerShapeError(f"{where}.meta does not describe the requested page")
    return total, limit


def _fetch_liquidations(violators, timeout):
    rows = []
    for violator in sorted(violators):
        offset = 0
        for _ in range(MAX_PAGES):
            page = _request_json(
                "/v3/liquidations",
                params={
                    "chainId": str(CHAIN_ID),
                    "violator": violator,
                    "limit": str(PAGE),
                    "offset": str(offset),
                },
                timeout=timeout,
            )
            data = _list(_require(page, "data", "liquidations response"), "liquidations response.data")
            total, limit = _liquidation_meta(page, offset, "liquidations response")
            rows.extend(data)
            offset += len(data)
            if offset >= total:
                break
            if not data or len(data) > limit:
                raise EulerShapeError("liquidations pagination made no valid progress")
        else:
            raise EulerShapeError(
                f"liquidations did not run out after {MAX_PAGES} pages for {violator}"
            )
    return rows


def _vault_rows(vaults, timeout):
    rows = []
    wanted = sorted(vaults)
    for offset in range(0, len(wanted), PAGE):
        batch = wanted[offset : offset + PAGE]
        page = _request_json(
            "/v3/evk/vaults/batch",
            body={"chainId": CHAIN_ID, "addresses": batch},
            timeout=timeout,
        )
        rows.extend(_list(_require(page, "data", "vault response"), "vault response.data"))
        meta = _mapping(_require(page, "meta", "vault response"), "vault response.meta")
        missing = _list(_require(meta, "notFound", "vault response.meta"), "vault response.meta.notFound")
        if missing:
            raise EulerShapeError(f"Euler V3 did not resolve vaults: {missing!r}")
    return rows


class _VaultCache:
    def __init__(self, rows, wanted):
        self._rows = {}
        for index, raw in enumerate(rows):
            row = _mapping(raw, f"vaults.data[{index}]")
            if _integer(row, "chainId", f"vaults.data[{index}]") != CHAIN_ID:
                raise EulerShapeError(f"vaults.data[{index}] is not on mainnet")
            vault = _address(row, "address", f"vaults.data[{index}]")
            if vault in self._rows:
                raise EulerShapeError(f"duplicate vault metadata for {vault}")
            asset = _mapping(_require(row, "asset", f"vaults.data[{index}]"), f"vaults.data[{index}].asset")
            self._rows[vault] = {
                "market": vault,
                "market_symbol": sanitise.clean(_text(row, "symbol", f"vaults.data[{index}]")),
                "token": _address(asset, "address", f"vaults.data[{index}].asset"),
                "token_symbol": sanitise.clean(_text(asset, "symbol", f"vaults.data[{index}].asset")),
                "token_decimals": _integer(asset, "decimals", f"vaults.data[{index}].asset", maximum=255),
            }
        missing = sorted(set(wanted) - set(self._rows))
        extra = sorted(set(self._rows) - set(wanted))
        if missing or extra:
            raise EulerShapeError(
                f"vault metadata does not match requested vaults; missing={missing}, extra={extra}"
            )

    def get(self, vault):
        try:
            return self._rows[vault]
        except KeyError as error:
            raise EulerShapeError(f"vault metadata was not cached for {vault}") from error


def _event_common(raw, addresses, index):
    where = f"events.data[{index}]"
    event = _mapping(raw, where)
    _text(event, "id", where)
    if _integer(event, "chainId", where) != CHAIN_ID:
        raise EulerShapeError(f"{where}.chainId is not mainnet")
    kind = _text(event, "type", where)
    if kind not in EXPECTED_CATEGORIES:
        raise EulerShapeError(
            f"unknown borrowing event type {kind!r}; refusing to drop it silently"
        )
    if _text(event, "category", where) != EXPECTED_CATEGORIES[kind]:
        raise EulerShapeError(f"{where}.category does not match {kind}")
    if _text(event, "source", where) != "v3-ponder":
        raise EulerShapeError(f"{where}.source is not v3-ponder")
    owner = _address(event, "owner", where)
    if owner not in addresses:
        raise EulerShapeError(f"{where}.owner {owner} is not a subject address")
    account = _address(event, "account", where)
    sub_index = _integer(event, "subAccountIndex", where, maximum=255)
    _subaccount(owner, account, sub_index, where)
    vault = _address(event, "vault", where)
    if _text(event, "vaultType", where) != "evk":
        raise EulerShapeError(f"{where}.vaultType is not evk")
    return {
        "raw": event,
        "where": where,
        "kind": kind,
        "owner": owner,
        "account": account,
        "sub_index": sub_index,
        "vault": vault,
        "source": _hash(event, "txHash", where),
        "observed_at": _timestamp(event, "timestamp", where),
        "block": _integer(event, "blockNumber", where),
        "log_index": _integer(event, "logIndex", where),
    }


def _asset(event, kind):
    where = event["where"]
    assets = _list(_require(event["raw"], "assets", where), f"{where}.assets")
    found = []
    for index, raw in enumerate(assets):
        item = _mapping(raw, f"{where}.assets[{index}]")
        item_kind = _text(item, "kind", f"{where}.assets[{index}]")
        amount = _integer(item, "amountRaw", f"{where}.assets[{index}]")
        if item_kind == kind:
            found.append((item, amount))
    if len(found) != 1:
        raise EulerShapeError(f"{where}.assets must contain exactly one {kind!r} leg")
    return found[0]


def _liquidation_row(raw, index):
    where = f"liquidations.data[{index}]"
    row = _mapping(raw, where)
    if _integer(row, "chainId", where) != CHAIN_ID:
        raise EulerShapeError(f"{where}.chainId is not mainnet")
    return {
        "raw": row,
        "where": where,
        "vault": _address(row, "vault", where),
        "violator": _address(row, "violator", where),
        "liquidator": _address(row, "liquidator", where),
        "collateral": _address(row, "collateral", where),
        "repay": _integer(row, "repayAssets", where),
        "yield_balance": _integer(row, "yieldBalance", where),
        "debt_asset": _address(row, "debtAsset", where),
        "debt_decimals": _integer(row, "debtAssetDecimals", where, maximum=255),
        "collateral_asset": _address(row, "collateralAsset", where),
        "collateral_decimals": _integer(row, "collateralAssetDecimals", where, maximum=255),
        "collateral_assets": _integer(row, "collateralAssets", where),
        "block": _integer(row, "blockNumber", where),
        "source": _hash(row, "txHash", where),
        "observed_at": _timestamp(row, "timestamp", where),
    }


def _liquidation_key(item):
    return item["source"], item["vault"], item["account"] if "account" in item else item["violator"]


def _records(events, liquidation_rows, vault_cache, addresses):
    rich = defaultdict(list)
    for index, raw in enumerate(liquidation_rows):
        row = _liquidation_row(raw, index)
        rich[_liquidation_key(row)].append(row)

    records = []
    for index, raw in enumerate(events):
        event = _event_common(raw, addresses, index)
        kind = event["kind"]
        if kind in IGNORED:
            continue

        market = dict(vault_cache.get(event["vault"]))
        shared = dict(
            market,
            subaccount=event["account"],
            sub_account_index=event["sub_index"],
        )

        def record(claim, values):
            records.append(
                Record(
                    venue=VENUE,
                    address=event["owner"],
                    provenance=addresses[event["owner"]],
                    claim=claim,
                    values=dict(shared, **values),
                    source=event["source"],
                    observed_at=event["observed_at"],
                    block=event["block"],
                )
            )

        if kind == "liquidation":
            key = _liquidation_key(event)
            _, repaid = _asset(event, "assets")
            collateral_leg, yield_balance = _asset(event, "collateral")
            collateral_address = _address(
                collateral_leg, "address", f"{event['where']}.assets"
            )
            liquidator = _address(event["raw"], "actor", event["where"])
            matching = [
                (position, candidate)
                for position, candidate in enumerate(rich[key])
                if candidate["repay"] == repaid
                and candidate["yield_balance"] == yield_balance
                and candidate["collateral"] == collateral_address
                and candidate["liquidator"] == liquidator
                and candidate["block"] == event["block"]
                and candidate["observed_at"] == event["observed_at"]
            ]
            if not matching:
                raise EulerShapeError(
                    f"no /liquidations row matches {event['source']} log {event['log_index']}"
                )
            if len(matching) != 1:
                raise EulerShapeError(
                    f"multiple /liquidations rows match {event['source']} log {event['log_index']}"
                )
            position, row = matching[0]
            del rich[key][position]
            collateral_meta = vault_cache.get(row["collateral"])
            if (
                row["debt_asset"] != market["token"]
                or row["debt_decimals"] != market["token_decimals"]
                or row["collateral_asset"] != collateral_meta["token"]
                or row["collateral_decimals"] != collateral_meta["token_decimals"]
            ):
                raise EulerShapeError(
                    f"/liquidations and vault metadata disagree for {event['source']}"
                )
            record(
                "liquidation",
                {
                    "repaid": row["repay"],
                    "seized_collateral": row["collateral_assets"],
                    "collateral_vault": row["collateral"],
                    "collateral_token": row["collateral_asset"],
                    "collateral_symbol": collateral_meta["token_symbol"],
                    "collateral_decimals": row["collateral_decimals"],
                    "liquidator": row["liquidator"],
                    "collateralised": True,
                },
            )
            continue

        _, amount = _asset(event, "assets")
        values = {"amount": amount}
        if kind == "pull_debt":
            values["debt_transfer"] = True
            if "counterparty" in event["raw"]:
                values["counterparty"] = _address(event["raw"], "counterparty", event["where"])
        record(CLAIMS[kind], values)

    leftovers = sum(len(rows) for rows in rich.values())
    if leftovers:
        raise EulerShapeError(
            f"/liquidations returned {leftovers} row(s) with no account activity event"
        )
    return records


def adapter(addresses, config):
    """Run the Euler v2 mainnet venue. Returns ``(records, coverage)``."""
    config = config or {}
    fixtures = config.get("fixtures")
    timeout = config.get("timeout", 30)

    if fixtures:
        events_page = _load_fixture(fixtures, "euler-events.json")
        events = _list(_require(events_page, "data", "events fixture"), "events fixture.data")
        has_more, _, start, end = _coverage(events_page, "events fixture")
        if has_more:
            raise EulerShapeError("a fixture cannot claim an unprovided next events page")
        ranges = [(start, end)]
        liquidation_page = _load_fixture(fixtures, "euler-liquidations.json")
        liquidation_rows = _list(
            _require(liquidation_page, "data", "liquidations fixture"),
            "liquidations fixture.data",
        )
        total, _ = _liquidation_meta(liquidation_page, 0, "liquidations fixture")
        if total != len(liquidation_rows):
            raise EulerShapeError("liquidations fixture does not contain its full result")
        vault_page = _load_fixture(fixtures, "euler-vaults.json")
        vault_rows = _list(_require(vault_page, "data", "vault fixture"), "vault fixture.data")
        endpoint = "fixture:" + sanitise.clean(
            os.path.basename(os.path.normpath(fixtures)) or "unnamed", max_length=60
        )
        block_range = "fixture"
    else:
        events, ranges = _fetch_events(addresses, timeout)
        preliminary = [_event_common(raw, addresses, index) for index, raw in enumerate(events)]
        violators = {item["account"] for item in preliminary if item["kind"] == "liquidation"}
        liquidation_rows = _fetch_liquidations(violators, timeout) if violators else []
        rich = [_liquidation_row(raw, index) for index, raw in enumerate(liquidation_rows)]
        vaults = {item["vault"] for item in preliminary}
        vaults.update(item["collateral"] for item in rich)
        vault_rows = _vault_rows(vaults, timeout) if vaults else []
        endpoint = endpoints.EULER_V3_ENDPOINT
        start = max(item[0] for item in ranges)
        end = min(item[1] for item in ranges)
        if start > end:
            raise EulerShapeError("account queries have no common indexed block range")
        block_range = f"{start}-{end}"

    preliminary = [_event_common(raw, addresses, index) for index, raw in enumerate(events)]
    rich = [_liquidation_row(raw, index) for index, raw in enumerate(liquidation_rows)]
    wanted_vaults = {item["vault"] for item in preliminary}
    wanted_vaults.update(item["collateral"] for item in rich)
    cache = _VaultCache(vault_rows, wanted_vaults)
    records = _records(events, liquidation_rows, cache, addresses)

    common_start = max(item[0] for item in ranges)
    common_end = min(item[1] for item in ranges)
    return records, Coverage(
        venue=VENUE,
        status="checked" if records else "empty",
        endpoint=endpoint,
        block_range=block_range,
        note=(
            f"ethereum mainnet V3 event ledger; complete indexed coverage "
            f"{common_start}-{common_end}; "
            f"{len(records)} record(s) across {len(addresses)} EVC owner(s)"
            if records
            else "ethereum mainnet V3 event ledger; complete indexed coverage; "
            "no borrowing activity found for any subject EVC owner"
        ),
    )
