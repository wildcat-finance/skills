# Study: Build the berean plugin from its Wildcat Commons specification

Assuming, unless corrected:

1. Python 3.9 or later, standard library only, `unittest` discovery, matching
   every first-party plugin except Lazarus.
2. The prototype's reference release answers against a small frozen
   demonstration corpus shipped inside the plugin, plus preserved Goldfinch
   mainnet reads copied byte for byte from the Lazarus example fixture. A
   release grounded in live Wildcat documentation and captured Wildcat market
   reads is the held frontier, not this run.
3. The Ariadne binding is deferred. Ariadne's ledger holds
   `grounded-agent-predicate` as its own next job, and this run does not
   advance a sibling's frontier. Berean's release document carries the digests
   a future statement will cover, and nothing more.
4. Berean lands as the thirteenth marketplace plugin at version `0.1.0`, with
   every root integration point (marketplace manifests, portable entry, root
   README and AGENTS.md, hard-coded test lists) updated in the scaffold step.
5. No GitHub issue and no CI workflow are created for this run.

## 1. Problem statement

Build `berean`, the Wildcat Commons release kit for evidence-backed protocol
agents. A Berean release pins a corpus by digest, proves every citation as a
byte range in that corpus, binds every live value to a chain and block,
separates document claims from chain readings from calculations from
user-supplied facts, states which question families it supports and when it
refuses, and records the evaluation result that let it become active. The
verifier checks all of that offline, without the model that produced the
answers.

It is for developer relations, support and agent engineering teams who run a
protocol agent and need its answers testable after the fact. A working
prototype means: `python3 plugins/berean/scripts/berean.py verify-release
plugins/berean/examples/goldfinch-demo-v0` exits 0 against the shipped
reference release, exits 1 when any pinned byte or gate is disturbed, and
`python3 plugins/berean/examples/goldfinch-demo-v0/demo.py` walks the whole
path: corpus check, citation check, block-bound read check, eval run,
promotion record check. Both root suites and the berean suite pass, and every
shipped document lints clean.

## 2. Prior art

In this repository:

- Ariadne (`plugins/ariadne/`) supplies the verification grammar: in-toto
  statements matched by digest rather than name, closed field tables with
  `additionalProperties: false`, per-gate conformance fixtures named
  `pass-*` and `fail-<gate>-*`, `digests.py` refusing uppercase hex and
  symlinks, and `safejson.py` caps on size and depth. Its core gate 4 refuses
  conclusion vocabulary (`score`, `verdict`, `grade`) anywhere in a
  predicate, which is one reason berean's evaluation results cannot live
  inside an Ariadne predicate.
- Lazarus (`plugins/lazarus/`) supplies the evidence bundle berean consumes:
  `rpc.jsonl` records keyed by `request_key =
  sha256(canonical({method, params}))`, a manifest pinning block number and
  hash, and the release-binds-to-statement pattern in
  `scripts/lazarus_lib/binding.py` where two constants and a drift test
  replace a runtime import. Its `canonical.dumps` discipline (sorted keys,
  compact separators, floats refused) is copied, not imported.
- Lemma (`plugins/lemma/`) proves byte-exact quoting is workable
  (`display_text` sliced from source bytes, decoded after slicing,
  `synthesised` flagged) and shows the gap berean exists to close: its
  records carry no byte offsets, no span digest and no file digest, so a
  chunk cannot be re-verified against a pinned corpus from the record alone.
- Alexandria (`plugins/alexandria/`) names the rule berean generalises:
  evidence classes are preserved, never upgraded, and corrections are new
  releases with `supersedes` rather than mutations.
- Tabularium (`plugins/tabularium/docs/release-policy.md`) supplies the
  immutability and supersession policy for published releases.
- Probitas (`plugins/probitas/`) supplies the answer-side discipline: a claim
  without a source is dropped, gates rebuild the permitted fact set from
  evidence and fail the document on anything outside it, and coverage gaps
  are rows rather than silence.
- Imprimatur's labelled corpus
  (`plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/`) is the
  house pattern for a frozen, sealed evaluation corpus: pinned sample
  digests, a candidate freeze, named boolean gates, and a spent holdout.
- Brevitas (`plugins/brevitas/skills/brevitas/evals/`) shows the small form:
  a case file pinning its origin digest, graded by code, failing before
  grading when the pin no longer matches.

Outside: the in-toto Statement v1 shape (via Ariadne), EIP-1186 proofs (via
Lazarus), and the Agent Skills evaluation guide at
`https://agentskills.io/skill-creation/evaluating-skills`, whose case shape
(`id`, `prompt`, `files`, `assertions`) berean emits as an export so existing
runners can consume its cases.

## 3. Constraints and non-goals

Constraints. Starting ref `496f7a102bf012195c48ed1615f8eff7fd832f7b` on
`main`; run branch `claude/berean-wildcat-skill-zx1o2g`. Python 3.9+,
standard library only, `unittest`, no network anywhere in tests or examples.
Digested documents are canonical JSON: sorted keys, compact separators,
`ensure_ascii=False`, floats refused, duplicate keys refused. Digests are
lowercase sha256 hex. Every shipped Markdown file outside `docs/` must lint
clean under imprimatur; frontier prose must be byte-identical across every
marketplace-context block; the `EVOLUTION.md` baseline row must reproduce the
ledger digest formula in `plugins/hexaemeron/skills/VERSIONING.md`.

Non-goals, deferred past the prototype:

- The Ariadne grounded-agent predicate and any statement binding. Designed
  for, not shipped; it is Ariadne's held frontier job.
- A general evaluation runner. Berean grades recorded answer documents with
  its own code assertions and exports cases in the Agent Skills shape;
  it does not execute models or tools.
- Live capture of documentation or chain state. The corpus builder reads
  local trees; chain evidence arrives as preserved Lazarus-shaped records.
- A release grounded in live Wildcat documentation and captured Wildcat
  market reads. That is the held frontier after this run.
- Chat UI, model vendor integration, retrieval, embeddings.

## 4. Design options

Option A: implement the release manifest as a new Ariadne predicate.
Rejected. Gate 4 of Ariadne's core refuses `score`, `verdict` and `grade`
keys, so evaluation thresholds and results cannot be structured fields
there; and the predicate slot is Ariadne's own held next job, which an
ordinary berean delivery must not consume.

Option B: ship berean's formats and bind a reference release to an Ariadne
statement in this run. Rejected. The binding needs the grounded-agent
predicate to exist first, which is option A's problem again through a
narrower door.

Option C, chosen: berean owns five small formats (corpus manifest, answer
record, eval case, release manifest, promotion record), each a versioned
JSON schema with a closed field table, verified by one stdlib CLI. Chain
evidence is consumed in the Lazarus record shape, held by recomputed
`request_key`, with a drift test against the Lazarus fixture rather than an
import. The release document keeps every artefact digest a future Ariadne
statement would cover. The trade named: no in-toto interoperability ships in
v0.1.0, and berean carries its own schema maintenance instead of inheriting
Ariadne's. Bought with it: all eight specification gates are expressible,
including the two Ariadne's vocabulary forbids, and no sibling plugin is
coupled or advanced.

The pick is the construction cheapest to comprehend: one plugin, five
schemas, one verifier, no cross-plugin imports.

## 5. Risk register seed

The audit loop should look hardest at:

- Untrusted JSON: every reader needs the size cap, depth cap and
  duplicate-key refusal Ariadne's `safejson.py` models, or a poisoned release
  parses the verifier into a hang.
- Path handling: corpus and release component paths must refuse absolute
  paths, `..`, backslashes and symlinks, or a citation can read bytes outside
  the pinned tree.
- Digest discipline: lowercase hex only, byte-exact slicing before decoding,
  span digest and display text both checked, or a citation passes on one and
  lies on the other.
- Evidence-class inflation: a recorded read reported as proof-backed, or a
  document claim reported as a chain reading. The classes are closed enums
  copied from their owners and never widened at read time.
- Partial writes: releases and corpus manifests are staged and landed with
  one rename, so a killed run leaves no half-release that later verifies.
- Prompt-injection fixtures: the adversarial corpus contains documents whose
  text instructs policy changes; the graders must fail any answer that obeys
  them, and the fixtures must not be executable by anything.
- Marketplace prose drift: the frontier sentence replicates across roughly
  twenty files and root tests compare it byte for byte.

## 6. Glossary seeds

- `corpus manifest`: the digest-pinned inventory of a document tree; one
  entry per file with bytes and sha256, plus a corpus digest over the sorted
  listing.
- `citation`: document id, byte start, byte end, span sha256 and display
  text; valid only when re-slicing the pinned file reproduces both digest
  and text.
- `source class`: one of `document`, `chain_read`, `calculation`,
  `user_supplied`; every factual sentence in an answer carries exactly one.
- `chain read`: a preserved RPC outcome named by chain id, block number and
  recomputed request key.
- `time domain`: the version stamp of an evidence item; a document version
  on one side, a block number on the other. Answers report disagreement
  between domains rather than choosing silently.
- `refusal`: an answer whose body names the evidence boundary it could not
  satisfy instead of an answer text.
- `eval case`: a question, its expected evidence shape and its grader;
  adversarial cases expect refusals or preserved policy.
- `release manifest`: the document binding corpus, reads, rules, question
  families, eval results and retention declaration into one digested unit.
- `promotion record`: the record of which evaluation, thresholds and results
  made a release active; rollback is a new record naming the restored
  release, never an edit.

## 7. Sources

- The Commons specification, preserved beside this study at
  [spec.md](spec.md).
- `plugins/ariadne/docs/design.md`, `plugins/ariadne/docs/conformance.md`,
  `plugins/ariadne/scripts/ariadne_lib/`.
- `plugins/lazarus/docs/preservation-release.md`,
  `plugins/lazarus/examples/goldfinch-v0-release/`,
  `plugins/lazarus/scripts/lazarus_lib/{records,canonical,binding}.py`.
- `plugins/lemma/INVARIANTS.md`, `plugins/lemma/schema.py`,
  `plugins/lemma/chunkers/markdown.py`.
- `plugins/alexandria/docs/study.md` (evidence-class inflation),
  `plugins/tabularium/docs/release-policy.md` (supersession).
- `plugins/probitas/scripts/probitas_lib/{evidence,gates}.py`.
- `plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/README.md`.
- `plugins/hexaemeron/skills/VERSIONING.md`, `tests/test_marketplace_prose.py`,
  `tests/test_portable_skills.py`, `tests/test_version_propagation.py`,
  `tests/test_evolution_contract.py` (the integration gates).
- `https://agentskills.io/skill-creation/evaluating-skills` (exported case
  shape).

## 8. Signals, and the questions behind them

The kit is a terminal CLI, so the on-call questions are a maintainer's, not
an operator's:

- "Why did verify refuse this release?" Every gate prints one named
  pass/fail line and the first failing detail, the Ariadne report shape, so
  the refusal is in the output rather than in a debugger. Steps 4 and 6 emit
  this.
- "Did the eval run grade the corpus it claims?" The eval report starts with
  the corpus digest and release digest it graded against, and the runner
  refuses to grade when recomputed digests disagree with pinned ones. Step 5
  emits this.
- "Which release is active and what promoted it?" The promotion chain is a
  file the CLI prints verbatim with its digests checked. Step 4 emits this.

No logging framework: the CLI prints, per the ephoros rule that command-line
output is not telemetry.

## 9. Boundaries, per capability

- Corpus building opens a filesystem read boundary. Worth taking at it:
  bytes outside the tree via symlink or traversal. Control: resolve and
  refuse symlinks, refuse absolute and parent-relative paths, then digest
  what was actually read. Owned by phylax's rules in the audit rounds.
- Release verification opens an untrusted-input boundary. Worth taking:
  parser exhaustion and duplicate-key shadowing. Control: byte cap, depth
  cap, duplicate-key refusal before any field is trusted.
- Chain-read checking opens a provenance boundary. Worth taking: a value
  with no block, or a record whose key does not match its params. Control:
  recompute `request_key`, require chain id and block, refuse records whose
  copied bytes drift from the Lazarus fixture (drift test).
- The adversarial corpus opens a content boundary. Worth taking: instructions
  inside documents steering the verifier or graders. Control: fixtures are
  data to every code path; graders assert policy survived.

No network capability exists anywhere in the plugin, so no allowlist is
needed beyond the release's own declared chain and contract lists, which the
verifier checks answers against.

## 10. The budget, or its absence

None. No performance claim is made. Input ceilings (corpus bytes per file,
release component count, JSON depth) are correctness limits with tests, not
budgets, and are named in the schemas. If a later frontier adds a large
corpus, metron owns the measurement then.

## 11. The fail-closed posture

Builders refuse to write: a corpus manifest or release that fails its own
validation is not written at all, the Lemma `NOT WRITTEN` pattern. The
verifier runs every gate and reports each by name, exits 1 on any failure,
and never repairs. Readers refuse rather than coerce: wrong hex case, a
`0x`-less hash, a float, a duplicate key are refusals, not normalisations.
Every failure worked mid-step follows elenchus: reproduce, reduce, fix the
mechanism, and land a guard test named after the failure class
(`test_<what>_refuses_<how>`), so the fixture set grows one `fail-*` file per
class the way Ariadne's conformance corpus does.

## 12. Decisions and their homes

- Deferring the Ariadne binding, and what a future statement covers:
  `plugins/berean/docs/design.md`.
- Copying Goldfinch read records instead of referencing the Lazarus fixture
  path, with the drift test that holds the copy: `plugins/berean/docs/design.md`.
- Release immutability, supersession and rollback-as-record:
  `plugins/berean/docs/release-policy.md`.
- Source-class and time-domain vocabulary, and why the enums are closed:
  `plugins/berean/docs/answers.md`.
- How the specification's named inputs (Project Aleph, Project Null, Lemma)
  shaped each component, at the level the specification states:
  `plugins/berean/docs/influences.md`.

## Boundaries

Always:

- Both root suites and the berean suite before every commit:
  `python3 -m unittest discover -s tests` and
  `python3 -m unittest discover -s plugins/berean/tests -t plugins/berean`.
- The imprimatur lint on every shipped document; hypomnema over
  `README.md AGENTS.md .agents plugins docs`; phylax and ephoros over
  `plugins tests`.
- A `pass-*` and a `fail-*` fixture in the same step as every new gate.

Ask first:

- Adding a dependency (the plan is zero).
- Changing a published schema `$id`, a format string, or a closed enum
  (source classes, evidence classes, dispositions).
- Touching another plugin's files beyond the root integration points this
  study names.
- Widening the copied Lazarus record set or its provenance claims.

Never:

- Commit key material or an RPC credential; the plugin never holds either.
- Edit the Lazarus fixture, any vendored directory, or a frozen corpus file
  once its digest is pinned.
- Delete or weaken a failing test to make a suite pass.
- Claim a command, lint or suite ran when it did not.
- Upgrade an evidence class or source class during verification.
