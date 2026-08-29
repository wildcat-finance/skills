"""The Goldfinch example README stays bound to its manifest digest.

Anchored in lazarus's own suite so the check runs when the example changes
rather than on every unrelated gated change (it lived in
tests/test_marketplace_prose.py until the test-scoping de-duplication). Pure
hashlib/JSON, so it does not pull the lazarus runtime dependencies.
"""

from pathlib import Path
import hashlib
import json
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN_ROOT / "examples" / "goldfinch-v0"


class ExampleReadmeDigestTests(unittest.TestCase):
    def test_lazarus_release_readme_remains_digest_bound(self):
        manifest = json.loads((EXAMPLE / "manifest.json").read_text(encoding="utf-8"))
        files = {entry["path"]: entry["sha256"] for entry in manifest["components"]}
        readme = EXAMPLE / "README.md"
        self.assertEqual(hashlib.sha256(readme.read_bytes()).hexdigest(), files["README.md"])


if __name__ == "__main__":
    unittest.main()
