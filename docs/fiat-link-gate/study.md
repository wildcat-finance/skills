# Gate study and runbook links before their digests are pinned

Assuming, unless corrected:

1. The starting ref is `main` at `485c90d3ad545b696584197f83d942c705988216`, equal to `origin/main` on 2026-09-14. The interpreter is Python `3.14.6` from `.python-version`, standard library only.
2. The bundled Hypomnema script stays the resolver. This run changes Fiat's controller and prose, not Hypomnema's behaviour or its `SKILL.md`.
3. The gate covers every controller path that pins a study or runbook digest: `done study`, `done runbook`, `amend study` and `amend runbook`. An amendment is checked over the bytes it appends, because its receipted prefix cannot change.
4. This run is a Fiat generation. It adds one ledger row after `fiat-v6.56.1`, provisionally `fiat-v6.57.1`, and leaves frontier status `open`, revision `delegated-task-identity`, the frontier text and the held job, skills#1212, byte-identical. Integration settles the number, because a concurrent run can take it first.
5. No byte of `plugins/hexaemeron/skills/fiat/SKILL.md` from 18784 to 23112 changes, and the version line keeps its length, so the agent-instruction fixture needs digest re-pins and no new measurement or parity run.
6. No state contract key, receipt field, ledger event field or packet field is added.

## 1. Problem statement

`done study` and `done runbook` pin an artefact's SHA-256 without checking its links. At the starting ref, `done study` (`hexctl.py:7402`) runs one bundled checker, `design_evidence.py`, at `design-lock` (7413). `done runbook` (7443) compares the design-lock block and checks `step:1` (7501). Neither runs Hypomnema. `protasis.py` runs only inside `amend study` and `amend runbook` (11876, 11900).

`done study` reads `.hexaemeron/study.md`, one directory below the worktree root. Step 1 of a runbook commits a copy under `docs/` or `plugins/<plugin>/docs/`, and the check map's `lint-hypomnema` walks both trees. Of the 160 committed study copies there, 55 sit one directory deep, 55 two deep, 19 three deep and 31 four deep. A link relative to its own file resolves at some of those depths and not at others. Three runs met this after the digest was pinned (section 2). `amend study` keeps the receipted bytes as an exact prefix, so each accepted the finding, shipped a copy that differs from its receipt, or both.

For Fiat operators, the workers who write studies and runbooks, and readers of committed copies.

A working prototype refuses, before any state, ledger or artefact write, an artefact that carries a recognised link or runbook pointer whose target depends on the artefact's directory, or a pointer the bundled checker cannot resolve. The same bytes get the same verdict at every depth. A conforming artefact receipts exactly as it does today.

Done means:

1. A new guard test drives `hexctl done study` with the five `../<skill>/SKILL.md` citations the skills#1070 run froze. The receipt is refused with state and ledger unchanged, and the test fails against `485c90d3`.
2. The same bytes at `.hexaemeron/study.md`, two directories deep and four deep earn one verdict, and a commit-pinned rendering is accepted at all three.
3. `done runbook`, `amend study` and `amend runbook` refuse the same pointer class. An amendment to a run whose receipted study already carries such a pointer is accepted when its appended bytes conform.
4. `python3 plugins/hexaemeron/tests/run_tests.py`, `python3 -m unittest discover -t . -s tests`, `python3 scripts/promise_machine.py check` and `python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json` exit 0 on a clean detached snapshot of each step's exit commit.
5. `done integrate` accepts exactly one new Fiat ledger row.

Demo path, in a throwaway run directory: `done study` refuses the frozen specimen and names its line and target, then accepts the same study with commit-pinned URLs. The transcript goes in the last step's pull request.

## 2. Prior art

### The controller at the starting ref

- `done_study` splits `--skills` into a list (7409) and records it in the receipt and the event (7426, 7431). Nothing checks it.
- `done_prose` (8125) is the declaration precedent. It refuses when `config.skills.prose_lint` or `config.skills.voice`, seeded at 147-148, is missing from `--skills` (8129-8136). That proves an id was named, not that the lint passed.
- `_design_checker_receipt` (7200) runs `design_evidence.py` through `bounded_run` with fixed argv and admits only a closed JSON receipt.
- `_check_amended_study` (11876) and `_check_amended_runbook` (11900) write the captured candidate to a temporary file in the run-state directory and run `protasis.py` over those exact bytes.
- The controller already loads bundled modules in-process and refuses when loading fails: `observation_validator_module` (875) and the audit synopsis renderer inside `validated_audit_record` (7899).
- `hypomnema` occurs twice in `hexctl.py`: in `LINTS` (188), from which `audit-round` derives `--hypomnema-exit`, and in the decision-assignment allocator path (9054). Neither checks a link at receipt.
- `_unfenced_markdown_lines` (3005) closes `~~~` fences. Hypomnema does not, so a rule built on the controller's fence reader would skip a pointer Hypomnema resolves.
- When `contracts` is present, `validate_state_shape` accepts only the key set `{"design_evidence"}` (1740), so a new contract marker would change the state shape older controllers read.

### Hypomnema at the starting ref

- H001 resolves each Markdown link outside fences and code spans against the file's own directory, skipping `#` anchors and the `http`, `https`, `mailto`, `tel` and `ftp` schemes. H003 resolves `runbook:` keyword pointers the same way.
- Measured with the pinned checker on single files: a `/`-rooted link resolves against the filesystem root and reports H001; a link inside a `~~~` block reports H001; a stable decision reference reports H009 and a superseding pointer reports H002, because a single-file run indexes no decision records. Naming `docs/decisions` as well clears both, and `docs/decisions` alone is clean.
- `lint-hypomnema` in `tests/check-map-v1.json` walks `README.md`, `AGENTS.md`, two `.agents/skills/promise-machine` files, `plugins` and `docs`, so a committed copy is linted at its committed depth.

### The defect in audit records

- `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`, S1-R1-01, low, accepted: five H001 on `plugins/horos/docs/marker-self-exclusion/study.md` for `../<skill>/SKILL.md` links, byte-identical to the receipted study. Commit `6f36bee9560638376e3609bfd5831661dc118390` later rewrote the five links for the committed location.
- `audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.md`, the skills#1070 run, S1-R1-01, low, fixed in this round: five H001 on the committed copy, repaired by rewriting that copy with commit-pinned URLs and amending the step 1 exit to name the difference.
- `audit/rounds/fiat-857-framework-16-the-commit-gate-lives-in-one-cl.md`, S1-R1-01, medium, open: the shipped study differs from its receipt by a five-line link-target rewrite, and ten backticked `.hexaemeron/` citations pass H001 and sit outside the run-state guard's file list.
- `audit/rounds/fiat-856-framework-13-test-the-remaining-atlas-hand-o.md`: a relocated copy of a decision record reported H001 on two links while the same record was clean in place.
- `tests/test_contributors.py` holds `test_every_relative_link_resolves` and `test_no_published_file_cites_the_run_state_directory` over five named files. Its comment records that rounds 3 and 4 of one run's step 1 found the same dead-link defect twice.

### The last two merged pull requests

For the receipt handlers, `git log --first-parent -L` over `done_study` through `done_runbook` names two:

- [skills#1249](https://github.com/wildcat-finance/skills/pull/1249), merge `f2bfe5ca1cc8816c77c82c1d51da72986726d7d9`, 2026-09-05: `done runbook` refuses mismatched step titles. It has no carryover block. Its boundary, that legacy receipts are not rewritten, holds here: this gate never re-checks bytes an older controller receipted.
- [skills#1002](https://github.com/wildcat-finance/skills/pull/1002), merge `c79d6781e2278642d1653d50671acdabb5867ef8`, 2026-08-31: design evidence. Its known boundary, 77 H001 inside the generated runtime mirror, was closed for directory walks by skills#1609 and does not reach a single-file check.

For `hypomnema.py`:

- [skills#1609](https://github.com/wildcat-finance/skills/pull/1609), merged as `485c90d3ad545b696584197f83d942c705988216`, 2026-09-14: walks prune `.agents/skills/promise-machine/runtime`. Its body records a census regeneration and `test_commit_gate.ActivationTests` failing in a linked worktree with `core.hooksPath` pinned. Both bind this run's step exits.
- [skills#1281](https://github.com/wildcat-finance/skills/pull/1281), merge `0fefcc986107ed66ff43c6572b7aa1c7351f12f4`, 2026-09-05: its carryover block is `none`.

The [skills#1070](https://github.com/wildcat-finance/skills/pull/1070) carryover names two items this run answers. `resolver-not-committed`: the resolver sits beside the design record, and each report's command runs from the record's directory, so it stays true when step 1 commits the record, its reports and the resolver together. `study-copy-is-a-rendering` is the defect this run closes.

### The retired run of this issue

The first run of skills#1086 started at `79072bef97360eff130410e2a767d47b936d414d` and was halted and retired on 2026-09-14: its base was 1,098 commits behind `485c90d3`, every file its steps 2 and 3 changed had moved, and `plugins/hexaemeron/tests/test_issue_429_recovery.py` had been deleted. Its step 1 pull request, [skills#1093](https://github.com/wildcat-finance/skills/pull/1093), closed unmerged.

Its audit record, `audit/rounds/fiat-1086-check-that-a-study-or-runbook-resolves-its.md` at `3e64210529d6f6278f457a04ba003101d434a8e5`, exists only on the retired branches:

- Round 1 covered `frozen-artefact`, `reviewed-span-drift` and `self-application` as reviewed and `derived-digest-chain`, `frontier-drift` and `false-refusal` as not applicable. Elenchus verdict: null. Not checked: the waived security suite, hosted CI, the controller receipt, push, publication, whether the design was right, and `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`, red at that base for `VENUES.json`.
- S1-R1-01, low, recorded not fixed: `controller-surface-bytes` came from a literal table yet read as measured. Carried forward and partly answered: the value is now the source size of each candidate's executable prototype. It still estimates unwritten code, and section 4 says so because the closed report shape has no field for it.
- S1-R1-02, low, recorded not fixed: `check-latency-ms` timed one command for two candidates. Answered: each candidate is timed through its own gate. The two still fall within run-to-run spread, and section 4 gives the measured reason.
- Round 1 leads not pursued: neither weak metric affected the selection; the resolver was not committed, answered above; and a first draft of that record misstated where the resolver lived. A false statement about a file is not an unresolvable link, so this gate does not catch it either.
- Round 2 had the same coverage, Elenchus verdict null and no findings. It showed the step 1 guard fails when a file-relative link is appended to the committed study.
- `VENUES.json` is untracked at `485c90d3` while `tests/check-map-v1.json:393` still names it. That test was not rerun here.

### Audit sources and how they were read

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check <target-root>` exited 0 over 85 sources, six `AUDIT.md` files and 79 per-run records, each `committed=match` and `budget=pass`. The in-scope sources are `audit/AUDIT.md`, `plugins/hexaemeron/audit/AUDIT.md` and the 79 `audit/rounds/*.md` records, because any Fiat run can have met this defect. Each was read through its verified synopsis by grep for `done study`, `done runbook`, `H001`, relative-link wording and `design_evidence`. Thirty-four synopses matched; the records cited above come from their matching rows. No source or synopsis was read whole. The retired run's record is outside the 85, so no currency check covers a synopsis of it, and its source was read by grep at the commit above.

## 3. Constraints and non-goals

### Starting state

- Ref `485c90d3ad545b696584197f83d942c705988216`; Python `3.14.6`; Hexaemeron `1.6.37`; Fiat `fiat-v6.56.1`.
- `plugins/hexaemeron/skills/fiat/SKILL.md` is 80,506 bytes with SHA-256 `ae4f9cbf11f58848a9d55b063d7585fa777561f13562f60ba09a19978ccca7a4`. The fixture manifest measures bytes 18784 to 23112. `source-spans.json` binds the same digest with node spans 18784-18795 (twice), 19038-19196, 19197-19339, 19340-19515, 22513-22654 and 22656-23110.
- Edit sites outside that range: the `version:` line at byte 368, and the `**Study and runbook.**` phase note at byte 23128, whose Imprimatur sentence starts at byte 23522.
- The `done study --artifact <path> --skills <csv>` cell starts at byte 19149, inside `study-phase`, and stays byte-identical.
- Measured with `scripts/prove_agent_instruction_reconciliation.py` at the starting ref: `offline --candidate digest-neutral-corpus` is accepted with corpus digest `f03ddbef594669f5f5d0a06ae0adb90a4b38c003d6f5cb8d6ec0b7c0a64408ea`; `span-shift` accepts a 46-byte comment appended after the range and refuses the same comment prepended at byte 0 with `WAI-E-DIGEST.CORPUS`. Merge `eebab8621154cd6d5900c374f80474a6225d6ece` (skills#1615) replaced one byte of the version line, inserted 1,030 bytes at byte 48848, re-pinned `manifest.json`, `model.json`, `source-spans.json` and `compact.wai`, and left `evidence/measurement.json` and `evidence/parity.json` unchanged.

### What an edit forces, by digest

For each file, `shasum -a 256` at the starting ref, then `git grep -c <digest> 485c90d3`:

| Edited file | Pinned in (occurrences) |
| --- | --- |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `tests/promise_machine_coverage.json` (1, `run_observation_binding.controller.sha256`) |
| `plugins/hexaemeron/skills/fiat/SKILL.md` | `tests/fixtures/agent-instruction-v1/manifest.json` (1); `fiat-study-runbook-phase/model.json`, `source-spans.json` and `compact.wai` (1 each) |
| `plugins/hexaemeron/skills/fiat/EVOLUTION.md` | `tests/fixtures/promise-machine/runtime/fiat-final-integration.json` (4) |
| `model.json`, `source-spans.json`, `compact.wai`, `evidence/measurement.json`, `evidence/parity.json` | `tests/fixtures/agent-instruction-v1/manifest.json` and `tests/promise_machine_coverage.json` (1 each) |
| `tests/fixtures/agent-instruction-v1/manifest.json` | `tests/promise_machine_coverage.json` (1) |
| `tests/fixtures/promise-machine/runtime/fiat-final-integration.json` | `tests/promise_machine_coverage.json` (2) |
| `tests/promise_machine_coverage.json` | `docs/promise-machine/obligation-gates/demonstration-run.json` and `demonstration-evidence.md` (1 each) |
| `docs/promise-machine/obligation-gates/evaluation-run.json` | the same two files (1 each) |
| `tests/promise_machine_id_history.json` | the same two files (1 each); four copies under `docs/agent-instruction-reconciliation/evaluation-replay/` that no Python file reads |
| `plugins/hexaemeron/tests/test_hexctl.py` | `tests/promise_machine_coverage.json` (3); `tests/fixtures/promise-machine/composition/cases.json` (2); runtime `fiat-final-integration.json` (14), `fiat-receipted-delivery.json` (10), `fiat-study-amendment.json` (10) |
| `plugins/hexaemeron/tests/test_fiat_skill.py` | `tests/promise_machine_coverage.json` (1); runtime `fiat-runbook-amendment.json` (10) |
| `plugins/hexaemeron/skills/protasis/SKILL.md` | `docs/main-root-suite-recovery/package-measurement.json` (1), which no Python file reads |
| `tests/test_evolution_contract.py`, `tests/test_version_propagation.py`, `plugins/hexaemeron/tests/test_phylax_model_proxy.py`, the four version manifests, `plugins/hexaemeron/agents/surveyor.md`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, `plugins/hexaemeron/skills/fiat/references/audit-loop.md`, `.horos/census.json`, `.horos/boundary.json`, `demonstration-run.json`, `demonstration-evidence.md` | no hit |

Chains a digest grep does not show:

1. `evaluation-run.json` binds `tree_sha256` over 14 inputs, including `tests/promise_machine_coverage.json` and `plugins/hexaemeron/skills/hypomnema/SKILL.md`. After any coverage re-pin it is re-tallied with `tests/promise_evaluation_driver.py` `emit`, `tally` and `verify` from `evaluation-answers.json`, keeping the recorded model and date. Editing `hypomnema-record-placement`, the one evaluated Hypomnema promise, would change a prompt and void that reuse.
2. The version bump moves `metadata.version` in `fiat/SKILL.md` (line 10); the head assertions in `tests/test_evolution_contract.py` (360 and 366-373, with `FIAT_FRONTIER` and `FIAT_NEXT_JOB` unchanged); and `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` (`hexctl.py:454`, last member `fiat-v6.56.1` at 478), which checkpoint restore compares at 16984-16985. That constant is itself a `hexctl.py` edit.
3. A plugin bump from `1.6.37` changes `.agents/plugins/marketplace.json:21`, `.claude-plugin/marketplace.json:35`, `plugins/hexaemeron/.claude-plugin/plugin.json:4`, `plugins/hexaemeron/.codex-plugin/plugin.json:3`, `plugins/hexaemeron/tests/test_phylax_model_proxy.py:5679` and `tests/test_version_propagation.py:47`. Tests check that these agree, not that they move; skills#1249 and skills#1615 bumped by practice.
4. Editing a promise stanza in `fiat/SKILL.md` (from line 883) moves `tests/promise_machine_id_history.json` through PM104, then the demonstration pair. Tests can cover the gate without a stanza edit.
5. Tracked byte-count changes move `.horos/census.json`; skills#1615 also regenerated `.horos/boundary.json` and `.horos/candidates.json`.
6. `INTEGRATED_CONTROLLER_SHA256` no longer exists in code or tests. It survives in nine Markdown files as history, and `plugins/hexaemeron/tests/test_issue_429_recovery.py` is gone.

New tests in a new test file keep the `test_hexctl.py` and `test_fiat_skill.py` rows out of the chain.

### Always, ask first, never

- Always: run the root suite and the Hexaemeron parallel runner on a clean detached snapshot before a step exit; run Imprimatur and Hypomnema on each shipped document at its committed path; run the prover's `prepare` and `apply --check-only` before the fixture re-pin.
- Ask first: any `fiat/SKILL.md` edit inside bytes 18784 to 23112 or any length change before 18784; a Hypomnema behaviour or `SKILL.md` change; a new contract key, receipt field or packet field; any model run for measurement, parity or evaluation.
- Never: re-obtain evaluation answers to clear `tree_sha256`; change an inherited decision record or add a numbered one by hand; edit a byte-pinned audit record; report a suite as passed without its exit code.

### Non-goals

- Factual claims no lint reads, such as the Anamnesis ADR-004 claim about Synkrisis that the issue names.
- Citations inside code spans, the class of the open fiat-857 finding; backticked paths pass H001 and this rule.
- Resolving absolute URLs. The gate makes no network call, so a commit-pinned URL to a missing path is accepted.
- Re-checking bytes an older controller receipted, or rewriting committed studies.
- Resolving `/`-rooted links against the repository root. The bundled checker resolves them against the filesystem root, so the rule refuses them.
- Changing Hypomnema, Protasis or the audit round. skills#1067, which asked the audit round to run the repository suite, is closed.
- Advancing Fiat's frontier.

### Concurrency

On 2026-09-14, 62 open pull requests came from `fiat/` branches of at least 18 runs, and none named `fiat-v6.57.1` or `1.6.38`. Both numbers stay provisional until integration, and the decision record's number is assigned at merge (section 12).

## 4. Design options

The design record beside this study is a `protasis-design-evidence/v1` matrix of three candidates, six criteria and 18 reports. The candidate ids and the criteria's id, concern, kind, unit, comparator, threshold, owner, stage and blocks are the retired run's, unchanged. Every cell was re-measured at `485c90d3`.

**`declare-only`** requires `hexaemeron:hypomnema` in `--skills`, as `done_prose` requires its two ids. It is the smallest change. It never opens the artefact, so it accepts the specimen whenever the id is declared.

**`lint-in-place`** runs the bundled check on the artefact where it sits. It refuses the specimen, but identical bytes pass at one depth and fail at another, so a verdict at `.hexaemeron/study.md` says nothing about the committed copy.

**`require-location-independent`** refuses a recognised link or runbook pointer that is neither an absolute URL nor an in-page anchor, then runs the bundled check. The verdict reads the pointer, not the artefact's path, so it holds at every depth. It is the largest of the three and matches the commit-pinned form the skills#1070 repair used. After the pointer rule, what the check still resolves in a study is its decision references: H002, H008 and H009.

### How the cells were measured

`resolve.py`, beside the record, reads the bundled `hypomnema.py`, `fiat/SKILL.md` and `source-spans.json` as Git blobs at `485c90d3`, so its values reproduce after later steps change those files. It builds a probe tree under `tmp/` in the worktree, runs each candidate's prototype gate there, prints the report, writes only to a new `--out` path opened exclusively, and removes the probe tree. Each report's `command` runs from the record's directory. A rerun onto an existing report exited 2 and left it unchanged, and all 15 untimed cells reproduced byte for byte.

Three frozen bodies drive the probes: the specimen, five `../<skill>/SKILL.md` citations; the depth-sensitive body, one `../../plugins/hexaemeron/skills/fiat/SKILL.md` link that resolves two directories deep and not four; and the conforming body, that link pinned to `485c90d3`.

Prototype decisions, A for accept and R for refuse:

| Probe | `declare-only` | `lint-in-place` | `require-location-independent` |
| --- | --- | --- | --- |
| specimen at `.hexaemeron/study.md`, lint declared | A | R | R |
| depth-sensitive body, two deep | A | A | R |
| depth-sensitive body, four deep | A | R | R |
| conforming body, two deep and four deep | A | A | A |
| conforming body at `.hexaemeron/study.md`, lint not declared | R | A | A |

Cell values, with the retired record's value in brackets where it differs:

| Criterion and rule | `declare-only` | `lint-in-place` | `require-location-independent` |
| --- | --- | --- | --- |
| `catches-observed-defect`, equals 1 | 0, fail | 1, pass | 1, pass |
| `verdict-location-independent`, equals 1 | 0, fail | 0, fail | 1, pass |
| `reviewed-span-bytes-touched`, equals 0 | 0, pass | 0, pass | 0, pass |
| `enforces-result-not-declaration`, equals 1 | 0, fail | 1, pass | 1, pass |
| `controller-surface-bytes`, minimise | 102 [220] | 542 [480] | 2,519 [900] |
| `check-latency-ms`, minimise | 0 | 41 [63] | 44 [63] |

What each value is:

- `catches-observed-defect` and `enforces-result-not-declaration` are executed. The second is 1 only when a failing artefact is refused although the lint is declared and a passing one is accepted although it is not.
- `verdict-location-independent` is executed under one stated reading: a decision counts as a link verdict only if changing the link alone, at one depth, changes it. `declare-only` gives one decision everywhere and scores 0, as the retired record held. Read literally, identical decisions at two depths would score it 1; it would still fail two gates, and the selection would not move.
- `reviewed-span-bytes-touched` applies each candidate's one-sentence phase note after byte 23631, plus the version line change, to the pinned bytes and counts differing bytes inside the spans. The sentences are modelled; the count is measured.
- `controller-surface-bytes` is a modelled estimate: the source bytes of each prototype. For the selected candidate that is the gate, the pointer scan, the module loader and the subprocess call. It excludes Hypomnema's parser, which the rule loads rather than copies; a copy would add 2,568 bytes. The closed report shape cannot mark an estimate, so this sentence does.
- `check-latency-ms` is a timed median of 21 calls after one warm-up, over the conforming body. Five runs gave 41 to 49 ms for `lint-in-place` and 43 to 46 ms for `require-location-independent`. The selected candidate's extra work is a module load, 0.13 ms warm, and a scan, 8.8 µs on the 166-byte body and 425 µs on a 12,493-byte study. Both sit inside the spread, so the metric does not separate the two.

### Selection

`declare-only` fails three gates and `lint-in-place` fails one. `require-location-independent` passes all four and is the only survivor, so the rule is `unique-frontier` and the metrics decide nothing. `design_evidence.py --transition design-lock` exits 0 and consumes all 18 reports.

### Construction settled here

1. The rule loads the bundled `hypomnema.py` in-process, as the controller already loads its observation validator and audit synopsis renderer, and calls that module's `LINK`, `RUNBOOK`, `suppressed`, `_external`, `_code_spans` and `_within`. A missing module or name refuses the receipt. The recognised pointer set is Hypomnema's, fence reading included, so no copied parser can drift from it.
2. Resolution runs the bundled checker as a bounded subprocess with `--format json` over the exact captured bytes in a controlled temporary file. `docs/decisions` is named too when it exists, and only findings on the artefact count.
3. `done study` and `done runbook` check the whole artefact; `amend study` and `amend runbook` check the appended bytes.
4. A refusal writes nothing, and no contract key, receipt field, event field or packet field is added.

## 5. Risk register seed

```risk-register
frozen-artefact | the digest pin in done study, done runbook, amend study and amend runbook | every refusal happens before any state, ledger or artefact write, so a refused artefact stays editable
recognition-parity | the pointer rule against the bundled Hypomnema parser | the rule calls the loaded module's own helpers, a missing name refuses, and one specimen table covers backtick fences, tilde blocks, code spans, anchors, the skipped schemes and the allow pragma
false-refusal | a conforming study or runbook | pinned absolute URLs, anchors, code-span paths, stable decision references and superseding pointers are accepted because docs/decisions is in the check's scope
false-acceptance | a repository-rooted link, a tilde-fenced link and a runbook keyword pointer | each is refused at every depth, matching what the bundled checker would report on the committed copy
legacy-prefix-lockout | an amendment to a run whose receipted study predates the gate | only appended bytes are checked, so an inherited relative link cannot block later amendments
captured-bytes | the artefact between its bounded read and the check | the check reads the captured bytes through a controlled temporary file and never re-reads the path
subprocess-and-output | the checker argv, timeout, output cap and JSON | fixed argv under the plugin root, no shell, closed bounded JSON, and no raw child output in a refusal
parser-complexity | the scan of an untrusted artefact | the scan stays linear on a line holding tens of thousands of backticks, as the Hypomnema code-span guards require
reviewed-span-drift | fiat SKILL.md bytes 18784 to 23112 and the version line | no byte in the range changes, the version line keeps its length, and agent_instruction.py check accepts with no new measurement or parity
derived-digest-chain | every artefact pinning an edited file | each section 3 hit is re-pinned, evaluation-run.json is re-tallied from committed answers, and no answer is re-obtained
frontier-drift | plugins/hexaemeron/skills/fiat/EVOLUTION.md | exactly one generation row is added and status, revision, frontier text and held job stay byte-identical
self-application | this run's study, runbook and committed copies | each passes the new rule at its receipt location and at its committed location
```

## 6. Glossary seeds

- **Receipt location.** Where a receipt reads the artefact: `.hexaemeron/study.md` or `.hexaemeron/runbook.md`, one directory below the worktree root.
- **Committed copy.** The study or runbook a runbook step commits under `docs/` or `plugins/<plugin>/docs/`, one to four directories deep.
- **Recognised pointer.** A Markdown link or `runbook:` keyword pointer that Hypomnema resolves: outside backtick fences and code spans, and not suppressed.
- **Location-dependent pointer.** A recognised pointer that is neither an absolute URL with a skipped scheme nor an in-page anchor; a `/`-rooted path counts.
- **Link verdict.** A receipt decision that changes when only the artefact's links change.
- **Declaration versus result.** A `--skills` id naming a lint, against the lint's findings on the artefact.
- **Reviewed span.** The bytes of `fiat/SKILL.md` the agent-instruction fixture measures and binds, 18784 to 23112 at the starting ref.
- **Digest chain.** The artefacts pinning an edited file's SHA-256, and the artefacts pinning those.
- **Generation row.** A Fiat ledger row for a behaviour change that keeps the prior frontier revision and digest.

## 7. Sources

Files at the starting ref:

- [hexctl.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/fiat/scripts/hexctl.py), lines 147-148, 188, 454-480, 588, 875, 1740, 3000-3005, 7200-7205, 7402-7535, 7899, 8125-8136, 9054, 11876-11923, 16984-16985
- [fiat SKILL.md](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/fiat/SKILL.md), bytes 368, 19149, 23128, 23522, 23631; promise stanzas from line 883
- [fiat EVOLUTION.md](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/fiat/EVOLUTION.md) and [VERSIONING.md](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/VERSIONING.md)
- [hypomnema.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py) and [Hypomnema SKILL.md](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/hypomnema/SKILL.md)
- [Protasis SKILL.md](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/protasis/SKILL.md), [design_evidence.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/protasis/scripts/design_evidence.py) and [protasis.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/protasis/scripts/protasis.py)
- [source-spans.json](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json) and [manifest.json](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/fixtures/agent-instruction-v1/manifest.json)
- [promise_machine_coverage.json](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/promise_machine_coverage.json), [evaluation-run.json](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/docs/promise-machine/obligation-gates/evaluation-run.json), [demonstration-run.json](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/docs/promise-machine/obligation-gates/demonstration-run.json) and [promise_evaluation_driver.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/promise_evaluation_driver.py)
- [fiat-final-integration.json](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/fixtures/promise-machine/runtime/fiat-final-integration.json), [test_evolution_contract.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/test_evolution_contract.py) and [test_version_propagation.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/test_version_propagation.py)
- [check-map-v1.json](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/check-map-v1.json) and [test_contributors.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/tests/test_contributors.py)
- [prove_agent_instruction_reconciliation.py](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/scripts/prove_agent_instruction_reconciliation.py), [ADR-076](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/docs/decisions/ADR-076-digest-neutral-measured-corpus.md) and [ADR-092](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/docs/decisions/ADR-092-stage-reviewed-corpus-reconciliation.md)
- Audit synopses: [fiat-377](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.synopsis.md), [the skills#1070 run](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.synopsis.md), [fiat-856](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/audit/rounds/fiat-856-framework-13-test-the-remaining-atlas-hand-o.synopsis.md) and [fiat-857](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/audit/rounds/fiat-857-framework-16-the-commit-gate-lives-in-one-cl.synopsis.md)

Elsewhere:

- Issues [skills#1086](https://github.com/wildcat-finance/skills/issues/1086), [skills#1212](https://github.com/wildcat-finance/skills/issues/1212) and [skills#1067](https://github.com/wildcat-finance/skills/issues/1067)
- Pull requests [skills#1002](https://github.com/wildcat-finance/skills/pull/1002), [skills#1070](https://github.com/wildcat-finance/skills/pull/1070), [skills#1093](https://github.com/wildcat-finance/skills/pull/1093), [skills#1249](https://github.com/wildcat-finance/skills/pull/1249), [skills#1281](https://github.com/wildcat-finance/skills/pull/1281), [skills#1609](https://github.com/wildcat-finance/skills/pull/1609) and [skills#1615](https://github.com/wildcat-finance/skills/pull/1615)
- The retired run's record, `audit/rounds/fiat-1086-check-that-a-study-or-runbook-resolves-its.md`, at commit `3e64210529d6f6278f457a04ba003101d434a8e5`
- The design record and `resolve.py` beside this study, and the 18 reports in the record's `reports/` directory

## 8. Signals, and the questions behind them

Nothing runs unattended: a person or worker runs each receipt and reads its output at once, so no event, metric or alert is owed. Two questions must be answerable from that output:

1. Why was this receipt refused? The refusal names the artefact, the line, the pointer target and the stage that refused it, pointer rule or checker, and exits 2 with state and ledger unchanged. The target and message come from bounded, printable fields, never from raw child output.
2. Did the receipt that pinned this study pass the gate? The run anchor and `controller_currency` receipts record the controller version, and every controller from the version this run adds refuses before pinning.

[Ephoros](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal must carry.

## 9. Boundaries, per capability

One capability: before pinning, the controller scans bytes it already reads, loads one bundled module and runs one bundled script.

- The artefact is written by workers and operators. `read_bounded_source` (588) already contains and caps the read. The scan runs over those captured bytes, and the checker reads the same bytes through a controlled temporary file, so the file cannot change between check and digest.
- The module and the script come from the plugin root, resolved with `realpath`, and must be regular files. A load or interface failure refuses.
- The subprocess has fixed argv, no shell, and the timeout and output cap of `bounded_run`. Its JSON is admitted only as a closed, bounded shape; anything else refuses.
- A pointer target echoed in a refusal is first checked with `_contains_nonprinting_character` (3000).
- The change opens no network path, reads no credential and adds no dependency.

[Phylax](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and its controls. Section 5 carries these as `captured-bytes`, `subprocess-and-output` and `parser-complexity`.

## 10. The budget, or its absence

None, because the check runs once per receipt or amendment and nothing here changes for speed. `resolve.py` measured 41 to 49 ms per check over a 166-byte artefact with or without the pointer rule, a 0.13 ms module load, and a 425 µs scan of a 12,493-byte study. Those figures are selection evidence, not a budget. [Metron](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget carries.

## 11. The fail-closed posture

A receipt stops on a location-dependent pointer; a checker finding on the artefact; a bundled module or script that is missing, unloadable or missing a name; or a checker timeout, output overflow or malformed output. Each refuses before any write, and none is skipped, retried or reduced to a warning.

The run stops when the design checker refuses at `step:N` or `integration`; `scripts/agent_instruction.py check` refuses after a re-pin, or the prover reports `needs-evidence`, which makes a model run an ask-first decision; `scripts/promise_machine.py check` refuses, including PM104 and PM109; `promise_evaluation_driver.py verify` refuses; the root or Hexaemeron suite is red on a clean snapshot; or `frontier_close_fault` refuses at integration.

Guard convention: each new refusal test names its exact specimen, fails against its parent commit, passes on the fix, and runs through `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`. [Elenchus](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

1. Study and runbook receipts refuse location-dependent pointers, and the verdict reads the pointer, not the artefact's path. An artefact an older controller accepted can be refused after this change, so it earns a record. Home: a new draft at `docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md` with a `# Decision:` heading and the five record sections. The integration composer assigns its number with `decision_assignments.py` `plan`, `apply` and `replay`. Nothing numbered is added by hand, no inherited record changes, and no new `draft-*.md` goes at the `docs/decisions/` root, where only files inherited unchanged are tolerated; two sit there at the starting ref.
2. The same record carries the construction choices, each expensive to reverse: loading Hypomnema's parser rather than copying it or adding a Hypomnema mode; checking appended bytes on amendment; adding no contract key, receipt field or packet field. Its Alternatives section carries `declare-only` and `lint-in-place` with the reasons in section 4.
3. The Fiat generation row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md` points at that record and does not restate it.

This study cites the record by path, not by stable reference, because a single-file Hypomnema check indexes no decision records and would report H009. [Hypomnema](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where each one lives.

### Amendment -- 2026-09-14

**What changed.** Two construction points and two controls are corrected. The selected candidate and the design record are unchanged.

1. Construction item 3 in section 4 now reads: `done study` and `done runbook` check the whole artefact, and `amend study` and `amend runbook` check the bytes the amendment appends, read in the fence state the receipted prefix leaves.
2. The pointer rule's in-process scan gains a time bound. It refuses once it runs longer than the checker's 30-second `GIT_TIMEOUT`, naming the artefact and the pointer-rule stage, before any state, ledger or artefact write.
3. In section 5, `parser-complexity` is checked as: the scan of an untrusted artefact refuses at that bound, and stays linear on a line holding tens of thousands of backticks and one pointer.
4. In section 11, a pointer-rule timeout joins the causes that stop a receipt.

**Why.** Step 2 audit round 1 recorded both in `audit/rounds/fiat-1086-gate-study-and-runbook-links-before-their-d.md`. S2-R1-03: Hypomnema's `LINK` pattern backtracks quadratically on a line dense in `[`, and `_within` scans every code span for each match, so the scan took 43.2 s for 20,000 `[a](` repeats and 8.79 s for 20,000 links quoted in code spans; section 5's linear-scan claim held only for a line with few pointers. S2-R1-01: appended amendment bytes were read as if no fence were open, while Hypomnema reads them in the fence state the prefix leaves; commit `9dabc5176724ca00d7ba4117e0e051c3938c17b2` fixed it. The runbook amendment of the same date already carries both into Step 2's Exit and Tests.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
