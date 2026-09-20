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
from fixture_tools import native_signing_tools

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
        tool_paths = self.enterContext(native_signing_tools())
        self.to_audit(task_issue=ISSUE)
        self.run_ctl('record','security_suite','"waived: fixture"')
        for _ in range(7):self.run_ctl('audit-round','--findings','1',*LINTS_CLEAN)
        args=('audit-round','--findings','1','--fixes-commit','pending',
              '--elenchus-verdict','unguarded',*LINTS_CLEAN)
        self.append_valid_audit_record(args,self.state())
        keyhome=Path(self.dir).resolve()/'fixture-gnupg';keyhome.mkdir(mode=0o700)
        environment={**os.environ,'GNUPGHOME':str(keyhome)}
        subprocess.run([tool_paths['gpg'],'--batch','--pinentry-mode','loopback','--passphrase','',
                        '--quick-generate-key','Carryover Fixture <fixture@example.invalid>',
                        'ed25519','sign','0'],env=environment,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        self.addCleanup(subprocess.run,[tool_paths['gpgconf'],'--homedir',str(keyhome),'--kill','gpg-agent'],
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
        command=[sys.executable,str(SOURCE.with_name('hexctl.py')),'--dir',self.target]
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
        command2=[sys.executable,str(SOURCE.with_name('hexctl.py')),'--dir',second.target]
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


class InoculationBodyTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('inoculation_under_test', SOURCE.with_name('inoculation.py'))
        self.adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.adapter)
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def request(self, body='self.assertEqual(double(4), 8)', candidate='def double(value):\n    return value * 2\n'):
        import ast
        (self.root/'calc.py').write_text(candidate)
        source='import unittest\nfrom calc import double\nclass Guards(unittest.TestCase):\n    def test_double(self):\n        '+body+'\n'
        (self.root/'guards.py').write_text(source)
        method=ast.parse(source).body[-1].body[0]
        return {'schema':'fiat-inoculation-request/v1',
                'dependencies':[{'path':'calc.py','sha256':carryover.digest(candidate.encode())}],
                'guards':[{'id':'double-guard','family':'arithmetic','class':'Guards','method':'test_double',
                           'source':{'path':'guards.py','sha256':carryover.digest(source.encode())},
                           'body_sha256':carryover.digest(ast.get_source_segment(source,method).encode())}]}

    def test_same_preserved_behavior_guard_fails_broken_computation(self):
        request=self.request(); result=self.adapter.execute(self.root,request)
        self.assertTrue(result['passed']); self.assertEqual(result['rows'][0]['assertions'],1)
        original_guard=request['guards'][0]
        broken=self.request(candidate='def double(value):\n    return value + 2\n')
        self.assertEqual(broken['guards'][0],original_guard)
        result=self.adapter.execute(self.root,broken)
        self.assertFalse(result['passed']); self.assertEqual(result['rows'][0]['failure_type'],'AssertionError')

    def test_untaken_assertion_and_discovery_do_not_count_as_pass(self):
        request=self.request(body='if False:\n            self.assertEqual(double(4), 8)')
        self.adapter.prepare(self.root,request)
        result=self.adapter.execute(self.root,request)
        self.assertFalse(result['passed']);self.assertEqual(result['rows'][0]['assertions'],0)

    def test_lifecycle_decorators_dispatch_and_observer_mutation_refuse(self):
        sources=[
            '    @unittest.skip("skip")\n',
            '    def setUp(self):\n        pass\n',
            '    def run(self):\n        pass\n',
            '    def __call__(self):\n        pass\n']
        for prefix in sources:
            with self.subTest(prefix=prefix):
                request=self.request(); source=(self.root/'guards.py').read_text()
                source=source.replace('    def test_double',prefix+'    def test_double')
                (self.root/'guards.py').write_text(source)
                request['guards'][0]['source']['sha256']=carryover.digest(source.encode())
                with self.assertRaises(self.adapter.Refusal):self.adapter.prepare(self.root,request)
        for body in ['self.count = 10', 'self.assertEqual = double', 'globals()', 'self.assertTrue(self)',
                     'self.assertTrue(double.__globals__)', 'self.assertTrue(getattr(double, "x"))']:
            with self.subTest(body=body), self.assertRaises(self.adapter.Refusal):
                self.adapter.prepare(self.root,self.request(body=body))

    def test_unsafe_dependency_defaults_and_import_substitution_refuse(self):
        request=self.request(candidate='def double(value=print("effect")):\n    return value * 2\n')
        with self.assertRaises(self.adapter.Refusal):self.adapter.prepare(self.root,request)

    def test_unimported_and_other_module_functions_cannot_supply_lexical_names(self):
        request=self.request();source=(self.root/'guards.py').read_text().replace('from calc import double\n','')
        (self.root/'guards.py').write_text(source);request['guards'][0]['source']['sha256']=carryover.digest(source.encode())
        with self.assertRaises(self.adapter.Refusal):self.adapter.prepare(self.root,request)
        request=self.request(candidate='def double(value):\n    return hidden(value)\n')
        other='def hidden(value):\n    return value * 2\n';(self.root/'other.py').write_text(other)
        request['dependencies'].append({'path':'other.py','sha256':carryover.digest(other.encode())})
        with self.assertRaises(self.adapter.Refusal):self.adapter.prepare(self.root,request)
        request=self.request(); source=(self.root/'guards.py').read_text().replace('from calc','from another')
        (self.root/'guards.py').write_text(source);request['guards'][0]['source']['sha256']=carryover.digest(source.encode())
        with self.assertRaises(self.adapter.Refusal):self.adapter.prepare(self.root,request)


class ReplacementMappingTests(unittest.TestCase):
    def test_existing_packet_deletion_retains_null_reconstruction_disposition(self):
        spec=importlib.util.spec_from_file_location('replacement_under_test',SOURCE.with_name('replacement.py'))
        replacement=importlib.util.module_from_spec(spec);spec.loader.exec_module(replacement)
        value={'files':[{'path':'old.py','mode':'delete','payload':carryover.blob(b'')}],'passes':[]}
        request={'schema':'fiat-replacement-request/v1','packet':{'path':'packet.md','sha256':'0'*64},
                 'proof_repository':'/unused','attachment':None,
                 'files':[{'source':'old.py','target':None,'disposition':'unchanged','result':None,'reason':'preserved deletion',
                           'base':{'source':None,'target':None}}],
                 'occurrences':[],'execution':{'schema':'fiat-inoculation-request/v1','guards':[],'dependencies':[]}}
        self.assertEqual(replacement.mappings(value,request),[])


@unittest.skipUnless(sys.platform == "darwin", "native macOS policy required")
class ReplacementRuntimeTests(unittest.TestCase):
    def test_native_guard_capture_preserves_complete_input_outside_controller_archive(self):
        helper=InoculationBodyTests();helper.setUp();self.addCleanup(helper.doCleanups)
        request=helper.request()
        spec=importlib.util.spec_from_file_location('replacement_native_test',SOURCE.with_name('replacement.py'))
        replacement=importlib.util.module_from_spec(spec);spec.loader.exec_module(replacement)
        helper.root=helper.root.resolve()
        root=helper.root/'target';root.mkdir()
        stage=root/'.hexaemeron/replacements/test/attempt';stage.mkdir(parents=True)
        storage=helper.root/'private';storage.mkdir()
        replacement.write_json(stage,'private.json',replacement.directory_identity(storage))
        candidate=storage/'candidate';candidate.mkdir()
        for name in ('calc.py','guards.py'):(candidate/name).write_bytes((helper.root/name).read_bytes())
        (candidate/'unrelated.bin').write_bytes(b'preserved complete base')
        proof=replacement.execute_guards(root,stage,{'execution':request})
        replacement.verify_execution(stage,{'execution':request},proof)
        self.assertEqual((storage/'image/candidate/unrelated.bin').read_bytes(),b'preserved complete base')
        self.assertFalse((stage/'image').exists())
        capture=json.loads((stage/'capture.json').read_bytes())
        self.assertEqual(capture['input']['owned_copy_bytes'],sum(r['bytes'] for r in proof['image_inventory'])*2)
        with mock.patch.object(replacement,'MAX_BYTES',1),self.assertRaisesRegex(replacement.Refusal,'promotion-copy-byte-cap'):
            replacement.promote(root,stage,[],[],stage,{})
        changed=copy.deepcopy(proof);changed['capture_sha256']='0'*64
        with self.assertRaisesRegex(replacement.Refusal,'replacement-capture-drift'):
            replacement.verify_execution(stage,{'execution':request},changed)


class PromotionCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.area=Path(self.temporary.name).resolve()
        spec=importlib.util.spec_from_file_location('promotion_under_test',SOURCE.with_name('replacement.py'))
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.root=self.area/'root';self.root.mkdir()
        self.stage=self.area/'stage';self.stage.mkdir()
        self.storage=self.area/'storage';self.storage.mkdir()
        self.module.write_json(self.stage,'private.json',self.module.directory_identity(self.storage))
        candidate=self.storage/'image/candidate';candidate.mkdir(parents=True)
        (candidate/'value.txt').write_text('candidate');(self.root/'value.txt').write_text('original')
        self.original=[{'path':'value.txt','mode':'100644','bytes':8,'sha256':carryover.digest(b'original')}]
        self.final=self.module.inventory_path(candidate)

    def test_reconstruction_reserves_expanded_payload_before_materialization(self):
        import hashlib
        oid=hashlib.sha1(b'blob 8\0original').hexdigest()
        inventory=[{'path':'value.txt','mode':'100644','oid':oid}]
        request={'files':[{'source':'value.txt','target':'value.txt',
                          'result':{'mode':'100644','payload':carryover.blob(b'x'*20)}}]}
        destination=self.area/'reconstructed'
        with mock.patch.object(self.module,'bind_base',return_value=inventory), \
             mock.patch.object(self.module,'MAX_BYTES',24), \
             mock.patch.object(self.module.worker,'INPUT_MAX_BYTES',24), \
             self.assertRaises((self.module.Refusal,self.module.worker.Refusal)):
            self.module.reconstruct(None,self.root,'unused',{},request,destination)
        self.assertEqual((destination/'value.txt').read_bytes(),b'original')

    def test_independent_edit_after_preimage_check_is_preserved_and_refused(self):
        exclusive=self.module.worker._exclusive
        def write(parent,name,data):
            if name.startswith('.fiat-replacement-'):(self.root/'value.txt').write_text('independent user edit')
            return exclusive(parent,name,data)
        with mock.patch.object(self.module.worker,'_exclusive',side_effect=write), \
             self.assertRaisesRegex(self.module.Refusal,'independent-edit-preserved'):
            self.module.promote(self.root,self.stage,self.original,self.final,self.stage,{})
        self.assertTrue(any(p.read_text()=='independent user edit' for p in self.storage.glob('displaced-*/value')))
        self.assertEqual((self.storage/'originals/value.txt').read_text(),'original')

    def test_independent_destination_created_after_displacement_is_never_overwritten(self):
        link=os.link
        def create(source,destination,**kwargs):
            if source.startswith('.fiat-replacement-'):(self.root/'value.txt').write_text('independent new destination')
            return link(source,destination,**kwargs)
        with mock.patch.object(self.module.os,'link',side_effect=create),self.assertRaises(FileExistsError):
            self.module.promote(self.root,self.stage,self.original,self.final,self.stage,{})
        self.assertEqual((self.root/'value.txt').read_text(),'independent new destination')
        self.assertEqual([p.read_text() for p in self.storage.glob('displaced-*/value')],['original'])


@unittest.skipUnless(sys.platform == 'darwin', 'native macOS policy required')
class ReplacementAdmissionTests(HexctlCase):
    def test_signed_archive_to_native_admission_keeps_fresh_audit_and_pending_recovery(self):
        tool_paths = self.enterContext(native_signing_tools())
        from types import SimpleNamespace
        self.observations={}
        (Path(self.dir)/'obsolete.txt').write_text('old base file')
        self.git('add','obsolete.txt');self.git('commit','-m','Original deletion preimage')
        self.to_audit(task_issue=ISSUE)
        helper=InoculationBodyTests();helper.setUp();self.addCleanup(helper.doCleanups)
        execution=helper.request()
        import ast
        guard_source=(helper.root/'guards.py').read_text()+'    def test_zero(self):\n        self.assertEqual(double(0), 0)\n'
        (helper.root/'guards.py').write_text(guard_source)
        execution['guards'][0]['source']['sha256']=carryover.digest(guard_source.encode())
        method=ast.parse(guard_source).body[-1].body[-1]
        execution['guards'].append({'id':'zero-guard','family':'zero-input','class':'Guards','method':'test_zero',
            'source':dict(execution['guards'][0]['source']),
            'body_sha256':carryover.digest(ast.get_source_segment(guard_source,method).encode())})
        for name in ('calc.py','guards.py'):
            (Path(self.target)/name).write_bytes((helper.root/name).read_bytes())
        self.git('rm','obsolete.txt')
        (Path(self.target)/'notes.txt').write_text('carried note')
        self.git('add','calc.py','guards.py','notes.txt');self.git('commit','-m','Candidate and preserved behavior guard')
        self.run_ctl('record','security_suite','"waived: fixture"')
        for _ in range(7):self.run_ctl('audit-round','--findings','1',*LINTS_CLEAN)
        args=('audit-round','--findings','1','--fixes-commit','pending','--elenchus-verdict','unguarded',*LINTS_CLEAN)
        self.append_valid_audit_record(args,self.state())
        keytemporary=tempfile.TemporaryDirectory(prefix='fiat-key-')
        self.addCleanup(keytemporary.cleanup)
        keyhome=Path(keytemporary.name);keyhome.chmod(0o700)
        env={**os.environ,'GNUPGHOME':str(keyhome)}
        key_result=subprocess.run([tool_paths['gpg'],'--batch','--pinentry-mode','loopback','--passphrase','',
                        '--quick-generate-key','Replacement Fixture <fixture@example.invalid>',
                        'ed25519','sign','0'],env=env,check=False,capture_output=True,timeout=30)
        self.assertEqual(key_result.returncode,0,key_result.stderr.decode())
        self.addCleanup(subprocess.run,[tool_paths['gpgconf'],'--homedir',str(keyhome),'--kill','gpg-agent'],
                        capture_output=True,check=False,timeout=10)
        message='Fixed candidate\n\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\nWildcat-Origin: shoggoth\n'
        subprocess.run(['git','-c','user.signingkey=fixture@example.invalid','-c','gpg.format=openpgp',
                        'commit','--allow-empty','-S','-m',message],cwd=self.target,env=env,check=True,
                       capture_output=True,timeout=30)
        fixed=self.git('rev-parse','HEAD').stdout.strip();self.git('branch','-f',self.step_branch(1),fixed)
        self.auto_audit_records=False
        self.run_ctl('audit-round','--findings','1','--fixes-commit',fixed,'--elenchus-verdict','unguarded',*LINTS_CLEAN)
        self.git('update-ref','refs/heads/proof-pass-one',fixed)
        controller=hexctl_module();spec=importlib.util.spec_from_file_location('replacement_composed',SOURCE.with_name('replacement.py'))
        self.enterContext(mock.patch.dict(sys.modules,{controller.__name__:controller}))
        replacement=importlib.util.module_from_spec(spec);spec.loader.exec_module(replacement)
        capsule=Path(self.dir).resolve()/'replacement-capsule'
        with mock.patch.dict(os.environ,env),redirect_stdout(StringIO()) as output:
            controller.cmd_checkpoint_export(SimpleNamespace(dir=self.target,out=str(capsule)))
        manifest=json.loads(output.getvalue())['manifest_sha256']
        packet_path=Path(self.dir).resolve()/'508-CARRYOVER.md'
        with mock.patch.dict(os.environ,env):
            exported=carryover.export(controller,self.target,{'archive':str(capsule),'manifest_sha256':manifest,
                'fixed_ref':'refs/heads/proof-pass-one','previous':None,'out':str(packet_path)})
        proof=Path(self.dir).resolve()/'proof.git'
        subprocess.run(['git','clone','--mirror',self.target,str(proof)],check=True,capture_output=True,timeout=30)
        fresh=HexctlCase();fresh.setUp();self.addCleanup(fresh.tearDown)
        (Path(fresh.dir)/'base-only.txt').write_text('current base retained')
        fresh.git('add','base-only.txt');fresh.git('commit','-m','Independent current base file')
        fresh.init(topic='replacement candidate',task_issue=ISSUE)
        current=Path(fresh.target).resolve()
        with mock.patch.dict(os.environ,env):value=carryover.validate(controller,proof,packet_path.read_bytes(),exported['packet_sha256'])
        request={'schema':'fiat-replacement-request/v1','packet':{'path':str(packet_path),'sha256':exported['packet_sha256']},
                 'proof_repository':str(proof),'attachment':{'identity':'99','url':'https://github.com/user-attachments/files/99/508-CARRYOVER.md'},
                 'files':[],'occurrences':[],'execution':execution}
        for row in value['files']:
            result=None if row['mode']=='delete' else {'mode':row['mode'],'payload':row['payload']}
            request['files'].append({'source':row['path'],'target':row['path'] if result else None,
                'disposition':'unchanged','result':result,'reason':'preserve exact packet change',
                'base':{'source':None,'target':None}})
        for source in value['passes']:
            for round_record in source['rounds']:
                for occurrence in round_record['occurrences']:
                    selected=execution['guards'][len(request['occurrences'])%len(execution['guards'])]
                    request['occurrences'].append({'occurrence':replacement.occurrence_key(occurrence),
                        'guard':selected['id'],'family':selected['family'],'previous_guard':occurrence['guard'],
                        'previous_family':occurrence['family'],'reason':'current declared behavior coverage; historical identities remain unknown'})
        with mock.patch.dict(os.environ,env),mock.patch.object(replacement.packet,'attachment_readback') as transport:
            pending=replacement.begin(controller,current,request)
            transport.assert_called_once_with(request['attachment'],exported['packet_sha256'],packet_path.stat().st_size)
        self.assertEqual(pending['status'],'prepared')
        self.assertEqual(fresh.next_json()['do'],'replacement-resume')
        self.assertNotEqual(fresh.run_ctl('done','study','--artifact','missing',expect=2).returncode,0)
        fresh.run_ctl('halt','--reason','inspect pending reconstruction')
        with self.assertRaisesRegex(replacement.Refusal,'replacement-run-halted'):
            replacement.resume(controller,current)
        self.assertEqual(fresh.next_json()['do'],'resume');fresh.run_ctl('resume','--note','continue preserved transaction')
        with mock.patch.dict(os.environ,env),mock.patch.dict(sys.modules,{controller.__name__:controller}), \
             mock.patch.object(controller,'replacement_backend',return_value=replacement):
            with mock.patch.object(replacement,'promote',side_effect=KeyboardInterrupt),self.assertRaises(KeyboardInterrupt):
                replacement.resume(controller,current)
            self.assertEqual(fresh.state()['receipts']['replacement_pending']['status'],'promoting')
            self.assertFalse((current/'calc.py').exists())
            with mock.patch.object(replacement,'execute_guards',side_effect=AssertionError('guard rerun after interruption')):
                admitted=replacement.resume(controller,current)
            controller.verify_run(str(current))
        self.assertEqual(admitted['status'],'admitted')
        self.assertEqual((current/'calc.py').read_bytes(),(helper.root/'calc.py').read_bytes())
        self.assertEqual((current/'base-only.txt').read_text(),'current base retained')
        self.assertTrue(admitted['fresh_independent_audit_required'])
        self.assertEqual(fresh.state()['phase'],'study');self.assertEqual(fresh.state()['steps'],[])
        self.assertEqual(fresh.state()['receipts']['carryover_parent']['packet_sha256'],exported['packet_sha256'])
        self.assertFalse(current in Path(admitted['private']['path']).parents)
        self.addCleanup(__import__('shutil').rmtree,admitted['private']['path'])
        # The second pass follows real admission; no carryover_parent fixture seed.
        fresh.env['GNUPGHOME']=str(keyhome)
        with mock.patch.object(fresh,'init'):
            fresh.to_audit(task_issue=ISSUE)
        self.assertEqual(fresh.state()['steps'][0]['audit']['rounds'],[])
        fresh.run_ctl('record','security_suite','"waived: fixture"')
        for _ in range(7):fresh.run_ctl('audit-round','--findings','1',*LINTS_CLEAN)
        fresh.append_valid_audit_record(args,fresh.state())
        fresh.git('add','calc.py','guards.py','notes.txt')
        subprocess.run(['git','-c','user.signingkey=fixture@example.invalid','-c','gpg.format=openpgp',
                        'commit','--allow-empty','-S','-m',message],cwd=current,env=env,check=True,
                       capture_output=True,timeout=30)
        second_fixed=fresh.git('rev-parse','HEAD').stdout.strip()
        fresh.git('branch','-f',fresh.step_branch(1),second_fixed);fresh.auto_audit_records=False
        fresh.run_ctl('audit-round','--findings','1','--fixes-commit',second_fixed,
                      '--elenchus-verdict','unguarded',*LINTS_CLEAN)
        fresh.git('update-ref','refs/heads/proof-pass-two',second_fixed)
        # Preparation mutates only the dedicated proof repository, outside export.
        subprocess.run(['git','-C',str(proof),'fetch',str(current),
                        'refs/heads/proof-pass-two:refs/heads/proof-pass-two'],check=True,capture_output=True,timeout=30)
        self.assertNotEqual(fresh.git('show-ref','--verify','refs/heads/proof-pass-one',expect=128).returncode,0)
        capsule2=Path(fresh.dir).resolve()/'replacement-capsule-two'
        with mock.patch.dict(os.environ,env),redirect_stdout(StringIO()) as output:
            controller.cmd_checkpoint_export(SimpleNamespace(dir=str(current),out=str(capsule2)))
        manifest2=json.loads(output.getvalue())['manifest_sha256']
        packet2=Path(fresh.dir).resolve()/'508-CARRYOVER-2.md'
        with mock.patch.dict(os.environ,env):
            exported2=carryover.export(controller,current,{'archive':str(capsule2),'manifest_sha256':manifest2,
                'fixed_ref':'refs/heads/proof-pass-two','previous':{'path':str(packet_path),'sha256':exported['packet_sha256']},
                'out':str(packet2),'proof_repository':str(proof)})
            cumulative=carryover.validate(controller,proof,packet2.read_bytes(),exported2['packet_sha256'])
            controller.verify_run(str(current))
        self.assertEqual(len(cumulative['passes']),2)
        self.assertEqual(len(exported2['occurrences']),16)
        self.assertEqual(exported2['proof_repository'],carryover.proof_identity(proof))
        self.assertEqual(fresh.next_json()['do'],'audit-verdict')
        third=HexctlCase();third.setUp();self.addCleanup(third.tearDown)
        for name,content in {'calc.py':'def double(value):\n    return value * 3\n',
                             'obsolete.txt':'independent obsolete preimage','untouched.txt':'complete new base'}.items():
            (Path(third.dir)/name).write_text(content)
        third.git('add','calc.py','obsolete.txt','untouched.txt');third.git('commit','-m','Third current base')
        third.init(topic='cumulative replacement',task_issue=ISSUE)
        thirdroot=Path(third.target).resolve()
        request3=copy.deepcopy(request);request3['packet']={'path':str(packet2),'sha256':exported2['packet_sha256']}
        request3['attachment']={'identity':'100','url':'https://github.com/user-attachments/files/100/508-CARRYOVER-2.md'}
        request3['files']=[];request3['occurrences']=[]
        base3={r['path']:r for r in replacement.base_inventory(controller,thirdroot,third.state()['base'])}
        for row in cumulative['files']:
            result=None if row['mode']=='delete' else {'mode':row['mode'],'payload':row['payload']}
            target=row['path'] if result else None
            disposition='conflicted' if row['path'] in ('calc.py','obsolete.txt') else 'unchanged'
            if row['path']=='notes.txt':target='relocated-notes.txt';disposition='transformed'
            request3['files'].append({'source':row['path'],'target':target,'result':result,
                'disposition':disposition,'reason':'explicit current-base resolution',
                'base':{'source':replacement.preimage(base3.get(row['path'])),
                        'target':replacement.preimage(base3.get(target))}})
        for source in cumulative['passes']:
            for round_record in source['rounds']:
                for occurrence in round_record['occurrences']:
                    selected=execution['guards'][len(request3['occurrences'])%len(execution['guards'])]
                    request3['occurrences'].append({'occurrence':replacement.occurrence_key(occurrence),
                        'guard':selected['id'],'family':selected['family'],'previous_guard':occurrence['guard'],
                        'previous_family':occurrence['family'],'reason':'current declared coverage; source unknowns retained'})
        def refused_request(label,candidate):
            before=controller.load_state(str(thirdroot))
            with mock.patch.dict(os.environ,env),self.assertRaises(replacement.Refusal) as refusal:
                replacement.begin(controller,thirdroot,candidate)
            self.assertEqual(controller.load_state(str(thirdroot)),before)
            self.observations[label]={'code':str(refusal.exception),'state_unchanged':True}
        missing=copy.deepcopy(request3);missing['files']=missing['files'][:-1]
        refused_request('partial-mapping-refused',missing)
        missing=copy.deepcopy(request3);missing['occurrences']=missing['occurrences'][:-1]
        refused_request('missing-occurrence-refused',missing)
        mismatch=copy.deepcopy(request3);mismatch['packet']['sha256']='0'*64
        refused_request('attachment-digest-mismatch',mismatch)
        omitted=copy.deepcopy(cumulative);omitted['files']=omitted['files'][:-1]
        omitted_path=Path(third.dir).resolve()/'omitted.md';omitted_bytes=carryover.packet_bytes(omitted)
        omitted_path.write_bytes(omitted_bytes)
        missing=copy.deepcopy(request3);missing['packet']={'path':str(omitted_path),'sha256':carryover.digest(omitted_bytes)}
        refused_request('omitted-payload-refused',missing)
        conflict=copy.deepcopy(request3)
        next(row for row in conflict['files'] if row['source']=='calc.py')['disposition']='unchanged'
        refused_request('unacknowledged-conflict-refused',conflict)
        subprocess.run(['git','-C',str(proof),'update-ref','refs/heads/proof-pass-two',second_fixed+'^'],
                       check=True,capture_output=True,timeout=10)
        refused_request('signed-fixed-tree-ref-required',request3)
        subprocess.run(['git','-C',str(proof),'update-ref','refs/heads/proof-pass-two',second_fixed],
                       check=True,capture_output=True,timeout=10)
        # The old packet is unavailable; cumulative validation receives packet2 only.
        old_packet=packet_path.with_name('old-packet-unavailable');packet_path.rename(old_packet)
        with mock.patch.dict(os.environ,env),mock.patch.object(replacement.packet,'attachment_readback'):
            third_pending=replacement.begin(controller,thirdroot,request3)
            preserved_request=Path(third_pending['directory']['path'])/'request.json'
            original_request=preserved_request.read_bytes();preserved_request.chmod(0o600)
            preserved_request.write_bytes(original_request+b' ')
            with self.assertRaisesRegex(replacement.Refusal,'replacement-request-drift') as stale:
                replacement.resume(controller,thirdroot)
            self.observations['stale-source-refused']={'code':str(stale.exception),'candidate_not_promoted':True}
            preserved_request.write_bytes(original_request);preserved_request.chmod(0o400)
            rename=os.rename;displaced=[]
            def interrupt_after_displacement(source,destination,**kwargs):
                result=rename(source,destination,**kwargs)
                if source=='calc.py' and destination=='value':
                    displaced.append(True);raise KeyboardInterrupt()
                return result
            with mock.patch.object(replacement.os,'rename',side_effect=interrupt_after_displacement),self.assertRaises(KeyboardInterrupt):
                replacement.resume(controller,thirdroot)
            self.assertEqual(displaced,[True]);self.assertFalse((thirdroot/'calc.py').exists())
            partial=controller.load_state(str(thirdroot),allow_pending_replacement=True)['receipts']['replacement_pending']
            self.assertEqual(partial['status'],'promoting')
            with self.assertRaisesRegex(replacement.Refusal,'replacement-working-drift'):
                replacement.resume(controller,thirdroot)
            stage=Path(partial['stage']['path']);storage=Path(partial['private']['path'])
            displaced_calc=next(replacement.read_json(path) for path in stage.glob('displaced-*.json')
                                if replacement.read_json(path)['path']=='calc.py')
            actual=Path(displaced_calc['directory']['path'])/'value'
            self.assertEqual(actual.read_text(),'def double(value):\n    return value * 3\n')
            # Explicit fixture-operator recovery, not automatic controller rollback.
            (thirdroot/'calc.py').write_bytes(actual.read_bytes());(thirdroot/'calc.py').chmod(0o644)
            retired=list(thirdroot.glob('.fiat-replacement-*'))
            for temporary in retired:temporary.unlink()
            self.observations['interrupted-admission-preserved']={
                'status':'promoting','mutation':'calc.py displaced before interruption',
                'resume_refused_until_operator_restoration':True,'original_sha256':carryover.digest(actual.read_bytes()),
                'operator_removed_retired_temporaries':len(retired)}
            with mock.patch.object(replacement,'execute_guards',side_effect=AssertionError('must reuse captured guard evidence')):
                third_admitted=replacement.resume(controller,thirdroot)
            controller.verify_run(str(thirdroot))
            with self.assertRaisesRegex(replacement.Refusal,'fresh-replacement-run-required') as duplicate:
                replacement.begin(controller,thirdroot,request3)
            self.observations['duplicate-sequence-refused']={'code':str(duplicate.exception),'sequence':2}
        self.addCleanup(__import__('shutil').rmtree,third_admitted['private']['path'])
        self.assertEqual(len(request3['occurrences']),16)
        self.assertEqual(third.state()['receipts']['carryover_parent']['sequence'],2)
        self.assertEqual((thirdroot/'untouched.txt').read_text(),'complete new base')
        self.assertEqual((thirdroot/'calc.py').read_bytes(),(helper.root/'calc.py').read_bytes())
        self.assertFalse((thirdroot/'obsolete.txt').exists())
        self.assertFalse((thirdroot/'notes.txt').exists())
        self.assertEqual((thirdroot/'relocated-notes.txt').read_text(),'carried note')
        self.assertFalse(packet_path.exists())
        self.observations.update({
            'two-exhausted-passes-one-packet':{'passes':len(cumulative['passes']),'occurrences':16,
                'packet_sha256':exported2['packet_sha256'],'old_packet_available':packet_path.exists()},
            'current-base-complete-reconstruction':{'untouched_sha256':carryover.digest((thirdroot/'untouched.txt').read_bytes()),
                'transformed':'notes.txt -> relocated-notes.txt','conflicts':['calc.py','obsolete.txt'],
                'admitted_capture_sha256':third_admitted['execution']['capture_sha256']},
            'no-gate-before-completion':{'attempt':'done study','exit':2,'pending_status':'prepared'},
            'executed-passes-all-families':json.loads((Path(third_admitted['stage']['path'])/'inoculation.json').read_bytes()),
            'new-independent-audit-after-guards':{'fresh_rounds_before_audit':0,'new_rounds':8,
                'reused_historical_audit':False}})


@unittest.skipUnless(sys.platform == 'darwin', 'native macOS policy required')
class ReplacementGuardAdmissionTests(unittest.TestCase):
    def test_discovery_skips_and_replaced_bodies_cannot_supply_execution_evidence(self):
        helper=InoculationBodyTests();helper.setUp();self.addCleanup(helper.doCleanups)
        helper.root=helper.root.resolve();original=helper.request()
        spec=importlib.util.spec_from_file_location('replacement_guard_refusals',SOURCE.with_name('replacement.py'))
        replacement=importlib.util.module_from_spec(spec);spec.loader.exec_module(replacement)
        self.observations={}
        for label in ('discovery-only-refused','skipped-guard-refused','replaced-guard-refused'):
            request=copy.deepcopy(original)
            area=helper.root/label;area.mkdir()
            root=area/'target';root.mkdir();stage=area/'stage';stage.mkdir()
            storage=area/'private';storage.mkdir();candidate=storage/'candidate';candidate.mkdir()
            replacement.write_json(stage,'private.json',replacement.directory_identity(storage))
            for name in ('calc.py','guards.py'):(candidate/name).write_bytes((helper.root/name).read_bytes())
            source=(candidate/'guards.py').read_text()
            if label=='discovery-only-refused':
                dependencies,guards=replacement.adapter.prepare(candidate,request)
                self.assertEqual(len(guards),1)
                discovered=[g[0]['id'] for g in guards]
                replacement.write_json(stage,'discovery.json',{'guards':discovered,'execution_observed':False})
                with self.assertRaises(FileNotFoundError):
                    replacement.verify_execution(stage,{'execution':request},{'capture_sha256':'0'*64})
                self.observations[label]={'discovered':discovered,'execution_observed':False,'refusal':'capture absent'}
                continue
            if label=='skipped-guard-refused':
                source=source.replace('    def test_double','    @unittest.skip("not executed")\n    def test_double')
            else:
                source=source.replace('self.assertEqual(double(4), 8)','self.assertTrue(True)')
            (candidate/'guards.py').write_text(source)
            request['guards'][0]['source']['sha256']=carryover.digest(source.encode())
            with self.assertRaises(replacement.adapter.Refusal) as refused:
                replacement.execute_guards(root,stage,{'execution':request})
            self.assertFalse((stage/'capture.json').exists())
            self.observations[label]={'code':str(refused.exception),'capture_created':False,
                                      'preserved_body_sha256':request['guards'][0]['body_sha256']}
