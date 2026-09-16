#!/usr/bin/env python3
"""Emit complete unittest execution for the records-and-signatures criterion."""
from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_checkpoint_authority_records as cases


class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.started=[];self.completed=[];self.subtests=0
        self.failure_cases=set();self.error_cases=set()
    def startTest(self,test):
        self.started.append(test.id());super().startTest(test)
    def stopTest(self,test):
        self.completed.append(test.id());super().stopTest(test)
    def addSubTest(self,test,subtest,error):
        if error is not None:
            target=self.failure_cases if issubclass(error[0],test.failureException) else self.error_cases
            target.add(test.id())
        self.subtests+=1;super().addSubTest(test,subtest,error)
    def addFailure(self,test,error):
        self.failure_cases.add(test.id());super().addFailure(test,error)
    def addError(self,test,error):
        self.error_cases.add(test.id());super().addError(test,error)


def main():
    suite=unittest.defaultTestLoader.loadTestsFromModule(cases)
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,resultclass=Result,verbosity=2).run(suite)
    complete=(len(result.started)==len(result.completed)==len(set(result.started))==result.testsRun and result.testsRun>0)
    passed=complete and result.wasSuccessful() and not (result.skipped or result.expectedFailures or result.unexpectedSuccesses)
    profile=json.loads((cases.FIXTURES.parent/'tool-profile.json').read_bytes())
    tool_rows=[]
    for name in ('openssl','ssh-keygen','gpg','cosign'):
        try:
            pin=cases.tool(name);pin.check()
            tool_rows.append({'name':name,'sha256':pin.sha256})
        except Exception:
            passed=False
    output=stream.getvalue().encode()
    report={'schema':'checkpoint-authority-record-execution/v1','complete':complete,
        'passed':bool(passed),'tests_run':result.testsRun,'subtests_run':result.subtests,
        'started':result.started,'completed':result.completed,
        'failure_cases':sorted(result.failure_cases),'error_cases':sorted(result.error_cases),
        'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
        'expected_failures':len(result.expectedFailures),'unexpected_successes':len(result.unexpectedSuccesses),
        'output_sha256':hashlib.sha256(output).hexdigest(),'output_bytes':len(output),
        'tools':tool_rows,'python':sys.version.split()[0],
        'schema_tools':{name:importlib.metadata.version(name) for name in profile['schema_tools']}}
    print(json.dumps(report,sort_keys=True,separators=(',',':')))
    if not passed:
        # Only test ids and fixed summary counts reach the conformance interface.
        print('records-and-signatures execution failed',file=sys.stderr)
        for category in ('failure_cases','error_cases'):
            for case in report[category]:print(category+': '+case,file=sys.stderr)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
