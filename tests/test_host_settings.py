"""The checked-in Claude Code attribution settings hold one object.

`INSTALL.md` documents `.claude/settings.json` as a shared project setting that
Claude Code reads from the checkout, holding one `attribution` object. Its
`commit`, `pr` and `sessionUrl` values are presentation preferences, not Fiat
policy: Fiat admits a validly signed commit whatever its bylines say. This
module pins the file's shape and its `sessionUrl` value.

A key added beside `attribution` would reach every session opened in this
clone, and the study that added the file put every addition to it on the
ask-first tier.
"""

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"


class HostSettingsTests(unittest.TestCase):
    def test_the_file_holds_one_attribution_object(self):
        self.assertTrue(SETTINGS.is_file(), f"{SETTINGS} is absent")
        document = json.loads(SETTINGS.read_text(encoding="utf-8"))
        self.assertIsInstance(document, dict)
        self.assertEqual(set(document), {"attribution"})
        self.assertIsInstance(document["attribution"], dict)
        self.assertEqual(set(document["attribution"]), {"commit", "pr", "sessionUrl"})
        # The settings reference types `commit` and `pr` as strings. The type is
        # shape and the text is a preference, so only the type is pinned: a
        # nested value would carry keys that neither key-set check above reads.
        self.assertIsInstance(document["attribution"]["commit"], str)
        self.assertIsInstance(document["attribution"]["pr"], str)

    def test_session_url_is_off(self):
        document = json.loads(SETTINGS.read_text(encoding="utf-8"))
        # `0 == False` in Python, so equality alone would let a zero through.
        self.assertIs(document["attribution"]["sessionUrl"], False)

    def test_the_file_ends_with_one_newline(self):
        raw = SETTINGS.read_bytes()
        self.assertTrue(raw.endswith(b"\n"), "no newline at end of file")
        self.assertFalse(raw.endswith(b"\n\n"), "more than one newline at end of file")


if __name__ == "__main__":
    unittest.main()
