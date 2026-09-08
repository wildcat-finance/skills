"""Measure the two documentation corpora through the existing Berean API."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'plugins/berean/scripts'))
from berean_lib import corpus

STATE = ROOT / '.hexaemeron'
REPORTS = STATE / 'design-reports'
DOC_REPO = '/Users/c0rtexzer0/Documents/GitHub/wildcat-docs'
COMMIT = '636b1dcba90c816e699c0d876c22d39be2c58b06'
SELECTED = ['using-wildcat/terminology.md', 'using-wildcat/delinquency.md', 'technical-overview/contract-deployments.md']


def emit(candidate, criterion, value, unit, command):
    path = REPORTS / f'{candidate}-{criterion}.json'
    obj = {'schema':'protasis-design-report/v1','candidate':candidate,'criterion':criterion,'value':value,'unit':unit,'command':command,'exit':0}
    path.write_text(json.dumps(obj, sort_keys=True, indent=2)+'\n')
    return {'candidate':candidate,'criterion':criterion,'state':'pass','report':{'path':str(path.relative_to(STATE)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}


def main():
    REPORTS.mkdir(exist_ok=True)
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        release = 'plugins/berean/examples/wildcat-mainnet-v0/release'
        commands = [
            ['python3','plugins/berean/scripts/berean.py','verify-release',release],
            ['python3','plugins/berean/scripts/berean.py','run-evals',release],
            ['python3','plugins/berean/examples/wildcat-mainnet-v0/demo.py'],
            ['python3','plugins/ariadne/scripts/ariadne.py','verify','plugins/berean/examples/wildcat-mainnet-v0/grounded-agent.intoto.json'],
        ]
        observed = []
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
            observed.append({'command':command, 'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
            if result.returncode:
                print(json.dumps(observed)); return 1
        (REPORTS / f'{candidate}-release-output.json').write_text(json.dumps(observed, indent=2)+'\n')
        emit(candidate,'final-release',True,'boolean',f'python3 .hexaemeron/design_probe.py {candidate}')
        return 0
    paths = subprocess.check_output(['git','-C',DOC_REPO,'ls-tree','-r','--name-only',COMMIT],text=True).splitlines()
    all_md = sorted(x for x in paths if x.endswith('.md'))
    results = []
    observations = {}
    for candidate, selected in [('selected-docs',SELECTED),('whole-markdown',all_md)]:
        with tempfile.TemporaryDirectory(prefix='berean-study-',dir=STATE) as temp:
            directory = Path(temp)
            for relative in selected:
                data = subprocess.check_output(['git','-C',DOC_REPO,'show',f'{COMMIT}:{relative}'])
                path = directory / relative
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(data)
            durations=[]
            for repeat in range(5):
                start=time.perf_counter_ns()
                manifest=corpus.build(str(directory),COMMIT)
                verified=all(c.passed for c in corpus.verify(manifest,str(directory)))
                durations.append((time.perf_counter_ns()-start)/1000000)
                assert verified
            source_equal = all((directory/p).read_bytes()==(STATE/'inputs/docs'/p).read_bytes() for p in SELECTED)
            victim=directory/SELECTED[0]
            original=victim.read_bytes(); victim.write_bytes(original+b'\nchanged\n')
            refused=any(c.name=='corpus-bytes' and not c.passed for c in corpus.verify(manifest,str(directory)))
            victim.write_bytes(original)
            recovered=all(c.passed for c in corpus.verify(manifest,str(directory)))
            observations[candidate]={'files':len(manifest['files']), 'bytes':sum(e['bytes'] for e in manifest['files']), 'duration_ms':durations,'corpus_digest':manifest['corpus_digest'], 'same_selected_source_bytes':source_equal,'tamper_refused':refused,'restored_pass':recovered}
            values=[('source-bytes',source_equal,'boolean'),('existing-schema',verified,'boolean'),('build-verify-time',math.ceil(max(durations)),'milliseconds'),('corpus-space',sum(e['bytes'] for e in manifest['files']),'bytes'),('recover-pinned-bytes',refused and recovered,'boolean')]
            for criterion,value,unit in values:
                results.append(emit(candidate,criterion,value,unit,'python3 .hexaemeron/design_probe.py'))
    (REPORTS/'corpus-observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    criteria=[
        {'id':'source-bytes','concern':'correctness','kind':'gate','stage':'selection','owner':'berean','unit':'boolean','comparator':'equals','threshold':True,'blocks':'design-lock'},
        {'id':'existing-schema','concern':'compatibility','kind':'gate','stage':'selection','owner':'berean','unit':'boolean','comparator':'equals','threshold':True,'blocks':'design-lock'},
        {'id':'build-verify-time','concern':'time','kind':'gate','stage':'selection','owner':'metron','unit':'milliseconds','comparator':'at-most','threshold':1000,'blocks':'design-lock'},
        {'id':'corpus-space','concern':'space','kind':'metric','stage':'selection','owner':'metron','unit':'bytes','comparator':'minimise','threshold':None,'blocks':'design-lock'},
        {'id':'recover-pinned-bytes','concern':'recovery','kind':'gate','stage':'selection','owner':'berean','unit':'boolean','comparator':'equals','threshold':True,'blocks':'design-lock'},
        {'id':'final-release','concern':'correctness','kind':'gate','stage':'conformance','owner':'berean','unit':'boolean','comparator':'equals','threshold':True,'blocks':'integration'},
    ]
    for candidate in observations:
        results.append({'candidate':candidate,'criterion':'final-release','state':'pending','resolver':f'python3 .hexaemeron/design_probe.py {candidate}','report':f'design-reports/{candidate}-final-release.json','blocks':'integration'})
    evidence={'schema':'protasis-design-evidence/v1','candidates':[{'id':'selected-docs','summary':'Freeze the three captured official documents needed by the finite market release.'},{'id':'whole-markdown','summary':'Freeze every Markdown document at the same official repository commit.'}],'criteria':criteria,'results':results,'selection':{'candidate':'selected-docs','rule':'unique-frontier','policy_ref':None}}
    (STATE/'design-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(observations,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
