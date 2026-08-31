---
name: metron
description: >-
  Change performance only against a recorded measurement: baseline first, one
  change at a time, re-measure the same way, then keep it or revert it. Use
  when something is slow, when a budget exists, when a change might have cost
  time, or when a profile is needed before touching code. Do not use it for
  Solidity gas, which belongs to hermes and its Foundry loop, and do not use it
  for something that is broken rather than slow, which belongs to elenchus.
metadata:
  version: "1.1.0"
---

<p align="center">
  <img src="../../assets/characters/metron.png" width="1200">
</p>

# Metron

From *metron*, the measure. The name is the rule: nothing here happens without
a number, and the number comes first.

## Where this sits

Metron owns every measurement except gas: the page, the route, the query, the
harvest, the release build.

Hermes owns Solidity gas and its Foundry evidence. Elenchus owns something that
has failed rather than something that is slow. Fiat and Mason apply Metron
during implementation when a performance claim or budget exists; Metron
returns the measured keep-or-revert decision and does not control the delivery.

Synkrisis may surface an association between recorded run facts, but that is
not a Metron measurement. Its suggestion still requires the same controlled
baseline and re-measurement.

Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

**Current state.** Metron ships the budget check, so a declared budget is held mechanically, and nothing in the plugin produces the measurement it reads.

## Refuse these four

1. No baseline, no change. A performance edit with no recorded before is an
   opinion with a diff attached.
2. No re-measurement, no keep. The change is a hypothesis until measured the
   second time.
3. Neutral is a revert. A change that does not beat the noise costs
   maintenance forever and bought nothing.
4. Red suite, no win. A number that improved because the code stopped doing
   something the product needed is a regression.

## The loop

Measure, find the actual bottleneck, change one thing, measure again the same
way, then keep or revert, and guard what you kept.

Change one thing at a time. Three edits landed together produce a single
number that cannot be attributed to any of them. If they must ship together,
measure each alone first.

## Measure how you will re-measure

Same command, same conditions, same fixed budget of wall clock or samples or
requests. A baseline on a cold cache against a result on a warm one measures
the cache.

Repeat enough to see the spread, then compare the change against it. A gain of
three percent inside five percent of run-to-run variance is not a gain; it is
another sample. Read durations at p95 and p99, because the mean is where the
worst experience goes to hide.

## Where to look first

Let the symptom pick the instrument.

- **The page takes too long to appear.** Bundle size, then server response
  time, then whatever blocks the render.
- **Interaction feels sluggish.** Long tasks on the main thread, then
  re-renders from unstable props.
- **One route is slow.** Query count before query speed. An index is worth
  measuring only once the count is right.
- **A harvest is slow.** Time per interval and round trips per interval.
  Latency multiplied by requests is usually the whole answer.
- **A release build is slow.** Digest work against file reads, measured
  separately.

## The usual causes here

A query inside a loop is the oldest one. Prisma reaches related rows through
`include`, and Apollo can ask for the whole shape in one document rather than
one per row. Where a list has no bound, `take` and `skip` give it one.

Round trips dominate anything that talks to a chain. Batch calls where the
provider allows it, and prefer one multicall to twenty reads. The same holds in
Python: a loop that touches a preserved capture once per item pays the read
every time, and reading once into memory is the fix when the capture fits.

On the client, a new object literal in a render gives every child a fresh
prop, so hoist it or memoise it. Heavy and rarely used components load
dynamically. Reach for `memo` and `useMemo` against a measurement, since
scattering them costs renders of its own.

## Budgets

| Signal | Good | Needs work | Poor |
| --- | --- | --- | --- |
| Largest contentful paint | 2.5s or less | 4.0s or less | over 4.0s |
| Interaction to next paint | 200ms or less | 500ms or less | over 500ms |
| Cumulative layout shift | 0.1 or less | 0.25 or less | over 0.25 |

Set the rest from what the product needs rather than from habit: a p95 for each
route, a ceiling on the initial bundle, a wall-clock bound on a full harvest.
A budget nobody checks in CI is a preference.

So declare them in a file and run the check over it:

```bash
python3 scripts/metron.py check \
  --budgets metron-budgets.json --baseline metron-baseline.json --run build/run.json
```

A budget carries a limit, a variance and a direction. The check compares a recorded run
against the limit and against the stored baseline, and exits non-zero when a budget is past
its ceiling, when it regressed past its variance, when the run stopped reporting it, or when
the run reports a name no budget declares. A move inside the variance is another sample, as
above. `record` keeps the ledger below, including the reverted attempts.

It measures nothing itself. The run comes from whatever measured it.
[`references/budget-check.md`](references/budget-check.md) has the file formats and the six
verdicts.

## Keep or revert

| Result against baseline | Action | Reason |
| --- | --- | --- |
| Past the threshold, suite green | Keep, with both numbers in the message | It paid for itself |
| Inside the noise | Revert | Complexity with nothing bought |
| Worse | Revert | The hypothesis was wrong |
| Better, but a test went red | Revert | A regression in a win's clothing |

The third row is the one teams skip. The change is already written, discarding
it feels wasteful, and so it lands unmeasured and is maintained forever.

## Log every attempt, including the reverted ones

A revert leaves no trace in history, which is why the same dead idea comes back
next quarter. Keep a short ledger where the next person will read it, in the
pull request or in a file beside the code.

| Idea | Baseline to result | Verdict | Why |
| --- | --- | --- | --- |
| Memoise the row component | 240ms to 235ms | reverted | Inside noise; rows were not the cost |
| Virtualise the list | 240ms to 90ms | kept | Long tasks gone from the trace |
| Batch the balance reads | 41 calls to 3 | kept | Round trips were the whole cost |

## Correctness gates the number

The suite stays green and the number moves. Both, or neither counts.

An optimisation that wins by dropping work is not one. Skipping a validation,
caching something that has to be fresh, removing an await that was holding
order, or relaxing a digest check each buy time by removing a guarantee. In a
credit protocol that trade is not yours to make quietly; it belongs in the
study, with the risk written down.

## Rationalisations

- "We will optimise later." Anti-patterns compound and micro-optimisations do
  not. Fix the first now, defer the second.
- "It is fast on my machine." Your machine is not the network, the phone, or
  the archive node under load.
- "This one is obvious." Then measuring is cheap and settles it.
- "Nobody notices a hundred milliseconds." They notice, and on a signing flow
  they hesitate.
- "It did not help much, but it does not hurt." It does. You maintain it
  forever and got nothing.
- "We already wrote it." The measurement does not care how long it took.
- "The win is obvious, no need to re-measure." Then the second run is quick
  and makes it a fact.

## Red flags

- A performance change with no profile behind it.
- One number covering several edits, so none can be attributed.
- A query inside a loop, or a list endpoint with no bound.
- Latency reported as a mean.
- Bundle size growing with nobody watching.
- `memo` and `useMemo` scattered without a measurement.
- Neutral changes kept because they were already written.
- A win that needed a test changed, skipped or deleted.
- The same failed idea tried twice because nobody wrote down the first.

## Before the change is receipted

Report the count, then name every item that failed.

- [ ] Baseline and result exist as specific numbers, taken the same way.
- [ ] The improvement is larger than run-to-run variance.
- [ ] One change is responsible, or each was measured alone first.
- [ ] Anything that did not beat the baseline was reverted.
- [ ] The attempt ledger records this run, kept or reverted.
- [ ] The bottleneck is named, not assumed.
- [ ] Budgets in scope still pass.
- [ ] No new query sits inside a loop.
- [ ] The suite is green, and nothing was skipped to make it so.

## Hand back

Lead with the verdict: kept with the numbers, or reverted with the numbers.
Give baseline and result in the same units, taken the same way.

Separate the measured from the inferred. The number is measured. Why it moved
is inferred until a second measurement isolates it, and a bottleneck you
believe rather than profiled gets named as a belief.

End with one action: the next thing worth measuring, the budget that needs a
threshold, or the reverted idea somebody should stop suggesting.

## Promise Machine contract

### metron-budget-verdict

- Promise: A budget verdict establishes that a named workload was measured against a stated threshold with a fixed command, environment, inputs, repetitions and aggregation rule.
- Evidence: The benchmark identity, environment, input fixture, warm-up and repetition policy, raw or preserved measurements, aggregation method, variance and threshold comparison.
- Evidence classes: measured, recorded
- Boundary: The verdict applies only to the recorded workload and measurement method; it does not generalise to other machines, inputs, workloads or correctness.
- Authorises: Accepting or refusing the measured subject against the named budget without strengthening the result beyond its measurement boundary.
- Consequence: 1
- Refuses: A missing baseline, changed method, mean-only latency, result inside unexplained noise, unbounded workload or comparison across unlike environments.
- Recovery: Freeze one reproducible method, establish the baseline and variance, rerun the exact workload and compare it to the stated threshold.
- Exceptions: none

### metron-change-decision

- Promise: A keep decision establishes that one isolated change improved the named measurement beyond variance while the correctness gates remained green; otherwise the attempted change is reverted and recorded.
- Evidence: Before and after measurements taken the same way, isolated change diff, variance, correctness-suite results, budget results and the attempt-ledger verdict.
- Evidence classes: measured, checked, recorded
- Boundary: The decision proves the measured effect of the isolated change on the named workload, not its effect on unmeasured workloads or the reason for the movement unless separately isolated.
- Authorises: Keeping the change only when both the measured improvement and correctness gates pass, or recording and abandoning it otherwise.
- Consequence: 2
- Refuses: Several unisolated edits, an unmeasured optimisation, a neutral or noisy result, a red or weakened correctness gate, or a speed gain bought by removing a guarantee.
- Recovery: Revert the candidate, restore the baseline, isolate one hypothesis, repeat the same measurement and record the new verdict whether kept or rejected.
- Exceptions: none
