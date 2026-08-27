# Imprimatur causal subject has no formula study

Assuming, unless corrected:

1. The target is `wildcat-finance/skills` at `main` commit `fc0374bcd2d4311a2ce7d1f710e6809e40f00c92`, checked out on the Fiat run branch `fiat/teach-imprimatur-the-causal-subject-has-no-formu`.
2. The user's phrase `because noun has no` names a syntactic family: causal `because`, an explicit noun phrase as grammatical subject, then `has no`. The report says this move delays comprehension even when its factual content is correct. The lint must diagnose the move; it must not call the sentence false.
3. The first implementation is deliberately narrow. It covers `because`, a punctuation-free subject of one to eight word tokens, and `has no`, including ordinary line wrapping. It does not infer equivalent meaning from `since`, `lacks`, `does not have`, or a standalone `has no` sentence.
4. A match is a medium structural defect in Imprimatur's normal three-pass mode. It is not a hard term, does not enter `--hard-only`, and does not change `hook_gate.py`.
5. The supplied specimen appears in two current public passages, `README.md:69-70` and `docs/how-to-help-shoggoth.md:93-94`. Both copies are in scope for a content-preserving rewrite.
6. The user-supplied specimen is new external evidence for a generation repair. It does not make the failed `labelled-prose-v1` result usable for tuning. That frozen fixture, its spent holdout, the `labelled-prose-v2` frontier revision, frontier digest `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4`, open status, and held next job remain unchanged.
7. The implementation remains standard-library Python and repository-owned JSON. No parser, model call, dependency, network read, or CI service is added.
8. Verified audit synopses are the reading view in this study. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited 0 at the starting ref and reported every committed synopsis equal to freshly rendered bytes. The study does not claim to have read the authoritative sources behind those verified views.

## 1. Problem statement

Imprimatur currently misses the exact text `because this repository has no checked Atlas hand-off for them`. A direct standard-input run at the starting ref reports score 100.0, zero defects, zero signals, and no family hit. The same wording ships in the root catalogue and the contributor guide. A reader found the formula by eye and explained the failure: the clause first makes the reader parse a subject as the possessor of an absence, then asks that absence to carry the causal relation. The sentence can remain true while taking longer to untangle.

The users are people reading Wildcat's public prose and contributors or agents who run Imprimatur before that prose ships. A working prototype adds one named structural family, reports the supplied specimen and bounded variants at their original line and column, keeps nearby direct constructions clean, and rewrites the two current public copies without losing the launch-support qualification.

The prototype is proved by all of these checks:

- `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` advances from the observed 112/112 baseline and passes positive, clean, quoted, wrapped-line, source-comment, and self-lint specimens for `causal_subject_has_no`.
- Sending the exact supplied specimen to `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py - --format json --max-defects 0` exits 1 and reports one medium structural `causal_subject_has_no` defect. The same command reports no such defect for `No checked Atlas hand-off exists for them, so they stay on the manual route.`
- `python3 -m unittest discover -s tests` and `python3 plugins/hexaemeron/tests/run_tests.py` pass. The root prose test proves the new family is active over mutable first-party prose rather than present only in a fixture.
- `rg -n -U 'because\s+this\s+repository\s+has\s+no\s+checked\s+Atlas\s+hand-off' README.md docs/how-to-help-shoggoth.md` returns no match after the rewrite. A content check still finds Cline, Roo Code, the manual route, and the absence of a built and checked Atlas hand-off in both passages.
- `python3 -m unittest tests.test_evolution_contract tests.test_version_propagation` proves the skill generation and Hexaemeron package copies agree while the held frontier fields remain unchanged.

These checks establish recognition and preserved repository behavior. They do not establish a universal reading-time claim or that prose without this family is easy to read.

## 2. Prior art

### Current repository behavior

`plugins/hexaemeron/skills/imprimatur/lexicon/structural.json` contains 14 structural patterns, three of them advisory signals. Each pattern owns a name, note, severity, and regular expression. `scan_structural()` in `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` compiles those expressions with multiline and, by default, case-insensitive flags, preserves line and column, and separates `signal_only` matches from scoring. That data-driven path already owns a bounded syntactic formula and needs no new scanner capability.

`plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` keeps named true positives beside a clean corpus and says a clean-corpus hit is a rule bug. Its current structural positives cover negation-correction formulae, while its clean cases protect quotations, technical referents, status reports, headings, and genuine lists. The new family belongs in both halves: several causal subject forms must report, and direct causal or non-causal absence statements must remain clean.

The exact public specimen occurs at `README.md:69-70` and `docs/how-to-help-shoggoth.md:93-94`. Both passages distinguish tested launch routes from the manual route. The rewrite therefore keeps three facts fixed: Cline and Roo Code are not presented as launch options, no Atlas hand-off for them has been built and checked, and the manual route remains available.

`plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md` already says rules belong to families rather than isolated tokens. `references/rewriting.md` says a rewrite locks facts and qualifiers before changing the surface. The new family follows those contracts: it names one grammatical move and gives direct rewrites rather than replacing one banned word.

### Last two merged pull requests

The last two merged pull requests that changed Imprimatur at the starting ref were read through their complete GitHub pull-request records:

- [PR #630, Read source comments in Imprimatur](https://github.com/wildcat-finance/skills/pull/630), merge `6a4ae7fb44ea7de21e2d63290e51a351d6547db9`, added source-prose extraction and advanced the skill to `imprimatur-v2.3.0`. Its `Carried forward` section states that nothing was unfinished. Full TypeScript and Solidity parser equivalence remains an explicit non-goal and is not reopened here.
- [PR #596, docs: refresh the Shoggoth collective map](https://github.com/wildcat-finance/skills/pull/596), merge `8e6480230a5f43c57aef4f9a6c52f4c602d86790`, refreshed public sibling boundaries in Imprimatur's skill prose without changing the checker. It records no unfinished Imprimatur work. This study keeps its marketplace boundary intact.

### In-scope audit evidence

The verified `audit/AUDIT_SYNOPSIS.md` view contains two Imprimatur labelled-prose rounds from 2026-08-18. Both retain `[missing legacy field: audit-schema]`, `[missing legacy field: covered]`, `[missing legacy field: not-checked]`, and `[missing legacy field: elenchus-verdict]`; those fields remain unknown. The recorded leads not pursued were authorship claims, population-prevalence claims, and tuning against the spent v1 holdout. This study accepts those limits. The new user specimen is a named generation requirement, not a reinterpretation of the failed corpus.

The verified `audit/rounds/fiat-503-imprimatur-1-read-comment-spans-in-source-fi.synopsis.md` view contains the source-extraction run. Its finding ids and statuses are:

- `S1-R1-01`, `S1-R1-02`: fixed in round 1.
- `S1-R2-01`, `S1-R2-02`, `S1-R2-03`, `S1-R2-04`, `S1-R2-05`, `S1-R2-06`: fixed in round 2.
- `S1-R3-01`, `S1-R3-02`, `S1-R3-03`, `S1-R3-04`: fixed in round 3.
- `S1-R4-01`, `S1-R4-02`, `S1-R4-03`: fixed in round 4.
- `S1-R5-01`, `S1-R5-02`, `S1-R5-03`: fixed in round 5.
- `S1-R6-01`, `S1-R6-02`, `S1-R6-03`, `S1-R6-04`, `S1-R6-05`, `S1-R6-06`, `S1-R6-07`: fixed in round 6.
- `S1-R7-01`, `S1-R7-02`, `S1-R7-03`, `S1-R7-04`, `S1-R7-05`, `S1-R7-06`: fixed in round 7.
- `S1-R8-01`, `S1-R8-02`, `S1-R8-03`: fixed in round 8.
- Step 2 round 1 records three `none` ids as clean for package metadata, proof accuracy, and the full step diff.

Every round in that view retains the same four missing legacy fields, so audit schema, Covered, Not checked, and Elenchus verdict remain unknown rather than inferred. Its repeated lead, full parser equivalence for TypeScript and Solidity, remains outside this change. The source mode, coordinate guarantees, input cap, and named extraction refusals are carried forward unchanged.

The verified `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` view records `F-01` through `F-09` as fixed and `F-10` as accepted. `F-10` preserves the fail-open hook escape hatches while distinguishing them from the explicit lint workflow. The current change respects that decision by leaving `hook_gate.py` and `--hard-only` alone. This view also retains the four missing legacy fields, which remain unknown. Its unpursued controller, symlink, concurrency, and machine-facing JSON leads do not touch this local structural rule.

### Organisation and outside work

No other Wildcat checker owns this prose formula. Vulgate may rewrite a diagnosed sentence while preserving its content, and Brevitas may later shape engineering prose, but Imprimatur owns recognition and the family name.

The upstream slopkit material named in `NOTICE.md` supplies the family and substitution-drift doctrine. The current absorbed structural set has no causal subject `has no` rule, so the new pattern is Wildcat-maintained rather than attributed to an upstream pattern.

External work supports caution, not a universal claim. Research on negative quantification reports extra processing work in its tested tasks, including [Testing two-step models of negative quantification](https://pmc.ncbi.nlm.nih.gov/articles/PMC11261742/). [When the truth is not too hard to handle](https://pmc.ncbi.nlm.nih.gov/articles/PMC3225068/) found that pragmatically licensed negation can be integrated without an inherent semantic penalty. The [GOV.UK Functional Standards writing style guide](https://www.gov.uk/government/publications/handbook-for-standard-managers/functional-standards-writing-style-guide) advises positive phrasing where it makes sense. None tests this exact English formula. The user report and repository specimens define the house rule; the external sources explain why its note must not claim that all negation is confusing.

## 3. Constraints and non-goals

The exact starting ref is `main` at `fc0374bcd2d4311a2ce7d1f710e6809e40f00c92`. The observed local tools are CPython 3.14.6, Apple Git 2.50.1, and GitHub CLI 2.96.0. The repository contract remains standard-library Python and its existing test entrypoints; these observed local versions are evidence for this study run, not new runtime pins.

The matcher must stay in `lexicon/structural.json` unless tests prove that the existing data path cannot express the bounded family. Its intended shape is equivalent to `\bbecause\s+(?:[\w'’-]+[ \t\r\n]+){1,8}has[ \t\r\n]+no\b` under the checker's existing case-insensitive multiline flags. The bounded word count and punctuation-free subject stop the expression at a local grammatical clause. The regular expression may be adjusted only to make the declared positive and clean matrix agree; changing the grammatical boundary requires an amended study.

The family name is `causal_subject_has_no`, severity is medium, and `signal_only` is false. The rule applies after the existing code and quotation masks, so quoted discussion stays exempt and source comments use their original coordinates. Scoring math, cadence, hard and gated families, source extraction, CLI options, and report schema do not change.

This is a generation change to `imprimatur-v2.4.0`. The generation row must preserve frontier status `open`, revision `labelled-prose-v2`, digest `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4`, current frontier text, and held next job byte for byte. The current Hexaemeron package is 1.6.5; the expected package at this base is the smallest repository-valid increment, 1.6.6, propagated to both plugin manifests, both marketplace entries, and version assertions. Integration must retain a newer compatible package version if `main` advances first.

`labelled-prose-v1`, its samples, labels, splits, reports, hashes, and holdout are immutable non-goals. This run does not build `labelled-prose-v2`, estimate prevalence, claim an authorship tell, generalise to every negative causal clause, or change prose outside the named current surfaces and Imprimatur's live rule documentation. Historical audits, delivered studies and runbooks, legal text, frozen evaluations, and vendored Pashov prose are never rewritten to make the new rule look retroactive.

Always: run the focused Imprimatur suite, the Hexaemeron suite, the root suite, evolution and version checks, the required tree lints, Imprimatur over every changed prose file, Brevitas where the repository requires it, and `git diff --check`. Prove the supplied specimen red on the parent and green on the fixed tree, preserve the frozen v1 bytes, and compare both public rewrites with their source facts.

Ask first: broaden the conjunction or verb family, change the medium severity, make the pattern advisory only, alter `hook_gate.py`, touch CI, add a dependency, change report or scoring interfaces, edit an evaluation fixture, or move the held frontier.

Never: weaken quote or source masking to force a hit, scan code as prose by default, rewrite a historical record to clear a later rule, edit vendored material, delete a clean-corpus guard, treat the user's report as population research, or claim a command ran when it did not.

## 4. Design options

### Option A: add exact phrases

Add the supplied sentence and a few close strings as hard terms. This is easy to implement but teaches tokens rather than the grammatical move. A change of repository name, object, or pronoun escapes it. Rejected because it would recreate the substitution problem Imprimatur's family model exists to prevent.

### Option B: use an unbounded causal expression

Add a pattern like `because.*has no`. It catches the specimen but can cross punctuation, clauses, list items, and paragraphs. It also gives a reviewer no local bound to reason about. Rejected because one distant `has no` could turn an unrelated causal clause into a defect.

### Option C: add one bounded structural family

Add `causal_subject_has_no` to `structural.json`. Match `because`, one to eight punctuation-free word tokens, then `has no`, with line wrapping allowed. Use medium severity and the normal defect path. Add direct positive and clean examples, a quoted example, a wrapped example, a source-comment example, and the supplied public sentence. Document two rewrite shapes: name the missing condition first, or name the actor and action that would supply it.

This is the chosen design. It uses the checker's existing data contract and gives a reader one short boundary. It trades away long, punctuated, and synonymous forms. That miss is accepted because the user supplied one precise grammatical family, while a broader block would need new calibration evidence.

### Option D: parse English clauses

Add a part-of-speech or dependency parser to identify noun phrases and causal attachments. This could recognise more variants, but it adds a model or package, versions an English grammar, and turns a local style rule into a new input and dependency boundary. Rejected because its installation and trust cost is larger than the requested detector.

## 5. Risk register seed

```risk-register
specimen-false-clean | the supplied causal clause entering the structural pass | the exact bytes and both line-wrapped public forms report causal_subject_has_no at original coordinates
cross-clause-false-hit | punctuation and another clause between because and has no | comma semicolon full-stop and second-clause controls remain clean
ordinary-absence-overreach | direct statements of absence outside the named causal formula | standalone has no, there is no, no item exists, and lacks forms remain clean
quotation-regression | quoted examples and rule documentation passing through masks | straight smart and inline-code quotations stay exempt under existing masking
source-mode-drift | a matching sentence inside supported source comments | one source-comment guard reports the original coordinate while code and string specimens remain blank
public-fact-loss | README and contributor-guide rewrites | Cline Roo Code manual route and unbuilt unchecked Atlas hand-off facts survive in both files
immutable-evaluation-drift | labelled-prose-v1 and its spent holdout | every fixture byte and recorded digest remains unchanged and no v1 metric is cited as tuning evidence
frontier-drift | Imprimatur generation and held labelled-prose-v2 fields | evolution tests prove v2.4.0 while revision digest status current frontier and held job remain byte-identical
historical-prose-rewrite | audit delivered-spec legal and vendored surfaces | the diff contains no style rewrite to an immutable or upstream-owned record
package-version-drift | Hexaemeron manifests marketplaces and root assertions | version-propagation tests report one agreed package value without changing the skill version meaning
```

The audit loop must cite every id as reviewed or not applicable. A clean focused suite alone does not settle the public-fact, immutable-record, or frontier risks.

## 6. Glossary seeds

- Causal subject has no: the bounded structural family `because` plus an explicit noun phrase plus `has no`.
- Subject: the grammatical possessor placed between the conjunction and `has no`, not the topic or affected person.
- Missing condition: the absent item, check, permission, record, or capability that actually explains the outcome.
- Direct rewrite: a sentence that leads with the missing condition or names the actor and action without making an inanimate subject possess an absence.
- Structural defect: a report about sentence form that asks for rewrite; it is not a claim that the sentence is factually false.
- Clean control: a nearby sentence that must produce no `causal_subject_has_no` defect.
- Spent holdout: the already opened v1 evaluation split that may be replayed for its published result but may not guide a new rule.

## 7. Sources

- User-supplied report in this run: `because this repository has no checked Atlas hand-off for them`, plus the explanation that the formula is accurate but disrupts comprehension.
- `README.md:69-70` and `docs/how-to-help-shoggoth.md:93-94`, the two current public specimens.
- `plugins/hexaemeron/skills/imprimatur/lexicon/structural.json`, the current 14-pattern structural data contract.
- `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, especially `scan_structural()`, `build()`, quotation masking, and source-prose dispatch.
- `plugins/hexaemeron/skills/imprimatur/tests/run_tests.py`, the 112/112 baseline, positive corpus, clean corpus, behavior checks, and self-lint.
- `tests/test_shipped_prose_lints.py`, the repository-wide mutable first-party prose gate.
- `plugins/hexaemeron/skills/imprimatur/SKILL.md`, `references/lexicon-rationale.md`, and `references/rewriting.md`, the diagnostic, family, and preservation contracts.
- `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` and `plugins/hexaemeron/skills/VERSIONING.md`, the current generation and unchanged held frontier.
- `plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/README.md`, the failed agreement and structural-coverage gates, spent holdout, and v2-only tuning rule.
- [PR #630](https://github.com/wildcat-finance/skills/pull/630), complete body and file list, plus merge `6a4ae7fb44ea7de21e2d63290e51a351d6547db9`.
- [PR #596](https://github.com/wildcat-finance/skills/pull/596), complete body and file list, plus merge `8e6480230a5f43c57aef4f9a6c52f4c602d86790`.
- `audit/AUDIT_SYNOPSIS.md`, `audit/rounds/fiat-503-imprimatur-1-read-comment-spans-in-source-fi.synopsis.md`, and `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, read only after the whole-set synopsis check exited 0.
- [Testing two-step models of negative quantification](https://pmc.ncbi.nlm.nih.gov/articles/PMC11261742/), tested processing cost for negative quantification.
- [When the truth is not too hard to handle](https://pmc.ncbi.nlm.nih.gov/articles/PMC3225068/), evidence that pragmatic licensing changes negation processing.
- [GOV.UK Functional Standards writing style guide](https://www.gov.uk/government/publications/handbook-for-standard-managers/functional-standards-writing-style-guide), external plain-language advice to phrase points positively when appropriate.

## 8. Signals, and the questions behind them

No retained telemetry is added. Imprimatur is a bounded synchronous lint, not an unattended service, so there is no three-in-the-morning operator question that needs a log, metric, trace, or alert. The immediate command report already answers the relevant local questions: which family matched, at which path and coordinate, with which severity, and whether the configured threshold was crossed. Tests assert those report fields rather than creating persistent signals. This answer cites `plugins/hexaemeron/skills/ephoros/SKILL.md`; it does not copy Ephoros's signal contract.

## 9. Boundaries, per capability

The existing capability boundary is caller-supplied prose entering repository-owned regular expressions. The value at risk is the accuracy and availability of the local diagnostic. The new pattern is fixed repository data, uses bounded repetition, receives already masked prose, and neither evaluates input nor turns it into a path, command, URL, or template. Positive and clean guards make a malformed or over-broad rule visible.

No new dependency, subprocess, network host, credential, secret, output file, or model-output boundary opens. Source paths retain their existing size, regular-file, UTF-8, and extraction controls; this change only sees the resulting prose view. The implementation must not alter those controls to make the specimen match. This answer cites `plugins/hexaemeron/skills/phylax/SKILL.md`; it does not restate Phylax's control catalogue.

## 10. The budget, or its absence

No product performance budget or speed claim applies. The selected expression has a fixed eight-token upper bound and runs inside the existing structural pattern loop. The change adds one pattern to a synchronous local lint and does not attempt an optimisation. No Metron before-and-after command is warranted; the focused and root commands in section 1 are correctness checks. If review finds input-size growth or backtracking outside the fixed bound, that is a new performance claim and must start with `plugins/hexaemeron/skills/metron/SKILL.md` before any optimisation.

## 11. The fail-closed posture

Implementation stops if the exact supplied specimen remains clean, the named family or medium severity is absent, a clean control reports, either public copy still contains the old phrase, any protected fact disappears, a frozen evaluation byte changes, or a frontier or package version check disagrees. The normal lint must exit 1 under `--max-defects 0`; a successful process with only an advisory signal does not satisfy this study. The hard-only hook remaining unchanged is intentional and is not evidence that the full lint passed.

The first guard is the exact user sentence added to the focused suite and observed failing on parent `fc0374bcd2d4311a2ce7d1f710e6809e40f00c92`. Each boundary in the risk register receives a neighboring positive or clean test. If an audit repair changes the matcher, its smallest reproducer must fail without that repair and pass with it before the full focused, Hexaemeron, and root suites run again. This follows `plugins/hexaemeron/skills/elenchus/SKILL.md`; the failure output and command are preserved rather than replaced by a nearby green test.

## 12. Decisions and their homes

The consequential choice is to make this exact bounded family a medium structural defect instead of a hard token, advisory signal, or general English parser rule. It affects normal lint exits and future public prose, so the `imprimatur-v2.4.0` generation row in `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` will record the user specimen, chosen boundary, rejected broad and parser options, frozen v1 exclusion, and unchanged v2 frontier fields.

`plugins/hexaemeron/skills/imprimatur/lexicon/structural.json` owns the executable family name, note, severity, and expression. `plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` owns the positive and clean examples. `plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md` owns the short human explanation and rewrite examples. `plugins/hexaemeron/skills/imprimatur/SKILL.md` needs only the user-visible statement that this causal absence formula is among the structural rewrites; it must not duplicate the expression.

The two public rewrites remain in `README.md` and `docs/how-to-help-shoggoth.md`. No repository-wide ADR, alert runbook, or new calibration artefact is warranted: the rule is local, reversible through its governed generation history, and introduces no public data format or cross-plugin interface. The expected Hexaemeron 1.6.6 package propagation is distribution metadata, not the home of the prose decision. This placement follows `plugins/hexaemeron/skills/hypomnema/SKILL.md` and avoids recording the same choice twice.
