# Decision: Record a timed run as its declared aggregation with the spread beside it

## Status

Proposed, 2026-09-07. The record takes its number at the integration composition,
which is where the merge composer assigns one from the base branch.

## Context

`scripts/metron.py check` holds a declared budget against a run file that
something else wrote, and until now nothing in the plugin wrote one. The `time`
verb produces that file, so the file's shape is now an interface rather than a
convention: the check reads it, a contributor reads it when a budget fails, and
a later reader sets a `variance` from it.

Two things in the skill constrain the shape before any code is written.
`SKILL.md` asks the reader to repeat enough to see the spread and to read
durations at p95 and p99, and it lists latency reported as a mean among its red
flags. The check refuses a number sitting at the top level beside
`measurements`, because a document carrying values in two places would have one
of them dropped in silence.

A run file also outlives the command that produced it. It is read months later
by somebody comparing two numbers, and nothing in it can be recovered by asking
the machine that wrote it.

## Decision

One timed run writes one `metron-timed-run/v1` file whose `measurements` block
carries a single number, the aggregation of the kept samples that
`recorder.aggregation` names. The aggregation is `median` or `p95`, and there is
no mean. Beside it, `recorder.spread` carries `samples`, `min`, `p50`, `p95`,
`max` and `relative_spread`, which is `(max - min) / p50` or `null` when fewer
than two samples were kept or `p50` is zero. Percentiles are by nearest rank, so
every number in the spread is a sample that was recorded. Every recorder number
sits under `recorder`. No resource usage of the child is recorded. No run file
is written when any repetition failed, a discarded warm-up included.

## Alternatives

**A mean in the block.** One line of arithmetic, and the shape everybody
recognises. It loses to the skill's own rule: an outlying repetition moves a
mean and leaves nothing in the file saying it did, which is the reading
`SKILL.md` refuses in the prose the recorder is meant to serve.

**Interpolated percentiles.** A p95 of five samples would become a weighted
point between the fourth and fifth. It reads as more precision than five
samples hold, and it puts a number in the file that appears in no repetition,
so a reader cannot check it against the samples listed below it.

**Resource usage per repetition.** Recording `RUSAGE_CHILDREN` user time, system
time and max RSS would put memory beside wall clock for the same cost in
repetitions. The design record's probe settled it: `ru_maxrss` is a high-water
mark over every child the process has waited on, and it does not fall after a
small child follows a large one, so a per-repetition column would carry an
earlier repetition's number without saying so.

**A run file after a failed repetition, marking the failure.** It keeps the
samples that did complete. It also makes a passing check possible on a run that
did not finish, since the check reads `measurements` and would have to be taught
this file's failure convention to refuse it. Writing nothing keeps that
knowledge in one place.

**A separate spread file.** The check would keep the shape it already reads and
the recorder would write its evidence next door. The two files then travel apart,
and the one that survives is the one with no spread in it.

## Consequences

A budget's `variance` can be set from a measurement rather than from habit: run
`time` a few times on an unchanged tree and read `relative_spread`. A failing
budget can be read without rerunning anything, because the samples and the
bounds they ran under are in the file.

The block value moves with the aggregation, so two runs are comparable only when
`recorder.aggregation` agrees. A reader comparing numbers has to look.

Memory is out of reach for anyone using this recorder, and a workload whose cost
is resident size needs a different one. `relative_spread` is recorded unrounded,
so it is a long float in a file people read.

The shape is now something the check depends on. A field can be added under
`recorder`, and moving or renaming one is a change to `metron-timed-run/v1` and
to [the reference](../../../plugins/hexaemeron/skills/metron/references/budget-check.md)
that documents it.
