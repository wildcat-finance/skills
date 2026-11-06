import json
from pathlib import Path
P=Path('.hexaemeron/xray-preparation')
def walk(x):
 if isinstance(x,dict):
  if 'nodeType' in x:yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
for label in ('deployed','candidate'):
 ast=json.loads((P/f'{label}-ast.json').read_text());nodes={n['id']:n for n in walk(ast) if 'id' in n}
 def typ(t):
  k=t['nodeType']
  if k=='ElementaryTypeName':return {'uint':'uint256','int':'int256','byte':'bytes1','address payable':'address'}.get(t['name'],t['name'])
  if k=='ArrayTypeName':return typ(t['baseType'])+'['+(t['length']['value'] if t.get('length') else '')+']'
  if k=='UserDefinedTypeName':
   n=nodes[t['referencedDeclaration']]
   if n['nodeType']=='UserDefinedValueTypeDefinition':return typ(n['underlyingType'])
   if n['nodeType']=='ContractDefinition':return 'address'
   if n['nodeType']=='EnumDefinition':return 'uint8'
   if n['nodeType']=='StructDefinition':return '('+','.join(typ(m['typeName']) for m in n['members'])+')'
  if k=='FunctionTypeName':return 'function'
  raise ValueError(t)
 evs={}
 for n in nodes.values():
  if n['nodeType']=='EventDefinition':
   evs['0x'+n['eventSelector']]={'signature':n['name']+'('+','.join(typ(x['typeName']) for x in n['parameters']['parameters'])+')','abi_types':[typ(x['typeName']) for x in n['parameters']['parameters']]}
 f=P/f'{label}-support-facts.json';d=json.loads(f.read_text());counter=[0]
 def update(x):
  if isinstance(x,dict):
   if 'topic0' in x and x['topic0'] in evs:
    v=evs[x['topic0']];x['source_signature']=x.get('source_signature',x['signature']);x['signature']=v['signature'];x['signature_kind']='canonical ABI';counter[0]+=1
    for field,atype in zip(x['fields'],v['abi_types']):field['source_type']=field.pop('type',field.get('source_type'));field['abi_type']=atype
   for v in x.values():update(v)
  elif isinstance(x,list):
   for v in x:update(v)
 update(d);f.write_text(json.dumps(d,indent=2)+'\n');print(label,'canonicalized event occurrences',counter[0])
left=json.loads((P/'deployed-support-facts.json').read_text());right=json.loads((P/'candidate-support-facts.json').read_text());L={r['id']:r for r in left['actions']};R={r['id']:r for r in right['actions']};obs=[]
for i in sorted(L.keys()|R.keys()):
 a=L.get(i);b=R.get(i);row={'id':i,'classification':'added' if a is None else 'removed' if b is None else 'unchanged','before':None if a is None else {'path':a['source_path'],'line':a['line']},'after':None if b is None else {'path':b['source_path'],'line':b['line']},'changed_fields':[],'observation':''}
 if a is None:row['changed_fields']=['action'];row['observation']='Candidate-only action; see candidate support facts for complete access, effects, value flow and event conditions.'
 elif b is None:row['changed_fields']=['action'];row['observation']='Deployed-only action.'
 else:
  con=a['contract'];fn=a['function'];row['observation']='Access, persistent effects, value flow and successful-path local event families retained. Source prose and exact bytes may differ.'
  if con=='Wildcat4626Wrapper' and fn not in ('approve','permit'):
   row['classification']='changed';row['changed_fields']=['conditions','downstream_effects']
   row['observation']='Inherited transfer hook now uses live principal sanctions and wrapper solvency, with deterministic escrow quarantine/release exceptions; same event signatures do not imply same admitted paths.'
   if fn in ('deposit','mint','withdraw','redeem'):
    row['changed_fields']+=['rounding','amounts'];row['observation']+=' Execution changes half-up scaling to floor/ceil composition, adds operational/solvency checks and exact scaled movement checks; Deposit/Withdraw and mint/burn Transfer names remain.'
    if fn in ('deposit','mint'):row['observation']+=' New transfer-policy gate checks whether wrapper may receive market tokens.'
   if fn=='sweep':row['changed_fields']+=['access','rounding','amounts'];row['observation']='Caller must be live market borrower instead of captured marketOwner. Recipient sanctions follow live principal; market-token surplus normalization changes half-up to ceil. TokensSwept name remains.'
   row['helper_evidence']={'before':['src/vault/Wildcat4626Wrapper.sol:428','src/vault/Wildcat4626Wrapper.sol:438'],'after':['src/vault/Wildcat4626Wrapper.sol:764','src/vault/Wildcat4626Wrapper.sol:954','src/vault/Wildcat4626Wrapper.sol:991']}
  elif con=='Wildcat4626WrapperFactory':
   row['classification']='changed';row['changed_fields']=['conditions','effects','calls','events'];row['observation']='Generation-aware legacy routing added; undeclared rounding returns legacy factory result without local WrapperDeployed, while supported floor market creates and registers local wrapper after policy queries.'
  elif con=='WildcatSanctionsEscrow':
   row['observation']='Original-namespace release access, all-balance transfer and EscrowReleased retained. Sentinel query implementation changes high-level call to bounded bool-decoding assembly with the same successful ABI semantics; failed/malformed external reads still reject.'
  elif con=='WildcatArchController':row['observation']+=' Ownable ownership and SphereX roles remain separate; new registry users of owner authority do not change these action bodies or local emitted topics.'
 obs.append(row)
out={'schema':'issue-1363-support-comparison/v1','producer':'/root/xray_support','before_commit':left['commit'],'after_commit':right['commit'],'basis':'Direct source reads plus explicit helper review; no inference of unchanged semantics from top-level body equality alone. Local event equivalence is not external emission equivalence.','counts':{k:sum(r['classification']==k for r in obs) for k in ('added','removed','changed','unchanged')},'observations':obs}
(P/'support-comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(out['counts'])
