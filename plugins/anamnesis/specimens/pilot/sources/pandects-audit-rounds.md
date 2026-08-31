# Pandects audit log

<!-- marketplace-context:start -->
> **Record status.** This is a historical audit record; findings and dispositions below are preserved as evidence. Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

One section per round. A round with no findings is still a round and still gets
written down.

The suite for this run is the vendored Pashov set: `x-ray`, `solidity-auditor`
and `fizz`, recorded on the run's ledger rather than waived, because this build
ships Solidity. Each round says which of them ran, and where one did not, why.

Echidna and Medusa were not installed when this log opened, and the step 1
rounds below say so because it was true when they were written.

They were installed on 2026-08-16, after step 1 closed and before step 2 began:
Echidna 2.3.3, Medusa 1.5.1 and Slither 0.11.6, all from homebrew-core. Both
fuzzers were proved against a contract written to break a law before either was
relied on. Rounds from step 2 onwards therefore run campaigns, and each says
which engine produced which result.

## Step 1, round 1 -- 2026-08-16

Reviewed: `src/ICreditObservables.sol`, `src/Law.sol`, and the Python that
decides whether something is a law, against the risks listed in
[`docs/design.md`](../docs/design.md).

**How the suite ran.** `solidity-auditor` fans twelve specialist agents over
the in-scope `.sol` files, excluding `test/` and `*.t.sol`. The in-scope set for
this step is one interface and one abstract contract, neither of which has a
single function body: there is no arithmetic, no state, no access control and
no external call to audit. The review was therefore done directly rather than
fanned out, and this line is here so nobody reads twelve agents into it.
`x-ray` produces a pre-audit report over a protocol, and there is no protocol in
this step for the same reason. `fizz` builds an invariant suite over a stateful
system; the first stateful contracts arrive with the specimens in step 2, and
its campaigns start there.

What that leaves is the Python, which is where this step's decisions actually
execute, and it is where the round found things.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `scripts/pandects_lib/checker.py` | The revert check looked for `require` and `revert` and not `assert`. A law reaching for `assert(cond)` to mean "violated" reverts with a panic, which under `fail_on_revert = false` is as silent as any other revert, so the law reports nothing and the check that exists to catch exactly that missed it | fixed in this round: `assert` is scanned with the other two and the finding names which was used |
| S1-R1-02 | medium | `scripts/pandects_lib/checker.py` | The check first matched the body of `check()` with a regex that depended on the closing brace sitting at four spaces. A law written on one line, or inside a library, or indented differently, produced no match at all, and the revert check then silently did not run. A check that stops checking without saying so is worse than no check | fixed in this round: the scan reads the whole component. A law component holds `id`, `statement` and `check` and nothing else, so no revert anywhere in it is legitimate and there is no body to find first |
| S1-R1-03 | low | `scripts/pandects_lib/checker.py` | A component or specimen that was not UTF-8 raised out of the checker instead of being reported. `check_specimen` also called `.lower()` on the read result, so the same input crashed there twice over | fixed in this round: reading returns `None` and both call sites report it as a finding |
| S1-R1-04 | low | `scripts/pandects_lib/checker.py` | `os.path.commonpath` raises on paths it cannot compare, which would have escaped as a traceback rather than a refusal to resolve | fixed in this round |

Checked and found sound:

- The word `require` inside a comment is no longer evidence, and a test asserts
  it. Comments are stripped before the scan, so a law explaining what it does
  not do is not accused of doing it.
- `resolve` refuses a component path that leaves the plugin, including an
  absolute one, so a catalogue cannot point the checker at `/etc/passwd`.
- A law missing any part is a finding naming the part rather than a parse
  error calling the file malformed. Walked all seven fields by hand.
- `Law.check` is `view` and an override may only narrow that, so no law can
  quietly become state-changing.

Leads not pursued:

- **A law calling a helper that reverts.** The scan reads one file. A component
  that delegates to a library which reverts is not caught, and no regex over
  one file would catch it. The specimen is what closes this: a law that reverts
  where it should return fails against its own specimen in step 2, which is
  evidence rather than a pattern match.
- **Orphan scanning is limited to `src/laws/`.** A component filed elsewhere and
  claimed by nobody is not reported. That is the documented location for law
  components, and widening the scan would report every Solidity file in the
  plugin.
- **A target that consumes all gas in a view call** stalls a campaign rather
  than failing it. That belongs to the harness adapter in step 4, which decides
  what an unobservable state means.

## Step 1, round 2 -- 2026-08-16

Reviewed: the checker with round 1 applied, starting from the scan that round
widened. Widening it introduced two ways to accuse an honest law, which is the
cost of scanning a whole file instead of one function body and worth paying only
once it is paid down.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `scripts/pandects_lib/checker.py` | The pattern accepted any uppercase letter after the word, to catch `revert CustomError()`. A function named `revertHelper` matched it, so a law with an honestly named internal helper was reported as reverting to signal a violation | fixed in this round: the pattern takes the two real spellings, `revert(` and `revert` followed by whitespace and a capital, and nothing else |
| S1-R2-02 | medium | `scripts/pandects_lib/checker.py` | The scan read string literals. A law whose `statement()` describes a system that requires collateral was accused of requiring it, which would have pushed authors to write worse sentences to get past a check | fixed in this round: string literals are removed before comments, so a `//` inside one is removed with the string rather than truncating the line |

Checked and found sound:

- Removing strings before comments is the right order, and the residual case is
  a double quote inside a comment over-removing that comment. Comments are
  being removed anyway, so the cost is nothing.
- `require(`, `assert(`, `revert(` and `revert CustomError()` are all still
  caught, asserted individually.

Leads not pursued:

- **Nothing yet proves a law fails its specimen.** The catalogue names one and
  the checker confirms it exists and says it is deliberately broken. That it is
  actually caught is a Solidity claim, and the diagonal in step 2's
  `test/Corpus.t.sol` is what will make it. This is the corpus's central
  discipline and it is worth saying that at the end of step 1 it is declared
  rather than demonstrated.

## Step 1, round 3 -- 2026-08-16

Reviewed: the checker and the catalogue parser swept over malformed entries.
Five law entries, each malformed differently: every field absent, every field
the wrong type, empty and whitespace paths, absolute and traversing paths, and
paths naming a directory where a file belongs. Then the parser over six
documents that are not catalogues.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | low | `scripts/pandects_lib/checker.py` | A path carrying an embedded null byte raised `ValueError` out of `realpath` rather than being reported. The same class as round 1's unreadable component: malformed input crashing the checker instead of being told to the reader | fixed in this round: a path the filesystem will not look at is a containment that cannot be established, so it is refused |

Checked and found sound:

- Every other malformed entry produces findings and renders them. Nothing in
  the five raised after the fix.
- The parser refuses six non-catalogues as `CatalogueError` and raises nothing
  else.
- A path naming a directory where a file belongs is reported as a missing
  component rather than read.

Leads not pursued: the specimen claim carried from round 2, which step 2 closes.

## Step 1, round 4 -- 2026-08-16

Reviewed: the step's whole diff with three rounds applied. Re-read
`ICreditObservables.sol`, `Law.sol`, and the four Python modules end to end,
re-ran the malformed sweep, and re-ran every suite: 53 catalogue and checker
tests on Python 3.9 and 3.14, four Solidity tests under `forge 1.7.1`, and the
repository's nine contract tests.

No findings.

Leads not pursued: the specimen claim, which step 2 closes with the diagonal in
`test/Corpus.t.sol`.

## Step 2, round 1 -- 2026-08-16

The first round with the engines. Reviewed: three laws, four specimens, the
diagonal and the counterexamples.

**What ran.** Slither 0.11.6 over the corpus, 5 contracts and 102 detectors.
A Foundry campaign over the sound reference, driving `deposit`, `borrow`, `repay`, `accrueFee` and `reserve` at the 64 runs and depth 64 that `foundry.toml` pins. Echidna 2.3.3 at 20,000
transactions and seed 20260816 against four harnesses, and Medusa 1.5.1 at
20,000 transactions against the same four. `x-ray` was not run as a procedure:
it enumerates a protocol, builds a threat model from entry points and writes a
readiness report, and the subject here is a nine-file property corpus with no
protocol, no privileged role and no external integration. The review that
procedure exists to produce was done directly and this line is here so nobody
reads a report into it.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `specimens/Sound.sol` | The sound reference is not sound. A Foundry campaign broke `reserves-backed-by-claims` against it and shrank the sequence to four calls: deposit, fee, reserve, fee. `accrueFee` reduced claims with no regard for what was already reserved, so a fee charged after a reservation dropped claims below reserved. In economic terms the protocol was taking its fee out of value already promised to a lender who had asked to leave. The law is right and the reference was wrong | fixed in this round: the fee is capped at claims that are not already reserved, and the reason is recorded on the function |
| S2-R1-02 | medium | `src/campaigns/Specimens.sol` | The campaign harnesses were written under `test/`. crytic-compile skips `test/` when it builds a Foundry project, so Echidna could not see them at all and answered `Given contract not found`. A harness an engine cannot see is a campaign that quietly tests nothing, which is the failure this corpus exists to refuse, in its own tooling | fixed in this round: harnesses live under `src/campaigns/`, with the reason on the contract |
| S2-R1-03 | low | `test/Corpus.t.sol` | A test function that reads and does not write was not marked `view`, which the compiler warned about. A warning nobody clears is a warning nobody reads | fixed in this round |

**What the campaigns found, and what changed because of it.**

Every engine reproduces the diagonal. Against the sound reference all three laws
hold; against each broken specimen exactly its own law fails and the other two
hold. Three independent searches agreeing is the evidence that the diagonal is a
property of the laws rather than of the states somebody chose.

Echidna reduced two of the three counterexamples. The hand-written sequences
moved a hundred units where one was enough, so `deposit(1)` replaced
`deposit(100)` for `value-conserved` and `deposit(1), reserve(1)` replaced the
hundreds for `held-assets-partitioned`. The counterexample file said an engine
finding something smaller meant the sequence was not minimal and would be
replaced; it was, and it has been.

Checked and found sound:

- Slither reports nothing across 102 detectors.
- The sound reference survives a Foundry campaign at 512 runs and depth 128,
  three further campaigns at fresh seeds, Echidna at 20,000 transactions and
  Medusa at 20,000.
- Every harness declares both `echidna_` and `property_` prefixes. A harness
  carrying one of them is silent under the other engine, which is the same
  class of defect as S2-R1-02 and was designed out rather than found.

Leads not pursued:

- **Medusa reports no seed**, so its campaigns above are not reproducible call
  for call. Echidna's are, and the seed is recorded. The search record in step 4
  states this per engine rather than implying both are reproducible.
- **The specimens bound their inputs by remainder**, so a fuzzer never explores
  the arithmetic ceiling through them. The ceiling is covered instead by the
  `Extreme` target in the diagonal, which asserts each law reports rather than
  reverts there. Worth revisiting if a law is ever added whose defect lives near
  the boundary.

## Step 2, round 2 -- 2026-08-16

Reviewed: the tree with round 1 applied, starting from what round 1's own fix
changed about the reach of its tools.

**What ran.** Slither over 14 contracts, which is the point of the first
finding. Foundry, Echidna at 20,000 transactions and seed 20260816, and Medusa
at 20,000, all four harnesses each.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | `src/campaigns/Specimens.sol` | The harness discarded the detail every law builds. `Law` is written so that a reader who finds a failure later learns which quantities were compared and what they were, and the campaign entry points dropped exactly that, leaving an operator with a call sequence and no reason. Slither's `unused-return` is what pointed at it | fixed in this round: `explain()` returns each law's reason for the current state, so a replayed sequence gives up its reason instead of having to be worked out again. A property function may return only a boolean and emitting the string would make it non-view, so this is where it goes |
| S2-R2-02 | low | `audit/AUDIT.md` | Round 1 recorded Slither over 5 contracts and no results. True when written, and stale within the same round: moving the harnesses out of `test/` so Echidna could see them also moved them into Slither's scope, and Slither was not run again afterwards. The clean result covered less than the sentence suggested | fixed in this round: Slither re-run over all 14 contracts, and the entry above records the count so the scope is legible |
| S2-R2-03 | low | `specimens/Sound.sol` | `asset` was declared and never assigned, so every specimen reported that its quantities were denominated in the zero address. An observable that says nothing about itself while the interface promises it names the unit | fixed in this round: a named constant, with the reason that these specimens model units rather than a token |
| S2-R2-04 | low | `src/campaigns/Specimens.sol` | Seven harness fields were mutable storage where they are set once. Cosmetic on its own, but a detector list with fourteen entries nobody intends to act on is a detector list nobody reads | fixed in this round: the fields are immutable, and the two detectors that remain by design are disabled at each site with the reason in the source rather than repository wide, so the next thing either catches is read rather than filtered out with them |

Checked and found sound:

- Slither reports nothing across 102 detectors and 14 contracts.
- The diagonal survives every change: Sound clean under all three engines,
  each broken specimen caught by its own law alone under Echidna and Medusa.
- `explain()` returns the law's own sentence, asserted against the exact
  string in `test/Explain.t.sol` rather than against a non-empty check.

Leads not pursued:

- **A law that reads one observable twice** could be fooled by a target
  answering differently between the two calls. None of the three does, and each
  reads every quantity once into a local. Worth a rule if a law ever needs two
  reads of the same observable, and worth checking then rather than forbidding
  now.
- **The campaign harnesses ship under `src/`**, so a consumer of the corpus
  receives them. They have to be there for crytic-compile to see them, and they
  document how to point an engine at a specimen, so this is left deliberate
  rather than hidden behind a build flag.

## Step 2, round 3 -- 2026-08-16

Reviewed: the step's whole diff with two rounds applied, and the one lead round
2 left open.

**The lead, settled.** No law reads the same observable twice. Each of the
three assigns every quantity it needs into a local once, checked mechanically
across all three components rather than by reading them. That closes the way a
target could answer differently between two reads of the same getter and get a
verdict neither answer deserved. It is left as a property the current laws have
rather than a rule the checker enforces, because there is no law yet that needs
two reads and a check written against a case nobody has met is a check nobody
can calibrate.

**What ran.** The full sweep: 55 catalogue and checker tests on Python 3.9 and
3.14, the repository's 9, `pandects check` over three laws, 20 Solidity tests
across five suites, Slither over 14 contracts, and the diagonal under Foundry,
Echidna and Medusa.

No findings.

Leads not pursued: the two carried from round 2, both recorded there with their
reasons.


## Step 3, round 1 -- 2026-08-16

Reviewed: the whole of the step's diff. Two new law shapes, a queue extension
interface, six laws, six specimens, six counterexamples and the campaign
harness that carries a snapshot between calls.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | src/laws/QueueOrderPreserved.sol, src/laws/ReservesCoverPayableClaims.sol, src/Observation.sol | Both queue laws and the snapshot helper traverse the whole queue with one external call per claim. Above some queue length the call runs out of gas and reverts, and the corpus counts a revert as no verdict -- so each law stops working, silently, at a size nobody has written down. | fixed in 2429718 |
| S3-R1-02 | medium | src/laws/DebtFallsOnlyAgainstPayment.sol, src/laws/NoAccrualAtRest.sol, src/laws/RecordedClaimNeverShrinks.sol | The succession laws compare totals, so an offsetting movement inside one transition hides a violation. A write-off in the same call as a deposit of the same size leaves debt down and held assets up, and the payment law holds. | fixed in 2429718 |
| S3-R1-03 | low | src/PairLaw.sol | Three laws each explain, in their own words, what they do with a pair they cannot judge, and two of them reach opposite conclusions. The rule behind that was written nowhere, so it read as inconsistency rather than as policy. | fixed in 2429718 |
| S3-R1-04 | low | -- | A Medusa run was read as "none failed" when it had not run at all: stale crytic artefacts, and the engine exited on `Failed to initialize the test chain` before any campaign started. Caught by noticing that Medusa disagreed with Echidna on five specimens. The corpus's own rule is never to report a campaign under an engine that did not run, and this round nearly broke it. | fixed in 2429718 |

**S3-R1-01, on why the fix is prose.** There is no partial answer available.
Both properties are about the whole queue, and a law that read the first
hundred claims and held would be reporting on part of a system as though it
were the system. So the limit is stated where a reader meets it -- in each
component and in the applicability the catalogue carries -- and a target that
queues more than can be read in one call needs an adapter that pages rather
than a law that guesses.

**S3-R1-02, on the shape of the gap.** A law over aggregates cannot attribute
movement to a cause, and attributing it needs per-transition detail the
observables do not carry. The honest fix is the applicability: these laws mean
what they say when the two observations bracket a single operation. That is how
every harness in this repository uses them, including the campaign, which
snapshots on the way into each entry point.

**S3-R1-04, on what was actually wrong.** The first invocation passed a
hand-written Medusa config; the engine's own crytic-compile step produced
nothing and it exited before the chain came up. The output contained no
failures because it contained no campaign. The run was redone with the
invocation the README documents, `medusa fuzz --compilation-target .
--target-contracts <name>`, after clearing `crytic-export` and the stale
artefact hash, and every campaign then reported.

**What ran.** 50 Solidity tests across eight suites under forge 1.7.1, 63
catalogue and checker tests on Python 3.14, the repository's 9 contract tests,
`pandects check` over nine laws, Slither 0.11.6 over 24 contracts, and both
engines over all ten campaigns: Echidna 2.3.3 at 20,000 transactions with seed
20260816, and Medusa 1.5.1 at 20,000.

**The diagonal, under both engines.** Each broken specimen failed exactly its
own property and nothing else, under Echidna and under Medusa, and the sound
reference failed nothing under either.

`CompoundsPerStep` passed every property under both engines, which is the
expected result and the sharpest illustration in the corpus of why a passing
campaign is not evidence. Its defect is path independence, which compares two
systems advanced by different routes; a campaign drives one system along one
route and can never see it. It is caught deterministically in
`test/Pairs.t.sol` and reduced in `test/counterexamples/Accrual.t.sol`.

Leads not pursued:

- **A recorded claim has no identity, only an index.** The claim law compares
  the queue positionally, so a system that dropped one claim and appended
  another of the same size would keep its length and its amounts and go
  uncaught. Giving `claimAt` an identifier would close it. Not done here,
  because that is a new observable and no law in the corpus reads it: the
  applicability already assumes a claim keeps its index, and inventing an
  observable ahead of the law that needs it is how interfaces grow members
  nobody can justify.
- **Nothing says the clock never runs backwards.** `NoAccrualAtRest` holds
  whenever the two observation times differ, in either direction, so a system
  whose `observedAt` went down would slip past every accrual law. That is a
  law, and a real one, but it is not one of the six this step was asked for.
- **`slither_results.json` is tracked.** Generated output committed in an
  earlier step, so every Slither run leaves a diff. Raised separately rather
  than folded into this step.

## Step 3, round 2 -- 2026-08-16

Reviewed: the tree with round 1 applied, and the two areas round 1 did not
reach -- what the path-independence law takes on trust, and what the reference
can be driven into that no law describes.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | src/laws/AccrualPathIndependent.sol | The bound is `subdivisions - 1`, and `subdivisions` is fixed when the law is deployed. Nothing in either observation says how many steps the subdivided run actually took, so a law built for the wrong count silently compares against the wrong bound -- too generous and a compounding system passes, too tight and a correct one is reported as violated. | fixed in 0b7ae32 |
| S3-R2-02 | low | src/laws/ReservesCoverPayableClaims.sol | The law reports a violation when more claims are declared payable than exist, which is marginally broader than its statement. The reason -- that the alternative reads past the end of the queue and reverts into silence -- was in nobody's head but mine. | fixed in 0b7ae32 |

**S3-R2-01, and why the fix is a test rather than a guard.** There is no guard
available. The count cannot be derived from the observations, so it is part of
the question rather than part of the answer, and the honest response is to say
so where it will be read and to show it going wrong.
`test_a_bound_built_for_the_wrong_run_is_wrong_in_both_directions` builds the
same compounding pair three times: caught by a law built for the two steps it
took, passed by a law built for a thousand, and a correct system reported as
violated by a law built for one. A hazard nobody has watched fail is a hazard
people assume is handled.

**What ran.** 51 Solidity tests across eight suites, 63 catalogue and checker
tests, the repository's 9, `pandects check` over nine laws, Slither 0.11.6 over
24 contracts, and both engines over the sound campaign and the three campaigns
carrying pair laws: Echidna 2.3.3 at 20,000 transactions with seed 20260816,
and Medusa 1.5.1 at 20,000. Scoped rather than swept, because this round's diff
is comments, one catalogue assumption and one test, and claiming a full sweep
that did not happen is the failure mode round 1 caught me in.

Slither returned the same fifteen results as round 1: one uninitialized-state
and three uninitialized-local, all of them Solidity's zero defaults for a
storage array and three counters, and two calls-loop, which is the traversal
round 1 documented rather than removed.

Leads not pursued:

- **The reference can record withdrawal claims summing beyond the pooled claim
  total.** `reserve` caps each request at total lender claims rather than at
  the claims not already spoken for, so two requests can each ask for the whole
  pool. That is what `PayableBeyondReserves` is driven into, and capping at the
  unspoken-for remainder would put that state out of reach of every operation
  the reference has. It is also not obviously wrong: the model has no lender
  identity, claims are pooled, and a request cannot be bounded by a share the
  system does not track. The law it implies -- unpaid recorded claims never
  exceed total lender claims -- needs per-lender accounting, which is a larger
  model than this step.
- **A full queue drops a withdrawal request silently.** `reserve` records
  nothing once `MAX_CLAIMS` claims exist. The cap is a harness bound, so that
  every observation stays affordable to copy, and it is documented as one. No
  law says a request must become a claim, and a lost request is a real defect
  shape; both are worth a later step and neither is this one.
- Three carried from round 1, each recorded there with its reason: claims have
  position but no identity, no law says the clock never runs backwards, and
  `slither_results.json` is tracked.

## Step 3, round 3 -- 2026-08-16

Reviewed: the whole step with both rounds applied, and the three Slither
categories neither earlier round had read line by line.

**What ran.** The full sweep: 51 Solidity tests across eight suites under forge
1.7.1, 63 catalogue and checker tests on Python 3.14, the repository's 9,
`pandects check` over nine laws, Slither 0.11.6 over 24 contracts, and both
engines over all ten campaigns -- Echidna 2.3.3 at 20,000 transactions with
seed 20260816, and Medusa 1.5.1 at 20,000.

**The diagonal, complete.** Eight broken specimens, each failing exactly its own
property and no other, identically under Echidna and Medusa. The sound
reference failed nothing under either. `CompoundsPerStep` passed everything
under both, which is the documented expectation rather than a miss: its defect
compares two systems and a campaign drives one.

**The Slither results, settled.** Fifteen, unchanged across all three rounds and
none of them a finding. Six `costly-loop` on `settle`, which writes three
storage slots inside a loop that returns after the first claim it settles.
Three `uninitialized-local` and one `uninitialized-state`, all of them
Solidity's zero defaults for three counters and an empty storage array. Two
`cache-array-length`, gas in a specimen written to be read. Two `calls-loop`,
which is the queue traversal round 1 documented as a limit rather than removed.

No findings.

Leads not pursued: the five carried forward, each recorded in the round that
found it -- claims have position but no identity; nothing says the clock never
runs backwards; the reference can record claims summing past the pooled total;
a full queue drops a request silently; and `slither_results.json` is tracked.

## Step 4, round 1 -- 2026-08-16

Reviewed: the whole of the step's diff. Two adapter shapes over a caller's
target, the probe, both engine entry points, the search record and the corpus
digest.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | high | adapters/CorpusBase.sol | A driving adapter whose entry points do not carry `records` reports all three succession laws holding, forever, and nothing about that verdict distinguishes it from three laws that held. The forgotten modifier is not something the compiler can catch, and the result of forgetting it is three green properties over a system nobody judged. | fixed in aa3df12 |
| S4-R1-02 | medium | scripts/pandects_lib/run.py | A campaign killed by the timeout was reported as an engine that did not run. The engine ran, searched for as long as it was given and was killed; dropping it from the record hides a search that happened, and calling it passed would be worse. | fixed in aa3df12 |
| S4-R1-03 | medium | scripts/pandects_lib/run.py | Settings were read from `[invariant]` only, and an absent or differently named section produced `"configuration": {}` -- a record saying the campaign ran under no settings, when what happened is that nobody could read them. Foundry accepts `[profile.default.invariant]` as well. | fixed in aa3df12 |

**S4-R1-01, and why the fix is a counter.** There is nothing to enforce. A base
cannot see whether an entry point somebody else wrote carries a modifier, and a
fallback that forwarded calldata blindly would forward the call that breaks a
law without recording the state before it. So the unexercised case is made
visible instead: `recordedCalls` is public, `successionExercised` reads it, and
`explainSuccession` returns "no call was recorded, so no transition was judged"
rather than three empty strings. An integrator now has a number to assert on,
and `successionHolds` means something only when read beside it.

**S4-R1-03, on the shape of the mistake.** The record's entire purpose is
describing the search. A configuration that describes a different search, or
none, is worse than a record that refuses to be written, so it refuses.

**What ran.** 59 Solidity tests across nine suites under forge 1.7.1, 90
catalogue, checker and search-record tests on Python 3.14, the repository's 9,
`pandects check` over nine laws, Slither 0.11.6 over 26 contracts, and both
engines against both adapter forms.

**The adapters, under both engines.** `ObservedQueueJumped` failed
`queue_order_preserved` and nothing else, under Echidna and under Medusa,
through an adapter that never saw the call that broke it -- which is the case
for the observing form in one line. `DrivenClaimHaircut` failed
`recorded_claim_never_shrinks` and nothing else, under both, which is the case
for the driving one.

Slither returned the same fifteen results as step 3 and nothing new for the
adapters: the zero defaults, the queue traversal already documented, and gas in
a specimen.

Leads not pursued:

- **The observer cannot tell a queue-less target from a broken one.**
  `queueHolds` reverts against a system that does not implement the extension,
  which is the documented limit, but an integrator meets it as a revert with no
  explanation attached. A probe that answered "this target has no queue" would
  need a call that cannot be distinguished from a target whose queue read
  happens to revert, so there is nothing honest to return.
- **`hasWithdrawalQueue` defaults to true.** A queue-less integrator who does
  not override it gets two reverting invariants. The default is deliberate --
  false would silently skip two laws for every system that does have a queue --
  but it is a sharp edge and the prose is the only thing guarding it.
- **The five carried from step 3**, each recorded in the round that found it.

## Step 4, round 2 -- 2026-08-16

Reviewed: the tree with round 1 applied, and the two places round 1 did not
reach -- what an integrator without a withdrawal queue can actually get out of
the adapters, and whether the record says "unknown" the same way twice.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R2-01 | medium | adapters/CorpusBase.sol | `explainOneState` reads all five laws, so against a target with no withdrawal queue it reverts and takes the three answers down with the two reads that had none. An integrator whose system has no queue was told nothing at all, including about the laws that were happy to judge it. | fixed in cf9cf68 |
| S4-R2-02 | low | scripts/pandects_lib/run.py | A seed nobody could read was absent from the record; an engine version nobody could read was present and null. Same reason, two spellings, in one document. | fixed in cf9cf68 |

**S4-R2-01, and what the fix is not.** `explainOneState` still reverts, because
reading a queue off a target that has none is exactly the documented limit and
softening it would be inventing a verdict. What changed is that `explainCore`
exists beside it, carrying the three reasons that had answers. `coreHolds` and
`queueHolds` were already split this way; the explanation was not, and the split
is only useful if it goes all the way through.

**S4-R2-02, on why a low finding was worth fixing.** A record that spells
"unknown" two ways has to be read twice, and the second reading is where
somebody decides that null means the run had no seed. The rule is now one rule
and a test walks the whole record asserting no field anywhere in it is null,
rather than checking the two fields that prompted it.

**What ran.** 60 Solidity tests across nine suites, 92 catalogue, checker and
search-record tests, the repository's 9, `pandects check` over nine laws, and
Echidna 2.3.3 against both adapter forms with the shipped configuration. Scoped
rather than swept: this round's diff is one new function, one field rule and two
tests.

`ObservedQueueJumped` failed `queue_order_preserved` and nothing else;
`DrivenClaimHaircut` failed `recorded_claim_never_shrinks` and nothing else.

Leads not pursued:

- **A counterexample changing does not change the corpus digest.** The digest
  covers the catalogue, the law components and the specimens. That is
  deliberate -- the criterion asks for a digest that moves when the corpus moves
  and holds still when a test does -- but a counterexample is closer to a law
  than a test is, and which side of the line it belongs on is a real question
  rather than a settled one.
- **The three carried from round 1**, and the five carried from step 3, each
  recorded in the round that found it.

## Step 4, round 3 -- 2026-08-16

Reviewed: the whole step with both rounds applied, and whether the adapters
disturbed anything the specimen campaigns already prove.

**What ran.** The full sweep: 60 Solidity tests across nine suites under forge
1.7.1, 92 catalogue, checker and search-record tests on Python 3.14, the
repository's 9, `pandects check` over nine laws, Slither 0.11.6 over 26
contracts, Echidna 2.3.3 against both adapter forms with the shipped
configuration and against three specimen campaigns at seed 20260816, and Medusa
1.5.1 against both adapter forms at 20,000.

**The adapters.** `ObservedQueueJumped` failed `queue_order_preserved` and
nothing else under both engines, through an adapter that never saw the call
that broke it. `DrivenClaimHaircut` failed `recorded_claim_never_shrinks` and
nothing else under both.

**The specimen campaigns, unchanged.** `SoundCampaign` failed nothing,
`PayableBeyondReserves` failed its own law alone, and `CompoundsPerStep` passed
everything, which is still the documented expectation rather than a miss.

**Slither.** Fifteen results, the same set as step 3 and nothing new for the
adapters: zero defaults for a storage array and three counters, the queue
traversal documented as a limit, and gas in a specimen.

No findings.

Leads not pursued: the one from round 2 about which side of the line a
counterexample belongs on, the three carried from round 1, and the five carried
from step 3. Each is recorded in the round that found it.

## Step 5, round 1 -- 2026-08-16

Reviewed: the whole of the step's diff. The Wildcat model, its applicability
notes, the three documents, the drift check and the demo.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | medium | docs/catalogue.md | The document calls itself a rendering and there was no renderer. It was written once by a script that was not committed, and the drift test caught a stale document without offering any way to fix it: somebody adding a law was told the document was wrong and left to work out what it should have said. | fixed in ac37f14 |
| S5-R1-02 | low | integrations/wildcat/APPLICABILITY.md | A law added to the catalogue could go unmentioned in the integration's notes, which is the one place the applicability question actually gets asked of a real design. Nothing checked. | fixed in ac37f14 |

**S5-R1-01, and what it took to make the claim true.**
`scripts/pandects_lib/render.py` is now the only thing that writes that file,
`python3 scripts/pandects.py render` regenerates it, and a test compares the
committed bytes with what the renderer produces. Drift is a one-line fix rather
than a transcription exercise. The renderer also skips a family the catalogue
declares and files nothing under, because a heading with nothing beneath it
reads as a section somebody deleted.

**What ran.** 71 Solidity tests across ten suites under forge 1.7.1, 104
catalogue, checker, search-record and document tests on Python 3.14, the
repository's 9, `pandects check` over nine laws, Slither 0.11.6 over 28
contracts, and both engines against the Wildcat campaign: Echidna 2.3.3 with the
shipped configuration and Medusa 1.5.1 at 20,000.

**The finding the integration was for.** Echidna and Medusa both failed
`recorded_claim_never_shrinks` against `WildcatMarketCampaign`, and both were
right. A Wildcat batch accumulates while it is open, so the amount owed on it
rises, and the law says a recorded claim keeps its amount. The applicability
notes had already claimed the law held before either engine ran.

That is recorded in the step rather than here, because it is a fact about the
design rather than a defect in the work: an open batch is not a claim that has
been recorded, it is one still being assembled, and the law starts applying when
the batch closes. Both halves are asserted in `test/Wildcat.t.sol`. It is worth
repeating in this log because it is the sharpest evidence in the whole run for
why a corpus proven against contracts written to break it has not yet been
tested.

Slither returned twenty-one results, six more than step 4 and all of them the
model's share of the same benign classes: zero defaults for two counters and two
storage arrays, gas in loops that return after one iteration, and the queue
traversal documented in step 3.

Leads not pursued:

- **Whether `claims/recorded-claim-never-shrinks/v1` should be relaxed.** Saying
  a recorded claim is never written *down* would still catch the specimen it was
  built for, and would hold over an open batch. It would also stop catching a
  system that silently raises a claim nobody asked to raise, which conservation
  does not see because moving claim into a batch moves no value. One design
  should not settle a law on its own, and a second integration is the honest way
  to decide.
- **A fee can drop pooled claims below what is owed on open batches.**
  `accrueFee` caps at claims less what is reserved, and reserved cannot exceed
  what the market holds, so a delinquent market can take a fee that leaves it
  promising more withdrawals than lenders are owed in total. No law covers it.
  It is a real gap and a new law rather than a fix to this one.
- **The nine carried from earlier steps**, each recorded in the round that found
  it.

## Step 5, round 2 -- 2026-08-16

Reviewed: the tree with round 1 applied, and the one thing round 1's fix could
not check about itself.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R2-01 | medium | scripts/pandects_lib/render.py | The renderer hardcoded "Nine laws in three families" and looped over its own list of families rather than the catalogue's. A tenth law would produce a document that lies about its own count, and a law filed under a new family would vanish from the document entirely -- neither of which the drift test can see, because that test compares the document against this renderer and both would be wrong the same way. | fixed in 9eb1314 |
| S5-R2-02 | low | .gitignore | The demo tells a reader to write `search-record.json` into the plugin, and nothing ignored it. Following the documented walkthrough left the repository dirty. | fixed in 9eb1314 |

**S5-R2-01, and why round 1's fix could not have caught it.** Making the
document a rendering closed the gap between the document and the renderer. It
opened a new one between the renderer and the catalogue, and a test comparing
the first pair is structurally blind to the second. The preamble now counts what
it rendered, the headings come from the laws rather than from a vocabulary, and
two tests assert both from outside: a one-law catalogue renders "One law in one
family", and a law filed under a family the renderer has never heard of still
appears under its own heading.

**What ran.** 71 Solidity tests across ten suites, 106 catalogue, checker,
search-record and document tests, the repository's 9, `pandects check` over nine
laws, and `pandects render` reproducing the committed document byte for byte.
Scoped rather than swept: this round's diff is one module, one ignore rule and
three tests, none of it Solidity.

Leads not pursued:

- **`slither_results.json` is still tracked.** Raised in step 3, raised again
  here, and still generated output sitting in the index. It is a two-line fix
  that belongs to nobody's step.
- Two carried from round 1, each recorded there with its reason: whether the
  claim law should be relaxed, and the fee that can drop pooled claims below
  what is owed on open batches.

## Step 5, round 3 -- 2026-08-16

Reviewed: the whole step with both rounds applied, and whether the integration
disturbed anything the earlier steps prove.

**What ran.** The full sweep: 71 Solidity tests across ten suites under forge
1.7.1, 106 catalogue, checker, search-record and document tests on Python 3.14,
the repository's 9, `pandects check` over nine laws, `pandects render`
reproducing the committed document byte for byte, Slither 0.11.6 over 28
contracts, Echidna 2.3.3 against the Wildcat campaign and three earlier
harnesses with the shipped configuration, and Medusa 1.5.1 against the Wildcat
campaign at 20,000.

**The engines.** `WildcatMarketCampaign` failed `recorded_claim_never_shrinks`
and nothing else, under both engines, which is the documented expectation and
the finding this step exists for. `SoundCampaign` failed nothing.
`DrivenClaimHaircut` and `ObservedQueueJumped` each failed their own law alone,
unchanged from step 4.

**Slither.** Twenty-one results, the same set as round 1 and none of them a
finding: zero defaults for two counters and two storage arrays, gas in loops
that return after one iteration, and the queue traversal documented in step 3.

No findings.

Leads not pursued: whether the claim law should be relaxed and the fee that can
drop pooled claims below what is owed on open batches, both from round 1;
`slither_results.json` still tracked, from round 2; and the nine carried from
earlier steps. Each is recorded in the round that found it.

## Leads closed since

The rounds above stay as they were written. This section is what became of two of
the leads they left open, so a reader meeting them does not have to guess whether
anybody went back.

**A fee can drop pooled claims below what is owed on open batches**, from step 5
round 1, which closes with "No law covers it. It is a real gap and a new law rather
than a fix to this one." One does now.
`claims/pooled-claims-cover-open-batches/v1` was added in the
`withdrawal-batch-fee-law` frontier run, with `specimens/FeeFromQueued.sol`, a
four-call counterexample reduced by Echidna, and a campaign both engines drive. The
lead's own reading was right on both counts: the cap against the earmark was the
defect, and it needed a law rather than a change to the one it sat beside. Both
`Sound` and `WildcatMarketModel` were corrected, and the study, the runbook and that
run's rounds are in `docs/withdrawal-batch-fee-law/` and the repository's
`audit/AUDIT.md`.

**`slither_results.json` still tracked**, from step 5 round 2. Closed in the same
run. The ignore rules for it and two sibling artefacts were written one directory too
shallow, so an engine invoked from a subdirectory wrote past them. The patterns are
depth-independent now and the three files are untracked.

The other leads those rounds left open are untouched, including whether
`claims/recorded-claim-never-shrinks/v1` should be relaxed, which still wants a
second integration to decide.
