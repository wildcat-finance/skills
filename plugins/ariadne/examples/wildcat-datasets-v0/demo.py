#!/usr/bin/env python3
"""Bind the two accepted Wildcat releases through Ariadne's dataset caller API."""

import argparse
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from unittest.mock import patch

EXAMPLE = Path(__file__).resolve().parent
sys.path.insert(0, str(EXAMPLE.parents[1] / 'scripts'))
from ariadne_lib import envelope, registry, safejson, verify as verifier  # noqa: E402
from ariadne_lib.capture import dataset  # noqa: E402

METADATA_SHA256 = '95fe70b1ffc78e55fb4f2e7c92915d47504e8e2d05350819fbc54c4df24e314a'
METADATA_LIMIT = 1048576
COMPONENT_LIMIT = 64 * 1024 * 1024
OUTPUT_LIMIT = 8 * 1024 * 1024
SELECTORS = {'/records', '/epochs', '/shards', '/entries'}
GAP_REASON = (
    'Conservative whole-interval projection of semantic omissions in the bound '
    'source inventory: targeted traces exclude transactions without matching '
    'subject logs; deployment blocks and credit interpretations remain limited. '
    'All source gaps, unsupported collections and partition notes remain in '
    'coverage.json. This does not mean blocks were unread or turn partition '
    'notes into missing intervals.'
)
BOUNDARY = (
    'Python socket construction and connection helpers were denied during this '
    'local adapter execution; zero attempted calls were observed. This is not '
    'an operating-system sandbox, syscall trace or claim about native code, '
    'other processes, archive access or the original collection.'
)


class DemoError(ValueError):
    """A refused input or result, with the failed relation named."""


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(value, *, directory=False, fresh=False):
    """Reject symlinks and lexical traversal before any file is opened."""
    path = Path(value)
    if '..' in path.parts:
        raise DemoError('unsafe path traversal')
    path = Path(os.path.abspath(path))
    for ancestor in reversed((path,) + tuple(path.parents)):
        if ancestor.is_symlink():
            raise DemoError('unsafe symlink path')
    if fresh:
        if path.exists():
            raise DemoError('output destination already exists')
        safe_path(path.parent, directory=True)
    else:
        mode = path.stat().st_mode
        if not (stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)):
            raise DemoError('path is not a ' + ('directory' if directory else 'regular file'))
    return path


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise DemoError('unsafe relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(x in ('', '.', '..') for x in value.split('/')):
        raise DemoError('unsafe relative path')
    return path


def read_bytes(path, limit):
    path = safe_path(path)
    if path.stat().st_size > limit:
        raise DemoError('file exceeds byte limit')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise DemoError('file exceeds byte limit')
    return raw


def read_json(raw):
    return safejson.loads(raw.decode('utf-8'), max_bytes=max(len(raw), 1), max_depth=100)


def digest_file(path, expected_size):
    if type(expected_size) is not int or not 0 <= expected_size <= COMPONENT_LIMIT:
        raise DemoError('component size outside source cap')
    path = safe_path(path)
    if path.stat().st_size != expected_size:
        raise DemoError('release file size mismatch')
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            size += len(block)
            if size > expected_size:
                raise DemoError('release file size changed')
            digest.update(block)
    if size != expected_size:
        raise DemoError('release file size changed')
    return digest.hexdigest()


def metadata_document(reference, base=EXAMPLE):
    for field in ('bytes', 'encoded_bytes'):
        if type(reference[field]) is not int or not 0 < reference[field] <= METADATA_LIMIT:
            raise DemoError('metadata size exceeds limit')
    raw = read_bytes(base / relative(reference['path']), reference['encoded_bytes'])
    if len(raw) != reference['encoded_bytes'] or sha(raw) != reference['encoded_sha256']:
        raise DemoError('encoded metadata mismatch')
    if reference['encoding'] != 'gzip':
        raise DemoError('unsupported metadata encoding')
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        decoded = stream.read(reference['bytes'] + 1)
    if len(decoded) != reference['bytes'] or sha(decoded) != reference['sha256']:
        raise DemoError('decoded metadata mismatch')
    return read_json(decoded)


def load_inputs(base=EXAMPLE):
    raw = read_bytes(base / 'inputs.json', METADATA_LIMIT)
    if sha(raw) != METADATA_SHA256:
        raise DemoError('accepted inputs identity mismatch')
    metadata = read_json(raw)
    expected = {row['path'] for row in metadata['files']}
    actual = set()
    for name in ('inputs', 'spec'):
        actual.update(name + '/' + rel for rel, _ in dataset.files(str(safe_path(base / name, directory=True))))
    if actual != expected:
        raise DemoError('preserved metadata inventory mismatch')
    for row in metadata['files']:
        if digest_file(base / relative(row['path']), row['bytes']) != row['sha256']:
            raise DemoError('preserved metadata digest mismatch')
    for estate in metadata['estates']:
        for value in estate.values():
            if isinstance(value, dict) and value.get('encoding') == 'gzip':
                metadata_document(value, base)
    return metadata


def release_rows(estate, manifest):
    if manifest['release_id'] != estate['release_id']:
        raise DemoError('release identity mismatch')
    components = manifest['components']
    if len(components) + 1 != estate['subjects']:
        raise DemoError('subject inventory count mismatch')
    rows = [{'path': 'manifest.json', 'sha256': estate['manifest']['sha256'],
             'bytes': estate['manifest']['bytes'], 'record_count': 1, 'selector': 'metadata-document'}]
    captures = {c['component']: c for c in manifest['captures']}
    if len(captures) != len(manifest['captures']) or set(captures) != {c['name'] for c in components}:
        raise DemoError('capture component inventory mismatch')
    for component in components:
        path = str(relative(component['object_path']))
        digest = component['sha256'].removeprefix('sha256:')
        if len(digest) != 64 or any(x not in '0123456789abcdef' for x in digest):
            raise DemoError('invalid component digest')
        if path != 'objects/sha256/' + digest[:2] + '/' + digest:
            raise DemoError('component path and digest mismatch')
        capture = captures[component['name']]
        coverage = capture['coverage']
        collections = coverage['collections']
        if len(collections) != 1 or collections[0]['selector'] not in SELECTORS:
            raise DemoError('unsupported count selector')
        collection = collections[0]
        count = collection['record_count']
        if type(count) is not int or count < 0 or count != coverage['record_count']:
            raise DemoError('conflicting record counts')
        if capture['component_sha256'] != component['sha256']:
            raise DemoError('capture component digest mismatch')
        rows.append({'path': path, 'sha256': digest, 'bytes': component['bytes'],
                     'record_count': count, 'selector': collection['selector']})
    if len({r['path'] for r in rows}) != len(rows):
        raise DemoError('duplicate release file')
    if sum(r['bytes'] for r in rows) != estate['release_bytes']:
        raise DemoError('release byte inventory mismatch')
    return sorted(rows, key=lambda r: r['path'])


def check_release(root, rows):
    root = safe_path(root, directory=True)
    if [r for r, _ in dataset.files(str(root))] != [r['path'] for r in rows]:
        raise DemoError('release file inventory mismatch')
    for row in rows:
        path = root / relative(row['path'])
        if digest_file(path, row['bytes']) != row['sha256']:
            raise DemoError('release file digest mismatch')
        if row['selector'] != 'metadata-document':
            document = read_json(read_bytes(path, COMPONENT_LIMIT))
            selected = document.get(row['selector'][1:])
            if not isinstance(selected, list) or len(selected) != row['record_count']:
                raise DemoError('selector record count mismatch')
    return root


def inventory_documents(metadata, estate, manifest, rows):
    return {
        'inventory.json': {'estate': estate['estate'], 'release_id': estate['release_id'],
                           'file_subjects': estate['subjects'], 'files': rows},
        'coverage.json': {'estate': estate['estate'], 'interval': estate['interval'],
                          'projection_reason': GAP_REASON, 'captures': manifest['captures'],
                          'components': manifest['components']},
        'provenance.json': {'estate': estate, 'producer_sources': metadata['producer_sources'],
                            'source_revision': metadata['source_revision'],
                            'signature_status': 'unsigned',
                            'boundary': 'Observed offline rebuild provenance; historical collection remains separate.'},
    }


def input_entries(metadata, estate, docs):
    entries = []
    for name, doc in sorted(docs.items()):
        entries.append({'name': name, 'locator': 'wildcat-example://' + estate['estate'] + '/' + name,
                        'digest': {'sha256': sha(encoded(doc))}})
    for field, ref in sorted(estate.items()):
        if isinstance(ref, dict) and ref.get('encoding') == 'gzip':
            entries.append({'name': field, 'locator': 'wildcat-example://' + ref['path'],
                            'digest': {'sha256': ref['sha256']}})
    entries.append({'name': 'preserved staging archive', 'locator': estate['archive']['location'],
                    'digest': {'sha256': estate['archive']['sha256']}})
    for row in metadata['producer_sources']:
        entries.append({'name': row['path'], 'locator': 'git:' + metadata['source_revision'] + ':' + row['path'],
                        'digest': {'sha256': row['sha256']}})
    return entries


def report_for(statement):
    report = verifier.report(envelope.read(encoded(statement)), registry.DEFAULT)
    if len(report.ordered) != 10 or sorted(g.number for g in report.gates if g.number) != list(range(1, 8)):
        raise DemoError('verifier gate inventory mismatch')
    return report


def coverage_mutation(statement, mutation):
    candidate = copy.deepcopy(statement)
    coverage = candidate['predicate']['coverage']
    if mutation == 'missing-gap':
        del coverage['gaps']
    elif mutation == 'missing-reason':
        del coverage['gaps'][0]['reason']
    elif mutation == 'outside-bound':
        coverage['gaps'][0]['end'] = coverage['end'] + 1
    else:
        raise DemoError('unknown mutation')
    return candidate


def statement_outputs(statement):
    report = report_for(statement)
    if not report.ok or report.unchecked or report.document.signed:
        raise DemoError('statement did not pass every unsigned verifier gate')
    outputs = {'statement.json': encoded(statement), 'verify.json': encoded(report.to_dict()),
               'verify.txt': ('\n'.join(report.lines()) + '\n').encode()}
    for mutation in ('missing-gap', 'missing-reason', 'outside-bound'):
        result = report_for(coverage_mutation(statement, mutation))
        failed = [g.name for g in result.gates if not g.passed]
        if result.ok or failed != ['coverage']:
            raise DemoError('coverage mutation was not refused by coverage')
        outputs['refusals/' + mutation + '.json'] = encoded(result.to_dict())
        outputs['refusals/' + mutation + '.txt'] = ('\n'.join(result.lines()) + '\n').encode()
    return outputs


def build_estate(metadata, estate, root):
    manifest = metadata_document(estate['manifest'])
    rows = release_rows(estate, manifest)
    root = check_release(root, rows)
    docs = inventory_documents(metadata, estate, manifest, rows)
    observed = estate['observed_rebuild']
    start, end = (int(estate['interval'][x]) for x in ('start', 'end'))
    statement = dataset.capture(
        str(root), 'wildcat-' + estate['estate'] + '-full-release', 'block', start, end,
        'alexandria', 'source:' + observed['runtime_commit'] + ';python:' + observed['python'],
        observed['argv'], gaps=[{'start': start, 'end': end, 'reason': GAP_REASON}],
        inputs=input_entries(metadata, estate, docs),
        parameters={'environment': observed['environment'], 'runtime_commit': observed['runtime_commit']},
        record_counts={r['path']: r['record_count'] for r in rows},
        first_release_reason='First Ariadne statement for this accepted Wildcat ' + estate['estate'] +
        ' estate. No previous statement is supplied; V1 and V2 are separate estates, not a baseline pair.',
    )
    # Recheck the external tree after capture: this observes drift, not an atomic snapshot.
    check_release(root, rows)
    outputs = {name: encoded(doc) for name, doc in docs.items()}
    outputs.update(statement_outputs(statement))
    return outputs


def observed_outputs(metadata, roots):
    attempts = []
    def deny(*args, **kwargs):
        attempts.append('socket attempt')
        raise DemoError('socket use refused during offline observation')
    outputs = {}
    with patch('socket.socket', deny), patch('socket.create_connection', deny), patch('socket.socketpair', deny):
        for estate in metadata['estates']:
            for name, raw in build_estate(metadata, estate, roots[estate['estate']]).items():
                outputs[estate['estate'] + '/' + name] = raw
    if attempts:
        raise DemoError('socket attempt observed')
    outputs['observation.json'] = encoded({'schema': 'wildcat-dataset-observation/v1',
                                          'socket_attempts': len(attempts), 'boundary': BOUNDARY})
    return outputs


def release_roots(metadata):
    roots = {}
    for estate in metadata['estates']:
        value = os.environ.get(estate['release_environment'])
        if not value:
            raise DemoError('required external release environment: ' + estate['release_environment'])
        roots[estate['estate']] = safe_path(value, directory=True)
    if roots['v1'] == roots['v2']:
        raise DemoError('release roots alias')
    return roots


def write_outputs(output, outputs):
    output = safe_path(output, fresh=True)
    output.mkdir()
    for name, raw in sorted(outputs.items()):
        path = output / relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        safe_path(path.parent, directory=True)
        with path.open('xb') as stream:
            stream.write(raw)
    # An interrupted run may leave this new directory incomplete; never replace it.


def compare_outputs(output, expected):
    output = safe_path(output, directory=True)
    if {r for r, _ in dataset.files(str(output))} != set(expected):
        raise DemoError('output inventory mismatch')
    for name, raw in expected.items():
        if read_bytes(output / relative(name), OUTPUT_LIMIT) != raw:
            raise DemoError('output content mismatch: ' + name)


def preserved_outputs(metadata):
    """Replay statements against pinned metadata without claiming external file reads."""
    outputs = {}
    for estate in metadata['estates']:
        prefix = estate['estate'] + '/'
        manifest = metadata_document(estate['manifest'])
        rows = release_rows(estate, manifest)
        docs = inventory_documents(metadata, estate, manifest, rows)
        raw = read_bytes(EXAMPLE / 'preserved' / prefix / 'statement.json', OUTPUT_LIMIT)
        statement = read_json(raw)
        body = statement['predicate']
        if set(statement) != {'_type', 'subject', 'predicateType', 'predicate'} or set(body) != {
                'producer', 'inputs', 'dataset_subjects', 'coverage', 'deltas', 'claims', 'commands'}:
            raise DemoError('preserved statement shape mismatch')
        if statement['_type'] != 'https://in-toto.io/Statement/v1' or statement['predicateType'] != dataset.predicate.TYPE:
            raise DemoError('preserved statement type mismatch')
        subjects = [{'name': r['path'], 'path': r['path'], 'digest': {'sha256': r['sha256']},
                     'record_count': r['record_count']} for r in rows]
        if body['dataset_subjects'] != subjects or body['inputs'] != input_entries(metadata, estate, docs):
            raise DemoError('preserved statement subject or input inventory mismatch')
        expected_claims = [dataset.claim(
            'digest and record count read from the released file', subject['digest'], 'passed',
            detail='%s, %d record(s)' % (subject['path'], subject['record_count'])) for subject in subjects]
        if body['claims'] != expected_claims or body['commands'] != []:
            raise DemoError('preserved claims or commands mismatch')
        observed = estate['observed_rebuild']
        producer = {'tool': 'alexandria',
                    'tool_version': 'source:' + observed['runtime_commit'] + ';python:' + observed['python'],
                    'command': observed['argv'],
                    'parameters_digest': dataset.parameters_digest({'environment': observed['environment'],
                                                                    'runtime_commit': observed['runtime_commit']})}
        if body['producer'] != producer:
            raise DemoError('preserved producer mismatch')
        start, end = (int(estate['interval'][x]) for x in ('start', 'end'))
        if body['coverage'] != {'dimension': 'block', 'start': start, 'end': end,
                               'gaps': [{'start': start, 'end': end, 'reason': GAP_REASON}]}:
            raise DemoError('preserved coverage mismatch')
        name = 'wildcat-' + estate['estate'] + '-full-release'
        bundle = dataset.bundle(subjects)
        if statement['subject'] != [{'name': r['name'], 'digest': r['digest']} for r in subjects] + [{'name': name, 'digest': bundle}]:
            raise DemoError('preserved outer subject mismatch')
        if body['deltas'] != {'baseline': None, 'current': {'name': name, 'digest': bundle},
                             'reason': 'First Ariadne statement for this accepted Wildcat ' + estate['estate'] +
                             ' estate. No previous statement is supplied; V1 and V2 are separate estates, not a baseline pair.'}:
            raise DemoError('preserved first-release boundary mismatch')
        for filename, value in docs.items():
            outputs[prefix + filename] = encoded(value)
        outputs.update({prefix + filename: value for filename, value in statement_outputs(statement).items()})
    outputs['observation.json'] = read_bytes(EXAMPLE / 'preserved/observation.json', OUTPUT_LIMIT)
    if read_json(outputs['observation.json']) != {'schema': 'wildcat-dataset-observation/v1', 'socket_attempts': 0, 'boundary': BOUNDARY}:
        raise DemoError('preserved observation mismatch')
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('build', 'verify'):
        sub.add_parser(name).add_argument('--output', required=True)
    sub.add_parser('verify-preserved')
    args = parser.parse_args(argv)
    metadata = load_inputs()
    if args.command == 'verify-preserved':
        compare_outputs(EXAMPLE / 'preserved', preserved_outputs(metadata))
        print('Preserved statements and reports verified against exact metadata; no external release read, new rebuild or socket observation.')
    else:
        roots = release_roots(metadata)
        output = safe_path(args.output, fresh=args.command == 'build', directory=args.command == 'verify')
        if any(output == root or output in root.parents or root in output.parents for root in roots.values()):
            raise DemoError('input/output alias or containment refused')
        expected = observed_outputs(metadata, roots)
        if args.command == 'build':
            write_outputs(output, expected)
        else:
            compare_outputs(output, expected)
        print('Both real releases checked; V1 110 files / 111 outer subjects; V2 128 files / 129 outer subjects.')
        print('Each unsigned statement: seven gates and three dataset checks passed; three coverage mutations refused.')
        print(BOUNDARY)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (DemoError, OSError, ValueError, KeyError, TypeError) as error:
        print('Wildcat dataset demo refused: ' + str(error), file=sys.stderr)
        sys.exit(1)
