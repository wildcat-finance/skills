"""The optional Claude presentation setting has no Fiat policy standing."""

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

    def test_fiat_does_not_consult_the_presentation_setting(self):
        controller = (ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(".claude/settings.json", controller)
        self.assertNotIn("HOST_BYLINE_RE", controller)


if __name__ == "__main__":
    unittest.main()
