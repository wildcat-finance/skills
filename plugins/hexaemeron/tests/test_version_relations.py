"""Focused fixtures for Fiat's runbook version-relation anchor.

The relation changes when a version becomes concrete.  These tests hold the
earlier boundary: ``done runbook`` captures exact starting-commit evidence,
does not reserve a label, and leaves a literal-only run byte-compatible.
"""

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock

try:
    from plugins.hexaemeron.tests.test_hexctl import HexctlCase, hexctl_module
except ModuleNotFoundError:  # direct discovery from this directory
    from test_hexctl import HexctlCase, hexctl_module


RELATION = "next-generation-after-integration-base"
SCHEMA = "fiat-version-relations/v1"


def field_digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class VersionRelationTests(HexctlCase):
    def setUp(self):
        super().setUp()
        # These fixtures need the real object database.  HexctlCase's delivery
        # shim is for signature and GitHub topology tests and deliberately
        # replaces ordinary ``git show`` output.
        self.env["PATH"] = os.pathsep.join(self.env["PATH"].split(os.pathsep)[1:])

    def test_parser_admits_the_version_resolution_receipt(self):
        parser = hexctl_module().build_parser()
        args = parser.parse_args(
            ["--dir", self.dir, "done", "resolve-versions"]
        )
        self.assertEqual(args.phase, "resolve-versions")

    def _capture_chain_anchor(self, generations=(2,)):
        self.install_chain("fiat", list(generations))
        anchor_commit = self.commit_seed()
        module = hexctl_module()
        source = {
            "source_sha256": "a" * 64,
            "targets": [
                {
                    "skill": "fiat",
                    "ledger": self.ledger_path("fiat"),
                    "relation": RELATION,
                }
            ],
        }
        receipt = module.capture_version_relations(
            self.dir, source, anchor_commit
        )
        return module, anchor_commit, receipt["targets"][0]

    def _commit_chain(self, generations, message):
        self.install_chain("fiat", list(generations))
        self.git("add", "-A")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def test_resolution_accepts_zero_compatible_generation_drift(self):
        module, anchor_commit, anchor = self._capture_chain_anchor()
        head_commit = self._commit_chain((2, 3), "candidate generation")

        resolved = module.resolve_version_relation_target(
            self.dir, anchor_commit, anchor_commit, head_commit, anchor
        )

        self.assertEqual(resolved["base_version"], "fiat-v1.2.3")
        self.assertEqual(resolved["resolved_version"], "fiat-v1.3.3")
        self.assertEqual(resolved["skill_metadata_version"], "1.3.3")

    def test_resolution_accepts_one_compatible_generation_drift(self):
        module, anchor_commit, anchor = self._capture_chain_anchor()
        base_commit = self._commit_chain((2, 3), "concurrent generation")
        head_commit = self._commit_chain((2, 3, 4), "candidate generation")

        resolved = module.resolve_version_relation_target(
            self.dir, anchor_commit, base_commit, head_commit, anchor
        )

        self.assertEqual(resolved["base_version"], "fiat-v1.3.3")
        self.assertEqual(resolved["resolved_version"], "fiat-v1.4.3")

    def test_resolution_accepts_several_compatible_generations(self):
        module, anchor_commit, anchor = self._capture_chain_anchor()
        base_commit = self._commit_chain((2, 3, 4, 5), "three concurrent generations")
        head_commit = self._commit_chain((2, 3, 4, 5, 6), "candidate generation")

        resolved = module.resolve_version_relation_target(
            self.dir, anchor_commit, base_commit, head_commit, anchor
        )

        self.assertEqual(resolved["base_version"], "fiat-v1.5.3")
        self.assertEqual(resolved["resolved_version"], "fiat-v1.6.3")

    def test_resolution_accepts_the_maximum_representable_generation(self):
        module = hexctl_module()
        final_generation = module.VERSION_RELATION_COUNTER_MAX
        module, anchor_commit, anchor = self._capture_chain_anchor(
            (final_generation - 1,)
        )
        head_commit = self._commit_chain(
            (final_generation - 1, final_generation),
            "candidate maximum generation",
        )

        resolved = module.resolve_version_relation_target(
            self.dir, anchor_commit, anchor_commit, head_commit, anchor
        )

        self.assertEqual(
            resolved["resolved_version"],
            f"fiat-v1.{final_generation}.3",
        )

    def test_resolution_refuses_a_rewritten_base_history_prefix(self):
        module, anchor_commit, anchor = self._capture_chain_anchor()
        rewritten = self.chain_ledger("fiat", (2, 3)).replace(
            "fixture-0", "rewritten-evidence"
        )
        self.write(self.ledger_path("fiat"), rewritten)
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 3, 3)))
        self.git("add", "-A")
        self.git("commit", "-m", "rewrite history")
        base_commit = self.git("rev-parse", "HEAD").stdout.strip()
        head_commit = self._commit_chain((2, 3, 4), "candidate generation")

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.resolve_version_relation_target(
                self.dir, anchor_commit, base_commit, head_commit, anchor
            )
        self.assertIn("rewrites its required prefix", stderr.getvalue())

    def test_resolution_history_enforces_evolution_and_epoch_digest_rules(self):
        module = hexctl_module()
        unchanged = "a" * 64
        changed = "b" * 64
        baseline = (
            f"- `fiat-v1.1.3` | baseline | `held` | `{unchanged}` | "
            "fixture | Versioning starts here.\n"
        )
        invalid = (
            (
                baseline
                + f"- `fiat-v2.1.3` | evolution | `held` | `{unchanged}` | "
                "fixture | Frontier changed.\n"
            ),
            (
                baseline
                + f"- `fiat-v1.1.4` | epoch | `held` | `{changed}` | "
                "fixture | Tooling changed.\n"
            ),
        )

        for ledger in invalid:
            with self.subTest(ledger=ledger.splitlines()[-1]):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module._ledger_history_records(
                        "# fiat evolution ledger\n\n## History\n\n" + ledger,
                        "fiat",
                        "version resolution fixture",
                    )
                self.assertNotIn("fiat-v", stderr.getvalue())

    def test_each_non_generation_compatibility_field_blocks_resolution(self):
        module, _, anchor = self._capture_chain_anchor()
        snapshot = {
            "parts": (anchor["evolution"], anchor["generation"], anchor["epoch"]),
            "status": anchor["frontier_status"],
            "revision": anchor["frontier_revision"],
            "frontier_sha256": anchor["frontier_sha256"],
            "current_frontier_sha256": anchor["current_frontier_sha256"],
            "next_job_sha256": anchor["next_job_sha256"],
        }
        mutations = {
            "evolution": lambda value: {
                **value,
                "parts": (value["parts"][0] + 1, value["parts"][1], value["parts"][2]),
            },
            "epoch": lambda value: {
                **value,
                "parts": (value["parts"][0], value["parts"][1], value["parts"][2] + 1),
            },
            "frontier_status": lambda value: {**value, "status": "mature"},
            "frontier_revision": lambda value: {**value, "revision": "changed"},
            "frontier_sha256": lambda value: {**value, "frontier_sha256": "0" * 64},
            "current_frontier_sha256": lambda value: {
                **value,
                "current_frontier_sha256": "1" * 64,
            },
            "next_job_sha256": lambda value: {
                **value,
                "next_job_sha256": "2" * 64,
            },
        }
        for field, mutate in mutations.items():
            with self.subTest(field=field):
                self.assertEqual(
                    module.version_compatibility_fault(anchor, mutate(snapshot)),
                    field,
                )

    def test_resolution_refuses_candidate_metadata_without_the_row(self):
        module, anchor_commit, anchor = self._capture_chain_anchor()
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 3, 3)))
        self.git("add", "-A")
        self.git("commit", "-m", "metadata only")
        head_commit = self.git("rev-parse", "HEAD").stdout.strip()

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.resolve_version_relation_target(
                self.dir, anchor_commit, anchor_commit, head_commit, anchor
            )
        self.assertIn("metadata does not match its ledger", stderr.getvalue())

    def test_resolution_refuses_missing_and_oversized_candidate_objects(self):
        module, anchor_commit, anchor = self._capture_chain_anchor()
        os.unlink(os.path.join(self.dir, self.ledger_path("fiat")))
        self.git("add", "-A")
        self.git("commit", "-m", "remove candidate ledger")
        missing_head = self.git("rev-parse", "HEAD").stdout.strip()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.resolve_version_relation_target(
                self.dir, anchor_commit, anchor_commit, missing_head, anchor
            )
        self.assertIn("object is missing", stderr.getvalue())

        self.git("reset", "--hard", anchor_commit)
        oversized = os.path.join(self.dir, self.ledger_path("fiat"))
        with open(oversized, "wb") as handle:
            handle.write(b"x" * (2 * 1024 * 1024 + 1))
        self.git("add", "-A")
        self.git("commit", "-m", "oversized candidate ledger")
        oversized_head = self.git("rev-parse", "HEAD").stdout.strip()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.resolve_version_relation_target(
                self.dir, anchor_commit, anchor_commit, oversized_head, anchor
            )
        self.assertIn("byte cap", stderr.getvalue())

    def _relation_run_with_candidate(self, generations=(2, 3)):
        self.install_chain("fiat", (2,))
        anchor_commit = self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        self.install_chain("fiat", generations)
        self.git("add", "-A")
        self.git("commit", "-m", "candidate relation generation")
        head_commit = self.git("rev-parse", "HEAD").stdout.strip()
        return anchor_commit, head_commit, self.integrate_state(state, head_commit)

    def test_build_resolution_uses_one_stable_base_and_run_snapshot(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        with mock.patch.object(
            module,
            "remote_branch_tip",
            side_effect=[anchor_commit, head_commit, head_commit, anchor_commit],
        ) as remote:
            receipt = module.build_version_resolution(self.target, state)

        self.assertEqual(remote.call_count, 4)
        self.assertEqual(receipt["base_commit"], anchor_commit)
        self.assertEqual(receipt["head_commit"], head_commit)
        self.assertEqual(receipt["targets"][0]["resolved_version"], "fiat-v1.3.3")

    def test_build_resolution_refuses_a_base_ref_change_around_reads(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        with mock.patch.object(
            module,
            "remote_branch_tip",
            side_effect=[anchor_commit, head_commit, head_commit, "f" * 40],
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module.build_version_resolution(self.target, state)
        self.assertIn("remote refs changed", stderr.getvalue())

    def test_build_resolution_refuses_a_run_ref_change_around_reads(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        with mock.patch.object(
            module,
            "remote_branch_tip",
            side_effect=[anchor_commit, head_commit, "e" * 40, anchor_commit],
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module.build_version_resolution(self.target, state)
        self.assertIn("remote refs changed", stderr.getvalue())

    def test_resolution_remote_reads_ignore_inherited_git_repository(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        self.git("remote", "add", "origin", self.dir)

        with tempfile.TemporaryDirectory() as attacker:
            for argv in (
                ("init", "-q", "-b", "main"),
                ("config", "user.email", "attacker@example.invalid"),
                ("config", "user.name", "Attacker"),
                ("config", "commit.gpgsign", "false"),
                ("commit", "-q", "--allow-empty", "-m", "substitute remote"),
            ):
                subprocess.run(
                    ["git", *argv], cwd=attacker, check=True, capture_output=True
                )
            subprocess.run(
                ["git", "branch", state["run_branch"]],
                cwd=attacker,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "remote", "add", "origin", attacker],
                cwd=attacker,
                check=True,
                capture_output=True,
            )
            with mock.patch.dict(
                os.environ, {"GIT_DIR": os.path.join(attacker, ".git")}
            ):
                receipt = module.build_version_resolution(self.target, state)

        self.assertEqual(receipt["base_commit"], anchor_commit)
        self.assertEqual(receipt["head_commit"], head_commit)

    def test_555_collision_topology_requires_signed_sync_before_resolution(self):
        self.install_chain("fiat", (2,))
        anchor_commit = self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        original_branch = self.git("branch", "--show-current").stdout.strip()

        self.install_chain("fiat", (2, 3))
        self.git("add", "-A")
        self.git("commit", "-m", "product selects generation three")
        product_head = self.git("rev-parse", "HEAD").stdout.strip()
        state = self.integrate_state(state, product_head)

        self.git("checkout", "-b", "concurrent-base", anchor_commit)
        base_ledger = self.chain_ledger("fiat", (2, 3)).replace(
            "fixture-1", "concurrent-base-collision"
        )
        self.write(self.ledger_path("fiat"), base_ledger)
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 3, 3)))
        self.git("add", "-A")
        self.git("commit", "-m", "base independently selects generation three")
        concurrent_base = self.git("rev-parse", "HEAD").stdout.strip()

        self.git("checkout", original_branch)
        module = hexctl_module()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.build_version_resolution(
                self.target,
                state,
                exact_base=concurrent_base,
                exact_head=product_head,
            )
        self.assertIn("recorded signed sync", stderr.getvalue())
        self.assertNotIn(anchor_commit, stderr.getvalue())

        self.git("merge", "--no-ff", "--no-commit", concurrent_base, expect=1)
        corrected = self.chain_ledger("fiat", (2, 3, 4)).replace(
            "fixture-1", "concurrent-base-collision"
        ).replace("fixture-2", "signed-sync-correction")
        self.write(self.ledger_path("fiat"), corrected)
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 4, 3)))
        self.git("add", "-A")
        self.git("commit", "-m", "sync resolves collision at generation four")
        sync_head = self.git("rev-parse", "HEAD").stdout.strip()
        target_paths = sorted(
            [self.ledger_path("fiat"), self.skill_path("fiat")]
        )
        state["integrate"]["sync"] = {
            "commit": sync_head,
            "base": "main",
            "starting_base": state["base"],
            "base_head": concurrent_base,
            "parents": [product_head, concurrent_base],
            "github_verified": [sync_head],
            "product_evidence": module.product_evidence_record(
                state, product_head
            ),
            "revalidation": {
                "schema": module.INTEGRATION_REVALIDATION_SCHEMA,
                "affected_paths": target_paths,
                "checks": [
                    {
                        "id": "collision-versions",
                        "command": "python3 -m unittest",
                        "paths": target_paths,
                        "exit": 0,
                    }
                ],
            },
        }
        with mock.patch.object(
            module, "verify_local_commit", return_value=sync_head
        ):
            receipt = module.build_version_resolution(
                self.target,
                state,
                exact_base=concurrent_base,
                exact_head=sync_head,
            )
        self.assertEqual(receipt["targets"][0]["base_version"], "fiat-v1.3.3")
        self.assertEqual(
            receipt["targets"][0]["resolved_version"], "fiat-v1.4.3"
        )

    def test_literal_only_run_cannot_manufacture_a_resolution_receipt(self):
        self.commit_seed()
        _, state = self.receipt_runbook()
        state = self.integrate_state(state, "a" * 40)
        module = hexctl_module()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.build_version_resolution(
                self.target,
                state,
                exact_base="b" * 40,
                exact_head="a" * 40,
            )
        self.assertIn("declares no version relation", stderr.getvalue())

    def _persistable_resolution(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        receipt = module.build_version_resolution(
            self.target,
            state,
            exact_base=anchor_commit,
            exact_head=head_commit,
        )
        module.commit(
            self.target,
            state,
            "fixture:integrate",
            {"head": head_commit},
        )
        return module, state, receipt

    def test_done_resolve_versions_records_one_atomic_event_without_product_edit(self):
        module, state, receipt = self._persistable_resolution()
        before_head = self.git("rev-parse", "HEAD").stdout.strip()
        before_status = self.git("status", "--short").stdout
        with mock.patch.object(
            module, "build_version_resolution", return_value=receipt
        ):
            module.done_resolve_versions(SimpleNamespace(dir=self.target), state)

        recorded = self.state()["integrate"]["version_resolutions"]
        self.assertEqual(recorded, [receipt])
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), before_head)
        self.assertEqual(self.git("status", "--short").stdout, before_status)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            events = [json.loads(line) for line in handle if line.strip()]
        resolution_events = [
            event for event in events if event["event"] == "done:version-resolution"
        ]
        self.assertEqual(
            [event["data"] for event in resolution_events],
            [module.version_resolution_event(receipt)],
        )
        self.assertFalse(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )
        module.verify_run(self.target)

    def test_exact_resolution_retry_is_idempotent(self):
        module, state, receipt = self._persistable_resolution()
        with mock.patch.object(
            module, "build_version_resolution", return_value=receipt
        ):
            module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
            current = self.state()
            before = self.read_bytes(
                os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
            )
            module.done_resolve_versions(SimpleNamespace(dir=self.target), current)
            after = self.read_bytes(
                os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
            )
        self.assertEqual(before, after)
        self.assertEqual(len(self.state()["integrate"]["version_resolutions"]), 1)

    def test_resolution_history_retains_eight_and_refuses_a_ninth(self):
        module, state, receipt = self._persistable_resolution()
        history = []
        for index in range(8):
            item = json.loads(json.dumps(receipt))
            item["base_commit"] = f"{index + 1:040x}"
            item["head_commit"] = f"{index + 101:040x}"
            item["ts"] = f"2026-08-25T00:00:0{index}+00:00"
            history.append(item)
        state["integrate"]["version_resolutions"] = history
        module.validate_version_resolution_history(
            history, "fixture.version_resolutions"
        )
        ninth = json.loads(json.dumps(receipt))
        ninth["base_commit"] = "f" * 40
        ninth["head_commit"] = "e" * 40
        ninth["ts"] = "2026-08-25T00:01:00+00:00"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module._state_with_resolution(state, ninth)
        self.assertIn("exceeds its item cap", stderr.getvalue())
        self.assertEqual(len(state["integrate"]["version_resolutions"]), 8)

    def _resolution_marker(self, module, state, receipt):
        candidate = module._state_with_resolution(state, receipt)
        marker = {
            "schema": module.VERSION_RESOLUTION_PENDING_SCHEMA,
            "subject": "version-resolution",
            "state_before_sha256": module.state_fingerprint(state),
            "state_after_sha256": module.state_fingerprint(candidate),
            "ledger_head": module._intact_ledger_entries(
                self.target, "fixture"
            )[-1]["hash"],
            "receipt_sha256": hashlib.sha256(
                module.canonical(receipt).encode()
            ).hexdigest(),
            "receipt": receipt,
        }
        return candidate, marker

    def _resolution_event_count(self):
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            return sum(
                1
                for line in handle
                if line.strip()
                and json.loads(line)["event"] == "done:version-resolution"
            )

    def test_pending_write_failure_leaves_state_and_ledger_unchanged(self):
        module, state, receipt = self._persistable_resolution()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        before_state = self.read_bytes(state_path)
        before_ledger = self.read_bytes(ledger_path)
        with (
            mock.patch.object(
                module, "build_version_resolution", return_value=receipt
            ),
            mock.patch.object(
                module,
                "write_version_resolution_pending",
                side_effect=OSError("interrupted before pending replacement"),
            ),
        ):
            with self.assertRaises(OSError):
                module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
        self.assertEqual(self.read_bytes(state_path), before_state)
        self.assertEqual(self.read_bytes(ledger_path), before_ledger)
        self.assertFalse(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )

    def test_interruption_after_pending_marker_retries_once(self):
        module, state, receipt = self._persistable_resolution()
        original_append = module.append_ledger
        with (
            mock.patch.object(
                module, "build_version_resolution", return_value=receipt
            ),
            mock.patch.object(
                module,
                "append_ledger",
                side_effect=KeyboardInterrupt("after pending marker"),
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
        self.assertTrue(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )
        with (
            mock.patch.object(
                module, "build_version_resolution", return_value=receipt
            ),
            mock.patch.object(module, "append_ledger", side_effect=original_append),
        ):
            module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
        self.assertEqual(self._resolution_event_count(), 1)
        module.verify_run(self.target)

    def test_interruption_after_ledger_event_retries_once(self):
        module, state, receipt = self._persistable_resolution()
        with (
            mock.patch.object(
                module, "build_version_resolution", return_value=receipt
            ),
            mock.patch.object(
                module,
                "save_state",
                side_effect=KeyboardInterrupt("after ledger event"),
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
        self.assertEqual(self._resolution_event_count(), 1)
        with mock.patch.object(
            module, "build_version_resolution", return_value=receipt
        ):
            module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
        self.assertEqual(self._resolution_event_count(), 1)
        self.assertEqual(self.state()["integrate"]["version_resolutions"], [receipt])
        module.verify_run(self.target)

    def test_interruption_after_state_replacement_clears_once(self):
        module, state, receipt = self._persistable_resolution()
        with (
            mock.patch.object(
                module, "build_version_resolution", return_value=receipt
            ),
            mock.patch.object(
                module,
                "clear_version_resolution_pending",
                side_effect=KeyboardInterrupt("before pending clear"),
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
        persisted = module.load_state(
            self.target, allow_pending_resolution=True
        )
        self.assertEqual(persisted["integrate"]["version_resolutions"], [receipt])
        with mock.patch.object(
            module, "build_version_resolution", return_value=receipt
        ):
            module.done_resolve_versions(
                SimpleNamespace(dir=self.target), persisted
            )
        self.assertEqual(self._resolution_event_count(), 1)
        self.assertFalse(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )
        module.verify_run(self.target)

    def test_pending_resolution_before_ledger_rolls_back_once(self):
        module, state, receipt = self._persistable_resolution()
        _, marker = self._resolution_marker(module, state, receipt)
        module.write_version_resolution_pending(self.target, marker)

        recovered_state, completed = module.recover_version_resolution(
            self.target, state, marker, receipt
        )

        self.assertFalse(completed)
        self.assertEqual(recovered_state, state)
        self.assertFalse(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )
        module.verify_run(self.target)

    def test_pending_resolution_loads_the_maximum_target_shape(self):
        module, state, receipt = self._persistable_resolution()
        counter = int("1" * module.VERSION_RELATION_COUNTER_DIGITS_MAX)
        targets = []
        for index in range(module.VERSION_RELATIONS_MAX):
            skill = f"s{index:02d}" + "a" * 1008
            ledger = f"{skill}/EVOLUTION.md"
            target = json.loads(json.dumps(receipt["targets"][0]))
            target.update(
                {
                    "skill": skill,
                    "ledger": ledger,
                    "anchor_version": f"{skill}-v{counter}.{counter}.{counter}",
                    "base_version": f"{skill}-v{counter}.{counter}.{counter}",
                    "resolved_version": f"{skill}-v{counter}.{counter + 1}.{counter}",
                    "skill_metadata_version": f"{counter}.{counter + 1}.{counter}",
                }
            )
            targets.append(target)
        receipt["targets"] = targets
        module.validate_version_resolution_shape(receipt, "fixture.max_resolution")
        _, marker = self._resolution_marker(module, state, receipt)
        encoded = (
            json.dumps(marker, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        self.assertGreater(len(encoded), 131072)
        self.assertEqual(len(receipt["targets"][0]["ledger"].encode("utf-8")), 1024)

        module.write_version_resolution_pending(self.target, marker)

        self.assertEqual(
            module.load_version_resolution_pending(self.target), marker
        )

    def test_pending_resolution_after_ledger_completes_state_once(self):
        module, state, receipt = self._persistable_resolution()
        candidate, marker = self._resolution_marker(module, state, receipt)
        module.write_version_resolution_pending(self.target, marker)
        module.append_ledger(
            self.target,
            "done:version-resolution",
            module.version_resolution_event(receipt),
            marker["state_after_sha256"],
        )

        recovered_state, completed = module.recover_version_resolution(
            self.target, state, marker, receipt
        )

        self.assertTrue(completed)
        self.assertEqual(recovered_state, candidate)
        self.assertEqual(
            self.state()["integrate"]["version_resolutions"], [receipt]
        )
        module.verify_run(self.target)

    def test_pending_resolution_after_state_only_clears_the_marker(self):
        module, state, receipt = self._persistable_resolution()
        candidate, marker = self._resolution_marker(module, state, receipt)
        module.write_version_resolution_pending(self.target, marker)
        module.append_ledger(
            self.target,
            "done:version-resolution",
            module.version_resolution_event(receipt),
            marker["state_after_sha256"],
        )
        module.save_state(self.target, candidate)

        recovered_state, completed = module.recover_version_resolution(
            self.target, candidate, marker, receipt
        )

        self.assertTrue(completed)
        self.assertEqual(recovered_state, candidate)
        self.assertFalse(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )
        module.verify_run(self.target)

    def test_pending_resolution_refuses_an_unrelated_ledger_tail(self):
        module, state, receipt = self._persistable_resolution()
        _, marker = self._resolution_marker(module, state, receipt)
        module.write_version_resolution_pending(self.target, marker)
        module.append_ledger(
            self.target,
            "unrelated:event",
            {"bounded": True},
            marker["state_before_sha256"],
        )

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.recover_version_resolution(self.target, state, marker, receipt)
        self.assertIn("unrelated transition", stderr.getvalue())
        self.assertTrue(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )

    def test_pending_resolution_refuses_changed_evidence(self):
        module, state, receipt = self._persistable_resolution()
        _, marker = self._resolution_marker(module, state, receipt)
        module.write_version_resolution_pending(self.target, marker)
        changed = json.loads(json.dumps(receipt))
        changed["head_commit"] = "f" * 40

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.recover_version_resolution(self.target, state, marker, changed)
        self.assertIn("stale base, head, or target", stderr.getvalue())
        self.assertTrue(
            os.path.exists(module.version_resolution_pending_path(self.target))
        )

    def test_resolution_state_and_ledger_shapes_are_closed_and_joined(self):
        module, state, receipt = self._persistable_resolution()
        malformed = json.loads(json.dumps(receipt))
        malformed["targets"][0].pop("row_sha256")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.validate_version_resolution_shape(
                malformed, "fixture.version_resolution"
            )
        self.assertIn("unsupported field set", stderr.getvalue())

        with mock.patch.object(
            module, "build_version_resolution", return_value=receipt
        ):
            module.done_resolve_versions(SimpleNamespace(dir=self.target), state)
        ledger_file = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_file, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        entries[-1]["data"]["head_commit"] = "f" * 40
        entries[-1]["hash"] = hashlib.sha256(
            module.canonical(
                {
                    "ts": entries[-1]["ts"],
                    "event": entries[-1]["event"],
                    "data": entries[-1]["data"],
                    "prev": entries[-1]["prev"],
                    "state": entries[-1]["state"],
                }
            ).encode()
        ).hexdigest()
        with open(ledger_file, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.verify_run(self.target)
        self.assertIn("does not match", stderr.getvalue())

    def _terminal_resolution_fixture(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        receipt = module.build_version_resolution(
            self.target,
            state,
            exact_base=anchor_commit,
            exact_head=head_commit,
        )
        state["integrate"]["version_resolutions"] = [receipt]
        subprocess.run(
            ["git", "merge", "--no-ff", "-m", "integration fixture", head_commit],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        merge_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return module, state, receipt, merge_commit

    def test_terminal_resolution_replays_exact_base_candidate_parents(self):
        module, state, receipt, merge_commit = self._terminal_resolution_fixture()
        with mock.patch.object(
            module, "remote_branch_tip", return_value=merge_commit
        ):
            replayed = module.terminal_version_resolution(
                self.target, state, merge_commit
            )
        self.assertEqual(replayed, receipt)

    def test_terminal_resolution_refuses_wrong_parent_order(self):
        module, state, receipt, merge_commit = self._terminal_resolution_fixture()
        with mock.patch.object(
            module,
            "_native_relation_parents",
            return_value=[receipt["head_commit"], receipt["base_commit"]],
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module.terminal_version_resolution(self.target, state, merge_commit)
        self.assertIn("[base, candidate]", stderr.getvalue())

    def test_terminal_parent_replay_ignores_git_replacement_objects(self):
        module, state, receipt, merge_commit = self._terminal_resolution_fixture()
        tree = self.git("rev-parse", f"{merge_commit}^{{tree}}").stdout.strip()
        replacement = self.git(
            "commit-tree",
            tree,
            "-m",
            "replacement parent order",
            "-p",
            receipt["head_commit"],
            "-p",
            receipt["base_commit"],
        ).stdout.strip()
        self.git("replace", merge_commit, replacement)
        self.assertEqual(
            self.git("show", "-s", "--format=%P", merge_commit).stdout.strip(),
            f"{receipt['head_commit']} {receipt['base_commit']}",
        )
        with mock.patch.object(
            module, "remote_branch_tip", return_value=merge_commit
        ):
            replayed = module.terminal_version_resolution(
                self.target, state, merge_commit
            )
        self.assertEqual(replayed, receipt)

    def test_terminal_resolution_refuses_a_post_check_base_move(self):
        module, state, _, merge_commit = self._terminal_resolution_fixture()
        with mock.patch.object(
            module, "remote_branch_tip", return_value="f" * 40
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module.terminal_version_resolution(self.target, state, merge_commit)
        self.assertIn("base branch moved again", stderr.getvalue())

    def test_next_withholds_integration_until_a_resolution_exists(self):
        _, _, state = self._relation_run_with_candidate()
        module = hexctl_module()

        directive = module._integrate_directive(state, self.target)

        self.assertEqual(directive["do"], "resolve-versions")
        self.assertEqual(directive["then"], "hexctl done resolve-versions")

    def test_next_carries_only_the_active_current_resolution(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        receipt = module.build_version_resolution(
            self.target,
            state,
            exact_base=anchor_commit,
            exact_head=head_commit,
        )
        state["integrate"]["version_resolutions"] = [receipt]
        with mock.patch.object(
            module, "active_version_resolution", return_value=receipt
        ):
            directive = module._integrate_directive(state, self.target)

        self.assertEqual(directive["do"], "integrate")
        self.assertEqual(directive["version_resolution"], receipt)

    def test_active_resolution_refuses_stale_head_evidence(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        receipt = module.build_version_resolution(
            self.target,
            state,
            exact_base=anchor_commit,
            exact_head=head_commit,
        )
        state["integrate"]["version_resolutions"] = [receipt]
        changed = json.loads(json.dumps(receipt))
        changed["head_commit"] = "f" * 40
        with mock.patch.object(
            module, "build_version_resolution", return_value=changed
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module.active_version_resolution(self.target, state)
        self.assertIn("stale", stderr.getvalue())

    def test_status_distinguishes_active_stale_and_terminal_resolution(self):
        anchor_commit, head_commit, state = self._relation_run_with_candidate()
        module = hexctl_module()
        receipt = module.build_version_resolution(
            self.target,
            state,
            exact_base=anchor_commit,
            exact_head=head_commit,
        )
        state["integrate"]["version_resolutions"] = [receipt]
        module.save_state(self.target, state)

        with mock.patch.object(
            module, "active_version_resolution", return_value=receipt
        ):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                module.cmd_status(SimpleNamespace(dir=self.target, json=True))
        status = json.loads(stdout.getvalue())["version_resolution_status"]
        self.assertEqual(status["status"], "active")
        self.assertEqual(status["history"], 1)

        def stale(*_args, **_kwargs):
            module.die("the active version resolution is stale for the current head")

        with mock.patch.object(module, "active_version_resolution", side_effect=stale):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                module.cmd_status(SimpleNamespace(dir=self.target, json=True))
        status = json.loads(stdout.getvalue())["version_resolution_status"]
        self.assertEqual(status["status"], "stale")
        self.assertIn("current head", status["reason"])

        state["phase"] = "done"
        state["receipts"]["integrate"] = {"version_resolution": receipt}
        module.save_state(self.target, state)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            module.cmd_status(SimpleNamespace(dir=self.target, json=True))
        status = json.loads(stdout.getvalue())["version_resolution_status"]
        self.assertEqual(status["status"], "terminal")

    def _sync_evidence_fixture(self):
        _, product_head, state = self._relation_run_with_candidate()
        module = hexctl_module()
        base_commit = "b" * 40
        sync_head = "c" * 40
        relation = state["receipts"]["runbook"]["version_relations"]
        ledger = self.ledger_path("fiat")
        skill = self.skill_path("fiat")
        sync = {
            "commit": sync_head,
            "base": "main",
            "starting_base": state["base"],
            "base_head": base_commit,
            "parents": [product_head, base_commit],
            "github_verified": [sync_head],
            "product_evidence": module.product_evidence_record(
                state, product_head
            ),
            "revalidation": {
                "schema": module.INTEGRATION_REVALIDATION_SCHEMA,
                "affected_paths": sorted([ledger, skill]),
                "checks": [
                    {
                        "id": "versions",
                        "command": "python3 -m unittest",
                        "paths": sorted([ledger, skill]),
                        "exit": 0,
                    }
                ],
            },
        }
        return module, state, relation, sync, product_head, base_commit, sync_head

    def test_resolution_accepts_only_a_signed_covered_product_base_sync(self):
        (
            module,
            state,
            relation,
            sync,
            product_head,
            base_commit,
            sync_head,
        ) = self._sync_evidence_fixture()
        paths = sorted([self.ledger_path("fiat"), self.skill_path("fiat")])
        with (
            mock.patch.object(
                module,
                "_native_relation_parents",
                return_value=[product_head, base_commit],
            ),
            mock.patch.object(module, "verify_local_commit", return_value=sync_head),
            mock.patch.object(
                module, "_native_relation_diff_paths", return_value=paths
            ),
        ):
            module._require_resolution_sync(
                self.target,
                state,
                sync,
                product_head,
                base_commit,
                sync_head,
                relation,
            )

    def test_resolution_sync_refuses_parent_and_signature_faults(self):
        (
            module,
            state,
            relation,
            sync,
            product_head,
            base_commit,
            sync_head,
        ) = self._sync_evidence_fixture()
        wrong_head = json.loads(json.dumps(sync))
        wrong_head["commit"] = "d" * 40
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module._require_resolution_sync(
                self.target,
                state,
                wrong_head,
                product_head,
                base_commit,
                sync_head,
                relation,
            )
        self.assertIn("stale or malformed", stderr.getvalue())

        with mock.patch.object(
            module,
            "_native_relation_parents",
            return_value=[base_commit, product_head],
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module._require_resolution_sync(
                    self.target,
                    state,
                    sync,
                    product_head,
                    base_commit,
                    sync_head,
                    relation,
                )
        self.assertIn("sync parents", stderr.getvalue())

        with (
            mock.patch.object(
                module,
                "_native_relation_parents",
                return_value=[product_head, base_commit],
            ),
            mock.patch.object(module, "verify_local_commit", side_effect=SystemExit(2)),
        ):
            with self.assertRaises(SystemExit):
                module._require_resolution_sync(
                    self.target,
                    state,
                    sync,
                    product_head,
                    base_commit,
                    sync_head,
                    relation,
                )

    def test_resolution_sync_refuses_missing_path_or_green_check_coverage(self):
        (
            module,
            state,
            relation,
            sync,
            product_head,
            base_commit,
            sync_head,
        ) = self._sync_evidence_fixture()
        paths = sorted([self.ledger_path("fiat"), self.skill_path("fiat")])
        sync["revalidation"]["affected_paths"] = [self.ledger_path("fiat")]
        with (
            mock.patch.object(
                module,
                "_native_relation_parents",
                return_value=[product_head, base_commit],
            ),
            mock.patch.object(module, "verify_local_commit", return_value=sync_head),
            mock.patch.object(
                module, "_native_relation_diff_paths", return_value=paths
            ),
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module._require_resolution_sync(
                    self.target,
                    state,
                    sync,
                    product_head,
                    base_commit,
                    sync_head,
                    relation,
                )
        self.assertIn("omits a changed target path", stderr.getvalue())

        sync["revalidation"]["affected_paths"] = paths
        sync["revalidation"]["checks"][0]["exit"] = 1
        with (
            mock.patch.object(
                module,
                "_native_relation_parents",
                return_value=[product_head, base_commit],
            ),
            mock.patch.object(module, "verify_local_commit", return_value=sync_head),
            mock.patch.object(
                module, "_native_relation_diff_paths", return_value=paths
            ),
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                module._require_resolution_sync(
                    self.target,
                    state,
                    sync,
                    product_head,
                    base_commit,
                    sync_head,
                    relation,
                )
        self.assertIn("failed or malformed check", stderr.getvalue())

    def test_two_target_resolution_is_all_or_nothing_and_skill_sorted(self):
        self.install_chain("fiat", (2,))
        self.install_chain("protasis", (7,), evolution=4, epoch=0)
        anchor_commit = self.commit_seed()
        _, state = self.receipt_runbook(
            block=self.relation_block("protasis", "fiat")
        )
        self.install_chain("fiat", (2, 3))
        self.git("add", "-A")
        self.git("commit", "-m", "only one target advanced")
        partial_head = self.git("rev-parse", "HEAD").stdout.strip()
        partial_state = self.integrate_state(state, partial_head)
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        before_state = self.read_bytes(state_path)
        before_ledger = self.read_bytes(ledger_path)
        module = hexctl_module()

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.build_version_resolution(
                self.target,
                partial_state,
                exact_base=anchor_commit,
                exact_head=partial_head,
            )
        self.assertIn("exactly one target history row", stderr.getvalue())
        self.assertEqual(self.read_bytes(state_path), before_state)
        self.assertEqual(self.read_bytes(ledger_path), before_ledger)

        self.install_chain("protasis", (7, 8), evolution=4, epoch=0)
        self.git("add", "-A")
        self.git("commit", "-m", "second target advanced")
        complete_head = self.git("rev-parse", "HEAD").stdout.strip()
        complete_state = self.integrate_state(state, complete_head)
        receipt = module.build_version_resolution(
            self.target,
            complete_state,
            exact_base=anchor_commit,
            exact_head=complete_head,
        )
        self.assertEqual(
            [target["skill"] for target in receipt["targets"]],
            ["fiat", "protasis"],
        )

    @staticmethod
    def ledger_path(skill):
        return f"plugins/hexaemeron/skills/{skill}/EVOLUTION.md"

    @staticmethod
    def skill_path(skill):
        return f"plugins/hexaemeron/skills/{skill}/SKILL.md"

    @staticmethod
    def read_bytes(path):
        with open(path, "rb") as handle:
            return handle.read()

    @staticmethod
    def ledger(
        skill,
        version=(1, 2, 3),
        *,
        status="open",
        revision="held-frontier",
        frontier="The held frontier remains exact.",
        job="Complete the held job.",
    ):
        label = f"{skill}-v{version[0]}.{version[1]}.{version[2]}"
        digest = hashlib.sha256(
            f"{status}|{revision}|{frontier}|{job}\n".encode("utf-8")
        ).hexdigest()
        return (
            f"# {skill} evolution ledger\n\n"
            f"- Current version: `{label}`\n"
            f"- Frontier status: `{status}`\n"
            f"- Frontier revision: `{revision}`\n"
            f"- Current frontier: {frontier}\n"
            f"- Next Fiat job: {job}\n\n"
            "## History\n\n"
            f"- `{label}` | baseline | `{revision}` | `{digest}` | "
            "fixture | Versioning starts here.\n"
        )

    @staticmethod
    def skill(skill, version=(1, 2, 3)):
        number = ".".join(str(part) for part in version)
        return (
            "---\n"
            f"name: {skill}\n"
            "description: Fixture governed skill.\n"
            "metadata:\n"
            f"  version: \"{number}\"\n"
            "---\n\n"
            f"# {skill}\n"
        )

    @classmethod
    def chain_ledger(
        cls,
        skill,
        generations,
        *,
        evolution=1,
        epoch=3,
        status="open",
        revision="held-frontier",
        frontier="The held frontier remains exact.",
        job="Complete the held job.",
    ):
        digest = hashlib.sha256(
            f"{status}|{revision}|{frontier}|{job}\n".encode("utf-8")
        ).hexdigest()
        labels = [
            f"{skill}-v{evolution}.{generation}.{epoch}"
            for generation in generations
        ]
        rows = []
        for index, label in enumerate(labels):
            axis = "baseline" if index == 0 else "generation"
            rows.append(
                f"- `{label}` | {axis} | `{revision}` | `{digest}` | "
                f"fixture-{index} | generation {index}.\n"
            )
        return (
            f"# {skill} evolution ledger\n\n"
            f"- Current version: `{labels[-1]}`\n"
            f"- Frontier status: `{status}`\n"
            f"- Frontier revision: `{revision}`\n"
            f"- Current frontier: {frontier}\n"
            f"- Next Fiat job: {job}\n\n"
            "## History\n\n"
            + "".join(rows)
        )

    def install_chain(self, skill, generations, **fields):
        self.write(
            self.ledger_path(skill),
            self.chain_ledger(skill, generations, **fields),
        )
        self.write(
            self.skill_path(skill),
            self.skill(skill, (fields.get("evolution", 1), generations[-1], fields.get("epoch", 3))),
        )

    @staticmethod
    def integrate_state(state, head):
        state = json.loads(json.dumps(state))
        state["phase"] = "integrate"
        state["current_step"] = None
        for step in state["steps"]:
            step["status"] = "done"
            step["phase"] = "done"
        state["integrate"] = {
            "merged": [step["n"] for step in state["steps"]],
            "merges": {
                str(state["steps"][-1]["n"]): {
                    "merge_commit": head,
                }
            },
        }
        return state

    def install_target(self, skill, version=(1, 2, 3), **ledger_fields):
        self.write(self.ledger_path(skill), self.ledger(skill, version, **ledger_fields))
        self.write(self.skill_path(skill), self.skill(skill, version))

    def commit_seed(self):
        self.git("add", "-A")
        self.git("commit", "-m", "seed governed skills")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def hash_object(self, text):
        result = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=self.target,
            input=text,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    @staticmethod
    def relation_block(*skills):
        rows = [
            f"{skill} | plugins/hexaemeron/skills/{skill}/EVOLUTION.md | {RELATION}"
            for skill in skills
        ]
        return "```version-relations\n" + "\n".join(rows) + "\n```\n"

    def receipt_runbook(self, *skills, block=None, study_text="# Study\n"):
        self.init()
        study = self.write("study.md", study_text)
        self.run_ctl("done", "study", "--artifact", study)
        if block is None:
            block = self.relation_block(*skills) if skills else ""
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + block
            + "\n## Step 1: Build\n\n**Goal.** Build the fixture.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        return result, self.state()

    def receipt(self, state):
        return state["receipts"]["runbook"]["version_relations"]

    def assert_unchanged_after_refusal(self, before_state, before_ledger):
        with open(
            os.path.join(self.target, ".hexaemeron", "state.json"),
            encoding="utf-8",
        ) as handle:
            self.assertEqual(json.load(handle), before_state)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            self.assertEqual(handle.read(), before_ledger)

    def test_one_target_captures_every_anchor_field_without_reserving(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        relation = self.receipt(state)

        self.assertEqual(relation["schema"], SCHEMA)
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(
            relation["source_sha256"],
            hashlib.sha256(self.relation_block("fiat").encode()).hexdigest(),
        )
        self.assertNotIn("reserved", json.dumps(relation).lower())
        self.assertEqual(len(relation["targets"]), 1)
        target = relation["targets"][0]
        self.assertEqual(
            target,
            {
                "skill": "fiat",
                "ledger": self.ledger_path("fiat"),
                "relation": RELATION,
                "anchor_version": "fiat-v1.2.3",
                "evolution": 1,
                "generation": 2,
                "epoch": 3,
                "frontier_status": "open",
                "frontier_revision": "held-frontier",
                "frontier_sha256": hashlib.sha256(
                    (
                        "open|held-frontier|The held frontier remains exact.|"
                        "Complete the held job.\n"
                    ).encode()
                ).hexdigest(),
                "current_frontier_sha256": field_digest(
                    "The held frontier remains exact."
                ),
                "next_job_sha256": field_digest("Complete the held job."),
                "ledger_sha256": hashlib.sha256(
                    self.ledger("fiat").encode()
                ).hexdigest(),
                "skill_sha256": hashlib.sha256(self.skill("fiat").encode()).hexdigest(),
                "skill_metadata_version": "1.2.3",
            },
        )

    def test_two_targets_are_atomic_and_sorted_not_source_ordered(self):
        self.install_target("fiat")
        self.install_target("protasis", (4, 7, 0))
        self.commit_seed()
        _, state = self.receipt_runbook(
            block=self.relation_block("protasis", "fiat")
        )
        self.assertEqual(
            [target["skill"] for target in self.receipt(state)["targets"]],
            ["fiat", "protasis"],
        )

    def test_partial_target_coverage_captures_only_the_declared_skill(self):
        self.install_target("fiat")
        self.install_target("protasis", (4, 7, 0))
        self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        self.assertEqual(
            [target["skill"] for target in self.receipt(state)["targets"]],
            ["fiat"],
        )

    def test_starting_commit_wins_over_later_worktree_and_ref_drift(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()

        self.write(self.ledger_path("fiat"), self.ledger("fiat", (1, 9, 3)))
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 9, 3)))
        self.git("add", "-A")
        self.git("commit", "-m", "move run worktree")

        with open(os.path.join(self.dir, "base-drift.txt"), "w", encoding="utf-8") as handle:
            handle.write("main moved\n")
        subprocess.run(
            ["git", "add", "base-drift.txt"], cwd=self.dir, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "move base ref"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_base_rewind_cannot_move_anchor_before_the_run_start(self):
        self.install_target("fiat", (1, 1, 3))
        older = self.commit_seed()
        self.write(self.ledger_path("fiat"), self.ledger("fiat", (1, 2, 3)))
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 2, 3)))
        self.commit_seed()
        self.init()

        subprocess.run(
            ["git", "reset", "--hard", older],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done",
            "runbook",
            "--artifact",
            runbook,
            "--steps-file",
            steps,
            expect=2,
        )
        self.assertIn("init starting commit", result.stderr)
        self.assertNotIn(older, result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_run_branch_recreation_cannot_replace_the_init_anchor(self):
        self.install_target("fiat")
        original = self.commit_seed()
        self.init()
        run_branch = self.state()["run_branch"]

        origin_ledger = os.path.join(self.dir, self.ledger_path("fiat"))
        origin_skill = os.path.join(self.dir, self.skill_path("fiat"))
        with open(origin_ledger, "w", encoding="utf-8") as handle:
            handle.write(self.ledger("fiat", (9, 9, 9)))
        with open(origin_skill, "w", encoding="utf-8") as handle:
            handle.write(self.skill("fiat", (9, 9, 9)))
        subprocess.run(
            ["git", "add", "-A"], cwd=self.dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "move the integration base"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        moved = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Deleting and recreating the checked-out ref replaces its branch
        # reflog without touching the linked worktree's controller state.
        subprocess.run(
            ["git", "update-ref", "-d", f"refs/heads/{run_branch}"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "update-ref",
                "--create-reflog",
                f"refs/heads/{run_branch}",
                moved,
            ],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done",
            "runbook",
            "--artifact",
            runbook,
            "--steps-file",
            steps,
            expect=2,
        )
        self.assertIn("init starting commit", result.stderr)
        self.assertNotIn(original, result.stderr)
        self.assertNotIn(moved, result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_relation_anchor_does_not_require_native_reflogs(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        subprocess.run(
            ["git", "config", "core.logAllRefUpdates", "false"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        _, state = self.receipt_runbook("fiat")

        relation = self.receipt(state)
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_sha256_repository_anchor_replays_across_packets_and_verify(self):
        controller = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "skills",
                "fiat",
                "scripts",
                "hexctl.py",
            )
        )
        with tempfile.TemporaryDirectory() as repository:
            for argv in (
                ("init", "-q", "--object-format=sha256", "-b", "main"),
                ("config", "user.email", "fixture@example.invalid"),
                ("config", "user.name", "Fixture"),
                ("config", "commit.gpgsign", "false"),
            ):
                subprocess.run(
                    ["git", *argv],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                )
            ledger = os.path.join(repository, self.ledger_path("fiat"))
            skill = os.path.join(repository, self.skill_path("fiat"))
            os.makedirs(os.path.dirname(ledger), exist_ok=True)
            with open(ledger, "w", encoding="utf-8") as handle:
                handle.write(self.ledger("fiat"))
            with open(skill, "w", encoding="utf-8") as handle:
                handle.write(self.skill("fiat"))
            for argv in (("add", "-A"), ("commit", "-q", "-m", "seed")):
                subprocess.run(
                    ["git", *argv],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                )
            anchor = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(len(anchor), 64)

            def control(directory, *argv):
                result = subprocess.run(
                    [sys.executable, controller, "--dir", directory, *argv],
                    cwd=directory,
                    env=self.env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return result

            control(repository, "init", "--topic", "sha256 relation")
            with open(
                os.path.join(repository, ".hexaemeron", "worktree"),
                encoding="utf-8",
            ) as handle:
                worktree = handle.read().strip()
            with open(
                os.path.join(worktree, "study.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write("# Study\n")
            control(worktree, "done", "study", "--artifact", "study.md")
            with open(
                os.path.join(worktree, "runbook.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write(
                    "# Runbook\n\n"
                    + self.relation_block("fiat")
                    + "\n## Step 1: Build\n\n**Goal.** Build.\n"
                )
            with open(
                os.path.join(worktree, "steps.json"), "w", encoding="utf-8"
            ) as handle:
                handle.write('["Build"]')
            control(
                worktree,
                "done",
                "runbook",
                "--artifact",
                "runbook.md",
                "--steps-file",
                "steps.json",
            )
            status = json.loads(control(worktree, "status", "--json").stdout)
            relation = status["receipts"]["runbook"]["version_relations"]
            self.assertEqual(relation["anchor_commit"], anchor)
            self.assertEqual(
                relation["targets"][0]["anchor_version"], "fiat-v1.2.3"
            )
            control(worktree, "next")
            control(worktree, "verify")

    def test_commit_replacement_cannot_substitute_anchor_tree(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.write(self.ledger_path("fiat"), self.ledger("fiat", (9, 9, 9)))
        self.write(self.skill_path("fiat"), self.skill("fiat", (9, 9, 9)))
        self.git("add", "-A")
        self.git("commit", "-m", "replacement tree")
        replacement = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("reset", "--hard", anchor)

        self.init(base=anchor)
        self.git("replace", anchor, replacement)
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_blob_replacements_cannot_substitute_anchor_bytes(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        ledger_blob = self.git(
            "rev-parse", f"{anchor}:{self.ledger_path('fiat')}"
        ).stdout.strip()
        skill_blob = self.git(
            "rev-parse", f"{anchor}:{self.skill_path('fiat')}"
        ).stdout.strip()
        replacement_ledger = self.hash_object(self.ledger("fiat", (9, 9, 9)))
        replacement_skill = self.hash_object(self.skill("fiat", (9, 9, 9)))

        self.init(base=anchor)
        self.git("replace", ledger_blob, replacement_ledger)
        self.git("replace", skill_blob, replacement_skill)
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_grafted_branch_history_refuses_anchor_derivation(self):
        self.install_target("fiat")
        self.commit_seed()
        self.init()
        self.env["GIT_GRAFT_FILE"] = os.path.join(self.dir, "attacker-grafts")
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("rewritten by a graft", result.stderr)

    def test_relation_git_environment_cannot_redirect_anchor_repository(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        state = self.state()

        with tempfile.TemporaryDirectory() as attacker:
            for argv in (
                ("init", "-q", "-b", "main"),
                ("config", "user.email", "attacker@example.invalid"),
                ("config", "user.name", "Attacker"),
                ("config", "commit.gpgsign", "false"),
            ):
                subprocess.run(
                    ["git", *argv], cwd=attacker, check=True, capture_output=True
                )
            ledger = os.path.join(attacker, self.ledger_path("fiat"))
            skill = os.path.join(attacker, self.skill_path("fiat"))
            os.makedirs(os.path.dirname(ledger), exist_ok=True)
            with open(ledger, "w", encoding="utf-8") as handle:
                handle.write(self.ledger("fiat", (9, 9, 9)))
            with open(skill, "w", encoding="utf-8") as handle:
                handle.write(self.skill("fiat", (9, 9, 9)))
            subprocess.run(
                ["git", "add", "-A"], cwd=attacker, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "substitute repository"],
                cwd=attacker,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", state["run_branch"]],
                cwd=attacker,
                check=True,
                capture_output=True,
            )

            study = self.write("study.md", "# Study\n")
            self.run_ctl("done", "study", "--artifact", study)
            runbook = self.write(
                "runbook.md",
                "# Runbook\n\n"
                + self.relation_block("fiat")
                + "\n## Step 1: Build\n\n**Goal.** Build.\n",
            )
            steps = self.write("steps.json", '["Build"]')
            self.env["GIT_DIR"] = os.path.join(attacker, ".git")
            try:
                self.run_ctl(
                    "done", "runbook", "--artifact", runbook,
                    "--steps-file", steps,
                )
            finally:
                self.env.pop("GIT_DIR", None)

        with open(
            os.path.join(self.target, ".hexaemeron", "state.json"),
            encoding="utf-8",
        ) as handle:
            relation = self.receipt(json.load(handle))
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_relation_git_ignores_alternate_object_environment(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.path.join(
            self.dir, "absent-object-store"
        )
        try:
            self.run_ctl(
                "done", "runbook", "--artifact", runbook, "--steps-file", steps
            )
        finally:
            self.env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)

        relation = self.receipt(self.state())
        self.assertEqual(relation["anchor_commit"], anchor)
        self.assertEqual(relation["targets"][0]["anchor_version"], "fiat-v1.2.3")

    def test_repository_alternate_object_store_refuses_anchor_capture(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init(base=anchor)
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        alternates = self.git(
            "rev-parse", "--path-format=absolute", "--git-path",
            "objects/info/alternates",
        ).stdout.strip()
        os.makedirs(os.path.dirname(alternates), exist_ok=True)
        with tempfile.TemporaryDirectory() as alternate:
            with open(alternates, "w", encoding="utf-8") as handle:
                handle.write(alternate + "\n")
            runbook = self.write(
                "runbook.md",
                "# Runbook\n\n"
                + self.relation_block("fiat")
                + "\n## Step 1: Build\n\n**Goal.** Build.\n",
            )
            steps = self.write("steps.json", '["Build"]')
            result = self.run_ctl(
                "done", "runbook", "--artifact", runbook,
                "--steps-file", steps, expect=2,
            )
        self.assertIn("uses an alternate object store", result.stderr)

    def test_shallow_history_refuses_anchor_derivation(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        with open(shallow, "w", encoding="ascii") as handle:
            handle.write(anchor + "\n")
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("starting history is shallow", result.stderr)

    def test_anchor_derivation_refuses_history_that_turns_shallow_mid_read(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.init()
        state = self.state()
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        module = hexctl_module()
        native_git = module._native_relation_git
        changed = False

        def change_history_after_check(base_dir, argv, refusal):
            nonlocal changed
            output = native_git(base_dir, argv, refusal)
            if argv == ["rev-parse", "--is-shallow-repository"] and not changed:
                with open(shallow, "w", encoding="ascii") as handle:
                    handle.write(anchor + "\n")
                changed = True
            return output

        module._native_relation_git = change_history_after_check
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                module.relation_anchor_commit(self.target, state)
        self.assertIn("starting history is shallow", stderr.getvalue())

    def test_replay_refuses_tree_typed_anchor_commit(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.receipt_runbook("fiat")
        anchor_tree = self.git("rev-parse", f"{anchor}^{{tree}}").stdout.strip()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"]["version_relations"][
            "anchor_commit"
        ] = anchor_tree
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)

        for command in (("status",), ("next",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=2)
                self.assertIn("anchor commit", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_replay_refuses_post_receipt_repository_alternate(self):
        self.install_target("fiat")
        self.commit_seed()
        self.receipt_runbook("fiat")
        alternates = self.git(
            "rev-parse", "--path-format=absolute", "--git-path",
            "objects/info/alternates",
        ).stdout.strip()
        os.makedirs(os.path.dirname(alternates), exist_ok=True)
        with tempfile.TemporaryDirectory() as alternate:
            with open(alternates, "w", encoding="utf-8") as handle:
                handle.write(alternate + "\n")
            for command in (("status",), ("next",)):
                with self.subTest(command=command):
                    result = self.run_ctl(*command, expect=2)
                    self.assertIn("uses an alternate object store", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_replay_refuses_post_receipt_shallow_history(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.receipt_runbook("fiat")
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        with open(shallow, "w", encoding="ascii") as handle:
            handle.write(anchor + "\n")

        for command in (("status",), ("next",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=2)
                self.assertIn("starting history is shallow", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_replay_refuses_history_that_turns_shallow_mid_read(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        self.receipt_runbook("fiat")
        state = self.state()
        shallow = self.git(
            "rev-parse", "--path-format=absolute", "--git-path", "shallow"
        ).stdout.strip()
        module = hexctl_module()
        runbook = module.receipted_source(self.target, state, "runbook")
        native_git = module._native_relation_git
        changed = False

        def change_history_during_replay(base_dir, argv, refusal):
            nonlocal changed
            output = native_git(base_dir, argv, refusal)
            if argv[:2] == ["cat-file", "blob"] and not changed:
                with open(shallow, "w", encoding="ascii") as handle:
                    handle.write(anchor + "\n")
                changed = True
            return output

        module._native_relation_git = change_history_during_replay
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                module.receipted_version_relations(self.target, runbook)
        self.assertIn("starting history is shallow", stderr.getvalue())

    def test_no_block_preserves_the_legacy_receipt_and_packet_shape(self):
        _, state = self.receipt_runbook()
        self.assertEqual(
            set(state["receipts"]["runbook"]),
            {"artifact", "sha256", "step_count"},
        )
        raw = self.run_ctl("next").stdout
        directive = json.loads(raw)
        self.assertEqual(
            set(directive["brief"]["runbook_step"]),
            {
                "markdown",
                "baseline_markdown",
                "baseline_sha256",
                "amendments",
                "effective_sha256",
                "path",
                "sha256",
                "number",
                "title",
            },
        )
        self.assertNotIn("version_relations", json.dumps(directive))
        step_markdown = "## Step 1: Build\n\n**Goal.** Build the fixture.\n"
        step_sha256 = hashlib.sha256(step_markdown.encode()).hexdigest()
        branch = self.step_branch(1)
        expected = {
            "step": 1,
            "title": "Build",
            "do": "implement",
            "run_branch": "fiat/test-topic",
            "branch": branch,
            "branch_from": "fiat/test-topic",
            "pr_base": "fiat/test-topic",
            "merge_now": False,
            "state_sha256": hexctl_module().state_fingerprint(state),
            "agent": "mason",
            "brief": {
                "runbook_step": {
                    "markdown": step_markdown,
                    "baseline_markdown": step_markdown,
                    "baseline_sha256": step_sha256,
                    "amendments": [],
                    "effective_sha256": step_sha256,
                    "path": os.path.realpath(
                        os.path.join(
                            self.target,
                            state["receipts"]["runbook"]["artifact"],
                        )
                    ),
                    "sha256": state["receipts"]["runbook"]["sha256"],
                    "number": 1,
                    "title": "Build",
                },
                "branch": branch,
                "branch_from": "fiat/test-topic",
            },
        }
        self.assertEqual(raw, json.dumps(expected) + "\n")
        self.run_ctl("verify")

    def test_no_block_performs_no_git_version_read(self):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: Build\n\n**Goal.** Build.\n"
        )
        steps = self.write("steps.json", '["Build"]')
        sentinel = os.path.join(self.dir, "unexpected-git-read")
        wrapper_dir = os.path.join(self.dir, "refusing-git")
        os.makedirs(wrapper_dir)
        wrapper = os.path.join(wrapper_dir, "git")
        with open(wrapper, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                "import os\n"
                "Path(os.environ['VERSION_GIT_SENTINEL']).write_text('called\\n')\n"
                "raise SystemExit(99)\n"
            )
        os.chmod(wrapper, 0o755)
        prior_path = self.env["PATH"]
        self.env["PATH"] = wrapper_dir + os.pathsep + prior_path
        self.env["VERSION_GIT_SENTINEL"] = sentinel
        try:
            self.run_ctl(
                "done", "runbook", "--artifact", runbook, "--steps-file", steps
            )
            self.run_ctl("status")
            self.run_ctl("next")
        finally:
            self.env["PATH"] = prior_path
            self.env.pop("VERSION_GIT_SENTINEL", None)
        self.assertFalse(os.path.exists(sentinel))

    def test_no_block_init_does_not_require_native_reflogs(self):
        subprocess.run(
            ["git", "config", "core.logAllRefUpdates", "false"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        _, state = self.receipt_runbook()

        self.assertEqual(
            set(state["receipts"]["runbook"]),
            {"artifact", "sha256", "step_count"},
        )
        self.assertNotIn("version_relations", self.run_ctl("next").stdout)
        self.run_ctl("verify")

    def test_relation_packet_and_status_label_anchor_and_projection(self):
        self.install_target("fiat")
        anchor = self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        packet = self.next_json()["brief"]["runbook_step"]["version_relations"]
        self.assertEqual(packet["status"], "anchor")
        self.assertIsNone(packet["resolution"])
        self.assertEqual(packet["anchor_commit"], anchor)
        self.assertEqual(packet["targets"][0]["ledger"], self.ledger_path("fiat"))
        self.assertEqual(packet["targets"][0]["anchor_version"], "fiat-v1.2.3")
        self.assertEqual(packet["targets"][0]["projection"], "fiat-v1.3.3")
        self.assertNotIn("reserved", json.dumps(packet).lower())
        human = self.run_ctl("status").stdout
        self.assertIn(SCHEMA, human)
        self.assertIn(packet["source_sha256"], human)
        self.assertIn(anchor, human)
        self.assertIn(self.ledger_path("fiat"), human)
        self.assertIn("resolution null", human)
        self.assertIn("projection fiat-v1.3.3", human)
        self.run_ctl("verify")
        self.assertEqual(
            self.receipt(state), self.state()["receipts"]["runbook"]["version_relations"]
        )

    def test_projection_increments_generation_without_semver_reset(self):
        self.install_target("fiat", (7, 99, 13))
        self.commit_seed()
        self.receipt_runbook("fiat")
        packet = self.next_json()["brief"]["runbook_step"]["version_relations"]
        self.assertEqual(packet["targets"][0]["anchor_version"], "fiat-v7.99.13")
        self.assertEqual(packet["targets"][0]["projection"], "fiat-v7.100.13")

    def test_projection_refuses_an_unrepresentable_generation_successor(self):
        maximum = "9" * 128
        self.install_target("fiat", (1, maximum, 0))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertIn(
            "generation cannot be projected within its counter bound",
            result.stderr,
        )
        self.assertNotIn(maximum, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_leading_zero_counters_are_not_canonical_labels(self):
        self.install_target("fiat", ("01", "02", "03"))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("malformed current label", result.stderr)

    def test_warden_and_scribe_packets_reconstruct_the_same_anchor(self):
        self.install_target("fiat")
        self.commit_seed()
        _, state = self.receipt_runbook(
            "fiat",
            study_text=(
                "# Study\n\n```risk-register\n"
                "relation-anchor | packet boundary | reconstruct\n```\n"
            ),
        )
        expected = self.next_json()["brief"]["runbook_step"]["version_relations"]
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")

        # Packet construction is the subject here.  Move the valid state fixture
        # between worker phases without exercising their unrelated Git receipts.
        state["receipts"]["security_suite"] = "waived: packet fixture"
        state["steps"][0]["phase"] = "audit"
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        warden = self.next_json()
        self.assertEqual(
            warden["brief"]["runbook_step"]["version_relations"], expected
        )

        self.git("branch", self.step_branch(1), "HEAD")
        state["steps"][0]["phase"] = "prose"
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        scribe = self.next_json()
        self.assertEqual(scribe["brief"]["version_relations"], expected)

    def test_ledger_and_skill_metadata_mismatch_refuses_without_partial_state(self):
        self.install_target("fiat")
        self.write(self.skill_path("fiat"), self.skill("fiat", (1, 2, 4)))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb") as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat") + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("metadata version", result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_body_example_cannot_stand_in_for_frontmatter_metadata(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            "---\n"
            "name: fiat\n"
            "description: Fixture with no metadata field.\n"
            "---\n\n"
            "Example only:\n\n"
            '  version: "1.2.3"\n',
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("frontmatter metadata version", result.stderr)

    def test_skill_frontmatter_name_must_match_the_relation_target(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            self.skill("other").replace("# other", "# fiat"),
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("frontmatter name", result.stderr)

    def test_quoted_duplicate_frontmatter_name_is_ambiguous(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            self.skill("fiat").replace(
                "name: fiat\n", 'name: fiat\n"name": other\n'
            ),
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertIn("frontmatter name", result.stderr)

    def test_quoted_duplicate_metadata_version_is_ambiguous(self):
        self.write(self.ledger_path("fiat"), self.ledger("fiat"))
        self.write(
            self.skill_path("fiat"),
            self.skill("fiat").replace(
                '  version: "1.2.3"\n',
                '  version: "1.2.3"\n  "version": "9.9.9"\n',
            ),
        )
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertIn("frontmatter metadata version", result.stderr)

    def test_yaml_equivalent_protected_keys_are_ambiguous(self):
        canonical = self.skill("fiat")
        specimens = {
            "escaped-name": canonical.replace(
                "name: fiat\n", 'name: fiat\n"na\\u006de": other\n'
            ),
            "tagged-name": canonical.replace(
                "name: fiat\n", "name: fiat\n!!str name: other\n"
            ),
            "explicit-name": canonical.replace(
                "name: fiat\n", "name: fiat\n? name\n: other\n"
            ),
            "continued-name": canonical.replace(
                "name: fiat\n", "name: fiat\n  other\n"
            ),
            "escaped-version": canonical.replace(
                '  version: "1.2.3"\n',
                '  version: "1.2.3"\n  "ver\\u0073ion": "9.9.9"\n',
            ),
            "tagged-version": canonical.replace(
                '  version: "1.2.3"\n',
                '  version: "1.2.3"\n  !!str version: "9.9.9"\n',
            ),
        }
        for label, text in specimens.items():
            with self.subTest(label=label):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        hexctl_module()._skill_frontmatter_identity(text, "fiat")

    def test_relation_failure_does_not_echo_the_controlled_target_id(self):
        controlled = "private-relation-target-token"
        self.write(self.skill_path(controlled), self.skill(controlled))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block(controlled)
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook,
            "--steps-file", steps, expect=2,
        )
        self.assertNotIn(controlled, result.stderr)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 256)
        self.assertNotIn("Traceback", result.stderr)

    def test_unbounded_decimal_label_refuses_instead_of_raising(self):
        label = "fiat-v" + ("9" * 5000) + ".0.0"
        try:
            parsed = hexctl_module()._label_parts(label, "fiat")
        except ValueError:
            self.fail("unbounded decimal label raised instead of refusing")
        self.assertIsNone(parsed)

    def test_decimal_limit_is_independent_of_python_startup_policy(self):
        huge = "9" * 5000
        self.install_target("fiat", (huge, 0, 0))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb"
        ) as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.env["PYTHONINTMAXSTRDIGITS"] = "0"
        try:
            result = self.run_ctl(
                "done", "runbook", "--artifact", runbook,
                "--steps-file", steps, expect=2,
            )
        finally:
            self.env.pop("PYTHONINTMAXSTRDIGITS", None)
        self.assertIn("malformed current label", result.stderr)
        self.assertNotIn(huge, result.stderr)
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def test_one_bad_target_refuses_the_whole_capture(self):
        self.install_target("fiat")
        self.write(self.skill_path("protasis"), self.skill("protasis", (4, 7, 0)))
        self.commit_seed()
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        before_state = self.state()
        with open(os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), "rb") as handle:
            before_ledger = handle.read()
        runbook = self.write(
            "runbook.md",
            self.relation_block("fiat", "protasis")
            + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assert_unchanged_after_refusal(before_state, before_ledger)

    def _assert_object_refused(self, skill, needle):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            self.relation_block(skill) + "\n## Step 1: Build\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn(needle, result.stderr)
        self.assertNotIn("ghp_", result.stderr)

    def test_missing_ledger_object_is_refused_content_free(self):
        self.write(self.skill_path("missing"), self.skill("missing"))
        self.commit_seed()
        self._assert_object_refused("missing", "missing")

    def test_tree_ledger_object_is_refused(self):
        self.write(self.skill_path("tree"), self.skill("tree"))
        self.write(self.ledger_path("tree") + "/child", "not a blob\n")
        self.commit_seed()
        self._assert_object_refused("tree", "regular blob")

    def test_symlink_ledger_object_is_refused(self):
        self.write(self.skill_path("linked"), self.skill("linked"))
        ledger = os.path.join(self.dir, self.ledger_path("linked"))
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        os.symlink("SKILL.md", ledger)
        self.commit_seed()
        self._assert_object_refused("linked", "regular blob")

    def test_gitlink_ledger_object_is_refused(self):
        self.write(self.skill_path("gitlink"), self.skill("gitlink"))
        self.git("add", self.skill_path("gitlink"))
        target = self.git("rev-parse", "HEAD").stdout.strip()
        self.git(
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{target},{self.ledger_path('gitlink')}",
        )
        self.git("commit", "-m", "seed gitlink")
        self._assert_object_refused("gitlink", "regular blob")

    def test_non_utf8_ledger_object_is_refused(self):
        self.write(self.skill_path("binary"), self.skill("binary"))
        ledger = os.path.join(self.dir, self.ledger_path("binary"))
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "wb") as handle:
            handle.write(b"\xff\xfe\x00")
        self.commit_seed()
        self._assert_object_refused("binary", "UTF-8")

    def test_oversized_ledger_object_is_refused_before_parsing(self):
        self.write(self.skill_path("large"), self.skill("large"))
        ledger = os.path.join(self.dir, self.ledger_path("large"))
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "wb") as handle:
            handle.write(b"x" * (2 * 1024 * 1024 + 1))
        self.commit_seed()
        self._assert_object_refused("large", "byte cap")

    def test_unsafe_relation_path_is_not_treated_as_legacy(self):
        self.install_target("fiat")
        self.commit_seed()
        block = (
            "```version-relations\n"
            f"fiat | ../fiat/EVOLUTION.md | {RELATION}\n"
            "```\n"
        )
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md", block + "\n## Step 1: Build\n\n**Goal.** Build.\n"
        )
        steps = self.write("steps.json", '["Build"]')
        result = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("safe repository-relative", result.stderr)

    def test_malformed_stored_anchor_refuses_status_next_and_verify(self):
        self.install_target("fiat")
        self.commit_seed()
        self.receipt_runbook("fiat")
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"]["version_relations"]["targets"][0].pop(
            "ledger_sha256"
        )
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        for command in (("status",), ("next",), ("verify",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=1)
                self.assertIn("version relations", result.stderr)

    def test_surrogate_revision_is_a_bounded_state_refusal(self):
        self.install_target("fiat")
        self.commit_seed()
        self.receipt_runbook("fiat")
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"]["version_relations"]["targets"][0][
            "frontier_revision"
        ] = "\ud800"
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        expected = (
            "state version relations key "
            "'receipts.runbook.version_relations.targets[0].frontier_revision' "
            "is malformed"
        )
        for command in (("status",), ("next",), ("verify",)):
            with self.subTest(command=command):
                result = self.run_ctl(*command, expect=1)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    import unittest

    unittest.main()
