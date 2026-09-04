# Runbook: make a bound instruction document editable off one machine

Derived from the receipted study. Six steps, in dependency order. Each is one
pull request, green at both ends, and assumes every earlier step's exit state
and nothing else.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 969dbc4a8d8ce31b34e3b90662c3c75c8336d45bccc969de01dc618b702275f4
candidate | digest-neutral-corpus
```

## Correction to the receipted study

The study defers reissuing `parity.json`, saying the selected design makes it
unnecessary. That is right for every later out-of-span edit and wrong for the
landing change. `scripts/agent_instruction.py:3258-3260` compares both
`measurement.json` and `parity.json` against `_corpus_sha256(manifest)` and
refuses each with `WAI-E-DIGEST.CORPUS`. The subject that function digests
includes `fixtures`, which carries every bound source's whole-file digest, so
switching the subject moves the digest once and staled both records once.

Step 3 therefore reissues both, and needs `gpt-oss:120b` at 65,369,799,840
bytes for `measure` plus `qwen3.8-27b-aeon:q4_k_m` for the second parity
family. Both are installed locally. The user accepted that cost before this
runbook was written, and holds the machine quiet for step 3 alone.

The selection is unchanged. Every other candidate pays this same parity
reissue on every bound-source edit rather than once, which is why the gate
`reissue-model-bytes` removed two of them. The correction raises the landing
cost the criterion `landing-model-measure-runs` recorded, not the ranking.
This correction is repeated into the study by `hexctl amend study` once step 1
is active, because study amendment is refused outside the steps phase.

## Runner contract

Every step uses one Elenchus runner contract, because the repository has one
root suite and one report format:

```text
command | python3 tests/run_tests.py --elenchus-report {report}
format  | elenchus.unittest.v1
report  | .hexaemeron/elenchus/step-<N>.json
```

Warden owns those three inputs for any fix it makes, and may not substitute a
nearby suite or infer a command from `Files`.

## Step 1: Characterise the refusal and commit the spec

**Goal.** Pin today's behaviour as a test before anything changes it, and land
the study and this runbook in the repository.
**Entry.** `fiat/1098-make-a-bound-instruction-document-editable` at
`bacb34c0d49a83dea0c4463a61b2cf1525fec60b`.
**Exit.** `tests/test_agent_instruction_corpus.py` proves, against a copied
fixture tree and never the live one, that an out-of-span edit to a bound source
with every mechanical pass applied refuses `WAI-E-DIGEST.CORPUS` at
`$.evidence.measurement_record`, that the same edit also stales
`$.evidence.parity_record`, and that an in-span edit refuses as well.
`scripts/prove_agent_instruction_reconciliation.py` exists with its `offline`,
`span-shift` and `selftest` subcommands, each writing a closed
`protasis-design-report/v1` object; `selftest` exits 0. `python3
tests/run_tests.py` exits 0.
**Files.** `docs/agent-instruction-machine-binding/study.md`,
`docs/agent-instruction-machine-binding/runbook.md`,
`tests/test_agent_instruction_corpus.py`,
`scripts/prove_agent_instruction_reconciliation.py`.
**Tests.** New module, six tests expected: out-of-span measurement refusal,
out-of-span parity refusal, in-span refusal, mechanical-pass completeness,
fixture-copy isolation, and prover self-test. Runner contract above.
**Disciplines.** phylax: the prover copies a fixture tree, writes inside it and
shells out to the checker, so its path confinement and subprocess boundary are
this step's new surface. ephoros: none, nothing here runs unattended. metron:
none, no performance claim is made. elenchus: the runner contract above carries
any fix. hypomnema: none, the decision record is due at step 3 with the change
it describes.

## Step 2: Add the digest-neutral projection without switching the subject

**Goal.** Introduce the measured projection and its tests while
`_corpus_sha256` still digests today's subject, so the change is reviewable
before any evidence record moves.
**Entry.** Step 1's branch at its exit state.
**Exit.** `scripts/agent_instruction.py` exposes the projection, which replaces
every bound whole-file source digest with one fixed 64-character placeholder
and changes nothing else. New tests prove it is a pure projection: idempotent,
byte-identical on an unmodified fixture except at the placeholder positions, and
unchanged by an out-of-span edit. `agent_instruction.py check` still exits 0
on the untouched fixture, and no file under
`tests/fixtures/agent-instruction-v1/evidence/` changes in this step. `python3
tests/run_tests.py` exits 0.
**Files.** `scripts/agent_instruction.py`, `tests/test_agent_instruction.py`.
**Tests.** Extend `test_agent_instruction.py` with projection tests, four
expected. Runner contract above.
**Disciplines.** phylax: none, the projection opens no boundary and reads no
new input. ephoros: none. metron: none, the projection is not a speed change.
elenchus: the runner contract above. hypomnema: none, step 3 records the
decision.

## Step 3: Switch the corpus subject and reissue both evidence records

**Goal.** Stop the corpus digest moving when a bound source is edited outside
its reviewed span, and
honestly reissue the two evidence records that binding stales.

**This is the only step that consults a model.** It runs `measure` once and
`parity` once, against the single-run budget the study records.

**Entry.** Step 2's branch at its exit state, with `127.0.0.1:11434` free and
nothing else serving it.
**Exit.** `_corpus_sha256` digests the reviewed span digest and the projection
digests in place of the whole-file digest and the raw artefact digests, and the
manifest still binds the whole-file digest for review. `ollama ps` lists
`gpt-oss:120b` as loaded before the `measure` call, because a cold 65 GB load
exceeds the profile's own `--max-time 170`. `measure` and `parity` each run once
and their outputs are written unedited; no count or date is hand-written.
`measurement.json` and `parity.json` carry the new `corpus_sha256` and each
names the exact projection it measured. `agent_instruction.py check` exits 0.
The observed `delta_tokens` is recorded as observed, not asserted in advance.
`python3 tests/run_tests.py` exits 0, and the port's state at exit is recorded
beside the result.
**Files.** `scripts/agent_instruction.py`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json`,
`tests/promise_machine_coverage.json`,
`docs/decisions/ADR-<next>-digest-neutral-measured-corpus.md`.
**Tests.** Extend `test_agent_instruction.py`: the corpus digest is unchanged by
an out-of-span edit, still moves on an in-span edit, and
`test_stale_measurement_report_refuses` and `test_stale_parity_report_refuses`
both still fail on a stale record. Three tests expected, none deleted or
weakened. Runner contract above.
**Disciplines.** phylax: the step invokes a pinned loopback adapter and a local
model, so the executable pins, the port and the adapter's output caps are its
surface. ephoros: none, the measurement is one bounded call rather than
something that runs unattended. metron: none, the token delta is evidence about
the instruction language and not a performance claim about this code.
elenchus: `WAI-E-MEASURE.NON_NEGATIVE_DELTA` is the one refusal that can end
the delivery, and there is no second run to fall back on; work it to its cause
rather than re-running. hypomnema: the corpus-subject change is expensive to
reverse and owes the ADR named in `Files`.

## Step 4: Resolve the two pending conformance gates

**Goal.** Produce the evidence the design record schedules at `integration`,
using the exact resolver commands it names.
**Entry.** Step 3's branch at its exit state.
**Exit.** Both resolvers exit 0 and write closed `protasis-design-report/v1`
objects at the paths the record names:
`python3 scripts/prove_agent_instruction_reconciliation.py offline --candidate
digest-neutral-corpus --report
.hexaemeron/reports/digest-neutral-corpus-offline-reconciliation-green.json`
and the same with `span-shift` and its own report path. The offline report
proves a bound-source edit reconciles with no model consulted; the span-shift
report covers an edit before a reviewed span start as well as after it, since
only the first moves the recorded binding offsets. `python3 tests/run_tests.py`
exits 0.
**Files.** `scripts/prove_agent_instruction_reconciliation.py`,
`.hexaemeron/reports/digest-neutral-corpus-offline-reconciliation-green.json`,
`.hexaemeron/reports/digest-neutral-corpus-span-shift-regression.json`,
`tests/test_agent_instruction_corpus.py`.
**Tests.** Extend the step 1 module with the before-span offset case, which
#1098's third acceptance check names and which no test covers today. Two tests
expected. Runner contract above.
**Disciplines.** phylax: the provers write reports and copy fixture trees, so
their confinement is rechecked here. ephoros: none. metron: none. elenchus: the
runner contract above. hypomnema: none.

## Step 5: Close the guarantee and the refusal-detail hole

**Goal.** Make two things enforced that are currently true only by accident.
**Entry.** Step 4's branch at its exit state.
**Exit.** A test fails if `measurement.json` records a token count or an
`observed_on` date for bytes no tokenizer read, which is #1098's fourth
acceptance check and holds today only because nobody can re-measure. Every
adapter refusal a contributor can actually reach names the tokenizer and the
machine: PR #1100 attached that guidance to the two `EXECUTABLE_CHANGED` sites
only, so a client executable present at another path returns a bare
`WAI-E-ADAPTER.EXECUTABLE` and the profile holder a bare
`WAI-E-ADAPTER.UNAVAILABLE`. Both now carry the same detail, closing the
register item `refusal-detail-coverage`. `python3 tests/run_tests.py` exits 0.
**Files.** `scripts/agent_instruction.py`, `tests/test_agent_instruction.py`.
**Tests.** Four expected: the unmeasured-count guarantee, the unmeasured-date
guarantee, and one per newly detailed refusal site. Runner contract above.
**Disciplines.** phylax: the refusal text must not leak an absolute path or an
account name from the environment. ephoros: none. metron: none. elenchus: the
runner contract above. hypomnema: none.

## Step 6: Demonstrate the offline reconciliation

**Goal.** Run the demo path from the study's problem statement and show that a
contributor with no model reconciles a bound-source edit.
**Entry.** Step 5's branch at its exit state.
**Exit.** The study's four-command demo path runs, its third and fourth
commands exit 0, and no model is consulted: verified by asserting the run makes
no loopback call rather than by observing that none happened.
`docs/agent-instruction-machine-binding/demo.md` records the exact commands and
their observed output. `python3 tests/run_tests.py` exits 0.
**Files.** `docs/agent-instruction-machine-binding/demo.md`,
`tests/test_agent_instruction_corpus.py`.
**Tests.** One test asserting the offline path opens no socket to the adapter
port. Runner contract above.
**Disciplines.** phylax: the demo must not require or accept a credential.
ephoros: none. metron: none. elenchus: the runner contract above. hypomnema:
the demo document is the record a later reader starts from.
