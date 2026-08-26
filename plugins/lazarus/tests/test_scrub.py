"""Provider credentials and prose never become fixture diagnostics."""

from pathlib import Path
import tempfile
import unittest

from lazarus_lib.errors import IntegrityError
from lazarus_lib.scrub import (
    SCAN_CHUNK_BYTES,
    assert_no_secrets,
    provider_secrets,
    provider_secret_union,
    redact_text,
    sanitised_rpc_error,
)


class ScrubTests(unittest.TestCase):
    def test_secret_union_covers_primary_headers_and_every_anchor_url(self):
        secrets = provider_secret_union(
            (
                ("https://primary.example/?key=primary-secret", {"Authorization": "Bearer header-secret"}),
                ("https://anchor-a.example/?key=anchor-a-secret", None),
                ("https://anchor-b.example/?key=anchor-b-secret", None),
            )
        )
        for value in (
            "primary-secret",
            "header-secret",
            "anchor-a-secret",
            "anchor-b-secret",
        ):
            self.assertIn(value, secrets)

    def test_url_userinfo_and_query_keys_are_secret_material(self):
        url = "https://alice:p%40ss@rpc.example/v1?apiKey=shh-secret&project=wildcat"
        secrets = provider_secrets(url)
        for value in (url, "alice", "p@ss", "apiKey", "shh-secret", "project", "wildcat"):
            self.assertIn(value, secrets)

    def test_bearer_and_cookie_values_are_secret_material(self):
        headers = {
            "Authorization": "Bearer bearer-secret",
            "Cookie": "session=cookie-secret; theme=dark",
            "X-API-Key": "custom-header-secret",
        }
        secrets = provider_secrets("https://rpc.example", headers)
        for value in ("bearer-secret", "cookie-secret", "dark", "custom-header-secret"):
            self.assertIn(value, secrets)

    def test_provider_error_text_and_data_are_discarded(self):
        error = sanitised_rpc_error(
            {"code": -32001, "message": "bad bearer-secret", "data": {"url": "secret"}}
        )
        self.assertEqual(error, {"code": -32001, "message": "provider request failed"})
        self.assertNotIn("secret", str(error))

    def test_redaction_covers_urls_bearers_cookies_and_known_values(self):
        text = (
            "POST https://user:pass@rpc.example/?key=query-secret "
            "Authorization: Bearer bearer-secret Cookie: sid=cookie-secret"
        )
        scrubbed = redact_text(text, secrets={"query-secret"})
        for secret in ("user", "pass", "query-secret", "bearer-secret", "cookie-secret"):
            self.assertNotIn(secret, scrubbed)

    def test_final_output_scan_fails_on_a_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "component.json"
            path.write_text('{"value":"bearer-secret"}\n', encoding="utf-8")
            with self.assertRaisesRegex(IntegrityError, "secret"):
                assert_no_secrets(directory, {"bearer-secret"})

    def test_secret_scan_detects_a_value_across_streaming_chunks(self):
        marker = bytes(range(32, 64))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "component.jsonl"
            path.write_bytes(b"x" * (SCAN_CHUNK_BYTES - 5) + marker + b"\n")
            with self.assertRaisesRegex(IntegrityError, "secret"):
                assert_no_secrets(directory, {marker.decode()})


if __name__ == "__main__":
    unittest.main()
