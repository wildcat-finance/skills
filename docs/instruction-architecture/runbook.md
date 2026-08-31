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
