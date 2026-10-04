#!/usr/bin/env python3
"""Restore a checkpoint in a network-disabled container with an empty keyring.

Only the archive, sidecar and controller enter the container. After inspection,
its verified bundle supplies the sibling runtime. The input controller replaces
only that runtime's controller file; the transcript records that overlay.
After restore, a probe-owned Git configuration rewrites the restored origin URL
to the verified bundle, so a directive that reads origin refs, such as
`merge-step`, reads the archived refs without network. Those refs prove only
captured state; live GitHub reads remain mandatory before integration.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid

import checkpoint_measure as measure

SCHEMA = 'fiat-checkpoint-restore-transcript/v1'
CONTROLLER_PATH = 'plugins/hexaemeron/skills/fiat/scripts/hexctl.py'
# The probe is fixed program text. Archive content is parsed only after the
# separately supplied controller has accepted the out-of-band digest.
PROBE = r'''
import hashlib, json, os, pathlib, re, shutil, sys, zipfile
root = pathlib.Path('/probe')
root.mkdir()
keyring = root / 'keyring'
keyring.mkdir(mode=0o700)
(root / 'home').mkdir()
os.environ.clear()
os.environ.update(PATH='/usr/local/bin:/usr/bin:/bin', HOME='/probe/home',
    GNUPGHOME=str(keyring), LANG='C.UTF-8', GIT_CONFIG_NOSYSTEM='1',
    GIT_CONFIG_GLOBAL='/dev/null', GIT_ALLOW_PROTOCOL='file',
    GIT_TERMINAL_PROMPT='0', GIT_NO_REPLACE_OBJECTS='1')
expected = sys.argv[1]
archive = pathlib.Path('/input/checkpoint.zip')
controller = pathlib.Path('/input/hexctl.py')
controller_digest = hashlib.sha256(controller.read_bytes()).hexdigest()
print(json.dumps({'operation':'start', 'keyring_empty':not any(keyring.iterdir()),
    'input_files':sorted(p.name for p in pathlib.Path('/input').iterdir()),
    'controller_sha256':controller_digest}), flush=True)
def perform(name, argv, json_result=False):
    result = command(argv)
    event = {'operation':name, 'argv':argv, 'exit':result['exit'], 'wall_ms':result['wall_ms'], 'failure':result.get('failure'),
        'stdout_sha256':hashlib.sha256(result['stdout'].encode()).hexdigest(),
        'stderr_sha256':hashlib.sha256(result['stderr'].encode()).hexdigest()}
    if result['exit'] or result.get('failure'):
        print(json.dumps(event), flush=True)
        raise SystemExit(result['exit'] or 1)
    value = json.loads(result['stdout']) if json_result else None
    if name == 'inspect':
        event['result'] = {key:value[key] for key in ('schema','outer_sha256','findings','bytes','identity')}
    elif name == 'restore':
        event['result'] = value
    elif name == 'next':
        event['result'] = {key:item for key,item in value.items()
            if key not in ('state_sha256','brief','brief_path')}
    elif name == 'identity':
        event['result'] = {'snapshot_id':value['snapshot_id']}
    elif name == 'status':
        event['json_object'] = isinstance(value,dict) and bool(value)
    print(json.dumps(event), flush=True)
    return value
perform('inspect', ['python','/input/hexctl.py','checkpoint','inspect',
    '--archive',str(archive),'--sha256',expected], True)
with zipfile.ZipFile(archive) as reader:
    manifest_bytes = reader.read('checkpoint.json')
    manifest = json.loads(manifest_bytes)
    with reader.open('git/repository.bundle') as source, (root/'repository.bundle').open('wb') as out:
        shutil.copyfileobj(source,out)
commit = manifest['boundary']['working_commit_sha']
if not re.fullmatch('[0-9a-f]{40}',commit):
    raise SystemExit('invalid runtime commit')
runtime = root/'runtime'
perform('runtime-init',['git','init',str(runtime)])
perform('runtime-fetch',['git','-C',str(runtime),'fetch','--no-tags',str(root/'repository.bundle'),
    '+refs/heads/*:refs/heads/*'])
perform('runtime-checkout',['git','-C',str(runtime),'checkout','--detach',commit])
runtime_controller = runtime/'plugins/hexaemeron/skills/fiat/scripts/hexctl.py'
bundled_controller_digest = hashlib.sha256(runtime_controller.read_bytes()).hexdigest()
shutil.copyfile(controller,runtime_controller)
if hashlib.sha256(runtime_controller.read_bytes()).hexdigest() != controller_digest:
    raise SystemExit('controller overlay differs')
destination = root/'destination'
destination.mkdir()
empty = not any(destination.iterdir())
print(json.dumps({'operation':'runtime', 'runtime_commit':commit,
    'bundle_sha256':manifest['bundle']['sha256'],
    'bundled_controller_sha256':bundled_controller_digest,
    'controller_sha256':controller_digest, 'controller_overlay_verified':True,
    'destination_was_empty':empty, 'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
    'capsule_manifest_sha256':manifest['controller_capsule']['manifest_sha256'],
    'manifest_next':manifest['boundary']['next'],
    'snapshot_id':manifest['identity'].get('snapshot_id'),
    'expanded_bytes':len(manifest_bytes)+sum(item['bytes'] for item in manifest['archive']['entries'])}),flush=True)
restored = perform('restore',['python',str(runtime_controller),'--dir',str(destination),
    'checkpoint','restore','--archive',str(archive),'--sha256',expected],True)
worktree = pathlib.Path(restored['restore']['worktree']).resolve()
if not worktree.is_relative_to(destination):
    raise SystemExit('restored worktree escapes destination')
bundle = root/'repository.bundle'
def listing(argv):
    result = command(argv)
    if result['exit'] or result.get('failure'):
        raise SystemExit('ref listing failed')
    return result['stdout']
bundle_refs = listing(['git','ls-remote','--refs',str(bundle)])
origin = command(['git','-C',str(worktree),'config','--get-all','remote.origin.url'])
if origin.get('failure') or origin['exit'] not in (0,1):
    raise SystemExit('origin could not be read')
origin_url = origin['stdout'].strip() or None
origin_refs = None
if origin_url is not None:
    if '\n' in origin_url:
        raise SystemExit('origin names more than one URL')
    config = root/'gitconfig'
    perform('origin-config',['git','config','--file',str(config),
        'url.'+str(bundle)+'.insteadOf',origin_url])
    os.environ['GIT_CONFIG_GLOBAL'] = str(config)
    origin_refs = listing(['git','-C',str(worktree),'ls-remote','--refs','origin'])
print(json.dumps({'operation':'origin-refs', 'origin_url':origin_url,
    'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),
    'bundle_refs_sha256':hashlib.sha256(bundle_refs.encode()).hexdigest(),
    'origin_refs_sha256':None if origin_refs is None else hashlib.sha256(origin_refs.encode()).hexdigest(),
    'refs':len(bundle_refs.splitlines())}),flush=True)
for name,tail,parsed in [('verify',['verify'],False),('status',['status','--json'],True),
                        ('next',['next'],True),('identity',['checkpoint','identity'],True)]:
    perform(name,['python',str(runtime_controller),'--dir',str(worktree),*tail],parsed)
'''
LEGACY_OPERATIONS = ('start', 'inspect', 'runtime-init', 'runtime-fetch', 'runtime-checkout',
                     'runtime', 'restore', 'verify', 'status', 'next', 'identity')
OPERATIONS = LEGACY_OPERATIONS[:7] + ('origin-config', 'origin-refs') + LEGACY_OPERATIONS[7:]
# An unanchored run has no origin to rewrite, so it records no configuration.
UNANCHORED_OPERATIONS = LEGACY_OPERATIONS[:7] + ('origin-refs',) + LEGACY_OPERATIONS[7:]
UNCOMMANDED = ('start', 'runtime', 'origin-refs')
# The delegate `hexctl next` names for each directive; every other directive
# carries `agent: null` and `task_identity: null`.
DELEGATES = {'study': 'surveyor', 'inoculate': 'mason', 'implement': 'mason',
             'audit-round': 'warden', 'prose': 'scribe'}
TASK_IDENTITY_KEYS = {'schema', 'handle', 'task', 'step', 'round', 'role'}
TASK_SEGMENT = re.compile(r'[1-9][0-9]*|[a-z0-9]+(?:-[a-z0-9]+)*')
GITHUB_ORIGIN = re.compile(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git')


def _positive(value) -> bool:
    return type(value) is int and value > 0


def checked_next(observed, expected: dict, *, legacy: bool):
    """Return the delegate identity after checking one whole `next` result.

    The manifest records the directive without its delegation envelope. Every
    other key must equal the manifest's; `agent` and `task_identity` are held to
    the delegate that directive names. A legacy log was recorded by a probe that
    dropped `agent` under a controller that emitted no `task_identity`.
    """
    if not isinstance(observed, dict) or not isinstance(expected, dict):
        raise ValueError('restored next differs from manifest')
    rest = dict(observed)
    if legacy:
        if rest != expected:
            raise ValueError('restored next differs from manifest')
        return None
    if 'agent' not in rest or 'task_identity' not in rest:
        raise ValueError('restored next omits its delegation envelope')
    agent, identity = rest.pop('agent'), rest.pop('task_identity')
    if rest != expected:
        raise ValueError('restored next differs from manifest')
    role = DELEGATES.get(expected.get('do'))
    if role is None:
        if agent is not None or identity is not None:
            raise ValueError('restored next names a delegate its directive lacks')
        return None
    if agent != role or not isinstance(identity, dict) or set(identity) != TASK_IDENTITY_KEYS:
        raise ValueError('restored next delegate differs from its directive')
    step = None if role == 'surveyor' else expected.get('step')
    round_ = expected.get('round') if role == 'warden' else None
    task = identity['task']
    if (identity['schema'] != 'fiat-task-identity/v1' or identity['role'] != role
            or identity['step'] != step or (step is not None and not _positive(step))
            or identity['round'] != round_ or (round_ is not None and not _positive(round_))
            or type(task) is not str or not TASK_SEGMENT.fullmatch(task)
            or identity['handle'] != 'fiat-{}-{}-{}'.format(
                task, 'study' if step is None else 'step-{}'.format(step), role)):
        raise ValueError('restored next task identity differs from its directive')
    return identity


def checked_origin_refs(event: dict, runtime: dict) -> dict:
    """Hold the rewritten origin to the verified bundle's exact refs."""
    if (event.get('bundle_sha256') != runtime.get('bundle_sha256')
            or not isinstance(event.get('bundle_refs_sha256'), str)
            or not measure.HEX.fullmatch(event['bundle_refs_sha256'])
            or not _positive(event.get('refs'))):
        raise ValueError('origin refs are not the verified bundle')
    url = event.get('origin_url')
    if url is None:
        if event.get('origin_refs_sha256') is not None:
            raise ValueError('origin refs recorded without an origin')
    elif (not isinstance(url, str) or not GITHUB_ORIGIN.fullmatch(url)
            or event.get('origin_refs_sha256') != event['bundle_refs_sha256']):
        raise ValueError('origin refs differ from the verified bundle')
    return {'scope': 'archived-bundle-refs', 'origin_url': url,
            'bundle_refs_sha256': event['bundle_refs_sha256'], 'refs': event['refs'],
            'live_github_read_required': True}


def assemble_transcript(log: str, *, expected: str, controller_sha256: str,
                        base_digest: str, derived_digest: str, network: str,
                        export: dict, rss_text: str, producer_platform: str) -> dict:
    """Validate recorded probe operations and compute all transcript joins."""
    if len(log.encode()) > measure.OUTPUT_CAP:
        raise ValueError('probe log exceeds byte limit')
    events = [json.loads(line) for line in log.splitlines() if line.strip()]
    sequence = tuple(event.get('operation') for event in events)
    if sequence not in (OPERATIONS, UNANCHORED_OPERATIONS, LEGACY_OPERATIONS):
        raise ValueError('probe operations are missing, repeated or reordered')
    legacy = sequence == LEGACY_OPERATIONS
    records = dict(zip(sequence, events))
    start, runtime = records['start'], records['runtime']
    if network != 'none' or start.get('keyring_empty') is not True:
        raise ValueError('container isolation was not established')
    if start.get('input_files') != ['checkpoint.zip', 'checkpoint.zip.sha256', 'hexctl.py']:
        raise ValueError('unexpected container input inventory')
    if start.get('controller_sha256') != controller_sha256 or runtime.get('controller_sha256') != controller_sha256:
        raise ValueError('controller identity differs')
    if runtime.get('controller_overlay_verified') is not True or runtime.get('destination_was_empty') is not True:
        raise ValueError('runtime overlay or empty destination not established')
    for name in sequence:
        if name in UNCOMMANDED:
            continue
        if records[name].get('exit') != 0 or type(records[name].get('exit')) is not int:
            raise ValueError('a probe command failed')
        measure.checked_integer(records[name].get('wall_ms'))
    inspected = records['inspect']['result']
    restored = records['restore']['result']
    if (inspected.get('schema') != 'fiat-checkpoint-inspect/v1' or inspected.get('findings') != []
            or inspected.get('outer_sha256') != expected or restored.get('outer_sha256') != expected
            or restored.get('schema') != 'fiat-checkpoint-archive-restore/v1'
            or restored.get('verify') != 'ok' or records['status'].get('json_object') is not True):
        raise ValueError('archive or restored controller verification differs')
    expected_next = runtime['manifest_next']
    snapshot = runtime['snapshot_id']
    if restored['next'] != expected_next or restored['restore']['next'] != expected_next:
        raise ValueError('restored next differs from manifest')
    identity = checked_next(records['next']['result'], expected_next, legacy=legacy)
    if not legacy:
        origin = checked_origin_refs(records['origin-refs'], runtime)
        if (sequence == OPERATIONS) != (origin['origin_url'] is not None):
            raise ValueError('origin configuration differs from the recorded origin')
    if (not isinstance(snapshot,str) or not measure.HEX.fullmatch(snapshot)
            or inspected['identity'].get('snapshot_id') != snapshot
            or restored['snapshot_id'] != snapshot or records['identity']['result']['snapshot_id'] != snapshot):
        raise ValueError('restored identity differs from manifest')
    if export['outer_sha256'] != expected or inspected['bytes'] != export['bytes']:
        raise ValueError('producer measurements belong to another archive')
    measurements = measure.saved_measurements(export,rss_text,system=producer_platform,
        inspect_ms=records['inspect']['wall_ms'],restore_ms=records['restore']['wall_ms'],
        expanded_bytes=runtime['expanded_bytes'])
    record = {'schema':SCHEMA,'network':network,'keyring':'empty-at-start',
        'destination_was_empty':True,'hexctl_verify_exit':0,
        'next_matches_manifest':True,'snapshot_id_matches':True,
        'outer_sha256':expected,'manifest_sha256':runtime['manifest_sha256'],
        'capsule_manifest_sha256':runtime['capsule_manifest_sha256'],
        'snapshot_id':snapshot,'next':expected_next,'controller_sha256':controller_sha256,
        'base_image_digest':base_digest,'derived_image_digest':derived_digest,
        'runtime':{key:runtime[key] for key in ('runtime_commit','bundle_sha256',
            'bundled_controller_sha256','controller_overlay_verified')},
        'measurement_scope':{'producer_platform':producer_platform,
            'export':'saved controller timing_ms.export interval; peak RSS covers whole producer command',
            'consumer':'one whole inspect/restore command inside the network-disabled Linux container'},
        'measurements':measurements,'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
    if not legacy:
        # A log recorded before these checks carries neither member.
        record['next_task_identity'] = identity
        record['origin_refs'] = origin
    return record


def demonstrate(archive: Path, expected: str, image: str, transcript: Path) -> dict:
    if image != 'python:3.14-slim':
        raise ValueError('only the study base image is supported')
    export,rss = measure.read_export(Path.cwd(),archive,expected)
    controller = Path(__file__).with_name('hexctl.py').resolve()
    controller_digest = measure.digest(controller)
    inspected = measure.require_success(measure.command(['docker','image','inspect',image]))
    metadata = json.loads(inspected['stdout'])[0]
    matches = [item for item in metadata['RepoDigests'] if re.fullmatch(r'(?:docker.io/library/)?python@sha256:[0-9a-f]{64}',item)]
    if len(matches) != 1:
        raise ValueError('base image has no unique immutable digest')
    base = matches[0]
    with tempfile.TemporaryDirectory(prefix='checkpoint-clean-machine-') as temporary:
        scratch = Path(temporary).resolve()
        context = scratch/'build'; context.mkdir()
        (context/'Dockerfile').write_text('FROM '+base+'\nRUN apt-get update && apt-get install -y --no-install-recommends git gnupg && rm -rf /var/lib/apt/lists/*\n')
        image_id_file = scratch/'image-id'
        measure.require_success(measure.command(['docker','build','--pull=false','--iidfile',str(image_id_file),str(context)],timeout=600))
        derived = measure.read_bytes(image_id_file).decode().strip()
        if not re.fullmatch(r'sha256:[0-9a-f]{64}',derived):
            raise ValueError('derived image digest is invalid')
        inputs = scratch/'input';inputs.mkdir()
        measure.snapshot_archive(archive,inputs/'checkpoint.zip',expected,export['bytes'])
        (inputs/'checkpoint.zip.sha256').write_bytes(measure.read_bytes(
            archive.with_name('checkpoint.zip.sha256'),maximum=4096))
        (inputs/'hexctl.py').write_bytes(measure.read_bytes(controller))
        if measure.digest(inputs/'checkpoint.zip') != expected or measure.digest(inputs/'hexctl.py') != controller_digest:
            raise ValueError('input copy changed')
        probe = 'import os, selectors, signal, subprocess, time\nOUTPUT_CAP=2097152\n'+inspect.getsource(measure.command)+'\n'+PROBE
        owner = uuid.uuid4().hex
        container_name = 'checkpoint-proof-' + owner
        container = None
        try:
            created = measure.require_success(measure.command(['docker','create','--network','none',
                '--name',container_name,'--label','fiat.checkpoint.proof='+owner,
                '--entrypoint','python',derived,'-c',probe,expected]))
            container = created['stdout'].strip()
            if not re.fullmatch(r'[0-9a-f]{64}',container):
                raise ValueError('container id is invalid')
            measure.require_success(measure.command(['docker','cp',str(inputs),container+':/input']))
            info = json.loads(measure.require_success(measure.command(['docker','inspect',container]))['stdout'])[0]
            network = info['HostConfig']['NetworkMode']
            if network != 'none' or info['Mounts']:
                raise ValueError('container has network or host mounts')
            result = measure.command(['docker','start','--attach',container],timeout=240)
            transcript.parent.mkdir(parents=True,exist_ok=True)
            log_path = transcript.with_suffix('.log')
            log_path.write_text(result['stdout'],encoding='utf-8')
            measure.require_success(result)
            state = json.loads(measure.require_success(measure.command(['docker','inspect',container]))['stdout'])[0]['State']
            if state['Running'] or state['ExitCode'] != 0:
                raise ValueError('container did not complete successfully')
            record = assemble_transcript(result['stdout'],expected=expected,controller_sha256=controller_digest,
                base_digest=base.split('@',1)[1],derived_digest=derived,network=network,
                export=export,rss_text=rss,producer_platform=sys.platform)
            measure.write_json(transcript,record)
            return record
        finally:
            # Creation can reach the daemon even when its CLI times out. Resolve
            # the unique owned name and remove only its immutable, labelled ID.
            found = measure.command(['docker','inspect',container_name])
            if found['exit'] == 0 and not found['failure']:
                owned = json.loads(found['stdout'])[0]
                identifier = owned['Id']
                if (owned['Config'].get('Labels',{}).get('fiat.checkpoint.proof') != owner
                        or not re.fullmatch(r'[0-9a-f]{64}',identifier)
                        or (container is not None and container != identifier)):
                    raise ValueError('container cleanup ownership differs')
                measure.require_success(measure.command(['docker','rm','--force',identifier]))
            elif container is not None:
                measure.require_success(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--archive',required=True,type=Path)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--image',required=True)
    parser.add_argument('--transcript',required=True,type=Path)
    args=parser.parse_args()
    try:
        result=demonstrate(args.archive.resolve(),args.sha256,args.image,args.transcript)
    except (OSError, ValueError, KeyError, TypeError) as error:
        measure.write_json(args.transcript.with_suffix('.failure.json'), {
            'schema':'fiat-checkpoint-clean-machine-failure/v1', 'failure':type(error).__name__,
            'operation':getattr(error,'record',None)})
        print('checkpoint_clean_machine: refused: '+type(error).__name__,file=sys.stderr)
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
