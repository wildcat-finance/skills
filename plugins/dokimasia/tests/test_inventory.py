"""What the rules recognise in the committed fixture, and what they refuse."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from dokimasia_lib import inventory, paths  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "tests" / "fixtures" / "app"
SCHEMA = json.loads((PLUGIN / "schemas" / "inventory-v1.json").read_text(encoding="utf-8"))


def compiled():
    return inventory.compile_inventory(paths.declared_root(FIXTURE))


def by_kind(items, kind):
    return [item for item in items if item["kind"] == kind]


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.items = compiled()

    def test_the_root_page_answers_on_slash(self):
        urls = {item["url"] for item in by_kind(self.items, "route")}
        self.assertIn("/", urls)

    def test_a_route_group_contributes_nothing_to_the_url(self):
        urls = {item["url"] for item in by_kind(self.items, "route")}
        self.assertIn("/about", urls)
        self.assertNotIn("/(marketing)/about", urls)

    def test_a_parallel_route_segment_contributes_nothing(self):
        urls = {item["url"] for item in by_kind(self.items, "route")}
        self.assertIn("/login", urls)
        self.assertNotIn("/@modal/login", urls)

    def test_a_dynamic_segment_keeps_its_declared_shape(self):
        route = next(i for i in by_kind(self.items, "route") if i["url"] == "/markets/[marketId]")
        self.assertEqual(route["dynamic_segments"], ["[marketId]"])

    def test_a_catch_all_segment_keeps_its_declared_shape(self):
        route = next(i for i in by_kind(self.items, "route") if i["url"] == "/docs/[...slug]")
        self.assertEqual(route["dynamic_segments"], ["[...slug]"])

    def test_a_nested_route_records_its_whole_path(self):
        urls = {item["url"] for item in by_kind(self.items, "route")}
        self.assertIn("/markets/[marketId]/lenders", urls)


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.items = compiled()

    def test_directly_exported_methods_are_recorded(self):
        handler = next(i for i in by_kind(self.items, "api") if i["url"] == "/api/health")
        self.assertEqual(handler["methods"], ["GET", "HEAD"])

    def test_a_method_exported_through_a_clause_is_recorded(self):
        handler = next(
            i for i in by_kind(self.items, "api") if i["url"] == "/api/markets/[marketId]"
        )
        self.assertEqual(handler["methods"], ["GET", "PUT"])

    def test_a_commented_or_quoted_method_is_not_recorded(self):
        handler = next(i for i in by_kind(self.items, "api") if i["url"] == "/api/health")
        self.assertNotIn("POST", handler["methods"])
        self.assertNotIn("DELETE", handler["methods"])


class ActionAndGuardTests(unittest.TestCase):
    def setUp(self):
        self.items = compiled()

    def test_a_server_action_module_is_recorded_with_its_exports(self):
        action = next(iter(by_kind(self.items, "action")))
        self.assertEqual(action["source"], "src/actions/update-market.ts")
        self.assertEqual(action["exports"], ["closeMarket", "updateMarket"])

    def test_a_quoted_directive_does_not_make_an_action(self):
        self.assertFalse([i for i in by_kind(self.items, "action") if "decoy" in i["source"]])

    def test_middleware_is_recorded_with_its_matchers(self):
        guard = next(i for i in by_kind(self.items, "guard") if i["guard"] == "middleware")
        self.assertEqual(guard["matchers"], ["/api/:path*", "/markets/:path*"])

    def test_a_named_gate_is_recorded(self):
        guard = next(i for i in by_kind(self.items, "guard") if i["guard"] == "named-gate")
        self.assertEqual(guard["names"], ["RequireAuth"])


class DeterminismTests(unittest.TestCase):
    def test_two_compiles_agree_byte_for_byte(self):
        self.assertEqual(
            inventory.canonical_bytes(compiled()),
            inventory.canonical_bytes(compiled()),
        )

    def test_the_digest_excludes_the_subject_so_a_label_cannot_move_it(self):
        items = compiled()
        first = inventory.record(items, {"label": "one"})
        second = inventory.record(items, {"label": "two"})
        self.assertEqual(first["inventory_sha256"], second["inventory_sha256"])

    def test_items_are_sorted_so_directory_order_cannot_move_the_digest(self):
        items = compiled()
        keys = [(i["kind"], i.get("url", ""), i["source"]) for i in items]
        self.assertEqual(keys, sorted(keys))


class RecordShapeTests(unittest.TestCase):
    def setUp(self):
        self.record = inventory.record(compiled(), {"label": "synthetic fixture"})

    def test_the_record_carries_exactly_the_declared_keys(self):
        self.assertEqual(sorted(self.record), sorted(SCHEMA["required"]))

    def test_every_declared_kind_is_counted(self):
        self.assertEqual(
            sorted(self.record["counts"]), ["action", "api", "guard", "route"]
        )
        self.assertEqual(sum(self.record["counts"].values()), self.record["scoped_items"])

    def test_the_caps_are_recorded_with_the_record_they_bounded(self):
        self.assertEqual(
            self.record["caps"],
            {"files": paths.MAX_FILES, "file_bytes": paths.MAX_FILE_BYTES,
             "depth": paths.MAX_DEPTH},
        )

    def test_no_item_carries_a_key_the_schema_does_not_declare(self):
        allowed = set(SCHEMA["properties"]["items"]["items"]["properties"])
        for item in self.record["items"]:
            with self.subTest(source=item["source"]):
                self.assertTrue(set(item) <= allowed, set(item) - allowed)


class RefusalTests(unittest.TestCase):
    def test_every_declared_rule_and_cap_refuses_by_name(self):
        results = dict(inventory.refusal_proofs())
        self.assertEqual(
            sorted(results),
            ["absolute-path", "over-deep-tree", "over-large-file-count",
             "oversized-file", "parent-directory", "symlink-root"],
        )
        for name, refusal in sorted(results.items()):
            with self.subTest(rule=name):
                self.assertTrue(refusal, f"{name} was accepted; it must refuse")

    def test_no_declared_cap_is_mutated_while_the_proofs_run(self):
        before = (paths.MAX_FILES, paths.MAX_FILE_BYTES, paths.MAX_DEPTH)
        inventory.refusal_proofs()
        self.assertEqual((paths.MAX_FILES, paths.MAX_FILE_BYTES, paths.MAX_DEPTH), before)

    def test_a_matcher_list_that_never_closes_refuses_rather_than_truncating(self):
        from dokimasia_lib import lexer
        runaway = lexer.tokenize(
            "export const config = { matcher: [" + '"/a",' * 400 + "\n"
        )
        with self.assertRaises(inventory.InventoryError) as caught:
            inventory._matchers(runaway)
        self.assertIn("token cap", str(caught.exception))

    def test_the_check_entry_point_reports_no_failures_on_the_fixture(self):
        self.assertEqual(inventory.check(paths.declared_root(FIXTURE)), [])


class ProcessBoundaryTests(unittest.TestCase):
    """phylax: a compile spawns nothing and opens nothing."""

    def test_a_compile_spawns_no_subprocess_and_opens_no_socket(self):
        import socket
        import subprocess

        calls: list[str] = []
        real_popen, real_socket = subprocess.Popen, socket.socket

        def refuse_popen(*args, **kwargs):
            calls.append("subprocess")
            raise AssertionError("a compile spawned a subprocess")

        def refuse_socket(*args, **kwargs):
            calls.append("socket")
            raise AssertionError("a compile opened a socket")

        subprocess.Popen = refuse_popen
        socket.socket = refuse_socket
        try:
            compiled()
        finally:
            subprocess.Popen = real_popen
            socket.socket = real_socket
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
