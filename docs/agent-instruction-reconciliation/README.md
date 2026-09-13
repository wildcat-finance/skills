# Reviewed corpus reconciliation

The staged repair now prepares every fixture bound to one edited source,
admits complete owner evidence and publishes through a recovery journal.
The [recorded demonstration](demonstration.json) completes a moved law-span
repair with fresh measurement and parity. The live product corpus and its
reviewed profiles remain unchanged.

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
`tests.test_agent_instruction_corpus`, `tests.test_joined_front_door` and
`tests.test_agent_instruction_reconciliation`
in process with fixed module names.
It reuses the confined writer in `tests/emit_run_observation_report.py`:
one fresh path inside the current worktree, exclusive file creation and
identity-checked readback. Preserve an earlier report before reusing its name.
The output uses `elenchus.unittest.v1`; counts come from the actual completed
run. Failed tests and unexpected successes exit 1; report-path or write failure
exits 2. An interrupted run does not emit a completed result. The report answers
which tests ran, whether the run completed, and what failed or was skipped.

## Prepare and admit evidence

Choose the full immutable commit whose corpus was accepted before the source
edit. The baseline must exist locally. The tool verifies its commit, path-tree
and blob identities, then checks the complete fixture/evidence closure with
the running owner. It does not check out code from that commit.

```sh
baseline=$(git rev-parse HEAD)
uv run --no-project --python "$(cat .python-version)" python scripts/prove_agent_instruction_reconciliation.py prepare --root . --baseline "$baseline" --source PROMISE_MACHINE.md --stage tmp/law-repair
```

Use a new stage path. Preserve the printed `plan_sha256` as `plan_sha256` for
the next commands. Preparation leaves live product files untouched and calls
no model. It locates exact unchanged reviewed anchors and nodes, selects every
fixture bound to the source, and refuses changed or ambiguous reviewed bytes,
unrelated drift and unsafe paths. Absolute v1 offsets remain absolute.

The result names corpus, profile and report identities, measured-stream
identities and `ready` or `needs-evidence` states. Profile readiness means
that the stored record matches its source-owned authority. The actual owner
acquisition also checks the installed runtime and model identities.
Before-span edits require fresh reports because recorded offsets contribute
to measured model and compact streams. After-span edits may retain exact old
reports when the full owner checker accepts their unchanged inputs.

Run both printed owner commands. Their separate output paths keep the old
bound reports and manifest coherent throughout acquisition:

```sh
uv run --no-project --python "$(cat .python-version)" python scripts/agent_instruction.py measure --root tmp/law-repair/work --manifest tests/fixtures/agent-instruction-v1/manifest.json --output acquisitions/measurement.json
uv run --no-project --python "$(cat .python-version)" python scripts/agent_instruction.py parity --root tmp/law-repair/work --manifest tests/fixtures/agent-instruction-v1/manifest.json --output acquisitions/parity.json
uv run --no-project --python "$(cat .python-version)" python scripts/prove_agent_instruction_reconciliation.py apply --root . --stage tmp/law-repair --plan-sha256 "$plan_sha256" --check-only
```

Preserve each failed attempt, output and timestamp before retrying an output
path. Do not relabel earlier counts or answers. `--check-only` admits the pair
together into `tmp/law-repair/accepted` and runs the full owner checker. It
writes no live product file. A changed profile, incomplete pair or stale report
refuses. The accepted copy is immutable; changed inputs need a new stage.

## Apply and recover

```sh
uv run --no-project --python "$(cat .python-version)" python scripts/prove_agent_instruction_reconciliation.py apply --root . --stage tmp/law-repair --plan-sha256 "$plan_sha256"
```

Apply rechecks live identities, the stage and every bound sibling. It writes
all old/new backups, publication and restoration exchange slots, and the
complete intent before the first live write.
The `journal-durable` event prints its SHA-256 and exact recovery command.
Generated inputs publish before manifest and coverage; every output is read
back before success. The contributor's edited source is never a target.

A handled failure restores the old generated bytes. Retry from a new stage
because restoration gives files new identities. A killed process leaves
`tmp/agent-instruction-reconciliation/active.json`, which blocks another
prepare or apply. Use the journal SHA-256 printed before publication:

```sh
uv run --no-project --python "$(cat .python-version)" python scripts/prove_agent_instruction_reconciliation.py recover --root . --journal-sha256 "$journal_sha256"
```

Recovery validates the complete journal, backups and retained exchange slots
before writing. It binds old, planned new and restored bytes to their stable
file identities. Exchange itself can change ctime; comparison excludes that
field while retaining the byte digest, inode, mode, link count, size and mtime.
A third version, changed source or altered stage refuses and keeps the journal.
Repeating completed recovery verifies the restored set and returns
`already-recovered`.

Publication atomically exchanges the target with its journal-bound
`publish_slot`; restoration uses `restore_slot`. Both files survive the
exchange. If a concurrent version is displaced, the refusal includes a
`conflict` object with its original `target`, retained `path` and exact
`sha256`. Recovery checks that slot even when the live target contains planned
bytes. The tool leaves a further concurrent live version untouched and never
exchanges back to hide a conflict. Preserve both versions and the journal for
explicit resolution by the file's owner; no conflict-resolution override is
provided.

These checks cover tested races, handled exceptions and actual process
termination, including a kill immediately after exchange. Apply requires
Darwin `renameatx_np` or Linux `renameat2` with atomic exchange support. An
unsupported host or filesystem refuses without a replacement fallback.
Per-file fsync and the journal do not supply a hardware power-loss guarantee.
The fixed limits are 1 MiB per file/output,
256 publication targets, 32 MiB total stage bytes and a 600-second owner-check
subprocess deadline. No speed improvement is claimed.

Coverage reports its downstream owner obligation separately. A generated
coverage rebind can stale evaluation, portable and demonstration records.
The repair is complete only after those owners and root checks accept the
composition. Historical evaluation answers may be replayed only after every
corresponding prompt is proven byte-identical, retaining the original model
and date with explicit replay status.

The [current owner replay](evaluation-replay/replay-after-exchange.json) proved all 11 historical
prompts byte-identical and changed only `tree_sha256`. It retains the original
2026-08-31 model, date and answers; it is not a new model observation.

## Verify the completed demonstration

```sh
uv run --no-project --python "$(cat .python-version)" python scripts/prove_agent_instruction_reconciliation.py demonstrate --root . --verify docs/agent-instruction-reconciliation/demonstration.json
```

The record preserves six structural placements. Its before-span law case
completed measurement in 63.551 seconds and parity in 201.785 seconds on the
first acquisition attempt, then applied seven targets and passed the full
owner check: three fixtures, 15 reviewed bindings and 20 checks. Actual calls
ran from 05:03:34 to 05:07:59 UTC on 2026-09-13. The owner reports retain their
frozen profile observation date, 2026-09-12. No acquisition failed.

The first publication used the writer later shown to lose a concurrent
version at its final replacement syscall. That successful attempt remains
preserved as historical evidence. The repaired exchange writer then completed
a new disposable publication and full owner check. All 28 acquisition inputs
were byte-identical, so it reused the same fresh reports without new model
calls or changed acquisition timestamps.

Verification reads the declared content-addressed evidence, verifies preserved
Git objects, recomputes each relocation and checks the accepted owner reports
against their exact corpus and profiles. It uses no model, Git fetch or local
history. Preserved path objects establish the bounded baseline; they do not
establish its parent ancestry or signature history. Offline checks validate
report semantics and byte identities, without independently recounting model
tokens, authenticating the recorded clock or judging model quality.

The boundary evidence records actual SIGKILL recovery, handled rollback and
retry, third-version refusal, hostile inputs and resource limits. Two law/Horos
selection assertions fail under the retained legacy behavior and pass under
the new implementation. A separate exact-syscall guard fails behaviorally
against the preserved pre-exchange writer and passes with the repair. Its
companions retain third and fourth versions, detect same-byte inode
replacement, and refuse a conflict arising during recovery. The recorded
boundary run passed all 26 named tests. A separate development attempt caught a wrong
`canonical_model` field lookup in measured-stream reporting; its two errors
are preserved and do not count as behavioral counterfactual proof.

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
