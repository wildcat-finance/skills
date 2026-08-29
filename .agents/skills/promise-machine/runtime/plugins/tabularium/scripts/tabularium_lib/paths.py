"""Release-relative path handling that refuses traversal and symlinks."""

from pathlib import Path, PurePosixPath, PureWindowsPath

from .core import TabulariumError


def _inside(root, candidate, label):
    try:
        return candidate.relative_to(root)
    except ValueError as error:
        raise TabulariumError("%s is outside the release directory" % label) from error


def relative_artifact_path(release_root, path, label, must_exist):
    """Return a safe POSIX path for an artefact passed to build."""
    root = Path(release_root).resolve(strict=True)
    candidate = Path(path)
    if candidate.is_symlink():
        raise TabulariumError("%s is a symlink" % label)
    if must_exist:
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file():
            raise TabulariumError("%s is not a regular file" % label)
    else:
        parent = candidate.parent.resolve(strict=True)
        resolved = parent / candidate.name
    relative = _inside(root, resolved, label)
    if not relative.parts:
        raise TabulariumError("%s does not name a file" % label)
    return relative.as_posix()


def resolve_artifact_path(release_root, relative, label):
    """Resolve a manifest path inside its release without following symlinks."""
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or "\x00" in relative
    ):
        raise TabulariumError("%s is not a safe relative path" % label)
    pure = PurePosixPath(relative)
    windows = PureWindowsPath(relative)
    if (
        pure.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        raise TabulariumError("%s is not a safe relative path" % label)

    root = Path(release_root).resolve(strict=True)
    candidate = root
    for part in pure.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise TabulariumError("%s uses a symlink" % label)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise TabulariumError("%s is missing" % label) from error
    _inside(root, resolved, label)
    if not resolved.is_file():
        raise TabulariumError("%s is not a regular file" % label)
    return resolved
