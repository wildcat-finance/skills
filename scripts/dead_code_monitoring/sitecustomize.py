"""Process-local Python 3.14 execution probe for ``dead_code.py coverage``.

This module is loaded only when the coverage command prepends this directory to
``PYTHONPATH``.  A checked-runner containment marker is also required, so the
orchestrating runner is never monitored and recursive direct use is inert.
"""

from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import stat
import sys
import uuid

ACTIVE_ENV = "WILDCAT_DEAD_CODE_COVERAGE_ACTIVE"
OUTPUT_ENV = "WILDCAT_DEAD_CODE_COVERAGE_OUTPUT"
CONTAINMENT_ENV = "WILDCAT_CHECK_CONTAINMENT"
SOURCE_ROOT_ENV = "WILDCAT_DEAD_CODE_COVERAGE_SOURCE_ROOT"
SCHEMA = "dead-code-process-coverage/v1"
MAX_EVENTS = 50_000
MAX_RECORD_BYTES = 16 * 1024 * 1024
MAX_ARG_BYTES = 16 * 1024
TOOL_NAME = "wildcat-dead-code-coverage"


def _repository_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        try:
            marker = candidate / ".git"
            info = marker.lstat()
        except OSError:
            continue
        if stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode):
            return candidate
    return None


def _safe_argv() -> list[str]:
    retained: list[str] = []
    consumed = 0
    for item in getattr(sys, "orig_argv", sys.argv):
        encoded = os.fsencode(item)
        if consumed + len(encoded) > MAX_ARG_BYTES:
            retained.append("<truncated>")
            break
        retained.append(item)
        consumed += len(encoded)
    return retained


class MonitoringProbe:
    """Own one free monitoring id and put it back exactly as it was."""

    def __init__(self, output_directory: Path, repository_root: Path, run_id: str):
        self.output_directory = output_directory
        self.repository_root = repository_root.resolve()
        self.initial_cwd = Path.cwd()
        self.run_id = run_id
        self.tool_id = sys.monitoring.COVERAGE_ID
        self.started = False
        self.owns_tool = False
        self.closed = False
        self.truncated = False
        self.errors: list[str] = []
        self.lines: set[tuple[str, str, int]] = set()
        self.branches: set[tuple[str, str, int, int, str]] = set()
        self._line_cache: dict[object, dict[int, int]] = {}
        self._location_cache: dict[object, tuple[str, str] | None] = {}

    def _location(self, code: object) -> tuple[str, str] | None:
        if code in self._location_cache:
            return self._location_cache[code]
        filename = getattr(code, "co_filename", None)
        if not isinstance(filename, str) or not filename or filename.startswith("<"):
            self._location_cache[code] = None
            return None
        candidate = Path(filename)
        if not candidate.is_absolute():
            candidate = self.initial_cwd / candidate
        try:
            relative = Path(os.path.normpath(candidate)).relative_to(self.repository_root)
        except ValueError:
            self._location_cache[code] = None
            return None
        path = relative.as_posix()
        if not path.endswith(".py") or path.startswith("tmp/check-runner/"):
            self._location_cache[code] = None
            return None
        qualname = getattr(code, "co_qualname", getattr(code, "co_name", "<module>"))
        location = (path, str(qualname))
        self._location_cache[code] = location
        return location

    def _remember_line(self, code: object, line: int) -> object:
        if len(self.lines) >= MAX_EVENTS:
            self.truncated = True
            return sys.monitoring.DISABLE
        location = self._location(code)
        if location is None or line < 1:
            return sys.monitoring.DISABLE
        self.lines.add((*location, line))
        return sys.monitoring.DISABLE

    def _offset_line(self, code: object, offset: int) -> int | None:
        mapping = self._line_cache.get(code)
        if mapping is None:
            mapping = {}
            try:
                for start, end, line in code.co_lines():
                    if line is not None:
                        for instruction in range(start, end, 2):
                            mapping[instruction] = line
            except (AttributeError, TypeError, ValueError) as error:
                self.errors.append(f"line-map:{type(error).__name__}")
            self._line_cache[code] = mapping
        return mapping.get(offset)

    def _remember_branch(
        self,
        direction: str,
        code: object,
        source: int,
        target: int,
    ) -> object:
        if len(self.branches) >= MAX_EVENTS:
            self.truncated = True
            return sys.monitoring.DISABLE
        location = self._location(code)
        if location is None:
            return sys.monitoring.DISABLE
        source_line = self._offset_line(code, source)
        target_line = self._offset_line(code, target)
        if source_line is None or target_line is None:
            return sys.monitoring.DISABLE
        self.branches.add((*location, source_line, target_line, direction))
        return sys.monitoring.DISABLE

    def _left(self, code: object, source: int, target: int) -> object:
        return self._remember_branch("left", code, source, target)

    def _right(self, code: object, source: int, target: int) -> object:
        return self._remember_branch("right", code, source, target)

    def start(self) -> bool:
        monitoring = sys.monitoring
        if monitoring.get_tool(self.tool_id) is not None:
            self.errors.append("coverage-tool-id-in-use")
            return False
        monitoring.use_tool_id(self.tool_id, TOOL_NAME)
        self.owns_tool = True
        try:
            monitoring.register_callback(self.tool_id, monitoring.events.LINE, self._remember_line)
            monitoring.register_callback(self.tool_id, monitoring.events.BRANCH_LEFT, self._left)
            monitoring.register_callback(self.tool_id, monitoring.events.BRANCH_RIGHT, self._right)
            monitoring.set_events(
                self.tool_id,
                monitoring.events.LINE
                | monitoring.events.BRANCH_LEFT
                | monitoring.events.BRANCH_RIGHT,
            )
        except BaseException:
            self._restore()
            raise
        self.started = True
        return True

    def _restore(self) -> None:
        monitoring = sys.monitoring
        if not self.owns_tool:
            return
        owner = monitoring.get_tool(self.tool_id)
        if owner != TOOL_NAME:
            reason = "ownership-lost" if owner is None else "ownership-changed"
            self.errors.append(f"restore:{reason}")
            self.owns_tool = False
            return
        try:
            monitoring.set_events(self.tool_id, 0)
            for event in (
                monitoring.events.LINE,
                monitoring.events.BRANCH_LEFT,
                monitoring.events.BRANCH_RIGHT,
            ):
                monitoring.register_callback(self.tool_id, event, None)
            monitoring.free_tool_id(self.tool_id)
        except (RuntimeError, ValueError) as error:
            self.errors.append(f"restore:{type(error).__name__}")
        finally:
            self.owns_tool = False

    def _document(self) -> dict[str, object]:
        containment = os.environ.get(CONTAINMENT_ENV, "")
        return {
            "schema": SCHEMA,
            "run": self.run_id,
            "process": {
                "pid": os.getpid(),
                "parent_pid": os.getppid(),
                "containment": containment,
                "argv": _safe_argv(),
                "cwd": Path.cwd().as_posix(),
            },
            "status": {
                "state": "degraded" if self.truncated or self.errors or not self.started else "ran",
                "truncated": self.truncated,
                "errors": sorted(set(self.errors)),
            },
            "lines": [
                {"path": path, "function": function, "line": line}
                for path, function, line in sorted(self.lines)
            ],
            "branches": [
                {
                    "path": path,
                    "function": function,
                    "from_line": source,
                    "to_line": target,
                    "direction": direction,
                }
                for path, function, source, target, direction in sorted(self.branches)
            ],
        }

    def _write(self) -> None:
        document = self._document()
        payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if len(payload) > MAX_RECORD_BYTES:
            document["lines"] = []
            document["branches"] = []
            document["status"] = {
                "state": "degraded",
                "truncated": True,
                "errors": sorted(set([*self.errors, "record-byte-limit"])),
            }
            payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        directory_fd = os.open(
            self.output_directory,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            name = f"process-{os.getpid()}-{uuid.uuid4().hex}.json"
            fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self._restore()
        try:
            self._write()
        except OSError:
            pass


def _activate() -> MonitoringProbe | None:
    run_id = os.environ.get(ACTIVE_ENV, "")
    output = os.environ.get(OUTPUT_ENV, "")
    if not run_id or not output or not os.environ.get(CONTAINMENT_ENV):
        return None
    if not hasattr(sys, "monitoring"):
        return None
    if len(run_id) != 32 or any(character not in "0123456789abcdef" for character in run_id):
        return None
    inherited_root = os.environ.get(SOURCE_ROOT_ENV)
    root = Path(inherited_root) if inherited_root else _repository_root(Path.cwd().resolve())
    if root is None:
        return None
    try:
        root = root.resolve(strict=True)
    except OSError:
        return None
    os.environ[SOURCE_ROOT_ENV] = str(root)
    probe = MonitoringProbe(Path(output), root, run_id)
    try:
        probe.start()
    except (RuntimeError, ValueError):
        probe.errors.append("monitoring-start-failed")
    atexit.register(probe.close)
    return probe


PROBE = _activate() if __name__ == "sitecustomize" else None
