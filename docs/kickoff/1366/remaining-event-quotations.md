# Distinct event quotations

## Behavior

Step 2 of #1366 preserves each Solidity event declaration's owner and exact
quotation. The retained public guard failed one of four tests on the
unfixed parent, with no errors or skips. The schema had treated declarations
under different owners as duplicate content after whitespace normalization.

Events now keep separate chunks, including identical declarations and unequal
quotations whose comment-stripped model text matches. Each records the UTF-8
byte start and length of its complete quotation. Validation checks owner,
signature, path, ID and span consistency; repeated spans, duplicate IDs and
same-owner duplicate content refuse. Compilation-unit merging also refuses a
changed event location. Non-event and Markdown duplicate rules remain unchanged.
The selected design and rejected alternatives remain in Lemma's
[version ledger](../../../plugins/lemma/skills/lemma/EVOLUTION.md).

## Evidence

The public reduction and four retained Maple examples passed the production CLI
using `0.6.11+commit.5ef660b1`. Their five outputs contain 1,649 chunks and 142
events; all 142 event quotations matched the recorded input byte spans. The
compiler artifact SHA-256 is
`9778e4a7667d5fd7632caf3ef3791d390a7cc217f94f96e919a31e3be332386a`.
The private execution record is
`.hexaemeron/evidence/step-2-mason/real-cases.json`, SHA-256
`dff954921d68bb0f354152e57fe3c5ae2c761dee918f2852b51c4f96ab1a6b6f`.
It retains input/output digests, counts, exit codes and measured durations.
These five observations establish no performance improvement or whole-corpus
conformance.

The event suite passed 109 tests with no failures, errors or skips. The actual
0.8.25 compiler suite passed 201 assertions; Markdown passed 190. Hostile cases
cover missing and forged owner fields, invalid spans, repeated identities,
namespace consistency, source-path changes and refusal preserving existing
output files. The compiler fixtures also exercise anonymous and overloaded
events across all 20 retained builds.

## Limits

Direct schema validation checks metadata consistency; it cannot authenticate
source bytes without the source input. Older event corpora without spans need a
rebuild to meet the current schema. This change belongs to the run's
`lemma-v0.5.1` generation. The accepted Wildcat archive remains prior
inherited evidence. Input preparation and complete remaining-venue conformance
remain Steps 3 and 4. #1872's capture verification is unchanged, and the separate
Euler set-164 custody gap is still unresolved.
