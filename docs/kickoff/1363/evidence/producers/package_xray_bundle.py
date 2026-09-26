import difflib, hashlib, json, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from assemble_xray_evidence import ROOT, PREP, OUT, PINS, read, write

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def copy(source, destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
def retain(source,name):
    path=OUT/name;copy(source,path)
    return {'path':name,'sha256':sha(path),'bytes':path.stat().st_size}
def run():
    execution={'schema':'issue-1363-execution/v1','roles':PINS,'collated_at':datetime.now(timezone.utc).isoformat(),'coverage':[],
        'preparation':{},'ast':{},'rendering':{},
        'boundary':'AST-only compilation establishes parse/type information for enumeration. Coverage failed before test execution. Test inventory is not a passing test, audit, fuzz or coverage result.'}
    for role,pin in PINS.items():
        source=ROOT/'.hexaemeron/sources'/role
        assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==pin
        capture=read(PREP/f'{role}-preparation-execution.json')
        execution['preparation'][role]=dict(capture,record=retain(PREP/f'{role}-preparation-execution.json',f'evidence/{role}-preparation-execution.json'))
        coverage=read(source/'x-ray/coverage-result.json')
        gaps = {'deployed': ['Solar analysis failed: unresolved symbol locals at src/spherex/SphereXProtectedRegisteredBase.sol:153:39.', 'Solc Yul stack-depth failure: var_market path exceeds the stack by three slots; no memoryguard.'],
            'candidate': ['Solc Stack too deep at script/deploy/v2-5/02-deploy-hooks-factory-standard.s.sol:342:35, initCodeHash.', 'Solc Yul stack-depth failure: var_deployments/var_result path exceeds the stack by six slots; no memoryguard.']}
        for attempt in coverage['attempts']:
            log=retain(source/'x-ray'/attempt['log'],f'evidence/{role}-{attempt["log"]}')
            execution['coverage'].append({'role':role,'commit':pin,'argv':attempt['argv'],'exit':attempt['exit_code'],'status':'failed',
                'tool_version':capture['forge_version'],'log':log,
                'gap':gaps[role][int('--ir-minimum' in attempt['argv'])] + ' No coverage or passing test result was produced.'})
        retain(source/'x-ray/coverage-result.json',f'evidence/{role}-coverage-result.json')
        for name in ['git-security-analysis.json','git-security-analysis.log']:
            retain(source/'x-ray'/name,f'evidence/{role}-{name}')
        for suffix in ['action-denominator.json','function-denominator.json','runtime-denominator.json','ast-result.json',
                       'entry-scan-single.txt','entry-scan-multiline.txt','enumeration.txt','history-supplement.json',
                       'market-facts.json','hooks-facts.json','support-facts.json','library-facts.json','doc-extraction.md']:
            retained_suffix = 'doc-extraction.txt' if suffix == 'doc-extraction.md' else suffix
            retain(PREP/f'{role}-{suffix}',f'evidence/{role}-{retained_suffix}')
        execution['ast'][role]=read(PREP/f'{role}-ast-result.json')
        inp=read(PREP/f'{role}-ast-input.json')
        config={'role':role,'commit':pin,'language':inp['language'],'source_paths':list(inp['sources']),'settings':inp['settings'],
            'serialization':{'ensure_ascii':True,'separators':[',',':'],'trailing_newline':False},
            'input_sha256':sha(PREP/f'{role}-ast-input.json'),
            'boundary':'Rebuild content from these exact repository files; inherited imports resolve through the pinned recursive submodules.'}
        write(OUT/f'evidence/{role}-ast-input-recovery.json',config)
        generator=ROOT/'plugins/hexaemeron/skills/x-ray/scripts/generate_svg.py'
        argv=['/opt/homebrew/bin/python3',str(generator),str(OUT/role/'architecture.json'),str(OUT/role/'architecture.svg')]
        result=subprocess.run(argv,capture_output=True,timeout=30,check=True)
        png=PREP/f'{role}-architecture-preview.png'
        raster=['/opt/homebrew/bin/rsvg-convert','-z','2',str(OUT/role/'architecture.svg'),'-o',str(png)]
        raster_result=subprocess.run(raster,capture_output=True,timeout=30,check=True)
        execution['rendering'][role]={'svg':{'argv':argv,'exit':result.returncode,'generator_sha256':sha(generator)},
            'png_preview':{'argv':raster,'exit':raster_result.returncode,'sha256':sha(png)},
            'boundary':'Rendering is separate from the named reviewer visual inspection receipt.'}
    for name in ['cross-system-links.json','doc-inputs.json','support-comparison.json','hooks-comparison.md','market-comparison.md','support-comparison.md']:
        retain(PREP/name,'evidence/'+name)
    for source in sorted(PREP.glob('*.py')):
        retain(source,'evidence/producers/'+source.name)
    for name in ['assemble_xray_evidence.py','derive_xray_records.py','report_text.py','capture_xray_executions.py','package_xray_bundle.py']:
        retain(ROOT/'.hexaemeron'/name,'evidence/producers/'+name)
    retain(ROOT/'.hexaemeron/design-selection/probe.py','evidence/producers/design-selection-probe.py')
    write(OUT/'evidence/execution.json',execution)
    paths=['plugins/hexaemeron/skills/x-ray/SKILL.md','plugins/hexaemeron/skills/x-ray/scripts/enumerate.sh',
        'plugins/hexaemeron/skills/x-ray/scripts/analyze_git_security.py','plugins/hexaemeron/skills/x-ray/scripts/generate_svg.py',
        'docs/kickoff/1359/targets.json','docs/kickoff/1372/eventdecision.json']
    provenance={'schema':'issue-1363-provenance/v1','producer':'/root','source_readers':['/root','/root/xray_hooks','/root/xray_specs','/root/xray_support'],
        'skills_repository':'wildcat-finance/skills','skills_base':'95dca9d0f04353856f4e1684333b3ed94e85de87',
        'inputs':[{'path':p,'sha256':sha(ROOT/p),'bytes':(ROOT/p).stat().st_size} for p in paths],
        'accepted_eventdecision_merge':'9182d0adcb7e9a5330c259d9dc1e044b511711c2',
        'roles':PINS,'boundary':'The deployed-comparison pin is not a claim that its entire tree matches every deployed address. Existing verification inputs establish only their named blob matches. Candidate Sepolia evidence does not establish mainnet deployment.'}
    write(OUT/'evidence/provenance.json',provenance)
    old=(OUT/'deployed/entry-points.md').read_text().splitlines(keepends=True)
    new=(OUT/'candidate/entry-points.md').read_text().splitlines(keepends=True)
    (OUT/'entry-points.diff').write_text(''.join(difflib.unified_diff(old,new,fromfile='deployed/entry-points.md',tofile='candidate/entry-points.md')))
    print('packaged',sum(p.is_file() for p in OUT.rglob('*')),'files',sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'bytes')
if __name__=='__main__':run()
