# Imprimatur labelled-corpus calibration

## Problem statement

Imprimatur has a deterministic three-tier prose lint and 55 passing tests. Its
current specimens are written inside the test file: 19 positive snippets, 12
clean snippets, behavior checks, and self-lint. They prove known rules, but
they do not measure false positives or misses on prose that was published
before the test authors selected the examples.

This delivery is for Wildcat Skills maintainers. It must build a versioned,
held-out fixture of shipped human and model-assisted prose; record source and
origin evidence for every sample; label actionable spans by hard, gated, and
structural tier; run a deterministic evaluation; change the lint only when
the calibration split demonstrates an error; and publish baseline and final
metrics. The fixture tests prose quality rules. It is not an origin detector,
and origin is used only to report whether one authoring group fares
differently from the other.

A working prototype consists of these repository artefacts:

- `plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/README.md`
  defines selection, provenance, annotation, split, and metric rules.
- `samples.jsonl` holds 64 immutable paragraph samples with source URLs,
  source commits, content hashes, genre, source-group ids, origin class, and
  affirmative origin evidence.
- `labels.jsonl` holds adjudicated span labels without changing sample text.
- `split.json` assigns 32 samples to calibration and 32 to holdout by whole
  source group.
- `scripts/evaluate_labelled_corpus.py` checks schema, source hashes,
  provenance, balance, group isolation, duplicate leakage, annotation
  coverage, and then reports precision, recall, F1, specificity, and counts by
  tier and origin.
- `baseline.json` records the untouched `imprimatur-v1.1.0` result on the
  calibration split. `final.json` records calibration and one sealed holdout
  run after any measured fixes.

The demonstration command is:

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/evaluate_labelled_corpus.py \
  --fixture plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1 \
  --verify-sources --report /tmp/imprimatur-eval.json
```

It must exit 0, reproduce checked-in metrics byte for byte apart from an
explicit timestamp field, and leave the normal 55-test suite green. The
repository checks required by `AGENTS.md` must also pass.

The held job says "shipped human and model-assisted prose." The selected
reading is public prose that reached the default branch of a Wildcat GitHub
repository, or a merged PR or issue in `wildcat-finance/skills`. The user has
supplied an authoritative origin rule: prose shipped before 2025-08-01 may be
labelled human. Model-assisted rows need an affirmative agent marker. Unmarked
prose from 2025-08-01 onward remains `unknown` unless another explicit origin record
exists, and unknown rows are excluded from scored samples.

## Evidence at study time

The active target is `main` at
`bcbaede047e746aec5573a31d70201275ee58533`, the merge commit for PR #77. The
live controller is in phase `study` for topic
`imprimatur-labelled-corpus-calibration`. Unrelated untracked
`.agents/skills/sapheneia/` and `plugins/sapheneia/` directories are present
and are outside this run.

The installed and checkout copies of the current lint and tests are
byte-identical:

| File | SHA-256 |
| --- | --- |
| `scripts/imprimatur.py` | `8132f705ad2ce98ca42855b5ca191f4d7725d1260e2cc2d411187e198f1529f1` |
| `tests/run_tests.py` | `56e474e71bc93e6cf6e02e1344aa3fa9fcdd0c5f3cf9c0fd1fe3d519272f7251` |

The installed Imprimatur suite passed 55 of 55 tests during this study. The
lint implementation is 454 lines of Python and depends only on the standard
library. Its three JSON lexicons contain nine hard families, four gated
families, eleven structural patterns, and cadence settings. Three structural
patterns are advisory signals and do not affect the score.

The current suite has no provenance fields, train/test split, confusion
counts, or recall calculation. Its positive snippets are all written to match
known terms or regexes. Its clean snippets cover useful cases such as quoted
mentions, code, quantified intensifiers, named identifiers, anaphora, and a
genuine three-item list. They must remain regression tests, but they cannot be
reused in the new fixture or counted as held-out evidence.

GitHub currently reports 40 merged PRs in `wildcat-finance/skills`; 17 carry
the `origin:ai` label. PR #77 demonstrates the current full provenance form:
the label, `<!-- wildcat-origin: shoggoth -->` in the PR body, and Shoggoth
trailers on its commits. Earlier merged work also provides affirmative
model-assisted evidence through named Claude Opus 5 co-authors, including PRs
#40 and #41. The repository has no `origin:human` label. Twenty-three merged
PRs lack `origin:ai`, but absence is not a human-origin assertion. The user's
pre-1-August-2025 rule supplies the human class from older public Wildcat repositories;
it does not reclassify later unmarked work.

The Wildcat organisation has other public and private repositories. Public
repositories including `wildcat-finance/wildcat-protocol`,
`wildcat-finance/v2-protocol`, and `wildcat-finance/wildcat-docs` contain the
pre-1-August-2025 history from which the human pool can be sampled. A bounded public
search found no shared `Wildcat-Origin: shoggoth` record outside
`wildcat-finance/skills`, so the affirmative model-assisted pool remains in
the Skills repository. Private organisation prose is excluded so another
person can reproduce the fixture without additional access.

## Prior art

### Existing Imprimatur machinery

`plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` exposes `build()`
and returns tier, family, severity, line, column, term, and rationale for each
finding. That is enough to adapt to span metrics without changing normal CLI
output. The script masks quotes and code, finds hard tokens, decides whether a
gated term has same-sentence evidence, applies structural regexes, and reports
cadence separately.

`plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` is a direct
regression suite. It includes 19 expected findings, 12 expected clean snippets,
gate behavior, hook behavior, self-lint, JSON parsing, and duplicate-hard-term
checks. The new evaluation should call the same `build()` function and leave
these examples in the fast suite.

`lexicon/hard.json`, `gated.json`, and `structural.json` are the rule sources.
The gated file declares per-family token windows, although the current
`window_tokens()` implementation returns the full containing sentence when a
sentence span is found. That code-to-data mismatch is a review target. It is
not grounds for a change until labelled calibration prose shows a false
positive or miss.

`references/lexicon-rationale.md` describes substitution drift and makes clear
that a high score only means known markers were absent. `references/rewriting.md`
protects facts, uncertainty, and author stance. `references/agent-replies.md`
puts honesty before brevity. These rules supply annotation guidance, but the
annotators must not see lint output.

### Git and GitHub provenance

`plugins/hexaemeron/skills/fiat/references/push-discipline.md` requires every
Fiat-created commit to carry Shoggoth co-author and `Wildcat-Origin` trailers,
and every Fiat-created PR to carry `origin:ai` plus the hidden body marker.
That gives the model-assisted pool an affirmative rule from PR #48 onward.

For earlier work, GitHub commit author arrays provide named Claude or Shoggoth
co-authors. PR #40 has Claude Opus 5 on commit
`84ed83f0c5f7d745275ae1c941ea213df6d3bc41`; PR #41 has Claude Opus 5 on
`6441158026259584d1053930872bd90c300b9778`. These are suitable
model-assisted source groups even though the later `origin:ai` label did not
yet exist.

GitHub's human account author field is insufficient for the human pool because
the same account owns both marked and unmarked PRs. Instead, the user's
authoritative cutoff labels prose human when its source commit is reachable
from the public repository's default branch and its committed timestamp is
before `2025-08-01T00:00:00Z`. Record the commit, timestamp, default-branch
reachability check, and source path. A separate explicit maintainer attestation
may admit later human prose. Branch names, missing labels, and missing trailers
are never promoted to proof.

### Upstream and external work

Imprimatur absorbed rule material from `ehmo/slopkit`. At upstream commit
`b33718bb9283c11b09567dc714f92d90ffb7bd16`, Slopbeth carries 88 authored
rewrite cases, 12 false-positive rows, eight annotated long samples, and
independent judge rows. Slopgent carries 16 authored communication cases,
decoys, blinded judge packets, and deterministic scoring. The upstream docs
plainly say those cases are authored rather than sampled from live sessions.
They are useful examples for schemas, blinding, decoys, and limits. They are
excluded from the new fixture because Imprimatur's rules were derived from
the same project and because they are not the required shipped Wildcat prose.

Precision, recall, and F1 follow the standard information-retrieval
definitions used by `sklearn.metrics.precision_recall_fscore_support`.
Scikit-learn's common-pitfalls guide supplies the group-before-split and
no-test-tuning rule. Unicode Standard Annex #15 supplies NFKC normalization
for duplicate checks. The fixture follows the provenance questions in
"Datasheets for Datasets" by recording collection purpose, source, origin,
selection, exclusions, labels, licence, and known limits.

## Constraints and non-goals

- Use only public Wildcat GitHub prose for scored samples. Use pre-1-August-2025
  default-branch history for the human pool and affirmatively marked
  `wildcat-finance/skills` history for the model-assisted pool. Do not copy
  private Slack, email, customer, legal, or counterparty text into the
  repository.
- Do not infer human origin from a human Git author, unmarked prose at or after the cutoff, a
  branch prefix, writing style, or account ownership. Apply the supplied
  pre-1-August-2025 rule only when the immutable source and default-branch reachability
  are recorded.
- Do not infer model origin from prose style. Require `origin:ai` plus its PR
  marker, a Shoggoth trailer, or a named model co-author.
- Keep `unknown` candidates in an inventory report if useful, but never in
  the 64 scored samples.
- Use paragraph-sized prose only. Exclude code, tables, generated data,
  quotations of other text, vendored material, release fixtures, and any path
  under the existing Imprimatur skill.
- Exclude exact and near-duplicates of existing test snippets, lexicon notes,
  Imprimatur references, and upstream slopkit cases. Also exclude copied
  `SKILL.md`/`README.md` mirrors and repeated marketplace descriptions.
- Pin every source to a commit SHA or immutable GitHub object URL. Store its
  SHA-256 after newline normalization. Do not fetch mutable branch heads when
  verifying.
- Use Python 3 and the standard library. A new third-party metrics dependency
  would add packaging work without improving this small deterministic runner.
- Keep origin separate from quality labels. A human sample may contain an
  actionable span; a model-assisted sample may be clean.
- Do not train an authorship classifier, compare model brands, make claims
  about all Wildcat prose, or treat this enriched fixture as a prevalence
  survey.
- Do not tune on holdout labels, rewrite source prose, weaken truthfulness
  language, add a new family for a single example, or make a term hard merely
  because it appeared once.
- Do not edit the lint when calibration reports no adjudicated error. A
  no-code-change result is valid.
- The Solidity suite is out of scope. The active Fiat state records its
  waiver.

## Corpus and annotation design

### Source selection

Build two source pools from immutable public GitHub data:

1. Model-assisted pool: merged PR bodies, commit messages, and Markdown
   paragraphs with affirmative agent provenance.
2. Human pool: Markdown paragraphs and other shipped prose from public Wildcat
   default-branch commits before `2025-08-01T00:00:00Z`, plus any later source
   with a separate explicit maintainer attestation.

Select eight source groups per origin, four distinct paragraphs per group, for
32 samples per origin and 64 total. A source group is one merged PR or one
commit series that introduced the prose. Include at least two groups from each
of three genres: technical documentation, delivery or incident reports, and
GitHub change descriptions.

Within each origin and genre stratum, order eligible paragraphs by
`sha256(seed || source_url || normalized_text)` with seed
`imprimatur-labelled-prose-v1`. Take the first eligible rows after exclusions.
This prevents choosing samples because they look easy or because the current
lint fires on them.

Normalize for duplicate detection with Unicode NFKC, lowercase conversion,
Markdown marker removal, and whitespace collapse. Reject an exact normalized
hash match. Reject a candidate when word five-gram Jaccard similarity is at
least 0.80 against an existing sample or any excluded Imprimatur/upstream
specimen. Store the nearest comparison and score for every rejection.

### Split and concealment

Assign whole source groups, never individual paragraphs, to calibration or
holdout. Use four groups per origin in each split, producing 32 samples per
split. The split generator sorts group hashes with the fixed seed and checks
origin and genre balance. All paragraphs copied or revised from the same text
family share a group.

Two annotators independently label a blinded packet containing only sample id,
text, and annotation rules. It omits origin, source, split, current lint output,
and lexicon matches. Each annotator writes:

- tier and family;
- UTF-8 start and end byte offsets;
- `actionable`, `licensed`, or `signal_only` decision;
- severity and a one-sentence reason;
- for gated terms, the licensing evidence span or the reason it is absent.

An adjudicator resolves differences before any lint run. Report binary
sample-by-tier Cohen's kappa and one-to-one span F1 between the two raw label
sets. Preserve raw labels, adjudication decisions, and adjudicator reasons.

The holdout labels are placed with a separate annotation owner after their
SHA-256 is recorded. The tuning owner receives only `samples.jsonl`, the
split, calibration labels, and the sealed holdout-label digest. Holdout labels
are revealed once the candidate lint and lexicons are frozen at a commit SHA.
Any later change creates `labelled-prose-v2`; it does not rewrite the v1 final
result.

### Matching and metrics

Match predicted and gold findings one to one within a sample and tier. A match
requires the same family and either exact offsets or token-span intersection
over union of at least 0.50. Choose the pairing with the greatest overlap so a
wide regex cannot claim several gold spans.

For each tier report TP, FP, FN, TN, precision, recall, F1, specificity, and
gold prevalence. Report the same counts by origin and represented family.
When a denominator is zero, write `null`; never substitute 0 or 1. Advisory
signals are excluded from defect metrics and get their own alert-yield count:
useful signals divided by all emitted signals.

The fixture is deliberately enriched for coverage. After blind annotation,
retain at least eight actionable gold spans and eight negative samples per
tier in the holdout. Refill a deficient stratum by continuing the deterministic
candidate order and repeat blind annotation. Report this enrichment, so nobody
reads the results as production frequency.

### Tuning rule

Run the untouched lint on calibration first and save `baseline.json`. A change
is allowed only for an adjudicated FP or FN in that report. Each change must:

- name the sample id, tier, family, and error class;
- alter the narrowest existing rule or code path that explains the error;
- add a small regression specimen derived from the calibration case without
  copying holdout text;
- keep all earlier tests green; and
- improve the affected calibration count without worsening another tier.

Do not add a family for a lone occurrence. Two independent examples with the
same move are required before a family or term expansion. After the last
calibration fix, freeze the code and lexicon hashes, reveal holdout labels, and
run holdout exactly once. A holdout error is reported; it is not tuned away in
this delivery.

## Design options

### Option 1: Extend the unit-test lists

Add more tuples to `TRUE_POSITIVES` and `FALSE_POSITIVES` and count successes.
This is small, but it repeats the current selection bias, has no origin
evidence, and cannot calculate misses when expected spans are absent from the
fixture format.

### Option 2: Import slopkit benchmarks

Vendor upstream JSONL and adapt its labels. The schemas and judge records are
useful prior art, but the data helped shape Imprimatur, is authored rather than
sampled from shipped Wildcat prose, and would add tens of thousands of bytes
without satisfying the held job.

### Option 3: Versioned Wildcat fixture and deterministic runner

Add the 64-sample JSONL fixture, blinded labels, group split, source verifier,
metrics runner, reports, and only calibration-backed lint changes. This is a
small new evaluation surface with explicit provenance and a real holdout.

### Option 4: Live GitHub sampling on every run

Fetch recent PRs and recalculate metrics in CI. This avoids checked-in text,
but mutable inputs make results irreproducible, network access becomes a test
requirement, provenance can change after labelling, and new text may contain
private or unsuitable material.

### Decision

Choose option 3 and deliver it in one Fiat implementation step. The fixture,
runner, any measured fix, report, tests, documentation, and evolution entry
belong to one acceptance boundary. Multiple PRs would expose holdout labels
before the candidate lint is frozen and repeat the full audit/prose/push cycle
without a separate usable result.

The step should first commit or record the sealed source, split, annotation,
and holdout-label digests; then run the calibration baseline; then make only
allowed fixes; then freeze hashes and reveal and run holdout once. The final PR
contains all inputs and outputs needed for later replay.

## Maturity decision

Advance Imprimatur once on the evolution axis when this frontier job completes.
If the criteria below hold, set `imprimatur-v2.1.0`, `Frontier status: mature`,
and `Next Fiat job: None -- mature`:

1. All 64 samples have valid immutable sources and affirmative origin evidence;
   both origins, both splits, all required genres, and group isolation pass.
2. No exact or near-duplicate crosses calibration, holdout, current tests,
   Imprimatur prose, or the pinned upstream specimens.
3. Both annotation passes are complete; sample-by-tier kappa and raw span F1
   are each at least 0.80 after reporting their exact denominators.
4. Holdout has at least eight actionable spans and eight negative samples for
   each scored tier.
5. Hard-tier precision and recall are 1.00. Gated and scored-structural
   precision and recall are each at least 0.90.
6. There is no missed critical finding, no family with two or more errors in
   the same direction, and no origin F1 gap above 0.15 when both sides have at
   least eight relevant cases.
7. Every lint change cites a calibration error and improves its measured count;
   no holdout-driven change occurs; all required tests pass.

If corpus validity, agreement, or tier coverage fails, keep the frontier open
and name one next job that supplies the missing evidence. If final holdout
misses a metric, keep it open and make the exact holdout error class the next
job; do not change v1 after seeing it. If all gates hold, another calibration
pass over the same evidence would be interchangeable work and Imprimatur
should close. A later model release, a newly observed family-level miss, an
origin-stratum regression, or another external requirement can reopen it by
the epoch rule in `VERSIONING.md`.

## Risk register seed

| Risk | Why it matters | Check or control |
| --- | --- | --- |
| Origin misclassification | Human account authorship can include model assistance. | Apply the user's pre-1-August-2025 rule with commit timestamp and default-branch reachability; require affirmative markers for model rows; quarantine later unmarked work. |
| Test leakage | Existing examples or copied docs would inflate results. | NFKC normalization, hashes, five-gram similarity, mirror groups, and group-before-split checks. |
| Selection from lint output | Choosing rows that current rules already find biases recall upward. | Select by provenance, genre, and fixed source hash before lint or labels are visible. |
| Annotator leakage | Seeing origin or lint output can shape labels. | Blind packets and preserve two independent raw label sets. |
| Ambiguous doctrine | Gated and structural decisions need judgement. | Record reasons and evidence spans; gate maturity on agreement. |
| Span matching inflation | One wide prediction could cover several labels. | One-to-one maximum-overlap pairing with family and tier equality. |
| Undefined metrics | A tier with no positive or predicted cases can look deceptively clean. | Emit `null`, print denominators, and require minimum holdout coverage. |
| Prevalence claim | An enriched fixture does not estimate live frequency. | Report enrichment and avoid population claims. |
| Tuning on holdout | Repeated peeking turns the holdout into training data. | Separate annotation owner, digest seal, frozen candidate commit, one reveal. |
| Rule expansion from one phrase | A single token can create broad false positives. | Require two independent calibration examples for family or term expansion. |
| Gated-window mismatch | JSON declares windows while code reads a whole sentence. | Treat as a review target; change only if labelled errors demonstrate harm. |
| Quote and code masking | Long quotations or Markdown forms may produce false positives. | Include represented negative cases from shipped prose and label actual use separately from mention. |
| Reproducibility drift | Mutable GitHub text or branch heads could change. | Pin commits and immutable URLs; verify hashes; keep normal evaluation offline. |
| Copyright or confidentiality | External or private prose may not be suitable for a public fixture. | Use small public Wildcat excerpts only and record source and licence. |
| Unrelated worktree state | `.agents/skills/sapheneia/` and `plugins/sapheneia/` belong to another task. | Exclude them from reads, writes, staging, tests, and PR scope. |

## Glossary seeds

- **Sample:** One immutable paragraph of shipped prose plus source and origin
  metadata.
- **Source group:** All samples introduced by the same PR, commit series, or
  copied text family; groups never cross the split.
- **Origin evidence:** For `human`, a pre-1-August-2025 public default-branch source
  under the user's rule or a separate attestation; for `model_assisted`, an
  affirmative agent marker. Later unmarked work is `unknown`.
- **Gold span:** An adjudicated byte range with tier, family, decision,
  severity, and reason.
- **Actionable:** A labelled use the lint should report as a defect.
- **Licensed:** A gated term whose local evidence makes it legitimate.
- **Signal-only:** An advisory structural or cadence observation excluded from
  defect precision and recall.
- **Calibration split:** The only labelled half available while changing lint
  code or lexicons.
- **Holdout split:** Source-isolated labels revealed once after the candidate
  implementation is frozen.
- **Leakage:** Shared text, source groups, annotations, or outputs that allow
  holdout knowledge to influence selection or tuning.
- **Precision:** Matched actionable predictions divided by all actionable
  predictions.
- **Recall:** Matched actionable predictions divided by all gold actionable
  spans.
- **Specificity:** Correct negative samples divided by all gold negative
  samples for a tier.
- **Alert yield:** Advisory signals judged useful divided by all advisory
  signals emitted.
- **Enriched fixture:** A deliberately balanced test set with enough positives
  and negatives to measure each tier, without claiming production frequency.
- **Mature:** No evidenced follow-on job remains after the pre-registered
  validity and metric gates hold.

## Sources

### Repository sources

- `AGENTS.md` and `plugins/hexaemeron/AGENTS.md` at
  `bcbaede047e746aec5573a31d70201275ee58533`.
- `plugins/hexaemeron/skills/imprimatur/SKILL.md`, `EVOLUTION.md`, `NOTICE.md`,
  all three reference files, all three lexicons, `scripts/imprimatur.py`,
  `scripts/hook_gate.py`, and `tests/run_tests.py` at that commit.
- `plugins/hexaemeron/skills/VERSIONING.md` and
  `plugins/hexaemeron/skills/fiat/references/push-discipline.md` at that
  commit.
- Installed Hexaemeron package
  `/Users/c0rtexzer0/.codex/plugins/cache/wildcat-labs/hexaemeron/1.0.0+codex.20260816145806/`,
  including the installed Fiat study reference and Imprimatur code and tests.
- `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl`, read without a
  controller transition.

### GitHub evidence

- [Wildcat Skills merged PR list](https://github.com/wildcat-finance/skills/pulls?q=is%3Apr+is%3Amerged).
- [Wildcat Protocol repository](https://github.com/wildcat-finance/wildcat-protocol).
- [Wildcat V2 Protocol repository](https://github.com/wildcat-finance/v2-protocol).
- [Wildcat documentation repository](https://github.com/wildcat-finance/wildcat-docs).
- [PR #48: Require Shoggoth provenance in Fiat](https://github.com/wildcat-finance/skills/pull/48).
- [PR #40: Lock a run for the length of a mutating command](https://github.com/wildcat-finance/skills/pull/40).
- [PR #41: Check the receipts against the world they describe](https://github.com/wildcat-finance/skills/pull/41).
- [PR #60: Cold-read repository prose](https://github.com/wildcat-finance/skills/pull/60).
- [PR #64: Rewrite and synchronise the plugin marketplace](https://github.com/wildcat-finance/skills/pull/64).
- [PR #77: Publish Fiat's installed controller proof](https://github.com/wildcat-finance/skills/pull/77).

### Upstream and evaluation references

- [ehmo/slopkit at `b33718bb9283c11b09567dc714f92d90ffb7bd16`](https://github.com/ehmo/slopkit/tree/b33718bb9283c11b09567dc714f92d90ffb7bd16),
  especially `skills/slopbeth/benchmarks/` and
  `skills/slopgent/benchmarks/`.
- [Scikit-learn precision, recall, F-measure support](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html).
- [Scikit-learn common pitfalls and data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
- [Unicode Standard Annex #15: Unicode normalization forms](https://unicode.org/reports/tr15/).
- [Datasheets for Datasets](https://arxiv.org/abs/1803.09010).
