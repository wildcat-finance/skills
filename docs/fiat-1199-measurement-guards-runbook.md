# Runbook: check a measurement-record token count and adapter identity digest, not only their echo

Derived from `.hexaemeron/study.md`, receipted at
`590121a8c8d4f71e3c9bd771e2f7e652dab9e6781b39f12d427c0a5c5cf0c3f1`. The design
is locked below and no step reopens it.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 32506d00c7ea9eb4e292ed3d2ba03512fdcf5f4d20b204570bd9d97e4f4876db
candidate | source-pinned-count-commitment
```

Two local command interfaces are registered. `tests/run_tests.py` is the root
suite the study names, and it already accepts the Elenchus report flag every
step below declares. `tests/prove_measurement_guards.py` is the resolver for the
design record's one pending conformance cell, `identity-cause-attribution`,
which blocks `integration`.

```command-interfaces
schema | protasis-command-interfaces/v1
tests/prove_measurement_guards.py | main | 6aef210ebe7c6a76cb228feb0ac94673a92676f088b0dfe6db1099d5f57168d2
tests/run_tests.py | report_target | aa577d63846e947944c04506ca9985b18bf3bac21c6d360bdbc18fd1f8360258
```

The resolver was written, run against this tree and digest-pinned before this
runbook was receipted, because a registered source that changes afterwards
refuses the gate with `registered-source-drift`. Step 1 commits those exact
bytes. No later step may edit either registered file, and a step that needs a
different resolver needs a dated runbook amendment carrying a replacement
registration fence.

On the tree this runbook is written against, the resolver exits 1 and reports
that a rendering change and a model change both reach
`WAI-E-ADAPTER.IDENTITY_CHANGED` at `$.profile.acquisition_sha256`. That is the
defect skills#1098 recorded as S3-R1-02. It exits 0 and writes its report once
Step 4 lands, which is why no step before Step 4 runs it.

## Step 1: Scaffold the run records and the pinned resolver

**Goal.** Commit the receipted study and runbook as the run's operator-facing
records, and commit the pre-pinned conformance resolver, changing no behaviour.

**Entry.** The run branch `fiat/1199-check-a-measurement-record-token-count-and`
at `9182d0adcb7e9a5330c259d9dc1e044b511711c2`, with the study receipted at
`590121a8c8d4f71e3c9bd771e2f7e652dab9e6781b39f12d427c0a5c5cf0c3f1` and the
design record at
`32506d00c7ea9eb4e292ed3d2ba03512fdcf5f4d20b204570bd9d97e4f4876db`.

**Exit.** The tracked study and runbook copies carry the same bytes as the
receipted artefacts under `.hexaemeron/`, and
`tests/prove_measurement_guards.py` is committed at
`6aef210ebe7c6a76cb228feb0ac94673a92676f088b0dfe6db1099d5f57168d2`, the digest
the registration fence above pins. No file under `scripts/` or
`tests/fixtures/` changes in this step, so every refusal the checker emits is
the one it emitted before. Prove it with:

```sh
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-1199-measurement-guards-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-1199-measurement-guards-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-1199-measurement-guards-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-1199-measurement-guards-runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py tests/prove_measurement_guards.py
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py tests/prove_measurement_guards.py
python3 tests/run_tests.py
```

**Files.** Create `docs/fiat-1199-measurement-guards-study.md`,
`docs/fiat-1199-measurement-guards-runbook.md` and
`tests/prove_measurement_guards.py`. The resolver's bytes are fixed: copy them
from the run worktree, do not re-author them, and confirm the digest before
committing. Change nothing else.

**Tests.** No new test. The root suite is the exit, and it must stay at its
entry count plus nothing: this step adds no `test_` file and changes no
assertion. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`

**Disciplines.** phylax: the step commits a new script under `tests/` that
reads committed evidence files and runs a child process, so the lint that
covers that directory is an exit here. ephoros: the same lint covers what the
resolver prints, which is the only record it leaves. metron: none, this step
changes no code the budget in study item 10 measures. elenchus: none, no
failure is in hand and no guard is claimed yet. hypomnema: none, the decision
record is Step 5's and writing it here would name a design the later steps have
not yet built.

## Step 2: Reach the active measurement path with a synthetic fixture

**Goal.** Build the in-tree `active` fixture the later guards need, and prove it
reaches `_validate_measurement_record` through `check_manifest` as a real tree
would.

**Entry.** Step 1's exit state.

**Exit.** A helper in the agent-instruction test module builds a temporary tree
carrying `model_evidence_status: active` with its own manifest, artefacts and
evidence records, reusing the committed `tokenizer-profile.json` and
`family-profiles.json` bytes verbatim because `TRUSTED_PROFILE_SHA256` pins
both. A test drives `check_manifest` over that tree and it is accepted at exit
zero, which is the statement that the tree reached the record validator rather
than the `disabled` short circuit at `scripts/agent_instruction.py:3484-3488`.
A second test holds the committed fixture on the `disabled` path: it is still
accepted, and an edit to either frozen record still refuses
`WAI-E-DIGEST.FROZEN`. No byte under `tests/fixtures/agent-instruction-v1/`
changes. Prove it with:

```sh
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py tests/test_agent_instruction.py
python3 tests/run_tests.py
```

**Files.** Change `tests/test_agent_instruction.py` and re-pin its
`agent_instruction.tests` row in `tests/promise_machine_coverage.json`. Change
no file under `tests/fixtures/`.

**Tests.** Two tests beside `MeasurementTests` at
`tests/test_agent_instruction.py:2499`, built the way `edited_token_count_tree`
at line 3731 builds its tree. One asserts the synthetic `active` tree is
accepted; one asserts the committed `disabled` tree is accepted and that an
edit to a frozen record still refuses `WAI-E-DIGEST.FROZEN` with its existing
node path. Both are green before and after this step's behaviour, because this
step adds no refusal. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`

**Disciplines.** phylax: the fixture is untrusted input the checker parses, and
study item 9 names that boundary first, so the lint over `tests/` is an exit.
ephoros: none, this step emits no new record and `run.summary` already carries
`model_evidence_status`. metron: none, test-only. elenchus: the fixture is what
every later guard fails against, so `synthetic-fixture-fidelity` in the risk
register is checked here rather than assumed later. hypomnema: none, no
decision is taken; the fixture is a test detail.

## Step 3: Anchor the recorded token counts in checker source

**Goal.** Compare the record's count vector against a constant the checker
carries, so an edit confined to the evidence tree cannot reach the comparand.

**Entry.** Step 2's exit state.

**Exit.** The checker carries a new plain data constant beside
`DISABLED_MODEL_EVIDENCE_SHA256` at line 37 and `TRUSTED_PROFILE_SHA256` at
line 51 of `scripts/agent_instruction.py`, holding the digest of the count
vector. On the `active` path
`_validate_measurement_record` compares the record's counts against it and
refuses when they disagree, naming the count field rather than
`$.evidence.measurement_record` as a whole. An `active` record with no anchor
refuses rather than being read as nothing to check. The constant is reachable
by no path `check` reads. The `disabled` path reaches none of this and behaves
exactly as it did at Step 2's exit. `docs/agent-instruction-language-v1.md` no
longer says the `active` path restores the existing full evidence validation,
because it no longer does. Prove it with:

```sh
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/agent-instruction-language-v1.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts/agent_instruction.py
python3 tests/run_tests.py
```

**Files.** Change `scripts/agent_instruction.py`,
`tests/test_agent_instruction.py`,
`docs/agent-instruction-language-v1.md`, and re-pin the
`agent_instruction.checker`, `agent_instruction.tests` and documentation rows in
`tests/promise_machine_coverage.json`. Leave `digest_neutral_projection`,
`_corpus_sha256` and every recorded span offset untouched: those are
skills#1192's surface and study item 3 makes them a non-goal.

**Tests.** One test per new refusal, asserting the exact code and node path and
never only that something refused. The self-consistent tamper of skills#1098's
S3-R2-05, a count moved with every recomputable field rebound, now refuses. An
`active` record whose counts match the anchor is accepted, so an honest
re-measurement plus its one reviewed constant still passes.
`test_a_consistent_token_count_edit_is_not_detected` at
`tests/test_agent_instruction.py:3805` is replaced in this step by a case
asserting the new refusal; it is not left to be found red. Its sibling
`test_an_edited_token_count_refuses_on_its_own` at line 3786 stays unchanged.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`

**Disciplines.** phylax: this step creates the trust boundary study item 9
names third, the checker's own source as an anchor, so the control that the
constant is plain data and unreachable from the tree is checked here. ephoros:
the refusal must answer the on-call question of whether the counts or the bytes
moved, and whether an anchor is stale or a record is tampered, so the code and
node path are part of the exit. metron: the budget in study item 10 applies to
this step and no other, because this is the comparison `check` now pays for on
every run. elenchus: every new condition refuses and each one carries a guard
that fails without the change. hypomnema: the decision is taken here but its
record is Step 5's, so that one draft can carry both this and Step 4's.

## Step 4: Separate the two adapter identity causes

**Goal.** Make a rendering change and a model change reach different refusals,
so a re-pin stops being the only response to either.

**Entry.** Step 3's exit state.

**Exit.** The identity check at line 1589 of the checker
reads the `MODEL_BLOB_RE` projection of the captured identity bytes before the
whole-text `acquisition_sha256` digest. A changed model blob set refuses
`WAI-E-TOKENIZER.MISMATCH` at `$.profile.model_blobs_sha256`; a rendering
change that leaves the blob set intact refuses
`WAI-E-ADAPTER.IDENTITY_CHANGED` at `$.profile.acquisition_sha256`. Both stay
reachable, the refusal detail register still enumerates every adapter refusal,
and no subprocess, argument or environment entry is added. The resolver now
exits zero and writes its report. Prove it with:

```sh
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts/agent_instruction.py
python3 tests/prove_measurement_guards.py --case identity-cause-attribution --report .hexaemeron/design/reports/source-pinned-count-commitment--identity-cause-attribution.json
python3 tests/run_tests.py
```

**Files.** Change `scripts/agent_instruction.py` and
`tests/test_agent_instruction.py`, and re-pin their rows in
`tests/promise_machine_coverage.json`. Change
`docs/agent-instruction-language-v1.md` only if it names either refusal code.
Do not edit `tests/prove_measurement_guards.py`: its digest is registered above
and any change to it refuses the gate.

**Tests.** One test for each of the two codes, driving the identity check over a
disposable stand-in runtime the way the adapter tests at
`tests/test_agent_instruction.py:2397` already do, and asserting the exact code
and node path. A third test holds the honest case accepted, so the split cannot
be satisfied by refusing everything. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`

**Disciplines.** phylax: the adapter subprocess and its stdout are study item
9's second boundary, and this step reads the same captured bytes with the same
regex that already runs, which is the claim the exit has to hold. ephoros: the
emitted code is what answers whether a contributor re-pins or has a different
runtime, so which code is emitted is the deliverable. metron: none, the
projection already runs on this path and the ordering change adds no work.
elenchus: both causes are refusals and each carries a guard that fails without
the change. hypomnema: this changes the meaning of an emitted code that other
readers depend on, which is the second decision Step 5's draft records.

## Step 5: Record the decision and bind the design bridge

**Goal.** Write the decision record the two guards need, and bind the selected
candidate to it through the study's design bridge.

**Entry.** Step 4's exit state.

**Exit.** An unnumbered draft decision record exists at
`docs/decisions/drafts/pin-measurement-counts-in-checker-source.md`, beside the
one already in that directory,
carrying both decisions: holding an evidence value in checker source, and
splitting the adapter identity check into two causes. It states plainly what
the guard establishes, that the counts have not moved since a human reviewed
them, and what it does not, that any count is what a tokenizer would return.
The study carries a closed three-row `design-bridge` block naming
`hypomnema-design-bridge/v1`, the selected candidate and that draft path, added
by `hexctl amend study` rather than by editing the file, and the tracked study
copy is refreshed to match the amended artefact. Prove it with:

```sh
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-1199-measurement-guards-study.md --design-evidence .hexaemeron/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions/drafts/pin-measurement-counts-in-checker-source.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/drafts/pin-measurement-counts-in-checker-source.md
python3 tests/run_tests.py
```

**Files.** Create
`docs/decisions/drafts/pin-measurement-counts-in-checker-source.md`. Change
`docs/fiat-1199-measurement-guards-study.md` to match the amended
`.hexaemeron/study.md`. Take no ADR number here: the draft is numbered at
assignment time, and study item 12 records that no existing record in
`docs/decisions/` governs `model_evidence_status`.

**Tests.** No new test. The bridge check and the record lint are the exit, and
the root suite must stay at Step 4's count. Two controller hazards belong to
whoever runs this step. A study amendment reverts every runbook step's amended
field to its baseline, so any runbook amendment taken in Steps 1 to 4 must be
reapplied after the amendment and before the next receipt. The amendment also
moves the study digest, which is why the tracked copy is refreshed in this same
step. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-5.json`

**Disciplines.** phylax: none, this step adds no input, no subprocess and no
dependency. ephoros: none, no record is emitted at runtime. metron: none, no
code changes. elenchus: none, no failure is in hand. hypomnema: this is the
step the discipline owns outright, and study item 12 defers the design bridge
to it by name, because the record the bridge points at does not exist until
here.

## Step 6: Demonstrate both guards on the demo path

**Goal.** Run the study's demo path and commit what it produced.

**Entry.** Step 5's exit state.

**Exit.** A demonstration record at
`docs/fiat-1199-measurement-guards-demonstration.md` carries the
resolver's report object and names, in plain terms, the two refusals a reader
would see and the one thing neither establishes: that a recorded count is what
a tokenizer would return. The resolver exits zero and writes
`.hexaemeron/design/reports/source-pinned-count-commitment--identity-cause-attribution.json`,
which is the report the design record's pending cell names and which
`done integrate` consumes at the `integration` transition. The root suite is
green. Prove it with:

```sh
python3 tests/prove_measurement_guards.py --case identity-cause-attribution --report .hexaemeron/design/reports/source-pinned-count-commitment--identity-cause-attribution.json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-1199-measurement-guards-demonstration.md
python3 tests/run_tests.py
```

**Files.** Create `docs/fiat-1199-measurement-guards-demonstration.md`. Change
nothing under `scripts/` or `tests/`: if this step needs a code change, an
earlier step's exit was wrong and belongs to that step.

**Tests.** No new test. The demo path is the exit. The resolver is not a
`unittest` case and the root suite does not collect it, so both commands run.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-6.json`

**Disciplines.** phylax: none, the demonstration record adds no boundary and
the resolver's own were checked at Step 1. ephoros: the demonstration record is
the operator-facing answer to both on-call questions in study item 8, so what
it names is the deliverable. metron: none, no performance claim is made here.
elenchus: none, no failure is in hand; the guards were proved in their own
steps. hypomnema: the demonstration record is a standing document and belongs
beside the draft decision record Step 5 wrote, not inside it.

### Amendment -- 2026-09-18

```command-interfaces
schema | protasis-command-interfaces/v1
tests/prove_measurement_guards.py | main | ecc983e8b85627a2f962144edadbf5a61fa11025baacd60d7c4fbf17336a30ef
tests/run_tests.py | report_target | aa577d63846e947944c04506ca9985b18bf3bac21c6d360bdbc18fd1f8360258
```

**What changed.** Complete replacement Exit: The tracked study and runbook
copies carry the same bytes as the receipted artefacts under `.hexaemeron/`,
and `tests/prove_measurement_guards.py` is committed at
`ecc983e8b85627a2f962144edadbf5a61fa11025baacd60d7c4fbf17336a30ef`, the digest
the registration fence above pins. No file under `scripts/` or
`tests/fixtures/` changes in this step, so every refusal the checker emits is
the one it emitted before. Prove it with:

```sh
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-1199-measurement-guards-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-1199-measurement-guards-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-1199-measurement-guards-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-1199-measurement-guards-runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py tests/prove_measurement_guards.py
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py tests/prove_measurement_guards.py
python3 tests/run_tests.py
```

**Why.** The registered resolver's original bytes failed this repository's own
structural scratch-quiescence check once tracked:
`tests/test_scratch_quiescence.py` requires a `dir=` argument on a
`tempfile.mkstemp` construction to sit inside a function named
`scratch_directory`, and `write_report`'s atomic-write call did not. The
violation is invisible to a plain suite run against an untracked copy, because
that check scans `git ls-files`, and only became visible once the file was
staged for Step 1's commit. The fix extracts the one `mkstemp(dir=...)` call
into a function named `scratch_directory`, changing no behaviour: the resolver
produces byte-identical output before and after, re-verified by running it
against this tree. The digest changes because the bytes do; the
`command-interfaces` fence above carries the corrected value and Step 1's Exit
field is replaced to match. `tests/run_tests.py`'s own registration is
unchanged, because that file was not touched.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds.
