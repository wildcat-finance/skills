# Study: check a measurement-record token count and adapter identity digest, not only their echo

Issue: https://github.com/wildcat-finance/skills/issues/1199

Assuming, unless corrected:

1. The interpreter in `.python-version`, 3.14.6, with stdlib `unittest`; the run
   worktree reports `Python 3.14.6`.
2. No tokenizer, no model, no socket to `127.0.0.1:11434` and no pinned host at
   any point in this delivery. The issue's own "What this does not settle"
   section rules out a remedy that needs the pinned machine on every check.
3. The committed fixture keeps `model_evidence_status: disabled` and every byte
   under `tests/fixtures/agent-instruction-v1/` is unchanged by this delivery.
   The `active` path is exercised through a synthetic fixture built in-tree.
4. `measure` and `parity` are not re-issued here. The frozen historical records
   stay frozen, and re-enabling them is other, unrelated work.
5. skills#1192 owns the recorded span offsets, `digest_neutral_projection` and
   `_corpus_sha256`. This delivery touches none of them.

I will proceed on these unless corrected.

## 1. Problem statement

Two guards in `scripts/agent_instruction.py` report green on evidence they
cannot see, and one number that can end a delivery rests on neither.

**The token count is compared to itself.** `_measurement_material` at
`scripts/agent_instruction.py:2938` reads the recorded count at line 2958 and
puts that same value into the object it compares against at line 2967:

```python
expected = {
    "sha256": _digest(expected_bytes),
    "bytes": len(expected_bytes),
    "projection": projection,
    "tokens": token_count,
}
```

`sha256` and `bytes` are computed by the checker from the projected stream.
`tokens` is not. The function's own docstring says so. The digest beside it
covers the stream and not the count, so a hand-edited count is invisible to it.

**The adapter identity digests rendered text.** `_verify_profile_identity` at
`scripts/agent_instruction.py:1589` digests the whole rendered stdout of the
identity command at line 1650 and refuses `WAI-E-ADAPTER.IDENTITY_CHANGED`. A
cosmetic renderer difference and a genuine runtime swap both change those bytes,
and a hand re-pin is the only response available to either.

**Who this is for.** A Wildcat contributor who reviews or re-issues the
agent-instruction evidence records, and anyone who reads
`WAI-E-MEASURE.NON_NEGATIVE_DELTA` at `scripts/agent_instruction.py:3215` as a
gate that can end a delivery. Today that refusal rests on the run that produced
the record having been honest.

**What a working prototype means here.** Two behaviours, each provable by a
command on a machine with no tokenizer:

1. A measurement record whose token count is edited by hand, with every field
   the editor can recompute rebound, is refused under `model_evidence_status:
   active`, and the refusal names the count.
2. A change to the identity command's rendering that leaves the model-blob set
   unchanged refuses under a different code from a change to the blob set, or
   the refusal states which of the two it cannot distinguish.

**The demo path.** The last step runs, from the repository root:

```bash
python3 tests/prove_measurement_guards.py --case identity-cause-attribution \
  --report .hexaemeron/design/reports/source-pinned-count-commitment--identity-cause-attribution.json
python3 tests/run_tests.py
```

The first command is also the resolver for the record's one pending conformance
cell. The second is the root suite; three lints are not CI and are not it.

## 2. Prior art

### In this repository

- `scripts/agent_instruction.py:2938-2973`, `_measurement_material`. The
  tautology, re-verified by reading on this tree.
- `scripts/agent_instruction.py:2976-3215`, `_validate_measurement_record`. It
  recomputes `one_document`, `totals`, `amortised` and every
  `measurement.result` event from `documents[*]`, which is why a count moved
  alone is caught and a count moved consistently is not.
- `scripts/agent_instruction.py:3484-3488`. When `model_evidence_status` is
  `disabled` the six evidence files are checked against
  `DISABLED_MODEL_EVIDENCE_SHA256` at line 37 and the function returns.
  `_validate_measurement_record` is never reached, so the tautology is live code
  that the shipped fixture does not run.
- `scripts/agent_instruction.py:51-54`, `TRUSTED_PROFILE_SHA256`. The repository
  already anchors two evidence files to constants in reviewed checker source.
  This is the shape the selected design reuses; it is not new here.
- `scripts/agent_instruction.py:156` and `1656-1668`. `MODEL_BLOB_RE` already
  extracts a structured model-blob set out of the same rendered identity bytes
  the whole-text digest covers, and compares it to `model_blobs_sha256` and
  `vocabulary_sha256`. The structured projection the adapter half needs exists
  and is already checked; what is missing is that it is checked after, and is
  masked by, the whole-text digest.
- `tests/test_agent_instruction.py:3731`, `edited_token_count_tree`, with
  `test_an_edited_token_count_refuses_on_its_own` at line 3786 and
  `test_a_consistent_token_count_edit_is_not_detected` at line 3805. Both assert
  `WAI-E-DIGEST.FROZEN` today. Re-run on this tree:
  `python3 -m unittest tests.test_agent_instruction.MeasurementTests` is 38 of
  38, OK. The second test's docstring still describes a silent pass; what it now
  asserts is the frozen-digest refusal of the `disabled` path catching any edit,
  which is not the tautology being refused. Its own docstring says it "is
  expected to fail the moment the counts are bound to the run that produced
  them", and this delivery is that moment.
- `docs/agent-instruction-language-v1.md`, sections "Measurement and parity
  evidence" and "Frozen historical token measurement". They record that
  `disabled` means the bound measurement and parity bytes are a frozen
  historical record of an earlier corpus, and that changing the status to
  `active` "requires separate authority and newly issued evidence, neither of
  which this corpus claims".
- `tests/promise_machine_coverage.json`. Thirty rows bind this surface by
  SHA-256, including `agent_instruction.checker` for
  `scripts/agent_instruction.py`, `agent_instruction.tests` for
  `tests/test_agent_instruction.py`, `agent_instruction.documentation[0]` for
  `docs/agent-instruction-language-v1.md` and `agent_instruction.evidence[2]`
  for `tests/fixtures/agent-instruction-v1/evidence/measurement.json` at
  `e5714268b231ec6d2d71de61297ae02f9a6c76ba7cda8bbabdf6039ac2054921`, which is
  the same value `DISABLED_MODEL_EVIDENCE_SHA256` carries. Every file this
  delivery edits re-pins its row.

### Merged pull requests read

The last two merges touching `scripts/agent_instruction.py` are
https://github.com/wildcat-finance/skills/pull/1638, "Require known-failure
guards before implementation", merged 2026-09-14 and carrying an
`ADR-Assignment` trailer that landed ADR-098; and the
2026-08-31 merge "merge: sync issue 909 with main". Neither carried forward work
on the measurement guards. The unfinished work of the run that produced this
issue is in that run's audit record, read below, and in skills#1192.

### Audit records read

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` was
run from the target root and exits 0; every listed pair reports
`committed=match`. A verified synopsis is therefore an admitted reading view.
The in-scope sources, and which view was actually read:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/rounds/fiat-1098-make-a-bound-instruction-document-editable.md` | the authoritative source, read directly | the two findings this issue disposes are here; their full rows and every `Leads not pursued` line were read from the source, not the synopsis |
| `audit/rounds/fiat-1098-make-a-bound-instruction-document-editable.synopsis.md` | read | `source_sha256=f10c56f2f7c8defd4bcea98b2291e2f74c8f85416ee9cb5f341bc7ad83c79442`, `h2_count=14` |
| `audit/AUDIT.md` and `audit/AUDIT_SYNOPSIS.md` | the synopsis, grepped for this surface | the whole-set check exits 0; no row in it names `acquisition_sha256`, `_measurement_material`, `NON_NEGATIVE_DELTA` or `IDENTITY_CHANGED` |

The #1098 record carries 50 findings. Its final statuses: 22 `fixed`, 6
`closed`, 4 `accepted`, 18 `open`. The `open` set is S1-R1-01, S1-R1-02, S1-R1-03, S1-R1-08,
S1-R2-01, S2-R1-07, S2-R2-03, S2-R3-02, S3-R1-02, S3-R2-05, S4-R1-01, S4-R1-02,
S4-R1-03, S4-R1-06, S5-R1-02, S5-R1-03, S6-R1-02 and S6-R1-03. Three of those
are in scope here and the rest stay with skills#1098 by its own carryover.

- **S3-R2-05, high, open.** Last recorded at
  `scripts/agent_instruction.py:2917-2951, tests/test_agent_instruction.py:3583`.
  "`_measurement_material` builds `expected` with `"tokens": token_count`, where
  `token_count` came from the supplied record, so the comparison is tautological
  for that one field." Demonstrated in that round: `delta_tokens` moves from
  `-165` to `-170` and `check` exits 0 with no refusal. **Carried forward as the
  content of this study.** The line numbers have moved; the code has not.
- **S3-R1-02, medium, open.** `acquisition_sha256` still digests rendered text.
  The round verified the mechanism from the machine: the model layer blobs did
  not move, `/Applications/Ollama.app/Contents/Resources/ollama` still hashed to
  `eee609f0a6da58b978d453e0385fd0e3496e6cf319c639875669b51cb4277d2d`, and what
  changed was the server process that rendered the identity bytes. "No field was
  split and nothing distinguishes the two causes." **Carried forward**, and that
  observation is the evidence that the blob set is the part that survives a
  rendering change.
- **S4-R1-01, high, open.** Disposed to https://github.com/wildcat-finance/skills/issues/1192.
  **Refused by name here**: its surface is the recorded span offsets and the two
  measured streams, and section 3 makes it a non-goal.

Three `Leads not pursued` entries from step 3 round 2 are directly on this
question, and each is answered:

1. "whether the two evidence records should carry an adapter-side signature over
   the counts, which is the only shape that would close S3-R2-05 without a
   second model run and which nobody has costed." **Costed here and not
   selected.** The lead assumes a signer. Ollama signs nothing, and a digest the
   editor can recompute is not a signature. The measured result is in the design
   record: the nearest constructible form, `fold-into-stream-digest`, fails
   `comparand-independence`. What does close it is an anchor the editor cannot
   reach, which is a constant in checker source rather than a signature.
2. "whether `acquisition_sha256` should be split into the part that identifies
   the model and the part that is rendering, so a re-pin stops being the only
   response to either, noted here because S3-R1-02's remedy may be a narrower
   field rather than an extra one." **Selected.** No new profile field is
   needed: `MODEL_BLOB_RE` already extracts the identifying part.
3. "whether the audit-record schema should carry a `Corrections` field."
   **Stated as still open and out of scope.** It is a Fiat schema question, not
   a measurement question.

### Outside this repository

No external standard was found that covers validating a model-produced count
without the model. What the search did settle is that the general shape is
ordinary: a value that cannot be recomputed is held against a trust anchor
outside the data being validated. This repository already does that twice, at
`scripts/agent_instruction.py:37` and `scripts/agent_instruction.py:51`, so the
selected design adds no new idea, only a third use of an existing one.

## 3. Constraints and non-goals

**Starting ref.** The run branch `fiat/1199-check-a-measurement-record-token-count-and`
at `9182d0adcb7e9a5330c259d9dc1e044b511711c2`, which is the current `main` tip
recorded in this worktree. The controller's brief names `fix/1199-measurement-guards`
as the base ref; both name the same commit content in this worktree.

**Toolchain.** Python 3.14.6 from `.python-version`, stdlib `unittest`, no new
dependency. The root suite is `python3 tests/run_tests.py`.

**Measured on this tree, and binding on the runbook.** Flipping the committed
fixture to `model_evidence_status: active` in a scratch copy refuses
`WAI-E-DIGEST.CORPUS` at `$.evidence.measurement_record` before
`_validate_measurement_record` is reached. The frozen record describes an
earlier corpus. Comparing it to today's projected streams:

| Fixture | source | canonical_model | compact |
| --- | --- | --- | --- |
| `fiat-study-runbook-phase` | recorded 4,328 bytes, actual 10,952, digest differs | recorded 3,110, actual 3,885, digest differs | recorded 1,924, actual 2,428, digest differs |
| `horos-boundary-check` | 1,018, matches | 2,491, matches | 1,814, matches |
| `promise-machine-router-selection` | 5,824, matches | 2,968, matches | 2,331, matches |

So the `active` path cannot be exercised by flipping the committed fixture, in
this delivery or any other, until the record is re-issued. The guards must be
built against a synthetic in-tree fixture that carries
`model_evidence_status: active` and its own manifest, artefacts and evidence
records. That fixture is constructible entirely offline, because the defect
under repair is exactly that nothing checks the counts against a model: a
synthetic record may carry any self-consistent counts. It must reuse the
committed `tokenizer-profile.json` and `family-profiles.json` bytes verbatim,
because `TRUSTED_PROFILE_SHA256` pins both.

**Always.** The root suite `python3 tests/run_tests.py` before a commit. The
imprimatur lint on every shipped document. Every
`tests/promise_machine_coverage.json` row whose file the step changed re-pinned
in that same step.

**Ask first.** Adding a dependency. Changing `model_evidence_status` on a
committed fixture. Changing any admitted refusal code's meaning rather than
adding one. Widening what `check` is allowed to execute.

**Never.** Run `measure` or `parity`, open a socket, or consult a model. Edit a
byte under `tests/fixtures/agent-instruction-v1/`. Re-issue or re-pin the frozen
historical measurement or parity record. Delete a failing test to make the suite
pass. Claim a command ran when it did not.

**Non-goals.**

- Recomputing counts at check time. The issue rules it out, and the design
  record records the measured reason: `recompute-at-check` fails
  `offline-checkability`.
- Re-enabling `model_evidence_status: active` on the committed fixture. That
  needs a fresh `measure` and `parity` pair on the one pinned host, which is
  separate, unrelated work. This delivery states plainly that the committed
  fixture will exercise the fixed logic only once that lands.
- skills#1192's surface: the recorded span offsets, `digest_neutral_projection`
  and `_corpus_sha256`. Re-read on 2026-09-17; that issue is still open with no
  comments and was last updated 2026-09-13. Its remedy stores binding offsets
  relative to the reviewed span start. This delivery must leave every one of
  those untouched so that remedy still applies unchanged.
- skills#1520, the coverage-field red on `main`, closed 2026-09-12. It is not
  this delivery's to fix and no result here is reported against it.
- The `Corrections` field on the audit-record schema, raised three times in
  skills#1098 and still open. Out of scope.

**One reading recorded rather than guessed.** The run carries the
`protasis-success-criteria-execution/v1` contract, whose optional
`success-criteria` fence binds each declared criterion to an exact runbook step
number and a byte-exact Exit command string. The runbook does not exist, so any
step number written here would be a guess, and a wrong guess refuses
`done runbook` and forces a study amendment. The fence is documented as optional
and its absence is a valid no-criteria run, so it is omitted deliberately. Each
success criterion below names its proving command in prose instead.

## 4. Design options

Four constructions were built as rules and measured. The prose explains them;
the selection is made by `.hexaemeron/design-evidence.json`, not here.

1. **`recompute-at-check`.** Recompute every count with the pinned tokenizer at
   check time. It is the only construction that establishes the counts are
   *correct*. Its trade is that `check` stops working anywhere but the pinned
   host, which is the problem skills#1098 exists to work around.
2. **`fold-into-stream-digest`.** Extend the recorded per-stream digest so it
   covers the count beside it. This is the construction the issue's shape
   suggests, and it does not work. The checker computes that digest from the
   stream it read and the count the record carried, so the comparand still
   depends on the field under examination: the tautology moves one level up
   rather than closing. An editor who rebinds the manifest rebinds this too, and
   the audit's own demonstration rebinds the manifest. Its trade is that it buys
   nothing beyond the derived-field arithmetic that already catches a count
   moved alone.
3. **`source-pinned-count-commitment`.** Hold the digest of the record's count
   vector as a constant in reviewed checker source, beside
   `DISABLED_MODEL_EVIDENCE_SHA256` and `TRUSTED_PROFILE_SHA256`, and compare
   against it. The comparand is then something the checker carries and the
   record does not, so editing the evidence tree cannot reach it. Its trade is
   stated plainly in section 6: this establishes that the counts have not moved
   since a human reviewed them, not that they are right. An honest re-measure
   costs one reviewed constant. For the adapter half, the same construction
   checks the `MODEL_BLOB_RE` projection first and the whole-text digest second,
   under its own code.
4. **`token-stream-witness`.** Carry the per-stream token-id sequence and
   recompute each count as its length. It raises the cost of a tamper and does
   not close it: the checker cannot decode those ids without the vocabulary
   blob, which is not in the repository, so an editor shortens the sequence and
   rebinds its digest. Its trade is 22,098 bytes added to committed artefacts
   for a guard that still fails the tamper.

The measured matrix, from `.hexaemeron/design-evidence.json` and the twenty
reports under `.hexaemeron/design/reports/`:

| Candidate | comparand-independence | offline-checkability | honest-remeasure-acceptance | rule-wall-clock | committed-bytes-added |
| --- | --- | --- | --- | --- | --- |
| `recompute-at-check` | pass | **fail** | pass | 3 ms | 0 bytes |
| `fold-into-stream-digest` | **fail** | pass | pass | 40 ms | 0 bytes |
| `source-pinned-count-commitment` | pass | pass | pass | 11 ms | 109 bytes |
| `token-stream-witness` | **fail** | pass | pass | 133 ms | 22,098 bytes |

Three candidates fail a selection hard gate. One survives, and
`unique-frontier` selects `source-pinned-count-commitment`.
`python3 "$PLUGIN_ROOT/skills/protasis/scripts/design_evidence.py" .hexaemeron/design-evidence.json --transition design-lock`
reports `clean` at exit 0. The record digests to
`32506d00c7ea9eb4e292ed3d2ba03512fdcf5f4d20b204570bd9d97e4f4876db`.

**How the numbers were produced, and what they do not establish.**
`.hexaemeron/design/probe.py` reduces each candidate to its acceptance rule and
applies it to real material: the six projected byte streams from the two
fixtures whose recorded digest and byte length still recompute from today's
bytes, paired with the counts a real run recorded for them. The third fixture is
excluded rather than given a made-up count. `recompute-at-check` is handed an
oracle seeded from those recorded counts, and every oracle read is counted,
which is how it fails `offline-checkability`. The oracle stands in for a
tokenizer, so the probe establishes each rule's dependency structure and its
discriminating power against the tamper. It does not establish that any
candidate's implementation exists, nor that the committed counts are right.
`rule-wall-clock` times 5,000 applications because the contract carries
milliseconds as an integer; it is a comparison between rules, not a budget.

**The issue's own claim, checked rather than assumed.** The issue argues both
fields are "the same shape of hole", the remedy for both being "to derive the
compared value from something the checker computes rather than from something
the record carries". **That does not hold for the adapter half.** There the
checker already computes the compared value: it runs the identity command and
digests what came back. The fault is not that the comparand echoes the record;
it is that one digest conflates two causes. The two halves therefore need two
independent remedies, and the design record's one conformance criterion,
`identity-cause-attribution`, is the adapter half's own obligation.

## 5. Risk register seed

`check` reads an evidence tree it does not trust, runs a subprocess, and is the
gate a delivery is accepted on. The audit loop should look hardest at whether
the new anchor can be reached from the tree it is meant to anchor, and at
whether the `disabled` path keeps behaving exactly as it does today.

```risk-register
count-anchor-reachability | the constant the checker compares the count vector against | no edit confined to the evidence tree, the manifest or the coverage register changes the value the checker compares against
disabled-path-unchanged | the short circuit at scripts/agent_instruction.py:3484-3488 | the disabled path still refuses WAI-E-DIGEST.FROZEN on any edit and reaches no new code, and the committed fixture still accepts at exit 0
synthetic-fixture-fidelity | the synthetic active fixture built for the guards | it reaches _validate_measurement_record through check_manifest as a real tree would, reuses the TRUSTED_PROFILE_SHA256 bytes verbatim, and changes no byte under tests/fixtures/agent-instruction-v1
identity-cause-separation | the two refusal codes at scripts/agent_instruction.py:1650-1668 | a rendering change with an unchanged blob set and a blob-set change reach different codes, both are reachable, and refusal-detail-coverage still enumerates every adapter refusal
honest-remeasure-not-trapped | the path a genuine re-measurement takes | a re-issued record plus its one reviewed constant is accepted, so the guard refuses tampering rather than refusing repair
coverage-register-currency | tests/promise_machine_coverage.json rows for the checker, its tests and its documentation | every row whose file the step changed is re-pinned in the same step and the register check is green
issue-1192-surface-untouched | digest_neutral_projection, _corpus_sha256 and the recorded span offsets | the diff reaches none of them, so skills#1192's remedy still applies unchanged
```

## 6. Glossary seeds

- **Comparand.** The value a check compares a recorded field against. The whole
  question here is where it comes from.
- **Tautological guard.** A check whose comparand is derived from the field it
  is checking, so it cannot fail.
- **Trust anchor.** A value the checker carries and the data under examination
  cannot reach. In this repository, a constant in `scripts/agent_instruction.py`.
- **Count vector.** The ordered token counts a measurement record carries, one
  per measured stream, taken together as the thing the anchor commits to.
- **Self-consistent tamper.** An edit to a recorded count carried through every
  field the editor can recompute from the record and the tree, including the
  manifest binding.
- **Rendered identity.** The stdout of the adapter's identity command, digested
  whole as `acquisition_sha256`.
- **Model-blob projection.** The `sha256-<64 hex>` set `MODEL_BLOB_RE` extracts
  from that same stdout. It identifies the model; the rendering around it does
  not.
- **Synthetic active fixture.** An in-tree fixture carrying
  `model_evidence_status: active`, built offline, used to reach code the
  committed fixture cannot reach.
- **Self-consistency, not correctness.** What the selected design establishes:
  the counts have not moved since they were reviewed. It never establishes that
  a count is what a tokenizer would return.

## 7. Sources

- Issue: https://github.com/wildcat-finance/skills/issues/1199
- Related, open, non-goal: https://github.com/wildcat-finance/skills/issues/1192
- Predecessor, closed 2026-09-04: https://github.com/wildcat-finance/skills/issues/1098
- Unrelated, closed 2026-09-04: https://github.com/wildcat-finance/skills/issues/1205
- Unrelated, closed 2026-09-12: https://github.com/wildcat-finance/skills/issues/1520
- Last merge touching the checker: https://github.com/wildcat-finance/skills/pull/1638
- Source: `scripts/agent_instruction.py`, lines 37, 51, 156, 1589-1668,
  2938-2973, 2976-3215 and 3484-3488.
- Tests: `tests/test_agent_instruction.py`, lines 2499, 3731, 3786 and 3805.
- Runtime contract: `docs/agent-instruction-language-v1.md`.
- Decision already in force on this surface:
  `docs/decisions/ADR-062-encode-a-closed-agent-instruction-model.md` and
  `docs/decisions/ADR-076-digest-neutral-measured-corpus.md`.
- Audit: `audit/rounds/fiat-1098-make-a-bound-instruction-document-editable.md`
  and its sibling `.synopsis.md`; `audit/AUDIT.md` and `audit/AUDIT_SYNOPSIS.md`.
- Coverage register: `tests/promise_machine_coverage.json`.
- Design record and reports: `.hexaemeron/design-evidence.json`,
  `.hexaemeron/design/probe.py`, `.hexaemeron/design/reports/`.

## 8. Signals, and the questions behind them

`check` is run from a terminal and from CI, so there is no unattended alerting
here. There are on-call questions, and the answer to each is a record `check`
already emits. [ephoros](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry; this study only names the questions and the step
that answers them.

1. *This refused. Was it the counts, or the bytes?* The refusal's code and
   `node_path` must separate them. A count refusal names the count field, not
   `$.evidence.measurement_record` as a whole. Answered by the step that adds
   the count commitment.
2. *This refused on the adapter. Do I re-pin, or is my runtime actually
   different?* Answered by the step that splits the identity check: the code
   itself says which of the two it saw, and where it cannot tell, it says so.
3. *Which path did this tree take, active or disabled?* Already answered:
   `run.summary` carries `model_evidence_status`, emitted at
   `scripts/agent_instruction.py:2913`. No change needed, and the new records
   must not drop it.
4. *Is the anchor stale, or is the record tampered?* These must not look alike.
   The refusal must distinguish a record that disagrees with a current anchor
   from one whose anchor was never updated after a legitimate re-issue.

## 9. Boundaries, per capability

[phylax](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and the controls. Three boundaries are open here and this
delivery opens no new one.

1. **The evidence tree is untrusted input.** `check` parses JSON a contributor
   or an attacker may have written. The control today is the closed-object
   codec, bounded numbers and confined reads. The new count check must add no
   unbounded read and no new parse: it compares a digest over values the codec
   has already validated. This is the boundary the whole issue sits at, because
   the tree is currently trusted for one field.
2. **The adapter subprocess and its stdout.** `_run_bounded`, defined at
   `scripts/agent_instruction.py:1395` and called for the identity command at
   line 1639, runs a pinned absolute executable with a fixed environment and
   capped output. The identity split reads the same
   captured bytes with the same regex that already runs. It adds no subprocess,
   no argument and no environment entry.
3. **The checker's own source as a trust anchor.** This is the boundary the
   selected design creates, and it is worth naming rather than assuming. Moving
   a constant in `scripts/agent_instruction.py` is a reviewed diff that re-pins
   `agent_instruction.checker` in `tests/promise_machine_coverage.json`. The
   control is that the anchor must be a plain data constant and not reachable by
   any path `check` reads, so a tree edit can never supply it.

No credential, no network, no new dependency and no new filesystem write are
introduced.

## 10. The budget, or its absence

There is a budget and it is small.
[metron](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/metron/SKILL.md)
owns what a budget carries and how it is checked.

`check` is run by contributors and by CI on every change to this surface, so
added work is paid often. The selected rule was measured at 11 milliseconds for
5,000 applications over six materials, against 40 for
`fold-into-stream-digest` and 133 for `token-stream-witness`. Scaled to one
`check` run over three fixtures, the added work is well under a millisecond.

**Budget.** `check` over the committed manifest must not get more than 50
milliseconds slower than its pre-change baseline. Measured before and after the
count commitment lands, on the same machine, by:

```bash
python3 -m timeit -n 5 -r 5 -s "import sys; sys.path.insert(0, 'scripts'); import agent_instruction as AI" "AI.check_manifest('.', 'tests/fixtures/agent-instruction-v1/manifest.json')"
```

The baseline is recorded before the change, not reconstructed after it. Fifty
milliseconds is chosen because it is far above the measured cost of the rule and
far below anything a contributor would notice; a change that spends it has done
something other than compare a digest.

## 11. The fail-closed posture

[elenchus](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

**What stops the run.** Every new condition refuses; none warns. A count vector
that disagrees with its anchor refuses. An anchor absent for a record on the
`active` path refuses, rather than being treated as "no anchor, therefore
nothing to check" -- an empty anchor is the same failure as an empty
known-failure list. A rendering change the checker cannot attribute refuses and
says it cannot attribute it. The `disabled` path keeps refusing
`WAI-E-DIGEST.FROZEN` on any edit to the two frozen records.

**Guard convention.** Each named refusal gets one test that fails without the
fix and passes with it, in `tests/test_agent_instruction.py` beside the existing
`MeasurementTests` at line 2499, driving `check_manifest` over a temporary tree
exactly as `edited_token_count_tree` at line 3731 already does. A guard asserts
the exact refusal code and node path, never only that something refused.

`test_a_consistent_token_count_edit_is_not_detected` at line 3805 is the case
this delivery inverts. It is replaced deliberately, in the step that lands the
count commitment, by a case asserting the new refusal. It is not left to be
found red, and its sibling `test_an_edited_token_count_refuses_on_its_own` at
line 3786 stays, because the record's own arithmetic is still the half of the
guard that works.

## 12. Decisions and their homes

[hypomnema](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record and where each one lives.

Two decisions here are expensive to reverse.

1. **Anchoring an evidence value in checker source.** This changes what an
   honest re-measurement costs: from re-issuing a record to re-issuing a record
   and moving a reviewed constant. Reversing it means removing a guard, which
   needs the reason it was added. No existing record governs it:
   `docs/decisions/ADR-062-encode-a-closed-agent-instruction-model.md` fixes the
   codec and puts measurement and parity adapters outside its authority, and
   `docs/decisions/ADR-076-digest-neutral-measured-corpus.md` governs how the
   corpus is measured, not how a count is trusted. Nothing in `docs/decisions/`
   governs `model_evidence_status`. **This needs its own record**, written as an
   unnumbered draft at
   `docs/decisions/drafts/pin-measurement-counts-in-checker-source.md`, beside
   the one draft already there, and numbered at assignment time. It must state
   plainly what the guard does and does not establish, because that distinction
   is the whole of its value.
2. **Splitting the adapter identity check into two causes.** This changes the
   meaning of an emitted refusal code, which other readers and the
   `refusal-detail-coverage` register depend on. It belongs in the same draft
   record as a second decision, because the two are delivered together and a
   reader asking "why two codes?" is asking the same question as "why an
   anchor?": both are about what a green result is worth.

**One reading recorded rather than guessed.** Hypomnema's own design bridge, the
three-row `design-bridge` block that binds a selected candidate to its record
home, is not declared in this study. That record does not exist yet, so a bridge
naming it would be red until the step that writes it lands. No receipt in this
run runs the bridge check: `done study` runs only the file lint, and neither
Fiat's nor Protasis's contract mentions the block. The step that writes the
draft is the right place to add the bridge, by study amendment.

`docs/agent-instruction-language-v1.md` is the runtime contract and is updated
in the same step as the behaviour, not after it. Its "Measurement and parity
evidence" section currently says the `active` path "restores the existing full
evidence validation"; that sentence stops being true when this lands and must
be corrected rather than left standing.
