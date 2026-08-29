# Alexandria release-statement study

Assumptions, unless corrected:

- Issue [#407](https://github.com/wildcat-finance/skills/issues/407) is an ordinary
  `wish`. It does not complete, replace, increment, or otherwise alter the held
  `usdc-interval-collector` frontier in
  `plugins/alexandria/skills/alexandria/EVOLUTION.md`.
- The build starts from `main` at
  `58b7dcd1004bf8e6b0cf517bbcc778789e2c43ff`.
- "Ariadne-ready" means a conforming in-toto Statement v1 that Ariadne can
  parse, inspect, and run through its core gates. It does not mean that Ariadne
  already registers the Alexandria predicate or that its predicate-owned gates
  pass.
- The output is unsigned. Cosign remains the signing and signature-verification
  boundary; no key, signer identity, or authenticated publisher claim enters
  Alexandria.
- One command, its schema, focused tests, and operator prose form one shippable
  module. Splitting the emitter from its public contract would leave neither a
  useful green intermediate state nor an independently useful capability.

## 1. Problem statement

Add an Alexandria command that reads an existing raw or derived release,
verifies it offline, and atomically emits a deterministic in-toto Statement v1.
The statement must bind the logical `release_id` and every declared component
digest as subjects. Its Alexandria predicate must preserve each capture's exact
scope, coverage status and counts, unsupported collections, and declared gaps.

A working prototype is proved by a repository fixture through this path:

1. `python3 plugins/alexandria/scripts/alexandria.py statement <release> --output <statement.json>` exits zero after offline release verification.
2. Repeating the command over unchanged input emits byte-identical JSON.
3. The subject set is exactly the release SHA-256 plus the manifest component
   SHA-256 values, without truncation, prefix confusion, invention, or omission.
4. The predicate bytes reproduce the manifest's capture scope, coverage counts,
   unsupported collections, and gaps, and a tampered or invalid release emits
   nothing.
5. `python3 plugins/ariadne/scripts/ariadne.py inspect <statement.json>` parses
   the statement, reports the predicate as unregistered and the signature as
   unchecked, while `verify` keeps predicate-owned gates 2 and 5 visibly
   unchecked rather than calling them passed.

The user is a release operator who needs portable evidence bytes that can later
be signed outside Alexandria or consumed by Ariadne without translating an
Alexandria manifest into a lossy single-interval dataset claim.

## 2. Prior art

### Current Alexandria surface

`plugins/alexandria/scripts/alexandria.py` exposes `ingest`, `verify`, `derive`,
`index`, and `query`; there is no statement command or equivalent helper.
`plugins/alexandria/scripts/alexandria_lib/release.py` already owns canonical
manifest parsing, offline verification, logical release identity, component
digests, confined paths, duplicate-key refusal, size bounds, and atomic release
installation. `plugins/alexandria/tests/test_release.py` proves that
`release_id` is the canonical manifest-content digest and that component bytes,
object paths, coverage counts, and the release tree are checked again during
verification. The emitter must consume those established results instead of
building a second verifier.

`plugins/alexandria/docs/study.md` lines 185-192 and 282-294 deferred this exact
join: Ariadne can bind an Alexandria manifest and components, but neither tool
authenticates a publisher or proves provider completeness or canonical-chain
membership. The same study sketches an Alexandria predicate carrying the
harvester revision, mappings, inputs, outputs, and validation results. Issue
#407 narrows this generation to release and component subjects plus capture
scope, coverage counts, and gaps.

### Ariadne and the standards boundary

`plugins/ariadne/skills/ariadne/SKILL.md` and
`plugins/ariadne/scripts/ariadne_lib/statement.py` implement in-toto Statement
v1 and optional DSSE reading. Ariadne matches subjects by digest, never by name;
rejects malformed statement and ResourceDescriptor shapes; and neither creates
nor verifies signatures. Unknown predicate types still receive the core gates,
with gates 2 and 5 reported unchecked.

Ariadne's registered
`https://ariadne.wildcat.finance/dataset/v1` predicate is close but not
isomorphic. It describes one ordered numeric interval and structured interval
gaps, plus producer inputs and per-file record counts. One Alexandria release
can contain multiple captures with different scope kinds, chains, subjects,
block ranges or snapshots, finality declarations, and free-form declared gaps.
Flattening those into one dataset interval would either discard evidence or
invent equivalence. Issue #408 explicitly directs Tabularium to use or extend
the dataset predicate; issue #407 instead points back to the deferred
Alexandria predicate. That contrast is carried as a design constraint, not
silently harmonised away.

The external wire standards are in-toto Attestation Framework Statement v1 and
its ResourceDescriptor digest form. DSSE and cosign are downstream envelopes
and signing operations, not output of this command.

### Last two merged Alexandria changes

- [PR #62](https://github.com/wildcat-finance/skills/pull/62), merged as
  `de8228be2d2c37225512c2530a295970e3ac1f69`, published Alexandria's raw
  digest-bound archive, derived views, disposable index, demonstration, and
  Compound specification. Its stated evidence boundary was local bytes,
  declared scope, coverage, and derived-row agreement; publisher identity,
  provider completeness, canonical-chain inclusion, a production harvester,
  and a Compound mapping were not claimed. All those limits remain.
- [PR #69](https://github.com/wildcat-finance/skills/pull/69), merged as
  `25b38af4a1663e834db87afc4166cca580804449`, applied four Compound v3 Phase 0
  audit rounds. Its final round was clean; it reported 255 Alexandria tests and
  134 Tabularium tests passing. This wish does not reopen the fixed-method proof
  or turn it into the held interval collector.

### Audit record reading

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited zero from the complete target tree before this study. Alexandria has no
plugin-local `audit/AUDIT.md`; its applicable historical record is the shared
`audit/AUDIT.md`, read through the current `audit/AUDIT_SYNOPSIS.md`. The
Compound v3 Phase 0 record carries `S1-R1-01`, `S1-R1-02`, `S1-R1-03`, and
`S1-R1-04`, all fixed in round 1; rounds 2 through 4 were clean and every round
records no leads not pursued. Every one of those legacy rounds reports
`[missing legacy field: audit-schema]`, `[missing legacy field: covered]`,
`[missing legacy field: not-checked]`, and
`[missing legacy field: elenchus-verdict]`; those fields remain unknown rather
than inferred.

The Ariadne sibling record was read through current
`plugins/ariadne/audit/AUDIT_SYNOPSIS.md`. Its findings
`S1-R1-01` through `S1-R1-04`, `S1-R2-01` through `S1-R2-04`, `S1-R3-01`
through `S1-R3-02`, `S1-R4-01` through `S1-R4-02`, `S2-R1-01` through
`S2-R1-03`, `S2-R2-01` through `S2-R2-03`, `S2-R3-01` through `S2-R3-02`,
`S3-R1-01` through `S3-R1-03`, `S3-R2-01` through `S3-R2-03`, `S3-R3-01`,
`S3-R4-01`, `S4-R1-01` through `S4-R1-03`, `S4-R2-01` through `S4-R2-04`,
`S4-R3-01` through `S4-R3-02`, `S5-R1-01` through `S5-R1-04`, and
`S5-R2-01` through `S5-R2-02` are all fixed; the clean closing rounds carry no
new finding. Applicable open leads remain visible: core gates do not eliminate
homoglyph keys or prove which of several same-digest subjects a prose claim
intended; replay is not a sandbox; and short secret-like strings may evade
Ariadne's capture scrubber. This command neither invokes replay nor copies
commands, credentials, or source locators into its output. All Ariadne rounds
carry the same four missing legacy fields named above, so their covered,
not-checked, and Elenchus verdict fields remain unknown.

The Tabularium sibling record was read through current
`plugins/tabularium/audit/AUDIT_SYNOPSIS.md`. Findings `E1-R1-01` through
`E1-R1-03`, `E1-R2-01`, `E1-R3-01` through `E1-R3-02`, `E1-R4-01`,
`S2-R1-01`, `S3-R1-01`, `S3-R2-01` through `S3-R2-02`, and `S4-R1-01` are
fixed; its remaining listed rounds are clean and all say no leads were left
unpursued. Its rounds also carry the same four missing legacy fields, which
remain unknown. No Tabularium implementation changes are needed: it consumes
Alexandria releases and owns interpretation, while this statement preserves
the Alexandria manifest's declared evidence without assigning new meaning.

## 3. Constraints and non-goals

The implementation stays in Python's standard library and under
`plugins/alexandria/`. It must accept both raw and derived
`alexandria-release/v1` directories already accepted by `verify`, reach no
network, not mutate the release, bound its reads through the existing verifier,
and install the output through a sibling temporary file followed by an atomic
replace. It must refuse an output inside the release tree because adding the
statement there would make the verified release contain an undeclared entry.

The public predicate type is
`https://ariadne.wildcat.finance/alexandria-release/v1`. It remains
unregistered in Ariadne in this issue. The predicate carries the release
format and digest, component names, paths, media types, byte counts and digests,
the exact manifest capture scope and coverage declarations, one passed claim
that names the verified logical release digest, and an explicit empty
`commands` list. It does not invent a producer command that the release cannot
recover.

Non-goals are Ariadne registry or gate implementation, DSSE envelope creation,
cosign invocation, signature verification, authenticated publisher catalogues,
TUF, network reads, recapture, a new release format, manifest migration,
Tabularium mappings, provider-completeness proof, consensus finality proof,
canonical-chain proof, or work on the held interval collector.

- **Always:** run the Alexandria suite, root portable suite, focused Ariadne
  inspect/verify compatibility tests, schema drift checks, Imprimatur on every
  changed prose file, repository structural lints over their governed trees,
  and `git diff --check` before committing.
- **Ask first:** add a dependency; change `alexandria-release/v1`; register or
  alter a predicate in Ariadne; touch CI, a marketplace version, or another
  plugin; widen network access; sign anything; or edit an evolution frontier.
- **Never:** commit credentials or key material; follow a release symlink;
  mutate a verified release; emit after failed verification; delete or weaken a
  failing test; claim publisher identity, provider completeness, canonical
  chain status, predicate-owned gate success, or signature verification.

## 4. Design options

### Option A: encode Alexandria as Ariadne dataset/v1

This reuses registered gates and avoids a new type. The cost is semantic loss:
Alexandria's heterogeneous captures cannot be represented by one numeric
coverage interval and structured interval gaps without flattening distinct
scope kinds or inventing bounds. Rejected because a registered but lossy claim
is worse than an explicit unchecked predicate.

### Option B: emit an Alexandria-specific Statement v1 predicate

The Alexandria CLI verifies the release, projects its exact evidence boundary
into a versioned predicate, emits the logical release plus component subjects,
and leaves signing and Ariadne registration outside the step. Ariadne can parse
and inspect it now; its unknown-predicate report keeps gates 2 and 5 visible as
unchecked. Chosen because it is the smallest construction that meets #407
without changing either sibling's ownership or vocabulary.

### Option C: emit and register the predicate in Ariadne together

This could make predicate-owned gates run immediately. It also turns one
Alexandria wish into a cross-plugin public validation contract, requiring
Ariadne schema, registry, conformance fixtures, docs, and an additional audit
surface. Rejected for this prototype because #407 asks for emission, while the
current Ariadne contract deliberately gives unknown predicates a safe partial
path. Registration can later consume the frozen type and schema rather than
changing emitted bytes.

### Option D: expose a generic caller-supplied predicate template

This avoids choosing fields but lets operator prose and unverified values enter
what looks like archive evidence. Rejected because the release already contains
the authoritative scope, counts, and gaps; copying caller claims would weaken
the Promise Machine boundary.

## 5. Risk register seed

```risk-register
subject-binding | the conversion from Alexandria sha256-prefixed identities to in-toto digest maps | every release and component subject is present exactly once with the full lowercase digest and every claim names the logical release digest
predicate-fidelity | the projection from a verified manifest into the Alexandria predicate | scope kinds fields coverage counts unsupported collections and gaps survive without coercion omission or invented equivalence
untrusted-release | the release directory and manifest supplied to the new command | existing offline verification and bounded duplicate-key-safe parsing complete before any output is installed
output-confinement | the caller-selected output path beside a verified immutable release | outputs inside the release or aliased through a symlink are refused and the release tree remains unchanged
partial-write | the statement output while canonical JSON is being written | a sibling temporary regular file is flushed and atomically replaced and every failure removes the temporary file without a final output
claim-inflation | the language and Ariadne gate status exposed with the statement | the command claims only successful Alexandria verification and leaves signing authenticity completeness finality and unknown predicate gates visibly unproved
schema-drift | the emitter and published release-statement schema | a fixture validates against both and a test fails when their field sets or type URI diverge
determinism | canonical ordering and serialisation across repeated emission | unchanged verified input produces byte-identical UTF-8 JSON with a trailing newline
```

The audit loop should attack malformed manifests, output aliases, killed writes,
subject omission and duplication, prefix conversion, multiple capture scope
kinds, zero counts, empty and non-empty gaps, unsupported collections,
unregistered Ariadne reports, and every forbidden evidence upgrade.

## 6. Glossary seeds

- **Logical release subject:** the Alexandria `release_id`, a SHA-256 over the
  canonical manifest content defined by `alexandria-release/v1`, represented as
  an in-toto digest rather than a claim about the manifest file's bytes.
- **Component subject:** one manifest component represented by its name and
  declared SHA-256; its digest was rechecked against the confined object before
  emission.
- **Alexandria release predicate:**
  `https://ariadne.wildcat.finance/alexandria-release/v1`, the versioned
  projection of a verified release's scope, coverage, components, and gaps.
- **Ariadne-ready:** parseable as Statement v1 and eligible for Ariadne's core
  gates, with unregistered predicate gates still reported unchecked.
- **Unsigned:** no DSSE envelope or external signature verification result is
  present; this says nothing about publisher identity.
- **Declared gap:** negative-space prose already present in the release
  manifest; the emitter preserves it but does not independently prove it.

## 7. Sources

- Issue #407, `alexandria-1 - emit an Ariadne-ready release statement`, live
  body and labels read 2026-08-26.
- `plugins/alexandria/AGENTS.md` and
  `plugins/alexandria/skills/alexandria/SKILL.md`.
- `plugins/alexandria/scripts/alexandria.py`,
  `plugins/alexandria/scripts/alexandria_lib/release.py`,
  `plugins/alexandria/tests/test_release.py`, and
  `plugins/alexandria/tests/test_scaffold.py`.
- `plugins/alexandria/docs/study.md`,
  `plugins/alexandria/docs/raw-releases.md`, and
  `plugins/alexandria/skills/alexandria/EVOLUTION.md`.
- PR #62 at `de8228be2d2c37225512c2530a295970e3ac1f69` and PR #69 at
  `25b38af4a1663e834db87afc4166cca580804449`.
- `audit/AUDIT_SYNOPSIS.md`,
  `plugins/ariadne/audit/AUDIT_SYNOPSIS.md`, and
  `plugins/tabularium/audit/AUDIT_SYNOPSIS.md`, used only after the complete
  synopsis currency check exited zero.
- `plugins/ariadne/skills/ariadne/SKILL.md`,
  `plugins/ariadne/scripts/ariadne_lib/statement.py`,
  `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py`, and its
  conformance fixtures.
- Issue #408, `tabularium-2 - emit release evidence through Ariadne's dataset
  predicate`, read only to distinguish the sibling predicate decision.
- in-toto Attestation Framework, Statement v1:
  `https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md`.

## 8. Signals, and the questions behind them

The command is local and short-lived, so it adds no remote telemetry. Its
machine-readable success output and controlled stderr must answer:

- Which Alexandria release was bound? The statement step emits the full
  `release_id`, component count, capture count, predicate type, and output path
  after the atomic install.
- Did verification finish before emission? The same step emits no success
  record and leaves no final output if `verify` fails; the exit code and bounded
  error name the refusal.
- What remains unchecked downstream? The compatibility test records Ariadne's
  unregistered predicate status, unchecked signature status, and unchecked
  gates 2 and 5.
- Was the output deterministic? The test step emits the two computed statement
  digests and requires equality for identical input.

These are terminal receipts rather than logs: there is no daemon, request ID,
metric sink, or unattended retry loop to correlate.

## 9. Boundaries, per capability

- **Read a release:** the caller controls the directory. Worth taking is only a
  release that existing Alexandria verification accepts. The control is the
  current bounded, duplicate-key-safe, symlink-refusing, offline verifier before
  projection.
- **Project evidence:** the verified manifest controls all subjects and
  predicate values. Worth taking is the exact governed subset. The control is a
  closed schema, direct structural copies, digest normalization only at the
  in-toto boundary, and hostile fixture tests for omissions and type changes.
- **Write a statement:** the caller controls the output path. Worth taking is a
  new or replaceable regular file outside the release. The control is path
  separation, sibling temporary creation, no symlink following, cleanup, flush,
  and atomic replacement.
- **Consume through Ariadne:** Ariadne is a sibling process reading emitted
  bytes. Worth taking is its parse and core-gate report. The control is an exact
  Statement v1 shape and an acceptance test that requires unregistered and
  unchecked states to remain visible.
- **Sign or publish:** this capability is not opened. The command never reads a
  key, invokes cosign, reaches a catalogue, or states a publisher.

## 10. The budget, or its absence

There is no separate performance budget because the existing release verifier
already bounds the manifest, component, row, and file work, and statement
projection is linear in that accepted manifest. The audit should still record
the same-path measurement
`/usr/bin/time -p python3 plugins/alexandria/scripts/alexandria.py statement <fixture-release> --output <tmp-statement>`
before and after any claimed performance change. No performance change is
planned, so a measurement is not an exit condition for the prototype.

## 11. The fail-closed posture

Stop on any release-verification failure, malformed or missing digest, subject
or capture mismatch, unsupported output target, canonical-serialization error,
short write, flush failure, or atomic-install failure. Do not leave or replace a
final statement unless the whole path succeeds. A failure remains a controlled
Alexandria error with no traceback for expected hostile input.

Every discovered defect is first reduced to the smallest release or output-path
case that reproduces it. The guard test must fail against the implementation
without the fix, pass with the fix, and name the violated boundary rather than
the incidental exception. The audit record cites each risk-register id as
reviewed or not applicable.

## 12. Decisions and their homes

- The public type URI, closed predicate field set, subject semantics, and
  signing boundary are expensive to reverse. They live in
  `plugins/alexandria/schemas/release-statement-v1.schema.json` and
  `plugins/alexandria/docs/release-statements.md`; schema and fixture drift tests
  keep the two honest.
- The command name, arguments, side effects, exit codes, and operator language
  live in `plugins/alexandria/skills/alexandria/SKILL.md` and the generated-host
  mirror already governed by repository tests.
- The choice to remain unregistered in Ariadne is recorded here and in the
  release-statements document. A future registration changes Ariadne's own
  predicate registry, schema, gates, conformance fixtures, audit record, and
  docs; it must not silently change this version's emitted bytes.
- The ordinary-wish status and unchanged held frontier stay in this study and
  the Fiat receipts. `plugins/alexandria/skills/alexandria/EVOLUTION.md` is not
  edited because #407 does not deliver its named frontier.
