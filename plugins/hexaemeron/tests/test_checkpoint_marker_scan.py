"""Regression guards for public audit quotations rejected as key material."""

from __future__ import annotations

from functools import cache
import hashlib
import importlib.util
from pathlib import Path
import stat
import sys
import tracemalloc
import unittest


ROOT = Path(__file__).resolve().parents[3]
CONTROLLER = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
AUDIT_SOURCE = (
    "audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md",
    376713,
    "bce008b201071b1ded3e656e24c0bfabb67923932a2cb3a994cb260172d6709c",
)
AUDIT_SYNOPSIS = (
    "audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.synopsis.md",
    378244,
    "86bab9bce5db6b37a67527336bbfb1f65036a4f3ff504e50914be416be3934b2",
)


def public_fixture(specification: tuple[str, int, str]) -> bytes:
    """Read the pinned public bytes; custody failures remain test errors."""
    relative, length, digest = specification
    path = ROOT / relative
    if not stat.S_ISREG(path.lstat().st_mode):
        raise OSError(f"public fixture is not a regular file: {relative}")
    with path.open("rb") as stream:
        data = stream.read(length + 1)
    if len(data) != length or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"public fixture bytes differ from the capture: {relative}")
    return data


@cache
def controller_module():
    specification = importlib.util.spec_from_file_location(
        "checkpoint_marker_scan_hexctl", CONTROLLER
    )
    if specification is None or specification.loader is None:
        raise ImportError("checkpoint scanner controller cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class PublicAuditQuotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = controller_module()

    def test_preserved_public_audit_source_is_not_key_material(self):
        data = public_fixture(AUDIT_SOURCE)
        self.assertFalse(
            self.controller._checkpoint_archive_secret_shaped(data),
            "the preserved public audit source contains quotations without key material",
        )

    def test_preserved_public_audit_synopsis_is_not_key_material(self):
        data = public_fixture(AUDIT_SYNOPSIS)
        self.assertFalse(
            self.controller._checkpoint_archive_secret_shaped(data),
            "the preserved public audit synopsis contains quotations without key material",
        )


HEAD_PREFIX = b"-" * 5 + b"BEGIN "
END_PREFIX = b"-" * 5 + b"END "


def markers(label=b"RSA PRIVATE KEY"):
    return HEAD_PREFIX + label + b"-" * 5, END_PREFIX + label + b"-" * 5


def streaming(predicate, payload):
    carry = b""
    for at in range(0, len(payload), 65536):
        chunk = payload[at:at + 65536]
        if predicate(carry + chunk):
            return True
        carry = chunk[-10079:]
    return False


@cache
def material_corpus():
    """Reproduce the study's 436 refusal and 119 benign byte specimens."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from plugins.hexaemeron.tests import test_hexctl_checkpoint_archive as fixture
    CTL = controller_module()
    pem, modulus, public, private = fixture.rsa_private_key_pem()
    assert modulus.bit_length() == 3072
    assert pow(pow(0xC0FFEE, public, modulus), private, modulus) == 0xC0FFEE
    body = ''.join(pem.splitlines()[1:-1]).encode()
    positive = []
    spellings = [(name, value.encode()) for name, value in fixture.LINE_BREAK_SPELLINGS]
    spellings.extend([('numeric-uppercase-cr', b'\\u000D'), ('numeric-uppercase-lf', b'\\u000A'), ('numeric-uppercase-crlf', b'\\u000D\\u000A')])
    for label in [b'PRIVATE KEY', b'RSA PRIVATE KEY', b'EC PRIVATE KEY', b'DSA PRIVATE KEY', b'ENCRYPTED PRIVATE KEY', b'OPENSSH PRIVATE KEY', b'PGP PRIVATE KEY BLOCK']:
        header, footer = markers(label)
        for name, ending in spellings:
            rows = [body[at:at + 64] for at in range(0, len(body), 64)]
            for closing in ['complete', 'no-footer', 'truncated']:
                content = ending.join(rows) if closing != 'truncated' else ending.join(rows[:2])
                suffix = ending + footer if closing == 'complete' else b''
                value = b'{"key":"' + header + ending + content + suffix + b'"}'
                positive.append((label.decode() + '/' + name + '/' + closing, value))
    header, footer = markers()
    for width in [1, 8]:
        for name, ending in spellings:
            rows = [body[at:at + width] for at in range(0, len(body), width)]
            for closing in ['complete', 'no-footer']:
                suffix = ending + footer if closing == 'complete' else b''
                value = header + ending + ending.join(rows) + suffix
                positive.append((f'rewrapped-{width}/{name}/{closing}', value))
    for label, metadata in [(b'RSA PRIVATE KEY', [b'Proc-Type: 4,ENCRYPTED', b'DEK-Info: AES-256-CBC,0123456789ABCDEF']), (b'PGP PRIVATE KEY BLOCK', [b'Version: fixture', b'Comment: disposable fixture', b'MessageID: example', b'Hash: SHA256', b'Charset: UTF-8'])]:
        header, footer = markers(label)
        for name, ending in spellings[1:]:
            for width in [1, 8, 64]:
                rows = [body[at:at + width] for at in range(0, len(body), width)]
                value = header + ending + ending.join(metadata) + ending * 2 + ending.join(rows) + ending + footer
                positive.append((f'metadata/{label.decode()}/{width}/{name}', value))
    header, footer = markers()
    for name, ending in spellings:
        twin = fixture.rsa_shaped_pem(8192).encode().replace(b'\n', ending)
        positive.append(('8192-geometry/' + name, twin))
    for name, ending in spellings:
        payload = header + ending + ending.join([b'/A/' * 3 for _ in range(100)]) + ending + footer
        positive.append(('escaped-solidus/' + name, payload.replace(b'/', b'\\/')))
    bodyline = b'A' * 64
    for split in [1, len(header) - 1, len(header) + 8, len(header) + 70]:
        value = b'#' * (CTL.CHECKPOINT_IO_CHUNK - split) + header + b'\n' + bodyline + b'\n' + footer
        positive.append((f'chunk-split-{split}', value))
    positive.append(('repeated-headers-with-material', (header + b'\n') * 100 + bodyline + b'\n' + footer))
    for i, token in enumerate(CTL.CHECKPOINT_ARCHIVE_SECRET_HEADERS[2:]):
        positive.append((f'token-{i}', token))
        positive.append((f'token-chunk-{i}', b'#' * (CTL.CHECKPOINT_IO_CHUNK - 2) + token))
    negative = [(entry[0], public_fixture(entry)) for entry in (AUDIT_SOURCE, AUDIT_SYNOPSIS)]
    for label in [b'PRIVATE KEY', b'RSA PRIVATE KEY', b'OPENSSH PRIVATE KEY', b'PGP PRIVATE KEY BLOCK']:
        header, footer = markers(label)
        for name, ending in spellings:
            negative.append(('empty-pair/' + label.decode() + '/' + name, header + ending + footer))
            negative.append(('prose-pair/' + label.decode() + '/' + name, header + ending + b'this line is not base64' + ending + footer))
        negative.append(('header-only/' + label.decode(), b'`' + header + b'` is the marker.'))
        negative.append(('quoted-pair/' + label.decode(), b'`' + header + b'` and `' + footer + b'` name markers.'))
        negative.append(('repeated-empty/' + label.decode(), (header + b'\n' + footer + b'\n') * 100))
    negative.append(('public-key-body', markers(b'PGP PUBLIC KEY BLOCK')[0] + b'\n' + body + b'\n'))
    return tuple(positive), tuple(negative)


def boundary_cases():
    """Exercise declared limits with new inputs; historical probe bytes were not kept."""
    header, footer = markers()
    cases = []
    for count in (15, 16):
        cases.append((f"glyphs-{count}", header + b"A" * count + b"!", count == 16))
    for count in (256, 257):
        metadata = b"Comment:" + b"x" * (count - 8)
        cases.append((f"metadata-bytes-{count}", header + b"\r" + metadata + b"\r" + b"A" * 16 + b"!", count == 256))
    for count in (7, 8):
        cases.append((f"metadata-lines-{count}", header + b"\r" + b"Hash: x\r" * count + b"A" * 16 + b"!", count == 7))
    for offset in (1791, 1792):
        cases.append((f"body-start-{offset}", header + b" " * offset + b"A" * 16 + b"!", offset == 1791))
    for end in (9984, 9985):
        prefix = b"\rA" + b" " * (end - 18) + b"\r" + b"B" * 15 + b"!"
        cases.append((f"lookahead-end-{end}", header + prefix, end == 9984))
    for count in (15, 16):
        cases.append((f"ordinary-word-{count}", header + b"\r" + b"a" * count + b"!", count == 16))
    cases.append(("unknown-metadata", header + b"\rUnknown: x\r" + b"A" * 16 + b"!", False))
    cases.append(("space-in-prose", header + b"\rthe words contain spaces\r" + footer, False))
    return tuple(cases)


def measurement_workload():
    header = markers(b"PGP PRIVATE KEY BLOCK")[0]
    return (
        b"#" * (1024 * 1024),
        (header + b"\n") * (1024 * 1024 // (len(header) + 1)),
        public_fixture(AUDIT_SOURCE),
        public_fixture(AUDIT_SYNOPSIS),
    )


class CheckpointMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = controller_module()
        cls.positive, cls.negative = material_corpus()

    def test_study_corpus_counts_and_unique_names(self):
        self.assertEqual(436, len(self.positive))
        self.assertEqual(119, len(self.negative))
        for cases in (self.positive, self.negative):
            self.assertEqual(len(cases), len({name for name, _ in cases}))

    def test_material_refusal_corpus(self):
        for name, payload in self.positive:
            with self.subTest(case=name):
                self.assertTrue(streaming(self.controller._checkpoint_archive_secret_shaped, payload))

    def test_benign_acceptance_corpus(self):
        for name, payload in self.negative:
            with self.subTest(case=name):
                self.assertFalse(streaming(self.controller._checkpoint_archive_secret_shaped, payload))

    def test_declared_prefix_boundaries(self):
        for name, payload, expected in boundary_cases():
            with self.subTest(case=name):
                self.assertEqual(expected, streaming(self.controller._checkpoint_archive_secret_shaped, payload))

    def test_complete_prefix_bound_survives_chunk_splits(self):
        for name, payload, expected in boundary_cases():
            if not name.startswith("lookahead-end-"):
                continue
            for split in (1, len(payload) // 2, len(payload) - 2):
                carried = b"#" * (65536 - split) + payload
                with self.subTest(case=name, bytes_before_boundary=split):
                    self.assertEqual(
                        expected,
                        streaming(self.controller._checkpoint_archive_secret_shaped, carried),
                    )

    def test_independent_whole_line_still_refuses_after_quoted_header(self):
        header, _ = markers()
        payload = b"`" + header + b"` is quoted.\n" + b"A" * 16 + b"\n"
        self.assertTrue(self.controller._checkpoint_archive_secret_shaped(payload))

    def test_stripped_16384_bit_geometry_has_an_early_material_prefix(self):
        from plugins.hexaemeron.tests import test_hexctl_checkpoint_archive as fixture
        header, footer = markers()
        payload = fixture.rsa_shaped_pem(16384).replace("\n", "").encode()
        self.assertGreater(payload.index(footer) - len(header), 9984 + 2048)
        self.assertIsNone(self.controller.CHECKPOINT_ARCHIVE_SECRET_BODY.search(payload))
        self.assertTrue(streaming(self.controller._checkpoint_archive_secret_shaped, payload))

    def test_empty_quoted_and_unquoted_pairs_have_the_same_result(self):
        header, footer = markers()
        for value in (header + footer, b"`" + header + b"` and `" + footer + b"`", header + b"\n" + footer):
            with self.subTest(sha256=hashlib.sha256(value).hexdigest()):
                self.assertFalse(self.controller._checkpoint_archive_secret_shaped(value))

    def test_inputs_and_repeated_results_are_unchanged(self):
        cases = self.positive + self.negative
        before = [hashlib.sha256(value).hexdigest() for _, value in cases]
        first = [streaming(self.controller._checkpoint_archive_secret_shaped, value) for _, value in cases]
        second = [streaming(self.controller._checkpoint_archive_secret_shaped, value) for _, value in cases]
        self.assertEqual(first, second)
        self.assertEqual(before, [hashlib.sha256(value).hexdigest() for _, value in cases])

    def test_fixed_scan_bounds(self):
        self.assertEqual(65536, self.controller.CHECKPOINT_IO_CHUNK)
        self.assertEqual(10079, self.controller.CHECKPOINT_ARCHIVE_SECRET_WINDOW)
        self.assertEqual(1792, self.controller.CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD)
        self.assertEqual(9984, self.controller.CHECKPOINT_ARCHIVE_SECRET_FOOTER_LOOKAHEAD)
        self.assertEqual(256, self.controller.CHECKPOINT_ARCHIVE_SECRET_ARMOUR_LINE)
        self.assertEqual(7, self.controller.CHECKPOINT_ARCHIVE_SECRET_ARMOUR_LINES)
        self.assertEqual(16, self.controller.CHECKPOINT_ARCHIVE_SECRET_PREFIX_GLYPHS)

    def test_scan_peak_stays_under_one_mebibyte(self):
        workload = measurement_workload()
        self.assertEqual(2852105, sum(map(len, workload)))
        tracemalloc.start()
        try:
            for payload in workload:
                streaming(self.controller._checkpoint_archive_secret_shaped, payload)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(peak, 1048576)


if __name__ == "__main__":
    unittest.main()
