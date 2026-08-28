#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""
Lemma shared schema

The one chunk shape. Every chunker emits this; the index, the retriever and the
citation layer all read this and nothing else.

The shared schema keeps the retrieval layer independent of chunker-specific
output shapes and avoids source-type branches for core retrieval behavior.

DESIGN

Fields are divided into three tiers with distinct ownership:

  Core: every chunk has it, and the retriever may rely on it.
  Provenance: §4 of the ingestion manifest. What makes an answer citable and
                a build replayable. Filled by the pipeline, not the chunker.
  detail: everything source-specific, in a dict. Solidity's `exposed_by`
                has no markdown analogue and markdown's `anchor` has no
                Solidity analogue; forcing both into the top level produces a
                schema that is mostly nulls.

`display_text` and `model_text` are separate on purpose. The first is what a
human is shown and what a citation quotes, always verbatim. The second is what
reaches the model's context window, with comments stripped. Collapsing them
means either citing text that isn't in the file, or feeding the model comments
that are attacker-writable free text. Both are worse than carrying two fields.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import Any

# Adding a chunker means adding its source type here. The allowlist is
# deliberate: an unrecognised source_type is far more often a typo than a new
# format, and validate() is the last thing that runs before chunks are indexed.
SOURCE_TYPES = ("solidity", "markdown")
TIERS = ("A", "B")
MARKDOWN_SLICED_MAX_CHARS = 10_000
WHOLE_DOCUMENT_MAX_CHARS = 500
_STRONG_SECTION = re.compile(
    r"(?m)^ {0,3}(?:\*\*[^*\r\n][^*\r\n]*?\*\*"
    r"|__[^_\r\n][^_\r\n]*?__)[ \t]*$")
_ORPHAN_MARKUP = re.compile(r"^ {0,3}(?:\*|\*\*|_|__)[ \t]*$")


def _orphan_markup_at_edge(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    return bool(lines and (_ORPHAN_MARKUP.fullmatch(lines[0])
                           or _ORPHAN_MARKUP.fullmatch(lines[-1])))


@dataclass
class Chunk:
    # ---- core: present on every chunk -------------------------------------
    id: str                       # stable, unique, human-readable
    kind: str                     # Function | Struct | surface | section | ...
    source_type: str              # solidity | markdown
    path: str                     # path within the source repo
    line: int                     # 1-based; 0 when not meaningful
    breadcrumb: str               # "file › Contract › signature" or heading path

    display_text: str             # verbatim text that a citation quotes
    model_text: str               # what enters the context window
    embed_text: str               # what gets embedded

    # ---- provenance: filled by the pipeline, not the chunker --------------
    tier: str = "A"               # A canonical, B published docs
    corpus_build_id: str | None = None
    source_ref: str | None = None         # tag + commit, or docs commit
    protocol_version: str | None = None   # e.g. "v1.2"; public names only
    deployment_status: str | None = None  # deployed | not_deployed | n/a
    effective_date: str | None = None     # tier B
    doc_version: str | None = None        # tier B
    supersedes: str | None = None

    # ---- integrity --------------------------------------------------------
    # True when display_text is assembled rather than sliced from source. The
    # citation layer must never present one of these as a verbatim quote: it is
    # a summary that looks exactly like source, which is worse than either.
    synthesised: bool = False
    warnings: list[str] = field(default_factory=list)

    # ---- source-specific --------------------------------------------------
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.model_text.encode()).hexdigest()


# --------------------------------------------------------------------------
# validation runs before anything is indexed
# --------------------------------------------------------------------------

def validate(chunks: list[Chunk], oversize_chars: int = 24_000,
             embed_oversize_chars: int | None = None) -> list[str]:
    """
    Return a list of problems. Empty means the set is safe to index.

    These are the failures that produce a *plausible* wrong answer rather than
    an obvious one, which is why they are checked rather than trusted.
    """
    problems: list[str] = []
    embed_limit = (oversize_chars if embed_oversize_chars is None
                   else embed_oversize_chars)

    seen: dict[str, int] = {}
    for c in chunks:
        seen[c.id] = seen.get(c.id, 0) + 1
    for cid, n in seen.items():
        if n > 1:
            problems.append(f"duplicate id ({n}x): {cid}")

    # Exact duplicate evidence inside one source file is almost always a
    # chunk-boundary error. Identical prose in different canonical/published
    # sources is permitted and remains visible to the audit report.
    content_seen: dict[tuple[str, str, str], str] = {}
    for c in chunks:
        namespace = c.id.partition(":")[0] if ":" in c.id else ""
        normalized = " ".join(c.model_text.split())
        if not normalized:
            continue
        key = (namespace, c.path, hashlib.sha256(normalized.encode()).hexdigest())
        previous = content_seen.get(key)
        if previous is not None:
            problems.append(
                f"{c.id}: duplicate content in {c.path}; also emitted as "
                f"{previous}")
        else:
            content_seen[key] = c.id

    for c in chunks:
        if c.source_type not in SOURCE_TYPES:
            problems.append(f"{c.id}: unknown source_type {c.source_type!r}")
        if c.tier not in TIERS:
            problems.append(f"{c.id}: unknown tier {c.tier!r}")
        if not c.display_text.strip():
            problems.append(f"{c.id}: empty display_text")
        if not c.embed_text.strip():
            problems.append(f"{c.id}: empty embed_text — will embed as noise")
        if len(c.model_text) > oversize_chars:
            problems.append(
                f"{c.id}: model_text {len(c.model_text)} chars exceeds "
                f"{oversize_chars}; the context window truncates silently")
        # embed_text is a superset of model_text by construction, and it is the
        # string the embedder actually receives. Checking only the shorter one
        # enforces a limit on text nothing consumes.
        if len(c.embed_text) > embed_limit:
            problems.append(
                f"{c.id}: embed_text {len(c.embed_text)} chars exceeds "
                f"{embed_limit}; the embedder truncates silently")
        # A sliced chunk exists to quote its source. One with no visible content,
        # such as an all-comment section, quotes nothing while still occupying
        # an index slot and a citation.
        if not c.synthesised and not c.model_text.strip():
            problems.append(
                f"{c.id}: empty model_text — sliced from source but there is "
                "nothing a reader can see")
        # A chunk claiming to be verbatim must actually be quotable. The
        # chunker knows whether it sliced or assembled; nothing downstream can
        # tell by looking, which is exactly why the flag has to be right.
        if c.synthesised and c.kind not in _ASSEMBLED_KINDS:
            problems.append(
                f"{c.id}: synthesised but kind={c.kind!r} is normally sliced")
        if not c.synthesised and c.kind in _ASSEMBLED_KINDS:
            problems.append(
                f"{c.id}: kind={c.kind!r} is assembled but not flagged "
                "synthesised — it would be quoted as source")
        if c.source_type == "markdown" and not c.synthesised:
            if len(c.model_text) > MARKDOWN_SLICED_MAX_CHARS:
                problems.append(
                    f"{c.id}: sliced Markdown is {len(c.model_text)} chars; "
                    f"review and split it below {MARKDOWN_SLICED_MAX_CHARS}")
            strong_sections = _STRONG_SECTION.findall(c.model_text)
            if (len(strong_sections) > 1
                    and c.detail.get("heading_level", 0) == 0):
                problems.append(
                    f"{c.id}: contains {len(strong_sections)} standalone "
                    "strong section titles; split them into evidence units")
            if (c.detail.get("whole_document")
                    and len(c.model_text) > WHOLE_DOCUMENT_MAX_CHARS):
                problems.append(
                    f"{c.id}: accidental whole-document chunk is "
                    f"{len(c.model_text)} chars; review its structure")
            if _orphan_markup_at_edge(c.model_text):
                problems.append(
                    f"{c.id}: contains an isolated Markdown delimiter")

    return problems


_ASSEMBLED_KINDS = {"contract", "interface", "library", "surface", "index"}


def stamp(chunks: list[Chunk], **provenance) -> list[Chunk]:
    """
    Apply build-time provenance uniformly. Chunkers do not know their own
    corpus_build_id or source_ref — the pipeline does — and letting each one
    guess is how two chunks from one build end up claiming different origins.
    """
    for c in chunks:
        for k, v in provenance.items():
            if not hasattr(c, k):
                raise AttributeError(f"no such provenance field: {k}")
            setattr(c, k, v)
    return chunks


# --------------------------------------------------------------------------
# corpus provenance: what produced a delivered chunks.jsonl
# --------------------------------------------------------------------------

PROVENANCE_SCHEMA = "lemma-corpus-provenance/v1"
# The one thing a recorded pin may claim, because it is the one comparison
# `require_solc_version` performs. There is deliberately no "exact".
PIN_MATCH = "prefix"
# Nothing fetches or resolves a source ref. The record says so in its own words
# so a reader is not left to infer it from the field's absence.
REF_ORIGIN = "asserted-by-caller"
_URL = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*)://(.*)$")
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _named(value) -> bool:
    """True when a field holds a name rather than an absence.

    The presence tests here were spelled `str(value).strip()`, which reads a
    JSON `null` as the four-character string `None` and passes. A compiler
    absence carrying `reason: null`, an applicable compiler carrying
    `invocation: null`, and an input carrying `path: null` all validated clean,
    while the same records with the key removed were refused. A field either
    holds a non-blank string or holds nothing, and the two spellings of nothing
    have to land in the same place.
    """
    return isinstance(value, str) and bool(value.strip())


def _strip_userinfo(ref: str) -> str:
    """Drop `user:token@` from a ref that parses as a URL, keeping the rest.

    Ariadne's audit finding S4-R1-02 established the rule at
    `plugins/ariadne/scripts/ariadne_lib/scrub.py`: a repository is recorded so
    a reader can find it, so redacting the whole URL would defeat the field, and
    what has to go is the userinfo some tooling leaves in front of the host.
    The rule is implemented here rather than imported, because a cross-plugin
    import would break both the marketplace boundary and the packaging of the
    portable runtime.

    The split is bounded by the authority, which is the one difference from
    Ariadne's own mechanism and a deliberate one: Ariadne partitions on the
    first `@` anywhere after the scheme, and a source ref is the field where an
    `@` most often belongs to the ref itself. `https://host/owner/repo@7e449ba`
    carries no credential, and partitioning it would leave `https://7e449ba` —
    an origin silently replaced by a fragment of itself.

    What goes is the whole userinfo, whatever shape it has, and not only the
    `user:token@` one. `ssh://git@host/owner/repo.git` becomes
    `ssh://host/owner/repo.git`, which is a clean ref changed into one that
    will not clone. A ref with no scheme is untouched, which keeps
    `git@host:owner/repo.git` and `owner/repo@sha` verbatim and equally keeps
    the userinfo in a ref nobody spelled as a URL.

    The authority bound has a cost, and it belongs in the same breath as the
    rule. An unencoded `/`, `?` or `#` ahead of the `@` ends the authority
    before it, so nothing is stripped: `https://user:pa/ss@host/p` comes back
    whole where Ariadne's unbounded partition returns `https://host/p`. RFC
    3986 requires those three percent-encoded inside userinfo, so a conforming
    ref does not carry them; this strip is a defence against an accident, and
    that is the accident it does not catch.
    """
    match = _URL.match(ref)
    if not match:
        return ref
    scheme, rest = match.group(1), match.group(2)
    cut = min([len(rest)] + [at for at in (rest.find(c) for c in "/?#")
                             if at != -1])
    authority, remainder = rest[:cut], rest[cut:]
    if "@" not in authority:
        return ref
    return f"{scheme}://{authority.rpartition('@')[2]}{remainder}"


def compiler_absent(reason: str) -> dict:
    """A compiler block for a corpus no compiler produced.

    The Markdown chunker parses text; there is no version to record. Writing
    `unknown` here would be a guess wearing the shape of a value, and a reader
    two years later cannot tell one from a compiler actually called `unknown`.
    An absence says it is an absence and says why, so a blank reason is
    refused here rather than left for the validator to find.
    """
    if not _named(reason):
        raise ValueError(
            f"the reason no compiler applies is {reason!r}, which says "
            "nothing; an absence carries the reason it is an absence")
    return {"applicable": False, "reason": reason}


def compiler_reported(invocation: str, reported_version: str, *,
                      pin: str | None = None,
                      unpinned_reason: str | None = None) -> dict:
    """A compiler block for a corpus a compiler produced.

    `pin` is the `--expect-solc` string that was gated on, or None with a reason
    saying why nothing was gated. Exactly one of the two, because the pair is
    what keeps an ungated run from reading as a pinned one: a block with no pin
    and no reason would say nothing, and a pin the run did not make would say
    something false.

    A recorded pin is named `prefix`, never `exact`. `require_solc_version` in
    `chunkers/solidity.py` compares with `found.startswith(expected)`, so a gate
    on `0.8.25` accepts `0.8.25+commit.deadbeef` as readily as the build it was
    meant to name. The version the compiler reported for itself sits beside the
    pin so a reader can see the whole of what was checked.

    A pin that is not a non-blank string is refused rather than recorded.
    `require_solc_version` reads `if expected and not
    found.startswith(expected)`, so an empty `--expect-solc` skips the
    comparison altogether; a block carrying one would name a prefix gate the
    run never made, which is the first thing this pair exists to prevent.
    """
    if pin is not None and not _named(pin):
        raise ValueError(
            f"a pin of {pin!r} gates nothing: require_solc_version skips the "
            "comparison when the expected version is empty, so record the "
            "reason nothing was gated rather than a gate that was not made")
    if unpinned_reason is not None and not _named(unpinned_reason):
        raise ValueError(
            f"the reason nothing was gated is {unpinned_reason!r}, which says "
            "nothing; an ungated run records why it was ungated")
    if (pin is None) == (unpinned_reason is None):
        raise ValueError(
            "a compiler block records either the pin that was gated on or a "
            "reason none was, and never both or neither")
    return {"applicable": True,
            "invocation": invocation,
            "reported_version": reported_version,
            "pin": pin,
            "pin_match": None if pin is None else PIN_MATCH,
            "reason": unpinned_reason}


def provenance_record(*, chunker: str, chunker_version: str, source_ref: str,
                      corpus_build_id: str, chunk_count: int,
                      inputs: list[dict], include: list[str],
                      units_present: list[str], units_selected: list[str],
                      compiler) -> dict:
    """Build the one-line record a chunker writes to `provenance.jsonl`.

    A delivered corpus is two files in one directory. `chunks.jsonl` carries
    what a citation quotes; this record carries what produced it, which is the
    part no consumer can recover from the chunks themselves. It goes beside
    them so its bytes land inside the directory an Ariadne dataset capture
    walks, where its digest becomes a subject of the statement.

    The fields:

      schema             `lemma-corpus-provenance/v1`.
      chunker            which chunker ran, from SOURCE_TYPES.
      chunker_version    the lemma skill's governed version.
      source_ref         the origin, as given, less any URL userinfo.
      source_ref_origin  that nothing resolved it. See REF_ORIGIN.
      corpus_build_id    recomputed by the caller from the chunks written.
      chunk_count        how many chunks are in the file beside this one.
      inputs             `{path, sha256}` per digested input.
      selection          the include patterns and the source units present,
                         selected and excluded. The excluded ones are derived
                         here rather than passed, because they are what a
                         coverage block turns into gaps and a hand-written
                         list is a list that can disagree with itself.
      compiler           from compiler_absent() or compiler_reported().

    Refusals belong here rather than downstream: a corpus delivered with no
    origin is the defect the record exists to close, and a ref of `"   "`
    satisfies a presence check while naming nothing. A ref carrying a control
    character is refused for the same reason one line further on: `_URL` cannot
    span a newline, so such a ref never reaches the strip and any userinfo in
    it would be written verbatim.

    The list-shaped arguments are refused here for a related reason. `list()`
    and `sorted()` spread a bare string into one entry per character, so
    `include="**/*.sol"` became eight one-character patterns. Three of the four
    were then caught downstream by a cross-check that happened to disagree;
    `include` has no cross-check and validated clean, which is a record naming
    a coverage its corpus never had.
    """
    for name, value in (("--include", include),
                        ("units_present", units_present),
                        ("units_selected", units_selected)):
        if not isinstance(value, list) or not all(_named(u) for u in value):
            raise ValueError(
                f"{name} is {value!r}; it is a list of strings, and a bare "
                "string spreads into one entry per character rather than "
                "naming anything")
    if not isinstance(inputs, list) or not all(
            isinstance(entry, dict) for entry in inputs):
        raise ValueError(
            f"--inputs is {inputs!r}; it is a list of {{path, sha256}} objects")
    # Before .strip(), which is what turned a non-string ref into an
    # AttributeError naming neither the flag nor the problem, while every other
    # argument here refuses by type with a reason that names it.
    if not isinstance(source_ref, str):
        raise ValueError(
            f"--source-ref is {source_ref!r}; it is the origin string, and a "
            "value that is not one carries no ref to strip or to record")
    ref = source_ref.strip()
    if not ref:
        raise ValueError(
            "--source-ref is empty; a corpus delivered with no origin is the "
            "defect this record exists to close")
    if any(ch < " " or ch == "\x7f" for ch in ref):
        raise ValueError(
            f"--source-ref {ref!r} carries a control character; a ref is one "
            "line, and a ref that is not one line does not parse as a URL, so "
            "any userinfo in it would reach disk unstripped")
    return {
        "schema": PROVENANCE_SCHEMA,
        "chunker": chunker,
        "chunker_version": chunker_version,
        "source_ref": _strip_userinfo(ref),
        "source_ref_origin": REF_ORIGIN,
        "corpus_build_id": corpus_build_id,
        "chunk_count": chunk_count,
        "inputs": list(inputs),
        "selection": {
            "include": list(include),
            "units_present": sorted(units_present),
            "units_selected": sorted(units_selected),
            "units_excluded": sorted(set(units_present) - set(units_selected)),
        },
        "compiler": compiler,
    }


def _strings(value):
    """Every string anywhere in a record, so a guess cannot hide in a block."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def validate_provenance(record: dict) -> list[str]:
    """
    Return a list of problems. Empty means the record is safe to write beside a
    corpus.

    Every problem, not the first: the record is written once, digested, and
    named in a statement, so a caller who has to run again for each mistake
    learns the shape of the record one failure at a time.
    """
    problems: list[str] = []
    if not isinstance(record, dict):
        return [f"provenance record is {type(record).__name__}, not an object"]

    if record.get("schema") != PROVENANCE_SCHEMA:
        problems.append(f"schema is {record.get('schema')!r}, expected "
                        f"{PROVENANCE_SCHEMA!r}")
    if record.get("chunker") not in SOURCE_TYPES:
        problems.append(f"unknown chunker {record.get('chunker')!r}")
    for name in ("chunker_version", "source_ref", "corpus_build_id"):
        value = record.get(name)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{name} names nothing: {value!r}")
    if record.get("source_ref_origin") != REF_ORIGIN:
        problems.append(
            f"source_ref_origin is {record.get('source_ref_origin')!r}; "
            f"nothing resolves a ref, so it is {REF_ORIGIN!r}")
    count = record.get("chunk_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        problems.append(f"chunk_count is {count!r}; a corpus has chunks")

    inputs = record.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        problems.append("inputs is empty — the record digests nothing")
    else:
        for entry in inputs:
            if not isinstance(entry, dict) or not _named(entry.get("path")):
                problems.append(f"input has no path: {entry!r}")
            # str() here read a 64-digit number as a digest, because every
            # decimal digit is also a hexadecimal one.
            elif not (isinstance(entry.get("sha256"), str)
                      and _SHA256.fullmatch(entry["sha256"])):
                problems.append(
                    f"input {entry['path']}: sha256 {entry.get('sha256')!r} is "
                    "not 64 hexadecimal characters")

    selection = record.get("selection")
    if not isinstance(selection, dict):
        problems.append(f"selection is {selection!r}, not an object")
    else:
        include = selection.get("include")
        if not include:
            problems.append(
                "selection.include is empty — nothing says which source units "
                "the corpus was meant to cover")
        elif not isinstance(include, list) or not all(
                _named(pattern) for pattern in include):
            # The one field in this block with no type test and no cross-check
            # to catch it afterwards.
            problems.append(
                f"selection.include is {include!r}, not a list of patterns")
        # All three are compared as sets below. A value that is not a list of
        # strings took the validator down with a TypeError instead of
        # reporting the problem it exists to report.
        units = {}
        for name in ("units_present", "units_selected", "units_excluded"):
            value = selection.get(name) or []
            if not isinstance(value, list) or not all(
                    isinstance(unit, str) for unit in value):
                problems.append(
                    f"selection.{name} is {value!r}, not a list of source-unit "
                    "names")
                value = []
            units[name] = value
        present, selected, excluded = (units["units_present"],
                                       units["units_selected"],
                                       units["units_excluded"])
        if not selected:
            problems.append("selection.units_selected is empty — no corpus")
        stray = sorted(set(selected) - set(present))
        if stray:
            problems.append(
                f"selection: units selected that the input never declared: {stray}")
        # The excluded units are what the coverage block turns into gaps. A
        # record whose exclusions do not account for the difference lets an
        # interval read as complete while source units are missing from it.
        if sorted(set(present) - set(selected)) != sorted(excluded):
            problems.append(
                "selection: units_excluded is not the units present but not "
                "selected, so the gaps cannot be written from this record")

    problems.extend(_compiler_problems(record.get("compiler")))

    guesses = [value for value in _strings(record) if value == "unknown"]
    if guesses:
        problems.append(
            f"{len(guesses)} field(s) written as the string 'unknown'; an "
            "absent value is an absence with a reason")
    return problems


def _compiler_problems(compiler) -> list[str]:
    if not isinstance(compiler, dict) or "applicable" not in compiler:
        return [f"compiler block is {compiler!r}; it must say whether a "
                "compiler applies"]
    if compiler["applicable"] is False:
        if not _named(compiler.get("reason")):
            return ["compiler does not apply and no reason says why"]
        return []
    if compiler["applicable"] is not True:
        return [f"compiler applicable is {compiler['applicable']!r}, "
                "not a boolean"]

    problems: list[str] = []
    reported = compiler.get("reported_version")
    if not isinstance(reported, str) or not reported.strip():
        problems.append(f"compiler applies but reported {reported!r}")
    if not _named(compiler.get("invocation")):
        problems.append("compiler applies but the invocation is not recorded")
    pin, match = compiler.get("pin"), compiler.get("pin_match")
    if pin is None:
        if match is not None:
            problems.append(f"compiler has no pin but claims a {match!r} match")
        if not _named(compiler.get("reason")):
            problems.append("compiler was not gated and no reason says why")
    elif not _named(pin):
        # `require_solc_version` reads `if expected and not
        # found.startswith(expected)`, so an empty pin skips the comparison and
        # a non-string one never reached it. Either way the block names a gate
        # the run did not make, and comparing it further would only say so
        # twice.
        problems.append(
            f"compiler pin is {pin!r}, which gates nothing; the comparison is "
            "skipped when the expected version is empty, so record the reason "
            "nothing was gated")
    else:
        if match != PIN_MATCH:
            problems.append(
                f"compiler pin match is {match!r}; the gate compares with "
                f"startswith, so it is {PIN_MATCH!r}")
        if isinstance(reported, str) and not reported.startswith(pin):
            problems.append(
                f"compiler pin {pin!r} is not a prefix of the reported "
                f"{reported!r}, so the pin records a gate that did not pass")
    return problems
