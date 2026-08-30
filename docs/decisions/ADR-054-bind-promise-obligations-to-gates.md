# ADR-054: Bind explicit Promise Machine obligations to production gates

## Status

Accepted, 2026-08-30. This record fixes the framework rule selected for issue
[#884](https://github.com/wildcat-finance/skills/issues/884). ADR-054 was free
on the pinned implementation branch when this record was written.

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

The accepted study and runbook live under
`docs/promise-machine/obligation-gates/`. They are the build contract for this
framework change; this ADR is the standing reason for the interface choice.

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
