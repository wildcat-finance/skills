# study: framework-74 instruction architecture research

assuming, unless later evidence refuses the assumption:

| id | assumption | evidence and consequence |
| --- | --- | --- |
| A1 | the research source is `main` at `a2b634d8e039af988bf30c8316defccf70071d8d` | the run was initialised and pushed from that exact clean commit; every census, manifest, adapter and source span must bind it until a receipted base sync says otherwise |
| A2 | issue [#1046](https://github.com/wildcat-finance/skills/issues/1046) is the task authority | it permits research artifacts and an ADR, but forbids production integration, live-corpus conversion, Noema-stack integration, plugin registration, loader or router changes, and follow-up issue filing |
| A3 | Markdown remains authoritative for every experiment | WAI1 and Noema are derived controls; a representation, classifier, retrieval result or model answer is data and cannot create authority |
| A4 | the five required benchmark arms are raw Markdown, merged WAI1, parked Noema, a simple deterministic control, and any distinct candidate earned on the development cohort | a no-change result is valid; the evaluator may not make either existing IR its semantic host |
| A5 | the previous four measurement models stay in the panel and three unlike hosted families are added | the fixed panel is `anthropic/claude-opus-5`, `google/gemini-3.7-flash`, `qwen/qwen3.8-27b`, `openai/gpt-5.6-sol`, `deepseek/deepseek-v4-pro-0813`, `moonshotai/kimi-k3`, and `z-ai/glm-5.3`; model and provider availability remain a later checked predicate |
| A6 | OpenRouter calls are authorised up to a gross hard ceiling of `$100.00` for this run | the user explicitly authorised more OpenRouter credit, model families and repetitions; no call may start without a credential, route, ZDR, price, reservation and remaining-credit check, and no amendment may raise the ceiling after holdout preregistration |
| A7 | Python 3.14.6 and the standard library are the implementation floor | `.python-version` is `3.14.6` and `pyproject.toml` requires `==3.14.*`; the workbench may use repository-pinned development tools but must not add a runtime dependency merely to make a research number look better |
| A8 | the 106-file, 1,545,537-byte issue census is the starting physical denominator, not the final answer | at the source ref it consists of 32 canonical skill contracts, 18 `AGENTS.md`, 18 Promise Machine contracts and 38 Markdown references; exact whole-file deduplication reduces it to 89 unique files and 1,074,093 bytes, while reachable and prompt denominators remain unmeasured until the loader graph is verified |
| A9 | the holdout is selected and committed before candidate tuning, then opened once | it must include at least five logical skills and 20% of unique canonical bytes with the issue's required semantic classes; a failure ends the candidate version rather than becoming training data |
| A10 | WAI1 remains at the merged source and Noema remains at its parked research head | adapters may present either control to the neutral workbench, but may not edit either control's grammar, canonical model, source paths or pass criteria |
| A11 | audit synopses are usable only after whole-set verification | the base check and the Noema review-head check both exited zero on 2026-08-31; the study names exactly which views it read and retains their qualifications |
| A12 | the selected design in `.hexaemeron/design-evidence.json` chooses the research evaluator, not the eventual instruction architecture | the final ADR alone may select raw, WAI1, Noema, the simple control, a distinct candidate, or none after the sealed evidence is complete |

## 1. problem statement

The repository has several quantities that have been called instruction size,
but they answer different questions. Physical repository bytes include
generated duplicates. Unique bytes remove exact copies but say nothing about
what a request loads. A loader path says what is reachable but not what is sent
to one model call. WAI1 measures three reviewed envelopes. Noema maps 2.99% of
four complete skill files and keeps the rest as unsupported remainders. None of
those figures ranks the architectures.

The user needs an implementation-ready decision for contributors and
unattended agents. The research must find the smallest design that preserves
operative semantics, exact literals and authority while meeting the issue's
0.80 cold-prompt and 0.70 warm-prompt ratio gates for complete prompts.
“Smallest” includes executable code, schema, dependencies,
source-edit amplification and recovery work, not just model tokens.

The working prototype is a candidate-neutral workbench under
`research/instruction-architecture/`. It freezes one source manifest, verifies
the real load graph, partitions every source byte, seals development and
holdout cohorts, presents all five arms through representation-neutral case
and result schemas, measures deterministic and provider evidence, and replays
the retained result without a network. One command must reproduce every
deterministic aggregate and refuse a stale or incomplete input. The final demo
is complete only when the holdout report, dominance-frontier report, ADR, implementation
contract or negative result, and ready-to-file decomposition all verify from
content-addressed artifacts.

The expected candidate worth testing is a source-span section graph: canonical
Markdown remains authority; exact sections and literals remain recoverable;
duplicate and unreachable material is omitted by a deterministic loader graph;
and consequence-2 or consequence-3 actions stay behind existing deterministic
authority checks. This is a hypothesis, not the study's conclusion.

## 2. prior art

### merged WAI1

`wildcat-agent-instruction/v1` is in `scripts/agent_instruction.py`,
`schemas/agent-instruction-v1.schema.json`,
`docs/agent-instruction-language-v1.md`, and
`tests/fixtures/agent-instruction-v1/`. Human Markdown is authoritative;
canonical JSON is the reviewed semantic subset; WAI1 is a strict derived
codec. It preserves exact literals, source spans, closed refusal families and
hostile mutations. Its current three-envelope result is 11,170 source bytes
and 2,528 tokens versus 7,001 compact-plus-bootstrap bytes and 2,452 tokens:
37.3% fewer bytes but only 3.0% fewer measured tokens.

The last two merged pull requests that touched this target were read in full.
[PR #991](https://github.com/wildcat-finance/skills/pull/991) registered the
bounded prototype on its run branch and carried the limits that it did not
establish arbitrary-English losslessness, deployed-agent transfer,
repository-wide migration or Shoggoth readiness. [PR
#996](https://github.com/wildcat-finance/skills/pull/996) integrated WAI1 into
`main`; it carried repository-wide conversion, Shoggoth migration and wider
model evidence into later decisions, left audit PR #990 separate, and stated
that no work remained inside #909's bounded prototype. This run accepts wider
corpus and model evidence as its own task, keeps conversion and migration out
of scope, and does not reopen #909.

Issue [#1030](https://github.com/wildcat-finance/skills/issues/1030) records a
seven-pass WAI1 rebind after a Fiat version bump. Issue #1046 marks that item a
duplicate rather than authorising a second fix. The benchmark therefore
measures source-edit amplification and recovery, but it neither closes nor
implements #1030.

The base whole-set synopsis check passed. The study read
`audit/rounds/fiat-909-compact-lossless-agent-instruction-language.synopsis.md`,
whose authoritative source is its sibling `.md` and whose header binds source
SHA-256 `cc47585873d2992e78810265fb32e541c4c860dc7f59d7cb0cb23cfc6c859aa6`.
It retained all 17 rounds' `Covered`, `Not checked`, Elenchus verdicts,
finding statuses and leads. The relevant history is not merely the clean final
round: audits fixed a missing Promise claim, integer and literal bounds,
duplicate source paths, incomplete mutation oracles, omitted Fiat semantics,
answer leakage, profile-selected command execution, unvalidated evidence
bodies, hostile Unicode and redaction failures. Its remaining boundary is
still narrow: three source fragments, local-family evidence and no proof of
arbitrary-English completeness or general deployment transfer.

### parked Noema

Noema v1 at product head
`07ee0475d1559a2b09488f925645a83f786d1f3c` provides a closed typed graph,
canonical `.noe`, modules, exact inert literals, three-valued facts,
conservative operation/state slices and a non-executing policy runtime. Its
four complete source files contain 106,269 bytes, but only 3,173 bytes in 40
reviewed spans are mapped; 103,096 bytes remain explicit unsupported
remainders. The low canonical and slice ratios are therefore not whole-corpus
semantic compression ratios.

No Noema pull request is merged. The current product and audit surfaces are
[PR #1033](https://github.com/wildcat-finance/skills/pull/1033) and [PR
#1032](https://github.com/wildcat-finance/skills/pull/1032). Their bodies were
read because #1046 directly consumes their parked result. They state that the
controller is at its first `merge-step`, no step or run was integrated, no
plugin was registered, and #942 remains open. This run treats those branches
as immutable evidence and does not merge, rebase, close or resume them.

The whole-set synopsis check at review head
`7344de8874f9de8a2a2ef78a31f7e760f56e491e` passed. The study read
`audit/rounds/fiat-942-prototype-noema-as-a-model-native-sliced-ins.synopsis.md`,
which binds authoritative source SHA-256
`a444a6913d81eb6f98502323d9500759be1fd30823d9343c295c74b9d62c1884`.
All 44 rounds' dispositions remain in force. The audit fixed source and
manifest forgery, slice omission, policy permission errors, bound resets,
literal disclosure, path races, paid-accounting and retry defects, experiment
instability, evidence retention, stale prose, shallow-checkout verification
and product/audit baseline drift. Its clean result still does not establish
current-main source compatibility, full semantic coverage, small-local-model
viability or integration authority. The accepted model cohorts were 16/16 for
Google and OpenAI, while the four-family measurement panel was Anthropic,
Google, Qwen/open-weight and OpenAI.

### repository and external controls

The raw control is the exact current Markdown reached through the documented
root router, plugin contract, selected skill and conditionally linked
references. The deliberately simple control is an exact file-level manifest
with content-addressed deduplication and explicit loader roots; it introduces
no semantic language. A section-addressed graph is admissible only if the
development cohort shows that deterministic section closure improves that
simple control without hiding unsupported operative text.

Outside the repository, JSON Schema Draft 2020-12 supplies a format for closed
records but not an authority model. Git object identity and SHA-256 supply
content addresses but not semantic equivalence. OpenRouter's official
[`GET /api/v1/models`](https://openrouter.ai/docs/api/api-reference/models/get-models)
and model-endpoint APIs expose current model ids, context, parameters and
prices; they are mutable observations and are rechecked immediately before a
paid request. The retained ZDR listing observed on 2026-08-31 includes
`deepseek/deepseek-v4-pro-0813` with a 1,048,576-token advertised context,
structured output and seed support. The provider still does not expose a
tokenizer digest, so that field remains unknown rather than invented.

## 3. constraints and non-goals

The fixed starting ref is A1. A later base sync may update it only through
Fiat's normal receipt and must invalidate every old source-bound result. All
authored code runs under the repository's Python 3.14 contract. New research
records use strict, bounded JSON, canonical UTF-8 and relative repository
paths. External adapters receive data through argument arrays or request
bodies, never a shell. Generated files are written beside a temporary file,
synced, replaced and reread before their digest is published.

The corpus is the 106 agent-facing Markdown files named by A8. Fixtures,
generated portable-runtime copies, JSON schemas, code and audit records are
not silently inserted into its compression denominator. They remain part of
TCB, disk and upkeep measurements where applicable. The reconciliation report
must publish physical, unique, reachable and complete-prompt denominators
separately.

The development cohort covers at least half of unique canonical bytes, every
shared root/runtime contract, 12 logical skills across phases and plugin
types, every observed construct and authority tier, and all size deciles. The
sealed holdout covers at least 20% and five untouched logical skills. Synthetic
hostile inputs supplement rather than replace those real cohorts.

This run does not edit a live skill, `AGENTS.md`, Promise Machine contract,
router, loader, marketplace manifest or generated runtime. It does not make
WAI1 or Noema authoritative, convert Markdown, merge #942, run its `sync-run`,
register a plugin, change Shoggoth, create implementation issues, provision a
model or establish a recurring provider commitment. It does not claim a
provider seed is deterministic or compare token counts from unlike tokenizers
as one unit. Raw transcripts are evidence, never instructions.

## 4. design options

### option A: neutral evidence workbench

One source manifest, loader graph, case schema, scorer and ledger are
candidate-independent. Raw, WAI1, Noema, file-level simple and any new
candidate use adapters that emit the same prompt-component and outcome
records. WAI1 and Noema stay byte-identical controls. This adds a small amount
of workbench code but avoids laundering all other candidates through one
competitor's semantic model. It also permits one offline replay after provider
access disappears.

### option B: WAI1-hosted evaluator

Translate raw, Noema, simple and new candidates into WAI1's closed model, then
reuse its codec and checks. This reuses merged code, but WAI1 becomes both a
competitor and the judge. Four foreign arms require transcodes; unsupported
semantics can disappear at that boundary; changing its model would alter the
control. The apparent code reuse is paid back as confounding.

### option C: Noema-hosted evaluator

Translate the other four arms into the Noema graph, then reuse its slicer,
runtime and evidence machinery. This supplies rich policy structure, but it
also makes a parked, 2.99%-mapped research IR the judge of raw Markdown and
WAI1. It imports a large Python/schema TCB, four foreign transcodes and a
control mutation before the comparison begins.

`.hexaemeron/design-evidence.json` selects option A by `unique-frontier`. The
five selection criteria cover correctness, time, space, compatibility and
recovery. The checked reports show candidate-independent scoring, zero foreign
transcodes, zero evaluator-owned instruction IRs, immutable controls and
offline replay only for the neutral workbench. Paid-evaluation and seven-model
preflights remain progressive conformance gates at Step 4. This lock chooses
the experiment's referee, not the architecture the final ADR will rank.

## 5. risk register seed

```risk-register
source-omission | the boundary between the frozen Markdown corpus and its manifest | every physical byte is classified once and missing or extra paths refuse
loader-fiction | the boundary between filenames and actual host loading | roots and conditional links are proved from repository contracts rather than inferred from names
duplicate-denominator | physical, unique, reachable and prompt accounting | mutually exclusive component rows reconcile without silently counting generated copies as savings
semantic-drift | source spans and every derived representation | stale digests, moved spans, unsupported operative text and ambiguous mappings refuse before comparison
authority-confusion | candidate text, model output and consequence-2 or consequence-3 actions | data cannot create authority and deterministic gates retain the controlling source identity
control-mutation | adapters around merged WAI1 and parked Noema | control bytes and results bind their pinned heads and no adapter changes their grammar or acceptance rule
evaluation-contamination | development, holdout and answer records | holdout selection is sealed before tuning, opened once, scorer expectations never enter prompts and retries keep identity
provider-boundary | OpenRouter request, route, response and mutable catalog | credential is secret, route and ZDR status are checked, hostile or malformed output is bounded data and unavailable means unknown
spend-overrun | reservations, settled costs, fees and account credit | gross exposure is durably reserved before a call and cannot exceed $100 even after retry uncertainty
partial-write | manifests, packets, transcripts, ledgers and reports | interruption leaves either the old verified file or a non-verifying temporary file, never a half-valid result
parser-exhaustion | Markdown, JSON, archives and hostile model output | byte, depth, count, expansion and output caps apply before unbounded allocation or recursion
path-race | source reads and artifact publication | no-follow descriptor reads and identity rechecks detect symlink, replacement and concurrent-edit drift
scorer-bias | representation-neutral tasks and deterministic grading | primary outcomes are plans, decisions, refusals, recoveries or tool invocations; candidate labels are never the oracle
statistical-overclaim | paired behavioral estimates and selection gates | the preregistered interval, trial count and failure taxonomy are fixed before holdout and underpowered remains inconclusive
edit-amplification | a one-byte or version-length source change | touched artifacts, rebind time and failure messages are measured for every arm without repairing issue 1030
replay-gap | retained network evidence and offline verification | every accepted aggregate binds prompts, raw responses, route metadata, costs and scorer output for one-command replay
```

The audit loop enumerates every id. A round that cannot examine one says why;
silence is not a disposition.

## 6. glossary seeds

**physical corpus**: every in-scope repository path and byte before
deduplication.

**unique canonical corpus**: one canonical file per declared exact duplicate
group; it does not remove similar prose.

**loader graph**: verified roots and conditional edges that describe which
canonical documents a host may load for one scenario.

**scenario-reachable bytes**: the union of canonical source bytes reachable
for one declared scenario before prompt shaping.

**complete prompt**: every wrapper, kernel, source, IR, slice, literal,
dictionary, receipt and task byte actually sent in one model request, each
counted once.

**simple control**: exact file-level content addressing, deduplication and
loader-root selection without a new instruction language or section semantics.

**section graph**: exact Markdown byte spans with stable section ids,
dependencies, authority tier and scenario roots; source bytes remain the
payload and authority.

**operative span**: source bytes that constrain an agent's decision, order,
scope, refusal, recovery, evidence or authorship.

**unsupported operative span**: operative bytes not represented or preserved
by an arm; it is a failure, never a compression saving.

**development cohort**: the source-bound cases available for construction
and candidate selection.

**sealed holdout**: preregistered, committed, untouched logical skills and
cases opened once after thresholds and a candidate version are frozen.

**reservation**: conservative gross cost assigned before a provider attempt;
uncertain attempts remain reserved.

**candidate version**: one content-addressed adapter, manifest, prompt
template, scorer and gate set; any post-holdout change creates a failed old
version and a separate future experiment.

## 7. sources

Repository authority and task inputs:

- `AGENTS.md`, `SHOGGOTH.md`, `PROMISE_MACHINE.md`, and
  `.agents/skills/promise-machine/SKILL.md` at A1;
- issue #1046, issue #1030, merged PRs #991 and #996, and open Noema PRs #1032
  and #1033;
- `docs/agent-instruction-language-v1.md`,
  `docs/decisions/ADR-062-encode-a-closed-agent-instruction-model.md`,
  `scripts/agent_instruction.py`, its schema and fixture tree;
- Noema product head `07ee0475d1559a2b09488f925645a83f786d1f3c`, review head
  `7344de8874f9de8a2a2ef78a31f7e760f56e491e`,
  `docs/noema-v1.md`, `docs/decisions/ADR-066-evaluate-noema-as-a-sliced-instruction-ir.md`,
  `scripts/noema.py`, its schema and fixture tree;
- the two verified audit synopses and their authoritative sibling records named
  in item 2;
- `.hexaemeron/design-evidence.json`, `.hexaemeron/design-facts.json`, its 15
  closed design reports, and
  `.hexaemeron/evidence/openrouter-model-snapshot.json`.

Discipline contracts, cited rather than copied:

- [Ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) for signals;
- [Phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) for external and
  off-chain boundaries;
- [Metron](../../plugins/hexaemeron/skills/metron/SKILL.md) for measurement and
  budgets;
- [Elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md) for failure
  localisation and guards;
- [Hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) for durable
  decisions.

External sources are the official OpenRouter model and endpoint API references
linked in item 2. Their mutable values are evidence snapshots, not stable
documentation claims.

## 8. signals, and the questions behind them

The questions are: “which exact source, candidate, prompt, model route and
attempt produced this result?”, “did the run stop because semantics failed,
the holdout failed, a provider was unavailable, or spend authority ran out?”,
and “can another agent replay the accepted decision without the provider?”

Step 1 emits corpus, duplicate-group, loader-root, cohort and seal identities.
Steps 2 and 3 emit per-arm parse, projection, fidelity, prompt-component,
mutation, resource and edit-amplification rows. Step 4 emits reservations,
attempt identities, route/model revisions, timings, token usage, costs,
scorer outcomes, interval state and terminal cause. Step 5 emits the final
frontier, chosen trade, failed gates and replay identities. Every event shares
the run, source, candidate version, case and correlation ids defined by
[Ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md); no secret or raw
credential enters them.

## 9. boundaries, per capability

Filesystem reading is worth taking because the corpus and source spans must be
exact; descriptor-relative no-follow reads, byte caps and final identity checks
close replacement and symlink races. Git and GitHub reads are worth taking for
pinned controls and topology; immutable commit ids and checked signatures
close branch-name drift. Research writes are worth taking only below the named
research, fixture, document and audit paths; atomic publication and closed
inventories close partial or ambient artifacts.

Subprocesses are worth taking for repository-pinned checkers and Git; fixed
argument arrays, pinned executables, empty or bounded inherited environment and
no shell close injection. Network access is worth taking only for official
model/catalog reads and preregistered model calls; host allowlists, TLS,
bounded responses, ZDR routing, redaction and durable attempt records close the
boundary. The OpenRouter credential is loaded from the existing secret file
into process memory and never appears in argv, output, Git or a report.

Model output is worth taking as behavioral evidence only. A closed response
schema, byte limits, strict parsing, deterministic scoring and existing
authority checks keep it from becoming executable instruction. Provider
availability, hidden tokenizer revision and stochastic drift remain named
unknowns. These controls apply [Phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md)
without broadening its contract.

## 10. the budget, or its absence

The source manifest must contain exactly 106 in-scope physical files at the
frozen ref unless its reconciliation report explains a verified topology
change. Every byte is classified exactly once. Development coverage is at
least 50% of unique canonical bytes and the sealed holdout at least 20%. The
selected candidate's deterministic authority, ordering, scope, recovery and
literal vectors allow zero failures. Complete median cold prompt ratio is at
most 0.80 and warm ratio at most 0.70 on the holdout.

The workbench measures parse, validate, select and prompt assembly p50/p95,
peak RSS, disk bytes, executable LOC, dependencies, touched artifacts and
rebind time. It records model TTFT, end-to-end time, input/output tokens and
cost without setting an unearned latency target. The behavioral gate is the
issue's preregistered paired 95% interval: it must exclude aggregate
degradation greater than 0.02, and every critical policy regression fails
regardless of the aggregate.

Gross OpenRouter exposure is capped at `$100.00`, including uncertain retries
and route fees. The exact commands are fixed in the runbook; before Step 4 the
progressive record requires:

```text
uv run --no-project --python 3.14.6 python3 research/instruction-architecture/benchmark.py preflight-spend --candidate neutral-evidence-workbench --authority .hexaemeron/model-evaluation-authority.json --max-gross-usd 100 --report .hexaemeron/design-reports/neutral-evidence-workbench-paid-evaluation-preflight.json
uv run --no-project --python 3.14.6 python3 research/instruction-architecture/benchmark.py preflight-model-matrix --candidate neutral-evidence-workbench --models anthropic/claude-opus-5,google/gemini-3.7-flash,qwen/qwen3.8-27b,openai/gpt-5.6-sol,deepseek/deepseek-v4-pro-0813,moonshotai/kimi-k3,z-ai/glm-5.3 --require-zdr --report .hexaemeron/design-reports/neutral-evidence-workbench-seven-model-preflight.json
```

No provider call runs before both reports pass. [Metron](../../plugins/hexaemeron/skills/metron/SKILL.md)
governs baselines and comparisons; a missing measurement stays unknown.

## 11. the fail-closed posture

The run stops on a stale source or control digest, incomplete or overlapping
byte partition, invented loader edge, missing dependency closure, unsupported
operative span, non-canonical or malformed record, holdout access before the
open transition, scorer expectation in a prompt, parser differential, resource
limit, concurrent source change, uncorrelated receipt, credential disclosure,
unreserved call, insufficient credit, `$100` exposure, missing ZDR route,
provider/model mismatch, critical policy regression, failed interval, prompt
ratio failure, irreproducible deterministic output or dirty offline replay.

Safe fallback is the exact canonical Markdown only when its digest and loader
path still verify; fallback is recorded as a candidate failure, not counted as
that candidate's success. A provider outage is `unknown`. A crashed call keeps
its reservation until a later bounded reconciliation proves settlement.

A defect follows [Elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md):
preserve the failing bytes and attempt identity, reproduce on the exact parent,
localise the mechanism, add the smallest parent-red guard, repair the cause,
then prove fixed-green without rewriting the sealed cohort. Any repair after
holdout opening invalidates that candidate version for this issue.

## 12. decisions and their homes

The neutral-evaluator decision is expensive to reverse during the run and is
held by `.hexaemeron/design-evidence.json`; the receipted study and runbook
carry its rationale. The source/corpus/loader and holdout decisions live under
`research/instruction-architecture/` as closed, content-addressed manifests.
Prompt, scorer, model, provider, privacy, retry and budget decisions live in
the benchmark preregistration and model-runtime manifest beside the retained
evidence.

The final architecture, every WAI1 and Noema mechanism's
`adopt`/`adapt`/`reject` disposition, Pareto frontier, failure taxonomy and
chosen trade live in a new numbered ADR. If and only if the selected candidate
passes, its semantic domain, canonical form, source mapping, review projection,
slice algorithm, literal and authority rules, deterministic APIs, versioning,
migration, rollback, observability, bounds and compatibility gates live in
`docs/instruction-architecture/implementation-contract.md`. A negative result
uses the same path to state why no implementation contract exists.

The corpus reconciliation, benchmark method and replay commands live in
`docs/instruction-architecture/research-report.md`; machine evidence stays
under `tests/fixtures/instruction-architecture/`. The ready-to-file but unfiled
repository decomposition lives in
`docs/instruction-architecture/follow-up-decomposition.md`. No issue is filed
and no production file is changed. These homes follow
[Hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) and keep evidence,
decision, specification and future work distinct.
