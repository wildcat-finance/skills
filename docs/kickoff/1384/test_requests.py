"""Keep the delivered request inventory admissible to the pinned capture path."""

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / 'plugins/lazarus/scripts'))

from capture_requests import requests
from lazarus_lib.capture import _validate_capture_plan
from lazarus_lib.errors import FormatError
from lazarus_lib.schemas import validate_document


def plan(generation):
    scope = json.loads((ROOT / 'scope.json').read_text())
    anchor = scope['anchors'][generation]
    return {
        'schema_version': 2,
        'chain': {'chain_id': '0x1', 'network': 'ethereum-mainnet'},
        'block': {'number': hex(anchor['number']), 'hash': anchor['hash'],
                  'hash_source': 'accepted Alexandria capture'},
        'requests': requests(generation),
        'proof_targets': json.loads((ROOT / f'proof-targets-{generation}.json').read_text()),
        'limits': {'max_requests': 20000, 'max_component_bytes': 33554432,
                   'max_total_bytes': 536870912, 'max_elapsed_seconds': 3600},
        'anchor_sources': [{'source_id': 'recorded-capture'}],
    }


class CaptureInventoryTests(unittest.TestCase):
    def test_capture_accepts_both_inventories(self):
        for generation in ('v1', 'v2'):
            with self.subTest(generation=generation):
                document = plan(generation)
                validate_document('plan', document)
                try:
                    _validate_capture_plan(document)
                except FormatError as error:
                    self.fail(f'capture refused the declared inventory: {error}')

    def test_getter_reverts_remain_recordable(self):
        for generation in ('v1', 'v2'):
            calls = [row for row in requests(generation) if row['method'] == 'eth_call']
            self.assertTrue(calls)
            self.assertTrue(all(row['required'] is False for row in calls))

    def test_schema_alone_does_not_admit_proof_labels(self):
        document = copy.deepcopy(plan('v1'))
        document['requests'][0]['evidence'] = 'proof-backed'
        validate_document('plan', document)
        with self.assertRaisesRegex(FormatError, 'must be recorded-rpc'):
            _validate_capture_plan(document)


if __name__ == '__main__':
    unittest.main()
