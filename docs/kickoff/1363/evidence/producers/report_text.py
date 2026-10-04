import collections
import json
import re
from concurrent.futures import ThreadPoolExecutor
from assemble_xray_evidence import ROOT, PREP, OUT, PINS, read, write

T = chr(96)

def md(text):
    return text.replace('§', T)

def cell(value):
    if isinstance(value, (dict, list)): value = json.dumps(value, ensure_ascii=False)
    return str(value).replace('|', '&#124;').replace('\n', ' ')

def surface(text):
    # Keep ABI, predicates and source links byte-identical during the wording pass.
    before = re.findall(r'`[^`]*`|https?://[^\s)]+', text)
    headings = {'Entry Point Map':'Entry point map', 'Protocol Flow Paths':'Protocol flow paths', 'External Event Boundary':'External event boundary',
        'How It Fits Together':'How it fits together', 'Protocol Threat Profile':'Protocol threat profile', 'Key Attack Surfaces':'Key attack surfaces',
        'Temporal Risk Profile':'Temporal risk profile', 'Dangerous Area Evolution':'Dangerous area evolution', 'Technical Debt Markers':'Technical debt markers'}
    parts = re.split(r'(`[^`]*`|https?://[^\s)]+)', text)
    for index in range(0, len(parts), 2):
        value = parts[index]
        for original, replacement in headings.items():
            value = re.sub(r'(?m)^(#{1,6} )' + re.escape(original) + r'(?=\s*$)', lambda m:m[1]+replacement, value)
        value = value.replace(' — ', ': ')
        value = re.sub(r'\*\*([^*\n]+):\*\*', r'\1:', value)
        parts[index] = re.sub(r'\*\*([^*\n]+)\*\*:', r'\1:', value)
    text = ''.join(parts)
    assert before == re.findall(r'`[^`]*`|https?://[^\s)]+', text)
    return text

def ref(role, path, line):
    if path.startswith('lib/solady/'):
        return f'[{path}:{line}](https://github.com/Vectorized/solady/blob/2ba1cc1eaa3bffd5c093d94f76ef1b87b167ff3c/{path.removeprefix("lib/solady/")}#L{line})'
    return f'[{path}:{line}](https://github.com/wildcat-finance/v2-protocol/blob/{PINS[role]}/{path}#L{line})'

def access_class(a):
    text = a['access'].lower()
    if text.startswith('permissionless'): return 'Permissionless'
    if 'admin-only' in text or 'archcontroller owner' in text or 'arch controller owner' in text: return 'Admin-Only'
    return 'Role-Gated'

def display_chains(action):
    paths=[]
    for path in action['call_path']:
        pieces=[]
        for part in path.split(' -> '):
            part=part.split(' @ ')[0]
            name=re.match(r'\s*((?:[A-Za-z_$][\w$]*\.)*[A-Za-z_$][\w$]*)\s*\(',part)
            if name:
                part=name[1]+'()'
            part=' '.join(part.split())
            if part not in pieces:pieces.append(part)
        result=' → '.join(pieces)
        if result not in paths:paths.append(result)
    return '<br>'.join(cell(x) for x in paths)

def flows(candidate):
    return md("""## Protocol Flow Paths

### Deployment and admission

§ArchController.owner → registerControllerFactory → HooksFactory.registerWithArchController§
§ArchController.owner → registerBorrower → HooksFactory.deployHooksInstance → deployMarket§
§HooksFactory.addHooksTemplate → deployHooksInstance§ ◄── template enabled and caller admitted
§hook authority.addRoleProvider → registered provider calls hook.grantRole§ ◄── provider and approval timestamp valid

### Lender and borrower

§[registered market] → asset.approve → WildcatMarket.deposit / depositUpTo§ ◄── cap, sanctions and hook policy
§[deposit] → WildcatMarketToken.approve → transferFrom§ ◄── allowance and scaled balance
§[deposit] → queueWithdrawal / queueFullWithdrawal → executeWithdrawal§ ◄── batch no longer pending and paid share available
§[available liquidity] → borrower.borrow§ ◄── source-defined borrowing reserve and open market
§payer.repay§ ◄── open market and positive amount; no prior borrow call required
§payer.repayAndProcessUnpaidWithdrawalBatches§ ◄── alternative funding/batch-processing path; zero repayment can process existing liquidity
§[registered market] → updateState / collectFees§ ◄── accrual and fee-liquidity conditions
§borrower.closeMarket → [remaining queues and claims]§ ◄── debts funded and queued scaled amounts settled

### Wrapping and sanctions

§registered market → Wildcat4626WrapperFactory.createWrapper → marketToken.approve → wrapper.deposit / mint§
§[wrapped balance] → wrapper.withdraw / redeem§ ◄── shares and market-token liquidity
§sanctioned lender → WildcatMarket.nukeFromOrbit → [ordinary queue path] → escrowed claim§ ◄── hook term rules
§sentinel override / external sanctions removal → WildcatSanctionsEscrow.releaseEscrow§ ◄── release predicate
""") + (md("""
### Candidate identities and periodic terms

§registry borrower-account registration → requestBorrowerTransfer → acceptBorrowerTransfer§ ◄── pending actor and rechecked principal
§requestAdministratorTransfer → acceptAdministratorTransfer → factory index update§
§PeriodicTermHooks APR proposal → [activation delay] → user calls market.executePendingAnnualInterestBipsReduction → hook.executePendingAnnualInterestBipsReduction§
""") if candidate else '')

def entry_report(role, snapshot):
    actions=snapshot['actions']
    counts=collections.Counter(access_class(a) for a in actions)
    lines=[f'# Entry Point Map\n\n> Wildcat V2 | {PINS[role]} | {len(actions)} runtime actions | {counts["Permissionless"]} permissionless | {counts["Role-Gated"]} role-gated | {counts["Admin-Only"]} admin-only\n', flows(role=='candidate'),
       'The count is over concrete source contracts and canonical ABI signatures, including inherited methods. It does not count deployed addresses. Abstract definitions, view/pure methods, internal libraries and constructors have separate dispositions in the evidence.\n']
    for category in ['Permissionless','Role-Gated','Admin-Only']:
        subset=[a for a in actions if access_class(a)==category]
        lines.append('## '+category+'\n')
        if category=='Permissionless':
            for a in subset:
                params='; '.join(f"{p['name'] or '(unnamed)'}: {p['type']} ({p['trust']})" for p in a['parameters']) or 'None'
                chains=display_chains(a)
                lines.append(md(f'### §{a["id"]}§\n\n| Aspect | Detail |\n| --- | --- |\n'
                   f'| Source and selector | {ref(role,a["source_path"],a["line"])}; §{a["selector"]}§; inherited: {str(a["inherited"]).lower()} |\n'
                   f'| Visibility | {a["visibility"]}; {a["mutability"]} |\n'
                   f'| Caller and constraints | {cell(a["access"])} |\n'
                   f'| Parameters | {cell(params)} |\n'
                   f'| Call chain branches | {chains} |\n'
                   f'| State modified | {cell("; ".join(a["effects"]))} |\n'
                   f'| Value flow | {cell(a["value_flow"])} |\n'
                   f'| Reentrancy guard | {"yes" if a["reentrancy_guard"] else "no"} |\n'
                   f'| Event disposition | {a["disposition"]}; source paths and conditions in [linkage.json](../linkage.json) |\n'))
        else:
            lines.append('| Action and selector | Source | Caller / parameters | State and value effects | Call branches / guard |\n| --- | --- | --- | --- | --- |')
            for a in subset:
                params='; '.join(f"{p['name'] or '(unnamed)'} {p['type']} ({p['trust']})" for p in a['parameters']) or 'no parameters'
                chains=display_chains(a)
                lines.append(md(f'| §{a["id"]}§<br>§{a["selector"]}§ | {ref(role,a["source_path"],a["line"])} | {cell(a["access"])}<br>{cell(params)} | {cell("; ".join(a["effects"]))}<br>{cell(a["value_flow"])} | {chains}<br>nonReentrant: {"yes" if a["reentrancy_guard"] else "no"} |'))
            lines.append('')
    lines.append('## Initialization\n\nConstructors run only at creation; inherited constructors execute in Solidity order. Stored template/initcode bytes need their own deployment binding before a concrete constructor can be attributed to a live address.\n\n| Constructor | Source | Inputs |\n| --- | --- | --- |')
    for a in snapshot['initialization']:
        lines.append(md(f'| §{a["contract"]}:{a["signature"]}§ | {ref(role,a["source_path"],a["line"])} | {cell("; ".join(p["name"]+": "+p["type"] for p in a["parameters"]) or "none")} |'))
    lines.append('\n## External Event Boundary\n\n[linkage.json](../linkage.json) records local possible events for every runtime action, including eventless and unresolved rows. [Cross-system links](../evidence/cross-system-links.json) bind named caller/callee paths and conditional built-in hook profiles. A configured address is not proved to run a source contract by this report. STATICCALL cannot persist logs; arbitrary mutable token, hook, provider and SphereX calls remain unresolved. Reverted paths leave no persistent logs. Constructors are separate from later callable actions.\n')
    return '\n'.join(lines)

def invariant_report(role):
    candidate=role=='candidate'
    guards=read(OUT/'evidence'/f'{role}-guards.json')['guards']
    q,pay,claim,close,transfer=(130,1023,315,205,105) if candidate else (104,667,253,232,86)
    base='src/market/WildcatMarketBase.sol';market='src/market/WildcatMarket.sol';wd='src/market/WildcatMarketWithdrawals.sol';token='src/market/WildcatMarketToken.sol'
    invariants=[
      ('Conservation','Yes','In the full market runtime, scaledTotalSupply equals the sum of account scaled balances plus scaledPendingWithdrawals at the end of each successful external call, after all paired storage writes complete.',
       f'Δ-pair: {ref(role,market,66 if candidate else 78)} and {ref(role,market,73 if candidate else 85)} add the same deposit amount; {ref(role,wd,q)} and {ref(role,wd,140 if candidate else 114)} move it from account to pending; {ref(role,base,pay)} through {ref(role,base,1031 if candidate else 675)} burn pending and total equally. Transfer writes at {ref(role,token,transfer)} and {ref(role,token,109 if candidate else 90)} conserve the account sum. Batched write-site search found these durable writers; constructor fields start at zero, and pure simulation helpers do not persist their memory copies.',
       'The aggregate market-token claim would differ from allocated account and queued balances.'),
      ('Conservation','Yes','A successful batch payment increases normalizedUnclaimedWithdrawals and that batch normalizedAmountPaid by the same amount, while reducing pending and total scaled supply by the same burn.',
       f'Δ-pair: {ref(role,base,1024 if candidate else 668)} and {ref(role,base,1028 if candidate else 672)}; paired scaled reductions at {ref(role,base,1025 if candidate else 669)} and {ref(role,base,1031 if candidate else 675)} occur in _applyWithdrawalBatchPayment without an external call between the writes.',
       'Reserved claim accounting would diverge from the batch payment record.'),
      ('Ratio','Yes','For each successful withdrawal claim, the recorded total is floor(batch.normalizedAmountPaid × status.scaledAmount / batch.scaledTotalAmount), evaluated before updating the claim; the paid increment is the checked difference from its prior total.',
       f'Δ-pair and ratio: {ref(role,wd,299 if candidate else 243)} computes newTotalWithdrawn; {ref(role,wd,303 if candidate else 247)} subtracts the old storage value before {ref(role,wd,claim)} assigns it and subtracts the same increment from normalizedUnclaimedWithdrawals. This is the only durable claim-total assignment; the getter copies storage to memory.',
       'An account could receive a payment inconsistent with its scaled share of the paid batch.'),
      ('StateMachine','Yes','A full market can transition from open to closed once; no scoped action reopens it.',
       f'edge: constructor isClosed=false at {ref(role,base,265 if candidate else 185)} → closeMarket isClosed=true at {ref(role,market,close)}. closeMarket rejects an already closed state; all state-write sites preserve this field except that transition.',
       'The close settlement assumptions could be reused after operations resume.')]
    hookfacts=read(PREP/f'{role}-hooks-facts.json')
    for h in hookfacts['invariant_candidates']:
        if h['category']=='CrossContract':continue
        if h['id'] not in ('hooks-known-lender-monotonic','hooks-temporary-reserve-expiry') and 'positive-minimum' not in h['id']:continue
        cites=[]
        for r in h['derivation']:
            path,line=r.rsplit(':',1);cites.append(ref(role,path,int(line)))
        sites=[]
        for r in h.get('all_write_sites',[]):
            if isinstance(r,str):path,line=r.rsplit(':',1);sites.append(ref(role,path,int(line)))
            else:sites.append(ref(role,r['path'],r['line']))
        kind='edge: false → true' if h['category']=='StateMachine' else 'temporal: tmp.expiry > 0 and block.timestamp >= tmp.expiry' if h['category']=='Temporal' else 'guard-lift: positive minimumDeposit requires the immutable deposit callback'
        if h['category']=='Bound':
            kind += ('; exact setter rejection predicate is newMinimumDeposit > 0 && !' + ('hookedMarket.depositHookEnabled' if h['id'].startswith('Periodic') else '_depositHookEnabled[market]')) if candidate else '; the setter has no equivalent callback-enable predicate'
        derivation=kind+'; '+', '.join(cites)+'. All write sites: '+', '.join(sites)+'. '+h.get('write_site_verification',h.get('gap',''))
        invariants.append((h['category'],'No' if h['on_chain'].startswith('No') else 'Yes',h['claim'],derivation,'The stated admission, term or remembered-lender relation would no longer describe the stored policy.'))
    if candidate:
        invariants.append(('StateMachine','Yes','A successful market borrower acceptance clears both pending fields and replaces the operational borrower and its revalidated principal atomically.',
          f'edge: pending actor at {ref(role,base,514)} → cleared pending slots and replacement borrower/principal at {ref(role,base,525)}. Request writes both pending fields at {ref(role,base,483)}; cancel clears both at {ref(role,base,500)}. Acceptance rechecks the stored expected principal in {ref(role,base,384)}. These are all writers of the pending address slots.',
          'Market authority and its sanctions identity could disagree with the accepted transfer.'))
    cross=[
      ('Yes','Withdrawal execution routes a sanctioned claimant to an escrow bound to the principal/borrower, account and underlying token; successful release pays that bound account.',
       f'{ref(role,wd,318 if candidate else 256)} selects escrow instead of the claimant; {ref(role,base,1113 if candidate else 754)} supplies the borrower identity and underlying asset.',
       f'{ref(role,"src/WildcatSanctionsSentinel.sol",135 if candidate else 121)} creates the deterministic escrow and constructor input; {ref(role,"src/WildcatSanctionsEscrow.sol",21 if candidate else 17)} fixes the account and token, and releaseEscrow reads the release predicate before paying that account.',
       'Sanctions custody could be associated with a different account or token.'),
      ('Yes','Successful wrapper deposit/mint accounting is checked against the actual change in the wrapped market scaled balance, under the generation-specific rounding convention.',
       f'{ref(role,"src/vault/Wildcat4626Wrapper.sol",316 if candidate else 216)} measures market scaled balances across transferFrom and compares minted shares; mint has its own measured path in the same source file.',
       f'{ref(role,token,91 if candidate else 72)} updates market account scaled balances using '+('floor' if candidate else 'half-up')+' conversion. The external asset must actually be the named in-scope market for this paired property.',
       'Wrapper share issuance would diverge from the scaled market claims received.')]
    if candidate:
        cross.append(('Yes','The named wrapper factory creates a nonzero wrapper before setting the market registration; the market admits only its immutable wrapperFactory and a currently empty slot.',
          f'{ref(role,"src/vault/Wildcat4626WrapperFactory.sol",160)} creates the contract and calls registerWrapper at line 162.',
          f'{ref(role,"src/market/WildcatMarketConfig.sol",63)} checks caller and empty slot before assigning it. The market body alone accepts zero; the nonzero property is limited to this factory path.',
          'A wrapper address could be inconsistent with the generation and factory selected by the market.'))
    economics=[('Yes','Batch payment converts interest-bearing scaled debt to normalized claim reserves; claiming reduces those reserves by the increment recorded as withdrawn.',
       'I-1 + I-2 + I-3; executeWithdrawal subtracts the same increment from normalizedUnclaimedWithdrawals before transferring it. This is claim bookkeeping, not a guarantee of borrower solvency.',
       'Queued scaled debt and paid normalized claims could be counted inconsistently.')]
    lines=[f'# Properties of `src/market/` and the hooks\n\n> Wildcat V2 | {PINS[role]} | {len(guards)} guards | {len(invariants)+len(cross)+len(economics)} inferred properties\n',
      'These are source-derived properties and explicit limits. On-chain “Yes” means the cited source paths enforce the bounded statement; no runtime property campaign result is claimed.\n',
      '## 1. Enforced Guards (Reference)\n\nExact rejection predicates appear below. Multiline predicates retain their source whitespace; each has a source location and purpose.\n']
    for g in guards:
        lines.append(f'#### {g["id"]}\n\n{T}{g["text"]}{T} · {ref(role,g["path"],g["line"])} · **Purpose:** {g["purpose"]}\n')
    lines.append('## 2. Inferred Invariants (Single-Contract)\n')
    for i,(category,onchain,claim,derivation,consequence) in enumerate(invariants,1):
        lines.append(f'#### I-{i}\n\n{T}{category}{T} · On-chain: **{onchain}**\n\n> {claim}\n\n**Derivation** — {derivation}\n\n**If violated** — {consequence}\n')
    lines.append('## 3. Inferred Invariants (Cross-Contract)\n')
    for i,(onchain,claim,caller,callee,consequence) in enumerate(cross,1):
        lines.append(f'#### X-{i}\n\nOn-chain: **{onchain}**\n\n> {claim}\n\n**Caller side** — {caller}\n\n**Callee side** — {callee}\n\n**If violated** — {consequence}\n')
    lines.append('## 4. Economic Invariants\n')
    for i,(onchain,claim,derivation,consequence) in enumerate(economics,1):
        lines.append(f'#### E-{i}\n\nOn-chain: **{onchain}**\n\n> {claim}\n\n**Follows from** — {derivation}\n\n**If violated** — {consequence}\n')
    return '\n'.join(lines),{'guards':len(guards),'single':len(invariants),'cross':len(cross),'economic':len(economics)}

def graph(role):
    candidate=role=='candidate'
    data={'title':'Wildcat V2 — '+role+' source '+PINS[role][:7],'nodes':[],'edges':[],'groups':[]}
    def node(id,label,subtitle,type,row):data['nodes'].append(dict(id=id,label=label,subtitle=subtitle,type=type,row=row))
    node('lender','Lender','Deposits and claims','actor',0)
    node('borrower','Borrower','Market operations','actor',0)
    node('owner','ArchController owner','Registration authority','actor',0)
    node('spherex_authority','SphereX admin / operator','Separate protection roles','actor',0)
    node('wrapper','Wildcat4626Wrapper','WrapperFactory / market-token shares','protocol',1)
    node('market','WildcatMarket'+(' / WildcatMarketRevolving' if candidate else ''),'Base / Token / Config / Withdrawals','protocol',1)
    node('factory','HooksFactory'+(' / HooksFactoryRevolving' if candidate else ''),'Templates and deployment','protocol',1)
    node('arch','WildcatArchController','Owner-controlled registry','protocol',1)
    node('hooks','OpenTermHooks / FixedTermHooks'+(' / PeriodicTermHooks' if candidate else ''),'BaseAccessControls / MarketConstraintHooks','protocol',2)
    node('sentinel','WildcatSanctionsSentinel','Borrower-specific overrides','protocol',2)
    node('asset','Underlying ERC20','External token behavior','external',2)
    node('engine','SphereX engine','Mutable external validator','external',2)
    if candidate:node('identity','WildcatBorrowerIdentityRegistry','Operational account → principal','protocol',2)
    node('providers','Role providers','External credential sources' if not candidate else 'AccessList / Merkle / token adapters','external' if not candidate else 'protocol',3)
    node('escrow','WildcatSanctionsEscrow','Account-bound custody','protocol',3)
    node('oracle','Chainalysis list','External sanctions source','external',3)
    node('provider_factories','Provider factories','AccessList / Merkle / token adapters' if candidate else 'Configured external factory','protocol' if candidate else 'external',3)
    if candidate:
        node('provider_tokens','Credential tokens','ERC20 / ERC721 / ERC1155 / ERC4626','external',4)
    edges=[('lender','wrapper','wrap claims'),('lender','market','deposit withdraw'),('borrower','market','borrow repay'),('borrower','factory','deploy market'),('owner','arch','manage registry'),
        ('wrapper','market','transfer claims'),('factory','market','create code'),('factory','arch','register market'),('factory','hooks','create hook'),
        ('market','hooks','run callback'),('market','sentinel','check sanctions'),('market','asset','move assets'),('market','engine','validate action'),
        ('arch','engine','allow sender'),('hooks','providers','check credential'),('sentinel','escrow','create custody'),('sentinel','oracle','read sanctions'),('escrow','asset','release assets'),('spherex_authority','arch','manage protection')]
    edges += [('hooks','provider_factories','create provider')]
    if candidate:edges += [('market','identity','resolve borrower'),('providers','provider_tokens','read eligibility')]
    data['edges']=[dict(zip(('from','to','label'),e)) for e in edges]
    assert len({e['label'] for e in data['edges']})==len(data['edges'])
    rows={n['id']:n['row'] for n in data['nodes']}
    assert all(abs(rows[e['from']]-rows[e['to']])<=1 for e in data['edges'])
    return data

def xray_report(role, snapshot, invariant_counts):
    c=role=='candidate';pin=PINS[role];nsloc=13621 if c else 7522
    root=ROOT/'.hexaemeron/sources'/role
    hist=read(root/'x-ray/git-security-analysis.json')
    supplement=read(PREP/f'{role}-history-supplement.json')
    shape=hist['repo_shape'];dev=hist['dev_patterns'];late=hist['late_changes']
    linecounts={m[1]:int(m[2]) for m in re.finditer(r'^(src/[^:\n]+): (\d+)$',(PREP/f'{role}-enumeration.txt').read_text(),re.M)}
    ast=read(PREP/f'{role}-ast.json')['sources']
    excluded=set()
    for path,unit in ast.items():
        decls=[n for n in unit['ast'].get('nodes',[]) if n.get('nodeType')=='ContractDefinition']
        if decls and all(n['contractKind']=='interface' for n in decls):excluded.add(path)
    groups=collections.defaultdict(int)
    for path,number in linecounts.items():
        if path in excluded:continue
        group='Markets' if '/market/' in path else 'Hooks and factories' if '/access/' in path or 'HooksFactory' in path else 'Libraries and types' if '/libraries/' in path or '/types/' in path else 'Wrappers' if '/vault/' in path else 'Providers' if '/providers/' in path else 'Read-only lenses' if '/lens/' in path else 'Registry, sanctions and guards'
        groups[group]+=number
    labels={'Markets':('WildcatMarket / Base / Config / Token / Withdrawals'+(' / Revolving' if c else ''),'Scaled balances, accrual, borrowing and withdrawals'),
      'Hooks and factories':('HooksFactory'+(' / HooksFactoryRevolving' if c else '')+'; OpenTermHooks / FixedTermHooks'+(' / PeriodicTermHooks' if c else ''),'Deployment, admission and term policy'),
      'Libraries and types':('FeeMath / MarketState / MarketEvents / HooksConfig','Accounting, dispatch and typed state'),
      'Wrappers':('Wildcat4626Wrapper / Wildcat4626WrapperFactory','Non-rebasing shares of market-token claims'),
      'Providers':('AccessList / Merkle / token role providers and factories','Credential eligibility and administration'),
      'Read-only lenses':('MarketLens'+(' / Core / Live / Aggregator' if c else ''),'Read-only derived views'),
      'Registry, sanctions and guards':('WildcatArchController / SanctionsSentinel / SanctionsEscrow'+(' / BorrowerIdentityRegistry' if c else '')+'; ReentrancyGuard / SphereX','Registration, custody, identity and execution gates')}
    table='\n'.join(f'| {g} | {labels[g][0]} | {n} | {labels[g][1]} |' for g,n in groups.items())
    commits=collections.Counter()
    for a in supplement['all_history_contributors']:commits[a['name']]+=a['commits']
    contributors='\n'.join(f'| {a["author"]} | {commits[a["author"]]} | +{a["lines_added"]} | {a["pct"]*100:.1f}% |' for a in dev['contributor_breakdown'])
    hotspots='\n'.join(f'| {p} | {n} | Current source path; historical modifications |' for p,n in supplement['hotspots'] if (root/p).exists())
    fixes='\n'.join(f'| [{x["sha"]}](https://github.com/wildcat-finance/v2-protocol/commit/{x["full_sha"]}) | {x["date"]} | {cell(x["subject"])} | {x["score"]} | {cell(x["reasons"][0])} |' for x in hist['fix_candidates'][:8] if x['score']>=5)
    danger='\n'.join(f'| {name} | {hist["dangerous_area_changes"][name]["commit_count"]} | '+', '.join(hist['dangerous_area_changes'][name]['files'][:3])+' |' for name in ['access_control','fund_flows','signatures','state_machines'])
    docs=read(PREP/'doc-inputs.json')
    nat=sum(len(re.findall(rb'@(notice|dev|param|return|inheritdoc|custom:)',p.read_bytes())) for p in root.glob('src/**/*.sol'))
    base_line=722 if c else 406;queue_line=96 if c else 80;deposit_line=43 if c else 55
    hookline=940 if c else 712;wrapline=316 if c else 216
    source_limit=('Named candidate verification inputs match these source bytes; candidate mainnet deployment is not established by the input ledger.' if c else
                  'This is the accepted deployed-comparison commit. Only the verification inputs named by the target ledger are matched to deployed evidence; the entire commit is not certified as every deployed market.')
    access_detail=('Operational borrower, registered principal, hooks administrator and registry-account administrator are separate authorities.' if c else
                   'The market borrower is immutable; the hooks borrower is fixed at hook creation and controls its provider and market-policy setters.')
    extra_surfaces=(f'\n- **Borrower transfer and identity** [I-10](invariants.md#i-10) — {ref(role,"src/market/WildcatMarketBase.sol",384)} resolves the pending principal again; compare registry changes with existing market and escrow identity.\n\n'
        f'- **Revolving debt attribution** [I-2](invariants.md#i-2) — {ref(role,"src/market/WildcatMarketRevolving.sol",98)} distinguishes explicit repayment from donated liquidity; trace inherited accrual and close paths.\n\n'
        f'- **Periodic timing policy** — {ref(role,"src/access/PeriodicTermHooks.sol",140)} retains four mainnet duration decisions; review their relation to withdrawal windows and delayed APR activation.\n' if c else '')
    doc_note=('Candidate specifications document floor rounding, identity and event attribution; the recorded audit-scope freeze differs from this commit, and complete finding/retest lineage was not reconstructed.' if c else
              'Core-Behavior.md says a supply cap stops withdrawals, while Terminology.md and deposit code apply it to deposits; treat that sentence as a documentation conflict.')
    debt=('### Technical Debt Markers\n\n| Source | Marker | Text |\n| --- | --- | --- |\n'+'\n'.join(f'| {ref(role,x["file"],x["line"])} | {x["type"]} | {x["text"]} |' for x in hist['tech_debt']['items'])+'\n' if c else
          'The debt-marker scan found zero uppercase markers; that does not mean there are no lowercase todo comments or unresolved design questions.\n')
    tier='EXPOSED' if c else 'FRAGILE'
    verdict=('The source-only rubric rates roles without an operational timelock as FRAGILE, then lowers one tier for four unresolved timing-policy TODOs.' if c else
             'The source-only rubric rates the access layer as FRAGILE because roles exist without a protocol-enforced operational timelock.')
    result=md(f"""# X-Ray Report

> Wildcat V2 | {nsloc} nSLOC | {pin[:7]} (§detached HEAD§) | Foundry | 26/09/26

## 1. Protocol Overview

**What it does:** Wildcat markets lend underlying ERC20 assets to an admitted borrower while accounting for transferable, interest-bearing lender claims and queued withdrawals.

- **Users:** Lenders supply and transfer claims; the borrower draws liquidity and funds repayments; executors can update accounting and claim paid withdrawals.
- **Core flow:** Deposit → borrow/repay → queue scaled claims → settle a batch → execute a normalized payment.
- **Key mechanism:** Scaled balances share an accrual factor; hook callbacks impose admission and term policy.
- **Token model:** The market token rebases through its scale factor; Wildcat4626Wrapper issues non-rebasing shares backed by market-token scaled balances.
- **Admin model:** ArchController ownership governs registration. Separate SphereX admin/operator slots govern protection configuration; ownership transfer does not transfer those roles. Borrower and hooks authority govern market and access operations.

See the [architecture diagram](architecture.svg). {source_limit}

### Contracts in Scope

| Subsystem | Key contracts | nSLOC | Role |
| --- | --- | ---: | --- |
{table}

The header retains the enumerator's exact {nsloc} nSLOC across all {108 if c else 62} source files. The subsystem rows exclude interface-only declarations; their {sum(linecounts.get(p,0) for p in excluded)} nSLOC remain in the source manifest and enumeration evidence. Vendored dependencies are outside those totals; inherited Solady actions are included in the callable map.

### How It Fits Together

The core trick: a lender's scaled claim persists while accrued interest changes its normalized value; batch payment burns the scaled debt and reserves a normalized withdrawal claim.

### Deposit and transfer

§§§text
WildcatMarket.deposit → _depositUpTo → OpenTermHooks / FixedTermHooks{(' / PeriodicTermHooks' if c else '')}.onDeposit
├─ asset.transferFrom(caller, market) — underlying moves before the paired scaled-account/supply writes
└─ WildcatMarketToken.transfer → hook.onTransfer → scaled from/to balance writes
§§§

### Withdrawal and sanctions

§§§text
queueWithdrawal → hook.onQueueWithdrawal → account balance becomes queued scaled debt
├─ _applyWithdrawalBatchPayment → burn scaled supply and reserve normalized claims
└─ executeWithdrawal → hook.onExecuteWithdrawal → claimant or WildcatSanctionsEscrow
§§§

### Wrapping

§§§text
Wildcat4626Wrapper.deposit / mint → WildcatMarketToken.transferFrom → measured scaled balance change
└─ withdraw / redeem → burn wrapper shares → WildcatMarketToken.transfer
§§§

### Deployment

§§§text
HooksFactory{(' / HooksFactoryRevolving' if c else '')} → stored template/initcode → hook.onCreateMarket → market constructor
└─ WildcatArchController.registerMarket → factory discovery events
§§§

Stored initcode must be bound separately before assigning the named constructor to a deployed address.

## 2. Threat & Trust Model

### Protocol Threat Profile

> **Uncollateralized lending** with **tokenized claim wrapping** and **external admission-policy hooks**.

There is no collateral liquidation price oracle in the reviewed lending core; sanctions and credentials are separate external data dependencies.

### Actors & Adversary Model

| Actor | Trust level | Capabilities |
| --- | --- | --- |
| Lender / market-token holder | Bounded by balances, sanctions and hooks | Deposits, transfers and queues claims; timing and access checks constrain withdrawal paths. |
| Borrower | Bounded market authority | Draws available liquidity, changes terms and closes a funded market; operational setters have no timelock. |
| ArchController owner | Trusted registration authority | Changes registered actors/factories immediately; ownership handover expiry is not an action delay. |
| SphereX admin / operator | Separate protection authorities | Admin changes the operator; operator changes the engine; either can propagate the engine to registered contracts. Ownable transfers do not change these slots. |
| {'Hooks administrator' if c else 'Hooks borrower'} | Trusted admission-policy authority | Manages providers and lender restrictions; named term setters add their own conditions. |
| Registered role provider | Bounded credential authority | Grants/revokes access; pull and validation responses cross a separate code boundary. |
| Withdrawal executor / repayment payer | Bounded by destination and accounting | May act for another claimant or repay another borrower's market; receives no arbitrary claim destination. |

{access_detail} Source code does not establish live signer arrangements, multisig membership or external engine policy.

See [entry-points.md](entry-points.md) for the complete permissionless and restricted action maps.

**Adversary ranking**

1. **Borrower or privileged-account compromise** — those actors control credit drawdown, registration or lender-admission policy.
2. **Lender or token operator** — balance movement and withdrawal timing meet shared accounting.
3. **External hook, credential or token implementation** — the market relies on code and return values outside its own storage.
4. **Transaction scheduler** — block timing and action order determine batch expiry and accrued state.

### Trust Boundaries

- **Borrower authority** — {ref(role,"src/market/WildcatMarket.sol",118 if c else 146)} permits immediate borrowing within source-defined reserves; repayment capacity remains an external credit question.
- **Registration and engines** — Owner-controlled registration is separate from SphereX configuration roles in {ref(role,"src/spherex/SphereXConfig.sol",142 if c else 141)}. These setters have no operational delay; SphereX callbacks can reject guarded actions at {ref(role,"src/spherex/SphereXProtectedRegisteredBase.sol",278 if c else 282)}.
- **Admission and terms** — {ref(role,"src/access/BaseAccessControls.sol",hookline)} accepts credentials through configured providers; term hooks also constrain forced sanctions queues.
- **Custody** — {ref(role,"src/market/WildcatMarketWithdrawals.sol",286 if c else 230)} separates the caller, claimant and possible escrow recipient.

No common protocol pause modifier was found on the reviewed action set; closure and external SphereX rejection have distinct, narrower semantics.

### Key Attack Surfaces

- **Scaled-account and batch settlement** [I-1](invariants.md#i-1), [I-2](invariants.md#i-2), [I-3](invariants.md#i-3) — {ref(role,"src/market/WildcatMarketBase.sol",base_line)} crosses accrual, batch expiry and claim reservations; trace the rounding at each conversion.

- **Wrapper and market rounding** [X-2](invariants.md#x-2) — {ref(role,"src/vault/Wildcat4626Wrapper.sol",wrapline)} measures market-token movement around share issuance; compare previews, transfers and redemption paths.

- **Hook configuration and remembered access** [I-5](invariants.md#i-5), [I-7](invariants.md#i-7), [I-8](invariants.md#i-8) — {ref(role,"src/access/OpenTermHooks.sol",189 if c else 175)} stores minimums separately from callback configuration; check creation and later administration together.

- **Sanctions custody and term policy** [X-1](invariants.md#x-1) — {ref(role,"src/market/WildcatMarket.sol",280 if c else 298)} uses the ordinary queue hook before custody can move to escrow.

- **Temporary reserve timing** [I-6](invariants.md#i-6) — {ref(role,"src/access/MarketConstraintHooks.sol",196 if c else 204)} changes caller-keyed temporary reserves only when an APR callback executes.
{extra_surfaces}
### Protocol-Type Concerns

- **Finite accrual fields** — FeeMath stores scaleFactor in uint112 and timestamps in uint32; {ref(role,"src/libraries/FeeMath.sol",1)} supplies the arithmetic, while lifetime estimates in specifications remain spec claims.
- **Explicit payment versus liquidity** — {ref(role,"src/market/WildcatMarket.sol",163 if c else 188)} emits DebtRepaid for an explicit payer action; a raw ERC20 donation has different attribution.

### Temporal Risk Profile

- **Initialization** — {ref(role,"src/market/WildcatMarketBase.sol",235 if c else 157)} reads construction parameters from its caller; deployed factory/initcode identity must come from separate evidence.
- **Closure** [I-4](invariants.md#i-4) — {ref(role,"src/market/WildcatMarket.sol",183 if c else 212)} settles queued scaled debt and fixes the closed-state rates before later claims continue.

### Composability & Dependency Risks

> **Underlying ERC20** — via LibERC20 and the market.
> - Assumes: balances and transfer amounts describe the accounting asset; fee-on-transfer or rebasing behavior is not normalized by an actual-received deposit check.
> - Validates: low-level call success and return shape; token availability and mutable implementation remain external.
> - On failure: the call reverts and its logs roll back.

> **Hook and credential implementations** — via HooksConfig and BaseAccessControls.
> - Assumes: configured addresses implement the intended admission/term behavior.
> - Validates: enabled callback return shape and local policy checks; pull probes have explicit fallback behavior.
> - On failure: callback revert rejects the host action; credential paths can try another provider according to the cited implementation.

> **Sanctions list** — via WildcatSanctionsSentinel.
> - Assumes: external list responses represent the desired sanctions policy.
> - Validates: local borrower/principal override namespace; raw borrower checks bypass those overrides.
> - On failure: the relevant read or action reverts.

> **SphereX engine** — via SphereXProtectedRegisteredBase.
> - Assumes: the configured external engine implements pre/post validation.
> - Mutability: ArchController controls the engine target; a zero engine bypasses its validation path.
> - On failure: a guarded operation reverts; other actions do not acquire a general pause.

## 3. Invariants

> **[Full invariant map](invariants.md)** — {invariant_counts['guards']} enforced guards; {invariant_counts['single']} single-contract properties; {invariant_counts['cross']} cross-contract properties; {invariant_counts['economic']} economic property. Each inferred block names its source derivation and enforcement limit.

## 4. Documentation Quality

| Aspect | Status | Notes |
| --- | --- | --- |
| README | Present | Repository orientation; it does not establish deployed code equality. |
| NatSpec | {nat} annotation markers detected | Count over src files; presence is separate from correctness. |
| Specifications | Present | Fresh extraction and source hashes retained in doc-inputs and the role extraction record. |
| Inline comments | Present | Accounting, packed state and assembly intent are documented; claims were checked against source before promotion. |

{doc_note} Source-only event mapping retains emitter and canonical ABI topics; off-chain role attribution still needs the accepted event-decision and deployment evidence.

## 5. Test Analysis

| Metric | Value | Source |
| --- | --- | --- |
| Test files | {82 if c else 72} | File enumeration |
| Test functions | {698 if c else 602} | File enumeration |
| Line coverage | Unavailable | {'Default solc compilation and --ir-minimum Yul compilation failed' if c else 'Default Solar analysis and --ir-minimum Yul compilation failed'} |
| Branch coverage | Unavailable | No completed coverage execution |

### Test Depth

| Category | Count | Evidence limit |
| --- | ---: | --- |
| Test functions (unit/integration not individually partitioned) | {698 if c else 602} | Names detected, no pass claim |
| Stateless fuzz | {31 if c else 21} | Function-name scan |
| Foundry invariants | {9 if c else 8} | Function-name scan |
| Formal verification | 0 | No Certora/Halmos/HEVM signals in the prescribed scan |

### Gaps

- No Echidna/Medusa, formal-verification or fork-test signals were detected by the prescribed enumeration.
- Coverage cannot be quantified: {'default compilation reports Stack too deep at script/deploy/v2-5/02-deploy-hooks-factory-standard.s.sol:342; the IR fallback reports a six-slot var_deployments/var_result Yul stack excess' if c else 'default Solar analysis reports an unresolved locals symbol at src/spherex/SphereXProtectedRegisteredBase.sol:153:39; the IR fallback reports a three-slot var_market Yul stack excess'}. Exact commands and logs are retained.

## 6. Developer & Git History

> Normal development history: {shape['source_touching_commits']} source-touching commits among {shape['total_commits']} ancestors of detached HEAD §{pin}§, spanning {shape['date_spread_days']} days.

### Contributors

| Recorded author name | All-history commits | Source lines added | Share of source additions |
| --- | ---: | ---: | ---: |
{contributors}

Names are Git author labels, not verified people; identical names from several email identities are aggregated here. Source-addition shares and all-history commit counts have different denominators.

### Review & Process Signals

| Signal | Value | Interpretation |
| --- | --- | --- |
| Merge commits | {supplement['merge_commits']} of {shape['total_commits']} | Merge topology does not prove independent review |
| History dates | {shape['first_commit_date']} → {shape['last_commit_date']} | Ancestors of this pin only |
| Source activity in final 30-day window | {late['total_late_source_commits']} | Window ends at the pin's latest commit |
| Test co-change | {dev['test_co_change_rate']*100:.1f}% | Source commits that also change test files; not coverage |
| Fix-scored commits without test-file changes | {dev['fix_without_test_rate']*100:.1f}% | Heuristic subset; not proof of absent tests |

### File Hotspots

| Current file | Modifications | Scope |
| --- | ---: | --- |
{hotspots}

### Security-Relevant Commits

The script scores message/diff features for navigation; historical subjects do not establish a present vulnerability or completed repair. The full scored list is retained with the pin.

| Commit | Date | Historical subject | Score | Leading script signal |
| --- | --- | --- | ---: | --- |
{fixes}

### Dangerous Area Evolution

| Heuristic area | Commits | Example paths |
| --- | ---: | --- |
{danger}

Keyword matches under oracle/liquidation headings are not evidence that this credit core implements a price oracle or liquidation mechanism.

### Forked Dependencies

The pin includes {len(hist['forked_deps']['detected_libs'])} Git submodules. Inherited Solady Ownable/ERC20 behavior is read and hash-bound. LibERC20 is an internalized transfer helper and SphereX is adapted source; mixed pragma scans alone do not establish a departure from upstream behavior.

{debt}
### Security Observations

- **Source concentration** — {dev['top_contributor']} accounts for {dev['single_developer_pct']*100:.1f}% of recorded source additions.
- **Recent activity** — {late['total_late_source_commits']} source commits fall in the final 30-day window; {late['source_without_test_count']} omit a test-file change in the same commit.
- **Accounting history** — MarketBase and withdrawal source remain among the current-file hotspots.
- **Evidence separation** — neither merge counts nor fix-scored subjects establish review completion or deployed behavior.

### Cross-Reference Synthesis

- **Accounting priority** — repeated MarketBase/Withdrawals edits coincide with the scaled settlement and claim paths in I-1 through I-3.
- **Access priority** — hook/provider and engine change history supplies reading order for the documented trust boundaries.
- **Execution limit** — the detected tests inform the structural rubric; failed coverage remains an independent tool result.

## X-Ray Verdict

**{tier}** — {verdict}

This tier describes the template's structural evidence rubric; it is not a security, deployment or credit-solvency verdict. Tests reach its HARDENED presence threshold, documentation includes specifications, and live multisig arrangements were not established.

**Structural facts:**

1. {108 if c else 62} source files contain {nsloc} enumerated nSLOC.
2. The source action inventory contains {len(snapshot['actions'])} callable contract/signature contexts and {len(snapshot['initialization'])} separate constructors.
3. The scan detects {698 if c else 602} test functions, {31 if c else 21} stateless fuzz functions and {9 if c else 8} Foundry invariant functions.
4. Both attempted coverage modes fail before producing coverage metrics.
""")
    assert len(result.splitlines())<500
    return result

def produce():
    bundle=read(OUT/'linkage.json')
    for role in PINS:
        inv,counts=invariant_report(role)
        contents={'invariants.md':inv,'entry-points.md':entry_report(role,bundle['snapshots'][role]),
            'x-ray.md':xray_report(role,bundle['snapshots'][role],counts),
            'architecture.json':json.dumps(graph(role),indent=2)+'\n'}
        contents = {name:surface(value) if name.endswith('.md') else value for name,value in contents.items()}
        folder=OUT/role;folder.mkdir(parents=True,exist_ok=True)
        # Four independent report views are written together after analysis is complete.
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda item:(folder/item[0]).write_text(item[1]),contents.items()))
        print(role,{name:len(text.splitlines()) for name,text in contents.items()})

if __name__=='__main__':produce()
