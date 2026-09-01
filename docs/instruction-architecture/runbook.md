# runbook: framework-74 instruction architecture research

This runbook derives from `.hexaemeron/study.md` at SHA-256
`99a9195aa31af3f15ed70c51ac3f9d3d2221c724494b65a2d6c4c7185453d48f`.
It uses five ordered research steps. The source Markdown, root contracts,
router, plugins, generated runtime and parked Noema stack remain unchanged.
The workbench may select an implementation architecture or a negative result;
it does not implement or integrate the selected result.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 117dd4d94d8f7b464f069332e0845d3ee9fd789950020a553b6b2096cafa6f48
candidate | neutral-evidence-workbench
```

## Step 1: Freeze the corpus, loader graph, byte classes and sealed cohorts

**Goal.** Commit the receipted study and runbook, scaffold a bounded neutral
workbench, emit the exact current corpus/load manifest and byte partition, and
seal disjoint development and holdout cohorts before any candidate is built.

**Entry.** Run branch
`fiat/1046-framework-74-select-an-implementation-ready` at
`a2b634d8e039af988bf30c8316defccf70071d8d`, with the study and design lock
receipted, the repository clean, the base whole-set audit synopsis check green,
the Noema review head available as read-only evidence, and no
`research/instruction-architecture/`,
`tests/fixtures/instruction-architecture/`, or
`docs/instruction-architecture/` product path present.

**Exit.** All of the following hold:

1. The committed corpus manifest binds exactly the 106 agent-facing Markdown
   files at the entry ref: 32 canonical skill contracts, 18 `AGENTS.md`, 18
   Promise Machine contracts and 38 Markdown references. It records path,
   logical document, class, size, SHA-256, exact duplicate group, canonical
   owner, authority tier, loader roots, scenario reachability and external
   runtime ownership. A reconciliation report reproduces 1,545,537 physical
   bytes, 89 exact-unique files and 1,074,093 exact-unique bytes or refuses with
   the precise changed predicate.
2. Every physical byte belongs to exactly one range classified as governed
   operative semantics, exact literal or evidence, human-only explanation or
   rationale, generated duplicate, or unsupported/unknown. Ranges are ordered,
   non-overlapping, gapless and source-digest bound. Any unsupported operative
   range is visible and blocks later selection.
3. The loader graph proves each root and edge from a source path, byte span and
   digest. It distinguishes unconditional host loading from conditional linked
   references and excludes test fixtures and the moved `skills-runtime`
   package. File presence alone never creates an edge.
4. A deterministic stratified selection fixes a development cohort covering
   at least 50% of unique bytes, every shared root/runtime contract, at least
   12 logical skills, every observed construct and authority tier, and every
   size decile. A disjoint sealed holdout fixes at least 20% of unique bytes and
   five logical skills with authority, failure, recovery, exact-literal and
   cross-document cases. The seal binds source, method, seed, membership and a
   closed future case envelope; Step 1 does not open or score that envelope.
5. `benchmark.py verify-corpus`, `benchmark.py verify-loader`,
   `benchmark.py verify-partition`, and `benchmark.py verify-seal` each emit one
   bounded correlated JSON result and exit zero. Repeating all four commands
   is byte-identical. The copied study and runbook match their receipted bytes,
   the focused tests and repository-selected checks pass, and no live
   instruction or production path changes.

**Files.** Create `research/instruction-architecture/benchmark.py`, local
strict schemas and a short research README under the same directory;
`tests/test_instruction_architecture.py`;
`tests/fixtures/instruction-architecture/corpus-manifest.json`,
`byte-partition.json`, `loader-graph.json`, `cohorts.json`,
`holdout-seal.json`, and their source-bound inventory;
`docs/instruction-architecture/study.md`,
`docs/instruction-architecture/runbook.md`, and
`docs/instruction-architecture/corpus-reconciliation.md`. Change
`tests/check-map-v1.json` only as needed to give every new path an existing
bounded owner. Regenerate `.horos/boundary.json`, `.horos/candidates.json` and
`.horos/census.json` only when the deterministic scan requires them. Change no
`SKILL.md`, `AGENTS.md`, Promise Machine, router, plugin manifest, generated
runtime, README, CI, dependency, toolchain pin or external repository file.

**Tests.** Add `CorpusManifestTests`, `BytePartitionTests`,
`LoaderGraphTests`, and `HoldoutSealTests` for exact inventory, duplicate
groups, range closure, source-span anchors, conditional edges, runtime-owner
exclusions, cohort coverage, disjointness, seed replay, sealed-envelope
non-disclosure and stale-source refusal. Run these exact commands from the
repository root:

```text
python3 research/instruction-architecture/benchmark.py verify-corpus --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
python3 research/instruction-architecture/benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
python3 research/instruction-architecture/benchmark.py verify-partition --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
python3 research/instruction-architecture/benchmark.py verify-seal --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
python3 -m unittest tests.test_instruction_architecture.CorpusManifestTests tests.test_instruction_architecture.BytePartitionTests tests.test_instruction_architecture.LoaderGraphTests tests.test_instruction_architecture.HoldoutSealTests -v
python3 scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
cmp -s .hexaemeron/study.md docs/instruction-architecture/study.md
cmp -s .hexaemeron/runbook.md docs/instruction-architecture/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/instruction-architecture/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/instruction-architecture/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/instruction-architecture/study.md docs/instruction-architecture/runbook.md docs/instruction-architecture/corpus-reconciliation.md
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For an audit repair, run
`python3 tests/run_tests.py --elenchus-report {report}` with the fresh report
path `.elenchus/fiat-1046-step-1.json`. The expected schema is
`elenchus.unittest.v1`. A missing, stale, malformed or infrastructure-failed
report is inconclusive.

**Disciplines.** phylax: source and Git-object reads are bounded, no-follow,
regular-file operations with identity rechecks; generated writes are atomic
and confined. ephoros: every inventory, partition, edge and seal result names
the run, source and artifact digests; there is no production alert. metron:
the four denominators are baselines, not interchangeable savings claims.
elenchus: a missing byte, invented edge, overlap or cohort leak is preserved on
the parent and guarded before repair. hypomnema: the corpus reconciliation owns
topology facts; the study and runbook own the research contract.

## Step 2: Build the neutral workbench and five immutable comparison arms

**Goal.** Implement one representation-neutral case, prompt-component, outcome
and scoring contract, then adapt raw Markdown, merged WAI1, parked Noema, the
file-level simple control and a distinct source-span section graph without
letting any arm define another arm's semantics.

**Entry.** Step 1 is integrated into the run branch; its manifest, partition,
loader graph and unopened holdout seal verify byte-identically; development and
holdout memberships are disjoint; WAI1 at the entry ref and Noema product head
`07ee0475d1559a2b09488f925645a83f786d1f3c` remain available as immutable
controls.

**Exit.** All of the following hold:

1. Closed strict schemas cover cases, prompt components, adapter results,
   deterministic scores, mutations, resource samples and aggregate reports.
   Case semantics and scorer expectations come from exact canonical source
   spans, not a candidate id. Prompts contain the task and representation but
   no expected answer, scorer key or competing arm's label.
2. The raw arm follows the verified actual-loader graph and preserves exact
   current Markdown. The WAI1 arm invokes the merged checker and uses its exact
   three bound envelopes plus raw fallback for every unmapped current span. The
   Noema arm binds the parked product artifacts and review evidence, admits
   only current spans whose exact bytes still verify, and uses raw fallback for
   every unsupported or stale span. Neither control source is edited.
3. The simple arm performs only exact whole-file content addressing,
   deduplication and scenario file selection. The section-graph arm splits
   canonical Markdown into exact recoverable spans, assigns stable ids and
   explicit dependency edges, selects conservative scenario closure and keeps
   unsupported operative material as raw fallback. It has no inferred
   permission, prose summary or model-built mapping.
4. All five arms run the same development cases and synthetic supplements for
   order, scope, negation, exception, literal, alias, unknown, refusal,
   recovery and authority. Canonical round trips pass where claimed; source
   traceability is complete; every unsupported or ambiguous byte remains
   counted; parser differential, stale-source, malformed-input, missing-edge,
   digest, concurrent-change, hostile-output and resource-bound cases refuse.
5. `benchmark.py build-development` and `benchmark.py replay --cohort
   development` regenerate byte-identical arm artifacts and reports with the
   sealed holdout unopened. The focused and repository-selected checks pass.

**Files.** Change only the Step 1 workbench, its local schemas,
`tests/test_instruction_architecture.py`, check-map ownership when required,
and deterministic Horos files when required. Create arm-owned immutable
adapters and evidence below
`tests/fixtures/instruction-architecture/controls/`, development cases below
`tests/fixtures/instruction-architecture/development/`, synthetic hostile
cases below `tests/fixtures/instruction-architecture/hostile/`, and generated
development reports below
`tests/fixtures/instruction-architecture/evidence/development/`. Do not edit or
copy over WAI1 product paths, any Noema branch, the holdout reveal, a live
instruction, production loader or authority contract.

**Tests.** Add `NeutralSchemaTests`, `RawAdapterTests`, `Wai1ControlTests`,
`NoemaControlTests`, `SimpleControlTests`, `SectionGraphTests`,
`DevelopmentCaseTests`, `MutationTests`, `PathBoundaryTests` and
`ResourceBoundTests`. Cover all five adapter inventories, exact source
recovery, raw fallback, immutable control digests, closed JSON, duplicate keys,
Unicode scalar refusal, size/depth/count limits, symlink and replacement races,
atomic output, deterministic ordering, prompt-key absence and holdout
non-access. Run:

```text
python3 research/instruction-architecture/benchmark.py build-development --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --output tests/fixtures/instruction-architecture/evidence/development
python3 research/instruction-architecture/benchmark.py replay --cohort development --evidence tests/fixtures/instruction-architecture/evidence/development
python3 -m unittest tests.test_instruction_architecture -v
python3 tests/run_tests.py
python3 scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py research/instruction-architecture tests/test_instruction_architecture.py tests/fixtures/instruction-architecture
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py research/instruction-architecture tests/test_instruction_architecture.py tests/fixtures/instruction-architecture
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py research/instruction-architecture docs/instruction-architecture tests/fixtures/instruction-architecture
git diff --check
```

For an audit repair, run
`python3 tests/run_tests.py --elenchus-report {report}` with fresh path
`.elenchus/fiat-1046-step-2.json` and expected schema
`elenchus.unittest.v1`.

**Disciplines.** phylax: candidate files, JSON, Git objects and copied control
artifacts are untrusted bounded inputs; adapters use no shell, network or
secret. ephoros: one correlation joins source, arm, scenario, case, prompt,
mutation and output digests. metron: record parse/select/assembly wall time,
peak RSS, disk bytes, executable LOC and dependency count without tuning yet.
elenchus: every accepted hostile specimen becomes a parent-red guard before
repair. hypomnema: adapter contracts live beside their evidence; comments
explain only local invariants.

## Step 3: Run development selection and freeze the holdout experiment

**Goal.** Measure the five arms on the development cohort, select one candidate
version or select none, and freeze the complete holdout protocol, scorer,
seven-model matrix, two cohorts, routing policy and `$100` gross spend ceiling
before the holdout opens.

**Entry.** Step 2 is integrated; all five arms replay from identical
development inputs; controls retain their pinned digests; the holdout seal has
not been opened; no paid provider call or route probe has run in this Fiat
issue.

**Exit.** All of the following hold:

1. One content-addressed development aggregate ranks raw, WAI1, Noema, simple
   and section graph on coverage, exact fidelity, complete cold/warm bytes and
   locally available token counts, parse/select/assembly p50 and p95, peak RSS,
   disk, executable LOC, dependencies, mutations, crashes, nondeterminism and
   source-edit amplification. Component rows are mutually exclusive and every
   denominator reconciles.
2. Candidate selection applies the issue's fixed gates without holdout data.
   It records one frozen version and the measured trade, or records none. A
   source-span section graph may advance only if it preserves every operative
   span and exact literal, has zero deterministic authority/order/scope/recovery
   failure, meets 0.80 cold and 0.70 warm ratios on development, and beats the
   simple control after TCB, latency, upkeep and recovery are counted.
3. The preregistration binds 16 answer-producing holdout cases across the
   sealed logical skills and all required semantic classes. Each response is a
   bounded structured plan, decision, refusal, recovery or tool invocation;
   identifier-only multiple choice is diagnostic only. A deterministic scorer
   is representation-blind. Presentation order and case order use fixed seeds.
4. Two independent cohorts run all five arms through all seven model ids:
   `anthropic/claude-opus-5`, `google/gemini-3.7-flash`,
   `qwen/qwen3.8-27b`, `openai/gpt-5.6-sol`,
   `deepseek/deepseek-v4-pro-0813`, `moonshotai/kimi-k3`, and
   `z-ai/glm-5.3`. This preregisters 1,120 logical calls before bounded retries.
   Each model has one ordered provider policy with ZDR required; unavailable
   means unknown and no other model id substitutes.
5. The paired one-sided 95% degradation interval, trial aggregation, error
   taxonomy, critical-policy zero tolerance, prompt ratios and no-tuning rule
   are frozen. With 224 selected-versus-raw paired observations, zero observed
   regressions is sufficiently powered to exclude a degradation above 0.02;
   the exact implementation recomputes rather than assumes that bound.
6. `.hexaemeron/model-evaluation-authority.json` records the user's 2026-08-31
   authority, `$100.00` gross ceiling, credential location by label rather than
   value, reservation and settlement rules, retry cap, redaction policy and
   current credit observation. `benchmark.py preflight-spend` and
   `preflight-model-matrix` produce all six progressive Protasis report files
   for the three evaluator-design candidates. They make no paid call. The
   immutable design-evidence record passes `--transition step:4`.
7. The frozen packet can be emitted without answers; searching its prompt bytes
   finds no expected answer, scorer key, source class label or competing
   representation name. Offline development replay, focused tests and
   repository-selected checks pass.

**Files.** Change the workbench, schemas, tests, development evidence and
research README. Create
`tests/fixtures/instruction-architecture/development-selection.json`,
`preregistration.json`, `model-runtime-manifest.json`, `prompt-template.txt`,
`scorer.json`, `holdout-packet-commitment.json`, and answer-free packet
artifacts under `tests/fixtures/instruction-architecture/evidence/frozen/`.
Create the non-secret ignored authority and six progressive report files only
under `.hexaemeron/`. Update `docs/instruction-architecture/research-report.md`
with development evidence and the frozen protocol. Do not reveal a holdout
source, expected answer or response; make a paid call; change either control;
or change a production path.

**Tests.** Add `DevelopmentAggregateTests`, `CandidateSelectionTests`,
`PreregistrationTests`, `PromptContaminationTests`, `StatisticsTests`,
`BudgetLedgerTests`, `ModelPreflightTests` and `PacketCommitmentTests`.
Parent-red guards cover a candidate that loses to simple after TCB cost, an
underpowered interval, scorer material in a prompt, mismatched model id,
non-ZDR route, missing fee, over-budget reservation, lost uncertain attempt and
post-freeze threshold change. Run:

```text
python3 research/instruction-architecture/benchmark.py aggregate-development --evidence tests/fixtures/instruction-architecture/evidence/development --output tests/fixtures/instruction-architecture/development-selection.json
python3 research/instruction-architecture/benchmark.py freeze-experiment --selection tests/fixtures/instruction-architecture/development-selection.json --seal tests/fixtures/instruction-architecture/holdout-seal.json --output tests/fixtures/instruction-architecture/evidence/frozen
python3 research/instruction-architecture/benchmark.py preflight-spend --candidate neutral-evidence-workbench --authority .hexaemeron/model-evaluation-authority.json --max-gross-usd 100 --report .hexaemeron/design-reports/neutral-evidence-workbench-paid-evaluation-preflight.json
python3 research/instruction-architecture/benchmark.py preflight-model-matrix --candidate neutral-evidence-workbench --models anthropic/claude-opus-5,google/gemini-3.7-flash,qwen/qwen3.8-27b,openai/gpt-5.6-sol,deepseek/deepseek-v4-pro-0813,moonshotai/kimi-k3,z-ai/glm-5.3 --require-zdr --report .hexaemeron/design-reports/neutral-evidence-workbench-seven-model-preflight.json
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:4
python3 research/instruction-architecture/benchmark.py emit-packet --preregistration tests/fixtures/instruction-architecture/preregistration.json --seal tests/fixtures/instruction-architecture/holdout-seal.json --commitment-only --output tmp/framework-74-packet
python3 -m unittest tests.test_instruction_architecture -v
python3 tests/run_tests.py
python3 scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
git diff --check
```

Run the two preflight commands once for each of
`neutral-evidence-workbench`, `wai1-hosted-evaluator`, and
`noema-hosted-evaluator`, using the exact report paths recorded in
`.hexaemeron/design-evidence.json`. For an audit repair, run
`python3 tests/run_tests.py --elenchus-report {report}` with fresh path
`.elenchus/fiat-1046-step-3.json` and expected schema
`elenchus.unittest.v1`.

**Disciplines.** phylax: the no-call preflight reads only the named secret-file
metadata, official allowlisted endpoints and bounded catalog responses; no
credential enters argv or artifacts. ephoros: development selection,
experiment freeze, reservation and route events have stable run/candidate/case
correlations and explicit terminal causes. metron: the development baseline is
measured before selection and the `$100` ceiling includes all unsettled
attempts. elenchus: any change after freeze invalidates the candidate version;
it is not repaired against the same holdout. hypomnema: preregistration owns
the experiment, the selection record owns the provisional trade, and the
research report explains both.

## Step 4: Open the holdout once and run deterministic plus seven-model evidence

**Goal.** Reveal the sealed holdout exactly once, apply the frozen five arms,
run every deterministic conformance check and the preregistered 1,120-call
seven-model matrix under the gross ledger, and publish a content-addressed
pass, fail or inconclusive result without tuning.

**Entry.** Step 3 is integrated; its selection, preregistration, packet
commitment, scorer, model routes and thresholds are immutable; the design
evidence transition `step:4` is receipted; all six progressive reports pass;
the current OpenRouter credential and account credit can fund the next
reservation; no holdout reveal or paid issue-1046 call exists. If any predicate
fails, stop before a provider request rather than reducing the matrix.

**Exit.** All of the following hold:

1. One reveal record reproduces the Step 1 seal, source ref, selection method,
   seed, logical skills, byte coverage and closed cases. It proves the holdout
   was opened once after the candidate version and thresholds froze. Any drift
   is a terminal failed version.
2. All five frozen arms build against the same revealed sources. Deterministic
   round-trip, source traceability, classification, order, scope, negation,
   exception, literal, alias, unknown, refusal, recovery, authority, resource,
   stale-source, concurrent-edit, crash-recovery and safe-fallback checks emit
   exact per-case rows. Critical deterministic failure cannot be averaged away.
3. Every preregistered logical call either has a bounded accepted response or a
   durable unknown/refusal with model id, exposed provider revision, route,
   attempt, request digest, response digest, timing, usage, settled cost and
   reservation. The adapter uses HTTPS, no shell, a strict response cap and
   schema, at most three byte-identical attempts with fixed backoff, and no
   transcript-derived instruction. Raw public transcripts are retained after
   secret and header redaction.
4. The gross ledger starts at zero for this experiment, chains every
   reservation, settlement and retained uncertainty, reconciles OpenRouter
   usage and never exceeds `$100.00`. It checks live credit before each batch.
   A top-up changes only available credit, not the authority ceiling or
   experiment. No failed or uncertain attempt silently releases money.
5. Model and aggregate reports show all five arms, seven models, both cohorts,
   every prompt token/component row, per-case success, false allow/refuse,
   critical failures, latency, cost and exact paired interval. Provider-hidden
   tokenizer or revision values remain `unknown`. Unlike tokenizer counts are
   reported per model and never pooled as one token unit.
6. The selected candidate passes only if every issue gate holds on holdout:
   complete classification and operative/literal preservation; zero
   deterministic critical failure; no observed model critical regression; a
   one-sided paired 95% upper degradation bound at or below 0.02; median cold
   and warm prompt ratios at or below 0.80 and 0.70 for each preregistered
   model; deterministic reproducibility and no local-inference dependency; and
   dominance over the simple control after TCB and upkeep. Otherwise the
   result is fail or inconclusive with the exact predicate, not a tuned rerun.
7. `benchmark.py replay --cohort holdout --offline` reconstructs every
   deterministic row, prompt digest, score, cost sum, interval and aggregate
   without network access. Hostile mutations of source, transcript, ledger,
   route, score and report refuse. The full repository checks pass.

**Files.** Change only the workbench, tests and research report when a frozen
interface defect is not involved; a frozen-interface defect records a failed
version and stops candidate repair. Create the holdout reveal, exact arm
artifacts, redacted transcripts, attempt records, ledgers, per-case scores,
resource samples and aggregate reports below
`tests/fixtures/instruction-architecture/evidence/holdout/`. Update the model
runtime manifest only with observed provider revision, route and unknown
fields, never with a substituted model. Do not change preregistration,
selection, thresholds, scorer, prompt template, control source, live
instruction, production path or provider authority.

**Tests.** Add `HoldoutRevealTests`, `ProviderAdapterTests`,
`TranscriptBoundaryTests`, `SpendLedgerTests`, `HoldoutConformanceTests`,
`BehavioralScoringTests`, `IntervalTests`, `OfflineReplayTests` and hostile
evidence mutations. Fake providers cover every HTTP, JSON, retry, truncation,
usage, price, credit and redaction path before the live matrix. Run:

```text
python3 research/instruction-architecture/benchmark.py open-holdout --seal tests/fixtures/instruction-architecture/holdout-seal.json --preregistration tests/fixtures/instruction-architecture/preregistration.json --output tests/fixtures/instruction-architecture/evidence/holdout/reveal.json
python3 research/instruction-architecture/benchmark.py build-holdout --reveal tests/fixtures/instruction-architecture/evidence/holdout/reveal.json --output tests/fixtures/instruction-architecture/evidence/holdout/deterministic
python3 research/instruction-architecture/benchmark.py run-model-matrix --preregistration tests/fixtures/instruction-architecture/preregistration.json --authority .hexaemeron/model-evaluation-authority.json --credential-file /Users/kethcode/.config/codex/secrets/openrouter-api-key --output tests/fixtures/instruction-architecture/evidence/holdout/provider
python3 research/instruction-architecture/benchmark.py aggregate-holdout --evidence tests/fixtures/instruction-architecture/evidence/holdout --output tests/fixtures/instruction-architecture/evidence/holdout/aggregate.json
python3 research/instruction-architecture/benchmark.py replay --cohort holdout --evidence tests/fixtures/instruction-architecture/evidence/holdout --offline
python3 -m unittest tests.test_instruction_architecture -v
python3 tests/run_tests.py
python3 scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py research/instruction-architecture tests/test_instruction_architecture.py tests/fixtures/instruction-architecture/evidence/holdout
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py research/instruction-architecture tests/test_instruction_architecture.py tests/fixtures/instruction-architecture/evidence/holdout
git diff --check
```

For an audit repair, run
`python3 tests/run_tests.py --elenchus-report {report}` with fresh path
`.elenchus/fiat-1046-step-4.json` and expected schema
`elenchus.unittest.v1`. A repair that changes any frozen experiment byte does
not rerun the holdout in this issue.

**Disciplines.** phylax: credential, HTTPS, mutable catalog, provider output,
filesystem and concurrency boundaries are closed by allowlists, caps,
redaction, strict parsing, no shell, atomic writes and identity checks.
ephoros: every request and retry has one correlation from source through cost
and score; terminal stop causes are explicit. metron: compare identical cases
and model routes, reserve before attempts, retain p50/p95 and tails, and stop at
`$100`. elenchus: provider and evidence failures reproduce under fakes; a
holdout semantic failure invalidates the version rather than inviting tuning.
hypomnema: raw evidence stays machine-readable; the research report states the
observed boundary without deciding the final architecture early.

## Step 5: Publish the decision, implementation boundary and offline handoff

**Goal.** Rank the complete evidence, give every WAI1 and Noema mechanism an
`adopt`, `adapt` or `reject` disposition, select one architecture or none, and
publish the exact future implementation and recovery handoff without filing or
executing it.

**Entry.** Step 4 is integrated; its holdout reveal, deterministic and model
reports, ledger, interval, prompt ratios, costs, failures and offline replay are
immutable and green as evidence. A candidate need not have passed, but every
unknown and failed gate must be retained. Fetch `origin/main` and record the
current next-free ADR number only at publication; no temporary decision path
may overwrite an independently landed ADR.

**Exit.** All of the following hold:

1. A numbered ADR ranks raw, WAI1, Noema, simple and the distinct candidate on
   one dominance frontier, names every failed or unknown gate, records the
   chosen trade and selects exactly one architecture or explicitly selects
   none. Every substantive #909 and #942 mechanism has one measured
   `adopt`/`adapt`/`reject` row. Historical WAI1 and Noema results remain pinned
   and are not rewritten as comparable measurements.
2. If and only if the chosen candidate passed every holdout gate,
   `docs/instruction-architecture/implementation-contract.md` fixes semantic
   domain, schema/grammar, canonical form, source mapping, review projection,
   slice algorithm, exact literals, authority and authorship, deterministic
   APIs, versioning, migration, rollback, observability, bounds and
   compatibility gates. If no candidate passed, the path is absent and the ADR
   states the next bounded research question.
3. `docs/instruction-architecture/follow-up-decomposition.md` gives a
   ready-to-file but unfiled set of repository boundaries, ordered changes,
   acceptance tests, migration and rollback sequence, review points and
   dependencies. It does not create, assign or execute an issue.
4. The final research report reconciles all physical, unique, reachable and
   prompt denominators; documents corpus partitions, cases, models, provider
   terms, prompts, scoring, confidence interval, TCB/upkeep measurements,
   costs, failures and reproduction commands; links every claim to a retained
   digest; and says plainly that no production integration occurred.
5. One offline command verifies the closed package from repository bytes,
   including corpus, controls, selection, seal/reveal, deterministic results,
   transcripts, ledgers, statistics, ADR claims and optional implementation
   contract. Tampering, missing evidence or a claim/report disagreement
   refuses. The full repository runner, discipline checks, Protasis,
   Imprimatur, audit synopsis, Horos, dead-code currency when selected, and
   whitespace checks pass.
6. The final branch contains only research harnesses, schemas, fixtures,
   evidence, tests, specifications, the ADR, required generated repository
   boundary records and Fiat audit artifacts. It changes no live behavior and
   does not merge #942, run `sync-run`, register or deploy anything, convert
   Markdown, file follow-up issues or close #1030.

**Files.** Change the research report, README, workbench and tests only when
needed to bind final evidence without changing frozen semantics. Create the
temporary decision path
`docs/decisions/select-an-agent-instruction-architecture.md`, rename it and all
current references to the next free `ADR-NNN` at integration, create
`docs/instruction-architecture/follow-up-decomposition.md`, and create
`docs/instruction-architecture/implementation-contract.md` only on a passing
selection. Permit deterministic `.horos` regeneration and a report-only
`.dead-code/baseline.json` refresh only when repository checks require them.
Do not change any other product, plugin, root contract, dependency, CI or
external-repository path.

**Tests.** Add `DecisionConsistencyTests`, `MechanismDispositionTests`,
`ImplementationContractTests`, `FollowUpBoundaryTests`,
`ResearchReportTests` and `CompleteReplayTests`. They bind every reported
number and digest, exact candidate status, all #909/#942 rows, optional-contract
iff logic, absence of filed issue ids, production-path exclusion and one-command
offline replay. Run:

```text
python3 research/instruction-architecture/benchmark.py verify-package --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --evidence tests/fixtures/instruction-architecture/evidence --decision docs/decisions/select-an-agent-instruction-architecture.md
python3 research/instruction-architecture/benchmark.py replay --cohort all --evidence tests/fixtures/instruction-architecture/evidence --offline
python3 -m unittest tests.test_instruction_architecture -v
python3 tests/run_tests.py
python3 scripts/run_checks.py --full --jobs 8
python3 scripts/dead_code.py baseline --check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/instruction-architecture/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/instruction-architecture/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/instruction-architecture/study.md docs/instruction-architecture/runbook.md docs/instruction-architecture/corpus-reconciliation.md docs/instruction-architecture/research-report.md docs/instruction-architecture/follow-up-decomposition.md docs/decisions/select-an-agent-instruction-architecture.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py research/instruction-architecture tests/test_instruction_architecture.py tests/fixtures/instruction-architecture
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py research/instruction-architecture tests/test_instruction_architecture.py tests/fixtures/instruction-architecture
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py research/instruction-architecture docs/instruction-architecture docs/decisions/select-an-agent-instruction-architecture.md tests/fixtures/instruction-architecture
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Include the implementation contract in Imprimatur and Hypomnema commands when
it exists. For an audit repair, run
`python3 tests/run_tests.py --elenchus-report {report}` with fresh path
`.elenchus/fiat-1046-step-5.json` and expected schema
`elenchus.unittest.v1`.

**Disciplines.** phylax: final replay opens no network or credential and proves
all external evidence is inert, bounded and redacted. ephoros: the final report
maps every decision to source, candidate, case, model, cost and replay ids;
there is no production alert. metron: publish baselines, ratios, tails, costs
and upkeep with their exact units and do not pool unlike tokenizers. elenchus:
any packaging or prose mismatch is parent-red and guarded; no semantic holdout
failure is repaired in this version. hypomnema: the ADR owns the costly choice,
the optional contract owns future implementation, the research report owns
evidence and the decomposition owns unfiled work.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: All of the following hold:

1. The committed corpus manifest binds exactly the 106 agent-facing Markdown
   files at the entry ref: 32 canonical skill contracts, 18 `AGENTS.md`, 18
   Promise Machine contracts and 38 Markdown references. It records path,
   logical document, class, size, SHA-256, exact duplicate group, canonical
   owner, authority tier, loader roots, scenario reachability and external
   runtime ownership. A reconciliation report reproduces 1,545,537 physical
   bytes, 89 exact-unique files and 1,074,093 exact-unique bytes or refuses with
   the precise changed predicate.
2. Every physical byte belongs to exactly one range classified as governed
   operative semantics, exact literal or evidence, human-only explanation or
   rationale, generated duplicate, or unsupported/unknown. Ranges are ordered,
   non-overlapping, gapless and source-digest bound. Any unsupported operative
   range is visible and blocks later selection.
3. The loader graph proves each root and edge from a source path, byte span and
   digest. It distinguishes unconditional host loading from conditional linked
   references and excludes test fixtures and the moved `skills-runtime`
   package. File presence alone never creates an edge.
4. A deterministic stratified selection fixes a development cohort covering
   at least 50% of unique bytes, every shared root/runtime contract, at least
   12 logical skills, every observed construct and authority tier, and every
   size decile. A disjoint sealed holdout fixes at least 20% of unique bytes and
   five logical skills with authority, failure, recovery, exact-literal and
   cross-document cases. The seal binds source, method, seed, membership and a
   closed future case envelope; Step 1 does not open or score that envelope.
5. `benchmark.py verify-corpus`, `benchmark.py verify-loader`,
   `benchmark.py verify-partition`, and `benchmark.py verify-seal` each emit one
   bounded correlated JSON result and exit zero. Repeating all four commands
   is byte-identical. The committed runbook matches its amended receipted
   bytes. The committed study differs from its receipted bytes only in the ten
   relative plugin links whose destination moved one directory deeper; a guard
   reverses that relocation and recovers the receipted study SHA-256. The
   focused tests and repository-selected checks pass, and no live instruction
   or production path changes.
Complete replacement Tests: Add `CorpusManifestTests`, `BytePartitionTests`,
`LoaderGraphTests`, and `HoldoutSealTests` for exact inventory, duplicate
groups, range closure, source-span anchors, conditional edges, runtime-owner
exclusions, cohort coverage, disjointness, seed replay, sealed-envelope
non-disclosure, study-link relocation and stale-source refusal. Run these exact
commands from the repository root:

```text
python3 research/instruction-architecture/benchmark.py verify-corpus --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
python3 research/instruction-architecture/benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
python3 research/instruction-architecture/benchmark.py verify-partition --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
python3 research/instruction-architecture/benchmark.py verify-seal --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
python3 -m unittest tests.test_instruction_architecture.CorpusManifestTests tests.test_instruction_architecture.BytePartitionTests tests.test_instruction_architecture.LoaderGraphTests tests.test_instruction_architecture.HoldoutSealTests -v
python3 scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
cmp -s .hexaemeron/runbook.md docs/instruction-architecture/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/instruction-architecture/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/instruction-architecture/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/instruction-architecture/study.md docs/instruction-architecture/runbook.md docs/instruction-architecture/corpus-reconciliation.md
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For an audit repair, run
`python3 tests/run_tests.py --elenchus-report {report}` with the fresh report
path `.elenchus/fiat-1046-step-1.json`. The expected schema is
`elenchus.unittest.v1`. A missing, stale, malformed or infrastructure-failed
report is inconclusive.
**Why.** The receipted study lived one directory below the repository root;
its committed copy lives two directories below it. Keeping the ten original
relative links made every target absent at the shipped path and failed the
required Hypomnema pointer lint. Relocating only those links preserves their
targets and leaves every research statement unchanged.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: All of the following hold:

1. The committed corpus manifest binds exactly 175 agent-facing Markdown files
   and 2,069,258 physical bytes at the entry ref. It retains the original 32
   skill contracts, 18 `AGENTS.md` contracts, 18 Promise Machine contracts and
   38 Markdown references, and adds one identity contract, one conditional
   identity roster, one installed-router contract, one vendored-overlay
   contract, one frontier policy, 26 frontier ledgers, 14 worker prompts and 24
   operation references. It records path, logical document, document class,
   admission kind, size, SHA-256, exact duplicate group, canonical owner,
   authority tier, loader roots, scenario reachability and external runtime
   ownership. Exact whole-file deduplication yields 158 unique files and
   1,597,814 unique bytes. The reconciliation enumerates all 69 additions by
   class, path, bytes and source anchor, and classifies excluded human,
   background, generated, historical, dynamic-target and unavailable-operation
   links rather than treating their presence as a load.
2. Every physical byte belongs to exactly one range classified as governed
   operative semantics, exact literal or evidence, human-only explanation or
   rationale, generated duplicate, or unsupported/unknown. Ranges are ordered,
   non-overlapping, gapless and source-digest bound. Any unsupported operative
   range is visible and blocks later selection.
3. The loader graph proves every root and edge from a source path, byte span
   and digest. It distinguishes unconditional loads from installed-route,
   credential-identity, vendored-overlay, frontier-gate, worker-dispatch and
   operation-branch conditions; resolves a same-repository canonical URL to a
   pinned local path only on an exact repository-and-path match; recursively
   closes required Markdown loads; and refuses a manifest loader-root or
   scenario claim that graph reachability does not reproduce. File presence, a
   human or background link, a generated reader artefact, a historical record
   or an unavailable-operation specification creates no edge. Test fixtures
   and the moved `skills-runtime` package remain excluded.
4. A deterministic stratified selection fixes a development cohort covering
   at least 50% of unique bytes, every shared root/runtime contract, at least
   12 logical skills, every observed construct and authority tier, every
   admitted document class and every size decile. A disjoint sealed holdout
   fixes at least 20% of unique bytes and five logical skills with authority,
   failure, recovery, exact-literal and cross-document cases. The seal binds
   source, method, seed, membership and a closed future case envelope; Step 1
   does not open or score that envelope.
5. `benchmark.py verify-corpus`, `verify-loader`, `verify-partition` and
   `verify-seal` each emit one bounded correlated JSON result and exit zero.
   Repeating all four commands is byte-identical. `build-baseline` reproduces
   the five committed records, their inventory and the reconciliation byte for
   byte without permitting any output/reconciliation alias. The committed
   runbook matches its amended receipted bytes. The committed study differs
   from its receipted bytes only in the ten guarded relative-link relocations.
   Focused and root tests attributable to the changed paths pass; any unrelated
   repository-selected baseline or environment failure is reproduced on the
   parent and recorded. No live instruction or production path changes.
Complete replacement Tests: Add `CorpusManifestTests`, `BytePartitionTests`,
`LoaderGraphTests` and `HoldoutSealTests` for the exact 175-path inventory, all
twelve document-class counts and four denominators; the 69-path admission
inventory; the 26-ledger, 14-worker-prompt and 24-operation-reference closures;
same-repository canonical-URL resolution; recursive required-load closure;
explicit refusal of file-presence, human/background, generated, historical,
dynamic-target and unavailable-operation edges; exact duplicate groups; range
closure; source-span anchors; unconditional and conditional edges;
graph-derived loader-root and scenario equality; runtime-owner exclusions;
cohort coverage and disjointness; seed replay; sealed-envelope non-disclosure;
study-link relocation; output/reconciliation non-aliasing; host-independent
integer bounds; and stale-source refusal. Run these exact commands from the
repository root under the pinned runtime:

```text
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py build-baseline
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-corpus --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-partition --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-seal --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
uv run --no-project --python 3.14.6 python -m unittest tests.test_instruction_architecture.CorpusManifestTests tests.test_instruction_architecture.BytePartitionTests tests.test_instruction_architecture.LoaderGraphTests tests.test_instruction_architecture.HoldoutSealTests -v
uv run --no-project --python 3.14.6 python scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
cmp -s .hexaemeron/runbook.md docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/instruction-architecture/study.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/instruction-architecture/study.md docs/instruction-architecture/runbook.md docs/instruction-architecture/corpus-reconciliation.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
uv run --no-project --python 3.14.6 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Run the four verifiers twice and require byte-identical stdout. After
`build-baseline`, require the five records, artifact inventory and
reconciliation to match the committed bytes. For an audit repair, run
`uv run --no-project --python 3.14.6 python tests/run_tests.py --elenchus-report .elenchus/fiat-1046-step-1.json`;
require schema
`elenchus.unittest.v1`. A missing, stale, malformed or infrastructure-failed
report is inconclusive.
**Why.** Audit round 4 proved that the starting 106-path census omitted 69
source-directed identity, routing, overlay, frontier, worker and operation
documents. It also proved that graph reachability and manifest loader roots
could disagree, the integer cap depended on mutable host configuration, and
two individually allowed scratch outputs could alias. The replacement binds
the corrected corpus and those refusal checks without changing the selected
design or any production source.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: All of the following hold:

1. The committed corpus manifest binds exactly 176 agent-facing Markdown files
   and 2,071,863 physical bytes at the entry ref. It retains every class from
   the prior 175-path closure and adds
   `plugins/anamnesis/docs/demo.md` as a 2,605-byte unique
   `operation_reference`, source-directed by the exact
   `../../docs/demo.md` span in Anamnesis's canonical skill. The corpus now has
   25 operation references, 70 source-directed additions totalling 526,326
   bytes, 159 exact-unique files and 1,600,419 exact-unique bytes. The
   reconciliation enumerates the new path, digest and anchor and proves that
   recursively resolving every admitted document adds no second path.
2. Every physical byte remains in one ordered, gapless, digest-bound partition
   range. Unsupported operative bytes remain zero. Exact duplicates remain
   limited to the root Promise Machine contract and its generated copies; the
   Anamnesis document is unique governed instruction rather than evidence or a
   generated duplicate.
3. The loader graph retains the complete source-proved potential edge
   inventory, but each declared scenario is one realizable invocation. A
   scenario binds one host route, one selected canonical skill and a closed,
   sorted condition vector for credential identity, operation choice, frontier
   gates, worker dispatch and nested selection. Scenario reachability includes
   only matching edges. Every potential conditional edge appears in at least
   one scenario, while mutually exclusive siblings never co-occur: a Kronos
   invocation chooses one target skill before exact Fiat dispatch; an Ariadne
   invocation chooses one supported operation; repository checkout never loads
   the isolated `PORTABLE.md`; standalone mode never loads the repository
   prelude. Production validation refuses fragment roots, incomplete route or
   selection scope, an unknown condition, an uncovered potential edge, a
   sibling-branch union and any manifest reachability claim the graph does not
   reproduce.
4. Because the old unopened holdout is only 319,564 of 1,600,419 unique bytes,
   rerun the unchanged seed and selection method before any candidate or case
   construction. The replacement holdout is exactly `ariadne`, `fizz`,
   `fizz-sync`, `hermes` and `kronos`: 33 unique paths and 320,086 bytes
   (0.200001). Development is the disjoint remaining 1,280,333 bytes
   (0.799999) and still covers every shared contract, document class,
   authority tier, construct and size decile. The replacement seal binds the
   corrected source, membership and closed 16-slot envelope with `opened` false
   and no prompt, answer, scorer key or model output.
5. Every source-bound path field is a canonical non-empty printable-ASCII POSIX
   relative path of at most 1,024 bytes, with no empty, `.` or `..` segment,
   backslash, control byte or trailing slash. Runtime and Draft 2020-12 schema
   accept the same structural language. `build-baseline` reproduces all five
   records, their inventory and reconciliation byte for byte; all four
   verifiers repeat byte-identically; the amended study and runbook receipts,
   focused/root tests and parent-attributable selected checks pass; no live
   instruction or production path changes.

Complete replacement Tests: Extend `CorpusManifestTests`,
`LoaderGraphTests`, `BytePartitionTests` and `HoldoutSealTests` to cover the
exact 176-path inventory, twelve class counts, four denominators, 70 admissions
and 25 operation references; the Anamnesis demo's exact path, size, digest,
owner and source span; a second fixed-point pass with no addition; exact
duplicate and partition closure; source-span and manifest reachability
equality; and the exact replacement cohort, 33 holdout paths, byte floors,
disjointness, unchanged seed, unopened seal and forbidden answer fields.

Add scenario guards that independently reconstruct each route and condition
vector; require complete repository, isolated Agent Skills and standalone
preludes; prove one Kronos target and one Ariadne operation per invocation;
reject sibling target or operation unions, unknown conditions, wildcard
conditional leakage, fragment roots, cross-runtime selection and a potential
edge with no witnessing scenario. Add runtime and schema cases for empty paths,
`.`, `..`, `a/.`, `a/..`, `a//b`, `a/`, absolute paths, backslashes, controls,
non-ASCII input and 1,024/1,025-byte bounds, while retaining every prior JSON,
Git, process, output-alias, stale-source and race guard. Run these exact
commands from the repository root under the pinned runtime:

```text
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py build-baseline
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-corpus --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-partition --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-seal --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
uv run --no-project --python 3.14.6 python -m unittest tests.test_instruction_architecture.CorpusManifestTests tests.test_instruction_architecture.BytePartitionTests tests.test_instruction_architecture.LoaderGraphTests tests.test_instruction_architecture.HoldoutSealTests -v
uv run --no-project --python 3.14.6 python scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
cmp -s .hexaemeron/runbook.md docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/instruction-architecture/study.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/instruction-architecture/study.md docs/instruction-architecture/runbook.md docs/instruction-architecture/corpus-reconciliation.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
uv run --no-project --python 3.14.6 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Run the four verifiers twice and require byte-identical stdout. After
`build-baseline`, require the five records, artifact inventory and
reconciliation to match the committed bytes. For an audit repair, run
`uv run --no-project --python 3.14.6 python tests/run_tests.py --elenchus-report .elenchus/fiat-1046-step-1.json`;
require schema `elenchus.unittest.v1`, and report an infrastructure-failed
fixture overlay as inconclusive rather than relabelling a supplementary guard
run.
**Why.** Audit round 6 found one operative Anamnesis document outside the
receipted fixed point, which made the unopened holdout miss its byte floor. It
also proved that route-by-skill scenarios still activated impossible branch
unions and that schema/runtime path handling admitted non-canonical aliases or
disagreed on terminal traversal and Unicode length. The replacement repairs
those source, sampling and identity predicates before any candidate or paid
evaluation exists.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: All of the following hold:

1. The committed corpus manifest binds exactly 188 agent-facing instruction
   and reference files and 2,290,439 physical bytes at the entry ref. It
   retains the prior 176 Markdown documents and adds exactly 12
   `structured_reference` JSON documents: all nine non-Markdown files under
   admitted canonical `references/` directories and Imprimatur's three named,
   mandatory lexicons. Their path, size, SHA-256, owner, admission rule and
   source/runtime anchors match the frozen inventory; no script, output
   template, test/eval, example/specimen, generated output or caller/project
   input enters. Exact whole-file deduplication yields 171 files and 1,818,995
   bytes. An independent extension-agnostic fixed-point pass reproduces the
   inventory and a second pass adds nothing.
2. Every physical byte belongs to one ordered, gapless, digest-bound partition
   range. The totals are exactly 1,473,399 governed operative, 345,596 exact
   literal or evidence, 471,444 generated duplicate, zero human-only and zero
   unsupported bytes. All 218,576 new bytes are exact literal or evidence; all
   are unique; the existing Promise Machine family remains the only duplicate
   family.
3. The loader graph proves each actual read from frozen source and runtime
   spans and labels it as agent/prompt, mandatory executable or reference-only.
   Hermes's corpus and schema are immutable beside-script inputs on every
   Hermes run; Synkrisis's committed rules are read only by realizable
   `diagnose` and `verify` invocations; Imprimatur reads all three lexicons on
   every lint invocation. The six Homologia/Synkrisis schemas remain
   reference-only with empty loader roots and scenario reachability. Validation
   refuses an omitted qualifying input, an invented schema edge, an executable
   edge without both canonical-skill and runtime-read anchors, a reference-only
   document with claimed reachability, and any manifest/graph/scenario
   disagreement. Every prior route, condition-vector, branch-exclusivity and
   canonical-path guard remains.
4. The unchanged seed and selection method produce exactly `alexandria`,
   `fizz`, `phylax`, `probitas` and `sapheneia`: 31 unique paths and 363,804
   bytes (`0.200003`). Development is the disjoint remaining 140 paths and
   1,455,191 bytes (`0.799997`) and covers every shared contract, class,
   authority tier, construct and size decile. The replacement seal binds the
   corrected source and membership plus the closed 16-slot envelope, has
   `opened` false, and contains no prompt, answer, scorer key or model output.
5. `build-baseline` atomically reproduces all five records, their inventory and
   reconciliation byte for byte. `verify-corpus`, `verify-loader`,
   `verify-partition` and `verify-seal` each emit one bounded correlated JSON
   result and repeat byte-identically. Draft 2020-12 schemas and runtime
   validators remain equivalent; the amended study/runbook receipt, focused
   and root suites, parent-attributable selected checks, Elenchus evidence,
   Phylax, Ephoros, Hypomnema, Protasis, Imprimatur, Horos, synopsis and diff
   gates pass. No live instruction, loader, router, marketplace or production
   path changes.

Complete replacement Tests: Extend `CorpusManifestTests`,
`BytePartitionTests`, `LoaderGraphTests` and `HoldoutSealTests` to bind the
exact 188-path inventory, 13 document-class counts, four denominators, all 12
added paths, sizes, SHA-256s, owners and anchors, the 12-file 218,576-byte
subtotal, the exact five partition totals, unique/duplicate closure, and a
second fixed-point pass with no addition. Mutate a reference suffix away from
`.md`, omit each JSON reference, move or omit each Imprimatur lexicon, change a
mandatory runtime read, and add a decoy script, template, fixture, example or
caller input; require the first five classes to fail closed and the decoys to
remain excluded.

Add source/runtime-equivalence cases for Hermes's fixed corpus/schema
resolution and reads, Synkrisis `diagnose`/`verify` rule reads, and Imprimatur's
three fixed lexicon reads. Require the six reference-only schemas to have empty
runtime roots and scenario reachability; reject invented edges, missing
executable edges, false all-operation reachability and manifest/graph
disagreement. Retain every prior Git/source, strict-JSON, schema/runtime path,
process, output-alias, resource, atomic-write, race, route, scenario,
branch-exclusivity and seal guard. Bind the exact replacement holdout, 31 held
paths, byte floor, disjoint 140-path development cohort, unchanged seed/method,
unopened seal and forbidden answer fields.

Run these exact commands from the repository root under the pinned runtime:

```text
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py build-baseline
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-corpus --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-partition --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-seal --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
uv run --no-project --python 3.14.6 python -m unittest tests.test_instruction_architecture.CorpusManifestTests tests.test_instruction_architecture.BytePartitionTests tests.test_instruction_architecture.LoaderGraphTests tests.test_instruction_architecture.HoldoutSealTests -v
uv run --no-project --python 3.14.6 python tests/run_tests.py --elenchus-report .elenchus/fiat-1046-step-1.json
uv run --no-project --python 3.14.6 python scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
cmp -s .hexaemeron/runbook.md docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/instruction-architecture/study.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/instruction-architecture/study.md docs/instruction-architecture/runbook.md docs/instruction-architecture/corpus-reconciliation.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
uv run --no-project --python 3.14.6 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Run the four verifiers twice and require byte-identical stdout. Rebuild once
into a fresh `tmp/` destination with `--output` and `--reconciliation`; require
all five records, artifact inventory and reconciliation to equal the committed
bytes. Require Elenchus schema `elenchus.unittest.v1`; an
infrastructure-failed fixture overlay remains inconclusive.

**Why.** Audit round 7 found a content-authority bug: extension filtering
excluded 218,576 bytes of exact rules and reference evidence while every
current verifier passed, invalidating the source, partition and sealed sampling
denominators before evaluation. The replacement fixes the admission predicate
and preserves honest zero reachability for schemas that production does not
load.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: Retain the current Step 1 exit, with loader-graph clause 3 additionally requiring 25 source-proved Kronos ranking-scan edges from Kronos to every governed non-Kronos frontier ledger across all three Kronos bases and every declared Kronos condition vector. The exact graph inventory is 19 roots, 237 host edges, 233 scenario roots, 277 scenario edges and six reference-only records; corpus, partition, cohort and seal counts remain unchanged. Every Kronos scenario reaches all 25 candidate ledgers and the shared versioning policy, exactly one selected target skill and Fiat's dispatch contract, while target selection alone does not execute that target's mandatory structured inputs. The existing `benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json` command is the executable exit check.

Complete replacement Tests: Retain every current Step 1 test and command. Add an independent exhaustive oracle requiring every Kronos scenario to reach exactly the 25 governed non-Kronos frontier ledgers, the shared versioning policy, exactly one selected target and no target-only mandatory executable input; mutate one Kronos ranking edge and require production validation to refuse the missing ledger. Retain the direct Hermes, Fiat-Scribe-to-Imprimatur and Synkrisis diagnose/verify executable-input oracles.
**Why.** Audit round 8 found that the current Kronos scenarios model target selection but omit the mandatory ranking scan that precedes it, while a separate owner-document shortcut invents target executable reads. Exact scenario denominators require both sides of that boundary.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: Retain every current Step 1 exit requirement, with loader-graph clause 3 additionally requiring the complete semantic-condition-vector product across host routes. Derive each vector by canonical-owner and shortest-conditional-chain priority, emit it on every tied repository, isolated Agent Skills and standalone base, and use route order only for deterministic serialization. The exact graph inventory is 19 roots, 237 host edges, 656 scenario roots, 277 scenario edges and six reference-only records. The 31 selected skills have 198 identical non-credential vectors per route; repository and isolated Agent Skills each add exactly 31 credential-backed vectors, while standalone adds none, for route totals 229/229/198. Exact repository/Agent-Skills/standalone distributions are Ariadne 7/7/6, Kronos 28/28/27 and Synkrisis 5/5/4. Every potential conditional edge has a realizable witness; sibling operations and targets remain exclusive; every Kronos vector reaches all 25 candidate ledgers, shared versioning, exactly one target and Fiat dispatch without executing target-only mandatory inputs. Production validation independently reconstructs the normalized vector set for every selected skill, requires equality across all three routes after removing the credential condition, and requires that credential condition only on the two checkout routes.

The corpus stays at 188 physical files and 2,290,439 bytes, 171 unique files and 1,818,995 bytes. Partition totals, 31-path/363,804-byte holdout and 140-path/1,455,191-byte development membership remain unchanged. Regenerate the five baseline records, artifact inventory and reconciliation atomically; require all seven fresh outputs to match committed bytes. Keep the sealed membership digest and case-envelope digest unchanged, `opened` false, and update only manifest-bound cohort, seal and inventory identities. The four existing verifier commands remain executable exit checks and must repeat byte-identically.

Complete replacement Tests: Retain every current Step 1 test and command. Replace exact scenario-root assertions 233 and 27-Kronos with 656 and 83, and bind the route totals 229/229/198 plus Ariadne 7/7/6, Kronos 28/28/27 and Synkrisis 5/5/4. Add an independent source-derived oracle that strips only `credential:github-contributor`, reconstructs every selected skill's condition-vector set, and proves identical repository, isolated Agent Skills and standalone sets; separately require exactly one credential vector per selected skill on repository and isolated Agent Skills and none on standalone. Delete one route's otherwise-valid condition vector and remove that identifier from every edge scope; require production validation to refuse the incomplete route product. Retain the independent 25-ledger Kronos scan, branch-union, execution-versus-read, direct Hermes, Fiat-Scribe-to-Imprimatur and exclusive Synkrisis `diagnose`/`verify` oracles. Rebuild into a fresh `tmp/` destination, validate the schema and all six instances, run the four verifiers twice, compare all seven outputs byte for byte, then run the focused and repository-selected suites and every existing Step 1 discipline gate.

**Why.** The current candidate selector uses route order to choose one representative among semantically equivalent bases, and the current validator quantifies only over roots that survived that selection. Both therefore certify an incomplete route-by-condition product. The replacement makes host route a measured invocation dimension and leaves semantic ownership, branch exclusivity and execution boundaries intact.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: All of the following hold:

1. The committed corpus manifest binds exactly 190 agent-facing instruction
   and reference files and 2,290,443 physical bytes at the entry ref. Exact
   whole-file deduplication yields 173 files and 1,818,999 bytes. Fourteen fixed
   non-Markdown inputs are admitted: the prior 12 JSON inputs plus X-Ray's
   two-byte local `VERSION` and Solidity-auditor's distinct two-byte local
   `VERSION`, each proved by its direct `SKILL.md` Read instruction. Their remote
   version fetches remain external runtime observations. An extension-agnostic
   fixed-point pass reproduces the exact inventory and a second pass adds
   nothing. Fizz's unread `VERSION`, descriptive toolchain pins, the generated
   Horos boundary, optional shell-expanded configuration and dynamic remote or
   target inputs remain excluded with exact source reasons. No script, output
   template, test/eval, example/specimen, generated output or caller/project
   input enters.
2. Every physical byte belongs to one ordered, gapless, digest-bound partition
   range. The totals are exactly 1,473,399 governed operative, 345,600 exact
   literal or evidence, 471,444 generated duplicate, zero human-only and zero
   unsupported bytes. The Promise Machine family remains the only exact
   duplicate family.
3. A source-owned
   `tests/fixtures/instruction-architecture/invocation-profiles.json` record
   under schema `wildcat-instruction-architecture-invocation-profiles/v1`
   contains exactly 519 normalized rows across all 31 selected skills. One row
   is one bounded prompt-bearing operation, directive or dispatch phase and
   carries a stable profile id, selected skill, applicability predicate,
   independent optional/fallback state, exclusive group, exact required
   canonical documents, exact worker prompts, fixed non-Markdown inputs classified as
   executed or read-only, and exact source path/span/digest evidence. Sequential
   same-operation requirements are one union; exclusive modes are separate;
   independent optional and fallback states form their complete product; a
   gate-only frontier is separate from ordinary execution. The exact per-skill
   counts are `alexandria=3, anamnesis=3, ariadne=7, berean=2, brevitas=2,
   elenchus=3, ephoros=2, fiat=415, fizz=6, fizz-convert=1, fizz-sync=1,
   hermes=2, homologia=2, horos=2, hypomnema=2, imprimatur=2, janus=2,
   kronos=26, lazarus=5, lemma=3, metron=3, pandects=2, phylax=3,
   probitas=3, protasis=3, sapheneia=2, solidity-auditor=1, synkrisis=4,
   tabularium=4, vulgate=2, x-ray=1`. Fiat's 415 split exactly into 360
   implement, 26 audit, 16 prose, two study and 11 other bounded controller
   operations. Production generation and validation consume this record; they
   never derive it by minimizing graph edges or by quantifying over roots the
   generator already emitted.
4. The loader graph retains 19 physical host roots and emits exactly 2,595
   scenario roots from the profile ledger. Let `N=519`: repository checkout has
   `2N=1,038`, isolated Agent Skills has `2N=1,038`, and standalone has
   `N=519`. Every normalized profile appears once with credential absent and
   once with credential present on each checkout route and once with credential
   absent on standalone. Stripping only credential state yields the same 519
   ids and required-byte unions on all three routes. Every graph edge is proved
   by a frozen source or mandatory-runtime span and labelled agent/prompt,
   mandatory executable, fixed agent/prompt input or reference-only. The three
   Imprimatur Markdown
   `References` links and three descriptive Pandects documents join the six
   Homologia/Synkrisis schemas as exactly 12 reference-only records with empty
   production roots and reachability; Imprimatur's three lexicons, Hermes's
   corpus/schema and Synkrisis's `diagnose`/`verify` rules retain their exact
   mandatory-executable profiles. All five vendored skills load `PROMISES.md`
   in every operational profile.

   Every Kronos profile reads its own ledger. Default full scope reads all 25
   governed non-Kronos ledgers and emits one rank-only plus 21 currently open
   single-target dispatch profiles; phase-only reads its fixed six ledgers and
   emits one rank-only plus three currently open single-target dispatch
   profiles. No bounded Kronos profile loads shared `VERSIONING.md`, dispatches
   a mature target, unions multiple targets or executes a target-only input.
   Arbitrary named Kronos scopes and Fiat `version-relations` target subsets are
   explicitly classified as parameterized external runtime input and contribute
   no concrete source-frozen scenario root. On Fiat audit, a recorded Pashov
   suite and the audit-loop waiver are exclusive: the former loads X-Ray,
   X-Ray's local `VERSION`, Solidity-auditor, Solidity-auditor's local `VERSION`
   and the applicable Fizz branch; the latter loads the
   Phylax/Ephoros/Hypomnema non-Solidity gates. Every Fiat implement, audit,
   prose and study profile preserves the applicable inline/delegated worker
   alternative and complete discipline or mask bundle.
5. The unchanged seed and selection method still produce exactly `alexandria`,
   `fizz`, `phylax`, `probitas` and `sapheneia`: 31 exact-unique paths and
   363,804 bytes (`0.200002`). Development is the disjoint remaining 142 paths
   and 1,455,195 bytes (`0.799998`) and covers every shared contract, class,
   authority tier, construct and size decile. Regenerate manifest reachability,
   the manifest-bound partition/cohort, artifact inventory, reconciliation and
   seal commitment against the profile and graph identities. Holdout membership,
   membership digest, closed 16-slot case-envelope digest and `opened: false`
   remain unchanged; no prompt, answer, scorer key or model output exists.
6. `build-baseline` atomically reproduces the six records, artifact inventory
   and reconciliation: eight outputs byte for byte. `verify-corpus`,
   `verify-profiles`, `verify-loader`, `verify-partition` and `verify-seal` each
   emit one bounded correlated JSON result and repeat byte-identically. Profile
   validation independently checks the frozen source spans, per-skill counts,
   branch grammar, document/worker/input unions and route expansion without
   calling the graph builder's selection or scope helpers. Draft 2020-12 schemas
   and runtime validators remain equivalent. The amended study/runbook receipt,
   focused and root suites, parent-attributable selected checks, Elenchus,
   Phylax, Ephoros, Hypomnema, Protasis, Imprimatur, Horos, synopsis and diff
   gates pass. No live instruction, loader, router, marketplace or production
   path changes.

Complete replacement Files: Retain every current Step 1 file and add
`research/instruction-architecture/schemas/invocation-profile-v1.schema.json`
and
`tests/fixtures/instruction-architecture/invocation-profiles.json`; include the
new record in the source-bound artifact inventory and reconciliation. No other
path is authorized.

Complete replacement Tests: Extend `CorpusManifestTests`,
`BytePartitionTests`, `LoaderGraphTests`, `HoldoutSealTests` and a new
`InvocationProfileTests` surface to bind all six records, the 190-path physical
inventory, byte/partition/holdout totals, 31 selected skills, the exact
per-skill profile counts above, `N=519`, Fiat's `360/26/16/2/11` split, route
totals `1,038/1,038/519`, 2,595 scenario roots, 19 physical host roots and 12
reference-only records. Bind all 14 fixed non-Markdown inputs, including both
local `VERSION` paths, bytes, digests, owners and direct Read spans. The
independent oracle must read and digest every
ledger source span and reconstruct the expected profile ids, exact required
document/worker/input sets and credential expansion without importing or
calling production profile, graph, scope or minimization helpers.

Add hostile mutants that each must refuse:

1. Split one sequential bundle or worker set: Alexandria's three documents,
   an Ariadne pair, Protasis's five disciplines, Fizz's common/report or
   eight-worker branch, Solidity-auditor's local `VERSION`, 12 workers and
   shared rules, X-Ray's local `VERSION` and references, Hermes's three inputs,
   Probitas's gates/venues, or one Fiat
   worker/discipline/mask bundle.
2. Merge exclusive modes, omit one independent optional/fallback combination,
   omit an inline or delegated worker alternative, select a mature Kronos
   target, union two Kronos targets, or collapse Synkrisis `diagnose` and
   `verify` because they read equal bytes.
3. Put the vendored overlay in one singleton witness rather than every
   applicable profile; omit or demote a mandatory fixed input to reference-only; execute
   a target-only structured input on Kronos selection; or give any of the six
   Imprimatur/Pandects human references production reachability.
4. Delete or add a profile and make the same deletion or addition in graph
   roots and every edge scope; alter, overlap or stale one source span; change a
   required target while preserving counts; remove one credential variant; add
   a standalone credential variant; or let route order choose one otherwise
   equivalent profile. The independent oracle must still reject the synchronized
   fiction.
5. Union Warden's waived and Pashov branches; omit one of Scribe's Brevitas,
   task-issue or last-step combinations; model an unbounded Fiat/Kronos loop;
   enumerate an arbitrary named Kronos subset; or claim an exact prompt union
   for a task-supplied Fiat `version-relations` set. Admit Fizz's unread
   `VERSION`, `.python-version`, `pyproject.toml`, the generated Horos boundary
   or a remote version response as fixed prompt input. Retain every prior
   strict-JSON, schema/runtime-path, Git/source, subprocess, resource, output
   alias, atomic-write, race, seal and fresh-`tmp/` hostile guard.

Run these exact commands from the repository root under the pinned runtime:

```text
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py build-baseline
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-corpus --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-profiles --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --profiles tests/fixtures/instruction-architecture/invocation-profiles.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --profiles tests/fixtures/instruction-architecture/invocation-profiles.json --graph tests/fixtures/instruction-architecture/loader-graph.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-partition --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py verify-seal --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
uv run --no-project --python 3.14.6 python -m unittest tests.test_instruction_architecture.CorpusManifestTests tests.test_instruction_architecture.BytePartitionTests tests.test_instruction_architecture.InvocationProfileTests tests.test_instruction_architecture.LoaderGraphTests tests.test_instruction_architecture.HoldoutSealTests -v
uv run --no-project --python 3.14.6 python tests/run_tests.py --elenchus-report .elenchus/fiat-1046-step-1.json
uv run --no-project --python 3.14.6 python scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d
cmp -s .hexaemeron/runbook.md docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/instruction-architecture/study.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/instruction-architecture/runbook.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/instruction-architecture/study.md docs/instruction-architecture/runbook.md docs/instruction-architecture/corpus-reconciliation.md
uv run --no-project --python 3.14.6 python plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
uv run --no-project --python 3.14.6 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Run the five verifiers twice and require byte-identical stdout. Rebuild once
into a fresh `tmp/` destination with `--output` and `--reconciliation`; validate
the schemas and all six records and require all eight outputs to equal the
committed bytes. Require Elenchus schema `elenchus.unittest.v1`; an
infrastructure-failed fixture overlay remains inconclusive.

**Why.** Follow-on audit 2 found that production creates singleton
shortest-path witnesses for conditional edges and validation reconstructs the
same fiction from already-declared roots and scopes. Mandatory bundles,
independent branch products, worker alternatives and the credential product are
therefore absent while all current checks pass. Six descriptive/reference links
are also treated as executed loads. The prior `N=198`, 656-root and derived
prompt/seal identities are not source-complete.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: The complete replacement Exit in
the immediately preceding amendment block (amendment SHA-256
`d0724990657c51c4c49caa4a5f01c4ac77cd99550d624e461fd6ffc2a01f8750`) is
incorporated here verbatim by reference and remains unchanged, including its
exact command block beginning with `uv run --no-project --python 3.14.6 python research/instruction-architecture/benchmark.py build-baseline`. Complete
replacement Files: The complete replacement Files in that immediately preceding
amendment block is incorporated here verbatim by reference and remains
unchanged. Complete replacement Tests: The complete replacement Tests in that
immediately preceding amendment block is incorporated here verbatim by reference
and remains unchanged.

**Why.** The preceding amendment repaired the Step 1 definition but incorrectly
marked its exit broken. A holding verdict states whether the definition still
holds; it does not claim that implementation has already satisfied the Exit.
The broken verdict therefore blocked implementation from resuming against the
repaired definition.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.
