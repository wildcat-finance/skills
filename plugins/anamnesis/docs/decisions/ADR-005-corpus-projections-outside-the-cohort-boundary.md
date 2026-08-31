# ADR-005: Corpus projections sit outside the Synkrisis cohort boundary

## Status

Accepted, 2026-08-31.

## Context

Anamnesis emits `anamnesis-synkrisis-observation/v1`. Synkrisis admits one
producer identity, `promise-machine-run-observation/v1`, checked at two places:
`load_manifest` refuses another with `SK008`, and cohort verification refuses one
with `SK012`. The projection is produced and not consumed, and that gap has been
Anamnesis's held next job since the consumer projections shipped. Anamnesis's own
ADR-004 said the schema was one "Synkrisis explicitly admits"; that was wrong when
written, and its status now says so.

The two shapes disagree about what a member is. A Synkrisis cohort member is a
run. Its schema requires nine fields per member, and six of them have no source
in a finding: `reason_code` is a closed enum of `dimension-mismatch` and
`binding-unavailable`, and `record`, `sha256`, `bytes`, `events` and
`binding_status` all describe a stored event stream. `events` has a declared
minimum of 2. A finding has none of these.

They also disagree about what a denominator is. A Synkrisis cohort partitions one
population: every declared run appears exactly once as included, excluded or
unknown, and the cohort digest binds rule evaluation to that classification. The
Anamnesis projection carries ten denominators over ten different populations:
engagements, findings, occurrences, relations, remediations, rounds, rounds with
no findings, submissions, verifications, and findings withheld by disclosure.
There is no single population to partition, so there is nothing for the
included, excluded and unknown arrays to be a partition of.

Synkrisis has already refused a different input class on this reasoning.
Synkrisis's own ADR-004, at
`plugins/synkrisis/docs/decisions/ADR-004-separate-run-and-reachability-evidence.md`,
rejected issue-437 reachability candidates because "a disposition
describes a run, and a reachability candidate is not a run". A finding is not a
run either.

## Decision

Corpus projections sit outside the Synkrisis cohort boundary. Anamnesis does not
ask Synkrisis to widen its producer contract, and this record does not decide
anything on Synkrisis's behalf.

What reads the projection instead is the projection itself, read directly under
`anamnesis-synkrisis-observation/v1`. `anamnesis observations` emits it,
`check_projection` holds it to its closed field set before it leaves, and a guard
in `plugins/anamnesis/tests/test_s5_boundary.py` establishes that it carries what
a reader needs: every count has a denominator to be read against, and the
exclusions, the unknowns and the `not_established` sentence are all present.
A projection missing any of the four is refused.

That is the whole claim. The projection is legible on its own terms, so it does
not need a consumer to be worth emitting.

## Alternatives

**Widen the producer constant.** One module constant and a schema `const`
become an enum, and corpus findings map onto `runs[]`. It is the cheapest edit
and the largest misstatement: six required run fields would carry values a
finding cannot supply, `events` would carry a number where a finding has none,
and the ten denominators would be dropped at the boundary because the cohort
object declares none and is closed. The held job requires denominators and
exclusions to survive, and this is the option that loses them.

**A sibling cohort kind in Synkrisis.** A second producer contract, its own rule
kinds and its own promise, which is the seam that same Synkrisis ADR-004 named for a
future admission. This is the option that would work, and it is not Anamnesis's
to take. It is a frontier-scale change to Synkrisis, whose ledger is open at
`synkrisis-v4.2.0` on a different held job about captured run observations. The
versioning contract reserves a held target for a completed frontier job on that
skill.

## Consequences

Anamnesis emits a projection that no other member consumes, and that is now a
recorded position rather than an unanswered question.

The seam stays open. If Synkrisis later wants corpus comparison, that Synkrisis
ADR-004 already describes the shape: a new producer contract in the manifest, a new rule
kind, and a promise stating what the combination establishes and what it refuses.
Nothing here forecloses that, and nothing here obliges it.

Anyone wanting to compare corpora today reads the projection directly. They get
counts with their denominators attached and an explicit statement of what the
counts do not establish, which is what the shape was built to carry.
