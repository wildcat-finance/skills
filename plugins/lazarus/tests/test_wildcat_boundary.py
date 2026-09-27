"""Offline checks for the Wildcat boundary example.

Both plans regenerate from the committed generator, probe summaries and value
map to the digests and counts `plans.json` records, Lazarus plan validation
accepts them, the generator's refusals hold, the copies under
`docs/lazarus-wildcat-boundary-fixtures/` match the receipted digests, and no
committed file in the example carries a URL or credential pattern. Nothing
here reaches a network: the probe's reads are study-time evidence that no
test repeats.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from .support import PLUGIN_ROOT, REPO_ROOT
from lazarus_lib.canonical import load
from lazarus_lib.schemas import validate_document

EXAMPLE = PLUGIN_ROOT / "examples" / "wildcat-boundary-v0"
GENERATOR = EXAMPLE / "plan_v3.py"
DOCS = REPO_ROOT / "docs" / "lazarus-wildcat-boundary-fixtures"
KICKOFF = REPO_ROOT / "docs" / "kickoff" / "1384"
GENERATIONS = ("v1", "v2")
COMMITTED_EXAMPLE_FILES = {
    "README.md", "plan_v3.py", "plans.json", "probe-v1.json", "probe-v2.json",
    "probe.py", "wildcat_slots.py",
}
# The Step 1 artefacts by SHA-256, as the run's controller receipted them.
RECEIPTED = {
    "study.md": "cbaed6098ba614b9ee4297fd78e903a8248824145425a2e263115f760e114fa2",
    "runbook.md": "9e867d56efd26db5d027753df8b48d47f0b59d100a8bc21a51d01c5f59154ab1",
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


class RegeneratedPlanTests(unittest.TestCase):
    """The V2 plan is about 7 MB, so both plans are generated once per class."""

    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.scratch.cleanup)
        cls.record = json.loads((EXAMPLE / "plans.json").read_text(encoding="utf-8"))
        cls.plans = {}
        for generation in GENERATIONS:
            out = Path(cls.scratch.name) / f"{generation}.json"
            probe = EXAMPLE / cls.record["plans"][generation]["probe"]
            completed = run_generator(generation, probe, out)
            if completed.returncode != 0:
                raise AssertionError(f"{generation}: {completed.stderr.strip()}")
            cls.plans[generation] = (out, json.loads(completed.stdout))

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
            for pattern in URL_OR_CREDENTIAL:
                with self.subTest(name=name, pattern=pattern.pattern):
                    self.assertIsNone(pattern.search(text))

    def test_generator_imports_no_network_module(self):
        for name in ("plan_v3.py", "wildcat_slots.py"):
            text = (EXAMPLE / name).read_text(encoding="utf-8")
            for module in ("urllib", "socket", "http", "requests", "ssl"):
                with self.subTest(name=name, module=module):
                    self.assertNotRegex(text, rf"(?m)^\s*(?:import|from)\s+{module}\b")
        self.assertIn('KICKOFF = Path("docs/kickoff/1384")', GENERATOR.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
