# Rolling Fiat frontiers audit

## Step 1, round 1 -- 2026-08-17

The committed non-Solidity diff has no open finding. Status: clean.

The review checked the nine landing-page commands, frontier agreement across
marketplace copies, the scope of skill-level README deletions, stale live
links, the protected Lazarus fixture digest, and the Alexandria receipt
regenerated after Probitas added two venues. The repository Python matrix and
Pandects Foundry checks pass.

Leads not pursued: none.


## Compound v3 Phase 0, step 1, round 1 -- 2026-08-17

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `plugins/alexandria/scripts/alexandria_lib/compound_registry.py` | Offline validation checked the registry's shape and pin labels but did not bind all 28 generated entries to the reviewed registry bytes; Git replace objects could also affect source reads. | fixed in this round |
| S1-R1-02 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | Rebound malformed RPC results exposed uncontrolled type errors; an error response could also carry a result, and a nested trace-filter frame was not tied to the selected transaction. | fixed in this round |
| S1-R1-03 | high | `plugins/tabularium/scripts/tabularium_lib/compound_witness.py` | A relevant slot-0 or `userBasic` write at an unexpected depth was silently skipped when a later write restored the expected poststate, leaving an unexplained write out of the witness. | fixed in this round |
| S1-R1-04 | medium | `plugins/tabularium/scripts/tabularium_lib/compound_witness.py` | Witness verification used unbounded path reads and did not verify that the imported Alexandria module came from the sibling plugin. | fixed in this round |

The review covered the study risk register, the full implementation diff,
registry and corpus pins, capture bounds and secret handling, JSON-RPC
request/result binding, proxy and implementation storage attribution, call to
opcode alignment, Ethereum Keccak, signed `int104` decoding, offline no-write
behaviour and immutable release bytes. Focused suites now pass 253 Alexandria
tests and 134 Tabularium tests. Both socket-denied rebuilds match the committed
release and witness.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 2 -- 2026-08-17

- S1-R2-01 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | Round 1's top-level type checks did not cover malformed struct-log elements, nested prestate maps or non-hexadecimal proxy runtime code, so some rebound evidence could still fail outside the controlled refusal path. | fixed in this round

The hardening review also checked the registry generator against the pinned
Comet Git objects with replacement refs disabled. Its bytes match the
committed registry. The focused hostile tests and both socket-denied rebuilds
pass after the nested evidence checks.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 3 -- 2026-08-17

- S1-R3-01 | medium | `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` | The capture bounded each response but not aggregate bytes, so a permitted 48-request run could exhaust disk well before a component crossed its individual ceiling. | fixed in this round
- S1-R3-02 | medium | `plugins/tabularium/scripts/tabularium_lib/compound_witness.py` | The principal fact pointed at the entire opcode list and only the poststate slot; it did not bind the prestate map that establishes an absent slot as zero or each exact principal-writing struct log. | fixed in this round

The aggregate capture cap is 128 MiB and fails before installation. The
principal fact now selects the prestate storage map, exact poststate slot and
each contributing struct log. The witness manifest also binds the fact byte
count. Focused tests and both offline rebuilds pass with the regenerated
unpublished witness bytes.

Leads not pursued: none.

## Compound v3 Phase 0, step 1, round 4 -- 2026-08-17

The fixed non-Solidity tree has no open finding. Status: clean.

The clean review repeated the registry, capture, JSON-RPC, trace alignment,
storage attribution, source-selector, safe-read, schema and immutable-byte
checks against the accumulated audit branch. All 255 Alexandria tests and 134
Tabularium tests pass. Both socket-denied rebuilds match, and the twelve
published Goldfinch and Euler truth digests are unchanged.

Leads not pursued: none.

## Fiat installed-path proof, step 1, round 1 -- 2026-08-17

The Solidity suite was waived because this step changes only Markdown
evidence and governed skill metadata. The review covered every changed line
against the runbook risk register.

- S1-R1-01 | low | `plugins/hexaemeron/docs/fiat-installed-path-and-maturity-proof/proof.md` | The proof reported 14 non-blocking Imprimatur signals, but the reproducible per-file total is 15. | Fixed on the stacked audit branch before round 2.

Leads not pursued: publisher authentication, cache signing, native Windows
support, and general release attestation are outside this frontier and are
not claimed by the proof.

## Fiat installed-path proof, step 1, round 2 -- 2026-08-17

The corrected non-Solidity tree has no open finding. Status: clean.

The clean review repeated the controller-path, target-root, receipt-order,
source-hash, frontier-version, digest, maturity, test-result, and prose-count
checks against the stacked branch.

Leads not pursued: publisher authentication, cache signing, native Windows
support, and general release attestation remain outside this frontier and are
not claimed by the proof.

## Imprimatur labelled prose, step 1, round 1 -- 2026-08-18

The Solidity suite was waived because this step changes a Python evaluator,
frozen evaluation data, tests, prose and governed skill metadata. The review
covered provenance and the 1 August 2025 cutoff, default-branch reachability,
blind-id separation, independent annotator ids, UTF-8 offsets, source-group
split isolation, duplicate checks, one-to-one span pairing, metric
denominators, candidate freezing, the spent holdout and the open-frontier
decision.

- S1-R1-01 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/evaluate_labelled_corpus.py` | The evaluator parsed the published schemas but did not apply them to fixture rows, and it did not verify the annotation-seal or candidate-freeze digests before scoring. A changed row or schema could therefore be evaluated under the same published evidence claims. | Fixed in this round: the standard-library evaluator now enforces the schema subset, checks both digest manifests, and rejects identical annotator ids; mutation regressions cover row and schema changes.

The focused evaluator has 15 passing checks after the fix. The 55 Imprimatur
tests, 61 Hexaemeron tests and 14 repository tests also pass. Replaying
`final.json` still produces the same metrics and gate decisions.

Leads not pursued: model authorship beyond the declared provenance rule,
population-prevalence claims and tuning against the spent v1 holdout are
outside this frontier and are explicitly disclaimed by the fixture.

## Imprimatur labelled prose, step 1, round 2 -- 2026-08-18

The fixed non-Solidity tree has no open finding. Status: clean.

The clean review repeated the fixture-row schema checks, annotation and
candidate digest checks, distinct-annotator check, UTF-8 span validation,
split isolation, metric replay and frontier digest verification against the
stacked audit branch. The focused evaluator has 15 passing checks and the
published calibration and final reports replay without a byte difference.

Leads not pursued: model authorship beyond the declared provenance rule,
population-prevalence claims and tuning against the spent v1 holdout remain
outside this frontier.

## Withdrawal batch fee law, step 1, round 1 -- 2026-08-18

The Pashov pair did not run and no campaign ran, because this step commits two
markdown documents and touches no Solidity. Saying so is the point: the
`security_suite` receipt names `x-ray`, `solidity-auditor` and `fizz`, none of
them read this diff, and a zero count here would assert they had. The review
instead read the committed spec against the risk register it declares, against
the nine shipped laws, and against the two models it proposes to correct.

- S1-R1-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/study.md` | The study asserted that all nine laws hold in the violating state, but only the five single-state laws had been executed. The four pair laws were reasoned about from what a fee does not touch. In a corpus whose whole argument is that a passing campaign proves nothing without a specimen, an argued verdict presented beside measured ones is the same defect one level up. | Fixed in this round: all four pair laws executed against the pair on both models, and the study now reports what was run. `accrual/path-independent/v1` returns held and the study says that verdict carries no weight, because the law compares two runs rather than one system's before and after.
- S1-R1-02 | low | `plugins/pandects/docs/withdrawal-batch-fee-law/study.md` | The study named a fee leak in `integrations/wildcat/WildcatMarketModel.sol` with figures, and never fixed the boundary to the deployed market contracts. The plugin's own applicability document warns that nothing in the model should be mistaken for them; a reader meeting the figures first could take the study as a claim about the protocol. | Fixed in this round: the study states that the finding is about the reduced model and the corpus's silence, and that it establishes nothing either way about the deployed contracts.

A third lead was checked and is not a finding. The study's chosen statement is
false of `Sound` as shipped, and the study says so and builds on it. That is the
method in `docs/writing-a-law.md` working rather than a defect in the spec.

Leads not pursued: whether the two model corrections should ship as their own
step ahead of the law, which the runbook argues against on the grounds that
`pandects.py check` and the corpus diagonal leave no green intermediate state;
and the seven property families deferred from the original delivery, which are
outside this frontier.

## Withdrawal batch fee law, step 1, round 2 -- 2026-08-18

Again no Solidity in the diff and no campaign, for the same reason, stated again
rather than counted as a clean suite run. This round read the round-1 fixes back,
then checked the runbook's own numbers against the test files it points step 2 at.

- S1-R2-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | The runbook sized step 2's test work as the diagonal growing "from 9x9 to 10x10 over the single-state half". No such table exists. `test/Corpus.t.sol` runs its diagonal over the single-state laws alone, where `COUNT` is 5, and `test/Pairs.t.sol` runs over 3, with path independence handled separately. Nine and ten are corpus totals. Whoever implemented step 2 from the runbook would have gone looking for a table with the wrong shape. | Fixed in this round: the runbook names both dimensions and says that ten is a total rather than a dimension.

The round-1 fixes were re-read and hold. The four pair-law verdicts in the study
match what was executed, the path-independence caveat is stated where the verdict
appears, and the boundary sentence about the deployed contracts sits in the
problem statement where a reader meets the figures.

One check found nothing and is worth recording because it removes work from step
2. `test_the_sound_reference_holds_every_law` charges its fee before it reserves,
so the queue is empty when the cap applies and the tightened cap cannot change
that test. The runbook now says so.

Leads not pursued: the two carried from round 1, unchanged.

## Withdrawal batch fee law, step 1, round 3 -- 2026-08-18

No Solidity and no campaign again. This round read the runbook's file lists
against what the repository actually generates and against what it treats as a
record, which is the class of error the previous two rounds had not looked at.

- S1-R3-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 2 listed `docs/catalogue.md` as a file to write and step 4 listed it again as prose to reconcile. It is neither: `python3 scripts/pandects.py render` generates it and `tests/test_documents.py` checks it against the renderer. A hand-edit either fails that check, or passes it by reproducing what the renderer would have produced and thereby hides a real drift. An earlier round of the original delivery, S5-R2-01, fixed the renderer for exactly this reason. | Fixed in this round: step 2 regenerates it and says why, and step 4 drops it from the prose surfaces and names the command.
- S1-R3-02 | low | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 4's reconciliation list left this run's own study and runbook out without saying so, and both of them claim Pandects ships nine laws. The omission reads as an oversight rather than a decision, so an implementer would either rewrite a spec into disagreement with the run it specifies, or leave a claim stale with nothing recording which was meant. | Fixed in this round: step 4 states that the two spec documents are records on the same footing as the audit log's historical rounds and are not reconciled, and why rewriting them would be worse.

The round-2 fix was re-read against the sources. `COUNT` is 5 in
`test/Corpus.t.sol` and 3 in `test/Pairs.t.sol`, which is what the runbook now
says.

Leads not pursued: the two carried from round 1, unchanged.

## Withdrawal batch fee law, step 1, round 4 -- 2026-08-18

No Solidity and no campaign. This round read step 3's evidence requirement
against the tooling that exists to satisfy it, and re-checked which documents in
the plugin are generated, which the previous round had only established for one of
them.

- S1-R4-01 | medium | `plugins/pandects/docs/withdrawal-batch-fee-law/runbook.md` | Step 3 asked for "a search record for each run" and for "a run record beside the existing campaign evidence", without naming a mechanism. One exists and does not cover the case: `python3 scripts/pandects.py run` writes a search record and knows only the `foundry` engine. An implementer would either read the requirement as satisfied by that command for all three engines, which would silently drop the two fuzzers the step exists to run, or invent a record format for them. | Fixed in this round: step 3 names the command for the Foundry record, says it has no Echidna or Medusa support, and requires the two fuzzers to be recorded as audit prose the way the original delivery recorded them. It also says not to extend the runner here.

`docs/applicability.md` was checked and is not generated. `pandects render` writes
`docs/catalogue.md` and nothing else, so step 4's remaining prose surfaces are
hand-written and correctly listed.

Leads not pursued: extending the search-record runner past `foundry`, now stated
in the runbook as out of scope for this step and a candidate frontier of its own;
and the two carried from round 1.

## Withdrawal batch fee law, step 1, round 5 -- 2026-08-18

No Solidity and no campaign, for the fifth time and for the same reason. This
round re-read the four earlier fixes against their sources and then resolved every
file path the two documents name, which is the check that catches a spec rotting
against a repository that moved under it.

The fixed non-Solidity tree has no open finding. Status: clean.

Thirty-nine distinct paths are named across the study and the runbook. Every one
resolves, except the two the run exists to create,
`src/laws/PooledClaimsCoverOpenBatches.sol` and `specimens/FeeFromQueued.sol`, and
a glob in the sources list. The earlier fixes hold: the pair-law verdicts match
what was executed, the deployed-contract boundary sits where the figures are, both
diagonal dimensions match `COUNT` in their test files, `docs/catalogue.md` is
regenerated rather than written, the two spec documents are declared records, and
step 3 names the runner and its single engine.

Leads not pursued: extending the search-record runner past `foundry`; whether the
two model corrections should ship ahead of the law, which the runbook argues
against on the grounds that no green intermediate state exists; and the seven
property families deferred from the original delivery. Each is recorded in the
round that raised it.

## Withdrawal batch fee law, step 2, round 1 -- 2026-08-18

Reviewed: the whole of the step's diff. The new law, both model corrections, the
specimen, the counterexample, the catalogue entry, the renderer, the test that
counted for it, and the Wildcat notes.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `search-record.json` | The record shipped at the plugin root stated nine laws and a corpus digest taken over nine, and the corpus now holds ten. Nothing compared it with the catalogue, in CI or in the suite, so it had gone stale silently and would have gone stale again on the eleventh law. A stale search record is worse than an absent one: it carries a count and a digest with the authority of something a script produced, and nothing about reading it says when. | Fixed in this round: regenerated, and three tests now hold the shipped record against the catalogue's law count, its recomputed digest and its version. Each was made to fail against a perturbed record before being kept. |
| S2-R1-02 | medium | `test/SoundInvariant.t.sol` | The harness asserted the five old single-state laws over the reference under fuzzing and did not assert the sixth. So the one law whose correctness rests on two caps that were just rewritten was the one law no search checked against the reference; the diagonal tested it at a single hand-derived state. A cap is exactly the thing a single state cannot vouch for. | Fixed in this round: `invariant_pooled_claims_cover_open_batches` added. It passes at 64 runs and 4096 calls with no reverts. |
| S2-R1-03 | medium | `adapters/medusa/README.md` | The document offered the command line as an alternative to the config file and then claimed, two paragraphs later, that the settings match `adapters/echidna/echidna.yaml`. Both cannot be true. Naming a target on the command line means not passing `--config`, so the run happens under Medusa's defaults, with assertion testing on where the file turns it off. Anyone following the documented command and recording the shipped configuration would be recording a different search from the one they ran. Passing both is worse: the file's empty `targetContracts` beats `--target-contracts`, and Medusa exits with no tests found before searching anything, which is the silent non-run this same file warns about at the bottom. | Fixed in this round: the file route is now the documented one, the command-line route is named as a run under Medusa's defaults, and the both-flags case is written down with the exact message it exits on. |

**What ran.** 75 Solidity tests across ten suites under forge 1.7.1 and solc
0.8.28, up from 74 by the invariant added here. 109 catalogue, checker,
search-record and document tests on Python 3.14, up from 106 by the three gates
added here. The repository's 20. `pandects check` over ten laws, every part
present. Slither 0.11.6 over 50 contracts. Echidna 2.3.3 against `SoundCampaign`
and `WildcatMarketCampaign` with the shipped configuration and seed 20260816.
Medusa 1.5.1 against `SoundCampaign` at twenty thousand, run through a copy of
the shipped config with `targetContracts` filled in, for the reason S2-R1-03
gives.

**The engines on the corrected models.** `SoundCampaign` failed nothing under
either engine: eight properties passing over 20,116 calls under Echidna, eight
passing under Medusa. `WildcatMarketCampaign` failed
`recorded_claim_never_shrinks` and nothing else, which is the documented
expectation for a design whose batches accumulate while open, and it is unchanged
by the fee correction. So neither correction cost the corpus a property, and
neither introduced one.

**What the engines did not test.** The new law. `src/campaigns/Specimens.sol`
carries one property per law and the new one is not among them, which is step 3's
whole content. Foundry's invariant runner reaches it after S2-R1-02 and the two
fuzzers do not reach it yet. Saying so is the point: eight properties passing is
evidence about eight laws.

**Slither.** Twenty-three results across three classes, all of them the same
benign set the original delivery documented: cached array length in four queue
traversals, costly operations inside a loop that returns after one iteration, and
one unused constant inherited by a specimen. Nothing names the new law or the new
specimen.

**The independence argument, and its limit.** `FeeFromQueued` can only lower
`claims` further than the reference would, so the laws it could break are the
ones bounded below by `claims`. The old cap stopped exactly at `reserved`, which
is why `reserves-backed-by-claims` survives it, and the remaining eight read
quantities a fee does not move. That is an argument rather than a search, the
diagonal checks one state, and step 3 is where an engine gets to disagree.

Leads not pursued:

- **`pandects run` knows one engine.** The shipped record carries the Foundry
  campaign and nothing else, so the Echidna and Medusa evidence in this run lives
  in this log as prose. That is the arrangement step 3 was told to keep and it is
  a candidate frontier of its own, recorded in the runbook.
- **The two carried from step 1**, unchanged.

## Withdrawal batch fee law, step 2, round 2 -- 2026-08-18

Reviewed: the tree with round 1 applied, and what round 1's own commit did to it.

- S2-R2-01 | medium | `.gitignore` | Round 1's commit tracked three engine artefacts: `crytic-export/combined_solc.json`, `.medusa-artifact-hash` and `slither_results.json`. The ignore rules for all three existed and did not match, because they were written as `plugins/*/` and an engine writes beside wherever it was invoked from. The Medusa run went through a config under `adapters/medusa/`, so the artefacts landed two levels below the plugin root and walked straight past a one-level pattern. This is the lead the original delivery carried from its own step 5 round 2 about `slither_results.json` being tracked, arriving again by the same mechanism. | Fixed in this round: the three files are untracked, the patterns are depth-independent, and a fresh Medusa run confirmed all three are ignored where they are actually written rather than where the old patterns expected them.
- S2-R2-02 | low | `.gitignore` | `plugins/*/search-record.json` sat in the fuzzing-output section while the file it names is tracked, shipped as evidence, and as of round 1 held to the catalogue by three tests. The two statements cannot both be right. Left alone, a fresh clone that regenerated the record would show no diff, and deleting it would draw no complaint from git. | Fixed in this round: the entry is removed and the reason it is not output is written where the entry used to be.

**What ran.** The full suite again on the fixed tree: 75 Solidity tests under
forge 1.7.1, 109 Python tests, the repository's 20, `pandects check` over ten
laws. Medusa 1.5.1 twice more, once to reproduce the artefact paths and once to
confirm they are ignored. No engine re-run was needed for the findings themselves,
because neither touches a contract.

**What round 1's fixes look like on re-reading.** The three search-record gates
were re-checked against a perturbed record and each still fails for its own
reason. `invariant_pooled_claims_cover_open_batches` still passes at 64 runs and
4096 calls. The Medusa README's file route was exercised in this round, which is
how the artefact paths in S2-R2-01 were found: following one's own corrected
instructions is what surfaced the defect the instructions caused.

Leads not pursued: the two carried from step 1, and `pandects run` knowing one
engine, carried from round 1.

## Withdrawal batch fee law, step 2, round 3 -- 2026-08-18

Reviewed: the new law against the corpus's own edge-case tests rather than
against its specimen. The first two rounds looked at evidence and at tooling.
This one asked which of the assertions the other nine laws face were never
extended to the tenth.

- S2-R3-01 | medium | `test/Corpus.t.sol` | `test_a_queue_law_over_a_target_with_no_queue_reverts` walked a hardcoded `Law[2]` of the two queue laws that existed when it was written. The new law is a third and was not in it, so nothing asserted that it reverts rather than returning a verdict against a target with no queue. The test's own comment names the failure it exists to prevent: a law returning true there reports that a system with no queue keeps its queue in order. | Fixed in this round: the array is a `Law[3]` and the new law is asserted with the other two.
- S2-R3-02 | medium | `test/Corpus.t.sol` | The new law sums unchecked and reports the overflow as a violation, and no test could reach that branch. `test_a_sum_that_overflows_is_reported_as_a_violation` uses `Extreme`, which implements no queue, so a queue law reverts on the read long before its own addition is asked to hold the answer. The branch that exists precisely so the law does not fall silent where the numbers are worst was itself unexercised, which is the corpus's own argument about untested properties turned on one of its laws. | Fixed in this round: `ExtremeQueue` reports two claims each owed everything there is, and `test_a_queue_law_reports_its_own_overflow` asserts the law returns rather than reverts, returns violated, and gives the overflow as its reason.

**What ran.** 76 Solidity tests under forge 1.7.1, up from 75 by the assertion
added here. 109 Python tests, the repository's 20, `pandects check` over ten laws.
No engine re-run: both findings are test coverage over an unchanged law, and
neither alters a contract the engines drive.

**Why the second one is worth a fixture.** The overflow branch is not decoration.
In 0.8 the addition reverts, a revert under `fail_on_revert = false` carries no
verdict, and the law would go quiet exactly where a system's numbers had gone
furthest wrong. The corpus argues that about every other summing law and tests it
for two of them. Asserting the detail string as well as the verdict is what makes
the test evidence that this branch ran rather than evidence that some branch
returned false.

Leads not pursued: `Extreme` and `ExtremeQueue` are two fixtures where the
difference is one interface, and a single parameterised fixture would serve both.
Left alone deliberately: the split is what makes the two tests say different
things, and merging them would put a flag in a fixture whose whole job is to be
obvious. The three carried from earlier rounds and from step 1 stand.

## Withdrawal batch fee law, step 2, round 4 -- 2026-08-18

Reviewed: what an integrator gets rather than what the corpus proves about
itself. Earlier rounds read the evidence, the tooling and the edge cases. This one
followed the law outwards, into the files somebody else's protocol actually
inherits.

- S2-R4-01 | high | `adapters/CorpusBase.sol` | The adapter an integrator inherits names its laws one by one in Solidity and had nine of the ten. So the corpus documented ten laws, `pandects check` counted ten, and anybody pointing `CorpusObserver` at their own market ran nine, with no signal anywhere: the adapter compiles, `queueHolds` returns a verdict, `explainOneState` returns five reasons, and every test passes. The one law missing was the one this whole run exists to add. Called high because it is exactly what the corpus is built to refuse, a law that is never asked reported as a corpus that holds, reaching the surface an outsider inherits rather than a specimen written to be broken. | Fixed in this round: the adapter carries it, `queueHolds` judges it, `explainOneState` returns six reasons and says why its width is the catalogue's count, and `test/Adapters.t.sol` reads six.
- S2-R4-02 | medium | `tests/test_documents.py` | Nothing tied the adapter to the catalogue, which is why S2-R4-01 could happen quietly and would happen again on the eleventh law. The plugin already has this check twice over, for the rendered catalogue and for the integration notes, and the one surface where the omission reaches a third party had none. | Fixed in this round: `ShippedAdapterTests` holds every catalogued law to the adapter, with path independence excluded as an exact pinned set rather than a skip list, so a second exclusion has to be argued for in the file. Made to fail by removing the law from the adapter before being kept.

**What ran.** 76 Solidity tests under forge 1.7.1, 111 Python tests, up from 109
by the two checks added here, the repository's 20, and `pandects check` over ten
laws. The adapter change is a contract change, so Slither 0.11.6 ran again over 50
contracts with no new result, and Echidna 2.3.3 ran again against `SoundCampaign`:
eight properties passing, seed 20260816. The campaign harness does not reach the
new law, which is step 3, so that number is still evidence about eight laws.

**Why this one is the important finding of the step.** The corpus's argument is
that a passing campaign proves nothing without a specimen, because a law that
cannot fail is invisible in a green result. A law absent from the shipped adapter
is worse than one that cannot fail: it is one nobody asks, on the surface furthest
from anybody who would notice. `specimens/FeeFromQueued.sol`,
`test_pooled_claims_cover_open_batches_counterexample`, the catalogue entry and
`invariant_pooled_claims_cover_open_batches` were all correct while
`CorpusObserver`, the contract an integrator points at their own market, ran nine
laws.

**Carried into step 3 with a mechanism rather than a hope.**
`src/campaigns/Specimens.sol` has the same shape and the same hazard and is still
unchecked. The check cannot land here: until the harness carries the law it would
fail, and a check added after the change it was meant to force is a check written
to pass. The runbook's step 3 now requires `ShippedAdapterTests` to be extended to
the campaign harness in the same commit that adds the property.

Leads not pursued: the merged-fixture question from round 3, `pandects run`
knowing one engine, and the two carried from step 1.

## Withdrawal batch fee law, step 2, round 5 -- 2026-08-18

Reviewed: round 4's own fix, on the suspicion that gating one file and calling the
class closed was too quick. It was.

- S2-R5-01 | high | `adapters/foundry/CorpusInvariants.sol` | The same defect as S2-R4-01, one file along and untouched by its fix. `CorpusBase` carries the law objects; this file decides which of them a Foundry run asserts, and it declared eight invariants for nine laws. After round 4 the adapter carried the tenth law and no Foundry invariant asked it, so an integrator extending `CorpusOneStateTest` still ran nine. Carrying a law and never asserting it is the same silence as not carrying it. | Fixed in this round: `invariant_pooled_claims_cover_open_batches` added, standing down with the other queue laws when `hasWithdrawalQueue` is false, and the two comments that counted the queue laws as two now say three.
- S2-R5-02 | medium | `tests/test_documents.py` | Round 4's check read one path and asserted the law's component name appeared in it. That is why it did not see S2-R5-01: the component name did appear, in the file that binds it, and the check had no opinion about the file that asserts it. A check aimed at one of two surfaces is not a check on the class. | Fixed in this round: the check takes a list of shipped adapters. It maps the variable names `CorpusBase` binds components to, classifies each law's shape by reading whether its component extends `Law` or `PairLaw` rather than from a hand-kept list, and asserts every one-state law's variable is asserted in the Foundry adapter. Made to fail by deleting the invariant while leaving the law bound, which is the exact shape S2-R5-01 had.

**What ran.** 76 Solidity tests under forge 1.7.1 and 111 Python tests, up from
109 in round 4 by one net: round 4's second check was replaced rather than added
to, because the version it shipped counted braces and carried a dead local. The
repository's 20 and `pandects check` over ten laws.

**On round 4's second check.** It passed, it was green, and it could not have
caught what round 5 found. It also contained a statement with no effect and a
subtest that asserted a string appeared somewhere in a file. Recorded plainly
because the step's own findings are about tests that cannot fail, and writing one
in the round that argues against them is worth writing down rather than quietly
replacing.

**The class, now that it has been walked properly.** Six shipped surfaces name
laws: the catalogue, the rendered document, the integration notes, `CorpusBase`,
`CorpusInvariants` and the campaign harness. Five are now held to the catalogue by
a test. The sixth is the campaign harness, still step 3's, still scheduled in the
runbook with the reason it cannot be gated earlier.

Leads not pursued: the merged-fixture question from round 3, `pandects run`
knowing one engine, and the two carried from step 1.

## Withdrawal batch fee law, step 2, round 6 -- 2026-08-18

Reviewed: the rest of the class rounds 4 and 5 opened. Two rounds had each found
the same defect in one more file, so this round enumerated every shipped file that
names laws before looking at any of them.

- S2-R6-01 | high | `adapters/echidna/CorpusEchidna.sol`, `adapters/medusa/CorpusMedusa.sol` | The third and fourth occurrence, in the two adapters an integrator extends to run the corpus under a fuzzer. Each declared five one-state properties and the tenth law was not among them, so anyone pointing Echidna or Medusa at their own system through the shipped adapter searched nine laws. The runbook had scheduled both files into step 3. Rounds 4 and 5 are the argument against that: a law missing from a surface an outsider inherits is a defect in the step that adds the law, and scheduling is how it survived twice. | Fixed in this round: both adapters carry the property, standing down with the other queue laws when `hasWithdrawalQueue` is false.
- S2-R6-02 | medium | `tests/test_documents.py` | Round 5's check took a list of two paths, which was the right shape aimed at the wrong set. It knew about `CorpusBase` and the Foundry adapter and had no opinion about the two engine adapters, so it could not have caught S2-R6-01 either. Three rounds running, the check was narrower than the class. | Fixed in this round: the binding file and the asking files are separated, and the asking set is all three adapters that decide which bound law a run asks. Each was made to fail on its own by deleting one property at a time, which caught a fourth thing: the probe used for the Foundry file in the first attempt matched nothing, so a clean result there was the probe failing rather than the check passing. The exact-string version failed as it should.

**What ran.** 76 Solidity tests under forge 1.7.1, 111 Python tests, the
repository's 20, `pandects check` over ten laws, Slither 0.11.6 over 50 contracts
at 23 results with nothing new, and Echidna 2.3.3 against four campaigns with the
shipped configuration and seed 20260816.

**The evidence this round bought.** Every campaign that extends the shipped
adapters picked the new law up as a consequence of S2-R6-01's fix, so the engines
reached it in step 2 rather than step 3:

| campaign | the new law | its own expected failure | calls |
| --- | --- | --- | --- |
| `SoundCampaign` | not carried | none | 20,140 |
| `ObservedQueueJumpedEchidna` | passing | `queue_order_preserved` | 20,205 |
| `DrivenClaimHaircutEchidna` | passing | `recorded_claim_never_shrinks` | 20,176 |
| `WildcatMarketCampaign` | passing | `recorded_claim_never_shrinks` | 20,123 |

The last row is the one worth reading twice. Echidna searched 20,123 calls against
the corrected Wildcat model and did not reach a state where pooled claims sit below
what the open batches are owed. Before the correction, five calls written by hand
got there and took four fifths of a departing lender's money on the way. Each
campaign still fails exactly the property it was built to fail and no other, so the
new law did not arrive broad.

`SoundCampaign` extends `Campaign` in `src/campaigns/Specimens.sol` rather than the
shipped adapter, which is why it is the one campaign the new law does not reach.
That harness is step 3's remaining content and the last surface without a check.

Leads not pursued: the merged-fixture question from round 3, `pandects run`
knowing one engine, and the two carried from step 1.

## Withdrawal batch fee law, step 2, round 7 -- 2026-08-18

Reviewed: every file in the plugin that names laws, enumerated mechanically
before any of them was opened, because three rounds running had found the same
defect one file further along and inspection had picked the files in the wrong
order each time. Ten Solidity files import two or more laws and three documents
name three or more. One of the ten had not been looked at.

- S2-R7-01 | medium | `test/Wildcat.t.sol` | Step 2 added a row to the integration's applicability table saying the model holds the new law once corrected, with figures, and added no assertion behind it. `test_the_model_holds_every_one_state_law_it_claims` asserted five laws and the document claimed six. That document's own idiom is the opposite: it says of two other claims that they are watched happening rather than described, and the check requiring every catalogued law to appear in it exists because a claim nobody tests is the thing this plugin refuses. The claim was mine and it shipped bare. | Fixed in this round: the law joins the law-by-law assertion, and `test_a_delinquent_market_can_take_no_fee_from_a_queued_batch` drives the market into the state the notes describe and asserts the figures they quote -- 200 held, a batch owed 1000 unpaid, and a fee of nothing where the earmark cap permitted 800. Reverting the model's cap to `reserved()` makes it fail with "a fee was taken out of a queued batch".

**What ran.** 77 Solidity tests under forge 1.7.1, up from 76 by the assertion
added here, 111 Python tests, the repository's 20, and `pandects check` over ten
laws. No engine or Slither re-run: the only contract touched is a test.

**The enumeration, and what it settles.** Every shipped surface that names laws is
now either held to the catalogue by a test or scheduled with the reason it cannot
be. `adapters/CorpusBase.sol` binds them and is gated; the Foundry, Echidna and
Medusa adapters decide which are asked and are gated; `docs/catalogue.md` is
generated and drift-checked; `integrations/wildcat/APPLICABILITY.md` is gated for
mention and, after this round, asserted for the claim it makes; `test/Corpus.t.sol`
walks a diagonal of six; `test/SoundInvariant.t.sol` searches all six.
`src/campaigns/Specimens.sol` is the one surface left and it is step 3's, with its
check required in the same commit as its property. `docs/withdrawal-batch-fee-law/study.md`
names six law ids and is a record rather than a surface, which step 4 states.

Leads not pursued:

- **A gate on the applicability table itself.** Every law the table says holds
  could be required in an assertion in `test/Wildcat.t.sol`.
  It would
  have caught S2-R7-01 the way the adapter gates caught rounds 4 to 6. It needs a
  parser for a prose table with three laws that legitimately do not hold and one
  that holds under a condition, and a fragile parser guarding a document is a
  worse trade than the check is worth. Recorded rather than built, and it is a
  candidate frontier.
- The merged-fixture question from round 3, `pandects run` knowing one engine, and
  the two carried from step 1.

## Withdrawal batch fee law, step 2, round 8 -- 2026-08-18

Reviewed: the comments this step's own rounds wrote, on the principle that a round
which has spent six findings on untested claims should read its own. One of them
promised a guarantee that did not exist.

- S2-R8-01 | medium | `adapters/CorpusBase.sol` | Round 4 widened `explainOneState` to six and wrote above it that the width is the count of one-state laws in the catalogue and that `test/Adapters.t.sol` holds it to that count. The second half was false. That test reads `string[6]` because the adapter returns `string[6]`; the two are one number written twice and a test taking it from the file it checks would be wrong the same way. So an eleventh one-state law would leave the width at six and nothing would say so, which is the argument the renderer's own drift test makes, and the comment claiming otherwise was written in the round that found the same defect elsewhere. | Fixed in this round: `test_the_explanation_is_as_wide_as_the_one_state_laws` reads the signature out of the source, counts the one-state laws in the catalogue by the shape their components declare, asserts the two agree, and asserts each of those laws is the subject of one of the assignments. Narrowing the width and hollowing the last entry each make it fail for their own reason. The comment now names the test that exists.

**What ran.** 77 Solidity tests under forge 1.7.1, 112 Python tests, up from 111
by the check added here, the repository's 20, `pandects check` over ten laws, and
Slither 0.11.6 over 50 contracts at 23 results, unchanged. No engine re-run: this
round touched one comment and one test.

**Accepted, and why.** This is the eighth round, which is the configured ceiling,
so the tree has a fix in it that no later round has audited. That is the honest
shape of the close rather than a clean sweep: round 8 found one defect, fixed it,
and proved the fix fails when it should, and no ninth round exists to read the
proof back. The four leads below are accepted for the reasons given, none of them
because the rounds ran out.

- **A gate on the applicability table**, from round 7. It would catch the class
  S2-R7-01 belongs to, and it needs a parser for a prose table carrying three laws
  that do not hold and one that holds conditionally. A fragile parser guarding a
  document is a worse trade than the check is worth. A candidate frontier.
- **`pandects run` knows one engine**, from round 1. The shipped record carries the
  Foundry campaign, and the Echidna and Medusa results are written into the
  rounds above as prose rather than emitted as records.
  That is the arrangement the runbook fixes for step 3, and widening the runner is
  its own piece of work.
- **`Extreme` and `ExtremeQueue` differ by one interface**, from round 3. Merging
  them would put a flag inside a fixture whose job is to be obvious.
- Two more come from step 1 and stand unchanged. Whether the model corrections
  should have shipped as their own step, which the runbook argues against because
  no green intermediate state exists between them and the law. And the seven
  property families the original delivery deferred.

**The one surface still without a check.** `src/campaigns/Specimens.sol`, and it is
step 3's first line of work with the check required in the same commit as the
property. Recorded here as well as in the runbook, because it is the only thing
this step knowingly leaves for the next one.

## Withdrawal batch fee law, step 3, round 1 -- 2026-08-18

Reviewed: the whole of the step's diff, and first of all the check it added, since
step 2 spent six findings on checks narrower than the class they were written for.
It was narrower than the class it was written for.

- S3-R1-01 | medium | `tests/test_documents.py` | The campaign-harness check skipped every pair law. It classified each law by shape and returned early on anything that was not one-state, so the three pair properties the harness declares through `judgePair` were held to nothing, and a fourth pair law would arrive in the catalogue and not in the harness with a green suite either way. The check was written in the commit that closed this class for the one-state family and left the other half open. | Fixed in this round: pair-law bindings are read alongside the one-state ones and the property pattern accepts `judge` or `judgePair`, so both families are held under both prefixes. Deleting `echidna_recorded_claim_never_shrinks` now names that law.
- S3-R1-02 | medium | `tests/test_documents.py` | Nothing tied a catalogued specimen to a campaign. Every one has a campaign today, and `FeeFromQueuedCampaign` exists because this step added it by hand, so the eleventh specimen would have rested on somebody remembering. A specimen with a property to fail and no harness to fail it under is caught by the deterministic suite and by no search, and a campaign report says nothing about which specimens were in it. | Fixed in this round: every catalogued specimen must have a `<Specimen>Campaign` in the harness. Renaming `FeeFromQueuedCampaign` now names the law whose specimen went undriven.

**What ran.** 77 Solidity tests under forge 1.7.1, 114 Python tests, up from 113 by
the specimen check, the repository's 20, and `pandects check` over ten laws. No
engine re-run for the findings themselves: both are tests over an unchanged harness,
and the engine evidence this step exists for was taken in the implement phase and is
recorded below.

**The engines, on the harness this step built.** Both reach the specimen and neither
reaches anything else.

- engine: Echidna 2.3.3, seed 20260816; `pooled_claims_cover_open_batches`: falsified, shrunk to four calls; the other eight: passing; detail: `deposit`, `borrow(1)`, `reserve`, `accrueFee(1)`
- engine: Medusa 1.5.1, twenty thousand; `pooled_claims_cover_open_batches`: failed; the other eight: passing; detail: "pooled claims are below what the open batches are owed"

**A defect in the check, caught by the check.** The first version of the pair-law
pattern read `judgePair?`, which is `judgePai` followed by an optional `r` rather
than `judge` followed by an optional `Pair`. It matched the pair laws and missed
every one-state law, so twelve subtests failed at once and named the laws they could
not find. Worth recording because the failure was loud: a pattern that matches
nothing leaves `asked` empty and every law unfound, rather than passing quietly,
which is the behaviour a check guarding against silence should have.

Leads not pursued: the four accepted at the close of step 2 stand, and none of them
is touched by this step.

## Withdrawal batch fee law, step 3, round 2 -- 2026-08-18

Reviewed: the tree with round 1 applied, then the harness's own reporting path,
which no round had opened. The properties were right and the thing that tells you
why one failed was not.

- S3-R2-01 | medium | `src/campaigns/Specimens.sol` | `explain` returned eight reasons for the nine laws the harness now carries, and the missing one was the new law's. That function exists so a reader replaying a falsified sequence gets the law's own words with the numbers in them rather than reconstructing them from a call trace, and for the one law this run added it returned nothing. Both engines had already falsified that property, so the failure was reachable and its reason was not. This is the same defect as `explainOneState` in step 2, which is the third place in the plugin where a law count is written twice. | Fixed in this round: `explain` returns nine, the new law's reason sits with the one-state group, and the three pair-law positions moved by one. `test_the_campaign_explanation_is_as_wide_as_the_laws_it_carries` holds the width and the contents to the catalogue; narrowing it back and hollowing the entry each fail for their own reason.
- S3-R2-02 | low | `src/campaigns/Specimens.sol` | The comment on `FeeFromQueuedCampaign` said reaching the property needs three things and listed a deposit, a borrow and a fee. It needs four. The withdrawal request is the one it left out and the one that matters: with no recorded claim nothing is owed, and with a claim no larger than what is held the earmark covers it and the cap does not leak. Echidna's own shrink is four calls. | Fixed in this round: the comment names four, says which one the earlier draft dropped and why the property cannot be reached without it.

**What the index shift caught on the way.** `test/Explain.t.sol` read positions as
numerals, so inserting a one-state law in the middle of that group moved every
pair-law index by one and the compiler only objected to the width. A test asserting
`details[6]` carried a pair law's reason would have gone on passing against a
different law's reason had the widths happened to agree. The positions are named
constants now, with the reason written where they are declared.

**What ran.** 78 Solidity tests under forge 1.7.1, up from 77 by the reason
assertion for the new law, 115 Python tests, up from 114 by the width check, the
repository's 20, and `pandects check` over ten laws. No engine re-run: `explain` is
not a property and no property changed.

Leads not pursued: the four accepted at the close of step 2. None is touched here.

## Withdrawal batch fee law, step 3, round 3 -- 2026-08-18

Reviewed: the harness header, which is the last thing in this step's files stating a
number nothing checked, and the two claims that number rests on.

- S3-R3-01 | low | `src/campaigns/Specimens.sol` | The header reads "Nine of these eleven are expected to fail one property". Both numbers are written by hand, both move when a specimen is added, and this run has already found four counts written twice with nothing holding them. The figures were right; nothing said they would stay right. | Fixed in this round: a test counts the campaigns the file declares and the ones whose specimen breaks a law the harness asks, spells both out, and requires the header to match. Reverting the header to the pre-step counts names the two it should have read.

**The two exceptions, verified rather than reasoned.** The claim is that nine of
eleven campaigns fail a property, so two do not, and the two are worth an engine run
each because they are the exceptions the count depends on.

- campaign: `SoundCampaign`; result: nine properties passing; calls: 20,140
- campaign: `CompoundsPerStepCampaign`; result: nine properties passing; calls: 20,140

`CompoundsPerStepCampaign` is the interesting one. Its specimen compounds, which
breaks `accrual/path-independent/v1`, and no campaign can search that law because a
campaign drives one system along one route. So it holds everything a campaign can
ask, and the new property is among the nine it holds, which is independence evidence
for the new law from a specimen built to break something else.

**Round 2's own prose.** It shipped "load-bearing" in the audit entry and in the
comment that entry described, which imprimatur bans as a structural metaphor. The
lint ran after that commit rather than before it. Fixed in `364a7ac`, and recorded
here rather than left in a commit message, because the same mistake in a shipped
document is what step 2's rounds spent findings on.

**What ran.** 78 Solidity tests under forge 1.7.1, 116 Python tests, up from 115 by
the count gate, the repository's 20, `pandects check` over ten laws, and Echidna
2.3.3 against `CompoundsPerStepCampaign` with the shipped configuration and seed
20260816.

Leads not pursued: the four accepted at the close of step 2, none touched here.

## Withdrawal batch fee law, step 3, round 4 -- 2026-08-18

Reviewed: the step against its own exit conditions, then the diagonal against the
engines rather than against hand-derived states. Two conditions the runbook set for
this step had not been met.

- S3-R4-01 | medium | `test/Adapters.t.sol` | The step's exit asks for the new entry point to be exercised without an engine, the way `test_the_echidna_entry_points_answer` already does for an older law, and nothing called either of the new prefixed wrappers. They are two separate functions delegating to the same internal judgement, so one can be wired to the wrong law while the other is right, and only a campaign under that one engine would notice: the deterministic suite would pass and the other engine would agree with it. | Fixed in this round: `test_both_prefixes_answer_for_the_new_law` calls both before and after the four-call sequence, and asserts two unrelated laws stay held. Rewiring `property_pooled_claims_cover_open_batches` to a different law fails it by name.
- S3-R4-02 | low | `audit/AUDIT.md` | The step's exit asks that a Medusa record state the seed as unavailable rather than invent one. Round 1 recorded the Medusa run with its engine, version and call limit and said nothing about a seed at all, which is the absence this plugin's own discipline is about: silence reads as a run whose seed nobody wrote down rather than a run that has none to write. | Fixed in this round: recorded below, and the earlier table stands with this note against it.

**Medusa exposes no seed.** Medusa 1.5.1 takes no seed argument and reports none, so
the runs in rounds 1 to 4 carry the engine, its version, the configuration digest,
the call limit of twenty thousand and the corpus digest, and no seed. Echidna's runs
all carry seed 20260816 from `adapters/echidna/echidna.yaml`. A Medusa campaign here
is reproducible to the configuration and not to the sequence.

**The diagonal, under search.** The deterministic diagonal asserts each specimen
breaks its own law at one state. This is the same claim put to an engine, every
campaign in the harness, each at roughly twenty thousand calls with seed 20260816.

| campaign | the law it fails | the new law |
| --- | --- | --- |
| `SoundCampaign` | none | passing |
| `MintedClaimsCampaign` | `value_conserved` | passing |
| `OverReservedCampaign` | `reserves_backed` | passing |
| `OverPromisedCampaign` | `held_partitioned` | passing |
| `DebtForgivenCampaign` | `debt_falls_only_against_payment` | passing |
| `AccruesAtRestCampaign` | `no_accrual_at_rest` | passing |
| `CompoundsPerStepCampaign` | none searchable | passing |
| `ClaimHaircutCampaign` | `recorded_claim_never_shrinks` | passing |
| `QueueJumpedCampaign` | `queue_order_preserved` | passing |
| `PayableBeyondReservesCampaign` | `reserves_cover_payable` | passing |
| `FeeFromQueuedCampaign` | **the new law** | falsified, four calls |

Every campaign fails exactly one property and it is the one its specimen was built to
break. The new law fires on one specimen out of eleven and on none of the other ten
under search, which is the study's second risk answered by an engine rather than by
the argument the step opened with. Three adapter-based campaigns were run earlier in
step 2 and agree: `ObservedQueueJumpedEchidna`, `DrivenClaimHaircutEchidna` and
`WildcatMarketCampaign` each hold the new law and fail only their own.

**What ran.** 79 Solidity tests under forge 1.7.1, up from 78 by the entry-point
assertion, 116 Python tests, the repository's 20, `pandects check` over ten laws, and
Echidna 2.3.3 against eight campaigns in this round.

Leads not pursued: the four accepted at the close of step 2, none touched here.

## Withdrawal batch fee law, step 3, round 5 -- 2026-08-18

Reviewed: what these rounds have said about the suite, rather than the tree. Both
findings are about this log rather than the code, and both are the kind the honesty
rule at the top of Fiat's audit loop exists for.

- S3-R5-01 | medium | `audit/AUDIT.md` | Round 2 changed a function in `src/campaigns/Specimens.sol`, which is a contract, and recorded "No engine re-run: `explain` is not a property and no property changed." That was true of the engines and said nothing about Slither, which had not run against this step's contracts at all. Rounds 3 and 4 carried the same omission forward. A round that changes Solidity and reports the suite without one of its members has reported a suite that did not run. | Fixed in this round: Slither 0.11.6 run against the step's tree. 52 contracts, 23 results across the same three benign classes the original delivery documented, and nothing naming the new campaign or the new law. The rounds above stand with this note against them.
- S3-R5-02 | medium | `audit/AUDIT.md` | The `security_suite` receipt names `hexaemeron:x-ray`, `hexaemeron:solidity-auditor` and `hexaemeron:fizz`, and no round in either step has said what became of the third. Silence about a named member of the suite is the failure this log is supposed to make impossible, and it is worse here than a waiver would have been, because a reader counting three names against the rounds would assume all three ran. | Fixed in this round: stated below, plainly, with what was done instead and why.

**Fizz, and why the generator did not run.** `fizz` generates a stateful Solidity
fuzz suite under `test/fizz/` with its runtime metadata beside it. This plugin
already has that suite: `src/campaigns/Specimens.sol` is a hand-written harness with
one campaign per specimen and one property per law, and building or refreshing it is
the whole content of this step rather than something a round does to it. It sits
under `src/` on purpose, and the file says why: crytic-compile skips `test/` when it
builds a Foundry project, so a harness generated into `test/fizz/` is a harness
neither engine can see.

So the function `fizz` performs was performed, by hand, as the step's deliverable,
and the generator was not run because running it would produce a second harness in
the one directory this plugin documents as unreachable. That is a judgement, not a
waiver, and it is recorded here rather than left as an absence. `x-ray` and
`solidity-auditor` are the reading passes and the rounds above are what they
produced.

**What ran.** 79 Solidity tests under forge 1.7.1, 116 Python tests, the
repository's 20, `pandects check` over ten laws, and Slither 0.11.6 over 52
contracts. No engine re-run in this round: nothing in it touches a contract.

Leads not pursued: the four accepted at the close of step 2, none touched here.

## Withdrawal batch fee law, step 3, round 6 -- 2026-08-18

Reviewed: the fixed tree, and each check the five earlier rounds added, by breaking
the thing it guards and confirming it says so.

The fixed tree has no open finding. Status: clean.

**The checks, re-proved rather than re-read.** Removing a pair-law property fails the
prefix check. Renaming a specimen's campaign fails two checks at once, the
specimen-has-a-campaign one and the header count, which is the right answer and shows
they are independent. Narrowing `explain` back to eight fails the width check.
Changing "Nine of these eleven" to ten fails the header check. All four then pass
again with the file restored.

**What ran.** 79 Solidity tests across ten suites under forge 1.7.1 and solc 0.8.28,
116 catalogue, checker, search-record and document tests on Python 3.14, the
repository's 20, `pandects check` over ten laws, Slither 0.11.6 over 52 contracts at
23 results, and Echidna 2.3.3 over every campaign in the harness at roughly twenty
thousand calls each with seed 20260816.

**One asymmetry, stated rather than left to be noticed.** Echidna drove all eleven
campaigns. Medusa drove two: `SoundCampaign`, which holds everything, and
`FeeFromQueuedCampaign`, which is the specimen this step exists for. The step's exit
asks that both engines drive the new specimen and both do. The other nine campaigns
have Echidna's verdict and not Medusa's, and no claim here rests on Medusa having
searched them.

Leads not pursued: the four accepted at the close of step 2, none of them touched by
this step, and the Medusa coverage asymmetry above, which is a stated limit rather
than a defect.

## Withdrawal batch fee law, step 4, round 1 -- 2026-08-18

Reviewed: every document the step touched, the ledger against the versioning
contract, and the branch the step was built on. This step ships prose and a ledger
entry, so `x-ray`, `solidity-auditor` and `fizz` had no Solidity to read and none of
them ran. Saying so rather than recording a zero, for the reason step 3 round 5 gave.

- S4-R1-01 | medium | `plugins/pandects/audit/AUDIT.md` | The plugin's own audit log records this run's whole subject as a lead not pursued, closing with "No law covers it. It is a real gap and a new law rather than a fix to this one." A law covers it now, and nothing in that log said so. Its historical rounds stay as written, which is right, but that left a reader of the plugin's own record meeting an open gap that had been closed in another file. The same log also carries the `slither_results.json` lead, which this run closed in step 2 round 2. | Fixed in this round: a "Leads closed since" section says what became of both, names the law, the specimen, the reduced counterexample and where the run is recorded, and states which leads remain untouched. No historical round was edited.
- S4-R1-02 | medium | this log | The step was branched from a stale `origin/loop/2026-08-18-kronos`, taken before step 3's pull request merged, so the tree it was verified against did not contain step 3. The demo path caught it: `forge test` reported 77 where step 3 had closed at 79. Merging would not have reverted step 3, because the merge base was below it, but every number in the step's receipt would have described a tree that was never going to ship. | Fixed before the step was committed: the branch was reset to the current tip and the twelve-file change reapplied, which it did cleanly because step 3 and step 4 share no file. Re-verified after replanting: 79 Solidity tests, ten laws, no catalogue drift. Recorded here rather than left in the reflog, because the receipt would have carried the wrong evidence and only a count nobody was checking on purpose revealed it.

**The ledger, against the contract.** `pandects-v0.1.0` becomes `pandects-v1.1.0`:
the evolution counter moves once for a completed frontier job, generation and epoch
are retained, and `SKILL.md` frontmatter matches the ledger. The frontier revision
moves from `withdrawal-batch-fee-law` to `search-record-engine-coverage`, which an
evolution entry is allowed to do and a generation entry is not. The recorded SHA-256
was recomputed from the four ledger fields as written, including the trailing
newline, and matches the digest in the history row.

**The new frontier, and why it is not mature.** The contract asks whether another
pass has a concrete evidenced chance of material improvement. It does, and the
evidence is this run's own log: rounds in steps 2 and 3 recorded Echidna and Medusa
results as prose because `pandects run` emits one engine, `foundry`, and nothing
else. A corpus whose argument is that a campaign result means nothing without its
search record can machine-record one of the three engines it uses. That is a gap
this run demonstrated rather than one chosen from a list.

**What was reconciled.** Twelve documents carried the old frontier sentence and all
twelve carry the new one. Five prose law counts said nine and say ten. Two others say
nine and are right: one counts the laws other than this one, and one is about a
lexicon. `docs/catalogue.md` was regenerated rather than edited and produced no
diff, because it already counted ten from the catalogue.

**What ran.** The repository's 20 tests including the marketplace prose gate, 116
plugin tests, 79 Solidity tests under forge 1.7.1, `pandects laws` printing ten with
their applicability, `pandects check` over ten laws, and `pandects render` with no
drift.

Leads not pursued: the four accepted at the close of step 2, and the Medusa coverage
asymmetry stated in step 3 round 6.

## Withdrawal batch fee law, step 4, round 2 -- 2026-08-18

Reviewed: the tree with round 1 applied, then every count and claim in browsing prose
that the run had touched or should have. One it had not touched.

- S4-R2-01 | medium | `README.md` | The repository README says how many of the corpus's laws carry no tolerance, and it still said eight. Nine of the ten are exact; only `accrual/path-independent/v1` carries a bound. Step 4 had corrected the same claim in the plugin's own README and missed this one, so the two documents disagreed with each other and one of them disagreed with the catalogue. | Fixed in this round: nine, taken from the catalogue's `bounds` field rather than counted by eye.
- S4-R2-02 | medium | `tests/test_marketplace_prose.py` | Nothing held either README's corpus counts to the catalogue. The rendered document derives both of its counts, the adapters are held to theirs by the plugin's suite, and these two were hand-written sentences that a frontier run adding a law simply has to remember. This run corrected five of them and missed the sixth, which is the whole argument. | Fixed in this round: `test_pandects_prose_counts_the_laws_the_catalogue_holds` derives the total, the exact count and the family count from the catalogue and requires both documents to state them. Each of the three anchored claims was made to fail on its own before the test was kept.

**The mirror, checked and clean.** `.agents/skills/pandects/SKILL.md` was compared with
the canonical skill in case the version bump had left them disagreeing. It is a
deliberately different document, a short routing entrypoint with its own description
and no frontmatter version, and no other plugin's mirror carries a version either. The
frontier sentence is the part they share and the prose gate already holds it.

**The ledger, machine-checked rather than read.** `tests/test_evolution_contract.py`
holds every governed ledger to the versioning contract, and it passes on this entry:
the frontmatter version matches the ledger, the recorded SHA-256 matches the digest of
the current status line, and the axis rules allow an evolution entry to move the
frontier revision where a generation entry may not. The reading in round 1 was right
and this is the part of it that did not depend on my reading.

**What ran.** The repository's 21 tests, up from 20 by the count gate, 116 plugin
tests, 79 Solidity tests under forge 1.7.1, and the demo path: ten laws printed, ten
laws with every part present, no catalogue drift. No Solidity in this step, so the
Pashov pair and `fizz` had nothing to read and did not run.

Leads not pursued: the four accepted at the close of step 2, and the Medusa coverage
asymmetry from step 3 round 6.

## Withdrawal batch fee law, step 4, round 3 -- 2026-08-18

Reviewed: whether the frontier this step declares is visible where a reader would meet
it. The ledger names a gap in the search-record runner. Two documents describe that
runner and neither said the gap existed.

- S4-R3-01 | medium | `plugins/pandects/README.md` | "Saying how it was searched" opens with "A campaign result without its settings is an anecdote" and then hands the reader `pandects run`, without saying that the command emits the Foundry campaign and nothing else. A reader who has just run Echidna or Medusa, which this plugin ships adapters and a configuration for, would look for a record the tool cannot produce. The section names `foundry.toml` and so is not false; it is silent exactly where the corpus's own held frontier says the gap is. | Fixed in this round: the section says `run` knows one engine, that an engine which did not run is absent rather than empty, that a campaign under either fuzzer is not recorded by the command, and that widening it is the held frontier.
- S4-R3-02 | medium | `plugins/pandects/adapters/medusa/README.md` | The adapter document says "A Medusa record therefore carries the engine, the configuration, the sequence length and the corpus digest", which describes such records as things this plugin produces. Nothing produces them. It is the document somebody reads to learn how to run Medusa here, so it is the worst place for that to be implied. | Fixed in this round: the record is described as written by hand, with `pandects run` named as emitting Foundry and no other engine, and the widening named as the frontier.

**Why these count as reconciliation rather than new work.** The held job asks for a
cold read of mutable first-party marketplace prose, and the step had read it for law
counts and the frontier sentence. It had not read it against the frontier it was
about to declare. A ledger that names a gap while the two documents describing that
tool imply it is filled is a record disagreeing with itself, which is the same defect
class as a count written twice.

**What ran.** The repository's 21 tests, 116 plugin tests, 79 Solidity tests under
forge 1.7.1, and the demo path: ten laws printed, ten laws with every part present, no
catalogue drift. No Solidity in the diff, so the Pashov pair and `fizz` had nothing to
read and did not run.

Leads not pursued: the four accepted at the close of step 2, and the Medusa coverage
asymmetry from step 3 round 6.

## Withdrawal batch fee law, step 4, round 4 -- 2026-08-18

Reviewed: the fixed tree, the gates the earlier rounds added, and one last read for
anything still describing the closed frontier as open.

The fixed tree has no open finding. Status: clean.

**Nothing still calls the gap open.** No document or contract outside the audit logs
and this run's own spec describes a fee reducing pooled claims below what open batches
are owed as uncovered. `src/laws/ReservesCoverPayableClaims.sol` still says no law
covers a claim paid beyond what it was owed, which remains true and is a different
defect. `docs/applicability.md` names two laws as examples of qualified applicability,
and both readings still hold.

**The frontier agrees everywhere.** The new sentence appears once per surface across
all twelve documents that carry a marketplace-context block, and matches the row in the
repository README's selection table. The other nine plugins' frontiers are untouched.

**The gates, re-proved.** Setting the repository README's exact count back to eight
fails the count gate. Desyncing the ledger label from the frontmatter fails two
evolution-contract checks at once, which is the right answer: the label and the digest
are separate claims.

**What ran.** The repository's 21 tests, 116 plugin tests, 79 Solidity tests across ten
suites under forge 1.7.1 and solc 0.8.28, and the demo path from the study's problem
statement: `pandects laws` printing ten with their applicability, `pandects check` over
ten laws with every part present, and `pandects render` producing no drift. No Solidity
in this step at any round, so `x-ray`, `solidity-auditor` and `fizz` had nothing to read
and none of them ran; the reading passes are these four rounds.

Leads not pursued: the four accepted at the close of step 2, unchanged and none of them
touched by this step, and the Medusa coverage asymmetry stated in step 3 round 6.

## Repository-wide Brevitas pass, step 1, round 1 -- 2026-08-18

- Low: A historical finding changed during the structural audit-log rewrite.
- Location: `audit/AUDIT.md:20` at entry ref `a7d001009e7e2a7e63343e206ef10ecabc2cab42`.
- Mechanism: `could raise uncontrolled type errors` became `permitted uncontrolled type errors`.
- Impact: the rewrite altered the recorded failure mechanism without new audit evidence.
- Fix: used `exposed` for the first mechanism and retained the separate qualified error-response claim.

The manual round also checked both parser implementations, their compact-list fixtures,
the 159-file source inventory, 43 excluded files, 29 protected passages, four digest
refusals, and the committed study and runbook. No other open finding was established.
The Solidity security suite remains waived because the step changes Markdown and Python
test parsers only.

## Repository-wide Brevitas pass, step 1, round 2 -- 2026-08-18

The fixed non-Solidity tree has no open finding. Status: clean.

The round re-read the historical mechanism at `audit/AUDIT.md:20`, both compact-list
parsers, their fixtures, and the full protected-state proof. Root `22/22`, Hexaemeron
`62/62`, Imprimatur, Brevitas `--source`, protected SHA verification, and
`git diff --check` pass. No further lead was established.

## Repository-wide Brevitas pass, step 2, round 1 -- 2026-08-18

The Brevitas prose diff has no open finding. Status: clean.

The review compared five changed files with entry ref `a7d001009e7e2a7e63343e206ef10ecabc2cab42`, checked the compact history parser, and recomputed frontier digest `dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62`. It also verified the three refusal digests: `08e534ff9fd8005778e2224f374bd1e42a4bb129c2504e8aa54549f8621f0494`, `2cdd9bb04532ec278184d2a3290a0b0b72c02be47ca634911428440ddbed6d58`, and `ed8fbcf14186a1c79f9db8f971796d192969ec729edeb2bba0fc78f30ff75e48`.

Root `22/22`, Brevitas `13/13`, evals `3/3`, Agent Skills validation, Imprimatur, Brevitas `--source`, protected SHA verification, and `git diff --check` pass. The security suite remains waived because only Markdown changed.

## Step 1, round 1 -- 2026-08-18

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R1-01; severity: low; file: step commit; finding: Fiat-created commit carried one provenance trailer where push-discipline requires both; status: fixed by amend on the step branch

Leads not pursued: none. The round ran the waiver's lint battery -- phylax,
ephoros and hypomnema over the changed tree, all clean -- and reviewed the diff
against the study's risk register: no dangling pointer survives (the record
lint caught one at implement time, fixed before commit), the fiat prose pins
in `test_fiat_skill.py` still hold, both ledgers keep their axes, `hexctl.py`
is untouched, and the marketplace prose tests pass. Root 24/24, hexaemeron
124/124.

## Step 1, round 2 -- 2026-08-18

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The amended commit carries both provenance trailers, the lint
battery is clean over the fixed tree, and both suites pass.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-18

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The three lints exit clean over the changed tree; the diff
touches two references and one phase note, none of which a test pins; the new
lint commands resolve through `$PLUGIN_ROOT` exactly as the masks already do
in the same file; and both suites pass. Root 24/24, hexaemeron 124/124.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-18

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The lint battery is clean over the changed tree; the diff touches
two READMEs' prose, one manifest description and three version fields; the
short description four surfaces must agree on is untouched, and the marketplace
prose tests hold. Root 24/24, hexaemeron 124/124.

Leads not pursued: the root README's one-line Hexaemeron entry says nothing
about the phase skills. It also says nothing false, and the status table's
"Use it for" cell already names them, so no change.

## Step 4, round 1 -- 2026-08-18

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The lint battery is clean, the ledger axes hold under both
suites, the evolution row's digest matches the recomputed header, and the
cold read's one defect, a hand-off line predating the phase skills, was fixed
in the step commit. Root 24/24, hexaemeron 124/124.

Leads not pursued: none.

## Step 1, round 1 -- 2026-08-18

Run: Horos, the reading-boundary skill. Step 1 scaffolds and registers the
plugin. Suite waived (no Solidity); the round ran the three bundled lints and
a diff review against the study's risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/horos/README.md | "What it ships" claimed the scanner, boundary and maps in the present tense while this step ships only the scaffold | fixed: section reframed as what the runbook lands, in order |
| S1-R1-02 | low | plugins/horos/docs/runbook.md | the committed runbook copy pointed at the gitignored .hexaemeron path as the spec | fixed: points at the committed study beside it |
| S1-R1-03 | low | README.md | the role matrix omits a Horos column, and a Developers score at or above five demands a worked example the landing README lacked | fixed: column added (Developers 8, Security 2, all other desks 1) and a Day-to-day example added |

Lints: phylax 0, ephoros 0, hypomnema 0 over plugins tests and the changed
documents. Leads not pursued: none.

## Step 1, round 2 -- 2026-08-18

The round re-ran against the tree with round 1's fixes applied. Lints: phylax
0, ephoros 0, hypomnema 0. Root 24/24, horos 4/4. The review of the fix diff
found nothing further.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); the round ran the three bundled lints, all clean,
then reviewed the classifier against the study's risk register.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: medium; file: plugins/horos/skills/horos/scripts/horos.py; finding: classify_file swallowed OSError and returned None, so an unreadable file was reported as readable instead of counted in files_skipped_unreadable, understating what the scan skipped; status: fixed: the function raises and the walker counts, with a chmod-0 regression test
- id: S2-R1-02; severity: low; file: plugins/horos/skills/horos/scripts/horos.py; finding: classify_file is public but did not itself refuse symlinks; only the walker guarded them, so a direct caller could make the scanner read outside root; status: fixed: the function refuses links as well

Leads not pursued: a stat-then-open race (a file swapped for a symlink between
the check and the read) is accepted for the prototype; exploiting it requires
an attacker writing to the tree during the scan, at which point the tree is
already theirs.

## Step 2, round 2 -- 2026-08-18

Re-ran against the fixed tree. Lints: phylax 0, ephoros 0, hypomnema 0.
Horos 26/26, root 24/24. The fix diff review found nothing further: the one
public caller of classify_file already counts the raised OSError as skipped.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none beyond the accepted race recorded in
round 1.

## Step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Review focused on the
risk register's partial-write and determinism rows.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: low; file: plugins/horos/skills/horos/scripts/horos.py; finding: the temporary boundary file used one fixed name, so two concurrent scans of the same tree could unlink each other's half-written temporary and fail one run's atomic replace; status: fixed: the temporary name carries the writing process id; the existing cleanup tests pin that no temporary survives either path

Leads not pursued: a giant hand-crafted boundary.json can make check spend
memory parsing it; accepted for the prototype, the file is repository-local
and the parse failure path already exits 2.

## Step 3, round 2 -- 2026-08-18

Re-ran against the fixed tree. Lints: phylax 0, ephoros 0, hypomnema 0.
Horos 39/39, root 24/24. The fix diff is one line plus its comment; the
review found nothing further.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none beyond round 1's accepted parse-memory
lead.

## Step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
45/45, root 24/24. The review checked the map verb against the never rules:
it parses and never imports or executes the target, hostile nesting is capped
by the tokenizer's indentation limit and lands in the caught SyntaxError
path, and undecodable bytes are replaced before parsing.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: map reads the named file whole, unlike the
bounded scanner; that is the verb's purpose (one tool read instead of the
agent reading the file), and the file is user-named rather than
tree-discovered.

## Step 5, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
51/51, root 24/24, and the study's four repeatable success criteria pass as
written from the repository root. The review checked the shipped example
against the risk register: the fixture's committed boundary is reproduced
byte for byte by a fresh scan on every supported interpreter path (the
document is sorted-key JSON of ints and posix strings), the documented
mutation fails by name in both drift directions, relative links in the final
SKILL.md resolve, and the example's vendored and lockfile specimens are
inert data that no suite imports or executes.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Live-evidence run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two committed spec documents. Root 24/24, horos 51/51. The step adds prose
only; the review checked the committed copies match the receipted artefacts.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Live-evidence run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
bundle. Horos 55/55, root 24/24. The review checked the risk register's
rows: the bundle names its commit and tool version, the consistency test
reads only the committed boundary and never re-scans or touches the network,
and the quoted totals are asserted rather than trusted. The one derived
number (80.3%) is recomputed by the test from the quoted operands.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Live-evidence run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
six changed surfaces. Root 24/24 (the evolution contract validates the
v1.1.0 row's script-computed digest and the prose contract validates surface
agreement and job uniqueness), horos 55/55. The review confirmed the refusal
is recorded in both the skill text and the ledger with its reason, and that
the in-place study corrections are named in the commit rather than silent.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Rule-classes run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two spec documents. Root 24/24, horos 55/55. Prose-only step; the committed
copies match the receipted artefacts.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Rule-classes run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0 over plugins tests,
hypomnema 0 over the changed README. Horos 61/61, root 24/24. The review
checked the register's false-exclusion row: both rules are gated on name
plus content or name plus path, each carries two near-miss tests, and the
example's readable file stays readable. The SVG rule runs before the marker
scan by decision, recorded as a comment at the check itself.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: .svgz and other compressed asset variants
stay readable; they are binary when deflated on disk and out of the held
job's evidence either way.

## Rule-classes run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
new bundle. Horos 65/65, root 24/24. The review held the register's rows:
the first capture's files are untouched (git shows additions only), the
delta test proves the added entries are exactly the two families with
nothing removed, both bundles name the same commit, and the consistency
tests read only committed files.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Rule-classes run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0 over plugins tests,
imprimatur 100 on all four reconciled surfaces. Root 24/24 (the evolution
contract validates the v2.1.0 digest; the prose contract validates surface
agreement and job uniqueness), horos 65/65. The review confirmed the
supersession keeps the refusal's grounds in the record rather than erasing
them, and that both prior ledger rows are byte-identical to before.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Outline-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
67/67, root 24/24. The review checked the move: the Python extractor's
output is pinned by the untouched fixture test, the registry refuses
unregistered suffixes naming its supported list, and the refusal-message
test moved with the message as the runbook records.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Outline-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 79/79, root
24/24. The review walked the risk register's lexer rows: escapes consume
line continuations, character classes protect a slash inside a regex, the
newline guard bounds a wrong regex guess to one line, operator folding
keeps arrow and equality tokens whole, and every unterminated construct
confesses the remainder.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: inside a template expression the scanner
treats a slash literally, so a regex literal containing a brace or backtick
inside `${...}` can mis-span the template. Bounded to that template, and
deferred to the step 4 corpus run, which will show whether real code does
this before any fix is designed.

## Outline-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 89/89, root
24/24. Two defects were found and fixed during the step's own build, before
the implement receipt, and are recorded here for the trail: a statement
position that never advanced on a stray closing brace hung the first live
run (fixed with an explicit step-over plus a monotonic advance guard), and
method heads truncated at their parameter list because the statement-end
scanner was handed the closing parenthesis itself (fixed with
position-ordered member dispatch). The round's review after those fixes
walked the emitted fixture line by line against the source and found the
slices verbatim and the confession exact.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings in the round itself. Leads not pursued: multiline arrow-
function signatures quote only their first line; the differential in step 4
measures whether that loses names in practice.

## Outline-extractor run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
92/92, root 24/24. The review held the register's rows: the oracle tool is
committed but nothing in the runtime or test path imports or invokes it
(the consistency tests read only the committed results JSON); the bundle
names its commit, oracle version and altitudes; the acceptance numbers
(missed 0, extra 0, crashes 0) are asserted by test rather than quoted; and
the three corpus-found fixes each landed with the corpus rerun after them.
The step 2 lead (a regex with braces inside a template expression) did not
occur in 866 real files: no file crashed or misparsed on it, so it stays a
recorded limitation.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: the corpus is one repository's style
(prettier, semicolon-free); a semicolon-heavy or decorator-heavy corpus
would exercise different paths and can join the evidence when one matters.

## Outline-extractor run, step 5, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24 (the evolution contract validates
the v3.2.0 digest; the prose contract validates surface agreement and job
uniqueness), horos 92/92. The review confirmed the refusal's revision is
recorded as a revision, both prior ledger rows are byte-identical, and the
new held job is the maintainer's own words for the filetype census.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Census run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two spec documents. Root 24/24, horos 92/92. Prose-only step; the committed
copies match the receipted artefacts.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Census run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
changed README. Horos 101/101, root 24/24. The review held the register's
rows: one walk produces both artefacts (the tally rides the existing loops
rather than a parallel implementation), the frozen boundary is reproduced
byte for byte by test, rows sum to the totals with the boundary column
bounded by its row, symlinks and skipped directories appear in neither
walk, and the census writer is the boundary's own atomic writer refactored,
not a copy.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: readable files are statted twice when the
census is on (once inside classify_file, once for the tally); measured
against Metron's rule it is noise on real trees and not worth plumbing size
out of the classifier.

## Census run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
104/104, root 24/24. One defect was caught by the bundle's own consistency
test before the implement receipt and is recorded for the trail: the prose
quoted the boundary walk's file count instead of the census's (which
includes files inside aggregated directories), 1,041 against the true
1,113. The review confirmed both documents carry the shipped schema, the
rows sum to the totals, and the Solidity call is recorded as a candidate
pending more censuses, in the maintainer's words.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings in the round itself. Leads not pursued: none.

## Census run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24 (evolution digest and prose
contracts), horos 104/104, demo census byte-identical. The review confirmed
the held job carries the maintainer's own restraint: breadth first, no
extractor from one tree, Solidity recorded as leading candidate rather than
commitment, and the three prior ledger rows byte-identical.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Go-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
104/104, root 24/24. Prose-only step; one imprimatur defect (a bold-lead
bullet) was fixed before the copies were committed, and the committed
copies match the receipted artefacts.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Go-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 116/116, root
24/24. The review walked the study's risk rows: raw strings keep
backslashes as plain bytes and span lines, runes holding quotes are pinned,
iota members emit without types, receivers ride inside function slices, and
the statement walker advances monotonically (the guard the TypeScript
extractor learned the hard way is present from the start).

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: an anonymous struct in a result type
(func f() struct{ x int } {) would mis-slice at the struct's brace; the
step 3 corpus over 1,421 real files will show whether the pattern occurs
before any fix is designed.

## Go-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
118/118, root 24/24. The review held the register's rows: the venv and
oracle stay outside every runtime and test path (the consistency tests read
only the committed results JSON), the bundle names its commit, oracle and
the compiler-absence trade, the acceptance numbers are asserted by test,
and the step 2 lead (an anonymous struct in a result type) did not occur in
1,421 real files. The three dev-side tooling defects the run surfaced are
named in the bundle; the shipped outliner needed no fix at all.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: the corpus is gofmt-regular by
construction; hand-mangled Go would exercise the confession paths harder,
and can join the evidence when such a tree matters.

## Go-extractor run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24, horos 118/118, demo pinned. The
review confirmed the evolution row's numbers equal the committed bundle's,
the C++ job carries the maturity expectation in the maintainer's words, and
all prior rows are byte-identical.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Cpp-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
118/118, root 24/24. Prose-only step; one imprimatur defect (a structural
metaphor) was fixed before the copies were committed.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Cpp-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 132/132, root
24/24. Three defects were found and fixed during the step's own build,
before the implement receipt, recorded for the trail: a broken template
reattachment vestige replaced with the decorator pattern; a function body's
close consuming the following statement (refresh, fromQuery and formatApr
vanished from the fixture until the tail scan was cut back to the brace);
and Allman-style bodies orphaned from their heads until a one-line peek
joined them, with the orphan-brace branch defused from eating statements.
The round's review walked the fixture against the source and found the
slices verbatim, the raw-string containment exact and the confession
correct.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings in the round itself. Leads not pursued: preprocessor
conditionals that unbalance braces mis-slice until the next recogniser, as
the study prices; the step 3 corpus reports how often real code does it.

## Cpp-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity shipped; the corpus is the Solidity compiler's
C++); lints phylax 0, ephoros 0, hypomnema 0. Horos 136/136, root 24/24.
The review held the register's rows: the venv and oracle stay outside every
runtime and test path, the bundle declares its altitudes and exclusions
including the 170 oracle-unparsed files, the acceptance numbers are
asserted by test, and the five corpus-found outliner defects each landed
with the corpus rerun after them. The step 2 lead (preprocessor
conditionals unbalancing braces) produced zero confessed regions across 842
files of heavily conditionalised code.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: the oracle-unparsed fifth of the corpus
is compared for crash-freedom only; a stronger C++ oracle would widen the
compared set and can join the evidence if one becomes available without a
toolchain the ingested tree does not owe us.

## Cpp-extractor run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24 (the evolution contract validates
the mature row's digest; the prose contract validates surface agreement),
horos 136/136, demo pinned. The review confirmed the maturity closure meets
the study's stated condition (the differential closed clean at declared
altitudes), the reopening path is named on every surface, and all prior
ledger rows are byte-identical.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity shipped); lints phylax 0, ephoros 0, hypomnema 0.
Horos 136/136, root 24/24. Prose-only step; the committed copies match the
receipted artefacts.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (the run ships Python that reads Solidity, none of its own);
lints phylax 0, ephoros 0. Horos 149/149, root 24/24. The review walked the
study's risk rows: hex and unicode strings lex through the ordinary quote
scanner with prefixes staying in code harmlessly, attribute chains and
override lists ride in verbatim heads, the walker inherits the monotonic
advance and Allman peeks its three predecessors learned, and constructors
are outlined but excluded from the differential's compared set like C++
destructors.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 3, round 1 -- 2026-08-18

Suite waived (Python reading Solidity, none shipped); lints phylax 0,
ephoros 0, hypomnema 0. Horos 152/152, root 24/24. The review held the
register's rows: the venv and oracle stay outside every runtime and test
path, the bundle declares its altitudes and exclusions, the acceptance
numbers are asserted by test, and the one corpus defect (the multiline
inheritance swallow, exactly the silent-consumption class this loop exists
to catch) landed with a pinned regression and a structural fix rather than
a heuristic patch.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 4, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, imprimatur 100 on all four
reconciled surfaces. Root 24/24, horos 152/152, demo pinned. The review
confirmed the evolution row's numbers equal the committed bundle's, the
held job quotes the maintainer's specification by its committed path, and
all prior rows are byte-identical.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Refinement run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
152/152, root 24/24. Prose-only step; the committed copies match the
receipted artefacts and sit beside the maintainer's verbatim specification.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Refinement run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Root 24/24. One
finding, and it is a process finding against this run's own record: the
implement receipt recorded "horos 157/157" while the plugin suite was in
fact red with two test errors, because a chained shell command swallowed
the suite's exit status. The errors were wrong expectations in the two new
nested-attributes tests (asserting file-level entries where directory
aggregation correctly forecloses them), fixed in 1d33f7f with the semantics
documented in the tests themselves. The true counts: 155 tests before the
fix with 2 errors; 155/155 after. The receipt's count also overstated the
total by two. The correction stands here rather than in a rewritten
receipt, because the ledger is append-only and the round exists to catch
exactly this.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: high; file: .hexaemeron ledger; finding: implement receipt asserted a green suite over a red one; status: corrected in 1d33f7f and recorded here

Leads not pursued: none.

## Refinement run, step 2, round 2 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 155/155, root
24/24, against the fixed tree. The round re-walked the two corrected tests
against the scanner's actual semantics and the scope table's registration
order, and re-verified the frozen fixture boundary is byte-identical.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Refinement run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
changed README. Horos 159/159, root 24/24, both verified before the
implement receipt this time. The review walked the specification against
the landed pipeline clause by clause: the hard list is exactly the
specification's five plus corroborated directories, geometry stays
candidate wherever found including the windows, the sample is
deterministic (first eight sorted, 4 KiB each), the byte budget holds (at
most 8 KiB for large unresolved files), candidates never bind and check
never fails on them, and the safety rule the specification preserves
(security reviews ignore the boundary) is untouched in the skill text.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: the specification's closing note names
nested .gitattributes and corroborated exclusions as the largest gains;
both landed, and the recapture evidence for real trees belongs to the
third job.

## Refinement run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0 (the git subprocess carries its
allow comment naming fixed argv, no shell, pinned cwd), ephoros 0. Horos
165/165, root 24/24, verified before the receipt. The review held the
register's rows: ignored files never enter any universe, the widened mode
still excludes them, aggregation counts only universe members, check
reproduces the committed universe, and the fixture's tracked label is safe
because running the suite presupposes a git clone.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Refinement run, step 5, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, imprimatur 100 on all four
reconciled surfaces. Root 24/24, horos 165/165, demo byte-identical, all
verified before the receipt. The review confirmed the discipline's new
grade and universe language matches the shipped behaviour exactly, and all
prior ledger rows are byte-identical.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Marking run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
165/165, root 24/24, verified before the receipt. Prose-only step.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Marking run, step 2, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, hypomnema 0 over the changed
AGENTS.md. Root 24/24 with the stanza in place, horos 165/165, check from
the root clean, all verified before the receipt. The review read the
committed boundary's 14 hard entries and spot-checked them against the
tree: the fixture's own specimens, the shipped example artefacts and the
evidence JSONs classify exactly as the rules say, and no hand-written
plugin source appears in the hard set. The 35 candidates are advisory and
say so.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Marking run, step 3, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, hypomnema 0. Horos 168/168, root
24/24, verified before the receipt. The review held the register's rows:
one branch and one pull request per product repository and nothing merged
past their gates; the gitattributes promotions ride inside the reviewable
diffs exactly as the specification intends candidates to be promoted; the
bundle's numbers are asserted against the committed boundary copies; and
the stanza text in both product AGENTS.md files is the scanner's verbatim.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Marking run, step 4, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, imprimatur 100 on all reconciled
surfaces. Root 24/24 (the evolution contract validates the mature row's
digest), horos 168/168, check from the root clean, all verified before the
receipt. Two self-catches in this step, both resolved before any receipt:
check flagged the marking evidence copies as new sinks (they quote
generation markers), so the boundary refreshed in the close commit; and
the suite then flagged the bundle's stale skills count, reconciled in the
follow-up commit. The review confirmed the mature closure names the open
product pull requests rather than pretending merges, and all prior ledger
rows are byte-identical.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Phylax TypeScript boundaries, step 1, round 1 -- 2026-08-19

Severity Medium. TypeScript input had no work bound.
Location: `plugins/hexaemeron/skills/phylax/scripts/phylax.py:610`
Mechanism: The checker read each untrusted `.ts` or `.tsx` file in full before the linear lexer ran.
Impact: An oversized tracked file could consume unbounded memory and analysis time.
Fix: Read at most 1 MiB plus one byte, fail closed with `P000`, and guard the limit with a regression test.

## Phylax TypeScript boundaries, step 1, round 2 -- 2026-08-19

Suite waived (no Solidity); Phylax, Ephoros and Hypomnema lints clean.
Hexaemeron 167/167, root 24/24, pinned application clean and unchanged.
Manual review of `bff0eb6460e8f682e230ee6d982456121a33e2cc` found no further issue.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.
## Elenchus structured reports, step 1, round 1 -- 2026-08-19

Severity Medium. A descendant process could supply the accepted report.
Location: `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:310`
Mechanism: The report path was exported through `ELENCHUS_REPORT_FILE`, so every descendant inherited the same write target.
Impact: A broken parent run was classified as guarded from a nested fixture's unrelated assertion report.
Fix: Substitute one exact `{report}` command argument and remove the inherited report variable before launch.

Severity Medium. The report-size check had a stat/read race.
Location: `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:214`
Mechanism: A background writer could grow the file after its accepted size was read but before unbounded `read_bytes()` completed.
Impact: A report could exceed the 1 MiB memory and parser-work limit.
Fix: Read at most 1 MiB plus one byte and reject the extra byte before parsing.

## Elenchus structured reports, step 1, round 2 -- 2026-08-19

Suite waived (no Solidity); Phylax, Ephoros and Hypomnema lints clean.
Hexaemeron 179/179 and root 24/24. Real unittest, Forge and Node fixtures ran without skips.
Manual review of `5311fbaff498e1d20e256eb5d312b024d9354a2c` found no further issue.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.
## Ariadne dataset predicate, step 1, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. The step ships three documents and one test change, and no Solidity,
so the suite waiver covers the Pashov pair. The three bundled lints ran against
the changed tree and each exited 0: `phylax`, `ephoros`, `hypomnema`.

The step relaxes a test, so the review checked that the relaxation stays narrow.
Two adversarial probes were run and both behaved:

- A non-policy relative link leaving the plugin, appended to the ledger, still
  fails `test_no_shipped_document_links_outside_the_plugin`.
- A policy citation pointing at a file that does not exist still fails
  `test_ledgers_cite_the_versioning_contract` at the repository root.

Both suites pass on the committed tree: 24 repository tests and 310 ariadne
tests, 2 skipped.

Leads not pursued: the same out-of-plugin policy citation exists in the other
ten non-Hexaemeron ledgers and is unasserted there, because only Ariadne ships
a link test. Raising it across the marketplace is outside this step and outside
this run's held frontier.

## Ariadne dataset predicate, step 2, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. The step ships Python, a JSON schema and prose, and no Solidity, so
the suite waiver covers the Pashov pair. The three bundled lints ran against the
changed tree and each exited 0: `phylax`, `ephoros`, `hypomnema`.

The risk register named two concerns the lints cannot see. Both were probed.

**Gate isolation.** The conformance suite requires a breaching fixture to fail
its named gate and no other. Nine representative faults were run through
`verify.report` on the real envelope path. Each tripped exactly one check: two
gate 2 cases, two gate 5 cases, two coverage cases, one inputs case, one
predicate-fields case, and a clean statement failing nothing. A clean dataset
statement reports `unchecked: []`, which is the state the held frontier was
opened to reach.

**Malformed input from elsewhere.** A statement arrives from a stranger, so every
check must return rather than raise. 361 malformed shapes were run through
`dataset.check`: the whole predicate replaced by each of nineteen junk values,
then every top-level field, every coverage sub-field, and the first entry of
`inputs`, `dataset_subjects` and `coverage.gaps` replaced the same way. Nothing
raised.

Both suites pass on the committed tree: 24 repository tests and 373 ariadne
tests, 2 skipped, 62 of them new in this step.

Leads not pursued: the two probes above are one-off scripts rather than committed
tests. Step 3 owns the fixture and gate-completeness contract, so the guards land
there rather than here.

## Ariadne dataset predicate, step 3, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. The step ships fixtures, tests and prose, and no Solidity, so the
suite waiver covers the Pashov pair. The three bundled lints ran against the
changed tree and each exited 0: `phylax`, `ephoros`, `hypomnema`.

The step adds four completeness tests, so the review asked whether they catch what
they claim. Three adversarial probes were run and all three failed as they should:

- A new unnumbered check added to a predicate with no fixture fails
  `test_every_named_check_has_a_breaching_fixture`.
- A fixture edited to breach coverage and the field-shape check at once fails
  `test_every_check_breaching_fixture_fails_the_check_it_is_named_for`.
- A fixture whose name misspells its check fails
  `test_every_fixture_follows_the_naming_convention`, because the name is
  recovered by matching against the checks the registered predicates return
  rather than by parsing the filename.

The tree was restored after each probe and `git status` came back empty.

Both new passing fixtures were also verified through the command line rather than
only the harness. `pass-dataset-release.json` prints seven numbered gates and
three checks, all passing, with no unchecked line, and exits 0.
`fail-check-coverage-dataset-no-gaps-block.json` fails the coverage check alone
and exits 1.

Both suites pass on the committed tree: 24 repository tests and 381 ariadne
tests, 2 skipped.

Leads not pursued: `test_predicate_robustness.py` sweeps eighteen shapes at the
top level and one declared field at a time. It does not sweep nested fields two
levels down, so a gate indexing into a gap entry's contents without a type check
would not be caught by it. The gap-entry case is covered by the hand-written
tests in `test_dataset.py`; a general recursive sweep is a larger piece of work
than this step.

## Ariadne dataset predicate, step 4, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R1-01; severity: high; file: `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py`; finding: A symlink to a directory inside the release was skipped in silence. `os.walk` does not descend one, so every file under it was left out of both `dataset_subjects` and the release bundle digest, and nothing in the statement recorded that anything had been left out. A release could ship a statement describing part of its contents with no indication. This is the silent absence the gates exist to refuse, applied against the tool itself.; status: fixed in this round
- id: S4-R1-02; severity: medium; file: `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py`; finding: `SKIPPED_NAMES` dropped `.git` and `__pycache__` from the walk without recording it, so the bundle digest covered part of the tree while the statement said nothing about the rest. Same class as S4-R1-01, smaller blast radius.; status: fixed in this round

Both are now refusals that name what to change rather than omissions. The
directory case says why it refuses: the contents "would be left out of the
statement and out of the release digest without anything saying so".

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. No Solidity ships in this step, so the suite waiver covers
the Pashov pair.

The rest of the filesystem surface was probed and behaved:

- A symlink to a *file* inside the release was already refused.
- The release directory itself may be a symlink; `confined` resolves it.
- A `..` segment in `--release` resolves before use.
- A release holding no files is refused rather than producing an empty statement.
- `--out` writes through a temporary file in the same directory and replaces the
  target. A forced failure of `os.replace` leaves neither the target nor a stray
  temporary file.
- Record counts are read in fixed blocks. A 20000-record file spanning several
  blocks counts correctly, and a final line with no trailing newline still counts.

Three guard tests were added for the fixed cases, plus one asserting that a nested
directory of records is captured rather than skipped, since the fix touches the
walk.

Both suites pass on the fixed tree: 24 repository tests and 422 ariadne tests, 2
skipped.

Leads not pursued: `MAX_RELEASE_FILES` is 4096 and there is no cap on the total
bytes a release may hold. A caller pointing `--release` at a very large tree waits
a long time rather than being refused. Adding a byte budget is a flag and a
decision about its default, which is more than this step asks for.

## Ariadne dataset predicate, step 4, round 2 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R2-01; severity: high; file: `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py`; finding: `os.walk` swallows a directory it cannot read, because `onerror` defaults to `None`. An unreadable subdirectory's files were dropped from `dataset_subjects` and from the release bundle digest with nothing recording it. Same class as S4-R1-01, which round 1 fixed for symlinked directories only and did not generalise.; status: fixed in this round

`onerror` now raises a `CaptureError`: a release that cannot be read whole cannot
be captured.

The finding was reached by asking whether round 1's fix generalised. It did not:
round 1 closed the one silent path it had found and left a second open. The probe
that found it replaces `os.scandir` for one directory rather than using
permissions, because this container runs as root and a `chmod 0` probe passes
without exercising anything. That is recorded here because the first attempt at
this probe was inconclusive for exactly that reason.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`.

Both suites pass: 24 repository tests and 423 ariadne tests, 2 skipped.

Leads not pursued: the byte-budget lead from round 1 stands. `MAX_RELEASE_FILES`
caps the file count at 4096 and nothing caps total bytes.

## Ariadne dataset predicate, step 4, round 3 -- 2026-08-19

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R3-01 | high | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | The producer block was fabricated when the caller supplied nothing: `tool` defaulted to `ariadne`, `tool_version` to the string `unstated`, and `command` to `["ariadne", "capture-dataset"]`. Gate 2 passed on that, so a statement asserted a recoverable environment while recording nothing recoverable, and named Ariadne as what produced a dataset it had only read. `unstated` is a value that satisfies a non-empty-string check while carrying no information, which is the move gate 3 refuses for claims. | fixed in this round |
| S4-R3-02 | medium | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | A `--record-count` naming a path the release does not hold was accepted in silence. A typo meant the count the caller believed they supplied was not the one in the statement, and for a line-delimited file the derived count would be used instead with no sign anything had been ignored. | fixed in this round |
| S4-R3-03 | low | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | The refusal added for S4-R3-02 ran before the path refusals, so a release holding a symlinked file reported the count problem rather than the path problem. Found by two tests that started failing for the wrong reason. Every path refusal now happens inside `files()`, before any count is considered. | fixed in this round |

All three producer fields are required at the library boundary and on the command
line. The three bundled lints ran against the fixed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`.

The study's demo path changed with the code rather than after it. Both committed
copies of the study now carry the producer flags, and the path was run end to end
against the fixed tree: seven numbered gates, no unchecked line, exit 0.

Both suites pass: 24 repository tests and 429 ariadne tests, 2 skipped.

Leads not pursued: the byte-budget lead stands from round 1. `parameters_digest`
over an empty parameter set is a real digest of an empty mapping rather than a
fabrication, so it is left as it is and documented.

## Ariadne dataset predicate, step 4, round 4 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R4-01; severity: high; file: `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py`; finding: The inputs check accepted `"disposition": "passed"` with no digest. That is a single word around the rule the check exists for: it asserted the input was read while recording nothing about what was read, and the tally then counted it as recorded absent, which contradicts the disposition it carries. A statement built this way verified clean and exited 0.; status: fixed in this round

`passed` is no longer available as an input disposition. An input that was read
carries a digest; the four remaining values describe an absence and each needs a
reason. The rule is enforced in three places: the gate, the published schema's
enum, and the command line where the caller can still fix the invocation. The
drift test asserts `passed` is absent from that enum with the reason written next
to the assertion.

This is the fourth consecutive round to find something, and all four are the same
family: a field that satisfies a shape check while carrying no evidence. Rounds 1
and 2 were absences dropped from the walk, round 3 was a fabricated producer, and
this is an absence dressed as a result.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. Both suites pass: 24 repository tests and 434 ariadne
tests, 2 skipped.

Leads not pursued: the byte-budget lead stands from round 1.

## Ariadne dataset predicate, step 4, round 5 -- 2026-08-19

Eight weakest-passing-value probes, one per field the predicate declares, rather
than the ad-hoc probing of earlier rounds. Three were defects and five were
legitimate values that must keep passing.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R5-01 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | A statement claiming `record_count: -5` verified clean. The published schema says `minimum: 0` and the gate did not check, so the validator and the schema disagreed about what they accept. | fixed in this round |
| S4-R5-02 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | Two `dataset_subjects` entries could name the same `path` with different digests. One file cannot carry two digests, and the release bundle digest is taken over that listing, so the digest covered a description of the release that contradicted itself. | fixed in this round |
| S4-R5-03 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | A released file's `path` could be absolute or carry a `..` segment. A consumer resolves `path` against a release directory, so either form describes a file the release does not hold and points a careless reader out of the tree. The capture path never produces one; a hand-written statement did. | fixed in this round |

The five that were left alone, with the reason: two files with identical content
are a real thing to publish and only a duplicate path is incoherent; a
single-point coverage interval is one block; a negative coverage interval is
nonsense for `block` but the dimension is free-form and could legitimately be
signed; a gap covering the whole interval is a release that honestly describes
nothing; and a `tool_version` of the literal string `unstated` is a caller stating
something false rather than the tool fabricating it, which no shape check can tell
from a real version string.

The schema now states the path and count constraints, and a new drift test holds
the two together rather than only comparing field tables.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. Both suites pass: 24 repository tests and 440 ariadne
tests, 2 skipped.

Leads not pursued: the drift tests compare field tables and now three constraints,
not every constraint in the schema. A general comparison would need the schema
walked and each keyword mapped to the gate that enforces it, which is a piece of
work in its own right. The byte-budget lead stands from round 1.

## Ariadne dataset predicate, step 4, round 6 -- 2026-08-19

Round 5's method applied to the surface it had not reached: the capture function's
own arguments, twelve probes, and the gate-5 branch those probes walked into.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R6-01 | high | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | Gate 5 never checked the current side on a first release. The `baseline is None` branch validated the reason and returned, so a statement could name a current side with no name, no digest, or a digest the statement does not cover, and verify clean. Every first release therefore had one end of its comparison unchecked. | fixed in this round |
| S4-R6-02 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | A release compared against itself passed gate 5 and reported no differences, which reads as a release that changed nothing rather than as a comparison that means nothing. | fixed in this round |
| S4-R6-03 | medium | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | `parameters` or `record_counts` passed as a list of pairs raised a bare `ValueError` out of `dict()`, and a non-numeric stated count raised `TypeError` from a `%d` format. A library caller got a stack trace instead of the refusal the module gives for every other bad argument. | fixed in this round |
| S4-R6-04 | medium | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | A blank or absent `--name` produced a statement whose current side had no name. With S4-R6-01 open it verified clean; with it fixed the capture would have emitted a statement its own verifier refuses. | fixed in this round |
| S4-R6-05 | medium | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | `inputs` or `gaps` passed as a string, or holding a non-object entry, produced a statement that verify then refused. A blank `--first-release-reason` did the same. The capture's contract is that what it writes, verify accepts unedited. | fixed in this round |
| S4-R6-06 | high | `plugins/ariadne/scripts/ariadne_lib/predicates/solidity_release.py` | The same hole as S4-R6-01 is present in the Solidity release predicate, and has been since before this run. Confirmed against the shipped fixture: replacing a first release's `deltas.current` with `{"name": "", "digest": <a digest the statement does not cover>}` verifies clean and exits 0. The shipped fixture omits `current` entirely on a first release, so nothing exercised the branch. | open, out of scope |

S4-R6-06 is left open deliberately. This run's study put
`predicates/solidity_release.py` under ask-first, and the fix belongs to the
Solidity predicate rather than to a run whose subject is a new type. The patch is
the same shape as the one applied here: move the `check_side(deltas.get("current"),
...)` call and its subject-coverage check above the `baseline is None` branch, so
the current side is validated on both paths, and add a
`fail-gate5-solidity-first-release-unnamed-current.json` fixture to exercise it.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. Both suites pass: 24 repository tests and 451 ariadne
tests, 2 skipped.

Leads not pursued: the byte-budget lead stands from round 1, and the
constraint-level drift lead from round 5.

## Ariadne dataset predicate, step 4, round 7 -- 2026-08-19

Every sweep from rounds 1 to 6 was re-run against the fixed tree first and all of
it came back clean: the three lints, 306 malformed shapes across both registered
predicates with nothing raised, all 27 conformance fixtures with each breaching one
holding to a single check, the demo path end to end, and both suites. Then seven
new weakest-value probes were run on fields the earlier sweeps had not reached, and
four of those were defects.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R7-01 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | A gap `reason` of whitespace passed. `missing()` reads `""` as absent but not `"   "`, so the one field whose whole job is to carry the reason accepted a string that carries none. Gate 3 already refuses this for a claim reason, so the predicate disagreed with itself. | fixed in this round |
| S4-R7-02 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | An unknown key inside `deltas.records` passed, while an unknown section one level up was refused. Both are undeclared content sitting inside a digested comparison. `records` now carries `added`, `removed` and `changed` and nothing else. | fixed in this round |
| S4-R7-03 | low | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | A producer `command` containing an empty word passed. An argv with an empty word is not what ran, and gate 2's promise is that somebody else can run it. | fixed in this round |
| S4-R7-04 | low | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | A `coverage.dimension` of whitespace passed, naming nothing while satisfying the string check. | fixed in this round |

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. Both suites pass: 24 repository tests and 456 ariadne
tests, 2 skipped.

Leads not pursued: the byte-budget lead from round 1, the constraint-level drift
lead from round 5, and S4-R6-06 in the Solidity release predicate, which stays open
and out of scope with its patch recorded.

## Ariadne dataset predicate, step 4, round 8 -- 2026-08-19

The last round the controller allows. Method changed again: instead of hand-picked
probes, every leaf in a fully populated valid predicate was replaced in turn by each
of nine values that satisfy a presence check while carrying nothing. 369 mutations,
and 101 of them still verified clean.

Triage separated three groups. Four were values that must keep passing and were
settled in round 5: a `record_count` of zero on either file, and a `coverage.start`
of zero or negative. Twenty-two sit in the core gates and eight in a helper shared
with the Solidity predicate, both recorded below as out of scope. The rest were
defects.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R8-01 | medium | `.../predicates/dataset.py` | A released file `path` of whitespace passed. `usable_path` tested truthiness, so `"   "` was a path. | fixed in this round |
| S4-R8-02 | medium | `.../predicates/dataset.py` | A gap `reason` that was not a string passed: `1.5`, `0` and `True` all satisfied the presence check. Round 7 fixed whitespace strings and did not generalise to the type. | fixed in this round |
| S4-R8-03 | medium | `.../predicates/dataset.py` | Entries in `deltas.records.added` and `.removed`, and both sides of a `changed` entry, accepted any value at all: `None`, `{}`, `1.5`. A comparison listed records it did not identify, inside a block gate 5 reports as a recorded difference. | fixed in this round |
| S4-R8-04 | low | `.../predicates/dataset.py` | `producer.tool` and `producer.tool_version` of whitespace passed. | fixed in this round |
| S4-R8-05 | low | `.../predicates/dataset.py` | An input `name` or `locator` that was whitespace or a number passed. The locator is what lets a reader find the input again. | fixed in this round |
| S4-R8-06 | low | `.../predicates/dataset.py` | A released file `name` of whitespace passed. | fixed in this round |
| S4-R8-07 | low | `.../predicates/dataset.py` | An argv word of whitespace passed. Round 7 required non-empty and stopped there. | fixed in this round |
| S4-R8-08 | low | `.../gates.py` | Core gates 3 and 6 accept a blank or non-string `name` on a claim or a command, and gate 6 accepts an argv word that is empty or whitespace. `core_predicate.label()` falls back to a positional name, so nothing breaks, but a recorded command cannot be re-run from an argv holding a blank word. | open, out of scope |
| S4-R8-09 | low | `.../core_predicate.py` | `check_side` accepts a delta side `name` that is whitespace or a number, because it tests truthiness. The helper is shared with the Solidity release predicate, so tightening it changes what that predicate accepts. | open, out of scope |

S4-R8-08 and S4-R8-09 are both left open on the same reasoning as S4-R6-06: this
run's study puts the core gates and the Solidity predicate's behaviour under
ask-first, and neither belongs to a run whose subject is a new predicate. The patch
for S4-R8-09 is to give `core_predicate` the same non-blank-string helper this
predicate now uses and call it from `check_side`; for S4-R8-08 it is the same helper
applied to the `name` and `argv` checks in `gates.py`, each with a fixture.

After the fixes the sweep was re-run: 34 mutations still verify clean, and every one
is accounted for. Twenty-two core gates, eight the shared helper, four deliberate,
and none unexplained.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. All 27 conformance fixtures behave. Both suites pass: 24
repository tests and 463 ariadne tests, 2 skipped.

Leads not pursued: S4-R6-06, S4-R8-08 and S4-R8-09 above, the byte-budget lead from
round 1, and the constraint-level drift lead from round 5.

## Ariadne dataset predicate, step 5, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S5-R1-01; severity: low; file: `plugins/ariadne/scripts/ariadne_lib/registry.py`; finding: The module docstring said "It is empty at this point in the build, and `ariadne predicates` says so." That was already false before this run, since the Solidity release predicate was registered, and the dataset predicate made it doubly so. A shipped file that describes its own state wrongly is the drift this plugin's own document tests exist to catch, and no test reached a docstring.; status: fixed in this round

The step reconciles prose, so the review looked for the failure a prose test cannot
see: a paraphrase that says the same stale thing in different words. The repository
was swept for claims about how many predicates are registered and which remain
unimplemented, across Markdown, Python and JSON. One shipped file was wrong, and it
is fixed above.

Two hits were left alone on purpose. The committed study says "its registry holds one
predicate", which is its problem statement describing the state the run started from
and is correct as a historical record. The Fiat run artefacts under `.hexaemeron/` are
not shipped.

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. No Solidity ships in this step, so the suite waiver covers the
Pashov pair.

The ledger was checked against the contract rather than only by the suite. The
recomputed frontier digest
`ec925d3f57001ac32eb6d40ffdd7d43f130e360283ef40eb8fbbda724f262c2f` is over
`open|state-fixture-predicate|<current frontier>|<next Fiat job>` with its trailing
newline, the new row sits on the evolution axis with the counter moving 0.1.0 to
1.1.0, and the frontier revision changes because the held target was met.

The demo path from the study was run end to end against the committed tree: seven
numbered gates, three checks, no unchecked line, exit 0.

Both suites pass: 24 repository tests and 463 ariadne tests, 2 skipped.

Leads not pursued: nothing tests a docstring against the state it describes, which is
how S5-R1-01 survived. A check for it would have to decide which sentences are claims
about the code, and that is a larger piece of work than this step.

## Ariadne dataset predicate, step 5, round 2 -- 2026-08-19

Round 1 found one docstring describing a state long gone. This round generalised the
search rather than assuming it was the only one, and found two more.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S5-R2-01; severity: low; file: `plugins/ariadne/tests/test_cli.py`; finding: The module docstring said "The two subcommands that exist at this point". There are six.; status: fixed in this round
- id: S5-R2-02; severity: low; file: `plugins/ariadne/scripts/ariadne.py`; finding: The `capture` subcommand's `kind` argument was helped by "the predicate to capture; one so far". A reader meeting it now takes it as a claim about the registry, which holds two.; status: fixed in this round

Both docstrings now describe what they do rather than how many of something there
are, and `test_cli.py` says why the count is left out. A sentence that counts
something goes stale the next time one is added, which is what produced all three of
these findings across two rounds.

The search covered every Python file under the plugin for phrases that date a
sentence: "one so far", "two so far", "at this point", "for now", "not yet",
"currently". A re-sweep after the fixes returns nothing.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. Both suites pass: 24 repository tests and 463 ariadne tests,
2 skipped.

Leads not pursued: the lead from round 1 stands. Nothing tests a docstring against the
state it describes, and a check for it would have to decide which sentences are
claims about the code.

## Ariadne dataset predicate, step 5, round 3 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. The step's own subject was checked against the contract rather than only
by the suite that guards it.

- Fourteen marketplace-context blocks across the plugin and the portable entrypoint
  carry one distinct frontier sentence between them, and the root selection table's
  cell is that same sentence.
- The ledger's frontier digest recomputes from
  `open|state-fixture-predicate|<current frontier>|<next Fiat job>` with its trailing
  newline. The new row sits on the evolution axis at `ariadne-v1.1.0`.
- The skill metadata, both plugin manifests and the marketplace entry all read 1.1.0.
- The landing README's next-job line carries the required prefix and suffix with a
  topic that ends in a full stop, which is what the repository contract reads.
- The demo path from the study runs end to end and exits 0.

The three bundled lints ran across every Python and Markdown file in the plugin and
each exited 0: `phylax`, `ephoros`, `hypomnema`. Both suites pass: 24 repository tests
and 463 ariadne tests, 2 skipped.

Leads not pursued: the docstring lead from rounds 1 and 2 stands, and the three
findings left open in step 4 stay open with their patches recorded.

## Ariadne dataset predicate, integrate -- 2026-08-19

Not an audit round. A record of what the integrate phase did and did not do, and
of one receipt that was wrong before it was made right.

**The stack is consolidated.** All five step branches are merged into
`fiat/ariadne-dataset-predicate-with-schema-gates-conf` in step order, with a merge
commit each. Both suites pass on the consolidated branch: 24 repository tests and 463
ariadne tests, 2 skipped.

**The merge into `main` is refused.** Both routes were tried. The pull request merge
API returns HTTP 403, "Merging into a protected base branch is not permitted for this
session type." A direct `git push` to `main` is rejected. This is an environment
restriction on the session rather than a state of the branch or of the change, and
nothing in the diff can clear it.

**A receipt was wrong and has been corrected.** The first `merge-step` for step 1 was
receipted with a shell variable that had captured the 403 response body instead of a
commit SHA, so the ledger briefly recorded a merge that had not happened. The merge
was then performed with `git` and pushed, which made the receipt true in substance,
and `merge_step_1_correction` records the error string, the real merge commit
`a57d1ce78cd6dfc6439963d7b91b4e0db7c3077b`, and why the API route was unavailable. The
four later merge-step receipts carry real SHAs and were taken after each merge.

**Two things this environment also refuses.** Changing a pull request's base branch
returns 403, so #198, #199, #200 and #201 stay open pointing at the step branches
below them even though every commit in them is in the run branch. Deleting a merged
step branch was refused as well, which is why they are all still present.

The integration pull request is #202, from the run branch into `main`, carrying the
run-level description. It is open and waiting for a merge this session cannot perform.

## Receipted lint rounds, step 1, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R1-01; severity: medium; file: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; finding: `solidity_round` raised out of the controller on a state whose `config` or `receipts` was not an object. `state.get("config", {})` returns `None` when the key exists holding null, so the default never applies and the next `.get` is an `AttributeError`. 356 of 676 state shapes produced a traceback rather than the named error every other fault in this file gets. `load_state` validates no shape at all, so a hand-edited or half-written state reaches this function.; status: fixed in this round
- id: S1-R1-02; severity: low; file: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; finding: `is_waiver` used `startswith`, so it read `waivedX` and `waived-ish` as waivers, which is not the rule written beside `WAIVER_PREFIX`. Both spellings reach the same classification by the other branch, so the mismatch produced no wrong answer; it would produce one the moment a message explained which branch it took. The first word is now compared rather than the prefix.; status: fixed in this round

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. No Solidity ships in this run, so the suite waiver covers the
Pashov pair.

The classifier is a pure function of two values, so it was swept rather than probed.
81 combinations of the three config modes against 27 receipt values were checked
against the rule its docstring states, and every answer matched. That sweep is what
showed S1-R1-02 to be invisible rather than absent: a mis-parsed waiver and an
unreadable receipt both land on non-Solidity, so the wrong reasoning gave the right
answer. 676 malformed state shapes were then run through it, which is what found
S1-R1-01.

Both suites pass on the fixed tree: 24 repository tests and 192 of 193 Hexaemeron
tests, 20 new in this step. The single error is
`test_elenchus_checker.ForgeReports`, which needs `forge`. The proxy refuses both
`foundry.paradigm.xyz` and GitHub releases, so it cannot be installed here, and it
errors identically on clean `origin/main`. Node was raised to v26.6.0 so the sibling
fixture passes; without that the baseline would be 191 of 193.

Leads not pursued: `load_state` still validates nothing, so every other reader of the
state file has the same exposure this round fixed in one function. Validating the
whole state shape on load is a larger change than this step, and it would belong to a
run about the controller's own robustness rather than to this one.

## Receipted lint rounds, step 1, round 2 -- 2026-08-19

Round 1 found a chained read defeated by a stored null and fixed it in one function.
This round asked whether that fix generalised. It did not.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R2-01; severity: medium; file: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; finding: The same shape sat at four more sites: three reads of `state["integrate"]["merged"]` at lines 854, 1072 and 1151, and one of `step["receipts"]["push"]["pr_url"]` at line 863. Each raises `AttributeError` out of the controller when the key exists holding null. Both spellings were confirmed to raise before being touched. `as_dict()` is now the single guard at all six sites, and behaviour on well-formed state is unchanged.; status: fixed in this round

The guard for this one asserts the pattern against the source rather than against
behaviour, because the defect is a spelling that four separate call sites shared.
Injecting one of the old reads makes the test fail and print the offending text.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`.

One process note, recorded because it cost work rather than because it changed the
code. The regression probe for that test was first run by editing the working file and
undoing it with `git checkout --`, which reverted to the last commit and discarded the
round's uncommitted fix along with the injected regression. The suite reported 187 of
195 and the loss was visible immediately. The change was redone, committed as a safety
point, and the probe re-run against a copy of the file instead. Nothing reached a
branch in the broken state.

Both suites pass: 24 repository tests and 194 of 195 Hexaemeron tests, 22 new in this
step. The single error is `ForgeReports`, unchanged and environmental.

Leads not pursued: the `load_state` lead from round 1 stands. `as_dict` guards the
reads this file makes; it does not make `load_state` validate the state it returns.

## Receipted lint rounds, step 1, round 3 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. Every sweep from rounds 1 and 2 was re-run against the fixed tree and came
back clean: 676 malformed state shapes with nothing raised, 42 mode-and-receipt pairs
all returning a boolean, and the source-level assertion that no chained read uses a
container default.

Two checks were new to this round.

**Backward compatibility against real data rather than a fixture.** The state and
ledger of the Ariadne run archived earlier today were copied to a scratch directory and
read with the new controller. `status` reports its five shipped steps, `verify` passes
48 ledger entries with the chain intact, `config get solidity` answers `"auto"`, and the
classifier reads that run's waiver as a non-Solidity round. That run's state was written
before any of this existed.

**The command line rather than the function.** A fresh run defaults to `"auto"`,
accepts `false`, and refuses `"maybe"` with a message naming the three modes.

The three bundled lints ran and each exited 0: `phylax`, `ephoros`, `hypomnema`. Both
suites pass: 24 repository tests and 194 of 195 Hexaemeron tests. The single error is
`ForgeReports`, environmental and unchanged.

Leads not pursued: the `load_state` lead stands from round 1.

## Receipted lint rounds, step 2, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`.

The new logic is a function of the round type, the findings count and three optional
exits, so it was swept rather than probed. All 108 combinations were run through a fresh
state via the command line -- two receipt kinds, findings of 0 and 1, and each of the
three exits absent, 0 or 1 -- and every accept or refuse matched the rule the code
documents. No combination differed.

Three properties were checked beyond the sweep.

**No reader assumes the new field.** Every existing read of a round touches `findings`
or `fixes_commit`. Nothing indexes `lints`, so a round recorded before this step has
nothing to trip over, and a test pops the key back out to hold that.

**The override leaves a trace.** `config set solidity true` lifts the requirement, which
is the point of having it, and a run that uses it to dodge the lints records
`{"path": "solidity", "value": true}` in the hash-chained ledger. `verify` passes on that
ledger, so the dodge is auditable rather than invisible. This is the honest limit of the
change: `hexctl` records what the caller reports, as the study's non-goals say, and
cannot know whether a lint really ran. What it can do, and now does, is refuse a round
that does not even claim.

**The refusal names only what is missing.** Passing two of three names the third and not
the two supplied, so the message tracks the actual gap.

Both suites pass: 24 repository tests and 213 of 214 Hexaemeron tests, 19 new in this
step. The single error is `ForgeReports`, environmental and unchanged.

Leads not pursued: the `load_state` lead stands from step 1 round 1. `verify` validates
the ledger chain and the state's phase consistency, not the shape of a round, so a
hand-edited round with a nonsense `lints` value would pass it.

## Receipted lint rounds, step 2, round 2 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding, and one guard added for a property nothing asserted.

`done_audit` calls a close clean when the last round found nothing, and the consistency
rule from this step forbids a zero findings count beside a non-zero lint exit. Together
those mean a clean close cannot sit on a failing lint. That is the property the whole
change buys, and it was emergent rather than tested: it holds because two separate rules
happen to compose, so a later edit to either could take it away without any test
noticing.

The new test walks the sequence rather than asserting the composition abstractly: a
failing lint beside zero findings is refused, the same failure recorded with a findings
count is accepted, closing is then blocked while that count stands, and only a genuinely
clean round closes with `clean` true and every recorded exit zero.

The three bundled lints ran and each exited 0. Both suites pass: 24 repository tests and
214 of 215 Hexaemeron tests. The single error is `ForgeReports`, environmental.

Leads not pursued: the two from earlier rounds stand. `load_state` validates nothing, and
`verify` checks the ledger chain and phase consistency rather than the shape of a round,
so a hand-edited round carrying a nonsense `lints` value would pass it.

## Receipted lint rounds, step 3, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: low; file: `plugins/hexaemeron/skills/fiat/references/audit-loop.md`; finding: Step 4 of the generic "One round" list still showed the bare command. It is complete for a Solidity round, and a reader working a non-Solidity round would have taken it as complete for theirs, then met the refusal. The step now says which round it is complete for and points at the section that adds the rest.; status: fixed in this round

The step reconciles prose, so the review looked for the failure a prose test cannot see: a
surface that still describes the old contract. Every mention of `audit-round` across the
repository's Markdown was read. One was stale and is fixed; the rest are the new receipt
table, the new reference section, the ledger row, this run's committed study and runbook,
a Solidity-agnostic `...` elision in the plugin README, an unrelated historical audit
entry, and Elenchus's SKILL.md naming the phase it serves.

The study's line about 21 call sites is left as it was: it describes the tree the run
started from, which is what a study's prior-art section is for.

The ledger was checked against the contract rather than only by the suite. The digest
`6e406e13adce5276ded6bfe7317c3229f069312b8a9de3a4a0c5c78c89ec9ca3` recomputes from
`open|receipted-lint-rounds|<current frontier>|<next Fiat job>` with its trailing newline,
the row sits on the evolution axis moving 3.4.1 to 4.4.1, and the frontmatter version
agrees with it.

Hexaemeron's plugin-level frontier was deliberately not touched. It concerns a published
end-to-end Solidity delivery, this run is not one, and Fiat's SKILL.md warns against
substituting one frontier for the other. The plugin's context blocks therefore need no
change, which is why this step edits no landing README.

The demonstration ran end to end against the checkout controller: `next` naming the three
flags, the refusal without them, acceptance with them, the three exits on the round in the
state file, a clean close, and `verify` reporting the chain intact.

The three bundled lints ran and each exited 0. Both suites pass: 24 repository tests and
214 of 215 Hexaemeron tests. The single error is `ForgeReports`, environmental.

Leads not pursued: the `load_state` lead is now this skill's held frontier rather than a
lead, so it leaves this list. `verify` still checks the ledger chain and phase consistency
rather than the shape of a round.

## Receipted lint rounds, step 3, round 2 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. Round 1's fix was re-read in place rather than trusted: the bare form at
`audit-loop.md:40` is still there, which is right, and the sentence after it now says the
form is complete for a Solidity round and points at the section that adds the rest. Every
other `audit-round` form in the repository's Markdown is either the new receipt table row,
the new reference section, or this run's committed study and runbook.

The demonstration was re-run against the committed tree: the round is refused without the
three results, accepted with them, and `verify` reports the chain intact.

The three bundled lints ran and each exited 0. Both suites pass: 24 repository tests and
214 of 215 Hexaemeron tests. The single error is `ForgeReports`, environmental.

Leads not pursued: `verify` checks the ledger chain and phase consistency rather than the
shape of a round.

## Receipted lint rounds, integrate -- 2026-08-19

Not an audit round. A record of what the integrate phase did and did not do.

The stack is consolidated: all three step branches merged into
`fiat/receipted-lint-results-as-structured-fields-on-h` in order, one merge commit each,
receipted from the real commit each time. The run branch already contained `main`, so no
base merge and no conflict this time.

The merge into `main` is refused, as it was for the Ariadne run. The pull request merge
API returns HTTP 403, "Merging into a protected base branch is not permitted for this
session type", and a direct push to `main` is rejected. Integration pull request #206 is
open from the run branch into `main`, `mergeable_state` clean, awaiting a human merge.

CI on the head is green: CodeQL and the four Analyze jobs. Worth recording that **no
workflow runs the Hexaemeron suite**. The repository has three workflows, and `lazarus.yml`
and `pandects.yml` are path-filtered to their own plugins, so all 39 tests added by this
run are covered by local evidence only. The same was true of the Ariadne run's 439 tests.

Both suites pass on the consolidated branch: 24 repository tests and 214 of 215 Hexaemeron
tests, the single error being `ForgeReports`.

## Metron budget check, step 1, round 1 -- 2026-08-19

The first audit round in this marketplace recorded under the contract #206 added. The
directive named the three flags before the round was taken, and the round carries their
exits.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R1-01; severity: medium; file: `plugins/hexaemeron/skills/metron/skills/../scripts/metron.py`; finding: `NaN`, `Infinity` and `-Infinity` were accepted as a budget limit and as a measurement. `json.loads` permits all three by default as a Python extension rather than as JSON. The consequence is specific to a comparison tool: every comparison against `nan` is False, including `!=`, so a `nan` measurement does not fail a threshold -- it falls through whichever branch is tested last and is reported as whatever that branch says. An infinite limit means nothing ever exceeds it, so the budget passes forever.; status: fixed in this round

Fixed at both layers. `parse_constant` refuses the three tokens while reading, which names
the token, and `number()` requires `math.isfinite`, which guards a value reaching the
comparison any other way.

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. No Solidity ships in this run, so the suite waiver covers the
Pashov pair.

The loader is a function of one document, so it was swept rather than probed. Every required
budget field was replaced in turn by each of sixteen values that satisfy a presence check
but carry nothing usable, 80 combinations, and the whole document and the measurement files
were mutated the same way: 178 mutations in total. Nothing raised. After the fix the only
values still accepted are legitimate ones: a short name, a short unit, limits of 0, 1 and
3.5, and a variance of 0.

Two accepted shapes were examined and left alone. An empty `measurements` object loads,
because a run that measured nothing is a real thing to record and step 2's `unmeasured`
verdict is what refuses it. A negative measurement loads, because a delta can be negative
and the comparison decides what it means rather than the loader.

Both suites pass on the fixed tree: 24 repository tests and 252 of 253 Hexaemeron tests, 39
new in this step. The single error is `test_elenchus_checker.ForgeReports`, which needs
`forge`; the proxy refuses both `foundry.paradigm.xyz` and GitHub releases, and it errors
identically on clean `main`.

Leads not pursued: `MAX_BYTES` caps each file at 4 MiB and nothing caps the number of
budgets a file may declare. A file with a million budgets would be read and reported rather
than refused, which is slow rather than wrong.

## Metron budget check, step 1, round 2 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R2-01; severity: medium; file: `plugins/hexaemeron/skills/metron/scripts/metron.py`; finding: A run or baseline carrying both shapes at once -- a `measurements` block and measurement values at the top level -- silently kept the block and dropped the rest. `{"measurements": {"a": 1}, "b": 2}` loaded as `{"a": 1}` with nothing said about `b`. For this check that is worse than an ordinary dropped field: a measurement that never arrives cannot produce an `undeclared` verdict, so a typo'd name would vanish instead of failing.; status: fixed in this round

The ambiguous document is now refused and the message names every stray value. Metadata
beside the block still loads, because a producer recording a note, a timestamp, a flag or a
list of tags alongside its numbers is doing the right thing, and only a stray *number* is
ambiguous.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`, `ephoros`,
`hypomnema`.

Three other file-handling probes behaved and are now guarded: a directory passed where a
file belongs is refused rather than raising `IsADirectoryError`, a file past `MAX_BYTES` is
refused, and a file that merely approaches the cap is still read. A symlink is followed,
which is left as it is: these paths are named by whoever runs the check rather than supplied
by a stranger, and refusing a symlinked budget file would break a legitimate layout.

Both suites pass: 24 repository tests and 257 of 258 Hexaemeron tests, 44 new in this step.
The single error is `ForgeReports`, environmental.

Leads not pursued: the budget-count lead from round 1 stands.

## Metron budget check, step 1, round 3 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. The sweep was re-run against the fixed tree and widened to cover the shape round
2 introduced: 185 mutations across every budget field, the whole document, the measurement
files, and a stray value beside a measurements block. Nothing raised, no document was
accepted that should not have been, and the only budget values still accepted are legitimate
ones -- a short name, a short unit, limits of 0, 1 and 3.5, and a variance of 0. The three
non-standard JSON constants are refused.

The three bundled lints ran and each exited 0: `phylax`, `ephoros`, `hypomnema`. Both suites
pass: 24 repository tests and 257 of 258 Hexaemeron tests. The single error is
`ForgeReports`, environmental.

Leads not pursued: the budget-count lead from round 1 stands. Nothing caps how many budgets
a file may declare, which is slow rather than wrong.

## Metron budget check, step 2, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: medium; file: `plugins/hexaemeron/skills/metron/scripts/metron.py`; finding: `--promote` wrote the baseline with `write_text`, which truncates before it writes. A write that died partway left the baseline as invalid JSON, and the baseline is what every later comparison is measured against: the previous value was gone with nothing saying so, and every subsequent run would exit 2 on a file it could no longer read. Reproduced by making the write fail after a short write and reading the result back.; status: fixed in this round

`write_atomically` writes a temporary file in the same directory, fsyncs it and replaces the
target, so the baseline is either the old contents or the new ones. A forced failure of
`os.replace` now leaves the file byte-identical and no temporary behind. This is the same
fault the Ariadne run fixed for `capture --out`, in a second place.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`, `ephoros`,
`hypomnema`.

The comparison is a function of seven inputs, so it was swept rather than probed. 2880
combinations of a run value, a baseline, both directions, two limits, three variances, a
present or absent measurement, and an undeclared name were each checked against the rule the
code documents. Nothing differed and nothing raised. All six verdicts were reached, and every
verdict's `failed` flag agreed with the `FAILING` list, which is what the exit status reads.

Both suites pass: 24 repository tests and 297 of 298 Hexaemeron tests, 40 new in this step.
The single error is `ForgeReports`, environmental.

Leads not pursued: `append_ledger` opens in append mode and writes one line, which is atomic
enough for a single short write on a local filesystem but is not guaranteed across a network
mount. A ledger is a record rather than a gate, so a torn line loses one entry rather than
changing a verdict.

## Metron budget check, step 2, round 2 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. Round 1's fix was re-verified and the round moved to the write path, which the
comparison sweep had not touched.

The ledger's shape is one JSON object per line, so the round asked what could break that. A
note carrying a newline, a carriage return, a quote, a tab or non-ASCII text is escaped by
`json.dumps`, so five such notes produced five lines, each parsing on its own with the value
preserved. That case is now guarded.

Concurrency was checked rather than assumed: six threads appending forty entries each produced
exactly 240 lines and all 240 parsed. That is left unguarded on purpose, because a threaded
test is a flake waiting to happen in a suite nobody watches, and the property it would guard
is a single short append in `a` mode rather than logic this run wrote.

Three smaller shapes behaved: an empty run against a declared budget is `unmeasured` rather
than nothing, and both report styles render a single verdict correctly, with the JSON `ok`
field agreeing with the exit status.

The three bundled lints ran and each exited 0. Both suites pass: 24 repository tests and 298
of 299 Hexaemeron tests. The single error is `ForgeReports`, environmental.

Leads not pursued: the network-mount caveat on `append_ledger` from round 1 stands, and the
budget-count lead from step 1.

## Metron budget check, step 3, round 1 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: low; file: `plugins/hexaemeron/README.md`; finding: The plugin README said "six more skills holding each phase to a standard, four of them with an executable check". Four was right on `main` -- `elenchus`, `phylax`, `ephoros` and `hypomnema` -- and this run made it five. A prose count of something the tree can be asked about goes stale the next time one is added, which is exactly what happened.; status: fixed in this round

The count is corrected and derived rather than trusted: a new test in `test_fiat_skill.py`
counts the phase skills that ship `scripts/<name>.py` and asserts the README's number word
matches. Reverting the count to four makes it fail, which was checked.

The step reconciles prose, so the review looked for a surface still describing the old shape.
Metron's own claim that it serves the `implement` phase with no Fiat counterpart is unchanged
and still true; the same sentence appears in `phylax` and `ephoros`. The portable entrypoint
routes to the canonical skill rather than describing its files, so it needed nothing.

The three bundled lints ran and each exited 0: `phylax`, `ephoros`, `hypomnema`.

The demonstration from the study ran against the committed tree: the regression fixture exits
1 naming the budget and its margin, the neutral fixture exits 0, `record` writes the reverted
attempt into the ledger with its verdicts, `SKILL.md` has no dangling links, and the script it
names runs.

The ledger was checked against the contract rather than only by the suite. The digest
`5186746b189eea981393a052e8437de3a179d36d1afa88b38b18384cec881cff` recomputes from
`open|measured-before-and-after|<current frontier>|<next Fiat job>` with its trailing newline,
the row sits on the evolution axis moving 0.1.0 to 1.1.0, and the frontmatter version agrees.

Both suites pass: 24 repository tests and 300 of 301 Hexaemeron tests. The single error is
`ForgeReports`, environmental.

Leads not pursued: the plugin's own version is not bumped by this run. #207 moved Hexaemeron
to 1.4.0 for the controller change, and metron gaining a script is the same class of thing:
an installation on 1.4.0 will not see `scripts/metron.py` until the version moves again. That
is a decision about release cadence rather than a defect in this diff, and it is named here so
it is not discovered the way #207 was.

## Metron budget check, step 3, round 2 -- 2026-08-19

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No finding. Round 1 found a prose count the tree could have answered, so this round asked
whether there were others rather than assuming that was the only one.

Every number word followed by a countable noun in the shipped prose of every plugin README,
runtime contract and canonical skill was pulled out and checked. Three were counts of tree
contents and all three hold: Hexaemeron's "six more skills" matches the six phase skill
directories, Ariadne's "five core gates" matches `len(gates.CORE_GATES)` and is already
asserted twice in that plugin's own document tests, and Pandects' "three succession laws" is
guarded at the repository level by
`test_marketplace_prose.test_pandects_prose_counts_the_laws_the_catalogue_holds`. The rest
were descriptive rather than counts, such as "one security round" and "one long step".

So the README's check count was the only unguarded one, and it is now derived.

The three bundled lints ran and each exited 0. Both suites pass: 24 repository tests and 300
of 301 Hexaemeron tests. The single error is `ForgeReports`, environmental.

Leads not pursued: the plugin-version lead from round 1 stands. An installation will not see
`scripts/metron.py` until Hexaemeron's version moves again, which is a release-cadence
decision rather than a defect in this diff.

## Metron budget check, integrate -- 2026-08-19

Not an audit round. A record of what the integrate phase did and did not do.

The stack is consolidated: three step branches merged into
`fiat/a-metron-budget-file-and-the-check-that-holds-a` in order, receipted from the real
commit each time. `main` had moved to 9ba4444 with the #207 version bump, which merged in with
no conflict because this run does not touch those files.

The merge into `main` is refused, as it was for the two runs before this. The pull request
merge API returns HTTP 403, "Merging into a protected base branch is not permitted for this
session type", and a direct push is rejected. Integration pull request #211 is open from the run
branch into `main` awaiting a human merge.

Both suites pass on the consolidated branch: 24 repository tests and 300 of 301 Hexaemeron
tests, 113 new across the run. The single error is `ForgeReports`.

## Ariadne state-fixture predicate, step 1, round 1 -- 2026-08-19

Reviewed: the gate 5 change on the Solidity release predicate, which closes the hole the
dataset run recorded as S4-R6-06 and left to the run that would inherit it. A new predicate
copies this branch, so a state-fixture predicate written over the hole would carry it.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R1-01; severity: low; file: `plugins/ariadne/tests/test_solidity_release.py`; finding: `deltas.current` set to `null` was refused by the code and held by no test. A producer emitting the key with nothing in it has said a side exists and then identified none, which is the case the absent branch must not swallow; membership rather than a truthiness test is what separates them, and nothing pinned that line; status: fixed in this round: two tests, one on each branch

The finding came from a mutation probe rather than a reading. Five mutants of the change were
built and the suite run against each: dropping the new block, requiring the side to be present
instead of checking it when present, skipping the covers check, dropping the baselined branch's
requirement that a comparison name a current side, and replacing membership with a truthiness
test. Four were caught. The fifth survived, which is what a missing test looks like from the
outside. All five are caught now.

The gate was also swept rather than probed. Every shape of `deltas` over a baseline, a current
side, a reason and one content section was built from an alphabet of eleven side values, six
reasons and three content states -- 2178 statements -- and each verdict compared against the
rule restated from the docstrings independently of the implementation. Zero disagreements.

The three bundled lints ran against the changed tree and each exited 0: `phylax`, `ephoros`,
`hypomnema`. No Solidity ships in this run, so the build's suite waiver covers the Pashov pair.

Suites on the fixed tree: 473 Ariadne tests, 24 repository tests, and 300 of 301 Hexaemeron
tests. The single error is `test_elenchus_checker.ForgeReports`, which needs `forge`; the proxy
refuses both `foundry.paradigm.xyz` and GitHub releases, and it errors identically on clean
`main`.

Leads not pursued: none.

## Ariadne state-fixture predicate, step 1, round 2 -- 2026-08-19

Reviewed: the same change from three angles round 1 did not reach, and once end to end.

No findings.

Seven digest shapes were put on the current side of a first release: `sha512` alone against a
statement carrying `sha256`, a matching `sha256` beside an unknown `sha512`, a non-matching
`sha256` beside `sha512`, an uppercased `sha256`, an empty set, an integer, and a list. Each
verdict is the one `covers` and `digests.check` document. The only pass is the case where a
shared supported algorithm agrees, which is the rule step 1 of the original build wrote.

Twenty-one hostile values were then put on the current side against both branches of the gate,
42 calls in total, to see whether the reordered block could raise where the old one returned
first. Nothing raised.

The proof is a before and after. The new conformance fixture was copied into a detached
worktree at `origin/main` and verified there: exit 0, with gate 5 reporting `pass -- no
baseline`. The same file on this branch exits 1 with gate 5 failing. The hole was live and is
closed.

One thing was examined and left alone. The covers check is guarded by a no-faults test, so an
unrelated fault -- an unknown delta section, say -- suppresses the line about the current side
being outside the statement. The gate still fails on the suppressing fault, so no statement
verifies clean because of it, and the dataset predicate guards identically. Reporting one fault
rather than two is this build's stated preference, written into gate 1's own docstring.

Leads not pursued: none.

## Ariadne state-fixture predicate, step 2, round 1 -- 2026-08-19

Reviewed: the new predicate module, its published schema, and the drift tests holding
one to the other.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: medium; file: `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py`; finding: The published schema caps each evidence count at 100000, taken from Lazarus's manifest schema, and the module enforced no ceiling at all. A count of 10 to the 30th passed the verifier and was refused by the schema shipping beside it; status: fixed in this round: `MAX_COUNT` enforced, and the drift tests now compare maxima and minima rather than field names alone
- id: S2-R1-02; severity: high; file: `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py`; finding: Gate 2 required `state_root`, which made the evidence check's central rule unreachable. Every statement that rule would refuse had already failed the gate, so it read as the safeguard this type exists for while deciding nothing. It also refused an honest capture that proved nothing and had no use for a root; status: fixed before the implement receipt: the root is required by what a statement claims, and gate 2 checks it only when present

The second finding came from writing the conformance fixture rather than from reading
the code. The fixture could not breach the evidence check alone, which is what the
naming convention demands, and the reason it could not was that the rule had nothing
of its own to decide.

The sweep was 509 leaf mutations: every required field replaced in turn by each of
eighteen values that satisfy a presence check while carrying nothing usable, plus
every block replaced by each of them, plus every block removed. Nothing raised.
Sixty-two mutations verified clean and each was read rather than counted.

The sweep also had a fault of its own worth recording. It called the predicate's
`check()` directly, so twenty of those sixty-two were mutations of `claims` and
`commands`, which belong to gates 1, 3 and 6 and cannot fail a check this module
returns. Re-run through `verify.report`, only the unmutated values verify clean, so
the core catches all thirty-four.

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. No Solidity ships in this run, so the build's suite waiver
covers the Pashov pair.

Leads not pursued: `chain_id` and `block_number` are unbounded above in the module
and in the schema, which is agreement rather than drift, and a well-formed nonsense
number is contradicted by the block hash beside it.

## Ariadne state-fixture predicate, step 2, round 2 -- 2026-08-19

Reviewed: the schema and the verifier against each other, on the same documents.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | high | `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py` | The all-zero hash matched the pattern and identified nothing, so a proof-backed count could sit beside a state root nobody filled in. The emitted-but-empty shape, in the one field this type exists to guard | fixed in this round: refused for the block hash and the state root, pinned by four tests |
| S2-R2-02 | low | `plugins/ariadne/schemas/state-fixture-v1.json` | The schema carried a comment saying a schema could not express the conditional state-root rule. Draft 2020-12 has `if`/`then` and can | fixed in this round: the rule is in the schema, and the document says which rule a schema still cannot carry -- the reason rather than the shape |
| S2-R2-03 | medium | `plugins/ariadne/schemas/state-fixture-v1.json` | The component path had no pattern, so the schema accepted paths the verifier went on to reject. A producer validating against the published shape would be sent into a refusal | fixed in this round: a pattern refusing a leading slash, a backslash, an empty segment and any `..` segment |

Both schema findings came from one technique: fourteen documents put through the
schema and the verifier with the verdicts compared. Two disagreed. A test now holds
the pair to the same answer on fifteen shapes, so they cannot drift apart quietly.

Fourteen state-root shapes were put beside a non-zero proof-backed count -- absent,
uppercase, unprefixed, too short, too long, all-zero, empty, whitespace, the string
`null`, an integer, a boolean, a list, a nested digest set, and `0x` alone. One got
through, which is the first finding.

The hash drift test now compares behaviour rather than pattern text. The module
refuses the all-zero value inside `hash32` and the schema refuses it inside the
pattern, so the two spell one rule in different places and comparing the strings
would report a disagreement that is not one.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 2, round 3 -- 2026-08-19

Reviewed: whether any test holds each rule the predicate adds, by mutating the rules
one at a time.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R3-01; severity: medium; file: `plugins/ariadne/tests/test_state_fixture.py`; finding: Changing the proof-backed rule from `> 0` to `> 1` left the suite green. Every test of that rule counted two records, so a fixture claiming exactly one proved record with no state root would have verified clean -- the smallest claim the rule exists to refuse, and the one a real capture is likeliest to make; status: fixed in this round: a boundary test, and a sweep across zero, one, two, three, a hundred and the ceiling

Fourteen mutants, one per rule: accept the all-zero hash, drop the state-root rule,
raise its threshold, stop requiring every evidence class, drop the count ceiling, let
a boolean count through, accept a truthy replay value, stop requiring both replay
fields, accept a hex block number, stop closing the chain object, stop requiring a
component digest to be a subject, accept a path leaving the fixture, drop the
duplicate-path check, stop closing the predicate shape. Thirteen caught. All fourteen
are caught now.

Checked and found sound:

- All thirty-three conformance fixtures re-verified after the zero-hash and ceiling
  changes. Every passing fixture is clean and every breaching one fails exactly one
  gate or check.
- The registry lists three types, and an unregistered type still reports that gates 2
  and 5 belong to a predicate and were not checked. Adding the third predicate did
  not disturb the first two.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 2, round 4 -- 2026-08-19

Reviewed: the comparison block for this type, the envelope path, and the strength of
the evidence round 2 left behind.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R4-01; severity: low; file: `plugins/ariadne/tests/test_state_fixture.py`; finding: The schema agreement test needs `jsonschema`, which this plugin does not depend on, so it skipped on every interpreter without the package. The evidence for round 2's two schema fixes was conditional on something nobody installs; status: fixed in this round: a companion test reads the schema and checks both rules are in the document. Structural, weaker than validating, and it never skips

The deltas matrix was swept as the Solidity predicate's was in step 1: 2178 shapes
over eleven baseline values, eleven current values, six reasons and three content
states, each verdict compared against the rule restated from the docstrings
independently of the implementation. Zero disagreements.

A statement of this type inside an unsigned DSSE envelope reports ten gate lines, runs
the predicate, and leaves nothing unchecked.

The suite runs green on Python 3.10, 3.11, 3.12 and 3.13. On an interpreter without
`jsonschema` the agreement test skips and the structural one runs, which was confirmed
rather than assumed.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 2, round 5 -- 2026-08-19

Reviewed: the helpers, the module's own constants, and the shipped fixture against the
capture it claims to describe.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R5-01; severity: medium; file: `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py`, `dataset.py`; finding: `usable_path` normalised only a doubled backslash, because the source wrote four characters where two reach the string. So `a\..\..\b` arrived as one path segment and passed the check that keeps a consumer inside the tree. One odd filename on POSIX; a traversal out of the tree on Windows; status: fixed in this round in both predicates, with the same normalisation and matching tests

The defect was already live in the dataset predicate, which this copy came from.
Fixing only the new copy would have meant shipping a fix for a defect while leaving
the original in place, so both are fixed together. `dataset.py` is outside this step's
file list and the deviation is recorded here rather than left for a reader to find.

A UNC prefix still fails, because it normalises to a leading slash. A trailing
separator still fails, because it names a directory. A backslash inside a filename
still passes, because refusing every one would refuse a legitimate POSIX name.

Checked and found sound:

- The five checks against a non-object predicate, built directly rather than through
  `from_dict`, which refuses one first. The guards are depth against a caller that did
  not go through the parser, which is what the tests are.
- The module's constants against each other: the proved class is one of the three,
  `CHAIN_FIELDS` covers `CHAIN_REQUIRED`, `REFUSALS` covers every replay field, and the
  five check names are distinct.
- The shipped passing fixture re-derived field by field from
  `plugins/lazarus/examples/goldfinch-v0` rather than trusted: the chain id, block
  number, block hash, state root, evidence counts, tool version, and every component
  digest and byte count. Zero disagreements.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 2, round 6 -- 2026-08-19

Reviewed: what round 5 changed, attacked again from a different direction.

No findings.

`usable_path` was swept over 8400 generated paths -- seven prefixes by ten segments by
six separator combinations by ten segments -- with each verdict compared against a rule
written independently as a segment walk rather than by reusing the module's own. Zero
disagreements, against both predicates, and the two copies agree with each other on
all 4200 paths, so the fix landed identically.

Checked and found sound:

- Unicode separator look-alikes. A path carrying U+2215 division slash or U+FF0F
  fullwidth solidus is accepted, correctly: no filesystem treats either as a
  separator, so the path names one file.
- A path containing a newline is accepted, which led to the one question worth
  following past the predicate. `digests.of_tree` separates a listing's fields with a
  NUL byte and its records with a newline, so a filename carrying a newline could in
  principle forge an entry. It cannot, and this was confirmed by trying it: the
  filesystem accepts a newline in a filename and refuses a NUL, so the field separator
  is unforgeable. A rename still changes the tree digest.

Leads not pursued: nothing cross-checks an evidence count against the presence of a
matching component, because this predicate reads a statement rather than a fixture
directory. It is stated in the document's own boundary section and it is step 4's
work, where capture takes the counts from the manifest.

## Ariadne state-fixture predicate, step 3, round 1 -- 2026-08-19

Reviewed: the conformance fixtures, read as the artefact another implementation checks
itself against rather than as test data.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | `plugins/ariadne/tests/fixtures/conformance/fail-gate5-state-fixture-baseline-without-digest.json` | Three changes from its passing sibling for a one-rule breach, so a reader diffing the pair could not tell which change caused it | fixed in this round: two, which is the least that reaches the branch |
| S3-R1-02 | medium | `plugins/ariadne/tests/fixtures/conformance/` | Most of the refusals this type can produce had no fixture. A verifier passing the whole set could have implemented one field of the pin and skipped another | fixed in this round: four fixtures for the rules distinctive to the type, and the remaining gap stated in the conformance document |
| S3-R1-03 | low | `plugins/ariadne/docs/conformance.md` | The coverage section I had just written claimed every breaching fixture in the directory was one leaf from its passing sibling. Measurement contradicted it | fixed in this round: the true numbers, and a test holding the claim it can defend |

The third is worth reading twice, because it is the same fault this project spends its
gates refusing. A sentence went into a shipped document asserting a property of the
fixture set, and the property had not been measured. Twelve of fourteen hold for this
type; nine of twenty-one elsewhere, up to eight leaves for the core fixtures written
against `pass-minimal.json`, which is a different and deliberate choice.

Measuring it needed a comparison carrying each value's type. Two of these fixtures
change only a type -- `header_bound` from `1` to `true`, `reaches_network` from
`false` to `0` -- and `True == 1` in Python, so a comparison without the type reported
them as identical to the fixture they breach against. The rules those two fixtures
exercise exist because of that same equality.

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. No Solidity ships in this run, so the build's suite waiver
covers the Pashov pair.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 3, round 2 -- 2026-08-19

Reviewed: whether the shipped files are what a stranger receives, and whether the
published schema agrees with the verifier about them.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R2-01; severity: medium; file: `plugins/ariadne/schemas/`; finding: All three schemas typed a delta side name as a string with no lower bound, so they accepted an empty name every verifier here refuses. Two shipped fixtures were files the schema accepted and the tool rejected; status: fixed in this round in all three, since the shape was copied between them

Four probes came back clean before that one. The sixteen files on disk are canonical
two-space JSON, ASCII, newline-terminated, with no tabs or carriage returns. Every
verdict survives a decode and a re-encode. Every verdict is the same inside an unsigned
DSSE envelope as bare. The CLI exits 0 for both passing fixtures and 1 for all
fourteen breaching ones.

A fifth checked every fixture field by field against
`plugins/lazarus/examples/goldfinch-v0`. Each agrees with the real capture except in
the leaf it deliberately mutates.

The technique matters more than the finding. The agreement test added in step 2 ran
over fourteen shapes somebody had thought of, and an empty side name was not one of
them. It runs over the shipped fixtures now, which are the files another implementation
actually reads.

One disagreement is beyond any schema and stays. Whether a component digest also
appears in the statement's `subject` array is a fact about the document around the
predicate, and no keyword reaches outside the body being validated.

Leads not pursued: two more schema disagreements, both outside this step's files and
both expressible. `schemas/dataset-v1.json` accepts an input carrying neither a digest
nor a disposition, which `anyOf` on an input item would close.
`schemas/solidity-release-v1.json` accepts delta content beside a null baseline, which
`if`/`then` would close.

## Ariadne state-fixture predicate, step 3, round 3 -- 2026-08-19

Reviewed: what round 2 changed, and what sat underneath it.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R3-01; severity: medium; file: `plugins/ariadne/scripts/ariadne_lib/core_predicate.py`; finding: `check_side` tested a side's name for truthiness, and `"   "` is truthy. A comparison could name either end with a space and pass the check whose whole job is making both ends identifiable; status: fixed in this round, with tests from all three callers

The schemas agreed with the verifier here and both were wrong, which is why round 2's
comparison stayed quiet: a lower bound refuses an empty string and accepts a space. A
pattern requiring one non-whitespace character refuses both, and all three schemas
carry it now.

`core_predicate.py` is outside this step's file list. The rule is written once and
called from all three predicates, so fixing it anywhere means fixing it everywhere.

This was the fourth appearance in this run of a field satisfying a presence check while
carrying no evidence, after the null current side, the all-zero hash, and `0` in place
of `false`.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 3, round 4 -- 2026-08-19

Reviewed: that same family, hunted across all three predicates at once rather than
waiting for a fifth instance.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R4-01 | high | `plugins/ariadne/scripts/ariadne_lib/predicates/solidity_release.py` | `confirmed_against_chain` was read for truthiness, so a deployment carrying `"null"` or `" "` verified clean and the report line read `0 unconfirmed against a chain`. The verifier told a reader every deployment had been checked against a chain, by a tool that reaches no network | fixed in this round: only the two booleans, with a fixture and tests |
| S3-R4-02 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/solidity_release.py` | `chain_id` was unchecked, so a deployment could name its chain `" "` or `true` | fixed in this round |
| S3-R4-03 | low | `plugins/ariadne/scripts/ariadne_lib/predicates/` | U+200B and U+2060 pass `stated()`, because Python's `str.strip()` does not treat them as whitespace, so a name or a path can render as empty and satisfy every check | recorded as a lead: refusing invisible characters is a policy decision with real trade-offs and belongs in its own change |

The first is the one that mattered. The field exists because an address printed with no
note reads as confirmed, and this let a note be written that meant nothing. Both were
already correct in the published schema -- `"type": "boolean"` and `"type": "integer"`
-- so the verifier was accepting statements its own shape refused, and a producer
following the tool would have shipped something the shape rejects.

The sweep was every leaf of every passing fixture replaced by each of fourteen values
that satisfy a presence check and carry nothing: 4426 substitutions, nothing raised.

The instrument was wrong first, and said so. It walked the predicate and wrote into the
document root, so all 784 substitutions of the first run raised `KeyError` into an
`except ... continue` and the sweep reported no findings because it had run nothing. The
zero total is the only reason that did not read as a clean round.

`tests/test_schema_agreement.py` is the systemic answer to three drift findings from one
technique. It runs the schema and the verifier over every shipped fixture of every
registered type. Three disagreements remain, each named with its reason, and four guards
stop a fourth joining them quietly: an unlisted disagreement fails, a listed one that no
longer disagrees fails, and a listed one naming a fixture that does not exist fails.

`solidity_release.py` is outside this step's file list. The deviation is recorded here.

Leads not pursued: the invisible-character finding above, and the two schema
disagreements carried from round 2.

## Ariadne state-fixture predicate, step 3, round 5 -- 2026-08-19

Reviewed: round 4's changes, from the other direction.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R5-01; severity: low; file: `plugins/ariadne/docs/conformance.md`; finding: The coverage section said the predicate makes 31 distinguishable refusals. That figure came from a list written by hand while auditing, not from anything a reader could recompute; status: fixed in this round: removed, with the denominator stated as unavailable rather than implied

Checked and found sound:

- The hardened deployments check refuses nothing legitimate: mainnet confirmed and
  unconfirmed, an L2, a chain id of 2 to the 53rd. It counts correctly across three
  deployments with one confirmed, and reports both faults when two are wrong rather
  than stopping at the first.
- The new agreement test was mutated seven ways to see whether it can fail at all.
  Five schema mutations in both directions, including one making a schema stricter
  than the verifier, and two on its own exception list. All seven caught.

The finding is the same fault as round 1's and worse in kind. A claim reads as an
assertion; a number reads as having been counted.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 3, round 6 -- 2026-08-19

Reviewed: the step's shipped documents, read as assertions.

No findings.

Three of the five earlier rounds found faults in prose rather than in code, so each
claim was checked against the code: fourteen breaching fixtures, twelve of fourteen at
one leaf, every fixture of this type named in the conformance document, the one allowed
schema exception named, three registered types in the skill and three in the registry,
every predicate field and evidence class and replay field named in the predicate
document, the passing fixture's counts equal to the ones in Lazarus's manifest, seven
gate lines and three further checks, exit 0, and every fixture path the document prints
present on disk. Fourteen claims, all holding.

The cheapest member of that family is now a test rather than a habit. Every
`tests/fixtures/...json` path any document under `docs/` prints has to exist, and the
test was proved able to fail by breaking one path and watching it catch rather than
accepted on the strength of a green run.

Leads not pursued: the three carried from earlier rounds, each named in
`ACCEPTED_BY_THE_SCHEMA` or in a round log with the keyword that would close it.

## Ariadne state-fixture predicate, step 4, round 1 -- 2026-08-19

Reviewed: the capture, which is the first step in this run that reads files somebody
else wrote.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R1-01; severity: medium; file: `plugins/ariadne/scripts/ariadne_lib/capture/state_fixture.py`; finding: `"schema_version": true` was accepted, because `True == 1` in Python and the check was a plain inequality against 1. That is the one check refusing a manifest this capture cannot read, and reading a later manifest as though it were version 1 is the evidence upgrade the capture exists to refuse; status: fixed in this round: the type is tested before the value
- id: S4-R1-02; severity: low; file: `plugins/ariadne/scripts/ariadne_lib/capture/state_fixture.py`; finding: `fixture_digest` was required and never looked at, so a manifest carrying `{"a": 1}` there passed a check implying the document is one Lazarus wrote; status: fixed in this round: its shape is checked, and a test asserts the value is still unused

The first is the bool-is-an-int trap, fifth appearance in this marketplace and the
first in code written for this run. It was found by sweeping every field of a real
manifest against twenty values that satisfy a presence test and carry nothing: 300
mutations over a copy of the shipped Goldfinch fixture.

Nothing raised anything other than `CaptureError`, which is the contract the command
line depends on to exit 2 rather than print a traceback.

Thirty-one mutations captured anyway and each was read. After both fixes the only ones
still accepted are legitimate: a zero count, which is a fixture that captured nothing
of that kind, and odd `tool_version` strings, which a version is allowed to be.

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`.

Leads not pursued: one of the accepted `tool_version` values is a zero-width space,
which is the invisible-character lead recorded in step 3 and not reopened here.

## Ariadne state-fixture predicate, step 4, round 2 -- 2026-08-19

Reviewed: the capture through the filesystem rather than through the manifest,
thirteen ways.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R2-01; severity: medium; file: `plugins/ariadne/scripts/ariadne_lib/digests.py`; finding: A fifo where a component belongs hung the capture indefinitely. `of_file` refused a symlink and read anything else, so `open` blocked until something wrote to it: no output, no error, no timeout; status: fixed in this round in `of_file` and in the shared walk

`tree_listing` has refused non-regular files since the first build and its comment
names this exact hazard. `of_file` never got the same guard, and both capture paths
call it directly rather than going through a tree digest, so the hang was live in the
dataset capture on `main` as well as in the one this step adds. A fix applied in one
place and not the other, found because this step wrote a third caller.

The probe found it by hanging. The round could not finish until it was fixed, which is
the most direct evidence a hang can offer.

Ten of the thirteen cases were already refused correctly: a symlink pointing out of the
tree, a symlinked subdirectory, `.git`, `__pycache__`, the manifest or the header
replaced by a directory, a manifest over the size cap, a manifest that is not UTF-8,
and a component that changed after the manifest was written.

Three captured and each was judged rather than counted. Two unreadable-path cases
captured because these tests run with rights that ignore file modes, which is the same
reason the suite already skips two permission tests. The third is `--fixture` itself
being a symlink to a real directory, which is captured on purpose: `confined` resolves
it, and the refusals are about symlinks inside a tree whose targets could be elsewhere.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 4, round 3 -- 2026-08-19

Reviewed: whether any test holds each rule the capture and its shared walk add.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R3-01; severity: low; file: `plugins/ariadne/tests/test_capture_state_fixture.py`; finding: Taking the check off the state root read from `header.json` left the suite green. The rule held and nothing held the rule: the header is read off disk exactly like the manifest and had no coverage at all; status: fixed in this round: six tests

Seventeen mutants, one per rule: the schema version, the fixture-digest shape, a
declared file the directory lacks, an undeclared file the directory holds, the digest
comparison, the byte-count comparison, a leading zero in a quantity, an unknown
evidence class, a class left out, a count outside the bounds, the caller's version
overriding the manifest, a component path leaving the fixture, a component declared
twice, replay written true, the state root taken unchecked, a fifo, and a symlinked
file. Sixteen caught, and all seventeen are caught now.

The six tests record what the rule actually is. The all-zero root, one too short, one
with no prefix, a number and a null are refused. An uppercased one is lowered rather
than refused, because that is two spellings of one value, as with the block hash. A
header with no state root leaves the field out, and the predicate's evidence check is
what refuses the proof-backed count beside it.

Leads not pursued: none new.

## Ariadne state-fixture predicate, step 4, round 4 -- 2026-08-19

Reviewed: the command line, and what the shared walk did to the two captures that
already shipped.

No findings.

Eleven command-line cases give the exit code they should: 0 for the happy path, for a
version agreeing with the manifest, and for a parameter; 2 for a missing flag, a
fixture that is not there, a fixture that is a file, an empty tool name, no reason and
no previous, `--previous` without its name, and a version disagreeing with the
manifest.

Checked and found sound:

- A failure prints its reason and no traceback, which is the contract the command line
  depends on to exit 2 rather than crash.
- `--out` writes, leaves no temporary file behind, and the written statement passes
  `verify` and `inspect` through the command line.
- The dataset capture still works end to end after moving to the shared walk, and the
  Foundry capture, untouched by this step, still works.
- Three separate processes produce a byte-identical statement, so the capture is
  deterministic across runs rather than only within one.
- The capture's output agrees with the hand-written conformance fixture on the pin, the
  counts, the replay block, and on the digest and byte count of all four components the
  fixture describes. The fixture names four of the eleven with human names; the capture
  names all eleven by path, because nothing on disk states a human name.

Leads not pursued: `capture/foundry.py` still defines its own `CaptureError`, so a
caller catching one does not catch the other. The dataset capture's is now an alias of
the shared class and Foundry's is not, because its `confined` does something different
and touching it buys nothing here.

## Ariadne state-fixture predicate, step 5, round 1 -- 2026-08-19

Reviewed: the reconciliation, by re-deriving it rather than rereading the diff.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S5-R1-01; severity: low; file: `plugins/ariadne/AGENTS.md`; finding: The runtime contract said `capture` writes only where `--out` points and every other subcommand prints, naming one of three capture subcommands. Accurate when written, narrowed silently when `capture-dataset` arrived, and narrower again now; status: fixed in this round: all three named, with what they have in common

It is the document that tells an agent what the tool writes, so a reader could take
the sentence as covering the subcommand it names and conclude the other two were not
spoken for.

Checked and found sound:

- The ledger digest recomputed from the header matches the stored row, checked against
  the contract's own computation as well as by hand.
- Every version agrees: the ledger at `ariadne-v2.1.0`, the skill metadata at 2.1.0,
  the plugin manifest and the marketplace entry both at 1.2.0.
- All twelve Ariadne marketplace-context blocks carry the ledger's frontier sentence,
  as do the audit record-status block and the root selection table row. The old
  sentence appears nowhere.
- The tool reports three registered types, and no document still claims two.

Two probe defects, recorded rather than hidden. The digest check stripped backticks
from one ledger field where the contract strips them from four, so the digest appeared
not to match until it was compared against the contract's own computation. The
frontier-surface check looked for the word Ariadne near a context block rather than for
the Ariadne context block, so ten of Lazarus's and Pandects's own frontier sentences
read as disagreements. Neither was a defect in the run.

The three bundled lints ran against the changed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`.

Leads not pursued: the root README's Lazarus row says an Ariadne state-fixture
predicate remains unimplemented, which this run makes false. That sentence is governed
by Lazarus's own ledger, and the versioning contract reserves a frontier sentence to a
completed frontier job for that skill. Changing it from here would be this run editing
another skill's held frontier, so it is left for the run that closes it.

## Ariadne state-fixture predicate, step 5, round 2 -- 2026-08-19

Reviewed: the run's output as a stranger meets it -- every command any Ariadne document
prints, run as written.

No findings.

Nineteen commands across the plugin README, the runtime contract, the examples README,
six documents under `docs/` and the skill. All nineteen exit 0 or 1, and the 1s are the
two the documents say exit 1.

A third probe defect belongs here, because it bears on what a clean round is worth. The
probe split command lines on whitespace rather than with `shlex`, so a quoted
`--first-capture-reason` fragmented into positional arguments and two documented
commands read as broken. Across these two rounds the probes were wrong three times and
the deliverable once. A probe with that history is weak evidence when it finally comes
back clean, so this round rests on the nineteen commands actually running rather than
on the absence of a finding.

Leads not pursued: the Lazarus frontier sentence carried from round 1.

## Goldfinch preservation release, step 1, round 1 -- 2026-08-19

Reviewed: the release document type, swept as a format other tools will write
against rather than read as a diff.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: L1-R1-01; severity: medium; file: `plugins/lazarus/schemas/release-v1.json`, `scripts/lazarus_lib/paths.py`; finding: Every string field in a release took a value that satisfies its length check and renders as empty. Whitespace is one kind and a legal POSIX filename; U+200B and its neighbours are the other, because `str.strip` does not treat them as whitespace; status: fixed in this round: `lazarus_lib/text.py`, wired into the path helper and the release semantics

The second kind is the one worth naming. `component` and `component` followed by
a zero-width space are two different files that look identical in any listing, in
any terminal, in any review. It has been recorded as a lead twice in this
marketplace and closed nowhere, and it is closed here for Lazarus because it
turned up in a format being written rather than one being read. The Ariadne side
stays open and is named in that plugin's own rounds.

The sweep was seventeen hollow values through each of sixteen leaves, 272
substitutions, plus every block replaced by each of them and every block removed.
Nothing raised outside `FormatError` and `PathError`, which is the contract the
command line depends on to exit 1 rather than print a traceback. Every block
replacement and removal was refused. Thirty-two values were accepted and each was
read; the rest of those are legitimate, being a zero count and the required
`false`.

`text.py` answers one question and is applied to identifiers rather than to
prose, so a reason field explaining a skipped capture may still say whatever a
person needs to write. Non-Latin text stays visible, asserted in four scripts,
because refusing most of the world's names would be a worse defect than the one
being fixed.

Two errors of my own, recorded because they cost the round time and because a
round that only lists the code's faults is not a record of what happened. I
asserted on one string replacement and not the next, so an import silently did
not land and seventy-nine tests failed with a `NameError` until I read one. And
the module inventory test refused `text.py` before I had named it, which is that
contract working rather than a fault.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. No Solidity ships in this run, so the suite
waiver recorded at init covers the Pashov trio.

Leads not pursued: the previous run's audit record is split across two files, and
the split is mine. Fourteen sections sit in this file and six in
`plugins/ariadne/audit/AUDIT.md`, so a reader of either sees part of one run.
Nothing is lost. It belongs to a different plugin and a finished run, and it is
on this run's ledger as `previous_run_audit_split` rather than fixed from here.

## Goldfinch preservation release, step 1, round 2 -- 2026-08-19

Reviewed: what round 1's change reaches, since it touched a path helper the
manifest also uses.

No findings.

The question worth asking of a stricter rule is whether it refuses anything real,
and it does not. All eleven components the shipped Goldfinch fixture holds are
still accepted. 1734 generated paths -- three prefixes by seventeen segments by
two separators by seventeen segments -- were compared against a rule written out
independently rather than by reusing the module, with zero disagreements.

Checked and found sound:

- Fourteen filenames anybody might write are accepted, including ones carrying
  spaces, dates, French accents, Japanese and Cyrillic.
- The shipped example still verifies to the same fixture digest and the same
  three counts.
- `validate schemas` passes with the re-pinned digest, and the existing offline
  demonstration still exits 0.

Leads not pursued: the split audit record carried from round 1.

## Goldfinch preservation release, step 2, round 1 -- 2026-08-19

Reviewed: the binding rule, which decides whether a statement describes this
fixture and whether it claims more than the records support.

Seven findings, all one shape: a field a producer writes and nothing reads.

The rule the module exists for was sound. Fifteen mutants against it all died,
including the one that compares the counts in a single direction, and the study's
tamper is refused naming both numbers. What the mutation could not show was the
half of the document nothing looked at. A sweep of twenty hostile values through
every leaf of a statement -- 460 substitutions -- bound 162 of them.

The seven, in the order they were closed:

- `_type`. A predicate type says how to read a predicate; the statement type says
  the document is the kind of thing that has one. Any value bound, so a bare
  object carrying two strings was read as an attestation.
- `chain_id`, `block_number` and `state_root`. The block hash was the only thing
  pinned. A statement naming the right hash, another chain, another height and
  another state root bound, and read as though all four had been corroborated.
  Every proof in a fixture is checked against the header's state root, so a
  statement naming a different one describes a verification nobody ran.
- `reaches_network`. Its neighbour `canonical_chain_claim` was refused unless
  exactly false and this one was not read, so a statement could say the records
  had been corroborated live.
- The in-toto `subject` list. The detail lives in `predicate.fixture_subjects`,
  and `subject` is the array a policy engine matches on. A component described in
  the predicate and absent from the subject list was bound here and invisible
  there.
- Subject names. Nothing required a name to name anything, and nothing refused
  one name over two digests, which leaves a reader matching by name unable to
  tell which was meant.

The verified report now carries `block_number` and `state_root` alongside
`block_hash`, all three from the header the proofs were checked against, so the
binding compares against what verification established rather than against what a
manifest claims.

Checked and found sound: the counts come from `verify_fixture` and not from the
manifest, which is the whole point of the step; a manifest carrying inflated
counts changes nothing.

Two further findings, one in a test and one in me. Mutation found a rule with no
test that reached it: repeating a whole fixture subject now trips the
duplicate-name rule first, so the duplicate-path rule needed an entry differing
everywhere but the path. And the mutation probe writes the module in place and
restores it afterwards, which it does not do when the runner is killed; a
two-minute timeout left a mutation on disk. The probe now refuses to start unless
the unmutated suite passes, and says so when it has put the file back.

Leads not pursued: the previous run's split audit record, carried from step 1,
is being fixed as its own change off `main` rather than from inside this run.

## Goldfinch preservation release, step 2, round 2 -- 2026-08-19

Reviewed: the two documents the binding is handed alongside the statement, and
the study's pair measured live rather than in a sample.

Two findings.

A manifest whose component path is a list raised `TypeError` from inside a set,
and a report whose count is `None` raised `TypeError` from inside a comparison.
Forty-eight substitutions and eight removed keys ended in a traceback rather than
a refusal. None of them can come out of `verify_manifest` or `verify_fixture`,
which is the point: the caller who reaches them is the one who handed over the
manifest read off disk instead of the verified one, and a traceback out of the
middle of a comparison tells them nothing about which document was wrong. The
module now names the fields it reads out of each and refuses what it cannot read.
It is not a second verification, and the docstring says so.

Names are compared in composed form now. Two Unicode spellings of one name bound
together, which is the ambiguity the duplicate-name rule exists to refuse: a
reader that normalises sees one name over two digests.

Checked and found sound:

- The Ariadne statement for the shipped `goldfinch-v0` fixture binds with every
  check, against the real fixture rather than a sample.
- The study's tamper is refused: six proof-backed records claimed where two
  verify.
- Understating is refused too, and says so: nought recorded RPC records claimed
  where four verify.
- A statement naming another chain, another height or another state root is
  refused against the real fixture.

## Goldfinch preservation release, step 2, round 3 -- 2026-08-19

Reviewed: what the binding leaves behind, and whether two fixtures can be
confused for each other.

No findings in the module. One in the probe.

None of eight calls -- the clean case and seven refusals -- changed any of their
three inputs. A hundred calls agreed. The returned list is the caller's own, so
a caller who appends to it changes nothing for the next.

A second fixture was built rather than imagined: synthetic material written to a
temporary directory, a manifest built over it, and a statement captured over it
by Ariadne. Each statement binds against its own fixture. Each is refused by the
other, naming both block hashes.

Ariadne's own shipped statements were run through the same rule. The clean
`goldfinch-v0` statement binds. The tampered one with its state root removed is
refused, by the rule round 1 added.

The finding was mine. The section that edits a component after a statement is
written replaced a string the file does not contain, so it reported a clean
result having tested nothing. It now refuses to run unless the edit changes
bytes. With a real edit the fixture stops verifying, on a digest mismatch, which
is where a release must stop -- and the statement still binds against the report
taken before the edit, because the binding is handed a report rather than a
directory. That is a constraint on the command in step 3, which has to verify and
bind in one pass rather than accept a report from elsewhere.

## Goldfinch preservation release, step 2, round 4 -- 2026-08-19

Reviewed: what happens at the sizes nobody writes by hand.

Three findings.

A statement can be sixteen mebibytes, which is around a hundred and ten thousand
fixture subjects. The binding read every one of them and then named every one of
them in the refusal. The message for a statement describing two hundred thousand
components ran to tens of megabytes of comma-separated paths: a refusal nobody
reads, in a log nobody keeps.

Both ends are bounded. A statement describing more components than a fixture can
hold is refused with the limit named, and the limit is taken from the manifest's
own `MAX_COMPONENTS` rather than restated, so the two cannot drift into a
statement this accepts and no fixture can satisfy. The subject list gets a looser
cap, because it legitimately names more than the components -- the capture itself
is one. And a refusal spells out eight names, then counts.

The verifier had the same message. Its proof-target list is bounded by the plan
schema at a hundred thousand addresses, which is four megabytes of refusal.
`listed` lives in `text.py` beside `visible` because they are one concern at two
scales: whether the thing a person reads shows them anything.

The third: the statement `_type` told shape and disagreement apart in one place
and not the other. A caller catching a format problem should not have to catch an
integrity one to learn a field was blank.

Checked and found sound: exactly the limit is read rather than refused, since a
fixture may hold that many.

## Goldfinch preservation release, step 2, round 5 -- 2026-08-19

Reviewed: which statements of the module the tests execute, and whether the names
it publishes still match what it does.

One finding in the module, three in the probe.

Of a hundred and seventy-four executable statements, a hundred and seventy-three
were reached. The one left was the conversion failure in the hex-quantity helper,
where a value starts with `0x` and then is not a number. Nothing in a verified
manifest or report can get there, which is why it went unnoticed, and it is
reachable by the same caller mistake the rest of the guards exist for. It has a
test now; the code did not change.

The three in the probe are worth recording because two of them made it report a
clean result. Its tracer matched any file whose name ends in `binding.py`, so it
counted lines of the test file as coverage of the module and called three
module-level constants reached that were not. Fixing that showed all seven
constants unreached, because they run at import before the tracer is installed,
so the probe reloads the module under trace. Its claim that the module imports
nothing outside this package read relative imports wrongly, since `ast` records
the leading dot as a level rather than in the name.

Checked and found sound: eight check names over seven calls, each name distinct,
in the order the calls are made; the module runs no subprocess, opens no file,
and imports nothing outside this package and the standard library.

## Goldfinch preservation release, step 2, round 6 -- 2026-08-19

Reviewed: whether anything here passes for the wrong reason.

No findings.

Every one of the fourteen test classes passes alone in its own process, and the
whole suite passes under five shuffled orders. The question is not idle: a test
file in this marketplace was found last run passing only under discovery order,
because another module's import supplied what it needed.

Every instrument the five rounds before this one built was run again against the
finished module. Thirty-seven mutants, none surviving. Six hundred and twenty
substitutions through the statement and five hundred and forty through the two
documents handed alongside it, none raising anything outside `LazarusError`. None
of the three inputs changed by a call. A hundred and seventy-four of a hundred
and seventy-four statements reached.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. No Solidity ships in this run, so the suite
waiver recorded at init covers the Pashov trio.

## Goldfinch preservation release, step 3, round 1 -- 2026-08-19

Reviewed: the release command, which verifies a fixture, binds a statement to it,
and writes a directory holding both.

Six findings.

Twenty rules were mutated and five survived, which is five rules nothing pinned:

- An output that is a dangling symlink. `exists` follows the link and says no, so
  the name reads as free while a rename onto it would replace the link.
- The comparison between the copy's digest and the original's. The test that
  broke the copy broke its verification too, so it raised before reaching the
  comparison. Reaching it takes a second fixture that verifies cleanly to a
  different digest.
- Validation of the document before it is returned. Nothing built a document the
  schema refuses, so removing the check changed no result.
- The check refusing a statement that is not an object. This one was removed
  rather than tested. The binding already refuses a non-object, in the words it
  uses for every other shape it will not read, and two authorities on one
  question is one too many.
- One read of the directory rather than two, which is the decision the module
  docstring leads with. Verification and binding both need the manifest, and
  two reads see two states.

A sweep then asked the release's own question fifty-eight times: after a refusal,
is anything left behind? Eighteen malformed statements, thirteen output paths,
fourteen fixture paths and thirteen statement paths. Nothing raised outside the
plugin's own errors or the operating system's, and no output or staging directory
survived a refusal. A component removed, added, edited or replaced by a symlink
between capture and release is refused, naming which. A component whose mode
changed is released, because a mode is not evidence.

The sixth finding was in the probe, and it is the same class caught in step 2
round 3: the case that edits a component replaced a string the file does not
contain, so it reported a release written where it should have reported a
refusal. It now refuses to run unless the edit changes bytes.

## Goldfinch preservation release, step 3, round 2 -- 2026-08-19

Reviewed: the window the release cannot close, what two runs agree on, and what
the digest actually covers.

Three findings.

The release was written with mixed modes: directories at 0700 and files at 0644,
inside a plugin whose fixture writer uses 0600 throughout. The directory gated
it, so nothing was exposed, but one artefact with two rules about who may read it
is a rule nobody can state. Everything a release holds is 0600 or 0700 now. A
release is not published by being written; whoever hands it over opens it up
deliberately.

The digest function's docstring claims that a field added to the schema and not
to the digest identity would be a test failure. Nothing tested that. It does now,
by comparing the identity against the schema's own list of required fields, one
field at a time.

The third is a limit rather than a fix, and it is worth stating plainly. The
output name is free when a run begins, and the copy takes time. The name is
checked again after the copy, which narrows the window, and the comment says it
does not close it: between the last check and the rename the name is still
unheld. What a lost race costs is now recorded rather than assumed. Rename
replaces an empty directory and nothing else -- a file, a symlink, or a directory
holding anything survives, the release refuses, and the staged copy is removed --
and a process that can win that window can rewrite the finished release anyway.

Checked and found sound: two runs over one fixture and statement produce
byte-identical releases, down to the fixture copy. A release nobody can rebuild
is a release nobody can check.

## Goldfinch preservation release, step 3, round 3 -- 2026-08-19

Reviewed: which statements the tests reach, whether a release touches what it
reads, and the shipped fixture released end to end.

Two findings, both about a statement handed over from inside the fixture it
describes.

The case already refused itself twice over, and neither refusal named the reason.
An unlisted file fails verification. A listed one would have to carry its own
digest, which no file can, so the reader gets a digest mismatch and a while to
work out why. The reason is the one the release document is already held to: the
fixture digest would cover the statement made about the fixture. The release says
that now, before it reads anything.

The second was in the check written for the first. It skipped silently when a
path would not resolve, which is the quiet failure this plugin refuses everywhere
else. A symlink loop is the case that gets there, and `pathlib` reports that one
as a `RuntimeError` rather than as the `OSError` the kernel gave it.

Checked and found sound:

- Seventy-five of seventy-five statements reached.
- A release leaves the fixture and the statement byte for byte and mode for mode
  as it found them.
- The shipped `goldfinch-v0` fixture releases, reads back with every digest and
  count agreeing, and still verifies after the release directory is moved
  elsewhere.

## Goldfinch preservation release, step 3, round 4 -- 2026-08-19

Reviewed: the document the command produces, against the schema meant to
describe it.

Two findings.

Four hundred and eighty-three hostile values went through every leaf of a
release the command had just produced. Two came back accepted where they should
not have: a fixture path of `.` and a statement path of `.`.

The cause is in `paths.py` rather than in the release. `PurePosixPath(".")` has
no parts at all, so every part-based check in the path rule ran over nothing and
the value came back unchanged as though it named a file. It names the directory
itself. Both the manifest and the release document read paths through that
helper, so a manifest component could be declared as `.` too; it failed later, on
a read that found a directory, which is a refusal that explains nothing.

Checked and found sound, and worth writing down because it looks like a finding
until the line is drawn: `validate` accepts a release whose digest no longer
covers it. That is the same line `validate manifest` draws, measured rather than
assumed -- a manifest carrying a wrong fixture digest passes it too. `validate`
answers whether a document is well formed; `verify` answers whether its digests
hold. The release digest is checked by `verify-release`, which is the next step.

Also sound: no field can be added to or removed from a release without the
schema refusing it, at the top level and inside each of the four blocks. All
twelve test classes pass alone in their own process, and the suite passes under
three shuffled orders.

The second finding was in the probe. Its class list was read out of the source
with a string split, which picked up a helper class that is not a test case and
reported it as a class failing alone.

## Goldfinch preservation release, step 3, round 5 -- 2026-08-19

Reviewed: the shared path rule the previous round's fix touched, and then every
instrument built for this step.

No findings.

The path rule was compared against a rule written out separately, leaning on
`posixpath` rather than on `pathlib` parts, which is where `.` slipped through.
Seven thousand five hundred and eighty-one paths -- five prefixes by
twenty-two segments by three separators by twenty-two segments, plus each segment
alone and with a separator at either end. No disagreements, and nothing raised
outside a path error.

Then the earlier instruments, all against the finished step: twenty-three
mutants, none surviving; fifty-eight hostile paths and statements, none leaving
an output or a staging directory behind; seventy-five of seventy-five statements
reached; four hundred and eighty-three substitutions through a produced release,
accepted only where a filename is legitimate; twelve classes passing alone and
the suite passing under three shuffled orders.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. No Solidity ships in this run, so the suite
waiver recorded at init covers the Pashov trio.

## Goldfinch preservation release, step 4, round 1 -- 2026-08-20

Reviewed: `verify-release`, which reads a release back and checks every claim it
makes about itself.

Three findings.

Fifteen rules were mutated and four survived. Two of those trace to one test that
passed for the wrong reason, and it is the more interesting half of the round.

The test for a fixture reached through a symlinked segment put the symlink at the
top of the release, where a different rule refuses it for being an unaccounted
symlink. So the rule under test never ran, while the test read as though it
covered it. Removing the no-follow flag from the directory walk left the suite
green, and so did replacing the confined walk with plain path joining. The
symlink is buried a level down now, and a companion test proves the same fixture
reached without a symlink still verifies, so the test cannot pass for a fixture
that is simply absent.

The third: the read helper normalised a path and then handed it to a reader that
normalises it again.

Two mutants were dropped rather than caught, because no test can tell them apart
from the original. After the count comparison passes, the document's counts and
the fixture's are the same numbers, so reporting either is the same value.

A sweep then edited a release every way there is. One byte flipped at the start,
the middle and the end of each of its seven files. Each file truncated, emptied
and doubled. Each file replaced by each other file, forty-two pairs. And every
one of twenty document fields changed with the digest restamped, so each change
had to be caught on its merits rather than by the digest. Everything was refused
except setting a path to the value it already had.

## Goldfinch preservation release, step 4, round 2 -- 2026-08-20

Reviewed: what the write says against what the read says, and whether a release
is a document or a layout.

No defects. Two properties nothing pinned.

The write and the read compute the same seven claims about one release by
different routes, and nothing compared them.

The reader honours the paths the document names, and nothing said so. A release
whose fixture sits at `state` and whose statement is `attestation.json` verifies,
as does one with the fixture a level down, and the unaccounted-file rule follows
the document rather than the word `fixture`. A reader that looked for its own
names regardless would be reading a layout, and the two path fields in the
document would be decoration.

Checked and found sound:

- 114 of 114 statements reached.
- Neither of two releases accepts the other's fixture, statement or document,
  with a companion test proving both verify on their own, so the three refusals
  cannot be passing for a pair that never verified.

## Goldfinch preservation release, step 4, round 3 -- 2026-08-20

Reviewed: whether anything here passes for the wrong reason, and the whole path
through the commands.

No findings.

All seventeen test classes pass alone in their own process, and the suite passes
under three shuffled orders.

On the shipped `goldfinch-v0` fixture, five commands run in sequence and each
exits 0: verify the fixture, release it, verify the release, validate the
document, and verify the fixture copy on its own. Then three tampers, one at a
time, each exiting 1 and naming what disagreed: a proved count raised in the
statement, a byte changed in a recorded RPC component, and the block the document
records.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. No Solidity ships in this run, so the suite
waiver recorded at init covers the Pashov trio.

## Goldfinch preservation release, step 5, round 1 -- 2026-08-20

Reviewed: every surface this step touched, against what the code does, and
whether the guards against a stale release actually bite.

Two findings, both in the probe.

The surfaces agree. Nine files state the new frontier and none states the old
one. The ledger label, the skill frontmatter, both host manifests and the
marketplace entry all read 1.1.0. The eight check names appear in three places --
the documentation table, the binding's own tuple, and the shipped release
document -- in the same order in each. No link is broken across six documents,
every command the prose promises exists in the command line, and a clean
worktree checkout verifies both the fixture and the release and passes the suite.

The guards bite. Six drifts, six caught, each one failing the suite rather than
shipping quietly: a byte in the release's fixture copy, a count in its statement,
the block its document records, the document's own digest, a check name the
binding makes, and a manifest rewritten by a later writer. That last one is the
recapture case the runbook asked for, and it fails seven tests.

The findings in the probe are worth recording because one of them made it report
a clean pass. Its edit to the release digest searched for a string with a space
after the colon, and canonical JSON has no space there, so it changed nothing and
would have counted a drift as caught having tested nothing. That is the fourth
edit in this run to miss its target, which is why the probe now refuses to count
a no-op.

The second: two earlier runs of it were killed at the two-minute mark with a
tracked file mutated, and a restore that lives in a `finally` block does not run
when the runner is killed. It now refuses to start on a dirty tree and says what
is outstanding, rather than measuring a baseline that is already wrong.

## Goldfinch preservation release, step 5, round 2 -- 2026-08-20

Reviewed: whether the shipped release stands on its own, and whether the
statement it ships survives its own author's gates.

One finding, in the probe.

Carried into another directory the release verifies. With the checked-in fixture
renamed out of reach it still verifies, which is the property that matters:
nothing inside a release reaches back to where it was made.

Ariadne's own `verify` passes every gate over the shipped statement -- the seven
core gates and the three named checks -- reporting two proof-backed records, one
header-bound and four recorded RPC. A release shipping a statement its own
author would refuse would be a strange thing to archive.

The release and the statement agree on the predicate type, the block, the three
counts, the canonical-chain claim and the component list. The demonstration
prints all nine things its docstring promises and leaves nothing behind in the
repository.

The finding was mine: the probe called `ariadne verify` with a flag it does not
take, so the first run reported exit 2 and a usage message rather than an
answer.

## Goldfinch preservation release, step 5, round 3 -- 2026-08-20

Reviewed: everything once more, after the merge brought the base branch in.

One finding, in the probe.

Thirty-eight test classes across seven modules each pass alone in their own
process. The suite passes under three shuffled orders, at three hundred and
sixty-two tests. Both demonstrations exit 0.

The merged audit record holds a hundred and fifty-seven sections and no conflict
markers: twenty from the previous run's state-fixture predicate, sixteen from
this one, and the rest from every run before them. The Ariadne plugin's own build
record still stands at four hundred and sixty-six lines, which is what the
separate change to un-split that record was for.

The finding was mine again. The probe ran the root suite from the plugins
directory rather than the repository root, so `unittest` could not import the
start directory and the probe printed an `ImportError` as though the suite were
broken. Run from the root it passes, as it has all along. That makes five edits
or invocations in this run that missed their target and reported the miss as a
result, which is the argument for every one of these probes checking its own
premise before it counts anything.

## Goldfinch preservation release, step 5, round 4 -- 2026-08-20

Reviewed: the same sweep, with the probe run from where it should have been run.

No findings.

Thirty-eight classes alone, three shuffled orders at three hundred and sixty-two
tests, the root suite at twenty-four, both demonstrations exiting 0, and the
merged audit record at a hundred and fifty-seven sections with no conflict
markers.

Worth naming what this step's four findings had in common: every one of them was
in the measuring apparatus and none in the work. The shipped release, the
statement beside it, the ledger and the marketplace prose held under every check
made of them. What kept failing was the probe -- an edit for a string the file
does not contain, a search for a space canonical JSON does not have, a flag a
command does not take, a suite run from the wrong directory. Each surfaced as a
finding rather than as a clean pass because the probe checks its own premise
before it counts anything, which is the habit this run bought.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. No Solidity ships in this run, so the suite
waiver recorded at init covers the Pashov trio.

## Protasis discipline cores, step 1, round 1 -- 2026-08-20

Reviewed: the two committed spec documents, `docs/protasis-discipline-cores/study.md`
and `docs/protasis-discipline-cores/runbook.md`, as the whole of this step's diff.

No findings.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. No Solidity ships in this run, so the suite
waiver recorded at init covers the Pashov trio. Root suite 24/24, plugin suite
303/303, imprimatur clean over both documents.

The risk register names four concerns. Three of them (path handling, hostile
document content, a miscount reported as clean) belong to the checker and have
no surface in a step that commits two documents. The fourth is the ledger, and
the check here is that this step does not touch it: the diff is confined to
`docs/`, and `EVOLUTION.md` is step 4's business alone.

Two things the step corrected before it was receipted, both found by running the
stated exit rather than by reading it. The runbook's exit commands named
`python3 -m unittest discover -s plugins/hexaemeron/tests -t .`, which cannot
load: the directory is not an importable package and `AGENTS.md` documents
`python3 plugins/hexaemeron/tests/run_tests.py` instead. The study also assumed
Python 3.11 where the interpreter is 3.14.6. Both were wrong on the page, which
is the cheapest place for them to be wrong, and both are now stated as the
commands and the version that actually hold.

Leads not pursued: the installed Fiat controller's `audit-round` accepts only
`--findings`, `--log` and `--fixes-commit`, while this repository's
`fiat-v4.4.1` ledger records that the receipt takes the three lint exits. The
installed plugin is behind the checkout. The lint outcomes are therefore
recorded in this entry rather than as structured receipt fields. Out of scope
here: it is a Fiat concern, not a Protasis one, and this run's topic does not
touch the controller.

## Protasis discipline cores, step 2, round 1 -- 2026-08-20

Reviewed: the contract growth in `plugins/hexaemeron/skills/protasis/SKILL.md`,
which is the whole of this step's diff.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: medium; file: plugins/hexaemeron/skills/protasis/SKILL.md; finding: The frontmatter description enumerates what the contract holds and still listed only the four original commitments after five study items and a step field were added. That text decides whether the skill triggers, so an understated list costs a run that should have been held to the disciplines.; status: fixed in 70f5b66

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24, plugin suite 303/303,
imprimatur 100.0 clean before and after the fix.

The risk register's four concerns: path handling, hostile document content and
a miscount reported as clean all belong to the checker, which step 3 builds, and
have no surface in a prose change. The fourth is the ledger, and the check is
that this step leaves it alone. The diff is one file and the version in
frontmatter is untouched, so the single ledger write stays step 4's.

One judgement worth recording rather than filing. Item 9 asks for each boundary,
what is worth taking at it, and the control that closes it, which follows the
same three-part shape phylax uses. The line between citing and restating is
whether the text carries the rules or the question, and this carries the
question: no STRIDE table, no always/ask-first/never list, no control catalogue.
Phylax remains the only place those live. Recorded because the next person to
grow this contract will stand at the same line.

Leads not pursued: none.

## Protasis discipline cores, step 2, round 2 -- 2026-08-20

Reviewed: the same file with round 1's fix applied.

No findings.

The three bundled lints ran against the fixed tree and each exited 0: `phylax`,
`ephoros`, `hypomnema`. Root suite 24/24, plugin suite 303/303, imprimatur
100.0 clean.

Round 1's fix was checked rather than assumed: the description now names both
the discipline questions and the gates a step declares, the study still holds
twelve numbered items, Disciplines is still the last field of the schema, and
the checklist still covers both additions. A fix to trigger text is the kind
that can quietly contradict the body it advertises, so the check compares the
two rather than reading the diff.

## Protasis discipline cores, step 3, round 1 -- 2026-08-20

Reviewed: the checker, its tests, its four fixtures, and the README count that
an existing test derives.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: high; file: plugins/hexaemeron/skills/protasis/scripts/protasis.py; finding: The step cap stopped scanning and discarded the fact that it had, so five hundred sound steps followed by a broken one returned clean at exit 0. The cap turned a broken runbook into a passing one.; status: fixed in bf4fd43

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24, plugin suite 332/332.

The finding came from probing the risk register rather than reading the code.
The register's third entry says a checker that finds nothing and exits 0 is
worse than no checker, and names an empty step set as the way in. P003 already
covered that door. The cap was the other one, and it was open. The fix keeps the
bound, because a document from outside the process gets bounded, and returns the
dropped count so P004 can report what went unchecked.

Two more register entries were probed and are sound. Regex cost is not a denial
surface: a 200,000 character step heading finishes in 0.7 ms and an unterminated
allow comment of the same size in 2.4 ms, both linear enough at a 2 MiB read cap.
Path handling refuses anything that is not a regular file, which covers device
and directory arguments, and the argument list is documented as the trust
boundary rather than pretended away.

Also worth recording from this step, though it was caught by the suite rather
than by the audit: P002 was first written to search the whole step for a command,
which lets any field carrying backticks answer for the exit. Since
`**Files.** `a.py`` is close to universal, the code would never have fired on a
real runbook. It now searches the exit's own field span. Both that fix and this
round's fix are guarded by tests seen to fail on the unfixed tree.

Leads not pursued: the README states "124 controller, contract and practice-check
tests, 55 lint tests" while the plugin suite ran 303 before this run and 332
after. That prose was already stale by roughly 180 tests before this run touched
it, no test derives it, and correcting it is outside what this step asks for.

## Protasis discipline cores, step 3, round 2 -- 2026-08-20

Reviewed: the checker with round 1's fix applied, probing what that fix might
have exposed rather than re-reading it.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R2-01; severity: high; file: plugins/hexaemeron/skills/protasis/scripts/protasis.py; finding: The last tracked step's body ran to the next non-step heading, so where the cap had dropped steps their fields sat inside that span and donated themselves upward. A broken step at the cap boundary passed while missing five of six fields.; status: fixed in 6a8bca8

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24, plugin suite 333/333.

How it surfaced. Round 1 removed an early break, so the question for this round
was what that changed downstream. Four probes: eight times the cap finishes in
16 ms and reports P004 exactly once rather than once per dropped step; a
document exactly at the cap stays clean; one step past it reports; and a broken
step inside the cap alongside overflow reported no P001 at all, which is where
it came apart. Shrinking the cap to two steps isolated it in one document.

The defect predates round 1. The old code broke out of the scan at the cap and
produced the same span, so the donation happened identically; round 1 only made
the boundary reachable by a probe. Recorded that way rather than as a regression,
because a reader deciding whether to trust earlier releases needs to know it was
always there.

Leads not pursued: none new. The README test-count staleness from round 1 still
stands and is still outside this step.

## Protasis discipline cores, step 3, round 3 -- 2026-08-20

Reviewed: the twice-fixed checker, probing what round 2's boundary change might
have broken.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R3-01; severity: high; file: plugins/hexaemeron/skills/protasis/scripts/protasis.py; finding: Round 2 let any same-level heading end the last step, and that scan does not track code fences, so a runbook quoting a step heading inside an example truncated its own last step and reported the fields below it missing.; status: fixed in 8cb3ef9

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24, plugin suite 334/334.

Six probes this round: an h1 between steps, an h3 inside a step, a fenced step
heading inside an exit, a last step that genuinely ends the document, a
suppressed step at the cap boundary, and a step whose six fields are all present
but empty. The third came apart. The sixth reports P002 and is correct: a field
with no text names no command, and the module documents that it reads presence
rather than quality.

Unlike round 2's finding, this one is a regression from the round before it, and
the entry says so. Round 2 widened the boundary rule without carrying over the
fence tracking the step scan has always had. The irony is worth keeping: the
document that broke it is this skill's own contract, which quotes a step heading
a few lines from where it states the schema.

Leads not pursued: none new.

## Protasis discipline cores, step 3, round 4 -- 2026-08-20

Reviewed: the thrice-fixed checker, probing fence and line-ending variants.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R4-01; severity: medium; file: plugins/hexaemeron/skills/protasis/scripts/protasis.py; finding: Fences matched backticks only, so a runbook using tilde fences had its examples read as content: a quoted step heading became a step with no fields and the document collected six findings it had not earned.; status: fixed in 2226614

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24, plugin suite 337/337.

Eight probes: tilde fences, backticks nested inside a tilde block, a four
backtick run, an indented fence, a field label inside a fence, CRLF line
endings, trailing spaces on a step heading, and a file with no final newline.
Only the tilde case came apart, and it is the one that produces findings a
document has not earned. A checker that cries wolf gets switched off, so this
was worth a round even at medium.

The fix carries a second change the previous three rounds argued for. Fence
state was tracked separately at three sites and one of them shipped without any
tracking, which was round 3's finding; the tilde gap then had to be fixed at all
three. They now share one generator. The duplication was the defect rather than
the place it happened to surface, and rounds 3 and 4 are the same underlying
fault twice.

Leads not pursued: full CommonMark fence semantics remain unimplemented, and
deliberately. Info strings, fences indented past three spaces and fences inside
list items are all legal and all unhandled. The contract states the runbook
shape and the study traded tolerance of an unconventional shape away on purpose.
What was fixed here is the case a real runbook in this repository would hit.

## Protasis discipline cores, step 3, round 5 -- 2026-08-20

Reviewed: the checker after round 4's fix and the refactor that came with it.

No findings.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24, plugin suite 337/337.

The refactor moved three separate fence trackers onto one generator, which is
the kind of change that pays for a round of its own. Six probes: cost at 400 and
3000 steps, the exit span still bounding correctly with a later field carrying
backticks, an allow comment inside a fence, a document made only of fences, and
the three real runbook-shaped documents this repository now holds. Cost is 3 ms
and 7 ms, so replacing the early break with a full scan did not turn the check
quadratic. Everything else answered as it should.

Four rounds found four things and the fifth found nothing, which is where the
loop closes. Worth naming what the four had in common: every one was the checker
reporting a verdict it had not earned. Two said clean over a broken document, one
truncated a document and blamed it for the missing fields, one invented findings
against a document that used a legal fence. None was a crash, and none would have
been caught by reading the diff. They came from asking what the code would say
about a document built to embarrass it.

## Protasis discipline cores, step 4, round 1 -- 2026-08-20

Reviewed: the ledger row, the frontmatter version, and the demo path, by
recomputing every claim rather than reading it.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R1-01; severity: low; file: plugins/hexaemeron/skills/protasis/EVOLUTION.md; finding: The row claimed 37 cases where the file holds 34. The inflated count came from reading a subTest loop as six cases where unittest reports one. A ledger is what a stranger reads instead of running the suite.; status: fixed in cb14cd3

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24 including all seven
evolution-contract checks, plugin suite 337/337, imprimatur 100.0 on both files.

What was recomputed. The header digest against the four-field canonical line;
exactly one new row for this run; the evolution axis holding generation and epoch
while incrementing evolution; the new digest differing from the row before it;
the frontmatter version matching the ledger; the twelve study items the row
claims actually present in the contract; all five finding codes present in the
module; and the case count, which is where it came apart. The digest was then
rechecked after the correction, since editing a row near a hashed block invites
exactly that mistake.

The frontier does not close mature, and the reason is on the record rather than
asserted. The runbook schema is executable and the study contract beside it is
not, and step 2 widened that gap from seven items to twelve. This run's own study
named the study check as a non-goal and a successor before any of it was built,
so the next job is evidenced rather than invented to keep a ledger open.

Leads not pursued: the README test-count staleness first logged in step 3 round 1
still stands.

## Protasis discipline cores, step 4, round 2 -- 2026-08-20

Reviewed: the corrected ledger row, every number in it recomputed.

No findings.

The three bundled lints ran against the changed tree and each exited 0:
`phylax`, `ephoros`, `hypomnema`. Root suite 24/24, plugin suite 337/337.

Seven claims recomputed and all seven hold: 34 cases against a suite that
reports 34, seven study items becoming twelve against twelve numbered items in
the contract, five codes against P000 through P004 in the module, a sixth step
field against six labels in the schema block, and five audit rounds with four
faults against five logged round headings and four finding rows in this run's own
sections.

Two of this round's first measurements were wrong, and in the same way: one read
the header line because it also contains the version string, and one counted
`S3-R` finding ids across the whole file, catching entries from earlier runs.
Both were probe faults rather than content faults, and both are worth recording,
because a probe that reads the wrong line reports either a false pass or a false
finding depending on which way it lands. This run has now had three of them: two
here and the shell quoting that fed three lint tools one concatenated path in
step 1. The probe checks its own premise, or its verdict is worth nothing.

Six findings across the run, one of them in the ledger and four in the checker,
and every one was a verdict stated with more confidence than the evidence carried.
None was a crash.

# Run: record each Kronos ranking pass in a durable scoreboard

## Step 1, round 1 -- 2026-08-20

Two Markdown documents, no code. The three bundled lints ran against both
files, passed as separate arguments rather than one concatenated string, which
is the shell-quoting fault the previous run recorded in this file.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

phylax exit 0, ephoros exit 0, hypomnema exit 0.

The look the lints cannot do, against the study's risk register: the register's
concerns are all about the writer step 2 builds, so none of them can be
exercised by two documents. What a document can get wrong is a false claim, so
the diff was checked against the tree instead. The frontier digest quoted in
both files matches `plugins/hexaemeron/skills/kronos/EVOLUTION.md` byte for
byte; the cited test at `tests/test_evolution_contract.py:111` is the digest
recomputation the study says it is; the four axis caps match `SKILL.md` lines
70 to 73. The diff carries no credential and no account data, which the
marketplace preflight forbids shipping.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-20

phylax exit 0, ephoros exit 0, hypomnema exit 0. The lints found nothing, and
both findings below came from walking the study's risk register against the
code, one boundary at a time.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: medium; file: plugins/hexaemeron/skills/kronos/scripts/kronos.py; finding: `.kronos/` occupied by a symlink was written through, putting the scoreboard and its `*` gitignore in a directory the caller never named; status: fixed in 885bcb6
- id: S2-R1-02; severity: low; file: plugins/hexaemeron/skills/kronos/scripts/kronos.py; finding: the `run` field was stored with no type check, so any JSON value reached the record; status: fixed in 885bcb6

S2-R1-01 was reproduced before it was believed: a symlinked `.kronos` pointing
at an empty directory, one `record` call, and both files appeared in the target.
The study's boundary list states the control it needed, "refuse anything that is
not a real directory", so this was a promise the code had not kept. Where the
link points somewhere git watches, the `*` gitignore hides whatever sits beside
it and the scoreboard dirties the tree, which is the failure option C was
rejected for.

The first fix was wrong and the guard test caught it. Checking
`scoreboard.parent` after `Path(...).resolve()` never sees a symlink, because
resolve follows it: the check ran against the target directory and passed. The
mechanism was the resolve, not the check, so the guard now runs against the path
as the caller gave it, and covers a symlinked scoreboard file as well as a
symlinked directory.

Four guard cases were run against the tree without the fix and all four failed,
then against the fixed tree and all four passed.

Leads not pursued: the scoreboard read cap of 16 MiB refuses an append once a
file passes it, which stops recording rather than losing a line. Accepted: the
cap is stated in the source, and 16 MiB of ranking passes is far past any real
loop.

## Step 2, round 2 -- 2026-08-20

Against the tree with round 1's fixes applied. phylax exit 0, ephoros exit 0,
hypomnema exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The look went after what round 1's fix could have broken and what it did not
cover. Moving the K010 check ahead of the stdin read does not weaken the
append-nothing property, since it refuses earlier rather than later. `show` has
no such check, which is correct: it only reads, and reading through a link the
caller named writes nothing anywhere.

One property was assumed in round 1 and checked here instead. A basis holding a
newline could have split one record across two lines and broken the file for
every later read. It does not: `json.dumps` escapes it, the file kept one line,
and `show` renders the text across two lines without the record changing.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-20

phylax exit 0, ephoros exit 0, hypomnema exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: medium; file: plugins/hexaemeron/skills/kronos/SKILL.md; finding: step 4 recorded the pass before Fiat was invoked, so the run link the record exists to carry could never be set; status: fixed in 251eb45
- id: S3-R1-02; severity: low; file: plugins/hexaemeron/skills/kronos/SKILL.md; finding: a refusal was documented for a `total` field the skill never documented as a field; status: fixed in 251eb45

The ledger row was checked by hand rather than trusted to the suite that also
checks it: the header names one version with the row, the axis arithmetic moves
generation alone, the recomputed digest matches the row, the generation retains
the prior revision and digest byte for byte, the status stays mature with no
next job, and SKILL.md's frontmatter agrees with the header.

S3-R1-01 came from reading the new text against the field it introduced. The
wishlist entry asks for a link to the Fiat run a pass launched, and step 4 ran
before any run existed, so every line would have carried a null. Both fixes have
guards that were run against the unfixed SKILL.md first and failed there.

Leads not pursued: none.

## Step 3, round 2 -- 2026-08-20

Against the tree with round 1's fixes applied. phylax exit 0, ephoros exit 0,
hypomnema exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The demo path was run again after the wiring changed, this time with `run`
named and a stated `total` supplied, which is what step 6 now asks for. Two
passes, drift marked on the unchanged held job, and the run carried through to
the rendered output.

Leads not pursued: phase-only mode narrows step 8 to the six phase ledgers and
says nothing about the scoreboard read-back that step 8 also carries. Accepted:
the section says steps 3 to 7 are unchanged and then narrows step 8's scope
rather than replacing its instructions, so the read-back is inherited. Worth a
sentence if a later reader trips on it, but writing one now would restate step 8
in a second place, which is how the two drift.

# Run: park a blocked Kronos job instead of stalling the loop

## Step 1, round 1 -- 2026-08-20

Two Markdown documents, no code. phylax exit 0, ephoros exit 0, hypomnema
exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The risk register describes a lane step 2 has not built, so the look went at the
documents' claims instead. The study leans on K006 refusing a selection the
tie-break did not pick, and that refusal is at `kronos.py:232` reading as
described, which matters because option A is rejected on it. The quoted stop
text appears in `SKILL.md` byte for byte. The halt-record shape cited from
`hexctl.py` is the one at `cmd_halt`. The frontier digest matches the ledger.
The diff carries no credential and no account data.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-20

phylax exit 0, ephoros exit 0, hypomnema exit 0. Both findings came from walking
the study's risk register against the code.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: low; file: plugins/hexaemeron/skills/kronos/scripts/kronos.py; finding: a halt reason carrying a newline printed at the left margin, so it could forge the summary line telling a reader whether anything still stands; status: fixed in 00cf4d2
- id: S2-R1-02; severity: low; file: plugins/hexaemeron/tests/test_kronos_scoreboard.py; finding: nothing held the record format backward compatible, so a scoreboard written under v0.3.0 could stop reading without a test noticing; status: fixed in 00cf4d2

S2-R1-01 was reproduced before it was believed: a park whose reason held a
newline and the text `0 park(s) standing; the loop is not complete` printed that
line at the margin, under the real summary saying 1. The exit code stayed 3
throughout, so the mechanical gate never lied; the report a person reads did.
The reason is stored byte for byte by requirement, so the display indents
continuation lines rather than editing what was recorded.

The replay was checked against the register's other cases: park after unpark, a
second park for a parked skill, and an unpark with nothing standing all resolve
to something defined and tested. A stale park still blocks completion, and an
unreadable ledger reads as unknown rather than as cleared, which is the one that
would have quietly emptied the lane.

Leads not pursued: a reason may still carry terminal control characters, which
render as whatever the terminal does with them. Accepted: stripping them on
display would make the printed reason differ from the recorded one, which is the
property the verbatim requirement exists to protect, and the reason arrives from
a Fiat halt inside the same loop rather than from outside it.

## Step 2, round 2 -- 2026-08-20

Against the tree with round 1's fixes applied. phylax exit 0, ephoros exit 0,
hypomnema exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The look went after what round 1's fix could have broken. The forged line now
sits indented under its park and the real summary still reads 1, an ordinary
single-line reason renders exactly as before, and a second park in the same file
prints its own reason line rather than folding into the first.

One property the fix touches without being about it: the reason on disk is
unchanged, so the display change cannot drift from the record. The stored value
is read back by the byte-for-byte case and the newline case, both of which read
the file rather than the output.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-20

phylax exit 0, ephoros exit 0, hypomnema exit 0. This step resumed after a halt:
the root README had been replaced in this checkout by another process, taking
`tests/test_marketplace_prose.py` red, and the file's owner restored it. Nothing
in this run touched it.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: medium; file: plugins/hexaemeron/skills/kronos/SKILL.md; finding: phase-only mode restates its own stop condition, and that restatement omitted the park clause, so a loop following it could finish over a standing park; status: fixed in 4bc12a9
- id: S3-R1-02; severity: low; file: plugins/hexaemeron/skills/kronos/scripts/kronos.py; finding: `show` dropped the parked flag the record carries, so a parked candidate outscoring the selected one read as a contradiction of the tie-break; status: fixed in 4bc12a9

S3-R1-02 surfaced in the demo path itself: protasis printed at 81 above elenchus
at 60 with nothing saying why the lower score won. The record held the flag all
along; only the display lost it.

S3-R1-01 came from reading the phase-only section against the new stop text.
Inheritance was the answer to a similar gap in the previous run, and it is not
the answer here: this section writes its own stopping rule out in full, so a
clause missing from it is missing, not inherited.

The ledger row was checked by hand as well as by the suite: the header names one
version with the row, generation moves alone, the recomputed digest matches, the
prior revision and digest are retained byte for byte, the status stays mature
with no next job, and the frontmatter agrees.

Leads not pursued: none.

## Step 3, round 2 -- 2026-08-20

Against the tree with round 1's fixes applied. phylax exit 0, ephoros exit 0,
hypomnema exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The look went after what the new mark could have broken. With nothing parked the
selected mark still stands alone, and a `kronos-v0.3.0` line carrying no parked
field at all renders and exits 0, because the flag is read with `get` rather than
indexed. That second case is the one that would have broken every scoreboard
written before this run.

Leads not pursued: none.

# Run: add a rank-only reporting mode to Kronos

## Step 1, round 1 -- 2026-08-20

Two Markdown documents, no code. phylax exit 0, ephoros exit 0, hypomnema
exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The register describes fields step 2 has not added, so the look went at the
claims the study rests on. The quoted description line is in `SKILL.md` byte for
byte. `PASS_FIELDS` and `MODES` hold what the study says they hold, and `run` is
already read with `get`, which is what makes a pass with no run representable
today and indistinguishable tomorrow. The field-drift guard the runbook plans
around exists. Step 2's ungoverned-report sentence is in the loop as quoted. The
frontier digest matches the ledger, and the diff carries no credential.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-20

phylax exit 0, ephoros exit 0, hypomnema exit 0. The finding came from walking
the study's risk register against the code.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: low; file: plugins/hexaemeron/skills/kronos/scripts/kronos.py; finding: a skill could be recorded as a scored candidate and reported ungoverned in the same pass, and `show` printed both; status: fixed in aaf172a

Reproduced before it was believed: a pass naming protasis as a candidate scored
from its ledger and in `ungoverned` as having none recorded cleanly, and the
rendered output asserted each. Ungoverned means no ledger, and the held-job hash
on a scored candidate is computed out of one, so the two cannot both hold.

The register's other entries were checked and hold. The `rank_only` and `run`
contradiction is refused on the combination rather than on either alone, and a
pass carrying `rank_only` beside an explicit null run is still accepted, since
a null run is the absence the flag asserts. Both fields are read with a default
in `show`, held by a case over a `v0.4.0`-shaped line, which is the fault this
audit found twice in the previous run.

Leads not pursued: the ungoverned list is not deduplicated, so a name repeated
in it prints twice. Accepted: it is a report of what the walk found, repetition
in it is the caller's own output rather than a contradiction, and refusing it
would be a rule about tidiness rather than about meaning.

## Step 2, round 2 -- 2026-08-20

Against the tree with round 1's fix applied. phylax exit 0, ephoros exit 0,
hypomnema exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The look went after what the new refusal could have caught by mistake. An
ungoverned list naming skills that are not candidates records as before, an
empty list records, and a rank-only pass carrying an explicit null run records,
which is the case a refusal keyed on the field's presence rather than its value
would have broken.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-20

phylax exit 0, ephoros exit 0, hypomnema exit 0. Both findings came from reading
the new section against the sections it refers to.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: low; file: plugins/hexaemeron/skills/kronos/SKILL.md; finding: the section said to record the pass, then said steps 5 to 8 do not happen, and step 6 is where recording lives; status: fixed in 7a03c5f
- id: S3-R1-02; severity: low; file: plugins/hexaemeron/skills/kronos/SKILL.md; finding: it asked for standing parks in the report without saying `parked` exits 3 whenever one stands, and the parked section explains that 3 only in terms of step 8; status: fixed in 7a03c5f

Neither is a code fault and both would have cost a reader a wrong action: the
first dropping the record, the second reading a normal exit as a failure. One
guard covers the section's required content, run against the unfixed text first.

The ledger row was checked by hand as well as by the suite: header and row name
one version, generation moves alone, the recomputed digest matches, the prior
revision and digest are retained byte for byte, the status stays mature with no
next job, and the frontmatter agrees. The description change is carried by
`tests/test_portable_skills.py`, which requires a non-empty description and
passes over the edited one.

Leads not pursued: none.

## Step 3, round 2 -- 2026-08-20

Against the tree with round 1's fixes applied. phylax exit 0, ephoros exit 0,
hypomnema exit 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The look went at whether the amended text broke the guards that were already
holding it, and at whether the three shipped mechanisms compose. All four prose
guards pass together: the field list, the phase-only park clause, the rank-only
section's own content, and the one requiring step 6 rather than step 4 to carry
the loop's recording, which the new wording could have moved.

The three mechanisms were then run against each other in one pass: a phase-only
rank-only ranking with a parked candidate scoring above the selection, an
ungoverned skill, and `parked` reporting the block. The parked candidate carried
its `P` and stayed out of selection, the pass rendered as `(rank-only)`, and
`parked` exited 3, which the amended section now says means a park stands rather
than a failure.

Leads not pursued: none.

## Berean from its Commons specification, step 1, round 1 -- 2026-08-20

Scope: `496f7a1..fe36843`, the plugin scaffold and its marketplace landing.
The Solidity suite is waived for this run: the delivery is Python, JSON and
Markdown with no contracts in any step. The mechanical part ran phylax,
ephoros and hypomnema over the changed trees, all exit 0, with the root
suite (34, at 13 plugins) and the berean suite (5) green on the tracked
tree, which also puts every new shipped document through the in-process
imprimatur gate.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

The look beyond the lints checked the risk register's step 1 concerns: the
frontier sentence is byte-identical across the eight berean surfaces and the
root status row; the ledger digest reproduces from the header fields; the
three manifests and the openai interface carry one description; the portable
entry's links resolve at their depth; the Commons section moves berean from
the remaining list without rewording the janus entry; and the preserved
specification differs from the upload only in its header block, which
`docs/design.md` records verbatim.

Leads not pursued: brevitas B011 flags the runtime contract's selection and
capability tables (1x3 and 5x2); the shipped template in every existing
plugin carries the same shapes and the same flags, so the tables stay with
the house form. Nothing else.

## Berean from its Commons specification, step 2, round 1 -- 2026-08-20

Scope: `c3bec0c..4438d2e`, the corpus and citation core. The suite waiver
stands; the mechanical part ran phylax, ephoros and hypomnema over the
changed trees, all exit 0, with the root suite (34) and berean suite (59 at
review, 61 after fixes) green.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: B2-R1-01; severity: medium; file: `plugins/berean/scripts/berean_lib/jsonio.py`; finding: NaN and Infinity reach `json.loads` through `parse_constant`, not `parse_float`, so a document carrying them passed the reader built to refuse non-finite numbers.; status: fixed in `c8c72d3`
- id: B2-R1-02; severity: low; file: `plugins/berean/scripts/berean_lib/corpus.py`; finding: A pinned path swapped for a symlink between the walk and the drift read raised out of `verify` as a usage error instead of failing a named check.; status: fixed in `c8c72d3`

The look beyond the lints traced the risk register's concerns through the
new code: traversal and backslash refusals sit in one place and both
builders go through it; the staged write cannot leave a half manifest that
later verifies, and a crashed staging file inside the corpus is itself a
refusal; verification is set equality, so an unpinned extra file fails
rather than passing as a superset; and citation digest and display text are
checked separately so neither can vouch for the other.

Leads not pursued: none.

## Berean from its Commons specification, step 2, round 2 -- 2026-08-20

Scope: the step 2 tree with `c8c72d3` applied. Both fixes re-reviewed
against the current tree: the constant hook refuses all three JSON
constants with a guard test per spelling, and the drift loop reports a
swapped symlink as a named `corpus-bytes` failure with the refusal in its
detail. Lints phylax, ephoros and hypomnema exit 0; root suite 34 and
berean suite 61 green.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

Leads not pursued: none.

## Berean from its Commons specification, step 3, round 1 -- 2026-08-20

Scope: `d1df164..cf9d9d2`, answer records, source classes and block-bound
reads. The suite waiver stands; phylax, ephoros and hypomnema exit 0, root
suite 34 and berean suite 95 green at review, 96 after the fix.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: B3-R1-01; severity: low; file: `plugins/berean/scripts/berean_lib/answers.py`; finding: Citation ids and read ids lived in separate namespaces, so one id naming both left a calculation's evidence reference resolving to two artefacts.; status: fixed in `2883291`
- id: B3-R1-02; severity: note; file: `plugins/berean/scripts/berean_lib/answers.py`; finding: A dead constant and an unused import survived drafting.; status: fixed in `2883291`

The look traced the register's step 3 concerns: request keys are recomputed
rather than trusted, an outcome is exactly a result or an error, reads files
must arrive sorted and unique so one spelling exists, refusals are enforced
empty, evidence nothing cites is refused, and the per-class evidence rules
hold user-supplied facts to no artefact at all.

Leads not pursued: none.

## Berean from its Commons specification, step 3, round 2 -- 2026-08-20

Scope: the step 3 tree with `2883291` applied. The collision refusal
re-reviewed against the current tree with its guard test; nothing new
surfaced. Lints phylax, ephoros and hypomnema exit 0; root suite 34 and
berean suite 96 green.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

Leads not pursued: none.

## Berean from its Commons specification, step 4, round 1 -- 2026-08-20

Scope: `9ea6e4e..2a68fc7`, release manifests, verifier gates and promotion
records. The suite waiver stands; phylax, ephoros and hypomnema exit 0,
root suite 34 and berean suite 121 green at review, 124 after fixes.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: B4-R1-01; severity: medium; file: `plugins/berean/scripts/berean_lib/release.py`; finding: The contract allowlist scanned only top-level string params, so an address nested in a filter object (the `eth_getLogs` shape) escaped the gate.; status: fixed in `464bc6a`
- id: B4-R1-02; severity: low; file: `plugins/berean/scripts/berean_lib/promote.py`; finding: `promote` digested the report bytes but parsed a second read of the file, so a swap between the two reads validated content the digest never covered.; status: fixed in `464bc6a`

The look traced the register through the new surface: the release digest
is built from named identity fields; the promotion chain replays whole and
refuses gaps, reorders and forged counts; a crashed staging file inside
the release fails the components gate rather than hiding; the report binds
by corpus, cases and answers digests rather than the release digest, which
would have been a cycle; and every gate has a committed breach that fails
it by name.

Leads not pursued: none.

## Berean from its Commons specification, step 4, round 2 -- 2026-08-20

Scope: the step 4 tree with `464bc6a` applied. The params walk and the
digested-bytes parse re-reviewed with their guard tests; nothing new
surfaced. Lints exit 0; root suite 34 and berean suite 124 green.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

Leads not pursued: none.

## Berean from its Commons specification, step 5, round 1 -- 2026-08-20

Scope: `1ac41c4..f5a5230`, the evaluation corpus and its graders. The suite
waiver stands; phylax, ephoros and hypomnema exit 0, root suite 34 and
berean suite 142 green at review, 143 after the fix.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: B5-R1-01; severity: medium; file: `plugins/berean/scripts/berean_lib/promote.py`; finding: Promotion checked the pinned report's digests and counts but never graded, so a report claiming a clean pass would promote a release whose cases fail when graded today.; status: fixed in `df5edc7`

The look traced the register through the graders: cases embed the answers
they grade so broken answers never join a release's pinned set; the run
parses the same bytes it digested; injection cases must name forbidden
content and a boundary claim without a refusal expectation is refused;
the rejected grader passes only on a named checker refusal, so the
adversarial corpus cannot pass by accident.

Leads not pursued: forbidden-content scanning covers sentence texts and
not citation display text, deliberately, because a citation quoting a
poisoned document is the disclosure the format wants; recorded in the
grader beside the scan.

## Berean from its Commons specification, step 5, round 2 -- 2026-08-20

Scope: the step 5 tree with `df5edc7` applied. The re-grading promotion
re-reviewed with its guard test; the lazy import that breaks the module
cycle is one-directional and inside the function. Lints exit 0; root
suite 34 and berean suite 143 green.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

Leads not pursued: none.

## Berean from its Commons specification, step 6, round 1 -- 2026-08-20

Scope: `23fcb9a..bdac6a4`, the reference release and the demonstration.
The suite waiver stands; phylax, ephoros and hypomnema exit 0, root suite
34 and berean suite 150 green.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: B6-R1-01; severity: note; file: `plugins/berean/docs/runbook.md`; finding: The runbook's step 6 file list put the README and demo inside the release directory, which the components gate refuses by design; the layout landed with the release under `release/` and the copy did not yet record the correction.; status: fixed in `07772a9`

The look held the reference release to the register: the copied reads are
byte-identical to the Lazarus fixture and the drift test proves it; the
corpus documents state that they are demonstration prose and make no claim
about the live protocol beyond the preserved evidence; the corpus files
carry no rolling marketplace prose, so a frontier refresh cannot move
pinned bytes; the rebuild is deterministic and compared byte for byte; and
the demo's three tamper stages name their refusing gates.

Leads not pursued: none.

## Berean from its Commons specification, step 6, round 2 -- 2026-08-20

Scope: the step 6 tree with `07772a9` applied. The corrected runbook copy
re-read against the layout on disk; nothing new surfaced. Lints exit 0;
root suite 34 and berean suite 150 green; the demo exits 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

# Run: create the janus skill in the Wildcat Commons

## Step 1, round 1 -- 2026-08-20

Non-Solidity round; the security-suite waiver covers the Pashov pair (the step
lands Markdown only). phylax exit 0, ephoros exit 0, hypomnema exit 0 over
`docs/commons/janus.md`, `docs/janus-commons-spec/study.md` and
`docs/janus-commons-spec/runbook.md`.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The look went at the study's risk register. Byte preservation holds:
`sha256sum docs/commons/janus.md` prints the pinned
`8234ee09201927aeb8df34c9068c5c68e9201539057ccffce3d2600dd724c3ed`. Sweep
boundaries hold: the spec's marketplace-context block carries no frontier
line, and nothing fails because `tests/test_shipped_prose_lints.py` skips
`docs/**` while the frontier scans in `tests/test_marketplace_prose.py` walk
only the twelve plugin subtrees; the full root suite ran against this tree,
34 tests, all green. All five `../../plugins/` links in the committed study
resolve from `docs/janus-commons-spec/`. Nothing landed under `plugins/` or
`.agents/`, so the versioning and evolution contracts see no new surface.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-20

Non-Solidity round under the run's suite waiver. phylax exit 0, ephoros exit
0, hypomnema exit 0 over `README.md`, the only file this step changes.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The look went at the study's remaining risks. The README edit adds two lines
inside the Commons bullet and moves nothing else, so every exact sentence and
section ordering `tests/test_marketplace_prose.py` asserts still holds; the
full root suite ran against this tree, 34 tests, all green. The new pointer
resolves: `docs/commons/janus.md` exists on this branch at the pinned digest.
The edited README scores 100/100 under imprimatur with no defects.

Leads not pursued: none.

# Run: build the Janus hook-conformance suite against the Wildcat v2.5 hooks

## Step 1, round 1 -- 2026-08-20

Scaffold step. The security_suite receipt lists the bundled Pashov ids; this
round applies them proportionately to what the step actually ships.
`solidity-auditor` was run over the step's Solidity, its own exclude pattern
skipping `*.t.sol`. The two remaining files are `harness/src/Vm.sol` (a
cheatcode interface declaration with no logic) and `harness/src/JanusBase.sol`
(an abstract test base of pure `require` assertions). Neither holds state,
makes an external call, moves value, uses assembly, delegatecall, payable, or
selfdestruct. `foundry.toml` leaves `ffi` unset (default false) and scopes
`fs_permissions` to read `./manifests` and `./examples` and read-write `./out`.

`x-ray` and `fizz` are deferred with reason, not run: x-ray produces a
pre-audit readiness report over a protocol's entry points, state transitions
and value flow, and this step ships none of those; fizz builds an invariant
fuzz suite over shipped contracts, and the harness gates and invariants arrive
in steps 4 and 5. Both apply there, against the Wildcat host model, the gate
engine and the hostile hooks, and are recorded when they run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The risk-register look went at the one boundary this step opens, the harness
filesystem and cheatcode surface (phylax). It is closed: no `ffi`, no network,
`fs_permissions` scoped to the plugin's own directories, no absolute paths.
`forge build` and `forge test` pass; the repository packaging suite passes at
thirteen plugins; the Janus Python suite passes; every shipped document lints
100/100. One `forge lint` advisory remains, `screaming-snake-case-const` on the
`vm` constant in `JanusBase.sol`; it is kept lowercase deliberately, matching
the ecosystem-standard `forge-std` cheatcode handle, and is not a defect.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-20

Python and JSON step: the JSON manifest schema, the stdlib validator, and its
fixtures. No Solidity ships, so `x-ray` and `solidity-auditor` have nothing to
review this step; the review surface is the validator, an untrusted-JSON
boundary. The three bundled lints ran clean over the changed files (phylax 0,
ephoros 0, hypomnema 0), and the validator was read against the risk register.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: medium; file: plugins/janus/scripts/janus.py; finding: The validator scanned effect free-text for wildcards but did not enforce the `scope` and `kind` enumerations the schema documents, so a manifest with an unrecognised storage scope or call kind validated. Gate 1 promises effects are enumerated; an unrecognised enum value slipping through is a fail-open hole.; status: fixed in ae61738509855e47ba687299fb0705e609d2f478

The fix adds code J015: an unrecognised `scope` or `kind` is rejected, fail
closed, with a fixture. The validator otherwise fails closed correctly: it uses
`json.load` with no `eval` or code execution, raises on the first broken rule,
and returns invalid on any parse or rule failure. Gate 1's "omitted list is
forbidden" is enforced through the required-keys check (J006) and the non-list
check (J008); wildcards are refused in every free-text field (J009).

Leads not pursued: none.

## Step 2, round 2 -- 2026-08-20

Against the tree with round 1's fix applied. The bundled lints re-ran clean
(phylax 0), the Janus validator suite passes with the J015 fixture, and the
repository suite passes. The look checked that the enum enforcement did not
narrow a legitimate manifest: the honest Wildcat manifest still validates, and
the J015 path fires only on a scope or kind outside the documented sets.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-20

Solidity step shipping the state-delta recorder, the trust root of the suite,
where a missed effect is a false pass. The vendored `solidity-auditor` was run
over `StateDeltaRecorder.sol`, `HostAdapter.sol` and `Vm.sol`, focused on the
one property that matters: the recorder must never miss an effect that occurred.
`x-ray` and `fizz` are deferred with reason: x-ray produces a protocol
readiness report and this ships a test-harness library, and fizz's invariant
suite lands in step 5 with the gate engine and the hostile hooks.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | plugins/janus/harness/src/StateDeltaRecorder.sol | CREATE and SELFDESTRUCT account accesses carry a target and moved value, and the recorder dropped both, so a hook could move value invisibly by deploying with an endowment or sweeping its balance. The one false-pass vector. | fixed in 13dfd3f546aa8db06a42025ee7383dbdd1b2112b |
| S3-R1-02 | low | plugins/janus/harness/src/StateDeltaRecorder.sol | A second `_beginRecording` while one was open reset Foundry's state-diff buffer and silently dropped everything recorded so far; only the missing-begin direction failed closed. | fixed in 13dfd3f546aa8db06a42025ee7383dbdd1b2112b |
| S3-R1-03 | low | plugins/janus/harness/src/StateDeltaRecorder.sol | `_valueMoved` summed delegatecall value, which is inherited from the enclosing call and double-counts. An over-count is a false-fail rather than a false-pass, but it made the measure unreliable. | fixed in 13dfd3f546aa8db06a42025ee7383dbdd1b2112b |

The auditor verified as sound, and this review confirms: the two-pass count and
fill predicates are byte-identical so the index counters cannot over- or
under-flow; reverted accesses are correctly dropped as non-persisted; the flat
access array means nesting and reentrant frames cannot hide a write or call;
the taken flag plus the RecordingNotStarted revert prevent a silent clean
delta; and the Vm struct and enum layout matches the Foundry cheatcode ABI. One
documented assumption (L-2): correctness of the drop-reverted logic rests on
Foundry never marking a persisted effect reverted, which errs toward false-fail
rather than false-pass. Attribution of an effect to the hook and comparison
against a manifest are the gate engine's job, not the recorder's.

Leads not pursued: none.

## Step 3, round 2 -- 2026-08-20

Against the tree with round 1's fixes applied. The three fixes are additive and
narrow: `_reachesAccount` now includes create and selfdestruct, `_beginRecording`
guards the already-open case, and `_valueMoved` sums only value-moving kinds.
Re-review confirmed the count and fill predicates stayed identical (both now
call `_reachesAccount`), so the index counters remain in bounds, and the new
`_movesValue` filter is applied only in the value sum, not in the calls list, so
no target is dropped. All seven harness tests pass, including the create-endowment
and double-begin cases. The repository and Janus Python suites pass.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

Leads not pursued: none.

## Step 4, round 1 -- 2026-08-20

Solidity step shipping the Wildcat host model, the honest hook, the adapter and
the gate engine, the fidelity core. The vendored `solidity-auditor` reviewed
all five files against two properties: fidelity to the real v2.5 seam, and no
false pass. Fidelity was verified against the checked-out v2-protocol source at
the anchor commit and confirmed on every cited mechanic (the hook call
primitive and its bubble, the value-return `>= 0x40` contract and bounds, the
hook-before-effects ordering and the queueWithdrawal expiry exception, the
global reentrancy guard, and onExecuteWithdrawal never being hook-gated).
`x-ray` and `fizz` are deferred with reason: the harness is not a protocol to
x-ray, and the invariant suite lands in step 5 with the hostile hooks.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | high | plugins/janus/harness/src/JanusHarness.sol | Gate 1 and the value measure attributed a hook's effects by the immediate `accessor`, so they saw only the hook's direct callees. A hook could launder a forbidden call or value movement one hop through a permitted or reachable non-hook accessor and be reported conformant. | fixed in 657c1f1a4746cf0f69ba4eca9e45b056173e5ca1 |
| S4-R1-02 | medium | plugins/janus/harness/src/JanusHarness.sol | `_hookValueMoved` shared the immediate-accessor limitation and did not filter by value-moving kind, so a delegatecall's inherited value was double-counted. | fixed in 657c1f1a4746cf0f69ba4eca9e45b056173e5ca1 |
| S4-R1-03 | medium | plugins/janus/harness/src/JanusHarness.sol | Honest-path gates could pass vacuously on an empty or reverted delta; nothing forced a drive expected to have effects to have produced any. | fixed in 657c1f1a4746cf0f69ba4eca9e45b056173e5ca1 |

The fix attributes effects by the transitive closure of the hook's causal
subtree, iterated to a fixpoint over the recorded (accessor, target) pairs, and
a new test launders a call through an allowed forwarder to show gate 1 now
catches it. The auditor confirmed `_drive`'s revert handling sound (a caught,
fully-reverted action yields an effect-free delta and a conserved value
snapshot, so a reverting hook is never mis-attributed effects). One documented
fidelity note (low): the model's setAPR omits the market's own
reserve-ratio-versus-liquidity reverts, which guard the returned value
independently of hook honesty and cannot pass a hook here that the real market
would reject on the seam.

Leads not pursued: none.

## Step 4, round 2 -- 2026-08-20

Against the tree with round 1's fixes applied. The transitive attribution is a
strict strengthening: the honest hook makes no calls, so its closure stays
empty and it still clears gate 1; the laundering test confirms a forbidden call
one hop past an allowed forwarder is now caught. The re-review checked the
fixpoint terminates (it only ever sets bits true, bounded by the call count)
and that the value sum's new kind filter does not drop a real Call or Create
value. All fifteen harness tests pass, and the repository and Janus Python
suites pass.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

Leads not pursued: none.

## Step 5, round 1 -- 2026-08-20

Solidity step shipping the five hostile reference hooks and the completed gate
engine. This is the round where invariant fuzzing applies: `fizz`'s stateful
approach is realised as a Foundry invariant that keeps the reentry hook in the
loop over 2048 calls. The vendored `solidity-auditor` reviewed the hostile
hooks, the engine, and the tests for two properties: no false pass, and each
hostile hook genuinely exercising the class it claims. `x-ray` is deferred with
reason: the harness is not a protocol to profile.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | high | plugins/janus/harness/src/JanusHarness.sol | The accessor-closure attribution swept the host's own base-action calls into the hook's set once a hook merely read host state, wrongly failing a legitimate hook. A false fail, not a false pass, but it broke soundness for real hooks that read host state. | fixed in 1ef5bab6e4b91bb25eeae04654ca0b80a78ee209 |
| S5-R1-02 | medium | plugins/janus/harness/src/JanusHarness.sol | No gate validated storage writes; the storage-mutation hook only exercised the call allowlist, so a hook-caused write to non-permitted storage was ungated. | fixed in 1ef5bab6e4b91bb25eeae04654ca0b80a78ee209 |
| S5-R1-03 | medium | plugins/janus/harness/src/JanusHarness.sol | The findings JSON was concatenated with no escaping, so a field carrying a quote could inject or hide a finding (a detail overrode a gate number in the auditor's proof). | fixed in 1ef5bab6e4b91bb25eeae04654ca0b80a78ee209 |
| S5-R1-04 | low | plugins/janus/harness/test/HostileHooks.t.sol | The reentry invariant asserted only that no deposit landed; a re-entering deposit would revert on a balance underflow even if the guard were removed, so it did not isolate gate 6. | fixed in 1ef5bab6e4b91bb25eeae04654ca0b80a78ee209 |
| S5-R1-05 | low | plugins/janus/harness/test/HostileHooks.t.sol | The stale-auth exit test did not pin the revert reason. | fixed in 1ef5bab6e4b91bb25eeae04654ca0b80a78ee209 |

The depth-subtree attribution resolves the earlier laundering finding and this
round's over-attribution together: it captures the hook's descendant calls
without the host's siblings, and gate 1 now enforces state-changing calls only,
so a read is never an effect. Gate 1 also refuses a hook-caused write to an
account outside its permitted write scopes. The auditor confirmed no false pass
among the five hostile hooks as tested, that the attribution terminates and
does not under-attribute, and that the sequence guard and the invariant target
restriction are correct.

Accepted limitations, recorded rather than fixed:

- The one value-returning hook can return an adversarial but in-bounds rate,
  and no gate constrains the returned value beyond the market's own `<= 10000`
  bound. Constraining it needs a rate-band field the manifest format does not
  carry. Left as a documented gap; a hook cannot exceed the market's bound, so
  the exposure is policy griefing, not an out-of-bound write or value theft.
- The gas gate is exercised on deposit; a hook cheap on deposit and grief-heavy
  on another action is not covered by the hostile set, though the gate itself
  reads a per-action budget and applies to any action driven.

Leads not pursued: the two accepted limitations above, both needing a manifest
extension out of this step's scope.

## Step 5, round 2 -- 2026-08-20

Against the tree with round 1's fixes. The depth-subtree attribution is a
strict correction: the honest hook and the host-reading hook both clear gate 1
now, the laundering and storage-mutation hooks are still caught, and the
injection regression shows an escaped field cannot rewrite another. The
strengthened invariant runs 2048 calls with every block confirmed to be the
reentrancy guard. All 24 harness tests pass, and the repository and Janus
Python suites pass. The two accepted limitations from round 1 stand as
recorded; no new issue surfaced.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

Leads not pursued: the two accepted limitations recorded in round 1.

## Step 6, round 1 -- 2026-08-20

Python, prose and deletion step: the report subcommand, the sample findings,
the README retirement of the anchor, and the removal of the delivered spec. No
Solidity ships, so x-ray and solidity-auditor have nothing to review; the three
bundled lints ran clean over the changed files (phylax 0, ephoros 0, hypomnema
0) and the reporter was read against the risk register.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S6-R1-01; severity: low; file: plugins/janus/scripts/janus.py; finding: A finding field carrying a pipe or a newline would malform the human report's Markdown table, opening a spurious column or splitting the row.; status: fixed in fde7c12cd9f53078548357bccc4714219a99814b

The SARIF output was already safe, serialized through `json.dump` rather than
concatenated. `load_findings` fails closed on a missing key or a non-list
findings value. The clean-run report states the manifest and the sequence
count and explicitly does not claim safety, matching the liveness caveat. The
anchor retirement leaves only historical, point-in-time references to
`docs/commons/janus.md` in the audit log and the two committed run specs, which
the repository treats as records of what was written rather than live links.

Leads not pursued: none.

## Step 6, round 2 -- 2026-08-20

Against the tree with round 1's fix. The cell escaping is confined to the
Markdown renderer and does not touch the SARIF path; a test confirms a pipe in
a field is escaped rather than dropped and the row keeps its four columns. The
Janus Python suite and the repository suite pass. The demo path runs end to
end: forge test, manifest validation, and the report to Markdown and SARIF.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

Leads not pursued: none.
## Scoped entry, step 1, round 1 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over
`plugins tests` and the documented doc set. Horos 183/183 with three expected
failures, root 35/35 with one, verified before this receipt. The look went at
the measurement record rather than the fixtures, since the fixtures were each
run in isolation and print the failure they claim: `out/` as a hard entry at 0
bytes and 0 files, `check` exit 1 beside an ignored build directory, `check`
exit 2 on a descendant, and the root boundary against a fresh tracked scan.
Both findings are the risk register's first class, a record that reads as
more than it measured. Fixes are committed on the step branch rather than a
side branch, because four later steps chain from it.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R1-01; severity: low; file: plugins/horos/tests/benchmark_scope.py; finding: the record's `root` field was `os.path.relpath(root, root)`, always `"."`, so a run against a different root recorded the same value as a run against the repository; status: fixed in b6e7ed2
- id: S1-R1-02; severity: low; file: plugins/horos/tests/benchmark_scope.py; finding: a refused check still reported a median, so `--root plugins/horos` recorded `0.014 ms` beside exit 2; a duration for a check that classified nothing reads as a fast check; status: fixed in b6e7ed2

Leads not pursued: the scaffold test bounds its build-order assertion to a
300-character window after the `Build order:` line, which is a positional
assumption rather than a parse; it fails rather than passes if the line moves,
so it was left as it is.

## Scoped entry, step 1, round 2 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
183/183 with three expected failures, root 35/35 with one, verified before this
receipt. The round audited the tree with round 1's fix applied. The fix is
eleven lines and does one thing on both sides of the record: a refused check
reports a null median and the refusal reason instead of a duration. Re-ran the
benchmark against both a working root and a rootless one to see each branch
taken, and re-ran each fixture in isolation to confirm the fix moved none of
them.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: the benchmark's module docstring still
describes the null-median treatment as the scope side's alone, which is now
under-description rather than error, since both sides carry a status field. It
goes to the prose phase with the rest of this step's wording rather than
opening a third round for a docstring.

## Scoped entry, step 2, round 1 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
188/188 with one expected failure, root 35/35 with one, verified before this
receipt. Three of the five new guards were seen failing on the unfixed
classifier and all eleven pass on the fixed one.

The review went at the paths the change could break rather than the ones it
fixes. The pruning is safe because the dropped entry covers no tracked file, so
the walk has nothing to classify under it, and that was already the behaviour
for a matched directory. Two edges were run rather than reasoned about. An
empty tracked universe, a repository with nothing committed, produces an empty
boundary and zero walked files, which is the fail-open position stated in the
skill. The widened universe still separates the two cases correctly: with
`--include-untracked`, an untracked-but-not-ignored `dist/` binds at one file
while an ignored `out/` stays out, so the flag still means what it says.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: two. A directory that will be dropped is
still walked in full before the drop, so the count that decides it is paid for
and discarded; measured against Metron's rule the full-tree check sits at 55.5
ms against 52.1 ms at step 1 on a tree that also grew, which is noise rather
than a regression, and short-circuiting it would put a universe prefix scan in
front of every directory to save that. Separately, `check .` now names this
file's own classifier source as drifted, because the marker rule excludes it
and its byte count moved: that is the held frontier defect showing itself
during unrelated work, evidence for the marker self-exclusion job rather than
for this one.

## Scoped entry, step 3, round 1 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
188/188 with one expected failure, root 38/38 clean, verified before this
receipt. `check .` exits 0 for the first time in this run, 87 entries, the
evidence copy included, none binding zero tracked files. The guard was seen
failing three ways before it passed: as step 1's expected failure on the
evidence copy, against a hand-removed entry, and on its own source, because a
fixture spelling the generated-marker literal put this guard inside the
boundary. The round then went looking for claims the earlier steps had not
earned, which is where the finding is.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R1-01; severity: medium; file: plugins/horos/docs/scoped-entry/runbook.md; finding: step 2's exit claimed a fresh scan takes this repository's hard entries from 93 to 87. Running the pre-fix classifier over a pristine worktree of the same commit gives 87 with no phantom entry: the 93 came from the maintainer's own checkout, which carries a stale worktree under `.claude/worktrees/` and a `plugins/pandects/out/` directory. The number described a checkout and was written as a property of the repository; status: fixed in 84bb99e, and pull request 256's body corrected in place

Leads not pursued: step 2's commit message carries the same wrong figure and
keeps it. That commit is named in the run's sealed ledger as step 2's
implementation, so rewording it would leave the ledger pointing at a commit
that no longer exists; the corrected account lives in the runbook, the pull
request body and this row. Separately, `plugins/horos/**` has no CI workflow of
its own, so this plugin's 188 tests run locally and nowhere else; adding one is
an ask-first change under this run's boundaries and is recorded on pull request
256 rather than made here.

## Scoped entry, step 3, round 2 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
188/188 with one expected failure, root 38/38 clean, `check .` exit 0, all
verified before this receipt. The round audited the tree with round 1's
correction applied and re-read every remaining quantitative claim in this
run's two documents against the tree rather than against the earlier prose:
the entry count, the census rows, the suite counts, the baseline median, and
the audit references. The 87 figure now carries the checkout it was measured
in. The three mutations that pin the guard ran again in this round as part of
the root suite; the three ways the guard was seen failing belong to the step
rather than to this round, and are recorded there.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Scoped entry, step 4, round 1 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
206/206, root 38/38, verified before this receipt. Two mutations were run
against the committed step before the suite was trusted: making the committed
slice ignore the scope fails five of the nineteen cases, and pruning the
ancestor chain instead of walking it fails six. The round then went at the
control the risk register names rather than at the happy path, and found it
half-built.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R1-01; severity: medium; file: plugins/horos/skills/horos/scripts/horos.py; finding: the escape control only inspected the given path, so a symlink as the final component was refused while a symlink in the middle was not. `git -C` resolves symlinks before answering, so `check bridge/sub` reported the far repository as its own worktree and the check would have been answered from that tree's boundary; status: fixed in 312bf0a, with two guards seen failing without it

Leads not pursued: `check_scope` slices the candidate document by scope
although the scan it came from was already scope-limited, so that slice can
never remove anything; it is a redundant call rather than a wrong one, and
removing it would leave the two documents sliced by different code paths.

## Scoped entry, step 4, round 2 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
206/206, root 38/38, `check .` exit 0, verified before this receipt. The round
audited the tree with round 1's escape fix applied, and asked the question
round 1 had not: whether the evidence the study demands for this step actually
exists yet. It did not.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R2-01; severity: medium; file: plugins/horos/tests/benchmark_scope.py; finding: the benchmark still called `check_tree`, which knows nothing of ancestor resolution, so every scoped run recorded exit 2 and a null median while the check itself worked. Criterion 12's measurement did not exist, and the record said `unavailable` rather than being wrong, which is why round 1 read past it; status: fixed in fad07e3

The fix also replaced the placeholder `tracked_files_inspected_outside_scope`
null with counters taken from the same scoped walk the check performs, of which
`classified_outside_scope` is the one that carries the claim. First measured
numbers, five runs each: full tree 59.6 ms; `plugins/alexandria` 24.4 ms over
210 classified files with 0 outside; `plugins/brevitas` 15.9 ms over 21
classified files with 0 outside. The heavier scope costs more than a third of
the whole tree because its weight is a content-addressed store, and digest
verification reads whole files by design.

Leads not pursued: the escape rule reads the process's working directory, so a
caller that changes directory between resolving a path and checking it would be
answered against the new one; every entry point here resolves and checks in one
call, and threading a base directory through the command would add a parameter
no caller has asked for.

## Scoped entry, step 4, round 3 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
207/207, root 38/38, `check .` exit 0, benchmark re-run at 24.1 ms for the
`plugins/alexandria` scope with 0 classified outside it, all verified before
this receipt. The round audited the tree with both earlier fixes applied and
re-checked the two things those fixes touched: the escape rule still refuses
all four escape shapes and admits every legitimate relative path. The
sibling case, `../two` from inside another scope, was run and then pinned as a
test in 5deb3e3 rather than left as a reasoned assumption; and the benchmark's
counters now come from the walk rather than from a constant.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: none.

## Scoped entry, step 5, round 1 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0, imprimatur
100.0/100 on both changed documents, brevitas clean, `git diff --check` clean.
Horos 212/212, root 38/38, the demonstration's own five cases and the seven
evolution-contract cases each run on their own as well, all verified before
this receipt.

This round's job was the assembled path rather than new code, so all fourteen
success criteria were re-derived from commands rather than from the earlier
rounds' word. The two that could only be checked by hand were the ledger
arithmetic and the demonstration's pinned output. Recomputing the frontier
digest with the contract's own helpers gives
`13eaade4077f194fe1296e041265d2a46e2db26ccd73e64d580a8637673869d9`, identical
to the row above it, with the revision held and the axis reading generation:
the held job was not spent. The demonstration was run from a temporary copy of
the example and its README compared line by line. One correction came out of
writing it: the README is itself a tracked file above the scope, so it moved
`listed outside scope` from 0 to 1, and the pinned value now matches what the
tool prints rather than what it printed before the file existed.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

Zero findings. Leads not pursued: `plugins/horos/**` still has no CI workflow,
so this plugin's 212 tests run locally and in no gate; `lazarus.yml` and
`pandects.yml` cover `tests/**`, which is why step 3 drew checks and steps 2
and 4 drew none. Adding `horos.yml` is an ask-first change under this run's
boundaries and is recorded on pull requests 256 and 261 rather than made here.

## Promise Machine, step 1, round 1 -- 2026-08-20

### Review scope

The Solidity suite was waived because this step changes Markdown policy,
runtime contracts and a standard-library Python checker. Phylax, Ephoros and
Hypomnema each exited 0 against the changed tree. The manual review covered the
law identity and field schema, fixed copy destinations, bounded reads, path and
symlink confinement, atomic replacement, empty discovery, component selection,
JSON/text finding parity and the generated-copy decision record.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `scripts/promise_machine.py` | `check --only copies` removed a missing-law finding and returned success without an authored source to compare | fixed and guarded on the audit branch |
| S1-R1-02 | medium | `scripts/promise_machine.py` | `check --only law` still ran plugin discovery and could fail on an unrelated empty plugin tree | fixed and guarded on the audit branch |
| S1-R1-03 | high | `audit/AUDIT.md` | The first audit-log write replaced the shared historical ledger instead of appending this round | parent bytes restored before receipt; this section is appended |

### Leads not pursued

Replacement of a plugin directory by another local process
between discovery and atomic rename. The command operates in the caller-owned
checkout under the caller's filesystem permissions, writes fixed destinations
and claims no hostile multi-user synchronisation boundary.

## Promise Machine, step 1, round 2 -- 2026-08-20

### Review scope

The fixed non-Solidity tree has no open finding. The root law and 14 copies
match, the missing-source copy check refuses with `PM001`, and law-only checking
does not depend on a plugin tree. The 11 focused Promise Machine tests and all
49 root tests pass. Phylax, Ephoros and Hypomnema each exit 0.

### Findings

Zero findings.

### Leads not pursued

The local directory-replacement race recorded in round 1, under the same
caller-owned-checkout boundary.

## Promise Machine, step 2, round 1 -- 2026-08-20

### Review scope

The Solidity suite remained waived because this step changes the standard-library
checker and its Python and Markdown fixtures. The review covered manifest and
recursive skill discovery, ownership classification, bounded reads, child-path
confinement, declaration parsing, exception attribution, deterministic reports
and the distinction between discovered and checked artefacts.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `scripts/promise_machine.py` | Inventory and inventory-only checks reported 14 copies although neither command read a copy | fixed in JSON and text output; guarded against future evidence overstatement |
| S2-R1-02 | high | `scripts/promise_machine.py` | A symlinked child router could be followed outside the repository without a finding | fixed by explicit child enumeration and confinement; guarded |
| S2-R1-03 | high | `scripts/promise_machine.py` | A symlinked promise overlay was silently omitted instead of refused | fixed by explicit fixed-path inspection; guarded |
| S2-R1-04 | medium | `scripts/promise_machine.py` | Exception prose containing the four attribution words passed without structured authority, scope, record or expiry values | fixed by labelled non-empty attribution parsing; guarded |
| S2-R1-05 | high | `scripts/promise_machine.py` | A vendored instruction could author its own Promise Machine contract while the structure check skipped it | fixed by refusing contracts in vendored instructions and requiring a first-party overlay; guarded |

### Leads not pursued

A local process can replace a regular directory after discovery, and an unreadable
caller-owned directory may stop Python's filesystem walk before a coded report is
formed. The checker runs inside the caller's checkout under the caller's filesystem
permissions and claims no hostile multi-user synchronisation or recovery from a
checkout the caller cannot read.

## Promise Machine, step 2, round 2 -- 2026-08-20

### Review scope

The corrected checker derives 14 plugins, 28 canonical skills, 23 governed
skills, five vendored skills and 20 routers without claiming copy validation.
The five focused guards, all 67 root tests and the Phylax, Ephoros and Hypomnema
gates pass. Vendored instructions remain unchanged.

### Findings

Zero findings.

### Leads not pursued

The caller-owned checkout limits recorded in round 1 remain unchanged.

## Promise Machine, step 3, round 1 -- 2026-08-20

### Review scope

The Solidity suite remained waived. The review covered the sole-router
cardinality, confined one-hop links, runtime-to-canonical resolution, canonical
logical ids, frontmatter authority, package and skill version layers, host-set
equality and the Horos Codex exposure.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | high | `scripts/promise_machine.py` | Full-document regexes let body prose supply a missing skill name or version, and accepted the first of duplicate metadata versions | fixed with bounded frontmatter parsing and exact multiplicity; guarded |
| S3-R1-02 | high | `scripts/promise_machine.py` | Package-version counts compared the two plugin manifests but ignored the root Claude marketplace version | fixed by comparing all three package surfaces before counting a package version; guarded |
| S3-R1-03 | medium | `scripts/promise_machine.py` | The router version check scanned body prose and falsely refused an indented version example outside frontmatter | fixed by limiting router identity and version checks to frontmatter; guarded |

### Leads not pursued

Runtime contracts identify canonical paths in their selection prose, but the
checker does not interpret natural-language request predicates. The sole router
and plugin contracts remain agent instructions; exact semantic request routing
is demonstrated manually rather than represented as a second policy language.

## Promise Machine, step 3, round 2 -- 2026-08-20

### Review scope

The corrected identity check reports one portable router, 28 unique canonical
skills, 14 package versions, 23 governed skill versions and matching 14-plugin
host sets. The four focused frontmatter and version guards, all 74 root tests
and the Phylax, Ephoros and Hypomnema gates pass.

### Findings

Zero findings.

### Leads not pursued

The natural-language routing boundary recorded in round 1 remains unchanged.

## Promise Machine, step 3, publication correction -- 2026-08-20

### Review scope

Publication CI exposed four plugin-local scaffold tests that still addressed
portable mirrors removed by this step. The Alexandria, Brevitas, Lazarus and
Sapheneia guards now reach those plugins through the sole Promise Machine
router and then verify the runtime contract's canonical-skill link. Lazarus
keeps its invocation aliases at the runtime-contract layer.

### Findings

S3-CI-01, high, affected the Alexandria, Brevitas, Lazarus and Sapheneia test
directories. Their plugin-local scaffold guards still opened four deleted
portable mirrors, so the published Lazarus matrix failed despite the root suite
passing. The guards are fixed and exercised in all four affected plugin suites.

### Evidence

The 255 Alexandria tests, 15 Brevitas tests, 364 Lazarus tests and four
Sapheneia tests pass. The 74-test root suite also passes. Lazarus was exercised
in a fresh environment built from its committed `requirements.lock`, matching
the dependency boundary used by CI.

## Promise Machine, step 4, round 1 -- 2026-08-20

### Review scope

The Solidity audit suite remained waived because the step changes Markdown
declarations, Python contract checks and packaging guards. The review compared
all 43 standalone promises with their canonical commands and existing refusal
boundaries, then exercised absent-contract and declaration-identity mutations.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | high | `scripts/promise_machine.py` | The documented `contracts` component was only an alias for the earlier optional structure pass, so an absent standalone declaration still passed | fixed by requiring a contract for every non-Hexaemeron first-party skill and guarding an absent section |
| S4-R1-02 | high | `plugins/pandects/skills/pandects/SKILL.md` | `pandects-law-contract` said `pandects.py check` established generated catalogue-byte equality, although that relation belongs to the separate renderer regression | fixed by narrowing the law check and adding a separate render promise |
| S4-R1-03 | medium | `tests/test_promise_machine_contract.py` | The population guard collected expected promise ids from every level-three heading in a skill, so an id moved outside the contract section could satisfy the repository-specific assertion | fixed by confining exact id-set comparison to the contract section |

### Leads not pursued

This round does not claim behavioural conformance from the new Markdown.
Executable, prompt and transformation evidence receives its own coverage and
negative-evidence work in the following runbook steps.

## Promise Machine, step 4, round 2 -- 2026-08-20

### Review scope

The corrected contracts component requires all 13 standalone first-party
declarations while leaving the next step's Hexaemeron population explicit.
The exact contract-section id sets contain 43 promises. Pandects now gives
structural law checking and catalogue rendering separate evidence and
consequences. The absent-section mutation, 75 root tests, 116 Pandects Python
tests and the Pandects Foundry suite pass.

### Findings

Zero findings.

### Leads not pursued

The behavioural-conformance boundary recorded in round 1 remains unchanged.

## Promise Machine, step 5, round 1 -- 2026-08-20

### Review scope

The Solidity suite remained waived because this step changes first-party
Markdown contracts, a standard-library checker and its Python tests. The
review compared all 18 Hexaemeron declarations with their canonical
instructions and checked the five vendored overlays against their unchanged
upstream bytes. It also inspected overlay discovery, confinement, bounded
reads, suite-wide identifier uniqueness, exact coverage, digest drift,
first-party rejection and the runtime digest-check instruction.

### Findings

Zero findings.

### Evidence

The checker reports 61 canonical first-party promises and five digest-bound
vendored overlays. All 44 focused Promise Machine tests, 80 root tests and 451
Hexaemeron tests pass. A one-byte mutation of a vendored instruction is
refused with `PM057`; the five vendored instruction paths have no diff.
Imprimatur, Brevitas, Phylax, Ephoros, Hypomnema and Horos are clean.

### Leads not pursued

The declarations state evidence contracts but do not yet prove every skill's
runtime implementation conforms to them. Executable, prompt, transformation
and vendored conformance are the explicit subjects of the next two runbook
steps, so treating that work as a finding here would duplicate their scope.

## Promise Machine, step 6, round 1 -- 2026-08-20

### Review scope

The Solidity suite remained waived because this step changes a standard-library
checker, JSON coverage records and Python tests. The review traced every selected
P/M/S/O/R/X reference to its exact selector, checked evidence reuse and
inapplicability rules, inspected the Berean and Janus preservation boundaries and
the Lazarus-to-Berean-to-Ariadne handoffs, and compared judgement-held promises
with the narrower mechanical gates beside them.

### Findings

FINDING
Severity High. S6-R1-01: Three judgement-held promises cited mechanical parser tests.
Location: `tests/promise_machine_coverage.json`
Mechanism: The Ephoros, Phylax and Protasis review rows borrowed evidence from narrower mechanical gates.
Impact: The coverage map overstated what those tests established.
Fix: Added 15 labelled review cases that record P/M/S/O/R judgements without presenting them as checked runtime proof.
END

FINDING
Severity Medium. S6-R1-02: Evidence references could not state their base class.
Location: `scripts/promise_machine.py`
Mechanism: The schema accepted only a path, selector and claim.
Impact: Recorded judgement cases were indistinguishable from executable checks.
Fix: Added a validated optional `evidence_class` field and refusal tests for unsupported classes.
END

### Evidence

The executable coverage gate reports 50 selected promises out of 66 discovered,
with no finding. The 25 focused coverage and labelled-case checks, all 90 root
tests and all 467 Hexaemeron tests pass. The Phylax, Ephoros and Hypomnema gates
are clean.

### Leads not pursued

Recorded review cases establish that each decision path has been named and kept
inside its boundary; they do not turn a human review judgement into runtime
proof. The remaining prompt, transformation and vendored rows stay visibly
pending for runbook step 8.

## Promise Machine, step 6, round 2 -- 2026-08-20

### Review scope

The corrected coverage map keeps executable tests, recorded review cases and
inapplicability reasons distinct. All exact references resolve; incompatible
P/M/S/O/R paths remain separate; the required preservation and handoff records
remain explicit; and the full law, copy and executable-coverage checks are clean.

### Findings

Zero findings.

### Evidence

All 90 root tests and all 467 Hexaemeron tests pass. The Phylax, Ephoros and
Hypomnema gates are clean.

### Leads not pursued

The recorded-judgement and later-runbook boundaries from round 1 remain
unchanged.

## Promise Machine, step 7, round 1 -- 2026-08-20

### Review scope

The Solidity suite remained waived because this step changes Python and JSON
coverage records and tests, not Solidity. The review compared all 16 prompt,
transformation and vendored rows with their canonical evidence classes, traced
each P/M/S/O/R/X reference to its owning test or labelled corpus, checked
evaluation provenance and confirmed that the five vendored instructions remain
byte-exact.

### Findings

FINDING
Severity High. S7-R1-01: Vulgate cases used an evidence class its promise does not accept.
Location: `tests/promise_machine_coverage.json`
Mechanism: Generic Hexaemeron cases were marked `recorded`, while Vulgate declares only `checked` and `inferred` evidence.
Impact: A recognised class could pass even when the owning promise excluded it.
Fix: Added Vulgate-specific inferred references and made the gate reject explicit classes absent from the canonical declaration.
END

FINDING
Severity Medium. S7-R1-02: Evaluation corpora could use checkout-specific absolute paths.
Location: `scripts/promise_machine.py`
Mechanism: Confinement accepted an absolute path when it happened to resolve inside the current checkout.
Impact: A locally clean record could fail to identify the same corpus in another checkout.
Fix: Required confined repository-relative corpus paths and added missing, absolute and overclaimed-provenance refusal cases.
END

### Evidence

The prompt and vendored coverage gate reports all 16 selected promises with no
finding. The 17 focused coverage checks pass, including evidence-class and
evaluation-corpus mutations. Vulgate stays `unknown` for cross-model content
parity and its labelled evidence is `inferred`, not `recorded` or `proved`.

### Leads not pursued

Labelled cases describe expected decisions and do not establish that a future
model will follow them. The coverage rows name `not-run` wherever no model,
campaign, conversion, sync, pre-audit or audit was executed.

## Promise Machine, step 7, round 2 -- 2026-08-20

### Review scope

The corrected gate derives every accepted evidence class from the owning
canonical declaration, requires explicit classes for prompt and vendored
references, and confines evaluation corpora to resolving repository-relative
paths. All 16 selected rows retain model, prompt, corpus and disposition
records with status limited to `recorded` or `unknown`.

### Findings

Zero findings.

### Evidence

All 17 focused coverage checks, 21 Brevitas tests, 60 Imprimatur checks, nine
Sapheneia tests, 474 Hexaemeron tests and 97 root tests pass. The Phylax,
Ephoros, Hypomnema and Horos gates are clean. The five vendored instruction
files remain unchanged.

### Leads not pursued

The forward-testing and no-execution limits recorded in round 1 remain
unchanged.

## Promise Machine, step 8, round 1 -- 2026-08-20

### Review scope

The Solidity suite remained waived because this step changes the root Python
checker, JSON inventories, package manifests, prose and Imprimatur's Markdown
heading rule, not Solidity. The review compared all 29 level-2 and level-3
bindings with their canonical declarations and result surfaces, checked package
and skill version separation, recomputed the unchanged frontier digest for the
Imprimatur generation, and inspected the new default full-check path.

### Findings

FINDING
Severity High. S8-R1-01: A runtime field map was not bound to the result surface bytes.
Location: `tests/promise_machine_coverage.json`
Mechanism: The gate checked that each schema, writer or contract existed, but a later change to that source could leave its field map green.
Impact: A stale map could misstate where a consequential result carries its subject, evidence, unknowns or transition.
Fix: Added a required source SHA-256, recomputation in the root checker and a source-drift refusal test.
END

FINDING
Severity Medium. S8-R1-02: Runtime source hashing had no read bound.
Location: `scripts/promise_machine.py`
Mechanism: A coverage entry could point the checker at any regular repository file and read all of it into memory.
Impact: A malformed or hostile entry could turn the structural gate into an avoidable memory sink.
Fix: Hash sources in 64 KiB chunks, stop above 1 MiB and guard the limit with an oversized-source test.
END

### Evidence

The full checker reports 14 plugins, 28 canonical skills, 66 promises, 29
digest-bound runtime bindings and zero findings. The focused runtime mutations
refuse an absent binding, a repository escape, source drift and an oversized
source.

### Leads not pursued

The inventory binds existing domain formats; it does not replace them with a
generic result envelope or claim that a structural field map proves the domain
result. Berean's Wildcat-grounded release and Janus's second adapter remain held
frontier work.

## Promise Machine, step 8, round 2 -- 2026-08-20

### Review scope

The corrected checker now derives the high-consequence set from canonical
declarations, requires exactly one complete runtime map for each member, confines
its source, recomputes the reviewed source digest through a bounded read and
refuses stale or extra entries. The package release still leaves every unrelated
skill frontier untouched.

### Findings

Zero findings.

### Evidence

The Promise Machine full check is clean across all 66 promises. All 91 focused
contract, evolution, version and marketplace tests, all 104 root tests, all 474
Hexaemeron tests and all 62 Imprimatur checks pass. The Phylax, Ephoros,
Hypomnema and Horos gates are clean.

### Leads not pursued

The digest proves which result surface the map reviewed, not that a domain
operation ran or its assertion is true. Those claims remain with the exact
command, gate or observation named by the owning promise.

## Promise Machine, step 8, publication gate repair -- 2026-08-20

### Failure

FINDING
Severity High. S8-PG-01: Lazarus's scaffold test still equated package and skill versions.
Location: `plugins/lazarus/tests/test_scaffold.py`
Mechanism: The test compared both host manifest versions with canonical skill metadata instead of the marketplace package entry.
Impact: The planned `lazarus` package release failed on Python 3.11 and 3.13 despite preserving `lazarus-v1.1.0` correctly.
Fix: Compare both host manifests with the marketplace package version and guard its independence from skill and writer versions.
END

### Evidence

The failure reproduced with the exact Lazarus scaffold test. The corrected test
passes on the full Lazarus suite and preserves the checked-in fixture's
`tool_version` separately.

### Boundary

This repair changes no Lazarus command, result format, canonical skill version,
frontier digest or held job. It corrects a stale test of the distribution layer.

## Promise Machine, step 8, publication gate repair follow-up -- 2026-08-20

### Failure

FINDING
Severity High. S8-PG-02: Four plugin suites retained the same package/skill version assumption.
Location: `plugins/alexandria/tests/test_scaffold.py`, `plugins/berean/tests/test_scaffold.py`, `plugins/probitas/tests/test_manifests.py` and `plugins/tabularium/tests/test_scaffold.py`
Mechanism: Three tests pinned the preceding package version and the Probitas test required package and canonical skill versions to be equal.
Impact: The complete Step 10 demonstration stopped in Alexandria, while Probitas would have rejected the intended package-only release despite its held skill frontier.
Fix: Bind package assertions to the release version and marketplace surfaces, and make Probitas's package-versus-skill independence explicit.
END

### Evidence

The failure reproduced in Alexandria's full suite. The corrected Alexandria,
Berean, Probitas and Tabularium suites pass 255, 151, 276 and 134 tests. Their
host manifests carry the release package versions while their canonical skill
versions and evolution ledgers remain unchanged.

### Boundary

This follow-up changes test expectations only. It does not change a command,
result format, promise, canonical skill version, frontier digest or held job.

## Promise Machine, step 9, round 1 -- 2026-08-20

### Review scope

The Solidity suite remained waived because Step 9 adds one Markdown evidence
record and changes no executable or Solidity file. The review compared every
recorded count with its command result, checked the installed package and skill
versions independently, inspected the Codex resolver entries, and confirmed
that both unavailable host observations were reported as unknowns.

### Findings

Zero findings.

### Evidence

The Promise Machine inventory and full check are clean, the checker completes
in 0.10 seconds, and the root suite passes 104 tests. Every plugin suite named
in the runbook passes, including Berean's 151 tests, Janus's 14 Python and 24
Foundry tests, and Pandects's 116 Python and 79 Foundry tests. The Phylax,
Ephoros and Hypomnema tree checks exit clean. The new evidence document passes
Imprimatur and Brevitas.

### Leads not pursued

Codex computer control cannot inspect the Codex app, so the picker screenshot
was not taken. Claude Code's expired OAuth token prevented the model-backed
slash invocation. The evidence record names both limits and retains the
resolver, package and host-neutral transcripts that did run; it does not infer
either missing result.

## Protasis audit-record source, step 1, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The step adds two committed documents, byte-identical to the
run's `.hexaemeron` study and runbook. Phylax, ephoros and hypomnema lints
exit 0 over the tree. The diff was reviewed against the risk register's
concerns: no contract prose changed this step, so wording drift against the
audit loop's file definition and the ledger arithmetic do not yet arise.
Root suite 104/104. Hexaemeron suite 470/472: the two failures are
`test_elenchus_checker` requiring a `forge` binary and node v26.6.0 that
this container does not have (node v22.22.2, no Foundry, install blocked by
network policy); both fail identically on base `b26181b`, so they are
environmental rather than introduced.

Leads not pursued: none

## Protasis audit-record source, step 2, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The diff was reviewed against the risk register's three
concerns. Item 2's wording names the audit file exactly as the audit loop
defines it (`config audit.log_path`, default `audit/AUDIT.md`). The
checklist line asks for what item 2 states and nothing more, including the
plain statement where there was nothing to read. The ledger row holds the
generation arithmetic, revision and digest, proved by the evolution suite.
Phylax, ephoros, hypomnema and the protasis runbook check all exit 0.
Root suite 104/104; hexaemeron suite 470/472 with the same two
environmental failures recorded for step 1.

Leads not pursued: none

## Protasis study schema check, step 1, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The step commits the study and runbook, byte-identical to the
run's working copies. Phylax, ephoros and hypomnema exit 0 over the tree.
Reviewed against the risk register: no checker code exists yet, so the
unearned-verdict concerns do not arise this step. Root suite 104/104;
hexaemeron 470/472 with the two recorded environment failures.

Leads not pursued: none

## Protasis study schema check, step 2, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The round worked the risk register's four unearned-verdict
concerns directly against the code: a fenced item heading is not an item
(backtick and tilde probed), a duplicate number returns S004 and no answer
verdict, a bare none in five spellings is refused whole-answer only, and
the heading form the check reads is the one every committed study uses.
Further probes: an item 13 is ignored as unmandated, a subsection stays in
its item's body, a CRLF document scans identically. Phylax, ephoros and
hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the two recorded
environment failures and 20 new study cases passing.

Leads not pursued: an answer asserting none with filler words but no
reason ("None whatsoever at all.") passes as content. Distinguishing a
reason from filler is answer quality, which the checker's stated boundary
leaves to the reviewer; tightening it mechanically would refuse honest
long-form answers.

## Protasis study schema check, step 3, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

One fault surfaced and was fixed before this round closed: the first cut
of the new held-job text used a word the prose lint refuses without a
concrete referent, caught by the root suite's shipped-prose gate; the
sentence was rewritten and the frontier digest recomputed over the final
line, which is the order the versioning contract demands. Reviewed
against the register: the evolution row's arithmetic, digest and header
agreement are held by the evolution suite; the mechanical-subset section
cites both modes without restating either. Phylax, ephoros and hypomnema
exit 0. Demo path clean over the run's own study. Root 104/104;
hexaemeron 490/492 with the two recorded environment failures.

Leads not pursued: none

## Protasis risk-register block, step 1, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Two committed documents, byte-identical to the run's working
copies; the study's own item 5 carries the first fenced block and the
study check exits 0 over it. Per the register: shape-drift reviewed, the
held job's wording is untouched this step; example-mismatch reviewed, the
block's three lines each split into three pipe-separated fields;
ledger-arithmetic not applicable, no row cut this step. Phylax, ephoros
and hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the two
recorded environment failures.

Leads not pursued: none

## Protasis risk-register block, step 2, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Per the register: shape-drift reviewed, the held job's
target and acceptance read byte-identical before and after the diff, and
the row retains revision and digest; example-mismatch reviewed, the
example block in item 5 splits into three pipe-separated fields on both
lines; ledger-arithmetic reviewed, the evolution suite passes over the
new generation row. Phylax, ephoros, hypomnema and the study check exit
0. Root 104/104; hexaemeron 490/492 with the two recorded environment
failures.

Leads not pursued: none

## Protasis amendment contract, step 1, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Two committed documents, byte-identical to the run's working
copies; the study check exits 0 over the study. Per the register:
refusal-drift not applicable, no contract text changed this step;
field-mismatch reviewed, the study's item 1 and item 4 name the same four
fields; ledger-arithmetic not applicable, no row cut this step. Phylax,
ephoros and hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the
two recorded environment failures.

Leads not pursued: none

## Protasis amendment contract, step 2, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Per the register: refusal-drift reviewed, the new rule
reuses the contract's existing three-part refusal report rather than
defining a second shape; field-mismatch reviewed, the block's four fields
match the study's item 1 and the wish; ledger-arithmetic reviewed, the
evolution suite passes over the new generation row. Phylax, ephoros,
hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the two recorded
environment failures.

Leads not pursued: none

## Hypomnema first records, step 1, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Two committed documents, byte-identical to the run's working
copies; the study check exits 0. Per the register: content-drift not
applicable, no record touched this step; pointer-rot reviewed, the
hypomnema lint exits 0 over docs and plugins; ledger-arithmetic not
applicable, no row cut this step. Phylax and ephoros exit 0. Root
104/104; hexaemeron 490/492 with the two recorded environment failures.

Leads not pursued: none

## Hypomnema first records, step 2, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings open. One fault surfaced and was fixed before the step's
commit: ADR-006's first consequences sentence used a metaphor the prose
lint refuses; the sentence was rewritten with the fact intact. Per the
register: content-drift reviewed, the normalisation diff over ADR-002,
ADR-003 and ADR-004 touches status shape and one heading name only, 11
insertions against 9 deletions, and ADR-001 needed no change; pointer-rot
reviewed, the hypomnema lint exits 0 and every ADR cross-reference
(ADR-003 from ADR-005, ADR-004 from ADR-006) resolves; ledger-arithmetic
not applicable, no row cut this step. Phylax and ephoros exit 0. Root
104/104; hexaemeron 490/492 with the two recorded environment failures.

Leads not pursued: ADR-002 and ADR-004 carry no Alternatives section;
their rejected options live as prose in their context and decision
sections, written by the run that authored them. Restructuring that prose
into sections risks rewording another run's reasoning, so the gap is left
for the shape check this run's close names as the successor frontier.

## Hypomnema first records, step 3, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

One fault surfaced and was fixed within the step: the contract edit moved
the bytes of a Promise Machine runtime binding surface, and the coverage
gate refused the drift (PM071). The field map was reviewed as unchanged
and the inventory digest updated with the surface, which is the checker's
own remedy; the full promise_machine check returns clean. Per the
register: content-drift reviewed, no record changed this step;
pointer-rot reviewed, the hypomnema lint exits 0; ledger-arithmetic
reviewed, the evolution suite passes over the new row and its digest
matches the new frontier line. Phylax and ephoros exit 0. Root 104/104;
hexaemeron 490/492 with the two recorded environment failures.

Leads not pursued: none

## Hypomnema design bridge, step 1, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Two committed documents, byte-identical to the run's working
copies; the study check exits 0. Per the register: double-record and
scope-creep not applicable, no contract text changed this step;
ledger-arithmetic not applicable, no row cut this step. Phylax, ephoros
and hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the two
recorded environment failures.

Leads not pursued: none

## Hypomnema design bridge, step 2, round 1 -- 2026-08-20

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Per the register: double-record reviewed, the rule states
point-or-write and names the two homes with never both; scope-creep
reviewed, the rule fires in the prose phase on shipped studies and leaves
protasis's items 4 and 12 unchanged; ledger-arithmetic reviewed, the
evolution suite passes over the new generation row and the coverage
digest moved with the reviewed surface. Phylax, ephoros, hypomnema and
the promise_machine check exit 0. Root 104/104; hexaemeron 490/492 with
the two recorded environment failures.

Leads not pursued: none

## Protasis register check, step 1, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Two committed documents, byte-identical to the run's working
copies; the study check and the runbook check exit 0 over them, and the
regenerated boundary carries exactly the two new paths. Per the register:
false-clean, interface-drift, fixture-coverage and history-pragma not
applicable, no scanner, code or pragma changes this step;
ledger-arithmetic not applicable, no row cut this step. Phylax, ephoros
and hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the two
recorded environment failures.

Leads not pursued: none

## Protasis register check, step 2, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Per the register: false-clean reviewed, the fixture tests
prove a register quoted inside another fence and an item 5 duplicated by
S004 earn no verdict; interface-drift reviewed, S000 to S004 and P000 to
P004 keep their numbers and firing conditions, the new codes join the
docstring, the SKILL.md subset and the fixtures, and the one test that
changed did so because the incomplete fixture honestly gained an S005
under the new rule; fixture-coverage reviewed, each fault class has a
fixture line and a test naming its code; history-pragma reviewed, the
pragma on the pre-block study states its reason and no other historical
study changed; ledger-arithmetic reviewed, the evolution suite passes
over the v4.5.0 row. Phylax, ephoros and hypomnema exit 0. Root 104/104;
hexaemeron 505/507 with the two recorded environment failures.

Leads not pursued: none

## Hypomnema ADR shape check, step 1, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Two committed documents, byte-identical to the run's working
copies; the study check and the runbook check exit 0 over them, and the
regenerated boundary carries exactly the two new paths. Per the register:
backfill-fidelity, shape-source, false-positive and interface-drift not
applicable, no record, rule or code changes this step; ledger-arithmetic
not applicable, no row cut this step. Phylax, ephoros and hypomnema exit
0. Root 104/104; hexaemeron 505/507 with the two recorded environment
failures.

Leads not pursued: none

## Hypomnema ADR shape check, step 2, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Per the register: backfill-fidelity reviewed, each of the
six new alternative entries traces to a named line of the Promise
Machine study -- option D and the option C trade for ADR-002, the
non-goals list and the release context for ADR-004 -- and the records'
other sections are byte-identical to base; shape-source, false-positive
and interface-drift not applicable, no rule or code changes this step;
ledger-arithmetic not applicable, no row cut this step. Phylax, ephoros
and hypomnema exit 0. Root 104/104; hexaemeron 505/507 with the two
recorded environment failures.

Leads not pursued: none

## Hypomnema ADR shape check, step 3, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings open. One fault surfaced and was fixed within the step,
worked under elenchus: the section regex read a heading pragma as part
of the section name, so a suppressed status check reported the section
itself missing; the fix strips the allow comment before matching and the
suppression test guards it. The expected PM071 refusal fired on the
SKILL.md edit and took the checker's own remedy, the field map reviewed
as unchanged and the binding digest updated with its surface; the full
check returns clean. Per the register: backfill-fidelity not applicable,
no record content changed this step; shape-source reviewed, the dated
rule accepts exactly the v1.1.0 shape and all six tree records pass;
false-positive reviewed, a non-record name, a record name outside a
decisions directory and a fenced heading each earn no shape verdict, and
walks skip fixture specimens relative to the root; interface-drift
reviewed, H000 to H003 keep their numbers and firing conditions and
every pre-existing test passes unchanged; ledger-arithmetic reviewed,
the evolution suite passes over the v2.2.0 row. Phylax, ephoros and
hypomnema exit 0. Root 104/104; hexaemeron 519/521 with the two recorded
environment failures.

Leads not pursued: none

## Hypomnema source-comment references, step 1, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Two committed documents, byte-identical to the run's working
copies; the study check and the runbook check exit 0 over them, and the
regenerated boundary carries exactly the two new paths. Per the register:
string-false-positive, tree-self-trip, index-reuse and interface-drift
not applicable, no scanner, test or code changes this step;
ledger-arithmetic not applicable, no row cut this step. Phylax, ephoros
and hypomnema exit 0. Root 104/104; hexaemeron 519/521 with the two
recorded environment failures.

Leads not pursued: none

## Hypomnema source-comment references, step 2, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The expected PM071 refusal fired on the SKILL.md edit and
took the checker's own remedy, the field map reviewed as unchanged and
the binding digest updated with its surface; the full check returns
clean. Per the register: string-false-positive reviewed, the tests
prove a reference inside a string, after a quote-glued marker and
behind a URL's double slash earn no finding; tree-self-trip reviewed,
the tree-wide walk exits 0 with the new tests in place and their
specimens built by concatenation; index-reuse reviewed, both passes
resolve against the one index built from record file names, and the
fixture walk catches the dangling reference beside the shape faults;
interface-drift reviewed, H000 to H005 keep their numbers and firing
conditions and every pre-existing test passes unchanged;
ledger-arithmetic reviewed, the evolution suite passes over the v3.2.0
row. Phylax, ephoros and hypomnema exit 0. Root 104/104; hexaemeron
532/534 with the two recorded environment failures.

Leads not pursued: none

## Hypomnema runbook shape check, step 1, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. The step contains the study and runbook byte-identical to the
receipted working copies and a regenerated Horos boundary for those two paths.
The Protasis checks are clean, the root suite passes 104/104 and the
Hexaemeron suite passes 536/536. Phylax, Ephoros and Hypomnema each exit 0 over
the changed tree. The risk-register concerns are not yet applicable: this step
changes no path classifier, heading scan, pragma, handoff interface, stable
code, frontier row or marketplace description.

Leads not pursued: none

## Hypomnema runbook shape check, step 2, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings open. H007 applies only to Markdown below a `runbooks` directory,
requires the three exact level-two headings and non-empty bodies outside code
fences, and accepts a reasoned exception only on line 1 or the relevant
heading. Six fixtures isolate the missing and empty cases; the complete
fixture, outside-scope file, fenced examples and pragma boundaries stay clean.
H003 remains existence-only, and no alert-rule parsing moves out of Ephoros.
H000 to H006 retain their tests and scope. The frontier row advances exactly
from v3.2.0 to v4.2.0, its digest and Promise Machine binding recompute, and
the skills#314 design-bridge lead becomes the evidenced successor.

The frontier prose review covered 288 tracked mutable first-party surfaces.
It found four stale descriptions, all corrected in this step: Hypomnema's
SKILL and ledger, Hexaemeron's Codex long description and its README test
description. Historical studies and runbooks remain point-in-time records.
One earlier environment failure was worked under Elenchus: the walker tried
to read generated directories whose names ended in `.sol`; an `is_file()`
guard and its regression test now keep directories out of the source set.

Phylax, Ephoros and Hypomnema each exit 0. The focused Hypomnema suite passes
58/58, the root suite 104/104, Hexaemeron 548/548, evolution 7/7 and
marketplace prose 13/13. Promise Machine checks 14 plugins and copies clean;
Horos scans 1,360 files with 89 classified entries and none unreadable.

Leads not pursued: none

## Ephoros alert-runbook annotations, step 1, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S1-R1-01; severity: low; file: `.horos/boundary.json`; finding: The committed tracked-universe document reports 1,367 files walked; a fresh scan of the committed step tree reports 1,369. Removing only `counts.files_walked` makes the documents byte-identical, so the hard boundary is current but its published walk count omits the two tracked study/runbook files.; status: open

Scope: `0bfad60bb482245dd08d9747139d26824392a2c7..a8f2a13f9143b0335cba514c4ef0f9dd9afa34ed`, limited to the two tracked specification documents and regenerated Horos boundary. Both documents are byte-identical to the receipted working copies; Protasis study/runbook, Imprimatur, per-file Brevitas and diff checks exit 0. Phylax, Ephoros and Hypomnema tree lints each exit 0. Evolution 18/18, root 104/104 and Hexaemeron 548/548 pass; Promise Machine reports 14 plugins and copies clean. The step commit has a good local signature and exactly one required co-author and origin trailer.

Leads not pursued: none

### Resolution: E319-S1-R1-01 -- 2026-08-21

Resolved on the audit branch by regenerating `.horos/boundary.json` after the two specification documents were tracked. The committed document and a fresh tracked-universe scan are now byte-identical at 1,369 files walked, with 89 classified entries and none unreadable. The complete step-1 gate set remains clean: document copies, Protasis, Imprimatur, per-file Brevitas, Promise Machine, evolution 18/18, root 104/104, Hexaemeron 548/548, boundary currency 4/4, diff check and the Phylax, Ephoros and Hypomnema tree lints all exit 0. No new leads.

## Ephoros alert-runbook annotations, step 1, round 2 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- Table fields: id; severity; file; finding; status

No findings. Re-reviewed the folded scope `0bfad60bb482245dd08d9747139d26824392a2c7..04c0df48073f79efe82e6e9999b87344e7a80e40`, including the two specification documents, corrected Horos boundary and round-1 audit history. The boundary and a fresh tracked-universe scan are byte-identical at 1,369 files walked, with 89 classified entries and none unreadable. Both documents remain byte-identical to the receipted copies. Protasis, Imprimatur, per-file Brevitas, Promise Machine, evolution 18/18, root 104/104, Hexaemeron 548/548, boundary currency 4/4, diff check and the Phylax, Ephoros and Hypomnema tree lints all exit 0.

No further leads remain.

## Ephoros alert-runbook annotations, step 2, round 1 -- 2026-08-21

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R1-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` | E004 suppression searches the raw alert line and its raw predecessor. A pragma-shaped string in a quoted scalar, or the last line of a block scalar immediately above an unannotated alert, therefore suppresses E004 even though it is not a YAML comment. | open |
| E319-S2-R1-02 | low | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | `BLOCK_SCALAR` recognises only a mapping-key header containing `:`. A valid bare sequence scalar such as `- |` or `- >` is not entered as scalar content, so an example `- alert:` or `runbook:` line in its body produces E004 or H003. | open |
| E319-S2-R1-03 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | Both YAML paths call `Path.read_bytes()` before comparing the result with `MAX_YAML_BYTES`. Oversize inputs fail visibly, but the process has already read the complete caller-named file into memory, so the promised 1 MiB read boundary is not enforced. | open |
| E319-S2-R1-04 | low | `.horos/boundary.json` | The step did not regenerate the tracked-tree document after adding seven fixtures. The committed boundary reports 1,369 files walked and a fresh tracked scan reports 1,376; removing only `counts.files_walked` makes the documents byte-identical. | open |
| E319-S2-R1-05 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` | The `alert`, `annotations` and `runbook` key recognisers are case-insensitive. Consequently `- Alert:` is classified although it is outside the exact supported key shape, while an exact `alert:` entry carrying `Annotations.Runbook` passes E004 even though it lacks the required lowercase nested keys. | open |

Scope: `3b2d58955d483586f326ab68ed73994532a0d7bf..cefd3735b447cd916b086881aaff936c0d9cf7f5`, the complete folded step-2 diff. Focused checker tests pass 96/96; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 569/569. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and the Phylax, Ephoros and Hypomnema tree lints exit 0. The boundary-currency unit module passes 4/4 because its comparison names entry drift but does not compare `counts.files_walked`; the direct fresh-document comparison above fails. The step commit has a good local signature and exactly one required co-author and origin trailer. The two generation rows retain their prior frontier revisions, digests, statuses and held jobs, and H007 is unchanged.

Leads not pursued: non-HTTP URI schemes and unquoted hashes in plain scalar paths remain outside the documented relative-path prototype; neither changes the five findings above.

### Resolution: Ephoros alert-runbook annotations, step 2, round 1 -- 2026-08-21

All five findings are resolved on the audit branch. E319-S2-R1-01 now derives
E004 suppression only from reasoned YAML comments outside quoted and block
scalar text. E319-S2-R1-02 extends both bounded lexers to recognise bare
sequence block scalars introduced by `- |` and `- >`. E319-S2-R1-03 replaces
whole-file `read_bytes()` calls with one binary read capped at 1 MiB plus one
byte, and guards the requested read size. E319-S2-R1-04 regenerates the Horos
document over 1,376 tracked files with 89 entries and none unreadable.
E319-S2-R1-05 makes the supported YAML keys exact-case, so `Alert`,
`Annotations` and `Runbook` remain outside the lowercase prototype.

The seven new guard tests were observed red before the fixes: the focused
suite ran 103 tests with ten assertion failures covering the two scalar
markers and two suppression specimens separately. After repair, the focused
suite passes 103/103, evolution and version propagation 23/23, marketplace
prose 13/13, root 104/104 and Hexaemeron 576/576. Protasis accepts both
documents; Imprimatur and per-file Brevitas accept the six named prose files;
Promise Machine reports 14 plugins and 14 copies clean; Phylax, Ephoros and
Hypomnema each exit 0 over their required trees. E000 to E004 and H000 to H007
retain their ownership and numbers, H007 is unchanged, and both held frontier
digests remain unchanged. No new leads.

## Ephoros alert-runbook annotations, step 2, round 2 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-R2-01; severity: medium; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`; finding: `_split_yaml_comment` treats every unquoted `#` as a comment marker, although a hash without separating whitespace remains plain-scalar content. A preceding list item such as `- note: literal# ephoros: allow not-a-comment` therefore suppresses E004 on the next unannotated alert.; status: open
- id: E319-S2-R2-02; severity: low; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`; finding: `_yaml_allow_lines` handles a comment-only line before checking whether its indentation ended the active block scalar. A real dedented reasoned comment immediately after a scalar and immediately before an alert is therefore discarded as scalar text, and the documented E004 suppression does not apply.; status: open

Scope: the complete folded tree `3b2d58955d483586f326ab68ed73994532a0d7bf..89bff0f5a5415cf9900efd26d7121cffe6225763`. All seven round-1 regression tests were run against `ba37b42d5890ca45e59d24f5034b32e4dfe9ddb4` in memory and produced ten failures; the same seven pass against the fixed tree. This closes the five exact round-1 specimens, including capped reads and boundary identity, but the two adjacent suppression-state cases above remain open. Focused tests pass 103/103; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 576/576. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 files walked, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer. Ownership remains E004 presence, H003 pointer existence and unchanged H007 Markdown shape; both ordinary-generation frontier digests remain unchanged.

Further leads: none beyond E319-S2-R2-01 and E319-S2-R2-02.

### Resolution: Ephoros alert-runbook annotations, step 2, round 2 -- 2026-08-21

Both findings are resolved on the audit branch. E319-S2-R2-01 now recognises
an unquoted `#` as a YAML comment marker only at the start of a line or after
separating whitespace, so pragma-shaped plain-scalar content cannot suppress
E004. E319-S2-R2-02 checks a comment-only line's indentation against active
block-scalar state first, so a genuinely dedented reasoned comment exits the
scalar and can suppress the alert immediately below it.

The two guards were observed red before repair: the focused suite ran 105
tests with two failures, one for each mechanism. After repair, the focused
suite passes 105/105, evolution and version propagation 23/23, marketplace
prose 13/13, root 104/104 and Hexaemeron 578/578. Protasis accepts both
documents; Imprimatur and per-file Brevitas accept the six named prose files;
Promise Machine reports 14 plugins and 14 copies clean; Phylax, Ephoros and
Hypomnema each exit 0 over their required trees. All other YAML behaviour,
finding codes, ownership, versions and held frontier digests are unchanged.
No new leads.

## Ephoros alert-runbook annotations, step 2, round 3 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-R3-01; severity: medium; file: `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`; finding: Hypomnema's separate YAML comment splitter still treats every unquoted `#` as a comment marker. An alert pointer such as `runbook: runbooks/missing#book.md` is accepted by Ephoros as a relative Markdown annotation, then truncated before `.md` and ignored by H003, so the missing target passes both ownership gates.; status: open
- id: E319-S2-R3-02; severity: low; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`; finding: The YAML/Python directory walk does not require discovered paths to be files. A directory whose name ends in `.yaml`, `.yml` or `.py` is passed to `check()` and produces E000 instead of being left outside the source set; Hypomnema's parallel walk already guards this boundary with `is_file()`.; status: open

Scope: the complete folded tree `3b2d58955d483586f326ab68ed73994532a0d7bf..ed3785f0b6669b9c45a9ffa4874b8569984628c8`. Both round-2 guards were run against `a0af48ee6f162b7602414105a59e26929863627a` in memory and failed once each; both pass against the fixed tree. The exact round-2 suppression cases are closed, but the remaining YAML boundary probes found the two cases above. Focused tests pass 105/105; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 578/578. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 files walked, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer. Per-alert isolation, E004/H003 ownership, unchanged H007 and both ordinary-generation frontier digests otherwise remain intact.

Further leads: none beyond E319-S2-R3-01 and E319-S2-R3-02.

### Resolution: Ephoros alert-runbook annotations, step 2, round 3 -- 2026-08-21

Both findings are resolved on the audit branch. E319-S2-R3-01 gives
Hypomnema the same whitespace-bounded YAML comment marker as Ephoros, so the
plain-scalar path `runbooks/missing#book.md` remains whole and emits H003 when
absent; the paired E004 presence guard stays clean. E319-S2-R3-02 now requires
recursive Ephoros walk candidates to be files, leaving suffix-matching
directories outside the checker input set.

The two fault guards were observed red before repair: the focused suite ran
108 tests with two failures, one for each finding. After repair, the focused
suite passes 108/108, evolution and version propagation 23/23, marketplace
prose 13/13, root 104/104 and Hexaemeron 581/581. Protasis accepts both
documents; Imprimatur and per-file Brevitas accept the six named prose files;
Promise Machine reports 14 plugins and 14 copies clean; Phylax, Ephoros and
Hypomnema each exit 0 over their required trees. A fresh Horos scan remains
at 1,376 tracked files, 89 entries and none unreadable. All other semantics,
finding codes, ownership, versions and held frontier digests are unchanged.
No new leads.

## Ephoros alert-runbook annotations, step 2, round 4 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-R4-01; severity: medium; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`; finding: Both bounded YAML lexers reset quote state on every physical line. In a valid multi-line single- or double-quoted scalar, alert-shaped text is therefore treated as real keys: quoted `annotations.runbook` text can satisfy E004 for an unannotated alert, quoted `- alert:` text can produce E004, and quoted `runbook:` text can produce H003.; status: open

Scope: the complete folded tree `3b2d58955d483586f326ab68ed73994532a0d7bf..9e3be06a062c79138ad6aed1776ad824bf642a03`. The two round-3 fault guards were run against `3008376882d955c7a7168c013d57cbfc24d44c91` in memory and failed once each; both pass against the fixed tree, and the paired Ephoros hash-path presence guard is also green. The round-3 path and walk boundaries are closed; the remaining material YAML review found only the multi-line quoted-scalar case above. Focused tests pass 108/108; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 581/581. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 files walked, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer. Per-alert isolation, E004/H003 ownership, unchanged H007 and both ordinary-generation frontier digests otherwise remain intact.

Further leads: none beyond E319-S2-R4-01.

### Resolution: Ephoros alert-runbook annotations, step 2, round 4 -- 2026-08-21

E319-S2-R4-01 is resolved on the audit branch. Both bounded YAML lexers now
carry single- and double-quoted scalar state across physical lines. Lines
inside those scalars cannot supply an alert, an alert annotation, a reasoned
suppression pragma or a generic runbook pointer. Block scalar bodies remain
opaque before quote scanning, preserving the earlier scalar boundary.

The four guards cover both quote styles and were observed red before repair:
the focused suite ran 112 tests with eight subtest failures across false E004
alert detection, false E004 satisfaction, false E004 suppression and false
H003 detection. After repair, the focused suite passes 112/112, evolution and
version propagation 23/23, marketplace prose 13/13, root 104/104 and
Hexaemeron 585/585. Protasis accepts both documents; Imprimatur and per-file
Brevitas accept the six named prose files; Promise Machine reports 14 plugins
and 14 copies clean; Phylax, Ephoros and Hypomnema each exit 0 over their
required trees. All other semantics, finding codes, ownership, versions and
held frontier digests are unchanged. No new leads.

## Ephoros alert-runbook annotations, step 2, round 5 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-R5-01; severity: medium; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`; finding: The cross-line quote state opens on every apostrophe or double quote, including one inside a plain scalar. A preceding value such as `O'Brien` or `six" pipe` therefore hides a later `- alert:` or `runbook:` key, allowing missing E004 or H003 evidence to pass.; status: open
- id: E319-S2-R5-02; severity: low; file: `plugins/hexaemeron/tests/test_ephoros_checker.py`, `audit/AUDIT.md`; finding: The quoted-runbook-satisfaction guard is already green against the pre-fix round-4 tree. Independent replay produces six red subtests, not the eight recorded in the round-4 resolution, so this guard does not establish the claimed false-E004-satisfaction mechanism and the resolution overstates its red evidence.; status: open

Scope: the complete folded tree `3b2d58955d483586f326ab68ed73994532a0d7bf..914099ab3daed011b6f147303214c7d62b3c61f6`. The four round-4 guard methods were run against `91fdc4c2904040d548b75900978c7de3c8c18af6` in memory: false alert detection, false suppression and false H003 detection produced six subtest failures across both quote styles, while the claimed false-satisfaction guard remained green. All four methods pass against the fixed tree. Direct current-tree probes then found E319-S2-R5-01 for both quote characters and both ownership gates. Focused tests pass 112/112; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 585/585. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 tracked files, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer. H007 remains unchanged; per-alert isolation, pointer base, stable finding codes, ordinary generation and held frontier digests otherwise remain intact.

Further leads: none beyond E319-S2-R5-01 and E319-S2-R5-02.

### Resolution: Ephoros alert-runbook annotations, step 2, round 5 -- 2026-08-21

Both findings are resolved on the audit branch. E319-S2-R5-01 restricts
cross-line quote state to a quote at a supported quoted-scalar start. An
apostrophe or double quote embedded in a plain scalar no longer hides a later
alert or runbook pointer, while genuine multi-line quoted scalars remain
opaque. E319-S2-R5-02 corrects the round-4 evidence: independent replay found
six red subtests, two each for false alert detection, false suppression and
false H003 detection. The quoted-runbook-satisfaction guard was already green
for both quote styles and remains a regression guard, not red evidence.

The two round-5 guard methods were observed red before repair: the focused
suite ran 114 tests with four subtest failures across both quote styles and
both ownership gates. After repair, the focused suite passes 114/114,
evolution and version propagation 23/23, marketplace prose 13/13, root
104/104 and Hexaemeron 587/587. Protasis accepts both documents; Imprimatur
and per-file Brevitas accept the six named prose files; Promise Machine
reports 14 plugins and 14 copies clean; Phylax, Ephoros and Hypomnema each
exit 0 over their required trees. All other semantics, finding codes,
ownership, versions and held frontier digests are unchanged. No new leads.

## Ephoros alert-runbook annotations, step 2, round 6 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-R6-01; severity: medium; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`; finding: `_yaml_quote_starts` accepts a mapping-looking colon or sequence-looking dash without requiring YAML separation before the quote. Valid plain scalars such as `- note: plain:"text` and an indented `-"text` therefore open cross-line quote state and hide later alert or runbook keys, allowing missing E004 or H003 evidence to pass.; status: open

Scope: the complete folded tree `3b2d58955d483586f326ab68ed73994532a0d7bf..80a43d1be67eb9d2c71501e51fa1db97446cf829`. The two round-5 guard methods were run against `49bbe00b2d3aff9fbdd121a9a87f3984db5dcd78` in memory and produced four subtest failures, one for each quote style and ownership gate; both methods pass against the fixed tree. The four round-4 methods were also replayed against `91fdc4c2904040d548b75900978c7de3c8c18af6` and produced six subtest failures while the quoted-runbook-satisfaction guard remained green, matching the corrected audit record. Entry and exit probes for ordinary quoted scalars, escaped quotes and embedded plain-scalar quotes remain clean; the remaining material plain-scalar review found E319-S2-R6-01. Focused tests pass 114/114; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 587/587. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 tracked files, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer. Per-alert isolation, pointer base, H007, stable finding codes, ordinary generation and held frontier digests otherwise remain intact.

Further leads: none beyond E319-S2-R6-01.

### Resolution: Ephoros alert-runbook annotations, step 2, round 6 -- 2026-08-21

E319-S2-R6-01 is resolved on the audit branch. Both quoted-scalar start
predicates now require YAML whitespace separation between a mapping colon or
sequence dash and the opening quote. A quote remains valid as the first
non-space character, but `plain:"text` and `-"text` remain plain-scalar
content and cannot hide a later alert or runbook pointer.

The two guard methods were observed red before repair: the focused suite ran
116 tests with eight subtest failures across both unseparated shapes, both
quote styles and both ownership gates. After repair, the focused suite passes
116/116, evolution and version propagation 23/23, marketplace prose 13/13,
root 104/104 and Hexaemeron 589/589. Protasis accepts both documents;
Imprimatur and per-file Brevitas accept the six named prose files; Promise
Machine reports 14 plugins and 14 copies clean; Phylax, Ephoros and Hypomnema
each exit 0 over their required trees. All other semantics, finding codes,
ownership, versions and held frontier digests are unchanged. No new leads.

## Ephoros alert-runbook annotations, step 2, round 7 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-R7-01; severity: medium; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`; finding: Neither lexer tracks an active multi-line plain scalar. A continuation line whose first non-space character is an unmatched quote is valid plain-scalar content, but `_yaml_quote_starts` opens quoted-scalar state and hides the following alert or runbook key, allowing missing E004 or H003 evidence to pass.; status: open

Scope: the complete folded tree `3b2d58955d483586f326ab68ed73994532a0d7bf..7114c05310bd95a072e4a3503d30096a40005d9c`. The two round-6 guard methods were run against `3588e21b3c46efa119db5b8df43375d90b3b5ce0` in memory and produced eight subtest failures across both unseparated shapes, both quote styles and both ownership gates; both methods pass against the fixed tree. The penultimate documented-subset review then reproduced E319-S2-R7-01 for both quote styles and both checkers: `- note: first` followed by an indented `"continued` is one valid plain-scalar specimen before a real alert, with a parallel top-level mapping before a real runbook pointer. Focused tests pass 116/116; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 589/589. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 tracked files, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer. Quote entry separation, quote exit and escape handling, block scalars, comments, suppression scope, per-alert isolation, pointer base, H007, stable finding codes, ordinary generation and held frontier digests otherwise remain intact.

Further leads: none beyond E319-S2-R7-01.

### Resolution: Ephoros alert-runbook annotations, step 2, round 7 -- 2026-08-21

E319-S2-R7-01 is resolved on the audit branch. Both bounded YAML lexers now
carry the key indentation of a supported inline plain scalar. More-indented
continuation content is consumed before quote-start recognition, while a
dedent ends the state before a later alert or runbook pointer. Comment lines
remain available to the existing YAML comment and suppression handling.

The two guard methods were observed red before repair: the focused suite ran
118 tests with four subtest failures across both quote styles and both
ownership gates. After repair, the focused suite passes 118/118, evolution
and version propagation 23/23, marketplace prose 13/13, root 104/104 and
Hexaemeron 591/591. Protasis accepts both documents; Imprimatur and per-file
Brevitas accept the six named prose files; Promise Machine reports 14 plugins
and 14 copies clean; Phylax, Ephoros and Hypomnema each exit 0 over their
required trees. All other semantics, finding codes, ownership, versions and
held frontier digests are unchanged. No new leads.

## Ephoros alert-runbook annotations, step 2, round 8 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-R8-01; severity: medium; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`; finding: Both checkers bind a multi-line plain `runbook` scalar from its first physical line before discarding its continuation. With a present decoy `runbooks/present.md`, the valid YAML value `runbooks/present.md extra` therefore satisfies E004 and passes H003 even though that actual pointer is neither the checked Markdown path nor a resolving target.; status: open

Scope: the complete folded tree `3b2d58955d483586f326ab68ed73994532a0d7bf..c578496aa8fa8b94e8a66a62cdce8c14b05b5016`. The two round-7 guard methods were run against `f95f35b90ed927d6c1ce44da1662c47f19221624` in memory and produced four subtest failures across both quote styles and both ownership gates; both methods pass against the fixed tree. The final documented block-YAML and folded-diff review then reproduced E319-S2-R8-01 with `runbook: runbooks/present.md` followed by a more-indented `extra`: YAML binds the folded value `runbooks/present.md extra`, Ephoros emits no E004, and Hypomnema emits no H003 when the first-line decoy exists. Focused tests pass 118/118; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 591/591. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 tracked files, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer. Lexer state transitions, suppression scope, per-alert isolation, pointer base, H007, stable finding codes, ordinary generation and held frontier digests otherwise remain intact.

Further leads: none beyond E319-S2-R8-01.

### Resolution: Ephoros alert-runbook annotations, step 2, round 8 -- 2026-08-21

E319-S2-R8-01 is resolved on the audit branch. Both bounded YAML passes now
fold more-indented continuation text into a supported plain `runbook` value
before Ephoros validates the annotation or Hypomnema resolves the pointer.
The first physical line can no longer stand in for the actual YAML value;
single-line pointers and folded pointers that name a real path remain clean.

The five guard methods were observed before repair: the focused suite ran 123
tests with four failures covering the E004 decoy, the H003 decoy and the two
valid-fold outcomes; the single-line guard was already clean. After repair,
the focused suite passes 123/123, evolution and version propagation 23/23,
marketplace prose 13/13, root 104/104 and Hexaemeron 596/596. Protasis accepts
both documents; Imprimatur and per-file Brevitas accept the six named prose
files; Promise Machine reports 14 plugins and 14 copies clean; Phylax,
Ephoros and Hypomnema each exit 0 over their required trees. All other
semantics, finding codes, ownership, versions and held frontier digests are
unchanged. No new leads.

## Ephoros alert-runbook annotations, step 2, post-cap closure verification -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: E319-S2-PC-01; severity: medium; file: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`; finding: The new plain-scalar fold drops blank physical lines and joins the next continuation with a space, although YAML preserves the blank as a line break. A present decoy `runbooks/present target.md` therefore makes E004 and H003 clean for the actual YAML value `runbooks/present\ntarget.md`.; status: open

This is an independent verification after the controller's eighth and final round, not a ninth round. The five round-8 guard methods were run against `9af605d8ff9e6a0b4af58ddbde96f2d9411a3091` in memory and produced four failures: the E004 and H003 decoys and both valid nonblank-fold outcomes were red, while the single-line case was already green. All five methods pass at `4983ed99b86226cda585e936ec9d812b70137d65`, so the exact nonblank-continuation mechanism in E319-S2-R8-01 is closed. Review of that fix then reproduced E319-S2-PC-01 with one blank line before the continuation: the checkers resolve a space-folded decoy while YAML binds a newline-containing scalar, so closure is incomplete. Focused tests pass 123/123; evolution and version propagation 23/23; marketplace prose 13/13; root 104/104; Hexaemeron 596/596. Promise Machine, Protasis, Imprimatur, per-file Brevitas, diff check and Phylax, Ephoros and Hypomnema tree lints exit 0. The committed and fresh Horos documents are byte-identical at 1,376 tracked files, 89 entries and none unreadable. The fix commit has a good local signature and exactly one required co-author and origin trailer.

Further leads: none beyond E319-S2-PC-01.

### Resolution: Ephoros alert-runbook annotations, post-cap closure -- 2026-08-21

E319-S2-PC-01 is resolved on the audit branch. The supported plain-runbook
fold now counts blank physical lines and inserts the corresponding line break
before the next continuation. Ephoros rejects a newline-containing annotation
path, while Hypomnema resolves the exact newline-containing YAML value rather
than a space-collapsed decoy. The existing single-line and nonblank-fold
guards remain clean.

The three new guard methods were observed red before repair: the focused
suite ran 126 tests with three failures covering E004, the H003 space decoy
and the exact H003 newline path. After repair, the focused suite passes
126/126, evolution and version propagation 23/23, marketplace prose 13/13,
root 104/104 and Hexaemeron 599/599. Protasis accepts both documents;
Imprimatur and per-file Brevitas accept the six named prose files; Promise
Machine reports 14 plugins and 14 copies clean; Phylax, Ephoros and Hypomnema
each exit 0 over their required trees. All other semantics, finding codes,
ownership, versions and held frontier digests are unchanged. No new leads.

## Ephoros alert-runbook annotations, step 2, final post-cap closure verification -- 2026-08-21

### Guard replay

This independent closure verification is not a ninth controller round.
The three E319-S2-PC-01 guards fail three times against
`69534e2149973cbcd043c7cdbc7ceee639c45b15` and pass 3/3 at
`6934de985613e126c6f30f423106935aa4493b56`. Direct comparison with Ruby's
YAML parser agrees for single-line values, ordinary nonblank folds, and one-
and two-blank-line folds. The E004 validator rejects newline-containing paths,
and H003 resolves the exact newline-containing value rather than its
space-folded decoy. E319-S2-R8-01 and E319-S2-PC-01 are closed.

### Regression gates

Focused tests pass 126/126; evolution and version propagation 23/23;
marketplace prose 13/13; root 104/104; Hexaemeron 599/599. Promise Machine
reports 14 plugins and 14 copies clean. Both Protasis checks, Imprimatur,
per-file Brevitas, diff check and the Phylax, Ephoros and Hypomnema tree lints
exit 0. The fresh and committed Horos documents are byte-identical at 1,376
tracked files, 89 entries and none unreadable. The fix has a good local
signature and exactly one required co-author and origin trailer.

### Verdict

Further leads: none. All recorded round-8 and post-cap findings are closed.

## Fiat delegation packets, step 1, round 1 -- 2026-08-21

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I320-S1-R1-01 | medium | `docs/fiat-delegation-packets-runbook.md:11` | The exit claims a captured red Horos currency check, but adding the two ordinary Markdown files changes only `counts.files_walked`. Horos `check` and the root currency guard compare classified entries, so replay with the parent boundary exits 0 and says the boundary matches. The runbook supplies no full-document comparison that can produce the claimed red. | open |
| I320-S1-R1-02 | medium | `docs/fiat-delegation-packets-runbook.md:75` | Protasis requires the final step to run the problem statement's demo path. The study defines a fresh run through study, runbook, implement, audit, prose, push, merge-step and integrate, but step 3 never names or requires that full-lifecycle demo. | open |
| I320-S1-R1-03 | medium | `docs/fiat-delegation-packets-runbook.md:38` | The step calls the study and runbook the durable decision record, while Hypomnema states that a study is a run artefact rather than a record. The planned Fiat evolution row does not exist in this step. | open |

### Evidence and gates

The receipted and tracked study and runbook are byte-identical. The parent
boundary records 1,376 tracked files and the fresh step tree records 1,378,
with the same 89 classified entries. Injecting the parent boundary into the
current Horos tree check exits 0; the regenerated committed boundary is
byte-identical to a fresh scan, with none unreadable. The signing requirement
is otherwise clear about local commits, exact trailers, pushed commits and
GitHub-created merges. Step commit
`bb0a19b69c9b905023deb25226b742a4572899ad` has a good local signature and
exactly one required co-author and origin trailer.

Both Protasis modes, Imprimatur, per-file Brevitas, diff check and the Phylax,
Ephoros and Hypomnema tree lints exit 0. Root tests pass 104/104, Hexaemeron
599/599, and Promise Machine reports 14 plugins and 14 copies clean.

### Risk-register disposition

`local-signature-gap` was reviewed and is closed for the step commit.
`remote-verification-gap` and `merge-origin-confusion` are not yet applicable
before push and merge. `packet-state-drift`, `artefact-drift`,
`protasis-grammar-drift`, `file-range-confusion`, `subprocess-control`,
`legacy-state-overclaim` and `path-escape` are not applicable to this
docs-and-boundary step; they remain obligations for steps 2 and 3.

Leads not pursued: none.

### Resolution: Fiat delegation packets, step 1, round 1 -- 2026-08-21

All three findings are resolved on the audit branch. I320-S1-R1-01 now names
the direct parent-versus-fresh whole-document comparison and its
`files_walked` evidence; it also states that `horos check .` and the legacy
root currency guard remain green because they compare classified entries.
I320-S1-R1-02 requires the named
`TestDelegationPacketLifecycle.test_fresh_run_emits_packets_through_integrate`
Step 3 demonstration to start in a fresh temporary repository and traverse
study through integration. I320-S1-R1-03 identifies the study and runbook as
run inputs and the Step 3 Fiat `EVOLUTION.md` generation row as the durable
decision home.

The controller and tracked runbooks remain byte-identical. Both Protasis
modes, Imprimatur and both per-file Brevitas checks are clean. Root tests pass
104/104, Hexaemeron 599/599 and Promise Machine reports 14 plugins and 14
copies clean. Phylax, Ephoros and Hypomnema each exit 0 over their required
trees, and the diff check is clean. No new leads.

## Fiat delegation packets, step 1, round 2 -- 2026-08-21

### Finding

| id | severity | evidence | round-2 verdict | status |
| --- | --- | --- | --- | --- |
| I320-S1-R2-01 | medium | `docs/fiat-delegation-packets-runbook.md:13` | I320-S1-R1-01 is partly closed: the proof block contains only two known-green entry checks and `scan --write`, so no executable comparison observes parent/fresh inequality and committed/fresh identity. Add the exact whole-document red and green commands. | open |
| I320-S1-R1-02 | medium | `docs/fiat-delegation-packets-runbook.md:83` | The final step now names the fresh lifecycle demo through integration. | closed |
| I320-S1-R1-03 | medium | `docs/fiat-delegation-packets-runbook.md:40` | The runbook now distinguishes run inputs from the future Fiat evolution record. | closed |

### Closure and gates

I320-S1-R1-02 and I320-S1-R1-03 are closed: Step 3 names a fresh
temporary-repository lifecycle demonstration through integration, and the
runbook now distinguishes run inputs from the Fiat evolution row that will
hold the decision. The tracked and controller study and runbook copies are
byte-identical. Direct reviewer replay establishes that the parent and fresh
whole documents differ at 1,376 versus 1,378 tracked files, while the current
committed and fresh documents are byte-identical at 89 entries and none
unreadable. Fix commit `81bcd6a87eca923852218e4ee2cdce49809b4add`
has a good local signature and exactly one required co-author and origin
trailer.

The focused boundary suite passes 4/4, root 104/104 and Hexaemeron 599/599;
Promise Machine reports 14 plugins and 14 copies clean. Both Protasis modes,
Imprimatur, both per-file Brevitas checks, diff check, Horos and the Phylax,
Ephoros and Hypomnema tree lints exit 0.

### Risk-register disposition

`local-signature-gap` remains closed for both step content commits.
`remote-verification-gap` and `merge-origin-confusion` remain inapplicable
before push and merge. The other seven study risks remain inapplicable to the
docs-and-boundary step and are held for steps 2 and 3.

Further leads: none beyond I320-S1-R2-01.

### Resolution: Fiat delegation packets, step 1, round 2 -- 2026-08-21

I320-S1-R2-01 is resolved on the audit branch. The Step 1 proof block now
creates a temporary evidence directory, reads the exact parent boundary with
`git show`, regenerates the current boundary, requires parent/current
inequality, saves that current document as fresh, regenerates again and
requires fresh/current identity before removing the temporary directory. It
then runs the two legacy entry-only checks and explicitly records that both
remain green rather than serving as the red evidence.

The executable sequence passes: the parent/current inequality and
fresh/current identity predicates both hold, `horos check .` reports a match,
and the focused boundary suite passes 4/4. The controller and tracked
runbooks remain byte-identical. Both Protasis modes, Imprimatur and both
per-file Brevitas checks are clean. Root tests pass 104/104, Hexaemeron
599/599 and Promise Machine reports 14 plugins and 14 copies clean. Phylax,
Ephoros and Hypomnema each exit 0 over their required trees, Horos is current
at 1,378 files, 89 entries and none unreadable, and the diff check is clean.
No new leads.

## Fiat delegation packets, step 1, round 3 -- 2026-08-21

### Closure

Zero findings. The Step 1 Horos proof block passes exactly as written under
fail-fast shell semantics: the parent/current comparison is unequal, the
second scan matches the saved fresh document, the temporary evidence directory
is removed, and the two documented legacy entry-only checks remain green.
I320-S1-R1-01, I320-S1-R1-02, I320-S1-R1-03 and I320-S1-R2-01 are closed.
The controller and tracked study and runbook copies are byte-identical.

### Gates

The focused boundary suite passes 4/4, root 104/104 and Hexaemeron 599/599;
Promise Machine reports 14 plugins and 14 copies clean. Both Protasis modes,
Imprimatur, both per-file Brevitas checks, diff check, Horos and the Phylax,
Ephoros and Hypomnema tree lints exit 0. A fresh Horos scan is byte-identical
to the committed document at 1,378 tracked files, 89 entries and none
unreadable. Fix `ff0d7a0130cd4d812ba8095358f163c0102d3cb1` has a good local
signature and exactly one required co-author and origin trailer.

### Risk-register disposition

`local-signature-gap` is closed for all three step content commits.
`remote-verification-gap` and `merge-origin-confusion` remain inapplicable
before push and merge. The other seven study risks remain inapplicable to the
docs-and-boundary step and are held for steps 2 and 3.

Further leads: none.

## Fiat delegation packets, step 2, round 1 -- 2026-08-21

### Findings

Two findings remain open.

I320-S2-R1-01 (medium), `protasis-grammar-drift`:
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1409-1411` defines private
source selectors that are narrower than the Protasis grammar which accepts the
study and runbook. A runbook step heading with trailing spaces passes the
Protasis runbook check but `source_runbook_step` refuses it as having no exact
source block. A ` ``` risk-register` opener likewise passes the Protasis study
check but `source_risk_register` reports no fenced register. The packet builder
must select every source form accepted by the authoritative grammar, or the
authoritative checker and selector must share one grammar.

I320-S2-R1-02 (medium), `path-escape`: the Warden packet concatenates mutable
`audit.stacked_suffix` at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1616-1624` without validating
the resulting ref. Setting the suffix to `" bad"` emits a `stacked_branch`
which `git check-ref-format --branch` rejects. Validate the complete emitted
branch name before returning the packet.

### Review evidence

The four total envelopes and exact Surveyor, Mason, Warden and Scribe brief
schemas were reviewed against their agent contracts. Receipt digests bind the
study and runbook source bytes; mutation, duplicate-selector, missing-source,
containment, input-size and legacy cases have focused guards. The current run
is deliberately legacy: `hexctl next` emitted the held audit directive with
the current state digest, `agent: null` and `brief: {}` because its study
receipt predates the new digest fields.

Scribe uses the exact two-dot PR-base-to-step-branch range, NUL-delimited Git
output, containment checks, sorted unique files, a 500-path cap and bounded
output. Git calls use fixed argument vectors with `shell=False`; direct fake-Git
probes confirmed fail-visible timeout and output-cap behaviour. Packet
reconstruction is state-bound and deterministic. No issue was found in those
mechanisms.

### Gates and provenance

The packet-focused suites pass 159/159 and the full Hexaemeron suite 610/610;
root tests pass 104/104. Promise Machine reports 14 plugins and 14 copies
clean. Imprimatur and all four per-file Brevitas checks exit 0. Phylax,
Ephoros and Hypomnema tree lints, Horos and the folded diff check exit 0.
Source commit `d98010622f18f40ded9dccc10e60b04bcfaeeb19` has a good local
signature and exactly one required co-author and origin trailer.

### Risk-register disposition

`packet-state-drift`, `artefact-drift`, `file-range-confusion`,
`subprocess-control` and `legacy-state-overclaim` are covered by the reviewed
implementation and green evidence. `protasis-grammar-drift` and `path-escape`
remain open as I320-S2-R1-01 and I320-S2-R1-02. `local-signature-gap` is closed
for the step source commit. `remote-verification-gap` and
`merge-origin-confusion` are inapplicable before push and merge.

Further leads: none beyond I320-S2-R1-01 and I320-S2-R1-02.

## Fiat delegation packets, step 2, round 1 resolution -- 2026-08-21

Both findings are closed.

### Fixes

- I320-S2-R1-01: the source selectors now use the step-heading grammar and
  fence-info split accepted by Protasis. Trailing-space step headings and
  spaced `risk-register` openers retain their exact source bytes. Fenced
  decoys remain excluded, and Protasis remains the shape authority.
- I320-S2-R1-02: the controller assembles the complete Warden stacked branch,
  then runs bounded, no-shell `git check-ref-format --branch` on that value.
  An invalid mutable suffix stops packet emission with the named
  `stacked_branch` refusal.

### Red-to-green evidence

The two focused guards were red before the fix: selector parity exited with
one error, and the invalid suffix guard failed because the controller emitted
the malformed ref. They now pass 2/2. The focused suite passes 161/161, the
root suite 104/104 and Hexaemeron 612/612. Promise Machine reports 14 plugins
and 14 copies clean. Both Protasis modes pass. The remaining Step 2 prose,
tree and diff gates pass.

### Boundary

No Step 3 signing, remote, version or publication rule is changed.

## Fiat delegation packets, step 2, round 2 -- 2026-08-21

### Verdict

Zero findings. I320-S2-R1-01 and I320-S2-R1-02 are closed, with no further
leads.

### Red-to-green evidence

The two round-1 guards were replayed unchanged against pre-fix commit
`6d9a69bf90eec1b353d417d133ba7f01036134e7`: selector parity errored on the
Protasis-accepted trailing-space heading, and the Warden guard failed because
the invalid assembled branch was emitted. The same guards pass 2/2 at fix
`0f9ec96217ad917b5aa9bbb99eaa9d81cf9f62ab`. The selector test also exercises
the Protasis-accepted spaced `risk-register` opener. The fix commit has a good
local signature and exactly one required co-author and origin trailer.

### Bounded review

The folded packet diff was rechecked against the four agent contracts and the
study risk register. The exact Surveyor, Mason, Warden and Scribe schemas,
total null envelope, state and artefact binding, duplicate selectors,
containment and size caps, deterministic reconstruction, legacy null packet,
Scribe range and sort, and bounded no-shell Git remain intact. The complete
Warden ref is now checked before emission, and the source selectors accept the
same spacing forms as Protasis without admitting fenced decoys.

`packet-state-drift`, `artefact-drift`, `protasis-grammar-drift`,
`file-range-confusion`, `subprocess-control`, `legacy-state-overclaim` and
`path-escape` are closed by the reviewed implementation and evidence.
`local-signature-gap` is closed for the fix. `remote-verification-gap` and
`merge-origin-confusion` remain inapplicable before push and merge.

### Gates

The two focused guards pass 2/2, the packet-focused suites 161/161, the full
Hexaemeron suite 612/612 and root tests 104/104. Promise Machine reports 14
plugins and 14 copies clean. Both Protasis modes, Imprimatur, all four
per-file Brevitas checks, Phylax, Ephoros, Hypomnema, Horos and the folded diff
check exit 0.

Further leads: none.

## Fiat delegation packets, step 3, round 1 -- 2026-08-21

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I320-S3-R1-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1003-1015,1194-1238` | Implement and push validate the declared branch name and the supplied base-to-head range separately, but never require the supplied head to be the declared step branch tip. A different signed descendant of the base can therefore be receipted as that branch and pushed as its range. Resolve the declared branch and require exact equality with the supplied head; bind the pushed PR head to the same SHA. | open |
| I320-S3-R1-02 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1315-1355,1361-1412` | `merge-step` and `integrate` require only a valid GitHub verification response for the supplied value. They do not establish that it is the named step-to-run or run-to-base merge, or that it belongs to the recorded PR. Any GitHub-valid commit in the selected repository can advance either receipt. Bind each receipt to the exact PR, expected head/base and resulting merge SHA. | open |
| I320-S3-R1-03 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1194-1250,1375-1411,1712-1756` | Repository identity and publication identity are separate unchecked claims. `gh repo view` supplies an owner/name which is not cross-checked with the target remote, while `--pr-url` is any non-empty text and is not checked against that repository. The fresh test passes in a temporary repository with the fake repository `wildcat-finance/example` while receipting `https://x/...`. Bind the GitHub repository to the target and require the PR response and URL to name that repository and the expected refs. | open |
| I320-S3-R1-04 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1731-1756` | GitHub verification does not validate each input with `COMMIT_RE` before placing it in the endpoint and refusal text. A direct fake-GitHub probe accepted `not-a-sha`; a token-shaped value can be repeated in an API refusal. Require one full SHA before any command or error is built and keep unvalidated values out of diagnostics. | open |
| I320-S3-R1-05 | medium | `plugins/hexaemeron/tests/test_hexctl.py:789-838` | The named fresh lifecycle calls `to_steps` before its first packet assertion, so it neither observes the study and runbook directives nor proves second-process reconstruction at each transition. It also uses arbitrary commit labels and unrelated PR URLs accepted by the fake binaries. Extend the proof from the first study directive through every transition with repository-, ref- and SHA-realistic evidence. | open |

### Independent probes

The local range reader refuses empty, malformed, non-descendant and oversized
ranges, verifies every enumerated intermediate commit, counts both exact
trailers once and discards raw signature output. Its missing control is the
relation between that range head and the branch it is said to represent.

The GitHub reader rejects malformed response JSON, missing or mismatched
response SHAs, false verification, every non-valid reason, tool failure,
timeout and oversized output. Against its shipped fake boundary,
`verify_github_commits` returned `['not-a-sha']`. The same boundary accepts a
repository name without a target-remote comparison. Fixed argv, target cwd,
`shell=False`, the 30-second timeout and 2 MiB output cap remain intact.

The current pre-generation run remains compatible: `hexctl next` emits the
held Step 3 audit directive with its state digest and explicit `agent: null`,
`brief: {}`. Packet, artefact, Protasis and path controls from Step 2 remain
unchanged.

### Publication and gates

The Fiat release is an ordinary `fiat-v4.9.1` generation. Its
`receipted-lint-rounds` revision, frontier text and digest remain unchanged;
the held `load_state` job is not displaced. The Hexaemeron package, both plugin
manifests and both marketplace records agree on `1.5.2`. Source commit
`cc7e81f7789d4748abac678dfbd464c2c70702c7` has a good local signature and
exactly one required co-author and origin trailer.

The Step 3 focused set passes 196/196, the named lifecycle 1/1, root tests
104/104 and Hexaemeron 616/616. Promise Machine reports 14 plugins and 14
copies clean. Both Protasis modes, Imprimatur, all per-file Brevitas checks,
Phylax, Ephoros, Hypomnema, Horos and the folded diff check exit 0.

### Risk-register disposition

`file-range-confusion` and `local-signature-gap` remain open through
I320-S3-R1-01. `merge-origin-confusion` remains open through I320-S3-R1-02.
`remote-verification-gap` remains open through I320-S3-R1-03 and
I320-S3-R1-04. `subprocess-control` remains open only for the unvalidated
GitHub value and diagnostic in I320-S3-R1-04; its execution controls pass.
`packet-state-drift`, `artefact-drift`, `protasis-grammar-drift`,
`legacy-state-overclaim` and `path-escape` are clean in the folded diff.

Further leads: none beyond I320-S3-R1-01 through I320-S3-R1-05.

## Fiat delegation packets, step 3, round 1 resolution -- 2026-08-21

All five findings are closed.

### Fixes

- I320-S3-R1-01: implement and push now resolve the declared step branch and
  require its tip to equal the supplied head before verifying the exact owned
  range. Push also requires the PR head OID to equal that verified tip.
- I320-S3-R1-02: `merge-step` and `integrate` inspect the recorded PR and
  require the expected head, base, merged state and exact merge OID before
  accepting GitHub verification.
- I320-S3-R1-03: the repository is derived from the target's GitHub origin,
  cross-checked against `gh repo view`, and required on the supplied and
  returned PR URLs.
- I320-S3-R1-04: every GitHub-bound value must be one full commit SHA before a
  command or SHA-bearing refusal is built. Invalid input gets a generic
  refusal and reaches no `gh` process.
- I320-S3-R1-05: the named fresh lifecycle now starts at `init`, observes the
  Surveyor, runbook, Mason, Warden and Scribe transitions, compares two fresh
  `next` processes at every transition, and uses full SHAs, GitHub PR URLs and
  fake branch/PR topology bound to the target repository.

### Evidence

Seven focused guards cover branch-tip binding, pushed PR identity,
target-origin identity, pre-command SHA rejection, and both merge topologies.
They were red before the fix (the initial bounded run failed 6/6; the separate
push-tip case extends the same branch control) and now pass 7/7. Versions and
the held Fiat frontier are unchanged. No remote operation was performed.

## Fiat delegation packets, step 3, round 2 -- 2026-08-21

### Finding

I320-S3-R2-01 (high), open at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1444-1451`: integration
inspects the expected run-branch and base names and the supplied merge OID,
but passes `expected_head_sha=None`. A merged PR carrying a different head OID
therefore completes the run. Bind the integration PR head OID to the actual
merged run-branch tip, or to equivalent stored topology evidence, before
accepting the merge.

### Replay and review

Seven product guards replayed against pre-fix `cc7e81f7789d4748abac678dfbd464c2c70702c7`
fail 7/7 and pass 7/7 at `afd180dae569a7a24df1c8e5d624685f6c5e56d8`.
They cover declared implementation and push tips, cross-repository PRs, target
origin identity, pre-command full-SHA rejection and both recorded merge
topologies. The fresh lifecycle proof passes 1/1 and now starts at `init`,
observes every directive and checks two-process reconstruction; this closes
R1-05's former evidence-shape gap rather than a previously failing runtime
predicate.

The residual probe supplied the correct integration PR URL, run-branch name,
base name, merged state and merge OID, but a deliberately different 40-byte
head OID. `done integrate` returned 0 and marked the run complete. The other
four round-1 mechanisms are closed. Repository parsing, PR identity, step PR
head binding, full-SHA validation and generic secret-safe refusals showed no
further bypass in this round.

### Gates and risk disposition

The Step 3 focused set passes 203/203, the named lifecycle 1/1, root tests
104/104 and Hexaemeron 623/623. Promise Machine reports 14 plugins and 14
copies clean. Both Protasis modes, Imprimatur, all per-file Brevitas checks,
Phylax, Ephoros, Hypomnema, Horos and the folded diff check exit 0. Fix commit
`afd180dae569a7a24df1c8e5d624685f6c5e56d8` has a good local signature and
exactly one required co-author and origin trailer.

`merge-origin-confusion` and `remote-verification-gap` remain open only through
I320-S3-R2-01. The other eight risk ids are clean in the folded diff.

Further leads: none beyond I320-S3-R2-01.

## Fiat delegation packets, step 3, round 2 resolution -- 2026-08-21

### Fix

I320-S3-R2-01 is closed.

- Before integration inspects the PR, the controller runs bounded, no-shell
  `git ls-remote --refs origin` for the exact recorded run-branch ref.
- It accepts exactly one tab-separated full SHA and matching ref. An absent,
  duplicate, malformed or differently named result stops the receipt.
- The integration PR's `headRefOid` must equal that remote tip alongside the
  existing repository, URL, head name, base name, merged state, merge OID and
  GitHub verification checks.

### Evidence

The wrong-head lifecycle guard was red before the fix: a PR with every other
field correct completed the run. It now refuses. The focused positive and
absent, malformed and duplicate remote-ref cases pass, and the fresh lifecycle
uses the same remote topology. Versions and the held frontier are unchanged;
no remote mutation was performed.

## Fiat delegation packets, step 3, round 3 -- 2026-08-21

### Finding

I320-S3-R3-01 (high), open at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1444-1453`: integration now
binds the PR head to the remote run-branch tip, but does not bind that tip to
the last step merge recorded by the controller. After recording step merge
`eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee`, a probe replaced the remote tip
and PR head with `8888888888888888888888888888888888888888`; every other PR
and verification field matched, and `done integrate` returned 0. Require the
remote run tip to equal the final recorded step merge before integration.

### Replay and gates

The R2 wrong-head guard is red against
`afd180dae569a7a24df1c8e5d624685f6c5e56d8` and green at
`5f076d66e5c37435f74dd8dd7127b794eedf748f`. Remote-tip parsing accepts one
exact full SHA and matching ref and refuses absent, malformed and duplicate
results. Repository, PR, local signature, trailer, GitHub predicate and
secret-safe error controls show no further bypass in this bounded review.

The Step 3 focused set passes 205/205, the lifecycle 1/1, root tests 104/104
and Hexaemeron 625/625. Promise Machine reports 14 plugins and 14 copies
clean. Both Protasis modes, Imprimatur, every per-file Brevitas check, Phylax,
Ephoros, Hypomnema, Horos and the folded diff check exit 0. Fix commit
`5f076d66e5c37435f74dd8dd7127b794eedf748f` has a good local signature and
exactly one required co-author and origin trailer.

`merge-origin-confusion` and `remote-verification-gap` remain open only through
I320-S3-R3-01. The other eight risk ids are clean in the folded diff.

Further leads: none beyond I320-S3-R3-01.

## Fiat delegation packets, step 3, round 3 resolution -- 2026-08-21

### Fix

I320-S3-R3-01 is closed. `done integrate` reads the last step's recorded
`merge_commit`, requires it to be a full SHA, and refuses unless it equals the
exact remote run-branch tip. The existing PR inspection then requires its
`headRefOid` to equal that same tip before the integration merge can be
receipted. The terminal receipt records both `run_head` and
`final_step_merge`, which must therefore be identical.

### Evidence

The divergent recorded-step/remote-tip guard was red before the fix: a remote
tip and PR head that agreed with each other but not with the last step receipt
completed the run. It now refuses. The fresh lifecycle records the last step
merge as both terminal head fields and remains green. Versions and the held
frontier are unchanged; no remote mutation was performed.

## Fiat delegation packets, step 3, round 4 -- 2026-08-21

### Verdict

Zero findings. I320-S3-R3-01 is closed, and no further leads remain.

### Replay and bounded review

The recorded-step/remote-tip divergence guard is red against
`5f076d66e5c37435f74dd8dd7127b794eedf748f` and green at
`e037a895cda39a1505d5c98e2c16fd55b1ea2bf8`. Integration now requires one full
SHA to be identical across the final recorded step merge, the exact remote
run-branch tip and the integration PR head OID. The PR repository, URL, head
and base names, merged state and merge OID remain independently bound, and the
merge SHA still requires GitHub's exact valid verification result.

The final bounded signing review found no gap in the owned local ranges,
intermediate commit enumeration, branch-tip checks, exact trailer counts,
local signature checks, remote repository identity, pushed PR topology,
step-merge topology, input validation, resource caps, no-shell execution or
secret-safe refusals. Legacy null packets, source-bound delegation and the
published generation and frontier identities remain unchanged.

### Gates

The Step 3 focused set passes 206/206, the lifecycle 1/1, root tests 104/104
and Hexaemeron 626/626. Promise Machine reports 14 plugins and 14 copies
clean. Both Protasis modes, Imprimatur, every per-file Brevitas check, Phylax,
Ephoros, Hypomnema, Horos and the folded diff check exit 0. Fix commit
`e037a895cda39a1505d5c98e2c16fd55b1ea2bf8` has a good local signature and
exactly one required co-author and origin trailer.

All ten study risk ids are clean in the folded Step 3 diff.

Further leads: none.

## Fiat delegation packets, post-push merge incident -- 2026-08-21

### Incident

The live controller remained in `integrate` after the reported
`done merge-step --step 1 --merge-commit 570ad2...` attempt refused with
`recorded step pull request has no verified head`. No controller transition
occurred. Work stopped at that receipt; this repair did not retry it.

### Cause and fix

- Step pull requests created before the verification receipt shipped can name
  the exact PR but carry no `verified_commits` or `github_verified` list.
- A signed repair committed after push can also make those recorded lists
  stale even though the PR now names the repaired head.
- At merge time the controller now inspects the exact recorded PR and merged
  topology, resolves the exact remote step-branch head, and requires both to
  agree. When the push evidence is missing or stale, it verifies every local
  commit and exact trailer in the recorded `pr_base..head` range, then requires
  GitHub `verified: true` with `reason: valid` for every SHA. Only that earned
  evidence becomes the merge receipt's `effective_push`; the old push receipt
  is not rewritten.

### Red-to-green evidence

The missing-legacy-evidence and signed-post-push-head guards both failed on the
old controller and now pass. Invalid local signature, invalid GitHub
verification, remote/PR head disagreement and PR topology mismatch all refuse.
The ordinary lifecycle records `repaired: false`. Versions and the held
frontier are unchanged, and no controller or remote state was mutated.
## Hermes rule corpus, step 1, round 1 -- 2026-08-21

The committed non-Solidity diff has no open finding. Status: clean.

The Pashov pair did not run: the `security_suite` receipt records a waiver
because the run ships Python, JSON and Markdown and creates or changes no
Solidity, contract or Foundry project. Phylax, Ephoros and Hypomnema each
exit 0 over `plugins`, `tests` and the document set. The root suite passes
104/104 and the Hermes suite 14/14. Protasis is clean over both artefacts and
Imprimatur scores each 100/100.

The look the lints cannot do covered the three risk-register concerns this
step can carry. On `frontier-displacement`: the study states the displacement
in its assumptions, its amendment, its risk register and item 12, and the
runbook puts the single epoch row and its reopening text in step 6. The body
of the study still describes two ledger rows where the amendment describes
one; that is the append-rather-than-edit rule the spec contract states, and
the amendment carries the correction, so it is reviewed rather than fixed. On
`successor-judgement`: neither document names the successor frontier, which
matches the study's position that the choice is an end-of-run judgement
against the run's own evidence. On `cli-break` and the ten remaining
concerns: not reachable from a Markdown and boundary-counter diff.

One in-step fault, found before this round and fixed at its cause. The study
quoted the rolling-job marker verbatim while describing the constraint that
governs it, and `test_rolling_fiat_jobs_exist_only_in_plugin_landing_readmes`
scans every tracked Markdown file for that literal, so the document tripped
the guard it was describing. The detector cannot tell a quotation from a
declaration and should not try; the sentence now names the line without
reproducing its marker. The existing test is the guard, so no new one was
written.

The boundary regeneration moved `files_walked` from 1,360 to 1,369 with the
entry set unchanged at 89. Two of the nine are this step's documents. The
other seven are the Hypomnema runbook fixtures that landed after that round
wrote its boundary, which is why its own log reports 1,360 beside them.

Leads not pursued: the boundary currency guard compares entry sets and not
the counts beside them, so a stale `files_walked` ships without a test
noticing, as it just did. Correcting it here was a side effect of following
the regeneration rule rather than a fix, and widening that guard belongs to
Horos rather than to a Hermes corpus run.

## Hermes rule corpus, step 2, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S2-R1-01; severity: low; file: `plugins/hermes/skills/hermes/scripts/hermes.py`; finding: The header check named the three record classes in its own tuple, so a schema that grew a fourth class would report the corpus key holding it as an unknown top-level field rather than validating its records.; status: fixed in this round

The Pashov pair did not run under the recorded waiver. Phylax, Ephoros and
Hypomnema each exit 0. The root suite passes 104/104 and the Hermes suite
32/32, of which 18 are new this step. `corpus --validate` reports 28 myths and
40 references with no fault.

The review read the whole validator against the risk register. On
`corpus-schema-drift`: records are lists rather than objects keyed by id,
because `json.load` drops a duplicate key silently and a duplicate rule id has
to be a refusal; the duplicate, unknown-field, missing-field, bad-pattern and
unimplemented-token cases each have a test. On `citation-network`: the new code
imports nothing that can open a socket and the citations are inert strings; the
`https` shape check is a format rule, not a fetch. On `binding-digest`: the
`hermes.py` digest in the Promise Machine coverage moved twice in this step,
once for the implementation and once for the round's fix, and the file was
edited by substring replacement rather than reserialised, which is what keeps
the diff at two lines instead of 1,908. On `citation-shape`: the extraction
counts footnote definitions, and the test pins REF-25 at one entry because the
source states it both as a line-initial citation and as a definition.

One candidate finding was investigated and rejected. The nested shape tokens
(`source`, `verified_on`, `scope`) are read out of the schema, which looks like
a cycle a malformed schema could ride into unbounded recursion. It cannot: each
level recurses only when the value at that level is an object, so the walk is
bounded by the nesting of the data and JSON cannot express infinite nesting. A
depth limit and its test were written, shown not to fire, and removed rather
than kept as a guard against a fault that has no reachable path. Deeply nested
input would exhaust the recursion limit inside `json.loads` before the
validator saw it, and the corpus is in-tree data rather than caller input.

Leads not pursued: the corpus records were produced by a throwaway extractor
run against the pinned source, which cross-checked every citation's footnote
URL against its table URL and found all 40 in agreement. That extractor is not
committed, so `transcription-fidelity` rests on counts, id shape and reference
resolution rather than on text equality with the source. Committing an
extractor and asserting it reproduces the committed bytes would close the gap
for the mechanically derivable fields. The runbook does not ask for it, and
adding it here would be scope the step did not carry; it belongs to a later
frontier judgement.

## Hermes rule corpus, step 2, round 2 -- 2026-08-21

Round 1's fix introduced no regression and this round found nothing. Status:
clean.

Phylax, Ephoros and Hypomnema each exit 0 against the fixed tree. The root
suite passes 104/104 and the Hermes suite 32/32. `corpus --validate` reports
28 myths and 40 references with no fault, at corpus digest `0692e53d` and
source digest `297c926d`, so neither the data nor the pinned document moved
while the validator was corrected.

The second look re-read the fix itself. Deriving the record classes from the
schema means the header check and the record walk now read one declaration
rather than two, so a class added to the schema cannot be a class the header
rejects. Its guard adds a fourth class in a temporary copy and requires the
corpus holding it to validate.

Leads not pursued: the extractor gap recorded in round 1 stands unchanged.

## Hermes rule corpus, step 3, round 1 -- 2026-08-21

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` | TRN-07's scope floored at Cancun. That rule is the chain-capability check itself, so the floor refused it on exactly the targets it exists to protect: a Paris deployment is where somebody most needs to be told that bytecode reaching `TLOAD` will fail. | fixed in this round |
| S3-R1-02 | medium | `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` | STO-12 mapped to `storage-load-caching`. Its saving is fewer `SSTORE`s, and no Hermes class names that, so the mapping was the nearest-sounding one rather than a real one. Now null. | fixed in this round |
| S3-R1-03 | low | `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` | MEM-09 mapped to `calldata-memory`. Memory-expansion discipline and bounds checking on attacker-controlled offsets are neither a parameter-location change nor a copy removal. Now null. | fixed in this round |

The Pashov pair did not run under the recorded waiver. Phylax, Ephoros and
Hypomnema each exit 0. The root suite passes 104/104 and the Hermes suite
42/42. `corpus --validate` reports 62 rules, 28 myths and 40 references clean.

The review read all 62 class assignments and all 62 scopes one by one, which is
what the study's risk register asks of the two authored fields. Three were
wrong and are fixed above. The rest hold, and the reasoning worth keeping is
this: `storage-packing` takes the rules that move a storage representation,
because that is the Hermes class whose gate already expects a declared layout
change; `control-flow` takes STO-13, STO-14 and STO-21, all of which add or
reorder a branch around a write; and `calldata-memory` keeps MEM-07 and MEM-16
on the strength of its catalogue row naming needless copies, which is what both
rules remove.

S3-R1-02 is worth more than its severity. Hermes has twelve classes and none
of them names a reduction in the number of storage writes, so STO-12, a P0
grade A rule and one of the most valuable in the source, cannot be run as a
candidate at all. The corpus made that hole visible by refusing to let it be
papered over. It is a candidate for the successor frontier rather than
something to fix by inventing a thirteenth class inside a transcription step,
which the study's constraints forbid.

31 of the 62 rules now name no class. That is the honest count: twelve
measurement rules constrain how a run is conducted, seven transient-storage
rules have no class at all, and the rest are accounting or collection
architecture. The count is asserted by a test so that a later change cannot
quietly map one of them to something plausible.

The obligations were read in full, 37 across the group. Each is an exact
substring of its own rule's statement, checked by a test rather than by eye.
One is a mechanism sentence rather than an instruction: STO-03's "updating one
packed field requires loading, masking, and rewriting the shared slot" matched
the requirement-verb heuristic through a descriptive "requires". The heuristic
keeps it and the schema now records the false-positive class, because the cost
is an operator explaining a mechanism in one sentence and the alternative is a
field that is part derived and part hand-curated with no record of which is
which.

Leads not pursued: the step 2 extractor lead is now closed for the transcribed
fields, since `statement`, `title`, `priority`, `evidence_grade`, `automation`
and `references` are each compared against the pinned source by test. The
authored fields cannot be closed that way and stay a reading task.

## Hermes rule corpus, step 3, round 2 -- 2026-08-21

Round 1's three fixes introduced no regression and this round found nothing.
Status: clean.

Phylax, Ephoros and Hypomnema each exit 0. The root suite passes 104/104 and
the Hermes suite 42/42. `corpus --validate` is clean at 62 rules.

The second look re-read the three fixes and the tests now holding them. TRN-07
floors at Homestead with its reason naming why it sits outside the transient
group, and a test asserts both that and the Cancun floor on TRN-01 through
TRN-06, so the exception cannot spread by accident. STO-12 and MEM-09 carry
null and are named in the unclassed test alongside the count, now 31 of 62, so
neither can be quietly reclassified later. 31 rules remain selectable as
candidates.

Leads not pursued: the class-vocabulary hole recorded in round 1 stands as a
successor-frontier candidate.

## Hermes rule corpus, step 4, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S4-R1-01; severity: medium; file: `plugins/hermes/skills/hermes/references/gas-rule-corpus.json`; finding: MEM-12 mapped to `hashing-encoding`. The rule states its own implementation is scratch-memory `KECCAK256`, and Gate 2 already refuses added assembly outside the `assembly` class, so a candidate declared under that mapping would have been refused every time it was attempted. Now `assembly`.; status: fixed in this round
- id: S4-R1-02; severity: medium; file: `plugins/hermes/skills/hermes/references/gas-rule-corpus.json`; finding: DEP-07 and DEP-08 floored at Shanghai on the strength of EIP-3860. Both rules hold wherever EIP-170's runtime limit applies, so the floor refused correct advice on every earlier fork. The same shape as step 3's TRN-07 finding. Now floored at Homestead with the initcode half named in the reason.; status: fixed in this round

The Pashov pair did not run under the recorded waiver. Phylax, Ephoros and
Hypomnema each exit 0. The root suite passes 104/104 and the Hermes suite
49/49. `corpus --validate` is clean at 120 rules, 28 myths and 40 references,
and a test now asserts the corpus id set equals the source's rather than only
the count.

S4-R1-01 is the more useful of the two, because it is the first case where the
class mapping had to be decided against an existing gate rather than against a
description. Gate 2 refuses a candidate that adds assembly under any class but
`assembly`, so a rule whose own statement names an assembly implementation has
only one correct mapping whatever its subject matter is. That reading was
applied across the group: MEM-06, MEM-10, MEM-11, MEM-13, CTL-18 and all
fourteen YUL rules take `assembly` for the same reason.

CTL-13 was examined under the same test and kept as `loop-arithmetic`. Its
canonical implementation is Uniswap v3's tick bitmap, whose `BitMath` is
ordinary Solidity, so a candidate under it does not have to add assembly and
the mapping does not set up a refusal.

The review read all 58 assignments and all 58 scopes. 62 of the 120 rules now
name a class and 58 do not. All twelve DEP rules are null and carry
`architecture` as their kind, all fourteen YUL rules take `assembly`, and a
bidirectional test holds the mapping from the other side: every class the
harness knows is named by at least one rule, so the vocabulary is not
over-broad even though it is plainly under-broad.

The unclassed CTL and EXT rules are the ones worth naming, because unlike DEP
they are real source changes with measurable savings that no class describes:
removing a generic SafeMath wrapper, omitting a redundant zero initialisation,
batching, pull settlement, and adopting a mature safe-transfer implementation.
With STO-12 from step 3 they are the evidence behind the successor-frontier
candidate.

Leads not pursued: the class vocabulary itself. Twelve classes cover 62 of the
120 documented rules, and widening them is a change to the harness's public
interface that the study's constraints put out of scope for this run.

## Hermes rule corpus, step 4, round 2 -- 2026-08-21

Round 1's two fixes introduced no regression and this round found nothing.
Status: clean.

Phylax, Ephoros and Hypomnema each exit 0. The root suite passes 104/104 and
the Hermes suite 49/49. `corpus --validate` is clean at 120 rules.

The second look re-read both fixes and the guards now holding them. MEM-12
takes `assembly` and its guard asserts the mapping beside the word
`scratch-memory` in the rule's own statement, so the reason travels with the
assertion. DEP-07 and DEP-08 floor at Homestead and their guard requires
EIP-3860 to stay named in the reason, so the initcode half of each rule cannot
quietly disappear from the record while the floor moves. `hashing-encoding`
remains reachable through MEM-14, which is what keeps the bidirectional
mapping test meaningful after MEM-12 moved.

Leads not pursued: the class vocabulary, unchanged from round 1.

## Hermes rule corpus, step 5, round 1 -- 2026-08-21

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | high | `plugins/hermes/skills/hermes/scripts/hermes.py` | A run directory sealed by the previous Hermes carries neither `corpus_sha256` nor `forge_config`, and Gate 2 read both by subscript. An operator resuming against an older baseline got an unhandled `KeyError` traceback rather than a refusal with an exit code, which is the one failure mode a fail-closed harness must not have. | fixed in this round |
| S5-R1-02 | medium | `plugins/hermes/skills/hermes/scripts/hermes.py` | `resolve_scope` indexed `fork_order` for the rule's floor without checking the floor was in it, so a corpus fault escaped as an uncontrolled `ValueError`. Unreachable through `verify`, because validation runs first; reachable at the function boundary, which is where the guard now sits. | fixed in this round |
| S5-R1-03 | low | `plugins/hermes/skills/hermes/scripts/hermes.py` | The rejected-rule citation scan was case-sensitive, so the same citation written in lower case went unnoticed. The refusal now matches either case and names the canonical id beside what was written. | fixed in this round |

The Pashov pair did not run under the recorded waiver. Phylax, Ephoros and
Hypomnema each exit 0. The root suite passes 104/104 and the Hermes suite
71/71, of which 22 are new this step.

The review drove the new helpers adversarially rather than reading them. Six
probes: a rejected-rule id inside an obligation answer, the same in lower case,
an obligation answer at 19, 20 and 21 characters against the 20-character
minimum the existing rationale flag already uses, an obligation index of zero
and of minus one, an answer supplied to a rule that states no obligation, and a
`fork_order` with the rule's floor removed. Four refused correctly, one refused
by design and case-sensitively, and the last produced the S5-R1-02 traceback.
S5-R1-01 came out of asking what a run directory from the previous version
looks like.

One thing the round changed about method rather than code. S5-R1-02's first
guard test drove the fault through `verify` and passed for the wrong reason:
`validate_corpus` catches the same corpus first and refuses with its own
message, so the test proved validation worked and said nothing about the guard.
It is now a direct call on `resolve_scope`, which is where the guard applies.
A guard test that cannot fail without its fix is the whole point of writing one.

The budget in the study's item 10 was measured, not asserted, and measuring it
found a defect. The suite had grown to 82 cases in 34.5 seconds against a
25-second ceiling. The cause was not the new cases: `CorpusGateTests` inherited
`HermesHarnessTests`, so all fourteen harness cases ran a second time under a
`verify` the subclass had overridden. The fixture is now a plain mixin that is
not itself collected, and the suite runs 71 cases in 23.9 seconds. Corpus
validation runs in 0.04 seconds against its one-second ceiling.

Leads not pursued: the 20-character minimum for an obligation answer is
inherited from the existing rationale flags rather than derived from anything.
It stops an empty field and nothing more, which is what the boundary language
in the new promise says out loud.

## Hermes rule corpus, step 5, round 2 -- 2026-08-21

Round 1's three fixes introduced no regression and this round found nothing.
Status: clean.

Phylax, Ephoros and Hypomnema each exit 0. The root suite passes 104/104 and
the Hermes suite 71/71 in 24.4 seconds, inside the 25-second ceiling. Corpus
validation is clean at 120 rules.

The three probes that produced round 1's findings were re-run against the fixed
tree. A rejected-rule citation is refused in either case and the refusal names
the canonical id beside what the operator wrote. A `fork_order` missing a rule's
floor is refused as `corpus/invalid` rather than raising. The shipped corpus
reports no fault, so neither fix moved the data.

The stale-baseline guard was read once more for the direction it fails in. It
refuses the run rather than taking a fresh baseline on the operator's behalf,
which is right: a baseline is the thing the whole record hangs from and Hermes
does not seal one as a side effect of being asked to verify.

Leads not pursued: the obligation-answer minimum, unchanged from round 1.

## Hermes rule corpus, step 6, round 1 -- 2026-08-21

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S6-R1-01; severity: low; file: `AGENTS.md`, `README.md`, `plugins/hermes/skills/hermes/SKILL.md`; finding: The marketplace-wide cold read the frontier obligation requires found three surfaces describing Hermes as it was before the corpus: the boundary sentence in the root runtime contract, the two published invocation prompts, and the skill's own selection description. Each now names the corpus.; status: fixed in this round
- id: S6-R1-02; severity: low; file: `plugins/hermes/skills/hermes/SKILL.md`, `references/optimisation-catalogue.md`; finding: Two new two-column tables failed Brevitas B011, which requires three by three before a table earns its shape. Both are lists now.; status: fixed in this round

The Pashov pair did not run under the recorded waiver. Phylax, Ephoros and
Hypomnema each exit 0, and Brevitas exits 0 on all six changed prose surfaces.
The root suite passes 104/104 and the Hermes suite 72/72 in 24.8 seconds. The
demo path from the study's problem statement runs clean at 120 rules, 28 myths
and 40 references, corpus digest `5d1773f9`, source digest `297c926d`.

The epoch row was recomputed independently of the code that wrote it: the four
frontier header fields hashed in the contract's canonical order give
`1916665dfd39d783`, which is the digest in the row; the baseline row retains its
own digest byte for byte; the arithmetic is `hermes-v0.1.0` to `hermes-v0.1.1`
on the epoch axis; and the change text carries `reopen`, which the contract
requires of an epoch row that moves the frontier. All six surfaces carrying the
frontier sentence agree and no stale copy remains.

Two things the cold read found and deliberately left. Horos's live-evidence
study cites Hermes's held ambition, meaning the evidence bundle this run
displaced, and Probitas's audit log mentions Hermes in a logged round. Both sit
under paths the shipped-prose lint excludes because they are records of what was
written at the time, and editing either would rewrite history to look tidier
than it was. The displacement is recorded in ADR-007 where a reader of those
documents can find it.

The budget was measured a second time and renegotiated on the page rather than
quietly. Four consecutive runs of the 72-case suite gave 26.1, 24.8, 25.9 and
25.0 seconds against a 25-second ceiling authored before the 22 hermetic gate
cases existed. A ceiling inside its own noise band fails intermittently and
teaches a reader to ignore it, so the study's third amendment moves it to 30
seconds with the four measurements and the rejected alternative, which was to
share one sealed baseline across the gate cases. That was rejected because a run
directory records absolute paths, so sharing one means teaching the harness a
relocation it has no other reason to support.

Leads not pursued: none. The class-vocabulary gap recorded in steps 3 and 4 is
no longer a lead, because it is the successor frontier this row holds.

## Hermes rule corpus, step 6, round 2 -- 2026-08-21

Round 1's two fixes introduced no regression and this round found nothing.
Status: clean.

Phylax, Ephoros and Hypomnema each exit 0. The root suite passes 104/104 and
the Hermes suite 72/72. The demo path is clean at 120 rules.

The second look re-read the prose the cold read changed, against the thing it
now claims. The root boundary sentence says Hermes measures one class named by
a rule from its pinned corpus, which is what Gate 2 enforces. Both published
invocation prompts tell a reader to name the rule, which is what `verify`
requires. The skill's selection description names the corpus, the counts and the
scope refusal, so an agent choosing between skills can see what changed without
  the body. The catalogue's generated index is held to the corpus by a
test, so no future reader is told a mapping the data does not carry.

Leads not pursued: none.

## Fiat delegation packets, integration sync closure -- 2026-08-21

### Incident

The issue 320 integration pull request conflicted after the independently
merged Hermes rule-corpus run advanced `main`. The overlaps were the Horos
document and append-only audit ledger; Git merged the root README and Promise
Machine coverage without manual selection. Rebasing would have rewritten the
22 signed Fiat commits, while an unreceipted run-branch commit would have
broken the final-step, remote-tip and pull-request-head identity established by
the step 3 audit.

### Resolution

`done sync-run` records one explicit integration repair. It requires the remote
run tip to equal the supplied signed merge, the remote base tip to equal the
supplied base commit, and the merge parents to be exactly the final recorded
step merge followed by that base tip. It verifies the local signature and both
exact provenance trailers, requires GitHub `verified: true` with `reason:
valid`, refuses a second sync, and makes the recorded sync commit the only
permitted integration pull-request head. It neither rewrites the stack nor
loosens ordinary integrations, which still require the final step merge as the
run tip.

### Evidence

Three focused guards failed before the command existed. Five pass after the
fix: exact sync and terminal integration, wrong-parent refusal, unsigned-commit
refusal, stale-base refusal and invalid-GitHub-verification refusal. The Horos
document was regenerated over the merged tracked tree at 1,385 files, 89
classified entries and none unreadable. The Fiat controller suite passes
146/146, the root suite 104/104, Hexaemeron 637/637 and Hermes 72/72. Promise
Machine reports 14 plugins, 14 copies and all 67 coverage rows clean. The
changed prose, three tree lints and diff check are clean; historical audit-log
lexicon signals remain outside this appended closure.

Further leads: none.

## Fiat state-shape validation, step 1, round 1 -- 2026-08-21

The exact range `6980aef4c33ece8614b21e4ef8ff32dd19c3e7fc..7f4600dec3b66f5d5781f5f7b9992587bda7357b`
contains the two byte-identical tracked specification copies and the matching
Horos census update. No product source or Solidity changed, so the recorded
security-suite waiver applies and the Pashov pair did not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

The Horos red specimen reproduced from the exact parent: its document digest
changed from `17bf1887627572f15612f3e7ebe39f8204afba0bd16e4b78bcc8fac1fdc63942`
to `dbfe1e25e5aadf1747318de7d1192f8797d49fd4e3a4b51786a4f20d79a0a4d4`
when the two Markdown files entered the census. The regenerated document is
byte-identical to the tracked document and a second scan leaves it unchanged
at 1,387 walked files, 89 classified entries and zero unreadable files.

Protasis accepts both tracked specifications. Imprimatur and the runbook's
Brevitas check are clean. Phylax, Ephoros and Hypomnema each exit 0. The
boundary suite passes 4/4, the root suite 104/104 and Hexaemeron 637/637.
Promise Machine reports 14 plugins and 14 copies clean. The Mason head has a
valid local signature and exactly one of each required Shoggoth trailer.

The review covered all 12 source-bound risks: `validation-bypass`,
`path-diagnostic-drift`, `validation-order`, `legacy-state-rejection`,
`semantic-scope-creep`, `secret-echo`, `verify-parity`, `partial-write`,
`round-indexing`, `frontier-arithmetic`, `marketplace-prose-drift` and
`signing-provenance`. Step 1 preserves those acceptance boundaries without
implementing or weakening them.

Leads not pursued: none.

## Fiat state-shape validation, step 2, round 1 -- 2026-08-21

The exact range `ea03021ae3cc1d4b24bb422ba6f96ca163a25fec..f750e031c352c6a49796da651f5c8c7fd1da16cb`
adds one central `load_state` container-spine validator, its command-level
guards and the corresponding Promise Machine source digest. No Solidity
changed, so the recorded security-suite waiver applies and the Pashov pair did
not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

The Elenchus guard was replayed on the exact parent by applying only the new
test class to `ea03021ae3cc1d4b24bb422ba6f96ca163a25fec`. All three tests were
red with 104 command-level failures: wrong-shaped state was variously accepted,
reported only as an edited fingerprint or allowed to raise a traceback. The
same tests pass on the implementation head. Removing the central validation
boundary therefore makes the guard red rather than leaving a reader-specific
check in place.

The review exercised all 12 source-bound risks. `validation-bypass`,
`path-diagnostic-drift`, `verify-parity`, `partial-write`, `secret-echo` and
`round-indexing` are covered by the root, required-container, nested-member and
command matrix: `status`, `next`, `verify` and `record` return the same exact
value-free line with exit 1, no traceback and byte-identical state and ledger.
`validation-order` was probed with seven additional multiple-fault specimens
across 28 command invocations, including faults split across configuration,
top-level receipts, step members and round members; every first diagnosis
followed the documented two-pass step-member then per-step-container order.

`legacy-state-rejection` was checked against all 11 archived runs: both
`status` and `verify` succeed for every archived state and ledger pair. The
heterogeneous-receipt guard also preserves scalar and list leaf payloads, so
`semantic-scope-creep` remains outside the container contract.
`frontier-arithmetic` and `marketplace-prose-drift` are unchanged in this step;
the implementation does not touch the evolution ledger or shipped prose.
`signing-provenance` passes for `f750e031c352c6a49796da651f5c8c7fd1da16cb`:
the local signature is valid and each required Shoggoth trailer occurs exactly
once.

The focused controller and Fiat skill suites pass 189/189, the root suite
104/104 and Hexaemeron 640/640. Promise Machine reports 14 plugins, 14 copies
and all 67 coverage rows clean. Phylax, Ephoros and Hypomnema each exit 0;
Python compilation and the diff check are clean.

Leads not pursued: none.

## Fiat state-shape validation, step 3, round 1 -- 2026-08-21

The exact range `6530928e82e68d96bdfa5fcd3204e785942efef2..dd41bdf375f7ef4fbd0f0e778f1a5988000716c2`
publishes the completed Fiat frontier, synchronises Hexaemeron's release
surfaces and reconciles the mutable first-party marketplace prose made stale
by the new load boundary. No Solidity changed, so the recorded security-suite
waiver applies and the Pashov pair did not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

The frontier advances exactly once, from `fiat-v4.9.1` to `fiat-v5.9.1` on
the evolution axis. An independent reconstruction of the four frontier fields
hashes to the recorded
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`.
The new row closes issue 321's held state-shape job and holds issue 363's
delegated task-identity failure as the open successor without importing that
work. Fiat frontmatter agrees with the ledger. The two plugin manifests and
two marketplaces agree on Hexaemeron `1.5.3`, and the controller source hashes
to the Promise Machine coverage digest
`f8aa8214615ddcb6f329b5b78ed6469215ba12f0996d6381744d0253a53c84c3`.

The prose inventory enumerated 204 candidate root, landing, runtime, skill,
evolution, agent, reference, manifest and marketplace surfaces. Generated
Promise Machine copies, vendored Pashov instructions, fixtures,
content-addressed evidence, completed studies and historical audit text remain
outside the mutable publication set. A stale-term search found the old frontier
revision only in its evolution history and completed receipted-lint-rounds
records. The public Fiat skill, Hexaemeron README, Fiat agent prompt and Codex
runtime description all name the state-container gate; the remaining mutable
first-party surfaces do not make a stale state-validation, version or successor
claim.

All 12 source-bound risks were reviewed. The publication diff does not change
the central validator. Its three malformed-state guards pass and retain
command and verify parity, value-free diagnostics and byte-identical refusal,
covering `validation-bypass`, `path-diagnostic-drift`, `validation-order`,
`legacy-state-rejection`, `semantic-scope-creep`, `secret-echo`,
`verify-parity`, `partial-write` and `round-indexing`. The independent ledger,
publication and signature checks cover `frontier-arithmetic`,
`marketplace-prose-drift` and `signing-provenance`.

The focused suite passes 227/227, the root suite 106/106 and Hexaemeron
640/640. Promise Machine reports 14 plugins, 14 copies and all 67 coverage
rows clean. Horos reports 1,387 files, 89 classified entries and none
unreadable; its boundary suite passes 4/4. Imprimatur is clean on every changed
prose-bearing surface, Brevitas is clean on each applicable document, and
Phylax, Ephoros and Hypomnema each exit 0. The diff check is clean. Mason head
`dd41bdf375f7ef4fbd0f0e778f1a5988000716c2` has a valid local signature and
exactly one copy of each required Shoggoth trailer.

Leads not pursued: none.

## Ephoros wallet-address telemetry, step 1, round 1 -- 2026-08-21

The exact range `6412c85d7cfd352e21fcc3dc0d8cef39a0649976..a1af4b888b1c181b2a0267b6feee2156abcee238`
contains the two committed specification copies and nothing else. No product
source or Solidity changed, so the recorded security-suite waiver applies and
the Pashov pair did not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

Protasis accepts both tracked specifications, study mode and runbook mode each
exiting 0. Imprimatur exits 0 on each document. Phylax, Ephoros and Hypomnema
each exit 0 over the two changed files. The Hexaemeron suite passes 640/640 and
the root suite 107/107. Promise Machine reports 14 plugins and 14 copies clean.
The step head has a valid local signature and exactly one of each required
Shoggoth trailer.

The review covered all 8 source-bound risks: `ts-lexer-input`,
`false-positive-cache-keys`, `rule-boundary-drift`, `e002-reassignment`,
`suppression-parity`, `yaml-label-keys`, `fixture-exclusion` and
`walk-widening`. Each names an implementation obligation of steps 2 through 4;
this documents-only step records them without implementing or weakening any.

Leads not pursued: none.

## Ephoros wallet-address telemetry, step 2, round 1 -- 2026-08-21

The exact range `485023a30468f898068454fb92e10ae2b547a604..a88b649c1993c95babe2d848c220efc1e4f966bc`
holds the E005 recognisers in Python and block-YAML, ten fixtures under
`telemetry-keys/` and 21 new checker tests. No Solidity changed, so the
recorded security-suite waiver applies and the Pashov pair did not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

Phylax, Ephoros and Hypomnema each exit 0. The focused checker suite passes
67/67, the Hexaemeron suite 661/661 and the root suite 107/107. The step head
has a valid local signature and exactly one of each required Shoggoth trailer.

The review ran roughly seventy adversarial specimens against the checker
beyond the committed tests. The register ids in this step's reach were each
worked by execution: `e002-reassignment` (overlap labels such as
`wallet_hash` and `address_url` yield exactly one code, E005; `tx_hash` keeps
E002; a mixed label set yields one of each), `yaml-label-keys` (25 probes:
block scalars, quoted keys, list forms, flow mappings, comment interruptions,
alert-boundary containment and `annotations:` nesting all behave inside the
E004 subset, and E004 and E005 co-fire where both apply), `suppression-parity`
in its Python half (a reasoned pragma on the line and the line above
suppresses all three shapes, a bare pragma suppresses none, and pragma-shaped
text inside scalars is inert) and `fixture-exclusion` (the walk reaches zero
`telemetry-keys/` files while an identical specimen outside a fixtures
directory is caught, exit 1). A parent-to-head differential over every
pre-existing fixture shows E001 to E004 unmoved; the one modified test is the
sanctioned E002-to-E005 guard re-pin. `ts-lexer-input`, the TypeScript half of
`suppression-parity`, `false-positive-cache-keys` and `walk-widening` are not
applicable until step 3 opens that surface.

Leads not pursued: the `s?` suffix shared by `ADDRESS_KEY` and the
pre-existing `UNBOUNDED` regex misses `-es` plurals such as `addresses` and
`hashes`, a checker-wide lexical gap that predates this commit and belongs to
a deliberate rule-widening decision; the E005 message says wallet address for
any `address`-fragment key such as `ip_address`, a wording the SKILL.md prose
in step 4 should state; nested mappings under `labels:` pass silently because
recognition is direct-children-only, worth a line in the same step 4 prose.

## Ephoros wallet-address telemetry, step 3, round 1 -- 2026-08-21

The exact range `e78a3cac6d684e474dbf5d78c65bd8faa5d84417..41f5da1d637826851bdc8c647da3df3dc590d49f`
opens the TypeScript surface: `check_typescript` through the shared masked
lexer, the widened walk, and 20 new checker tests. No Solidity changed, so the
recorded security-suite waiver applies and the Pashov pair did not run. The
three lints and both suites were green; every finding below came from
adversarial probes beyond the committed tests.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | high | scripts/ephoros.py | a ~3 KB nested-template file raises RecursionError through the shared lexer, crashes the run and drops sibling findings, falsifying the E000 fail-closed claim | fixed in 2a464fe |
| S3-R1-02 | medium | scripts/ephoros.py | pragma text inside a TS string or template suppresses a real E005; allow lines were read from raw text rather than comment spans | fixed in 2a464fe |
| S3-R1-03 | medium | scripts/ephoros.py | TS E000 findings were suppressible, so a crafted unterminated file plus a pragma vanished with exit 0 | fixed in 2a464fe |
| S3-R1-04 | medium | scripts/ephoros.py | the widened ALLOW grammar leaked `//` pragma semantics into Python files, changing parent behaviour out of step scope | fixed in 2a464fe |
| S3-R1-05 | medium | scripts/ephoros.py | `index:` string-literal values were missed because the property regex ran over the blanked mask | fixed in 2a464fe |
| S3-R1-06 | low | scripts/ephoros.py | canonical prom-client `labelNames:` spelling unrecognised | fixed in 2a464fe |
| S3-R1-07 | low | scripts/ephoros.py | optional chaining `?.` defeated every recogniser | fixed in 2a464fe |
| S3-R1-08 | low | tests/test_ephoros_checker.py | five YAML alert-label tests were absorbed into a TypeScript-named class | fixed in 2a464fe |
| S3-R1-09 | info | scripts/ephoros.py | `#` pragmas suppressed inside `.ts` files under the same un-gated grammar | fixed in 2a464fe |

Each fix landed under the guard-test convention, red observed then green: 13
tests over the step head's 87, for 100 focused cases. After the fixes the
clone run stays clean at exit 0 with zero pragmas and an empty porcelain, the
tree lint exits 0, the Hexaemeron suite passes 694/694 and the root suite
107/107. Phylax still exits 0 over the changed checker and over the clone's
`src`, and a mixed secret-plus-address specimen draws exactly one code from
each lint, so the boundary between the two holds. A parent-to-head
differential over E001 to E003, the Python E005 shapes, Python suppression and
the YAML shapes shows zero mismatches beyond the sanctioned fixes.

The register ids this step opens were each worked by execution:
`ts-lexer-input` (cap exact at 1 MiB and applied before lexing, 0.2 ms refusal
on cap-plus-one; unterminated constructs, invalid UTF-8, BOM, CRLF, JSX and
regex ambiguity all E000 or clean; no execution or import of inspected
source), `false-positive-cache-keys` (the clone's five real address patterns
stay clean while tags shorthand, statsd tags, instance labels, positional hex
and attributes fire), `suppression-parity` in its TypeScript half (line and
line-above suppress, bare and block-comment pragmas do not), `walk-widening`
(`node_modules` excluded by test and probe, symlinked directories not
traversed, and the walked `dist`/`build` question checked against both named
trees, which hold no tracked build output today) and `rule-boundary-drift`
(no P004 to P007 pattern duplicated or moved).

Leads not pursued: the shared lexer's recursion defect itself stays in
`plugins/hexaemeron/lib/typescript_lexer.py` and reproduces identically under
phylax, which predates this run; ephoros now contains it at its own boundary,
and the lexer fix belongs to a deliberate change on the owning surface,
carried forward for the run report. Computed object keys and method-call
dashboard access pass on both language sides alike, parity holds and widening
either is a rule decision nobody has asked for. The study's count of 882
tracked TypeScript files reads 875 at the pinned clone commit, a
study-document discrepancy with no bearing on any acceptance command.

## Ephoros wallet-address telemetry, step 3, round 2 -- 2026-08-21

The round audited the fixed tree at `2a464fe` with the seams of round 1's nine
fixes as its focus. All nine held: the recursion containment survives five
other lexer stress paths and an exception-injection probe, the comment-span
pragma collection holds under CRLF, JSX, template-expression and
file-boundary edges, E000 stays unsuppressible without over-rotating real
findings, and a three-way differential shows parent Python behaviour exactly
restored. The three lints and both suites were green; the findings below came
from fresh probes.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | low | scripts/ephoros.py | the `?.[` bracket form of optional chaining still defeated the subscript recognisers, an ordinary shape with 16 occurrences in the pinned clone | fixed in 82e7274 |
| S3-R2-02 | low | scripts/ephoros.py | a whitespace-separated dotted chain scanned quadratically, 62.8 seconds at 100 KB and hours at the cap, inside the untrusted-read boundary; introduced by this step's range and missed in round 1 | fixed in 82e7274 |
| S3-R2-03 | info | scripts/ephoros.py | a `//` pragma inside a block comment suppressed, against the documented line-comment grammar | fixed in 82e7274 |
| S3-R2-04 | info | scripts/ephoros.py | a constant template-literal index value was missed while the quoted forms fired | fixed in 82e7274 |

The scan fix is structural rather than a cap: chain parsing is anchored to
bracket positions and runs once, backwards, per bracket, taking the
adversarial 100 KB specimen from 58.7 seconds to 0.017 and the same content at
the full 1 MiB cap to 0.177 seconds, with a normal 1 MiB file at 0.295
seconds -- measured before and after through the real check path, as metron
requires. Ten guard tests landed with the fixes, six observed red first and
four pinning negatives, for 110 focused cases. After the fixes the clone run
stays clean at exit 0 with zero pragmas and an empty porcelain, the tree lint
exits 0, the Hexaemeron suite passes 704/704, the root suite 107/107, and
phylax and hypomnema each exit 0.

Leads not pursued: the Python `#` pragma matches inside a Python string, a
line-based behaviour identical at the step-2 parent and outside this step's
diff, belonging to a deliberate decision on that surface; the shared lexer's
recursion defect stays carried forward for the owning surface; read and write
subscripts both fire on both language sides alike, a parity-preserving rule
decision nobody has asked to change; a constant backtick literal now counts
as a string in every constant-key position, semantically identical to the
quoted forms, with the self-lint and clone run clean under it.

## Ephoros wallet-address telemetry, step 3, round 3 -- 2026-08-21

The round audited the tree at `82e7274` with round 2's fix seams as its
focus and one converging sweep. All thirteen earlier fixes held: the backward
chain parser was differentialed against the old grammar over a 65-shape
corpus, four thousand seeded fuzz cases and a findings-level comparison across
all 882 clone TypeScript files with zero unexpected deltas, and the pragma,
backtick and regression seams each held under execution. The three lints and
both suites were green; the findings below came from the sweep's mandated
adversarial shapes.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R3-01; severity: medium; file: scripts/ephoros.py; finding: deeply nested brackets scanned quadratically through `_matching`, extrapolating to roughly 1.9 hours at the 1 MiB cap, the `ts-lexer-input` register class; status: fixed in 7295cfe
- id: S3-R3-02; severity: low; file: scripts/ephoros.py; finding: a findings-saturated file paid a per-finding newline count, 9.9 seconds for fifty thousand findings; status: fixed in 7295cfe

Both fixes are structural and measured before and after through the real
check path, as metron requires: one linear stack pass maps every opening
bracket to its closer and cheap sink-name gates precede all span work, taking
the nested specimen at cap scale from an extrapolated 1.9 hours to 0.814
seconds; a per-file newline table with bisect takes the saturated specimen
from 9.877 to 0.526 seconds with line numbers pinned identical at the first,
middle and last finding. Two guard tests land the specimens at runtime,
asserting completion, exact counts and exact line numbers rather than
wall-clock. After the fixes the focused suite passes 112, the Hexaemeron suite
706/706, the root suite 107/107, the tree lint exits 0 and the clone run stays
clean at exit 0 in 0.886 seconds with an empty porcelain.

Leads not pursued: a generic-call type argument hides the chain from both the
old and new grammars alike, a lexical depth the study declares a non-goal; a
name carrying both dashboard and log words reports the dashboard reading by
deterministic precedence, contrived and consistent; wider fuzzing past four
thousand cases, marginal after the corpus and clone differentials came back
with zero unexpected deltas.

## Ephoros wallet-address telemetry, step 3, round 4 -- 2026-08-21

The round audited the tree at `7295cfe` with round 3's fix seams as its focus.
Every seam held under the strongest equivalence evidence of the loop: a
findings-tuple differential over all 882 clone TypeScript files, the 24
committed fixtures, a 40-shape corpus of mismatched and cross-nested brackets
and fourteen thousand seeded fuzz cases came back with zero deltas, line
numbers pinned identically including on E000 paths, and every prior specimen
kept its bound. The three lints and both suites were green; the finding below
came from extending the adversarial shapes to sink-named nesting, which round
3's unnamed-chain specimens could not reach.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S3-R4-01; severity: medium; file: scripts/ephoros.py; finding: overlapping spans that name a sink still paid per-span work behind the gates, 107 seconds at 160 KB and roughly 77 minutes at the cap on a nested `.labels(` shape; status: fixed in d21e5ea

The fix indexes each file once: both property regexes run a single pass over
the whole mask with spans collecting their rows by bisection, depth-zero
punctuation is attributed to its innermost matched pair in one scan, and key
extraction reads a bounded window whose equivalence the grammar guarantees.
Measured before and after through the real check path, the nested `.labels(`
shape goes from an extrapolated 80 minutes at the cap to 1.16 seconds, the
sink-named bracket nest from 12.2 to 1.08 seconds, and every earlier specimen
keeps its bound with a normal 1 MiB file at 0.43 seconds. The fixer's own
differential -- the clone, the fixtures and ten thousand seeded fuzz cases,
10,906 ordered comparisons -- shows zero behaviour deltas. Four guard tests
land the shapes with exact codes, counts and line numbers, for 116 focused
cases; the Hexaemeron suite passes 710/710, the root suite 107/107, the tree
lint exits 0 and the clone run stays clean at exit 0 in 0.86 seconds.

Leads not pursued: shapes whose mandated output is itself quadratic, such as
nested sinks each re-reporting their inner label containers, now run in
output-proportional time and cannot be faster than what they must print; the
shared lexer's recursion defect stays carried forward for the owning surface,
unchanged since round 1.

## Ephoros wallet-address telemetry, step 3, round 5 -- 2026-08-21

The closing round audited the tree at `d21e5ea` with round 4's span-index fix
as its focus, on evidence independent of the fixer's own harness: a fresh
differential with its own generators and seed over the 882 clone files, the 24
fixtures and 5,400 fuzz cases biased at the fix's edges, 6,306 ordered
comparisons with zero deltas, plus 43 hand-directed attacks derived from a
static read of the diff. The bounded-window equivalence argument was attacked
directly and holds: no truncating constant exists, the one numeric literal is
an exact-length gate beside an anchored hex match, and 500 KB values with the
address word at the far end fire identically on both sides. Performance holds
with nothing over 1.13 seconds at the cap, including a fresh shape aimed at
the new index's bisection. The three lints exit 0, the focused suite passes
116/116, the Hexaemeron suite 710/710, the root suite 107/107, and the clone
runs clean at exit 0 in 0.86 seconds with zero pragmas and an empty porcelain
at start and end.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

The remaining lead set is stable and recorded: the shared lexer's recursion
defect belongs to its owning surface and is contained at this checker's
boundary by the unsuppressible E000 path, re-confirmed by 178 fail-closed fuzz
cases; output-proportional shapes now do exactly the work their mandated
output requires; the spec-accepted lexical misses are declared non-goals with
parity across both language sides.

Leads not pursued: fuzzing past the cumulative twenty-five thousand cases,
marginal after two clone-wide differentials with zero unexpected deltas; two
pre-existing hypomnema pointer hits inside historical Hermes entries of this
log, outside this step's diff and outside the acceptance lint scope; the
study's file-count note from round 1, resolved -- the pinned clone reads
exactly 882 tracked TypeScript files today.

## Ephoros wallet-address telemetry, step 4, round 1 -- 2026-08-21

The exact range `fdd187a809d1aba0da0ef807b00dff3bbca13979..1fc0a2aaff4d2d216ada128da2ef098c21aabc51`
holds documentation and records only: the E005 section of the ephoros
SKILL.md with its three stated limits, the `ephoros-v1.2.0` evolution row,
ADR-010, one phylax boundary sentence pointing at it, and the two re-pinned
promise digests. No product source or Solidity changed, so the recorded
security-suite waiver applies and the Pashov pair did not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

The review checked the prose against the run's measured evidence rather than
against itself: every claimed behaviour in the new SKILL.md section -- the
three surfaces, the cap and fail-closed path, the E002 subset move, both
pragma grammars, bare-pragma inertness and the three stated limits -- was
established by execution in the step 2 and step 3 rounds above, and the
ledger row's successor job names a live specimen in the pinned clone. One
correction is on the page rather than silent: the study and runbook wrote the
completed-frontier label as `ephoros-v0.3.0`, and the versioning contract's
own arithmetic, enforced by `tests.test_evolution_contract`, makes a
completed frontier increment the first counter, so the recorded label is
`ephoros-v1.2.0` with generation and epoch retained. The demo path from study
item 1 ran green in order on the finished tree: the focused suite 116, both
tree lints exit 0, the clone clean at exit 0, the Hexaemeron suite 710/710,
the root suite 107/107 and the evolution contract 8 tests. Promise Machine
reports 14 plugins and 14 copies clean after the digest re-pins, imprimatur
scores 100 on each changed prose file, hypomnema exits 0 with every ADR
pointer resolving, and the step head carries a valid local signature with
exactly one of each required Shoggoth trailer.

The register ids are prose-inapplicable here and each stands at its step 2
and 3 disposition; this step records them without weakening any.

Leads not pursued: none.

## Fiat task-issue branch names, step 1, round 1 -- 2026-08-21

The exact range
`6412c85d7cfd352e21fcc3dc0d8cef39a0649976..7e2010b88f121a72239f00b2db595364f2043119`
adds byte-identical tracked copies of the accepted issue 438 study and runbook,
then refreshes the Horos tracked-file count for those two documents. No
Solidity changed, so the recorded security-suite waiver applies and the
Pashov pair did not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

Phylax 1.1.0 and Ephoros 0.2.0 each inspected the two Markdown files and
`.horos/boundary.json`; both exit 0. Hypomnema 4.3.0 inspected the two changed
documents and exits 0. The tracked study and runbook match their accepted
`.hexaemeron` sources byte for byte. The committed Horos document matches a
fresh tracked-tree scan at 1,390 files, and the boundary-currency suite passes
4/4. The exact step diff also passes `git diff --check`.

All 12 risk-register ids were reviewed. `issue-url-parse`,
`issue-receipt-drift`, `truncation-loss`, `override-escape`, `late-rename`,
`legacy-branch-mutation`, `no-issue-regression`, `step-propagation` and
`topology-regression` each have an explicit construction, refusal or regression
obligation in steps 2 and 3. This documentation-only step neither implements
those controls nor claims their evidence. `frontier-drift` is unchanged: no
evolution or version surface is in the diff, and the documents require the
issue 363 frontier fields and digest to remain exact. `controller-version-gap`
is explicit in both documents: old-controller phase receipts are kept separate
from checked-in-controller evidence. `fork-completion-overclaim` is also
explicit: the run cannot claim an upstream merge or issue closure until both
are observed.

The step introduces no executable boundary, dependency, subprocess, remote
fetch, credential, telemetry or alert. The study and runbook remain run
records, and they point to the step-3 Fiat evolution row as the durable home
for the governed decision. Issue 363's implementation and evolution surfaces
are untouched.

Leads not pursued: none.

## Fiat task-issue branch names, step 2, round 1 -- 2026-08-22

The exact range
`17397f180e7f0ce0ac36df232b569f30a912af3d..6da8ec6609bd7900fb4ff9af237b46454c8eb9ea`
adds issue-aware initialization, immutable task-issue recording, focused
controller guards and the corresponding Promise Machine digest. No Solidity
changed, so the recorded security-suite waiver applies and the Pashov pair did
not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: I438-S2-R1-01; severity: medium; file: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:256-267`; `plugins/hexaemeron/tests/test_hexctl.py:1618-1625`; finding: `task_issue_number` checks only the path returned by `urlsplit`. Relative text, hostless or non-HTTP URLs, and raw controls removed by `urlsplit` can therefore supply an issue number and be stored unchanged as the task-issue receipt. Require raw whitespace, C0 and DEL rejection, then an absolute HTTP(S) URL with a hostname; add each counterexample to the no-state-on-refusal guard.; status: open

Direct probes return issue `438` for `not-a-url/issues/438`,
`https:///issues/438`, `javascript:payload/issues/438` and a literal newline
inside `https://example.test/issues/438`. The last value demonstrates a split
between the normalized path used for branch identity and the unchanged invalid
receipt written by `cmd_init`. The current invalid-input test covers a bare
non-URL, zero, leading zero, a trailing path component and a pull-request path,
but none of these accepted shapes.

Phylax 1.1.0, Ephoros 0.2.0 and Hypomnema 4.3.0 each inspect the three changed
paths and exit 0. The nine issue-focused guards pass 9/9. The implementation
receipt records the complete controller suite at 158 tests, the root suite at
107/107 and Hexaemeron at 649/649. Promise Machine reports 14 plugins and 14
copies clean, the controller digest is
`3cfbb2dcf06aee9760893de2b122c6ee3fe06b9e49f7832b126ead4da21edba7`,
and both coverage bindings carry that digest. The exact diff check is clean.

All 12 risk-register ids were reviewed. `issue-url-parse` remains open as
I438-S2-R1-01. `issue-receipt-drift` is otherwise bound by one successful
parse, the unchanged state receipt, init-ledger data and fingerprint test.
`truncation-loss` keeps `438-` at the front of a 48-character composite slug.
`override-escape` accepts `fiat/438-prep` and refuses a different namespace,
missing issue and colliding number before state creation. `late-rename` keeps
state and ledger bytes exact on refusal and matching replay. The legacy-state
fixture covers `legacy-branch-mutation`; the unchanged automatic and explicit
paths cover `no-issue-regression`; and the two-step fixture covers
`step-propagation`.

`topology-regression` is unchanged: branch-tip, remote-tip, pull-request and
repository checks receive the stored branch without a new exception, and the
complete controller suite is green. `frontier-drift` is unchanged because no
evolution or version surface moved and issue 363 remains untouched.
`controller-version-gap` stays explicit: current behavior is exercised through
the checked-in controller, not inferred from this run's older phase receipts.
`fork-completion-overclaim` is not reached by this local initialization step;
the diff performs no network action and records no upstream merge or closure.

The controller remains interactive and adds no unattended path, log, metric,
trace or alert. Its bounded exit status, stderr, init output, state and next
directive remain the operator signals. The permanent Fiat record and mutable
procedure stay assigned to the step-3 evolution and prose pass.

Leads not pursued: none.

## Fiat task-issue branch names, step 2, round 2 -- 2026-08-22

Round 2 reviews fix range
`6da8ec6609bd7900fb4ff9af237b46454c8eb9ea..63861895b98585cf597ae1fb3a2ec749ae3c9ef7`
against I438-S2-R1-01 and the full accepted step contract. No Solidity changed,
so the recorded security-suite waiver still applies and the Pashov pair did
not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: I438-S2-R1-01; severity: medium; file: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:256-281`; `plugins/hexaemeron/tests/test_hexctl.py:1618-1640`; finding: The parser now rejects raw whitespace, C0 and DEL before parsing, then requires HTTP(S), a hostname and the positive terminal issue path. The no-state-on-refusal guard carries the round-1 relative, hostless, non-HTTP and normalized-newline counterexamples.; status: fixed in `63861895b98585cf597ae1fb3a2ec749ae3c9ef7`

Independent function probes refuse relative text, a hostless HTTPS URL, a
JavaScript URL, space, tab, newline, NUL and DEL with exit 2 and the bounded
task-issue diagnostic. Valid HTTP and uppercase HTTPS specimens return their
exact issue numbers. The focused invalid-input and valid-binding tests pass
2/2; the invalid-input test also proves that state and ledger files remain
absent after each refusal.

Fresh round evidence passes the task-issue focus 10/10, controller 158/158,
root 107/107 and Hexaemeron 649/649. Promise Machine check and coverage are
clean. The controller digest is
`0fafe32c3ccf9799d681cd96154abd781a1e3c9dac50976bff199971d97af292`,
and both coverage bindings carry it. Phylax, Ephoros and Hypomnema each exit 0,
and the diff check is clean. Fix commit
`63861895b98585cf597ae1fb3a2ec749ae3c9ef7` has a valid signature and exactly
one copy of each required Shoggoth trailer.

All 12 risk-register ids were re-reviewed. `issue-url-parse` is closed by the
raw and parsed URL gates. `issue-receipt-drift` remains closed because only the
validated original string reaches the initial state and ledger. The fix does
not touch slug or branch construction, so `truncation-loss`, `override-escape`,
`late-rename`, `legacy-branch-mutation`, `no-issue-regression` and
`step-propagation` retain their round-1 guards. It adds no topology exception,
network action, evolution surface or version change, so
`topology-regression`, `frontier-drift`, `controller-version-gap` and
`fork-completion-overclaim` remain unchanged. Issue 363 is untouched.

No new findings.

Leads not pursued: none.

## Fiat task-issue branch names, step 3, round 1 -- 2026-08-22

The exact range
`d0b115314f603cb6b2af1cd9252635266582aeb7..c913f54fea7f8f71f60e6cd69df85c3734696a0f`
publishes Fiat `v5.10.1`, reconciles its mutable instructions and public
descriptions, and advances the Hexaemeron package to `1.5.4`. No Solidity
changed, so the recorded security-suite waiver applies and the Pashov pair did
not run.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

The Fiat ledger advances once on the generation axis from `fiat-v5.9.1` to
`fiat-v5.10.1`. The frontier status, revision, current-frontier text and full
issue 363 successor remain exact. Recomputing those four fields produces the
recorded digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`.
The new row cites issue 438 and leaves all earlier rows unchanged. Fiat
frontmatter agrees with the ledger. Both manifests and both marketplaces agree
on package `1.5.4`. The final controller source hashes to
`2a509e311ae21f07e67cc60baffbe7f1623729fd9fe5443b19f001e88e2b8838`,
which matches both Promise Machine coverage bindings.

The checked-in CLI help names the issue-aware default. Fresh temporary CLI
fixtures prove the exact issue receipt and `fiat/438-` run prefix, step-prefix
inheritance, the unchanged issue-free name, no state after malformed issue or
override refusal, and byte-identical state and ledger after a late first
receipt refusal. The focused controller and publication set passes 241/241,
the root suite passes 109/109 and Hexaemeron passes 651/651. Promise Machine
reports 14 plugins, 14 copies and all 67 coverage rows clean. The exact diff
check is clean.

Phylax 1.1.0, Ephoros 0.2.0 and Hypomnema 4.3.0 each inspect the changed tree
and exit 0. The step adds no network path, subprocess, dependency, secret,
unattended path, telemetry or alert. The evolution row remains the established
home for the governed choice. Imprimatur reports no defect on every changed
prose-bearing publication surface. Brevitas exits 0 on each applicable
Markdown document and on the changed Codex long description extracted from
its JSON container. Commit
`c913f54fea7f8f71f60e6cd69df85c3734696a0f` has a valid local signature and
exactly one copy of each required Shoggoth trailer.

All 12 risk-register ids were reviewed. The publication commit changes only
controller help, not issue parsing, receipt storage or branch construction, so
the step-2 guards retain `issue-url-parse`, `issue-receipt-drift`,
`truncation-loss`, `override-escape`, `late-rename`,
`legacy-branch-mutation`, `no-issue-regression` and `step-propagation`.
`topology-regression` retains the existing branch-tip, remote-tip, pull-request
and repository checks without a new exception. The exact ledger and
publication checks close `frontier-drift`. `controller-version-gap` remains
explicit: the current behavior is proved with the checked-in controller, not
the older phase controller. `fork-completion-overclaim` is not reached: this
commit performs no remote action and claims no upstream merge or issue
closure. Issue 363 remains untouched.

Leads not pursued: none.

## Shoggoth contributor guide, step 1, round 1 -- 2026-08-22

Reviewed the three new documents against the eight study risks and the
non-Solidity phase gates. The security-suite waiver applies: this step adds no
Solidity, so X-Ray, Solidity Auditor and Fizz did not run. Phylax, Ephoros and
Hypomnema each inspected the changed paths and exited 0. Imprimatur, Brevitas,
the document assertions and the 109-test root suite had already exited 0 on
the exact implementation commit.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: SCG-S1-R1-01; severity: medium; file: `docs/how-to-help-shoggoth-study.md`; `docs/how-to-help-shoggoth-runbook.md`; finding: Step 1 shipped the study before the planned framework observation existed. The study named that issue as the standing home for the volunteer-selector trade, so Hypomnema's record-placement rule had no existing record to inspect when implementation was receipted.; status: fixed by filing [issue #447](https://github.com/wildcat-finance/skills/issues/447), which carries the chosen intent-packet design, rejected inference boundary, claim-channel alternatives and unresolved questions; exact title and labels were read back from GitHub
- id: SCG-S1-R1-02; severity: low; file: audit invocation; finding: The first Hypomnema command included `audit/AUDIT.md`, whose historical failure specimens deliberately name absent runbooks. It reproduced two H003 findings at lines 6119 and 6269; the reduced command over the three changed documents exited 0.; status: fixed by applying the pointer gate to the changed documentation scope named by the audit contract; no checker or shipped-document defect existed, so no code guard was added

`selection-overclaim` is closed for this step: every selector example is under
"The selector we should discuss" and the following sentence says the commands
are proposed, not live. `contributor-attribution` is closed by PR #445, issue
#438 and the merged audit rounds; no personal name or handle appears in the
three documents. `wave-drift` is bounded by the 22 August 2026 date and the
sentence refusing a permanent priority claim. `duplicate-work` stays visible:
the guide names assignment, branches and pull requests, and says the
pre-pull-request claim channel remains open. `scope-widening` is closed by the
diff, which contains only the guide, study and runbook.

`mascot-identity`, `issue-authority` and `binary-review` are not applicable to
the step-1 repository diff. The standing issue was filed as the audit fix under
the user's explicit request, with only the existing `observation` and
`origin:ai` labels; the exact body differs from the preview only by GitHub's
terminal newline. Artwork and binary inspection remain obligations of step 3.

Leads not pursued: SCG-S1-R1-02 changed no code and has no regression test; the
exact failing and corrected invocations are recorded above.

## Shoggoth contributor guide, step 1, round 2 -- 2026-08-22

Reviewed the fixed tree and issue #447 readback against both round-1 findings
and all eight study risks. The discussion record exists, stays open, carries
the exact expected title and the `observation` and `origin:ai` labels, and its
body differs from the preview only by GitHub's terminal newline. The three
changed documents still contain no personal name or handle, and proposed
syntax remains marked as not live.

Phylax, Ephoros and Hypomnema each inspected the three changed documents and
exited 0. The security-suite waiver still applies; no Solidity entered the
tree. Zero findings.

Leads not pursued: none.

## Shoggoth contributor guide, step 2, round 1 -- 2026-08-22

Reviewed implementation range
`eeed036b4f994104c9c1e7b5c03f6cdaea71ac13..c35dda9d02b88b9f489eb7c380e7ce61bcca88e6`,
the corrected issue #447 readback and the user correction receipts. The
security-suite waiver applies because the step changes documentation and one
discussion issue, not Solidity.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: SCG-S2-R1-01; severity: medium; file: `docs/how-to-help-shoggoth.md`; `docs/how-to-help-shoggoth-study.md`; `docs/how-to-help-shoggoth-runbook.md`; issue #447; finding: The first correction described the default as the earliest Wave with an eligible open issue. That narrows the user's rule: first choose the earliest Wave that still has open issues, then apply eligibility inside it.; status: fixed in this round; the tracked prose and issue now use the open-issue boundary, while the second immutable correction receipt records how eligibility applies inside the chosen Wave
- id: SCG-S2-R1-02; severity: low; file: issue #447; finding: The issue body counted ten open issues without Wave metadata. Filing the issue made that count stale immediately because the observation itself has no Wave metadata.; status: fixed in this round by keeping the relevant fact without a self-invalidating count

The dated live census finds Waves 3 through 12 with open work. Wave 3 is the
earliest and contains issues #323 through #328. All six are open and
unassigned, and none has an issue-number branch or open-pull-request trail.
The guide therefore uses issue #323 as its present-day named-issue example.
This snapshot does not assert that Wave 3 remains the default after its open
issues close.

The first requirements correction remains byte-for-byte intact at digest
`2b1cee87ec199012030e286d0047945ca47ef133c244adf3e0a316d0dcaaabca`.
The clarification at digest
`06fefa4266fc2ade47efe05d4a8619424d441641903c4ce29be4a249a8e03605`
supersedes only its narrower eligibility phrase. `hexctl verify` accepts the
15-entry chain.

Phylax, Ephoros and Hypomnema each inspect the changed guide, study, runbook,
issue preview and clarification and exit 0. The GitHub readback matches the
previewed body, title and labels after ignoring only its terminal newline.
The exact-selection, no-personal-name and current Wave assertions pass.
Imprimatur reports no defect, Brevitas exits 0 and the root suite passes
109/109.

All eight study risks were reviewed. `selection-overclaim`, `wave-drift`,
`duplicate-work` and `issue-authority` are bounded by the proposed-not-live
label, dated snapshot, public-claim discussion and exact issue readback.
`contributor-attribution` is clean: the public text says only "an external
contributor". `scope-widening` remains closed. `mascot-identity` and
`binary-review` remain Step 3 obligations.

Leads not pursued: none.

## Shoggoth contributor guide, step 2, round 2 -- 2026-08-22

Re-reviewed the fixed tree, both immutable correction receipts and the exact
issue #447 readback against the two round-1 findings. The selector first finds
the earliest Wave with open issues, then applies eligibility inside that Wave.
If none is eligible, it stops instead of advancing to another Wave or silently
falling through to frontier work. The issue no longer carries a count that its
own creation invalidates.

Wave 3 remains the earliest open snapshot group. Issues #323 through #328 are
still open, unassigned and free of issue-number branch or open-pull-request
trails. Phylax, Ephoros and Hypomnema each exit 0 on the corrected scope. The
root suite passes 109/109, the controller verifies its 16-entry receipt chain,
and the exact-selection and no-personal-name assertions pass.

No new findings.

Leads not pursued: none.

## Shoggoth contributor guide, step 3, round 1 -- 2026-08-22

Reviewed commit `6ee76df52b506cfe511294c9e67086ba5aa542d3`, the
final PNG, the five-page PDF, its extracted text, all five Poppler renders and
the eight study risks. The security-suite waiver applies because this step
adds documentation assets and no Solidity.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: SCG-S3-R1-01; severity: medium; file: `.horos/boundary.json`; `docs/assets/how-to-help-shoggoth-infographic.png`; `output/pdf/how-to-help-shoggoth.pdf`; finding: The pre-commit Horos scan could not place the untracked artwork and PDF in the tracked-tree boundary. After the implementation commit, `test_the_committed_boundary_matches_a_fresh_scan` named both paths and the root suite failed 1/109.; status: fixed in this round by rerunning the required committed-tree scan; both assets now have hard binary entries backed by their PNG and PDF file signatures, the focused boundary suite passes 4/4 and the root suite passes 109/109

The final artwork is a wide 1672 by 941 RGB PNG. The three foreground figures
have human torsos, arms, hands and posture, with hard-surface faceted masks.
The Shoggoth is identified by the dark tentacular mass and many eyes behind
the central figure. Visual inspection finds no animal body, fur, paws,
whiskers, tail or muzzle. An earlier uncommitted candidate with a more feline
head silhouette was rejected and is not present in either shipped asset.

The PDF is five A4 landscape pages and 4,454,214 bytes. It is unencrypted,
contains no JavaScript and reopens with PyPDF. Text extraction contains the
external-contributor example, the earliest-open-Wave rule, the proposed-not-
live warning, the three lanes, the Promise Machine, domain skills, phase
skills, Hex and Fiat, and issue #447. It contains no personal name or handle,
no latest-Wave rule and no non-ASCII dash. Its three link annotations resolve
to issue #323, PR #445 and issue #447. Poppler renders every page without
clipping, overlap or missing type; the one selection-order overflow found
during pre-receipt visual QA was corrected before the implementation commit.

Phylax, Ephoros and Hypomnema each exit 0 on the extracted final text.
Imprimatur scores it 100 with no defect, Brevitas exits 0, the binary and link
assertions pass, the controller verifies its 21-entry chain, and the final
commit has a valid local signature with both provenance trailers.

All eight study risks were reviewed. `mascot-identity` and `binary-review` are
closed by the reference-led regeneration, file checks, extracted-text checks
and rendered-page inspection. `selection-overclaim`, `contributor-attribution`
and `wave-drift` stay bounded in the PDF by the proposed-not-live label, the
external-contributor wording and the dated Wave 3 snapshot. The assets add no
issue write, runtime claim channel, controller change or frontier movement, so
`duplicate-work`, `issue-authority` and `scope-widening` remain unchanged.

Leads not pursued: none.

## Shoggoth contributor guide, step 3, round 2 -- 2026-08-22

Re-reviewed the fixed committed tree against SCG-S3-R1-01 and all eight study
risks. The fresh Horos document and committed boundary agree. The two new hard
binary entries name the exact PNG and PDF paths and file signatures. The
focused boundary suite passes 4/4 and the full root suite passes 109/109.

The final assets are byte-identical to round 1. The five rendered pages retain
their clear margins and readable type, the mascots remain human figures with
faceted geometric masks, the proposed selector remains labelled as not live,
and the Wave rule remains the earliest Wave with open issues. Phylax, Ephoros
and Hypomnema each exit 0 on the extracted PDF text. Binary reopening,
required-text and forbidden-name assertions pass. The controller verifies its
22-entry receipt chain.

No new findings.

Leads not pursued: none.

## Fiat receipted study amendments, step 1, round 1 -- 2026-08-22

The Pashov `x-ray`, `solidity-auditor`, and `fizz` suite did not run under the
recorded waiver because this step publishes two Markdown specifications and a
deterministic Horos boundary update, and ships no Solidity.

Reviewed commit `f3555a06229edb169628bbddf6050c2b765718b9` against run branch
`fiat/446-receipted-study-amendments`. The exact diff adds the byte-identical
tracked study and runbook and changes only `files_walked` from 1427 to 1429 in
`.horos/boundary.json`. The two `cmp` checks, both Protasis modes, Imprimatur,
Brevitas, `git diff --check`, all 113 root tests, and all 741 Hexaemeron tests
exit 0. Phylax, Ephoros, and Hypomnema each exit 0 on their required scopes.

Findings: 0.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: No findings.; status: clean

### Risk-register dispositions

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- risk id: `prefix-forgery`; disposition: Specified for step 2 and not activated by this documentation-only step. The study requires an exact prefix hash against the current receipt before mutation, and the runbook requires named regression guards.
- risk id: `amendment-selection`; disposition: Specified for step 2 and not activated here. The study fixes selection to one final dated block and requires fenced-decoy, duplicate-final-block, and trailing-prose cases to refuse.
- risk id: `field-ambiguity`; disposition: Specified for step 2 and not activated here. The study requires each of the four fields exactly once with non-empty bounded content, and the runbook assigns invalid-field guards.
- risk id: `step-verdict-coverage`; disposition: Specified for step 2 and not activated here. Every unbuilt step must appear exactly once with entry-and-exit verdicts; missing, duplicate, ambiguous, and completed-step cases are assigned tests.
- risk id: `broken-step-transition`; disposition: Specified for step 2 and not activated here. A valid broken-current-step amendment must be recorded before durable state blocks all dependent packets, with explicit recovery left available.
- risk id: `checker-binding`; disposition: Specified for step 2 and not activated here. The study binds an argv-only invocation to the bundled checker, exact candidate bytes, its exit, timeout, and bounded diagnostics.
- risk id: `path-scope`; disposition: Specified for step 2 and not activated here. Candidate and canonical paths must remain inside the target; symlink escape, unreadable, and oversized sources refuse before mutation.
- risk id: `partial-write`; disposition: Specified for step 2 and not activated here. Validation must finish before the existing state lock and recoverable atomic-write sequence mutate the artefact, state, or ledger.
- risk id: `receipt-history`; disposition: Specified for step 2 and not activated here. The receipt and ledger must retain old, new, and amendment digests plus bounded verdict metadata without erasing prior transitions.
- risk id: `post-amend-drift`; disposition: Specified for step 2 and not activated here. `next` and `verify` must recompute the amended digest and retain the ordinary refusal for any later unreceipted edit.
- risk id: `legacy-state`; disposition: Specified for step 2 and not activated here. Runs without an amendments member retain their ordinary read and `next` behaviour until the new command is used.
- risk id: `evidence-overclaim`; disposition: Closed for the published specification and retained as an implementation boundary. The study limits the future receipt to checked structure, order, digests, and recorded operator verdicts, not the truth of the correction or correctness of the remaining plan.

The record-placement review found the chosen command and its rejected
alternatives in the tracked study, the semantic origin linked to PR 307, and
the durable behaviour explicitly assigned to Fiat's canonical skill and tests
in step 2. No evolution row or standalone ADR is claimed by this ordinary
delivery. The two published documents are exact copies of the receipted
sources, so this audit does not revise the accepted specification.

Leads not pursued: none.

## Fiat receipted study amendments, step 2, round 1 -- 2026-08-22

The Pashov `x-ray`, `solidity-auditor`, and `fizz` suite did not run under the
recorded waiver because this step changes Fiat's Python controller, tests and
instructions and ships no Solidity. The audit reviewed the exact Step 2 commit
`6edcf7f72ca12ec797aead542dd8d7dc17ff7696` against its parent
`de7090b7c107241dac13d4655c8dc2f68bf12574`, then reviewed every fix on the
stacked audit branch.

Findings: 3.

| id | severity | file | mechanism | status |
| --- | --- | --- | --- | --- |
| FSA-S2-R1-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; `plugins/hexaemeron/tests/test_hexctl.py` | `_replace_study_bytes` ran before the ledger/state `commit`. An interruption in that gap left the new study with the old receipt and ledger, while `hexctl verify` still exited 0. An interruption after the ledger append could also make recovery append the same `amend:study` event twice. | fixed in this round with a fsynced write-ahead marker, refusal of every other controller command while it exists, exact-byte revalidation, finish-or-rollback recovery, final cross-file verification before marker removal, and non-duplicating completion of an already-written ledger event; both guards were observed red before the fix |
| FSA-S2-R1-02 | medium | `plugins/hexaemeron/skills/fiat/SKILL.md`; `plugins/hexaemeron/tests/test_fiat_skill.py`; `tests/promise_machine_coverage.json`; `tests/test_promise_machine_contract.py` | The new consequence-2 durable mutation had no Promise whose `Authorises` field permitted canonical study replacement and receipt re-pinning. The new `blocked` directive was also absent from Fiat's loop terminal set, action table and stop contract. | fixed in this round with `fiat-study-amendment`, operation-specific positive/missing/stale/overclaim/recovery bindings, and an explicit receipt-free `blocked` stop; the contract guards were observed red before the fix |
| FSA-S2-R1-03 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; `plugins/hexaemeron/tests/test_hexctl.py` | The Markdown selector tracked only the fence character, so three backticks closed a four-backtick fence. A heading still inside the longer Markdown fence could therefore be selected as the live amendment. | fixed in this round by tracking the opening delimiter length and accepting only a same-character closing delimiter at least as long; the adversarial guard was observed accepting the fenced heading before the fix |

### Risk-register dispositions

| risk id | status | disposition |
| --- | --- | --- |
| `prefix-forgery` | closed | The candidate prefix is hashed against the current receipt before mutation; the original prefix-drift guard leaves artefact, state and ledger unchanged. |
| `amendment-selection` | fixed | FSA-S2-R1-03 makes fenced decoys respect delimiter character and length; duplicate final blocks and trailing sections refuse. |
| `field-ambiguity` | closed | Date validity, exact cardinality, non-empty values and accepted order are covered by named guards. |
| `step-verdict-coverage` | closed | Every non-done step gets one exact entry-and-exit verdict; missing, duplicate, ambiguous, unknown and completed-step cases refuse. |
| `broken-step-transition` | fixed | FSA-S2-R1-02 records a broken current-step amendment, makes `next` emit the source-bound `blocked` outcome, refuses step receipts, and names inspection, halt or a separately specified repair as recovery. |
| `checker-binding` | closed | The controller writes the captured bytes to a private temporary file, invokes the sibling Protasis checker with `sys.executable` and a fixed argv list, bounds time and output, suppresses raw diagnostics, and refuses a non-zero exit. |
| `path-scope` | closed | Candidate and canonical paths use the existing real-path containment and byte cap; outside paths, non-files and oversized inputs refuse before the write-ahead transition. |
| `partial-write` | fixed | FSA-S2-R1-01 adds a durable pending record before replacement; recovery distinguishes prior, candidate and already-committed states and verifies artefact, state and ledger before clearing it. |
| `receipt-history` | closed | State and ledger carry prior, new and amendment digests plus normalized touched-step and verdict metadata; interruption recovery records the event exactly once. |
| `post-amend-drift` | closed | Both `next` and `verify` recompute the receipted study digest, and the general verify path now checks every source-bound study rather than only one already carrying amendment history. |
| `legacy-state` | closed | A study receipt with no amendment member retains ordinary packet behavior; an unbound legacy receipt may still be read but cannot use the new mutation. |
| `evidence-overclaim` | fixed | FSA-S2-R1-02 establishes checked byte continuity, structure, checker exit and recorded operator verdicts, not correction truth, verdict correctness or runbook repair. |

### Evidence and checks

The two implementation guards were applied to detached parent
`de7090b7c107241dac13d4655c8dc2f68bf12574`: the parser rejected the absent
`amend` command and the append demonstration remained unable to replace the
ordinary digest refusal. The three audit mechanisms were then observed red
against unfixed Step 2 commit `6edcf7f72ca12ec797aead542dd8d7dc17ff7696`:
the long-fence specimen was accepted, no pending transaction survived the
replace/commit interruption, and Fiat had neither the `blocked` loop outcome
nor an amendment `Authorises` block. The ledger-before-state interruption
guard additionally reproduced two amendment events before the recovery fix.

The fixed temporary-repository demonstration records a holding amendment,
finds all three digests in state and ledger, and reconstructs the amended Mason
packet. Its second run records a broken current step and receives the durable
blocked directive. No fixture is described as a production run.

The focused controller, Fiat prose and Protasis suite passes 313/313; the root
suite passes 113/113; the complete Hexaemeron suite passes 765/765. Promise
Machine contract and coverage checks are clean at 68 promises and 68 selected
rows. Phylax, Ephoros and Hypomnema each exit 0 on their required scopes.
Imprimatur finds no defect in the changed Fiat skill; Brevitas exits 0 on that
skill and on this appended audit entry.

Leads not pursued: a general transaction rewrite for controller mutations
other than `amend study`, the deliberately separate runbook-repair transition,
and the truth of amendment prose or operator verdicts. None is authorised or
claimed by this step.

## Fiat receipted study amendments, step 2, round 2 -- 2026-08-22

The fixed tree at `35d79f4eaa7515bb2dd4078d2bcf45bbc3f6bb5e` was
re-audited against all three round-1 mechanisms and the complete twelve-item
risk register. The recorded waiver still applies: no Solidity entered the
tree, so `x-ray`, `solidity-auditor`, `fizz` and a Solidity campaign did not
run.

### Findings

- Findings: 0. The round-1 fixes hold.

### Risk-register dispositions

| risk id | status | round-2 evidence |
| --- | --- | --- |
| `prefix-forgery` | clean | The fixed prefix-drift guard still refuses before any durable mutation. |
| `amendment-selection` | clean | Fence state now retains delimiter character and opening length; the long-fence specimen, ordinary fenced decoy, duplicate block and trailing section all refuse as intended. |
| `field-ambiguity` | clean | Calendar date, exact four-field cardinality, order and non-empty values remain guarded. |
| `step-verdict-coverage` | clean | Missing, duplicate, ambiguous, unknown and completed-step verdict cases remain refused; each non-done step receives one normalized verdict. |
| `broken-step-transition` | clean | The broken demonstration records its amendment, emits `blocked`, emits no delegated agent brief, and every step receipt remains refused. Fiat's loop and stop contract names that receipt-free terminal outcome. |
| `checker-binding` | clean | The fixed sibling checker path, captured private temporary file, argv-only invocation, timeout, output cap and bounded refusal remain unchanged. |
| `path-scope` | clean | Real-path containment, regular-file checks and the source byte ceiling remain ahead of the write-ahead transition. |
| `partial-write` | clean | Round 2 exercised marker-before-replacement rollback and post-commit marker cleanup in addition to the two committed interruption guards. All four windows recover with matching artefact, state and ledger. |
| `receipt-history` | clean | Recovery after a written ledger event completes state without appending a second `amend:study`; holding and broken histories retain all three digests and normalized verdicts. |
| `post-amend-drift` | clean | Both `next` and `verify` recompute the amended artefact digest and refuse later drift. |
| `legacy-state` | clean | Source-bound receipts without an amendment member retain their ordinary packet behavior, while receipts lacking a digest cannot invoke the new transition. |
| `evidence-overclaim` | clean | `fiat-study-amendment` remains consequence 2 and authorises only recoverable replacement, receipt re-pinning and the holding-or-blocked result. It still refuses correction truth, verdict correctness and runbook repair. |

The write-ahead order is marker, canonical artefact, ledger, state,
cross-file verification, then marker removal. A probe interrupted before the
canonical replacement and recovered by visibly rolling back to the prior
digest. A second probe interrupted after the state and ledger commit and
recovered by verifying the recorded transition and clearing the marker. The
two committed guards continue to cover interruption after artefact replacement
and after ledger append but before state replacement; the latter still leaves
exactly one amendment event.

### Checks and bounded leads

The temporary holding and broken demonstrations both pass. The focused
controller, Fiat prose and Protasis suite passes 313/313; the root suite passes
113/113; the complete Hexaemeron suite passes 765/765. Promise Machine checks
are clean at 68 promises and 68 selected coverage rows. Phylax, Ephoros and
Hypomnema each exit 0 on the source-bound plugin paths.

Leads not pursued: the same bounded exclusions remain: a general transaction
rewrite outside `amend study`, the separately specified runbook-repair
transition, and the truth of amendment prose or operator verdicts. None is a
new defect in the fixed Step 2 tree.
## Fiat run worktree, step 1, round 1 -- 2026-08-22

Reviewed the committed specification against all eleven risk-register entries.
The step ships two documents and no executable path, so nine of the eleven are
not exercised by anything here and are carried to the steps that build them.
The two a document step can still get wrong were checked directly.

`docs/fiat-run-worktree-study.md` and `docs/fiat-run-worktree-runbook.md` are
byte-identical to the receipted artefacts, so the committed yardstick and the
frozen run record agree. Neither document carries an absolute path under a home
or root directory, which is the finding the earlier backed-out copy of this
step recorded and fixed; the block that carried it is not present in this
version. All five relative links resolve from `docs/`. The cited suite command
at `AGENTS.md:138` is the line the study claims it is.

The two inherited claims were re-measured rather than accepted. The four suite
commands are green on this run's base with no exception: 741/741, 113 OK, and
both Promise Machine checks clean. The earlier copy's two pinned-toolchain
failures do not reproduce, because this machine carries the forge and node
versions those fixtures assert; that is recorded in the study as a fact about a
container rather than the repository.

Phylax, Ephoros and Hypomnema each exit 0 on both documents.

No findings.

Leads not pursued: none.

## Fiat run worktree, step 2, round 1 -- 2026-08-22

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: FRW-S2-R1-01; severity: medium; file: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; finding: `check_worktree_path` read occupancy off the resolved path. A dangling symlink at the derived path resolves to something that does not exist, so the check saw a free path, accepted it, and returned the link's target rather than the path it was asked about. Step 3 would then create the run's tree at a location the deriver never chose, with the state and breadcrumb naming a different path, and the link left in place. Contained inside the repository root, so it redirects rather than escapes.; status: fixed in the same commit as this entry, guarded by `test_a_dangling_symlink_at_the_derived_path_refuses` and `test_a_symlink_to_a_real_directory_inside_the_repository_refuses`

Reviewed against the eleven risk-register entries. Two are exercised by this
step. `path-escape` is the whole subject of the change and drew the finding
above; the escape controls themselves hold. `subprocess-control` holds: the one
git invocation is `rev-parse --show-toplevel` through the existing bounded
fixed-argv reader, with no caller value reaching a shell. The other nine belong
to steps that write something, and this step writes nothing.

The finding was found by probing rather than by a lint. Both the escape checks
and the live-symlink case behaved correctly; the dangling case was the one
combination where occupancy and resolution disagree. Occupancy is now read off
the supplied path with `lexists`, and a link at the derived path is refused
whether it dangles or not, because the run's tree is a real directory there or
it is nothing.

Phylax, Ephoros and Hypomnema each exit 0 on both changed files.

1 finding, fixed. Suites after the fix: 759/759, 113 OK, both Promise Machine
checks clean.

Leads not pursued: one. There is a gap between validating a path and creating
something at it, so a path free at the check can be occupied by the time step 3
runs. `git worktree add` refuses a path that exists, so the race closes into a
refusal rather than a wrong tree, and closing it earlier would mean holding a
lock over a directory that does not exist yet.

## Fiat run worktree, step 2, round 2 -- 2026-08-22

Re-reviewed the fixed tree. FRW-S2-R1-01 is closed: a dangling link, a live link
to a real directory inside the repository, and a link leaving the repository are
each refused, the first two naming the link and the third naming the crossing,
and a free derived path is still accepted and returned unchanged. Both guards
fail against the pre-fix validator and pass against this one.

The same eleven risk-register entries were read again. `path-escape` and
`subprocess-control` hold; the remaining nine are still not exercised by a step
that writes nothing.

Phylax, Ephoros and Hypomnema each exit 0. Suites: 759/759, 113 OK, both Promise
Machine checks clean.

No new findings.

Leads not pursued: the check-to-create race recorded in round 1 is unchanged and
belongs to step 3, where `git worktree add` turns it into a refusal.

## Fiat run worktree, step 3, round 1 -- 2026-08-22

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: FRW-S3-R1-01; severity: medium; file: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; finding: The breadcrumb held one line, so `init` refused any second run from the same checkout, naming the first run's tree. [skills#439](https://github.com/wildcat-finance/skills/issues/439) asks for the opposite: two runs against one repository that do not contend for `HEAD` or the index. The guard turned an acceptance condition into a refusal.; status: fixed in the same commit as this entry, guarded by `test_two_runs_against_one_repository_each_get_their_own_tree`, `test_the_breadcrumb_records_every_live_run` and `test_repeating_a_topic_refuses_and_names_the_existing_tree`

Reviewed against the eleven risk-register entries. Nine are exercised here.
`operator-head-mutation`, `dirty-origin-tree` and `partial-write` are each held
by a test: the checkout's branch, `HEAD` and `git status --short` are captured
before and after a successful `init`, a run starts from a deliberately dirty
checkout, and every refusal path leaves no state, no ledger, no breadcrumb and
no directory. `branch-already-checked-out` refuses by name before anything is
written, and names the tree holding the branch. `stale-tree-reuse` and
`path-escape` are step 2's validator, called before the first mutation.
`subprocess-control` holds: two fixed-argv git invocations through the bounded
reader, no caller value near a shell. `cross-filesystem-atomicity` holds by
construction, since the tree is created under the repository root.
`legacy-state-resume` holds: an existing state directory in a checkout still
resumes and the archived-run fixtures still pass. `uncommitted-work-loss` and
`resume-orphan` belong to step 4.

The finding came from reading the issue's acceptance list against the built
behaviour rather than from a lint. The breadcrumb is now one line per live run,
sorted, with entries whose state has gone dropped on read, so a finished or
reset run stops being offered. A repeat of the same run still refuses, and now
names its own tree rather than somebody else's.

Two things about the origin checkout, recorded rather than fixed. It keeps a
`.hexaemeron/` holding three files: the self-ignoring `.gitignore` the
controller has always written, the kernel lock taken before any mutating
command runs, and the breadcrumb. Only the breadcrumb is the run's own writing,
and the study's phrase about narrowing write access to one breadcrumb line
describes that rather than the lock that precedes it. ADR-012 states what is
actually kept. Separately, a refusal in a directory that is not a repository
still leaves that `.hexaemeron/` behind, because the lock is taken before any
command can decide the target is unusable; no state, ledger or breadcrumb is
written, which is the standard the state-shape rounds set.

The bounded reader was split into `bounded_run`, `bounded_tool` and
`bounded_tool_status`. The security-relevant behaviour is unchanged and now sits
in one place: no shell, fixed argv, a hard timeout, a hard output cap, and
nothing from the child's stream in any diagnosis.

Phylax, Ephoros and Hypomnema each exit 0. Suites after the fix: 773/773,
113 OK, both Promise Machine checks clean.

1 finding, fixed.

Leads not pursued: two. `init` writes the worktree home's self-ignoring
`.gitignore` only when none is there, so a repository that already keeps a
different `tmp/fiat/.gitignore` would not get the ignore and would see the tree
as untracked; overwriting somebody else's ignore file is the worse of the two.
And the check-to-create race carried from step 2 is unchanged: `git worktree
add` refuses an occupied path, so it closes into a refusal rather than a wrong
tree.

## Fiat run worktree, step 3, round 2 -- 2026-08-22

Re-reviewed the fixed tree. FRW-S3-R1-01 is closed. Two runs started from one
checkout each take their own tree and their own branch, the checkout stays on
its own branch with its `HEAD` and `git status --short` unchanged, and the
breadcrumb carries both. A repeat of the same run refuses and names that run's
own tree. A breadcrumb entry whose state has gone is dropped on the next read,
so a finished or reset run stops being offered while its neighbours stay.

The same eleven risk-register entries were read again. Nothing in the fix widens
a boundary: it changes how many lines the breadcrumb holds and which path a
refusal names. `uncommitted-work-loss` and `resume-orphan` still belong to
step 4.

Phylax, Ephoros and Hypomnema each exit 0. Suites: 773/773, 113 OK, both Promise
Machine checks clean.

No new findings.

Leads not pursued: the two carried from round 1, both unchanged.

## Fiat run worktree, step 4, round 1 -- 2026-08-22

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: FRW-S4-R1-01; severity: medium; file: `docs/fiat-run-worktree-runbook.md`; finding: The committed runbook puts worktree removal in `done integrate`. Built that way it removes the state and the ledger along with the tree, because both live in the tree, so the last act of a run is to delete its own evidence. Fiat's own contract then has the caller run `status` and `verify` after the run reports done, and neither has anywhere to read from. Seven existing integrate tests failed on exactly this.; status: fixed by moving retirement to `reset`, guarded by `test_reset_removes_a_clean_tree_and_archives_its_evidence` and `test_a_tree_holding_work_is_kept_and_never_forced`

The specification was wrong here and the code does not follow it. `reset` already
means the run is finished and can be put away, it already archives, and it already
refuses a run that is not done. `done integrate` records whether the tree was
clean and says what `reset` will do with it, so the outcome is still named at the
point the runbook wanted it named. The divergence is recorded here and in the
pull request rather than resolved by editing the committed runbook, which is the
frozen record of what the run believed when it started.

A second thing fell out of the same reasoning. A run that lived in a worktree now
archives into the checkout it was started from. Archiving inside the tree and then
removing the tree would destroy the archive in the same breath.

Reviewed against the eleven risk-register entries. `resume-orphan` is held: the
breadcrumb and `git worktree list` agree, a recorded tree that is gone refuses
naming that path instead of starting a second run, and a retired run drops out of
the breadcrumb on the next read. `uncommitted-work-loss` is held by the rule and
by a test: cleanliness is read before anything moves, a tree holding work is kept
and named, and nothing anywhere passes `--force`. `legacy-state-resume` is held:
state already sitting in a checkout still resumes, and the archived-run fixtures
still verify. The other eight are unchanged from step 3.

One incidental confirmation. An attempt to force a run to `done` by editing
`state.json` directly was refused by the ledger chain check, which is the
behaviour the state-shape rounds established and which this change does not
weaken.

Phylax, Ephoros and Hypomnema each exit 0. Suites: 784/784, 113 OK, both Promise
Machine checks clean.

1 finding, fixed.

Leads not pursued: three. The two carried from step 3 are unchanged. New: if the
archive move succeeds and the removal then fails, the tree is left without its
state while the archive holds it; the tree is harmless at that point and the
breadcrumb drops it, so the alternative would be to undo a completed archive to
restore a directory nobody needs.

## Fiat run worktree, step 4, round 2 -- 2026-08-22

Re-reviewed the fixed tree. FRW-S4-R1-01 is closed. `done integrate` leaves the
tree in place and reports its cleanliness, `status` and `verify` still read the
run after it reports done, and `reset` archives into the origin checkout before
removing anything. A tree holding work survives `reset` with its file intact and
the run archived beside it.

The same eleven risk-register entries were read again and none moved. Nothing in
the fix widens a boundary: it changes which command retires the tree and where
the archive lands.

Phylax, Ephoros and Hypomnema each exit 0. Suites: 784/784, 113 OK, both Promise
Machine checks clean.

No new findings.

Leads not pursued: the three from round 1, all unchanged.

## Fiat run worktree, step 5, round 1 -- 2026-08-22

Reviewed the corrected contract, the ledger row and the demonstrations.

The ledger row was checked the way the `done integrate` gate reads it, not by
eye. The axis arithmetic goes `fiat-v5.10.1` to `fiat-v5.11.1` on the generation
counter alone, the row retains `state-shape-validation` and the digest
`e413d604...` byte for byte from the row before it, the header and the row name
the same version, and the digest recomputed over the live
`{status}|{revision}|{frontier}|{next job}` line matches. The held
[skills#363](https://github.com/wildcat-finance/skills/issues/363) job is
byte-identical, which is what a generation row owes.

Eight cases hold the contract text, including that `git worktree add ../` is
gone from both `SKILL.md` and `hexctl.py`. The advice it replaces was contract
text as well, and it was wrong in the ordinary case for as long as it stood, so
the replacement is asserted rather than trusted. Two more run the study's demo
path instead of describing it: one from a deliberately dirty checkout, asserting
the branch, `HEAD` and `git status --short` are identical afterwards, and one
against a directory that is not a repository, asserting the refusal writes no
state, ledger or breadcrumb.

An existing lock test asserted the old advice and now asserts its absence and
the new command, which is the same test doing the opposite job.

Imprimatur reports zero defects on all five changed documents. The Horos
boundary matches the tree. Phylax, Ephoros and Hypomnema each exit 0 across the
three changed sources and the five documents.

No findings.

Leads not pursued: the three carried from step 4, all unchanged. Worth naming
once, though it is a property of this shell rather than of the change: zsh does
not word-split an unquoted variable, so a lint invoked as `lint $FILES` receives
one argument naming a file that does not exist and reports it unreadable. It was
caught here because the exit status was read; a round that only read the word
`clean` would not have seen it.

## Phylax credential argv, step 1, round 1 -- 2026-08-22

### Suite disposition

The Solidity suite was waived exactly as recorded by the controller:
`waived: issue 325 changes the Python Phylax lint, fixtures, and governed prose;
it has no Solidity target`. No `.sol` file appears in the step diff. X-Ray,
Solidity Auditor and Fizz therefore did not run, and this round does not count
their absence as a clean Solidity review.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| review-code | none | `plugins/hexaemeron/skills/phylax/scripts/phylax.py` | No confirmed code finding. | clean |
| review-tests | none | `plugins/hexaemeron/tests/test_phylax_checker.py` | No confirmed test or diagnostic-secrecy finding. | clean |
| review-records | none | governed prose, ledgers and generated records | No confirmed specification, ledger, coverage or tracked-artifact finding. | clean |

Finding count: 0.

### Evidence

The review read all eight changed files and the full diff from
`4408597bcd0130b0cee8bd7aab0b55d64ff957c7` through
`23c7b3d57e66d5da7c91ab027b6952d372d3413d`. Each of the ten risk-register
rows was checked. Runner resolution remains the existing import-bound
`_starts_process` decision; only the first positional argument or explicit
`args=` value is walked; `env=` remains clean; nested names, tuples and list
concatenation are covered; local and unrelated runners stay clean; reasoned
and bare suppressions retain opposite results; P001 and P002 keep their prior
classifications; and neither text nor JSON diagnostics contain the fixture
credential value.

The tracked study and runbook match their receipted artefacts byte for byte.
The canonical frontier line recomputes to
`3d0057bb195f303c0e40b5782bf59ab0cba53e3172478c6a331d5990236ac604`;
only generation moves, from `phylax-v1.1.0` to `phylax-v1.2.0`. The Promise
Machine coverage digest matches the changed `SKILL.md`, and the Horos boundary
matches the tracked tree.

The focused Phylax suite passes 61/61 on Python 3.9.6 and 3.12.13. The first
full Hexaemeron run stopped because ambient Node v22.22.3 did not match the
fixture's declared v26.6.0. The official v26.6.0 Darwin arm64 archive matched
its published SHA-256,
`75480cd43b6fcb35d8e772dd18983fbd9f691b2f03b1c94393206098e9944b5e`,
and a PATH-scoped rerun passed 833/833 without changing the repository or
system toolchain. The root suite passes 118/118, the evolution contract passes
8/8, and the full Promise Machine check is clean. Phylax, Ephoros and
Hypomnema each exit 0.

### Leads not pursued

Leads not pursued: `API_TOKEN` in the study's motivating specimen remains
outside the existing `CREDENTIAL` grammar, and attribute/subscript values,
separately assigned argv, star-expanded call forms, `**kwargs`, runner-name
rebinding and flag interpretation remain outside the receipted source-local
boundary. Widening any of them would change the approved finding grammar or
runner-resolution contract rather than repair this implementation.

## Phylax unsafe deserialization, step 1, round 1 -- 2026-08-22

### Suite disposition

The controller recorded this waiver: `waived: issue 324 changes the Python
Phylax lint, fixtures, and governed prose; it has no Solidity target`. No
`.sol` file appears in the full step or stacked diff. X-Ray and Solidity
Auditor did not run; the waiver applies only to that pair.

The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0 over every
step-changed path. The manual review covered the full diff and every receipted risk.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/phylax/scripts/phylax.py:138` | Depth-first import discovery missed dangerous calls inside functions defined before their module or direct import. | fixed and guarded |
| S1-R1-02 | low | `plugins/hexaemeron/skills/phylax/scripts/phylax.py:187` | Conflicting imports could select one safe identity and hide an unsafe loader or deserializer under the same alias. | fixed and guarded |
| S1-R1-review | none | full step diff | No further code, test, record or payload-disclosure finding was confirmed. | clean |

Finding count: 2.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `source-parse` | `ast.parse`, one `ast.walk` and the existing visitor inspect source without importing, executing or deserializing it. | clean |
| `call-identity` | Module, module-alias, direct and direct-alias fixtures include imports after function definitions; relative imports remain excluded. | fixed by S1-R1-01 |
| `pickle-scope` | `load` and `loads` report; `dump`, `dumps` and unrelated loaders stay clean. | clean |
| `marshal-scope` | `load` reports and `loads` has an explicit negative fixture. | clean |
| `yaml-loader` | Positional and keyword `SafeLoader` and `CSafeLoader` aliases pass; absent, unknown, unsafe and conflicting bindings report. | fixed by S1-R1-02 |
| `dynamic-source` | Names, calls and f-strings report; inline string and bytes constants pass; no-argument and keyword-only shapes follow the stated first-positional-argument grammar. | clean |
| `alias-rebinding` | Assignment rebinding remains outside analysis; conflicting import evidence is conservative, and a bare/local `eval` collision still reports. | clean within scope |
| `suppression-line` | A reason-bearing pragma suppresses P008 and a bare pragma does not. | clean |
| `diagnostic-output` | Text and JSON carry fixed family messages and omit the sentinel payload. | clean |
| `classification-drift` | P000 through P007 guards and the full focused and plugin suites pass. | clean |
| `analysis-work` | The change adds one linear AST import pass and constant-time checks per relevant call, with no dataflow or target execution. | clean |
| `partial-run` | Every required lint and relevant test was read to completion; no interrupted result is counted as clean. | clean |
| `ledger-integrity` | `phylax-v1.3.0` advances generation only; the mature frontier fields and digest remain unchanged, and Promise Machine verification passes. | clean |

### Evidence

The review read all seven files changed from
`64096f4d89fc821ab9d91d075cd86be7e7bb92b5` through
`3766c516bf6960945774aeaa0b2b0c819bbbde95`, then reviewed the stacked fixes.
The tracked study matches `.hexaemeron/study.md` at
`5eac7e9c171969933bf9d08a07a50aefd0e3f52ff353fada05691271373f397f`.

The fix collects import evidence before call classification, retains exact
absolute module and direct-import resolution, and trusts a YAML module or
loader alias only when all explicit imports under that local name belong to
the safe family. Guards at
`plugins/hexaemeron/tests/test_phylax_checker.py:104` cover late module and
direct imports; the adjacent cases cover conflicting bindings, loader
precedence, relative imports, bare/local eval collisions, no-argument and
keyword-only shapes, and one finding per nested boundary call.

The focused Phylax suite passes 78/78 on Python 3.9.6 and 3.12.13. With the
fixture-pinned Node v26.6.0 first on `PATH`, the full Hexaemeron suite passes
850/850. The root suite passes 118/118, the evolution contract passes 8/8,
the full Promise Machine check is clean, the Horos boundary matches the tree,
and `git diff --check` exits 0. The ambient Node v22.22.3 run stopped at the
fixture's exact-version assertion before the pinned-version rerun passed.

### Leads not pursued

Leads not pursued: `marshal.loads`; wildcard and dynamic imports; assignment,
scope, taint and control-flow analysis; custom-loader proofs; the accepted
pragma-in-string quirk; and Python file-size policy. The receipted study names
these as exclusions. Bare/local `eval` collisions remain conservative P008
findings with the reason-bearing pragma as the escape. An exploratory
whole-file Hypomnema scan reported H003 at `audit/AUDIT.md:6119` and
`audit/AUDIT.md:6269`; both are quoted prior findings outside the step paths,
so neither enters this round's required lint exits.

## Phylax unsafe deserialization, step 1, round 2 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 324 changes the Python
Phylax lint, fixtures, and governed prose; it has no Solidity target`. The
complete base-to-stacked diff and the round 2 fix contain no `.sol` path.
X-Ray and Solidity Auditor did not run. Their active instruction digests match
the Promise Machine overlays; the waiver applies only to those two operations.

The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0 on the
repository-mandated scopes. The manual pass re-read the full diff and checked
all thirteen receipted risks against the fixed tree.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | low | `plugins/hexaemeron/skills/phylax/scripts/phylax.py:305` | Conflicting imports retained several possible call identities, but sorted iteration let the first unsafe candidate supply a false family-specific diagnostic. | fixed and guarded in round 2 |
| S1-R2-review | none | full base-to-stacked diff | No other code, test, record or payload-disclosure finding was confirmed. | clean |
| S1-R2-records | none | study, runbook, evolution and Promise Machine binding | The committed records still match their receipted bytes and generation-only boundary. | clean |

Finding count: 1.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `source-parse` | P008 uses `ast.parse`, `ast.walk` and the existing visitor; no target import, deserialization or execution was added. | clean |
| `call-identity` | Late module and direct imports resolve from functions and class bodies; nested imports remain conservative source-local evidence. | clean |
| `pickle-scope` | `load` and `loads` report; dump calls, JSON and unrelated readers remain clean. | clean |
| `marshal-scope` | `load` reports and the named `loads` exclusion stays clean. | clean |
| `yaml-loader` | Positional and keyword safe-loader forms pass; absent, unsafe, unknown and conflicting loader bindings report. | clean |
| `dynamic-source` | Names, calls and f-strings report; inline string and bytes constants pass. | clean |
| `alias-rebinding` | Conflicting import identities retain one conservative finding without inventing one family; assignment and lexical-scope dataflow remain excluded. | fixed by S1-R2-01 |
| `suppression-line` | Reason-bearing and bare pragmas retain opposite results. | clean |
| `diagnostic-output` | Text and JSON use a fixed unresolved-family message for ambiguous imports and omit the sentinel payload. | fixed by S1-R2-01 |
| `classification-drift` | P000 through P007 guards and the full focused, plugin and root suites pass. | clean |
| `analysis-work` | Binding classification adds one bounded pass over the import identities already collected; no recursion, dataflow or target execution enters. | clean |
| `partial-run` | Every result below reached a terminal zero exit; no partial dot stream was counted. | clean |
| `ledger-integrity` | `phylax-v1.3.0`, the mature frontier fields and its digest remain unchanged; Promise Machine verification is clean. | clean |

### Evidence

The review started on the exact stacked branch at signed commit
`116819e77574e116e5f5ddcaed57ef4e22d2c4af` and inspected all eight paths in
the full diff from `64096f4d89fc821ab9d91d075cd86be7e7bb92b5`.
The tracked and receipted study copies both hash to
`5eac7e9c171969933bf9d08a07a50aefd0e3f52ff353fada05691271373f397f`;
the runbook copies both hash to
`678e406845563e2bb51cae9dbbcc6d0b3d6f048ee3d3e8a68ceb84b71decdf07`.

The reduced guard
`UnsafeDeserialization.test_conflicting_imports_do_not_claim_one_call_family`
failed on the unfixed tree for all four module, direct, neighbour and explicit
bare-shadow specimens. It passes after the fix, which records ambiguity from
all visible import identities and emits one fixed unresolved-family message.
The same guard checks text and JSON for the sentinel payload.

The focused Phylax suite passes 79/79 on Python 3.9.6 and 3.12.13. With the
checksum-verified Node v26.6.0 fixture first on `PATH`, the full Hexaemeron
suite passes 851/851. The root suite passes 118/118 and the evolution contract
passes 8/8. The full Promise Machine check, both Protasis checks, the Horos
boundary check, the changed-tree Phylax scan and `git diff --check` each exit
0. The active-plugin Phylax, Ephoros and Hypomnema lint exits are `0`, `0` and
`0`.

### Leads not pursued

Leads not pursued: `marshal.loads`; wildcard and dynamic imports; assignment,
lexical-scope, taint and control-flow analysis; custom-loader proofs; the
accepted pragma-in-string quirk; and Python file-size policy. In particular,
reassigning an imported safe YAML alias or importing it in another lexical
scope can retain source-local trust. The study names both limits, and the
public contract says assignments are not followed, so changing either requires
a study amendment rather than an audit-side widening.

## Phylax unsafe deserialization, step 1, round 3 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 324 changes the Python
Phylax lint, fixtures, and governed prose; it has no Solidity target`. No
`.sol` path appears from `main` through the accumulated fixed tree. X-Ray and
Solidity Auditor did not run; the waiver applies only to that pair.

The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0 on the
repository-mandated scopes. The manual pass read the complete base-to-stacked
diff and checked all thirteen receipted risks against the round 2 fixes.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | `plugins/hexaemeron/skills/phylax/scripts/phylax.py:215` | A direct YAML boundary import under bare `eval` or `exec`, collected from another lexical scope, displaced the built-in candidate; paired safe-loader evidence could make an outer non-literal dynamic call produce no P008. | fixed and guarded in round 3 |
| S1-R3-review | none | full base-to-stacked diff | No other code, test, record or payload-disclosure finding was confirmed. | clean |
| S1-R3-records | none | study, runbook, evolution and Promise Machine binding | The tracked study remains byte-identical to the receipted artifact, and generation-only bookkeeping remains unchanged. | clean |

Finding count: 1.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `source-parse` | P008 still uses `ast.parse`, `ast.walk` and the existing visitor without importing, executing or deserializing target source. | clean |
| `call-identity` | Same-family, boundary-to-boundary and boundary-to-neighbour conflicts were exercised; bare built-ins now remain candidates beside direct imports. | fixed by S1-R3-01 |
| `pickle-scope` | Module and direct aliases for `load` and `loads` report once; dumps and unrelated readers remain clean. | clean |
| `marshal-scope` | `load` reports once while the receipted `loads` exclusion remains clean. | clean within scope |
| `yaml-loader` | Module and loader aliases for `SafeLoader` and `CSafeLoader` pass; unsafe and conflicting evidence reports. Lexical-scope trust remains an explicit exclusion. | bounded by the receipted exclusion |
| `dynamic-source` | Bare `eval` and `exec` with non-literal source report even when another scope imports YAML boundaries under those names. Literal source remains clean. | fixed by S1-R3-01 |
| `alias-rebinding` | Conflicts now keep every possible call family, including the implicit built-in family. Assignment and general scope analysis remain excluded. | clean within scope |
| `suppression-line` | The existing reason-bearing and bare pragma cases retain opposite results. | clean |
| `diagnostic-output` | Conflict cases emit one fixed unresolved-family message per call, omit payload text in text and JSON, and retain stable order under two hash seeds. | clean |
| `classification-drift` | P000 through P007 guards, both focused interpreter runs and the full plugin suite pass. | clean |
| `analysis-work` | The fix adds one set member and a constant-size union per bare dynamic call; it adds no recursive walk, dataflow or target execution. | clean |
| `partial-run` | Every recorded test and lint reached a terminal zero exit; the two expected red guard runs are identified separately. | clean |
| `ledger-integrity` | `phylax-v1.3.0`, the mature frontier fields and its digest are unchanged; Promise Machine verification exits 0. | clean |

### Evidence

The review started from exact signed stacked head
`f5a2ef2c23c22840dd8f06af62cc759d6a3fd1e3` and re-read all eight paths from
`64096f4d89fc821ab9d91d075cd86be7e7bb92b5`. The tracked and receipted study
copies still hash to
`5eac7e9c171969933bf9d08a07a50aefd0e3f52ff353fada05691271373f397f`.

The reduced guard
`UnsafeDeserialization.test_bare_dynamic_calls_survive_cross_scope_yaml_aliases`
failed twice on the unfixed tree, for both `eval` and `exec`. Each specimen
places a YAML boundary and safe-loader import in another function while the
outer function passes non-literal source and a globals mapping to the actual
built-in. The fix retains the built-in family beside direct-import evidence,
so both calls now emit one ambiguous P008 instead of escaping the rule.

The focused Phylax suite passes 80/80 on Python 3.9.6 and 3.12.13. With the
retained Node v26.6.0 fixture first on `PATH`, the full Hexaemeron suite passes
852/852. The root suite passes 118/118 and the evolution contract passes 8/8.
The full Promise Machine check, both Protasis checks, the Horos boundary check,
the changed-tree Phylax scan and `git diff --check` each exit 0. The
active-plugin Phylax, Ephoros and Hypomnema lint exits are `0`, `0` and `0`.

### Leads not pursued

Leads not pursued: `marshal.loads`; relative, wildcard, dynamic and dotted
imports such as `import yaml.loader`; assignment, general lexical-scope, taint
and control-flow analysis; custom-loader proofs; the accepted pragma-in-string
quirk; and Python file-size policy. Cross-scope YAML module and loader aliases
can still retain source-local trust for an actual `yaml.load` call. Those
limits are inside the receipted exact-import grammar; widening them requires a
study amendment. Bare `eval` and `exec` are no longer allowed to disappear
behind that exclusion.

## Phylax unsafe deserialization, step 1, round 4 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 324 changes the Python
Phylax lint, fixtures, and governed prose; it has no Solidity target`. No
`.sol` path appears in the complete `main`-to-stacked diff. X-Ray and Solidity
Auditor did not run; the waiver applies only to that pair.

The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0 on the
repository-mandated scopes. The manual pass read the complete diff from
`64096f4d89fc821ab9d91d075cd86be7e7bb92b5` through signed head
`dec65fcf1dc52b055d5d188633eb3b3c226f8007` and checked all thirteen
receipted risks against the accumulated fixes.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-review | none | full base-to-stacked diff | No new code, test or payload-disclosure finding was confirmed. | clean |
| S1-R4-tests | none | P008 focused and round-4 probe suites | No classification, ordering or diagnostic-secrecy failure was confirmed. | clean |
| S1-R4-records | none | study, runbook, evolution and Promise Machine binding | No record drift or unreceipted boundary change was confirmed. | clean |

Finding count: 0.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `source-parse` | P008 still uses `ast.parse`, `ast.walk` and the existing visitor; the checker neither imports nor runs target source. | clean |
| `call-identity` | Same-scope, late and cross-scope module/direct imports, neighbour conflicts and boundary-family conflicts retain one conservative result. | clean |
| `pickle-scope` | Module/direct `load` and `loads` report once; dump calls and unrelated readers stay clean. | clean |
| `marshal-scope` | `load` reports once and the receipted `loads` exclusion stays clean. | clean within scope |
| `yaml-loader` | Positional and keyword `SafeLoader`/`CSafeLoader` forms pass; absent, unsafe, unknown and conflicting loader evidence reports. | clean |
| `dynamic-source` | Bare and resolved `eval`/`exec` report names, calls and f-strings; inline string/bytes constants pass. | clean |
| `alias-rebinding` | Conflicting identities retain one unresolved-family result, and bare built-ins survive YAML aliases from another scope. Assignment and general scope analysis remain excluded. | clean within scope |
| `suppression-line` | Reason-bearing and bare pragma fixtures retain opposite results. | clean |
| `diagnostic-output` | Conflict probes emit one fixed message, omit payload text and return identical JSON under hash seeds 1 and 947. | clean |
| `classification-drift` | The 61 pre-existing cases inside the 80-test focused suite pass on Python 3.9.6 and 3.12.13; P000 through P007 remain guarded. | clean |
| `analysis-work` | Import collection is one linear AST walk, followed by constant-size candidate checks per call; no dataflow or target execution enters. | clean |
| `partial-run` | Both focused runs, all three required lints and every supporting check below reached terminal exit 0. | clean |
| `ledger-integrity` | Receipted and tracked artifacts match, `phylax-v1.3.0` advances generation only, the mature frontier fields stay fixed, and Promise Machine verification passes. | clean |

### Evidence

The focused Phylax suite passes 80/80 on Python 3.9.6 and 3.12.13. A separate
round-4 matrix passes 28 same/cross-scope call cases and four ambiguous-message
guards. The root suite passes 118/118 and the evolution contract passes 8/8.
The repository Phylax scan, Promise Machine check, both Protasis checks, Horos
boundary check and `git diff --check` each exit 0. Active-plugin lint exits are
Phylax 0, Ephoros 0 and Hypomnema 0.

The receipted and tracked study copies both hash to
`5eac7e9c171969933bf9d08a07a50aefd0e3f52ff353fada05691271373f397f`;
the runbook copies both hash to
`678e406845563e2bb51cae9dbbcc6d0b3d6f048ee3d3e8a68ceb84b71decdf07`.
The checked `SKILL.md` hashes to
`fc3fdf6bf76cd24bf602d39ae30d1b77b1f196a34e0207522fec7ff9115007ca`,
matching its Promise Machine pin.

No retained Node v26.6.0 binary was present, so round 4 did not repeat the
supplementary full Hexaemeron suite. Round 3's 852/852 run remains the latest
full-suite evidence for this exact code head; it is not counted as a round-4
execution.

### Leads not pursued

Leads not pursued: `marshal.loads`; relative, wildcard, dynamic and dotted
imports; assignment, general lexical-scope, taint and control-flow analysis;
custom-loader proofs; the accepted pragma-in-string quirk; and Python file-size
policy. Cross-scope YAML module and loader aliases can retain source-local
trust for an actual `yaml.load` call. The receipted study excludes that scope,
so changing it would require an amendment rather than an audit-side widening.

## Elenchus audit-round verdict, step 1, round 1 -- 2026-08-22

### Suite disposition

The controller waiver is exact: `waived: issue 327 changes Python controller
state, Elenchus integration, tests, and governed prose; it has no Solidity
target`. No `.sol` path appears in `454bf3c..b8acf611` or the stacked fix.
X-Ray, Solidity Auditor and Fizz did not run. The active-plugin Phylax,
Ephoros and Hypomnema lints each exit 0 on their repository scopes.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/tests/run_tests.py:13` | Report containment was checked before arbitrary tests ran, but the later write reused a relative path and followed ancestor components. A test could change the process directory or replace a validated parent with a symlink, redirecting the report outside the worktree. | fixed; manual guard red, Elenchus verdict `passed` |
| S1-R1-review | none | full `454bf3c..b8acf611` diff plus stacked fix | No other report-schema, exit-semantics, source-contract or path-control finding was confirmed. | clean |
| S1-R1-records | none | study, runbook and generation rows | The three governed frontiers and their held targets retain the prior revision and digest. The tracked artifact differences are recorded below. | clean |

Finding count: 1.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `fix-claim-confusion` | Step 1 does not change `audit-round`; the study keeps `--fixes-commit` as the only machine fix claim for step 2. | reviewed; not applicable to this step's code |
| `enum-drift` | The Elenchus classifier and its four result strings are unchanged; report fixtures retain the exact unittest schema. | clean |
| `command-substitution` | The runbook owns the exact command/report triplet. The runner parses one path and never evaluates it through a shell. | clean |
| `legacy-round-breakage` | Step 1 changes no Fiat state reader or writer. Legacy-round fixtures belong to step 2. | reviewed; not applicable |
| `receipt-overclaim` | The Elenchus contract calls the future field a declaration and says it does not attest report bytes or command execution. | clean |
| `downstream-loss` | Step 1 adds no issue 429 schema or issue 369 synopsis path. Both remain named dependent work. | reviewed; not applicable |
| `frontier-drift` | `elenchus-v1.2.0` and `protasis-v4.6.0` advance generation only; prior frontier revision, digest, status and target bytes are retained. | clean |

### Evidence

The review read the complete eight-path diff from
`454bf3c9930c94985e5eb6179f3b01be2bf741c2` through
`b8acf61151b60484a8477786ef5a7f0c2b9c6035`. The reduced cwd-rebinding and
parent-symlink cases both failed on that unfixed head. The first wrote the
relative report under the suite-selected directory; the second returned 0
after creating the report through the outside symlink.

The fix pins the resolved worktree with a directory descriptor, opens or
creates every report-parent component relative to that descriptor with
`O_NOFOLLOW`, and creates the final file with `O_EXCL`. Short writes continue
until complete; an error removes only the inode this invocation created.
Eight focused runner-result cases pass, including cwd rebinding, ancestor
replacement, dangling targets and a forced partial write.

The exact runbook Elenchus invocation under pinned Node v26.6.0 returns
`passed`: 860 executed tests, zero assertion failures and zero errors. This is
not mechanical red-parent evidence. `changed_tests()` classifies both changed
paths under `plugins/hexaemeron/tests/` as tests, so it overlays the fixed
`run_tests.py` beside the new guards on the parent. The two focused manual red
runs above remain separate evidence and the recorded verdict is not relabeled.

Under pinned Node v26.6.0, the focused Elenchus/Fiat/Protasis suite passes
153/153 and the full Hexaemeron suite passes 860/860. The root suite passes
118/118. Both Protasis checks, the three active-plugin lints and
`git diff --check` exit 0. The unwrapped focused command reaches host Node
v22.22.3 and fails only the fixture's exact v26.6.0 assertion; it is recorded
as environment evidence, not a green gate.

The receipted study hashes to
`06f8e81b95c7ceba26ada998fe62b57a87d9afa3eea10a31813862842851abe0`.
Its tracked copy changes only five links to remain relative to the committed
directory. The receipted runbook hashes to
`82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85`;
the tracked copy removes one terminal blank line after the exact copy failed
`git diff --check`.

### Leads not pursued

Leads not pursued: issue 429's audit schema, issue 453's evidence binding and
production `guarded` gate, and Fiat's step-2 controller field. Tests run with
the caller's operating-system authority and can write elsewhere directly;
this fix establishes only that the report writer does not redirect its own
declared output. Mechanical red-parent classification for an implementation
under a test directory remains an evidence discrepancy; changing Elenchus's
test-file boundary is outside step 1, and issue 453 owns the blocking policy.
No further step-1 lead remained after the full diff review.

## Elenchus audit-round verdict, step 1, round 2 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 327 changes Python
controller state, Elenchus integration, tests, and governed prose; it has no
Solidity target`. No Solidity path changed. X-Ray, Solidity Auditor and Fizz
did not run. The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0
on their repository scopes.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `plugins/hexaemeron/tests/run_tests.py:13` | The round-1 fix held its worktree directory descriptor across arbitrary in-process tests. A test could close that descriptor and reopen an outside directory in the same numeric slot; the report writer then trusted the rebound slot and wrote outside the worktree. | fixed in `cc984ba`; manual guard red, Elenchus verdict `passed` |
| S1-R2-02 | low | `plugins/hexaemeron/tests/run_tests.py:68` | The unsupported-platform gate collapsed every absent secure-directory primitive into one generic error, so an operator could not identify which required control was missing. | fixed in `cc984ba`; manual guard red |
| S1-R2-review | none | full `454bf3c..cc984ba` diff | No further schema, exit-semantics, containment, descriptor-lifetime or record finding was confirmed. | clean |
| S1-R2-records | none | study, runbook and generation rows | The changed contracts still describe a four-state declaration rather than report-byte attestation, and the governed frontiers remain fixed. | clean |

Finding count: 2.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `fix-claim-confusion` | This round has a signed fixes commit. Step 1 cannot yet store the verdict in Fiat state, so the audit record preserves `passed` without claiming a controller receipt that does not exist. | clean within step 1 |
| `enum-drift` | The exact runbook invocation returned the existing `passed` status. The classifier and `elenchus.unittest.v1` fields are unchanged. | clean |
| `command-substitution` | The comparison used the source runbook's exact command, `unittest-json-v1` format and `.elenchus/hexaemeron-unittest.json` path under pinned Node v26.6.0. | clean |
| `legacy-round-breakage` | Step 1 still changes no Fiat state reader or writer. Legacy-round behavior remains step 2 work. | reviewed; not applicable |
| `receipt-overclaim` | The audit record keeps mechanical `passed` separate from the two manual red-parent guards and does not relabel it `guarded`. | clean |
| `downstream-loss` | No issue 429, 369 or 453 consumer changed in this step. | reviewed; not applicable |
| `frontier-drift` | The evolution/version tests pass 14/14; Elenchus and Protasis retain their prior revision, digest, status and held target while advancing generation only. | clean |

### Evidence

The descriptor reproducer on `0eacf593` observed root slot 3 closed and an
outside directory reopened as slot 3. `write_report` then left no inside file
and created the declared nested report outside. The new black-box guard fails
on that parent at `assertTrue(report.is_file())`. A second parent run fails
because the old refusal names none of `os.open(dir_fd)`, `os.mkdir(dir_fd)`,
`os.stat(dir_fd)`, `os.unlink(dir_fd)` or `os.stat(follow_symlinks)`.

The fix retains the canonical root and its `(st_dev, st_ino)` identity rather
than a live descriptor. It reopens and verifies that directory only after the
suite, walks report parents through owned directory descriptors with
`O_NOFOLLOW`, and closes root, parent and report handles on success and error
paths. A partial write loops until complete; a zero, exception or failed close
cannot produce a parseable complete report through this path. Unsupported
hosts now fail before test discovery and name every missing primitive.

The ten focused report-adapter cases pass on the fixed tree. Under offline,
pinned Node v26.6.0, the Elenchus/Fiat/Protasis focus passes 155/155 and the
complete Hexaemeron suite passes 862/862 in 153.871 seconds. The root suite
passes 118/118. The evolution/version tests pass 14/14. Both Protasis checks,
Promise Machine verification, all three active-plugin lints and
`git diff --check` exit 0. The exact runbook Elenchus comparison on signed
commit `cc984ba840d45105a20479331cec8622fc38fbe2` returns `passed`.

The receipted study still hashes to
`06f8e81b95c7ceba26ada998fe62b57a87d9afa3eea10a31813862842851abe0`.
Every one of its seven risk ids has a disposition above.

### Leads not pursued

Leads not pursued: issue 429's audit schema, issue 453's evidence binding and
production `guarded` gate, Fiat's step-2 controller field, and hostile
background threads that continue manipulating descriptors after the suite
returns. In-process tests already share the runner's operating-system
authority; this fix removes the deterministic descriptor inherited across the
whole suite and fails closed when the recorded root identity changes. A crash
can still leave a partial fresh file, but Elenchus rejects malformed or
incomplete JSON rather than accepting it as a completed report.

## Elenchus audit-round verdict, step 1, round 3 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 327 changes Python
controller state, Elenchus integration, tests, and governed prose; it has no
Solidity target`. No Solidity path changed. X-Ray, Solidity Auditor and Fizz
did not run. The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-review | none | full `454bf3c..3b394541` diff | No report-schema, path-containment, descriptor-lifetime, source-contract or record finding was confirmed. | clean |
| S1-R3-guards | none | `plugins/hexaemeron/tests/run_tests.py` | Both prior escapes remain reproducible on their parents and refused on the fixed tree; worktree replacement also fails closed. | clean |
| S1-R3-records | none | report and governed ledgers | The report matches the runbook contract and both generation rows retain their governed frontiers. | clean |

Finding count: 0.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `fix-claim-confusion` | This clean round has no fixes commit, so it records no Elenchus verdict. The full-suite report below is test evidence, not a fix receipt. | clean |
| `enum-drift` | The pinned Elenchus/Fiat/Protasis focus exercises all four classifier strings and passes 155/155; the runner report keeps the exact `elenchus.unittest.v1` fields. | clean |
| `command-substitution` | The pinned invocation used the receipted runbook's exact Python command, `unittest-json-v1` format and `.elenchus/hexaemeron-unittest.json` path without shell interpolation inside the runner. | clean |
| `legacy-round-breakage` | Step 1 still changes no Fiat state reader or writer. The legacy-round path remains step 2 work. | reviewed; not applicable |
| `receipt-overclaim` | The generated report is recorded as current-tree suite evidence only. It is not relabeled `guarded`, and no controller receipt is claimed for a field the installed controller does not have. | clean |
| `downstream-loss` | No issue 429, 369 or 453 consumer changed in this step. | reviewed; not applicable |
| `frontier-drift` | The 14 evolution and version checks pass; Elenchus and Protasis retain their prior revision, digest, status and held target while advancing generation only. | clean |

### Evidence

The review read the complete diff from entry commit
`454bf3c9930c94985e5eb6179f3b01be2bf741c2` through pre-round head
`3b394541599f48607edc28b6a2606a998de55b3d`. It reproduced both fixed faults
directly from their signed parents. On `b8acf611`, replacing the missing report
parent with an outside symlink created the report outside the worktree. On
`0eacf593`, closing the retained root descriptor and reopening an outside
directory into the same slot created the nested report outside.

The fixed tree's ten report-adapter cases pass, including both prior faults,
cwd rebinding, partial writes, fresh-target enforcement and the named
unsupported-operation refusal. A separate root-replacement probe moved the
recorded worktree aside, created a new directory at its path and observed
`report worktree identity changed`; neither directory received a report.

Under pinned Node v26.6.0, the Elenchus/Fiat/Protasis focus passes 155/155. The
exact runbook report command passes 862/862 in 149.917 seconds. Its 161-byte,
mode-0600 JSON object records `testsRun: 862`, zero failures, zero errors and
schema `elenchus.unittest.v1`; its SHA-256 is
`7f51f15b8bb35b792c348e247f85461d3f4074f41348a6fdbd64417820a4db43`.
The generated report was removed after inspection.

The root suite passes 118/118. The focused runner plus evolution/version gate
passes 24/24. Promise Machine verification, both Protasis checks, the Horos
boundary check, all three active-plugin lints and `git diff --check` exit 0.

### Leads not pursued

Leads not pursued: issue 429's audit schema, issue 453's evidence binding and
production `guarded` gate, Fiat's step-2 controller field, and hostile
background threads with the runner's own operating-system authority. The
receipted runbook's extra terminal byte remains the round-1 recorded artefact
discrepancy: the tracked copy removes only that final blank line so
`git diff --check` can pass. Round 3 does not rewrite either source.

## Elenchus audit-round verdict, step 2, round 1 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 327 changes Python
controller state, Elenchus integration, tests, and governed prose; it has no
Solidity target`. No Solidity path changed. X-Ray, Solidity Auditor and Fizz
did not run. The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-review | none | full `72309e09..93853281` step diff | No enum, mutation-order, verified-range, legacy-reader, source-packet, release or record fault was confirmed. | clean |
| S2-R1-inherited | none | full `454bf3c9..93853281` issue diff | The inherited runner and Elenchus/Protasis contracts still supply the exact command/report triplet and four classifier strings without widening the receipt claim. | clean |
| S2-R1-runtime | none | `tests/promise_machine_coverage.json` | Exactly three existing Fiat runtime-source digests moved from `61184838` to `01efd29f`; their binding maps and canonical promise text did not change. | clean |

Finding count: 0. This round has no fixes commit and therefore no Elenchus
verdict. The current-tree report below is suite evidence, not a detached-parent
guard result.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `fix-claim-confusion` | `cmd_audit_round` requires the verdict only for a non-empty `--fixes-commit`, then verifies the exact base-to-head range before storing either field. Missing and unbound values leave state and ledger digests unchanged. | clean |
| `enum-drift` | `ELENCHUS_VERDICTS`, argparse, state, ledger, stdout and both skill contracts carry exactly `guarded`, `unguarded`, `passed`, and `inconclusive`. The 38-case focused contract gate exercises the runner and receipt fixtures. | clean |
| `command-substitution` | The receipted runbook SHA-256 is `82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85`. Step 2 is selected by exact number and title with its Markdown, real path and full-source digest; Mason's packet is unchanged. | clean |
| `legacy-round-breakage` | A round with no field passes `status`, `next`, `verify`, a later fixed round and `done audit`; the later round retains the missing key rather than manufacturing a fifth value. | clean |
| `receipt-overclaim` | Fiat describes the value as checked-and-recorded operator evidence beside `verified_commits`. It does not claim the report ran, attest report bytes or block a non-`guarded` value. | clean |
| `downstream-loss` | The table-driven fixture preserves all four strings in state and ledger plus null for a no-fix round. Issue 429, 369 and 453 surfaces are unchanged. | clean |
| `frontier-drift` | The 14 evolution/version checks pass. Elenchus `v1.2.0`, Fiat `v5.12.1` and Protasis `v4.6.0` are generation rows retaining each prior revision and digest; mature/held targets are unchanged. Hexaemeron package surfaces agree on `1.5.5`. | clean |

### Evidence

The signed implementation head is
`93853281c8b94b15e103da38b557be6e2600c1ad`, directly above
`72309e099b5d410a8eee9390f4f6adf8cfa0a729`, with both required provenance
trailers. The amended receipted study hashes to
`e416668d0adb0c986ee1080b92ba9f6c07f151ba7b13ecf776b664a75dc26870`.
Its seven risk ids are each disposed above. The amendment permits only the
three runtime digest refreshes proved by the diff and Promise Machine check.

Under pinned Node v26.6.0, the step-2 controller and contract suite passes
307/307. The focused runner, verdict, skill and version fixtures pass 38/38,
and the evolution/version gate passes 14/14. The exact runbook report command
passes 872/872 in 162.140 seconds. Its fresh 161-byte, mode-0600 JSON object
records schema `elenchus.unittest.v1`, `testsRun: 872`, zero failures and zero
errors; its SHA-256 is
`f0b0d7a7b6943d3907c5b17bb97fc30274d7d68a42a59a4c9b462acd8692cad9`.
The report was removed after inspection.

The root suite passes 118/118. Promise Machine verification, both Protasis
checks, the Horos boundary check, all three active-plugin lints and
`git diff --check` exit 0. The controller source hashes to
`01efd29fcc0b1198aa62989291c1dbe4713d7c26cccbba40a1fbe4b210884870`,
matching all three amended runtime bindings. This round's exact prose passes
Imprimatur and Brevitas; the four changed governed contracts also pass
Imprimatur.

### Leads not pursued

Leads not pursued: issue 429's audit schema and synopsis, issue 369's later
study source, issue 453's report-byte binding and production `guarded` gate,
and issue 363's delegation identity frontier. The installed v5.11.1 controller
cannot emit step 2's new `runbook_step` field or receipt its verdict; this
self-hosting round bound the receipted source manually and does not claim that
the old controller recorded a field it lacks. No further step-2 lead remained.

## Elenchus audit-round verdict, step 3, round 1 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 327 changes Python
controller state, Elenchus integration, tests, and governed prose; it has no
Solidity target`. No Solidity path changed. X-Ray, Solidity Auditor and Fizz
did not run. The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | `plugins/hexaemeron/docs/elenchus-audit-round-verdict/proof.md:13` | The proof deleted its disposable repository after publishing packet, state, ledger and commit hashes that depended on generated paths, timestamps and signing metadata. It retained no hashed bytes or complete definition of the hash inputs. A fresh reader had a behavioral replay with no way to verify those fixed values. | fixed in `d55da516`; replay now asserts within-run relations, prints run-local digests and fixes source-byte hashes across runs; Elenchus verdict `unguarded` |
| S3-R1-02 | low | `plugins/hexaemeron/docs/elenchus-audit-round-verdict/proof.md:68` | The reproduction used a separate `git commit -m` paragraph for each required provenance trailer. Git inserted a blank line between them while the prose claimed consecutive final lines. | fixed in `d55da516`; one message paragraph carries both lines and the replay checks all five signed commits |
| S3-R1-review | none | full `024a64d9..d55da516` step diff | No controller, schema, legacy-reader, release, boundary or record fault remained after the proof repair. | clean |
| S3-R1-release | none | all mutable Hexaemeron release surfaces | Skill, package, marketplace, Promise coverage and frontier values agree. | clean |

Finding count: 2.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `fix-claim-confusion` | The real controller demo ties the verdict obligation only to a non-empty signed fixes range. Each unbound or incomplete receipt exits 2 before state or ledger drift. | clean |
| `enum-drift` | State and ledger assertions preserve `guarded`, `unguarded`, `passed` and `inconclusive` as four distinct values, plus explicit null and a missing legacy key. | clean |
| `command-substitution` | Mason and Warden reconstruct the same five-field Step 1 source block from runbook SHA-256 `82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85`. This round used Step 3's exact Python command, `unittest-json-v1` format and report path for `d55da516`. | clean |
| `legacy-round-breakage` | The replay removes the key from state and ledger, repairs the canonical state fingerprint and ledger tail, then requires `status`, audit-round 2 `next`, `verify`, a later signed round, close and final `prose`. | clean |
| `receipt-overclaim` | Run-local digests are labeled diagnostics, fixed hashes bind only stable source bytes, and the `unguarded` declaration is not called report-byte attestation. | clean |
| `downstream-loss` | Official GitHub issue state still shows 429, 369, 453 and 363 open in that order. No downstream schema or gate changed; all four values remain available to them. | clean |
| `frontier-drift` | Elenchus, Fiat and Protasis retain frontier digests `08e77bae`, `e413d604` and `10140710`; version tests pass 14/14 and Hexaemeron package surfaces agree on `1.5.5`. | clean |

### Evidence

The review read the complete step diff from parent
`024a64d9265ca21551cfab4a969657e7cefef2ad` through implementation
`1ad770c296621de55ad99f3368439c0c25fe67e9`, then repaired only the proof in
signed commit `d55da516fcd652beddcad82219170079c5491129`. That commit has the two
required consecutive provenance lines and a valid local signature.

The final proof's Bash blocks replay clean as one script. They create a fresh
repository, compare repeated Mason and Warden packets, require all three
exit-2 refusals to preserve raw state and ledger bytes, assert explicit null,
repair and exercise a missing-key legacy round, and record four sequential
single-commit signed ranges. State and ledger both expose `missing`, `guarded`,
`unguarded`, `passed` and `inconclusive` in order. Each range contains only its
named head in `verified_commits`; close moves the step to `prose`; final
`verify` succeeds. The cleanup checks the generated parent and prefix before
removal, then proves the boundary is absent. No credential or raw signature
bytes enter the record.

The exact runbook Elenchus invocation on `d55da516` returns `unguarded` because
the proof repair changes no test file. Under pinned Node v26.6.0, the exact
runbook report command passes 872/872 in 157.807 seconds. Its fresh 161-byte,
mode-0600 JSON object records schema `elenchus.unittest.v1`, `testsRun: 872`
and zero failures or errors; SHA-256 is
`f0b0d7a7b6943d3907c5b17bb97fc30274d7d68a42a59a4c9b462acd8692cad9`.
The generated report was removed after inspection.

The root suite passes 118/118, Imprimatur's suite passes 62/62, and the
evolution/version gate passes 14/14. Promise Machine verification, both
Protasis checks, all three active-plugin lints, the Horos boundary check,
Imprimatur and Brevitas over the repaired proof, and `git diff --check` exit 0.

The amended receipted study keeps its original bytes at
`06f8e81b95c7ceba26ada998fe62b57a87d9afa3eea10a31813862842851abe0`
and its exact 888-byte suffix at
`51e378a68b0c39a59b8ba0051b35a8b8ecc6a691446c5862bfbe34eae095debb`.
The committed copy changes only five links before the same suffix. The tracked
runbook is exactly the receipted 11,430-byte file without its final byte, as
already recorded.

### Leads not pursued

Leads not pursued: the exact Elenchus result is `unguarded`, as expected for a
documentation-only fix; issue 453 owns any later policy that blocks that value.
Issues 429, 369, 453 and 363 remain open downstream work. Historical run-local
hashes are not retained as evidence after their bytes are deleted; the replay
instead proves the relations that carry the acceptance claim. No further
step-3 lead remained.

## Elenchus audit-round verdict, step 3, round 2 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 327 changes Python
controller state, Elenchus integration, tests, and governed prose; it has no
Solidity target`. No Solidity path changed. X-Ray, Solidity Auditor and Fizz
did not run. The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | `plugins/hexaemeron/docs/elenchus-audit-round-verdict/proof.md:21` | The committed reproduction copied its study, runbook and step list from the active run's untracked `.hexaemeron` files and created its fixture below that pre-existing directory. A clean detached checkout failed before the demo began, so the durable proof depended on state removed by Fiat reset. | fixed in `27f78d96`; the replay now uses tracked study and runbook bytes, reconstructs the receipted terminal newline and step list, and creates then removes the ignored state directory when absent |
| S3-R2-02 | low | `plugins/hexaemeron/docs/elenchus-audit-round-verdict/proof.md:83` | The prose said every proof-owned commit carried both provenance trailers, but the script's signed demo-base commit does not. The executable check covers the receipted implementation and four fix commits. | fixed in `27f78d96`; the claim now names only receipted implementation and fix commits |
| S3-R2-review | none | full `024a64d9..27f78d96` step diff | No controller, receipt-schema, legacy-reader, release, cleanup or record fault remained after the proof repair. | clean |
| S3-R2-round1 | none | round 1 log and `d55da516` | Round 1 records its two findings and `unguarded` verdict without claiming a guard. Its fix has a valid signature and the two exact final provenance lines. | clean |

Finding count: 2.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `fix-claim-confusion` | The clean-checkout replay again requires a verdict only beside a non-empty signed fixes range. Each incomplete or unbound receipt exits 2 and independently preserves raw state and ledger bytes. | clean |
| `enum-drift` | State and ledger assertions retain explicit null, a missing legacy key, and the four distinct values `guarded`, `unguarded`, `passed` and `inconclusive`. | clean |
| `command-substitution` | Tracked runbook bytes hash to `a98c67bd`; appending the one recorded terminal newline reconstructs receipted SHA-256 `82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85`. Repeated Mason and Warden packets carry the same five-field source block. This round used Step 3's command, `unittest-json-v1` format and report path for `27f78d96`. | clean |
| `legacy-round-breakage` | The replay repairs the state fingerprint and ledger tail after omitting both keys, then requires `status`, round-2 `next`, `verify`, a later signed round, close, final `verify` and phase `prose`. | clean |
| `receipt-overclaim` | Generated packet, state, ledger and demo-commit hashes remain run-local diagnostics. Fixed values bind only tracked source, receipted artefact, amendment and frontier bytes. The `unguarded` result remains a recorded declaration, not report-byte attestation. | clean |
| `downstream-loss` | The replay retains all four values independently in state and ledger. The public GitHub issue pages showed 429, 369, 453 and 363 open on 2026-08-22; this step changes none of their owned surfaces. | clean |
| `frontier-drift` | The 14 evolution/version checks pass. Elenchus, Fiat and Protasis retain frontier digests `08e77bae`, `e413d604` and `10140710`; both manifests and both marketplaces retain Hexaemeron `1.5.5`. | clean |

### Evidence

A clean detached checkout at `773fb670d72fde9e936d321f57779dbd056f06d0`
had no `.hexaemeron` directory. The original concatenated Bash replay exited 1
when `mktemp` could not create its child there. That failure localised the
mechanism before the proof changed.

Signed fix `27f78d96d2f1b1f91c9e60ab70ebe0fb338d3c71` reads only tracked
delivery documents, checks their fixed hashes, recreates the receipted
runbook's one missing newline, writes the three step titles, and scopes cleanup
to the generated prefix below `.hexaemeron`. The same concatenated replay at
that detached commit starts with no state directory, exits 0, leaves no state
directory or symlink, and leaves the checkout clean. It asserts every refusal,
null, legacy repair, verdict, verified range, adjacent parent, trailer,
signature, close and final phase named by the runbook.

The exact runbook Elenchus invocation on `27f78d96` returns `unguarded` because
the fix changes no test file. Under pinned Node v26.6.0, the current-tree report
command passes 872/872 in 156.409 seconds. Its 161-byte, mode-0600 JSON object
records schema `elenchus.unittest.v1`, `testsRun: 872`, `complete: true`, and
zero failures, errors, skips, expected failures or unexpected successes. Its
SHA-256 is
`f0b0d7a7b6943d3907c5b17bb97fc30274d7d68a42a59a4c9b462acd8692cad9`.
The generated report was removed after inspection.

The root suite passes 118/118, Imprimatur's suite passes 62/62, and the
evolution/version gate passes 14/14. Promise Machine verification, both
Protasis checks, the Horos boundary check, all three active-plugin lints,
Imprimatur and Brevitas over this round and the fixed proof, and
`git diff --check` exit 0.

### Leads not pursued

Leads not pursued: the fix is documentation-only, so `unguarded` is the exact
Elenchus result; issue 453 owns any later blocking policy. Issues 429, 369, 453
and 363 remain open downstream work. The clean replay now depends only on
tracked release bytes and its configured signing key. No further step-3 lead
remained after the repair.

## Elenchus audit-round verdict, step 3, round 3 -- 2026-08-22

### Suite disposition

The controller waiver remains exact: `waived: issue 327 changes Python
controller state, Elenchus integration, tests, and governed prose; it has no
Solidity target`. No Solidity path changed. X-Ray, Solidity Auditor and Fizz
did not run. The active-plugin Phylax, Ephoros and Hypomnema lints each exit 0.

### Finding table

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-review | none | full `024a64d9..017a7418` step diff | No proof, source-bound packet, legacy-reader, release, cleanup, trailer-scope or record fault was confirmed. | clean |
| S3-R3-proof | none | `plugins/hexaemeron/docs/elenchus-audit-round-verdict/proof.md` | The concatenated replay succeeds from a clean detached checkout with no active Fiat state and leaves that checkout clean. | clean |
| S3-R3-round2 | none | `27f78d96` and round 2 log | Both round-2 findings are fixed, the fix is signed with the two exact final provenance lines, and its exact Elenchus result is `unguarded`. | clean |

Finding count: 0. This round has no fixes commit and therefore no Elenchus
verdict.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `fix-claim-confusion` | The clean replay requires a verdict only beside a non-empty verified fix range. Missing, unbound and unknown values each exit 2 without changing state or ledger bytes. | clean |
| `enum-drift` | State and ledger retain explicit null, a missing legacy key, and the four distinct values `guarded`, `unguarded`, `passed` and `inconclusive`. | clean |
| `command-substitution` | The replay reads tracked study and runbook files, reconstructs the receipted terminal newline, checks the full runbook digest and requires equal five-field Mason and Warden step packets. | clean |
| `legacy-round-breakage` | The replay repairs the state fingerprint and ledger tail after removing both keys, then requires `status`, `next`, `verify`, a later fix round, audit close and final phase `prose`. | clean |
| `receipt-overclaim` | Fixed hashes cover stable source bytes. Generated packet, state, ledger and commit hashes stay run-local, and no recorded verdict is called report-byte attestation. | clean |
| `downstream-loss` | The proof preserves every accepted value independently. The step diff changes no issue 429, 369, 453 or 363 owned surface. | clean |
| `frontier-drift` | The 14 evolution/version checks pass. Elenchus, Fiat and Protasis retain their prior frontier digests and Hexaemeron package surfaces agree on `1.5.5`. | clean |

### Evidence

A detached checkout at `017a74189b15b95af72d16c79c48ec07730b7e7e`
started without `.hexaemeron`. The proof's concatenated Bash blocks exited 0,
asserted the three refusal cases independently, exercised null and missing-key
rounds, stored all four verdicts, verified each single-commit range, closed the
audit and removed the generated boundary. The checkout had no tracked change
or untracked file afterward. The proof and study blobs at `27f78d96` equal
their current-head blobs, so the replay covers the round-2 fix rather than a
later rewrite.

The proof scopes its trailer claim to the receipted implementation and four
fix commits. Its executable check requires each message to end in one exact
copy of both consecutive provenance lines and requires `git verify-commit` to
exit 0. The delivery's five commits from `1ad770c2` through `017a7418` also
have valid local signatures and the same two final lines. Running the exact
runbook Elenchus invocation on signed fix `27f78d96` returns `unguarded`
because that commit changes no test file.

Under pinned Node v26.6.0, the full Hexaemeron suite passes 872/872 in 158.756
seconds. The root suite passes 118/118, Imprimatur's suite passes 62/62, and
the evolution/version gate passes 14/14. Promise Machine verification, both
Protasis checks, the Horos boundary check, all three active-plugin lints and
`git diff --check` exit 0. The current proof and this step's audit additions
pass Imprimatur and Brevitas.

The committed study's 888-byte amendment hashes to
`51e378a68b0c39a59b8ba0051b35a8b8ecc6a691446c5862bfbe34eae095debb`.
The tracked runbook is 11,429 bytes; one terminal newline reconstructs the
11,430-byte receipted file and SHA-256
`82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85`.
The controller source hashes to
`01efd29fcc0b1198aa62989291c1dbe4713d7c26cccbba40a1fbe4b210884870`,
matching the three Fiat runtime bindings checked by Promise Machine.

### Leads not pursued

Leads not pursued: `unguarded` is the expected exact result for the
documentation-only round-2 fix, and issue 453 owns any later blocking policy.
Issues 429, 369, 453 and 363 remain separately owned downstream work. The
checked proof needs Python 3.12, the named shell tools and a configured signing
key; none is hidden in active Fiat state. No further step-3 lead remained.

## Issue 434 observable run record, step 1, round 1 -- 2026-08-23

### Suite disposition

The receipted suite waiver is exact: issue #434 Step 1 changes generated
boundary metadata and Markdown only, with no Solidity path in the complete
run-to-step diff. X-Ray, Solidity Auditor and Fizz did not run. The Phylax,
Ephoros and repository-specified Hypomnema lint exits are `0`, `0` and `0`.

### Finding disposition

Finding count: 0. `S1-R1-review` covers the full run-to-step diff. No Step 1
defect was confirmed. Status: clean.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Step 1 adds no input reader; the study records fixed byte, line, event, nesting, string and collection ceilings for Step 2. | dormant until Step 2 |
| `unsafe-path` | The published copies contain no filesystem-absolute pointer or relative Markdown source link; paths are backticked repository names or absolute web links. | clean |
| `unsafe-deserialisation` | Step 1 adds no deserialiser and names JSON-only, no-execution handling as a Step 2 boundary. | dormant until Step 2 |
| `schema-drift` | No schema or runtime lands in Step 1; the runbook assigns exact schema/runtime binding to Step 2. | dormant until Step 2 |
| `event-order` | No event validator lands in Step 1; the accepted relations and negative fixtures are stated as Step 2 exit evidence. | dormant until Step 2 |
| `correlation-gap` | No correlation implementation lands in Step 1; backward same-run resolution remains a Step 2 requirement. | dormant until Step 2 |
| `evidence-binding` | No evidence consumer lands in Step 1; exact subject, selector and class binding remains a Step 2 requirement. | dormant until Step 2 |
| `evidence-promotion` | The study and ADR state that structural acceptance proves neither truth nor mutation authority and introduce no class ranking. | clean |
| `hidden-reasoning` | The study and ADR refuse hidden model reasoning as observable data; no payload format lands in this step. | clean |
| `sensitive-payload` | Step 1 contains specifications only and permits bounded metadata, digests and references rather than prompts, completions, output, environment or credentials. | clean |
| `optional-host-facts` | The study and ADR require unavailable host, model and token facts to stay omitted or unknown. | clean |
| `token-accounting` | The accepted design limits token values to optional non-negative exposed counts with source, scope and accounting identity, without cost or quality claims. | clean |
| `deterministic-report` | No reporter lands in Step 1; one shared sorted finding model and text/JSON parity remain Step 2 exit evidence. | dormant until Step 2 |
| `partial-record` | No record reader lands in Step 1; final-newline, malformed-tail and lifecycle refusal remain Step 2 requirements. | dormant until Step 2 |
| `command-drift` | Every Step 1 command exits 0. The correct Horos command exits 0; the obsolete `scan . --check` spelling exits 2. A temporary specimen using the five former relative targets emits exactly five H001 findings. | clean |

### Step contract and evidence

The committed study and runbook are byte-identical to the receipted copies.
Their SHA-256 digests are
`685243b2727d0341bfce4869d1c5615fe37e052377ca3a6983ff1bc688d437b3`
and `9eae8f964c2a081c509d29fe78a1adb3f0c837854aa2ef4d91c65b9fa199466d`.
ADR-015 records root Promise Machine ownership, the chosen location split,
three rejected alternatives, the structural-only authority boundary and the
work left outside this issue.

The old-link specimen used these exact former targets from a temporary
directory: `../plugins/hexaemeron/skills/ephoros/SKILL.md`,
`../plugins/hexaemeron/skills/phylax/SKILL.md`,
`../plugins/hexaemeron/skills/metron/SKILL.md`,
`../plugins/hexaemeron/skills/elenchus/SKILL.md`, and
`../plugins/hexaemeron/skills/hypomnema/SKILL.md`. Hypomnema exits 1 with five
H001 findings. The specimen was removed. The obsolete Horos spelling exits 2
with `unrecognized arguments: --check`; the documented
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exits 0 and
reports that the boundary matches the tree.

Both Protasis modes, the repository Hypomnema pass, Imprimatur, all three
Brevitas files, the exact `git diff --check`, and the full run-to-step diff
check exit 0. Root tests pass 118/118. The implementation commit
`19a3f2135b0317904eb91676cabf5da6cb739f35` has a valid local signature and
exactly one required co-author and origin trailer. The diff changes only the
two receipted copies, ADR-015 and the generated Horos boundary.

### Leads not pursued

The Step 2 schema, validator, fixtures, Promise declaration and demonstration
do not exist at the Step 1 exit and were not treated as implemented. A direct
Hypomnema scan of the historical audit log reports two old H003 specimens at
lines 6119 and 6269; the repository's required pointer-gate scope excludes
`audit/AUDIT.md`, and the current step neither creates nor changes those
specimens. No other lead remains.

## Issue 434 observable run record, step 2, round 1 -- 2026-08-23

### Suite disposition

The suite waiver is exact: Step 2 adds JSON, Python, fixtures and Markdown and
ships no Solidity. X-Ray, Solidity Auditor and Fizz did not run. The full
run-to-Step 2 tree was read without Horos exclusions. Phylax, Ephoros and
Hypomnema exit `0`, `0` and `0` after the fixes below.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `scripts/run_observation.py` | A regular input that grew after `lstat` bypassed the 1 MiB total-byte ceiling. One growing overlong line also bypassed it while the drain loop searched for a newline. | fixed in this round; both races were reproduced without `RO002`, then guarded |
| S2-R1-02 | high | `scripts/run_observation.py` | Hostile JSON types reached set membership, regular-expression and numeric relation operations. Invalid event types, statuses, evidence digests and retry attempts raised `TypeError` instead of returning a finding. | fixed in this round; five typed mutations now refuse with `RO007` without crashing |
| S2-R1-03 | medium | `scripts/run_observation.py` | The runtime accepted an empty evidence selector and the finite-overflow JSON number `1e999`, although the schema refuses both. The schema test bound event names but not runtime field sets or status and evidence-class enums. | fixed in this round; each mismatch was reproduced red and the schema/runtime bindings now cover those sets and enums |
| S2-R1-04 | high | `scripts/run_observation.py` | A `run.finished` outcome with status `success` could name a subject that did not match its evidence reference. The accepted record would therefore promote evidence to another subject. | fixed in this round; an outcome subject mismatch now returns `RO012` |
| S2-R1-05 | high | `scripts/run_observation.py` | Forbidden-field matching accepted common aliases such as `api_key` and camel-case `chainOfThought`, allowing a credential-shaped value or hidden-reasoning claim inside metadata. | fixed in this round; field names are normalised and the sensitive-name set covers credential and raw-argument aliases |
| S2-R1-06 | low | `scripts/run_observation.py` | A caller-controlled filename containing a control character split the stable one-finding-per-line text report and the clean result. | fixed in this round; display paths now escape control characters in text and JSON output |

Finding count: 6. All six are fixed and guarded on the stacked audit branch.
A clean second round is required before the audit can close.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static size, running bytes, the overlong-line drain, 512 events, 65,536-byte lines, depth, string and collection bounds were read and exercised. Both post-identity growth cases now return `RO002`. | fixed, round 2 required |
| `unsafe-path` | The command accepts one repository-confined regular non-symlink. Recorded repository paths remain slash-separated relative strings and are never followed. Symlink input refuses, and control characters no longer split display paths. | fixed, round 2 required |
| `unsafe-deserialisation` | JSON uses duplicate-key and non-finite-constant hooks, closed shapes and explicit types. The new mutation guards cover unhashable event/status values, non-string digests and malformed retry attempts. A separate 239-field container mutation pass returned no crash or accepted mutation. | fixed, round 2 required |
| `schema-drift` | The schema id, event union, common and event-specific required/optional fields, evidence classes and both status enums are bound to runtime constants. Empty selectors and finite overflow now refuse, and the release digests were refreshed. | fixed, round 2 required |
| `event-order` | Bad sequence, events after finish, duplicate starts/finishes, unmatched capabilities, invalid retry attempts and retries not aimed at an earlier failed/refused finish are covered. | clean on the fixed tree |
| `correlation-gap` | Parent, capability, retry, refusal, handoff and finish event references resolve backward in the same run; cross-run retry refuses with `RO010`. Each finding preserves bounded run, event and correlation identities when valid. | clean on the fixed tree |
| `evidence-binding` | Every consumed evidence id resolves to an earlier exact subject, scope, time-domain and class definition. Duplicate and absent ids refuse with `RO011`. | clean on the fixed tree |
| `evidence-promotion` | Handoff subject/scope/time-domain and reference classes remain exact. Run outcomes now also preserve the referenced evidence subject and introduce no class ranking. | fixed, round 2 required |
| `hidden-reasoning` | Exact, hyphenated, underscored and camel-case forbidden names are normalised before recursive inspection; nested containers also fail the closed metadata shape. | fixed, round 2 required |
| `sensitive-payload` | Raw prompt, completion, output, environment, payload, argument and credential-shaped field names refuse. Diagnostics contain fixed messages and bounded identities, never rejected values. | fixed, round 2 required |
| `optional-host-facts` | Host and model values require a non-placeholder source and identity. Unavailable facts may be omitted or named under `unknowns`; no placeholder or estimate passes. | clean on the fixed tree |
| `token-accounting` | Counts require a source, scope, accounting identity and at least one non-negative integer. Boolean counts refuse, and no price, cost or quality inference exists. | clean on the fixed tree |
| `deterministic-report` | One sorted `Finding` model feeds text and canonical JSON. Parity tests pass, the finding cap is fixed, and escaped display paths preserve line framing. | fixed, round 2 required |
| `partial-record` | Malformed or overlong final lines, missing newline, absent finish, unresolved start and trailing events all refuse without mutation. | clean on the fixed tree |
| `command-drift` | All runbook commands were executed. The four valid CLIs exit `0`; the five required invalid fixtures exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`; the obsolete Horos spelling exits `2`, while `horos.py check .` exits `0`. | clean on the fixed tree |

### Evidence

The focused suite passes 22/22 and the root suite passes 141/141. All four
valid fixture commands exit `0`. The five required invalid fixtures exit `1`
with their distinct expected codes. Promise Machine sync writes zero files;
the contract check reports 14 identical copies and coverage reports 68/68.
Phylax, Ephoros, Hypomnema, Imprimatur, Brevitas, Horos and
`git diff --check` each exit `0` on the fixed tree. The obsolete
`horos.py scan . --check` spelling exits `2` with its expected argument error.

The runtime and focused-test SHA-256 values are
`d38272fd6e11c7d8482abab409f18b162fc2ee6a0fefbf6381fd38d33fa7bb54`
and
`81c0a1715f2c54fb9d609687ef4471354ecdce656ab1e38eb98538db70bbab32`;
both match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction, persistence and Fiat receipt binding remain in issues
#435 and #436. Cross-run diagnosis remains in issue #449. The schema remains a
published contract rather than an executed dependency: adding a JSON Schema
engine would violate the accepted standard-library boundary, so runtime/schema
agreement stays guarded by exact field, enum, fixture and behavioural tests.
The review did not treat structural conformance as completeness, external
truth, cause, model quality, delivery correctness or a security conclusion.

## Issue 434 observable run record, step 2, round 2 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python, fixture and Markdown
step. X-Ray, Solidity Auditor and Fizz did not run. The complete fixed tree was
read without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and
`0` after the fix below.

### Findings

S2-R2-01 (medium), `scripts/run_observation.py`: finding context copied run,
event and correlation strings before identity validation, while pointer segments
copied object keys without escaping. Newline and carriage-return values split a
text finding into forged-looking physical lines. Context now admits only valid
non-placeholder identities; pointer segments escape JSON controls, `/` and `~`;
one regression guard covers both routes.

Finding count: 1. The finding is fixed and guarded on the stacked audit branch.
A clean third round is required before the audit can close.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static and streaming byte limits, overlong-line draining, event, depth, string and collection limits were re-read. Both post-identity growth guards still return `RO002`. | clean on the round-2 tree |
| `unsafe-path` | Input remains one confined regular non-symlink. Recorded repository paths are validated but never followed. Filenames and pointer segments are now independently escaped for display. | clean on the round-2 tree |
| `unsafe-deserialisation` | JSON still uses duplicate-key and non-finite hooks plus closed typed shapes. A 3,377-case recursive field-type mutation pass produced no crash; only valid zero counts and durations, plus the permitted empty references on a refused outcome, remained accepted. | clean on the round-2 tree |
| `schema-drift` | Schema identity, event union, field sets, evidence classes and status enums remain bound to runtime constants. The refreshed runtime and test digests match the coverage record. | clean on the round-2 tree |
| `event-order` | Sequence, first and final events, capability pairing, backward links, retry targets and trailing-event refusals remain guarded. | clean on the round-2 tree |
| `correlation-gap` | Run, event and correlation identities remain required and bounded. Invalid identities are now omitted from diagnostic context rather than treated as safe labels. | fixed in this round; round 3 required |
| `evidence-binding` | Every consumed evidence id still resolves to an earlier definition with exact subject, scope, time domain and class; duplicate and absent ids refuse. | clean on the round-2 tree |
| `evidence-promotion` | Handoff bindings and run outcomes remain exact against their referenced evidence. No evidence-class ranking or strengthening path was found. | clean on the round-2 tree |
| `hidden-reasoning` | Recursive normalised field-name checks continue to refuse the supported hidden-reasoning aliases. Hostile pointer text is now escaped before reporting. | clean on the round-2 tree |
| `sensitive-payload` | The supported prompt, completion, output, environment, argument and credential aliases refuse. Diagnostics emit fixed messages, safe pointers and valid bounded identities rather than rejected values. | fixed in this round; round 3 required |
| `optional-host-facts` | Host and model facts still require non-placeholder source and identity fields; omission plus an explicit unknown remains valid. | clean on the round-2 tree |
| `token-accounting` | Counts still require source, scope, accounting identity and a non-negative integer; Boolean counts refuse. No price or quality claim was introduced. | clean on the round-2 tree |
| `deterministic-report` | Text and JSON still share one sorted `Finding` model. The new hostile context specimen previously split output, and now preserves one physical line per finding with JSON Pointer escaping. | fixed in this round; round 3 required |
| `partial-record` | Missing newline, malformed or overlong final input, absent finish, unresolved starts and post-finish events still refuse without mutation. | clean on the round-2 tree |
| `command-drift` | The four valid CLIs exit `0`. The five required invalid fixtures exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`. The current Horos command exits `0`; its obsolete spelling exits `2`. | clean on the round-2 tree |

### Evidence

The focused suite passes 22/22 and the root suite passes 141/141. All four
valid fixture commands exit `0`; the five required invalid fixtures exit `1`
with their expected codes. Promise Machine sync writes zero files, its check
reports 14 identical copies, and coverage reports 68/68. Phylax, Ephoros,
Hypomnema, Imprimatur, Brevitas, Horos and `git diff --check` exit `0`. The
obsolete `horos.py scan . --check` spelling exits `2`.

The runtime and focused-test SHA-256 values are
`4dc9b5f05e8d4b0ae011c3ff5b5d4e5ddd6bb82e6efd2c0c40c054b3c3d872fe`
and
`e63a457b998b46192ea93587c0b08f617969621b5c4d96afdfecf43a15b6ce2f`;
both match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction, persistence and Fiat receipt binding remain in issues
#435 and #436. Cross-run diagnosis remains in issue #449. The schema remains a
published contract rather than an executed dependency: adding a JSON Schema
engine would breach the accepted standard-library boundary, so exact field,
enum, fixture and behavioural tests continue to guard runtime agreement. The
review did not treat structural conformance as completeness, external truth,
cause, model quality, delivery correctness or a security conclusion.

## Issue 434 observable run record, step 2, round 3 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python, fixture and Markdown
step. X-Ray, Solidity Auditor and Fizz did not run. The full fixed tree was
read without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and
`0` after the fixes below.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | high | `scripts/run_observation.py` | A same-size rewrite during streaming could replace an invalid event while it was read and restore the invalid named bytes before exit. The validator returned clean because it compared inode and device only. | fixed in this round; post-read size, modification-time and change-time identity now refuses with `RO001` |
| S2-R3-02 | high | `scripts/run_observation.py` | A successful outcome could use the placeholder `unknown` as its subject and throughout its evidence definition and reference. The record therefore treated unavailable facts as a positive subject and binding. | fixed in this round; required names, observable values, selectors, sources, references and outcomes reject placeholders |
| S2-R3-03 | high | `scripts/run_observation.py` | Acronym and compact spellings such as `APIKey`, `apikey`, `rawArgs` and `chainofthought` bypassed the sensitive and hidden-name checks. | fixed in this round; acronym-aware normalisation and compact comparison preserve `RO013` and `RO014` |
| S2-R3-04 | medium | `scripts/run_observation.py` | The schema's integer type includes integral JSON numbers such as `1.0`, while the runtime rejected that spelling for sequence, duration, retry and token fields. | fixed in this round; one finite non-Boolean integer predicate now covers every schema integer field |
| S2-R3-05 | medium | `schemas/promise-machine-run-observation-v1.schema.json`, `scripts/run_observation.py` | Repository paths admitted Windows drive-qualified names and control characters; the newline case also disagreed with the published schema pattern. | fixed in this round; schema and runtime now reject drive-qualified, control-bearing and placeholder paths |

Finding count: 5. All five are fixed and guarded on the stacked audit branch.
A clean fourth round is required before the audit can close.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static and running byte limits, the overlong-line drain, event count, depth, strings and collections were exercised again. Both growth probes still return `RO002`; a same-size rewrite now returns `RO001`. | fixed in this round; round 4 required |
| `unsafe-path` | Input remains confined by resolution, final-component no-follow, regular-file and inode checks. Recorded paths now reject POSIX absolute, drive-qualified, traversal, backslash, control and placeholder values and are never followed. | fixed in this round; round 4 required |
| `unsafe-deserialisation` | Duplicate-key and non-finite hooks, closed shapes and typed relations remain active. A 3,706-case recursive mutation pass across all four valid flows produced zero crashes and accepted only valid short names or zero-valued quantities. | clean on the fixed tree |
| `schema-drift` | Schema identity, field sets, event and status enums, evidence classes and coverage digests agree. Integral JSON numbers now follow schema semantics, finite overflow refuses and repository path patterns agree on the new hostile cases. | fixed in this round; round 4 required |
| `event-order` | Contiguous sequence, start and finish cardinality, capability pairing, retry targets and events after finish remain guarded. | clean on the fixed tree |
| `correlation-gap` | Parent, capability, retry, refusal, handoff and finish links resolve backward within one run. Invalid identities remain absent from diagnostic context. | clean on the fixed tree |
| `evidence-binding` | Evidence definitions and references now require non-placeholder ids, subject, scope, time domain, class, source and selector or digest before exact relation checks. | fixed in this round; round 4 required |
| `evidence-promotion` | Successful and handoff outcomes still match every bound evidence subject. The all-placeholder success specimen now refuses rather than turning unknowns into authority. | fixed in this round; round 4 required |
| `hidden-reasoning` | Exact, separated, camel-case, acronym and compact aliases refuse recursively. `chainofthought` now returns `RO013`. | fixed in this round; round 4 required |
| `sensitive-payload` | The existing raw-value families remain forbidden, and `APIKey`, `apikey` and `rawArgs` now return `RO014`. Diagnostics still emit fixed messages and safe context only. | fixed in this round; round 4 required |
| `optional-host-facts` | Host, model, unknown and token fields require a named non-placeholder source, identity, field or reason where present; omission remains available. | fixed in this round; round 4 required |
| `token-accounting` | Counts remain source-bound, non-negative and non-Boolean. Integral JSON numbers agree with the schema, while non-integral and non-finite values refuse. | fixed in this round; round 4 required |
| `deterministic-report` | One sorted finding model still feeds text and canonical JSON. Hostile filenames, identities and JSON-pointer segments remain on one physical line with controls and pointer delimiters escaped. | clean on the fixed tree |
| `partial-record` | Final newline, malformed tail, lifecycle completion and post-finish guards remain. Metadata identity now detects same-size mutation during the read. | fixed in this round; round 4 required |
| `command-drift` | Four valid fixtures exit `0`; five required invalid fixtures exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`. The current Horos command exits `0`, and the obsolete spelling exits `2`. | clean on the fixed tree |

### Evidence

Before repair, five minimal probes on commit
`8aba6942167288b6ef7e8eb0689c3f4205d685b2` returned clean for the restored
invalid bytes, the all-placeholder successful binding, all four compact alias
spellings and all three unsafe path specimens; the integral-number specimen
returned `RO009`. The committed guards cover those same mechanisms. The first
fixed-tree run also preserved two older growth regressions: removing a
pre-open metadata comparison restored their required `RO002` result while the
post-read comparison retained the new `RO001` guard.

The focused suite passes 27/27 and the root suite passes 146/146. The recursive
type mutation probe covered 3,706 replacements across success, refusal, retry
and handoff with zero crashes. All four valid fixture commands exit `0`; the
five required invalid fixtures exit `1` with their expected codes. Promise
Machine sync writes zero files, its check reports 14 identical copies and
coverage reports 68/68. Phylax, Ephoros, Hypomnema, Imprimatur, Brevitas,
Horos and `git diff --check` exit `0`. The obsolete
`horos.py scan . --check` spelling exits `2`.

The runtime, schema and focused-test SHA-256 values are
`d62311e0724ac0d1491513d0e13e84a1bb17a76cf8d80caab431cb61ffde33c6`,
`2fce7a9b4b48db88bcfe5d4d564cd5b9ed307cb21d250ad8463bfaaea8a7a4fe`
and
`5639caa06670c544e1b8f07cae1330ced2457eddb7ef9b6d4d19d7c6b5c46928`;
all three match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction, persistence and Fiat receipt binding remain in issues
#435 and #436. Cross-run diagnosis remains in issue #449. The metadata-change
check detects ordinary concurrent rewrites but is not a mandatory lock against
a cooperating writer; the result remains bounded to the bytes the checker
observed. The review did not treat structural conformance as completeness,
external truth, cause, model quality, delivery correctness or a security
conclusion.

## Issue 434 observable run record, step 2, round 4 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python, fixture and Markdown
step. X-Ray, Solidity Auditor and Fizz did not run. The complete fixed tree was
read without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and
`0` after the fixes below.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R4-01 | high | `scripts/run_observation.py` | A path that was a regular file at `lstat` could be replaced by a FIFO before `open`. The blocking read-only open then waited indefinitely before the descriptor type check, so hostile input escaped the validator's bounded-work promise. | fixed in this round; the open is non-blocking where FIFOs exist, and the post-open regular-file and identity checks still refuse the replacement with `RO001` |
| S2-R4-02 | medium | `scripts/run_observation.py` | Binary float rounding turned a mathematically non-integral JSON token count such as `9007199254740993.1` into an integral float, so the runtime accepted a number the schema's integer type refuses. | fixed in this round; JSON decimals retain their exact lexical value and one finite non-Boolean integer predicate handles all schema integer fields |
| S2-R4-03 | medium | `scripts/run_observation.py` | An unknown top-level object key was interpolated raw into the `RO007` message. A key containing a newline forged another physical finding line, and a long key expanded the otherwise bounded diagnostic. | fixed in this round; the message reports only the bounded unknown-field count and never copies the rejected key |
| S2-R4-04 | medium | `schemas/promise-machine-run-observation-v1.schema.json`, `scripts/run_observation.py` | Metadata object keys were omitted from the advertised 4,096-character string ceiling in both schema and runtime. A 4,097-character key therefore validated, and could also enlarge a finding path. | fixed in this round; schema `propertyNames` and the recursive runtime walk share the same key ceiling and emit a value-free `RO006` finding |
| S2-R4-05 | high | `scripts/run_observation.py` | Obvious suffixed and compact sensitive or hidden-reasoning names such as `promptText`, `accessTokenValue`, `apikeyValue`, `reasoningContent` and `chainofthoughttext` bypassed exact-name matching. | fixed in this round; normalised token families and compact compound markers retain bounded metadata such as `argument_count` and `output_format` while refusing the hidden or raw families |

Finding count: 5. All five are fixed and guarded on the stacked audit branch.
Another clean audit round is required before closure.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static and running byte limits, overlong-line draining, event, nesting, value-string and collection limits remain. A pre-open FIFO replacement was observed blocking past one second; non-blocking open now reaches the regular-file refusal, and object keys share the value-string ceiling. | fixed in this round; another round required |
| `unsafe-path` | The input remains repository-confined, final-component no-follow, regular and identity-checked. Recorded paths refuse POSIX absolute, drive-qualified, traversal, backslash, control and placeholder values and are never followed. | clean on the fixed tree |
| `unsafe-deserialisation` | JSON keeps duplicate-key and non-finite hooks, closed shapes and typed relations. Exact decimal parsing removes binary rounding from integer decisions. A fresh 5,387-case recursive type replacement pass across all four valid flows produced zero crashes. | fixed in this round; another round required |
| `schema-drift` | Schema id, event union, common and event fields, evidence classes and status enums agree. Metadata key length and every integer spelling now have the same schema/runtime disposition; runtime, schema and test digests are refreshed. | fixed in this round; another round required |
| `event-order` | Contiguous sequence, one opening and closing event, capability pairing, retry targets and post-finish refusal remain guarded. Fifteen targeted lifecycle and reference mutations all returned their required code. | clean on the fixed tree |
| `correlation-gap` | Run, event and correlation identities remain bounded; parent, capability, retry, refusal, handoff and finish links resolve backward in the same run. Invalid identities stay out of diagnostic context. | clean on the fixed tree |
| `evidence-binding` | Evidence definitions require non-placeholder id, subject, scope, time domain, class, source and one selector or digest. Every consumer resolves to an earlier exact definition; forward and absent ids refuse. | clean on the fixed tree |
| `evidence-promotion` | Handoff and outcome references preserve exact subject, scope, time domain and class. Empty authorising references, each changed binding field and a successful outcome subject change all refuse. | clean on the fixed tree |
| `hidden-reasoning` | Exact, separated, camel-case, acronym, compact and suffixed rationale, reasoning and thought families refuse recursively. The new compact and suffixed specimens return `RO013`. | fixed in this round; another round required |
| `sensitive-payload` | Prompt, completion, payload, environment, transcript, credential and compound key/token or output families refuse across separated, compact and suffixed spellings. Unknown field names no longer reach messages. | fixed in this round; another round required |
| `optional-host-facts` | Host and model facts still require non-placeholder source and identity. Omission and explicit unknowns remain valid without supplying a positive fact. | clean on the fixed tree |
| `token-accounting` | Counts remain source-bound, non-negative and non-Boolean. Exact decimal parsing rejects non-integral values that binary float previously rounded into integers; no cost, price or quality inference exists. | fixed in this round; another round required |
| `deterministic-report` | Text and canonical JSON still share one sorted finding model. Hostile filenames, identities, pointer segments and now unknown field names cannot add a physical line or unbounded message. | fixed in this round; another round required |
| `partial-record` | Missing newline, malformed or overlong tails, absent finish, unresolved starts, trailing events, growth and same-size change remain refusing cases. FIFO replacement now refuses before any blocking read. | fixed in this round; another round required |
| `command-drift` | Four valid fixture CLIs exit `0`; five required invalid CLIs exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`. Current Horos exits `0`; the obsolete spelling exits `2`. | clean on the fixed tree |

### Evidence

Before repair on commit `d72605257ed2050496402e9d30f816d72175025e`,
five minimal mechanisms were reproduced. The FIFO race exceeded a one-second
subprocess bound. The non-integral token literal, 4,097-character metadata key,
and compact or suffixed forbidden names returned clean. One logical unknown-key
finding printed as two physical lines. The fixed-tree regression guards cover
the same mechanisms.

The focused suite passes 32/32 and the root suite passes 151/151. A new 5,387
case recursive type sweep produced zero crashes, and 15 explicit backward
reference, lifecycle, evidence-binding and evidence-promotion probes all
refused as required. All four valid fixture commands exit `0`; the five
required invalid fixtures exit `1` with their expected codes. Promise Machine
sync writes zero files, its check reports 14 identical copies, and coverage
reports 68/68. Phylax, Ephoros and Hypomnema exit `0`. Imprimatur and Brevitas
exit `0` on the changed operator prose and this round's entry. Horos and
`git diff --check` exit `0`. The obsolete `horos.py scan . --check` spelling
exits `2`.

The runtime, schema and focused-test SHA-256 values are
`829564c4cd6f192405e50abbd50dc5866e6feeed5d3789648964be67dc3350f5`,
`c817b2691d51531ed8798c1f351750de0d3b811b87bdf9ede2384b8e40f2b8fd`
and
`978d458505fc6740fdda50c2baba4c9e01b8b8b3f4d93565d804828653aa1197`;
all three match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in issue #435. Fiat receipt binding
remains in issue #436, and cross-run diagnosis remains in issue #449. The
schema remains a published contract rather than an executed dependency;
adding a JSON Schema engine would breach the accepted standard-library
boundary. Field-name checks can refuse declared raw or hidden-reasoning
families but cannot establish the semantics of an innocently named string.
The metadata-change check detects ordinary concurrent rewrites but does not
lock out a cooperating writer; its result stays bound to the bytes observed.

This round makes no claim of capture completeness, external truth, cause,
model quality, Fiat delivery correctness, deployment readiness, security or
mutation authority. No further lead lies outside those recorded boundaries.

## Issue 434 observable run record, step 2, round 5 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python, fixture and Markdown
step. X-Ray, Solidity Auditor and Fizz did not run. The complete fixed tree was
read without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and
`0` after the fixes below.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R5-01 | high | `scripts/run_observation.py`, `schemas/promise-machine-run-observation-v1.schema.json` | Exact-decimal parsing had an undeclared binary-float magnitude ceiling: finite `1e309` values passed the schema but refused at runtime, and an exponent outside `Decimal`'s context raised `InvalidOperation` out of the validator. | fixed in this round; schema and runtime share the finite magnitude ceiling, integers and decimals use one guarded parser, and oversized exponents refuse without a traceback |
| S2-R5-02 | medium | `scripts/run_observation.py`, `schemas/promise-machine-run-observation-v1.schema.json` | An `inferred` evidence definition could use an arbitrary selector or digest instead of naming a prior event, despite the accepted study requiring a deterministic rule and prior event id. | fixed in this round; `source` names the rule, `selector` must be a strictly earlier event id, and the schema requires selector rather than digest for inferred evidence |
| S2-R5-03 | high | `scripts/run_observation.py` | A handoff could name one earlier source event while carrying evidence defined by an unrelated event. Both references were backward, but the producing source did not carry the evidence being handed off. | fixed in this round; every handoff evidence id must be defined or consumed by its named source event |
| S2-R5-04 | medium | `scripts/run_observation.py` | A run could finish as `handoff` or `refused` without an earlier `handoff.recorded` or `transition.refused` event. The final status therefore claimed an observable lifecycle transition absent from the record. | fixed in this round; both final statuses require their matching earlier event |
| S2-R5-05 | medium | `scripts/run_observation.py` | One event could supply host or token facts and mark the same fact unknown, or repeat the same normalised unknown field. The record accepted contradictory absence evidence. | fixed in this round; duplicate and same-event contradictory unknowns return `RO007` |
| S2-R5-06 | high | `scripts/run_observation.py` | Common credential and raw-value aliases including `authHeader`, `refreshToken`, `idToken`, `argumentsText` and `toolResult` passed the normalised field-name refusal. | fixed in this round; separated, camel-case and compact forms now retain `RO014`, while bounded names such as `argument_count` and `output_format` remain accepted |

Finding count: 6. All six are fixed and guarded on the stacked audit branch.
A clean sixth round is required before the audit can close.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static and streaming bytes, lines, events, nesting, strings, object keys and collections remain bounded. Exact decimals now carry an explicit schema/runtime magnitude ceiling, and unsupported exponents fail closed. | fixed in this round; round 6 required |
| `unsafe-path` | Input remains confined, final-component no-follow, non-blocking, regular and identity-checked. Repository paths still refuse absolute, drive-qualified, traversal, backslash, control and placeholder values and are never followed. | clean on the fixed tree |
| `unsafe-deserialisation` | JSON keeps duplicate-key and non-finite hooks, closed shapes and typed relations. Both integer and fractional tokens now enter through the same guarded exact-decimal parser. A fresh 3,792-case recursive replacement sweep produced zero validator crashes. | fixed in this round; round 6 required |
| `schema-drift` | Schema id, event union, field sets, enums, numeric ceilings and the inferred-evidence selector rule agree with runtime constants and tests. All four release digests were refreshed. | fixed in this round; round 6 required |
| `event-order` | Contiguous sequence, opening and closing cardinality, capability pairing, retry targets and trailing-event refusal remain. Final refusal and handoff statuses now require their observable events. | fixed in this round; round 6 required |
| `correlation-gap` | All event references remain backward within one run. Inferred selectors are now strictly earlier, and the 24-case reference, evidence and lifecycle probe returned every expected refusal. | fixed in this round; round 6 required |
| `evidence-binding` | Definitions and consumers retain exact id, subject, scope, time domain and class. Handoff evidence must now be present on its named source event, and inferred evidence names a prior event. | fixed in this round; round 6 required |
| `evidence-promotion` | Handoff and final outcome references still preserve exact bindings. The new source-event check prevents unrelated evidence from acquiring the handoff's producer and consumer context. | fixed in this round; round 6 required |
| `hidden-reasoning` | Existing exact, separated, camel-case, acronym, compact and suffixed hidden-reasoning families still refuse recursively. | clean on the fixed tree |
| `sensitive-payload` | Credential headers, access, refresh, identity and session tokens, argument text and tool results now join the existing prompt, completion, environment and output families. Rejected values never enter diagnostics. | fixed in this round; round 6 required |
| `optional-host-facts` | Host, model and token facts remain optional and source-bound. Same-event positive and unknown claims now conflict instead of presenting absence and presence together. | fixed in this round; round 6 required |
| `token-accounting` | Counts remain optional, source-bound, non-negative and non-Boolean. Exact non-integral decimals refuse, and the published magnitude ceiling matches runtime handling. | fixed in this round; round 6 required |
| `deterministic-report` | One sorted finding model still feeds text and canonical JSON. Oversized exponents return one bounded syntax finding, and the new relation findings use fixed messages without rejected values. | clean on the fixed tree |
| `partial-record` | Missing newline, malformed or overlong tails, absent finish, unresolved starts, trailing events, growth, same-size change and pre-open FIFO replacement remain refusing cases. | clean on the fixed tree |
| `command-drift` | Four valid fixture CLIs exit `0`; five mandated invalid CLIs exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`. Current Horos exits `0`; the obsolete spelling exits `2`. | clean on the fixed tree |

### Evidence

Each mechanism was observed against signed head
`4a7fc75bec272d00c8b223bb2147b435d506cafe` before repair. Finite `1e309`
values refused despite the open schema, and an oversized exponent raised
`InvalidOperation`. Arbitrary and self-referential inferred selectors, an
unrelated handoff source, final statuses without their event, contradictory
unknowns and all five named raw aliases returned clean. The fixed-tree tests
cover the same mechanisms.

The focused suite passes 37/37 and the root suite passes 156/156. A fresh
3,792-case recursive type replacement sweep across all four valid flows
produces zero validator crashes; 24 explicit reference, lifecycle, placeholder
and evidence-binding probes return their expected codes. All four valid
fixture commands exit `0`; the five mandated invalid fixtures exit `1` with
their expected codes. Promise Machine sync writes zero files, its check
reports 14 identical copies, and coverage reports 68/68. Phylax, Ephoros and
Hypomnema exit `0`. Imprimatur and Brevitas exit `0` on the changed operator
prose and this entry. Horos and `git diff --check` exit `0`. The obsolete
`horos.py scan . --check` spelling exits `2`.

The runtime, schema, operator-document and focused-test SHA-256 values are
`30414362067171eaae71822a7e19223cf0b070efa3f878c66237097bd4da2183`,
`22f9b5a3517a27dc0d61e43c64b4856265bd3a9ecfce8254267f3cc20e0e7cc4`,
`84bb8a04a13d2108d1483e2439758aef627970a1a56b1c700736b884a777eaf5`
and `90dc390e8be553b6b89d3e3f30f0334e497466e0a850cad967609fc7dfc54986`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in issue #435. Fiat receipt binding
remains in issue #436, and cross-run diagnosis remains in issue #449. The
schema remains a published contract rather than an executed dependency;
adding a JSON Schema engine would breach the accepted standard-library
boundary. The input change check does not lock out a cooperating writer, and
field-name checks cannot establish the meaning of an innocently named value.

The v1 contract allows one run to record evidence for narrower subjects, so it
does not require every evidence subject to equal the opening subject. It also
records scheduled retries rather than cancellation or attempt-chain state;
widening either relation would change the public contract. This round makes no
claim of capture completeness, external truth, cause, model quality, Fiat
delivery correctness, deployment readiness, security or mutation authority.
No other in-scope lead remains after these fixes; round 6 must independently
reassess them before closure.

## Issue 434 observable run record, step 2, round 6 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python, fixture and Markdown
step. X-Ray, Solidity Auditor and Fizz did not run. The complete fixed tree was
read without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and
`0` after the fixes below.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R6-01 | medium | `schemas/promise-machine-run-observation-v1.schema.json`, `scripts/run_observation.py` | The schema admitted placeholder identities and blank observed strings that runtime refused. Its time, unknown-field and repository-path shapes also lacked the runtime's exact patterns. | fixed in this round; shared constants and tests now bind the schema patterns to runtime acceptance |
| S2-R6-02 | medium | `scripts/run_observation.py` | An event could supply a host or token fact while an alias such as `host_id`, `hostName`, `input_token_count` or `accounting_id` claimed that family was unknown. An unknown name with no normalised characters also passed. | fixed in this round; normalised fact families conflict with supplied facts, and empty normalised names refuse |
| S2-R6-03 | high | `scripts/run_observation.py` | A final handoff outcome could cite bound evidence that no earlier handoff event carried. The outcome therefore promoted evidence into a terminal handoff without an observable transfer. | fixed in this round; final handoff evidence must be included in the evidence carried by prior handoff events |
| S2-R6-04 | high | `scripts/run_observation.py` | Raw metadata aliases including `messages`, `chatMessages`, `systemMessage`, `inputText`, `requestBody`, `responseBody`, `functionArguments`, `envVars`, `headers` and `apiToken` passed the normalised-name guard. | fixed in this round; expanded raw families refuse these names while bounded descriptors and digests remain valid |
| S2-R6-05 | medium | `schemas/promise-machine-run-observation-v1.schema.json`, `scripts/run_observation.py` | Repository paths admitted URI-looking values, Windows reserved names, empty or dot segments, trailing dot or space and components longer than 255 characters. | fixed in this round; schema and runtime share one portable relative-path language with a 255-character component ceiling |
| S2-R6-06 | medium | `scripts/run_observation.py` | A caller-supplied input path produced an unbounded diagnostic path. On Windows, a different-drive relative-path calculation raises before a finding is emitted. | fixed in this round; display paths have a 512-character content-addressed ceiling and a guarded fallback |

Finding count: 6. All six are fixed and guarded on the stacked audit branch.
Round 7 is required; closure is not earned in this round.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static and streaming bytes, lines, events, nesting, strings, keys, collections and exact numbers remain bounded. Repository components now stop at 255 characters, and a diagnostic path stops at 512 characters with a SHA-256 suffix. | fixed in this round; round 7 required |
| `unsafe-path` | Input remains repository-confined, final-component no-follow, non-blocking, regular and identity-checked. Recorded paths now share a schema/runtime portable language that excludes absolute, URI, traversal, reserved-name and nonportable segment forms. | fixed in this round; round 7 required |
| `unsafe-deserialisation` | JSON retains duplicate-key and non-finite hooks, exact decimal parsing, closed shapes and typed relations. A 674-case wrong-kind sweep across all four valid flows produced zero crashes and zero accepted mutations. | clean on the fixed tree |
| `schema-drift` | Identity, observed-string, time, unknown-field and repository-path patterns now match runtime constants exactly. Field sets, enums and release digests also agree. | fixed in this round; round 7 required |
| `event-order` | Contiguous sequence, opening and closing cardinality, capability pairing, retry targets and trailing-event refusal remain. Final handoff evidence now agrees with prior handoff events. | fixed in this round; round 7 required |
| `correlation-gap` | Run, parent, capability, retry, refusal, handoff, inferred-source and outcome links remain backward within one run. Eighteen state-sequence and relation probes returned their expected refusals. | clean on the fixed tree |
| `evidence-binding` | Definitions and uses retain exact id, subject, scope, time domain, class, source and selector or digest relations. Final handoff evidence must now have crossed a prior handoff boundary. | fixed in this round; round 7 required |
| `evidence-promotion` | Handoff and outcome references preserve their exact bindings, and an outcome can no longer add evidence absent from every prior handoff. | fixed in this round; round 7 required |
| `hidden-reasoning` | Exact, separated, camel-case, acronym, compact and suffixed hidden-reasoning families still refuse recursively. | clean on the fixed tree |
| `sensitive-payload` | Message, prompt, input, request, response, argument, environment, header and token value families now join the existing refusals. Safe counts, names, formats and digests remain available. | fixed in this round; round 7 required |
| `optional-host-facts` | Host, model and token facts remain optional and source-bound. Normalised aliases now prevent the same event from claiming a supplied fact is unknown. | fixed in this round; round 7 required |
| `token-accounting` | Counts remain optional, source-bound, exact, finite, non-negative and non-Boolean. Token and accounting aliases now conflict with a supplied token fact instead of recording contradictory absence. | fixed in this round; round 7 required |
| `deterministic-report` | One sorted finding model still feeds text and canonical JSON without rejected values. Hostile caller paths are now bounded and content-addressed, including the different-drive fallback. | fixed in this round; round 7 required |
| `partial-record` | Missing newline, malformed or overlong tails, absent finish, unresolved starts, trailing events, growth, same-size change and FIFO replacement remain refusing cases. | clean on the fixed tree |
| `command-drift` | Four valid fixture CLIs exit `0`; five mandated invalid CLIs exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`. Current Horos exits `0`; the obsolete spelling exits `2`. | clean on the fixed tree |

### Evidence

Each mechanism was reproduced on signed head
`9720783753a6a7c6ee6b1d4656d41c11ec303d26` before repair. Placeholder and
blank schema specimens, contradictory unknown aliases, unhanded terminal
evidence, raw aliases and nonportable paths returned clean. A hostile caller
path produced 2,056 display characters, and the schema lacked the observed
string pattern. Test-only guards then failed in 26 subcases and raised two
missing-constant errors before the implementation changed.

The focused suite passes 40/40 and the root suite passes 159/159. The 674-case
wrong-kind sweep across all four valid flows produces zero crashes and zero
accepted mutations. Eighteen relation and state-sequence probes, plus a
23-case portable-path matrix, produce no unexpected result. All four valid
fixture commands exit `0`; the five mandated invalid fixtures exit `1` with
their expected codes. Promise Machine sync writes zero files, its check
reports 14 identical copies, and coverage reports 68/68. Phylax, Ephoros and
Hypomnema exit `0`. Imprimatur and Brevitas exit `0` on the changed prose and
this entry. Horos and `git diff --check` exit `0`. The obsolete
`horos.py scan . --check` spelling exits `2`.

The runtime, schema, operator-document and focused-test SHA-256 values are
`300b4aa7b4565800ef14b81aa71546db7e4978d52f154187f155b2daa2187349`,
`3bd3a2977e31284b1983337f9717ece1ea1f34108f9106bf40cf949b332b2806`,
`17fde53ca475430dd8647b3a6808e0f35d098274fed4e0e92967f14f21ef69a1`
and `27312718ed127a38e4dc5ef5950d8c173b6634e5e735bfe9be18fba0d26afb22`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in issue #435. Fiat receipt binding
remains in issue #436, and cross-run diagnosis remains in issue #449. The
schema remains a published contract rather than an executed dependency;
adding a JSON Schema engine would breach the accepted standard-library
boundary. The input change check does not lock out a cooperating writer, and
field-name checks cannot establish the meaning of an innocently named value.

The v1 contract allows evidence for subjects narrower than the opening
subject. It records scheduled retries, not cancellation or attempt-chain
state, and does not require a failed capability for every failed run. Sequence
is authoritative, so this round does not infer invalidity from wall-clock
rollback alone. It makes no claim of capture completeness, external truth,
cause, model quality, Fiat delivery correctness, deployment readiness,
security or mutation authority. The six fixes require round 7 review.

## Issue 434 observable run record, step 2, round 7 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python, fixture and Markdown
step. X-Ray, Solidity Auditor and Fizz did not run. The complete fixed tree was
read without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and
`0` after the fixes below.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R7-01 | high | `scripts/run_observation.py` | A valid regular file could be opened and its named path replaced with invalid bytes while the open descriptor remained unchanged. The validator returned clean for bytes no longer present at the path named by its result. | fixed in this round; the post-read check now requires the named path to remain the same regular non-symlink inode |
| S2-R7-02 | medium | `scripts/run_observation.py` | A caller path containing an embedded null or an unencodable surrogate raised from `lstat` instead of returning the bounded `RO001` refusal. | fixed in this round; path representation failures now use the same safe input finding |
| S2-R7-03 | high | `scripts/run_observation.py` | A terminal handoff whose `outcome.evidence_refs` was null, Boolean or numeric reached an unconditional iteration after the shape finding and raised `TypeError`. | fixed in this round; the handoff relation consumes only a list and leaves other kinds to the existing `RO007` refusal |
| S2-R7-04 | high | `schemas/promise-machine-run-observation-v1.schema.json`, `scripts/run_observation.py`, `docs/promise-machine/run-observation-v1.md` | The v1 surface did not define issue or topic, step, role or selected skill and promise context, and it carried only one repository commit. Generic metadata could not bind those issue #434 fields, a refusal to its selected promise, a handoff to its selected producer, or an after-commit to its opening identity. | fixed in this round; one closed opening context is required and relationally bound, while closed opening and closing repository objects name and preserve explicit before and after Git identities |

Finding count: 4. All four are fixed and guarded on the stacked audit branch.
Round 8 is required; closure is not earned in this round.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static and streaming byte, line, event, nesting, string, key, collection and exact-number ceilings remain. Null and unencodable caller paths now refuse without escaping the finding model. | fixed in this round; round 8 required |
| `unsafe-path` | The open descriptor and the caller-named path must now retain one regular non-symlink inode through the complete read. Repository paths retain the portable closed language from round 6. | fixed in this round; round 8 required |
| `unsafe-deserialisation` | Duplicate keys, non-finite numbers, exact decimals, closed shapes and typed relations remain fail-closed. A 2,064-case recursive wrong-kind sweep across the four valid flows now produces zero validator crashes. | fixed in this round; round 8 required |
| `schema-drift` | Runtime and schema now agree on the required closed run context, explicit opening and closing repository shapes, event field sets, patterns, enums and release digests. | fixed in this round; round 8 required |
| `event-order` | Contiguous sequence, one opening and closing event, capability pairing, retry targets and terminal lifecycle requirements remain. Twenty-five adjacent, reversed and rotated lifecycle sequences produced no unexpected clean result. | clean on the fixed tree |
| `correlation-gap` | Run, parent, capability, retry, refusal, handoff, inferred-source and outcome links remain backward within one run. The selected promise and handoff producer now also resolve to the opening context. | fixed in this round; round 8 required |
| `evidence-binding` | Definitions and consumers retain exact id, subject, scope, time domain, class, source and selector or digest relations. Handoff evidence remains bound to its source event and its producer now remains bound to the selected skill. | fixed in this round; round 8 required |
| `evidence-promotion` | Handoff and outcome references preserve their earlier evidence bindings, and the selected producer and promise cannot be renamed at the transition. | clean on the fixed tree |
| `hidden-reasoning` | Exact, separated, camel-case, acronym, compact and suffixed hidden-reasoning families still refuse recursively. | clean on the fixed tree |
| `sensitive-payload` | Raw message, prompt, input, request, response, argument, environment, header, token and credential families remain refusing. No rejected value enters diagnostics. | clean on the fixed tree |
| `optional-host-facts` | Host and model facts remain optional, source-bound and mutually exclusive with same-event unknown claims. The required work context is distinct from optional host identity. | clean on the fixed tree |
| `token-accounting` | Counts remain optional, source-bound, exact, finite, non-negative and non-Boolean, with explicit unknowns when absent. | clean on the fixed tree |
| `deterministic-report` | One sorted finding model still feeds canonical JSON and text. Named-path replacement, unrepresentable paths and malformed handoff evidence now return bounded stable findings without rejected values. | fixed in this round; round 8 required |
| `partial-record` | Missing newline, malformed or overlong tails, absent finish, unresolved starts, trailing events, growth, same-inode rewrites, FIFO replacement and named-path replacement all refuse without mutation. | fixed in this round; round 8 required |
| `command-drift` | Four valid fixture CLIs exit `0`; five mandated invalid CLIs exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`. Current Horos exits `0`; the obsolete spelling exits `2`. | clean on the fixed tree |

### Evidence

All four mechanisms were reproduced against signed head
`19a113bd87f1febed9dee87d18aa8cb9c37db319` before repair. A path swap left
invalid bytes at the named location while validation returned no findings.
Null and unencodable caller paths raised instead of returning `RO001`.
Null, Boolean and numeric terminal handoff references raised `TypeError`.
Every valid fixture omitted the issue-required work context, and the success
fixture exposed only one unqualified repository commit.

The Step 1 study describes repository identities and says a record does not
select a skill; it does not forbid recording the selection already made. Its
ask-first line covers public-field changes. The controlling runbook also says
this step implements issue #434 and must demonstrate every issue acceptance
case. Because v1 is still unpublished, the minimal closed context and explicit
Git transition repair that omission without widening the schema into capture,
selection or Fiat receipt binding.

The focused suite passes 44/44 and the root suite passes 163/163. The 2,064-case
recursive wrong-kind sweep produces zero crashes. Twenty-five systematic
lifecycle reorderings and the focused context, repository, evidence, handoff,
retry and path matrices produce no unexpected result. All four valid fixture
commands exit `0`; the five mandated invalid fixtures exit `1` with their
expected codes. Promise Machine sync writes zero files, its check reports 14
identical copies, and coverage reports 68/68. Phylax, Ephoros and Hypomnema
exit `0`. Imprimatur and Brevitas exit `0` on changed prose and this entry.
Horos and `git diff --check` exit `0`. The obsolete
`horos.py scan . --check` spelling exits `2`.

The runtime, schema, operator-document and focused-test SHA-256 values are
`5cf48b08108508ac801800ea906a11c40f30b9151632980ff811d91476e2fbb6`,
`98da42d4ac23210a28dcc06752dd3fc58c095561f77c927f31596831697390b0`,
`e542d249e685a6ef809cab113f00e0aa40052addb97f4ab1464177cbde18280d`
and `28c6decc07bb5d6068fd5f9d5d3bbd92d93e32ce5005afc9786fcf8d01207716`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in issue #435. Fiat receipt binding
remains in issue #436, and cross-run diagnosis remains in issue #449. The
schema remains a published contract rather than an executed dependency;
adding a JSON Schema engine would breach the accepted standard-library
boundary. The descriptor and path checks detect ordinary concurrent changes
but do not lock out a cooperating writer. Field-name checks cannot establish
the meaning of an innocently named value.

The v1 contract allows evidence for subjects narrower than the opening
subject. It records scheduled retries rather than cancellation or attempt-chain
state, and does not require a failed capability for every failed run. Parent
links are optional and correlation ids may identify separate joined paths, so
neither is strengthened into a single linear trace. Sequence remains
authoritative over wall-clock order. This round makes no claim of capture
completeness, external truth, cause, model quality, Fiat delivery correctness,
deployment readiness, security or mutation authority. The four fixes require
round 8 review.

## Issue 434 observable run record, step 2, round 8 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python, fixture and Markdown
step. X-Ray, Solidity Auditor and Fizz did not run. The complete fixed tree was
read without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and
`0` after the fixes below.

### Normative map

| contract statement | schema and runtime enforcement | executable evidence |
| --- | --- | --- |
| One v1 contract and closed event union | Schema `$id` and seven `$defs`; `CONTRACT_ID`, `EVENT_TYPES`, `shape` | schema-union, all-event-type and four valid-flow tests |
| Stable run, event, correlation and work identities | `identity`, `eventBase` and `runContext`; `scalar_fields`, `check_context`, run-wide identity checks | missing-identity, placeholder and context-binding tests |
| Contiguous order, one opening and closing event, backward same-run links | Event sequence fields; `relations` and `backward_event_refs` | bad-order fixture, 38 reorderings and 50 strict-reference mutations |
| Capability exit, duration and scheduled retry | Capability and retry definitions; capability maps, finish pairing and retry target checks | success, refusal and retry fixtures plus lifecycle probes |
| Exact evidence definitions, references and inferred selectors | Evidence definitions and enums; `check_evidence_list`, `evidence_relations` and inferred-selector checks | unbound, strengthened, inferred, source-event and outcome tests |
| Refusals and handoffs preserve selected context | Refusal and handoff definitions; promise, producer, distinct-consumer, source and final-status checks | refusal, cross-skill handoff, self-handoff and terminal-status tests |
| Optional host, model, token and unknown facts | Host, token and unknown definitions; `check_host_fact`, `check_tokens`, `check_unknowns` | recorded-versus-unknown, conflict and Boolean-token tests |
| Portable repository path and paired Git transition | Repository definitions; `check_repository` and opening-to-closing relation checks | path matrix, changed binding and missing-half tests |
| Confined, bounded, immutable JSONL input | File, byte, line, event and recursive limits in `read` and `check_limits_and_names` | growth, FIFO, same-inode rewrite, final-path and parent-path replacement tests |
| Bounded raw-payload and hidden-reasoning refusal | Closed scalar metadata and recursive normalised-name checks | duplicate-key, wrong-kind, alias and combined-hostile tests |
| Stable text and canonical JSON findings | One `Finding` model, sorting, safe path rendering and CLI projection | text/JSON parity, control-framing and display-path tests |
| Structural authority only | Root Promise declaration, generated copies, coverage digest bindings and operator boundary | Promise sync, check, coverage and root contract tests |

The field-set, enum, pattern, integer-ceiling and release-digest bindings show
no schema/runtime drift on the fixed tree. A 1,825-case recursive wrong-kind
sweep across all four valid records produced no crash and no unexpected clean
result. The 38 event reorderings and 50 strict reference substitutions also
produced no crash or unexpected clean result.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R8-01 | high | `scripts/run_observation.py` | Replacing a parent directory with a symlink to an outside directory containing a hard link to the open input preserved the final file inode. The post-read final-component check passed and the validator returned clean for a named path that no longer resolved inside its confined root. | fixed in this round; post-read resolution must remain inside the root, and the exact parent replacement is guarded |
| S2-R8-02 | medium | `scripts/run_observation.py`, `docs/promise-machine/run-observation-v1.md` | A record opened with a repository path and `before_commit`. The validator accepted it when the closing repository object was omitted, so the claimed transition was half-recorded. | fixed in this round; opening and closing repository identities must appear together or both stay absent |
| S2-R8-03 | medium | `scripts/run_observation.py`, `docs/promise-machine/run-observation-v1.md` | A handoff whose producer and consumer were the same selected skill returned clean. It satisfied field shape while recording no cross-skill transfer. | fixed in this round; a handoff now requires a distinct consumer identity |

Finding count: 3. All three are fixed and guarded on the stacked audit branch.
This is the configured eighth and final round, so this run cannot earn a clean
closure. Its findings and remediations must become carryover prior art for the
next focused Fiat run.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `unbounded-input` | Static and streaming byte, line, event, nesting, string, key, collection and exact-number ceilings remain. The recursive wrong-kind sweep produced no crash. | clean on the round-8 fixed tree |
| `unsafe-path` | Final-component identity still holds, and the named path must now resolve inside the confined root after the read even when an ancestor changes. Portable recorded-path checks remain. | fixed in this round; restart audit required |
| `unsafe-deserialisation` | Duplicate-key and non-finite hooks, exact decimals, closed shapes and typed relations remain fail-closed. The 1,825 wrong-kind mutations produced no crash or clean mutation. | clean on the round-8 fixed tree |
| `schema-drift` | Event fields, enums, patterns, integer ceilings and schema identity remain bound to runtime constants. Pairing and distinct-consumer rules are cross-event relations rather than divergent field shapes. | clean on the round-8 fixed tree |
| `event-order` | Thirty-eight adjacent, reversed and rotated sequences and 50 strict reference substitutions refused as expected. Repository halves now form one lifecycle relation. | fixed in this round; restart audit required |
| `correlation-gap` | Parent, capability, retry, refusal, handoff, inferred-source and finish links remain backward in one run. Distinct correlation ids may still represent joined paths as declared. | clean on the round-8 fixed tree |
| `evidence-binding` | Definitions, consumers, inferred selectors, source events, handoff carriage and terminal references retain exact id, subject, scope, time domain and class relations. | clean on the round-8 fixed tree |
| `evidence-promotion` | Handoff and outcome references preserve their earlier evidence. A self-handoff can no longer present an unchanged producer as a transfer. | fixed in this round; restart audit required |
| `hidden-reasoning` | Exact, separated, camel-case, acronym, compact and suffixed hidden-reasoning families still refuse recursively. | clean on the round-8 fixed tree |
| `sensitive-payload` | Raw message, prompt, input, request, response, argument, environment, header, token and credential families remain refusing. Rejected values do not enter findings. | clean on the round-8 fixed tree |
| `optional-host-facts` | Host and model facts remain optional, source-bound and exclusive with same-event unknown claims. | clean on the round-8 fixed tree |
| `token-accounting` | Counts remain optional, source-bound, exact, finite, non-negative and non-Boolean, with explicit unknowns available. | clean on the round-8 fixed tree |
| `deterministic-report` | Text and JSON still derive from one sorted finding model. The three new refusals use fixed bounded messages and no rejected value. | clean on the round-8 fixed tree |
| `partial-record` | Missing newline, malformed or overlong tails, missing lifecycle halves, growth, same-inode rewrites, FIFO and final or ancestor path replacement all refuse without mutation. | fixed in this round; restart audit required |
| `command-drift` | Four valid fixture CLIs exit `0`; five mandated invalid CLIs exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and `RO013`. Current Horos exits `0`; the obsolete spelling exits `2`. | clean on the round-8 fixed tree |

### Evidence

All three mechanisms were reproduced against signed head
`0ec8073500ce1dad83aba86462ca7817592ade3f` before repair. The ancestor-swap
probe moved the named path outside its designated root while preserving the
open inode and returned no findings. Removing the closing repository object
and setting a handoff consumer equal to its producer also returned clean. The
new focused guards cover the same mechanisms.

The focused suite passes 45/45 and the root suite passes 164/164. Four valid
fixture commands exit `0`; the five mandated invalid fixtures exit `1` with
their expected codes. Promise Machine sync writes zero files, its check reports
14 identical copies, and coverage reports 68/68. Phylax, Ephoros and
Hypomnema exit `0`. Imprimatur and Brevitas exit `0` on changed prose and this
entry. Horos and `git diff --check` exit `0`. The obsolete
`horos.py scan . --check` spelling exits `2`.

The runtime, schema, operator-document and focused-test SHA-256 values are
`dff62c568e5f5421032699deed2297ce0fe662f478b14d48f990a5d05356e632`,
`98da42d4ac23210a28dcc06752dd3fc58c095561f77c927f31596831697390b0`,
`d925759b54bfe7b3b0c78a03b9525a542a765f5c179862d033fa6e8b96fe2019`
and `d2c90c55729e60f21b7702edc0b9f8ddbda08a65dab9ce6e8ba653008bff7633`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in issue #435. Fiat receipt binding
remains in issue #436, and cross-run diagnosis remains in issue #449. The
schema remains a source contract rather than an executed dependency; adding a
JSON Schema engine would breach the accepted standard-library boundary. The
input checks detect ordinary concurrent changes but do not lock out a
cooperating writer, and field-name checks cannot establish the meaning of an
innocently named value.

The v1 contract allows evidence for subjects narrower than the opening
subject. It records scheduled retries rather than cancellation or attempt-chain
state, allows correlation ids to join separate paths, and treats sequence as
authoritative over wall-clock order. Equal before and after commits remain a
valid observation of no repository change. This round makes no claim of
capture completeness, external truth, cause, model quality, Fiat delivery
correctness, deployment readiness, security or mutation authority. No other
in-scope lead remains on the fixed tree, but the configured maximum requires
carryover and a fresh audit run rather than closure.

## Issue 434 observable run record carryover inoculation 2, step 1, round 1 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived for this JSON, Python and Markdown step.
X-Ray, Solidity Auditor and Fizz did not run. The complete fixed tree was read
without Horos exclusions. The protected origin retained exactly its four
pre-existing status lines before the first write and after every write batch.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I434-C2-S1-R1-01 | medium | `schemas/promise-machine-run-observation-v1.schema.json` | The schema accepted metadata strings longer than 4,096 characters while the runtime refused them with `RO006`. | fixed and guarded; metadata scalar strings now share the runtime ceiling |
| I434-C2-S1-R1-02 | high | `scripts/run_observation.py` | Empty and punctuation-only metadata keys, plus bare raw-payload and hidden-work aliases such as `input`, `env`, `analysis` and `scratchpad`, returned clean. | fixed and guarded; arbitrary keys must name a fact and the alias sets now cover the reproduced families |
| I434-C2-S1-R1-03 | high | `scripts/run_observation.py` | A forbidden field name containing sensitive bytes was copied into the finding pointer and canonical JSON even though its value was withheld. | fixed and guarded; invalid and forbidden keys use fixed pointer segments before recursion |
| I434-C2-S1-R1-04 | high | `tests/emit_run_observation_report.py` | Replacing the named report after exclusive open and write made the reporter return success while the named path contained forged JSON. | fixed and guarded; the reporter fsyncs, reopens the root and parent without creation, then requires the named regular file to retain the created inode |

Finding count: 4. All four are fixed and guarded on the audit branch. Another
independent round is required; clean closure is not earned in this round.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | Both attachment URLs yielded the archived bytes at SHA-256 `11bbf719ce1b2f59b0344d4ad92d69e467c503d758b35a1689a98c7231156784` and `54469718c5949953dae414da664a65f940aca249868e00382f97139cda03fef0`. Both signed refs, parents, trailers, archived states, 23-entry and 8-entry ledgers, and receipted study/runbook bytes verify. | clean on the fixed tree |
| `prior-art-drift` | Signed attempt 4 remains a direct child of base `367e9662384bb29ea94576d270ab86744f3326a2`; its 37-path inventory matches the reconstructed implementation inventory. Old check output was treated as history only. | clean on the fixed tree |
| `delegated-path-resolution` | Every patch path and the generated Elenchus report path was canonical, absolute and under the run worktree. | clean on the fixed tree |
| `origin-checkout-drift` | The origin remained limited to `.horos/boundary.json`, `output/pdf/how-to-help-shoggoth.pdf`, and the two untracked help-Shoggoth PNGs. | clean on the fixed tree |
| `gate-command-arity` | Both Protasis modes, the source-owned report command, four separate Brevitas invocations, current Horos and the obsolete negative specimen accepted the exact documented argument shapes. | clean on the fixed tree |
| `current-main-loss` | Implementation head and attempt 4 are based directly on current run base. ADR-014 remains present, ADR-015 is separate, and this round changes only seven declared implementation paths plus this audit record. | clean on the fixed tree |
| `carryover-map-gap` | The machine-readable map has 36 unique ids across eight families; every guard selector resolved and ran. | clean on the fixed tree |
| `schema-runtime-drift` | Field sets, required sets, enums, patterns, exact numeric ceilings and metadata string limits now agree. | fixed in this round; another round required |
| `wrong-kind-crash` | The retained 365-case recursive matrix plus 3,650 fresh structural substitutions produced no crash or unexpected clean result. | clean on the fixed tree |
| `lifecycle-reference-gap` | Existing lifecycle, reference and context matrices pass; 1,461 fresh event-renumbering permutations produced no crash or unexpected clean result. | clean on the fixed tree |
| `input-replacement` | Five input-file and ancestor races still refuse. The added reporter target-swap guard now refuses success when the named output no longer has the created identity. | fixed in this round; another round required |
| `recorded-path-gap` | Portable repository and bounded caller-path matrices pass, including drive, reserved, dot, control, NUL, surrogate and different-root cases. | clean on the fixed tree |
| `name-normalisation-gap` | The matrix now covers 62 styled, compact, invalid and bare-alias cases. Safe descriptors and known-versus-unknown names remain available. | fixed in this round; another round required |
| `diagnostic-injection` | Text and JSON still share one finding model. Rejected values, forbidden key names and hostile framing bytes do not enter rendered diagnostics. | fixed in this round; another round required |
| `context-binding-gap` | Issue/topic, step, role, selected skill and promise, Git identities, refusals, handoffs and outcomes remain related to the opening context. | clean on the fixed tree |
| `evidence-promotion` | Evidence subject, scope, time domain, class, source event, handoff carriage and terminal use retain the prior exact relations. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, number, string, key, path and collection limits remain fail-closed; schema metadata strings now state the same ceiling. | fixed in this round; another round required |
| `sensitive-payload` | Recursive raw-payload and hidden-work families now include the reproduced bare aliases, reject non-names and redact forbidden pointer segments. | fixed in this round; another round required |
| `optional-telemetry` | Host, model, token and unknown facts remain optional, source-bound and type checked. No exporter or backend was added. | clean on the fixed tree |
| `partial-or-stale-record` | Truncation, lifecycle halves, concurrent input mutation and now named-report replacement all refuse without claiming a fresh record. | fixed in this round; another round required |
| `elenchus-report-drift` | The source-owned runner emitted a fresh complete `unittest-json-v1` report for 57 tests with zero failures, errors, skips, expected failures or unexpected successes. Root, parent and named-target identities are rechecked after write. | fixed in this round; another round required |
| `closure-overclaim` | This round found four defects. The controller remains in audit and no receipt, push, PR, comment, merge or issue mutation was made. | another round is required |

### Evidence

Each mechanism was reproduced twice against signed implementation head
`546b773f6ebd98a16b42c4f1c3a94f54465a5db0` before repair. The schema exposed
no metadata-value `maxLength`; empty, punctuation-only and bare-alias keys
returned no finding; forbidden key bytes appeared in JSON; and both report
swaps returned success with `{"schema":"forged"}` at the named path.

The focused and inoculation suites pass 57/57. The inoculation record reports
771 cases across the eight declared families, zero crashes and zero unexpected
clean results. The root suite passes 176/176. Four valid fixture commands exit
`0`; the five invalid fixture commands exit `1` with their established
`RO008`, `RO009`, `RO011`, `RO012` and `RO013` findings. The report command
exits `0` with a complete fresh report.

Promise Machine sync writes zero files, its check reports 14 identical copies,
and coverage reports 68/68. Protasis study and runbook checks, Phylax, Ephoros,
Hypomnema, Imprimatur and each of the four Brevitas commands exit `0`. Python,
schema, coverage and nine JSONL syntax checks exit `0`. Current Horos and
`git diff --check` exit `0`; the obsolete Horos spelling exits `2` as required.

The runtime, schema, operator-document and focused-test SHA-256 values are
`970566cb2e6fc0254e0c6157ac58c55c5fb5775ebe74f7f7380f4623b52fde00`,
`d3e56551d01022a90c3079a8f1be2dda341783918c83f6de6f7310f26fda564d`,
`388c6da34807fb1e50b0ccc12d3ef6e88c9bb3884521b352836176f948dc74c3`
and `c7b10561fdb82ed537afec145bffbbecfce2074eeb35d8f178ec6bd3b0b97faa`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in issue #435. Fiat receipt binding
remains in issue #436, and cross-run diagnosis remains in issue #449. Adding a
JSON Schema engine would breach the accepted standard-library boundary. File
identity checks detect ordinary concurrent replacement but cannot lock out a
cooperating same-account writer, and field-name rules cannot determine the
meaning of an innocently named scalar.

The v1 contract still permits evidence for a subject narrower than the opening
subject. It records retry scheduling rather than cancellation or a complete
attempt chain, does not require a failed capability for every failed run,
allows correlation ids to join separate paths, and treats sequence as
authoritative over wall-clock order. Expected failures and skips remain
explicit report fields and would make Elenchus inconclusive; this run had none.
This round makes no claim of capture completeness, external truth, cause,
model quality, Fiat delivery correctness, deployment readiness, security or
mutation authority. The four fixes require another independent review.

## Issue 434 observable run record carryover inoculation 3, step 1, reconstruction and inoculation -- 2026-08-23

### Disposition

The three archived carryover packets, their 23-entry, 8-entry and 10-entry
ledger chains, receipts, signed refs, parents, trailers and path inventories
were verified before reconstruction. The 37-path attempt-5 fixed tree was
reconstructed by path and meaning from signed ref
`50a9129c8481e7519d8c640c152f58401035f323` without merge, rebase or
cherry-pick. The implementation source is signed attempt-5 implementation
`546b773f6ebd98a16b42c4f1c3a94f54465a5db0`; the published study and runbook
are the current receipted bytes.

The ref above is preserved historical evidence, not the implementation result
of this run. No receipt, push, pull request, issue mutation or audit-closure
claim is made here. A later independent Warden round remains required.

### Reproduced mechanisms and repairs

Each mechanism below was reproduced twice against the reconstructed signed
attempt-5 fixed tree before repair.

| id | severity | surface | reproduced mechanism | remediation and inoculation |
| --- | --- | --- | --- | --- |
| I434-C3-S1-M-01 | high | `scripts/run_observation.py` | Hidden-work suffix and camel aliases `analysisText`, `scratchpadContent`, `deliberationNotes` and `internalMonologueBuffer` returned clean. | fixed and guarded; normalised suffix, prefix, compact, camel, token and acronym families refuse while bounded descriptor suffixes remain valid |
| I434-C3-S1-M-02 | high | schema, runtime and operator prose | Repository paths containing an unpaired surrogate, bidirectional controls or a decomposed non-NFC form returned clean; composed and decomposed spellings were not governed consistently. | fixed and guarded; repository paths require Unicode scalar values in NFC and exclude controls and bidi formatting, with non-NFC input refused rather than silently normalised |
| I434-C3-S1-M-03 | high | `scripts/run_observation.py` | An equal-length same-inode rewrite after the post-read `fstat` restored invalid named bytes while the validator returned clean. | fixed and guarded; a clean result now requires one bounded final named-path reopen and reread whose digest, length, identity, confinement and stat observations match the validated snapshot |
| I434-C3-S1-M-04 | high | `tests/emit_run_observation_report.py` | A same-inode equal-length rewrite after reporter `fsync` left forged report bytes while the reporter returned success. | confirmed, fixed and guarded; the non-recursive original `fsync` path now closes, reopens and rereads the exact named report and compares its bytes and identity without a stability loop |

### Cumulative binding

The carryover fixture binds all three packet URLs and SHA-256 digests, their
source runs and preserved refs, the attempt-5 parent implementation, the 36
original unique finding ids across eight families, four carried round-1
mechanisms, three current input repairs and the confirmed reporter lead. Every
original id maps to a remediation family and a current guard.

The inoculation suite reports 812 cases: 36 carryover-map, 4 fixed-round-1-map,
3 current-repair-map, 1 reporter-lead-map, 251 schema-runtime, 365
recursive-wrong-kind, 9 lifecycle-reference, 8 file-replacement, 23
path-representation, 87 normalised-field-name, 8 report-parity-no-echo and 17
work-repository-context cases. It reports zero crashes and zero unexpected
clean results.

### Gate evidence

The focused and inoculation suites pass 60/60; the root suite passes 179/179.
The source-owned reporter exits `0`, runs 60 tests and emits a complete
`elenchus.unittest.v1` report with zero failures, errors, skips, expected
failures or unexpected successes. All four valid CLIs exit `0`; the five
required invalid fixtures exit `1` with `RO008`, `RO009`, `RO011`, `RO012` and
`RO013` respectively.

Promise Machine sync writes zero files, its copy check reports 14 identical
copies, and coverage reports 68/68. Phylax, Ephoros, Hypomnema, both Protasis
modes, Imprimatur and each of the four separate Brevitas commands exit `0`.
Python and changed JSON syntax, all 34 fixture JSONL objects, both receipted-byte
comparisons, the 37-path scope comparison, current Horos and
`git diff --check` exit `0`. The obsolete Horos spelling exits `2` as required.

The runtime, schema, operator-document and focused-test SHA-256 values are
`17a8c54f0ab00d13f48fcde9bc1d566e5a93a6df608556f0c2fdbd7f462c3137`,
`d732a91c82554ede9adbba7e0eb6cb919635b00831efd280213ebfa253208b20`,
`b514a789e1ff2c4aded638f95439a1154814db0ba38b863c493b2b332363de78`
and `def37843169b5894e37849efe94dfd6d0bde7e7bd26ec308b8463a53879915db`;
all four match `tests/promise_machine_coverage.json`.

### Remaining boundary

The bounded final reread narrows the observation instant; it does not lock the
file or prevent a later writer. Structural conformance does not establish
capture completeness, external truth, cause, model quality, receipt binding,
delivery correctness, deployment readiness, security or mutation authority.
If another restart packet is required, `434-CARRYOVER-4.md` or its successor
must be a full cumulative packet containing every finding, remediation and
inoculation from all earlier issue-434 runs and this run. It supersedes the
older packets as the single reconstruction and inoculation source.

## Issue 434 observable run record carryover inoculation 3, step 1, round 1 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived because the complete step changes Python,
JSON, JSONL and Markdown and ships no Solidity. X-Ray, Solidity Auditor and
Fizz did not run. The complete 37-path tree was read without Horos exclusions.
Phylax, Ephoros and Hypomnema exit `0`, `0` and `0` after the fixes below.

The implementation entered audit as one signed 37-path union directly above
the current base. All earlier findings and inoculations were present before
any current verification or test ran. No intermediate carryover tree was
accepted or tested as an implementation exit.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I434-C3-S1-R1-01 | high | `scripts/run_observation.py` | Normalised actor-payload, raw-payload and compact aliases such as `rawInput`, `inputRaw`, `userInput`, `assistantOutput`, `assistantResponse`, `functionResult`, `toolCallArguments`, `requestArguments` and `jwt` validated clean as metadata. | fixed and guarded; token and compact actor/raw payload families now refuse while bounded descriptor suffixes remain accepted, and diagnostics copy none of the rejected names |
| I434-C3-S1-R1-02 | medium | schema, runtime and operator prose | A repository segment of 255 Unicode scalars could encode to 1,020 UTF-8 bytes and still validate as portable. A 255-emoji segment was reproduced clean twice, then failed materialisation on the current checkout host with `ENAMETOOLONG`. | fixed and guarded; each NFC segment is now bounded to 255 UTF-8 bytes in runtime, schema annotation, prose and tests, with a 252-byte emoji boundary accepted |
| I434-C3-S1-R1-03 | medium | schema, runtime and operator prose | The schema time pattern admitted leap-second spelling, impossible month 13 and hour 24 while the runtime refused them, so the declared timestamp surface drifted from executable acceptance. | fixed and guarded; schema and runtime now share one canonical uppercase RFC-3339 civil-time profile with real date validation, bounded offsets and no leap-second spelling |

Finding count: 3. Each mechanism was reproduced twice against signed
implementation `5bc47221a574164d1aa783c7f4fd2bc7b7f1675a` before repair. All three are
fixed on this audit branch. Another independent round is required.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | The three archived packet bytes match their issue digests. Their 23-entry, 8-entry and 10-entry ledgers recompute from `genesis` to the archived state fingerprints; study and runbook receipt digests match. All three preserved refs resolve exactly, verify locally and carry one required co-author and origin trailer. | clean on the fixed tree |
| `prior-art-drift` | The implementation commit is a single 37-path child of current base `367e966...`; signed attempt-5 was used as prior art and old check output was not promoted to current evidence. | clean on the fixed tree |
| `delegated-path-resolution` | Every patch target was an absolute path below the run worktree. Temporary fixtures and the standalone reporter used resolved target-rooted paths and were removed by their bounded test contexts. | clean on the fixed tree |
| `origin-checkout-drift` | Before and after each mutation batch, the protected checkout retained exactly its five pre-existing status lines. None was inspected for content, staged, removed or changed. | clean on the fixed tree |
| `gate-command-arity` | The reporter, four valid and five invalid CLIs, four separate one-file Brevitas commands, both Protasis modes, current Horos and obsolete Horos negative specimen accepted their exact documented shapes and returned the expected exits. | clean on the fixed tree |
| `current-main-loss` | The current tree retains Fiat 5.12.1, Elenchus 1.2.0, ADR-014, Atlas and all unrelated base paths. The run-to-current path set remains the declared 37-path observation surface, including this audit record. | clean on the fixed tree |
| `carryover-map-gap` | The cumulative fixture binds 36 original findings, four fixed prior-round mechanisms, three pre-audit input repairs, the confirmed reporter repair and these three audit-round mechanisms to current guards and the eight families. | clean on the fixed tree |
| `schema-runtime-drift` | Required and optional fields, enums, patterns, exact-number ceilings, metadata limits, Unicode policy and the new timestamp profile agree. The schema/runtime matrix now runs 252 cases. | fixed in this round; another round required |
| `wrong-kind-crash` | The recursive matrix mutates every structural value position in all four valid flows. Its 365 current cases produce zero crashes and zero unexpected clean results. | clean on the fixed tree |
| `lifecycle-reference-gap` | Sequence, capability pairing, retry, refusal, inferred selector, handoff, evidence and terminal relations remain guarded. The generated matrix runs nine cases clean. | clean on the fixed tree |
| `input-replacement` | Growth, FIFO, same-size rewrite, named swap, ancestor escape, bounded final reread and both reporter replacement windows remain in the eight-case replacement family. | clean on the fixed tree |
| `reporter-replacement` | Named-target swap and same-inode post-`fsync` rewrite guards pass. A fresh absolute-path reporter run executes 60 tests and writes only the expected complete report bytes. | clean on the fixed tree |
| `recorded-path-unicode` | Scalar validity, NFC, C0/C1 controls, bidi formatting, portable syntax and now 255-byte UTF-8 segment ceilings agree in runtime, schema annotation, prose and the 25-case path family. | fixed in this round; another round required |
| `name-normalisation-gap` | Separator, camel, Pascal, compact, token, prefix, suffix, actor-payload, raw-payload, hidden-work and acronym families now run 128 cases. Safe count, digest, format, identity and status descriptors remain accepted. | fixed in this round; another round required |
| `diagnostic-injection` | Text and canonical JSON still derive from one finding model. All new forbidden names resolve to the fixed `[forbidden-field]` pointer and no rejected alias appears in JSON findings. | clean on the fixed tree |
| `context-binding-gap` | The 17-case context family preserves issue/topic, step, role, selected skill and promise, paired Git identities, refusal promise, handoff producer and outcome relations. | clean on the fixed tree |
| `evidence-promotion` | Evidence ids, subjects, scopes, time domains, classes, inferred source events, handoff carriage and terminal outcomes remain exact backward bindings. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, finite number, string, key, collection, character-path and UTF-8 segment ceilings all refuse over-boundary inputs without coercion. | fixed in this round; another round required |
| `sensitive-payload` | Recursive forbidden-field checks now cover the reproduced actor, raw and JWT aliases across separated, camel, Pascal and compact forms without echoing them. | fixed in this round; another round required |
| `optional-telemetry` | Host, model and token facts remain optional, source-bound and exclusive with same-event unknowns. No estimator, exporter or backend was added. | clean on the fixed tree |
| `partial-or-stale-record` | Malformed tails, missing lifecycle halves, concurrent input mutation and report replacement continue to refuse. The fixes add no fallback or repair of source bytes. | clean on the fixed tree |
| `elenchus-report-drift` | The exact source-owned command, `unittest-json-v1` format and `.elenchus/run-observation.json` report path ran against this signed fixes commit. Final verdict: `guarded`; the parent report contains an assertion failure and the fixed-tree report is complete. | fixed and guarded; another round required |
| `closure-overclaim` | This round found three defects. No controller receipt, push, pull request, issue mutation, merge or closure action was performed. | another independent round is required |

### Current gate evidence

Focused and inoculation tests pass 60/60. The cumulative inoculation reports
859 cases across eight generated families and five map groups, zero crashes
and zero unexpected clean results. Root tests pass 179/179. The standalone
source reporter runs 60 tests and emits one complete report with no failures,
errors, skips, expected failures or unexpected successes.

All four valid CLIs exit `0`. The five required invalid fixtures exit `1` and
emit their expected `RO008`, `RO009`, `RO011`, `RO012` and `RO013` codes.
Promise sync writes zero files, its copy check reports 14 identical copies and
coverage reports 68/68. Phylax, Ephoros, Hypomnema, both Protasis modes,
Imprimatur and each separate Brevitas command exit `0`. Current Horos and
`git diff --check` exit `0`; obsolete Horos exits `2`.

Python syntax, the schema, coverage record, cumulative map and all 34 JSONL
objects parse. The published study and runbook remain byte-identical to their
receipted sources. The run-to-current set stays inside the declared 37-path
surface, including `audit/AUDIT.md`.

The runtime, schema, operator-document and focused-test SHA-256 values are
`a36c3f1bd5dedd00aebaa74699946f69db8bcce2434eb35e662ceb4af7bcba47`,
`f0ef6cc9064e8afb67d6830173dde093260b3ea5050152a9ca6c65cc95166e86`,
`b1e388ca2b4709d03e814d9b945384025f84b1508c95cc946fc8e8a86fccf3da`
and `11186842623d30b582dcd417e92d5faa0fbc166e60e5de64a382f42914026eda`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in #435. Fiat receipt binding
remains in #436, and cross-run diagnosis remains in #449. The schema remains a
source contract rather than an executed dependency. Field-name checks cannot
establish the meaning of an innocently named scalar, and the final bounded
reread cannot prevent a writer changing a file after the observation ends.

The record still treats sequence as authoritative over wall-clock order,
records retry scheduling rather than cancellation or a full attempt chain,
allows correlation ids to join separate paths and permits evidence narrower
than the opening subject. No finding was assigned to those declared
boundaries. This round makes no claim of capture completeness, external truth,
cause, model quality, delivery correctness, deployment readiness, security or
mutation authority.

If another restart packet is required, `434-CARRYOVER-4.md` must be one full,
self-contained aggregate of every earlier and current finding, remediation,
inoculation, audit count, unresolved lead, signed fixed-tree identity, receipt
digest and final check. Mason must apply that whole union before any tree
verification or test; intermediate `0 -> 1 -> 2 -> 3` reconstructions are not
acceptance trees.

## Issue 434 observable run record carryover inoculation 3, step 1, round 2 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived because the complete step changes Python,
JSON, JSONL and Markdown and ships no Solidity. X-Ray, Solidity Auditor and
Fizz did not run. The complete 37-path tree was read without Horos exclusions.
Phylax, Ephoros and Hypomnema exit `0`, `0` and `0` after the fixes below.

The implementation entered round 2 as one signed 37-path union. The 36
original carryover findings, four carried round-1 mechanisms, three pre-audit
input repairs, the reporter repair and all three round-1 audit repairs were
present before current verification or testing. No intermediate carryover tree
was accepted or tested as an implementation exit.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I434-C3-S1-R2-01 | high | `scripts/run_observation.py` | Actor-payload aliases `developerMessage`, `developermessage`, `agentOutput`, `agentoutput`, `humanInput` and `humaninput` validated clean as metadata. | fixed and guarded; systematic developer, agent and human actor-payload token and compact families now refuse while bounded descriptors remain accepted |
| I434-C3-S1-R2-02 | medium | schema, runtime and operator prose | A 17-segment path with 63 emoji per segment was 1,087 characters but 4,300 UTF-8 bytes and validated clean. | fixed and guarded; the complete NFC repository path is limited to 4,096 UTF-8 bytes as well as its existing character and per-segment limits |
| I434-C3-S1-R2-03 | medium | schema and runtime | The schema pattern accepted year zero and impossible civil dates such as `2026-02-30T00:00:00Z` while runtime civil-date validation refused them. | fixed and guarded; schema and runtime share one Gregorian-date pattern including leap-year boundaries and refusal of year zero |
| I434-C3-S1-R2-04 | medium | schema and runtime | Optional host and token facts accepted explicit sources such as `estimated from text` and `approximation` despite the exposed-fact contract. | fixed and guarded; optional sources and identities share one estimate-free exposed-fact rule in schema and runtime |

Finding count: 4. Each mechanism was reproduced twice against signed
implementation `be389ab2aaf4c8408db46a42e7260599861e9097` before repair. All four
are fixed on this audit branch. Another independent round is required.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | The three archived packet bytes and digests, their 23-entry, 8-entry and 10-entry ledgers, study and runbook receipts, signed refs, parents and required trailers remain bound by the cumulative fixture. | clean on the fixed tree |
| `prior-art-drift` | The implementation remains one 37-path cumulative tree above the current base. All carried mechanisms and inoculations were applied before current verification or acceptance tests. | clean on the fixed tree |
| `delegated-path-resolution` | Repository edits used absolute paths below the run worktree. One bounded audit-command incident created nine exact `/tmp/warden-*` outputs; each was removed immediately by exact-file `apply_patch`, all nine are absent, neither repository changed, and the affected CLI matrix passed again without redirection. | audit-process incident resolved; no product finding |
| `origin-checkout-drift` | The protected checkout retained exactly its five pre-existing status entries before and after each mutation batch. None was read for content, staged, removed or changed. | clean on the fixed tree |
| `gate-command-arity` | Reporter, four valid and five invalid CLIs, four separate one-file Brevitas commands, both Protasis modes, current Horos and the obsolete Horos specimen used their documented shapes and expected exits. | clean on the fixed tree |
| `current-main-loss` | The current tree retains the unrelated base surfaces. The run-to-current path set remains the declared 37-path observation surface, including this audit record. | clean on the fixed tree |
| `carryover-map-gap` | The fixture maps 36 original findings, four carried round-1 mechanisms, three current input repairs, one reporter repair, three audit-round-1 repairs and these four audit-round-2 repairs to current guards. | clean on the fixed tree |
| `schema-runtime-drift` | Required and optional values, wrong kinds, exact finite numbers, size ceilings, path rules, timestamp spelling and exposed-fact rules agree across schema and runtime. The schema/runtime matrix runs 258 cases. | fixed in this round; another round required |
| `wrong-kind-crash` | The recursive matrix mutates every structural value position in all four valid flows. Its 365 cases produce zero crashes and zero unexpected clean results. | clean on the fixed tree |
| `lifecycle-reference-gap` | Sequence, event order, capability pairing, retry, refusal, inferred selector, context, handoff, evidence and terminal relations remain guarded by the nine-case lifecycle matrix and focused tests. | clean on the fixed tree |
| `input-replacement` | Growth, FIFO, same-size rewrite, named swap, ancestor escape, final reread and both reporter replacement windows remain guarded by the eight-case replacement family. | clean on the fixed tree |
| `reporter-replacement` | Named-target swap and same-inode post-`fsync` rewrite guards pass. The source reporter writes one complete report and verifies the named bytes and identity. | clean on the fixed tree |
| `recorded-path-unicode` | Unicode scalar validity, NFC, control and bidi refusal, portable syntax, 255-byte segment limit and new 4,096-byte total limit agree across runtime, schema annotation, prose and the 26-case path family. | fixed in this round; another round required |
| `name-normalisation-gap` | Separator, camel, Pascal, compact, token, actor-payload, raw-payload, hidden-work and acronym families now run 143 cases. Safe bounded descriptors remain accepted. | fixed in this round; another round required |
| `diagnostic-injection` | Text and canonical JSON derive from one finding model. New aliases and rejected estimate text resolve to bounded diagnostics without copying rejected content. The parity/no-echo matrix runs eight cases. | clean on the fixed tree |
| `context-binding-gap` | The 17-case context family preserves issue/topic, step, role, selected skill and promise, paired Git identities, refusal promise, handoff producer and outcome relations. | clean on the fixed tree |
| `evidence-promotion` | Evidence ids, subjects, scopes, time domains, classes, inferred source events, handoff carriage, optional usage and terminal outcomes retain their exact backward bindings. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, finite number, string, key, collection, character-path, UTF-8 segment and complete-path ceilings refuse over-boundary input without coercion. | fixed in this round; another round required |
| `sensitive-payload` | Recursive forbidden-field checks cover developer, agent, human, user, assistant, function and tool payload aliases without echoing rejected names or values. | fixed in this round; another round required |
| `optional-telemetry` | Host, model and token facts remain optional, same-event bound, exclusive with unknowns and now explicitly free of estimated or approximated sources. No estimator, exporter or backend was added. | fixed in this round; another round required |
| `partial-or-stale-record` | Malformed tails, lifecycle halves, concurrent input mutation and report replacement refuse deterministically. The fixes add no fallback, retry loop or repair of source bytes. | clean on the fixed tree |
| `elenchus-report-drift` | The exact source-owned command, `unittest-json-v1` format and `.elenchus/run-observation.json` path ran against the signed fixes commit. Verdict: `guarded`; the parent report has 17 assertion failures and zero errors, while the fixed-tree report is complete. | fixed and guarded; another round required |
| `closure-overclaim` | This round found four defects. No controller receipt, push, pull request, issue mutation, merge or closure action was performed. | another independent round is required |

### Current gate evidence

Focused and inoculation tests pass 64/64. The cumulative inoculation reports
885 cases: 36 carryover-map, 4 fixed-round-1-map, 3 current-repair-map, 1
reporter-lead-map, 3 audit-round-1-map, 4 audit-round-2-map, 258
schema-runtime, 365 recursive-wrong-kind, 9 lifecycle-reference, 8
file-replacement, 26 path-representation, 143 normalised-field-name, 8
report-parity-no-echo and 17 work-repository-context cases. It reports zero
crashes and zero unexpected clean results. Root tests pass 183/183.

The source-owned reporter runs 64 tests and emits one complete
`elenchus.unittest.v1` report with no failures, errors, skips, expected failures
or unexpected successes. Elenchus reports `guarded`: its parent run has 17
assertion failures, zero infrastructure errors and no skips.

All four valid CLIs exit `0`. The five required invalid fixtures exit `1` and
emit their expected `RO009`, `RO013`, `RO008`, `RO012` and `RO011` codes.
Promise sync writes zero files, its copy check reports 14 identical copies and
coverage reports 68/68. Phylax, Ephoros, Hypomnema, both Protasis modes,
Imprimatur and each separate Brevitas command exit `0`. Current Horos and
`git diff --check` exit `0`; obsolete Horos exits `2`.

Python syntax, the schema, coverage record, cumulative map and all 34 JSONL
objects parse. The published study and runbook remain byte-identical to their
receipted sources. The run-to-current set stays inside the declared 37-path
surface, including `audit/AUDIT.md`.

The runtime, schema, operator-document and focused-test SHA-256 values are
`c79628359a41040708a2f06f57eaf8ae273e7faccce2675821c5f522bcf4622b`,
`9069845401cfb9192ce225000277bf41fe6e43d6c8f520c08cc94795701b6da3`,
`9846cdfcc4d842f5321e575a87a83d4143b1f607cea9c8d4bc5dcc7bc36e66cd`
and `0e03d5f1b47099f6342ec59e3c401e0b9f7a9eb3546a1fab9d701543e40fe091`;
all four match `tests/promise_machine_coverage.json`.

### Audit-process incident and uncompleted leads

The first CLI gate invocation mistakenly redirected bounded output outside the
target worktree to these exact files:

- `/tmp/warden-valid-success.out`
- `/tmp/warden-valid-refusal.out`
- `/tmp/warden-valid-retry.out`
- `/tmp/warden-valid-handoff.out`
- `/tmp/warden-invalid-bad-order.jsonl.out`
- `/tmp/warden-invalid-hidden-reasoning.jsonl.out`
- `/tmp/warden-invalid-missing-run-id.jsonl.out`
- `/tmp/warden-invalid-strengthened-evidence.jsonl.out`
- `/tmp/warden-invalid-unbound-evidence.jsonl.out`

All nine were removed immediately through exact absolute `apply_patch` targets
and verified absent. No repository or protected-origin path changed. The four
valid and five invalid CLI fixtures were rerun from clean state through
in-memory subprocess capture, without redirection, and returned their expected
codes. The rerun exposed no repository mechanism, so this remains an
audit-process incident rather than a fifth product finding.

Capture, redaction and persistence remain in #435. Fiat receipt binding
remains in #436, and cross-run diagnosis remains in #449. The schema remains a
source contract rather than an executed dependency. Field-name checks cannot
establish the meaning of an innocently named scalar, and the final bounded
reread cannot prevent a writer changing a file after observation ends.

The record treats sequence as authoritative over wall-clock order, records
retry scheduling rather than cancellation or a complete attempt chain, allows
correlation ids to join separate paths and permits evidence narrower than the
opening subject. No finding was assigned to those declared boundaries. This
round makes no claim of capture completeness, external truth, cause, model
quality, delivery correctness, deployment readiness, security or mutation
authority.

If another restart packet is required, `434-CARRYOVER-4.md` or its successor
must be one full, self-contained aggregate of every earlier and current
finding, remediation, inoculation, audit-round count, unresolved lead, signed
fixed-tree identity, receipt digest and final check. Mason must apply the whole
union to one final tree before any tree verification or acceptance test; no
intermediate reconstruction is an acceptance tree.

## Issue 434 observable run record carryover inoculation 3, step 1, round 3 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived because the complete step changes Python,
JSON, JSONL and Markdown and ships no Solidity. X-Ray, Solidity Auditor and
Fizz did not run. The complete 37-path tree was read without Horos exclusions.
Phylax, Ephoros and Hypomnema exit `0`, `0` and `0` after the fixes below.

The implementation entered round 3 as one signed 37-path union. All earlier
findings and inoculations, including both earlier audit rounds, were present
before current verification or acceptance testing. No intermediate carryover
tree was accepted or tested as an implementation exit.

### Findings

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: I434-C3-S1-R3-01; severity: high; file: `scripts/run_observation.py`; finding: Raw actor-payload synonym families such as `aiOutput`, `llmResponse`, `assistantReply`, `userQuery`, `chatHistory`, `messageHistory`, `toolReturn` and `functionReturn` validated clean as metadata.; status: fixed and guarded in `56425a622cd7f24e9a192cb9096643e36b211cc8`; actor and payload token families now cover AI and LLM output, replies, queries, histories, calls, observations, content, invocations and function or tool returns while bounded descriptor suffixes remain accepted
- id: I434-C3-S1-R3-02; severity: medium; file: schema and runtime; finding: Optional host and token facts accepted explicit estimate sources using `guessed`, `heuristic`, `projected` and `predicted`, despite the estimate-free exposed-fact contract.; status: fixed and guarded in `56425a622cd7f24e9a192cb9096643e36b211cc8`; schema and runtime now share those explicit estimate markers beside the carried estimate and approximation families

Finding count: 2. Each mechanism was reproduced twice against signed parent
`e3652820d42418ed5f068aad38a311862e66431a` before repair. Both guards were
then observed red on that unfixed tree. The fixes are signed and guarded in
`56425a622cd7f24e9a192cb9096643e36b211cc8`. Another independent round is
required.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | The three archived packet bytes and digests, their 23-entry, 8-entry and 10-entry ledgers, receipted study and runbook bytes, signed refs, parents and required trailers remain bound by the cumulative fixture. | clean on the fixed tree |
| `prior-art-drift` | The current implementation remains one cumulative 37-path child chain above base `367e966...`. Earlier checks were treated only as history; this round reran the current tests and gates. | clean on the fixed tree |
| `delegated-path-resolution` | Every temporary probe and report path was canonical, absolute and rooted under the run worktree. The standalone report was removed by its exact absolute path after inspection. | clean on the fixed tree |
| `origin-checkout-drift` | The protected checkout retained exactly its five pre-existing status entries before and after every write and report batch. No image content was read, staged, removed or changed. | clean on the fixed tree |
| `gate-command-arity` | The reporter, four valid and five invalid CLIs, four separate one-file Brevitas commands, both Protasis modes, current Horos and obsolete Horos used their documented shapes and expected exits. | clean on the fixed tree |
| `current-main-loss` | Fiat 5.12.1, Elenchus 1.2.0, ADR-014, Atlas and unrelated base paths remain present. The run-to-current scope stays at the declared 37 paths, including this audit record. | clean on the fixed tree |
| `carryover-map-gap` | The cumulative map binds the 36 original findings, four carried round-1 mechanisms, three current input repairs, one reporter repair, three audit-round-1 repairs, four audit-round-2 repairs and these two repairs to current guards and the eight families. | clean on the fixed tree |
| `schema-runtime-drift` | Closed fields, enums, patterns, exact-number ceilings, civil timestamps, Unicode and path limits, and exposed-fact sources agree. The matrix now runs 266 cases, including schema and runtime refusals for the four new estimate synonyms. | fixed in this round; another round required |
| `wrong-kind-crash` | The recursive matrix mutates every structural value position in all four valid flows. Its 365 cases produce zero crashes and zero unexpected clean results. | clean on the fixed tree |
| `lifecycle-reference-gap` | The nine-case generated matrix and focused guards cover order, capability pairing, retry, refusal, inferred selectors, handoff, evidence and terminal relations. | clean on the fixed tree |
| `input-replacement` | Growth, FIFO, same-size rewrite, named swap, ancestor escape, final reread and both reporter replacement windows remain guarded by the eight-case matrix. | clean on the fixed tree |
| `reporter-replacement` | Named-target swap and same-inode post-`fsync` rewrite guards pass. The source reporter writes one complete report and verifies its named bytes and identity. | clean on the fixed tree |
| `recorded-path-unicode` | Unicode scalar validity, NFC, C0 and C1 control refusal, bidi formatting refusal, portable syntax, 255-byte segment limit and 4,096-byte total limit agree across runtime, schema, prose and the 26-case matrix. | clean on the fixed tree |
| `name-normalisation-gap` | Separator, camel, Pascal, compact, token and acronym forms now cover actor inputs and outputs plus reply, query, history, call, return, generation, observation, invocation and content synonyms. The matrix runs 258 cases and retains safe descriptor suffixes. | fixed in this round; another round required |
| `diagnostic-injection` | Text and canonical JSON derive from one finding model. New forbidden names resolve to the fixed pointer, and direct guards prove that no rejected alias enters JSON findings. | clean on the fixed tree |
| `context-binding-gap` | The 17-case context family preserves issue or topic, step, role, selected skill and promise, paired Git identities, refusal promise, handoff producer and outcome relations. | clean on the fixed tree |
| `evidence-promotion` | Evidence ids, subjects, scopes, time domains, classes, inferred source events, handoff carriage, optional usage and terminal outcomes retain exact backward bindings. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, finite number, string, key, collection, character-path, UTF-8 segment and complete-path ceilings refuse over-boundary input without coercion. | clean on the fixed tree |
| `sensitive-payload` | Recursive name checks now cover the reproduced actor and payload synonym products without echoing rejected names or values. Innocently named scalar semantics remain outside the mechanical claim. | fixed in this round; another round required |
| `optional-telemetry` | Host, model and token facts remain optional, same-event bound, exclusive with unknowns and free of the carried and new explicit estimate-source families. No estimator, exporter or backend was added. | fixed in this round; another round required |
| `partial-or-stale-record` | Malformed tails, lifecycle halves, concurrent input mutation and report replacement refuse. The changes add no fallback, stability loop or source repair. | clean on the fixed tree |
| `elenchus-report-drift` | Exact source-owned command `python3 tests/emit_run_observation_report.py {report}`, format `unittest-json-v1` and report file `.elenchus/run-observation.json` ran against signed fixes commit `56425a6...`. Verdict: `guarded`; the parent report contains assertion failures and the fixed-tree report is complete. | fixed and guarded; another round required |
| `closure-overclaim` | This round found two defects. No controller receipt, push, pull request, issue mutation, merge or closure action was performed. | another independent round is required |

### Current gate evidence

Focused and inoculation tests pass 65/65. The cumulative inoculation reports
1,010 cases: 36 carryover-map, 4 fixed-round-1-map, 3 current-repair-map, 1
reporter-lead-map, 3 audit-round-1-map, 4 audit-round-2-map, 2
audit-round-3-map, 266 schema-runtime, 365 recursive-wrong-kind, 9
lifecycle-reference, 8 file-replacement, 26 path-representation, 258
normalised-field-name, 8 report-parity-no-echo and 17
work-repository-context cases. It reports zero crashes and zero unexpected
clean results. Root tests pass 184/184.

The source-owned reporter runs 65 tests and emits one complete
`elenchus.unittest.v1` report with no failures, errors, skips, expected
failures or unexpected successes. Elenchus reports `guarded`: its parent run
contains assertion failures rather than infrastructure errors.

All four valid CLIs exit `0`. The five required invalid fixtures exit `1` and
emit `RO009`, `RO013`, `RO008`, `RO012` and `RO011` respectively. Promise
sync writes zero files, its copy check reports 14 identical copies and
coverage reports 68/68. Phylax, Ephoros, Hypomnema, both Protasis modes,
Imprimatur and each separate Brevitas command exit `0`. Current Horos and
`git diff --check` exit `0`; obsolete Horos exits `2`.

Python syntax, the schema, coverage record, cumulative map and all 34 JSONL
objects parse. The published study and runbook remain byte-identical to their
receipted sources. The run-to-current set stays inside the declared 37-path
surface, including `audit/AUDIT.md`.

The runtime, schema, operator-document and focused-test SHA-256 values are
`2a4ff882391ff1249e4231ff0383613c1b9db8dd1769883d97804e5e9c72e0c2`,
`8064b0735f119b1556cdf79c04e2b7c6165c460990c4e807ee7f1fa5b6727388`,
`9846cdfcc4d842f5321e575a87a83d4143b1f607cea9c8d4bc5dcc7bc36e66cd`
and `e01e331744e8b7d9484c3b51a41edcc92eec84cc805349218e8ee0811ee09126`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in #435. Fiat receipt binding
remains in #436, and cross-run diagnosis remains in #449. The schema remains a
source contract rather than an executed dependency. Field-name checks cannot
establish the meaning of an innocently named scalar, and the final bounded
reread cannot prevent a writer changing a file after observation ends.

Non-bidirectional Unicode format characters and Unicode scalar noncharacters
remain inside the declared scalar and NFC path language; this round did not
widen the documented control and bidirectional-formatting refusal into a new
Unicode-category policy. The record also treats sequence as authoritative over
wall-clock order, records retry scheduling rather than cancellation or a
complete attempt chain, allows correlation ids to join separate paths and
permits evidence narrower than the opening subject. No finding was assigned to
those declared boundaries.

This round makes no claim of capture completeness, external truth, cause,
model quality, delivery correctness, deployment readiness, security or
mutation authority. If another restart packet is required,
`434-CARRYOVER-4.md` or its successor must be one full, self-contained
aggregate of every earlier and current finding, remediation, inoculation,
audit-round count, unresolved lead, signed fixed-tree identity, receipt digest
and final check. Mason must apply that whole union to one final tree before
any tree verification or acceptance test; no intermediate reconstruction is
an acceptance tree.

## Issue 434 observable run record carryover inoculation 3, step 1, round 4 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived because the complete step changes Python,
JSON, JSONL and Markdown and ships no Solidity. X-Ray, Solidity Auditor and
Fizz did not run. The complete 37-path tree was read without Horos exclusions.
Phylax, Ephoros and Hypomnema exit `0`, `0` and `0` after the fixes below.

The round began from one signed cumulative tree at
`a4b93d2982f5d0324c83fff31d21f4a2670894b0`. It already contained every
earlier finding, remediation and inoculation before this round's verification.
No intermediate carryover tree was treated as an acceptance tree.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I434-C3-S1-R4-01 | medium | schema, runtime and operator prose | Unicode `Cf` format controls outside the earlier bidi set, including soft hyphen, zero-width space, word joiner and byte-order mark, validated as portable repository paths. | fixed and guarded in `42dfd13628ef63be161a2d04dc6bc93613f2fdf2`; runtime refuses `Cc`, `Cf` and `Cs`, the schema publishes the same category boundary and BMP pattern, and path matrices cover the reproduced forms |
| I434-C3-S1-R4-02 | high | `scripts/run_observation.py` | Raw `systemInstructions` and `developerInstructions`, plus hidden-work `thinkingText` and `reflectionNotes`, validated clean as metadata. | fixed and guarded in `42dfd13628ef63be161a2d04dc6bc93613f2fdf2`; raw instruction and hidden thinking or reflection families now refuse while bounded count, digest, format and status descriptors remain accepted |
| I434-C3-S1-R4-03 | medium | schema and runtime | Optional host and token facts accepted explicit forecast, ballpark, assumption, extrapolation, modeled and modelled sources despite the estimate-free exposed-fact contract. | fixed and guarded in `42dfd13628ef63be161a2d04dc6bc93613f2fdf2`; schema and runtime share those explicit estimate markers beside the carried families |

Finding count: 3. Each mechanism was reproduced twice against signed parent
`a4b93d2982f5d0324c83fff31d21f4a2670894b0`. The focused guards were observed
red before repair and Elenchus reproduced parent assertion failures from the
source-owned reporter. The signed fix commit is
`42dfd13628ef63be161a2d04dc6bc93613f2fdf2`. Another independent round is
required.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | The three archived packets and digests, 23-entry, 8-entry and 10-entry ledgers, receipted study and runbook, signed refs, parents and trailers remain bound by the cumulative fixture. | clean on the fixed tree |
| `prior-art-drift` | The current result remains one cumulative 37-path chain above base `367e966...`; this round treated old results as history and reran all current evidence. | clean on the fixed tree |
| `delegated-path-resolution` | Every probe and report target was canonical, absolute and confined to the run worktree. Generated reports were removed by exact path. | clean on the fixed tree |
| `origin-checkout-drift` | The protected checkout retained exactly five pre-existing status entries before and after each batch. No image content was read, staged, removed or changed. | clean on the fixed tree |
| `gate-command-arity` | The reporter, four valid and five invalid CLIs, four one-file Brevitas commands, both Protasis modes, current Horos and obsolete Horos used their receipted shapes and expected exits. | clean on the fixed tree |
| `current-main-loss` | Fiat 5.12.1, Elenchus 1.2.0, ADR-014, Atlas and unrelated base work remain. The run-to-current inventory stays within the declared 37 paths. | clean on the fixed tree |
| `carryover-map-gap` | The map binds 36 original findings, four carried mechanisms, three current repairs, one reporter repair and all 12 findings from current rounds 1 through 4 to guards and eight families. | clean on the fixed tree |
| `schema-runtime-drift` | Closed fields, enums, patterns, numbers, civil times, path categories and limits, and exposed-fact estimate markers agree. The matrix runs 279 cases. | fixed in this round; another round required |
| `wrong-kind-crash` | The 365-case recursive matrix mutates every structural value position in four valid flows and reports zero crashes or unexpected clean results. | clean on the fixed tree |
| `lifecycle-reference-gap` | Nine generated cases plus focused order, capability, retry, refusal, inferred-selector, handoff, evidence and terminal guards pass. | clean on the fixed tree |
| `input-replacement` | Growth, FIFO, same-size rewrite, named swap, ancestor escape, bounded final reread and both reporter replacement windows remain guarded in eight cases. | clean on the fixed tree |
| `reporter-replacement` | Named-target swap and same-inode post-`fsync` rewrite guards pass; the reporter rereads and verifies one complete named report. | clean on the fixed tree |
| `recorded-path-unicode` | NFC, scalar validity, `Cc`, `Cf` and `Cs` refusal, portable syntax, and 255-byte segment and 4,096-byte path limits agree across code, schema declaration, prose and 30 cases. | fixed in this round; another round required |
| `name-normalisation-gap` | Separator, camel, Pascal, compact, token and acronym products now cover raw instructions and hidden thinking or reflection beside carried actor and payload families. The matrix runs 278 cases and preserves safe descriptors. | fixed in this round; another round required |
| `diagnostic-injection` | Text and canonical JSON use one finding model. The new forbidden aliases resolve to fixed pointers, and guards prove no rejected alias is echoed. | clean on the fixed tree |
| `context-binding-gap` | The 17-case family preserves issue or topic, step, role, selected skill and promise, paired Git identities, refusal promise, handoff producer and terminal relations. | clean on the fixed tree |
| `evidence-promotion` | Evidence id, subject, scope, time domain, class, source event, handoff carriage, optional usage and terminal outcome relations remain exact and backward. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, number, string, key, collection, character-path and UTF-8 path ceilings remain fail-closed. | clean on the fixed tree |
| `sensitive-payload` | Recursive name checks refuse the reproduced instruction payloads and all carried raw families without echo. Innocently named scalar meaning remains outside the mechanical claim. | fixed in this round; another round required |
| `optional-telemetry` | Host, model and token facts remain optional, source-bound, mutually exclusive with same-event unknowns and free of the expanded explicit estimate families. | fixed in this round; another round required |
| `partial-or-stale-record` | Malformed tails, lifecycle halves, input mutation and report replacement refuse without repair, fallback or an unbounded stability loop. | clean on the fixed tree |
| `elenchus-report-drift` | The exact command `python3 tests/emit_run_observation_report.py {report}`, format `unittest-json-v1` and file `.elenchus/run-observation.json` ran against signed commit `42dfd13...`. Verdict: `guarded`; the parent report contains assertion failures and the fixed report is complete. | fixed and guarded; another round required |
| `closure-overclaim` | This round found three defects. No controller receipt, push, pull request, issue mutation, merge or closure action was performed. | another independent round is required |

### Current gate evidence

Focused and inoculation tests pass 66/66. The cumulative inoculation reports
1,050 cases: 36 carryover-map, 4 fixed-round-1-map, 3 current-repair-map, 1
reporter-lead-map, 3 audit-round-1-map, 4 audit-round-2-map, 2
audit-round-3-map, 3 audit-round-4-map, 279 schema-runtime, 365
recursive-wrong-kind, 9 lifecycle-reference, 8 file-replacement, 30
path-representation, 278 normalised-field-name, 8 report-parity-no-echo and 17
work-repository-context cases. It reports zero crashes and zero unexpected
clean results. Root tests pass 185/185.

The source-owned reporter runs 66 tests and emits one complete
`elenchus.unittest.v1` report with no failures, errors, skips, expected
failures or unexpected successes. Elenchus reports `guarded` because the
unfixed parent report contains assertion failures.

All four valid CLIs exit `0`. The five required invalid fixtures exit `1` and
emit `RO009`, `RO013`, `RO008`, `RO012` and `RO011`. Promise sync writes zero
files, its check reports 14 identical copies and coverage reports 68/68.
Phylax, Ephoros, Hypomnema, Imprimatur and each separate Brevitas command for
the changed operator prose exit `0`. Current Horos and `git diff --check` exit `0`;
obsolete Horos exits `2`.

Python syntax, schema, coverage record, cumulative map and all JSONL objects
parse. The receipted study and runbook remain unchanged. The run-to-current
set stays inside the declared 37-path surface.

The runtime, schema, operator-document and focused-test SHA-256 values are
`7753182f25f3b91fb90de2ba77716b3f82d9a81607c4c2d2d4d6f61be77e2e80`,
`ee5d2fe4cda98e75896f4f0dec8fcdc4ddcbcb6e3b317815bff978ce9eb25c0e`,
`728bdd330daebde1907a10f61e7146ad1c147964b4bf38dc969ee6d1737eacf5`
and `4a177edbd153a683270ca982a1bbe3189a3734cc615e67927532e4b4f8cb265b`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in #435. Fiat receipt binding
remains in #436, and cross-run diagnosis remains in #449. The schema remains a
source contract rather than an executed dependency. Field-name checks cannot
establish the meaning of an innocently named scalar, and the final bounded
reread cannot prevent a writer changing a file after observation ends.

Unicode scalar noncharacters and non-`Cf` default-ignorable marks remain
inside the declared scalar and NFC path language. The record treats sequence
as authoritative over wall-clock order, records scheduled retries rather than
cancellation or a full attempt chain, permits joined correlation paths and
allows evidence narrower than the opening subject. These declared boundaries
did not produce another in-scope finding.

This round makes no claim of capture completeness, external truth, cause,
model quality, delivery correctness, deployment readiness, security or
mutation authority. Any later `434-CARRYOVER-4.md` or successor must be one
full self-contained aggregate of every pass. Mason must apply the whole union
to one final tree before any verification or acceptance test; no intermediate
reconstruction is an acceptance tree.

## Issue 434 observable run record carryover inoculation 3, step 1, round 5 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived because the complete step changes Python,
JSON, JSONL and Markdown and ships no Solidity. X-Ray, Solidity Auditor and
Fizz did not run. The complete 37-path tree was read without Horos exclusions.
Phylax, Ephoros and Hypomnema exit `0`, `0` and `0` after the fixes below.

The round began from signed cumulative audit tree
`abcf1b195896ed4ac03cc579c3d41637d9792de6`, whose parent is signed fixed tree
`42dfd13628ef63be161a2d04dc6bc93613f2fdf2`. Every earlier finding,
remediation and inoculation was present before this round's verification. No
intermediate carryover tree was treated as an acceptance tree.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I434-C3-S1-R5-01 | high | schema and `scripts/run_observation.py` | Raw or hidden metadata names such as `developerDirective`, `cognitiveProcess` and Unicode-confusable `prоmpt` validated clean. Untyped safe-suffix fields such as `promptCount: "the complete raw prompt text"` also bypassed the refusal. | fixed and guarded in `717a2de305e01b7a32970424c0ede7a695639642`; names require printable ASCII, the raw and hidden families cover the reproduced synonyms, and a descriptor exemption requires a value of the descriptor's declared kind |
| I434-C3-S1-R5-02 | medium | schema and `scripts/run_observation.py` | Optional host and token facts accepted explicit estimate sources including `rough count`, `approx count` and `derived from text`, despite the estimate-free exposed-fact contract. | fixed and guarded in `717a2de305e01b7a32970424c0ede7a695639642`; schema and runtime share the expanded explicit approximation, derivation, inference, calculation, rounding and uncertainty families |
| I434-C3-S1-R5-03 | medium | schema, runtime and operator prose | Windows device spellings using superscript digits, including `COM¹`, `COM².txt` and `LPT³.log`, validated as portable repository paths. | fixed and guarded in `717a2de305e01b7a32970424c0ede7a695639642`; schema, runtime, prose and generated path cases refuse the superscript-one, superscript-two and superscript-three forms |
| I434-C3-S1-R5-04 | low | `scripts/run_observation.py` | The first repair treated compact safe descriptors such as `promptcount: 2` and `analysisdigest: <sha256>` as forbidden even though separated equivalents remained valid. | fixed and guarded in `29007dfe350c50391f31f1e7d3f7609e6aff9628`; compact suffixes use the same typed descriptor exemption as separated names |

Finding count: 4. The first three mechanisms were reproduced twice against
signed parent `abcf1b195896ed4ac03cc579c3d41637d9792de6`; the fourth was
reproduced twice during adversarial review of signed repair `717a2de...`.
Focused guards were red before each causal repair. Signed fixed-tree commits
are `717a2de305e01b7a32970424c0ede7a695639642` and
`29007dfe350c50391f31f1e7d3f7609e6aff9628`. Another independent round is
required.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | The three archived packet bytes and digests, their 23-entry, 8-entry and 10-entry ledgers, receipted study and runbook, signed refs, parents and required trailers remain bound by the cumulative fixture. | clean on the fixed tree |
| `prior-art-drift` | The result remains one cumulative 37-path chain above base `367e9662384bb29ea94576d270ab86744f3326a2`. Earlier results were history only; this round reran current evidence. | clean on the fixed tree |
| `delegated-path-resolution` | One operator wrapper wrongly redirected focused output to `/tmp/round5-focused.out` and then failed because zsh reserves `status`. The wrapper was unreceipted and contributed no product evidence. That exact file was deleted and proved absent; the affected check was rerun with a canonical absolute target-rooted output and a non-reserved variable, then target scope and protected origin were reverified. Every product probe and accepted report was confined to the run worktree. | operator incident contained; product tree clean |
| `origin-checkout-drift` | The protected checkout retained exactly its five pre-existing status entries before and after every mutation and report batch. No image content was read, staged, removed or changed. | clean on the fixed tree |
| `gate-command-arity` | The source reporter, four valid and five invalid CLIs, four separate one-file Brevitas commands, both Protasis modes, current Horos and obsolete Horos used their receipted shapes and expected exits. | clean on the fixed tree |
| `current-main-loss` | Fiat 5.12.1, Elenchus 1.2.0, ADR-014, Atlas and unrelated base paths remain present. The run-to-current inventory stays at the declared 37 paths. | clean on the fixed tree |
| `carryover-map-gap` | The cumulative map binds 36 original findings, four fixed carried mechanisms, three current input repairs, one reporter repair and all 16 audit findings from rounds 1 through 5 to current guards and eight generated families. | clean on the fixed tree |
| `schema-runtime-drift` | Closed fields, printable-ASCII names, enums, patterns, number ceilings, civil times, Unicode paths and exposed-fact sources agree. The differential matrix runs 309 cases. | fixed in this round; another round required |
| `wrong-kind-crash` | The recursive matrix mutates every structural value position in four valid flows. Its 365 cases report zero crashes and zero unexpected clean results. | clean on the fixed tree |
| `lifecycle-reference-gap` | Nine generated cases plus focused order, capability, retry, refusal, inferred-selector, handoff, evidence and terminal guards pass. | clean on the fixed tree |
| `input-replacement` | Growth, FIFO, same-size rewrite, named swap, ancestor escape, bounded final reread and both reporter replacement windows remain guarded in eight cases. | clean on the fixed tree |
| `reporter-replacement` | Named-target swap and same-inode post-`fsync` rewrite guards pass. A fresh absolute-path source report ran 67 tests and its complete named bytes and identity were checked before exact removal. | clean on the fixed tree |
| `recorded-path-unicode` | NFC, scalar validity, `Cc`, `Cf` and `Cs` refusal, portable syntax, byte ceilings and Windows numeric and superscript device aliases agree across runtime, schema, prose and 33 generated cases. | fixed in this round; another round required |
| `name-normalisation-gap` | Separator, camel, Pascal, compact, token and acronym products now cover the carried and new raw and hidden families. Printable ASCII excludes confusable names, and typed descriptor values preserve both separated and compact safe names. The matrix runs 317 cases. | fixed in this round; another round required |
| `diagnostic-injection` | Text and canonical JSON derive from one finding model. Invalid and forbidden names use fixed pointer segments, and guards prove none of the reproduced names or values is echoed. | clean on the fixed tree |
| `context-binding-gap` | The 17-case family preserves issue or topic, step, role, selected skill and promise, paired Git identities, refusal promise, handoff producer and terminal relations. | clean on the fixed tree |
| `evidence-promotion` | Evidence ids, subjects, scopes, time domains, classes, source events, handoff carriage, optional usage and terminal outcomes retain exact backward bindings. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, number, string, key, collection, character-path and UTF-8 path ceilings remain fail-closed without coercion. | clean on the fixed tree |
| `sensitive-payload` | Recursive checks refuse the reproduced directives, rules, turns, utterances, artifacts and command-family payloads, plus hidden cognition families and Unicode-confusable names, without echo. Innocently named scalar meaning remains outside the mechanical claim. | fixed in this round; another round required |
| `optional-telemetry` | Host, model and token facts remain optional, source-bound and exclusive with same-event unknowns. Explicit rough, approximate, derived, inferred, calculated, rounded, unmeasured and speculative sources now refuse beside the carried estimate families. | fixed in this round; another round required |
| `partial-or-stale-record` | Malformed tails, lifecycle halves, concurrent input mutation and report replacement refuse without fallback, repair or an unbounded stability loop. | clean on the fixed tree |
| `elenchus-report-drift` | The exact source command `python3 tests/emit_run_observation_report.py {report}`, format `unittest-json-v1` and report file `.elenchus/run-observation.json` ran against signed fixed tree `29007df...`. Verdict: `guarded`; the parent report records an assertion failure and the fixed report is complete. | fixed and guarded; another round required |
| `closure-overclaim` | This round found four defects. No controller receipt, push, pull request, issue mutation, merge or closure action was performed. | another independent round is required |

### Current gate evidence

Focused and inoculation tests pass 67/67. The cumulative inoculation reports
1,126 cases: 36 carryover-map, 4 fixed-round-1-map, 3 current-repair-map, 1
reporter-lead-map, 3 audit-round-1-map, 4 audit-round-2-map, 2
audit-round-3-map, 3 audit-round-4-map, 4 audit-round-5-map, 309
schema-runtime, 365 recursive-wrong-kind, 9 lifecycle-reference, 8
file-replacement, 33 path-representation, 317 normalized-field-name, 8
report-parity-no-echo and 17 work-repository-context cases. It reports zero
crashes and zero unexpected clean results. Root tests pass 186/186.

The source-owned reporter runs 67 tests and emits one complete
`elenchus.unittest.v1` report with no failures, errors, skips, expected
failures or unexpected successes. Elenchus reports `guarded` because its
unfixed parent report contains an assertion failure.

All four valid CLIs exit `0`. The five required invalid fixtures exit `1` and
emit `RO009`, `RO013`, `RO008`, `RO012` and `RO011`. Promise sync writes zero
files, its check reports 14 identical copies and coverage reports 68/68.
Phylax, Ephoros, Hypomnema, both Protasis modes, Imprimatur and each separate
Brevitas command exit `0`. Current Horos and `git diff --check` exit `0`;
obsolete Horos exits `2`.

Python syntax, schema, coverage record, cumulative map and all 34 JSONL
objects parse. The receipted study and runbook remain byte-identical to their
published copies. The run-to-current set stays inside the declared 37-path
surface. The protected origin retains exactly its five recorded paths.

The runtime, schema, operator-document and focused-test SHA-256 values are
`0e20b47e019d50115d94c4538fd42160bd96e4bae0748121697ea35f5f1af5cb`,
`51dc2e885e2303eea2cbe824b4f241bf4f25045d09f0fbc081ff2d8648ca5d67`,
`b75e57ea191ba4ea170103088f249279683db4d0d4ae16c6a3e43e3ac01925db`
and `e18095a4c6e3d9fc9afee037b3e6f863b7ad51e0bde4dfee010f7d0d5e6edc08`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in #435. Fiat receipt binding
remains in #436, and cross-run diagnosis remains in #449. The schema remains a
source contract rather than an executed dependency. Field-name checks cannot
establish the meaning of an innocently named scalar, and the final bounded
reread cannot prevent a writer changing a file after observation ends.

Unicode scalar noncharacters and non-`Cf` default-ignorable marks remain
inside the declared scalar and NFC path language. The record treats sequence
as authoritative over wall-clock order, records scheduled retries rather than
cancellation or a complete attempt chain, permits joined correlation paths
and allows evidence narrower than the opening subject. These declared
boundaries did not produce another in-scope finding.

The failed `/tmp` wrapper is retained above as an operator-path lead rather
than promoted into product evidence. This round makes no claim of capture
completeness, external truth, cause, model quality, delivery correctness,
deployment readiness, security or mutation authority.

If another restart packet is required, `434-CARRYOVER-4.md` or any successor
must be one full, self-contained aggregate of every pass, including earlier
daisy-chained packets and every later audit. It must carry every finding,
remediation, inoculation, audit-round count, unresolved lead, signed
fixed-tree identity, receipt digest and final check. Mason must apply that
whole amalgamated union to one final tree before any tree verification or
acceptance test. No partial or intermediate reconstruction is an acceptance
tree.

## Issue 434 observable run record carryover inoculation 3, step 1, round 6 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived because the complete 37-path step changes
Python, JSON, JSONL and Markdown and ships no Solidity. X-Ray, Solidity
Auditor and Fizz did not run. The complete tree was reviewed without Horos
exclusions. Phylax, Ephoros and Hypomnema exit `0`, `0` and `0` after the
fixes below.

The round began from signed cumulative audit tree
`f0bf34c8003a61ab6ba659d9210aa03c16d84e06`, whose parent is signed fixed
tree `29007dfe350c50391f31f1e7d3f7609e6aff9628`. Every earlier finding,
remediation and inoculation was present before this round. No intermediate
tree was treated as an acceptance tree.

### Findings

`I434-C3-S1-R6-01` is high severity in `scripts/run_observation.py`. Bare
`content` and related content-payload metadata names validated clean, although
the operator contract refuses raw-payload name families. It is fixed and
guarded in `934fc1ba238f32cc1827d1b1cb06f001f6bac7f2`: `content` and `contents`
token families now refuse without echo, while typed separated and compact
count and digest descriptors remain valid.

`I434-C3-S1-R6-02` is medium severity in `audit/AUDIT.md` and the decision
identity tests. Two reconstructed audit sentences still called the observation
decision ADR-014 after the distinct Wave Atlas decision took that number. It
is fixed and guarded in `934fc1ba238f32cc1827d1b1cb06f001f6bac7f2`: the
observation file, heading, published references and reconstructed audit
sentences remain ADR-015, while the distinct ADR-014 file and heading are
unchanged.

Finding count: 2. Each mechanism was reproduced twice against signed parent
`f0bf34c8003a61ab6ba659d9210aa03c16d84e06`. The focused guards were red
before repair and green afterwards. The exact source-owned Elenchus command
ran against signed fix commit `934fc1ba238f32cc1827d1b1cb06f001f6bac7f2`.
Verdict: `guarded`; the detached-parent report records assertion failures and
the fixed report is complete. Another independent round is required.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | The three packet identities, digests, source runs and preserved refs remain exact in the cumulative fixture; its 36 original findings and archived receipt boundaries still pass. | clean on the fixed tree |
| `prior-art-drift` | The current result remains one cumulative 37-path chain above `367e9662384bb29ea94576d270ab86744f3326a2`; earlier checks were history only and all current evidence was rerun. | clean on the fixed tree |
| `delegated-path-resolution` | Both reproduction directories and the report path were canonical absolute paths under the run worktree. One wrong unittest selector and one read-only zsh reserved-variable loop failed before product evidence and were rerun correctly; neither created an accepted output or changed another path. | operator diagnostics contained; product tree clean |
| `origin-checkout-drift` | The protected checkout retained exactly five pre-existing status entries before and after every write and report batch. No image content was read, staged, removed or changed. | clean on the fixed tree |
| `gate-command-arity` | The reporter, four valid and five invalid CLIs, both Protasis modes, four separate Brevitas forms, current Horos and obsolete Horos used the receipted shapes and expected exits. | clean on the fixed tree |
| `current-main-loss` | Fiat 5.12.1, Elenchus 1.2.0, Wave Atlas and unrelated base paths remain. The observation decision is ADR-015 and the distinct existing ADR-014 is unchanged. | fixed in this round; another round required |
| `carryover-map-gap` | The map binds 36 original findings, four carried guards, three current repairs, one reporter repair and all 18 audit findings from rounds 1 through 6 to current guards and eight families. | clean on the fixed tree |
| `schema-runtime-drift` | Closed fields, printable-ASCII names, enums, patterns, exact-number ceilings, civil times, path rules, limits and optional facts agree. The differential matrix runs 309 cases. | clean on the fixed tree |
| `wrong-kind-crash` | The 365-case recursive matrix mutates every structural value position in four valid flows and reports zero crashes and zero unexpected clean results. | clean on the fixed tree |
| `lifecycle-reference-gap` | Nine generated cases plus focused order, capability, retry, refusal, inferred-selector, handoff, evidence and terminal guards pass. | clean on the fixed tree |
| `input-replacement` | Growth, FIFO, same-size rewrite, named swap, ancestor escape and the bounded final reread remain guarded in the eight-case replacement family. | clean on the fixed tree |
| `reporter-replacement` | Named-target swap and same-inode post-`fsync` rewrite guards pass. The fresh absolute-path reporter ran 69 tests and its complete bytes and identity were checked before removal. | clean on the fixed tree |
| `recorded-path-unicode` | NFC, scalar validity, `Cc`, `Cf` and `Cs` refusal, portable syntax, byte ceilings and numeric or superscript device aliases agree across runtime, schema, prose and 33 cases. | clean on the fixed tree |
| `name-normalisation-gap` | Separator, camel, Pascal, compact, token, acronym and content families now run 329 cases. Raw content names refuse; typed separated and compact count or digest descriptors remain accepted. | fixed in this round; another round required |
| `diagnostic-injection` | Text and canonical JSON derive from one finding model. Invalid and forbidden content names use fixed pointer segments, and guards prove rejected names and values are not echoed. | clean on the fixed tree |
| `context-binding-gap` | The 17-case family preserves issue or topic, step, role, selected skill and promise, paired Git identities, refusal promise, handoff producer and terminal relations. The ADR identity guard binds the named decision files and reconstructed audit record. | fixed in this round; another round required |
| `evidence-promotion` | Evidence ids, subjects, scopes, time domains, classes, source events, handoff carriage, optional usage and terminal outcomes retain exact backward bindings. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, number, string, key, collection, character-path and UTF-8 path ceilings remain fail-closed without coercion. | clean on the fixed tree |
| `sensitive-payload` | Recursive checks now refuse bare and compound content families beside all carried raw and hidden families without echo. Innocently named scalar meaning remains outside the mechanical claim. | fixed in this round; another round required |
| `optional-telemetry` | Host, model and token facts remain optional, source-bound and exclusive with same-event unknowns; explicit estimate families and wrong kinds refuse. | clean on the fixed tree |
| `partial-or-stale-record` | Malformed tails, lifecycle halves, concurrent input mutation, report replacement and stale decision identity refuse without fallback, repair or an unbounded stability loop. | fixed in this round; another round required |
| `elenchus-report-drift` | The exact command `python3 tests/emit_run_observation_report.py {report}`, format `unittest-json-v1` and file `.elenchus/run-observation.json` ran against signed commit `934fc1b...`. Verdict: `guarded`; the parent report contains assertion failures and the fixed report is complete. | fixed and guarded; another round required |
| `closure-overclaim` | This round found two defects. No controller receipt, push, pull request, issue mutation, merge or closure action was performed. | another independent round is required |

### Current gate evidence

Focused and inoculation tests pass 69/69. The cumulative inoculation reports
1,140 cases: 36 carryover-map, 4 fixed-round-1-map, 3 current-repair-map, 1
reporter-lead-map, 3 audit-round-1-map, 4 audit-round-2-map, 2
audit-round-3-map, 3 audit-round-4-map, 4 audit-round-5-map, 2
audit-round-6-map, 309 schema-runtime, 365 recursive-wrong-kind, 9
lifecycle-reference, 8 file-replacement, 33 path-representation, 329
normalised-field-name, 8 report-parity-no-echo and 17
work-repository-context cases. It reports zero crashes and zero unexpected
clean results. Root tests pass 188/188.

The source-owned reporter runs 69 tests and emits one complete
`elenchus.unittest.v1` report with no failures, errors, skips, expected
failures or unexpected successes. Elenchus reports `guarded` because the
unfixed parent report contains assertion failures.

All four valid CLIs exit `0`. The five required invalid fixtures exit `1` and
emit `RO009`, `RO013`, `RO008`, `RO012` and `RO011`. Promise sync writes zero
files, its check reports 14 identical copies and coverage reports 68/68.
Phylax, Ephoros, Hypomnema, both Protasis modes, Imprimatur and each separate
Brevitas command exit `0`. Current Horos and `git diff --check` exit `0`;
obsolete Horos exits `2`.

Python syntax, schema, coverage record, cumulative map and all 34 tracked
JSONL objects parse. The receipted study and runbook remain byte-identical to
their published copies. The run-to-current set stays at the declared 37 paths
and contains no image. The protected origin retains exactly its five recorded
paths.

The runtime, schema, operator-document and focused-test SHA-256 values are
`0b18caf55ca5d35f3724025fb2231fd880b048b05ea847a1479be14e6c64ce0b`,
`51dc2e885e2303eea2cbe824b4f241bf4f25045d09f0fbc081ff2d8648ca5d67`,
`b75e57ea191ba4ea170103088f249279683db4d0d4ae16c6a3e43e3ac01925db`
and `18ec9b78a0dfdc10657a8d6f010fe679586aa0f82b18ba92ccfa71b5d699e268`;
all four match `tests/promise_machine_coverage.json`.

### Leads not pursued

Capture, redaction and persistence remain in #435. Fiat receipt binding
remains in #436, and cross-run diagnosis remains in #449. The schema remains a
source contract rather than an executed dependency. Field-name checks cannot
establish the meaning of an innocently named scalar, and the final bounded
reread cannot prevent a writer changing a file after observation ends.

Unicode scalar noncharacters and non-`Cf` default-ignorable marks remain
inside the declared scalar and NFC path language. Sequence remains
authoritative over wall-clock order; retries are scheduled rather than a full
attempt chain. The record allows correlation ids to join paths. Evidence may
be narrower than the opening subject. These declared boundaries did not produce another
in-scope finding.

This round makes no claim of capture completeness, external truth, cause,
model quality, delivery correctness, deployment readiness, security or
mutation authority. Any later `434-CARRYOVER-4.md` or successor must remain
one self-contained aggregate of every pass if a restart is required. No
partial or intermediate reconstruction is an acceptance tree.

## Issue 434 observable run record carryover inoculation 3, step 1, round 8 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived: the complete 37-path step changes Python,
JSON, JSONL and Markdown and ships no Solidity. The full tree was reviewed
without Horos exclusions. Phylax, Ephoros and Hypomnema exit `0` on the fixed
tree.

The round began at signed audit head
`941563a9df09f478c1ca2b2ee59b6f2768d2dfc4`, whose sole parent is signed fixed
tree `69d28ba2f253b23f58e28abae64fc466cfd170d5`. It ended at signed repair
`1ed72f7154bd4ff5ea39066c21665a51daad9594`, whose sole parent is that audit
head. All three prior packet identities, digests, refs, historical findings,
current repairs and inoculations were applied to one tree before any check.

### Finding

`I434-C3-S1-R8-01` is high severity in `scripts/run_observation.py`. Raw
instruction and directive aliases, including `instructionSet`,
`instructionsText`, `directiveSet` and `directiveText`, validated clean as
metadata although the operator contract excludes raw instructions and
directives. Two independent target-rooted probes against signed head
`941563a9df09f478c1ca2b2ee59b6f2768d2dfc4` each returned zero findings.

The repair in `1ed72f7154bd4ff5ea39066c21665a51daad9594` makes token and
compact normalisation refuse those families with `RO014`, while correctly
typed bounded descriptors remain valid. The runtime, schema declaration,
operator document, focused guard, systematic inoculation, carryover map and
coverage digests change together. The initial systematic red guard exposed the
uncovered compact spelling; the repair adds the compact marker and the final
guard is green.

The exact source-owned Elenchus command ran against the signed repair:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py \
  --ref 1ed72f7154bd4ff5ea39066c21665a51daad9594 \
  --test-command "python3 tests/emit_run_observation_report.py {report}" \
  --report-format unittest-json-v1 \
  --report-file .elenchus/run-observation.json
```

Verdict: `guarded -- the runner report records a parent assertion failure`.
The fixed-tree reporter is complete `elenchus.unittest.v1`, 70 tests, zero
failures, errors, skips, expected failures and unexpected successes. This is
the configured final round and it found one defect: no controller receipt,
push, pull request, issue action, integration or closure occurred. A full
`434-CARRYOVER-4.md` packet and halted restart are required.

### Risk coverage

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- risk id: `carryover-chain-gap`; disposition: Three prior packet URLs, digests, source runs and preserved refs remain exact in the cumulative fixture.
- risk id: `prior-art-drift`; disposition: All prior remediation was applied before one fixed-tree verification; history was not promoted to current evidence.
- risk id: `delegated-path-resolution`; disposition: Probes, report and edits used canonical paths below the run worktree.
- risk id: `origin-checkout-drift`; disposition: The protected checkout retained exactly its five pre-existing paths; no contents were read or changed.
- risk id: `gate-command-arity`; disposition: Reporter, valid/invalid CLI, Promise, lint and Horos command forms used their receipted shapes.
- risk id: `current-main-loss`; disposition: Fiat, Elenchus, Wave Atlas, ADR-014 and ADR-015 remain distinct and present.
- risk id: `carryover-map-gap`; disposition: Map binds 36 historical findings, four carried repairs and 20 audit-round mechanisms through round 8.
- risk id: `schema-runtime-drift`; disposition: Runtime and schema now declare the instruction/directive boundary; 309 differential cases pass.
- risk id: `wrong-kind-crash`; disposition: 365 recursive cases report zero crashes and zero unexpected clean results.
- risk id: `lifecycle-reference-gap`; disposition: Nine lifecycle/reference cases pass.
- risk id: `input-replacement`; disposition: Eight replacement/final-reread cases pass.
- risk id: `reporter-replacement`; disposition: Named-target and same-inode post-fsync guards pass; the current reporter is complete.
- risk id: `recorded-path-unicode`; disposition: NFC, scalar, `Cc`, `Cf`, `Cs`, portable and byte-ceiling guards pass.
- risk id: `name-normalisation-gap`; disposition: 384 generated name cases cover separated, camel, compact and descriptor forms; fixed in this round.
- risk id: `diagnostic-injection`; disposition: Refused names and values use fixed pointers and are not echoed.
- risk id: `context-binding-gap`; disposition: Context, paired Git identity, handoff and distinct ADR identities remain guarded.
- risk id: `evidence-promotion`; disposition: Evidence, source-event and terminal relations retain their exact backward bindings.
- risk id: `unbounded-input`; disposition: File, line, event, nesting, scalar, key, collection and path ceilings remain fail-closed.
- risk id: `sensitive-payload`; disposition: Instruction and directive raw payload aliases now join the carried forbidden families; fixed in this round.
- risk id: `optional-telemetry`; disposition: Optional host, model and token facts remain source-bound and estimate-free.
- risk id: `partial-or-stale-record`; disposition: Tails, lifecycle halves, concurrent input mutation, report replacement and stale identity refuse.
- risk id: `elenchus-report-drift`; disposition: Exact command, format and report path give a guarded detached-parent comparison and complete fixed report.
- risk id: `closure-overclaim`; disposition: One configured-final-round finding prevents receipt and requires full aggregate carryover and restart.

### Current gate evidence

Focused and inoculation tests pass 70/70. The cumulative inoculation reports
1,197 cases: 36 carryover-map, 4 fixed-round-1-map, 3 current-repair-map, 1
reporter-lead-map, 3 audit-round-1-map, 4 audit-round-2-map, 2
audit-round-3-map, 3 audit-round-4-map, 4 audit-round-5-map, 2
audit-round-6-map, 1 audit-round-7-map, 1 audit-round-8-map, 309
schema-runtime, 365 recursive-wrong-kind, 9 lifecycle-reference, 8
file-replacement, 33 path-representation, 384 normalized-field-name, 8
report-parity-no-echo and 17 work-repository-context cases. Root tests pass
189/189. Promise sync/check reports 14 identical copies and coverage 68/68.
Phylax, Ephoros, Hypomnema, Imprimatur, four separate Brevitas commands,
current Horos and diff check exit `0`; obsolete Horos exits `2` as required.

The runtime, schema, operator document, focused-test, map and coverage SHA-256
values are `a03a37e1d447d58ed7eeb64cd1a2d4487452c77803343c011044352d5a5eb61c`,
`12bfc139217adf336bfa39b082097dc9b493e13c49cb6e25787bcdb5991499b6`,
`a0a028615dddc9e379c1ae3cfd638e8d1cec0687cf3d13b21251c2222803c5b9`,
`1f02c6d2eb163b36c3faf8cf7dec356212879d7fcf29cfefcdd6523166d7e9bd`,
`fbbb8ab95b7cdf65fc9f4f1af9e35ab050b73d18ad974b100f5e9791e3059e14` and
`1d99d9781364c2517775700f3f9c3a7b1ba05f393391249ebc2ab0953c9dd0a8`.

### Restart handoff

The next attempt must use one `434-CARRYOVER-4.md` packet that aggregates all
findings, remediations, inoculations, audit counts, unresolved leads, signed
fixed-tree identities, receipts and final checks from packets one through
three and rounds one through eight. Mason must apply the complete aggregate to
one tree before any test, lint, reporter, verification or audit round. No
incremental packet chain or intermediate acceptance tree is permitted.

## Issue 434 observable run record carryover inoculation 3, step 1, round 7 -- 2026-08-23

### Suite disposition

The Solidity suite remains waived: the complete 37-path step changes Python,
JSON, JSONL and Markdown and ships no Solidity. X-Ray, Solidity Auditor and
Fizz did not run. The full tree was reviewed without Horos exclusions.
Phylax, Ephoros and Hypomnema exited `0`, `0` and `0` on the fixed tree.

The round started from signed audit head
`06787433ebef83be947bb06e36718422a04f9625`, whose parent is signed fixed tree
`934fc1ba238f32cc1827d1b1cb06f001f6bac7f2`. The repair is signed commit
`69d28ba2f253b23f58e28abae64fc466cfd170d5`; it has that audit head as its
sole parent. All prior carryover packets, findings, remediations and
inoculations were present before this round. No intermediate tree was accepted.

### Findings

`I434-C3-S1-R7-01` is high severity in `scripts/run_observation.py`. Raw
execution, source and trace aliases including `command`, `shellCommand`,
`subprocessCommand`, `commandLine`, `shellScript`, `sourceCode`, `stackTrace`,
`executionTrace` and `traceData` validated clean as metadata despite the
record's raw-payload boundary. It is fixed and guarded in
`69d28ba2f253b23f58e28abae64fc466cfd170d5`: token-pair and compact
normalisation now refuse the aliases with `RO014`, while correctly typed
bounded descriptors remain admissible. The red-first guard failed for all
nine aliases on the unfixed parent and passes on the fixed tree.

Finding count: 1. The mechanism was reproduced twice against signed head
`06787433ebef83be947bb06e36718422a04f9625`: once with a target-rooted
validator probe and once through the focused red-first unittest guard. The
exact source-owned Elenchus command
`python3 tests/emit_run_observation_report.py {report}` ran against signed fix
`69d28ba2f253b23f58e28abae64fc466cfd170d5` with format
`unittest-json-v1` and `.elenchus/run-observation.json`; verdict `guarded`.
The detached parent reports an assertion failure and the fixed report is
complete. Another independent round is required.

### Risk coverage

| risk id | evidence checked | disposition |
| --- | --- | --- |
| `carryover-chain-gap` | Three packet identities, digests, source runs and preserved refs remain exact in the cumulative fixture; 36 original findings and archived receipt boundaries pass. | clean on the fixed tree |
| `prior-art-drift` | The result remains one cumulative 37-path chain above `367e9662384bb29ea94576d270ab86744f3326a2`; history was not promoted into current evidence. | clean on the fixed tree |
| `delegated-path-resolution` | Reproduction, reports and all writes used canonical absolute paths below the run worktree; no accepted output used `/tmp`. | clean on the fixed tree |
| `origin-checkout-drift` | Before and after write batches, the protected checkout had exactly its five recorded paths; no image content was read, staged, removed or changed. | clean on the fixed tree |
| `gate-command-arity` | Reporter, valid and invalid CLIs, Promise commands, lints, current Horos and obsolete Horos used their receipted shapes and actual exits. | clean on the fixed tree |
| `current-main-loss` | Fiat 5.12.1, Elenchus 1.2.0, Wave Atlas and unrelated base work remain; ADR-014 is distinct and the observation decision is ADR-015. | clean on the fixed tree |
| `carryover-map-gap` | The map binds 36 original findings, four carried guards, three current repairs, one reporter repair and 19 audit findings through round 7 to current guards and eight families. | fixed in this round; another round required |
| `schema-runtime-drift` | Closed fields, enums, patterns, civil times, path rules, limits and optional facts agree; the differential matrix runs 309 cases. | clean on the fixed tree |
| `wrong-kind-crash` | The recursive matrix mutates all structural value positions in four valid flows and reports 365 cases, zero crashes and zero unexpected clean results. | clean on the fixed tree |
| `lifecycle-reference-gap` | Nine generated order, capability, retry, refusal, inferred-selector, handoff, evidence and terminal cases pass. | clean on the fixed tree |
| `input-replacement` | Growth, FIFO, same-size rewrite, named swap, ancestor escape and final bounded reread remain guarded in eight cases. | clean on the fixed tree |
| `reporter-replacement` | Named-target swap and same-inode post-`fsync` rewrite guards pass; the source reporter emits one fresh confined report. | clean on the fixed tree |
| `recorded-path-unicode` | NFC, scalar validity, `Cc`, `Cf`, `Cs`, portable syntax, byte ceilings and numeric or superscript device aliases agree in runtime, schema, prose and 33 cases. | clean on the fixed tree |
| `name-normalisation-gap` | Separated, camel, Pascal and compact execution, source and trace aliases now refuse; typed descriptors retain their value checks. The generated matrix runs 369 cases. | fixed in this round; another round required |
| `diagnostic-injection` | Text and JSON derive from one finding model; newly refused aliases use fixed pointer segments and are not echoed. | clean on the fixed tree |
| `context-binding-gap` | The 17-case family preserves issue or topic, step, role, selected skill and promise, paired Git identities, refusal promise and handoff producer; ADR identities remain distinct. | clean on the fixed tree |
| `evidence-promotion` | Evidence ids, subjects, scopes, time domains, classes, source events, handoff carriage, optional usage and terminal outcomes retain exact backward bindings. | clean on the fixed tree |
| `unbounded-input` | File, line, event, nesting, number, string, key, collection and path ceilings refuse before unbounded work. | clean on the fixed tree |
| `sensitive-payload` | Raw execution, source and trace family variants now join prior directives, rules, turns, utterances, artifacts and cognition families without echo. | fixed in this round; another round required |
| `optional-telemetry` | Host, model and token facts remain optional, source-bound and exclusive with same-event unknowns; explicit estimate families and wrong kinds refuse. | clean on the fixed tree |
| `partial-or-stale-record` | Malformed tails, lifecycle halves, concurrent input mutation, report replacement and stale identity refuse without fallback, repair or stability loops. | clean on the fixed tree |
| `elenchus-report-drift` | Exact source command, format and report path produced a guarded detached-parent comparison for signed fix `69d28ba…`; the fixed report is complete. | fixed and guarded; another round required |
| `closure-overclaim` | This round found one defect. No controller receipt, push, pull request, issue mutation, merge or closure action occurred. | another independent round is required |

### Current gate evidence

Focused and inoculation tests pass 70/70. The cumulative inoculation reports
1,181 cases: 36 carryover-map, 4 fixed-round-1-map, 3 current-repair-map, 1
reporter-lead-map, 3 audit-round-1-map, 4 audit-round-2-map, 2
audit-round-3-map, 3 audit-round-4-map, 4 audit-round-5-map, 2
audit-round-6-map, 1 audit-round-7-map, 309 schema-runtime, 365
recursive-wrong-kind, 9 lifecycle-reference, 8 file-replacement, 33
path-representation, 369 normalized-field-name, 8 report-parity-no-echo and
17 work-repository-context cases. It reports zero crashes and zero unexpected
clean results. Root tests pass 189/189.

The source-owned reporter runs 70 tests and emits one complete
`elenchus.unittest.v1` report with no failures, errors, skips, expected
failures or unexpected successes. Elenchus reports `guarded` because the
unfixed parent report contains assertion failures.

All four valid CLIs exit `0`. The five required invalid fixtures exit `1` and
emit `RO009`, `RO013`, `RO008`, `RO012` and `RO011`. Promise sync writes zero
files, its check reports 14 identical copies and coverage reports 68/68.
Phylax, Ephoros, Hypomnema, both Protasis modes, Imprimatur and each separate
Brevitas command exit `0`. Current Horos and `git diff --check` exit `0`;
obsolete Horos exits `2` as its negative specimen.

Python syntax, schema, coverage record, cumulative map and all 34 tracked
JSONL objects parse. The receipted study and runbook remain byte-identical to
their published copies. The run-to-current set remains at the declared
37-path surface and contains no image. The protected origin retains exactly
its five recorded paths.

### Leads not pursued

Capture, redaction and persistence remain in #435. Fiat receipt binding
remains in #436, and cross-run diagnosis remains in #449. The schema remains
a source contract rather than an executed dependency. Field-name checks cannot
establish the meaning of an innocently named scalar, and the final bounded
reread cannot prevent a writer changing a file after observation ends.

Unicode scalar noncharacters and non-`Cf` default-ignorable marks remain
inside the declared scalar and NFC path language. Sequence remains
authoritative over wall-clock order; retries are scheduled rather than a full
attempt chain. The record allows correlation ids to join paths. Evidence may
be narrower than the opening subject. These declared boundaries did not
produce another in-scope finding.

This round makes no claim of capture completeness, external truth, cause,
model quality, delivery correctness, deployment readiness, security or
mutation authority. Any later `434-CARRYOVER-4.md` or successor must remain
one self-contained aggregate of every pass if a restart is required. No
partial or intermediate reconstruction is an acceptance tree.
## Issue 434 carryover 5, step 1, round 1 -- 2026-08-23

Severity: high. The required Brevitas gate failed on the reconstructed audit record.
Location: `audit/AUDIT.md`.
Mechanism: 198 historical tables had fewer than three rows or three columns; the linter rejects each structure.
Impact: the documented fixed-tree gate matrix was not clean, so no audit closure was available.
Fix: `19156949f2810096ddaa85954be9e5c638edd823` converts each table to a lossless key/value record and retains every header and cell.

### Reproduction and repair

- Parent: `35c118df6354cc9d3be02e1712b01c76477029e7`.
- Red-first command: `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py audit/AUDIT.md` exited `1` twice with byte-identical 205-line diagnostics.
- Causal repair: the audit archive now represents every short historical table as a record. The gate exits `0` on `19156949f2810096ddaa85954be9e5c638edd823`.
- Guard: this document-only repair changes no test file. The twice-red Brevitas command is the reproducible guard; the source-owned Elenchus comparison reports `unguarded` for that reason.

### Fixed-tree evidence

- Full union: `37/37` tracked paths and `61/61` unique manifest rows across the eight mandatory families.
- Focused plus Promise tests: `142/142` passed. The inoculation matrix reports `1,258` cases, `0` crashes, and `0` unexpected clean results.
- Root suite: `190/190` passed. The four valid CLI fixtures exit `0`; the five invalid fixtures exit `1`.
- Promise sync, check, and coverage are clean. Phylax, Ephoros, Hypomnema, current Horos, Imprimatur, Brevitas, and `git diff --check` exit `0`.
- Solidity stays waived because the fixed tree changes Python, JSON, JSONL, and Markdown only.

### Risk dispositions

- `carryover-union-gap`: clean; the complete map is unique and current.
- `partial-tree-evidence`: clean; this audit began after the one-tree completion check.
- `coverage-contract-gap`: clean; `PromiseCoverageTests.test_run_observation_coverage_binds_the_exact_release_surface` passed.
- `schema-runtime-drift`, `wrong-kind-crash`, and `lifecycle-reference-gap`: clean under focused and inoculation evidence.
- `file-replacement`, `path-representation`, `metadata-redaction-gap`, and `diagnostic-echo`: clean under focused and inoculation evidence.
- `context-binding-gap`, `origin-checkout-drift`, `absolute-write-boundary`, and `gate-command-arity`: clean on the named worktree and fixed-tree gates.
- `closure-overclaim`: open; this round found and repaired one defect, so another independent Warden round is required.

Leads not pursued: capture, redaction, persistence, Fiat receipt binding, and cross-run diagnosis remain assigned to their separate issues. The record makes no claim about capture completeness, external truth, cause, model quality, delivery correctness, deployment readiness, security, or mutation authority.

## Issue 434 carryover 5, step 1, round 2 -- 2026-08-23

Severity: high. The source-owned Elenchus reporter omitted the exact-release coverage guard.
Location: `tests/emit_run_observation_report.py`.
Mechanism: its required surface and module list ran only the two run-observation
modules. The result therefore reported `70/70` while omitting
`tests.test_promise_machine_contract`, including
`PromiseCoverageTests.test_run_observation_coverage_binds_the_exact_release_surface`.
Impact: the reporter could present a green product guard without exercising
the CARRYOVER-5 coverage-contract repair that makes the aggregate tree whole.
Fix: add the Promise contract test path and module, and make the reporter
surface assertion live in the already-reported run-observation suite. Update
the bound test-file digest after adding that guard.

### Reproduction and repair

- Parent: `1dfdf23dd5ea22a4de6cf57035e3388ea20e13dc`.
- Red-first command: `python3 -m unittest tests.test_promise_machine_contract.PromiseCoverageTests.test_run_observation_reporter_includes_the_exact_coverage_guard -v` exited `1` twice. Both runs identified the absent contract-test path.
- Causal repair: the reporter now requires and loads `tests.test_promise_machine_contract`; its fixed-tree result is `143/143`, including the 72 Promise tests and the 71 run-observation and inoculation tests.
- Guard: the same assertion was red above and is retained as `RunObservationRefusalTests.test_reporter_includes_the_exact_coverage_guard`, which passes on the fixed tree. The source-owned Elenchus comparison reports `passed`: its parent reporter predates the new test and cannot execute it. The two red-first runs remain the guard evidence. The C5 coverage digest now binds the changed run-observation test surface.

### Fixed-tree evidence

- Full union remains `37/37` tracked paths and `61/61` unique manifest rows across the eight mandatory families.
- Focused plus Promise tests and the source-owned reporter pass `143/143`. The inoculation matrix reports `1,258` cases, `0` crashes, and `0` unexpected clean results.
- Root suite, valid and invalid CLI fixture checks, Promise sync/check/coverage, Phylax, Ephoros, Hypomnema, Horos, per-file Imprimatur and Brevitas, and `git diff --check` exit `0`.
- Solidity stays waived because this tree changes Python, JSON, JSONL, and Markdown only.

### Risk dispositions

- `carryover-union-gap`: clean; the complete map is unique and current.
- `partial-tree-evidence`: clean; this round began from the C5 aggregate tree and no halted partial result was used.
- `coverage-contract-gap`: fixed; the exact release-surface guard is now inside the source-owned report.
- `schema-runtime-drift`, `wrong-kind-crash`, `lifecycle-reference-gap`, `file-replacement`, `path-representation`, `metadata-redaction-gap`, and `diagnostic-echo`: clean under focused and inoculation evidence.
- `context-binding-gap`, `origin-checkout-drift`, `absolute-write-boundary`, and `gate-command-arity`: clean on the named worktree and fixed-tree gates.
- `closure-overclaim`: open; this round repaired a finding, so a further independent Warden round remains required.

Leads not pursued: capture, redaction, persistence, Fiat receipt binding, and
cross-run diagnosis remain assigned to their separate issues. This record makes
no claim about capture completeness, external truth, cause, model quality,
delivery correctness, deployment readiness, security, or mutation authority.

## Issue 434 carryover 5, step 1, round 3 -- 2026-08-23

Independent Warden review of signed HEAD
`97f043fb3f794a6ec30dc9e9fd0d6a0c31f573b1` found no new product defect.
The review began only after the committed C5 aggregate tree was present: 37
tracked paths and the 61-entry map spanning all eight mandatory families.
The halted C4 36-path reconstruction and its outputs remain non-evidence.

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I434-C5-S1-R3-01 | high | `audit/AUDIT.md` | The first version of this record used a one-row, five-column findings table. | reproduced twice as B011 |
| I434-C5-S1-R3-01 | high | `audit/AUDIT.md` | Brevitas rejects that non-minimal table shape, blocking the required prose gate. | fixed in this audit record |
| I434-C5-S1-R3-01 | high | `audit/AUDIT.md` | The three-row record retains the finding, cause, and remediation without the prohibited short table. | fixed-tree gates pending |

Finding count: 1. The defect reproduced twice with
`python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py audit/AUDIT.md`.
This document-only signed repair changes no test file, and the exact
source-owned Elenchus command reports
`unguarded`; a further Warden round is required after signing the final audit
record.

### Independent risk coverage

| risk id | probe and evidence | disposition |
| --- | --- | --- |
| `carryover-union-gap` | Read C5 at SHA-256 `c00cbaf7a609c8b3b7ae930dc4836f17fc067eaa72785914c00b493a7abae517`; inspect the 37-path diff and cumulative 61-id bijection. | clean |
| `partial-tree-evidence` | Confirmed audit starts from the signed full union; no C4 partial output was used. | clean |
| `coverage-contract-gap` | Focused run executes `PromiseCoverageTests.test_run_observation_coverage_binds_the_exact_release_surface`; source reporter loads the Promise contract module. | clean |
| `schema-runtime-drift` | Schema/runtime differential inoculations report 309 cases with no crash or unexpected clean result. | clean |
| `wrong-kind-crash` | Recursive wrong-kind matrix reports 365 cases, zero crashes, and zero unexpected clean results. | clean |
| `lifecycle-reference-gap` | Focused lifecycle tests and nine generated lifecycle/reference cases pass. | clean |
| `file-replacement` | Reviewed input and report descriptor, reopen, identity, digest, confinement, FIFO, swap, and same-inode guards; eight replacement cases pass. | clean |
| `path-representation` | Reviewed portable-path, NFC, control, bidi, component, complete-byte, display, and representational-error guards; 33 path cases pass. | clean |
| `metadata-redaction-gap` | Normalised raw, hidden, actor, execution, source, instruction, and directive families report 384 refusal/descriptor cases with no unexpected clean result. | clean |
| `diagnostic-echo` | Text and JSON findings use one sorted model; the eight parity/no-echo cases and control-character probes pass. | clean |
| `context-binding-gap` | The 17-case work/repository context matrix covers issue/topic, role, skill, promise, paired Git identities, and ADR identity. | clean |
| `promise-copy-drift` | `sync --check`, `check`, and `coverage --check` report 14 identical copies and 68 selected coverage rows. | clean |
| `source-reporter-surface` | Source-owned reporter emits a complete `elenchus.unittest.v1` result for 143 tests; the detached-parent Elenchus command returns `passed`. | clean; no new fix claim |
| `gate-command-arity` | Four valid CLIs exit 0; five invalid CLIs exit 1; Phylax, Ephoros, Hypomnema, Horos, per-file Imprimatur, per-file Brevitas, syntax, and `git diff --check` are rerun after this record-form repair. | pending fixed-tree gates |
| `closure-overclaim` | This round found one documentation-gate defect; no receipt, push, pull request, issue action, merge, or integration occurred. | another independent round required |

### Current evidence

`python3 -m unittest tests.test_run_observation tests.test_run_observation_inoculation tests.test_promise_machine_contract -v` passed 143/143. Its inoculation summary reports 1,258 cases, zero crashes, and zero unexpected clean results. `python3 -m unittest discover -s tests` passed 191/191. The source-owned reporter passed 143/143 and its exact Elenchus command returned `passed`; that output is current-tree evidence, not a replacement for this independent Warden verdict.

The four valid JSONL fixtures exit 0. The five invalid fixtures exit 1. Promise copy, contract, and coverage checks are clean. Phylax, Ephoros, Hypomnema, Horos, individual Imprimatur and Brevitas gates, Python syntax, and `git diff --check` are rerun after the record-form repair. Solidity remains waived because this step alters only Python, JSON, JSONL, and Markdown.

Leads not pursued: capture, redaction, persistence, Fiat receipt binding, and
cross-run diagnosis remain in their separate issues. The final bounded reread
cannot stop a writer changing bytes after observation ends; the record neither
claims capture completeness nor external truth, cause, model quality, delivery
correctness, deployment readiness, security, or mutation authority.

## Issue 434 carryover 5, step 1, round 4 -- 2026-08-23

Finding ID: `I434-C5-S1-R4-01`.

Severity: high. The shipped observable-run-record runbook contradicted its
absolute-path write boundary.

Location: `docs/promise-machine/run-observation-runbook.md`.

Mechanism: the demonstration passed the reporter and Elenchus a relative
`.elenchus/run-observation.json` path while later prose required every report
path to be canonical and absolute. The same prose named a prior C4 worktree,
not the worktree that executed the command. A caller could therefore write the
report below an unintended current directory, or follow stale instructions to
the wrong run tree.

Impact: the runbook could not establish the report-output boundary it claimed,
and its command was unsuitable as evidence for the current C5 tree.

Reproduction: on parent `5a1f31565f3db02c6882e7409b6ffcac5b7e7dde`, a
read-only documentation probe failed twice because the direct reporter command
and `--report-file` were relative and the obsolete worktree route remained.

Causal repair: define `REPORT_PATH` as
`$(pwd -P)/.elenchus/run-observation.json`, pass that absolute value to both
the reporter and Elenchus, and replace the historical root with a current-
worktree requirement. The retained
`RunObservationRefusalTests.test_runbook_resolves_the_report_target_to_the_current_worktree`
guard rejects the prior relative arguments and stale run root. The C5
controller runbook is already receipted and immutable; this record preserves
that historical mismatch rather than rewriting controller evidence.

Current report evidence: the source-owned reporter ran with the canonical
absolute C5 worktree target and emitted a complete `elenchus.unittest.v1`
result: 144 tests, zero failures, errors, or skips. The transient report was
removed immediately after the bounded check.

The full fixed-tree matrix follows this record. No controller receipt, push,
pull request, issue action, merge, or integration occurs in this round. A
further independent Warden round is required after its signed repair.

## Issue 434 carryover 5, step 1, round 5 -- 2026-08-23

Finding ID: `I434-C5-S1-R5-01`.

Severity: high. The public report demonstration passed an absolute path to an
Elenchus parameter that only accepts a relative descendant of Elenchus's
detached parent worktree.

Location: `docs/promise-machine/run-observation-runbook.md`.

Mechanism: `REPORT_PATH` correctly names a canonical absolute target for the
direct source-owned reporter in the current worktree. Reusing that value for
Elenchus `--report-file` is invalid: Elenchus constructs a separate detached
parent worktree, rejects absolute paths before the reporter starts, and then
replaces `{report}` with an absolute descendant of that detached tree. The
single public command therefore claimed an absolute write boundary while its
Elenchus invocation could only produce an inconclusive result.

Impact: a reader following the public demonstration could not obtain the
recorded Elenchus evidence. Treating the command's zero process exit as green
would hide Elenchus's explicit `inconclusive` verdict.

Reproduction: on signed parent `d148adcc353fcab50737bf0748ed4d0d1048a687`,
the documented command with absolute `--report-file "$REPORT_PATH"` was run
twice. Each returned `inconclusive` with `the report path must be a relative
worktree descendant`; neither invocation created the named current-worktree
report.

Causal repair: signed commit `4c0dff1b0b5d93126f01d905d4273a4749eee0bc`
keeps the direct reporter target absolute and changes only the Elenchus
declaration to `.elenchus/run-observation.json`. The runbook explains that
Elenchus substitutes `{report}` with a canonical absolute descendant of its
detached parent before invoking the source-owned reporter. It also records
that the current-worktree `REPORT_PATH` must never be passed to
`--report-file`.

Guard: `RunObservationRefusalTests.test_runbook_separates_direct_and_elenchus_report_targets`
was red twice before the documentation repair and passes on the fixed tree.
The coverage binding now names the replacement selector and its current
SHA-256. Elenchus on the signed repair reports `guarded`: 144 executed tests,
one parent assertion failure, zero infrastructure errors and zero skips. That
is a real red-to-green result, not an asserted clean classification.

### Fixed-tree evidence

- The one-tree union remains exactly 37 tracked paths and 61 unique manifest
  ids across all eight mandatory families.
- Focused plus Promise tests pass 144/144. The inoculation summary records
  1,258 cases, zero crashes and zero unexpected clean results.
- The root suite passes 192/192. All four valid JSONL fixtures are clean and
  all five invalid fixtures exit 1.
- The direct source-owned reporter writes to the canonical absolute C5
  worktree target and passes 144/144 with zero failures, errors and skips.
  Its transient report was removed after the bounded read.
- Promise copy, contract and coverage checks are clean: 14 identical copies
  and 68 selected coverage rows. Phylax, Ephoros, Hypomnema, Imprimatur,
  Brevitas, Horos, Python syntax and `git diff --check` exit 0.

### Risk dispositions

- `carryover-union-gap` and `partial-tree-evidence`: clean; this review used
  the 61-id, 37-path committed tree and no C4 partial output.
- `coverage-contract-gap`: clean; the exact release-surface binding carries
  the renamed report-target guard and its current digest.
- `absolute-write-boundary` and `gate-command-arity`: fixed; direct reporter
  and Elenchus now receive the different path forms their own contracts need.
- `source-reporter-surface`: fixed and guarded; the detached-parent reporter
  result is explicitly `guarded`, not silently upgraded to clean.
- `closure-overclaim`: open; this round repaired one material finding, so an
  additional independent Warden round remains necessary.

Leads not pursued: capture, redaction, persistence, Fiat receipt binding, and
cross-run diagnosis remain in their separate issues. This record makes no
claim about capture completeness, external truth, cause, model quality,
delivery correctness, deployment readiness, security, or mutation authority.

## Issue 434 carryover 5, step 1, round 6 -- 2026-08-23

Independent Warden review of signed HEAD
`f9d398b65a0c062366538d0452e5c0efa0e15e39` found no new product defect.
The review began from the signed C5 aggregate tree, not the halted C4 partial
reconstruction. The C4 partial output remains non-evidence.

### Findings

Finding count: 0. The reviewed repair is
`4c0dff1b0b5d93126f01d905d4273a4749eee0bc` and was locally
signature-verified before this verdict. This record is signed after its gates
pass.

### Independent risk coverage

| risk id | probe and evidence | disposition |
| --- | --- | --- |
| `carryover-union-gap` | Compared the signed aggregate diff with the C5 61-id, eight-family manifest. | clean |
| `partial-tree-evidence` | Confirmed this round started after the complete signed aggregate tree and did not use the halted 36-path C4 output. | clean |
| `coverage-contract-gap` | The direct reporter loaded `tests.test_promise_machine_contract` and ran 144/144 tests. | clean |
| `schema-runtime-drift` | Reviewed the retained schema/runtime differential coverage and the 1,258-case inoculation summary. | clean |
| `wrong-kind-crash` | Reviewed the recursive wrong-kind guard and its zero-crash result. | clean |
| `lifecycle-reference-gap` | Reviewed the lifecycle/reference guards and generated cases. | clean |
| `file-replacement` | Reviewed descriptor, reopen, identity, FIFO, target-swap, and same-inode guards. | clean |
| `path-representation` | Reviewed portable-path, NFC, control, bidi, component, byte, and display guards. | clean |
| `metadata-redaction-gap` | Reviewed raw, hidden, actor, execution, source, instruction, and directive refusal families. | clean |
| `diagnostic-echo` | Reviewed the shared text/JSON finding model and parity/no-echo guards. | clean |
| `context-binding-gap` | Reviewed issue, topic, role, skill, promise, Git identity, and ADR context guards. | clean |
| `promise-copy-drift` | Reviewed the current Promise copy and coverage bindings. | clean |
| `source-reporter-dual-path` | Direct reporter accepted only the canonical absolute C5 target and passed 144/144. Absolute, parent-escape, and lexical-dot-dot escape candidates each refused before write. The causal-repair Elenchus replay accepted `.elenchus/run-observation.json` as its relative declaration, substituted an absolute detached-worktree target, and returned `guarded` with 144 executed tests, one parent assertion failure, zero errors, and zero skips. | clean |
| `gate-command-arity` | Re-read the published command forms against both parser contracts: the emitter accepts its absolute target and Elenchus requires its relative descendant declaration. | clean |
| `closure-overclaim` | No product finding, receipt, push, pull request, issue action, merge, or integration occurred in this round. This is an independent audit verdict only. | clean |

### Current evidence

The direct source-owned command created one fresh report at
`$(pwd -P)/.elenchus/warden-r6-direct.json`; it recorded complete
`elenchus.unittest.v1` output for 144 tests with zero failures, errors, skips,
expected failures, or unexpected successes. The exact transient report was
removed after its bounded read. `/tmp/warden-r6-escape.json`,
`../warden-r6-escape.json`, and
`./.elenchus/../warden-r6-escape.json` each exited 2 before writing.

The audited causal repair's exact Elenchus invocation used
`--report-file .elenchus/run-observation.json`; it returned `guarded`, rather
than a process-exit surrogate. Its report names 144 executed tests, one parent
assertion failure, zero infrastructure errors, and zero skips. The checked
documentation says explicitly that the reporter receives a canonical absolute
target only after Elenchus has substituted its detached-worktree descendant.

Leads not pursued: capture, redaction, persistence, Fiat receipt binding, and
cross-run diagnosis remain assigned to their separate issues. This record does
not claim capture completeness, external truth, cause, model quality, delivery
correctness, deployment readiness, security, or mutation authority.
## Step 1, round 1 -- 2026-08-24

Covered: `evidence-loss`, `false-semantic-proof`, `final-byte-drift`,
`queue-format-drift`, `github-bypass`, `history-rewrite`, `session-leak`,
`open-issue-collision`, and `frontier-drift` reviewed; `pr-509-overlap` and
`task-comment-mismatch` not applicable until Step 2.

Not checked: Solidity security suite (waived); cross-model corpus execution;
GitHub signature state and publication state.

Evidence: signed commit `96acb17c36601532ee6d3ad45f5fc8f369332e23` verified
locally with both provenance trailers once; 11 Sapheneia, 105 focused, and 195
root tests passed; Promise Machine, Protasis, Horos, Imprimatur, Brevitas,
Phylax, Ephoros, Hypomnema, and diff checks passed.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Step 2 controller behaviour, PR #509 combined-tree
reconciliation, and remote task-comment byte readback.

## Step 2, round 1 -- 2026-08-24

Finding count: 1. Audit filter declaration:
`--audit-filter sapheneia:sapheneia`. Security suite: waived because the
repository framework change contains no Solidity.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `docs/durable-agent-prose-gates/runbook.md:127` | PR #518 advanced `origin/main` from `dd23413ef6e9021bd80b930ad57e1766bf166f0b` to `191f2ce1d60abb8068887095a8c39fb4341f0be6` at 2026-08-24T01:03:30+01:00, before signed Step 2 commit `6dcfb93374ab825817fa2bcd5f832fe9aea22397` at 2026-08-24T01:27:35+01:00. The step remains on the old base although its exit requires reconciliation when main advances first. A combined-tree probe conflicts at `.horos/boundary.json`, so current checks do not prove the post-advance delivery tree. | open; reconcile the base, regenerate Horos, and rerun the gates |

Risk coverage: `evidence-loss`, `false-semantic-proof`, `final-byte-drift`,
`queue-format-drift`, `github-bypass`, `history-rewrite`, `session-leak`,
`open-issue-collision`, `frontier-drift`, and `task-comment-mismatch` are clean
within the signed range. `pr-509-overlap` remains external: merge commit
`c04718fc700b09bf2d6c089f3ac5a8bf05a5738c` is not on `main`, and its branch
overlaps 15 Step 2 paths, including the controller, Warden contract, audit-loop
reference, evolution ledger, manifests, and tests.

Evidence: signed range
`6b91fcc61feabb8504b46006d65197bc731b0845..6dcfb93374ab825817fa2bcd5f832fe9aea22397`
contains one locally verified Shoggoth commit with both provenance trailers
once. The controller packet names round 1, state digest
`3c667578d6dddb2ee2eb4584d3cea35968d5d8eeb311fb33264e2d9d835656c7`, study
digest `dd3f12d317e01271fdc5636d1c3eae2b1fe0b276a0ed784617f3655ad21bc4e0`,
runbook digest `700e59cdca0b67d41b195c1223d15152477213d85bc739aa771bf89d838fe9df`,
and the exact audit-filter obligation. The dated amendment preserves frontier
revision `state-shape-validation`, digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, status
`open`, and issue #363 as the Next Fiat job while advancing only the generation.

Checks: Phylax exit 0; Ephoros exit 0; Hypomnema exit 0. Fiat focused tests
passed 327/327; Hexaemeron passed 881/881; focused root passed 106/106; root
passed 196/196; Sapheneia passed 11/11. Promise Machine, Protasis, Horos,
Imprimatur, Brevitas, and `git diff --check` passed.

Unknowns: the reconciled PR #518 tree and any future PR #509 combined tree were
not tested. GitHub signature state, issue-comment publication, remote byte
readback, and model-level semantic correctness were not established.

Sapheneia comparison: the compact candidate retains the finding, severity,
status, exact locations, SHAs, dates, counts, digests, lint exits, waiver,
declaration, qualifications, unknowns, negative results, and unpursued leads.
No protected item changed or disappeared.

Leads not pursued: reconcile PR #509 only if its integration branch approaches
`main`; exercise the task-issue comment sequence when a run has a bound issue;
verify remote signatures only after publication.

## Step 2, round 2 -- 2026-08-24

Finding count: 0. Audit filter declaration:
`--audit-filter sapheneia:sapheneia`. Security suite: waived because the
repository framework change contains no Solidity.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Prior finding `S2-R1-01` is fixed at the instruction layer by signed commit
`2290b6851c67423867f26e72c25fd57ef5776675`. Receipted amendment SHA-256
`9d347b7cb89e6971e019cae3c6f5e8362e6bdeb39b0e8eea49532b378f85a989`
supersedes the runbook's rebase wording with Fiat's canonical rule: do not
rewrite the signed stack; if the integration pull request conflicts, merge the
exact remote base tip once through a signed `sync-run` after the final step
merge. PR #518's actual main merge, the `.horos/boundary.json` conflict,
combined-tree regeneration, and all post-sync checks remain mandatory
integrate-phase work. They are not claimed complete here.

Elenchus verdict: `unguarded`. The exact fixed commit changed no test files, so
Elenchus returned `the commit changed no test files`; no process exit or clean
fixed-tree suite was substituted for that verdict.

Risk coverage: `evidence-loss`, `false-semantic-proof`, `final-byte-drift`,
`queue-format-drift`, `github-bypass`, `history-rewrite`, `session-leak`,
`open-issue-collision`, `frontier-drift`, and `task-comment-mismatch` are
clean for the fixes range. `pr-509-overlap` remains external and unresolved:
its non-main branch still overlaps the controller, Warden contract, audit-loop
reference, evolution ledger, manifests, and tests.

Evidence: fixes range
`6dcfb93374ab825817fa2bcd5f832fe9aea22397..2290b6851c67423867f26e72c25fd57ef5776675`
contains one locally verified Shoggoth commit with both provenance trailers
once. The canonical rule is at
`plugins/hexaemeron/skills/fiat/SKILL.md:443-446` and
`plugins/hexaemeron/skills/fiat/references/push-discipline.md:180-189`.
The controller packet names round 2, study digest
`cdb4c122872db7e291bc4057531e198a7faa32557ae87f3eb2c909a221106f19`,
state digest `372160e4aa61cb90991bbc4e59e8f05b2f99b1695315b18402da5be98a9fa949`,
and the exact audit-filter obligation.

Checks: Phylax exit 0; Ephoros exit 0; Hypomnema exit 0. Hexaemeron passed
881/881; root passed 196/196; Sapheneia passed 11/11. Promise Machine,
Protasis, Horos, controller verification, and `git diff --check` passed.
Round-1 Imprimatur and Brevitas evidence covered every changed target required
by the runbook. This round does not claim that this one-row audit candidate is
Brevitas-clean: Fiat's required five-column audit table conflicts with that
structural rule.

Unknowns: no `sync-run`, Horos regeneration on the combined tree, remote
signature check, task-issue comment publication, remote byte readback, PR #509
reconciliation, or model-level semantic proof occurred in this round.

Sapheneia comparison: the compact candidate retains the zero finding count,
prior finding id and fix status, exact SHAs, amendment and state digests,
locations, verdict and cause, lint exits, test counts, waiver, declaration,
qualifications, unknowns, negative evidence, and unpursued leads. The table
shape and every protected token match the source inventory.

Leads not pursued: execute and receipt the signed `sync-run` only at the
canonical integrate transition if the integration pull request conflicts;
reconcile PR #509 only if it approaches `main`; exercise the task-issue comment
sequence only for a bound issue.
## Fiat merged attribution, step 1, round 1 -- 2026-08-24

The Pashov pair did not run. The `security_suite` receipt records a waiver:
this step commits three Markdown documents and changes no Solidity. The three
bundled lints are the mechanical part and all exited 0 against the changed
paths. The diff was then read against every id in the study's risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | `plugins/hexaemeron/docs/fiat-merged-attribution/study.md` | The prior-art paragraph quotes a contributor's work address where a description would carry the same point. A document whose subject is not publishing addresses reads better without one. | accepted, not fixed |
| S1-R1-02 | low | `docs/decisions/ADR-017-bind-merged-authorship-to-the-integration-receipt.md` | The Decision section describes the receipt and the integration check in the present tense, one step before either exists. A reader landing on the record at this step would read it as a description of the shipped controller. | fixed in this round: Status now names the steps that implement it and states that v5.13.1 records no attribution |

S1-R1-01 is accepted rather than fixed. This step's exit requires the committed
study to be byte-identical to the receipted artefact, and a Protasis amendment
appends rather than edits, so the prefix cannot be corrected without abandoning
a receipted artefact. The address is a company-domain work address already
published by the organisation in issue 515 and in the public default-branch
commit history, and the study's own "Never" entry governs the attribution
record the controller persists, which stores a digest and never an address. The
wording is carried forward for the next study over this target.

Risk register disposition. `attribution-private-email` is the id S1-R1-01 sits
under, dispositioned above; nothing in this step writes state.
`attribution-overclaim` is the id S1-R1-02 sits under and is closed by the
Status fix. `attribution-null-login`, `attribution-unbounded-field`,
`attribution-coauthor-parse`, `attribution-ancestor-check`,
`attribution-rewritten-merge` and `attribution-state-shape` are not applicable
to a step that ships no code.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
874/874. Protasis both modes, Imprimatur, Brevitas and the Horos scan exit 0 on
the changed paths. The implementation commit
`8ed925488c888cce3633226356e6cd1e0d24d741` has a good local signature and
exactly one copy of each required trailer.

Leads not pursued: none beyond the accepted S1-R1-01.

## Fiat merged attribution, step 1, round 2 -- 2026-08-24

Against the tree with round 1's fix applied. Zero findings. Status: clean.

The Pashov pair did not run, for the reason the waiver records. The three
bundled lints exited 0 again over the same changed paths. The re-read confirmed
S1-R1-02 closed: ADR-017's Status now states that the decision is recorded
before the code, names steps 2 and 3 as the ones that carry it, and says
plainly that v5.13.1 records no attribution and checks nothing at the merge.
The two committed copies remain byte-identical to the receipted artefacts.

Risk register disposition. `attribution-overclaim` is clean on the fixed tree.
`attribution-private-email` carries the accepted S1-R1-01 and is otherwise
clean: no state is written by this step. The remaining six ids stay not
applicable to a step that ships no code.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
874/874. The fixes commit `64ea0e7e599048eac0988d46f38ecadc2b236bdd` has a good
local signature and exactly one copy of each required trailer.

Leads not pursued: none beyond the accepted S1-R1-01, which is carried forward.

## Fiat merged attribution, step 2, round 1 -- 2026-08-24

The Pashov pair did not run, for the reason the waiver records: this step
changes a Python controller and its tests. The three bundled lints exited 0.
The review then read the diff against every id in the study's risk register,
and both findings came out of that read rather than out of a lint.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `checked_login` treated an `author` object carrying no usable login as an unlinked commit and recorded `null`. GitHub spells "matched to no account" as a literal `null`, so an object without a login is a payload nobody predicted, and reading it as unlinked lets a shape the reader does not understand become a claim about a person. | fixed in this round: only a literal `null` records `null`; an object must carry a login string |
| S2-R1-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `verify_github_commits` was implemented over the attribution reader, so the identity checks silently gated the merge-step, integration and run-sync receipts as well. A merge commit whose author name exceeded the cap, or whose message was absent, would have refused a receipt that has nothing to do with attribution. The step widened a gate it did not declare. | fixed in this round: verification keeps its own reader and fails only on GitHub's verification result |

Both fixes are guarded. Against the implementation commit
`afd1c92a00b289538af5851e74e1307c046ab914` the two guards report
`FAILED (failures=1, errors=2)`; against the fixed tree they pass. The
`attribution-null-account-object` case moved out of the "records null" test and
into the negative matrix, and
`test_verification_alone_does_not_apply_the_attribution_checks` is new.

Risk register disposition. `attribution-null-login` carried S2-R1-01 and is
closed by the fix: a literal `null` records `null`, an unlinked author keeps its
digest, and the refusal names the commit. `attribution-unbounded-field` is
clean: the account login is matched against a closed expression, the name and
address are type-checked and capped at 256 and 320 bytes, and the co-author
count is capped at 32. `attribution-coauthor-parse` is clean: the trailer is
parsed with the same expression the local range gate uses, so the two cannot
disagree, and a host identity in a trailer refuses on either view.
`attribution-private-email` is clean: the recorded container holds a login, a
display name and a digest, and the receipt and ledger tests both assert that no
`@` appears in the recorded bytes. `attribution-state-shape` is clean: the new
container sits inside `steps[i].receipts`, which the version-1 spine already
validates, so `load_state` needed no change. `attribution-ancestor-check` and
`attribution-rewritten-merge` belong to step 3. `attribution-overclaim` is not
applicable: this step ships no prose.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
882/882 with 8 new tests. `python3 scripts/promise_machine.py check` reports 14
plugins and 14 copies clean after the three `fiat-*` runtime digests were
refreshed to `64a9d2b7e16235e6503eac3b496bf281b2d9259e90a0272679175e2569b53f4a`.
The Elenchus report at `tmp/elenchus/step-2.json` records
`elenchus.unittest.v1`, complete, 882 tests, 0 failures.

Leads not pursued, carried to step 3: `done_merge_step`'s repair path recomputes
the verified range and the GitHub verification for a moved branch head but does
not recompute the attribution container, so a repaired push receipt can hold
attribution for commits that are no longer the branch tip. Step 3 owns the
merged-state binding and must not read a stale container as current. Logged
here rather than fixed, because the consumer does not exist yet and a guard
written against no consumer guards nothing.

## Fiat merged attribution, step 2, round 2 -- 2026-08-24

Against the tree with round 1's fixes applied. Zero findings. Status: clean.

The three bundled lints exited 0 again over the controller and its tests. The
re-read confirmed both fixes and found no regression introduced by either.
`checked_login` now refuses an account object without a login string and still
records a literal `null` as `null` with the author's digest intact.
`verify_github_commits` has its own loop over `github_commit_payload` and
`require_github_verified`, so an oversized author name or an absent message on
a merge commit no longer refuses a verification receipt, while the attribution
reader still refuses both. The duplication is two lines of loop and is
documented in the docstring as deliberate, because the alternative is one
reader failing for two unrelated reasons.

Risk register disposition. All eight ids read clean on the fixed tree, with
`attribution-ancestor-check`, `attribution-rewritten-merge` still belonging to
step 3 and `attribution-overclaim` still not applicable to a step shipping no
prose. `attribution-null-login` is closed on the fixed tree.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
882/882. Promise Machine reports 14 plugins and 14 copies clean.
`hexctl verify` reports 15 ledger entries, chain intact, state consistent. The
fixes commit `3800bd437524e1ec0db27e601f904932b1d42ce2` has a good local
signature and exactly one copy of each required trailer.

Leads not pursued: the stale-attribution repair path stays carried to step 3,
as round 1 recorded.

## Fiat merged attribution, step 3, round 1 -- 2026-08-24

The Pashov pair did not run, for the reason the waiver records. The three
bundled lints exited 0. The review read the diff against every id in the
study's risk register, and both findings came out of that read.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The rewritten-merge fallback inspected only the base merge. A step squash-merged into the run branch leaves its commits unreachable while its identity survives on that step's own merge commit, which is itself an ancestor of the base merge. The check would have refused an identity that did reach the base, and the refusal would have pointed at the wrong merge. | fixed in this round: the step's recorded merge is tried first and the base merge second, and a recorded merge counts only while it is reachable from the base merge |
| S3-R1-02 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `recorded_run_attribution` chose between the repaired container and the push container by truthiness, so an empty repaired container would have been read as absent and the stale push attribution used in its place. Not reachable today, because a repaired range is never empty. | fixed in this round: presence decides, and a direct guard pins it |

Three guards. `test_a_step_merge_is_tried_before_the_base_merge` and
`test_a_step_merge_that_never_reached_the_base_is_not_a_carrier` cover
S3-R1-01, and `test_an_empty_repaired_container_is_current_not_absent` covers
S3-R1-02. Against the implementation commit
`353adec7497a4effcff04ea90817b6ce511fd782` the three report
`FAILED (failures=1, errors=2)`; against the fixed tree they pass. The fake
git's ancestry answer was narrowed to a named set of commits, because a mode
that answered "not an ancestor" to every question could not tell a detached
step commit from a detached step merge, and the first version of the test
passed for the wrong reason.

Risk register disposition. `attribution-rewritten-merge` carried S3-R1-01 and
is closed by the fix: a squash or rebase at either merge point now resolves
through the merge that actually carried the identity, and an identity no
recorded merge carries refuses the receipt by step, commit and account or
digest prefix. `attribution-ancestor-check` is clean: `commit_is_ancestor`
reads only exit 0 and 1 as an answer, refuses any other status, and runs
argv-only through `bounded_tool_status` with no shell. A regression covers the
unanswerable call. `attribution-private-email` is clean: the refusal names an
identity by login or by a twelve-character digest prefix, and a test asserts no
`@` reaches stderr. `attribution-null-login` is clean: an unlinked identity
resolves on its digest, which is the only comparison available for it and for a
co-author trailer. `attribution-unbounded-field` and
`attribution-coauthor-parse` are unchanged from step 2 and clean; the merge
commit's identity passes through the same checked reader.
`attribution-state-shape` is clean: the new receipt containers sit inside
`receipts` and `integrate`, both already validated by the version-1 spine.
`attribution-overclaim` is not applicable: this step ships no prose.

The step also closed the lead step 2 carried forward. The merge-time repair
path recomputes the attribution beside the verified range it already
recomputed, and a regression proves the integration check reads the refreshed
container rather than the head it replaced.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
893/893 with 11 new tests across steps 2 and 3. Promise Machine reports 14
plugins and 14 copies clean after the three `fiat-*` runtime digests were
refreshed to
`56d4862f47da60968f19586b042bf4948f12119ca691f42b3460c4672736374f`. The
Elenchus report at `tmp/elenchus/step-3.json` records `elenchus.unittest.v1`,
complete, 893 tests, 0 failures, 0 errors.

Leads not pursued: the live run is governed by the installed Fiat v5.13.1
controller, which cannot write or read either new container. Every claim above
rests on the checked-in controller under test, and step 4 owns the disposable
replay that exercises both gates end to end. Nothing here claims the installed
controller enforced a field it cannot parse.

## Fiat merged attribution, step 3, round 2 -- 2026-08-24

Against the tree with round 1's fixes applied. Zero findings. Status: clean.

The three bundled lints exited 0. The re-read followed the resolution order
through both fixes and found no regression.

Carrier order is the step's own merge then the base merge, deduplicated, and a
carrier not itself reachable from the base merge is skipped rather than
trusted. The recorded `carriers` map is keyed by SHA and filled in step order,
so a rerun over the same state records the same bytes. `identity_matches`
compares accounts when both sides have one and digests otherwise, which is the
only comparison available for a co-author trailer or an unlinked commit; two
addresses on one account still resolve to one contributor.

`github_repository` and every carrier read sit inside the branch that runs only
after an ancestry check has failed. A run whose commits all reached the base
intact therefore reads nothing extra and cannot be refused by an unexpected
identity shape on a merge commit.

Risk register disposition. All eight ids read clean on the fixed tree.
`attribution-rewritten-merge` and `attribution-ancestor-check` are closed by
this step. `attribution-overclaim` remains not applicable until step 4 ships
prose.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
893/893. Promise Machine reports 14 plugins and 14 copies clean. The fixes
commit `e04e799041b92be3c5f6ecd3f589acdb61973fff` has a good local signature
and exactly one copy of each required trailer.

This record was shaped by the bounded `sapheneia:sapheneia` durable-record
operation before append. The frozen inventory was compared item by item:
verdict, status, the three lint exits, both suite counts, the Promise Machine
counts, the fixes commit and its signature and trailer attribution, the four
risk ids and the eight-id total, the four named identifiers, every
qualification, and both unpursued leads all survive unchanged. Only connective
and process prose was compacted.

Leads not pursued: the installed-controller split stays as round 1 recorded it.
Step 4 owns the disposable replay that exercises both gates end to end.

## Fiat merged attribution, step 4, round 1 -- 2026-08-24

The Pashov pair did not run, for the reason the waiver records: this step ships
prose, metadata and a replay document. The three bundled lints exited 0. The
review compared every published sentence against what the controller does, and
read the replay document as a script a stranger runs in their own checkout.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | medium | `plugins/hexaemeron/docs/fiat-merged-attribution/proof.md` | The red-to-green replay overwrites the controller in the reader's working tree and restores it on the next statement. A failed assertion, an unreadable `git show`, or a killed process left the checkout holding an older controller with no warning. A document that tells a stranger to run it owns that outcome. | fixed in this round: the loop restores from `HEAD` in a `finally` block, both `git show` reads are asserted non-empty, and the restore was proved against a simulated interruption |
| S4-R1-02 | low | `plugins/hexaemeron/docs/fiat-merged-attribution/study.md` | The 2026-08-24 amendment states that step 4 regenerates `docs/pdf/how-to-help-shoggoth.pdf` with `scripts/build_contributor_guide.py`. Step 4 does not. That generator exists only on `main`, which this branch was cut before, and `reportlab` is absent locally while adding a dependency is an ask-first boundary in this study. The amendment put the work in the wrong place. | accepted, not fixed |

S4-R1-02 is accepted rather than fixed. The amendment is receipted and this
step's exit requires the committed study to match the receipted bytes, and a
Protasis amendment appends rather than edits, so a second amendment could
correct the placement but not the sentence. The guide gains a section and the
generated PDF is that section behind until the generator next runs. Recorded
here and carried forward in the run body.

`attribution-overclaim` review, sentence by sentence. The README says Fiat
stores the matched account and a digest for every commit it pushes, refuses to
record a run as integrated unless the base still carries each identity, and
records plainly when an address matches no account: all three hold. It names
the two GitHub-side conditions and claims nothing about the list appearing. The
contributor guide adds that a merge commit keeps the commits while a squash or
rebase merge does not, and that the merge itself then has to carry the name:
that matches the two mechanisms and the carrier order. Neither document claims
the run's own receipts carry attribution, which they do not, and the
`fiat-final-integration` promise boundary states that the result does not
establish that GitHub will resolve an identity or list a contributor.

Risk register disposition. `attribution-overclaim` is closed by the review
above and by the promise boundary. `attribution-private-email` is clean: no
address appears in the README, the guide, the ADR, the ledger row or the proof.
`attribution-null-login`, `attribution-unbounded-field`,
`attribution-coauthor-parse`, `attribution-ancestor-check`,
`attribution-rewritten-merge` and `attribution-state-shape` are unchanged by
this step and remain closed as steps 2 and 3 recorded them.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
893/893. Promise Machine reports 14 plugins and 14 copies clean. Imprimatur
scores 100.0 with zero defects on `README.md`,
`docs/how-to-help-shoggoth.md`, the ADR and the proof; Brevitas exits 0 on each.
The Horos scan leaves `.horos/boundary.json` at the one line this step's new
documents earned. The implementation commit
`7910706f4b7fc25309a974c46ea63ab324a54d27` has a good local signature and
exactly one copy of each required trailer.

Two facts about this step that are not findings. The `fiat-v5.14.1` row and
`docs/decisions/ADR-017-gate-durable-agent-prose.md` are carried onto this
branch verbatim from `origin/main` at `6c98a728a9f8ee25f4eed70b7032dc10f836eb17`,
because this branch was cut before that run landed and its published row links
to that file; without both, this branch's own ledger skips a generation and
H001 fails. And `tests/test_evolution_contract.py` pins the newest row's
evidence to one ADR, so every future generation row has to move that assertion.
That brittleness predates this run and is left as it was found.

Leads not pursued: the installed-controller split, recorded under step 2 round
1 and step 3 rounds 1 and 2, and the frontier gate arithmetic that refuses two
concurrent frontier runs on one skill. Both are carried forward in the run body.

This record was shaped by the bounded `sapheneia:sapheneia` durable-record
operation before append. The frozen inventory was compared item by item: both
findings with their ids, severities, files and statuses, the accepted
disposition and its reason, every sentence-by-sentence verdict, the eight risk
ids, the three lint exits, both suite counts, the Promise Machine counts, the
Imprimatur score, the two carried-verbatim artefacts with the exact base
commit, the implementation commit with its signature and trailer attribution,
and both unpursued leads all survive unchanged. Only connective and process
prose was compacted.

## Fiat merged attribution, step 4, round 2 -- 2026-08-24

Against the tree with round 1's fix applied. Zero findings. Status: clean.

The three bundled lints exited 0. The replay document's restore now runs in a
`finally` block and was proved against a simulated interruption, leaving the
controller byte-identical to `HEAD`. Both `git show` reads assert non-empty
output, so an unreadable commit fails loudly instead of writing an empty file
over the controller.

The committed study and runbook still match the receipted artefacts byte for
byte, including the 2026-08-24 amendment.

Risk register disposition. All eight ids read clean on the fixed tree.
`attribution-overclaim` stays closed on the published sentences reviewed in
round 1.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 192/192, Hexaemeron suite
893/893. Promise Machine reports 14 plugins and 14 copies clean. The fixes
commit `76e50de022d037c2b70edb84c27654d7c28bf239` has a good local signature
and exactly one copy of each required trailer.

Leads not pursued: the accepted S4-R1-02, the installed-controller split and
the frontier gate arithmetic, all carried forward in the run body.

This record was shaped by the bounded `sapheneia:sapheneia` durable-record
operation before append. The frozen inventory was compared item by item:
verdict, status, the three lint exits, both suite counts, the Promise Machine
counts, the byte-for-byte artefact claim, the eight risk ids, the fixes commit
with its signature and trailer attribution, and all three unpursued leads
survive unchanged. Only connective and process prose was compacted.

## Fiat frontier row attribution, step 1, round 1 -- 2026-08-24

The Pashov pair did not run, for the reason the waiver records: this step
changes a Python controller and its tests. The three bundled lints exited 0.
The review then read the diff against every id in the study's risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The integration receipt recorded `frontier_published_rows` as the base ledger's entire row set, which for this repository is twenty versions, under a field name that says the gate subtracted them. The runbook's exit says the receipt records the subtracted versions. A reader would have taken a twenty-entry list as twenty discounted rows. | fixed in this round: `frontier_subtracted_rows` records the intersection of the base set with the rows after the anchor, and the field is renamed to match |
| S1-R1-02 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The row slicing existed twice in effect: the gate sliced rows after the anchor to count them, and the receipt would have had to slice them again to say which were subtracted. Two copies of that rule drift, and a refusal would then count rows the receipt omitted. | fixed in this round: `frontier_rows_after_anchor` is shared by both, with a regression asserting they agree |

Both fixes are guarded. Against the implementation commit
`332c58e8b407d7bf527c7bb69ad58e6d8cc8c44a` the two new guards report
`FAILED (errors=2)`; against the fixed tree they pass.

Risk register disposition. `base-read-failure` is clean: the read goes through
`bounded_run` rather than `bounded_git`, so a blob it cannot fetch returns a
status this function handles instead of printing a refusal and exiting, and an
unfetchable, non-UTF-8 or malformed blob subtracts nothing and leaves the older
count. Three regressions cover an empty base, a non-SHA base and an
unreachable SHA, and one asserts the fallback still refuses the issue 466
topology. `foreign-row-overcount` is clean: only exact version labels present
in the base are subtracted, and a regression shows a duplicated label
subtracting both of its rows to `gained 0` rather than one of them.
`own-row-not-newest` is clean and covered by a regression whose topology puts a
published row after the run's own, which is the only arrangement where the
count passes and the newest-row rule has to fire. `two-own-rows` is clean: a run
appending two of its own rows is still refused, with and without an irrelevant
published set. `no-sync-unchanged` is clean: `done_integrate` consults the base
only when a sync receipt exists, so a run without one keeps today's arithmetic.
`bounded-git-read` is clean: argv-only, no shell, the existing output cap, and
the status distinguished from empty output.

One behaviour change is not a finding and is recorded here. On the legacy path
with no `version_at_init`, a ledger that has lost rows since `init` previously
reported a negative `gained` and now reports `0`. Both refuse; only the number
in the message differs. The append-only anchor check catches the same case
whenever `version_at_init` is recorded, which every current run records.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 196/196, Hexaemeron suite
912/912 with 12 new tests. Promise Machine reports 14 plugins and 14 copies
clean after the three `fiat-*` runtime digests were refreshed. The Elenchus
report at `tmp/elenchus/step-1.json` records `elenchus.unittest.v1`, complete,
909 tests, 0 failures, against the implementation commit.

Leads not pursued. This run drives the installed `fiat-v5.14.1` controller
while the repository holds `fiat-v5.15.1`, recorded in the `controller_version`
receipt, so its own receipts carry no attribution container and its own
integration will not exercise the field this step adds. A run under a
controller carrying `fiat-v5.16.1` is the first that can. Brevitas reports B010
and B001 against the one-step runbook, because Protasis fixes that artefact's
shape at one heading per step; Protasis owns the schema, so the runbook was not
padded to satisfy a budget written for prose answers.

This record was shaped by the bounded `sapheneia:sapheneia` durable-record
operation before append. The frozen inventory was compared item by item: both
findings with their ids, severities, files and statuses, the red-side result
against the exact implementation commit, all six risk ids with their
dispositions, the recorded behaviour change, the three lint exits, both suite
counts, the Promise Machine counts, the Elenchus report fields, and both
unpursued leads survive unchanged. Only connective and process prose was
compacted.

## Fiat frontier row attribution, step 1, round 2 -- 2026-08-24

Against the tree with round 1's fixes applied. Zero findings. Status: clean.

The three bundled lints exited 0. The re-read followed the shared slicing
through both callers. `frontier_rows_after_anchor` is the only place the anchor
rule lives, the gate counts what it returns, and `frontier_subtracted_rows`
intersects the same slice with the base set, so the refusal and the receipt
cannot name different rows. A regression asserts that agreement directly.

Risk register disposition. All six ids read clean on the fixed tree.
`base-read-failure` and `bounded-git-read` are unchanged by the fix, which
touched neither the read nor its fallback.

Gates: phylax 0, ephoros 0, hypomnema 0. Root suite 196/196, Hexaemeron suite
912/912. Promise Machine reports 14 plugins and 14 copies clean. The fixes
commit `37b6f941431452670faede130e32bef46af3fc49` has a good local signature
and exactly one copy of each required trailer.

Leads not pursued: the installed-controller split and the Brevitas budget on a
one-step runbook, both as round 1 recorded them.

This record was shaped by the bounded `sapheneia:sapheneia` durable-record
operation before append. The frozen inventory was compared item by item:
verdict, status, the three lint exits, both suite counts, the Promise Machine
counts, the six risk ids, the fixes commit with its signature and trailer
attribution, and both unpursued leads survive unchanged. Only connective and
process prose was compacted.
## Issue 435 CARRYOVER-12, step 1, round 1 -- 2026-08-24

### Verdict

Zero findings. The signed implementation under review is
`5d41815783e27beeae5dfa81cfdd0862f2e4f7d0`; its signature is good and its
required co-author and origin trailers each occur once. The tree is clean.

### Risk register

- `raw-descriptor`: raw prompt, command, header, and analysis probes become
  non-echoing gaps.
- `report-path`: writer-forgery and symlink-parent guards pass; absolute
  outside and lexical-escape targets refuse with exit 2.
- `receipt-drift`, `terminal-bytes`, and `authored-escape`: source/copy
  comparisons pass, tails are `2e 0a`, and authored bytes contain no `5c 6e`.
- `partial-tree`, `adr-allocation`, `coverage-drift`, `receipt-mutation`, and
  `base-divergence`: the 25-ID preflight, ADR checks, coverage bindings, source
  digests, and controller identity pass.
- `detached-tree`: the narrow receipt-unavailable guard passes.
- `guard-evidence`: no repair exists in this round, so no Elenchus verdict is
  claimed.

### Evidence and leads

Gates: focused 107/107; direct reporter 108/108 with zero failures, errors,
and skips; root 231/231; inoculation 1,258 cases with zero crashes and zero
unexpected clean results; Promise sync/check/coverage 14/14 and 69/69;
Phylax, Ephoros, Hypomnema, Imprimatur, Brevitas, Horos, and both diff checks
exit 0.

Leads not pursued: live capture, #436 receipt binding, #437 handover, and #508
process work are outside issue #435. No controller receipt, push, PR, merge, or
issue closure occurred in this audit.

This record was shaped by the bounded `sapheneia:sapheneia` durable-record
operation before append. The frozen inventory retained the zero-finding verdict,
all twelve risk dispositions, signed implementation identity, check counts,
known limits, and non-actions.
## Step 1, round 1 -- 2026-08-24

Non-Solidity round. The security suite is waived for this run: the step ships
Python, Markdown and JSON only, with no Solidity and no Foundry or Hardhat
project. Phylax, Ephoros and Hypomnema each returned clean over
`scripts/contributors.py`, `tests/test_contributors.py`,
`tests/emit_contributors_report.py` and `docs/contributors`. The three findings
below came from reading the diff, not from a lint.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | tests/emit_contributors_report.py | The emitter had no test at all. The step's exit requires it to write one `elenchus.unittest.v1` report to the supplied path and only that path, and nothing regressed it. It also imports `report_target`, `result_payload` and `write_report` from `tests/emit_run_observation_report.py`, so a signature change there breaks this module at import time, and the first symptom would be a broken audit round in a later step rather than a failing test here. The emitter cannot be executed from inside the module it loads without recursing, so the wiring is tested instead: the reused helpers import and are callable, every declared required file exists, the declared module list loads, an empty root produces a failing substitute suite, a present surface produces none, and the payload carries the `elenchus.unittest.v1` schema. | fixed in this round |
| S1-R1-02 | low | tests/test_contributors.py | `frozensets_from_source` raised a clear `AssertionError` when an assignment was not a `frozenset(...)` call, but passed the call's argument straight to `ast.literal_eval`. A frozenset built from a comprehension or a name rather than a set literal therefore surfaced as a bare `ValueError`, so the parity test reported an error where it had a diagnosis available. The guard was one branch short of the message it intended. | fixed in this round |
| S1-R1-03 | medium | scripts/contributors.py | Guard-order hazard reaching into step 2. `claude[bot]` and `app/claude` are both declared host identities and both fail `valid_login`, because neither is a legal GitHub login. The study's fail-closed posture stops the run on a login-grammar failure. So a ranking pipeline that validated grammar before excluding hosts would fail the whole weekly refresh on an identity the host set already knows how to drop, and nothing in the step recorded the required order. Fixed by stating the order in `valid_login`'s docstring next to the predicate it constrains, and by a test asserting that every host login failing the grammar check is still recognised by `is_host_login`. That test also fails loudly if the hazard ever disappears, so it cannot rot into a tautology. | fixed in this round |

Leads not pursued: `LOGIN_RE` accepts consecutive hyphens, which GitHub itself
rejects in a login. Left alone deliberately: the pattern exists to keep Markdown
syntax out of a generated artefact, a hyphen carries none, and tightening it
would trade a real guarantee for a cosmetic one. `.elenchus/` is not in the
repository's `.gitignore`, which predates this run and belongs to whoever owns
the run-observation emitter rather than to this step.

## Step 1, round 2 -- 2026-08-24

Against the tree with round 1's fixes applied. Phylax, Ephoros and Hypomnema
each returned clean again. Both findings are in round 1's own fixes, which is
what this round exists to catch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | tests/test_contributors.py | The parity check compared only the three host sets it already knew by name. A fourth `HOST_*` frozenset added to `hexctl.py` would therefore pass every test here while `scripts/contributors.py` missed a whole class of runtime identity, and the contributor ranking would treat that class as people. Round 1 closed a drift gap in the sets it knew and left the discovery gap open. Fixed by discovering `HOST_*` frozensets by prefix and asserting the discovered names equal `SET_NAMES` exactly, so a new set fails by name until the generator accounts for it. Verified in both directions: discovery over the real `hexctl.py` finds exactly the three, and a synthetic fourth set breaks parity. The first attempt at this fix was itself wrong, matching `HOST_BYLINE_RE`, a compiled pattern rather than a set; the predicate now skips a `HOST_*` name that is not a `frozenset(...)` call and says why, and a missing known set is still caught by the name comparison rather than by asserting shape at the wrong place. | fixed in this round |
| S1-R2-02 | low | tests/test_contributors.py | Round 1's guard around `ast.literal_eval` caught `ValueError` only. That is the exception every non-literal argument raises on the interpreter in hand, 3.14, but the repository's declared floor is 3.9 and the round-1 change pinned an exception type to behaviour observed on one version. Broadened to `(ValueError, TypeError)`. The `tempfile` import was also moved to module level, so no test body reaches for an import mid-run. | fixed in this round |

Leads not pursued: none.

## Step 1, round 3 -- 2026-08-24

Against the tree with rounds 1 and 2 applied. Phylax, Ephoros and Hypomnema
clean again. One finding, in the committed spec rather than the code.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | docs/contributors/study.md | Five dead relative links in a shipped document. The study is authored in the run's `.hexaemeron` directory, where `../ephoros/SKILL.md` correctly names the sibling skill. Copied to `docs/contributors/`, that same text resolves to `docs/ephoros/SKILL.md`, which does not exist, so every one of the study's five discipline citations was broken in the published copy. Copying a document changes what its relative links mean, and nothing in this repository checked a link in a shipped document. Fixed by rewriting the five to `../../plugins/hexaemeron/skills/<name>/SKILL.md`, each verified present, and by a test that resolves every relative link in both published spec files. The canonical `.hexaemeron/study.md` keeps its plugin-relative form and is deliberately not edited: it is receipted and digest-pinned, and its links are correct where it lives. The published copy diverging from it in link paths alone is the intended outcome, not drift. | fixed in this round |

Leads not pursued: the parity test reads the repository's vendored
`hexctl.py` rather than the installed controller running the loop. That is the
correct authority for a test that has to pass in CI, where no plugin cache
exists, but the test does not say so. Left as is; a comment would restate what
the path already shows.

## Step 1, round 4 -- 2026-08-24

Against the tree with rounds 1 to 3 applied. Phylax, Ephoros and Hypomnema
clean. One finding, again in the published spec rather than the code.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | medium | docs/contributors/runbook.md | The published runbook's header sent readers to `` `.hexaemeron/study.md` `` for its study. `.hexaemeron/` carries its own `.gitignore` matching everything and has zero tracked files, so that path exists only on the machine that ran the delivery and never in a clone. Round 3 fixed the study's dead Markdown links and missed this because the reference is backticked prose rather than a link, so the round-3 guard could not see it. Fixed by pointing the published runbook at its sibling published study, and by a guard asserting no published spec file mentions `.hexaemeron` at all, which is the general form of the defect rather than the one instance. The `re` import was also moved to module level, matching the correction made to `tempfile` in round 2 and undoing an inconsistency round 3 introduced. | fixed in this round |

Leads not pursued: the link-resolution regex truncates a URL containing a
closing parenthesis and would read `](` inside a fenced code block as a link.
Neither occurs in the two files it checks, and a stricter parser would be more
machinery than the defect justifies.

## Step 1, round 5 -- 2026-08-24

Against the tree with rounds 1 to 4 applied. Zero findings.

Phylax, Ephoros and Hypomnema clean. Root suite 211 tests, all passing. The
four guards installed across rounds 1 to 4 were each confirmed to fail without
their fix, three of them by Elenchus returning `guarded` on a recorded parent
assertion failure.

The remaining question this round examined was whether `docs/contributors/`
needed registering anywhere. It does not: nothing in the repository enumerates
`docs/` subdirectories, and `docs/protasis-discipline-cores/study.md` is
existing precedent for a nested study and runbook pair alongside the flat
`docs/<topic>-study.md` form. No index to update and no convention broken.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-24

Non-Solidity round on the step that opens the network boundary. Phylax and
Ephoros clean. Hypomnema clean once invoked correctly; see S2-R1-05.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | scripts/contributors.py | The reader checked the landing host with `response.geturl()` after `urlopen` returned. `urllib`'s `HTTPRedirectHandler.redirect_request` copies every request header onto the redirected request except `content-length` and `content-type`, confirmed by reading its source: `Authorization` is not excluded. So a 301 or 302 off `api.github.com` sent the bearer token to the redirect target, and the check fired only after that request had already completed. A token leak to an arbitrary host, detected one step too late to matter. Fixed with a `RefuseOffHostRedirect` handler that stops before the redirected request is issued, kept at module level so it is testable rather than sealed inside the reader factory. The landing-host check is retained as a second line. Three tests: the off-host stop, an on-host redirect still allowed, and one pinning `urllib`'s header-copying behaviour so nobody removes the guard as belt and braces. The stop's message is asserted not to echo the token. | fixed in this round |
| S2-R1-02 | medium | scripts/contributors.py | `--repo` reached the API path unvalidated. A login is checked against the GitHub login grammar before it is interpolated, so a login cannot inject query syntax, but the repository came straight from the command line into `/repos/{repo}/contributors?...` and `q=repo:{repo}+...`. `--repo 'x/y&per_page=1'` rewrites the query. Operator-supplied rather than attacker-supplied, but the study names this read as a boundary with controls and an unvalidated path component is not one. Fixed with an `owner/name` grammar check, tested against seven malformed forms. | fixed in this round |
| S2-R1-03 | low | scripts/contributors.py | The git-authorship corroboration counted how many sampled commits carried a non-host author, stored both counts on the working entry, and then dropped them: the rendered payload took only rank, login, commits and merged pull requests. Evidence gathered and discarded is evidence nobody can check. Both counts are now reported per contributor. | fixed in this round |
| S2-R1-04 | medium | scripts/contributors.py | Two silent caps. The contributors read took `per_page=100` and used page one only, so a repository with more than a hundred contributors would lose everyone past the first page with no sign in the output. The closed-issue read did the same and additionally ignored `total_count`, so partial coverage read as full coverage. Both are the failure mode where a truncated list looks complete. Fixed with a paginating read that stops rather than truncating when pages outlast `MAX_PAGES`, and a closed-issue check that stops naming how many of how many it read. Three tests, including one asserting page two is actually fetched. | fixed in this round |
| S2-R1-05 | low | audit procedure | Hypomnema was first run over `scripts tests` only and reported two H006 findings claiming `ADR-016` does not exist. It does. The lint resolves a comment's record citation against an index it builds from the record files it walked, so omitting `docs` from the invocation empties the index and turns every valid citation into a finding. The trap is worse than a wasted round: acting on the finding would mean deleting a correct citation to satisfy a lint that was never shown the record. Recorded here so later rounds on this run invoke it as `hypomnema.py docs scripts tests`. No code change. | recorded, no fix needed |

Leads not pursued: the corroboration read samples at most twenty commits per
contributor, which is a bound rather than a proof. It is now reported in the
payload as `commits_sampled` alongside `human_authored_sampled`, so the bound is
visible rather than implied, and widening it would cost an API call per
contributor to strengthen a check that already fails closed.

Elenchus verdict for this round: `inconclusive`, not `guarded`. Against the
parent it recorded 45 executed, three assertion failures and four errors. The
three failures are the guards working: the repository-grammar stop, the
closed-issue coverage stop, and the corroboration-evidence report each failed on
the unfixed tree. The four errors are `AttributeError` from two tests naming
`RefuseOffHostRedirect` and `read_all_pages`, symbols the parent does not carry.
Elenchus cannot tell a proved guard from a broken harness once errors appear, so
it declines to call the round guarded, and that is the correct reading of the
evidence rather than a tooling complaint. Round 2 reshapes those two tests to
assert the symbol's presence instead of dereferencing it.

## Step 2, round 2 -- 2026-08-24

Against the tree with round 1's fixes applied. Phylax and Ephoros clean.
Hypomnema clean, invoked as `hypomnema.py docs scripts tests` per S2-R1-05.
One finding, in round 1's own guards.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | tests/test_contributors.py | Round 1's guards for the redirect and pagination fixes dereferenced `contributors.RefuseOffHostRedirect` and `contributors.read_all_pages` directly. On a tree without those symbols that raises `AttributeError`, which unittest records as an error rather than a failure, and Elenchus refuses to call a round guarded once errors appear because it cannot tell a proved guard from a broken harness. Round 1 therefore recorded `inconclusive` on five findings whose guards were mostly sound: three failed cleanly, four crashed. A guard that errors on the unfixed tree proves nothing it could not have proved by failing. Fixed by asserting each symbol's presence and returning it, through one helper per class carrying the reason. Verified directly rather than inferred: the reshaped guards run against the pre-fix `scripts/contributors.py` from `5f424e5` produce 7 assertion failures and 0 errors, where round 1's shape produced 3 failures and 4 errors. | fixed in this round |

Leads not pursued: this round's Elenchus verdict is `passed` rather than
`guarded`, and that is the honest reading. The change is a test reshape with no
behaviour change, so against its own parent, which already carries round 1's
fixes, nothing fails. The reshape cannot retroactively re-prove round 1; it makes
the guards well-shaped from here on, and the proof of that is the direct
comparison recorded above rather than a verdict this round could produce.

## Step 2, round 3 -- 2026-08-24

Against the tree with rounds 1 and 2 applied. All three lints clean. One
finding, in a promise the study made that the code had not kept.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | scripts/contributors.py | The study's item 10 states the generator "must complete inside the unauthenticated rate limit when run without a token, or say plainly that it needs one." Nothing implemented that. Worse, `urllib.error.HTTPError` subclasses `URLError`, confirmed directly, so catching only `URLError` reported every HTTP status as a generic "api read failed" and discarded the one field that says what to do. A rate-limited run therefore looked like a network fault. The numbers make it reachable rather than theoretical: the search endpoints allow 30 requests a minute with a token and 10 without, and this generator issues two search calls per ranked contributor plus two more, so an unauthenticated run stops being viable at about four contributors. Fixed by catching `HTTPError` ahead of `URLError`, naming the status when it is not rate limiting, and on a 403 or 429 carrying an exhausted `X-RateLimit-Remaining` or a `Retry-After` saying which limit was hit, when it resets, and whether the answer is to set a token. Four tests, one of which pins the subclass relationship so a future reordering of the handlers cannot silently lose the status again. | fixed in this round |

Leads not pursued: the generator does not pre-flight `/rate_limit` before
starting, so it discovers exhaustion by hitting it. Adding a pre-flight would
spend a request to predict a condition the run now diagnoses correctly when it
happens, and the diagnosis is what was missing.

### Correction to the step 2 round 3 record

The controller ledger stores `elenchus_verdict: guarded` for step 2 round 3.
That receipt is wrong. Elenchus returned `inconclusive` on that commit, with 49
executed, 0 assertion failures and 3 errors. The wrong value was submitted to
`hexctl audit-round` and the ledger is hash-chained and append-only, so the
false entry cannot be rewritten; `hexctl amend` covers a study amendment and not
an audit round. This paragraph is the correction, and round 4 below carries the
verdict the round should have recorded.

The cause is the defect S2-R2-01 named one round earlier, repeated. The three
new rate-limit tests dereferenced `contributors.rate_limit_aware_message`, a
symbol the parent does not carry, so they raised `AttributeError` and Elenchus
saw errors rather than assertion failures. The round-2 fix established the shape
that avoids this and round 3 did not apply it to its own new tests. Round 4
applies it and re-derives the verdict.

Anyone reading the ledger for step 2 round 3 should read `inconclusive`.

## Step 2, round 4 -- 2026-08-24

Against the tree with rounds 1 to 3 applied, plus the correction above. All
three lints clean. One finding, and it is the same omission as S2-R2-01 made a
third time.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R4-01 | medium | tests/test_contributors.py | Round 3's three rate-limit guards dereferenced `contributors.rate_limit_aware_message` directly and so errored rather than failed on the unfixed tree, which is exactly the defect S2-R2-01 named. Round 2 had fixed the same shape by adding a per-class accessor, and that fix was not generalised, so the next new test reintroduced it. The first attempt at this round's fix then put the accessor on `NetworkBoundary` while the three tests live in `Coverage`, breaking the suite outright and making the same class-scoping mistake visible a second time within one round. Fixed properly with a shared `RequiresSymbol` mixin carrying one `require(name, why)` method, used by both classes, so the next new guard inherits the right shape instead of depending on whoever writes it remembering. Verified directly: against the pre-round-3 `scripts/contributors.py` the reshaped guards give 3 assertion failures and 0 errors, where round 3's shape gave 0 failures and 3 errors. | fixed in this round |

Leads not pursued: none. The pattern that produced S2-R2-01, S2-R4-01 and the
false receipt corrected above is one pattern, and the mixin is the structural
answer to it rather than a third instance of remembering.

## Step 2, round 5 -- 2026-08-24

Against the tree with rounds 1 to 4 applied. Zero findings.

Phylax, Ephoros and Hypomnema clean. Root suite 241 tests, all passing. The
live `--json` path runs clean against the real API and ranks `kethcode` then
`radup1337`, excluding `claude`, `claude[bot]`, `laurenceday` and
`shoggoth-wildcat` with a distinct reason for each.

This round examined the one thing the local machine cannot check. The repository
CI matrix pins Python 3.9 and this machine has only 3.14, so 3.9 behaviour is
asserted by reading rather than running: both files carry
`from __future__ import annotations`, so every annotation is a string and never
evaluated, and an AST walk finds no `match` statement and no runtime `X | Y`
union, the two 3.10 features that a future import does not cover. That is
evidence about the syntax, not a passing 3.9 run. The 3.9 job on this step's
pull request is the actual check, and step 1's equivalent job passed.

Leads not pursued: `http_reader` imports `urllib.error` inside the factory while
`urllib.parse` and `urllib.request` are imported at module scope, because the
module-level pair is needed by `RefuseOffHostRedirect` at class-definition time
and the third is not. Consistent enough to leave; moving it would change nothing
a reader relies on.

## Step 3, round 1 -- 2026-08-24

Non-Solidity round on the step that writes tracked files. Phylax, Ephoros and
Hypomnema clean. Four findings.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | scripts/contributors.py | `atomic_write` built its replacement with `tempfile.NamedTemporaryFile`, which creates at 0600, and `os.replace` carries the temporary file's mode onto the target. Both artefacts landed as `-rw-------` where every other file in the repository is `-rw-r--r--`, confirmed by `stat`. The serious half is `README.md`: a tracked file that existed before this run was silently narrowed from 0644, and git records only the executable bit, so the change appears in no diff and no review would catch it. Fixed by preserving an existing file's mode and giving a new file 0644. The two artefacts already on disk were repaired and regenerated. Three tests: a tracked file keeps 0644, a new artefact is world-readable, and an unusual existing mode is preserved rather than normalised. | fixed in this round |
| S3-R1-02 | medium | scripts/contributors.py | `rendered` read `README.md` with a bare `read_text`, so an absent or non-UTF-8 README came out of `--check` as `FileNotFoundError` or `UnicodeDecodeError` rather than a named stop. The study's fail-closed posture requires a stop to name what went wrong; a traceback from the middle of a weekly job names the line and not the cause. Both are now stops that name the file. | fixed in this round |
| S3-R1-03 | medium | .horos/boundary.json | Adding `CONTRIBUTORS.md` at the repository root invalidated the committed Horos reading boundary, and the step did not refresh it. The repository's own `test_boundary_currency` caught this, which is the system working, but it also corrects a judgement made earlier in this run: during the post-spec marketplace reassessment Horos was dismissed as having no concrete job in the remaining steps. It had one, and the evidence was a failing test rather than an argument. Refreshed with `horos.py scan . --write`. | fixed in this round |
| S3-R1-04 | low | tests/test_contributors.py | Two of this round's own guards used `assertRaises(Stop)` against code whose defect is that it raises the wrong exception type. `assertRaises` records a wrong type as an error, and the wrong type was the finding, so those guards could never prove their own fix. This is the third distinct shape of the same underlying mistake in this run, after a missing symbol and a mis-scoped helper. Fixed with an `assert_stops` helper on the shared mixin that catches everything and fails on any exception that is not a `Stop`. Verified: against the parent the round's guards now give 5 assertion failures and 0 errors, where before they gave 3 failures and 2 errors. | fixed in this round |

Leads not pursued: `atomic_write` does not fsync the containing directory after
`os.replace`, so the rename is not guaranteed durable across a host crash. The
artefacts are regenerated weekly from a source of truth that is not this file, so
the recovery for a lost rename is the next scheduled run.

## Step 3, round 2 -- 2026-08-24

Against the tree with round 1 applied. All three lints clean. One finding, in
the atomic-write path round 1 touched but did not follow through.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | scripts/contributors.py, .gitignore | Round 1 established that `atomic_write` cleans up its temporary file when `os.replace` raises. It does not, and cannot, clean up after a hard kill. Confirmed by leaving one deliberately: `.CONTRIBUTORS.md.5le1z97x` appeared in the repository root, `git status` listed it as an untracked change, and `git check-ignore` confirmed nothing ignored it. Two consequences, and the second is the one that matters. A broad `git add` could commit the litter. More importantly step 4's workflow decides whether to open a pull request from whether anything changed, so an orphan from a killed run would make an unchanged ranking look changed and open an empty pull request every week. Fixed by ignoring `.CONTRIBUTORS.md.*` and `.README.md.*`, and by sweeping the script's own orphans at the start of a write. The sweep is anchored to the exact artefact names it writes and touches regular files only, so nothing outside its own litter is in scope; a test asserts a bystander file survives it. | fixed in this round |

Leads not pursued: the sweep runs at the start of a write and not on a
`--check`, so a check on a littered tree still reports the ranking correctly
while leaving the orphan in place. That is deliberate: `--check` is the read-only
mode and should not mutate the tree it is inspecting.

Also in this round, and worth naming as a pattern rather than an incident: one of
the round's own tests called `contributors.sweep_orphans` directly instead of
going through the `require` helper, so Elenchus first returned `inconclusive` on
one error. That is the fourth occurrence of the same mistake in this run, in a
round whose predecessor added the very mixin that prevents it. The instance was
fixed and the verdict re-derived as `guarded` with three assertion failures and
zero errors.

The lesson taken is that a helper only prevents the mistake for whoever
remembers to call it. So the check is now mechanical: compare the symbols the
test file dereferences against the symbols the parent commit defines, and treat
any name present in the former and absent from the latter as a guard that will
error rather than fail. Run against this round it reports none. That comparison
is cheap enough to run before every audit round in the remaining steps.

## Step 3, round 3 -- 2026-08-24

Against the tree with rounds 1 and 2 applied. Zero findings.

Phylax, Ephoros and Hypomnema clean. Root suite 260 tests, all passing.
`--check` exits 0. Both artefacts are `-rw-r--r--` after a regeneration, no
orphan temporaries remain, and the working tree is clean.

The check this round added is the one step 5's demonstration depends on:
`--write` followed by `git diff --exit-code` over both artefacts comes back
clean, so what is committed is exactly what the generator produces. Without that,
step 5 could pass its own demo against artefacts a human had edited by hand.

Leads not pursued: `.gitignore` now also hides a file a person might genuinely
name `.CONTRIBUTORS.md.bak`. Accepted: the pattern has to cover a random suffix,
and losing a hand-made backup of a generated file from `git status` costs nothing
that matters.

## Step 4, round 1 -- 2026-08-24

Non-Solidity round on the unattended trigger. All three lints clean. Two
findings, one of them the inverse of the signal the study asked this step for.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | high | .github/workflows/contributors.yml | The summary step ran under `if: always()` and its first branch tested `steps.decide.outputs.changed != 'true'`. A `decide` step that failed, which is what a rate-limited or unreachable API produces, sets no output at all, so the empty value satisfied that branch and the summary announced "No change. The committed list already matches the repository's history." A failed weekly run would therefore have reported a clean no-op, in the one place somebody looks to find out whether the refresh is still working. The study's item 8 asked for the opposite property in as many words: a no-op distinguishable from a failure. This inverted it. Fixed by testing `job.status` first and saying plainly that the run failed and established nothing, with a test asserting the status check precedes the changed check rather than merely existing. | fixed in this round |
| S4-R1-02 | low | .github/workflows/contributors.yml | The two generated commits carried the message "chore(contributors): refresh the ranked list" and nothing about their origin, so a reader of `git log` could not tell they were machine-written or how to reproduce them. Each now names the workflow, the generator, and the command that reproduces the result. Deliberately no provenance trailers: a scheduled job is not the Shoggoth performing governed work under ADR-016, and `Co-authored-by: Shoggoth` on a cron commit would claim an authorship that did not happen. A test asserts both trailers stay absent from the workflow's executable lines. | fixed in this round |

Leads not pursued: the workflow is not executed by this run and cannot be. Its
shape is asserted by twelve tests and its behaviour is established by its first
scheduled or dispatched run. Two things it depends on could not be verified from
here. Whether organisation policy permits the Actions token to open a pull
request returned HTTP 403 on the permissions endpoint for the account running
this delivery, so it is unknown rather than confirmed. And whether a Contents API
write satisfies the signed-commit ruleset is inferred from an existing merge
commit in this repository reporting `verified: true` with committer `GitHub`,
which is strong evidence about GitHub's signing but not a test of this workflow.
Both are named in the pull request as first-run risks rather than left implicit.

## Step 4, round 2 -- 2026-08-24

Against the tree with round 1 applied. All three lints clean. One finding.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R2-01 | low | .github/workflows/contributors.yml | The job set no `timeout-minutes`, so a hung API call would hold a runner until GitHub's six-hour job ceiling, once a week, with nobody watching. No other workflow in this repository sets one either, but that is not the same precedent: the others are pull-request CI, bounded by the change that triggered them and observed by whoever opened it. This one is a scheduled writer making network calls unattended. Bounded at ten minutes, which is generous for a handful of API reads and two writes. The reason for departing from the surrounding style is recorded in the workflow itself, so the next reader does not normalise it away. A test asserts exactly one timeout exists and that it is not so large as to be no bound at all. | fixed in this round |

Leads not pursued: `actions/checkout@v4` and `actions/setup-python@v5` are
pinned by tag rather than commit digest. Every other workflow here does the same,
so changing only this one would be inconsistent without being safer; pinning is a
repository-wide decision rather than this step's.

## Step 4, round 3 -- 2026-08-24

Against the tree with rounds 1 and 2 applied. All three lints clean. One
finding, and it is the most serious of the step.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R3-01 | high | .github/workflows/contributors.yml | The workflow was not valid YAML and would never have run. Round 1's own fix for S4-R1-02 introduced a multi-line shell string inside a `run: |` block whose continuation lines began at column 1. A block scalar ends at the first line indented less than the block, so YAML terminated the script there and tried to read `Generated by ...` as a new mapping key. Confirmed with a parser rather than by eye: Ruby's YAML reports `could not find expected ':' while scanning a simple key at line 112`, and the repository's other four workflows parse cleanly, so the fault was this file's alone. GitHub would have reported a workflow syntax error and the weekly refresh would simply never have happened, silently, from the moment it merged. Fixed by building the message with `printf` and properly indented continuations. | fixed in this round |

The failure this round exposes is not only the broken file. Fifteen shape tests
passed against an unparseable workflow. Every one of them read strings or
indentation, so all of them were satisfied while the artefact they described
could not load at all. Structural assertions about a file say nothing about
whether the file is valid, and a suite of them can be entirely green over
rubble. Two guards were added. A parser check is not one of them, because
PyYAML is absent from this repository's root suite and adding a dependency to
validate one file is the wrong trade. Instead the specific defect class is
guarded directly: no line may sit at column 1 unless it is one of the five
known top-level keys, which is exactly what a terminated block scalar produces.
That guard was verified by reintroducing the original defect and confirming it
flags the line.

Leads not pursued: the guard catches an unindented line, not every possible way
to invalidate YAML. A malformed nested mapping would still pass it. Accepted:
the check is aimed at the one failure this file actually suffered, and GitHub's
own workflow parser is the backstop for the rest.

## Step 4, round 4 -- 2026-08-24

Against the tree with rounds 1 to 3 applied. Zero findings.

All three lints clean. Root suite 281 tests, all passing. `--check` exits 0 and
the working tree is clean.

This round re-read the workflow through an actual parser rather than through the
string assertions that had already been fooled once. It loads, and the values it
loads are the ones the runbook asked for: the job guard is
`github.repository == 'wildcat-finance/skills'`, `timeout-minutes` is 10,
`permissions` is exactly `contents: write` and `pull-requests: write` with
nothing else, `concurrency` is grouped as `refresh-contributor-list` with
`cancel-in-progress` false, and the triggers are one weekly cron at `17 4 * * 0`
plus `workflow_dispatch`. Six steps.

Leads not pursued: two properties of this workflow cannot be established from
here and are named in the pull request rather than left implicit. Whether
organisation policy permits the Actions token to open a pull request could not be
read: the permissions endpoint returns HTTP 403 to the account running this
delivery. And whether a Contents API write satisfies the signed-commit ruleset is
inferred from an existing merge commit in this repository reporting
`verified: true` with committer `GitHub`, which is good evidence about how GitHub
signs but is not a test of this job. Both resolve on the first dispatched run,
which is the correct place for them to resolve.

## Step 5, round 1 -- 2026-08-24

Non-Solidity round on the records this work leaves behind. All three lints
clean. Three findings, the first of them external in origin.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | medium | docs/decisions/ | Decision-record number collision. This run planned `ADR-017-rank-contributors-by-resolved-identity.md`, and the concurrent delivery for issue #466 had already opened pull request 521 carrying `ADR-017-bind-merged-authorship-to-the-integration-receipt.md`. Two records cannot share a number, and #521 claimed it first. Renumbered to ADR-018. The renumbering is recorded three ways rather than performed silently: inside the record's own Status section, in a dated Protasis amendment to the receipted study through `hexctl amend study`, which returned `step 5 holds`, and in the published spec copies. The study's item 12 still reads ADR-017 above the amendment, which is the point: the amendment appends so the run's earlier belief stays readable. | fixed in this round |
| S5-R1-02 | low | tests/test_contributors.py | The dead-link guard added in step 1 round 3 listed only the two published spec files. Step 1 found that same defect twice, and a guard scoped to the files that had already failed could not cover the records added later, which is most of this step's output. Widened to every document this work ships, including the two new records and `CONTRIBUTORS.md`. The companion run-state guard was also over-broad: it flagged any line mentioning `.hexaemeron`, which would fail on a document that legitimately discusses the directory, so it now matches a citation rather than a mention. | fixed in this round |
| S5-R1-03 | low | docs/decisions/ADR-018-rank-contributors-by-resolved-identity.md | The widened guard immediately earned itself. ADR-018 linked to #521's ADR-017 by relative path, and that file does not exist on this branch and will not until #466 lands, so the record shipped with a link that resolved to nothing. Changed to a named reference carrying the pull-request number, with the reason it is not a link stated in the record. | fixed in this round |

Leads not pursued: this run and the #466 delivery both append to
`audit/AUDIT.md`, so whichever merges second will conflict there. The conflict is
textual and the resolution is to keep both blocks, since the file is an
append-only log of rounds that genuinely both happened. Left for the merge rather
than pre-empted, because reordering this run's own log to anticipate another
branch's would make the record less true, not more.

## Step 5, round 2 -- 2026-08-24

Against the tree with round 1 applied. Zero findings.

All three lints clean. Root suite 287 tests, all passing. The demonstration path
from the study's problem statement runs clean end to end, including
`git diff --exit-code` over both artefacts, which is what establishes that the
committed files are exactly what the generator produces rather than something a
hand edited afterwards. The working tree is clean and the guard-shape comparison
against the parent commit reports nothing that would error rather than fail.

Leads not pursued: none.

## Issue 436 run-observation receipt binding, step 1, round 1 -- 2026-08-24

### State

Audit of signed implementation `8296e09402d1061508f976cc7b9027aaccd5927a`.
Six findings were reproduced against that tree and repaired together in signed
commit `f22e235dad0c20485eb3e10d96d38ffd551bb4dc`. The repair does not advance a
Fiat phase or strengthen the observation claim.

### Findings

| id | severity | mechanism | remediation |
| --- | --- | --- | --- |
| I436-S1-R1-01 | high | The controller captured one stable byte snapshot, then asked the validator to reopen the named path. An ABA replacement could therefore validate later bytes while the receipt digested earlier invalid bytes. | Added immutable-byte validation, path/byte parity guards, and made binding validate only the captured snapshot. |
| I436-S1-R1-02 | medium | Verification summed the unbound tail after every historical prefix. Two bindings over one stream overstated the actual latest tail. | Report only the bytes after the newest verified prefix; the two-binding guard pins the exact count. |
| I436-S1-R1-03 | high | Each binding verified in isolation, but verification did not re-establish one ordered, strictly increasing stream. A later valid binding could name a different artefact or cease extending the earlier digest. | Recompute record order, artefact identity, byte and event growth, and the earlier-prefix digest for every adjacent binding. |
| I436-S1-R1-04 | high | A binding was joined to a ledger record only by its binding digest and line adjacency. Edited `receipt_hash` or `capture_status` record data still verified. | Require one unused exact observation record whose receipt hash and capture status equal the binding. |
| I436-S1-R1-05 | high | Extra `record:run-observation` ledger entries with no state binding were ignored. Verification could report one clean prefix while another observation receipt was orphaned. | Require an exact count match between bindings and observation ledger records, then consume each record once. |
| I436-S1-R1-06 | high | Verification recomputed digest, count and interval but did not rerun structural validation. Malformed bytes carrying a forbidden hidden-work field could be rehashed into state and ledger and verify cleanly. | Rerun the immutable-byte structural validator over every exact bound prefix before accepting its summary. |

### Risk dispositions

- `companion-path` -- exercised. Canonical confined no-follow reads, symlinked
  file and parent refusals, and stable double reads remain green.
- `prefix-drift` -- exercised. Replacement, truncation, reorder, ABA capture,
  and post-receipt mutation guards refuse with `FOB003` or `FOB004`.
- `unbound-tail` -- exercised. One and two-binding guards preserve the earlier
  claim and report only the newest tail.
- `run-association` -- exercised. Wrong contract and wrong run refuse without
  echoing either rejected value.
- `receipt-association` -- exercised and repaired. Line adjacency, exact receipt
  fields, record data, record count, uniqueness, and increasing ledger order are checked.
- `contract-identity` -- exercised. Binding and observation contract drift
  refuse, and every exact prefix is structurally revalidated.
- `count-agreement` -- exercised. Byte count, event count, interval, final
  newline, and adjacent-prefix growth are recomputed.
- `gate-status` -- exercised and repaired. Accepted claims require passing
  capture, validation and redaction fields plus a fresh structural result.
- `controller-independence` -- exercised. Ordinary `hexctl verify` remains green
  while each corrupted dependent observation claim refuses.
- `legacy-state` -- exercised. A version-1 run without a binding verifies
  normally; only `verify --observations` returns `FOB001`.
- `partial-write` -- exercised. Stable descriptor reads, exact captured-byte
  validation, final rereads, and digest checks prevent a clean torn prefix.
- `diagnostic-echo` -- exercised. Findings expose only stable codes, bounded
  descriptions and recovery; hostile path and event values remain absent.
- `binding-growth` -- exercised and repaired. The 64-binding cap, one-to-one
  ledger join, strict extension and increasing record order bound growth.
- `coverage-drift` -- exercised. Promise coverage binds controller, validator,
  documentation, fixtures, both test surfaces, and every new selector.

### Evidence

- Focused observation and Promise surface: 157 of 157 tests passed.
- Root suite: 349 tests run; 344 passed and five detached-receipt tests skipped
  under their existing explicit condition.
- Hexaemeron suite and Elenchus fixed-tree report: 955 of 955 tests passed.
- Inoculation matrix: 1,258 cases, zero crashes and zero unexpected clean.
- Promise Machine: 14 copies exact; 70 promises and 70 selected coverage rows.
- Elenchus verdict for `f22e235`: `guarded`; its parent report records assertion
  failure in the new guard surfaces, with no infrastructure substitution.
- Phylax, Ephoros, Hypomnema, both Protasis modes, Horos, syntax, JSON, receipt
  byte identity, diff check, and all eight per-document prose gates exited zero.

### Boundary and next

ADR-024 is the allocated observation-binding decision; reserved ADR-023 and
accepted ADR-015 and ADR-022 remain unchanged. No Solidity surface exists, so
the security suite remains waived and Phylax carries the off-chain review.
No push, pull request, issue mutation, integration or controller receipt was
performed by Warden. Six findings prevent closure; an independent round 2 must
review the repaired tree.

Leads not pursued: none. A filename's host-specific Unicode spelling is not a
portable artefact claim here; the declared boundary is lexical confinement,
no-follow regular-file access and no rejected-path echo, all of which were
exercised.

## Issue 436 run-observation receipt binding, step 1, round 2 -- 2026-08-24

### State

Audit of round 1's signed fixed tree at
`71f1471722c4de5e14f9ed7e7efd2435da97f7fa`. One high finding was reproduced
twice on both affected command paths and repaired in signed commit
`49b8652db3d19c1501e074582454d08fab54b8e6`.

### Finding

`I436-S1-R2-01` -- high -- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`.
Binding and verification each captured stable named bytes and validated that
immutable snapshot, but neither re-established the named file after validation
finished. A deterministic replacement during the validator call therefore let
`observe` record a receipt, or let `verify --observations` return clean, while
the named path already held different bytes. The repair adds one shared final
no-follow double reread after all validation and summary work. It compares the
entire named snapshot, including any unbound tail, before state mutation or a
clean verification result. Separate bind and verify guards fail on the signed
parent and pass on the repair.

### Risk dispositions

- `companion-path` -- exercised and repaired: final named-byte identity now
  follows validation on both commands.
- `prefix-drift` -- exercised: before, during, and after-validation replacement
  mechanisms refuse without weakening an earlier digest.
- `unbound-tail` -- exercised: the final reread compares the complete current
  file while the claim remains limited to the selected prefix.
- `run-association` -- exercised: the derived controller identity and event run
  id still match after final reread.
- `receipt-association` -- exercised: exact selected entry, observation record,
  record data, count, and order remain joined.
- `contract-identity` -- exercised: both contract identifiers and structural
  rules are checked against the captured bytes.
- `count-agreement` -- exercised: byte count, event count, interval, prefix
  digest, and final named bytes agree.
- `gate-status` -- exercised: capture, validation and redaction must pass; the
  validation result is no longer separated from the final named subject.
- `controller-independence` -- exercised: ordinary verification remains green
  when the dependent observation check refuses.
- `legacy-state` -- exercised: no-binding runs remain valid outside the explicit
  dependent claim.
- `partial-write` -- exercised and repaired: deterministic post-validation swaps
  now return bounded `FOB002` refusals in bind and verify.
- `diagnostic-echo` -- exercised: the new refusal names no path or rejected byte.
- `binding-growth` -- exercised: the count cap, exact record join and strict
  extension checks remain green with the final reread.
- `coverage-drift` -- exercised: both new selectors and the repaired controller
  digest are bound in Promise coverage.

### Evidence

- Focused observation and Promise surface: 159 of 159 tests passed.
- Root suite: 349 tests run; 344 passed and five explicit detached-receipt tests
  skipped.
- Hexaemeron suite and Elenchus fixed-tree report: 957 of 957 tests passed.
- Inoculation matrix: 1,258 cases, zero crashes and zero unexpected clean.
- Promise Machine: 14 exact copies and 70 of 70 coverage rows.
- Elenchus verdict for `49b8652`: `guarded`; its parent report records assertion
  failures rather than errors or missing tests.
- All three discipline lints, both Protasis modes, Horos, syntax, JSON, receipt
  byte identity, diff check, and eight per-document prose gates exited zero.

### Boundary and next

The exact round-2 section is Imprimatur- and Brevitas-clean. Whole-file Brevitas
still names historical diagnostics before the issue #436 records; this round
does not rewrite unrelated audit history or claim that whole-file result.
ADR-024 remains the allocated decision and ADR-023 remains untouched. No push,
pull request, issue mutation, integration or controller receipt was performed
by Warden. One finding requires an independent round 3.

Leads not pursued: none.

## Issue 436 run-observation receipt binding, step 1, round 3 -- 2026-08-24

### State

Audit of the round-2 fixed tree at
`811e7d43c3f5e670ffe770bb169fd8eec99f0f2f`. Two high findings were
reproduced twice. The first is repaired in signed commit
`08bafba5629692873cce5ecc58feed3009f1ee0a`; the second is repaired in
signed commit `066e4524023a26aca1dcf2e1938536c0a6826f13`, which has the first
repair in its ancestry. The third receipted study amendment, SHA-256
`4fff8fe9b5a62463a6287e1b2f2395125235147c2ec1227b703975d5905a55be`,
adds only the source-owned reporter and its coverage guard to this step.

### Findings

`I436-S1-R3-01` -- high -- the final stable read checked the named file and
held its file descriptor, but it released the directory descriptors before
returning. Renaming `.hexaemeron/observations` outside the worktree at that
point left the original descriptor readable and made the named path disappear;
the command could return a clean snapshot that no longer named an in-root
artefact. The repair keeps the full no-follow descriptor chain and rechecks
the root and each opened directory identity before returning the snapshot.
The regression guard is
`test_final_read_refuses_parent_escape_during_second_snapshot`.

`I436-S1-R3-02` -- high -- the receipted source-bound command
`python3 plugins/hexaemeron/tests/run_tests.py {report}` was rejected before
the reporter emitted JSON because the runner accepted only
`--elenchus-report PATH`. The exact command exited 2 twice on signed
`08bafba`. The repair accepts one positional path as a compatibility alias,
keeps the existing confined no-follow report handling, and refuses the
positional and flagged forms together before creating either target. The guard
is `test_receipted_elenchus_reporter_accepts_positional_target`.

### Risk dispositions

- `companion-path` -- exercised and repaired. Final reads retain and verify
  every directory identity back to the confined root.
- `prefix-drift` -- exercised. Replacement, truncation, reordering, and
  before, during, and after-validation swaps refuse the dependent claim.
- `unbound-tail` -- exercised. The complete final reread detects alteration
  while preserving the prior prefix boundary.
- `run-association` -- exercised. The stable controller run identity remains
  required for the recorded prefix.
- `receipt-association` -- exercised. Each prefix still consumes one exact
  preceding receipt and record data.
- `contract-identity` -- exercised. Event and capture contracts are
  structurally revalidated over immutable bytes.
- `count-agreement` -- exercised. Byte count, event count, interval, and
  digest remain recomputed from the final stable snapshot.
- `gate-status` -- exercised. Capture, validation, and redaction status must
  pass before a binding can be recorded.
- `controller-independence` -- exercised. A refused observation never
  invalidates ordinary Fiat verification.
- `legacy-state` -- exercised. Version-1 runs remain valid until the
  explicitly dependent observation claim is requested.
- `partial-write` -- exercised and repaired. The second-snapshot
  parent-escape and post-validation replacement guards return bounded
  refusals rather than a clean result.
- `diagnostic-echo` -- exercised. The new path and argument refusals retain
  codes and recovery without echoing hostile bytes or paths.
- `binding-growth` -- exercised. Exact ordered receipt joins and the
  64-binding cap remain unchanged.
- `coverage-drift` -- exercised and repaired. Promise coverage now binds the
  reporter source, its exact digest, and the positional compatibility guard.

### Evidence

- Focused binding suite: 23 of 23 tests passed.
- Observation validator suite: 65 of 65 tests passed.
- Promise-contract suite: 73 of 73 tests passed.
- Source-owned fixed-tree reporter: 959 of 959 tests passed in 289.684
  seconds; its `elenchus.unittest.v1` record is complete with zero failures,
  errors, skips, expected failures, and unexpected successes. Its generated
  report was checked then removed.
- Root suite: 349 of 349 tests passed, with five existing explicit
  detached-receipt skips. The inoculation matrix ran 1,258 cases with zero
  crashes and zero unexpected clean results.
- Promise Machine has 14 exact copies and 70 selected coverage rows of 70.
  Both Protasis modes, Phylax, Ephoros, Hypomnema, Horos, syntax, JSON,
  receipt-copy parity, and diff check exited zero. Each of the four changed
  documents passed Imprimatur and Brevitas separately.
- The exact source-bound Elenchus command against `066e452` returned
  `passed`, not `guarded`: it overlays changed files in a detached parent
  worktree, and its current test classifier treats
  `plugins/hexaemeron/tests/run_tests.py` as a test because it is below a
  `tests` directory. The fixed reporter therefore also runs in the parent.
  This is not represented as `guarded`. The direct exact command red result
  on signed `08bafba` was preserved twice, and `passed` is an accepted
  controller verdict.

### Boundary and next

The framework classification detail is retained as a bounded lead for the
existing executable-gate prior art; no framework file is changed inside issue
#436. No push, pull request, issue mutation, integration, or controller
receipt was performed by Warden. Two findings require an independent round 4.

Leads not pursued: no new product mechanism after the complete fixed-tree
matrix.

## Issue 436 run-observation receipt binding, step 1, round 4 -- 2026-08-24

### State

Independent review of the signed round-3 tree at
`69a9ab36a307e58cf4da24933451a44e0bbae064`. The controller verified an
11-entry intact chain before review. No product or dependency bytes changed
after the fixed-tree reporter and root evidence recorded in round 3. This
round found zero product findings.

### Risk dispositions

- `companion-path` -- re-read. The final no-follow directory chain remains
  bound to the run root; the parent-escape regression refuses.
- `prefix-drift` -- re-read. Bind and verify still refuse replacement before,
  during, and after validation.
- `unbound-tail` -- re-read. The selected prefix remains distinct from later
  bytes in the same stream.
- `run-association` -- re-read. The controller-derived run identity and
  observation event identity remain exact.
- `receipt-association` -- re-read. A malformed matching ledger data value
  returns `FOB003`, not a Python exception.
- `contract-identity` -- re-read. Immutable bytes undergo the validator and
  closed interval checks before a receipt claim.
- `count-agreement` -- re-read. Digest, byte count, event count, and
  contiguous interval remain recomputed.
- `gate-status` -- re-read. Only accepted capture, passing validation, and
  passing redaction can support the dependent claim.
- `controller-independence` -- re-read. Ordinary controller verification
  remains separate from the optional observation claim.
- `legacy-state` -- re-read. The explicit observation verifier retains the
  bounded absence result for an older run.
- `partial-write` -- re-read. Stable double reads and the final named reread
  refuse torn, replaced, or escaped subjects.
- `diagnostic-echo` -- re-read. Refusals expose codes and recovery only.
- `binding-growth` -- re-read. Ordered receipt joins, strict extension, and
  the binding cap remain in force.
- `coverage-drift` -- re-read. Promise source digests, reporter guard, and
  all selected coverage rows remain current.

### Evidence

- The fresh binding and observation-validator slice passed 88 of 88 tests in
  28.468 seconds. It includes the three post-validation and parent-escape
  refusal guards.
- A direct malformed-ledger-data probe returned the bounded `FOB003`
  refusal. Positional and flagged reporter forms both resolved to confined
  in-worktree targets without creating a file; the duplicate-form probe exited
  2 before a write.
- The unchanged signed product tree retains round 3's fixed reporter result of
  959 of 959 tests passed and root result of 349 of 349 passed with five
  explicit detached-receipt skips. The 1,258-case inoculation matrix has zero
  crashes and zero unexpected clean results.
- Promise Machine remains at 14 exact copies and 70 selected coverage rows of
  70. The required discipline, copy, prose, syntax, JSON, Horos, and diff
  gates have the clean exits recorded in round 3.

### Boundary and next

No repair was made in this round, so no new Elenchus comparison is claimed.
The round-3 source-bound result remains `passed` with its classifier
limitation recorded there. Whole-file Brevitas retains historical findings
before the issue #436 sections; no new-line defect is introduced here.
No push, pull request, issue mutation, integration, or controller receipt was
performed by Warden. A zero-finding record permits the controller's audit-close
transition.

Leads not pursued: no new mechanism after the receipt, path, reporter, and
coverage review.
# Run: give the Kronos scoreboard and parked lane a durable home across ephemeral runners

## Step 1, round 1 -- 2026-08-24

Two Markdown documents, no code. The Solidity suite is waived for this run.
phylax exit 0, ephoros exit 0, hypomnema exit 0 over `docs/kronos-durable-home`.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The risk register describes the git subprocess and the working-copy write that
step 2 has not built, so none of those concerns can be exercised by two
documents. The look went at the claims the documents rest on. The frontier
digest
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1`
matches `plugins/hexaemeron/skills/kronos/EVOLUTION.md` byte for byte. The
starting ref `2b6848b95e9d90f4bc9995b8cd89106d1807e9a9` is this run's HEAD
parent. The five discipline citations in the committed study resolve from
`docs/kronos-durable-home/` to files that exist. Protasis and Imprimatur both
exit 0 over both documents. The committed copies are the receipted artefacts
with those five links rewritten for the new depth.

Root suite 310/310. Plugin suite 928/930: the two failures are
`test_elenchus_checker.ForgeReports.test_fixture_exercised_the_declared_forge_version`
(`1.7.1` vs local `1.4.0`) and
`test_elenchus_checker.NodeReports.test_fixture_exercised_the_declared_node_version`
(`v26.6.0` vs local `v22.14.0`). Both fail on the unfixed starting commit
`2b6848b95e9d90f4bc9995b8cd89106d1807e9a9` as well. This step does not touch
those fixtures.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-24

Non-Solidity round on `pull` and `push`. The Solidity suite is waived for this run.
phylax exit 0, ephoros exit 0, hypomnema exit 0 over `plugins/hexaemeron/skills/kronos` and the tests.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

The risk register was exercised by the new cases, all of which fail on the unfixed tree.

- symlink-escape: K010 still fires on `pull` and `push` when `.kronos` or a JSONL path is a symlink; nothing is written through the link.
- dirty-tree: after `pull`, `record`, `park` and `push`, `git status --short` in the scope is empty. `.kronos/.gitignore` still holds `*`.
- partial-write: a failed `os.replace` leaves the previous complete scoreboard; a missing final newline still refuses with K008.
- subprocess-git: git is a fixed argv list, no shell, 30s timeout, 2 MiB cap. A URL argument is refused with K020 before git starts. Git stderr is not copied into Kronos diagnostics; the K018 and K019 messages contain no `fatal` text.
- empty-as-cleared: a configured remote whose URL cannot be read refuses with K018 and leaves a standing park on disk.
- concurrent-push: a second tree's push updates the ref; a first tree that did not pull then refuses with K019 and its JSONL bytes are unchanged.
- remote-url-fetch: `https://example.invalid/skills.git` is K020 with `subprocess.Popen` patched to raise, so no fetch runs.
- state-commit-identity: throwaway commits use `git config` `user.name` / `user.email` from the scope and `commit.gpgsign=false`. No Shoggoth trailers.

A local `.kronos/tip` file, gitignored by `*`, records the last pulled or pushed SHA so a runner that has not pulled cannot fast-forward over a newer ref. It is not copied onto `refs/heads/kronos/state`. The two JSONL files remain the only blobs the ref holds.

Root suite 310/310. Plugin suite 944/946: the two failures are
`test_elenchus_checker.ForgeReports.test_fixture_exercised_the_declared_forge_version`
(`1.7.1` vs local `1.4.0`) and
`test_elenchus_checker.NodeReports.test_fixture_exercised_the_declared_node_version`
(`v26.6.0` vs local `v22.14.0`). Both fail on the unfixed starting commit
`2b6848b95e9d90f4bc9995b8cd89106d1807e9a9` as well. This step does not touch
those fixtures. Promise Machine coverage digests for `kronos-fiat-dispatch` and
`kronos-parked-lane` were updated to the new `kronos.py` bytes after reviewing
those field maps as unchanged; `pull` / `push` are not those promises' result
surface.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-24

Non-Solidity round on the skill text, the generation row and ADR-022. The
Solidity suite is waived for this run. phylax exit 0, ephoros exit 0,
hypomnema exit 0 over `plugins/hexaemeron/skills/kronos`, `docs/decisions`
and `docs/kronos-durable-home`.

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: --; severity: --; file: --; finding: none; status: --

This step adds no boundary and no new subprocess. The look went at the
records. `SKILL.md` frontmatter is `0.6.0` and matches the ledger. The new
history row is generation `kronos-v0.6.0` with frontier revision
`terminal-goal-loop` and digest
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1`, matching
the prior row byte for byte. Status remains `mature` and the next job remains
`None -- mature`. ADR-022 has the dated status and the five template sections.
The five discipline links in the committed study still resolve. The field-drift
guard still finds every `record` field named in the skill. The demo path on a
local bare remote: `parked` on the second tree exits 3 with the same held-job
hash and the same reason bytes; `show` prints the pass; `git status --short`
is empty.

Root suite 310/310. Plugin suite 944/946: the two failures are
`test_elenchus_checker.ForgeReports.test_fixture_exercised_the_declared_forge_version`
(`1.7.1` vs local `1.4.0`) and
`test_elenchus_checker.NodeReports.test_fixture_exercised_the_declared_node_version`
(`v26.6.0` vs local `v22.14.0`). Both fail on the unfixed starting commit
`2b6848b95e9d90f4bc9995b8cd89106d1807e9a9` as well. This step does not touch
those fixtures.

Leads not pursued: none.
## H003 quoted specimen, step 1, round 1 -- 2026-08-24

Non-Solidity round over the two Markdown documents step 1 commits. Zero
findings.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over both changed documents and over the required tree
`README.md AGENTS.md .agents plugins docs`. Protasis accepts the study and the
runbook. Imprimatur reports no defect on either. The Hexaemeron suite passes
935/935 and the boundary-currency guard 7/7 at commit
`85933daa48353759b177c4a1a66588501b53d962`, whose local signature is good and
which carries exactly one co-author and one origin trailer. The committed
boundary still describes the tree, so `.horos/boundary.json` stands unchanged.

Two register concerns are reachable at this step and both were checked.
`code-scope-creep`: the step changes no script, so every H000 to H007 case is
byte-identical to the entry state. `span-hides-live-pointer`: neither new
document produces a pointer match at all, under the current rule or the one
step 2 introduces, and the study carries exactly one Markdown link, which is
absolute. The other five concerns sit in step 2's diff and are not yet
reachable.

Brevitas is recorded rather than gated, as the step states: B010 and B001 on
the runbook, which a two-step specification cannot satisfy, and two B022
line-start matches on the study where a wrapped line begins with the word
`reading`. The shipped `docs/hypomnema-runbook-shape-check-runbook.md` carries
the same two structure codes on `main`, and the study's bytes are frozen by its
receipt.

Leads not pursued: the root suite reports 5 failures in this worktree and none
of them belong to this run. `tests/test_run_observation_capture.py` asserts
that `.hexaemeron/study.md` and `.hexaemeron/runbook.md` under the repository
root are byte-identical to the tracked issue 435 capture-profile copies,
against the hard-coded digests
`6858aaeadb12f204538b9120e51390b9c940fa995c8edb1471815d89aaa7f404` and
`56df27b7faae2af8f7ba16ec89526413038def6a0bbf86ff0274dc566f8bf9c5`, and it
skips only when those two files are absent. Every live Fiat run worktree holds
them and they always belong to that run, so the five tests fail for every run
except issue 435's. The same suite reports `OK (skipped=5)` on a clean checkout
of `main` at `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`, which places the cause
on `main` rather than in this step. Repairing it means editing another
delivery's receipted evidence binding, which is outside issue 500 and outside
this step's files, so it is named here rather than touched.

## H003 quoted specimen, step 2, round 1 -- 2026-08-24

Non-Solidity round over the checker change at
`af576c1bc9be26ed3884a1296a0f9ad06ceb592d`. Zero findings.

All three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over the required tree `README.md AGENTS.md .agents plugins docs`.
The demo path from the study's problem statement,
`hypomnema.py audit/AUDIT.md`, exits 0 where it reported two findings at the
step's entry. The Hexaemeron suite passes 946/946, the evolution and version
propagation suites 16/16, boundary currency 7/7, and Promise Machine reports
14 plugins and 14 copies clean after the `hypomnema-record-placement` runtime
binding digest was moved to `dff041c5b5a4db5ff9556bdae566b25bdd6d3b5229b139282d151a263f72c5be`
to match the edited `SKILL.md`. That file, `tests/promise_machine_coverage.json`,
is the one path this step changed that its runbook Files field did not name; the
gate the same step's exit runs is what required it. Imprimatur and per-file
Brevitas accept `SKILL.md` and `EVOLUTION.md`. The commit has a good local
signature and exactly one co-author and one origin trailer.

The whole-tree finding sets were compared between the parent checker at
`008364c78a47972dc033382e5b66d7983dd39a76` and this one, vendored trees
included. The parent reports four findings, this one reports two, and the
difference is exactly the two intended ledger specimens at `audit/AUDIT.md`
lines 6041 and 6186. Nothing anywhere in the repository is newly reported. The
two surviving findings are H001 link targets in
`plugins/hexaemeron/skills/x-ray/SKILL.md` line 344, inside the vendored Pashov
suite the default walk excludes, and they are unchanged by this step.

Every register concern was exercised. `backtick-run-blowup`: pairing is one
pass keyed by run length and the escape count walks backwards from each run
rather than over a prefix slice, which was the first draft and quadratic; a
line of 30,000 runs resolves its pointer in 0.008s, one of 20,000 mixed-length
runs in 0.006s, and 30,000 preceding backslashes in 0.002s. `span-hides-live-pointer`:
21 hand-built probes covering bare and quoted keywords, a backticked path after
a bare keyword, two spans with the keyword between them, a span closing
immediately before the keyword, double and triple backtick runs, an unbalanced
double-open, case variants, table cells, and a hash-bearing path all classify as
specified. `unmatched-run-drift`: an unpaired run opens no span, so a single
stray backtick cannot swallow a later pointer. `multiline-span-boundary`: a span
opened on one line and closed on the next is not read as a span and the pointer
stays reported. `code-scope-creep`: H001 and H002 still fire inside a span, and
the whole-tree comparison above is the wider proof. `yaml-pass-isolation`: the
YAML pass shares no helper with the span scan and its cases are byte-identical.
`pragma-interaction`: suppression runs after span state is computed and still
suppresses a live pointer.

One property of the demo path was checked rather than assumed. The fence state
machine over `audit/AUDIT.md` is balanced: 2 fence markers, 5 lines inside a
fence, the file ends outside one, and no pointer anywhere in it is hidden by
fence state. The clean exit is therefore a real clean and not a fence artefact.

Eleven guards ship with the change. Three are red against the parent: a wholly
quoted pointer earns no finding, an escaped backslash still opens a span, and
both recorded ledger specimens go clean. Eight are invariance pins, green on
both sides by construction, and the study's dated amendment of 2026-08-24
records why demanding red from those inverts their purpose.

Leads not pursued: three, each named rather than fixed.

The `RUNBOOK` pattern carries no leading word boundary, so `myrunbook: a/b`
matches and reports. That is a false positive rather than a false clean, it
predates this step, and closing it means narrowing what H003 reads in the same
run that narrows where it reads, which is the scope creep the study rules out
as a non-goal.

A backtick run of three or more on its own line is a fence opener under
CommonMark and the existing scan treats it as one, so a pointer on that line is
never reached. This is the fence rule rather than the span rule and it predates
the step; the parity check above establishes that it hides nothing in the
document this step unblocks.

The root suite still reports the same five capture-profile failures step 1
recorded, from the issue 435 receipt binding on `main`. Nothing in this step
touches them.

## H003 quoted specimen, step 2, round 2 -- 2026-08-24

Against the tree with round 1's record appended. Zero findings.

All three lints exit 0 again, the demo path over `audit/AUDIT.md` exits 0, and
the focused Hypomnema suite passes 91/91.

Round 1's own record turned out to be the clearest evidence the change was
needed. That block quotes a pattern specimen inside a code span, and the parent
checker at `008364c78a47972dc033382e5b66d7983dd39a76` reports H003 on it at
line 12544 for the target `a/b`, alongside the two older specimens at 6041 and
6186. The fixed checker reports none of the three. So the defect was not a
historical residue of two frozen lines: an ordinary round writing an ordinary
record added a third instance, permanently, on a file whose append-only
contract forbids the repair. That is what the three earlier rounds were
recording as a lead each time they met it.

Leads not pursued: the three named in round 1 stand unchanged, and no new lead
was found.

## Step 1, round 1 -- 2026-08-24

Zero findings.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

The audited range is
`84abae32d6d65b3a3ce27648ca144852a9e22e98..fae33c7e68f82095cf723ce72af858b7cbdc4018`
on
`fiat/554-runbook-amendment-receipts-step-1-publish-the-accepted-runbook-ame`.
It changes only `.horos/boundary.json`,
`docs/fiat-runbook-amendments-study.md`, and
`docs/fiat-runbook-amendments-runbook.md`; all three paths remain regular
non-executable files. The two documents are byte-identical to their receipted
sources: the study SHA-256 is
`1258efb979883681cc97e850dc9b641dd63f37a0f7beaf5bd5029d705ef76806`
and the runbook SHA-256 is
`21fa5133526f29a57bc7ada26b911c9d41e5d484eaf076a918023f75a53e6fcd`.
The relative skill links resolve from both sibling publication directories.
The boundary check reports `boundary matches the tree`.

Both source-bound repair runners use CLI report format
`unittest-json-v1` and separately name expected report schema
`elenchus.unittest.v1`, at runbook lines 71-73 and 199-201. Step 1's Files
field permits `audit/AUDIT.md` solely for append-only Warden round records at
line 46; this append therefore does not violate the implementation boundary.
The `audit-record-scope` row is discharged by this cold review only, not by a
product guard. `elenchus-identifier-swap` is also discharged by the labelled
role comparison rather than token presence.

Protasis exits 0 for the study and runbook. Imprimatur exits 0 for each, with
score 100.0/100 and zero defects. Phylax, Ephoros, and Hypomnema each exit 0
over the exact three-path committed surface and again over the four-path
candidate including `audit/AUDIT.md`. The root suite passes 349/349 with 5
skips, the Hexaemeron suite passes 986/986, Horos exits 0, and
`git diff --check` exits 0. The security suite waiver is unchanged: this
range contains JSON and Markdown, no Solidity. No Elenchus repair report was
created and no Elenchus verdict applies to this zero-finding round.

The implementation commit has a good Shoggoth signature, parent
`84abae32d6d65b3a3ce27648ca144852a9e22e98`, and exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one
`Wildcat-Origin: shoggoth` trailer. The range adds no executable path,
dependency, subprocess, service, unattended operation, or trust boundary.

The fifteen product risks `subject-confusion`, `prefix-forgery`,
`amendment-selection`, `field-ambiguity`, `step-verdict-coverage`,
`duplicate-step-source`, `effective-step-source`, `repair-precedence`,
`partial-write`, `pending-collision`, `checker-binding`, `post-amend-drift`,
`legacy-recovery`, `evidence-overclaim`, and `generation-collision` sit in
Step 2's controller, checker, tests, Promise, or ledger work and are not
reachable in this docs-only range. They remain owed there; this round makes no
claim about their implementation.

Qualification: the tracked study is a run artefact, not Hypomnema's standing
record. The governed-skill choice and rejected alternatives remain required
in the Fiat and Protasis `EVOLUTION.md` generation rows before the stack can
integrate, as Step 2's Files and Exit fields state. This Step 1 tip preserves
that placement contract; integration without those rows would not. No Step 2
runtime behaviour, receipt recovery, packet source, generation label, remote
link content, push, pull request, or integration state was checked in this
round.

The Sapheneia durable-record comparison preserved the heading, empty finding
table, zero verdict, date, identifiers, paths, digests, command results,
qualifications, unknowns, and lead disposition item by item. It changes no
existing audit bytes and does not claim audit-host enforcement.

Leads not pursued: the fifteen product risks above require Step 2's absent
implementation and remain assigned to that step. No other lead was found.

## Step 2, round 1 -- 2026-08-24

Finding count: 2. Audit filter declaration:
`--audit-filter sapheneia:sapheneia`. The Solidity security suite is waived
because the signed implementation and this repair contain Python, Markdown,
and JSON only.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:3435`; `plugins/hexaemeron/skills/protasis/scripts/protasis.py:74` | Both fence scanners accepted arbitrary leading whitespace. Four spaces make an indented CommonMark code block, not a fence, so a candidate could put `## Step 3` between four-space-indented backtick lines, hide that real heading from topology checks, then carry it in delegated step source. | fixed and guarded in `3d8ef99537ab0ccbf39a9f81d42159b061ba613b`; both scanners now permit at most three leading spaces, and controller plus Protasis guards cover the four-space rejection |
| S2-R1-02 | medium | `plugins/hexaemeron/skills/protasis/scripts/protasis.py:301` | `Complete replacement Exit: Reviewed and working.` passed because replacement parsing checked only that the value was non-empty. That let Fiat receipt and carry a replacement exit with no command even though Protasis's existing Exit contract requires one. | fixed and guarded in `3d8ef99537ab0ccbf39a9f81d42159b061ba613b`; Protasis applies its existing command-presence rule to a replacement Exit, while Fiat remains bound to Protasis and adds no separate semantic parser |

Brevitas report mode exits 1 only with B011 because the required table has two
finding rows; evidence precedence and Fiat's one-row-per-finding format forbid
fabricating a third row, so no Brevitas-clean claim is made.

### Evidence

The audited implementation is signed commit
`a36768abf65d4afbcb310f1c231e98866798fbe7`, parent
`68cd65757ada8756a72d4596cb8aaa58f7adec66`; its local Shoggoth signature and
single co-author and origin trailers are good. The tracked study SHA-256 is
`1258efb979883681cc97e850dc9b641dd63f37a0f7beaf5bd5029d705ef76806`
and the tracked runbook SHA-256 is
`21fa5133526f29a57bc7ada26b911c9d41e5d484eaf076a918023f75a53e6fcd`;
both remain byte-identical to their receipted `.hexaemeron` sources.
Repair commit `3d8ef99537ab0ccbf39a9f81d42159b061ba613b` also has a good
local Shoggoth signature and exactly one co-author and one origin trailer.

The exact source runner used CLI report format `unittest-json-v1`. Its red
parent report,
`.elenchus/fiat-runbook-amendments-step-2-round-1-red.json`, has SHA-256
`3ec86c5b210c7f37ae078ed17e92bf8c3adbb3df763b0a17a76e8840f87e8c8d`,
schema `elenchus.unittest.v1`, `complete: true`, 1,019 tests, four assertion
failures, zero errors, and zero skips. The canonical repaired-tree report,
`.elenchus/fiat-runbook-amendments-step-2.json`, has SHA-256
`6deeed2b4b0b58b1c83d57bb03f31362f8c1a86a0826669390a5e59408ceba9a`,
the same schema, `complete: true`, and 1,019/1,019 green with zero errors and
zero skips. Verdict: `guarded`.

Mason's source-runner layout repair is also closed. The preserved early report
`.elenchus/fiat-runbook-amendments-step-2-red.json` has SHA-256
`ad5953059354e3d5b41946caeb8f382e1f41f711df8bcb1187bf45ff4f8de0b2`,
schema `elenchus.unittest.v1`, 931 tests, and one import-context error. The
preserved signed-tree report
`.elenchus/fiat-runbook-amendments-step-2-mason-green.json` has SHA-256
`cd494b76389778edda0015b96069ea84c741bfa00e92f51c816fb6037d85179c`,
the same schema, and 1,015/1,015 green. The bounded fallback import now works
in package and source-runner layouts; the fresh repaired-tree run above remains
green.

The focused Fiat, Protasis, and controller suite passes 473/473; evolution
passes 9/9; root passes 349/349 with five skips; and Hexaemeron passes
1,019/1,019. Promise Machine sync and contract checks are clean across 14
plugins and 14 copies; coverage is 71/71. The six changed controller-digest
bindings in `tests/promise_machine_coverage.json` now equal
`b84075e32d73602eb2e05bb12070845740811008f203e6422497f99827982a6b`;
their field maps are unchanged and no write-mode sync ran. Protasis accepts
both tracked specifications. Phylax, Ephoros, and Hypomnema exit 0;
Imprimatur gives all six specified prose files 100/100 with zero defects;
Horos, `py_compile`, both receipt comparisons, and `git diff --check` exit 0.

### Risk dispositions

- `subject-confusion`: clean. Diagnostics, pending markers, receipts, and ledger events retain one exact subject; legacy study recovery and two-subject refusal stay guarded.
- `prefix-forgery`: clean. A forged byte prefix refuses before durable mutation.
- `amendment-selection`: fixed by S2-R1-01. Fenced decoys, short or mismatched fences, duplicate final blocks, trailing sections, and four-space indented code cannot select or hide a block.
- `field-ambiguity`: fixed by S2-R1-02. The four ordered amendment fields, full replacement clauses, and replacement Exit command presence are checked by Protasis before Fiat mutates.
- `step-verdict-coverage`: clean. Every unbuilt step has one entry-and-exit verdict; unknown and completed steps, omissions, duplicates, and broken current-step verdicts refuse or block as specified.
- `duplicate-step-source`: fixed by S2-R1-01. A packet retains one numbered and titled baseline block; appended, fenced-decoy, and four-space-hidden step headings refuse.
- `effective-step-source`: clean. Mason and Warden receive byte-identical baseline and applicable amendment bytes with matching digests in receipt order, including exact Unicode and whitespace.
- `repair-precedence`: clean. A repair binds the current study digest and step; a later study receipt makes the older repair inapplicable.
- `partial-write`: clean. Each interrupted write window finishes or rolls back once, without duplicate ledger events or mixed receipt state.
- `pending-collision`: clean. One labelled pending marker blocks other commands; two subjects refuse without deleting either marker.
- `checker-binding`: clean. Protasis receives the captured candidate bytes through fixed argv with bounded input and output; non-zero, unsafe-path, and oversized cases refuse before mutation.
- `post-amend-drift`: clean. `next`, `status`, `verify`, source packets, and receipt-history checks recompute digests and refuse unreceipted drift.
- `legacy-recovery`: clean. Version-1 state and subjectless study markers remain readable and recover exactly once.
- `evidence-overclaim`: clean. The `fiat-runbook-amendment` Promise is limited to checked continuity, structure, receipt history, and source carriage; it does not claim replacement truth, command success, or plan correctness.
- `generation-collision`: clean on the recorded base. Fiat is `fiat-v5.21.1` and Protasis is `protasis-v4.7.0`; each adds one generation row while retaining its frontier revision, digest, status, current-frontier text, and next job. No frontier counter moved.
- `elenchus-identifier-swap`: clean by cold review. The role-swapped specimen was refused; the accepted contract names `unittest-json-v1` only as CLI report format and `elenchus.unittest.v1` only as expected JSON schema.
- `audit-record-scope`: clean by cold review. Step 2's Files field names `audit/AUDIT.md` as the append-only Warden exception without widening Mason's product files.

### Qualifications

The fixed parser establishes the accepted structure, not that free-form
replacement prose is a sound criterion or that a named future command will
succeed. No remote signature, push, pull request, integration result, or
GitHub state was checked. The Sapheneia comparison preserves the required
heading and table, both findings, severities, exact locations, commits,
hashes, report roles, counts, verdict, risk dispositions, qualifications,
unknowns, negative results, and lead disposition; it changes no earlier audit
byte and does not claim audit-host enforcement.

Leads not pursued: none.

## Step 2, round 2 -- 2026-08-24

Finding count: 0. Audit filter declaration:
`--audit-filter sapheneia:sapheneia`. The Solidity security suite remains
waived because the audited range contains Python, Markdown, and JSON only.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Brevitas report mode exits 1 only with B011 because the required table has zero
finding rows; evidence precedence and Fiat's one-row-per-finding format forbid
fabricating a row, so no Brevitas-clean claim is made.

### Evidence

This round re-audited the complete fixed tree at signed tip
`2acea79bb16225ffe9028e776dbfbed7b375ff1c`. The implementation
`a36768abf65d4afbcb310f1c231e98866798fbe7`, mechanism fix
`3d8ef99537ab0ccbf39a9f81d42159b061ba613b`, and round-1 audit commit all
have good local Shoggoth signatures and exactly one required co-author and one
origin trailer. Round 1's receipt records two findings, fixes tip
`2acea79bb16225ffe9028e776dbfbed7b375ff1c`, Elenchus `guarded`, all three
lint exits 0, and the two verified local commits. Its append remains unchanged.

All four round-1 guards pass directly: Fiat refuses both the commandless
replacement Exit and the four-space-hidden step heading without mutation or
carriage, and Protasis independently refuses both forms. The parent red report
`.elenchus/fiat-runbook-amendments-step-2-round-1-red.json` retains SHA-256
`3ec86c5b210c7f37ae078ed17e92bf8c3adbb3df763b0a17a76e8840f87e8c8d`,
schema `elenchus.unittest.v1`, 1,019 tests, four failures, zero errors, and zero
skips. The fixed report `.elenchus/fiat-runbook-amendments-step-2.json` retains
SHA-256
`6deeed2b4b0b58b1c83d57bb03f31362f8c1a86a0826669390a5e59408ceba9a`
and 1,019/1,019 green. The runner contract still labels
`unittest-json-v1` as the CLI report format and `elenchus.unittest.v1` as the
expected JSON schema. This round changed no product or guard, created no new
report, and therefore carries no fixes commit and `elenchus_verdict: null`.

The focused Fiat, Protasis, and controller suite passes 473/473; evolution
passes 9/9; root passes 349/349 with five skips; and Hexaemeron passes
1,019/1,019. Promise Machine sync and contract checks are clean across 14
plugins and 14 copies; coverage is 71/71. The six Fiat controller bindings
still carry digest
`b84075e32d73602eb2e05bb12070845740811008f203e6422497f99827982a6b`
with unchanged field maps. The receipted study and runbook still match tracked
SHA-256 values
`1258efb979883681cc97e850dc9b641dd63f37a0f7beaf5bd5029d705ef76806`
and `21fa5133526f29a57bc7ada26b911c9d41e5d484eaf076a918023f75a53e6fcd`.
Protasis accepts both. Phylax, Ephoros, and Hypomnema exit 0; all six specified
Imprimatur runs score 100/100 with zero defects; Horos, `py_compile`, both
receipt comparisons, and `git diff --check` exit 0.

Fiat remains `fiat-v5.21.1`, frontier `state-shape-validation`, digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`,
status `open`, with issue 363 as its next job. Protasis remains
`protasis-v4.7.0`, frontier `amendment-block-check`, digest
`1014071026a149d38e7d79c222dfcfc25dd061d825fac9e7813a3a46b184cd29`,
status `open`, with its held amendment-block check as the next job. The two
generation rows preserve those held fields.

### Risk dispositions

- `subject-confusion`: clean. Subject-labelled diagnostics, markers, receipts, and events remain distinct; legacy and two-subject recovery guards pass.
- `prefix-forgery`: clean. Exact-prefix mismatch still refuses before mutation.
- `amendment-selection`: clean after S2-R1-01. Only CommonMark fences with at most three leading spaces affect selection; decoys, duplicate blocks, and trailing sections refuse.
- `field-ambiguity`: clean after S2-R1-02. Protasis owns the four fields, full replacement clauses, and replacement Exit command-presence rule before Fiat mutates.
- `step-verdict-coverage`: clean. Every unbuilt step has one complete verdict; unknown, completed, missing, duplicate, and broken cases remain guarded.
- `duplicate-step-source`: clean after S2-R1-01. Packets retain one numbered and titled baseline; visible appended or indented-code step headings refuse.
- `effective-step-source`: clean. Mason and Warden receive the same exact baseline and applicable digest-matched amendment bytes in receipt order.
- `repair-precedence`: clean. Current study digest and step remain required, and later study receipts invalidate older repairs.
- `partial-write`: clean. Every interruption window finishes or rolls back once without mixed state or duplicate ledger events.
- `pending-collision`: clean. One marker blocks other commands and two subject markers refuse without deletion.
- `checker-binding`: clean. Captured bytes reach Protasis through fixed argv and bounded I/O; checker failure, unsafe path, and oversize refuse before mutation.
- `post-amend-drift`: clean. Status, next, verify, packets, and receipt-history checks refuse unreceipted byte drift.
- `legacy-recovery`: clean. Version-1 state and subjectless study markers remain readable and recover once.
- `evidence-overclaim`: clean. The Promise remains limited to continuity, structure, receipt history, and source carriage, not truth or future command success.
- `generation-collision`: clean on the recorded base. Both generation labels and all held frontier fields remain internally consistent and unchanged by the audit fixes.
- `elenchus-identifier-swap`: clean by cold review. Format and schema retain their separate labelled roles in the source-bound Step 2 contract.
- `audit-record-scope`: clean by cold review. Both round records use only the append-only `audit/AUDIT.md` exception; Mason's product scope is not widened.

### Qualifications

The round establishes no semantic correctness for free-form replacement prose,
future command success, remote signature, push, pull request, integration
result, GitHub state, or audit-host enforcement. The Sapheneia comparison
preserves the zero finding count, required empty table, date, identifiers,
paths, hashes, roles, counts, prior verdict, current null verdict, all 17 risk
dispositions, qualifications, unknowns, negative results, and lead disposition;
it changes no earlier audit byte.

Leads not pursued: none.

## Capture receipt binding, step 1, round 1 -- 2026-08-24

Non-Solidity round over the two Markdown documents step 1 commits, at
`3dbabca3f87a5dd542fc0f49d04cbede60de1742`. Zero findings.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over both new documents and over the required tree
`README.md AGENTS.md .agents plugins docs`. Protasis accepts the study in
`--study` mode and the runbook in runbook mode. Imprimatur reports no defect on
either, both scoring 100.0. Horos reports the boundary matches the tree, so
`.horos/boundary.json` stands unchanged. The Hexaemeron suite passes 962/962.
The commit's local signature is good and it carries exactly one co-author and
one origin trailer.

The root suite needs stating precisely, because this step's exit criterion was
written before the receipts it describes existed. In a clean worktree of
`3dbabca` it reports 345 tests, `OK (skipped=5)`, which is the criterion as
written. In this run's own worktree the same command reports 5 failures, every
one of them `tests/test_run_observation_capture.py` reading this delivery's
`.hexaemeron/study.md` and `.hexaemeron/runbook.md` instead of issue 435's. That
is issue 574 itself, the defect step 2 removes, and it shows up at step 1
because writing a study and a runbook is what creates it. The tracked tree meets
the exit and the run worktree cannot. No amendment was made: the criterion is
right about the artefact the step delivers, and the run worktree figure is the
reproduction step 2 starts from.

Two register concerns are reachable at this step and both were checked.
`digest-transcription`: both digests the study quotes,
`6858aaeadb12f204538b9120e51390b9c940fa995c8edb1471815d89aaa7f404` and
`56df27b7faae2af8f7ba16ec89526413038def6a0bbf86ff0274dc566f8bf9c5`, appear
byte-identical in `tests/test_run_observation_capture.py`, and the base SHA the
study states matches the run's recorded base `7f4264ecc26ac2149ddb99834433bee3b5dd9fdc`.
`untracked-path-read`: the step changes no code, so every read in the module is
byte-identical to the entry state. The other four concerns, `weakened-claim`,
`guard-map-drift`, `dormant-skip` and `subprocess-argv`, sit in step 2's diff
and are not yet reachable.

Brevitas is recorded rather than gated: clean on the study, B010 and B001 on the
runbook, which a two-step specification cannot satisfy. The shipped
`docs/hypomnema-quoted-specimen-runbook.md` carries the same two codes on `main`.

Leads not pursued: none.

## Capture receipt binding, step 2, round 1 -- 2026-08-24

Non-Solidity round over the test rebinding at
`4141b8593e9c568f9e01d04c2dbd70ebd228f599`. Zero findings.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over the required tree `README.md AGENTS.md .agents plugins docs`.
Horos reports the boundary matches the tree. `promise_machine.py` reports clean
on `coverage --check`, `check` and `sync --check` after the module's recorded
digest moved to
`cb2eb238380a216033f115a23398c18072ad1f227113aae97b57a4bb74c05b74`. The Elenchus
reporter exits 0 with 0 failures, 0 errors and 0 skipped. The root suite reports
345 tests OK with no skips, where the same command reported 5 failures at the
step's entry. The Hexaemeron suite passes 962/962. The commit's local signature
is good and it carries exactly one co-author and one origin trailer.

All six register concerns are reachable at this step and each was checked.
`weakened-claim`: appending one byte to
`docs/promise-machine/run-observation-capture-study.md` fails four of the five,
and appending the two-byte sequence `5c 6e` to the runbook copy fails the fifth,
so each assertion still bites on the artefact it now reads.
`guard-map-drift`: the union-manifest test passes, so all twenty-three carryover
ids still name a test that exists, R9-01 among them under its new name
`test_receipt_assertions_never_read_a_live_run_path`.
`dormant-skip`: the module reports 0 skipped, and the one remaining `skipTest`
is the class setUp's guard for a detached parent worktree with no capture
runtime, which is a real absence rather than a path a live run owns.
`digest-transcription`: both recorded digests are unchanged from the entry state
and each equals the recomputed hash of its tracked copy, which is what two of
the five now assert.
`untracked-path-read`: the module carries no live-run state read at all, down
from ten lines at the step's entry, and the new guard makes that a standing
assertion rather than a one-time check.
`subprocess-argv`: two subprocess calls remain, the `git show` in the
newline-escape test and the `elenchus.py --help` in R1-08, both argv lists, with
no `shell=True` anywhere in the module.

One deviation from the runbook's stated method. Its Tests field said the
mutation proof would run against a copy in a temporary directory. It ran against
the tracked copies in the worktree instead, restored with `git checkout --` after
each of the two mutations, with `git status --short docs/` empty afterwards. The
proof is the same and the tree is where it started, but the method is not the one
the step named.

Leads not pursued: none.

## Where the rounds after this one are

Every run appended here, from a literal default in the Fiat controller. That put
this file in `done sync-run`'s overlap set on every integration where anything
else had merged, so a run that had only appended to it still owed a green check
over it. `fiat-v5.22.1` derives `audit/rounds/<run branch with separators
flattened>.md` at `init` instead, one record per run.

This file keeps every round written before that change and takes no new ones.
Nothing above this line was edited. The reasoning is in
[ADR-025](../docs/decisions/ADR-025-give-each-fiat-run-its-own-audit-record.md),
and Protasis item 2 tells a study to read both.

## Step 1, round 1 -- 2026-08-24

Zero findings.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

The audited range is
`08512d4ada7b1d7418e1af213be0d4b8c1494b6d..da5069195737aa17ece2ba9ebc448b6072b951cf`
on `fiat/controller-currency-guarantee-step-1-publish-the-accepted-controller`.
One commit; its parent is the run branch tip and the study's stated starting
ref. It adds only `docs/fiat-controller-currency-study.md` and
`docs/fiat-controller-currency-runbook.md`, both regular non-executable
files. Both are byte-identical to their receipted sources: `cmp` against
`.hexaemeron/study.md` and `.hexaemeron/runbook.md` exits 0 for each, the
study SHA-256 is
`ebc957fd8570d36f39b2e1597d09f61369498c390b9f4ef7a2158d7ed764cbee`, and the
runbook SHA-256 is
`964e52909a0e91951069d6d0e83032b5e04e6baa853b2544747604912ad46a7c`. The
runbook's embedded source receipt quotes that same study digest, starting
ref, and run branch. The study's five relative links resolve from `docs/` to
the elenchus, ephoros, hypomnema, metron, and phylax `SKILL.md` files, and
the runbook carries no relative link. Step 1's Files field permits
`audit/AUDIT.md` solely for append-only Warden round records, so this append
stays inside the implementation boundary.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and
`tests`, Hypomnema over `README.md AGENTS.md .agents plugins docs`. Protasis
exits 0 on the study in `--study` mode and on the runbook. Imprimatur exits 0
on each, score 100.0/100 with zero defects; its runbook output lists only
known-false-positive and cadence signals. Horos reports `boundary matches the
tree`, so the untouched `.horos/boundary.json` is correct. `git diff --check`
over the range exits 0. The root suite passes 349/349 and the Hexaemeron
suite passes 1019/1019, each at exit 0. The security suite stays waived: no
Solidity in scope, and this range is Markdown only. The commit has a good
local Shoggoth signature and exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one
`Wildcat-Origin: shoggoth` trailer. No Elenchus repair report was created and
no Elenchus verdict applies to this zero-finding round.

Two of the study's internal citations were spot-checked: `audit/AUDIT.md`
line 11977 carries the `controller_version` lead driving installed
`fiat-v5.14.1` against repository `fiat-v5.15.1`, as the study quotes it, and
`I320-S3-R2-01` exists as the `ls-remote` parsing record.

Eight register ids are not reachable in this docs-only range and remain owed
to their steps: `upstream-read-surface`, `url-source-confusion`,
`registry-hostile-input`, `route-misdetection`, and `state-compat` sit in
step 2's controller work; `repin-partiality` sits in step 3;
`ledger-arithmetic` and `version-propagation` sit in step 4. This round makes
no claim about their implementation. The other four are reachable at
specification level and were reviewed. `verdict-honesty`: both documents keep
`behind` and `unknown` distinct at every occurrence -- the study's option B,
glossary, and fail-closed section, and the runbook's step 2 exit conditions 1
and 4. `waiver-visibility`: the flag, the recorded reason, and the runbook's
empty-reason refusal agree across both documents. `secret-echo`: neither
document carries a credentialed URL, raw child output, or registry bytes, and
the only remote URL quoted is the public marketplace origin.
`bootstrap-limit`: the study states the gate governs runs after the next
re-pin, and the runbook's step 4 exit condition 1 binds `plugin-currency.md`
to state both limits. The implementations of all four remain owed where the
runbook places them.

Qualification: this round establishes publication fidelity and tree health,
not step 2 to 4 behaviour, remote signature verification, push, pull request,
or integration state.

The Sapheneia durable-record comparison preserved the heading, the empty
finding table, the zero count, the date, every identifier, path, digest,
exit code, suite count, and quoted token, all twelve register dispositions,
the qualification, and the lead disposition item by item. It changes no
existing audit byte.

Leads not pursued: the study's three external links (issue 363, pull requests
583 and 585) were not fetched, and its 2026-08-24 host-state measurements
under `~/.claude/plugins` describe a host outside the tracked tree and were
not re-measured; both stand as receipted study claims. No other lead was
found.

## Step 2, round 1 -- 2026-08-24

Two findings, both fixed on the stacked branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | `hexctl record controller_currency` replaced the init-written provenance receipt in state with an arbitrary value; `verify` stayed green afterwards and the honest values survived only in the init transition, while `task_issue`, the other init-written receipt, already had an immutability guard | fixed |
| S2-R1-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | a git-pinned install whose marketplace clone is missing read route and verdict `managed` with the pin recorded and no warning, so deleting one directory silenced the gate without a trace, against the study glossary (pin absent on the managed route) and the verdict-honesty control (an unobservable head warns) | fixed |

The audited range is
`f97b10a90e69db3c2e48a42680967ec1fcc7137f..d113c06b7eb267e1aade53d81a3c0ad940e7a72a`
on `fiat/controller-currency-guarantee-step-2-observe-controller-currency-at-i`,
two commits: `068a8da2bbd66c6f04c36cdc596d059115114dcc` adds the observation,
the init gate, the waiver flag, the `test_hexctl_currency.py` suite, the
shared fake-git `ls-remote` log hook in `test_hexctl.py`, and the six
refreshed digest pins; `d113c06b7eb267e1aade53d81a3c0ad940e7a72a` adds
ADR-033. Both commits have a good local Shoggoth signature and exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one
`Wildcat-Origin: shoggoth` trailer. The range touches only files the amended
Step 2 Files boundary names; this append and the fixes stay inside it too.

Six-pin note, recorded as directed: the coverage refresh in `068a8da2`
changed six `hexctl.py` digest pins in `tests/promise_machine_coverage.json`
-- five `runtime.*` rows plus `run_observation_binding.controller.sha256` --
where the amendment's Why field counted five. The Files clause ("refreshed
runtime digests only") governs, and all six are digests of the same runtime
file: the JSON diff replaces only sha256 values on `hexctl.py` rows, 12
changed lines, nothing else, from
`b84075e32d73602eb2e05bb12070845740811008f203e6422497f99827982a6b` to
`7a629f691cc65c588dbdd9ee22392a0a61e9371f9581dd30688f230cd549be54`, and the
new value equals the file's digest at both commits. The fixes commit
refreshes the same six pins again to
`43ee3e565d20a41fab4df1c8b417ec562828e73c008199ff416fe2538e1c50f5` for the
repaired controller bytes.

Mechanical results, re-run on the fixed tree after a session interruption so
every number below is from a completed run: Phylax, Ephoros (each over
`plugins tests`) and Hypomnema (over `README.md AGENTS.md .agents plugins
docs`) all print `clean` and exit 0, both before and after the fixes. The
Hexaemeron suite passed 1037/1037 at the step tip and passes 1039/1039 with
the fixes; the root suite passes 349/349 at both points. Imprimatur exits 0
on ADR-033 at score 100.0/100 with zero defects. Horos reports `boundary
matches the tree` and `git diff --check` exits 0 over the range and after
the fixes. The security suite stays waived: no Solidity in scope; the range
changes the Python controller, tests, one JSON fixture and one ADR.

The Elenchus convention was checked directly: with the
`observe_controller_currency()` call neutralised in `cmd_init`, the three
sampled guards (behind refusal, waiver receipt, current provenance) fail
3/3, and the tree was restored byte-clean afterwards. The suite carries 18
gate tests at the step tip, six beyond the required twelve, and 20 after
the fixes.

Fixes: one commit, `561252ff2f287e72c4e339f81ed921cb62cc75fc` on
`fiat/controller-currency-guarantee-step-2-observe-controller-currency-at-i--audit`,
referencing both finding ids, signed with a good Shoggoth signature and the
two trailers. S2-R1-01: `cmd_record` now refuses the `controller_currency`
key by name, as it already did for `task_issue`, with a guard test that
drives the CLI. S2-R1-02: only a pin-absent record classifies as `managed`;
a recorded pin with a missing clone now reads route `git-backed`, verdict
`unknown`, warning `clone-missing`, pin recorded and head an explicit null,
with a guard test; the managed-route test now models a true pinless managed
install and additionally asserts `pin` null with the clone present but
unread. The source-bound Elenchus runner was invoked exactly as Step 2
declares it -- test command `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, format `unittest-json-v1`, report file
`.elenchus/fiat-controller-currency-step-2.json`, fresh path inside the
runner's detached parent worktree -- against the fixes commit. Its verdict
is `guarded`: the parent report is complete, 1039 tests executed, exactly
the two new guards fail as assertions, zero errors, zero skips.

Risk-id dispositions for this range:

- `upstream-read-surface`: holds. The one `ls-remote` runs argv-fixed
  (`ls-remote --refs origin refs/heads/<branch>`), shell-free, with
  `GIT_TERMINAL_PROMPT=0` (witnessed by a test), `GIT_TIMEOUT` and the
  output cap through `bounded_probe`, and the URL-confinement test proves
  exactly one read at init. Failure vocabulary is fixed
  (`remote-start|timeout|output-cap|failed|malformed`); no child byte
  reaches any diagnosis, transition or receipt.
- `url-source-confusion`: holds. The read runs with cwd inside the
  marketplace clone naming remote `origin`; no URL string passes through
  controller code, and a hostile target-repository `url.insteadOf` rewrite
  is proven inert by test. The plugins root derives from
  `os.path.realpath(__file__)`, which also normalises `..`, so no registry
  or environment value can steer the directory; a crafted `installPath` is
  only string-compared, never opened or followed.
- `registry-hostile-input`: holds. Missing, oversized (1 MiB cap),
  malformed, wrong-kind and unmatched registries each read `unknown` with a
  named warning, by test; a non-hex pin reads
  `unknown`/`registry-pin-malformed` and mixed-kind entries are skipped, by
  direct probe; nothing echoes registry bytes. Multiple matching install
  records resolve first-match in registry order, deterministically.
- `route-misdetection`: S2-R1-02 found here and fixed. Cache-split
  precedence over the in-repo check is deterministic when both conditions
  hold; an unmatched install path reads `unknown` per test; the deepest
  `cache` ancestor with marketplace, plugin and version components decides,
  and a wrong split degrades to `registry-missing`, never a verdict.
- `verdict-honesty`: holds with the S2-R1-02 repair. `behind` requires a
  validated pin and one well-formed observed head that differ; every
  `unknown` path returns before the comparison, so `unknown` cannot promote;
  a malformed remote line, wrong ref, duplicate line, non-SHA and empty
  answer each read `remote-malformed` by test. A waiver passed when the
  verdict is not `behind` is recorded verbatim beside the true verdict --
  the receipt stays honest about both.
- `waiver-visibility`: holds, strengthened by S2-R1-01. An empty reason is
  refused by test; a waived init records verdict `behind` and the reason;
  no other flag or environment value silences the gate; and the receipt can
  no longer be rewritten after init, so the ledger and the receipt now
  agree durably.
- `secret-echo`: holds. The refusal states only the two validated hex SHAs
  the exit condition requires; warnings come from a closed vocabulary; the
  behind-refusal test asserts no `https://` reaches stderr and the
  confinement test asserts no URL reaches the receipt.
- `state-compat`: holds. The compat test strips the receipt from state and
  the init transition, re-fingerprints and re-hashes the ledger entry, then
  drives `status`, `verify` and `next` through the CLI at exit 0 -- real
  `load_state` and `verify` paths, not a JSON reload.
- `bootstrap-limit`: reviewed at its documentation surface: ADR-033 states
  the gate ships inside the artifact it gates and governs runs after the
  next re-pin. The reference and SKILL text land in step 4; no claim here.
- `repin-partiality` sits in step 3, `ledger-arithmetic` and
  `version-propagation` in step 4: not reachable in this range, no claim.

The `bounded_run` refactor preserves every existing caller: `bounded_run`
now wraps the non-dying `bounded_probe` core, the three refusal messages
(`could not start`, `timed out after {GIT_TIMEOUT} seconds`, `exceeded
{GIT_OUTPUT_MAX}-byte output cap`) are byte-identical at the same exit 2,
the returncode passes through unchanged, and `env=None` inherits the parent
environment exactly as before, so `bounded_tool`, `bounded_tool_status`,
`bounded_git` and the publishable-versions `git show` reader keep their
refusal semantics; the full green suites at both ends carry the regression
evidence. The `branch_name_ok` extraction keeps `check_branch_name`
behaviour identical and gives the clone-HEAD read the same conservative
refname subset, which also keeps a leading-dash argv confusion out of the
`ls-remote` call because the passed ref always begins `refs/heads/`.

Qualification: this round establishes the audited range's behaviour under
the study's boundary controls and the fixes above, not step 3 or 4
behaviour, remote signature verification, push, pull request, or
integration state. The Elenchus line records the runner's declared result;
it does not attest the report bytes.

The Sapheneia durable-record comparison preserved the heading, the finding
table with both ids, severities, files and statuses, the audited range,
branch and three commit SHAs, all four digests, the six-pin count and
12-line measurement, every exit code, all four suite counts, the 3/3
spot-check, the 18/20 test counts, the Elenchus contract tokens and
`guarded` verdict with its counters, all twelve register dispositions, the
qualification, and every lead below, item by item. The comparison caught one
mismatched number in the draft -- the gate-test tally, drafted 17/19 against
the measured 18/20 -- which was corrected before this append. It changes no
existing audit byte.

Leads seen and not pursued: the `registry-pin-malformed` branch has no
dedicated suite guard (probed by hand here, reads `unknown`); `COMMIT_RE`
accepts 64-hex object-format pins alongside 40-hex, consistent with the
codebase-wide validator and still hex-bounded, though the amendment's test
list says "not 40-hex"; a hostile registry record with a crafted
`installPath` prefix such as `/` can supply the pin for any file, which
stays inside the registry's existing authority over pin values and is never
echoed or dereferenced; `bounded_probe` inherits stdin as every
`bounded_run` caller always has, bounded by the timeout; and a clone whose
`.git/HEAD` is detached or unreadable reads `clone-head-unreadable` by
probe, without a dedicated suite guard. None of these changes a verdict or
crosses a boundary; they stand for a later round or step.

## Step 2, round 2 -- 2026-08-24

Zero findings.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

The audited range is
`d113c06b7eb267e1aade53d81a3c0ad940e7a72a..fb98d4da595070ec3533f6cabdf30e59355653b0`
on
`fiat/controller-currency-guarantee-step-2-observe-controller-currency-at-i--audit`,
two commits: `561252ff2f287e72c4e339f81ed921cb62cc75fc` carries the round 1
fixes for S2-R1-01 and S2-R1-02 with their guard tests and the six digest
pins refreshed to
`43ee3e565d20a41fab4df1c8b417ec562828e73c008199ff416fe2538e1c50f5`, and
`fb98d4da595070ec3533f6cabdf30e59355653b0` appends the round 1 record to
`audit/AUDIT.md` and touches nothing else. Both commits have a good local
Shoggoth signature and exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one
`Wildcat-Origin: shoggoth` trailer. This round re-audits the two repairs on
the fixed tree.

The S2-R1-01 repair breaks no legitimate record path: the only writers of
the `controller_currency` key are init's receipt and init transition, a
search across `plugins/hexaemeron/skills`, `docs` and `README.md` finds no
flow that directs `hexctl record controller_currency`, and the refusal sits
after the phase-receipt check and before the `halt_note` and `task_issue`
handling, which keep their behaviour. The refusal message is one fixed
string with no interpolated value.

The S2-R1-02 repair reads honestly on every side. A pinned install with the
marketplace clone missing warns on stderr with the pre-existing unknown
sentence naming `clone-missing` and stating that the receipt records the
nulls rather than a verdict, so the wording claims neither `current` nor
`behind`; the guard test pins the receipt to route `git-backed`, verdict
`unknown`, warning `clone-missing`, the pin recorded and the head an
explicit null, with no network read. The rewritten managed fixture is a true
pinless install: `gitCommitSha` null classifies `absent`, the receipt
asserts `pin` null, and the clone is present but unread.

The four risk ids the fixes touched were re-checked on the fixed code.
`verdict-honesty`: the `clone-missing` path returns before the comparison,
and the only verdict assignments remain `no-pin`, `managed` on a pin-absent
record, `current`/`behind` after one validated head, and `unknown`
everywhere else. `route-misdetection`: `git-backed` now follows the
registry's recorded pin, matching the study glossary, and the cache-split
precedence is unchanged. `registry-hostile-input`: registry parsing is
untouched by the fixes and its named-warning vocabulary is unchanged.
`secret-echo`: the two new strings -- the `clone-missing` warning token and
the record refusal -- are fixed vocabulary with no value bytes.

Mechanical results for this round: Phylax, Ephoros (each over `plugins
tests`) and Hypomnema (over `README.md AGENTS.md .agents plugins docs`) all
print `clean` and exit 0. The Hexaemeron suite passes 1039/1039 and the root
suite passes 349/349. Horos reports `boundary matches the tree` and `git
diff --check` exits 0 over the range. The security suite stays waived: no
Solidity in scope, unchanged from round 1. No repair was made this round, so
no Elenchus report was created and no Elenchus verdict applies.

Qualification: this round establishes that the round 1 repairs hold on the
fixed tree and that the tree is healthy, not step 3 or 4 behaviour, remote
signature verification, push, pull request, or integration state.

The Sapheneia durable-record comparison preserved the heading, the zero
count, the empty finding table, the date, the range, branch and both commit
SHAs, the refreshed digest, both finding ids named as context with their
held repairs, every exit code and suite count, all four re-checked register
dispositions, the qualification, and the lead line below, item by item. It
changes no existing audit byte.

Leads not pursued: the five recorded at round 1 stand unchanged --
the unguarded `registry-pin-malformed` branch, the 64-hex pin acceptance,
the crafted `installPath` prefix inside the registry's existing authority,
`bounded_probe` stdin inheritance, and the unguarded `clone-head-unreadable`
branch. No new lead was found this round.

## Step 3, round 1 -- 2026-08-24

One finding, fixed on the stacked branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | a plugin key or version carrying control bytes forged extra `hexctl currency` text lines -- a demonstrated fabricated row reading as another plugin's all-clear verdict -- while the exit code and `--json` stayed honest | fixed |

The audited range is
`79a1df75719c44882847ef130f79b43b2bdf95d0..014b1c5f83801058a71bc4ced1cd95aea75630fa`
on `fiat/controller-currency-guarantee-step-3-expose-the-currency-observation`,
two commits: `75107d7cf3a162011caccd8675e7fe5febf81406` adds the read-only
`hexctl currency [--json]` subcommand, the `currency_report` core, three
extractions of the step 2 reads, the per-report remote memo and seven guard
tests, with the six digest pins refreshed;
`014b1c5f83801058a71bc4ced1cd95aea75630fa` names the re-pin boundary in the
Kronos loop text. Both commits have a good local Shoggoth signature and
exactly one `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer
and one `Wildcat-Origin: shoggoth` trailer. The range touches only files the
amended Step 3 Files boundary names; the fix and this append stay inside it.

Six-pin note: the refresh replaces only sha256 values on the same six
`hexctl.py` rows as step 2 -- five `runtime.*` rows plus
`run_observation_binding.controller.sha256` -- 12 changed lines, from
`43ee3e565d20a41fab4df1c8b417ec562828e73c008199ff416fe2538e1c50f5` to
`b00e525ef023dd2bf516197bcdd905e5bb4bbe653da41d4669af300eebe7ecc4`, and the
new value equals the file's digest at both range commits. The fixes commit
refreshes the same six to
`ccc703a00792f0447a1a4d8ab7d04ac2853229ae8897fc7b5392a184f9aa4495`.

Extraction compatibility: `currency_registry_load`, `currency_record_pin`
and `currency_pin_observation` re-host the step 2 logic line-faithfully --
the bounded registry read with its four named failure kinds, the per-record
pin answer including `registry-pin-malformed`, and the
managed/git-backed/`clone-missing` tail carrying the S2-R1-02 semantics and
comment. All twenty step 2 guards run green through the refactor, first-match
multi-record resolution is unchanged in `currency_registry_pin`, and a direct
probe of defective records through the new report path reads `unknown` rows
with fixed warnings (`registry-wrong-kind` for a non-list value, an empty
list and a non-dict record; `install-path-unrecognised` for a path outside
the derived root) while the plugin never vanishes from the report.

Read-only honesty: `cmd_currency` is absent from `MUTATING`, so the
dispatcher runs it without `held_lock`, whose directory creation is
init-only besides; the refusal paths go through `die`, which writes nothing;
and the mixed-verdict guard asserts no `.hexaemeron` exists after a report.
No lock, state, or breadcrumb is possible on any path.

The dedup memo is per-report, keyed on (clone directory, branch): fourteen
plugins over two marketplaces cost exactly two reads by test, asserted on
realpath'd clone directories, so no cross-marketplace head can label another
marketplace's row. A memoized failure is (null, warning), so poisoning can
only mark same-origin rows `unknown` with the named warning, never mint a
`current` or `behind`; each row compares its own registry pin against the
shared head.

Exit-code honesty: a registry that cannot answer at all refuses at exit 1
with empty stdout (missing and malformed both tested), a controller outside
an install cache refuses at exit 1 (tested), one hostile record is a
row-level `unknown` (tested via the malformed pin), exit 3 while anything is
behind and 0 when nothing is (both tested). The refusal/row boundary is
principled and stated in the docstring: an empty success would read as a
fleet with nothing behind.

The superset call is recorded in the docstring and matches behaviour: every
install record gets a row because filtering by a hard-coded marketplace name
would blind the report on a private-mirror host; the wildcat-labs
requirement is satisfied as a subset, and each row's marketplace is derived
from its own realpath'd `installPath` under the controller's derived plugins
root or the row reads `install-path-unrecognised`. The warning field is a
closed vocabulary with no URL or registry byte; row identity fields (plugin,
version) are the report's spec-required subject, and S3-R1-01 closed the one
channel where their bytes could forge report structure.

Kronos: the re-pin text sits at the rescan boundary of loop step 8, before
"Then rescan the entire scope from disk", runs `hexctl currency`, loops
while exit 3 reinstalling through the host's own installer, refreshes and
re-resolves paths, and cites `../fiat/references/plugin-currency.md`, which
resolves; it contradicts neither the `pull`/`push` state rules, which govern
`kronos.py` subcommands, nor phase-only mode, which runs the same loop over
a narrower scope. Imprimatur on the changed `SKILL.md` exits 0 at 100.0/100
with zero defects, listing only known-false-positive and cadence signals.

Mechanical results: Phylax, Ephoros and Hypomnema print `clean` and exit 0
at the step tip and again on the fixed tree. The Hexaemeron suite passes
1046/1046 at the tip and 1047/1047 with the fix; the root suite passes
349/349 at both points. Horos reports `boundary matches the tree` and
`git diff --check` exits 0 over the range and on the fixed tree. The
security suite stays waived: no Solidity in scope; the range changes the
Python controller, its tests, one JSON fixture and one skill's loop prose.

Fix: one commit, `61ddcfe32c05fc81c9be509db8c25a39e7fdb85d` on
`fiat/controller-currency-guarantee-step-3-expose-the-currency-observation--audit`,
signed with a good Shoggoth signature and the two trailers: text mode renders
every row field through one helper that maps control bytes to `?`, leaving
`--json` and the exit contract as the machine surfaces, with a guard test.
The source-bound Elenchus runner was invoked exactly as Step 3 declares it --
test command `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, format `unittest-json-v1`, report file
`.elenchus/fiat-controller-currency-step-3.json`, fresh inside the runner's
detached parent worktree -- against the fixes commit. Its verdict is
`guarded`: the parent report is complete, 1047 tests executed, exactly the
one new guard fails as an assertion, zero errors, zero skips.

Risk-id dispositions for this range: `repin-partiality`, the step's
headline, holds at its report half -- every install record is a row across
the fourteen-plugin fleet by test, one bounded read per distinct origin by
test, exit 3 gates the loop, and the Kronos text reinstalls everything
behind -- while the operational half, the next init receipt evidencing the
new pin, is stated in prose and owed to operation, with no claim here.
`verdict-honesty` holds: rows reuse the init observation's verdict logic,
a hostile pin is a row-level `unknown`, and a refusal replaces the empty
all-clear. `secret-echo` holds with the S3-R1-01 repair; the refusal
interpolates only the fixed warning token. `upstream-read-surface` holds:
the memo wraps the same bounded `currency_remote_head` with no new argv
shape. `url-source-confusion` holds: no target-repository or environment
value reaches routing; the marketplace comes from the record's install path
confined under the derived root. `registry-hostile-input` holds: the
load/record split keeps the named-warning contract at both granularities.
`route-misdetection` and `state-compat` are unchanged by this range and
their step 2 evidence stands; `waiver-visibility` and `bootstrap-limit` are
not reachable here; `ledger-arithmetic` and `version-propagation` sit in
step 4, no claim.

Qualification: this round establishes the subcommand's behaviour, the
refactor's fidelity and the loop text's placement, not the reinstall
operation itself, step 4 behaviour, remote signature verification, push,
pull request, or integration state. The Elenchus line records the runner's
declared result; it does not attest the report bytes.

The Sapheneia durable-record comparison preserved the heading, the finding
with its id, severity, file and status, the range, branch and three commit
SHAs, all three digests, the six-pin and 12-line measurements, every exit
code, all four suite counts, the two-read memo evidence, the guard tallies,
the Elenchus contract tokens and `guarded` verdict with its counters, all
twelve register dispositions, the qualification, and every lead below, item
by item. It changes no existing audit byte.

Leads seen and not pursued: a well-formed registry whose plugins map is
empty yields zero rows at exit 0, an all-clear a lying-but-valid registry
could stage, inside the registry's existing authority (the unreadable case
refuses); a space inside a plugin name shifts text columns without forging
lines, and `--json` is the parse surface; the defective-record row shapes
and the empty-plugins case above were probed by hand but carry no dedicated
suite guard; a fleet with unknowns and nothing behind exits 0 by
construction without a dedicated guard; and the step 2 leads stand as
recorded. None of these changes a verdict or crosses a boundary.

## Step 3, round 2 -- 2026-08-24

One finding, fixed on the stacked branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | the round 1 sanitizer mapped only C0 controls and DEL, so a Unicode line or paragraph separator in a plugin key still forged a text row for any `splitlines` consumer, and a lone surrogate in a registry value crashed `hexctl currency` text mode mid-report with a raw `UnicodeEncodeError` traceback at exit 1 -- the hostile-registry traceback the study contract names -- both demonstrated end to end | fixed |

This round re-audits round 1's fix commit
`61ddcfe32c05fc81c9be509db8c25a39e7fdb85d` on
`fiat/controller-currency-guarantee-step-3-expose-the-currency-observation--audit`,
entered at `63adaf8c1d2416e4b900cb489d76f35965f42fd3` with both suites green
(1047/1047 and 349/349) and all three lints at exit 0.

The regression audit of `currency_text_field` found the finding above and
otherwise holds. Byte-for-byte preservation was probed directly: plugin
slugs, semver strings, 40-hex SHAs, every verdict and route token, and the
`null` rendering pass unchanged through the old and new predicate alike.
`--json` stays byte-honest and crash-free: `json.dumps` under its default
ASCII escaping carries raw registry values, a lone surrogate included, which
the new guard asserts by reading the hostile value back from the JSON rows.
No other text-rendering path in the step 3 code prints registry bytes: the
two refusal messages and every warning token are fixed vocabulary.
`secret-echo` and `verdict-honesty` hold on the fixed rendering because the
sanitizer is display-only -- verdicts, rows and the exit code are computed
before any rendering, and the JSON surface is untouched.

The repair replaces the byte-class predicate with printability: every
non-printable character renders as `?`, which a direct probe shows inert for
NEL, the line and paragraph separators, the bidi override, the zero-width
space, the no-break space and a lone surrogate, while every legitimate value
above passes byte for byte. The bidi-override display residue is thereby
closed along with the reported classes.

Fix: one commit, `f4cc25c1bfff65940b12c49fa34d043f0bbc0e9f`, signed with a
good Shoggoth signature and the two trailers, carrying the predicate change,
the guard test (a `\u2028`-forged key plus a `\ud800` version: no traceback,
line count equals row count, one `hexaemeron` row, raw value present in
`--json`), and the six digest pins refreshed from
`ccc703a00792f0447a1a4d8ab7d04ac2853229ae8897fc7b5392a184f9aa4495` to
`782629a7d37d68a31ba53503534ece05fb6432f3bc97ac8aa486240294d24a5e`, values
only, same six rows. The source-bound Elenchus runner was invoked with the
step's declared test command and format at this round's fresh report path
`.elenchus/fiat-controller-currency-step-3-r2.json` against the fixes
commit. Its verdict is `guarded`: the parent report is complete, 1048 tests
executed, exactly the one new guard fails as an assertion, zero errors,
zero skips.

Mechanical results on the fixed tree: Phylax, Ephoros and Hypomnema print
`clean` and exit 0; the Hexaemeron suite passes 1048/1048 and the root suite
349/349; Horos reports `boundary matches the tree`; `git diff --check`
exits 0. The security suite stays waived: no Solidity in scope, unchanged.

Qualification: this round establishes the round 1 repair's completion and
the fixed rendering's behaviour, not the reinstall operation, step 4
behaviour, remote signature verification, push, pull request, or
integration state. The Elenchus line records the runner's declared result;
it does not attest the report bytes.

The Sapheneia durable-record comparison preserved the heading, the finding
with its id, severity, file and status, both commit SHAs and the entry SHA,
both digests, every suite count and exit code, the probe inventories, the
Elenchus contract tokens and `guarded` verdict with its counters, the
qualification, and the leads below, item by item. It changes no existing
audit byte.

Leads not pursued: the round 1 leads stand as recorded -- a well-formed
registry with an empty plugins map still reads zero rows at exit 0, a space
inside a plugin name still shifts text columns without forging lines, and
the defective-record row shapes and the unknowns-only fleet still carry no
dedicated suite guard. One new lead: lookalike printable names (homoglyphs)
remain renderable, as any name display leaves them. The step 2 leads stand
as recorded.

## Step 3, round 3 -- 2026-08-24

Zero findings.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

This convergence round re-audits round 2's fix commit
`f4cc25c1bfff65940b12c49fa34d043f0bbc0e9f` on
`fiat/controller-currency-guarantee-step-3-expose-the-currency-observation--audit`,
entered at `4d858a7570659cecc3654e822e3cd85dce448954` with a clean tree.

The printability predicate cannot misrender a value this registry
legitimately carries. A direct probe passes byte for byte: plugin slugs
including hyphenated ones, semver strings including pre-release and build
metadata, 40- and 64-hex pins, every route and verdict token, marketplace
names, and exotic-but-printable names -- accented, CJK, emoji and umlaut
samples -- while `None` renders `null` and interior spaces are kept, since
U+0020 is the one whitespace `str.isprintable` admits. The only characters
the helper mutates are non-printables, which no legitimate name, version,
hex pin or enum contains.

The round 2 guard reads the fix and not an accident: with the predicate
reverted in place to round 1's byte-class form, the guard fails on the
separator-forgery assertion, and the tree was restored byte-clean
afterwards.

No rendering path in the range prints registry bytes unsanitized. The
range's complete output inventory in the controller: the two refusal
strings, whose only interpolation is the fixed registry warning token; the
row warning suffix, a closed vocabulary; the text line, built exclusively
from the sanitizing field helper; and the `--json` dump, the deliberate raw
machine surface under native JSON escaping.

Mechanical results: Phylax, Ephoros and Hypomnema print `clean` and exit 0.
The Hexaemeron suite passes 1048/1048 and the root suite 349/349. The
security suite stays waived: no Solidity in scope, unchanged. No repair was
made this round, so no Elenchus report was created and no Elenchus verdict
applies.

Qualification: this round establishes the sanitizer's convergence and the
range's rendering inventory, not the reinstall operation, step 4 behaviour,
remote signature verification, push, pull request, or integration state.

The Sapheneia durable-record comparison preserved the heading, the zero
count, the empty finding table, the date, both commit SHAs, the probe
inventories, the revert-check result, the rendering inventory, every exit
code and suite count, the qualification, and the lead line below, item by
item. It changes no existing audit byte.

Leads not pursued: the standing step 2 and step 3 leads as recorded at
rounds 1 and 2, unchanged. No new lead was found this round.

## Step 4, round 1 -- 2026-08-24

Zero findings.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

The audited range is
`74b46b5c01d7769980913dd7b179980016f716df..69b8b4205e221bb56ad81e1b6e2f91fdf962bd92`
on
`fiat/controller-currency-guarantee-step-4-align-the-documentation-and-vers`,
two commits: `3dec30e33f545d9596d84c9e1985a3ae9db87865` rewrites
`plugin-currency.md`; `69b8b4205e221bb56ad81e1b6e2f91fdf962bd92` carries both
ledgers, both frontmatters, preflight step 3, the four manifests, the two
pinned test surfaces and the seven base-verbatim evidence imports. Both
commits have a good local Shoggoth signature and exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one
`Wildcat-Origin: shoggoth` trailer. The 18 touched files are exactly the
third amendment's Files list; nothing else rode in.

Ledger arithmetic, the headline risk, was checked byte by byte and by the
controller's own gate. The absorbed `fiat-v5.22.1` and `fiat-v5.23.1` rows
are byte-identical to `origin/main`'s at
`0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, whose ledger head is
`fiat-v5.23.1`, so `fiat-v5.24.1` is the next free version and appears
exactly once; all three appended rows retain frontier revision
`state-shape-validation` and digest `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` byte for byte, the
header matches the newest row, and the held issue 363 job text is untouched
-- the contract test's unchanged `FIAT_NEXT_JOB` literal enforces that
mechanically. `frontier_close_fault` run against the tree ledger with the
run's init snapshot (`fiat-v5.21.1`, 26 rows, sha256 `a4e5a531a53eafc779dae3f7aedc282292a9b01d4a0a55eb73a792032ec396a7`) and the
28 base-published versions returns `None`: exactly one row this run owns.
Kronos: one new `kronos-v0.7.0` generation row, absent from the base,
retaining revision `terminal-goal-loop` and digest `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` byte
for byte, the trailing evolution counter still 0, status still `mature`, and
the header matching the newest row.

Version propagation: all five compared surfaces read 1.6.0 -- both plugin
manifests, both marketplace manifests, and the pinned
`DELIVERY_PACKAGE_VERSIONS` map -- and the propagation suite passes. A
tree-wide `1.5.9` sweep finds no sixth live surface: the remaining hits are
fixture literals in the currency test's fabricated install layout, one
receipted historical delivery doc describing the move to 1.5.9, and the
receipted study's own host measurement.

The seven base-verbatim imports hash-compare byte-identical to
`origin/main`: `ADR-025-give-each-fiat-run-its-own-audit-record.md` and the
six files under `plugins/hexaemeron/docs/fiat-per-run-audit-log/` and
`plugins/hexaemeron/docs/fiat-bound-step-merge/`. The two pinned test
surfaces change literals only: the propagation map's one version line, and
the evolution contract's head-row literals (current version, latest version,
three evidence substrings) with every assertion, the digest literal, and the
frontier and next-job constants unchanged.

`plugin-currency.md` describes the landed behaviour accurately, audit fixes
included: the closed verdict vocabulary with `managed` defined as a pinless
record and a missing clone reading `unknown` (S2-R1-02's semantics), the
init refusal at exit 1 before any state with the two exits and the verbatim
`--controller-currency-waiver '<reason>'` flag, the empty-reason refusal,
the seven receipt fields as named in code, the `hexctl record` refusal of
the receipt key (S2-R1-01), the read-only fleet report with the 0/3/1 exit
contract and both refusal causes, one read per distinct origin, and the
printability sanitizer (S3-R1-01/S3-R2-01). Every documented flag, key,
route, verdict and field token greps verbatim in `hexctl.py`. Both honesty
limits are stated in their own section -- currency at init rather than for
the run's duration, and the gate governing runs after the next re-pin, never
the run that wrote it -- and the bootstrap property also appears in
ADR-033, the `fiat-v5.24.1` row, and the re-pin boundary's between-runs
placement in the kronos row. The still-true sections are retained: per-host
refresh, the mirror chain, the route check, the version gate, the
`controller_version` receipt with its two-gaps distinction, and the in-repo
identity case now stated in the observation's vocabulary. Preflight step 3
reflects the enforced gate, names the waiver flag verbatim, keeps the
stale-controller warning path, and cites the reference rather than
restating it.

Mechanical results: Phylax, Ephoros and Hypomnema print `clean` and exit 0
-- the imported evidence targets satisfy the pointer walk. The Hexaemeron
suite passes 1048/1048, the root suite 349/349, and
`scripts/promise_machine.py check` reports `clean: 14 plugin(s), 14
copy/copies` at exit 0. Imprimatur exits 0 at 100.0/100 with zero defects on
`plugin-currency.md` and on the fiat `SKILL.md`. Horos reports `boundary
matches the tree` and `git diff --check` exits 0 over the range. The
security suite stays waived: no Solidity in scope; the range is Markdown,
JSON manifests and two test-literal surfaces. No repair was made, so no
Elenchus report was created and no Elenchus verdict applies.

Risk-id dispositions for this range: `ledger-arithmetic` holds as measured
above. `version-propagation` holds as measured above. `bootstrap-limit`
holds: every surface describing the gate states it governs runs after the
next re-pin. `repin-partiality`'s report half stands on step 3's evidence,
its prose now restated in the reference and the kronos row; the operational
half stays owed to operation. `verdict-honesty`, `waiver-visibility`,
`secret-echo`, `upstream-read-surface`, `url-source-confusion`,
`registry-hostile-input`, `route-misdetection` and `state-compat` are
untouched by this range and their step 2 and 3 evidence stands; the
demonstration suite (behind refusal, waiver receipt, in-repo nulls,
currency exit contract) runs green inside the 1048.

Qualification: this round establishes the range's fidelity to the amended
step and the accuracy of its prose against the landed code, not remote
signature verification, push, pull request, integration state, or the
reinstall operation. The absorbed-row and import comparisons are against
the locally recorded `origin/main` ref named above, not a fresh network
fetch.

The Sapheneia durable-record comparison preserved the heading, the zero
count, the empty finding table, the date, the range, branch and three
commit or ref SHAs, both ledger digests and both frontier revisions, the
init-snapshot values, the 28-row published set size, the gate's `None`,
the five surfaces and the version 1.6.0, the seven import identities, every
exit code and suite count, the promise-machine line, all twelve register
dispositions, the qualification, and the lead line below, item by item. It
changes no existing audit byte.

Leads not pursued: the package version moved minor (1.5.9 to 1.6.0), a
choice the propagation suite accepts without policy input, taken as the
mason's call and not re-litigated; the standing step 2 and step 3 leads as
recorded. No new lead was found this round.

## Homologia, step 1, round 1 -- 2026-08-23

Suite: waived for the Pashov pair. The step ships a Python plugin, Markdown
contract text and JSON manifests, and no Solidity. The mechanical part is the
three bundled lints against the step's 24 changed paths, each required to exit
zero.

| lint | exit | result |
| --- | --- | --- |
| phylax | 0 | clean |
| ephoros | 0 | clean |
| hypomnema | 0 | clean |

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| | | | no finding | |

Risk register review, the part the lints cannot see. Ten of the eleven recorded
concerns have no surface in this step, and the review confirmed the absence
rather than assuming it: `plugins/homologia/scripts/homologia.py` opens no file,
starts no subprocess, reads no environment variable and writes no output path,
so `mirror-command-boundary`, `float-contamination`, `tolerance-creep`,
`provenance-conflation`, `decimals-scale-mismatch`, `runtime-drift`,
`answer-count-mismatch`, `input-exhaustion`, `subprocess-hang` and
`partial-write` have nothing to act on until step 2 accepts a manifest.

The eleventh, `evidence-strengthening`, is live from the first commit, because
prose can claim what code cannot do. The shipped documents were read for it
directly. The canonical contract states that a verdict never says either
implementation is correct; the landing page repeats it; the declared promise
`homologia-scaffold-identity` is bounded to packaging and refusal and says in
its own boundary that it establishes nothing about a manifest, a vector, a
mirror or agreement; and every verb writes its refusal to standard error and
exits 3, with a case requiring standard output to stay empty so no caller can
read a verdict off this version.

Leads not pursued:

- `--version` prints `homologia 0.1.0 (scaffold)` to standard output and exits
  zero, which is the one path in the command that answers rather than refuses.
  Left as is: it is a flag rather than a verb, the string names the scaffold,
  and a version report is not a verdict. Recorded here so a later round that
  widens the command surface can revisit it.
- The study and runbook both say implementation starts only after the issue
  owner approves the assumptions, including any new CI surface. The run was
  authorised by the issue owner and the study and runbook are receipted, so the
  name and the no-EVM posture are covered. The CI surface is not: no
  `.github/workflows/homologia.yml` was created, and the suite command lives in
  the root runtime contract instead. That gate stays closed and unspent.
- Two `H004` shape defects in `ADR-001` (missing `## Status` and
  `## Alternatives` sections) were found by running hypomnema before the commit
  and repaired there, so they are not findings of this round. Noted because the
  round's clean hypomnema exit would otherwise read as a record that was always
  well shaped.
- This log is append-only and the round's block was appended to it. Running the
  two prose lints over the whole file reports 2 `H003` findings at lines 6119
  and 6269 and 7 imprimatur defects between lines 1176 and 5018. All nine are
  byte-identical on `main` at `81105bb` and sit in historical blocks written by
  earlier runs, several of them inside quoted specimens. The round's recorded
  exits come from the step's own changed paths, which is the scope the loop
  names; the nine are noted here so a later reader does not read the clean
  exits as a claim about the whole file.

### Amendment -- 2026-08-24

**What changed.** The round above was run against `main` at `81105bb`. The step
ships rebased onto `dd23413`, twelve commits later, and three of the numbers
recorded above no longer reproduce.

The installed root law moved. `main` added a `## Run observation promise`
section to the root `PROMISE_MACHINE.md`, so the byte-identical copy under
`plugins/homologia/` was refreshed to match it, and one of the 24 audited paths
now carries different bytes. The three lints were re-run over the same 24 paths
at the new base: phylax, ephoros and hypomnema each exit 0, and there are still
no findings.

The fourth lead's whole-file counts were measured at `81105bb` and are stale.
`main` rewrote historical finding tables into archival records, so the log is
not the pure append that lead assumed. Over the file as it now stands hypomnema
reports the same two `H003` findings at lines 6041 and 6186, and imprimatur
reports six defects between lines 1173 and 4945 rather than seven. All eight
sit in historical blocks written by earlier runs, and none is in this step's
paths.

The root suite is 192 tests rather than 119, because `main` added the run
observation suites. The coverage ledger holds 68 rows on `main` and 69 here, so
`homologia-scaffold-identity` adds one row and displaces none.

**Why.** The exits recorded above are evidence about particular bytes at a
particular base. Carrying them onto a different base without saying so would
let a reader check the cited lines, find other numbers there, and have no way
to tell a stale record from a wrong one.
