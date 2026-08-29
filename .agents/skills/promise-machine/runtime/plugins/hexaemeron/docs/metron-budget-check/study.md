# Study: a metron budget file and the check that holds a run to it

## Assumptions

Assuming, unless corrected:

1. Python 3.9 upward, standard library only, `unittest`, matching the sibling checks.
   `from __future__ import annotations` so the annotation style matches `ephoros.py`.
2. The starting ref is `main` at `0d04c04`, which carries the receipted lint round.
3. Metron ships no code today: `SKILL.md`, `EVOLUTION.md` and an agent card. Its three
   sibling phase skills each ship `scripts/<name>.py` and a test file in
   `plugins/hexaemeron/tests/`, so this check follows that shape rather than inventing one.
4. This check does not measure anything. It reads numbers a caller produced, the same way
   `hexctl audit-round` reads a lint exit a caller produced. Measuring is the caller's job
   under `SKILL.md`.
5. `forge` cannot be installed in this container, so
   `test_elenchus_checker.ForgeReports` errors here and on `main`. Node was raised to
   v26.6.0 locally, giving a baseline of 214 of 215.
6. This run is driven by the installed controller, refreshed after #206 merged, so its own
   audit rounds record the three lint exits. It is the first run governed by that contract.

## Problem statement

`SKILL.md` says it plainly: "A budget nobody checks in CI is a preference." Metron sets
out a table of budgets, a variance rule, and a keep-or-revert decision, and every one of
those depends on a person choosing to do it. Nothing in the plugin can be run.

This run ships the mechanical part: a budget file, and a check that reads a recorded run,
compares it against a stored baseline, and fails when a named budget regresses beyond the
variance that budget declares.

A working prototype means all of these hold:

```text
python3 plugins/hexaemeron/skills/metron/scripts/metron.py check \
  --budgets <fixture>/metron-budgets.json \
  --baseline <fixture>/metron-baseline.json \
  --run <fixture>/runs/regressed.json      # exits 1, naming the budget and the margin

python3 .../metron.py check --run <fixture>/runs/neutral.json ...   # exits 0
python3 .../metron.py record --run <fixture>/runs/neutral.json --ledger <path>
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

## Prior art

**In this repository.**

- `plugins/hexaemeron/skills/metron/SKILL.md` is the contract. Four refusals, a
  keep-or-revert table, a budget table with three web signals, the rule that a gain inside
  run-to-run variance is another sample rather than a gain, and the instruction to read
  durations at p95 and p99 because the mean hides the worst experience.
- `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, 203 lines, is the house shape for
  one of these: a module docstring listing coded rules, `argparse` with
  `--format {text,json}`, `main(argv) -> int`, exit 0 clean, 1 findings, 2 bad invocation.
  `phylax` and `hypomnema` follow it too.
- `plugins/hexaemeron/tests/test_ephoros_checker.py` loads the script by path with
  `importlib`, and its docstring makes the point that the neighbours matter as much as the
  specimens.
- `hexctl audit-round` now takes a lint exit the caller reports rather than running the
  lint. The same division applies here, and for the same reason: a tool that both measures
  and judges can be made to agree with itself.
- `plugins/hermes` owns Solidity gas and is explicitly out of scope in `SKILL.md`.

**Outside.** Lighthouse CI's `assert` step and `size-limit` both compare a measured value
against a declared budget and exit non-zero. Neither carries a variance, which is the part
Metron's own prose insists on: a threshold with no noise band turns every re-run into a
verdict.

## Constraints and non-goals

**Constraints.**

- Standard library only. No new dependency.
- Both suites green at every step boundary.
- The check must be usable from CI with no arguments beyond file paths.
- A budget file and a baseline are checked in, so both are prose a reviewer reads. They
  stay small, ordered and diff-friendly.

**Non-goals.**

- The check does not measure. It reads a run a caller recorded.
- No Solidity gas. `hermes` owns that.
- No CI workflow. Touching CI is ask-first under this study, and the repository runs no
  workflow over the Hexaemeron suite at all, which is recorded separately.
- No statistical machinery beyond a declared variance. No confidence intervals, no
  distribution fitting.
- No change to `hexctl` or to any sibling skill.

## Design options

**Option A: a threshold check.** Each budget declares a limit; a run fails when it exceeds
it.

Trade: cheap, and it contradicts the skill it serves. A limit with no noise band fails a
run that is 0.4% over on a noisy machine and passes a 40% regression that started under
the limit.

**Option B: a baseline comparison.** Each budget declares a variance; a run fails when it
is worse than the stored baseline by more than that.

Trade: catches drift, and never catches a value that was always unacceptable. A route that
has been at 900ms since it was written stays green forever.

**Option C: both, reported separately.** A budget carries a limit and a variance. A run
fails if it exceeds the limit, and fails if it regresses past the baseline by more than the
variance. A move inside the variance is neutral, which is the skill's "another sample". An
improvement past the variance is reported as one.

Trade: two ways to fail and four verdicts to explain, against a check that says what the
skill says.

**Chosen: C.** A and B each drop half of what `SKILL.md` asks for. The verdict vocabulary
is the cost, and it is the same vocabulary the keep-or-revert table already uses, so a
reader of the skill already has it.

Two smaller decisions, both taken to match the skill rather than the shortest code:

- **Direction is declared per budget.** Wall clock and bundle size are lower-is-better;
  throughput and hit rate are not. A check that assumes lower-is-better would call a
  throughput improvement a regression.
- **Variance is a fraction of the baseline, not an absolute.** The skill's example is
  "three percent inside five percent", which is proportional.

## The shape

A budget file, `metron-budgets.json`:

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

A baseline, `metron-baseline.json`, mapping a budget name to the value it was last kept at.
A run, the same mapping, produced by whatever measured it.

Verdicts per budget, and what each does to the exit status:

| Verdict | When | Exit |
| --- | --- | --- |
| `over-budget` | The run is worse than `limit` | fails |
| `regressed` | Worse than the baseline by more than `variance` | fails |
| `neutral` | Inside `variance` either way | passes |
| `improved` | Better than the baseline by more than `variance` | passes |
| `unmeasured` | The run carries no value for a declared budget | fails |
| `undeclared` | The run carries a value no budget declares | fails |

The last two are the absence rules. A run that quietly stops reporting a budget would
otherwise pass, and a run reporting a name nobody declared is either a typo or a budget
that was never written down.

`record` writes a run into a ledger, which is the file `SKILL.md` already asks for, and
promotes it to baseline only when asked.

## Risk register seed

- **Absence passing as success.** The failure this predicate class keeps producing. A
  missing measurement, a budget silently dropped from the file, a baseline with no entry
  for a declared budget. Each has to be a verdict rather than a skipped iteration.
- **Untrusted input.** All three files come from outside the process. Bounded reads, no
  `eval`, every field type-checked before arithmetic, and a refusal rather than a traceback
  on a malformed file, as `hexctl` now does.
- **The bool-is-an-int trap.** Hit twice in the last two runs. `True` is a number in Python
  and would arrive as a measurement.
- **Division by a zero baseline.** A proportional variance against a baseline of zero has
  no meaning, and `0` is a legitimate measurement for a count.
- **Direction inverted.** Getting `higher_is_better` backwards turns every improvement into
  a failure, which is worse than not shipping the check.
- **Float comparison at the boundary.** A run exactly at the variance edge must fall on one
  declared side, and the same input must always give the same verdict.
- **A ledger that grows without bound**, or one a concurrent writer corrupts.

## Glossary seeds

- **Budget.** A named signal with a unit, a limit, a variance and a direction.
- **Limit.** The value past which a run fails regardless of history.
- **Variance.** The fraction of the baseline inside which a change is another sample.
- **Baseline.** The value a budget was last kept at.
- **Run.** One recorded set of measurements.
- **Verdict.** One of the six above, per budget.
- **Ledger.** The append-only record of runs, including reverted attempts.

## Boundaries

**Always.**

- Both suites before every commit.
- The imprimatur lint on every shipped document.
- The three bundled lints in every audit round of this run, recorded as exits on the round.
- A fixture for every verdict, including the two absence ones.

**Ask first.**

- Adding a dependency. This run intends none.
- Touching CI, including adding a workflow that would run this check.
- Changing `hexctl`, `SKILL.md`'s refusals, or any sibling skill.
- Changing the three web-signal budget values in `SKILL.md`, which are external standards
  rather than this repository's opinion.

**Never.**

- Measure anything and report it as though a caller had.
- Let a missing measurement pass as a pass.
- Delete or skip a failing test to make a suite pass.
- Claim the Hexaemeron suite is green while `ForgeReports` errors; report 214 of 215 and
  say why.

## Sources

- `plugins/hexaemeron/skills/metron/SKILL.md` -- the contract, the variance rule, the
  keep-or-revert table and the ledger.
- `plugins/hexaemeron/skills/metron/EVOLUTION.md` -- the held frontier and its acceptance
  condition.
- `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` and
  `plugins/hexaemeron/tests/test_ephoros_checker.py` -- the house shape for a bundled check
  and its tests.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` -- the caller-reports division of
  labour, and `as_dict` as the guard for a file nothing validates.
- `audit/AUDIT.md` -- the Ariadne and Fiat runs, for the recurring fault this risk register
  is written against.
