#!/usr/bin/env python3
"""Regenerate the declared public schemas and complete fixture/case inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'plugins/hexaemeron/skills/fiat/scripts'))
from checkpoint_authority import conformance, schema
import test_checkpoint_authority_records as cases


def members(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from members(item)
        else:
            yield item.id()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = {conformance.CORPUS_ROOT + 'schemas/' + kind + '.schema.json':
               encoded(schema.document(kind)) for kind in schema.RECORD_TYPES}
    manifest = {'schema': 'checkpoint-authority-conformance-corpus/v1',
                'candidate': conformance.CANDIDATE, 'criteria': list(conformance.CRITERIA),
                'implemented_criteria': ['records-and-signatures'],
                'cases': sorted(members(unittest.defaultTestLoader.loadTestsFromModule(cases))),
                'files': [{'path': path, 'sha256': hashlib.sha256(outputs[path] if path in outputs
                          else (ROOT / path).read_bytes()).hexdigest()} for path in conformance.CORPUS_FILES]}
    outputs[conformance.MANIFEST_PATH] = encoded(manifest)
    drift = []
    for relative, data in outputs.items():
        path = ROOT / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                drift.append(relative)
        else:
            path.write_bytes(data)
    print(json.dumps({'schemas': len(schema.RECORD_TYPES), 'files': len(manifest['files']),
                      'cases': len(manifest['cases']), 'drift': drift}, sort_keys=True))
    return bool(drift)


if __name__ == '__main__':
    raise SystemExit(main())
