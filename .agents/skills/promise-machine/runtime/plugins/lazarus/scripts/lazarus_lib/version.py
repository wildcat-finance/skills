"""The version Lazarus stamps into a fixture manifest as `tool_version`.

This is the writer's version, not the skill's. It appears inside every new
manifest this build writes. Historical fixtures retain the version that wrote
them only when a deterministic rebuild matches their exact manifest bytes;
schema version alone does not identify the writer that produced a capture.

So it moves when the writer or the format moves, and not when the skill's
frontier advances. The skill's evolution label lives in
`skills/lazarus/EVOLUTION.md` and the host manifests follow it; the two axes are
kept apart deliberately, and `tests/test_scaffold.py` holds them to that.
"""

__version__ = "0.2.0"

# The released manifest-v1 example has no receipt witness or receipt-trie
# relation. Its exact deterministic rebuild preserves the writer identity its
# existing bytes carry; fresh manifest-v1 and manifest-v2 output use the current
# writer above.
MANIFEST_V1_WRITER_VERSION = "0.1.0"
