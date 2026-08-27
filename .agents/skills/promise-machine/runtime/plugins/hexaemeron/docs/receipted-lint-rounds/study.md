# Study: receipted lint results on hexctl audit-round

## Assumptions

Assuming, unless corrected:

1. Python 3.9 upward, standard library only, `unittest`, matching the rest of the
   repository. `hexctl` imports nothing outside the standard library today.
2. The starting ref is `main` at `f7d76cf`, which carries the Ariadne dataset
   predicate and the Elenchus structured-reports work.
3. This run is driven by the *installed* controller under
   `~/.claude/plugins/cache/wildcat-labs/hexaemeron/1.3.0/`, which is byte-identical
   to the checkout copy at the starting ref. The change lands in the checkout, so the
   demonstration runs the checkout copy against a throwaway state directory rather
   than against this run's own state.
4. `forge` cannot be installed in this container: the proxy refuses
   `foundry.paradigm.xyz` and GitHub releases. `test_elenchus_checker.ForgeReports`
   therefore errors on `main` and will keep erroring. Node was raised to v26.6.0 so the
   sibling Node fixture passes, giving a baseline of 176 of 177.

## Problem statement

`audit-round` records a findings count, a log path and a fixes commit. When a step
ships no Solidity, the round's mechanical part is three bundled lints -- `phylax`,
`ephoros` and `hypomnema` -- and the controller neither asks for their results nor
notices when they are absent. Their outcomes live only as prose someone typed into
`audit/AUDIT.md`, which the controller never reads.

That is the gap. A run can record a clean non-Solidity round having executed nothing,
and the ledger cannot tell the difference between a round whose lints passed and a
round whose lints were skipped.

This run teaches `hexctl` to take the three results as structured fields and to refuse
a non-Solidity round without them.

A working prototype means all three of these hold:

```text
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
```

and, against a throwaway state directory:

```text
hexctl audit-round --findings 0                      # refused, names the three flags
hexctl audit-round --findings 0 --phylax-exit 0 \
  --ephoros-exit 0 --hypomnema-exit 0                # accepted, records all three
```

## Prior art

**In this repository.**

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, 1207 lines.
  `cmd_audit_round` is the function to change; `done_audit` reads the rounds it
  wrote; `next` reports the round number and the prior findings count.
- `DEFAULT_CONFIG` carries `"solidity": "auto"`. Nothing reads it. It is the only
  dead key in that table, and it is exactly the switch this job needs.
- The `security_suite` receipt is the one existing signal for whether the Pashov
  pair applies. `record security_suite '["hexaemeron:x-ray", ...]'` stores a list;
  `record security_suite '"waived: <reason>"'` stores a string. `cmd_audit_round`
  already refuses to run without that receipt.
- `references/audit-loop.md` states the rule this job enforces: for a non-Solidity
  step, run the three lints and "require exit 0 from each", and "a non-zero exit is
  a finding like any other".
- `plugins/hexaemeron/tests/test_hexctl.py`, 800 lines, calls `audit-round` at 21
  sites. Most are non-Solidity in shape and will need the new fields.
- The three lint scripts live at `plugins/hexaemeron/skills/<name>/scripts/<name>.py`
  and exit 0 when clean, non-zero otherwise.

**From the Ariadne run that just landed.** Its audit spent eight rounds on one
recurring fault: a field that satisfies a shape check while carrying no evidence.
That is the trap here. `--phylax clean` would be a word the caller types, indistinguishable
from a lint nobody ran. An exit status is a number the lint produced.

## Constraints and non-goals

**Constraints.**

- Standard library only. No new dependency.
- Existing state files must keep loading. Archived runs hold rounds with no lint
  fields, and `status`, `next` and `verify` read them.
- A Solidity round must not be forced to carry lint fields it has no use for.
- The repository suite and the Hexaemeron suite are the gate:
  `python3 -m unittest discover -s tests` and
  `python3 plugins/hexaemeron/tests/run_tests.py`.

**Non-goals.**

- `hexctl` will not run the lints itself. It records what the caller reports, the
  same way it records a findings count and a commit SHA. Running them is the agent's
  job under `references/audit-loop.md`.
- No change to the seven-phase loop, the branch model, or any other receipt.
- No change to the three lint scripts.
- Nothing that reads the audit log. The log stays prose for humans.

## Design options

**Option A: a closed vocabulary per lint.** `--phylax clean|findings`.

Trade: three words the caller types. A skipped lint and a passing lint are the same
keystroke, which is the fault the Ariadne audit spent eight rounds on.

**Option B: exit status per lint.** `--phylax-exit N`, `--ephoros-exit N`,
`--hypomnema-exit N`, each a non-negative integer, required on a non-Solidity round.

Trade: three more flags on the busiest command, and the caller can still type a
number the lint did not return. It cannot be typed *accidentally*: a caller who ran
nothing has no number to hand, where "clean" is always to hand.

**Option C: exit status plus a consistency rule.** Option B, and `audit-round`
refuses `--findings 0` when any recorded exit is non-zero.

Trade: one more refusal to explain. It buys the thing the ledger cannot currently
say: that a round reported as clean is consistent with the lints it reports.

**Chosen: C.** B alone would let a round record `phylax-exit 1` beside
`findings 0`, which is the same silence in a new place -- the log would say a lint
failed and the ledger would say the round was clean. The rule is four lines and it
makes the two halves of the receipt agree.

For deciding *which* rounds must carry the fields, the `security_suite` receipt is
the evidence already on the ledger: a waiver string means the Pashov pair did not
run, which is what "non-Solidity round" means in `references/audit-loop.md`. The dead
`solidity` config key becomes the override: `auto` infers from the receipt, `true`
treats every round as Solidity, `false` treats every round as non-Solidity.

## Risk register seed

- **Backward compatibility.** Rounds already on disk carry none of these fields.
  Every reader (`done_audit`, `next`, `status`, `verify`) must treat them as absent
  rather than assume them. An archived run that stops loading is a broken ledger.
- **The refusal firing on a Solidity run.** A repo that records a real suite must not
  be asked for lint exits. Getting the classification backwards blocks every
  Solidity round in the marketplace.
- **A waiver that is not a waiver.** The receipt is free-form: `"waived: ..."`,
  `"Waived: ..."`, a list, or something a caller invented. The classifier must have
  one rule, stated, and must not guess.
- **Integer parsing.** `--phylax-exit` takes a shell-supplied value. A negative
  number, a float, or a word must be refused by the parser rather than stored.
- **The consistency rule inverted.** Refusing a legitimate round is worse than
  accepting a sloppy one, because it stops work. The rule must fire only on the exact
  contradiction: a zero findings count beside a non-zero exit.
- **Test churn hiding a regression.** 21 call sites change. A mechanical edit across
  all of them could mask a real behaviour change, so the diff needs reading
  per-site rather than trusting a pass.

## Glossary seeds

- **Non-Solidity round.** An audit round whose `security_suite` receipt is a waiver,
  or whose run sets `solidity` to `false`.
- **Lint exit.** The integer a bundled lint returned. Zero is clean.
- **The three lints.** `phylax`, `ephoros`, `hypomnema`, bundled in this plugin.
- **Consistency rule.** A round may not report zero findings while reporting a
  non-zero lint exit.
- **Classifier.** The function deciding whether a round must carry lint fields.

## Boundaries

**Always.**

- Both suites before every commit.
- The imprimatur lint on every shipped document.
- The three bundled lints in every audit round of this run, which is itself a
  non-Solidity run.
- A state file written by the old controller must still load.

**Ask first.**

- Adding a dependency. This run intends none.
- Changing any receipt other than `audit-round`, or any phase ordering.
- Renaming or removing an existing flag.
- Touching CI.
- Changing the three lint scripts.

**Never.**

- Make `hexctl` run a lint and report a result nobody watched.
- Accept a lint result on a round where the lint did not run.
- Delete or skip a failing test to make a suite pass.
- Claim the Hexaemeron suite is green while `ForgeReports` errors; report 176 of 177
  and say why.

## Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` -- `cmd_audit_round`,
  `done_audit`, `DEFAULT_CONFIG`, the `next` state machine.
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md` -- the non-Solidity
  section that states the rule being enforced.
- `plugins/hexaemeron/skills/fiat/SKILL.md` -- the receipt table that has to change.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md` -- the held frontier and its
  acceptance condition.
- `plugins/hexaemeron/tests/test_hexctl.py` -- the controller's own tests.
- `audit/AUDIT.md`, Ariadne step 4 rounds 1 to 8 -- the evidence that a
  presence-checked field carrying no evidence is what to design against here.
