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

No test or class name here contains `hostile` or `restore_from_archive`: the
design record's conformance resolvers select later steps' tests with
`-k hostile` and `-k restore_from_archive`, and a match here would change
their counts.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import zipfile
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


class CheckpointArchiveExportTests(HexctlCase):
    """`checkpoint archive` over one real, really signed run.

    The controller fixture fakes the delivery tools a run talks to, which is
    right for receipts and wrong for an archive: a bundle built from invented
    SHAs carries no objects, and a signature proof read from a canned trailer
    block proves nothing. So this fixture keeps the fake `gh` and the fake ref
    reader, points the fake ref map at the commits it really made, and signs
    those commits with an OpenPGP key generated into a temporary `GNUPGHOME`
    for the class. Nothing here reads or writes the operator's keyring.
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
        self.to_post_push()
        planted = Path(self.target) / ".hexaemeron" / "notes.txt"
        planted.write_text("carry over: AKIA" + "A1B2C3D4E5F6G7H8"[:16] + "\n", encoding="utf-8")
        result, _ = self.archive(expect=1)
        self.assertEqual("secret-shaped-member\n", result.stderr)
        self.assertFalse(sorted(self.store_root().glob("*/*")))
        # The OpenSSH header, which the PEM pattern matches on its own, and the
        # OpenPGP block, which the 2026-09-09 study amendment added because no
        # pattern reached it: its header ends `PRIVATE KEY BLOCK-----`.
        for header in (SUBSUMED_PATTERN_SPAN, ADDED_PATTERN_SPAN):
            with self.subTest(header=header):
                planted.write_text(header + "\n", encoding="utf-8")
                result, _ = self.archive(expect=1)
                self.assertEqual("secret-shaped-member\n", result.stderr)
        planted.unlink()
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
        self.assertEqual(len(patterns), len(headers))
        self.assertEqual(
            max(len(header) for header in headers),
            module.CHECKPOINT_ARCHIVE_SECRET_WINDOW,
        )

        # Each header is the longest run its own pattern can need, and no other
        # pattern's: a header that two patterns match would hide the loss of
        # one of them here.
        for index, header in enumerate(headers):
            with self.subTest(header=header):
                matched = [i for i, p in enumerate(patterns) if p.search(header)]
                self.assertEqual([index], matched, header)

        filler = b"a" * chunk
        for header in headers:
            for split in (1, len(header) // 2, len(header) - 1):
                # `split` bytes of the header sit in the first chunk and the
                # rest in the second, so the whole spread is walked, ending at
                # the worst case the window has to cover.
                start = chunk - split
                payload = bytearray(filler + filler)
                payload[start : start + len(header)] = header
                with self.subTest(header=header, bytes_before_the_boundary=split):
                    self.assertEqual(
                        "secret-shaped-member\n", self.scan(bytes(payload))
                    )

    def test_secret_scan_passes_a_member_that_carries_no_header(self):
        module = hexctl_module()
        chunk = module.CHECKPOINT_IO_CHUNK
        clean = (
            b"a" * chunk
            + b"-----BEGIN PGP PUBLIC KEY BLOCK-----\n-----BEGIN CERTIFICATE-----\n"
            + b"a" * chunk
        )
        self.assertIsNone(self.scan(clean))


if __name__ == "__main__":
    unittest.main()
