# Deliver the emitter-fidelity suite as a first-party harness

## Status

Proposed, 2026-09-07. Unnumbered on purpose, and nothing assigns the number
yet. Numbers are compared against the default branch by
`tests/test_decision_records.py`, so a number picked while this branch is open
can collide with one another open branch lands first. Whoever merges this
record gives it a number by hand, or leaves it unnumbered knowingly.

The filename carries no `ADR-` prefix because `tests/test_decision_records.py`
globs `ADR-*.md` and then requires digits, so a prefixed draft fails
`test_every_filename_follows_the_convention`. Elsewhere this record is cited by
its stable slug, `deliver-the-emitter-fidelity-suite-as-a-first-party-harness`.

This record supersedes nothing.

## Context

Twenty-seven event emitters in `wildcat-finance/v2-protocol` build their logs by
hand in assembly rather than through the compiler's `emit`. Nothing checks that
what they write matches what the corresponding `event` declaration says a log
of that event looks like: the topic count, topic0, the indexed values in
declaration order, and the ABI-encoded data region. An emitter and its
declaration can drift apart and every test in the protocol repository still
passes, because the tests read the emitters' own output.

A suite that proves that correspondence has to live somewhere. Four homes were
proposed and measured, and the measurement is not this prose: it is
`.hexaemeron/design-evidence.json` under `protasis-design-evidence/v1`, whose
values `.hexaemeron/measure_design.py` computes from the two real trees. Three
of the four candidates fail a gate.

Two constraints narrowed the field before any measurement. The Fizz skill tree
is vendored: its `NOTICE.md` records it as taken verbatim from the Pashov Audit
Group suite, and `ADR-005-vendor-the-pashov-suite-whole-and-ungoverned` decides
that the suite is upstream-owned, byte-for-byte unmodified and ungoverned, with
the loop's own conventions stopping at the vendored boundary. That makes the
Fizz tree ineligible as a home for first-party Solidity. Separately, a home
that no declared check in this repository builds is a delivery that executes
nothing, which is the failure two carried audit findings already record.

## Decision

**The suite is delivered into `wildcat-finance/skills` as a first-party Foundry
root at `plugins/hexaemeron/harness/`,** carrying the pinned protocol closure,
a mirror-emit reference and the differential cases, in the shape
`plugins/janus/harness/` already has, with its own workflow and its own entries
in `tests/check-map-v1.json`.

The three rejected candidates and the gate each failed:

- **`fizz-inline`**, the generator, template and reference added inside the
  vendored Fizz skill tree. It failed all three gates:
  `repo-runnable-emitters` 0 against a floor of 27, `vendored-tree-writes` 3
  against a ceiling of 0, and `offline-missing-sources` 11 against a ceiling of
  0. The middle number is the one that matters most: three of its write paths
  land under a root whose `NOTICE.md` declares it vendored verbatim, which
  `ADR-005-vendor-the-pashov-suite-whole-and-ungoverned` refuses.
- **`spec-only`**, the inventory, specification, oracle design and campaign
  record landing here as evidence with the executable suite delivered to the
  protocol repository separately. It failed two gates:
  `repo-runnable-emitters` 0 and `offline-missing-sources` 11. A reader holding
  only this repository could reproduce nothing.
- **`fixture-project`**, a Foundry project under
  `plugins/hexaemeron/tests/fixtures/` in the shape Ariadne uses. It failed the
  correctness gate, `repo-runnable-emitters` 0, because no declared check in
  this repository compiles a Foundry root of that shape; the existing fixtures
  of that shape ship compiler output rather than a compiled tree.

`skills-harness` is the one candidate that passes every gate, so the record's
selection rule is `unique-frontier`.

### The oracle is declaration-derived

**Each expected log is derived from the `event` declaration, through a
mirror-emit reference contract.** The reference imports the declaring interface
and redeclares nothing of its own; it emits each event through high-level
`emit` and lets the compiler derive topic0, the topic count, the indexed
positions and the data encoding. A differential case calls the emitter and the
reference with the same arguments and compares the two recorded logs.

No expected topic0, topic count, indexed position or data offset is read from
or transcribed out of the two emitter files. An oracle transcribed from the
code under test proves only that the transcription was faithful, and a suite
built that way can be green for a year while proving nothing. Because the
reference imports the declaring interface rather than restating the events, a
change to a declaration reaches the reference by compilation and cannot pass
unnoticed.

### The vendored closure is pinned and its provenance is checked

**This repository carries a pinned copy of eleven protocol Solidity files,
46,799 bytes, taken from `wildcat-finance/v2-protocol` at ref
`f5a26146987926f4811b72a795d662813dedfe85`.** That is the transitive import
closure of the two emitter files and the two declaring files. The closure has
no remapped or external imports, measured, so it builds with `libs = []` and
pulls no dependency across with it.

**The provenance-check rule.** The harness records the protocol ref and each
vendored file's SHA-256, and the suite checks those digests on every run. A
mismatch fails. It never re-baselines itself, and no vendored protocol file is
edited in place. Re-pinning to a later protocol ref therefore means changing
the recorded ref and the recorded digests together, in a change a reviewer can
see, with the suite re-run against the new bytes. What this buys is that a
stale or substituted copy cannot quietly become the thing the suite proves
fidelity against.

### No version is incremented

**This delivery increments no skill version.** Fizz keeps no frontier ledger:
it has a `VERSION` file containing `1` and no `EVOLUTION.md`. No
Hexaemeron plugin-level ledger exists in the tracked tree either. There is
nothing to increment, and the task issue's `held-job` label does not authorise
an increment; it marks a job as held, not a frontier as advanced. The only
Hexaemeron ledger in scope is Fiat's own, and nothing here touches it.

## Alternatives

The three rejected homes are named above with the gate each failed, because
the home decision is the one they are alternatives to. Two further alternatives
were considered for the sections that follow it.

- **An oracle transcribed from the emitters,** with each expected topic0 and
  data offset written out beside the emitter that produces it. Rejected because
  it makes the code under test its own authority: every case would pass by
  construction on the day it was written and would keep passing through any
  drift the transcription shared.
- **Fetching the protocol closure at run time instead of vendoring it.**
  Rejected because it fails the recovery gate the measurement applied to
  `spec-only` and `fizz-inline`: eleven files a reader would have to fetch from
  elsewhere before a filed counterexample could be reproduced. Vendoring pays
  46,799 tracked bytes and a re-pinning duty to make the suite reproducible
  from this repository alone.

## Consequences

**A new emitter must pair by name or the suite fails.** Every `emit_<EventName>`
free function has to resolve to exactly one declaration, and the paired count
has to equal the count of such functions in the two vendored files. An emitter
that resolves to no declaration fails the suite rather than being skipped. So
adding an emitter in the protocol repository without adding its case here turns
this repository red, which is the point: silence is what the suite exists to
remove.

**The re-pinning duty outlives this delivery.** Once the protocol moves, the
vendored bytes here are a snapshot of something older, and the digest check
says so rather than hiding it. Somebody has to re-pin deliberately. Nothing
here does it automatically, and nothing here should.

**Reversing the home is expensive.** It moves every file, every specimen path,
the workflow and the check-map entries. That is why the choice is recorded
rather than left to whoever reads the directory layout next.

**The oracle and the home are one decision recorded once.** The mirror-emit
construction is what the first-party home makes possible; a reader who finds
one needs the other, so they are sections of a single record rather than two
records pointing at each other.
