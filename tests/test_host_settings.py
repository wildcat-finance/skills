"""The checked-in Claude Code attribution switch holds exactly one object.

ADR-016 makes a runtime host execution metadata, never an author, co-author or
byline, and Fiat refuses those identities at its receipts. Claude Code adds
them by default: a `Co-Authored-By` trailer naming the model on every commit,
an attribution line on every pull-request description and, from a cloud or
Remote Control session, a session link on both. Its settings reference
documents one object that turns all three off and lists `.claude/settings.json`
among the files it is read from, so this repository checks that object in and
pins it here (skills#617).

The pin is whole-document equality. A key added beside `attribution` would
reach every session opened in this clone, and the study that added the file
put every addition to it on the ask-first tier. The setting is not evidence:
Fiat still reads the pull-request body back and refuses the host defaults by
name whether or not the host honoured this file.
"""

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"
EXPECTED = {"attribution": {"commit": "", "pr": "", "sessionUrl": False}}


class HostSettingsTests(unittest.TestCase):
    def test_the_document_is_exactly_the_attribution_switch(self):
        self.assertTrue(SETTINGS.is_file(), f"{SETTINGS} is absent")
        document = json.loads(SETTINGS.read_text(encoding="utf-8"))
        self.assertEqual(document, EXPECTED)
        # `0 == False` in Python, so equality alone would let a zero through.
        self.assertIs(document["attribution"]["sessionUrl"], False)

    def test_no_key_beyond_the_attribution_object_is_present(self):
        document = json.loads(SETTINGS.read_text(encoding="utf-8"))
        self.assertEqual(set(document), {"attribution"})
        self.assertEqual(set(document["attribution"]), {"commit", "pr", "sessionUrl"})

    def test_the_file_ends_with_one_newline(self):
        raw = SETTINGS.read_bytes()
        self.assertTrue(raw.endswith(b"\n"), "no newline at end of file")
        self.assertFalse(raw.endswith(b"\n\n"), "more than one newline at end of file")


if __name__ == "__main__":
    unittest.main()
