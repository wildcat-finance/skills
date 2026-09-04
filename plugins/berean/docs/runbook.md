# Runbook: Build the berean plugin from its Wildcat Commons specification

Derived from the study preserved beside this runbook at
[study.md](study.md). The run branch is
`claude/berean-wildcat-skill-zx1o2g`, cut from `main` at
`496f7a102bf012195c48ed1615f8eff7fd832f7b`, where the root suite is green
(34 tests). Each step branches from the step below it; nothing merges until
the integrate phase. Every step ends with both suites green: the root suite
and, from step 1 on, `python3 -m unittest discover -s plugins/berean/tests
-t plugins/berean`.

## Step 1: Scaffold the plugin and land it in the marketplace

**Goal.** Berean exists as the thirteenth plugin, with its shell, committed
spec, study and runbook, and every root integration point updated and green.
**Entry.** Run branch at `496f7a102bf012195c48ed1615f8eff7fd832f7b`.
**Exit.** `python3 -m unittest discover -s tests` green with the plugin
count assertions at 13; `python3 -m unittest discover -s
plugins/berean/tests -t plugins/berean` green;
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` clean
on every new shipped Markdown file; `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents plugins docs` exit 0.
**Files.** `plugins/berean/.claude-plugin/plugin.json`,
`plugins/berean/.codex-plugin/plugin.json`, `plugins/berean/AGENTS.md`,
`plugins/berean/README.md`, `plugins/berean/LICENSE`,
`plugins/berean/skills/berean/SKILL.md`,
`plugins/berean/skills/berean/EVOLUTION.md`,
`plugins/berean/skills/berean/agents/openai.yaml`,
`plugins/berean/docs/spec.md`, `plugins/berean/docs/study.md`,
`plugins/berean/docs/runbook.md`, `plugins/berean/docs/design.md`,
`plugins/berean/tests/__init__.py`, `plugins/berean/tests/support.py`,
`plugins/berean/tests/test_scaffold.py`, `.agents/skills/berean/SKILL.md`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`README.md`, `AGENTS.md`, `tests/test_marketplace_prose.py`,
`tests/test_portable_skills.py`.
**Tests.** `test_scaffold.py`: the three manifests agree, the ledger digest
reproduces, the frontier sentence matches across the plugin's own files.
Expected count: 6 to 10.
**Disciplines.** phylax: none, this step ships manifests, prose and tests
only. ephoros: none, no runtime code yet. metron: none, no performance
claim. elenchus: none, no failure in hand. hypomnema: the Ariadne deferral
and the copied-reads decision land in `plugins/berean/docs/design.md`
alongside the committed spec.

## Step 2: Corpus manifests and byte-exact citations

**Goal.** A document tree can be pinned into a corpus manifest and a
citation can be proved or refused as exact bytes in it.
**Entry.** Step 1's exit state.
**Exit.** `python3 -m unittest discover -s plugins/berean/tests -t
plugins/berean` green, including tests that a one-byte edit to a pinned
file fails `verify-corpus` and a wrong span digest or display text fails
`check-citation`; root suite still green.
**Files.** `plugins/berean/scripts/berean.py`,
`plugins/berean/scripts/berean_lib/__init__.py`, `canonical.py`,
`digests.py`, `jsonio.py`, `corpus.py`, `citations.py` under
`plugins/berean/scripts/berean_lib/`,
`plugins/berean/schemas/corpus-manifest-v1.json`,
`plugins/berean/tests/test_canonical.py`, `test_digests.py`,
`test_corpus.py`, `test_citations.py`, fixture trees under
`plugins/berean/tests/fixtures/corpus/`.
**Tests.** Canonical JSON refusals (floats, duplicate keys), digest
refusals (uppercase hex, symlinks), corpus build and verify, citation pass
and every refusal class. Expected count: 30 to 40.
**Disciplines.** phylax: this step opens the filesystem read boundary;
symlinks, absolute and parent-relative paths are refused with tests.
ephoros: the CLI prints named results, no logging. metron: none, ceilings
are correctness limits with tests. elenchus: any red test is worked to its
mechanism and lands a guard test. hypomnema: none, the format decisions are
already recorded in `design.md`.

## Step 3: Answer records, source classes and block-bound reads

**Goal.** An answer document carries a source class on every factual
sentence, block-named chain reads held by recomputed request keys, declared
time domains and a clean refusal shape, and `check-answer` proves or
refuses each.
**Entry.** Step 2's exit state.
**Exit.** Plugin suite green, including tests that an unclassified sentence,
a chain value without chain and block, a request-key mismatch, and a silent
time-domain disagreement each fail `check-answer`; root suite still green.
**Files.** `plugins/berean/schemas/answer-v1.json`,
`plugins/berean/scripts/berean_lib/answers.py`,
`plugins/berean/scripts/berean_lib/reads.py`, subcommand wiring in
`scripts/berean.py`, `plugins/berean/tests/test_answers.py`,
`test_reads.py`, fixtures under `plugins/berean/tests/fixtures/answers/`
and `fixtures/reads/`.
**Tests.** Source-class enum closure, per-sentence classification checks,
read record recomputation against Lazarus-shaped records, time-domain
disagreement reporting, refusal shape. Expected count: 30 to 40.
**Disciplines.** phylax: the untrusted-input boundary widens to answer and
read documents; caps and refusals carry tests. ephoros: `check-answer`
prints one named line per check. metron: none. elenchus: as step 2.
hypomnema: the closed source-class and time-domain vocabulary is recorded
in `plugins/berean/docs/answers.md`.

## Step 4: Release manifests, verifier gates and promotion records

**Goal.** A release binds corpus, reads, rules, question families, refusal
conditions, eval references and retention into one digested document;
`verify-release` reports the specification's gates by name; promotion and
rollback are records, never edits.
**Entry.** Step 3's exit state.
**Exit.** Plugin suite green, including one `pass-*` and at least one
`fail-*` conformance fixture per verifier gate, staged-write tests, and
promotion-chain tests; root suite still green.
**Files.** `plugins/berean/schemas/release-v1.json`,
`plugins/berean/schemas/promotion-record-v1.json`,
`plugins/berean/scripts/berean_lib/release.py`,
`plugins/berean/scripts/berean_lib/promote.py`, subcommand wiring,
`plugins/berean/docs/release-policy.md`,
`plugins/berean/tests/test_release.py`, `test_promote.py`,
`plugins/berean/tests/fixtures/conformance/`.
**Tests.** Gate-by-gate pass and refusal, whole-release digest, staged
landing, promotion evidence checks, rollback as supersession. Expected
count: 40 to 50.
**Disciplines.** phylax: release paths are confined to the release
directory with tests. ephoros: `verify-release` prints every gate's named
verdict. metron: none. elenchus: as step 2. hypomnema: immutability and
rollback policy land in `plugins/berean/docs/release-policy.md`.

## Step 5: The evaluation corpus and its graders

**Goal.** Ordinary and adversarial eval cases are schema-validated, graded
by code against recorded answer documents with digests pinned first, and
exportable in the Agent Skills case shape.
**Entry.** Step 4's exit state.
**Exit.** Plugin suite green, including graders failing an answer that obeys
an injected instruction, cites a mismatched span, presents stale state as
current, answers past the evidence boundary, or answers where refusal is
expected; `run-evals` refuses to grade on a digest mismatch; root suite
still green.
**Files.** `plugins/berean/schemas/eval-case-v1.json`,
`plugins/berean/scripts/berean_lib/evals.py`, subcommand wiring,
`plugins/berean/tests/test_evals.py`, case and answer fixtures under
`plugins/berean/tests/fixtures/evals/`.
**Tests.** Case schema closure, each grader class, each adversarial family,
export shape, digest-mismatch refusal. Expected count: 30 to 40.
**Disciplines.** phylax: adversarial fixtures are data to every code path;
nothing interprets them. ephoros: the eval report opens with the digests it
graded against. metron: none. elenchus: as step 2. hypomnema: none, the
grading vocabulary was recorded in step 4's policy and step 3's answers
records.

## Step 6: The reference release, and the demonstration

**Goal.** A complete reference release under
`plugins/berean/examples/aave-v4-demo-v0/` answers, refuses and discloses
a time-domain disagreement against a frozen corpus and preserved Aave v4
mainnet reads, and the demo proves the whole path offline.
**Entry.** Step 5's exit state.
**Exit.** `python3 plugins/berean/scripts/berean.py verify-release
plugins/berean/examples/aave-v4-demo-v0/release` exits 0; the tamper tests prove
a mutated corpus byte, read record and promotion record each exit 1;
`python3 plugins/berean/examples/aave-v4-demo-v0/demo.py` exits 0 with no
network; both suites green; the lint set from the study's Always list exits
clean.
**Files.** `plugins/berean/examples/aave-v4-demo-v0/` (`README.md`,
`demo.py`, `rebuild.py`, and the release under `release/`: corpus files,
`corpus-manifest.json`, `reads.jsonl`, answer documents, eval cases and
results, `release.json`, `promotions.jsonl`). Corrected during the step:
the release sits under `release/` because the components gate refuses
undeclared files beside `release.json`, and the browsing files belong
beside the release rather than inside it.
`plugins/berean/docs/influences.md`, `plugins/berean/tests/test_examples.py`,
reconciled `plugins/berean/README.md` and
`plugins/berean/skills/berean/SKILL.md`.
**Tests.** Example verifies clean, tamper refusals, the drift test holding
`reads.jsonl` byte-identical to the named Lazarus fixture records, docs
link checks. Expected count: 15 to 25.
**Disciplines.** phylax: the demo reads only inside the example tree.
ephoros: `demo.py` prints each stage's named result. metron: none.
elenchus: as step 2. hypomnema: `plugins/berean/docs/influences.md` records
how the specification's named inputs shaped each component.
