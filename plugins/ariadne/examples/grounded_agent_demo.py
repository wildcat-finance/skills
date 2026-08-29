#!/usr/bin/env python3
"""Rebuild, capture, verify, and tamper the grounded-agent example offline."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARIADNE = ROOT / "plugins" / "ariadne" / "scripts" / "ariadne.py"
BEREAN_REBUILD = (
    ROOT / "plugins" / "berean" / "examples" / "goldfinch-demo-v0" / "rebuild.py"
)
BEREAN_RELEASE = BEREAN_REBUILD.parent / "release"
LAZARUS_READS = (
    ROOT
    / "plugins"
    / "lazarus"
    / "examples"
    / "goldfinch-v0-release"
    / "fixture"
    / "rpc.jsonl"
)
SHIPPED = HERE / "goldfinch-demo-v0-agent.json"
TAMPERED = HERE / "tampered" / "goldfinch-demo-v0-agent-policy-byte-changed.json"

NAME = "goldfinch-demo-v0"
FIRST_CAPTURE_REASON = "first Ariadne capture of this Berean release"
PRODUCER_COMMAND = [
    "python3",
    "plugins/berean/examples/goldfinch-demo-v0/rebuild.py",
]
EXPECTED_RELEASE_DIGEST = (
    "7b104766e0df92de73d2b2cf98379e417151c0f824ada105c37eafdd367a7e8c"
)
EXPECTED_STATEMENT_SHA256 = (
    "03fb54176a417248447a5e92ce702acce229855b0378215fd68a4286130165bc"
)
EXPECTED_SUBJECTS = 12
EXPECTED_DECLARED_BYTES = 93165


class DemoError(Exception):
    """A stage failed to prove the boundary it names."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def stage(name):
    print("\n== %s ==" % name)


def run(argv, environment, expected=0):
    completed = subprocess.run(
        [str(part) for part in argv],
        cwd=str(ROOT),
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=60,
        check=False,
    )
    if completed.returncode != expected:
        raise DemoError(
            "%s exited %d rather than %d: %s"
            % (
                Path(str(argv[1])).name if len(argv) > 1 else str(argv[0]),
                completed.returncode,
                expected,
                (completed.stderr or completed.stdout).strip(),
            )
        )
    return completed


def release_files(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def replace_one_byte(path, old, new):
    if len(old) != len(new):
        raise DemoError("one-byte mutation changed the specimen length")
    data = path.read_bytes()
    if data.count(old) != 1:
        raise DemoError("one-byte mutation target is not unique in %s" % path.name)
    changed = data.replace(old, new)
    differing = sum(left != right for left, right in zip(data, changed))
    if differing != 1:
        raise DemoError("mutation changed %d bytes rather than one" % differing)
    path.write_bytes(changed)


def capture_command(release, output):
    return [
        sys.executable,
        ARIADNE,
        "capture-grounded-agent",
        "--release",
        release,
        "--name",
        NAME,
        "--producer-tool",
        "berean",
        "--producer-version",
        "0.2.0",
        "--producer-command",
        PRODUCER_COMMAND[0],
        "--producer-command",
        PRODUCER_COMMAND[1],
        "--first-capture-reason",
        FIRST_CAPTURE_REASON,
        "--output",
        output,
    ]


def capture_refusal(source, holder, label, mutate, expected, environment):
    lane = holder / label
    release = lane / "release"
    output = lane / "statement.json"
    shutil.copytree(source, release)
    mutate(release)
    completed = run(capture_command(release, output), environment, expected=2)
    if output.exists():
        raise DemoError("%s refusal exposed an output" % label)
    message = completed.stderr.strip()
    wanted = "capture failed: %s" % expected
    if message != wanted:
        raise DemoError("%s refusal was %r, expected %r" % (label, message, wanted))
    print("%s: %s" % (label, message))


def network_guard(directory):
    guard = directory / "network-guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import socket\n"
        "def _blocked(*args, **kwargs):\n"
        "    raise RuntimeError('network disabled by grounded-agent demo')\n"
        "socket.socket = _blocked\n"
        "socket.create_connection = _blocked\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(guard) + (os.pathsep + existing if existing else "")
    return environment


def main():
    for required in (ARIADNE, BEREAN_REBUILD, BEREAN_RELEASE, LAZARUS_READS, SHIPPED, TAMPERED):
        if not required.exists():
            raise DemoError("required sibling artefact is absent: %s" % required)

    with tempfile.TemporaryDirectory(prefix="ariadne-grounded-agent-") as temporary:
        holder = Path(temporary)
        environment = network_guard(holder)

        stage("rebuild the preserved Berean release")
        source_reads = (BEREAN_RELEASE / "reads.jsonl").read_bytes()
        if source_reads != LAZARUS_READS.read_bytes():
            raise DemoError("Berean reads differ from the preserved Lazarus bytes")
        release = holder / "rebuilt" / "release"
        release.mkdir(parents=True)
        (release / "reads.jsonl").write_bytes(source_reads)
        rebuilt = run(
            [sys.executable, BEREAN_REBUILD, "--release", release],
            environment,
        )
        if release_files(release) != release_files(BEREAN_RELEASE):
            raise DemoError("the release rebuilt from reads.jsonl differs from the committed tree")
        release_document = json.loads((release / "release.json").read_text(encoding="utf-8"))
        if release_document["release_digest"] != EXPECTED_RELEASE_DIGEST:
            raise DemoError("the rebuilt semantic release identity drifted")
        print(rebuilt.stdout.strip())
        print("preserved reads: %s" % release_document["reads"]["sha256"])
        print(
            "Berean regenerated its seven-case report; Ariadne binds those bytes "
            "without running run-evals or regrading them"
        )

        stage("capture twice and compare exact bytes")
        first = holder / "capture-1.json"
        second = holder / "capture-2.json"
        run(capture_command(release, first), environment)
        run(capture_command(release, second), environment)
        first_bytes = first.read_bytes()
        if first_bytes != second.read_bytes() or first_bytes != SHIPPED.read_bytes():
            raise DemoError("two fresh captures or the committed statement differ")
        if sha256(first_bytes) != EXPECTED_STATEMENT_SHA256:
            raise DemoError("the committed statement digest drifted")
        statement = json.loads(first_bytes.decode("utf-8"))
        declared_bytes = sum(
            component["bytes"]
            for component in statement["predicate"]["given"]["corpus"]["components"]
        )
        declared_bytes += statement["predicate"]["release"]["document"]["bytes"]
        declared_bytes += statement["predicate"]["given"]["corpus"]["manifest"]["bytes"]
        declared_bytes += statement["predicate"]["given"]["reads"]["component"]["bytes"]
        declared_bytes += sum(
            component["bytes"] for component in statement["predicate"]["produced"]["answers"]
        )
        declared_bytes += sum(
            statement["predicate"]["produced"]["evaluations"][name]["bytes"]
            for name in ("cases", "report")
        )
        declared_bytes += statement["predicate"]["produced"]["promotion"]["component"]["bytes"]
        if len(statement["subject"]) != EXPECTED_SUBJECTS:
            raise DemoError("the captured subject count drifted")
        if declared_bytes != EXPECTED_DECLARED_BYTES:
            raise DemoError("the captured byte count drifted")
        print("statement sha256: %s" % sha256(first_bytes))
        print("subjects: %d; declared bytes: %d" % (len(statement["subject"]), declared_bytes))

        stage("verify all registered gates offline")
        verified = run([sys.executable, ARIADNE, "verify", first], environment)
        lines = verified.stdout.strip().splitlines()
        gate_lines = [line for line in lines if line.startswith("gate ")]
        check_lines = [line for line in lines if line.startswith("check ")]
        if len(gate_lines) != 7 or len(check_lines) != 6:
            raise DemoError("verification did not emit seven gates and six checks")
        if any("FAIL" in line or "unchecked" in line.lower() for line in gate_lines + check_lines):
            raise DemoError("verification left a gate failed or unchecked")
        print("\n".join(gate_lines + check_lines))

        stage("verify the shipped one-byte tamper")
        tampered = run(
            [sys.executable, ARIADNE, "verify", TAMPERED, "--json"],
            environment,
            expected=1,
        )
        tampered_report = json.loads(tampered.stdout)
        failed = [entry["name"] for entry in tampered_report["gates"] if not entry["passed"]]
        if failed != ["release-digest"] or tampered_report["unchecked"]:
            raise DemoError("the one-byte peer did not fail only release-digest")
        clean_bytes = SHIPPED.read_bytes()
        peer_bytes = TAMPERED.read_bytes()
        if len(clean_bytes) != len(peer_bytes):
            raise DemoError("the one-byte peer changed length")
        if sum(left != right for left, right in zip(clean_bytes, peer_bytes)) != 1:
            raise DemoError("the one-byte peer does not differ by exactly one byte")
        print("check release-digest: refused; unchecked: none")

        stage("mutate each Berean evidence class independently")

        def identity_mutation(root):
            replace_one_byte(
                root / "release.json",
                b'"release_version":"goldfinch-demo-v0"',
                b'"release_version":"goldfinch-demo-w0"',
            )

        def input_mutation(root):
            path = root / "reads.jsonl"
            data = path.read_bytes()
            if not data.endswith(b"\n"):
                raise DemoError("reads.jsonl has no final LF to mutate")
            path.write_bytes(data[:-1] + b" ")

        def output_mutation(root):
            path = root / "answers" / "grounded.json"
            data = path.read_bytes()
            if not data.endswith(b"\n"):
                raise DemoError("grounded answer has no final LF to mutate")
            path.write_bytes(data[:-1] + b" ")

        def promotion_mutation(root):
            release_json = json.loads((root / "release.json").read_text(encoding="utf-8"))
            digest = release_json["evals"]["report_sha256"].encode("ascii")
            replacement = (b"0" if digest[:1] != b"0" else b"1") + digest[1:]
            replace_one_byte(root / "promotions.jsonl", digest, replacement)

        capture_refusal(
            release,
            holder,
            "identity",
            identity_mutation,
            "release_digest does not match the canonical identity fields",
            environment,
        )
        capture_refusal(
            release,
            holder,
            "input",
            input_mutation,
            "release reads does not match its declared sha256",
            environment,
        )
        capture_refusal(
            release,
            holder,
            "output",
            output_mutation,
            "release answer 1 does not match its declared sha256",
            environment,
        )
        capture_refusal(
            release,
            holder,
            "promotion",
            promotion_mutation,
            "promotion report digest is not the release report",
            environment,
        )

        print("\nmodel execution: none; network: disabled; every stage held")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (DemoError, OSError, ValueError, json.JSONDecodeError) as error:
        print("demo failed: %s" % error, file=sys.stderr)
        sys.exit(1)
