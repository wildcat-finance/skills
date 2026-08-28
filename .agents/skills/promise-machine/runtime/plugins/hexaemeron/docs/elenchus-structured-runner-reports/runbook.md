# Elenchus structured runner-report runbook

This run has one step. The report adapters, the shared decision table, the
three fixture repositories, the public command contract, the skill text and
the frontier ledger all change the same compatibility boundary. Splitting
them would leave either an undocumented interface or a classifier with no
cross-runner proof.

## Step 1: Replace diagnostic matching with structured runner reports

**Goal.** Make Elenchus decide `guarded`, `passed` or `inconclusive` from a
fresh runner-owned report for unittest, Forge and Node `node:test`, with no
exit-code or diagnostic-text matching in the decision.

**Entry.** Controller base `main` at
`c29159d098dd468f07ba1edde3c03614106b3694`; controller run branch
`fiat/teach-the-check-to-read-a-runner-s-own-report-ra`. The implementation
step branches from that run branch using the exact `branch` and `branch_from`
in the controller's implementation directive. Elenchus is
`elenchus-v0.1.0`; its checker still carries `BROKEN_RUN` and
`broken_run(output)`. Baselines at this ref are 8 focused Elenchus tests, 167
Hexaemeron tests and 24 root tests, all green under Python 3.14.6. The runner
fixtures will be exercised with Forge 1.7.1 and Node 26.6.0.

**Exit.** `elenchus.py` accepts the explicit report-format and report-file
contract from the study, substitutes the path for one exact `{report}` command
argument without exporting an inheritable report variable, validates paths and sizes, parses versioned
unittest `TestResult` JSON, Forge JUnit XML and Node `TestsStream` JSON, and
normalises each into completion, executed, assertion-failure, error and skip
counts. The shared decision table fails closed for missing, stale, malformed,
partial, oversized, mixed-error, zero-test, timed-out, interrupted and legacy
no-report runs. Exit codes and stdout/stderr remain diagnostic only;
`BROKEN_RUN`, `broken_run()` and all diagnostic-string classification are
gone. Real git fixtures prove guarded, passed and broken outcomes for all
three runners, including diagnostics whose words contradict the structured
result. Existing statuses, audit-line shape, default severity, changed-test
detection, parent overlay and source-tree cleanliness remain covered.

The repository also contains prose-checked copies of this study and runbook.
`SKILL.md` documents the new command contract and its fail-closed limits.
Elenchus's governed version advances once from `elenchus-v0.1.0` to
`elenchus-v1.1.0`; its evolution ledger records the completed evidence and
either one concrete evidenced next job or a mature frontier with
`None -- mature`, following `skills/VERSIONING.md`. The focused test, both
repository suites and the final demo below exit zero, the audit closes clean,
and the run completes through one merged integration pull request.

**Files.** Change
`plugins/hexaemeron/skills/elenchus/scripts/elenchus.py`,
`plugins/hexaemeron/tests/test_elenchus_checker.py`,
`plugins/hexaemeron/skills/elenchus/SKILL.md`, and
`plugins/hexaemeron/skills/elenchus/EVOLUTION.md`. Create
`plugins/hexaemeron/docs/elenchus-structured-runner-reports/study.md` and
`plugins/hexaemeron/docs/elenchus-structured-runner-reports/runbook.md` as
committed copies of the completed specification and plan. Keep fixture
repository sources inside the focused test unless a separate fixture file is
needed to make a runner-owned emitter readable; if so, place it under
`plugins/hexaemeron/tests/fixtures/elenchus/` and list every added file in the
step handoff. Do not change Fiat controller state, audit history outside the
required appended step record, other skills, CI, vendored Foundry output or
the portable Elenchus entrypoint unless a failing contract test proves it is
required.

**Tests.** Preserve the entry baselines before editing:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 --version
forge --version
node --version
```

Extend the focused suite with three real temporary git repositories. Each
runner must prove a parent assertion is `guarded`, an unchanged passing test is
`passed`, and an import/load/compile failure is `inconclusive`. Add rejection
cases for a missing report, stale report, malformed report, incomplete report,
oversized report, contradictory counts, mixed assertion and infrastructure
errors, zero executed tests, unsafe report paths, symlinks and legacy
no-report commands. Add at least two poisoned-diagnostic cases: assertion
structure accompanied by broken-run wording, and broken structure accompanied
by assertion wording. Verify timeout and executable-not-found paths clean up
their worktrees and reports. Do not skip Forge or Node cases and count the
suite as acceptance.

Run the final demo from the repository root:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
git diff --check
```

Then verify that the old classifier is absent and that all changed prose is
clean:

```bash
! rg -n 'BROKEN_RUN|broken_run\(' plugins/hexaemeron/skills/elenchus plugins/hexaemeron/tests/test_elenchus_checker.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/elenchus/SKILL.md plugins/hexaemeron/skills/elenchus/EVOLUTION.md plugins/hexaemeron/docs/elenchus-structured-runner-reports/study.md plugins/hexaemeron/docs/elenchus-structured-runner-reports/runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/elenchus plugins/hexaemeron/tests/test_elenchus_checker.py
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins/hexaemeron/skills/elenchus plugins/hexaemeron/tests/test_elenchus_checker.py
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/hexaemeron/skills/elenchus plugins/hexaemeron/docs/elenchus-structured-runner-reports
```

The audit concentrates on report-path containment and symlinks, stale and
partial files, JSON/XML size and schema validation, XML entity handling,
boolean-as-integer and contradictory counts, subprocess interruption,
diagnostic poisoning, secret-bearing output, Node error identity, the exact
Forge JUnit subset, cleanup of detached worktrees, backward-command severity,
and the evolution digest. The prose phase covers the committed study and
runbook, changed Elenchus prose, the appended audit record, and the pull
request title and body.
