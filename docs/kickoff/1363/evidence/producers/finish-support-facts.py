import hashlib,json
from pathlib import Path
p=Path('.hexaemeron/xray-preparation')
for label in ('deployed','candidate'):
 f=p/f'{label}-support-facts.json';d=json.loads(f.read_text());den=json.loads((p/f'{label}-action-denominator.json').read_text()); by={(r['contract'],r['selector'].removeprefix('0x')):r for r in den['actions']}
 for a in d['actions']:
  row=by[(a['contract'],a['selector'].removeprefix('0x'))]
  a['signature']=row['signature'];a['id']=row['id'];a['body_sha256']=row['body_sha256'];a['line']=row['line']
  if a['function']=='sweep': a['effects']=['no direct wrapper supply write; the selected token transfer may move wrapper shares when token == address(this)']
  if a['contract']=='WildcatArchController' and a['function']=='updateSphereXEngineOnRegisteredContracts': a['external_event_condition']='Each nonempty selected target receives changeSphereXEngine; the source implementation emits ChangedSpherexEngineAddress. Registry membership itself does not verify target bytecode. External SphereX engine events are out of scope.'
  for e in a['reachable_local_events']:
   e['condition']='Successful execution reaching this emit site; any branch or loop is determined by its exact cited source function and action conditions.'
  for e in a['assembly_log_sites']:
   func=e['reaching_function']; name=None
   if func.startswith('emit_'):name=func.removeprefix('emit_')
   elif func in ('_setOwner','_initializeOwner'):name='OwnershipTransferred'
   elif func=='requestOwnershipHandover':name='OwnershipHandoverRequested'
   elif func=='cancelOwnershipHandover':name='OwnershipHandoverCanceled'
   elif func in ('approve','permit','_approve'):name='Approval'
   elif func in ('transfer','transferFrom','_transfer','_mint','_burn'):name='Transfer'
   e['event_name']=name;e['condition']='Successful execution reaching the cited assembly log; branch conditions are recorded for the action.'
 d['reconciliation']={'canonical_inventory':f'{label}-action-denominator.json','canonical_inventory_sha256':hashlib.sha256((p/f'{label}-action-denominator.json').read_bytes()).hexdigest(),'identity':'contract plus canonical ABI signature, with compiler selector','count':len(d['actions']),'exact_support_subset':True}
 d['invariant_candidates']=[
 {'kind':'NatSpec','scope':'Wildcat4626Wrapper','claim':'Shares mirror scaled ownership, with matching market-generation transfer arithmetic.','locations':['src/vault/Wildcat4626Wrapper.sol:25' if label=='deployed' else 'src/vault/Wildcat4626Wrapper.sol:42'],'status':'developer claim; wrapper supply/backing is not equality under direct market-token donations'},
 {'kind':'conservation','scope':'ERC20 inherited wrapper balances','claim':'Successful transfer changes from/to balances by equal opposite amount and leaves totalSupply unchanged.','locations':['lib/solady/src/tokens/ERC20.sol:208','lib/solady/src/tokens/ERC20.sol:215','lib/solady/src/tokens/ERC20.sol:263','lib/solady/src/tokens/ERC20.sol:270'],'status':'same-block writes verified; mint and burn separately pair supply and account balances'},
 {'kind':'one-shot-local-registry','scope':'Wildcat4626WrapperFactory','claim':'A locally registered market wrapper mapping can only transition from zero to the freshly deployed wrapper.','locations':['src/vault/Wildcat4626WrapperFactory.sol:32','src/vault/Wildcat4626WrapperFactory.sol:37'] if label=='deployed' else ['src/vault/Wildcat4626WrapperFactory.sol:145','src/vault/Wildcat4626WrapperFactory.sol:161'],'status':'sole mapping write in this source verified; candidate legacy branch uses separate factory mapping'},
 {'kind':'per-call-guard','scope':'SphereX transfer acceptance','claim':'Only pendingSphereXAdmin can accept; action clears pending admin.','locations':['src/spherex/SphereXConfig.sol:121' if label=='deployed' else 'src/spherex/SphereXConfig.sol:131'],'status':'two-step role transfer; not a permanent one-shot latch or operation timelock'}]
 if label=='candidate': d['invariant_candidates'] += [
 {'kind':'one-shot-origin-binding','scope':'WildcatBorrowerIdentityRegistry','claim':'Account registration records an originating factory once; principal transfers preserve it.','locations':['src/WildcatBorrowerIdentityRegistry.sol:107','src/WildcatBorrowerIdentityRegistry.sol:119','src/WildcatBorrowerIdentityRegistry.sol:167'],'status':'only accountFactoryOf assignment is registration; no deletion path in this source'},
 {'kind':'per-call-guard','scope':'Wildcat4626Wrapper','claim':'Core ERC4626 paths reject insolvency using scaledBacking < shareSupply.','locations':['src/vault/Wildcat4626Wrapper.sol:954','src/vault/Wildcat4626Wrapper.sol:967'],'status':'do not promote to unconditional global solvency: external market sanctions/transfer effects may change backing independently'},
 {'kind':'state-transition','scope':'ManagedRoleProvider','claim':'Request changes pending administrator; accept by pending address clears pending and changes administrator.','locations':['src/providers/ManagedRoleProvider.sol:27','src/providers/ManagedRoleProvider.sol:54'],'status':'repeatable two-step transfer; pending status grants no administration before acceptance'}]
 f.write_text(json.dumps(d,indent=2)+'\n')
 print(label,len(d['actions']),f.stat().st_size,hashlib.sha256(f.read_bytes()).hexdigest())
