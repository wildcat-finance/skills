# The budget check

`scripts/metron.py` is the mechanical part of this skill: the file a budget is declared in,
and the comparison that holds a run to it. Everything else here stays a judgement.

The check judges and does not measure. A run arrives from whatever produced it, the same
division `hexctl` uses for a lint exit. A tool that both measures and judges can be made to
agree with itself. `time` is the one recorder shipped beside the check, and it writes the
file rather than reading it.

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

## Timing a command

`time` runs one fixed argv and writes the run file the check reads. The command goes after
`--`, as a list, with no shell between it and the process:

```bash
python3 scripts/metron.py time \
  --name harvest.usdc.wall_clock --out build/run.json \
  --repeat 5 --warmup 2 --aggregate median \
  --timeout-seconds 600 --expect-exit 0 --cwd . --note "cold cache" \
  -- ./harvest --market usdc
```

`--name` and `--out` are required. `--repeat` is 1 to 1000 and defaults to 1. `--warmup` is
0 to 100 and defaults to 0; a warm-up repetition runs under the same timeout and output cap
as a kept one and records nothing. `--aggregate` is `median` or `p95` and defaults to
`median`. Every duration is wall clock in milliseconds, so a budget declared in seconds is
held to a number a thousand times its size: declare `"unit": "ms"` for a budget this
recorder measures.

The run file:

```json
{
  "measurements": { "harvest.usdc.wall_clock": 1020.5 },
  "recorder": {
    "schema": "metron-timed-run/v1",
    "argv": ["./harvest", "--market", "usdc"],
    "cwd": "/srv/harvester",
    "repeat": 5, "warmup": 2, "timeout_ms": 600000, "expect_exit": 0,
    "unit": "ms", "aggregation": "median",
    "spread": {
      "samples": 5, "min": 1004.1, "p50": 1020.5, "p95": 1188.0, "max": 1188.0,
      "relative_spread": 0.18020578147966682
    },
    "repetitions": [
      { "index": 1, "wall_clock_ms": 1004.1, "exit": 0,
        "stdout_bytes": 512, "stderr_bytes": 0 }
    ],
    "recorded_at": "2026-09-07T09:00:00+00:00",
    "platform": "Linux-6.8.0-x86_64", "python": "3.14.6"
  }
}
```

The value in `measurements` is the aggregation `recorder.aggregation` names, taken from the
kept samples and rounded to three decimals. Percentiles are by nearest rank, so every number
in `spread` is a sample that was recorded rather than an interpolation between two of them,
and `p95` of five samples is the largest. There is no mean to ask for; `SKILL.md` reads
durations at p95 and lists latency reported as a mean among its red flags. Every recorder
number sits under `recorder`, because a number beside `measurements` is a stray measurement
the check refuses.

`relative_spread` is `(max - min) / p50`, or `null` when fewer than two samples were kept or
`p50` is zero. It is recorded unrounded, so it recomputes from the three numbers beside it.
It is also the number a budget's `variance` is set from: run `time` a few times on
an unchanged tree, take the largest `relative_spread` you see, and declare a variance at
least that wide. A variance below the machine's own run-to-run noise reports a regression
every time the noise goes the wrong way. The reasoning behind this file's shape is in
`adr/record-timed-runs-at-the-median-with-spread`.

Exit 0 with the run file written atomically. Exit 1 when any repetition failed, a warm-up
included: the command exited other than `--expect-exit`, ran past `--timeout-seconds`, wrote
more than 1 MiB to a stream, or left a process outside its group holding the pipes. One
stderr line names the repetition and the cause, and no run file is written, so a file the
check can read has every repetition green. Exit 2 on a bad invocation, an argument outside
its bounds, a command that cannot start, or an `--out` that cannot be written. A run file
already at `--out` keeps its previous bytes through both refusals.

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

The check does no measurement; the separate `time` command records it. Neither
handles Solidity gas or installs a CI workflow. Comparison uses the declared variance. Wiring it into a pipeline is a decision for the repository it guards.
