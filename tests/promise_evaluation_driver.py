#!/usr/bin/env python3
"""Emit, tally, and verify isolated Promise Machine evaluation packets.

The driver stops at the model boundary. ``emit`` writes one self-contained
prompt per promise and a manifest last. An operator gives each prompt to one
fresh context and returns the raw response strings in one closed answer sheet.
``tally`` records only digests, bounded counts, and named failures; ``verify``
recomputes that record without changing a corpus. Nothing here calls a model,
opens a socket, reads a credential, or starts a child process.
"""

from __future__ import annotations

import argparse
from datetime import date as civil_date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = Path("tests/promise_machine_coverage.json")
PROMPT_TEMPLATE_PATH = Path(
    "tests/fixtures/promise-machine/evaluation/prompt-template.txt"
)
HEXAEMERON_PROMISES_PATH = Path("plugins/hexaemeron/PROMISES.md")
MANIFEST_NAME = "manifest.json"
PACKET_CONTRACT = "promise-machine-evaluation-packet/v1"
ANSWERS_CONTRACT = "promise-machine-evaluation-answers/v1"
RUN_CONTRACT = "promise-machine-evaluation-run/v1"
EVALUATION_CASE_SCHEMA = "promise-machine-evaluation-cases/v1"
EVALUATION_GATE = "labelled-case-classification"
DOMAIN_EVIDENCE_BOUNDARY = "required-separately"
RUN_DOMAIN_EVIDENCE = "not-supplied"
EVALUATION_KEYS = {
    "status",
    "model",
    "prompt",
    "corpus",
    "disposition",
    "gate",
    "run",
    "domain_evidence",
}
EXPECTED_CASES = 11
CASE_CODES = ("P", "M", "S", "O", "R")
# Do not preserve the semantic P/M/S/O/R ordering in a graded prompt. The
# context sees opaque scenario identities and has to read each scenario.
PROMPT_CASE_ORDER = ("O", "P", "R", "M", "S")
SCENARIO_IDS = tuple(f"E{number:02d}" for number in range(1, 6))
DISPOSITIONS = frozenset({"accept", "refuse", "recover"})
PROMISE_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MODEL_ID = re.compile(
    r"^[a-z][a-z0-9._-]*/[^@\s]+@sha256:[0-9a-f]{64}$",
    re.IGNORECASE,
)
MAX_COVERAGE_BYTES = 512 * 1024
MAX_CORPUS_BYTES = 256 * 1024
MAX_SKILL_BYTES = 512 * 1024
MAX_TEMPLATE_BYTES = 64 * 1024
MAX_MANIFEST_BYTES = 256 * 1024
MAX_PROMPT_BYTES = 512 * 1024
MAX_ANSWERS_BYTES = 1 << 20
MAX_ANSWER_BYTES = 16 * 1024
MAX_RUN_BYTES = 512 * 1024
OPEN_SUPPORTS_DIR_FD = os.open in getattr(os, "supports_dir_fd", set())
MKDIR_SUPPORTS_DIR_FD = os.mkdir in getattr(os, "supports_dir_fd", set())


class DriverError(Exception):
    """A fail-closed packet, answer, or run-record refusal."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _compact(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _duplicate_rejector(what: str):
    def reject(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DriverError(f"{what}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    return reject


def _decode_json(payload: bytes, what: str):
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DriverError(f"{what} is not UTF-8: {error}") from error
    try:
        return json.loads(text, object_pairs_hook=_duplicate_rejector(what))
    except DriverError:
        raise
    except json.JSONDecodeError as error:
        raise DriverError(f"{what} is not readable JSON: {error}") from error


def _path_has_escape(path: Path) -> bool:
    return ".." in path.parts


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


def _file_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )


def _open_relative_file(root: Path, relative: Path) -> int:
    if (
        not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_NONBLOCK")
        or not OPEN_SUPPORTS_DIR_FD
    ):
        raise OSError("platform lacks no-follow non-blocking descriptor reads")
    parts = relative.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise OSError("input path is not a safe relative file path")
    current = os.open(root, _directory_flags())
    descriptor = None
    try:
        if not stat.S_ISDIR(os.fstat(current).st_mode):
            raise OSError("input root is not a directory")
        for part in parts[:-1]:
            following = os.open(part, _directory_flags(), dir_fd=current)
            if not stat.S_ISDIR(os.fstat(following).st_mode):
                os.close(following)
                raise OSError(f"input path component is not a directory: {part}")
            os.close(current)
            current = following
        descriptor = os.open(parts[-1], _file_flags(), dir_fd=current)
        return descriptor
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        raise
    finally:
        os.close(current)


def _read_regular(
    path: Path,
    what: str,
    limit: int,
    *,
    root: Path | None = None,
) -> bytes:
    if _path_has_escape(path):
        raise DriverError(f"{what} contains a parent-directory escape")
    relative = None
    if root is not None:
        supplied_root = Path(root)
        root = supplied_root.resolve(strict=True)
        if path.is_absolute():
            try:
                relative = path.relative_to(supplied_root)
            except ValueError:
                try:
                    relative = path.relative_to(root)
                except ValueError as error:
                    raise DriverError(f"{what} resolves outside {root}") from error
        else:
            relative = path
    else:
        try:
            root = path.parent.resolve(strict=True)
        except OSError as error:
            raise DriverError(f"{what} parent could not be resolved: {error}") from error
        relative = Path(path.name)

    try:
        descriptor = _open_relative_file(root, relative)
    except OSError as error:
        raise DriverError(f"{what} could not be opened: {error}") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise DriverError(f"{what} is not a regular file")
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise DriverError(f"{what} is larger than {limit} bytes")
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise DriverError(f"{what} changed while it was read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _repository_file(root: Path, raw: str, what: str, limit: int) -> tuple[Path, bytes]:
    if not isinstance(raw, str) or not raw.strip():
        raise DriverError(f"{what} has no repository-relative path")
    relative = Path(raw)
    if relative.is_absolute() or _path_has_escape(relative):
        raise DriverError(f"{what} path is not repository-relative: {raw!r}")
    path = root / relative
    return path, _read_regular(path, what, limit, root=root)


def _coverage(root: Path) -> tuple[dict, bytes]:
    path = root / COVERAGE_PATH
    raw = _read_regular(path, COVERAGE_PATH.as_posix(), MAX_COVERAGE_BYTES, root=root)
    document = _decode_json(raw, COVERAGE_PATH.as_posix())
    if not isinstance(document, dict) or not isinstance(document.get("rows"), list):
        raise DriverError(f"{COVERAGE_PATH} has no rows list")
    return document, raw


def _target_rows(root: Path) -> list[dict]:
    document, _ = _coverage(root)
    selected = []
    for row in document["rows"]:
        if not isinstance(row, dict):
            continue
        evaluation = row.get("evaluation")
        if not isinstance(evaluation, dict):
            continue
        if evaluation.get("model") == "not-run":
            raise DriverError(
                f"coverage evaluation for {row.get('promise_id')!r} is explicitly not-run"
            )
        if evaluation.get("gate") == EVALUATION_GATE:
            selected.append(row)
    ids = [row.get("promise_id") for row in selected]
    if len(selected) != EXPECTED_CASES:
        raise DriverError(
            f"coverage discovers {len(selected)} fixture-only evaluations, not {EXPECTED_CASES}"
        )
    if any(not isinstance(item, str) or PROMISE_ID.fullmatch(item) is None for item in ids):
        raise DriverError("a fixture-only evaluation has a missing or malformed promise id")
    if len(set(ids)) != len(ids):
        raise DriverError("fixture-only evaluation promise ids are repeated")
    models = set()
    runs = set()
    for row in selected:
        promise_id = row["promise_id"]
        evaluation = row["evaluation"]
        if set(evaluation) != EVALUATION_KEYS or any(
            not isinstance(evaluation.get(key), str)
            or not evaluation[key].strip()
            or evaluation[key] != evaluation[key].strip()
            for key in EVALUATION_KEYS
        ):
            raise DriverError(
                f"coverage evaluation for {promise_id} is not a closed non-empty gate record"
            )
        if evaluation["status"] != "recorded":
            raise DriverError(f"coverage evaluation for {promise_id} is not recorded")
        if MODEL_ID.fullmatch(evaluation["model"]) is None:
            raise DriverError(
                f"coverage evaluation for {promise_id} has no full model identity"
            )
        if evaluation["domain_evidence"] != DOMAIN_EVIDENCE_BOUNDARY:
            raise DriverError(
                f"coverage evaluation for {promise_id} does not keep domain evidence separate"
            )
        if (
            not isinstance(row.get("group"), str)
            or row["group"] not in {"prompt", "vendored"}
        ):
            raise DriverError(f"coverage evaluation for {promise_id} has no supported group")
        if not isinstance(row.get("skill_path"), str) or not row["skill_path"].strip():
            raise DriverError(f"coverage evaluation for {promise_id} has no skill path")
        models.add(evaluation["model"])
        runs.add(evaluation["run"])
    if len(models) != 1 or len(runs) != 1:
        raise DriverError("fixture-only evaluations do not bind one model and run record")
    return sorted(selected, key=lambda row: row["promise_id"])


def _declared_model(root: Path) -> str:
    return next(iter({row["evaluation"]["model"] for row in _target_rows(root)}))


def _contract_section(source: str, promise_id: str, path: str) -> str:
    marker = f"### {promise_id}"
    start = source.find(marker)
    if start < 0:
        raise DriverError(f"{path} carries no {marker!r} declaration")
    if source.find(marker, start + len(marker)) >= 0:
        raise DriverError(f"{path} repeats {marker!r}")
    end = source.find("\n### ", start + len(marker))
    section = source[start : end if end >= 0 else None].strip() + "\n"
    required = (
        "Promise",
        "Evidence",
        "Evidence classes",
        "Boundary",
        "Authorises",
        "Consequence",
        "Refuses",
        "Recovery",
        "Exceptions",
    )
    if not all(f"\n- {field}:" in "\n" + section for field in required):
        raise DriverError(f"{path} has an incomplete {promise_id} declaration")
    return section


def _case_record(document: dict, promise_id: str, path: str) -> dict:
    if (
        not isinstance(document, dict)
        or set(document) != {"schema", "cases"}
        or document.get("schema") != EVALUATION_CASE_SCHEMA
    ):
        raise DriverError(f"{path} declares an unsupported evaluation-case schema")
    cases = document.get("cases")
    if not isinstance(cases, dict) or promise_id not in cases:
        raise DriverError(f"{path} carries no case for {promise_id}")
    record = cases[promise_id]
    if not isinstance(record, dict):
        raise DriverError(f"{path}: {promise_id} is not an object")
    if set(record) != set(CASE_CODES) | {"request"}:
        raise DriverError(f"{path}: {promise_id} has an open or incomplete case shape")
    if not isinstance(record.get("request"), str) or not record["request"].strip():
        raise DriverError(f"{path}: {promise_id} has no request")
    for code in CASE_CODES:
        value = record.get(code)
        if (
            not isinstance(value, dict)
            or set(value) != {"disposition", "scenario", "boundary"}
            or not isinstance(value.get("disposition"), str)
            or value["disposition"] not in DISPOSITIONS
            or not isinstance(value.get("scenario"), str)
            or not value["scenario"].strip()
            or not isinstance(value.get("boundary"), str)
            or not value["boundary"].strip()
        ):
            raise DriverError(f"{path}: {promise_id}.{code} is malformed")
    return record


def load_cases(root: Path = REPOSITORY_ROOT) -> list[dict]:
    root = Path(root).resolve(strict=True)
    rows = _target_rows(root)
    corpus_cache: dict[str, dict] = {}
    assigned: dict[str, set[str]] = {}
    for row in rows:
        corpus_raw = row["evaluation"]["corpus"]
        assigned.setdefault(corpus_raw, set()).add(row["promise_id"])
    for corpus_raw, promise_ids in assigned.items():
        _, corpus_bytes = _repository_file(
            root,
            corpus_raw,
            f"evaluation corpus for {sorted(promise_ids)}",
            MAX_CORPUS_BYTES,
        )
        document = _decode_json(corpus_bytes, corpus_raw)
        if (
            not isinstance(document, dict)
            or set(document) != {"schema", "cases"}
            or document.get("schema") != EVALUATION_CASE_SCHEMA
            or not isinstance(document.get("cases"), dict)
            or set(document["cases"]) != promise_ids
        ):
            raise DriverError(
                f"{corpus_raw} is not the closed corpus for its exact assigned promise set"
            )
        corpus_cache[corpus_raw] = document
    cases = []
    for row in rows:
        promise_id = row["promise_id"]
        evaluation = row["evaluation"]
        corpus_raw = evaluation.get("corpus")
        record = _case_record(corpus_cache[corpus_raw], promise_id, corpus_raw)
        request = evaluation.get("prompt")
        if not isinstance(request, str) or not request.strip():
            raise DriverError(f"coverage evaluation for {promise_id} carries no request")
        if record["request"] != request:
            raise DriverError(
                f"{corpus_raw}: {promise_id} request disagrees with coverage"
            )
        skill_raw = (
            HEXAEMERON_PROMISES_PATH.as_posix()
            if row.get("group") == "vendored"
            else row.get("skill_path")
        )
        skill_path, skill_bytes = _repository_file(
            root, skill_raw, f"canonical contract for {promise_id}", MAX_SKILL_BYTES
        )
        try:
            skill_text = skill_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DriverError(f"{skill_raw} is not UTF-8: {error}") from error
        scenarios = []
        for scenario_id, code in zip(SCENARIO_IDS, PROMPT_CASE_ORDER):
            source = record[code]
            scenarios.append(
                {
                    "id": scenario_id,
                    "text": source["scenario"],
                    "expected": source["disposition"],
                    "boundary": source["boundary"],
                }
            )
        cases.append(
            {
                "id": promise_id,
                "skill_path": skill_path.relative_to(root).as_posix(),
                "request": request,
                "contract": _contract_section(skill_text, promise_id, skill_raw),
                "scenarios": scenarios,
            }
        )
    return cases


def _source_inventory(root: Path) -> list[dict]:
    root = Path(root).resolve(strict=True)
    rows = _target_rows(root)
    paths = {COVERAGE_PATH, PROMPT_TEMPLATE_PATH}
    for row in rows:
        paths.add(Path(row["skill_path"]))
        if row.get("group") == "vendored":
            paths.add(HEXAEMERON_PROMISES_PATH)
        paths.add(Path(row["evaluation"]["corpus"]))
    inventory = []
    for relative in sorted(paths, key=lambda item: item.as_posix()):
        _, raw = _repository_file(
            root,
            relative.as_posix(),
            f"evaluation input {relative.as_posix()}",
            max(MAX_COVERAGE_BYTES, MAX_SKILL_BYTES),
        )
        inventory.append({"path": relative.as_posix(), "sha256": _sha256(raw)})
    return inventory


def input_files(root: Path = REPOSITORY_ROOT) -> list[Path]:
    root = Path(root).resolve(strict=True)
    return [root / item["path"] for item in _source_inventory(root)]


def _corpus_digest(root: Path) -> str:
    rows = _target_rows(root)
    paths = sorted({row["evaluation"]["corpus"] for row in rows})
    inventory = []
    for raw_path in paths:
        _, raw = _repository_file(
            root, raw_path, f"evaluation corpus {raw_path}", MAX_CORPUS_BYTES
        )
        inventory.append({"path": raw_path, "sha256": _sha256(raw)})
    return _sha256(_compact(inventory))


def _tree_digest(root: Path) -> str:
    return _sha256(_compact(_source_inventory(root)))


def _template(root: Path) -> tuple[str, str]:
    path = root / PROMPT_TEMPLATE_PATH
    raw = _read_regular(
        path, PROMPT_TEMPLATE_PATH.as_posix(), MAX_TEMPLATE_BYTES, root=root
    )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DriverError(f"{PROMPT_TEMPLATE_PATH} is not UTF-8: {error}") from error
    required = ("{promise_id}", "{skill_path}", "{contract}", "{request}", "{scenarios}")
    for placeholder in required:
        if text.count(placeholder) != 1:
            raise DriverError(
                f"{PROMPT_TEMPLATE_PATH} must contain {placeholder} exactly once"
            )
    return text, _sha256(raw)


def render_prompt(case: dict, *, root: Path = REPOSITORY_ROOT) -> str:
    template, _ = _template(Path(root).resolve(strict=True))
    scenario_text = "\n".join(
        f"{item['id']}. {item['text']}" for item in case["scenarios"]
    )
    values = {
        "{promise_id}": case["id"],
        "{skill_path}": case["skill_path"],
        "{contract}": case["contract"].rstrip(),
        "{request}": case["request"],
        "{scenarios}": scenario_text,
    }
    placeholders = re.compile(
        "|".join(re.escape(placeholder) for placeholder in values)
    )
    rendered, substitutions = placeholders.subn(
        lambda match: values[match.group(0)], template
    )
    if substitutions != len(values):
        raise DriverError("the prompt template retained an unsubstituted placeholder")
    return rendered


def _write_member(directory_fd: int, name: str, payload: bytes) -> None:
    if Path(name).name != name or not name:
        raise DriverError(f"unsafe packet member name: {name!r}")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _new_output_directory(out: Path) -> int:
    if _path_has_escape(out):
        raise DriverError(f"{out} contains a parent-directory escape")
    if out.exists() or out.is_symlink():
        raise DriverError(f"{out} already exists")
    if not hasattr(os, "O_NOFOLLOW") or not MKDIR_SUPPORTS_DIR_FD:
        raise DriverError("platform lacks no-follow descriptor-relative directory creation")
    parent = out.parent
    try:
        resolved_parent = parent.resolve(strict=True)
    except OSError as error:
        raise DriverError(f"{parent} could not be resolved: {error}") from error
    if not resolved_parent.is_dir():
        raise DriverError(f"{parent} is not a directory")
    parent_fd = None
    try:
        parent_fd = os.open(resolved_parent, _directory_flags())
        os.mkdir(out.name, mode=0o700, dir_fd=parent_fd)
        os.fsync(parent_fd)
        return os.open(out.name, _directory_flags(), dir_fd=parent_fd)
    except OSError as error:
        raise DriverError(f"{out} could not be created safely: {error}") from error
    finally:
        if parent_fd is not None:
            os.close(parent_fd)


def emit(out: Path, *, root: Path = REPOSITORY_ROOT) -> dict:
    root = Path(root).resolve(strict=True)
    out = Path(out)
    cases = load_cases(root)
    _, template_sha256 = _template(root)
    manifest = {
        "contract": PACKET_CONTRACT,
        "prompt_template_sha256": template_sha256,
        "corpus_sha256": _corpus_digest(root),
        "tree_sha256": _tree_digest(root),
        "cases": [],
    }
    directory_fd = _new_output_directory(out)
    try:
        for case in cases:
            name = f"{case['id']}.txt"
            payload = render_prompt(case, root=root).encode("utf-8")
            if len(payload) > MAX_PROMPT_BYTES:
                raise DriverError(f"prompt for {case['id']} is too large")
            _write_member(directory_fd, name, payload)
            manifest["cases"].append(
                {
                    "id": case["id"],
                    "prompt": name,
                    "prompt_sha256": _sha256(payload),
                    "scenarios": list(SCENARIO_IDS),
                }
            )
        # This write is deliberately last. A killed emit has prompt fragments
        # but no packet authority, so tally refuses it at the first read.
        _write_member(directory_fd, MANIFEST_NAME, _canonical(manifest))
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return manifest


def _load_manifest(packet: Path) -> dict:
    if _path_has_escape(packet):
        raise DriverError(f"{packet} contains a parent-directory escape")
    if packet.is_symlink() or not packet.is_dir():
        raise DriverError(f"{packet} is not a real packet directory")
    raw = _read_regular(
        packet / MANIFEST_NAME,
        f"{packet / MANIFEST_NAME}",
        MAX_MANIFEST_BYTES,
        root=packet,
    )
    manifest = _decode_json(raw, str(packet / MANIFEST_NAME))
    required = {
        "contract",
        "prompt_template_sha256",
        "corpus_sha256",
        "tree_sha256",
        "cases",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise DriverError(f"{packet / MANIFEST_NAME} has an open or incomplete shape")
    if manifest.get("contract") != PACKET_CONTRACT:
        raise DriverError(f"{packet / MANIFEST_NAME} declares another contract")
    for field in ("prompt_template_sha256", "corpus_sha256", "tree_sha256"):
        if not isinstance(manifest.get(field), str) or SHA256.fullmatch(manifest[field]) is None:
            raise DriverError(f"{packet / MANIFEST_NAME} has no valid {field}")
    records = manifest.get("cases")
    if not isinstance(records, list) or len(records) != EXPECTED_CASES:
        raise DriverError(f"{packet / MANIFEST_NAME} does not name {EXPECTED_CASES} cases")
    seen = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {
            "id", "prompt", "prompt_sha256", "scenarios"
        }:
            raise DriverError(f"{packet / MANIFEST_NAME} has a malformed case record")
        case_id = record.get("id")
        if not isinstance(case_id, str) or PROMISE_ID.fullmatch(case_id) is None:
            raise DriverError(f"{packet / MANIFEST_NAME} has a malformed case id")
        if case_id in seen:
            raise DriverError(f"{packet / MANIFEST_NAME} repeats {case_id}")
        seen.add(case_id)
        if record.get("prompt") != f"{case_id}.txt":
            raise DriverError(f"{packet / MANIFEST_NAME} gives {case_id} an unsafe prompt path")
        if not isinstance(record.get("prompt_sha256"), str) or SHA256.fullmatch(record["prompt_sha256"]) is None:
            raise DriverError(f"{packet / MANIFEST_NAME} has no prompt digest for {case_id}")
        if record.get("scenarios") != list(SCENARIO_IDS):
            raise DriverError(f"{packet / MANIFEST_NAME} changes {case_id}'s scenario set")
    return manifest


def _validate_packet(packet: Path, manifest: dict, root: Path) -> list[dict]:
    cases = load_cases(root)
    by_id = {case["id"]: case for case in cases}
    expected_ids = sorted(by_id)
    manifest_ids = [record["id"] for record in manifest["cases"]]
    if manifest_ids != expected_ids:
        raise DriverError("the packet case set does not match current discovery")
    _, template_sha256 = _template(root)
    comparisons = {
        "prompt_template_sha256": template_sha256,
        "corpus_sha256": _corpus_digest(root),
        "tree_sha256": _tree_digest(root),
    }
    for field, current in comparisons.items():
        if manifest[field] != current:
            raise DriverError(
                f"the packet {field} is {manifest[field]}, but current inputs are {current}"
            )
    expected_names = {MANIFEST_NAME} | {record["prompt"] for record in manifest["cases"]}
    actual_names = set()
    with os.scandir(packet) as entries:
        for entry in entries:
            actual_names.add(entry.name)
            if len(actual_names) > EXPECTED_CASES + 1:
                raise DriverError("the packet has more members than the closed case set")
    if actual_names != expected_names:
        raise DriverError("the packet has missing or extra members")
    for record in manifest["cases"]:
        prompt_path = packet / record["prompt"]
        payload = _read_regular(
            prompt_path,
            str(prompt_path),
            MAX_PROMPT_BYTES,
            root=packet,
        )
        if _sha256(payload) != record["prompt_sha256"]:
            raise DriverError(f"the prompt for {record['id']} was edited after emit")
        expected = render_prompt(by_id[record["id"]], root=root).encode("utf-8")
        if payload != expected:
            raise DriverError(f"the prompt for {record['id']} is not the current isolated request")
    return cases


def _load_answers(path: Path, expected_ids: list[str]) -> dict[str, str]:
    raw = _read_regular(path, str(path), MAX_ANSWERS_BYTES)
    document = _decode_json(raw, str(path))
    if not isinstance(document, dict) or set(document) != {"contract", "answers"}:
        raise DriverError(f"{path} has an open or incomplete answer-sheet shape")
    if document.get("contract") != ANSWERS_CONTRACT:
        raise DriverError(f"{path} declares another answer-sheet contract")
    answers = document.get("answers")
    if not isinstance(answers, dict):
        raise DriverError(f"{path} has no answers object")
    expected = set(expected_ids)
    given = set(answers)
    missing = sorted(expected - given)
    extra = sorted(given - expected)
    if missing:
        raise DriverError(f"{path} has no raw answer for {missing}")
    if extra:
        raise DriverError(f"{path} carries answers the packet did not ask: {extra}")
    for case_id in expected_ids:
        answer = answers[case_id]
        if not isinstance(answer, str) or not answer.strip():
            raise DriverError(f"{path}: {case_id} has no raw answer")
        if answer.strip().lower() == "not-run":
            raise DriverError(f"{path}: {case_id} is explicitly not-run")
        if len(answer.encode("utf-8")) > MAX_ANSWER_BYTES:
            raise DriverError(f"{path}: {case_id} answer is larger than {MAX_ANSWER_BYTES} bytes")
        parsed = _decode_json(answer.encode("utf-8"), f"{path}: {case_id}")
        if not isinstance(parsed, dict) or set(parsed) != set(SCENARIO_IDS):
            raise DriverError(f"{path}: {case_id} is missing, partial, or has extra scenarios")
        for scenario_id, disposition in parsed.items():
            if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
                raise DriverError(
                    f"{path}: {case_id}.{scenario_id} uses the open disposition {disposition!r}"
                )
    return {case_id: answers[case_id] for case_id in expected_ids}


def _validate_model_and_date(model: str, date: str) -> None:
    if not isinstance(model, str) or MODEL_ID.fullmatch(model) is None:
        raise DriverError(
            "the model must be a full provider/name@sha256:<64-hex> identity"
        )
    try:
        parsed = civil_date.fromisoformat(date)
    except (TypeError, ValueError) as error:
        raise DriverError(f"{date!r} is not a real YYYY-MM-DD date") from error
    if parsed.isoformat() != date:
        raise DriverError(f"{date!r} is not a canonical YYYY-MM-DD date")


def _build_run(
    manifest: dict,
    cases: list[dict],
    answers: dict[str, str],
    model: str,
    date: str,
) -> dict:
    _validate_model_and_date(model, date)
    answer_records = []
    failures = []
    passed = 0
    for case in cases:
        raw = answers[case["id"]]
        selected = _decode_json(raw.encode("utf-8"), f"raw answer for {case['id']}")
        expected = {item["id"]: item["expected"] for item in case["scenarios"]}
        case_passed = 0
        for scenario_id in SCENARIO_IDS:
            if selected[scenario_id] == expected[scenario_id]:
                case_passed += 1
            else:
                failures.append(
                    {
                        "case": case["id"],
                        "scenario": scenario_id,
                        "selected": selected[scenario_id],
                    }
                )
        passed += case_passed
        answer_records.append(
            {
                "case": case["id"],
                "sha256": _sha256(raw.encode("utf-8")),
                "bytes": len(raw.encode("utf-8")),
                "passed": case_passed,
                "failed": len(SCENARIO_IDS) - case_passed,
            }
        )
    return {
        "contract": RUN_CONTRACT,
        "model": model,
        "date": date,
        "prompt_template_sha256": manifest["prompt_template_sha256"],
        "corpus_sha256": manifest["corpus_sha256"],
        "tree_sha256": manifest["tree_sha256"],
        "cases": [case["id"] for case in cases],
        "answers": answer_records,
        "counts": {
            "answers": len(answer_records),
            "cases": len(cases),
            "outcomes": len(cases) * len(SCENARIO_IDS),
            "passed": passed,
            "failed": len(failures),
        },
        "failures": failures,
        "domain_evidence": RUN_DOMAIN_EVIDENCE,
    }


def _exclusive_write_path(path: Path, payload: bytes) -> None:
    if _path_has_escape(path):
        raise DriverError(f"{path} contains a parent-directory escape")
    if path.exists() or path.is_symlink():
        raise DriverError(f"{path} already exists")
    parent = path.parent
    try:
        resolved_parent = parent.resolve(strict=True)
    except OSError as error:
        raise DriverError(f"{parent} could not be resolved: {error}") from error
    directory_fd = os.open(
        resolved_parent,
        _directory_flags(),
    )
    try:
        _write_member(directory_fd, path.name, payload)
        os.fsync(directory_fd)
    except OSError as error:
        raise DriverError(f"{path} could not be created safely: {error}") from error
    finally:
        os.close(directory_fd)


def tally(
    packet: Path,
    answers: Path,
    out: Path,
    model: str,
    date: str,
    *,
    root: Path = REPOSITORY_ROOT,
) -> dict:
    root = Path(root).resolve(strict=True)
    packet = Path(packet)
    answers = Path(answers)
    out = Path(out)
    if out.exists() or out.is_symlink() or _path_has_escape(out):
        raise DriverError(f"{out} is not a new confined run-record path")
    if model != _declared_model(root):
        raise DriverError("the tally model does not match the identity bound in coverage")
    manifest = _load_manifest(packet)
    cases = _validate_packet(packet, manifest, root)
    raw_answers = _load_answers(answers, [case["id"] for case in cases])
    run = _build_run(manifest, cases, raw_answers, model, date)
    _exclusive_write_path(out, _canonical(run))
    return run


def verify(
    packet: Path,
    answers: Path,
    run: Path,
    *,
    root: Path = REPOSITORY_ROOT,
) -> dict:
    root = Path(root).resolve(strict=True)
    packet = Path(packet)
    answers = Path(answers)
    run = Path(run)
    manifest = _load_manifest(packet)
    cases = _validate_packet(packet, manifest, root)
    raw_answers = _load_answers(answers, [case["id"] for case in cases])
    raw_run = _read_regular(run, str(run), MAX_RUN_BYTES)
    recorded = _decode_json(raw_run, str(run))
    if not isinstance(recorded, dict):
        raise DriverError(f"{run} is not an object")
    model = recorded.get("model")
    date = recorded.get("date")
    if model != _declared_model(root):
        raise DriverError("the run model does not match the identity bound in coverage")
    expected = _build_run(manifest, cases, raw_answers, model, date)
    if recorded != expected or raw_run != _canonical(expected):
        raise DriverError(f"{run} does not match the packet and raw answer identities")
    return expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)
    emitter = subparsers.add_parser("emit", help="write one isolated prompt per case")
    emitter.add_argument("--out", required=True)
    scorer = subparsers.add_parser("tally", help="tally one closed raw answer sheet")
    scorer.add_argument("--packet", required=True)
    scorer.add_argument("--answers", required=True)
    scorer.add_argument("--out", required=True)
    scorer.add_argument("--model", required=True)
    scorer.add_argument("--date", required=True)
    verifier = subparsers.add_parser("verify", help="verify a recorded tally")
    verifier.add_argument("--packet", required=True)
    verifier.add_argument("--answers", required=True)
    verifier.add_argument("--run", required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve(strict=True) if args.root else REPOSITORY_ROOT
    try:
        if args.command == "emit":
            manifest = emit(Path(args.out), root=root)
            print(
                "promise-evaluation packet cases=%d corpus_sha256=%s "
                "tree_sha256=%s prompt_template_sha256=%s"
                % (
                    len(manifest["cases"]),
                    manifest["corpus_sha256"],
                    manifest["tree_sha256"],
                    manifest["prompt_template_sha256"],
                )
            )
        elif args.command == "tally":
            record = tally(
                Path(args.packet),
                Path(args.answers),
                Path(args.out),
                args.model,
                args.date,
                root=root,
            )
            print(
                "promise-evaluation run model=%s date=%s cases=%d passed=%d failed=%d"
                % (
                    record["model"],
                    record["date"],
                    record["counts"]["cases"],
                    record["counts"]["passed"],
                    record["counts"]["failed"],
                )
            )
        else:
            record = verify(
                Path(args.packet), Path(args.answers), Path(args.run), root=root
            )
            print(
                "promise-evaluation verified model=%s date=%s cases=%d passed=%d failed=%d"
                % (
                    record["model"],
                    record["date"],
                    record["counts"]["cases"],
                    record["counts"]["passed"],
                    record["counts"]["failed"],
                )
            )
    except (DriverError, OSError) as error:
        print(f"promise_evaluation_driver: error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
