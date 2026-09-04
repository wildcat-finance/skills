# ADR-074: Measure the instruction corpus through a digest-neutral projection

## Status

Accepted, 2026-09-04, for
[skills#1098](https://github.com/wildcat-finance/skills/issues/1098).

The Fiat runbook allocated this decision as `ADR-<next>`, which was ADR-069 on
the branch the step was cut from. Concurrent work landed ADR-069 through
ADR-073 on `main` while the run was in flight, so the decision lands as
ADR-074.

Depends on [ADR-062](ADR-062-encode-a-closed-agent-instruction-model.md), which
settled two things this record does not reopen: that the bound corpus retains
source digests and spans beside every derived form, and that a measurement of
the compact encoding against its source is evidence the prototype owes. This
record changes what one digest in that arrangement is a digest *of*. It does
not argue that the measurement should stop existing, and it does not weaken the
whole-file binding.

## Context

Three instruction documents are bound into `tests/fixtures/agent-instruction-v1`
by whole-file SHA-256. Each is bound four times over: the manifest records the
document's whole-file digest, the three artefacts derived from it — `model.json`,
`source-spans.json`, and the compact document's `h64:` literal — each embed that
same digest, and the manifest then binds each of those artefacts by a digest of
the bytes the embedding sits inside.

`_corpus_sha256` digested a subject carrying `fixtures` whole, so it carried all
four. Editing a bound document *outside* its reviewed span therefore moved the
corpus digest, even though the reviewed span, its digest, every recorded binding
offset, and every byte the measurement actually counted were untouched.

Both committed evidence records — `evidence/measurement.json` and
`evidence/parity.json` — carry that corpus digest, and `check` compares each one
against the recomputed value. So a typo fix past the end of a reviewed span
refused the whole fixture with `WAI-E-DIGEST.CORPUS`, and clearing that refusal
required reissuing both records.

Reissuing them is not a formality the repository can perform on demand. Only
`agent_instruction.py measure` and `parity` can write them honestly, they run
through a loopback adapter pinned to one macOS install and one 65 GB local
model, and no count, correlation id, or observation date in either record may be
written by hand. The practical effect was that a bound instruction document was
uneditable: the cheapest correction cost a measurement run that most
contributors cannot perform at all.

`_validate_measurement_record` recomputes `correlation_id` from
`_corpus_sha256`, and that correlation id is stamped into every
`events[*].correlation_id`. The corpus digest therefore reaches further into the
measurement record than the `corpus_sha256` field alone, which is why moving the
subject stales the record wholesale rather than in one place.

## Decision

Keep the manifest's bindings exactly as they are, and change only what the
measured corpus's identity is computed from.

`digest_neutral_projection` substitutes one fixed marker — 64 `f` characters,
well-formed lowercase hexadecimal that is not a plausible SHA-256 output — for
every digest the manifest binds a path by. That set is each fixture's
whole-file `source.sha256` and all five of its `artifacts.*.sha256`: six per
fixture, eighteen across the committed corpus. It is the same enumeration
`bound_digests` reports in
`scripts/prove_agent_instruction_reconciliation.py`, and
`test_the_projection_covers_every_path_the_prover_binds` asks the prover for
that list rather than restating one, so a path the manifest starts binding
cannot be protected by the prover and passed over by the projection.

Substitution is by byte rather than by field path, because one embedding has no
addressable path: the compact document carries the digest as an `h64:` literal
inside a codec's byte stream, not as JSON.

`_corpus_sha256` keeps its subject's shape — schema, the three counts, the risk
classes, and `fixtures` whole — and digests those canonical bytes *after* the
projection has run over them. The corpus's identity is therefore the reviewed
span digest and the projected digests, in place of the whole-file digest and the
raw artefact digests.

`span_sha256` is never in the projected set. That is the whole of why the
widening is safe: an edit inside a reviewed span moves it, the subject differs,
and the corpus digest moves, so `in-span-edit-refusal` holds unchanged.
`test_the_corpus_subject_still_moves_on_an_in_span_edit` checks that for all
three fixtures, and
`test_the_reviewed_span_digest_is_distinct_from_the_projected_digest` checks the
premise it rests on rather than leaving it to the fixtures' good behaviour.

One marker serves all eighteen bindings rather than one marker per binding. The
corpus digest is meant to stop distinguishing revisions that differ only in a
bound digest, and per-binding markers would keep distinguishing them by which
slot moved. The subject still carries every source path, every reviewed span's
offsets, and every artefact path, so an artefact appearing, vanishing, or being
renamed still moves the corpus digest.

`measure` and `parity` count the same projection. The canonical models and the
compact documents are put to the tokenizer, and to each parity family, through
`digest_neutral_projection`, and each recorded count names the projection it was
taken under. Projecting the subject without projecting the measured bytes would
have left the measurement record stale at
`documents[*].canonical_model` under exactly the edit the subject change absorbs,
which is half a design rather than a smaller one.

`check` still verifies every whole-file and artefact digest against the bytes on
disk. `WAI-E-DIGEST.SOURCE` and `WAI-E-DIGEST.ARTIFACT` are untouched, and a
tampered bound document is caught exactly where it was before. What stops
happening is a measurement being declared stale by a change that moved no
measured byte.

## Alternatives

- **Vendor a deterministic tokenizer and leave the corpus definition alone.**
  This is the direct fix for the underlying grievance — that reissuing evidence
  needs a machine almost nobody has — and it would make the measurement
  reproducible anywhere. Rejected because it reissues the recorded counts
  against different model bytes: the committed measurement is an observation of
  `gpt-oss:120b`, and replacing the tokenizer replaces the thing observed while
  keeping the record's shape. ADR-062 put the measurement adapters outside the
  codec's authority precisely so they could support only the exact profiles they
  record, and a vendored tokenizer would quietly make the record a claim about
  a tokenizer nobody measured.
- **Publish a container or record a second tokenizer profile, so the pinned
  adapter can run somewhere besides one laptop.** This attacks the same
  grievance from the other side and leaves every digest where it is. Rejected
  for this delivery rather than on the merits: it does not stop an out-of-span
  edit invalidating the records, it only makes reissuing them cheaper, so the
  cost of editing a bound document stays proportional to a model run. It is a
  reasonable separate change and this record does not rule it out.
- **Stop comparing each committed evidence record's corpus digest to the
  manifest.** The smallest possible diff, and it makes the refusal go away
  immediately. Rejected because it removes the binding rather than narrowing it:
  nothing would then catch an evidence record left behind by a genuine change to
  the reviewed corpus, which is the case the comparison exists for. Narrowing
  what the digest is a digest of keeps an in-span edit refusing; deleting the
  comparison does not.
- **Substitute by JSON field path instead of by byte.** Rejected because the
  compact document's `h64:` literal has no field path, so this would need a
  schema-aware walker per artefact kind and would still miss the one embedding
  that motivated the projection.

## Consequences

An out-of-span edit to a bound instruction document, with the five mechanical
passes applied, no longer moves the corpus digest, and neither evidence record
is staled by it. An in-span edit still moves it and still refuses, at
`WAI-E-DIGEST.SOURCE_SPAN` before any evidence record is consulted and at
`WAI-E-DIGEST.CORPUS` behind a rebound span digest.

Switching the subject moves the corpus digest once, as a one-off. Both committed
evidence records, their `correlation_id`, and every `events[*].correlation_id`
are stale against the new subject from the moment this lands, and only one
`measure` run and one `parity` run can replace them. The tests that compare a
committed record against the recomputed digest assert the post-reissue value and
are red until that run happens, which is the honest way to make the reissue's
absence visible.

The corpus digest is now weaker evidence than it was, and deliberately so. It no
longer distinguishes two revisions of the corpus that differ only in a bound
digest's value. It still distinguishes a change to any reviewed span, to any
recorded offset, to the set or the paths of the bound artefacts, or to the
counts and risk classes. Anything relying on the corpus digest to detect a
changed artefact *value* must read the manifest's own bindings instead, which
`check` verifies on every run.

The change reaches the measured bytes as well as the measured subject, because
the design record takes the embedded whole-file digest out of both. `measure`
counts `digest_neutral_projection(manifest, ...)` of each canonical model and
each compact document, `parity` puts the projected compact document to each
model family, and `_measurement_material` and `_validate_parity_mode_record`
compare against those same streams. The reviewed spans are still counted raw:
a span's recorded digest is its `span_sha256`, and that equality is the review
boundary. `test_no_reviewed_span_carries_a_bound_digest` observes that no span
would be changed by the projection anyway, so measuring it raw is a checked
fact rather than an exception carved out in the code.

One trap comes with the widening, and it is latent rather than present. The
projection substitutes a digest *value*, so it cannot tell a `source.sha256`
apart from any other field carrying the same bytes. No fixture's reviewed span
covers its whole file today, so no `span_sha256` holds the same bytes as its own
`source.sha256` and the review boundary survives. A fourth fixture whose span ran
from 0 to the file's length would make those two digests identical, the
projection would neutralise the span digest along with the binding it aims at,
and an in-span edit would stop moving the corpus digest: `in-span-edit-refusal`
would fail while every other property still held.
`test_the_reviewed_span_digest_is_distinct_from_the_projected_digest` asserts
that `(start, end)` is not `(0, len(source))` for every fixture and that no
`span_sha256` is in the bound set, so the trap is caught by the suite and not by
`check`. Whoever adds a fourth fixture meets it as a test failure rather than as
a refusal naming the cause; closing that gap means a new refusal in `check`, and
a new refusal is a change to a version-1 contract, so it was not taken here.

Every measured stream in both records carries a `projection` field naming the
rule applied before it was counted, either `none` or
`digest-neutral-bound-sha256/v1`. The name is versioned because it identifies
what a count is a count of: widening or narrowing the projection requires a new
name, so a record written under one rule cannot read as though it were written
under another. An undefined name refuses with `WAI-E-MEASURE.PROJECTION` or
`WAI-E-PARITY.PROJECTION`. The contract for the field is in
[`docs/agent-instruction-language-v1.md`](../agent-instruction-language-v1.md),
because a reader who finds a `compact.sha256` that does not match `compact.wai`
on disk has to be able to find out why from the contract rather than from the
checker.

Not measured here has not become not bound anywhere. The manifest still binds
every artefact by the digest of the bytes on disk, and `check` still verifies
each one on every run, so the measurement record's projected digest and the
manifest's raw digest are two different checked claims about two different byte
strings, and neither substitutes for the other.
`test_the_measurement_record_binds_the_projected_artefact_digests` asserts both
at once, and asserts that the two differ, so a projection that quietly stopped
projecting could not pass it.

The whole property was simulated end to end before the single budgeted run was
spent: both records rebuilt in a throwaway copy by the checker's own generators,
with the committed token counts substituted for the model, then an out-of-span
edit applied to each of the three bound sources with the five mechanical passes
run. `check` exited 0 for all three with the corpus digest unmoved, and exited 2
with the corpus digest moved for an in-span edit to each of the three. The
simulation holds the counts fixed, so it establishes what `check` compares and
says nothing about the sign of `delta_tokens`, which only the run can observe.

One placement stays uncovered and is step 4's: an edit *before* a reviewed span
start moves every recorded binding offset, and reconciling it needs the offsets
re-derived rather than the digests rewritten.
`prove_agent_instruction_reconciliation.py span-shift` reports that placement as
uncovered rather than omitting it, so the criterion stays unmet until it is
exercised.
