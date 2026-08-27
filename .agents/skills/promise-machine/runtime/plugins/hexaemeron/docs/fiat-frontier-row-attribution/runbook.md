# Runbook: subtract already-published rows from the frontier close gate

Derived from `.hexaemeron/study.md`. One step. It scaffolds, changes the gate,
and demonstrates, because the whole delivery is one function, its regressions
and the documents that describe it. Splitting it would hand the next step a
tree whose gate and tests disagree.

## Step 1: Attribute ledger rows to the run that published them

**Goal.** Make `frontier_close_fault` count only the rows a run added, by
subtracting the rows already present in the base it recorded at sync, and
refuse a run whose own row is not the newest.

**Entry.** Run branch `fiat/subtract-already-published-rows-from-the-frontie`
at `ea4d238abb3968d25542ac03e199619d4b7c6a73`, study receipt recorded, no
tracked changes in the run worktree.

**Exit.** `frontier_close_fault` takes the base's row versions and counts only
non-foreign rows after the anchor; `done_integrate` reads them from the ledger
blob at the recorded sync base commit through `bounded_git`, and passes an
empty set when there is no sync or the read fails. A run whose newest row is
foreign is refused. The integration receipt records the subtracted versions.
`plugins/hexaemeron/docs/fiat-frontier-row-attribution/study.md` and
`runbook.md` match the receipted artefacts, `EVOLUTION.md` carries one new
`fiat-v5.16.1` generation row, and Hexaemeron moves to `1.5.9` across all four
version surfaces. Prove it with:

```bash
cmp .hexaemeron/study.md plugins/hexaemeron/docs/fiat-frontier-row-attribution/study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-frontier-row-attribution/runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/tests/test_hexctl.py
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
```

The demonstration is `TestFrontierClose`, which replays the exact issue 466
topology: an anchor row, a foreign row published meanwhile, and one row of the
run's own. It passes here and fails against
`ea4d238abb3968d25542ac03e199619d4b7c6a73`.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`, `tests/test_evolution_contract.py`,
`plugins/hexaemeron/docs/fiat-frontier-row-attribution/study.md` and
`runbook.md`, `.hexaemeron/run-pr.md`, and `.horos/boundary.json` if the scan
earns an entry.

**Tests.** A new `TestFrontierClose` class in
`plugins/hexaemeron/tests/test_hexctl.py`, driving `frontier_close_fault`
directly over written ledger fixtures and driving `done integrate` through the
CLI. Cases: the issue 466 topology passes; the same topology refuses without a
subtracted set; a run adding two of its own rows refuses; a run whose newest
row is foreign refuses; a duplicated foreign label cannot subtract twice; an
unreadable base ledger falls back to today's count rather than passing; a run
with no sync keeps today's arithmetic; and the integration receipt records the
subtracted versions. Expect about 8 new tests, so roughly 908 Hexaemeron and
196 root. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-1.json`.

**Disciplines.** phylax: the step adds a git read of a historical blob and
parses its text, and it decides what the receipt persists. ephoros: the refusal
text and the recorded subtracted versions are what answer why a frontier
receipt was refused. metron: none, one bounded read per run and no performance
claim. elenchus: a failure in hand at entry, the recorded refusal from the
issue 466 run, worked under the runner contract above. hypomnema: the ledger
row is the record; the study's item 12 states why no ADR is earned.
