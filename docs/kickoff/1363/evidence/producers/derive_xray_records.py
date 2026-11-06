import collections
import hashlib
import json
import re
from pathlib import Path
from assemble_xray_evidence import ROOT, PREP, OUT, PINS, read, write, walk

def derive():
    comparisons = []
    links = read(OUT / 'linkage.json')
    maps = {role: {a['id']: a for a in links['snapshots'][role]['actions']} for role in PINS}
    support = {a['id']: a for a in read(PREP / 'support-comparison.json')['observations']}
    hook_comparisons = {}
    for role in PINS:
        for a in read(PREP / f'{role}-hooks-facts.json')['semantic_comparison']:
            hook_comparisons[a['id']] = a
    for aid in sorted(set(maps['deployed']) | set(maps['candidate'])):
        before, after = maps['deployed'].get(aid), maps['candidate'].get(aid)
        refs = {'deployed': before['source_refs'] if before else [], 'candidate': after['source_refs'] if after else []}
        extra = []
        if aid in support:
            row = support[aid]
            status, reason = row['classification'], row['observation']
            extra = row.get('helper_evidence', [])
        elif aid in hook_comparisons:
            row = hook_comparisons[aid]
            status, reason = row['status'], row['reason']
            if status.startswith('unchanged'): status = 'unchanged'
            extra = row.get('additional_cites', [])
        elif not before:
            status, reason = 'added', 'New concrete runtime action in the candidate source; access, internal override context, effects and possible events are recorded in the candidate linkage row.'
        elif not after:
            status, reason = 'removed', 'This canonical action ID is absent from the candidate source. A changed signature is a removed action plus an added action, not a selector-equivalence assertion.'
        elif before['function'] in ('approve', 'changeSphereXEngine'):
            status = 'unchanged'
            reason = ('Reviewed allowance assignment and Approval emission are unchanged; neither action calls accrual or token-transfer helpers. SphereX activation/caller and nonreentrant policy are unchanged.' if before['function']=='approve' else 'The immutable ArchController operator restriction, engine-slot replacement and ChangedSpherexEngineAddress emission are unchanged; live operator and engine deployments are not established.')
        else:
            status = 'changed'
            function = before['function']
            reasons = {
                'rescueTokens': 'Borrower authority changes from an immutable address to the current operational borrower; excluded rescue assets and transfer destination semantics remain.',
                'borrow': 'Authority and raw-sanctions checks use the operational borrower and principal; accounting checkpoint/liquidity helpers change; Borrow adds borrower attribution.',
                'deposit': 'Inherited deposit helper floors scaling, uses current-principal sanctions and changed accounting checkpoints and hook credential/minimum-deposit semantics.',
                'depositUpTo': 'Deposit helper floors scaling, uses current-principal sanctions and changed accounting checkpoints and hook credential/minimum-deposit semantics.',
                'repay': 'Payer identity remains msg.sender; accrual/checkpoint writes change, and the candidate adds virtual repayment accounting used by the new Revolving runtime.',
                'collectFees': 'Withdrawable-fee/liquidity and accrual helpers change; FeesCollected adds collector and recipient attribution.',
                'closeMarket': 'Borrower authority, reserve arithmetic, settlement rounding and checkpoints change; closing also emits the combined term-change event and caller-attributed MarketClosed.',
                'transfer': 'Scaling changes from half-up to floor; principal sanctions, accounting checkpoints and hook transfer-policy/provider paths change.',
                'transferFrom': 'Allowance deduction remains normalized; scaled transfer, principal sanctions, accounting checkpoints and hook transfer-policy/provider paths change.',
                'queueWithdrawal': 'Scaling floors; expiry narrows with a checked cast, closed-batch collision handling and checkpointed settlement are added; hook access/provider paths change.',
                'queueFullWithdrawal': 'The exact account scaled balance is still queued; closed-batch collision handling, checkpointed settlement and hook access/provider paths change.',
                'executeWithdrawal': 'Claim formula and executor/account separation remain; hook ABI adds expiry, sanctions use current principal, and accrual/checkpoint/settlement helpers change.',
                'executeWithdrawals': 'Atomic multi-claim and empty extraData remain; each claim adds hook expiry and uses current-principal sanctions and revised accounting helpers.',
                'repayAndProcessUnpaidWithdrawalBatches': 'Liquidity subtraction saturates, accrual/checkpoint and settlement math change, and repayment dispatch gains the Revolving override context.',
                'nukeFromOrbit': 'Current-principal sanctions replace immutable-borrower sanctions, registered wrappers are excluded, and accounting/queue helpers change; Config-only empty _blockAccount stays distinct.',
                'setMaxTotalSupply': 'Authority becomes current borrower; MaxTotalSupplyUpdated adds caller and old/new values, and accounting checkpoints change.',
                'setAnnualInterestAndReserveRatioBips': 'Current-borrower authority, accounting/liquidity and hook reserve math change; two rate events become one combined old/new/caller event.',
                'setProtocolFeeBips': 'Positive fees now require a nonzero immutable recipient; the event adds factory caller and old/new values; accounting checkpoints change.',
                'updateState': 'Accrual advances delinquency time at zero fee, uses checkpointed assets at expiry and revised settlement/liquidity rounding; StateUpdated ABI remains.'}
            reason = reasons[function]
            extra = ['deployed:src/market/WildcatMarketBase.sol:406', 'candidate:src/market/WildcatMarketBase.sol:722'] if function != 'rescueTokens' else []
        comparisons.append({'id': aid, 'status': status, 'reason': reason, 'source_refs': refs, 'helper_evidence': extra,
            'selectors': {'deployed': before['selector'] if before else None, 'candidate': after['selector'] if after else None},
            'equivalence_boundary': 'Source semantics of this action and reviewed helper paths; not bytecode, gas, deployed configuration or runtime trace equivalence.'})
    write(OUT / 'comparison.json', {'schema': 'issue-1363-comparison/v1', 'roles': PINS,
        'basis': 'Fresh source reads at both pins, concrete inheritance and helper dispatch, reviewed source/event relations. Same top-level body bytes alone never establish unchanged behavior.',
        'counts': dict(collections.Counter(a['status'] for a in comparisons)), 'actions': comparisons})
    print('comparison', collections.Counter(a['status'] for a in comparisons))

    for role in PINS:
        root = ROOT / '.hexaemeron/sources' / role
        ast = read(PREP / f'{role}-ast.json')['sources']
        srcids = {v['id']: p for p,v in ast.items()}
        raw = {p:(root/p).read_bytes() for p in ast}
        nodes = {n['id']:n for v in ast.values() for n in walk(v['ast']) if 'id' in n}
        def loc(n):
            off,length,fid=map(int,n['src'].split(':'));p=srcids[fid]
            return {'path':p,'line':raw[p][:off].count(b'\n')+1,'end_line':raw[p][:off+length].count(b'\n')+1,'text':raw[p][off:off+length].decode()}
        guards=[]
        for path,item in ast.items():
            if not path.startswith('src/') or path.endswith(('Errors.sol','SafeCastLib.sol')):continue
            for n in walk(item['ast']):
                predicate=None
                kind=n.get('nodeType')
                if kind=='FunctionCall' and n.get('expression',{}).get('name') in ('require','assert'):
                    predicate=n
                elif kind=='IfStatement':
                    block=n['trueBody'];statements=block.get('statements',[block])
                    fails=any(s.get('nodeType')=='RevertStatement' or
                        s.get('nodeType')=='ExpressionStatement' and s.get('expression',{}).get('nodeType')=='FunctionCall' and
                        s['expression'].get('expression',{}).get('name','').startswith('revert') for s in statements)
                    if fails:predicate=n['condition']
                elif kind=='YulIf':
                    if any(s.get('nodeType')=='YulExpressionStatement' and s.get('expression',{}).get('functionName',{}).get('name')=='revert' for s in n['body']['statements']):predicate=n['condition']
                if predicate is None:continue
                p=loc(predicate)
                # Generic pure math input checks are not persistent protocol guards.
                if path.startswith('src/libraries/') and not any(x in p['text'] for x in ('state.','batch.','scaleFactor','returndata','staticcall','call(')):continue
                purpose=('Protects market balances, accounting or the authority needed to change them.' if '/market/' in path else
                    'Protects wrapper share accounting and the boundary to the wrapped market.' if '/vault/' in path else
                    'Protects hook policy, credential state or the authority needed to change it.' if '/access/' in path else
                    'Protects credential issuance, validation or provider administration.' if '/providers/' in path else
                    'Protects deployment parameters, registration or factory authority.' if 'HooksFactory' in path else
                    'Protects engine configuration or validation of a guarded market action.' if '/spherex/' in path else
                    'Protects sanctions custody and release conditions.' if 'Sanctions' in path else
                    'Protects registration and controller authority.' if 'ArchController' in path else
                    'Protects borrower identity resolution and registration state.' if 'IdentityRegistry' in path else
                    'Protects the checked accounting or external-return boundary.')
                guards.append(dict(p,kind=kind,purpose=purpose))
        guards=sorted({(g['path'],g['line'],g['text']):g for g in guards}.values(),key=lambda g:(g['path'],g['line']))
        for i,g in enumerate(guards,1):g['id']=f'G-{i}'
        write(OUT/'evidence'/f'{role}-guards.json',{'role':role,'commit':PINS[role],'guards':guards,
            'boundary':'Exact Solidity/Yul rejection predicates; parameter-only generic library bounds omitted. These are call guards, not global invariants.'})

        # Reconcile the prescribed text scans with parsed source declarations.
        functions=[]
        for path,item in ast.items():
            if not path.startswith('src/'):continue
            for n in walk(item['ast']):
                if n.get('nodeType')=='FunctionDefinition':functions.append((n,loc(n)))
        hits=collections.defaultdict(set)
        for scan in ['single','multiline']:
            for line in (PREP/f'{role}-entry-scan-{scan}.txt').read_text().splitlines():
                match=re.match(r'(src/.*\.sol)[:\-](\d+)[:\-]',line)
                if not match:continue
                path,number=match[1],int(match[2])
                for node,s in functions:
                    if path==s['path'] and s['line']<=number<=s['end_line']:
                        hits[node['id']].add(scan)
        dispositions=[]
        for node,s in functions:
            wanted=bool(node.get('body') and node['visibility'] in ('public','external') and node['stateMutability'] not in ('view','pure') and node['kind']=='function')
            if node['id'] in hits or wanted:
                dispositions.append({'path':s['path'],'line':s['line'],'function':node['name'],'scan_hits':sorted(hits[node['id']]),
                    'disposition':'implemented mutating definition; resolve concrete inheritance in action denominator' if wanted else 'excluded: interface declaration, view/pure, internal helper or initialization',
                    'visibility':node['visibility'],'mutability':node['stateMutability']})
        write(OUT/'evidence'/f'{role}-scan-reconciliation.json',{'role':role,'commit':PINS[role],'definitions':dispositions,
            'boundary':'Both prescribed scans retain context and are incomplete for some split/long signatures. Parsed source closes that omission and includes inherited library dependency actions; each permissionless source body and access helper was read by root.'})
        print(role,'guards',len(guards),'scan dispositions',len(dispositions))

if __name__=='__main__':derive()
