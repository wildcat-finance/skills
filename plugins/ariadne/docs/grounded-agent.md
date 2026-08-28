# The grounded-agent predicate

Type URI: `https://ariadne.wildcat.finance/grounded-agent/v1`.

This predicate joins a `berean-release/v1` identity to the exact bytes it was
given and produced. Ariadne checks the join. It does not rerun Berean, decide
whether an answer is good, or promote evaluation output into a conclusion.

## The body

Every object is closed: an unknown key fails `predicate-fields`. Optional
evidence is not implicit. The three optional blocks are an object or JSON
`null`, so a verifier can tell absence from an omitted decision.

- `release` names `berean-release/v1`, its version, the semantic
  `release_digest`, and the component holding the exact `release.json` bytes.
- `given` contains the corpus identity, manifest and corpus components, plus an
  optional block-bound reads component and its chain pin. A null reads block
  requires `reads_absence_reason`.
- `produced` contains answer components and optional evaluation case/report and
  promotion-chain components. Their paired fields are
  `evaluations_absence_reason` and `promotion_absence_reason`.
- `policy` preserves question families, refusal conditions, source and evidence
  vocabularies, allowlists, and retention.
- `adapter` records the tool, version, argv and parameters digest used to project
  this predicate.
- `comparison` names the current semantic release and either a named baseline
  or `null` with a stated `first_capture_reason`.
- `claims` and `commands` are the core Ariadne blocks.

The semantic `release_digest` and the digest of the exact `release.json` bytes
are separate values. The former is recomputed from Berean's release identity;
the latter is the `sha256` on `release.document`. They must not be equal. A
change to policy or another identity field needs a new semantic digest, while a
byte-only rewrite of `release.json` changes only the component digest.

Each absence-reason field is null when its evidence object is present. When the
object is null, the reason is a bounded non-blank string. A missing reason or a
reason beside present evidence is contradictory and fails `optional-evidence`.

## Components and subjects

Every component carries `name`, release-relative `path`, lowercase `sha256`, and
a whole-number `bytes` count. Names and paths are bounded, visible Unicode
scalar strings, free of line separators, and unique after Unicode NFC
normalisation. Absolute paths, drive
paths, backslashes, empty or dot segments, parent traversal, oversized values
and duplicate paths fail. Every component digest must appear in the in-toto
subject array, and every subject must name a declared component. Subject aliases
may add digest algorithms, but cannot give one `sha256` conflicting aliases or
map one supported digest to different `sha256` identities. A claim likewise
cannot combine supported aliases that the statement has already assigned to
different `sha256` identities.

Digest maps carry at most eight algorithms. Three slots cover Ariadne's current
supported algorithms and five remain for transition metadata; wider claim or
subject maps fail before claim-by-subject matching begins.

The corpus block carries its own `path`, `corpus_version`, semantic
`corpus_digest`, `manifest`, and non-empty `components`. A non-null reads block
carries `component`, `chain_id`, `block_number`, non-zero `block_hash`, and
stated `source`. Answers are a non-empty component array. A non-null evaluation
block carries only `cases` and `report` components.

A non-null promotion block binds the exact `promotions.jsonl` component, the
`berean-promotion/v1` format and its terminal `sequence`, `action`, and
`target_release_digest`. Its sequence is bounded by Berean's 1,000-record chain,
a rollback cannot be the first record, and either terminal action requires the
release's evaluation files. It deliberately has no `score`, `grade`, `verdict`,
`threshold`, or `result count`. Those are evaluation conclusions, not Ariadne
identity metadata. The exact Berean threshold and result-count keys are also
refused recursively in claim details, command details and subject descriptor
extensions, so an open core field cannot restore the projection that the closed
promotion block omits.

## Gate 2: recoverable environment

Gate 2 requires the complete release identity, exact component subjects,
corpus and optional read boundary, unchanged Berean source/evidence
vocabularies, release policy, and adapter parameters. It refuses malformed
digests and byte counts, unsafe names or paths, missing or extra subjects,
inconsistent optional blocks, and evidence vocabulary upgrades.

## Gate 5: explicit comparison

The current side always carries a portable name and the semantic digest of this
release. The baseline is either another named, digested release or JSON `null`.
A null baseline requires a non-blank `first_capture_reason`; a present baseline
requires that reason to be null and must not identify the current release.

The other core gates remain in force. Gate 4 refuses conclusion vocabulary such
as a `score`, `grade` or `verdict` anywhere in the predicate. Gate 7 refuses
authorship or verification identity keys that Ariadne did not authenticate.

## Predicate checks

After gates 2 and 5, named checks report the closed field shape, component and
subject coverage, semantic release digest, explicit optional evidence, unchanged
evidence boundary without evaluation-result projection, and portable subject
names. Each failing line names the affected gate or check and the field to
repair.

## Published schema

[`schemas/grounded-agent-v1.json`](../schemas/grounded-agent-v1.json) publishes
the closed JSON shape. Drift tests compare its fields, bounds and vocabularies
with `scripts/ariadne_lib/predicates/grounded_agent.py`, and compare Ariadne's
copied Berean public constants through Python syntax only when the sibling
plugin is present. There is no runtime dependency on Berean.
