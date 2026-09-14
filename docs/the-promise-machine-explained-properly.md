# THE PROMISE MACHINE, EXPLAINED PROPERLY

This is the non-specialist guide to how **Wildcat Labs Skills, the Shoggoth,**
fits together. The repository is its installable distribution; the Promise
Machine, plugins, skills, workers, and upstream security siblings are its
working parts. This guide starts with a normal crypto R&D job and introduces
the internal vocabulary only when it becomes useful.

The normative rules live in [`PROMISE_MACHINE.md`](../PROMISE_MACHINE.md).
Where this guide and that contract differ, the contract wins.

## START WITH AN ORDINARY FAILURE

Imagine that a protocol test which used to pass against an archive RPC now
fails. The team wants to know whether the contract changed, the SDK changed,
the provider changed, or the original test depended on state nobody preserved.

An unbounded assistant might fetch whatever is available today, repair the
test, and write a confident explanation. That may produce working code, but it
does not leave enough evidence to tell which explanation was true.

The collective can split the job into narrower parts:

1. **Lazarus** captures the exact block, state, and RPC request-response pairs
   the test needs. It proves only the relations its verifier supports and marks
   the rest as recorded.
2. **Elenchus** reproduces the failure, reduces it, fixes the cause, and leaves
   a guard that is red on the parent and green with the fix.
3. **Ariadne** can bind the released fixture or patch digest to the evidence
   behind it.
4. **Fiat**, if a person explicitly asked for a full delivery, can control the
   study, runbook, implementation, audit, prose, push, and integration phases.

At every hand-off, the next specialist receives the claim that was actually
established. “This response was recorded” does not become “this value was
proved.” “This regression test passes” does not become “the protocol is safe.”

That preservation of meaning is the Promise Machine.

## WHAT A PROMISE CONTAINS

A promise is not a prediction and it is not a claim that an agent is generally
reliable. It is the contract for one operation.

Every first-party promise answers the same questions:

| Field | Question | Why it is present |
| --- | --- | --- |
| Promise | What does success establish? | Names the exact result. |
| Evidence | Which command, input, result, test, proof, or observation backs it? | Names the basis for that result. |
| Evidence classes | Was the result checked, recomputed, proved, measured, recorded, attested, inferred, or left unknown? | Prevents one relation from being described as a stronger one. |
| Boundary | What nearby conclusion is tempting but unsupported? | Stops the result expanding beyond its evidence. |
| Authorises | What may happen next? | Names the permitted transition. |
| Consequence | How consequential is that next action? | Sets the evidence strength required for it. |
| Refuses | What stops if the evidence is absent or wrong? | Defines the local failure. |
| Recovery | What can still be inspected, repaired, rerun, rolled back, or exited safely? | Keeps useful recovery paths open. |
| Exceptions | Is any attributed, scoped, recorded waiver permitted? | Makes a permitted waiver explicit. |

The stable promise id lets another tool refer to this exact contract without
copying or paraphrasing it.

## EVIDENCE WORDS HAVE NARROW MEANINGS

The evidence classes describe relations. They are not a league table.

| Word | What it means here | What it does not mean |
| --- | --- | --- |
| `checked` | A named deterministic rule or schema accepted the subject. | Everything about the subject is correct. |
| `recomputed` | A result was derived again from named inputs and a named method. | The inputs or method are authoritative. |
| `proved` | A named formal, cryptographic, or defined proof relation accepted. | Any neighbouring fact was proved. |
| `measured` | A value was observed under a recorded method and environment. | The value is universal or caused by the change. |
| `recorded` | Exact bytes or a statement were preserved from an identified source. | The source was truthful. |
| `attested` | An identified actor or system made the statement. | The statement is independently true. |
| `inferred` | A named rule produced a conclusion from named evidence. | The conclusion was directly observed. |
| `unknown` | The matter was not established. | Anything positive may proceed. |

This distinction matters in crypto work. A provider response can be recorded
without being proved. A storage value can be proved against a named state root
without proving that the provider chose the canonical block. A security tool
can check a bounded property without proving that a contract has no bugs.

## CONSEQUENCE CHANGES THE GATE

The contract uses four consequence levels for the transition after a result:

| Level | What happens next | Minimum discipline |
| --- | --- | --- |
| 0 | A response or presentation | Preserve scope, content, and uncertainty. |
| 1 | A derived artefact | Validate its shape, provenance, and visible gaps. |
| 2 | A repository or durable-data change | Run tests, preserve negative evidence, and keep recovery possible. |
| 3 | Publication, deployment, external action, or a security or financial conclusion | Fail closed with recorded authority and independently inspectable evidence. |

The level belongs to the action, not to the personality of the skill. One
skill can have separate operations at different levels.

A level-3 action cannot rest only on model judgement, chat memory, or an
unchecked receipt. This is why a repository change that looks finished can
still stop before publication.

## COMPOSITION KEEPS THE CAVEATS

Skills are designed to hand work to siblings, but composition is where
overclaiming often happens. The consumer must carry forward the producer,
subject, scope, evidence class, time boundary, conflicts, unknowns, and any
transformation.

Some current examples:

- Lemma chunks remain source-linked retrieval material. They do not establish
  that an answer based on them is true.
- Lazarus RPC responses remain recorded unless a named proof check established
  a narrower proved relation.
- Berean citation and evaluation records establish their release gates. They
  do not establish general model quality or universal factual truth.
- Janus stays bound to one named host adapter, manifest, recorder, and bounded
  search. It does not establish hook safety across every execution or host.
- Ariadne binds an artefact digest to declared evidence. Without a separate
  signature verifier it does not authenticate the publisher.
- Synkrisis recomputes a checked cohort, bounded findings, and a report. It
  does not turn repeated observations into cause or permission to act.

A consumer may add evidence under a separate identity.
It may not rename the old evidence into something stronger.

## REFUSAL SHOULD BE LOCAL AND USEFUL

When evidence is missing, stale, malformed, or about the wrong subject, the
dependent transition stops. The whole system should not become unusable.

A useful refusal names:

- the promise that failed;
- the field or evidence at fault;
- the blocked action;
- the consequence level; and
- the recovery action.

Inspection, diagnosis, repair, rerun, rollback, and safe exit remain available
unless the promise explains why one of them cannot exist. A checker must never
delete or rewrite the failing source merely to make its own report pass.

## WHAT THE REPOSITORY CHECKS

The Promise Machine's structural checks discover the governed skill universe
from manifests and canonical skill paths. They reject missing declarations,
duplicate identities, uncovered skills, divergent installation copies, and
unbound vendored instructions. They also check the shapes of the Promise
Machine's own operations for run observations, contributor ranking, router
selection, first-party licensing, and the bounded agent-instruction prototype
whose public contract is
[`agent-instruction-language-v1.md`](agent-instruction-language-v1.md).

This is a wiring and contract check. Behavioural evidence still comes from the
named domain tests, broken specimens, proof checks, measurements, and manual
demonstrations. Green wiring cannot prove a false domain claim true.

## THE SPECIALISTS

The current distribution has <!-- front-door:count key="plugins" -->18 plugins
and <!-- front-door:count key="governed" -->27 governed first-party skills;
both numbers are derived from the tree when this page is checked. They are
easier to understand as parts of a few R&D paths than as one long alphabetical
list.

### PREPARING AND PRESERVING EVIDENCE

- **Horos** bounds initial repository reading.
- **Lemma** prepares source-linked document or Solidity chunks.
- **Lazarus** preserves finite historical Ethereum state and exact RPC traffic.
- **Ariadne** binds release digests to evidence statements.

### BUILDING AND COMPARING CHECKABLE RELEASES

- **Berean** evaluates protocol-agent releases against pinned documents and
  block-bound chain reads.
- **Synkrisis** compares declared observations from several runs under one
  comparison policy and bounded rule catalogue.

### PROTOCOL BEHAVIOUR AND CONTRACT SAFETY

- **Janus** checks host-specific hook-effect boundaries.
- **Pandects** supplies executable credit laws with broken specimens.
- **Hermes** performs measured Solidity gas work.
- **Homologia** is the planned integer-parity specialist, but today it is a
  refusing scaffold rather than an operational comparison tool.
- The unchanged upstream **X-Ray**, **Solidity Auditor**, **Fizz**, **Fizz
  Convert**, and **Fizz Sync** skills cover audit preparation, contract review,
  and stateful fuzz harnesses.

### LENDING RECORDS AND DOSSIERS

- **Alexandria** preserves raw lending inputs.
- **Tabularium** maps supported venue records into reproducible events.
- **Probitas** assembles a declared-address dossier without making the lending
  decision.

### DELIVERY, ENGINEERING, AND COMMUNICATION

- **Fiat** controls the full repository delivery.
- **Protasis**, **Phylax**, **Ephoros**, **Metron**, **Elenchus**, and
  **Hypomnema** govern readiness, off-chain security, observability,
  non-gas performance, failure reduction, and durable explanation.
- **Imprimatur**, **Vulgate**, **Sapheneia**, and **Brevitas** diagnose, rewrite,
  shape, and constrain prose without owning its facts.
- **Kronos** can rank eligible held frontier work and dispatch it through Fiat
  when explicitly asked.

The root [`README.md`](../README.md) gives examples and current gaps for these
groups. [`FUTUREPROOFING.md`](../FUTUREPROOFING.md) separates shipped behaviour
from plausible final forms member by member.

## HEXAEMERON AND FIAT

Hexaemeron is the delivery plugin. Fiat is its controller. Fiat is not an
always-on mode and the word “deliver” is not enough to activate it. A person
must explicitly ask to start, run, resume, recover, or continue Fiat or
Hexaemeron.

A normal run moves through:

```text
study -> runbook -> implementation step(s) -> audit round(s) -> prose -> push -> integration
```

The exact path can include amendments, deferrals, stacked pull requests, and
recovery. Durable state and receipts, rather than chat, decide where the run is.

Four worker roles may execute bounded packets:

- **Surveyor** writes one source-bound study.
- **Mason** implements and tests one exact runbook step.
- **Warden** performs one audit round and returns preserved findings, fixes,
  and an Elenchus verdict.
- **Scribe** performs one bounded prose pass.

They cannot advance Fiat, receipt their own work, widen their packet, or claim
publication authority. Fiat may perform a packet inline when a separate worker
is unavailable.

[`fiat-in-plain-english.md`](./fiat-in-plain-english.md) explains the run without
the controller vocabulary. The exact controller contract remains the Fiat
`SKILL.md`.

## THE ROUTER

Portable agents discover one host-neutral `promise-machine` router. The router
first determines whether it is in a full checkout or an isolated installed
copy, loads the shared contract and plugin runtime, and then selects the
narrowest canonical skill that owns the request.

The router does no domain work. Where two of them appear to match, it reads the
boundary that separates them. If the repository defines no owner, it stops at
inspection and reports the uncovered boundary instead of inventing a general
capability.

## WHAT “DONE” MEANS

For a single operation, done means the named promise passed and the result
contains its evidence, boundary, and recovery information.

For a Fiat delivery, done means the controller has accepted every required
receipt and the authorised integration conditions hold. A convincing chat
summary, a green test from an older tree, or a branch that merely contains code
is not a substitute.

For the collective as a research project, there is no final “all done.” The
useful standard is smaller: each claimed capability should have a real user, a
finite checked operation, a hostile or broken specimen, a visible frontier,
and a reason to keep maintaining it. Where those are missing, the public prose
should say so.

## CURRENT SOURCE BOUNDARY

This guide describes the repository snapshot dated 31 August 2026. Counts,
frontiers, and examples can change. The canonical current sources are:

- [`SHOGGOTH.md`](../SHOGGOTH.md) for collective identity and roster shape;
- [`PROMISE_MACHINE.md`](../PROMISE_MACHINE.md) for evidence and transition
  law;
- each plugin's `AGENTS.md` for routing and runtime boundaries;
- each canonical `SKILL.md` for the operation contract; and
- each `EVOLUTION.md` for the accepted frontier and next evidenced job.
