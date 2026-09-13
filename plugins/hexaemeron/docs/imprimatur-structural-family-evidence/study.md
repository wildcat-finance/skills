# Imprimatur structural prose family evidence catalogue study

Assuming, unless corrected:

1. The deliverable is an evidence catalogue that labelled-prose-v2 (issue #422) can consume, not a lint change. `scripts/imprimatur.py` and the three lexicon files stay byte-identical, and no score, threshold or regex changes.
2. The catalogue covers every family headed in issue #1298. The issue body carries 42 `###` family headings with a `Disposition` line each, not the 39 the run brief quoted; the catalogue keeps all 42 and records the count.
3. Positive specimens are collected only for the 13 evidence targets the issue names: the five high-value families and the eight signal families. The other 29 rows carry the issue's boundary, disposition and rewrite, with specimens optional.
4. The specimen universe is the one labelled-prose-v1 used: public `wildcat-finance` repositories at a pinned default-branch head, plus merged pull requests and issues in `wildcat-finance/skills`. Prose from the 16 v1 source groups, Imprimatur's own files, and issue #1298 itself is excluded.
5. Python is the interpreter in `.python-version`, 3.14.6, with the standard library only. The checker adds no dependency.
6. `EVOLUTION.md` does not change. The catalogue is an evaluation fixture, not a generation of the lint, so the held frontier fields stay byte-identical.

## 1. Problem statement

Build one checked evidence fixture, `plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1/`, that records every candidate structural prose family from issue #1298 with its grammatical form, reader cost, content-preserving rewrite, boundary, disposition and evidence tier, and that binds shipped positive and negative specimens to each advancing family by source URL, commit, path, line range, byte span and text digest. A stdlib script, `scripts/check_family_evidence.py`, refuses a malformed row, a wrong digest, a span outside its text, a specimen annotated after lint output, a family below its tier minimum, or two positives that share a source group.

The user is the labelled-prose-v2 run under issue #422 and the Imprimatur maintainer who will decide which family earns a regex. Today they have the issue body and nothing checkable.

A working prototype means all of the following hold at the run's last step:

- `python3 plugins/hexaemeron/skills/imprimatur/scripts/check_family_evidence.py --fixture plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1 --report /tmp/family-evidence.json` exits 0 and the report lists 42 families, at least 2 independent positive and 2 negative specimens for each of the 5 high-value families, and at least 2 positive and 1 negative for each of the 8 signal families.
- `python3 plugins/hexaemeron/skills/imprimatur/scripts/check_family_evidence.py --fixture ... --verify-sources` exits 0 after replaying every specimen against its immutable GitHub object.
- `sha256sum plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/imprimatur/lexicon/*.json plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` prints the same digests as at `7d12d63e13fe193fcc1f8827b393f8aa51161731`.
- `git diff --stat 7d12d63e13fe193fcc1f8827b393f8aa51161731 -- plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1` prints nothing.
- `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` still reports `112/112 passed`, and `python3 -m unittest discover -s plugins/hexaemeron/tests -t plugins/hexaemeron -p test_imprimatur_family_evidence.py` exits 0.
- `python3 scripts/run_checks.py` exits 0 from the worktree root.

The demo path is the first command above followed by `python3 -c "import json; r=json.load(open('/tmp/family-evidence.json')); print(r['families'], r['below_minimum'])"`, which must print `42 []`.

## 2. Prior art

### In this repository

`plugins/hexaemeron/skills/imprimatur/SKILL.md` (version 2.3.0) describes the three tiers: hard terms in `lexicon/hard.json` (9 families, 248 terms), gated terms in `lexicon/gated.json` (4 families plus an allowlist and an abstract-noun list) and structural regexes in `lexicon/structural.json` (14 patterns, 3 of them `signal_only`, plus cadence thresholds). `scripts/imprimatur.py` (1,075 lines) applies each structural pattern with `re.I | re.M` unless `case_sensitive`, honours `allow_exact`, and separates `signal_only` hits from defects in `build()` at line 933. There is no field for a pattern without a regex: `scan_structural()` at line 801 reads `spec["regex"]` and a missing key raises.

`references/lexicon-rationale.md` gives the substitution-drift argument that families, not tokens, are the unit. `EVOLUTION.md` records `imprimatur-v2.3.0`, frontier revision `labelled-prose-v2` with SHA-256 `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4`, status `open`, and the held job: refill structural holdout coverage, obtain two fresh blind annotations at kappa and span F1 of at least 0.80, then calibrate and run one sealed holdout without tuning on v1.

`evals/labelled-prose-v1/` is the evaluator contract this catalogue must fit. Its `README.md` records 64 samples in 16 source groups, deterministic ordering by `sha256("imprimatur-labelled-prose-v1" || source_url || text)`, five-gram Jaccard duplicate rejection at 0.80, and the outcome: raw span F1 0.486772, kappa 0.644820, and only two structural actionable holdout spans. Its holdout is spent. `schemas/labels.schema.json` fixes the span record a v2 evaluator will read: `tier`, `family`, `start_byte`, `end_byte`, `decision`, `severity`, `reason`, with optional evidence bytes. `schemas/sample.schema.json` fixes the provenance record: `source_url`, `source_commit`, `source_path`, `source_start_line`, `source_end_line`, `text_sha256`, `source_group_id`, `origin`, `origin_evidence`. Two observations from running it at the starting ref: `evaluate_labelled_corpus.py --fixture . --validate-only` exits 1 and prints `candidate code or lexicon digest differs from freeze`, because the lint moved on to 2.3.0 after the v1 freeze; and `validate_annotation()` at line 219 refuses any family name absent from the current lexicon. A new family therefore cannot be labelled inside v1 without changing the lexicon, which the issue forbids. `tests/run_tests.py` passes 112 of 112 at the starting ref; `plugins/hexaemeron/tests/test_imprimatur_source_extraction.py` is the precedent for a unittest module discovered by the Hexaemeron suite.

### The last two merged pull requests

`git log --merges -- plugins/hexaemeron/skills/imprimatur` lists no merge commit, so the two were found with `gh pr list --state merged --search imprimatur`. Both bodies were read.

PR #630, merged 2026-08-26T02:08:49Z as `6a4ae7fb`, carried run 503 (source-prose extraction) into `main`. Its `Carried forward` section states that nothing is unfinished and that full TypeScript and Solidity parser equivalence is outside the contract, not a deliverable. Nothing from it is owed here.

PR #629, merged 2026-08-26T01:27:06Z as `8ffbc2ee`, was Step 2 of the same run: package version 1.5.10, proof document, and the statement that frontier revision, digest, status and held job #422 do not change. Nothing from it is owed here.

PR #678, "Flag indirect causal absence in Imprimatur", is later (merged 2026-08-27T18:02:24Z) but returns 404 because its author account is hidden (issue #1300), and it merged into the step branch `fiat/teach-imprimatur-the-causal-subject-has-no-formu`, which was deleted, so it is not on `main`. Its merge commit `1d2fd059cf6d1f6c4bf60600063c7e9961c1c8c2` was fetched by hash and read: the `causal_subject_has_no` entry in `structural.json` with a bounded separator regex and a `reject_masked_span` flag; the `evidence_text` comparison in `scan_structural()`; smart-single quotation masking; a 43-line rationale section; a study with four design options; and 230 lines of tests. Restoring it is issue #1314's job and a non-goal here. What this run carries forward from it is the shape of a family record: one bounded form, a named separator rule, two rewrite shapes (lead with the missing condition, or name the actor), and a list of neighbouring forms that must stay clean. Those become the `form`, `boundary`, `direct_rewrite` and negative-specimen fields of every row.

### Audit records

One in-scope source exists on `main`: `audit/rounds/fiat-503-imprimatur-1-read-comment-spans-in-source-fi.md`. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exits 0 from the worktree root, so the synopsis `audit/rounds/fiat-503-imprimatur-1-read-comment-spans-in-source-fi.synopsis.md` (schema `fiat-audit-synopsis/v1`, source SHA-256 `85680333092b7e587810a5ce5ca2b86fb07fd78e861ef7dd56fa5984b81fb197`, 9 sections) was read as the reading view; the source was not read. It holds 34 finding ids, `S1-R1-01` through `S1-R8-03`, every one `fixed in this round`, and a Step 2 round with none. Its legacy fields `audit-schema`, `covered`, `not-checked` and `elenchus-verdict` are each `[missing legacy field: ...]` and remain unknown. `Leads not pursued`: full parser-level validity for TypeScript and Solidity, outside the comment-extraction boundary. None of those findings touches structural families.

The audit record of PR #678, `audit/rounds/fiat-teach-imprimatur-the-causal-subject-has-no-formu.md`, exists only in the hidden merge commit and is not an in-scope source on `main`. Its first 80 lines were read directly from `1d2fd059` for context: rounds 1 to 5 on 2026-08-27, schema `fiat-audit-round/v2`, verdicts `passed`, `guarded`, `inconclusive`, `inconclusive`, `null`, findings `S1-R1-01`, `S1-R2-01`, `S1-R3-01`, `S1-R3-02`, `S1-R4-01` about separator handling across masked spans and smart quotation marks. Its lesson for this catalogue is that every regex boundary question in the issue's open question 4 turned into a real round there; the catalogue records the boundary as prose and specimens and leaves the regex to #1314 and v2.

### In the organisation and outside

Issue #422 holds labelled-prose-v2. Issue #1314 restores #678. Issue #1300 is the recovery record for the hidden numbers. Issue #1298's `carryover` block already names `restore-678 | duplicate | #1314`. `NOTICE.md` records that part of the lexicon is absorbed from slopkit (ehmo, MIT), and v1 pinned its specimens at `b33718bb9283c11b09567dc714f92d90ffb7bd16` for duplicate rejection. No search outside the repository and its issues was made for a labelled corpus of these grammatical families; none is claimed to exist or not exist.

## 3. Constraints and non-goals

Starting ref: `7d12d63e13fe193fcc1f8827b393f8aa51161731` on `main`. Toolchain: Python 3.14.6 from `.python-version`, standard library only; the Hexaemeron plugin at `1.6.27` supplies the Protasis and Imprimatur checkers. Issue #1298 carries `Fiat-Required: 1`.

Ruled out by the issue: any regex, any score or threshold change, any change to the three lexicon files, and any tuning against the spent v1 holdout. Ruled out by ownership: restoring `causal_subject_has_no` (#1314), the v2 annotation, kappa and sealed holdout (#422), and a version row in `EVOLUTION.md`. Deferred past the prototype: specimens for the 29 non-target rows beyond what falls out of negative collection, a parser-backed cadence family (`heavy_preverbal_subject`, `sentence_stutter`), and a reference-integrity check for `deictic_here`.

Counting note. The run brief said 39 families. The issue body has 42 `###` headings that each carry a `Disposition` line: 8 causal, 5 hidden-actor, 6 verb-shell, 12 hedge-and-emphasis, 11 existential-and-scope. The catalogue keeps 42 and records this count in its README. The five items under "Ideas that do not yet form a family" are listed in the README, not as rows.

Boundaries this run states:

- Always: run `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py`, the Hexaemeron suite and `python3 scripts/run_checks.py` before a commit; run the Imprimatur lint on the README, this study and the runbook; verify every specimen digest against its immutable source before the fixture is committed.
- Ask first: adding any dependency; changing a v1 schema or any v1 byte; adding a field to `structural.json`; widening the specimen universe beyond public Wildcat prose; touching CI or `tests/check-map-v1.json` beyond registering the new fixture path.
- Never: write a regex for a catalogued family; change a score; read v1 holdout labels while choosing specimens; commit a specimen whose text cannot be re-fetched from a pinned commit; claim the checker or a suite ran when it did not.

## 4. Design options

Four candidates were probed under `.hexaemeron/design-probe/`, each with one family (`causal_fact_clause_wrapper`), one positive and one negative specimen, a well-formed and a malformed variant, and the check command that candidate would ship with. `measure.py` in that directory produced every value in the record; the reports under `.hexaemeron/reports/` carry the command and exit for each cell.

### Option A: `jsonl-fixture` (selected)

A new fixture directory beside v1 with `families.jsonl` (one row per family), `specimens.jsonl` (one row per specimen), two JSON schemas, a README, a stdlib checker and a unittest module. The trade: it is the largest of the four in bytes (2,481 bytes for the one-family probe against 826 for Markdown) and adds a script and a test file to maintain. In exchange it is the only candidate that passes every selection gate: the lint and v1 bytes stay unchanged, its checker exits 0 on the well-formed probe in 76 ms, refuses the malformed row and a half-written file, and carries the `family`, `tier`, `start_byte`, `end_byte` and `text_sha256` fields the v1 labels and sample schemas already use.

### Option B: `markdown-reference`

One Markdown catalogue under `references/`, checked by the Imprimatur lint alone. Smallest and quickest to write. It fails three gates: the lint accepts a section that lacks its rewrite and specimens (`malformed-row-refused` false), accepts the file cut in half (`truncated-file-refused` false), and offers a v2 evaluator no byte span or digest to read (`v2-span-fields` false). It stays as the prose form of what the README will say about each family.

### Option C: `extend-v1-fixture`

Add the new families as extra label rows and schema values inside `labelled-prose-v1`. Its probe added 204 bytes. It fails two gates: its target paths are inside the sealed v1 directory (`v1-fixture-unchanged` false), and its own check, `evaluate_labelled_corpus.py --validate-only`, exits 1 on the well-formed probe with `candidate freeze mismatch for labels.jsonl` (`check-passes-wellformed` false). The evaluator also refuses a family name absent from the lexicon, so this option needs a lexicon change the issue rules out.

### Option D: `structural-json-entries`

Add regex-free candidate entries to `lexicon/structural.json`. It fails three gates: its target is the lexicon (`lint-bytes-unchanged` false); `scan_structural()` raises on an entry without `regex`, so the shipped lint cannot load it (`check-passes-wellformed` false); and an entry carrying a broken regex is reported to stderr and skipped rather than refused (`malformed-row-refused` false).

### The record

`.hexaemeron/design-evidence.json` holds four candidates, nine criteria and 36 cells. Eight selection criteria: six boolean gates (`lint-bytes-unchanged`, `v1-fixture-unchanged`, `check-passes-wellformed`, `malformed-row-refused`, `v2-span-fields`, `truncated-file-refused`) and two comparative metrics (`probe-bytes`, `check-ms`). One conformance gate, `two-independent-specimens`, a count of at least 2, is pending for every candidate and blocks `integration`; its resolver for the selected candidate is the shipped checker with `--min-independent-positive 2 --tier high-value`. After the gates, `jsonl-fixture` is the only eligible candidate, so the frontier has one member and the rule is `unique-frontier`. `design_evidence.py --transition design-lock` exits 0.

### The selected design in detail

Files:

- `evals/structural-family-evidence-v1/README.md`: selection rules, universe, exclusions, tiers, minimums, the 42-family count, the five non-family observations, and the commands.
- `evals/structural-family-evidence-v1/families.jsonl`: 42 rows with `family_id`, `group`, `evidence_tier`, `form`, `reader_cost`, `direct_rewrite`, `boundary`, `disposition`, `overlaps`, `discovery_phrases`, `minimum_positive`, `minimum_negative`, `source_issue`. Wording of `form`, `reader_cost`, `direct_rewrite`, `boundary` and `disposition` is copied from the issue body.
- `evals/structural-family-evidence-v1/specimens.jsonl`: one row per specimen with `specimen_id`, `family_id`, `tier` (always `structural`), `family`, `polarity`, `decision` (`actionable`, `signal_only`, `negative`), `text`, `text_sha256`, `start_byte`, `end_byte`, `reason`, `rewrite`, `repository`, `source_url`, `source_commit`, `source_path`, `source_start_line`, `source_end_line`, `source_object`, `source_group_id`, `origin`, `annotated_before_lint`, `selection_seed`, `selection_rank_within_group`.
- `evals/structural-family-evidence-v1/schemas/family.schema.json` and `specimen.schema.json`, checked by the same hand-written `validate_schema()` style v1's evaluator uses.
- `scripts/check_family_evidence.py`: exits 0 on a clean fixture, 1 on any finding, 2 on bad invocation; opens no socket unless `--verify-sources` is given; writes one JSON report with `--report`.
- `plugins/hexaemeron/tests/test_imprimatur_family_evidence.py`: one test per refusal plus a clean-fixture test and a self-check that the lint and v1 digests equal the frozen values recorded in the fixture README.

Evidence tiers and minimums: `high-value` (5 families: `causal_subject_has_no`, `causal_fact_clause_wrapper`, `reason_is_because`, `empty_expletive_case`, `redundant_connective_pair` adversative form) need 2 independent positives and 2 negatives; `signal` (8 families: `stacked_epistemic_modal`, `causal_negative_passive`, `purpose_periphrasis`, `agentless_choice_passive`, `litotic_double_negative`, `attention_adverb_opener`, `backward_demonstrative_cause`, `existential_relative_shell`) need 2 positives and 1 negative; `boundary`, `existing-family` and `future` rows need none. Independence means distinct `source_group_id`, derived as in v1 from repository and document.

Specimen selection: candidate paragraphs come from the v1 universe minus the exclusions in assumption 4, discovered by the per-family `discovery_phrases` recorded in `families.jsonl`, ordered by `sha256("imprimatur-structural-family-evidence-v1" || source_url || text)`, and taken in that order until the tier minimum is met. The annotator records span, decision and rewrite before running any lint; the current lint has none of these families, so it could not fire anyway, and `annotated_before_lint` records the protocol. Every rejected candidate is written to `selection-rejections.jsonl` with its reason. Discovery by phrase is a bias the README states: it finds the issue's forms, not the forms the issue missed.

The issue's open question 3 is answered in the row for `agentless_choice_passive`: it stays `signal`, and decision ownership remains Hypomnema's record-level rule; the catalogue cross-references that contract and adds no enforcement.

## 5. Risk register seed

```risk-register
lint-bytes-drift | scripts/imprimatur.py and the three lexicon files | digests equal the starting-ref values in every step and the fixture README
v1-bytes-drift | evals/labelled-prose-v1 and candidate-freeze.json | git diff against the starting ref prints nothing for that directory
holdout-leak | v1 holdout source groups and labels during specimen selection | no specimen shares a source group with any of the 16 v1 groups and no v1 label file is opened by the collector
specimen-provenance | source_url commit path and lines of every specimen | verify-sources replays each immutable object and the text digest matches
span-integrity | start_byte and end_byte against text | span is inside the UTF-8 bytes splits no codepoint and is non-empty
independence | two positives for one family | distinct source_group_id or the checker refuses
annotation-order | annotated_before_lint on every specimen | the field is true and the README protocol names when lint may be run
issue-wording | form reader_cost direct_rewrite boundary disposition copied from #1298 | a test compares each field with the recovered issue body text
partial-write | families.jsonl and specimens.jsonl during collection | a truncated file is refused and the collector writes to a temp file then renames
fetch-boundary | the collector reading github.com | only gh with pinned commits during the build step and never from the checked-in checker without --verify-sources
family-count | 42 rows against the issue body | a test counts the level-three headings with a Disposition line in the recovered issue text
untrusted-text | specimen text from public repositories | treated as bytes never executed never interpolated into a shell
```

The audit loop must cite every id as reviewed or not applicable. A green checker alone does not settle `holdout-leak`, `annotation-order` or `issue-wording`, which are protocol claims a round has to read.

## 6. Glossary seeds

- family: one grammatical move with a stable kebab-or-snake id, as in `structural.json` and issue #1298.
- specimen: one shipped paragraph with a byte span that shows a family (positive) or its nearest legitimate neighbour (negative).
- evidence tier: `high-value`, `signal`, `boundary`, `existing-family` or `future`, fixing the specimen minimum per row.
- independent: two specimens with different `source_group_id`.
- discovery phrase: a literal string used to find candidate paragraphs, recorded so the bias is visible.
- v1 universe: public `wildcat-finance` default-branch prose and merged skills PRs and issues, as defined in the v1 README.
- source group: repository plus document, the unit v1 splits on.
- verify-sources: the optional online replay of each specimen against its immutable GitHub object.

## 7. Sources

- Issue #1298, body recovered at `2026-09-06` via `gh issue view 1298 --repo wildcat-finance/skills --json body`.
- Issues #422, #1300, #1314 in `wildcat-finance/skills`.
- PR #630 and PR #629 bodies via `gh pr view`; PR #678 via `git fetch origin 1d2fd059cf6d1f6c4bf60600063c7e9961c1c8c2` and `git show`.
- `plugins/hexaemeron/skills/imprimatur/SKILL.md`, `EVOLUTION.md`, `NOTICE.md`, `lexicon/structural.json`, `lexicon/hard.json`, `lexicon/gated.json`, `references/lexicon-rationale.md`, `scripts/imprimatur.py`, `scripts/evaluate_labelled_corpus.py`, `tests/run_tests.py`.
- `plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/README.md`, `study.md`, `schemas/*.json`, `split.json`.
- `audit/rounds/fiat-503-imprimatur-1-read-comment-spans-in-source-fi.synopsis.md` and the synopsis currency check.
- `AGENTS.md` sections "Issue queues", "What every issue body decides", "Written-record publication", "Checks for changes to this repository".
- `.hexaemeron/design-probe/measure.py`, the four `probe.json` files, and `.hexaemeron/reports/*.json`.
- Protasis `SKILL.md` 5.10.0 and Imprimatur `SKILL.md` 2.3.0 in the Hexaemeron 1.6.27 plugin cache.

## 8. Signals, and the questions behind them

None as unattended telemetry, and here is why: the checker runs from a terminal or a test, finishes in under a second, and nothing here runs on a schedule or serves a request. The one question a later run will ask is "which families still lack their minimum, and why was each candidate rejected", and the `--report` JSON answers it with `families`, `below_minimum` (family id, tier, counted positives, counted negatives) and a pointer to `selection-rejections.jsonl`. [ephoros](../../skills/ephoros/SKILL.md) owns what a signal must carry; no event, metric or alert is added.

## 9. Boundaries, per capability

Two boundaries open. First, the build-step collector reads prose from github.com through `gh` at pinned commits; what is worth taking there is a wrong or moved paragraph, and the control is that every specimen carries `source_commit` and `text_sha256`, `--verify-sources` replays them, and the checked-in checker opens no socket by default. Second, specimen text is untrusted bytes from public repositories; the control is that the checker never executes, evaluates or shell-interpolates it, caps each JSONL file at 1,048,576 bytes, refuses symlinks, and resolves paths only below the fixture directory. No secret, subprocess or model output is involved. [phylax](../../skills/phylax/SKILL.md) owns the boundary list and the controls; ids `fetch-boundary`, `untrusted-text` and `partial-write` in item 5 are the audit hooks.

## 10. The budget, or its absence

One budget: `/usr/bin/time -p python3 plugins/hexaemeron/skills/imprimatur/scripts/check_family_evidence.py --fixture plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1` must report `real` under 2.0 seconds on the full 42-family fixture. The probe baseline is 76 ms for one family and two specimens (`.hexaemeron/reports/jsonl-fixture-check-ms.json`). `--verify-sources` is network-bound and carries no budget. [metron](../../skills/metron/SKILL.md) owns how the number is taken and re-taken.

## 11. The fail-closed posture

The checker exits 1 on the first finding class it meets and prints every finding of that class; exit 2 on a bad path, an oversized file, a symlink or an unreadable JSON line. A pending or missing specimen is a finding, not a warning. When a fix is needed the guard follows [elenchus](../../skills/elenchus/SKILL.md): reproduce with the exact fixture bytes, reduce to one row, and add `test_refuses_<condition>` to `test_imprimatur_family_evidence.py` so it fails without the fix. Every step of the runbook names that module as its Elenchus runner with one `{report}` argument.

## 12. Decisions and their homes

Three decisions are expensive to reverse once v2 reads the fixture: the fixture location and the two row schemas; the specimen selection rule, seed and universe; and the tier minimums. Each is recorded in `evals/structural-family-evidence-v1/README.md`, which is where v1 put the same three decisions, and [hypomnema](../../skills/hypomnema/SKILL.md) says to match what is already there. A fourth decision, leaving `EVOLUTION.md` byte-identical because no lint generation changes, is recorded in that README's opening paragraph and cited from the runbook's Step 1. No ADR under `docs/decisions/` is added: v1 earned none, and the fixture's README is the interface its consumer reads.
