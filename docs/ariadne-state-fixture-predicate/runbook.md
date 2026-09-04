# Runbook: the Ariadne state-fixture predicate

Five steps, one pull request each, stacked. Both suites run at every boundary:

```text
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
```

Step 1 stands alone: it closes a hole on a shipped type and could be reviewed and merged
without the rest.

## Step 1: Close the gate 5 hole on the Solidity release predicate

**Goal.** Check the current side of a comparison on both branches, so a first release cannot
name a side with no name and a digest the statement does not cover.

**Entry.** The run branch `fiat/the-ariadne-state-fixture-predicate-and-the-gate` off `main` at
`271c7b8`. The hole is live and reproduced in the study.

**Exit.** A first-release statement whose current side is unnamed or uncovered fails gate 5. A
new conformance fixture exercises that branch and breaches gate 5 alone. Every existing Solidity
fixture and test still passes. Both suites green.

**Files.**

- `plugins/ariadne/scripts/ariadne_lib/predicates/solidity_release.py`
- `plugins/ariadne/tests/fixtures/conformance/fail-gate5-solidity-first-release-unnamed-current.json`
- `plugins/ariadne/tests/test_solidity_release.py`
- `plugins/ariadne/docs/conformance.md`
- `plugins/ariadne/docs/state-fixture-predicate/study.md` and `runbook.md` (new)

**Tests.** The current side absent, unnamed, undigested, and carrying a digest the statement does
not cover, each on a null baseline. A legitimate first release still passing. Expect roughly 8
new tests.

## Step 2: The predicate module and its published schema

**Goal.** Register `https://ariadne.wildcat.finance/state-fixture/v1` with its field tables, its
gates 2 and 5, its evidence and replay checks, and a published schema held to the module.

**Entry.** Step 1's exit state.

**Exit.** `ariadne predicates` lists three types. A state-fixture statement verifies with no gate
reported unchecked. The three evidence class names are read from Lazarus rather than restated.
Both suites green.

**Files.**

- `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py` (new)
- `plugins/ariadne/scripts/ariadne_lib/predicates/__init__.py`
- `plugins/ariadne/schemas/state-fixture-v1.json` (new)
- `plugins/ariadne/tests/test_state_fixture.py` (new)
- `plugins/ariadne/tests/test_schema_drift.py`, `test_docs.py`, `test_cli.py`
- `plugins/ariadne/docs/state-fixture.md` (new)

**Tests.** Gate 2 with each pin field absent, a hex block number, a component digest the
statement does not cover. The evidence check with a class key absent, a negative count, a boolean
count, and a proof-backed count with no state root. The replay check with each field absent and
with either flipped true. One test reading the class names out of Lazarus's own module. Expect
roughly 35 new tests.

## Step 3: Conformance fixtures for the new type

**Goal.** A passing fixture and one per breach, so another implementation can check itself.

**Entry.** Step 2's exit state.

**Exit.** Every new fixture breaches its named gate or check alone. The completeness tests already
in the suite pass without being relaxed. Both suites green.

**Files.**

- `plugins/ariadne/tests/fixtures/conformance/pass-state-fixture-*.json` (new)
- `plugins/ariadne/tests/fixtures/conformance/fail-gate2-state-fixture-*.json` (new)
- `plugins/ariadne/tests/fixtures/conformance/fail-gate5-state-fixture-*.json` (new)
- `plugins/ariadne/tests/fixtures/conformance/fail-check-evidence-*.json` (new)
- `plugins/ariadne/tests/fixtures/conformance/fail-check-replay-*.json` (new)
- `plugins/ariadne/docs/conformance.md`

**Tests.** The existing conformance tests extend to the new fixtures with no change to their
rules. Expect roughly 6 new fixtures.

## Step 4: The capture path over a Lazarus fixture

**Goal.** Read a Lazarus fixture directory into a statement, taking the evidence counts from its
manifest rather than computing them.

**Entry.** Step 3's exit state.

**Exit.** `capture-state-fixture` over `plugins/lazarus/examples/aave-v4-spoke-v0` writes a statement
`verify` passes with no unchecked gate. A fixture whose manifest and components disagree is
refused. Both suites green.

**Files.**

- `plugins/ariadne/scripts/ariadne_lib/capture/state_fixture.py` (new)
- `plugins/ariadne/scripts/ariadne_lib/capture/__init__.py`
- `plugins/ariadne/scripts/ariadne.py`
- `plugins/ariadne/tests/test_capture_state_fixture.py` (new)
- `plugins/ariadne/docs/capturing-a-state-fixture.md` (new)

**Tests.** The Aave v4 fixture captured and verified. A missing manifest, a missing header, a
component the manifest declares and the directory lacks, a digest that disagrees, a path leaving
the directory, and `--out` written atomically. Expect roughly 20 new tests.

## Step 5: Demonstrate, then reconcile the ledger and the marketplace prose

**Goal.** Run the demo path, move the ledger, and bring every surface stating Ariadne's frontier
into agreement.

**Entry.** Step 4's exit state.

**Exit.** The demo path exits 0 with seven gate lines and none unchecked. `EVOLUTION.md` carries
one new row on the evolution axis with a recomputed digest. Every marketplace-context block, the
root selection table and the landing README agree. Both suites green.

**Files.**

- `plugins/ariadne/skills/ariadne/EVOLUTION.md` and `SKILL.md`
- `plugins/ariadne/README.md`, `AGENTS.md`, `docs/*.md`, `examples/README.md`, `audit/AUDIT.md`,
  the fixture READMEs
- `.claude-plugin/marketplace.json`, both `plugin.json` files, `.agents/skills/ariadne/SKILL.md`,
  root `README.md`

**Tests.** No new tests. `tests/test_evolution_contract.py` and `tests/test_marketplace_prose.py`
are the proof, plus the demo path.
