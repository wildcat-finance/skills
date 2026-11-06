#!/usr/bin/env python3
"""Measure proposed source rows against the three declared specimen inputs.

This is a design probe, not the implementation. Reports print to stdout and
are written only when --out names a fresh file. Conformance runs the real
plugin suite and checks all three rebuilt manifest row contracts.
"""
import argparse
import copy
import hashlib
import json
import os
import stat
from pathlib import Path
import statistics
import shlex
import sys
import subprocess
import time

CANDIDATES = ('manifest-only', 'full-rights', 'retained-rights')
CRITERIA = ('rights-bound', 'private-prose', 'row-bytes', 'probe-ms', 'ids-moved', 'repeatable', 'implementation')
# Resolve the shipped probe beside its specimens, even from another directory.
ROOT = Path(__file__).resolve().parents[5]
SPECIMENS = ROOT / 'plugins/anamnesis/specimens'
NAMES = ('pilot', 'estate', 'synopsis')
COMPONENTS = ('engagements', 'assertions', 'relations', 'quarantine', 'unknowns')
MAX_INPUT_BYTES = 1_048_576


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def row(candidate, source):
    result = {k: source[k] for k in ('id', 'sha256', 'bytes')}
    result['disclosure'] = source['rights']['disclosure']
    result['basis'] = source['rights']['basis']
    result['rights_sha256'] = hashlib.sha256(canonical(source['rights'])).hexdigest()
    if candidate == 'full-rights':
        result['rights'] = copy.deepcopy(source['rights'])
    return result


def identity(candidate, policy, rows, graph):
    h = hashlib.sha256(canonical(policy))
    for source in sorted(rows, key=lambda s: s['id']):
        fields = ('id', 'sha256', 'bytes') if candidate == 'manifest-only' else ('id', 'sha256', 'bytes', 'disclosure', 'basis', 'rights_sha256')
        h.update(':'.join(str(source[k]) for k in fields).encode())
    for key in COMPONENTS:
        h.update(canonical(graph[key]))
    return h.hexdigest()



def read_json(path):
    """Read one fixed specimen input as a bounded regular file."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_INPUT_BYTES:
            raise ValueError('specimen input is not a bounded regular file')
        body = handle.read(MAX_INPUT_BYTES + 1)
    if len(body) > MAX_INPUT_BYTES:
        raise ValueError('specimen input exceeds the byte limit')
    return json.loads(body)

def inputs():
    result = []
    for name in NAMES:
        base = SPECIMENS / name
        sources = read_json(base / 'policy.json')['sources']
        policy = read_json(base / 'curation-policy.json')
        graph = {k: read_json(base / 'release' / (k + '.json')) for k in COMPONENTS}
        manifest = read_json(base / 'release/manifest.json')
        result.append((sources, policy, graph, manifest))
    return result


def measure(candidate, criterion):
    cases = inputs()
    if criterion == 'rights-bound':
        total = 0
        for sources, policy, graph, _ in cases:
            original = identity(candidate, policy, [row(candidate, s) for s in sources], graph)
            for key, value in (('basis', 'contract'), ('holder', 'probe holder'), ('statement', 'probe decision'), ('disclosure', 'restricted')):
                changed = copy.deepcopy(sources)
                changed[0]['rights'][key] = value
                total += identity(candidate, policy, [row(candidate, s) for s in changed], graph) != original
        return total, 'count'
    if criterion == 'private-prose':
        return sum(len(canonical(r['rights'])) for sources, _, _, _ in cases for s in sources if 'rights' in (r := row(candidate, s))), 'bytes'
    if criterion == 'row-bytes':
        return sum(len(canonical([row(candidate, s) for s in sources])) for sources, _, _, _ in cases), 'bytes'
    if criterion == 'probe-ms':
        elapsed = []
        for _ in range(7):
            start = time.perf_counter_ns()
            for _repeat in range(100):
                for sources, policy, graph, _ in cases:
                    identity(candidate, policy, [row(candidate, s) for s in sources], graph)
            elapsed.append((time.perf_counter_ns() - start) / 1_000_000)
        return round(statistics.median(elapsed)), 'milliseconds'
    if criterion == 'ids-moved':
        return sum(identity(candidate, policy, [row(candidate, s) for s in sources], graph) != identity('manifest-only', policy, [row('manifest-only', s) for s in sources], graph) for sources, policy, graph, _ in cases), 'count'
    if criterion == 'repeatable':
        return all(identity(candidate, policy, [row(candidate, s) for s in sources], graph) == identity(candidate, policy, json.loads(canonical([row(candidate, s) for s in reversed(sources)])), graph) for sources, policy, graph, _ in cases), 'boolean'
    if criterion == 'implementation':
        if candidate != 'retained-rights':
            raise SystemExit('rejected candidate has no implementation')
        run = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'plugins/anamnesis/tests', '-t', 'plugins/anamnesis'], capture_output=True, text=True, timeout=300, cwd=ROOT)
        if run.returncode:
            raise SystemExit(run.stdout + run.stderr)
        for sources, policy, graph, manifest in cases:
            expected = sorted([row(candidate, s) for s in sources], key=lambda s: s['id'])
            if manifest['sources'] != expected or manifest['release_id'] != identity(candidate, policy, expected, graph):
                raise SystemExit('shipped manifest differs from retained-rights construction')
        return True, 'boolean'
    raise SystemExit('unknown criterion')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('candidate', choices=CANDIDATES)
    parser.add_argument('criterion', choices=CRITERIA)
    parser.add_argument('--out')
    args = parser.parse_args()
    if args.out and os.path.lexists(args.out):
        raise SystemExit('source-rights resolver: output already exists; name a fresh file')
    try:
        value, unit = measure(args.candidate, args.criterion)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        raise SystemExit(f'source-rights resolver: {type(error).__name__}; no report written') from None
    report = {'schema': 'protasis-design-report/v1', 'candidate': args.candidate, 'criterion': args.criterion, 'value': value, 'unit': unit, 'command': shlex.join(['python3', *sys.argv]), 'exit': 0}
    body = canonical(report).decode()
    if args.out:
        try:
            with open(args.out, 'x', encoding='utf-8') as handle:
                handle.write(body)
        except OSError as error:
            raise SystemExit(f'source-rights resolver: {type(error).__name__}; output refused') from None
    print(body, end='')


if __name__ == '__main__':
    main()
