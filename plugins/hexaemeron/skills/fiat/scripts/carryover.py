"""Bounded inert cumulative export; replacement admission is unavailable.

The controller supplies its existing checkpoint and native Git verifiers.
Payloads are data, never commands. A detached receipt hashes final Markdown
bytes, avoiding a self-referential packet digest.
"""

import base64
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
from urllib.parse import urlsplit

MAX_BYTES = 64 * 1024 * 1024
MAX_ITEMS = 4096
MAX_PASSES = 32
SCHEMA = "fiat-carryover-packet/v1"
PREFIX = b"# Cumulative carryover packet\n\n```json\n"
SUFFIX = b"\n```\n"


class Refusal(ValueError):
    """A bounded refusal code, never an echo of untrusted content."""


def require(condition, code):
    if not condition:
        raise Refusal(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode()


def closed(value, keys):
    require(type(value) is dict and set(value) == set(keys.split()), "object-shape")
    return value


def text(value, ceiling=1024):
    require(type(value) is str and 0 < len(value.encode('utf-8')) <= ceiling
            and all(ord(c) >= 32 and ord(c) != 127 for c in value), "text-shape")
    return value


def sha(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "digest-shape")
    return value


def path(value, *, metadata=False):
    text(value)
    parts = value.split('/')
    require(not value.startswith('/') and '\\' not in value
            and all(p not in ('', '.', '..') for p in parts), "unsafe-path")
    require(value.isascii() and all(p == p.strip() and ':' not in p for p in parts), "ambiguous-path")
    if not metadata:
        require(all(p.casefold() not in ('.git', '.hexaemeron') for p in parts),
                "metadata-path")
    return value


def paths(values, *, metadata=False):
    require(len(values) <= MAX_ITEMS and len(set(values)) == len(values), "duplicate-path")
    folded = set()
    for value in values:
        path(value, metadata=metadata)
        name = value.casefold()
        require(name not in folded, "ambiguous-path")
        folded.add(name)
    for name in folded:
        require(not any('/'.join(name.split('/')[:i]) in folded
                        for i in range(1, len(name.split('/')))), "path-collision")


def load(data):
    require(type(data) is bytes and len(data) <= MAX_BYTES, "packet-byte-cap")
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "duplicate-json-key")
            result[k] = v
        return result
    def constant(_):
        raise Refusal('invalid-json-number')
    try:
        result = json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
        def visit(value, depth=0):
            require(depth <= 32, "json-depth")
            require(type(value) in (dict, list, str, int, bool, type(None)), "json-scalar")
            if isinstance(value, (dict, list)):
                require(len(value) <= MAX_ITEMS, "item-cap")
                if isinstance(value,dict):
                    for key in value: key.encode('utf-8')
                for item in (value.values() if isinstance(value, dict) else value):
                    visit(item, depth + 1)
            elif isinstance(value, str):
                value.encode('utf-8')
        visit(result)
        return result
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, Refusal):
            raise
        raise Refusal('invalid-json') from None


def read_regular(supplied, ceiling=MAX_BYTES):
    value = os.path.abspath(supplied)
    require(os.path.realpath(value) == value, 'symlink-path')
    fd = os.open(value, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'not-regular')
        require(before.st_size <= ceiling, 'packet-byte-cap')
        data = bytearray()
        while len(data) <= ceiling:
            chunk = os.read(fd, min(65536, ceiling + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        after = os.fstat(fd)
        # Reading may update access time. Bind identity, permissions, size and
        # modification/change times without treating that read as source drift.
        def identity(info):
            return tuple(getattr(info,key) for key in (
                'st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid',
                'st_size','st_mtime_ns','st_ctime_ns'))
        require(identity(before) == identity(after) and
                identity(os.stat(value, follow_symlinks=False)) == identity(after),
                'source-changed')
        require(len(data) <= ceiling, 'packet-byte-cap')
        return bytes(data)
    finally:
        os.close(fd)


def blob(data):
    return {'bytes': len(data), 'sha256': digest(data),
            'base64': base64.b64encode(data).decode('ascii')}


def unblob(value, budget):
    closed(value, 'bytes sha256 base64')
    require(type(value['bytes']) is int and 0 <= value['bytes'] <= budget[0], 'decoded-byte-cap')
    sha(value['sha256'])
    require(type(value['base64']) is str and len(value['base64']) <= ((value['bytes'] + 2)//3)*4,
            'encoded-byte-cap')
    try:
        data = base64.b64decode(value['base64'], validate=True)
    except (ValueError, UnicodeError):
        raise Refusal('invalid-base64') from None
    require(len(data) == value['bytes'] and digest(data) == value['sha256']
            and base64.b64encode(data).decode() == value['base64'], 'payload-digest')
    budget[0] -= len(data)
    return data


def native(controller, root, args):
    return controller._native_relation_git(str(root), args, 'carryover native object unavailable')


def resolve(controller, root, ref):
    text(ref)
    require(not ref.startswith('-') and controller.branch_name_ok(ref), 'fixed-ref-shape')
    result = native(controller, root, ['rev-parse', '--verify', ref + '^{commit}']).decode().strip()
    require(re.fullmatch(r'[0-9a-f]{40}', result), 'commit-shape')
    return result


def tree(controller, root, commit):
    return native(controller, root, ['rev-parse', commit + '^{tree}']).decode().strip()


def git_files(controller, root, original, fixed, ceiling=MAX_BYTES):
    require(re.fullmatch(r'[0-9a-f]{40}', original) and re.fullmatch(r'[0-9a-f]{40}', fixed),
            'commit-shape')
    raw = native(controller, root, ['diff-tree', '--no-commit-id', '--no-renames',
                                  '-r', '--raw', '-z', original, fixed])
    chunks = raw.split(b'\0'); result = []; remaining = min(MAX_BYTES,ceiling)
    require((len(chunks)-1)//2 <= MAX_ITEMS, 'item-cap')
    require(chunks[-1] == b'', 'diff-shape')
    for i in range(0, len(chunks)-1, 2):
        require(i+1 < len(chunks)-1, 'diff-shape')
        fields = chunks[i].decode('ascii').split()
        require(len(fields) == 5, 'diff-shape')
        old_mode, mode, old_oid, oid, change = fields
        require(old_mode[1:] in ('000000','100644','100755') and
                mode in ('000000','100644','100755'), 'special-git-mode')
        name = path(chunks[i+1].decode('utf-8'))
        data = b''
        if mode != '000000':
            size = int(native(controller, root, ['cat-file','-s',oid]))
            require(0 <= size <= min(remaining,controller.GIT_OUTPUT_MAX), 'git-blob-byte-cap')
            remaining -= size
            data = native(controller, root, ['cat-file','blob',oid])
            require(len(data)==size, 'git-blob-size')
        result.append({'path': name, 'mode': 'delete' if mode == '000000' else mode,
                       'payload': blob(data)})
    paths([f['path'] for f in result])
    require(sum(f['payload']['bytes'] for f in result) <= MAX_BYTES, 'decoded-byte-cap')
    return sorted(result, key=lambda f:f['path'])


def archive(controller, supplied, expected, ceiling=MAX_BYTES):
    archive_root = Path(supplied)
    require(archive_root.is_absolute() and str(archive_root.resolve())==str(archive_root), 'archive-path')
    total = 0; count = 0
    for directory, dirs, files in os.walk(archive_root, followlinks=False):
        for name in dirs + files:
            st = os.lstat(Path(directory)/name); count += 1
            require(count <= MAX_ITEMS and not stat.S_ISLNK(st.st_mode), 'archive-entry-cap')
            require(stat.S_ISDIR(st.st_mode) or (stat.S_ISREG(st.st_mode) and st.st_nlink==1), 'archive-special')
            total += st.st_size if stat.S_ISREG(st.st_mode) else 0
            require(total <= min(MAX_BYTES,ceiling), 'archive-byte-cap')
    verified = controller._checkpoint_restore_capsule(supplied, sha(expected))
    capsule, manifest, state, state_bytes, ledger_bytes, inventory = verified
    require(manifest['boundary']['kind'] == 'audit-verdict', 'not-exhausted')
    files = []
    total = 0
    for row in inventory:
        name = row['path']
        data = read_regular(Path(capsule)/name,min(MAX_BYTES,ceiling)-total)
        total += len(data)
        require(total <= MAX_BYTES, 'decoded-byte-cap')
        files.append({'path': path(name, metadata=True), 'payload': blob(data)})
    manifest_bytes = read_regular(Path(capsule)/controller.CHECKPOINT_MANIFEST_FILE,
                                  min(MAX_BYTES,ceiling)-total)
    return {'manifest': blob(manifest_bytes), 'files': files}, state, ledger_bytes


def replay_archive(controller, value, budget):
    closed(value, 'manifest files')
    manifest = unblob(value['manifest'], budget)
    require(type(value['files']) is list and len(value['files']) <= MAX_ITEMS, 'archive-shape')
    names = []
    for entry in value['files']:
        closed(entry, 'path payload')
        name = path(entry['path'], metadata=True)
        require(name.startswith(controller.CHECKPOINT_CONTROLLER_DIR+'/'), 'archive-path')
        names.append(name)
    paths(names, metadata=True)
    # Only controller evidence is materialised, inside a fresh private directory.
    # Changed-file payload is never written or executed by export or validation.
    with tempfile.TemporaryDirectory(prefix='carryover-evidence-') as temporary:
        root = Path(temporary).resolve()
        (root/controller.CHECKPOINT_CONTROLLER_DIR).mkdir()
        (root/controller.CHECKPOINT_MANIFEST_FILE).write_bytes(manifest)
        for entry in value['files']:
            name = entry['path']
            target = root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(unblob(entry['payload'], budget))
        verified = controller._checkpoint_restore_capsule(str(root), digest(manifest))
        require(verified[1]['boundary']['kind'] == 'audit-verdict', 'not-exhausted')
        return verified[2], verified[4]


def table_cells(line):
    """Split unescaped delimiters; retain producer escape bytes in each cell."""
    cells=[];current=[];slashes=0
    for character in line:
        if character=='|' and slashes%2==0:
            cells.append(''.join(current));current=[]
        else:
            current.append(character)
        slashes=slashes+1 if character=='\\' else 0
    cells.append(''.join(current))
    if cells and not cells[0].strip():cells.pop(0)
    if cells and not cells[-1].strip():cells.pop()
    return [cell.strip() for cell in cells]


def findings(data, source_run, step, round_number):
    """Keep physical rows and offsets; tuple identity groups, never deduplicates."""
    rows = []; offset = 0; in_table = False; columns = []
    for line in data.splitlines(keepends=True):
        decoded = line.decode('utf-8', 'replace').strip()
        cells = table_cells(decoded)
        if decoded.startswith('|') and cells and cells[0].lower().strip('`') in ('id','risk id'):
            in_table = True
            columns = [cell.lower().strip('`') for cell in cells]
        elif in_table and decoded.startswith('|'):
            if decoded == '| -- | -- | -- | none | -- |':
                offset += len(line)
                continue
            if not all(re.fullmatch(r':?-+:?', x) for x in cells):
                def declared(names):
                    if len(cells)!=len(columns):return None
                    matches=[i for i,name in enumerate(columns) if name in names]
                    if len(matches)!=1 or matches[0]>=len(cells): return None
                    value=cells[matches[0]]
                    return value if value not in ('','--','unknown') else None
                rows.append({'identity':[source_run,step,round_number,cells[0]],
                             'ordinal':len(rows),'offset':offset,'raw':blob(line),
                             'disposition':declared(('status','disposition')),
                             'guard':declared(('guard','guards','guard identities')),
                             'family':declared(('family','families','family identities'))})
        else:
            in_table = False
        offset += len(line)
    return rows


def pass_record(controller, root, state, ledger, evidence, archive_location, fixed_ref, inherited=(), ceiling=MAX_BYTES):
    step = controller.current_step(state)
    require(controller._next_directive(state).get('do') == 'audit-verdict', 'not-exhausted')
    refs = load(unblob(evidence['manifest'], [MAX_BYTES]))['boundary']['refs']
    original = refs.get(state['base'])
    fixed = resolve(controller, root, fixed_ref)
    require(fixed == controller.last_local_commit(step), 'fixed-receipt-mismatch')
    controller.verify_local_commit(str(root), fixed, 'carryover fixed tree', native_relation=True)
    source_run = controller.controller_run_id(state)
    text(source_run)
    events=[load(line) for line in ledger.splitlines() if line.strip()]
    actual_rounds=[e['data'] for e in events if e.get('event')=='audit-round']
    declared_rounds=[{'step':s['n'],**r} for s in state['steps'] for r in s.get('audit',{}).get('rounds',[])]
    require(actual_rounds==declared_rounds,'archive-round-inventory')
    rounds = []; budget = [min(MAX_BYTES,ceiling)]
    check_blobs(evidence,budget)
    for source_step in state['steps']:
        for entry in source_step.get('audit',{}).get('rounds',[]):
            producer = None; occurrences = []; unknown = []
            log = entry.get('log')
            if log:
                path(log)
                size = int(native(controller,root,['cat-file','-s',fixed+':'+log]))
                # The full producer, selected span and raw occurrence rows are
                # separately carried. Reserve their upper bound before fetching.
                require(0<=size<=min(budget[0]//3,controller.GIT_OUTPUT_MAX),'producer-byte-cap')
                producer_bytes = native(controller, root, ['show', fixed+':'+log])
                require(len(producer_bytes)==size,'producer-size')
                end = entry.get('log_end_offset'); expected = entry.get('entry_sha256')
                if type(end) is int and 0 < end <= len(producer_bytes) and expected:
                    prefix = producer_bytes[:end]
                    starts = [m.start() for m in re.finditer(rb'(?m)^## ',prefix)]
                    require(starts, 'producer-span')
                    selected = prefix[starts[-1]:]
                    require(digest(selected)==expected, 'producer-drift')
                else:
                    selected = producer_bytes
                    unknown.append('legacy-producer-span')
                producer = {'path':log,'payload':blob(producer_bytes), 'selected':blob(selected)}
                occurrences = findings(selected, source_run, source_step['n'], entry['round'])
                if entry.get('schema') in controller.AUDIT_RECORD_SCHEMAS:
                    require(len(occurrences)==entry['findings'],'producer-finding-count')
                else:
                    unknown.append('legacy-finding-count')
            else:
                unknown.append('legacy-producer-missing')
            for field in ('elenchus_verdict','fixes_commit','entry_sha256'):
                if entry.get(field) is None: unknown.append(field)
            for field in ('guard','family'):
                if any(o[field] is None for o in occurrences):
                    unknown.append(field+'-identities')
            record={'step':source_step['n'],'round':entry['round'],'receipt':entry,
                    'producer':producer,'occurrences':occurrences,'unknown':unknown}
            check_blobs(record,budget)
            rounds.append(record)
    require(rounds, 'missing-rounds')
    return {'source_run':source_run,'archive_location':text(archive_location,4096),
            'archive':evidence,'original_commit':original,'original_tree':tree(controller,root,original),
            'fixed_ref':fixed_ref,'fixed_commit':fixed,'fixed_tree':tree(controller,root,fixed),
            'rounds':rounds,'files':complete_files(controller,root,original,fixed,inherited,budget[0]//2)}


def attachment(value):
    closed(value, 'identity url')
    text(value['identity'],256); text(value['url'],2048)
    require(re.fullmatch(r'https://github\.com/user-attachments/files/[1-9][0-9]*/[A-Za-z0-9_.-]+',
                         value['url']), 'attachment-url')
    require(value['identity'] == value['url'].split('/')[-2], 'attachment-identity')
    return value


def issue(value):
    require(type(value) is str and re.fullmatch(
        r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*', value),
        'issue-url')
    return value


def filename(issue_url, sequence):
    require(type(sequence) is int and 1 <= sequence <= MAX_PASSES, 'sequence')
    return issue_url.rsplit('/',1)[1] + '-CARRYOVER' + ('' if sequence == 1 else '-'+str(sequence)) + '.md'


def packet_bytes(value):
    result = PREFIX + canonical(value) + SUFFIX
    require(len(result) <= MAX_BYTES, 'packet-byte-cap')
    return result


def check_blobs(value, budget):
    if isinstance(value, dict):
        if set(value) == {'bytes','sha256','base64'}:
            unblob(value, budget)
        else:
            for item in value.values(): check_blobs(item,budget)
    elif isinstance(value,list):
        for item in value: check_blobs(item,budget)


def cumulative(passes):
    final = {}
    for entry in passes:
        for item in entry['files']:
            final[item['path']] = item
    paths(list(final))
    return [final[name] for name in sorted(final)]


def remaining_pass_budget(passes):
    # Earlier pass bytes remain carried; reserve their current final inventory
    # too. New file extraction reserves a second copy for the new final view.
    budget=[MAX_BYTES]
    check_blobs(passes,budget)
    check_blobs(cumulative(passes),budget)
    return budget[0]


def validate(controller, root, data, expected_digest):
    """Replay source evidence and native Git objects; write no candidate files."""
    require(type(data) is bytes and len(data) <= MAX_BYTES, 'packet-byte-cap')
    require(digest(data) == sha(expected_digest), 'packet-digest')
    require(data.startswith(PREFIX) and data.endswith(SUFFIX), 'markdown-envelope')
    value = load(data[len(PREFIX):-len(SUFFIX)])
    closed(value, 'schema issue sequence filename previous_sha256 passes files')
    require(value['schema']==SCHEMA and packet_bytes(value)==data, 'packet-canonical')
    issue(value['issue'])
    require(value['filename']==filename(value['issue'],value['sequence']), 'sequence-name')
    require(type(value['passes']) is list and len(value['passes'])==value['sequence'], 'pass-count')
    if value['sequence']==1:
        require(value['previous_sha256'] is None,'unexpected-parent')
    else:
        sha(value['previous_sha256'])
    check_blobs(value,[MAX_BYTES])
    identities = []; previous_prefix_digest = None
    for number, record in enumerate(value['passes'],1):
        closed(record, 'source_run archive_location archive original_commit original_tree fixed_ref fixed_commit fixed_tree rounds files')
        state, ledger = replay_archive(controller,record['archive'],[MAX_BYTES])
        require(state['receipts'].get('task_issue') == value['issue'], 'source-issue-mismatch')
        expected = pass_record(controller,root,state,ledger,record['archive'],
                               record['archive_location'],record['fixed_ref'],
                               [f['path'] for p in value['passes'][:number-1] for f in p['files']],
                               remaining_pass_budget(value['passes'][:number-1]))
        require(canonical(record)==canonical(expected), 'source-inventory-mismatch')
        identity = (record['source_run'],controller.current_step(state)['n'])
        require(identity not in identities,'duplicate-source-pass'); identities.append(identity)
        inherited = state['receipts'].get('carryover_parent')
        if number == 1:
            require(inherited is None,'missing-prior-pass')
        else:
            closed(inherited,'packet_sha256 sequence source_runs')
            require(sha(inherited['packet_sha256'])==previous_prefix_digest,'lineage-prefix-digest')
            require(inherited['sequence']==number-1 and
                    inherited['source_runs']==[x[0] for x in identities[:-1]],'lineage-mismatch')
            if number == len(value['passes']):
                require(inherited['packet_sha256']==value['previous_sha256'],'lineage-digest')
        prefix={**value,'sequence':number,'filename':filename(value['issue'],number),
                'previous_sha256':previous_prefix_digest,'passes':value['passes'][:number],
                'files':cumulative(value['passes'][:number])}
        previous_prefix_digest=digest(packet_bytes(prefix))
    require(value['files']==cumulative(value['passes']),'cumulative-payload-mismatch')
    return value


def publish(destination, data):
    """Create one immutable output; a refused rename never removes other bytes."""
    target = Path(destination)
    require(target.is_absolute() and os.path.realpath(target.parent)==str(target.parent),
            'output-parent')
    parent = os.open(target.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        pinned = os.fstat(parent)
        require(os.stat(target.parent,follow_symlinks=False).st_ino==pinned.st_ino,'output-parent-drift')
        fd = os.open(target.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400,dir_fd=parent)
        try:
            remaining = memoryview(data)
            while remaining:
                written = os.write(fd,remaining);require(written>0,'output-write');remaining=remaining[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(parent)
        current = os.stat(target.parent,follow_symlinks=False)
        require((current.st_dev,current.st_ino)==(pinned.st_dev,pinned.st_ino),'output-parent-drift')
    finally:
        os.close(parent)


def proof_identity(value):
    location=Path(value)
    require(location.is_absolute() and os.path.realpath(location)==str(location),'proof-repository-path')
    fd=os.open(location,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        return {'path':str(location),'device':info.st_dev,'inode':info.st_ino}
    finally:os.close(fd)


def export(controller, root, request):
    """Export and receipt exact cumulative data while the exhausted round stays open."""
    closed(request,'archive manifest_sha256 fixed_ref previous out'+
           (' proof_repository' if 'proof_repository' in request else ''))
    proof_binding=proof_identity(request['proof_repository']) if 'proof_repository' in request else None
    root = Path(root).resolve()
    proof_root=Path(proof_binding['path']) if proof_binding else root
    controller.verify_run(str(root))
    state = controller.load_state(str(root)); step = controller.current_step(state)
    require(controller._next_directive(state).get('do')=='audit-verdict','not-exhausted')
    require(not state['receipts'].get('carryover_exports'),'already-exported')
    before_state = read_regular(controller.state_path(str(root)))
    before_ledger = read_regular(controller.ledger_path(str(root)))
    issue_url = issue(state['receipts'].get('task_issue'))
    passes = []; prior_digest = None
    if request['previous'] is not None:
        closed(request['previous'],'path sha256')
        prior_digest = sha(request['previous']['sha256'])
        prior = validate(controller,proof_root,read_regular(request['previous']['path']),prior_digest)
        require(prior['issue']==issue_url,'prior-issue-mismatch')
        passes = prior['passes']
    remaining=remaining_pass_budget(passes)
    evidence, captured, ledger = archive(controller,request['archive'],request['manifest_sha256'],remaining)
    archive_manifest=load(unblob(evidence['manifest'],[MAX_BYTES]))
    require(archive_manifest['source']['state_sha256']==digest(before_state) and
            controller.canonical(captured)==controller.canonical(state) and ledger==before_ledger,
            'archive-source-mismatch')
    record = pass_record(controller,root,state,ledger,evidence,
                         os.path.abspath(request['archive']),request['fixed_ref'],
                         [f['path'] for p in passes for f in p['files']],remaining)
    passes = [*passes,record];sequence=len(passes)
    value={'schema':SCHEMA,'issue':issue_url,'sequence':sequence,
           'filename':filename(issue_url,sequence),'previous_sha256':prior_digest,
           'passes':passes,'files':cumulative(passes)}
    data=packet_bytes(value); packet_digest=digest(data)
    validate(controller,proof_root,data,packet_digest)
    if proof_binding:require(proof_identity(proof_root)==proof_binding,'proof-repository-drift')
    require(Path(request['out']).name==value['filename'],'sequence-name')
    require(read_regular(controller.state_path(str(root)))==before_state and
            read_regular(controller.ledger_path(str(root)))==before_ledger,'controller-drift')
    require(resolve(controller,root,request['fixed_ref'])==record['fixed_commit'],'fixed-ref-drift')
    publish(request['out'],data)
    require(read_regular(request['out'])==data,'published-packet-drift')
    receipt={'schema':'fiat-carryover-export/v1','packet':request['out'],
             'packet_sha256':packet_digest,'issue':issue_url,'attachment':None,
             'attachment_status':'unbound','sequence':sequence,
             'source_runs':[p['source_run'] for p in passes],
             'fixed_ref':record['fixed_ref'],'fixed_commit':record['fixed_commit'],
             'fixed_tree':record['fixed_tree'],'archive':record['archive_location'],
             'archive_sha256':request['manifest_sha256'],
             'occurrences':[o['identity'] for p in passes for r in p['rounds'] for o in r['occurrences']],
             'source_state_sha256':digest(before_state),'source_ledger_sha256':digest(before_ledger),
             'replacement_admission':'unavailable'}
    if proof_binding:receipt['proof_repository']=proof_binding
    state['receipts']['carryover_exports']=[receipt]
    controller.commit(str(root),state,'carryover:export',receipt)
    return receipt


def complete_files(controller, root, original, fixed, inherited, ceiling=MAX_BYTES):
    result = {f['path']: f for f in git_files(controller,root,original,fixed,ceiling)}
    remaining = min(MAX_BYTES,ceiling) - sum(f['payload']['bytes'] for f in result.values())
    for name in sorted(set(inherited)-set(result)):
        path(name); require(len(result)<MAX_ITEMS, 'item-cap')
        raw = native(controller,root,['ls-tree','-z',fixed,'--',name])
        mode = 'delete'; data = b''
        if raw:
            require(raw.endswith(b'\0') and raw.count(b'\0')==1,'inherited-path-shape')
            meta, actual = raw[:-1].split(b'\t',1)
            mode, kind, oid = meta.decode('ascii').split()
            require(actual.decode('utf-8')==name and kind=='blob'
                    and mode in ('100644','100755'),'inherited-special-mode')
            size = int(native(controller,root,['cat-file','-s',oid]))
            require(0<=size<=min(remaining,controller.GIT_OUTPUT_MAX),'git-blob-byte-cap')
            remaining-=size; data=native(controller,root,['cat-file','blob',oid])
            require(len(data)==size,'git-blob-size')
        result[name]={'path':name,'mode':mode,'payload':blob(data)}
    paths(list(result))
    return [result[k] for k in sorted(result)]


def verify_receipts(controller, root, state):
    receipts=state['receipts'].get('carryover_exports')
    if receipts is None: return
    require(type(receipts) is list and len(receipts)==1,'export-receipt-shape')
    events=[e['data'] for e in controller.ledger_entries(str(root)) if e['event']=='carryover:export']
    require(events==receipts,'export-receipt-ledger')
    receipt=receipts[0]
    closed(receipt,'schema packet packet_sha256 issue attachment attachment_status sequence source_runs fixed_ref fixed_commit fixed_tree archive archive_sha256 occurrences source_state_sha256 source_ledger_sha256 replacement_admission'+
           (' proof_repository' if 'proof_repository' in receipt else ''))
    require(receipt['schema']=='fiat-carryover-export/v1' and
            receipt['replacement_admission']=='unavailable','export-receipt-shape')
    data=read_regular(receipt['packet'])
    require(digest(data)==sha(receipt['packet_sha256']),'export-packet-drift')
    proof_root=root
    if 'proof_repository' in receipt:
        binding=receipt['proof_repository'];closed(binding,'path device inode')
        require(proof_identity(binding['path'])==binding,'proof-repository-drift')
        proof_root=Path(binding['path'])
    packet=validate(controller,proof_root,data,receipt['packet_sha256'])
    last=packet['passes'][-1]
    manifest=load(unblob(last['archive']['manifest'],[MAX_BYTES]))
    expected={'schema':'fiat-carryover-export/v1','packet':receipt['packet'],
              'packet_sha256':digest(data),'issue':packet['issue'],'attachment':None,
              'attachment_status':'unbound','sequence':packet['sequence'],
              'source_runs':[p['source_run'] for p in packet['passes']],
              'fixed_ref':last['fixed_ref'],'fixed_commit':last['fixed_commit'],
              'fixed_tree':last['fixed_tree'],'archive':last['archive_location'],
              'archive_sha256':last['archive']['manifest']['sha256'],
              'occurrences':[o['identity'] for p in packet['passes'] for r in p['rounds'] for o in r['occurrences']],
              'source_state_sha256':manifest['source']['state_sha256'],
              'source_ledger_sha256':manifest['source']['ledger_sha256'],
              'replacement_admission':'unavailable'}
    if 'proof_repository' in receipt:expected['proof_repository']=receipt['proof_repository']
    require(receipt==expected,'export-receipt-binding')
    bindings=state['receipts'].get('carryover_attachments',[])
    events=[e['data'] for e in controller.ledger_entries(str(root)) if e['event']=='carryover:attachment']
    require(type(bindings) is list and len(bindings)<=1 and events==bindings,'attachment-receipt-ledger')
    for binding in bindings:
        closed(binding,'schema packet_sha256 issue sequence attachment bytes status')
        attachment(binding['attachment'])
        require(binding['schema']=='fiat-carryover-attachment/v1' and binding['status']=='read-back'
                and binding['packet_sha256']==receipt['packet_sha256'] and
                binding['issue']==receipt['issue'] and binding['sequence']==receipt['sequence']
                and binding['bytes']==len(data),'attachment-receipt-binding')



def attachment_readback(value, expected, size):
    """Read the public identity and at most one validated GitHub asset redirect.

    No caller headers, cookies or credentials cross either connection. The
    response must finish inside one acceptance deadline; socket timeouts use
    its remaining budget. System DNS, trickling response headers and detached response sockets can
    outlive that budget; a late response is never accepted. This is not a
    hard bound on the time until the call returns.
    """
    attachment(value)
    require(type(size) is int and 0<=size<=25*1024*1024,'attachment-provider-byte-cap')
    deadline=time.monotonic()+30
    host='github.com';operand=value['url'].removeprefix('https://github.com')
    for hop in range(2):
        remaining=deadline-time.monotonic();require(remaining>0,'attachment-deadline')
        connection=http.client.HTTPSConnection(host,timeout=min(15,remaining))
        try:
            connection.request('GET',operand,headers={
                'Accept':'application/octet-stream','User-Agent':'Fiat-carryover/1'})
            response=connection.getresponse()
            require(time.monotonic()<deadline,'attachment-deadline')
            if response.status==302 and hop==0:
                location=response.getheader('Location')
                text(location,8192)
                target=urlsplit(location)
                require(target.scheme=='https' and target.netloc=='objects.githubusercontent.com'
                        and not target.fragment and target.path.isascii()
                        and re.fullmatch(r'/github-production-repository-file-[0-9a-f]+/[0-9]+/[A-Za-z0-9_.-]+',target.path)
                        and all(part not in ('.','..') for part in target.path.split('/')),
                        'attachment-redirect')
                host='objects.githubusercontent.com'
                operand=target.path+('?' + target.query if target.query else '')
                continue
            require(response.status==200,'attachment-readback-status')
            data=bytearray()
            while len(data)<=size:
                remaining=deadline-time.monotonic();require(remaining>0,'attachment-deadline')
                if connection.sock is not None: connection.sock.settimeout(min(15,remaining))
                chunk=response.read1(min(65536,size+1-len(data)))
                require(time.monotonic()<deadline,'attachment-deadline')
                if not chunk: break
                data.extend(chunk)
            require(len(data)==size and digest(data)==expected,'attachment-readback-digest')
            return
        except (OSError,http.client.HTTPException):
            raise Refusal('attachment-transport') from None
        finally:
            connection.close()
    raise Refusal('attachment-redirect-limit')


def bind_attachment(controller, root, request):
    closed(request,'packet_sha256 attachment')
    controller.verify_run(str(root));state=controller.load_state(str(root))
    require(controller._next_directive(state).get('do')=='audit-verdict','not-exhausted')
    exports=state['receipts'].get('carryover_exports')
    require(type(exports) is list and len(exports)==1,'export-required')
    require(not state['receipts'].get('carryover_attachments'),'already-bound')
    before_state=read_regular(controller.state_path(str(root)))
    exported=exports[0]
    require(sha(request['packet_sha256'])==exported['packet_sha256'],'attachment-packet')
    value=attachment(request['attachment'])
    require(value['url'].rsplit('/',1)[1]==filename(exported['issue'],exported['sequence']), 'attachment-name')
    data=read_regular(exported['packet']); require(digest(data)==exported['packet_sha256'],'packet-digest')
    attachment_readback(value,exported['packet_sha256'],len(data))
    receipt={'schema':'fiat-carryover-attachment/v1','packet_sha256':exported['packet_sha256'],
             'issue':exported['issue'],'sequence':exported['sequence'],'attachment':value,
             'bytes':len(data),'status':'read-back'}
    require(read_regular(controller.state_path(str(root)))==before_state and
            read_regular(exported['packet'])==data,'attachment-source-drift')
    state['receipts']['carryover_attachments']=[receipt]
    controller.commit(str(root),state,'carryover:attachment',receipt)
    return receipt
