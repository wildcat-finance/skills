# ADR-066: Bind explicit Promise Machine obligations to production gates

## Status

Accepted, 2026-08-30; renumbered 2026-08-31. This record fixes the framework
rule selected for issue
[#884](https://github.com/wildcat-finance/skills/issues/884). ADR-054 was free
on the pinned implementation branch when this record was written. The default
branch later assigned ADR-054 through ADR-061 to other decisions, and a
receipted Step 3 amendment moved this unchanged decision to ADR-062. The
default branch then assigned ADR-062 through ADR-065 as well, so the receipted
Step 4 amendments move the standing identifier to ADR-066 without changing
the decision.

## Context

`PROMISE_MACHINE.md` states obligations about evidence, transitions,
refusals, exceptions, composition, and identity. The checker can enforce a
rule without exposing which clause it serves, while the law can gain a
normative clause without a test noticing that no gate serves it. A registry
that defines its own universe does not close either omission.

The root law is the authored source. Its prose must remain readable, generated
copies must remain byte-identical, and the checker must stay offline and use
the standard library. Domain-native result formats also remain in place; this
decision is not a universal result envelope or a second policy language.

## Decision

An executable root-law clause uses this closed authoring grammar:

```markdown
<!-- promise-machine-obligation: id=stable-kebab-id -->
> Obligation: The normative clause.
```

The checker discovers these clauses from the law. A marker is valid only when
it has one stable id and owns the next explicit clause. An explicit clause
without a marker, an orphan or malformed marker, and a repeated id all refuse.

`tests/promise_machine_obligations.json` maps each discovered id to exactly one
marked-clause digest, production gate selector, negative specimen, expected
stable finding code, consequence, blocked transition, and recovery.
Registry-only and marker-only ids refuse. The clause digest prevents valid
markers from exchanging clauses. The checker's closed selector registry
independently binds each stable id to its one selector and finding code, so
rows cannot exchange or share a gate. A specimen is bounded,
duplicate-key-rejecting JSON at a confined fixed path. It applies one exact
in-memory replacement to the law and runs the same production law validator
used by `check`; it passes only when that mutation returns its one expected
finding. The specimen does not execute code, write the law, fetch data, or
define a fixture-only validator.

Step 1 converts the structural clauses whose production gates already exist.
It does not claim that every natural-language rule in the law has moved into
the explicit grammar. The generated-copy marker and law field inventory do not
claim byte equality across copies or per-skill declaration completeness; those
broader rules retain their existing prose until their own evaluators join.
Each later semantic step must add its marker, registry row, real selector, and
red specimen atomically. A semantic rule is not counted merely because a
fixture mentions it.

Step 2 adds one closed transition record for consequence evaluation. Levels
zero through two require successively different exact evidence roles. Level
three requires the complete level-two set plus a digest-bound authority record
and independently inspectable evidence, so replaying a level-two result cannot
cross a level-three gate. `unknown`, `not-run`, missing and stale evidence are
visible states but never satisfying states. A transition also resolves a
digest-bound declaration for the same promise, gate, consequence, subject,
scope and action before it can pass.

An exception is a digest-bound record rather than a list of labels. It resolves
the authority identity, promise and gate, subject, scope, durable reason,
expiry rule, explicit revocation state and recovery. The transition supplies
the recorded evaluation time; an absent, mismatched, expired or revoked record
refuses. The exception does not bypass missing evidence or strengthen an
evidence class.

Every emitted finding is adapted to one actionable refusal shape before either
renderer sees it. It carries a promise id, an obligation id when known, finding
code, consequence, blocked transition and recovery. Text and canonical JSON
therefore derive from the same object. The core checker also scans its own
Python syntax for network, credential, shell, child-process and dynamic-code
paths. Direct builtins access and dynamic access through `os`, `Path` and
`tempfile` fail closed, apart from the two named OS flag lookups used by
confined reads. A test runs the core check with network and child-process
constructors, string and byte environment helpers, and mutation primitives
denied. Its open wrappers reject write-capable modes and reads outside the
checkout. Neither guard executes an evidence command.

The accepted study and runbook live under
`docs/promise-machine/obligation-gates/`. They are the build contract for this
framework change; this ADR is the standing reason for the interface choice.

Promise ids are also an append-only interface. The committed
`tests/promise_machine_id_history.json` starts at Fiat entry commit
`7e97b5195d5b0e43146b4200f26cd41b89003413`. Its entry count and canonical
digest bind all 80 original ids, paths, and semantic digests. A semantic
digest covers the nine authored Promise Machine fields. Each id has one row
with its entry snapshot, current snapshot, and one continuity action:
`unchanged`, `introduced`, `retired`, `renamed`, or `split`.

An unchanged row must preserve its entry path and semantic digest. Retirement
has no successor. Rename has one active successor with the same semantic
digest. Split has at least two active successors. Both sides of every rename
or split edge name each other. Every current declaration has exactly one
active row, and every active row resolves to exactly one current declaration.
The offline core checks this file without reading Git history or running a
command. Changing the entry anchor is therefore an explicit reviewed change,
not a side effect of checking the working tree.

Eleven prompt or vendored promises use one further closed gate,
`labelled-case-classification`. Their coverage rows name a full model identity,
one prompt request, one source corpus, one run record, and the literal boundary
`required-separately`. The two corpora own only the request and five labelled
P/M/S/O/R scenarios for each promise. They do not carry a model result.

`tests/promise_evaluation_driver.py` stops at the model boundary. `emit` reads
only bounded repository inputs, writes one isolated prompt per promise, and
writes the manifest last. The manifest binds the prompt template, corpus,
complete input tree, exact case set, and every prompt byte. An operator invokes
one fresh model context per prompt and preserves each raw response as a string.
`tally` accepts only the exact eleven answers and the closed
`accept`/`refuse`/`recover` vocabulary, then records the full model identity,
date, input digests, raw-answer byte identities, and outcome counts. `verify`
recomputes that record. None of the three commands opens a socket, reads a
credential, invokes a model, or starts a child process.

The driver accepts only the request-only schema, the exact promise set assigned
to each corpus, and one full model and run identity across the eleven coverage
rows. Each template placeholder appears exactly once. Rendering replaces only
tokens already present in that template, so braces supplied by a request remain
data instead of starting a second template pass.

Repository and answer reads walk descriptor-relative paths without following
links and open the final file in non-blocking mode. They require a stable
regular-file identity before and after each bounded read. Packet and run-record
writes use exclusive descriptor-relative creation. A platform without those
controls refuses instead of weakening the boundary.

The core `evaluation` check independently reads the committed answer sheet and
run record, recomputes the source-tree and corpus digests, grades all 55
outcomes, and refuses missing, partial, duplicate, extra, edited, stale,
symlinked, `not-run`, or malformed evidence under PM107 through PM110. The run
must say `domain_evidence: not-supplied`. A perfect grade satisfies only the
labelled-case gate: it is not evidence that Fizz, Fizz Convert, Fizz Sync,
X-Ray, Solidity Auditor, Hypomnema, Vulgate, Kronos, or Sapheneia performed the
operation named by its promise. Those transitions still require their native
records and authority.

## Alternatives

**Treat normative words as the obligation grammar.** Rejected. Words such as
“must”, “never”, and “refuses” occur in tables, promise examples, boundaries,
and explanations. A prose heuristic would move the discovered universe when
an editor changes register rather than meaning.

**Let the registry define the obligation universe.** Rejected. Deleting a row
would delete both the claimed obligation and its coverage, leaving the checker
green. Discovery belongs to the authored law and the registry must be its
bijection.

**Accept a selector name and a test path without running the specimen.**
Rejected. That proves strings resolve, not that the selected gate refuses its
hostile neighbour. A deleted or no-op gate must make the retained row fail.

**Use a fixture-only validator or external policy engine.** Rejected. A second
validator can agree with its own specimen while production accepts the bad
law, and an external engine adds a dependency and a second expression of the
same rules.

**Read Git history during every core check.** Rejected. A checkout may be
shallow or packaged without its object database, and the core is required to
remain offline and child-process free. The committed entry anchor and explicit
continuity graph preserve the comparison boundary instead.

**Let the evaluation driver call the model.** Rejected. That would mix network,
credential, process, provider, and retry policy into the deterministic evidence
tool. The driver emits and verifies bytes; the operator owns the isolated model
invocations.

**Use a correct model classification as the owning skill's result.** Rejected.
The classifier sees authored scenarios, not a campaign, audit, conversion,
sync, pre-audit, placement review, rewrite comparison, user authority record,
or active session. The grade can test the promise boundary without supplying
the evidence the boundary demands.

## Consequences

A reader can move from an explicit clause to the gate, red specimen,
consequence, blocked transition, and recovery that hold it. Adding one side of
the relation without the other stops the root check by obligation id. Removing
a production gate while its row remains also stops because the specimen no
longer produces its expected finding.

The explicit grammar is an interface. Moving, splitting, or retiring a marked
clause needs the same atomic treatment as changing its gate. The first step
adds only structural clauses; later runbook steps bear the migration cost for
semantic obligations and may not cite this scaffold as proof that those
semantics already run.

The registry and fixtures become dependencies of the portable Promise Machine
runtime. Generated plugin law copies and the portable runtime are regenerated
from authored inputs; they are never edited by hand.

Removing a promise id now requires a retained retirement, rename, or split
row. Reusing one unchanged id for different semantics fails even when its
current digest is updated in the history file. A newly introduced id is
visible as such and cannot silently replace an entry id.
