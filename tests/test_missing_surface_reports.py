"""A missing runner prerequisite is an error, not a failed guard assertion."""

import tempfile
import unittest
from pathlib import Path

from tests import (
    emit_contributors_report,
    emit_dead_code_report,
    emit_emitter_declarations_report,
    emit_run_observation_report,
)


class MissingSurfaceReportTests(unittest.TestCase):
    def test_each_runner_reports_an_absent_surface_as_an_error(self):
        emitters = (
            emit_contributors_report,
            emit_dead_code_report,
            emit_emitter_declarations_report,
            emit_run_observation_report,
        )
        with tempfile.TemporaryDirectory() as empty:
            for emitter in emitters:
                with self.subTest(emitter=emitter.__name__):
                    suite = emitter.missing_surface_suite(Path(empty))
                    self.assertIsNotNone(suite)
                    result = unittest.TestResult()
                    suite.run(result)
                    self.assertEqual(result.testsRun, 1)
                    self.assertEqual(len(result.failures), 0)
                    self.assertEqual(len(result.errors), 1)
                    payload = emitter.result_payload(result)
                    self.assertEqual(payload["failures"], 0)
                    self.assertEqual(payload["errors"], 1)
