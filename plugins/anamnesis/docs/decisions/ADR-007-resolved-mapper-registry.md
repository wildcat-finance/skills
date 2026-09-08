# ADR-007: Resolve the declared mapper through a registry keyed by name and version

## Status

Accepted, 2026-09-08.

## Context

A curation policy has always declared its mapper as a `{name, version}` object,
and until this run the declaration selected nothing. One parser ran whatever
the policy said. A policy naming a mapper that had never existed still curated,
still built a release, and still hashed that name into the release id, so every
assertion carried a mapper string no code had checked. The record said which
implementation had read the source, and it was not in a position to know.

The same parser could not tell whether the bytes it was handed were its format.
Read the three committed synopsis records with it and it returns 31 rounds and
0 findings. A whole corpus arrives empty, and nothing anywhere says the format
was wrong, so "this source held no findings" and "these bytes are not mine"
reach a reader as one observation.

Four constructions were scored in
`plugins/anamnesis/docs/resolved-mapper/design-evidence.json`, every cell a
report under `plugins/anamnesis/docs/resolved-mapper/reports/`. Three
candidates each fail one hard gate. `registry-and-synopsis-mapper` fails none
and is the sole survivor.

## Decision

Three decisions, taken together.

**The mapper is resolved through a registry keyed by name and version, and the
resolved entry is what an assertion records.** `MAPPER_REGISTRY` is a
module-level constant map from `(name, version)` to an implementation, wrapped
so that nothing can write to it after import. Lookup is exact: no fallback, no
default, no partial match. A declaration that resolves to nothing refuses
`A078` before any assertion, quarantine entry or release directory exists.
`_assertion` records `mapper_identity(resolved)`, which is the entry that ran,
never the object the policy declared. Both `curate` and `ingest` resolve before
they read, so neither entry point can reach a source through an implementation
the operator did not name.

**The mapper stays in the curation policy rather than moving per source.**
`per-source-mapper` would move the declaration into each admitted source in the
admission policy, which is the more general mechanism and the one a mixed
corpus will eventually need. It was rejected because `mapper` then leaves
`CURATION_POLICY_KEYS`, and `release_id` hashes the curation policy: the
measured `shipped-release-policies-changed` value is 2, recorded in
`plugins/anamnesis/docs/resolved-mapper/reports/per-source-mapper-shipped-release-policies-changed.json`.
Both shipped release ids move, and ADR-006, two `DEMONSTRATION.md` observation
lines and the front-door card all depend on them. The same criterion measures 0
for the selected candidate.

**The second corpus preserves the same findings the pilot preserves.** This
governs what the synopsis release may be cited for, and it is the decision most
likely to be misread. Its second home is the `scope.preserves` sentence in
`plugins/anamnesis/specimens/synopsis/curation-policy.json`, cited here rather
than restated so that one wording governs. That sentence is inside the release:
the curation policy is a release component whose bytes equal `manifest.policy`,
and it is hashed into the release id
`74c591e1f010868b3aadd048cdeb6db20df9ea4ac146b43f52c577a41dd6ac39`. Each
synopsis header carries a `source_sha256` equal to the digest the pilot's own
admission policy records for the same audit record, so the claim is mechanical
rather than asserted.

## Alternatives

| Criterion | `registry-and-synopsis-mapper` | `registry-and-red-team-mapper` | `registry-only` | `per-source-mapper` |
| --- | --- | --- | --- | --- |
| `unknown-mapper-refuses-at-curation` (gate, true) | true | true | true | true |
| `assertion-records-the-mapper-that-ran` (gate, true) | true | true | true | true |
| `second-format-declares-its-own-schema` (gate, true) | true | false | false | true |
| `shipped-release-policies-changed` (gate, 0) | 0 | 0 | 0 | 2 |
| `recovery-without-a-program-edit` (gate, true) | true | true | true | true |
| `second-corpus-rebuilds-deterministically` (gate, true) | true | pending | pending | pending |
| `second-format-findings-read` (metric, count) | 41 | 1 | 0 | 41 |
| `source-bytes-added` (metric, bytes) | 36455 | 3057 | 0 | 36455 |
| `acceptance-check-ms` (metric, milliseconds) | 1 | 1 | 1 | 1 |

**`registry-and-red-team-mapper`.** The same registry, with the second
implementation reading a `FINDING` to `END` key-value block and the third
corpus admitting the one preserved external red-team record. The producer is
genuinely independent and external, which is more than the selected candidate
offers. It fails `second-format-declares-its-own-schema`: the format declares
no schema or version anywhere in its bytes, so the mapper cannot check that
what it was handed is its format and fails open exactly as the first one did.
The producer also wrote no finding identifiers, so the mapper would have had to
assign them, and an identifier the mapper invented is not a preserved one.

**`registry-only`.** The registry and the refusal, with no second
implementation and no third corpus. Cheapest, adds no source bytes, and honest
about what it did not show. It fails `second-format-declares-its-own-schema`
because there is no second format at all, and it leaves the frontier open on
the same input, handing the next run an identical question.

**`per-source-mapper`.** Rejected on the measured value of 2, as the second
decision above records. It stays the right shape for a corpus holding two
producers' formats at once, and it is where the successor job starts.

## Consequences

An assertion's `mapper` object now means something a reader can check. It is
the registry entry that ran, so a release states which implementation produced
its records rather than repeating a policy's claim. Because a resolved entry
carries the same name and version the policy named, the recorded object is
byte-identical to what a resolving declaration wrote before, and both shipped
release ids stay where they were: the pilot at
`41d640fb168049d5061e12c9d7282dafad2266343eeb0be2a078db8797c0bfbf` and the
estate at `509239765f9fa2db782d3bc70fadea3b05411fc0638402fe5e0a43882f0063e3`.

Adding a format is now a program change and never a policy change. A policy can
select an implementation and can no longer name one, so an operator who wants a
new format needs a registry entry and the review that comes with it. That is
the trade: the declaration lost its reach, and in exchange a release built
under an unknown name refuses instead of shipping.

A mixed-format corpus is deferred. One curation policy still declares one
mapper, so a corpus whose sources come in two formats cannot be admitted until
the declaration moves per source, and that move costs the two shipped release
ids this decision protects.

Backtracking outcome: a measured bound of 4.6 milliseconds at the admission
policy's own byte cap. The five patterns the synopsis mapper runs,
`SYNOPSIS_HEADER`, `ROUND_HEADING`, `OTHER_HEADING`, `ROUND_FIELD` and
`FINDING_ROW`, were run over the widest cell any admitted source produces, 668
bytes on physical line 7 of
`plugins/anamnesis/specimens/synopsis/sources/pandects-audit-synopsis.md`, and
over all 434 cells the three admitted sources produce. Every pattern returns,
and the slowest, `FINDING_ROW`, takes about 13 microseconds on that cell on one
machine. Beyond the admitted corpus the same pattern was measured on a crafted
cell shaped `| <id> | <severity> | ` followed by spaces: 0.009 milliseconds at
1000 bytes, 0.055 at 10000, 0.661 at 100000 and 4.612 at 1000000, which is
`max_source_bytes` in all three shipped policies. Growth is linear across three
orders of magnitude. No budget is declared and none is implied: those figures
are recorded measurements, and study section 10's position is that this run
declares no performance budget.

The bound exists because the pattern was changed. As first written,
`FINDING_ROW` put a greedy `\s*` beside a lazy group at six places, so the
engine could try each way of splitting one span of whitespace across both. On
the same crafted cell it took 5.9 seconds at 2019 bytes and 45 seconds at 4019,
roughly eight times the work for twice the length, with or without a closing
pipe. A cell is bounded only by the physical line the source byte cap bounds,
`max_source_bytes` at 1000000 under a `MAX_SOURCE_BYTES_CEILING` of 8000000, so
that cap was not a bound on this: one crafted line inside an admitted source
would have held curation indefinitely. Every whitespace run in the pattern is
now possessive, which removes the ambiguity without changing what the pattern
accepts. All three specimens rebuild to the release ids they shipped with, so
the grammar both implementations share reads every admitted row exactly as
before. `mapper-backtracking` is closed by that change rather than carried, and
`tests/test_s13_guards.py` holds the structural property rather than a
duration, because a guard asserting a wall clock would be the budget this run
declines to declare.

The `<br>` split loses a producer cell that carries the separator rather than
shortening it. Neither fragment of such a cell matches the finding grammar,
which is anchored on the whole cell, so no partial or shortened row reaches a
record; the same holds for an unterminated row and for a truncated final line.
That is fail-closed on the byte level and silent at the corpus level: the row
is absent from the release, and nothing counts it. No admitted synopsis source
carries the separator inside a cell's content today, and neither does any of
the three audit records they were rendered from, so this is a property of the
format and not a defect the corpus currently reproduces.
