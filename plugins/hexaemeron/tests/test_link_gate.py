"""Study and runbook receipts refuse location-dependent pointers.

`done study` and `done runbook` pin an artefact's SHA-256, and an amendment
keeps the receipted bytes as its exact prefix, so a link that resolves only
from the directory it was written in cannot be repaired after the pin. Three
runs met that. These cases hold the four receipts that pin a study or runbook
digest to the rule through the command line, and inject loader and checker
faults into one controller process where the command line cannot stage them.
"""

import hashlib
import json
import os
import random
import shutil
import tempfile
import time
import unittest
from contextlib import chdir, nullcontext, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

try:
    from .hexctl_harness import COMPLETE_STUDY, HexctlCase, hexctl_module
except ImportError:
    from hexctl_harness import COMPLETE_STUDY, HexctlCase, hexctl_module

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HYPOMNEMA = HERE.parent / "skills" / "hypomnema" / "scripts" / "hypomnema.py"
DESIGN_EVIDENCE = HERE.parent / "skills" / "protasis" / "scripts" / "design_evidence.py"
FIAT_SKILL = HERE.parent / "skills" / "fiat" / "SKILL.md"
PINNED = "485c90d3ad545b696584197f83d942c705988216"

# The five discipline citations the skills#1070 run froze into its receipted
# study, in the form the design record's specimen probe uses.
SPECIMEN = "\n".join(
    ["# Specimen", ""]
    + [
        f"See [{name}](../{name}/SKILL.md) for its contract."
        for name in ("ephoros", "phylax", "metron", "elenchus", "hypomnema")
    ]
) + "\n"
# Resolves two directories deep and not four.
DEPTH_SENSITIVE = (
    "# Specimen\n\n"
    "See [fiat](../../plugins/hexaemeron/skills/fiat/SKILL.md) for the loop.\n"
)
# The same citation, pinned to a commit.
CONFORMING = (
    "# Specimen\n\n"
    "See [fiat](https://github.com/wildcat-finance/skills/blob/"
    f"{PINNED}/plugins/hexaemeron/skills/fiat/SKILL.md) for the loop.\n"
)
PENDING = ("study-amendment-pending.json", "runbook-amendment-pending.json")


def hypomnema_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("link_gate_hypomnema", HYPOMNEMA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decision_record(number, title):
    return (
        f"# {number}: {title}\n\n"
        "## Status\n\nAccepted, 2026-09-14.\n\n"
        "## Context\n\nA fixture needs a record.\n\n"
        "## Decision\n\nKeep the fixture.\n\n"
        "## Alternatives\n\nNone were needed.\n\n"
        "## Consequences\n\nNone follow.\n"
    )


def run_in_process(module, target, *argv):
    """Run one hexctl command inside this process, as `main()` would from `target`."""
    args = module.build_parser().parse_args(["--dir", target, *argv])
    output, error = StringIO(), StringIO()
    code = 0
    with chdir(target), redirect_stdout(output), redirect_stderr(error):
        try:
            with module.held_lock(args.dir, args.fn.__name__):
                args.fn(args)
        except SystemExit as exit:
            code = exit.code
    return code, output.getvalue(), error.getvalue()


class LinkGateCase(HexctlCase):
    def controller_bytes(self):
        root = Path(self.target) / ".hexaemeron"
        return tuple(
            (root / name).read_bytes() for name in ("state.json", "ledger.jsonl")
        )

    def leftovers(self):
        root = Path(self.target) / ".hexaemeron"
        return sorted(
            [path.name for path in root.glob("link-gate-*")]
            + [name for name in PENDING if (root / name).exists()]
        )

    def refuse_study(self, name, body):
        path = self.write(name, body)
        before = self.controller_bytes()
        refused = self.run_ctl(
            "done", "study", "--artifact", path,
            "--skills", "hexaemeron:imprimatur,hexaemeron:hypomnema",
            expect=2,
        )
        self.assertEqual(self.controller_bytes(), before)
        self.assertEqual(self.leftovers(), [])
        return refused.stderr

    def receipt_without_the_gate(self, *argv):
        """Receipt as a controller from before the gate would have."""
        module = hexctl_module()
        with mock.patch.object(
            module,
            "refuse_location_dependent_pointers",
            lambda *args, **kwargs: None,
            create=True,
        ):
            code, _, error = run_in_process(module, self.target, *argv)
        self.assertEqual(code, 0, error)


class PointerRuleReceiptTests(LinkGateCase):
    def test_done_study_refuses_the_frozen_specimen_and_writes_nothing(self):
        self.init()
        stderr = self.refuse_study(".hexaemeron/study.md", SPECIMEN)
        self.assertIn(
            "study artefact .hexaemeron/study.md line 3: pointer rule refused "
            "pointer ../ephoros/SKILL.md:",
            stderr,
        )
        self.assertNotIn("../phylax/SKILL.md", stderr)
        self.assertEqual(self.next_json()["do"], "study")

    def test_a_link_that_resolves_from_the_state_directory_is_still_refused(self):
        self.init()
        body = "# Study\n\nThe checked record is [the evidence](design-evidence.json).\n"
        placed = Path(self.target) / self.write(".hexaemeron/study.md", body)
        self.assertEqual([], [f.code for f in hypomnema_module().check(placed)])
        stderr = self.refuse_study(".hexaemeron/study.md", body)
        self.assertIn(
            "line 3: pointer rule refused pointer design-evidence.json:", stderr
        )

    def test_a_slash_rooted_link_is_refused_even_when_it_resolves(self):
        self.init()
        record = Path(self.target).resolve() / ".hexaemeron" / "design-evidence.json"
        self.assertTrue(record.is_file())
        body = f"# Study\n\nRead [the record]({record.as_posix()}).\n"
        stderr = self.refuse_study(".hexaemeron/study.md", body)
        self.assertIn(
            f"line 3: pointer rule refused pointer {record.as_posix()}:", stderr
        )

    def test_a_link_inside_a_tilde_block_is_refused(self):
        self.init()
        body = "# Study\n\n~~~text\n[quoted](../quoted.md)\n~~~\n"
        stderr = self.refuse_study(".hexaemeron/study.md", body)
        self.assertIn("line 4: pointer rule refused pointer ../quoted.md:", stderr)

    def test_a_runbook_keyword_pointer_is_refused(self):
        self.init()
        body = "# Study\n\nThe alert names runbook: runbooks/stall.md first.\n"
        stderr = self.refuse_study(".hexaemeron/study.md", body)
        self.assertIn(
            "line 3: pointer rule refused pointer runbooks/stall.md:", stderr
        )

    def test_location_independent_forms_receipt_exactly_as_before(self):
        self.init()
        body = (
            "# Study\n\n## Scope\n\n"
            "The loop is [fiat](https://github.com/wildcat-finance/skills/blob/"
            f"{PINNED}/plugins/hexaemeron/skills/fiat/SKILL.md).\n"
            "Return to [the scope](#scope).\n"
            "The controller is `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,"
            " once quoted as `[hexctl](../fiat/scripts/hexctl.py)`.\n"
            "See [the notes](../notes.md). "
            "<!-- hypomnema: allow the notes land in a later step -->\n\n"
            "```text\n[example](../example.md)\n```\n"
        )
        path = self.write(".hexaemeron/study.md", body)
        self.run_ctl(
            "done", "study", "--artifact", path, "--skills", "hexaemeron:imprimatur"
        )
        receipt = self.state()["receipts"]["study"]
        self.assertEqual(
            set(receipt), {"artifact", "sha256", "skills", "design_evidence"}
        )
        self.assertEqual(receipt["artifact"], ".hexaemeron/study.md")
        self.assertEqual(receipt["sha256"], hashlib.sha256(body.encode()).hexdigest())
        ledger = (Path(self.target) / ".hexaemeron" / "ledger.jsonl").read_text(
            encoding="utf-8"
        )
        event = json.loads(ledger.splitlines()[-1])
        self.assertEqual(event["event"], "done:study")
        self.assertEqual(
            set(event["data"]), {"artifact", "sha256", "skills", "design_evidence"}
        )
        self.assertEqual(self.leftovers(), [])

    def test_identical_bytes_get_one_verdict_at_every_depth(self):
        places = (
            ".hexaemeron/study.md",
            "docs/link-gate/study.md",
            "plugins/hexaemeron/docs/link-gate/study.md",
        )
        self.init()
        fiat = Path(self.target) / "plugins" / "hexaemeron" / "skills" / "fiat"
        fiat.mkdir(parents=True)
        (fiat / "SKILL.md").write_text("# Fiat\n", encoding="utf-8")
        checker = hypomnema_module()
        in_place = {}
        for place in places:
            placed = Path(self.target) / self.write(place, DEPTH_SENSITIVE)
            in_place[place] = [finding.code for finding in checker.check(placed)]
            placed.unlink()
        # The checker alone passes one depth and fails the others.
        self.assertEqual(in_place, {places[0]: ["H001"], places[1]: [], places[2]: ["H001"]})
        for place in places:
            with self.subTest(refused=place):
                stderr = self.refuse_study(place, DEPTH_SENSITIVE)
                self.assertIn(f"study artefact {place} line 3: pointer rule refused", stderr)
        for place in places:
            with self.subTest(accepted=place):
                run = self if place == places[0] else type(self)(methodName="runTest")
                if run is not self:
                    run.setUp()
                try:
                    if run is not self:
                        run.init()
                    path = run.write(place, CONFORMING)
                    run.run_ctl("done", "study", "--artifact", path)
                    self.assertEqual(run.next_json()["do"], "runbook")
                finally:
                    if run is not self:
                        run.tearDown()

    def test_done_runbook_refuses_the_specimen_and_accepts_a_conforming_runbook(self):
        self.init()
        study = self.write(".hexaemeron/study.md", CONFORMING)
        self.run_ctl("done", "study", "--artifact", study)
        self.auto_design_lock = False
        head = self.design_lock_block() + "\n# Runbook\n\n## Step 1: Core\n\n**Goal.** Core.\n\n"
        steps = self.write(".hexaemeron/steps.json", '["Core"]')
        text = head + SPECIMEN.split("\n", 2)[2]
        runbook = self.write(".hexaemeron/runbook.md", text)
        line = text.splitlines().index("See [ephoros](../ephoros/SKILL.md) for its contract.") + 1
        before = self.controller_bytes()
        refused = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps, expect=2
        )
        self.assertIn(
            f"runbook artefact .hexaemeron/runbook.md line {line}: pointer rule "
            "refused pointer ../ephoros/SKILL.md:",
            refused.stderr,
        )
        self.assertEqual(self.controller_bytes(), before)
        self.assertEqual(self.leftovers(), [])
        self.write(".hexaemeron/runbook.md", head + CONFORMING.split("\n", 2)[2])
        self.run_ctl("done", "runbook", "--artifact", runbook, "--steps-file", steps)
        self.assertEqual(
            set(self.state()["receipts"]["runbook"]),
            {"artifact", "sha256", "step_count", "design_lock"},
        )
        self.assertEqual(self.next_json()["do"], "implement")

    def test_amend_study_checks_only_the_appended_bytes(self):
        self.init()
        fixture = Path(COMPLETE_STUDY).read_text(encoding="utf-8")
        original = fixture.replace(
            "This repository.\n", "This repository, and [the notes](../notes.md).\n", 1
        )
        self.assertNotEqual(original, fixture)
        study = self.write("study.md", original)
        self.receipt_without_the_gate("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Core\n\n**Goal.** Core.\n\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n",
        )
        steps = self.write("steps.json", json.dumps(["Core", "Finish"]))
        self.run_ctl("done", "runbook", "--artifact", runbook, "--steps-file", steps)
        canonical = Path(self.target) / "study.md"
        hostile = original + self.amendment(
            why="The receipted baseline disproved it; see [the notes](../notes.md)."
        )
        candidate = self.write("candidate.md", hostile)
        line = next(
            number for number, text in enumerate(hostile.splitlines(), 1)
            if text.startswith("**Why.**")
        )
        before = (self.controller_bytes(), canonical.read_bytes())
        refused = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn(
            f"study amendment to study.md line {line}: pointer rule refused "
            "pointer ../notes.md:",
            refused.stderr,
        )
        self.assertEqual((self.controller_bytes(), canonical.read_bytes()), before)
        self.assertEqual(self.leftovers(), [])
        conforming = original + self.amendment()
        candidate = self.write("candidate.md", conforming)
        self.run_ctl("amend", "study", "--artifact", candidate)
        self.assertEqual(
            self.state()["receipts"]["study"]["sha256"],
            hashlib.sha256(conforming.encode()).hexdigest(),
        )

    def test_amend_runbook_checks_only_the_appended_bytes(self):
        self.init()
        study = self.write("study.md", Path(COMPLETE_STUDY).read_text(encoding="utf-8"))
        self.run_ctl("done", "study", "--artifact", study)
        blocks = []
        for number, title in enumerate(("Core", "Finish"), 1):
            goal = f"Ship {title}"
            if number == 1:
                goal += ", as [the notes](../notes.md) describe"
            blocks.append(
                f"## Step {number}: {title}\n\n"
                f"**Goal.** {goal}.\n"
                f"**Entry.** Step {number} is ready.\n"
                "**Exit.** Run `fiat-v1.0.0`.\n"
                f"**Files.** `step-{number}.md`.\n"
                "**Tests.** Run `python3 -m unittest`.\n"
                "**Disciplines.** none, fixture only.\n"
            )
        receipted = self.design_lock_block() + "\n# Runbook\n\n" + "\n".join(blocks)
        runbook = self.write("runbook.md", receipted)
        steps = self.write("steps.json", json.dumps(["Core", "Finish"]))
        self.receipt_without_the_gate(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        canonical = Path(self.target) / "runbook.md"
        hostile = receipted + self.runbook_amendment(
            why="The target version changed; see [the notes](../notes.md)."
        )
        candidate = self.write("candidate.md", hostile)
        line = next(
            number for number, text in enumerate(hostile.splitlines(), 1)
            if text.startswith("**Why.**")
        )
        before = (self.controller_bytes(), canonical.read_bytes())
        refused = self.run_ctl("amend", "runbook", "--artifact", candidate, expect=2)
        self.assertIn(
            f"runbook amendment to runbook.md line {line}: pointer rule refused "
            "pointer ../notes.md:",
            refused.stderr,
        )
        self.assertEqual((self.controller_bytes(), canonical.read_bytes()), before)
        self.assertEqual(self.leftovers(), [])
        conforming = receipted + self.runbook_amendment()
        candidate = self.write("candidate.md", conforming)
        self.run_ctl("amend", "runbook", "--artifact", candidate)
        self.assertEqual(
            self.state()["receipts"]["runbook"]["sha256"],
            hashlib.sha256(conforming.encode()).hexdigest(),
        )

    def test_decision_references_resolve_only_against_a_record_in_docs_decisions(self):
        self.init()
        decisions = Path(self.target) / "docs" / "decisions"
        decisions.mkdir(parents=True)
        (decisions / "ADR-002-other-decision.md").write_text(
            decision_record("ADR-002", "Other decision"), encoding="utf-8"
        )
        stable = "# Study\n\nThe choice is recorded as `adr/demo-decision`.\n"
        superseding = "# Study\n\nThe first choice was superseded by ADR-001.\n"
        stderr = self.refuse_study(".hexaemeron/study.md", stable)
        self.assertIn(
            "study artefact .hexaemeron/study.md line 3: checker refused pointer "
            "adr/demo-decision with H009",
            stderr,
        )
        stderr = self.refuse_study(".hexaemeron/study.md", superseding)
        self.assertIn(
            "study artefact .hexaemeron/study.md line 3: checker refused pointer "
            "ADR-001 with H002",
            stderr,
        )
        (decisions / "ADR-001-demo-decision.md").write_text(
            decision_record("ADR-001", "Demo decision"), encoding="utf-8"
        )
        path = self.write(".hexaemeron/study.md", stable + superseding.split("\n", 2)[2])
        self.run_ctl("done", "study", "--artifact", path)
        self.assertEqual(self.next_json()["do"], "runbook")


class CheckerBoundaryTests(LinkGateCase):
    """Loader and checker faults, injected into one controller process."""

    SOURCE = HYPOMNEMA.read_text(encoding="utf-8")
    MAIN = 'if __name__ == "__main__":\n'

    def replaced_main(self, body):
        head, marker, _ = self.SOURCE.rpartition(self.MAIN)
        self.assertEqual(marker, self.MAIN)
        return head + marker + body

    def fake_root(self, checker_source):
        root = Path(tempfile.mkdtemp(prefix="plugin-root-"))
        self.addCleanup(shutil.rmtree, root, True)
        scripts = root / "skills" / "hypomnema" / "scripts"
        scripts.mkdir(parents=True)
        if checker_source is not None:
            (scripts / "hypomnema.py").write_text(checker_source, encoding="utf-8")
        evidence = root / "skills" / "protasis" / "scripts" / "design_evidence.py"
        evidence.parent.mkdir(parents=True)
        shutil.copyfile(DESIGN_EVIDENCE, evidence)
        return root

    def refused_in_process(self, root, **constants):
        study = self.write(".hexaemeron/study.md", CONFORMING)
        module = hexctl_module()
        before = self.controller_bytes()
        with mock.patch.object(module, "plugin_root", return_value=str(root)):
            with mock.patch.multiple(module, **constants) if constants else nullcontext():
                code, _, stderr = run_in_process(
                    module, self.target, "done", "study", "--artifact", study
                )
        self.assertEqual(code, 2, stderr)
        self.assertEqual(self.controller_bytes(), before)
        self.assertEqual(self.leftovers(), [])
        return stderr

    def test_a_missing_checker_refuses_before_any_write(self):
        self.init()
        stderr = self.refused_in_process(self.fake_root(None))
        self.assertIn(
            "study artefact .hexaemeron/study.md: pointer rule refused: the bundled "
            "Hypomnema checker is unavailable",
            stderr,
        )

    def test_a_checker_missing_a_name_refuses(self):
        self.init()
        definitions = {
            "LINK": "\nLINK = re.compile(",
            "RUNBOOK": "\nRUNBOOK = re.compile(",
            "suppressed": "\ndef suppressed(",
            "_external": "\ndef _external(",
            "_code_spans": "\ndef _code_spans(",
            "_within": "\ndef _within(",
        }
        for name, definition in definitions.items():
            with self.subTest(name=name):
                self.assertEqual(self.SOURCE.count(definition), 1)
                renamed = self.SOURCE.replace(
                    definition, definition.replace(name, f"{name}_renamed")
                )
                stderr = self.refused_in_process(self.fake_root(renamed))
                self.assertIn(
                    f"pointer rule refused: the bundled Hypomnema checker has no "
                    f"usable {name}",
                    stderr,
                )

    def test_a_checker_that_cannot_be_loaded_refuses(self):
        self.init()
        for label, source in (
            ("syntax", "def (\n"),
            ("exit", "raise SystemExit(3)\n"),
            ("error", "raise RuntimeError('ghp_LOADER_SECRET')\n"),
        ):
            with self.subTest(label=label):
                stderr = self.refused_in_process(self.fake_root(source))
                self.assertIn(
                    "pointer rule refused: the bundled Hypomnema checker cannot be "
                    "loaded",
                    stderr,
                )
                self.assertNotIn("ghp_LOADER_SECRET", stderr)

    def test_a_checker_timeout_refuses(self):
        self.init()
        root = self.fake_root(
            self.replaced_main("    import time\n    time.sleep(20)\n")
        )
        started = time.monotonic()
        stderr = self.refused_in_process(root, GIT_TIMEOUT=1)
        self.assertLess(time.monotonic() - started, 15)
        self.assertIn(
            "checker refused: the bundled Hypomnema checker timed out after 1 seconds",
            stderr,
        )
        self.assertFalse((root / "skills" / "hypomnema" / "scripts" / "__pycache__").exists())

    def test_a_checker_output_overflow_refuses(self):
        self.init()
        root = self.fake_root(self.replaced_main("    print('x' * 8192)\n"))
        stderr = self.refused_in_process(root, GIT_OUTPUT_MAX=1024)
        self.assertIn(
            "checker refused: the bundled Hypomnema checker exceeded its "
            "1024-byte output cap",
            stderr,
        )

    def test_malformed_checker_output_refuses(self):
        self.init()
        finding = (
            '{"path": sys.argv[3], "line": 1, "code": "H001", "message": "m"}'
        )
        cases = {
            "not-json": "    print('ghp_CHILD_SECRET')\n    raise SystemExit(1)\n",
            "object": "    import json\n    print(json.dumps({'findings': []}))\n",
            "extra-key": (
                "    import json\n"
                "    print(json.dumps([{**" + finding + ", 'raw': 'x'}]))\n"
                "    raise SystemExit(1)\n"
            ),
            "boolean-line": (
                "    import json\n"
                "    print(json.dumps([{**" + finding + ", 'line': True}]))\n"
                "    raise SystemExit(1)\n"
            ),
            "line-past-the-end": (
                "    import json\n"
                "    print(json.dumps([{**" + finding + ", 'line': 99}]))\n"
                "    raise SystemExit(1)\n"
            ),
            "bad-code": (
                "    import json\n"
                "    print(json.dumps([{**" + finding + ", 'code': 'X1'}]))\n"
                "    raise SystemExit(1)\n"
            ),
            "duplicate-key": (
                "    print('[{\"path\": \"a\", \"path\": \"b\", \"line\": 1,"
                " \"code\": \"H001\", \"message\": \"m\"}]')\n"
                "    raise SystemExit(1)\n"
            ),
            "non-finite": (
                "    print('[{\"path\": \"a\", \"line\": NaN,"
                " \"code\": \"H001\", \"message\": \"m\"}]')\n"
                "    raise SystemExit(1)\n"
            ),
            "clean-exit-with-findings": (
                "    import json\n    print(json.dumps([" + finding + "]))\n"
            ),
            "finding-exit-without-findings": (
                "    print('[]')\n    raise SystemExit(1)\n"
            ),
            "usage-exit": "    print('[]')\n    raise SystemExit(2)\n",
        }
        for label, body in cases.items():
            with self.subTest(label=label):
                root = self.fake_root(self.replaced_main(body))
                stderr = self.refused_in_process(root)
                self.assertIn(
                    "study artefact .hexaemeron/study.md: checker refused: the "
                    "bundled Hypomnema checker returned malformed output",
                    stderr,
                )
                self.assertNotIn("ghp_CHILD_SECRET", stderr)


class PointerRuleSourceTests(unittest.TestCase):
    """The rule's reading, held against the loaded checker and the tree."""

    # Every row sits in a directory where no relative target exists, so the
    # checker reports H001 or H003 exactly where it recognises a pointer.
    RECOGNITION = (
        ("[a](missing.md)", True),
        ("[a](missing.md#part)", True),
        ("[a](#anchor)", False),
        ("[a](https://example.org/x.md)", False),
        ("[a](HTTP://example.org/x.md)", False),
        ("[a](mailto:owner@example.org)", False),
        ("[a](tel:+15550100)", False),
        ("[a](ftp://example.org/x.md)", False),
        ("[a](file:///link-gate-absent/x.md)", True),
        ("[a](/link-gate-absent/x.md)", True),
        ("`[a](missing.md)`", False),
        ("\\`[a](missing.md)\\`", True),
        ("![a](missing.png)", False),
        ("```\n[a](missing.md)\n```", False),
        ("  ```python\n[a](missing.md)\n  ```", False),
        ("````\n[a](missing.md)\n````", False),
        ("```\n```\n[a](missing.md)", True),
        ("~~~\n[a](missing.md)\n~~~", True),
        ("[a](missing.md) <!-- hypomnema: allow lands later -->", False),
        ("<!-- hypomnema: allow lands later -->\n[a](missing.md)", False),
        ("<!-- hypomnema: allow -->\n[a](missing.md)", True),
        ("runbook: runbooks/missing.md", True),
        ("`runbook: runbooks/missing.md`", False),
        ("runbook: `runbooks/missing.md`", True),
        ("myrunbook: runbooks/missing.md", False),
        ("sub-runbook: runbooks/missing.md", False),
    )

    def test_the_rule_recognises_exactly_the_pointers_the_checker_resolves(self):
        module = hexctl_module()
        rule = module.link_gate_module("specimen")
        checker = hypomnema_module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "specimen.md"
            for source, recognised in self.RECOGNITION:
                with self.subTest(source=source):
                    path.write_text(source + "\n", encoding="utf-8")
                    reported = any(
                        finding.code in ("H001", "H003")
                        for finding in checker.check(path)
                    )
                    found = module._location_dependent_pointer(rule, source + "\n")
                    self.assertEqual(reported, recognised)
                    self.assertEqual(found is not None, recognised)

    def test_the_committed_link_gate_study_and_runbook_pass_the_rule(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            shutil.copytree(ROOT / "docs" / "decisions", base / "docs" / "decisions")
            for name in ("study.md", "runbook.md"):
                data = (ROOT / "docs" / "fiat-link-gate" / name).read_bytes()
                with self.subTest(name=name):
                    error = StringIO()
                    try:
                        with redirect_stderr(error):
                            module.refuse_location_dependent_pointers(
                                str(base), data, f"committed {name}"
                            )
                    except SystemExit as exit:
                        self.fail(f"{name} refused with {exit.code}: {error.getvalue()}")
                    self.assertEqual(list((base / ".hexaemeron").glob("*")), [])

    def test_a_line_of_tens_of_thousands_of_backticks_scans_in_linear_time(self):
        module = hexctl_module()
        rule = module.link_gate_module("specimen")
        # A line that starts with three backticks is a fence line, so each
        # prefix opens with other text: thirty thousand single runs, one run of
        # sixty thousand, and thirty thousand escaped backticks.
        for prefix in ("` " * 30000, "a" + "`" * 60000, "\\` " * 30000):
            for pointer, target in (
                ("[x](../missing.md)", "../missing.md"),
                ("runbook: runbooks/missing.md", "runbooks/missing.md"),
            ):
                with self.subTest(runs=len(prefix), pointer=pointer):
                    started = time.perf_counter()
                    found = module._location_dependent_pointer(
                        rule, prefix + " " + pointer + "\n"
                    )
                    elapsed = time.perf_counter() - started
                    self.assertEqual(found, (1, target))
                    self.assertLess(elapsed, 2.0)

    def test_amendment_lines_map_onto_the_full_candidate(self):
        module = hexctl_module()
        pieces = ("a", "b", " ", "\n", "\r", "\r\n", "\x0b", "\x85", " ")
        generator = random.Random(1086)
        for _ in range(3000):
            whole = "".join(
                generator.choice(pieces) for _ in range(generator.randint(1, 14))
            )
            boundary = generator.randint(0, len(whole))
            preceding, appended = whole[:boundary], whole[boundary:]
            spans, start = [], 0
            for line in whole.splitlines(keepends=True):
                spans.append((start, start + len(line)))
                start += len(line)
            offset = boundary
            for number, line in enumerate(appended.splitlines(keepends=True), 1):
                expected = next(
                    index for index, (low, high) in enumerate(spans, 1)
                    if low <= offset < high
                )
                self.assertEqual(
                    module._link_gate_line(preceding, appended, number),
                    expected,
                    (whole, boundary, number),
                )
                offset += len(line)

    def test_the_phase_note_names_the_four_receipts_and_the_appended_bytes_check(self):
        text = FIAT_SKILL.read_text(encoding="utf-8")
        start = text.index("**Study and runbook.**")
        paragraph = " ".join(text[start:text.index("\n\n", start)].split())
        for receipt in ("`done study`", "`done runbook`", "`amend study`", "`amend runbook`"):
            self.assertIn(receipt, paragraph)
        self.assertIn("absolute URL", paragraph)
        self.assertIn("in-page anchor", paragraph)
        self.assertIn("bytes an amendment appends", paragraph)


if __name__ == "__main__":
    unittest.main()
