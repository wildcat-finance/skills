# Issue 331: bind user_supplied sentences to the recorded question

Rounds for the run on branch
`fiat/331-bind-user-supplied-sentences-to-the-recorded`, off `main` at
`0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`. Headings carry step and round
alone, because the file names the run.

## Step 1, round 1 -- 2026-08-25

Non-Solidity round over the question-span verifier change, its tests, the
regenerated fixture, the prose, the `berean-v0.2.0` row and the emitter, at
`df7ca171d2c8cf1bab091523d4caa13c4ef7c8c4`. The diff runs from the run branch
to the step branch, 23 files in three commits: `3a01db9` (the study and
runbook copies), `819dd19` (verifier, tests, fixture, coverage selector) and
`df7ca17` (prose, ledger row, version surfaces, emitter). The Pashov pair and
fizz are waived because the diff carries no Solidity. One finding, fixed on
the stacked branch.

### Finding

<!-- brevitas: archival-table rendered as a record because this historical table is below the 3x3 presentation threshold -->
- id: S1-R1-01; severity: low; file: `plugins/berean/scripts/berean_lib/answers.py:84`; finding: `validate` encoded `question` at the slice without proving it could be encoded. `json.loads` turns a lone-surrogate escape such as `"\udc80"` into a str with no UTF-8 encoding, and the escape passes `jsonio` because the file bytes are valid UTF-8, so an answer document carrying one made `check-answer`, `verify-release` and `run-evals` exit 1 through an `UnicodeEncodeError` traceback instead of a named `answer-shape` refusal. The run branch accepted the same document silently, so the traceback is new to this step. Reproduced through `verify-release` on a copy of the conformance fixture with the escape in `answers/a1.json` and its digests re-pinned; status: fixed at `115231a397a93479813cf7cb79f24988c8518cea` on `fiat/331-bind-user-supplied-sentences-to-the-recorded-step-1-bind-user-supplied-sentences-to--audit`. The encode moved to where the question is stated, for both kinds, and a failure is `answer-shape` with the detail `question is not encodable as UTF-8 at character 22; a lone surrogate names no bytes`: the position and no text. The guard `test_an_unencodable_question_fails_the_shape_by_name` fails on the step head with two assertion failures on both interpreters, the answer kind by crash and the refusal kind by acceptance, and passes after the fix. Elenchus against the fix commit under the runbook's runner contract returns `guarded`, "the runner report records a parent assertion failure", with executed 161, assertion_failures 2, errors 0, skipped 1. The trade: a refusal-kind document with an unencodable question moves from accepted to refused; no committed record is affected, and the fixture, the reference release and every other probe outcome are unchanged by the fix.

### Gates, suites and fixture

The three bundled lints exit 0 at the step head and again after the fix:
Phylax and Ephoros over `plugins` and `tests`, Hypomnema over
`README.md AGENTS.md .agents plugins docs`. The Berean suite reports
`Ran 161 tests`, `OK (skipped=1)` on Python 3.9.6 and 3.12.13 at the step head
and `Ran 162 tests`, `OK (skipped=1)` on both after the fix. The root suite
reports 350 tests OK, `tests.test_evolution_contract` 9 tests OK,
`scripts/promise_machine.py check` prints `clean: 14 plugin(s), 14 copy/copies`
and `coverage --check` prints `promises=71 coverage_rows=71 coverage_selected=71`.
Horos reports `boundary matches the tree`, `git diff --check` is clean, and
Imprimatur scores the five changed Markdown files 100.0 with no defects.
Protasis accepts the committed study in `--study` mode and the committed
runbook in runbook mode, and both copies under `docs/berean-question-spans/`
are byte-identical to the receipted ones at
`298ca6544d45168463c80b8a528b3a020a7205578520c20ccfcc5d69c6afb505` and
`41fdc1dc92e29ab1dd4e81e3c07e12ce52dbd12623db0d6c94eb9f904ba7d6d4`. The three
step commits carry good local signatures, one co-author trailer and one
origin trailer each.

The fixture was rebuilt through `release_fixture.build` into a scratch
directory and `diff -r` against the committed `pass-release` finds no
difference, before and after the fix; the release digest is
`7993b7a7a28c5f1fbc656016ec89c707bd7d7314609a2d21316e3ef6aa057dd2`.
`verify-release` on it passes every named check, `run-evals` grades 7 of 7,
and `c-reclassified` passes as `rejected` with the reason
`answer-shape (sentence 3 is user_supplied and names no span of the question)`.
No byte under `plugins/berean/examples/goldfinch-demo-v0/` changed;
`verify-release` on the reference release passes and `demo.py` ends with
`every stage held`. The emitter exits 0, writes one file at the named path
with mode 0600 and nothing else, and its payload is
`{"complete": true, "errors": 0, "expectedFailures": 0, "failures": 0,
"schema": "elenchus.unittest.v1", "skipped": 1, "testsRun": 161,
"unexpectedSuccesses": 0}` at the step head and `"testsRun": 162` after the
fix. It imports `tests.support` before loading the shared writer by file path
under a private module name, the comment states why, and `plugins/berean/tests`
is a regular package, so the writer's own `sys.path` insert cannot rebind
`tests`.

The `berean-v0.2.0` row was checked against the contract.
`sha256("open|wildcat-reference-release|<current frontier>|<next fiat job>\n")`
recomputed from the ledger's four header fields is
`ee99e8539e4b67e18c9ec9640358cc5d9a27fe167069ce8e03a8d75d7cefe987`, equal to
both rows' digests; the row is a generation from `berean-v0.1.0`, retains
`wildcat-reference-release`, and the `Frontier status`, `Frontier revision`,
`Current frontier` and `Next Fiat job` lines are byte-identical to the run
branch's. `SKILL.md` frontmatter reads `0.2.0`; the package reads `0.1.2` on
`plugins/berean/.claude-plugin/plugin.json`,
`plugins/berean/.codex-plugin/plugin.json` and `.claude-plugin/marketplace.json`
and on the pins in `plugins/berean/tests/test_scaffold.py` and
`tests/test_version_propagation.py`; the remaining `0.1.1` strings in the
marketplace manifest belong to other plugins. The `berean-answer-o` selector
resolves to `test_a_user_supplied_fact_names_the_question_spans_it_rests_on`,
which still refuses `["c1"]`, `["r1"]` and `["question:7-21", "c1"]` with the
detail `no artefact behind it`, so its claim that the nearest overclaim stays
unavailable holds. The `<!-- marketplace-context -->` blocks in
`plugins/berean/AGENTS.md`, `plugins/berean/README.md`,
`plugins/berean/skills/berean/SKILL.md`, `README.md` and `AGENTS.md` are
unchanged.

Guard strength was checked by restoring the run branch's `answers.py` over the
step tree and running the Berean suite on both interpreters:
`Ran 161 tests`, `FAILED (failures=46, errors=7, skipped=1)` on each, 53
failure and error entries over 28 distinct test methods, 9 in `test_answers`
(every `QuestionSpanTests` method and the renamed `GateOneTests` method), 7 in
`test_release`, 4 in `test_evals` and 8 in `test_promote`, the last three
modules because the fixture's bound sentence is refused by the old rule. The
file was restored with `git checkout` and `git status --short` was empty
afterwards.

### Register and prose

The register, id by id. `untrusted-answer-json`: the only read paths are
`jsonio.load` and `jsonio.loads`; the size, depth, duplicate-key and float
refusals precede the span parser, and the one string that slipped through
them, a lone surrogate, is S1-R1-01. `span-grammar`: `question`, `question:`,
`question:7`, `question:7-`, `question:07-21`, `question:+7-21`,
`question:7-21-3`, `Question:7-21`, a leading or trailing space, `\n`, `\r`
and `\x00` suffixes, an eight-digit offset, a negative offset, Arabic-Indic
and fullwidth digits all fail as grammar with one detail that never echoes
the reference; `question:0-9999999` parses and fails on bounds, so the digit
bound holds before `int` on both interpreters. `span-bounds`: `question:0-0`,
`question:7-7` and `question:21-7` fail as empty or inverted, `question:22-23`
and `question:7-23` leave the 22 byte question, `question:21-22` and
`question:0-22` pass. `span-utf8`: in a question with `—`, with a
combining `́` and with the 4-byte `\U0001F600` at bytes 23 to 27, every
cut inside a character (23-24, 23-25, 23-26, 24-27, 25-27, 26-27, 22-25,
24-26) fails as split UTF-8 and the whole character passes. `span-blank`: a
single space, two tabs and a no-break space fail as blank; a zero-width space
passes, because `str.strip` does not treat U+200B as whitespace, which is the
rule `jsonio.stated` applies to every stated field. `artefact-ref-refused`:
`["c1"]`, `["r1"]` and `["question:7-21", "c1"]` on a `user_supplied` sentence
fail with the retained reason. `id-prefix-collision`: a citation id
`question:7-21` and a read id `question:` fail at collection with a detail that
names the prefix and not the id; the prefix and the grammar are both
case-sensitive, so `Question:7-21` is an ordinary id and no string resolves
two ways. `diagnostic-output`: across every refusal above, no `answer-shape`
detail contained the question text, an unparsed reference or a decoded span;
the details carry the sentence index, the reference position, the parsed
offsets and the encoded length, `release.verify` wraps them as
`{path}: {name} ({detail})`, `evals.grade` as `the checker refused it: ...`,
and `berean.py` prints `Check.line()`. `other-classes-unchanged`: every
existing `test_answers` verdict holds, the named check lists of
`answers.check` and `release.verify` are unchanged, and a `user_supplied`
sentence in a refusal document still fails as `a refusal carries no
sentences`. `fixture-regeneration`, `report-consistency`,
`goldfinch-untouched`, `coverage-pin`, `ledger-integrity` and
`version-surfaces`: the paragraphs above. `partial-run`: every command in the
runbook's exit list ran to exit 0 on this tree, on both interpreters where
the runbook names both, and the counts above are the observed ones.

The prose was read against the code. `docs/answers.md` states the grammar,
the byte unit, the four slice conditions, multiple spans and the reserved
prefix, and separates what the check proves from what it does not; gate 1 and
the `berean-answer-evidence` refuses clause in `SKILL.md` and the schema
`description` say the same rule in fewer words. None of them says more than
the code does. The rule's premise that `question` has a UTF-8 encoding is
what S1-R1-01 enforces; no prose changed in the fix, so the prose phase may
decide whether that premise deserves a sentence.

### Cost and leads

Resource cost was measured rather than guessed: 500 whole-question spans over
a 1 MiB question take 0.019 s in ASCII (0.04 ms per span) and 0.181 s in
two-byte characters (0.36 ms per span), and 5000 citation ids against 20000
span references take 0.728 s. At the 4 MiB `jsonio` ceiling a crafted
document could hold about 130000 whole-question references over a 2 MiB
question, about 90 s of CPU.

Leads not pursued: five. First, a list-typed reference on a `document`,
`chain_read` or `calculation` sentence crashes `validate` with
`TypeError: unhashable type: 'list'` at `answers.py:104`; the run branch
crashes the same way, the diff does not touch that branch, and the new
`_question_span` guards its own class with an `isinstance` check, so the
asymmetry is visible but pre-existing. It belongs in a `berean-wish` filing
rather than in this round's stacked branch. Second, a `jsonio`-level refusal
of lone surrogates would cover every string in every document kind, including
citation display text and sentence text; `jsonio.py` is outside the step's
file list, and the fix proves the one string the step slices. Third, the
resource cost above: Metron has no gate here by the study's section 10, the
shape mirrors the citation re-slice and the `citation_ids | read_ids` union
the calculation branch already computes per reference, and a boundary-only
UTF-8 check would not remove the decode the blank check needs. Fourth,
duplicate spans, zero-width-space spans and combining-mark spans pass the
mechanical check as real, whole, non-blank bytes; whether a sentence rests on
them honestly stays with gate 6 and the evaluation corpus, as the study says.
Fifth, `release.verify` still walks every answer after `release-answers`
finds a fault, so a large release reports every faulty answer rather than the
first; that is the existing design and no register line asks for otherwise.

## Step 1, round 2 -- 2026-08-25

Non-Solidity re-check of the tree with round 1's fix applied, at
`a612861848f4a383d8a03afb4863595c48e2f805` on the stacked branch. The diff
since the step head is `115231a397a93479813cf7cb79f24988c8518cea`, two files,
43 insertions and 3 deletions in `plugins/berean/scripts/berean_lib/answers.py`
and `plugins/berean/tests/test_answers.py`, plus the round 1 record. The
Pashov pair and fizz stay waived; the diff carries no Solidity. Zero findings.

### Gates and suites

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and
`tests`, Hypomnema over `README.md AGENTS.md .agents plugins docs`. The
Berean suite reports `Ran 162 tests`, `OK (skipped=1)` on Python 3.9.6 and
3.12.13. The root suite reports 350 tests OK, `tests.test_evolution_contract`
9 tests OK, `scripts/promise_machine.py check` prints `clean: 14 plugin(s),
14 copy/copies` and `coverage --check` prints `promises=71 coverage_rows=71
coverage_selected=71`. `run-evals` grades 7 of 7 on the conformance fixture,
`verify-release` exits 0 on the fixture and on the reference release, Horos
reports `boundary matches the tree`, `git diff --check` is clean, and
Imprimatur scores the five changed Markdown files and this record 100.0 with
no defects.

### Register

Four register ids are reachable by the fix and each was re-checked against
it. `untrusted-answer-json`: the encode now happens at `jsonio.stated`, before
the kind branch, so both document kinds are held to it; a lone surrogate at
character 22 and one at character 0 are refused as `answer-shape` by name, a
valid surrogate pair (`😀`, U+1F600) decodes to four bytes whose
whole span passes and whose cut span fails as split UTF-8. `diagnostic-output`:
the new detail carries the character position only; probes of the
lone-surrogate, grammar and out-of-range refusals contained neither the
question text nor the reference string. `other-classes-unchanged`: every
existing verdict holds at 162 tests; the one behaviour the fix adds beyond the
span rule is that a refusal-kind document whose question cannot be encoded
moves from accepted to refused, which is the fail-closed posture at the
boundary the register's first line names, changes no field, vocabulary or
named check, and affects no committed record. `partial-run`: every command
above exited 0. The remaining twelve ids sit in files the fix does not touch;
round 1's evidence for them stands on an unchanged tree.

Both commits on the stacked branch carry good local signatures, one co-author
trailer and one origin trailer each; the step branch is unchanged at
`df7ca171d2c8cf1bab091523d4caa13c4ef7c8c4`.

Leads not pursued: none new. Round 1's five stand as recorded.
