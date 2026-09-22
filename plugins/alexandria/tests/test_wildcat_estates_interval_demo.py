"""Whole-estate proof and hostile summaries, with real staging absence explicit."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/wildcat-estates-interval-v0'
spec = importlib.util.spec_from_file_location('wildcat_estates_demo', EXAMPLE / 'demo.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class WholeDemoBoundaryTests(unittest.TestCase):
    def test_metadata_check_states_that_no_rebuild_ran(self):
        with demo.offline():
            result = demo.verify_preserved()
        self.assertFalse(result['rebuild_performed'])
        self.assertEqual(result['scope'], 'committed-metadata-only')
        self.assertEqual({k: v['epochs'] for k, v in result['estates'].items()},
                         {'wildcat-v1': 16, 'wildcat-v2': 137})

    def test_missing_external_input_refuses_before_output(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ):
            os.environ.pop('ALEXANDRIA_WILDCAT_V1_STAGING', None)
            output = Path(directory) / 'build'
            with self.assertRaisesRegex(demo.AlexandriaError, 'ALEXANDRIA_WILDCAT_V1_STAGING'):
                demo.build(output)
            self.assertFalse(output.exists())

    def test_existing_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            sentinel = output / 'keep'
            sentinel.write_bytes(b'keep')
            with self.assertRaisesRegex(demo.AlexandriaError, 'already exists'):
                demo.build(output)
            self.assertEqual(sentinel.read_bytes(), b'keep')

    def test_network_guard_refuses_socket_construction_and_connection(self):
        with demo.offline():
            with self.assertRaisesRegex(demo.AlexandriaError, 'socket construction refused'):
                socket.socket()
            with self.assertRaisesRegex(demo.AlexandriaError, 'connection refused'):
                socket.create_connection(('unused.invalid', 443))

    def test_summary_read_refuses_symlink_and_oversized_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'other').write_bytes(b'{}')
            (root / 'summary.json').symlink_to(root / 'other')
            with self.assertRaises(demo.AlexandriaError):
                demo.read(root, 'summary.json')
            (root / 'summary.json').unlink()
            (root / 'summary.json').write_bytes(b'{}\n')
            with mock.patch.object(demo, 'MAX_RAW_COMPONENT_BYTES', 2):
                with self.assertRaises(demo.AlexandriaError):
                    demo.read(root, 'summary.json')


class WholePreservedRebuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for variable in ('ALEXANDRIA_WILDCAT_V1_STAGING', 'ALEXANDRIA_WILDCAT_V2_STAGING'):
            if not os.environ.get(variable):
                raise unittest.SkipTest(f'not run: {variable} does not name preserved staging')
        cls.temporary = tempfile.TemporaryDirectory(prefix='whole-estates-test-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name) / 'built'
        cls.observed = demo.build(cls.output)

    def test_both_real_estates_and_compound_recompute_the_entire_pin(self):
        checked = demo.verify(self.output)
        self.assertEqual(checked, self.observed)
        self.assertEqual(checked['compound_pattern_rows'], 9)
        self.assertEqual(checked['v1_source_identities'], 16)
        self.assertEqual(checked['v1_missing_deployment_blocks'], 12)
        self.assertEqual(checked['shared_log_counts']['wildcat-v1'], {
            '0x437e0551892c2c9b06d3ffd248fe60572e08cd1a': 0,
            '0xfeb516d9d946dd487a9346f6fee11f40c6945ee4': 54,
        })
        self.assertEqual(len(checked['refusals']), 7)
        self.assertEqual(checked['coverage_fields']['coverage'],
                         ['collections', 'gaps', 'record_count', 'status', 'unsupported_collections'])

    def test_forged_success_summary_cannot_replace_recomputed_evidence(self):
        path = self.output / 'summary.json'
        original = path.read_bytes()
        forged = json.loads(original)
        forged['v1_source_identities'] = 0
        path.write_bytes(demo.canonical_bytes(forged))
        try:
            with self.assertRaisesRegex(demo.AlexandriaError, 'summary differs'):
                demo.verify(self.output)
        finally:
            path.write_bytes(original)
