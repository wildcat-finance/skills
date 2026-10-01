"""Deterministic in-toto statements for verified Alexandria releases."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import secrets
import stat
from typing import NamedTuple

from .canonical import MAX_CONTROL_BYTES, canonical_bytes
from .errors import AlexandriaError
from .release import (
    MAX_MANIFEST_NODES,
    load_manifest,
    read_manifest_bytes,
    sha256,
    validate_manifest,
    verify,
)


STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://ariadne.wildcat.finance/alexandria-release/v1"
VERIFICATION_CLAIM = "alexandria release offline verification"
DIGEST_PREFIX = "sha256:"
MAX_STATEMENT_BYTES = MAX_CONTROL_BYTES
# Ariadne's aggregate key budget: gates 4 and 7 refuse a statement whose scanned
# keys (see `key_characters`) exceed this many characters.
MAX_STATEMENT_KEY_CHARACTERS = 262_144
# Three quarters of Ariadne's input limit is the largest payload whose base64
# still fits it; 64 KiB less leaves 87,380 bytes of an envelope for the DSSE
# fields and signatures, so a part that verifies bare also verifies signed.
MAX_PART_BYTES = MAX_STATEMENT_BYTES * 3 // 4 - 65_536
PART_PREDICATE_TYPE = "https://ariadne.wildcat.finance/alexandria-release-part/v1"
INDEX_PREDICATE_TYPE = "https://ariadne.wildcat.finance/alexandria-release-parts/v1"
INDEX_NAME = "index.json"
PART_NAME = "part-{:05d}.json"
PART_SUBJECT_PREFIX = "part/"
PART_DIRECTORY = "part"

PREDICATE_FIELDS = frozenset(
    {"release", "components", "captures", "claims", "commands"}
)
COMPONENT_FIELDS = frozenset(
    {"name", "object_path", "media_type", "bytes", "digest"}
)
CAPTURE_FIELDS = frozenset(
    {
        "id",
        "component",
        "component_digest",
        "venue",
        "chain",
        "evidence_class",
        "scope",
        "coverage",
    }
)
PART_PREDICATE_FIELDS = frozenset(
    {"release", "part", "components", "captures", "claims", "commands"}
)
PART_FIELDS = frozenset({"index", "first_component", "components", "captures"})
INDEX_PREDICATE_FIELDS = frozenset({"release", "parts", "claims", "commands"})
INDEX_PARTS_FIELDS = frozenset({"count", "components", "captures"})


class StatementPastSingleBounds(AlexandriaError):
    """A release whose one statement passes Ariadne's input limit or key budget.

    `statement --parts` writes such a release as an index and its parts.
    """


def in_toto_digest(value: str) -> dict[str, str]:
    """Convert one full lowercase Alexandria SHA-256 identity."""
    if (
        not isinstance(value, str)
        or not value.startswith(DIGEST_PREFIX)
        or len(value) != len(DIGEST_PREFIX) + 64
    ):
        raise AlexandriaError("statement identity must be a full sha256: digest")
    hexadecimal = value[len(DIGEST_PREFIX):]
    if hexadecimal != hexadecimal.lower() or any(
        character not in "0123456789abcdef" for character in hexadecimal
    ):
        raise AlexandriaError(
            "statement identity must use 64 lowercase hexadecimal characters"
        )
    return {"sha256": hexadecimal}


def statement_for(manifest) -> dict:
    """Project one validated manifest into Alexandria's Statement v1 shape."""
    release_digest = in_toto_digest(manifest["release_id"])
    subjects = [
        {
            "name": f"release/{manifest['release']['name']}",
            "digest": release_digest,
        }
    ]
    components = []
    for component in manifest["components"]:
        digest = in_toto_digest(component["sha256"])
        subjects.append(
            {"name": f"component/{component['name']}", "digest": digest}
        )
        components.append(
            {
                "name": component["name"],
                "object_path": component["object_path"],
                "media_type": component["media_type"],
                "bytes": component["bytes"],
                "digest": digest,
            }
        )

    captures = []
    for capture in manifest["captures"]:
        captures.append(
            {
                "id": capture["id"],
                "component": capture["component"],
                "component_digest": in_toto_digest(
                    capture["component_sha256"]
                ),
                "venue": capture["venue"],
                "chain": capture["chain"],
                "evidence_class": capture["evidence_class"],
                "scope": deepcopy(capture["scope"]),
                "coverage": deepcopy(capture["coverage"]),
            }
        )

    return {
        "_type": STATEMENT_TYPE,
        "subject": subjects,
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "release": {
                "format": manifest["format"],
                "digest": release_digest,
            },
            "components": components,
            "captures": captures,
            "claims": [
                {
                    "name": VERIFICATION_CLAIM,
                    "subject": release_digest,
                    "disposition": "passed",
                }
            ],
            "commands": [],
        },
    }


def validate_projection(manifest, statement) -> None:
    """Refuse a projection that omits or changes verified manifest evidence."""
    expected = statement_for(manifest)
    if statement != expected:
        raise AlexandriaError(
            "release statement does not exactly project the verified manifest"
        )


def key_characters(statement) -> int:
    """Characters in the keys Ariadne's gates 4 and 7 scan in one statement.

    That is every object key at any depth under `predicate`, and every key of
    each subject's `digest` object. Subject names are values, not keys, and an
    Alexandria subject carries no field beside `name` and `digest`.
    """
    total = 0
    stack = [statement["predicate"]]
    stack.extend(subject["digest"] for subject in statement["subject"])
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                total += len(key)
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return total


class StatementParts(NamedTuple):
    """A part set: the index bytes, then each part as (file name, bytes) in order."""

    index: bytes
    parts: tuple


def project_statement(manifest):
    """Project one verified manifest into its single statement or a part set.

    A statement within `MAX_STATEMENT_BYTES` and `MAX_STATEMENT_KEY_CHARACTERS`
    returns as the exact canonical bytes `emit_statement` writes. Any other
    returns a `StatementParts`, each file within `MAX_PART_BYTES` and the key
    budget. The manifest must be one the offline `verify` already accepted.
    """
    statement = statement_for(manifest)
    if key_characters(statement) <= MAX_STATEMENT_KEY_CHARACTERS:
        body = _encode_statement(statement)
        if len(body) <= MAX_STATEMENT_BYTES:
            return body
    return _part_set(statement)


def _encode_statement(value) -> bytes:
    # A verified manifest holds at most MAX_MANIFEST_NODES nodes and its
    # projection adds two a component, so this node limit, the one
    # `emit_statement` uses, refuses nothing the byte limits admit.
    try:
        return canonical_bytes(value, max_nodes=MAX_CONTROL_BYTES)
    except AlexandriaError as error:
        raise AlexandriaError(f"release statement cannot be encoded: {error}") from error


def _value_bytes(value) -> int:
    """Bytes one value adds inside a canonical document, without the newline."""
    return len(_encode_statement(value)) - 1


def _part(release_subject, predicate, number, first, subjects, components, captures):
    return {
        "_type": STATEMENT_TYPE,
        "subject": [release_subject, *subjects],
        "predicateType": PART_PREDICATE_TYPE,
        "predicate": {
            "release": predicate["release"],
            "part": {
                "index": number,
                "first_component": first,
                "components": len(components),
                "captures": len(captures),
            },
            "components": components,
            "captures": captures,
            "claims": predicate["claims"],
            "commands": [],
        },
    }


def _part_bytes(frame, number, first, components, captures, values) -> int:
    """The exact encoded size of a part from its empty frame and its values.

    `frame` is the size of a part with no component, no capture and the four
    counts at zero. Each count adds its decimal digits less that zero, and each
    array element after the first adds a comma; the subject array already holds
    the release, so every component subject adds one.
    """
    digits = sum(len(str(count)) - 1 for count in (number, first, components, captures))
    commas = components + (components - 1) + max(captures - 1, 0)
    return frame + digits + values + commas


def _part_set(statement) -> StatementParts:
    """Greedy parts in manifest order, then the index that binds them by digest.

    A part closes before the component whose subject, component object and
    captures would carry it past `MAX_PART_BYTES` or the key budget. Each
    capture lands in the part holding its component, in manifest order.
    """
    release_subject = statement["subject"][0]
    predicate = statement["predicate"]
    components = predicate["components"]
    owned = {}
    for capture in predicate["captures"]:
        owned.setdefault(capture["component"], []).append(capture)

    empty = _part(release_subject, predicate, 0, 0, [], [], [])
    frame = len(_encode_statement(empty))
    frame_keys = key_characters(empty)
    groups = []
    first = count = captures = values = keys = 0
    for position, component in enumerate(components):
        subject = statement["subject"][position + 1]
        its = owned.get(component["name"], [])
        cost = sum(_value_bytes(value) for value in (subject, component, *its))
        cost_keys = key_characters(
            {"subject": [subject], "predicate": [component, *its]}
        )
        if count:
            grown = _part_bytes(
                frame, len(groups), first, count + 1, captures + len(its), values + cost
            )
            if (
                grown <= MAX_PART_BYTES
                and keys + cost_keys <= MAX_STATEMENT_KEY_CHARACTERS
            ):
                count += 1
                captures += len(its)
                values += cost
                keys += cost_keys
                continue
            groups.append((first, count))
        alone = _part_bytes(frame, len(groups), position, 1, len(its), cost)
        if alone > MAX_PART_BYTES:
            raise AlexandriaError(
                f"release statement component {component['name']} needs a part of "
                f"{alone} bytes, above the {MAX_PART_BYTES}-byte part limit"
            )
        if frame_keys + cost_keys > MAX_STATEMENT_KEY_CHARACTERS:
            raise AlexandriaError(
                f"release statement component {component['name']} needs a part of "
                f"{frame_keys + cost_keys} key characters, above Ariadne's "
                f"{MAX_STATEMENT_KEY_CHARACTERS}-character scan budget"
            )
        first, count, captures, values = position, 1, len(its), cost
        keys = frame_keys + cost_keys
    groups.append((first, count))

    home = {}
    for number, (first, count) in enumerate(groups):
        for component in components[first:first + count]:
            home[component["name"]] = number
    placed = [[] for _ in groups]
    for capture in predicate["captures"]:
        placed[home[capture["component"]]].append(capture)

    parts = []
    for number, (first, count) in enumerate(groups):
        part = _part(
            release_subject,
            predicate,
            number,
            first,
            statement["subject"][first + 1:first + count + 1],
            components[first:first + count],
            placed[number],
        )
        body = _encode_statement(part)
        name = PART_NAME.format(number)
        _refuse_past_part_bounds(name, body, part)
        parts.append((name, body))

    index = {
        "_type": STATEMENT_TYPE,
        "subject": [release_subject]
        + [
            {"name": PART_SUBJECT_PREFIX + name, "digest": in_toto_digest(sha256(body))}
            for name, body in parts
        ],
        "predicateType": INDEX_PREDICATE_TYPE,
        "predicate": {
            "release": predicate["release"],
            "parts": {
                "count": len(parts),
                "components": len(components),
                "captures": len(predicate["captures"]),
            },
            "claims": predicate["claims"],
            "commands": [],
        },
    }
    body = _encode_statement(index)
    _refuse_past_part_bounds(INDEX_NAME, body, index)
    return StatementParts(body, tuple(parts))


def _refuse_past_part_bounds(name: str, body: bytes, statement) -> None:
    # Packing keeps every part inside both bounds, and the index of the
    # largest admitted release is far inside them; this holds the output to
    # the promise rather than to the arithmetic above.
    if len(body) > MAX_PART_BYTES:
        raise AlexandriaError(
            f"release statement {name} encodes to {len(body)} bytes, above the "
            f"{MAX_PART_BYTES}-byte part limit"
        )
    found = key_characters(statement)
    if found > MAX_STATEMENT_KEY_CHARACTERS:
        raise AlexandriaError(
            f"release statement {name} carries {found} key characters, above "
            f"Ariadne's {MAX_STATEMENT_KEY_CHARACTERS}-character scan budget"
        )


def emit_statement(release_root: Path, output: Path) -> dict:
    """Verify a release and atomically emit its canonical unsigned statement."""
    release_root = Path(release_root).absolute()
    release_id = verify(release_root)
    manifest = _verified_manifest(release_root, release_id)
    statement = statement_for(manifest)
    validate_projection(manifest, statement)
    # Every node encodes to at least one byte, so a node limit equal to the byte
    # limit refuses no statement the byte limit admits: the refusal a large
    # release meets is Ariadne's, not the encoder's default node limit.
    try:
        body = canonical_bytes(statement, max_nodes=MAX_STATEMENT_BYTES)
    except AlexandriaError as error:
        raise AlexandriaError(f"release statement cannot be encoded: {error}") from error
    if len(body) > MAX_STATEMENT_BYTES:
        raise StatementPastSingleBounds(
            f"release statement encodes to {len(body)} bytes, above Ariadne's "
            f"{MAX_STATEMENT_BYTES}-byte input limit"
        )
    keys = key_characters(statement)
    if keys > MAX_STATEMENT_KEY_CHARACTERS:
        raise StatementPastSingleBounds(
            f"release statement carries {keys} key characters, above Ariadne's "
            f"{MAX_STATEMENT_KEY_CHARACTERS}-character scan budget"
        )
    output = _write_statement(release_root, manifest, output, body, release_id)
    return {
        "release_id": release_id,
        "component_count": len(manifest["components"]),
        "capture_count": len(manifest["captures"]),
        "predicate_type": PREDICATE_TYPE,
        "output": str(output),
    }


def _verified_manifest(release_root: Path, release_id: str):
    """The manifest `verify` accepted, read again under the manifest limits.

    The second read is bound to the first: its bytes have to be canonical and
    hash to the identity `verify` returned, so a manifest changed in between
    refuses by name instead of being projected.
    """
    data = read_manifest_bytes(release_root, "manifest.json", "manifest")
    manifest = load_manifest(data, "manifest")
    validate_manifest(manifest)
    if canonical_bytes(manifest, max_nodes=MAX_MANIFEST_NODES) != data:
        raise AlexandriaError("manifest changed after release verification")
    identity = deepcopy(manifest)
    claimed = identity.pop("release_id")
    if (
        claimed != release_id
        or sha256(canonical_bytes(identity, max_nodes=MAX_MANIFEST_NODES)) != claimed
    ):
        raise AlexandriaError("manifest changed after release verification")
    return manifest


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _prepare_output(release_root: Path, output: Path):
    output = Path(os.path.abspath(output))
    if output.name in {"", ".", ".."}:
        raise AlexandriaError("statement output must name a file")

    release_resolved = release_root.resolve(strict=True)
    try:
        output_resolved = output.resolve(strict=False)
        parent_resolved = output.parent.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AlexandriaError(
            "statement output parent must already exist and be inspectable"
        ) from exc
    if _inside(output_resolved, release_resolved):
        raise AlexandriaError("statement output must not be inside the release")

    parent_absolute = output.parent.absolute()
    if parent_absolute != parent_resolved:
        raise AlexandriaError("statement output must not pass through a symlink")
    if _inside(parent_resolved / output.name, release_resolved):
        raise AlexandriaError("statement output must not be inside the release")

    required = (
        hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
        and os.unlink in os.supports_dir_fd
    )
    if not required:
        raise AlexandriaError(
            "this platform cannot perform a confined statement write"
        )
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        inspected = os.stat(parent_resolved, follow_symlinks=False)
    except OSError as exc:
        raise AlexandriaError(f"cannot inspect statement output parent: {exc}") from exc
    if not stat.S_ISDIR(inspected.st_mode):
        raise AlexandriaError("statement output parent must be a directory")

    parent_fd = None
    try:
        parent_fd = os.open(parent_resolved, flags)
        opened = os.fstat(parent_fd)
        current = os.stat(parent_resolved, follow_symlinks=False)
    except OSError as exc:
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass
        raise AlexandriaError(f"cannot inspect statement output parent: {exc}") from exc
    identities = {
        (inspected.st_dev, inspected.st_ino),
        (opened.st_dev, opened.st_ino),
        (current.st_dev, current.st_ino),
    }
    if (
        len(identities) != 1
        or not stat.S_ISDIR(opened.st_mode)
        or not stat.S_ISDIR(current.st_mode)
    ):
        os.close(parent_fd)
        raise AlexandriaError("statement output parent changed during inspection")
    return output, parent_resolved, parent_fd, (opened.st_dev, opened.st_ino)


def _target_stat(parent_fd: int, name: str):
    try:
        found = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise AlexandriaError(f"cannot inspect statement output: {exc}") from exc
    if not stat.S_ISREG(found.st_mode):
        raise AlexandriaError(
            "statement output must be absent or an existing regular file"
        )
    return found


def _release_files(manifest):
    paths = ["manifest.json"]
    paths.extend(component["object_path"] for component in manifest["components"])
    if "derivation" in manifest:
        from .derivation import output_paths

        paths.extend(output_paths(manifest["derivation"]))
    return paths


def _refuse_release_alias(release_root: Path, manifest, target) -> None:
    if target is None:
        return
    for relative in _release_files(manifest):
        try:
            release_file = os.stat(
                release_root / relative, follow_symlinks=False
            )
        except OSError as exc:
            raise AlexandriaError(
                f"cannot inspect release file while checking output alias: {exc}"
            ) from exc
        if (target.st_dev, target.st_ino) == (
            release_file.st_dev,
            release_file.st_ino,
        ):
            raise AlexandriaError("statement output must not alias a release file")


def _temporary(parent_fd: int, output_name: str):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    for _ in range(32):
        name = f".{output_name}.tmp-{secrets.token_hex(8)}"
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            continue
        try:
            created = os.fstat(descriptor)
        except OSError as exc:
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                os.unlink(name, dir_fd=parent_fd)
            except OSError:
                pass
            raise AlexandriaError(
                f"cannot inspect statement temporary output: {exc}"
            ) from exc
        if not stat.S_ISREG(created.st_mode):
            _remove_temporary(parent_fd, name, created)
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise AlexandriaError("statement temporary output is not a regular file")
        return name, descriptor, created
    raise AlexandriaError("cannot allocate a fresh statement temporary file")


def _write_all(descriptor: int, body: bytes) -> None:
    remaining = memoryview(body)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("statement write made no progress")
        remaining = remaining[written:]


def _remove_temporary(parent_fd: int, name: str, created) -> None:
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return
    if (current.st_dev, current.st_ino) != (created.st_dev, created.st_ino):
        return
    try:
        os.unlink(name, dir_fd=parent_fd)
    except OSError:
        pass


def _write_statement(
    release_root: Path,
    manifest,
    output: Path,
    body: bytes,
    release_id: str,
) -> Path:
    output, parent, parent_fd, parent_identity = _prepare_output(
        release_root, output
    )
    temporary_name = None
    descriptor = None
    created = None
    try:
        target = _target_stat(parent_fd, output.name)
        _refuse_release_alias(release_root, manifest, target)
        temporary_name, descriptor, created = _temporary(parent_fd, output.name)
        _write_all(descriptor, body)
        os.fsync(descriptor)

        if verify(release_root) != release_id:
            raise AlexandriaError("release changed while its statement was emitted")
        current_parent = parent.stat()
        if (current_parent.st_dev, current_parent.st_ino) != parent_identity:
            raise AlexandriaError("statement output parent changed during emission")
        current_temporary = os.stat(
            temporary_name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (current_temporary.st_dev, current_temporary.st_ino) != (
            created.st_dev,
            created.st_ino,
        ):
            raise AlexandriaError("statement temporary output changed during emission")
        target = _target_stat(parent_fd, output.name)
        _refuse_release_alias(release_root, manifest, target)
        os.replace(
            temporary_name,
            output.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temporary_name = None
        return output
    except AlexandriaError:
        raise
    except OSError as exc:
        raise AlexandriaError(f"cannot write release statement: {exc}") from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_name is not None and created is not None:
            _remove_temporary(parent_fd, temporary_name, created)
        os.close(parent_fd)


def emit_statement_parts(release_root: Path, output: Path) -> dict:
    """Verify a release past the single bounds and atomically write its part set.

    The set is `index.json` and `part/part-<k>.json` in a new directory at
    `output`, which must be absent. A release whose one statement is within
    both single bounds is refused, so each release has exactly one form.
    """
    release_root = Path(release_root).absolute()
    release_id = verify(release_root)
    manifest = _verified_manifest(release_root, release_id)
    validate_projection(manifest, statement_for(manifest))
    projection = project_statement(manifest)
    if not isinstance(projection, StatementParts):
        raise AlexandriaError(
            f"release statement fits Ariadne's {MAX_STATEMENT_BYTES}-byte input "
            f"limit and {MAX_STATEMENT_KEY_CHARACTERS}-character scan budget; "
            "emit it with --output <file>"
        )
    output = _write_parts(release_root, output, projection, release_id)
    return {
        "release_id": release_id,
        "part_count": len(projection.parts),
        "component_count": len(manifest["components"]),
        "capture_count": len(manifest["captures"]),
        "index_predicate_type": INDEX_PREDICATE_TYPE,
        "part_predicate_type": PART_PREDICATE_TYPE,
        "output": str(output),
    }


def _identity(found) -> tuple:
    return found.st_dev, found.st_ino


def _refuse_existing_parts(parent_fd: int, output: Path) -> None:
    try:
        os.stat(output.name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise AlexandriaError(f"cannot inspect statement parts output: {exc}") from exc
    raise AlexandriaError(f"statement parts output already exists: {output}")


def _make_directory(directory_fd: int, name: str, created: list) -> int:
    """Create one directory under `directory_fd` and return a no-follow descriptor.

    The directory joins `created` as soon as it exists, so a failure after this
    point removes it.
    """
    os.mkdir(name, 0o700, dir_fd=directory_fd)
    made = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    created.append((directory_fd, name, _identity(made), True))
    descriptor = os.open(
        name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd
    )
    opened = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(made.st_mode)
        or not stat.S_ISDIR(opened.st_mode)
        or _identity(opened) != _identity(made)
    ):
        os.close(descriptor)
        raise AlexandriaError("statement parts temporary directory changed during emission")
    return descriptor


def _temporary_parts_directory(parent_fd: int, output_name: str, created: list):
    for _ in range(32):
        name = f".{output_name}.tmp-{secrets.token_hex(8)}"
        try:
            return name, _make_directory(parent_fd, name, created)
        except FileExistsError:
            continue
    raise AlexandriaError("cannot allocate a fresh statement parts temporary directory")


def _create_part_file(directory_fd: int, name: str, body: bytes, created: list) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        try:
            made = os.fstat(descriptor)
        except OSError:
            try:
                os.unlink(name, dir_fd=directory_fd)
            except OSError:
                pass
            raise
        created.append((directory_fd, name, _identity(made), False))
        if not stat.S_ISREG(made.st_mode):
            raise AlexandriaError("statement parts temporary file is not a regular file")
        _write_all(descriptor, body)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_created(created: list) -> None:
    """Remove what this write made, innermost first, only while it is still ours."""
    for directory_fd, name, identity, is_directory in reversed(created):
        try:
            current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError:
            continue
        if _identity(current) != identity:
            continue
        try:
            if is_directory:
                os.rmdir(name, dir_fd=directory_fd)
            else:
                os.unlink(name, dir_fd=directory_fd)
        except OSError:
            pass


def _write_parts(
    release_root: Path,
    output: Path,
    projection: StatementParts,
    release_id: str,
) -> Path:
    if Path(os.path.abspath(output)).name in {"", ".", ".."}:
        raise AlexandriaError("statement parts output must name a directory")
    if not (
        os.mkdir in os.supports_dir_fd
        and os.rmdir in os.supports_dir_fd
        and os.rename in os.supports_dir_fd
    ):
        raise AlexandriaError(
            "this platform cannot perform a confined statement parts write"
        )
    output, parent, parent_fd, parent_identity = _prepare_output(release_root, output)
    created = []
    descriptors = []
    installed = False
    try:
        _refuse_existing_parts(parent_fd, output)
        temporary, temporary_fd = _temporary_parts_directory(
            parent_fd, output.name, created
        )
        descriptors.append(temporary_fd)
        temporary_identity = created[0][2]
        _create_part_file(temporary_fd, INDEX_NAME, projection.index, created)
        part_fd = _make_directory(temporary_fd, PART_DIRECTORY, created)
        descriptors.append(part_fd)
        for name, body in projection.parts:
            _create_part_file(part_fd, name, body, created)
        os.fsync(part_fd)
        os.fsync(temporary_fd)

        if verify(release_root) != release_id:
            raise AlexandriaError(
                "release changed while its statement parts were emitted"
            )
        if _identity(parent.stat()) != parent_identity:
            raise AlexandriaError(
                "statement parts output parent changed during emission"
            )
        current = os.stat(temporary, dir_fd=parent_fd, follow_symlinks=False)
        if _identity(current) != temporary_identity:
            raise AlexandriaError(
                "statement parts temporary directory changed during emission"
            )
        _refuse_existing_parts(parent_fd, output)
        os.rename(temporary, output.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        installed = True
        return output
    except AlexandriaError:
        raise
    except OSError as exc:
        raise AlexandriaError(f"cannot write release statement parts: {exc}") from exc
    finally:
        if not installed:
            _remove_created(created)
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass
        os.close(parent_fd)
