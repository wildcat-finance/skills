"""Schema and runtime agree on the additive Wildcat header marker."""

from copy import deepcopy
import json
from pathlib import Path
import unittest
import tempfile
from tests.test_wildcat_venue import fixture, schema_errors
from alexandria_lib import event_headers, interval
from alexandria_lib.errors import AlexandriaError


class EventHeaderSchemaTests(unittest.TestCase):
    def test_schema_and_runtime_admit_only_supported_marker(self):
        root = Path(__file__).resolve().parents[1]
        for version in (1, 2):
            schema = json.loads((root / f"schemas/interval-plan-v{version}.schema.json").read_bytes())
            plan = deepcopy(fixture()["plan"])
            if version == 1:
                plan["proxy"] = plan.pop("subjects")[0]
                plan["format"] = interval.PLAN_FORMAT
            self.assertEqual(schema_errors(schema, plan), [])
            interval.validate_plan(plan)
            plan[event_headers.FIELD] = event_headers.RULE
            self.assertEqual(schema_errors(schema, plan), [])
            interval.validate_plan(plan)
            for key, value in ((event_headers.FIELD, None), (event_headers.FIELD, True),
                               (event_headers.FIELD, "unknown"), ("venue", "compound-v3"),
                               ("evidence_classes", ["boundary-blocks"])):
                bad = dict(plan, **{key: value})
                with self.subTest(version=version, key=key, value=value):
                    self.assertTrue(schema_errors(schema, bad))
                    with self.assertRaises(AlexandriaError):
                        interval.validate_plan(bad)

    def test_checkpoint_schema_admits_actual_opted_in_digest(self):
        root = Path(__file__).resolve().parents[1]
        for split in (False, True):
            plan = deepcopy(fixture()["plan"])
            plan[event_headers.FIELD] = event_headers.RULE
            if split:
                plan["shards_per_component"] = 1
            with self.subTest(split=split), tempfile.TemporaryDirectory() as temporary:
                staging = interval.Staging(Path(temporary), plan)
                staging.resume()
                checkpoint = staging.commit(0, plan["shards"][0]["end"], "0x" + "ab" * 32)
                version = 2 if split else 1
                schema = json.loads((root / f"schemas/interval-checkpoint-v{version}.schema.json").read_bytes())
                self.assertEqual(schema_errors(schema, checkpoint), [])
                interval.validate_checkpoint(checkpoint, staging.digest, staging.shard_count, staging.classes, staging.ranges)
                for value in (None, True, "bad"):
                    bad = dict(checkpoint, event_headers_sha256=value)
                    self.assertTrue(schema_errors(schema, bad))
                    with self.assertRaises(AlexandriaError):
                        interval.validate_checkpoint(bad, staging.digest, staging.shard_count, staging.classes, staging.ranges)
                staging.close()
