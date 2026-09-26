from pathlib import Path
import difflib
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / 'xray-candidate-bundle'
ROLES = {'deployed': 'f5a26146987926f4811b72a795d662813dedfe85', 'candidate': 'bea503c2736d47de7fd34130c64f10783dc35b39'}
failures = []
result = {}

def check(ok, message):
    if not ok:
        failures.append(message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def pointer(ref):
    path, fragment = ref.split('#', 1)
    value = read(BUNDLE / path)
    for piece in fragment.lstrip('/').split('/'):
        piece = piece.replace('~1', '/').replace('~0', '~')
        value = value[int(piece)] if isinstance(value, list) else value[piece]
    return value

def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)

linkage = read(BUNDLE / 'linkage.json')
sources = read(BUNDLE / 'sources.json')
cross = read(BUNDLE / 'evidence/cross-system-links.json')
topics = set()

for role, pin in ROLES.items():
    root = ROOT / 'sources' / role
    check(subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip() == pin, role + ': source HEAD')
    denominator = read(BUNDLE / ('evidence/' + role + '-action-denominator.json'))
    actions = {a['id']: a for a in linkage['snapshots'][role]['actions']}
    denoms = {a['id']: a for a in denominator['actions']}
    check(len(actions) == len(linkage['snapshots'][role]['actions']), role + ': unique normalized IDs')
    check(len(denoms) == len(denominator['actions']), role + ': unique denominator IDs')
    check(actions.keys() == denoms.keys(), role + ': exact denominator action IDs')
    astpath = ROOT / 'xray-preparation' / (role + '-ast.json')
    check(digest(astpath) == denominator['ast_sha256'], role + ': AST hash')
    ast = read(astpath)
    paths = {s['id']: p for p, s in ast['sources'].items()}
    contracts = {}
    allnodes = {}
    for path, src in ast['sources'].items():
        for node in walk(src['ast']):
            if 'id' in node:
                allnodes[node['id']] = node
            if node.get('nodeType') == 'ContractDefinition':
                contracts[node['id']] = (path, node)
    independent = {}
    for path, contract in contracts.values():
        if not path.startswith('src/') or contract['contractKind'] != 'contract' or contract['abstract']:
            continue
        selected = {}
        for baseid in contract['linearizedBaseContracts']:
            for node in contracts[baseid][1]['nodes']:
                selector = node.get('functionSelector')
                if selector and selector not in selected:
                    selected[selector] = node
        for selector, node in selected.items():
            if node['nodeType'] != 'FunctionDefinition' or node['stateMutability'] in ('view', 'pure'):
                continue
            independent[(contract['name'], selector)] = node
    recorded = {(a['contract'], a['selector'].removeprefix('0x')): a for a in denominator['actions']}
    check(independent.keys() == recorded.keys(), role + ': independent C3/selector action denominator')
    implementation_ids = set()
    for key, node in independent.items():
        a = recorded[key]
        start, length, sourceid = map(int, node['src'].split(':'))
        path = paths[sourceid]
        raw = (root / path).read_bytes()
        check(a['source_path'] == path, role + ': source path ' + a['id'])
        check(a['line'] == raw[:start].count(b'\n') + 1, role + ': source line ' + a['id'])
        check(a['body_sha256'] == hashlib.sha256(raw[start:start+length]).hexdigest(), role + ': function bytes ' + a['id'])
        implementation_ids.add(node['id'])
    srcs = sources['snapshots'][role]
    tracked = set(subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '--name-only', 'HEAD', 'src'], text=True).splitlines())
    tracked = {p for p in tracked if p.endswith('.sol')}
    check(tracked == {f['path'] for f in srcs['files']}, role + ': complete tracked source inventory')
    for row in srcs['files'] + srcs['inherited_dependencies']:
        path = root / row['path']
        check(digest(path) == row['sha256'] and path.stat().st_size == row['bytes'], role + ': source bytes ' + row['path'])
    for row in srcs['inherited_dependencies']:
        check(row['commit'] == '2ba1cc1eaa3bffd5c093d94f76ef1b87b167ff3c' and row['repository'] == 'Vectorized/solady', role + ': dependency source URL')
    guards = read(BUNDLE / ('evidence/' + role + '-guards.json'))['guards']
    for g in guards:
        fragment = '\n'.join((root / g['path']).read_text().splitlines()[g['line']-1:g['end_line']])
        check(g['text'] in fragment, role + ': guard source ' + g['id'])
    crossrole = cross['snapshots'][role]
    for name, sha in crossrole['input_facts_sha256'].items():
        check(digest(BUNDLE / 'evidence' / name) == sha, role + ': cross input ' + name)
    for path, sha in crossrole['referenced_source_sha256'].items():
        check(digest(root / path) == sha, role + ': cross source ' + path)
    for a in actions.values():
        original = pointer(a['evidence_pointer'])
        if '/event_routes/' in a['evidence_pointer']:
            check(original['selector'] == a['selector'] and original['source'] == a['source_path'] + ':' + str(a['line']), role + ': event-route pointer ' + a['id'])
        else:
            check(a['id'] in [original.get(k) for k in ('id', 'canonical_denominator_id')], role + ': fact pointer ' + a['id'])
        check(a['body_sha256'] == denoms[a['id']]['body_sha256'], role + ': normalized body binding ' + a['id'])
        for ref in a.get('conditional_cross_system_links', []):
            check(pointer(ref['pointer'])['id'] == ref['id'], role + ': conditional pointer ' + a['id'])
        for event in a['events']:
            topics.add((event['signature'], event['topic0']))
    for name, profile in crossrole['callback_profiles'].items():
        check({e['signature'] for e in actions[name]['events']} == {e['signature'] for e in profile['possible_events']}, role + ': callback profile/local event-set match ' + name)
        for event in profile['possible_events']:
            topics.add((event['signature'], event['topic0']))
    report = (BUNDLE / role / 'entry-points.md').read_text()
    check(all(a in report for a in actions), role + ': entry-point report ID coverage')
    check(not re.search(r'https://github.com/wildcat-finance/v2-protocol/blob/[^/)]+/lib/solady/', report), role + ': no gitlink-as-directory URL')
    result[role] = {'source_commit': pin, 'independent_compiler_actions': len(independent), 'unique_implementations': len(implementation_ids), 'source_files': len(srcs['files']), 'inherited_dependencies': len(srcs['inherited_dependencies']), 'guard_predicates': len(guards), 'callback_profiles': len(crossrole['callback_profiles']), 'action_cross_references': sum(len(a.get('conditional_cross_system_links', [])) for a in actions.values()), 'reviewed_actions': sorted(actions)}

expected_diff = ''.join(difflib.unified_diff((BUNDLE / 'deployed/entry-points.md').read_text().splitlines(keepends=True), (BUNDLE / 'candidate/entry-points.md').read_text().splitlines(keepends=True), fromfile='deployed/entry-points.md', tofile='candidate/entry-points.md'))
check((BUNDLE / 'entry-points.diff').read_text() == expected_diff, 'literal entry-points diff')
for signature, topic in topics:
    actual = subprocess.check_output([shutil.which('cast'), 'keccak', signature], text=True).strip()
    check(actual.lower() == topic.lower(), 'event topic ' + signature)

output = {'schema': 'issue-1363-final-review-checks/v1', 'reviewer': '/root/xray_1363_artifact_review', 'status': 'passed' if not failures else 'findings', 'roles': result, 'unique_event_topics': len(topics), 'failures': failures, 'boundary': 'Independent source-byte, compiler-denominator and artifact reconciliation. Does not prove runtime execution or complete security coverage.'}
(ROOT / 'xray-final-review-checks.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps({'status': output['status'], 'roles': {r: {k:v for k,v in d.items() if k != 'reviewed_actions'} for r,d in result.items()}, 'unique_event_topics': len(topics), 'failures': failures}, indent=2))
