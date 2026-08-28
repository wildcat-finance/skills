# Futureproofing the Shoggoth

This is the development map for the collective as a whole. It asks which
abilities deserve to become part of the lasting system, which experiments
should stay contained, and what each member still needs before a stranger can
rely on it without its maintainer standing nearby.

It is a strategy record, not a promise that every item below will be built. The
current contracts, ledgers, tests, and permissions still decide what any member
may do today. The [Promise Machine](./PROMISE_MACHINE.md) still governs every
claim and hand-off.

## The question that matters

> Are we making the collective measurably better at solving important problems
> that recur, or merely making it more elaborate?

The right unit of progress is a proved improvement on a real problem. A closed
issue, a version bump, a longer catalogue, and a clever demonstration are not
proof of that improvement.

## What fully formed means

A fully formed member does not need to do everything. It does need to do its
own job completely.

- A stranger can give it a real job in plain language.
- It finishes that job or gives a clear, useful refusal.
- It survives the failures that happen outside a demonstration.
- Its output contains enough evidence for the next person or member to trust
  it.
- Its maintainer is not the hidden brain supplying missing judgement by hand.
- Its boundary with neighbouring members is clear and tested.
- Somebody owns its data, upkeep, failures, and retirement.

That is a higher bar than having a good prompt, a sound specification, or a
passing happy-path test.

## Questions to ask before evolving anything

These questions come before implementation and before a proposal becomes a
held frontier job. A proposal with weak answers remains research.

### 1. Is the problem real?

- Who has the problem? Name the user, operator, researcher, reviewer, or team.
- What decision, failure, or expensive task are they facing?
- How often has it happened?
- What are three real examples from different jobs or repositories?
- What do people do today, and what does that workaround cost in time, money,
  risk, or attention?
- What happens if we leave it alone for six months?

One severe, repeated security, legal, or financial failure may outweigh the
three-example rule. The consequence must be concrete rather than imagined.

### 2. Is it a shared ability or a local quirk?

- Does the same underlying problem appear across different repositories,
  models, hosts, or users?
- Are we solving a class of problems or memorialising one awkward incident?
- Which other members become more useful if this succeeds?
- Does the work strengthen a shared hand-off, source record, test, recovery
  path, or operator view?
- Could the need be met by a connector, fixture, recipe, or example instead of
  changing the core member?
- What evidence would show that nobody else needs it?

Do not turn one awkward repository, one model quirk, one host limitation, or
one issue into a permanent core feature.

### 3. Can we prove that it helped?

- What is the present baseline?
- What exact outcome should improve: completion, correctness, recovery, time,
  cost, user effort, or safety?
- What is the smallest experiment that could test the idea?
- What result would disprove the idea?
- Which examples will be kept unseen until the experiment is ready?
- Can another person repeat the test from the record?
- What result would justify keeping the change?

If no observation could prove the idea wrong, it is a preference rather than a
research claim.

### 4. Does it have the right owner and home?

- Which member owns the problem under the current marketplace boundaries?
- What does that member receive, and what must it hand to the next member?
- Are we trying to widen one member because the correct sibling is unfinished?
- Does the work belong in the core, a plugin, a connector, a data release, a
  test fixture, or a written example?
- Does it remove hidden maintainer judgement or merely move that judgement to
  a less visible place?
- Which existing promise or refusal must change if the work succeeds?

No member should become a general-purpose fallback merely because it is easier
to add instructions there.

### 5. Can we afford to keep it alive?

- Who owns the result after the first release?
- What data, external service, chain access, model access, or specialist review
  must remain available?
- How will drift, broken sources, false alarms, and stale assumptions be
  noticed?
- What does one year of upkeep cost?
- Can the result be reproduced after a machine, provider, or model changes?
- What is the safe way to turn it off?

The build cost is often the smaller part. Collection, checking, support, and
repair are where long-lived systems become expensive.

### 6. When will we stop?

- What is the time or effort limit for the experiment?
- Which result means continue, change course, park, or kill?
- What evidence would make us remove the feature from the core?
- Which old path will disappear if the new one succeeds?
- Does the finished system become simpler to operate?

Every research bet needs a kill condition before enthusiasm and sunk cost take
over.

## The evolution admission gate

Before work enters the core frontier or a Fiat delivery packet, its written
proposal should contain all of the following:

- a named user and a real decision, failure, or repeated task;
- three examples from distinct jobs or repositories, or one documented
  high-consequence recurring failure;
- the present workaround and its cost;
- the shared ability being improved;
- the correct member, boundary, and hand-off;
- a recorded baseline and a measurable target;
- the smallest useful experiment and the result that would disprove it;
- unseen examples or an independent check;
- the expected upkeep and its owner; and
- a time limit and kill condition.

Missing answers do not make the idea bad. They keep it in the research queue
until the unknowns are resolved.

A niche proposal may skip the breadth requirement only when at least one of
these is true:

- it closes a severe security, legal, or financial risk;
- a named user is paying for or depending on the exact result; or
- it creates a small building block that several members can reuse.

The exception still needs a baseline, an owner, an upkeep plan, and a kill
condition.

### Where work should live while it proves itself

| Home | Use it when | Promotion rule |
| --- | --- | --- |
| Core member | The ability recurs across users or targets and belongs inside the member's promise | Keep it only after repeated results and a known upkeep owner |
| Connector or adapter | The need comes from one host, venue, chain, provider, or external format | Promote only the shared part; leave the local translation at the edge |
| Example or fixture | The value is teaching, testing, or preserving one failure | Keep it as evidence without widening the member's job |
| Research branch | Demand, method, or value is still uncertain | Time-box it, record the result, then graduate, change course, park, or remove it |

Niche work can be valuable. Containment stops a useful special case from
quietly becoming the shape of the whole system.

## What an R&D powerhouse should mean here

The collective becomes a serious research organisation when it repeatedly
turns uncertain, important questions into checked knowledge and reusable
abilities. It should be good at learning, discarding weak ideas, preserving
negative results, and moving proved work into dependable operation.

It should not be judged by how many agents it can name. It should be judged by
what it can discover, prove, reuse, and operate.

### Five research programmes

These programmes give individual work a larger direction without erasing
member boundaries.

| Programme | Central question | Lasting output |
| --- | --- | --- |
| Reliable agent delivery | Can a bounded job finish, recover, and hand over trustworthy evidence without a maintainer rescuing it? | Better Promise Machine checks, Fiat recovery, representative jobs, and failure records |
| Evidence-bound research | Can an answer be traced to stable source material and checked again later? | Preserved sources, source-linked chunks, release records, question sets, and comparable run observations |
| Credit intelligence | Can raw lending records become a reproducible credit history and a useful human dossier without hiding gaps? | Collectors, venue mappings, releases, dossiers, corrections, and coverage records |
| Executable protocol safety | Can economic laws, hook permissions, gas changes, and security checks catch real failures without inventing safety? | Reviewed laws, broken specimens, host adapters, exploit cases, and measured changes |
| Human use and memory | Can people understand, steer, and revisit the work without losing evidence or being buried in it? | Durable decisions, clear replies, checked prose, user preferences, and operator runbooks |

Each programme needs a human owner who decides why the question matters. Kronos
may rank eligible held jobs. It does not choose the collective's research
purpose.

### The research loop

Every serious experiment should follow the same simple loop:

1. Observe a real problem and preserve the example.
2. State a testable explanation or proposed improvement.
3. Record the baseline and the result that would disprove the idea.
4. Run the smallest experiment that can answer the question.
5. Repeat it on unseen examples and, where the stakes warrant it, ask another
   person to check it.
6. Decide: keep, change course, park, or kill.
7. Preserve the result and any reusable asset before moving on.

Protasis can make an individual study testable. The programme owner still has
to decide whether the question is worth asking.

### Research must compound

Every funded experiment should leave at least one useful thing behind, even
when its main idea fails:

- a real failure specimen;
- a clean dataset or preserved source;
- a repeatable measurement;
- a reviewed law or property;
- a connector or adapter;
- a question set with expected answers and refusals;
- a decision record explaining why an option lost; or
- a run record that a later Synkrisis implementation could compare.

Negative results belong in the record. Repeating a failed idea because nobody
wrote down the failure is wasted research.

### A starting portfolio

Use this split as a starting allocation, then change it when the evidence says
to:

- 50% on shared foundations: evidence, delivery, recovery, testing, and
  operator visibility;
- 30% on complete vertical programmes that solve a real problem from start to
  finish; and
- 20% on uncertain, high-upside experiments with strict time limits.

The percentages are a steering aid rather than a permanent rule. Review them
quarterly. A foundation that never serves a real programme is drifting just as
surely as a niche feature.

### Review rhythm

- For each experiment: decide keep, change course, park, or kill when its time
  limit ends.
- Monthly: review failures, maintainer rescues, repeated user requests, and
  assets created.
- Quarterly: review the five programmes, move time between them, and close work
  that no longer answers an important question.
- Yearly: ask which members should be merged, narrowed, retired, or turned into
  ordinary tools rather than assuming the roster must only grow.

The review should use run records and real outcomes. Synkrisis helps compare
validated observations, and it now produces a checked cohort, bounded findings
over one, and a report that verifies against its inputs, though a person still
makes these decisions from the evidence available.

### Measures that matter

Track trends rather than a single grand score.

- How often real jobs finish without maintainer rescue.
- How often failures produce a useful refusal and recovery path.
- How much hidden judgement remains outside the record.
- How often an ability works on a second repository, host, venue, or user.
- How long a user waits for a trustworthy answer or artefact.
- How much human time and operating cost the result saves.
- How many later projects reuse the datasets, fixtures, laws, adapters, and
  measurements created by research.
- How often independent checks agree, and where they disagree.
- How many stale or unowned features are retired.
- Whether real users make better decisions or avoid concrete failures.

Do not use issue count, version count, prose volume, agent count, or raw task
count as stand-ins for value.

## Recommended build order

The order matters because later members depend on evidence and delivery that
the earlier work supplies.

1. Make the Promise Machine and Fiat dependable across real end-to-end jobs.
   Prove pause, recovery, hand-off, and safe refusal on unrelated repositories.
2. Finish the more contained craft members: Protasis, Metron, Hypomnema,
   Imprimatur, Vulgate, Brevitas, Horos, and Lemma. Give each a representative
   test set and remove hidden maintainer judgement.
3. Build the evidence backbone through Ariadne and Lazarus. Long-lived research
   needs source and release records that survive changing machines and
   providers.
4. Complete one credit path from Alexandria through Tabularium to Probitas
   before adding many venues and chains. One trustworthy vertical path teaches
   more than a wide collection of partial connectors.
5. Exercise Berean against current Wildcat material and questions from real
   users. Its answer quality, refusals, source use, and upkeep must be observed
   in practice.
6. Implement Synkrisis after enough trustworthy run records exist to compare.
   Building the comparison layer first would produce neat reports about weak
   inputs.
7. Develop Pandects, Janus, Hermes, and the vendored security path alongside
   real protocol work, where actual failures can test them.

Do not make Kronos more autonomous before Fiat is dependable. A smarter
allocator sitting on a fragile delivery loop merely fails faster.

## Difficulty guide

The estimates below are planning judgements, not delivery promises. They assume
one or two experienced people, stable access to users and target systems, and
focused work rather than occasional spare time.

| Difficulty | Likely effort | Why it takes that long |
| --- | --- | --- |
| 3/5 | Roughly one to two focused months | The job is bounded, but it still needs representative examples and careful checking |
| 4/5 | Roughly two to four focused months | Several environments, kinds of failure, or human judgements must be brought under control |
| 5/5 | Roughly four to nine months or more | The work depends on live data, deep security judgement, many external systems, or long-running operation |

Continuous collectors, security research, and public evidence services keep
needing attention after their first useful release.

## What each member still needs

This section describes the next shape of a fully formed member. It does not
replace that member's `EVOLUTION.md` ledger or grant authority to do the work.

### Shared law and delivery

#### Promise Machine (4/5)

Fully formed means every real hand-off keeps the exact claim, evidence, gap,
and refusal intact across hosts and members.

It still needs:

- end-to-end tests that cross several members rather than checking contracts in
  isolation;
- simple explanations of why a transition stopped and what the operator can do
  next;
- safe host and contract upgrades with visible compatibility checks;
- signed or otherwise independently checkable installation and release
  records; and
- tests that deliberately try to weaken evidence during a real multi-member
  run.

#### Fiat (4/5)

Fully formed means a bounded delivery can pause, recover, move machines, and
finish without chat history or a maintainer's memory becoming the controller.

It still needs:

- one clear preflight for tools, permissions, signing, GitHub access, and target
  instructions;
- tested recovery from conflicts, failed checks, rate limits, machine loss, and
  long pauses;
- safe movement between environments without losing receipts or branch state;
- proof on several unrelated repositories and job shapes; and
- a plain operator view showing the current step, evidence, refusal, and next
  safe action.

### Phase disciplines

#### Kronos (4/5)

Fully formed means it chooses among eligible jobs using evidence about cost,
dependence, and past results, then explains the choice plainly.

It still needs:

- actual effort and outcome data from completed jobs;
- dependency handling so related work can be ordered or bundled;
- time and cost limits;
- a reasoned explanation for every choice and rejection;
- stale-priority detection; and
- carefully bounded parallel work where jobs truly do not interfere.

#### Protasis (3/5)

Fully formed means a plan makes the outcome, risks, build steps, and checks line
up so another person can execute it without guessing.

It still needs:

- direct links from intended outcomes and risks to steps and checks;
- contradiction detection across the study and runbook;
- expectations that change with the kind of task;
- examples of plans that looked complete but failed in practice; and
- human grading over a mixed set of good and bad plans.

#### Elenchus (4/5)

Fully formed means it can take a messy real failure, isolate the cause, prove
the correction mattered, and leave a guard that catches the failure again.

It still needs:

- more languages and test systems;
- flaky, timing-dependent, and remote-service failures;
- exact environment capture;
- checks that distinguish cause from coincidence; and
- a library of real bugs and known causes.

#### Phylax (5/5)

Fully formed means dangerous input is followed from entry to consequence, and
the risky action is stopped at runtime rather than merely mentioned in a
report.

It still needs:

- input-flow checking across the main supported languages;
- runtime guards around commands, paths, URLs, secrets, and model output;
- stronger dependency and secret checks;
- a maintained set of real attack specimens; and
- independent security review of both the checker and its escape hatches.

#### Ephoros (4/5)

Fully formed means unattended work emits enough useful information for an
operator to notice a failure, understand it, and act without drowning in
noise.

It still needs:

- working signal and monitoring integrations, not only advice about them;
- simulated failures that test alerts and runbooks;
- limits on noise, cost, and sensitive data;
- a proved path from symptom to diagnosis; and
- checks across several kinds of long-running system.

#### Metron (3/5)

Fully formed means it owns a repeatable measurement and can tell a real change
from machine noise.

It still needs:

- recorded measurement environments;
- treatment of noisy machines and warm-up effects;
- CPU, memory, disk, network, and load measurements;
- history and regression detection; and
- experiments that isolate the cause of a slowdown.

#### Hypomnema (3/5)

Fully formed means the right decision or operating reason is easy to find and
stays linked to the code, alert, or interface it explains.

It still needs:

- stale-record and supersession checks;
- links from decisions to code, checks, alerts, and releases;
- help surfacing the relevant record when somebody needs it;
- user tests showing that people can actually find the answer; and
- safe cleanup of duplicate pointers without deleting history.

#### Imprimatur (3/5)

Fully formed means its findings reflect current human judgement, catch known
machine-writing habits, and create few enough false alarms that people keep it
enabled.

It still needs:

- a fresh, human-reviewed evaluation set;
- fewer false alarms and clearer explanations;
- project-specific vocabulary without loose exemptions;
- correct treatment of quotations and specimens; and
- regular checks against new model output as writing habits change.

#### Vulgate (4/5)

Fully formed means a plain-language rewrite can be shown to preserve every
fact, number, name, commitment, caveat, link, and intended relation.

It still needs:

- a protected inventory before each rewrite;
- a repeatable comparison after the rewrite;
- support for long documents, tables, and code-heavy prose;
- consistency tests across several models and registers; and
- a refusal when meaning preservation is uncertain.

### Evidence and research

#### Ariadne (5/5)

Fully formed means a release can still be tied to its evidence and recognised
publisher years later.

It still needs:

- real signature and identity checks;
- key rotation, expiry, and revocation;
- common evidence formats across the suite;
- public or replicated discovery of records;
- long-term verification after tools and locations change;
- use in a real release pipeline; and
- clear handling of partial, missing, and conflicting evidence.

#### Lazarus (5/5)

Fully formed means a historical chain-dependent test can run again without
trusting the original provider or hoping old state remains available.

It still needs:

- support across clients, chains, and common layer-two systems;
- comparison across more than one provider;
- handling for chain rewrites and finality assumptions;
- smaller captures that still contain everything the test needs;
- a portable local replay environment; and
- fixture compression, archive, migration, and retirement rules.

#### Lemma (3/5)

Fully formed means source-linked material stays identifiable as documents move
and can be updated without rebuilding or confusing the whole corpus.

It still needs:

- stable identities across file moves and edits;
- preserved links between related sections and source files;
- incremental updates;
- retrieval tests that measure whether the chunks help later answers;
- broader compiler and document variants; and
- predictable speed on large repositories.

#### Berean (5/5)

Fully formed means real Wildcat questions receive sourced answers or honest
refusals against current documents and preserved chain reads.

It still needs:

- a maintained set of current Wildcat sources and chain evidence;
- real user questions, including hostile and unanswerable ones;
- comparisons across model and instruction changes;
- monitoring and rollback when answer quality falls;
- Ariadne-bound releases; and
- repeated use by people making real protocol decisions.

This is likely a six-to-twelve-month programme before it is dependable enough
for routine internal use.

#### Synkrisis (5/5)

Fully formed means it can compare genuinely comparable run observations,
explain uncertainty and missing information, and refuse causal stories the
records do not support.

It still needs:

- a measured work budget over the delivered four operations;
- reliable observation records from several hosts;
- rules for fair comparison and visible confounders;
- uncertainty and missing-data treatment;
- privacy controls;
- real experimental use; and
- checks against gaming the measures.

It is currently a specification and a command that refuses every operation.
Reaching the fuller form is likely a six-to-twelve-month programme after the
observation supply is trustworthy.

#### Horos (3/5)

Fully formed means it reduces reading cost without hiding the file that would
have changed the answer.

It still needs:

- more languages and file formats;
- fast updates after a small tree change;
- better dependency and entry-point maps;
- reading plans that adapt to the task;
- tests that measure harmful misses, not only saved tokens; and
- useful integration with the places agents actually read repositories.

### Credit intelligence

#### Alexandria (5/5)

Fully formed means lending records arrive continuously, gaps are visible and
repairable, and preserved releases survive provider and venue changes.

It still needs:

- continuous collectors with restart and gap repair;
- several providers and explicit disagreement handling;
- chain rewrite and finality handling;
- more venues and chains after one path is proved;
- permanent, discoverable releases;
- migrations when venue formats change; and
- daily operating ownership.

This is likely a six-to-twelve-month build followed by permanent upkeep.

#### Tabularium (5/5)

Fully formed means preserved venue records become one reproducible credit-event
release without hiding corrections, conflicts, or missing coverage.

It still needs:

- a stable common event language;
- connectors for the venues that matter to real dossiers;
- correction, conflict, and chain-rewrite handling;
- incremental releases;
- independent review of venue mappings;
- useful query surfaces; and
- a tested hand-off to Probitas.

#### Probitas (5/5)

Fully formed means an underwriter can inspect a current, sourced borrowing and
repayment history, see every important unknown, and make the human decision
without reconstructing the evidence by hand.

It still needs:

- broader venue coverage through Tabularium;
- refreshed and change-only dossiers;
- correct treatment of time, debt, repayment, and open exposure;
- cautious address matching with human confirmation;
- independent source checks;
- a human-owned risk decision method; and
- validation with real underwriters and real cases.

### Protocol safety

#### Pandects (5/5)

Fully formed means a large set of reviewed credit laws catches known broken
behaviour and states exactly where each law applies.

It still needs:

- many more independently reviewed laws;
- a clear process for deciding that a law is true and applicable;
- support across the main Solidity test tools;
- historic exploit and broken-design specimens;
- safe composition of laws with different assumptions; and
- use against real protocols rather than only prepared examples.

#### Janus (5/5)

Fully formed means a host-specific hook boundary can be explored deeply enough
to expose forbidden effects, re-entry, failure, and composition problems.

It still needs:

- adapters for several real hook systems;
- assisted permission drafting with human approval;
- fuller observation of state effects;
- multi-hook, re-entry, gas, and failure cases;
- deeper search without claiming complete safety; and
- a library of real hook failures.

#### Hermes (5/5)

Fully formed means it can find worthwhile Solidity gas changes, measure them
fairly, and keep only changes whose behaviour and interfaces remain intact.

It still needs:

- broader coverage of its optimisation advice;
- automatic discovery of candidates;
- more compiler versions and build systems;
- treatment of interactions between several changes;
- comparison of deployment cost with later savings;
- real production contracts; and
- independent security review of accepted changes.

### Human use and memory

#### Sapheneia (4/5)

Fully formed means people can choose the structure and detail that helps them
steer work, without the system guessing a diagnosis or hiding evidence.

It still needs:

- research with actual AuDHD users;
- explicit, optional presentation preferences;
- several shapes for structure and detail;
- safe persistence across long work and different hosts;
- feedback that changes presentation without changing facts; and
- strong privacy limits around personal preferences.

#### Brevitas (3/5)

Fully formed means shorter engineering prose keeps every reason, qualifier,
counterexample, and reproduction step that could change a decision.

It still needs:

- checks beyond addresses and numbers for protected reasoning;
- different budgets for different decisions and stakes;
- expandable evidence behind a short surface;
- a held set of prose from several models; and
- comprehension tests with real readers.

### Fiat workers

The workers are bounded parts of Fiat rather than independent controllers.
They still need their own representative tests because controller receipts do
not prove worker judgement.

#### Surveyor (3/5)

It needs captured sources, explicit disagreements and unknowns, measurable
coverage, and repeated proof that its studies lead to plans another person can
build.

#### Mason (4/5)

It needs safer isolated work across more languages, better protection of user
changes, recovery from interrupted steps, and a large set of real runbook
steps rather than prepared demonstrations.

#### Warden (5/5)

It needs independence from Mason's assumptions, sound tool selection,
calibrated false alarms, real vulnerability specimens, and a second check for
high-consequence conclusions.

#### Scribe (3/5)

It needs meaning-preserving comparison across several files, stable project
terminology, exact previews of public text, and a byte-for-byte hand-off to the
publisher.

### Vendored security siblings

These remain upstream-owned. The development question for this repository is
how safely and usefully they are selected and handed evidence, not how to
quietly rewrite their contracts.

#### X-Ray (3/5)

It needs checked coverage, protection against stale conclusions, and a tested
handoff from repository map to the later audit.

#### Solidity Auditor (5/5)

It needs stronger machine-backed checks, known-vulnerability specimens,
system-level and upgrade review, fewer false alarms, and a second opinion for
high-consequence findings.

#### Fizz (5/5)

It needs strong support for proxies, many-contract systems, and external
dependencies; better property discovery and coverage measures; and failures
that reproduce across the supported fuzzers.

#### Fizz Convert (4/5)

It needs evidence that each generated assertion still means the same thing as
the English property, support for properties that depend on remembered state,
and refusal of assertions that pass without testing the intended claim.

#### Fizz Sync (4/5)

It needs meaning-drift detection, protection for manual work, safe merging of
generated and hand-written changes, and tests against real contract upgrades.

## Whole-program difficulty

Turning every item above into dependable internal practice is larger than a
normal repository roadmap.

- One strong person working mostly alone: roughly three to five years.
- A focused team of four to six people: roughly twelve to twenty-four months
  for trusted internal use.
- A public service that other teams can depend on: longer, with continuing
  data, security, support, and release work.

The estimates overlap because the work can run in parallel. They also assume
that weak experiments are stopped. Trying to complete every wish regardless of
evidence would take longer and produce a worse system.

## The first ninety days

### Days 1 to 30: establish reality

- Name an owner and one concrete question for each of the five research
  programmes.
- Gather representative real jobs, failures, user questions, and current
  workarounds.
- Record completion, rescue, recovery, time, cost, and evidence baselines.
- Apply the admission gate to the open frontier and wish inventory.
- Park proposals that lack a user, proof plan, upkeep owner, or kill condition.

### Days 31 to 60: strengthen the foundations

- Run Fiat and the Promise Machine across several unrelated jobs and preserve
  every failure.
- Fix the kinds of failure that recur across those jobs.
- Give the contained craft members mixed, held examples rather than more prose
  about their intended behaviour.
- Make operator state, refusals, and recovery paths visible in plain language.

### Days 61 to 90: prove complete paths

- Run one credit path from preserved source to human dossier.
- Run one delivery path from study to checked hand-off on a real repository.
- Preserve the datasets, fixtures, measurements, and negative results.
- Hold the first portfolio review and choose what to keep, change course, park,
  or kill.

The result of the first ninety days should be a smaller set of better-supported
bets, not a larger backlog.

## Proposal template

Use this short record before a proposed evolution enters the core frontier:

```text
Problem:
Named user:
Real examples:
Current workaround and cost:
Shared ability improved:
Owning member and hand-off:
Baseline:
Smallest experiment:
Result that would disprove it:
Unseen or independent check:
Upkeep and owner:
Time limit:
Kill condition:
Expected reusable asset:
```

Existing issue-queue names and ownership rules remain unchanged. This record
decides whether an idea deserves scarce research and delivery time; it does not
rename the queue or let the filer choose a different member's work.

## Standing rules

- Wishes are leads, not strategy.
- Core changes need repeated evidence or a named high-consequence exception.
- Experiments stay contained until they earn promotion.
- Every bet starts with a baseline, a possible disproof, and a kill condition.
- Every result leaves behind something reusable or an honest negative record.
- Every long-lived ability has an upkeep owner and a retirement path.
- Member boundaries remain intact; unfinished siblings are finished rather than
  bypassed.
- The maintainer must not be the hidden brain.
- Real user outcomes beat internal activity counts.
- The roster may shrink when merging, narrowing, or retiring a member makes the
  collective stronger.
