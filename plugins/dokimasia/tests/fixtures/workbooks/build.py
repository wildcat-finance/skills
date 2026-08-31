"""Build every workbook fixture deterministically, benign and hostile.

The fixtures are built rather than committed. A hostile archive is the point of
several of them, and a repository is the wrong place to keep a zip bomb; a
builder also lets a reader see exactly what each fixture contains instead of
opening a binary.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    "</Types>"
)
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOCREL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _workbook_xml(sheets: list[str]) -> str:
    entries = "".join(
        f'<sheet name="{name}" sheetId="{index + 1}" r:id="rId{index + 1}"/>'
        for index, name in enumerate(sheets)
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<workbook xmlns="{MAIN}" xmlns:r="{DOCREL}"><sheets>{entries}</sheets></workbook>'
    )


def _rels_xml(count: int, absolute: bool = False) -> str:
    prefix = "/xl/" if absolute else ""
    entries = "".join(
        f'<Relationship Id="rId{index + 1}" '
        f'Type="{DOCREL}/worksheet" Target="{prefix}worksheets/sheet{index + 1}.xml"/>'
        for index in range(count)
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{RELS}">{entries}</Relationships>'


def _column(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _sheet_xml(rows: list[list[str]], shared: list[str] | None = None,
               inline: bool = False, formula_row: int | None = None) -> str:
    out = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row):
            reference = f"{_column(column_index)}{row_index}"
            if value == "":
                continue
            if formula_row is not None and row_index == formula_row and column_index == 0:
                # A formula whose cached value differs from what evaluating it
                # would give. A reader that computed would disagree.
                cells.append(
                    f'<c r="{reference}" t="str"><f>CONCATENATE("EVAL","-99")</f>'
                    f"<v>{value}</v></c>"
                )
            elif inline:
                cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{value}</t></is></c>')
            elif shared is not None and value in shared:
                cells.append(f'<c r="{reference}" t="s"><v>{shared.index(value)}</v></c>')
            else:
                cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{value}</t></is></c>')
        out.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{MAIN}">'
        f'<sheetData>{"".join(out)}</sheetData></worksheet>'
    )


def _shared_xml(strings: list[str]) -> str:
    items = "".join(f"<si><t>{value}</t></si>" for value in strings)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<sst xmlns="{MAIN}" count="{len(strings)}" uniqueCount="{len(strings)}">{items}</sst>'
    )


HEADER = ["ID", "Flow / Area", "Test step", "Expected result", "Wallet",
          "Tester", "Status", "Comments / Defect ref", "Tx hash / evidence", "Source"]


def _case_rows() -> list[list[str]]:
    return [
        ["1 Admin"],
        ["Admin panel flows"],
        [],
        HEADER,
        ["Login section"],
        ["ADM-01", "Admin login", "Log in", "Succeeds", "EOA", "", "Pass", "clean", "0xabc", "Requested"],
        ["ADM-02", "Invite", "Invite a borrower", "Invite sent", "EOA", "", "Not Run", "", "", "Added"],
        ["M2-03", "Add token", "Add the market token and check the balance",
         "Both hold", "EOA", "", "Pass", "compound row", "0xdef", "Requested"],
        ["ADM-04", "Unknown status", "Do a thing", "It happens", "Safe", "", "Weird", "", "", "Requested"],
    ]


def benign(target: Path) -> Path:
    """Two sheets, shared and inline strings, an empty cell and a cached formula."""
    shared = ["ADM-01", "Admin login", "Pass", "Requested"]
    second = [["Defect ID", "Description"], ["DEF-001", "A defect"]]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("xl/workbook.xml", _workbook_xml(["1 Admin", "Defect Log"]))
        archive.writestr("xl/_rels/workbook.xml.rels", _rels_xml(2))
        archive.writestr("xl/sharedStrings.xml", _shared_xml(shared))
        archive.writestr("xl/worksheets/sheet1.xml", _sheet_xml(_case_rows(), shared=shared))
        archive.writestr("xl/worksheets/sheet2.xml", _sheet_xml(second, inline=True))
    return target


def absolute_targets(target: Path) -> Path:
    """The same workbook, with package-absolute relationship targets."""
    shared = ["ADM-01", "Pass"]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("xl/workbook.xml", _workbook_xml(["1 Admin"]))
        archive.writestr("xl/_rels/workbook.xml.rels", _rels_xml(1, absolute=True))
        archive.writestr("xl/sharedStrings.xml", _shared_xml(shared))
        archive.writestr("xl/worksheets/sheet1.xml", _sheet_xml(_case_rows(), shared=shared))
    return target


def cached_formula(target: Path) -> Path:
    """A status cell holding a formula whose cached value is what must be read."""
    rows = _case_rows()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("xl/workbook.xml", _workbook_xml(["1 Admin"]))
        archive.writestr("xl/_rels/workbook.xml.rels", _rels_xml(1))
        archive.writestr("xl/worksheets/sheet1.xml", _sheet_xml(rows, formula_row=6))
    return target


def zip_bomb(target: Path) -> Path:
    """One member whose expansion ratio is far past the cap."""
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("xl/workbook.xml", _workbook_xml(["1 Admin"]))
        archive.writestr("xl/_rels/workbook.xml.rels", _rels_xml(1))
        archive.writestr("xl/worksheets/sheet1.xml", "0" * (8 * 1024 * 1024))
    return target


def traversal_member(target: Path) -> Path:
    """A member name that would escape the extraction root."""
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("../escaped.xml", "<x/>")
        archive.writestr("xl/workbook.xml", _workbook_xml(["1 Admin"]))
    return target


def too_many_members(target: Path) -> Path:
    """More members than the archive cap allows."""
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        for index in range(600):
            archive.writestr(f"xl/pad/{index}.xml", "<x/>")
    return target


def entity_declaration(target: Path) -> Path:
    """A well-formed archive whose sheet part declares expanding entities."""
    bomb = (
        '<?xml version="1.0"?>\n'
        "<!DOCTYPE worksheet [\n"
        '  <!ENTITY a "AAAAAAAAAA">\n'
        '  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">\n'
        '  <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">\n'
        "]>\n"
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData><row r=\"1\"><c r=\"A1\" t=\"inlineStr\"><is><t>&c;</t></is></c>"
        "</row></sheetData></worksheet>"
    )
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", _workbook_xml(["Cases"]))
        archive.writestr("xl/_rels/workbook.xml.rels", _rels_xml(1))
        archive.writestr("xl/worksheets/sheet1.xml", bomb)
    return target


def not_a_spreadsheet(target: Path) -> Path:
    """A file that is not a zip archive at all."""
    target.write_bytes(b"this is not a spreadsheet")
    return target


BUILDERS = {
    "benign.xlsx": benign,
    "absolute-targets.xlsx": absolute_targets,
    "cached-formula.xlsx": cached_formula,
    "zip-bomb.xlsx": zip_bomb,
    "traversal-member.xlsx": traversal_member,
    "too-many-members.xlsx": too_many_members,
    "entity-declaration.xlsx": entity_declaration,
    "not-a-spreadsheet.xlsx": not_a_spreadsheet,
}


def build_all(directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    return {name: builder(directory / name) for name, builder in BUILDERS.items()}
