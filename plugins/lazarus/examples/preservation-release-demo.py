#!/usr/bin/env python3
"""The whole preservation-release path, offline, from the repository root.

    python3 plugins/lazarus/examples/preservation-release-demo.py

Verifies the checked-in Aave v4 fixture, captures an Ariadne statement over it,
writes a release, reads that release back, and reads the shipped release back
too. Then the two refusals that matter, because a path that only succeeds
demonstrates nothing:

1. A manifest with one integer edited and its fixture digest recomputed, so the
   document is entirely self-consistent. Lazarus recomputes the three evidence
   counts from the records and refuses it. Ariadne reads the counts from the
   manifest and does not re-derive them, so it accepts the same fixture and
   writes a statement reporting nine proof-backed records where five exist.
2. An honest fixture with a statement that overstates it. This is the one the
   release path exists for: the binding holds a statement to what verification
   recomputed rather than to what the manifest claims, and names the class and
   both numbers.

Needs no network and no provider. Writes only into a temporary directory and
leaves the checked-in fixture and release untouched.

The capture step runs Ariadne, which lives in this repository beside Lazarus. A
release does not need it: reading one back is Lazarus alone, and the shipped
release is read back here without Ariadne being involved.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = PLUGIN.parents[1]
LAZARUS = PLUGIN / "scripts" / "lazarus.py"
ARIADNE = REPOSITORY / "plugins" / "ariadne" / "scripts" / "ariadne.py"
FIXTURE = PLUGIN / "examples" / "aave-v4-spoke-v0"
SHIPPED = PLUGIN / "examples" / "aave-v4-spoke-v0-release"


def run(tool: Path, *arguments: object) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(tool)] + [str(argument) for argument in arguments],
        capture_output=True,
        text=True,
    )


def expect(what: str, result: subprocess.CompletedProcess, code: int, *phrases: str):
    """A step passes when its exit status and its words are both right."""
    output = result.stdout + result.stderr
    if result.returncode != code:
        raise SystemExit(
            "%s exited %d, expected %d\n%s" % (what, result.returncode, code, output)
        )
    for phrase in phrases:
        if phrase not in output:
            raise SystemExit("%s did not say %r\n%s" % (what, phrase, output))
    first = output.strip().splitlines()
    print("  %-46s exit %d  %s" % (what, result.returncode, first[0] if first else ""))


def capture(fixture: Path, out: Path, reason: str) -> subprocess.CompletedProcess:
    return run(
        ARIADNE,
        "capture-state-fixture",
        "--fixture", fixture,
        "--name", "aave-v4-spoke-v0",
        "--capture-tool", "lazarus",
        "--capture-command", "python3 plugins/lazarus/scripts/lazarus.py capture",
        "--first-capture-reason", reason,
        "--out", out,
    )


def tampered_copy(source: Path, target: Path) -> None:
    """One integer moved, and the fixture digest recomputed to match.

    Seven recorded RPC responses presented as proved state, in a document with
    nothing else wrong with it.
    """
    shutil.copytree(source, target)
    sys.path.insert(0, str(PLUGIN / "scripts"))
    from lazarus_lib.canonical import dumps, loads
    from lazarus_lib.manifest import fixture_digest

    manifest = loads((target / "manifest.json").read_bytes())
    manifest["evidence_counts"]["proof_backed"] = 9
    manifest["evidence_counts"]["recorded_rpc"] = 0
    manifest["fixture_digest"] = "0" * 64
    manifest["fixture_digest"] = fixture_digest(manifest)
    (target / "manifest.json").write_bytes(dumps(manifest) + b"\n")


def overstating_statement(source: Path, target: Path) -> None:
    """The same claim, made in the statement instead of the manifest."""
    document = json.loads(source.read_bytes())
    document["predicate"]["evidence"]["proof_backed"] = 9
    document["predicate"]["evidence"]["recorded_rpc"] = 0
    target.write_bytes(json.dumps(document, indent=2).encode())


def main() -> int:
    if not ARIADNE.is_file():
        raise SystemExit(
            "this demonstration captures a statement with Ariadne, which sits at "
            "%s in this repository and is not there" % ARIADNE
        )
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        print("the whole path, on the checked-in fixture:")
        expect("verify the fixture", run(LAZARUS, "verify", FIXTURE), 0,
               "proof-backed: 5", "recorded-rpc: 7")

        statement = workspace / "statement.json"
        expect(
            "capture a statement over it",
            capture(FIXTURE, statement,
                    "the first statement over this fixture; the fixture was "
                    "captured before Ariadne had a predicate for one"),
            0, "wrote",
        )
        release = workspace / "release"
        expect("write the release", run(LAZARUS, "release", FIXTURE,
                                       "--statement", statement, "--out", release),
               0, "checks: statement-type")
        expect("read the release back", run(LAZARUS, "verify-release", release), 0,
               "proof-backed: 5", "recorded-rpc: 7")
        expect("read the shipped release back",
               run(LAZARUS, "verify-release", SHIPPED), 0,
               "proof-backed: 5", "recorded-rpc: 7")

        print()
        print("a manifest with one integer edited and its digest recomputed:")
        tampered = workspace / "tampered-fixture"
        tampered_copy(FIXTURE, tampered)
        expect("lazarus refuses the fixture", run(LAZARUS, "verify", tampered), 1,
               "evidence counts")
        elsewhere = workspace / "statement-over-the-tampered-fixture.json"
        expect(
            "ariadne accepts it and writes a statement",
            capture(tampered, elsewhere, "a probe of the gap between the two tools"),
            0, "wrote",
        )
        claimed = json.loads(elsewhere.read_bytes())["predicate"]["evidence"]
        print("  the statement it wrote reports %d proof-backed record(s), "
              "where five exist" % claimed["proof_backed"])
        expect("and the release refuses it",
               run(LAZARUS, "release", tampered, "--statement", elsewhere,
                   "--out", workspace / "never-written"),
               1, "evidence counts")

        print()
        print("an honest fixture and a statement that overstates it:")
        overstating = workspace / "overstating-statement.json"
        overstating_statement(statement, overstating)
        expect("the release refuses it, naming the class",
               run(LAZARUS, "release", FIXTURE, "--statement", overstating,
                   "--out", workspace / "also-never-written"),
               1, "proof_backed", "more than the records support")
        for absent in ("never-written", "also-never-written"):
            if (workspace / absent).exists():
                raise SystemExit("a refused release left %s behind" % absent)
        print("  neither refusal left an output directory behind")
    print()
    print("the whole path ran offline, and both refusals held.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
