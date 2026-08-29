# Runbook: a metron budget file and the check that holds a run to it

Three steps, one pull request each, stacked. Both suites run at every boundary:

```text
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

The second is 214 of 215 at entry and stays there. `ForgeReports` errors because `forge`
cannot be installed in this container, which is true on `main` too.

## Step 1: The budget file, and refusing one that cannot be read

**Goal.** Ship the budget file format, its loader, and the fixture directory. A malformed
budget file is refused by name rather than raising.

**Entry.** The run branch `fiat/a-metron-budget-file-and-the-check-that-holds-a` off `main`
at `0d04c04`. Metron ships no code.

**Exit.** `metron.py` loads a budget file and refuses every malformed shape with a message
naming the field. The fixture carries budgets in both directions. Both suites green, the
Hexaemeron count up by the new tests.

**Files.**

- `plugins/hexaemeron/skills/metron/scripts/metron.py` (new: the loader and the CLI skeleton)
- `plugins/hexaemeron/tests/fixtures/metron/metron-budgets.json` (new)
- `plugins/hexaemeron/tests/test_metron_check.py` (new)
- `plugins/hexaemeron/docs/metron-budget-check/study.md` (new, the study)
- `plugins/hexaemeron/docs/metron-budget-check/runbook.md` (new, this file)

**Tests.** A budget file that loads. Each required field absent in turn. A `variance`
outside 0 to 1, a negative `limit`, a `direction` outside the two, a duplicate budget name,
a boolean where a number belongs, a top level that is not an object, a `budgets` that is
not a list, an entry that is not an object, and a file that is not JSON. Expect roughly 20
new tests.

## Step 2: The verdicts, the exit status, and the ledger

**Goal.** Compare a run against the budgets and the baseline, produce one of six verdicts
per budget, exit non-zero on any that fails, and record a run into the ledger.

**Entry.** Step 1's exit state.

**Exit.** `check` exits 1 on a deliberate regression fixture naming the budget and the
margin, exits 0 on a neutral one, and reports an improvement without failing. A run missing
a declared budget fails as `unmeasured`; a run carrying an undeclared name fails as
`undeclared`. `record` appends a run to the ledger and promotes it to baseline only when
asked. Both suites green.

**Files.**

- `plugins/hexaemeron/skills/metron/scripts/metron.py` (the comparison, the verdicts, the
  two subcommands)
- `plugins/hexaemeron/tests/fixtures/metron/metron-baseline.json` (new)
- `plugins/hexaemeron/tests/fixtures/metron/runs/*.json` (new: one per verdict)
- `plugins/hexaemeron/tests/test_metron_check.py` (the verdicts and the exit statuses)

**Tests.** One fixture per verdict, run through the command line and asserted on the exit
status as well as the text. Both directions. A zero baseline. A value exactly at the
variance edge, asserted to be the same verdict twice. A boolean measurement. A malformed
run and a malformed baseline. `record` appending twice, and refusing to promote without the
flag. Expect roughly 30 new tests.

## Step 3: Say so in the skill, then demonstrate

**Goal.** Give `SKILL.md` the section that names the check, add the reference a caller
follows, move the ledger, and run the demonstration from the study.

**Entry.** Step 2's exit state.

**Exit.** `SKILL.md` names the script and its two subcommands, and its Budgets section says
a budget is declared in a file the check reads. A reference document sets out the file
formats and the six verdicts. `EVOLUTION.md` carries one new row on the evolution axis with
a recomputed digest and a new held job. The demonstration from the study runs and behaves.
Both suites green.

**Files.**

- `plugins/hexaemeron/skills/metron/SKILL.md` (the section, and the frontmatter version)
- `plugins/hexaemeron/skills/metron/references/budget-check.md` (new)
- `plugins/hexaemeron/skills/metron/EVOLUTION.md`
- `plugins/hexaemeron/skills/metron/agents/openai.yaml` if its description names the surface

**Tests.** No new tests. `tests/test_evolution_contract.py` and the demonstration are the
proof.
