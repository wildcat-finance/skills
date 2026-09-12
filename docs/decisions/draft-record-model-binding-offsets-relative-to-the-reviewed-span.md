# Record model binding offsets relative to the reviewed span

## Status

Proposed, 2026-09-12. Unnumbered on purpose. The arithmetic against this base
gives a number the default branch is still handing out to concurrent runs, and
issue #888 records why a record taking its number at authoring time goes stale:
ADR-050 collided that way, and the ADR-024 duplicate turned `main` red until
#582 renumbered the Wave Delta chain. Whoever merges this record gives it a
number by hand.

The filename carries no `ADR-` prefix because `tests/test_decision_records.py`
globs `ADR-*.md` and then requires digits, so a prefixed draft fails
`test_every_filename_follows_the_convention`.

This reopens the encoding ADR-062 settled, which is why it is a record rather
than an amendment.

## Context

`tests/fixtures/agent-instruction-v1/manifest.json` binds three instruction
documents, and for each one it records a reviewed span by absolute byte offsets.
Editing a bound document **after** its reviewed span end was made reconcilable
by skills#1098. Editing one **before** the span was not, and skills#1192 was
filed for the difference.

The measurement record measures each fixture's `canonical_model` and `compact`.
Both documents carried the reviewed span's offsets *inside* them: `model.json`
as every binding's `start` and `end`, and `compact.wai` as the codec's rendering
of the same model. So an edit before the span moved both measured streams, and
`_measurement_material` refused `WAI-E-MEASURE.RECORD` for them.

skills#1098 diagnosed one cause, `_corpus_sha256` digesting a subject that
carried `fixtures` whole, and tried removing the offsets from that subject. It
backed the removal out at `a629a25d`: it cleared the first check and not the
second, bought no observable behaviour, and cost the corpus digest its ability
to distinguish a moved offset.

The digest-neutral projection cannot close the second cause. It substitutes byte
sequences, which is sound for a 64-hex digest literal and unsound for a decimal:
`18445` is a substring of `184450`, so substituting one offset can rewrite part
of another number. And those two streams are what the recorded token counts are
counts of, so making the corpus digest ignore them is not the narrowing that
argument licenses.

The cost fell on one machine. Only `scripts/agent_instruction.py measure` can
reissue the counts, and only the host the tokenizer profile pins can run it. A
contributor without that machine could not edit a bound document before its
reviewed span at all.

## Decision

`model.json` records every binding's `start` and `end` **relative to the
reviewed span's start** rather than as absolute file offsets.

An edit before the span moves `source.start`, `source.end` and every absolute
span in `source-spans.json` by one delta, and leaves every relative offset
exactly where it was. The two measured streams therefore do not move, and no
`measure` run is owed for a placement that changes no reviewed byte.

The offsets keep their full meaning: they still locate each governed node within
the reviewed span. `source-spans.json` stays absolute, because it is the record
checked against the source bytes, and `_validate_source_spans` resolves the
model's relative pairs against `source.start` before comparing the two.

## Consequences

`scripts/prove_agent_instruction_reconciliation.py` no longer re-derives the
model's offsets. Its model pass still requires the record to be its own
canonical bytes and then returns them unchanged, so a malformed model refuses
where it always did.

`tests/test_agent_instruction.py::DigestNeutralProjectionTests::test_a_before_span_edit_still_moves_the_measured_artefact_streams`
pinned the behaviour this record changes. skills#1192 named it as expected to
fail, and it is replaced by
`test_a_before_span_edit_leaves_the_measured_artefact_streams_where_they_are`,
which asserts the invariance directly. `test_source_span_records_mirror_model_bindings`
resolves one record against the other instead of matching decimal strings, and
`test_model_bindings_are_relative_to_the_reviewed_span` refuses any binding that
carries a file offset again.

An edit **inside** a reviewed span still moves the corpus digest and `check`
still refuses it. That is unchanged and is the guard against this going too far.

**This change costs one `measure` run and one `parity` run, and they are owed.**
Moving the three fixtures from absolute to relative offsets changed the model's
own bytes once, because `"18710"` is five characters where `"0"` is one, so
`evidence/measurement.json` and `evidence/parity.json` carry counts of bytes
that are no longer there. `agent_instruction.py check` reports `failed: 0` for
every fixture and refuses at `$.evidence.measurement_record` alone. Until those
two records are reissued on the pinned host, that refusal stands and the tests
that read them stay red. It is the last such run this placement will cost.
