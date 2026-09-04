"""The integrate gate's read of the sync receipt's recorded base head.

`test_hexctl.py` is cited as authored law by the promise machine, whose
bounded read refuses a contract over 262144 bytes; this suite did not fit in
the file's remaining headroom. The class drives the same CLI surface through
the same fixtures -- `HexctlCase` and its fake delivery tools -- so only the
file boundary moved, not the arrangement under test.

The pre-fix red these guards captured, against the entry controller
(`hexctl.py` sha256
`58e56fd1e07771030ef19e11dacdd16d88ef1229cd6039b13ec55c85a3eb6a37`):
`done sync-run` recorded the merged base tip under `"base_head"`
while `done integrate` asked the receipt for `"base_commit"`, a key no
shipped writer ever stored. The getter always passed None, the published set
was always empty, and a frontier run whose one receipted sync absorbed two
published ledger rows was refused at its terminal receipt with "gained 3
history row(s)" -- the controller-currency run's halt, rebuilt here in
fixture. Each test fails against that controller: the two end-to-end guards
on the refusal itself, the rest on the missing shared constant.
"""

import json
import os
import shutil
import subprocess

try:
    from plugins.hexaemeron.tests.test_hexctl import (
        HEXCTL,
        SUITE,
        HexctlCase,
        frontier_digest,
        hexctl_module,
        row,
        widget_ledger,
    )
except ModuleNotFoundError:
    from test_hexctl import (
        HEXCTL,
        SUITE,
        HexctlCase,
        frontier_digest,
        hexctl_module,
        row,
        widget_ledger,
    )


STEP_PR = "https://github.com/wildcat-finance/example/pull/1"
RUN_PR = "https://github.com/wildcat-finance/example/pull/2"


class FrontierReceiptCase(HexctlCase):
    """A frontier run whose one receipted sync absorbed published rows.

    The topology the controller-currency run halted on: `init` pins a
    one-row ledger, the base publishes two rows while the run is under way,
    the sync receipt records the exact merged base tip, and the run's ledger
    ends with those two absorbed rows plus exactly one row of its own.
    """

    HELD = ("open", "held-thing", "The widget does not do the thing.",
            "Make the widget do the thing.")
    FOREIGN = ("widget-v1.2.0", "widget-v1.3.0")
    OWN = "widget-v1.4.0"

    def setUp(self):
        super().setUp()
        self.install_blob_passthrough()
        self.ledger_rel = os.path.join(
            "plugins", "demo", "skills", "widget", "EVOLUTION.md")
        self.base_digest = frontier_digest(*self.HELD)
        self.baseline_row = row(
            "widget-v1.1.0", "baseline", self.HELD[1], self.base_digest,
            "Versioning starts here.")
        self.write_ledger(self.dir, [self.baseline_row], "widget-v1.1.0")
        self.git("add", self.ledger_rel)
        self.git("commit", "-q", "-m", "widget ledger baseline")

    def install_blob_passthrough(self):
        """Serve `git show <sha>:<path>` from the real repository.

        The shared fake git answers every unhandled `show` with a stub commit
        message, which is right for the trailer checks it exists for and
        wrong for the one blob read `base_ledger_versions` makes. Exactly
        that form goes to the real git -- the fixture is a real repository,
        so the recorded base commit really carries the published ledger --
        and every other call keeps the fake's answers.
        """
        passthrough_bin = os.path.join(self.dir, "blob-tools")
        os.makedirs(passthrough_bin)
        fixture_git = os.path.join(self.dir, "delivery-tools", "git")
        real_git = shutil.which("git")
        script = os.path.join(passthrough_bin, "git")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                "import os, re, sys\n"
                "args = sys.argv[1:]\n"
                "if (len(args) == 2 and args[0] == \"show\"\n"
                "        and re.fullmatch(r\"[0-9a-f]{40}:.+\", args[1])):\n"
                f"    os.execv({real_git!r}, [{real_git!r}, *args])\n"
                f"os.execv({fixture_git!r}, [{fixture_git!r}, *args])\n"
            )
        os.chmod(script, 0o755)
        self.env["PATH"] = passthrough_bin + os.pathsep + self.env["PATH"]

    def held_generation_row(self, version):
        """One generation row retaining the held revision and digest."""
        return row(version, "generation", self.HELD[1], self.base_digest)

    def write_ledger(self, root, rows, header_version):
        widget_ledger(
            os.path.join(root, self.ledger_rel), rows,
            version=header_version, status=self.HELD[0],
            revision=self.HELD[1], frontier=self.HELD[2], job=self.HELD[3])

    def publish_base_rows(self):
        """Two rows other runs published on the base while this one ran."""
        self.write_ledger(
            self.dir,
            [self.baseline_row,
             *(self.held_generation_row(v) for v in self.FOREIGN)],
            self.FOREIGN[-1])
        subprocess.run(["git", "add", self.ledger_rel], cwd=self.dir,
                       check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "published rows"],
                       cwd=self.dir, check=True, capture_output=True)
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.dir,
                              check=True, capture_output=True,
                              text=True).stdout.strip()

    def advance_to_merged_step(self):
        """One step from study to its recorded merge, as the fixtures do."""
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "receipt-key-drift | receipt | compare recorded keys\n"
            "```\n",
        )
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: Ship\n\n**Goal.** Ship.\n")
        steps = self.write("steps.json", json.dumps(["Ship"]))
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)
        self.git("add", "study.md", "runbook.md", "steps.json")
        self.git("commit", "-q", "-m", "fixture")
        self.git("branch", self.step_branch(1))
        self.run_ctl("done", "implement", "--branch", self.step_branch(1),
                     "--commit", "abc123")
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.run_ctl(
            "done", "push", "--pr-url", STEP_PR,
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        self.run_ctl("done", "merge-step", "--step", "1",
                     "--merge-commit", "e" * 40)
        self.write_run_pr()

    def receipt_sync(self, base_sha, sync_sha="7" * 40):
        """A green `done sync-run` whose receipt names the real base tip."""
        state = self.state()
        final_merge = state["integrate"]["merges"]["1"]["merge_commit"]
        base_before = "4" * 40
        self.fake_refs[state["run_branch"]] = sync_sha
        self.fake_refs[self.integration_base(state)] = base_sha
        self.fake_parents[sync_sha] = [final_merge, base_sha]
        self.env["FAKE_GIT_MERGE_BASE"] = base_before
        self.env["FAKE_GIT_DIFF_PATHS"] = json.dumps(
            {
                f"{base_before}..{final_merge}": ["product.py"],
                f"{base_before}..{base_sha}": [self.ledger_rel],
                f"{final_merge}..{sync_sha}": [self.ledger_rel],
            }
        )
        revalidation = self.write(
            os.path.join(".hexaemeron", "integration-revalidation.json"),
            json.dumps(
                {
                    "schema": "fiat-integration-revalidation/v1",
                    "affected_paths": [self.ledger_rel],
                    "checks": [
                        {
                            "id": "root-suite",
                            "command":
                                "python3 -m unittest discover -s tests",
                            "paths": [self.ledger_rel],
                            "exit": 0,
                        }
                    ],
                }
            ),
        )
        self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
        )

    def to_receipted_sync(self):
        """The whole topology up to and including the sync receipt."""
        self.run_ctl("init", "--topic", "frontier receipt",
                     "--frontier", self.ledger_rel)
        self.write_design_evidence()
        base_sha = self.publish_base_rows()
        self.advance_to_merged_step()
        self.write_ledger(
            self.target,
            [self.baseline_row,
             *(self.held_generation_row(v) for v in self.FOREIGN),
             self.held_generation_row(self.OWN)],
            self.OWN)
        self.receipt_sync(base_sha)
        return base_sha

    def integrate(self, expect=0):
        return self.run_ctl(
            "done", "integrate", "--pr-url", RUN_PR,
            "--merge-commit", "f" * 40, expect=expect,
        )

    def edit_sync_receipt(self, edit):
        """A state some other writer left, with its receipt chain intact.

        `verify_run` refuses a state.json whose bytes the chain never
        recorded, so the arrangement under test -- a sync receipt without
        the base-tip key, or with a corrupt value -- is written through the
        module's own commit path, exactly as the controller that recorded
        such a receipt would have written it.
        """
        module = hexctl_module()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        edit(state["integrate"]["sync"])
        module.commit(self.target, state, "fixture:sync-receipt-shape", {})

    def sync_base_head_key(self):
        """Return the shared key while keeping the entry red an assertion."""
        module = hexctl_module()
        self.assertTrue(
            hasattr(module, "SYNC_BASE_HEAD_KEY"),
            "sync receipt writer and reader need one shared base-head key",
        )
        return module.SYNC_BASE_HEAD_KEY

    def test_a_receipted_sync_lets_absorbed_rows_pass_integrate(self):
        """The end-to-end green: subtraction engaged, run complete."""
        base_sha = self.to_receipted_sync()
        proc = self.integrate()
        self.assertIn("run complete", proc.stdout)
        receipt = self.state()["receipts"]["integrate"]
        self.assertEqual(
            receipt["sync"][self.sync_base_head_key()], base_sha)

    def test_the_receipt_names_only_the_subtracted_versions(self):
        """The receipt field carries exactly the two absorbed rows."""
        self.to_receipted_sync()
        self.integrate()
        receipt = self.state()["receipts"]["integrate"]
        self.assertEqual(
            receipt["frontier_subtracted_rows"], list(self.FOREIGN))
        self.assertNotIn(self.OWN, receipt["frontier_subtracted_rows"])

    def test_the_sync_receipt_key_set_is_pinned(self):
        """Writer drift on the receipt shape fails here, not at integrate."""
        self.to_receipted_sync()
        sync = self.state()["integrate"]["sync"]
        self.assertEqual(
            set(sync),
            {
                "commit",
                "base",
                "starting_base",
                self.sync_base_head_key(),
                "parents",
                "github_verified",
                "product_evidence",
                "revalidation",
                "resolution_guard",
            },
        )

    def test_the_reader_and_the_writer_share_one_key(self):
        """The two sites cannot name different keys again.

        The defect was exactly this drift: the writer stored `base_head`, the
        reader asked for `base_commit`, and no test compared the two names.
        The constant is pinned by value, the reader is pinned to consume the
        constant, and the dead literal is pinned absent.
        """
        _module = hexctl_module()
        self.assertEqual(self.sync_base_head_key(), "base_head")
        with open(HEXCTL, encoding="utf-8") as handle:
            source = handle.read()
        self.assertEqual(
            source.count("recorded_sync.get(SYNC_BASE_HEAD_KEY)"), 1)
        self.assertEqual(source.count("SYNC_BASE_HEAD_KEY: base_tip"), 1)
        self.assertNotIn('recorded_sync.get("base_commit")', source)

    def test_a_sync_receipt_missing_the_base_tip_reads_as_empty(self):
        """A receipt without the key keeps the older, stricter arithmetic."""
        key = self.sync_base_head_key()
        self.to_receipted_sync()
        self.edit_sync_receipt(lambda sync: sync.pop(key))
        proc = self.integrate(expect=2)
        self.assertIn("gained 3 history row(s)", proc.stderr)
        self.assertNotIn("after subtracting", proc.stderr)

    def test_a_malformed_base_tip_reads_as_empty(self):
        """A corrupt recorded tip subtracts nothing rather than guessing."""
        module = hexctl_module()
        key = self.sync_base_head_key()
        self.to_receipted_sync()
        self.edit_sync_receipt(
            lambda sync: sync.update({key: "not-a-sha"}))
        proc = self.integrate(expect=2)
        self.assertIn("gained 3 history row(s)", proc.stderr)
        self.assertNotIn("after subtracting", proc.stderr)
        # The read itself: None, malformed, and unfetchable all answer empty.
        for base in (None, "", "not-a-sha", "f" * 40):
            with self.subTest(base=base):
                self.assertEqual(
                    module.base_ledger_versions(
                        self.target, base, self.ledger_rel),
                    frozenset(),
                )


if __name__ == "__main__":  # pragma: no cover
    import unittest

    unittest.main()
