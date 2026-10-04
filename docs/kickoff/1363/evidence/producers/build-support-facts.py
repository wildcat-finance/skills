"""Issue 1363 source-fact extraction; local study artifact, not a product verifier."""
import copy, hashlib, json, re, subprocess
from pathlib import Path
RUN=Path.cwd(); PREP=RUN/'.hexaemeron/xray-preparation'
PINS={'deployed':'f5a26146987926f4811b72a795d662813dedfe85','candidate':'bea503c2736d47de7fd34130c64f10783dc35b39'}
def own(path):
 return path.startswith('src/') and not path.startswith(('src/market/','src/access/','src/libraries/','src/types/')) and not Path(path).name.startswith('HooksFactory')
def walk(x):
 if isinstance(x,dict):
  if 'nodeType' in x: yield x
  for v in x.values(): yield from walk(v)
 elif isinstance(x,list):
  for v in x: yield from walk(v)

def semantic(contract,name,label):
 c=label=='candidate'; A={'access':'permissionless','caller_checks':[],'effects':[],'value_flow':'none','external_boundary':[],'conditions':[],'delta_writes':[],'event_notes':[]}
 def put(access=None,checks=(),effects=(),value='none',calls=(),conditions=(),deltas=(),events=()):
  A.update(access=access or A['access'],caller_checks=list(checks),effects=list(effects),value_flow=value,external_boundary=list(calls),conditions=list(conditions),delta_writes=list(deltas),event_notes=list(events));return A
 if contract=='WildcatArchController':
  sets={'registerBorrower':('_borrowers','add'),'removeBorrower':('_borrowers','remove'),'addBlacklist':('_assetBlacklist','add'),'removeBlacklist':('_assetBlacklist','remove'),'registerControllerFactory':('_controllerFactories','add'),'removeControllerFactory':('_controllerFactories','remove'),'registerController':('_controllers','add'),'removeController':('_controllers','remove'),'registerMarket':('_markets','add'),'removeMarket':('_markets','remove')}
  if name in sets:
   v,op=sets[name]; role='admin-only: current Ownable owner';checks=['onlyOwner -> Ownable._checkOwner: msg.sender equals stored owner']
   if name=='registerController':role='role-gated: registered controller factory';checks=['onlyControllerFactory: _controllerFactories.contains(msg.sender)']
   if name=='registerMarket':role='role-gated: registered controller';checks=['onlyController: _controllers.contains(msg.sender)']
   calls=['SphereX engine.addAllowedSenderOnChain(address) if engine is nonzero'] if name in ('registerControllerFactory','registerController','registerMarket') else []
   return put(role,checks,[f'{v}.{op}(address); rejects unchanged membership'],calls=calls,events=['Registration emits NewAllowedSenderOnchain as well as the registry event only when the SphereX engine is nonzero.'] if calls else [])
  if name=='updateSphereXEngineOnRegisteredContracts':return put('role-gated: SphereX operator or admin',['spherexOnlyOperatorOrAdmin; every supplied address must belong to its matching registry'],['pushes current engine to selected contracts; registers allowed senders on nonzero engine'],calls=['selected registered contract.changeSphereXEngine(engine)','nonzero engine.addAllowedSenderOnChain(account)'],conditions=['empty arrays perform no updates and emit no local events','engine zero suppresses NewAllowedSenderOnchain; target changes can still emit ChangedSpherexEngineAddress','one failed target update reverts the batch'],events=['Local NewAllowedSenderOnchain is assembly-backed and emitted per target only for nonzero engine.'])
 if name in ('transferOwnership','renounceOwnership','requestOwnershipHandover','cancelOwnershipHandover','completeOwnershipHandover'):
  changes={'transferOwnership':['owner = newOwner'],'renounceOwnership':['owner = zero'],'requestOwnershipHandover':['handoverExpiry[msg.sender] = block.timestamp + 172800'],'cancelOwnershipHandover':['handoverExpiry[msg.sender] = 0'],'completeOwnershipHandover':['handoverExpiry[pendingOwner] = 0','owner = pendingOwner']}
  chk=[] if name in ('requestOwnershipHandover','cancelOwnershipHandover') else ['onlyOwner -> _checkOwner assembly compares caller() to owner slot']
  cond=['48-hour request validity is an expiry, not an operational timelock; direct owner operations remain immediate']
  if name=='completeOwnershipHandover':chk+=['timestamp() <= sload(handoverSlot)']
  return put('admin-only: current Ownable owner' if chk else 'permissionless',chk,changes[name],value='optional native ETH from caller to contract because inherited action is payable; no token movement',conditions=cond,events=['Ownable events are emitted with assembly log2/log3; not Solidity EmitStatement.'])
 if name in ('transferSphereXAdminRole','acceptSphereXAdminRole','changeSphereXOperator','changeSphereXEngine'):
  roles={'transferSphereXAdminRole':'current SphereX admin','acceptSphereXAdminRole':'pending SphereX admin','changeSphereXOperator':'current SphereX admin','changeSphereXEngine':'SphereX operator' if contract!='SphereXProtectedRegisteredBase' else 'immutable ArchController'}
  changes={'transferSphereXAdminRole':['pending SphereX admin = newAdmin'],'acceptSphereXAdminRole':['SphereX admin = msg.sender','pending SphereX admin = zero'],'changeSphereXOperator':['SphereX operator = newSphereXOperator'],'changeSphereXEngine':['SphereX engine = newSphereXEngine']}
  return put('role-gated: '+roles[name],[('body msg.sender == pendingSphereXAdmin()' if name=='acceptSphereXAdminRole' else 'declared SphereX role modifier')],changes[name],calls=['nonzero engine.supportsInterface(ISphereXEngine)'] if name=='changeSphereXEngine' and contract!='SphereXProtectedRegisteredBase' else [],conditions=['zero engine disables pre/post validation'] if name=='changeSphereXEngine' else ['two-step acceptance; no elapsed-time delay'],events=['Events reach free emit_* helpers in SphereXProtectedEvents.sol and their assembly log1 sites.'])
 if contract=='WildcatBorrowerIdentityRegistry':
  roles={'addAccountFactory':'current ArchController owner','removeAccountFactory':'current ArchController owner','registerBorrowerAccount':'approved account factory','requestBorrowerAccountPrincipalTransfer':'account current principal','cancelBorrowerAccountPrincipalTransfer':'account current principal','acceptBorrowerAccountPrincipalTransfer':'account pending principal'}
  effects={'addAccountFactory':['_accountFactories.add(accountFactory)'],'removeAccountFactory':['_accountFactories.remove(accountFactory)'],'registerBorrowerAccount':['principalOf[account] = principal','accountFactoryOf[account] = msg.sender','_borrowerAccounts[principal].add(account)','_borrowerAccountsForFactory[msg.sender].push(account)'],'requestBorrowerAccountPrincipalTransfer':['pendingPrincipalOf[account] = newPrincipal'],'cancelBorrowerAccountPrincipalTransfer':['delete pendingPrincipalOf[account]'],'acceptBorrowerAccountPrincipalTransfer':['delete pendingPrincipalOf[account]','_borrowerAccounts[previousPrincipal].remove(account)','_borrowerAccounts[newPrincipal].add(account)','principalOf[account] = newPrincipal']}
  checks={'addAccountFactory':['onlyArchControllerOwner -> current external ArchController.owner()'],'removeAccountFactory':['onlyArchControllerOwner -> current external ArchController.owner()'],'registerBorrowerAccount':['onlyAccountFactory: _accountFactories.contains(msg.sender)'],'requestBorrowerAccountPrincipalTransfer':['body msg.sender == _getAccountPrincipal(account)'],'cancelBorrowerAccountPrincipalTransfer':['body msg.sender == _getAccountPrincipal(account)'],'acceptBorrowerAccountPrincipalTransfer':['body msg.sender == pendingPrincipalOf[account]']}
  return put(('admin-only: ' if name in ('addAccountFactory','removeAccountFactory') else 'role-gated: ')+roles[name],checks[name],effects[name],calls=['ArchController.owner() or isRegisteredBorrower(address) as selected by helper'],conditions=['factory removal does not erase accounts already registered; registry principal transfer does not rewrite market borrower state','registration and acceptance reject ambiguous account/principal identities; principal must be currently registered'],events=['BorrowerAccountPrincipalTransfer events belong to registry account identity, distinct from market BorrowerTransfer events.'])
 if contract=='WildcatSanctionsSentinel':
  if name in ('overrideSanction','removeSanctionOverride'):return put(effects=[f'sanctionOverrides[msg.sender][account] = {str(name=="overrideSanction").lower()}'],conditions=['caller affects only its own borrower namespace; no registered-borrower caller check'])
  return put(effects=['temporary escrow parameters set then reset to address(1) tuple','CREATE2 escrow for (borrower, account, asset)','sanctionOverrides[borrower][escrow] = true'],calls=['new WildcatSanctionsEscrow constructor reads sentinel.tmpEscrowParams()'],conditions=['existing escrow code causes immediate return with no writes or event','new deployment emits NewSanctionsEscrow then SanctionOverride; no token transfer in this function'])
 if contract=='WildcatSanctionsEscrow':return put(effects=['no local mutable balance ledger'],value='all escrowed ERC20 asset balance -> immutable account',calls=['sentinel.isSanctioned(immutable borrower, immutable account)','asset.balanceOf(this)','asset.transfer(account, amount)'],conditions=['any caller may release when original borrower namespace permits it; caller is not recipient','EscrowReleased logs transfer request amount; external token effects depend on that token'])
 if contract.endswith('RoleProviderFactory'):
  provider=contract[:-7]
  return put(effects=['CREATE2 provider; factory retains no mutable storage registry'],calls=[f'new {provider}(caller-supplied constructor inputs)'],conditions=['salt = keccak256(abi.encode(msg.sender, inputs.salt)); predicted address must have no code','bytes overload ABI-decodes inputs; typed overload passes same inputs'],events=([f'{provider}Deployed is emitted by factory; AccessListRoleProvider constructor emits MemberAdded for each initial member'] if provider=='AccessListRoleProvider' else [f'{provider}Deployed is emitted after constructor succeeds']))
 if name in ('requestAdministratorTransfer','cancelAdministratorTransfer','acceptAdministratorTransfer'):
  changes={'requestAdministratorTransfer':['pendingAdministrator = newAdministrator'],'cancelAdministratorTransfer':['pendingAdministrator = zero'],'acceptAdministratorTransfer':['pendingAdministrator = zero','administrator = prior pendingAdministrator']}
  return put('role-gated: '+('pending provider administrator' if name=='acceptAdministratorTransfer' else 'provider administrator'),['msg.sender == pendingAdministrator (body)' if name=='acceptAdministratorTransfer' else 'onlyAdministrator: msg.sender == administrator'],changes[name],conditions=['provider authority is independent of hooks authority and ArchController registration; no elapsed-time delay'])
 if contract=='AccessListRoleProvider':
  add=name.startswith('add');return put('role-gated: provider administrator',['onlyAdministrator -> msg.sender == administrator'],[f'_members.{"add" if add else "remove"}(account) per input'],conditions=['empty batch emits no MemberAdded/MemberRemoved; each successful change emits one','adding zero address or duplicate, or removing absent member, reverts whole transaction'])
 if contract=='MerkleRoleProvider':return put('role-gated: provider administrator',['onlyAdministrator -> msg.sender == administrator'],['root = newRoot'],conditions=['hook-side cached credentials persist according to hook TTL; replacing root does not clear them'])
 if contract=='Wildcat4626Wrapper':
  hook='live principal sanctions and wrapper solvency with deterministic-escrow exceptions' if c else 'sanctions checks on nonzero from/to against immutable marketOwner'
  if name=='approve':return put(effects=['allowance[msg.sender][spender] = amount'],conditions=['no _beforeTokenTransfer call or sanctions check; no asset movement'],events=['Approval emitted by assembly log3 in ERC20.approve'])
  if name=='permit':return put(effects=['nonce[owner] += 1 on successful signature recovery','allowance[owner][spender] = value'],calls=['ecrecover precompile 0x01'],conditions=['valid owner signature and unexpired deadline required; anyone may relay; no _beforeTokenTransfer call'],events=['Approval emitted by assembly log3 in ERC20.permit'])
  if name in ('transfer','transferFrom'):
   return put(effects=['wrapper share balances debit from and credit to','finite allowance[from][msg.sender] decreases for transferFrom'],value='wrapper shares between holders; underlying market tokens remain held by wrapper',calls=['_beforeTokenTransfer -> '+hook],conditions=['sufficient share balance; transferFrom requires allowance even if caller == from','inherited actions have no nonReentrant modifier'],deltas=['delta(balance[from]) = -amount','delta(balance[to]) = +amount'],events=['Transfer emitted by assembly log3; spending allowance emits no Approval'])
  if name in ('deposit','mint'):
   return put(effects=['wrapper totalSupply and receiver share balance increase','underlying market-token scaled balance increases'],value='market tokens: caller -> wrapper; wrapper shares minted to receiver',calls=['market.scaleFactor and scaledBalanceOf reads','LibERC20.safeTransferFrom -> wrapped market transferFrom','ERC20._mint -> wrapper._beforeTokenTransfer -> '+hook],conditions=(['execution expects floor-scaled transfer amount exactly; deposit equality rather than lower bound','solvency checked before operation and after mint; live recipient transfer policy must allow wrapper'] if c else ['execution uses half-up market scaling; deposit accepts scaled increase >= expected; mint requires equality','capacity = market.maxTotalSupply - wrapper normalized token holdings']),deltas=['ERC20._mint: delta(totalSupply) = +shares; delta(balance[receiver]) = +shares'],events=['Wrapper emits mint Transfer via ERC20._mint then Deposit; wrapped-market Transfer and possible hooks events are emitted by external target, not wrapper'])
  if name in ('withdraw','redeem'):
   return put(effects=['wrapper totalSupply and owner share balance decrease','finite delegated allowance decreases','underlying scaled backing decreases'],value='market tokens: wrapper -> receiver; owner wrapper shares burned',calls=['ERC20._burn -> wrapper._beforeTokenTransfer -> '+hook,'LibERC20.safeTransfer -> wrapped market transfer'],conditions=['delegated caller requires allowance; sufficient owner shares']+(['withdraw floor-scales assets; redeem ceil-converts shares to normalized assets; exact scaled debit check and post-operation solvency'] if c else ['withdraw half-up scales assets; redeem half-up normalizes shares; exact scaled debit check']),deltas=['ERC20._burn: delta(totalSupply) = -shares; delta(balance[owner]) = -shares'],events=['Wrapper emits burn Transfer via ERC20._burn then Withdraw; wrapped-market Transfer and hooks events are external-target events'])
  if name=='sweep':return put('role-gated: '+('live market borrower' if c else 'immutable marketOwner'),['body caller equality check; nonReentrant alone is not authority'],['no share supply/balance writes'],value='ERC20: wrapper -> to; wrapped-market token limited to surplus above wrapper shares',calls=['token.balanceOf and token.transfer','wrapped-market scaleFactor/scaledBalanceOf for surplus route','sentinel sanctions check for recipient'],conditions=['nonzero token/to, recipient not sanctioned, nonzero recoverable amount','wrapped-market route verifies exact scaled debit equals backing surplus'],events=['TokensSwept emitted on both successful branches'])
  if name=='nukeFromOrbit':return put(effects=['_authorizedEscrows[escrow] = true when holder shares are nonzero','wrapper share balances move holder -> deterministic escrow'],value='holder market position quarantined by market; holder wrapper shares -> escrow; wrapper market backing is not redeemed',calls=['wrappedMarket.call(full original calldata) -> WildcatMarket.nukeFromOrbit(account)','sentinel.createEscrow(live borrowerPrincipal, account, wrapper)','ERC20._transfer -> wrapper._beforeTokenTransfer'],conditions=['account != wrapper and account currently sanctioned','market call occurs even if wrapper share balance is zero; zero shares then return with no wrapper event','nonzero shares emit Transfer plus SanctionedAccountSharesSentToEscrow; sentinel new-escrow events conditional'],deltas=['ERC20._transfer: delta(balance[account]) = -shares; delta(balance[escrow]) = +shares'])
 if contract=='Wildcat4626WrapperFactory':
  return put(effects=['one wrapper mapping entry set for locally supported market generation'],calls=(['rounding probe','legacy branch: v1Factory.createWrapper(market)','local branch: market hooks transfer-policy queries','new Wildcat4626Wrapper(market)','market.registerWrapper(wrapper)'] if c else ['archController.isRegisteredMarket(market)','new Wildcat4626Wrapper(market)']),conditions=(['existing local wrapper rejects','undeclared rounding routes to configured V1 factory; no local WrapperDeployed event on that return path','declared unknown rounding rejects; local floor-rounding market requires registration, transfers enabled and both policy queries','local wrapper constructor checks market.wrapperFactory == deployer'] if c else ['nonzero registered market; wrapperForMarket[market] must be zero']),events=['WrapperDeployed only after successful local deployment; external legacy factory event retains legacy emitter'] if c else ['WrapperDeployed after deployment and mapping write'])
 raise ValueError((contract,name,label))

def build(label):
 root=RUN/'.hexaemeron/sources'/label
 assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PINS[label]
 raw=(PREP/f'{label}-ast.json').read_bytes(); ast=json.loads(raw); nodes={}; paths={}; sources={}
 for p,u in ast['sources'].items():
  b=(root/p).read_bytes();sources[p]=b
  for n in walk(u['ast']):
   if 'id' in n:nodes[n['id']]=n;paths[n['id']]=p
 source_ids={u['id']:p for p,u in ast['sources'].items()}
 def path(n):return source_ids[int(n['src'].split(':')[2])]
 def txt(n):
  start,size,_=map(int,n['src'].split(':'));return sources[path(n)][start:start+size].decode()
 def loc(n):
  p=path(n);start=int(n['src'].split(':')[0]);return {'path':p,'line':sources[p][:start].count(b'\n')+1}
 def ref(n):return dict(loc(n),text=txt(n))
 def params(n):return [{'name':p['name'],'type':p['typeDescriptions']['typeString'],'indexed':p.get('indexed',False)} for p in n['parameters']['parameters']]
 def event(n):return dict(loc(n),name=n['name'],signature=n['name']+'('+','.join(p['typeDescriptions']['typeString'] for p in n['parameters']['parameters'])+')',topic0='0x'+n['eventSelector'],fields=params(n))
 events={n['id']:event(n) for n in nodes.values() if n['nodeType']=='EventDefinition'}
 def extracted(fn):
  out={'name':fn.get('name',fn.get('kind')),'kind':fn['nodeType'],'location':loc(fn),'visibility':fn.get('visibility'),'mutability':fn.get('stateMutability'),'calls':[],'guard_predicates':[],'writes':[],'events':[]}
  for n in walk(fn.get('body',{})):
   typ=n['nodeType']
   if typ=='FunctionCall':
    ex=n['expression']; nt=ex['nodeType']; ts=ex.get('typeDescriptions',{}).get('typeString','')
    if n.get('kind')=='functionCall':out['calls'].append(dict(loc(n),expression=txt(n),declaration=ex.get('referencedDeclaration'),call_type='external' if ' external' in ts or (nt=='MemberAccess' and ex.get('memberName') in ('call','staticcall','delegatecall')) else 'internal-or-builtin'))
    if nt=='Identifier' and ex.get('name') in ('require','assert'):out['guard_predicates'].append(dict(loc(n),predicate=txt(n['arguments'][0]),form=ex['name']))
   elif typ=='IfStatement':
    body=n.get('trueBody',{}); children=list(walk(body))
    if any(x['nodeType']=='RevertStatement' or x['nodeType']=='FunctionCall' and x.get('expression',{}).get('name','').startswith('revert_') for x in children):out['guard_predicates'].append(dict(loc(n),predicate=txt(n['condition']),form='if-revert'))
   elif typ=='YulIf':
    if any(x['nodeType']=='YulFunctionCall' and x.get('functionName',{}).get('name')=='revert' for x in walk(n.get('body',{}))):out['guard_predicates'].append(dict(loc(n),predicate=txt(n['condition']),form='assembly-if-revert'))
   elif typ in ('Assignment','UnaryOperation'):
    left=n.get('leftHandSide',n.get('subExpression',{}));ids=[x.get('referencedDeclaration') for x in walk(left)]
    if any(nodes.get(i,{}).get('stateVariable') or nodes.get(i,{}).get('storageLocation')=='storage' for i in ids):out['writes'].append(dict(loc(n),expression=txt(n),kind='direct-storage'))
   elif typ=='FunctionCall' and n.get('expression',{}).get('memberName') in ('add','remove','push','pop'):
    pass
   elif typ=='YulFunctionCall' and n.get('functionName',{}).get('name') in ('sstore','tstore'):
    out['writes'].append(dict(loc(n),expression=txt(n),kind='assembly-storage'))
   elif typ=='EmitStatement':
    call=n['eventCall'];ev=events.get(call['expression'].get('referencedDeclaration'))
    out['events'].append(dict(loc(n),expression=txt(n),event=ev))
  for n in walk(fn.get('body',{})):
   if n['nodeType']=='FunctionCall' and n.get('expression',{}).get('memberName') in ('add','remove','push','pop'):
    ids=[x.get('referencedDeclaration') for x in walk(n['expression'].get('expression',{}))]
    if any(nodes.get(i,{}).get('stateVariable') or nodes.get(i,{}).get('storageLocation')=='storage' for i in ids):out['writes'].append(dict(loc(n),expression=txt(n),kind='storage-helper-call'))
  return out
 files=[]
 for p in sorted(sources):
  if not own(p):continue
  unit=ast['sources'][p]['ast'];decls=[n for n in unit['nodes'] if n['nodeType']=='ContractDefinition'];logical=[n for n in decls if n['contractKind']!='interface'];free=[n for n in unit['nodes'] if n['nodeType']=='FunctionDefinition']
  info={'path':p,'sha256':hashlib.sha256(sources[p]).hexdigest(),'bytes':len(sources[p]),'lines':len(sources[p].splitlines()),'disposition':'included-source' if logical or free else 'interface-or-data-declarations-no-runtime-action','imports':[n['absolutePath'] for n in unit['nodes'] if n['nodeType']=='ImportDirective'],'contracts':[],'free_functions':[extracted(n) for n in free]}
  for con in decls:
   facts={'name':con['name'],'type':('abstract ' if con.get('abstract') else '')+con['contractKind'],'inherits':[txt(n['baseName']) for n in con['baseContracts']],'state_variables':[dict(loc(n),name=n['name'],type=n['typeDescriptions']['typeString'],mutability=n['mutability']) for n in con['nodes'] if n['nodeType']=='VariableDeclaration'],'functions':[extracted(n) for n in con['nodes'] if n['nodeType'] in ('FunctionDefinition','ModifierDefinition') and n.get('body')],'declared_events':[events[n['id']] for n in con['nodes'] if n['nodeType']=='EventDefinition']}
   info['contracts'].append(facts)
  if p.startswith('src/lens/'):
   info['semantic_note']='Read-only lens/data helper: memory output assembly and external static reads; no token transfers, persistent writes, or non-view public/external actions after construction. Optional probes can omit absent/failed metadata.'
  if p.startswith('src/spherex/'):
   info['semantic_note']='Included modified SphereX integration, not silently excluded as vendor: runtime inherited management, assembly event helpers and engine pre/post calls are part of the target surface.'
  files.append(info)
 runtime=json.loads((PREP/f'{label}-runtime-denominator.json').read_text())
 actions=[]
 def closure(fn):
  seen=set();stack=[fn];result=[]
  while stack:
   x=stack.pop()
   if x['id'] in seen:continue
   seen.add(x['id']);result.append(x)
   for n in walk(x.get('body',{})):
    if n['nodeType']=='FunctionCall':
     ex=n['expression'];nd=nodes.get(ex.get('referencedDeclaration'))
     if nd and nd['nodeType']=='FunctionDefinition' and nd.get('body') and not ' external' in ex.get('typeDescriptions',{}).get('typeString',''):stack.append(nd)
  return result
 for row in runtime['actions']:
  if not own(row['contract_path']):continue
  fn=nodes[row['function_id']]; a=copy.deepcopy(row);a['selector']='0x'+a['selector'];a['signature']=fn['name']+'('+','.join(p['typeDescriptions']['typeString'].replace(' memory','').replace(' calldata','') for p in fn['parameters']['parameters'])+')';a['parameters']=[dict(x,trust='user-signed' if fn['name']=='permit' else 'user-controlled') for x in params(fn)];a['state_mutability']=fn['stateMutability'];a['modifiers']=[txt(m) for m in fn['modifiers']];a['non_reentrant']='nonReentrant' in a['modifiers'];a.update(semantic(row['contract'],row['function'],label));a['direct_extraction']=extracted(fn);a['reachable_local_events']=[];a['assembly_log_sites']=[]
  for f in closure(fn):
   for e in extracted(f)['events']:a['reachable_local_events'].append(dict(e,reaching_function=f.get('name'),reaching_location=loc(f)))
   for n in walk(f.get('body',{})):
    if n['nodeType']=='YulFunctionCall' and re.fullmatch('log[0-4]',n.get('functionName',{}).get('name','')):a['assembly_log_sites'].append(dict(loc(n),expression=txt(n),reaching_function=f.get('name')))
  a['event_disposition']='source-linked local emits or assembly logs; external-target event conditions require the stated external boundary' if a['reachable_local_events'] or a['assembly_log_sites'] else 'no event in direct body or resolved internal helper closure; inspect branch-specific external boundary'
  actions.append(a)
 inherited=[]
 for p in ('lib/solady/src/auth/Ownable.sol','lib/solady/src/tokens/ERC20.sol','lib/solady/src/tokens/ERC4626.sol'):
  b=(root/p).read_bytes();inherited.append({'path':p,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'disposition':'inherited runtime and event declarations reviewed; same bytes independently hashed in both source trees'})
 abstract=[]
 for n in nodes.values():
  if n['nodeType']=='ContractDefinition' and n.get('abstract') and own(paths[n['id']]):
   for f in n['nodes']:
    if f['nodeType']=='FunctionDefinition' and f.get('implemented') and f.get('visibility') in ('public','external') and f.get('stateMutability') not in ('view','pure') and f['kind']=='function':abstract.append({'contract':n['name'],'location':loc(f),'selector':'0x'+f['functionSelector'],'function':f['name'],'signature':f['name']+'('+','.join(p['typeDescriptions']['typeString'] for p in f['parameters']['parameters'])+')','semantics':semantic(n['name'],f['name'],label)})
 data={'schema':'issue-1363-support-source-facts/v1','producer':'/root/xray_support','snapshot':label,'commit':PINS[label],'ast_sha256':hashlib.sha256(raw).hexdigest(),'method':'Direct reads of logical support source at this pin; compiler AST used for exact selectors/locations and mechanical conditions/writes/events; runtime inventory reconciled separately. Interface-only files are declaration inventory, not callable implementations. No protocol writes or execution claims.','files':files,'inherited_sources':inherited,'actions':actions,'abstract_base_actions':abstract,'bounds':['High-level helper closure is a navigation aid, not dynamic-call proof; virtual _beforeTokenTransfer is explicitly interpreted in wrapper action semantics.','External token and engine emissions depend on their implementations; downstream market/hook evidence is joined by the report producer.','Guard lists retain per-call predicates and have not been promoted into global invariants.','Source code alone does not establish deployed addresses, callers, multisig control or live engine configuration.']}
 (PREP/f'{label}-support-facts.json').write_text(json.dumps(data,indent=2)+'\n')
 print(label,len(files),'files',len(actions),'runtime actions',len(abstract),'abstract base declarations')
for label in PINS:build(label)
