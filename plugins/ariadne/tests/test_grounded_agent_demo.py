"""The grounded-agent walkthrough stays complete, deterministic, and offline."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

from . import support


DEMO = (
    Path(support.PLUGIN_ROOT) / "examples" / "grounded_agent_demo.py"
)
STATEMENT_SHA256 = (
    "03fb54176a417248447a5e92ce702acce229855b0378215fd68a4286130165bc"
)


class GroundedAgentDemoTests(unittest.TestCase):
    def test_demo_holds_every_stage_without_model_or_network(self):
        with tempfile.TemporaryDirectory(
            prefix="ariadne-demo-test-network-guard-"
        ) as temporary:
            guard = Path(temporary)
            (guard / "sitecustomize.py").write_text(
                "import socket\n"
                "def _blocked(*args, **kwargs):\n"
                "    raise RuntimeError('network disabled by demo test')\n"
                "socket.socket = _blocked\n"
                "socket.create_connection = _blocked\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            existing = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = str(guard) + (
                os.pathsep + existing if existing else ""
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [sys.executable, str(DEMO)],
                cwd=support.REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                timeout=120,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        output = completed.stdout
        for stage in (
            "rebuild the preserved Berean release",
            "capture twice and compare exact bytes",
            "verify all registered gates offline",
            "verify the shipped one-byte tamper",
            "mutate each Berean evidence class independently",
        ):
            self.assertIn("== %s ==" % stage, output)

        self.assertIn("statement sha256: %s" % STATEMENT_SHA256, output)
        self.assertIn("subjects: 12; declared bytes: 93165", output)

        verification = output.split(
            "== verify all registered gates offline ==", 1
        )[1].split("== verify the shipped one-byte tamper ==", 1)[0]
        gate_lines = [
            line for line in verification.splitlines() if line.startswith("gate ")
        ]
        check_lines = [
            line for line in verification.splitlines() if line.startswith("check ")
        ]
        self.assertEqual(len(gate_lines), 7, gate_lines)
        self.assertEqual(len(check_lines), 6, check_lines)
        self.assertFalse(
            any(
                "FAIL" in line or "unchecked" in line.lower()
                for line in gate_lines + check_lines
            )
        )

        self.assertIn("check release-digest: refused; unchecked: none", output)
        for refusal in (
            "identity: capture failed: release_digest does not match the canonical identity fields",
            "input: capture failed: release reads does not match its declared sha256",
            "output: capture failed: release answer 1 does not match its declared sha256",
            "promotion: capture failed: promotion report digest is not the release report",
        ):
            self.assertIn(refusal, output)
        self.assertTrue(
            output.rstrip().endswith(
                "model execution: none; network: disabled; every stage held"
            )
        )


if __name__ == "__main__":
    unittest.main()
