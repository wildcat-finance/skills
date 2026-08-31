"""Write a preservation release: a fixture, a statement about it, and the bind.

A release is three things in one directory. The fixture is a byte-for-byte copy
of a directory that verifies. The statement is the bytes somebody handed over,
unaltered, because the release digests them and a re-encoded document is a
different document. The release file records what verification established and
which checks the binding made.

Two decisions are worth stating.

**One read of the directory, not two.** Verification and binding both need the
manifest, and reading it twice means reading two states: a component can change
between the two reads, and nothing after the first read would notice. So
`verify_fixture` hands back the manifest its report was computed from, and the
binding is given that rather than a second read.

**The output appears whole or not at all.** Everything is built in a staging
directory beside the destination and moved into place with one rename. A run
that dies halfway leaves a directory whose name starts with a dot and is not a
release, rather than half of one that reads as whole.

The fixture copy is verified again after it is written, and its digest compared
to the original's. Copying is where bytes go missing, and a release holding a
fixture nobody has verified is the thing this exists to prevent.
"""

from __future__ import annotations

import errno
import hashlib
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any

from .binding import bind, predicate_type_of
from .canonical import MAX_JSON_BYTES, dumps, loads
from .errors import FormatError, IntegrityError, PathError
from .manifest import MANIFEST_NAME
from .paths import (
    confined_directory,
    read_confined_bytes,
    validate_relative_path,
)
from .schemas import validate_document
from .verifier import verify_fixture
from .version import __version__

FIXTURE_DIRECTORY = "fixture"
"""Where the fixture copy sits inside a release."""

STATEMENT_NAME = "statement.json"
"""Where the statement sits inside a release, beside the fixture rather than in it."""

RELEASE_NAME = "release.json"
"""The document binding the other two."""

_DARWIN_ROOT_ALIASES = {
    "etc": (b"private/etc", ("private", "etc")),
    "tmp": (b"private/tmp", ("private", "tmp")),
    "var": (b"private/var", ("private", "var")),
}

# alias name, exact link text, link identity, target identity. The link state is
# deliberately kept with the opened target until the final file is held. A new
# root compatibility alias is a new trust-boundary decision, not another item a
# caller may supply at runtime.
_DarwinAliasGuard = tuple[
    str,
    bytes,
    tuple[int, int, int, int, int, int],
    tuple[int, int],
]


def release_digest(release: dict[str, Any]) -> str:
    """A digest over everything the release says except the digest itself.

    Built from named fields rather than by deleting a key, so a field added to
    the schema and not to this identity is a test failure rather than a digest
    that quietly stops covering it.
    """
    identity = {
        "schema_version": release["schema_version"],
        "tool_version": release["tool_version"],
        "fixture": release["fixture"],
        "statement": release["statement"],
        "verified": release["verified"],
        "binding": release["binding"],
    }
    return hashlib.sha256(dumps(identity)).hexdigest()


def build_release(
    statement: dict[str, Any],
    statement_bytes: bytes,
    report: dict[str, Any],
    checks: list[str],
) -> dict[str, Any]:
    """The release document for a fixture that verified and a statement that bound."""
    version = report["manifest"]["schema_version"]
    verified = {
        "block_hash": report["block_hash"],
        "evidence_counts": dict(report["evidence_counts"]),
        "canonical_chain_claim": False,
    }
    if version == 2:
        verified["receipts_root"] = report["receipts_root"]
    release: dict[str, Any] = {
        "schema_version": version,
        "tool_version": __version__,
        "fixture": {
            "path": FIXTURE_DIRECTORY,
            "fixture_digest": report["fixture_digest"],
        },
        "statement": {
            "path": STATEMENT_NAME,
            "sha256": hashlib.sha256(statement_bytes).hexdigest(),
            "predicate_type": predicate_type_of(statement),
        },
        "verified": verified,
        "binding": {"checks": list(checks)},
        "release_digest": "0" * 64,
    }
    release["release_digest"] = release_digest(release)
    return validate_document("release", release)


def write_release(
    fixture: str | Path,
    statement_path: str | Path,
    out: str | Path,
) -> dict[str, Any]:
    """Verify a fixture, bind a statement to it, and write the release.

    Nothing is written until both pass. The return value is the release document,
    so a caller printing a summary reads what was written rather than recomputing
    it.
    """
    source = Path(fixture)
    destination = Path(out)
    _refuse_overlap(source, destination)
    if destination.exists() or destination.is_symlink():
        raise FormatError(f"release output already exists: {destination}")
    parent = destination.parent
    if not parent.is_dir():
        raise FormatError(f"release output has no parent directory: {parent}")

    _refuse_statement_inside(source, statement_path)
    statement_bytes = _read_statement(statement_path)
    # A document that is not an object is refused by the binding, which says so
    # in the same words it uses for every other shape it will not read. A second
    # check here would be a second authority on one question.
    statement = loads(statement_bytes)

    report = verify_fixture(source)
    checks = bind(statement, report["manifest"], report)
    release = build_release(statement, statement_bytes, report, checks)

    staged = parent / f".{destination.name}.staged"
    if staged.exists() or staged.is_symlink():
        raise FormatError(f"a staged release is already in the way: {staged}")
    try:
        staged.mkdir(mode=0o700)
        _copy_fixture(source, staged / FIXTURE_DIRECTORY, report["manifest"])
        copied = verify_fixture(staged / FIXTURE_DIRECTORY)
        if copied["fixture_digest"] != report["fixture_digest"]:
            raise IntegrityError(
                "the fixture copy verifies to "
                f"{copied['fixture_digest']} and the original to "
                f"{report['fixture_digest']}"
            )
        _write_owner_only(staged / STATEMENT_NAME, statement_bytes)
        _write_owner_only(staged / RELEASE_NAME, dumps(release) + b"\n")
        if destination.exists() or destination.is_symlink():
            # Checked again because the copy takes time and the name was free
            # when the run began. This narrows the window rather than closing
            # it: between here and the rename the name is still unheld, and
            # rename replaces an empty directory. Nothing else -- a file, a
            # symlink, a directory holding anything -- can be replaced, so what
            # a lost race costs is an empty directory, and a process that can
            # win it can rewrite the finished release anyway.
            raise FormatError(f"release output appeared while it was built: {destination}")
        os.replace(staged, destination)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return release


def verify_release(directory: str | Path) -> dict[str, Any]:
    """Read a release back and check every claim it makes about itself.

    Everything the write did is done again from the bytes on disk: the fixture
    copy is verified, the statement beside it is bound to that verification, and
    the document is held to both. Nothing is taken from the document except the
    two paths it names, because a document checking itself against its own
    numbers checks nothing.

    This is also where the release digest is checked. `validate release` answers
    whether a document is well formed, the way `validate manifest` does; whether
    its digests hold is this question, and it is asked here.
    """
    root = Path(directory)
    release = validate_document(
        "release", loads(_read_inside(root, RELEASE_NAME, "release document"))
    )
    if release["release_digest"] != release_digest(release):
        raise IntegrityError(
            "the release digest does not cover this document; it records "
            f"{release['release_digest']} and the document digests to "
            f"{release_digest(release)}"
        )
    _refuse_unlisted(root, release)

    statement_bytes = _read_inside(
        root, release["statement"]["path"], "statement"
    )
    held = hashlib.sha256(statement_bytes).hexdigest()
    if held != release["statement"]["sha256"]:
        raise IntegrityError(
            f"the statement digests to {held} and the release records "
            f"{release['statement']['sha256']}"
        )
    statement = loads(statement_bytes)

    fixture = confined_directory(root, release["fixture"]["path"])
    report = verify_fixture(fixture)
    fixture_version = report["manifest"]["schema_version"]
    if release["schema_version"] != fixture_version:
        raise IntegrityError(
            f"release-v{release['schema_version']} holds a manifest-v{fixture_version} "
            "fixture; preservation formats are never upgraded implicitly"
        )
    if report["fixture_digest"] != release["fixture"]["fixture_digest"]:
        raise IntegrityError(
            f"the fixture verifies to {report['fixture_digest']} and the release "
            f"records {release['fixture']['fixture_digest']}"
        )

    declared = predicate_type_of(statement)
    if declared != release["statement"]["predicate_type"]:
        raise IntegrityError(
            f"the statement is a {declared} and the release records a "
            f"{release['statement']['predicate_type']}"
        )

    checks = bind(statement, report["manifest"], report)
    if checks != release["binding"]["checks"]:
        raise IntegrityError(
            "the release records checks this binding does not make: recorded "
            f"{', '.join(release['binding']['checks'])}; made "
            f"{', '.join(checks)}"
        )

    verified = release["verified"]
    if verified["block_hash"] != report["block_hash"]:
        raise IntegrityError(
            f"the release records block {verified['block_hash']} and the fixture "
            f"verifies to {report['block_hash']}"
        )
    if verified["evidence_counts"] != report["evidence_counts"]:
        raise IntegrityError(
            "the release records evidence counts the fixture does not verify to: "
            f"recorded {verified['evidence_counts']}, verified "
            f"{report['evidence_counts']}"
        )
    if release["schema_version"] == 2:
        if verified["receipts_root"] != report["receipts_root"]:
            raise IntegrityError(
                "the release records receipts root "
                f"{verified['receipts_root']} and the fixture reconstructs "
                f"{report['receipts_root']}"
            )
    # `verified.canonical_chain_claim` is not checked here. The schema pins it to
    # false, so a document claiming it does not get this far, and the binding
    # already refuses a report that claims it. A third check would be a third
    # authority on one question.
    result = {
        "release_digest": release["release_digest"],
        "fixture_digest": report["fixture_digest"],
        "block_hash": report["block_hash"],
        "evidence_counts": dict(report["evidence_counts"]),
        "predicate_type": declared,
        "statement_sha256": held,
        "checks": list(checks),
    }
    if release["schema_version"] == 2:
        result["receipts_root"] = report["receipts_root"]
    return result


def _read_inside(root: Path, relative: str, what: str) -> bytes:
    """One file from inside a release, through no-follow descriptors."""
    try:
        # read_confined_bytes normalises the path itself, and doing it here as
        # well would be a second authority saying the same thing.
        return read_confined_bytes(root, relative, max_bytes=MAX_JSON_BYTES)
    except PathError as error:
        # Not nested: read_confined_bytes speaks about fixture components, and a
        # release document is not one. The cause is kept on the exception.
        raise PathError(f"cannot read the {what}: {relative}") from error


def _refuse_unlisted(root: Path, release: dict[str, Any]) -> None:
    """A release holds the document, the statement and the fixture, and no more.

    The same rule the fixture manifest applies to its own directory. A file the
    document does not account for is a file a reader has no reason to trust and
    no way to check, sitting inside something whose whole claim is that every
    part of it was checked.
    """
    fixture = validate_relative_path(release["fixture"]["path"])
    statement = validate_relative_path(release["statement"]["path"])

    # Only the fixture subtree is opaque here; verify_fixture inventories it.
    # Every ancestor leading to that subtree or to the statement must itself be
    # exact, otherwise `inner/state` would make an unrelated `inner/note` look
    # accounted for merely because both share the first path segment.
    directories = {""}
    for relative in (fixture, statement):
        parts = relative.split("/")
        directories.update("/".join(parts[:index]) for index in range(1, len(parts)))
    allowed = {RELEASE_NAME, fixture, statement} | (directories - {""})

    for directory in sorted(
        directories, key=lambda value: (value.count("/"), value)
    ):
        absolute = root / directory if directory else root
        try:
            with os.scandir(absolute) as entries:
                for entry in entries:
                    relative = "/".join(
                        part for part in (directory, entry.name) if part
                    )
                    if entry.is_symlink():
                        raise PathError(f"release holds a symlink: {relative}")
                    if relative not in allowed:
                        raise IntegrityError(
                            "release holds an entry it does not account for: "
                            f"{relative}"
                        )
        except OSError as error:
            raise PathError(
                f"cannot inventory release directory: {directory or '.'}"
            ) from error


def _resolved(path: Path, what: str) -> Path:
    """The absolute path, or a refusal saying it could not be worked out.

    Every containment question below asks whether one path sits inside another,
    which needs both resolved first. Letting a resolve failure through would
    skip the question it was asked in aid of, which is the quiet failure this
    plugin refuses everywhere else.

    `pathlib` does not report a symlink loop the same way across versions: up to
    Python 3.12 `resolve` raises `RuntimeError`, and from 3.13 it resolves the
    loop to a path and raises nothing. So this catches both kinds and does not
    depend on either happening.
    """
    try:
        return path.resolve()
    except (OSError, RuntimeError) as error:
        raise PathError(f"cannot resolve the {what}: {path} ({error})") from error


def _refuse_overlap(source: Path, destination: Path) -> None:
    """Neither directory may sit inside the other.

    A release written inside the fixture would be covered by the fixture digest
    it records, and a fixture read from inside the release output would be read
    while it was being written.
    """
    first = _resolved(source, "fixture")
    second = _resolved(destination, "release output")
    if first == second:
        raise FormatError("release output is the fixture directory")
    if second.is_relative_to(first):
        raise FormatError(
            f"release output {destination} sits inside the fixture it describes"
        )
    if first.is_relative_to(second):
        raise FormatError(
            f"fixture {source} sits inside the release output {destination}"
        )


def _refuse_statement_inside(source: Path, statement_path: str | Path) -> None:
    """A statement about a fixture may not be a file inside it.

    The case refuses itself either way -- an unlisted file fails verification,
    and a listed one would have to carry its own digest, which no file can. Both
    refusals name something else, and a reader chasing a digest mismatch would
    spend a while getting to the reason. The reason is that the fixture digest
    would cover the statement made about the fixture, which is the same rule the
    release document is held to.
    """
    handed = Path(statement_path)
    resolved = _resolved(handed, "statement")
    inside = _resolved(source, "fixture")
    if resolved.is_relative_to(inside):
        raise FormatError(
            f"statement {handed} sits inside the fixture it describes; the "
            "fixture digest would cover the statement made about it"
        )


def _read_statement(path: str | Path) -> bytes:
    """The statement's bytes, read once, capped, and never re-encoded.

    Every named path segment is opened relative to the descriptor above it.
    `O_NOFOLLOW` on the final file alone still follows a symlinked parent, which
    lets a path checked by `_refuse_statement_inside` name different bytes by the
    time this read begins.
    """
    handed = Path(path)
    if ".." in handed.parts:
        # ``abspath`` is lexical: collapsing a parent segment after a symlink
        # can name different bytes from the path the caller handed over. It can
        # also make a user-controlled first ancestor disappear and expose one
        # of the Darwin root aliases to the bounded exception below. Refuse the
        # ambiguous spelling instead of changing which file is read.
        raise PathError("statement path contains a parent segment")
    absolute = Path(os.path.abspath(os.fspath(handed)))
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    root_descriptor: int | None = None
    current: int | None = None
    descriptor: int | None = None
    alias_guard: _DarwinAliasGuard | None = None
    failure = None
    try:
        root_descriptor = os.open(os.sep, directory_flags)
        current = root_descriptor
        parents = absolute.parts[1:-1]
        first_parent = 0
        if parents:
            accepted = _open_darwin_root_alias(
                root_descriptor,
                parents[0],
                directory_flags,
                handed,
            )
            if accepted is not None:
                current, alias_guard = accepted
                first_parent = 1
        for part in parents[first_parent:]:
            following = os.open(part, directory_flags, dir_fd=current)
            if current != root_descriptor:
                os.close(current)
            current = following
        if absolute.name:
            descriptor = os.open(absolute.name, file_flags, dir_fd=current)
        if alias_guard is not None:
            _recheck_darwin_root_alias(
                root_descriptor,
                alias_guard,
                directory_flags,
                handed,
            )
    except OSError as exc:
        failure = exc.errno
    except PathError:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        raise
    finally:
        if current is not None and current != root_descriptor:
            os.close(current)
        if root_descriptor is not None:
            os.close(root_descriptor)
    if descriptor is None:
        if failure in (errno.ELOOP, errno.ENOTDIR):
            raise PathError(
                f"statement path contains a symlink or non-directory: {handed}"
            )
        raise PathError(f"statement is not a regular file: {handed}")

    problem: Exception | None = None
    data = b""
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            problem = PathError(f"statement is not a regular file: {handed}")
        elif before.st_size > MAX_JSON_BYTES:
            problem = FormatError(
                f"statement exceeds {MAX_JSON_BYTES} bytes: {before.st_size}"
            )
        else:
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                data = handle.read(MAX_JSON_BYTES + 1)
            if len(data) > MAX_JSON_BYTES:
                problem = FormatError(
                    f"statement exceeds {MAX_JSON_BYTES} bytes: {len(data)}"
                )
            else:
                after = os.fstat(descriptor)
                if (
                    before.st_size,
                    before.st_mtime_ns,
                    before.st_ctime_ns,
                ) != (
                    after.st_size,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                ) or len(data) != before.st_size:
                    problem = PathError(f"statement changed while it was read: {handed}")
    except OSError:
        problem = PathError(f"cannot read statement: {handed}")
    finally:
        os.close(descriptor)
    if problem is not None:
        raise problem
    return data


def _open_darwin_root_alias(
    root_fd: int,
    alias: str,
    directory_flags: int,
    handed: Path,
) -> tuple[int, _DarwinAliasGuard] | None:
    """Open one fixed Apple root alias through its physical target.

    Ordinary directories still use the no-follow walk. On Darwin, only a
    symlink with one of the three exact lexical names may enter this exception.
    Its literal link bytes, link identity and followed target identity are held
    against the corresponding descriptor-opened ``private/*`` directory.
    """
    if sys.platform != "darwin":
        return None
    contract = _DARWIN_ROOT_ALIASES.get(alias)
    if contract is None:
        return None
    expected_link, physical = contract
    first = os.stat(alias, dir_fd=root_fd, follow_symlinks=False)
    if not stat.S_ISLNK(first.st_mode):
        raise _root_alias_refusal(handed)
    if os.readlink(os.fsencode(alias), dir_fd=root_fd) != expected_link:
        raise _root_alias_refusal(handed)

    target_fd: int | None = None
    try:
        target_fd = _open_root_directory(root_fd, physical, directory_flags)
        target = os.fstat(target_fd)
        followed = os.stat(alias, dir_fd=root_fd, follow_symlinks=True)
        second = os.stat(alias, dir_fd=root_fd, follow_symlinks=False)
        second_link = os.readlink(os.fsencode(alias), dir_fd=root_fd)
        link_identity = _root_link_identity(first)
        target_identity = _directory_identity(target)
        if (
            not stat.S_ISDIR(target.st_mode)
            or not stat.S_ISDIR(followed.st_mode)
            or _root_link_identity(second) != link_identity
            or second_link != expected_link
            or _directory_identity(followed) != target_identity
        ):
            raise _root_alias_refusal(handed)
        guard: _DarwinAliasGuard = (
            alias,
            expected_link,
            link_identity,
            target_identity,
        )
        return target_fd, guard
    except BaseException:
        if target_fd is not None:
            os.close(target_fd)
        raise


def _recheck_darwin_root_alias(
    root_fd: int,
    guard: _DarwinAliasGuard,
    directory_flags: int,
    handed: Path,
) -> None:
    """Re-prove the accepted root transition immediately before file reads."""
    try:
        reopened = _open_darwin_root_alias(
            root_fd,
            guard[0],
            directory_flags,
            handed,
        )
    except OSError:
        raise _root_alias_refusal(handed) from None
    if reopened is None:
        raise _root_alias_refusal(handed)
    descriptor, observed = reopened
    try:
        if observed != guard:
            raise _root_alias_refusal(handed)
    finally:
        os.close(descriptor)


def _open_root_directory(
    root_fd: int,
    components: tuple[str, ...],
    directory_flags: int,
) -> int:
    """Open a fixed root-relative directory without borrowing the root fd."""
    current: int | None = None
    try:
        for component in components:
            following = os.open(
                component,
                directory_flags,
                dir_fd=root_fd if current is None else current,
            )
            if current is not None:
                os.close(current)
            current = following
        if current is None:
            raise OSError(errno.ENOENT, "root alias has no physical target")
        return current
    except BaseException:
        if current is not None:
            os.close(current)
        raise


def _root_link_identity(details: os.stat_result) -> tuple[int, int, int, int, int, int]:
    """The symlink state whose continuity is required across both checks."""
    return (
        details.st_dev,
        details.st_ino,
        details.st_mode,
        details.st_size,
        details.st_mtime_ns,
        details.st_ctime_ns,
    )


def _directory_identity(details: os.stat_result) -> tuple[int, int]:
    """The filesystem identity of the fixed physical target."""
    return details.st_dev, details.st_ino


def _root_alias_refusal(handed: Path) -> PathError:
    """Keep the public refusal identical to every other symlinked parent."""
    return PathError(
        f"statement path contains a symlink or non-directory: {handed}"
    )


def _copy_fixture(source: Path, target: Path, manifest: dict[str, Any]) -> None:
    """Copy the manifest and every component it lists, and nothing else.

    Driven by the verified manifest rather than by walking the directory, so a
    file the manifest does not list cannot ride along into the copy. Verification
    of the source already refused any such file, and this keeps the copy honest
    even if that ever stops being true.
    """
    manifest_bytes = dumps(manifest) + b"\n"
    expected = [
        (
            MANIFEST_NAME,
            len(manifest_bytes),
            hashlib.sha256(manifest_bytes).hexdigest(),
        )
    ] + [
        (entry["path"], entry["bytes"], entry["sha256"])
        for entry in manifest["components"]
    ]
    target.mkdir(mode=0o700, parents=True)
    for relative, expected_bytes, expected_digest in expected:
        normalised = validate_relative_path(relative)
        data = read_confined_bytes(
            source, normalised, max_bytes=expected_bytes
        )
        if (
            len(data) != expected_bytes
            or hashlib.sha256(data).hexdigest() != expected_digest
        ):
            raise IntegrityError(
                f"fixture component changed after verification: {normalised}"
            )
        written = target / normalised
        written.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _write_owner_only(written, data)


def _write_owner_only(path: Path, data: bytes) -> None:
    """Write a new file the owner can read and nobody else can.

    The same mode `atomic_write_confined` uses for a fixture component. A release
    is not published by being written; whoever wants to hand it over opens it up
    deliberately.
    """
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
