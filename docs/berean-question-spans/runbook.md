# runbook: bind user_supplied sentences to the recorded question

This runbook derives from `.hexaemeron/study.md` at the receipted digest
`298ca6544d45168463c80b8a528b3a020a7205578520c20ccfcc5d69c6afb505`. The topic
is one verifier change with the tests, fixture, prose and ledger row that
describe it, so one auditable step both scaffolds and demonstrates it, as the
Phylax P008 delivery did for a change of the same shape. A split was
considered and refused: a step that tightened `answers.py` without
regenerating the fixture would hand the next step a red tree, and a step that
shipped the behaviour without its ledger row would leave a skill decision
unrecorded between two pull requests. The repository already supplies the
layout, licences, Python 3.9 and 3.12 compatibility and CI; issue #331 does
not authorise touching those, and this step verifies them rather than
replacing them.

The study's section 11 names the Berean discover command as the runner Warden
holds a fix to. Elenchus reads structured reports only, so the step adds one
plugin-local emitter that runs that same discover command and writes the
`elenchus.unittest.v1` payload through the shared writer in
`tests/emit_run_observation_report.py`. It is test support for the Fiat
runner contract, not a product decision; the study's chosen design and its
file list are otherwise unchanged.

## Step 1: bind user_supplied sentences to question spans, record berean-v0.2.0 and demonstrate

**Goal.** Make a `user_supplied` sentence name at least one real span of the
recorded question through `question:<start>-<end>` strings in its existing
`evidence` list, refuse one that names nothing or names a span that does not
re-slice, keep every other class and gate as it is, and ship the tests,
regenerated fixture, prose, generation row and package version that go with
the rule.

**Entry.** The clean run branch
`fiat/331-bind-user-supplied-sentences-to-the-recorded` at
`0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with the Fiat study and this
runbook receipted; the Berean suite green at 151 OK with one skipped on
Python 3.9.6 and 3.12.13; the root suite at 350 OK;
`tests.test_evolution_contract` at 9 OK; `scripts/promise_machine.py check`
and `coverage --check` clean; the fixture builder reproducing the committed
conformance fixture byte for byte; and a `user_supplied` sentence with an
empty `evidence` list accepted by `check-answer`. No dependency, toolchain
pin or CI change enters this step.

**Exit.** `answers.validate` parses each `evidence` string of a
`user_supplied` sentence with the grammar
`^question:(0|[1-9][0-9]{0,6})-(0|[1-9][0-9]{0,6})$`, requires `start < end
<= len(question.encode("utf-8"))`, a slice that decodes as whole UTF-8 and is
not blank, refuses an empty list, keeps refusing a citation or read id on
that class, and refuses a citation or read id that begins with `question:`;
every failure is `answer-shape` with a detail carrying the sentence index,
the reference position and parsed integers only. `evals.export` carries one
new `grounded-answer` assertion string. The schema `description` says that
`evidence` on a `user_supplied` sentence resolves against `question`; the
schema's structure, `FORMAT`, `FIELDS`, `SENTENCE_FIELDS`, `SOURCE_CLASSES`
and `MAX_SENTENCES` are unchanged. The conformance fixture is regenerated
through `release_fixture.build`, its bound sentence names `question:7-21`,
its cases file carries `c-reclassified` as a seventh case with expectation
`rejected` and adversarial class `unsupported-inference`, and
`run-evals` grades 7 of 7. `plugins/berean/tests/emit_report.py` exists and
writes one `elenchus.unittest.v1` report for the Berean suite. `docs/answers.md`,
`SKILL.md` gate 1 and the `berean-answer-evidence` refuses clause state the
new rule; `SKILL.md` frontmatter reads `0.2.0`; `EVOLUTION.md` carries the
`berean-v0.2.0` generation row and current version with the frontier
revision, digest, status and next job byte-identical to `berean-v0.1.0`; the
`berean-answer-o` coverage selector resolves; the package reads `0.1.2` on
`plugins/berean/.claude-plugin/plugin.json`,
`plugins/berean/.codex-plugin/plugin.json` and `.claude-plugin/marketplace.json`
with both test pins moved; the study and this runbook are committed under
`docs/berean-question-spans/`; nothing under
`plugins/berean/examples/aave-v4-demo-v0/` changes; and every command in
this demo path exits zero from the repository root (remove
`tmp/berean-question-spans-step-1.json` first if an earlier run left it):

```bash
/usr/bin/python3 -B -m unittest discover -s plugins/berean/tests -t plugins/berean
uv run --python 3.12.13 python -m unittest discover -s plugins/berean/tests -t plugins/berean
uv run --python 3.12.13 python plugins/berean/scripts/berean.py verify-release plugins/berean/tests/fixtures/conformance/pass-release
uv run --python 3.12.13 python plugins/berean/scripts/berean.py run-evals plugins/berean/tests/fixtures/conformance/pass-release
uv run --python 3.12.13 python plugins/berean/scripts/berean.py verify-release plugins/berean/examples/aave-v4-demo-v0/release
uv run --python 3.12.13 python plugins/berean/examples/aave-v4-demo-v0/demo.py
uv run --python 3.12.13 python plugins/berean/tests/emit_report.py tmp/berean-question-spans-step-1.json
uv run --python 3.12.13 python -m unittest discover -s tests
uv run --python 3.12.13 python -m unittest tests.test_evolution_contract
uv run --python 3.12.13 python scripts/promise_machine.py check
uv run --python 3.12.13 python scripts/promise_machine.py coverage --check
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/berean-question-spans/study.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/berean-question-spans/runbook.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/berean-question-spans/study.md docs/berean-question-spans/runbook.md plugins/berean/docs/answers.md plugins/berean/skills/berean/SKILL.md plugins/berean/skills/berean/EVOLUTION.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
uv run --python 3.12.13 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `plugins/berean/scripts/berean_lib/answers.py`,
`plugins/berean/scripts/berean_lib/evals.py` (one assertion string),
`plugins/berean/schemas/answer-v1.json` (one `description` sentence),
`plugins/berean/tests/test_answers.py`, `plugins/berean/tests/test_evals.py`,
`plugins/berean/tests/test_release.py`,
`plugins/berean/tests/release_fixture.py`, `plugins/berean/docs/answers.md`,
`plugins/berean/skills/berean/SKILL.md`,
`plugins/berean/skills/berean/EVOLUTION.md`,
`tests/promise_machine_coverage.json`,
`plugins/berean/.claude-plugin/plugin.json`,
`plugins/berean/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`plugins/berean/tests/test_scaffold.py` and
`tests/test_version_propagation.py`; regenerate
`plugins/berean/tests/fixtures/conformance/pass-release/answers/a1.json`,
`evals/cases.json`, `evals/report.json` and `release.json` through the
builder only; create `plugins/berean/tests/emit_report.py` and exact
committed copies at `docs/berean-question-spans/study.md` and
`docs/berean-question-spans/runbook.md`; Warden appends rounds to
`audit/rounds/fiat-331-bind-user-supplied-sentences-to-the-recorded.md`; and
regenerate `.horos/boundary.json` only if its scan changes that tracked
file. No other path is in scope without a study amendment.

**Tests.** First write the refusals and observe the focused suite fail
against the current `answers.py`: an empty `evidence` list on a
`user_supplied` sentence passes today and must fail; `question`, `question:`,
`question:7`, `question:7-`, `question:07-21`, `question:+7-21`,
`question:7-21-3`, `Question:7-21`, a leading or trailing space and an
eight-digit offset must fail as grammar; `question:21-7` and `question:7-7`
must fail as inverted or empty; `question:7-23` and `question:22-30` must fail
as out of range; a range cutting a multibyte character in a question that
carries one must fail as split UTF-8; `question:2-3`, the single space, must
fail as blank; a citation or read id whose id begins with `question:` must
fail at collection. Keep the artefact-id refusal under the renamed
`test_a_user_supplied_fact_names_the_question_spans_it_rests_on`, which also
proves `question:7-21`, two spans on one sentence and a span covering the
whole question pass. Assert that no `answer-shape` detail for these cases
contains the question text or the decoded span. In `test_evals.py` move the
case count to 7, assert `c-reclassified` passes as `rejected`, and keep the
adversarial class set at four. In `test_release.py` add one release-level
guard that copies the fixture, blanks the bound sentence's span list,
re-pins `answers[0].sha256` and `release_digest`, and asserts the failures
are exactly `release-answers` with a detail naming `answer-shape`. Extend the
export test if one pins the assertion list. Every guard must fail when the
span check is removed. The 151 existing tests plus every new named case pass
on Python 3.9.6 and 3.12.13; the command output records the final count.
Elenchus runner contract for this step, test command
`python3 plugins/berean/tests/emit_report.py {report}`, report format
`unittest-json-v1`, report file `.elenchus/berean-question-spans-step-1.json`.

**Disciplines.** phylax: this step adds a parse and a slice over untrusted
answer JSON inside `validate`, which stays regex-first with bounded digits, a
bounds check before the slice, a decode check and a blank check, and it adds
one script that writes one confined report path through the shared writer;
no subprocess, network path or secret enters. ephoros: none, because Berean
is a CLI that reads files and exits, and the two signals it already emits,
the `fail  answer-shape: <detail>` line and the exit status, are kept and
tested for the new refusal. metron: none, because the issue makes no
performance claim and the design adds one regex match and one slice per span
reference. elenchus: reproduce each missing refusal red before the fix, treat
the `c-reclassified` case as the eval-level red, and retain guards that fail
if the span check is removed; a round finding follows the same order under
the runner contract above. hypomnema: record the grammar, the byte unit, the
retained artefact-id refusal and the rejected per-sentence and top-level
constructions in the `berean-v0.2.0` row, pointing at the committed study;
`docs/answers.md` owns the vocabulary, `SKILL.md` the public gate text, the
commit message the package bump and its reason, and a comment in the emitter
the import-order trap it works around; no ADR.

Implementation order inside the step is fixed: commit the exact study and
runbook copies; write the red tests and preserve their failing output; make
the smallest `validate` change that turns them green on both interpreters;
bind the fixture sentence, add `c-reclassified`, regenerate the fixture
through the builder and confirm the committed bytes equal its output; move
the eval count, add the release-level guard, the export assertion and the
schema sentence; update the prose, the ledger row, the frontmatter version,
the coverage selector and the five version surfaces; add the emitter; run the
full demo path; then enter the Fiat audit and prose gates. Any need for a new
field, a new vocabulary value, a second named check, a change to the
reference release, a breach operation, a dependency, CI or a different package
version stops the step for a study amendment.
