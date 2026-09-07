# ADR-006: Declare the corpus scope in the release policy

## Status

Accepted, 2026-09-07.

## Context

The pilot's record bound sat in `anamnesis.py`: `seed_scope` refused `A073`
outside 25 to 50 records, and nothing in a release said what the corpus was
meant to preserve. A release id covered the curation policy, the source digests
and the graph, so two releases with the same sources under the same policy had
the same id, but the id said nothing about scope because no document declared
one. A second corpus of 17 records could not be admitted at all, and the only
remedy was to edit the program.

Two facts were already true. `verify_release` recomputes the release id from
the release's own bytes, and the first study's `partial-release` and
`source-byte-drift` controls rest on that. The curation policy is a release
component whose bytes equal `manifest.policy`; the admission policy is not in
the release.

## Decision

`scope` is a required closed object of the curation policy, with `id`,
`preserves`, `sources` and `records` (`minimum`, `maximum`) and nothing else.
`check_scope` runs where the curation policy and the admission result meet
(`admit-seed`, `curate`, `release` and the rebuild behind `verify-rebuild` and
`demo`) and refuses `A074` for an admitted source outside the scope, `A075` for
a scope source that was not admitted, and `A073` for a record count outside the
declared bounds. `verify_release` refuses `A077` when the manifest's sources
differ from the scope its policy declares. A malformed scope refuses `A076`,
and `seed_scope` is removed.

## Alternatives

Four candidates were scored in the corpus-scope design record
(`plugins/anamnesis/docs/corpus-scope/design-evidence.json`) over eight
criteria. Gates read `equals`; metrics were never compared because the frontier
had one member.

| Criterion | `release-policy-scope` | `admission-policy-scope` | `permanent-seed-record` | `widen-constant` |
| --- | --- | --- | --- | --- |
| `release-id-declared-function` (gate, true) | true | true | false | false |
| `scope-recorded-in-release` (gate, true) | true | false | false | false |
| `estate-findings-admissible-without-widening` (gate, true) | true | true | false | false |
| `foreign-ledgers-touched` (gate, 0) | 0 | 0 | 0 | 0 |
| `pilot-artefacts-rebuilt` (metric, count) | 7 | 6 | 0 | 1 |
| `policy-bytes-added` (metric, bytes) | 340 | 220 | 0 | 0 |
| `acceptance-check-ms` (metric, milliseconds) | 35 | 35 | 0 | 19 |
| `scope-recovery-by-policy-edit` (gate, true) | true | true | false | false |

**`admission-policy-scope`.** Put the scope in the admission policy and extend
the release id to hash that policy's canonical bytes. It passed every gate but
`scope-recorded-in-release`: the admission policy is not a release component,
so a release id that depended on it could not be recomputed from the release
alone, and the pilot's admitted events would change with the policy digest. It
also adds fewer bytes (220 against 340) and rebuilds one file fewer, and neither
figure was reached because the gate had already failed.

**`permanent-seed-record`.** Change no code and record the 41-record seed as
the permanent shape of the corpus. It failed four gates:
`release-id-declared-function`, `scope-recorded-in-release`,
`estate-findings-admissible-without-widening` and
`scope-recovery-by-policy-edit`. `seed_scope(17)` refuses the second corpus,
and the bound stays where only a program edit can move it.

**`widen-constant`.** Keep `seed_scope` and widen it, or add a second constant
for the second corpus. It failed the same four gates: the corpus becomes
admissible while the release id still says nothing about scope, and every later
corpus needs another edit to the program.

## Consequences

The pilot's curation policy moves to `curation-2026-09-06`, because a policy
with new bytes is a new policy, and its release id moves with it; the release
manifest, its policy component and its relations change, and the four
components that carry no policy version stay byte-identical. The demonstration
ledger is re-pinned to the new program digest and release id without moving the
demo frontier.

Every corpus must now declare what it preserves before it can be built, and a
release carries that declaration inside its own bytes, so a reader can check the
manifest's sources against the scope without any document outside the release.

The admission policy stays outside the release id. Admission events, the
sources and the admission policy digest do not change when a scope is declared
or amended.

A scope refusal is recovered by editing a policy file, never `anamnesis.py`;
the bounds and the source list live in the policy, and the program holds no
number of its own.
