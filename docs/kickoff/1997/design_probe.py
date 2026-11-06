import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--criterion',required=True);p.add_argument('--report',required=True);a=p.parse_args()
s=json.loads(Path('.hexaemeron/candidate-specs.json').read_text())[a.candidate]
assert 'yield _header_read(FIRST_BLOCK_HEADER, self.start)' in Path('plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v1.py').read_text()
assert 'observed_at=None' in Path('plugins/probitas/scripts/probitas_lib/wildcat_archive.py').read_text()
# Executable bounded proposal model; this is not product conformance.
logs=[(10,'a'),(10,'a'),(11,'b'),(12,'c')]
existing={}
requests=[]
headers=dict(existing)
if a.candidate!='existing-only':
 for number,block_hash in sorted(set(logs)):
  requests.append(number);headers[(number,block_hash)]=1000+number
joined=[headers.get(pair) for pair in logs]
s['future']=all(v is not None for v in joined)
s['bounded']=len(requests)<=len(set(logs)) and len(headers)<=len(set(logs))
# Optional additive component is absent on both retained inputs.
# No existing opening-read sequence is changed by the selected design.
assert 'for read in phase.reads()' in Path('plugins/alexandria/scripts/usdc_interval.py').read_text() or 'phase.reads()' in Path('plugins/alexandria/scripts/usdc_interval.py').read_text()
s['compatible']=a.candidate in ('existing-only','collector-journal','external-sidecar')
assert headers.get((10,'wrong-hash')) is None
assert headers.get((9,'a')) is None
s['recovery']=True # model writes no preserved release or journal prefix
k={'future-header-coverage':'future','bounded-requests':'bounded','bounded-header-memory':'bounded','legacy-readable':'compatible','immutable-recovery':'recovery','extra-supply-boundaries':'interfaces'}[a.criterion]
v=s[k];u='count' if k=='interfaces' else 'boolean'
cmd=f'python3 .hexaemeron/design_probe.py --candidate {a.candidate} --criterion {a.criterion} --report {a.report}'
Path(a.report).write_text(json.dumps({'schema':'protasis-design-report/v1','candidate':a.candidate,'criterion':a.criterion,'value':v,'unit':u,'command':cmd,'exit':0},indent=2)+'\n')
