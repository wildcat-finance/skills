"""Read a spreadsheet with the standard library, under caps, evaluating nothing.

A workbook is an untrusted zip archive of XML. Everything here treats it that
way: member names are checked before extraction, every size is bounded before
it is read, and the expansion ratio is bounded so an archive cannot spend the
reader's memory. No formula is ever computed. Where a cell holds one, the value
read is the one the producing application cached, and the formula text is not
consulted.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

MAX_MEMBERS = 512
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_EXPANSION_RATIO = 200

NAMESPACE = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RELATIONS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
OFFICE_RELATION = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


class XlsxRefusal(Exception):
    """One named refusal at the archive or document boundary."""


def _checked_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """Every member, once every declared archive cap has held."""
    members = archive.infolist()
    if len(members) > MAX_MEMBERS:
        raise XlsxRefusal(
            f"the archive holds {len(members)} members, over the {MAX_MEMBERS} cap"
        )
    total = 0
    for member in members:
        name = member.filename
        if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
            raise XlsxRefusal(f"member {name!r} is an absolute path")
        if ".." in Path(name).parts:
            raise XlsxRefusal(f"member {name!r} contains a parent-directory segment")
        if member.file_size > MAX_MEMBER_BYTES:
            raise XlsxRefusal(
                f"member {name!r} expands to {member.file_size} bytes, "
                f"over the {MAX_MEMBER_BYTES} cap"
            )
        if member.compress_size > 0:
            ratio = member.file_size / member.compress_size
            if ratio > MAX_EXPANSION_RATIO:
                raise XlsxRefusal(
                    f"member {name!r} expands {ratio:.0f} times, over the "
                    f"{MAX_EXPANSION_RATIO} ratio cap"
                )
        total += member.file_size
        if total > MAX_TOTAL_BYTES:
            raise XlsxRefusal(
                f"the archive expands past the {MAX_TOTAL_BYTES}-byte total cap"
            )
    return members


def _read_member(archive: zipfile.ZipFile, name: str) -> bytes:
    try:
        return archive.read(name)
    except KeyError as error:
        raise XlsxRefusal(f"the workbook has no {name}") from error


def _shared_strings(archive: zipfile.ZipFile, names: set[str]) -> list[str]:
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ElementTree.fromstring(_read_member(archive, "xl/sharedStrings.xml"))
    return ["".join(node.itertext()) for node in root.findall(f"{NAMESPACE}si")]


def _sheet_targets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Sheet names paired with their part, in the workbook's own order."""
    workbook = ElementTree.fromstring(_read_member(archive, "xl/workbook.xml"))
    relations = ElementTree.fromstring(
        _read_member(archive, "xl/_rels/workbook.xml.rels")
    )
    targets = {
        node.get("Id"): node.get("Target")
        for node in relations.findall(f"{RELATIONS}Relationship")
    }
    pairs: list[tuple[str, str]] = []
    for node in workbook.iter(f"{NAMESPACE}sheet"):
        name = node.get("name") or ""
        target = targets.get(node.get(f"{OFFICE_RELATION}id"), "")
        if not target:
            raise XlsxRefusal(f"sheet {name!r} names no part")
        pairs.append((name, _resolve_part(target)))
    return pairs


def _resolve_part(target: str) -> str:
    """Resolve one relationship target against the workbook part's own base.

    A target beginning with `/` is already package-absolute and only loses its
    leading separator. Anything else is relative to `xl/`, which is where
    `xl/workbook.xml` lives.
    """
    if target.startswith("/"):
        return target.lstrip("/")
    if target.startswith("xl/"):
        return target
    return f"xl/{target}"


def _column(reference: str) -> int:
    """Zero-based column index from a cell reference such as `AB7`."""
    index = 0
    for char in reference:
        if not char.isalpha():
            break
        index = index * 26 + (ord(char.upper()) - 64)
    return index - 1


def _cell_value(cell: ElementTree.Element, shared: list[str]) -> str:
    kind = cell.get("t")
    if kind == "inlineStr":
        node = cell.find(f"{NAMESPACE}is")
        return "".join(node.itertext()) if node is not None else ""
    value = cell.find(f"{NAMESPACE}v")
    if value is None or value.text is None:
        return ""
    text = value.text
    if kind == "s":
        try:
            return shared[int(text)]
        except (ValueError, IndexError) as error:
            raise XlsxRefusal(
                f"cell {cell.get('r')!r} names shared string {text!r}, which is absent"
            ) from error
    # `t="str"` is a cached formula result. The `<f>` element beside it is
    # never read, so nothing here evaluates anything.
    return text


def read_sheets(path: Path) -> dict[str, list[list[str]]]:
    """Every sheet as a rectangular grid of strings, in workbook order."""
    if not zipfile.is_zipfile(path):
        raise XlsxRefusal(f"{path.name} is not a spreadsheet archive")
    sheets: dict[str, list[list[str]]] = {}
    with zipfile.ZipFile(path) as archive:
        names = {member.filename for member in _checked_members(archive)}
        shared = _shared_strings(archive, names)
        for sheet_name, part in _sheet_targets(archive):
            if part not in names:
                raise XlsxRefusal(f"sheet {sheet_name!r} names a missing part {part!r}")
            root = ElementTree.fromstring(_read_member(archive, part))
            rows: list[list[str]] = []
            for row in root.iter(f"{NAMESPACE}row"):
                cells: dict[int, str] = {}
                for cell in row.findall(f"{NAMESPACE}c"):
                    reference = cell.get("r") or ""
                    cells[_column(reference)] = _cell_value(cell, shared)
                width = max(cells) + 1 if cells else 0
                rows.append([cells.get(index, "") for index in range(width)])
            sheets[sheet_name] = rows
    return sheets
