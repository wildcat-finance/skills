#!/usr/bin/env python3
"""Prove that a refused adapter identity says which of two causes it saw.

Resolver for the ``identity-cause-attribution`` conformance criterion of the
``source-pinned-count-commitment`` design in ``.hexaemeron/design-evidence.json``.
That criterion blocks ``integration``, so this runs in the delivery's last
step, once the guard it examines is in place.

The question. ``_verify_profile_identity`` in ``scripts/agent_instruction.py``
digests the whole rendered stdout of the adapter's identity command as
``acquisition_sha256``, and separately compares the ``MODEL_BLOB_RE``
projection of those same bytes against ``model_blobs_sha256``. Two different
events move those bytes: the runtime rendered its output differently, and the
model behind it actually changed. Before this delivery the whole-text digest is
checked first, so both events reach ``WAI-E-ADAPTER.IDENTITY_CHANGED`` at
``$.profile.acquisition_sha256`` and a re-pin is the only response available to
either. That is skills#1098's S3-R1-02, carried forward by this run's study.

What is proved. Four specimens are put to the shipped function, and the gate
holds when the two refusals disagree:

1. ``honest-plain``    the recorded rendering and the recorded blob set. Accepted.
2. ``honest-annotated`` a second rendering, recorded as itself. Accepted.
3. ``rendering-only``  the annotated rendering against a plain recording. The
   blob set is unchanged, so only the rendering moved. Refuses.
4. ``model-blob-set``  the plain rendering carrying a different model's blob.
   The model moved. Refuses.

Specimens 1 and 2 are the precondition, not decoration: acceptance is exactly
the statement that the bytes this prover expects are the bytes the stub
produced, for both renderings. Without them a stub that silently emitted
something else would make specimens 3 and 4 refuse for the wrong reason.

The gate is that specimens 3 and 4 reach different ``(code, node_path)`` pairs.
The study admits a weaker second disjunct -- a single refusal that states it
cannot attribute the cause -- but the selected design does not need it: it
checks the blob projection first and the whole-text digest second, under its
own code, so two causes reach two codes. A prose detail is not a stable
interface, and this gate does not read one.

Real material. The two blob digests are the ones this repository already
records: ``gpt-oss:120b`` from ``tests/fixtures/agent-instruction-v1/evidence/
tokenizer-profile.json`` and ``qwen3.8-27b-aeon:q4_k_m`` from its sibling
``family-profiles.json``. Both files are pinned by ``TRUSTED_PROFILE_SHA256``
and that pin is checked here before anything else, so a swapped fixture stops
this prover rather than being reported through it. No byte under
``tests/fixtures/`` is written.

Boundaries. Offline. No tokenizer, no model, no socket, and no Ollama. The
adapter runtime is a stand-in written to a disposable directory, so
``_run_bounded`` and ``_hash_executable`` run for real against a real
executable file whose output this prover chose. Nothing is monkeypatched: the
function under proof is the shipped one. ``--report`` must resolve inside this
repository and must be named for the candidate and criterion it carries, which
is what keeps a mistyped path from landing on one of the study's receipted
selection reports. The report is written to a temporary file beside its
destination and renamed, so an interrupted run leaves no partial object. No
controller state and no ledger is written.

Exit 0 writes the closed ``protasis-design-report/v1`` object and means the two
causes are distinguishable. Exit 1 means they are not, or a specimen behaved in
a way this prover cannot report; no report is written, so a receipted report
never records an unproved gate. Exit 2 is a bad invocation and exit 3 a
precondition this prover could not establish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_instruction as AI  # noqa: E402

REPORT_SCHEMA = "protasis-design-report/v1"
CRITERION = "identity-cause-attribution"
UNIT = "boolean"

#: Every candidate the design record carries. The report's candidate is read
#: from its own file name, so each candidate's declared resolver command is
#: correct as written, and a name outside this set is a typo rather than a
#: candidate.
CANDIDATES = (
    "recompute-at-check",
    "fold-into-stream-digest",
    "source-pinned-count-commitment",
    "token-stream-witness",
)

TOKENIZER_PROFILE = "tests/fixtures/agent-instruction-v1/evidence/tokenizer-profile.json"
FAMILY_PROFILES = "tests/fixtures/agent-instruction-v1/evidence/family-profiles.json"

#: The two renderings. `plain` is the shape `ollama show --modelfile` gives and
#: the shape this repository's own adapter tests already use. `annotated` adds
#: a header line and nothing else, so the blob projection of the two is
#: identical by construction and only the whole-text digest separates them.
ANNOTATION = b'# Modelfile generated by "ollama show"\n'

VERSION_OUTPUT = b"stub-runtime 1\n"

#: The stand-in runtime. It answers the two calls `_verify_profile_identity`
#: makes and nothing else, and it reads no input, opens no socket and consults
#: no model: the bytes it prints are the ones named on its command line.
STUB_SOURCE = '''import sys

command = sys.argv[1]
if command == "version":
    sys.stdout.write("stub-runtime 1\\n")
    raise SystemExit(0)
if command == "identity":
    if sys.argv[2] == "annotated":
        sys.stdout.write('# Modelfile generated by "ollama show"\\n')
    sys.stdout.write("FROM @sha256-" + sys.argv[3] + "\\n")
    raise SystemExit(0)
raise SystemExit(2)
'''


class Unproven(Exception):
    """A precondition this prover could not establish."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rendered_identity(style: str, blob: str) -> bytes:
    """The bytes the stand-in prints for one rendering and one model blob."""
    prefix = ANNOTATION if style == "annotated" else b""
    return prefix + b"FROM @sha256-" + blob.encode("ascii") + b"\n"


def pinned_evidence(name: str, relative: str) -> dict:
    """Read one committed profile file and hold it to its source pin."""
    path = ROOT / relative
    try:
        data = path.read_bytes()
    except OSError as error:
        raise Unproven(f"{relative} could not be read: {error}") from error
    expected = AI.TRUSTED_PROFILE_SHA256[name]
    if digest(data) != expected:
        raise Unproven(
            f"{relative} does not match TRUSTED_PROFILE_SHA256; this prover "
            "reads the committed profiles and will not report through a "
            "fixture it cannot recognise"
        )
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise Unproven(f"{relative} is not readable JSON: {error}") from error


def model_blobs() -> tuple[str, str]:
    """Return two different model blob digests this repository records."""
    tokenizer = pinned_evidence("tokenizer_profile", TOKENIZER_PROFILE)
    families = pinned_evidence("family_profiles", FAMILY_PROFILES)
    recorded = tokenizer.get("vocabulary_sha256")
    others = [
        profile.get("vocabulary_sha256")
        for profile in families.get("profiles", [])
        if profile.get("vocabulary_sha256") != recorded
    ]
    if not isinstance(recorded, str) or not others or not isinstance(others[0], str):
        raise Unproven(
            "the committed profiles do not record two different model blobs, "
            "so a model change cannot be told from a rendering change here"
        )
    return recorded, others[0]


def stand_in_runtime(directory: Path) -> Path:
    """Write the disposable adapter runtime and return its path."""
    path = directory / "identity-runtime.py"
    path.write_text(f"#!{sys.executable}\n" + STUB_SOURCE, encoding="utf-8")
    path.chmod(0o700)
    return path


def specimen_profile(runtime: Path, observed: tuple[str, str], recorded: tuple[str, str]) -> dict:
    """One tokenizer profile: what the runtime prints against what is recorded.

    `observed` is the rendering and blob the stand-in is told to print.
    `recorded` is the rendering and blob the profile claims. Equal pairs are an
    honest machine; a differing rendering is S3-R1-02's cosmetic change and a
    differing blob is a genuine model swap.
    """
    executable = digest(runtime.read_bytes())
    recorded_style, recorded_blob = recorded
    return {
        "id": "prove-measurement-guards",
        "executable": str(runtime),
        "executable_sha256": executable,
        "runtime_executable": str(runtime),
        "runtime_executable_sha256": executable,
        "environment_allowlist": [],
        "fixed_environment": {"PROVE_MEASUREMENT_GUARDS": "1"},
        "timeout_seconds": "60",
        "max_stdout_bytes": "4096",
        "max_stderr_bytes": "4096",
        "version_argv": ["version"],
        "version_sha256": digest(VERSION_OUTPUT),
        "identity_argv": ["identity", observed[0], observed[1]],
        "acquisition_sha256": digest(rendered_identity(recorded_style, recorded_blob)),
        "model_blobs_sha256": [recorded_blob],
        "vocabulary_sha256": recorded_blob,
    }


def observe(profile: dict) -> tuple[str, str] | None:
    """Run the shipped identity check and return its refusal, or None."""
    try:
        AI._verify_profile_identity(profile, "$.profile")
    except AI.CodecError as refusal:
        return (refusal.code, refusal.node_path)
    return None


def specimens(runtime: Path) -> dict[str, tuple[str, str] | None]:
    """Put the four specimens to the shipped function, in a fixed order."""
    recorded_blob, other_blob = model_blobs()
    plan = (
        ("honest-plain", ("plain", recorded_blob), ("plain", recorded_blob)),
        ("honest-annotated", ("annotated", recorded_blob), ("annotated", recorded_blob)),
        ("rendering-only", ("annotated", recorded_blob), ("plain", recorded_blob)),
        ("model-blob-set", ("plain", other_blob), ("plain", recorded_blob)),
    )
    return {
        name: observe(specimen_profile(runtime, observed, recorded))
        for name, observed, recorded in plan
    }


def describe(refusal: tuple[str, str] | None) -> str:
    return "accepted" if refusal is None else f"{refusal[0]} at {refusal[1]}"


def report_destination(supplied: str, case: str) -> tuple[Path, str]:
    """Resolve the report path inside this repository and read its candidate.

    The name carries the candidate and the criterion, which is the whole of
    what stops a mistyped path from overwriting one of the study's receipted
    selection reports: those are named for a selection criterion and no
    selection criterion is this case.
    """
    target = (ROOT / supplied).resolve() if not Path(supplied).is_absolute() else Path(supplied).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        raise SystemExit(f"--report must stay inside {ROOT}")
    stem = target.name
    suffix = f"--{case}.json"
    if not stem.endswith(suffix):
        raise SystemExit(f"--report must name a file ending {suffix}")
    candidate = stem[: -len(suffix)]
    if candidate not in CANDIDATES:
        raise SystemExit(f"--report names no declared candidate: {candidate}")
    return target, candidate


def scratch_directory(directory: Path) -> tuple[int, str]:
    """`mkstemp` beside the report's own destination, named for the repository's
    `dir=`-anchoring convention rather than reused from it.

    Every other module's `scratch_directory` anchors at the fixed, gitignored
    top-level `tmp/`, because their scratch is a throwaway fixture with nowhere
    else to live. This one is not that: the staging file has to sit in the same
    directory as the report `--report` names, because that is what makes the
    following `os.replace` an atomic rename rather than a cross-directory copy.
    The destination is `.hexaemeron/design/`, itself entirely gitignored, so no
    transient entry reaches `git status` either way. This function exists so
    the one `dir=` call this module makes is named the way the repository's
    structural scratch-quiescence check requires, and is the only such call.
    """
    return tempfile.mkstemp(dir=str(directory), prefix=".report-")


def write_report(target: Path, candidate: str, command: str) -> None:
    """Write the closed design report through a temporary file and a rename."""
    payload = {
        "schema": REPORT_SCHEMA,
        "candidate": candidate,
        "criterion": CRITERION,
        "value": True,
        "unit": UNIT,
        "command": command,
        "exit": 0,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, staged = scratch_directory(target.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(body)
        os.replace(staged, target)
    except OSError:
        try:
            os.unlink(staged)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    """Prove one conformance criterion and write its report, or refuse."""
    parser = argparse.ArgumentParser(description="Prove the skills#1199 measurement guards.")
    parser.add_argument("--case", required=True, help="the conformance criterion to prove")
    parser.add_argument("--report", required=True, help="where to write the design report")
    arguments = parser.parse_args(argv)

    if arguments.case != CRITERION:
        print(f"unknown case: {arguments.case}", file=sys.stderr)
        return 2
    target, candidate = report_destination(arguments.report, arguments.case)
    command = (
        f"python3 tests/prove_measurement_guards.py --case {arguments.case} "
        f"--report {arguments.report}"
    )

    try:
        with tempfile.TemporaryDirectory() as directory:
            observed = specimens(stand_in_runtime(Path(directory)))
    except Unproven as unproven:
        print(f"unproven: {unproven}", file=sys.stderr)
        return 3

    for name in ("honest-plain", "honest-annotated", "rendering-only", "model-blob-set"):
        print(f"{name:18s} {describe(observed[name])}")

    for name in ("honest-plain", "honest-annotated"):
        if observed[name] is not None:
            print(
                f"unproven: {name} was refused with {describe(observed[name])}; the "
                "bytes this prover expects are not the bytes the stand-in produced, "
                "so nothing here would be measuring the guard",
                file=sys.stderr,
            )
            return 3

    rendering = observed["rendering-only"]
    model = observed["model-blob-set"]
    if rendering is None or model is None:
        print(
            "refused: a changed identity was accepted, so the adapter identity "
            "is not checked at all",
            file=sys.stderr,
        )
        return 1
    if rendering == model:
        print(
            f"refused: both causes reach {describe(rendering)}, so a rendering "
            "change and a model change cannot be told apart",
            file=sys.stderr,
        )
        return 1

    write_report(target, candidate, command)
    print(
        f"{CRITERION}: a rendering change reaches {describe(rendering)} and a "
        f"model change reaches {describe(model)}; wrote {target}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
