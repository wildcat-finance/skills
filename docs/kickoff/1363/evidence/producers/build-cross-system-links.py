"""Encode the source-reviewed inter-contract boundaries for issue 1363."""
import hashlib
import json
import re
from pathlib import Path

P = Path('.hexaemeron/xray-preparation')
ROOT = Path('.hexaemeron/sources')


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


out = {
    'schema': 'issue-1363-cross-system-links/v1',
    'producer': '/root/xray_support',
    'evidence_kind': 'pinned source reasoning; no runtime or test observation',
    'semantics': [
        'Each link names a source call boundary, not proof that an on-chain address executes the pinned target.',
        'Events are possible successful-path emissions with explicit conditions; all enclosing calls and the transaction must succeed.',
        'Reverting child calls retain no logs. A caught failed child call also retains no child logs.',
        'STATICCALL and its descendants cannot persist logs or writes, even for an arbitrary target. Their return data and availability remain external assumptions.',
        'Mutable CALL to arbitrary ERC20, hook, provider, provider factory or SphereX code has unresolved event effects.',
        'Constructors reached through stored initcode are conditional on that stored bytecode matching the named pinned implementation.',
        'A locally eventless action may still reach eventful mutable calls. Profile references below compose conditionally, not as unconditional unions.',
    ],
    'snapshots': {},
}

for role in ('deployed', 'candidate'):
    ast = json.loads((P / f'{role}-ast.json').read_text())
    nodes = {n['id']: n for n in walk(ast) if 'nodeType' in n and 'id' in n}
    paths = {s['id']: path for path, s in ast['sources'].items()}
    sources = {path: (ROOT / role / path).read_bytes() for path in paths.values()}
    contracts, functions = {}, {}
    for path, unit in ast['sources'].items():
        for contract in unit['ast']['nodes']:
            if contract['nodeType'] == 'ContractDefinition':
                contracts[contract['name']] = contract
                for function in contract['nodes']:
                    if function['nodeType'] == 'FunctionDefinition':
                        functions.setdefault((contract['name'], function['name'] or function['kind']), []).append(function)
            elif contract['nodeType'] == 'FunctionDefinition':
                functions.setdefault(('<free>', contract['name']), []).append(contract)
    denominator = json.loads((P / f'{role}-action-denominator.json').read_text())
    hookfacts = json.loads((P / f'{role}-hooks-facts.json').read_text())
    marketfacts = json.loads((P / f'{role}-market-facts.json').read_text())
    supportfacts = json.loads((P / f'{role}-support-facts.json').read_text())
    used_paths = set()

    def text(node):
        offset, length, source_id = map(int, node['src'].split(':'))
        return sources[paths[source_id]][offset:offset + length].decode()

    def ref(node):
        offset, length, source_id = map(int, node['src'].split(':'))
        path = paths[source_id]
        used_paths.add(path)
        return {'path': path, 'line': sources[path][:offset].count(b'\n') + 1, 'src': node['src'], 'ast_id': node['id']}

    def typ(t):
        kind = t['nodeType']
        if kind == 'ElementaryTypeName':
            return {'uint': 'uint256', 'int': 'int256', 'byte': 'bytes1', 'address payable': 'address'}.get(t['name'], t['name'])
        if kind == 'ArrayTypeName':
            return typ(t['baseType']) + '[' + (t['length']['value'] if t.get('length') else '') + ']'
        if kind == 'UserDefinedTypeName':
            node = nodes[t['referencedDeclaration']]
            if node['nodeType'] == 'UserDefinedValueTypeDefinition':
                return typ(node['underlyingType'])
            if node['nodeType'] == 'ContractDefinition':
                return 'address'
            if node['nodeType'] == 'EnumDefinition':
                return 'uint8'
            if node['nodeType'] == 'StructDefinition':
                return '(' + ','.join(typ(m['typeName']) for m in node['members']) + ')'
        if kind == 'FunctionTypeName':
            return 'function'
        raise ValueError(t)

    def sig(node):
        return (node['name'] or node['kind']) + '(' + ','.join(typ(x['typeName']) for x in node['parameters']['parameters']) + ')'

    def fn(contract, name, count=None):
        found = functions[(contract, name)]
        if count is not None:
            found = [f for f in found if len(f['parameters']['parameters']) == count]
        assert len(found) == 1, (role, contract, name, len(found))
        return found[0]

    def fr(contract, name, count=None):
        function = fn(contract, name, count)
        r = ref(function)
        return {'contract': contract, 'signature': sig(function), 'function_id': contract + ':' + sig(function),
                'selector': '0x' + function['functionSelector'] if function.get('functionSelector') else None,
                'source': r, 'runtime_action_ids': [a['id'] for a in denominator['actions'] if a['source_path'] == r['path'] and a['line'] == r['line']]}

    def sites(contract, name, needle, count=None):
        function = fn(contract, name, count)
        start = ref(function)
        return [{'path': start['path'], 'line': start['line'] + index, 'expression': line.strip()}
                for index, line in enumerate(text(function).splitlines()) if needle in line]

    eventnodes = {}
    for n in nodes.values():
        if n['nodeType'] == 'EventDefinition':
            eventnodes.setdefault(n['name'], []).append(n)

    def ev(name, condition, emitter_contract, emitter_function, count=None, declaration_path=None):
        candidates = eventnodes[name]
        if declaration_path:
            candidates = [e for e in candidates if ref(e)['path'] == declaration_path]
        signatures = {sig(e) for e in candidates}
        assert len(signatures) == 1, (role, name, signatures)
        node = candidates[0]
        declaration = ref(node)
        return {'signature': sig(node), 'topic0': '0x' + node['eventSelector'], 'declaration': declaration,
                'condition': condition, 'emitter': fr(emitter_contract, emitter_function, count),
                'emission_sites': sites(emitter_contract, emitter_function, name, count)}

    def market_ev(name, condition, contract, function):
        result = ev(name, condition, contract, function)
        entries = [e for e in marketfacts['event_catalog'] if e['name'] == name]
        result['assembly_emitter_catalog'] = entries
        return result

    profiles = {}
    links = []
    absences = []
    is_candidate = role == 'candidate'
    hooktypes = ['OpenTermHooks', 'FixedTermHooks'] + (['PeriodicTermHooks'] if is_candidate else [])
    markettypes = ['WildcatMarket'] + (['WildcatMarketRevolving'] if is_candidate else [])

    def add(contract, function, target, condition, caller, events=None, **extra):
        source = fr(contract, function, extra.pop('source_parameter_count', None))
        row = {'id': role + ':' + source['function_id'] + ' -> ' + target,
               'from': source, 'target': target, 'condition': condition, 'callee_msg_sender': caller,
               'possible_events': events or [], **extra}
        links.append(row)
        return row

    # Concrete callback profiles are source-reviewed. In particular, queue withdrawal cannot
    # retain an access-revocation log because missing access reverts the outer callback.
    for hook in hooktypes:
        for name in [n for (c, n) in functions if c == hook and n.startswith('on')]:
            profile = {'id': hook + ':' + sig(fn(hook, name)), 'target_function': fr(hook, name),
                       'condition': 'Configured hooks address executes this pinned concrete implementation; callback gate and enclosing transaction succeed.',
                       'possible_events': [], 'external_event_effects': []}
            events = profile['possible_events']
            if name in ('onDeposit', 'onTransfer', 'onQueueWithdrawal'):
                prefix = 'Access validation reached; '
                if name == 'onTransfer':
                    prefix += 'recipient is not already known' + (' and is not the registered wrapper' if is_candidate else '') + '; '
                if name == 'onQueueWithdrawal':
                    prefix += 'lender is not already known; withdrawal access check enabled where optional; '
                events.append(ev('AccountAccessGranted', prefix + 'credential was updated and remains valid', 'BaseAccessControls', '_writeLenderStatus'))
                if name != 'onQueueWithdrawal':
                    events.append(ev('AccountAccessRevoked', prefix + 'old credential removed; no replacement; this market does not require credential for the action', 'BaseAccessControls', '_writeLenderStatus'))
                    events.append(ev('AccountMadeFirstDeposit', prefix + 'valid credential; account was not previously known on this market', 'BaseAccessControls', '_writeLenderStatus'))
                profile['external_event_effects'] = ['getCredential uses STATICCALL: no persisted callee logs.', 'validateCredential uses mutable CALL for an applicable hooksData suffix: arbitrary provider event effects unresolved; failed calls retain no logs.']
            elif name == 'onCloseMarket' and hook == 'FixedTermHooks':
                events.append(ev('FixedTermUpdated', 'Before fixed-term end and early closure or term reduction allowed', hook, name))
            elif name == 'onCloseMarket' and hook == 'PeriodicTermHooks':
                events.append(ev('AnnualInterestBipsReductionProposalCancelled', 'Pending APR proposal exists', hook, name))
                events.append(ev('PeriodicTermClosed', 'Registered hooked market and successful close', hook, name))
            elif name == 'onSetAnnualInterestAndReserveRatioBips':
                parent_events = [
                    ('TemporaryExcessReserveRatioExpired', 'temporary ratio exists; proposed APR is at least current APR and expiry has passed'),
                    ('TemporaryExcessReserveRatioCanceled', 'temporary ratio exists; expiry branch false; proposed APR is at least original APR'),
                    ('TemporaryExcessReserveRatioActivated', 'proposed APR below original; no existing temporary ratio'),
                    ('TemporaryExcessReserveRatioUpdated', 'proposed APR below original; existing temporary ratio; no expiry/cancel branch'),
                ]
                if is_candidate and hook == 'PeriodicTermHooks':
                    profile['inherited_path_exclusions'] = [{
                        'excluded_event_signatures': [sig(eventnodes[event][0]) for event, _ in parent_events],
                        'reason': 'Every APR decrease returns through proposal execution before the parent call. Parent temporaryExcessReserveRatio starts empty and only its decrease branch can initialize it. Induction over all scoped writers leaves the map empty in PeriodicTermHooks: increase/equal parent calls can neither initialize it nor expire, cancel or update an existing entry.',
                        'override': fr(hook, name), 'parent': fr('MarketConstraintHooks', name),
                        'source_sites': sites(hook, name, 'annualInterestBips < intermediateState.annualInterestBips') + sites(hook, name, 'return (annualInterestBips, intermediateState.reserveRatioBips)') + sites(hook, name, 'super.onSetAnnualInterestAndReserveRatioBips') + sites('MarketConstraintHooks', name, 'annualInterestBips < originalAnnualInterestBips') + sites('MarketConstraintHooks', name, 'temporaryExcessReserveRatio[market] = tmp'),
                        'source_fact_reference': {'file': f'{role}-hooks-facts.json', 'semantic_resolution': 'writer induction for PeriodicTermHooks temporaryExcessReserveRatio'},
                    }]
                else:
                    for event, condition in parent_events:
                        events.append(ev(event, condition, 'MarketConstraintHooks', name))
                if hook == 'PeriodicTermHooks':
                    events.append(ev('AnnualInterestBipsReductionProposalCancelled', 'APR increases and a pending proposal exists', hook, name))
                    events.append(ev('AnnualInterestBipsReductionExecuted', 'APR decreases; matching proposal, response window and unpaid-withdrawal gates pass', hook, '_executePendingAnnualInterestBipsReduction'))
            profile['local_event_disposition'] = 'conditional-events' if events else 'no-local-events; empty callback body'
            profiles[profile['id']] = profile
        if is_candidate and hook == 'PeriodicTermHooks':
            f = fr(hook, 'executePendingAnnualInterestBipsReduction')
            profiles[f['function_id']] = {'id': f['function_id'], 'target_function': f,
                'condition': 'Configured address executes pinned PeriodicTermHooks, caller is a hooked market, and proposal/time/debt gates pass.',
                'possible_events': [ev('AnnualInterestBipsReductionExecuted', 'matching pending proposal; response window finished; validity period not expired; pending withdrawals zero; reduced APR in range', hook, '_executePendingAnnualInterestBipsReduction')],
                'external_event_effects': []}

        # The external body is inherited from IHooks, but its virtual _onCreateMarket
        # target must resolve in the concrete hook runtime before following helpers.
        creation_action = next(a for a in hookfacts['actions'] if a['contract'] == hook and a['function'] == 'onCreateMarket')
        creation_events = []
        if hook == 'FixedTermHooks':
            creation_events.append(ev('FixedTermUpdated', 'Every successful concrete creation callback; all enclosing deployment steps succeed', hook, '_onCreateMarket'))
        elif hook == 'PeriodicTermHooks':
            creation_events.append(ev('PeriodicTermUpdated', 'Every successful concrete creation callback; all enclosing deployment steps succeed', hook, '_onCreateMarket'))
        creation_events.append(ev('MinimumDepositUpdated', 'Decoded minimumDeposit > 0; all enclosing deployment steps succeed', hook, '_onCreateMarket'))
        assert {e['signature'] for e in creation_events} == {e['event'] for e in creation_action['events']}
        profiles[creation_action['id']] = {
            'id': creation_action['id'], 'target_function': fr('IHooks', 'onCreateMarket'),
            'runtime_action_id': creation_action['id'], 'implementation': fr(hook, '_onCreateMarket'),
            'condition': 'Configured address executes this pinned concrete hook; caller is immutable factory; explicit administrator/deployer equals stored hook administrator/borrower; parameter and creation-data guards pass; enclosing deployment succeeds.',
            'virtual_dispatch': 'IHooks.onCreateMarket -> concrete ' + hook + '._onCreateMarket -> MarketConstraintHooks._onCreateMarket',
            'source_fact_reference': {'file': f'{role}-hooks-facts.json', 'action_id': creation_action['id'], 'reachable_function_ids': creation_action['reachable_function_ids']},
            'guard_evidence': creation_action['guard_evidence'],
            'storage_write_evidence': creation_action['storage_write_evidence'],
            'possible_events': creation_events, 'local_event_disposition': 'conditional concrete creation events; FixedTermUpdated/PeriodicTermUpdated occurs on every successful applicable callback',
            'external_event_effects': [],
        }

    # Actual market callback call sites, preserving each caller function and enabled flag.
    for (contract, name), variants in functions.items():
        if contract not in ('WildcatMarket', 'WildcatMarketToken', 'WildcatMarketWithdrawals', 'WildcatMarketConfig'):
            continue
        for function in variants:
            for call in walk(function.get('body', {})):
                if call.get('nodeType') != 'FunctionCall':
                    continue
                match = re.match(r'hooks\.(on\w+)\(', text(call))
                if not match:
                    continue
                callback = match.group(1)
                condition = 'Host action reaches this call; ' + callback.replace('on', 'useOn', 1) + ' flag enabled; callback and enclosing transaction succeed.'
                if name == 'repayAndProcessUnpaidWithdrawalBatches':
                    condition += ' Repay amount is greater than zero.'
                if name == 'setProtocolFeeBips':
                    condition += 'Requested fee differs from current fee.'
                add(contract, name, 'hooks.hooksAddress().' + callback, condition, 'market address',
                    call_site=ref(call), dispatch=fr('LibHooksConfig', callback), runtime_contracts=markettypes,
                    call_opcode='CALL', concrete_target_profiles=[p for p in profiles if any(p.startswith(h + ':' + callback + '(') for h in hooktypes)],
                    unknown_target_event_effects='Unresolved for a different configured hooks implementation; no unconditional built-in event claim.')
    if is_candidate:
        add('WildcatMarketConfig', 'executePendingAnnualInterestBipsReduction', 'hooks.hooksAddress().executePendingAnnualInterestBipsReduction',
            'Market open and dedicated pending-APR callback flag enabled; returned APR must strictly reduce current APR; whole transaction succeeds.',
            'market address', concrete_target_profiles=[p for p in profiles if p.startswith('PeriodicTermHooks:executePendingAnnualInterestBipsReduction(')],
            call_opcode='CALL', runtime_contracts=markettypes,
            call_sites=sites('WildcatMarketConfig', 'executePendingAnnualInterestBipsReduction', '.executePendingAnnualInterestBipsReduction'),
            unknown_target_event_effects='Arbitrary configured implementation unresolved; OpenTermHooks and FixedTermHooks have no such endpoint.')

    factorytypes = ['HooksFactory'] + (['HooksFactoryRevolving'] if is_candidate else [])
    for factory in factorytypes:
        add(factory, 'constructor', 'WildcatArchController.sphereXEngine() -> SphereX base initialization',
            'Named pinned factory constructor executes successfully; provided ArchController engine getter returns successfully.',
            'new factory address at static getter',
            events=[ev('ChangedSpherexOperator', 'Factory constructor reaches base initialization', 'SphereXProtectedRegisteredBase', '__SphereXProtectedRegisteredBase_init'),
                    ev('ChangedSpherexEngineAddress', 'Factory constructor reaches base initialization', 'SphereXProtectedRegisteredBase', '__SphereXProtectedRegisteredBase_init')],
            call_opcode='STATICCALL for ArchController getter; local initialization emits the two events',
            call_sites=sites(factory, 'constructor', '__SphereXProtectedRegisteredBase_init'),
            event_boundary='No persisted logs from static getter; local constructor logs survive only if construction and enclosing transaction succeed.')
        add(factory, 'registerWithArchController', 'WildcatArchController.registerController(address)',
            'Factory is registered in ArchController controller-factory set; controller not already registered.',
            'factory address, not external invoker',
            events=[ev('ControllerAdded', 'successful registry add', 'WildcatArchController', 'registerController'),
                    ev('NewAllowedSenderOnchain', 'ArchController SphereX engine is nonzero and engine registration succeeds', 'SphereXConfig', '_addAllowedSenderOnChain')],
            target_function=fr('WildcatArchController', 'registerController'),
            call_sites=sites(factory, 'registerWithArchController', 'registerController'), call_opcode='CALL',
            nested_unknown='Nonzero SphereX engine.addAllowedSenderOnChain mutable call may emit arbitrary events.')
        add(factory, '_deployMarket', 'WildcatArchController.registerMarket(address)',
            'Market creation and all earlier validation succeed; factory is a registered controller; computed market address not already registered.',
            'factory address',
            events=[ev('MarketAdded', 'successful registry add', 'WildcatArchController', 'registerMarket'),
                    ev('NewAllowedSenderOnchain', 'ArchController SphereX engine nonzero; engine registration succeeds', 'SphereXConfig', '_addAllowedSenderOnChain')],
            target_function=fr('WildcatArchController', 'registerMarket'), call_sites=sites(factory, '_deployMarket', 'registerMarket'),
            call_opcode='CALL', nested_unknown='SphereX mutable-call event effects unresolved.')
        add(factory, '_deployMarket', 'stored market initcode -> WildcatMarketBase.constructor',
            'Stored marketInitCodeStorage bytes match the pinned market initcode; CREATE2 succeeds; registration and enclosing transaction succeed.',
            'factory address at constructor',
            events=[ev('ChangedSpherexOperator', 'Pinned constructor reaches SphereX base initialization', 'SphereXProtectedRegisteredBase', '__SphereXProtectedRegisteredBase_init'),
                    ev('ChangedSpherexEngineAddress', 'Pinned constructor reaches SphereX base initialization', 'SphereXProtectedRegisteredBase', '__SphereXProtectedRegisteredBase_init')],
            target_function=fr('WildcatMarketBase', 'constructor'), call_opcode='CREATE2',
            call_sites=sites(factory, '_deployMarket', 'create2WithStoredInitCode'),
            constructor_input_route={'getter': fr(factory, 'getMarketParameters'), 'receiver': fr('WildcatMarketBase', '_getMarketParameters'), 'opcode': 'STATICCALL',
                'identity': 'Operational borrower is original factory msg.sender; ' + ('borrowerPrincipal is separately resolved and temporarily stored; registry and wrapperFactory are separate addresses.' if is_candidate else 'borrower equals that operational deployer.'),
                'events': 'Getter and all static descendants have no persisted logs.'},
            unknown_target_event_effects='Stored bytecode identity is not established by source alone; other constructor events unresolved.')
        add(factory, '_deployHooksInstance', 'stored hooks template -> concrete hook constructor',
            'Template exists and enabled; template bytes after first byte match a named pinned hook; CREATE2 and enclosing transaction succeed.',
            'factory address at IHooks constructor; principal/deployer is an explicit constructor argument', call_opcode='CREATE2',
            call_sites=sites(factory, '_deployHooksInstance', 'create2('),
            possible_target_functions=[fr(h, 'constructor') for h in hooktypes],
            constructor_identity='administrator=resolved registered principal; separate from operational borrower and factory' if is_candidate else 'borrower=original factory caller; factory=constructor msg.sender',
            initialization=fr('BaseAccessControls', '_initialize'),
            events=[ev('RoleProviderAdded', 'Nonempty constructor args; initialization registers a previously absent provider', 'BaseAccessControls', '_addRoleProvider'),
                    ev('RoleProviderUpdated', 'Nonempty constructor args; initialization repeats an already added provider and updates TTL', 'BaseAccessControls', '_addRoleProvider')],
            nested_unknown='Optional provider factory createRoleProvider is mutable CALL and may deploy/event; arbitrary factory and stored hook bytecode events unresolved.')
        links[-1]['factory_local_events'] = [ev('HooksInstanceDeployed', 'CREATE2 succeeds and all enclosing deployment calls succeed', factory, '_deployHooksInstance')]
        if is_candidate:
            links[-1]['factory_local_events'].append(ev('HooksInstanceRoleProviders', 'Metadata static queries finish; availability flag records success/failure; entire transaction succeeds', factory, '_deployHooksInstance'))
        deployment_emitter = '_emitMarketDeployment' if is_candidate else '_deployMarket'
        market_deployment_events = [ev('MarketDeployed', 'Market deployment, ArchController registration and all enclosing calls succeed', factory, deployment_emitter)]
        if is_candidate:
            market_deployment_events.extend([ev('MarketDeploymentConfig', 'Successful complete market deployment', factory, deployment_emitter), ev('MarketHooksData', 'Successful complete market deployment', factory, deployment_emitter)])
            if factory == 'HooksFactoryRevolving':
                market_deployment_events.append(ev('RevolvingMarketDeployed', 'Successful complete revolving market deployment', factory, deployment_emitter))
        add(factory, '_deployMarket', 'factory deployment event sequence after registration',
            'All hook callbacks, stored-initcode construction, registration and metadata operations succeed.',
            'factory original external caller remains operational borrower', events=market_deployment_events,
            call_opcode='local emission; external effects described in separate joins',
            target_function=fr(factory, deployment_emitter))
        links[-1]['successful_path_order'] = [
            'deployMarketAndHooks first creates the hook: concrete constructor initialization, then factory HooksInstanceDeployed' + (' and HooksInstanceRoleProviders' if is_candidate else '') + '.',
            '_deployMarket pays any applicable origination fee, then calls onCreateMarket at the predicted market address before market construction.',
            'Concrete creation callback events precede temporary parameter storage and market CREATE2.',
            'Matching pinned market constructor emits inherited SphereX initialization events; then factory registers market with ArchController.',
            'ArchController registration events precede the factory market deployment event sequence.',
            'Every earlier event is discarded if any later step in the enclosing transaction reverts; other stored template/initcode implementations remain unresolved.',
        ]
        if factory == 'HooksFactoryRevolving':
            add('WildcatMarketRevolving', 'constructor', 'HooksFactoryRevolving.getRevolvingMarketCommitmentFeeBips()',
                'Stored initcode is pinned revolving market; constructor caller implements expected getter and returns canonical uint16.',
                'new revolving market address at factory', target_function=fr(factory, 'getRevolvingMarketCommitmentFeeBips'),
                call_opcode='STATICCALL', call_sites=sites('WildcatMarketRevolving', 'constructor', 'staticcall('),
                event_disposition='No local logs in revolving-specific constructor; static getter has no persisted logs. Inherited base initialization events are separate.')
        for hook in hooktypes:
            creation_profile = hook + ':' + sig(fn('IHooks', 'onCreateMarket'))
            events = profiles[creation_profile]['possible_events']
            add(factory, '_deployMarket', hook + '.onCreateMarket',
                'Configured hooks instance executes this pinned implementation; caller equals hook immutable factory; explicit administrator/deployer equals stored hook administrator/borrower; constraints and remaining deployment succeed.',
                'factory address; explicit first argument is ' + ('borrower principal' if is_candidate else 'operational borrower'),
                events=events, target_function=fr('IHooks', 'onCreateMarket'), implementation=fr(hook, '_onCreateMarket'),
                concrete_target_profiles=[creation_profile],
                call_sites=sites(factory, '_deployMarket', 'onCreateMarket'), call_opcode='CALL',
                input_route='hooksData is caller-supplied creation bytes; returned HooksConfig is persisted in temporary market parameters and read by the new market constructor.',
                unknown_target_event_effects='Other configured hook bytecode: events unresolved; these are alternative implementations, never a joint unconditional event set.')
        for parameter_count in (1, 3):
            add(factory, 'pushProtocolFeeBipsUpdates', 'named market -> WildcatMarketConfig.setProtocolFeeBips(uint16)',
                'Template exists; selected page contains at least one market; each named target executes pinned market code; caller factory matches market immutable factory; fee <= 1000 bips; market open; all selected calls and enclosing transaction succeed.' +
                (' Positive candidate fee additionally requires a nonzero immutable fee recipient.' if is_candidate else ''),
                'factory address at each market; external invoker may be anyone',
                events=[ev('ProtocolFeeBipsUpdated', 'Requested fee differs from market current fee; callback and all subsequent page/transaction steps succeed', 'WildcatMarketConfig', 'setProtocolFeeBips')],
                source_parameter_count=parameter_count, target_function=fr('WildcatMarketConfig', 'setProtocolFeeBips'),
                intermediary=fr(factory, 'pushProtocolFeeBipsUpdates', 3),
                call_sites=sites(factory, 'pushProtocolFeeBipsUpdates', 'call(gas(), market', 3), call_opcode='CALL',
                overload_binding='Single-address overload binds start=0 and end=uint256.max; paged overload clamps end to list length.' if parameter_count == 1 else 'Explicit start/end; end clamped to list length.',
                local_event_disposition='Factory emits no local event. Empty page invokes no market and emits no downstream event.',
                pagination='start > clamped end reverts InvalidPaginationRange; boundary-empty page returns' if is_candidate else 'start > clamped end reverts from checked subtraction; boundary-empty page has zero iterations',
                market_event_route_refs=[{'file': f'{role}-market-facts.json', 'event_routes_key': key} for key in marketfacts['event_routes'] if key.startswith('setProtocolFeeBips:')],
                concrete_callback_profiles=[p for p in profiles if any(p.startswith(h + ':onSetProtocolFeeBips(') for h in hooktypes)],
                callback_condition='onSetProtocolFeeBips runs only when fee differs and callback flag enabled; pinned built-in callback bodies emit no local events.',
                nested_event_effects='Market accrual/checkpoint/withdrawal processing events remain conditioned as in referenced market routes, even when fee is unchanged. SphereX and arbitrary hook mutable-call effects remain unresolved.',
                unknown_target_event_effects='The stored market address alone does not establish bytecode identity; named-callee event joins are conditional, including for the single-address overload.')
        if is_candidate:
            add(factory, '_resolveBorrowerPrincipal', 'WildcatBorrowerIdentityRegistry.resolveBorrower(address)',
                'Factory borrower admission/deployment resolves original external caller; registry call must return exactly one ABI address word and nonzero principal.',
                'factory address', target_function=fr('WildcatBorrowerIdentityRegistry', 'resolveBorrower'),
                call_sites=sites(factory, '_resolveBorrowerPrincipal', 'staticcall'), call_opcode='STATICCALL',
                event_disposition='no-logs under static call; returned principal and availability remain external assumptions')

    # Sanctions route: executing an already queued withdrawal is distinct from queuing it.
    add('WildcatMarketWithdrawals', '_executeWithdrawal', 'WildcatMarketBase._createEscrowForUnderlyingAsset -> WildcatSanctionsSentinel.createEscrow',
        'Payable withdrawal amount nonzero; batch executable; account is sanctioned; enabled callback and whole transaction succeed.',
        'market address at sentinel',
        events=[ev('NewSanctionsEscrow', 'Escrow does not yet have code; new CREATE2 succeeds', 'WildcatSanctionsSentinel', 'createEscrow'),
                ev('SanctionOverride', 'New escrow deployed; exemption for that escrow set', 'WildcatSanctionsSentinel', 'createEscrow'),
                market_ev('SanctionedAccountWithdrawalSentToEscrow', 'Underlying asset transfer to escrow succeeds', 'WildcatMarketWithdrawals', '_executeWithdrawal'),
                market_ev('WithdrawalExecuted', 'Execution and underlying transfer succeed', 'WildcatMarketWithdrawals', '_executeWithdrawal')],
        target_function=fr('WildcatSanctionsSentinel', 'createEscrow'), intermediary=fr('WildcatMarketBase', '_createEscrowForUnderlyingAsset'),
        call_sites=sites('WildcatMarketWithdrawals', '_executeWithdrawal', '_createEscrowForUnderlyingAsset'), call_opcode='CALL',
        namespace='Current market borrowerPrincipal' if is_candidate else 'Immutable market borrower',
        reused_escrow='Existing deterministic escrow returns without sentinel events or constructor execution.',
        nested_unknown='Underlying ERC20 safeTransfer is mutable CALL: arbitrary token events unresolved; sanctions queries are STATICCALL and have no persisted logs.')
    add('WildcatSanctionsSentinel', 'createEscrow', 'WildcatSanctionsEscrow.constructor',
        'No code exists at derived escrow address; CREATE2 and parent transaction succeed.', 'sentinel address',
        target_function=fr('WildcatSanctionsEscrow', 'constructor'), call_opcode='CREATE2',
        call_sites=sites('WildcatSanctionsSentinel', 'createEscrow', 'new WildcatSanctionsEscrow'),
        event_disposition='Pinned escrow constructor emits no local logs; its tmpEscrowParams read is STATICCALL with no persisted logs.',
        identity='Constructor freezes borrower namespace, account and asset from sentinel temporary parameters; later borrower transfer does not rewrite an existing escrow.')
    add('WildcatSanctionsEscrow', 'releaseEscrow', 'sentinel.isSanctioned; asset.balanceOf; asset.transfer',
        'Any invoker; immutable account not sanctioned in immutable borrower namespace; transfer succeeds.', 'escrow address',
        events=[ev('EscrowReleased', 'Whole immutable-asset balance transferred successfully', 'WildcatSanctionsEscrow', 'releaseEscrow')],
        call_opcode='STATICCALL for sanctions/balance reads; CALL for transfer',
        unknown_target_event_effects='No logs from static reads; arbitrary asset transfer event effects unresolved.',
        identity='Release beneficiary is immutable original account; no invocation of market executeWithdrawal occurs here.')

    # Wrapper actions move market tokens; they do not tender the underlying asset to the market.
    for name in ('deposit', 'mint', 'withdraw', 'redeem'):
        entering = name in ('deposit', 'mint')
        target = 'transferFrom' if entering else 'transfer'
        add('Wildcat4626Wrapper', name, 'WildcatMarketToken.' + target,
            'Wrapper amount, allowance, sanctions and backing checks pass; market token call and all later checks succeed.', 'wrapper address',
            events=[market_ev('Transfer', 'Successful market-token movement', 'WildcatMarketToken', '_transfer')],
            target_function=fr('WildcatMarketToken', target), intermediary=fr('WildcatMarketToken', '_transfer'),
            call_sites=sites('Wildcat4626Wrapper', name, '.safeTransferFrom' if entering else '.safeTransfer'),
            runtime_contracts=markettypes, call_opcode='CALL',
            amount_route='Caller market tokens -> wrapper; mint wrapper shares' if entering else 'Burn wrapper shares; wrapper market tokens -> receiver',
            nested_event_routes='Market _getUpdatedState and _writeState can emit accounting events; see market facts event_routes for transferFrom/transfer. Configured onTransfer profile and SphereX guard are conditional.',
            unknown_target_event_effects='If supplied market address executes other bytecode, mutable-call event effects unresolved.',
            wrapper_local_events='Wrapper emits its own Transfer plus Deposit/Withdraw; these are distinct emitting contracts from market Transfer.')
    absences.append({'from_contract': 'Wildcat4626Wrapper', 'functions': [fr('Wildcat4626Wrapper', n) for n in ('deposit', 'mint', 'withdraw', 'redeem')],
                     'absent_routes': ['market.deposit', 'market.depositUpTo', 'market.queueWithdrawal', 'market.queueFullWithdrawal'],
                     'basis': 'Complete operational bodies call market token transferFrom/transfer. ERC4626 naming is not evidence of market deposit/withdrawal-entry forwarding.'})
    if is_candidate:
        add('Wildcat4626Wrapper', 'nukeFromOrbit', 'WildcatMarketConfig.nukeFromOrbit(address) -> WildcatMarket._blockAccount -> _queueWithdrawal',
            'Target is sanctioned and not wrapper itself; wrapper forwards complete original calldata to market first; market gates and entire transaction succeed.',
            'wrapper address at market', target_function=fr('WildcatMarketConfig', 'nukeFromOrbit'), intermediary=fr('WildcatMarket', '_blockAccount'),
            call_sites=sites('Wildcat4626Wrapper', 'nukeFromOrbit', 'call('), call_opcode='CALL', runtime_contracts=markettypes,
            nested_event_routes='Market _blockAccount queues only if account has positive scaled market-token balance; ordinary queue hook and term restrictions remain. Full market nuke routes in market facts.',
            wrapper_second_stage={'condition': 'Target holds positive wrapper shares after market call', 'target_function': fr('WildcatSanctionsSentinel', 'createEscrow'),
                'namespace': 'Live market principal; asset is wrapper address',
                'events': [ev('NewSanctionsEscrow', 'New deterministic wrapper-asset escrow', 'WildcatSanctionsSentinel', 'createEscrow'), ev('SanctionOverride', 'New deterministic wrapper-asset escrow', 'WildcatSanctionsSentinel', 'createEscrow'),
                    ev('Transfer', 'Positive wrapper shares transferred to escrow; whole transaction succeeds', 'ERC20', '_transfer'),
                    ev('SanctionedAccountSharesSentToEscrow', 'Positive wrapper shares transferred to escrow; whole transaction succeeds', 'Wildcat4626Wrapper', 'nukeFromOrbit')],
                'effects': 'Mark authorized escrow then transfer wrapper shares to escrow; wrapper Transfer and quarantine event. Zero shares returns after market call.'},
            unknown_target_event_effects='Arbitrary wrapped market or configured SphereX/hook mutable calls unresolved.')
        add('Wildcat4626WrapperFactory', 'createWrapper', 'WildcatMarketConfig.registerWrapper(address)',
            'Supported floor-rounding generation; ArchController registers market; transfer policy permits transfers; wrapper constructor succeeds; market wrapperFactory equals this factory; no prior wrapper registered.',
            'wrapper factory address', events=[ev('WrapperRegistered', 'successful market registration', 'WildcatMarketConfig', 'registerWrapper')],
            target_function=fr('WildcatMarketConfig', 'registerWrapper'), call_opcode='CALL',
            call_sites=sites('Wildcat4626WrapperFactory', 'createWrapper', 'registerWrapper'),
            alternative='Legacy rounding-undeclared branch calls configured v1Factory.createWrapper and returns; no local WrapperDeployed or registerWrapper call on that branch. Arbitrary v1 factory events unresolved.')

    # Provider pull and stateful validation are different boundaries. Built-in provider
    # implementations are credential query targets, not sources of grantRole/revokeRole calls.
    for name, opcode, target in [('_tryGetCredential', 'STATICCALL', 'IRoleProvider.getCredential(address)'), ('_tryValidateCredential', 'CALL', 'IRoleProvider.validateCredential(address,bytes)')]:
        add('BaseAccessControls', name, target,
            'Applicable registered provider selected by refresh/query or hooksData path; failed provider calls return no child logs; enclosing access action must succeed.',
            'hook instance address', call_opcode=opcode,
            event_disposition='no-logs under static call' if opcode == 'STATICCALL' else 'Arbitrary provider events unresolved; pinned built-in credential implementations emit no local logs and make only static external reads.',
            call_sites=sites('BaseAccessControls', name, 'staticcall' if opcode == 'STATICCALL' else 'if call('),
            concrete_targets=[fr(c, 'getCredential' if opcode == 'STATICCALL' else 'validateCredential') for c in contracts if c.endswith('RoleProvider') and not c.startswith('I') and (c, 'getCredential' if opcode == 'STATICCALL' else 'validateCredential') in functions],
            callback_event_join='A successful/failed credential result can alter hook-local AccountAccessGranted/Revoked/AccountMadeFirstDeposit conditions; those are emitted by hook, not provider.')
    for name in ('grantRole', 'grantRoles', 'revokeRole', 'revokeRoles'):
        grant = name.startswith('grant')
        event = 'AccountAccessGranted' if grant else 'AccountAccessRevoked'
        helper = '_setCredentialAndEmitAccessGranted' if grant else '_revokeRole'
        source = fr('BaseAccessControls', name)
        links.append({'id': role + ':external provider -> ' + source['function_id'], 'from': {'contract': 'external provider caller', 'function_id': None, 'source_status': 'No concrete built-in caller found'},
            'target': source['function_id'], 'target_function': source, 'callee_msg_sender': 'provider address',
            'condition': ('Caller exists in hook provider registry; credential expiry/replacement checks pass' + ('; timestamp nonzero and not future' if is_candidate else '')) if grant else 'Caller equals account credential lastProvider; membership in current provider registry is not checked',
            'possible_events': [ev(event, 'One per successfully processed account; empty batch has none; any later revert discards earlier batch logs', 'BaseAccessControls', helper)],
            'concrete_runtime_contracts': hooktypes, 'source_dispatch_status': 'Public admission route only; not a proven provider-contract push call.'})
    absences.append({'from_scope': 'src/providers/**', 'absent_routes': ['BaseAccessControls.grantRole', 'BaseAccessControls.grantRoles', 'BaseAccessControls.revokeRole', 'BaseAccessControls.revokeRoles'],
                     'basis': 'No built-in provider implementation calls these hook endpoints; current source scope has no providers subtree at deployed pin.' if not is_candidate else 'All concrete built-in providers return credentials or maintain their own configuration; no hooks grant/revoke call in source.'})
    add('BaseAccessControls', '_createRoleProvider', 'configured roleProviderFactory.createRoleProvider(bytes)',
        'Hook administrator path or constructor initialization selects provider factory; nonzero returned provider and subsequent registration succeed.',
        'hook instance address', call_opcode='CALL',
        events=[ev('RoleProviderAdded', 'Created provider registered for first time', 'BaseAccessControls', '_addRoleProvider'), ev('RoleProviderUpdated', 'Factory returns an already registered provider', 'BaseAccessControls', '_addRoleProvider')],
        call_sites=sites('BaseAccessControls', '_createRoleProvider', 'createRoleProvider'),
        concrete_target_functions=[fr(c, 'createRoleProvider') for c in contracts if c.endswith('RoleProviderFactory') and not c.startswith('I')],
        nested_event_routes='Named candidate factory constructor/event joins are separate records. AccessList constructor additionally emits MemberAdded per initial member. Other pinned built-in constructors emit no local events.',
        unknown_target_event_effects='Configured arbitrary factory may emit other events; no unconditional constructor/event claim.')
    if is_candidate:
        for factory in [c for c in contracts if c.endswith('RoleProviderFactory') and not c.startswith('I')]:
            provider = factory.removesuffix('Factory')
            events = [ev(provider + 'Deployed', 'Named pinned factory constructs provider and all enclosing calls succeed', factory, '_createRoleProvider')]
            if provider == 'AccessListRoleProvider':
                events.append(ev('MemberAdded', 'One per initialMembers entry processed; all enclosing calls succeed', provider, '_addMember'))
            add(factory, '_createRoleProvider', provider + '.constructor',
                'CREATE2 target has no code; constructor succeeds; enclosing hook initialization/administrator action also succeeds if present.',
                'provider factory address at constructor; deployer/salt namespace is hook address when called by hook',
                events=events, target_function=fr(provider, 'constructor'), call_opcode='CREATE2',
                call_sites=sites(factory, '_createRoleProvider', 'new ' + provider),
                identity='Provider administrator comes from encoded provider inputs; factory and hook administrator are separate roles.',
                nested_event_disposition='Any token interface/balance constructor validation uses static queries and cannot persist callee logs.')

    if is_candidate:
        for name in ('requestBorrowerTransfer', 'acceptBorrowerTransfer'):
            add('WildcatMarketBase', name, 'WildcatBorrowerIdentityRegistry.resolveBorrower(address)',
                'Current operational borrower requests, or pending operational borrower accepts; nonzero target resolves; acceptance must match stored pending principal; both sides pass raw sanctions checks.',
                'market address', target_function=fr('WildcatBorrowerIdentityRegistry', 'resolveBorrower'), intermediary=fr('WildcatMarketBase', '_validateBorrowerTransferTarget'),
                call_sites=sites('WildcatMarketBase', '_validateBorrowerTransferTarget', 'staticcall('), call_opcode='STATICCALL',
                event_disposition='Registry and raw-sanctions static queries cannot persist logs.',
                market_events=[market_ev('BorrowerTransferRequested' if name == 'requestBorrowerTransfer' else 'BorrowerTransferred', 'Market identity update succeeds; registry itself is not mutated', 'WildcatMarketBase', name)],
                identity='Registry account-principal ownership and market borrower/principal state are separate; market principal is stored, not automatically live-resolved on every action.')
        for name in ('requestBorrowerAccountPrincipalTransfer', 'cancelBorrowerAccountPrincipalTransfer', 'acceptBorrowerAccountPrincipalTransfer'):
            # The registry mutates its own account principal; no broadcast/callback to markets.
            if ('WildcatBorrowerIdentityRegistry', name) not in functions:
                continue
            absences.append({'from': fr('WildcatBorrowerIdentityRegistry', name), 'absent_routes': ['market.requestBorrowerTransfer', 'market.acceptBorrowerTransfer', 'market borrower storage rewrite'],
                             'basis': 'Registry transfer changes its own account-principal relation. Existing market state and existing escrow immutable borrower namespaces are not rewritten.'})
            event = {'requestBorrowerAccountPrincipalTransfer': 'BorrowerAccountPrincipalTransferRequested', 'cancelBorrowerAccountPrincipalTransfer': 'BorrowerAccountPrincipalTransferCancelled', 'acceptBorrowerAccountPrincipalTransfer': 'BorrowerAccountPrincipalTransferred'}[name]
            add('WildcatBorrowerIdentityRegistry', name, 'registry account-principal relation only',
                'Current principal requests/cancels or pending principal accepts; target/principal registration validation passes where applicable.',
                'external current or pending principal; no market invocation',
                events=[ev(event, 'Successful registry transition', 'WildcatBorrowerIdentityRegistry', name)],
                call_opcode='local mutation; nested ArchController registration checks are STATICCALL and cannot persist logs',
                downstream_identity_effect='Subsequent resolveBorrower reflects updated registry relation; existing market borrowerPrincipal remains stored until market borrower transfer.')

    raw_hook_actions = {action['id']: action for action in hookfacts['actions']}
    for profile_id, profile in profiles.items():
        generated_events = {(event['signature'], event['topic0']) for event in profile['possible_events']}
        raw_events = {(event['event'], event['topic0']) for event in raw_hook_actions[profile_id]['events']}
        assert generated_events == raw_events, (role, profile_id, 'cross-system callback events differ from current raw hooks action', generated_events - raw_events, raw_events - generated_events)
    for referenced in walk([profiles, links, absences]):
        for key in ('path', 'source_path', 'ref', 'emitter'):
            value = referenced.get(key)
            if isinstance(value, str):
                source_path = value.split(':', 1)[0]
                if source_path in sources:
                    used_paths.add(source_path)
    out['snapshots'][role] = {'commit': denominator['commit'], 'source_root': str((ROOT / role).resolve()),
        'input_facts_sha256': {f'{role}-{name}-facts.json': sha(P / f'{role}-{name}-facts.json') for name in ('support', 'market', 'hooks')},
        'callback_profiles': profiles, 'links': links, 'explicit_absences': absences,
        'callback_event_reconciliation': {'basis': 'Exact canonical signature and topic0 set equality against each corresponding current raw hooks action', 'matched_profiles': len(profiles), 'unmatched_profiles': 0},
        'referenced_source_sha256': {path: hashlib.sha256(sources[path]).hexdigest() for path in sorted(used_paths)},
        'counts': {'links': len(links), 'callback_profiles': len(profiles), 'explicit_absences': len(absences)}}

(P / 'cross-system-links.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({role: data['counts'] for role, data in out['snapshots'].items()}))
