# Study: structured runner reports for the Elenchus guard check

## Assumptions

Assuming, unless corrected:

1. Work starts from `c29159d098dd468f07ba1edde3c03614106b3694` in the Wildcat Skills repository.
2. The held job remains word for word: “Teach the check to read a runner's own report rather than its exit code and output text, so an assertion failure is told from a broken run by structure instead of by matching error strings. Accepted when it classifies correctly for unittest, forge and one JavaScript runner in fixture repositories, with no string matching left in the decision, and both suites pass.”
3. “Both suites” means `python3 plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest discover -s tests`, run from the repository root.
4. The checker and its report parsers remain Python standard-library code. Forge and Node are test runners under inspection, not new Python dependencies.
5. The JavaScript runner is Node's built-in `node:test`. It is chosen because its documented `TestsStream` supplies structured events and a fixture needs no package install or lockfile.
6. The observed local toolchain is Python 3.14.6, Forge 1.7.1 and Node 26.6.0. The fixture evidence establishes these versions; broader version support is not claimed without another fixture run.
7. A unittest fixture may carry a small runner-owned emitter because stdlib unittest has no native JSON file. The emitter serialises the `TestResult` categories; it does not infer a category from traceback text.
8. A runner report is authoritative only if it is fresh, parseable, complete and records at least one executed test. Missing, stale, malformed, partial and zero-test reports are `inconclusive`.
9. Output and exit status remain available as diagnostics. Neither is an input to the guarded/passed/inconclusive decision.

These assumptions choose a fail-closed interface over silent compatibility. An old invocation that supplies only `--test-command` cannot prove a guard and therefore returns `inconclusive`; it never falls back to the current string heuristic.

## Problem statement

Elenchus tests whether a fix commit carries a real guard by copying the commit's changed test files onto its parent and running them there. It reports:

- `guarded` when the overlaid test makes an assertion fail on the parent;
- `unguarded` when the fix commit changed no test file;
- `passed` when the test also passes on the parent; and
- `inconclusive` when the run breaks before a useful assertion.

The current implementation makes the critical distinction using the process exit code and the `BROKEN_RUN` tuple in `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py`. `broken_run(output)` lowercases stdout and stderr and searches for fragments such as `importerror`, `cannot find module`, `compiler run failed` and `syntaxerror`. This can call a genuine assertion inconclusive when its diagnostic contains one of those phrases, or call a broken run guarded when a runner changes its wording.

Build a structured-report boundary for maintainers who use Elenchus against Python, Solidity and JavaScript fixes. The test command must produce a declared runner report. Elenchus parses that report into one small internal outcome and decides from the report's fields, never from process text or exit status.

A working prototype classifies `guarded`, `passed` and `inconclusive` correctly in three real git fixture repositories: stdlib unittest, Forge and Node `node:test`. Each fixture must contain an assertion failure on the parent, a test that passes on the parent and a run that breaks before assertion. Diagnostic poisoning must also prove that failure wording cannot change the decision.

### Demo path and success criteria

Run from the Wildcat Skills root:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
```

The prototype is accepted only when all of these are true:

1. The unittest fixture classifies a `TestResult.failure` as `guarded`, a clean result as `passed`, and a `TestResult.error` as `inconclusive`.
2. The Forge fixture classifies a JUnit `<failure>` from a test revert/assertion as `guarded`, a report with executed passing cases as `passed`, and a compile failure that produces no valid report as `inconclusive`.
3. The Node fixture classifies an assertion event from `TestsStream` as `guarded`, completed passing test events as `passed`, and a load/runtime error event as `inconclusive`.
4. A missing, malformed, incomplete, stale or zero-executed-test report is `inconclusive` for every applicable adapter.
5. A run whose diagnostic text says `ModuleNotFoundError` but whose report records an assertion stays `guarded`; a broken report whose diagnostic says `AssertionError` stays `inconclusive`.
6. The decision function contains no substring, regular-expression or exception-message matching. `BROKEN_RUN` and `broken_run()` are absent.
7. Exit-code changes with an unchanged complete report do not change the classification.
8. The original fixture repository's working tree is unchanged after each check, and temporary report files and worktrees are removed.
9. The focused test and both named suites exit zero. The current baseline is 8 focused Elenchus tests, 167 Hexaemeron tests and 24 root tests.

## Prior art

### In this repository

- `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` already supplies the git mechanics, changed-test detection, detached parent worktree, test overlay, timeout, cleanup, result shape, audit line and `--require-guard` policy. Those remain the compatibility boundary.
- The same file's `BROKEN_RUN` tuple and `broken_run(output)` name the defect this frontier removes. The output slice in the returned result is diagnostic evidence, not a classification API.
- `plugins/hexaemeron/tests/test_elenchus_checker.py` builds a real temporary git repository. Its commits cover guarded, unguarded, passed and import-broken outcomes and verify that the source working tree stays untouched. The report fixtures should preserve this style rather than mock git or runners.
- `plugins/hexaemeron/skills/elenchus/SKILL.md` says that an assertion failure is a guard and an import/build failure is inconclusive. It also treats error output as untrusted data, which rules out using text as a control signal.
- `plugins/hexaemeron/skills/elenchus/EVOLUTION.md` holds the exact job under frontier revision `observed-failure-root-cause` at `elenchus-v0.1.0`.
- Commit `5b1105a` introduced Elenchus, its checker, tests and ledger. There is no later checker history to reconcile.
- `plugins/hexaemeron/tests/run_tests.py` discovers the Hexaemeron suite and prints a pass count. The root suite enforces portable skill and evolution contracts affected by a completed frontier change.
- `plugins/ariadne/tests/fixtures/forge-project/` and `plugins/pandects/foundry.toml` show dependency-light Foundry fixtures pinned to Solidity 0.8.28. Their generated `out/` trees are reading-boundary exclusions and are not prior-art inputs.

### Runner-owned structures

- Python's `unittest.TestResult` has separate `failures` and `errors` collections. `addFailure` records a test's assertion failure; `addError` records an unexpected exception. `TestRunner.run()` returns the result for reporting tools. This is the structured distinction the JSON emitter preserves.
- Local `forge test --help` at Forge 1.7.1 exposes `--junit`, described as a JUnit XML test report. A completed test failure appears as a test-case failure; compilation that prevents a run from producing a valid report leaves no accepted report.
- Node documents built-in test reporters but warns that their rendered output is not a programmatic interface. It directs consumers to `TestsStream`, whose `test:pass`, `test:fail`, `test:complete` and `test:summary` events carry structured execution metadata and the actual thrown error as `details.error.cause`.
- JUnit XML uses `testcase`, `failure`, `error` and `skipped` elements. It has no single formal specification across all producers, so the Forge adapter accepts only the exact subset anchored by the fixture.

## Constraints and non-goals

### Constraints

- Preserve result statuses, the `check()` purpose, `audit_line()`, JSON/text CLI output and default `--require-guard` severity. Change only how a completed runner invocation is classified.
- Keep `changed_tests`, parent lookup, overlay and worktree cleanup behaviour unless a report-path safety fix requires a narrow change.
- Add explicit `--report-format` and `--report-file` inputs. The declared file is resolved inside the detached worktree, removed before the run, and substituted for one exact `{report}` argument in the declared command. Remove any inherited `ELENCHUS_REPORT_FILE` variable so nested commands cannot acquire the path by accident.
- Accept three declared formats: versioned unittest JSON, Forge JUnit XML and versioned Node test JSON. Parse JSON with `json` and XML with `xml.etree.ElementTree`.
- Require a schema/version marker, completion marker where the native format supports one, non-negative integer counts and at least one executed test. Reject contradictions such as totals smaller than failures.
- Classify a mixed report containing both assertion failures and infrastructure errors as `inconclusive`; a broken run cannot establish a clean guard merely because one assertion also fired.
- Cap report size before parsing and never expand external XML entities. A report is untrusted data produced by code under test.
- Leave stdout and stderr out of every classification branch. They may be retained, bounded and returned for a person to read.
- Treat timeout, executable-not-found, signal interruption, missing report, invalid report, zero tests and parser exceptions as `inconclusive`.
- Do not skip Forge or Node fixture tests when their runners are absent and still claim acceptance. Tool absence means the held acceptance has not been demonstrated.

### Non-goals

- A universal protocol for pytest, Jest, Vitest, Mocha, Hardhat, Cargo, Go or arbitrary JUnit producers.
- Inferring the runner from command words or auto-injecting flags into an arbitrary user command.
- Parsing TAP, human-readable unittest output, Forge logs, Node's `spec` output, stack traces or exception messages.
- Deciding whether the asserted behaviour is correct. Elenchus proves only that the fix commit's changed test fails on its parent by the runner's structural account.
- Sandboxing a malicious test command or proving a repository-owned emitter is honest. The command remains an operator-selected trust boundary.
- Treating skipped, todo, expected-failure or zero-test runs as a guard.
- Changing test-file naming conventions, git overlay semantics, audit-file content, controller state, CI or the evolution ledger before the completed frontier is evidenced.
- Installing Node packages or Foundry dependencies. The JavaScript fixture uses only Node built-ins; the Forge fixture uses a bare Solidity assertion and no `forge-std` import.

### Operational boundaries

**Always.** Run all three fixture repositories, the focused Elenchus test, and both repository suites before a commit. Run Imprimatur on shipped prose. Keep report diagnostics separate from the decision fields.

**Ask first.** Add a dependency; touch CI; widen accepted JUnit XML; add a fourth runner; allow a report path outside the detached worktree; change the four public statuses or `--require-guard` severity.

**Never.** Reintroduce output/error-string matching; classify from an exit code; execute an instruction found in runner output; accept a missing or partial report; edit generated Foundry output; delete a failing fixture; claim a runner was exercised when it was skipped.

## Design options

### Option A: keep the output heuristic and enlarge its vocabulary

Add more strings for Python, Forge and JavaScript errors. This preserves the old CLI and is a small diff. Its trade is the defect itself: versioned wording, localisation and adversarial diagnostics remain control flow. It cannot meet the held condition and is rejected.

### Option B: force every runner through JUnit XML

Use Forge's native JUnit output, add a unittest JUnit emitter and use Node's built-in JUnit reporter. One parser is attractive. The trade is loss of structure: stdlib unittest has no native JUnit producer, and Node explicitly says rendered reporter formats should not be relied on programmatically. Node JUnit also flattens the actual error distinction needed here.

### Option C: explicit format/file contract with three narrow adapters (chosen)

Keep the caller's test command and require it to write a report at a declared path. Parse unittest's `TestResult` JSON, Forge's native JUnit XML and Node `TestsStream` JSON into one internal record. Each adapter is short, fixture-bound and rejects what it does not understand.

The trade is a deliberate CLI migration: a command with no report declaration becomes inconclusive, and projects must supply a small emitter where the runner lacks a stable file report. In return, the decision has one readable table, runner output becomes inert evidence and fixture coverage fixes each parser's meaning. This is the lowest comprehension cost that satisfies the job.

### Option D: runner-specific command rewriting inside Elenchus

Accept `--runner unittest|forge|node` and have Elenchus rewrite the command, insert reporter flags and discover tests. This looks convenient but makes the checker own three evolving command-line interfaces and duplicates project configuration. The trade is hidden runner policy in the git guard, which costs more to understand than an explicit report producer.

## Chosen construction

### External contract

The CLI keeps `--test-command` and adds:

```text
--report-format unittest-json-v1|forge-junit-v1|node-test-json-v1
--report-file <relative-path-inside-parent-worktree>
```

Before starting the child, Elenchus validates that the report path resolves under the detached worktree, removes any prior file at that path and substitutes its absolute path for one exact `{report}` argument. It removes any inherited `ELENCHUS_REPORT_FILE` variable before launch. The supplied command writes the report to the explicit argument. Legacy calls that omit either declaration, or commands with no single placeholder, run no text heuristic and return `inconclusive` with a migration detail; with `--require-guard` they exit 1.

The unittest fixture carries a stdlib emitter that discovers tests, runs them, and writes a versioned JSON object from `TestResult.testsRun`, `failures`, `errors`, `skipped`, `expectedFailures` and `unexpectedSuccesses`. It records counts and completion, not traceback strings.

The Forge fixture carries a small stdlib launcher that sends native `forge test --junit` XML to the report-path argument. The parser counts executed `testcase` elements and their `failure`, `error` and `skipped` children. A compiler failure produces no accepted XML and is therefore inconclusive.

The Node fixture carries a custom reporter over `node:test`'s programmatic `TestsStream`. It writes versioned JSON counts, marks an assertion using the actual assertion-error type/structured cause, marks other failed events as errors, and writes `complete: true` only after the stream ends. It uses no npm dependency.

### Normalised report and decision

Every adapter returns this internal shape:

```text
complete: bool
executed: non-negative integer
assertion_failures: non-negative integer
errors: non-negative integer
skipped: non-negative integer
```

The decision is ordered and runner-neutral:

| Condition | Status |
| --- | --- |
| no changed tests in the fix commit | `unguarded` |
| no parent, timeout, child launch failure, unsafe path, missing/stale/malformed/oversized/incomplete report | `inconclusive` |
| `executed == 0` or `errors > 0` | `inconclusive` |
| `assertion_failures > 0` and `errors == 0` | `guarded` |
| `executed > 0`, `assertion_failures == 0`, `errors == 0` | `passed` |

Exit code and diagnostic bytes appear nowhere in this table. String equality on report schema identifiers is format dispatch, not error diagnosis; no diagnostic content is searched or compared.

### Fixture repositories

Each runner gets its own temporary git repository so its command and report emitter are real:

- **unittest:** a buggy Python adder in the parent; a changed assertion that catches it; a harmless passing test; and a changed test importing a module added only by the fix commit.
- **Forge:** a dependency-free Solidity adder and `foundry.toml` pinned to Solidity 0.8.28; a changed bare `assert` guard; a passing arithmetic test; and a changed test importing a contract absent from the parent.
- **Node:** an ES module adder, built-in `node:test` plus `node:assert/strict`, and the `TestsStream` reporter in the base commit; guarded, passing and missing-module commits parallel the other fixtures.

Add adversarial diagnostics to at least one guarded and one broken case. The words must disagree with the structured report, proving the old heuristic cannot influence the result. Keep the common unguarded, severity, test-file detection and clean-working-tree tests.

## Risk register seed

| Area | Boundary or failure | Control | Audit evidence |
| --- | --- | --- | --- |
| Runner report | Test code can emit arbitrary JSON/XML or forge a completion marker. | The operator declares a reviewed emitter; parsers validate exact schemas and fail closed. | Fixture emitter source and parser rejection tests. |
| Diagnostic injection | Stdout/stderr can contain instruction-shaped or classifier-shaped text. | Diagnostics are stored only for humans; the decision accepts only normalised fields. | Poisoned-output tests with opposite structured outcomes. |
| Subprocess | Command missing, killed, timed out or signalled. | Catch launch/timeout failures and return inconclusive; use argument lists and no shell. | Fixture or mocked launch-boundary tests plus cleanup assertions. |
| Filesystem | A report path can escape the worktree, follow a symlink or overwrite a tracked file. | Require a relative resolved descendant, reject symlinks and pre-existing tracked targets, remove stale files before the run. | Traversal, absolute-path, symlink and stale-report tests. |
| Partial writes | A killed emitter leaves valid-looking JSON/XML without a complete run. | Require completion marker for JSON; parse Forge XML only after process end; timeout always wins. | Truncated JSON/XML and timeout fixtures. |
| Resource use | A crafted report can exhaust memory or XML parsing time. | Enforce a small byte cap before stdlib parsing and reject oversized files. | Boundary-size tests. |
| Arithmetic | Negative, contradictory or boolean-as-integer counts can cross the decision table. | Validate exact integer types, non-negative values and count relationships before normalising. | Schema property tests for invalid counts. |
| unittest | Traceback text exists inside `TestResult` entries and could tempt matching. | Emitter serialises category counts only; `failures` and `errors` come from runner callbacks. | Assertion/import fixtures whose messages contain misleading terms. |
| Forge | JUnit is a producer convention rather than a fully stable standard; compile failures may emit surrounding logs. | Accept only fixture-proven Forge 1.7.1 XML elements; missing valid XML is inconclusive. | Captured fixture reports for pass, assertion and compile failure. |
| Node | Rendered reporters are unstable and Error identity may vary with isolation/version. | Use documented `TestsStream`; pin fixture evidence to Node 26.6.0; classify from structured cause/type, not rendered text. | Reporter fixture and recorded Node version. |
| Git worktree | Reports and runner artifacts can dirty the source repo or survive interruption. | Run only in the detached parent tree and keep unconditional worktree/temp cleanup. | Before/after source status and worktree-list assertions. |
| Secret material | Test diagnostics may contain credentials. | Keep bounded diagnostics, do not echo them during classification and never include them in fixed detail strings. | Result-output test using a sentinel secret. |
| Compatibility | Old callers expect exit/output classification. | Retain flag name and public statuses but fail legacy no-report calls closed with a clear migration detail. | Legacy invocation test, including `--require-guard`. |

There is no Solidity storage change, public ABI, upgrade path, arithmetic over protocol funds or signer custody in the implementation. Forge is present only as a fixture runner.

## Glossary seeds

| Term | Meaning |
| --- | --- |
| assertion failure | A runner-owned result category showing that an executed test explicitly rejected the parent behaviour. |
| broken run | A command that did not reach a trustworthy assertion result because loading, collection, compilation, setup or execution infrastructure failed. |
| complete report | A fresh report whose parser sees the producer's terminal structure and consistent counts. |
| diagnostic output | Stdout and stderr retained for a person but excluded from classification. |
| emitter | A runner-specific fixture component that serialises the runner's structured result to the declared report file. |
| executed test | A non-skipped test case the runner reports as having reached an outcome. |
| fixture repository | A real temporary git history containing parent, fix, tests and runner configuration for one report format. |
| legacy no-report run | An invocation with a test command but no declared structured report; it is inconclusive. |
| normalised report | The five-field internal record returned by every report parser. |
| report adapter | The narrow parser that validates one declared runner report and produces the normalised record. |
| runner-owned structure | Categories or events supplied by the runner API, not inferred from rendered prose. |
| stale report | A report that existed before the current child started or was not freshly completed by it. |

## Sources

- Starting ref: `c29159d098dd468f07ba1edde3c03614106b3694`.
- Elenchus checker: `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` at the starting ref.
- Elenchus fixture tests: `plugins/hexaemeron/tests/test_elenchus_checker.py` at the starting ref.
- Elenchus policy and held frontier: `plugins/hexaemeron/skills/elenchus/SKILL.md` and `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`.
- Elenchus introduction: Git commit `5b1105a`.
- Hexaemeron runner: `plugins/hexaemeron/tests/run_tests.py`.
- Local runner probes: `python3 --version` = 3.14.6; `forge --version` = 1.7.1; `node --version` = 26.6.0; `forge test --help` documents `--junit`.
- Python `unittest.TestResult`: <https://docs.python.org/3/library/unittest.html#unittest.TestResult> (`failures`, `errors`, `addFailure`, `addError`).
- Node test reporters and `TestsStream`: <https://nodejs.org/api/test.html#test-reporters> and <https://nodejs.org/api/test.html#class-testsstream>.
- Node `test:fail` event structure: <https://nodejs.org/api/test.html#event-testfail> (`details.error.cause`).
- Foundry test command reference: <https://getfoundry.sh/forge/tests> and the local Forge 1.7.1 `forge test --help` output.
- Foundry JUnit feature history: <https://github.com/foundry-rs/foundry/issues/7004>.
- Python XML parser used for the narrow JUnit subset: <https://docs.python.org/3/library/xml.etree.elementtree.html>.
