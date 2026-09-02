"""Focused guards for Fiat's companion observation-prefix receipt."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from unittest import mock

try:
    from plugins.hexaemeron.tests.test_hexctl import HexctlCase, hexctl_module
except ModuleNotFoundError:  # plugin-root discovery
    from test_hexctl import HexctlCase, hexctl_module


ROOT = Path(__file__).resolve().parents[3]
SUCCESS = ROOT / "tests" / "fixtures" / "run-observation" / "valid" / "success.jsonl"
CASES = Path(__file__).resolve().parent / "fixtures" / "run-observation-binding" / "cases.json"
BINDING_CONTRACT = "fiat-run-observation-binding/v1"
OBSERVATION_CONTRACT = "promise-machine-run-observation/v1"


def source_runner_module():
    """Load the source-owned Elenchus reporter without invoking its suite."""
    source = ROOT / "plugins" / "hexaemeron" / "tests" / "run_tests.py"
    spec = importlib.util.spec_from_file_location("fiat_run_tests_reporter", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ObservationBindingTests(HexctlCase):
    def test_binding_validates_the_captured_bytes_not_a_later_path_snapshot(self):
        self.to_steps(("Bind",))
        relative, _, captured = self.write_prefix()
        events = [json.loads(line) for line in captured.splitlines()]
        events[0]["chainOfThought"] = "not-receiptable"
        rejected = b"".join(
            json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
            + b"\n"
            for event in events
        )
        controller = hexctl_module()

        with mock.patch.object(
            controller,
            "read_observation_bytes",
            return_value=(relative, rejected),
        ):
            with self.assertRaises(SystemExit):
                controller.validated_observation_prefix(
                    self.target,
                    relative,
                    controller.load_state(self.target),
                )

    def test_binding_finally_rechecks_the_named_bytes_after_validation(self):
        self.to_steps(("Bind",))
        relative, target, _ = self.write_prefix()
        controller = hexctl_module()
        validator = mock.Mock()

        def replace_after_validation(*_args, **_kwargs):
            with open(target, "wb") as handle:
                handle.write(b"{}\n")
            return []

        validator.validate_bytes.side_effect = replace_after_validation
        with mock.patch.object(
            controller,
            "observation_validator_module",
            return_value=validator,
        ):
            with self.assertRaises(SystemExit):
                controller.validated_observation_prefix(
                    self.target,
                    relative,
                    controller.load_state(self.target),
                )

    def test_status_exposes_a_stable_run_id_without_persisting_it(self):
        self.init("Bind observation identity")
        first = json.loads(self.run_ctl("status", "--json").stdout)
        second = json.loads(self.run_ctl("status", "--json").stdout)
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            stored = json.load(handle)

        self.assertEqual(first["observation_run_id"], second["observation_run_id"])
        self.assertEqual(first["observation_run_id"], self.controller_run_id())
        self.assertNotIn("observation_run_id", stored)
        self.run_ctl("verify")

    def test_receipted_elenchus_reporter_accepts_positional_target(self):
        self.to_steps(("Bind",))
        target_dir = Path(self.target).resolve()
        report = target_dir / ".elenchus" / "binding.json"
        runner = source_runner_module()
        current = Path.cwd()
        try:
            os.chdir(target_dir)
            root, _, parts = runner.report_target([str(report)])
        finally:
            os.chdir(current)
        self.assertEqual(root, target_dir)
        self.assertEqual(parts, (".elenchus", "binding.json"))

    def test_fixture_manifest_names_the_normal_and_nine_negative_mechanisms(self):
        manifest = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(manifest["contract"], BINDING_CONTRACT)
        cases = manifest["cases"]
        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        self.assertEqual(
            {
                "normal-prefix",
                "replacement",
                "truncation",
                "reordered-events",
                "wrong-run-association",
                "event-count-mismatch",
                "contract-drift",
                "failed-redaction",
                "missing-binding",
                "appended-event-confusion",
            }
            - {case["id"] for case in cases},
            set(),
        )
        for case in cases:
            self.assertTrue(hasattr(self, case["guard"]), case)

    def controller_run_id(self):
        state = self.state()
        identity = {
            "base": state["base"],
            "controller": state["controller"],
            "created_at": state["created_at"],
            "run_branch": state["run_branch"],
            "topic": state["topic"],
            "version": state["version"],
        }
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        return "fiat-" + hashlib.sha256(encoded).hexdigest()

    def write_prefix(self, *, run_id=None, contract=OBSERVATION_CONTRACT):
        run_id = run_id or self.controller_run_id()
        events = [json.loads(line) for line in SUCCESS.read_text().splitlines()][:-1]
        for event in events:
            event["run_id"] = run_id
            event["schema_id"] = contract
        relative = os.path.join(".hexaemeron", "observations", "run.jsonl")
        target = os.path.join(self.target, relative)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = "".join(
            json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            for event in events
        ).encode()
        with open(target, "wb") as handle:
            handle.write(data)
        return relative, target, data

    def append_finish(self, target):
        event = json.loads(SUCCESS.read_text().splitlines()[-1])
        event["run_id"] = self.controller_run_id()
        data = (
            json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        with open(target, "ab") as handle:
            handle.write(data)
        return data

    def ledger(self):
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    @staticmethod
    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def rewrite_last_binding(self, mutate):
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        binding = state["receipts"]["run_observations"][-1]
        mutate(binding)
        state_digest = hashlib.sha256(self.canonical(state).encode()).hexdigest()
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        entries[-1]["data"]["binding_sha256"] = hashlib.sha256(
            self.canonical(binding).encode()
        ).hexdigest()
        entries[-1]["state"] = state_digest
        unsigned = {
            key: entries[-1][key]
            for key in ("ts", "event", "data", "prev", "state")
        }
        entries[-1]["hash"] = hashlib.sha256(
            self.canonical(unsigned).encode()
        ).hexdigest()
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

    def rewrite_last_ledger_data(self, mutate):
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        mutate(entries[-1]["data"])
        unsigned = {
            key: entries[-1][key]
            for key in ("ts", "event", "data", "prev", "state")
        }
        entries[-1]["hash"] = hashlib.sha256(
            self.canonical(unsigned).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

    def bind(self, relative, *, expect=0):
        return self.run_ctl(
            "observe",
            "--artifact",
            relative,
            "--capture-status",
            "accepted",
            "--redaction-status",
            "passed",
            expect=expect,
        )

    def test_normal_prefix_binds_to_the_selected_receipt(self):
        self.to_steps(("Bind",))
        relative, _, data = self.write_prefix()
        selected = self.ledger()[-1]
        phase = self.state()["steps"][0]["phase"]

        result = self.bind(relative)

        self.assertIn(BINDING_CONTRACT, result.stdout)
        state = self.state()
        self.assertEqual(state["steps"][0]["phase"], phase)
        binding = state["receipts"]["run_observations"][0]
        self.assertEqual(binding["schema"], BINDING_CONTRACT)
        self.assertEqual(binding["observation_contract"], OBSERVATION_CONTRACT)
        self.assertEqual(binding["controller_run_id"], self.controller_run_id())
        self.assertEqual(binding["artifact"], relative)
        self.assertEqual(binding["event_count"], 3)
        self.assertEqual(binding["byte_count"], len(data))
        self.assertEqual(binding["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(binding["receipt"]["hash"], selected["hash"])
        self.assertEqual(binding["receipt"]["event"], selected["event"])
        self.assertEqual(self.ledger()[-1]["event"], "record:run-observation")
        verified = self.run_ctl("verify", "--observations")
        self.assertIn("1 observation prefix", verified.stdout)

    def test_legacy_run_stays_valid_until_the_dependent_claim_is_requested(self):
        self.to_steps(("Bind",))
        self.run_ctl("verify")
        refused = self.run_ctl("verify", "--observations", expect=1)
        self.assertIn("FOB001", refused.stderr)

    def test_non_available_capture_records_no_digest_and_does_not_break_verify(self):
        self.to_steps(("Bind",))
        self.run_ctl(
            "observe",
            "--capture-status",
            "unavailable",
            "--redaction-status",
            "unknown",
            "--reason-code",
            "observer-unavailable",
        )
        binding = self.state()["receipts"]["run_observations"][0]
        self.assertEqual(binding["capture_status"], "unavailable")
        for key in ("artifact", "byte_count", "event_count", "sha256"):
            self.assertNotIn(key, binding)
        self.run_ctl("verify")
        refused = self.run_ctl("verify", "--observations", expect=1)
        self.assertIn("FOB005", refused.stderr)

    def test_replacement_and_truncation_break_only_the_dependent_claim(self):
        replacements = (b"{}\n", b"")
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                self.to_steps(("Bind",))
                relative, target, _ = self.write_prefix()
                self.bind(relative)
                with open(target, "wb") as handle:
                    handle.write(replacement)

                self.run_ctl("verify")
                refused = self.run_ctl("verify", "--observations", expect=1)
                self.assertIn("FOB004", refused.stderr)

                self.tearDown()
                self.setUp()

    def test_reordered_events_break_only_the_dependent_claim(self):
        self.to_steps(("Bind",))
        relative, target, data = self.write_prefix()
        self.bind(relative)
        lines = data.splitlines(keepends=True)
        with open(target, "wb") as handle:
            handle.write(lines[1] + lines[0] + b"".join(lines[2:]))

        self.run_ctl("verify")
        refused = self.run_ctl("verify", "--observations", expect=1)
        self.assertIn("FOB004", refused.stderr)

    def test_appended_bytes_remain_explicitly_unbound(self):
        self.to_steps(("Bind",))
        relative, target, original = self.write_prefix()
        self.bind(relative)
        tail = b'{"unbound":"tail"}\n'
        with open(target, "ab") as handle:
            handle.write(tail)

        verified = self.run_ctl("verify", "--observations")
        self.assertIn(f"unbound tail: {len(tail)} bytes", verified.stdout)
        binding = self.state()["receipts"]["run_observations"][0]
        self.assertEqual(binding["byte_count"], len(original))

    def test_later_receipt_binds_only_a_strict_extension_of_the_same_stream(self):
        self.to_steps(("Bind",))
        relative, target, first = self.write_prefix()
        self.bind(relative)
        finish = self.append_finish(target)
        self.run_ctl("record", "boundary", '"later receipt"')

        self.bind(relative)
        bindings = self.state()["receipts"]["run_observations"]
        self.assertEqual(len(bindings), 2)
        self.assertEqual(bindings[1]["event_count"], 4)
        self.assertEqual(bindings[1]["byte_count"], len(first + finish))
        self.run_ctl("verify", "--observations")

        self.run_ctl("record", "boundary", '"unchanged prefix"')
        refused = self.bind(relative, expect=2)
        self.assertIn("FOB004", refused.stderr)

    def test_multiple_bindings_report_only_the_latest_unbound_tail(self):
        self.to_steps(("Bind",))
        relative, target, _ = self.write_prefix()
        self.bind(relative)
        self.append_finish(target)
        self.run_ctl("record", "boundary", '"later receipt"')
        self.bind(relative)
        tail = b'{"unbound":"latest-tail"}\n'
        with open(target, "ab") as handle:
            handle.write(tail)

        verified = self.run_ctl("verify", "--observations")
        self.assertIn(f"unbound tail: {len(tail)} bytes", verified.stdout)

    def test_verification_recomputes_monotonic_stream_relationships(self):
        self.to_steps(("Bind",))
        relative, target, _ = self.write_prefix()
        self.bind(relative)
        self.append_finish(target)
        self.run_ctl("record", "boundary", '"later receipt"')
        self.bind(relative)
        other_relative = os.path.join(
            ".hexaemeron", "observations", "other.jsonl"
        )
        other = os.path.join(self.target, other_relative)
        with open(target, "rb") as source, open(other, "wb") as destination:
            destination.write(source.read())
        self.rewrite_last_binding(
            lambda binding: binding.__setitem__("artifact", other_relative)
        )

        self.run_ctl("verify")
        refused = self.run_ctl("verify", "--observations", expect=1)
        self.assertIn("FOB004", refused.stderr)

    def test_verification_recomputes_the_structural_validation_gate(self):
        self.to_steps(("Bind",))
        relative, target, captured = self.write_prefix()
        self.bind(relative)
        events = [json.loads(line) for line in captured.splitlines()]
        events[1]["chainOfThought"] = "must-not-be-receipted"
        rejected = b"".join(
            json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
            + b"\n"
            for event in events
        )
        with open(target, "wb") as handle:
            handle.write(rejected)
        self.rewrite_last_binding(
            lambda binding: binding.update(
                byte_count=len(rejected),
                sha256=hashlib.sha256(rejected).hexdigest(),
            )
        )

        self.run_ctl("verify")
        refused = self.run_ctl("verify", "--observations", expect=1)
        self.assertIn("FOB003", refused.stderr)

    def test_verification_finally_rechecks_named_bytes_after_validation(self):
        self.to_steps(("Bind",))
        relative, target, _ = self.write_prefix()
        self.bind(relative)
        controller = hexctl_module()
        validator = mock.Mock()

        def replace_after_validation(*_args, **_kwargs):
            with open(target, "wb") as handle:
                handle.write(b"{}\n")
            return []

        validator.validate_bytes.side_effect = replace_after_validation
        with mock.patch.object(
            controller,
            "observation_validator_module",
            return_value=validator,
        ):
            with self.assertRaises(SystemExit):
                controller.verify_observation_bindings(
                    self.target,
                    controller.load_state(self.target),
                )

    def test_verification_joins_each_binding_to_one_exact_ledger_record(self):
        self.to_steps(("Bind",))
        relative, _, _ = self.write_prefix()
        self.bind(relative)
        self.rewrite_last_ledger_data(
            lambda data: data.__setitem__("receipt_hash", "0" * 64)
        )

        self.run_ctl("verify")
        refused = self.run_ctl("verify", "--observations", expect=1)
        self.assertIn("FOB003", refused.stderr)

    def test_verification_refuses_an_orphaned_observation_record(self):
        self.to_steps(("Bind",))
        relative, target, _ = self.write_prefix()
        self.bind(relative)
        self.append_finish(target)
        self.run_ctl("record", "boundary", '"later receipt"')
        self.bind(relative)
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["run_observations"] = state["receipts"][
            "run_observations"
        ][1:]
        state_digest = hashlib.sha256(self.canonical(state).encode()).hexdigest()
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        entries[-1]["state"] = state_digest
        unsigned = {
            key: entries[-1][key]
            for key in ("ts", "event", "data", "prev", "state")
        }
        entries[-1]["hash"] = hashlib.sha256(
            self.canonical(unsigned).encode()
        ).hexdigest()
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

        self.run_ctl("verify")
        refused = self.run_ctl("verify", "--observations", expect=1)
        self.assertIn("FOB003", refused.stderr)

    def test_wrong_run_contract_and_failed_redaction_refuse_before_receipt(self):
        cases = (
            ("wrong-run", OBSERVATION_CONTRACT, "passed", "FOB003"),
            (None, "wrong-contract/v1", "passed", "FOB003"),
            (None, OBSERVATION_CONTRACT, "failed", "FOB005"),
        )
        for run_id, contract, redaction, code in cases:
            with self.subTest(run_id=run_id, contract=contract, redaction=redaction):
                self.to_steps(("Bind",))
                relative, _, _ = self.write_prefix(run_id=run_id, contract=contract)
                before = len(self.ledger())
                refused = self.run_ctl(
                    "observe",
                    "--artifact",
                    relative,
                    "--capture-status",
                    "accepted",
                    "--redaction-status",
                    redaction,
                    expect=2,
                )
                self.assertIn(code, refused.stderr)
                self.assertEqual(len(self.ledger()), before)

                self.tearDown()
                self.setUp()

    def test_bound_run_contract_and_event_count_are_recomputed(self):
        mutations = (
            (lambda binding: binding.__setitem__("controller_run_id", "wrong-run")),
            (lambda binding: binding.__setitem__("observation_contract", "wrong/v1")),
            (lambda binding: binding.__setitem__("event_count", 99)),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.to_steps(("Bind",))
                relative, _, _ = self.write_prefix()
                self.bind(relative)
                self.rewrite_last_binding(mutate)

                self.run_ctl("verify")
                refused = self.run_ctl("verify", "--observations", expect=1)
                self.assertIn("FOB003", refused.stderr)

                self.tearDown()
                self.setUp()

    def test_symlinked_file_and_parent_are_refused_before_receipt(self):
        for parent_link in (False, True):
            with self.subTest(parent_link=parent_link):
                self.to_steps(("Bind",))
                relative, target, _ = self.write_prefix()
                external = os.path.join(self.target, "external.jsonl")
                os.replace(target, external)
                if parent_link:
                    observations = os.path.dirname(target)
                    os.rmdir(observations)
                    os.symlink(os.path.dirname(external), observations)
                else:
                    os.symlink(external, target)
                before = len(self.ledger())

                refused = self.run_ctl(
                    "observe",
                    "--artifact",
                    relative,
                    "--capture-status",
                    "accepted",
                    "--redaction-status",
                    "passed",
                    expect=2,
                )
                self.assertIn("FOB002", refused.stderr)
                self.assertEqual(len(self.ledger()), before)

                self.tearDown()
                self.setUp()

    def test_final_read_refuses_parent_escape_during_second_snapshot(self):
        self.to_steps(("Bind",))
        target_dir = self.target
        relative, target, _ = self.write_prefix()
        observations = os.path.dirname(target)
        escaped = os.path.join(self.dir, "escaped-observations")
        controller = hexctl_module()
        original_stat = controller.os.stat
        named_reads = [0]

        def escape_on_final_named_stat(*args, **kwargs):
            result = original_stat(*args, **kwargs)
            if args == ("run.jsonl",) and kwargs.get("dir_fd") is not None:
                named_reads[0] += 1
            if named_reads[0] == 2:
                os.rename(observations, escaped)
            return result

        with mock.patch.object(controller.os, "stat", side_effect=escape_on_final_named_stat):
            with self.assertRaises(SystemExit) as refused:
                controller.read_observation_bytes(target_dir, relative)
        self.assertEqual(named_reads[0], 2)
        self.assertEqual(refused.exception.code, 2)
        self.assertFalse(os.path.exists(target))

    def test_consecutive_binding_cannot_select_an_observation_receipt(self):
        self.to_steps(("Bind",))
        relative, _, _ = self.write_prefix()
        self.bind(relative)
        refused = self.bind(relative, expect=2)
        self.assertIn("FOB003", refused.stderr)


if __name__ == "__main__":
    import unittest

    unittest.main()
