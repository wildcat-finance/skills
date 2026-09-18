"""Require complete, source-bound execution before a conformance pass."""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'plugins/hexaemeron/skills/fiat/scripts'))
from checkpoint_authority import conformance as subject


class ImplementedConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/'repo';self.root.mkdir()
        for relative in (*subject.SOURCE_PATHS,*subject.TOOLCHAIN_PATHS,*subject.CORPUS_FILES,subject.MANIFEST_PATH):
            path=self.root/relative;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,path)

    def invoke(self,criterion='records-and-signatures'):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            status=subject.main(['--candidate','ordered-replay','--criterion',criterion,'--report',f'.hexaemeron/reports/ordered-replay-{criterion}.json'],root=self.root)
        return status,json.loads(output.getvalue())

    def test_actual_execution_is_complete_and_bound(self):
        status,event=self.invoke()
        self.assertEqual(status,0)
        self.assertTrue(event['complete'])
        self.assertEqual(event['execution']['tests_run'],len(event['executed_cases']))
        self.assertGreater(event['execution']['subtests_run'],1000)
        self.assertEqual(event['execution']['skips'],0)
        self.assertEqual({row['name'] for row in event['execution']['tools']},{'openssl','ssh-keygen','gpg','cosign'})
        self.assertEqual(event['fixture_manifest'],subject._inputs(self.root)['fixture_manifest'])

    def test_later_criteria_still_refuse_without_execution(self):
        with mock.patch.object(subject,'_execute',side_effect=AssertionError('later gate executed')):
            for criterion in subject.CRITERIA[3:]:
                status,event=self.invoke(criterion)
                self.assertEqual(status,3);self.assertFalse(event['complete'])
                self.assertEqual(event['executed_cases'],[])

    def test_missing_inventory_or_changed_fixture_refuses_before_execution(self):
        path=self.root/subject.MANIFEST_PATH
        original=path.read_bytes();manifest=json.loads(original)
        manifest['files'].pop();path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(subject.Refusal,'unsupported-manifest'):subject._inputs(self.root)
        path.write_bytes(original)
        specimen=self.root/subject.CORPUS_FILES[0];specimen.write_bytes(specimen.read_bytes()+b' ')
        with self.assertRaisesRegex(subject.Refusal,'fixture-drift'):subject._inputs(self.root)

    def test_incomplete_skipped_empty_or_inconsistent_execution_never_passes(self):
        cases=subject._inputs(self.root)['cases']
        base={'complete':True,'passed':True,'started':cases,'completed':cases,'tests_run':len(cases),
              'failures':0,'errors':0,'skips':0,'expected_failures':0,'unexpected_successes':0}
        changes=({'skips':1},{'failures':1},{'errors':1},{'expected_failures':1},
                 {'unexpected_successes':1},{'complete':False},{'completed':cases[:-1]},
                 {'started':[],'completed':[],'tests_run':0},{'tests_run':True})
        for change in changes:
            report=base|change
            with mock.patch.object(subject,'_execute',return_value=(report,0,'a'*64,'b'*64)):
                status,event=self.invoke()
            self.assertEqual(status,1);self.assertFalse(event['complete'])
            # Remove only this test's exclusive temporary output pair for the next case.
            for path in (self.root/'.hexaemeron/reports').iterdir():path.unlink()

    def test_execution_report_has_a_closed_shape_and_exact_toolchain(self):
        raw=json.loads((ROOT/subject.CORPUS_ROOT/'tool-profile.json').read_bytes())
        good={'schema':'checkpoint-authority-record-execution/v1','complete':True,'passed':True,
              'started':[],'completed':[],'tests_run':0,'subtests_run':0,'failures':0,'errors':0,
              'skips':0,'expected_failures':0,'unexpected_successes':0,'output_bytes':0,
              'failure_cases':[],'error_cases':[],
              'output_sha256':'a'*64,'python':(ROOT/'.python-version').read_text().strip(),
              'tools':[{'name':name,'sha256':'b'*64} for name in ('openssl','ssh-keygen','gpg','cosign')],
              'schema_tools':raw['schema_tools']}
        subject._validate_execution(good,self.root)
        for change in ({'extra':1},{'tests_run':True},{'skips':-1},{'started':[{}]},
                       {'failure_cases':[{}]},{'failures':1},{'errors':1},
                       {'tools':[]},{'python':'3.13.0'},{'schema_tools':{}},{'output_sha256':[]}):
            with self.assertRaises(subject.Refusal):subject._validate_execution(good|change,self.root)

    def test_runner_retains_parent_case_ids_for_subtest_failures_and_errors(self):
        from plugins.hexaemeron.tests.checkpoint_authority_record_suite import Result
        class Observed(unittest.TestCase):
            def runTest(self):
                with self.subTest(vector='assertion'):self.fail('observed assertion')
                with self.subTest(vector='exception'):raise ValueError('observed exception')
        case=Observed()
        result=unittest.TextTestRunner(stream=io.StringIO(),resultclass=Result).run(case)
        self.assertEqual(result.failure_cases,{case.id()})
        self.assertEqual(result.error_cases,{case.id()})
        self.assertEqual(len(result.failures),1)
        self.assertEqual(len(result.errors),1)
        self.assertEqual(result.started,result.completed)
        self.assertEqual(result.subtests,2)

    def test_source_change_during_execution_refuses_a_pass(self):
        cases=subject._inputs(self.root)['cases']
        def changed(root):
            path=root/subject.SOURCE_PATHS[0];path.write_bytes(path.read_bytes()+b'\n')
            return {'complete':True,'passed':True,'started':cases,'completed':cases,'tests_run':len(cases),
                    'failures':0,'errors':0,'skips':0,'expected_failures':0,'unexpected_successes':0},0,'a'*64,'b'*64
        with mock.patch.object(subject,'_execute',side_effect=changed):status,event=self.invoke()
        self.assertEqual(status,2);self.assertEqual(event['code'],'source-changed')

    def test_execution_reaps_descendants_after_reporter_parent_exits(self):
        from plugins.hexaemeron.tests.test_checkpoint_authority_records import (
            DESCENDANT_PROBE, assert_descendant_stopped, cleanup_descendant,
        )
        runner = self.root / 'plugins/hexaemeron/tests/checkpoint_authority_record_suite.py'
        runner.write_text(DESCENDANT_PROBE)
        try:
            with mock.patch.object(subject, '_validate_execution'):
                result, exit_code, _, _ = subject._execute(self.root)
            self.assertEqual((result, exit_code), ({}, 0))
            assert_descendant_stopped(self, self.root)
        finally:
            cleanup_descendant(self.root)


if __name__=='__main__':unittest.main()
