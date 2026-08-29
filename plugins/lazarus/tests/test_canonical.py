"""Canonical JSON stays strict and byte-stable."""

from pathlib import Path
import os
import tempfile
import traceback
import unittest

from lazarus_lib.canonical import dump, dump_jsonl, dumps, load, load_jsonl, loads
from lazarus_lib.errors import FormatError, ResourceLimitError


class CanonicalTests(unittest.TestCase):
    def assert_value_free_refusal(self, source, protected):
        with self.assertRaises(FormatError) as raised:
            loads(source)
        error = raised.exception
        surfaces = {
            "message": str(error),
            "args": repr(error.args),
            "repr": repr(error),
            "cause": repr(error.__cause__),
            "context": repr(error.__context__),
            "traceback": "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            ),
        }
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        for name, rendered in surfaces.items():
            with self.subTest(surface=name):
                self.assertNotIn(protected, rendered)
                self.assertLessEqual(len(rendered.encode("utf-8")), 4096)

    def test_object_insertion_order_does_not_change_bytes(self):
        left = {"z": [2, 1], "a": {"b": True, "a": None}}
        right = {"a": {"a": None, "b": True}, "z": [2, 1]}
        self.assertEqual(dumps(left), dumps(right))
        self.assertEqual(dumps(left), b'{"a":{"a":null,"b":true},"z":[2,1]}')
        self.assertEqual(dumps({"text": "caf\u00e9"}), b'{"text":"caf\xc3\xa9"}')

    def test_json_and_jsonl_have_one_trailing_newline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(dump(root / "one.json", {"b": 2, "a": 1}), b'{"a":1,"b":2}\n')
            data = dump_jsonl(root / "rows.jsonl", [{"id": 2}, {"id": 1}], sort_key=lambda row: row["id"])
            self.assertEqual(data, b'{"id":1}\n{"id":2}\n')
            self.assertEqual(load_jsonl(root / "rows.jsonl"), [{"id": 1}, {"id": 2}])

    def test_duplicate_keys_and_non_integer_numbers_fail(self):
        with self.assertRaisesRegex(FormatError, "duplicate JSON key"):
            loads(b'{"a":1,"a":2}')
        for source in (b'{"n":1.5}', b'{"n":NaN}', b'{"n":Infinity}'):
            with self.subTest(source=source), self.assertRaises(FormatError):
                loads(source)

    def test_json_parse_refusals_do_not_echo_hostile_lexemes(self):
        prefix = "PRIVATE_PROVIDER_VALUE_"
        for marker in (prefix + "SECRET", prefix + "x" * 200_000):
            duplicate = f'{{"{marker}":0,"{marker}":1}}'.encode("utf-8")
            with self.subTest(shape="duplicate-key", size=len(marker)):
                self.assert_value_free_refusal(duplicate, prefix)

            malformed = f'{{"value":"{marker}'.encode("utf-8")
            with self.subTest(shape="malformed-value", size=len(marker)):
                self.assert_value_free_refusal(malformed, prefix)

            invalid_utf8 = b'{"value":"' + marker.encode("utf-8") + b'\xff"}'
            with self.subTest(shape="invalid-utf8", size=len(marker)):
                self.assert_value_free_refusal(invalid_utf8, prefix)

        for number in ("314159.265358", "314159." + "2" * 200_000):
            with self.subTest(shape="number", size=len(number)):
                self.assert_value_free_refusal(
                    f'{{"value":{number}}}'.encode("utf-8"), "314159."
                )

    def test_json_strings_refuse_surrogate_code_points_as_format_errors(self):
        cases = (
            ("loaded value", lambda: loads(b'{"value":"\\ud800"}')),
            ("loaded key", lambda: loads(b'{"\\udfff":0}')),
            ("dumped value", lambda: dumps({"value": "\ud800"})),
            ("dumped key", lambda: dumps({"\udfff": 0})),
        )
        for name, operation in cases:
            caught = None
            try:
                operation()
            except Exception as error:  # The assertion below classifies the boundary.
                caught = error
            with self.subTest(name=name):
                self.assertIsNotNone(caught)
                self.assertIsInstance(caught, FormatError)
                self.assertIn("surrogate code point", str(caught))
                self.assertIsNone(caught.__cause__)
                self.assertIsNone(caught.__context__)

    def test_invalid_utf8_and_unsupported_values_fail(self):
        with self.assertRaisesRegex(FormatError, "not UTF-8"):
            loads(b'"\xff"')
        with self.assertRaisesRegex(FormatError, "unsupported JSON value"):
            dumps({"bad": {1, 2}})

    def test_byte_depth_record_and_count_limits_fail_closed(self):
        with self.assertRaises(ResourceLimitError):
            loads(b'{"a":1}', max_bytes=3)
        nested = None
        for _ in range(66):
            nested = [nested]
        with self.assertRaises(ResourceLimitError):
            dumps(nested)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = Path(directory) / "rows.jsonl"
            path.write_bytes(b'{"a":1}\n{"a":2}\n')
            with self.assertRaises(ResourceLimitError):
                load_jsonl(path, max_records=1)
            with self.assertRaises(ResourceLimitError):
                load_jsonl(path, max_record_bytes=4)
            with self.assertRaises(ResourceLimitError):
                dump(root / "large.json", {"value": "abcdef"}, max_bytes=4)
            with self.assertRaises(ResourceLimitError):
                dump_jsonl(path, [{"value": "abcdef"}], max_record_bytes=4)
            with self.assertRaises(ResourceLimitError):
                dump_jsonl(path, [{"a": 1}, {"b": 2}], max_bytes=8)

    def test_jsonl_requires_nonempty_newline_terminated_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl"
            path.write_bytes(b'{"a":1}')
            with self.assertRaisesRegex(FormatError, "trailing newline"):
                load_jsonl(path)
            path.write_bytes(b'\n')
            with self.assertRaisesRegex(FormatError, "empty"):
                load_jsonl(path)

    def test_jsonl_record_limit_stops_an_oversized_iterable(self):
        consumed = []

        def records():
            for number in range(100):
                consumed.append(number)
                yield {"number": number}

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ResourceLimitError):
                dump_jsonl(Path(directory) / "rows.jsonl", records(), max_records=2)
        self.assertEqual(consumed, [0, 1, 2])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are POSIX-only")
    def test_direct_loaders_reject_a_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            os.mkfifo(path)
            with self.assertRaisesRegex(FormatError, "regular file"):
                load(path)
            with self.assertRaisesRegex(FormatError, "regular file"):
                load_jsonl(path)


if __name__ == "__main__":
    unittest.main()
