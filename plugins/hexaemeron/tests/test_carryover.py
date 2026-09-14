"""Exercise inert packet bounds, native objects and exhausted controller receipts."""

from contextlib import ExitStack, redirect_stdout
from io import StringIO
import importlib.util
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from hexctl_harness import HexctlCase, LINTS_CLEAN, hexctl_module

SOURCE = Path(__file__).resolve().parents[1]/'skills/fiat/scripts/carryover.py'
spec = importlib.util.spec_from_file_location('carryover_under_test',SOURCE)
carryover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(carryover)
ISSUE = 'https://github.com/wildcat-finance/example/issues/508'


class PacketBoundaryTests(unittest.TestCase):
    def test_duplicate_keys_and_non_json_scalars_refuse(self):
        for data in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":1.2}',b'{"a":"\\ud800"}',b'{"\\ud800":1}'):
            with self.subTest(data=data), self.assertRaises(carryover.Refusal):
                carryover.load(data)

    def test_raw_cap_precedes_json_parser(self):
        with mock.patch.object(carryover,'MAX_BYTES',8), mock.patch.object(carryover.json,'loads') as parser:
            with self.assertRaisesRegex(carryover.Refusal,'packet-byte-cap'):
                carryover.load(b' '*9)
            parser.assert_not_called()

    def test_encoded_and_decoded_budgets_refuse_before_decode(self):
        value=carryover.blob(b'abcd')
        with mock.patch.object(carryover.base64,'b64decode') as decode:
            with self.assertRaisesRegex(carryover.Refusal,'decoded-byte-cap'):
                carryover.unblob(value,[3])
            decode.assert_not_called()
        value['base64']+='AAAA'
        with self.assertRaisesRegex(carryover.Refusal,'encoded-byte-cap'):
            carryover.unblob(value,[10])

    def test_aggregate_blob_budget_counts_repeated_payload(self):
        value=carryover.blob(b'abcd')
        with self.assertRaisesRegex(carryover.Refusal,'decoded-byte-cap'):
            carryover.check_blobs([value,value],[7])

    def test_prior_payload_reserves_final_copy_before_archive_reads(self):
        prior=[{'files':[{'path':'a','mode':'100644','payload':carryover.blob(b'abcd')}]}]
        with mock.patch.object(carryover,'MAX_BYTES',10):
            remaining=carryover.remaining_pass_budget(prior)
        self.assertEqual(remaining,2)
        controller=mock.Mock()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();(root/'too-large').write_bytes(b'123')
            with self.assertRaisesRegex(carryover.Refusal,'archive-byte-cap'):
                carryover.archive(controller,str(root),'a'*64,remaining)
        controller._checkpoint_restore_capsule.assert_not_called()

    def test_paths_refuse_metadata_aliases_and_collisions(self):
        for value in ('../a','a/../b','a/.git/config','A/.HEXAEMERON/state','a\\b','/a','a//b','a/ b','a:x','caf\u00e9','e\u0301.py','\u00e9.py'):
            with self.subTest(path=value), self.assertRaises(carryover.Refusal):
                carryover.path(value)
        for values in (['a','a'],['a','A'],['a','a/b']):
            with self.assertRaises(carryover.Refusal):carryover.paths(values)

    def test_symlink_hardlink_and_fifo_are_never_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve(); p=root/'regular';p.write_bytes(b'kept')
            (root/'link').symlink_to(p);os.link(p,root/'alias');os.mkfifo(root/'fifo')
            for value in ('regular','link','alias','fifo'):
                with self.subTest(path=value), self.assertRaises((carryover.Refusal,OSError)):
                    carryover.read_regular(root/value)
            self.assertEqual(p.read_bytes(),b'kept')

    def test_archive_aliases_refuse_before_materialization(self):
        controller=hexctl_module()
        for names in (['controller/a','controller/A'],['controller/a','controller/a/b'],
                      ['controller/a','controller/a'],['controller/\u00e9','controller/e\u0301']):
            evidence={'manifest':carryover.blob(b'{}'),
                      'files':[{'path':name,'payload':carryover.blob(b'x')} for name in names]}
            with self.subTest(names=names),mock.patch.object(carryover.tempfile,'TemporaryDirectory') as temporary:
                with self.assertRaises(carryover.Refusal):
                    carryover.replay_archive(controller,evidence,[100])
                temporary.assert_not_called()

    def test_access_time_alone_does_not_change_content_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            file=Path(temporary).resolve()/'sample';file.write_bytes(b'kept')
            original=carryover.os.fstat;calls=0
            def observed(fd):
                nonlocal calls
                value=original(fd);calls+=1
                if calls==1:return value
                fields=list(value);fields[7]+=1
                return os.stat_result(fields,{'st_atime_ns':value.st_atime_ns+10**9,
                    'st_mtime_ns':value.st_mtime_ns,'st_ctime_ns':value.st_ctime_ns})
            with mock.patch.object(carryover.os,'fstat',side_effect=observed):
                self.assertEqual(carryover.read_regular(file),b'kept')

    def test_content_mutation_during_read_still_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            file=Path(temporary).resolve()/'sample';file.write_bytes(b'kept')
            original=carryover.os.read;changed=False
            def observed(fd,size):
                nonlocal changed
                result=original(fd,size)
                if not changed:
                    changed=True;file.write_bytes(b'changed')
                return result
            with mock.patch.object(carryover.os,'read',side_effect=observed):
                with self.assertRaisesRegex(carryover.Refusal,'source-changed'):
                    carryover.read_regular(file)

    def test_zero_sentinel_is_not_a_finding_and_duplicates_survive(self):
        header=b'| id | severity | file | finding | status |\n| --- | --- | --- | --- | --- |\n'
        self.assertEqual(carryover.findings(header+b'| -- | -- | -- | none | -- |\n','run',1,1),[])
        row=b'| F1 | low | a | problem | fixed |\n'
        result=carryover.findings(header+row+row,'run',1,8)
        self.assertEqual(len(result),2);self.assertEqual(result[0]['identity'],result[1]['identity'])
        self.assertNotEqual(result[0]['offset'],result[1]['offset'])

    def test_sequence_and_attachment_identity_are_checked(self):
        self.assertEqual(carryover.filename(ISSUE,1),'508-CARRYOVER.md')
        self.assertEqual(carryover.filename(ISSUE,2),'508-CARRYOVER-2.md')
        for sequence in (0,True,33):
            with self.assertRaises(carryover.Refusal):carryover.filename(ISSUE,sequence)
        with self.assertRaisesRegex(carryover.Refusal,'attachment-identity'):
            carryover.attachment({'identity':'2','url':'https://github.com/user-attachments/files/1/508-CARRYOVER.md'})

    def test_explicit_guard_and_family_columns_are_custody_not_execution(self):
        data=b'| id | status | guard | family |\\n| --- | --- | --- | --- |\\n| F1 | fixed | test_guard | parser |\\n'.replace(b'\\n',b'\n')
        row=carryover.findings(data,'source',1,8)[0]
        self.assertEqual((row['disposition'],row['guard'],row['family']),('fixed','test_guard','parser'))
        self.assertEqual(carryover.unblob(row['raw'],[100]),b'| F1 | fixed | test_guard | parser |\n')

    def test_escaped_pipe_parity_does_not_shift_declared_identities(self):
        header=b'| id | finding | guard | family |\n'
        for finding in (b'input a '+b'\\'+b'| b',b'input a '+b'\\'*3+b'| b',b'input a '+b'\\'*2):
            raw=b'| F1 | '+finding+b'| guard-one | family-one |\n'
            with self.subTest(finding=finding):
                row=carryover.findings(header+raw,'source',1,8)[0]
                self.assertEqual((row['guard'],row['family']),('guard-one','family-one'))
                self.assertEqual(carryover.unblob(row['raw'],[200]),raw)
        ambiguous=carryover.findings(header+b'| F1 | a | b | guard-one | family-one |\n','source',1,8)[0]
        self.assertIsNone(ambiguous['guard']);self.assertIsNone(ambiguous['family'])

    def test_cumulative_prefix_and_omission_checks(self):
        # Source replay is controlled here; the composed fixture below verifies
        # actual checkpoint, signed Git and controller receipt joins.
        controller=mock.Mock()
        controller.current_step.return_value={'n':1}
        first={'source_run':'one','archive_location':'/first','archive':{},
               'original_commit':'a'*40,'original_tree':'b'*40,'fixed_ref':'first',
               'fixed_commit':'c'*40,'fixed_tree':'d'*40,'rounds':[],
               'files':[{'path':'restored','mode':'delete','payload':carryover.blob(b'')}]}
        one={'schema':carryover.SCHEMA,'issue':ISSUE,'sequence':1,
             'filename':'508-CARRYOVER.md','previous_sha256':None,'passes':[first],
             'files':first['files']}
        previous=carryover.digest(carryover.packet_bytes(one))
        second={**first,'source_run':'two','archive_location':'/second','fixed_ref':'second',
                'files':[{'path':'restored','mode':'100644','payload':carryover.blob(b'base')}]}
        parent={'packet_sha256':previous,'sequence':1,'source_runs':['one']}
        states=[{'receipts':{'task_issue':ISSUE}},
                {'receipts':{'task_issue':ISSUE,'carryover_parent':parent}}]
        value={**one,'sequence':2,'filename':'508-CARRYOVER-2.md',
               'previous_sha256':previous,'passes':[first,second],'files':second['files']}
        def verify(candidate, supplied_states=states):
            data=carryover.packet_bytes(candidate)
            with mock.patch.object(carryover,'replay_archive',side_effect=[(s,b'') for s in supplied_states]), \
                 mock.patch.object(carryover,'pass_record',side_effect=[first,second]):
                return carryover.validate(controller,None,data,carryover.digest(data))
        self.assertEqual(verify(value)['files'],second['files'])
        omitted=copy.deepcopy(value);omitted['files']=[]
        with self.assertRaisesRegex(carryover.Refusal,'cumulative-payload-mismatch'):verify(omitted)
        stale=copy.deepcopy(states);stale[1]['receipts']['carryover_parent']['packet_sha256']='0'*64
        with self.assertRaisesRegex(carryover.Refusal,'lineage-prefix-digest'):verify(value,stale)
        tampered=copy.deepcopy(value);tampered['passes'][0]['rounds']=[{'invented':True}]
        with self.assertRaisesRegex(carryover.Refusal,'source-inventory-mismatch'):verify(tampered)

    def test_four_pass_prefixes_preserve_every_source_and_occurrence(self):
        controller=mock.Mock();controller.current_step.return_value={'n':1}
        passes=[];states=[];previous=None
        for number in range(1,5):
            receipts={'task_issue':ISSUE}
            if previous is not None:
                receipts['carryover_parent']={'packet_sha256':previous,'sequence':number-1,
                                             'source_runs':[p['source_run'] for p in passes]}
            states.append({'receipts':receipts})
            record={'source_run':str(number),'archive_location':'/fixture/'+str(number),
                    'archive':{},'original_commit':'a'*40,'original_tree':'b'*40,
                    'fixed_ref':'pass-'+str(number),'fixed_commit':'c'*40,'fixed_tree':'d'*40,
                    'rounds':[{'occurrences':[{'identity':[str(number),1,8,'F1']},
                                               {'identity':[str(number),1,8,'F1']}]}],
                    'files':[{'path':'a','mode':'100644','payload':carryover.blob(str(number).encode())}]}
            passes.append(record)
            value={'schema':carryover.SCHEMA,'issue':ISSUE,'sequence':number,
                   'filename':carryover.filename(ISSUE,number),'previous_sha256':previous,
                   'passes':list(passes),'files':record['files']}
            data=carryover.packet_bytes(value);previous=carryover.digest(data)
        with mock.patch.object(carryover,'replay_archive',side_effect=[(s,b'') for s in states]), \
             mock.patch.object(carryover,'pass_record',side_effect=passes):
            checked=carryover.validate(controller,None,data,previous)
        self.assertEqual(checked['filename'],'508-CARRYOVER-4.md')
        self.assertEqual(sum(len(r['occurrences']) for p in checked['passes'] for r in p['rounds']),8)
        self.assertEqual(carryover.unblob(checked['files'][0]['payload'],[1]),b'4')

    def test_legacy_missing_evidence_stays_unknown_without_invented_rows(self):
        controller=mock.Mock();entry={'round':8,'findings':2}
        step={'n':1,'audit':{'rounds':[entry]}}
        state={'base':'main','steps':[step]}
        controller.current_step.return_value=step
        controller._next_directive.return_value={'do':'audit-verdict'}
        controller.controller_run_id.return_value='legacy-run'
        controller.last_local_commit.return_value='c'*40
        evidence={'manifest':carryover.blob(carryover.canonical({'boundary':{'refs':{'main':'a'*40}}})),
                  'files':[]}
        ledger=carryover.canonical({'event':'audit-round','data':{'step':1,**entry}})+b'\n'
        with mock.patch.object(carryover,'resolve',return_value='c'*40), \
             mock.patch.object(carryover,'tree',return_value='d'*40), \
             mock.patch.object(carryover,'complete_files',return_value=[]):
            record=carryover.pass_record(controller,None,state,ledger,evidence,'/legacy','fixed')
        row=record['rounds'][0]
        self.assertEqual(row['receipt'],entry);self.assertIsNone(row['producer'])
        self.assertEqual(row['occurrences'],[])
        self.assertIn('legacy-producer-missing',row['unknown'])
        self.assertIn('elenchus_verdict',row['unknown'])

    def test_attachment_readback_checks_bytes_and_refuses_redirects(self):
        binding={'identity':'1','url':'https://github.com/user-attachments/files/1/508-CARRYOVER.md'}
        for status,data,valid in ((200,b'bytes',True),(200,b'other',False),(302,b'bytes',False)):
            connection=mock.Mock();response=connection.getresponse.return_value
            response.status=status;response.read.return_value=data;response.read1.side_effect=[data,b'']
            with mock.patch.object(carryover.http.client,'HTTPSConnection',return_value=connection):
                if valid:carryover.attachment_readback(binding,carryover.digest(b'bytes'),5)
                else:
                    with self.assertRaises(carryover.Refusal):
                        carryover.attachment_readback(binding,carryover.digest(b'bytes'),5)
            connection.close.assert_called_once()

    def test_github_asset_redirect_preserves_exact_public_packet_identity(self):
        binding={'identity':'1','url':'https://github.com/user-attachments/files/1/508-CARRYOVER.md'}
        first=mock.Mock();second=mock.Mock()
        first.getresponse.return_value.status=302
        first.getresponse.return_value.getheader.return_value=(
            'https://objects.githubusercontent.com/github-production-repository-file-5c1aeb/1/asset?fixture=1')
        second.getresponse.return_value.status=200
        second.getresponse.return_value.read.return_value=b'bytes'
        second.getresponse.return_value.read1.side_effect=[b'bytes',b'']
        accepted=False
        with mock.patch.object(carryover.http.client,'HTTPSConnection',side_effect=[first,second]):
            try:
                carryover.attachment_readback(binding,carryover.digest(b'bytes'),5)
                accepted=True
            except carryover.Refusal:
                pass
        self.assertTrue(accepted,'the supported GitHub asset redirect must reach exact digest readback')

    def test_redirects_refuse_other_hosts_credentials_ports_and_extra_hops(self):
        binding={'identity':'1','url':'https://github.com/user-attachments/files/1/508-CARRYOVER.md'}
        for location in ('http://objects.githubusercontent.com/a',
                         'https://evil.invalid/a','https://127.0.0.1/a',
                         'https://user@objects.githubusercontent.com/a',
                         'https://objects.githubusercontent.com:444/a',
                         'https://objects.githubusercontent.com/a#fragment'):
            connection=mock.Mock();connection.getresponse.return_value.status=302
            connection.getresponse.return_value.getheader.return_value=location
            with mock.patch.object(carryover.http.client,'HTTPSConnection',return_value=connection) as connect:
                with self.assertRaises(carryover.Refusal):
                    carryover.attachment_readback(binding,carryover.digest(b'bytes'),5)
                self.assertEqual(connect.call_count,1)
        first=mock.Mock();second=mock.Mock()
        first.getresponse.return_value.status=302
        first.getresponse.return_value.getheader.return_value='https://objects.githubusercontent.com/github-production-repository-file-5c1aeb/1/asset'
        second.getresponse.return_value.status=302
        with mock.patch.object(carryover.http.client,'HTTPSConnection',side_effect=[first,second]) as connect:
            with self.assertRaises(carryover.Refusal):
                carryover.attachment_readback(binding,carryover.digest(b'bytes'),5)
            self.assertEqual(connect.call_count,2)
            self.assertEqual(first.request.call_args.kwargs['headers'],second.request.call_args.kwargs['headers'])
            self.assertNotIn('Authorization',second.request.call_args.kwargs['headers'])
            self.assertNotIn('Cookie',second.request.call_args.kwargs['headers'])

    def test_deadline_is_shared_across_redirect_hops(self):
        connection=mock.Mock();connection.getresponse.return_value.status=302
        with mock.patch.object(carryover.time,'monotonic',side_effect=[0,0,31]),mock.patch.object(carryover.http.client,'HTTPSConnection',return_value=connection):
            with self.assertRaisesRegex(carryover.Refusal,'attachment-deadline'):
                carryover.attachment_readback({'identity':'1','url':'https://github.com/user-attachments/files/1/508-CARRYOVER.md'},'a'*64,5)

    def test_attachment_transport_limit_is_distinct(self):
        binding={'identity':'1','url':'https://github.com/user-attachments/files/1/508-CARRYOVER.md'}
        with mock.patch.object(carryover.http.client,'HTTPSConnection') as connection:
            with self.assertRaisesRegex(carryover.Refusal,'provider-byte-cap'):
                carryover.attachment_readback(binding,'a'*64,25*1024*1024+1)
            connection.assert_not_called()

    def test_publish_never_overwrites_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary).resolve()/'508-CARRYOVER.md';p.write_bytes(b'original')
            with self.assertRaises(FileExistsError):carryover.publish(str(p),b'new')
            self.assertEqual(p.read_bytes(),b'original')

    def test_occupied_output_recovers_to_new_destination_without_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();occupied=root/'508-CARRYOVER.md'
            occupied.write_bytes(b'independent')
            with self.assertRaises(FileExistsError):carryover.publish(str(occupied),b'packet')
            fresh=root/'fresh';fresh.mkdir();destination=fresh/'508-CARRYOVER.md'
            carryover.publish(str(destination),b'packet')
            self.assertEqual(carryover.read_regular(destination),b'packet')
            self.assertEqual(occupied.read_bytes(),b'independent')


class NativePayloadTests(unittest.TestCase):
    def setUp(self):
        self.home=tempfile.TemporaryDirectory();self.addCleanup(self.home.cleanup)
        self.root=Path(self.home.name).resolve();self.controller=hexctl_module()
        self.git('init','-q');self.git('config','user.name','Fixture');self.git('config','user.email','fixture@example.invalid')
        self.git('config','commit.gpgsign','false')

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,stderr=subprocess.PIPE)

    def commit(self):
        self.git('add','-A');self.git('commit','-qm','fixture');return self.git('rev-parse','HEAD').decode().strip()

    def test_complete_diff_preserves_bytes_deletions_and_modes(self):
        (self.root/'old').write_bytes(b'old');(self.root/'run').write_bytes(b'old');base=self.commit()
        (self.root/'old').unlink();(self.root/'run').write_bytes(b'new\x00bytes');(self.root/'run').chmod(0o755);fixed=self.commit()
        files=carryover.git_files(self.controller,self.root,base,fixed)
        self.assertEqual([(x['path'],x['mode']) for x in files],[('old','delete'),('run','100755')])
        self.assertEqual(carryover.unblob(files[1]['payload'],[100]),b'new\x00bytes')

    def test_restoration_equal_to_new_base_replaces_prior_deletion(self):
        (self.root/'restored').write_bytes(b'current base');base=self.commit()
        (self.root/'other').write_bytes(b'new');fixed=self.commit()
        files=carryover.complete_files(self.controller,self.root,base,fixed,['restored'])
        restored=next(f for f in files if f['path']=='restored')
        self.assertEqual(carryover.unblob(restored['payload'],[100]),b'current base')
        result=carryover.cumulative([{'files':[{'path':'restored','mode':'delete','payload':carryover.blob(b'')}]},{'files':files}])
        self.assertEqual(next(f for f in result if f['path']=='restored')['mode'],'100644')

    def test_symlink_modes_refuse(self):
        (self.root/'a').write_bytes(b'a');base=self.commit();(self.root/'link').symlink_to('a');fixed=self.commit()
        with self.assertRaisesRegex(carryover.Refusal,'special-git-mode'):
            carryover.git_files(self.controller,self.root,base,fixed)

    def test_size_is_checked_before_blob_read(self):
        (self.root/'a').write_bytes(b'a');base=self.commit();(self.root/'a').write_bytes(b'large');fixed=self.commit()
        original=carryover.native;calls=[]
        def observe(controller,root,args):
            calls.append(args);return original(controller,root,args)
        with mock.patch.object(carryover,'MAX_BYTES',2),mock.patch.object(carryover,'native',side_effect=observe):
            with self.assertRaisesRegex(carryover.Refusal,'git-blob-byte-cap'):
                carryover.git_files(self.controller,self.root,base,fixed)
        self.assertFalse(any(a[:2]==['cat-file','blob'] for a in calls))

    def test_unsigned_fixed_commit_refuses_native_verifier(self):
        (self.root/'a').write_bytes(b'a');fixed=self.commit()
        with self.assertRaises(SystemExit):
            self.controller.verify_local_commit(str(self.root),fixed,'fixture',native_relation=True)

    def test_moved_native_ref_cannot_inherit_archived_commit(self):
        (self.root/'a').write_bytes(b'first');first=self.commit()
        self.git('branch','fixed',first)
        (self.root/'a').write_bytes(b'second');second=self.commit()
        self.git('update-ref','refs/heads/fixed',second)
        state={'base':'main','steps':[{'n':1}]}
        evidence={'manifest':carryover.blob(carryover.canonical({'boundary':{'refs':{'main':first}}})),
                  'files':[]}
        with mock.patch.object(self.controller,'current_step',return_value=state['steps'][0]), \
             mock.patch.object(self.controller,'_next_directive',return_value={'do':'audit-verdict'}), \
             mock.patch.object(self.controller,'last_local_commit',return_value=first), \
             mock.patch.object(self.controller,'verify_local_commit') as verifier:
            with self.assertRaisesRegex(carryover.Refusal,'fixed-receipt-mismatch'):
                carryover.pass_record(self.controller,self.root,state,b'',evidence,'/fixture','fixed')
            verifier.assert_not_called()
        self.assertEqual((self.root/'a').read_bytes(),b'second')


class ExhaustedReceiptTests(HexctlCase):
    def test_round_eight_export_records_without_closing_or_changing_base(self):
        self.to_audit(task_issue=ISSUE)
        self.run_ctl('record','security_suite','"waived: fixture"')
        for _ in range(8):self.run_ctl('audit-round','--findings','1',*LINTS_CLEAN)
        self.assertEqual(self.next_json()['do'],'audit-verdict')
        before=self.state();controller=hexctl_module();capsule=Path(self.dir).resolve()/'capsule'
        output=self.run_ctl('checkpoint','export','--out',str(capsule))
        checkpoint=json.loads(output.stdout);fixed=controller.last_local_commit(controller.current_step(before))
        request={'archive':str(capsule),'manifest_sha256':checkpoint['manifest_sha256'],
                 'fixed_ref':'refs/heads/fixed','previous':None,'out':str(Path(self.dir).resolve()/'508-CARRYOVER.md')}
        def native_source(ctl,root,args):
            if args[0]=='show':return (Path(self.target)/args[1].split(':',1)[1]).read_bytes()
            if args[:2]==['cat-file','-s']:
                return str((Path(self.target)/args[2].split(':',1)[1]).stat().st_size).encode()
            raise AssertionError(args)
        # This fixture exercises real controller/archive/receipt state. Native Git
        # extraction and signature refusal have separate actual-repository tests.
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(carryover,'resolve',return_value=fixed))
            stack.enter_context(mock.patch.object(carryover,'tree',return_value='b'*40))
            stack.enter_context(mock.patch.object(carryover,'git_files',return_value=[]))
            stack.enter_context(mock.patch.object(carryover,'native',side_effect=native_source))
            stack.enter_context(mock.patch.object(controller,'verify_local_commit',return_value=fixed))
            receipt=carryover.export(controller,self.target,request)
            stack.enter_context(mock.patch.object(controller,'carryover_backend',return_value=carryover))
            stack.enter_context(mock.patch.dict(sys.modules,{controller.__name__:controller}))
            controller.verify_run(self.target)
        after=self.state();self.assertEqual(after['base'],before['base'])
        self.assertEqual(after['steps'],before['steps']);self.assertEqual(self.next_json()['do'],'audit-verdict')
        self.assertEqual(len(receipt['occurrences']),8)
        self.assertEqual(receipt['attachment_status'],'unbound')
        self.assertEqual(receipt['replacement_admission'],'unavailable')

    def test_composed_signed_tree_capsule_export_and_receipt_replay(self):
        self.to_audit(task_issue=ISSUE)
        self.run_ctl('record','security_suite','"waived: fixture"')
        for _ in range(7):self.run_ctl('audit-round','--findings','1',*LINTS_CLEAN)
        args=('audit-round','--findings','1','--fixes-commit','pending',
              '--elenchus-verdict','unguarded',*LINTS_CLEAN)
        self.append_valid_audit_record(args,self.state())
        keyhome=Path(self.dir).resolve()/'fixture-gnupg';keyhome.mkdir(mode=0o700)
        environment={**os.environ,'GNUPGHOME':str(keyhome)}
        subprocess.run(['gpg','--batch','--pinentry-mode','loopback','--passphrase','',
                        '--quick-generate-key','Carryover Fixture <fixture@example.invalid>',
                        'ed25519','sign','0'],env=environment,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        self.addCleanup(subprocess.run,['gpgconf','--homedir',str(keyhome),'--kill','gpg-agent'],
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=10)
        message='Fixture fixed tree\n\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\nWildcat-Origin: shoggoth\n'
        subprocess.run(['git','-c','user.signingkey=fixture@example.invalid',
                        '-c','gpg.format=openpgp','commit','--allow-empty','-S','-m',message],
                       cwd=self.target,env=environment,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        fixed=self.git('rev-parse','HEAD').stdout.strip()
        self.git('branch','-f',self.step_branch(1),fixed)
        self.auto_audit_records=False
        self.run_ctl('audit-round','--findings','1','--fixes-commit',fixed,
                     '--elenchus-verdict','unguarded',*LINTS_CLEAN)
        before=self.state();controller=hexctl_module();capsule=Path(self.dir).resolve()/'native-capsule'
        from types import SimpleNamespace
        with mock.patch.dict(os.environ,environment),redirect_stdout(StringIO()) as stream:
            controller.cmd_checkpoint_export(SimpleNamespace(dir=self.target,out=str(capsule)))
        exported=json.loads(stream.getvalue())
        request={'archive':str(capsule),'manifest_sha256':exported['manifest_sha256'],
                 'fixed_ref':'refs/heads/carried-pass-one','previous':None,
                 'out':str(Path(self.dir).resolve()/'508-CARRYOVER.md')}
        self.git('update-ref','refs/heads/carried-pass-one',fixed)
        request_path=Path(self.dir).resolve()/'export-request.json';request_path.write_text(json.dumps(request))
        command=['python3',str(SOURCE.with_name('hexctl.py')),'--dir',self.target]
        result=subprocess.run([*command,'carryover-export','--request',str(request_path)],
                              env=environment,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        receipt=json.loads(result.stdout);self.assertEqual(receipt['fixed_commit'],fixed)
        self.assertEqual(len(receipt['occurrences']),8)
        checked=subprocess.run([*command,'carryover-validate','--packet',request['out'],
                                '--sha256',receipt['packet_sha256']],env=environment,
                               capture_output=True,text=True,timeout=60)
        self.assertEqual(checked.returncode,0,checked.stderr)
        replay=subprocess.run([*command,'verify'],env=environment,capture_output=True,text=True,timeout=30)
        self.assertEqual(replay.returncode,0,replay.stderr)
        self.assertEqual(self.state()['steps'],before['steps']);self.assertEqual(self.state()['base'],before['base'])
        self.assertEqual(self.git('rev-parse','HEAD').stdout.strip(),fixed)
        self.assertEqual(self.next_json()['do'],'audit-verdict')
        with mock.patch.dict(os.environ,environment), \
             mock.patch.dict(sys.modules,{controller.__name__:controller}), \
             mock.patch.object(controller,'carryover_backend',return_value=carryover), \
             mock.patch.object(carryover,'attachment_readback') as transport:
            bound=carryover.bind_attachment(controller,self.target,{
                'packet_sha256':receipt['packet_sha256'],
                'attachment':{'identity':'99','url':'https://github.com/user-attachments/files/99/508-CARRYOVER.md'}})
            transport.assert_called_once_with(bound['attachment'],receipt['packet_sha256'],Path(request['out']).stat().st_size)
        replay=subprocess.run([*command,'verify'],env=environment,capture_output=True,text=True,timeout=30)
        self.assertEqual(replay.returncode,0,replay.stderr)
        second=HexctlCase();second.setUp();self.addCleanup(second.tearDown)
        second.to_audit(task_issue=ISSUE)
        # Step 5 will own admission. This disposable fixture seeds only its
        # future parent receipt, through the controller's real ledger writer.
        later=second.state()
        later['receipts']['carryover_parent']={'packet_sha256':receipt['packet_sha256'],
            'sequence':1,'source_runs':receipt['source_runs']}
        controller.commit(second.target,later,'fixture:carryover-parent',later['receipts']['carryover_parent'])
        second.run_ctl('record','security_suite','"waived: fixture"')
        for _ in range(7):second.run_ctl('audit-round','--findings','1',*LINTS_CLEAN)
        second.append_valid_audit_record(args,second.state())
        subprocess.run(['git','-c','user.signingkey=fixture@example.invalid',
                        '-c','gpg.format=openpgp','commit','--allow-empty','-S','-m',message],
                       cwd=second.target,env=environment,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        second_fixed=second.git('rev-parse','HEAD').stdout.strip()
        second.git('branch','-f',second.step_branch(1),second_fixed)
        second.auto_audit_records=False
        second.run_ctl('audit-round','--findings','1','--fixes-commit',second_fixed,
                       '--elenchus-verdict','unguarded',*LINTS_CLEAN)
        second.git('fetch',self.target,'refs/heads/carried-pass-one:refs/heads/carried-pass-one')
        capsule2=Path(second.dir).resolve()/'second-capsule'
        with mock.patch.dict(os.environ,environment),redirect_stdout(StringIO()) as stream:
            controller.cmd_checkpoint_export(SimpleNamespace(dir=second.target,out=str(capsule2)))
        checkpoint2=json.loads(stream.getvalue())
        request2={'archive':str(capsule2),'manifest_sha256':checkpoint2['manifest_sha256'],
                  'fixed_ref':second.step_branch(1),
                  'previous':{'path':request['out'],'sha256':receipt['packet_sha256']},
                  'out':str(Path(second.dir).resolve()/'508-CARRYOVER-2.md')}
        request_path2=Path(second.dir).resolve()/'request.json';request_path2.write_text(json.dumps(request2))
        command2=['python3',str(SOURCE.with_name('hexctl.py')),'--dir',second.target]
        exported2=subprocess.run([*command2,'carryover-export','--request',str(request_path2)],
                                 env=environment,capture_output=True,text=True,timeout=60)
        self.assertEqual(exported2.returncode,0,exported2.stderr)
        receipt2=json.loads(exported2.stdout)
        self.assertEqual(receipt2['sequence'],2);self.assertEqual(len(receipt2['occurrences']),16)
        self.assertEqual(len(set(receipt2['source_runs'])),2)
        checked2=subprocess.run([*command2,'carryover-validate','--packet',request2['out'],
                                 '--sha256',receipt2['packet_sha256']],env=environment,
                                capture_output=True,text=True,timeout=60)
        self.assertEqual(checked2.returncode,0,checked2.stderr)
        self.assertEqual(second.next_json()['do'],'audit-verdict')
        self.git('update-ref','refs/heads/carried-pass-one',fixed+'^')
        refused=subprocess.run([*command,'verify'],env=environment,capture_output=True,text=True,timeout=30)
        self.assertNotEqual(refused.returncode,0)
