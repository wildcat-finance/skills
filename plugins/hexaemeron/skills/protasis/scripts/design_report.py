#!/usr/bin/env python3
"""Run one design-evidence resolver and write its closed report.

usage: design_report.py --candidate <id> --criterion <id> --unit <unit>
                        --out <path> [--record <design-evidence.json>]
                        (--value-from-exit | --value-json <path> --value-key <key>)
                        -- <argv...>

The argv after `--` runs as a list with no shell, as the leader of its own
process group, under a 900 second timeout and a 1 MiB captured-output cap. On
the timeout the whole group is killed, and so is a descendant still holding the
output open after the child exits, so no resolver process outlives the wrapper
that way. The report written to `--out` is one closed
`protasis-design-report/v1` object: `exit` is the child's exit status and
`command` is the quoted argv. The value is `true` when the exit is 0 and
`false` otherwise (`--value-from-exit`, boolean unit only), or the named
top-level key of a JSON file the child wrote (`--value-json`, `--value-key`).
The wrapper records the exit and never turns it into a verdict; the
design-evidence checker does that against the record's threshold.

The record's directory is the directory holding `design-evidence.json`. With
`--record` it is that file's directory. Without it, `--out` must sit at
`<record dir>/design/reports/<file>`, the layout the record's report paths use,
and `<record dir>/design-evidence.json` must exist. Before the child runs the
wrapper refuses an `--out` that exists, is a symlink, lies outside the record's
directory, or equals any argv element, so a resolver's own report and the
controller's object can never share a path. The child may change the tree while
it runs, so the report is then created from the record's directory one
component at a time, following no link, with `O_EXCL`.

Exit 0 when a report was written, whatever the child's exit; 2 on a refusal,
which writes nothing.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import selectors
import shlex
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

REPORT_SCHEMA = "protasis-design-report/v1"
RECORD_NAME = "design-evidence.json"
REPORT_PARENTS = ("design", "reports")
TIMEOUT_SECONDS = 900
OUTPUT_CAP_BYTES = 1 << 20
MAX_VALUE_JSON_BYTES = 1 << 20
MAX_JSON_DEPTH = 64
MAX_COMMAND_BYTES = 4096
MAX_STRING_VALUE_BYTES = 512
READ_CHUNK = 64 * 1024
POLL_SECONDS = 1.0
DIRECTORY_FLAGS = (
    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
)
REPORT_FLAGS = (
    os.O_WRONLY | os.O_CREAT | os.O_EXCL
    | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
)

ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UNITS = ("boolean", "bytes", "count", "milliseconds", "ratio", "string")
INTEGER_UNITS = frozenset({"bytes", "count", "milliseconds"})


class Refusal(RuntimeError):
    """The wrapper will not run the child or write a report."""


class DuplicateKey(ValueError):
    pass


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey("duplicate object key")
        result[key] = value
    return result


def canonical(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")


def _bounded_text(value: object, maximum: int) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return len(encoded) <= maximum and all(character.isprintable() for character in value)


def value_matches_unit(value: object, unit: str) -> bool:
    if unit == "boolean":
        return isinstance(value, bool)
    if unit == "string":
        return _bounded_text(value, MAX_STRING_VALUE_BYTES)
    if unit in INTEGER_UNITS:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    if unit == "ratio":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and 0 <= value <= 1
        )
    return False


# -- argument handling ------------------------------------------------------


def split_argv(raw: list[str]) -> tuple[list[str], list[str]]:
    """Split the wrapper's options from the child argv at the first `--`."""
    if "--" not in raw:
        raise Refusal("the child argv must follow a `--` separator")
    index = raw.index("--")
    child = raw[index + 1:]
    if not child:
        raise Refusal("the child argv after `--` is empty")
    return raw[:index], child


def parse_options(options: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="design_report.py",
        description="Run one design-evidence resolver and write its closed report.",
    )
    parser.add_argument("--candidate", required=True, help="candidate id in the record")
    parser.add_argument("--criterion", required=True, help="criterion id in the record")
    parser.add_argument("--unit", required=True, choices=UNITS, help="the criterion's unit")
    parser.add_argument("--out", required=True, help="report path; must not exist")
    parser.add_argument(
        "--record",
        help=f"the {RECORD_NAME} whose directory bounds --out; "
             f"default: --out sits at <record dir>/design/reports/<file>",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--value-from-exit", action="store_true",
        help="value true when the child exits 0, false otherwise (boolean unit)",
    )
    source.add_argument(
        "--value-json", help="JSON object the child writes; the value is one key of it",
    )
    parser.add_argument("--value-key", help="top-level key of --value-json holding the value")
    args = parser.parse_args(options)
    if not ID.fullmatch(args.candidate) or not ID.fullmatch(args.criterion):
        raise Refusal("candidate and criterion must be kebab-case ids")
    if args.value_from_exit:
        if args.value_key is not None:
            raise Refusal("--value-key needs --value-json")
        if args.unit != "boolean":
            raise Refusal("--value-from-exit yields a boolean, so --unit must be boolean")
    elif args.value_key is None or not args.value_key:
        raise Refusal("--value-json needs a non-empty --value-key")
    return args


def command_text(child: list[str]) -> str:
    text = " ".join(shlex.quote(element) for element in child)
    if not _bounded_text(text, MAX_COMMAND_BYTES):
        raise Refusal(
            f"the quoted command must be printable and at most {MAX_COMMAND_BYTES} bytes"
        )
    return text


# -- path boundary ----------------------------------------------------------


def _regular_file(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
    except OSError:
        return False
    return stat.S_ISREG(mode) and not stat.S_ISLNK(mode)


def record_directory(out_abs: Path, record: str | None) -> Path:
    """The lexical directory of the record that bounds the report."""
    if record is not None:
        record_abs = Path(os.path.abspath(record))
        if not _regular_file(record_abs):
            raise Refusal(f"--record {record} is not a regular file")
        return record_abs.parent
    parents = (out_abs.parent.parent.name, out_abs.parent.name)
    if parents != REPORT_PARENTS or len(out_abs.parents) < 3:
        raise Refusal(
            "--out must sit at <record dir>/design/reports/<file> when no --record is given"
        )
    record_dir = out_abs.parent.parent.parent
    if not _regular_file(record_dir / RECORD_NAME):
        raise Refusal(f"no {RECORD_NAME} at {record_dir}, so --out has no record directory")
    return record_dir


def check_output_path(
    out: str, out_abs: Path, record_dir: Path, child: list[str], value_json: str | None,
) -> tuple[str, Path, tuple[int, int]]:
    """Refuse every collision; return the record-relative path and the record's identity."""
    if os.path.lexists(out_abs):
        if out_abs.is_symlink():
            raise Refusal(f"--out {out} is a symlink")
        raise Refusal(f"--out {out} already exists")
    try:
        relative = out_abs.relative_to(record_dir)
    except ValueError:
        raise Refusal(f"--out {out} lies outside the record directory {record_dir}") from None
    if any(part in ("", ".", "..") for part in relative.parts) or len(relative.parts) < 1:
        raise Refusal(f"--out {out} does not name a file below the record directory")
    try:
        record_real = record_dir.resolve(strict=True)
        record_stat = record_real.stat()
    except OSError:
        raise Refusal(f"the record directory {record_dir} cannot be resolved") from None
    lexical = record_dir
    for part in relative.parts:
        lexical = lexical / part
        if lexical.is_symlink():
            raise Refusal(f"--out {out} crosses a symlink at {lexical}")
    try:
        parent_real = out_abs.parent.resolve(strict=True)
        parent_real.relative_to(record_real)
    except (OSError, ValueError):
        raise Refusal(
            f"--out {out} resolves outside the record directory or its directory is absent"
        ) from None
    for index, element in enumerate(child):
        if element == out or os.path.abspath(element) == str(out_abs):
            raise Refusal(f"--out {out} equals child argv element {index}")
    if value_json is not None:
        if value_json == out or os.path.abspath(value_json) == str(out_abs):
            raise Refusal("--value-json must not equal --out")
        if os.path.lexists(value_json):
            raise Refusal(f"--value-json {value_json} exists before the child runs")
    return relative.as_posix(), record_real, (record_stat.st_dev, record_stat.st_ino)


# -- the child --------------------------------------------------------------


def _kill_group(process: subprocess.Popen) -> None:
    """Kill the child's process group, then the child itself.

    `start_new_session` makes the child the leader of its own group, so its pid
    is the group id and a resolver's own subprocesses go with it. A lookup
    failure means the group is already gone. A descendant that starts a session
    of its own has left the group and is out of this reach.
    """
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        pass
    try:
        process.kill()
    except OSError:
        pass


def run_child(child: list[str], timeout: float, cap: int) -> dict:
    """Run the argv with no shell; keep at most `cap` bytes of its output."""
    try:
        process = subprocess.Popen(
            child,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            start_new_session=True,
        )
    except (OSError, ValueError) as exc:
        reason = getattr(exc, "strerror", None) or str(exc)
        raise Refusal(f"the child argv could not be started: {reason}") from None
    deadline = time.monotonic() + timeout
    chunks: list[bytes] = []
    kept = 0
    total = 0
    timed_out = False
    drained = False
    held_open = False
    pipe = process.stdout
    try:
        descriptor = pipe.fileno()
        os.set_blocking(descriptor, False)
        with selectors.DefaultSelector() as selector:
            selector.register(descriptor, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                if not selector.select(timeout=min(remaining, POLL_SECONDS)):
                    if process.poll() is not None:
                        # The child has exited, yet something it started still
                        # holds the output open: stop waiting on it.
                        held_open = True
                        break
                    continue
                try:
                    chunk = os.read(descriptor, READ_CHUNK)
                except BlockingIOError:
                    continue
                if not chunk:
                    drained = True
                    break
                total += len(chunk)
                if kept < cap:
                    taken = chunk[: cap - kept]
                    chunks.append(taken)
                    kept += len(taken)
        if process.poll() is None:
            try:
                process.wait(timeout=max(deadline - time.monotonic(), 0))
            except subprocess.TimeoutExpired:
                timed_out = True
    finally:
        if not drained or process.returncode is None:
            _kill_group(process)
        process.wait()
        pipe.close()
    return {
        "exit": process.returncode,
        "captured": b"".join(chunks),
        "output_bytes": total,
        "truncated": total > cap,
        "timed_out": timed_out,
        "held_open": held_open or (not drained and not timed_out),
    }


# -- the value --------------------------------------------------------------


def _json_depth_within_limit(data: bytes) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for byte in data:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                return False
        elif byte in (0x5D, 0x7D) and depth:
            depth -= 1
    return True


def read_value(value_json: str, key: str, unit: str) -> object:
    path = Path(value_json)
    if not _regular_file(path):
        raise Refusal(f"the child did not leave a regular file at {value_json}")
    try:
        if path.lstat().st_size > MAX_VALUE_JSON_BYTES:
            raise Refusal(f"{value_json} exceeds {MAX_VALUE_JSON_BYTES} bytes")
        descriptor = os.open(
            path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            data = os.read(descriptor, MAX_VALUE_JSON_BYTES + 1)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise Refusal(f"{value_json} cannot be read: {exc.strerror}") from None
    if len(data) > MAX_VALUE_JSON_BYTES or not _json_depth_within_limit(data):
        raise Refusal(f"{value_json} is oversized or too deeply nested")
    try:
        document = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number {token}")
            ),
        )
    except (DuplicateKey, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Refusal(f"{value_json} is not strict JSON: {exc}") from None
    if not isinstance(document, dict) or key not in document:
        raise Refusal(f"{value_json} is not an object carrying the key {key!r}")
    value = document[key]
    if not value_matches_unit(value, unit):
        raise Refusal(f"the value at {key!r} does not match the unit {unit}")
    return value


# -- the report -------------------------------------------------------------


def write_report(
    record_real: Path, identity: tuple[int, int], relative: str, payload: dict,
) -> bytes:
    """Create the report below the record directory, following no link.

    The path was checked before the child ran, and the child may have changed
    the tree since. So the walk starts from the record directory checked then,
    opens each directory below it with `O_NOFOLLOW`, and creates the report with
    `O_EXCL`. A write that fails removes the file it created, so a refusal
    leaves nothing at `--out`.
    """
    if os.open not in os.supports_dir_fd or not getattr(os, "O_NOFOLLOW", 0):
        raise Refusal("this platform cannot create the report without following links")
    data = canonical(payload)
    parts = relative.split("/")
    try:
        directory = os.open(record_real, DIRECTORY_FLAGS)
    except OSError:
        raise Refusal(f"the record directory {record_real} changed while the child ran") from None
    try:
        opened = os.fstat(directory)
        if (opened.st_dev, opened.st_ino) != identity:
            raise Refusal(f"the record directory {record_real} changed while the child ran")
        for part in parts[:-1]:
            try:
                below = os.open(part, DIRECTORY_FLAGS, dir_fd=directory)
            except OSError:
                raise Refusal(
                    f"{relative} no longer lies below the record directory through "
                    "real directories"
                ) from None
            os.close(directory)
            directory = below
        try:
            descriptor = os.open(parts[-1], REPORT_FLAGS, 0o644, dir_fd=directory)
        except FileExistsError:
            raise Refusal(f"{relative} appeared before the report could be written") from None
        except OSError as exc:
            raise Refusal(f"{relative} could not be created: {exc.strerror}") from None
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            try:
                os.unlink(parts[-1], dir_fd=directory)
            except OSError:
                pass
            raise Refusal(f"{relative} could not be written and was removed: {exc.strerror}") from None
    finally:
        os.close(directory)
    return data


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    try:
        options, child = split_argv(raw)
        args = parse_options(options)
        command = command_text(child)
        out_abs = Path(os.path.abspath(args.out))
        record_dir = record_directory(out_abs, args.record)
        report_path, record_real, identity = check_output_path(
            args.out, out_abs, record_dir, child, args.value_json,
        )
        outcome = run_child(child, TIMEOUT_SECONDS, OUTPUT_CAP_BYTES)
        if outcome["captured"]:
            sys.stderr.write(outcome["captured"].decode("utf-8", "replace"))
            if not outcome["captured"].endswith(b"\n"):
                sys.stderr.write("\n")
        if outcome["timed_out"]:
            print(
                f"design_report: the child exceeded the {TIMEOUT_SECONDS} s timeout and "
                f"its process group was killed; its exit {outcome['exit']} is recorded, "
                "not judged",
                file=sys.stderr,
            )
        elif outcome["held_open"]:
            print(
                f"design_report: the child exited {outcome['exit']} while a process it "
                "started still held its output; that process group was killed",
                file=sys.stderr,
            )
        if outcome["truncated"]:
            print(
                f"design_report: captured output truncated at the {OUTPUT_CAP_BYTES} byte "
                f"cap; the child emitted {outcome['output_bytes']} bytes",
                file=sys.stderr,
            )
        if args.value_from_exit:
            value: object = outcome["exit"] == 0
        else:
            value = read_value(args.value_json, args.value_key, args.unit)
        payload = {
            "schema": REPORT_SCHEMA,
            "candidate": args.candidate,
            "criterion": args.criterion,
            "value": value,
            "unit": args.unit,
            "command": command,
            "exit": outcome["exit"],
        }
        write_report(record_real, identity, report_path, payload)
    except Refusal as exc:
        print(f"design_report: refused, {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "candidate": args.candidate,
        "criterion": args.criterion,
        "unit": args.unit,
        "value": value,
        "exit": outcome["exit"],
        "report": report_path,
        "out": str(out_abs),
        "captured_bytes": len(outcome["captured"]),
        "output_bytes": outcome["output_bytes"],
        "truncated": outcome["truncated"],
        "timed_out": outcome["timed_out"],
        "timeout_seconds": TIMEOUT_SECONDS,
        "output_cap_bytes": OUTPUT_CAP_BYTES,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
