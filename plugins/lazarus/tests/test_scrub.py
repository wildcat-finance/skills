"""Provider credentials and prose never become fixture diagnostics."""

import inspect
from pathlib import Path
import tempfile
import unittest

from lazarus_lib.canonical import dumps
from lazarus_lib.errors import IntegrityError, ResourceLimitError
from lazarus_lib.scrub import (
    SCAN_CHUNK_BYTES,
    assert_no_secret_bytes,
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
        url = (
            "https://alice:pass%40word@rpc.example/v1"
            "?apiKey=shh-secret&project=wildcat"
        )
        secrets = provider_secrets(url)
        for value in (
            url,
            "alice",
            "pass@word",
            "apiKey",
            "shh-secret",
            "project",
            "wildcat",
        ):
            self.assertIn(value, secrets)

    def test_url_path_credentials_and_percent_case_variants_are_secret_material(self):
        url = "https://rpc.example/v3/path%2Fcredential-value"
        secrets = provider_secrets(url)
        for value in (
            "path%2Fcredential-value",
            "path%2fcredential-value",
            "path/credential-value",
        ):
            with self.subTest(value=value):
                self.assertIn(value, secrets)
                with self.assertRaisesRegex(IntegrityError, "secret"):
                    assert_no_secret_bytes(
                        f'{{"result":"{value}"}}'.encode(),
                        secrets,
                        label="capture terminal result",
                    )

    def test_url_authority_and_fragment_parts_are_secret_material(self):
        url = (
            "https://authority-credential.rpc.example/v3/public"
            "#session=fragment-credential"
        )
        secrets = provider_secrets(url)
        for value in (
            "authority-credential.rpc.example",
            "authority-credential",
            "fragment-credential",
        ):
            with self.subTest(value=value):
                self.assertIn(value, secrets)
                with self.assertRaisesRegex(IntegrityError, "secret"):
                    assert_no_secret_bytes(
                        f'{{"result":"{value}"}}'.encode(),
                        secrets,
                        label="capture terminal result",
                    )

    def test_mixed_case_and_nested_percent_spellings_are_secret_material(self):
        url = (
            "https://rpc.example/v3/a%2Fb%3Acredential/"
            "double%252Fcredential"
        )
        secrets = provider_secrets(url)
        for value in (
            "a%2fb%3Acredential",
            "a/b:credential",
            "double/credential",
            "credential",
            "cre%64ential",
            "cre%2564ential",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(IntegrityError, "secret"):
                    assert_no_secret_bytes(
                        f'{{"result":"{value}"}}'.encode(),
                        secrets,
                        label="capture terminal result",
                    )

    def test_query_plus_and_percent_space_are_equivalent_secret_spellings(self):
        secrets = provider_secrets(
            "https://rpc.example/v3?token=space+credential"
        )
        with self.assertRaisesRegex(IntegrityError, "secret"):
            assert_no_secret_bytes(
                b'{"result":"space%20credential"}',
                secrets,
                label="capture terminal result",
            )

    def test_secret_scan_fails_closed_beyond_percent_decode_limit(self):
        spelling = "cre%64ential"
        for _ in range(8):
            spelling = spelling.replace("%", "%25")
        with self.assertRaisesRegex(IntegrityError, "secret"):
            assert_no_secret_bytes(
                spelling.encode(),
                {"credential"},
                label="capture terminal result",
            )

    def test_encoded_url_credentials_are_scanned_in_their_raw_form(self):
        url = (
            "https://alice%40account:pass%2Fword@rpc.example/"
            "?token=alpha%2Fencoded-secret"
        )
        secrets = provider_secrets(url)
        for value in (
            "alice%40account",
            "pass%2Fword",
            "alpha%2Fencoded-secret",
        ):
            self.assertIn(value, secrets)
            with self.assertRaisesRegex(IntegrityError, "secret"):
                assert_no_secret_bytes(
                    f'{{"result":"{value}"}}'.encode(),
                    secrets,
                    label="capture terminal result",
                )

    def test_json_escaped_secret_is_refused_in_terminal_bytes(self):
        marker = 'alpha"escaped-secret'
        secrets = provider_secrets(
            "https://rpc.example/?token=alpha%22escaped-secret"
        )
        with self.assertRaisesRegex(IntegrityError, "terminal result"):
            assert_no_secret_bytes(
                dumps({"result": marker}),
                secrets,
                label="capture terminal result",
            )

    def test_json_escaped_secret_is_refused_in_staged_files(self):
        marker = 'alpha"escaped-secret'
        secrets = provider_secrets(
            "https://rpc.example/?token=alpha%22escaped-secret"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rpc.jsonl"
            path.write_bytes(dumps({"result": marker}) + b"\n")
            with self.assertRaisesRegex(IntegrityError, "secret"):
                assert_no_secrets(directory, secrets)

    def test_bearer_and_cookie_values_are_secret_material(self):
        headers = {
            "Authorization": "Bearer bearer-secret",
            "Cookie": "session=cookie-secret; theme=dark",
            "X-API-Key": "custom-header-secret",
        }
        secrets = provider_secrets("https://rpc.example", headers)
        for value in ("bearer-secret", "cookie-secret", "dark", "custom-header-secret"):
            self.assertIn(value, secrets)

    def test_short_credential_values_are_refused_instead_of_dropped(self):
        cases = (
            ("https://u:p@rpc.example/", None),
            ("https://rpc.example/?token=abc", None),
            ("https://rpc.example/?token=%61bc", None),
            ("https://rpc.example/", {"X-API-Key": "z"}),
            (
                "https://rpc.example/",
                {"Authorization": "Basic dTpsb25nLXBhc3N3b3Jk"},
            ),
        )
        for url, headers in cases:
            with self.subTest(url=url, headers=headers):
                with self.assertRaisesRegex(ResourceLimitError, "shorter"):
                    provider_secrets(url, headers)

    def test_short_delimited_credential_components_are_refused(self):
        cases = (
            (
                "https://rpc.example/",
                {"Authorization": 'Digest nonce="abc", realm="longrealm"'},
            ),
            (
                "https://rpc.example/?token=prefix%3Aabc",
                None,
            ),
            (
                "https://rpc.example/",
                {"X-API-Key": "prefix=abc; scope=longscope"},
            ),
        )
        for url, headers in cases:
            with self.subTest(url=url, headers=headers):
                with self.assertRaisesRegex(ResourceLimitError, "shorter"):
                    provider_secrets(url, headers)

    def test_short_public_url_structure_is_not_a_credential_false_positive(self):
        url = "https://a.rpc.example/v3?x="
        secrets = provider_secrets(url)
        self.assertIn(url, secrets)
        for public_component in ("a", "v3", "x"):
            self.assertNotIn(public_component, secrets)

    def test_public_provider_port_is_not_a_secret_fragment(self):
        url = "http://127.0.0.1:41119/rpc"
        secrets = provider_secrets(url)
        self.assertIn(url, secrets)
        self.assertIn("127.0.0.1:41119", secrets)
        self.assertNotIn("41119", secrets)
        assert_no_secret_bytes(
            b'{"ordinary_fixture_value":"41119"}',
            secrets,
            label="capture terminal result",
        )

    def test_header_count_is_bounded_before_materialising_the_mapping(self):
        class StreamingHeaders:
            yielded = 0

            def __bool__(self):
                return True

            def items(self):
                for index in range(1_000):
                    self.yielded += 1
                    yield f"X-Header-{index}", "long-header-value"

        headers = StreamingHeaders()
        with self.assertRaisesRegex(ResourceLimitError, "headers"):
            provider_secrets("https://rpc.example", headers)
        self.assertEqual(headers.yielded, 65)

    def test_provider_classifier_rechecks_the_elapsed_budget(self):
        self.assertIn(
            "check_time", inspect.signature(provider_secrets).parameters
        )
        self.assertIn(
            "check_time", inspect.signature(provider_secret_union).parameters
        )
        checks = 0

        def check_time():
            nonlocal checks
            checks += 1
            if checks == 3:
                raise ResourceLimitError("elapsed")

        with self.assertRaisesRegex(ResourceLimitError, "elapsed"):
            provider_secret_union(
                (("https://rpc.example/path/credential", None),),
                check_time=check_time,
            )
        self.assertEqual(checks, 3)

    def test_every_authorization_payload_is_secret_material(self):
        headers = {
            "Authorization": "Basic dXNlcjpiYXNpYy1jcmVkZW50aWFs",
            "Proxy-Authorization": 'Digest nonce="digest-credential"',
        }
        secrets = provider_secrets("https://rpc.example", headers)
        for value in (
            "dXNlcjpiYXNpYy1jcmVkZW50aWFs",
            "basic-credential",
            "digest-credential",
        ):
            with self.subTest(value=value):
                self.assertIn(value, secrets)
                with self.assertRaisesRegex(IntegrityError, "secret"):
                    assert_no_secret_bytes(
                        f'{{"result":"{value}"}}'.encode(),
                        secrets,
                        label="capture terminal result",
                    )

    def test_provider_secret_classifier_bounds_component_cardinality(self):
        url = "https://rpc.example/" + "/".join(
            f"credential-{index:04d}" for index in range(1_100)
        )
        with self.assertRaisesRegex(ResourceLimitError, "too many"):
            provider_secrets(url)

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

    def test_redaction_detects_mixed_percent_escape_case(self):
        self.assertEqual(
            redact_text("path%2fcredential", secrets={"path%2Fcredential"}),
            "[x]",
        )

    def test_redaction_placeholder_does_not_repeat_the_secret(self):
        self.assertNotIn("redacted", redact_text("redacted", secrets={"redacted"}))

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

    def test_secret_scan_decodes_an_escape_split_across_streaming_chunks(self):
        marker = b"raw-credential"
        encoded = b"raw%2dcredential"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "component.jsonl"
            path.write_bytes(
                b"x" * (SCAN_CHUNK_BYTES - 5) + encoded + b"\n"
            )
            with self.assertRaisesRegex(IntegrityError, "secret"):
                assert_no_secrets(directory, {marker.decode()})

    def test_secret_scan_rechecks_the_elapsed_budget_between_chunks(self):
        self.assertIn(
            "check_time", inspect.signature(assert_no_secrets).parameters
        )
        checks = 0

        def check_time():
            nonlocal checks
            checks += 1
            if checks == 3:
                raise ResourceLimitError("elapsed")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "component.json"
            path.write_bytes(b"x" * (SCAN_CHUNK_BYTES * 3))
            with self.assertRaisesRegex(ResourceLimitError, "elapsed"):
                assert_no_secrets(
                    directory,
                    {"absent-secret"},
                    check_time=check_time,
                )
        self.assertEqual(checks, 3)

    def test_terminal_result_bytes_use_the_same_provider_secret_union(self):
        with self.assertRaisesRegex(IntegrityError, "terminal result"):
            assert_no_secret_bytes(
                b'{"correlation_id":"anchor-terminal-secret"}',
                {"primary-terminal-secret", "anchor-terminal-secret"},
                label="capture terminal result",
            )

    def test_terminal_byte_scan_rechecks_the_elapsed_budget(self):
        self.assertIn(
            "check_time", inspect.signature(assert_no_secret_bytes).parameters
        )

        def check_time():
            raise ResourceLimitError("elapsed")

        with self.assertRaisesRegex(ResourceLimitError, "elapsed"):
            assert_no_secret_bytes(
                b'{"result":"public"}',
                {"absent-secret"},
                label="capture terminal result",
                check_time=check_time,
            )


if __name__ == "__main__":
    unittest.main()
