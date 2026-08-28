"""Fail-closed Morpho Midnight fixed-maturity evidence."""

import copy
import json
import os
import tempfile
import unittest
from unittest import mock
import urllib.error

from . import support

from probitas_lib import endpoints  # noqa: E402
from probitas_lib.adapters import run_adapter  # noqa: E402
from probitas_lib.adapters import morpho_midnight as midnight  # noqa: E402
from probitas_lib.adapters.morpho_midnight import (  # noqa: E402
    MidnightShapeError,
    adapter,
)

FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")
SUBJECT = "0x535690cb1330232dd4f2ac5b724040751bdf4c91"
OTHER = "0xd4f43105098845ffe89b16e7a3dcdd0a31898118"
MARKET = "0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738"
TOKEN = "0x4200000000000000000000000000000000000006"
SUBJECTS = {SUBJECT: "declared"}


def fixture(case):
    return os.path.join(FIXTURES, case)


def load(case="midnight-cleared"):
    with open(
        os.path.join(fixture(case), "morpho-midnight.json"), encoding="utf-8"
    ) as handle:
        return json.load(handle)


def collect(case="midnight-cleared", addresses=None):
    return adapter(addresses or SUBJECTS, {"fixtures": fixture(case)})


def outcomes(records):
    return [record for record in records if record.claim == "maturity_outcome"]


class MutationCase(unittest.TestCase):
    def adapt(self, mutate, case="midnight-cleared", addresses=None):
        payload = load(case)
        mutate(payload)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "morpho-midnight.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(payload, handle)
        return adapter(addresses or SUBJECTS, {"fixtures": directory.name})

    def assert_refused(self, mutate, case="midnight-cleared", match=None):
        with self.assertRaises(MidnightShapeError) as caught:
            self.adapt(mutate, case=case)
        if match is not None:
            self.assertIn(match, str(caught.exception))


class TestSourceDatedSpecimens(unittest.TestCase):
    def test_every_specimen_names_its_source_date_and_official_origin(self):
        for case in (
            "midnight-cleared",
            "midnight-late",
            "midnight-not-due",
            "midnight-empty",
        ):
            with self.subTest(case=case):
                source = load(case)["source"]
                self.assertEqual(source["date"], "2026-08-28")
                self.assertEqual(source["origin"], "https://api.morpho.org")
                self.assertEqual(len([key for key in source if key.endswith("_reference")]), 4)

    def test_cleared_includes_the_maturity_second_and_equal_second_group(self):
        records, coverage = collect()
        outcome = outcomes(records)[0]
        self.assertEqual(coverage.status, "checked")
        self.assertEqual(outcome.values["obligation_state"], "cleared_by_maturity")
        self.assertEqual(outcome.values["observation_state"], "cleared")
        self.assertEqual(outcome.values["settlement_mode"], "primary_repayment")
        self.assertEqual(outcome.values["debt_units_at_maturity"], "0")
        self.assertEqual(outcome.values["debt_units_at_observation"], "0")
        self.assertEqual(outcome.values["maturity"], "1784300400")

    def test_late_zero_position_does_not_rewrite_the_due_time_result(self):
        records, _ = collect("midnight-late")
        outcome = outcomes(records)[0]
        self.assertEqual(outcome.values["obligation_state"], "outstanding_at_maturity")
        self.assertEqual(outcome.values["observation_state"], "settled_late")
        self.assertEqual(outcome.values["settlement_mode"], "liquidation")
        self.assertEqual(outcome.values["debt_units_at_maturity"], "136075232067")
        self.assertEqual(outcome.values["debt_units_at_observation"], "0")

    def test_late_outcome_cites_the_determining_liquidation(self):
        records, _ = collect("midnight-late")
        outcome = outcomes(records)[0]
        self.assertEqual(
            outcome.source,
            "0xa542774c5cc03cc7e94a07b392d2de4e27a620f41a3a4f17a025482b1f7e1490",
        )
        self.assertEqual(outcome.values["determining_transaction"], outcome.source)
        self.assertEqual(outcome.values["contributing_records"], "8")

    def test_every_economic_record_cites_a_transaction(self):
        records, _ = collect("midnight-late")
        for record in records:
            if record.claim not in {
                "market_terms",
                "token_metadata",
                "position_state",
                "maturity_outcome",
            }:
                with self.subTest(claim=record.claim):
                    self.assertEqual(record.source_kind, "transaction")

    def test_market_terms_have_the_exact_official_route(self):
        records, _ = collect()
        terms = next(record for record in records if record.claim == "market_terms")
        self.assertEqual(
            terms.source,
            f"https://api.morpho.org/v0/midnight/markets/{MARKET}",
        )
        self.assertEqual(terms.values["maturity"], "1784300400")

    def test_token_and_position_inputs_have_their_own_citations(self):
        records, _ = collect()
        by_claim = {record.claim: record for record in records}
        self.assertEqual(
            by_claim["token_metadata"].source,
            f"https://api.morpho.org/v0/tokens/8453:{TOKEN}",
        )
        self.assertEqual(by_claim["token_metadata"].values["token_decimals"], "18")
        self.assertEqual(
            by_claim["position_state"].source,
            f"https://api.morpho.org/v0/midnight/markets/{MARKET}/users/{SUBJECT}/position",
        )
        self.assertEqual(by_claim["position_state"].values["current_debt_units"], "0")

    def test_transaction_records_keep_only_transaction_native_context(self):
        records, _ = collect()
        event = next(record for record in records if record.claim == "borrow")
        self.assertNotIn("token_name", event.values)
        self.assertNotIn("token_decimals", event.values)
        self.assertNotIn("maturity", event.values)

    def test_not_due_has_no_invented_due_time_balance(self):
        records, _ = collect("midnight-not-due")
        outcome = outcomes(records)[0]
        self.assertEqual(outcome.values["obligation_state"], "not_due")
        self.assertEqual(outcome.values["observation_state"], "not_due")
        self.assertIsNone(outcome.values["debt_units_at_maturity"])
        self.assertEqual(outcome.values["debt_units_at_observation"], "100")

    def test_empty_is_only_empty_after_a_terminal_cursor(self):
        records, coverage = collect("midnight-empty")
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "empty")
        self.assertIn("cursor walk(s) exhausted", coverage.note)
        self.assertIn("no returned index boundary", coverage.note)

    def test_coverage_is_explicitly_api_scoped(self):
        _, coverage = collect("midnight-late")
        self.assertEqual(coverage.block_range, "unpublished-50551562")
        self.assertIn("Base chain id 8453", coverage.note)
        self.assertIn("API history lower bound unpublished", coverage.note)
        self.assertIn("not archive-chain completeness", coverage.note)
        self.assertIn("observed_at=1785374000", coverage.note)

    def test_harmless_extra_market_fields_are_accepted(self):
        records, _ = collect()
        self.assertTrue(records)


class TestVocabularyAndAttribution(MutationCase):
    def ignored_event(self, kind, number):
        common = {
            "id": f"0048754000-ddddd-{number:06d}:1",
            "chain_id": 8453,
            "market_id": MARKET,
            "event_type": kind,
            "tx_hash": "0x" + f"{number:064x}",
            "created_at": 1784290000,
        }
        if kind in {"lend", "exit_lend_secondary"}:
            buyer, seller = (SUBJECT, OTHER) if kind == "lend" else (OTHER, SUBJECT)
            common["data"] = {
                "account": SUBJECT,
                "caller": "0x" + "aa" * 20,
                "maker": SUBJECT,
                "taker": OTHER,
                "buyer": buyer,
                "seller": seller,
                "buyer_assets": "10",
                "seller_assets": "10",
                "assets": "10",
                "units": "10",
                "take_units": "10",
                "buyer_pending_fee_increase": "0",
                "seller_pending_fee_decrease": "0",
                "total_units_delta": "10",
                "payer": SUBJECT,
                "receiver": OTHER,
                "group": "0x" + "ab" * 32,
                "consumed": "10",
            }
        elif kind == "exit_lend_primary":
            common["data"] = {
                "account": SUBJECT,
                "caller": OTHER,
                "on_behalf": SUBJECT,
                "receiver": OTHER,
                "units": "10",
                "pending_fee_decrease": "0",
            }
        else:
            common["data"] = {
                "account": SUBJECT,
                "caller": OTHER,
                "on_behalf": SUBJECT,
                "collateral": "0x" + "83" * 20,
                "assets": "10",
            }
            if kind == "withdraw_collateral":
                common["data"]["receiver"] = OTHER
        return common

    def test_all_named_non_borrow_variants_are_validated_then_ignored(self):
        for number, kind in enumerate(sorted(midnight.IGNORED), start=10):
            with self.subTest(kind=kind):
                records, _ = self.adapt(
                    lambda payload, k=kind, n=number: payload["transactions"][
                        SUBJECT
                    ][0]["data"].append(self.ignored_event(k, n))
                )
                self.assertEqual(len(records), 7)

    def test_an_unknown_type_never_disappears_as_empty(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][0].update(
                event_type="borrow_v2"
            ),
            match="unknown Midnight event type",
        )

    def test_secondary_borrow_close_remains_explicitly_ambiguous(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][0].update(
                event_type="exit_borrow_secondary"
            ),
            match="ambiguous secondary close",
        )

    def test_the_common_account_must_be_the_subject(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][0][
                "data"
            ].update(account=OTHER),
            match="is not subject",
        )

    def test_a_borrow_must_name_the_subject_as_seller(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][0][
                "data"
            ].update(seller="0x" + "ee" * 20),
            match="seller is not subject",
        )

    def test_a_primary_exit_must_name_the_subject_on_behalf(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][2][
                "data"
            ].update(on_behalf=OTHER),
            match="on_behalf is not the subject",
        )

    def test_a_liquidation_must_name_the_subject_as_borrower(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][2][
                "data"
            ].update(borrower=OTHER),
            case="midnight-late",
            match="borrower is not the subject",
        )

    def test_known_ignored_variants_are_still_strict(self):
        def mutate(payload):
            event = self.ignored_event("supply_collateral", 99)
            event["data"]["assets"] = True
            payload["transactions"][SUBJECT][0]["data"].append(event)

        self.assert_refused(mutate, match="not an exact integer")


class TestExactAccounting(MutationCase):
    def test_equal_second_order_does_not_change_the_balance(self):
        def mutate(payload):
            rows = payload["transactions"][SUBJECT][0]["data"]
            rows[1], rows[2] = rows[2], rows[1]

        records, _ = self.adapt(mutate)
        self.assertEqual(outcomes(records)[0].values["debt_units_at_maturity"], "0")

    def test_a_negative_group_end_balance_is_refused(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][2][
                "data"
            ].update(units="121"),
            match="became negative",
        )

    def test_a_debt_increase_after_maturity_is_refused(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][1].update(
                created_at=1784300401
            ),
            match="increased after market maturity",
        )

    def test_liquidation_mode_must_match_the_immutable_maturity(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][2][
                "data"
            ].update(post_maturity_mode=False),
            case="midnight-late",
            match="disagrees with immutable maturity",
        )

    def test_current_position_must_reconcile(self):
        self.assert_refused(
            lambda payload: payload["positions"][f"{MARKET}:{SUBJECT}"][
                "data"
            ].update(type="borrow", debt="1"),
            match="disagrees with reconstructed debt units",
        )

    def test_position_index_must_cover_the_evidence(self):
        self.assert_refused(
            lambda payload: payload["positions"][f"{MARKET}:{SUBJECT}"][
                "data"
            ].update(last_indexed_block="1"),
            match="indexed before the transaction evidence",
        )

    def test_a_future_transaction_is_refused(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][0].update(
                created_at=1785374001
            ),
            case="midnight-not-due",
            match="after observation time",
        )

    def test_reductions_without_a_recorded_borrow_are_refused(self):
        def mutate(payload):
            payload["transactions"][SUBJECT][0]["data"] = [
                payload["transactions"][SUBJECT][0]["data"][2]
            ]

        self.assert_refused(mutate, match="without a recorded borrow")

    def test_float_and_boolean_units_are_never_coerced(self):
        for value in (1.5, True):
            with self.subTest(value=value):
                self.assert_refused(
                    lambda payload, v=value: payload["transactions"][SUBJECT][0][
                        "data"
                    ][0]["data"].update(units=v),
                    match="not an exact integer",
                )

    def test_decimal_and_negative_strings_are_never_coerced(self):
        for value in ("1.0", "-1"):
            with self.subTest(value=value):
                self.assert_refused(
                    lambda payload, v=value: payload["transactions"][SUBJECT][0][
                        "data"
                    ][0]["data"].update(units=v),
                    match="not an exact integer",
                )


class TestStrictSemanticShapes(MutationCase):
    def test_a_missing_semantic_field_is_refused(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0]["data"][0][
                "data"
            ].pop("take_units"),
            match="has no 'take_units'",
        )

    def test_wrong_chain_event_id_market_id_and_hash_are_refused(self):
        mutations = {
            "chain": lambda event: event.update(chain_id=1),
            "event id": lambda event: event.update(id="event-1"),
            "market id": lambda event: event.update(market_id="0xshort"),
            "hash": lambda event: event.update(tx_hash="0xshort"),
        }
        for label, change in mutations.items():
            with self.subTest(label=label):
                self.assert_refused(
                    lambda payload, c=change: c(
                        payload["transactions"][SUBJECT][0]["data"][0]
                    )
                )

    def test_duplicate_event_ids_are_refused(self):
        def mutate(payload):
            rows = payload["transactions"][SUBJECT][0]["data"]
            rows[1]["id"] = rows[0]["id"]

        self.assert_refused(mutate, match="duplicate transaction event id")

    def test_market_chain_id_and_requested_id_are_bound(self):
        for key, value in (("chain_id", 1), ("market_id", "0x" + "ee" * 32)):
            with self.subTest(key=key):
                self.assert_refused(
                    lambda payload, k=key, v=value: payload["markets"][MARKET][
                        "data"
                    ].update({k: v})
                )

    def test_market_immutable_fields_are_required_and_exact(self):
        for key in (
            "maturity",
            "rcf_threshold",
            "enter_gate",
            "liquidator_gate",
            "collaterals",
        ):
            with self.subTest(key=key):
                self.assert_refused(
                    lambda payload, k=key: payload["markets"][MARKET]["data"].pop(k)
                )

    def test_market_duplicate_collateral_is_refused(self):
        def mutate(payload):
            rows = payload["markets"][MARKET]["data"]["collaterals"]
            rows.append(copy.deepcopy(rows[0]))

        self.assert_refused(mutate, match="duplicate collateral tokens")

    def test_token_chain_address_and_decimals_are_bound(self):
        mutations = (
            ("chain_id", 1),
            ("address", "0x" + "ee" * 20),
            ("decimals", True),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                self.assert_refused(
                    lambda payload, k=key, v=value: payload["tokens"][
                        f"8453:{TOKEN}"
                    ]["data"].update({k: v})
                )

    def test_position_chain_market_subject_token_and_maturity_are_bound(self):
        mutations = (
            ("chain_id", 1),
            ("market_id", "0x" + "ee" * 32),
            ("user_address", OTHER),
            ("loan_token", "0x" + "ee" * 20),
            ("maturity", 1),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                self.assert_refused(
                    lambda payload, k=key, v=value: payload["positions"][
                        f"{MARKET}:{SUBJECT}"
                    ]["data"].update({k: v})
                )

    def test_unknown_or_internally_ambiguous_position_types_are_refused(self):
        mutations = (
            {"type": "borrower"},
            {"type": "borrow", "debt": "0"},
            {"type": None, "collaterals": [{"token": OTHER, "amount": "1"}]},
        )
        for change in mutations:
            with self.subTest(change=change):
                self.assert_refused(
                    lambda payload, c=change: payload["positions"][
                        f"{MARKET}:{SUBJECT}"
                    ]["data"].update(c)
                )

    def test_duplicate_position_collateral_is_refused(self):
        def mutate(payload):
            position = payload["positions"][f"{MARKET}:{SUBJECT}"]["data"]
            position["collaterals"] = [
                {"token": OTHER, "amount": "1"},
                {"token": OTHER, "amount": "2"},
            ]
            position["type"] = "collateral_only"

        self.assert_refused(mutate, match="duplicate collateral tokens")


class TestCursorAndFixtureBounds(MutationCase):
    def test_subject_count_is_bounded_before_collection(self):
        subjects = {
            "0x" + f"{index:040x}": "declared"
            for index in range(midnight.MAX_SUBJECTS + 1)
        }
        with self.assertRaisesRegex(MidnightShapeError, "subject address count"):
            adapter(subjects, {"fixtures": fixture("midnight-empty")})

    def test_repeated_cursor_is_refused(self):
        def mutate(payload):
            first = payload["transactions"][SUBJECT][0]
            first["cursor"] = "same"
            payload["transactions"][SUBJECT].append(
                {"cursor": "same", "data": []}
            )

        self.assert_refused(mutate, match="repeated a cursor")

    def test_pages_after_terminal_cursor_are_refused(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT].append(
                {"cursor": None, "data": []}
            ),
            match="pages after a terminal",
        )

    def test_nonterminal_fixture_without_its_next_page_is_refused(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0].update(cursor="next"),
            match="did not terminate",
        )

    def test_cursor_length_is_bounded(self):
        self.assert_refused(
            lambda payload: payload["transactions"][SUBJECT][0].update(
                cursor="x" * (midnight.MAX_CURSOR_LENGTH + 1)
            ),
            match="not a usable cursor",
        )

    def test_page_count_is_bounded(self):
        def mutate(payload):
            first = payload["transactions"][SUBJECT][0]
            first["cursor"] = "next"
            payload["transactions"][SUBJECT].append({"cursor": None, "data": []})

        with mock.patch.object(midnight, "MAX_PAGES", 1):
            self.assert_refused(mutate, match="did not terminate after 1 pages")

    def test_page_item_count_is_bounded(self):
        with mock.patch.object(midnight, "PAGE_SIZE", 2):
            self.assert_refused(lambda payload: None, match="exceeds")

    def test_fixture_byte_count_is_bounded(self):
        with mock.patch.object(midnight, "MAX_FIXTURE_BYTES", 10):
            with self.assertRaisesRegex(MidnightShapeError, "byte ceiling"):
                collect()

    def test_json_depth_and_item_counts_are_bounded(self):
        def deep(payload):
            value = {}
            cursor = value
            for _ in range(midnight.MAX_JSON_DEPTH + 1):
                cursor["x"] = {}
                cursor = cursor["x"]
            payload["harmless_extra"] = value

        self.assert_refused(deep, match="depth ceiling")
        with mock.patch.object(midnight, "MAX_JSON_NODES", 2):
            with self.assertRaisesRegex(MidnightShapeError, "item ceiling"):
                collect()

    def test_fixture_must_be_source_dated_and_origin_bound(self):
        for key, value in (("date", "soon"), ("origin", "https://example.com")):
            with self.subTest(key=key):
                self.assert_refused(
                    lambda payload, k=key, v=value: payload["source"].update({k: v})
                )


class FakeResponse:
    def __init__(self, payload=None, *, raw=None, status=200, headers=None):
        self.raw = (
            json.dumps(payload).encode("utf-8") if raw is None else raw
        )
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.status

    def read(self, limit):
        return self.raw[:limit]


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class TestRestBoundary(unittest.TestCase):
    def budget(self):
        return midnight._RequestBudget(5)

    def request(self, response):
        opener = FakeOpener([response])
        with mock.patch.object(midnight, "_OPENER", opener):
            return midnight._request_json(
                "https://api.morpho.org/v0/midnight/example",
                self.budget(),
                "test",
            )

    def test_live_collection_uses_only_the_documented_locked_routes(self):
        payload = load()
        position = payload["positions"][f"{MARKET}:{SUBJECT}"]
        responses = [
            FakeResponse(payload["transactions"][SUBJECT][0]),
            FakeResponse(payload["markets"][MARKET]),
            FakeResponse(payload["tokens"][f"8453:{TOKEN}"]),
            FakeResponse(position),
        ]
        opener = FakeOpener(responses)
        with mock.patch.object(midnight, "_OPENER", opener), mock.patch.object(
            midnight.time, "time", return_value=payload["source"]["observed_at"]
        ):
            records, coverage = adapter(SUBJECTS, {"timeout": 5})
        self.assertEqual(len(records), 7)
        self.assertEqual(coverage.endpoint, endpoints.MORPHO_MIDNIGHT_ENDPOINT)
        urls = [request.full_url for request, _ in opener.requests]
        self.assertEqual(len(urls), 4)
        self.assertTrue(all(url.startswith("https://api.morpho.org/") for url in urls))
        self.assertIn(f"/users/{SUBJECT}/transactions?", urls[0])
        self.assertIn("chain_ids=8453", urls[0])
        self.assertIn("sort_direction=asc", urls[0])
        self.assertEqual(urls[1], f"https://api.morpho.org/v0/midnight/markets/{MARKET}")
        self.assertEqual(urls[2], f"https://api.morpho.org/v0/tokens/8453:{TOKEN}")
        self.assertEqual(
            urls[3],
            f"https://api.morpho.org/v0/midnight/markets/{MARKET}/users/{SUBJECT}/position",
        )

    def test_live_cursor_is_returned_verbatim_to_the_same_route(self):
        payload = load()
        rows = payload["transactions"][SUBJECT][0]["data"]
        responses = [
            FakeResponse({"cursor": "opaque+/=", "data": rows}),
            FakeResponse({"cursor": None, "data": []}),
            FakeResponse(payload["markets"][MARKET]),
            FakeResponse(payload["tokens"][f"8453:{TOKEN}"]),
            FakeResponse(payload["positions"][f"{MARKET}:{SUBJECT}"]),
        ]
        opener = FakeOpener(responses)
        with mock.patch.object(midnight, "_OPENER", opener), mock.patch.object(
            midnight.time, "time", return_value=payload["source"]["observed_at"]
        ):
            _, coverage = adapter(SUBJECTS, {"timeout": 5})
        self.assertIn("cursor=opaque%2B%2F%3D", opener.requests[1][0].full_url)
        self.assertIn("across 2 page(s)", coverage.note)

    def test_redirects_are_refused_without_exposing_the_location(self):
        handler = midnight._NoRedirect()
        with self.assertRaisesRegex(MidnightShapeError, "redirected unexpectedly"):
            handler.redirect_request(None, None, 302, "found", {}, "https://evil")

    def test_endpoint_configuration_cannot_select_another_origin(self):
        with mock.patch.object(
            endpoints, "MORPHO_API_ORIGIN", "https://example.com"
        ):
            with self.assertRaisesRegex(MidnightShapeError, "locked HTTPS origin"):
                midnight._market_url(MARKET)

    def test_timeout_is_a_bounded_secret_free_error(self):
        opener = FakeOpener([TimeoutError("secret response body")])
        with mock.patch.object(midnight, "_OPENER", opener):
            with self.assertRaises(MidnightShapeError) as caught:
                midnight._request_json(
                    "https://api.morpho.org/v0/midnight/example",
                    self.budget(),
                    "transactions",
                )
        self.assertIn("timeout", str(caught.exception))
        self.assertNotIn("secret response body", str(caught.exception))

    def test_http_status_and_transport_errors_are_bounded(self):
        errors = (
            urllib.error.HTTPError("https://api.morpho.org", 500, "x", {}, None),
            urllib.error.URLError("secret host detail"),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                opener = FakeOpener([error])
                with mock.patch.object(midnight, "_OPENER", opener):
                    with self.assertRaises(MidnightShapeError) as caught:
                        midnight._request_json(
                            "https://api.morpho.org/v0/midnight/example",
                            self.budget(),
                            "market",
                        )
                self.assertNotIn("secret host detail", str(caught.exception))

    def test_non_json_and_invalid_json_are_refused(self):
        with self.assertRaisesRegex(MidnightShapeError, "not application/json"):
            self.request(
                FakeResponse(
                    raw=b"plain",
                    headers={"Content-Type": "text/plain"},
                )
            )
        with self.assertRaisesRegex(MidnightShapeError, "not valid bounded JSON"):
            self.request(FakeResponse(raw=b"{"))

    def test_content_length_and_actual_response_bytes_are_bounded(self):
        with self.assertRaisesRegex(MidnightShapeError, "byte ceiling"):
            self.request(
                FakeResponse(
                    {},
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(midnight.MAX_RESPONSE_BYTES + 1),
                    },
                )
            )
        with self.assertRaisesRegex(MidnightShapeError, "byte ceiling"):
            self.request(FakeResponse(raw=b"x" * (midnight.MAX_RESPONSE_BYTES + 1)))

    def test_total_bytes_request_count_and_time_have_ceiling_guards(self):
        budget = self.budget()
        with self.assertRaisesRegex(MidnightShapeError, "total byte ceiling"):
            budget.consume(midnight.MAX_TOTAL_BYTES + 1)
        with mock.patch.object(midnight, "MAX_HTTP_REQUESTS", 0):
            with self.assertRaisesRegex(MidnightShapeError, "request ceiling"):
                self.budget().next_timeout()
        budget = self.budget()
        with mock.patch.object(midnight.time, "monotonic", return_value=budget.deadline + 1):
            with self.assertRaisesRegex(MidnightShapeError, "time ceiling"):
                budget.next_timeout()

    def test_timeout_configuration_is_strict(self):
        for value in (True, 0, -1, midnight.MAX_COLLECTION_SECONDS + 1, "5"):
            with self.subTest(value=value):
                with self.assertRaises(MidnightShapeError):
                    midnight._RequestBudget(value)


class TestNoPartialRecords(MutationCase):
    def test_falsey_non_mapping_config_uses_shared_error_coverage(self):
        records, coverage = run_adapter(
            midnight.VENUE,
            adapter,
            SUBJECTS,
            [],
        )
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")
        self.assertIn("adapter config is not a mapping", coverage.note)
        self.assertIn("cursor_walks_exhausted=0/1", coverage.note)

    def test_invalid_fixture_source_and_provenance_do_not_echo_raw_values(self):
        cases = (
            (SUBJECTS, {"fixtures": []}, "fixture source"),
            ({SUBJECT: "private-provenance-sentinel"}, {}, "provenance tier"),
        )
        for addresses, config, cause in cases:
            with self.subTest(cause=cause):
                records, coverage = run_adapter(
                    midnight.VENUE,
                    adapter,
                    addresses,
                    config,
                )
                self.assertEqual(records, [])
                self.assertIn(cause, coverage.note)
                self.assertNotIn("private-provenance-sentinel", coverage.note)
                self.assertIn("no records emitted", coverage.note)

    def test_any_failure_returns_zero_records_through_shared_error_coverage(self):
        payload = load()
        payload["positions"][f"{MARKET}:{SUBJECT}"]["data"].update(
            type="borrow", debt="1"
        )
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "morpho-midnight.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(payload, handle)

        records, coverage = run_adapter(
            midnight.VENUE,
            adapter,
            SUBJECTS,
            {"fixtures": directory.name},
        )
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")
        self.assertEqual(coverage.records, 0)
        self.assertIn("reconstructed debt units", coverage.note)
        self.assertIn("cursor_walks_exhausted=1/1", coverage.note)
        self.assertIn("observed_at=1785374000", coverage.note)
        self.assertIn("returned_index_boundary=50551562", coverage.note)
        self.assertIn("no records emitted", coverage.note)

    def test_pre_cursor_refusal_reports_that_no_walk_exhausted(self):
        records, coverage = run_adapter(
            midnight.VENUE,
            adapter,
            SUBJECTS,
            {"fixtures": "/tmp/probitas-secret-path-that-does-not-exist"},
        )
        self.assertEqual(records, [])
        self.assertIn("cursor_walks_exhausted=0/1", coverage.note)
        self.assertIn("observed_at=unavailable", coverage.note)
        self.assertIn("returned_index_boundary=unavailable", coverage.note)
        self.assertNotIn("probitas-secret-path", coverage.note)

    def test_raw_malformed_values_are_not_echoed_into_error_coverage(self):
        payload = load()
        sentinel = "private-response-sentinel"
        payload["transactions"][SUBJECT][0]["data"][0]["data"]["units"] = sentinel
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(
            os.path.join(directory.name, "morpho-midnight.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(payload, handle)
        _, coverage = run_adapter(
            midnight.VENUE,
            adapter,
            SUBJECTS,
            {"fixtures": directory.name},
        )
        self.assertIn("not an exact integer", coverage.note)
        self.assertNotIn(sentinel, coverage.note)

    def test_adapter_returns_one_coverage_row_with_its_record_count(self):
        records, coverage = collect("midnight-late")
        self.assertEqual(coverage.venue, "morpho-midnight")
        self.assertEqual(coverage.records, len(records))


if __name__ == "__main__":
    unittest.main()
