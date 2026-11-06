#!/usr/bin/env python3
"""Resolve future design gates only from executed product checks."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CRITERIA=('boundary-conformance','complete-demonstration','final-currency')
CANDIDATES=('fixed-live-v1','sequential-general-v1','staged-general-v1')

def snapshot(criterion):
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip()
 dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT)
 if dirty: raise ValueError('conformance requires a clean tracked tree')
 paths=['scripts/agent_instruction.py','scripts/prove_agent_instruction_reconciliation.py','tests/fixtures/agent-instruction-v1/manifest.json']
 if criterion=='boundary-conformance': paths.append('tests/emit_agent_instruction_reconciliation_report.py')
 if criterion=='complete-demonstration': paths.append('docs/agent-instruction-reconciliation/demonstration.json')
 return {'head':head,'tree':tree,'inputs':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in paths},'resolver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',choices=CANDIDATES,required=True);parser.add_argument('--criterion',choices=CRITERIA,required=True);args=parser.parse_args()
 out=ROOT/'.hexaemeron';reports=out/'reports'; reports.mkdir(exist_ok=True)
 prefix=out/'study-evidence'/('conformance-'+args.criterion)
 if args.criterion=='boundary-conformance':
  commands=[[sys.executable,'tests/emit_agent_instruction_reconciliation_report.py',str(prefix.with_suffix('.runner.json'))]]
 elif args.criterion=='complete-demonstration':
  commands=[[sys.executable,'scripts/prove_agent_instruction_reconciliation.py','demonstrate','--root','.','--verify','docs/agent-instruction-reconciliation/demonstration.json']]
 else:
  commands=[[sys.executable,'scripts/agent_instruction.py','check','--root','.','--manifest','tests/fixtures/agent-instruction-v1/manifest.json'],[sys.executable,'scripts/portable_promise_machine.py','check'],[sys.executable,'-m','unittest','tests.test_skills_sh_package']]
 identity=snapshot(args.criterion)
 logs=[]
 for index,command in enumerate(commands):
  result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=1200,check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  prefix.with_suffix(f'.{index}.stdout').write_bytes(result.stdout);prefix.with_suffix(f'.{index}.stderr').write_bytes(result.stderr)
  logs.append({'argv':command,'exit':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()})
  if result.returncode:
   prefix.with_suffix('.failed.json').write_text(json.dumps(logs,sort_keys=True,indent=2)+'\n');print('unresolved: '+args.criterion,file=sys.stderr);return 1
 if snapshot(args.criterion)!=identity: raise ValueError('source changed during conformance')
 if args.criterion=='complete-demonstration':
  records=[json.loads(line) for line in result.stdout.splitlines() if line.strip()]
  verification=records[-1] if records else {}
  expected=identity['inputs']['docs/agent-instruction-reconciliation/demonstration.json']
  if verification.get('schema')!='agent-instruction-reconciliation-verification/v1' or verification.get('outcome')!='accepted' or verification.get('record_sha256')!=expected or verification.get('structural_placements')!=6 or verification.get('complete_law_repairs')!=1 or verification.get('unchanged_reviewed_bindings')!=15 or type(verification.get('verified_dependencies')) is not int or verification['verified_dependencies']<1: raise ValueError('incomplete demonstration verification')
 if args.criterion=='boundary-conformance':
  runner=json.loads(prefix.with_suffix('.runner.json').read_bytes())
  if runner.get('schema')!='elenchus.unittest.v1' or runner.get('complete') is not True or not isinstance(runner.get('testsRun'),int) or runner['testsRun']<=0 or any(runner.get(k)!=0 for k in ['failures','errors','skipped','expectedFailures','unexpectedSuccesses']): print('unresolved: incomplete focused report',file=sys.stderr);return 1
 prefix.with_suffix('.proof.json').write_text(json.dumps({'identity':identity,'commands':logs},sort_keys=True,indent=2)+'\n')
 command=f'uv run --no-project --python 3.14.6 python .hexaemeron/scripts/resolve_reconciliation_conformance.py --candidate {args.candidate} --criterion {args.criterion}'
 report={'schema':'protasis-design-report/v1','candidate':args.candidate,'criterion':args.criterion,'value':True,'unit':'boolean','command':command,'exit':0}
 target=reports/f'{args.candidate}-{args.criterion}.json';target.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(str(target));return 0
if __name__=='__main__': raise SystemExit(main())
