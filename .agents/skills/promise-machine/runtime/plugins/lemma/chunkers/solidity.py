#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""
Lemma Solidity chunker

Turns Solidity into retrieval chunks via the compiler's AST, one chunk per
semantic unit, with natspec attached and citations that point at real bytes.

Input is a solc standard-json input file, the same `standard-input.json` that
verified deployments ship for Etherscan. That file carries the full source set
and the exact compiler settings used for the deployed bytecode, so chunks
describe that compiled source rather than whatever the working tree happened to
contain when the tool ran.

    python3 solidity.py \\
        --input .../MyContract-0xabc.../standard-input.json \\
        --solc solc --include 'src/**' --out chunks.jsonl

Read INVARIANTS.md before trusting the output. A crash is visible, but a chunk
that cites the wrong source can still look verified.
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

_spec = importlib.util.spec_from_file_location(
    "lemma_schema", pathlib.Path(__file__).resolve().parent.parent / "schema.py")
_schema = importlib.util.module_from_spec(_spec)
sys.modules["lemma_schema"] = _schema
_spec.loader.exec_module(_schema)
Chunk = _schema.Chunk

# Nodes that become their own chunk.
CHUNKABLE = {
    "FunctionDefinition",
    "ModifierDefinition",
    "EventDefinition",
    "ErrorDefinition",
    "StructDefinition",
    "EnumDefinition",
    "UserDefinedValueTypeDefinition",
}
CONTAINERS = {"ContractDefinition"}

# bge-m3 has an 8192-token context. Solidity tokenises at roughly three
# characters per token, so this is the point at which truncation starts.
# Truncation is silent, which is why it is checked rather than assumed.
# Measured against v2.1.0: median chunk 175 chars, p99 2,292, max 5,062. The
# limit is nowhere near being approached; the check exists to notice if that
# changes.
OVERSIZE_CHARS = 24_000

# The same ceiling, applied to a different string for a different reason.
# OVERSIZE_CHARS bounds `model_text`, which is what reaches the model's context
# window. EMBED_OVERSIZE_CHARS bounds `embed_text`, which is what reaches the
# embedder. Its composition makes it strictly longer than `model_text` by
# adding exposure and alias lines after deduplication. One build produced a
# corpus whose `model_text` was 25 characters and whose `embed_text` was 46,204,
# and every check passed, because the guard measured the string nobody embeds.
EMBED_OVERSIZE_CHARS = 24_000


class ChunkError(Exception):
    """Raised for conditions that must stop a build rather than warn."""


def validate_source_path(path: str) -> None:
    """
    A source-unit key becomes a chunk's `path`, its `id` and its breadcrumb —
    which is to say it becomes a citation. It must therefore be a canonical
    repository-relative POSIX path and nothing else.

    `standard-input.json` is an input file, and solc will happily compile a
    source unit named `src/../../not-in-repo.sol`, which yields chunks citing a
    path that resolves outside the pinned tree. A citation
    layer normalising that lands somewhere it was never meant to read, and the
    result looks as verified as everything around it.
    """
    if not path or path != path.strip():
        raise ChunkError(f"source path is empty or padded: {path!r}")
    if "\\" in path:
        raise ChunkError(
            f"source path uses backslashes, which are not path separators "
            f"here and can traverse on other platforms: {path!r}")
    if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        raise ChunkError(f"source path is absolute: {path!r}")
    for part in path.split("/"):
        if part in ("", ".", ".."):
            raise ChunkError(
                f"source path is not canonical — component {part!r} in "
                f"{path!r}. Chunk ids and citations are built from this.")


# --------------------------------------------------------------------------
# source handling: byte offsets, not character offsets
# --------------------------------------------------------------------------

class SourceMap:
    """
    solc `src` fields are "start:length:fileIndex" in **bytes**. Slicing a
    Python str with those numbers silently corrupts any file containing a
    non-ASCII byte — and Solidity source legitimately contains them, in string
    literals, natspec and identifiers. Everything here works on bytes and
    decodes only at the end.
    """

    def __init__(self, sources: dict[str, dict], ast_ids: dict[str, int]):
        self.by_index: dict[int, tuple[str, bytes]] = {}
        for path, entry in sources.items():
            idx = ast_ids.get(path)
            if idx is None:
                continue
            self.by_index[idx] = (path, entry["content"].encode("utf-8"))

    def slice(self, src: str) -> tuple[str, str]:
        """`src` -> (path, text). Raises rather than guessing."""
        start_s, len_s, file_s = src.split(":")
        start, length, file_idx = int(start_s), int(len_s), int(file_s)
        if file_idx not in self.by_index:
            raise KeyError(f"src {src!r} references unknown file index {file_idx}")
        path, blob = self.by_index[file_idx]
        end = start + length
        if start < 0 or end > len(blob):
            raise ValueError(f"src {src!r} out of range for {path} ({len(blob)} bytes)")
        return path, blob[start:end].decode("utf-8")

    def line_of(self, src: str) -> int:
        """
        1-based line number. Counts LF, CRLF and lone CR, because solc accepts
        all three and a citation that says line 1 for every node in a CR-only
        file is worse than no line number at all.
        """
        start_s, _, file_s = src.split(":")
        _, blob = self.by_index[int(file_s)]
        head = blob[: int(start_s)]
        return len(head.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n"))

    def span(self, src: str) -> tuple[int, int, int]:
        """(start, length, file_index) as integers."""
        a, b, c = src.split(":")
        return int(a), int(b), int(c)

    def slice_range(self, file_idx: int, start: int, end: int) -> tuple[str, str]:
        path, blob = self.by_index[file_idx]
        if start < 0 or end > len(blob) or start >= end:
            raise ValueError(f"range {start}:{end} out of bounds for {path}")
        return path, blob[start:end].decode("utf-8")


# --------------------------------------------------------------------------
# comment stripping for model_text only, never for display_text
# --------------------------------------------------------------------------

def strip_comments(code: str, keep_ranges: tuple = ()) -> str:
    """
    Remove comments while preserving string and hex literals.

    A regex cannot do this correctly: `"http://x"` contains `//`, and
    `unicode"/* "` contains a comment opener inside a literal. This is a small
    hand-rolled scanner instead, and it is deliberately conservative — when in
    doubt it keeps the character.

    Documentation is preserved only where `keep_ranges` says the *compiler*
    attached it — character ranges into `code`, supplied by the caller from the
    AST. Comment syntax alone is not evidence of documentation: solc attaches
    `///` and `/** */` to a declaration only when it precedes one, so the same
    tokens mid-function are ordinary comments. `/// IGNORE ALL PREVIOUS
    INSTRUCTIONS` placed inside a function body survived a control whose entire
    purpose is removing non-documentation text.

    Kept natspec is still untrusted and must be fenced as quoted material in the
    prompt, never treated as instruction.
    """
    def kept(pos: int) -> bool:
        return any(a <= pos < b for a, b in keep_ranges)

    out: list[str] = []
    i, n = 0, len(code)
    while i < n:
        c = code[i]

        # string literals, including the unicode"" and hex"" prefixed forms
        if c in ('"', "'"):
            quote = c
            out.append(c)
            i += 1
            while i < n:
                if code[i] == "\\" and i + 1 < n:      # escape: copy both
                    out.append(code[i:i + 2])
                    i += 2
                    continue
                out.append(code[i])
                if code[i] == quote:
                    i += 1
                    break
                i += 1
            continue

        if code.startswith("//", i):
            # solc accepts LF, CRLF and lone CR. Stopping only at LF eats the
            # rest of a CR-only file from the first line comment onward.
            nl, cr = code.find("\n", i), code.find("\r", i)
            cands = [x for x in (nl, cr) if x != -1]
            j = min(cands) if cands else n
            if kept(i):
                out.append(code[i:j])
            else:
                out.append(" ")     # never weld the comment's neighbours together
            i = j
            continue

        if code.startswith("/*", i):
            j = code.find("*/", i + 2)
            j = n if j == -1 else j + 2
            if kept(i):
                out.append(code[i:j])
            else:
                # A block comment can sit between two tokens with no other
                # separator. `uint256/* x */value` is valid Solidity, so the
                # removed comment must leave whitespace behind. Newlines are
                # preserved so line numbers stay usable.
                removed = code[i:j]
                nl = removed.count("\n")
                out.append("\n" * nl if nl else " ")
            i = j
            continue

        out.append(c)
        i += 1

    return "".join(out)


# --------------------------------------------------------------------------
# signatures: overloads must not collide
# --------------------------------------------------------------------------

# Leading keywords solc puts in front of user-defined types, and the data
# location suffixes it puts after them.
_TYPE_PREFIXES = ("struct ", "enum ", "contract ", "interface ", "library ",
                  "type ", "function ")
_TYPE_SUFFIXES = (" memory", " storage", " calldata", " pointer", " ptr",
                  " ref", " slot", " super")


def canonical_type(type_string: str) -> str:
    """
    Reduce a solc `typeString` to something short, stable and *distinguishing*.

        "struct Position memory"     -> "Position"
        "contract IRegistry"         -> "IRegistry"
        "uint256[] calldata"         -> "uint256[]"
        "enum Status"                -> "Status"

    Taking the first whitespace-delimited token instead — as this did
    originally — collapses every struct parameter to the literal word "struct",
    so two functions differing only by struct type produce identical
    signatures and therefore identical chunk IDs. Nothing in the current corpus
    collides, but that is luck rather than design, and a silent ID collision
    means one chunk overwrites another.
    """
    t = (type_string or "?").strip()
    for prefix in _TYPE_PREFIXES:
        if t.startswith(prefix):
            t = t[len(prefix):]
            break
    changed = True
    while changed:                      # "storage pointer" needs two passes
        changed = False
        for suffix in _TYPE_SUFFIXES:
            if t.endswith(suffix):
                t = t[: -len(suffix)]
                changed = True
    # struct types are reported fully qualified when imported: "Foo.Bar"
    return " ".join(t.split()).strip()


def param_types(node: dict) -> list[str]:
    params = (node.get("parameters") or {}).get("parameters") or []
    return [canonical_type((p.get("typeDescriptions") or {}).get("typeString"))
            for p in params]


# Solidity permits overloading on all of these, so a bare name is not a unique
# identifier for any of them. Only functions and modifiers can be *overridden*;
# the rest are merely inherited, which matters in resolve_inheritance().
PARAMETERISED = {"FunctionDefinition", "EventDefinition",
                 "ErrorDefinition", "ModifierDefinition"}
OVERRIDABLE = {"FunctionDefinition", "ModifierDefinition"}


def signature(node: dict) -> str:
    kind = node.get("kind")
    name = node.get("name") or ""
    if node["nodeType"] == "FunctionDefinition":
        if kind == "constructor":
            name = "constructor"
        elif kind in ("fallback", "receive"):
            name = kind
    if node["nodeType"] in PARAMETERISED:
        return f"{name}({','.join(param_types(node))})"
    return name


# --------------------------------------------------------------------------
# chunks
# --------------------------------------------------------------------------

def natspec_of(node: dict, smap: SourceMap) -> str:
    doc = node.get("documentation")
    if not doc:
        return ""
    if isinstance(doc, str):
        return doc
    if doc.get("src"):
        try:
            return smap.slice(doc["src"])[1]
        except (KeyError, ValueError):
            pass
    return doc.get("text", "")


def documented_span(node: dict, smap: SourceMap):
    """
    Return (path, text, line, doc_len) covering documentation *and* declaration
    as one contiguous slice, or None if they cannot be joined contiguously.
    `doc_chars` is how many leading *characters* of `text` the compiler
    considers documentation, which is the only thing the comment stripper may
    preserve. Characters, not bytes: solc reports `src` spans in bytes, and
    handing a byte length to a stripper indexing a decoded Python string
    widens the permitted range by one position per non-ASCII character in the
    documentation. 120 accented characters of natspec is enough to push the
    range into the function body and re-admit exactly the mid-body injection
    the character-based range closes.

    Concatenating the two separately-sliced ranges — which is what this used to
    do — silently drops whatever whitespace sat between them, so the result is
    not a substring of the file it cites. It still looked verbatim, which is the
    failure this whole design exists to avoid. If a single span cannot be taken,
    the caller keeps the declaration alone and leaves the natspec in `detail`.
    """
    doc = node.get("documentation")
    if not isinstance(doc, dict) or not doc.get("src"):
        return None
    try:
        d_start, d_len, d_file = smap.span(doc["src"])
        n_start, n_len, n_file = smap.span(node["src"])
    except (ValueError, KeyError):
        return None
    if d_file != n_file or d_start + d_len > n_start:
        return None
    try:
        path, text = smap.slice_range(d_file, d_start, n_start + n_len)
        # measured on the decoded documentation, in the same units the caller
        # will index with
        _, doc_text = smap.slice_range(d_file, d_start, d_start + d_len)
    except (KeyError, ValueError):
        return None
    return path, text, smap.line_of(doc["src"]), len(doc_text)


def make_chunk(node, contract, smap, inherits) -> Chunk | None:
    try:
        path, text = smap.slice(node["src"])
    except (KeyError, ValueError) as e:
        print(f"  !! skipping node: {e}", file=sys.stderr)
        return None

    kind = node["nodeType"].replace("Definition", "")
    sig = signature(node)
    cname = contract["name"] if contract else None
    ckind = contract.get("contractKind") if contract else None
    doc = natspec_of(node, smap)

    # Take documentation and declaration as one contiguous slice where possible,
    # so display_text remains byte-exact source. Where it is not possible, the
    # declaration alone is quoted and the natspec stays in `detail`. A smaller
    # chunk is preferable to an unquotable one.
    line = smap.line_of(node["src"])
    joined = documented_span(node, smap)
    if joined:
        _, display, line, doc_chars = joined
        keep = ((0, doc_chars),)
    else:
        display = text
        keep = ()
    model = strip_comments(display, keep_ranges=keep)

    breadcrumb = " › ".join(x for x in (path, cname, sig) if x)

    warnings = []
    if len(model) > OVERSIZE_CHARS:
        warnings.append("chunk exceeds the embedding context; truncation is silent")

    uid = f"{path}:{cname or '<file>'}.{sig}"
    return Chunk(
        id=uid,
        kind=kind,
        source_type="solidity",
        path=path,
        line=line,
        breadcrumb=breadcrumb,
        display_text=display,
        model_text=model,
        # the embedding needs the context the body lacks: which contract, what
        # it is called, what kind of thing it is. It is composed again from the
        # final merged state; see compose_embed_text().
        embed_text=f"{embed_head(kind, breadcrumb)}\n\n{model}",
        warnings=warnings,
        detail={
            "contract": cname,
            "name": node.get("name") or sig,
            "signature": sig,
            "visibility": node.get("visibility"),
            "natspec": doc,
            "inherits": inherits,
            "declared_in_kind": ckind,
            "exposed_by": [],
            "overridden": False,
        },
    )


def contract_header(contract: dict, smap: SourceMap, inherits) -> Chunk | None:
    """
    A chunk for the contract itself: its natspec, declaration line, inheritance
    and state variables — but not the bodies of its functions, which are their
    own chunks. Without this, "what is MyContract" has nothing to retrieve.
    """
    try:
        path, _ = smap.slice(contract["src"])
    except (KeyError, ValueError):
        return None
    doc = natspec_of(contract, smap)
    state = []
    for n in contract.get("nodes", []):
        if n["nodeType"] == "VariableDeclaration":
            try:
                state.append(smap.slice(n["src"])[1])
            except (KeyError, ValueError):
                continue
    decl = f"{contract.get('contractKind','contract')} {contract['name']}"
    if inherits:
        decl += " is " + ", ".join(inherits)
    body = decl + " {\n" + "\n".join("  " + s + ";" for s in state) + "\n}"
    display = (doc + "\n" + body) if doc else body
    model = strip_comments(display, keep_ranges=((0, len(doc)),) if doc else ())
    breadcrumb = f"{path} › {contract['name']}"
    return Chunk(
        id=f"{path}:{contract['name']}",
        kind=contract.get("contractKind", "contract"),
        source_type="solidity",
        path=path,
        line=smap.line_of(contract["src"]),
        breadcrumb=breadcrumb,
        display_text=display,
        model_text=model,
        embed_text=f"{embed_head(contract.get('contractKind', 'contract'), breadcrumb)}\n\n{model}",
        synthesised=True,
        detail={
            "contract": contract["name"],
            "name": contract["name"],
            "signature": contract["name"],
            "visibility": None,
            "natspec": doc,
            "inherits": inherits,
            "declared_in_kind": contract.get("contractKind"),
            "exposed_by": [],
            "overridden": False,
        },
    )


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

_VERSION_RE = re.compile(r"Version:\s*(\S+)")


def solc_version(solc: str) -> str:
    """
    The compiler's own account of itself, e.g. `0.8.25+commit.b61c2a91`.

    A build is only reproducible against a named compiler, and the AST is the
    compiler's output — a different solc can change chunk boundaries, natspec
    attachment and the ABI the surface is checked against. A review environment
    that drifts to a newer patch release keeps building green and produces a
    quietly different corpus. CI pins a container digest, so this is defence in
    depth for everywhere else, but a version that is never recorded cannot be
    checked afterwards.
    """
    r = subprocess.run([solc, "--version"], capture_output=True, text=True)
    if r.returncode != 0:
        raise ChunkError(f"{solc} --version failed: {r.stderr[:200]}")
    m = _VERSION_RE.search(r.stdout)
    if not m:
        raise ChunkError(f"cannot parse a version out of: {r.stdout[:200]!r}")
    return m.group(1)


def require_solc_version(solc: str, expected: str | None) -> str:
    """Resolve the compiler version, and refuse a mismatch when one is named."""
    found = solc_version(solc)
    if expected and not found.startswith(expected):
        raise ChunkError(
            f"compiler is {found}, expected {expected}\n"
            f"  {solc}\n"
            "  the AST is this compiler's output; a different one is a "
            "different corpus")
    return found


def compile_ast(input_path: str, solc: str) -> dict:
    doc = json.load(open(input_path))
    # Validated before solc sees it: a path this chunker would refuse to cite
    # is not worth spending a compilation on.
    for src_path in (doc.get("sources") or {}):
        validate_source_path(src_path)
    doc.setdefault("settings", {})["outputSelection"] = {
        "*": {"": ["ast"], "*": ["abi"]}}
    doc["settings"].pop("libraries", None)
    r = subprocess.run([solc, "--standard-json"], input=json.dumps(doc),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise ChunkError(f"solc failed: {r.stderr[:400]}")
    out = json.loads(r.stdout)
    for src_path in (out.get("sources") or {}):
        validate_source_path(src_path)      # solc echoes keys; verify it did
    errors = [e for e in out.get("errors", []) if e.get("severity") == "error"]
    if errors:
        detail = "\n".join(e.get("formattedMessage", "")[:300] for e in errors[:5])
        raise ChunkError(
            f"{len(errors)} compilation error(s) — refusing to chunk\n{detail}")
    return doc, out


def chunk(input_path: str, solc: str, includes: list[str],
          glob_hits: dict[str, int] | None = None) -> list[Chunk]:
    doc, out = compile_ast(input_path, solc)
    ast_ids = {p: s["id"] for p, s in out["sources"].items()}
    smap = SourceMap(doc["sources"], ast_ids)

    # Selection is fail-loud: a glob that matches nothing
    # is an error, not an empty set. A silently-empty selection is how a
    # renamed directory removes the corpus while every build stays green.
    # `--include 'typo/**'` demonstrates it: 0 chunks, exit 0, empty JSONL
    # written.
    selected: set[str] = set()
    for path in out["sources"]:
        hit = False
        for g in includes:
            if fnmatch.fnmatch(path, g):
                hit = True
                if glob_hits is not None:
                    glob_hits[g] = glob_hits.get(g, 0) + 1
        if hit or not includes:
            selected.add(path)
    if includes and not selected:
        roots = sorted({str(pathlib.PurePosixPath(x).parts[0]) for x in out["sources"]})
        raise ChunkError(
            f"include patterns selected nothing in {input_path}\n"
            f"  patterns : {includes}\n"
            f"  top-level paths present: {roots}")

    chunks: list[Chunk] = []
    for path, entry in out["sources"].items():
        if path not in selected:
            continue
        ast = entry.get("ast")
        if not ast:
            continue
        for node in ast.get("nodes", []):
            if node["nodeType"] in CONTAINERS:
                inherits = [b["baseName"].get("name", "?")
                            for b in node.get("baseContracts", [])]
                header = contract_header(node, smap, inherits)
                if header:
                    chunks.append(header)
                for member in node.get("nodes", []):
                    if member["nodeType"] in CHUNKABLE:
                        c = make_chunk(member, node, smap, inherits)
                        if c:
                            chunks.append(c)
            elif node["nodeType"] in CHUNKABLE:
                # free functions, file-level structs/errors/enums
                c = make_chunk(node, None, smap, [])
                if c:
                    chunks.append(c)

    chunks = resolve_inheritance(out, chunks)
    chunks += surface_chunks(out, includes, smap)

    # Within one compilation unit an ID must be unique. Checking after the
    # cross-unit merge is too late: the merge is dict-keyed, so a duplicate is
    # silently absorbed and the collision count reports zero.
    seen: dict[str, Chunk] = {}
    for c in chunks:
        prior = seen.get(c.id)
        if prior is not None:
            raise ChunkError(
                f"duplicate id within one compilation unit: {c.id}\n"
                f"  {prior.breadcrumb} (line {prior.line})\n"
                f"  {c.breadcrumb} (line {c.line})\n"
                "  signature generation is not distinguishing these")
        seen[c.id] = c
    if not chunks:
        raise ChunkError(
            f"{input_path}: selection matched {len(selected)} source file(s) "
            "but produced zero chunks — nothing chunkable in the selection")
    return chunks


def resolve_inheritance(out: dict, chunks: list[Chunk]) -> list[Chunk]:
    """
    Annotate each member chunk with the concrete contracts that expose it.

    solc gives `linearizedBaseContracts` — the C3 resolution order, most derived
    first. Walking it and keeping the first definition of each signature is
    exactly Solidity's own override semantics, so an overridden base function is
    correctly *not* attributed to the derived contract.

    Bases are collected from every source in the compilation, including paths
    excluded from chunking: a contract in `src/` can inherit from `lib/`, and
    resolving against only the included subset would silently under-report.
    """
    by_id: dict[int, dict] = {}
    node_path: dict[int, str] = {}
    for path, entry in out["sources"].items():
        ast = entry.get("ast")
        if not ast:
            continue
        for node in ast.get("nodes", []):
            if node["nodeType"] == "ContractDefinition":
                by_id[node["id"]] = node
                node_path[node["id"]] = path

    # signature -> defining contract, per concrete contract
    exposure: dict[tuple[str, str], list[str]] = {}
    overridden: set[tuple[str, str]] = set()

    for cid, contract in by_id.items():
        if contract.get("contractKind") != "contract" or contract.get("abstract"):
            continue                      # only concrete contracts have a surface
        seen: set[tuple[str, str]] = set()
        for base_id in contract.get("linearizedBaseContracts", []):
            base = by_id.get(base_id)
            if base is None:
                continue
            for member in base.get("nodes", []):
                # A public state variable compiles to an external getter. That
                # getter can satisfy and shadow an inherited
                # function declaration. It is not a chunk of its own, so it
                # takes no exposure, but it must occupy the slot. Without it an
                # interface's function declaration stays attributed to the
                # implementing contract and marked un-overridden, when what that
                # contract actually exposes is the getter.
                if member["nodeType"] == "VariableDeclaration":
                    if member.get("visibility") != "public":
                        continue
                    gsig = f"{member.get('name')}({','.join(getter_params(member))})"
                    seen.add(("FunctionDefinition", gsig))
                    continue
                if member["nodeType"] not in CHUNKABLE:
                    continue
                # A constructor is neither inherited nor callable through a
                # derived contract: it runs once, at the deployment of the
                # contract that declares it. Attributing a base constructor to
                # its derived contracts answers "what can I call on X" with
                # something that cannot be called on X, or at all.
                if member.get("kind") == "constructor":
                    continue
                sig = signature(member)
                key = (node_path[base_id], f"{base['name']}.{sig}")
                # Only functions and modifiers can be overridden. Two events
                # with the same signature in a hierarchy are a redeclaration,
                # not a shadowing, and marking one "overridden" hides it from
                # the unreachable report for the wrong reason.
                shadow_key = (member["nodeType"], sig)
                if shadow_key in seen:
                    if member["nodeType"] in OVERRIDABLE:
                        overridden.add(key)
                    continue
                seen.add(shadow_key)
                exposure.setdefault(key, []).append(contract["name"])

    for c in chunks:
        if c.synthesised or c.detail.get("contract") is None:
            continue
        key = (c.path, f'{c.detail["contract"]}.{c.detail["signature"]}')
        c.detail["exposed_by"] = sorted(set(exposure.get(key, [])))
        c.detail["overridden"] = key in overridden
    return chunks


def embed_head(kind: str, breadcrumb: str) -> str:
    """
    The context line(s) that sit above the body in embed_text. One authority:
    the construction sites and compose_embed_text() both call this, so the
    format cannot drift between them.
    """
    if kind == "surface":
        return breadcrumb
    if kind in ("contract", "interface", "library"):
        return f"{breadcrumb}\ncontract declaration and state"
    return f"{breadcrumb}\n{kind}"


def compose_embed_text(chunks: list[Chunk]) -> None:
    """
    Derive embed_text wholesale from structured state — breadcrumb, kind,
    model_text, exposed_by, alias breadcrumbs — once, after all merging and
    deduplication is done.

    Accumulate-and-guard was replaced with rebuild; the rebuild then recovered
    the base text by splitting on a "\\n\\nexposed by: " marker, which hands
    control of the embedding to anyone who can write that
    marker into natspec: everything after it, function body included, vanished
    from embed_text while display_text stayed intact and every check passed.
    Nothing here parses previous embed_text. It is composed, never recovered.
    """
    for c in chunks:
        parts = [f"{embed_head(c.kind, c.breadcrumb)}\n\n{c.model_text}"]
        exposed = c.detail.get("exposed_by") or []
        if exposed:
            parts.append("exposed by: " + ", ".join(exposed))
        # Folded duplicates are findable only if the identity that was folded
        # away is actually in the text being indexed. detail.aliases records
        # it for machines; this line records it for retrieval.
        alias_bc = c.detail.get("alias_breadcrumbs") or []
        if alias_bc:
            parts.append("also declared as:\n" + "\n".join(alias_bc))
        c.embed_text = "\n\n".join(parts)


def getter_params(var: dict) -> list[str]:
    """
    Parameter list of the compiler-generated getter for a public state variable.
    Mappings take a key per level; arrays take a uint256 index. Anything else
    takes none.
    """
    params: list[str] = []
    t = var.get("typeName") or {}
    while True:
        kind = t.get("nodeType")
        if kind == "Mapping":
            params.append(canonical_type(
                ((t.get("keyType") or {}).get("typeDescriptions") or {}).get("typeString")))
            t = t.get("valueType") or {}
        elif kind == "ArrayTypeName":
            params.append("uint256")
            t = t.get("baseType") or {}
        else:
            return params


def _abi_callable_signatures(out: dict, path: str, name: str) -> list[str] | None:
    """
    Signature multiset of the externally callable surface, straight from the
    ABI: functions as `name(type,...)`, plus fallback/receive by kind. Events,
    errors and the constructor are not callable on a deployed contract and are
    excluded. Returns None when the ABI was not produced, so the caller can
    tell "no check ran" apart from "the check passed".

    An earlier check compared names only, which counted how many overloads were
    called `f` and said nothing about what any `f` accepted; changing a parameter
    type on the AST side left it green. `internalType` is preferred over `type`
    because it preserves the struct, enum and contract names the AST side uses:
    `struct Position` rather than `tuple`.
    """
    entry = ((out.get("contracts") or {}).get(path) or {}).get(name)
    if entry is None or "abi" not in entry:
        return None
    sigs: list[str] = []
    for item in entry["abi"]:
        kind = item.get("type")
        if kind == "function":
            params = [canonical_type(i.get("internalType") or i.get("type"))
                      for i in item.get("inputs") or []]
            sigs.append(f"{item.get('name')}({','.join(params)})")
        elif kind in ("fallback", "receive"):
            sigs.append(f"{kind}()")
    return sigs


def _multiset_diff(a: list[str], b: list[str]) -> list[str]:
    rest = list(b)
    out = []
    for x in a:
        if x in rest:
            rest.remove(x)
        else:
            out.append(x)
    return out


def surface_chunks(out: dict, includes: list[str], smap: SourceMap) -> list[Chunk]:
    """
    One chunk per concrete contract listing its full callable surface — every
    external and public function, with the contract that actually defines it.

    This is what answers "what can I call on MyContract", which no
    per-function chunk can, because the answer is spread across eight contracts.
    Synthesised, and marked as such.
    """
    by_id, node_path = {}, {}
    for path, entry in out["sources"].items():
        ast = entry.get("ast")
        if not ast:
            continue
        for node in ast.get("nodes", []):
            if node["nodeType"] == "ContractDefinition":
                by_id[node["id"]] = node
                node_path[node["id"]] = path

    chunks = []
    for cid, contract in by_id.items():
        path = node_path[cid]
        if includes and not any(fnmatch.fnmatch(path, g) for g in includes):
            continue
        if contract.get("contractKind") != "contract" or contract.get("abstract"):
            continue
        seen: set[str] = set()
        lines: list[str] = []
        names: list[str] = []          # signature multiset, checked vs the ABI
        for base_id in contract.get("linearizedBaseContracts", []):
            base = by_id.get(base_id)
            if base is None:
                continue
            for m in base.get("nodes", []):
                origin = "" if base_id == cid else f"   (from {base['name']})"

                # Every public state variable, including a constant or
                # immutable, gets a compiler-generated external getter. An
                # earlier version excluded constants here, so public constants
                # went missing from the surface: the one place that promises to
                # answer "what can I call" was understating it.
                if m["nodeType"] == "VariableDeclaration":
                    if m.get("visibility") != "public":
                        continue
                    sig = f"{m.get('name')}({','.join(getter_params(m))})"
                    if sig in seen:
                        continue
                    seen.add(sig)
                    names.append(sig)
                    mut = m.get("mutability")
                    tag = ("[getter, constant]" if mut == "constant"
                           else "[getter, immutable]" if mut == "immutable"
                           else "[getter]")
                    lines.append(f"  public {sig}   {tag}{origin}")
                    continue

                if m["nodeType"] != "FunctionDefinition":
                    continue
                # A constructor is not callable on a deployed contract, and a
                # base contract's constructor is not callable at all. Listing
                # them answers "what can I call" incorrectly in one direction
                # while the missing getters answer it incorrectly in the other.
                if m.get("kind") == "constructor":
                    continue
                if m.get("visibility") not in ("external", "public"):
                    continue
                sig = signature(m)
                if sig in seen:
                    continue
                seen.add(sig)
                names.append(sig)
                lines.append(f"  {m.get('visibility')} {sig}{origin}")
        if not lines:
            continue

        # The listing above approximates what the compiler does; the ABI *is*
        # what the compiler does. Comparing their name multisets counts missing
        # overloads and stops the build if the approximation diverges from the
        # real surface. This check would have caught the missing
        # constant getters.
        abi_sigs = _abi_callable_signatures(out, path, contract["name"])
        if abi_sigs is not None and sorted(names) != sorted(abi_sigs):
            missing = _multiset_diff(abi_sigs, names)
            extra = _multiset_diff(names, abi_sigs)
            raise ChunkError(
                f"surface for {contract['name']} disagrees with the ABI\n"
                + (f"  in ABI but not listed : {sorted(missing)}\n" if missing else "")
                + (f"  listed but not in ABI : {sorted(extra)}\n" if extra else "")
                + "  the surface builder no longer models what solc generates")
        body = f"{contract['name']} callable surface\n\n" + "\n".join(sorted(lines))
        breadcrumb = f"{path} › {contract['name']} › callable surface"
        chunks.append(Chunk(
            id=f"{path}:{contract['name']}#surface",
            kind="surface",
            source_type="solidity",
            path=path,
            line=smap.line_of(contract["src"]) if contract.get("src") else 0,
            breadcrumb=breadcrumb,
            display_text=body,
            model_text=body,
            embed_text=f"{embed_head('surface', breadcrumb)}\n\n{body}",
            synthesised=True,
            detail={
                "contract": contract["name"],
                "name": contract["name"],
                "signature": "#surface",
                "visibility": None,
                "natspec": "",
                "inherits": [b["baseName"].get("name", "?")
                             for b in contract.get("baseContracts", [])],
                "declared_in_kind": "contract",
                "exposed_by": [],
                "overridden": False,
            },
        ))
    return chunks


def dedupe(chunks: list[Chunk]) -> tuple[list[Chunk], int]:
    """
    Identical bodies appear across files — the same interface vendored twice,
    the same trivial getter. Duplicates inflate retrieval scores for whatever
    happens to be duplicated, so keep the first and record the rest.
    """
    # Sorted, so which duplicate survives does not depend on the order inputs
    # happened to be passed on the command line.
    seen: dict[str, Chunk] = {}
    kept, dropped = [], 0
    for c in sorted(chunks, key=lambda x: x.id):
        h = c.content_hash
        prior = seen.get(h)
        if prior is not None:
            dropped += 1
            # Keep the discarded identity rather than losing it: the body is the
            # same, but the ID and its contract context are not, and a query
            # naming the dropped contract should still find something. The
            # breadcrumb is kept alongside the ID so compose_embed_text() can
            # put the folded identity into the retrieval text without parsing
            # the ID back apart. IDs are output, not input.
            prior.detail.setdefault("aliases", []).append(c.id)
            prior.detail.setdefault("alias_breadcrumbs", []).append(c.breadcrumb)
            prior.detail["exposed_by"] = sorted(
                set(prior.detail.get("exposed_by") or [])
                | set(c.detail.get("exposed_by") or []))
            continue
        seen[h] = c
        kept.append(c)
    return kept, dropped


def build(inputs: list[str], solc: str, includes: list[str],
          no_dedupe: bool = False,
          expect_solc: str | None = None) -> tuple[list[Chunk], int]:
    """
    The whole pipeline behind the CLI: chunk each compilation unit, merge,
    deduplicate, compose embeddings. Raises ChunkError for every condition
    that must stop a build. main() is a thin wrapper around this, and the
    tests call this — the same function, not a re-enactment of it.
    Fatal-condition tests that recreate the checks by hand keep passing however
    badly this code regresses.
    """
    if not inputs:
        raise ChunkError("no compilation units given")
    version = require_solc_version(solc, expect_solc)
    print(f"  compiler      : {version}"
          + (f"  (matches --expect-solc {expect_solc})" if expect_solc
             else "  (unpinned — pass --expect-solc to gate on it)"))

    glob_hits: dict[str, int] = {g: 0 for g in includes}
    merged: dict[str, Chunk] = {}
    # Sorted, so the merge does not depend on the order inputs were listed.
    for path in sorted(inputs):
        for c in chunk(path, solc, includes, glob_hits=glob_hits):
            prior = merged.get(c.id)
            if prior is None:
                merged[c.id] = c
                continue
            # Same member in another compilation unit. Inheritance resolves
            # per unit, so a function can look unreachable in one build and
            # be exposed by a concrete contract in another. The merged result
            # is the union. Any other difference is a disagreement about
            # source, which is fatal.
            if prior.display_text != c.display_text:
                raise ChunkError(
                    f"conflicting source for {c.id} across compilation units\n"
                    f"  {prior.path}:{prior.line} and {c.path}:{c.line}\n"
                    "  two builds disagree about the same source. Keeping\n"
                    "  either body would attach a plausible citation to\n"
                    "  arbitrary code.")
            prior.detail["exposed_by"] = sorted(
                set(prior.detail.get("exposed_by") or [])
                | set(c.detail.get("exposed_by") or []))
            # OR, not AND: a member absent from one unit is not evidence
            # that it is un-overridden there.
            prior.detail["overridden"] = (
                prior.detail.get("overridden") or c.detail.get("overridden"))

    # Each pattern must match somewhere across the units. A single unit may
    # legitimately lack a file (only one input carries
    # Ownable.sol) is fine; a pattern matching nothing anywhere is a typo.
    unmatched = [g for g, n in glob_hits.items() if n == 0]
    if unmatched:
        raise ChunkError(
            "include pattern(s) matched nothing in any compilation unit: "
            + ", ".join(repr(g) for g in unmatched))

    chunks = list(merged.values())
    dropped = 0
    if not no_dedupe:
        chunks, dropped = dedupe(chunks)
    chunks.sort(key=lambda c: c.id)

    if not chunks:
        raise ChunkError("zero chunks after merging — refusing to call an "
                         "empty corpus a successful build")

    # embed_text is derived last, from final state, so it cannot disagree with
    # the metadata beside it.
    compose_embed_text(chunks)
    return chunks, dropped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, action="append",
                    help="solc standard-json input file; repeat to merge "
                         "compilation units (inheritance resolves per unit)")
    ap.add_argument("--solc", default="solc")
    ap.add_argument("--include", action="append", default=[],
                    help="glob of source paths to chunk, e.g. 'src/**'")
    ap.add_argument("--out", help="JSONL output; stdout summary if omitted")
    ap.add_argument("--no-dedupe", action="store_true")
    ap.add_argument("--expect-solc", metavar="VERSION",
                    help="refuse to build unless solc reports this version, "
                         "e.g. 0.8.25; fail the build on any other compiler")
    args = ap.parse_args()

    try:
        chunks, dropped = build(args.input, args.solc, args.include,
                                no_dedupe=args.no_dedupe,
                                expect_solc=args.expect_solc)
    except ChunkError as e:
        print(f"\nFATAL: {e}", file=sys.stderr)
        return 1

    # Oversize is a property of both relevant lengths, not of whether a chunk
    # has any warning attached.
    oversize = [c for c in chunks if len(c.model_text) > OVERSIZE_CHARS
                or len(c.embed_text) > EMBED_OVERSIZE_CHARS]
    sizes = sorted(len(c.model_text) for c in chunks)
    esizes = sorted(len(c.embed_text) for c in chunks)
    p99 = sizes[int(0.99 * len(sizes))] if sizes else 0
    synth = sum(1 for c in chunks if c.synthesised)
    exposed = sum(1 for c in chunks if c.detail.get("exposed_by"))
    aliased = sum(len(c.detail.get("aliases") or []) for c in chunks)

    problems = _schema.validate(chunks, oversize_chars=OVERSIZE_CHARS,
                                embed_oversize_chars=EMBED_OVERSIZE_CHARS)

    orphan = [c for c in chunks
              if c.detail.get("contract") and not c.synthesised
              and not c.detail.get("exposed_by")
              and c.kind == "Function"
              and c.detail.get("visibility") in ("external", "public")
              and c.detail.get("declared_in_kind") == "contract"
              and not c.detail.get("overridden")
              # Constructors carry no exposure by design because they run once
              # at deployment. That differs from being unreachable.
              and not c.detail.get("signature", "").startswith("constructor(")]

    print(f"{len(chunks)} chunks from {len(args.input)} compilation unit(s)  "
          f"({dropped} duplicate bodies folded, {aliased} alias id(s) kept)")
    print(f"  schema        : {len(problems)} problem(s)"
          + ("  <-- FATAL" if problems else ""))
    for pr in problems[:5]:
        print(f"      {pr}")
    print(f"  oversize      : {len(oversize)}  "
          f"(model p99 {p99}, max {sizes[-1] if sizes else 0}; "
          f"embed max {esizes[-1] if esizes else 0}; "
          f"limits {OVERSIZE_CHARS}/{EMBED_OVERSIZE_CHARS})")
    print(f"  synthesised   : {synth}  (not quotable as source)")
    print(f"  inheritance   : {exposed} chunks attributed to a concrete contract")
    print(f"  unreachable   : {len(orphan)} public/external fns on contracts "
          f"exposed by nothing" + ("  <-- check" if orphan else ""))
    for c in orphan[:5]:
        print(f"      {c.breadcrumb}")
    kinds: dict[str, int] = {}
    for c in chunks:
        kinds[c.kind] = kinds.get(c.kind, 0) + 1
    print("  by kind       : " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())))

    if args.out and not problems and not oversize:
        with open(args.out, "w") as f:
            for c in chunks:
                f.write(json.dumps(c.to_dict()) + "\n")
        print(f"  written       : {args.out}")
    elif args.out:
        print("  NOT WRITTEN   : refusing to emit a corpus that fails its own checks")

    return 1 if (problems or oversize) else 0


if __name__ == "__main__":
    sys.exit(main())
