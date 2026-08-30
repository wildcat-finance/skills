"""Focused acceptance tests for the beginner primer package."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_child_or_golden_retriever_primer.py"
REPORT = ROOT / "tmp" / "elenchus" / "child-or-golden-retriever-unit.json"
PRIMER = ROOT / "docs" / "a-child-or-a-golden-retriever.md"
SOURCE_NOTE = ROOT / "docs" / "a-child-or-a-golden-retriever-source-note.md"
STUDY = ROOT / "docs" / "a-child-or-a-golden-retriever-study.md"
COVER = ROOT / "docs" / "assets" / "a-child-or-a-golden-retriever-cover.png"
HEX_PLUGIN_MANIFEST = (
    ROOT / "plugins" / "hexaemeron" / ".codex-plugin" / "plugin.json"
)
FIAT_SKILL = ROOT / "plugins" / "hexaemeron" / "skills" / "fiat" / "SKILL.md"
PUSH_DISCIPLINE = (
    ROOT
    / "plugins"
    / "hexaemeron"
    / "skills"
    / "fiat"
    / "references"
    / "push-discipline.md"
)
CHECKPOINT_REFERENCE = (
    ROOT
    / "plugins"
    / "hexaemeron"
    / "skills"
    / "fiat"
    / "references"
    / "controller-checkpoint.md"
)
CONTRIBUTOR_GUIDE = ROOT / "docs" / "how-to-help-shoggoth.md"
CONTRIBUTOR_BUILDER = ROOT / "scripts" / "build_contributor_guide.py"
CONTRIBUTOR_PDF = ROOT / "docs" / "pdf" / "how-to-help-shoggoth.pdf"

KIT_DIGEST = "e09eb107921ab52e467bae54e3e605f2e01fa258df7c12529be44fc486d71218"
COVER_DIGEST = "5763ab9da93a3bd3420d2e905eef9525dbeb2e642f3121d8ad76c38d9f9cc32a"
HEX_VERSION = "1.6.14"
STUDY_HEX_VERSION = "1.6.9"
FIAT_VERSION = "5.40.1"
STUDY_FIAT_VERSION = "5.34.1"
PROMPT_DIGESTS = (
    "5e2c721d2ac5fb76106aa9047f0e3b887d6b66c0c14f44f287a6584b2022b157",
    "c721f3b2d600ea83fe36be3427396335c407c65c762cce2424cfab079d93f8e9",
)
EXPECTED_DEFINITIONS = (
    ("Shoggoth", "Shoggoth is the Wildcat agent-and-skill collective."),
    (
        "The Interceptor",
        "The Interceptor is that same collective working through its external "
        "problem-solving harness under the target repository's authority.",
    ),
    ("Hexaemeron", "Hexaemeron is the delivery plugin and ordered system."),
    ("Fiat", "Fiat is Hex's explicit controller and receipt ledger."),
)
EXPECTED_LIFECYCLE = (
    "study",
    "runbook",
    "implement",
    "audit",
    "prose",
    "push",
    "integrate",
)
SOURCE_PNGS = {
    "docs/assets/a-child-or-a-golden-retriever-cover.png": (
        (1448, 1086),
        COVER_DIGEST,
    ),
    "docs/assets/a-child-or-a-golden-retriever-mascot-roles.png": (
        (1774, 887),
        "f25e3e7c62b22895a89f270b5383288cb4996ac2976987c82170da4ca97e7485",
    ),
    "docs/assets/a-child-or-a-golden-retriever-mascot-fiat.png": (
        (1774, 887),
        "6bcbab3534c69e06134e2b404ac765e2a1a859eaff4019a791ce862b2e3b13f5",
    ),
}
TEXT_FREE_SOURCE_PNGS = {
    "docs/assets/a-child-or-a-golden-retriever-mascot-roles.png",
    "docs/assets/a-child-or-a-golden-retriever-mascot-fiat.png",
}
INFOGRAPHICS = {
    "docs/assets/a-child-or-a-golden-retriever-whos-who.png": (1672, 941),
    "docs/assets/a-child-or-a-golden-retriever-fiat-flow.png": (1672, 941),
}
PDFS = {
    "docs/pdf/a-child-or-a-golden-retriever.pdf": (
        2,
        6,
        "A child or a golden retriever",
    ),
    "docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf": (
        1,
        1,
        "A child or a golden retriever - quick-start",
    ),
}
PDF_LINKS = {
    "docs/pdf/a-child-or-a-golden-retriever.pdf": (
        "https://github.com/wildcat-finance/skills/blob/"
        "docs/a-child-or-a-golden-retriever/docs/"
        "a-child-or-a-golden-retriever.md#the-five-minute-demo",
        "https://github.com/wildcat-finance/skills/blob/main/INSTALL.md",
        "https://github.com/laurenceday/shoggoth-interceptor",
    ),
    "docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf": (
        "https://github.com/wildcat-finance/skills/blob/"
        "docs/a-child-or-a-golden-retriever/docs/"
        "a-child-or-a-golden-retriever.md#the-five-minute-demo",
        "https://github.com/wildcat-finance/skills/blob/main/INSTALL.md",
    ),
}
NEW_BINARIES = {*SOURCE_PNGS, *INFOGRAPHICS, *PDFS}
EXPECTED_BINARY_DIGESTS = {
    "docs/assets/a-child-or-a-golden-retriever-cover.png": COVER_DIGEST,
    "docs/assets/a-child-or-a-golden-retriever-mascot-roles.png": (
        "f25e3e7c62b22895a89f270b5383288cb4996ac2976987c82170da4ca97e7485"
    ),
    "docs/assets/a-child-or-a-golden-retriever-mascot-fiat.png": (
        "6bcbab3534c69e06134e2b404ac765e2a1a859eaff4019a791ce862b2e3b13f5"
    ),
    "docs/assets/a-child-or-a-golden-retriever-whos-who.png": (
        "0aa924e981e5a07a5f5a288184fbacda31082f12ba6b9f2b1f9cb10aa8f7716e"
    ),
    "docs/assets/a-child-or-a-golden-retriever-fiat-flow.png": (
        "5fa9dd3da85d34721a2d35debdb4e299d2ae281a4dafc42ea903cb8f649bf2d3"
    ),
    "docs/pdf/a-child-or-a-golden-retriever.pdf": (
        "914f597f12bb9b95ba4420204df4b1e945bb05eefe109489d452e08321527755"
    ),
    "docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf": (
        "094472325b38d5bac46d16c7d510a261ba17447044c2d9ba46b1aa19c1164463"
    ),
}
REQUIRED_FILES = {
    "README.md",
    "docs/a-child-or-a-golden-retriever.md",
    "docs/a-child-or-a-golden-retriever-source-note.md",
    "docs/a-child-or-a-golden-retriever-study.md",
    "docs/a-child-or-a-golden-retriever-runbook.md",
    "docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md",
    "scripts/build_child_or_golden_retriever_primer.py",
    "tests/test_child_or_golden_retriever_primer.py",
    *NEW_BINARIES,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def marked_block(text: str, name: str) -> str:
    start = f"<!-- primer-{name}:start -->"
    end = f"<!-- primer-{name}:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise AssertionError(f"expected exactly one {name} marker pair")
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def png_details(path: Path) -> tuple[tuple[int, int], tuple[bytes, ...]]:
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"not a PNG: {path.relative_to(ROOT)}")
    cursor = 8
    chunks: list[bytes] = []
    dimensions: tuple[int, int] | None = None
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise AssertionError(f"truncated PNG: {path.relative_to(ROOT)}")
        length = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        chunk_type = payload[cursor + 4 : cursor + 8]
        data_start = cursor + 8
        data_end = data_start + length
        chunk_end = data_end + 4
        if chunk_end > len(payload):
            raise AssertionError(f"oversized PNG chunk: {path.relative_to(ROOT)}")
        chunks.append(chunk_type)
        if chunk_type == b"IHDR":
            dimensions = struct.unpack(">II", payload[data_start : data_start + 8])
        cursor = chunk_end
        if chunk_type == b"IEND":
            break
    if dimensions is None or not chunks or chunks[-1] != b"IEND":
        raise AssertionError(f"incomplete PNG structure: {path.relative_to(ROOT)}")
    return dimensions, tuple(chunks)


def run_text(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def find_builder_python() -> Optional[Path]:
    """Return a local Python that carries the optional PDF build dependencies."""
    candidates = []
    configured = os.environ.get("WILDCAT_PRIMER_PYTHON")
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        (
            Path(sys.executable),
            Path.home()
            / ".cache"
            / "codex-runtimes"
            / "codex-primary-runtime"
            / "dependencies"
            / "python"
            / "bin"
            / "python3",
        )
    )
    seen = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved in seen or not resolved.is_file() or resolved.is_symlink():
            continue
        seen.add(resolved)
        probe = subprocess.run(
            [str(resolved), "-c", "import PIL, pypdf, reportlab"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return resolved
    return None


class ChildOrGoldenRetrieverPrimerTests(unittest.TestCase):
    """Keep all beginner-facing views bound to one checked source package."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime_python = find_builder_python()
        cls.builder_stdout = ""
        cls.report = None
        if cls.runtime_python is None:
            return
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.unlink(missing_ok=True)
        result = subprocess.run(
            [
                str(cls.runtime_python),
                str(BUILDER),
                "--check",
                "--report",
                str(REPORT.relative_to(ROOT)),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(
                "deterministic primer check failed\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        cls.builder_stdout = result.stdout
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_required_inventory_is_present_and_regular(self) -> None:
        for relative in sorted(REQUIRED_FILES):
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertFalse(path.is_symlink(), relative)

    def test_canonical_definitions_and_lifecycle_are_exact(self) -> None:
        text = PRIMER.read_text(encoding="utf-8")
        expected_lines = [
            f"- {name}: {definition}"
            for name, definition in EXPECTED_DEFINITIONS
        ]
        self.assertEqual(
            marked_block(text, "definitions").splitlines(),
            expected_lines,
        )
        self.assertEqual(
            marked_block(text, "lifecycle"),
            f"`{' -> '.join(EXPECTED_LIFECYCLE)}`",
        )

    def test_cover_is_the_near_top_hero_and_demo_anchor_is_stable(self) -> None:
        text = PRIMER.read_text(encoding="utf-8")
        cover_reference = "./assets/a-child-or-a-golden-retriever-cover.png"
        self.assertEqual(text.count(cover_reference), 1)
        cover_line = next(
            index
            for index, line in enumerate(text.splitlines(), start=1)
            if cover_reference in line
        )
        answer_line = next(
            index
            for index, line in enumerate(text.splitlines(), start=1)
            if line == "## The answer in thirty seconds"
        )
        self.assertLessEqual(cover_line, 12)
        self.assertLess(cover_line, answer_line)
        self.assertEqual(text.count("## The five-minute demo"), 1)
        builder = BUILDER.read_text(encoding="utf-8")
        self.assertIn("#the-five-minute-demo", builder)
        self.assertIn("a-child-or-a-golden-retriever-cover.png", builder)
        self.assertIn(COVER_DIGEST, builder)
        self.assertRegex(builder, r"\(\s*1448\s*,\s*1086\s*\)")

    def test_readme_exposes_markdown_and_both_pdfs(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for link in (
            "./docs/a-child-or-a-golden-retriever.md",
            "./docs/pdf/a-child-or-a-golden-retriever.pdf",
            "./docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf",
        ):
            self.assertEqual(readme.count(link), 1, link)

    def test_current_versions_and_checkpoint_boundary_are_pinned(self) -> None:
        manifest = json.loads(HEX_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], HEX_VERSION)
        fiat = FIAT_SKILL.read_text(encoding="utf-8")
        match = re.search(r'^  version: "([^"]+)"$', fiat, flags=re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), FIAT_VERSION)
        self.assertIn("### fiat-controller-checkpoint", fiat)
        self.assertIn("hexctl checkpoint export", fiat)
        self.assertIn("hexctl checkpoint restore", fiat)

        procedure = PUSH_DISCIPLINE.read_text(encoding="utf-8")
        self.assertIn("checkpoint export --out", procedure)
        self.assertIn("checkpoint restore", procedure)
        self.assertIn("--manifest-sha256", procedure)
        self.assertIn("controller-checkpoint.md", procedure)
        reference = CHECKPOINT_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("`fiat-controller-checkpoint/v1`", reference)
        self.assertIn("Continuation means", reference)
        self.assertIn("never a fresh Fiat ledger", reference)

        study = STUDY.read_text(encoding="utf-8")
        self.assertIn(f"Hexaemeron package `{STUDY_HEX_VERSION}`", study)
        self.assertIn(f"Fiat `{STUDY_FIAT_VERSION}`", study)

        primer = " ".join(PRIMER.read_text(encoding="utf-8").lower().split())
        for stale_claim in (
            "does not yet support checkpointing",
            "before checkpointing exists",
            "checkpoints do not exist",
            "there are no checkpoints",
            "move an unfinished run to another machine",
        ):
            self.assertNotIn(stale_claim, primer)
        self.assertIn(
            "after a completed step, another machine may resume from the portable "
            "checkpoint, but it must verify that checkpoint before doing anything else.",
            primer,
        )
        self.assertIn(
            "no explicitly authorised publisher has a repository-valid signing key and account",
            primer,
        )
        self.assertNotIn("sign and publish as the contributing actor", primer)

    def test_fiat_routes_a_checkpoint_arrival_before_fresh_initialization(self) -> None:
        fiat = FIAT_SKILL.read_text(encoding="utf-8")
        checkpoint = fiat.index("checkpoint zip")
        active_state = fiat.index("If `.hexaemeron/state.json` exists")
        fresh_init = fiat.index("Otherwise: say exactly `Let there be light.`")
        self.assertLess(
            checkpoint,
            active_state,
            "checkpoint recovery must be selected before active-state resume",
        )
        self.assertLess(
            active_state,
            fresh_init,
            "active-state resume must be selected before fresh initialization",
        )

    def test_contributor_guide_and_pdf_state_the_verified_transfer_boundary(self) -> None:
        expected = (
            "after a completed step, another machine may resume from the portable "
            "checkpoint, but it must verify that checkpoint before doing anything else."
        )
        stale_claims = (
            "does not yet support checkpointing",
            "no checkpoints yet",
            "before checkpointing exists",
        )
        guide = " ".join(
            line.removeprefix("> ")
            for line in CONTRIBUTOR_GUIDE.read_text(encoding="utf-8")
            .lower()
            .splitlines()
        )
        guide = " ".join(guide.split())
        builder = " ".join(
            CONTRIBUTOR_BUILDER.read_text(encoding="utf-8").lower().split()
        )
        self.assertIn(expected, guide)
        self.assertIn(expected, builder)
        self.assertIn("arbitrary mid-step state is not portable", guide)
        self.assertIn("restore carries the same verified ledger", builder)
        for stale_claim in stale_claims:
            self.assertNotIn(stale_claim, guide)
            self.assertNotIn(stale_claim, builder)

        pdftotext = shutil.which("pdftotext")
        if pdftotext is not None:
            rendered = " ".join(
                run_text([pdftotext, str(CONTRIBUTOR_PDF), "-"]).lower().split()
            )
            self.assertIn(expected, rendered)
            self.assertIn("restore carries the same verified ledger", rendered)

    def test_builder_runtime_discovery_is_host_neutral(self) -> None:
        module_source = Path(__file__).read_text(encoding="utf-8")
        match = re.search(
            r"^def find_builder_python\(\).*?(?=^class ChildOrGoldenRetrieverPrimerTests)",
            module_source,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(match)
        source = match.group(0)
        self.assertNotIn("/Users/", source)
        self.assertIn("WILDCAT_PRIMER_PYTHON", source)
        self.assertIn("Path.home()", source)

    def test_source_note_pins_archive_prompts_tool_and_cover(self) -> None:
        note = SOURCE_NOTE.read_text(encoding="utf-8")
        self.assertIn(KIT_DIGEST, note)
        self.assertIn("built-in `image_gen` tool", note)
        self.assertIn("docs/assets/a-child-or-a-golden-retriever-cover.png", note)
        self.assertIn(COVER_DIGEST, note)
        prompts = re.findall(r"```text\n(.*?)\n```", note, flags=re.DOTALL)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(
            tuple(hashlib.sha256(prompt.encode("utf-8")).hexdigest() for prompt in prompts),
            PROMPT_DIGESTS,
        )

    def test_png_signatures_dimensions_digests_and_text_free_sources(self) -> None:
        for relative, (expected_dimensions, expected_digest) in SOURCE_PNGS.items():
            path = ROOT / relative
            dimensions, chunks = png_details(path)
            self.assertEqual(dimensions, expected_dimensions, relative)
            self.assertEqual(digest(path), expected_digest, relative)
            if relative in TEXT_FREE_SOURCE_PNGS:
                self.assertTrue(
                    {b"tEXt", b"zTXt", b"iTXt"}.isdisjoint(chunks),
                    relative,
                )
        for relative, expected_dimensions in INFOGRAPHICS.items():
            dimensions, _ = png_details(ROOT / relative)
            self.assertEqual(dimensions, expected_dimensions, relative)

    def test_pdf_signatures_page_bounds_titles_text_and_cover_image(self) -> None:
        pdfinfo = shutil.which("pdfinfo")
        pdftotext = shutil.which("pdftotext")
        pdfimages = shutil.which("pdfimages")
        if not all((pdfinfo, pdftotext, pdfimages)):
            self.skipTest("Poppler command-line tools are not installed")
        for relative, (minimum, maximum, title) in PDFS.items():
            path = ROOT / relative
            payload = path.read_bytes()
            self.assertTrue(payload.startswith(b"%PDF-"), relative)
            self.assertIn(b"\x00", payload[:8192], f"Git must detect {relative} as binary")
            info = run_text([str(pdfinfo), str(path)])
            pages_match = re.search(r"^Pages:\s+(\d+)\s*$", info, flags=re.MULTILINE)
            title_match = re.search(r"^Title:\s+(.+?)\s*$", info, flags=re.MULTILINE)
            size_match = re.search(
                r"^Page size:\s+([0-9.]+) x ([0-9.]+) pts",
                info,
                flags=re.MULTILINE,
            )
            self.assertIsNotNone(pages_match, relative)
            self.assertIsNotNone(title_match, relative)
            self.assertIsNotNone(size_match, relative)
            pages = int(pages_match.group(1))
            self.assertGreaterEqual(pages, minimum, relative)
            self.assertLessEqual(pages, maximum, relative)
            self.assertEqual(title_match.group(1), title, relative)
            self.assertGreater(float(size_match.group(1)), float(size_match.group(2)))
            extracted = " ".join(
                run_text([str(pdftotext), str(path), "-"]).split()
            )
            for _, definition in EXPECTED_DEFINITIONS:
                self.assertIn(definition, extracted, relative)
            self.assertIn(" -> ".join(EXPECTED_LIFECYCLE), extracted.lower(), relative)
        images = run_text(
            [str(pdfimages), "-list", str(ROOT / "docs/pdf/a-child-or-a-golden-retriever.pdf")]
        )
        self.assertRegex(
            images,
            r"(?m)^\s*1\s+\d+\s+image\s+1448\s+1086\s+rgb\s+3\s+8\s+"
            r"(?:jpeg|image)\s+no\s+\d+\s+0\b",
        )

    def test_pdf_links_pass_and_active_content_is_absent(self) -> None:
        if self.report is not None:
            checks = {item["name"]: item for item in self.report["checks"]}
            self.assertEqual(checks["pdf-output"]["status"], "passed")
            self.assertIn("links", checks["pdf-output"]["detail"])
        for relative in PDFS:
            payload = (ROOT / relative).read_bytes()
            for token in (b"/JavaScript", b"/JS ", b"/OpenAction"):
                self.assertNotIn(token, payload, relative)
            for url in PDF_LINKS[relative]:
                self.assertIn(url.encode("ascii"), payload, relative)

    def test_shipped_binary_digests_are_fixed(self) -> None:
        self.assertEqual(set(EXPECTED_BINARY_DIGESTS), NEW_BINARIES)
        for relative, expected in sorted(EXPECTED_BINARY_DIGESTS.items()):
            self.assertEqual(digest(ROOT / relative), expected, relative)

    def test_deterministic_check_report_covers_every_binary(self) -> None:
        if self.report is None:
            self.skipTest(
                "Pillow, pypdf, and ReportLab are not installed; "
                "checked-in binary digests remain covered"
            )
        self.assertEqual(
            self.report["schema"],
            "child-or-golden-retriever-check/v1",
        )
        summary = self.report["summary"]
        self.assertEqual(summary["total"], len(self.report["checks"]))
        self.assertEqual(summary["passed"], summary["total"])
        self.assertEqual(summary["failed"], 0)
        self.assertTrue(
            all(item["status"] == "passed" for item in self.report["checks"])
        )
        self.assertIn("rebuilt byte-identically", self.builder_stdout)
        self.assertEqual(set(self.report["outputs"]), NEW_BINARIES)
        for relative, (dimensions, _) in SOURCE_PNGS.items():
            self.assertEqual(
                self.report["outputs"][relative]["dimensions"],
                list(dimensions),
            )

    def test_declared_contrast_pairs_pass(self) -> None:
        if self.report is None:
            self.skipTest(
                "Pillow, pypdf, and ReportLab are not installed; "
                "the explicit builder check owns rendered contrast"
            )
        checks = {item["name"]: item for item in self.report["checks"]}
        self.assertEqual(checks["contrast"]["status"], "passed")
        ratios = [float(value) for value in re.findall(r"([0-9]+\.[0-9]+):1", checks["contrast"]["detail"])]
        self.assertGreaterEqual(len(ratios), 5)
        self.assertTrue(all(ratio >= 3.0 for ratio in ratios))

    def test_no_kit_references_are_copied_and_horos_covers_binaries(self) -> None:
        forbidden = (
            "WildcatBrandGuideline.pdf",
            "brand-guide-page-",
            "mascot-reference-session",
            "reference-contact-sheet",
        )
        copied = [
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "docs").rglob("*")
            if path.is_file() and any(token in path.name for token in forbidden)
        ]
        self.assertEqual(copied, [])
        boundary = json.loads(
            (ROOT / ".horos" / "boundary.json").read_text(encoding="utf-8")
        )
        entries = {
            item["path"]: item
            for item in boundary.get("entries", [])
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        for relative in sorted(NEW_BINARIES):
            self.assertIn(relative, entries)
            self.assertEqual(entries[relative].get("category"), "binary")


if __name__ == "__main__":
    unittest.main()
