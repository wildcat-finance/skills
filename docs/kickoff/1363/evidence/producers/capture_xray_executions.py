import concurrent.futures, hashlib, json, os, subprocess, time
from pathlib import Path
root=Path(__file__).resolve().parent.parent
prep=root/'.hexaemeron/xray-preparation'
scripts=root/'plugins/hexaemeron/skills/x-ray/scripts'
def capture(role):
    source=root/'.hexaemeron/sources'/role
    env=dict(os.environ)
    env['PATH']='/opt/homebrew/opt/grep/libexec/gnubin:'+env['PATH']
    rows=[]
    for name,argv in [
        ('enumeration',['bash',str(scripts/'enumerate.sh'),str(source),'src']),
        ('git-security-analysis',['/opt/homebrew/bin/python3',str(scripts/'analyze_git_security.py'),'--repo',str(source),'--src-dir','src','--json',str(source/'x-ray/git-security-analysis.json')])]:
        start=time.monotonic()
        result=subprocess.run(argv,cwd=root,env=env,capture_output=True,timeout=90)
        log=prep/f'{role}-enumeration.txt' if name=='enumeration' else source/'x-ray/git-security-analysis.log'
        log.write_bytes(result.stdout+result.stderr)
        rows.append({'argv':argv,'cwd':str(root),'exit':result.returncode,'elapsed_seconds':time.monotonic()-start,
            'log':str(log.relative_to(root)),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
            'environment_override':{'PATH_prefix':'/opt/homebrew/opt/grep/libexec/gnubin'}})
        if result.returncode: raise RuntimeError((name,result.returncode,result.stderr.decode()[:500]))
    version=subprocess.run(['forge','--version'],capture_output=True,check=True,timeout=20).stdout.decode()
    sub=subprocess.run(['git','-C',str(source),'submodule','status','--recursive'],capture_output=True,check=True,timeout=20).stdout.decode()
    clean=subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src'],capture_output=True,timeout=20)
    result={'role':role,'commands':rows,'forge_version':version,'recursive_submodules':sub,'source_tracked_diff_exit':clean.returncode}
    (prep/f'{role}-preparation-execution.json').write_text(json.dumps(result,indent=2)+'\n')
    return {'role':role,'commands':[r['exit'] for r in rows],'tracked_source_diff_exit':clean.returncode}
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(capture,['deployed','candidate']): print(result)

