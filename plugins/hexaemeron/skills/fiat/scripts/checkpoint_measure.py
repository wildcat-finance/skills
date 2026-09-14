#!/usr/bin/env python3
"""Measure one checkpoint using its saved export and fresh local read/restore.

Export wall time is the controller's recorded timing_ms.export interval; peak
RSS covers the complete producer command. Inspect and restore wall times cover
whole fresh commands under /usr/bin/time. These scopes are kept in the record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

PREFIX = 'checkpoint.archive.'
NAMES = tuple(PREFIX + name for name in (
    'export_wall_ms', 'inspect_wall_ms', 'restore_wall_ms', 'bytes',
    'expanded_bytes', 'export_peak_rss_bytes',
))
OUTPUT_CAP = 2 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}')


def read_bytes(path: Path, maximum: int = OUTPUT_CAP) -> bytes:
    """Read one bounded regular file, refusing symlinks and excess bytes."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError('input must be a regular non-symlink file')
        data = handle.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('input exceeds byte limit')
    return data


def snapshot_archive(source: Path, destination: Path, expected: str, size: int) -> None:
    """Copy bounded bytes once; all consumers then share the verified private file."""
    checked_integer(size)
    if size > 1024 * 1024 * 1024:
        raise ValueError('archive exceeds snapshot ceiling')
    descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    hasher = hashlib.sha256()
    total = 0
    with os.fdopen(descriptor, 'rb') as reader, destination.open('xb') as writer:
        if not stat.S_ISREG(os.fstat(reader.fileno()).st_mode):
            raise ValueError('archive must be a regular file')
        while chunk := reader.read(min(1024 * 1024, size - total + 1)):
            total += len(chunk)
            if total > size:
                raise ValueError('archive exceeds saved size')
            hasher.update(chunk)
            writer.write(chunk)
    if total != size or hasher.hexdigest() != expected:
        raise ValueError('archive snapshot differs from saved export')


def digest(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def checked_integer(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError('measurement must be a non-negative integer')
    return value


class CommandFailure(ValueError):
    """Carry bounded operation evidence to the caller's failure record."""
    def __init__(self, result: dict):
        super().__init__('command failed')
        self.record = {key: result[key] for key in ('exit', 'wall_ms', 'failure')}
        self.record.update({name + '_sha256': hashlib.sha256(result[name].encode()).hexdigest()
                            for name in ('stdout', 'stderr')})


def command(argv: list[str], *, timeout: int = 120, env=None) -> dict:
    """Return bounded command output, status and whole-command elapsed time."""
    start = time.monotonic()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=env, shell=False, start_new_session=True)
    streams = {'stdout': bytearray(), 'stderr': bytearray()}
    selector = selectors.DefaultSelector()
    assert process.stdout is not None and process.stderr is not None
    selector.register(process.stdout, selectors.EVENT_READ, 'stdout')
    selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
    failure = None
    try:
        while selector.get_map():
            if time.monotonic() - start > timeout:
                failure = 'timeout'
                break
            for key, _ in selector.select(0.1):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                streams[key.data].extend(chunk)
                if sum(map(len, streams.values())) > OUTPUT_CAP:
                    failure = 'output-cap'
                    break
            if failure:
                break
        if failure:
            # The leader has not been polled or reaped, so its PID cannot name
            # another process group while the complete owned group is killed.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            status = process.wait(timeout=max(0.1, timeout - (time.monotonic() - start)))
        except subprocess.TimeoutExpired:
            failure = 'timeout'
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            status = process.wait()
        return {'exit': status, 'failure': failure, 'wall_ms': round((time.monotonic() - start) * 1000),
                **{name: bytes(value[:OUTPUT_CAP]).decode('utf-8',errors='replace') for name, value in streams.items()}}
    finally:
        if process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        selector.close()
        process.stdout.close()
        process.stderr.close()


def require_success(result: dict) -> dict:
    if result['exit'] != 0 or result.get('failure'):
        raise CommandFailure(result)
    return result


def saved_measurements(export: dict, rss_text: str, *, system: str,
                       inspect_ms: int, restore_ms: int, expanded_bytes: int) -> dict:
    """Join saved producer measurements with fresh consumer intervals."""
    if export.get('schema') != 'fiat-checkpoint-archive-export/v1':
        raise ValueError('unsupported export result')
    if system == 'darwin':
        matches = re.findall(r'^\s*(\d+)\s+maximum resident set size\s*$', rss_text, re.M)
        multiplier = 1
    elif system.startswith('linux'):
        matches = re.findall(r'^\s*Maximum resident set size \(kbytes\):\s*(\d+)\s*$', rss_text, re.M)
        multiplier = 1024
    else:
        raise ValueError('unsupported time output platform')
    if len(matches) != 1:
        raise ValueError('saved export RSS is absent or ambiguous')
    values = (export['timing_ms']['export'], inspect_ms, restore_ms, export['bytes'],
              expanded_bytes, int(matches[0]) * multiplier)
    return dict(zip(NAMES, map(checked_integer, values)))


def read_export(root: Path, archive: Path, expected: str) -> tuple[dict, str]:
    """Require saved producer evidence for this exact externally named archive."""
    if not HEX.fullmatch(expected):
        raise ValueError('outer digest must be lowercase SHA-256')
    export = json.loads(read_bytes(root / '.hexaemeron/metron/step-4-export.json'))
    if export.get('outer_sha256') != expected or Path(export['archive']).resolve() != archive:
        raise ValueError('saved export belongs to another archive')
    size = checked_integer(export.get('bytes'))
    if size > 1024 * 1024 * 1024 or size != archive.stat().st_size or digest(archive) != expected:
        raise ValueError('archive differs from saved export')
    rss = read_bytes(root / '.hexaemeron/metron/step-4-export.time.txt').decode('utf-8')
    return export, rss


def write_json(path: Path, value: dict) -> None:
    """Publish a complete local record after writing a sibling temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError('output cannot be a symlink')
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                     prefix='.checkpoint-', delete=False) as handle:
        staged = Path(handle.name)
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write('\n')
    try:
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def measure(archive: Path, expected: str, root: Path) -> dict:
    export, rss = read_export(root, archive, expected)
    controller = Path(__file__).with_name('hexctl.py').resolve()
    flag = '-l' if sys.platform == 'darwin' else '-v'
    if sys.platform != 'darwin' and not sys.platform.startswith('linux'):
        raise ValueError('measurement requires macOS or Linux')
    with tempfile.TemporaryDirectory(prefix='checkpoint-measure-') as temporary:
        scratch = Path(temporary).resolve()
        verified_archive = scratch / 'checkpoint.zip'
        snapshot_archive(archive, verified_archive, expected, export['bytes'])
        operations = {}
        for name, tail in (
            ('inspect', ['checkpoint', 'inspect', '--archive', str(verified_archive), '--sha256', expected]),
            ('restore', ['--dir', str(scratch / 'destination'), 'checkpoint', 'restore',
                         '--archive', str(verified_archive), '--sha256', expected]),
        ):
            try:
                operations[name] = require_success(command(
                    ['/usr/bin/time', flag, sys.executable, str(controller), *tail]))
            except CommandFailure as error:
                error.record['name'] = name
                raise
        inspected = json.loads(operations['inspect']['stdout'])
        restored = json.loads(operations['restore']['stdout'])
        if inspected['outer_sha256'] != expected or inspected['findings'] or restored['outer_sha256'] != expected:
            raise ValueError('consumer output does not bind this archive')
        with zipfile.ZipFile(verified_archive) as reader:
            manifest = json.loads(reader.read('checkpoint.json'))
            expanded = sum(item['bytes'] for item in manifest['archive']['entries']) + len(reader.read('checkpoint.json'))
    measurements = saved_measurements(export, rss, system=sys.platform,
        inspect_ms=operations['inspect']['wall_ms'], restore_ms=operations['restore']['wall_ms'],
        expanded_bytes=expanded)
    return {'schema': 'fiat-checkpoint-measurements/v1', 'outer_sha256': expected,
            'controller_sha256': digest(controller), 'platform': sys.platform,
            'method': {'export_wall_ms': 'saved timing_ms.export controller interval',
                       'export_peak_rss_bytes': 'saved whole producer command maximum RSS',
                       'consumer_wall_ms': 'one whole command under /usr/bin/time; no warm-up; verified private copy excluded'},
            'measurements': measurements,
            'operations': {name: {'exit': record['exit'], 'wall_ms': record['wall_ms'],
                                 'time_output': record['stderr'],
                                 'stdout_sha256': hashlib.sha256(record['stdout'].encode()).hexdigest()}
                           for name, record in operations.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = measure(args.archive.resolve(), args.sha256, Path.cwd())
        write_json(args.out, result)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        write_json(args.out.with_suffix('.failure.json'), {'schema': 'fiat-checkpoint-measurement-failure/v1',
            'failure': type(error).__name__, 'operation': getattr(error, 'record', None)})
        print('checkpoint_measure: refused: ' + type(error).__name__, file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
