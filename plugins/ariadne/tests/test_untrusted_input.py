"""Bounds on a document that arrived from somebody else."""

import json
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, safejson  # noqa: E402


class SizeTests(unittest.TestCase):
    def test_a_document_over_the_cap_is_refused_by_size(self):
        data = b'{"a":"' + b"x" * 200 + b'"}'
        with self.assertRaises(safejson.InputError) as caught:
            safejson.loads(data, max_bytes=64)
        self.assertIn("over the 64 byte cap", str(caught.exception))

    def test_a_document_under_the_cap_parses(self):
        self.assertEqual(safejson.loads(b'{"a":1}', max_bytes=64), {"a": 1})


class DepthTests(unittest.TestCase):
    def test_nesting_past_the_cap_is_refused_before_parsing(self):
        data = ("[" * 100 + "]" * 100).encode()
        with self.assertRaises(safejson.InputError) as caught:
            safejson.loads(data, max_depth=64)
        self.assertIn("refused before parsing", str(caught.exception))

    def test_the_depth_counter_ignores_brackets_inside_strings(self):
        data = json.dumps({"a": "[[[[[[[[[[" * 20}).encode()
        self.assertIn("a", safejson.loads(data, max_depth=8))

    def test_an_escaped_quote_does_not_end_a_string(self):
        data = json.dumps({"a": '\\" [[[[[[[[' * 10}).encode()
        self.assertIn("a", safejson.loads(data, max_depth=8))

    def test_nesting_deep_enough_to_exhaust_the_stack_never_reaches_the_parser(self):
        data = ('{"a":' * 200000 + "1" + "}" * 200000).encode()
        with self.assertRaises(safejson.InputError):
            safejson.loads(data)


class BoundsTests(unittest.TestCase):
    def test_a_non_positive_bound_is_refused_rather_than_refusing_everything(self):
        for bounds in ({"max_bytes": 0}, {"max_depth": 0}, {"max_bytes": -1}):
            with self.assertRaises(safejson.InputError) as caught:
                safejson.loads(b"{}", **bounds)
            self.assertIn("bounds must be positive", str(caught.exception))


class DuplicateKeyTests(unittest.TestCase):
    def test_a_repeated_key_is_refused(self):
        data = b'{"predicateType":"a:b","predicateType":"c:d"}'
        with self.assertRaises(safejson.InputError) as caught:
            safejson.loads(data)
        self.assertIn("duplicate key", str(caught.exception))

    def test_the_same_key_in_two_different_objects_is_fine(self):
        data = b'{"one":{"name":"a"},"two":{"name":"b"}}'
        self.assertEqual(safejson.loads(data)["two"]["name"], "b")


class JsonGrammarTests(unittest.TestCase):
    def test_non_json_numeric_constants_are_refused(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(safejson.InputError):
                    safejson.loads(('{"value": %s}' % value).encode("ascii"))

    def test_exponent_overflow_is_refused_before_it_becomes_infinity(self):
        for value in ("1e9999", "-1e9999"):
            with self.subTest(value=value):
                with self.assertRaises(safejson.InputError):
                    safejson.loads(('{"value": %s}' % value).encode("ascii"))

    def test_integral_json_number_forms_keep_integer_semantics(self):
        for value, expected in (("1.0", 1), ("1e2", 100), ("-0.0", 0)):
            with self.subTest(value=value):
                parsed = safejson.loads(('{"value": %s}' % value).encode("ascii"))
                self.assertIs(type(parsed["value"]), int)
                self.assertEqual(parsed["value"], expected)
        self.assertIs(type(safejson.loads(b'{"value": 1.5}')["value"]), float)

    def test_an_oversized_integer_is_a_controlled_input_refusal(self):
        try:
            safejson.loads(('{"value": %s}' % ("9" * 5000)).encode("ascii"))
        except safejson.InputError as error:
            self.assertIn("integer", str(error))
        except ValueError as error:
            self.fail("raw ValueError escaped the input boundary: %s" % error)
        else:
            self.fail("oversized integer was accepted")


class ThroughTheReaderTests(unittest.TestCase):
    """The bounds apply to the envelope and to the payload inside it."""

    def test_a_deeply_nested_payload_inside_an_envelope_is_refused(self):
        payload = ('{"a":' * 100 + "1" + "}" * 100).encode()
        wrapped = envelope.wrap(payload).to_json()
        with self.assertRaises(safejson.InputError):
            envelope.read(wrapped, safejson.loader(max_depth=16))

    def test_a_duplicate_key_in_a_payload_is_refused(self):
        payload = b'{"_type":"x","_type":"y"}'
        wrapped = envelope.wrap(payload).to_json()
        with self.assertRaises(safejson.InputError):
            envelope.read(wrapped)

    def test_an_ordinary_document_passes_the_bounds(self):
        payload = json.dumps(
            {
                "_type": "https://in-toto.io/Statement/v1",
                "subject": [{"name": "a", "digest": {"sha256": "ab" * 32}}],
                "predicateType": "https://example.test/x/v1",
            }
        ).encode()
        document = envelope.read(envelope.wrap(payload).to_json())
        self.assertEqual(document.payload, payload)


if __name__ == "__main__":
    unittest.main()
