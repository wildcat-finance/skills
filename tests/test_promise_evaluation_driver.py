"""Guards for the isolated Promise Machine evaluation driver."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import promise_evaluation_driver as driver


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROMISES = {
    "hypomnema-record-placement",
    "kronos-fiat-dispatch",
    "vulgate-register-rewrite",
    "hexaemeron-fizz-harness-campaign",
    "hexaemeron-fizz-convert-properties",
    "hexaemeron-fizz-sync-drift",
    "hexaemeron-x-ray-preaudit",
    "hexaemeron-solidity-audit-report",
    "sapheneia-session-shape",
    "sapheneia-deactivation",
    "sapheneia-durable-record-shape",
}
MODEL = (
    "ollama/qwen3.8-uncensored:Q6_K@sha256:"
    "5d73434fd9f8fffa886252f291939eae0b38e5c135449db052ab2db04d117e68"
)
DATE = "2026-08-31"


def raw_answer(case):
    return json.dumps(
        {scenario["id"]: scenario["expected"] for scenario in case["scenarios"]},
        sort_keys=True,
        separators=(",", ":"),
    )


def answer_document(cases):
    return {
        "contract": "promise-machine-evaluation-answers/v1",
        "answers": {case["id"]: raw_answer(case) for case in cases},
    }


class DriverCase(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="promise-evaluation-"))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.packet = self.temp / "packet"
        self.cases = driver.load_cases()

    def write_answers(self, document=None, name="answers.json"):
        path = self.temp / name
        body = document if document is not None else answer_document(self.cases)
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        return path

    def emit(self):
        return driver.emit(self.packet)

    def tally(self, answers=None, name="run.json"):
        if not self.packet.exists():
            self.emit()
        answers = answers or self.write_answers()
        out = self.temp / name
        return driver.tally(self.packet, answers, out, MODEL, DATE), out


class DiscoveryTests(DriverCase):
    def test_exactly_the_eleven_fixture_only_promises_are_discovered(self):
        self.assertEqual({case["id"] for case in self.cases}, EXPECTED_PROMISES)
        self.assertEqual(len(self.cases), 11)

    def test_each_case_has_five_opaque_scenarios_and_one_request(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    set(case),
                    {"id", "skill_path", "request", "contract", "scenarios"},
                )
                self.assertTrue(case["request"].strip())
                self.assertTrue(case["contract"].startswith(f"### {case['id']}\n"))
                self.assertEqual(
                    [item["id"] for item in case["scenarios"]],
                    ["E01", "E02", "E03", "E04", "E05"],
                )
                self.assertEqual(
                    {item["expected"] for item in case["scenarios"]},
                    {"accept", "refuse", "recover"},
                )

    def test_discovery_is_deterministic(self):
        self.assertEqual(self.cases, driver.load_cases())
        self.assertEqual(
            [case["id"] for case in self.cases],
            sorted(case["id"] for case in self.cases),
        )


class PacketEmissionTests(DriverCase):
    def test_one_prompt_per_case_and_manifest_written_last(self):
        manifest = self.emit()
        self.assertEqual([item["id"] for item in manifest["cases"]], sorted(EXPECTED_PROMISES))
        self.assertEqual(
            sorted(path.name for path in self.packet.iterdir()),
            sorted([driver.MANIFEST_NAME] + [f"{case_id}.txt" for case_id in EXPECTED_PROMISES]),
        )

    def test_each_prompt_is_isolated_from_every_other_case(self):
        self.emit()
        by_id = {case["id"]: case for case in self.cases}
        for case_id, case in by_id.items():
            prompt = (self.packet / f"{case_id}.txt").read_text(encoding="utf-8")
            self.assertIn(case_id, prompt)
            self.assertIn(case["request"], prompt)
            for other_id, other in by_id.items():
                if other_id == case_id:
                    continue
                self.assertNotIn(other_id, prompt)
                self.assertNotIn(other["request"], prompt)

    def test_prompts_never_leak_expected_dispositions_or_boundaries(self):
        self.emit()
        for case in self.cases:
            prompt = (self.packet / f"{case['id']}.txt").read_text(encoding="utf-8")
            for scenario in case["scenarios"]:
                self.assertIn(scenario["text"], prompt)
                self.assertNotIn(scenario["boundary"], prompt)
            self.assertNotIn('"expected"', prompt)
            self.assertNotIn('"boundary"', prompt)

    def test_manifest_binds_template_corpus_tree_case_set_and_prompt_bytes(self):
        manifest = self.emit()
        self.assertEqual(
            set(manifest),
            {
                "contract",
                "prompt_template_sha256",
                "corpus_sha256",
                "tree_sha256",
                "cases",
            },
        )
        for field in ("prompt_template_sha256", "corpus_sha256", "tree_sha256"):
            self.assertRegex(manifest[field], r"^[0-9a-f]{64}$")
        for record in manifest["cases"]:
            payload = (self.packet / record["prompt"]).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), record["prompt_sha256"])
            self.assertEqual(record["scenarios"], ["E01", "E02", "E03", "E04", "E05"])

    def test_existing_directory_refuses_even_when_empty(self):
        self.packet.mkdir()
        with self.assertRaises(driver.DriverError):
            self.emit()

    def test_symlink_output_refuses(self):
        target = self.temp / "target"
        target.mkdir()
        self.packet.symlink_to(target, target_is_directory=True)
        with self.assertRaises(driver.DriverError):
            self.emit()

    def test_parent_escape_refuses(self):
        safe = self.temp / "safe"
        safe.mkdir()
        with self.assertRaises(driver.DriverError):
            driver.emit(safe / ".." / "escape")

    def test_interrupted_emit_leaves_no_manifest(self):
        original = driver.render_prompt
        seen = []

        def interrupted(case, **kwargs):
            seen.append(case["id"])
            if len(seen) == 4:
                raise OSError("simulated interrupted write")
            return original(case, **kwargs)

        with mock.patch.object(driver, "render_prompt", interrupted):
            with self.assertRaises(OSError):
                self.emit()
        self.assertTrue(any(self.packet.glob("*.txt")))
        self.assertFalse((self.packet / driver.MANIFEST_NAME).exists())


class TallyTests(DriverCase):
    def test_complete_answers_produce_a_bound_run_record(self):
        run, out = self.tally()
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), run)
        self.assertEqual(run["model"], MODEL)
        self.assertEqual(run["date"], DATE)
        self.assertEqual(run["cases"], sorted(EXPECTED_PROMISES))
        self.assertEqual(run["counts"], {"answers": 11, "cases": 11, "outcomes": 55, "passed": 55, "failed": 0})
        self.assertEqual(run["failures"], [])
        self.assertEqual(run["domain_evidence"], "not-supplied")
        self.assertEqual(len(run["answers"]), 11)

    def test_run_record_keeps_identities_and_counts_not_prompts_or_labels(self):
        run, _ = self.tally()
        rendered = json.dumps(run, sort_keys=True)
        for case in self.cases:
            self.assertNotIn(case["request"], rendered)
            for scenario in case["scenarios"]:
                self.assertNotIn(scenario["text"], rendered)
                self.assertNotIn(scenario["boundary"], rendered)
        for answer in run["answers"]:
            self.assertEqual(set(answer), {"case", "sha256", "bytes", "passed", "failed"})

    def test_tally_is_deterministic(self):
        self.emit()
        answers = self.write_answers()
        one = self.temp / "one.json"
        two = self.temp / "two.json"
        driver.tally(self.packet, answers, one, MODEL, DATE)
        driver.tally(self.packet, answers, two, MODEL, DATE)
        self.assertEqual(one.read_bytes(), two.read_bytes())

    def test_tally_never_rewrites_a_corpus(self):
        before = {path: path.read_bytes() for path in driver.input_files() if "evaluation-cases" in path.name or path.name == "cases.json"}
        self.tally()
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_missing_and_extra_answers_refuse(self):
        for mode in ("missing", "extra"):
            with self.subTest(mode=mode):
                document = answer_document(self.cases)
                if mode == "missing":
                    document["answers"].pop(sorted(document["answers"])[0])
                else:
                    document["answers"]["extra-promise"] = "{}"
                self.emit()
                with self.assertRaises(driver.DriverError):
                    driver.tally(
                        self.packet,
                        self.write_answers(document, f"{mode}.json"),
                        self.temp / f"{mode}-run.json",
                        MODEL,
                        DATE,
                    )
                shutil.rmtree(self.packet)

    def test_duplicate_outer_answer_refuses(self):
        self.emit()
        document = answer_document(self.cases)
        first = sorted(document["answers"])[0]
        body = json.dumps(document, separators=(",", ":"))
        needle = '"answers":{'
        duplicate = body.replace(
            needle,
            needle + json.dumps(first) + ":" + json.dumps(document["answers"][first]) + ",",
            1,
        )
        path = self.temp / "duplicate.json"
        path.write_text(duplicate, encoding="utf-8")
        with self.assertRaises(driver.DriverError):
            driver.tally(self.packet, path, self.temp / "run.json", MODEL, DATE)

    def test_duplicate_inner_scenario_refuses(self):
        self.emit()
        document = answer_document(self.cases)
        first = sorted(document["answers"])[0]
        document["answers"][first] = '{"E01":"accept","E01":"refuse","E02":"refuse","E03":"recover","E04":"refuse","E05":"refuse"}'
        with self.assertRaises(driver.DriverError):
            driver.tally(
                self.packet,
                self.write_answers(document),
                self.temp / "run.json",
                MODEL,
                DATE,
            )

    def test_partial_answer_not_run_and_open_vocabulary_refuse(self):
        mutations = (
            lambda raw: json.dumps({"E01": "accept"}),
            lambda raw: "not-run",
            lambda raw: raw.replace("refuse", "probably-refuse", 1),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.emit()
                document = answer_document(self.cases)
                first = sorted(document["answers"])[0]
                document["answers"][first] = mutate(document["answers"][first])
                with self.assertRaises(driver.DriverError):
                    driver.tally(
                        self.packet,
                        self.write_answers(document, f"bad-{index}.json"),
                        self.temp / f"bad-{index}-run.json",
                        MODEL,
                        DATE,
                    )
                shutil.rmtree(self.packet)

    def test_deeply_nested_answer_refuses_without_crashing(self):
        self.emit()
        document = answer_document(self.cases)
        first = sorted(document["answers"])[0]
        document["answers"][first] = "[" * 5_000 + "0" + "]" * 5_000
        with self.assertRaises(driver.DriverError):
            driver.tally(
                self.packet,
                self.write_answers(document, "deep.json"),
                self.temp / "deep-run.json",
                MODEL,
                DATE,
            )

    def test_invalid_utf8_oversize_non_file_and_symlink_answers_refuse(self):
        self.emit()
        invalid = self.temp / "invalid.json"
        invalid.write_bytes(b"\xff")
        oversized = self.temp / "oversized.json"
        oversized.write_bytes(b" " * (driver.MAX_ANSWERS_BYTES + 1))
        directory = self.temp / "answer-directory"
        directory.mkdir()
        link = self.temp / "answer-link.json"
        link.symlink_to(self.write_answers(name="linked-target.json"))
        for path in (invalid, oversized, directory, link):
            with self.subTest(path=path.name):
                with self.assertRaises(driver.DriverError):
                    driver.tally(self.packet, path, self.temp / f"{path.name}.run", MODEL, DATE)

    def test_edited_prompt_and_missing_manifest_refuse(self):
        for mode in ("edited", "partial"):
            with self.subTest(mode=mode):
                self.emit()
                manifest_path = self.packet / driver.MANIFEST_NAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if mode == "edited":
                    prompt = self.packet / manifest["cases"][0]["prompt"]
                    prompt.write_text(prompt.read_text(encoding="utf-8") + "edited\n", encoding="utf-8")
                else:
                    manifest_path.unlink()
                with self.assertRaises(driver.DriverError):
                    driver.tally(
                        self.packet,
                        self.write_answers(name=f"{mode}-answers.json"),
                        self.temp / f"{mode}-run.json",
                        MODEL,
                        DATE,
                    )
                shutil.rmtree(self.packet)

    def test_malformed_model_and_date_refuse(self):
        self.emit()
        answers = self.write_answers()
        for model, date in (("qwen", DATE), (MODEL, "31-08-2026"), (MODEL, "2026-02-30")):
            with self.subTest(model=model, date=date):
                with self.assertRaises(driver.DriverError):
                    driver.tally(self.packet, answers, self.temp / f"run-{date}.json", model, date)

    def test_existing_or_symlink_run_output_refuses(self):
        self.emit()
        answers = self.write_answers()
        existing = self.temp / "existing.json"
        existing.write_text("keep", encoding="utf-8")
        target = self.temp / "target.json"
        target.write_text("keep", encoding="utf-8")
        link = self.temp / "run-link.json"
        link.symlink_to(target)
        for out in (existing, link):
            with self.subTest(out=out.name):
                with self.assertRaises(driver.DriverError):
                    driver.tally(self.packet, answers, out, MODEL, DATE)
        self.assertEqual(existing.read_text(encoding="utf-8"), "keep")
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")


class VerificationTests(DriverCase):
    def test_verify_accepts_the_exact_packet_answers_and_run(self):
        run, path = self.tally()
        self.assertEqual(driver.verify(self.packet, self.temp / "answers.json", path), run)

    def test_verify_refuses_an_edited_answer_or_run(self):
        run, path = self.tally()
        answers = self.temp / "answers.json"
        original_answers = answers.read_bytes()
        document = json.loads(original_answers.decode("utf-8"))
        first = sorted(document["answers"])[0]
        document["answers"][first] = document["answers"][first].replace("accept", "refuse", 1)
        answers.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(driver.DriverError):
            driver.verify(self.packet, answers, path)
        answers.write_bytes(original_answers)

        changed = dict(run)
        changed["domain_evidence"] = "claimed-by-grade"
        path.write_text(json.dumps(changed, indent=2) + "\n", encoding="utf-8")
        with self.assertRaises(driver.DriverError):
            driver.verify(self.packet, answers, path)

    def test_tally_refuses_when_an_input_tree_file_changed_after_emit(self):
        scratch = self.temp / "repository"
        for source in driver.input_files():
            relative = source.relative_to(ROOT)
            destination = scratch / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        packet = self.temp / "scratch-packet"
        cases = driver.load_cases(root=scratch)
        driver.emit(packet, root=scratch)
        answers = self.temp / "scratch-answers.json"
        answers.write_text(json.dumps(answer_document(cases)), encoding="utf-8")
        corpus = next(path for path in driver.input_files(root=scratch) if path.name == "evaluation-cases.json")
        corpus.write_text(corpus.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaises(driver.DriverError):
            driver.tally(packet, answers, self.temp / "scratch-run.json", MODEL, DATE, root=scratch)


if __name__ == "__main__":
    unittest.main()
