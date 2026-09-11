"""Recovery and final-green guards for issue 453 Step 4."""

from __future__ import annotations

import hashlib
import io
import json
from contextlib import redirect_stderr
from pathlib import Path
import textwrap
import unittest

try:
    from .test_hexctl import HexctlCase, hexctl_module
except ImportError:
    from test_hexctl import HexctlCase, hexctl_module


FIXTURE_ROOT = Path(__file__).parent / "fixtures/issue-453"
AUDIT_LOOP_REFERENCE = (
    Path(__file__).parent.parent / "skills/fiat/references/audit-loop.md"
)
FIAT_SKILL = Path(__file__).parent.parent / "skills/fiat/SKILL.md"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def canonical_report(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")


class RecoveryTests(unittest.TestCase):
    """kf-453-06: resume parity and the bound explicit-emptiness claim."""

    def test_kf_453_06_resume_preserves_remaining_and_no_findings(self):
        fixture = load_fixture("recovery.json")
        controller = hexctl_module()
        validate = getattr(controller, "validate_known_failure_recovery", None)
        self.assertTrue(
            callable(validate),
            "Fiat cannot reconstruct its known-failure recovery projection",
        )

        self.assertEqual(
            fixture["projection_schema"],
            getattr(controller, "RECOVERY_PROJECTION_SCHEMA", None),
        )
        self.assertEqual(
            set(fixture["suite_checks"]),
            set(getattr(controller, "FINAL_GREEN_SUITE_CHECKS", ())),
        )

        for row in fixture["accepted"]:
            with self.subTest(accepted=row["id"]):
                document = row["document"]
                checked = validate(document, capture=fixture["capture"])
                self.assertEqual(document, checked)
                self.assertEqual(fixture["projection_fields"], sorted(checked))
                self.assertEqual(
                    fixture["final_green_fields"],
                    sorted(checked["final_green"]),
                )
                self.assertEqual(
                    sorted(
                        set(checked["assigned_ids"]) - set(checked["completed_ids"])
                    ),
                    checked["remaining_ids"],
                )
                claim = checked["no_known_findings"]
                if checked["assigned_ids"]:
                    self.assertIsNone(claim)
                else:
                    self.assertEqual(
                        fixture["no_known_findings_fields"], sorted(claim)
                    )
                    self.assertEqual(
                        fixture["capture"]["inventory_sha256"],
                        claim["inventory_sha256"],
                    )

        for row in fixture["rejected"]:
            with self.subTest(rejected=row["id"]):
                with self.assertRaisesRegex(ValueError, row["error"]):
                    validate(
                        row["document"],
                        capture=row.get("capture") or fixture["capture"],
                    )


class FinalGreenTests(unittest.TestCase):
    """kf-453-07: a red guard commit becomes fixed-tree green or nothing."""

    def test_kf_453_07_red_guard_cannot_finish_without_fixed_tree_green(self):
        fixture = load_fixture("final-green.json")
        controller = hexctl_module()
        admit = getattr(controller, "final_green_admission_counters", None)
        build = getattr(controller, "build_final_green_manifest", None)
        self.assertTrue(
            callable(admit) and callable(build),
            "Fiat admits no fixed-tree final-green evidence for a red guard",
        )

        green = fixture["green"]
        raw_report = canonical_report(green["report"])
        counters = admit(
            fixture["report_format"], raw_report, green["runner_exit"]
        )
        self.assertEqual(green["counters"], counters)
        self.assertEqual(fixture["counter_fields"], sorted(counters))

        for row in fixture["rejected"]:
            with self.subTest(rejected=row["id"]):
                with self.assertRaises(ValueError):
                    admit(
                        fixture["report_format"],
                        canonical_report(row["report"]),
                        row["runner_exit"],
                    )

        inputs = fixture["manifest"]
        retained_report = {
            "path": inputs["retained_report_path"],
            "bytes": len(raw_report),
            "sha256": hashlib.sha256(raw_report).hexdigest(),
        }
        manifest = build(
            finding_id=inputs["finding_id"],
            consuming_step=inputs["consuming_step"],
            controller_run_id=inputs["controller_run_id"],
            worktree_identity=inputs["worktree_identity"],
            capture=inputs["capture"],
            final_commit=inputs["final_commit"],
            green_command=inputs["green_command"],
            green_argv=inputs["green_argv"],
            report_format=inputs["report_format"],
            report_file=inputs["report_file"],
            retained_report=retained_report,
            runner_exit=green["runner_exit"],
            counters=counters,
        )
        self.assertEqual(fixture["manifest_schema"], manifest["schema"])
        self.assertEqual(set(fixture["manifest_fields"]), set(manifest))
        self.assertEqual(fixture["admission"], manifest["admission"])
        self.assertEqual(retained_report, manifest["retained_report"])
        self.assertEqual(inputs["final_commit"], manifest["final_commit"])
        self.assertEqual(counters, manifest["counters"])


GREEN_EMITTER = textwrap.dedent(
    '''\
    """A disposable fixed-tree runner in the inventory's closed argv shape."""

    import json
    import os
    import sys

    RED_MARKER = "red-marker"


    def main(argv):
        path = argv[argv.index("--report") + 1]
        failures = 1 if os.path.exists(RED_MARKER) else 0
        payload = {
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": failures,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\\n")
        return 1 if failures else 0


    if __name__ == "__main__":
        raise SystemExit(main(sys.argv[1:]))
    '''
)

CHECK_MAP_CHECKS = ("root-suite", "hexaemeron-suite")


class RecoveryFixture(HexctlCase):
    """One capture-aware run parked where Step 4's readers act on it."""

    FINDING = "kf-453-90"

    def controller_tree(self):
        root = Path(self.target, ".hexaemeron")
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.name != "lock"
        }

    def write_check_map(self, *, root_exit=0, hexaemeron_exit=0, checks=None):
        exits = {"root-suite": root_exit, "hexaemeron-suite": hexaemeron_exit}
        document = {
            "schema": "wildcat.check-map.v1",
            "checks": {
                name: {
                    "argv": ["python3", "-c", f"raise SystemExit({exits[name]})"],
                    "cwd": ".",
                }
                for name in (CHECK_MAP_CHECKS if checks is None else checks)
            },
        }
        return self.write(
            "tests/check-map-v1.json", json.dumps(document, indent=2) + "\n"
        )

    def inventory(self, *, assigned):
        source_path = "audit/rounds/source.md"
        source = "fixture audit source\n"
        source_sha256 = hashlib.sha256(source.encode()).hexdigest()
        view_path = "audit/rounds/source.synopsis.md"
        view = (
            "Synopsis schema=fiat-audit-synopsis/v1 | "
            f"source={source_path} | source_sha256={source_sha256} | h2_count=0\n"
        )
        view_sha256 = hashlib.sha256(view.encode()).hexdigest()
        self.write(source_path, source)
        self.write(view_path, view)
        source_views = [
            {
                "id": "fixture-audit",
                "path": view_path,
                "source_sha256": source_sha256,
                "view_sha256": view_sha256,
            }
        ]
        findings = []
        no_known_findings = {
            "source_views": [
                {
                    "id": "fixture-audit",
                    "source_sha256": source_sha256,
                    "view_sha256": view_sha256,
                }
            ],
            "consuming_step": 1,
            "surveyor_assertion": "no-known-findings",
        }
        if assigned:
            findings = [
                {
                    "id": self.FINDING,
                    "source_ref": "fixture-audit:1",
                    "failure": "the fixed tree is never proved green",
                    "guard_paths": ["green_report.py"],
                    "test_command": (
                        "python3 green_report.py --case "
                        f"{self.FINDING} --report {{report}}"
                    ),
                    "report_format": "unittest-json-v1",
                    "report_file": f".elenchus/{self.FINDING}.json",
                    "expected_guard_verdict": "guarded",
                    "green_command": (
                        "python3 green_report.py --case "
                        f"{self.FINDING} --report "
                        f".elenchus/{self.FINDING}-green.json"
                    ),
                    "consuming_step": 1,
                }
            ]
            no_known_findings = None
        return {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": source_views,
            "findings": findings,
            "no_known_findings": no_known_findings,
        }, source_path

    def prepare_capture(self, *, assigned=False):
        self.init()
        inventory, source_path = self.inventory(assigned=assigned)
        self.write("green_report.py", GREEN_EMITTER)
        self.write_check_map()
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "fixed-tree-green | the step exit | require final green\n"
            "```\n\n```known-failure-inventory\n"
            + json.dumps(inventory, indent=2)
            + "\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        assignment = (
            f"\nKnown-failure assignment: `{self.FINDING}` -> Step 1\n"
            if assigned
            else ""
        )
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Recover and require final green\n\n"
            "**Goal.** Exercise the fixed-tree transition.\n\n"
            "**Exit.** The source-bound transition is checked.\n" + assignment,
        )
        steps = self.write("steps.json", '["Recover and require final green"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        return source_path

    def rewrite_last_controller_state(self, state):
        controller = hexctl_module()
        root = Path(self.target, ".hexaemeron")
        (root / "state.json").write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )
        ledger = root / "ledger.jsonl"
        entries = [
            json.loads(line)
            for line in ledger.read_text(encoding="utf-8").splitlines()
            if line
        ]
        entries[-1]["state"] = controller.state_fingerprint(state)
        entries[-1]["hash"] = hashlib.sha256(
            controller.canonical(
                {
                    key: entries[-1][key]
                    for key in ("ts", "event", "data", "prev", "state")
                }
            ).encode()
        ).hexdigest()
        ledger.write_text(
            "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
            encoding="utf-8",
        )

    def park_on_step_branch(self, *, assigned=False):
        """Commit the fixture sources and stand on the Step branch."""
        source_path = self.prepare_capture(assigned=assigned)
        self.git(
            "add",
            "--",
            "study.md",
            "runbook.md",
            "steps.json",
            "green_report.py",
            "tests/check-map-v1.json",
            source_path,
            "audit/rounds/source.synopsis.md",
        )
        self.git("commit", "-q", "-m", "fixture capture parent")
        parent = self.git("rev-parse", "HEAD").stdout.strip()
        state = self.state()
        state["steps"][0]["inoculation_parent"] = parent
        self.rewrite_last_controller_state(state)
        self.fake_refs[state["run_branch"]] = parent
        self.git("checkout", "-q", "-b", self.step_branch(1, state))
        return parent

    def write_no_known_findings(self):
        state = self.state()
        capture = state["receipts"]["runbook"]["known_failure_inventory"]
        record = {
            "schema": "fiat-no-known-findings/v1",
            "study_sha256": capture["study_sha256"],
            "inventory_sha256": capture["inventory_sha256"],
            "source_views": [
                {
                    "id": view["id"],
                    "source_sha256": view["source_sha256"],
                    "view_sha256": view["view_sha256"],
                }
                for view in capture["source_views"]
            ],
            "consuming_step": state["current_step"],
            "assertion": "no-known-findings-for-step",
        }
        self.write(
            f".hexaemeron/steps/{state['current_step']}/inoculation/"
            "no-known-findings.json",
            json.dumps(record, indent=2, sort_keys=True) + "\n",
        )
        return record

    def open_implementation(self):
        """Receipt the zero-assigned inoculation and open `implement`."""
        parent = self.park_on_step_branch()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        return parent

    def receipt_implementation(self):
        """Commit a product change and receipt it through `done implement`."""
        self.write("implementation.py", "VALUE = 'implemented'\n")
        self.git("add", "--", "implementation.py")
        self.git("commit", "-q", "-m", "fixture implementation")
        head = self.git("rev-parse", "HEAD").stdout.strip()
        branch = self.step_branch(1, self.state())
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            branch,
            "--commit",
            head,
            "--tests",
            "green",
        )
        return head


class RecoveryLifecycleTests(RecoveryFixture):
    def test_status_and_next_preserve_the_recovery_projection(self):
        parent = self.open_implementation()
        controller = hexctl_module()

        payload = self.state()
        projection = payload["known_failure_recovery"]
        self.assertEqual(
            controller.RECOVERY_PROJECTION_SCHEMA, projection["schema"]
        )
        self.assertEqual(1, projection["step"])
        self.assertEqual("implement", projection["phase"])
        self.assertEqual(parent, projection["step_parent"])
        self.assertEqual([], projection["assigned_ids"])
        self.assertEqual([], projection["remaining_ids"])
        self.assertEqual(
            payload["receipts"]["runbook"]["known_failure_inventory"][
                "inventory_sha256"
            ],
            projection["inventory_sha256"],
        )
        self.assertEqual(
            "no-known-findings-for-step",
            projection["no_known_findings"]["assertion"],
        )

        directive = self.next_json()
        self.assertEqual(projection, directive["known_failure_recovery"])
        self.assertEqual(
            projection, directive["brief"]["known_failure_recovery"]
        )

        human = self.run_ctl("status").stdout
        self.assertIn("known failures: recovery", human)
        self.assertIn(parent[:12], human)
        self.assertIn("no-findings claim bound", human)

    def test_implementation_binds_declared_suites_and_verify_replays_them(self):
        self.open_implementation()
        head = self.receipt_implementation()

        receipted = self.state()
        final_green = receipted["steps"][0]["receipts"]["implement"][
            "final_green"
        ]
        self.assertEqual(
            {"final_commit", "manifests", "suites"}, set(final_green)
        )
        self.assertEqual(head, final_green["final_commit"])
        self.assertEqual([], final_green["manifests"])
        self.assertEqual(
            ["hexaemeron-suite", "root-suite"],
            [row["check"] for row in final_green["suites"]],
        )
        self.assertEqual([0, 0], [row["exit"] for row in final_green["suites"]])
        self.assertEqual("audit", receipted["known_failure_recovery"]["phase"])
        self.run_ctl("verify")

    def test_verify_refuses_a_receipt_whose_suite_evidence_went_missing(self):
        self.open_implementation()
        self.receipt_implementation()
        state = self.state()
        state["steps"][0]["receipts"]["implement"]["final_green"]["suites"] = []
        self.rewrite_last_controller_state(state)

        refused = self.run_ctl("verify", expect=1)
        self.assertIn("incomplete suite evidence", refused.stderr)

    def test_a_legacy_run_carries_no_invented_recovery_evidence(self):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Legacy\n\n**Goal.** Continue.\n",
        )
        steps = self.write("steps.json", '["Legacy"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

        payload = self.state()
        self.assertNotIn("known_failure_recovery", payload)
        self.assertNotIn("known_failure_recovery", self.next_json())
        self.assertNotIn("known failures", self.run_ctl("status").stdout)
        self.run_ctl("verify")

        payload["steps"][0]["receipts"]["implement"] = {
            "branch": "legacy",
            "commit": "0" * 40,
            "tests": "green",
            "verified_commits": [],
            "final_green": {
                "final_commit": "0" * 40,
                "manifests": [],
                "suites": [],
            },
        }
        self.rewrite_last_controller_state(payload)
        refused = self.run_ctl("verify", expect=1)
        self.assertIn("invented inoculation state", refused.stderr)

    def test_a_refused_receipt_leaves_controller_bytes_unchanged(self):
        self.open_implementation()
        self.receipt_implementation()
        state = self.state()
        state["steps"][0]["receipts"]["implement"]["final_green"]["suites"][0][
            "exit"
        ] = 1
        self.rewrite_last_controller_state(state)
        before = self.controller_tree()

        verification = self.run_ctl("verify", expect=1)
        self.assertIn("did not exit zero", verification.stderr)
        self.assertEqual(before, self.controller_tree())

        refused = self.run_ctl("audit-round", "--findings", "0", expect=2)
        self.assertIn("did not exit zero", refused.stderr)
        self.assertEqual(before, self.controller_tree())


class FinalGreenProductionTests(RecoveryFixture):
    def establish(self, controller, head):
        state = controller.load_state(self.target)
        capture = controller.receipted_known_failure_inventory(
            self.target, state
        )
        return controller.establish_final_green(
            self.target, state, capture, state["steps"][0], head
        )

    def prepare_assigned_implementation(self):
        self.park_on_step_branch(assigned=True)
        self.write("implementation.py", "VALUE = 'implemented'\n")
        self.git("add", "--", "implementation.py")
        self.git("commit", "-q", "-m", "fixture implementation")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def test_assigned_final_green_publishes_and_then_resumes_idempotently(self):
        head = self.prepare_assigned_implementation()
        controller = hexctl_module()

        first = self.establish(controller, head)
        self.assertEqual(head, first["final_commit"])
        self.assertEqual(
            [self.FINDING], [row["finding_id"] for row in first["manifests"]]
        )
        self.assertEqual(
            ["hexaemeron-suite", "root-suite"],
            [row["check"] for row in first["suites"]],
        )
        manifest_path = Path(
            self.target,
            ".hexaemeron/steps/1/final-green/manifests",
            f"{self.FINDING}.json",
        )
        report_path = Path(
            self.target,
            ".hexaemeron/steps/1/final-green/reports",
            f"{self.FINDING}.report",
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            controller.FINAL_GREEN_MANIFEST_SCHEMA, manifest["schema"]
        )
        self.assertEqual(controller.FINAL_GREEN_ADMISSION, manifest["admission"])
        self.assertEqual(head, manifest["final_commit"])
        self.assertEqual(
            hashlib.sha256(report_path.read_bytes()).hexdigest(),
            manifest["retained_report"]["sha256"],
        )
        self.assertEqual(0o600, manifest_path.stat().st_mode & 0o777)
        published = (manifest_path.read_bytes(), report_path.read_bytes())

        # A second pass discovers the published pair rather than sampling a
        # second execution. The declared report path is still occupied by the
        # first run's output, which a fresh run would refuse outright.
        self.assertEqual(first, self.establish(controller, head))
        self.assertEqual(
            published, (manifest_path.read_bytes(), report_path.read_bytes())
        )

    def test_a_red_fixed_tree_run_publishes_no_manifest(self):
        head = self.prepare_assigned_implementation()
        controller = hexctl_module()
        self.write("red-marker", "the fixed tree is still red\n")
        errors = io.StringIO()

        with redirect_stderr(errors), self.assertRaises(SystemExit) as refused:
            self.establish(controller, head)

        self.assertEqual(2, refused.exception.code)
        self.assertIn("is not admissible", errors.getvalue())
        self.assertFalse(
            Path(
                self.target,
                ".hexaemeron/steps/1/final-green/manifests",
                f"{self.FINDING}.json",
            ).exists()
        )

    def test_an_occupied_declared_report_path_refuses_before_the_runner(self):
        head = self.prepare_assigned_implementation()
        controller = hexctl_module()
        self.write(f".elenchus/{self.FINDING}-green.json", "{}\n")
        errors = io.StringIO()

        with redirect_stderr(errors), self.assertRaises(SystemExit) as refused:
            self.establish(controller, head)

        self.assertEqual(2, refused.exception.code)
        self.assertIn("is occupied", errors.getvalue())

    def test_a_failing_declared_suite_refuses_the_step(self):
        head = self.prepare_assigned_implementation()
        self.write_check_map(hexaemeron_exit=3)
        controller = hexctl_module()
        errors = io.StringIO()

        with redirect_stderr(errors), self.assertRaises(SystemExit) as refused:
            self.establish(controller, head)

        self.assertEqual(2, refused.exception.code)
        self.assertIn("exited 3", errors.getvalue())
        self.assertIn("the fixed tree is not green", errors.getvalue())

    def test_a_declared_command_outside_the_interpreter_set_refuses(self):
        controller = hexctl_module()
        with self.assertRaises(ValueError):
            controller._final_green_executable(["/bin/sh", "-c", "true"])
        self.assertEqual(
            ["-c", "raise SystemExit(0)"],
            controller._final_green_executable(
                ["python3", "-c", "raise SystemExit(0)"]
            )[1:],
        )


class AuditAdmissionTests(RecoveryFixture):
    def test_no_warden_packet_until_final_green_evidence_is_receipted(self):
        self.open_implementation()
        self.run_ctl("record", "security_suite", '"waived: fixture step"')
        self.receipt_implementation()

        directive = self.next_json()
        self.assertEqual("audit-round", directive["do"])
        self.assertEqual("warden", directive["agent"])
        self.assertIn("known_failure_recovery", directive["brief"])

        state = self.state()
        state["steps"][0]["receipts"]["implement"]["final_green"]["suites"] = []
        self.rewrite_last_controller_state(state)
        before = self.controller_tree()

        refused = self.run_ctl("next", expect=2)
        self.assertIn("incomplete suite evidence", refused.stderr)
        self.assertEqual(before, self.controller_tree())

        round_refusal = self.run_ctl(
            "audit-round", "--findings", "0", expect=2
        )
        self.assertIn("incomplete suite evidence", round_refusal.stderr)
        self.assertEqual(before, self.controller_tree())


class AuditLoopOrderingTests(unittest.TestCase):
    """The shipped prose states the ordering the controller enforces."""

    def test_the_audit_loop_reference_states_the_ordering(self):
        reference = " ".join(
            AUDIT_LOOP_REFERENCE.read_text(encoding="utf-8").split()
        )
        self.assertIn(
            "The first Warden audit of a source-bound step begins only after "
            "a complete inoculation receipt and final-green implementation "
            "evidence",
            reference,
        )

    def test_the_skill_names_the_two_schemas_the_receipt_binds(self):
        skill = " ".join(FIAT_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("fiat-final-green-manifest/v1", skill)
        self.assertIn("fiat-known-failure-recovery/v1", skill)


class CheckpointRecoveryTests(unittest.TestCase):
    """A capsule carries the projection and re-checks its own bytes."""

    def projection(self):
        """One complete projection beside the closed capture it binds."""
        fixture = load_fixture("recovery.json")
        document = json.loads(
            json.dumps(
                next(
                    row["document"]
                    for row in fixture["accepted"]
                    if row["id"] == "audit-ready"
                )
            )
        )
        capture = self.closed_capture(fixture["capture"])
        for name in ("study_sha256", "runbook_sha256", "inventory_sha256"):
            document[name] = capture[name]
        return document, capture

    def closed_capture(self, capture):
        controller = hexctl_module()
        source_views = [
            {
                "id": "fixture-audit",
                "path": "audit/rounds/source.synopsis.md",
                "source_sha256": "6" * 64,
                "view_sha256": "7" * 64,
            }
        ]
        claim = {
            "source_views": [
                {
                    "id": "fixture-audit",
                    "source_sha256": "6" * 64,
                    "view_sha256": "7" * 64,
                }
            ],
            "consuming_step": 1,
            "surveyor_assertion": "no-known-findings",
        }
        inventory = {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": source_views,
            "findings": [],
            "no_known_findings": claim,
        }
        return {
            "schema": "protasis-known-failure-inventory-capture/v1",
            "study_sha256": capture["study_sha256"],
            "runbook_sha256": capture["runbook_sha256"],
            "inventory_sha256": hashlib.sha256(
                controller.canonical(inventory).encode("utf-8")
            ).hexdigest(),
            "source_views": source_views,
            "findings": [],
            "no_known_findings": claim,
            "assignments": [],
        }

    def captured_state(self, projection, capture):
        return {
            "phase": "steps",
            "current_step": 1,
            "steps": [
                {
                    "n": projection["step"],
                    "phase": projection["phase"],
                    "inoculation_parent": projection["step_parent"],
                }
            ],
            "receipts": {"runbook": {"known_failure_inventory": capture}},
        }

    def inventory_for(self, projection):
        references = list(projection["guard_manifests"]) + list(
            projection["final_green"]["manifests"]
        )
        return [
            {
                "path": "controller/"
                + reference["path"].removeprefix(".hexaemeron/"),
                "bytes": 1,
                "sha256": reference["sha256"],
            }
            for reference in references
        ]

    def test_a_capsule_must_match_its_own_manifest_bytes(self):
        controller = hexctl_module()
        projection, capture = self.projection()
        state = self.captured_state(projection, capture)
        inventory = self.inventory_for(projection)
        manifest = {"known_failures": projection}

        controller._checkpoint_verify_known_failures(manifest, state, inventory)

        drifted = [dict(row) for row in inventory]
        drifted[0]["sha256"] = "e" * 64
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit):
            controller._checkpoint_verify_known_failures(
                manifest, state, drifted
            )
        self.assertIn("capsule's own manifest bytes", errors.getvalue())

    def test_a_capsule_cannot_omit_or_invent_recovery_evidence(self):
        controller = hexctl_module()
        projection, capture = self.projection()
        state = self.captured_state(projection, capture)
        inventory = self.inventory_for(projection)

        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit):
            controller._checkpoint_verify_known_failures({}, state, inventory)
        self.assertIn("omits its known-failure recovery", errors.getvalue())

        legacy = {
            "phase": "steps",
            "current_step": 1,
            "steps": [{"n": 1}],
            "receipts": {},
        }
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit):
            controller._checkpoint_verify_known_failures(
                {"known_failures": projection}, legacy, inventory
            )
        self.assertIn("invents known-failure recovery", errors.getvalue())
        controller._checkpoint_verify_known_failures({}, legacy, inventory)

    def test_a_capsule_projection_must_name_its_captured_step(self):
        controller = hexctl_module()
        projection, capture = self.projection()
        state = self.captured_state(projection, capture)
        state["steps"][0]["inoculation_parent"] = "9" * 40
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit):
            controller._checkpoint_verify_known_failures(
                {"known_failures": projection},
                state,
                self.inventory_for(projection),
            )
        self.assertIn("another step parent", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
