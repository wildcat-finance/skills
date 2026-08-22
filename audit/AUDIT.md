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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | step commit | Fiat-created commit carried one provenance trailer where push-discipline requires both | fixed by amend on the step branch |

Leads not pursued: none. The round ran the waiver's lint battery -- phylax,
ephoros and hypomnema over the changed tree, all clean -- and reviewed the diff
against the study's risk register: no dangling pointer survives (the record
lint caught one at implement time, fixed before commit), the fiat prose pins
in `test_fiat_skill.py` still hold, both ledgers keep their axes, `hexctl.py`
is untouched, and the marketplace prose tests pass. Root 24/24, hexaemeron
124/124.

## Step 1, round 2 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The amended commit carries both provenance trailers, the lint
battery is clean over the fixed tree, and both suites pass.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The three lints exit clean over the changed tree; the diff
touches two references and one phase note, none of which a test pins; the new
lint commands resolve through `$PLUGIN_ROOT` exactly as the masks already do
in the same file; and both suites pass. Root 24/24, hexaemeron 124/124.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The lint battery is clean over the changed tree; the diff touches
two READMEs' prose, one manifest description and three version fields; the
short description four surfaces must agree on is untouched, and the marketplace
prose tests hold. Root 24/24, hexaemeron 124/124.

Leads not pursued: the root README's one-line Hexaemeron entry says nothing
about the phase skills. It also says nothing false, and the status table's
"Use it for" cell already names them, so no change.

## Step 4, round 1 -- 2026-08-18

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); the round ran the three bundled lints, all clean,
then reviewed the classifier against the study's risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/horos/skills/horos/scripts/horos.py | classify_file swallowed OSError and returned None, so an unreadable file was reported as readable instead of counted in files_skipped_unreadable, understating what the scan skipped | fixed: the function raises and the walker counts, with a chmod-0 regression test |
| S2-R1-02 | low | plugins/horos/skills/horos/scripts/horos.py | classify_file is public but did not itself refuse symlinks; only the walker guarded them, so a direct caller could make the scanner read outside root | fixed: the function refuses links as well |

Leads not pursued: a stat-then-open race (a file swapped for a symlink between
the check and the read) is accepted for the prototype; exploiting it requires
an attacker writing to the tree during the scan, at which point the tree is
already theirs.

## Step 2, round 2 -- 2026-08-18

Re-ran against the fixed tree. Lints: phylax 0, ephoros 0, hypomnema 0.
Horos 26/26, root 24/24. The fix diff review found nothing further: the one
public caller of classify_file already counts the raised OSError as skipped.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none beyond the accepted race recorded in
round 1.

## Step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Review focused on the
risk register's partial-write and determinism rows.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | plugins/horos/skills/horos/scripts/horos.py | the temporary boundary file used one fixed name, so two concurrent scans of the same tree could unlink each other's half-written temporary and fail one run's atomic replace | fixed: the temporary name carries the writing process id; the existing cleanup tests pin that no temporary survives either path |

Leads not pursued: a giant hand-crafted boundary.json can make check spend
memory parsing it; accepted for the prototype, the file is repository-local
and the parse failure path already exits 2.

## Step 3, round 2 -- 2026-08-18

Re-ran against the fixed tree. Lints: phylax 0, ephoros 0, hypomnema 0.
Horos 39/39, root 24/24. The fix diff is one line plus its comment; the
review found nothing further.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none beyond round 1's accepted parse-memory
lead.

## Step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
45/45, root 24/24. The review checked the map verb against the never rules:
it parses and never imports or executes the target, hostile nesting is capped
by the tokenizer's indentation limit and lands in the caught SyntaxError
path, and undecodable bytes are replaced before parsing.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Live-evidence run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two committed spec documents. Root 24/24, horos 51/51. The step adds prose
only; the review checked the committed copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Live-evidence run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
bundle. Horos 55/55, root 24/24. The review checked the risk register's
rows: the bundle names its commit and tool version, the consistency test
reads only the committed boundary and never re-scans or touches the network,
and the quoted totals are asserted rather than trusted. The one derived
number (80.3%) is recomputed by the test from the quoted operands.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Live-evidence run, step 3, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
six changed surfaces. Root 24/24 (the evolution contract validates the
v1.1.0 row's script-computed digest and the prose contract validates surface
agreement and job uniqueness), horos 55/55. The review confirmed the refusal
is recorded in both the skill text and the ledger with its reason, and that
the in-place study corrections are named in the commit rather than silent.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Rule-classes run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two spec documents. Root 24/24, horos 55/55. Prose-only step; the committed
copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Rule-classes run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0 over plugins tests,
hypomnema 0 over the changed README. Horos 61/61, root 24/24. The review
checked the register's false-exclusion row: both rules are gated on name
plus content or name plus path, each carries two near-miss tests, and the
example's readable file stays readable. The SVG rule runs before the marker
scan by decision, recorded as a comment at the check itself.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Rule-classes run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0 over plugins tests,
imprimatur 100 on all four reconciled surfaces. Root 24/24 (the evolution
contract validates the v2.1.0 digest; the prose contract validates surface
agreement and job uniqueness), horos 65/65. The review confirmed the
supersession keeps the refusal's grounds in the record rather than erasing
them, and that both prior ledger rows are byte-identical to before.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Outline-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
67/67, root 24/24. The review checked the move: the Python extractor's
output is pinned by the untouched fixture test, the registry refuses
unregistered suffixes naming its supported list, and the refusal-message
test moved with the message as the runbook records.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Outline-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 79/79, root
24/24. The review walked the risk register's lexer rows: escapes consume
line continuations, character classes protect a slash inside a regex, the
newline guard bounds a wrong regex guess to one line, operator folding
keeps arrow and equality tokens whole, and every unterminated construct
confesses the remainder.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Census run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0 over the
two spec documents. Root 24/24, horos 92/92. Prose-only step; the committed
copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings in the round itself. Leads not pursued: none.

## Census run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24 (evolution digest and prose
contracts), horos 104/104, demo census byte-identical. The review confirmed
the held job carries the maintainer's own restraint: breadth first, no
extractor from one tree, Solidity recorded as leading candidate rather than
commitment, and the three prior ledger rows byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Go-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
104/104, root 24/24. Prose-only step; one imprimatur defect (a bold-lead
bullet) was fixed before the copies were committed, and the committed
copies match the receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Go-extractor run, step 2, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 116/116, root
24/24. The review walked the study's risk rows: raw strings keep
backslashes as plain bytes and span lines, runes holding quotes are pinned,
iota members emit without types, receivers ride inside function slices, and
the statement walker advances monotonically (the guard the TypeScript
extractor learned the hard way is present from the start).

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: the corpus is gofmt-regular by
construction; hand-mangled Go would exercise the confession paths harder,
and can join the evidence when such a tree matters.

## Go-extractor run, step 4, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, imprimatur 100 on
all four reconciled surfaces. Root 24/24, horos 118/118, demo pinned. The
review confirmed the evolution row's numbers equal the committed bundle's,
the C++ job carries the maturity expectation in the maintainer's words, and
all prior rows are byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Cpp-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
118/118, root 24/24. Prose-only step; one imprimatur defect (a structural
metaphor) was fixed before the copies were committed.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity shipped); lints phylax 0, ephoros 0, hypomnema 0.
Horos 136/136, root 24/24. Prose-only step; the committed copies match the
receipted artefacts.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Solidity-extractor run, step 4, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, imprimatur 100 on all four
reconciled surfaces. Root 24/24, horos 152/152, demo pinned. The review
confirmed the evolution row's numbers equal the committed bundle's, the
held job quotes the maintainer's specification by its committed path, and
all prior rows are byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Refinement run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
152/152, root 24/24. Prose-only step; the committed copies match the
receipted artefacts and sit beside the maintainer's verbatim specification.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | .hexaemeron ledger | implement receipt asserted a green suite over a red one | corrected in 1d33f7f and recorded here |

Leads not pursued: none.

## Refinement run, step 2, round 2 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0. Horos 155/155, root
24/24, against the fixed tree. The round re-walked the two corrected tests
against the scanner's actual semantics and the scope table's registration
order, and re-verified the frozen fixture boundary is byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Refinement run, step 5, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, imprimatur 100 on all four
reconciled surfaces. Root 24/24, horos 165/165, demo byte-identical, all
verified before the receipt. The review confirmed the discipline's new
grade and universe language matches the shipped behaviour exactly, and all
prior ledger rows are byte-identical.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Marking run, step 1, round 1 -- 2026-08-18

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
165/165, root 24/24, verified before the receipt. Prose-only step.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Marking run, step 3, round 1 -- 2026-08-18

Suite waived; lints phylax 0, ephoros 0, hypomnema 0. Horos 168/168, root
24/24, verified before the receipt. The review held the register's rows:
one branch and one pull request per product repository and nothing merged
past their gates; the gitattributes promotions ride inside the reviewable
diffs exactly as the specification intends candidates to be promoted; the
bundle's numbers are asserted against the committed boundary copies; and
the stanza text in both product AGENTS.md files is the scanner's verbatim.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Phylax TypeScript boundaries, step 1, round 1 -- 2026-08-19

[Medium] TypeScript input had no work bound.
Location: `plugins/hexaemeron/skills/phylax/scripts/phylax.py:610`
Mechanism: The checker read each untrusted `.ts` or `.tsx` file in full before the linear lexer ran.
Impact: An oversized tracked file could consume unbounded memory and analysis time.
Fix: Read at most 1 MiB plus one byte, fail closed with `P000`, and guard the limit with a regression test.

## Phylax TypeScript boundaries, step 1, round 2 -- 2026-08-19

Suite waived (no Solidity); Phylax, Ephoros and Hypomnema lints clean.
Hexaemeron 167/167, root 24/24, pinned application clean and unchanged.
Manual review of `bff0eb6460e8f682e230ee6d982456121a33e2cc` found no further issue.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.
## Elenchus structured reports, step 1, round 1 -- 2026-08-19

[Medium] A descendant process could supply the accepted report.
Location: `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:310`
Mechanism: The report path was exported through `ELENCHUS_REPORT_FILE`, so every descendant inherited the same write target.
Impact: A broken parent run was classified as guarded from a nested fixture's unrelated assertion report.
Fix: Substitute one exact `{report}` command argument and remove the inherited report variable before launch.

[Medium] The report-size check had a stat/read race.
Location: `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:214`
Mechanism: A background writer could grow the file after its accepted size was read but before unbounded `read_bytes()` completed.
Impact: A report could exceed the 1 MiB memory and parser-work limit.
Fix: Read at most 1 MiB plus one byte and reject the extra byte before parsing.

## Elenchus structured reports, step 1, round 2 -- 2026-08-19

Suite waived (no Solidity); Phylax, Ephoros and Hypomnema lints clean.
Hexaemeron 179/179 and root 24/24. Real unittest, Forge and Node fixtures ran without skips.
Manual review of `5311fbaff498e1d20e256eb5d312b024d9354a2c` found no further issue.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.
## Ariadne dataset predicate, step 1, round 1 -- 2026-08-19

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | high | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | A symlink to a directory inside the release was skipped in silence. `os.walk` does not descend one, so every file under it was left out of both `dataset_subjects` and the release bundle digest, and nothing in the statement recorded that anything had been left out. A release could ship a statement describing part of its contents with no indication. This is the silent absence the gates exist to refuse, applied against the tool itself. | fixed in this round |
| S4-R1-02 | medium | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | `SKIPPED_NAMES` dropped `.git` and `__pycache__` from the walk without recording it, so the bundle digest covered part of the tree while the statement said nothing about the rest. Same class as S4-R1-01, smaller blast radius. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R2-01 | high | `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` | `os.walk` swallows a directory it cannot read, because `onerror` defaults to `None`. An unreadable subdirectory's files were dropped from `dataset_subjects` and from the release bundle digest with nothing recording it. Same class as S4-R1-01, which round 1 fixed for symlinked directories only and did not generalise. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R4-01 | high | `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` | The inputs check accepted `"disposition": "passed"` with no digest. That is a single word around the rule the check exists for: it asserted the input was read while recording nothing about what was read, and the tally then counted it as recorded absent, which contradicts the disposition it carries. A statement built this way verified clean and exited 0. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | low | `plugins/ariadne/scripts/ariadne_lib/registry.py` | The module docstring said "It is empty at this point in the build, and `ariadne predicates` says so." That was already false before this run, since the Solidity release predicate was registered, and the dataset predicate made it doubly so. A shipped file that describes its own state wrongly is the drift this plugin's own document tests exist to catch, and no test reached a docstring. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R2-01 | low | `plugins/ariadne/tests/test_cli.py` | The module docstring said "The two subcommands that exist at this point". There are six. | fixed in this round |
| S5-R2-02 | low | `plugins/ariadne/scripts/ariadne.py` | The `capture` subcommand's `kind` argument was helped by "the predicate to capture; one so far". A reader meeting it now takes it as a claim about the registry, which holds two. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

Not an audit round. A record of what the integrate phase could and could not do, and
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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `solidity_round` raised out of the controller on a state whose `config` or `receipts` was not an object. `state.get("config", {})` returns `None` when the key exists holding null, so the default never applies and the next `.get` is an `AttributeError`. 356 of 676 state shapes produced a traceback rather than the named error every other fault in this file gets. `load_state` validates no shape at all, so a hand-edited or half-written state reaches this function. | fixed in this round |
| S1-R1-02 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `is_waiver` used `startswith`, so it read `waivedX` and `waived-ish` as waivers, which is not the rule written beside `WAIVER_PREFIX`. Both spellings reach the same classification by the other branch, so the mismatch produced no wrong answer; it would produce one the moment a message explained which branch it took. The first word is now compared rather than the prefix. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The same shape sat at four more sites: three reads of `state["integrate"]["merged"]` at lines 854, 1072 and 1151, and one of `step["receipts"]["push"]["pr_url"]` at line 863. Each raises `AttributeError` out of the controller when the key exists holding null. Both spellings were confirmed to raise before being touched. `as_dict()` is now the single guard at all six sites, and behaviour on well-formed state is unchanged. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | `plugins/hexaemeron/skills/fiat/references/audit-loop.md` | Step 4 of the generic "One round" list still showed the bare command. It is complete for a Solidity round, and a reader working a non-Solidity round would have taken it as complete for theirs, then met the refusal. The step now says which round it is complete for and points at the section that adds the rest. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

Not an audit round. A record of what the integrate phase could and could not do.

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/metron/skills/../scripts/metron.py` | `NaN`, `Infinity` and `-Infinity` were accepted as a budget limit and as a measurement. `json.loads` permits all three by default as a Python extension rather than as JSON. The consequence is specific to a comparison tool: every comparison against `nan` is False, including `!=`, so a `nan` measurement does not fail a threshold -- it falls through whichever branch is tested last and is reported as whatever that branch says. An infinite limit means nothing ever exceeds it, so the budget passes forever. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | `plugins/hexaemeron/skills/metron/scripts/metron.py` | A run or baseline carrying both shapes at once -- a `measurements` block and measurement values at the top level -- silently kept the block and dropped the rest. `{"measurements": {"a": 1}, "b": 2}` loaded as `{"a": 1}` with nothing said about `b`. For this check that is worse than an ordinary dropped field: a measurement that never arrives cannot produce an `undeclared` verdict, so a typo'd name would vanish instead of failing. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `plugins/hexaemeron/skills/metron/scripts/metron.py` | `--promote` wrote the baseline with `write_text`, which truncates before it writes. A write that died partway left the baseline as invalid JSON, and the baseline is what every later comparison is measured against: the previous value was gone with nothing saying so, and every subsequent run would exit 2 on a file it could no longer read. Reproduced by making the write fail after a short write and reading the result back. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | `plugins/hexaemeron/README.md` | The plugin README said "six more skills holding each phase to a standard, four of them with an executable check". Four was right on `main` -- `elenchus`, `phylax`, `ephoros` and `hypomnema` -- and this run made it five. A prose count of something the tree can be asked about goes stale the next time one is added, which is exactly what happened. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

Not an audit round. A record of what the integrate phase could and could not do.

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | `plugins/ariadne/tests/test_solidity_release.py` | `deltas.current` set to `null` was refused by the code and held by no test. A producer emitting the key with nothing in it has said a side exists and then identified none, which is the case the absent branch must not swallow; membership rather than a truthiness test is what separates them, and nothing pinned that line | fixed in this round: two tests, one on each branch |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py` | The published schema caps each evidence count at 100000, taken from Lazarus's manifest schema, and the module enforced no ceiling at all. A count of 10 to the 30th passed the verifier and was refused by the schema shipping beside it | fixed in this round: `MAX_COUNT` enforced, and the drift tests now compare maxima and minima rather than field names alone |
| S2-R1-02 | high | `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py` | Gate 2 required `state_root`, which made the evidence check's central rule unreachable. Every statement that rule would refuse had already failed the gate, so it read as the safeguard this type exists for while deciding nothing. It also refused an honest capture that proved nothing and had no use for a root | fixed before the implement receipt: the root is required by what a statement claims, and gate 2 checks it only when present |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | `plugins/ariadne/tests/test_state_fixture.py` | Changing the proof-backed rule from `> 0` to `> 1` left the suite green. Every test of that rule counted two records, so a fixture claiming exactly one proved record with no state root would have verified clean -- the smallest claim the rule exists to refuse, and the one a real capture is likeliest to make | fixed in this round: a boundary test, and a sweep across zero, one, two, three, a hundred and the ceiling |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R4-01 | low | `plugins/ariadne/tests/test_state_fixture.py` | The schema agreement test needs `jsonschema`, which this plugin does not depend on, so it skipped on every interpreter without the package. The evidence for round 2's two schema fixes was conditional on something nobody installs | fixed in this round: a companion test reads the schema and checks both rules are in the document. Structural, weaker than validating, and it never skips |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R5-01 | medium | `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py`, `dataset.py` | `usable_path` normalised only a doubled backslash, because the source wrote four characters where two reach the string. So `a\..\..\b` arrived as one path segment and passed the check that keeps a consumer inside the tree. One odd filename on POSIX; a traversal out of the tree on Windows | fixed in this round in both predicates, with the same normalisation and matching tests |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | `plugins/ariadne/schemas/` | All three schemas typed a delta side name as a string with no lower bound, so they accepted an empty name every verifier here refuses. Two shipped fixtures were files the schema accepted and the tool rejected | fixed in this round in all three, since the shape was copied between them |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-01 | medium | `plugins/ariadne/scripts/ariadne_lib/core_predicate.py` | `check_side` tested a side's name for truthiness, and `"   "` is truthy. A comparison could name either end with a space and pass the check whose whole job is making both ends identifiable | fixed in this round, with tests from all three callers |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R5-01 | low | `plugins/ariadne/docs/conformance.md` | The coverage section said the predicate makes 31 distinguishable refusals. That figure came from a list written by hand while auditing, not from anything a reader could recompute | fixed in this round: removed, with the denominator stated as unavailable rather than implied |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | medium | `plugins/ariadne/scripts/ariadne_lib/capture/state_fixture.py` | `"schema_version": true` was accepted, because `True == 1` in Python and the check was a plain inequality against 1. That is the one check refusing a manifest this capture cannot read, and reading a later manifest as though it were version 1 is the evidence upgrade the capture exists to refuse | fixed in this round: the type is tested before the value |
| S4-R1-02 | low | `plugins/ariadne/scripts/ariadne_lib/capture/state_fixture.py` | `fixture_digest` was required and never looked at, so a manifest carrying `{"a": 1}` there passed a check implying the document is one Lazarus wrote | fixed in this round: its shape is checked, and a test asserts the value is still unused |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R2-01 | medium | `plugins/ariadne/scripts/ariadne_lib/digests.py` | A fifo where a component belongs hung the capture indefinitely. `of_file` refused a symlink and read anything else, so `open` blocked until something wrote to it: no output, no error, no timeout | fixed in this round in `of_file` and in the shared walk |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R3-01 | low | `plugins/ariadne/tests/test_capture_state_fixture.py` | Taking the check off the state root read from `header.json` left the suite green. The rule held and nothing held the rule: the header is read off disk exactly like the manifest and had no coverage at all | fixed in this round: six tests |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S5-R1-01 | low | `plugins/ariadne/AGENTS.md` | The runtime contract said `capture` writes only where `--out` points and every other subcommand prints, naming one of three capture subcommands. Accurate when written, narrowed silently when `capture-dataset` arrived, and narrower again now | fixed in this round: all three named, with what they have in common |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| L1-R1-01 | medium | `plugins/lazarus/schemas/release-v1.json`, `scripts/lazarus_lib/paths.py` | Every string field in a release took a value that satisfies its length check and renders as empty. Whitespace is one kind and a legal POSIX filename; U+200B and its neighbours are the other, because `str.strip` does not treat them as whitespace | fixed in this round: `lazarus_lib/text.py`, wired into the path helper and the release semantics |

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
  reading it twice reads two states.

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/protasis/SKILL.md | The frontmatter description enumerates what the contract holds and still listed only the four original commitments after five study items and a step field were added. That text decides whether the skill triggers, so an understated list costs a run that should have been held to the disciplines. | fixed in 70f5b66 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | high | plugins/hexaemeron/skills/protasis/scripts/protasis.py | The step cap stopped scanning and discarded the fact that it had, so five hundred sound steps followed by a broken one returned clean at exit 0. The cap turned a broken runbook into a passing one. | fixed in bf4fd43 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | high | plugins/hexaemeron/skills/protasis/scripts/protasis.py | The last tracked step's body ran to the next non-step heading, so where the cap had dropped steps their fields sat inside that span and donated themselves upward. A broken step at the cap boundary passed while missing five of six fields. | fixed in 6a8bca8 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-01 | high | plugins/hexaemeron/skills/protasis/scripts/protasis.py | Round 2 let any same-level heading end the last step, and that scan does not track code fences, so a runbook quoting a step heading inside an example truncated its own last step and reported the fields below it missing. | fixed in 8cb3ef9 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R4-01 | medium | plugins/hexaemeron/skills/protasis/scripts/protasis.py | Fences matched backticks only, so a runbook using tilde fences had its examples read as content: a quoted step heading became a step with no fields and the document collected six findings it had not earned. | fixed in 2226614 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | low | plugins/hexaemeron/skills/protasis/EVOLUTION.md | The row claimed 37 cases where the file holds 34. The inflated count came from reading a subTest loop as six cases where unittest reports one. A ledger is what a stranger reads instead of running the suite. | fixed in cb14cd3 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/kronos/scripts/kronos.py | `.kronos/` occupied by a symlink was written through, putting the scoreboard and its `*` gitignore in a directory the caller never named | fixed in 885bcb6 |
| S2-R1-02 | low | plugins/hexaemeron/skills/kronos/scripts/kronos.py | the `run` field was stored with no type check, so any JSON value reached the record | fixed in 885bcb6 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | plugins/hexaemeron/skills/kronos/SKILL.md | step 4 recorded the pass before Fiat was invoked, so the run link the record exists to carry could never be set | fixed in 251eb45 |
| S3-R1-02 | low | plugins/hexaemeron/skills/kronos/SKILL.md | a refusal was documented for a `total` field the skill never documented as a field | fixed in 251eb45 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | low | plugins/hexaemeron/skills/kronos/scripts/kronos.py | a halt reason carrying a newline printed at the left margin, so it could forge the summary line telling a reader whether anything still stands | fixed in 00cf4d2 |
| S2-R1-02 | low | plugins/hexaemeron/tests/test_kronos_scoreboard.py | nothing held the record format backward compatible, so a scoreboard written under v0.3.0 could stop reading without a test noticing | fixed in 00cf4d2 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | plugins/hexaemeron/skills/kronos/SKILL.md | phase-only mode restates its own stop condition, and that restatement omitted the park clause, so a loop following it could finish over a standing park | fixed in 4bc12a9 |
| S3-R1-02 | low | plugins/hexaemeron/skills/kronos/scripts/kronos.py | `show` dropped the parked flag the record carries, so a parked candidate outscoring the selected one read as a contradiction of the tie-break | fixed in 4bc12a9 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | low | plugins/hexaemeron/skills/kronos/scripts/kronos.py | a skill could be recorded as a scored candidate and reported ungoverned in the same pass, and `show` printed both | fixed in aaf172a |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

The look went after what the new refusal could have caught by mistake. An
ungoverned list naming skills that are not candidates records as before, an
empty list records, and a rank-only pass carrying an explicit null run records,
which is the case a refusal keyed on the field's presence rather than its value
would have broken.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-20

phylax exit 0, ephoros exit 0, hypomnema exit 0. Both findings came from reading
the new section against the sections it refers to.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | plugins/hexaemeron/skills/kronos/SKILL.md | the section said to record the pass, then said steps 5 to 8 do not happen, and step 6 is where recording lives | fixed in 7a03c5f |
| S3-R1-02 | low | plugins/hexaemeron/skills/kronos/SKILL.md | it asked for standing parks in the report without saying `parked` exits 3 whenever one stands, and the parked section explains that 3 only in terms of step 8 | fixed in 7a03c5f |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| B2-R1-01 | medium | `plugins/berean/scripts/berean_lib/jsonio.py` | NaN and Infinity reach `json.loads` through `parse_constant`, not `parse_float`, so a document carrying them passed the reader built to refuse non-finite numbers. | fixed in `c8c72d3` |
| B2-R1-02 | low | `plugins/berean/scripts/berean_lib/corpus.py` | A pinned path swapped for a symlink between the walk and the drift read raised out of `verify` as a usage error instead of failing a named check. | fixed in `c8c72d3` |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

Leads not pursued: none.

## Berean from its Commons specification, step 3, round 1 -- 2026-08-20

Scope: `d1df164..cf9d9d2`, answer records, source classes and block-bound
reads. The suite waiver stands; phylax, ephoros and hypomnema exit 0, root
suite 34 and berean suite 95 green at review, 96 after the fix.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| B3-R1-01 | low | `plugins/berean/scripts/berean_lib/answers.py` | Citation ids and read ids lived in separate namespaces, so one id naming both left a calculation's evidence reference resolving to two artefacts. | fixed in `2883291` |
| B3-R1-02 | note | `plugins/berean/scripts/berean_lib/answers.py` | A dead constant and an unused import survived drafting. | fixed in `2883291` |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

Leads not pursued: none.

## Berean from its Commons specification, step 4, round 1 -- 2026-08-20

Scope: `9ea6e4e..2a68fc7`, release manifests, verifier gates and promotion
records. The suite waiver stands; phylax, ephoros and hypomnema exit 0,
root suite 34 and berean suite 121 green at review, 124 after fixes.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| B4-R1-01 | medium | `plugins/berean/scripts/berean_lib/release.py` | The contract allowlist scanned only top-level string params, so an address nested in a filter object (the `eth_getLogs` shape) escaped the gate. | fixed in `464bc6a` |
| B4-R1-02 | low | `plugins/berean/scripts/berean_lib/promote.py` | `promote` digested the report bytes but parsed a second read of the file, so a swap between the two reads validated content the digest never covered. | fixed in `464bc6a` |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

Leads not pursued: none.

## Berean from its Commons specification, step 5, round 1 -- 2026-08-20

Scope: `1ac41c4..f5a5230`, the evaluation corpus and its graders. The suite
waiver stands; phylax, ephoros and hypomnema exit 0, root suite 34 and
berean suite 142 green at review, 143 after the fix.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| B5-R1-01 | medium | `plugins/berean/scripts/berean_lib/promote.py` | Promotion checked the pinned report's digests and counts but never graded, so a report claiming a clean pass would promote a release whose cases fail when graded today. | fixed in `df5edc7` |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

Leads not pursued: none.

## Berean from its Commons specification, step 6, round 1 -- 2026-08-20

Scope: `23fcb9a..bdac6a4`, the reference release and the demonstration.
The suite waiver stands; phylax, ephoros and hypomnema exit 0, root suite
34 and berean suite 150 green.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| B6-R1-01 | note | `plugins/berean/docs/runbook.md` | The runbook's step 6 file list put the README and demo inside the release directory, which the components gate refuses by design; the layout landed with the release under `release/` and the copy did not yet record the correction. | fixed in `07772a9` |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

# Run: create the janus skill in the Wildcat Commons

## Step 1, round 1 -- 2026-08-20

Non-Solidity round; the security-suite waiver covers the Pashov pair (the step
lands Markdown only). phylax exit 0, ephoros exit 0, hypomnema exit 0 over
`docs/commons/janus.md`, `docs/janus-commons-spec/study.md` and
`docs/janus-commons-spec/runbook.md`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/janus/scripts/janus.py | The validator scanned effect free-text for wildcards but did not enforce the `scope` and `kind` enumerations the schema documents, so a manifest with an unrecognised storage scope or call kind validated. Gate 1 promises effects are enumerated; an unrecognised enum value slipping through is a fail-open hole. | fixed in ae61738509855e47ba687299fb0705e609d2f478 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the two accepted limitations recorded in round 1.

## Step 6, round 1 -- 2026-08-20

Python, prose and deletion step: the report subcommand, the sample findings,
the README retirement of the anchor, and the removal of the delivered spec. No
Solidity ships, so x-ray and solidity-auditor have nothing to review; the three
bundled lints ran clean over the changed files (phylax 0, ephoros 0, hypomnema
0) and the reporter was read against the risk register.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S6-R1-01 | low | plugins/janus/scripts/janus.py | A finding field carrying a pipe or a newline would malform the human report's Markdown table, opening a spurious column or splitting the row. | fixed in fde7c12cd9f53078548357bccc4714219a99814b |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/horos/tests/benchmark_scope.py | the record's `root` field was `os.path.relpath(root, root)`, always `"."`, so a run against a different root recorded the same value as a run against the repository | fixed in b6e7ed2 |
| S1-R1-02 | low | plugins/horos/tests/benchmark_scope.py | a refused check still reported a median, so `--root plugins/horos` recorded `0.014 ms` beside exit 2; a duration for a check that classified nothing reads as a fast check | fixed in b6e7ed2 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | plugins/horos/docs/scoped-entry/runbook.md | step 2's exit claimed a fresh scan takes this repository's hard entries from 93 to 87. Running the pre-fix classifier over a pristine worktree of the same commit gives 87 with no phantom entry: the 93 came from the maintainer's own checkout, which carries a stale worktree under `.claude/worktrees/` and a `plugins/pandects/out/` directory. The number described a checkout and was written as a property of the repository | fixed in 84bb99e, and pull request 256's body corrected in place |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. Leads not pursued: none.

## Scoped entry, step 4, round 1 -- 2026-08-20

Suite waived (no Solidity); lints phylax 0, ephoros 0, hypomnema 0. Horos
206/206, root 38/38, verified before this receipt. Two mutations were run
against the committed step before the suite was trusted: making the committed
slice ignore the scope fails five of the nineteen cases, and pruning the
ancestor chain instead of walking it fails six. The round then went at the
control the risk register names rather than at the happy path, and found it
half-built.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | medium | plugins/horos/skills/horos/scripts/horos.py | the escape control only inspected the given path, so a symlink as the final component was refused while a symlink in the middle was not. `git -C` resolves symlinks before answering, so `check bridge/sub` reported the far repository as its own worktree and the check would have been answered from that tree's boundary | fixed in 312bf0a, with two guards seen failing without it |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R2-01 | medium | plugins/horos/tests/benchmark_scope.py | the benchmark still called `check_tree`, which knows nothing of ancestor resolution, so every scoped run recorded exit 2 and a null median while the check itself worked. Criterion 12's measurement did not exist, and the record said `unavailable` rather than being wrong, which is why round 1 read past it | fixed in fad07e3 |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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
[High] S6-R1-01: Three judgement-held promises cited mechanical parser tests.
Location: `tests/promise_machine_coverage.json`
Mechanism: The Ephoros, Phylax and Protasis review rows borrowed evidence from narrower mechanical gates.
Impact: The coverage map overstated what those tests established.
Fix: Added 15 labelled review cases that record P/M/S/O/R judgements without presenting them as checked runtime proof.
END

FINDING
[Medium] S6-R1-02: Evidence references could not state their base class.
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
[High] S7-R1-01: Vulgate cases used an evidence class its promise does not accept.
Location: `tests/promise_machine_coverage.json`
Mechanism: Generic Hexaemeron cases were marked `recorded`, while Vulgate declares only `checked` and `inferred` evidence.
Impact: A recognised class could pass even when the owning promise excluded it.
Fix: Added Vulgate-specific inferred references and made the gate reject explicit classes absent from the canonical declaration.
END

FINDING
[Medium] S7-R1-02: Evaluation corpora could use checkout-specific absolute paths.
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
[High] S8-R1-01: A runtime field map was not bound to the result surface bytes.
Location: `tests/promise_machine_coverage.json`
Mechanism: The gate checked that each schema, writer or contract existed, but a later change to that source could leave its field map green.
Impact: A stale map could misstate where a consequential result carries its subject, evidence, unknowns or transition.
Fix: Added a required source SHA-256, recomputation in the root checker and a source-drift refusal test.
END

FINDING
[Medium] S8-R1-02: Runtime source hashing had no read bound.
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
[High] S8-PG-01: Lazarus's scaffold test still equated package and skill versions.
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
[High] S8-PG-02: Four plugin suites retained the same package/skill version assumption.
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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The step commits the study and runbook, byte-identical to the
run's working copies. Phylax, ephoros and hypomnema exit 0 over the tree.
Reviewed against the risk register: no checker code exists yet, so the
unearned-verdict concerns do not arise this step. Root suite 104/104;
hexaemeron 470/472 with the two recorded environment failures.

Leads not pursued: none

## Protasis study schema check, step 2, round 1 -- 2026-08-20

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. Two committed documents, byte-identical to the run's working
copies; the study check exits 0 over the study. Per the register:
refusal-drift not applicable, no contract text changed this step;
field-mismatch reviewed, the study's item 1 and item 4 name the same four
fields; ledger-arithmetic not applicable, no row cut this step. Phylax,
ephoros and hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the
two recorded environment failures.

Leads not pursued: none

## Protasis amendment contract, step 2, round 1 -- 2026-08-20

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. Per the register: refusal-drift reviewed, the new rule
reuses the contract's existing three-part refusal report rather than
defining a second shape; field-mismatch reviewed, the block's four fields
match the study's item 1 and the wish; ledger-arithmetic reviewed, the
evolution suite passes over the new generation row. Phylax, ephoros,
hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the two recorded
environment failures.

Leads not pursued: none

## Hypomnema first records, step 1, round 1 -- 2026-08-20

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. Two committed documents, byte-identical to the run's working
copies; the study check exits 0. Per the register: content-drift not
applicable, no record touched this step; pointer-rot reviewed, the
hypomnema lint exits 0 over docs and plugins; ledger-arithmetic not
applicable, no row cut this step. Phylax and ephoros exit 0. Root
104/104; hexaemeron 490/492 with the two recorded environment failures.

Leads not pursued: none

## Hypomnema first records, step 2, round 1 -- 2026-08-20

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. Two committed documents, byte-identical to the run's working
copies; the study check exits 0. Per the register: double-record and
scope-creep not applicable, no contract text changed this step;
ledger-arithmetic not applicable, no row cut this step. Phylax, ephoros
and hypomnema exit 0. Root 104/104; hexaemeron 490/492 with the two
recorded environment failures.

Leads not pursued: none

## Hypomnema design bridge, step 2, round 1 -- 2026-08-20

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

No findings. The step contains the study and runbook byte-identical to the
receipted working copies and a regenerated Horos boundary for those two paths.
The Protasis checks are clean, the root suite passes 104/104 and the
Hexaemeron suite passes 536/536. Phylax, Ephoros and Hypomnema each exit 0 over
the changed tree. The risk-register concerns are not yet applicable: this step
changes no path classifier, heading scan, pragma, handoff interface, stable
code, frontier row or marketplace description.

Leads not pursued: none

## Hypomnema runbook shape check, step 2, round 1 -- 2026-08-21

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S1-R1-01 | low | `.horos/boundary.json` | The committed tracked-universe document reports 1,367 files walked; a fresh scan of the committed step tree reports 1,369. Removing only `counts.files_walked` makes the documents byte-identical, so the hard boundary is current but its published walk count omits the two tracked study/runbook files. | open |

Scope: `0bfad60bb482245dd08d9747139d26824392a2c7..a8f2a13f9143b0335cba514c4ef0f9dd9afa34ed`, limited to the two tracked specification documents and regenerated Horos boundary. Both documents are byte-identical to the receipted working copies; Protasis study/runbook, Imprimatur, per-file Brevitas and diff checks exit 0. Phylax, Ephoros and Hypomnema tree lints each exit 0. Evolution 18/18, root 104/104 and Hexaemeron 548/548 pass; Promise Machine reports 14 plugins and copies clean. The step commit has a good local signature and exactly one required co-author and origin trailer.

Leads not pursued: none

### Resolution: E319-S1-R1-01 -- 2026-08-21

Resolved on the audit branch by regenerating `.horos/boundary.json` after the two specification documents were tracked. The committed document and a fresh tracked-universe scan are now byte-identical at 1,369 files walked, with 89 classified entries and none unreadable. The complete step-1 gate set remains clean: document copies, Protasis, Imprimatur, per-file Brevitas, Promise Machine, evolution 18/18, root 104/104, Hexaemeron 548/548, boundary currency 4/4, diff check and the Phylax, Ephoros and Hypomnema tree lints all exit 0. No new leads.

## Ephoros alert-runbook annotations, step 1, round 2 -- 2026-08-21

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R2-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` | `_split_yaml_comment` treats every unquoted `#` as a comment marker, although a hash without separating whitespace remains plain-scalar content. A preceding list item such as `- note: literal# ephoros: allow not-a-comment` therefore suppresses E004 on the next unannotated alert. | open |
| E319-S2-R2-02 | low | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` | `_yaml_allow_lines` handles a comment-only line before checking whether its indentation ended the active block scalar. A real dedented reasoned comment immediately after a scalar and immediately before an alert is therefore discarded as scalar text, and the documented E004 suppression does not apply. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R3-01 | medium | `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | Hypomnema's separate YAML comment splitter still treats every unquoted `#` as a comment marker. An alert pointer such as `runbook: runbooks/missing#book.md` is accepted by Ephoros as a relative Markdown annotation, then truncated before `.md` and ignored by H003, so the missing target passes both ownership gates. | open |
| E319-S2-R3-02 | low | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` | The YAML/Python directory walk does not require discovered paths to be files. A directory whose name ends in `.yaml`, `.yml` or `.py` is passed to `check()` and produces E000 instead of being left outside the source set; Hypomnema's parallel walk already guards this boundary with `is_file()`. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R4-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | Both bounded YAML lexers reset quote state on every physical line. In a valid multi-line single- or double-quoted scalar, alert-shaped text is therefore treated as real keys: quoted `annotations.runbook` text can satisfy E004 for an unannotated alert, quoted `- alert:` text can produce E004, and quoted `runbook:` text can produce H003. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R5-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | The cross-line quote state opens on every apostrophe or double quote, including one inside a plain scalar. A preceding value such as `O'Brien` or `six" pipe` therefore hides a later `- alert:` or `runbook:` key, allowing missing E004 or H003 evidence to pass. | open |
| E319-S2-R5-02 | low | `plugins/hexaemeron/tests/test_ephoros_checker.py`, `audit/AUDIT.md` | The quoted-runbook-satisfaction guard is already green against the pre-fix round-4 tree. Independent replay produces six red subtests, not the eight recorded in the round-4 resolution, so this guard does not establish the claimed false-E004-satisfaction mechanism and the resolution overstates its red evidence. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R6-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | `_yaml_quote_starts` accepts a mapping-looking colon or sequence-looking dash without requiring YAML separation before the quote. Valid plain scalars such as `- note: plain:"text` and an indented `-"text` therefore open cross-line quote state and hide later alert or runbook keys, allowing missing E004 or H003 evidence to pass. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R7-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | Neither lexer tracks an active multi-line plain scalar. A continuation line whose first non-space character is an unmatched quote is valid plain-scalar content, but `_yaml_quote_starts` opens quoted-scalar state and hides the following alert or runbook key, allowing missing E004 or H003 evidence to pass. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-R8-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | Both checkers bind a multi-line plain `runbook` scalar from its first physical line before discarding its continuation. With a present decoy `runbooks/present.md`, the valid YAML value `runbooks/present.md extra` therefore satisfies E004 and passes H003 even though that actual pointer is neither the checked Markdown path nor a resolving target. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| E319-S2-PC-01 | medium | `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` | The new plain-scalar fold drops blank physical lines and joins the next continuation with a space, although YAML preserves the blank as a line break. A present decoy `runbooks/present target.md` therefore makes E004 and H003 clean for the actual YAML value `runbooks/present\ntarget.md`. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | low | `plugins/hermes/skills/hermes/scripts/hermes.py` | The header check named the three record classes in its own tuple, so a schema that grew a fourth class would report the corpus key holding it as an unknown top-level field rather than validating its records. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | medium | `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` | MEM-12 mapped to `hashing-encoding`. The rule states its own implementation is scratch-memory `KECCAK256`, and Gate 2 already refuses added assembly outside the `assembly` class, so a candidate declared under that mapping would have been refused every time it was attempted. Now `assembly`. | fixed in this round |
| S4-R1-02 | medium | `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` | DEP-07 and DEP-08 floored at Shanghai on the strength of EIP-3860. Both rules hold wherever EIP-170's runtime limit applies, so the floor refused correct advice on every earlier fork. The same shape as step 3's TRN-07 finding. Now floored at Homestead with the initcode half named in the reason. | fixed in this round |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S6-R1-01 | low | `AGENTS.md`, `README.md`, `plugins/hermes/skills/hermes/SKILL.md` | The marketplace-wide cold read the frontier obligation requires found three surfaces describing Hermes as it was before the corpus: the boundary sentence in the root runtime contract, the two published invocation prompts, and the skill's own selection description. Each now names the corpus. | fixed in this round |
| S6-R1-02 | low | `plugins/hermes/skills/hermes/SKILL.md`, `references/optimisation-catalogue.md` | Two new two-column tables failed Brevitas B011, which requires three by three before a table earns its shape. Both are lists now. | fixed in this round |

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
reading the body. The catalogue's generated index is held to the corpus by a
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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-01 | medium | scripts/ephoros.py | deeply nested brackets scanned quadratically through `_matching`, extrapolating to roughly 1.9 hours at the 1 MiB cap, the `ts-lexer-input` register class | fixed in 7295cfe |
| S3-R3-02 | low | scripts/ephoros.py | a findings-saturated file paid a per-finding newline count, 9.9 seconds for fifty thousand findings | fixed in 7295cfe |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R4-01 | medium | scripts/ephoros.py | overlapping spans that name a sink still paid per-span work behind the gates, 107 seconds at 160 KB and roughly 77 minutes at the cap on a nested `.labels(` shape | fixed in d21e5ea |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I438-S2-R1-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:256-267`; `plugins/hexaemeron/tests/test_hexctl.py:1618-1625` | `task_issue_number` checks only the path returned by `urlsplit`. Relative text, hostless or non-HTTP URLs, and raw controls removed by `urlsplit` can therefore supply an issue number and be stored unchanged as the task-issue receipt. Require raw whitespace, C0 and DEL rejection, then an absolute HTTP(S) URL with a hostname; add each counterexample to the no-state-on-refusal guard. | open |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I438-S2-R1-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:256-281`; `plugins/hexaemeron/tests/test_hexctl.py:1618-1640` | The parser now rejects raw whitespace, C0 and DEL before parsing, then requires HTTP(S), a hostname and the positive terminal issue path. The no-state-on-refusal guard carries the round-1 relative, hostless, non-HTTP and normalized-newline counterexamples. | fixed in `63861895b98585cf597ae1fb3a2ec749ae3c9ef7` |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | No findings. | clean |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| SCG-S1-R1-01 | medium | `docs/how-to-help-shoggoth-study.md`; `docs/how-to-help-shoggoth-runbook.md` | Step 1 shipped the study before the planned framework observation existed. The study named that issue as the standing home for the volunteer-selector trade, so Hypomnema's record-placement rule had no existing record to inspect when implementation was receipted. | fixed by filing [issue #447](https://github.com/wildcat-finance/skills/issues/447), which carries the chosen intent-packet design, rejected inference boundary, claim-channel alternatives and unresolved questions; exact title and labels were read back from GitHub |
| SCG-S1-R1-02 | low | audit invocation | The first Hypomnema command included `audit/AUDIT.md`, whose historical failure specimens deliberately name absent runbooks. It reproduced two H003 findings at lines 6119 and 6269; the reduced command over the three changed documents exited 0. | fixed by applying the pointer gate to the changed documentation scope named by the audit contract; no checker or shipped-document defect existed, so no code guard was added |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| SCG-S2-R1-01 | medium | `docs/how-to-help-shoggoth.md`; `docs/how-to-help-shoggoth-study.md`; `docs/how-to-help-shoggoth-runbook.md`; issue #447 | The first correction described the default as the earliest Wave with an eligible open issue. That narrows the user's rule: first choose the earliest Wave that still has open issues, then apply eligibility inside it. | fixed in this round; the tracked prose and issue now use the open-issue boundary, while the second immutable correction receipt records how eligibility applies inside the chosen Wave |
| SCG-S2-R1-02 | low | issue #447 | The issue body counted ten open issues without Wave metadata. Filing the issue made that count stale immediately because the observation itself has no Wave metadata. | fixed in this round by keeping the relevant fact without a self-invalidating count |

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

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| SCG-S3-R1-01 | medium | `.horos/boundary.json`; `docs/assets/how-to-help-shoggoth-infographic.png`; `output/pdf/how-to-help-shoggoth.pdf` | The pre-commit Horos scan could not place the untracked artwork and PDF in the tracked-tree boundary. After the implementation commit, `test_the_committed_boundary_matches_a_fresh_scan` named both paths and the root suite failed 1/109. | fixed in this round by rerunning the required committed-tree scan; both assets now have hard binary entries backed by their PNG and PDF file signatures, the focused boundary suite passes 4/4 and the root suite passes 109/109 |

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

## Fiat run worktree, step 1, round 1 -- 2026-08-22

Suite waived (no Solidity: the step ships two Markdown documents). Phylax,
Ephoros and Hypomnema lints each exit 0 over both changed documents. Root suite
113/113. Hexaemeron 739/741, the two failures being
`test_elenchus_checker.ForgeReports.test_fixture_exercised_the_declared_forge_version`
and `NodeReports.test_fixture_exercised_the_declared_node_version`, which assert
`1.7.1` and `v26.6.0` against this container's `forge 1.5.1-stable` and
`v22.22.2`. Both compare a live tool against a string literal in a file this
run does not modify, so neither is caused by the step; the study's amendment
records them. Promise Machine check clean over 14 plugins, coverage clean
67/67.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| I439-S1-R1-01 | low | docs/fiat-run-worktree-study.md | The amendment named `/root/.foundry/bin` as a `PATH` requirement, putting one machine's home-directory path into a shipped document. The study's own never-list refuses absolute home paths, and the runbook preamble repeated it. Nothing reads the value, so the cost is a reader following a path that exists on one container. | fixed in the commit recording this round |

Reviewed against the risk register: `path-escape`, `branch-already-checked-out`,
`operator-head-mutation`, `stale-tree-reuse`, `uncommitted-work-loss`,
`resume-orphan`, `partial-write`, `cross-filesystem-atomicity`,
`subprocess-control`, `legacy-state-resume` and `dirty-origin-tree` are all not
applicable to this step, which adds no executable path, no filesystem write and
no state handling. The one concern a document step can carry is what it tells a
later reader to run, which is where the finding above sits.

Leads not pursued: the two pinned-toolchain assertions are left failing rather
than repaired. Raising this container to forge 1.7.1 and node v26.6.0, or
loosening the fixtures' pins, is a change to Elenchus's fixtures and belongs to
whoever owns that pin, not to a run about worktrees.

## Fiat run worktree, step 1, round 2 -- 2026-08-22

Suite waived (no Solidity). Phylax, Ephoros and Hypomnema each exit 0 over the
step's two shipped documents. Root suite 113/113; Hexaemeron 739/741 with the
two pinned-toolchain assertions round 1 already recorded; Promise Machine check
and coverage clean.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. I439-S1-R1-01 is closed: neither document names a
machine-specific path, and the study now says why the directory is not named.

Reviewed again against the risk register, with the same result as round 1: this
step adds no executable path, no filesystem write and no state handling, so
every concern in the register belongs to steps 2 through 4.

Leads not pursued: running Hypomnema over `audit/AUDIT.md` itself, rather than
over the step's shipped documents, exits 1 with two H003 alerts at lines 6119
and 6269. Both sit inside rounds written weeks ago, and both name runbook paths
(`runbooks/missing`, `runbooks/present.md`) that were fixture names in the work
those rounds recorded. They cannot be repaired: this file is append-only by
contract, and the rounds above stay as they were written. So the append-only
ledger and H003's file-existence rule cannot both hold over the whole file
forever. That is a question about H003's scope for whoever owns Hypomnema, not
something a run about worktrees can settle, and it is left here rather than
worked around quietly.
