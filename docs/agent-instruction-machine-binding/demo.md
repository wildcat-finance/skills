# Reconciling a bound instruction document with no model

Three instruction documents are bound into `tests/fixtures/agent-instruction-v1`
by whole-file SHA-256. Before skills#1098, editing any of them moved the corpus
digest, invalidated both committed evidence records, and only
`agent_instruction.py measure` and `parity` could reissue those records
honestly. Both run through a loopback adapter pinned to one macOS install and
one 65 GB local model, so the cheapest correction to a bound document cost a
measurement run that most contributors cannot perform at all.

This is that path, run and recorded. It is the study's demo path unchanged, and
the output below is what it printed rather than what it was expected to print.

## The four commands

Run from the repository root. Nothing here needs a network, a model, or a
credential.

```bash
printf '\n<!-- demo -->\n' >> plugins/hexaemeron/skills/fiat/SKILL.md
python3 scripts/prove_agent_instruction_reconciliation.py reconcile
python3 scripts/agent_instruction.py check \
  --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 -m unittest discover -s tests
```

The first command is the edit. It appends a comment after the end of the
reviewed span, which is the placement this delivery makes reconcilable; see
"What refuses" below for the other one. The second performs the reconciliation.
The third and fourth are the gates, and both exit 0.

## What it printed

Observed at `ea07263b`, on a checkout with the Ollama the tokenizer
profile pins installed but never contacted.

### 1. The edit

```text
exit 0
```

`plugins/hexaemeron/skills/fiat/SKILL.md` goes from 72,713 bytes to 72,728. Its
whole-file digest moves from `809f4111…` to `7d9ab620…`. Its reviewed span,
bytes 18445 to 22773, is untouched.

### 2. The reconciliation

```json
{
  "applied": [
    "manifest-source",
    "model",
    "source-spans",
    "compact",
    "manifest-artifacts",
    "coverage-register"
  ],
  "coverage_rebound": [
    "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai",
    "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json",
    "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json",
    "tests/fixtures/agent-instruction-v1/manifest.json"
  ],
  "outcome": "reconciled",
  "source": "plugins/hexaemeron/skills/fiat/SKILL.md",
  "source_sha256": {
    "from": "809f4111662e3168c29e3fb65868fd88e086e5cd10762f95f5c0be6df314199c",
    "to": "7d9ab6209ba0e2260b3c47b3c020f60b2caa188b13b27241ce09996a0b1bb737"
  },
  "written": [
    "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai",
    "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json",
    "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json",
    "tests/fixtures/agent-instruction-v1/manifest.json",
    "tests/promise_machine_coverage.json"
  ]
}
exit 0
```

Six passes. The first five are the ones `agent_instruction.py check` can see:
the manifest's record of the source digest, the same digest where `model.json`
and `source-spans.json` embed it, the compact document regenerated from the
model rather than substituted in, and the manifest's record of all three
artefact digests. The sixth is the one it cannot: `check` never reads
`tests/promise_machine_coverage.json`, so the register is rebound here and
`tests/test_agent_instruction.py` is what would otherwise catch it. That is why
the demo ends in the test suite and not in the checker.

Neither evidence record is written. `measurement.json` and `parity.json` are
untouched, because ADR-076's digest-neutral projection means the corpus digest
they carry no longer moves for an edit that leaves the reviewed span alone.
That is the whole difference this delivery makes.

### 3. The checker

```text
exit 0
```

```json
{"binding_count":15,"code":"WAI-OK","event":"run.summary","failed":0,"fixture_count":3,"outcome":"accepted","passed":20,"question_count":9,"refused":0,"roundtrip_count":3,"unknown":0,"mutation_count":14}
```

### 4. The suite

```text
exit 0
Ran 1154 tests in 113.512s
OK (skipped=2)
```

The same clone, before the edit and with no reconciliation, runs the same
command to `Ran 1154 tests in 122.434s / OK (skipped=2)`. Recorded as a control,
because a suite that was green either way would say nothing about the
reconciliation. The count is identical: the reconciliation rebinds digests and
adds no test.

### Run this in a clone, not in an export

`git archive` the branch into a directory and the same four commands end at
`FAILED (failures=4, errors=6)`. None of the ten is caused by the edit or by the
reconciliation. They are checks that read the repository's own Git state or its
ignored files, which an export does not carry:
`test_shipped_prose_lints`, `test_scratch_quiescence`,
`test_run_observation_capture`, `test_skills_sh_package`,
`test_boundary_currency`, `test_dead_code` and
`test_portable_promise_machine_package_is_current`. The same ten fail in an
export with no edit at all.

## What refuses, and why that is the right answer

`reconcile` handles an edit that leaves the reviewed span's bytes where they
were. Anything else refuses, and the refusal names both causes and both
remedies without guessing between them:

```text
plugins/hexaemeron/skills/fiat/SKILL.md is off its recorded reviewed-span
digest at the recorded offsets 18445-22773, so this edit either changed the
reviewed bytes or moved them. Neither is reconcilable here. Changed reviewed
bytes are what the recorded token counts are counts of, and only
agent_instruction.py measure can reissue those counts, on the machine the
tokenizer profile pins. Moved reviewed bytes need their offsets re-derived
from the pre-edit source, which this tree no longer holds; see
wildcat-finance/skills#1192
```

It does not try to tell the two apart. The manifest records the reviewed span's
digest and not its bytes, so a tree already carrying the edit gives nothing to
search for, and distinguishing "moved" from "changed" would be a guess
presented as a diagnosis.

An edit inside the reviewed span *should* refuse. Those bytes are what the
recorded token counts are counts of, so a mechanical pass that made the fixture
agree with itself again would be making the measurement record say something no
tokenizer measured.

An edit before the reviewed span is a different case, and the honest answer
today is that this command cannot reach it. Closing it means storing binding
offsets relative to the span start, which changes an artefact schema and the
codec ADR-062 settled. That is filed as
[skills#1192](https://github.com/wildcat-finance/skills/issues/1192) with its
own decision record. `prove_agent_instruction_reconciliation.py span-shift`
covers the placement in a throwaway copy, which is where the pre-edit bytes
still exist.

## No model, asserted rather than observed

`test_reconcile_opens_no_socket_and_runs_no_model` in
`tests/test_agent_instruction_corpus.py` puts two guards around a reconciliation
and fails if either fires. An `AF_INET` or `AF_INET6` socket constructed during
the run fails the case. Every subprocess the command starts is recorded and
checked, and the only checker verb reachable is `format`, so `measure` and
`parity` cannot arrive behind a passing reconciliation.

That is an assertion about the code path rather than an observation of one run.
A run where nothing happened to contact a model is not evidence that the next
one will not.

The command takes one argument, `--root`, and reads no credential. The checker
subprocess is given a constructed environment rather than the ambient one, so
a token in the caller's environment does not reach it.

## What this does not establish

That the delivery is green in CI. This is a local run.

That a `measure` run would clear a before-span refusal. It was not run here and
cannot be run off the machine the tokenizer profile pins, so ADR-076's sentence
on that point rests on a reading of `_validate_measurement_record`.

That the other two bound documents behave identically. The prover pins its
subject to `fiat-study-runbook-phase`, and this demo edits that one.
`plugins/horos/skills/horos/SKILL.md` and `PROMISE_MACHINE.md` are bound by the
same manifest and were not edited here.
