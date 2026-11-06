#!/usr/bin/env python3
"""Reconstruct a complete replacement before executing mapped current guards.

A separately named native Git repository supplies historical provenance.
Pending transactions preserve their originals and block ordinary acceptance.
"""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import uuid


def sibling(name):
    spec = importlib.util.spec_from_file_location('fiat_replacement_' + name,
                                                Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module; spec.loader.exec_module(module)
    return module


packet = sibling('carryover')
worker = sibling('worker_exec')
adapter = sibling('inoculation')
Refusal = packet.Refusal
require = packet.require
PENDING = 'replacement_pending'
ADMITTED = 'replacement_admission'
MAX_BYTES = 256 * 1024 * 1024
MAX_FILE = 64 * 1024 * 1024
MAX_FILES = 4096
SCHEMA = 'fiat-replacement-admission/v1'


def directory_identity(path):
    root = worker._absolute_directory(path)
    fd = worker._open_dir(root)
    try:
        info = os.fstat(fd)
        return {'path':str(root),'device':info.st_dev,'inode':info.st_ino}
    finally:
        os.close(fd)


def current_identity(controller, root, state):
    return {'run':controller.controller_run_id(state), 'root':directory_identity(root),
            'base':state['base'], 'head':packet.resolve(controller,root,'HEAD'),
            'base_tree':packet.tree(controller,root,state['base'])}


def base_inventory(controller, root, base):
    raw = packet.native(controller,root,['ls-tree','-r','-z',base])
    inventory = []
    for entry in raw.split(b'\0'):
        if not entry: continue
        metadata, name = entry.split(b'\t',1); mode, kind, oid = metadata.decode().split()
        require(kind=='blob' and mode in ('100644','100755'),'unsupported-base-mode')
        name=packet.path(name.decode('utf-8'))
        inventory.append({'path':name,'mode':mode,'oid':oid})
    packet.paths([r['path'] for r in inventory])
    require(len(inventory)<=MAX_FILES-3,'base-file-cap')
    return inventory


def copy_base(root, destination, inventory):
    """Stream held clean-base files, including large media, against Git blob IDs."""
    remaining=MAX_BYTES//2; root_fd=worker._open_dir(root); result=[]
    try:
        for row in inventory:
            parent=os.dup(root_fd)
            try:
                parts=row['path'].split('/')
                for part in parts[:-1]:
                    child=worker._open_dir(part,parent);os.close(parent);parent=child
                fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                try:
                    before=os.fstat(fd)
                    require(stat.S_ISREG(before.st_mode) and before.st_nlink==1
                            and before.st_size<=min(MAX_FILE,remaining),'base-file-boundary')
                    require(bool(before.st_mode & 0o111)==(row['mode']=='100755'),'base-mode-drift')
                    git_hash=hashlib.sha1() if len(row['oid'])==40 else hashlib.sha256()
                    git_hash.update(('blob '+str(before.st_size)+'\0').encode())
                    checksum=hashlib.sha256();size=0
                    target=destination/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
                    with target.open('xb') as output:
                        while chunk:=os.read(fd,worker.CHUNK):
                            size+=len(chunk);require(size<=before.st_size,'base-file-drift')
                            git_hash.update(chunk);checksum.update(chunk);output.write(chunk)
                        output.flush();os.fsync(output.fileno())
                    require(size==before.st_size and worker._stamp(os.fstat(fd))==worker._stamp(before)
                            and git_hash.hexdigest()==row['oid'],'base-blob-drift')
                    target.chmod(int(row['mode'],8)&0o777)
                    remaining-=size;result.append({**row,'bytes':size,'sha256':checksum.hexdigest()})
                finally:os.close(fd)
            finally:os.close(parent)
    finally:os.close(root_fd)
    return result


def occurrence_key(occurrence):
    return {'identity':occurrence['identity'],'ordinal':occurrence['ordinal'],
            'offset':occurrence['offset'],'raw_sha256':occurrence['raw']['sha256']}


def mappings(value, request):
    packet.closed(request,'schema packet proof_repository attachment files occurrences execution')
    require(request['schema']=='fiat-replacement-request/v1','replacement-request-schema')
    packet.closed(request['packet'],'path sha256')
    source_files={row['path']:row for row in value['files']}
    require(type(request['files']) is list and len(request['files'])==len(source_files),'partial-file-mapping')
    seen=set();targets=[];budget=[packet.MAX_BYTES]
    for mapping in request['files']:
        packet.closed(mapping,'source target disposition result reason base')
        packet.closed(mapping['base'],'source target')
        source=packet.path(mapping['source']);require(source in source_files and source not in seen,'file-mapping-source')
        seen.add(source);packet.text(mapping['reason'])
        require(mapping['disposition'] in ('unchanged','transformed','conflicted'),'file-mapping-disposition')
        if mapping['target'] is not None:targets.append(packet.path(mapping['target']))
        result=mapping['result']
        if result is not None:
            packet.closed(result,'mode payload');require(result['mode'] in ('100644','100755'),'mapping-mode')
            packet.unblob(result['payload'],budget);require(mapping['target'] is not None,'mapping-target')
        else:require(mapping['target'] is None,'mapping-deletion')
        if mapping['disposition']=='unchanged':
            original=source_files[source]
            expected=None if original['mode']=='delete' else {'mode':original['mode'],'payload':original['payload']}
            require(result==expected and mapping['target']==(source if expected else None),'unchanged-mapping-drift')
    packet.paths(targets)
    occurrences=[]
    blocking={'legacy-producer-missing','legacy-producer-span','legacy-finding-count','entry_sha256'}
    for source in value['passes']:
        for round_record in source['rounds']:
            require(not blocking.intersection(round_record['unknown']),'unknown-producer-evidence')
            occurrences.extend(round_record['occurrences'])
    require(type(request['occurrences']) is list and len(request['occurrences'])==len(occurrences),
            'missing-occurrence')
    expected={packet.canonical(occurrence_key(o)):o for o in occurrences}
    require(len(expected)==len(occurrences),'duplicate-raw-occurrence')
    seen=set();guard_ids=set();families=set()
    for mapping in request['occurrences']:
        packet.closed(mapping,'occurrence guard family previous_guard previous_family reason')
        key=packet.canonical(mapping['occurrence']);require(key in expected and key not in seen,'occurrence-mapping')
        seen.add(key);source=expected[key]
        require(mapping['previous_guard']==source['guard'] and mapping['previous_family']==source['family'],
                'historical-identity-mismatch')
        packet.text(mapping['guard']);packet.text(mapping['family']);packet.text(mapping['reason'])
        guard_ids.add(mapping['guard']);families.add(mapping['family'])
    execution=request['execution'];packet.closed(execution,'schema guards dependencies')
    require(type(execution['guards']) is list and {g['id'] for g in execution['guards']}==guard_ids
            and {g['family'] for g in execution['guards']}==families,'guard-family-coverage')
    for mapping in request['occurrences']:
        require(any(g['id']==mapping['guard'] and g['family']==mapping['family'] for g in execution['guards']),
                'occurrence-family-coverage')
    return occurrences


def preimage(row):
    return None if row is None else {'mode':row['mode'],'oid':row['oid']}


def bind_base(controller, root, base, value, request):
    inventory=base_inventory(controller,root,base)
    current={row['path']:row for row in inventory}
    proof=Path(request['proof_repository'])
    previous={row['path']:row for row in base_inventory(controller,proof,value['passes'][-1]['original_commit'])}
    final=set(current)
    for mapping in request['files']:
        source=mapping['source'];target=mapping['target']
        require(mapping['base']=={'source':preimage(current.get(source)),
                                  'target':preimage(current.get(target))},'current-base-preimage')
        intended=None
        if mapping['result'] is not None:
            data=packet.unblob(mapping['result']['payload'],[packet.MAX_BYTES])
            intended={'mode':mapping['result']['mode'],
                      'oid':hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()}
        source_conflict=(preimage(current.get(source))!=preimage(previous.get(source))
                         and preimage(current.get(source))!=intended)
        target_conflict=(target is not None and target!=source and target in current
                         and preimage(current[target])!=intended)
        require(not(source_conflict or target_conflict) or mapping['disposition']=='conflicted',
                'current-base-conflict')
        final.discard(source)
    for mapping in request['files']:
        if mapping['target'] is not None:final.add(mapping['target'])
    packet.paths(sorted(final));require(len(final)<=MAX_FILES-3,'reconstruction-file-cap')
    return inventory


def reconstruct(controller, root, base, value, request, destination):
    inventory=bind_base(controller,root,base,value,request)
    destination.mkdir(mode=0o700)
    original=copy_base(root,destination,inventory)
    original_paths={r['path'] for r in original}
    replaced={m['source'] for m in request['files']} | {m['target'] for m in request['files']}
    final_bytes=sum(r['bytes'] for r in original if r['path'] not in replaced)
    final_bytes+=sum(m['result']['payload']['bytes'] for m in request['files'] if m['result'] is not None)
    require(final_bytes<=MAX_BYTES//2,'reconstruction-copy-byte-cap')
    for mapping in request['files']:
        target=destination/mapping['source']
        if mapping['source'] in original_paths:target.unlink()
    for mapping in request['files']:
        if mapping['target'] is None:continue
        target=destination/mapping['target'];target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():target.unlink()
        payload=packet.unblob(mapping['result']['payload'],[packet.MAX_BYTES])
        with target.open('xb') as output:output.write(payload);output.flush();os.fsync(output.fileno())
        target.chmod(int(mapping['result']['mode'],8)&0o777)
    fd=worker._open_dir(destination)
    try:final=worker._input_inventory(fd)
    finally:os.close(fd)
    require(len(final)<=MAX_FILES-3,'reconstruction-file-cap')
    return original,final


def write_json(directory, name, value):
    fd=worker._open_dir(directory)
    try:worker._exclusive(fd,name,packet.canonical(value))
    finally:os.close(fd)


def read_json(path):
    return packet.load(packet.read_regular(path))


def sources():
    return {name:packet.digest(Path(__file__).with_name(name+'.py').read_bytes())
            for name in ('hexctl','carryover','replacement','inoculation','worker_exec')}


def transaction(root, pending):
    identity=directory_identity(pending['directory']['path'])
    require(identity==pending['directory'],'replacement-directory-drift')
    directory=Path(identity['path'])
    require(directory.parent==root/'.hexaemeron/replacements','replacement-directory-boundary')
    require(sources()==pending['sources'],'replacement-source-drift')
    raw=packet.read_regular(directory/'request.json')
    require(packet.digest(raw)==pending['request_sha256'],'replacement-request-drift')
    request=packet.load(raw)
    data=packet.read_regular(directory/'packet.md')
    require(packet.digest(data)==pending['packet_sha256'],'replacement-packet-drift')
    require(directory_identity(request['proof_repository'])==pending['proof_repository'],'proof-repository-drift')
    return directory,request,data


def begin(controller, root, request):
    root=worker._absolute_directory(root)
    controller.verify_run(str(root));state=controller.load_state(str(root))
    require(not state.get('halted'),'replacement-run-halted')
    require(state['phase']=='study' and not state['steps'] and state['current_step'] is None
            and not state['receipts'].get(PENDING) and not state['receipts'].get(ADMITTED)
            and not state['receipts'].get('carryover_parent'),'fresh-replacement-run-required')
    packet.closed(request,'schema packet proof_repository attachment files occurrences execution')
    packet.closed(request['packet'],'path sha256')
    proof=worker._absolute_directory(request['proof_repository'])
    data=packet.read_regular(request['packet']['path'])
    value=packet.validate(controller,proof,data,request['packet']['sha256'])
    require(value['issue']==state['receipts'].get('task_issue'),'replacement-issue-mismatch')
    identity=current_identity(controller,root,state)
    require(identity['head']==identity['base'],'replacement-base-head')
    require(not packet.native(controller,root,['status','--porcelain','--untracked-files=all']), 'replacement-base-dirty')
    mappings(value,request);bind_base(controller,root,state['base'],value,request)
    attachment=packet.attachment(request['attachment'])
    require(attachment['url'].rsplit('/',1)[-1]==value['filename'],'attachment-name')
    packet.attachment_readback(attachment,request['packet']['sha256'],len(data))
    root_fd=worker._open_dir(root)
    name=uuid.uuid4().hex
    try:
        directory_fd=worker._directory_at(root_fd,['.hexaemeron','replacements',name],create=True)
        try:
            worker._exclusive(directory_fd,'request.json',packet.canonical(request))
            worker._exclusive(directory_fd,'packet.md',data)
        finally:os.close(directory_fd)
    finally:os.close(root_fd)
    directory=root/'.hexaemeron/replacements'/name
    pending={'schema':'fiat-replacement-pending/v1','status':'prepared','identity':identity,
             'directory':directory_identity(directory),'sources':sources(),
             'request_sha256':packet.digest(packet.canonical(request)),
             'packet_sha256':request['packet']['sha256'],'proof_repository':directory_identity(proof),
             'attachment':attachment,'attachment_readback_bytes':len(data),
             'sequence':value['sequence'],'source_runs':[p['source_run'] for p in value['passes']]}
    require(current_identity(controller,root,state)==identity,'replacement-origin-drift')
    state['receipts'][PENDING]=pending
    controller.commit(str(root),state,'replacement:begin',pending)
    return pending


def private_storage(stage):
    identity=read_json(stage/'private.json')
    require(directory_identity(identity['path'])==identity,'replacement-private-drift')
    return Path(identity['path'])


def image_path(stage):
    return private_storage(stage)/'image'


def execute_guards(root, staging, request):
    storage=private_storage(staging)
    image=storage/'image';image.mkdir(mode=0o700)
    # Move the complete reconstruction into its final input namespace before
    # even the inert source filter runs. No target module is imported.
    (storage/'candidate').rename(image/'candidate')
    driver=Path(__file__).with_name('inoculation.py').read_bytes()
    execution_request=packet.canonical(request['execution'])
    candidate_bytes=sum(row['bytes'] for row in inventory_path(image/'candidate'))
    require(candidate_bytes+len(driver)+len(execution_request)<=MAX_BYTES//2,'driver-copy-byte-cap')
    (image/'inoculation.py').write_bytes(driver)
    (image/'request.json').write_bytes(execution_request)
    fd=worker._open_dir(image)
    try:before=worker._input_inventory(fd)
    finally:os.close(fd)
    verify_driver_input(before,request)
    adapter.prepare(image/'candidate',request['execution'])
    paths,_,_=worker.tool_inventory()
    captured=worker.run_worker(root,[str(paths['python']),'-I','input/inoculation.py',
                              'input/request.json','input/candidate','output/inoculation.json'],
                              input_root=image,outputs=['inoculation.json'],
                              deadline_seconds=300,output_cap_bytes=worker.MAX_CAP)
    write_json(staging,'capture.json',captured.record)
    packet.publish(str(staging/'stdout.bin'),captured.stdout)
    packet.publish(str(staging/'stderr.bin'),captured.stderr)
    require(captured.record['status']=='captured','inoculation-worker-refused')
    report=Path(captured.record['snapshot'])/'inoculation.json'
    raw=packet.read_regular(report,worker.MAX_CAP);result=packet.load(raw)
    expected=request['execution']['guards']
    require(result.get('schema')==adapter.SCHEMA and result.get('passed') is True
            and type(result.get('rows')) is list and len(result['rows'])==len(expected),'inoculation-not-passed')
    for guard,row in zip(expected,result['rows']):
        require(all(row.get(k)==guard[k] for k in ('id','family','source','body_sha256'))
                and row.get('entered') is True and row.get('completed') is True
                and row.get('status')=='passed' and type(row.get('assertions')) is int
                and row['assertions']>0,'inoculation-execution-identity')
    fd=worker._open_dir(image)
    try:require(worker._input_inventory(fd)==before,'reconstruction-drift')
    finally:os.close(fd)
    packet.publish(str(staging/'inoculation.json'),raw)
    return {'report_sha256':packet.digest(raw),'capture_sha256':packet.digest(packet.canonical(captured.record)),
            'input_sha256':captured.record['input']['sha256'],'image_inventory':before,
            'stdout_sha256':packet.digest(captured.stdout),'stderr_sha256':packet.digest(captured.stderr)}


def verify_driver_input(inventory, request):
    rows={row['path']:row for row in inventory}
    require(rows.get('inoculation.py',{}).get('sha256')==sources()['inoculation']
            and rows.get('request.json',{}).get('sha256')==packet.digest(packet.canonical(request['execution'])),
            'replacement-driver-input-drift')


def verify_execution(stage, request, proof):
    capture_bytes=packet.read_regular(stage/'capture.json',worker.MAX_CAP)
    require(packet.digest(capture_bytes)==proof['capture_sha256'],'replacement-capture-drift')
    # Native capture records include measured fractional seconds. Their exact
    # producer bytes are checked before parsing; packet scalars remain stricter.
    capture=json.loads(capture_bytes)
    require(capture.get('status')=='captured' and capture.get('returncode')==0
            and capture['input']['inventory']==proof['image_inventory']
            and capture['input']['sha256']==proof['input_sha256'],'replacement-capture-binding')
    verify_driver_input(proof['image_inventory'],request)
    tools,runtime,executables=worker.tool_inventory()
    dependencies=worker.runtime_dependencies(runtime)
    require(capture['executables']==executables and capture['runtime_dependencies']==dependencies
            and capture['supervisor']==worker._identity(Path(worker.__file__))
            and capture['native_backend']==worker._identity(worker.SANDBOX),'replacement-runtime-drift')
    expected_argv=[str(tools['python']),'-I','input/inoculation.py','input/request.json',
                   'input/candidate','output/inoculation.json']
    require(capture['argv']==expected_argv and capture['source_argv']==expected_argv
            and capture['report_operands']==[] and capture['outputs']==['inoculation.json']
            and capture['deadline_seconds']==300 and capture['output_cap_bytes']==worker.MAX_CAP,
            'replacement-launch-drift')
    scratch=Path(capture['scratch_root'])
    policy=worker.policy_text(scratch,runtime,executables,dependencies,scratch/'input')
    require(packet.digest(policy.encode())==capture['policy_sha256'],'replacement-policy-drift')
    raw=packet.read_regular(stage/'inoculation.json')
    require(packet.digest(raw)==proof['report_sha256'],'replacement-execution-drift')
    require(capture['artifacts']==[{'path':'inoculation.json','bytes':len(raw),'sha256':packet.digest(raw)}]
            and capture['artifact_bytes']==len(raw),'replacement-artifact-binding')
    streams=[packet.read_regular(stage/(name+'.bin'),worker.MAX_CAP) for name in ('stdout','stderr')]
    require(all(packet.digest(data)==proof[name+'_sha256'] for name,data in zip(('stdout','stderr'),streams))
            and sum(map(len,streams))==capture['stream_bytes'],'replacement-stream-drift')
    require(packet.read_regular(Path(capture['snapshot'])/'inoculation.json')==raw,
            'replacement-private-capture-drift')
    result=packet.load(raw);expected=request['execution']['guards']
    require(result.get('schema')==adapter.SCHEMA and result.get('passed') is True
            and len(result.get('rows',[]))==len(expected),'replacement-not-passed')
    for guard,row in zip(expected,result['rows']):
        require(all(row.get(k)==guard[k] for k in ('id','family','source','body_sha256'))
                and row.get('entered') is True and row.get('completed') is True
                and row.get('status')=='passed' and type(row.get('assertions')) is int
                and row['assertions']>0,'replacement-guard-drift')


def read_working(root, name):
    target=root/name
    if not target.exists() and not target.is_symlink():return None
    data=packet.read_regular(target,MAX_FILE)
    mode='100755' if target.stat().st_mode&0o111 else '100644'
    return {'mode':mode,'bytes':len(data),'sha256':packet.digest(data)}


def expected_working(row):
    return None if row is None else {k:row[k] for k in ('mode','bytes','sha256')}


def parent_bindings(root, paths):
    names=set()
    for name in paths:
        parts=name.split('/')
        names.update('/'.join(parts[:index]) for index in range(1,len(parts)))
    result={}
    for name in sorted(names):
        target=root/name
        result[name]=directory_identity(target) if target.exists() or target.is_symlink() else None
    return result


def promote(root, directory, original, final, stage, parents):
    base={row['path']:row for row in original}
    current={row['path']:{**row,'mode':'100755' if row['mode']&0o111 else '100644'} for row in final}
    names=sorted(set(base)|set(current))
    changed=[name for name in names if expected_working(base.get(name))!=expected_working(current.get(name))]
    backup_bytes=sum(base[name]['bytes'] for name in changed if name in base)
    image_bytes=sum(row['bytes'] for row in inventory_path(image_path(stage)))
    temporary_bytes=max((current[name]['bytes'] for name in changed if name in current),default=0)
    require(image_bytes*2+backup_bytes*2+temporary_bytes<=MAX_BYTES,'promotion-copy-byte-cap')
    backups=private_storage(stage)/'originals';backups.mkdir(exist_ok=True,mode=0o700)
    for name in names:
        actual=read_working(root,name)
        require(actual in (expected_working(base.get(name)),expected_working(current.get(name))),
                'replacement-working-drift')
    with ExitStack() as descriptors:
        root_fd=worker._open_dir(root);descriptors.callback(os.close,root_fd)
        root_identity=directory_identity(root)
        held={}
        parent_record=stage/'promotion-parents.json'
        recorded=read_json(parent_record) if parent_record.exists() else None
        if recorded is not None:require(set(recorded)==set(parents),'promotion-parent-record')
        for name, expected in sorted(parents.items(),key=lambda item:(item[0].count("/"),item[0])):
            target=root/name
            if expected is None and recorded is not None:
                expected=recorded[name]
            if expected is None:
                require(not target.exists() and not target.is_symlink(),"promotion-parent-drift")
                target.mkdir(mode=0o700)
            else:
                require(directory_identity(target)==expected,"promotion-parent-drift")
            fd=worker._open_dir(target);descriptors.callback(os.close,fd)
            held[name]=(fd,directory_identity(target))
        if recorded is None:write_json(stage,'promotion-parents.json',{name:identity for name,(_,identity) in held.items()})
        def check_parents():
            require(directory_identity(root)==root_identity,'promotion-root-drift')
            for name,(fd,identity) in held.items():
                require(directory_identity(root/name)==identity and os.fstat(fd).st_ino==identity["inode"],
                        "promotion-parent-drift")
        check_parents()
        for name in changed:
            wanted=expected_working(current.get(name))
            if read_working(root,name)==wanted:
                if name in base:
                    require(packet.digest(packet.read_regular(backups/name,MAX_FILE))==base[name]['sha256'],
                            'original-backup-required')
                continue
            parts=name.split('/')
            check_parents()
            parent=os.dup(held['/'.join(parts[:-1])][0]) if len(parts)>1 else os.dup(root_fd)
            try:
                old=expected_working(base.get(name))
                require(read_working(root,name)==old,'replacement-working-drift')
                if old is not None:
                    backup=backups/name;backup.parent.mkdir(parents=True,exist_ok=True)
                    if not backup.exists():
                        packet.publish(str(backup),packet.read_regular(root/name,MAX_FILE))
                    require(packet.digest(packet.read_regular(backup,MAX_FILE))==old['sha256'],'original-backup-drift')
                temporary=None
                if wanted is not None:
                    data=packet.read_regular(image_path(stage)/'candidate'/name,MAX_FILE)
                    require(packet.digest(data)==wanted['sha256'],'candidate-promotion-drift')
                    temporary='.fiat-replacement-'+uuid.uuid4().hex
                    worker._exclusive(parent,temporary,data)
                    os.chmod(temporary,int(wanted['mode'],8)&0o777,dir_fd=parent,follow_symlinks=False)
                if old is not None:
                    # Preserve the actual displaced inode, including an edit
                    # after the earlier preimage check. Never replace over it.
                    slot=private_storage(stage)/('displaced-'+uuid.uuid4().hex)
                    slot.mkdir(mode=0o700)
                    write_json(stage,slot.name+'.json',{'path':name,'expected':old,
                               'directory':directory_identity(slot)})
                    displaced=worker._open_dir(slot)
                    try:
                        os.rename(parts[-1],'value',src_dir_fd=parent,dst_dir_fd=displaced)
                        os.fsync(displaced);os.fsync(parent)
                    finally:os.close(displaced)
                    require(read_working(slot,'value')==old,'independent-edit-preserved-in-displacement')
                check_parents()
                if temporary is not None:
                    # link is exclusive: a new independent destination causes
                    # refusal and remains untouched. The temporary stays ours.
                    os.link(temporary,parts[-1],src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False)
                    os.unlink(temporary,dir_fd=parent)
                os.fsync(parent)
                check_parents()
                require(read_working(root,name)==wanted,'promotion-directory-drift')
            finally:os.close(parent)
    require(all(read_working(root,name)==expected_working(current.get(name)) for name in names),
            'promotion-incomplete')
    return changed


def preservation_inventory(stage, original, final):
    base={r['path']:r for r in original}
    current={r['path']:{**r,'mode':'100755' if r['mode']&0o111 else '100644'} for r in final}
    storage=private_storage(stage)
    result={'originals':[],'displacements':[]}
    for name,row in base.items():
        if expected_working(row)==expected_working(current.get(name)):continue
        raw=packet.read_regular(storage/'originals'/name,MAX_FILE)
        require(len(raw)==row['bytes'] and packet.digest(raw)==row['sha256'],'original-backup-drift')
        result['originals'].append({'path':name,**expected_working(row)})
    metadata=sorted(stage.glob('displaced-*.json'))
    require(len(metadata)<=MAX_FILES,'displacement-record-cap')
    for path in metadata:
        record=read_json(path);packet.closed(record,'path expected directory')
        location=Path(record['directory']['path'])
        require(location.parent==storage and directory_identity(location)==record['directory'],
                'displacement-directory-drift')
        actual=read_working(location,'value')
        require(actual==record['expected'],'displacement-content-drift')
        result['displacements'].append({'record':path.name,'sha256':packet.digest(packet.read_regular(path)),
                                       'path':record['path'],'value':actual})
    return result


def inventory_path(path):
    fd=worker._open_dir(path)
    try:return worker._input_inventory(fd)
    finally:os.close(fd)


def resume(controller, root):
    root=worker._absolute_directory(root)
    state=controller.load_state(str(root),allow_pending_replacement=True)
    controller.verify_run(str(root),allow_pending_replacement=True)
    require(not state.get('halted'),'replacement-run-halted')
    pending=state['receipts'].get(PENDING);require(type(pending) is dict,'replacement-not-pending')
    directory,request,data=transaction(root,pending)
    require(current_identity(controller,root,state)==pending['identity'],'replacement-origin-drift')
    value=packet.validate(controller,Path(request['proof_repository']),data,pending['packet_sha256'])
    mappings(value,request)
    if pending['status']=='prepared':
        require(not packet.native(controller,root,['status','--porcelain','--untracked-files=all']),
                'replacement-base-dirty')
        stage=directory/('attempt-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
        storage=Path(tempfile.mkdtemp(prefix='.fiat-replacement-',dir=root.parent))
        require(root not in storage.parents,'replacement-private-boundary')
        write_json(stage,'private.json',directory_identity(storage))
        parents=parent_bindings(root,[r['path'] for r in base_inventory(controller,root,state['base'])]+
                                [m['target'] for m in request['files'] if m['target'] is not None])
        original,final=reconstruct(controller,root,state['base'],value,request,storage/'candidate')
        plan={'original':original,'final':final,'parents':parents}
        write_json(stage,'plan.json',plan)
        proof=execute_guards(root,stage,request)
        require(current_identity(controller,root,state)==pending['identity'],'replacement-origin-drift')
        pending={**pending,'status':'guarded','stage':directory_identity(stage),
                 'plan_sha256':packet.digest(packet.canonical(plan)),
                 'private':directory_identity(storage),'execution':proof}
        state['receipts'][PENDING]=pending
        controller.commit(str(root),state,'replacement:guarded',pending)
    require(pending['status'] in ('guarded','promoting'),'replacement-phase')
    stage=Path(pending['stage']['path']);require(directory_identity(stage)==pending['stage'],'replacement-stage-drift')
    require(directory_identity(private_storage(stage))==pending['private'],'replacement-private-drift')
    plan=read_json(stage/'plan.json');require(packet.digest(packet.canonical(plan))==pending['plan_sha256'],'replacement-plan-drift')
    require(inventory_path(image_path(stage))==pending['execution']['image_inventory'],'replacement-image-drift')
    require(packet.digest(packet.read_regular(stage/'inoculation.json'))==pending['execution']['report_sha256'],
            'replacement-execution-drift')
    verify_execution(stage,request,pending['execution'])
    pending={**pending,'status':'promoting'};state['receipts'][PENDING]=pending
    controller.commit(str(root),state,'replacement:promoting',pending)
    changed=promote(root,directory,plan['original'],plan['final'],stage,plan['parents'])
    require(current_identity(controller,root,state)==pending['identity'],'replacement-origin-drift')
    require(inventory_path(image_path(stage))==pending['execution']['image_inventory'],'replacement-image-drift')
    verify_execution(stage,request,pending['execution'])
    # Source refs are read again after promotion. Refusal leaves the pending
    # marker and retained originals; it does not claim transactional rollback.
    packet.validate(controller,Path(request['proof_repository']),data,pending['packet_sha256'])
    require(sources()==pending['sources'],'replacement-source-drift')
    receipt={**pending,'schema':SCHEMA,'status':'admitted','changed_paths':changed,
             'fresh_independent_audit_required':True,'historical_audit_reused':False,
             'preservation':preservation_inventory(stage,plan['original'],plan['final'])}
    del state['receipts'][PENDING]
    state['receipts'][ADMITTED]=receipt
    state['receipts']['carryover_parent']={'packet_sha256':pending['packet_sha256'],
                                         'sequence':value['sequence'],
                                         'source_runs':[p['source_run'] for p in value['passes']]}
    controller.commit(str(root),state,'replacement:admitted',receipt)
    return receipt


def verify_receipt(controller, root, state):
    receipt=state['receipts'].get(ADMITTED)
    if receipt is None:return
    require(receipt.get('schema')==SCHEMA and receipt.get('status')=='admitted'
            and receipt.get('fresh_independent_audit_required') is True
            and receipt.get('historical_audit_reused') is False,'replacement-receipt-shape')
    root=worker._absolute_directory(root)
    require(receipt['identity']['run']==controller.controller_run_id(state)
            and receipt['identity']['root']==directory_identity(root)
            and receipt['identity']['base']==state['base'],'replacement-run-identity')
    directory,request,data=transaction(root,receipt)
    value=packet.validate(controller,Path(request['proof_repository']),data,receipt['packet_sha256'])
    mappings(value,request)
    require(state['receipts'].get('carryover_parent')=={
        'packet_sha256':receipt['packet_sha256'],'sequence':value['sequence'],
        'source_runs':[p['source_run'] for p in value['passes']]},'replacement-parent-drift')
    stage=Path(receipt['stage']['path'])
    require(directory_identity(stage)==receipt['stage'],'replacement-stage-drift')
    require(directory_identity(private_storage(stage))==receipt['private'],'replacement-private-drift')
    plan=read_json(stage/'plan.json');require(packet.digest(packet.canonical(plan))==receipt['plan_sha256'],
                                            'replacement-plan-drift')
    require(inventory_path(image_path(stage))==receipt['execution']['image_inventory'],'replacement-image-drift')
    raw=packet.read_regular(stage/'inoculation.json');require(packet.digest(raw)==receipt['execution']['report_sha256'],
                                                           'replacement-execution-drift')
    require(preservation_inventory(stage,plan['original'],plan['final'])==receipt['preservation'],
            'replacement-preservation-drift')
    result=packet.load(raw);require(result.get('passed') is True,'replacement-not-passed')
    verify_execution(stage,request,receipt['execution'])
    events=[packet.load(line) for line in packet.read_regular(controller.ledger_path(str(root))).splitlines() if line]
    recorded=[e['data'] for e in events if e.get('event')=='replacement:admitted']
    require(recorded==[receipt],'replacement-ledger-mismatch')
