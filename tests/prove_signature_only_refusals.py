#!/usr/bin/env python3
"""Prove that retiring host identity and trailers left the signature refusal.

Resolver for the ``signature-refusal-preserved`` conformance criterion of the
``retain-declaration`` design in ``.hexaemeron/design-evidence.json``. That
criterion blocks ``step:2``, so the refusals below are checked before the step
that narrows ``verify_local_commit``'s callers opens.

``verify_local_commit`` in ``plugins/hexaemeron/skills/fiat/scripts/hexctl.py``
no longer refuses a runtime-host author, a runtime-host committer, a host
byline or a missing provenance trailer. Its signature refusal is what is left,
and it is the whole of what keeps a receipted range the range that was pushed.
This prover holds three specimens against it and requires the exact message
``hexctl.py`` gives today, not merely a non-zero exit:

1. **Unsigned.** An empty-tree commit built by ``git commit-tree`` in a
   disposable repository that declines to sign. ``%GK`` is empty, so the bare
   refusal applies.
2. **Altered after signing.** The same empty-tree object carrying the armoured
   signature of a commit this repository verifies locally, with a different
   message, written back through ``git hash-object -t commit -w --stdin``. The
   signature is real and no longer covers the payload, so ``%GK`` names a key
   the keyring holds and the keyed refusal applies. The prover first checks
   that the harvested signature does verify on its own object, and refuses to
   report anything when no locally verified commit is reachable: a signature
   that fails for want of a public key would prove nothing about alteration.
3. **GitHub web-flow.** ``77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883``, read from
   this repository's own object database, signed with
   ``B5690EEEBB952194``. It must reach the ``GITHUB_SIGNING_KEYS`` branch, not
   the keyed one.

Removing any one of the three refusals in ``hexctl.py`` makes its specimen
report a different message, or none, and this prover exits non-zero.

Boundaries. Every ``git`` call is a fixed argument list with no shell, a hard
timeout and a hard output cap; nothing read from the object database is
unbounded. The disposable repository declines to sign under the hostile signing
configuration ``tests/hostile_signing_harness.py`` owns, and an empty sentinel
is required as evidence that no signer was reached, so the specimens cannot
acquire a contributor's real signature. No credential is read, and the
environment handed to a child is a copy. ``--out`` must resolve inside this
repository, and the report is staged beside its destination and renamed, so an
interrupted run leaves no partial object.

Exit 0 writes the closed ``protasis-design-report/v1`` object. Exit 1 is a
specimen that was accepted or refused with something else, 2 a bad invocation,
and 3 a precondition this prover could not establish.
"""

from pathlib import Path
import argparse
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
HEXCTL = REPO_ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
HARNESS = REPO_ROOT / "tests/hostile_signing_harness.py"

CRITERION = "signature-refusal-preserved"
SCHEMA = "protasis-design-report/v1"

WEB_FLOW_COMMIT = "77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883"
WEB_FLOW_KEY = "B5690EEEBB952194"

GIT_TIMEOUT = 60
GIT_OUTPUT_MAX = 1 << 20
SIGNED_COMMIT_SEARCH = 25

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

FIXED_IDENTITY = {
    "GIT_AUTHOR_NAME": "Signature Specimen",
    "GIT_AUTHOR_EMAIL": "specimen@example.invalid",
    "GIT_AUTHOR_DATE": "1700000000 +0000",
    "GIT_COMMITTER_NAME": "Signature Specimen",
    "GIT_COMMITTER_EMAIL": "specimen@example.invalid",
    "GIT_COMMITTER_DATE": "1700000000 +0000",
}


class Unproven(Exception):
    """A precondition this prover could not establish."""


class Refused(Exception):
    """A specimen that was accepted, or refused with something else."""


def load(name: str, path: Path):
    """Import one repository module from its exact path."""
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise Unproven(f"{path} cannot be imported")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def git(argv, *, cwd, environment=None, stdin=None):
    """One fixed-argv git call, with no shell, a timeout and an output cap."""
    try:
        completed = subprocess.run(
            ["git", *argv],
            cwd=str(cwd),
            env=environment,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except OSError as error:
        raise Unproven(f"git {argv[0]} could not start: {error}") from error
    except subprocess.TimeoutExpired as error:
        raise Unproven(f"git {argv[0]} timed out after {GIT_TIMEOUT}s") from error
    if len(completed.stdout) > GIT_OUTPUT_MAX:
        raise Unproven(f"git {argv[0]} exceeded the {GIT_OUTPUT_MAX}-byte output cap")
    return completed.returncode, completed.stdout


def git_text(argv, *, cwd, environment=None, stdin=None):
    """The stripped stdout of one git call that has to succeed."""
    status, output = git(argv, cwd=cwd, environment=environment, stdin=stdin)
    if status != 0:
        raise Unproven(f"git {argv[0]} failed with exit {status}")
    return output.decode("utf-8", "replace").strip()


def locally_verified_commit():
    """One reachable commit whose signature this keyring validates."""
    listed = git_text(
        ["rev-list", f"--max-count={SIGNED_COMMIT_SEARCH}", "HEAD"],
        cwd=REPO_ROOT,
    )
    for commit in listed.split():
        status, _ = git(
            ["-c", "gpg.program=gpg", "verify-commit", commit],
            cwd=REPO_ROOT,
        )
        if status == 0:
            return commit
    raise Unproven(
        "no commit in the last "
        f"{SIGNED_COMMIT_SEARCH} is verified by this keyring, so the altered "
        "specimen cannot be built from a signature that was valid first"
    )


def armoured_signature(commit: str) -> list[bytes]:
    """The ``gpgsig`` header of one commit object, as its exact lines."""
    _, raw = git(["cat-file", "commit", commit], cwd=REPO_ROOT)
    lines: list[bytes] = []
    collecting = False
    for line in raw.split(b"\n"):
        if line.startswith(b"gpgsig "):
            collecting = True
            lines.append(line)
            continue
        if collecting:
            if line.startswith(b" "):
                lines.append(line)
                continue
            break
    if not lines:
        raise Unproven(f"commit {commit} carries no armoured signature to harvest")
    return lines


def disposable_repository(root: Path, harness):
    """A repository that declines to sign under a hostile signing configuration.

    The hostile arm turns signing on and points git at a signer that records
    the attempt and refuses, so the repository's own declaration is the only
    thing keeping the specimens unsigned. An empty sentinel afterwards is the
    evidence that no signer was reached.
    """
    hostile = root / "hostile"
    repository = root / "repository"
    hostile.mkdir()
    repository.mkdir()
    files = harness.write_arm(hostile, harness.OPENPGP)
    environment = harness.child_environment(files.config)
    environment.update(FIXED_IDENTITY)
    git_text(["init", "--quiet", str(repository)], cwd=root, environment=environment)
    for key, value in (("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
        git_text(["-C", str(repository), "config", key, value], cwd=root, environment=environment)
    return repository, environment, files.sentinel


def specimens(root: Path, harness):
    """The unsigned and altered empty-tree objects, in a disposable repository."""
    repository, environment, sentinel = disposable_repository(root, harness)
    tree = git_text(
        ["-C", str(repository), "hash-object", "-t", "tree", "-w", "--stdin"],
        cwd=root,
        environment=environment,
        stdin=b"",
    )
    if tree != EMPTY_TREE:
        raise Unproven(f"the empty tree hashed to {tree}, not {EMPTY_TREE}")
    unsigned = git_text(
        ["-C", str(repository), "commit-tree", tree, "-m", "unsigned specimen"],
        cwd=root,
        environment=environment,
    )
    _, raw = git(
        ["-C", str(repository), "cat-file", "commit", unsigned],
        cwd=root,
        environment=environment,
    )
    header, separator, _ = raw.partition(b"\n\n")
    if not separator:
        raise Unproven(f"specimen {unsigned} has no message separator")
    signature = armoured_signature(locally_verified_commit())
    altered_object = (
        b"\n".join(header.split(b"\n") + signature) + b"\n\naltered after signing\n"
    )
    altered = git_text(
        ["-C", str(repository), "hash-object", "-t", "commit", "-w", "--stdin"],
        cwd=root,
        environment=environment,
        stdin=altered_object,
    )
    reached = sentinel.read_bytes()
    if reached:
        raise Unproven(
            "the disposable repository reached the hostile signer, so its "
            f"specimens are not reliably unsigned: {reached[:200]!r}"
        )
    return repository, unsigned, altered


def refusal(hexctl, base_dir: str, commit: str, label: str) -> tuple[int, str]:
    """The exit status and stderr of one ``verify_local_commit`` refusal."""
    stream = io.StringIO()
    try:
        with contextlib.redirect_stderr(stream):
            hexctl.verify_local_commit(base_dir, commit, label)
    except SystemExit as stop:
        code = stop.code
        return (code if isinstance(code, int) else 1), stream.getvalue().strip()
    raise Refused(f"{label} commit {commit} was accepted by verify_local_commit")


def require(label: str, observed: tuple[int, str], expected: str) -> None:
    """Hold one refusal to hexctl's exit status and its exact message."""
    status, message = observed
    if status != 2:
        raise Refused(f"{label} was refused with exit {status}, expected 2")
    if message != f"hexctl: error: {expected}":
        raise Refused(
            f"{label} was refused with a different message.\n"
            f"  observed: {message}\n"
            f"  expected: hexctl: error: {expected}"
        )


def prove(hexctl, harness) -> None:
    """Hold all three specimens against hexctl's signature refusal."""
    with tempfile.TemporaryDirectory(prefix="signature-specimens-") as raw_root:
        root = Path(raw_root)
        repository, unsigned, altered = specimens(root, harness)
        base_dir = str(repository)

        label = "unsigned specimen"
        require(
            label,
            refusal(hexctl, base_dir, unsigned, label),
            f"{label} commit {unsigned} has no valid local signature",
        )

        label = "altered specimen"
        key = hexctl.signing_key(base_dir, altered).upper()
        if not key:
            raise Refused(
                f"{label} commit {altered} reports no signing key, so the "
                "harvested signature was not read back"
            )
        if key in hexctl.GITHUB_SIGNING_KEYS:
            raise Refused(
                f"{label} commit {altered} is signed with GitHub key {key}; "
                "the altered specimen must carry a local signature"
            )
        require(
            label,
            refusal(hexctl, base_dir, altered, label),
            f"{label} commit {altered} has no valid local signature "
            f"(signed with key {key}, which this keyring cannot validate)",
        )

    label = "web-flow specimen"
    key = hexctl.signing_key(str(REPO_ROOT), WEB_FLOW_COMMIT).upper()
    if key != WEB_FLOW_KEY:
        raise Unproven(
            f"{WEB_FLOW_COMMIT} reports signing key {key or 'none'}, "
            f"not {WEB_FLOW_KEY}"
        )
    require(
        label,
        refusal(hexctl, str(REPO_ROOT), WEB_FLOW_COMMIT, label),
        f"{label} commit {WEB_FLOW_COMMIT} is signed by GitHub "
        f"(key {WEB_FLOW_KEY}), not locally. GitHub rewrote this commit: its "
        "merge button, its Contents API and the rebase its native stacked "
        "pull-request flow performs all re-sign with that key, and the author "
        "and provenance trailers survive while the local signature does not. "
        "The range being receipted is therefore not the range that was pushed. "
        "Land the run from a branch holding the original unrebased commits. Do "
        "not import GitHub's public key to make this check pass; that removes "
        "the guarantee the check exists for.",
    )


def destination(supplied: str) -> Path:
    """One report path, resolved and confirmed inside this repository."""
    candidate = Path(supplied)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        raise SystemExit(f"{sys.argv[0]}: --out must resolve inside {REPO_ROOT}")
    if not resolved.parent.is_dir():
        raise SystemExit(f"{sys.argv[0]}: {resolved.parent} is not a directory")
    return resolved


def write_report(target: Path, candidate: str, command: str) -> None:
    """Stage the closed report beside its destination, then rename it in."""
    report = {
        "candidate": candidate,
        "command": command,
        "criterion": CRITERION,
        "exit": 0,
        "schema": SCHEMA,
        "unit": "boolean",
        "value": True,
    }
    body = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    staged = target.with_name(target.name + ".staged")
    staged.write_bytes(body)
    os.replace(staged, target)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Prove the signature refusals hold.")
    parser.add_argument("--candidate", required=True, help="the design candidate id")
    parser.add_argument("--out", required=True, help="where to write the design report")
    arguments = parser.parse_args(argv)

    target = destination(arguments.out)
    command = (
        f"python3 tests/prove_signature_only_refusals.py "
        f"--candidate {arguments.candidate} --out {arguments.out}"
    )
    hexctl = load("hexctl_under_proof", HEXCTL)
    harness = load("hostile_signing_harness_under_proof", HARNESS)
    try:
        prove(hexctl, harness)
    except Refused as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
    except Unproven as unproven:
        print(f"unproven: {unproven}", file=sys.stderr)
        return 3
    write_report(target, arguments.candidate, command)
    print(
        f"{CRITERION}: unsigned, altered and web-flow commits are each still "
        f"refused with hexctl's own message; wrote {target}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
