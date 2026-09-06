#!/usr/bin/env python3
"""Kronos ranking scoreboard.

Kronos scores every eligible held Fiat job out of 100, prints the result, runs
the winner, and then reranks from scratch. Nothing carries between passes, so a
job can score 62 in one pass and 78 three passes later with nothing about it
changed. This appends each pass to a file so that movement is visible.

  record  read a pass on stdin, validate it, append exactly one JSON line
  show    print the recorded passes and mark every axis score that moved for a
          candidate whose held job did not
  pull    copy the working copy from refs/heads/kronos/state
  push    fast-forward that ref from the working copy

  K000  a path that cannot be read
  K001  stdin that is not a JSON object
  K002  a required field that is missing
  K003  a field the record does not carry
  K004  an axis outside its range
  K005  a stated total that disagrees with the axes
  K006  a selection that is not what the tie-break picks
  K007  a candidate ledger that cannot be used
  K008  an existing scoreboard line that cannot be read
  K009  more candidates than the check will track
  K010  a scoreboard directory that is not a real directory
  K011  a halt reason that is empty or over the cap
  K012  a park for a skill that is already parked
  K013  an unpark with no standing park to release
  K014  a parked flag that disagrees with the standing parks
  K015  a pass in which every candidate is parked
  K016  a rank-only pass that names a Fiat run
  K017  an ungoverned list that is too long or holds something that is not a name
  K018  an existing state ref that cannot be read
  K019  a state-ref push that is not a fast-forward
  K020  a remote that is a URL or not a configured name
  K021  git could not start, timed out, or exceeded the output cap
  K022  a declared-inputs block that breaks the shape VERSIONING.md defines

Exit 0 clean, 1 a refusal, 2 bad invocation, and 3 from `parked` alone while a
park stands. That last is not an error in the tool. It is the loop's reason not
to declare itself finished, which is why it needs a code of its own rather than
the one argparse already spends on a bad invocation. A refusal appends nothing:
a pass, a park and an unpark are each recorded whole or not at all.

The held-job identity hash is not supplied by the caller. It is computed here
from the candidate's ledger, as the SHA-256 of the canonical frontier line that
VERSIONING.md already defines, which is the same digest each ledger stores in
its own history row. A line written here can therefore be checked against the
ledger it describes.

What a ledger declared it needs is read the same way, from the same bytes, and
is likewise refused as an unknown field when a caller states it. VERSIONING.md
defines the optional declared-inputs block and tests/test_evolution_contract.py
checks every governed ledger against it; this reads one. `declared_inputs` is
an object when the ledger declared and null when it did not, and its digest
covers the rows rather than the block's bytes, so `show` can mark a declaration
that moved under a held job that did not. `show` prints each candidate's
declared rows beside its scores, and `declared: none` where the recorded line
carries no declaration. Every recorded string it prints is collapsed to one
line first, so a scope, skill, basis, run or row a caller wrote cannot open a
line of its own and spell a `declared:` heading no ledger carried. A
declaration is a claim its ledger's owner makes. Nothing here checks that a
declared input exists.

What this does not do. It records a judgement; it does not make one. An axis
score is a number the ranking agent supplies, and a basis is prose nobody
parses. It also cannot tell that a pass went unrecorded, because a loop that
skips this writer leaves a shorter file and nothing else.

The trust boundary is stdin, the argument list, and, for pull and push only, a
git subprocess. Ranking verbs start no subprocess and open no socket. The pass
document arrives from a caller and is read with a byte cap, an unknown field is
refused rather than stored, and the candidate count is capped. Each candidate
names a ledger path the caller chose, so that path is resolved, required to be a
regular file under the scoreboard's root, and read under a cap. Inside that
file, a declared-inputs block is bounded again: a row count, a whole-block byte
cap, an id and a note cap, and two closed vocabularies. A row breaking any of
them refuses the pass. An existing scoreboard is validated line by line before
anything is appended, so a run interrupted mid-append is refused rather than
written past.

pull and push copy the two JSONL files through a throwaway clone under the
system temp directory. Git is invoked with a fixed argv list, no shell, a
30-second timeout and a 2 MiB output cap. The remote is a configured remote
name, or KRONOS_STATE_REMOTE when that name is already configured; a URL
argument is refused. Git stderr is not copied into Kronos diagnostics. A
missing state ref is an empty start. An existing ref that cannot be read
refuses rather than clearing parks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Kronos SKILL.md step 3. The caps sum to 100, which is what "out of 100" means.
AXES = (("impact", 40), ("urgency", 25), ("readiness", 20), ("unblocks", 15))

CANDIDATE_FIELDS = frozenset(
    {"skill", "ledger", "basis", "total", "parked"} | {name for name, _ in AXES}
)
CANDIDATE_REQUIRED = ("skill", "ledger", "basis") + tuple(name for name, _ in AXES)
PASS_FIELDS = frozenset(
    {"scope", "mode", "candidates", "selected", "run", "rank_only", "ungoverned"}
)
PASS_REQUIRED = ("scope", "mode", "candidates", "selected")
MODES = ("full", "phase-only")

# Documents somebody handed over. Bound every axis that a caller controls.
MAX_STDIN_BYTES = 1024 * 1024
MAX_LEDGER_BYTES = 1024 * 1024
MAX_SCOREBOARD_BYTES = 16 * 1024 * 1024
MAX_CANDIDATES = 200
MAX_REASON_BYTES = 4096
MAX_UNGOVERNED = 200
STANDS = 3
GIT_TIMEOUT_SECONDS = 30
GIT_OUTPUT_CAP = 2 * 1024 * 1024

LEDGER_FIELDS = ("Frontier status", "Frontier revision", "Current frontier", "Next Fiat job")

# VERSIONING.md's optional declared-inputs block, made readable here. The rules
# are its own and tests/test_evolution_contract.py checks all 27 governed
# ledgers against them; these restate rather than import them because this
# script ships inside a plugin that carries neither file. A reader that
# accepted what that check refuses would be a second contract, so
# test_kronos_scoreboard.py holds the two to one verdict over every specimen.
DECLARED_INFO = "declared-inputs"
MAX_DECLARED_ROWS = 16
MAX_DECLARED_BLOCK_BYTES = 4096
MAX_DECLARED_ID_BYTES = 64
MAX_DECLARED_NOTE_BYTES = 200
DECLARED_KINDS = frozenset({"credential", "endpoint", "person", "corpus", "tool"})
DECLARED_AVAILABILITY = frozenset({"available", "absent", "unknown"})
DECLARED_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FENCE = re.compile(r"^ {0,3}(?P<mark>`{3,}|~{3,})(?P<info>.*)$")
HEADER_BULLET = re.compile(r"^- [^:]+: .+$")
HISTORY_HEADING = "## History"

PARK_EVENTS = ("park", "unpark")
PARKED_NAME = "parked.jsonl"
SCOREBOARD_NAME = "scoreboard.jsonl"
STATE_BLOBS = (SCOREBOARD_NAME, PARKED_NAME)
STATE_REF = "refs/heads/kronos/state"
REMOTE_ENV = "KRONOS_STATE_REMOTE"
TIP_NAME = "tip"


class Refusal(Exception):
    """A validation failure, carrying the code that names it."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def ledger_field(text: str, name: str) -> str:
    """One `- Name: value` line from a ledger, matching the contract test."""
    match = re.search(rf"(?m)^- {re.escape(name)}: (.+)$", text)
    if match is None:
        raise Refusal("K007", f"ledger has no {name!r} field")
    return match.group(1).strip().strip("`")


def held_job_from_text(text: str) -> str:
    """SHA-256 of the canonical frontier line VERSIONING.md defines."""
    canonical = "|".join(ledger_field(text, name) for name in LEDGER_FIELDS) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def held_job_hash(ledger: Path) -> str:
    """The same digest, for a caller holding the path rather than the bytes."""
    return held_job_from_text(read_capped(ledger, MAX_LEDGER_BYTES, "K007"))


def ledger_structure(text: str) -> tuple:
    """Every fenced region, and every line outside one, from a single walk.

    The contract check reads these as two functions over the same lines. They
    run one state machine between them, because a line is visible exactly when
    it is not a fence and no block is open, so this walks the ledger once.
    """
    blocks, visible, current = [], [], None
    for index, line in enumerate(text.splitlines()):
        fence = FENCE.match(line)
        if fence is None:
            if current is None:
                visible.append((index, line))
            else:
                current["rows"].append(line)
                current["raw"].append(line)
            continue
        sequence, info = fence.group("mark"), fence.group("info").strip()
        if current is None:
            current = {
                "start": index,
                "mark": sequence[0],
                "length": len(sequence),
                "info": info,
                "rows": [],
                "raw": [line],
                "closed": False,
            }
        elif sequence[0] == current["mark"] and len(sequence) >= current["length"] and not info:
            current["closed"] = True
            current["raw"].append(line)
            blocks.append(current)
            current = None
        else:
            current["rows"].append(line)
            current["raw"].append(line)
    if current is not None:
        blocks.append(current)
    return blocks, visible


def declared_block(text: str, where: str) -> dict | None:
    """The ledger's one declared-inputs block, or None where it declared nothing."""
    blocks, visible = ledger_structure(text)
    for block in blocks:
        # Refused before the placement rules, because an unclosed fence
        # swallows the History heading the placement rules are measured from.
        if not block["closed"]:
            raise Refusal("K022", f"{where} leaves a fenced block never closed")
    declared = [block for block in blocks if block["info"] == DECLARED_INFO]
    if len(declared) > 1:
        raise Refusal("K022", f"{where} carries {len(declared)} declared-inputs blocks, where at most one is allowed")
    if not declared:
        return None
    block = declared[0]
    history = [index for index, line in visible if line == HISTORY_HEADING]
    limit = history[0] if history else len(text.splitlines())
    bullets = [index for index, line in visible if index < limit and HEADER_BULLET.fullmatch(line)]
    if bullets and block["start"] < bullets[-1]:
        raise Refusal("K022", f"{where} opens its declared-inputs block above the last frontier header bullet")
    if history and block["start"] > history[0]:
        raise Refusal("K022", f"{where} opens its declared-inputs block below the History heading")
    return block


def declared_rows(block: dict, where: str) -> list:
    """One record per declared input, refusing the first row that breaks shape."""
    rows = [line for line in block["rows"] if line.strip()]
    if len(rows) > MAX_DECLARED_ROWS:
        raise Refusal("K022", f"{where} declares {len(rows)} inputs, over the {MAX_DECLARED_ROWS} cap")
    measured = len(("\n".join(block["raw"]) + "\n").encode("utf-8"))
    if measured > MAX_DECLARED_BLOCK_BYTES:
        raise Refusal("K022", f"{where} declares {measured} bytes, over the {MAX_DECLARED_BLOCK_BYTES} cap")
    declared, seen = [], set()
    for line in rows:
        if line.lstrip()[:1] in {"-", "|", "`"}:
            raise Refusal("K022", f"{where} declares a row opening with a hyphen, a pipe or a backtick")
        fields = [part.strip() for part in line.split("|")]
        if len(fields) != 4:
            raise Refusal("K022", f"{where} declares a row of {len(fields)} fields rather than four")
        if not all(fields):
            raise Refusal("K022", f"{where} declares a row carrying an empty field")
        identifier, kind, availability, note = fields
        if DECLARED_ID.fullmatch(identifier) is None:
            raise Refusal("K022", f"{where} declares id {identifier!r}, which is not kebab-case")
        size = len(identifier.encode("utf-8"))
        if size > MAX_DECLARED_ID_BYTES:
            raise Refusal("K022", f"{where} declares an id of {size} bytes, over the {MAX_DECLARED_ID_BYTES} cap")
        if identifier in seen:
            raise Refusal("K022", f"{where} declares id {identifier!r} twice")
        seen.add(identifier)
        if kind not in DECLARED_KINDS:
            raise Refusal("K022", f"{where} declares kind {kind!r}, outside the closed set")
        if availability not in DECLARED_AVAILABILITY:
            raise Refusal("K022", f"{where} declares availability {availability!r}, outside the closed set")
        size = len(note.encode("utf-8"))
        if size > MAX_DECLARED_NOTE_BYTES:
            raise Refusal("K022", f"{where} declares a note of {size} bytes, over the {MAX_DECLARED_NOTE_BYTES} cap")
        declared.append(
            {"id": identifier, "kind": kind, "availability": availability, "note": note}
        )
    return declared


def declaration_digest(rows: list) -> str:
    """SHA-256 over the canonical rows, built the way the frontier line is.

    The fields are digested rather than the block's own bytes, so re-spacing a
    row or moving the block within its allowed span states no new claim and
    does not read as a declaration somebody changed.
    """
    canonical = "".join(
        "|".join((row["id"], row["kind"], row["availability"], row["note"])) + "\n"
        for row in rows
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def declaration(text: str, where: str) -> dict | None:
    """What a ledger declared it needs, or None where it declared nothing."""
    block = declared_block(text, where)
    if block is None:
        return None
    rows = declared_rows(block, where)
    return {"digest": declaration_digest(rows), "rows": rows}


def read_capped(path: Path, cap: int, code: str) -> str:
    """Read a regular file under a byte cap, or refuse with the given code."""
    if not path.is_file():
        raise Refusal(code, f"{path} is not a regular file")
    size = path.stat().st_size
    if size > cap:
        raise Refusal(code, f"{path} is {size} bytes, over the {cap} byte cap")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal(code, f"{path} could not be read: {exc}") from exc


def resolved_under(root: Path, candidate: str) -> Path:
    """Resolve a caller-supplied path and require it to sit under the root."""
    path = (root / candidate).resolve() if not Path(candidate).is_absolute() else Path(candidate).resolve()
    if path != root and root not in path.parents:
        raise Refusal("K007", f"{candidate} resolves outside {root}")
    return path


def check_fields(obj: dict, allowed: frozenset, required: tuple, where: str) -> None:
    if not isinstance(obj, dict):
        raise Refusal("K001", f"{where} is not an object")
    for name in required:
        if name not in obj:
            raise Refusal("K002", f"{where} has no {name!r}")
    for name in obj:
        if name not in allowed:
            raise Refusal("K003", f"{where} carries {name!r}, which the record does not hold")


def score(candidate: dict, root: Path, where: str) -> dict:
    """Validate one candidate and return the line it contributes."""
    check_fields(candidate, CANDIDATE_FIELDS, CANDIDATE_REQUIRED, where)
    axes = {}
    for name, cap in AXES:
        value = candidate[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise Refusal("K004", f"{where} {name} is {value!r}, not an integer")
        if not 0 <= value <= cap:
            raise Refusal("K004", f"{where} {name} is {value}, outside 0 to {cap}")
        axes[name] = value
    total = sum(axes.values())
    stated = candidate.get("total")
    if stated is not None and stated != total:
        raise Refusal("K005", f"{where} states a total of {stated}, but the axes sum to {total}")
    for name in ("skill", "basis"):
        if not isinstance(candidate[name], str) or not candidate[name].strip():
            raise Refusal("K002", f"{where} {name} is empty")
    if not isinstance(candidate["ledger"], str) or not candidate["ledger"].strip():
        raise Refusal("K002", f"{where} ledger is empty")
    ledger = resolved_under(root, candidate["ledger"])
    # One read, two derivations. Both come off the ledger's bytes rather than
    # off the pass document, and reading the file twice would pay the cost the
    # design record measured a sidecar file for.
    text = read_capped(ledger, MAX_LEDGER_BYTES, "K007")
    relative = str(ledger.relative_to(root))
    return {
        "skill": candidate["skill"],
        "ledger": relative,
        "held_job": held_job_from_text(text),
        "declared_inputs": declaration(text, relative),
        **axes,
        "total": total,
        "basis": candidate["basis"],
    }


def tie_break(scored: list) -> str:
    """Kronos SKILL.md step 4: total, then impact, then readiness, then order."""
    ordered = sorted(
        enumerate(scored),
        key=lambda pair: (-pair[1]["total"], -pair[1]["impact"], -pair[1]["readiness"], pair[0]),
    )
    return ordered[0][1]["skill"]


def checked_path(given: Path) -> Path:
    """Resolve a write target, refusing a symlink at the file or its directory.

    Before resolving anything: a symlink at either end would put the file and
    the `*` gitignore beside it somewhere the caller did not name, and resolve()
    erases the link on the way past.
    """
    holder = given.parent
    if given.is_symlink():
        raise Refusal("K010", f"{given} is a symlink")
    if holder.is_symlink() or (holder.exists() and not holder.is_dir()):
        raise Refusal("K010", f"{holder} is not a real directory")
    return given.resolve()


def append_line(path: Path, entry: dict) -> None:
    """Create the gitignored directory if needed, then append one JSON line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    gitignore = path.parent / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def json_lines(path: Path, marker: str) -> list:
    """Every line already recorded, refusing a tail that cannot be read."""
    if not path.exists():
        return []
    text = read_capped(path, MAX_SCOREBOARD_BYTES, "K008")
    if text and not text.endswith("\n"):
        raise Refusal("K008", f"{path} does not end in a newline, so its last line is partial")
    entries = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise Refusal("K008", f"{path} line {number} is blank")
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Refusal("K008", f"{path} line {number} is not JSON: {exc}") from exc
        if not isinstance(entry, dict) or marker not in entry:
            raise Refusal("K008", f"{path} line {number} is not a {marker} record")
        entries.append(entry)
    return entries


def standing_parks(parked_file: Path) -> dict:
    """Replay park and unpark records in order into the set that still stands."""
    standing = {}
    for entry in json_lines(parked_file, "event"):
        if entry["event"] not in PARK_EVENTS:
            raise Refusal("K008", f"{parked_file} carries event {entry['event']!r}")
        if entry["event"] == "park":
            standing[entry["skill"]] = entry
        else:
            standing.pop(entry["skill"], None)
    return standing


def checked_reason(reason) -> str:
    if not isinstance(reason, str) or not reason.strip():
        raise Refusal("K011", "the reason is empty")
    size = len(reason.encode("utf-8"))
    if size > MAX_REASON_BYTES:
        raise Refusal("K011", f"the reason is {size} bytes, over the {MAX_REASON_BYTES} cap")
    return reason


def existing_passes(scoreboard: Path) -> list:
    """Every pass already recorded, refusing a tail that cannot be read."""
    return json_lines(scoreboard, "pass")


def git_env() -> dict:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_git(argv: list[str], *, cwd: Path | None = None) -> tuple[int, bytes, bytes]:
    """Fixed argv, no shell, timeout and output cap. Stderr is not for diagnostics."""
    try:
        process = subprocess.Popen(
            ["git", *argv],
            cwd=os.fspath(cwd) if cwd is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=git_env(),
        )
    except OSError as exc:
        raise Refusal("K021", "git could not start") from exc
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    selector.register(process.stderr, selectors.EVENT_READ)
    streams = {process.stdout: bytearray(), process.stderr: bytearray()}
    deadline = time.monotonic() + GIT_TIMEOUT_SECONDS
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.wait()
                raise Refusal("K021", f"git timed out after {GIT_TIMEOUT_SECONDS} seconds")
            events = selector.select(min(remaining, 0.1))
            if not events and process.poll() is not None:
                events = [(key, selectors.EVENT_READ) for key in selector.get_map().values()]
            for key, _ in events:
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                streams[key.fileobj].extend(chunk)
                if len(streams[process.stdout]) + len(streams[process.stderr]) > GIT_OUTPUT_CAP:
                    process.kill()
                    process.wait()
                    raise Refusal("K021", f"git exceeded the {GIT_OUTPUT_CAP}-byte output cap")
        process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise Refusal("K021", f"git timed out after {GIT_TIMEOUT_SECONDS} seconds")
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
    return process.returncode, bytes(streams[process.stdout]), bytes(streams[process.stderr])


def looks_like_fetch_url(value: str) -> bool:
    if not value or value.startswith("-") or "\n" in value or "\0" in value:
        return True
    if "://" in value or value.startswith("git@"):
        return True
    if value.startswith("/") or value.startswith("."):
        return True
    if "\\" in value or ":" in value:
        return True
    return False


def listed_remotes(scope: Path) -> list[str]:
    code, out, _err = run_git(["remote"], cwd=scope)
    if code != 0:
        raise Refusal("K020", "the scope has no usable git remotes")
    return [line.strip() for line in out.decode("utf-8", "replace").splitlines() if line.strip()]


def resolved_remote(scope: Path, requested: str | None) -> str:
    if requested is not None and looks_like_fetch_url(requested):
        raise Refusal("K020", "the remote must be a configured remote name, not a URL")
    env = os.environ.get(REMOTE_ENV)
    name = requested
    if name is None and env:
        if looks_like_fetch_url(env):
            raise Refusal("K020", f"{REMOTE_ENV} must be a configured remote name, not a URL")
        name = env
    remotes = listed_remotes(scope)
    if name is not None:
        if name not in remotes:
            raise Refusal("K020", f"{name} is not a configured remote")
        return name
    if "upstream" in remotes:
        return "upstream"
    if "origin" in remotes:
        return "origin"
    raise Refusal("K020", "no configured remote named upstream or origin")


def remote_url(scope: Path, name: str) -> str:
    code, out, _err = run_git(["remote", "get-url", name], cwd=scope)
    if code != 0:
        raise Refusal("K020", f"{name} is not a configured remote")
    url = out.decode("utf-8", "replace").strip()
    if not url or "\n" in url:
        raise Refusal("K020", f"{name} is not a configured remote")
    return url


def ls_state_ref(scope: Path, remote: str) -> str | None:
    """SHA of the state ref on the remote, or None if the ref is missing."""
    code, out, _err = run_git(["ls-remote", "--heads", "--", remote, STATE_REF], cwd=scope)
    if code != 0:
        raise Refusal("K018", "the state ref exists but could not be read")
    text = out.decode("utf-8", "replace").strip()
    if not text:
        return None
    sha = text.split()[0]
    if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
        raise Refusal("K018", "the state ref exists but could not be read")
    return sha


def working_copy(root: Path) -> dict[str, Path]:
    holder = Path(root) / ".kronos"
    files = {name: holder / name for name in STATE_BLOBS}
    for path in files.values():
        checked_path(path)
    return files


def install_blob(dest: Path, data: str | None) -> None:
    """Write data to dest via a sibling temporary, or remove dest if data is None."""
    checked_path(dest)
    if data is None:
        if dest.is_file() and not dest.is_symlink():
            dest.unlink()
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    gitignore = dest.parent / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n", encoding="utf-8")
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, dest)


def blob_at(git_dir: Path, name: str) -> str | None:
    # No `--` before the treeish:path: git show would then treat it as a path
    # on HEAD, which in a fresh bare repo is an unborn branch.
    code, out, _err = run_git(["--git-dir", str(git_dir), "show", f"{STATE_REF}:{name}"])
    if code != 0:
        return None
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("K018", f"{name} in the state ref could not be read") from exc


def tip_file(root: Path) -> Path:
    return Path(root) / ".kronos" / TIP_NAME


def read_tip(root: Path) -> str | None:
    path = tip_file(root)
    checked_path(path)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", text):
        raise Refusal("K008", f"{path} is not a state-ref tip")
    return text


def write_tip(root: Path, sha: str | None) -> None:
    install_blob(tip_file(root), None if sha is None else sha + "\n")


def git_identity(scope: Path) -> tuple[str, str]:
    def one(key: str) -> str:
        code, out, _err = run_git(["config", "--get", key], cwd=scope)
        return out.decode("utf-8", "replace").strip() if code == 0 else ""

    name, email = one("user.name"), one("user.email")
    if not name or not email or "\n" in name or "\n" in email:
        raise Refusal("K021", "git could not complete the state push")
    return name, email


def require_scope(root_arg: str) -> Path:
    root = Path(root_arg).resolve()
    if not root.is_dir():
        raise Refusal("K000", f"{root} is not a directory")
    return root


def cmd_pull(args: argparse.Namespace) -> int:
    root = require_scope(args.root)
    files = working_copy(root)
    remote = resolved_remote(root, args.remote)
    sha = ls_state_ref(root, remote)
    if sha is None:
        for path in files.values():
            install_blob(path, None)
        write_tip(root, None)
        print(f"pull empty start  {STATE_REF} is absent")
        return 0
    url = remote_url(root, remote)
    git_dir = Path(tempfile.mkdtemp(prefix="kronos-state-"))
    try:
        code, _out, _err = run_git(["init", "--bare", "--", str(git_dir)])
        if code != 0:
            raise Refusal("K021", "git could not complete the state pull")
        code, _out, _err = run_git(
            ["--git-dir", str(git_dir), "fetch", "--", url, f"{STATE_REF}:{STATE_REF}"]
        )
        if code != 0:
            raise Refusal("K018", "the state ref exists but could not be read")
        existed = any(path.exists() for path in files.values())
        for name, path in files.items():
            install_blob(path, blob_at(git_dir, name))
        write_tip(root, sha)
        kind = "replaced" if existed else "empty"
        print(f"pull {sha}  {kind} working copy")
        return 0
    finally:
        shutil.rmtree(git_dir, ignore_errors=True)


def cmd_push(args: argparse.Namespace) -> int:
    root = require_scope(args.root)
    files = working_copy(root)
    for name, path in files.items():
        if path.exists():
            json_lines(path, "pass" if name == SCOREBOARD_NAME else "event")
    remote = resolved_remote(root, args.remote)
    url = remote_url(root, remote)
    author, email = git_identity(root)
    expected = read_tip(root)
    remote_sha = ls_state_ref(root, remote)
    if remote_sha is not None and remote_sha != expected:
        raise Refusal(
            "K019",
            "the state ref is not a fast-forward from this working copy",
        )
    work = Path(tempfile.mkdtemp(prefix="kronos-state-"))
    try:
        code, _out, _err = run_git(["init", "--", str(work)])
        if code != 0:
            raise Refusal("K021", "git could not complete the state push")
        sha = remote_sha
        if sha is not None:
            code, _out, _err = run_git(
                ["fetch", "--", url, f"{STATE_REF}:{STATE_REF}"], cwd=work
            )
            if code != 0:
                raise Refusal("K018", "the state ref exists but could not be read")
            code, _out, _err = run_git(["checkout", "-B", "state", STATE_REF], cwd=work)
            if code != 0:
                raise Refusal("K018", "the state ref exists but could not be read")
        else:
            code, _out, _err = run_git(["checkout", "--orphan", "state"], cwd=work)
            if code != 0:
                raise Refusal("K021", "git could not complete the state push")
        for blob in STATE_BLOBS:
            dest = work / blob
            src = files[blob]
            if src.exists():
                dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            elif dest.exists() or dest.is_symlink():
                dest.unlink()
        for child in work.iterdir():
            if child.name in {".git", *STATE_BLOBS}:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        code, _out, _err = run_git(["add", "-A"], cwd=work)
        if code != 0:
            raise Refusal("K021", "git could not complete the state push")
        code, _out, _err = run_git(
            [
                "-c", f"user.name={author}",
                "-c", f"user.email={email}",
                "-c", "commit.gpgsign=false",
                "commit", "--allow-empty", "-m", "kronos state",
            ],
            cwd=work,
        )
        if code != 0:
            raise Refusal("K021", "git could not complete the state push")
        code, _out, err = run_git(["push", "--", url, f"HEAD:{STATE_REF}"], cwd=work)
        if code != 0:
            err_text = err.decode("utf-8", "replace").casefold()
            if "non-fast-forward" in err_text:
                raise Refusal(
                    "K019",
                    "the state ref is not a fast-forward from this working copy",
                )
            raise Refusal("K021", "git could not complete the state push")
        code, out, _err = run_git(["rev-parse", "HEAD"], cwd=work)
        if code != 0:
            raise Refusal("K021", "git could not complete the state push")
        new_sha = out.decode("utf-8", "replace").strip()
        write_tip(root, new_sha)
        print(f"push {new_sha}")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


def record(args: argparse.Namespace) -> int:
    scoreboard = checked_path(Path(args.scoreboard))
    root = Path(args.root).resolve() if args.root else scoreboard.parent.parent
    raw = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if len(raw) > MAX_STDIN_BYTES:
        raise Refusal("K001", f"stdin is over the {MAX_STDIN_BYTES} byte cap")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Refusal("K001", f"stdin is not JSON: {exc}") from exc

    check_fields(document, PASS_FIELDS, PASS_REQUIRED, "the pass")
    if document["mode"] not in MODES:
        raise Refusal("K002", f"mode is {document['mode']!r}, not one of {', '.join(MODES)}")
    candidates = document["candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise Refusal("K002", "the pass has no candidates")
    if len(candidates) > MAX_CANDIDATES:
        raise Refusal("K009", f"{len(candidates)} candidates, over the {MAX_CANDIDATES} cap")

    scored = [score(c, root, f"candidate {n}") for n, c in enumerate(candidates, start=1)]
    names = [c["skill"] for c in scored]
    if len(set(names)) != len(names):
        raise Refusal("K002", "two candidates name the same skill")

    # A parked candidate keeps its score and its place in the record. It is only
    # barred from being selected, because the loop already knows why it stalled.
    standing = standing_parks(scoreboard.parent / PARKED_NAME)
    for candidate, given in zip(scored, candidates):
        claimed = given.get("parked", False)
        if not isinstance(claimed, bool):
            raise Refusal("K004", f"{candidate['skill']} parked is {claimed!r}, not a boolean")
        if claimed != (candidate["skill"] in standing):
            raise Refusal(
                "K014",
                f"{candidate['skill']} is marked parked={claimed}, "
                f"but the standing parks say {candidate['skill'] in standing}",
            )
        candidate["parked"] = claimed

    unparked = [c for c in scored if not c["parked"]]
    if not unparked:
        raise Refusal("K015", "every candidate is parked, so the pass selects nobody")
    if document["selected"] not in names:
        raise Refusal("K006", f"selected {document['selected']!r} is not among the candidates")
    expected = tie_break(unparked)
    if document["selected"] != expected:
        raise Refusal("K006", f"selected {document['selected']!r}, but the tie-break picks {expected!r}")

    run = document.get("run")
    if run is not None and not isinstance(run, str):
        raise Refusal("K002", f"run is {run!r}, which is neither a string nor absent")

    rank_only = document.get("rank_only", False)
    if not isinstance(rank_only, bool):
        raise Refusal("K004", f"rank_only is {rank_only!r}, not a boolean")
    # A rank-only pass stops after selection, so there is no run for it to name.
    # Recording both would leave the file saying the ranking was and was not acted on.
    if rank_only and run is not None:
        raise Refusal("K016", f"a rank-only pass names run {run!r}, but it launched none")

    ungoverned = document.get("ungoverned", [])
    if not isinstance(ungoverned, list):
        raise Refusal("K017", f"ungoverned is {ungoverned!r}, not a list")
    if len(ungoverned) > MAX_UNGOVERNED:
        raise Refusal("K017", f"{len(ungoverned)} ungoverned names, over the {MAX_UNGOVERNED} cap")
    for name in ungoverned:
        if not isinstance(name, str) or not name.strip():
            raise Refusal("K017", f"ungoverned holds {name!r}, which is not a name")
        # Ungoverned means no ledger, and a scored candidate was scored from one.
        # A name in both leaves the record asserting each about the same skill.
        if name in names:
            raise Refusal("K017", f"{name} is reported ungoverned and scored in the same pass")

    previous = existing_passes(scoreboard)
    entry = {
        "pass": len(previous) + 1,
        "scope": document["scope"],
        "mode": document["mode"],
        "selected": document["selected"],
        "run": run,
        "rank_only": rank_only,
        "ungoverned": list(ungoverned),
        "candidates": scored,
    }
    append_line(scoreboard, entry)
    parked_note = f", {len(scored) - len(unparked)} parked" if len(unparked) != len(scored) else ""
    kind = "rank-only pass" if rank_only else "pass"
    print(
        f"{kind} {entry['pass']} recorded: {len(scored)} candidate(s){parked_note}, "
        f"selected {entry['selected']}"
    )
    return 0


def park(args: argparse.Namespace) -> int:
    parked_file = checked_path(Path(args.scoreboard_dir) / PARKED_NAME)
    root = Path(args.root).resolve() if args.root else parked_file.parent.parent
    reason = checked_reason(args.reason)
    ledger = resolved_under(root, args.ledger)
    held = held_job_hash(ledger)
    standing = standing_parks(parked_file)
    if args.skill in standing:
        raise Refusal("K012", f"{args.skill} is already parked; unpark it before parking it again")
    entry = {
        "event": "park",
        "skill": args.skill,
        "ledger": str(ledger.relative_to(root)),
        "held_job": held,
        "reason": reason,
    }
    append_line(parked_file, entry)
    print(f"parked {args.skill} on its held job {held[:12]}")
    return 0


def unpark(args: argparse.Namespace) -> int:
    parked_file = checked_path(Path(args.scoreboard_dir) / PARKED_NAME)
    reason = checked_reason(args.reason)
    standing = standing_parks(parked_file)
    if args.skill not in standing:
        raise Refusal("K013", f"{args.skill} is not parked, so there is nothing to release")
    append_line(parked_file, {"event": "unpark", "skill": args.skill, "reason": reason})
    print(f"released {args.skill}")
    return 0


def park_state(entry: dict, root: Path) -> str:
    """Whether the held job a park named is still the one on disk."""
    try:
        ledger = resolved_under(root, entry["ledger"])
        return "standing" if held_job_hash(ledger) == entry["held_job"] else "stale"
    except Refusal:
        # An unreadable ledger is not evidence that the blocker cleared.
        return "unknown"


def parked(args: argparse.Namespace) -> int:
    parked_file = Path(args.scoreboard_dir) / PARKED_NAME
    root = Path(args.root).resolve() if args.root else parked_file.resolve().parent.parent
    standing = standing_parks(parked_file)
    if not standing:
        print("no parks standing")
        return 0
    for skill in sorted(standing):
        entry = standing[skill]
        state = park_state(entry, root)
        note = {
            "standing": "held job unchanged",
            "stale": "held job has moved on since; a person decides whether the park still applies",
            "unknown": "ledger could not be read, so the park stands",
        }[state]
        print(f"{skill}  {entry['held_job'][:12]}  {note}")
        # Indented line by line. The reason is stored verbatim by requirement,
        # and a newline inside one would otherwise let it forge the summary line
        # that tells a reader whether anything still stands.
        for number, line in enumerate(entry["reason"].splitlines() or [""]):
            print(f"  {'reason: ' if number == 0 else '        '}{line}")
    print(f"{len(standing)} park(s) standing; the loop is not complete")
    return STANDS


def recorded_declaration(candidate: dict) -> str | None:
    """The declaration digest a recorded candidate carries, if it carries one.

    A line written before this field existed carries no key at all, and a
    ledger that declares nothing records null. Neither declared, so neither
    may read as a declaration that moved.
    """
    declared = candidate.get("declared_inputs")
    return declared.get("digest") if isinstance(declared, dict) else None


def one_line(value) -> str:
    """One line of recorded text, so nothing printed can open a second line.

    `show` writes a scoreboard's own words at fixed indents, and a reader
    tells a basis from a declared row by the line each sits on. A line break
    inside any recorded string would put text somebody supplied at the start
    of its own line, where it can spell a `declared:` heading no ledger wrote.
    `park` prints its reason a line at a time for the same reason; this holds
    the rest of the verb to that rule. Breaks collapse to a space rather than
    truncating, so every word the record carries still reaches the reader.
    `splitlines` is the splitter the block reader already uses, so the two
    agree on what a line break is, U+2028 and U+0085 included.
    """
    return " ".join(str(value).splitlines())


def declared_lines(candidate: dict) -> list:
    """What a recorded candidate declared, as lines for `show` to print.

    The rows are printed in the form the ledger wrote them, because a reader
    comparing the record against the ledger should not have to translate
    between two spellings of the same four fields. `none` covers both a line
    written before the field existed and a ledger that declared nothing, which
    is the same conflation the drift mark above already makes.

    The fields go through `one_line` even though `declared_rows` already
    refuses a break in one: a scoreboard read back from disk was not validated
    by this process, and the caller who could edit it is the one this guards.
    """
    declared = candidate.get("declared_inputs")
    if not isinstance(declared, dict):
        return ["declared: none"]
    rows = declared["rows"]
    lines = [f"declared: {len(rows)} input(s)"]
    lines.extend(
        "  " + " | ".join(
            one_line(row[name])
            for name in ("id", "kind", "availability", "note")
        )
        for row in rows
    )
    return lines


def drift(passes: list) -> dict:
    """Axis scores that moved for a skill whose held job did not, by pass."""
    seen = {}
    moved = {}
    for entry in passes:
        for candidate in entry["candidates"]:
            key = (candidate["skill"], candidate["held_job"])
            before = seen.get(key)
            if before is not None:
                changed = [name for name, _ in AXES if candidate[name] != before[name]]
                if changed:
                    moved[(entry["pass"], candidate["skill"])] = [
                        (name, before[name], candidate[name]) for name in changed
                    ]
            seen[key] = candidate
    return moved


def declaration_drift(passes: list) -> dict:
    """Declarations that moved for a skill whose held job did not, by pass.

    Keyed as the axis drift above is, and read the same way: the held job is
    half the key, so a candidate whose ledger moved on is a fresh subject
    rather than a change to the one before it.
    """
    seen = {}
    moved = {}
    for entry in passes:
        for candidate in entry["candidates"]:
            key = (candidate["skill"], candidate["held_job"])
            digest = recorded_declaration(candidate)
            before = seen.get(key, ...)
            if before is not ... and before != digest:
                moved[(entry["pass"], candidate["skill"])] = (before, digest)
            seen[key] = digest
    return moved


def show(args: argparse.Namespace) -> int:
    scoreboard = Path(args.scoreboard).resolve()
    if not scoreboard.exists():
        print(f"no scoreboard at {scoreboard}")
        return 0
    passes = existing_passes(scoreboard)
    moved = drift(passes)
    declared_moved = declaration_drift(passes)
    for entry in passes:
        note = "rank-only" if entry.get("rank_only") else (entry.get("run") or "no run recorded")
        print(
            f"pass {entry['pass']}  {one_line(entry['mode'])}  "
            f"{one_line(entry['scope'])}  ({one_line(note)})"
        )
        for candidate in sorted(entry["candidates"], key=lambda c: -c["total"]):
            # A parked candidate outscoring the selected one is the normal case
            # once anything is parked. Without the mark the output reads as
            # though it contradicts its own tie-break.
            if candidate["skill"] == entry["selected"]:
                mark = "*"
            elif candidate.get("parked"):
                mark = "P"
            else:
                mark = " "
            axes = " ".join(f"{name}={candidate[name]}" for name, _ in AXES)
            print(f"  {mark} {candidate['total']:3d}  {one_line(candidate['skill']):<24} {axes}")
            print(f"      {one_line(candidate['basis'])}")
            for line in declared_lines(candidate):
                print(f"      {line}")
            for name, before, after in moved.get((entry["pass"], candidate["skill"]), []):
                print(f"      drift: {name} {before} -> {after}, held job unchanged")
            change = declared_moved.get((entry["pass"], candidate["skill"]))
            if change is not None:
                was, now = (digest[:12] if digest else "none" for digest in change)
                print(f"      drift: declaration {was} -> {now}, held job unchanged")
        for name in entry.get("ungoverned", []):
            print(f"    ungoverned: {one_line(name)}")
    print(f"{len(passes)} pass(es), {len(set(moved) | set(declared_moved))} with drift")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    writer = sub.add_parser("record", help="append one validated pass read from stdin")
    writer.add_argument("--scoreboard", required=True, help="path to the scoreboard file")
    writer.add_argument("--root", help="checkout root each ledger must sit under")
    writer.set_defaults(handler=record)

    reader = sub.add_parser("show", help="print the recorded passes and any drift")
    reader.add_argument("--scoreboard", required=True, help="path to the scoreboard file")
    reader.set_defaults(handler=show)

    parker = sub.add_parser("park", help="record a blocked held job and why")
    parker.add_argument("--scoreboard-dir", required=True, help="the .kronos directory")
    parker.add_argument("--skill", required=True, help="the blocked skill")
    parker.add_argument("--ledger", required=True, help="that skill's EVOLUTION.md")
    parker.add_argument("--reason", required=True, help="the halt reason, stored as given")
    parker.add_argument("--root", help="checkout root the ledger must sit under")
    parker.set_defaults(handler=park)

    releaser = sub.add_parser("unpark", help="release a standing park")
    releaser.add_argument("--scoreboard-dir", required=True, help="the .kronos directory")
    releaser.add_argument("--skill", required=True, help="the parked skill")
    releaser.add_argument("--reason", required=True, help="why it is released, stored as given")
    releaser.set_defaults(handler=unpark)

    lister = sub.add_parser("parked", help="print standing parks; exits 3 while any stands")
    lister.add_argument("--scoreboard-dir", required=True, help="the .kronos directory")
    lister.add_argument("--root", help="checkout root the ledgers sit under")
    lister.set_defaults(handler=parked)

    puller = sub.add_parser("pull", help="replace the working copy from the state ref")
    puller.add_argument("--root", required=True, help="scope root holding .kronos")
    puller.add_argument("--remote", help="configured git remote name")
    puller.set_defaults(handler=cmd_pull)

    pusher = sub.add_parser("push", help="fast-forward the state ref from the working copy")
    pusher.add_argument("--root", required=True, help="scope root holding .kronos")
    pusher.add_argument("--remote", help="configured git remote name")
    pusher.set_defaults(handler=cmd_push)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except Refusal as refusal:
        print(refusal, file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"K000: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
