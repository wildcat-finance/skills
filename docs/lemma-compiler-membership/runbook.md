# Pinned compiler event membership runbook

Assuming the receipted study remains current, this run repairs issue #1983 in Lemma. It starts from `25e1e74cdf312cc4c2603b420f901fa0bd4f2a3d`. Python is pinned by `.python-version`. The study and its design evidence define the scope; the completed Wildcat tranche of #1366 and the remaining venue work in #1359 stay separate.

```design-lock
schema | protasis-design-evidence/v1
sha256 | bc94eb4a613e6345f1399a3c4242f50b966bb5af8ed209efd72c3f7f82b1cf68
candidate | pinned-inheritance
```

```version-relations
lemma | plugins/lemma/skills/lemma/EVOLUTION.md | next-generation-after-integration-base
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/lemma/tests/emit_issue_1983_report.py | build_parser | step:1
```

Known-failure assignment: `kf-1983-legacy-membership` -> Step 1

## Step 1: Scaffold the regression and repair pinned event membership

**Goal.** Preserve the parent failure, then accept healthy outputs from `0.8.10+commit.fc410830` and `0.8.19+commit.7dd6d404` without weakening the independent AST/ABI comparison. First add only the six inventory guard paths, commit them with a valid signature, retain the failing parent guard and receipt inoculation. Product work starts after that receipt. Derive legacy membership from declarations in compiler linearization order, selecting the first declaration for each external event signature. Keep parameter names, tuple component names, indexed flags and anonymous status out of that membership key but retain them in the compared descriptors. Preserve modern `usedEvents` behavior; malformed present lists still refuse. Admit only the exact compiler identities and tested official suffix forms. Direct validation without a version remains strict. Pass the version already observed by build through chunk without another compiler query. Bound repeated legacy traversal at 1,000,000 visits alongside existing limits.

**Entry.** The study and design lock are receipted, baseline event, Markdown, compiler-backed Solidity and root suites pass, and the controller assigns Step 1 with the exact parent and six closed guard paths. Existing layout, licence, CI and toolchain pins suffice; the new test module, reporter and public fixtures are the scaffold.

**Exit.** `python3 scripts/run_checks.py --scope lemma --scope root` exits zero. `python3 plugins/lemma/tests/emit_issue_1983_report.py --case event-tests --report .elenchus/issue-1983-step-1-exit.json` exits zero with completed tests, no failures, errors or skips. The controller independently retains the failing parent evidence before implementation and the green repair evidence afterwards.

**Files.** `plugins/lemma/chunkers/solidity.py`; the six inventory paths under `plugins/lemma/tests/`; `tests/check-map-v1.json`; Lemma's canonical `SKILL.md`, `INVARIANTS.md` and `EVOLUTION.md`; Lemma package and marketplace version metadata; repository copies of the study and runbook under `docs/lemma-compiler-membership/`; required decision records and generated portable runtime, Horos boundary and census. Keep the held `abi-return-mutability` frontier. Private inputs and controller evidence remain outside tracked files.

**Tests.** The parent guard calls the existing CLI with retained public compiler outputs and observed version strings, so the old refusal is an assertion failure rather than an unsupported-call error. Cover both old builds and the healthy 0.8.22 control; inherited and excluded declarations; overloaded and anonymous events; duplicate signatures with different metadata; tuple arrays; library event membership; malformed bases and version strings; unknown compilers; present malformed modern metadata; exact traversal limits; existing output preservation and a mismatch in a later build unit. Extend the checked runner's Lemma selection to execute the new suite. Elenchus command: `python3 plugins/lemma/tests/emit_issue_1983_report.py --case event-tests --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/issue-1983-step-1.json`.

**Disciplines.** Phylax checks compiler-output and identity trust boundaries. Ephoros checks that each refusal identifies its source and owner. Metron checks bounded traversal and zero added compiler queries; no speed improvement is claimed. Elenchus owns the retained parent failure and its green repair. Hypomnema records the compatibility decision and unchanged exclusions in the skill, S8 agreement rule and delivery documents. Warden independently audits the complete diff, with the non-Solidity security waiver recorded in controller state. Sapheneia, Imprimatur, Vulgate and Brevitas govern authored prose. Generated copies retain their owner's bytes.

## Step 2: Demonstrate compiler and CLI conformance

**Goal.** Show the accepted repair against actual pinned compiler executions and the two retained Aave inputs, then emit the selected design's production-conformance report. Compile the public specimen with the exact 0.8.10, 0.8.19 and 0.8.22 builds, run healthy and indexed-bit mismatch cases, and demonstrate refusal without replacing existing JSONL or manifest outputs. Rebuild retained set-001 and set-034 with their pinned compiler versions and input digests. These observations answer #1983 only; they do not complete #1359 or the remaining #1366 venue validation.

**Entry.** Step 1 is audited, prose-reviewed, signed, pushed and receipted. The controller records that Step 2 has no assigned known finding. The three verified compiler launchers and retained input digests from the study remain available. Stop the demonstration on missing or changed bytes rather than substituting a compiler or input.

**Exit.** `python3 scripts/run_checks.py --scope lemma --scope root` exits zero. `python3 plugins/lemma/tests/emit_issue_1983_report.py --case production-conformance --report .hexaemeron/reports/pinned-inheritance-production-conformance.json` exits zero and emits a passing report for the fixed pinned-inheritance candidate and production-conformance criterion. The selected design's integration gate consumes that exact report.

**Files.** `plugins/lemma/tests/test_legacy_events.py` and public fixtures if the demonstration exposes a missing guard; `docs/lemma-compiler-membership/validation.md`; generated Horos records where required. The reporter's interface stays fixed after its Step 1 binding. Actual compiler transcripts, private input identities and machine reports remain in `.hexaemeron/evidence/` and `.hexaemeron/reports/`.

**Tests.** Execute actual compiler and CLI checks twice where determinism is claimed. Compare healthy JSONL and manifest bytes, inspect the independent expected event descriptors, and mutate indexed metadata to force refusal. Re-run the full compiler-backed Solidity suite with the verified 0.8.25 launcher. Record command, compiler identity, input/output digest, exit status and coverage in the demonstration evidence. The production reporter runs the new and existing event tests and derives its result from executed counters. Elenchus command: `python3 plugins/lemma/tests/emit_issue_1983_report.py --case event-tests --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/issue-1983-step-2.json`.

**Disciplines.** Phylax checks retained-input and output custody. Ephoros checks readable refusal evidence. Metron checks deterministic observations without making a speed claim. Elenchus reruns the source-bound tests. Hypomnema writes the bounded validation record and names the unperformed venue work. Warden audits any test or documentation changes. Sapheneia, Imprimatur, Vulgate and Brevitas govern authored prose. The integration owner resolves the declared Lemma generation against the current base, runs the required checks and verifies remote delivery before closing #1983.
