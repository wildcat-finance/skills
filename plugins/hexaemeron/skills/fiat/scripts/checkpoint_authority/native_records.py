"""The pinned native v1 shapes; no native record is widened by this adapter."""
from __future__ import annotations

from dataclasses import dataclass
import re
import zipfile

from .canonical import Refusal, canonical, decode, digest
from .native_io import FILE_MAX, MANIFEST_MAX

NATIVE_COMMIT = "1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74"
CONTROLLER_SHA256 = "326817a508a2d0be382e8e44071ec1d5957411a9cb6091764d7a33e9e032ff30"
PROFILE = "native-1d4e4eeb-openpgp-v1"
CONTROLLER = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
IDENTITY_DOMAIN = b"wildcat-fiat-checkpoint-identity/v1\0"
CAPSULE = "controller-capsule/"
MEMBERS = ("checkpoint.json", CAPSULE + "MANIFEST.json", CAPSULE + "controller/state.json",
           CAPSULE + "controller/ledger.jsonl", "proof/signatures.json")
HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z", re.ASCII)


def closed(value, fields, schema=None):
    if type(value) is not dict or set(value) != set(fields) or (schema is not None and value.get("schema") != schema):
        raise Refusal("native-output-shape", "native")
    return value


def hexadecimal(value, *, commit=False):
    if type(value) is not str or (COMMIT if commit else HASH).fullmatch(value) is None:
        raise Refusal("native-output-shape", "native")
    return value


def count(value, maximum=100000, *, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise Refusal("native-output-shape", "native")
    return value


def shas(values, *, empty=True):
    if type(values) is not list or len(values) > 4096 or (not values and not empty):
        raise Refusal("native-coverage-shape", "coverage")
    for value in values:
        hexadecimal(value, commit=True)
    if len(values) != len(set(values)):
        raise Refusal("native-coverage-duplicate", "coverage")
    return tuple(values)


def ledger(data):
    if not data or len(data) > FILE_MAX or not data.endswith(b"\n"):
        raise Refusal("native-producer-ledger", "native")
    previous, entries = "genesis", []
    for raw in data.splitlines(keepends=True):
        row = decode(raw, limit=FILE_MAX)
        closed(row, ("ts", "event", "data", "prev", "state", "hash"))
        if type(row["event"]) is not str or type(row["data"]) is not dict or row["prev"] != previous:
            raise Refusal("native-producer-ledger", "native")
        hexadecimal(row["state"]); hexadecimal(row["hash"])
        if digest(canonical({key: value for key, value in row.items() if key != "hash"}, limit=FILE_MAX)) != row["hash"]:
            raise Refusal("native-producer-ledger", "native")
        entries.append(row); previous = row["hash"]
        if len(entries) > 100000:
            raise Refusal("native-producer-limit", "native")
    return entries


def custody(state, entries):
    """Reject unsupported history before a native command can read its locators."""
    events = {"init", "record", "done:study", "done:runbook", "done:implement",
              "audit-round", "done:audit", "done:prose", "done:push",
              "amend:study", "amend:runbook", "record:run-observation"}
    records = {"security_suite", "labs_marketplace", "controller_currency", "controller_runtime_update"}
    for entry in entries:
        if entry["event"] == "checkpoint:restore":
            raise Refusal("native-nested-restore-unavailable", "custody")
        if entry["event"] not in events or (entry["event"] == "record" and entry["data"].get("key") not in records):
            raise Refusal("native-history-class-unavailable", "custody")
    receipts = state.get("receipts")
    if type(receipts) is not dict or not set(receipts) <= records | {"task_issue_contract", "task_issue", "run_anchor", "study", "runbook", "run_observations"}:
        raise Refusal("native-private-custody-unavailable", "custody")
    if type(state.get("steps")) is not list:
        raise Refusal("native-producer-shape", "native")
    for step in state["steps"]:
        step_receipts = step.get("receipts") if type(step) is dict else None
        if type(step_receipts) is not dict or not set(step_receipts) <= {"implement", "audit", "prose", "push"}:
            raise Refusal("native-private-custody-unavailable", "custody")
    runbook = receipts.get("runbook")
    if type(runbook) is not dict or "known_failure_inventory" in runbook:
        raise Refusal("native-private-custody-unavailable", "custody")
    if "integrate" in state or "replacement" in state:
        raise Refusal("native-history-class-unavailable", "custody")


@dataclass(frozen=True)
class ArchiveMetadata:
    archive_bytes: bytes
    manifest_bytes: bytes
    state_bytes: bytes
    ledger_bytes: bytes
    proof_bytes: bytes

    @property
    def state(self):
        return decode(self.state_bytes, limit=FILE_MAX)

    @property
    def manifest(self):
        return decode(self.manifest_bytes, limit=MANIFEST_MAX)

    @property
    def outer(self):
        return decode(self.archive_bytes, limit=MANIFEST_MAX)

    @property
    def entries(self):
        return ledger(self.ledger_bytes)

    @property
    def proof(self):
        return decode(self.proof_bytes, limit=FILE_MAX)


def metadata(archive):
    """Read only fixed bounded members; native inspection still validates the ZIP."""
    try:
        with zipfile.ZipFile(archive) as container:
            infos = container.infolist()
            if len(infos) > 4200:
                raise Refusal("native-archive-limit", "native")
            data = []
            for name in MEMBERS:
                found = [info for info in infos if info.filename == name]
                maximum = MANIFEST_MAX if name in MEMBERS[:2] else FILE_MAX
                if len(found) != 1 or found[0].compress_type != zipfile.ZIP_STORED or found[0].flag_bits & 1 or not 0 < found[0].file_size <= maximum:
                    raise Refusal("native-metadata-unavailable", "native")
                with container.open(found[0]) as stream:
                    member = stream.read(maximum + 1)
                if len(member) != found[0].file_size:
                    raise Refusal("native-metadata-unavailable", "native")
                data.append(member)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
        raise Refusal("native-metadata-unavailable", "native") from None
    result = ArchiveMetadata(*data)
    manifest, state, entries = result.manifest, result.state, result.entries
    if (type(manifest) is not dict or type(state) is not dict
        or type(manifest.get("source")) is not dict
        or type(manifest.get("boundary")) is not dict):
        raise Refusal("native-producer-shape", "native")
    if canonical(manifest, limit=MANIFEST_MAX) + b"\n" != result.manifest_bytes:
        raise Refusal("native-manifest-encoding", "native")
    if (manifest.get("schema") != "fiat-controller-checkpoint/v1"
        or manifest.get("source", {}).get("state_sha256") != digest(result.state_bytes)
        or manifest.get("source", {}).get("ledger_sha256") != digest(result.ledger_bytes)
        or manifest["source"].get("ledger_entries") != len(entries)
        or manifest["source"].get("ledger_tail") != entries[-1]["hash"]
        or entries[-1]["state"] != digest(canonical(state, limit=FILE_MAX))):
        raise Refusal("native-producer-binding", "native")
    custody(state, entries)
    return result


def inspect_result(value):
    closed(value, ("schema", "outer_sha256", "entries", "bytes", "findings", "bundle", "signatures", "identity", "refs"), "fiat-checkpoint-inspect/v1")
    hexadecimal(value["outer_sha256"]); count(value["entries"], 4200, minimum=1)
    count(value["bytes"], 1073741824, minimum=1)
    if value["findings"] != []:
        raise Refusal("native-inspect-findings", "inspect")
    closed(value["identity"], ("status", "snapshot_id"))
    if value["identity"]["status"] != "bound":
        raise Refusal("native-identity-unavailable", "inspect")
    hexadecimal(value["identity"]["snapshot_id"])
    closed(value["bundle"], ("bytes", "complete_history", "hash_algorithm", "sha256"))
    if value["bundle"]["complete_history"] is not True or value["bundle"]["hash_algorithm"] != "sha1":
        raise Refusal("native-object-format-unavailable", "inspect")
    count(value["bundle"]["bytes"], 1073741824, minimum=1); hexadecimal(value["bundle"]["sha256"])
    if type(value["refs"]) is not dict or not 1 <= len(value["refs"]) <= 4096:
        raise Refusal("native-output-shape", "inspect")
    for ref, commit in value["refs"].items():
        if type(ref) is not str or not 0 < len(ref) <= 1024 or ref.startswith("-") or re.fullmatch(r"[a-zA-Z0-9/_-]+", ref) is None:
            raise Refusal("native-ref-unavailable", "inspect")
        hexadecimal(commit, commit=True)
    if type(value["signatures"]) is not list or len(value["signatures"]) > 4096:
        raise Refusal("native-output-shape", "inspect")
    commits = []
    for row in value["signatures"]:
        closed(row, ("sha", "fingerprint", "status", "trailers"))
        hexadecimal(row["sha"], commit=True)
        if row["status"] != "G" or type(row["fingerprint"]) is not str or re.fullmatch(r"[0-9A-F]{40}", row["fingerprint"]) is None:
            raise Refusal("native-signature-format-unavailable", "inspect")
        closed(row["trailers"], ("coauthored_by_shoggoth", "wildcat_origin"))
        for number in row["trailers"].values(): count(number, 4096)
        commits.append(row["sha"])
    shas(commits)
    return value


def restore_result(value):
    closed(value, ("schema", "outer_sha256", "restore", "snapshot_id", "status_sha256", "verify", "next"), "fiat-checkpoint-archive-restore/v1")
    inner = closed(value["restore"], ("schema", "worktree", "recovery", "manifest_sha256", "source_state_sha256", "source_ledger_sha256", "state_fingerprint", "ledger_entries", "ledger_sha256", "ledger_tail", "refs", "verify", "status_sha256", "next"), "fiat-controller-checkpoint-restore/v1")
    for name in ("outer_sha256", "snapshot_id", "status_sha256"): hexadecimal(value[name])
    for name in ("manifest_sha256", "source_state_sha256", "source_ledger_sha256", "state_fingerprint", "ledger_sha256", "ledger_tail", "status_sha256"): hexadecimal(inner[name])
    count(inner["ledger_entries"], minimum=1); count(inner["refs"], 4096, minimum=1)
    if (value["verify"] != "ok" or inner["verify"] != "ok" or inner["recovery"] != "new"
        or value["status_sha256"] != inner["status_sha256"] or value["next"] != inner["next"]
        or type(value["next"]) is not dict or type(inner["worktree"]) is not str):
        raise Refusal("native-restore-join", "restore")
    return value


def identity_result(value):
    closed(value, ("schema", "identity", "snapshot_id"), "fiat-checkpoint-identity-result/v1")
    ident = closed(value["identity"], ("schema", "run", "boundary", "evidence"), "fiat-checkpoint-identity/v1")
    run = closed(ident["run"], ("schema", "run_id", "repository", "task", "run_branch", "initial_base_sha", "integration_branch", "controller"), "fiat-run-anchor/v1")
    closed(run["controller"], ("name", "state_version", "version"))
    if run["controller"] != {"name": "hexctl", "state_version": 1, "version": "fiat-v6.61.1"} or type(run["controller"]["state_version"]) is not int:
        raise Refusal("native-producer-version-unavailable", "identity")
    hexadecimal(run["initial_base_sha"], commit=True)
    task = run["task"]
    if type(task) is not dict or task.get("kind") not in ("none", "github-issue", "external"):
        raise Refusal("native-anchor-unavailable", "identity")
    if task["kind"] == "none": closed(task, ("kind",))
    elif task["kind"] == "github-issue":
        closed(task, ("kind", "number")); count(task["number"], 2**63 - 1, minimum=1)
    else:
        closed(task, ("kind", "sha256")); hexadecimal(task["sha256"])
    if type(run["run_id"]) is not str or re.fullmatch(r"fiat-[0-9a-f]{64}", run["run_id"]) is None:
        raise Refusal("native-anchor-unavailable", "identity")
    for field in ("run_branch", "integration_branch"):
        if type(run[field]) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9/_.-]{0,1023}", run[field]) is None:
            raise Refusal("native-anchor-unavailable", "identity")
    if type(run["repository"]) is not str or re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", run["repository"]) is None or any(part in (".", "..") for part in run["repository"].split("/")):
        raise Refusal("native-anchor-unavailable", "identity")
    boundary = closed(ident["boundary"], ("kind", "step", "working_commit_sha"))
    if boundary["kind"] not in ("post-push", "audit-verdict"):
        raise Refusal("native-boundary-unavailable", "identity")
    count(boundary["step"], 4096, minimum=1); hexadecimal(boundary["working_commit_sha"], commit=True)
    evidence = closed(ident["evidence"], ("ledger_entries", "ledger_sha256", "ledger_tail", "observation_bindings", "observation_sha256", "observation_status", "policy_sha256", "run_anchor_sha256", "runbook_sha256", "state_fingerprint", "study_sha256"))
    count(evidence["ledger_entries"], minimum=1); count(evidence["observation_bindings"], minimum=1)
    for field in evidence:
        if field.endswith("sha256") or field in ("ledger_tail", "state_fingerprint"): hexadecimal(evidence[field])
    if evidence["observation_status"] != "bound" or evidence["run_anchor_sha256"] != digest(canonical(run)):
        raise Refusal("native-identity-join", "identity")
    if value["snapshot_id"] != digest(IDENTITY_DOMAIN + canonical(ident)):
        raise Refusal("native-identity-digest", "identity")
    return value
