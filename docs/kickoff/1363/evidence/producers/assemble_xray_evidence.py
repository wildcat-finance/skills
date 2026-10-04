import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREP = ROOT / '.hexaemeron/xray-preparation'
OUT = ROOT / '.hexaemeron/xray-candidate-bundle'
PINS = {'deployed': 'f5a26146987926f4811b72a795d662813dedfe85', 'candidate': 'bea503c2736d47de7fd34130c64f10783dc35b39'}

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)

def unique(items):
    seen = set()
    out = []
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out

def run():
    linkage = {'schema': 'issue-1363-linkage/v1', 'repository': 'wildcat-finance/v2-protocol', 'producer': '/root',
      'boundary': 'Source-local possible logs on successful paths; conditional joins describe named in-scope callees. Dynamic external implementations remain unresolved. Event absence is not transaction absence; no runtime execution is proved.', 'snapshots': {}}
    sources = {'schema': 'issue-1363-sources/v1', 'repository': 'wildcat-finance/v2-protocol', 'snapshots': {}}
    cross_system = read(PREP / 'cross-system-links.json')
    write(OUT / 'evidence/cross-system-links.json', cross_system)
    for role, commit in PINS.items():
        root = ROOT / '.hexaemeron/sources' / role
        denom = read(PREP / f'{role}-action-denominator.json')
        facts = {kind: read(PREP / f'{role}-{kind}-facts.json') for kind in ('market', 'hooks', 'support', 'library')}
        ast = read(PREP / f'{role}-ast.json')['sources']
        nodes = {n['id']: n for v in ast.values() for n in walk(v['ast']) if 'id' in n}
        srcids = {v['id']: p for p, v in ast.items()}
        content = {p: (root / p).read_bytes() for p in ast}
        contracts = {n['name']: n for n in nodes.values() if n.get('nodeType') == 'ContractDefinition' and n.get('linearizedBaseContracts')}
        joins = cross_system['snapshots'][role]['links']
        for name, expected in cross_system['snapshots'][role]['input_facts_sha256'].items():
            assert hashlib.sha256((PREP / name).read_bytes()).hexdigest() == expected, ('stale cross-system input', role, name)

        def join_refs(action):
            ancestors = {nodes[i]['name'] for i in contracts[action['contract']]['linearizedBaseContracts']}
            branches = '\n'.join(action.get('call_path', []))
            matched = []
            for index, join in enumerate(joins):
                origin = join['from']
                name = origin.get('signature', '').split('(')[0]
                direct = action.get('id') in origin.get('runtime_action_ids', [])
                helper = origin.get('contract') in ancestors and name and re.search(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'\s*(?:\(|\s*->)', branches)
                if direct or helper:
                    matched.append({'id': join['id'], 'pointer': f'evidence/cross-system-links.json#/snapshots/{role}/links/{index}', 'basis': 'exact runtime action ID' if direct else 'declaring ancestor and named helper in retained call branches'})
            return matched

        def source(node):
            off, length, fid = map(int, node['src'].split(':'))
            path = srcids[fid]
            return {'path': path, 'line': content[path][:off].count(b'\n') + 1, 'text': content[path][off:off+length].decode()}

        def abi(t):
            kind = t['nodeType']
            if kind == 'ElementaryTypeName':
                return {'uint': 'uint256', 'int': 'int256', 'address payable': 'address'}.get(t['name'], t['name'])
            if kind == 'UserDefinedTypeName':
                n = nodes[t['referencedDeclaration']]
                if n['nodeType'] == 'ContractDefinition': return 'address'
                if n['nodeType'] == 'EnumDefinition': return 'uint8'
                if n['nodeType'] == 'UserDefinedValueTypeDefinition': return abi(n['underlyingType'])
                if n['nodeType'] == 'StructDefinition': return '(' + ','.join(abi(m['typeName']) for m in n['members']) + ')'
            if kind == 'ArrayTypeName': return abi(t['baseType']) + '[' + (source(t['length'])['text'] if t.get('length') else '') + ']'
            if kind == 'FunctionTypeName': return 'function'
            raise ValueError(t)

        catalog = {}
        byname = collections.defaultdict(dict)
        for n in nodes.values():
            if n.get('nodeType') == 'EventDefinition':
                loc = source(n)
                sig = n['name'] + '(' + ','.join(abi(p['typeName']) for p in n['parameters']['parameters']) + ')'
                topic = '0x' + n['eventSelector']
                event = {'signature': sig, 'topic0': topic, 'source_ref': f"{loc['path']}:{loc['line']}", 'indexed': [p['name'] for p in n['parameters']['parameters'] if p['indexed']]}
                catalog[topic] = event
                byname[n['name']][sig] = event
        write(OUT / 'evidence' / f'{role}-event-catalog.json', sorted(catalog.values(), key=lambda e: e['signature']))

        # Reconcile file coverage against the exact source bytes, not another report list.
        files = []
        all_file_facts = collections.defaultdict(list)
        for kind, data in facts.items():
            for row in data['files']:
                all_file_facts[row['path']].append((kind, row))
        for path in sorted(root.glob('src/**/*.sol')):
            rel = path.relative_to(root).as_posix()
            rows = all_file_facts.pop(rel)
            assert len(rows) == 1, (rel, len(rows))
            kind, row = rows[0]
            raw = path.read_bytes()
            assert row['sha256'] == hashlib.sha256(raw).hexdigest(), rel
            files.append({'path': rel, 'sha256': row['sha256'], 'bytes': len(raw),
                'disposition': row.get('scope_disposition') or row.get('disposition') or 'fresh full source read',
                'source_analysis': f'evidence/{role}-{kind}-facts.json',
                'source_url': f'https://github.com/wildcat-finance/v2-protocol/blob/{commit}/{rel}'})
        assert not all_file_facts
        for dependency in facts['support']['inherited_sources']:
            dependency.update(repository='Vectorized/solady', commit='2ba1cc1eaa3bffd5c093d94f76ef1b87b167ff3c', source_url='https://github.com/Vectorized/solady/blob/2ba1cc1eaa3bffd5c093d94f76ef1b87b167ff3c/' + dependency['path'].removeprefix('lib/solady/'))
        sources['snapshots'][role] = {'commit': commit, 'files': files, 'action_inventory': f'evidence/{role}-action-denominator.json',
            'inherited_dependencies': facts['support']['inherited_sources'],
            'source_scope': 'Every src/**/*.sol file, including interface-only declarations and read-only/internal support. Runtime action denominator excludes libraries, interfaces, pure/view functions and constructors; includes concrete inheritance contexts.'}

        market = facts['market']
        mruntime = {a['id']: a for a in market['runtime_actions']}
        mdirect = {a['source_function']: a for a in market['actions']}
        mfunctions = {f['id']: f for f in market['functions']}
        mcat = {e['emitter']: e for e in market['event_catalog']}
        hooks = {a['id']: a for a in facts['hooks']['actions']}
        support = {a.get('canonical_denominator_id', a.get('id')): a for a in facts['support']['actions']}
        assert set(mruntime) | set(hooks) | set(support) == {a['id'] for a in denom['actions']}
        assert not (set(mruntime) & set(hooks) or set(mruntime) & set(support) or set(hooks) & set(support))
        actions = []
        for d in denom['actions']:
            action = dict(d)
            action['selector'] = '0x' + d['selector']
            action['source_refs'] = [f"{d['source_path']}:{d['line']}"]
            action['parameters'] = [dict(p, trust='user-signed' if d['function'] == 'permit' and p['name'] in ('v','r','s') else 'user-controlled') for p in d['parameters']]
            events = []
            bounds = []
            if d['id'] in mruntime:
                r = mruntime[d['id']]
                a = mdirect[r['source_function']]
                route = market['event_routes'][r['event_route']]
                f = mfunctions.get(r['source_function'], {})
                access = a['access']
                if d['function'] == 'deposit': access = 'permissionless; ' + access
                if d['function'] == 'executePendingAnnualInterestBipsReduction':
                    access = access.replace('APR/reserve hook flag', 'dedicated Bit_Enabled_ExecutePendingAnnualInterestBipsReduction hook flag')
                action.update(access=access, effects=[a['effects']], value_flow=a['value_flow'],
                    call_path=[], reentrancy_guard='nonReentrant' in f.get('modifiers', []) or d['function'] in ('deposit','depositUpTo'),
                    internal_overrides=r['internal_overrides'], evidence_pointer=f'evidence/{role}-market-facts.json#/event_routes/{r["event_route"]}')
                if d['contract'] == 'WildcatMarketConfig' and d['function'] == 'nukeFromOrbit':
                    action['effects'] = ['Accrue and write state, execute configured nuke callback; Base._blockAccount is empty in this runtime, so it does not queue the account balance.']
                if d['contract'] == 'WildcatMarketRevolving':
                    action['effects'].append('Revolving runtime dispatch applies drawn-principal and commitment-fee overrides where this action reaches those helpers; see internal_overrides and event paths.')
                for e in route['events']:
                    cat = mcat.get(e.get('emitter'))
                    if cat:
                        declaration = cat['matching_declarations'][0]
                        signature, topic = declaration['signature'], declaration['topic']
                    else:
                        choices = byname[e['event']]
                        assert len(choices) == 1, e
                        item = next(iter(choices.values())); signature, topic = item['signature'], item['topic0']
                    path = [f"{n.get('function', n.get('call', ''))} @ {n['ref']}" for n in e['call_path']]
                    events.append({'signature': signature, 'topic0': topic, 'emitter': d['contract'], 'source_ref': e.get('emitter', e.get('declaration')),
                        'conditions': e['conditions'], 'call_path': path})
                    action['call_path'].append(' -> '.join(path))
                for b in route['external_event_boundaries']:
                    static = b['call'].lstrip().startswith('staticcall(') or any(q in b['call'] for q in ('.isRegisteredBorrower(', '.resolveBorrower('))
                    bounds.append({'source_ref': b['ref'], 'call': b['call'], 'conditions': b['conditions'],
                        'event_disposition': 'staticcall-no-persisted-logs' if static else 'mutable-call-needs-conditional-callee-join',
                        'call_path': b['call_path']})
                    action['call_path'].append(' -> '.join(n.get('function', n.get('call','')) for n in b['call_path']))
                if not action['call_path']:
                    action['call_path'] = [d['contract'] + '.' + d['signature'] + ' -> ' + a['effects']]
            elif d['id'] in hooks:
                a = hooks[d['id']]
                action.update(access=a['access']['classification'] + ': ' + a['access']['required_caller'] + '; ' + a['access']['reason'],
                    effects=[a['state_effects']], value_flow=a['value_flow'], reentrancy_guard=a['reentrancy_guard'],
                    call_path=[], evidence_pointer=f'evidence/{role}-hooks-facts.json#/actions/{list(hooks).index(d["id"])}')
                for e in a['events']:
                    path = e.get('call_path', [])
                    events.append({'signature': e['event'], 'topic0': e['topic0'], 'emitter': d['contract'],
                        'source_ref': f"{e['source']['path']}:{e['source']['line']}", 'conditions': e.get('conditions', []), 'call_path': path})
                for call in a['call_sites']:
                    path = call.get('call_path', []) + [call['expression']]
                    action['call_path'].append(' -> '.join(path))
                    if call['kind'] == 'external':
                        bounds.append({'source_ref': f"{call['source']['path']}:{call['source']['line']}", 'call': call['expression'],
                            'conditions': call.get('conditions', []), 'event_disposition': 'callee-join-required'})
                for asm in a.get('assembly_evidence', []):
                    if any(re.search(r'\b'+opcode+r'\(', str(asm)) for opcode in ('call','staticcall','create','create2')):
                        bounds.append({'evidence': asm, 'event_disposition': 'assembly-dispatch-needs-callee-join'})
                if not action['call_path']: action['call_path'] = [d['contract'] + '.' + d['signature'] + ' -> ' + a['state_effects']]
            else:
                a = support[d['id']]
                action.update(access=a['access'], effects=a['effects'], value_flow=a['value_flow'],
                    reentrancy_guard=a['non_reentrant'], call_path=a['external_boundary'] or [d['contract']+'.'+d['signature']+' -> '+ '; '.join(a['effects'])],
                    conditions=a['conditions'], caller_checks=a['caller_checks'], evidence_pointer=f'evidence/{role}-support-facts.json#/actions/{list(support).index(d["id"])}')
                for e in a['reachable_local_events']:
                    ev = e['event']
                    events.append({'signature': ev['signature'], 'topic0': ev['topic0'], 'emitter': d['contract'],
                        'source_ref': f"{e['path']}:{e['line']}", 'conditions': [e['condition']] + a['conditions'],
                        'call_path': [d['contract']+'.'+d['signature'], e['reaching_function']]})
                for e in a['assembly_log_sites']:
                    choices = byname.get(e.get('event_name'), {})
                    if len(choices) == 1:
                        ev = next(iter(choices.values()))
                        events.append({'signature': ev['signature'], 'topic0': ev['topic0'], 'emitter': d['contract'],
                            'source_ref': f"{e['path']}:{e['line']}", 'conditions': [e['condition']] + a['conditions'],
                            'call_path': [d['contract']+'.'+d['signature'], e['reaching_function']]})
                    else:
                        bounds.append({'evidence': e, 'event_disposition': 'assembly-topic-resolution-unresolved'})
                if a['external_boundary']:
                    bounds.extend({'call': b, 'event_disposition': 'typed-source-callee-join-required'} for b in a['external_boundary'])
            action['events'] = unique(events)
            action['external_boundaries'] = unique(bounds)
            action['call_path'] = unique(action['call_path'])
            action['conditional_cross_system_links'] = join_refs(action)
            # Review joins refine this conservative local disposition.
            unresolved = any(b['event_disposition'] != 'staticcall-no-persisted-logs' for b in bounds)
            action['disposition'] = 'unresolved' if unresolved else ('events' if events else 'eventless')
            action['reason'] = ('Known local possible events are retained; conditional_cross_system_links joins named callees where resolved. Dynamic implementations and other external paths remain unresolved; configured addresses are not proved to contain these source implementations.' if unresolved else
                'Listed local events occur only on successful paths satisfying the recorded conditions; reverted logs do not persist.' if events else
                'The reviewed body and local helper paths emit no persistent event. This is a source-local disposition, not an inference that no transaction occurred.')
            actions.append(action)
        initialization = [dict(i, source_refs=[f"{i['source_path']}:{i['line']}"], disposition='constructor; excluded from runtime action denominator; inherited base constructors run in Solidity order') for i in denom['initialization']]
        linkage['snapshots'][role] = {'commit': commit, 'actions': actions, 'initialization': initialization,
            'cross_system_catalog': f'evidence/cross-system-links.json#/snapshots/{role}',
            'join_boundary': 'Local events and conditional callee event profiles remain separate. Linked records state call opcode, caller identity, conditions and arbitrary-target unknowns. The complete catalog also covers constructors and external provider callers.'}
        write(OUT / 'evidence' / f'{role}-normalization-notes.json', {'producer': '/root', 'role': role,
            'corrections': ['STATICCALL boundaries cannot persist logs; raw market extraction used an overbroad external-event placeholder.', 'Queue callback effects include FixedTerm maturity and PeriodicTerm window restrictions; failed credential validation cannot persist clearing after the outer revert.', 'Concrete inheritance contexts remain distinct even where they share a selector.', 'All runtime action IDs reconciled exactly against the independent immutable denominator.'],
            'counts': {'files': len(files), 'actions': len(actions), 'initialization': len(initialization)}})
        print(role, len(files), len(actions), collections.Counter(a['disposition'] for a in actions))
    write(OUT / 'sources.json', sources)
    write(OUT / 'linkage.json', linkage)

if __name__ == '__main__':
    run()
