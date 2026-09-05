"""Probitas statement projection and CLI integration."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest import mock
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
COMMAND = PLUGIN_ROOT / "scripts" / "probitas.py"
ARIADNE = REPO_ROOT / "plugins" / "ariadne" / "scripts" / "ariadne.py"
ARIADNE_SAFEJSON = (
    REPO_ROOT / "plugins" / "ariadne" / "scripts" / "ariadne_lib" / "safejson.py"
)
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from probitas_lib import gates  # noqa: E402
from probitas_lib import render  # noqa: E402
from probitas_lib import statement as statement_module  # noqa: E402


def run_command(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


class StatementModuleTests(unittest.TestCase):
    def setUp(self):
        self.dossier = b"# Dossier\n"
        self.evidence = b'{"schema":2}\n'
        names = ("provenance", "coverage", "sourcing", "negative space", "rating")
        self.results = [
            gates.Gate(number, name, True, "ok")
            for number, name in enumerate(names, start=1)
        ]

    def test_statement_binds_both_inputs_and_five_passed_gates(self):
        found = statement_module.statement_for(
            self.dossier, self.evidence, self.results
        )
        dossier_digest = {"sha256": hashlib.sha256(self.dossier).hexdigest()}
        evidence_digest = {"sha256": hashlib.sha256(self.evidence).hexdigest()}

        self.assertEqual(found["_type"], statement_module.STATEMENT_TYPE)
        self.assertEqual(found["predicateType"], statement_module.PREDICATE_TYPE)
        self.assertEqual(
            found["subject"],
            [
                {"name": "dossier", "digest": dossier_digest},
                {"name": "evidence", "digest": evidence_digest},
            ],
        )
        predicate = found["predicate"]
        self.assertEqual(
            predicate["dossier"],
            {"digest": dossier_digest, "bytes": len(self.dossier)},
        )
        self.assertEqual(
            predicate["evidence"],
            {"digest": evidence_digest, "bytes": len(self.evidence), "schema": 2},
        )
        self.assertEqual(predicate["tool"]["name"], "probitas")
        self.assertEqual(len(predicate["claims"]), 5)
        self.assertEqual(
            [claim["name"] for claim in predicate["claims"]],
            [f"probitas gate {result.number} {result.name}" for result in self.results],
        )
        self.assertTrue(
            all(claim["subject"] == dossier_digest for claim in predicate["claims"])
        )
        self.assertTrue(
            all(claim["disposition"] == "passed" for claim in predicate["claims"])
        )
        self.assertEqual(predicate["commands"], [])

    def test_statement_refuses_any_failed_gate(self):
        self.results[2].passed = False
        with self.assertRaisesRegex(ValueError, "all five gates"):
            statement_module.statement_for(
                self.dossier, self.evidence, self.results
            )

    def test_emission_is_canonical_atomic_and_bounded(self):
        with tempfile.TemporaryDirectory(prefix="probitas-statement-") as directory:
            output = Path(directory) / "statement.json"
            statement_module.emit_statement(
                self.dossier, self.evidence, self.results, output
            )
            first = output.read_bytes()
            self.assertTrue(first.endswith(b"\n"))
            self.assertEqual(
                first,
                statement_module.canonical_bytes(json.loads(first)),
            )
            output.write_bytes(b"stale\n")
            statement_module.emit_statement(
                self.dossier, self.evidence, self.results, output
            )
            self.assertEqual(output.read_bytes(), first)

            with mock.patch.object(statement_module, "MAX_STATEMENT_BYTES", 1):
                with self.assertRaisesRegex(ValueError, "input limit"):
                    statement_module.emit_statement(
                        self.dossier, self.evidence, self.results, output
                    )
            self.assertEqual(output.read_bytes(), first)

    def test_statement_limit_tracks_ariadne_bounded_reader(self):
        ariadne_limit = runpy.run_path(str(ARIADNE_SAFEJSON))["DEFAULT_MAX_BYTES"]
        self.assertEqual(statement_module.MAX_STATEMENT_BYTES, ariadne_limit)

    def test_tool_version_comes_from_canonical_skill_metadata(self):
        statement = statement_module.statement_for(
            self.dossier, self.evidence, self.results
        )
        skill = (PLUGIN_ROOT / "skills" / "probitas" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        declared = next(
            line.split('"')[1]
            for line in skill.splitlines()
            if line.startswith("  version: ")
        )
        self.assertEqual(statement["predicate"]["tool"]["version"], declared)


class RenderSplitEquivalenceTests(unittest.TestCase):
    def outcome(self, function, *args):
        try:
            return ("returned", function(*args))
        except Exception as error:  # Exact public error equivalence is the assertion.
            return ("raised", type(error), str(error))

    def assert_equivalent(self, path):
        self.assertEqual(
            self.outcome(render.load, path),
            self.outcome(render.load_bytes, path.read_bytes(), path),
        )

    def test_every_checked_in_fixture_json_has_equivalent_load_paths(self):
        fixture_files = sorted(FIXTURES.rglob("*.json"))
        self.assertTrue(fixture_files)
        for path in fixture_files:
            with self.subTest(path=path.relative_to(FIXTURES)):
                self.assert_equivalent(path)

    def test_valid_fixture_derived_evidence_has_equivalent_load_paths(self):
        from .test_gates import evidence

        cases = sorted(path.name for path in FIXTURES.iterdir() if (path / "wildcat.json").is_file())
        with tempfile.TemporaryDirectory(prefix="probitas-load-equivalence-") as directory:
            root = Path(directory)
            for case in cases:
                with self.subTest(case=case):
                    path = root / f"{case}.json"
                    path.write_text(json.dumps(evidence(case)), encoding="utf-8")
                    self.assert_equivalent(path)

    def test_malformed_evidence_has_identical_exception_types_and_messages(self):
        valid = {
            "schema": 2,
            "subject": {"addresses": []},
            "records": [],
            "coverage": [],
            "gaps": [],
        }
        malformed = {
            "schema-1": json.dumps({**valid, "schema": 1}).encode(),
            "wrong-schema": json.dumps({**valid, "schema": 99}).encode(),
            "non-dict": b"[]",
            "missing-required-key": json.dumps(
                {key: value for key, value in valid.items() if key != "gaps"}
            ).encode(),
            "invalid-json": b'{"schema":2,',
            "invalid-utf8": b"\xff",
        }
        with tempfile.TemporaryDirectory(prefix="probitas-load-malformed-") as directory:
            root = Path(directory)
            for name, data in malformed.items():
                with self.subTest(name=name):
                    path = root / f"{name}.json"
                    path.write_bytes(data)
                    direct = self.outcome(render.load, path)
                    from_bytes = self.outcome(render.load_bytes, data, path)
                    self.assertEqual(direct, from_bytes)
                    self.assertEqual(direct[0], "raised")


class StatementCliTests(unittest.TestCase):
    def setUp(self):
        from .test_gates import evidence

        self.temporary = tempfile.TemporaryDirectory(prefix="probitas-statement-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        payload = evidence("clean")
        self.evidence = self.root / "evidence.json"
        self.dossier = self.root / "dossier.md"
        self.statement = self.root / "statement.json"
        self.evidence.write_text(
            json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.dossier.write_text(render.render(payload), encoding="utf-8")

    def verify(self, *extra):
        return run_command("verify", self.dossier, self.evidence, *extra)

    def test_positive_case_emits_bound_statement(self):
        result = self.verify("--statement-out", self.statement)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.strip().splitlines()), 5)
        self.assertIn(f"wrote statement {self.statement}", result.stderr)
        found = json.loads(self.statement.read_text(encoding="utf-8"))
        self.assertEqual(found["predicateType"], statement_module.PREDICATE_TYPE)

    def test_recovery_case_failed_verify_preserves_existing_statement(self):
        self.statement.write_bytes(b"keep\n")
        document = self.dossier.read_text(encoding="utf-8")
        self.dossier.write_text(
            document.replace("## What could not be established", "## Notes"),
            encoding="utf-8",
        )
        result = self.verify("--statement-out", self.statement)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.statement.read_bytes(), b"keep\n")
        self.assertIn("no statement was written", result.stderr)

    def test_statement_path_must_not_resolve_to_an_input_or_stdout(self):
        evidence_alias = self.root / "evidence-alias.json"
        evidence_alias.symlink_to(self.evidence)
        for output in (self.dossier, self.evidence, evidence_alias, "-"):
            with self.subTest(output=output):
                result = self.verify("--statement-out", output)
                self.assertEqual(result.returncode, 2)
                self.assertIn("statement output", result.stderr)

    def test_no_flag_keeps_the_existing_five_line_interface(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.strip().splitlines()), 5)
        self.assertEqual(result.stderr, "")
        self.assertFalse(self.statement.exists())

    def test_missing_evidence_case_refuses_without_output(self):
        self.evidence.unlink()
        result = self.verify("--statement-out", self.statement)
        self.assertEqual(result.returncode, 2)
        self.assertIn("probitas:", result.stderr)
        self.assertFalse(self.statement.exists())

    def test_overclaim_case_keeps_ariadne_partial_boundary_visible(self):
        emitted = self.verify("--statement-out", self.statement)
        self.assertEqual(emitted.returncode, 0, emitted.stderr)

        inspect = subprocess.run(
            [sys.executable, str(ARIADNE), "inspect", str(self.statement)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(inspect.returncode, 0, inspect.stderr)
        self.assertIn(statement_module.PREDICATE_TYPE, inspect.stdout)
        self.assertIn("not registered here", inspect.stdout)
        self.assertIn("unsigned", inspect.stdout)

        verify = subprocess.run(
            [sys.executable, str(ARIADNE), "verify", str(self.statement)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(verify.returncode, 0, verify.stderr)
        self.assertEqual(verify.stdout.count(": pass --"), 5)
        self.assertIn("gates 2 and 5", verify.stdout)
        self.assertIn("not registered here", verify.stdout)
        self.assertIn("unsigned", verify.stdout)

    def test_stale_case_changes_only_the_mutated_input_digest(self):
        first = self.verify("--statement-out", self.statement)
        self.assertEqual(first.returncode, 0, first.stderr)
        original = json.loads(self.statement.read_text(encoding="utf-8"))

        self.evidence.write_bytes(self.evidence.read_bytes() + b"\n")
        second_path = self.root / "second-statement.json"
        second = self.verify("--statement-out", second_path)
        self.assertEqual(second.returncode, 0, second.stderr)
        changed = json.loads(second_path.read_text(encoding="utf-8"))

        self.assertEqual(original["subject"][0], changed["subject"][0])
        self.assertNotEqual(original["subject"][1], changed["subject"][1])

    def test_verify_reads_each_input_once_and_hashes_those_bytes(self):
        import probitas

        arguments = probitas.build_parser().parse_args(
            [
                "verify",
                str(self.dossier),
                str(self.evidence),
                "--statement-out",
                str(self.statement),
            ]
        )
        targets = {str(self.dossier): 0, str(self.evidence): 0}
        real_open = open

        def tracking_open(path, *args, **kwargs):
            name = str(path)
            if name in targets:
                targets[name] += 1
            return real_open(path, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=tracking_open), contextlib.redirect_stdout(
            io.StringIO()
        ), contextlib.redirect_stderr(io.StringIO()):
            code = arguments.func(arguments)

        self.assertEqual(code, 0)
        self.assertEqual(targets, {str(self.dossier): 1, str(self.evidence): 1})
        found = json.loads(self.statement.read_text(encoding="utf-8"))
        self.assertEqual(
            found["subject"],
            [
                {
                    "name": "dossier",
                    "digest": {"sha256": hashlib.sha256(self.dossier.read_bytes()).hexdigest()},
                },
                {
                    "name": "evidence",
                    "digest": {"sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest()},
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
