#!/usr/bin/env python3
"""Build the external-contributor field guide from checked-in source.

Run from any directory:

    python3 scripts/build_contributor_guide.py

The public Markdown source is docs/how-to-help-shoggoth.md. This builder owns
the matching five-page visual treatment and writes docs/pdf/how-to-help-shoggoth.pdf.

The harness page's roster is not written here. Its card label, its route line
and its detail all come from scripts/render_harness_roster.py, which derives
them from docs/harness-classification.json. No harness name appears anywhere in
this file, which is what stops the PDF and the two Markdown surfaces disagreeing
about a roster nobody re-probed.

The reportlab version is load-bearing for the committed file rather than only
for this run. .horos/boundary.json records the PDF's exact byte count, and two
boundary cases go red when it moves, so the same page built under a different
reportlab is a change the whole tree sees. The version that built a file is
readable from its /Producer string, and this builder prints it on every run.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import reportlab
from reportlab import rl_config
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


rl_config.useA85 = False


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/pdf/how-to-help-shoggoth.pdf"
COVER_IMAGE = ROOT / "docs/assets/shoggoth-contributor-cover.png"
RENDERER = ROOT / "scripts/render_harness_roster.py"


def roster():
    """scripts/render_harness_roster.py, loaded once by path.

    Loaded rather than imported because scripts/ is not a package, and the
    builder runs from any working directory. The renderer imports no PDF
    library, so this costs the build nothing it did not already pay.
    """
    existing = sys.modules.get("render_harness_roster")
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location("render_harness_roster", RENDERER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"build_contributor_guide: {RENDERER} could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

ATLAS = "https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/"
CHATGPT = f"{ATLAS}go/chatgpt"
CLAUDE = f"{ATLAS}go/claude"
JOB_API = f"{ATLAS}api/job"
INSTALL_CODEX = "https://github.com/wildcat-finance/skills/blob/main/INSTALL.md#codex"
INSTALL_CLAUDE = "https://github.com/wildcat-finance/skills/blob/main/INSTALL.md#claude-code"
GUIDE = "https://github.com/wildcat-finance/skills/blob/main/docs/how-to-help-shoggoth.md"

PAGE_W, PAGE_H = landscape(A4)
MARGIN = 44

BUNKER = HexColor("#141414")
BLUE = HexColor("#3E68FF")
PURPLE = HexColor("#4D26BC")
GOLD = HexColor("#D7A820")
OASIS = HexColor("#FBEDC3")
PAPER = HexColor("#F4F5F9")
INK = HexColor("#18181B")
SLATE = HexColor("#353746")
MUTED = HexColor("#6B6F7D")
LINE = HexColor("#D3D6E0")
GREEN = HexColor("#10A37F")
ORANGE = HexColor("#D97757")


def para(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: float = 11,
    leading: float | None = None,
    color: Color = SLATE,
    font: str = "Helvetica",
    align: int = TA_LEFT,
) -> float:
    """Draw a top-aligned paragraph and fail if its box is too small."""
    style = ParagraphStyle(
        name="inline",
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.28,
        textColor=color,
        alignment=align,
        spaceAfter=0,
        spaceBefore=0,
        allowWidows=0,
        allowOrphans=0,
    )
    paragraph = Paragraph(text, style)
    _, used = paragraph.wrap(w, h)
    if used > h + 0.1:
        raise ValueError(f"Text does not fit its box: {text[:80]!r}")
    paragraph.drawOn(c, x, y + h - used)
    return used


def label(c: canvas.Canvas, text: str, x: float, y: float, color: Color = BLUE) -> None:
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x, y, text.upper())


def footer(c: canvas.Canvas, page: int, *, dark: bool = False) -> None:
    color = HexColor("#B9BCC6") if dark else MUTED
    c.setFillColor(color)
    c.setFont("Helvetica", 7)
    c.drawString(MARGIN, 22, "wildcat skills - the shoggoth / contributor field guide / 31 August 2026")
    c.drawRightString(PAGE_W - MARGIN, 22, f"{page:02d}")


def page_heading(
    c: canvas.Canvas,
    eyebrow: str,
    title: str,
    subtitle: str,
    page: int,
) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    label(c, eyebrow, MARGIN, PAGE_H - 45)
    para(
        c,
        title,
        MARGIN,
        PAGE_H - 118,
        PAGE_W - (2 * MARGIN),
        58,
        size=29,
        leading=31,
        color=INK,
        font="Helvetica-Bold",
    )
    if subtitle:
        para(c, subtitle, MARGIN, PAGE_H - 148, PAGE_W - (2 * MARGIN), 26, size=11.5)
    footer(c, page)


def card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: Color = white,
    stroke: Color = LINE,
    accent: Color | None = None,
    radius: float = 11,
) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    if accent is not None:
        c.setFillColor(accent)
        c.roundRect(x, y + h - 7, w, 7, 4, stroke=0, fill=1)


def pill(c: canvas.Canvas, text: str, x: float, y: float, w: float, fill: Color, color: Color) -> None:
    c.setFillColor(fill)
    c.roundRect(x, y, w, 24, 12, stroke=0, fill=1)
    para(c, text, x + 6, y + 3, w - 12, 18, size=8, color=color, font="Helvetica-Bold", align=TA_CENTER)


def linked_button(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    provider: str,
    title: str,
    detail: str,
    url: str,
    fill: Color,
) -> None:
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, 13, stroke=0, fill=1)
    para(c, provider.upper(), x + 18, y + h - 31, w - 36, 15, size=8, color=white, font="Helvetica-Bold")
    para(c, title, x + 18, y + 27, w - 36, 28, size=17, leading=18, color=white, font="Helvetica-Bold")
    para(c, detail, x + 18, y + 10, w - 36, 15, size=8.5, color=white)
    c.linkURL(url, (x, y, x + w, y + h), relative=0, thickness=0)


def draw_image_contained(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
    image = ImageReader(str(path))
    iw, ih = image.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(image, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, mask="auto")


def bullet(c: canvas.Canvas, text: str, x: float, y: float, w: float, *, color: Color = BLUE) -> None:
    c.setFillColor(color)
    c.circle(x + 4, y + 8, 3.2, stroke=0, fill=1)
    para(c, text, x + 16, y, w - 16, 26, size=9.3, leading=11.5)


def draw_cover(c: canvas.Canvas) -> None:
    c.setFillColor(BUNKER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(0, PAGE_H - 8, PAGE_W, 8, stroke=0, fill=1)
    label(c, "Wildcat Labs Skills - the Shoggoth / contributor field guide", MARGIN, PAGE_H - 52, GOLD)

    card(c, 44, 154, 430, 340, fill=white, stroke=white, radius=15)
    draw_image_contained(c, COVER_IMAGE, 56, 166, 406, 316)

    para(
        c,
        "How to help<br/>build the<br/>Shoggoth",
        504,
        320,
        288,
        170,
        size=31,
        leading=34,
        color=white,
        font="Helvetica-Bold",
    )
    para(
        c,
        "Start with one real gap: try it, preserve it, explain it, or build the next checked piece.",
        504,
        275,
        285,
        52,
        size=12.5,
        leading=16,
        color=HexColor("#DADCE4"),
    )

    c.setFillColor(BLUE)
    c.roundRect(504, 170, 292, 84, 13, stroke=0, fill=1)
    para(
        c,
        "YOU DO NOT NEED TO<br/>LEARN THE WHOLE COLLECTIVE<br/>BEFORE YOU CAN HELP",
        524,
        184,
        252,
        54,
        size=11.8,
        leading=16,
        color=white,
        font="Helvetica-Bold",
    )

    steps = [
        ("1", "TRY", "one real operation"),
        ("2", "PROVE", "one useful change"),
        ("3", "SHARE", "one reviewable result"),
    ]
    x = 44
    for number, heading, detail in steps:
        c.setFillColor(HexColor("#222226"))
        c.roundRect(x, 62, 236, 60, 10, stroke=0, fill=1)
        pill(c, number, x + 12, 80, 26, GOLD, BUNKER)
        para(c, heading, x + 50, 90, 170, 16, size=8.5, color=GOLD, font="Helvetica-Bold")
        para(c, detail, x + 50, 71, 170, 17, size=9.5, color=white)
        x += 258
    footer(c, 1, dark=True)
    c.showPage()


def draw_contribution_page(c: canvas.Canvas) -> None:
    page_heading(
        c,
        "Choose the size of the contribution",
        "Make one real gap smaller.",
        "A reproducible failure or clear example can be more valuable than a broad new feature.",
        2,
    )

    card(c, 44, 352, 754, 104, fill=BUNKER, stroke=GOLD, accent=GOLD, radius=13)
    label(c, "Start where you have evidence", 64, 425, GOLD)
    para(
        c,
        "You can test one shipped operation, add a missing specimen or adapter, improve a confusing front door, implement one recorded frontier, or review a promise and its recovery path.",
        64,
        375,
        710,
        42,
        size=12.2,
        leading=15.5,
        color=white,
        font="Helvetica-Bold",
    )

    boxes = [
        (
            "TRY",
            "Run one documented operation on real work. Preserve the exact command, first failure, and boundary it exposed.",
            BLUE,
        ),
        (
            "ADD",
            "Contribute one source adapter, historical specimen, host boundary, corpus rule, or checked example.",
            GOLD,
        ),
        (
            "BUILD",
            "Take one accepted evolution frontier through implementation, a red-to-green guard, prose, and checks.",
            PURPLE,
        ),
    ]
    box_w = 238
    for index, (heading, body, accent) in enumerate(boxes):
        x = 44 + index * 258
        card(c, x, 190, box_w, 130, fill=white, accent=accent)
        label(c, heading, x + 18, 288, accent)
        para(c, body, x + 18, 214, box_w - 36, 65, size=9.8, leading=13, color=SLATE)

    card(c, 44, 64, 356, 94, fill=white, accent=BLUE)
    label(c, "Self-directed route", 62, 127, BLUE)
    para(c, "Choose one gap. Read its README, runtime contract, canonical skill, and current evolution frontier. Run the scoped checks.", 62, 79, 320, 40, size=9.2, leading=12)

    card(c, 420, 64, 378, 94, fill=OASIS, stroke=GOLD, accent=GOLD)
    label(c, "Atlas + Fiat route", 438, 127, GOLD)
    para(c, "Want the project to choose an unblocked issue and control the whole delivery? Use one Atlas route on the next page.", 438, 79, 342, 40, size=9.2, leading=12, color=BUNKER)
    c.linkURL(GUIDE, (44, 64, 400, 158), relative=0, thickness=0)
    c.linkURL(ATLAS, (420, 64, 798, 158), relative=0, thickness=0)
    c.showPage()


def draw_harness_page(c: canvas.Canvas) -> None:
    page_heading(
        c,
        "The Atlas and Fiat route",
        "Pick the path it actually supports.",
        "The Atlas chooses one unblocked issue. A bootstrap, a local package, and a file-reading fallback are different things.",
        3,
    )

    label(c, "Checked one-click bootstraps", 44, 427)
    linked_button(
        c,
        44,
        326,
        356,
        83,
        provider="OpenAI",
        title="ChatGPT web bootstrap",
        detail="Atlas job + prefilled prompt",
        url=CHATGPT,
        fill=GREEN,
    )
    linked_button(
        c,
        420,
        326,
        378,
        83,
        provider="Anthropic",
        title="Claude web bootstrap",
        detail="Atlas job + prefilled prompt",
        url=CLAUDE,
        fill=ORANGE,
    )

    c.setFillColor(OASIS)
    c.setStrokeColor(GOLD)
    c.roundRect(44, 270, 754, 42, 9, stroke=1, fill=1)
    para(
        c,
        "If a web chat cannot work in the repository and publish as you, stop before init and move the prompt to a local coding harness.",
        60,
        280,
        722,
        20,
        size=10.5,
        color=BUNKER,
        font="Helvetica-Bold",
        align=TA_CENTER,
    )

    label(c, "Native local package routes", 44, 240)
    card(c, 44, 142, 356, 82, fill=white, accent=BLUE)
    para(c, "Codex", 62, 184, 125, 22, size=16, color=INK, font="Helvetica-Bold")
    para(c, "Wildcat marketplace package.<br/>Open the repo, install, paste the Atlas prompt.", 160, 160, 216, 46, size=9.5)
    c.linkURL(INSTALL_CODEX, (44, 142, 400, 224), relative=0, thickness=0)

    card(c, 420, 142, 378, 82, fill=white, accent=PURPLE)
    para(c, "Claude Code", 438, 184, 135, 22, size=16, color=INK, font="Helvetica-Bold")
    para(c, "Wildcat plugin marketplace package.<br/>Open the repo, install, paste the Atlas prompt.", 573, 160, 201, 46, size=9.5)
    c.linkURL(INSTALL_CLAUDE, (420, 142, 798, 224), relative=0, thickness=0)

    # Every string in this card is derived from docs/harness-classification.json.
    # `para` refuses text that overflows its box, so a roster that outgrows the
    # card fails the build rather than shipping a page with a name cut off it.
    render = roster()
    try:
        manifest = render.load_manifest()
    except render.RenderError as error:
        # One line naming what the page could not be drawn from. A traceback
        # here would say the same thing and carry an absolute path out with it.
        raise SystemExit(f"build_contributor_guide: {error}") from error
    card(c, 44, 63, 754, 58, fill=BUNKER, stroke=BUNKER)
    label(c, render.pdf_label(manifest), 62, 98, GOLD)
    para(
        c,
        render.pdf_roster_line(manifest),
        158,
        90,
        440,
        20,
        size=10.5,
        color=white,
        font="Helvetica-Bold",
        align=TA_CENTER,
    )
    para(c, render.pdf_detail(manifest), 596, 66, 182, 52, size=8.2, leading=10, color=HexColor("#DADCE4"), align=TA_CENTER)
    c.linkURL(GUIDE, (44, 63, 798, 121), relative=0, thickness=0)
    c.showPage()


def draw_fiat_page(c: canvas.Canvas) -> None:
    page_heading(
        c,
        "Fiat handles the bounded run",
        "Visible steps. One reviewable contribution.",
        "Fiat supplies the order, checks, and record around one bounded issue.",
        4,
    )

    labels = ["STUDY", "RUNBOOK", "IMPLEMENT", "AUDIT", "PROSE", "PUSH", "INTEGRATE"]
    x = 44
    box_w = 94
    gap = 13
    for index, phase in enumerate(labels):
        fill = BLUE if phase in {"IMPLEMENT", "AUDIT"} else BUNKER
        c.setFillColor(fill)
        c.roundRect(x, 370, box_w, 48, 9, stroke=0, fill=1)
        para(c, phase, x + 5, 386, box_w - 10, 17, size=8.2, color=white, font="Helvetica-Bold", align=TA_CENTER)
        if index < len(labels) - 1:
            c.setFillColor(GOLD)
            c.circle(x + box_w + (gap / 2), 394, 3, stroke=0, fill=1)
        x += box_w + gap

    card(c, 44, 195, 356, 142, fill=white, accent=BLUE)
    label(c, "Fiat owns", 62, 307, BLUE)
    bullet(c, "A study and runbook before implementation.", 62, 274, 310)
    bullet(c, "One step at a time, with the required checks.", 62, 242, 310)
    bullet(c, "Audit and prose review before publication.", 62, 210, 310)

    card(c, 420, 195, 378, 142, fill=white, accent=GOLD)
    label(c, "The contributor owns", 438, 307, GOLD)
    bullet(c, "Their own Git author, signer and GitHub account.", 438, 274, 332, color=GOLD)
    bullet(c, "Keeping the same local workspace available.", 438, 242, 332, color=GOLD)
    bullet(c, "Following a failed gate instead of skipping it.", 438, 210, 332, color=GOLD)

    card(c, 44, 65, 754, 104, fill=BUNKER, stroke=BUNKER)
    label(c, "Done means", 62, 139, GOLD)
    para(
        c,
        "IMPLEMENTATION COMPLETE  /  REQUIRED CHECKS COMPLETE  /  CHANGES COMMITTED AND PUSHED AS DIRECTED  /  NORMAL GITHUB PR READY",
        62,
        104,
        718,
        31,
        size=10.5,
        leading=14,
        color=white,
        font="Helvetica-Bold",
        align=TA_CENTER,
    )
    para(
        c,
        "Completion makes the work inspectable. It does not promise acceptance or merge. Human authorship stays with the contributor.",
        80,
        79,
        682,
        20,
        size=8.8,
        color=HexColor("#DADCE4"),
        align=TA_CENTER,
    )
    c.showPage()


def draw_trouble_page(c: canvas.Canvas) -> None:
    page_heading(
        c,
        "Troubleshooting and the fallback",
        "Stop clearly. Keep the evidence.",
        "Resume only when the recovery is real; a failure is not permission to widen the job or invent a clean result.",
        5,
    )

    problems = [
        ("NO JOB", "Do not invent a number or choose a Wave. Stop and retry the Atlas later.", BLUE),
        ("ALREADY CLAIMED", "If an owner, issue branch or PR is active, ask the Atlas for another job before Fiat starts.", GOLD),
        ("FAILED CHECK", "Keep the state and output. Follow the named recovery and rerun the same check.", PURPLE),
    ]
    box_w = 238
    for index, (heading, body, accent) in enumerate(problems):
        x = 44 + index * 258
        card(c, x, 306, box_w, 135, fill=white, accent=accent)
        label(c, heading, x + 18, 410, accent)
        para(c, body, x + 18, 330, box_w - 36, 68, size=10.2, leading=13.5)

    card(c, 44, 202, 754, 78, fill=OASIS, stroke=GOLD)
    label(c, "Why this shape", 62, 252, GOLD)
    para(
        c,
        "Random allocation spreads contributors across the dependency-clear pool. The issue number bounds the work. Fiat leaves study, implementation and review evidence a maintainer can inspect. The accepted-boundary rule stops unfinished controller state being mistaken for a portable hand-off. Restore carries the same verified ledger.",
        62,
        214,
        718,
        34,
        size=9.5,
        leading=12.5,
        color=BUNKER,
    )

    card(c, 44, 57, 754, 120, fill=BUNKER, stroke=BUNKER)
    label(c, "Secondary manual route", 62, 148, GOLD)
    steps = [
        ("1", "GET /api/job"),
        ("2", "Read number, URL, prompt"),
        ("3", "Open repo; read AGENTS.md"),
        ("4", "Paste the exact prompt"),
        ("5", "Finish the same local run"),
    ]
    x = 62
    widths = [112, 146, 151, 139, 147]
    for (number, text), width in zip(steps, widths):
        pill(c, number, x, 101, 26, GOLD, BUNKER)
        para(c, text, x - 8, 74, width + 16, 22, size=8.4, leading=10, color=white, font="Helvetica-Bold", align=TA_CENTER)
        x += width
    c.linkURL(JOB_API, (44, 57, 798, 177), relative=0, thickness=0)
    c.showPage()


def build(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(
        str(output),
        pagesize=(PAGE_W, PAGE_H),
        pageCompression=1,
        invariant=1,
    )
    pdf.setTitle("How to help build the Shoggoth")
    pdf.setSubject("Contributor routes for Wildcat Labs Skills, from a small checked specimen to a complete Fiat delivery")
    pdf.setAuthor("Wildcat Labs")
    pdf.setCreator("scripts/build_contributor_guide.py")
    draw_cover(pdf)
    draw_contribution_page(pdf)
    draw_harness_page(pdf)
    draw_fiat_page(pdf)
    draw_trouble_page(pdf)
    pdf.save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output.resolve())
    size = args.output.resolve().stat().st_size
    # The reportlab version decides these bytes, and the byte count is recorded
    # in .horos/boundary.json, so a rebuild under a different version turns two
    # boundary cases red. Nothing else in the tree said which version produced
    # the committed file; this line does, and the PDF's own /Producer string
    # carries the same fact inside the artefact.
    print(f"wrote {args.output.resolve()} ({size} bytes, reportlab {reportlab.Version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
