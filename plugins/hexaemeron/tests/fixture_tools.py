"""Select real signing tools independently of a fixture's restricted PATH."""

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import tempfile


TOOL_DIRECTORIES = ("/usr/bin", "/bin", "/usr/local/bin", "/opt/homebrew/bin")
SIGNING_TOOLS = ("gpg", "gpgconf")


def signing_tool(name):
    if name not in SIGNING_TOOLS:
        raise ValueError(f"undeclared fixture signing tool: {name}")
    found = shutil.which(name, path=os.pathsep.join(TOOL_DIRECTORIES)) if TOOL_DIRECTORIES else None
    if found is None:
        raise FileNotFoundError(f"required fixture signing tool unavailable: {name}")
    return str(Path(found).resolve(strict=True))


@contextmanager
def native_signing_tools():
    """Expose only the selected tools to native verification's nested commands."""
    tools = {name: signing_tool(name) for name in SIGNING_TOOLS}
    previous = os.environ.get("PATH")
    with tempfile.TemporaryDirectory(prefix="fixture-tools-") as temporary:
        directory = Path(temporary).resolve()
        for name, executable in tools.items():
            (directory / name).symlink_to(executable)
        tail = os.defpath if previous is None else previous
        os.environ["PATH"] = str(directory) + (os.pathsep + tail if tail else "")
        try:
            yield tools
        finally:
            if previous is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous
