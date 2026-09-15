import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
results = []
with tempfile.TemporaryDirectory(prefix="host-write-probe-", dir=root) as directory:
    fixture = Path(directory)
    allowed = fixture / "allowed"
    outside = fixture / "outside"
    allowed.mkdir()
    outside.mkdir()
    (outside / "existing").write_text("unchanged")
    (allowed / "escape").symlink_to(outside, target_is_directory=True)
    profile = '(version 1) (allow default) (deny file-write*) (allow file-write* (subpath ' + json.dumps(str(allowed)) + '))'
    cases = [
        ("inside-python", [sys.executable, "-c", "import pathlib,sys;pathlib.Path(sys.argv[1]).write_text('ok')", str(allowed / "ok")], 0),
        ("outside-python", [sys.executable, "-c", "import pathlib,sys;pathlib.Path(sys.argv[1]).write_text('bad')", str(outside / "bad")], 1),
        ("symlink-escape", [sys.executable, "-c", "import pathlib,sys;pathlib.Path(sys.argv[1]).write_text('bad')", str(allowed / "escape" / "bad")], 1),
        ("outside-delete", ["/bin/rm", str(outside / "existing")], 1),
        ("nested-shell", ["/bin/sh", "-c", "/bin/sh -c 'touch \"$1\"' nested \"$1\"", "outer", str(outside / "child")], 1),
    ]
    for name, argv, expected in cases:
        completed = subprocess.run(["/usr/bin/sandbox-exec", "-p", profile, *argv], cwd=allowed, capture_output=True, text=True, timeout=10)
        denied = "Operation not permitted" in completed.stderr
        results.append({"case": name, "exit": completed.returncode, "expected_exit": expected, "denied": denied, "passed": completed.returncode == expected and (expected == 0 or denied)})
    preserved = sorted(path.name for path in outside.iterdir()) == ["existing"] and (outside / "existing").read_text() == "unchanged"
    inside_written = (allowed / "ok").read_text() == "ok"
report = {"schema": "fiat-508-host-primitive-probe/v1", "platform": platform.platform(), "python": platform.python_version(), "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "cases": results, "outside_preserved": preserved, "inside_written": inside_written, "passed": all(row["passed"] for row in results) and preserved and inside_written}
print(json.dumps(report, sort_keys=True, indent=2))
sys.exit(0 if report["passed"] else 1)
