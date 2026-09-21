"""Design report publication and unsupported operations refuse safely."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import checkpoint_network_design_report as design_report


class NetworkReportTests(unittest.TestCase):
    def test_missing_hosted_evidence_never_creates_a_report(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            code = design_report.main(["--candidate", "bubblewrap-seccomp", "--criterion", "hosted-macos",
                                       "--report", ".hexaemeron/reports/conformance/bubblewrap-seccomp-hosted-macos.json"], root=root)
            self.assertEqual(code, 2)
            self.assertEqual(list(root.iterdir()), [])

    def test_unsupported_candidate_and_unsafe_path_refuse_before_execution(self):
        for candidate, path in (("bubblewrap-netns", "x.json"), ("bubblewrap-seccomp", "../x.json")):
            with self.subTest(candidate=candidate), tempfile.TemporaryDirectory() as directory, \
                    contextlib.redirect_stdout(io.StringIO()), patch.object(design_report, "hostile") as runner:
                root = Path(directory)
                self.assertEqual(design_report.main(["--candidate", candidate, "--criterion", "hostile-evidence",
                                                    "--report", path], root=root), 2)
                runner.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    def test_report_publication_refuses_replacement_and_partial_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            design_report.publish(root, "test.json", {"report": 1}, {"evidence": 2})
            before = {p.name: p.read_bytes() for p in (root / ".hexaemeron/reports/conformance").iterdir()}
            with self.assertRaisesRegex(design_report.owner.Refusal, "report-exists"):
                design_report.publish(root, "test.json", {}, {})
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / ".hexaemeron/reports/conformance").iterdir()})
            (root / ".hexaemeron/reports/conformance/test.json").unlink()
            with self.assertRaisesRegex(design_report.owner.Refusal, "report-exists"):
                design_report.publish(root, "test.json", {}, {})

    def test_report_publication_refuses_a_linked_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "other"; target.mkdir()
            (root / ".hexaemeron").symlink_to(target, target_is_directory=True)
            with self.assertRaises((OSError, design_report.owner.Refusal)):
                design_report.publish(root, "test.json", {}, {})
            self.assertEqual(list(target.iterdir()), [])


