#!/usr/bin/env python3
"""Resolve one conformance cell of the issue 1891 design record.

Run from the root of the run worktree, after the step that owns the cell:

    python3 .hexaemeron/design/conformance.py <criterion> --candidate range-streamed-logs

Only the selected candidate carries cases; any other refuses by name with exit
2 before anything is read. The ten cells resolve three ways.

Five cells load named tests that Steps 2 to 4 create. A cell whose test module
does not exist yet refuses by name with exit 1. Otherwise loading is half the
check: an identifier that does not resolve, a name that loads no test, a run
that executes fewer tests than it names, a failure or an error each refuse. A
skip refuses too, unless its reason names one of the four
`ALEXANDRIA_WILDCAT_*` variables and that variable is unset.
`streamed-check-keeps-every-refusal` also runs five existing check modules
whole and refuses unless each file is byte for byte the base commit's.

Four cells measure with `/usr/bin/time -l`, with `/usr/bin/uptime`'s load
averages recorded beside every run:

- `todays-model-projects-past-the-host` extracts the base commit's
  `plugins/alexandria` with `git archive`, checks each extracted file against
  its blob, and uses that tree to generate and build three releases with
  `synthetic_interval.py` beside this script. It runs the tree's `check` three
  times on each, fits the median peak against release bytes and release bytes
  against shards, and picks the fewest shards whose projected peak is at
  least 1.1 times the host's 137,438,953,472 bytes. It refuses by name when
  the disk cannot hold 2.5 times that release. The base `check` never runs on
  the acceptance release;
- `acceptance-release-within-stated-peak` generates the acceptance release
  from the parameters that cell recorded, and measures the working tree's
  `build` and `check` on it;
- `v2-check-peak-halved` and `v2-check-cpu-within-budget` run the working
  tree's `check` three times on the preserved V2 release
  `ALEXANDRIA_WILDCAT_V2_RELEASE` names, after verifying its bytes.

`pinned-release-identities-reproduce` rebuilds and verifies every pinned
demonstration, rebuilds the preserved V2 staging tree inside
`wildcat_registry.checking_release()`, checks both preserved releases and
verifies the two committed releases, comparing each identifier with a
constant below, never with a file a step could edit. The estates
demonstration counts only once it builds: while it refuses with the #2023
registry message, the cell records that refusal and excludes it.

Every generated or extracted tree lives under one fresh directory the cell
creates in `--scratch` (the system temporary directory by default) and removes
when it finishes. On success the cell writes one closed
`protasis-design-report/v1` object to
`.hexaemeron/design/reports/conformance/<candidate>-<criterion>.json`, and a
measured cell also writes the figures behind it to
`.hexaemeron/design/evidence/<candidate>-<criterion>.json`. Both are
create-only: an existing file is compared byte for byte and never replaced.
`--no-report` prints the observation and writes neither. The acceptance cell
reads the parameters and planned bytes, and nothing else, from the
`todays-model-projects-past-the-host` evidence, and checks each as a whole
number. No controller state is read.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import statistics
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CANDIDATE = "range-streamed-logs"
BASE = "150943da240837040478a76c3611d150fa04f2b6"
PLUGIN = "plugins/alexandria"
GENERATOR = HERE / "synthetic_interval.py"
HOST_BYTES = 137_438_953_472
HOST_MARGIN = 1.1
STATED_PEAK = 4_294_967_296
V2_PEAK_CEILING = 620_273_664
V2_CPU_CEILING_MS = 9_400
DISK_HEADROOM = 2.5
MAX_SHARDS = 4_094
# The three generated releases today's model is fitted over: the same logs per
# shard, the shard count doubling.
MODEL_SHARDS = (8, 16, 32)
MODEL_LOGS_PER_SHARD = 15_000
RUNS = 3
TIMEOUT = 3_600
FAILED = "unittest.loader._FailedTest"
VARIABLES = ("ALEXANDRIA_WILDCAT_V1_STAGING", "ALEXANDRIA_WILDCAT_V2_STAGING",
             "ALEXANDRIA_WILDCAT_V1_RELEASE", "ALEXANDRIA_WILDCAT_V2_RELEASE")
V1_RELEASE_ID = "sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69"
V2_RELEASE_ID = "sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3"
KNOWN_2023 = "Wildcat V2 registry bytes do not match the pinned registry"

WALK = "tests.test_log_walk"
STREAMED_CHECK = "tests.test_streamed_check"
STREAMED_BUILD = "tests.test_streamed_build"
# criterion: (the test module the cell needs, the names it loads, the existing
# modules it runs whole and requires unchanged from the base commit)
TEST_CELLS = {
    "walk-matches-whole-list-derivation": (WALK, (
        f"{WALK}.WalkEquivalenceTests", f"{WALK}.WalkRefusalTests",
        f"{WALK}.TransactionKeyTests", f"{WALK}.OpeningLogTests",
    ), ()),
    # tests.test_log_attribution_parts runs whole and must pass, but is not
    # held unchanged from the base: runbook amendment 1 rewrites its one
    # whole-list attribute_logs call assertion, which streaming replaces.
    "streamed-check-keeps-every-refusal": (STREAMED_CHECK, (
        f"{STREAMED_CHECK}.RefusalOrderTests", f"{STREAMED_CHECK}.SecondReadTests",
        "tests.test_log_attribution_parts",
    ), (
        "tests.test_usdc_interval",
        "tests.test_check_verified_reads", "tests.test_wildcat_venue",
        "tests.test_release_limits",
    )),
    "check-peak-independent-of-size": (STREAMED_CHECK, (
        f"{STREAMED_CHECK}.CheckPeakTests.test_the_traced_peak_does_not_grow_with_the_release",
    ), ()),
    "build-peak-independent-of-size": (STREAMED_BUILD, (
        f"{STREAMED_BUILD}.BuildPeakTests.test_the_traced_peak_does_not_grow_with_the_release",
    ), ()),
    "killed-build-installs-nothing": (STREAMED_BUILD, (
        f"{STREAMED_BUILD}.KilledBuildTests",
    ), ()),
}
MEASURED = {
    "todays-model-projects-past-the-host": "bytes",
    "acceptance-release-within-stated-peak": "bytes",
    "v2-check-peak-halved": "bytes",
    "v2-check-cpu-within-budget": "milliseconds",
}
PINNED_CELL = "pinned-release-identities-reproduce"
CRITERIA = (*TEST_CELLS, *MEASURED, PINNED_CELL)
PINNED_DEMOS = {
    "usdc-interval-v0": {
        "sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa",
    },
    "usdc-interval-epochs-v0": {
        "sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036",
        "sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a",
        "sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32",
    },
    "usdc-interval-live-v0": {
        "sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32",
    },
    "credit-history-v0": {
        "sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec",
    },
    "wildcat-v1-interval-v0": {V1_RELEASE_ID},
}
ESTATES_DEMO = ("wildcat-estates-interval-v0", {
    V1_RELEASE_ID, V2_RELEASE_ID,
    "sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a",
})
PINNED_RELEASES = {
    "compound-v3-phase0-v0":
        "sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab",
    "proof-backed-state-v0":
        "sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f",
}
IDENTIFIER = re.compile(r"sha256:[0-9a-f]{64}")
# The V2 demonstration's build() inside checking_release(), in a fresh
# interpreter: argv[1] is the demonstration, argv[2] the fresh output.
V2_REBUILD = (
    "import importlib.util, json, sys\n"
    "from pathlib import Path\n"
    "spec = importlib.util.spec_from_file_location('wildcat_v2_demo', sys.argv[1])\n"
    "demo = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(demo)\n"
    "from alexandria_lib import wildcat_registry\n"
    "with wildcat_registry.checking_release():\n"
    "    summary = demo.build(Path(sys.argv[2]))\n"
    "print(summary['release_id'])\n"
)


class Refusal(Exception):
    pass


# -- child processes: fixed argv, no shell, a minimal environment ----------

def child_environment(extra=()) -> dict:
    environment = {"PATH": os.environ.get("PATH", os.defpath), "NO_COLOR": "1",
                   "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C"}
    for key in ("HOME", *extra):
        if key in os.environ:
            environment[key] = os.environ[key]
    return environment


def run(argv: list, *, cwd: Path, extra=(), timeout=TIMEOUT) -> tuple[int, str, str]:
    try:
        result = subprocess.run(  # phylax: allow subprocess: fixed interpreter, git, time and uptime argv, no shell
            argv, capture_output=True, timeout=timeout, env=child_environment(extra),
            cwd=str(cwd), check=False,
        )
    except subprocess.TimeoutExpired:
        raise Refusal(f"{Path(argv[0]).name} did not finish within {timeout} seconds") from None
    except OSError as error:
        raise Refusal(f"{Path(argv[0]).name} could not start: {type(error).__name__}: "
                      f"{error.strerror or error}") from None
    return (result.returncode, result.stdout.decode("utf-8", "replace"),
            result.stderr.decode("utf-8", "replace"))


def load_averages(cwd: Path) -> list:
    code, stdout, _ = run(["/usr/bin/uptime"], cwd=cwd, timeout=60)
    found = re.search(r"load averages?: ([0-9.]+),? ([0-9.]+),? ([0-9.]+)", stdout)
    if code != 0 or found is None:
        raise Refusal("uptime printed no load averages")
    return [float(value) for value in found.groups()]


def timed(argv: list, *, cwd: Path, extra=()) -> dict:
    """One `/usr/bin/time -l` run: exit, stdout, peak, seconds, and the load before it."""
    loads = load_averages(cwd)
    code, stdout, stderr = run(["/usr/bin/time", "-l", *argv], cwd=cwd, extra=extra)
    peak = re.search(r"^\s*(\d+)\s+maximum resident set size$", stderr, re.M)
    times = re.search(r"^\s*([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys$", stderr, re.M)
    if peak is None or times is None:
        raise Refusal(f"/usr/bin/time printed no peak for {Path(argv[1]).name}: "
                      + stderr.strip()[-300:])
    real, user, system = (float(value) for value in times.groups())
    return {"exit": code, "load_averages": loads, "maximum_resident_set_bytes": int(peak.group(1)),
            "real_seconds": real, "user_seconds": user, "system_seconds": system,
            "cpu_milliseconds": round((user + system) * 1000), "stdout": stdout,
            "stderr": stderr[: times.start()].strip()[-400:] if code else ""}


# -- git, isolated from the caller's configuration --------------------------

def git(repository: Path, *argv: str) -> bytes:
    home = tempfile.mkdtemp(prefix="fiat-1891-git-home-")
    try:
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("GIT_")}
        environment.update(HOME=home, XDG_CONFIG_HOME=home, GIT_CONFIG_NOSYSTEM="1",
                           GIT_CONFIG_GLOBAL=os.devnull, GIT_ATTR_NOSYSTEM="1", LC_ALL="C")
        try:
            result = subprocess.run(  # phylax: allow subprocess: fixed git argv, no shell
                ["git", "-c", "color.ui=never", "-c", f"core.attributesFile={os.devnull}",
                 "-C", str(repository), *argv],
                capture_output=True, timeout=300, env=environment, check=False,
            )
        except subprocess.TimeoutExpired:
            raise Refusal(f"git {argv[0]} did not finish within 300 seconds") from None
        except OSError as error:
            raise Refusal(f"git {argv[0]} could not start: {type(error).__name__}: "
                          f"{error.strerror or error}") from None
    finally:
        shutil.rmtree(home, ignore_errors=True)
    if result.returncode != 0:
        raise Refusal(f"git {' '.join(argv[:2])} failed: "
                      + result.stderr.decode("utf-8", "replace").strip()[:200])
    return result.stdout


def base_blobs(repository: Path, paths) -> dict:
    listing = git(repository, "ls-tree", "-r", "-z", BASE, "--", *paths).decode("utf-8")
    blobs = {}
    for entry in filter(None, listing.split("\0")):
        header, _, name = entry.partition("\t")
        mode, kind, oid = header.split(" ")
        if kind != "blob" or mode not in ("100644", "100755"):
            raise Refusal(f"the base commit holds {name} as {kind} {mode}, not a file")
        blobs[name] = oid
    return blobs


def blob_id(data: bytes, oid: str) -> str:
    return (hashlib.sha256 if len(oid) == 64 else hashlib.sha1)(
        b"blob %d\0" % len(data) + data).hexdigest()


def extract_base(repository: Path, destination: Path) -> Path:
    """The base commit's plugins/alexandria, every file checked against its blob."""
    data = git(repository, "archive", "--format=tar", BASE, PLUGIN)
    try:
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(destination, filter="data")
    except tarfile.TarError as error:
        raise Refusal("git archive of the base commit could not be read: "
                      + str(error).replace("\n", " ")[:200]) from None
    expected = base_blobs(repository, [PLUGIN])
    found = {path.relative_to(destination).as_posix()
             for path in destination.rglob("*") if path.is_file() or path.is_symlink()}
    if found != set(expected):
        raise Refusal("git archive of the base commit is not the base commit's "
                      f"{PLUGIN}: {len(set(expected) - found)} file(s) missing, "
                      f"{len(found - set(expected))} extra")
    for name, oid in expected.items():
        path = destination / name
        if path.is_symlink() or blob_id(path.read_bytes(), oid) != oid:
            raise Refusal(f"git archive of the base commit changed {name}")
    return destination / PLUGIN


# -- test cells --------------------------------------------------------------

def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def admitted_skip(reason: str) -> bool:
    return any(variable in reason and not os.environ.get(variable) for variable in VARIABLES)


def run_tests(names) -> tuple[bool, dict]:
    loader = unittest.TestLoader()
    loaded = {name: list(flatten(loader.loadTestsFromName(name))) for name in names}
    suite = unittest.TestSuite(unittest.TestSuite(group) for group in loaded.values())
    cases = [case for group in loaded.values() for case in group]
    empty = sorted(name for name, group in loaded.items() if not group)
    unresolved = sorted({case.id() for case in cases if case.id().startswith(FAILED)})
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    refused_skips = [case.id() for case, reason in result.skipped if not admitted_skip(reason)]
    observed = {"tests_run": result.testsRun, "failures": len(result.failures),
                "errors": len(result.errors), "skipped": len(result.skipped),
                "refused_skips": refused_skips, "loader_errors": len(loader.errors),
                "unresolved": unresolved, "empty": empty}
    passed = (not unresolved and not empty and not loader.errors
              and result.testsRun >= len(names)
              and result.testsRun > 0 and result.wasSuccessful() and not refused_skips
              and not result.expectedFailures)
    if not passed:
        observed["detail"] = stream.getvalue()[-4000:]
    return passed, observed


def test_cell(repository: Path, criterion: str) -> tuple[bool, dict]:
    module, names, unchanged = TEST_CELLS[criterion]
    package = repository / PLUGIN
    path = package / (module.replace(".", "/") + ".py")
    if not path.is_file():
        raise Refusal(f"{criterion} loads {PLUGIN}/{module.replace('.', '/')}.py, "
                      "which does not exist yet")
    observed = {"criterion": criterion}
    if unchanged:
        relative = [f"{PLUGIN}/{name.replace('.', '/')}.py" for name in unchanged]
        blobs = base_blobs(repository, relative)
        changed = sorted(name for name in relative if name not in blobs
                         or blob_id((repository / name).read_bytes(), blobs[name]) != blobs[name])
        observed["changed_from_base"] = changed
        if changed:
            return False, observed
    sys.path.insert(0, str(package / "scripts"))
    sys.path.insert(0, str(package))
    passed, tests = run_tests(names)
    observed["named"] = tests
    if unchanged and passed:
        passed, whole = run_tests(unchanged)
        observed["unchanged_modules"] = whole
    return passed, observed


# -- measured cells ----------------------------------------------------------

def generate(repository: Path, output: Path, parameters: dict, *, build: bool,
             package: Path | None = None) -> dict:
    argv = [sys.executable, str(GENERATOR), "--output", str(output)]
    for name, value in sorted(parameters.items()):
        argv += [f"--{name.replace('_', '-')}", str(value)]
    if build:
        argv.append("--build")
    if package is not None:
        argv += ["--package", str(package)]
    code, stdout, stderr = run(argv, cwd=repository)
    if code != 0:
        raise Refusal("the generator refused: " + stderr.strip()[-400:])
    return json.loads(stdout)


def fit(points) -> tuple[float, float]:
    """Least-squares intercept and slope of y on x."""
    xs, ys = [x for x, _ in points], [y for _, y in points]
    mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
    spread = sum((x - mean_x) ** 2 for x in xs)
    if spread == 0:
        raise Refusal("the model's releases do not differ in size")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / spread
    return mean_y - slope * mean_x, slope


def free_disk(path: Path) -> int:
    return shutil.disk_usage(path).free


def estimated_bytes(parameters: dict) -> int:
    """The generator's own upper estimate, which its disk refusal uses."""
    spec = importlib.util.spec_from_file_location("synthetic_interval_estimate", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    writes_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes_bytecode
    return module.Parameters(**parameters).planned_bytes()


def todays_model(repository: Path, scratch: Path) -> tuple[bool, int, dict]:
    base = extract_base(repository, scratch / "base")
    check = base / "scripts/usdc_interval.py"
    sizes = []
    for shards in MODEL_SHARDS:
        parameters = {"shards": shards, "logs_per_shard": MODEL_LOGS_PER_SHARD}
        output = scratch / f"model-{shards}"
        made = generate(repository, output, parameters, build=True, package=base)
        runs = []
        for _ in range(RUNS):
            measured = timed([sys.executable, str(check), "check", made["release"]],
                             cwd=scratch)
            reported = IDENTIFIER.findall(measured.pop("stdout"))
            if measured["exit"] != 0 or made["release_id"] not in reported:
                raise Refusal(f"the base check of the {shards}-shard release did not return "
                              f"{made['release_id']}: {measured['stderr']}")
            runs.append(measured)
        shutil.rmtree(output)
        sizes.append({"parameters": parameters, "release_id": made["release_id"],
                      "release_bytes": made["release_bytes"], "runs": runs,
                      "median_peak": statistics.median(
                          run["maximum_resident_set_bytes"] for run in runs)})
    intercept, slope = fit([(size["release_bytes"], size["median_peak"]) for size in sizes])
    fixed, per_shard = fit([(size["parameters"]["shards"], size["release_bytes"])
                            for size in sizes])
    if slope <= 0 or per_shard <= 0:
        raise Refusal("today's model does not grow with the release")
    target = HOST_MARGIN * HOST_BYTES
    shards = max(1, math.ceil(((target - intercept) / slope - fixed) / per_shard))
    if shards > MAX_SHARDS:
        raise Refusal(f"the acceptance release needs {shards} shards of "
                      f"{MODEL_LOGS_PER_SHARD} logs, above the generator's {MAX_SHARDS}")
    acceptance = {"shards": shards, "logs_per_shard": MODEL_LOGS_PER_SHARD}
    planned = math.ceil(fixed + per_shard * shards)
    projected = round(intercept + slope * planned)
    estimate = estimated_bytes(acceptance)
    needed = math.ceil(DISK_HEADROOM * max(planned, estimate))
    free = free_disk(scratch)
    evidence = {
        "acceptance": {"parameters": acceptance, "planned_release_bytes": planned,
                       "generator_estimate_bytes": estimate, "projected_peak": projected,
                       "target_peak": round(target), "disk_needed": needed,
                       "disk_free": free, "scratch": str(scratch.parent)},
        "base_commit": BASE,
        "model": {"peak_intercept": intercept, "peak_per_release_byte": slope,
                  "release_fixed_bytes": fixed, "release_bytes_per_shard": per_shard},
        "sizes": sizes,
    }
    if free < needed:
        raise Refusal(
            f"the disk under {scratch.parent} has {free} bytes free, and the acceptance release "
            f"of {shards} shards needs {DISK_HEADROOM} times its {max(planned, estimate)} "
            f"planned bytes, {needed}")
    return projected >= HOST_BYTES, projected, evidence


def evidence_path(repository: Path, criterion: str) -> Path:
    return repository / ".hexaemeron/design/evidence" / f"{CANDIDATE}-{criterion}.json"


def acceptance(repository: Path, scratch: Path) -> tuple[bool, int, dict]:
    source = evidence_path(repository, "todays-model-projects-past-the-host")
    if source.is_symlink() or not source.is_file():
        raise Refusal(f"{source.relative_to(repository)} does not exist yet; resolve "
                      "todays-model-projects-past-the-host first")
    try:
        recorded = json.loads(source.read_bytes())["acceptance"]
        parameters = {key: recorded["parameters"][key] for key in ("shards", "logs_per_shard")}
        planned = recorded["planned_release_bytes"]
    except (ValueError, KeyError, TypeError) as error:
        raise Refusal(f"{source.name} records no acceptance parameters: "
                      f"{type(error).__name__}") from None
    for name, value in (*parameters.items(), ("planned_release_bytes", planned)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise Refusal(f"{source.name} records {name} as something other than a whole number")
    made = generate(repository, scratch / "acceptance", parameters, build=False)
    script = repository / PLUGIN / "scripts/usdc_interval.py"
    release = scratch / "acceptance-release"
    built = timed([sys.executable, str(script), "build", "--plan", made["plan"],
                   "--staging", made["staging"], "--registry", made["registry"],
                   "--created-at", made["created_at"], "--output", str(release)], cwd=scratch)
    identifier = IDENTIFIER.findall(built.pop("stdout"))
    if built["exit"] != 0 or len(identifier) != 1:
        raise Refusal(f"build of the acceptance release failed: {built['stderr']}")
    size = sum(path.stat().st_size for path in release.rglob("*") if path.is_file())
    checked = timed([sys.executable, str(script), "check", str(release)], cwd=scratch)
    if checked["exit"] != 0 or identifier[0] not in IDENTIFIER.findall(checked.pop("stdout")):
        raise Refusal(f"check of the acceptance release failed: {checked['stderr']}")
    peak = max(built["maximum_resident_set_bytes"], checked["maximum_resident_set_bytes"])
    evidence = {"build": built, "check": checked, "parameters": parameters,
                "planned_release_bytes": planned, "release_bytes": size,
                "release_id": identifier[0]}
    return peak <= STATED_PEAK and size >= planned, peak, evidence


def verified_release(variable: str, pinned: str) -> Path:
    """The release a variable names, whose manifest hashes to its pinned id and
    whose every component matches the size and SHA-256 the manifest records."""
    value = os.environ.get(variable)
    if not value:
        raise Refusal(f"{variable} is not set; it names a preserved release directory")
    root = Path(value)
    try:
        manifest = json.loads((root / "manifest.json").read_bytes())
        identity = {key: item for key, item in manifest.items() if key != "release_id"}
        canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode("utf-8") + b"\n"
        if (manifest.get("release_id") != pinned
                or "sha256:" + hashlib.sha256(canonical).hexdigest() != pinned):
            raise Refusal(f"{variable} does not hold release {pinned}")
        for item in manifest["components"]:
            path = root / item["object_path"]
            if path.is_symlink() or not path.is_file():
                raise Refusal(f"{variable} component {item['name']} is not a regular file")
            data = path.read_bytes()
            if (len(data) != item["bytes"]
                    or "sha256:" + hashlib.sha256(data).hexdigest() != item["sha256"]):
                raise Refusal(f"{variable} component {item['name']} does not match its manifest")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise Refusal(f"{variable} names no readable Alexandria release: "
                      f"{type(error).__name__}") from None
    return root


def v2_check(repository: Path, scratch: Path, criterion: str) -> tuple[bool, int, dict]:
    release = verified_release("ALEXANDRIA_WILDCAT_V2_RELEASE", V2_RELEASE_ID)
    script = repository / PLUGIN / "scripts/usdc_interval.py"
    runs = []
    for _ in range(RUNS):
        measured = timed([sys.executable, str(script), "check", str(release)], cwd=scratch)
        if measured["exit"] != 0 or V2_RELEASE_ID not in IDENTIFIER.findall(measured.pop("stdout")):
            raise Refusal(f"check of the preserved V2 release failed: {measured['stderr']}")
        runs.append(measured)
    evidence = {"release_id": V2_RELEASE_ID, "runs": runs}
    if criterion == "v2-check-peak-halved":
        value = round(statistics.median(run["maximum_resident_set_bytes"] for run in runs))
        return value <= V2_PEAK_CEILING, value, evidence
    value = round(statistics.median(run["cpu_milliseconds"] for run in runs))
    return value <= V2_CPU_CEILING_MS, value, evidence


def reproduce(repository: Path, scratch: Path) -> tuple[bool, dict]:
    for variable in VARIABLES:
        if not os.environ.get(variable):
            raise Refusal(f"{variable} is not set; {PINNED_CELL} rebuilds and checks both "
                          "preserved Wildcat estates")
    observed = {"demos": {}, "releases": {}}
    passed = True
    examples = repository / PLUGIN / "examples"
    for demo, expected in (*PINNED_DEMOS.items(), ESTATES_DEMO):
        script = examples / demo / "demo.py"
        output = scratch / demo
        built, built_out, built_err = run([sys.executable, str(script), "build", "--output",
                                           str(output)], cwd=repository, extra=VARIABLES)
        if demo == ESTATES_DEMO[0] and built != 0 and KNOWN_2023 in built_err:
            observed["demos"][demo] = {"build": built, "excluded": "issue 2023: " + KNOWN_2023}
            continue
        checked, _, _ = run([sys.executable, str(script), "verify", str(output)],
                            cwd=repository, extra=VARIABLES)
        found = set(IDENTIFIER.findall(built_out)) & expected
        observed["demos"][demo] = {"build": built, "verify": checked,
                                   "identifiers": sorted(found)}
        passed = passed and built == 0 and checked == 0 and found == expected
    code, stdout, stderr = run(
        [sys.executable, "-c", V2_REBUILD,
         str(examples / "wildcat-v2-interval-v0/demo.py"), str(scratch / "v2-rebuild")],
        cwd=repository, extra=VARIABLES)
    observed["v2_rebuild_in_checking_release"] = {"exit": code, "identifier": stdout.strip()[:80],
                                                  "stderr": stderr.strip()[-300:] if code else ""}
    passed = passed and code == 0 and stdout.strip() == V2_RELEASE_ID
    script = repository / PLUGIN / "scripts/usdc_interval.py"
    for variable, pinned in (("ALEXANDRIA_WILDCAT_V1_RELEASE", V1_RELEASE_ID),
                             ("ALEXANDRIA_WILDCAT_V2_RELEASE", V2_RELEASE_ID)):
        code, stdout, _ = run([sys.executable, str(script), "check", os.environ[variable]],
                              cwd=scratch)
        found = IDENTIFIER.findall(stdout)
        observed["releases"][variable] = {"exit": code, "identifier": pinned if pinned in found
                                          else None}
        passed = passed and code == 0 and pinned in found
    for example, pinned in PINNED_RELEASES.items():
        code, stdout, _ = run([sys.executable, str(repository / PLUGIN / "scripts/alexandria.py"),
                               "verify", str(examples / example / "release")], cwd=repository)
        observed["releases"][example] = {"exit": code, "identifier": stdout.strip()[:80]}
        passed = passed and code == 0 and stdout.strip() == pinned
    return passed, observed


# -- reports -----------------------------------------------------------------

def create_only(repository: Path, files) -> None:
    """Write each (path, bytes) pair to a fresh path, after checking every one.

    A path that exists already must hold exactly these bytes and is left as it
    is; any other existing file refuses the whole write before one byte lands.
    """
    fresh = []
    for path, data in files:
        for part in (repository / ".hexaemeron", repository / ".hexaemeron/design",
                     path.parent.parent, path.parent):
            if part.is_symlink():
                raise Refusal(f"{part} must not be a symlink")
        if os.path.lexists(path):
            if (path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode)
                    or path.read_bytes() != data):
                raise Refusal(f"an existing {path.relative_to(repository)} differs from fresh "
                              "evidence; reports are never replaced")
        else:
            fresh.append((path, data))
    for path, data in fresh:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as handle:
            handle.write(data)


def resolve(repository: Path, criterion: str, scratch_parent) -> tuple[bool, object, dict]:
    if criterion in TEST_CELLS:
        passed, observed = test_cell(repository, criterion)
        return passed, True, observed
    if criterion in ("todays-model-projects-past-the-host",
                     "acceptance-release-within-stated-peak") and not GENERATOR.is_file():
        raise Refusal(f"{criterion} runs {GENERATOR.name} beside this script, "
                      "which does not exist yet")
    scratch = Path(tempfile.mkdtemp(prefix="fiat-1891-conformance-", dir=scratch_parent))
    try:
        if criterion == "todays-model-projects-past-the-host":
            return todays_model(repository, scratch)
        if criterion == "acceptance-release-within-stated-peak":
            return acceptance(repository, scratch)
        if criterion in ("v2-check-peak-halved", "v2-check-cpu-within-budget"):
            return v2_check(repository, scratch, criterion)
        passed, observed = reproduce(repository, scratch)
        return passed, True, observed
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("criterion", choices=CRITERIA)
    parser.add_argument("--candidate", default=CANDIDATE)
    parser.add_argument("--scratch", type=Path,
                        help="the directory each cell's fresh working directory is made in")
    parser.add_argument("--no-report", action="store_true",
                        help="print the observation and write no report or evidence")
    args = parser.parse_args(argv)
    if args.candidate != CANDIDATE:
        parser.error("only the selected candidate " + CANDIDATE
                     + " carries conformance cases; refusing " + args.candidate)
    repository = Path.cwd()
    if not (repository / PLUGIN).is_dir():
        parser.error(f"run this from the repository root; {PLUGIN} is absent")
    try:
        passed, value, observed = resolve(repository, args.criterion, args.scratch)
    except (Refusal, OSError) as refusal:
        print(f"conformance: {refusal}", file=sys.stderr)
        return 1
    print(json.dumps({"criterion": args.criterion, "passed": passed, "value": value,
                      "observed": observed}, sort_keys=True))
    if not passed:
        return 1
    if args.no_report:
        return 0
    unit = MEASURED.get(args.criterion, "boolean")
    report = {"candidate": CANDIDATE, "command": (
        "python3 .hexaemeron/design/conformance.py " + args.criterion + " --candidate "
        + CANDIDATE), "criterion": args.criterion, "exit": 0,
        "schema": "protasis-design-report/v1", "unit": unit, "value": value}
    files = [(repository / ".hexaemeron/design/reports/conformance"
              / f"{CANDIDATE}-{args.criterion}.json",
              (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())]
    if args.criterion in MEASURED:
        files.insert(0, (evidence_path(repository, args.criterion),
                         (json.dumps(observed, indent=1, sort_keys=True) + "\n").encode()))
    try:
        create_only(repository, files)
    except (Refusal, OSError) as refusal:
        print(f"conformance: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
