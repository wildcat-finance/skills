"""Reports written now keep a fresh timestamp when automatic stamps lag."""

import contextlib
import io
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

from test_elenchus_checker import elenchus, hexaemeron_runner as producer


class RunnerReportFreshnessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="runner-report-freshness-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        with contextlib.chdir(self.root):
            self.target = producer.bind_report_target("report.json", producer.argument_parser())
        self.path = self.root / "report.json"
        result = unittest.TestResult()
        unittest.FunctionTestCase(lambda: None).run(result)
        self.payload = producer.result_payload(result)

    def test_new_report_is_accepted_when_automatic_write_timestamps_lag(self):
        started = time.time_ns()
        native_write = os.write
        native_utime = os.utime

        def write_with_coarse_timestamp(descriptor, data):
            written = native_write(descriptor, data)
            native_utime(descriptor, ns=(0, started - 2_000_000))
            return written

        with mock.patch.object(producer.os, "write", side_effect=write_with_coarse_timestamp):
            producer.write_report(self.target, self.payload)
        report = elenchus.read_report(self.path, "unittest-json-v1", started, self.root)
        self.assertEqual(1, report.executed)
        self.assertTrue(report.complete)

    def test_stale_report_is_still_refused(self):
        producer.write_report(self.target, self.payload)
        os.utime(self.path, ns=(1, 1))
        with self.assertRaisesRegex(elenchus.ReportError, "stale"):
            elenchus.read_report(self.path, "unittest-json-v1", time.time_ns(), self.root)

    def test_timestamp_failure_removes_the_new_report(self):
        with mock.patch.object(producer.os, "utime", side_effect=OSError("timestamp unavailable")):
            with self.assertRaisesRegex(OSError, "timestamp unavailable"):
                producer.write_report(self.target, self.payload)
        self.assertFalse(self.path.exists())

    def test_missing_descriptor_timestamp_support_refuses_before_writing(self):
        supported = os.supports_fd - {os.utime}
        error = io.StringIO()
        with mock.patch.object(producer.os, "supports_fd", supported):
            with contextlib.chdir(self.root), contextlib.redirect_stderr(error):
                with self.assertRaises(SystemExit) as refused:
                    producer.bind_report_target("report.json", producer.argument_parser())
        self.assertEqual(2, refused.exception.code)
        self.assertIn("os.utime(fd)", error.getvalue())
        self.assertFalse(self.path.exists())
