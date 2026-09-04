#!/usr/bin/env python3
"""Observe this host's Atlas hand-off clients and write one roster manifest.

The roster's single source is a `harness-classification/v1` manifest, validated
by `schemas/harness-classification-v1.json` and pinned by
`docs/decisions/ADR-076-generate-the-harness-roster-from-one-probed-manifest.md`.
This module is the generator. It observes each client, classifies it, and
writes the manifest three later wording surfaces are rendered from.

Four properties are load-bearing, and each has a case in
`tests/test_harness_manifest.py` that fails without it.

**A class cannot outrun its observation.** `Atlas launcher` and `tested local
route` are earned classes. `classify` returns one only when the harness carries
a probe whose status is `answered` and whose client was found present. Every
other input shape reaches `manual route` or `unsupported`, whatever the rest of
the record claims. `answered` is itself earned: `probe_client` reads the exit
status before the output and records a non-zero exit as `unread`, because
`VERSION_TOKEN` matches dotted numbers that are not versions -- a loopback
address in a connection error, a date in an expiry message -- and a token
scraped out of a failure is not an answer.

**The command is fixed, and never read from a manifest.** Each harness declares
its own argv in `ROSTER`, as a tuple of plain strings. Nothing in this module
reads a command, an argument or a binary name out of a manifest, a manifest's
destination, or any other file. `_run` passes that tuple to `subprocess.run`
as a list, with no shell, a bounded timeout, `stdin` closed and an environment
holding nothing but `PATH`, so a client cannot echo an inherited credential
back at us.

**Nothing a client prints reaches the record verbatim.** `recognise_version`
allowlists one version-shaped token out of the client's output and discards the
rest, and `credential_findings` sweeps the serialised manifest and every log
event for a token, key, cookie or session shape before either is written. A hit
raises `CredentialLeak` and nothing is written at all.

**The manifest write is atomic.** `_atomic_write_text` writes a temporary file
in the destination's own directory and renames it over the target, so a probe
killed mid-write leaves the previous manifest exactly as it was, or nothing
where there was none. The temporary name is a dotfile with a `.tmp` suffix, so
no renderer globbing for JSON picks a half-written one up.

Two questions decide what gets recorded at all. Why did this harness get this
class, and did the probe read the client or only fail to find it? The manifest's
`probe` block and `blocker` answer the first for a reader months from now, and
`probe.result` beside `client_present` answers the second. Both are also emitted
per harness as one `harness_probe_done` event carrying a `run_id` minted for the
run, so two probes of the same host can be told apart. Nothing else is emitted:
no raw client output, no credential, no absolute path and no account identifier
reaches either surface.

One encoding is worth stating. A client that resolves on `PATH` but does not
answer -- it timed out, it exited non-zero, it printed no version -- is present,
and its version is unread. Recording it absent would collapse two different
facts, which is exactly what `client_present` and `auth_configured` exist to
prevent, so `client_present` stays true and `client_version` carries
`UNREAD_VERSION`. That sentinel cannot collide with a real version, because
`recognise_version` only ever returns a digit-led `VERSION_TOKEN` match, but a
sentinel is still prose where a reader wants a field: `version_read` carries
the same fact as a boolean the schema declares, so nothing downstream has to
string-match `"unread"` to know whether a version was read. The full reason is
in `probe.result` and in `blocker`.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass


SCHEMA_ID = "harness-classification/v1"

ATLAS_LAUNCHER = "Atlas launcher"
TESTED_LOCAL_ROUTE = "tested local route"
MANUAL_ROUTE = "manual route"
UNSUPPORTED = "unsupported"

CLASSIFICATIONS = (ATLAS_LAUNCHER, TESTED_LOCAL_ROUTE, MANUAL_ROUTE, UNSUPPORTED)

# The two classes a harness only reaches by a recorded client run. ADR-076
# makes the classifier, not the schema, the thing that enforces that.
EARNED_CLASSIFICATIONS = (ATLAS_LAUNCHER, TESTED_LOCAL_ROUTE)

STATUS_ANSWERED = "answered"
STATUS_ABSENT = "absent"
STATUS_UNREAD = "unread"

DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_TIMEOUT_SECONDS = 120.0

MAX_CLIENT_OUTPUT_CHARS = 4_096
MAX_CLIENT_OUTPUT_LINES = 16
MAX_MANIFEST_BYTES = 1_048_576

UNREAD_VERSION = "unread"

TEMPORARY_PREFIX = ".harness-classification-"
TEMPORARY_SUFFIX = ".tmp"

BASE_REF_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
HOST_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
RUN_ID_PATTERN = re.compile(r"^[0-9a-f]{8,64}$")

# One version-shaped token: digits joined by dots, with an optional build
# suffix. Everything else the client printed is discarded, which is what keeps
# a credential in its output out of the record.
VERSION_TOKEN = re.compile(r"[0-9]+(?:\.[0-9]+){1,3}(?:[-+][0-9A-Za-z.]{1,32})?")

BASE_REF_ARGV = ("git", "rev-parse", "HEAD")

NO_CLIENT_DECLARED = (
    "no client binary is declared for this harness, so no client run was attempted"
)

RESULT_ABSENT = "absent: {binary} did not resolve on PATH, so the command was not run"
RESULT_ANSWERED = "answered: the client reported version {version}"
RESULT_NO_VERSION = (
    "unread: {binary} answered with no version-shaped token, "
    "so its version is unread rather than absent"
)
RESULT_EXIT = (
    "unread: {binary} exited {code}, so its version is unread rather than absent"
)
RESULT_TIMEOUT = (
    "unread: {binary} did not answer within {seconds}s, "
    "so its version is unread rather than absent"
)
RESULT_UNRUNNABLE = (
    "unread: {binary} resolved on PATH but could not be executed ({reason}), "
    "so its version is unread rather than absent"
)

NO_AUTH_SIGNAL = "no declared authentication signal was observed on this host"
AUTH_SIGNAL = "a declared authentication signal was observed on this host"

# Shapes that must never reach the manifest or the probe log. The sweep is
# defence in depth beneath `recognise_version`, which allowlists rather than
# filters; if it ever fires, the write fails closed instead of redacting.
CREDENTIAL_PATTERNS = (
    ("token", re.compile(r"(?i)\b(?:bearer|token)\b\s*[:=]\s*[A-Za-z0-9._~+/-]{12,}")),
    ("token", re.compile(r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{16,}")),
    ("token", re.compile(r"\bey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("key", re.compile(r"(?i)\b(?:api|secret|private|access)[_-]?key\b\s*[:=]\s*\S{8,}")),
    ("key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("cookie", re.compile(r"(?i)\b(?:set-)?cookie\b\s*[:=]\s*\S{8,}")),
    ("session", re.compile(r"(?i)\bsession[_-]?(?:id|token|key|secret)\b\s*[:=]\s*\S{8,}")),
)

CREDENTIAL_SHAPES = ("cookie", "key", "session", "token")


class ProbeError(Exception):
    """The probe could not complete an observation or a write."""


class CredentialLeak(ProbeError):
    """A credential shape reached a record, so nothing is written."""


@dataclass(frozen=True)
class Harness:
    """One roster row's fixed declaration.

    `probe_argv` is the whole command, binary first, and it is the only place a
    command for this harness comes from. An empty tuple declares that no client
    binary exists to run, which is a different fact from a client that is
    absent from this host.
    """

    name: str
    probe_argv: tuple[str, ...]
    auth_env: tuple[str, ...]
    auth_files: tuple[str, ...]
    launcher_contract: str
    launcher_published: bool
    product_withdrawn: bool
    standing_blocker: str


@dataclass(frozen=True)
class ProbeRecord:
    """What the probe ran for one harness and what came back."""

    command: tuple[str, ...]
    result: str
    status: str
    version: str | None

    def document(self) -> dict[str, object]:
        return {"command": list(self.command), "result": self.result}


@dataclass(frozen=True)
class Observation:
    """One harness as this host showed it, before a class is derived."""

    name: str
    client_present: bool
    client_version: str | None
    auth_configured: bool
    launcher_contract: str
    launcher_published: bool
    product_withdrawn: bool
    standing_blocker: str
    probe: ProbeRecord | None


# The six harnesses issue #856 asks about. Every argv, authentication signal
# and published contract here is a fixed declaration read from
# `.hexaemeron/design/harness-evidence.json`, never from a manifest.
ROSTER: tuple[Harness, ...] = (
    Harness(
        name="GitHub Copilot",
        probe_argv=("copilot", "--version"),
        # Copilot entitlement is a seat on an account, which is a network fact
        # this probe deliberately does not read. Nothing local stands in for it.
        auth_env=(),
        auth_files=(),
        launcher_contract=(
            "ghapp://session/new with repo, pr, branch, prompt and mode, "
            "where mode takes plan, interactive or autopilot"
        ),
        launcher_published=True,
        product_withdrawn=False,
        standing_blocker=(
            "No Copilot seat is held on the active account and the organisation's "
            "Copilot CLI policy is unconfigured. Seat entitlement is a network fact "
            "this probe does not read, and clearing the blocker needs either an "
            "organisation policy change or a new personal plan"
        ),
    ),
    Harness(
        name="Cursor",
        probe_argv=("cursor-agent", "--version"),
        auth_env=("CURSOR_API_KEY",),  # phylax: allow a variable name is a credential location, never its value
        auth_files=(),
        launcher_contract=(
            "none published; the agent CLI takes -p for a prompt and "
            "--mode=ask or --plan for read-only work"
        ),
        launcher_published=False,
        product_withdrawn=False,
        standing_blocker=(
            "The client is absent and its authentication is an interactive account "
            "sign-in this environment has no Cursor account for"
        ),
    ),
    Harness(
        name="Gemini CLI",
        probe_argv=("gemini", "--version"),
        auth_env=(  # phylax: allow these names are credential locations, never their values
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ),
        auth_files=(".config/gcloud/application_default_credentials.json",),
        launcher_contract=(
            "none published; the prompt is supplied with --prompt or -p and the "
            "read-only mode is --approval-mode plan"
        ),
        launcher_published=False,
        product_withdrawn=False,
        standing_blocker=(
            "The client is absent and no authentication method is configured on "
            "this host"
        ),
    ),
    Harness(
        name="Windsurf",
        probe_argv=("windsurf", "--version"),
        auth_env=(),
        auth_files=(),
        launcher_contract=(
            "none published; Cascade documents Code mode and Chat mode, and "
            "Restricted Mode makes Cascade unavailable entirely"
        ),
        launcher_published=False,
        # The product is renamed rather than withdrawn. Which product a Windsurf
        # row should describe is a naming question a maintainer has to settle,
        # and classifying it `unsupported` from here would settle it silently.
        product_withdrawn=False,
        standing_blocker=(
            "The client is absent, and the product the issue names is now published "
            "as Cascade inside Devin Desktop. Which product a Windsurf row should "
            "describe is a naming question a maintainer has to settle before any run"
        ),
    ),
    Harness(
        name="Cline",
        probe_argv=("cline", "--version"),
        auth_env=(),
        auth_files=(),
        launcher_contract=(
            "none published; -p or --plan gives plan-first work, --auto-approve "
            "takes a boolean, and the positional-prompt form still defaults to act "
            "mode with auto-approval on"
        ),
        launcher_published=False,
        product_withdrawn=False,
        standing_blocker=(
            "The client is absent and unauthenticated. Its positional-prompt form "
            "still defaults to act mode with auto-approval on, so the recorded "
            "hazard is unchanged"
        ),
    ),
    Harness(
        name="Roo Code",
        probe_argv=(),
        auth_env=(),
        auth_files=(),
        launcher_contract="none; the product is sunset and RooCodeInc/Roo-Code is archived",
        launcher_published=False,
        product_withdrawn=True,
        standing_blocker=(
            "The product is sunset and its repository archived. No active successor "
            "was named, so there is nothing to test"
        ),
    ),
)


def credential_findings(text: str) -> list[str]:
    """Every credential shape this text carries, as sorted shape names."""
    return sorted({shape for shape, pattern in CREDENTIAL_PATTERNS if pattern.search(text)})


def _refuse_leak(where: str, text: str) -> None:
    found = credential_findings(text)
    if found:
        raise CredentialLeak(f"{where} carries a {', '.join(found)} shape")


class Recorder:
    """Structured probe events, every one carrying the same run identifier.

    The sweep runs as each event is recorded rather than at write time, so a
    leaking line never reaches the buffer, let alone a file.
    """

    def __init__(self, run_id: str) -> None:
        if not RUN_ID_PATTERN.match(run_id):
            raise ProbeError("run id must be 8 to 64 lowercase hexadecimal characters")
        self.run_id = run_id
        self.events: list[dict[str, object]] = []

    def record(self, event: str, **fields: object) -> dict[str, object]:
        entry: dict[str, object] = {"event": event, "run_id": self.run_id}
        entry.update(fields)
        _refuse_leak(f"probe log event {event}", json.dumps(entry, sort_keys=True))
        self.events.append(entry)
        return entry

    def lines(self) -> str:
        return "".join(json.dumps(event, sort_keys=True) + "\n" for event in self.events)


def _run(argv: tuple[str, ...], timeout: float) -> subprocess.CompletedProcess[str]:
    """Run one fixed argv as a list, with no shell and a bounded timeout.

    The child gets `PATH` and nothing else, so a client that echoes its
    environment cannot print an inherited credential, and `stdin` is closed so
    a client that would prompt fails the timeout instead of hanging for ever.
    """
    return subprocess.run(
        list(argv),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
        env={"PATH": os.environ.get("PATH", "")},
    )


def recognise_version(*streams: str | None) -> str | None:
    """The first whole version-shaped token in bounded client output, or None.

    This is an allowlist rather than a filter: the token comes back and the
    surrounding output is dropped, so nothing a client printed can reach the
    manifest by having been near a version.

    The character bound can land inside a token, and half of a version is not
    the version the client reported. A match that runs to the truncation point
    is discarded rather than recorded, so a client that buries its version past
    the bound lands in `unread` -- where a client that printed no version at all
    already lands -- instead of having a fragment recorded as its exact version.
    """
    for stream in streams:
        if not stream:
            continue
        bounded = stream[:MAX_CLIENT_OUTPUT_CHARS]
        # The tail is a fragment only where the cut landed mid-line. A cut that
        # landed on a newline left every line it kept intact.
        partial_tail = len(stream) > len(bounded) and not bounded.endswith(("\n", "\r"))
        kept = bounded.splitlines()
        tail = len(kept) - 1
        for index, line in enumerate(kept[:MAX_CLIENT_OUTPUT_LINES]):
            match = VERSION_TOKEN.search(line)
            if match is None:
                continue
            if partial_tail and index == tail and match.end() == len(line):
                continue
            return match.group(0)
    return None


def probe_client(
    harness: Harness,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    runner=None,
    path_lookup=None,
) -> ProbeRecord | None:
    """Run this harness's declared command, or record why it was not run."""
    if not harness.probe_argv:
        return None
    runner = _run if runner is None else runner
    path_lookup = shutil.which if path_lookup is None else path_lookup
    argv = harness.probe_argv
    binary = argv[0]

    if path_lookup(binary) is None:
        return ProbeRecord(argv, RESULT_ABSENT.format(binary=binary), STATUS_ABSENT, None)

    try:
        completed = runner(argv, timeout)
    except subprocess.TimeoutExpired:
        reason = RESULT_TIMEOUT.format(binary=binary, seconds=_seconds(timeout))
        return ProbeRecord(argv, reason, STATUS_UNREAD, None)
    except OSError as error:
        reason = RESULT_UNRUNNABLE.format(binary=binary, reason=type(error).__name__)
        return ProbeRecord(argv, reason, STATUS_UNREAD, None)

    # The exit status is read before the output, and it is decisive. A client
    # that exited non-zero did not answer, whatever its output happens to
    # contain, and `VERSION_TOKEN` matches plenty of things that are not
    # versions: a loopback address in a connection error, a date in an expiry
    # message, a version fragment inside a documentation URL. Scraping one of
    # those out of a failure and calling it an answer is how a client that
    # never worked earns `tested local route`.
    if completed.returncode != 0:
        reason = RESULT_EXIT.format(binary=binary, code=completed.returncode)
        return ProbeRecord(argv, reason, STATUS_UNREAD, None)
    version = recognise_version(completed.stdout, completed.stderr)
    if version is None:
        return ProbeRecord(argv, RESULT_NO_VERSION.format(binary=binary), STATUS_UNREAD, None)
    return ProbeRecord(argv, RESULT_ANSWERED.format(version=version), STATUS_ANSWERED, version)


def _seconds(timeout: float) -> str:
    return f"{timeout:g}"


def auth_signal(harness: Harness, *, environ=None, home=None) -> bool:
    """Whether a declared authentication signal exists here.

    Only presence is read. An environment variable's value is tested for being
    non-blank and never recorded, and a credential file's size is read while its
    bytes are not. A left-behind configuration directory is residue and counts
    for nothing, which is the error the separate observation fields exist to
    prevent.
    """
    environ = os.environ if environ is None else environ
    for name in harness.auth_env:
        if (environ.get(name) or "").strip():
            return True
    if not harness.auth_files:
        return False
    root = Path.home() if home is None else Path(home)
    for relative in harness.auth_files:
        try:
            status = (root / relative).stat()
        except OSError:
            continue
        if stat.S_ISREG(status.st_mode) and status.st_size > 0:
            return True
    return False


def observe(
    harness: Harness,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    runner=None,
    path_lookup=None,
    environ=None,
    home=None,
) -> Observation:
    """Read one harness off this host.

    Presence and authentication are read independently, so an absent client and
    a present unauthenticated one never collapse into one verdict.
    """
    probe = probe_client(harness, timeout=timeout, runner=runner, path_lookup=path_lookup)
    if probe is None or probe.status == STATUS_ABSENT:
        client_present = False
        client_version = None
    elif probe.status == STATUS_UNREAD:
        client_present = True
        client_version = UNREAD_VERSION
    else:
        client_present = True
        client_version = probe.version
    return Observation(
        name=harness.name,
        client_present=client_present,
        client_version=client_version,
        auth_configured=auth_signal(harness, environ=environ, home=home),
        launcher_contract=harness.launcher_contract,
        launcher_published=harness.launcher_published,
        product_withdrawn=harness.product_withdrawn,
        standing_blocker=harness.standing_blocker,
        probe=probe,
    )


def recorded_client_run(observation: Observation) -> bool:
    """Whether this record carries a client run somebody actually got an answer from."""
    probe = observation.probe
    return probe is not None and probe.status == STATUS_ANSWERED and observation.client_present


def classify(observation: Observation) -> str:
    """The one class this observation earns.

    The first branch is the gate ADR-076 puts here rather than in the schema:
    with no recorded client run, neither earned name is reachable from any input
    shape, whatever else the record claims.
    """
    if not recorded_client_run(observation):
        return UNSUPPORTED if observation.product_withdrawn else MANUAL_ROUTE
    if observation.product_withdrawn:
        return UNSUPPORTED
    if not observation.auth_configured:
        return MANUAL_ROUTE
    return ATLAS_LAUNCHER if observation.launcher_published else TESTED_LOCAL_ROUTE


def blocker_for(observation: Observation, classification: str) -> str | None:
    """The named reason this harness fell short, or None where nothing blocked it."""
    if classification in EARNED_CLASSIFICATIONS:
        return None
    reasons = [NO_CLIENT_DECLARED if observation.probe is None else observation.probe.result]
    reasons.append(AUTH_SIGNAL if observation.auth_configured else NO_AUTH_SIGNAL)
    reasons.append(observation.standing_blocker)
    return " ".join(_sentence(reason) for reason in reasons)


def _sentence(reason: str) -> str:
    trimmed = reason.rstrip(". ")
    return trimmed[:1].upper() + trimmed[1:] + "."


def entry_document(observation: Observation) -> dict[str, object]:
    """One `harnesses` entry, with its class derived rather than supplied."""
    classification = classify(observation)
    entry: dict[str, object] = {
        "name": observation.name,
        "classification": classification,
        "client_present": observation.client_present,
        "client_version": observation.client_version,
        # The structured half of the unread encoding. A reader must not have to
        # compare `client_version` against a magic string the schema does not
        # enumerate to learn whether anybody read a version, so the fact gets
        # its own boolean: true exactly when `client_version` holds a version a
        # client reported.
        "version_read": observation.client_version is not None
        and observation.client_version != UNREAD_VERSION,
        "auth_configured": observation.auth_configured,
        "launcher_contract": observation.launcher_contract,
        "blocker": blocker_for(observation, classification),
        "testable_here": observation.client_present and observation.auth_configured,
    }
    if observation.probe is not None:
        entry["probe"] = observation.probe.document()
    return entry


def manifest_document(
    observations, *, host: str, date: str, base_ref: str
) -> dict[str, object]:
    """The whole `harness-classification/v1` document, ready to validate."""
    if not HOST_PATTERN.match(host):
        raise ProbeError("host must be a short alphanumeric platform name")
    if not DATE_PATTERN.match(date):
        raise ProbeError("date must be YYYY-MM-DD")
    if not BASE_REF_PATTERN.match(base_ref):
        raise ProbeError("base ref must be a 40-character lowercase hexadecimal sha")
    entries = [entry_document(observation) for observation in observations]
    if not entries:
        raise ProbeError("a manifest needs at least one harness")
    return {
        "schema": SCHEMA_ID,
        "recorded": {"host": host, "date": date, "base_ref": base_ref},
        "harnesses": entries,
    }


def probe_roster(
    *,
    recorder: Recorder,
    roster=ROSTER,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    runner=None,
    path_lookup=None,
    environ=None,
    home=None,
):
    """Observe every harness in the roster, recording one event each."""
    recorder.record("probe_run_started", harnesses=len(roster), timeout_s=timeout)
    observations = []
    for harness in roster:
        observation = observe(
            harness,
            timeout=timeout,
            runner=runner,
            path_lookup=path_lookup,
            environ=environ,
            home=home,
        )
        probe = observation.probe
        recorder.record(
            "harness_probe_done",
            harness=observation.name,
            command=list(probe.command) if probe is not None else [],
            status=probe.status if probe is not None else "not_declared",
            result=probe.result if probe is not None else NO_CLIENT_DECLARED,
            classification=classify(observation),
            client_present=observation.client_present,
            auth_configured=observation.auth_configured,
        )
        observations.append(observation)
    return tuple(observations)


def _atomic_write_text(target: Path, payload: str) -> Path:
    """Write a temporary file beside the target, then rename it over the target.

    The temporary file lives in the destination's own directory so the rename
    is a same-filesystem operation, which is what makes it atomic. A process
    killed before the rename leaves the target untouched and a stray dotfile
    behind; it never leaves a half-written file where a reader looks.
    """
    directory = target.parent
    if not directory.is_dir():
        raise ProbeError(f"destination directory {directory} does not exist")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(directory), prefix=TEMPORARY_PREFIX, suffix=TEMPORARY_SUFFIX
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise
    return target


def write_manifest(target, document, recorder: Recorder | None = None) -> Path:
    """Sweep the manifest for credential shapes, then write it atomically."""
    payload = json.dumps(document, indent=2) + "\n"
    _refuse_leak("manifest", payload)
    encoded = len(payload.encode("utf-8"))
    if encoded > MAX_MANIFEST_BYTES:
        raise ProbeError(f"manifest is {encoded} bytes, over the {MAX_MANIFEST_BYTES} cap")
    written = _atomic_write_text(Path(target), payload)
    if recorder is not None:
        # The file name only. An absolute path under a home directory is a
        # personal identifier, and telemetry is the wrong place for one.
        recorder.record(
            "manifest_written",
            target=written.name,
            harnesses=len(document["harnesses"]),
            bytes=encoded,
        )
    return written


def write_log(target, recorder: Recorder) -> Path:
    """Write the recorded events as one JSON object per line."""
    return _atomic_write_text(Path(target), recorder.lines())


def read_manifest(path):
    """Read a manifest a renderer would accept, or refuse it.

    This is the oracle behind the killed-write guard. A torn file is not valid
    JSON, and a file that parses but declares another schema is not this
    roster, so neither can be mistaken for a manifest somebody finished writing.
    """
    target = Path(path)
    size = target.stat().st_size
    if size > MAX_MANIFEST_BYTES:
        raise ProbeError(f"manifest is {size} bytes, over the {MAX_MANIFEST_BYTES} cap")
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProbeError(f"manifest is not readable JSON: {error}") from error
    if not isinstance(document, dict) or document.get("schema") != SCHEMA_ID:
        raise ProbeError(f"manifest does not declare {SCHEMA_ID}")
    harnesses = document.get("harnesses")
    if not isinstance(harnesses, list) or not harnesses:
        raise ProbeError("manifest declares no harnesses")
    return document


def resolve_base_ref(explicit: str | None, *, runner=None) -> str:
    """The 40-hex ref this run was taken against, validated before it is used."""
    if explicit is not None:
        if not BASE_REF_PATTERN.match(explicit):
            raise ProbeError("base ref must be a 40-character lowercase hexadecimal sha")
        return explicit
    runner = _run if runner is None else runner
    try:
        completed = runner(BASE_REF_ARGV, DEFAULT_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ProbeError(f"could not read the base ref: {type(error).__name__}") from error
    candidate = (completed.stdout or "").strip()
    if completed.returncode != 0 or not BASE_REF_PATTERN.match(candidate):
        raise ProbeError("git did not report a 40-character base ref; pass --base-ref")
    return candidate


def default_host() -> str:
    return f"{platform.system().lower()}-{platform.machine()}"


def _checked_timeout(value: float) -> float:
    if not 0 < value <= MAX_TIMEOUT_SECONDS:
        raise ProbeError(f"timeout must be above 0 and at most {MAX_TIMEOUT_SECONDS:g}s")
    return value


def _checked_out(raw: str) -> Path:
    if not raw or "\x00" in raw:
        raise ProbeError("--out requires a non-empty path")
    return Path(raw).expanduser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe this host's Atlas hand-off clients.")
    parser.add_argument("--out", required=True, metavar="PATH", help="where to write the manifest")
    parser.add_argument("--log", metavar="PATH", help="where to write the structured probe log")
    parser.add_argument("--base-ref", metavar="SHA", help="the 40-hex ref this run was taken against")
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="the recorded observation date")
    parser.add_argument("--host", metavar="NAME", help="the recorded platform name")
    parser.add_argument("--run-id", metavar="HEX", help="the correlation id for this run's events")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"per-client bound, above 0 and at most {MAX_TIMEOUT_SECONDS:g}",
    )
    return parser


def main(argv=None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        target = _checked_out(arguments.out)
        recorder = Recorder(arguments.run_id or uuid.uuid4().hex)
        observations = probe_roster(
            recorder=recorder, timeout=_checked_timeout(arguments.timeout)
        )
        document = manifest_document(
            observations,
            host=arguments.host or default_host(),
            date=arguments.date or datetime.date.today().isoformat(),
            base_ref=resolve_base_ref(arguments.base_ref),
        )
        write_manifest(target, document, recorder)
        if arguments.log is not None:
            write_log(_checked_out(arguments.log), recorder)
    except ProbeError as error:
        print(f"probe_harnesses: {error}", file=sys.stderr)
        return 1
    for event in recorder.events:
        if event["event"] == "harness_probe_done":
            print(f"{event['harness']}: {event['classification']} -- {event['result']}")
    print(f"wrote {len(document['harnesses'])} harnesses to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
