# Runbook: Elenchus binds guard.test and repair.files to emit-path evidence

Derived from `.hexaemeron/study.md`, SHA-256
`b05fde2e0d1fb09a4125977185fd9011ecab8d5b8699b19dd7f885d0fd81d1ea`. Three
steps, in dependency order. Each one is a single pull request whose entry and
exit states are both green.

Assuming, unless corrected:

1. Python `3.14.6` from `.python-version`, stdlib `unittest`, no dependency
   outside the standard library.
2. `python3 scripts/run_checks.py --base origin/main` is the root suite, and a
   step is not finished until it exits zero on the committed tree.
3. The committed copies of the study and runbook live under
   `docs/elenchus-emit-path-bindings/`. The study's section 12 names homes for
   its decisions and none for the run documents, so this run follows the
   `docs/<run-topic>/` shape the #1275 run used.
4. `elenchus.py`, its flags and its four state strings do not change. No
   Solidity is in scope, so the Pashov suite and `fizz` are waived on every
   step.
5. The runbook carries no `version-relations` block, so `elenchus-v1.5.0` is a
   literal token, as `elenchus-v1.2.0` to `elenchus-v1.4.0` were.

```design-lock
schema | protasis-design-evidence/v1
sha256 | e950257f3d6c1dc607aaab6b6367603a933d78e56004ab3decdf2040fb552716
candidate | emit-path-rules
```

## Step 1: Land the specification and the two emit-path rules

**Goal.** Commit the run documents and add `F018` and `F019` to `emit()` with
the cases that see both hostile drafts refused.

**Entry.** Clean run branch `fiat/1318-elenchus-binds-guard-test-and-repair-files`
at `944277d7d60d25e52110bb82115804695307d3d3`, with
`plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py` at 790 lines
and its 55-case suite green.

**Exit.** `docs/elenchus-emit-path-bindings/study.md` and
`docs/elenchus-emit-path-bindings/runbook.md` are byte-identical to the
controller artefacts. `fixed_and_guarded.py` refuses, in `emit()` alone, `F019
repair.files` directly after `F007` when any path in `result["tests"]` is absent
from `repair.files`, naming every missing path; and `F018 guard.test` after
`F010` when any `[.:]`-split segment of `guard.test` does not occur as a whole
word, `(?<![A-Za-z0-9_])segment(?![A-Za-z0-9_])` over bytes, in the blob
`<repair.commit>:<guard.file>` read by `git cat-file -s` then `git cat-file
blob`, naming the first absent segment; a blob over `MAX_INPUT_BYTES`,
unreadable or not a blob is refused `F018`. Both refusals exit 1, name the code
and field on stderr, run before `prepare_output_path` and write nothing.
`check()` still calls `record_findings` alone. The module docstring lists
`F018` and `F019` beside `F007` and `F010` as emit-path rules `--check` never
runs; `result_findings`'s docstring says five values are read, and `F007`'s
message names `guard.file`. `F000` to `F017` are otherwise unchanged.
`elenchus.py` and `test_elenchus_checker.py` are byte-identical to the entry
ref. Proved by
`python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded`,
`python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker`,
`git diff --numstat 944277d7d60d25e52110bb82115804695307d3d3..HEAD -- plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`
reporting zero deleted lines,
`git diff 944277d7d60d25e52110bb82115804695307d3d3..HEAD -- plugins/hexaemeron/skills/elenchus/scripts/elenchus.py`
empty, `python3 .hexaemeron/reports/resolve.py emitter-suite-green` and
`python3 .hexaemeron/reports/resolve.py existing-cases-unedited` each printing
`True` for `emit-path-rules` and writing
`.hexaemeron/reports/emit-path-rules-emitter-suite-green.json` and
`.hexaemeron/reports/emit-path-rules-existing-cases-unedited.json`, the two
conformance results the design record holds pending against `step:2`, and
`python3 scripts/run_checks.py --base origin/main` at exit zero on the
committed tree.

**Files.** `docs/elenchus-emit-path-bindings/study.md`,
`docs/elenchus-emit-path-bindings/runbook.md`,
`plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py`,
`plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`, and
`.horos/boundary.json` only if the tracked-file count requires it.

**Tests.** `plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py` gains
cases and loses none: in `GuardBinding`, a draft whose `guard.test` names no
test in the guard file's bytes at the repair commit is refused `F018` at exit 1
with no file written, a module-qualified name whose module segments are absent
is refused, a name present as a whole word emits, and a blob over
`MAX_INPUT_BYTES` is refused; in `RecordRelations`, a draft whose
`repair.files` omits a `result["tests"]` path is refused `F019` at exit 1 with
every missing path named and no file written; and one boundary case asserting
a written record carrying an unbound `guard.test` and a short `repair.files`
still reads `clean` under `--check`. Each new case is seen red at the entry
ref before it is kept; every existing case passes unedited. Expected count 55
plus the new cases, at least 61. Step audit runner contract is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-1318-step-1.json`. That runner's discovery root contains the
emitter's module; `tests/run_tests.py` collects nothing under
`plugins/hexaemeron/tests/`. The report path must be fresh; a missing, stale,
empty, malformed or infrastructure-failed report is `inconclusive` rather than
evidence that a repair is guarded.

**Disciplines.** phylax: this step opens one new read of repository bytes
chosen by two draft values, so the controls are the commit `git rev-parse`
returned and `F010` matched, a `guard.file` that passed `_relative_path` and is
joined after a 40-or-64-hex commit and a colon so no operand begins with a
dash, two fixed-argv `git cat-file` calls with no shell, `-s` bounding the read
to `MAX_INPUT_BYTES` before `blob` runs, and blob bytes that are searched, never
decoded, executed or printed. ephoros: Warden and Mason run the emitter inside
an unattended audit round, so each refusal line names the code, the field, the
segment or paths and the commit on stderr, which is the only signal the study
requires. metron: none, no performance claim; the emit path gains two bounded
reads and one comparison over at most 256 strings. elenchus: the two hostile
drafts from the #1275 audit are failures in hand, so each new case is written
red against the entry ref and green after the fix, named after the failure,
and `test_elenchus_checker.py` is left alone so the classifier is never edited
beside a guard that depends on it. hypomnema: emit-path rules are a second
family, never carried-field members, and whole-word occurrence is what "names
the test inside that file" means; both decisions live in the module docstring
and the `F018` docstring, and no new decision record is earned.

## Step 2: Document the emit-path boundary and record the generation row

**Goal.** State the boundary between the emit path and `--check` wherever the
refusals are documented, add the `elenchus-v1.5.0` generation row and re-pin
the Hexaemeron package.

**Entry.** Step 1's exit state, with both rules and their cases committed.

**Exit.** `## Emit the result as a record` in
`plugins/hexaemeron/skills/elenchus/SKILL.md` lists `F018` and `F019` beside
`F007` and `F010` as the emit-path family, states that `--check` runs none of
the four and that `clean` excludes them by construction, and leaves the
carried-field enumeration at eleven; no other section changes except the
frontmatter, which moves to `version: "1.5.0"`.
`## What this run does not establish` in
`docs/elenchus-fixed-and-guarded-record/demonstration.md` no longer says the
emit path adds four things or that `guard.test` is checked for shape alone, and
gains one pointer to the skill section. `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`
carries `elenchus-v1.5.0` as current version and one new `generation` history
row whose frontier revision `observed-failure-root-cause`, frontier SHA-256
`08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`,
`Frontier status: mature` and `Next Fiat job: None -- mature` are byte-identical
to `elenchus-v1.4.0`. Hexaemeron re-pins from `1.6.26` to `1.6.27` in six
places: `plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`
and `.agents/plugins/marketplace.json` state the version, and
`tests/test_version_propagation.py` line 47 and
`plugins/hexaemeron/tests/test_phylax_model_proxy.py` line 5679 pin the
expectation those four agree on. The number is a checked property: it must
exceed every hexaemeron version claimed by any local or remote ref, it is
re-checked immediately before the integration push, and a collision moves all
six places to the next free number without a further amendment. Proved by
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/elenchus/SKILL.md`
and the same lint on `docs/elenchus-fixed-and-guarded-record/demonstration.md`
reporting clean, `python3 -m unittest plugins.hexaemeron.tests.test_evolution`
at exit zero, `python3 .hexaemeron/reports/resolve.py frontier-retained-byte-for-byte`
printing `True` for `emit-path-rules` and writing
`.hexaemeron/reports/emit-path-rules-frontier-retained-byte-for-byte.json`,
the conformance result the design record holds pending against `integration`,
and `python3 scripts/run_checks.py --base origin/main` at exit zero on the
committed tree.

**Files.** `plugins/hexaemeron/skills/elenchus/SKILL.md`,
`plugins/hexaemeron/skills/elenchus/EVOLUTION.md`,
`docs/elenchus-fixed-and-guarded-record/demonstration.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py`, and
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`.

**Tests.** `plugins.hexaemeron.tests.test_evolution` covers the row's axis
arithmetic and retained frontier line and is not edited;
`tests/test_version_propagation.py` and
`plugins/hexaemeron/tests/test_phylax_model_proxy.py` change only in the one
pinned literal each. No new executable behaviour is added, so no new test
module is written; the emitter's suite from step 1 stays green. Step audit
runner contract is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-1318-step-2.json`. That runner's discovery root contains the
emitter's module; `tests/run_tests.py` collects nothing under
`plugins/hexaemeron/tests/`. The report path must be fresh; a missing, stale,
empty, malformed or infrastructure-failed report is `inconclusive` rather than
evidence that a repair is guarded.

**Disciplines.** phylax: none, this step adds no input, process or write
boundary. ephoros: the second on-call question, which bindings `clean` checked,
is answered by the documentation this step writes, not by the record, so the
skill section and the demonstration's boundary section carry that sentence.
metron: none, no performance claim is made. elenchus: none, no failure is in
hand. hypomnema: the ledger row is the ledger's own durable record of a
behaviour change, and the skill section is the home the study's section 12
names for the two-family decision.

## Step 3: Demonstrate both refusals end to end

**Goal.** Run the demo path from the study's problem statement against a
scratch repository and write down what it produced.

**Entry.** Step 2's exit state, with the rules, the documentation, the ledger
row and the re-pin committed.

**Exit.** `EndToEnd.test_the_demo_path_emits_a_record_and_refuses_the_ones_it_should`
in `plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py` builds the
scratch repository with a real repaired failure, emits the genuine record,
runs the three demo-path commands through subprocesses and asserts:
`--draft inputs/guard-test-absent.json --result inputs/result.json --out records/guard-test-absent.json`
exits 1 with `F018 guard.test` on stderr and no file;
`--draft inputs/repair-files-short.json --result inputs/result.json --out records/repair-files-short.json`
exits 1 with `F019 repair.files` on stderr and no file; and
`--check records/fixed-and-guarded.json` exits 0 `clean`.
`docs/elenchus-emit-path-bindings/demonstration.md` records that run: the
commands, their exit codes, the exact refusal text, and what the record does
not establish, pointing at `## Emit the result as a record` for the boundary.
`docs/elenchus-emit-path-bindings/study.md` and
`docs/elenchus-emit-path-bindings/runbook.md` are byte-identical to the
controller artefacts, including every amendment appended since step 1. Proved
by `python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded`,
`cmp .hexaemeron/study.md docs/elenchus-emit-path-bindings/study.md`,
`cmp .hexaemeron/runbook.md docs/elenchus-emit-path-bindings/runbook.md`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/elenchus-emit-path-bindings/demonstration.md`
reporting clean, and `python3 scripts/run_checks.py --base origin/main`, all
at exit zero on the committed tree.

**Files.** `docs/elenchus-emit-path-bindings/demonstration.md`,
`plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`, and the two
committed copies under `docs/elenchus-emit-path-bindings/` if an amendment
moved the controller artefacts after step 1.

**Tests.** The existing `EndToEnd` case is extended, not replaced, with the two
refusal commands and the third command's `clean` exit, so the demonstration is
reproduced by the suite rather than only by hand; no existing assertion is
removed. Step audit runner contract is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-1318-step-3.json`. That runner's discovery root contains the
emitter's module; `tests/run_tests.py` collects nothing under
`plugins/hexaemeron/tests/`. The report path must be fresh; a missing, stale,
empty, malformed or infrastructure-failed report is `inconclusive` rather than
evidence that a repair is guarded.

**Disciplines.** phylax: the scratch repository is built by the test harness
inside a temporary directory and no path outside it is written, which is the
control this step needs. ephoros: none, the demonstration runs on demand and
nothing new starts running unattended. metron: none, no performance claim is
made. elenchus: the demonstration is the reproduce-and-guard shape the skill
describes, so its recorded run follows that procedure rather than a narrative
of it. hypomnema: none, the demonstration records an observation and reverses
no decision.
