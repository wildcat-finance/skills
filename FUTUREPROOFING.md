# Futureproofing the Shoggoth

This is the honest roadmap for Wildcat Labs Skills, the Shoggoth collective.
It describes what exists in the repository, what evidence is still missing,
and what each member could become if contributors close that gap.

It is not a product forecast. “Could become” means that the current contract
has a credible direction, not that the work is scheduled, funded, or already
partly delivered. The source of truth for the next accepted change remains
each skill's `EVOLUTION.md` ledger.

Snapshot: 31 August 2026, at repository revision
`ec426cd00508a8cb118d879f3f65d99098c4d787`.

## What we are trying to build

A fully formed Shoggoth would help a crypto team move from an uncertain
question to a result another person can inspect:

1. bound the material worth reading;
2. preserve the exact sources, chain state, and assumptions;
3. state the property or question precisely;
4. build, test, measure, or compare within that boundary;
5. record what the result proves and what it does not;
6. release the work with enough evidence for someone else to reproduce it;
7. learn from failures and repeated runs without letting an agent invent a
   stronger story than the record supports.

That is broader than contract auditing and broader than credit. It includes
protocol research, historical reconstruction, executable specifications,
off-chain hardening, grounded assistants, performance work, observability,
documentation, and repository delivery. Credit is one important proving ground
because it forces the system to deal with incomplete and adversarial evidence.

The final form should still be a collection of bounded specialists. Turning it
into one opaque “do everything” agent would remove the property that makes the
work inspectable.

## How to read each entry

Every entry has three labels:

- **Today** is backed by the current skill contract, tests, and evolution
  record.
- **Missing** is the nearest material limitation, not every possible feature.
- **With enough contribution** is a plausible end state. It remains
  conditional until code, specimens, and checks establish it.

No numeric maturity scores appear here. A narrow skill can be complete without
being broad, and a large implementation can remain unproved in actual use.

## Shared law and controlled delivery

### Promise Machine

**Today.** The Promise Machine gives every first-party skill one law for
evidence, consequence, composition, refusal, and recovery. Repository checks
validate declarations, installation copies, run-observation records,
contributor ranking, router selection, and the first-party licence boundary.

**Missing.** Structural conformance is not domain truth. A passing promise
check cannot establish that a protocol design is correct, that a data source is
canonical, or that an agent answer is useful unless another named operation
supplies that evidence.

**With enough contribution.** It could become a common interchange layer for
crypto R&D tools: every result would carry a machine-checkable statement of
what was observed, which bytes and chain positions support it, which later
actions it permits, and which uncertainty survives the hand-off. That needs
real integrations and hostile composition tests, not a larger vocabulary.

### Fiat

**Today.** Fiat controls an explicit, hash-chained repository delivery through
study, runbook, implementation, audit, prose, push, and integration. It owns a
dedicated worktree, durable state, per-step receipts, stacked pull requests,
signed integration checks, verified local checkpoint archives, recovery, and
retirement.

**Missing.** A reused collaboration handle can expose an earlier issue. Its
checkpoint store is deliberately local; it is not safe cross-machine hand-off
or distributed orchestration.

**With enough contribution.** Fiat could become a dependable delivery kernel
for long-running agent work: resumable across controlled hosts, capable of
proving exactly which worker and tool produced each transition, and able to
surface recurring failures to the research layer without relaxing human
publication authority. A distributed version would need authenticated state
transfer, replay protection, and recovery tests before it could claim that.

### Kronos

**Today.** Kronos ranks eligible held frontier jobs, records one durable goal,
can park work, and dispatches the highest unparked job through Fiat only when a
user explicitly asks it to run the field.

**Missing.** Its arithmetic is reproducible, but the input scores are still
human judgements. Ranking does not make those judgements objectively correct.

**With enough contribution.** Kronos could become a research-portfolio loop
that uses real failure rates, maintenance cost, field coverage, and downstream
reuse as evidence for prioritisation. The human would still set the policy and
retain the stop control.

## Sources, history, and releases

### Horos

**Today.** Horos emits and verifies repository reading boundaries, byte
censuses, drift reports, and skeleton maps for Python, TypeScript, Go, C++, and
Solidity. A boundary is fail-open and never applies during a security review.

**Missing.** The content-addressed-object rule has classified a large real
surface but still owes its frontier run. Markdown has no outline extractor.

**With enough contribution.** Horos could give an agent a cheap, proved map of
large mixed repositories: generated and vendored sinks excluded with reasons,
important interfaces outlined, and stale boundaries rejected before work
begins. It must continue to expose what it did not read.

### Lemma

**Today.** Lemma converts Solidity compiler standard JSON input or Markdown
trees into validated JSONL chunks with source locations and separate quotation,
model, and embedding text. It records corpus provenance and stops before
embedding, indexing, retrieval, or answering.

**Missing.** Its callable-surface ABI validation does not independently verify
return types or state mutability.

**With enough contribution.** Lemma could become a trustworthy source-preparation
layer for protocol research: compiler-aware Solidity units, documentation
structures, versioned schemas, and stable incremental rebuilds that make every
retrieved sentence traceable to exact source bytes.

### Lazarus

**Today.** Lazarus captures finite fixed-block Ethereum evidence, proves and
verifies the supported state offline, replays the exact recorded RPC requests
over loopback, and packages preservation releases. It now reconstructs a
scoped `receiptsRoot` relation for represented receipt payloads and log
projections.

**Missing.** Empty blocks have no receipt-witness representation. Transaction
hashes and unrelated RPC evidence may be recorded but are not thereby proved;
canonical-chain and provider-independence claims remain outside the fixture.

**With enough contribution.** Lazarus could become a general historical-test
preservation layer for EVM software: minimal fixture discovery, multiple
providers compared at capture time, broader proof relations, deterministic
local replay, and long-term release migration. It should remain finite rather
than pretending to replace an archive node.

### Berean

**Today.** Berean binds a document corpus by digest, proves citations against
exact bytes, ties live values to a chain and block, records evaluation, and
governs promotion and rollback of a grounded protocol-agent release.

**Missing.** The reference release uses a demonstration corpus and preserved
Goldfinch readings. No live Wildcat reference release or Ariadne binding has
been established.

**With enough contribution.** Berean could support continuously evaluated
protocol assistants whose releases fail closed when documents, deployments, or
chain readings drift. Real value would come from held questions written by
protocol users and maintainers, not from a larger demonstration set.

### Ariadne

**Today.** Ariadne captures, inspects, verifies, and performs bounded replay of
digest-bound in-toto statements. Its predicate registry covers Solidity,
datasets, historical-state fixtures, and grounded-agent releases. It can bind
an existing Berean release without rerunning the agent or using the network.

**Missing.** Ariadne does not sign a statement, authenticate its publisher, or
prove the truth of the underlying evidence. Those are separate relations.

**With enough contribution.** Ariadne could give every released model, fixture,
dataset, audit artefact, and binary a portable evidence envelope whose coverage
and gates can be checked offline. Signature verification and publisher policy
would need explicit owners rather than being smuggled into the current promise.

### Synkrisis

**Today.** All four operations ship: checked cohort construction, deterministic
bounded diagnosis, fixed-template rendering, and verification that recomputes
the entire path from the original inputs. A measured work budget also ships.

**Missing.** The current two rule kinds have been exercised on constructed
records, not a captured production cohort.

**With enough contribution.** Synkrisis could become the learning surface for
repeated crypto-agent runs: comparable cohorts, drift and failure signals,
counterfactual specimens, and links to the owner best placed to investigate.
It should never promote correlation into cause or authorise remediation.

## Protocol behaviour and Solidity

### Janus

**Today.** Janus validates a conformance manifest and runs seven bounded gates
for the Wildcat v2.5 hook seam, producing Markdown and SARIF reports about what
the hook may observe and change before and after a host action.

**Missing.** No second host adapter demonstrates that the manifest model
generalises beyond this callback design.

**With enough contribution.** Janus could compare hook and callback systems
across protocols using host-specific adapters over a common effect language,
with temporal properties and executable negative specimens. Generality must be
earned one real host at a time.

### Pandects

**Today.** Pandects maintains executable credit-law records, a rendered
catalogue, and broken specimens that prove each law catches its named failure.
Its structured search records currently cover Foundry campaigns.

**Missing.** Echidna and Medusa results remain prose in the audit record rather
than structured search records.

**With enough contribution.** Pandects could become an executable law library
for lending and adjacent accounting systems, with adapters from laws to
Foundry, Echidna, Medusa, Janus manifests, and formal tools. Each law must stay
small enough to falsify and must never stand in for a whole-protocol audit.

### Hermes

**Today.** Hermes optimises one named Solidity gas class at a time. It records a
baseline, applies one candidate, remeasures, reruns behaviour tests, checks
storage layout and selectors, and demands targeted arithmetic evidence before
keeping a change.

**Missing.** Its 12 classes cover 62 of the 120 rules in the pinned corpus; 58
cannot yet be selected as candidates.

**With enough contribution.** Hermes could turn a broad, versioned optimisation
corpus into reproducible compiler- and chain-aware experiments, including
interaction effects and long-term regressions. More rules only matter when
their preconditions and safety checks are executable.

### Homologia

**Today.** Homologia is a packaged and selectable scaffold. Its substantive
verbs refuse cleanly. There is no manifest validator, contract runner,
off-chain mirror runner, integer comparison, or parity verdict.

**Missing.** The operational skill itself.

**With enough contribution.** Homologia could compare one pinned on-chain
calculation with one pinned TypeScript or Python mirror over declared vectors,
integer for integer, preserving every divergence as a specimen. Pandects could
supply economic laws and Lazarus proved chain-side answers, but agreement would
still not prove that either implementation models the right rule.

### Upstream Pashov suite

**Today.** X-Ray maps a Solidity repository before audit; Solidity Auditor
reviews contracts; Fizz creates stateful Echidna/Medusa harnesses; Fizz Convert
turns recorded properties into assertions; Fizz Sync reconciles a harness with
source changes. These five skills ship unchanged under their upstream MIT
licence.

**Missing.** Wildcat does not own their roadmaps and must not describe an
upstream possibility as a first-party commitment.

**With enough contribution.** The collective can improve the checked hand-offs
around those tools: feed precise scope into them, preserve their raw outputs,
turn failures into Elenchus specimens, and bind released audit artefacts with
Ariadne. Changes to the tools themselves belong upstream.

## Lending and credit records

### Alexandria

**Today.** Alexandria preserves heterogeneous lending inputs by digest, emits
verified derived views, creates unsigned release statements, and answers
address queries without hiding source coverage. One Compound v3 Phase 0
execution witness exists.

**Missing.** There is no resumable, reconciled collector for a declared
Ethereum USDC interval.

**With enough contribution.** Alexandria could become a durable public archive
of raw lending evidence across venues and time: resumable capture, independent
source reconciliation, schema migration, and content-addressed releases. It
should continue to preserve rather than interpret.

### Tabularium

**Today.** Tabularium converts supported preserved venue records into
deterministic, venue-qualified credit-event releases with explicit mapping
provenance and coverage. One non-canonical Compound v3 witness has been rebuilt
from Alexandria.

**Missing.** Compound Phase 1, its canonical adapter, and the Ethereum USDC
specimen do not exist.

**With enough contribution.** Tabularium could maintain a broad, versioned
event model across lending protocols, with venue-native meanings kept visible,
mapping changes diffable, and every release reproducible from preserved input.
It should not erase disagreement in pursuit of a universal-looking table.

### Probitas

**Today.** Probitas collects evidence from addresses a subject declared and
builds a verified borrowing and repayment dossier with source coverage,
qualifications, and unknowns kept visible.

**Missing.** Morpho Midnight secondary-market exits on Base remain
unattributable and the relevant curation data has not been collected.

**With enough contribution.** Probitas could assemble venue-spanning,
time-bounded dossiers with explicit identity claims, dispute records, and
repeatable refreshes for human underwriting. It should never guess undisclosed
addresses, equate an address with a legal person, or make the credit decision.

## Engineering disciplines

### Protasis

**Today.** Protasis checks the mechanical content and relations of studies,
risk registers, amendments, runbooks, and optional version records. It also
checks one closed candidate-by-criterion design-evidence record progressively:
first at design lock, then when each step and the final integration make more
evidence due.

**Missing.** It proves that the matrix is complete and the declared evidence is
present when due. It does not prove that a cited report is true or that the
chosen design is correct.

**With enough contribution.** Protasis could support more project shapes,
more typed evidence producers, and stronger traceability from assumptions and
risks to tests and release gates, while leaving design judgement with people
and the relevant specialist.

### Phylax

**Today.** Phylax mechanically checks Python and source-local TypeScript
controls and guides review of external data, commands, URLs, credentials,
dependencies, paths, and model output.

**Missing.** A clean Phylax result is not a whole-system security review and
does not cover Solidity.

**With enough contribution.** It could become a multi-language off-chain
security layer with taint-aware fixtures, dependency and provenance policy,
and incident-derived rules. Every mechanical rule should arrive with a broken
specimen that proves its value.

### Ephoros

**Today.** Ephoros asks the operator's questions first, then checks bounded
patterns for logs, metrics, durations, runbook annotations, and address-key
exposure across the surfaces it supports.

**Missing.** Rules E001 to E003 do not inspect TypeScript. E004 is deliberately
limited to block-style YAML.

**With enough contribution.** Ephoros could specify and test end-to-end
observability contracts across Python, TypeScript, Solidity events, workers,
and release pipelines. The goal is an explainable failure, not more telemetry.

### Metron

**Today.** Metron accepts a declared workload, validates a recorded baseline
and candidate measurement, and keeps or rejects one change against the stated
budget.

**Missing.** The plugin checks measurement records but does not produce the
measurements it consumes.

**With enough contribution.** Metron could provide reproducible benchmark
drivers, environment fingerprints, variance handling, and long-term regression
tracking for off-chain tools. Hermes should continue to own Solidity gas.

### Elenchus

**Today.** Elenchus starts with a failure already in hand, reproduces and
localises it, fixes the cause, and requires parent-red and fixed-green evidence
from fresh unittest, Forge, or Node reports. It has a documented Lazarus
RPC-fixture hand-off.

**Missing.** Success proves the named failure and guard relation, not the
absence of nearby defects.

**With enough contribution.** It could build a reusable corpus of reduced
failure specimens across crypto tooling, with automatic historical fixtures,
cause taxonomy, and guarded replay. It should remain failure-led rather than
becoming a vague debugging persona.

### Hypomnema

**Today.** Hypomnema decides whether a durable decision belongs in an ADR,
comment, runbook, interface note, or pointer to an existing record, and checks
several of those shapes mechanically.

**Missing.** The bridge from a study to exactly one standing record is still a
judgement rather than a deterministic check.

**With enough contribution.** Hypomnema could maintain a navigable explanation
graph from code and alerts to decisions, assumptions, and operating procedures,
while rejecting duplicate or stale records.

### Imprimatur

**Today.** Imprimatur diagnoses three tiers of prose defects, including banned
AI writing habits, unsupported technical vocabulary, repeated formulae, and
source-comment wording. It does not rewrite the text.

**Missing.** Its first 64-sample evaluation failed annotation-agreement and
holdout-coverage gates. The holdout is spent and the reported scores remain
provisional.

**With enough contribution.** It could become a language and evidence lint
with independently labelled corpora for several engineering registers, stable
false-positive budgets, and transparent versioned rules. Contributors must
repair the evaluation before tuning to its numbers.

### Vulgate

**Today.** Vulgate rewrites messages, documentation, announcements, and
technical explanations into a plain human register while protecting facts,
numbers, commitments, caveats, links, and intended meaning.

**Missing.** Full semantic parity remains model judgement rather than a
repeatable evaluation.

**With enough contribution.** It could pair protected-content extraction with
held human evaluations across several registers, making tone changes easier to
check without flattening every author's voice.

### Sapheneia

**Today.** Sapheneia shapes an agent's replies for AuDHD readers and has one
bounded operation for durable audit records, issues, and comments. It preserves
protected evidence and does not change another skill's gates.

**Missing.** The ten interaction rules have no published held cross-model task
corpus.

**With enough contribution.** It could become an evaluated interaction layer
that adapts state, choices, and next actions to different cognitive needs
without patronising the reader or hiding uncertainty.

### Brevitas

**Today.** Brevitas enforces structural output budgets on engineering prose and
checks that protected tokens such as identifiers, paths, numbers, and
reproduction details survive compression.

**Missing.** It has no held cross-model engineering-review corpus. Semantic
preservation beyond protected tokens remains agent-checked.

**With enough contribution.** It could offer register-specific budgets backed
by reader-comprehension and decision-quality evidence, producing shorter work
because it is easier to use rather than because a line count looks tidy.

## Fiat's four worker roles

The workers are execution roles, not extra governed skills.

### Surveyor

**Today.** Surveyor receives one source-bound study packet and returns a study.
It cannot receipt the phase, steer Fiat, publish, or widen the task.

**With enough contribution.** Its packet could support reproducible research
logs and independent source verification while retaining the same lack of
controller authority.

### Mason

**Today.** Mason implements and tests one exact runbook step on its assigned
branch pair. It cannot push, open a pull request, merge, or alter Fiat.

**With enough contribution.** Its packet could support more execution
environments and stronger artefact capture without becoming an autonomous
delivery controller.

### Warden

**Today.** Warden runs one exact audit round, preserves raw findings, fixes
bounded defects, and reports an Elenchus verdict. It cannot receipt its own
round or call missing evidence clean.

**With enough contribution.** It could select richer security suites from the
study's named attack paths and preserve machine-readable findings for cross-run
analysis, with Fiat still controlling acceptance.

### Scribe

**Today.** Scribe performs one bounded prose pass, running Imprimatur, applying
Vulgate without changing protected content, and rerunning the lint. It cannot
invent claims, issues, or publication authority.

**With enough contribution.** It could check more document types and held
reader tasks while remaining a surface editor rather than a source of facts.

## Research programmes worth contributing to

The member frontiers become more useful when they form complete paths rather
than isolated features.

### Historical protocol laboratory

Combine Horos, Lazarus, Elenchus, Pandects, Janus, the Pashov suite, and Ariadne
so a real historical failure can be reduced, replayed offline, tested against a
named law or host boundary, and released with evidence. The current pieces are
useful; a multi-protocol public specimen set is missing.

### Checkable protocol assistants

Combine Lemma, Lazarus, Berean, Ariadne, Sapheneia, and Brevitas around held
questions from protocol users. The success measure is not answer volume. It is
whether answers remain source-correct under document and chain drift, refuse
when support is absent, and help a person decide what to do next.

### Cross-protocol behaviour

Extend Janus with real host adapters, Pandects with more executable laws, and
Homologia from scaffold to a tested parity operation. This could expose where
different protocols use the same words for different state transitions.

### Open lending evidence

Complete Alexandria capture, Tabularium adapters, and Probitas curation for
declared intervals and venues. Release preserved input, mapping provenance,
coverage, and disputes separately so a dossier can be corrected without
rewriting history.

### Evidence from repeated delivery

Capture Promise Machine observations from real Fiat runs, compare declared
cohorts with Synkrisis, and feed reproduced failures to the relevant owner.
This is how the collective can learn without allowing the comparison layer to
diagnose causes or change code on its own.

## The admission test for new work

Before adding a skill, operation, adapter, or rule, answer these questions in
ordinary language:

1. What real failure or repeated cost does this solve?
2. Why does it belong to this member rather than an existing sibling?
3. What finite operation will run?
4. What evidence will a success result carry?
5. What will it explicitly not prove?
6. Which broken specimen demonstrates that the check can fail usefully?
7. Which current user or workflow will exercise it?
8. What ongoing maintenance does it create?
9. What result would tell us to stop or remove it?

If those answers do not exist, write a study or preserve a specimen. Do not add
an agent name and hope that capability follows.

## Choosing useful work

Good first contributions are small enough to verify and large enough to change
what a user can establish. Examples from the current gaps include:

- a held production cohort for Synkrisis;
- a live Wildcat reference release for Berean;
- a second real host adapter for Janus;
- a complete first Homologia operation with a deliberately divergent specimen;
- structured Echidna or Medusa search records for Pandects;
- TypeScript parity for Ephoros rules E001 to E003;
- ABI return-type and mutability validation in Lemma;
- a canonical Compound v3 capture-to-release path across Alexandria and
  Tabularium;
- independent labels and fresh holdout tasks for the prose and interaction
  skills.

The exact accepted next job may be narrower than these examples. Check the
member's `EVOLUTION.md`, open issues, tests, and `AGENTS.md` before changing its
files.

## Review rhythm

Revisit this document when a member's shipped frontier changes, when a planned
integration is disproved, or when field evidence shows that a research
programme is not worth maintaining. A useful review asks:

- Did a real person run the operation?
- Did the output change or support a decision?
- Could another person reproduce it from the recorded evidence?
- Did the operation refuse when its evidence was missing?
- Did it create a burden larger than the problem it removed?
- Did the result reveal a better owner or a reason to stop?

The collective becomes durable by deleting weak claims, preserving failures,
and proving a few complete paths in real work. More names, more prose, and more
generated artefacts are not evidence of progress.
