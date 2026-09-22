# FUTUREPROOFING THE SHOGGOTH

This is the honest roadmap for Wildcat Labs Skills, the Shoggoth collective. It
is also the complete roster: every governed member, the four bounded delivery
worker roles, and the upstream skills that ship unchanged. It describes what
exists in the repository, what evidence is still missing, and where
contributions could help within each member's scope. The root
[README](./README.md) is a front door and links here rather than repeating it.

It is not a product forecast. “Could become” means that the current contract
has a credible direction, not that the work is scheduled, funded, or already
partly delivered. The source of truth for the next accepted change remains
each skill's `EVOLUTION.md` ledger.

Original snapshot: 31 August 2026, at repository revision
`ec426cd00508a8cb118d879f3f65d99098c4d787`. Reconciled against the contracts and
ledgers at `104f6f82c390003fb61039d3023d07c1abe05086` on 22 September 2026.
This records a source review; it does not claim fresh field evaluations.

## WHAT WE ARE TRYING TO BUILD

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

## HOW TO READ EACH ENTRY

Entries distinguish shipped behaviour, open work, and standing limits:

- **Today** describes the checked-out skill contract and recorded evidence.
- **Open work** names an unfinished implementation or evaluation in the ledger.
- **Boundary** states a limit the result must retain, including on a mature skill.
- **Possible direction** is a proposal beyond the current operation, not an
  accepted job or evidence that an existing capability is missing.
- **Further evidence** identifies observations that could justify revisiting a
  mature frontier. It creates no development commitment.

A mature ledger has no held next job. Maturity closes the recorded programme;
it does not prove general correctness or usefulness on every repository. A
maintainer must record new external evidence that invalidates the closure
before another frontier run can begin. The [evolution contract](./plugins/hexaemeron/skills/VERSIONING.md)
sets that rule, and each skill's ledger owns its status. Kronos is terminal by
design and does not rank itself for further evolution.

Standing limits are not a backlog. Signing, underwriting, security conclusions
and causal claims keep their named owners even when a contribution would make
a hand-off easier. No numeric maturity scores appear here.

## SHARED LAW AND CONTROLLED DELIVERY

### PROMISE MACHINE

**Today.** The Promise Machine gives every first-party skill one law for
evidence, consequence, composition, refusal, and recovery. Repository checks
validate declarations, installation copies, run-observation records,
contributor ranking, router selection, and the first-party licence boundary.

**Boundary.** Structural conformance is not domain truth. A passing promise
check cannot establish that a protocol design is correct, that a data source is
canonical, or that an agent answer is useful unless another named operation
supplies that evidence.

**Possible direction.** It could become a common interchange layer for
crypto R&D tools: every result would carry a machine-checkable statement of
what was observed, which bytes and chain positions support it, which later
actions it permits, and which uncertainty survives the hand-off. That needs
real integrations and hostile composition tests, not a larger vocabulary.

### FIAT

**Today.** [Fiat](./plugins/hexaemeron/skills/fiat) controls an explicit,
hash-chained repository delivery through study, runbook, implementation, audit,
prose, push, and integration. It owns a dedicated worktree, durable state,
per-step receipts, stacked pull requests, signed integration checks, verified
local checkpoint archives, recovery, and retirement. Delegated packets carry
a task handle bound to the run, phase and role; stale handles are refused.

**Open work.** Closed audit history still ships in the tree as frozen prose,
and audit evidence shares the Leads not pursued field. The held job separates
that evidence and moves closed records behind digest-bound indexes. Local
checkpoints still do not establish safe cross-machine hand-off or distributed
orchestration.

**Possible direction.** Fiat could become a dependable delivery kernel
for long-running agent work: resumable across controlled hosts, capable of
proving exactly which worker and tool produced each transition, and able to
surface recurring failures to the research layer without relaxing human
publication authority. A distributed version would need authenticated state
transfer, replay protection, and recovery tests before it could claim that.

### KRONOS

**Today.** [Kronos](./plugins/hexaemeron/skills/kronos) ranks eligible held
frontier jobs, records one durable goal, can park work, and dispatches the
highest unparked job through Fiat only when a user explicitly asks it to run
the field. Its [ledger](./plugins/hexaemeron/skills/kronos/EVOLUTION.md) is mature
and the loop is terminal by design.

**Boundary.** Its arithmetic is reproducible, but the input scores are human
judgements. Ranking does not make those judgements objectively correct.

**Further evidence.** Recorded failure rates, maintenance cost, field coverage
and downstream reuse could inform a person's scores under the existing policy.
That is an evidence contribution to ranking; there is no held job to turn
Kronos into another research loop. The human retains policy and stop control.

## SOURCES, HISTORY, AND RELEASES

### HOROS

**Today.** [Horos](./plugins/horos) emits and verifies repository reading
boundaries, byte censuses, drift reports, and skeleton maps for Python,
TypeScript, Go, C++, Solidity, and Markdown. Its [ledger](./plugins/horos/skills/horos/EVOLUTION.md)
is mature: the Markdown outline extractor closed the last held job. At that
closure, every filetype above 1% of this repository's readable bytes was mapped
or was a data format with no declarations to outline.

**Boundary.** A boundary is fail-open and never applies during a security
review. A skeleton reports recognised declarations and regions it cannot
outline; it does not prove semantic coverage. Byte counts do not measure reading
time.

**Further evidence.** Use the shipped exclusions, outlines and drift checks on
other repositories. Missed declarations, incorrect exclusions, unsupported
languages or measured reading costs could supply evidence for a maintainer to
reopen the frontier. A new capability or reading-cost saving would need evidence
of a specific gap. Horos must keep excluded files and unrecognised regions visible.

### LEMMA

**Today.** [Lemma](./plugins/lemma) converts Solidity compiler standard JSON
input or Markdown trees into validated JSONL chunks with source locations and
separate quotation, model, and embedding text. It records corpus provenance and
stops before embedding, indexing, retrieval, or answering.

**Open work.** Its callable-surface ABI validation does not independently verify
return types or state mutability.

**Possible direction.** Lemma could add stable incremental rebuilds and
versioned schema migration to its shipped source preparation. Compiler-aware
Solidity units, Markdown structure and byte-traceable chunks already exist;
future retrieval must retain that provenance.

### LAZARUS

**Today.** [Lazarus](./plugins/lazarus) captures finite fixed-block Ethereum
evidence, proves and verifies the supported state offline, replays the exact
recorded RPC requests over loopback, and packages preservation releases. It
reconstructs `receiptsRoot` for full ordered receipt sets; scoped witnesses
prove one receipt payload and its log projection. Empty witnesses are accepted
only at Ethereum's empty trie root and prove zero relations. Its
[ledger](./plugins/lazarus/skills/lazarus/EVOLUTION.md) is mature.

**Boundary.** Transaction hashes and unrelated RPC evidence remain recorded,
not thereby proved. Canonical-chain and provider-independence claims remain
outside the fixture. Preservation is finite and does not replace an archive node.

**Further evidence.** Historical tests using the shipped capture, replay and
release operations could expose a missing proof relation, a capture limitation
or a migration failure. Preserve such a specimen before proposing fixture
discovery, multi-provider comparison or broader proof support as new work.
Deterministic local replay already ships.

### BEREAN

**Today.** [Berean](./plugins/berean) binds a document corpus by digest, proves
citations against exact bytes, ties live values to a chain and block, records
evaluation, and governs promotion and rollback of a grounded protocol-agent
release.

**Open work.** The reference release uses a demonstration corpus and preserved
Aave v4 readings. No live Wildcat reference release or Ariadne binding has
been established.

**Possible direction.** Berean could support continuously evaluated
protocol assistants whose releases fail closed when documents, deployments, or
chain readings drift. Real value would come from held questions written by
protocol users and maintainers, not from a larger demonstration set.

### ARIADNE

**Today.** [Ariadne](./plugins/ariadne) captures, inspects, verifies, and
performs bounded replay of digest-bound in-toto statements. Its predicate
registry covers Solidity, datasets, historical-state fixtures, and
grounded-agent releases. It can bind an existing Berean release without
rerunning the agent or using the network. Its
[ledger](./plugins/ariadne/skills/ariadne/EVOLUTION.md) is mature.

**Boundary.** Ariadne does not sign a statement, authenticate its publisher, or
prove the truth of the underlying evidence. Those are separate relations.

**Further evidence.** Apply the existing predicates to real releases and
preserve cases whose evidence cannot be represented or checked. A new artefact
class needs its own supported relation and specimens before a maintainer can
reopen the frontier. Signature verification and publisher policy still need
explicit owners; their absence does not leave the current promise unfinished.

### SYNKRISIS

**Today.** All four [Synkrisis](./plugins/synkrisis) operations ship: checked
cohort construction, deterministic bounded diagnosis, fixed-template rendering,
and verification that recomputes the entire path from the original inputs. A
measured work budget also ships.

**Open work.** The current two rule kinds have been exercised on constructed
records, not a captured production cohort.

**Possible direction.** Captured production cohorts could establish which
shipped Synkrisis rules help investigations and which patterns need new rules.
Further comparison methods, including counterfactual specimens, remain
proposals requiring their own evidence. Synkrisis must never promote
correlation into cause or authorise remediation.

### ANAMNESIS

**Today.** [Anamnesis](./plugins/anamnesis) admits audit findings and the
changes that answered them against an explicit rights basis, keeps the
producer's bytes and identifiers unchanged, and curates, releases and projects
read-only views for Elenchus and Synkrisis. Its corpora rebuild offline from
preserved producer bytes; registered mappers record which implementation read
each source.

**Open work.** The three admitted corpora were all produced in this repository.
A mapper is declared once per curation policy, so a corpus cannot yet mix
sources in different formats. The held job requires per-source mapper
declarations and an external producer under an explicit rights basis. Corpus
completeness, finding validity and remediation correctness remain unproved.

**Possible direction.** Anamnesis could hold a cross-producer record of
what auditors found and what teams changed in reply, so a later reader can ask
whether a class of defect keeps returning. Admission would still turn on a
stated rights basis rather than on what happens to be reachable.

## PROTOCOL BEHAVIOUR AND SOLIDITY

### JANUS

**Today.** [Janus](./plugins/janus) validates a conformance manifest and runs
seven bounded gates for the Wildcat v2.5 hook seam, producing Markdown and
SARIF reports about what the hook may observe and change before and after a
host action.

**Open work.** No second host adapter demonstrates that the manifest model
generalises beyond this callback design.

**Possible direction.** Janus could compare hook and callback systems
across protocols using host-specific adapters over a common effect language,
with temporal properties and executable negative specimens. Generality must be
earned one real host at a time.

### PANDECTS

**Today.** [Pandects](./plugins/pandects) maintains executable credit-law
records, a rendered catalogue, and broken specimens that prove each law catches
its named failure. Its structured search records currently cover Foundry
campaigns.

**Open work.** Echidna and Medusa results remain prose in the audit record rather
than structured search records.

**Possible direction.** Pandects could extend its executable law library to
adjacent accounting systems and add checked hand-offs from laws to Foundry,
Echidna, Medusa, Janus manifests and formal tools. Each law must stay
small enough to falsify and must never stand in for a whole-protocol audit.

### HERMES

**Today.** [Hermes](./plugins/hermes) optimises one named Solidity gas class at
a time. It records a baseline, applies one candidate, remeasures, reruns
behaviour tests, checks storage layout and selectors, and demands targeted
arithmetic evidence before keeping a change.

**Open work.** Its 12 classes cover 62 of the 120 rules in the pinned corpus; 58
cannot yet be selected as candidates.

**Possible direction.** Hermes could turn a broad, versioned optimisation
corpus into reproducible compiler- and chain-aware experiments, including
interaction effects and long-term regressions. More rules only matter when
their preconditions and safety checks are executable.

### DOKIMASIA

**Today.** [Dokimasia](./plugins/dokimasia) compiles a frontend's routes,
actions and access guards into a coverage denominator, then reconciles a
reviewed UAT workbook against it so that every scoped item carries exactly one
disposition. Confirmed entries name a person and any applied rule with its
author. Its committed `wildcat-app-v2` scrutiny regenerates offline from
preserved coverage, scrutiny and report records.

**Open work.** The held job is a browser-driven draft of dispositions from a
pinned application, with observed oracles and human confirmation kept separate.
Current entries come from the workbook and record no running application
behaviour. The pinned application checkout and the reviewed workbook bytes
are not preserved here, so the scrutiny cannot yet be rebuilt from its primary
inputs. The closure ratio measures how much is accounted for; it never states
that anything passed.

**Possible direction.** Dokimasia could carry the same denominator across
several applications and releases, each with preserved inputs and a named
reviewer behind every disposition, which would make an unreviewed release
visible rather than arguable.

### HOMOLOGIA

**Today.** [Homologia](./plugins/homologia) validates a closed manifest and its
declared vectors into deterministic checked inputs, binding source digests and
expected-answer provenance. A proved-form answer must name a safe Lazarus
artefact reference; admission does not verify that artefact or its answer.

**Open work.** Mirror execution, integer comparison and parity verdicts have
not shipped. The next job runs one pinned mirror over checked vectors without
judging its answers. Chain-side execution remains with Lazarus.

**Possible direction.** Homologia could compare one pinned on-chain
calculation with one pinned TypeScript or Python mirror over declared vectors,
integer for integer, preserving every divergence as a specimen. Pandects could
supply economic laws and Lazarus proved chain-side answers, but agreement would
still not prove that either implementation models the right rule.

### UPSTREAM PASHOV SUITE

**Today.** X-Ray maps a Solidity repository before audit; Solidity Auditor
reviews contracts; Fizz creates stateful Echidna/Medusa harnesses; Fizz Convert
turns recorded properties into assertions; Fizz Sync reconciles a harness with
source changes. All of them ship unchanged under their upstream MIT licence.

**Boundary.** Wildcat does not own their roadmaps and must not describe an
upstream possibility as a first-party commitment.

**Possible direction.** The collective can improve the checked hand-offs
around those tools: feed precise scope into them, preserve their raw outputs,
turn failures into Elenchus specimens, and bind released audit artefacts with
Ariadne. Changes to the tools themselves belong upstream.

## LENDING AND CREDIT RECORDS

### ALEXANDRIA

**Today.** [Alexandria](./plugins/alexandria) preserves heterogeneous lending
inputs by digest, emits verified derived views, creates unsigned release
statements, and answers address queries without hiding source coverage. One
Compound v3 Phase 0 execution witness exists. The Ethereum USDC Comet interval
collector resumes after interruption, rewinds after reorgs, reconciles providers
and verifies offline. Version 2 interval receipts attribute proxy logs to
implementation epochs by block, transaction index and log index. Wildcat V1 and
V2 interval captures also ship with committed manifests of externally preserved
staging files. Rebuilding those releases requires the staging files; metadata
verification alone does not rebuild them.

**Open work.** Provider reconciliation omits the transaction index, so matching
logs reported at different transaction positions can still be marked agreed.
The held job must dispute that difference while preserving both providers'
bytes and the recorded meaning of historical releases.

**Possible direction.** Alexandria could become a durable public archive
of raw lending evidence across venues and time by extending its shipped
capture and release operations to more markets, with reviewed reconciliation
and schema migration. It should continue to preserve rather than interpret.

### TABULARIUM

**Today.** [Tabularium](./plugins/tabularium) converts supported preserved
venue records into deterministic, venue-qualified credit-event releases with
explicit mapping provenance and coverage. One non-canonical Compound v3 witness
has been rebuilt from Alexandria.

**Open work.** Compound Phase 1, its canonical adapter, and the Ethereum USDC
specimen do not exist.

**Possible direction.** Tabularium could maintain a broad, versioned
event model across lending protocols, with venue-native meanings kept visible,
mapping changes diffable, and every release reproducible from preserved input.
It should not erase disagreement in pursuit of a universal-looking table.

### PROBITAS

**Today.** [Probitas](./plugins/probitas) collects evidence from addresses a
subject declared and builds a verified borrowing and repayment dossier with
source coverage, qualifications, and unknowns kept visible. It can compare two
recorded dossiers for the same declared subject without inferring chronology
or debt resolution from a difference.

**Open work.** Morpho Midnight secondary-market exits on Base remain
unattributable and the relevant curation data has not been collected.

**Possible direction.** Probitas could extend venue coverage and add explicit
identity claims and dispute records to its shipped dossiers and comparison
operation for human underwriting. It should never guess undisclosed
addresses, equate an address with a legal person, or make the credit decision.

## ENGINEERING DISCIPLINES

### PROTASIS

**Today.** [Protasis](./plugins/hexaemeron/skills/protasis) checks the
mechanical content and relations of studies, risk registers, amendments,
runbooks, and optional version records. It also checks one closed
candidate-by-criterion design-evidence record progressively: first at design
lock, then when each step and the final integration make more evidence due.
Its [ledger](./plugins/hexaemeron/skills/protasis/EVOLUTION.md) is mature.

**Boundary.** It proves that the matrix is complete and the declared evidence
is present when due. It does not prove that a cited report is true or that the
chosen design is correct.

**Further evidence.** Preserve a real study or runbook whose missing relation
passes the checks, or whose valid evidence the format cannot express. Such a
case could justify another project shape or evidence producer. More
traceability is not a held job, and design judgement remains with people and
the relevant specialist.

### PHYLAX

**Today.** [Phylax](./plugins/hexaemeron/skills/phylax) mechanically checks
Python and source-local TypeScript controls and guides review of external data,
commands, URLs, credentials, dependencies, paths, and model output. Its
[ledger](./plugins/hexaemeron/skills/phylax/EVOLUTION.md) is mature.

**Boundary.** A clean Phylax result is not a whole-system security review and
does not cover Solidity.

**Further evidence.** A reproduced off-chain failure or a missed control in a
real application could justify a new rule or language surface. Preserve the
broken specimen and name the proposed check before reopening. Taint analysis
and dependency or provenance policies remain proposals requiring that evidence;
none is implied by a clean result today.

### EPHOROS

**Today.** [Ephoros](./plugins/hexaemeron/skills/ephoros) asks the operator's
questions first, then checks bounded patterns for logs, metrics, durations,
runbook annotations, and address-key exposure across the surfaces it supports.

**Open work.** The TypeScript rules are lexical: a comment before a string key
hides it from E002 and E005, and E001's concatenation half reads proximity rather
than operands. These are the held repair target. E004's supported block-style
YAML subset remains a standing limit.

**Possible direction.** Ephoros could specify and test end-to-end
observability contracts across Python, TypeScript, Solidity events, workers,
and release pipelines. The goal is an explainable failure, not more telemetry.

### METRON

**Today.** [Metron](./plugins/hexaemeron/skills/metron) accepts a declared
workload, validates a recorded baseline and candidate measurement, and keeps or
rejects one change against the stated budget. It also takes the measurement:
`time` runs one command in its own process group under a timeout and an output
cap, repeats it, and writes the run file the check reads, with the declared
aggregation of the kept samples and the spread a variance is set from.

**Open work.** The check compares a run against a baseline without reading the
conditions the recorder wrote beside each, so two numbers taken on different
machines or interpreters compare silently.

**Possible direction.** Metron could hold a comparison to those recorded
conditions, and could add variance handling beyond the declared spread and
long-term regression tracking for off-chain tools. Hermes should continue to
own Solidity gas.

### ELENCHUS

**Today.** [Elenchus](./plugins/hexaemeron/skills/elenchus) starts with a
failure already in hand, reproduces and localises it, fixes the cause, and
requires parent-red and fixed-green evidence from fresh unittest, Forge, or
Node reports. It has a documented Lazarus RPC-fixture hand-off. Its
[ledger](./plugins/hexaemeron/skills/elenchus/EVOLUTION.md) is mature.

**Boundary.** Success proves the named failure and guard relation, not the
absence of nearby defects.

**Further evidence.** Use Elenchus on real failures and retain specimens where
its reproduction or guard checks cannot express the result. Anamnesis owns
custody of historical findings and remedies; Lazarus owns preserved chain
fixtures. Elenchus must reproduce the present failure before using either as
evidence, and no corpus expansion is a held Elenchus frontier job.

### HYPOMNEMA

**Today.** [Hypomnema](./plugins/hexaemeron/skills/hypomnema) decides whether a
durable decision belongs in an ADR, comment, runbook, interface note, or
pointer to an existing record, and checks several of those shapes mechanically.
Study mode binds a selected Protasis candidate to one declared ADR or
skill ledger and refuses a duplicate the study declares.

**Open work.** It does not discover a second established home for the same
decision when the study declares only one. The held job checks that remaining
duplicate through exact identifiers.

**Possible direction.** Hypomnema could maintain a navigable explanation
graph from code and alerts to decisions, assumptions, and operating procedures,
while rejecting duplicate or stale records.

### IMPRIMATUR

**Today.** [Imprimatur](./plugins/hexaemeron/skills/imprimatur) diagnoses three
tiers of prose defects, including banned AI writing habits, unsupported
technical vocabulary, repeated formulae, and source-comment wording. It does
not rewrite the text.

**Open work.** Its first 64-sample evaluation failed annotation-agreement and
holdout-coverage gates. The holdout is spent and the reported scores remain
provisional.

**Possible direction.** It could become a language and evidence lint
with independently labelled corpora for several engineering registers, stable
false-positive budgets, and transparent versioned rules. Contributors must
repair the evaluation before tuning to its numbers.

### VULGATE

**Today.** [Vulgate](./plugins/hexaemeron/skills/vulgate) rewrites messages,
documentation, announcements, and technical explanations into a plain human
register while protecting facts, numbers, commitments, caveats, links, and
intended meaning.

**Open work.** Full semantic parity remains model judgement rather than a
repeatable evaluation.

**Possible direction.** It could pair protected-content extraction with
held human evaluations across several registers, making tone changes easier to
check without flattening every author's voice.

### SAPHENEIA

**Today.** [Sapheneia](./plugins/sapheneia) shapes an agent's replies for AuDHD
readers and has one bounded operation for every durable record an agent writes,
including audit records, issues, comments, pull requests, documents and commit
messages. It preserves protected evidence and does not change another skill's
gates.

**Open work.** The ten interaction rules have no published held cross-model task
corpus.

**Possible direction.** It could become an evaluated interaction layer
that adapts state, choices, and next actions to different cognitive needs
without patronising the reader or hiding uncertainty.

### BREVITAS

**Today.** [Brevitas](./plugins/brevitas) enforces structural output budgets on
engineering prose and checks specified evidence tokens, including addresses,
hashes, file-line references and numbers, against the source. Preservation of
counterexamples and reproduction steps remains agent-checked.

**Open work.** It has no held cross-model engineering-review corpus. Semantic
preservation beyond protected tokens remains agent-checked.

**Possible direction.** It could offer register-specific budgets backed
by reader-comprehension and decision-quality evidence, producing shorter work
because it is easier to use rather than because a line count looks tidy.

## FIAT'S FOUR WORKER ROLES

The workers are execution roles, not extra governed skills.

### SURVEYOR

**Today.** Surveyor receives one source-bound study packet and returns a study.
It cannot receipt the phase, steer Fiat, publish, or widen the task.

**Possible direction.** Its packet could support reproducible research
logs and independent source verification while retaining the same lack of
controller authority.

### MASON

**Today.** Mason implements and tests one exact runbook step on its assigned
branch pair. It cannot push, open a pull request, merge, or alter Fiat.

**Possible direction.** Its packet could support more execution
environments and stronger artefact capture without becoming an autonomous
delivery controller.

### WARDEN

**Today.** Warden runs one exact audit round, preserves raw findings, fixes
bounded defects, and reports an Elenchus verdict. It cannot receipt its own
round or call missing evidence clean.

**Possible direction.** It could select richer security suites from the
study's named attack paths and preserve machine-readable findings for cross-run
analysis, with Fiat still controlling acceptance.

### SCRIBE

**Today.** Scribe performs one bounded prose pass, running Imprimatur, applying
Vulgate without changing protected content, and rerunning the lint. It cannot
invent claims, issues, or publication authority.

**Possible direction.** It could check more document types and held
reader tasks while remaining a surface editor rather than a source of facts.

## RESEARCH PROGRAMMES WORTH CONTRIBUTING TO

These are integration proposals across shipped operations and named open gaps.
Using a mature skill in a new path does not reopen its frontier. Any extension
still needs the evidence and owner required by that skill's ledger.

### HISTORICAL PROTOCOL LABORATORY

Use Horos only for ordinary orientation; its exclusions never narrow the
security investigation. Combine Lazarus, Elenchus, Pandects, Janus, the Pashov
suite, and Ariadne so a real historical failure can be reduced, replayed
offline, tested against a named law or host boundary, and released with
evidence. The current pieces are useful; a multi-protocol public specimen set
is missing.

### CHECKABLE PROTOCOL ASSISTANTS

Combine Lemma, Lazarus, Berean, Ariadne, Sapheneia, and Brevitas around held
questions from protocol users. The success measure is not answer volume. It is
whether answers remain source-correct under document and chain drift, refuse
when support is absent, and help a person decide what to do next.

### CROSS-PROTOCOL BEHAVIOUR

Extend Janus with real host adapters, Pandects with more executable laws, and
Homologia from checked inputs through mirror execution to a tested parity
operation. This could expose where different protocols use the same words for
different state transitions.

### OPEN LENDING EVIDENCE

Extend Alexandria capture, complete Tabularium adapters, and add Probitas
curation for declared intervals and venues. Release preserved input, mapping
provenance, coverage, and disputes separately so a dossier can be corrected without
rewriting history.

### EVIDENCE FROM REPEATED DELIVERY

Capture Promise Machine observations from real Fiat runs, compare declared
cohorts with Synkrisis, and feed reproduced failures to the relevant owner.
This is how the collective can learn without allowing the comparison layer to
diagnose causes or change code on its own.

## THE ADMISSION TEST FOR NEW WORK

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

## CHOOSING USEFUL WORK

Start with the held next job in an open ledger. These are examples of recorded
gaps, not a claim that every job is small or ready to start:

- a held production cohort for Synkrisis;
- a live Wildcat reference release for Berean;
- a second real host adapter for Janus;
- a pinned Homologia mirror runner over the checked inputs, before comparison;
- structured Echidna or Medusa search records for Pandects;
- ABI return-type and mutability validation in Lemma;
- transaction-index reconciliation in Alexandria and the still-missing
  canonical Compound v3 Phase 1 adapter in Tabularium;
- independent labels and fresh holdout tasks for the prose and interaction
  skills.

The exact accepted next job may be narrower than these examples. Check the
member's `EVOLUTION.md`, open issues, tests, and `AGENTS.md` before changing its
files. For a mature member, contribute a reproducible field result through its
existing operations; a possible direction here does not authorise another
frontier run.

## REVIEW RHYTHM

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
