# Reviewed corpus reconciliation

Step 1 preserves the selected `staged-general-v1` contract and adds a report
emitter for the existing 352 corpus tests and the joined front-door module.
It also isolates that module's scratch fixtures from their sources. Prepare,
apply, recovery and the completed law demonstration remain Step 2 work.

## Contract and evidence

Read the [study](study.md), [runbook](runbook.md),
[design matrix](design-evidence.json) and decision
`adr/stage-reviewed-corpus-reconciliation`. The matrix has 15 resolved selection
cells and nine pending conformance cells. Only the selected candidate's three
integration cells gate delivery. The 18 reports include three `review-boundary`
probe results outside the matrix; those are preserved observations.

[source-copies.json](source-copies.json) binds each copy to its original
`.hexaemeron/` path, byte count and SHA-256. The study copy appends only its
design bridge to the exact receipted prefix. The runbook, design matrix,
reports, raw probes, scripts, baseline, prior-art responses and scoped audit
inventory retain their source bytes. No controller state, receipt or operator
configuration is part of this package. The runbook includes the receipted
fixture-isolation amendment; its previous bytes remain in
[the historical copy](history/runbook-before-fixture-isolation.md.txt).

Historical `study-source.md`, `study-prose-source.md` and
`runbook-prose-source.md` copies carry a `.txt` suffix here. Their bytes and
original source paths stay bound in `source-copies.json`; the suffix separates
preserved drafts from current runtime instructions.

Paths inside those historical records describe the original run. In this
directory their `.hexaemeron/` prefix maps to
`docs/agent-instruction-reconciliation/`; report paths remain relative to the
design record. Their command strings and digests are unchanged. The preserved
scripts expect their original `.hexaemeron/scripts/` location and must be
restored there in a disposable checkout before execution. They are evidence
scripts, with the bounds and omissions recorded in
[probe-environment.json](study-evidence/probe-environment.json).

## Run the focused report

From this repository root, use the interpreter in
[`.python-version`](../../.python-version), recorded as 3.14.6 for this study:

```sh
uv run --no-project --python "$(cat .python-version)" python tests/emit_agent_instruction_reconciliation_report.py .elenchus/agent-instruction-reconciliation.json
```

The emitter runs `tests.test_agent_instruction`,
`tests.test_agent_instruction_corpus` and `tests.test_joined_front_door`
in process with fixed module names.
It reuses the confined writer in `tests/emit_run_observation_report.py`:
one fresh path inside the current worktree, exclusive file creation and
identity-checked readback. Preserve an earlier report before reusing its name.
The output uses `elenchus.unittest.v1`; counts come from the actual completed
run. Failed tests and unexpected successes exit 1; report-path or write failure
exits 2. An interrupted run does not emit a completed result. The report answers
which tests ran, whether the run completed, and what failed or was skipped.

## Fixture isolation evidence

The [first full report](fixture-isolation/step-1-checks.json) passed 34 of 35
checks. One demonstration setup refused a source with D025
`file-changed-during-read`. The independent demonstration suite then passed
114 tests on the same signed commit. The
[disposable reproduction](fixture-isolation/metadata-reproduction.json)
shows that creating a hard link changes source ctime without changing its
bytes. The original failing process was not instrumented, so attribution to
the concurrent joined front-door fixture remains inferred.

The fixture builder now creates independent copies. Its new guard checks that
source identity and bytes survive fixture creation, mutation and deletion.
The [original implementation fails](fixture-isolation/fixture-guard-old.stderr)
that guard; the [copy implementation passes](fixture-isolation/fixture-guard-fixed.stderr).
This proves the fixture repair. It does not replay the original scheduling
race or establish corpus reconciliation behavior.

## Reproduce the selection probes

Use a disposable checkout at commit
`b9f8e36b8b6210bcd023a68059ecb46da3e35769`, tree
`5f48caffde9c41846e13dfdda5c5f10165d3e274`, with this evidence directory
copied into it. Leave an active Fiat run's evidence untouched. Restore only
the two preserved scripts to a new `.hexaemeron/scripts/` directory, and create
empty `.hexaemeron/reports/` and `.hexaemeron/study-evidence/` directories.

```sh
uv run --no-project --python "$(cat .python-version)" python .hexaemeron/scripts/probe_reconciliation_design.py --candidate fixed-live-v1
uv run --no-project --python "$(cat .python-version)" python .hexaemeron/scripts/probe_reconciliation_design.py --candidate sequential-general-v1
uv run --no-project --python "$(cat .python-version)" python .hexaemeron/scripts/probe_reconciliation_design.py --candidate staged-general-v1
```

These commands create new observations. Compare them with the frozen reports;
timings may differ. Six correctly classified placements include three
before-span `WAI-E-DIGEST.CORPUS` refusals, so the count does not establish six
green corpora. The four-target injected-fault probe establishes handled
restoration only. Durable crash recovery, complete publication and fresh model
acquisitions remain unestablished here.

The conformance resolver remains preserved at its original digest. Its exact
commands in the design matrix are due at integration after Step 2; restoring
the script alone supplies none of those results. Baseline and selection
evidence describe the pinned source tree, not later changes.
