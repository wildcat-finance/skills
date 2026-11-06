"""Bounded hosted checkpoint collection and fresh GitHub evidence admission.

Offline validation checks bytes, not their origin. Only admit() performs the
fresh authenticated reads which the design resolver may use as hosted evidence.
GitHub associates an artifact with a run, not directly with its producing job;
the checked workflow, unique attempt name and job time window supply that join.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io as memory
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import sys
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins/hexaemeron/skills/fiat/scripts"))
from checkpoint_authority import conformance as owner, native_io as bounded
from checkpoint_authority import network, network_policy, release, release_conformance as native
from checkpoint_authority.canonical import Refusal as NativeRefusal

REPOSITORY = "wildcat-finance/skills"
REPOSITORY_ID = 1334819508
WORKFLOW = ".github/workflows/checkpoint-conformance.yml"
PROFILES = {"ubuntu-24.04": ("linux", "x86_64", "Linux", "X64", "linux-amd64"),
            "macos-15": ("darwin", "arm64", "macOS", "ARM64", "darwin-arm64")}
MEMBERS = ("host.json", "direct.stdout", "direct.stderr", "descendant.stdout",
           "descendant.stderr", "release.stdout", "release.stderr", "tests.log")
ZIP_MAX = 65536
EXPANDED_MAX = 262144
HOST_MAX = 65536
LOG_MAX = 65536
SHA = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
SOURCE_PATHS = tuple(sorted(set(native.SOURCES) | {
    WORKFLOW, "plugins/hexaemeron/tests/checkpoint_hosted_evidence.py",
    "plugins/hexaemeron/tests/checkpoint_hosted_collect.py",
    "plugins/hexaemeron/tests/test_checkpoint_hosted_evidence.py",
    "plugins/hexaemeron/tests/requirements.lock",
    *(release.SCRIPTS + "checkpoint_authority/" + name + ".py" for name in release.MODULES)}))
TOOL_NAMES = ("python", "cosign", "sandbox", "git", "gpg", "gpgconf", "ssh-keygen", "openssl")
ASSOCIATION = "Run association is authenticated; job association uses the checked workflow, unique attempt artifact name and successful job time window. GitHub artifact REST rows do not directly attest the producing job."
APPARMOR_PROFILE = "/etc/apparmor.d/bwrap-userns-restrict"
APPARMOR_SHA256 = "11d39094f044f0cda0febb3ad517b830301da6b2ce929664af09ee9e4dd264f9"
LINUX_SETUP = {"apparmor_profile_sha256": APPARMOR_SHA256,
               "userns_restriction": 1, "local_overrides": "absent"}


def refuse(code):
    raise owner.Refusal("hosted-" + code)


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode()


def decode(data, maximum=HOST_MAX):
    if type(data) is not bytes or not 0 < len(data) <= maximum:
        refuse("json-limit")
    try:
        value = json.loads(data, object_pairs_hook=owner._unique_object,
                           parse_constant=lambda _: refuse("json-number"))
    except (ValueError, UnicodeError, RecursionError):
        refuse("json-shape")
    # Bound depth after parsing; the byte ceiling bounds parser allocation.
    def walk(item, depth=0):
        if depth > 16:
            refuse("json-depth")
        if type(item) is dict:
            for child in item.values(): walk(child, depth + 1)
        elif type(item) is list:
            for child in item: walk(child, depth + 1)
    walk(value)
    return value


def closed(value, fields, code):
    if type(value) is not dict or set(value) != set(fields): refuse(code)


def integer(value, code, maximum=10**15):
    if type(value) is not int or not 1 <= value <= maximum: refuse(code)
    return value


def text(value, code, maximum=1024):
    if (type(value) is not str or not 1 <= len(value) <= maximum
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        refuse(code)
    return value


def checksum(value, code):
    if type(value) is not str or SHA.fullmatch(value) is None: refuse(code)
    return value


def commit(value):
    if type(value) is not str or COMMIT.fullmatch(value) is None: refuse("checkout")
    return value


def timestamp(value):
    text(value, "timestamp", 32)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        refuse("timestamp")
    return parsed


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def artifact_name(profile, run_id, attempt):
    return f"checkpoint-{profile}-{run_id}-{attempt}"


def inventory(root):
    """Bind all native sources, host owners and transitive release fixtures."""
    observed = native.inputs(root)
    manifest = decode(bounded.read(root / release.MANIFEST, release.MANIFEST_MAX), release.MANIFEST_MAX)
    paths = set(SOURCE_PATHS) | {release.MANIFEST, native.MANIFEST}
    for component in manifest["components"].values():
        paths.update(row["path"] for row in component["files"])
    paths.update(row["path"] for row in manifest["transitive_files"])
    paths.update(native.FILES)
    if len(paths) > 256: refuse("source-count")
    rows = []
    for path in sorted(paths):
        release._path(path)
        digest, count = bounded.hash_file(root / path, release.FILE_MAX)
        rows.append({"path": path, "sha256": digest, "bytes": count})
    return {"files": rows, "cases": observed["cases"],
            "release_manifest": observed["release_manifest"],
            "fixture_manifest": observed["fixture_manifest"]}


@dataclass(frozen=True)
class Tool:
    """A caller-selected local executable pin, never populated by artifact bytes."""
    name: str
    path: str
    sha256: str

    def check(self):
        if self.name not in (*TOOL_NAMES, "gh") or bounded.hash_file(self.path, 268435456)[0] != self.sha256:
            refuse("tool-changed")


def pin(name, path=None):
    path = str(Path(path or shutil.which(name) or "/missing-tool").resolve(strict=True))
    return Tool(name, path, bounded.hash_file(path, 268435456)[0])


def command(tool, arguments, root, *, timeout=60, authenticated=False, check=True):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_") and (authenticated or key not in ("GH_TOKEN", "GITHUB_TOKEN"))}
    environment.update(GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0",
                       GH_HOST="github.com", GH_PROMPT_DISABLED="1")
    result = bounded.execute(tool, arguments, root, environment, stage="hosted-evidence",
                             attempt_id="hosted-evidence", input_sha256="0" * 64,
                             deadline=time.monotonic() + timeout)
    if check and result.exit != 0: refuse("command-failed")
    return result


def checkout(root):
    git = pin("git")
    if command(git, ["status", "--porcelain", "--untracked-files=normal"], root).stdout:
        refuse("dirty-checkout")
    return commit(command(git, ["rev-parse", "HEAD"], root).stdout.decode("ascii").strip())


def policy_descriptor(policy):
    return {"platform": policy.platform, "abi": policy.abi, "mechanism": policy.mechanism,
            "launcher": policy.launcher, "argv": list(policy.argv),
            "filter_sha256": hashlib.sha256(policy.filter_bytes).hexdigest(),
            "policy_sha256": policy.sha256}


def sandbox_setup(system):
    """Observe the reviewed Ubuntu profile without changing host policy."""
    if system != "linux":
        return None
    if bounded.hash_file(APPARMOR_PROFILE, 4096)[0] != APPARMOR_SHA256:
        refuse("apparmor-profile")
    for name in ("bwrap-userns-restrict", "unpriv_bwrap"):
        if os.path.lexists("/etc/apparmor.d/local/" + name):
            refuse("apparmor-override")
    # Procfs reports zero size; read its fixed kernel leaf with a separate cap.
    with bounded.directory(Path("/proc/sys/kernel")) as (parent, check):
        fd = os.open("apparmor_restrict_unprivileged_userns", bounded.FILE_FLAGS, dir_fd=parent)
        try:
            value = os.read(fd, 3)
        finally:
            os.close(fd)
        check()
    if value != b"1\n":
        refuse("userns-restriction")
    return dict(LINUX_SETUP)


def positive(value, root, expected):
    """Structural validation alone deliberately admits failures; hosted success does not."""
    native._validate(value, root, expected)
    cases = native.inputs(root)["cases"]
    if not (value["complete"] is True and value["passed"] is True
            and value["demonstration"] is not None and value["workload"] is not None
            and sorted(value["started"]) == cases and value["started"] == value["completed"]
            and value["tests_run"] == len(cases)
            and all(value[key] == 0 for key in ("failures", "errors", "skips", "expected_failures", "unexpected_successes"))):
        refuse("incomplete-execution")
    if value["demonstration"]["interoperability_cases"] != 5:
        refuse("interoperability-count")


def collect(root, profile, destination):
    """Retain partial evidence and bounded identity when real execution refuses."""
    if profile not in PROFILES: refuse("profile")
    destination = Path(destination).absolute()
    with bounded.directory(destination.parent):
        destination.mkdir(mode=0o700)
    context = {"profile": profile, "platform": sys.platform, "machine": platform.machine(),
               "checkout_sha": None, "run_id": None, "run_attempt": None, "source": None, "tools": None}
    try:
        return _collect(root, profile, destination, context)
    except (owner.Refusal, NativeRefusal, OSError, ValueError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, owner.Refusal) else (
            error.code if isinstance(error, NativeRefusal) else "collection-unavailable")
        failed = encode({"schema": "checkpoint-hosted-collection-refusal/v1", "complete": False,
                         "code": code, **context})
        if len(failed) <= HOST_MAX:
            bounded.create(destination / "failure.json", failed)
        raise


def _collect(root, profile, destination, context):
    """Execute real probes and the owner suite on the declared Actions host."""
    system, machine, runner_os, runner_arch, _ = PROFILES[profile]
    if (os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or sys.platform != system or platform.machine() != machine
            or os.environ.get("RUNNER_OS") != runner_os or os.environ.get("RUNNER_ARCH") != runner_arch):
        refuse("runtime-host")
    if system == "linux":
        os_release = platform.freedesktop_os_release()
        version = os_release.get("VERSION_ID", "")
        if os_release.get("ID") != "ubuntu" or version != "24.04": refuse("runtime-version")
    else:
        version = platform.mac_ver()[0]
        if version.split(".")[0] != "15": refuse("runtime-version")
    source = inventory(root); head = checkout(root)
    context.update(source=source, checkout_sha=head)
    if sys.version.split()[0] != bounded.read(root / ".python-version", 32).decode().strip(): refuse("python")
    try:
        run_id = integer(int(os.environ["GITHUB_RUN_ID"]), "run")
        attempt = integer(int(os.environ["GITHUB_RUN_ATTEMPT"]), "attempt", 10000)
    except (ValueError, KeyError): refuse("run")
    context.update(run_id=run_id, run_attempt=attempt)
    setup = sandbox_setup(system)
    event_head = commit(os.environ.get("CHECKPOINT_EVENT_HEAD", ""))
    event_sha = commit(os.environ.get("GITHUB_SHA", ""))
    merge = os.environ.get("CHECKPOINT_EVENT_MERGE", "")
    if merge: commit(merge)
    if head != event_head: refuse("checkout")
    event = os.environ.get("GITHUB_EVENT_NAME")
    if event not in ("push", "pull_request", "workflow_dispatch"): refuse("event")
    boundary = network.prepare()
    pins = {name: pin(name, sys.executable if name == "python" else
                      boundary.policy.launcher if name == "sandbox" else
                      os.environ.get("CHECKPOINT_COSIGN") if name == "cosign" else None)
            for name in TOOL_NAMES}
    tools = [{"name": name, "path": tool.path, "sha256": tool.sha256}
             for name, tool in pins.items()]
    context["tools"] = tools
    started = now()
    files = {}
    for label, program in (("direct", network.PROBE), ("descendant", network.DESCENDANT_PROBE)):
        code, stdout, stderr = boundary.run(pins["python"], ["-I", "-c", program], destination, timeout=10)
        files[label + ".stdout"] = stdout; files[label + ".stderr"] = stderr
        for suffix, data in (("stdout", stdout), ("stderr", stderr)):
            bounded.create(destination / (label + "." + suffix), data)
        if code != 0 or stdout != network.PROBE_OUTPUT or stderr: refuse("network-probe")
    result = command(pins["python"], [str(root / "plugins/hexaemeron/tests/checkpoint_authority_release_suite.py"),
                                     "--raw-log", str(destination / "tests.log")], root, timeout=1800, check=False)
    files["release.stdout"] = result.stdout; files["release.stderr"] = result.stderr
    for name in ("release.stdout", "release.stderr"): bounded.create(destination / name, files[name])
    if result.exit != 0: refuse("release-exit")
    value = decode(result.stdout)
    positive(value, root, boundary.expected())
    files["tests.log"] = bounded.read(destination / "tests.log", LOG_MAX)
    if hashlib.sha256(files["tests.log"]).hexdigest() != value["output_sha256"]: refuse("test-log")
    if result.stderr: refuse("release-stderr")
    for tool in pins.values(): tool.check()
    if (inventory(root) != source or checkout(root) != head
            or network.prepare().expected() != boundary.expected() or sandbox_setup(system) != setup):
        refuse("source-changed")
    host = {"schema": "checkpoint-hosted-execution/v1", "profile": profile,
            "repository": REPOSITORY, "run_id": run_id, "run_attempt": attempt,
            "checkout_sha": head, "event": event, "event_sha": event_sha,
            "event_head_sha": event_head, "event_merge_sha": merge or None,
            "runner": {"os": runner_os, "arch": runner_arch, "name": text(os.environ.get("RUNNER_NAME"), "runner-name", 256)},
            "runtime": {"platform": system, "machine": machine, "os_version": version, "python": sys.version.split()[0]},
            "sandbox_setup": setup,
            "started_at": started, "completed_at": now(), "source": source,
            "tools": tools, "policy": policy_descriptor(boundary.policy),
            "network": boundary.expected(), "release_exit": result.exit,
            "files": [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                      for name, data in sorted(files.items())]}
    encoded = encode(host)
    if len(encoded) > HOST_MAX: refuse("host-limit")
    bounded.create(destination / "host.json", encoded)
    return host


def archive_members(data):
    """Inspect exact flat regular members in memory; never extract a path."""
    if type(data) is not bytes or not 0 < len(data) <= ZIP_MAX: refuse("zip-limit")
    try:
        with zipfile.ZipFile(memory.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) != len(MEMBERS) or sorted(x.filename for x in infos) != sorted(MEMBERS): refuse("zip-members")
            if sum(x.file_size for x in infos) > EXPANDED_MAX: refuse("zip-expanded-limit")
            files = {}
            for entry in infos:
                kind = (entry.external_attr >> 16) & 0o170000
                if (entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                        or entry.is_dir() or kind not in (0, stat.S_IFREG)
                        or not 0 <= entry.file_size <= HOST_MAX or not 0 <= entry.compress_size <= ZIP_MAX):
                    refuse("zip-member-kind")
                with archive.open(entry) as stream: payload = stream.read(HOST_MAX + 1)
                if len(payload) != entry.file_size or len(payload) > HOST_MAX: refuse("zip-member-limit")
                files[entry.filename] = payload
            return files
    except (zipfile.BadZipFile, RuntimeError, ValueError, OSError, NotImplementedError):
        refuse("zip-shape")


def validate_files(root, profile, files):
    """Pure, non-authorising validation, including a foreign host's descriptor."""
    if profile not in PROFILES or type(files) is not dict or set(files) != set(MEMBERS): refuse("files")
    host = decode(files["host.json"])
    closed(host, ("schema", "profile", "repository", "run_id", "run_attempt", "checkout_sha", "event", "event_sha",
                  "event_head_sha", "event_merge_sha", "runner", "runtime", "started_at", "completed_at", "source",
                  "tools", "policy", "network", "release_exit", "files", "sandbox_setup"), "host-shape")
    if host["schema"] != "checkpoint-hosted-execution/v1" or host["profile"] != profile or host["repository"] != REPOSITORY: refuse("host-profile")
    integer(host["run_id"], "run"); integer(host["run_attempt"], "attempt", 10000)
    commit(host["checkout_sha"]); commit(host["event_sha"]); commit(host["event_head_sha"])
    if host["event_merge_sha"] is not None: commit(host["event_merge_sha"])
    if host["event"] not in ("push", "pull_request", "workflow_dispatch"): refuse("event")
    if host["checkout_sha"] != host["event_head_sha"]: refuse("checkout")
    if host["event"] != "pull_request" and (host["event_merge_sha"] is not None or host["event_sha"] != host["checkout_sha"]): refuse("event")
    started = timestamp(host["started_at"]); completed = timestamp(host["completed_at"])
    if not 0 <= (completed - started).total_seconds() <= 1860: refuse("execution-window")
    system, machine, runner_os, runner_arch, asset = PROFILES[profile]
    closed(host["runner"], ("os", "arch", "name"), "runner")
    if host["runner"]["os"] != runner_os or host["runner"]["arch"] != runner_arch: refuse("runner")
    text(host["runner"]["name"], "runner-name", 256)
    closed(host["runtime"], ("platform", "machine", "os_version", "python"), "runtime")
    runtime = host["runtime"]
    if runtime["platform"] != system or runtime["machine"] != machine: refuse("runtime-host")
    text(runtime["os_version"], "runtime-version", 32)
    if (system == "linux" and runtime["os_version"] != "24.04") or (system == "darwin" and runtime["os_version"].split(".")[0] != "15"): refuse("runtime-version")
    if runtime["python"] != bounded.read(root / ".python-version", 32).decode().strip(): refuse("python")
    if encode(host["sandbox_setup"]) != encode(LINUX_SETUP if system == "linux" else None):
        refuse("sandbox-setup")
    if encode(host["source"]) != encode(inventory(root)): refuse("source-drift")
    if type(host["tools"]) is not list or len(host["tools"]) != len(TOOL_NAMES): refuse("tools")
    tools = {}
    for row, name in zip(host["tools"], TOOL_NAMES):
        closed(row, ("name", "path", "sha256"), "tool")
        if row["name"] != name or not text(row["path"], "tool-path").startswith("/"): refuse("tool")
        checksum(row["sha256"], "tool-hash"); tools[name] = row
    tool_profile = decode(bounded.read(root / (release.CORPUS + "tool-profile.json"), HOST_MAX))
    if tools["cosign"]["sha256"] != tool_profile["cosign"]["assets"][asset]["sha256"]: refuse("cosign-pin")
    policy = network_policy.for_host(system, machine)
    if encode(host["policy"]) != encode(policy_descriptor(policy)) or tools["sandbox"]["path"] != policy.launcher: refuse("policy")
    expected = network.Boundary(tools["sandbox"]["sha256"], policy).expected()
    network.validate_observation(host["network"], expected)
    wanted = [{"path": name, "bytes": len(files[name]), "sha256": hashlib.sha256(files[name]).hexdigest()}
              for name in sorted(set(MEMBERS) - {"host.json"})]
    if encode(host["files"]) != encode(wanted): refuse("file-binding")
    for label in ("direct", "descendant"):
        if files[label + ".stdout"] != network.PROBE_OUTPUT or files[label + ".stderr"]: refuse("network-probe")
    if type(host["release_exit"]) is not int or host["release_exit"] != 0 or files["release.stderr"]: refuse("release-exit")
    execution = decode(files["release.stdout"])
    positive(execution, root, expected)
    if hashlib.sha256(files["tests.log"]).hexdigest() != execution["output_sha256"]: refuse("test-log")
    if execution["workload"]["environment"]["machine"] != machine: refuse("workload-host")
    return host, execution


def metadata_subjects(profile, request, run, jobs, artifact, archive_sha):
    """Check authenticated execution identity before inspecting artifact members."""
    if (type(run) is not dict or run.get("id") != request["run_id"] or type(run.get("id")) is not int
            or run.get("run_attempt") != request["run_attempt"] or type(run.get("run_attempt")) is not int
            or run.get("head_sha") != request["checkout_sha"] or run.get("path") != WORKFLOW
            or run.get("event") not in ("push", "pull_request", "workflow_dispatch")
            or run.get("status") != "completed" or run.get("conclusion") != "success"
            or type(run.get("repository")) is not dict or run["repository"].get("id") != REPOSITORY_ID
            or run["repository"].get("full_name") != REPOSITORY): refuse("workflow-run")
    if (type(jobs) is not dict or type(jobs.get("jobs")) is not list or type(jobs.get("total_count")) is not int
            or not 1 <= jobs["total_count"] == len(jobs["jobs"]) <= 100): refuse("jobs")
    matched = [job for job in jobs["jobs"] if type(job) is dict and job.get("name") == "checkpoint (" + profile + ")"]
    if len(matched) != 1: refuse("job")
    job = matched[0]
    for field in ("id", "run_id", "run_attempt"): integer(job.get(field), "job-" + field)
    if (job["run_id"] != request["run_id"] or job["run_attempt"] != request["run_attempt"]
            or job.get("head_sha") != request["checkout_sha"] or job.get("status") != "completed"
            or job.get("conclusion") != "success" or job.get("labels") != [profile]
            or job.get("runner_group_name") != "GitHub Actions" or job.get("runner_group_id") != 0
            or type(job.get("runner_group_id")) is not int): refuse("job")
    text(job.get("runner_name"), "runner-name", 256)
    steps = job.get("steps")
    if type(steps) is not list or not 1 <= len(steps) <= 100: refuse("job-steps")
    executed = [step for step in steps if type(step) is dict and step.get("name") == "Run checkpoint conformance"]
    if len(executed) != 1 or executed[0].get("status") != "completed" or executed[0].get("conclusion") != "success": refuse("job-execution")
    if profile == "ubuntu-24.04":
        setup = [step for step in steps if type(step) is dict and step.get("name") == "Prepare the Linux sandbox policy"]
        if len(setup) != 1 or setup[0].get("status") != "completed" or setup[0].get("conclusion") != "success":
            refuse("job-setup")
    if (type(artifact) is not dict or artifact.get("id") != request["artifact_id"]
            or type(artifact.get("id")) is not int or artifact.get("expired") is not False
            or artifact.get("name") != artifact_name(profile, request["run_id"], request["run_attempt"])
            or artifact.get("digest") != "sha256:" + archive_sha): refuse("artifact")
    integer(artifact.get("size_in_bytes"), "artifact-size", ZIP_MAX)
    workflow_run = artifact.get("workflow_run")
    if (type(workflow_run) is not dict or workflow_run.get("id") != request["run_id"]
            or workflow_run.get("repository_id") != REPOSITORY_ID
            or workflow_run.get("head_repository_id") != REPOSITORY_ID
            or workflow_run.get("head_sha") != request["checkout_sha"]): refuse("artifact-run")
    return job


def validate_metadata(host, profile, request, run, jobs, artifact, archive_sha):
    """Join required GitHub fields; extra provider fields carry no authority."""
    job = metadata_subjects(profile, request, run, jobs, artifact, archive_sha)
    if (host["run_id"] != request["run_id"] or host["run_attempt"] != request["run_attempt"]
            or host["checkout_sha"] != request["checkout_sha"] or run["event"] != host["event"]
            or job["runner_name"] != host["runner"]["name"]): refuse("run-binding")
    job_start = timestamp(job.get("started_at")); job_end = timestamp(job.get("completed_at"))
    execution_start = timestamp(host["started_at"]); execution_end = timestamp(host["completed_at"])
    uploaded = timestamp(artifact.get("created_at"))
    if not job_start <= execution_start <= execution_end <= uploaded <= job_end: refuse("artifact-window")
    return {"run_id": request["run_id"], "run_attempt": request["run_attempt"], "job_id": job["id"],
            "artifact_id": artifact["id"], "artifact_sha256": archive_sha,
            "checkout_sha": request["checkout_sha"], "profile": profile,
            "run_url": f"https://github.com/{REPOSITORY}/actions/runs/{request['run_id']}/attempts/{request['run_attempt']}",
            "job_url": f"https://github.com/{REPOSITORY}/actions/runs/{request['run_id']}/job/{job['id']}",
            "association_boundary": ASSOCIATION}


def github(path, root):
    """Fixed host and repository; gh owns credential use and redirect handling."""
    if not re.fullmatch(r"repos/wildcat-finance/skills/actions/[a-z0-9/?=_-]+", path): refuse("api-path")
    return command(pin("gh"), ["api", "--hostname", "github.com", path], root,
                   authenticated=True).stdout


def admit(root, profile, evidence):
    """Fresh authenticated reads and digest-checked download; local captures cannot admit."""
    if profile not in PROFILES or evidence != ".hexaemeron/sources/ci/" + profile: refuse("evidence-path")
    directory = root / evidence
    request = decode(bounded.read(directory / "request.json", 2048), 2048)
    closed(request, ("schema", "run_id", "run_attempt", "artifact_id", "checkout_sha"), "request")
    if request["schema"] != "checkpoint-hosted-request/v1": refuse("request")
    integer(request["run_id"], "run"); integer(request["run_attempt"], "attempt", 10000)
    integer(request["artifact_id"], "artifact-id"); commit(request["checkout_sha"])
    before = inventory(root)
    if checkout(root) != request["checkout_sha"]: refuse("checkout")
    # Each observation remains as evidence after admission or refusal.
    name = "observation-" + uuid.uuid4().hex
    with bounded.directory(directory) as (parent, check):
        os.mkdir(name, mode=0o700, dir_fd=parent)
        check()
    capture = directory / name
    bounded.create(capture / "request.json", encode(request))
    paths = {"run": f"repos/{REPOSITORY}/actions/runs/{request['run_id']}/attempts/{request['run_attempt']}",
             "jobs": f"repos/{REPOSITORY}/actions/runs/{request['run_id']}/attempts/{request['run_attempt']}/jobs?per_page=100",
             "artifact": f"repos/{REPOSITORY}/actions/artifacts/{request['artifact_id']}"}
    try:
        authentication = decode(command(pin("gh"), ["api", "--hostname", "github.com", "user"],
                                        root, authenticated=True).stdout)
        if type(authentication) is not dict: refuse("authentication")
        login = text(authentication.get("login"), "authentication", 64)
        actor_id = integer(authentication.get("id"), "authentication")
        bounded.create(capture / "authentication.json", encode({"login": login, "id": actor_id}))
        metadata = {}
        for name, path in paths.items():
            raw = github(path, root); bounded.create(capture / (name + ".json"), raw)
            metadata[name] = decode(raw)
        raw = github(paths["artifact"] + "/zip", root)
        bounded.create(capture / "artifact.zip", raw)
        archive_sha = hashlib.sha256(raw).hexdigest()
        metadata_subjects(profile, request, **metadata, archive_sha=archive_sha)
        files = archive_members(raw)
        host, execution = validate_files(root, profile, files)
        binding = validate_metadata(host, profile, request, **metadata, archive_sha=archive_sha)
        if metadata["artifact"]["size_in_bytes"] != len(raw): refuse("artifact-size")
        after = {}
        for name, path in paths.items():
            raw = github(path, root); bounded.create(capture / (name + "-after.json"), raw)
            after[name] = decode(raw)
        if validate_metadata(host, profile, request, **after, archive_sha=archive_sha) != binding:
            refuse("github-changed")
        if after["artifact"] != metadata["artifact"] or after["jobs"] != metadata["jobs"] or after["run"] != metadata["run"]:
            refuse("github-changed")
        if inventory(root) != before or checkout(root) != request["checkout_sha"]: refuse("source-changed")
        result = {"schema": "checkpoint-hosted-admission/v1", "complete": True, "passed": True,
                  **binding, "capture": str(capture.relative_to(root)), "host_sha256": hashlib.sha256(files["host.json"]).hexdigest(),
                  "release_stdout_sha256": hashlib.sha256(files["release.stdout"]).hexdigest(),
                  "tests_run": execution["tests_run"], "subtests_run": execution["subtests_run"],
                  "source_sha256": hashlib.sha256(encode(before)).hexdigest(),
                  "files": [{"path": path.name, "sha256": bounded.hash_file(path, HOST_MAX)[0]}
                            for path in sorted(capture.iterdir())]}
        bounded.create(capture / "admission.json", encode(result))
        return result
    except (owner.Refusal, NativeRefusal, OSError, ValueError, KeyError, TypeError):
        bounded.create(capture / "refusal.json", encode({"schema": "checkpoint-hosted-refusal/v1", "complete": False,
                                                        "run_id": request["run_id"], "run_attempt": request["run_attempt"],
                                                        "artifact_id": request["artifact_id"], "code": "evidence-not-admitted"}))
        raise
