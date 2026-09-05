# Decision: Emit the fixed-and-guarded result as a closed record

## Status

Proposed, 2026-09-05. Numberless under
[ADR-077](../ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md), which
assigns the number at merge.

## Context

Elenchus reproduces a failure, localises it to a mechanism, repairs the
mechanism and leaves a guard, then hands the result back as prose. The
`elenchus-fixed-and-guarded` Promise in
[the skill file](../../../plugins/hexaemeron/skills/elenchus/SKILL.md) already
names every part of that claim, and the skill already holds every part in order
to make it. Nothing survives the run in a form another program can read.

Once records exist, two things become expensive to reverse. The field set is
what every reader parses, so adding or removing a field afterwards splits the
population into records that carry it and records that do not. And the absence
of any key joining one record to another will read as an oversight to whoever
next wants to count recurrences, unless the reason is written down where the
shape is.

Both are settled here rather than in
[the study](../../elenchus-fixed-and-guarded-record/study.md), because a study
is read once and a record is read whenever somebody meets the schema.

## Decision

**One closed `elenchus-fixed-and-guarded/v1` object holds nine evidence
fields and a `schema` key, and refuses any other key.**

The nine are derived from the Promise's own two clauses and from nothing else.

The Evidence clause reads: "The reproduction command and output, causal
account, minimal case where useful, fix diff, detached-parent guard report,
fixed-tree report and both relevant suite results." That is seven fields:
`reproduction`, `causal_mechanism`, `minimal_case`, `repair`, `unfixed_parent`,
`fixed_tree` and `suites`.

The Boundary clause reads: "The result covers the reproduced failure and named
guard; it does not prove the surrounding system defect-free or turn an
inconclusive, zero-test or infrastructure-failed comparison into a guard." That
clause turns on which guard was named and on which of the four states the
comparison reached, which are `guard` and `verdict`.

| Field | Carries | Comes from |
| --- | --- | --- |
| `reproduction` | the exact command, and the digest and byte count of its observed output | the draft |
| `causal_mechanism` | the account as a mechanism, and the `path:line` where it starts | the draft |
| `minimal_case` | the reduced case, or `null` where none was useful | the draft |
| `repair` | the commit that repaired the mechanism, and the files it touched | the draft |
| `guard` | the regression test's file, and the test name inside it | the draft, with the file checked against the result's changed test files |
| `unfixed_parent` | the parent commit, and its normalised report counts | `git rev-parse <ref>^`, and the result's report |
| `fixed_tree` | the fixed commit, and its normalised report counts | the draft |
| `suites` | each suite command and its exit code | the draft |
| `verdict` | one of the four Elenchus states, and the runner-report account that produced it | the result's `status` and `detail`, untranslated |

**Every field is one Elenchus already holds.** The producer reads an operator
draft and an `elenchus.py --format json` result, and nothing else. The parent
commit is the single derivation: `elenchus.py` resolves it and compares against
it but prints `ref` rather than the parent, so the emitter re-derives it with
the same `git rev-parse <ref>^` call. Printing it from `elenchus.py` instead
would change the file this delivery is committed to leaving alone.

**The reproduction output is stored as a SHA-256 and a byte count, never as
bytes.** A stack trace can carry a credential, and a field that holds no bytes
gives one nowhere to land.

**The schema carries no cross-record identifier, and that absence is a
decision.** Nothing in the object may point at another record, and a record
carrying such a key is refused by the same rule that refuses any unknown key.
Two records naming a similar mechanism establish that two runs recorded a
similar mechanism, and nothing more. Recurrence is a claim about a population,
which needs an admission rule, a curator and a defined corpus; a record written
by whoever closed one failure has none of those. Making the join cheap here
would make the unwarranted claim cheap with it.

**A record establishes what the run recorded, and stops there.** It does not
prove the surrounding system free of defects, does not turn an inconclusive,
zero-test or infrastructure-failed comparison into a guard, does not certify
the repair beyond the reproduced failure and the named guard, and does not
authorise anything a Fiat receipt authorises. It is emitted; it is not
admitted, curated or resolved.

## Alternatives

- **A field set drawn from what a reader might want.** Rejected because the
  Promise is the only thing that says what the claim covers, and a field with
  no clause behind it has no evidence rule either.
- **A `recurrence_of` or `related` key.** Rejected for the reason above: the
  key would be filled by a producer with no way to establish the relation, and
  a reader would treat a filled key as a checked one.
- **Storing the reproduction output verbatim.** Rejected because the skill
  already forbids leaving instrumentation that prints a credential, and a
  record holding arbitrary command output reintroduces the same exposure at
  rest.
- **An open object that keeps unknown keys.** Rejected because a schema that
  accepts anything cannot refuse the two keys above, and because a reader
  cannot tell an extension from a typo.
- **Deferring the shape until a second producer exists.** Rejected because the
  first records would then be written under no shape at all, which is the split
  population this record exists to avoid.

## Consequences

A fixed-and-guarded result becomes machine-readable without any prose being
parsed, and the boundary travels inside the schema rather than only in a study.

A later producer that wants a field this set does not carry has to derive it
from the same two clauses or extend them deliberately, and cannot simply add a
key. That is the intended cost.

Anything wanting to relate two records must build the join outside the schema,
against a corpus with its own admission rule. Nothing here prevents that, and
nothing here pretends to have done it.
