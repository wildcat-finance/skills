"""Demonstrations own signing material despite operator signing defaults."""

import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from fixture_tools import native_signing_tools
from test_fiat_criteria_demonstration import ROOT, PROOF_PATH, load_proof


class DemonstrationSigningIsolationTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="demo-signing-isolation-")
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name).resolve()
        self.proof = load_proof(PROOF_PATH)
        self.config = self.scratch / "operator-config"

    def operator_defaults(self, signature_format):
        self.config.write_text(
            "[user]\n name = Operator\n email = operator@example.invalid\n"
            " signingkey = unavailable-operator-key\n"
            "[commit]\n gpgsign = true\n"
            f"[gpg]\n format = {signature_format}\n program = unavailable-operator-gpg\n"
            "[gpg \"ssh\"]\n program = unavailable-operator-ssh\n"
            " allowedSignersFile = unavailable-operator-signers\n",
            encoding="utf-8",
        )
        return mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(self.config), "GIT_CONFIG_NOSYSTEM": "1",
        })

    def assert_signed_with_operator_defaults(self, signature_format):
        with native_signing_tools(("ssh-keygen",)), self.operator_defaults(signature_format):
            original = self.config.read_bytes()
            _, evidence = self.proof.check_joined_demonstration(ROOT)
            self.assertEqual(original, self.config.read_bytes())
        self.assertTrue(evidence["fixture"]["source_signed"])
        self.assertTrue(evidence["controller"]["source"]["signed"])
        self.assertTrue(evidence["source_command"]["source_before"]["signed"])
        self.assertTrue(evidence["source_command"]["source_after"]["signed"])
        self.assertEqual(1, evidence["actual_counts"]["execution_invocations"])
        self.assertEqual(0, evidence["inspection_launches"])
        self.assertFalse(Path(evidence["fixture"]["origin"]).exists())

    def test_ssh_operator_defaults_do_not_choose_fixture_signing(self):
        self.assert_signed_with_operator_defaults("ssh")

    def test_openpgp_operator_defaults_do_not_choose_fixture_signing(self):
        self.assert_signed_with_operator_defaults("openpgp")

    def test_missing_signing_tool_keeps_unsigned_execution_explicit(self):
        native_which = shutil.which

        def without_signing_tool(name, *args, **kwargs):
            return None if name == "ssh-keygen" else native_which(name, *args, **kwargs)

        with self.operator_defaults("ssh"), mock.patch.object(
            self.proof.shutil, "which", side_effect=without_signing_tool
        ):
            self.assert_unsigned_refusal(ROOT)

    def test_copy_mode_keeps_unsigned_execution_explicit(self):
        root = self.scratch / "copy"
        skills = Path("plugins/hexaemeron/skills")
        shutil.copytree(ROOT / skills, root / skills,
                        ignore=shutil.ignore_patterns("__pycache__"))
        destination = root / self.proof.SELF
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / self.proof.SELF, destination)
        design = root / self.proof.PACKAGE
        shutil.copyfile(ROOT / self.proof.PACKAGE / "design-evidence.json", design / "design-evidence.json")
        shutil.copytree(ROOT / self.proof.PACKAGE / "reports", design / "reports")
        with self.operator_defaults("openpgp"):
            self.assert_unsigned_refusal(root, publish=True)

    def assert_unsigned_refusal(self, root, *, publish=False):
        native_load = self.proof.load_module
        observations = []

        def observe_execution(path, name):
            module = native_load(path, name)
            if name == "criteria_demonstration_execution":
                execute = module.execute

                def record(*args, **kwargs):
                    result = execute(*args, **kwargs)
                    observations.append((kwargs, result))
                    return result

                module.execute = record
            return module

        original = self.config.read_bytes()
        report = ".hexaemeron/reports/unsigned-demonstration.json"
        with mock.patch.object(self.proof, "load_module", side_effect=observe_execution):
            with self.assertRaisesRegex(self.proof.Refusal, "unsigned-fixture-not-admitted"):
                if publish:
                    self.proof.run(root, "controller-capture", "joined-demonstration", report)
                else:
                    self.proof.check_joined_demonstration(root)
        if publish:
            self.assertFalse((root / report).exists())
            self.assertFalse((root / report).with_suffix(".evidence.json").exists())
        self.assertEqual(original, self.config.read_bytes())
        self.assertEqual(1, len(observations))
        arguments, observed = observations[0]
        self.assertIs(arguments["require_signed"], False)
        self.assertTrue(observed["settled"])
        self.assertFalse(observed["source_before"]["signed"])
        self.assertFalse(observed["source_after"]["signed"])
        self.assertEqual(1, len(observed["invocations"]))
