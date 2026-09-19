from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from plugins.hexaemeron.tests import test_hexctl_checkpoint_archive as fixture

CTL = fixture.hexctl_module()
REPORTS = ROOT / '.hexaemeron/reports'
PUBLIC = (
    'audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md',
    'audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.synopsis.md',
)
LB = re.compile(rb'\\u000[dD]\\u000[aA]|\\r\\n|\r\n|\\u000[aAdD]|\\[nr]|[\r\n]')
BODY_RUN = re.compile(rb'[A-Za-z0-9+/=]+')
ARMOUR = re.compile(rb'(?:Version|Comment|MessageID|Hash|Charset|Proc-Type|DEK-Info):[^\n]*\n')
HEAD_PREFIX = b'-' * 5 + b'BEGIN '
END_PREFIX = b'-' * 5 + b'END '


def markers(label=b'RSA PRIVATE KEY'):
    return HEAD_PREFIX + label + b'-' * 5, END_PREFIX + label + b'-' * 5


def bodies_only(data):
    if any(p.search(data) for p in CTL.CHECKPOINT_ARCHIVE_SECRET_TOKEN_PATTERNS):
        return True
    positions = [m.start() for m in CTL.CHECKPOINT_ARCHIVE_SECRET_BODY.finditer(data)]
    for pattern in CTL.CHECKPOINT_ARCHIVE_SECRET_BLOCK_PATTERNS:
        index = 0
        for match in pattern.finditer(data):
            while index < len(positions) and positions[index] < match.end():
                index += 1
            if index < len(positions) and positions[index] < match.end() + CTL.CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD:
                return True
    return False


def material_prefix(data, start):
    stop = min(len(data), start + CTL.CHECKPOINT_ARCHIVE_SECRET_FOOTER_LOOKAHEAD)
    raw = data[start:stop]
    pos = 0
    armour_count = 0
    while pos < len(raw):
        while pos < len(raw) and raw[pos] in b' \t':
            pos += 1
        line_break = LB.match(raw, pos)
        if line_break:
            pos = line_break.end()
            continue
        tail = LB.sub(b'\n', raw[pos:pos + 268])
        armour = ARMOUR.match(tail)
        if armour:
            original_break = LB.search(raw, pos)
            if original_break is None or original_break.start() - pos > 256:
                return False
            armour_count += 1
            if armour_count > 7:
                return False
            pos = original_break.end()
            continue
        break
    if pos >= CTL.CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD:
        return False
    count = 0
    while pos < len(raw):
        escaped = False
        run = BODY_RUN.match(raw, pos)
        if run:
            count += run.end() - pos
            pos = run.end()
            if count >= 16:
                return True
        elif raw[pos:pos + 2] == b'\\/':
            escaped = True
            count += 1
            pos += 2
            if count >= 16:
                return True
        else:
            return False
        end_of_segment = pos
        while pos < len(raw) and raw[pos] in b' \t':
            pos += 1
        line_break = LB.match(raw, pos)
        if line_break:
            pos = line_break.end()
            while pos < len(raw) and raw[pos] in b' \t':
                pos += 1
            continue
        if raw[pos:pos + 2] == b'\\/':
            if pos != end_of_segment:
                return False
            continue
        if escaped and pos == end_of_segment and BODY_RUN.match(raw, pos):
            continue
        return False
    return False


def bounded_material(data):
    if bodies_only(data):
        return True
    return any(material_prefix(data, m.end())
               for p in CTL.CHECKPOINT_ARCHIVE_SECRET_BLOCK_PATTERNS
               for m in p.finditer(data))


def complete_decoder(data):
    if any(p.search(data) for p in CTL.CHECKPOINT_ARCHIVE_SECRET_TOKEN_PATTERNS):
        return True
    for pattern in CTL.CHECKPOINT_ARCHIVE_SECRET_BLOCK_PATTERNS:
        for match in pattern.finditer(data):
            footer = END_PREFIX + match.group(0)[len(HEAD_PREFIX):]
            end = data.find(footer, match.end(), match.end() + CTL.CHECKPOINT_ARCHIVE_SECRET_FOOTER_LOOKAHEAD)
            if end < 0:
                continue
            text = LB.sub(b'\n', data[match.end():end]).replace(b'\\/', b'/')
            rows = [row.strip(b' \t') for row in text.split(b'\n') if row.strip(b' \t')]
            while rows and ARMOUR.fullmatch(rows[0] + b'\n'):
                rows.pop(0)
            try:
                decoded = base64.b64decode(b''.join(rows), validate=True)
            except ValueError:
                continue
            if len(decoded) >= 12:
                return True
    return False


CANDIDATES = {
    'footer-proximity': CTL._checkpoint_archive_secret_shaped,
    'whole-lines-only': bodies_only,
    'bounded-material': bounded_material,
    'complete-decoder': complete_decoder,
}


def streaming(predicate, payload):
    carry = b''
    for at in range(0, len(payload), CTL.CHECKPOINT_IO_CHUNK):
        chunk = payload[at:at + CTL.CHECKPOINT_IO_CHUNK]
        if predicate(carry + chunk):
            return True
        carry = chunk[-CTL.CHECKPOINT_ARCHIVE_SECRET_WINDOW:]
    return False


def corpus():
    pem, modulus, public, private = fixture.rsa_private_key_pem()
    assert modulus.bit_length() == 3072
    assert pow(pow(0xC0FFEE, public, modulus), private, modulus) == 0xC0FFEE
    body = ''.join(pem.splitlines()[1:-1]).encode()
    positive = []
    spellings = [(name, value.encode()) for name, value in fixture.LINE_BREAK_SPELLINGS]
    spellings.extend([('numeric-uppercase-cr', b'\\u000D'), ('numeric-uppercase-lf', b'\\u000A'), ('numeric-uppercase-crlf', b'\\u000D\\u000A')])
    for label in [b'PRIVATE KEY', b'RSA PRIVATE KEY', b'EC PRIVATE KEY', b'DSA PRIVATE KEY', b'ENCRYPTED PRIVATE KEY', b'OPENSSH PRIVATE KEY', b'PGP PRIVATE KEY BLOCK']:
        header, footer = markers(label)
        for name, ending in spellings:
            rows = [body[at:at + 64] for at in range(0, len(body), 64)]
            for closing in ['complete', 'no-footer', 'truncated']:
                content = ending.join(rows) if closing != 'truncated' else ending.join(rows[:2])
                suffix = ending + footer if closing == 'complete' else b''
                value = b'{"key":"' + header + ending + content + suffix + b'"}'
                positive.append((label.decode() + '/' + name + '/' + closing, value))
    header, footer = markers()
    for width in [1, 8]:
        for name, ending in spellings:
            rows = [body[at:at + width] for at in range(0, len(body), width)]
            for closing in ['complete', 'no-footer']:
                suffix = ending + footer if closing == 'complete' else b''
                value = header + ending + ending.join(rows) + suffix
                positive.append((f'rewrapped-{width}/{name}/{closing}', value))
    for label, metadata in [(b'RSA PRIVATE KEY', [b'Proc-Type: 4,ENCRYPTED', b'DEK-Info: AES-256-CBC,0123456789ABCDEF']), (b'PGP PRIVATE KEY BLOCK', [b'Version: fixture', b'Comment: disposable fixture', b'MessageID: example', b'Hash: SHA256', b'Charset: UTF-8'])]:
        header, footer = markers(label)
        for name, ending in spellings[1:]:
            for width in [1, 8, 64]:
                rows = [body[at:at + width] for at in range(0, len(body), width)]
                value = header + ending + ending.join(metadata) + ending * 2 + ending.join(rows) + ending + footer
                positive.append((f'metadata/{label.decode()}/{width}/{name}', value))
    header, footer = markers()
    for name, ending in spellings:
        twin = fixture.rsa_shaped_pem(8192).encode().replace(b'\n', ending)
        positive.append(('8192-geometry/' + name, twin))
    for name, ending in spellings:
        payload = header + ending + ending.join([b'/A/' * 3 for _ in range(100)]) + ending + footer
        positive.append(('escaped-solidus/' + name, payload.replace(b'/', b'\\/')))
    bodyline = b'A' * 64
    for split in [1, len(header) - 1, len(header) + 8, len(header) + 70]:
        value = b'#' * (CTL.CHECKPOINT_IO_CHUNK - split) + header + b'\n' + bodyline + b'\n' + footer
        positive.append((f'chunk-split-{split}', value))
    positive.append(('repeated-headers-with-material', (header + b'\n') * 100 + bodyline + b'\n' + footer))
    for i, token in enumerate(CTL.CHECKPOINT_ARCHIVE_SECRET_HEADERS[2:]):
        positive.append((f'token-{i}', token))
        positive.append((f'token-chunk-{i}', b'#' * (CTL.CHECKPOINT_IO_CHUNK - 2) + token))
    negative = [(path, (ROOT / path).read_bytes()) for path in PUBLIC]
    for label in [b'PRIVATE KEY', b'RSA PRIVATE KEY', b'OPENSSH PRIVATE KEY', b'PGP PRIVATE KEY BLOCK']:
        header, footer = markers(label)
        for name, ending in spellings:
            negative.append(('empty-pair/' + label.decode() + '/' + name, header + ending + footer))
            negative.append(('prose-pair/' + label.decode() + '/' + name, header + ending + b'this line is not base64' + ending + footer))
        negative.append(('header-only/' + label.decode(), b'`' + header + b'` is the marker.'))
        negative.append(('quoted-pair/' + label.decode(), b'`' + header + b'` and `' + footer + b'` name markers.'))
        negative.append(('repeated-empty/' + label.decode(), (header + b'\n' + footer + b'\n') * 100))
    negative.append(('public-key-body', markers(b'PGP PUBLIC KEY BLOCK')[0] + b'\n' + body + b'\n'))
    return positive, negative


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', choices=CANDIDATES, required=True)
    parser.add_argument('--criterion', choices=['material-refusals', 'benign-acceptance', 'scan-time', 'peak-allocation', 'token-parity', 'input-preservation'], required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    predicate = CANDIDATES[args.candidate]
    positive, negative = corpus()
    details = {'positive_count': len(positive), 'negative_count': len(negative), 'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PUBLIC}, 'seeded_rsa_bits': 3072, 'candidate': args.candidate, 'criterion': args.criterion}
    unit = 'boolean'
    if args.criterion in ['material-refusals', 'benign-acceptance']:
        cases = positive if args.criterion == 'material-refusals' else negative
        wanted = args.criterion == 'material-refusals'
        failures = [name for name, value in cases if streaming(predicate, value) != wanted]
        value, unit = len(failures), 'count'
        details['mismatches'] = failures
    elif args.criterion in ['scan-time', 'peak-allocation']:
        header = markers(b'PGP PRIVATE KEY BLOCK')[0]
        workloads = [b'#' * (1024 * 1024), (header + b'\n') * (1024 * 1024 // (len(header) + 1))] + [v for _, v in negative[:2]]
        if args.criterion == 'scan-time':
            samples = []
            for _ in range(5):
                start = time.perf_counter_ns()
                for payload in workloads:
                    streaming(predicate, payload)
                samples.append((time.perf_counter_ns() - start) / 1e6)
            value, unit = math.ceil(statistics.median(samples)), 'milliseconds'
            details['samples_ms'] = samples
        else:
            tracemalloc.start()
            for payload in workloads:
                streaming(predicate, payload)
            _, value = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            unit = 'bytes'
        details['workload_bytes'] = sum(map(len, workloads))
        details['method'] = 'streaming 65536-byte chunks with unchanged 10079-byte carry; allocations exclude prebuilt input corpus'
    elif args.criterion == 'token-parity':
        probes = [token for token in CTL.CHECKPOINT_ARCHIVE_SECRET_HEADERS[2:]]
        value = all(predicate(token) == CTL._checkpoint_archive_secret_shaped(token) for token in probes)
        details['token_probes'] = len(probes)
    else:
        before = [hashlib.sha256(v).hexdigest() for _, v in positive + negative]
        first = [streaming(predicate, v) for _, v in positive + negative]
        second = [streaming(predicate, v) for _, v in positive + negative]
        after = [hashlib.sha256(v).hexdigest() for _, v in positive + negative]
        value = before == after and first == second
        details['method'] = 'input digests and deterministic repeated pure-scanner result; no native archive recovery claimed'
    report = {'schema': 'protasis-design-report/v1', 'candidate': args.candidate, 'criterion': args.criterion, 'value': value, 'unit': unit, 'command': 'python3 ' + ' '.join([str(Path(__file__).relative_to(ROOT)), *sys.argv[1:]]), 'exit': 0}
    target = ROOT / args.report
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n')
    target.with_suffix('.observation.json').write_text(json.dumps(details, indent=2) + '\n')
    print(json.dumps({'candidate': args.candidate, 'criterion': args.criterion, 'value': value, 'unit': unit, 'report': str(target.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
