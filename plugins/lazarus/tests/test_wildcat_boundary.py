"""Offline checks for the Wildcat boundary example.

Both plans regenerate from the committed generator, probe summaries and value
map to the digests and counts `plans.json` records, Lazarus plan validation
accepts them, the generator's refusals hold, the copies under
`docs/lazarus-wildcat-boundary-fixtures/` match the receipted digests, and no
committed file in the example carries a URL, credential or absolute-path
pattern. The capture driver's refusals hold and, with Lazarus's capture
routine replaced by a recording stand-in, the bearer travels only as a
request header. Each committed capture record's counts equal the plan's, and
each relation report gives all 61 map rows one class with a backing entry the
regenerated plan or the capture record carries. Nothing here reaches a
network: the probe's reads and the captures are recorded evidence that no
test repeats.

Step 3 adds the release records and the demonstration. The committed
statements, release documents, Alexandria plans and archive inventory are held
to the capture records and to one another, ``demo.py verify-preserved`` passes
on the committed example and refuses an edited digest, the mutation routine's
three refusal classes are exercised offline against the committed Aave v4
release fixture, and the demo script's refusals of a missing variable, an
existing output and a symlinked input hold. ``mutations`` and
``verify-releases`` over the real release trees run only when
``WILDCAT_BOUNDARY_V1_RELEASE`` and ``WILDCAT_BOUNDARY_V2_RELEASE`` are set;
otherwise those two tests skip and say so.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from .support import PLUGIN_ROOT, REPO_ROOT
from lazarus_lib.binding import CHECKS, IN_TOTO_STATEMENT_TYPE, STATE_FIXTURE_TYPE_V2
from lazarus_lib.canonical import load
from lazarus_lib.manifest import fixture_digest
from lazarus_lib.release import release_digest
from lazarus_lib.schemas import validate_document

EXAMPLE = PLUGIN_ROOT / "examples" / "wildcat-boundary-v0"
GENERATOR = EXAMPLE / "plan_v3.py"
DOCS = REPO_ROOT / "docs" / "lazarus-wildcat-boundary-fixtures"
KICKOFF = REPO_ROOT / "docs" / "kickoff" / "1384"
GENERATIONS = ("v1", "v2")
COMMITTED_EXAMPLE_FILES = {
    "README.md", "capture-v1.json", "capture-v2.json", "capture.py", "plan_v3.py",
    "plans.json", "probe-v1.json", "probe-v2.json", "probe.py", "relations-v1.json",
    "relations-v2.json", "relations.py", "wildcat_slots.py",
    # Step 3: the release records, the archive inventory and the demonstration.
    "alexandria-plan-v1.json", "alexandria-plan-v2.json", "archive.py", "archives.json",
    "demo.py", "release-v1.json", "release-v2.json", "statement-v1.json",
    "statement-v2.json",
}
# Ariadne and Lazarus wrote these four; their bytes are what the releases
# digest, so they carry the two in-toto type identifiers as written.
GENERATED_DOCUMENTS = {"release-v1.json", "release-v2.json", "statement-v1.json", "statement-v2.json"}
TYPE_IDENTIFIERS = (IN_TOTO_STATEMENT_TYPE, STATE_FIXTURE_TYPE_V2)
DRIVER = EXAMPLE / "capture.py"
RELATIONS = EXAMPLE / "relations.py"
DEMO = EXAMPLE / "demo.py"
ARCHIVER = EXAMPLE / "archive.py"
AAVE_RELEASE = PLUGIN_ROOT / "examples" / "aave-v4-spoke-v1-release"
AAVE_FIXTURE = AAVE_RELEASE / "fixture"
RELEASE_VARIABLES = {"v1": "WILDCAT_BOUNDARY_V1_RELEASE", "v2": "WILDCAT_BOUNDARY_V2_RELEASE"}
EVIDENCE_KEYS = ("proof_backed", "header_bound", "recorded_rpc", "receipt_trie_proved")
FIXTURE_COMPONENTS = {
    "anchors.jsonl", "header.json", "plan.json", "proofs.jsonl",
    "receipt-witness.json", "rpc.jsonl",
}
RELATION_CLASSES = ("proved", "header-bound", "recorded", "unsupported")
BATCH_ROWS = (
    "native.batch.scaledTotalAmount", "native.batch.scaledAmountBurned",
    "native.batch.normalizedAmountPaid",
)
SIMULATED_MARKET = "0x605309f21c1864bb0522781a2f97b91fe3a48601"
SIMULATED_EXPIRY = 1742310239
# getAvailableWithdrawalAmount takes the expired pending batch from the same
# simulation as getWithdrawalBatch, so its row carries the pair too (S2-R1-01).
AVAILABLE_ROW = "native.availableWithdrawal"
AVAILABLE_BATCH_FIELDS = ("scaledTotalAmount", "normalizedAmountPaid")
# The Step 1 artefacts by SHA-256, as the run's controller receipted them.
RECEIPTED = {
    "study.md": "718e79862c8ba29a88044eee8e893dcdb3d4f94297e5431aa17fe612e78c4972",
    "runbook.md": "c52fe58d80615fb291454ccdc1a3d9074ee7b7939356377d70c2cd93b80b9a66",
    "design-evidence.json": "6ff7cd6915dafcd5c9c4bca04219821a0b1df5180cc7eb135ed1503848b669ca",
}
# Every file `capture_requests.py` reads when it expands the inventory.
VALUE_MAP_INPUTS = (
    "scope.json", "population.json", "request-spec.json", "selectors.json",
    "capture_requests.py",
)
URL_OR_CREDENTIAL = (
    re.compile(r"https?://"),
    re.compile(r"\b[a-z0-9-]+\.(?:com|net|org|io|xyz|fi|app|dev)\b"),
    re.compile(r"Bearer [A-Za-z0-9._~+/=-]{20,}"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|token)\b\s*[:=]\s*[\"']?"
        r"[A-Za-z0-9._~+/=-]{16,}"
    ),
    re.compile(r"\bsk_(?:live|test)_"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{16,}"),
    re.compile(r"-----BEGIN "),
    re.compile(r"/(?:Users|home)/"),
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_generator(generation, probe, out, *, cwd=REPO_ROOT, generator=GENERATOR):
    argv = [
        sys.executable, str(generator), "--generation", generation,
        "--probe", str(probe), "--out", str(out),
    ]
    # Bytecode caches are the one write the interpreter would add beside the
    # generator and the value map; the tree stays quiescent without them.
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        argv, cwd=cwd, env=environment, capture_output=True, text=True,
        check=False, timeout=600,
    )


def plan_counts(plan):
    return {
        "requests": len(plan["requests"]),
        "proof_targets": len(plan["proof_targets"]),
        "slots": sum(len(target["slots"]) for target in plan["proof_targets"]),
    }


_REGENERATED = {}


def regenerated_plans():
    """Both plans, generated once per process: the V2 plan is about 7 MB."""
    if not _REGENERATED:
        scratch = tempfile.TemporaryDirectory()
        unittest.addModuleCleanup(scratch.cleanup)
        record = json.loads((EXAMPLE / "plans.json").read_text(encoding="utf-8"))
        for generation in GENERATIONS:
            out = Path(scratch.name) / f"{generation}.json"
            probe = EXAMPLE / record["plans"][generation]["probe"]
            completed = run_generator(generation, probe, out)
            if completed.returncode != 0:
                raise AssertionError(f"{generation}: {completed.stderr.strip()}")
            _REGENERATED[generation] = (out, json.loads(completed.stdout))
    return _REGENERATED


def plans_record():
    return json.loads((EXAMPLE / "plans.json").read_text(encoding="utf-8"))


def read_example(name):
    return json.loads((EXAMPLE / name).read_text(encoding="utf-8"))


class RegeneratedPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = plans_record()
        cls.plans = regenerated_plans()

    def check(self, generation):
        out, printed = self.plans[generation]
        expected = self.record["plans"][generation]
        data = out.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), expected["sha256"])
        self.assertEqual(len(data), expected["bytes"])
        self.assertEqual(printed["sha256"], expected["sha256"])
        self.assertEqual(printed["bytes"], expected["bytes"])
        plan = json.loads(data)
        counted = plan_counts(plan)
        for key in ("requests", "proof_targets", "slots"):
            with self.subTest(key=key):
                self.assertEqual(counted[key], expected[key])
                self.assertEqual(printed[key], expected[key])
        self.assertEqual(int(plan["block"]["number"], 16), expected["block_number"])
        self.assertEqual(plan["block"]["hash"], expected["block_hash"])
        self.assertEqual(plan["limits"]["max_elapsed_seconds"], expected["max_elapsed_seconds"])

    def test_v1_plan_regenerates_to_the_committed_record(self):
        self.check("v1")

    def test_v2_plan_regenerates_to_the_committed_record(self):
        self.check("v2")

    def test_lazarus_plan_validation_accepts_both_plans(self):
        for generation in GENERATIONS:
            with self.subTest(generation=generation):
                validate_document("plan", load(self.plans[generation][0]))

    def test_record_agrees_with_the_study_plan_summaries(self):
        for generation in GENERATIONS:
            summary = json.loads(
                (DOCS / "design" / "plans" / f"{generation}-full.summary.json")
                .read_text(encoding="utf-8")
            )
            expected = self.record["plans"][generation]
            with self.subTest(generation=generation):
                self.assertFalse(summary["state_words_only"])
                for key in ("sha256", "bytes", "requests", "proof_targets", "slots"):
                    self.assertEqual(summary[key], expected[key], key)

    def test_plans_carry_no_provider_coordinate(self):
        for generation in GENERATIONS:
            text = self.plans[generation][0].read_text(encoding="utf-8")
            with self.subTest(generation=generation):
                self.assertNotIn("://", text)
                plan = json.loads(text)
                self.assertEqual(
                    [source["source_id"] for source in plan["anchor_sources"]],
                    ["local-archive", "public-archive"],
                )


class GeneratorRefusalTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def test_refuses_a_request_inventory_that_differs_from_the_request_spec(self):
        kickoff = self.root / "docs" / "kickoff" / "1384"
        kickoff.mkdir(parents=True)
        for name in VALUE_MAP_INPUTS:
            shutil.copy(KICKOFF / name, kickoff / name)
        spec_path = kickoff / "request-spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        digest = spec["expanded_requests"]["v1"]["sha256"]
        spec["expanded_requests"]["v1"]["sha256"] = ("1" if digest[0] == "0" else "0") + digest[1:]
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        out = self.root / "plan.json"
        completed = run_generator("v1", EXAMPLE / "probe-v1.json", out, cwd=self.root)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("request inventory bytes disagree with request-spec.json", completed.stderr)
        self.assertFalse(out.exists())

    def test_refuses_a_market_whose_derived_word_count_differs_from_its_probe(self):
        copy = self.root / "example"
        copy.mkdir()
        for name in ("plan_v3.py", "wildcat_slots.py", "probe-v1.json"):
            shutil.copy(EXAMPLE / name, copy / name)
        probe_path = copy / "probe-v1.json"
        record = json.loads((EXAMPLE / "plans.json").read_text(encoding="utf-8"))
        # The unaltered copy still produces the committed plan, so the refusal
        # below is the probe change and not the relocation.
        control = self.root / "control.json"
        completed = run_generator("v1", probe_path, control, generator=copy / "plan_v3.py")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(sha256(control), record["plans"]["v1"]["sha256"])
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
        market = sorted(probe["fifo"])[0]
        read = probe["market_slots"][market]["accounts"]
        probe["market_slots"][market]["accounts"] = read + 1
        probe_path.write_text(json.dumps(probe), encoding="utf-8")
        out = self.root / "plan.json"
        completed = run_generator("v1", probe_path, out, generator=copy / "plan_v3.py")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            f"{market} accounts: generator derives {read} words, probe read {read + 1}",
            completed.stderr,
        )
        self.assertFalse(out.exists())

    def test_refuses_a_probe_outside_its_own_directory(self):
        probe = self.root / "probe-v1.json"
        shutil.copy(EXAMPLE / "probe-v1.json", probe)
        out = self.root / "plan.json"
        completed = run_generator("v1", probe, out)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("inside the generator's own directory", completed.stderr)
        self.assertFalse(out.exists())

    def test_refuses_an_output_path_that_exists(self):
        out = self.root / "plan.json"
        out.write_bytes(b"keep me\n")
        completed = run_generator("v1", EXAMPLE / "probe-v1.json", out)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("already exists", completed.stderr)
        self.assertEqual(out.read_bytes(), b"keep me\n")

    def test_refuses_an_output_path_that_is_a_symlink(self):
        target = self.root / "target.json"
        target.write_bytes(b"keep me\n")
        linked = self.root / "linked.json"
        linked.symlink_to(target)
        dangling = self.root / "dangling.json"
        dangling.symlink_to(self.root / "absent.json")
        for out in (linked, dangling):
            with self.subTest(out=out.name):
                completed = run_generator("v1", EXAMPLE / "probe-v1.json", out)
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertIn("is a symlink", completed.stderr)
        self.assertEqual(target.read_bytes(), b"keep me\n")
        self.assertFalse((self.root / "absent.json").exists())

    def test_refuses_to_run_outside_the_repository_root(self):
        out = self.root / "plan.json"
        completed = run_generator("v1", EXAMPLE / "probe-v1.json", out, cwd=self.root)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("run from the repository root", completed.stderr)
        self.assertFalse(out.exists())


class CommittedRecordTests(unittest.TestCase):
    def test_docs_copies_match_the_receipted_digests(self):
        for name, digest in RECEIPTED.items():
            with self.subTest(name=name):
                self.assertEqual(sha256(DOCS / name), digest)
        runbook = (DOCS / "runbook.md").read_text(encoding="utf-8")
        lock = re.search(r"```design-lock\n(.*?)```", runbook, re.S)
        self.assertIsNotNone(lock)
        rows = dict(line.split(" | ", 1) for line in lock.group(1).strip().splitlines())
        self.assertEqual(rows["sha256"], RECEIPTED["design-evidence.json"])
        self.assertEqual(rows["candidate"], "full-map-r2-handoff")

    def test_design_record_reports_resolve_from_the_copied_record(self):
        record = json.loads((DOCS / "design-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(record["selection"]["candidate"], "full-map-r2-handoff")
        resolved = 0
        pending = []
        for result in record["results"]:
            report = result["report"]
            if isinstance(report, dict):
                path = DOCS / report["path"]
                with self.subTest(path=report["path"]):
                    self.assertTrue(path.is_file())
                    self.assertEqual(sha256(path), report["sha256"])
                resolved += 1
            else:
                pending.append((result["state"], result["criterion"]))
        self.assertEqual(resolved, 36)
        self.assertEqual(
            sorted(p.name for p in (DOCS / "design" / "reports").iterdir() if p.is_file()),
            sorted(Path(r["report"]["path"]).name for r in record["results"]
                   if isinstance(r["report"], dict)),
        )
        # The two conformance cells stay pending for every candidate until
        # integration; their reports are not part of this step's copy.
        self.assertEqual({state for state, _ in pending}, {"pending"})
        self.assertEqual(
            {criterion for _, criterion in pending},
            {"altered-bytes-refused", "state-fixture-v2-binds"},
        )

    def test_example_files_carry_no_url_or_credential_pattern(self):
        names = {path.name for path in EXAMPLE.iterdir() if path.is_file()}
        self.assertEqual(names, COMMITTED_EXAMPLE_FILES)
        for name in sorted(COMMITTED_EXAMPLE_FILES):
            text = (EXAMPLE / name).read_text(encoding="utf-8")
            if name in GENERATED_DOCUMENTS:
                for identifier in TYPE_IDENTIFIERS:
                    text = text.replace(identifier, "")
            for pattern in URL_OR_CREDENTIAL:
                with self.subTest(name=name, pattern=pattern.pattern):
                    self.assertIsNone(pattern.search(text))

    def test_generator_imports_no_network_module(self):
        for name in ("plan_v3.py", "wildcat_slots.py", "relations.py", "demo.py", "archive.py"):
            text = (EXAMPLE / name).read_text(encoding="utf-8")
            for module in ("urllib", "socket", "http", "requests", "ssl"):
                with self.subTest(name=name, module=module):
                    self.assertNotRegex(text, rf"(?m)^\s*(?:import|from)\s+{module}\b")
        self.assertIn('KICKOFF = Path("docs/kickoff/1384")', GENERATOR.read_text(encoding="utf-8"))


def load_probe_module():
    """Import the study-time probe by path; nothing at import time reaches a network."""
    spec = importlib.util.spec_from_file_location("wildcat_boundary_probe", EXAMPLE / "probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProbeSummaryTests(unittest.TestCase):
    """The probe's route report carries no provider text (S1-R1-01)."""

    def test_refused_route_keeps_the_code_and_no_provider_text(self):
        probe = load_probe_module()
        # Composed at run time so no committed file carries the pattern.
        quoted = (
            "Archive requests require a personal token. Get one at: "
            + "https:" + "//provider.example/token"
        )
        outcome = probe.sanitised_outcome({"error": {"code": -32602, "message": quoted}}, 91)
        self.assertEqual(
            outcome, {"outcome": "refused", "code": -32602, "message": "provider request failed"}
        )
        text = json.dumps(outcome)
        self.assertNotIn("://", text)
        self.assertNotIn("Get one at", text)
        for pattern in URL_OR_CREDENTIAL:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(pattern.search(text))

    def test_served_and_shapeless_answers_carry_no_text_either(self):
        probe = load_probe_module()
        self.assertEqual(probe.sanitised_outcome({"result": "0x"}, 12), {"outcome": "served", "bytes": 12})
        self.assertEqual(
            probe.sanitised_outcome([], 0),
            {"outcome": "refused", "code": None, "message": "provider request failed"},
        )
        self.assertEqual(
            probe.sanitised_outcome({"error": {"code": "-32602", "message": "x"}}, 0),
            {"outcome": "refused", "code": None, "message": "provider request failed"},
        )


def load_driver():
    """Import the capture driver by path; importing it opens no connection."""
    spec = importlib.util.spec_from_file_location("wildcat_boundary_capture", DRIVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_driver(driver, argv, **kwargs):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = driver.main(argv, **kwargs)
    return code, stdout.getvalue(), stderr.getvalue()


class CaptureDriverTests(unittest.TestCase):
    """The bearer reaches Lazarus as a header and nothing else sees it."""

    @classmethod
    def setUpClass(cls):
        cls.driver = load_driver()
        cls.plan = regenerated_plans()["v1"][0]
        cls.record = plans_record()["plans"]["v1"]

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.out = self.root / "fixture"
        # Composed at run time so no committed file carries either pattern.
        self.url = "https:" + "//gateway.test/rpc/" + "k" * 24
        self.token = "tok-" + "q" * 40
        self.environment = {
            self.driver.GATEWAY_URL_VARIABLE: self.url,
            self.driver.GATEWAY_HEADER_VARIABLE: self.token,
        }
        self.calls = []

    def argv(self, plan=None, out=None):
        return [
            "capture", "--generation", "v1",
            "--plan", str(plan or self.plan), "--out", str(out or self.out),
        ]

    def stand_in(self, plan, rpc_url, output, **kwargs):
        self.calls.append((plan, rpc_url, output, kwargs))
        return {
            "fixture_digest": "0" * 64,
            "terminal_result": {
                "event": "lazarus.capture.completed", "stage": "fixture-finalised",
                "counts": {"rpc_requests": 3}, "fixture_digest": "0" * 64,
            },
        }

    def assert_no_value(self, *texts):
        for text in texts:
            self.assertNotIn(self.token, text)
            self.assertNotIn(self.url, text)
            self.assertNotIn("gateway.test", text)

    def test_refuses_when_either_named_variable_is_unset(self):
        for missing in (self.driver.GATEWAY_URL_VARIABLE, self.driver.GATEWAY_HEADER_VARIABLE):
            environment = {k: v for k, v in self.environment.items() if k != missing}
            with self.subTest(missing=missing):
                code, out, err = run_driver(
                    self.driver, self.argv(), environment=environment, routine=self.stand_in,
                )
                self.assertEqual(code, 2)
                self.assertIn(f"environment variable {missing} is unset", err)
                self.assertEqual(out, "")
                self.assertEqual(self.calls, [])
                self.assertFalse(self.out.exists())
        empty = dict(self.environment, **{self.driver.GATEWAY_HEADER_VARIABLE: ""})
        code, _, err = run_driver(
            self.driver, self.argv(), environment=empty, routine=self.stand_in,
        )
        self.assertEqual(code, 2)
        self.assertIn("is unset", err)
        self.assertEqual(self.calls, [])

    def test_refuses_an_existing_or_symlinked_output(self):
        self.out.mkdir()
        code, _, err = run_driver(
            self.driver, self.argv(), environment=self.environment, routine=self.stand_in,
        )
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)
        link = self.root / "link"
        link.symlink_to(self.root / "absent")
        code, _, err = run_driver(
            self.driver, self.argv(out=link), environment=self.environment,
            routine=self.stand_in,
        )
        self.assertEqual(code, 2)
        self.assertIn("is a symlink", err)
        self.assertEqual(self.calls, [])

    def test_refuses_a_plan_that_is_not_the_recorded_one(self):
        altered = self.root / "plan.json"
        altered.write_bytes(self.plan.read_bytes() + b"\n")
        code, _, err = run_driver(
            self.driver, self.argv(plan=altered), environment=self.environment,
            routine=self.stand_in,
        )
        self.assertEqual(code, 2)
        self.assertIn("is not the v1 plan that plans.json records", err)
        self.assertEqual(self.calls, [])

    def test_bearer_travels_only_as_a_request_header(self):
        argv = self.argv()
        code, out, err = run_driver(
            self.driver, argv, environment=self.environment, routine=self.stand_in,
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.calls), 1)
        plan, rpc_url, output, kwargs = self.calls[0]
        self.assertEqual(Path(plan), self.plan)
        self.assertEqual(Path(output), self.out)
        self.assertEqual(rpc_url, self.url)
        self.assertEqual(kwargs["headers"], {"authorization": "Bearer " + self.token})
        self.assertEqual(
            kwargs["anchor_rpc_env"],
            ["local-archive=RETH_RPC_URL", "public-archive=PUBLIC_ARCHIVE_RPC_URL"],
        )
        self.assertIsInstance(kwargs["terminal_context"], dict)
        self.assert_no_value(" ".join(argv), out, err)
        self.assertEqual(err, "")
        envelope = json.loads(out)
        self.assertEqual(envelope["schema"], "wildcat-boundary-capture-terminal/v1")
        self.assertEqual(envelope["generation"], "v1")
        self.assertEqual(envelope["plan_sha256"], self.record["sha256"])
        self.assertIsInstance(envelope["elapsed_seconds"], float)
        self.assertEqual(envelope["terminal_result"]["stage"], "fixture-finalised")
        for pattern in URL_OR_CREDENTIAL:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(pattern.search(out))

    def test_failure_result_goes_to_stderr_without_a_value(self):
        from lazarus_lib.capture import CaptureError

        def failing(plan, rpc_url, output, **kwargs):
            kwargs["terminal_context"].update({
                "correlation_id": "lazarus-capture:" + "0" * 64, "mode": "scoped",
                "stage": "staging", "block": {"number": "0x1", "hash": "0x" + "1" * 64},
                "recorded_target_selector": {"value": None, "evidence": "recorded_rpc",
                                             "transaction_index": None},
                "counts": {"rpc_requests": 0, "rpc_response_bytes": 0},
                "versions": {"plan": 3, "receipt_witness": 1},
            })
            raise CaptureError("capture failed at staging")

        code, out, err = run_driver(
            self.driver, self.argv(), environment=self.environment, routine=failing,
        )
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        failure = json.loads(err)
        self.assertEqual(failure["terminal_result"]["event"], "lazarus.capture.failed")
        self.assertEqual(failure["terminal_result"]["stage"], "staging")
        self.assertEqual(failure["terminal_result"]["failure"], "capture")
        self.assert_no_value(err)
        self.assertFalse(self.out.exists())

    def synthetic_fixture(self):
        """A fixture directory plus stand-ins for the two Lazarus reads ``record`` makes."""
        fixture = self.root / "finished"
        fixture.mkdir()
        manifest = {
            "fixture_digest": "f" * 64,
            "components": [
                {"path": name, "bytes": 1, "sha256": "0" * 64}
                for name in sorted(FIXTURE_COMPONENTS)
            ],
        }
        (fixture / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        report = {"manifest": manifest, "evidence_counts": {"proof_backed": 265}}
        plan = {
            "block": {"number": hex(self.record["block_number"]), "hash": self.record["block_hash"]},
            "requests": [{}] * self.record["requests"],
            "proof_targets": [{"slots": [0] * self.record["slots"]}]
            + [{"slots": []}] * (self.record["proof_targets"] - 1),
            "limits": {"max_elapsed_seconds": self.record["max_elapsed_seconds"]},
        }
        return fixture, report, plan

    def envelope_text(self, elapsed):
        envelope = {
            "schema": "wildcat-boundary-capture-terminal/v1", "generation": "v1",
            "plan_sha256": self.record["sha256"], "elapsed_seconds": 0,
            "terminal_result": {
                "event": "lazarus.capture.completed", "stage": "fixture-finalised",
                "fixture_digest": "f" * 64, "counts": {"rpc_requests": 3},
            },
        }
        # A raw token stands in for the value so NaN and Infinity, which
        # json.dumps would otherwise refuse or spell itself, reach the parser.
        return json.dumps(envelope).replace('"elapsed_seconds": 0', f'"elapsed_seconds": {elapsed}')

    def test_record_keeps_a_measured_float_and_refuses_a_non_finite_or_boolean_one(self):
        """``record`` reads the envelope with the standard parser (S2-R1-03)."""
        fixture, report, plan = self.synthetic_fixture()
        terminal = self.root / "terminal.json"

        def record(elapsed, out):
            terminal.write_text(self.envelope_text(elapsed), encoding="utf-8")
            argv = ["record", "--generation", "v1", "--fixture", str(fixture),
                    "--terminal", str(terminal), "--out", str(out)]
            with mock.patch.object(self.driver, "verify_fixture", return_value=report), \
                    mock.patch.object(self.driver, "load", return_value=plan):
                return run_driver(self.driver, argv)

        out = self.root / "capture-v1.json"
        code, printed, err = record("26.322", out)
        self.assertEqual(code, 0, err)
        written = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(written["schema"], "wildcat-boundary-capture-record/v1")
        self.assertEqual(written["plan"], self.record)
        self.assertEqual(written["fixture"]["fixture_digest"], "f" * 64)
        self.assertIsInstance(written["capture"]["elapsed_seconds"], float)
        self.assertEqual(written["capture"]["elapsed_seconds"], 26.322)
        self.assertEqual(json.loads(printed)["fixture_digest"], "f" * 64)
        for index, token in enumerate(("NaN", "Infinity", "-Infinity", "true")):
            fresh = self.root / f"refused-{index}.json"
            with self.subTest(token=token):
                code, printed, err = record(token, fresh)
                self.assertEqual(code, 2)
                self.assertEqual(printed, "")
                self.assertIn("refusing:", err)
                self.assertFalse(fresh.exists())

    def test_record_refuses_an_existing_output_and_a_provider_pattern(self):
        terminal = self.root / "terminal.json"
        terminal.write_text("{}", encoding="utf-8")
        existing = self.root / "capture-v1.json"
        existing.write_text("{}", encoding="utf-8")
        argv = ["record", "--generation", "v1", "--fixture", str(self.root),
                "--terminal", str(terminal), "--out", str(existing)]
        code, _, err = run_driver(self.driver, argv)
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)
        terminal.write_text(json.dumps({"note": self.url}), encoding="utf-8")
        argv[-1] = str(self.root / "fresh.json")
        code, _, err = run_driver(self.driver, argv)
        self.assertEqual(code, 2)
        self.assertIn("provider pattern", err)
        self.assert_no_value(err)
        self.assertFalse((self.root / "fresh.json").exists())


class CommittedCaptureRecordTests(unittest.TestCase):
    """Each capture record's counts equal the plan's and name one fixture."""

    @classmethod
    def setUpClass(cls):
        cls.plans = plans_record()["plans"]
        cls.records = {g: read_example(f"capture-{g}.json") for g in GENERATIONS}

    def test_record_counts_equal_the_plan_counts(self):
        for generation in GENERATIONS:
            record = self.records[generation]
            plan = self.plans[generation]
            counts = record["verify"]["evidence_counts"]
            terminal = record["capture"]["terminal_result"]
            with self.subTest(generation=generation):
                self.assertEqual(record["schema"], "wildcat-boundary-capture-record/v1")
                self.assertEqual(record["generation"], generation)
                self.assertEqual(record["plan"], plan)
                self.assertEqual(counts["proof_backed"], plan["proof_targets"] + plan["slots"])
                self.assertEqual(counts["header_bound"], 1)
                self.assertEqual(counts["recorded_rpc"], plan["requests"])
                self.assertEqual(counts["receipt_trie_proved"], 2)
                self.assertEqual(terminal["counts"]["recorded_rpc"], plan["requests"])
                self.assertEqual(terminal["counts"]["anchor_records"], 2)
                self.assertEqual(terminal["counts"]["receipt_trie_proved"], 2)
                self.assertGreaterEqual(terminal["counts"]["rpc_requests"], plan["requests"])
                self.assertEqual(record["verify"]["block_hash"], plan["block_hash"])
                self.assertEqual(int(record["verify"]["block_number"], 16), plan["block_number"])
                self.assertEqual(record["verify"]["manifest"]["evidence_counts"], counts)

    def test_record_names_one_fixture_and_its_components(self):
        for generation in GENERATIONS:
            record = self.records[generation]
            fixture = record["fixture"]
            digests = {
                fixture["fixture_digest"], record["verify"]["fixture_digest"],
                record["verify"]["manifest"]["fixture_digest"],
                record["capture"]["terminal_result"]["fixture_digest"],
            }
            with self.subTest(generation=generation):
                self.assertEqual(len(digests), 1)
                self.assertRegex(fixture["fixture_digest"], r"^[0-9a-f]{64}$")
                self.assertEqual({c["path"] for c in fixture["components"]}, FIXTURE_COMPONENTS)
                self.assertEqual(fixture["components"], record["verify"]["manifest"]["components"])
                for component in fixture["components"] + [fixture["manifest"]]:
                    self.assertGreater(component["bytes"], 0)
                    self.assertRegex(component["sha256"], r"^[0-9a-f]{64}$")
                self.assertEqual(fixture["manifest"]["path"], "manifest.json")

    def test_terminal_result_keeps_stage_counts_and_time_without_provider_identity(self):
        for generation in GENERATIONS:
            record = self.records[generation]
            capture = record["capture"]
            terminal = capture["terminal_result"]
            with self.subTest(generation=generation):
                self.assertEqual(terminal["event"], "lazarus.capture.completed")
                self.assertEqual(terminal["stage"], "fixture-finalised")
                self.assertGreater(capture["elapsed_seconds"], 0)
                self.assertLessEqual(
                    capture["elapsed_seconds"], self.plans[generation]["max_elapsed_seconds"]
                )
                self.assertGreater(terminal["counts"]["rpc_response_bytes"], 0)
                # The verify report's boolean claims name "provider" as a
                # word; the terminal result must not name one as a key.
                for key in ("url", "provider", "host", "bearer", "authorization"):
                    self.assertNotRegex(json.dumps(capture), rf'(?i)"{key}[a-z_]*"\s*:')
                text = json.dumps(record)
                for pattern in URL_OR_CREDENTIAL:
                    self.assertIsNone(pattern.search(text), pattern.pattern)


class ReadmeFigureTests(unittest.TestCase):
    """Every capture figure the README states is a committed record's or the study's (S2-R1-02)."""

    @classmethod
    def setUpClass(cls):
        cls.readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        cls.records = {g: read_example(f"capture-{g}.json") for g in GENERATIONS}
        cls.plans = plans_record()["plans"]

    def table_row(self, label):
        line = next(l for l in self.readme.splitlines() if l.startswith(f"| {label} |"))
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        self.assertEqual(cells[0], label)
        return cells[1:]

    def test_capture_table_repeats_the_committed_records(self):
        expected = {}
        for generation in GENERATIONS:
            record = self.records[generation]
            terminal = record["capture"]["terminal_result"]
            counts = record["verify"]["evidence_counts"]
            fixture = record["fixture"]
            component_bytes = sum(c["bytes"] for c in fixture["components"]) + fixture["manifest"]["bytes"]
            expected[generation] = {
                "Fixture digest": f"`{fixture['fixture_digest']}`",
                "Elapsed seconds": str(record["capture"]["elapsed_seconds"]),
                "RPC requests sent, response bytes":
                    f"{terminal['counts']['rpc_requests']:,}, {terminal['counts']['rpc_response_bytes']:,}",
                "Component bytes, with the manifest": f"{component_bytes:,}",
                "Proof-backed, header-bound, recorded-RPC, receipt-trie-proved":
                    f"{counts['proof_backed']:,}, {counts['header_bound']}, "
                    f"{counts['recorded_rpc']:,}, {counts['receipt_trie_proved']}",
                "Chain-anchor records": str(record["verify"]["chain_anchors"]["records"]),
                "Recorded calls whose outcome is an error":
                    str(len(record["verify"]["manifest"]["optional_failures"])),
            }
        for label in expected["v1"]:
            with self.subTest(label=label):
                self.assertEqual(
                    self.table_row(label), [expected[g][label] for g in GENERATIONS]
                )

    def test_projection_paragraph_states_only_recorded_seconds(self):
        study = (DOCS / "study.md").read_text(encoding="utf-8")
        projected = re.search(r"projected captures of ([0-9.]+) s and ([0-9.]+) s", study)
        self.assertIsNotNone(projected)
        paragraph = next(
            block for block in self.readme.split("\n\n") if block.startswith("The study projected")
        )
        stated = set(re.findall(r"(\d[\d,]*(?:\.\d+)?) s\b", paragraph))
        allowed = set(projected.groups()) | {
            str(self.records[g]["capture"]["elapsed_seconds"]) for g in GENERATIONS
        } | {f"{self.plans['v2']['max_elapsed_seconds']:,}"}
        # A figure the README derives by hand is neither a record nor the study.
        self.assertEqual(stated, allowed)
        for generation in GENERATIONS:
            self.assertIn(f"{self.records[generation]['capture']['elapsed_seconds']} s", paragraph)


class RelationReportTests(unittest.TestCase):
    """All 61 rows carry one class, and every backing entry is in the plan or record."""

    @classmethod
    def setUpClass(cls):
        cls.plans = regenerated_plans()
        cls.values = json.loads((KICKOFF / "values.json").read_text(encoding="utf-8"))["rows"]
        cls.selectors = json.loads((KICKOFF / "selectors.json").read_text(encoding="utf-8"))
        cls.reports = {g: read_example(f"relations-{g}.json") for g in GENERATIONS}
        cls.records = {g: read_example(f"capture-{g}.json") for g in GENERATIONS}

    def plan_index(self, generation):
        plan = json.loads(self.plans[generation][0].read_text(encoding="utf-8"))
        targets = {t["address"]: set(t["slots"]) for t in plan["proof_targets"]}
        requests = {r["name"]: r for r in plan["requests"]}
        return targets, requests

    def family_names(self, requests, item):
        names = []
        for name, request in requests.items():
            if request["method"] != item["method"]:
                continue
            if item["method"] == "eth_call":
                if not request["params"][0]["data"].lower().startswith(item["selector"].lower()):
                    continue
            names.append(name)
        return sorted(names)

    def test_every_row_has_one_class_and_a_backing_entry(self):
        expected_ids = [row["id"] for row in self.values]
        for generation in GENERATIONS:
            report = self.reports[generation]
            targets, requests = self.plan_index(generation)
            header = next(c for c in self.records[generation]["fixture"]["components"]
                          if c["path"] == "header.json")
            with self.subTest(generation=generation):
                self.assertEqual([row["id"] for row in report["rows"]], expected_ids)
                self.assertEqual(len(report["rows"]), 61)
                tally = {name: 0 for name in RELATION_CLASSES}
                for row in report["rows"]:
                    self.assertIn(row["class"], RELATION_CLASSES)
                    tally[row["class"]] += 1
                    if row["class"] == "unsupported":
                        continue
                    self.assertTrue(row["proof"], row["id"])
                    for item in row["proof"]:
                        if item["kind"] == "header":
                            self.assertEqual(item["sha256"], header["sha256"])
                            continue
                        self.assertEqual(item["kind"], "proof-target")
                        first = item["first"]
                        self.assertIn(first["address"], targets)
                        if "slot" in first:
                            self.assertIn(first["slot"], targets[first["address"]])
                        self.assertLessEqual(item["targets"], len(targets))
                    for item in row["recorded"]:
                        names = self.family_names(requests, item)
                        self.assertEqual(item["requests"], len(names), row["id"])
                        self.assertEqual(item["first"], names[0])
                        digest = hashlib.sha256(("\n".join(names) + "\n").encode()).hexdigest()
                        self.assertEqual(item["sha256"], digest)
                self.assertEqual(report["classes"], tally)
                self.assertEqual(sum(tally.values()), 61)
                self.assertEqual(report["classes"]["proved"] + report["classes"]["header-bound"], 44)

    def test_unsupported_rows_have_no_proof_target(self):
        for generation in GENERATIONS:
            report = self.reports[generation]
            by_id = {row["id"]: row for row in report["rows"]}
            with self.subTest(generation=generation):
                for row in self.values:
                    marked = row["status"].startswith("unsupported")
                    absent = generation not in row["generations"]
                    entry = by_id[row["id"]]
                    if marked or absent:
                        self.assertEqual(entry["class"], "unsupported", row["id"])
                        self.assertEqual(entry["proof"], [])
                        self.assertEqual(entry["recorded"], [])
                        self.assertEqual(
                            entry["reason"],
                            "not-in-generation" if absent else row["status"],
                        )
                    else:
                        self.assertNotEqual(entry["class"], "unsupported", row["id"])
                        self.assertNotIn("reason", entry)

    def test_simulated_batch_pair_carries_its_differing_view(self):
        v1 = {row["id"]: row for row in self.reports["v1"]["rows"]}
        v2 = {row["id"]: row for row in self.reports["v2"]["rows"]}
        self.assertEqual(self.reports["v1"]["differing_recorded_views"], 1)
        self.assertEqual(self.reports["v2"]["differing_recorded_views"], 0)
        differing = 0
        for identity in BATCH_ROWS:
            views = v1[identity]["differing_recorded_view"]
            self.assertEqual(len(views), 1, identity)
            self.assertEqual(views[0]["market"], SIMULATED_MARKET)
            self.assertEqual(views[0]["expiry"], SIMULATED_EXPIRY)
            self.assertEqual(views[0]["differs"], views[0]["stored"] != views[0]["view"])
            differing += views[0]["differs"]
            self.assertEqual(v1[identity]["class"], "proved")
            self.assertEqual(v2[identity]["differing_recorded_view"], [])
        self.assertEqual(differing, 2)
        population = json.loads((KICKOFF / "population.json").read_text(encoding="utf-8"))
        accounts = sorted(
            pair["account"].lower()
            for pair in population["v1"][SIMULATED_MARKET]["account_batches"]
            if int(pair["expiry"]) == SIMULATED_EXPIRY
        )
        self.assertEqual(len(accounts), 1)
        batch = v1[BATCH_ROWS[0]]["differing_recorded_view"][0]
        paid = v1[BATCH_ROWS[2]]["differing_recorded_view"][0]
        self.assertIn("differing_recorded_view", v1[AVAILABLE_ROW])
        views = v1[AVAILABLE_ROW]["differing_recorded_view"]
        self.assertEqual(len(views), 1)
        available = views[0]
        self.assertEqual(available["market"], SIMULATED_MARKET)
        self.assertEqual(available["expiry"], SIMULATED_EXPIRY)
        self.assertEqual(available["accounts"], accounts)
        self.assertEqual(set(available["stored"]), set(AVAILABLE_BATCH_FIELDS))
        self.assertEqual(
            available["stored"],
            {"scaledTotalAmount": batch["stored"], "normalizedAmountPaid": paid["stored"]},
        )
        self.assertEqual(
            available["view"],
            {"scaledTotalAmount": batch["view"], "normalizedAmountPaid": paid["view"]},
        )
        self.assertTrue(available["differs"])
        self.assertEqual(available["differs"], available["stored"] != available["view"])
        self.assertIn("getAvailableWithdrawalAmount", available["cause"])
        self.assertEqual(v2[AVAILABLE_ROW]["differing_recorded_view"], [])
        for report in (v1, v2):
            row = report[AVAILABLE_ROW]
            self.assertEqual(row["class"], "proved")
            words = {item["words"] for item in row["proof"] if item["kind"] == "proof-target"}
            self.assertLessEqual({"statuses", "batches", "state", "code", "balances"}, words)
            self.assertEqual([item["kind"] for item in row["proof"]].count("header"), 1)
        for identity, row in v1.items():
            if identity not in BATCH_ROWS + (AVAILABLE_ROW,):
                self.assertNotIn("differing_recorded_view", row)

    def test_report_legend_keeps_recorded_responses_outside_proved(self):
        """Each report says what its classes cover and that a recorded response is never proved (S2-R2-01)."""
        for generation in GENERATIONS:
            report = self.reports[generation]
            with self.subTest(generation=generation):
                self.assertIn("legend", report)
                legend = report["legend"]
                self.assertEqual(
                    set(legend), set(RELATION_CLASSES) | {"recorded_entries"}
                )
                self.assertIn("under proof", legend["proved"])
                self.assertIn("nothing else", legend["proved"])
                self.assertIn("never proved", legend["recorded_entries"])
                self.assertIn("differing_recorded_view", legend["recorded_entries"])
                for text in legend.values():
                    self.assertIsInstance(text, str)
                    self.assertTrue(text)

    def test_report_binds_the_committed_capture_record_and_plan(self):
        plans = plans_record()["plans"]
        for generation in GENERATIONS:
            report = self.reports[generation]
            record = self.records[generation]
            with self.subTest(generation=generation):
                self.assertEqual(report["schema"], "wildcat-boundary-relations/v1")
                self.assertEqual(report["plan_sha256"], plans[generation]["sha256"])
                self.assertEqual(report["block"]["hash"], plans[generation]["block_hash"])
                self.assertEqual(report["block"]["number"], plans[generation]["block_number"])
                self.assertEqual(report["capture_record"]["path"], f"capture-{generation}.json")
                self.assertEqual(
                    report["capture_record"]["sha256"], sha256(EXAMPLE / f"capture-{generation}.json")
                )
                self.assertEqual(
                    report["capture_record"]["fixture_digest"], record["fixture"]["fixture_digest"]
                )

    def test_generator_reproduces_the_report_and_refuses_an_existing_output(self):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for generation in GENERATIONS:
            with tempfile.TemporaryDirectory() as scratch, self.subTest(generation=generation):
                out = Path(scratch) / f"relations-{generation}.json"
                argv = [
                    sys.executable, str(RELATIONS), "--generation", generation,
                    "--plan", str(self.plans[generation][0]), "--out", str(out),
                ]
                completed = subprocess.run(
                    argv, cwd=REPO_ROOT, env=environment, capture_output=True,
                    text=True, check=False, timeout=600,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(
                    out.read_bytes(), (EXAMPLE / f"relations-{generation}.json").read_bytes()
                )
                repeated = subprocess.run(
                    argv, cwd=REPO_ROOT, env=environment, capture_output=True,
                    text=True, check=False, timeout=600,
                )
                self.assertEqual(repeated.returncode, 2)
                self.assertIn("already exists", repeated.stderr)


def run_demo(*argv, environment=None, cwd=REPO_ROOT):
    env = dict(os.environ if environment is None else environment, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, str(DEMO), *argv], cwd=cwd, env=env, capture_output=True,
        text=True, check=False, timeout=1800,
    )


def run_archiver(*argv, cwd=REPO_ROOT):
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, str(ARCHIVER), *argv], cwd=cwd, env=environment,
        capture_output=True, text=True, check=False, timeout=600,
    )


def load_demo():
    """Import the demonstration by path; importing it runs nothing."""
    spec = importlib.util.spec_from_file_location("wildcat_boundary_demo", DEMO)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_digests(root):
    """Every file below ``root`` by relative path and SHA-256, to prove a tree untouched."""
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(Path(root).rglob("*")) if path.is_file()
    }


def copy_example(destination):
    shutil.copytree(EXAMPLE, destination, ignore=shutil.ignore_patterns("__pycache__"))
    return Path(destination)


def flip_hex(value):
    return ("1" if value[0] == "0" else "0") + value[1:]


def release_variables(v1, v2):
    return dict(os.environ, **{RELEASE_VARIABLES["v1"]: str(v1), RELEASE_VARIABLES["v2"]: str(v2)})


class CommittedReleaseRecordTests(unittest.TestCase):
    """Each statement's counts are the capture record's; each release names what the inventory records."""

    @classmethod
    def setUpClass(cls):
        cls.records = {g: read_example(f"capture-{g}.json") for g in GENERATIONS}
        cls.statements = {g: read_example(f"statement-{g}.json") for g in GENERATIONS}
        cls.releases = {g: read_example(f"release-{g}.json") for g in GENERATIONS}
        cls.archives = read_example("archives.json")

    def test_statement_counts_equal_the_capture_records_verify_report(self):
        for generation in GENERATIONS:
            statement = self.statements[generation]
            verify = self.records[generation]["verify"]
            predicate = statement["predicate"]
            with self.subTest(generation=generation):
                self.assertEqual(statement["_type"], IN_TOTO_STATEMENT_TYPE)
                self.assertEqual(statement["predicateType"], STATE_FIXTURE_TYPE_V2)
                self.assertEqual(list(predicate["evidence"]), list(EVIDENCE_KEYS))
                self.assertEqual(predicate["evidence"], verify["evidence_counts"])
                for key in EVIDENCE_KEYS:
                    self.assertIsInstance(predicate["evidence"][key], int)
                    self.assertNotIsInstance(predicate["evidence"][key], bool)
                self.assertEqual(predicate["chain"], {
                    "chain_id": 1,
                    "block_number": int(verify["block_number"], 16),
                    "block_hash": verify["block_hash"],
                    "state_root": verify["state_root"],
                    "receipts_root": verify["receipts_root"],
                })
                components = {c["path"]: c for c in self.records[generation]["fixture"]["components"]}
                self.assertEqual(
                    {s["path"]: (s["bytes"], s["digest"]["sha256"]) for s in predicate["fixture_subjects"]},
                    {p: (c["bytes"], c["sha256"]) for p, c in components.items()},
                )
                subjects = {s["digest"]["sha256"] for s in statement["subject"]}
                self.assertLessEqual({c["sha256"] for c in components.values()}, subjects)
                self.assertIsNone(predicate["deltas"]["baseline"])
                self.assertEqual(predicate["deltas"]["current"]["name"], f"wildcat-boundary-{generation}")
                self.assertEqual(predicate["replay"], {
                    "reaches_network": False, "canonical_chain_claim": False,
                    "provider_independence_claim": False,
                })
                self.assertEqual(predicate["commands"], [])
                command = predicate["capture"]["command"]
                self.assertEqual(command[:3], ["python3", "plugins/lazarus/examples/wildcat-boundary-v0/capture.py", "capture"])
                self.assertIn(generation, command)
                for word in command:
                    for pattern in URL_OR_CREDENTIAL:
                        self.assertIsNone(pattern.search(word), word)

    def test_release_document_names_the_statement_and_fixture_the_inventory_records(self):
        for generation in GENERATIONS:
            release = self.releases[generation]
            record = self.records[generation]
            statement_bytes = (EXAMPLE / f"statement-{generation}.json").read_bytes()
            archive = next(
                a for a in self.archives["archives"]
                if a["generation"] == generation and a["contents"] == "lazarus-release"
            )
            with self.subTest(generation=generation):
                self.assertEqual(release["schema_version"], 2)
                self.assertEqual(release["statement"]["predicate_type"], STATE_FIXTURE_TYPE_V2)
                self.assertEqual(release["statement"]["sha256"], hashlib.sha256(statement_bytes).hexdigest())
                self.assertEqual(release["fixture"]["fixture_digest"], record["fixture"]["fixture_digest"])
                self.assertEqual(release["verified"]["evidence_counts"], record["verify"]["evidence_counts"])
                self.assertEqual(release["verified"]["block_hash"], record["verify"]["block_hash"])
                self.assertEqual(release["verified"]["receipts_root"], record["verify"]["receipts_root"])
                self.assertFalse(release["verified"]["canonical_chain_claim"])
                self.assertEqual(release["binding"]["checks"], list(CHECKS))
                self.assertEqual(release_digest(release), release["release_digest"])
                self.assertEqual(archive["fixture_digest"], release["fixture"]["fixture_digest"])
                self.assertEqual(archive["release_digest"], release["release_digest"])
                self.assertEqual(archive["statement_sha256"], release["statement"]["sha256"])

    def test_capture_record_manifest_recomputes_to_its_fixture_digest(self):
        for generation in GENERATIONS:
            record = self.records[generation]
            with self.subTest(generation=generation):
                self.assertEqual(fixture_digest(record["verify"]["manifest"]), record["fixture"]["fixture_digest"])


class AlexandriaPlanTests(unittest.TestCase):
    """Each plan admits the recorded fixture, scoped to every proof target and nothing else."""

    @classmethod
    def setUpClass(cls):
        scripts = REPO_ROOT / "plugins" / "alexandria" / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from alexandria_lib.release import validate_plan  # pylint: disable=import-outside-toplevel

        cls.validate_plan = staticmethod(validate_plan)
        cls.plans = {g: read_example(f"alexandria-plan-{g}.json") for g in GENERATIONS}
        cls.records = {g: read_example(f"capture-{g}.json") for g in GENERATIONS}
        cls.regenerated = regenerated_plans()

    def test_plan_validates_and_binds_the_recorded_fixture(self):
        for generation in GENERATIONS:
            plan = self.plans[generation]
            record = self.records[generation]
            with self.subTest(generation=generation):
                self.validate_plan(plan)
                self.assertEqual(plan["format"], "alexandria-capture-plan/v1")
                self.assertEqual(len(plan["captures"]), 1)
                capture = plan["captures"][0]
                self.assertEqual(capture["evidence_class"], "proof-backed-state")
                self.assertEqual(capture["chain"], "eip155:1")
                self.assertEqual(capture["source"], {
                    "kind": "lazarus-fixture", "locator_class": "local-fixture",
                    "reference": record["fixture"]["fixture_digest"],
                })
                interval = capture["scope"]["interval"]
                self.assertEqual(interval["kind"], "snapshot")
                self.assertEqual(interval["block_hash"], record["verify"]["block_hash"])
                self.assertEqual(int(interval["block_number"]), int(record["verify"]["block_number"], 16))
                self.assertEqual(capture["scope"]["finality"], "unknown")
                self.assertEqual(capture["scope"]["kind"], "subject-scoped")
                self.assertEqual(capture["coverage"]["status"], "complete")
                self.assertEqual(capture["coverage"]["record_count"], len(record["fixture"]["components"]))
                paths = sorted(c["path"] for c in plan["components"])
                expected = sorted(
                    f"fixture/{c['path']}" for c in record["fixture"]["components"] + [record["fixture"]["manifest"]]
                )
                self.assertEqual(paths, expected)
                manifest = next(c for c in plan["components"] if c["path"] == "fixture/manifest.json")
                self.assertEqual(manifest["role"], "lazarus-manifest")
                self.assertEqual(capture["component"], manifest["name"])
                for component in plan["components"]:
                    self.assertEqual(component["access"], "restricted")
                    self.assertEqual(component["redistribution"], "restricted")

    def test_subjects_are_exactly_the_plans_proof_targets(self):
        for generation in GENERATIONS:
            plan = json.loads(self.regenerated[generation][0].read_text(encoding="utf-8"))
            targets = {f"eip155:1:{t['address'].lower()}" for t in plan["proof_targets"]}
            with self.subTest(generation=generation):
                subjects = self.plans[generation]["captures"][0]["scope"]["subjects"]
                self.assertEqual(len(subjects), len(set(subjects)))
                self.assertEqual(set(subjects), targets)


class ArchiveInventoryTests(unittest.TestCase):
    """The inventory's members are the committed digests, and the builder is deterministic."""

    @classmethod
    def setUpClass(cls):
        cls.inventory = read_example("archives.json")
        cls.records = {g: read_example(f"capture-{g}.json") for g in GENERATIONS}
        cls.archiver = importlib.util.module_from_spec(
            importlib.util.spec_from_file_location("wildcat_boundary_archive", ARCHIVER)
        )
        spec = importlib.util.spec_from_file_location("wildcat_boundary_archive", ARCHIVER)
        cls.archiver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.archiver)

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def test_inventory_members_are_the_committed_digests(self):
        inventory = self.inventory
        self.assertEqual(inventory["schema"], "wildcat-boundary-archives/v1")
        self.assertEqual(inventory["format"], self.archiver.FORMAT)
        self.assertIn("establishes", inventory)
        self.assertIn("does_not_establish", inventory)
        self.assertIn("canonical-chain", inventory["does_not_establish"])
        self.assertEqual(
            [(a["generation"], a["contents"]) for a in inventory["archives"]],
            [(g, k) for g in GENERATIONS for k in ("lazarus-release", "alexandria-release")],
        )
        for archive in inventory["archives"]:
            generation = archive["generation"]
            record = self.records[generation]
            components = {
                c["path"]: (c["bytes"], c["sha256"])
                for c in record["fixture"]["components"] + [record["fixture"]["manifest"]]
            }
            prefix = archive["name"].removesuffix(".tar")
            members = {m["path"]: (m["bytes"], m["sha256"]) for m in archive["members"]}
            with self.subTest(archive=archive["name"]):
                self.assertEqual(archive["name"], f"wildcat-boundary-{generation}-{archive['contents']}.tar")
                self.assertEqual(archive["member_count"], len(members))
                self.assertEqual(len(archive["members"]), len(members))
                self.assertRegex(archive["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(archive["bytes"], sum(m["bytes"] for m in archive["members"]))
                self.assertEqual(archive["bytes"] % 512, 0)
                self.assertEqual([m["path"] for m in archive["members"]],
                                 sorted((m["path"] for m in archive["members"]), key=lambda p: p.encode()))
                self.assertEqual(archive["fixture_digest"], record["fixture"]["fixture_digest"])
                if archive["contents"] == "lazarus-release":
                    release_bytes = (EXAMPLE / f"release-{generation}.json").read_bytes()
                    statement_bytes = (EXAMPLE / f"statement-{generation}.json").read_bytes()
                    expected = {f"{prefix}/fixture/{p}": v for p, v in components.items()}
                    expected[f"{prefix}/release.json"] = (len(release_bytes), hashlib.sha256(release_bytes).hexdigest())
                    expected[f"{prefix}/statement.json"] = (len(statement_bytes), hashlib.sha256(statement_bytes).hexdigest())
                    self.assertEqual(archive["release_digest"], json.loads(release_bytes)["release_digest"])
                    self.assertEqual(archive["statement_sha256"], expected[f"{prefix}/statement.json"][1])
                else:
                    expected = {f"{prefix}/objects/sha256/{d[:2]}/{d}": (b, d) for b, d in components.values()}
                    self.assertRegex(archive["release_id"], r"^sha256:[0-9a-f]{64}$")
                    self.assertEqual(archive["manifest_sha256"], members[f"{prefix}/manifest.json"][1])
                    expected[f"{prefix}/manifest.json"] = members[f"{prefix}/manifest.json"]
                self.assertEqual(members, expected)

    def synthetic_trees(self, base):
        """Two small release trees per estate whose identities are the committed ones."""
        base.mkdir()
        arguments = []
        for generation in GENERATIONS:
            record = self.records[generation]
            digest = record["fixture"]["fixture_digest"]
            lazarus = base / f"{generation}-lazarus"
            (lazarus / "fixture").mkdir(parents=True)
            (lazarus / "fixture" / "manifest.json").write_bytes(b'{"fixture_digest":"' + digest.encode() + b'"}\n')
            (lazarus / "fixture" / "proofs.jsonl").write_bytes(b'{"evidence":"proof-backed"}\n')
            statement = b'{"predicateType":"synthetic"}\n'
            (lazarus / "statement.json").write_bytes(statement)
            document = {"fixture": {"fixture_digest": digest}, "release_digest": "9" * 64,
                        "statement": {"sha256": hashlib.sha256(statement).hexdigest()}}
            (lazarus / "release.json").write_bytes(json.dumps(document).encode() + b"\n")
            alexandria = base / f"{generation}-alexandria"
            (alexandria / "objects" / "sha256" / "ab").mkdir(parents=True)
            (alexandria / "objects" / "sha256" / "ab" / ("ab" + "0" * 62)).write_bytes(b"object\n")
            manifest = {"captures": [{"evidence_class": "proof-backed-state", "source": {"reference": digest}}],
                        "release_id": "sha256:" + "8" * 64}
            (alexandria / "manifest.json").write_bytes(json.dumps(manifest).encode() + b"\n")
            arguments += [f"--{generation}-lazarus-release", str(lazarus),
                          f"--{generation}-alexandria-release", str(alexandria)]
        return arguments

    def test_builder_reproduces_the_same_bytes_and_a_reproducible_record(self):
        arguments = self.synthetic_trees(self.root / "trees")
        first = run_archiver(*arguments, "--out-dir", str(self.root / "one"), "--record", str(self.root / "one.json"))
        self.assertEqual(first.returncode, 0, first.stderr)
        second = run_archiver(*arguments, "--out-dir", str(self.root / "two"), "--record",
                              str(self.root / "two.json"), "--expect", str(self.root / "one.json"))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("rebuilt inventory equals the expected record for 4 archives", second.stdout)
        self.assertEqual((self.root / "one.json").read_bytes(), (self.root / "two.json").read_bytes())
        names = sorted(p.name for p in (self.root / "one").iterdir())
        self.assertEqual(names, sorted(
            f"wildcat-boundary-{g}-{k}.tar" for g in GENERATIONS for k in ("lazarus-release", "alexandria-release")
        ))
        import tarfile  # pylint: disable=import-outside-toplevel

        for name in names:
            self.assertEqual((self.root / "one" / name).read_bytes(), (self.root / "two" / name).read_bytes())
            with tarfile.open(self.root / "one" / name) as archive:
                members = archive.getmembers()
                self.assertTrue(members)
                self.assertEqual([m.name for m in members], sorted((m.name for m in members), key=lambda n: n.encode()))
                for member in members:
                    self.assertTrue(member.isreg())
                    self.assertEqual((member.mtime, member.uid, member.gid, member.uname, member.gname, member.mode),
                                     (0, 0, 0, "", "", 0o644))
                    self.assertTrue(member.name.startswith(name.removesuffix(".tar") + "/"))
        record = json.loads((self.root / "one.json").read_text(encoding="utf-8"))
        self.assertEqual(record["format"], self.archiver.FORMAT)
        lazarus_v1 = record["archives"][0]
        self.assertEqual(lazarus_v1["release_digest"], "9" * 64)
        self.assertEqual(sorted(m["path"] for m in lazarus_v1["members"]), [
            "wildcat-boundary-v1-lazarus-release/fixture/manifest.json",
            "wildcat-boundary-v1-lazarus-release/fixture/proofs.jsonl",
            "wildcat-boundary-v1-lazarus-release/release.json",
            "wildcat-boundary-v1-lazarus-release/statement.json",
        ])
        edited = record
        edited["archives"][0]["sha256"] = flip_hex(edited["archives"][0]["sha256"])
        (self.root / "edited.json").write_text(json.dumps(edited), encoding="utf-8")
        third = run_archiver(*arguments, "--out-dir", str(self.root / "three"), "--record",
                             str(self.root / "three.json"), "--expect", str(self.root / "edited.json"))
        self.assertEqual(third.returncode, 1)
        self.assertIn("differs from the expected record: wildcat-boundary-v1-lazarus-release.tar", third.stderr)

    def test_builder_refusals(self):
        arguments = self.synthetic_trees(self.root / "trees")
        existing = self.root / "existing"
        existing.mkdir()
        cases = {
            "output directory already exists": ["--out-dir", str(existing), "--record", str(self.root / "r.json")],
            "record path already exists": ["--out-dir", str(self.root / "fresh"), "--record", str(self.root / "existing")],
            "output directory sits inside an input tree": [
                "--out-dir", str(self.root / "trees" / "v1-lazarus" / "out"), "--record", str(self.root / "r.json"),
            ],
        }
        for message, extra in cases.items():
            with self.subTest(message=message):
                completed = run_archiver(*arguments, *extra)
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertIn(message, completed.stderr)
                self.assertFalse((self.root / "r.json").exists())
        link = self.root / "linked"
        link.symlink_to(self.root / "trees" / "v1-lazarus")
        linked = list(arguments)
        linked[1] = str(link)
        completed = run_archiver(*linked, "--out-dir", str(self.root / "fresh"), "--record", str(self.root / "r.json"))
        self.assertEqual(completed.returncode, 2)
        self.assertIn("v1 Lazarus release tree is a symlink", completed.stderr)
        inner = self.root / "trees" / "v2-alexandria" / "stray"
        inner.symlink_to(self.root / "trees" / "v2-alexandria" / "manifest.json")
        completed = run_archiver(*arguments, "--out-dir", str(self.root / "fresh"), "--record", str(self.root / "r.json"))
        self.assertEqual(completed.returncode, 2)
        self.assertIn("stray is not a regular file", completed.stderr)
        # A refusal found while walking a tree leaves no output directory behind.
        self.assertFalse((self.root / "fresh").exists())
        inner.unlink()
        document = self.root / "trees" / "v1-lazarus" / "release.json"
        altered = json.loads(document.read_text(encoding="utf-8"))
        altered["fixture"]["fixture_digest"] = flip_hex(altered["fixture"]["fixture_digest"])
        document.write_text(json.dumps(altered), encoding="utf-8")
        completed = run_archiver(*arguments, "--out-dir", str(self.root / "fresh"), "--record", str(self.root / "r.json"))
        self.assertEqual(completed.returncode, 2)
        self.assertIn("fixture digest the committed capture record does not", completed.stderr)
        self.assertFalse((self.root / "fresh").exists())


class DemoVerifyPreservedTests(unittest.TestCase):
    """verify-preserved passes on the committed example and refuses an edited digest."""

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def test_passes_offline_and_writes_a_report(self):
        report = self.root / "preserved.json"
        completed = run_demo("verify-preserved", "--report", str(report), cwd=self.root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("verify-preserved checks=12 result=pass", completed.stdout)
        for generation in GENERATIONS:
            for check in ("capture-record", "release-document", "statement", "alexandria-plan", "archive-inventory"):
                self.assertIn(f"generation={generation}", completed.stdout)
                self.assertIn(f"check={check} result=pass", completed.stdout)
        written = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(written["schema"], "wildcat-boundary-demo-report/v1")
        self.assertEqual((written["subcommand"], written["result"], written["exit"]), ("verify-preserved", "pass", 0))
        self.assertEqual(len(written["observations"]), 12)
        self.assertIn("recompute", written["establishes"])
        self.assertIn("reruns no proof check", written["does_not_establish"])
        for pattern in URL_OR_CREDENTIAL:
            self.assertIsNone(pattern.search(report.read_text(encoding="utf-8")), pattern.pattern)

    def edited_copy(self, name, edit):
        copy = copy_example(self.root / f"copy-{name}-{len(list(self.root.iterdir()))}")
        path = copy / name
        document = json.loads(path.read_text(encoding="utf-8"))
        edit(document)
        path.write_text(json.dumps(document, indent=1), encoding="utf-8")
        return copy

    def test_refuses_an_edited_digest_count_or_root(self):
        def edit_release_fixture(d):
            d["fixture"]["fixture_digest"] = flip_hex(d["fixture"]["fixture_digest"])

        def edit_release_identity(d):
            d["release_digest"] = flip_hex(d["release_digest"])

        def edit_capture_component(d):
            d["fixture"]["components"][0]["sha256"] = flip_hex(d["fixture"]["components"][0]["sha256"])
            d["verify"]["manifest"]["components"][0]["sha256"] = d["fixture"]["components"][0]["sha256"]

        def edit_capture_count(d):
            d["verify"]["evidence_counts"]["proof_backed"] += 1
            d["verify"]["manifest"]["evidence_counts"]["proof_backed"] += 1

        def edit_statement_count(d):
            d["predicate"]["evidence"]["recorded_rpc"] -= 1

        def edit_archive_member(d):
            d["archives"][0]["members"][0]["sha256"] = flip_hex(d["archives"][0]["members"][0]["sha256"])

        def edit_plan_reference(d):
            d["captures"][0]["source"]["reference"] = flip_hex(d["captures"][0]["source"]["reference"])

        def edit_boolean_count(d):
            d["verify"]["evidence_counts"]["header_bound"] = True
            d["verify"]["manifest"]["evidence_counts"]["header_bound"] = True

        cases = [
            ("release-v1.json", edit_release_fixture, "release-v1.json: fixture.fixture_digest differs"),
            ("release-v2.json", edit_release_identity, "release-v2.json: release_digest does not recompute"),
            ("capture-v2.json", edit_capture_component, "capture-v2.json: the recorded manifest does not recompute"),
            ("capture-v1.json", edit_capture_count, "capture-v1.json: the recorded manifest does not recompute"),
            ("statement-v1.json", edit_statement_count, "statement-v1.json: its SHA-256 is not the one"),
            ("archives.json", edit_archive_member, "archives.json: wildcat-boundary-v1-lazarus-release.tar members differ"),
            ("alexandria-plan-v2.json", edit_plan_reference, "alexandria-plan-v2.json: source does not name"),
            ("capture-v1.json", edit_boolean_count, "must be a non-negative whole number"),
        ]
        for name, edit, message in cases:
            with self.subTest(name=name, message=message):
                copy = self.edited_copy(name, edit)
                report = self.root / f"report-{copy.name}.json"
                completed = run_demo("verify-preserved", "--example", str(copy), "--report", str(report), cwd=self.root)
                self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
                self.assertIn(message, completed.stderr)
                self.assertNotIn("verify-preserved checks=12 result=pass", completed.stdout)
                written = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual((written["result"], written["exit"]), ("fail", 1))
                self.assertIn("a check failed", written["establishes"])
        pristine = copy_example(self.root / "pristine")
        completed = run_demo("verify-preserved", "--example", str(pristine), cwd=self.root)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_refuses_a_non_finite_number_in_a_record(self):
        copy = copy_example(self.root / "nan")
        path = copy / "capture-v1.json"
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count('"elapsed_seconds": 26.322'), 1)
        path.write_text(text.replace('"elapsed_seconds": 26.322', '"elapsed_seconds": NaN'), encoding="utf-8")
        completed = run_demo("verify-preserved", "--example", str(copy), cwd=self.root)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("capture-v1.json is not finite JSON", completed.stderr)


class DemoRefusalTests(unittest.TestCase):
    """The demo refuses a missing variable, an existing output and a symlinked input before it reads anything."""

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.trees = {}
        for generation in GENERATIONS:
            tree = self.root / f"{generation}-tree"
            shutil.copytree(AAVE_RELEASE, tree)
            self.trees[generation] = tree
        self.environment = release_variables(self.trees["v1"], self.trees["v2"])

    def test_refuses_a_missing_or_empty_variable(self):
        for subcommand in ("mutations", "verify-releases"):
            for generation, variable in RELEASE_VARIABLES.items():
                for value in (None, ""):
                    environment = {k: v for k, v in self.environment.items() if k != variable}
                    if value is not None:
                        environment[variable] = value
                    with self.subTest(subcommand=subcommand, variable=variable, value=value):
                        completed = run_demo(subcommand, environment=environment)
                        self.assertEqual(completed.returncode, 2, completed.stderr)
                        self.assertIn(f"refusing: environment variable {variable} is unset", completed.stderr)
                        self.assertEqual(completed.stdout, "")

    def test_refuses_a_symlinked_tree_or_entry(self):
        link = self.root / "linked-tree"
        link.symlink_to(self.trees["v1"])
        environment = release_variables(link, self.trees["v2"])
        for subcommand in ("mutations", "verify-releases"):
            with self.subTest(subcommand=subcommand, what="tree"):
                completed = run_demo(subcommand, environment=environment)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("WILDCAT_BOUNDARY_V1_RELEASE release tree is a symlink", completed.stderr)
        linked_entry = self.root / "linked-entry"
        linked_entry.mkdir()
        shutil.copy(self.trees["v2"] / "release.json", linked_entry / "release.json")
        shutil.copy(self.trees["v2"] / "statement.json", linked_entry / "statement.json")
        (linked_entry / "fixture").symlink_to(self.trees["v2"] / "fixture")
        environment = release_variables(self.trees["v1"], linked_entry)
        completed = run_demo("verify-releases", environment=environment)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("WILDCAT_BOUNDARY_V2_RELEASE release tree entry fixture is a symlink", completed.stderr)
        example_link = self.root / "example-link"
        example_link.symlink_to(EXAMPLE)
        completed = run_demo("verify-preserved", "--example", str(example_link))
        self.assertEqual(completed.returncode, 2)
        self.assertIn("refusing: example directory is a symlink", completed.stderr)

    def test_refuses_an_existing_or_symlinked_report_and_one_inside_a_release_tree(self):
        before = {g: tree_digests(t) for g, t in self.trees.items()}
        existing = self.root / "report.json"
        existing.write_bytes(b"keep me\n")
        dangling = self.root / "dangling.json"
        dangling.symlink_to(self.root / "absent.json")
        inside = self.trees["v1"] / "report.json"
        cases = [
            (existing, "report path already exists"),
            (dangling, "report path is a symlink"),
            (inside, "report path sits inside a release tree"),
        ]
        for subcommand in ("mutations", "verify-releases", "verify-preserved"):
            for path, message in cases:
                if subcommand == "verify-preserved" and path == inside:
                    continue
                with self.subTest(subcommand=subcommand, message=message):
                    completed = run_demo(subcommand, "--report", str(path), environment=self.environment)
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertIn(f"refusing: {message}", completed.stderr)
        self.assertEqual(existing.read_bytes(), b"keep me\n")
        self.assertFalse((self.root / "absent.json").exists())
        self.assertEqual({g: tree_digests(t) for g, t in self.trees.items()}, before)

    def test_verify_releases_holds_a_tree_to_the_committed_documents(self):
        before = {g: tree_digests(t) for g, t in self.trees.items()}
        report = self.root / "releases.json"
        completed = run_demo("verify-releases", "--report", str(report), environment=self.environment)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("release tree's release.json differs from the committed release-v1.json", completed.stderr)
        written = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual((written["result"], written["exit"], written["observations"]), ("fail", 1, []))
        self.assertEqual({g: tree_digests(t) for g, t in self.trees.items()}, before)


class MutationRoutineTests(unittest.TestCase):
    """The three refusal classes hold offline against the committed Aave v4 release fixture, read only."""

    @classmethod
    def setUpClass(cls):
        cls.demo = load_demo()
        cls.before = tree_digests(AAVE_RELEASE)
        cls.manifest = json.loads((AAVE_FIXTURE / "manifest.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        if tree_digests(AAVE_RELEASE) != cls.before:
            raise AssertionError("the Aave v4 release example changed during the mutation tests")

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def test_six_copies_are_refused_by_the_named_checks_and_the_unchanged_copy_verifies(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            observed = self.demo.mutation_observations(AAVE_FIXTURE, "aave-v4-spoke-v1", self.manifest["fixture_digest"])
        self.assertEqual(observed["unchanged"], {"exit": 0, "fixture_digest": self.manifest["fixture_digest"]})
        changes = observed["changes"]
        self.assertEqual(len(changes), 6)
        expected_checks = {
            ("storage-value", "untouched"): "component-digest-mismatch",
            ("code-byte", "untouched"): "component-digest-mismatch",
            ("receipt-byte", "untouched"): "component-digest-mismatch",
            ("storage-value", "resealed"): "storage-value-mismatch",
            ("code-byte", "resealed"): "code-hash-mismatch",
            ("receipt-byte", "resealed"): "receipts-root-mismatch",
        }
        self.assertEqual({(c["change"], c["manifest"]): c["check"] for c in changes}, expected_checks)
        for change in changes:
            with self.subTest(change=change["change"], manifest=change["manifest"]):
                self.assertTrue(change["refused"])
                self.assertEqual(change["exit"], 1)
                self.assertNotEqual(change["changed"]["before"], change["changed"]["after"])
                self.assertIn(change["changed"]["component"], ("proofs.jsonl", "receipt-witness.json"))
                self.assertIn(f"check={change['check']}", stdout.getvalue())
        self.assertEqual(tree_digests(AAVE_RELEASE), self.before)

    def test_each_change_alters_one_field_and_the_reseal_only_the_manifest(self):
        for mutation, component in (
            ("storage-value", "proofs.jsonl"), ("code-byte", "proofs.jsonl"), ("receipt-byte", "receipt-witness.json"),
        ):
            copy = self.root / mutation
            shutil.copytree(AAVE_FIXTURE, copy)
            original = tree_digests(copy)
            detail = self.demo.CHANGES[mutation](copy)
            changed = tree_digests(copy)
            with self.subTest(mutation=mutation):
                self.assertEqual(detail["component"], component)
                self.assertEqual({p for p in original if original[p] != changed[p]}, {component})
                if component == "proofs.jsonl":
                    old_lines = (AAVE_FIXTURE / component).read_bytes().split(b"\n")
                    new_lines = (copy / component).read_bytes().split(b"\n")
                    differing = [i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b]
                    self.assertEqual(len(differing), 1)
                    old = json.loads(old_lines[differing[0]])
                    new = json.loads(new_lines[differing[0]])
                    if mutation == "storage-value":
                        self.assertEqual(new["storage_proof"][0]["value"], detail["after"])
                        new["storage_proof"][0]["value"] = old["storage_proof"][0]["value"]
                    else:
                        old_code, new_code = bytes.fromhex(old["code"][2:]), bytes.fromhex(new["code"][2:])
                        self.assertEqual(len(old_code), len(new_code))
                        self.assertEqual(sum(a != b for a, b in zip(old_code, new_code)), 1)
                        self.assertEqual(detail["byte_index"], len(old_code) - 1)
                        new["code"] = old["code"]
                    self.assertEqual(new, old)
                else:
                    old = json.loads((AAVE_FIXTURE / component).read_text(encoding="utf-8"))
                    new = json.loads((copy / component).read_text(encoding="utf-8"))
                    index = detail["transaction_index"]
                    self.assertEqual(index, int(old["target_receipt"]["transaction_index"], 16))
                    self.assertEqual(new["receipts"][index]["cumulative_gas_used"], detail["after"])
                    self.assertEqual(int(detail["after"], 16) ^ int(detail["before"], 16), 1)
                    new["receipts"][index]["cumulative_gas_used"] = old["receipts"][index]["cumulative_gas_used"]
                    self.assertEqual(new, old)
                before_reseal = tree_digests(copy)
                self.demo.reseal_manifest(copy, component)
                after_reseal = tree_digests(copy)
                self.assertEqual({p for p in before_reseal if before_reseal[p] != after_reseal[p]}, {"manifest.json"})
                manifest = json.loads((copy / "manifest.json").read_text(encoding="utf-8"))
                entry = next(c for c in manifest["components"] if c["path"] == component)
                self.assertEqual(entry["sha256"], after_reseal[component])
                self.assertEqual(manifest["fixture_digest"], fixture_digest(manifest))

    def test_routine_stops_when_a_copy_is_accepted_or_refused_by_another_check(self):
        for outcome, message in (((0, ""), "verify accepted the storage-value copy"),
                                 ((1, "lazarus: something else"), "refused by an unexpected check")):
            with self.subTest(outcome=outcome):
                answers = iter([(0, "")] + [outcome] * 6)
                with mock.patch.object(self.demo, "verify_fixture", side_effect=lambda path: next(answers)), \
                        contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(self.demo.CheckFailure) as caught:
                        self.demo.mutation_observations(AAVE_FIXTURE, "probe", None)
                self.assertIn(message, str(caught.exception))
        with mock.patch.object(self.demo, "verify_fixture", return_value=(1, "lazarus: broken")), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(self.demo.CheckFailure) as caught:
                self.demo.mutation_observations(AAVE_FIXTURE, "probe", None)
        self.assertIn("unchanged fixture does not verify", str(caught.exception))
        with mock.patch.object(self.demo, "verify_fixture", return_value=(0, "")), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(self.demo.CheckFailure) as caught:
                self.demo.mutation_observations(AAVE_FIXTURE, "probe", "0" * 64)
        self.assertIn("is not the recorded one", str(caught.exception))


RELEASE_TREES_UNSET = "the coordinator records mutations and verify-releases over the real release trees; " + " and ".join(
    v for v in RELEASE_VARIABLES.values() if not os.environ.get(v)
) + " unset here"


@unittest.skipUnless(all(os.environ.get(v) for v in RELEASE_VARIABLES.values()), RELEASE_TREES_UNSET)
class ReleaseTreeTests(unittest.TestCase):
    """The two conformance cells, run only when both release trees are named."""

    def test_mutations_refuse_all_six_changes_on_both_estates(self):
        completed = run_demo("mutations")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("mutations changes=6 refusals=12 unchanged_verified=2 result=pass", completed.stdout)

    def test_verify_releases_passes_on_both_trees(self):
        completed = run_demo("verify-releases")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("verify-releases trees=2 result=pass", completed.stdout)


class ReadmeIdentityTests(unittest.TestCase):
    """Every release, admission and archive figure the README states is a committed record's."""

    @classmethod
    def setUpClass(cls):
        cls.readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        cls.releases = {g: read_example(f"release-{g}.json") for g in GENERATIONS}
        cls.statements = {g: read_example(f"statement-{g}.json") for g in GENERATIONS}
        cls.archives = read_example("archives.json")["archives"]

    def table_row(self, label):
        line = next(l for l in self.readme.splitlines() if l.startswith(f"| {label} |"))
        return [cell.strip() for cell in line.strip().strip("|").split("|")][1:]

    def test_identity_table_repeats_the_committed_records(self):
        expected = {}
        for generation in GENERATIONS:
            release = self.releases[generation]
            counts = self.statements[generation]["predicate"]["evidence"]
            by_kind = {a["contents"]: a for a in self.archives if a["generation"] == generation}
            expected[generation] = {
                "Release digest": f"`{release['release_digest']}`",
                "Statement SHA-256": f"`{release['statement']['sha256']}`",
                "Statement evidence counts": ", ".join(f"{counts[k]:,}" for k in EVIDENCE_KEYS),
                "Alexandria release id": f"`{by_kind['alexandria-release']['release_id']}`",
                "Lazarus release archive, bytes and SHA-256":
                    f"{by_kind['lazarus-release']['bytes']:,}, `{by_kind['lazarus-release']['sha256']}`",
                "Alexandria release archive, bytes and SHA-256":
                    f"{by_kind['alexandria-release']['bytes']:,}, `{by_kind['alexandria-release']['sha256']}`",
            }
        for label in expected["v1"]:
            with self.subTest(label=label):
                self.assertEqual(self.table_row(label), [expected[g][label] for g in GENERATIONS])


if __name__ == "__main__":
    unittest.main()
