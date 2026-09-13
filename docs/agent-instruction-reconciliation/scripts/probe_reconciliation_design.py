#!/usr/bin/env python3
"""Compare disposable reconciliation constructions on the three current fixtures."""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, math, os, shutil, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import prove_agent_instruction_reconciliation as p
CANDIDATES=('fixed-live-v1','sequential-general-v1','staged-general-v1')
OUT=ROOT/'.hexaemeron'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def emit(path, value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
class Generic(p.Reconciliation):
 def __init__(self,root,subject): self.subject=subject; super().__init__(root)
 def _subject_fixture(self,manifest): return next(f for f in manifest['fixtures'] if f['id']==self.subject)

def probe(candidate):
 manifest=json.loads((ROOT/p.MANIFEST).read_bytes()); observations=[]; all_paths=set(); elapsed=[]; generated={}; failures=[]
 before={path:sha((ROOT/path).read_bytes()) for path,_ in p.bound_digests(manifest)}
 for fixture in manifest['fixtures']:
  recon=Generic(ROOT,fixture['id']); all_paths.update(recon.live_paths)
  for placement in p.SPAN_PLACEMENTS:
   with tempfile.TemporaryDirectory(dir=OUT/'study-evidence',prefix='probe-') as scratch:
    tree=recon.copy_tree(Path(scratch)); (tree/Path(p.COVERAGE).parent).mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/p.COVERAGE,tree/p.COVERAGE)
    edit=recon.edited_source(placement); start=time.perf_counter_ns(); failure=None
    if candidate=='fixed-live-v1':
     recon._write(tree,recon.source_path,edit)
     try:
      live=p.LiveReconciliation(tree)
      if not live.unchanged(): live.apply()
     except p.ProverError as error: failure=str(error)
    else:
     recon.apply_passes(tree,edit)
    elapsed.append((time.perf_counter_ns()-start)/1_000_000)
    code,records=recon.check(tree); refusals=[(r.get('code'),r.get('node_path')) for r in recon.refusals(records)]
    raw=json.loads((tree/p.MANIFEST).read_bytes()); found=next(f for f in raw['fixtures'] if f['id']==fixture['id']); anchor=edit[int(found['source']['start']):int(found['source']['end'])]
    correct=(not failure and sha(anchor)==fixture['source']['span_sha256'] and ((placement==p.AFTER_SPAN_PLACEMENT and code==0) or (placement==p.BEFORE_SPAN_PLACEMENT and ('WAI-E-DIGEST.CORPUS','$.evidence.measurement_record') in refusals)))
    observations.append({'fixture':fixture['id'],'placement':placement,'exit':code,'refusals':refusals,'repair_classification_correct':correct,'failure':failure,'reviewed_span_preserved':sha(anchor)==fixture['source']['span_sha256']})
    if fixture['id']=='promise-machine-router-selection' and placement==p.BEFORE_SPAN_PLACEMENT and candidate!='fixed-live-v1':
     for art in ('model','source_spans','compact'):
      relative=fixture['artifacts'][art]['path']; generated[relative]=(ROOT/relative).read_bytes(),(tree/relative).read_bytes()
     generated[p.MANIFEST]=(ROOT/p.MANIFEST).read_bytes(),(tree/p.MANIFEST).read_bytes()
  if candidate!='fixed-live-v1':
   for kind,edited in [('changed',recon.in_span_source()),('duplicate',recon.source+recon.span)]:
    try: result=recon.rederive_offsets(edited); rejected=result is None
    except p.ProverError: rejected=True
    failures.append({'fixture':fixture['id'],'case':kind,'refused':rejected})
 # This candidate probe isolates the publication primitive, not production crash recovery.
 # Sequential writes retain their mixed state on a fault. Journalled writes restore the exact preimage.
 rollback=[]
 for fault in range(len(generated)):
  with tempfile.TemporaryDirectory(dir=OUT/'study-evidence',prefix='publish-') as scratch:
   base=Path(scratch)
   for relative,(old,new) in generated.items(): path=base/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(old)
   journal={k:old for k,(old,new) in generated.items()}
   try:
    for index,(relative,(old,new)) in enumerate(generated.items()):
     if index==fault: raise OSError('injected publication fault')
     path=base/relative; temp=path.with_suffix(path.suffix+'.new'); temp.write_bytes(new); os.replace(temp,path)
   except OSError:
    if candidate=='staged-general-v1':
     for relative,old in journal.items(): path=base/relative; temp=path.with_suffix(path.suffix+'.restore'); temp.write_bytes(old); os.replace(temp,path)
   rollback.append(all((base/rel).read_bytes()==old for rel,(old,new) in generated.items()))
 snapshot_ok=before=={path:sha((ROOT/path).read_bytes()) for path in before}
 ordered=sorted(elapsed); p95=math.ceil(ordered[math.ceil(.95*len(ordered))-1])
 values={'fixture-placements':sum(x['repair_classification_correct'] for x in observations), 'review-boundary':bool(failures) and all(x['refused'] for x in failures), 'legacy-v1':snapshot_ok and (candidate=='fixed-live-v1' or all(x['repair_classification_correct'] for x in observations)), 'recover-preimage':bool(rollback) and all(rollback), 'prepare-p95':p95, 'staging-bytes':sum(len(a)+len(b) for a,b in generated.values()) if candidate=='staged-general-v1' else 0}
 detail={'candidate':candidate,'base_head':'b9f8e36b8b6210bcd023a68059ecb46da3e35769','observations':observations,'hostile_cases':failures,'publication_faults_restored':rollback,'preparation_samples_ms':elapsed,'source_unchanged':snapshot_ok,'publication_probe_boundary':'four generated targets, handled injected OSError; durable journal admission, killed-process replay and coverage publication remain conformance work','values':values}
 emit(OUT/'study-evidence'/f'{candidate}.json',detail)
 for criterion,value in values.items():
  unit={'fixture-placements':'count','prepare-p95':'milliseconds','staging-bytes':'bytes'}.get(criterion,'boolean')
  report={'schema':'protasis-design-report/v1','candidate':candidate,'criterion':criterion,'value':value,'unit':unit,'command':f'uv run --no-project --python 3.14.6 python .hexaemeron/scripts/probe_reconciliation_design.py --candidate {candidate}','exit':0}
  emit(OUT/'reports'/f'{candidate}-{criterion}.json',report)
 print(json.dumps(detail,sort_keys=True))
if __name__=='__main__':
 args=argparse.ArgumentParser();args.add_argument('--candidate',choices=CANDIDATES,required=True);probe(args.parse_args().candidate)
