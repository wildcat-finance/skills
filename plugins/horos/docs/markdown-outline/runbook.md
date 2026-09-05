# Runbook: ship the Markdown outline extractor

Derived from the receipted study at `.hexaemeron/study.md`. No task issue is
bound. The run branch is `fiat/ship-the-markdown-outline-extractor-the-census-n`,
cut from `main` at `bbb9de64b23da28cdcc56e3fcf975a0ecbed45e8`. Step 1 branches
from the run branch; every later step branches from the step below it.

Every `unittest` invocation below carries
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`,
written `<sign-off>` for brevity; expanding it is mandatory. `<imprimatur.py>`
means `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`. The root
suite's exit is held against a clean detached snapshot of the step's head,
because inside a Fiat worktree it is red on the two tests issue 1228 names.
Any step that adds a tracked file regenerates `.horos/boundary.json` and
`.horos/candidates.json` in the same commit (study assumption 8).

The selected design is `line-scanner` (study section 4): a line-oriented
scanner in the fixed extractor shape, stdlib only, headings and fences
sliced verbatim, front matter named, HTML blocks and an unterminated fence
confessed.

```design-lock
schema | protasis-design-evidence/v1
sha256 | c8879b32c9405b0d91ae6b5a0789059457a54df2b81e217b081c30357b451256
candidate | line-scanner
```

## Step 1: Commit the spec copies

**Goal.** Put the receipted study and this runbook where the repository keeps
them, so the branch carries its own specification.
**Entry.** The run branch at `bbb9de64b23da28cdcc56e3fcf975a0ecbed45e8`,
clean tree, root suite 1233 OK in a clean snapshot, horos suite 239 OK.
**Exit.** `plugins/horos/docs/markdown-outline/study.md` and
`plugins/horos/docs/markdown-outline/runbook.md` committed, then all of:
`python3 <imprimatur.py>` exit 0 on both copies,
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0,
`<sign-off> python3 -m unittest discover -s tests` green in a clean snapshot,
and `<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green (239 tests at this step).
**Files.** `plugins/horos/docs/markdown-outline/study.md`,
`plugins/horos/docs/markdown-outline/runbook.md`, `.horos/boundary.json`
and `.horos/candidates.json` where the two tracked files move the counts.
**Tests.** None written; the two existing suites are the gate. Elenchus
runner: `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/elenchus-step-1.json`.
**Disciplines.** hypomnema: the committed spec copies are a record home the
study's section 12 names. phylax: none, documentation only. ephoros: none,
nothing here runs unattended. metron: none, no performance claim. elenchus:
none, no failure in hand.

## Step 2: The Markdown outliner, its registry line and its pinned fixture

**Goal.** Ship the `line-scanner` extractor behind `horos.py map` for `.md`,
with a pinned fixture outline and one test per risk-register trap.
**Entry.** Step 1's exit tree.
**Exit.** All of, from the repository root:
`python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/examples/fixture-md/GUIDE.md`
printing the outline pinned in `plugins/horos/tests/test_md_outline.py`
byte for byte and exiting 0;
`python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/skills/horos/SKILL.md`
exiting 0 and printing `module: Horos`, `front matter: lines 1-6`,
`declarations: 16` and one confessed region;
`python3 plugins/horos/skills/horos/scripts/horos.py map` help text naming
the supported suffixes through `languages.supported()`;
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green with the new tests counted (about 254; the exact count is recorded at
exit); `<sign-off> python3 -m unittest discover -s tests` green in a clean
snapshot; `python3 plugins/horos/skills/horos/scripts/horos.py check .` exit
0; `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`
leaving `git status --short .horos/` empty; and the eight hostile inputs of
`.hexaemeron/design-reports/resolve.py` run once against the shipped module
with zero exceptions and each under 10 s, the figures recorded in the step's
audit record.
**Files.** `plugins/horos/skills/horos/scripts/languages/markdown/__init__.py`,
`plugins/horos/skills/horos/scripts/languages/markdown/markdown.py` (from the
study's `line-scanner` candidate, module docstring carrying the outline
definition and the register), `plugins/horos/skills/horos/scripts/languages/__init__.py`
(one `.md` registry line), `plugins/horos/skills/horos/scripts/horos.py`
(the `map` help strings only, naming the supported suffixes),
`plugins/horos/examples/fixture-md/GUIDE.md`,
`plugins/horos/tests/test_md_outline.py`, `.horos/boundary.json` and
`.horos/candidates.json`.
**Tests.** Written in `plugins/horos/tests/test_md_outline.py`, each observed
red against a deliberately broken rule before it is kept: the pinned
`GUIDE.md` outline byte for byte; registry dispatch for `.md` and refusal of
`.markdown`; one test per section 5 trap: `fence-shadowed-heading`
(backtick and tilde, indented up to three spaces, longer closing fence, text
after the closer does not close), `html-hidden-heading` (a heading inside an
HTML block is confessed, a type 7 block cannot interrupt a paragraph),
`setext-under-lazy-line` (a `---` under a lazy continuation is not a
heading; under an open paragraph it is an h2), `container-prefix` (a heading
behind `>` and a fence inside a list item that closes with the item),
`front-matter-phantom` (line 1 `---` with a closer is front matter, not a
setext h2), `unterminated-fence` (remainder confessed, `lexer:` line, exit 1),
`hostile-input` (empty file and CR-only file exit 0 without exception),
`no-execution` (a file whose body is executable Python is outlined and never
imported). Expected count: the horos suite grows from 239 by about 15.
Elenchus runner: `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/elenchus-step-2.json`.
**Disciplines.** phylax: the extractor reads one untrusted file and prints;
it must not import, execute or write, and the hostile set bounds its time
(study section 9). elenchus: every trap test is observed red first against a
rule broken on purpose in a scratch copy. metron: the section 10 budget
applies; the corpus outline time is re-measured in step 3 before any claim.
hypomnema: the outline definition and register live in the module docstring
and the fixture pins them. ephoros: none, the exit code and the `lexer:` and
`unparsed:` lines already answer what a reader asks.

## Step 3: The differential corpus and its evidence bundle

**Goal.** Hold the shipped extractor against markdown-it-py over every
tracked `.md` file of this repository at a named commit and record the run
as a machine-checked bundle.
**Entry.** Step 2's exit tree, with a scratchpad virtualenv holding
markdown-it-py 4.2.0 (dev-time only, never in the tree).
**Exit.** All of: `plugins/horos/docs/evidence/skills-markdown-outline.md`
and `skills-markdown-outline.results.json` committed, the bundle naming the
commit it ran at, the corpus size (files and bytes), the declared altitudes
(headings by level and line, fences by first and last line), the two declared
exclusions (front matter on both sides; an unterminated fence confessed
rather than matched), and the capture lines with prefix `mdoutline` whose
totals equal the results file; the results showing zero crashes, zero
unconfessed misses and zero extras; the corpus outline time re-measured by
`python3 .hexaemeron/design-reports/resolve.py line-scanner corpus-outline-ms`
against the shipped module and at or under 1,000 ms, quoted in the bundle;
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green with `plugins/horos/tests/test_evidence.py` extended by two tests
(bundle matches results; acceptance holds, including `fence_matched` equal
to `fence_oracle`); `<sign-off> python3 -m unittest discover -s tests` green
in a clean snapshot; `python3 <imprimatur.py> plugins/horos/docs/evidence/skills-markdown-outline.md`
exit 0; `python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0.
**Files.** `plugins/horos/dev/md_oracle.py` (the study's oracle and
differential driver, venv-run, absent from every runtime and test path),
`plugins/horos/docs/evidence/skills-markdown-outline.md`,
`plugins/horos/docs/evidence/skills-markdown-outline.results.json`,
`plugins/horos/tests/test_evidence.py`, `.horos/boundary.json` and
`.horos/candidates.json`.
**Tests.** Two added to `plugins/horos/tests/test_evidence.py` on the pattern
of the Go and Solidity bundle tests: the `mdoutline` capture lines equal the
committed results totals, and the acceptance (zero crashes, zero unconfessed
misses, zero extras, `fence_matched` equal to `fence_oracle`) holds. Expected
count: the horos suite grows by 2. Elenchus runner:
`python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`, report
format `unittest-json-v1`, report file `.hexaemeron/elenchus-step-3.json`.
**Disciplines.** metron: the corpus time is re-measured here against the
shipped module before the bundle claims it. elenchus: a corpus mismatch
becomes a fixture case in `test_md_outline.py` before any rule changes.
hypomnema: the declared altitudes and exclusions are recorded in the bundle
and the oracle's docstring. phylax: the oracle runs dev-time under a
virtualenv outside the tree and is imported by nothing shipped. ephoros:
none, nothing runs unattended.

## Step 4: Record the row, reconcile the prose and re-pin the skill file

**Goal.** Close the held job in the ledger as mature, reconcile every
mutable prose surface, edit `SKILL.md` once with its fixture chain re-pinned
in the same commit, and regenerate the stale census.
**Entry.** Step 3's exit tree.
**Exit.** All of: `plugins/horos/skills/horos/EVOLUTION.md` carrying exactly
one new history row, axis evolution, version `horos-v12.3.3`, frontier
revision `markdown-outline-extractor`, header `Frontier status: mature` and
`Next Fiat job: None -- mature`, the row's evidence linking the committed
study and the bundle and its change text carrying the census evidence of
study section 12; `plugins/horos/skills/horos/SKILL.md` frontmatter at
`version: "12.3.3"`, its map paragraph and marketplace-context block naming
Markdown among the mapped languages, the reviewed span unchanged (manifest
`span_sha256` still `0f2fb54b8f737de4b8ec42b88bdc6d9238f65de8525847c81381cbb83d0e91a2`),
and the fixture chain re-pinned in the same commit with
`~/.claude/tools/repin_fixture.py` and `~/.claude/tools/repin_evidence.py`
so that `python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json`
prints a `run.summary` with outcome `accepted` and no refused record and
`python3 scripts/promise_machine.py coverage` prints `clean`, the carried
token counts and parity responses said so in the step's audit record;
`.horos/census.json` regenerated once with
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
and its `.md` row quoted in the bundle; `<sign-off> python3 -m unittest tests.test_marketplace_prose`
green; `<sign-off> python3 -m unittest tests.test_evolution_contract` green;
`python3 <imprimatur.py> <file>` exit 0 for every prose file this step
touches; `python3 plugins/horos/skills/horos/scripts/horos.py check .` exit
0; `<sign-off> python3 -m unittest discover -s tests` green in a clean
snapshot; `<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green.
**Files.** `plugins/horos/skills/horos/EVOLUTION.md`,
`plugins/horos/skills/horos/SKILL.md`, the seven-file fixture chain
(`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/model.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/source-spans.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/compact.wai`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json`,
`tests/promise_machine_coverage.json`), `plugins/horos/README.md`,
`plugins/horos/AGENTS.md`, `FUTUREPROOFING.md`,
`plugins/horos/docs/evidence/skills-markdown-outline.md` (census row),
`.horos/census.json`, and `.horos/boundary.json` and
`.horos/candidates.json` where the regeneration moves them. The `SKILL.md`
frontmatter `description` and the Codex `longDescription` stay as they are
(ask-first, study section 12).
**Tests.** None written; `tests.test_marketplace_prose`,
`tests.test_evolution_contract` and the two suites are the gate. Elenchus
runner: `python3 tests/run_tests.py --elenchus-report {report}`, report
format `unittest-json-v1`, report file `.hexaemeron/elenchus-step-4.json`.
**Disciplines.** hypomnema: the ledger row is the record of the maturity
call and the reconciled blocks are the record homes the study's section 12
names; the carried re-pin is recorded in the audit record. metron: none, no
performance claim beyond step 3's. phylax: none, prose, ledger and fixture
digests only. ephoros: none, nothing runs unattended. elenchus: none, no
failure in hand.

## Step 5: Demonstrate the shipped extractor

**Goal.** Run the study's demo path end to end at the run head and record
the transcript.
**Entry.** Step 4's exit tree.
**Exit.** From the repository root, in order, all as stated:
`python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/examples/fixture-md/GUIDE.md`
printing the pinned outline, exit 0;
`python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/skills/horos/SKILL.md`
exit 0 with `module: Horos`, `front matter: lines 1-6`, `declarations: 16`;
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green at the count step 3 recorded;
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0 with
`boundary matches the tree`;
`python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json`
printing a `run.summary` with outcome `accepted`; and
`<sign-off> python3 -m unittest discover -s tests` green in a clean detached
snapshot of the run head. The transcript is committed as the last section of
`plugins/horos/docs/evidence/skills-markdown-outline.md` and carried in the
step's audit round record; `python3 <imprimatur.py>` exit 0 on the bundle
after the append.
**Files.** `plugins/horos/docs/evidence/skills-markdown-outline.md` (a final
"Demonstration at the run head" section), `.horos/boundary.json` and
`.horos/candidates.json` where the append moves them, and the run's audit
record through its round; no source file changes.
**Tests.** None written; the demo path is the gate. Elenchus runner:
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`unittest-json-v1`, report file `.hexaemeron/elenchus-step-5.json`.
**Disciplines.** ephoros: the demo exercises the whole observable surface,
exit codes and the printed outline (study section 8). phylax: none, nothing
new opens. metron: none, the budget was settled in step 3. elenchus: none
unless the demo fails, which stops the line. hypomnema: the transcript's
home is the bundle and the audit record.
