# Study: Forward-test Brevitas across a held engineering corpus

Assuming, unless corrected:

1. The build starts from `main` at `2e2608aa2ac62c5d556478e7f93186fddc36dce3`; the run branch and `origin/main` were at the same commit when this study was written.
2. Every Python command uses the repository pin, Python 3.13.15, through `mise exec python@3.13.15 -- python3`. The ambient Python 3.12.3 is not evidence for this run.
3. “Across a held engineering corpus” means a committed, digest-bound set that covers the `x-ray`, `solidity-auditor`, `gas`, `invariant`, and `diff-review` prose families. “Cross-model” means at least two explicitly recorded provider/model identities in each family, for a minimum of ten qualifying outputs. Existing cases without that provenance may remain as historical regressions, but do not count toward this criterion.
4. Model output is captured once, reviewed, sanitised, and committed as a fixture. No live model call, network access, credential, session identifier, or hidden reasoning belongs in a test run or release artefact.
5. Candidate source material may be copied only as bounded, redistributable excerpts after a licence and secret review. The adjacent `wildcat/mono` checkout is prior art and a possible source pool, not an authorised write target.
6. This job may change Brevitas prose, fixtures, its standard-library Python runner and linter, tests, audit records, and marketplace statements. It does not author Solidity or change another skill's governed behaviour.
7. The existing Brevitas rules remain the specification. A held output may reveal a confirmed bypass or false positive, but output frequency alone is not authority to weaken evidence precedence or rewrite a rule.
8. The Solidity security suite is waived because the planned change has no Solidity production surface. Fiat's per-step audit loop, pinned Python checks, prose checks, and repository contract checks still apply.

## 1. Problem statement

Brevitas currently has 21 unit tests and three digest-bound evaluation cases. All pass, but the evaluation set covers only three named examples, carries no enforceable engineering-family or model-provenance coverage, and can express only “compress” or “retain evidence.” It therefore cannot prove the held frontier recorded in `plugins/brevitas/skills/brevitas/EVOLUTION.md`: forward-testing across held `x-ray`, `solidity-auditor`, `gas`, `invariant`, and `diff-review` outputs from more than one model, followed by regression coverage for every confirmed structural bypass.

The prototype is for maintainers who change Brevitas rules and reviewers who need to know what those rules do to real engineering prose. It will add a closed-schema held corpus and a deterministic offline runner, classify expected results before rule repair, preserve named evidence spans, and make each confirmed bypass reproduce as a red test before the smallest corresponding fix. A clean held case remains valuable: it proves a specific accepted output at a fixed digest, not universal correctness. A corpus with no confirmed bypass must report zero rather than manufacture a rule change.

The demo path is:

```bash
mise exec python@3.13.15 -- python3 plugins/brevitas/skills/brevitas/scripts/run_evals.py
```

The command must exit zero and report all five families, at least two explicit provider/model identities per family, no unclassified case, no stale digest, no expectation drift, no missing protected evidence, and the result of every confirmed-bypass regression. The repository's Brevitas unit suite, root suite, marketplace-prose suite, Imprimatur check, and Brevitas source-aware check must also exit zero. These are corpus-scoped claims; the demo must not call itself an exhaustive model or prose assessment.

## 2. Prior art

### Current Brevitas implementation

`plugins/brevitas/skills/brevitas/SKILL.md` defines evidence precedence and structural rules for direct answers, findings, fences, tables, headings, qualifiers, and process prose. `scripts/brevitas.py` implements those rules without a third-party runtime dependency. Its source comparison mechanically protects transaction hashes, addresses, `file:line` references, and numeric tokens. Concrete counterexamples, ordered reproduction steps, and explicit limits on what was established are protected by policy and review, but not yet by a source-bound corpus field.

`scripts/run_evals.py` checks each current case's `origin_sha256`, lints its target against the source, requires shorter output for `compress`, and requires exact original retention for `retain-evidence`. The three cases are `fund-safety-evidence-exception`, `solidity-partial-recovery`, and `xray-replay-authority`. The runner has no negative expectation, no exact diagnostic expectation, no family/model coverage check, and no closed provenance schema. Pinned baseline evidence on 2026-08-27 is 21/21 unit tests and 3/3 evaluation cases passing.

The repository-wide Brevitas study at `docs/brevitas-repository-pass/study.md` and its runbook at `docs/brevitas-repository-pass/runbook.md` record the previous broad pass: 159 source files, 43 exclusions, 29 protected passages, and four digest refusals. That pass established that the source-token check is narrower than the full evidence-precedence promise and that a person still owns counterexamples, reproduction order, and establishment limits. It also records a host-contract boundary: short required audit tables and completeness-oriented specifications must not be padded or flattened merely to satisfy presentation rules.

`plugins/brevitas/skills/brevitas/EVOLUTION.md` is open at `brevitas-v0.2.0`, revision `held-engineering-corpus`. The initial frontier digest is `a087712...`; the exact ledger bytes, rather than this abbreviation, remain authoritative. The previous generation removed B008 after eight observed fence hits produced no surviving defect and widened the B006 fence cap from 15 to 40 after three hits produced one surviving defect. That is direct precedent for corpus evidence preceding a rule change.

### Pull requests

The last two merged pull requests that changed the Brevitas plugin were read before choosing a design:

- [PR #673](https://github.com/wildcat-finance/skills/pull/673), merged as `f4627a766...`, pinned the suite to Python 3.13 and centralised the workflow. It leaves no recorded unfinished Brevitas behaviour work. This study therefore uses the exact 3.13.15 repository pin.
- [PR #661](https://github.com/wildcat-finance/skills/pull/661), merged as `a241b0f...`, extracted shared repository-wide plugin-contract invariants while preserving plugin-local failure reporting. It leaves no recorded unfinished Brevitas behaviour work. The held-corpus runner should stay plugin-local while the shared contract suite remains a release gate.

Earlier behaviour-bearing prior art remains relevant: [PR #113](https://github.com/wildcat-finance/skills/pull/113) removed B008 and widened B006 from measured false-positive evidence; [PR #91](https://github.com/wildcat-finance/skills/pull/91) introduced the skill, linter, unit suite, and three evaluations; [PR #93](https://github.com/wildcat-finance/skills/pull/93) compressed the public Brevitas prose without changing its audit pointer. None supplies the missing five-family cross-model corpus.

### Audit evidence

The whole-set synopsis check ran from the target root under Python 3.13.15 and exited zero:

```bash
mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

The authoritative in-scope source is `audit/AUDIT.md`, 14,079 lines with source SHA-256 `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`. Its committed, fresh reading view is `audit/AUDIT_SYNOPSIS.md`, 425 lines with SHA-256 `b9fe6925729395a72433e0f5918ddba785cc1905b2acc8926a94a6a23b1bc6e6`. The synopsis exposed legacy omissions, so the three Brevitas records were also read in the source at `audit/AUDIT.md:842` onward. There is no existing per-run record at `audit/rounds/fiat-374-forward-test-brevitas-across-a-held-engineer.md`; Fiat will create that record during implementation.

- `Repository-wide Brevitas pass, step 1, round 1` established one low finding: a structural rewrite changed the historical mechanism from “could raise uncontrolled type errors” to “permitted uncontrolled type errors.” The fix used “exposed” for the first mechanism and retained the separate qualified error-response claim. The round checked both parsers, compact-list fixtures, the 159-file inventory, 43 exclusions, 29 protected passages, four digest refusals, and the committed study and runbook. No other open finding was established. The finding has no stable id in the legacy record and its recorded status is fixed.
- `Repository-wide Brevitas pass, step 1, round 2` re-read the mechanism and both parsers, then reported no open finding and status clean. Root 22/22, Hexaemeron 62/62, Imprimatur, Brevitas with `--source`, protected SHA verification, and `git diff --check` passed.
- `Repository-wide Brevitas pass, step 2, round 1` reviewed five changed prose files, the compact-history parser, frontier digest `dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62`, and refusal digests `08e534ff9fd8005778e2224f374bd1e42a4bb129c2504e8aa54549f8621f0494`, `2cdd9bb04532ec278184d2a3290a0b0b72c02be47ca634911428440ddbed6d58`, and `ed8fbcf14186a1c79f9db8f971796d192969ec729edeb2bba0fc78f30ff75e48`. It reported no open finding and status clean; root 22/22, Brevitas 13/13, evals 3/3, Agent Skills validation, Imprimatur, source-aware Brevitas, protected SHA verification, and `git diff --check` passed.

For all three legacy Brevitas rounds, `Audit schema`, `Covered`, `Not checked`, and `Elenchus verdict` are absent; they remain unknown rather than inferred. The first two do not state `Leads not pursued`; the third also supplies no such field. No open lead is manufactured from that silence. Separately, later audit records show B011 firing on required two-column rule and audit tables, and B010/B001 firing on short Protasis runbooks. Those are boundary evidence, not in-scope Brevitas findings: host-required structure and completeness specifications keep their own authority.

### Held engineering material in the organisation

Read-only inspection found candidate material in `/home/kethcode/wildcat/mono`. The checkout has user-owned changes and will not be modified. The candidate files and their observed digests are:

- x-ray: `v2-protocol/x-ray/x-ray.md`, SHA-256 `865a5427d8992080ba49c6becfb003faf7bd250a2032202610dc5e6f9af2b2e5`;
- `invariant` family report: `v2-protocol/x-ray/invariants.md`, SHA-256 `c0d167b6f9bc86303926a3c019b5c32b7d1dac9ee60e1c41d31e269358316be4`;
- gas: `v2-protocol/docs/gas-optimization-sweep.md`, SHA-256 `ae3c50d2746e7b4523321d230ffabb78d77b8fea3b1e37a78ce80b465dc5947d`;
- diff review: `kb/workstreams/v2.6/V2_PROTOCOL_PR124_DIFFERENTIAL_REVIEW_2026-08-14.md`, SHA-256 `1bc67f7bc2b955d93bccb6dae8d52dd2da3fd2cecbfd3d9efaddbf62510f91e9`;
- gas source and reviewed output: `kb/workstreams/v2.5/GAS_OPTIMIZATION_SWEEP_FULL_2026-08-21.md`, SHA-256 `ed414a9630a726c7e67bf74254b45c4c4d1de2a1fb6f91450e9fdd245d5804ac`, and `GAS_OPTIMIZATION_REVIEWED_FINAL_2026-08-21.md`, SHA-256 `03606c2d96e5eda9bc45a4ccdd44490e6d3a56a8819c36b791a7e1793b943782`.

A pinned exploratory lint, which is not a semantic classification, produced B023 on the x-ray, B027 on `v2-protocol/x-ray/invariants.md`, B011 on two gas/diff-review tables, many B023 findings in the differential review, and no finding on the full gas sweep. This establishes that the source pool contains both accepted and rejected syntax. It does not establish a bypass: a reviewer must first classify whether each bounded specimen violates a Brevitas rule.

The commits name a human author but carry no reliable model identity. Collective authorship is not model provenance. These documents may supply public engineering inputs or bounded examples after review, but cannot count as cross-model outputs unless a capture manifest records the provider, full returned model identifier, client version, prompt/source digest, and response digest. There is no held Solidity-auditor output with proven cross-model provenance in the material read. That is the remaining evidence gap the capture step must close.

### Outside practice

[CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/) and the [GitHub Flavored Markdown specification](https://github.github.com/gfm/) define parseable Markdown and table syntax, not evidence precedence or engineering-output budgets. [markdownlint custom rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/CustomRules.md) show a named-rule and structured-finding pattern; [Vale](https://vale.sh/docs/) supplies prose-style linting precedent. Neither binds a revised answer to source evidence.

OpenAI's [evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) recommends task-specific cases drawn from a real distribution, typical and edge cases, continuously growing datasets, human calibration, and deterministic classification where possible. The applicable part here is the dataset method, not a hosted product dependency or a model judge. Brevitas can keep the runner offline and use human classification only to establish a fixture's expected result.

## 3. Constraints and non-goals

The base ref and interpreter are fixed by assumptions 1 and 2. Keep the runner on Python's standard library, use repository-relative fixture paths, cap every file read, and produce stable sorted diagnostics. Preserve existing case ids or provide an explicit migration that proves all three original cases still run. Do not relax the source-token checks while adding stronger protection for evidence spans.

Always run the pinned focused suites before each step is declared green; run Imprimatur on prose that ships; run Brevitas with its source where the prose is a compressed derivative; retain raw expected/actual diagnostics in the audit record when a case fails; and compare changes with the step entry ref.

Ask first before adding a dependency, a networked CI job, a public file format outside the plugin, a new model provider, a paid capture, or source material whose licence or sensitivity is uncertain. Ask first if a confirmed result requires changing another skill's mandated document shape.

Never infer model identity from a Git author, filename, tool nickname, or prose style. Never commit credentials, session metadata, hidden chain-of-thought, private prompts, or unreviewed proprietary source. Never delete a failing case to make the suite green, relabel a false positive as a bypass, claim a model call ran in CI, or claim that corpus coverage proves universal correctness.

Deferred beyond this prototype are statistical model-quality scoring, live provider comparisons, automatic semantic judging, a general Markdown parser rewrite, repository-wide automatic formatting, performance optimisation, and changes to other skills' output contracts. The exact successor frontier is also deferred until the held corpus produces evidence; the ledger must not preselect one.

## 4. Design options

### Option A: manual one-time sweep

Run Brevitas over a folder, review the output, and add unit tests only for remembered defects. This has the smallest immediate diff, but loses model/source provenance, clean examples, classifications, and negative evidence. A future reviewer cannot reproduce the coverage claim. It does not meet the held requirement.

### Option B: manifest-driven held corpus and deterministic runner (chosen)

Commit bounded source/output fixtures with a closed manifest. Each qualifying case records a stable id, one of the five families, explicit provider and full model identity, capture client/version, source and prompt digests, original/output digest, expected outcome, expected sorted diagnostic codes, and protected evidence spans. The runner validates schema, paths, digests, coverage, classifications, results, and evidence retention without a network call. Reviewers classify fixtures before comparing them with the current linter. Every confirmed bypass first becomes a failing regression; the smallest rule repair follows.

This is the cheapest construction that makes the frontier claim reproducible. Its cost is repository weight and deliberate fixture curation. Bounded excerpts, byte ceilings, a licence/secret gate, and digests contain that cost. Exact model provenance makes capture work explicit, but avoids a false cross-model claim.

### Option C: live model matrix in CI

Call multiple providers on every run and lint fresh answers. This exercises current services, but adds secrets, cost, network availability, provider drift, nondeterministic responses, and a moving model alias. A failure cannot distinguish linter drift from model drift. It is unsuitable as the acceptance path; one-time capture may use model clients only at the controlled ingestion boundary.

### Option D: replace the line parser with an AST or model judge

A full Markdown AST could improve syntax handling, and a model judge could attempt semantic evidence checks. Both expand the trust surface and make the job larger than the recorded frontier. An AST likely adds a dependency; a model judge is nondeterministic and cannot be the authority for exact evidence retention. Either may become a later evidenced job, but neither is needed for this prototype.

## 5. Risk register seed

The audit loop must enumerate these concerns. A clean result means the named check was performed for this corpus and diff, not that the wider class is impossible.

```risk-register
model-provenance | the claim that a fixture came from a named model | the manifest records provider full returned model id client version and response digest without inference from authorship
source-authority | candidate engineering material copied into the plugin | each source is redistributable bounded secret-reviewed and bound to its original digest
corpus-coverage | the five-family cross-model acceptance claim | the runner refuses fewer than five named families or fewer than two explicit model identities in any family
manifest-drift | manifest metadata versus fixture bytes | every source prompt original target and protected-span digest is recomputed before linting
schema-ambiguity | untrusted manifest fields | unknown missing duplicate and malformed fields refuse under a closed versioned schema
path-escape | manifest-controlled filesystem paths | paths are relative regular files inside the corpus root with byte caps and no symlink escape
classification-bias | expected outcomes chosen after seeing current diagnostics | a reviewer records the rule-based classification before linter comparison and the audit record preserves the decision
diagnostic-bypass | prose that violates a current rule but exits clean | every confirmed bypass gets a red case with the expected code before the smallest linter fix
false-positive-repair | prose that obeys the specification but is rejected | a rule changes only after a human classification names the satisfied contract and a guard preserves adjacent detections
evidence-token-gap | protected evidence outside the existing numeric and reference token scan | manifest-declared counterexample limit and reproduction spans are checked exactly against the target
ordered-evidence-loss | a rewrite retains steps but changes their order | ordered protected spans must occur once and in manifest order
exception-abuse | evidence exceptions used to hide unrelated verbosity | exception cases identify the protected span and still satisfy all rules outside that span
host-contract-conflict | another skill mandates a shape Brevitas normally rejects | specification and host-required structures stay excluded or receive a narrow evidenced exception rather than padding
regression-overfit | a fix recognises only one captured sentence | unit tests include the captured case one adjacent positive and one adjacent negative shape
sensitive-output | captured model material contains secrets or hidden reasoning | ingestion rejects credentials session data private prompts and reasoning fields before files are committed
external-capture | one-time provider clients and their output | capture is read-only bounded non-shelling and outside CI with exact client and model metadata recorded
partial-capture | a killed capture leaves a fixture that appears valid | capture writes to a private temporary path and the manifest is published only after all digests and review fields pass
marketplace-drift | mutable first-party prose describes the old frontier | the late reconciliation cold-reads the complete enumerated surface after behaviour settles and the marketplace test passes
frontier-arithmetic | completion advances the wrong evolution axis or invents a next job | exactly one row increments revision only and names an evidenced successor or records mature with no target
```

## 6. Glossary seeds

**Held corpus.** Committed input/output fixtures whose bytes, provenance, classification, and expected result are checked offline.

**Qualifying case.** A case with complete provenance and one of the five required engineering-family labels; historical unknown-provenance cases do not qualify for cross-model coverage.

**Engineering family.** Exactly one of `x-ray`, `solidity-auditor`, `gas`, `invariant`, or `diff-review`.

**Model identity.** Provider plus the full model identifier returned at capture time; an alias, author, or tool name alone is insufficient.

**Classification.** A human, rule-cited decision made before comparison with the current linter: conforming, expected diagnostics, compression target, or evidence-retention target.

**Confirmed bypass.** A classified rule violation for which the current linter exits clean or omits the required diagnostic.

**False positive.** A linter diagnostic on prose that the applicable Brevitas and host contracts permit.

**Protected span.** Exact source text whose survival and, where declared, relative order is part of evidence precedence.

**Expectation drift.** A mismatch between the manifest's classified outcome and the runner's actual sorted result.

**Cold read.** A complete post-change read of every mutable first-party marketplace-context document, without assuming that passing search results prove current wording.

## 7. Sources

- Controller brief: issue [#374](https://github.com/wildcat-finance/skills/issues/374), title `brevitas-next — forward-test the linter across a held engineering corpus`.
- Brevitas contract and frontier: `plugins/brevitas/skills/brevitas/SKILL.md`, `plugins/brevitas/skills/brevitas/EVOLUTION.md`, `plugins/brevitas/skills/brevitas/scripts/brevitas.py`, `plugins/brevitas/skills/brevitas/scripts/run_evals.py`, and `plugins/brevitas/skills/brevitas/evals/` at base `2e2608aa2ac62c5d556478e7f93186fddc36dce3`.
- Earlier repository pass: `docs/brevitas-repository-pass/study.md` and `docs/brevitas-repository-pass/runbook.md`.
- Authoritative audit source and verified view: `audit/AUDIT.md` and `audit/AUDIT_SYNOPSIS.md`, with the line counts and digests in section 2. The former was read directly for the three legacy Brevitas entries because the latter reports missing fields.
- Pull-request history: [#673](https://github.com/wildcat-finance/skills/pull/673), [#661](https://github.com/wildcat-finance/skills/pull/661), [#113](https://github.com/wildcat-finance/skills/pull/113), [#91](https://github.com/wildcat-finance/skills/pull/91), and [#93](https://github.com/wildcat-finance/skills/pull/93).
- Organisation material: the six `/home/kethcode/wildcat/mono` paths and SHA-256 values listed in section 2, read under that repository's `AGENTS.md`, `CLANKER.md`, `ARCH.md`, `kb/agent-handbook/START_HERE.md`, and `docs/repos/V2-PROTOCOL.md` instructions.
- Marketplace enumeration: `tests/test_marketplace_prose.py` functions `repository_markdown` and `mutable_marketplace_surface`; at the base ref they enumerate 111 mutable first-party Markdown files carrying marketplace context across 14 plugins.
- External specifications and practice: [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/), [GitHub Flavored Markdown](https://github.github.com/gfm/), [markdownlint custom rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/CustomRules.md), [Vale documentation](https://vale.sh/docs/), and [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

## 8. Signals, and the questions behind them

This is a command-line test tool, not an unattended service, so it needs no pager, metric backend, or production alert. The applicable contract is `plugins/hexaemeron/skills/ephoros/SKILL.md`.

The runner must answer four failure questions in ordinary text and a stable machine-readable test result: Which case id and digest failed? Which family or model identity is absent from coverage? Which expected and actual sorted diagnostic codes differ? Which protected span was lost, duplicated, or reordered? The corpus/runner step emits case id, family, model identity, expectation, actual codes, and short digests; the repair step adds the guard-test name and rule code; the final demo emits aggregate family/model/case counts and zero-valued failure counts. It must not print prompts, full model responses, credentials, or hidden reasoning merely to improve diagnostics.

## 9. Boundaries, per capability

The applicable contract is `plugins/hexaemeron/skills/phylax/SKILL.md`.

- Corpus ingestion crosses from adjacent repository material and one-time model clients into committed release bytes. Worth taking: bounded public engineering inputs, exact output text, explicit provider/model/client identity, and digests. Controls: licence and secret review, allowlisted fields, byte ceilings, temporary writes, no shell interpolation, and commit only after validation.
- Manifest parsing crosses from data-controlled strings into filesystem reads and coverage claims. Worth taking: closed enums, repository-relative paths, hashes, and expected codes. Controls: JSON-only standard-library parsing, schema/version refusal, real-path containment, regular-file and size checks, uniqueness checks, and deterministic sorting.
- Source-aware linting crosses from held source/output bytes into a verdict. Worth taking: exact syntactic diagnostics and exact protected spans. Controls: digest verification before execution, explicit evidence inventory, ordered survival checks, no semantic model judge, and clear separation between a lint verdict and factual correctness.
- Rule repair crosses from a captured example into Brevitas's general behaviour. Worth taking: only a reviewer-confirmed bypass or false positive tied to a current rule. Controls: red-before fix, adjacent positive/negative guards, smallest patch, full existing suite, and audit comparison with the entry ref.
- Marketplace reconciliation crosses from settled behaviour into 111 mutable first-party descriptions. Worth taking: accurate frontier and capability wording. Controls: enumerate the whole surface with the existing test helper, cold-read after behaviour settles, change only stale prose, run Imprimatur, and re-run the marketplace test.

## 10. The budget, or its absence

There is no performance budget because this job makes no speed, memory, scale, or cost claim; it operates on a deliberately small held corpus with a standard-library runner. The applicable contract is `plugins/hexaemeron/skills/metron/SKILL.md`. Runtime may be printed as diagnostic information, but it is not an acceptance threshold. If a later change proposes performance work, it must first record a baseline using the exact corpus and command `time mise exec python@3.13.15 -- python3 plugins/brevitas/skills/brevitas/scripts/run_evals.py`; that later work is outside this prototype.

## 11. The fail-closed posture

The applicable contract is `plugins/hexaemeron/skills/elenchus/SKILL.md`. Stop before linting or claiming coverage on an unreadable or oversized file, path escape, unknown schema field, missing field, duplicate id, unknown family/outcome, unknown model identity, stale digest, incomplete five-family/two-model coverage, unclassified case, or missing protected span. Stop after linting on diagnostic mismatch, evidence loss or reordering, a focused-test failure, an existing-suite regression, a prose-check failure, marketplace drift, or invalid frontier arithmetic. A model client or network failure may block capture; it must not fall back to an unrecorded model or synthetic provenance.

For each confirmed bypass or false positive, preserve the original fixture and current result, add a named focused test keyed by the stable case id, run it against the entry implementation to record the red failure, localise the cause, make the smallest fix, and run that exact test before the broader suites. The audit report records the entry ref, failing command and result, fix commit, passing command and result, and Elenchus verdict. If classification remains disputed, mark the case unclassified and stop; do not choose whichever expectation makes the suite pass.

## 12. Decisions and their homes

The applicable contract is `plugins/hexaemeron/skills/hypomnema/SKILL.md`.

- The corpus schema, what counts toward cross-model coverage, and the protected-span vocabulary are expensive to reverse because fixtures and tooling depend on them. Record the decision beside the runner in a concise corpus README or, if implementation reveals competing consumers, a repository ADR; keep the executable schema and validation in `plugins/brevitas/skills/brevitas/`.
- Each source selection, capture identity, licence/secret review result, classification, expected diagnostics, and evidence inventory belongs in the versioned case manifest. Raw hidden reasoning and credentials have no home because they are forbidden inputs.
- A confirmed rule change belongs in `SKILL.md`, `scripts/brevitas.py`, focused unit/eval cases, and the per-run audit record. The audit record preserves why the example was a bypass or false positive and the red-before evidence.
- The final frontier decision belongs in exactly one appended `EVOLUTION.md` row. Completion increments revision only, retains generation and epoch, and either names a next job supported by at least one named corpus result or records `None -- mature`; no successor is selected during study.
- Mutable marketplace wording belongs at its existing first-party surfaces, changed only where the late cold read establishes drift. The 111-file enumeration and test result belong in the audit evidence, not as copied prose in every file.
- This study and the later runbook are committed under a topic-specific documentation directory in Step 1. The active `.hexaemeron` copies remain controller artefacts rather than the durable decision record.
