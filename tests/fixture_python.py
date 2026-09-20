"""Give a fixture's nested Python commands the interpreter running its tests."""

from contextlib import contextmanager
import os
from pathlib import Path
import sys
import tempfile


@contextmanager
def pinned_python_path():
    """Scope one real interpreter launcher without changing recorded argv."""
    previous = os.environ.get("PATH")
    with tempfile.TemporaryDirectory(prefix="fixture-python-") as temporary:
        directory = Path(temporary).resolve()
        (directory / "python3").symlink_to(Path(sys.executable).resolve(strict=True))
        tail = os.defpath if previous is None else previous
        os.environ["PATH"] = str(directory) + (os.pathsep + tail if tail else "")
        try:
            yield directory
        finally:
            if previous is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous
