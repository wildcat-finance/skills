"""Compare two final-argv research constructions, without editing the product."""
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch
import fcntl
import hashlib
import json
import platform
import statistics
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "plugins/hexaemeron/skills/fiat/scripts"))
from checkpoint_authority import demo, native_io, network, signatures
from checkpoint_authority.canonical import Refusal

POLICY = (HERE.parent / "linux-feasibility/x86_64-deny-network.bpf").read_bytes()
LAUNCHER = "/usr/bin/bwrap"
LAUNCHER_SHA = hashlib.sha256(Path(LAUNCHER).read_bytes()).hexdigest()
PREFIX = ["--unshare-net", "--unshare-pid", "--bind", "/", "/",
          "--dev-bind", "/dev", "/dev", "--die-with-parent", "--new-session", "--cap-drop", "ALL"]
PYTHON_PATH = str(Path(sys.executable).resolve())
PYTHON = native_io.NativeTool("python", PYTHON_PATH, hashlib.sha256(Path(PYTHON_PATH).read_bytes()).hexdigest())
COSIGN_PATH = "/tmp/fiat-native-admission-test-tools-h7vx7_f8/bin/cosign"
COSIGN = signatures.ToolPin("cosign", COSIGN_PATH, hashlib.sha256(Path(COSIGN_PATH).read_bytes()).hexdigest())

@dataclass(frozen=True)
class Wrapped:
    path: str
    sha256: str
    inner: object

    def check(self):
        self.inner.check()
        if native_io.hash_file(self.path, native_io.FILE_MAX)[0] != self.sha256:
            raise RuntimeError("research launcher changed")

class Boundary:
    def __init__(self, candidate):
        self.candidate = candidate
        self.policy = POLICY if candidate == "bubblewrap-seccomp" else b""
        self.prefix = PREFIX + (["--seccomp", "0"] if self.policy else []) + ["--"]

    def run(self, pin, args, directory, *, timeout):
        return signatures._run(Wrapped(LAUNCHER, LAUNCHER_SHA, pin),
                               [*self.prefix, pin.path, *args], directory,
                               input_bytes=self.policy, timeout=timeout)

    def probe(self, directory):
        result = self.run(PYTHON, ["-I", "-c", network.PROBE], directory, timeout=10)
        if result[0] != 0 or result[1] != network.PROBE_OUTPUT:
            raise Refusal("network-denial-probe", "research")
        return {"mechanism": "RESEARCH-" + self.candidate, "launcher_sha256": LAUNCHER_SHA,
                "policy_sha256": hashlib.sha256(self.policy).hexdigest(),
                "probe_sha256": hashlib.sha256(network.PROBE.encode()).hexdigest(),
                "probe_exit": 0, "probe_operations": 4}

def observe(boundary, source, directory, timeout=10):
    start = time.monotonic()
    try:
        status, out, err = boundary.run(PYTHON, ["-I", "-c", source], directory, timeout=timeout)
        row = {"exit": status, "stdout": out.decode(), "stderr": err.decode()}
    except Refusal as exc:
        row = {"refusal": exc.code}
    row["elapsed_ms"] = round(1000 * (time.monotonic() - start), 3)
    return row

def lock_released(directory):
    with (directory / "descendant.lock").open("rb") as stream:
        deadline = time.monotonic() + 2
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    return False
                time.sleep(0.01)

descendant_probe = "import subprocess,sys; p=subprocess.run([sys.executable,'-I','-c',%r],capture_output=True); sys.stdout.buffer.write(p.stdout); sys.stderr.buffer.write(p.stderr); sys.exit(p.returncode)" % network.PROBE
leader_exit = """import fcntl,os,time
r,w=os.pipe()
if os.fork():
    os.close(w); os.read(r,1); print('leader-exiting',flush=True); os._exit(0)
os.close(r)
with open('descendant.lock','w') as held:
    fcntl.flock(held,fcntl.LOCK_EX); os.write(w,b'1'); time.sleep(20)
"""
timeout_probe = leader_exit.replace("print('leader-exiting',flush=True); os._exit(0)", "time.sleep(20)")

observations = []
for candidate in ("bubblewrap-netns", "bubblewrap-seccomp"):
    boundary = Boundary(candidate)
    row = {"candidate": candidate, "argv_prefix": [LAUNCHER, *boundary.prefix],
           "policy_bytes": len(boundary.policy), "policy_sha256": hashlib.sha256(boundary.policy).hexdigest()}
    with tempfile.TemporaryDirectory(prefix="fiat-1794-study-selection-") as temporary:
        directory = Path(temporary)
        row["direct"] = observe(boundary, network.PROBE, directory)
        row["descendant"] = observe(boundary, descendant_probe, directory)
        row["launch_samples"] = [observe(boundary, "print('ready')", directory) for _ in range(3)]
        row["launch_median_ms"] = statistics.median(item["elapsed_ms"] for item in row["launch_samples"])
        row["leader_exit"] = observe(boundary, leader_exit, directory, timeout=0.3)
        row["leader_exit"]["descendant_lock_released"] = lock_released(directory)
        row["timeout"] = observe(boundary, timeout_probe, directory, timeout=0.3)
        row["timeout"]["descendant_lock_released"] = lock_released(directory)
        row["output_limit"] = observe(boundary, "import os; os.write(1,b'x'*70000)", directory)
    start = time.monotonic()
    try:
        with patch.object(network, "prepare", return_value=boundary):
            result = demo.interoperability(REPO, COSIGN)
        row["interoperability"] = {"passed": result["agreed"], "result": result}
    except Refusal as exc:
        row["interoperability"] = {"passed": False, "refusal": exc.code}
    row["interoperability"]["elapsed_ms"] = round(1000 * (time.monotonic() - start), 3)
    observations.append(row)

report = {"schema": "fiat-1794-selection-probe/v1", "command": "python3 .hexaemeron/sources/study/selection_probe.py",
          "base": "66f52785813a8453e7c7d54f2371aa8f6e465640", "python": sys.version,
          "platform": platform.platform(), "machine": platform.machine(),
          "launcher_sha256": LAUNCHER_SHA, "cosign_sha256": COSIGN.sha256,
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "scope": "Research only: in-memory boundary substitution around unchanged native runner and demo. No product conformance or macOS execution.",
          "observations": observations}
(HERE / "selection-probe.json").write_text(json.dumps(report, indent=2) + "\n")
for row in observations:
    print(json.dumps({key: row[key] for key in ("candidate", "direct", "descendant", "policy_bytes", "launch_median_ms", "leader_exit", "timeout", "output_limit", "interoperability")}, sort_keys=True))
