"""Compile one pinned checkout into a closed, digest-bound inventory.

The inventory is the denominator. It answers what the application can do,
under stated rules, so that reviewed rows can be placed against it and the
remainder named. It does not decide what any item should do.

Two compiles of the same tree produce the same digest. Everything that could
vary between machines stays out of the digested content: the root path is not
recorded, directory order is sorted, and no clock is read.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from . import lexer, paths
from . import schema as schema_lib

RULES = "dokimasia-inventory-rules/v1"
SCHEMA = "dokimasia-inventory/v1"
SOURCE_SUFFIXES = frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs"})
HTTP_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
# Client-side gates are found by name, which is a stated limit rather than a
# guarantee: a gate this list does not name is not in the inventory.
DEFAULT_GATE_NAMES = ("RequireAuth", "AuthGuard", "withAuth", "useAuthGuard", "ProtectedRoute")


class InventoryError(Exception):
    """One named refusal while compiling."""


def url_path(relative: PurePosixPath, app_root: PurePosixPath) -> str | None:
    """The URL a page or handler answers on, or None when it has no route.

    Route groups in parentheses contribute nothing. Dynamic, catch-all and
    optional catch-all segments keep their bracket form, because the inventory
    records the shape the source declares rather than one filled-in example.
    """
    try:
        inside = relative.relative_to(app_root)
    except ValueError:
        return None
    segments = []
    for part in inside.parts[:-1]:
        if part.startswith("(") and part.endswith(")"):
            continue
        if part.startswith("@"):
            continue
        segments.append(part)
    return "/" + "/".join(segments) if segments else "/"


def _dynamic_segments(url: str) -> list[str]:
    return [part for part in url.split("/") if part.startswith("[")]


def compile_inventory(
    root: Path,
    gate_names: tuple[str, ...] = DEFAULT_GATE_NAMES,
) -> list[dict]:
    """Every route, handler, action and guard the rules recognise, sorted."""
    files = paths.source_files(root, SOURCE_SUFFIXES)
    app_roots = _app_roots(files)
    items: list[dict] = []
    for relative in files:
        source = paths.read_source(root, relative)
        tokens = lexer.tokenize(source)
        directives = lexer.directive_prologue(tokens)
        exports = lexer.exported_names(tokens)
        stem = relative.stem
        app_root = _owning_app_root(relative, app_roots)

        if stem == "page" and app_root is not None:
            url = url_path(relative, app_root)
            if url is not None:
                items.append({
                    "kind": "route", "url": url, "source": relative.as_posix(),
                    "dynamic_segments": _dynamic_segments(url),
                })
        elif stem == "route" and app_root is not None:
            url = url_path(relative, app_root)
            if url is not None:
                methods = sorted(m for m in HTTP_METHODS if m in exports)
                items.append({
                    "kind": "api", "url": url, "source": relative.as_posix(),
                    "methods": methods, "dynamic_segments": _dynamic_segments(url),
                })
        if stem in {"middleware"} and len(relative.parts) <= 2:
            items.append({
                "kind": "guard", "guard": "middleware",
                "source": relative.as_posix(),
                "matchers": _matchers(tokens),
            })
        if "use server" in directives:
            items.append({
                "kind": "action", "source": relative.as_posix(),
                "exports": sorted(exports),
            })
        named_gates = sorted(set(exports) & set(gate_names))
        if named_gates:
            items.append({
                "kind": "guard", "guard": "named-gate",
                "source": relative.as_posix(), "names": named_gates,
            })
    return sorted(items, key=lambda item: (item["kind"], item.get("url", ""), item["source"]))


def _app_roots(files: list[PurePosixPath]) -> list[PurePosixPath]:
    """Every directory named `app` that holds routable files."""
    roots = set()
    for relative in files:
        parts = relative.parts
        for position, part in enumerate(parts[:-1]):
            if part == "app":
                roots.add(PurePosixPath(*parts[: position + 1]))
    return sorted(roots, key=lambda p: len(p.parts), reverse=True)


def _owning_app_root(relative: PurePosixPath, app_roots: list[PurePosixPath]):
    for candidate in app_roots:
        if candidate.parts == relative.parts[: len(candidate.parts)]:
            return candidate
    return None


MATCHER_TOKEN_CAP = 512


def _matchers(tokens: list[lexer.Token]) -> list[str]:
    """String values that follow a `matcher` key, up to a stated bound.

    The scan is capped, and reaching the cap refuses rather than returning a
    shorter list. A guard whose matchers were silently truncated would read as
    a guard that covers fewer paths than it does.
    """
    found: list[str] = []
    for position, token in enumerate(tokens):
        if not (token.kind == "name" and token.value == "matcher"):
            continue
        window = tokens[position + 1:position + 1 + MATCHER_TOKEN_CAP]
        closed = False
        for candidate in window:
            if candidate.kind == "string":
                found.append(candidate.value)
            if candidate.kind == "punct" and candidate.value == "}":
                closed = True
                break
        if not closed and len(window) == MATCHER_TOKEN_CAP:
            raise InventoryError(
                f"a matcher list did not close within the "
                f"{MATCHER_TOKEN_CAP}-token cap, so it cannot be recorded whole"
            )
    return sorted(set(found))


def canonical_bytes(items: list[dict]) -> bytes:
    """The exact bytes the inventory digest covers."""
    return json.dumps(
        {"schema": SCHEMA, "rules": RULES,
         "caps": {"files": paths.MAX_FILES, "file_bytes": paths.MAX_FILE_BYTES,
                  "depth": paths.MAX_DEPTH},
         "items": items},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def inventory_digest(items: list[dict]) -> str:
    return hashlib.sha256(canonical_bytes(items)).hexdigest()


def record(items: list[dict], subject: dict) -> dict:
    """The closed record, with the digest over content and not over the subject."""
    counts: dict[str, int] = {}
    for item in items:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    return {
        "schema": SCHEMA,
        "rules": RULES,
        "subject": subject,
        "caps": {"files": paths.MAX_FILES, "file_bytes": paths.MAX_FILE_BYTES,
                 "depth": paths.MAX_DEPTH},
        "counts": {kind: counts.get(kind, 0) for kind in ("route", "api", "action", "guard")},
        "scoped_items": len(items),
        "inventory_sha256": inventory_digest(items),
        "items": items,
    }


def refusal_proofs() -> list[tuple[str, str]]:
    """Drive every declared path rule and cap, and report what each refused.

    A cap that has never refused is a number in a document. Each case below
    builds the smallest tree that breaches one rule and requires the refusal to
    name it, so the guarantee is exercised rather than asserted.
    """
    import tempfile

    results: list[tuple[str, str]] = []

    def record(name: str, run) -> None:
        try:
            run()
        except paths.PathRefusal as refusal:
            results.append((name, str(refusal)))
        else:
            results.append((name, ""))

    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        root = base / "root"
        (root / "src").mkdir(parents=True)
        (root / "src" / "page.tsx").write_text("export default function P() {}", "utf-8")
        resolved = paths.declared_root(root)

        record("absolute-path", lambda: paths.relative_within(resolved, "/etc/passwd"))
        record("parent-directory", lambda: paths.relative_within(resolved, "../outside.ts"))

        link = base / "linked-root"
        link.symlink_to(root, target_is_directory=True)
        record("symlink-root", lambda: paths.declared_root(link))

        big = root / "src" / "big.tsx"
        big.write_bytes(b"x" * (paths.MAX_FILE_BYTES + 1))
        record("oversized-file",
               lambda: paths.read_source(resolved, PurePosixPath("src/big.tsx")))
        big.unlink()

        deep = root
        for level in range(paths.MAX_DEPTH + 2):
            deep = deep / f"d{level}"
        deep.mkdir(parents=True)
        (deep / "page.tsx").write_text("export default function D() {}", "utf-8")
        record("over-deep-tree",
               lambda: paths.source_files(resolved, SOURCE_SUFFIXES))

        # The file-count cap is exercised by passing a smaller bound rather
        # than by writing twenty thousand files. The branch under test is the
        # same one; only the number it compares against changes, and no module
        # global is mutated, so no concurrent read ever sees a lowered cap.
        shallow = base / "counted"
        (shallow / "src").mkdir(parents=True)
        for index in range(4):
            (shallow / "src" / f"p{index}.tsx").write_text("export default function P() {}", "utf-8")
        counted_root = paths.declared_root(shallow)
        record("over-large-file-count",
               lambda: paths.source_files(counted_root, SOURCE_SUFFIXES, max_files=2))
    return results


def check(fixture_root: Path) -> list[str]:
    """Every failure this step's exit criteria name, or an empty list."""
    failures: list[str] = []

    first = compile_inventory(fixture_root)
    second = compile_inventory(fixture_root)
    if canonical_bytes(first) != canonical_bytes(second):
        failures.append("two compiles of the same tree disagreed")
    if not first:
        failures.append("the fixture compiled to an empty inventory")

    kinds = {item["kind"] for item in first}
    for required in ("route", "api", "action", "guard"):
        if required not in kinds:
            failures.append(f"the fixture produced no {required} item")

    for name, refusal in refusal_proofs():
        if not refusal:
            failures.append(f"{name} was accepted; it must refuse")

    if any("decoy" in item["source"] for item in first):
        failures.append("a commented or quoted decoy reached the inventory")

    # The schema says the record is closed. Enforce it rather than stating it.
    failures.extend(
        f"the inventory record breaches its schema: {line}"
        for line in schema_lib.check(record(first, {"label": "tests/fixtures/app"}))
    )
    return failures
