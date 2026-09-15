"""Inventory guards for the Fiat checkpoint archive contract.

`skills/fiat/references/checkpoint-archive.md` is the contract the archive,
inspect and restore commands are built against. Every value in it comes from
the study committed as `docs/fiat-checkpoint-archive-study.md`, so a value that
drifts in one document and not the other is a specification an implementer
reads and a specification the study fixed, disagreeing.

The first test holds the reference to that study, item for item: the 24 refusal
classes of study section 4 and the 35 hostile fixture ids on section 5's risk
register `hostile-fixture-set` line, then the six schema names, the nine entry
paths, the store path fence, the two boundary directory names, the thirteen
closed manifest fields with the content each is closed to, the seven ceiling
values, the zip metadata rule including the entry mode, the bundle determinism
command, the six secret patterns, the closed fields of the export, inspect,
signature-proof and restore-transcript result objects, the sidecar two-space
rule and the `acceptance/current` rule, against the study's assumption list and
sections 1, 3, 4, 5 and 6.

The two documents abbreviate the boundary directories' head placeholder
differently, `<sha>` in the study's assumption 5 and its section 6 glossary
against `<full-head-sha>` in the reference, so each name is compared as the
stem before that placeholder, and the reference's own placeholder is held equal
to the one its store path fence uses -- a fence asserted equal to the study's,
which binds the placeholder to study section 1.

Four assertions are over the reference alone, because the study states no
counterpart to compare: the `## Restore transaction` heading, which study
section 12 names among this contract's contents without stating any of it; the
restore result's native `fiat-controller-checkpoint-restore/v1` object name and
its `outer_sha256` member, which the study states nowhere; and each path the
manifest's `joined against` column names, which must be a path the layout fence
states -- and that fence is held equal to the study's, so the join is bound to
study section 1 through it. The restore result is bounded against the study as
well: the four members section 1 does state must be among the reference's.

A class missing from the reference is a refusal nobody tests; an id missing is
a specimen nobody builds; a drifted ceiling, pattern or closed field is the
limit an implementer builds to. Mutating any one of those values, or deleting
it, fails this test. Both documents are read from the tracked copies, so the
test runs outside a Fiat run worktree.

The second test holds the budgets file to the six limits study section 10
derived, read through the same loader `metron.py check --budgets` uses, and
holds the reference's and the study's prose tables equal to it.

Every slice below is taken through `anchored` or `fenced_block`, which name the
missing anchor in an assertion rather than raising `IndexError` on a reworded
study.

The remaining class exports one archive from one really signed run. The
controller fixture the rest of the suite uses fakes every delivery tool, which
is correct for receipts and useless here: a bundle built from invented SHAs
carries no objects, and a signature proof read from a canned trailer block
proves nothing. So that class points the fake ref reader at the commits it
really made, signs them with a key generated into a temporary `GNUPGHOME`, and
lets the archive's bundle, digests and proof run against real bytes. The
operator's keyring is never opened.

Step 3 adds the 35 `test_hostile_<id>` methods themselves, in
`CheckpointArchiveInspectTests`, plus three more covering the clean path and
the write and print boundaries. Before that step, no test or class name here
contained `hostile` or `restore_from_archive`; the design record's
conformance resolvers select the intended tests with `-k hostile` and
`-k restore_from_archive`, so the classes above this one still keep those
words out of every name they hold, and `restore_from_archive` stays absent
from the whole file until the step that owns it.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import base64
import json
import os
import pathlib
import random
import re
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import unicodedata
import unittest
import zipfile
import zlib
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

# The capsule refuses a symlinked output parent by design, and macOS resolves
# TMPDIR under /var, a symlink to /private/var. Canonicalising the temporary
# root hands the controller a real path and leaves the refusal untouched.
tempfile.tempdir = os.path.realpath(tempfile.gettempdir())
os.environ["TMPDIR"] = tempfile.tempdir

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_hexctl import HEXCTL, LINTS_CLEAN, HexctlCase, hexctl_module  # noqa: E402

ORIGIN_URL = "https://github.com/wildcat-finance/example.git"
COAUTHOR = "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>"
ORIGIN_TRAILER = "Wildcat-Origin: shoggoth"

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
ROOT = PLUGIN.parents[1]
FIAT = PLUGIN / "skills" / "fiat"
REFERENCE = FIAT / "references" / "checkpoint-archive.md"
BUDGETS = FIAT / "scripts" / "checkpoint-archive-budgets.json"
METRON = PLUGIN / "skills" / "metron" / "scripts" / "metron.py"
STUDY = ROOT / "docs" / "fiat-checkpoint-archive-study.md"

TABLE_CLASS = re.compile(r"^\| `([a-z0-9]+(?:-[a-z0-9]+)+)` \|")
LIST_ID = re.compile(r"^- `([a-z0-9]+(?:-[a-z0-9]+)+)`$")
KEBAB_SPAN = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`")
MANIFEST_ROW = re.compile(r"^\| `(?P<field>[a-z_]+)` \| (?P<closed>.+) \| (?P<joined>.+) \|$")
# Study section 1 states each field's closed content as one parenthetical in
# the `checkpoint.json` sentence; the reference states the same content as a
# table cell. No parenthetical nests a bracket, so the class excludes both.
STUDY_MANIFEST_FIELD = re.compile(r"`(?P<field>[a-z_]+)` \((?P<closed>[^()]*)\)")
SCHEMA_NAME = re.compile(r"(?<![-\w])fiat-checkpoint-[a-z-]+/v[0-9]+")
BUDGET_ROW = re.compile(
    r"^\| `(?P<name>checkpoint\.archive\.[a-z_]+)` \| (?P<unit>[a-z]+) \|"
    r" (?P<limit>[0-9]+) \| (?P<derivation>.+) \|$"
)
STUDY_BUDGET_HEADING = "10. The budget, or its absence"
CEILING_NUMBER = re.compile(r"(?<![\w,.\-])([0-9][0-9,]*)")
CODE_SPAN = re.compile(r"`([^`]+)`")
BUNDLE_COMMAND = "`git -c pack.threads=1 bundle create`"
UNTHREADED_BUNDLE_COMMAND = "`git bundle create`"

# The six schema names of study sections 1 and 4. `fiat-controller-checkpoint`
# schemas belong to the capsule this archive carries and are not this
# reference's to fix, so the pattern above starts at `fiat-checkpoint-`.
EXPECTED_SCHEMAS = frozenset(
    {
        "fiat-checkpoint-archive/v1",
        "fiat-checkpoint-archive-export/v1",
        "fiat-checkpoint-archive-restore/v1",
        "fiat-checkpoint-inspect/v1",
        "fiat-checkpoint-restore-transcript/v1",
        "fiat-checkpoint-signature-proof/v1",
    }
)

# The nine entry paths, in the fixed order both documents state them.
EXPECTED_ENTRY_PATHS = (
    "checkpoint.json",
    "README.txt",
    "git/repository.bundle",
    "controller-capsule/MANIFEST.json",
    "controller-capsule/controller/...",
    "identity/checkpoint-identity.json",
    "proof/signatures.json",
    "proof/pubkey.asc",
    "acceptance/prior/<n>.json",
)

# The thirteen fields `checkpoint.json` is closed to, in order.
EXPECTED_MANIFEST_FIELDS = (
    "schema",
    "archive",
    "boundary",
    "run",
    "refs",
    "bundle",
    "controller_capsule",
    "identity",
    "signer",
    "proof",
    "acceptance",
    "controller",
    "limits",
)

# The seven ceiling values, in the order both documents state them: entries,
# expanded total, the bundle, every other entry, an entry name, an entry name
# component, and prior acceptance receipts.
EXPECTED_CEILINGS = (4200, 1300, 1, 64, 1024, 255, 64)
EXPECTED_CEILING_PHRASES = (
    "4,200 entries",
    "1,300 MiB",
    "1 GiB",
    "64 MiB",
    "1,024 UTF-8 bytes",
    "64 prior",
)
EXPECTED_ENTRY_MODE = "0100644"
EXPECTED_CONTAINER_CLAUSES = (
    "stored",
    f"Unix mode `{EXPECTED_ENTRY_MODE}`",
    "DOS time 1980-01-01 00:00:00",
    "`create_system` 3",
    "no directory entries",
    "no ZIP64 records",
    "no comment",
    "no extra fields",
    "sorted by UTF-8 bytes",
)
# Study section 4's own bullet still lists the set the study was receipted
# with. The dated amendment of 2026-09-09 replaces one member of it: the
# OpenSSH header is dropped, because the PEM pattern before it already matches
# that header, and the OpenPGP block takes the free place. The reference and
# the code carry the amended set, so the two expectations below are held
# against different parts of the same study rather than against each other.
SUBSUMED_PATTERN_SPAN = "-----BEGIN OPENSSH PRIVATE KEY-----"
ADDED_PATTERN_SPAN = "-----BEGIN PGP PRIVATE KEY BLOCK-----"
EXPECTED_SECRET_SPANS = (
    SUBSUMED_PATTERN_SPAN,
    "ghp_[A-Za-z0-9]{36}",
    "github_pat_[A-Za-z0-9_]{22,}",
    "AKIA[0-9A-Z]{16}",
    "xox[baprs]-",
)
EXPECTED_AMENDED_SECRET_SPANS = tuple(
    ADDED_PATTERN_SPAN if span == SUBSUMED_PATTERN_SPAN else span
    for span in EXPECTED_SECRET_SPANS
)
PATTERN_AMENDMENT_HEADING = "### Amendment -- 2026-09-09"
EXPECTED_PEM_PROSE = "PEM private-key block"

# The second amendment of 2026-09-09 refuses an armour header only when key
# material follows it, so every specimen that must still refuse is a block. The
# body line below is base64 of ASCII letters and carries nothing private; its
# job is to be shaped like material. A bare header is the opposite specimen:
# it is what this study, this reference and this test file all carry, and it
# must now publish.
ARMOURED_BODY_LINE = "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVphYmNkZWZnaGlqa2xtbg=="
ARMOURED_BLOCK_TRUNCATED = SUBSUMED_PATTERN_SPAN + "\n" + ARMOURED_BODY_LINE + "\n"
# The same block held as a JSON string value, which is how `state.json` and a
# `ledger.jsonl` line carry one: `json.dumps` writes every newline as the two
# characters `\` and `n`, so the member has no newline byte anywhere. Forty
# body lines put the footer further past the header than the lookahead
# reaches, so neither witness arrived and the member published. That was
# S2-R3-01, and it is the shape a real deploy key in controller state has.
ARMOURED_BLOCK_JSON_CARRIED = json.dumps(
    {
        "deploy_key": (
            SUBSUMED_PATTERN_SPAN
            + "\n"
            + (ARMOURED_BODY_LINE + "\n") * 40
            + "-----END OPENSSH PRIVATE KEY-----\n"
        )
    }
)

# The reference's block paragraph is the contract home steps 3 to 5 read for
# the block rule, and until this pin nothing held it: four anchored edits to
# it, including deleting it outright and inverting the truncated-key rule,
# left every test that reads the file green. That was S2-R3-03.
#
# The pin is an equality, so mutating any value in the paragraph fails, and
# the anchors below fail by name when the paragraph is deleted. The equality
# alone would only say the reference still reads as somebody once typed it,
# so each rule in it is also required to be a rule study section 4 states:
# a dated amendment that moves one moves this test, and the reference has to
# follow rather than drift quietly behind it.
REFERENCE_BLOCK_ANCHOR = "The two armour forms refuse as blocks."
REFERENCE_BLOCK_END = "\n\n- A PEM private-key block"
EXPECTED_BLOCK_PARAGRAPH = (
    "The two armour forms refuse as blocks. A header is secret-shaped "
    "only when key material follows it within the scanned window: one "
    "whole line of base64 body, or the `-----END` marker matching that "
    "header. The two witnesses have their own reaches: the body has to "
    "start within the block lookahead of 1,792 bytes, which the armour "
    "allowance bounds, and the footer has until the footer reach of "
    "9,984 bytes, the block lookahead plus the largest key the scan "
    "undertakes to reach, declared at 8,192 bits. A line ends at a "
    "newline character or at the two-character escape `\\n` that carries "
    "one inside a JSON string value, so a key held as a JSON string "
    "value in `state.json` or on one `ledger.jsonl` line carries body "
    "lines like any other. The delimiter set is the line feed as a "
    "byte, as the two-character escape, or as the six-character numeric "
    "escape, each optionally preceded by a carriage return in the "
    "matching form. The numeric escapes are `\\u000a` for the line feed "
    "and `\\u000d` before it for the carriage return, in either letter "
    "case, so a CRLF key refuses raw, escaped and numerically escaped "
    "alike. A body carrying no line delimiter in any form the witness "
    "can see, such as a key whose line breaks were stripped rather than "
    "encoded, refuses on its footer at every size below the declared "
    "one. What the scan does not reach is a key whose modulus exceeds "
    "that declared size, and the study states it as residue rather than "
    "implying the class is shut. A file naming a header in prose or "
    "quoting one in a code span supplies neither, so a run can archive "
    "its own specification text. A key whose footer was truncated still "
    "carries body lines and still refuses. The four token patterns are "
    "self-delimiting and refuse on the match alone. The scan reads in "
    "bounded chunks and carries between them the longest header the six "
    "can match plus the footer reach, so a block lying across a chunk "
    "boundary still refuses; the carry is derived from the patterns "
    "rather than fixed."
)
# Each row is one rule: what study section 4 states, and the words the
# reference paragraph has to restate it in. Neither side may be absent.
BLOCK_RULE_PARITY = (
    (
        "at least one line of base64 body or a matching `-----END` marker",
        "one whole line of base64 body, or the `-----END` marker matching "
        "that header",
    ),
    (
        "a line ends at a newline character or at the two-character escape "
        "`\\n` that carries one inside a JSON string value",
        "A line ends at a newline character or at the two-character escape "
        "`\\n` that carries one inside a JSON string value",
    ),
    (
        "the line feed as a byte, as the two-character escape, or as the "
        "six-character numeric escape, each optionally preceded by a "
        "carriage return in the matching form",
        "The delimiter set is the line feed as a byte, as the two-character "
        "escape, or as the six-character numeric escape, each optionally "
        "preceded by a carriage return in the matching form",
    ),
    (
        "in either letter case: `\\u000a` for the line feed and `\\u000d` "
        "before it for the carriage return",
        "`\\u000a` for the line feed and `\\u000d` before it for the "
        "carriage return, in either letter case",
    ),
    (
        "The block lookahead keeps its 1,792 bytes and bounds only where the "
        "body may start, which is what the armour allowance measures",
        "the body has to start within the block lookahead of 1,792 bytes, "
        "which the armour allowance bounds",
    ),
    (
        "A separate footer reach bounds where that header's own footer may "
        "sit, and is the armour allowance plus the largest key the scan "
        "undertakes to reach, declared at 8,192 bits, giving 9,984 bytes",
        "the footer has until the footer reach of 9,984 bytes, the block "
        "lookahead plus the largest key the scan undertakes to reach, "
        "declared at 8,192 bits",
    ),
    (
        "a body carrying no delimiter in any spelling is now refused at every "
        "size below it, because its footer is in reach",
        "such as a key whose line breaks were stripped rather than encoded, "
        "refuses on its footer at every size below the declared one",
    ),
    (
        "The residue narrows to a key whose modulus exceeds that declared "
        "size",
        "What the scan does not reach is a key whose modulus exceeds that "
        "declared size, and the study states it as residue",
    ),
    (
        "A document that names a header in prose or inside a code span is "
        "not a secret",
        "A file naming a header in prose or quoting one in a code span "
        "supplies neither",
    ),
    (
        "still catches a key whose footer was truncated",
        "A key whose footer was truncated still carries body lines and still "
        "refuses",
    ),
    (
        "The four token patterns are unchanged, because each is "
        "self-delimiting",
        "The four token patterns are self-delimiting and refuse on the match "
        "alone",
    ),
    (
        "The set stays six",
        "the longest header the six can match plus the footer reach",
    ),
    (
        "the carried window between chunks is derived from the footer reach "
        "rather than the block lookahead",
        "carries between them the longest header the six can match plus the "
        "footer reach",
    ),
)

# A well-formed fingerprint that is not the fixture's, for the proof's
# comparison against the set the manifest pins. It is never imported anywhere.
UNPINNED_FINGERPRINT = "0123456789ABCDEF0123456789ABCDEF01234567"

# The sidecar's two spaces are what `shasum -a 256 -c` reads, so the one-space
# form is rejected by name in both documents.
SIDECAR_SPAN = r"`<64 lowercase hex>  checkpoint.zip\n`"
SIDECAR_ONE_SPACE = r"`<64 lowercase hex> checkpoint.zip\n`"

# The store path fence, stated the same way in both documents.
STORE_PATH_ANCHOR = "The store path is derived from controller state and never supplied:"
STUDY_STORE_PATH_ANCHOR = "publishes with a no-replace rename:"

# The two boundary directory names, in the order both documents state them.
# The name splits into the stem before its head placeholder and the
# placeholder itself, because the study's prose abbreviates `<full-head-sha>`
# to `<sha>` and the stem is what the two documents can be held equal on. The
# optional segments are written out so a dropped `loop-<l>-` still parses and
# fails as a stem that does not match, rather than passing as no match at all.
BOUNDARY_NAME = re.compile(r"^((?:audit-verdict-)?step-.*?-)(<[^<>]+>)$")
EXPECTED_BOUNDARY_STEMS = ("step-<n>-", "audit-verdict-step-<n>-loop-<l>-")
BOUNDARY_SENTENCE_ANCHOR = "The two boundary directory names are"
BOUNDARY_SENTENCE_END = "The sidecar is"
STUDY_BOUNDARY_ASSUMPTION_ANCHOR = "5. Both accepted ADR-028 boundaries are in scope:"
STUDY_BOUNDARY_ASSUMPTION_END = "\n6. "
STUDY_GLOSSARY_HEADING = "6. Glossary seeds"
STUDY_GLOSSARY_BOUNDARY_ANCHOR = "- **Boundary directory:**"
STUDY_GLOSSARY_BOUNDARY_END = "\n- "

# The closed fields of four of the five result objects. Each is a paragraph of
# the reference's `## Results and proof` and a bullet or sentence of the study,
# wrapped and punctuated differently, so the slices below are compared as
# ordered code spans. `NO_RAW_GPG` bounds the signature proof because the
# reference alone goes on to name `push.verified_commits`.
NO_RAW_GPG = "No raw `gpg` output."
RESULT_OBJECTS = (
    (
        "export result",
        "`fiat-checkpoint-archive-export/v1`, from `archive`:",
        "\n\n",
        "options",
        "- Export result `fiat-checkpoint-archive-export/v1`:",
        "\n- ",
    ),
    (
        "inspect result",
        "`fiat-checkpoint-inspect/v1`, from `inspect`:",
        "\n\n",
        "options",
        "- Inspect result `fiat-checkpoint-inspect/v1`:",
        "\n- ",
    ),
    (
        "signature proof",
        "`fiat-checkpoint-signature-proof/v1`, the `proof/signatures.json` member:",
        NO_RAW_GPG,
        "options",
        "- Signature proof `fiat-checkpoint-signature-proof/v1`:",
        NO_RAW_GPG,
    ),
    (
        "restore transcript",
        "`fiat-checkpoint-restore-transcript/v1`, written by the clean-machine demo:",
        " measurements.",
        "problem",
        "writes `fiat-checkpoint-restore-transcript/v1` with",
        " measurements.",
    ),
)

# The fifth result object is bounded against the study rather than compared
# field for field. The reference states six members; study section 1 states
# four of them and states neither the native object's schema name nor
# `outer_sha256`, so those two are pinned over the reference alone below. The
# native object carries its qualifier into the assertion: an object of that
# name that is not the controller's own is a different contract.
RESTORE_RESULT_ANCHOR = "`fiat-checkpoint-archive-restore/v1`, from `restore --archive`:"
STUDY_RESTORE_RESULT_ANCHOR = "relocation transaction with the manifest digest, recomputes"
STUDY_RESTORE_RESULT_END = " prints one"
NATIVE_RESTORE_OBJECT = "the native `fiat-controller-checkpoint-restore/v1` object"
RESTORE_OUTER_DIGEST_MEMBER = "outer_sha256"

RESTORE_HEADING = "Restore transaction"
ACCEPTANCE_OUTSIDE = "`current` is the literal `outside`"
ACCEPTANCE_NEVER_WRITTEN = "No `acceptance/current` entry is ever written."
ACCEPTANCE_REFUSAL_ROW = "| `acceptance-self-reference` |"
ACCEPTANCE_REFUSAL_CONDITION = "an `acceptance/current` entry is present"
STUDY_ACCEPTANCE_REFUSES = "acceptance/current refuses"

EXPECTED_BUDGETS = {
    "checkpoint.archive.export_wall_ms": ("ms", 15000),
    "checkpoint.archive.inspect_wall_ms": ("ms", 10000),
    "checkpoint.archive.restore_wall_ms": ("ms", 20000),
    "checkpoint.archive.bytes": ("bytes", 201581002),
    "checkpoint.archive.expanded_bytes": ("bytes", 209715200),
    "checkpoint.archive.export_peak_rss_bytes": ("bytes", 1073741824),
}


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required Step 1 file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """The body under one `## heading`, up to the next `## ` heading."""
    marker = f"\n## {heading}\n"
    if marker not in text:
        raise AssertionError(f"no `## {heading}` section")
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def reference_refusal_classes(reference: str) -> list[str]:
    """The first cell of every data row in the refusal-class table, in order."""
    found = []
    for line in section(reference, "Refusal classes").splitlines():
        match = TABLE_CLASS.match(line)
        if match:
            found.append(match.group(1))
    return found


def reference_fixture_ids(reference: str) -> list[str]:
    """Every one-id list item under the fixture heading, in order."""
    found = []
    for line in section(reference, "Hostile fixtures").splitlines():
        match = LIST_ID.match(line)
        if match:
            found.append(match.group(1))
    return found


def study_refusal_classes(study: str) -> set[str]:
    """The kebab-case spans of study section 4's `Refusal classes` bullet.

    The bullet's only other span, `status: unavailable`, carries a colon and a
    space, so a kebab-only pattern leaves it out.
    """
    details = study.split("### Details the runbook binds", 1)[1].split("\n## ", 1)[0]
    bullet = details.split("- Refusal classes,", 1)[1].split("\n- ", 1)[0]
    return set(KEBAB_SPAN.findall(bullet))


def budget_rows(text: str, heading: str) -> list[str]:
    """The data rows of one budget table under `## heading`, exactly as written."""
    return [
        line
        for line in section(text, heading).splitlines()
        if BUDGET_ROW.match(line)
    ]


def flat(text: str) -> str:
    """One line, single-spaced, so a rewrapped paragraph reads the same."""
    return " ".join(text.split())


def normalise_closed(cell: str) -> str:
    """One line with no code-span backticks.

    The two documents span the same words differently -- the study writes
    ``format `zip` `` where the reference writes `` `format` `zip` `` -- so the
    words are the evidence and the span punctuation is not.
    """
    return flat(cell.replace("`", ""))


SMALL_PRIMES = [
    candidate
    for candidate in range(2, 4096)
    if all(candidate % factor for factor in range(2, int(candidate**0.5) + 1))
]


def _probable_prime(candidate: int, rng: random.Random, rounds: int = 6) -> bool:
    """Miller-Rabin, which is what makes the key below a key and not a shape."""
    odd, power = candidate - 1, 0
    while odd % 2 == 0:
        odd //= 2
        power += 1
    for _ in range(rounds):
        witness = pow(rng.randrange(2, candidate - 1), odd, candidate)
        if witness in (1, candidate - 1):
            continue
        for _ in range(power - 1):
            witness = witness * witness % candidate
            if witness == candidate - 1:
                break
        else:
            return False
    return True


def _prime(bits: int, rng: random.Random) -> int:
    """One prime of exactly `bits` bits, with the top two bits set.

    Both top bits, so the product of two of these is exactly twice the width
    and the key's byte length is the length a key of that size really has.
    """
    while True:
        candidate = rng.getrandbits(bits) | (3 << (bits - 2)) | 1
        for _ in range(4096):
            if all(candidate % factor for factor in SMALL_PRIMES):
                if _probable_prime(candidate, rng):
                    return candidate
            candidate += 2


def _der_length(size: int) -> bytes:
    if size < 0x80:
        return bytes([size])
    raw = size.to_bytes((size.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def _der_integer(value: int) -> bytes:
    """One DER INTEGER, always with a leading zero byte so it stays positive."""
    body = value.to_bytes(value.bit_length() // 8 + 1, "big")
    return b"\x02" + _der_length(len(body)) + body


def rsa_private_key_pem(bits: int = 3072, seed: int = 861) -> tuple[str, int, int, int]:
    """A real RSA private key, generated here rather than checked in.

    The CRLF guard below needs a key and not a base64-shaped line. What made
    S2-R4-02 publish was a real key's geometry: a body of 64-character lines
    whose `-----END` marker lands further past the header than the block
    lookahead reaches. A repeated synthetic line proves nothing about that
    distance, and checking a key into this repository is the one thing the
    scan under test exists to refuse. So the key is built here, as PKCS#1 DER
    inside PEM armour, and returned with the three numbers that let the caller
    prove it is a working keypair rather than a string shaped like one.

    `random` seeded to a constant, not `secrets`: this key secures nothing,
    never leaves a temporary directory and is regenerated every run, and a
    fixed seed keeps the search cost of the two primes fixed at about a
    second rather than varying with the machine's entropy.
    """
    rng = random.Random(seed)
    public = 65537
    while True:
        first = _prime(bits // 2, rng)
        second = _prime(bits // 2, rng)
        if first != second and (first - 1) % public and (second - 1) % public:
            break
    modulus = first * second
    private = pow(public, -1, (first - 1) * (second - 1))
    fields = b"".join(
        _der_integer(value)
        for value in (
            0,
            modulus,
            public,
            private,
            first,
            second,
            private % (first - 1),
            private % (second - 1),
            pow(second, -1, first),
        )
    )
    der = b"\x30" + _der_length(len(fields)) + fields
    text = base64.b64encode(der).decode("ascii")
    body = "".join(text[at : at + 64] + "\n" for at in range(0, len(text), 64))
    pem = "-----BEGIN RSA PRIVATE KEY-----\n" + body + "-----END RSA PRIVATE KEY-----\n"
    return pem, modulus, public, private


# The ten spellings a JSON string value can give a PEM's line breaks: none,
# then the carriage return alone and the line feed alone and the pair, each as
# the raw byte, the two-character escape and the six-character numeric escape.
# The first four carry no delimiter the body witness reads; the last six do.
LINE_BREAK_SPELLINGS = (
    ("stripped", ""),
    ("carriage return, raw", "\r"),
    ("carriage return, two-character escape", "\\r"),
    ("carriage return, numeric escape", "\\u000d"),
    ("line feed, raw", "\n"),
    ("line feed, two-character escape", "\\n"),
    ("line feed, numeric escape", "\\u000a"),
    ("CRLF, raw", "\r\n"),
    ("CRLF, two-character escape", "\\r\\n"),
    ("CRLF, numeric escape", "\\u000d\\u000a"),
)


def rsa_shaped_pem(bits: int, seed: int = 861) -> str:
    """The armour an RSA key of `bits` bits has, around nine numbers that are not one.

    The residue guard needs a modulus past `CHECKPOINT_ARCHIVE_SECRET_LARGEST_KEY`,
    and `rsa_private_key_pem` at twice that size would search for two 8,192-bit
    primes, which takes minutes in this interpreter where 8,192 bits takes
    eight seconds. What the scan reads is distance, not primality: the DER
    length is a function of the nine integers' widths alone, so drawing each
    at the width a real key's field has, top bits set, gives the same armour
    to within the four bytes a real key's `d`, `dp`, `dq` and `qinv` fall
    short of that width by. The S2-R7-01 guard measures that delta against
    the seeded real key, so this twin cannot drift from the geometry it stands
    in for without a test saying so.
    """
    rng = random.Random(seed)

    def width(size: int) -> int:
        return rng.getrandbits(size) | (3 << (size - 2)) | 1

    half = bits // 2
    fields = b"".join(
        _der_integer(value)
        for value in (
            0,
            width(bits),
            65537,
            width(bits),
            width(half),
            width(half),
            width(half),
            width(half),
            width(half),
        )
    )
    der = b"\x30" + _der_length(len(fields)) + fields
    text = base64.b64encode(der).decode("ascii")
    body = "".join(text[at : at + 64] + "\n" for at in range(0, len(text), 64))
    return "-----BEGIN RSA PRIVATE KEY-----\n" + body + "-----END RSA PRIVATE KEY-----\n"


def anchored(text: str, start: str, end: str, what: str) -> str:
    """The slice between two literal anchors, or a named assertion failure.

    A prose anchor that has moved is a specification change somebody must
    look at, so it fails by name here rather than as an `IndexError` from a
    bare `split`.
    """
    if start not in text:
        raise AssertionError(f"{what}: the opening anchor {start!r} is absent")
    tail = text.split(start, 1)[1]
    if end not in tail:
        raise AssertionError(f"{what}: no {end!r} closes {start!r}")
    return tail.split(end, 1)[0]


def fenced_block(text: str, anchor: str, what: str) -> str:
    """The body of the first ```text fence after a literal anchor."""
    if anchor not in text:
        raise AssertionError(f"{what}: the anchor {anchor!r} is absent")
    tail = text.split(anchor, 1)[1]
    opener = "```text\n"
    if opener not in tail:
        raise AssertionError(f"{what}: no ```text fence follows {anchor!r}")
    body = tail.split(opener, 1)[1]
    if "\n```" not in body:
        raise AssertionError(f"{what}: the fence after {anchor!r} does not close")
    return body.split("\n```", 1)[0]


def first_column(block: str) -> list[str]:
    """The first whitespace-separated field of every non-blank line."""
    return [line.split()[0] for line in block.splitlines() if line.strip()]


def ceiling_numbers(text: str) -> list[int]:
    """Every free-standing quantity in a ceilings block, in written order.

    The lookbehind keeps `C0`, `C1` and the `8` of `UTF-8` out, since those
    are a control-character class and an encoding name rather than limits.
    """
    return [int(found.replace(",", "")) for found in CEILING_NUMBER.findall(text)]


def code_spans(text: str) -> list[str]:
    """Every backticked span, in written order, with the wrapping removed."""
    return CODE_SPAN.findall(flat(text))


def secret_spans(text: str) -> list[str]:
    return code_spans(text)


def boundary_names(candidates: list[str], what: str) -> list[tuple[str, str]]:
    """Every boundary directory name among `candidates`, in written order.

    Each is returned as its stem and its head placeholder, so the two can be
    held against different evidence: the stem against the other document, the
    placeholder against the store path fence.
    """
    found = [
        (match.group(1), match.group(2))
        for match in (BOUNDARY_NAME.match(candidate) for candidate in candidates)
        if match
    ]
    if not found:
        raise AssertionError(f"{what}: no boundary directory name is stated")
    return found


def study_fixture_ids(study: str) -> set[str]:
    """The whitespace-separated ids after `one test per id:` in the register."""
    for line in study.splitlines():
        if line.startswith("hostile-fixture-set |"):
            return set(line.split("one test per id:", 1)[1].split())
    raise AssertionError("the study's risk register has no hostile-fixture-set line")


def hexctl_tree() -> ast.Module:
    """`hexctl.py` parsed, for the enumeration proofs that read structure."""
    return ast.parse(Path(HEXCTL).read_text(encoding="utf-8"))


def module_functions(tree: ast.Module) -> dict:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def called_names(node) -> set:
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            function = child.func
            if isinstance(function, ast.Name):
                names.add(function.id)
            elif isinstance(function, ast.Attribute):
                names.add(function.attr)
    return names


def refusal_literals(node) -> set:
    """Every refusal class named by a literal reaching the two entry points.

    A class forwarded as a variable is not counted, which bounds this to the
    literals: the only such forward is `_checkpoint_archive_guarded` handing
    its own parameter to `_checkpoint_archive_refuse`, and that parameter's
    values are the literals its call sites already supply.
    """
    classes = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            function = child.func
            name = (
                function.id
                if isinstance(function, ast.Name)
                else getattr(function, "attr", None)
            )
            if name in ("_checkpoint_archive_refuse", "_checkpoint_archive_guarded"):
                if child.args and isinstance(child.args[0], ast.Constant):
                    classes.add(child.args[0].value)
    return classes


def manifest_closed_fields(tree: ast.Module) -> set:
    """`checkpoint.json`'s top-level field set, as the inspector closes it."""
    shape = module_functions(tree)["_checkpoint_inspect_manifest_shape"]
    for child in ast.walk(shape):
        if (
            isinstance(child, ast.Call)
            and getattr(child.func, "id", None) == "_checkpoint_inspect_closed"
            and len(child.args) == 3
            and isinstance(child.args[2], ast.Constant)
            and child.args[2].value == "manifest"
            and isinstance(child.args[1], ast.Set)
        ):
            return {element.value for element in child.args[1].elts}
    raise AssertionError("the inspector closes no manifest field set")


def load_metron():
    spec = importlib.util.spec_from_file_location("metron_budget_loader", METRON)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckpointArchiveScaffoldTests(unittest.TestCase):
    def test_archive_reference_names_every_refusal_class_and_fixture_id(self):
        reference = read(REFERENCE)
        study = read(STUDY)
        problem = section(study, "1. Problem statement")
        constraints = section(study, "3. Constraints and non-goals")
        options = section(study, "4. Design options")

        # The 24 refusal classes (study section 4) and the 35 hostile fixture
        # ids (study section 5), as sets, so a drop is a failure.
        classes = reference_refusal_classes(reference)
        self.assertEqual(len(classes), len(set(classes)), "a refusal class row repeats")
        self.assertEqual(24, len(classes), classes)
        self.assertEqual(study_refusal_classes(study), set(classes))

        ids = reference_fixture_ids(reference)
        self.assertEqual(len(ids), len(set(ids)), "a fixture id repeats")
        self.assertEqual(35, len(ids), ids)
        self.assertEqual(study_fixture_ids(study), set(ids))

        # The six schema names. The reference's set is closed, so a renamed or
        # reversioned schema shows as both a missing and an unexpected member.
        self.assertEqual(EXPECTED_SCHEMAS, set(SCHEMA_NAME.findall(reference)))
        for schema in sorted(EXPECTED_SCHEMAS):
            with self.subTest(schema=schema):
                self.assertIn(schema, study)

        # The nine entry paths. Both documents carry the layout as one fenced
        # block, and the blocks are equal, so a dropped or renamed line fails
        # in the column comparison and again in the block comparison.
        reference_layout_block = fenced_block(
            reference, "Nine entry paths, fixed:", "reference layout fence"
        )
        study_layout_block = fenced_block(
            problem, "Layout, fixed:", "study section 1 layout fence"
        )
        self.assertEqual(list(EXPECTED_ENTRY_PATHS), first_column(reference_layout_block))
        self.assertEqual(list(EXPECTED_ENTRY_PATHS), first_column(study_layout_block))
        self.assertEqual(study_layout_block, reference_layout_block)

        # The store path (study section 1). Both documents carry it as one
        # fenced block, so the blocks are compared whole: a renamed store
        # directory, a moved boundary segment or a changed sidecar suffix in
        # one document and not the other fails here.
        reference_store = section(reference, "Store path and boundaries")
        reference_store_fence = fenced_block(
            reference_store, STORE_PATH_ANCHOR, "reference store path fence"
        )
        self.assertEqual(
            fenced_block(problem, STUDY_STORE_PATH_ANCHOR, "study section 1 store path fence"),
            reference_store_fence,
        )

        # The two boundary directory names, which the study states in its
        # assumption 5 and again in its section 6 glossary. Each document must
        # name both, in order, with the same stem: dropping `loop-<l>-` gives
        # one directory for every audit loop of a step, and the section above
        # states that an existing boundary directory is never replaced, so an
        # exporter built from that reference would refuse the second loop as
        # occupied rather than publish it.
        boundary_slices = (
            (
                "reference",
                anchored(
                    flat(reference_store),
                    BOUNDARY_SENTENCE_ANCHOR,
                    BOUNDARY_SENTENCE_END,
                    "reference boundary directory names",
                ),
            ),
            (
                "study assumption 5",
                anchored(
                    study,
                    STUDY_BOUNDARY_ASSUMPTION_ANCHOR,
                    STUDY_BOUNDARY_ASSUMPTION_END,
                    "study assumption 5 boundary directory names",
                ),
            ),
            (
                "study section 6",
                anchored(
                    section(study, STUDY_GLOSSARY_HEADING),
                    STUDY_GLOSSARY_BOUNDARY_ANCHOR,
                    STUDY_GLOSSARY_BOUNDARY_END,
                    "study section 6 boundary directory glossary",
                ),
            ),
        )
        stated = {}
        for name, block in boundary_slices:
            with self.subTest(document=name, value="boundary directory names"):
                stated[name] = boundary_names(
                    code_spans(block), f"{name} boundary directory names"
                )
                self.assertEqual(
                    list(EXPECTED_BOUNDARY_STEMS),
                    [stem for stem, _ in stated[name]],
                )

        # The reference's own head placeholder, held against the fence it
        # states two lines earlier -- the fence asserted equal to the study's
        # just above. `step-<n>-<head-sha>` in the prose beside
        # `step-<n>-<full-head-sha>` in the fence is one contract naming two
        # different directories for one boundary.
        fence_placeholders = sorted(
            {
                placeholder
                for _, placeholder in boundary_names(
                    [line.split("/", 1)[0] for line in first_column(reference_store_fence)],
                    "reference store path fence boundary directory",
                )
            }
        )
        self.assertEqual(1, len(fence_placeholders), fence_placeholders)
        for stem, placeholder in stated["reference"]:
            with self.subTest(boundary=stem, value="head placeholder"):
                self.assertEqual(fence_placeholders[0], placeholder)

        # The thirteen closed manifest fields (study section 1). The reference
        # states them as table rows and the study as one sentence, so the rows
        # are compared in order and the study is required to name each field in
        # the same order.
        manifest_rows = [
            match
            for match in (
                MANIFEST_ROW.match(line)
                for line in section(reference, "Content manifest").splitlines()
            )
            if match
        ]
        self.assertEqual(
            list(EXPECTED_MANIFEST_FIELDS),
            [match.group("field") for match in manifest_rows],
        )
        study_manifest = anchored(
            problem,
            "`checkpoint.json` is closed to:",
            "\n\n",
            "study section 1 closed manifest fields",
        )
        seen = -1
        for field in EXPECTED_MANIFEST_FIELDS:
            with self.subTest(manifest_field=field):
                at = study_manifest.find(f"`{field}`")
                self.assertNotEqual(-1, at, f"the study does not name `{field}`")
                self.assertGreater(at, seen, f"`{field}` is out of order in the study")
                seen = at

        # Each row's `closed to` cell against the study's parenthetical for the
        # same field, so a sub-field dropped, renamed or retyped in one document
        # and not the other fails here. `schema` carries no parenthetical in the
        # study sentence and its cell is the schema name `EXPECTED_SCHEMAS`
        # already holds, so it is asserted against that name instead.
        study_closed = {
            match.group("field"): normalise_closed(match.group("closed"))
            for match in STUDY_MANIFEST_FIELD.finditer(flat(study_manifest))
        }
        self.assertEqual(
            set(EXPECTED_MANIFEST_FIELDS) - {"schema"},
            set(study_closed),
            "study section 1 states no closed field list for each manifest field",
        )
        reference_closed = {
            match.group("field"): normalise_closed(match.group("closed"))
            for match in manifest_rows
        }
        self.assertEqual("fiat-checkpoint-archive/v1", reference_closed["schema"])
        for field in EXPECTED_MANIFEST_FIELDS:
            if field == "schema":
                continue
            with self.subTest(closed_field=field):
                self.assertEqual(study_closed[field], reference_closed[field])

        # Every path the `joined against` column names is a path the layout
        # fence states, and that fence is asserted equal to the study's above,
        # so a join renamed on its own is a reference naming one path in its
        # layout and another in its manifest -- a contradiction Step 2's
        # exporter would have to resolve by guessing. `proof/allowed_signers`
        # is named in the fence's description column, so the whole block is the
        # comparison rather than its first column.
        for match in manifest_rows:
            for span in CODE_SPAN.findall(match.group("joined")):
                if "/" not in span:
                    continue
                with self.subTest(joined_path=span):
                    self.assertIn(
                        span,
                        reference_layout_block,
                        f"the manifest join names `{span}`, absent from the layout",
                    )

        # The seven ceiling values (study section 1). The two documents wrap and
        # punctuate the list differently, so the values are compared as ordered
        # quantities and the unit-bearing phrases are required in both.
        reference_ceilings = section(reference, "Ceilings")
        study_ceilings = anchored(
            problem,
            "Ceilings (safety, not performance):",
            "\n\n",
            "study section 1 ceilings",
        )
        self.assertEqual(list(EXPECTED_CEILINGS), ceiling_numbers(reference_ceilings))
        self.assertEqual(list(EXPECTED_CEILINGS), ceiling_numbers(study_ceilings))
        for name, block in (("reference", reference_ceilings), ("study", study_ceilings)):
            flattened = flat(block)
            for phrase in EXPECTED_CEILING_PHRASES:
                with self.subTest(document=name, ceiling=phrase):
                    self.assertIn(phrase, flattened)
            with self.subTest(document=name, ceiling="255 per component"):
                self.assertRegex(flattened, r"255 (?:bytes )?per component")

        # The zip metadata rule, entry mode included (study section 1).
        reference_container = flat(section(reference, "Container"))
        study_container = flat(
            anchored(
                problem,
                "The zip is a pure container",
                "Layout, fixed:",
                "study section 1 container rule",
            )
        )
        for name, block in (
            ("reference", reference_container),
            ("study", study_container),
        ):
            for clause in EXPECTED_CONTAINER_CLAUSES:
                with self.subTest(document=name, clause=clause):
                    self.assertIn(clause, block)

        # The `entry-mode` refusal row names the mode the container rule fixes,
        # so the reference cannot state one mode and refuse against another.
        entry_mode_rows = [
            line
            for line in section(reference, "Refusal classes").splitlines()
            if line.startswith("| `entry-mode` |")
        ]
        self.assertEqual(1, len(entry_mode_rows), entry_mode_rows)
        self.assertIn(f"`{EXPECTED_ENTRY_MODE}`", entry_mode_rows[0])

        # The bundle determinism command (study section 3, constraint 12).
        reference_layout = flat(section(reference, "Layout"))
        study_bundle = flat(
            anchored(
                constraints,
                "Determinism rule for the bundle:",
                "\n",
                "study section 3 bundle determinism rule",
            )
        )
        self.assertIn(BUNDLE_COMMAND, reference_layout)
        self.assertIn(BUNDLE_COMMAND, study_bundle)
        self.assertNotIn(UNTHREADED_BUNDLE_COMMAND, reference_layout)

        # The six secret patterns (study section 4). Five are code spans that
        # are identical in both documents; the PEM block is prose in both.
        reference_secret_items = [
            line
            for line in section(reference, "Secret patterns").splitlines()
            if line.startswith("- ")
        ]
        self.assertEqual(6, len(reference_secret_items), reference_secret_items)
        study_secrets = anchored(
            anchored(options, "- Secret scan at export", "\n- ", "study section 4 secret scan"),
            "controller file:",
            ". A hit",
            "study section 4 secret pattern list",
        )
        self.assertEqual(
            list(EXPECTED_AMENDED_SECRET_SPANS),
            secret_spans("\n".join(reference_secret_items)),
        )
        self.assertEqual(list(EXPECTED_SECRET_SPANS), secret_spans(study_secrets))
        self.assertIn(EXPECTED_PEM_PROSE, flat("\n".join(reference_secret_items)))
        self.assertIn(EXPECTED_PEM_PROSE, flat(study_secrets))

        # The reference is allowed to differ from section 4's bullet only where
        # a dated study amendment says so, so the amendment is read here too:
        # it must name both the span it drops and the span it puts in its
        # place. Without this the two expectations above would be a constant
        # holding the reference to itself, and an amended value could drift.
        amendment = flat(
            anchored(
                study,
                PATTERN_AMENDMENT_HEADING,
                "\n**Steps touched.**",
                "study amendment 2026-09-09",
            )
        )
        self.assertIn(f"`{SUBSUMED_PATTERN_SPAN}`", amendment)
        self.assertIn(f"`{ADDED_PATTERN_SPAN}`", amendment)

        # The exporter compiles what the reference states. Five bullets are the
        # pattern source verbatim; the sixth is the PEM prose, held instead to
        # what it must and must not match, including the OpenSSH header the
        # amendment dropped as subsumed and the OpenPGP block it added.
        module = hexctl_module()
        compiled = [
            pattern.pattern.decode("utf-8")
            for pattern in module.CHECKPOINT_ARCHIVE_SECRET_PATTERNS
        ]
        self.assertEqual(6, len(compiled), compiled)
        self.assertEqual(list(EXPECTED_AMENDED_SECRET_SPANS), compiled[1:])
        pem = module.CHECKPOINT_ARCHIVE_SECRET_PATTERNS[0]
        for header in (
            b"-----BEGIN PRIVATE KEY-----",
            b"-----BEGIN RSA PRIVATE KEY-----",
            b"-----BEGIN EC PRIVATE KEY-----",
            b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
            SUBSUMED_PATTERN_SPAN.encode("utf-8"),
        ):
            with self.subTest(pem_header=header):
                self.assertTrue(pem.search(header), header)
        self.assertIsNone(pem.search(ADDED_PATTERN_SPAN.encode("utf-8")))
        self.assertIsNone(pem.search(b"-----BEGIN PGP PUBLIC KEY BLOCK-----"))

        # The closed fields of the result objects (study sections 1 and 4).
        # The reference states each as a paragraph and the study as a bullet or
        # a sentence, wrapped and punctuated differently, so the ordered code
        # spans are the comparison: a field dropped, renamed, retyped or
        # reordered in one document and not the other fails here.
        results = section(reference, "Results and proof")
        study_sections = {"problem": problem, "options": options}
        for what, start, end, where, study_start, study_end in RESULT_OBJECTS:
            with self.subTest(result_object=what):
                self.assertEqual(
                    code_spans(
                        anchored(
                            study_sections[where],
                            study_start,
                            study_end,
                            f"study {what} fields",
                        )
                    ),
                    code_spans(anchored(results, start, end, f"reference {what} fields")),
                )

        # The restore result. Study section 1 states four of its six members,
        # so those four are a bound on the reference's rather than a
        # field-for-field comparison.
        reference_restore = anchored(
            results, RESTORE_RESULT_ANCHOR, "\n\n", "reference restore result"
        )
        self.assertLessEqual(
            set(
                code_spans(
                    anchored(
                        problem,
                        STUDY_RESTORE_RESULT_ANCHOR,
                        STUDY_RESTORE_RESULT_END,
                        "study section 1 restore result",
                    )
                )
            ),
            set(code_spans(reference_restore)),
            "the reference's restore result drops a member study section 1 states",
        )

        # Its other two members are pinned over the reference alone, because
        # the study states neither: `fiat-controller-checkpoint-restore` does
        # not appear in it, and `outer_sha256` appears only in the export
        # result, the inspect result and section 8's first answer, never as a
        # member of a restore result. The native object is pinned with its
        # qualifier, because an object of that name that is not the
        # controller's own is a different contract to build against.
        self.assertIn(NATIVE_RESTORE_OBJECT, flat(reference_restore))
        self.assertIn(RESTORE_OUTER_DIGEST_MEMBER, code_spans(reference_restore))

        # The `## Restore transaction` heading, which is where the reference
        # states the transaction the Exit requires it to state.
        self.assertIn(f"\n## {RESTORE_HEADING}\n", reference)
        self.assertTrue(
            section(reference, RESTORE_HEADING).strip(),
            "the reference's `## Restore transaction` section is empty",
        )

        # The sidecar's two spaces, unflattened so the spacing is the evidence.
        for name, document in (("reference", reference), ("study", study)):
            with self.subTest(document=name, rule="sidecar two spaces"):
                self.assertIn(SIDECAR_SPAN, document)
                self.assertNotIn(SIDECAR_ONE_SPACE, document)

        # The block paragraph, on the same terms as every other value above.
        self.pin_the_reference_block_paragraph()

        # The `acceptance/current` rule, stated three ways in the reference and
        # two in the study, so an inverted sentence fails rather than passing on
        # a substring of itself.
        self.assertIn(ACCEPTANCE_NEVER_WRITTEN, reference)
        acceptance_rows = [
            line
            for line in section(reference, "Refusal classes").splitlines()
            if line.startswith(ACCEPTANCE_REFUSAL_ROW)
        ]
        self.assertEqual(1, len(acceptance_rows), acceptance_rows)
        self.assertIn(ACCEPTANCE_REFUSAL_CONDITION, acceptance_rows[0])
        self.assertIn(ACCEPTANCE_OUTSIDE, section(reference, "Content manifest"))
        self.assertIn(ACCEPTANCE_OUTSIDE, study_manifest)
        self.assertIn(STUDY_ACCEPTANCE_REFUSES, study)

    def pin_the_reference_block_paragraph(self):
        """The reference's block paragraph, held to what study section 4 says.

        Two assertions, and each one catches what the other cannot. The
        equality catches a mutated or deleted value in the reference, which
        was S2-R3-03: four anchored edits to this paragraph, one of them
        deleting it and one inverting the truncated-key rule, left every test
        that read the file green. The parity rows catch the drift the equality
        would freeze in place: a dated study amendment that moves one of these
        rules fails here, so the reference cannot quietly stay behind it.

        It is called from the test above rather than from the export test that
        first carried it, and rather than standing as a test of its own, which
        step 5's exact count over this module forbids. That was S2-R4-01: the
        export class skips itself whenever `gpg` is absent, and with the pin
        inside it all eight anchored edits below passed again, deletion of the
        paragraph included. Nothing this pin reads needs `gpg`, and this class
        is where every other value shared by the two documents is held.
        """
        reference = read(REFERENCE)
        study = flat(read(STUDY))
        paragraph = REFERENCE_BLOCK_ANCHOR + anchored(
            reference,
            REFERENCE_BLOCK_ANCHOR,
            REFERENCE_BLOCK_END,
            "the reference's private-key block paragraph",
        )
        self.assertEqual(EXPECTED_BLOCK_PARAGRAPH, flat(paragraph))
        for stated, restated in BLOCK_RULE_PARITY:
            with self.subTest(rule=stated):
                self.assertIn(stated, study)
                self.assertIn(restated, EXPECTED_BLOCK_PARAGRAPH)
        # The three counts the paragraph names are the shipped tuples, so a
        # pattern added or dropped in the code contradicts the prose here.
        module = hexctl_module()
        self.assertEqual(2, len(module.CHECKPOINT_ARCHIVE_SECRET_BLOCK_PATTERNS))
        self.assertEqual(4, len(module.CHECKPOINT_ARCHIVE_SECRET_TOKEN_PATTERNS))
        self.assertEqual(6, len(module.CHECKPOINT_ARCHIVE_SECRET_PATTERNS))
        # So are the two reaches and the declared key size it names, since
        # S2-R7-01 split them: a constant moved without the paragraph, or the
        # paragraph without the constant, contradicts the other here.
        footer_reach = getattr(
            module, "CHECKPOINT_ARCHIVE_SECRET_FOOTER_LOOKAHEAD", None
        )
        largest_key = getattr(module, "CHECKPOINT_ARCHIVE_SECRET_LARGEST_KEY", None)
        self.assertIsNotNone(footer_reach, "the scan declares no footer reach")
        self.assertIsNotNone(largest_key, "the scan declares no largest key")
        self.assertIn(
            f"block lookahead of {module.CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD:,} bytes",
            EXPECTED_BLOCK_PARAGRAPH,
        )
        self.assertIn(f"footer reach of {footer_reach:,} bytes", EXPECTED_BLOCK_PARAGRAPH)
        self.assertIn(f"declared at {largest_key:,} bits", EXPECTED_BLOCK_PARAGRAPH)

    def test_archive_budgets_declare_the_six_measured_limits(self):
        budgets = load_metron().load_budgets(str(BUDGETS))
        self.assertEqual(6, len(budgets))
        declared = {entry["name"]: entry for entry in budgets}
        self.assertEqual(sorted(EXPECTED_BUDGETS), sorted(declared))
        for name, (unit, limit) in EXPECTED_BUDGETS.items():
            with self.subTest(budget=name):
                entry = declared[name]
                self.assertEqual(unit, entry["unit"])
                self.assertEqual(limit, entry["limit"])
                self.assertEqual(0.25, entry["variance"])
                self.assertEqual("lower_is_better", entry["direction"])

        reference = read(REFERENCE)
        budgets_section = section(reference, "Budgets")
        for name in EXPECTED_BUDGETS:
            self.assertIn(f"`{name}`", budgets_section)
        self.assertIn("checkpoint-archive-budgets.json", budgets_section)

        # Both prose tables restate every declared limit, and the reference is
        # the contract the later steps are built against. Holding the three
        # statements equal is what keeps a drifted number from becoming the
        # ceiling an implementer reads while every other gate stays green.
        reference_rows = budget_rows(reference, "Budgets")
        self.assertEqual(6, len(reference_rows), reference_rows)
        self.assertEqual(budget_rows(read(STUDY), STUDY_BUDGET_HEADING), reference_rows)
        for row in reference_rows:
            fields = BUDGET_ROW.match(row)
            with self.subTest(budget=fields.group("name")):
                self.assertIn(fields.group("name"), declared, row)
                entry = declared[fields.group("name")]
                self.assertEqual(entry["unit"], fields.group("unit"))
                self.assertEqual(entry["limit"], int(fields.group("limit")))

    def test_refusal_classes_after_git_init_are_the_four_the_reference_qualifies(self):
        """S4-R5-01: the post-`git init` class set, computed rather than read.

        Study section 11 says any section-4 refusal class exits 1 before the
        destination repository exists. Four classes cannot hold that clause,
        and the qualification the reference owes has to name exactly those
        four -- rounds 1 to 3 each enumerated them by reading the restore
        path, and each enumeration was short: round 3 named three where there
        were four, and round 4 named four where `trailing-data` made five.

        So this computes the set instead. It takes every call `checkpoint
        restore --archive` makes at or after its `git init`, closes over
        every module function those calls can reach, and collects every
        refusal class named by a literal anywhere in that closure. The
        closure follows attribute calls by bare name as well as direct ones,
        so it over-approximates: a class it does not report is unreachable
        after `git init`, which is the direction this guard needs.

        A fifth class appearing here is not necessarily a defect in the code.
        It is a statement in the study that has stopped being true, and the
        two have to be repaired together.
        """
        tree = hexctl_tree()
        functions = module_functions(tree)
        restore = functions["_checkpoint_restore_from_archive"]
        git_init = min(
            node.lineno
            for node in ast.walk(restore)
            if isinstance(node, ast.Constant) and node.value == "init"
        )

        seeds = set()
        after = [
            node
            for node in ast.walk(restore)
            if isinstance(node, ast.Call) and node.lineno >= git_init
        ]
        for call in after:
            function = call.func
            if isinstance(function, ast.Name):
                seeds.add(function.id)
            elif isinstance(function, ast.Attribute):
                seeds.add(function.attr)
            for argument in call.args:
                seeds |= called_names(argument)

        reached, pending = set(), list(seeds)
        while pending:
            name = pending.pop()
            if name in reached or name not in functions:
                continue
            reached.add(name)
            pending.extend(called_names(functions[name]))

        classes = set()
        for call in after:
            classes |= refusal_literals(call)
        for name in reached:
            classes |= refusal_literals(functions[name])

        self.assertEqual(
            {
                "manifest-mismatch",
                "ref-disagreement",
                "identity-mismatch",
                "identity-unavailable",
            },
            classes,
            "the set of refusal classes reachable once the destination "
            "repository exists has changed, so study section 11's "
            "qualification names the wrong classes",
        )

    def test_controller_constants_carry_the_study_enumerations(self):
        """S4-R5-01: the study's closed lists, joined to the code that runs.

        `test_archive_reference_names_every_refusal_class_and_fixture_id`
        above holds the reference document to the study. Nothing held either
        document to the controller, so a class, field, ceiling or pattern
        could drift in `hexctl.py` alone and both documents would still agree
        with each other. These are the same five enumerations, read from the
        module and from the test module's own methods.
        """
        study = read(STUDY)
        module = hexctl_module()

        classes = set(module.CHECKPOINT_ARCHIVE_REFUSALS)
        self.assertEqual(24, len(classes))
        self.assertEqual(study_refusal_classes(study), classes)

        methods = {
            name
            for name in dir(CheckpointArchiveInspectTests)
            if name.startswith("test_hostile_")
        }
        self.assertEqual(35, len(methods))
        self.assertEqual(
            {"test_hostile_" + fixture.replace("-", "_")
             for fixture in study_fixture_ids(study)},
            methods,
        )

        fields = manifest_closed_fields(hexctl_tree())
        self.assertEqual(13, len(fields))
        self.assertEqual(set(EXPECTED_MANIFEST_FIELDS), fields)

        self.assertEqual(
            EXPECTED_CEILINGS,
            (
                module.CHECKPOINT_ARCHIVE_ENTRIES_MAX,
                module.CHECKPOINT_ARCHIVE_EXPANDED_BYTES_MAX // (1024 * 1024),
                module.CHECKPOINT_ARCHIVE_BUNDLE_BYTES_MAX // (1024 * 1024 * 1024),
                module.CHECKPOINT_ARCHIVE_ENTRY_BYTES_MAX // (1024 * 1024),
                module.CHECKPOINT_ARCHIVE_NAME_BYTES_MAX,
                module.CHECKPOINT_ARCHIVE_COMPONENT_BYTES_MAX,
                module.CHECKPOINT_ARCHIVE_ACCEPTANCE_MAX,
            ),
        )

        patterns = module.CHECKPOINT_ARCHIVE_SECRET_PATTERNS
        self.assertEqual(6, len(patterns))
        sources = [pattern.pattern.decode("ascii") for pattern in patterns]
        self.assertEqual(list(EXPECTED_AMENDED_SECRET_SPANS[1:]), sources[2:])
        self.assertEqual(ADDED_PATTERN_SPAN, sources[1])
        # The amendment's own reason for dropping the OpenSSH header: the PEM
        # pattern before it already matches that header.
        self.assertIsNotNone(
            patterns[0].search(SUBSUMED_PATTERN_SPAN.encode("ascii"))
        )

    def test_capsule_extraction_diagnoses_a_captured_copy_read_failure_as_itself(self):
        """S4-R5-01: a short read of the scratch copy is not `trailing-data`.

        Capsule extraction reads the inspector's captured copy after `git
        init` has filled the destination. Every member it reads was digested
        and accepted against the central directory before that, so a short
        read or an `OSError` at this point is a fact about this process's own
        scratch file and not about the archive's byte layout -- which is what
        `trailing-data` asserts, and what the risk register defines it as.

        The condition is driven directly rather than through the command,
        because inducing it through `checkpoint restore --archive` means
        changing the scratch copy inside the window between the inspector
        returning and extraction reading, and that window has no command-line
        surface. The bound is worth stating: this establishes the diagnosis
        at the extraction site, not the residue an operator meeting it finds.
        """
        module = hexctl_module()
        scratch = tempfile.mkdtemp(prefix="fiat861-r5-extract-")
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        local = os.path.join(scratch, "captured.zip")
        with open(local, "wb") as handle:
            handle.write(b"short")
        destination = os.path.join(scratch, "destination")
        os.makedirs(destination, 0o700)
        physical = [
            {
                "name": module.CHECKPOINT_ARCHIVE_CAPSULE_DIR + "/MANIFEST.json",
                "data_offset": 0,
                "size": 4096,
            }
        ]

        captured = StringIO()
        with redirect_stderr(captured):
            with self.assertRaises(SystemExit) as stopped:
                module._checkpoint_restore_archive_extract_capsule(
                    local, physical, destination, "0" * 64
                )

        self.assertEqual(
            2,
            stopped.exception.code,
            "a failed read of this process's own captured copy exited as a "
            "bounded archive refusal, which states something about the "
            "archive that the inspector already accepted",
        )
        self.assertNotIn("trailing-data", captured.getvalue())
        self.assertIn("capsule member could not be read", captured.getvalue())

    def test_source_verification_does_not_echo_the_producers_own_path(self):
        """S4-R6-01: a receipt outside `.hexaemeron/` printed the producer's path.

        `_checkpoint_restore_verify_source` derives one sanitised, portable
        relative path from the receipt and then, for an artefact outside the
        controller directory, handed the whole state to `receipted_source`.
        That reader re-reads the receipt's own `artifact` field rather than
        the derived path, and that field is still the producer's: for a run
        whose receipt recorded an absolute path it resolves outside the
        restored worktree every time, so `scoped_path` refuses it by printing
        the path it was handed. The refusal therefore carried the producer's
        home directory, account name and project name to stderr, out of a
        command whose whole purpose is to keep the archive's bytes inside its
        stage, and after `git init` has already filled the destination.

        Driven directly, for the reason the sibling above states: the value
        reaching this reader is the relocated state's, and there is no
        command-line surface that supplies one receipt path without supplying
        a whole archive built around it.

        The bound is worth stating: this establishes what the refusal prints,
        not that any particular archive reaches this branch.
        """
        module = hexctl_module()
        origin = "/Users/victim/secret-client-engagement"
        branch = "fiat/861-source-leak"
        producer_worktree = os.path.join(
            origin, *module.WORKTREE_HOME, branch.replace("/", "-")
        )
        artifact = os.path.join(producer_worktree, "docs", "study.md")
        state = {
            "run_branch": branch,
            "config": {"git": {"origin": origin, "worktree": producer_worktree}},
            "receipts": {
                "study": {
                    "sha256": hashlib.sha256(b"study bytes").hexdigest(),
                    "artifact": artifact,
                }
            },
        }
        scratch = tempfile.mkdtemp(prefix="fiat861-r6-source-")
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        destination = os.path.join(scratch, "worktree")
        stage = os.path.join(scratch, "stage")
        os.makedirs(destination, 0o700)
        os.makedirs(stage, 0o700)

        captured = StringIO()
        with redirect_stderr(captured):
            with self.assertRaises(SystemExit) as stopped:
                module._checkpoint_restore_verify_source(
                    destination, stage, state, "study"
                )

        diagnosis = captured.getvalue()
        self.assertEqual(2, stopped.exception.code)
        self.assertNotIn(
            origin,
            diagnosis,
            "the refusal carried the producer's home directory and project "
            "name to stderr, which is the source-path leak the register's "
            "`diagnostic-leak` row refuses",
        )
        self.assertNotIn(
            artifact,
            diagnosis,
            "the refusal echoed the receipt's own archive-supplied path",
        )
        self.assertNotIn("escapes target directory", diagnosis)

    def test_every_checkpoint_call_to_the_path_echoing_reader_is_sanitised(self):
        """S4-R6-01: the containment exists; pin that every call site uses it.

        `receipted_source` refuses through `scoped_path`, which prints the path
        it was handed. The module already states the remedy: the docstring of
        `_checkpoint_identity_sanitized` is "Run a legacy verifier without
        letting its path-bearing errors escape", and the identity route wraps
        this exact reader in it. The restore route called the same reader on
        the same archive-derived state and did not, which is the leak the
        sibling above drives.

        The repair removed that call rather than wrapping it, because reading
        the receipt's own pre-relocation path in the restored worktree could
        never have succeeded. This pins the resulting property structurally,
        so a later call site added without the containment is caught here
        rather than by the next enumeration: every `receipted_source` call
        inside a checkpoint function is lexically inside a
        `_checkpoint_identity_sanitized` call.

        The bound: this reads call sites, not reachability, so it says nothing
        about which of them an archive can drive.
        """
        module = hexctl_module()
        tree = ast.parse(
            pathlib.Path(inspect.getsourcefile(module)).read_text(encoding="utf-8")
        )
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node

        def sanitised(node):
            while node in parents:
                node = parents[node]
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_checkpoint_identity_sanitized"
                ):
                    return True
            return False

        unsanitised = []
        for owner in tree.body:
            if not isinstance(owner, ast.FunctionDef):
                continue
            if not owner.name.startswith("_checkpoint_"):
                continue
            for sub in ast.walk(owner):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "receipted_source"
                    and not sanitised(sub)
                ):
                    unsanitised.append(f"{owner.name}:{sub.lineno}")

        self.assertEqual(
            [],
            unsanitised,
            "a checkpoint reader calls `receipted_source` without the "
            "containment `_checkpoint_identity_sanitized` exists for, so its "
            "refusal prints the receipt's own path",
        )


class RunAnchorRepositoryAdmissionTests(unittest.TestCase):
    """S4-R7-01: what the restore may interpolate into `remote.origin.url`.

    `_checkpoint_restore_from_archive` writes the destination's origin from
    `receipts.run_anchor.repository`, and `validate_run_anchor_shape` is the
    only gate between the archive's bytes and that write. Before this round
    that gate was the bare `REPOSITORY_RE` pattern plus a lowercase rule,
    while `target_repository_binding` -- the one function that ever mints a
    repository, and the one that reads the written URL back -- additionally
    refuses a `.` or `..` segment. These two cases hold the accepting
    validator to the minting one.
    """

    # Owner/name forms a hostile archive can put in its anchor. The first is
    # the honest shape; the six after it are the relative-segment family.
    HONEST = "wildcat-finance/skills"
    RELATIVE_SEGMENT = (
        "./skills",
        "../skills",
        "wildcat-finance/.",
        "wildcat-finance/..",
        "../..",
        "./.",
    )
    # Admitted, and each must survive the round trip unchanged.
    ADMITTED = (
        HONEST,
        ".../skills",
        ".git/skills",
        "wildcat-finance/.git",
        "wildcat-finance/skills.git",
        "wildcat-finance.git/skills",
        "wildcat-finance/skills.",
        "wildcat-finance/skills.git.git",
        "-upload-pack/skills",
        "wildcat-finance/-o",
    )

    def anchor(self, repository):
        module = hexctl_module()
        return {
            "schema": module.RUN_ANCHOR_SCHEMA,
            "controller": {
                "name": "hexctl",
                "state_version": 1,
                "version": "fiat-v5.53.1",
            },
            "initial_base_sha": "0" * 40,
            "integration_branch": "main",
            "repository": repository,
            "run_branch": "fiat/861-anchor-admission",
            "run_id": "fiat-" + ("0" * 64),
            "task": dict(module.RUN_ANCHOR_TASK_NONE),
        }

    def test_run_anchor_repository_refuses_a_relative_path_segment(self):
        module = hexctl_module()
        self.assertEqual(
            self.anchor(self.HONEST),
            module.validate_run_anchor_shape(self.anchor(self.HONEST)),
        )
        for repository in self.RELATIVE_SEGMENT:
            with self.subTest(repository=repository):
                self.assertIsNotNone(
                    module.REPOSITORY_RE.fullmatch(repository),
                    "the bare pattern is what makes this case worth guarding",
                )
                with redirect_stderr(StringIO()) as captured:
                    with self.assertRaises(SystemExit) as raised:
                        module.validate_run_anchor_shape(self.anchor(repository))
                self.assertEqual(1, raised.exception.code)
                self.assertEqual(
                    "hexctl: error: run anchor repository identity is malformed\n",
                    captured.getvalue(),
                )
                self.assertNotIn(repository, captured.getvalue())

    def test_every_repository_the_anchor_admits_survives_the_minting_validator(self):
        """The property, not the six specimens: anything this gate admits must
        read back out of the URL the restore builds as the same repository."""
        module = hexctl_module()
        root = tempfile.mkdtemp(prefix="fiat861-anchor-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        for index, repository in enumerate(self.ADMITTED + self.RELATIVE_SEGMENT):
            with self.subTest(repository=repository):
                try:
                    with redirect_stderr(StringIO()):
                        module.validate_run_anchor_shape(self.anchor(repository))
                except SystemExit:
                    continue
                # exactly the interpolation `_checkpoint_restore_from_archive`
                # performs when it records the origin remote
                url = f"https://github.com/{repository}.git"
                work = os.path.join(root, str(index))
                subprocess.run(
                    ["git", "init", "-q", work], check=True, capture_output=True
                )
                subprocess.run(
                    ["git", "-C", work, "config", "remote.origin.url", url],
                    check=True,
                    capture_output=True,
                )
                with redirect_stderr(StringIO()) as captured:
                    try:
                        read_back = module.target_repository_binding(work)
                    except SystemExit:
                        read_back = f"refused: {captured.getvalue().strip()}"
                self.assertEqual(
                    repository,
                    read_back,
                    "the anchor gate admitted a repository the minting "
                    "validator will not read back, so the restore writes an "
                    "origin its own `verify` refuses",
                )


class SignedRunFixture(HexctlCase):
    """One real, really signed run, shared by every test that needs its archive.

    The controller fixture fakes the delivery tools a run talks to, which is
    right for receipts and wrong for an archive: a bundle built from invented
    SHAs carries no objects, and a signature proof read from a canned trailer
    block proves nothing. So this fixture keeps the fake `gh` and the fake ref
    reader, points the fake ref map at the commits it really made, and signs
    those commits with an OpenPGP key generated into a temporary `GNUPGHOME`
    for the class. Nothing here reads or writes the operator's keyring.

    This class carries no test of its own: it is a plain `unittest.TestCase`
    subclass only because its fixture methods need one, and `unittest`
    collects tests by walking a class's methods, inherited ones included, so
    a shared base that held its own `test_*` method would run it again under
    every subclass. `CheckpointArchiveExportTests` and
    `CheckpointArchiveInspectTests` hold the cases; both inherit from here.
    """

    key_home = None
    fingerprint = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("gpg") is None:
            return
        # A gpg-agent's socket lives in its home and AF_UNIX paths are capped
        # near 104 bytes, so the names below stay short. The system temporary
        # root, canonicalised above, leaves room; a name under the tree would
        # not, and `tests/test_scratch_quiescence.py` forbids anchoring there
        # anyway.
        cls.key_root = tempfile.mkdtemp(prefix="fiat861-")
        cls.key_home = os.path.join(cls.key_root, "h")
        os.mkdir(cls.key_home, 0o700)
        generated = subprocess.run(
            [
                "gpg",
                "--batch",
                "--quiet",
                "--pinentry-mode",
                "loopback",
                "--passphrase",
                "",
                "--quick-generate-key",
                "Fiat Fixture <fixture@example.invalid>",
                "ed25519",
                "sign",
                "never",
            ],
            env={**os.environ, "GNUPGHOME": cls.key_home},
            capture_output=True,
            text=True,
        )
        if generated.returncode != 0:
            cls.key_home = None
            return
        listed = subprocess.run(
            ["gpg", "--batch", "--with-colons", "--list-secret-keys"],
            env={**os.environ, "GNUPGHOME": cls.key_home},
            capture_output=True,
            text=True,
        )
        for line in listed.stdout.splitlines():
            if line.startswith("fpr:"):
                cls.fingerprint = line.split(":")[9]
                break
        if cls.fingerprint is None:
            cls.key_home = None

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "key_home", None) is None:
            return
        subprocess.run(
            ["gpgconf", "--homedir", cls.key_home, "--kill", "all"],
            capture_output=True,
        )
        shutil.rmtree(cls.key_root, ignore_errors=True)

    def setUp(self):
        if self.key_home is None:
            self.skipTest("gpg is unavailable, so no fixture key can be generated")
        super().setUp()
        self.env["GNUPGHOME"] = self.key_home
        self.git("remote", "add", "origin", ORIGIN_URL)
        self.git("config", "user.signingkey", self.fingerprint)
        self.git("config", "gpg.program", "gpg")
        self.fake_refs["main"] = self.head_sha()

    # -- fixture ---------------------------------------------------------

    def head_sha(self, ref="HEAD"):
        return self.git("rev-parse", ref).stdout.strip()

    def commit_signed(self, message, *, amend=False):
        """One real commit, really signed by the fixture key and nothing else."""
        subprocess.run(
            [
                "git",
                "-c",
                "commit.gpgsign=true",
                "-c",
                f"user.signingkey={self.fingerprint}",
                "-c",
                "gpg.program=gpg",
                "commit",
                "-q",
                *(("--amend",) if amend else ()),
                "-m",
                message,
            ],
            cwd=self.target,
            env={**os.environ, "GNUPGHOME": self.key_home},
            check=True,
            capture_output=True,
        )
        return self.head_sha()

    def signed_commit(self, message, path="work.txt"):
        full = os.path.join(self.target, path)
        with open(full, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
        self.git("add", path)
        return self.commit_signed(message)

    @staticmethod
    def trailers(subject="fixture work"):
        return f"{subject}\n\n{COAUTHOR}\n{ORIGIN_TRAILER}\n"

    def to_receipted_steps(self, titles=("First", "Second")):
        self.init()
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\npacket | boundary | check\n```\n",
        )
        self.run_ctl(
            "done", "study", "--artifact", study, "--skills", "hexaemeron:imprimatur"
        )
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            + "\n".join(
                f"## Step {number}: {title}\n\n**Goal.** Ship {title}.\n"
                for number, title in enumerate(titles, 1)
            ),
        )
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl("done", "runbook", "--artifact", runbook, "--steps-file", steps)
        self.git("add", study, runbook, steps)
        self.git("commit", "-q", "-m", "fixture sources")
        state = self.state()
        self.fake_refs[state["run_branch"]] = self.head_sha()
        for step in state["steps"]:
            self.git("branch", self.step_branch(step["n"], state))
            self.fake_refs[self.step_branch(step["n"], state)] = self.head_sha()
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        return state

    def implement_step(self, number):
        """Put one really signed commit on the step branch and receipt it."""
        branch = self.step_branch(number)
        self.git("checkout", "-q", branch)
        head = self.signed_commit(self.trailers(f"step {number}"))
        self.fake_refs[branch] = head
        self.run_ctl("done", "implement", "--branch", branch, "--commit", head)
        return head

    def to_post_push(self, titles=("First", "Second"), message=None):
        """One run standing at its post-push boundary with a really signed head.

        The harness commits the fixture audit record itself, unsigned, so the
        branch tip after a round is not the commit the step signed. Amending
        that commit into a signed one keeps the receipted head and the real
        head the same object, which is the state a genuine run is in.
        """
        self.to_receipted_steps(titles=titles)
        branch = self.step_branch(1)
        self.implement_step(1)
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        head = self.commit_signed(message or self.trailers("step 1"), amend=True)
        self.fake_refs[branch] = head
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "3",
            "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", head,
            "--pr-base", self.step_base(1),
        )
        return head

    def archive(self, *, expect=0):
        result = self.run_ctl("checkpoint", "archive", expect=expect)
        payload = json.loads(result.stdout) if expect == 0 else None
        return result, payload

    def store_root(self):
        state = self.state()
        return Path(state["config"]["git"]["origin"]) / ".hexaemeron" / "checkpoints"

    def published(self):
        found = sorted(self.store_root().glob("*/*/checkpoint.zip"))
        self.assertEqual(1, len(found), found)
        return found[0]

    def good_archive(self):
        """One real, published archive from one really signed, receipted run."""
        self.to_post_push()
        self.archive()
        return self.published()

    def good_members(self, path=None):
        with zipfile.ZipFile(path or self.good_archive()) as container:
            return {
                info.filename: container.read(info.filename)
                for info in container.infolist()
            }

    def outer_sha256(self, path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def manifest(self, members):
        return json.loads(members["checkpoint.json"])

    def set_manifest(self, members, manifest_obj):
        module = hexctl_module()
        members["checkpoint.json"] = (
            module.canonical(manifest_obj).encode("utf-8") + b"\n"
        )

    def retarget(self, members, manifest_obj, path, new_bytes):
        """Change one member's bytes and its own manifest record together,
        so only the check under test is left disagreeing with the rest.
        """
        members[path] = new_bytes
        for entry in manifest_obj["archive"]["entries"]:
            if entry["path"] == path:
                entry["bytes"] = len(new_bytes)
                entry["sha256"] = hashlib.sha256(new_bytes).hexdigest()
                if path == "git/repository.bundle":
                    # `checkpoint.json` records the bundle in its own block as
                    # well, and since S3-R3-01 `inspect` joins the two, so a
                    # specimen meant to disagree elsewhere keeps them equal.
                    manifest_obj["bundle"]["bytes"] = entry["bytes"]
                    manifest_obj["bundle"]["sha256"] = entry["sha256"]
                return
        raise AssertionError(f"{path} is not a manifest entry")

    def specimen_path(self, name="specimen.zip"):
        return os.path.join(self.dir, name)

    def write_specimen(self, members, overrides=None, *, path=None):
        """Pack `members` (name -> bytes), sorted by UTF-8 bytes, with any
        named entry's mode, method, flags, extra field or declared central-
        directory size overridden by `overrides`.
        """
        overrides = overrides or {}
        names = sorted(members, key=lambda item: item.encode("utf-8"))
        entries = []
        for name in names:
            entry = {"name": name.encode("utf-8"), "data": members[name]}
            entry.update(overrides.get(name, {}))
            entries.append(entry)
        target = path or self.specimen_path()
        write_raw_zip(target, entries)
        return target

    def controller_bytes(self):
        root = Path(self.target) / ".hexaemeron"
        return (
            root.joinpath("state.json").read_bytes(),
            root.joinpath("ledger.jsonl").read_bytes(),
        )

    def manifest_of(self, archive):
        with zipfile.ZipFile(archive) as container:
            return json.loads(container.read("checkpoint.json"))

    def direct_environment(self):
        environment = dict(self.env)
        environment["FAKE_GIT_REFS"] = json.dumps(self.fake_refs)
        environment["FAKE_GIT_PARENTS"] = json.dumps(self.fake_parents)
        environment["FAKE_GH_PRS"] = json.dumps(self.fake_prs)
        return environment

    def in_process(self, patches=()):
        """Run one export in this process, so a ceiling or reader can be replaced.

        The subprocess surface is what an operator uses and is what every other
        case here drives. Three refusals -- an oversized bundle, a disagreeing
        ref map and a manifest that stopped matching its members -- cannot be
        produced from outside the process without corrupting the fixture into
        something no run could reach, so they are provoked at the seam instead.
        """
        module = hexctl_module()
        error = StringIO()
        output = StringIO()
        stack = ExitStack()
        with stack:
            stack.enter_context(mock.patch.dict(os.environ, self.direct_environment(), clear=True))
            for name, value in patches:
                stack.enter_context(mock.patch.object(module, name, value))
            stack.enter_context(redirect_stderr(error))
            stack.enter_context(redirect_stdout(output))
            try:
                module.cmd_checkpoint_archive(SimpleNamespace(dir=self.target))
            except SystemExit as stopped:
                return stopped.code, output.getvalue(), error.getvalue()
        return 0, output.getvalue(), error.getvalue()


class CheckpointArchiveExportTests(SignedRunFixture):
    """`checkpoint archive` over one real, really signed run: the cases."""

    # -- cases -----------------------------------------------------------

    def test_archive_export_is_byte_identical_across_two_exports_and_two_absolute_paths(self):
        self.to_post_push()
        _, first = self.archive()
        original = self.published().read_bytes()
        sidecar = self.published().with_name("checkpoint.zip.sha256").read_text(
            encoding="utf-8"
        )
        self.assertEqual(f"{first['outer_sha256']}  checkpoint.zip\n", sidecar)

        shutil.rmtree(self.store_root())
        _, second = self.archive()
        self.assertEqual(original, self.published().read_bytes())
        self.assertEqual(first["outer_sha256"], second["outer_sha256"])
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])

        shutil.rmtree(self.store_root())
        elsewhere = self.relocated_copy()
        moved = subprocess.run(
            [sys.executable, HEXCTL, "checkpoint", "archive"],
            cwd=elsewhere,
            capture_output=True,
            text=True,
            env=self.direct_environment(),
        )
        self.assertEqual(0, moved.returncode, moved.stderr)
        self.assertEqual(original, self.published().read_bytes())
        self.assertEqual(first["outer_sha256"], json.loads(moved.stdout)["outer_sha256"])

    def relocated_copy(self):
        """The same run at another absolute path, with its recorded paths untouched.

        Copying rather than editing is the point: the controller state, and so
        the capsule, stays byte for byte what it was, and only the producer's
        location changes. The linked worktree's two pointers are the only
        things that have to follow it.
        """
        other = tempfile.mkdtemp(prefix="fiat861-elsewhere-")
        self.addCleanup(shutil.rmtree, other, True)
        destination = os.path.join(other, "origin")
        shutil.copytree(self.dir, destination, symlinks=True)
        name = os.path.basename(self.target)
        worktree = os.path.join(destination, "tmp", "fiat", name)
        with open(os.path.join(worktree, ".git"), "w", encoding="utf-8") as handle:
            handle.write(f"gitdir: {destination}/.git/worktrees/{name}\n")
        with open(
            os.path.join(destination, ".git", "worktrees", name, "gitdir"),
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(f"{worktree}/.git\n")
        return worktree

    def test_archive_reserves_prior_acceptance_entries(self):
        self.to_post_push()
        _, result = self.archive()
        manifest = self.manifest_of(self.published())
        self.assertEqual("outside", manifest["acceptance"]["current"])
        self.assertEqual([], manifest["acceptance"]["prior"])
        self.assertEqual({"current", "prior"}, set(manifest["acceptance"]))
        with zipfile.ZipFile(self.published()) as container:
            names = container.namelist()
        self.assertNotIn("acceptance/current", names)
        self.assertFalse([name for name in names if name.startswith("acceptance/")])
        self.assertEqual(64, manifest["limits"]["prior_acceptances"])
        self.assertEqual(result["entries"], len(names))

    def test_archive_export_refuses_every_unaccepted_boundary(self):
        def refused(label):
            before = self.controller_bytes()
            result, _ = self.archive(expect=1)
            self.assertEqual("boundary-unaccepted\n", result.stderr, label)
            self.assertFalse(self.store_root().exists(), label)
            self.assertEqual(before, self.controller_bytes(), label)

        self.init()
        refused("study")
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\npacket | boundary | check\n```\n",
        )
        self.run_ctl(
            "done", "study", "--artifact", study, "--skills", "hexaemeron:imprimatur"
        )
        refused("runbook")
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: One\n\n**Goal.** One.\n"
        )
        steps = self.write("steps.json", '["One"]\n')
        self.run_ctl("done", "runbook", "--artifact", runbook, "--steps-file", steps)
        self.git("add", study, runbook, steps)
        self.git("commit", "-q", "-m", "fixture sources")
        state = self.state()
        self.fake_refs[state["run_branch"]] = self.head_sha()
        self.git("branch", self.step_branch(1, state))
        self.fake_refs[self.step_branch(1, state)] = self.head_sha()
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        refused("implement")
        self.implement_step(1)
        refused("audit-before-round")
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        refused("close-audit")
        self.run_ctl("done", "audit")
        refused("prose")

    def test_archive_export_refuses_dirty_worktree(self):
        self.to_post_push()
        # A tracked file the receipts do not pin: a receipted source would
        # refuse at the controller's own verification, one check earlier, and
        # the dirty-tree rule would never be reached.
        with open(os.path.join(self.target, "work.txt"), "a", encoding="utf-8") as handle:
            handle.write("uncommitted\n")
        before = self.controller_bytes()
        result, _ = self.archive(expect=1)
        self.assertEqual("worktree-dirty\n", result.stderr)
        self.assertFalse(self.store_root().exists())
        self.assertEqual(before, self.controller_bytes())

    def test_archive_export_refuses_secret_shaped_member(self):
        """The refusal itself, over a really signed run.

        The reference paragraph that states this rule is pinned in
        `CheckpointArchiveScaffoldTests`, not here: this class skips whenever
        `gpg` is absent, and a document pin that needs no `gpg` must not skip
        with it.
        """
        self.to_post_push()
        planted = Path(self.target) / ".hexaemeron" / "notes.txt"
        planted.write_text("carry over: AKIA" + "A1B2C3D4E5F6G7H8"[:16] + "\n", encoding="utf-8")
        result, _ = self.archive(expect=1)
        self.assertEqual("secret-shaped-member\n", result.stderr)
        self.assertFalse(sorted(self.store_root().glob("*/*")))
        # The OpenSSH header, which the PEM pattern matches on its own, and the
        # OpenPGP block, which the 2026-09-09 study amendment added because no
        # pattern reached it: its header ends `PRIVATE KEY BLOCK-----`. Each is
        # planted as a block, because the second amendment of that date refuses
        # an armour header only when key material follows it.
        for header in (SUBSUMED_PATTERN_SPAN, ADDED_PATTERN_SPAN):
            with self.subTest(header=header):
                planted.write_text(
                    header + "\n" + ARMOURED_BODY_LINE + "\n", encoding="utf-8"
                )
                result, _ = self.archive(expect=1)
                self.assertEqual("secret-shaped-member\n", result.stderr)
        planted.unlink()
        # The same block carried as a JSON string value, which is the shape
        # `state.json` and a `ledger.jsonl` line give a credential and the
        # shape the block rule published until the escape became a delimiter.
        # It is planted alone: with another refusing member still in the
        # capsule this assertion passes against a scan that never read it,
        # which is what the first draft of this test did.
        self.assertNotIn("\n", ARMOURED_BLOCK_JSON_CARRIED)
        carried = Path(self.target) / ".hexaemeron" / "notes.json"
        carried.write_text(ARMOURED_BLOCK_JSON_CARRIED, encoding="utf-8")
        result, _ = self.archive(expect=1)
        self.assertEqual("secret-shaped-member\n", result.stderr)
        self.assertFalse(sorted(self.store_root().glob("*/*")))
        carried.unlink()
        self.archive()

    def test_secret_shaped_member_refuses_before_publish_on_a_truncated_key_block(self):
        """A block whose `-----END` is gone is still key material.

        The block rule admits two witnesses, the footer and a body line, and a
        key truncated in transit carries only the second. Reading the footer
        alone would publish it. The same header with prose after it instead of
        material publishes, which is the refusal S2-R2-02 recorded: the capsule
        carries every controller file, and this run's study quotes that header
        while specifying the scan.
        """
        self.to_post_push()
        planted = Path(self.target) / ".hexaemeron" / "notes.txt"
        # The body witness alone, then the footer witness alone. Each has to
        # refuse by itself, or dropping the other one goes unnoticed.
        footer_only = (
            SUBSUMED_PATTERN_SPAN
            + "\nthis line is not base64\n-----END OPENSSH PRIVATE KEY-----\n"
        )
        for specimen in (ARMOURED_BLOCK_TRUNCATED, footer_only):
            with self.subTest(witness=specimen.splitlines()[1]):
                planted.write_text(specimen, encoding="utf-8")
                result, _ = self.archive(expect=1)
                self.assertEqual("secret-shaped-member\n", result.stderr)
                self.assertFalse(sorted(self.store_root().glob("*/*")))
        planted.write_text(
            f"the scan names {SUBSUMED_PATTERN_SPAN} here, and nothing follows it\n",
            encoding="utf-8",
        )
        self.archive()

    def test_secret_shaped_member_refuses_an_adjacent_header_and_footer(self):
        """A header touching its own footer refuses, carrying no key at all.

        The footer witness asks only that a matching footer sit within the
        footer reach of the header. A document that names both markers on
        consecutive lines satisfies that with nothing between them, so a member
        holding the two markers, their line endings and no key material
        refuses. The test above
        pins the two witnesses in isolation but always puts a line between the
        markers, so this shape went undemonstrated until an export of real
        controller state met it.

        This is the cost of failing closed, not a defect: the rule would have
        to admit key-shaped content between the markers to tell the two apart,
        and narrowing it that way is a design change a dated study amendment
        has to make. What the step owes is that the cost is stated and pinned
        rather than found by the first person to archive a run whose notes
        quote a key header.
        """
        self.to_post_push()
        planted = Path(self.target) / ".hexaemeron" / "notes.txt"
        footer = "-----END OPENSSH PRIVATE KEY-----"
        adjacent = SUBSUMED_PATTERN_SPAN + "\n" + footer + "\n"
        # Nothing but the two markers and their line endings: no base64 line,
        # no body witness, and so no key.
        self.assertEqual(
            len(SUBSUMED_PATTERN_SPAN) + len(footer) + 2,
            len(adjacent.encode("utf-8")),
        )
        planted.write_text(adjacent, encoding="utf-8")
        result, _ = self.archive(expect=1)
        self.assertEqual("secret-shaped-member\n", result.stderr)
        self.assertFalse(sorted(self.store_root().glob("*/*")))
        # The header alone is not enough: dropping the footer witness would
        # leave this refusing too, and the difference is the whole rule.
        planted.write_text(SUBSUMED_PATTERN_SPAN + "\n", encoding="utf-8")
        self.archive()

    def test_archive_export_refuses_oversized_bundle(self):
        self.to_post_push()
        code, _, error = self.in_process(
            (("CHECKPOINT_ARCHIVE_BUNDLE_BYTES_MAX", 1),)
        )
        self.assertEqual(1, code)
        self.assertEqual("bundle-oversized\n", error)
        self.assertFalse(sorted(self.store_root().glob("*/*")))

    def test_archive_export_refuses_ref_disagreement(self):
        self.to_post_push()
        module = hexctl_module()
        honest = module._checkpoint_refs

        def drifted(base_dir, state):
            refs = honest(base_dir, state)
            return {**refs, state["run_branch"]: "0" * 40}

        code, _, error = self.in_process((("_checkpoint_refs", drifted),))
        self.assertEqual(1, code)
        self.assertEqual("ref-disagreement\n", error)
        self.assertFalse(sorted(self.store_root().glob("*/*")))

    def test_archive_export_refuses_occupied_boundary_directory(self):
        self.to_post_push()
        _, first = self.archive()
        published = self.published()
        before = published.read_bytes()
        result, _ = self.archive(expect=1)
        self.assertEqual("boundary-occupied\n", result.stderr)
        self.assertEqual(before, published.read_bytes())
        self.assertEqual(
            [], [entry for entry in published.parent.parent.iterdir() if entry.name.startswith(".")]
        )

    def test_archive_export_refuses_unsupported_signature(self):
        self.to_post_push()
        self.git("config", "gpg.format", "x509")
        result, _ = self.archive(expect=1)
        self.assertEqual("signature-format-unsupported\n", result.stderr)
        self.assertFalse(sorted(self.store_root().glob("*/*")))
        self.git("config", "gpg.format", "openpgp")
        self.archive()

    def test_archive_layout_and_entry_metadata_are_fixed(self):
        self.to_post_push()
        _, result = self.archive()
        archive = self.published()
        with zipfile.ZipFile(archive) as container:
            infos = container.infolist()
            names = [info.filename for info in infos]
            for info in infos:
                self.assertEqual(zipfile.ZIP_STORED, info.compress_type, info.filename)
                self.assertEqual(3, info.create_system, info.filename)
                self.assertEqual(0o100644, info.external_attr >> 16, info.filename)
                self.assertEqual((1980, 1, 1, 0, 0, 0), info.date_time, info.filename)
                self.assertEqual(b"", info.extra, info.filename)
                self.assertEqual(b"", info.comment, info.filename)
                self.assertFalse(info.filename.endswith("/"), info.filename)
                self.assertEqual(info.file_size, info.compress_size, info.filename)
            self.assertEqual(b"", container.comment)
        self.assertEqual(
            sorted(names, key=lambda name: name.encode("utf-8")), names
        )
        self.assertNotIn(b"PK\x06\x06", archive.read_bytes()[-65536:])
        for expected in (
            "README.txt",
            "checkpoint.json",
            "controller-capsule/MANIFEST.json",
            "controller-capsule/controller/state.json",
            "git/repository.bundle",
            "identity/checkpoint-identity.json",
            "proof/pubkey.asc",
            "proof/signatures.json",
        ):
            self.assertIn(expected, names)
        manifest = self.manifest_of(archive)
        self.assertEqual("fiat-checkpoint-archive/v1", manifest["schema"])
        self.assertEqual("zip", manifest["archive"]["format"])
        self.assertEqual("stored", manifest["archive"]["compression"])
        listed = [entry["path"] for entry in manifest["archive"]["entries"]]
        self.assertEqual(sorted(set(names) - {"checkpoint.json"}, key=lambda n: n.encode()), listed)
        self.assertEqual(archive.stat().st_size, result["bytes"])
        self.assertEqual(
            hashlib.sha256(archive.read_bytes()).hexdigest(), result["outer_sha256"]
        )

    def test_archive_manifest_carries_no_path_hostname_or_environment_value(self):
        self.to_post_push()
        self.archive()
        manifest = self.manifest_of(self.published())
        forbidden = {
            self.dir,
            self.target,
            os.path.realpath(self.dir),
            socket.gethostname(),
            self.key_home,
        }
        forbidden |= {
            value
            for name, value in os.environ.items()
            if name in ("HOME", "USER", "LOGNAME", "TMPDIR", "PWD") and value
        }
        strings = []

        def walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    strings.append(key)
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
            elif isinstance(value, str):
                strings.append(value)

        walk(manifest)
        for text in strings:
            self.assertFalse(text.startswith("/"), text)
            for secret in forbidden:
                if secret:
                    self.assertNotIn(secret, text)
        self.assertEqual(
            os.path.basename(self.target), manifest["run"]["worktree_name"]
        )
        self.assertEqual("wildcat-finance/example", manifest["run"]["repository"])

    def test_archive_export_appends_no_ledger_entry_and_reports_timing_stages(self):
        self.to_post_push()
        before = self.controller_bytes()
        raw, result = self.archive()
        self.assertEqual(before, self.controller_bytes())
        # The reference has every one of these commands print one canonical
        # JSON object, which is the form the next steps read back.
        self.assertEqual(
            json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
            raw.stdout,
        )
        self.assertEqual("", raw.stderr)
        self.assertEqual(
            {"export", "identity", "bundle", "proof", "pack", "inspect", "publish"},
            set(result["timing_ms"]),
        )
        for stage, value in result["timing_ms"].items():
            self.assertIsInstance(value, int, stage)
            self.assertGreaterEqual(value, 0, stage)
        self.assertEqual("fiat-checkpoint-archive-export/v1", result["schema"])
        self.assertEqual(
            {
                "schema", "archive", "sidecar", "outer_sha256", "manifest_sha256",
                "snapshot_id", "bundle_sha256", "entries", "bytes", "boundary",
                "next", "timing_ms",
            },
            set(result),
        )
        self.assertEqual("post-push", result["boundary"])
        self.assertEqual("implement", result["next"]["do"])
        self.assertRegex(result["snapshot_id"], r"^[0-9a-f]{64}$")
        manifest = self.manifest_of(self.published())
        self.assertEqual(
            {"status": "bound", "snapshot_id": result["snapshot_id"]},
            manifest["identity"],
        )

    def test_archive_export_self_check_refuses_manifest_mismatch(self):
        self.to_post_push()
        module = hexctl_module()
        honest = module._checkpoint_archive_manifest

        def drifted(**kwargs):
            entries = [dict(entry) for entry in kwargs.pop("entries")]
            entries[0]["sha256"] = "0" * 64
            return honest(entries=entries, **kwargs)

        code, _, error = self.in_process((("_checkpoint_archive_manifest", drifted),))
        self.assertEqual(1, code)
        self.assertEqual("manifest-mismatch\n", error)
        self.assertFalse(sorted(self.store_root().glob("*/*")))

    def test_archive_bundle_is_built_single_threaded_from_exactly_the_checkpoint_refs(self):
        self.to_post_push()
        self.git("tag", "fixture-tag")
        module = hexctl_module()
        honest = module.bounded_run
        seen = []

        def recorded(base_dir, program, argv, **kwargs):
            if program == "git" and "bundle" in argv:
                seen.append(list(argv))
            return honest(base_dir, program, argv, **kwargs)

        code, output, error = self.in_process((("bounded_run", recorded),))
        self.assertEqual(0, code, error)
        creation = next(argv for argv in seen if argv[:4] == ["-c", "pack.threads=1", "bundle", "create"])
        state = self.state()
        # The bounded ref set is the base, the run branch and every step branch
        # that has an implement receipt. Step 2 has none, so it is not a head:
        # "exactly `_checkpoint_refs`" is what this pins, not "every branch".
        expected = sorted(
            f"refs/heads/{name}"
            for name in (state["run_branch"], self.step_branch(1, state))
        )
        self.assertEqual(expected, creation[5 : 5 + len(expected)])
        self.assertEqual([state["base"]], creation[5 + len(expected) :])

        archive = self.published()
        with zipfile.ZipFile(archive) as container:
            header = container.read("git/repository.bundle").split(b"\n\n", 1)[0]
        heads = {}
        for line in header.decode("utf-8").splitlines()[1:]:
            value, _, name = line.partition(" ")
            heads[name] = value
        self.assertEqual(set(expected), set(heads))
        self.assertFalse([name for name in heads if name.startswith("refs/tags/")])
        manifest = self.manifest_of(archive)
        self.assertEqual(
            {name.removeprefix("refs/heads/"): value for name, value in heads.items()},
            {
                name: value
                for name, value in manifest["refs"].items()
                if not re.fullmatch(r"[0-9a-f]{40}", name)
            },
        )
        self.assertIn(state["base"], manifest["refs"])
        self.assertEqual("sha1", manifest["bundle"]["hash_algorithm"])
        self.assertTrue(manifest["bundle"]["complete_history"])
        self.assertEqual(
            json.loads(output)["bundle_sha256"], manifest["bundle"]["sha256"]
        )

    def test_archive_signature_proof_requires_good_status_and_exactly_one_trailer_each(self):
        head = self.to_post_push()
        self.archive()
        with zipfile.ZipFile(self.published()) as container:
            proof = json.loads(container.read("proof/signatures.json"))
            key = container.read("proof/pubkey.asc")
        self.assertEqual("fiat-checkpoint-signature-proof/v1", proof["schema"])
        self.assertEqual([head], [record["sha"] for record in proof["commits"]])
        record = proof["commits"][0]
        self.assertEqual("G", record["status"])
        self.assertEqual("openpgp", record["format"])
        self.assertEqual(self.fingerprint, record["fingerprint"])
        self.assertEqual(
            {"coauthored_by_shoggoth": 1, "wildcat_origin": 1}, record["trailers"]
        )
        self.assertTrue(record["github_verified"])
        self.assertIn(b"BEGIN PGP PUBLIC KEY BLOCK", key)
        self.assertNotIn(b"PRIVATE", key)
        manifest = self.manifest_of(self.published())
        self.assertEqual([self.fingerprint], manifest["signer"]["fingerprints"])
        self.assertEqual("proof/pubkey.asc", manifest["signer"]["key_path"])
        self.assertEqual(1, manifest["proof"]["commits"])

        # A second run of the same fixture, this time with the trailer counted
        # twice. `done push` reads the message through the fake delivery tool
        # and accepts it; the proof reads the commit itself and does not.
        self.tearDown()
        self.setUp()
        self.to_post_push(
            message=f"step 1\n\n{COAUTHOR}\n{ORIGIN_TRAILER}\n{ORIGIN_TRAILER}\n"
        )
        result, _ = self.archive(expect=1)
        self.assertEqual("signature-unverified\n", result.stderr)
        self.assertFalse(sorted(self.store_root().glob("*/*")))

    def test_signature_unverified_refuses_before_publish_on_a_status_other_than_good(self):
        """A good signature by a key the keyring does not trust is not a proof.

        Ownertrust is the only thing between Git's `G` and its `U`, and the
        disposable keyring writes it for exactly the fingerprints the export
        pinned, so the happy path can never reach this guard: every commit the
        fixture signs is `G` because the export made it so. Seeding the same
        keyring without that trust is what an operator meets when the key
        material travels and the trust does not. Measured on this fixture's
        key: `git verify-commit` still exits 0 and `%G?` answers `U`, so the
        status comparison is the only check that can refuse, and it must, with
        nothing published.
        """
        self.to_post_push()
        module = hexctl_module()

        def untrusted(base_dir, home, key_path, fingerprints):
            environment = module._checkpoint_archive_keyring_environment(home)
            if module.bounded_run(
                base_dir,
                "gpg",
                ["--batch", "--quiet", "--no-autostart", "--import", key_path],
                environment=environment,
            )[0] != 0:
                module._checkpoint_archive_refuse("signature-unverified")

        code, _, error = self.in_process(
            (("_checkpoint_archive_seed_keyring", untrusted),)
        )
        self.assertEqual(1, code)
        self.assertEqual("signature-unverified\n", error)
        self.assertFalse(sorted(self.store_root().glob("*/*")))

    def test_signature_unverified_refuses_before_publish_on_an_unpinned_fingerprint(self):
        """The key that verified must be the key the manifest pins.

        The export reads each commit twice: once against the operator's own
        keyring, which is where the pinned fingerprint set and the exported
        public key come from, and once inside the disposable keyring, which is
        what the proof records. Nothing makes those two answers the same
        object, so the second is compared against the pinned set. The seam is
        patched here for the same reason the ref-disagreement and
        manifest-mismatch cases above are: two keys that both verify one commit
        cannot be built from outside the process. Status stays `G` and both
        trailers stay correct, so the fingerprint comparison is the only check
        that can refuse.
        """
        self.to_post_push()
        module = hexctl_module()
        honest = module._checkpoint_archive_commit_read
        self.assertNotEqual(self.fingerprint, UNPINNED_FINGERPRINT)

        def read_as_another_key(base_dir, commit_sha, environment, verifier=None):
            status, fingerprint, body = honest(base_dir, commit_sha, environment, verifier)
            if environment is None:
                # The first pass, which is what pins the fingerprint set.
                return status, fingerprint, body
            return status, UNPINNED_FINGERPRINT, body

        code, _, error = self.in_process(
            (("_checkpoint_archive_commit_read", read_as_another_key),)
        )
        self.assertEqual(1, code)
        self.assertEqual("signature-unverified\n", error)
        self.assertFalse(sorted(self.store_root().glob("*/*")))


class CheckpointArchiveSecretScanTests(unittest.TestCase):
    """The carried window against the headers the patterns can match.

    `_checkpoint_archive_scan` reads a member in `CHECKPOINT_IO_CHUNK` pieces
    and carries `CHECKPOINT_ARCHIVE_SECRET_WINDOW` bytes of each into the next
    search, so a header lying across a chunk boundary is still one string when
    the patterns run. The window is derived from the headers rather than
    declared, and this is where that derivation is held: a header longer than
    the carry is a secret that leaves in an archive, silently, only when it
    happens to land on a boundary.
    """

    def scan(self, payload: bytes):
        """One scan of `payload` as a file, returning the refusal or None."""
        module = hexctl_module()
        error = StringIO()
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "member")
            with open(path, "wb") as handle:
                handle.write(payload)
            with redirect_stderr(error):
                try:
                    module._checkpoint_archive_scan(path)
                except SystemExit as stopped:
                    self.assertEqual(1, stopped.code)
                    return error.getvalue()
        return None

    def test_secret_shaped_member_refuses_across_a_chunk_boundary(self):
        module = hexctl_module()
        chunk = module.CHECKPOINT_IO_CHUNK
        patterns = module.CHECKPOINT_ARCHIVE_SECRET_PATTERNS
        # Read through `getattr` so a tree whose window is still a bare literal
        # fails here as a stated assertion rather than as an AttributeError.
        # An error and a failure are different report rows, and only the second
        # says the guard did its job.
        headers = getattr(module, "CHECKPOINT_ARCHIVE_SECRET_HEADERS", None)
        self.assertIsNotNone(
            headers, "the scan declares no headers, so its window is not derived"
        )
        lookahead = getattr(module, "CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD", None)
        self.assertIsNotNone(
            lookahead, "the scan declares no lookahead, so its window is not derived"
        )
        footer_reach = getattr(
            module, "CHECKPOINT_ARCHIVE_SECRET_FOOTER_LOOKAHEAD", None
        )
        self.assertIsNotNone(
            footer_reach,
            "the scan declares no footer reach, so its window is not derived",
        )
        blocks = getattr(module, "CHECKPOINT_ARCHIVE_SECRET_BLOCK_PATTERNS", ())
        self.assertEqual(len(patterns), len(headers))
        # Both terms are load-bearing. The header term brings a header that
        # straddles the boundary into one search; the reach term keeps it in
        # the carry while the material the block rule reads lies in the next
        # chunk. A header further back than the sum has its whole decision
        # region inside the chunk it starts in, so nothing beyond the sum is
        # needed and nothing below it is enough.
        #
        # The reach term is the footer's and not the body's. The block rule
        # consults both and the footer is the further, so carrying only the
        # body's lookahead would drop a header whose footer lies in the next
        # chunk. Holding the two to one figure was S2-R7-01, and asserting the
        # sum against the smaller of them would let that return unseen.
        self.assertGreater(
            footer_reach,
            lookahead,
            "the footer reach has to exceed the body lookahead: a footer sits "
            "past the whole body, which is the larger distance",
        )
        self.assertEqual(
            max(len(header) for header in headers) + footer_reach,
            module.CHECKPOINT_ARCHIVE_SECRET_WINDOW,
        )

        # Each header is the longest run its own pattern can need, and no other
        # pattern's: a header that two patterns match would hide the loss of
        # one of them here.
        for index, header in enumerate(headers):
            with self.subTest(header=header):
                matched = [i for i, p in enumerate(patterns) if p.search(header)]
                self.assertEqual([index], matched, header)

        # `#` is outside the base64 alphabet and the lines are short, so the
        # filler supplies no body line of its own. Filling with base64 would
        # hand every planted header the material the block rule looks for, and
        # the test would pass against a scan that never read a block at all.
        body = ARMOURED_BODY_LINE.encode("utf-8")
        filler = (b"#" * 63 + b"\n") * (chunk // 64)
        self.assertEqual(chunk, len(filler))
        for pattern, header in zip(patterns, headers):
            specimen = header if pattern not in blocks else header + b"\n" + body + b"\n"
            for split in (1, len(specimen) // 2, len(specimen) - 1):
                # `split` bytes of the specimen sit in the first chunk and the
                # rest in the second, so the whole spread is walked, ending at
                # the worst case the window has to cover.
                start = chunk - split
                payload = bytearray(filler + filler)
                payload[start : start + len(specimen)] = specimen
                with self.subTest(header=header, bytes_before_the_boundary=split):
                    self.assertEqual(
                        "secret-shaped-member\n", self.scan(bytes(payload))
                    )

        # The placement the window's lookahead term exists for: the header sits
        # as far back as it can while its material still lands past the
        # boundary, which puts its first byte exactly one inside the carry.
        pad = b"#" * (lookahead - 2) + b"\n"
        for pattern, header in zip(patterns, headers):
            if pattern not in blocks:
                continue
            specimen = header + pad + body + b"\n"
            start = chunk - lookahead + 1 - len(header)
            payload = bytearray(filler + filler)
            payload[start : start + len(specimen)] = specimen
            with self.subTest(header=header, placement="material past the boundary"):
                self.assertEqual("secret-shaped-member\n", self.scan(bytes(payload)))

    def test_secret_shaped_member_refuses_before_publish_on_a_crlf_key_in_json(self):
        """S2-R4-02: a CRLF key held as a JSON string value used to publish.

        The escaped-newline delimiter closed the line-feed half of S2-R3-01
        and not the other half. `json.dumps` writes a CRLF line ending as the
        four characters `\\`, `r`, `\\`, `n`; the body witness ended a line
        with a carriage-return byte, so it stopped one escape short of the
        line feed behind it and found no body line at all. Past the lookahead
        there is no footer either, and the member left in the archive.

        The first 2026-09-10 study amendment puts the carriage return in
        the delimiter set in both forms. The key is real and the geometry is
        asserted rather than assumed, so a key size or a lookahead that moves
        fails here instead of leaving a guard that tests nothing.
        """
        module = hexctl_module()
        lookahead = module.CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD
        pem, modulus, public, private = rsa_private_key_pem()
        probe = 0xC0FFEE
        self.assertEqual(3072, modulus.bit_length())
        self.assertEqual(probe, pow(pow(probe, public, modulus), private, modulus))

        header = b"-----BEGIN RSA PRIVATE KEY-----"
        footer = b"-----END RSA PRIVATE KEY-----"
        crlf = pem.replace("\n", "\r\n")
        carried = (
            ("state.json value", json.dumps({"deploy_key": crlf})),
            ("ledger.jsonl line", json.dumps({"seq": 1, "deploy_key": crlf}) + "\n"),
        )
        for name, member in carried:
            payload = member.encode("utf-8")
            with self.subTest(member=name):
                opened = payload.index(header) + len(header)
                self.assertIn(b"\\r\\n", payload)
                self.assertGreater(payload.index(footer) - opened, lookahead)
                self.assertNotIn(b"\n", payload[opened : payload.index(footer)])
                # Since S2-R7-01 the footer reach covers this key, so the
                # refusal alone no longer shows the carriage return was read.
                # Assert the body witness fired, which is the half this guard
                # is for.
                self.assertTrue(
                    module.CHECKPOINT_ARCHIVE_SECRET_BODY.search(payload),
                    "the body witness found no line, so a refusal here would "
                    "be the footer's and this guard would test nothing",
                )
                self.assertEqual("secret-shaped-member\n", self.scan(payload))

        # The three forms that refused before the amendment, so what landed is
        # a widening and not a swap.
        for name, text in (
            ("raw line feed", pem),
            ("raw CRLF", crlf),
            ("escaped line feed", json.dumps({"deploy_key": pem})),
        ):
            with self.subTest(member=name):
                self.assertEqual(
                    "secret-shaped-member\n", self.scan(text.encode("utf-8"))
                )

    def test_secret_shaped_member_refuses_before_publish_on_a_numeric_escaped_key_in_json(
        self,
    ):
        """S2-R6-01: a key whose line feeds are written `\\u000a` used to publish.

        JSON spells a line feed inside a string value three ways: the
        two-character escape, and the six-character numeric escape with its
        hex digits in either case. `json.loads` returns the identical key from
        each, and the body witness read only the first, so past the lookahead
        a key written with the numeric escape had neither a body line nor a
        footer in view and left in the archive. The second 2026-09-10 study
        amendment puts the numeric escapes in the delimiter set, `\\u000a` for
        the line feed and `\\u000d` before it for the carriage return, in
        either letter case.

        The key is real and the geometry is asserted: every member here parses
        back to the key it encodes, carries no newline byte and no
        two-character escape inside its body, and has its footer past the
        lookahead, so the refusal can only come from the numeric escape being
        read as a delimiter.
        """
        module = hexctl_module()
        lookahead = module.CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD
        pem, modulus, public, private = rsa_private_key_pem()
        probe = 0xC0FFEE
        self.assertEqual(3072, modulus.bit_length())
        self.assertEqual(probe, pow(pow(probe, public, modulus), private, modulus))

        header = b"-----BEGIN RSA PRIVATE KEY-----"
        footer = b"-----END RSA PRIVATE KEY-----"
        for name, escape, ending in (
            ("line feed, lower case", "\\u000a", "\n"),
            ("line feed, upper case", "\\u000A", "\n"),
            ("CRLF, lower case", "\\u000d\\u000a", "\r\n"),
            ("CRLF, upper case", "\\u000D\\u000A", "\r\n"),
        ):
            member = '{"deploy_key": "' + pem.replace("\n", escape) + '"}'
            payload = member.encode("utf-8")
            with self.subTest(member=name):
                self.assertEqual(
                    pem.replace("\n", ending), json.loads(member)["deploy_key"]
                )
                opened = payload.index(header) + len(header)
                body = payload[opened : payload.index(footer)]
                self.assertGreater(len(body), lookahead)
                self.assertNotIn(b"\n", body)
                self.assertNotIn(b"\\n", body)
                # The refusal has to come from the numeric escape being read
                # as a delimiter, and since S2-R7-01 the footer reach covers
                # this key too, so the scan alone no longer says which witness
                # fired. Assert the body witness directly.
                self.assertTrue(
                    module.CHECKPOINT_ARCHIVE_SECRET_BODY.search(payload),
                    "the body witness found no line, so a refusal here would "
                    "be the footer's and this guard would test nothing",
                )
                self.assertEqual("secret-shaped-member\n", self.scan(payload))

        # The guard below takes a body with no line delimiter at all. Before
        # S2-R7-01 that member published and the guard was an expected
        # failure; the footer reach now covers it and it refuses. The geometry
        # that made it an escape, a body past the block lookahead with nothing
        # in it for the witness to read, is still proved here on the same
        # seeded key, because that is what makes the refusal the footer's.
        stripped = ('{"deploy_key": "' + pem.replace("\n", "") + '"}').encode("utf-8")
        opened = stripped.index(header) + len(header)
        body = stripped[opened : stripped.index(footer)]
        self.assertGreater(len(body), lookahead)
        self.assertIsNone(re.search(rb"[^A-Za-z0-9+/=]", body))

    def test_secret_shaped_member_refuses_before_publish_on_a_body_the_witness_cannot_read(
        self,
    ):
        """S2-R7-01: a body with no delimiter the witness can see still refuses.

        Two members carry no line delimiter in any form the body witness
        reads: a key whose line breaks were stripped rather than encoded, and
        one whose lines end in a carriage return alone, raw or in either
        escape, because the carriage return is only ever a prefix to a line
        feed. Both used to publish once the footer was past the lookahead, and
        the second 2026-09-10 study amendment stated them as residue.

        They are residue no longer, and not because the witness was widened
        again. The block rule always had a second witness, the footer, and it
        was simply out of range: one constant served both reaches at 1,792
        bytes while these footers sit 2,356 to 2,812 past the header at 3,072
        bits. With the footer reach separated and sized to the largest key the
        scan undertakes to catch, every one of them refuses on the footer.

        So this asserts the refusal and the reason for it: the body witness
        finds nothing, which is what made these members escape, and the member
        refuses anyway.
        """
        module = hexctl_module()
        # Read through `getattr`, as the chunk-boundary guard does: on a tree
        # that still has one reach the attribute is absent, and an
        # AttributeError is an error row where only a failure row says the
        # guard did its job. Elenchus reads a mixed report as inconclusive.
        footer_reach = getattr(
            module, "CHECKPOINT_ARCHIVE_SECRET_FOOTER_LOOKAHEAD", None
        )
        self.assertIsNotNone(
            footer_reach, "the scan declares no footer reach apart from the lookahead"
        )
        largest_key = getattr(module, "CHECKPOINT_ARCHIVE_SECRET_LARGEST_KEY", None)
        self.assertIsNotNone(
            largest_key, "the scan declares no largest key for the footer reach"
        )
        header = b"-----BEGIN RSA PRIVATE KEY-----"
        footer = b"-----END RSA PRIVATE KEY-----"
        pem, modulus, public, private = rsa_private_key_pem()
        probe = 0xC0FFEE
        self.assertEqual(3072, modulus.bit_length())
        self.assertEqual(probe, pow(pow(probe, public, modulus), private, modulus))

        for name, ending in (
            ("stripped", ""),
            ("carriage return, raw", "\r"),
            ("carriage return, two-character escape", "\\r"),
            ("carriage return, numeric escape", "\\u000d"),
        ):
            member = '{"deploy_key": "' + pem.replace("\n", ending) + '"}'
            payload = member.encode("utf-8")
            with self.subTest(member=name):
                opened = payload.index(header) + len(header)
                body = payload[opened : payload.index(footer)]
                # Past the block lookahead, so the body witness is the only
                # one the old single-reach constant left in play.
                self.assertGreater(
                    len(body), module.CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD
                )
                self.assertIsNone(
                    module.CHECKPOINT_ARCHIVE_SECRET_BODY.search(payload),
                    "the body witness read a line here, so this member is not "
                    "the delimiter-free case this guard is for",
                )
                # And within the footer reach, which is what now refuses it.
                self.assertLess(len(body), footer_reach)
                self.assertEqual("secret-shaped-member\n", self.scan(payload))

        # The geometry twin the residue guard below stands on, held against
        # the real key here, where a failed precondition is a failure and not
        # something the expected-failure decorator swallows: the same line
        # count, and at most four bytes longer.
        twin = rsa_shaped_pem(3072)
        self.assertEqual(pem.count("\n"), twin.count("\n"))
        self.assertIn(len(twin) - len(pem), range(0, 5))

        # The declared largest key is in reach in every spelling a JSON string
        # value can give its line breaks, including none, so the constant
        # covers what its name says. Twelve bytes of numeric escape per line
        # is the longest spelling and the last member here.
        largest = rsa_shaped_pem(largest_key)
        for name, ending in LINE_BREAK_SPELLINGS:
            payload = ('{"deploy_key": "' + largest.replace("\n", ending) + '"}').encode(
                "utf-8"
            )
            with self.subTest(member=f"declared largest key, {name}"):
                opened = payload.index(header) + len(header)
                self.assertLess(payload.index(footer) - opened, footer_reach)
                self.assertEqual("secret-shaped-member\n", self.scan(payload))

        # And the residue's geometry, proved here for the guard below: at
        # twice the declared size a stripped body puts the footer past the
        # reach by far more than the twin's four-byte tolerance, with nothing
        # in it for the body witness to read.
        beyond = rsa_shaped_pem(2 * largest_key)
        stripped = ('{"deploy_key": "' + beyond.replace("\n", "") + '"}').encode("utf-8")
        opened = stripped.index(header) + len(header)
        body = stripped[opened : stripped.index(footer)]
        self.assertGreater(len(body), footer_reach + 2048)
        self.assertIsNone(module.CHECKPOINT_ARCHIVE_SECRET_BODY.search(stripped))

    @unittest.expectedFailure
    def test_secret_shaped_member_refuses_before_publish_on_a_key_past_the_declared_largest(
        self,
    ):
        """The residue the third 2026-09-10 study amendment states, as the
        refusal the scan does not make.

        A key whose modulus exceeds `CHECKPOINT_ARCHIVE_SECRET_LARGEST_KEY`,
        with its line breaks stripped, carries no delimiter the body witness
        can see and has its footer past the footer reach, so nothing is in
        view and the member publishes. This test asserts the refusal and is
        marked as the expected failure it is: `unittest` reports it apart from
        the tests that ran, the Exit's floor excludes an expected failure by
        name, and the day the residue closes it becomes an unexpected success,
        which `run_tests.py` counts as a failed run, so closing the residue is
        a dated amendment that edits this test rather than a quiet edit.

        The key is the geometry twin from `rsa_shaped_pem` at twice the
        declared size, because a real key of 16,384 bits takes minutes to
        search for here. The decorator swallows a failed precondition, so the
        twin's fidelity to the seeded real key and this member's geometry are
        proved by the S2-R7-01 guard above and not re-asserted here.
        """
        module = hexctl_module()
        largest_key = getattr(module, "CHECKPOINT_ARCHIVE_SECRET_LARGEST_KEY", None)
        self.assertIsNotNone(largest_key, "the scan declares no largest key")
        beyond = rsa_shaped_pem(2 * largest_key)
        stripped = '{"deploy_key": "' + beyond.replace("\n", "") + '"}'
        self.assertEqual("secret-shaped-member\n", self.scan(stripped.encode("utf-8")))

    def test_secret_scan_passes_a_member_that_carries_no_header(self):
        module = hexctl_module()
        chunk = module.CHECKPOINT_IO_CHUNK
        clean = (
            b"a" * chunk
            + b"-----BEGIN PGP PUBLIC KEY BLOCK-----\n-----BEGIN CERTIFICATE-----\n"
            + b"a" * chunk
        )
        self.assertIsNone(self.scan(clean))
        # A header with prose after it rather than material. Both armour forms
        # are named, because the block rule has to reach each of them.
        for header in (SUBSUMED_PATTERN_SPAN, ADDED_PATTERN_SPAN):
            with self.subTest(header=header):
                named = f"the scan names `{header}` and nothing follows it.\n"
                self.assertIsNone(self.scan(named.encode("utf-8")))
        # The footer witness is the marker matching the header that opened the
        # block, not any `-----END`. A document quoting a header near an
        # unrelated end marker is still prose.
        mismatched = (
            SUBSUMED_PATTERN_SPAN
            + "\nquoted in prose\n-----END PGP PUBLIC KEY BLOCK-----\n"
        )
        self.assertIsNone(self.scan(mismatched.encode("utf-8")))

    def test_secret_scan_passes_the_run_s_own_specification_documents(self):
        """The scan does not read a document's own pattern list as a key.

        `checkpoint archive` snapshots every controller file into the capsule
        and scans each one, so a run whose study quotes an armour header could
        not archive itself. That was S2-R2-02, and steps 4 and 5 export this run
        for real. Each document is read as it stands rather than as a fixture
        copy, so the guard keeps holding as it grows.
        """
        checked = [STUDY, REFERENCE]
        run_study = ROOT / ".hexaemeron" / "study.md"
        if run_study.exists():
            # Untracked run state: present in a Fiat run worktree, absent in a
            # clean checkout, and byte-equal to `STUDY` by this step's binding.
            checked.append(run_study)
        for path in checked:
            with self.subTest(document=path.name):
                text = read(path)
                self.assertTrue(
                    SUBSUMED_PATTERN_SPAN in text or ADDED_PATTERN_SPAN in text,
                    f"{path.name} names no armour header, so it guards nothing",
                )
                self.assertIsNone(self.scan(path.read_bytes()))


def _zip_local_header(name: bytes, data: bytes, *, method=0, flags=0, extra=b""):
    crc = zlib.crc32(data) & 0xFFFFFFFF
    header = struct.pack(
        "<4sHHHHHIIIHH",
        b"PK\x03\x04",
        20,
        flags,
        method,
        0,
        33,
        crc,
        len(data),
        len(data),
        len(name),
        len(extra),
    )
    return header + name + extra + data


def _zip_central_entry(
    name: bytes,
    data: bytes,
    offset: int,
    *,
    method=0,
    flags=0,
    extra=b"",
    comment=b"",
    mode=0o100644,
    declared_size=None,
):
    size = len(data) if declared_size is None else declared_size
    crc = zlib.crc32(data) & 0xFFFFFFFF
    header = struct.pack(
        "<4sHHHHHHIIIHHHHHII",
        b"PK\x01\x02",
        (3 << 8) | 20,
        20,
        flags,
        method,
        0,
        33,
        crc,
        size,
        size,
        len(name),
        len(extra),
        len(comment),
        0,
        0,
        mode << 16,
        offset,
    )
    return header + name + extra + comment


def write_raw_zip(path, entries):
    """Pack `entries` (each a dict with at least `name` bytes and `data` bytes)
    into one ZIP with no compression, no comment, and no ZIP64 record, in
    exactly the order given -- an independent writer from `hexctl.py`'s own,
    so a hostile test never merely re-exercises the code under test to build
    its own fixture.
    """
    body = bytearray()
    offsets = []
    for entry in entries:
        offsets.append(len(body))
        body += _zip_local_header(
            entry["name"],
            entry["data"],
            method=entry.get("method", 0),
            flags=entry.get("flags", 0),
            extra=entry.get("extra", b""),
        )
    cd_start = len(body)
    for entry, offset in zip(entries, offsets):
        body += _zip_central_entry(
            entry["name"],
            entry["data"],
            offset,
            method=entry.get("method", 0),
            flags=entry.get("flags", 0),
            extra=entry.get("extra", b""),
            comment=entry.get("comment", b""),
            mode=entry.get("mode", 0o100644),
            declared_size=entry.get("declared_size"),
        )
    cd_size = len(body) - cd_start
    eocd = struct.pack(
        "<4sHHHHIIH",
        b"PK\x05\x06",
        0,
        0,
        len(entries),
        len(entries),
        cd_size,
        cd_start,
        0,
    )
    body += eocd
    with open(path, "wb") as handle:
        handle.write(bytes(body))


class CheckpointArchiveInspectTests(SignedRunFixture):
    """`checkpoint inspect` over one real archive and its 35 hostile specimens.

    Every hostile test takes the archive `CheckpointArchiveExportTests`
    already builds from one really signed, receipted run, mutates exactly
    the bytes its id names, and asserts the one refusal class the reference's
    Ceilings, Content manifest or Refusal classes table binds to it. `inspect`
    is exercised the way an operator runs it, over a subprocess, never in
    process, and the ZIP writer above is independent of `hexctl.py`'s own so
    a fixture is never built with the code it is testing.
    """

    # -- fixture plumbing -------------------------------------------------

    def run_inspect(self, archive_path, sha256, *, scratch=None, expect=1):
        args = [
            sys.executable,
            HEXCTL,
            "checkpoint",
            "inspect",
            "--archive",
            str(archive_path),
            "--sha256",
            sha256,
        ]
        if scratch is not None:
            args += ["--scratch", str(scratch)]
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode != expect:
            raise AssertionError(
                f"checkpoint inspect -> rc {proc.returncode} (expected {expect})\n"
                f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def assert_refuses(self, archive_path, refusal, *, sha256=None, scratch=None):
        digest = sha256 if sha256 is not None else self.outer_sha256(archive_path)
        proc = self.run_inspect(archive_path, digest, scratch=scratch, expect=1)
        self.assertEqual(f"{refusal}\n", proc.stderr)
        self.assertEqual("", proc.stdout)

    # -- name policy and uniqueness ---------------------------------------

    def test_hostile_traversal_dotdot(self):
        members = self.good_members()
        members["controller-capsule/../evil.txt"] = members.pop("README.txt")
        path = self.write_specimen(members)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_absolute_path(self):
        members = self.good_members()
        members["/evil.txt"] = members.pop("README.txt")
        path = self.write_specimen(members)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_backslash_separator(self):
        members = self.good_members()
        members["controller-capsule\\evil.txt"] = members.pop("README.txt")
        path = self.write_specimen(members)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_drive_letter(self):
        members = self.good_members()
        members["C:/evil.txt"] = members.pop("README.txt")
        path = self.write_specimen(members)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_duplicate_name(self):
        members = self.good_members()
        names = sorted(members, key=lambda item: item.encode("utf-8"))
        entries = []
        for name in names:
            entries.append({"name": name.encode("utf-8"), "data": members[name]})
            if name == "README.txt":
                # Inserted immediately after its own sorted position, so the
                # physical order is already the sorted order the layout check
                # requires; only the name-policy scan is meant to catch this.
                entries.append({"name": name.encode("utf-8"), "data": members[name]})
        path = self.specimen_path()
        write_raw_zip(path, entries)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_case_fold_collision(self):
        members = self.good_members()
        members["readme.TXT"] = members["README.txt"]
        path = self.write_specimen(members)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_non_utf8_name(self):
        members = self.good_members()
        names = sorted(members, key=lambda item: item.encode("utf-8"))
        entries = [{"name": name.encode("utf-8"), "data": members[name]} for name in names]
        entries.append({"name": b"\xff\xfe-evil.txt", "data": b"hostile"})
        entries.sort(key=lambda entry: entry["name"])
        path = self.specimen_path()
        write_raw_zip(path, entries)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_control_character_name(self):
        members = self.good_members()
        members["evil\x01name.txt"] = members.pop("README.txt")
        path = self.write_specimen(members)
        self.assert_refuses(path, "entry-name-policy")

    def test_hostile_nfc_mismatch_name(self):
        members = self.good_members()
        decomposed = "e\u0301vil.txt"  # NFD: "e" + combining acute accent
        self.assertNotEqual(decomposed, unicodedata.normalize("NFC", decomposed))
        members[decomposed] = members.pop("README.txt")
        path = self.write_specimen(members)
        self.assert_refuses(path, "entry-name-policy")

    # -- entry mode, compression, encryption and ZIP64 ---------------------

    def test_hostile_directory_entry(self):
        members = self.good_members()
        path = self.write_specimen(members, overrides={"README.txt": {"mode": 0o040755}})
        self.assert_refuses(path, "entry-mode")

    def test_hostile_symlink_entry(self):
        members = self.good_members()
        path = self.write_specimen(members, overrides={"README.txt": {"mode": 0o120777}})
        self.assert_refuses(path, "entry-mode")

    def test_hostile_special_mode_entry(self):
        members = self.good_members()
        path = self.write_specimen(members, overrides={"README.txt": {"mode": 0o020666}})
        self.assert_refuses(path, "entry-mode")

    def test_hostile_setuid_or_executable_mode(self):
        members = self.good_members()
        path = self.write_specimen(members, overrides={"README.txt": {"mode": 0o104755}})
        self.assert_refuses(path, "entry-mode")

    def test_hostile_compressed_entry(self):
        members = self.good_members()
        path = self.write_specimen(members, overrides={"README.txt": {"method": 8}})
        self.assert_refuses(path, "entry-compressed")

    def test_hostile_encrypted_entry(self):
        members = self.good_members()
        path = self.write_specimen(members, overrides={"README.txt": {"flags": 0x1}})
        self.assert_refuses(path, "entry-encrypted")

    def test_hostile_zip64_record(self):
        members = self.good_members()
        zip64_extra = struct.pack("<HH", 0x0001, 0)
        path = self.write_specimen(members, overrides={"README.txt": {"extra": zip64_extra}})
        self.assert_refuses(path, "zip64-present")

    # -- ceilings, declared straight from the central directory ------------

    def test_hostile_entry_count_over_limit(self):
        members = self.good_members()
        path = self.write_specimen(members)
        data = bytearray(Path(path).read_bytes())
        eocd_offset = len(data) - 22
        self.assertEqual(b"PK\x05\x06", bytes(data[eocd_offset : eocd_offset + 4]))
        struct.pack_into("<H", data, eocd_offset + 8, 4201)
        struct.pack_into("<H", data, eocd_offset + 10, 4201)
        Path(path).write_bytes(bytes(data))
        self.assert_refuses(path, "entry-limit")

    def test_hostile_expanded_size_over_limit(self):
        members = self.good_members()
        path = self.write_specimen(
            members, overrides={"README.txt": {"declared_size": 65 * 1024 * 1024}}
        )
        self.assert_refuses(path, "entry-limit")

    def test_hostile_bundle_over_limit(self):
        members = self.good_members()
        path = self.write_specimen(
            members,
            overrides={"git/repository.bundle": {"declared_size": 1025 * 1024 * 1024}},
        )
        self.assert_refuses(path, "entry-limit")

    # -- structural bytes ---------------------------------------------------

    def test_hostile_trailing_data(self):
        members = self.good_members()
        path = self.write_specimen(members)
        with open(path, "ab") as handle:
            handle.write(b"\x00" * 8)
        self.assert_refuses(path, "trailing-data")

    # -- the digest join between checkpoint.json and the physical members --

    def test_hostile_size_mismatch(self):
        members = self.good_members()
        members["README.txt"] = members["README.txt"] + b"hostile appended bytes\n"
        path = self.write_specimen(members)
        self.assert_refuses(path, "manifest-mismatch")

    def test_hostile_tampered_manifest(self):
        members = self.good_members()
        target = "controller-capsule/MANIFEST.json"
        tampered = bytearray(members[target])
        tampered[-2] ^= 0xFF
        members[target] = bytes(tampered)
        path = self.write_specimen(members)
        self.assert_refuses(path, "manifest-mismatch")

    def test_hostile_unmanifested_member(self):
        members = self.good_members()
        members["controller-capsule/controller/hostile-extra.txt"] = b"extra\n"
        path = self.write_specimen(members)
        self.assert_refuses(path, "manifest-mismatch")

    def test_hostile_missing_member(self):
        members = self.good_members()
        del members["README.txt"]
        path = self.write_specimen(members)
        self.assert_refuses(path, "manifest-mismatch")

    def test_hostile_wrong_receipt(self):
        members = self.good_members()
        target = "controller-capsule/controller/ledger.jsonl"
        tampered = bytearray(members[target])
        tampered[-2] ^= 0xFF
        members[target] = bytes(tampered)
        path = self.write_specimen(members)
        self.assert_refuses(path, "manifest-mismatch")

    # -- the outer digest and sidecar ---------------------------------------

    def test_hostile_wrong_outer_digest(self):
        path = self.good_archive()
        real = self.outer_sha256(path)
        wrong = ("0" if real[0] != "0" else "1") + real[1:]
        self.assert_refuses(path, "outer-digest-mismatch", sha256=wrong)

    def test_hostile_tampered_sidecar(self):
        good = self.good_archive()
        path = self.specimen_path()
        shutil.copyfile(good, path)
        real = self.outer_sha256(path)
        wrong = ("0" if real[0] != "0" else "1") + real[1:]
        with open(path + ".sha256", "w", encoding="utf-8") as handle:
            handle.write(f"{wrong}  {os.path.basename(path)}\n")
        self.assert_refuses(path, "sidecar-mismatch", sha256=real)

    # -- the bundle and the three-way ref join ------------------------------

    def test_hostile_missing_object(self):
        """The good bundle's own header is reused byte for byte, so its heads
        and prerequisite count still equal the manifest's `refs` exactly;
        only the packed object data after the header is truncated, which
        `git fetch` and `git bundle verify` refuse as incomplete without the
        ref join ever seeing a discrepancy (S3-R4-01: the ref join runs on
        the header first, so a specimen meant to isolate the missing object
        alone must not also disturb the heads the header reports).
        """
        members = self.good_members()
        manifest = self.manifest(members)
        good_bundle = members["git/repository.bundle"]
        header_end = good_bundle.index(b"\n\n") + 2
        self.assertGreater(len(good_bundle), header_end + 64, "bundle too small to truncate")
        new_bytes = good_bundle[: header_end + 64]
        self.retarget(members, manifest, "git/repository.bundle", new_bytes)
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "bundle-incomplete")

    def test_hostile_ref_map_mismatch(self):
        members = self.good_members()
        manifest = self.manifest(members)
        refs = dict(manifest["refs"])
        target_name = sorted(refs)[0]
        original = refs[target_name]
        refs[target_name] = ("0" if original[0] != "0" else "1") + original[1:]
        manifest["refs"] = refs
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "ref-disagreement")

    # -- signatures, identity, schema and acceptance ------------------------

    def test_hostile_signature_proof_mismatch(self):
        members = self.good_members()
        manifest = self.manifest(members)
        proof = json.loads(members["proof/signatures.json"])
        original = proof["signer"]["fingerprints"][0]
        bogus = ("0" if original[0] != "0" else "1") + original[1:]
        proof["signer"]["fingerprints"] = [bogus]
        module = hexctl_module()
        proof_bytes = module.canonical(proof).encode("utf-8") + b"\n"
        self.retarget(members, manifest, "proof/signatures.json", proof_bytes)
        # `manifest["proof"]` is checkpoint.json's own second copy of the
        # proof member's digest, separate from its `archive.entries` record;
        # both have to move together or the join refuses before the
        # signature re-verify this fixture is actually aimed at ever runs.
        manifest["proof"]["sha256"] = hashlib.sha256(proof_bytes).hexdigest()
        manifest["signer"]["fingerprints"] = [bogus]
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "signature-unverified")

    def test_hostile_identity_mismatch(self):
        members = self.good_members()
        manifest = self.manifest(members)
        target = "identity/checkpoint-identity.json"
        payload = json.loads(members[target])
        original = payload["snapshot_id"]
        payload["snapshot_id"] = ("0" if original[0] != "0" else "1") + original[1:]
        module = hexctl_module()
        new_bytes = module.canonical(payload).encode("utf-8") + b"\n"
        self.retarget(members, manifest, target, new_bytes)
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "identity-mismatch")

    def test_hostile_unknown_schema_version(self):
        members = self.good_members()
        manifest = self.manifest(members)
        manifest["schema"] = "fiat-checkpoint-archive/v0"
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "schema-unsupported")

    def test_hostile_absolute_source_path_in_manifest(self):
        members = self.good_members()
        manifest = self.manifest(members)
        entries = manifest["archive"]["entries"]
        entries[0]["path"] = "/etc/passwd"
        entries.sort(key=lambda item: item["path"].encode("utf-8"))
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "schema-unsupported")

    def test_hostile_self_referential_acceptance(self):
        members = self.good_members()
        manifest = self.manifest(members)
        payload = b"{}\n"
        members["acceptance/current"] = payload
        manifest["archive"]["entries"].append(
            {
                "path": "acceptance/current",
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
        manifest["archive"]["entries"].sort(key=lambda item: item["path"].encode("utf-8"))
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "acceptance-self-reference")

    def test_hostile_secret_shaped_member(self):
        members = self.good_members()
        manifest = self.manifest(members)
        tampered = members["README.txt"] + b"\nghp_" + b"A" * 36 + b"\n"
        self.retarget(members, manifest, "README.txt", tampered)
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "secret-shaped-member")

    # -- the clean path, and the two write and print boundaries -------------

    def test_inspect_reports_clean_findings_on_a_good_archive(self):
        path = self.good_archive()
        digest = self.outer_sha256(path)
        proc = self.run_inspect(path, digest, expect=0)
        result = json.loads(proc.stdout)
        self.assertEqual("fiat-checkpoint-inspect/v1", result["schema"])
        self.assertEqual([], result["findings"])
        self.assertEqual(digest, result["outer_sha256"])
        with zipfile.ZipFile(path) as container:
            self.assertEqual(len(container.infolist()), result["entries"])
        self.assertEqual(os.path.getsize(path), result["bytes"])
        self.assertEqual("", proc.stderr)

    def test_inspect_digests_exactly_the_bytes_it_then_parses(self):
        """S3-R1-01: the outer digest has to cover what the parse reads.

        `--sha256` travels out of band so the operator can bind an exact run
        of bytes. That binding was worth nothing while the digest was one
        pass over the supplied path and the central directory, the local
        headers and every member were separate reopens of that same path:
        whoever can write where the sender left the archive could let one set
        of bytes be digested and another parsed. The length was forked the
        same way, `os.path.getsize` driving every layout invariant while the
        count the digest actually covered was discarded.

        The capture closes both. It reads the supplied path once, digesting
        and copying in the same pass into the 0700 scratch root, and returns
        the copy plus the digested length. This asserts the three properties
        that makes true, and that the supplied path is not read again.
        """
        module = hexctl_module()
        scratch = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, scratch, True)
        source = os.path.join(scratch, "supplied.zip")
        original = bytes(random.Random(861).getrandbits(8) for _ in range(4096))
        with open(source, "wb") as handle:
            handle.write(original)

        root = os.path.join(scratch, "root")
        os.makedirs(root, 0o700)
        local, size, digest = module._checkpoint_inspect_capture(source, root)

        # The copy is inside the private root, not the path the sender named.
        self.assertTrue(os.path.abspath(local).startswith(os.path.abspath(root)))
        self.assertNotEqual(os.path.abspath(local), os.path.abspath(source))
        # One length, and it is the digested count rather than a separate stat.
        self.assertEqual(len(original), size)
        self.assertEqual(hashlib.sha256(original).hexdigest(), digest)
        with open(local, "rb") as handle:
            self.assertEqual(original, handle.read())

        # Changing the supplied file afterwards cannot reach the parse.
        with open(source, "wb") as handle:
            handle.write(b"Z" * 9000)
        with open(local, "rb") as handle:
            self.assertEqual(original, handle.read())
        self.assertEqual(len(original), size)

        # And nothing downstream reads the supplied path again. The parse
        # logic itself lives in `_checkpoint_inspect_archive_verified` --
        # `_checkpoint_inspect_archive` is a thin wrapper `checkpoint restore
        # --archive` also calls, so it can read the same verified manifest,
        # captured file and parsed central directory this test's own
        # docstring already names -- and inside it the parameter appears only
        # in its own signature and in the capture call. A later reopen would
        # put the fork back without failing anything else here.
        body = inspect.getsource(module._checkpoint_inspect_archive_verified)
        mentions = [
            line.strip()
            for line in body.splitlines()
            if "archive_path" in line and not line.strip().startswith("#")
        ]
        self.assertEqual(
            ["archive_path: str,", "archive_path, expected_sha256, scratch"],
            mentions,
            "the supplied path is read outside the capture, so the digest no "
            "longer covers everything the inspector parses",
        )
        # The wrapper itself forwards `archive_path` on to the verified
        # reader above and nowhere else.
        wrapper_body = inspect.getsource(module._checkpoint_inspect_archive)
        wrapper_mentions = [
            line.strip()
            for line in wrapper_body.splitlines()
            if "archive_path" in line and not line.strip().startswith("#")
        ]
        self.assertEqual(
            [
                "archive_path: str,",
                "archive_path, expected_sha256, scratch, existing_repo=existing_repo",
            ],
            wrapper_mentions,
        )

    def test_inspect_refuses_a_current_acceptance_anywhere_under_its_root(self):
        """S3-R2-02: the self-reference rule is a location, not one string.

        A checkpoint's own acceptance is not inside its own archive; the next
        checkpoint carries it as a prior receipt. The check matched the single
        name `acceptance/current`, while the manifest names its own members and
        nothing else holds them to a fixed layout, so the same receipt one
        directory down or with a suffix passed. Every member under the
        acceptance root has to be a prior one.
        """
        module = hexctl_module()
        root = module.CHECKPOINT_ARCHIVE_ACCEPTANCE_ROOT
        prior = module.CHECKPOINT_ARCHIVE_ACCEPTANCE_DIR
        self.assertEqual(root, prior.split("/")[0])
        manifest = {
            "acceptance": {
                "current": module.CHECKPOINT_ARCHIVE_ACCEPTANCE_CURRENT,
                "prior": [],
            }
        }

        for names in (
            [f"{root}/current"],
            [f"{root}/current/receipt.json"],
            [f"{root}/current.json"],
            [f"{root}/anything-else"],
        ):
            with self.subTest(refused=names):
                with self.assertRaises(SystemExit):
                    module._checkpoint_inspect_acceptance(manifest, names)

        # A prior receipt is the one shape that belongs there.
        for names in (
            ["checkpoint.json"],
            [f"{prior}/001.json"],
            [f"{prior}/001.json", f"{prior}/002.json", "checkpoint.json"],
        ):
            with self.subTest(allowed=names):
                module._checkpoint_inspect_acceptance(manifest, names)

    def test_inspect_states_that_signature_reverification_is_internal(self):
        """S3-R2-01: a clean signature section is a claim about the archive.

        `inspect` re-runs `git verify-commit` rather than trusting the proof's
        own status, but it seeds the keyring from the archive's own key member
        and the fingerprints the archive's own manifest names. A `G` therefore
        establishes internal consistency, not that the key belongs to anyone,
        and `--sha256` is what carries provenance. That boundary was real and
        written down nowhere, which is what this pins: both the operator-facing
        reference and the function itself have to say it.
        """
        module = hexctl_module()
        body = inspect.getsource(module._checkpoint_inspect_signatures)
        self.assertIn("internal consistency", body)
        self.assertIn("--sha256", body)

        reference = pathlib.Path(module.__file__).resolve().parent.parent
        reference = reference / "references" / "checkpoint-archive.md"
        text = reference.read_text(encoding="utf-8")
        self.assertIn("does and does not establish", text)
        self.assertIn("not that the key belongs to anyone in particular", text)

    def test_inspect_writes_nothing_outside_scratch(self):
        path = self.good_archive()
        digest = self.outer_sha256(path)
        before = set(os.listdir(tempfile.gettempdir()))
        self.run_inspect(path, digest, expect=0)
        after = set(os.listdir(tempfile.gettempdir()))
        leaked = {
            name
            for name in after - before
            if name.startswith(".fiat-checkpoint-inspect-") or name.startswith(".fiat-gpg-")
        }
        self.assertEqual(set(), leaked)
        named_scratch = os.path.join(self.dir, "named-scratch")
        self.run_inspect(path, digest, scratch=named_scratch, expect=0)
        self.assertTrue(os.path.isdir(named_scratch))
        self.assertEqual(0o700, stat.S_IMODE(os.stat(named_scratch).st_mode))
        self.assertTrue(os.listdir(named_scratch))

    def test_inspect_prints_no_entry_content(self):
        path = self.good_archive()
        digest = self.outer_sha256(path)
        proc = self.run_inspect(path, digest, expect=0)
        with zipfile.ZipFile(path) as container:
            state_bytes = container.read("controller-capsule/controller/state.json")
        marker = state_bytes[:64].decode("utf-8", "ignore")
        self.assertNotIn(marker, proc.stdout)
        self.assertNotIn("controller-capsule/controller/state.json", proc.stdout)
        self.assertNotIn(str(path), proc.stdout)

    # -- round 3: the bundle block, the keyring root, value types, FIFOs ----

    def inspect_within(self, archive_path, sha256, seconds):
        """Run `inspect` and fail, rather than hang, if it has not returned."""
        args = [
            sys.executable,
            HEXCTL,
            "checkpoint",
            "inspect",
            "--archive",
            str(archive_path),
            "--sha256",
            sha256,
        ]
        try:
            return subprocess.run(args, capture_output=True, text=True, timeout=seconds)
        except subprocess.TimeoutExpired:
            self.fail(f"checkpoint inspect did not return within {seconds}s")

    def members_of(self, archive_path):
        with zipfile.ZipFile(archive_path) as container:
            return {
                info.filename: container.read(info.filename)
                for info in container.infolist()
            }

    def test_inspect_joins_the_bundle_block_to_the_bundle_member(self):
        """S3-R3-01. `checkpoint.json` records the bundle's digest and length
        twice, in `archive.entries` and in `bundle`. Only the first was held to
        the streamed bytes, and `bundle` is the copy `inspect` prints, so a
        block naming another digest passed and was echoed at exit 0.
        """
        good = str(self.good_archive())
        digest = self.outer_sha256(good)
        members = self.members_of(good)
        manifest = self.manifest(members)
        record = next(
            item
            for item in manifest["archive"]["entries"]
            if item["path"] == "git/repository.bundle"
        )
        printed = json.loads(self.run_inspect(good, digest, expect=0).stdout)["bundle"]
        self.assertEqual(record["sha256"], printed["sha256"])
        self.assertEqual(record["bytes"], printed["bytes"])
        real = manifest["bundle"]["sha256"]
        cases = (
            ("sha256", ("0" if real[0] != "0" else "1") + real[1:], "manifest-mismatch"),
            ("bytes", manifest["bundle"]["bytes"] + 1, "manifest-mismatch"),
            ("complete_history", False, "schema-unsupported"),
            ("hash_algorithm", "md5", "schema-unsupported"),
        )
        for index, (field, value, refusal) in enumerate(cases):
            mutated = dict(members)
            tampered = self.manifest(members)
            tampered["bundle"][field] = value
            self.set_manifest(mutated, tampered)
            path = self.write_specimen(
                mutated, path=self.specimen_path(f"bundle-{index}.zip")
            )
            self.assert_refuses(path, refusal)

    def test_inspect_keeps_the_disposable_keyring_under_its_scratch_root(self):
        """S3-R3-02. The reference promises a `GNUPGHOME` created 0700 under
        the scratch root and an `inspect` that writes nothing outside it. The
        home was made under the system temporary directory and removed before
        the command returned, which a TMPDIR snapshot taken afterwards cannot
        see; every temporary directory the command makes is recorded here.
        """
        good = str(self.good_archive())
        scratch = os.path.join(self.dir, "keyring-scratch")
        os.makedirs(scratch, 0o700)
        module = hexctl_module()
        made = []
        real_mkdtemp = tempfile.mkdtemp

        def recording(*args, **kwargs):
            path = real_mkdtemp(*args, **kwargs)
            made.append(path)
            return path

        with mock.patch.object(tempfile, "mkdtemp", recording), redirect_stdout(
            StringIO()
        ):
            result = module._checkpoint_inspect_archive(
                good, self.outer_sha256(good), scratch
            )
        self.assertEqual([], result["findings"])
        homes = [
            path for path in made if os.path.basename(path).startswith(".fiat-gpg-")
        ]
        self.assertEqual(1, len(homes), made)
        self.assertEqual(scratch, os.path.dirname(homes[0]))
        self.assertFalse(os.path.exists(homes[0]))
        outside = [path for path in made if not path.startswith(scratch + os.sep)]
        self.assertEqual([], outside)
        # A home under a long root would put the agent socket past the AF_UNIX
        # limit; the redirection files keep that from deciding the verdict.
        long_scratch = os.path.join(self.dir, "l" * (150 - len(self.dir)))
        self.run_inspect(good, self.outer_sha256(good), scratch=long_scratch, expect=0)
        self.assertGreaterEqual(len(long_scratch), 150)

    def test_inspect_refuses_a_malformed_signer_or_proof_block_with_one_class(self):
        """S3-R3-03. `signer.key_path` was the one manifest value whose type
        nothing checked before it reached a dictionary lookup; a list there
        ended the command in a traceback rather than one class. The signer
        and proof blocks now close their values as well as their keys.
        """
        members = self.good_members()
        module = hexctl_module()
        manifest = self.manifest(members)
        self.assertEqual("proof/pubkey.asc", manifest["signer"]["key_path"])
        signer_cases = (
            ("key_path", [manifest["signer"]["key_path"]]),
            ("key_path", "README.txt"),
            ("fingerprints", [manifest["signer"]["fingerprints"][0], 7]),
        )
        for index, (field, value) in enumerate(signer_cases):
            mutated = dict(members)
            tampered = self.manifest(members)
            tampered["signer"][field] = value
            proof = json.loads(mutated["proof/signatures.json"])
            proof["signer"] = tampered["signer"]
            proof_bytes = module.canonical(proof).encode("utf-8") + b"\n"
            self.retarget(mutated, tampered, "proof/signatures.json", proof_bytes)
            tampered["proof"]["sha256"] = hashlib.sha256(proof_bytes).hexdigest()
            self.set_manifest(mutated, tampered)
            path = self.write_specimen(
                mutated, path=self.specimen_path(f"signer-{index}.zip")
            )
            self.assert_refuses(path, "schema-unsupported")
        proof_cases = (("commits", "1"), ("sha256", "not a digest"))
        for index, (field, value) in enumerate(proof_cases):
            mutated = dict(members)
            tampered = self.manifest(members)
            tampered["proof"][field] = value
            self.set_manifest(mutated, tampered)
            path = self.write_specimen(
                mutated, path=self.specimen_path(f"proof-{index}.zip")
            )
            self.assert_refuses(path, "schema-unsupported")

    def test_inspect_does_not_block_on_a_fifo_at_the_archive_or_its_sidecar(self):
        """S3-R3-04. `open` on a FIFO waits for a writer, so a FIFO where the
        sender's directory holds the archive or its sidecar held the inspector
        for as long as the sender liked. The type is read off the opened
        descriptor, so a symbolic link to a regular sidecar still compares and
        one to a FIFO still refuses without waiting.
        """
        good = str(self.good_archive())
        digest = self.outer_sha256(good)
        beside = self.specimen_path("fifo-beside.zip")
        shutil.copyfile(good, beside)
        os.mkfifo(beside + ".sha256")
        proc = self.inspect_within(beside, digest, 30)
        self.assertEqual(
            (1, "sidecar-mismatch\n", ""), (proc.returncode, proc.stderr, proc.stdout)
        )
        linked = self.specimen_path("linked.zip")
        shutil.copyfile(good, linked)
        real = self.specimen_path("real.sha256")
        with open(real, "w", encoding="utf-8") as handle:
            handle.write(f"{digest}  linked.zip\n")
        os.symlink(real, linked + ".sha256")
        proc = self.inspect_within(linked, digest, 30)
        self.assertEqual((0, ""), (proc.returncode, proc.stderr))
        os.remove(linked + ".sha256")
        os.symlink(beside + ".sha256", linked + ".sha256")
        proc = self.inspect_within(linked, digest, 30)
        self.assertEqual((1, "sidecar-mismatch\n"), (proc.returncode, proc.stderr))
        fifo = self.specimen_path("fifo-archive.zip")
        os.mkfifo(fifo)
        proc = self.inspect_within(fifo, digest, 30)
        self.assertEqual(2, proc.returncode)
        self.assertIn("not a regular file", proc.stderr)
        self.assertNotIn(fifo, proc.stderr)

    # -- round 4: the ref join runs on the header, before completeness ------

    def test_inspect_reports_ref_disagreement_over_a_bundle_that_is_also_incomplete(
        self,
    ):
        """S3-R4-01. The reference states the three-way ref join as decided
        on the bundle's own header, with `git bundle verify` kept as "the
        independent second opinion", and the runbook's Exit lists the ref
        join before that verify. Until this fix, `_checkpoint_inspect_bundle`
        ran the header's prerequisite count, the disposable clone's fetch and
        `git bundle verify` before the caller ever reached the ref join, so a
        specimen that was both an incomplete bundle and ref-mismatched
        refused `bundle-incomplete` and `ref-disagreement` was never reached.
        A specimen bad in both ways must refuse the header-decided class.
        """
        members = self.good_members()
        manifest = self.manifest(members)
        # The good bundle's own header is reused byte for byte and only the
        # packed object data is truncated, the same construction
        # test_hostile_missing_object uses, so the bundle is genuinely
        # incomplete without its heads differing from the manifest on their
        # own; the ref map is then tampered explicitly below, so this
        # specimen's two defects are independent and neither masks the other.
        good_bundle = members["git/repository.bundle"]
        header_end = good_bundle.index(b"\n\n") + 2
        self.assertGreater(len(good_bundle), header_end + 64, "bundle too small to truncate")
        new_bytes = good_bundle[: header_end + 64]
        self.retarget(members, manifest, "git/repository.bundle", new_bytes)
        refs = dict(manifest["refs"])
        target_name = sorted(refs)[0]
        original = refs[target_name]
        refs[target_name] = ("0" if original[0] != "0" else "1") + original[1:]
        manifest["refs"] = refs
        self.set_manifest(members, manifest)
        path = self.write_specimen(members)
        self.assert_refuses(path, "ref-disagreement")


class CheckpointArchiveRestoreTests(SignedRunFixture):
    """`checkpoint restore --archive` over one real, really signed archive.

    Every case here restores into a fresh destination this process controls
    directly (never `self.target`, the fixture's own worktree), over a plain
    subprocess with no `FAKE_GIT_*` environment: the destination's Git history
    is whatever `git init` and the archive's own bundle actually produce, and
    `merge-base`, `rev-parse` and the rest resolve for real against it.
    """

    # -- fixture plumbing --------------------------------------------------

    def restore_destination(self, name="restore-dest"):
        root = tempfile.mkdtemp(prefix="fiat861-restore-")
        return os.path.join(root, name)

    def run_restore(self, archive_path, sha256, destination, *, expect=0, env=None):
        args = [
            sys.executable,
            HEXCTL,
            "--dir",
            str(destination),
            "checkpoint",
            "restore",
            "--archive",
            str(archive_path),
            "--sha256",
            sha256,
        ]
        proc = subprocess.run(args, capture_output=True, text=True, env=env)
        if proc.returncode != expect:
            raise AssertionError(
                f"checkpoint restore --archive -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def assert_restore_refuses(self, archive_path, refusal, destination=None, *, sha256=None):
        digest = sha256 if sha256 is not None else self.outer_sha256(archive_path)
        destination = destination or self.restore_destination()
        proc = self.run_restore(archive_path, digest, destination, expect=1)
        self.assertEqual(f"{refusal}\n", proc.stderr)
        self.assertEqual("", proc.stdout)

    def hexctl_status_json(self, worktree):
        proc = subprocess.run(
            [sys.executable, HEXCTL, "--dir", str(worktree), "status", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        payload = json.loads(proc.stdout)
        payload.pop("observation_run_id", None)
        payload.pop("version_resolution_status", None)
        return payload

    def hostile_identity_internally_consistent(self, members, manifest):
        """Tamper the identity claim so its two copies still agree.

        Unlike `test_hostile_identity_mismatch` above, which leaves the
        member's own recorded `snapshot_id` disagreeing with `checkpoint.json`'s
        copy -- a defect `checkpoint inspect` already catches on its own --
        this changes the identity object itself and re-derives both copies
        from the new, false content. `checkpoint inspect` sees two
        self-consistent copies and passes; only a mint from the real
        restored state, ledger and Git evidence can tell the claim is wrong.
        """
        target = "identity/checkpoint-identity.json"
        payload = json.loads(members[target])
        module = hexctl_module()
        tampered_identity = dict(payload["identity"])
        tampered_identity["restore_test_marker"] = "tampered"
        recomputed = hashlib.sha256(
            module.CHECKPOINT_IDENTITY_DOMAIN
            + module.canonical(tampered_identity).encode("utf-8")
        ).hexdigest()
        payload["identity"] = tampered_identity
        payload["snapshot_id"] = recomputed
        new_bytes = module.canonical(payload).encode("utf-8") + b"\n"
        self.retarget(members, manifest, target, new_bytes)
        manifest["identity"]["snapshot_id"] = recomputed
        self.set_manifest(members, manifest)

    # -- cases --------------------------------------------------------------

    def test_restore_from_archive_recreates_repository_and_controller_state(self):
        archive = self.good_archive()
        producer_state = self.state()
        producer_ledger = (
            Path(self.target) / ".hexaemeron" / "ledger.jsonl"
        ).read_bytes()
        digest = self.outer_sha256(archive)
        manifest = self.manifest(self.good_members(archive))
        destination = self.restore_destination()

        proc = self.run_restore(archive, digest, destination)
        payload = json.loads(proc.stdout)
        self.assertEqual("fiat-checkpoint-archive-restore/v1", payload["schema"])
        self.assertEqual("ok", payload["verify"])
        self.assertEqual(digest, payload["outer_sha256"])
        worktree = payload["restore"]["worktree"]

        verify_proc = subprocess.run(
            [sys.executable, HEXCTL, "--dir", worktree, "verify"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, verify_proc.returncode, verify_proc.stderr)

        restored_state = self.hexctl_status_json(worktree)
        for owned in (("config", "git", "worktree"), ("config", "git", "origin")):
            producer_node, restored_node = producer_state, restored_state
            for key in owned[:-1]:
                producer_node, restored_node = producer_node[key], restored_node[key]
            self.assertNotEqual(producer_node[owned[-1]], restored_node[owned[-1]])
            producer_node.pop(owned[-1])
            restored_node.pop(owned[-1])
        self.assertEqual(producer_state, restored_state)

        for name, expected_sha in manifest["refs"].items():
            rev = subprocess.run(
                ["git", "-C", destination, "rev-parse", "--verify", f"{name}^{{commit}}"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, rev.returncode, rev.stderr)
            self.assertEqual(expected_sha, rev.stdout.strip())

        restored_ledger = (Path(worktree) / ".hexaemeron" / "ledger.jsonl").read_bytes()
        self.assertTrue(restored_ledger.startswith(producer_ledger))
        appended = restored_ledger[len(producer_ledger):].decode("utf-8").splitlines()
        self.assertEqual(1, len(appended))
        self.assertEqual("checkpoint:restore", json.loads(appended[0])["event"])

    def test_restore_from_archive_offline_after_source_clone_removed(self):
        archive = self.good_archive()
        digest = self.outer_sha256(archive)

        portable_root = tempfile.mkdtemp(prefix="fiat861-portable-")
        portable_archive = os.path.join(portable_root, "checkpoint.zip")
        shutil.copyfile(archive, portable_archive)
        shutil.copyfile(f"{archive}.sha256", f"{portable_archive}.sha256")

        # The fixture's own worktree is the "source clone" the archive was
        # built from. Destroying it before restoring proves the restore below
        # reads only the portable archive copy above.
        shutil.rmtree(self.target, ignore_errors=True)

        scratch_home = tempfile.mkdtemp(prefix="fiat861-home-")
        env = os.environ.copy()
        env["HOME"] = scratch_home
        env["GIT_CONFIG_GLOBAL"] = os.path.join(scratch_home, "gitconfig")
        env.pop("GIT_CONFIG_SYSTEM", None)
        destination = self.restore_destination()

        proc = self.run_restore(portable_archive, digest, destination, env=env)
        payload = json.loads(proc.stdout)
        self.assertEqual("fiat-checkpoint-archive-restore/v1", payload["schema"])
        self.assertEqual("ok", payload["verify"])

        remote = subprocess.run(
            ["git", "-C", destination, "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, remote.returncode, remote.stderr)
        self.assertEqual("https://github.com/wildcat-finance/example.git\n", remote.stdout)

    def test_restore_from_archive_reverifies_signatures_receipts_identity_and_ancestry(
        self,
    ):
        archive = self.good_archive()

        # A proof status flipped from `G`: the same construction
        # `test_hostile_signature_proof_mismatch` uses, over this archive.
        members = self.good_members(archive)
        manifest = self.manifest(members)
        proof = json.loads(members["proof/signatures.json"])
        original = proof["signer"]["fingerprints"][0]
        bogus = ("0" if original[0] != "0" else "1") + original[1:]
        proof["signer"]["fingerprints"] = [bogus]
        module = hexctl_module()
        proof_bytes = module.canonical(proof).encode("utf-8") + b"\n"
        self.retarget(members, manifest, "proof/signatures.json", proof_bytes)
        manifest["proof"]["sha256"] = hashlib.sha256(proof_bytes).hexdigest()
        manifest["signer"]["fingerprints"] = [bogus]
        self.set_manifest(members, manifest)
        specimen = self.write_specimen(members, path=self.specimen_path("bad-signature.zip"))
        self.assert_restore_refuses(specimen, "signature-unverified")

        # A ledger byte changed inside the capsule: the outer manifest's own
        # digest join for that member is kept consistent by `retarget`, but
        # the capsule's own inner `MANIFEST.json` still names the original
        # ledger bytes and size, so the existing capsule reader -- reused
        # unchanged -- refuses once it re-verifies the capsule's file
        # inventory after extraction.
        members = self.good_members(archive)
        manifest = self.manifest(members)
        target = "controller-capsule/controller/ledger.jsonl"
        tampered_ledger = members[target] + b'{"tampered": true}\n'
        self.retarget(members, manifest, target, tampered_ledger)
        self.set_manifest(members, manifest)
        specimen = self.write_specimen(members, path=self.specimen_path("bad-ledger.zip"))
        digest = self.outer_sha256(specimen)
        destination = self.restore_destination()
        proc = self.run_restore(specimen, digest, destination, expect=2)
        self.assertIn("hexctl: error:", proc.stderr)
        self.assertIn("checkpoint manifest inventory does not match controller bytes", proc.stderr)

        # A snapshot_id changed: internally consistent, so only a fresh mint
        # from the restored state, ledger and Git evidence exposes it.
        members = self.good_members(archive)
        manifest = self.manifest(members)
        self.hostile_identity_internally_consistent(members, manifest)
        specimen = self.write_specimen(members, path=self.specimen_path("bad-identity.zip"))
        self.assert_restore_refuses(specimen, "identity-mismatch")

        # A working commit outside the anchor's descendants: point
        # `run.initial_base_sha` at a real commit this repository holds --
        # the run branch's own tip -- which is a descendant of the base, not
        # an ancestor of it, so the ancestry check refuses.
        members = self.good_members(archive)
        manifest = self.manifest(members)
        run_branch_sha = manifest["refs"][self.run_branch()]
        manifest["run"] = {**manifest["run"], "initial_base_sha": run_branch_sha}
        self.set_manifest(members, manifest)
        specimen = self.write_specimen(members, path=self.specimen_path("bad-ancestry.zip"))
        self.assert_restore_refuses(specimen, "ref-disagreement")

    def test_restore_from_archive_refuses_non_empty_destination(self):
        archive = self.good_archive()
        digest = self.outer_sha256(archive)

        occupied = self.restore_destination("occupied")
        os.makedirs(occupied)
        with open(os.path.join(occupied, "keep.txt"), "w", encoding="utf-8") as handle:
            handle.write("not empty\n")
        self.assert_restore_refuses(archive, "destination-occupied", occupied, sha256=digest)

        elsewhere = self.restore_destination("elsewhere")
        os.makedirs(elsewhere)
        symlinked = os.path.join(os.path.dirname(elsewhere), "symlinked")
        os.symlink(elsewhere, symlinked)
        self.assert_restore_refuses(archive, "destination-occupied", symlinked, sha256=digest)

    def test_restore_from_archive_executes_no_directive(self):
        archive = self.good_archive()
        digest = self.outer_sha256(archive)
        destination = self.restore_destination()

        proc = self.run_restore(archive, digest, destination)
        payload = json.loads(proc.stdout)
        worktree = payload["restore"]["worktree"]

        ledger_path = Path(worktree) / ".hexaemeron" / "ledger.jsonl"
        before = ledger_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual("checkpoint:restore", json.loads(before[-1])["event"])
        state_before = self.hexctl_status_json(worktree)

        next_proc = subprocess.run(
            [sys.executable, HEXCTL, "--dir", worktree, "next"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, next_proc.returncode, next_proc.stderr)
        directive = json.loads(next_proc.stdout)
        self.assertEqual(payload["next"]["do"], directive["do"])

        after = ledger_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(before, after)
        self.assertEqual(state_before, self.hexctl_status_json(worktree))

    def test_restore_from_archive_after_main_advances_stays_anchored(self):
        archive = self.good_archive()
        digest = self.outer_sha256(archive)

        # Advance the real "main" branch elsewhere, simulating upstream
        # having moved on since the archive was built. Restore reads only
        # the bundle already frozen inside the archive and never this
        # checkout, so this must not matter.
        advanced = os.path.join(self.dir, "advanced.txt")
        with open(advanced, "w", encoding="utf-8") as handle:
            handle.write("main moved on after the archive was built\n")
        subprocess.run(
            ["git", "add", "advanced.txt"], cwd=self.dir, check=True, capture_output=True
        )
        subprocess.run(
            [
                "git",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-q",
                "-m",
                "main advances after the archive was built",
            ],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )

        destination = self.restore_destination()
        proc = self.run_restore(archive, digest, destination)
        payload = json.loads(proc.stdout)
        self.assertEqual("fiat-checkpoint-archive-restore/v1", payload["schema"])
        self.assertEqual("ok", payload["verify"])

    # -- step 4, round 2 guards ---------------------------------------------
    #
    # Named `test_archive_restore_*` rather than `test_restore_from_archive_*`
    # on purpose: Step 4's Exit pins `-k restore_from_archive` at exactly six
    # tests, and these four are audit guards rather than that clause's cases.
    # The module canonicalises TMPDIR at import (see the note beside
    # `tempfile.tempdir` above), which is why the first guard below builds its
    # own symlink instead of relying on the platform's.

    def test_archive_restore_accepts_a_symlinked_destination_parent(self):
        """S4-R1-05: a symlinked *parent* is not an occupied destination.

        The destination here is absent, is no symlink and holds nothing; only
        the directory it is reached through is a link. On macOS this is every
        `/tmp` path, which is the ordinary staging location for a command whose
        whole purpose is restoring onto another machine.
        """
        archive = self.good_archive()
        digest = self.outer_sha256(archive)

        real_parent = tempfile.mkdtemp(prefix="fiat861-restore-real-")
        link_root = tempfile.mkdtemp(prefix="fiat861-restore-link-")
        linked_parent = os.path.join(link_root, "via-symlink")
        os.symlink(real_parent, linked_parent)
        self.assertNotEqual(
            os.path.realpath(linked_parent),
            linked_parent,
            "the guard needs a parent that is genuinely reached through a link",
        )

        destination = os.path.join(linked_parent, "restore-dest")
        proc = self.run_restore(archive, digest, destination)
        payload = json.loads(proc.stdout)
        self.assertEqual("fiat-checkpoint-archive-restore/v1", payload["schema"])
        self.assertEqual("ok", payload["verify"])

        # The run lands on the resolved path, which is the directory the
        # operator named, reached by its real name.
        self.assertTrue(os.path.isdir(os.path.join(real_parent, "restore-dest", ".git")))

    def test_archive_restore_removes_the_capsule_stage_once_it_completes(self):
        """S4-R1-03: the disposable root does not outlive a completed restore.

        The capsule is relocated into active controller state and re-verified
        from there, so leaving the staged copy under `.git/` duplicates the
        whole capsule -- state, ledger, receipts and every carried acceptance
        receipt -- for the life of the clone.
        """
        archive = self.good_archive()
        digest = self.outer_sha256(archive)
        destination = self.restore_destination()

        proc = self.run_restore(archive, digest, destination)
        payload = json.loads(proc.stdout)
        self.assertEqual("ok", payload["verify"])

        module = hexctl_module()
        stage = os.path.join(destination, ".git", module.CHECKPOINT_ARCHIVE_RESTORE_STAGE_DIR)
        self.assertFalse(
            os.path.exists(stage),
            f"the capsule stage survived a completed restore at {stage}",
        )

    def test_archive_restore_removes_a_destination_it_created_when_it_refuses(self):
        """S4-R1-04: a refused restore leaves no path hexctl created.

        The destination is admitted, and an absent one created, before the
        inspector runs. A refusal after that point must not reclassify the
        path for the next attempt from absent to empty and admit it again.
        """
        archive = self.good_archive()
        destination = self.restore_destination("never-made")
        self.assertFalse(os.path.exists(destination))

        wrong_digest = "0" * 64
        proc = self.run_restore(archive, wrong_digest, destination, expect=1)
        self.assertEqual("outer-digest-mismatch\n", proc.stderr)
        self.assertFalse(
            os.path.exists(destination),
            "a refused restore left behind the directory it created",
        )

    def test_archive_restore_diagnoses_its_own_scratch_failure_as_itself(self):
        """S4-R1-07: the process's scratch root is not the operator's destination.

        Reporting a failure to create this process's own temporary directory as
        `destination-occupied` tells the operator a false fact about a path that
        is absent, empty and entirely usable.

        The failure is driven in process rather than over the command line:
        `tempfile` falls through TMPDIR to `/tmp` and the rest of its candidate
        list, so an unusable TMPDIR in the child's environment never reaches
        this code path at all.
        """
        archive = self.good_archive()
        digest = self.outer_sha256(archive)
        destination = self.restore_destination("scratchless")
        module = hexctl_module()

        captured = StringIO()
        with mock.patch.object(
            module.tempfile, "mkdtemp", side_effect=OSError("no scratch here")
        ):
            with redirect_stderr(captured):
                with self.assertRaises(SystemExit) as stopped:
                    module._checkpoint_restore_from_archive(
                        destination, str(archive), digest
                    )

        self.assertEqual(2, stopped.exception.code)
        diagnosis = captured.getvalue()
        self.assertIn("hexctl: error:", diagnosis)
        self.assertIn("scratch directory could not be created", diagnosis)
        self.assertNotIn("destination-occupied", diagnosis)

        # S4-R1-04 again, on the same path: the destination this call created
        # before it refused is not left behind.
        self.assertFalse(os.path.exists(destination))

    # -- step 4, round 3 guards ---------------------------------------------
    #
    # Both apply a rule round 2 established at a site round 2's repair did not
    # reach, so they keep that round's naming and stay outside the Exit's
    # `-k restore_from_archive` clause for the same reason.

    def test_archive_restore_removes_a_destination_it_created_when_admission_refuses(self):
        """S4-R3-03: the admission's own refusals leave nothing it created.

        `_checkpoint_restore_archive_destination` creates an absent
        destination and can then refuse inside itself, below that `os.mkdir`.
        Those refusals return nothing to `_checkpoint_restore_from_archive`,
        so its `finally` never runs and the S4-R1-04 removal never reaches
        them: the path stayed behind, reclassified for the next attempt from
        absent to empty and admitted again.
        """
        destination = self.restore_destination("admission-refused")
        self.assertFalse(os.path.exists(destination))
        module = hexctl_module()

        captured = StringIO()
        with mock.patch.object(
            module.os, "fstat", side_effect=OSError("destination changed under us")
        ):
            with redirect_stderr(captured):
                with self.assertRaises(SystemExit) as stopped:
                    module._checkpoint_restore_archive_destination(destination)

        self.assertEqual(1, stopped.exception.code)
        self.assertEqual("destination-occupied\n", captured.getvalue())
        self.assertFalse(
            os.path.exists(destination),
            "the admission refused and left behind the directory it created",
        )

    def test_archive_restore_diagnoses_its_own_identity_scratch_failure_as_itself(self):
        """S4-R3-02: the identity scratch is the process's own, like the outer one.

        S4-R1-07 separated the outer scratch root's failure from
        `destination-occupied`. The identity scratch under it was left
        unguarded, and `main` carries no catch-all, so an `OSError` there
        reached the operator as a traceback carrying local absolute paths out
        of a command whose refusals are one bounded line.

        Driven in process for S4-R1-07's reason: `tempfile` falls through an
        unusable TMPDIR to `/tmp`, so this failure has no command-line surface.

        The escaping `OSError` is caught here and turned into a failure rather
        than left to propagate. The defect this guard names *is* an uncaught
        exception, so on the unfixed parent an `assertRaises(SystemExit)` alone
        never sees it: the `OSError` is not that type, it escapes the test, and
        unittest records an error. Elenchus reads any error as an
        infrastructure failure and returns `inconclusive` for the whole run, so
        a guard shaped that way cannot report what it proved. Catching it
        states the same property as an assertion and leaves the verdict
        readable.
        """
        archive = self.good_archive()
        digest = self.outer_sha256(archive)
        destination = self.restore_destination("identity-scratchless")
        module = hexctl_module()
        real_mkdtemp = module.tempfile.mkdtemp

        def refuse_only_the_identity_scratch(*args, **kwargs):
            prefix = kwargs.get("prefix", "")
            if prefix.startswith(".fiat-checkpoint-restore-identity-"):
                raise OSError("no identity scratch here")
            return real_mkdtemp(*args, **kwargs)

        captured = StringIO()
        code = None
        with mock.patch.object(
            module.tempfile, "mkdtemp", side_effect=refuse_only_the_identity_scratch
        ):
            with redirect_stderr(captured):
                try:
                    module._checkpoint_restore_from_archive(
                        destination, str(archive), digest
                    )
                except SystemExit as stopped:
                    code = stopped.code
                except OSError as escaped:
                    self.fail(
                        "the identity scratch failure escaped as an uncaught "
                        f"OSError ({escaped!r}) instead of one bounded refusal; "
                        "hexctl installs no excepthook and `main` has no "
                        "catch-all, so this reaches the operator as a traceback"
                    )
                else:
                    self.fail(
                        "the restore completed where the identity scratch "
                        "failure should have refused"
                    )

        self.assertEqual(2, code)
        diagnosis = captured.getvalue()
        self.assertIn("hexctl: error:", diagnosis)
        self.assertIn("scratch directory could not be created", diagnosis)
        self.assertNotIn("identity-mismatch", diagnosis)
        self.assertNotIn("Traceback", diagnosis)

    def test_archive_restore_keeps_its_marker_when_identity_refuses(self):
        """S4-R4-02: a refusal decided from relocated state keeps its marker.

        `identity-mismatch` is recomputed from the relocated state, so it can
        only fire once `_checkpoint_restore_relocate` has completed -- and
        that transaction used to complete by retiring its own marker. The
        refusal therefore left the destination holding active controller
        state with no marker beside it, which is a residue the reference
        describes nowhere: study section 11 and the risk register's
        `interrupted-restore` row between them cover a destination without
        active state, and a destination carrying the marker the existing
        retry rules resume or refuse, and neither is this.

        Both halves are asserted here, because the repair is a deferral and
        a deferral that never fires would leak a marker into every successful
        restore instead. So: the refusal keeps the marker, and the success
        retires it.
        """
        module = hexctl_module()
        marker_name = os.path.join(
            module.STATE_DIR_NAME, module.CHECKPOINT_RESTORE_MARKER_FILE
        )

        archive = self.good_archive()
        members = self.good_members(archive)
        manifest = self.manifest(members)
        self.hostile_identity_internally_consistent(members, manifest)
        specimen = self.write_specimen(
            members, path=self.specimen_path("r4-identity-marker.zip")
        )
        refused = self.restore_destination("r4-identity-refused")
        self.assert_restore_refuses(specimen, "identity-mismatch", destination=refused)
        self.assertTrue(
            os.path.isfile(os.path.join(refused, marker_name)),
            "identity-mismatch left active controller state with no relocation "
            "marker, so the existing retry rules have nothing to resume or "
            "refuse and the residue matches no rule the reference writes",
        )

        completed = self.restore_destination("r4-identity-completed")
        self.run_restore(archive, self.outer_sha256(archive), completed, expect=0)
        self.assertFalse(
            os.path.exists(os.path.join(completed, marker_name)),
            "a completed restore left its relocation marker behind, so the "
            "deferred retirement never ran",
        )

    def test_relocation_transaction_retires_in_place_for_its_native_caller(self):
        """S4-R4-02: `--from` keeps the retirement point it always had.

        `_checkpoint_restore_relocate` is shared with `checkpoint restore
        --from`, which is audited and receipted in an earlier step. The
        deferral above is opt-in precisely so that path is untouched: the
        parameter defaults to `None`, and the native caller passes nothing,
        so the `None` branch runs the same retirement at the same point.

        This pins that arrangement rather than the behaviour it produces, and
        the bound is worth stating: it establishes that the native caller has
        not been switched onto the deferred path, not that a successful
        `--from` restore retires its marker. Nothing in either suite asserts
        that today -- every native marker assertion in
        `test_hexctl_checkpoint.py` pins the marker *surviving* a refusal or
        an interrupted run -- so this guard closes the regression that the
        shared transaction newly makes possible and leaves that older gap
        visible instead of implying a green suite covered it.
        """
        module = hexctl_module()
        parameters = inspect.signature(
            module._checkpoint_restore_relocate
        ).parameters
        # Asserted rather than subscripted: on a tree without the repair this
        # name is absent, and a `KeyError` here would leave the test as an
        # error rather than a failure. Elenchus reads any error as an
        # infrastructure failure and returns `inconclusive` for the whole
        # run, which is how round 3's first check was lost.
        self.assertIn(
            "deferred_marker",
            parameters,
            "the relocation transaction takes no deferral parameter, so a "
            "refusal decided from relocated state cannot keep its marker",
        )
        self.assertIsNone(
            parameters["deferred_marker"].default,
            "the relocation transaction now defers by default; "
            "`checkpoint restore --from` would stop retiring its own marker",
        )

        native = inspect.getsource(module.cmd_checkpoint_restore)
        archive_branch, _, capsule_branch = native.partition(
            "if source is None or manifest_sha256 is None:"
        )
        self.assertIn("_checkpoint_restore_relocate", capsule_branch)
        self.assertNotIn(
            "deferred_marker",
            capsule_branch,
            "the native `--from` caller now passes a deferral, which moves "
            "marker retirement on a path audited and receipted in an earlier "
            "step",
        )
        self.assertNotIn("_checkpoint_restore_relocate", archive_branch)

    def test_archive_restore_keeps_its_marker_when_identity_cannot_be_minted(self):
        """S4-R4-01: `identity-unavailable` is the fourth post-`git init` class.

        Rounds 1 to 3 enumerated three refusal classes that can fire after the
        destination repository exists: `ref-disagreement`, the capsule stage's
        `manifest-mismatch`, and `identity-mismatch`. That enumeration was
        incomplete. `_checkpoint_archive_identity` mints under
        `_checkpoint_archive_guarded("identity-unavailable", mint)`, so any
        failure inside the mint refuses with `identity-unavailable` rather
        than `identity-mismatch`, from the same call site and therefore from
        the same position: after the relocation transaction has completed.

        The class is established here by observation rather than by reading,
        because an enumeration that names three of four classes makes any
        section 11 amendment wrong on the day it lands. The mint is failed at
        `_checkpoint_identity_verify_observations`, which is reached only from
        inside `mint`, and the archive is built before the patch so that
        export's own identity member is minted normally.

        It also pins that the S4-R4-02 deferral covers both identity classes,
        not just the one that named it.
        """
        archive = self.good_archive()
        digest = self.outer_sha256(archive)
        destination = self.restore_destination("r4-identity-unavailable")
        module = hexctl_module()
        marker_name = os.path.join(
            module.STATE_DIR_NAME, module.CHECKPOINT_RESTORE_MARKER_FILE
        )

        captured = StringIO()
        code = None
        with mock.patch.object(
            module,
            "_checkpoint_identity_verify_observations",
            side_effect=OSError("the restored tree cannot answer an observation"),
        ):
            with redirect_stdout(StringIO()):
                with redirect_stderr(captured):
                    try:
                        module._checkpoint_restore_from_archive(
                            destination, str(archive), digest
                        )
                    except SystemExit as stopped:
                        code = stopped.code
                    except OSError as escaped:
                        self.fail(
                            "the mint failure escaped as an uncaught OSError "
                            f"({escaped!r}) instead of one bounded refusal"
                        )
                    else:
                        self.fail(
                            "the restore completed where the mint failure "
                            "should have refused"
                        )

        self.assertEqual(1, code)
        self.assertEqual(
            "identity-unavailable\n",
            captured.getvalue(),
            "the fourth post-`git init` refusal class is not the one the "
            "reference's closed table names for a mint that cannot complete",
        )
        self.assertTrue(
            os.path.isfile(os.path.join(destination, marker_name)),
            "`identity-unavailable` left active controller state with no "
            "relocation marker, so the S4-R4-02 deferral covers only one of "
            "the two classes decided from relocated state",
        )


if __name__ == "__main__":
    unittest.main()
