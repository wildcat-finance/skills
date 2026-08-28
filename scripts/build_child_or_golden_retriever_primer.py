#!/usr/bin/env python3
"""Build and verify the beginner primer package from one Markdown source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import tempfile
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont
import reportlab
from reportlab import rl_config
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
PDFS = DOCS / "pdf"
PRIMER = DOCS / "a-child-or-a-golden-retriever.md"
SOURCE_NOTE = DOCS / "a-child-or-a-golden-retriever-source-note.md"
STUDY = DOCS / "a-child-or-a-golden-retriever-study.md"
HEX_PLUGIN_MANIFEST = (
    ROOT / "plugins" / "hexaemeron" / ".codex-plugin" / "plugin.json"
)
FIAT_SKILL = ROOT / "plugins" / "hexaemeron" / "skills" / "fiat" / "SKILL.md"
COVER_ART = ASSETS / "a-child-or-a-golden-retriever-cover.png"
ROLES_ART = ASSETS / "a-child-or-a-golden-retriever-mascot-roles.png"
FIAT_ART = ASSETS / "a-child-or-a-golden-retriever-mascot-fiat.png"
WHOS_WHO = ASSETS / "a-child-or-a-golden-retriever-whos-who.png"
FIAT_FLOW = ASSETS / "a-child-or-a-golden-retriever-fiat-flow.png"
PRIMER_PDF = PDFS / "a-child-or-a-golden-retriever.pdf"
QUICK_PDF = PDFS / "a-child-or-a-golden-retriever-quick-start.pdf"

GENERATED = (
    WHOS_WHO.relative_to(ROOT),
    FIAT_FLOW.relative_to(ROOT),
    PRIMER_PDF.relative_to(ROOT),
    QUICK_PDF.relative_to(ROOT),
)
NEW_BINARIES = (
    COVER_ART.relative_to(ROOT),
    ROLES_ART.relative_to(ROOT),
    FIAT_ART.relative_to(ROOT),
    *GENERATED,
)

PNG_WIDTH = 1672
PNG_HEIGHT = 941
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
EXPECTED_KIT_DIGEST = (
    "e09eb107921ab52e467bae54e3e605f2e01fa258df7c12529be44fc486d71218"
)
EXPECTED_HEX_VERSION = "1.6.6"
EXPECTED_FIAT_VERSION = "5.31.1"
STALE_CHECKPOINT_CLAIMS = (
    "does not yet support checkpointing",
    "before checkpointing exists",
    "checkpoints do not exist",
    "there are no checkpoints",
    "move an unfinished run to another machine",
)
EXPECTED_CHECKPOINT_TRANSFER = (
    "after a completed step, another machine may resume from the portable "
    "checkpoint, but it must verify that checkpoint before doing anything else."
)
EXPECTED_SOURCE_ART = {
    ROLES_ART.relative_to(ROOT): {
        "size": (1774, 887),
        "sha256": "f25e3e7c62b22895a89f270b5383288cb4996ac2976987c82170da4ca97e7485",
    },
    FIAT_ART.relative_to(ROOT): {
        "size": (1774, 887),
        "sha256": "6bcbab3534c69e06134e2b404ac765e2a1a859eaff4019a791ce862b2e3b13f5",
    },
}
EXPECTED_COVER = {
    "size": (1448, 1086),
    "bytes": 1_166_639,
    "sha256": "5763ab9da93a3bd3420d2e905eef9525dbeb2e642f3121d8ad76c38d9f9cc32a",
}

BUNKER = "#141414"
BLUE = "#3E68FF"
PURPLE = "#4D26BC"
GOLD = "#D7A820"
OASIS = "#FBEDC3"
PAPER = "#F8F4EA"
WHITE = "#FFFFFF"
SLATE = "#30323A"
GREY = "#E3E5EA"
MUTED = "#666A75"

PRIMER_URL = (
    "https://github.com/wildcat-finance/skills/blob/"
    "docs/a-child-or-a-golden-retriever/docs/"
    "a-child-or-a-golden-retriever.md#the-five-minute-demo"
)
INSTALL_URL = "https://github.com/wildcat-finance/skills/blob/main/INSTALL.md"
INTERCEPTOR_URL = "https://github.com/laurenceday/shoggoth-interceptor"

FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
FONT_REGULAR_PATH = FONT_DIR / "Vera.ttf"
FONT_BOLD_PATH = FONT_DIR / "VeraBd.ttf"
PDF_FONT = "PrimerVera"
PDF_FONT_BOLD = "PrimerVeraBold"
PAGE_W, PAGE_H = landscape(A4)

rl_config.useA85 = False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_regular(path: Path, *, max_bytes: int) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required regular file missing: {path.relative_to(ROOT)}")
    size = path.stat().st_size
    if size <= 0 or size > max_bytes:
        raise ValueError(
            f"file size outside boundary: {path.relative_to(ROOT)} ({size} bytes)"
        )


def marked_block(text: str, name: str) -> list[str]:
    start = f"<!-- primer-{name}:start -->"
    end = f"<!-- primer-{name}:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected one marked block: {name}")
    body = text.split(start, 1)[1].split(end, 1)[0]
    return [line for line in body.strip().splitlines() if line.strip()]


def plain_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("`", "").strip()


def read_primer_data() -> dict[str, object]:
    ensure_regular(PRIMER, max_bytes=128 * 1024)
    text = PRIMER.read_text(encoding="utf-8")
    definitions: list[tuple[str, str]] = []
    pattern = re.compile(r"^- (.+?): (.+)$")
    for line in marked_block(text, "definitions"):
        match = pattern.fullmatch(line)
        if not match:
            raise ValueError(f"malformed definition line: {line}")
        definitions.append((match.group(1), match.group(2)))
    lifecycle_lines = marked_block(text, "lifecycle")
    if len(lifecycle_lines) != 1:
        raise ValueError("lifecycle block must have one line")
    lifecycle = tuple(
        part.strip()
        for part in lifecycle_lines[0].strip("`").split("->")
        if part.strip()
    )
    first_action_lines = marked_block(text, "first-action")
    stop_lines = marked_block(text, "stop-rule")
    if len(first_action_lines) != 1 or len(stop_lines) != 1:
        raise ValueError("action and stop blocks must each have one line")
    data = {
        "text": text,
        "definitions": tuple(definitions),
        "lifecycle": lifecycle,
        "first_action": plain_markdown(first_action_lines[0]),
        "stop_rule": plain_markdown(stop_lines[0]),
    }
    if data["definitions"] != EXPECTED_DEFINITIONS:
        raise ValueError("the four fixed definitions drifted")
    if data["lifecycle"] != EXPECTED_LIFECYCLE:
        raise ValueError("the fixed lifecycle drifted")
    return data


def pillow_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    for path in (FONT_REGULAR_PATH, FONT_BOLD_PATH):
        ensure_regular(path, max_bytes=2 * 1024 * 1024)
    return {
        "body18": ImageFont.truetype(str(FONT_REGULAR_PATH), 18),
        "body23": ImageFont.truetype(str(FONT_REGULAR_PATH), 23),
        "body26": ImageFont.truetype(str(FONT_REGULAR_PATH), 26),
        "bold16": ImageFont.truetype(str(FONT_BOLD_PATH), 16),
        "bold18": ImageFont.truetype(str(FONT_BOLD_PATH), 18),
        "bold22": ImageFont.truetype(str(FONT_BOLD_PATH), 22),
        "bold26": ImageFont.truetype(str(FONT_BOLD_PATH), 26),
        "bold44": ImageFont.truetype(str(FONT_BOLD_PATH), 44),
        "bold58": ImageFont.truetype(str(FONT_BOLD_PATH), 58),
    }


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def wrap_pillow(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    line = words[0]
    for word in words[1:]:
        candidate = f"{line} {word}"
        if text_width(draw, candidate, font) <= width:
            line = candidate
        else:
            lines.append(line)
            line = word
    lines.append(line)
    if any(text_width(draw, line, font) > width for line in lines):
        raise ValueError(f"text cannot fit width {width}: {text}")
    return lines


def draw_pillow_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    *,
    font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int = 6,
    align: str = "left",
) -> int:
    x, y, width, height = box
    lines = wrap_pillow(draw, text, font, width)
    sample = draw.textbbox((0, 0), "Ag", font=font)
    line_height = sample[3] - sample[1]
    total = len(lines) * line_height + max(0, len(lines) - 1) * spacing
    if total > height:
        raise ValueError(f"text overflow in {width} by {height}: {text}")
    cursor = y
    for line in lines:
        line_width = text_width(draw, line, font)
        line_x = x
        if align == "center":
            line_x = x + (width - line_width) // 2
        elif align == "right":
            line_x = x + width - line_width
        draw.text((line_x, cursor), line, font=font, fill=fill)
        cursor += line_height + spacing
    return cursor


def paste_full_width(target: Image.Image, source_path: Path, y: int) -> None:
    ensure_regular(source_path, max_bytes=10 * 1024 * 1024)
    with Image.open(source_path) as opened:
        source = opened.convert("RGB")
    height = round(PNG_WIDTH * source.height / source.width)
    resized = source.resize((PNG_WIDTH, height), Image.Resampling.LANCZOS)
    target.paste(resized, (0, y))


def rounded_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: str,
    outline: str,
    radius: int = 18,
    width: int = 3,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def build_whos_who(data: dict[str, object], output: Path) -> None:
    fonts = pillow_fonts()
    image = Image.new("RGB", (PNG_WIDTH, PNG_HEIGHT), OASIS)
    paste_full_width(image, ROLES_ART, 104)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, PNG_WIDTH, 150), fill=BUNKER)
    draw.text((52, 28), "WHO IS WHO?", font=fonts["bold58"], fill=WHITE)
    draw.text(
        (55, 101),
        "Four names. One bounded system. The target repository still decides.",
        font=fonts["body26"],
        fill=GREY,
    )

    definitions = data["definitions"]
    if not isinstance(definitions, tuple):
        raise TypeError("definitions must be a tuple")
    card_y = 575
    card_h = 277
    gap = 20
    margin = 32
    card_w = (PNG_WIDTH - (2 * margin) - (3 * gap)) // 4
    accents = (BLUE, GOLD, PURPLE, BLUE)
    fills = (WHITE, OASIS, WHITE, WHITE)
    for index, ((label, definition), accent, card_fill) in enumerate(
        zip(definitions, accents, fills)
    ):
        x = margin + index * (card_w + gap)
        rounded_card(
            draw,
            (x, card_y, x + card_w, card_y + card_h),
            fill=card_fill,
            outline=accent,
        )
        draw.rectangle((x, card_y, x + card_w, card_y + 10), fill=accent)
        draw_pillow_text(
            draw,
            label.upper(),
            (x + 22, card_y + 28, card_w - 44, 38),
            font=fonts["bold26"],
            fill=accent if accent != GOLD else BUNKER,
        )
        draw_pillow_text(
            draw,
            definition,
            (x + 22, card_y + 80, card_w - 44, card_h - 102),
            font=fonts["body23"],
            fill=BUNKER,
            spacing=8,
        )

    draw.rectangle((0, 866, PNG_WIDTH, PNG_HEIGHT), fill=BUNKER)
    lifecycle_text = "  ->  ".join(data["lifecycle"])
    draw_pillow_text(
        draw,
        lifecycle_text.upper(),
        (38, 885, PNG_WIDTH - 76, 40),
        font=fonts["bold22"],
        fill=WHITE,
        align="center",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False, compress_level=9)


def build_fiat_flow(data: dict[str, object], output: Path) -> None:
    fonts = pillow_fonts()
    image = Image.new("RGB", (PNG_WIDTH, PNG_HEIGHT), OASIS)
    paste_full_width(image, FIAT_ART, 104)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, PNG_WIDTH, 145), fill=BUNKER)
    draw.text((52, 22), "FIAT KEEPS THE RUN IN ORDER", font=fonts["bold44"], fill=WHITE)
    draw.text(
        (54, 85),
        "One next action. One receipt. Then the next action.",
        font=fonts["body26"],
        fill=GREY,
    )

    card_x = (85, 263, 441, 620, 801, 982, 1160)
    fills = (BLUE, PURPLE, BUNKER, BLUE, PURPLE, BUNKER, BLUE)
    for x, phase, fill in zip(card_x, data["lifecycle"], fills):
        rounded_card(
            draw,
            (x, 485, x + 124, 671),
            fill=fill,
            outline=WHITE,
            radius=10,
            width=3,
        )
        draw_pillow_text(
            draw,
            phase.upper(),
            (x + 8, 555, 108, 60),
            font=fonts["bold16"],
            fill=WHITE,
            spacing=4,
            align="center",
        )

    draw.rectangle((0, 755, PNG_WIDTH, PNG_HEIGHT), fill=BUNKER)
    definitions = data["definitions"]
    if not isinstance(definitions, tuple):
        raise TypeError("definitions must be a tuple")
    gap = 15
    margin = 28
    card_w = (PNG_WIDTH - (2 * margin) - (3 * gap)) // 4
    for index, (label, definition) in enumerate(definitions):
        x = margin + index * (card_w + gap)
        rounded_card(
            draw,
            (x, 774, x + card_w, 922),
            fill=SLATE,
            outline=GOLD if index == 3 else GREY,
            radius=14,
            width=2,
        )
        draw_pillow_text(
            draw,
            label.upper(),
            (x + 16, 790, card_w - 32, 28),
            font=fonts["bold18"],
            fill=GOLD,
        )
        draw_pillow_text(
            draw,
            definition,
            (x + 16, 824, card_w - 32, 83),
            font=fonts["body18"],
            fill=WHITE,
            spacing=4,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False, compress_level=9)


def register_pdf_fonts() -> None:
    if PDF_FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(PDF_FONT, str(FONT_REGULAR_PATH)))
    if PDF_FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, str(FONT_BOLD_PATH)))


def pdf_wrap(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    line = words[0]
    for word in words[1:]:
        candidate = f"{line} {word}"
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            lines.append(line)
            line = word
    lines.append(line)
    if any(pdfmetrics.stringWidth(line, font, size) > width for line in lines):
        raise ValueError(f"PDF text cannot fit width {width}: {text}")
    return lines


def pdf_text(
    pdf: canvas.Canvas,
    text: str,
    *,
    x: float,
    top: float,
    width: float,
    height: float,
    size: float,
    color: str,
    font: str = PDF_FONT,
    leading: float | None = None,
    align: str = "left",
) -> float:
    leading = leading or size * 1.25
    lines = pdf_wrap(text, font, size, width)
    if len(lines) * leading > height + 0.01:
        raise ValueError(f"PDF text overflow in {width} by {height}: {text}")
    y = top - size
    pdf.setFont(font, size)
    pdf.setFillColor(HexColor(color))
    for line in lines:
        if align == "center":
            pdf.drawCentredString(x + width / 2, y, line)
        elif align == "right":
            pdf.drawRightString(x + width, y, line)
        else:
            pdf.drawString(x, y, line)
        y -= leading
    return y


def pdf_card(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    outline: str,
    radius: float = 10,
) -> None:
    pdf.setFillColor(HexColor(fill))
    pdf.setStrokeColor(HexColor(outline))
    pdf.setLineWidth(1)
    pdf.roundRect(x, y, width, height, radius, stroke=1, fill=1)


def pdf_image_contained(
    pdf: canvas.Canvas,
    path: Path,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    image = ImageReader(str(path))
    image_width, image_height = image.getSize()
    scale = min(width / image_width, height / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    pdf.drawImage(
        image,
        x + (width - draw_width) / 2,
        y + (height - draw_height) / 2,
        draw_width,
        draw_height,
        mask="auto",
    )


def pdf_footer(pdf: canvas.Canvas, page: int, *, dark: bool = False) -> None:
    pdf.setFont(PDF_FONT, 7)
    pdf.setFillColor(HexColor(GREY if dark else MUTED))
    pdf.drawString(35, 18, "Wildcat Skills / beginner primer / 27 August 2026")
    pdf.drawRightString(PAGE_W - 35, 18, f"{page:02d}")


def pdf_link_button(
    pdf: canvas.Canvas,
    text: str,
    url: str,
    *,
    x: float,
    y: float,
    width: float,
    fill: str,
) -> None:
    pdf.setFillColor(HexColor(fill))
    pdf.roundRect(x, y, width, 32, 9, stroke=0, fill=1)
    pdf.setFillColor(HexColor(WHITE))
    pdf.setFont(PDF_FONT_BOLD, 9)
    pdf.drawCentredString(x + width / 2, y + 11, text)
    pdf.linkURL(url, (x, y, x + width, y + 32), relative=0, thickness=0)


def new_pdf(path: Path, title: str, subject: str) -> canvas.Canvas:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(
        str(path),
        pagesize=(PAGE_W, PAGE_H),
        invariant=1,
        pageCompression=1,
    )
    pdf.setTitle(title)
    pdf.setSubject(subject)
    pdf.setAuthor("Wildcat Labs")
    pdf.setCreator("scripts/build_child_or_golden_retriever_primer.py")
    return pdf


def primer_page_one(pdf: canvas.Canvas, data: dict[str, object]) -> None:
    pdf.setFillColor(HexColor(BUNKER))
    pdf.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    pdf.setFillColor(HexColor(GOLD))
    pdf.rect(0, PAGE_H - 8, PAGE_W, 8, stroke=0, fill=1)
    pdf_text(
        pdf,
        "A CHILD OR A GOLDEN RETRIEVER",
        x=42,
        top=PAGE_H - 42,
        width=360,
        height=36,
        size=13,
        color=GOLD,
        font=PDF_FONT_BOLD,
    )
    pdf_text(
        pdf,
        "The five-minute primer for the Shoggoth, the Interceptor, Hex, and Fiat.",
        x=42,
        top=PAGE_H - 82,
        width=350,
        height=105,
        size=23,
        leading=27,
        color=WHITE,
        font=PDF_FONT_BOLD,
    )
    pdf_text(
        pdf,
        "Four names. One bounded delivery system. The target repository still decides.",
        x=42,
        top=PAGE_H - 196,
        width=340,
        height=58,
        size=12,
        leading=16,
        color=GREY,
    )
    pdf_card(pdf, 402, 164, 397, 344, fill=WHITE, outline=GOLD, radius=14)
    pdf_image_contained(pdf, COVER_ART, 414, 176, 373, 320)

    definitions = data["definitions"]
    if not isinstance(definitions, tuple):
        raise TypeError("definitions must be a tuple")
    y = 224
    for index, (label, definition) in enumerate(definitions):
        box_y = y - index * 54
        pdf_card(pdf, 42, box_y, 336, 46, fill=SLATE, outline=SLATE, radius=8)
        pdf_text(
            pdf,
            label.upper(),
            x=54,
            top=box_y + 35,
            width=92,
            height=18,
            size=8,
            color=GOLD,
            font=PDF_FONT_BOLD,
        )
        pdf_text(
            pdf,
            definition,
            x=145,
            top=box_y + 36,
            width=220,
            height=31,
            size=7.7,
            leading=9.4,
            color=WHITE,
        )
    lifecycle = "  ->  ".join(data["lifecycle"])
    pdf_text(
        pdf,
        lifecycle.upper(),
        x=42,
        top=55,
        width=757,
        height=20,
        size=9,
        color=WHITE,
        font=PDF_FONT_BOLD,
        align="center",
    )
    pdf_link_button(
        pdf,
        "OPEN THE FIVE-MINUTE DEMO",
        PRIMER_URL,
        x=586,
        y=58,
        width=213,
        fill=BLUE,
    )
    pdf_footer(pdf, 1, dark=True)
    pdf.showPage()


def primer_infographic_page(
    pdf: canvas.Canvas, image_path: Path, page: int, heading: str
) -> None:
    pdf.setFillColor(HexColor(PAPER))
    pdf.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    pdf_text(
        pdf,
        heading,
        x=35,
        top=PAGE_H - 24,
        width=771,
        height=28,
        size=14,
        color=BUNKER,
        font=PDF_FONT_BOLD,
    )
    pdf_image_contained(pdf, image_path, 20, 55, PAGE_W - 40, PAGE_H - 105)
    pdf_footer(pdf, page)
    pdf.showPage()


def primer_start_page(pdf: canvas.Canvas, data: dict[str, object]) -> None:
    pdf.setFillColor(HexColor(PAPER))
    pdf.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    pdf_text(
        pdf,
        "THE FIRST SAFE ACTION",
        x=42,
        top=PAGE_H - 38,
        width=757,
        height=44,
        size=25,
        color=BUNKER,
        font=PDF_FONT_BOLD,
    )
    pdf_text(
        pdf,
        "Fiat is explicit-only. Mentioning Hex or calling someone Shog does not start it.",
        x=42,
        top=PAGE_H - 82,
        width=757,
        height=35,
        size=12,
        color=MUTED,
    )
    pdf_card(pdf, 42, 316, 757, 128, fill=WHITE, outline=BLUE, radius=12)
    pdf_text(
        pdf,
        str(data["first_action"]),
        x=62,
        top=421,
        width=717,
        height=88,
        size=14,
        leading=19,
        color=BUNKER,
        font=PDF_FONT_BOLD,
    )
    pdf_link_button(
        pdf, "INSTALL HEXAEMERON", INSTALL_URL, x=584, y=329, width=195, fill=BLUE
    )

    pdf_text(
        pdf,
        "FIAT LIFECYCLE",
        x=42,
        top=285,
        width=757,
        height=24,
        size=11,
        color=PURPLE,
        font=PDF_FONT_BOLD,
    )
    phase_width = 96
    phase_gap = 11
    x = 42
    for index, phase in enumerate(data["lifecycle"]):
        fill = BLUE if phase in {"implement", "audit"} else BUNKER
        pdf_card(pdf, x, 218, phase_width, 46, fill=fill, outline=fill, radius=8)
        pdf_text(
            pdf,
            str(phase).upper(),
            x=x + 4,
            top=247,
            width=phase_width - 8,
            height=20,
            size=7.7,
            color=WHITE,
            font=PDF_FONT_BOLD,
            align="center",
        )
        if index < len(data["lifecycle"]) - 1:
            pdf.setFillColor(HexColor(GOLD))
            pdf.circle(x + phase_width + phase_gap / 2, 241, 2.5, stroke=0, fill=1)
        x += phase_width + phase_gap

    pdf_card(pdf, 42, 66, 757, 126, fill=BUNKER, outline=BUNKER, radius=12)
    pdf_text(
        pdf,
        str(data["stop_rule"]),
        x=62,
        top=168,
        width=717,
        height=84,
        size=13,
        leading=17,
        color=WHITE,
        font=PDF_FONT_BOLD,
    )
    pdf_footer(pdf, 4)
    pdf.showPage()


def primer_demo_page(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(HexColor(PAPER))
    pdf.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    pdf_text(
        pdf,
        "THE FIVE-MINUTE DEMO",
        x=42,
        top=PAGE_H - 38,
        width=757,
        height=44,
        size=25,
        color=BUNKER,
        font=PDF_FONT_BOLD,
    )
    questions = (
        "1. Is the Interceptor a new member, or the same collective in an external harness?",
        "2. Which name is the delivery plugin, and which is its explicit controller?",
        "3. Can you put study, runbook, implement, audit, prose, push, and integrate in order?",
        "4. Can you point to the first safe action and name the reasons to stop?",
    )
    y = 414
    for index, question in enumerate(questions):
        fill = WHITE if index % 2 == 0 else OASIS
        pdf_card(pdf, 42, y, 757, 72, fill=fill, outline=GREY, radius=10)
        pdf_text(
            pdf,
            question,
            x=62,
            top=y + 50,
            width=717,
            height=42,
            size=12.5,
            leading=16,
            color=BUNKER,
            font=PDF_FONT_BOLD,
        )
        y -= 86
    pdf_text(
        pdf,
        "If an answer is fuzzy, look at the two infographics and try once more. "
        "An explanation that still needs private context is the failure case.",
        x=42,
        top=117,
        width=500,
        height=48,
        size=10.5,
        leading=14,
        color=MUTED,
    )
    pdf_link_button(
        pdf, "READ THE SOURCE PRIMER", PRIMER_URL, x=563, y=74, width=236, fill=PURPLE
    )
    pdf_link_button(
        pdf,
        "SEE THE INTERCEPTOR",
        INTERCEPTOR_URL,
        x=563,
        y=34,
        width=236,
        fill=BUNKER,
    )
    pdf_footer(pdf, 5)
    pdf.showPage()


def build_primer_pdf(data: dict[str, object], output: Path) -> None:
    register_pdf_fonts()
    pdf = new_pdf(
        output,
        "A child or a golden retriever",
        "A five-minute primer for Shoggoth, the Interceptor, Hexaemeron, and Fiat",
    )
    primer_page_one(pdf, data)
    primer_infographic_page(pdf, WHOS_WHO, 2, "THE FOUR NAMES")
    primer_infographic_page(pdf, FIAT_FLOW, 3, "THE ORDER FIAT KEEPS")
    primer_start_page(pdf, data)
    primer_demo_page(pdf)
    pdf.save()


def build_quick_pdf(data: dict[str, object], output: Path) -> None:
    register_pdf_fonts()
    pdf = new_pdf(
        output,
        "A child or a golden retriever - quick-start",
        "One-page quick-start for Shoggoth, the Interceptor, Hexaemeron, and Fiat",
    )
    pdf.setFillColor(HexColor(PAPER))
    pdf.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    pdf.setFillColor(HexColor(BUNKER))
    pdf.rect(0, PAGE_H - 93, PAGE_W, 93, stroke=0, fill=1)
    pdf_text(
        pdf,
        "THE ONE-PAGE QUICK-START",
        x=36,
        top=PAGE_H - 28,
        width=520,
        height=34,
        size=21,
        color=WHITE,
        font=PDF_FONT_BOLD,
    )
    pdf_text(
        pdf,
        "Shoggoth / Interceptor / Hex / Fiat",
        x=36,
        top=PAGE_H - 59,
        width=520,
        height=20,
        size=10,
        color=GOLD,
        font=PDF_FONT_BOLD,
    )
    pdf_link_button(
        pdf,
        "FULL FIVE-MINUTE PRIMER",
        PRIMER_URL,
        x=594,
        y=PAGE_H - 66,
        width=211,
        fill=BLUE,
    )

    definitions = data["definitions"]
    if not isinstance(definitions, tuple):
        raise TypeError("definitions must be a tuple")
    card_width = 376
    card_height = 75
    positions = ((36, 404), (429, 404), (36, 315), (429, 315))
    for index, ((label, definition), (x, y)) in enumerate(zip(definitions, positions)):
        pdf_card(
            pdf,
            x,
            y,
            card_width,
            card_height,
            fill=WHITE if index != 1 else OASIS,
            outline=(BLUE, GOLD, PURPLE, BLUE)[index],
            radius=10,
        )
        pdf_text(
            pdf,
            label.upper(),
            x=x + 14,
            top=y + 56,
            width=102,
            height=18,
            size=7.5,
            color=PURPLE if index == 2 else BUNKER,
            font=PDF_FONT_BOLD,
        )
        pdf_text(
            pdf,
            definition,
            x=x + 116,
            top=y + 58,
            width=246,
            height=51,
            size=7.3,
            leading=9.3,
            color=BUNKER,
        )

    lifecycle = "  ->  ".join(data["lifecycle"])
    pdf_card(pdf, 36, 250, 769, 44, fill=BUNKER, outline=BUNKER, radius=9)
    pdf_text(
        pdf,
        lifecycle.upper(),
        x=48,
        top=277,
        width=745,
        height=20,
        size=8.7,
        color=WHITE,
        font=PDF_FONT_BOLD,
        align="center",
    )

    pdf_card(pdf, 36, 106, 480, 124, fill=WHITE, outline=BLUE, radius=10)
    pdf_text(
        pdf,
        str(data["first_action"]),
        x=51,
        top=209,
        width=450,
        height=83,
        size=10,
        leading=13,
        color=BUNKER,
        font=PDF_FONT_BOLD,
    )
    pdf_link_button(pdf, "INSTALL", INSTALL_URL, x=386, y=119, width=115, fill=BLUE)

    pdf_card(pdf, 531, 106, 274, 124, fill=BUNKER, outline=BUNKER, radius=10)
    pdf_text(
        pdf,
        str(data["stop_rule"]),
        x=546,
        top=209,
        width=244,
        height=90,
        size=8.3,
        leading=10.5,
        color=WHITE,
        font=PDF_FONT_BOLD,
    )
    pdf_footer(pdf, 1)
    pdf.showPage()
    pdf.save()


def build_into(stage_root: Path) -> None:
    data = read_primer_data()
    build_whos_who(data, stage_root / WHOS_WHO.relative_to(ROOT))
    build_fiat_flow(data, stage_root / FIAT_FLOW.relative_to(ROOT))
    original_whos = globals()["WHOS_WHO"]
    original_flow = globals()["FIAT_FLOW"]
    try:
        globals()["WHOS_WHO"] = stage_root / WHOS_WHO.relative_to(ROOT)
        globals()["FIAT_FLOW"] = stage_root / FIAT_FLOW.relative_to(ROOT)
        build_primer_pdf(data, stage_root / PRIMER_PDF.relative_to(ROOT))
        build_quick_pdf(data, stage_root / QUICK_PDF.relative_to(ROOT))
    finally:
        globals()["WHOS_WHO"] = original_whos
        globals()["FIAT_FLOW"] = original_flow


def atomic_install(stage_root: Path) -> None:
    for relative in GENERATED:
        source = stage_root / relative
        destination = ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink() or destination.parent.is_symlink():
            raise ValueError(f"refusing symlink output: {relative}")
        temporary = destination.with_name(f".{destination.name}.new")
        temporary.write_bytes(source.read_bytes())
        os.replace(temporary, destination)


def png_chunks(path: Path) -> tuple[bytes, ...]:
    payload = path.read_bytes()
    if not payload.startswith(bytes.fromhex("89504e470d0a1a0a")):
        raise ValueError(f"not a PNG: {path.relative_to(ROOT)}")
    chunks: list[bytes] = []
    cursor = 8
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise ValueError(f"truncated PNG chunk: {path.relative_to(ROOT)}")
        length = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        chunk_type = payload[cursor + 4 : cursor + 8]
        end = cursor + 12 + length
        if end > len(payload):
            raise ValueError(f"oversized PNG chunk: {path.relative_to(ROOT)}")
        chunks.append(chunk_type)
        cursor = end
        if chunk_type == b"IEND":
            break
    if not chunks or chunks[-1] != b"IEND":
        raise ValueError(f"missing PNG IEND: {path.relative_to(ROOT)}")
    return tuple(chunks)


def relative_contrast(first: str, second: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    one, two = luminance(first), luminance(second)
    lighter, darker = max(one, two), min(one, two)
    return (lighter + 0.05) / (darker + 0.05)


def check_source_art() -> str:
    for relative, expected in EXPECTED_SOURCE_ART.items():
        path = ROOT / relative
        ensure_regular(path, max_bytes=10 * 1024 * 1024)
        if sha256(path) != expected["sha256"]:
            raise ValueError(f"source art digest drifted: {relative}")
        with Image.open(path) as image:
            if image.size != expected["size"]:
                raise ValueError(f"source art dimensions drifted: {relative}")
            image.verify()
        chunks = png_chunks(path)
        if {b"tEXt", b"zTXt", b"iTXt"}.intersection(chunks):
            raise ValueError(f"source art carries textual PNG chunks: {relative}")
    note = SOURCE_NOTE.read_text(encoding="utf-8")
    for phrase in (
        "Neither contains a",
        "word, letter, number, logo, caption, speech bubble, watermark",
        "The cards and pages are blank.",
    ):
        if phrase not in note:
            raise ValueError("source note lost the no-typography visual review")
    return "2 source illustrations: fixed digest, dimensions, PNG structure, and visual-review record"


def check_cover_art() -> str:
    ensure_regular(COVER_ART, max_bytes=4 * 1024 * 1024)
    if COVER_ART.stat().st_size != EXPECTED_COVER["bytes"]:
        raise ValueError("Creator-supplied cover byte size drifted")
    if sha256(COVER_ART) != EXPECTED_COVER["sha256"]:
        raise ValueError("Creator-supplied cover digest drifted")
    with Image.open(COVER_ART) as image:
        if image.size != EXPECTED_COVER["size"] or image.mode != "RGB":
            raise ValueError("Creator-supplied cover properties drifted")
        image.verify()
    png_chunks(COVER_ART)
    note = SOURCE_NOTE.read_text(encoding="utf-8")
    if EXPECTED_COVER["sha256"] not in note or "copied byte for byte" not in note:
        raise ValueError("source note lost the supplied-cover provenance")
    primer = PRIMER.read_text(encoding="utf-8")
    if "./assets/a-child-or-a-golden-retriever-cover.png" not in primer:
        raise ValueError("Markdown primer lost the supplied cover")
    return "1 Creator-supplied cover: fixed bytes, digest, dimensions, mode, and provenance"


def check_png_outputs() -> str:
    for path in (WHOS_WHO, FIAT_FLOW):
        ensure_regular(path, max_bytes=12 * 1024 * 1024)
        with Image.open(path) as image:
            if image.size != (PNG_WIDTH, PNG_HEIGHT):
                raise ValueError(f"wrong infographic dimensions: {path.relative_to(ROOT)}")
            if image.mode != "RGB":
                raise ValueError(f"wrong infographic mode: {path.relative_to(ROOT)}")
            image.verify()
        png_chunks(path)
    return "2 PNGs: 1672 by 941, RGB, valid chunk stream"


def pdf_links(reader: object) -> set[str]:
    links: set[str] = set()
    for page in getattr(reader, "pages"):
        for reference in page.get("/Annots", []):
            annotation = reference.get_object()
            action = annotation.get("/A")
            if action is None:
                continue
            action = action.get_object()
            uri = action.get("/URI")
            if uri:
                links.add(str(uri))
    return links


def check_pdf_outputs() -> str:
    from pypdf import PdfReader

    specifications = (
        (
            PRIMER_PDF,
            "A child or a golden retriever",
            2,
            6,
            {PRIMER_URL, INSTALL_URL, INTERCEPTOR_URL},
        ),
        (
            QUICK_PDF,
            "A child or a golden retriever - quick-start",
            1,
            1,
            {PRIMER_URL, INSTALL_URL},
        ),
    )
    for path, title, minimum, maximum, expected_links in specifications:
        ensure_regular(path, max_bytes=15 * 1024 * 1024)
        payload = path.read_bytes()
        if not payload.startswith(b"%PDF-"):
            raise ValueError(f"not a PDF: {path.relative_to(ROOT)}")
        if b"/JavaScript" in payload or b"/JS " in payload or b"/OpenAction" in payload:
            raise ValueError(f"active content found: {path.relative_to(ROOT)}")
        reader = PdfReader(path)
        if not minimum <= len(reader.pages) <= maximum:
            raise ValueError(f"page bound failed: {path.relative_to(ROOT)}")
        if str(reader.metadata.title) != title:
            raise ValueError(f"title mismatch: {path.relative_to(ROOT)}")
        text = " ".join(
            " ".join((page.extract_text() or "").split()) for page in reader.pages
        )
        for _, definition in EXPECTED_DEFINITIONS:
            if definition not in text:
                raise ValueError(f"definition missing from PDF: {path.relative_to(ROOT)}")
        lifecycle = " -> ".join(EXPECTED_LIFECYCLE)
        if lifecycle not in text.lower():
            raise ValueError(f"lifecycle missing from PDF: {path.relative_to(ROOT)}")
        missing_links = expected_links - pdf_links(reader)
        if missing_links:
            raise ValueError(
                f"links missing from {path.relative_to(ROOT)}: {sorted(missing_links)}"
            )
        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            if not (840 <= width <= 843 and 594 <= height <= 597 and width > height):
                raise ValueError(f"not horizontal A4: {path.relative_to(ROOT)}")
    return "2 PDFs: page bounds, titles, text, links, horizontal A4, and no active content"


def check_contrast() -> str:
    pairs = (
        ("white on bunker", WHITE, BUNKER, 4.5),
        ("bunker on oasis", BUNKER, OASIS, 4.5),
        ("white on purple", WHITE, PURPLE, 4.5),
        ("bunker on gold", BUNKER, GOLD, 4.5),
        ("white on blue large", WHITE, BLUE, 3.0),
    )
    results = []
    for name, foreground, background, threshold in pairs:
        ratio = relative_contrast(foreground, background)
        if ratio < threshold:
            raise ValueError(f"contrast failed: {name} ({ratio:.2f}:1)")
        results.append(f"{name} {ratio:.2f}:1")
    return "; ".join(results)


def check_horos() -> str:
    boundary = ROOT / ".horos" / "boundary.json"
    ensure_regular(boundary, max_bytes=10 * 1024 * 1024)
    document = json.loads(boundary.read_text(encoding="utf-8"))
    entries = {
        entry.get("path"): entry
        for entry in document.get("entries", [])
        if isinstance(entry, dict)
    }
    missing = []
    for relative in NEW_BINARIES:
        entry = entries.get(relative.as_posix())
        if entry is None or entry.get("category") != "binary":
            missing.append(relative.as_posix())
    if missing:
        raise ValueError(f"Horos missing new tracked binaries: {missing}")
    return f"{len(NEW_BINARIES)} new binary paths classified"


def check_source_inventory() -> str:
    text = PRIMER.read_text(encoding="utf-8")
    if "## The five-minute demo" not in text:
        raise ValueError("five-minute demo heading missing")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "./docs/a-child-or-a-golden-retriever.md" not in readme:
        raise ValueError("README primer link missing")
    note = SOURCE_NOTE.read_text(encoding="utf-8")
    if EXPECTED_KIT_DIGEST not in note:
        raise ValueError("source note archive digest missing")
    if note.count("Use case: illustration-story") != 2:
        raise ValueError("source note must carry two exact image prompts")
    forbidden_names = (
        "WildcatBrandGuideline.pdf",
        "brand-guide-page-",
        "mascot-reference-session",
        "reference-contact-sheet",
    )
    for path in DOCS.rglob("*"):
        if path.is_file() and any(token in path.name for token in forbidden_names):
            raise ValueError(f"copied kit reference found: {path.relative_to(ROOT)}")
    return "canonical markers, demo anchor, README link, source provenance, and no copied kit reference"


def check_current_state() -> str:
    ensure_regular(HEX_PLUGIN_MANIFEST, max_bytes=128 * 1024)
    ensure_regular(FIAT_SKILL, max_bytes=256 * 1024)
    ensure_regular(STUDY, max_bytes=256 * 1024)

    manifest = json.loads(HEX_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("version") != EXPECTED_HEX_VERSION:
        raise ValueError("Hexaemeron version moved; review the beginner primer")

    fiat_text = FIAT_SKILL.read_text(encoding="utf-8")
    fiat_match = re.search(r'^  version: "([^"]+)"$', fiat_text, flags=re.MULTILINE)
    if fiat_match is None or fiat_match.group(1) != EXPECTED_FIAT_VERSION:
        raise ValueError("Fiat version moved; review the beginner primer")

    study = STUDY.read_text(encoding="utf-8")
    for version in (EXPECTED_HEX_VERSION, EXPECTED_FIAT_VERSION):
        if version not in study:
            raise ValueError(f"shipped study lost current version {version}")

    primer = " ".join(PRIMER.read_text(encoding="utf-8").lower().split())
    stale = [claim for claim in STALE_CHECKPOINT_CLAIMS if claim in primer]
    if stale:
        raise ValueError(f"stale checkpoint claim returned: {stale}")
    if EXPECTED_CHECKPOINT_TRANSFER not in primer:
        raise ValueError("verified portable checkpoint transfer guidance missing")
    return (
        f"Hexaemeron {EXPECTED_HEX_VERSION}, Fiat {EXPECTED_FIAT_VERSION}, "
        "no stale checkpoint claim, and verified portable transfer guidance"
    )


def compare_generated(stage_root: Path) -> str:
    mismatches = []
    for relative in GENERATED:
        staged = stage_root / relative
        final = ROOT / relative
        if not final.is_file() or staged.read_bytes() != final.read_bytes():
            mismatches.append(relative.as_posix())
    if mismatches:
        raise ValueError(f"deterministic rebuild mismatch: {mismatches}")
    return f"{len(GENERATED)} generated outputs rebuilt byte-identically"


def output_metadata() -> dict[str, object]:
    metadata: dict[str, object] = {}
    for relative in (COVER_ART.relative_to(ROOT), *EXPECTED_SOURCE_ART.keys(), *GENERATED):
        path = ROOT / relative
        item: dict[str, object] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        if path.suffix == ".png":
            with Image.open(path) as image:
                item["dimensions"] = [image.width, image.height]
        else:
            from pypdf import PdfReader

            item["pages"] = len(PdfReader(path).pages)
        metadata[relative.as_posix()] = item
    return metadata


def safe_report_path(raw: Path) -> Path:
    candidate = raw if raw.is_absolute() else ROOT / raw
    candidate = candidate.resolve()
    allowed = (ROOT / "tmp" / "elenchus").resolve()
    try:
        candidate.relative_to(allowed)
    except ValueError as exc:
        raise ValueError("report must stay under tmp/elenchus") from exc
    if candidate.exists() and candidate.is_symlink():
        raise ValueError("refusing symlink report")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    if candidate.parent.is_symlink():
        raise ValueError("refusing symlink report parent")
    return candidate


def write_report(path: Path, report: dict[str, object]) -> None:
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.new")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def run_check(stage_root: Path, report_path: Path) -> int:
    checks: list[dict[str, str]] = []

    def record(name: str, operation: Callable[[], str]) -> None:
        try:
            detail = operation()
        except Exception as exc:
            checks.append({"name": name, "status": "failed", "detail": str(exc)})
        else:
            checks.append({"name": name, "status": "passed", "detail": detail})

    record(
        "canonical-source",
        lambda: f"{len(read_primer_data()['definitions'])} definitions and 7 phases",
    )
    record("source-inventory", check_source_inventory)
    record("current-state", check_current_state)
    record("supplied-cover", check_cover_art)
    record("source-art", check_source_art)
    record("deterministic-rebuild", lambda: compare_generated(stage_root))
    record("png-output", check_png_outputs)
    record("pdf-output", check_pdf_outputs)
    record("contrast", check_contrast)
    record("horos", check_horos)

    failed = sum(item["status"] == "failed" for item in checks)
    report: dict[str, object] = {
        "schema": "child-or-golden-retriever-check/v1",
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": len(checks) - failed,
            "failed": failed,
        },
    }
    if failed == 0:
        report["outputs"] = output_metadata()
    write_report(report_path, report)
    for item in checks:
        print(f"{item['status'].upper()} {item['name']}: {item['detail']}")
    print(
        f"SUMMARY {len(checks) - failed} passed, {failed} failed; "
        f"report={report_path.relative_to(ROOT)}"
    )
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.check and args.report is None:
        parser.error("--check requires --report")
    if not args.check and args.report is not None:
        parser.error("--report is valid only with --check")

    tmp_root = ROOT / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    if tmp_root.is_symlink():
        raise ValueError("refusing symlink temporary root")
    with tempfile.TemporaryDirectory(
        prefix="child-or-golden-retriever.", dir=tmp_root
    ) as directory:
        stage_root = Path(directory)
        build_into(stage_root)
        if args.check:
            return run_check(stage_root, safe_report_path(args.report))
        atomic_install(stage_root)

    for relative in GENERATED:
        path = ROOT / relative
        print(f"wrote {relative} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
