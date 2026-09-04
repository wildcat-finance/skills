# Runbook: the first end-to-end Aave v4 preservation release

Five steps. Each is one pull request against the step below it, green at both
ends, and assumes only the exit state of the steps before it.

The order is dependency order. The document format comes first because
everything later writes or reads it; the binding rule comes next as a function
with no command around it, so its tests are about the rule rather than about
argument parsing; the two commands follow; and the release itself ships last,
because it is the thing the whole run exists to produce.

## Step 1: The release document and its schema

**Goal.** Register a `release` document type so the later steps have something
to write, and put the run's own study and runbook in the repository.

**Entry.** The run branch `fiat/the-first-end-to-end-aave-v4-preservation-rele`
off `main` at `382fdc0`.

**Exit.** `python3 scripts/lazarus.py validate schemas` exits 0 with six
registered types rather than five. `validate release <file>` accepts a
well-formed release document and refuses one missing any required field.
Lazarus's suite is green and the repository's is green.

**Files.**

- `plugins/lazarus/schemas/release-v1.json` (new)
- `plugins/lazarus/scripts/lazarus_lib/schemas.py`
- `plugins/lazarus/scripts/lazarus.py`
- `plugins/lazarus/tests/test_schemas.py`
- `docs/lazarus-aave-v4-preservation-release/study.md` and `runbook.md` (new,
  at the repository root beside the other runs' artefacts)

**Tests.** The new type's registered digest matches its file. A release document
with each required field removed in turn is refused. A document carrying a field
the type does not define is refused. Expect roughly 10 new tests.

## Step 2: The binding rule

**Goal.** Decide, from a verified report and a statement, whether the statement
describes that fixture and whether it claims more than the fixture holds.

**Entry.** Step 1's exit state.

**Exit.** A function that takes the verified report, the fixture manifest and a
parsed statement and returns the checks it made, raising a named error on the
first disagreement. The evidence check refuses a statement whose counts differ
from the recomputed ones in any class and in either direction. No command calls
it yet, and the suite is green.

**Files.**

- `plugins/lazarus/scripts/lazarus_lib/binding.py` (new)
- `plugins/lazarus/scripts/lazarus_lib/errors.py`
- `plugins/lazarus/tests/test_binding.py` (new)

**Tests.** The shipped Aave v4 fixture and a statement over it, binding clean.
Each of the six checks refused on its own: a predicate type that is not the
state-fixture type, a block hash that disagrees, evidence counts that disagree
in each class and in each direction, a canonical-chain claim that is true, a
component the statement names and the fixture lacks, a component the fixture
holds and the statement omits, and a component digest or byte count that
disagrees. The upgrade case gets its own test with the counts from the study's
reproduction. Expect roughly 30 new tests.

## Step 3: `lazarus release`

**Goal.** Write a preservation release: the fixture, the statement over it, and
the release document binding them.

**Entry.** Step 2's exit state.

**Exit.** `release <fixture> --statement <file> --out <dir>` verifies the
fixture, applies the binding rule, and writes the directory only when both pass.
The output holds `release.json`, `statement.json` and a `fixture/` copy, and is
finalised atomically so a killed run leaves nothing. A statement that overstates
the fixture is refused with the disagreeing class named, and no output
directory is left behind.

**Files.**

- `plugins/lazarus/scripts/lazarus_lib/release.py` (new)
- `plugins/lazarus/scripts/lazarus.py`
- `plugins/lazarus/tests/test_release.py` (new)

**Tests.** The Aave v4 fixture released clean. The study's tampered manifest
refused at the binding, with nothing written. An `--out` that already exists,
that resolves inside the fixture, or that cannot be written. A statement that is
not JSON, is not an object, carries `NaN`, or is larger than the read cap. A
killed write leaving no partial directory. Expect roughly 25 new tests.

## Step 4: `lazarus verify-release`

**Goal.** Read a release back offline and check it whole, using nothing but what
the release contains.

**Entry.** Step 3's exit state.

**Exit.** `verify-release <dir>` re-verifies the fixture copy, re-applies the
binding rule to the statement beside it, checks the release document against
both, and prints the three evidence counts. It exits 1 on any disagreement,
naming it. A release whose statement, fixture or document is edited after the
fact fails.

**Files.**

- `plugins/lazarus/scripts/lazarus_lib/release.py`
- `plugins/lazarus/scripts/lazarus.py`
- `plugins/lazarus/tests/test_release.py`

**Tests.** A release written by step 3 verifying clean. Each of its three parts
edited in turn and refused: a component byte in the fixture copy, a count in the
statement, a field in the release document. A release missing each of its three
parts. Expect roughly 20 new tests.

## Step 5: Ship the release, then reconcile the ledger and the prose

**Goal.** Produce the Aave v4 preservation release, demonstrate the whole
path, and bring every surface into agreement.

**Entry.** Step 4's exit state.

**Exit.** The demo path in the study runs offline from the repository root and
exits 0, and the negative check refuses the tampered manifest at `release`. The
release ships under `plugins/lazarus/examples/`. `EVOLUTION.md` carries one new
row on the evolution axis with a recomputed digest. Every marketplace-context
block that states Lazarus's frontier agrees, including the root selection table
row that this run makes true. Both suites green.

**Files.**

- `plugins/lazarus/examples/aave-v4-spoke-v0-release/` (new)
- `plugins/lazarus/examples/aave-v4-spoke-v0/demo.py` and `README.md`
- `plugins/lazarus/skills/lazarus/EVOLUTION.md` and `SKILL.md`
- `plugins/lazarus/README.md`, `AGENTS.md`, `docs/*.md`
- `.claude-plugin/marketplace.json`, `plugins/lazarus/.claude-plugin/plugin.json`,
  `.agents/skills/lazarus/SKILL.md`, root `README.md`
- `plugins/lazarus/docs/preservation-release.md` (new)

**Tests.** A test that the shipped release still verifies, and one that it still
describes the checked-in fixture, so a recapture without a re-release fails the
suite rather than shipping a stale release. Expect roughly 8 new tests.
