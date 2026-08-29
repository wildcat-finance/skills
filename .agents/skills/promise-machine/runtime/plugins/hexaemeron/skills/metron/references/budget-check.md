# The budget check

`scripts/metron.py` is the mechanical part of this skill: the file a budget is declared in,
and the comparison that holds a run to it. Everything else here stays a judgement.

It measures nothing. A run arrives from whatever produced it, the same division `hexctl`
uses for a lint exit. A tool that both measures and judges can be made to agree with itself.

## Declaring a budget

`metron-budgets.json`, checked in beside the code it governs:

```json
{
  "budgets": [
    {
      "name": "harvest.usdc.wall_clock",
      "unit": "s",
      "limit": 1200,
      "variance": 0.05,
      "direction": "lower_is_better"
    }
  ]
}
```

Every field is required.

- **`limit`** is the value past which a run fails whatever its history.
- **`variance`** is the fraction of the baseline inside which a move is another sample. It
  runs from 0 up to but not including 1.
- **`direction`** is `lower_is_better` or `higher_is_better`. Wall clock and bundle size are
  the first; throughput and hit rate are the second. For a higher-is-better budget the limit
  is a floor rather than a ceiling.

Both a limit and a variance, because one alone is not enough. A limit on its own fails a run
a fraction over on a noisy machine and passes a large regression that started under it. A
variance on its own never catches a value that was unacceptable from the day it was written.

## Recording a run

A run and a baseline hold the same shape, either bare or wrapped:

```json
{ "note": "batched the balance reads", "measurements": { "harvest.usdc.wall_clock": 1020 } }
```

A document carrying measurements in both places at once is refused rather than resolved,
because taking one shape would drop the other in silence.

## The verdicts

| Verdict | When | Exit |
| --- | --- | --- |
| `over-budget` | Worse than the limit | fails |
| `regressed` | Worse than the baseline by more than the variance | fails |
| `neutral` | Inside the variance either way | passes |
| `improved` | Better than the baseline by more than the variance | passes |
| `unmeasured` | The run carries no value for a declared budget | fails |
| `undeclared` | The run carries a value no budget declares | fails |

The last two are the absence rules, and they are the reason this is not a threshold script.
A run that quietly stops reporting a budget would otherwise pass, and a name nobody declared
is either a typo or a budget that was never written down.

Four smaller rules follow from the prose in `SKILL.md`:

- The limit is checked before the baseline. A ceiling does not care about drift.
- A budget with no baseline entry is neutral, not a failure. Failing it would block the
  commit that introduces the budget.
- A move exactly at the variance is neutral. A gain equal to the noise is another sample.
- A zero baseline admits no proportion, so any move off it in the wrong direction is a
  regression and nothing else is.

## Running it

```bash
python3 scripts/metron.py check \
  --budgets metron-budgets.json \
  --baseline metron-baseline.json \
  --run build/run.json

python3 scripts/metron.py check --budgets ... --run ... --format json
```

Exit 0 when every verdict passes, 1 when any fails, 2 on a bad invocation or a file that
cannot be read. `--baseline` is optional: without it the limits are still held and every
budget reports neutral against no history.

## The ledger

```bash
python3 scripts/metron.py record \
  --budgets metron-budgets.json --baseline metron-baseline.json \
  --run build/run.json --ledger metron-ledger.jsonl --note "batched the balance reads"
```

One JSON object per line, appended. It records the failing runs too, which is the point:
a revert leaves no trace in history, which is why the same dead idea comes back next quarter.

`--promote` writes the run over the baseline, and needs `--baseline` to say which file. The
write is atomic, so a baseline is either its old contents or its new ones.

## What it does not do

No measurement, no Solidity gas, no statistics beyond the declared variance, and no CI
workflow. Wiring it into a pipeline is a decision for the repository it guards.
