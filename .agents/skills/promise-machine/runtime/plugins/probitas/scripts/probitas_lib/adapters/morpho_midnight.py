"""Morpho Midnight fixed-maturity evidence on Base.

Midnight's v0 API is an evolving, API-scoped history rather than an archive
chain proof.  This adapter therefore makes a narrow promise: it exhausts the
unfiltered transaction cursor for every requested address, validates every
documented economic event, reconstructs exact debt units, and reconciles the
result with the current position at the returned index boundary.  Any missing
or ambiguous input raises before a record is returned.

The field mapping below follows the official v0 references observed on
2026-08-28.  Trade subjects are the seller for ``borrow``, the buyer for
``lend``, and the seller for ``exit_lend_secondary``.  The account-attributed
debt-unit mapping for ``exit_borrow_secondary`` remains unproved, so that named
variant fails closed.  Primary exits and collateral actions use ``on_behalf``;
liquidations use ``borrower``.  Lend and collateral events are known,
validated, and deliberately ignored because they do not describe the
subject's debt.  An event outside this closed vocabulary is never ignored.
"""

from collections import defaultdict
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from .. import endpoints, sanitise
from ..evidence import Coverage, PROVENANCE_TIERS, Record

VENUE = "morpho-midnight"
CHAIN_ID = 8453
PAGE_SIZE = 1000
MAX_PAGES = 200
MAX_CURSOR_LENGTH = 4096
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_FIXTURE_BYTES = 8 * 1024 * 1024
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 100_000
MAX_HTTP_REQUESTS = 1_000
MAX_COLLECTION_SECONDS = 120
MAX_TIMESTAMP = 253_402_300_799
MAX_MARKETS = 500
MAX_SUBJECTS = 100
MAX_UINT256 = (1 << 256) - 1

EVENT_TYPES = frozenset(
    {
        "borrow",
        "lend",
        "exit_lend_primary",
        "exit_lend_secondary",
        "exit_borrow_primary",
        "exit_borrow_secondary",
        "partial_liquidation",
        "full_liquidation",
        "withdraw_collateral",
        "supply_collateral",
    }
)

# These variants are still parsed and attributed before being ignored.  The
# reasons are local because accepting or dropping a variant is reversible
# adapter policy, not a new protocol decision.
IGNORED = frozenset(
    {
        "lend",  # lending is not the subject's borrowing obligation
        "exit_lend_primary",  # closes lender units, not debt units
        "exit_lend_secondary",  # sells lender units, not debt units
        "withdraw_collateral",  # collateral movement does not change debt
        "supply_collateral",  # collateral movement does not change debt
    }
)

_TRADE_SIDE = {
    "borrow": "seller",
    "lend": "buyer",
    "exit_lend_secondary": "seller",
}
_PRIMARY_OR_COLLATERAL = frozenset(
    {
        "exit_lend_primary",
        "exit_borrow_primary",
        "withdraw_collateral",
        "supply_collateral",
    }
)
_LIQUIDATIONS = frozenset({"partial_liquidation", "full_liquidation"})
_AMBIGUOUS = frozenset(
    {
        # The v0 reference names this variant and a live specimen carries a
        # trade-shaped ``units`` field, but neither establishes that field as
        # the account-attributed debt reduction.  Do not infer from the full
        # trade shape; a documented mapping or stronger source must land first.
        "exit_borrow_secondary"
    }
)
_EVENT_ID = re.compile(
    r"\A(?P<block>[0-9]{10})-[0-9a-fA-F]{5}-[0-9]{6}:[0-9]+\Z"
)
_HEX_32 = re.compile(r"\A0x[0-9a-fA-F]{64}\Z")
_SOURCE_DATE = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


class MidnightShapeError(ValueError):
    """The v0 service did not provide a complete, unambiguous evidence set."""


def _require(mapping, key, where):
    if not isinstance(mapping, dict) or key not in mapping:
        raise MidnightShapeError(f"{where} has no {key!r}; the v0 schema moved")
    return mapping[key]


def _mapping(value, where):
    if not isinstance(value, dict):
        raise MidnightShapeError(f"{where} is not an object")
    return value


def _list(value, where):
    if not isinstance(value, list):
        raise MidnightShapeError(f"{where} is not a list")
    return value


def _text(mapping, key, where, *, maximum=4096):
    value = _require(mapping, key, where)
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
    ):
        raise MidnightShapeError(f"{where}.{key} is not bounded non-empty text")
    return value


def _integer_value(value, where, *, maximum=None):
    if isinstance(value, bool) or isinstance(value, float):
        raise MidnightShapeError(f"{where} is not an exact integer")
    if isinstance(value, str):
        if re.fullmatch(r"[0-9]+", value) is None:
            raise MidnightShapeError(f"{where} is not an exact integer")
        if len(value) > 78:
            raise MidnightShapeError(f"{where} is outside the accepted range")
        integer = int(value)
    elif isinstance(value, int):
        integer = value
    else:
        raise MidnightShapeError(f"{where} is not an exact integer")
    upper = MAX_UINT256 if maximum is None else maximum
    if integer < 0 or integer > upper:
        raise MidnightShapeError(f"{where} is outside the accepted range")
    return integer


def _integer(mapping, key, where, *, maximum=None):
    return _integer_value(
        _require(mapping, key, where), f"{where}.{key}", maximum=maximum
    )


def _signed_integer(mapping, key, where):
    value = _require(mapping, key, where)
    if isinstance(value, bool) or isinstance(value, float):
        raise MidnightShapeError(f"{where}.{key} is not an exact signed integer")
    if isinstance(value, str):
        if re.fullmatch(r"-?[0-9]+", value) is None:
            raise MidnightShapeError(
                f"{where}.{key} is not an exact signed integer"
            )
        if len(value.removeprefix("-")) > 78:
            raise MidnightShapeError(f"{where}.{key} is outside the int256 range")
        integer = int(value)
    elif isinstance(value, int):
        integer = value
    else:
        raise MidnightShapeError(f"{where}.{key} is not an exact signed integer")
    if integer < -(1 << 255) or integer > (1 << 255) - 1:
        raise MidnightShapeError(f"{where}.{key} is outside the int256 range")
    return integer


def _boolean(mapping, key, where):
    value = _require(mapping, key, where)
    if not isinstance(value, bool):
        raise MidnightShapeError(f"{where}.{key} is not boolean")
    return value


def _address_value(value, where):
    if not isinstance(value, str) or re.fullmatch(r"0x[0-9a-fA-F]{40}", value) is None:
        raise MidnightShapeError(f"{where} is not a 20-byte address")
    return value.lower()


def _address(mapping, key, where):
    return _address_value(_require(mapping, key, where), f"{where}.{key}")


def _hex_32(mapping, key, where, label):
    value = _text(mapping, key, where, maximum=66)
    if not _HEX_32.fullmatch(value):
        raise MidnightShapeError(f"{where}.{key} is not a {label}")
    return value.lower()


def _transaction_hash(mapping, key, where):
    return _hex_32(mapping, key, where, "transaction hash")


def _market_id(mapping, key, where):
    return _hex_32(mapping, key, where, "Midnight market id")


def _event_id(mapping, where):
    value = _text(mapping, "id", where, maximum=80)
    match = _EVENT_ID.fullmatch(value)
    if match is None:
        raise MidnightShapeError(f"{where}.id is not a documented event id")
    return value, int(match.group("block"))


def _trade_data(data, where):
    for key in (
        "account",
        "caller",
        "maker",
        "taker",
        "buyer",
        "seller",
        "payer",
        "receiver",
    ):
        _address(data, key, where)
    for key in (
        "buyer_assets",
        "seller_assets",
        "assets",
        "units",
        "take_units",
        "buyer_pending_fee_increase",
        "seller_pending_fee_decrease",
        "consumed",
    ):
        _integer(data, key, where)
    # EventsLib.Take declares this full-trade field as int256.  It is not the
    # account-attributed debt delta, but a negative value is still a valid
    # response shape and must not make an otherwise known event disappear.
    _signed_integer(data, "total_units_delta", where)
    _hex_32(data, "group", where, "group id")


def _primary_data(data, where, kind):
    _address(data, "caller", where)
    _address(data, "on_behalf", where)
    _integer(data, "units", where)
    if kind == "exit_borrow_primary":
        _address(data, "payer", where)
    else:
        _address(data, "receiver", where)
        _integer(data, "pending_fee_decrease", where)


def _collateral_data(data, where, kind):
    _address(data, "caller", where)
    _address(data, "on_behalf", where)
    _address(data, "collateral", where)
    _integer(data, "assets", where)
    if kind == "withdraw_collateral":
        _address(data, "receiver", where)


def _liquidation_data(data, where):
    for key in ("caller", "borrower", "collateral", "payer", "receiver"):
        _address(data, key, where)
    for key in (
        "seized_assets",
        "repaid_units",
        "bad_debt",
        "latest_loss_factor",
        "latest_continuous_fee_credit",
    ):
        _integer(data, key, where)
    _boolean(data, "post_maturity_mode", where)
    _boolean(data, "pure_bad_debt_realization", where)


def _json_complexity(value, where):
    stack = [(value, 1)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise MidnightShapeError(f"{where} exceeds the JSON item ceiling")
        if depth > MAX_JSON_DEPTH:
            raise MidnightShapeError(f"{where} exceeds the JSON depth ceiling")
        if isinstance(item, dict):
            stack.extend((key, depth + 1) for key in item)
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MidnightShapeError("JSON object repeats a field name")
        result[key] = value
    return result


def _json_integer(value):
    if len(value.removeprefix("-")) > 78:
        raise MidnightShapeError("JSON integer exceeds the uint256 digit ceiling")
    return int(value)


def _json_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise MidnightShapeError("JSON contains a non-finite numeric value")
    return number


def _json_constant(_value):
    raise MidnightShapeError("JSON contains a non-standard numeric constant")


def _decode_json(raw, where):
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_json_object,
            parse_int=_json_integer,
            parse_float=_json_float,
            parse_constant=_json_constant,
        )
    except MidnightShapeError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise MidnightShapeError(f"{where} is not valid bounded JSON") from error
    _json_complexity(value, where)
    return value


def _locked_origin():
    origin = endpoints.MORPHO_API_ORIGIN
    parsed = urllib.parse.urlsplit(origin)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.morpho.org"
        or parsed.port is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise MidnightShapeError("Morpho API origin is not the locked HTTPS origin")
    if endpoints.MORPHO_MIDNIGHT_ENDPOINT != origin + "/v0/midnight":
        raise MidnightShapeError("Morpho Midnight endpoint left the locked origin")
    return origin


def _url(*segments, query=None, token_selector=False):
    origin = _locked_origin()
    encoded = []
    for segment in segments:
        safe = ":" if token_selector else ""
        encoded.append(urllib.parse.quote(str(segment), safe=safe))
    url = origin + "/" + "/".join(encoded)
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "api.morpho.org":
        raise MidnightShapeError("Morpho request escaped the locked origin")
    return url


def _market_url(market_id):
    return _url("v0", "midnight", "markets", market_id)


def _token_url(token):
    return _url("v0", "tokens", f"{CHAIN_ID}:{token}", token_selector=True)


def _position_url(market_id, subject):
    return _url(
        "v0",
        "midnight",
        "markets",
        market_id,
        "users",
        subject,
        "position",
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MidnightShapeError(f"Morpho API redirected unexpectedly ({code})")


_OPENER = urllib.request.build_opener(_NoRedirect())


class _RequestBudget:
    def __init__(self, timeout):
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise MidnightShapeError("timeout must be a positive number")
        if (
            (isinstance(timeout, float) and not math.isfinite(timeout))
            or timeout <= 0
            or timeout > MAX_COLLECTION_SECONDS
        ):
            raise MidnightShapeError("timeout is outside the accepted range")
        self.per_request = float(timeout)
        self.deadline = time.monotonic() + MAX_COLLECTION_SECONDS
        self.requests = 0
        self.bytes = 0

    def next_timeout(self):
        self.requests += 1
        if self.requests > MAX_HTTP_REQUESTS:
            raise MidnightShapeError("Morpho collection exceeded its request ceiling")
        return min(self.per_request, self.remaining())

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise MidnightShapeError("Morpho collection exceeded its time ceiling")
        return remaining

    def consume(self, size):
        self.bytes += size
        if self.bytes > MAX_TOTAL_BYTES:
            raise MidnightShapeError("Morpho collection exceeded its total byte ceiling")


def _request_json(url, budget, stage):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Probitas/1.0 (+https://github.com/wildcat-finance/skills)",
        },
        method="GET",
    )
    try:
        with _OPENER.open(request, timeout=budget.next_timeout()) as response:
            status = response.getcode()
            if status != 200:
                raise MidnightShapeError(
                    f"Morpho {stage} request returned status {status}"
                )
            content_type = response.headers.get("Content-Type", "")
            if content_type.split(";", 1)[0].strip().lower() != "application/json":
                raise MidnightShapeError(
                    f"Morpho {stage} response is not application/json"
                )
            length = response.headers.get("Content-Length")
            if length is not None:
                if not isinstance(length, str) or re.fullmatch(r"[0-9]+", length) is None:
                    raise MidnightShapeError(
                        f"Morpho {stage} Content-Length is malformed"
                    )
                if (
                    len(length) > len(str(MAX_RESPONSE_BYTES))
                    or int(length) > MAX_RESPONSE_BYTES
                ):
                    raise MidnightShapeError(
                        f"Morpho {stage} response exceeds the byte ceiling"
                    )
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            budget.remaining()
    except MidnightShapeError:
        raise
    except urllib.error.HTTPError as error:
        raise MidnightShapeError(
            f"Morpho {stage} request returned status {error.code}"
        ) from error
    except (TimeoutError, urllib.error.URLError) as error:
        name = "timeout" if isinstance(error, TimeoutError) else "transport error"
        raise MidnightShapeError(f"Morpho {stage} request failed: {name}") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise MidnightShapeError(f"Morpho {stage} response exceeds the byte ceiling")
    budget.consume(len(raw))
    value = _decode_json(raw, f"Morpho {stage} response")
    budget.remaining()
    return value


def _page(value, where):
    page = _mapping(value, where)
    data = _list(_require(page, "data", where), f"{where}.data")
    if len(data) > PAGE_SIZE:
        raise MidnightShapeError(f"{where}.data exceeds the documented page size")
    cursor = _require(page, "cursor", where)
    if cursor is not None and (
        not isinstance(cursor, str)
        or not cursor
        or len(cursor) > MAX_CURSOR_LENGTH
    ):
        raise MidnightShapeError(f"{where}.cursor is not a usable cursor")
    return data, cursor


class _LiveSource:
    def __init__(self, timeout):
        self.budget = _RequestBudget(timeout)
        self.observed_at = int(time.time())
        self.endpoint = endpoints.MORPHO_MIDNIGHT_ENDPOINT

    def transactions(self, subject):
        rows = []
        seen_cursors = set()
        cursor = None
        for page_number in range(MAX_PAGES):
            query = [
                ("chain_ids", str(CHAIN_ID)),
                ("sort_direction", "asc"),
                ("limit", str(PAGE_SIZE)),
            ]
            if cursor is not None:
                query.append(("cursor", cursor))
            url = _url(
                "v0", "midnight", "users", subject, "transactions", query=query
            )
            data, next_cursor = _page(
                _request_json(url, self.budget, "transactions"),
                f"transactions page {page_number}",
            )
            rows.extend(data)
            if next_cursor is None:
                return rows, page_number + 1
            if next_cursor in seen_cursors:
                raise MidnightShapeError("transactions pagination repeated a cursor")
            seen_cursors.add(next_cursor)
            cursor = next_cursor
        raise MidnightShapeError(
            f"transactions did not terminate after {MAX_PAGES} pages"
        )

    def market(self, market_id):
        return _request_json(_market_url(market_id), self.budget, "market")

    def token(self, token):
        return _request_json(
            _token_url(token),
            self.budget,
            "token",
        )

    def position(self, market_id, subject):
        return _request_json(
            _position_url(market_id, subject),
            self.budget,
            "position",
        )

    def complete(self):
        self.budget.remaining()


def _read_fixture(directory):
    path = os.path.join(directory, "morpho-midnight.json")
    try:
        size = os.path.getsize(path)
    except OSError as error:
        raise MidnightShapeError("Morpho Midnight fixture file is missing") from error
    if size > MAX_FIXTURE_BYTES:
        raise MidnightShapeError("Morpho Midnight fixture exceeds the byte ceiling")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_FIXTURE_BYTES + 1)
    except OSError as error:
        raise MidnightShapeError("Morpho Midnight fixture could not be read") from error
    if len(raw) > MAX_FIXTURE_BYTES:
        raise MidnightShapeError("Morpho Midnight fixture exceeds the byte ceiling")
    return _mapping(_decode_json(raw, "Morpho Midnight fixture"), "fixture")


class _FixtureSource:
    def __init__(self, directory):
        payload = _read_fixture(directory)
        source = _mapping(_require(payload, "source", "fixture"), "fixture.source")
        source_date = _text(source, "date", "fixture.source", maximum=10)
        if _SOURCE_DATE.fullmatch(source_date) is None:
            raise MidnightShapeError("fixture.source.date is not YYYY-MM-DD")
        if _text(source, "origin", "fixture.source") != _locked_origin():
            raise MidnightShapeError("fixture source is not the locked Morpho origin")
        self.observed_at = _integer(
            source, "observed_at", "fixture.source", maximum=MAX_TIMESTAMP
        )
        self._transactions = _mapping(
            _require(payload, "transactions", "fixture"), "fixture.transactions"
        )
        self._markets = _mapping(
            _require(payload, "markets", "fixture"), "fixture.markets"
        )
        self._tokens = _mapping(
            _require(payload, "tokens", "fixture"), "fixture.tokens"
        )
        self._positions = _mapping(
            _require(payload, "positions", "fixture"), "fixture.positions"
        )
        name = os.path.basename(os.path.normpath(directory)) or "unnamed"
        self.endpoint = "fixture:" + sanitise.clean(name, max_length=60)

    def transactions(self, subject):
        if subject not in self._transactions:
            raise MidnightShapeError(
                "fixture transactions have no requested subject"
            )
        pages = _list(
            self._transactions[subject],
            "fixture transaction pages",
        )
        rows = []
        seen_cursors = set()
        for page_number, raw in enumerate(pages):
            if page_number >= MAX_PAGES:
                raise MidnightShapeError(
                    f"transactions did not terminate after {MAX_PAGES} pages"
                )
            data, cursor = _page(raw, f"fixture transactions page {page_number}")
            rows.extend(data)
            if cursor is None:
                if page_number != len(pages) - 1:
                    raise MidnightShapeError(
                        "fixture provides pages after a terminal transaction cursor"
                    )
                return rows, page_number + 1
            if cursor in seen_cursors:
                raise MidnightShapeError("transactions pagination repeated a cursor")
            seen_cursors.add(cursor)
        raise MidnightShapeError("fixture transaction cursor did not terminate")

    def market(self, market_id):
        return _require(self._markets, market_id, "fixture.markets")

    def token(self, token):
        key = f"{CHAIN_ID}:{token}"
        if key not in self._tokens:
            raise MidnightShapeError("fixture tokens have no requested loan token")
        return self._tokens[key]

    def position(self, market_id, subject):
        key = f"{market_id}:{subject}"
        if key not in self._positions:
            raise MidnightShapeError("fixture positions have no requested subject")
        return self._positions[key]

    def complete(self):
        return None


def _transaction(raw, subject, index):
    where = f"transactions.data[{index}]"
    item = _mapping(raw, where)
    event_id, block = _event_id(item, where)
    if _integer(item, "chain_id", where) != CHAIN_ID:
        raise MidnightShapeError(f"{where}.chain_id is not Base 8453")
    market_id = _market_id(item, "market_id", where)
    kind = _text(item, "event_type", where, maximum=40)
    if kind not in EVENT_TYPES:
        raise MidnightShapeError(
            "unknown Midnight event type; refusing to drop it silently"
        )
    tx_hash = _transaction_hash(item, "tx_hash", where)
    created_at = _integer(item, "created_at", where, maximum=MAX_TIMESTAMP)
    data = _mapping(_require(item, "data", where), f"{where}.data")
    account = _address(data, "account", f"{where}.data")
    if account != subject:
        raise MidnightShapeError(f"{where}.data.account is not the requested subject")
    if kind in _AMBIGUOUS:
        raise MidnightShapeError(
            "exit_borrow_secondary has no proven account-attributed debt-unit "
            "mapping; refusing an ambiguous secondary close"
        )

    if kind in _TRADE_SIDE:
        _trade_data(data, f"{where}.data")
        buyer = _address(data, "buyer", f"{where}.data")
        seller = _address(data, "seller", f"{where}.data")
        if buyer == seller:
            raise MidnightShapeError(f"{where} has an ambiguous same-account trade")
        expected = buyer if _TRADE_SIDE[kind] == "buyer" else seller
        if expected != subject:
            raise MidnightShapeError(
                f"{where}.{_TRADE_SIDE[kind]} is not the requested subject"
            )
    elif kind in _PRIMARY_OR_COLLATERAL:
        if kind.startswith("exit_"):
            _primary_data(data, f"{where}.data", kind)
        else:
            _collateral_data(data, f"{where}.data", kind)
        if _address(data, "on_behalf", f"{where}.data") != subject:
            raise MidnightShapeError(f"{where}.data.on_behalf is not the subject")
    elif kind in _LIQUIDATIONS:
        _liquidation_data(data, f"{where}.data")
        if _address(data, "borrower", f"{where}.data") != subject:
            raise MidnightShapeError(f"{where}.data.borrower is not the subject")

    shared = {
        "event_id": event_id,
        "block": block,
        "market": market_id,
        "kind": kind,
        "source": tx_hash,
        "created_at": created_at,
        "delta": None,
        "claim": None,
        "mode": None,
        "values": {},
    }
    if kind in {"borrow", "lend", "exit_lend_secondary"}:
        units = _integer(data, "units", f"{where}.data")
        assets = _integer(data, "assets", f"{where}.data")
        if units == 0:
            raise MidnightShapeError(f"{where}.data.units is zero")
        if kind == "borrow":
            shared.update(
                delta=units,
                claim="borrow",
                values={"amount": assets, "debt_units": units},
            )
    elif kind in {"exit_borrow_primary", "exit_lend_primary"}:
        units = _integer(data, "units", f"{where}.data")
        if units == 0:
            raise MidnightShapeError(f"{where}.data.units is zero")
        if kind == "exit_borrow_primary":
            shared.update(
                delta=-units,
                claim="repayment",
                mode="primary_repayment",
                values={"debt_units": units},
            )
    elif kind in _LIQUIDATIONS:
        repaid = _integer(data, "repaid_units", f"{where}.data")
        seized = _integer(data, "seized_assets", f"{where}.data")
        collateral = _address(data, "collateral", f"{where}.data")
        post_maturity = _boolean(data, "post_maturity_mode", f"{where}.data")
        bad_debt = _integer(data, "bad_debt", f"{where}.data")
        pure_bad_debt = _boolean(
            data, "pure_bad_debt_realization", f"{where}.data"
        )
        if repaid == 0 and bad_debt == 0:
            raise MidnightShapeError(
                f"{where}.data liquidation has no debt-unit reduction"
            )
        expected_pure_bad_debt = repaid == 0 and seized == 0 and bad_debt > 0
        if pure_bad_debt != expected_pure_bad_debt:
            raise MidnightShapeError(
                f"{where}.data pure_bad_debt_realization is inconsistent"
            )
        # Midnight.liquidate removes realized bad debt before the separately
        # repaid units.  Both quantities therefore reduce this borrower's debt.
        debt_reduction = repaid + bad_debt
        shared.update(
            delta=-debt_reduction,
            claim="liquidation",
            mode="liquidation",
            values={
                "repaid_debt_units": repaid,
                "realized_bad_debt_units": bad_debt,
                "seized_collateral": seized,
                "collateral_token": collateral,
                "post_maturity_mode": post_maturity,
                "pure_bad_debt_realization": pure_bad_debt,
                "collateralised": True,
            },
        )
    return shared


def _market(payload, requested):
    row = _mapping(_require(payload, "data", "market response"), "market.data")
    if _integer(row, "chain_id", "market.data") != CHAIN_ID:
        raise MidnightShapeError("market.data.chain_id is not Base 8453")
    market_id = _market_id(row, "market_id", "market.data")
    if market_id != requested:
        raise MidnightShapeError("market response id does not match the request")
    _integer(row, "rcf_threshold", "market.data")
    _address(row, "enter_gate", "market.data")
    _address(row, "liquidator_gate", "market.data")
    collaterals = _list(
        _require(row, "collaterals", "market.data"), "market.data.collaterals"
    )
    collateral_tokens = set()
    for index, raw in enumerate(collaterals):
        item = _mapping(raw, f"market.data.collaterals[{index}]")
        token = _address(item, "token", f"market.data.collaterals[{index}]")
        if token in collateral_tokens:
            raise MidnightShapeError("market contains duplicate collateral tokens")
        collateral_tokens.add(token)
        _integer(item, "lltv", f"market.data.collaterals[{index}]")
        _integer(item, "liquidation_cursor", f"market.data.collaterals[{index}]")
        _address(item, "oracle", f"market.data.collaterals[{index}]")
    return {
        "market": market_id,
        "loan_token": _address(row, "loan_token", "market.data"),
        "maturity": _integer(
            row, "maturity", "market.data", maximum=MAX_TIMESTAMP
        ),
    }


def _token(payload, requested):
    row = _mapping(_require(payload, "data", "token response"), "token.data")
    if _integer(row, "chain_id", "token.data") != CHAIN_ID:
        raise MidnightShapeError("token.data.chain_id is not Base 8453")
    address = _address(row, "address", "token.data")
    if address != requested:
        raise MidnightShapeError("token response address does not match the request")
    name = sanitise.clean(_text(row, "name", "token.data"))
    symbol = sanitise.clean(_text(row, "symbol", "token.data"))
    if not name or not symbol:
        raise MidnightShapeError("token metadata is empty after sanitisation")
    return {
        "token": address,
        "token_name": name,
        "token_symbol": symbol,
        "token_decimals": _integer(
            row, "decimals", "token.data", maximum=255
        ),
    }


def _position(payload, subject, market):
    row = _mapping(
        _require(payload, "data", "position response"), "position.data"
    )
    if _integer(row, "chain_id", "position.data") != CHAIN_ID:
        raise MidnightShapeError("position.data.chain_id is not Base 8453")
    if _market_id(row, "market_id", "position.data") != market["market"]:
        raise MidnightShapeError("position response market id does not match")
    if _address(row, "user_address", "position.data") != subject:
        raise MidnightShapeError("position response subject does not match")
    if _address(row, "loan_token", "position.data") != market["loan_token"]:
        raise MidnightShapeError("position and market loan token disagree")
    if _integer(row, "maturity", "position.data") != market["maturity"]:
        raise MidnightShapeError("position and market maturity disagree")

    position_type = _require(row, "type", "position.data")
    if position_type not in (None, "borrow", "lend", "collateral_only"):
        raise MidnightShapeError("position.data.type is undocumented")
    credit = _integer(row, "credit", "position.data")
    debt = _integer(row, "debt", "position.data")
    _integer(row, "pending_fee", "position.data")
    _integer(row, "last_loss_factor", "position.data")
    _integer(row, "loss_factor", "position.data")
    collaterals = _list(
        _require(row, "collaterals", "position.data"),
        "position.data.collaterals",
    )
    collateral_tokens = set()
    for index, raw in enumerate(collaterals):
        item = _mapping(raw, f"position.data.collaterals[{index}]")
        token = _address(item, "token", f"position.data.collaterals[{index}]")
        if token in collateral_tokens:
            raise MidnightShapeError("position contains duplicate collateral tokens")
        collateral_tokens.add(token)
        _integer(item, "amount", f"position.data.collaterals[{index}]")

    if position_type == "borrow" and (debt == 0 or credit != 0):
        raise MidnightShapeError("borrow position has ambiguous debt and credit")
    if position_type == "lend" and (credit == 0 or debt != 0):
        raise MidnightShapeError("lend position has ambiguous debt and credit")
    if position_type == "collateral_only" and (
        debt != 0 or credit != 0 or not collaterals
    ):
        raise MidnightShapeError("collateral-only position is inconsistent")
    if position_type is None and (debt != 0 or credit != 0 or collaterals):
        raise MidnightShapeError("closed position is not actually empty")

    return {
        "debt": debt,
        "credit": credit,
        "position_type": position_type or "closed",
        "collateral_count": len(collaterals),
        "last_indexed_block": _integer(
            row, "last_indexed_block", "position.data"
        ),
    }


def _settlement_mode(events, after, through):
    modes = {
        event["mode"]
        for event in events
        if event["mode"] is not None
        and event["created_at"] > after
        and event["created_at"] <= through
    }
    if not modes:
        return "unsettled"
    if len(modes) == 1:
        return next(iter(modes))
    return "mixed"


def _records_for_market(subject, provenance, events, market, token, position, observed_at):
    maturity = market["maturity"]
    for event in events:
        if event["created_at"] > observed_at:
            raise MidnightShapeError("transaction timestamp is after observation time")
        if event["kind"] == "borrow" and event["created_at"] > maturity:
            raise MidnightShapeError("debt increased after market maturity")
        if event["kind"] in _LIQUIDATIONS:
            if (
                event["values"]["post_maturity_mode"]
                and event["created_at"] <= maturity
            ):
                raise MidnightShapeError(
                    "liquidation post_maturity_mode precedes immutable maturity"
                )

    ordered = sorted(events, key=lambda item: (item["created_at"], item["event_id"]))
    grouped = defaultdict(list)
    for event in ordered:
        grouped[event["created_at"]].append(event)

    balance = 0
    maturity_balance = 0
    determining = None
    for created_at in sorted(grouped):
        group = grouped[created_at]
        balance += sum(event["delta"] for event in group)
        if balance < 0:
            raise MidnightShapeError(
                f"debt-unit balance became negative at {created_at}"
            )
        determining = group[-1]
        if created_at <= maturity:
            maturity_balance = balance

    if position["last_indexed_block"] < max(event["block"] for event in events):
        raise MidnightShapeError(
            "current position was indexed before the transaction evidence"
        )
    if position["debt"] != balance:
        raise MidnightShapeError(
            "current position debt disagrees with reconstructed debt units"
        )

    if observed_at < maturity:
        obligation_state = "not_due"
        observation_state = "not_due"
        debt_at_maturity = None
        mode_after = -1
        through = observed_at
    elif maturity_balance == 0:
        obligation_state = "cleared_by_maturity"
        observation_state = "cleared"
        debt_at_maturity = 0
        mode_after = -1
        through = maturity
        due_events = [event for event in ordered if event["created_at"] <= maturity]
        determining = due_events[-1]
    else:
        obligation_state = "outstanding_at_maturity"
        debt_at_maturity = maturity_balance
        if balance == 0:
            observation_state = "settled_late"
        else:
            observation_state = "outstanding"
        mode_after = maturity
        through = observed_at

    outcome_common = {
        "chain_id": CHAIN_ID,
        "market": market["market"],
        "loan_token": token["token"],
        "token_name": token["token_name"],
        "token_symbol": token["token_symbol"],
        "token_decimals": token["token_decimals"],
        "maturity": maturity,
    }
    records = [
        Record(
            venue=VENUE,
            address=subject,
            provenance=provenance,
            claim="market_terms",
            values={
                "chain_id": CHAIN_ID,
                "market": market["market"],
                "loan_token": market["loan_token"],
                "maturity": maturity,
            },
            source=_market_url(market["market"]),
            observed_at=observed_at,
        ),
        Record(
            venue=VENUE,
            address=subject,
            provenance=provenance,
            claim="token_metadata",
            values={
                "chain_id": CHAIN_ID,
                "token": token["token"],
                "token_name": token["token_name"],
                "token_symbol": token["token_symbol"],
                "token_decimals": token["token_decimals"],
            },
            source=_token_url(token["token"]),
            observed_at=observed_at,
        ),
        Record(
            venue=VENUE,
            address=subject,
            provenance=provenance,
            claim="position_state",
            values={
                "chain_id": CHAIN_ID,
                "market": market["market"],
                "loan_token": market["loan_token"],
                "maturity": maturity,
                "current_position_type": position["position_type"],
                "current_credit": position["credit"],
                "current_debt_units": position["debt"],
                "current_collateral_count": position["collateral_count"],
                "last_indexed_block": position["last_indexed_block"],
            },
            source=_position_url(market["market"], subject),
            observed_at=observed_at,
            block=position["last_indexed_block"],
        ),
    ]
    for event in ordered:
        records.append(
            Record(
                venue=VENUE,
                address=subject,
                provenance=provenance,
                claim=event["claim"],
                values=dict(
                    chain_id=CHAIN_ID,
                    market=market["market"],
                    event_type=event["kind"],
                    debt_units_delta=event["delta"],
                    **event["values"],
                ),
                source=event["source"],
                observed_at=event["created_at"],
                block=event["block"],
            )
        )
    records.append(
        Record(
            venue=VENUE,
            address=subject,
            provenance=provenance,
            claim="maturity_outcome",
            values=dict(
                outcome_common,
                obligation_state=obligation_state,
                observation_state=observation_state,
                settlement_mode=_settlement_mode(ordered, mode_after, through),
                debt_units_at_maturity=debt_at_maturity,
                debt_units_at_observation=balance,
                contributing_records=len(ordered) + 3,
                determining_transaction=determining["source"],
                determining_event_id=determining["event_id"],
                last_indexed_block=position["last_indexed_block"],
            ),
            source=determining["source"],
            observed_at=observed_at,
            block=determining["block"],
        )
    )
    return records


def _collect(addresses, config, state):
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise MidnightShapeError("adapter config is not a mapping")
    if not isinstance(addresses, dict):
        raise MidnightShapeError("subject addresses are not a mapping")
    state["expected_walks"] = len(addresses)
    subjects = {}
    for raw, provenance in addresses.items():
        subject = _address_value(raw, "subject address")
        if provenance not in PROVENANCE_TIERS:
            raise MidnightShapeError("subject provenance tier is invalid")
        if subject in subjects and subjects[subject] != provenance:
            raise MidnightShapeError("one subject address has conflicting provenance")
        subjects[subject] = provenance
    if not subjects:
        raise MidnightShapeError("at least one subject address is required")
    if len(subjects) > MAX_SUBJECTS:
        raise MidnightShapeError("subject address count exceeds the ceiling")
    state["expected_walks"] = len(subjects)

    fixtures = config.get("fixtures")
    if fixtures is not None and (
        not isinstance(fixtures, str) or not fixtures
    ):
        raise MidnightShapeError("fixture source is not a non-empty path string")
    source = (
        _FixtureSource(fixtures)
        if fixtures
        else _LiveSource(config.get("timeout", 30))
    )
    state["observed_at"] = source.observed_at

    events_by_subject = {}
    total_pages = 0
    for subject in sorted(subjects):
        raw_events, pages = source.transactions(subject)
        state["exhausted_walks"] += 1
        total_pages += pages
        seen_ids = set()
        parsed = []
        for index, raw in enumerate(raw_events):
            event = _transaction(raw, subject, index)
            if event["event_id"] in seen_ids:
                raise MidnightShapeError(
                    f"duplicate transaction event id {event['event_id']!r}"
                )
            seen_ids.add(event["event_id"])
            if event["delta"] is not None:
                parsed.append(event)
        events_by_subject[subject] = parsed

    markets = {
        event["market"]
        for events in events_by_subject.values()
        for event in events
    }
    if len(markets) > MAX_MARKETS:
        raise MidnightShapeError("Midnight history exceeds the market ceiling")

    market_cache = {}
    token_cache = {}
    for market_id in sorted(markets):
        market = _market(source.market(market_id), market_id)
        market_cache[market_id] = market
        token = market["loan_token"]
        if token not in token_cache:
            token_cache[token] = _token(source.token(token), token)

    records = []
    index_boundaries = []
    for subject in sorted(subjects):
        by_market = defaultdict(list)
        for event in events_by_subject[subject]:
            by_market[event["market"]].append(event)
        for market_id in sorted(by_market):
            events = by_market[market_id]
            if not any(event["kind"] == "borrow" for event in events):
                raise MidnightShapeError(
                    f"debt reductions have no recorded borrow in {market_id}"
                )
            market = market_cache[market_id]
            position = _position(
                source.position(market_id, subject), subject, market
            )
            index_boundaries.append(position["last_indexed_block"])
            state["index_boundaries"].append(position["last_indexed_block"])
            records.extend(
                _records_for_market(
                    subject,
                    subjects[subject],
                    events,
                    market,
                    token_cache[market["loan_token"]],
                    position,
                    source.observed_at,
                )
            )

    if index_boundaries:
        block_range = f"unpublished-{min(index_boundaries)}"
        index_note = f"returned index through block {min(index_boundaries)}"
    else:
        block_range = "unpublished-unavailable"
        index_note = "no returned index boundary because no debt market was found"
    note = (
        f"Base chain id {CHAIN_ID}; all {len(subjects)} user transaction cursor "
        f"walk(s) exhausted across {total_pages} page(s); observed_at="
        f"{source.observed_at}; {index_note}; API history lower bound unpublished; "
        "API-scoped history only, not archive-chain completeness; "
        f"{len(records)} record(s)"
    )
    source.complete()
    return records, Coverage(
        venue=VENUE,
        status="checked" if records else "empty",
        endpoint=source.endpoint,
        block_range=block_range,
        note=note,
        records=len(records),
    )


def adapter(addresses, config):
    """Run the Base-only Midnight adapter. Returns ``(records, coverage)``."""
    state = {
        "expected_walks": len(addresses) if isinstance(addresses, dict) else 0,
        "exhausted_walks": 0,
        "observed_at": "unavailable",
        "index_boundaries": [],
    }
    try:
        return _collect(addresses, config, state)
    except MidnightShapeError as error:
        boundaries = state["index_boundaries"]
        boundary = min(boundaries) if boundaries else "unavailable"
        raise MidnightShapeError(
            f"Base chain id {CHAIN_ID}; cursor_walks_exhausted="
            f"{state['exhausted_walks']}/{state['expected_walks']}; "
            f"observed_at={state['observed_at']}; "
            f"returned_index_boundary={boundary}; no records emitted; "
            f"refusal: {error}"
        ) from error
