"""Deterministic in-toto statements for verified Alexandria releases."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import secrets
import stat

from .canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes
from .errors import AlexandriaError
from .paths import read_confined_file
from .release import sha256, validate_manifest, verify


STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://ariadne.wildcat.finance/alexandria-release/v1"
VERIFICATION_CLAIM = "alexandria release offline verification"
DIGEST_PREFIX = "sha256:"
MAX_STATEMENT_BYTES = MAX_CONTROL_BYTES

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


def emit_statement(release_root: Path, output: Path) -> dict:
    """Verify a release and atomically emit its canonical unsigned statement."""
    release_root = Path(release_root).absolute()
    release_id = verify(release_root)
    manifest = _verified_manifest(release_root, release_id)
    statement = statement_for(manifest)
    validate_projection(manifest, statement)
    body = canonical_bytes(statement)
    if len(body) > MAX_STATEMENT_BYTES:
        raise AlexandriaError(
            "release statement exceeds Ariadne's "
            f"{MAX_STATEMENT_BYTES}-byte input limit"
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
    data = read_confined_file(
        release_root,
        "manifest.json",
        "manifest",
        max_bytes=MAX_CONTROL_BYTES,
    )
    manifest = load_bytes(data, "manifest")
    validate_manifest(manifest)
    if canonical_bytes(manifest) != data:
        raise AlexandriaError("manifest changed after release verification")
    identity = deepcopy(manifest)
    claimed = identity.pop("release_id")
    if claimed != release_id or sha256(canonical_bytes(identity)) != claimed:
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
