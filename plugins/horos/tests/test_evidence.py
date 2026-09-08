"""The evidence bundle's prose cannot drift from its committed boundary."""

from pathlib import Path
import json
import re
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
EVIDENCE = PLUGIN / "docs" / "evidence"
BUNDLE = EVIDENCE / "wildcat-app-v2.md"
BOUNDARY = EVIDENCE / "wildcat-app-v2.boundary.json"
BUNDLE_2 = EVIDENCE / "wildcat-app-v2-rules.md"
BOUNDARY_2 = EVIDENCE / "wildcat-app-v2-rules.boundary.json"
BUNDLE_3 = EVIDENCE / "wildcat-app-v2-outline.md"
RESULTS_3 = EVIDENCE / "wildcat-app-v2-outline.results.json"
BUNDLE_4 = EVIDENCE / "wildcat-app-v2-census.md"
CENSUS_APP = EVIDENCE / "wildcat-app-v2-census.json"
CENSUS_PROTOCOL = EVIDENCE / "v2-protocol-census.json"
BUNDLE_5 = EVIDENCE / "go-ethereum-outline.md"
RESULTS_5 = EVIDENCE / "go-ethereum-outline.results.json"
BUNDLE_6 = EVIDENCE / "solidity-outline.md"
RESULTS_6 = EVIDENCE / "solidity-outline.results.json"
BUNDLE_7 = EVIDENCE / "v2-protocol-outline.md"
RESULTS_7 = EVIDENCE / "v2-protocol-outline.results.json"
BUNDLE_9 = EVIDENCE / "skills-markdown-outline.md"
RESULTS_9 = EVIDENCE / "skills-markdown-outline.results.json"
BUNDLE_8 = EVIDENCE / "three-repository-marking.md"
MARKING_V2P = EVIDENCE / "v2-protocol.boundary.json"
MARKING_APP = EVIDENCE / "wildcat-app-v2.boundary.v2.json"
# Frozen beside the other two marked repositories. Reading this repository's
# live boundary instead would make the recorded capture drift with the tree, so
# a later rule class would either fail this test or force the bundle's figures
# to be rewritten into a claim the marking run never made.
MARKING_SKILLS = EVIDENCE / "skills.boundary.json"


def capture_lines(bundle=BUNDLE, tag="evidence"):
    text = bundle.read_text(encoding="utf-8")
    return dict(re.findall(rf"<!-- {tag}:(\S+) (\S+) -->", text))


class EvidenceBundleTests(unittest.TestCase):
    def test_the_boundary_document_parses_with_the_shipped_schema(self):
        document = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], 1)
        self.assertEqual(document["tool"], "horos")

    def test_the_quoted_totals_equal_the_boundary_documents(self):
        lines = capture_lines()
        document = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        counts = document["counts"]
        self.assertEqual(int(lines["entries"]), len(document["entries"]))
        self.assertEqual(int(lines["files_walked"]), counts["files_walked"])
        self.assertEqual(
            int(lines["files_skipped_unreadable"]), counts["files_skipped_unreadable"]
        )
        for category in ("generated", "binary", "lockfile", "blob"):
            self.assertEqual(
                int(lines["bytes_" + category]), counts["bytes_" + category]
            )
        classified = sum(entry["bytes"] for entry in document["entries"])
        self.assertEqual(int(lines["classified_bytes"]), classified)

    def test_the_bundle_names_its_commit(self):
        lines = capture_lines()
        self.assertRegex(lines["commit"], r"^[0-9a-f]{40}$")
        self.assertIn(lines["commit"], BUNDLE.read_text(encoding="utf-8"))

    def test_the_criterion_arithmetic_holds(self):
        lines = capture_lines()
        share = 100 * int(lines["classified_bytes"]) / int(lines["total_bytes"])
        self.assertGreaterEqual(share, 60.0)
        self.assertAlmostEqual(share, 80.3, places=1)


class SecondCaptureTests(unittest.TestCase):
    def test_the_quoted_totals_equal_the_boundary_documents(self):
        lines = capture_lines(BUNDLE_2, "evidence2")
        document = json.loads(BOUNDARY_2.read_text(encoding="utf-8"))
        counts = document["counts"]
        self.assertEqual(int(lines["entries"]), len(document["entries"]))
        self.assertEqual(int(lines["files_walked"]), counts["files_walked"])
        for category in ("generated", "binary", "lockfile", "blob", "asset"):
            self.assertEqual(
                int(lines["bytes_" + category]), counts["bytes_" + category]
            )
        classified = sum(entry["bytes"] for entry in document["entries"])
        self.assertEqual(int(lines["classified_bytes"]), classified)

    def test_both_captures_name_the_same_commit(self):
        self.assertEqual(
            capture_lines()["commit"], capture_lines(BUNDLE_2, "evidence2")["commit"]
        )

    def test_the_delta_is_exactly_the_two_rule_families(self):
        old = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        new = json.loads(BOUNDARY_2.read_text(encoding="utf-8"))
        old_paths = {entry["path"] for entry in old["entries"]}
        new_paths = {entry["path"] for entry in new["entries"]}
        self.assertEqual(old_paths - new_paths, set())
        for path in new_paths - old_paths:
            self.assertTrue(
                path.endswith(".svg")
                or (path.endswith(".sql") and "migrations" in path.split("/")),
                path,
            )

    def test_the_outline_bundle_matches_its_committed_results(self):
        lines = capture_lines(BUNDLE_3, "outline")
        totals = json.loads(RESULTS_3.read_text(encoding="utf-8"))["totals"]
        for key in (
            "files",
            "crashes",
            "oracle",
            "matched",
            "missed",
            "missed_confessed",
            "extra",
            "files_with_regions",
        ):
            self.assertEqual(int(lines[key]), totals[key], key)

    def test_the_outline_run_names_the_same_commit_as_the_captures(self):
        self.assertEqual(
            capture_lines()["commit"], capture_lines(BUNDLE_3, "outline")["commit"]
        )

    def test_the_outline_acceptance_holds(self):
        totals = json.loads(RESULTS_3.read_text(encoding="utf-8"))["totals"]
        self.assertEqual(totals["crashes"], 0)
        self.assertEqual(totals["missed"], 0)
        self.assertEqual(totals["extra"], 0)

    def test_the_census_bundle_matches_both_committed_documents(self):
        lines = capture_lines(BUNDLE_4, "census1")
        app = json.loads(CENSUS_APP.read_text(encoding="utf-8"))
        self.assertEqual(int(lines["total_files"]), app["total_files"])
        self.assertEqual(int(lines["total_bytes"]), app["total_bytes"])
        tsx = next(row for row in app["rows"] if row["suffix"] == ".tsx")
        self.assertEqual(int(lines["tsx_bytes"]), tsx["bytes"])
        self.assertEqual(int(lines["tsx_boundary_bytes"]), tsx["boundary_bytes"])

        lines = capture_lines(BUNDLE_4, "census2")
        protocol = json.loads(CENSUS_PROTOCOL.read_text(encoding="utf-8"))
        self.assertEqual(int(lines["total_files"]), protocol["total_files"])
        self.assertEqual(int(lines["total_bytes"]), protocol["total_bytes"])
        sol = next(row for row in protocol["rows"] if row["suffix"] == ".sol")
        self.assertEqual(int(lines["sol_bytes"]), sol["bytes"])
        self.assertEqual(int(lines["sol_boundary_bytes"]), sol["boundary_bytes"])

    def test_the_app_census_names_the_same_commit_as_the_captures(self):
        self.assertEqual(
            capture_lines()["commit"], capture_lines(BUNDLE_4, "census1")["commit"]
        )

    def test_both_census_documents_carry_the_shipped_schema(self):
        for path in (CENSUS_APP, CENSUS_PROTOCOL):
            document = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(document=path.name):
                self.assertEqual(document["schema"], 1)
                self.assertEqual(document["tool"], "horos")
                self.assertEqual(
                    sum(row["bytes"] for row in document["rows"]),
                    document["total_bytes"],
                )

    def test_the_go_outline_bundle_matches_its_committed_results(self):
        lines = capture_lines(BUNDLE_5, "gooutline")
        totals = json.loads(RESULTS_5.read_text(encoding="utf-8"))["totals"]
        for key in (
            "files",
            "crashes",
            "oracle",
            "matched",
            "missed",
            "missed_confessed",
            "extra",
            "files_with_regions",
        ):
            self.assertEqual(int(lines[key]), totals[key], key)

    def test_the_go_outline_acceptance_holds(self):
        totals = json.loads(RESULTS_5.read_text(encoding="utf-8"))["totals"]
        self.assertEqual(totals["crashes"], 0)
        self.assertEqual(totals["missed"], 0)
        self.assertEqual(totals["extra"], 0)
        self.assertEqual(totals["matched"], totals["oracle"])

    def test_the_cpp_outline_bundle_matches_its_committed_results(self):
        lines = capture_lines(BUNDLE_6, "cppoutline")
        totals = json.loads(RESULTS_6.read_text(encoding="utf-8"))["totals"]
        for key in (
            "files",
            "crashes",
            "oracle",
            "matched",
            "missed",
            "missed_confessed",
            "extra",
            "oracle_unparsed",
        ):
            self.assertEqual(int(lines[key]), totals[key], key)

    def test_the_cpp_outline_acceptance_holds(self):
        totals = json.loads(RESULTS_6.read_text(encoding="utf-8"))["totals"]
        self.assertEqual(totals["crashes"], 0)
        self.assertEqual(totals["missed"], 0)
        self.assertEqual(totals["extra"], 0)
        self.assertEqual(totals["matched"], totals["oracle"])

    def test_the_sol_outline_bundle_matches_its_committed_results(self):
        lines = capture_lines(BUNDLE_7, "soloutline")
        totals = json.loads(RESULTS_7.read_text(encoding="utf-8"))["totals"]
        for key in (
            "files",
            "crashes",
            "oracle",
            "matched",
            "missed",
            "missed_confessed",
            "extra",
            "oracle_unparsed",
        ):
            self.assertEqual(int(lines[key]), totals[key], key)

    def test_the_sol_outline_acceptance_holds(self):
        totals = json.loads(RESULTS_7.read_text(encoding="utf-8"))["totals"]
        self.assertEqual(totals["crashes"], 0)
        self.assertEqual(totals["missed"], 0)
        self.assertEqual(totals["extra"], 0)
        self.assertEqual(totals["oracle_unparsed"], 0)
        self.assertEqual(totals["matched"], totals["oracle"])

    def test_the_markdown_outline_bundle_matches_its_committed_results(self):
        lines = capture_lines(BUNDLE_9, "mdoutline")
        totals = json.loads(RESULTS_9.read_text(encoding="utf-8"))["totals"]
        for key in (
            "files",
            "bytes",
            "crashes",
            "oracle",
            "matched",
            "missed",
            "missed_confessed",
            "extra",
            "fence_oracle",
            "fence_matched",
            "fence_missed",
            "fence_missed_confessed",
            "fence_extra",
            "regions",
            "files_with_regions",
        ):
            self.assertEqual(int(lines[key]), totals[key], key)
        self.assertRegex(lines["commit"], r"^[0-9a-f]{40}$")

    def test_the_markdown_outline_acceptance_holds(self):
        totals = json.loads(RESULTS_9.read_text(encoding="utf-8"))["totals"]
        self.assertEqual(totals["crashes"], 0)
        self.assertEqual(totals["missed"], 0)
        self.assertEqual(totals["extra"], 0)
        self.assertEqual(totals["fence_missed"], 0)
        self.assertEqual(totals["fence_extra"], 0)
        self.assertEqual(totals["matched"], totals["oracle"])
        self.assertEqual(totals["fence_matched"], totals["fence_oracle"])

    def test_the_marking_bundle_matches_the_committed_boundaries(self):
        lines = capture_lines(BUNDLE_8, "marking")
        for prefix, path in (
            ("skills", MARKING_SKILLS),
            ("v2p", MARKING_V2P),
            ("app", MARKING_APP),
        ):
            document = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(repository=prefix):
                self.assertEqual(document["schema"], 2)
                self.assertEqual(document["universe"], "tracked")
                self.assertEqual(
                    int(lines[f"{prefix}_entries"]), len(document["entries"])
                )
                self.assertEqual(
                    int(lines[f"{prefix}_hard_bytes"]),
                    sum(entry["bytes"] for entry in document["entries"]),
                )
                self.assertTrue(
                    all(entry["grade"] == "hard" for entry in document["entries"])
                )

    def test_the_second_share_exceeds_the_first(self):
        first = capture_lines()
        second = capture_lines(BUNDLE_2, "evidence2")
        self.assertEqual(first["total_bytes"], second["total_bytes"])
        self.assertGreater(
            int(second["classified_bytes"]), int(first["classified_bytes"])
        )
        share = 100 * int(second["classified_bytes"]) / int(second["total_bytes"])
        self.assertAlmostEqual(share, 83.3, places=1)


class OutlineResultsShapeTests(unittest.TestCase):
    """Every outline results document stays summable after the clean rows leave.

    A differential's evidence is its totals and its exceptions. Carrying a row
    for each file the outliner read exactly as the oracle did put 33,000 lines
    of matches and zeroes in the tree that no check read, so those files are
    recorded by count under `clean` instead. That only stays honest while the
    totals are still the sum of what the document holds, which is what these
    cases check; see skills#1259.
    """

    RESULTS = (RESULTS_3, RESULTS_5, RESULTS_6, RESULTS_7, RESULTS_9)
    SUMMED = (
        "matched", "missed", "missed_confessed", "extra", "oracle", "ours", "regions",
        "fence_matched", "fence_missed", "fence_missed_confessed", "fence_extra",
        "fence_oracle", "fence_ours",
    )

    def test_every_results_document_carries_the_trimmed_shape(self):
        for path in self.RESULTS:
            with self.subTest(results=path.name):
                document = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    sorted(document), ["clean", "files", "note", "totals"]
                )
                for name, value in document["clean"].items():
                    if isinstance(value, list):
                        self.assertEqual(len(value), 2, name)
                        self.assertTrue(all(isinstance(n, int) for n in value), name)
                    else:
                        self.assertIsInstance(value, int, name)
                self.assertEqual(set(document["clean"]) & set(document["files"]), set())

    def test_the_totals_are_the_sum_of_the_rows_and_the_clean_counts(self):
        for path in self.RESULTS:
            with self.subTest(results=path.name):
                document = json.loads(path.read_text(encoding="utf-8"))
                totals = document["totals"]
                summed = {key: 0 for key in self.SUMMED}
                for row in document["files"].values():
                    for key in self.SUMMED:
                        summed[key] += row.get(key, 0)
                for value in document["clean"].values():
                    heads, fences = value if isinstance(value, list) else (value, 0)
                    for key in ("matched", "ours", "oracle"):
                        summed[key] += heads
                    for key in ("fence_matched", "fence_ours", "fence_oracle"):
                        summed[key] += fences
                for key, total in totals.items():
                    if key in summed:
                        self.assertEqual(summed[key], total, f"{path.name}:{key}")
                self.assertEqual(
                    len(document["files"]) + len(document["clean"]), totals["files"]
                )


if __name__ == "__main__":
    unittest.main()
