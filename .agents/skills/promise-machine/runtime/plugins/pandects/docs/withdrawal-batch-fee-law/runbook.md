# Runbook: a law that stops a fee eating queued withdrawals

Built from `.hexaemeron/study.md`. Base `loop/2026-08-18-kronos` at `9ad3c59`;
every step branches in the chain and every pull request targets that branch.

Four steps. The second is large and the study says why: `pandects.py check`
refuses a law missing any of its six parts, and `test/Corpus.t.sol` requires the
reference to hold every law, so the law, the two model corrections, the specimen,
the counterexample and the catalogue entry cannot be separated without handing
the next step a red tree. Splitting them would buy a smaller diff and pay for it
with a step that is green at neither end.

The documents land as `plugins/pandects/docs/withdrawal-batch-fee-law/`, matching
the frontier revision and the subdirectory convention a second frontier run on an
existing plugin already uses in this repository.

## Step 1: Land the spec documents

**Goal.** Commit the study and runbook so a reader can build the rest from the
repository alone.

**Entry.** `loop/2026-08-18-kronos` at `9ad3c59`. Baseline green: `forge test` 72
passed, plugin catalogue suite 106 passed, repository suite 20 passed,
`pandects.py check` nine laws.

**Exit.** Both documents committed under
`plugins/pandects/docs/withdrawal-batch-fee-law/`, carrying no
marketplace-context block. That follows the closest precedent in this
repository: a first frontier run puts its study at the top of `docs/` and
carries the block, and the one earlier second run puts its study in a named
subdirectory and does not. The prose gate skips a document without the block, so
`python3 -m unittest discover -s tests` stays green and step 4 has two fewer
surfaces to reconcile.

**Files.** `plugins/pandects/docs/withdrawal-batch-fee-law/study.md`,
`plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md`.

**Tests.** None added. The repository prose suite is the gate.

## Step 2: The law, both corrections, and the specimen

**Goal.** Add `claims/pooled-claims-cover-open-batches/v1` with all six parts, and
correct the two models so they hold it.

**Entry.** Step 1's exit state.

**Exit.** `pandects.py check` reports ten laws with every part present;
`forge test` green; the diagonals in `test/Corpus.t.sol` and `test/Pairs.t.sol`
still exact, so the new specimen breaks this law and no other and no existing
specimen breaks this one; the counterexample replays with no fuzzer and asserts
the intermediate quantities.

**Files.**

- `src/laws/PooledClaimsCoverOpenBatches.sol`, new. Single-state `Law`, reads the
  queue by casting the target as its two siblings do, sums unchecked with the
  overflow returned as a violation, skips a claim paid beyond what it was owed
  rather than subtracting into an underflow, and says so in a comment naming
  `reserves-cover-payable` as the law that leaves that defect uncovered.
- `specimens/Sound.sol`, corrected twice. `reserve` caps a new claim against the
  pooled claim not already queued, matching what `requestWithdrawal` already does
  in the Wildcat model. `accrueFee` caps the fee against the pooled claim not
  already queued rather than against `reserved`.
- `integrations/wildcat/WildcatMarketModel.sol`, corrected once, in `accrueFee`,
  the same way.
- `specimens/FeeFromQueued.sol`, new. Inherits `Sound`, overrides `accrueFee`
  alone to restore the cap at `claims - reserved`, and carries the deliberately
  broken header the checker requires.
- `catalogue/pandects.json`, one entry: family `claims`, bounds `exact`,
  applicability naming the accounting model, the assumptions that would make the
  law false, and the four observables it requires.
- `docs/catalogue.md`, regenerated with `python3 scripts/pandects.py render`
  rather than edited. It is a rendering of the catalogue, `tests/test_documents.py`
  checks it against the renderer, and a hand-edit either fails that check or
  makes a real drift invisible by matching it.
- `test/counterexamples/Claims.t.sol`, extended.
- `test/Corpus.t.sol`, the new law and specimen added to the corpus tables the
  diagonal walks, and `PayableBeyondReserves` rerouted as described below.
- `scripts/pandects_lib/render.py` and `tests/test_documents.py`, for the two
  places the law count is stated and the test that froze it.
- `integrations/wildcat/APPLICABILITY.md`, moved here from step 4 because a test
  requires every catalogued law to appear in it.

**Tests.** One counterexample asserting `claims`, the queue total, `reserved` and
`held` at the violating state, not only the verdict. The diagonal in
`test/Corpus.t.sol` runs over the single-state laws alone, where `COUNT` is 5, and
becomes 6; `test/Pairs.t.sol` runs over 3 and does not move. Ten is the corpus
total and not a table dimension. Expect the plugin catalogue suite to rise above
106 by the entries the new law adds, and `forge test` to rise above 72.

**Watch.** The study's first risk. Around twenty existing call sites drive
`reserve` and `accrueFee`, including repeated `reserve(1); reserve(1)` pairs in
`test/Corpus.t.sol`, `test/Adapters.t.sol` and the counterexamples. A tighter cap
can turn one of those into a no-op and leave a passing test asserting a state it
no longer reaches. Read every one of them against the new caps rather than
trusting a green suite. One is already known safe:
`test_the_sound_reference_holds_every_law` charges its fee before it reserves
anything, so the queue is empty when the cap applies and the tightening cannot
reach it.

### Amended during step 2

Four things this step turned out to need, recorded here because the runbook was
wrong about where they belonged rather than because the plan changed.

**`claims/reserves-cover-payable/v1` loses its evidence.** Its specimen and
counterexample ran `deposit(1)`, `reserve(1)`, `reserve(1)`, which records two
units owed against one unit deposited. That is the over-recording the new law
forbids, so tightening `reserve` leaves one claim recorded and
`PayableBeyondReserves` never reaches the state its law was written to catch.
Both call sites move to `deposit(2)`, `borrow(1)`, `reserve(1)`, `reserve(1)`,
which reaches the same lie in an illiquid market: pooled claims 2 against 2 owed,
so the new law holds, and reserves of 1 against two batches declared payable, so
the cover law still fires. This is a better counterexample than the one it
replaces, because declaring more payable than you hold costs somebody money only
when the market cannot pay.

**The renderer states the law count twice.** `S5-R2-01` in the original delivery
fixed the derived count and left "Nine laws ship here" hardcoded three lines
above it. Both are derived now, and the sentence is reworded so it stays
grammatical at one law.

**A test froze the count.** `test_the_preamble_counts_what_was_rendered` asserted
"Nine laws in three families" while calling itself the check that has to come from
outside. It builds the expected phrase from the catalogue now, with its own word
list rather than the renderer's, so it still checks from outside without blocking
every law added after it.

**The Wildcat notes move from step 4 to here.**
`test_every_law_appears_in_the_wildcat_notes` requires every catalogued law to
appear in `integrations/wildcat/APPLICABILITY.md`, so the step cannot be green at
both ends without it. Step 4 no longer carries it.

## Step 3: Reach the specimen from both engines

**Goal.** Make the new specimen reachable in a campaign and record what the
engines found.

**Entry.** Step 2's exit state.

**Exit.** Echidna and Medusa both drive the new specimen and both report the
violation, and the harness exposes it under `echidna_` and `property_`.

Two mechanisms carry the evidence and they are not interchangeable.
`python3 scripts/pandects.py run` writes a machine search record, and it knows one
engine: `foundry`. It has no Echidna or Medusa support, and an engine that did not
run is absent from a record rather than present and empty, which is the runner's
own rule. So the Foundry record comes from that command, and the two fuzzers are
recorded the way the original delivery recorded them, as prose in the audit round
naming the engine, the configuration, the sequence and what failed, with Echidna's
seed given and Medusa's stated as unavailable rather than invented. Do not extend
the runner to a second engine in this step; that is its own frontier.

**Files.** `src/campaigns/Specimens.sol`, extended. That is all that is left of
this step's contracts. `adapters/echidna/CorpusEchidna.sol` and
`adapters/medusa/CorpusMedusa.sol` were named here originally and were done in
step 2 instead, because rounds 4 and 5 of that step established that a law missing
from a surface an outsider inherits is a defect in the step that adds the law
rather than work to schedule. The campaign harness stays here: it drives this
plugin's own specimens rather than anything a third party extends, and it is the
surface the engines need.

`tests/test_documents.py` also gets the last part of a check step 2 built.
`ShippedAdapterTests` holds the catalogue against `adapters/CorpusBase.sol`, which
binds the law objects, and against the three adapters that decide which of them a
run asks. `src/campaigns/Specimens.sol` has the same shape and the same hazard and
is the one surface still unchecked. The check has to land in this step rather than
earlier, because until the harness carries the law it would fail, and a check
written after the change it was meant to force is a check written to pass. Extend
`ShippedAdapterTests` to the campaign harness in the same commit that adds the
property.

**Tests.** `test/Corpus.t.sol` or `test/Adapters.t.sol` extended so the new
entry point is exercised without an engine, the way the existing prefixed entry
points already are. Engine runs are evidence, not tests, and are recorded as
campaigns.

**Watch.** A campaign that reaches the specimen but never reaches the illiquid
state proves nothing. The violation needs `held` below what the queue is owed, so
check the corpus coverage rather than accepting a failure report at face value.

## Step 4: Reconcile the prose, demonstrate, and close the frontier

**Goal.** Make every first-party document say what is now true, run the demo path,
and advance the ledger once.

**Entry.** Step 3's exit state.

**Exit.** The demo path from the study's problem statement runs green:

```bash
forge test
python3 scripts/pandects.py laws
python3 scripts/pandects.py check
```

Every claim of "nine laws" reconciled; the twelve documents carrying the frontier
sentence updated; `docs/catalogue.md` regenerated rather than edited;
`python3 -m unittest discover -s tests` green, which is the gate on the
marketplace-context blocks; the ledger advanced exactly once under
`plugins/hexaemeron/skills/VERSIONING.md`.

**Files.** `README.md` at the repository root, and inside the plugin
`README.md`, `AGENTS.md`, `docs/applicability.md`, `docs/design.md`,
`docs/writing-a-law.md`, `adapters/medusa/README.md`,
`audit/AUDIT.md` for its
marketplace-context block only, `skills/pandects/SKILL.md`,
`skills/pandects/EVOLUTION.md`, and the `.agents/skills/pandects/SKILL.md` mirror.

**Tests.** No new tests. The repository prose suite and `pandects.py check` are
the gates.

**Watch.** Three things, each a way to leave the record wrong.

The Wildcat applicability document was updated in step 2, because a test requires
every catalogued law to appear in it. Nothing is left to do there. It reads "Ten
laws. Seven apply without qualification, and one of those seven did not until this
model was corrected", which is the distinction that mattered: the model holds the
new law because `accrueFee` was corrected, not because it always did.

`audit/AUDIT.md` records past audit rounds. Those are history and stay as
written, including their nine-law counts. Only its marketplace-context block is
mutable.

This run's own study and runbook are records on the same footing, and they are
not reconciled either. Both say Pandects ships nine laws, which is what was true
when the spec was written and is the whole reason the run exists. Rewriting them
to say ten would leave a spec describing work nobody needed to do.

The ledger advances once: evolution increments, generation and epoch stay, and
either one evidenced next job is recorded or the frontier is set to `mature` with
`Next Fiat job` reading `None -- mature`. The frontier is not mature here. Seven
property families remain deferred from the original design, so the next job comes
from that list with evidence, not from a wish to keep the loop busy.
