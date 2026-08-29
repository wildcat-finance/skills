# Runbook: isolate disposable fixture signing

Derived from the receipted study at `.hexaemeron/study.md`. Task issue:
[wildcat-finance/skills#621](https://github.com/wildcat-finance/skills/issues/621).
The run branch is `fiat/621-isolate-disposable-fixture-signing`, cut from `main`
at `f5d94a5f27168e6c0faecd43eee426f6ee892cdc`. Step 1 branches from the run
branch; every later step branches from the step below it.

## Host conditions every command below assumes

Two facts about this machine are written into the commands rather than left to
the reader, so each one runs exactly as printed.

**The interpreter.** `AGENTS.md` defines bare `python3` as the exact patch in
`.python-version`, which is 3.14.6. On this host bare `python3` is 3.12.13 and
the pinned patch is `/Users/kethcode/.local/bin/python3.14`. Every command below
spells that absolute path. A reader on another machine substitutes their own
3.14.6 and changes nothing else.

**Node 26 for the Hexaemeron suite.** Host `node` is v22.22.3, and
`plugins/hexaemeron/tests/test_elenchus_checker.py` runs `node --version` and a
`node:test` emitter that needs 26. Every command that runs the Hexaemeron suite
is wrapped in `npx --yes --package=node@26.6.0 --call '...'`, spelled in full.

The study's section 3 also fixes a constraint that is not a host condition and
must not be relaxed: a hostile signing configuration is supplied to a test as a
`GIT_CONFIG_GLOBAL` file, never through the `GIT_CONFIG_COUNT` and
`GIT_CONFIG_KEY_n` triple, because the triple outranks repository-local config
and reports a correct fix as broken.

**The hostile configuration comes from a committed generator.** `.hexaemeron/`
is controller state whose own `.gitignore` is a single `*`, so git never sees
anything written there, and a step whose proof rests on a file in it cannot be
reproduced by a reviewer who checks the branch out. Step 2 therefore commits
`tests/hostile_signing_harness.py`; the guard imports it, so there is one
definition of what hostile means, and every later step runs it. Each step that
needs the configuration spells these three lines in its own exit, so no exit
depends on a command printed under a different step:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

The directory is a fresh temporary one rather than a path inside the repository,
because `.elenchus/` is neither tracked nor ignored and generating into it would
leave untracked files behind and dirty a tree the next step expects clean.

## What Elenchus can and cannot establish for this delivery

Every step declares the runner contract Protasis requires, and steps 3 and 4
also declare their expected exact result, so Warden records it rather than
investigating it.

This delivery changes test files only. Elenchus applies a commit's changed test
files to its parent and runs the declared command there. When the fix and the
guard are both test files, applying the changed set carries the fix to the
parent as well, so the guard passes there and the mechanical result is
`unguarded`. That is a property of a test-only change, not a defect in it, and
the repository has recorded the same expected value before: the round log for
the Elenchus audit-round verdict step 3 names `unguarded` as "the exact
Elenchus result, as expected for a documentation-only fix".

The acceptance proof therefore does not rest on an Elenchus verdict. It rests on
step 5's demo path, which is a command and an empty file.

## Step 1: Commit the spec copies and add the root Elenchus runner

**Goal.** Put the receipted study and this runbook where the repository keeps
them, and give the repository-wide suite an Elenchus report writer, so every
later step can declare a runner contract for a changed file under `tests/`.

**Entry.** The run branch `fiat/621-isolate-disposable-fixture-signing` at
`f5d94a5f27168e6c0faecd43eee426f6ee892cdc`, clean tree. The receipted study at
`.hexaemeron/study.md` and this runbook at `.hexaemeron/runbook.md`.

**Exit.** The two documents are committed under `docs/disposable-fixture-signing/`
byte-identical to the receipted artefacts, and `tests/run_tests.py` writes a
valid report. All of the following exit 0:

```bash
cmp .hexaemeron/study.md docs/disposable-fixture-signing/study.md
cmp .hexaemeron/runbook.md docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/disposable-fixture-signing/study.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/disposable-fixture-signing/study.md docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/disposable-fixture-signing/study.md docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-1.json
/Users/kethcode/.local/bin/python3.14 -c "import json,pathlib;d=json.loads(pathlib.Path('.elenchus/fiat-621-step-1.json').read_text());assert d['schema']=='elenchus.unittest.v1' and d['complete'] is True and d['failures']==0 and d['errors']==0, d"
/Users/kethcode/.local/bin/python3.14 plugins/horos/skills/horos/scripts/horos.py check .
```

Every relative link in both committed documents resolves from
`docs/disposable-fixture-signing/`, which the hypomnema command above proves:
`H001` fires on a relative link that resolves to nothing.

**Files.** Created: `docs/disposable-fixture-signing/study.md`,
`docs/disposable-fixture-signing/runbook.md`, `tests/run_tests.py`,
`tests/test_root_elenchus_runner.py`. Changed: `.horos/boundary.json` only if
the horos check above reports drift.

`tests/run_tests.py` is a faithful port of `plugins/hexaemeron/tests/run_tests.py`,
which is 241 lines and roughly 20 of them are path containment. Port that
containment rather than reimplementing it: reject a path containing `..`; refuse
a target that is already a symlink or already exists; resolve against the
worktree root and require `relative_to` to succeed; walk each parent component
with `lstat` and refuse a non-directory; probe for `os.O_DIRECTORY`,
`os.O_NOFOLLOW` and `dir_fd` support and refuse without them; open the root with
`O_RDONLY | O_DIRECTORY | O_NOFOLLOW` and compare `st_dev` and `st_ino` against
the pre-open stat to catch a worktree replaced during inspection; create report
directories through `dir_fd` at mode `0o700` without following a symlink; and
remove a failed write only while the target is still the inode that was created.
The payload is the same `elenchus.unittest.v1` object with `schema`, `complete`,
`testsRun`, `failures`, `errors`, `skipped`, `expectedFailures` and
`unexpectedSuccesses`. The two intended divergences are the discovery root,
which is `tests` rather than the Hexaemeron test directory, and the top-level
directory passed to `unittest`. Any other divergence is a defect.

**Tests.** `tests/test_root_elenchus_runner.py` imports the new module and
covers the refusals rather than only the success path: a `..` component, an
absolute path outside the worktree, an existing regular file, an existing
symlink, a parent component that is a regular file, and two report paths named
in one invocation. It also asserts the written payload carries every one of the
eight schema keys and that `schema` reads exactly `elenchus.unittest.v1`.
Expected new tests: 8 or more. The root suite's existing count must not fall.

The source-bound Elenchus runner contract for any audit repair in this step:

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-1.json
```

The format value is `unittest-json-v1`. The string `elenchus.unittest.v1` is the
schema written inside the report and is never a format value; the closed tuple
of accepted formats is at `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:29`.

**Disciplines.** phylax: the runner accepts a filesystem write path from the
command line, which is a boundary this repository did not previously open under
`tests/`, and the ported containment logic is the control that closes it.
ephoros: the report this runner writes is the artefact every later audit round
reads, and a missing, stale or malformed one is scored `inconclusive` rather
than failed, so its refusal messages must name which precondition failed.
metron: none, the step adds two documents and one runner and makes no
performance claim. elenchus: none, no failure is in hand; the guard arrives in
step 2. hypomnema: the committed study and runbook are the durable record of
this delivery, and ADR-045 is deliberately deferred to step 5 because its
content is not settled until the rule has been applied.

## Step 2: Add the disposable-fixture signing guard and its hostile-configuration harness

**Goal.** Establish the rule behaviourally before any fixture is touched: build
a hostile signing configuration, prove it is genuinely hostile, prove the
repository-local declaration defeats it, and leave the configuration behind as a
committed generator every later step runs.

**Entry.** Step 1's exit state: the spec copies committed, `tests/run_tests.py`
present and writing a valid report, every command in step 1's exit at 0.

**Exit.** The guard is committed and green, and it fails on a repository where
the local declaration is removed. All of the following exit 0:

```bash
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-2.json
/Users/kethcode/.local/bin/python3.14 -m unittest tests.test_disposable_fixture_signing -v
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
```

The committed generator produces a usable harness. All of these exit 0:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

```bash
test -s "$HOSTILE_DIR/hostile.gitconfig"
test -x "$HOSTILE_DIR/hostile-signer"
test ! -s "$HOSTILE_DIR/sentinel.log"
```

And this refusal check exits non-zero, proving the guard is not vacuous:

```bash
/Users/kethcode/.local/bin/python3.14 -m unittest tests.test_disposable_fixture_signing.NegativeControl.test_the_hostile_signer_is_reached_without_the_local_declaration \
  && echo "GUARD IS VACUOUS" && exit 1
```

**Files.** Created: `tests/test_disposable_fixture_signing.py` and
`tests/hostile_signing_harness.py`. No fixture under test is changed in this
step; the guard exercises repositories it constructs itself, so both ends are
green.

`tests/hostile_signing_harness.py` holds the harness the guard uses in-process
and a `--emit <dir>` entry point that writes `hostile.gitconfig` and the
executable `hostile-signer` into the named directory and truncates
`sentinel.log` beside them. The three filenames are fixed so a caller can name
them without parsing output. The guard imports the module rather than
duplicating the recipe, so the configuration every later step runs is the same
one the guard proves hostile.

**Tests.** `tests/test_disposable_fixture_signing.py`, in the order the study's
section 11 fixes:

1. The harness, imported from `tests/hostile_signing_harness.py`, writes a
   hostile `GIT_CONFIG_GLOBAL` file and a signing program
   that appends to a sentinel and exits non-zero, across three arms:
   `gpg.format=openpgp` with `gpg.program`, `gpg.format=ssh` with
   `gpg.ssh.program`, and an unsigned control. `GIT_CONFIG_SYSTEM=/dev/null`
   accompanies each. Both variables are set on the child process only and never
   on `os.environ`.
2. Negative control: a disposable repository built without the local
   declaration commits, and the test asserts the commit failed and the sentinel
   recorded an invocation. This is the assertion that makes the rest mean
   something, and its failure message says the hostile configuration failed to
   be hostile rather than that the fix is broken.
3. Positive case: the same construction with
   `git config --local commit.gpgsign false` asserts the commit succeeded, the
   sentinel is empty, and `git log -1 --format=%G?` reads exactly `N`. A commit
   that succeeds but is signed fails this test.
4. Enumeration: one representative test from each covered suite runs as a
   bounded subprocess under the hostile configuration, asserting exit 0 and an
   empty sentinel. This step registers no suite yet; steps 3 and 4 add their
   entries. The list is a module-level constant so a reader can see the covered
   set without reading the test bodies.

The guard fails rather than skips when git is unavailable or the hostile
configuration cannot be written, because a silent skip reports as a pass. Every
subprocess uses fixed argv, no shell, `sys.executable` rather than a `PATH`
lookup, and a timeout so a reintroduced pinentry stall fails the guard instead
of hanging it. Expected new tests: 6 or more.

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-2.json
```

**Disciplines.** phylax: this step opens all three boundaries the study's
section 9 names, writing and executing a signing program, redirecting git's
global and system configuration through the environment, and spawning suites as
subprocesses; the controls are the temporary directory, child-process-only
variables, fixed argv and a bounded timeout. ephoros: the guard is the only test
that fails when the cause is signing rather than the change under test, so it
owns all four on-call questions in the study's section 8, and it reports the
sentinel's contents on failure rather than only its emptiness. metron: none, the
guard bounds its own runtime with a timeout but claims no budget; the
measurement is step 5. elenchus: this step is the guard convention itself, and
the negative control is what stops it passing for the wrong reason. hypomnema:
none, the scope rule this guard enforces is recorded by ADR-045 in step 5, and a
second record here would be edited before anyone read it.

## Step 3: Declare the signing policy on the root and Horos construction sites

**Goal.** Apply the rule to the five construction sites in the root and Horos
suites, and extend the guard's enumeration to both.

**Entry.** Step 2's exit state: the guard committed and green, its enumeration
empty, `tests/hostile_signing_harness.py` committed, every command in step 2's
exit at 0.

**Exit.** Both suites pass under the hostile configuration, and the guard now
covers them. All of the following exit 0:

```bash
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s plugins/horos/tests -t plugins/horos
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-3.json
/Users/kethcode/.local/bin/python3.14 plugins/horos/skills/horos/scripts/horos.py check .
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
```

And, with this step's own hostile configuration generated by the committed
harness from step 2:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

```bash
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 -m unittest discover -s plugins/horos/tests -t plugins/horos
test ! -s "$HOSTILE_SENTINEL"
```

**Files.** Changed: `tests/test_boundary_currency.py` (the `GuardMutationTests`
setup at line 166), `plugins/horos/tests/test_scoped_entry.py` (line 64),
`plugins/horos/tests/test_demonstration.py` (line 53),
`plugins/horos/tests/test_universe.py` (lines 56, 134 and 195), and
`tests/test_disposable_fixture_signing.py` (enumeration entries for both
suites).

Each edit is one call, `git config --local commit.gpgsign false`, against the
fixture repository, placed immediately after the `git init` that created it and
before any other configuration. The three Horos modules each carry their own
byte-identical `git(root, *args)` helper; the line goes at each call site, not
into a shared module, per the study's section 3 non-goal. One comment per suite,
not per site, says why the line is there: fixture history is not signing
evidence, so inherited signing must not decide whether the repository can be
built. Do not touch `tests/test_boundary_currency.py:140` or
`plugins/horos/tests/test_scoped_entry.py:140`; neither commits, and the study's
section 2b records them as out of scope.

**Tests.** No new test module. `tests/test_disposable_fixture_signing.py` gains
one enumeration entry per suite, each naming a representative test that commits
fixture history: for the root suite a `GuardMutationTests` method, for Horos a
`UniverseTests` method. Both existing suites keep their counts; the root suite
and the Horos suite must report the same number of tests as at step 2's exit,
plus nothing.

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-3.json
```

Expected exact Elenchus result: `unguarded`. The fix and the guard are both test
files, so applying the changed set to the parent carries the fix there too and
the guard passes on the parent. Record that value; it is not a finding. The
acceptance evidence for this step is the pair of hostile-configuration commands
in the exit above.

**Disciplines.** phylax: every edit is a filesystem-affecting `git config` write,
and the register entry `config-scope-escape` is what Warden checks, that each
call names its own fixture repository and cannot fall through to the outer
checkout. ephoros: none, the step emits no new signal; the guard made the
signing cause legible in step 2 and this step only extends its enumeration.
metron: none, no performance claim is made here; both measurements are step 5.
elenchus: the step extends the guard to the two suites it changes and declares
`unguarded` in advance with the reason, so the audit round records rather than
investigates it. hypomnema: none, no decision is taken here that ADR-045 does
not already carry.

## Step 4: Declare the signing policy on the Hexaemeron and Hermes construction sites

**Goal.** Apply the rule to the remaining five construction sites, and extend
the guard's enumeration to both suites.

**Entry.** Step 3's exit state: the root and Horos sites declaring the policy,
the guard enumerating both suites, the committed harness from step 2 available,
every command in step 3's exit at 0.

**Exit.** Both remaining suites pass under the hostile configuration. All of the
following exit 0:

```bash
npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py'
/Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-4.json
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
```

And, under a hostile configuration this step generates for itself:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

```bash
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py'
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
test ! -s "$HOSTILE_SENTINEL"
```

**Files.** Changed: `plugins/hexaemeron/tests/test_elenchus_checker.py` (the
`Fixture` constructor at line 114),
`plugins/hexaemeron/tests/test_kronos_scoreboard.py` (lines 664 and 759),
`plugins/hermes/skills/hermes/scripts/test_hermes.py` (line 173),
`plugins/hexaemeron/tests/test_hexctl.py` and
`plugins/hexaemeron/tests/test_fiat_skill.py` for the scope hardening only, and
`tests/test_disposable_fixture_signing.py` (enumeration entries for both
suites).

The Kronos site at line 759 is a `git clone`, not a `git init`; the declaration
goes immediately after the clone, because the rule is stated at creation
whichever verb created the repository. The hardening at
`plugins/hexaemeron/tests/test_hexctl.py:55` and
`plugins/hexaemeron/tests/test_fiat_skill.py:1458` adds the explicit `--local`
scope and moves the call to immediately after `init`; both are already correct
and neither is a defect, so this is uniformity, not repair. Do not change
`plugins/hexaemeron/tests/test_hexctl.py:1366` or `:1388`: both re-initialise
the repository `make_origin_checkout` already configured, and a re-init
preserves local config. Do not change
`plugins/hexaemeron/tests/test_issue_429_recovery.py` or the signature classes
of `plugins/hexaemeron/tests/test_hexctl.py`; the study's section 2b lists them
as excluded because signing is their subject.

**Tests.** No new test module. `tests/test_disposable_fixture_signing.py` gains
one enumeration entry per suite. The signature-verification legs must be shown
untouched: the Hexaemeron suite reports the same test count as at step 3's exit
plus nothing, and `git diff` over
`plugins/hexaemeron/tests/test_issue_429_recovery.py` is empty.

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-4.json
```

Expected exact Elenchus result: `unguarded`, for the reason step 3 gives.

**Disciplines.** phylax: the same `config-scope-escape` boundary as step 3, plus
the register entry `signature-test-weakening`, because this is the step that
touches the two files where signature-subject tests live and Warden must confirm
their assertions and counts are unchanged. ephoros: none, no new signal; the
enumeration entries reuse what step 2 established. metron: none, no performance
claim; the measurement is step 5. elenchus: the guard is extended to the two
remaining suites and `unguarded` is declared in advance with its reason.
hypomnema: none, ADR-045 in step 5 carries the scope rule including the
exclusions this step honours.

## Step 5: Measure the construction path, demonstrate under inherited signing, and record ADR-045

**Goal.** Run the problem statement's own demo path, record the before and after
the acceptance requires, and write the decision record that governs the rule.

**Entry.** Step 4's exit state: all ten construction sites declaring the policy,
the guard enumerating all four suites, the committed harness from step 2
available, every command in step 4's exit at 0.

**Exit.** The demo path passes, both measurements are recorded, and the decision
record is committed and lints clean.

First generate the hostile configuration with the harness step 2 committed:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

Then the demo path, which is the study's section 1 verbatim. All four exit 0:

```bash
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py'
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 -m unittest discover -s plugins/horos/tests -t plugins/horos
```

And the sentinel is empty, which is the other half of the criterion:

```bash
test ! -s "$HOSTILE_SENTINEL"
```

Then the remaining exit commands, all 0:

```bash
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-5.json
/Users/kethcode/.local/bin/python3.14 -m unittest tests.test_decision_records
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-045-declare-signing-policy-on-disposable-git-fixtures.md
/Users/kethcode/.local/bin/python3.14 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-045-declare-signing-policy-on-disposable-git-fixtures.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
/Users/kethcode/.local/bin/python3.14 plugins/horos/skills/horos/scripts/horos.py check .
```

Acceptance item 2 is proved by comparison rather than assertion, and both
commands must print nothing:

```bash
git config --global --list > /tmp/fiat-621-global-after.txt
diff /tmp/fiat-621-global-before.txt /tmp/fiat-621-global-after.txt
git -C . config --local --list | diff - /tmp/fiat-621-local-before.txt
```

The two `before` files are captured at this step's entry, before any suite runs.

**Files.** Created:
`docs/decisions/ADR-045-declare-signing-policy-on-disposable-git-fixtures.md`,
`docs/disposable-fixture-signing/measurement.md`. Changed:
`plugins/horos/docs/marker-self-exclusion/runbook.md` is deliberately not
changed; it recorded a true host condition at its own ref and ADR-045 supersedes
it rather than editing it.

ADR-045 carries the scope rule, the three rejected options from the study's
section 4 with the measured reason for rejecting the process-wide override, the
`GIT_CONFIG_GLOBAL` constraint, and the retirement of the `<sign-off>` prefix.
Confirm before writing it that 045 is still free: `tests/test_decision_records.py`
refuses a number already on the default branch, and `main` moves during a run.
If it is taken, take the next free number and change the filename and first
heading together, since that test also requires the heading to state the number
its filename claims.

`docs/disposable-fixture-signing/measurement.md` records both measurements with
the host and its `commit.gpgsign`, `gpg.format` and `user.signingkey` beside the
numbers.

**Tests.** No new test module and no changed test file. The measurement is the
step's own work, recorded rather than asserted.

M1, the construction path, is where acceptance item 4's claim lives. Three
samples per arm, twenty commits each, wall time divided by twenty:

```bash
for mode in signed unsigned; do for run in 1 2 3; do
  R=$(mktemp -d); cd "$R"; git init -q
  git config user.name T; git config user.email t@example.invalid
  [ "$mode" = unsigned ] && git config --local commit.gpgsign false
  S=$(/Users/kethcode/.local/bin/python3.14 -c 'import time;print(time.time())')
  for i in $(seq 1 20); do echo "$i" > f.txt; git add f.txt; git commit -q -m "c$i"; done
  E=$(/Users/kethcode/.local/bin/python3.14 -c 'import time;print(time.time())')
  /Users/kethcode/.local/bin/python3.14 -c "print(f'$mode run$run: {($E-$S)*1000/20:.1f} ms/commit')"
done; done
```

The study's section 10 recorded this at the base ref: 25.6, 25.5 and 25.5
ms/commit signed against 20.3, 20.5 and 20.1 unsigned, spread at most 0.4 ms and
improvement 5.2 ms. The step re-runs it at the run head and records what it
gets. The improvement must exceed the spread; if it does not, that is the
recorded result and item 4 is reported as unmet rather than rounded into shape.

M2, suite wall time, is three samples of each of the four suite commands before
and after, under the contributor's real configuration. A delta inside variance
is recorded as inside variance. No suite-level speedup is claimed on this host
and item 4 is not satisfied from M2.

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-5.json
```

**Disciplines.** phylax: none, the step opens no boundary the earlier steps did
not already open, and the hostile signer it writes is the one step 2 specified
and controlled. ephoros: none, the step emits no new signal; it records the exit
codes and sentinel contents that step 2 defined as the observable surface.
metron: this step is the measurement, and both M1 and M2 exist because
acceptance item 4 requires a recorded before and after with its spread. elenchus:
the demo path is the acceptance proof for items 1 and 5, and it is a command and
an empty file rather than a verdict; the guard itself is unchanged. hypomnema:
ADR-045 is the expensive-to-reverse decision this delivery produces, because the
scope rule governs every future test that creates a repository and getting it
wrong in either direction is costly.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: The two documents are committed
under `docs/disposable-fixture-signing/` byte-identical to the receipted
artefacts, and `tests/run_tests.py` writes a valid report. All of the following
exit 0:

```bash
cmp .hexaemeron/study.md docs/disposable-fixture-signing/study.md
cmp .hexaemeron/runbook.md docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/disposable-fixture-signing/study.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/disposable-fixture-signing/study.md docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/disposable-fixture-signing/study.md
/Users/kethcode/.local/bin/python3.14 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/disposable-fixture-signing/runbook.md
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-1.json
/Users/kethcode/.local/bin/python3.14 -c "import json,pathlib;d=json.loads(pathlib.Path('.elenchus/fiat-621-step-1.json').read_text());assert d['schema']=='elenchus.unittest.v1' and d['complete'] is True and d['failures']==0 and d['errors']==0, d"
/Users/kethcode/.local/bin/python3.14 plugins/horos/skills/horos/scripts/horos.py check .
```

Every relative link in both committed documents resolves from
`docs/disposable-fixture-signing/`, which the hypomnema command above proves:
`H001` fires on a relative link that resolves to nothing.

Complete replacement Files: Created:
`docs/disposable-fixture-signing/study.md`,
`docs/disposable-fixture-signing/runbook.md`, `tests/__init__.py`,
`tests/run_tests.py`, `tests/test_root_elenchus_runner.py`. Changed:
`.horos/boundary.json` only if the horos check above reports drift.

`tests/__init__.py` makes the root suite a package. It is required by this
step's own mandated divergence rather than chosen: `TestLoader.discover`
refuses a start directory that is not importable whenever `start_dir` differs
from `top_level_dir`, so passing the repository root is unreachable without it.
Every plugin suite in this repository that passes a top-level directory already
carries one. It is also load-bearing: `tests/test_marketplace_prose.py` imports
`repo_contract` and `tests/test_run_observation_inoculation.py` imports
`tests.test_run_observation`, and today both resolve only because another test
module inserts the repository root as an import side effect and happens to sort
before them.

`tests/run_tests.py` is a faithful port of `plugins/hexaemeron/tests/run_tests.py`,
which is 241 lines and roughly 20 of them are path containment. Port that
containment rather than reimplementing it: reject a path containing `..`; refuse
a target that is already a symlink or already exists; resolve against the
worktree root and require `relative_to` to succeed; walk each parent component
with `lstat` and refuse a non-directory; probe for `os.O_DIRECTORY`,
`os.O_NOFOLLOW` and `dir_fd` support and refuse without them; open the root with
`O_RDONLY | O_DIRECTORY | O_NOFOLLOW` and compare `st_dev` and `st_ino` against
the pre-open stat to catch a worktree replaced during inspection; create report
directories through `dir_fd` at mode `0o700` without following a symlink; and
remove a failed write only while the target is still the inode that was created.
The payload is the same `elenchus.unittest.v1` object with `schema`, `complete`,
`testsRun`, `failures`, `errors`, `skipped`, `expectedFailures` and
`unexpectedSuccesses`. The three intended divergences are the discovery root,
which is `tests` rather than the Hexaemeron test directory; the top-level
directory passed to `unittest`; and the module docstring, which names the
repository suite rather than the controller suite because the parser prints it
under `--help` and the reference wording would be false at the repository root.
Any other divergence is a defect.

**Why.** Two receipted criteria could not be met as written, and neither
failure is in the delivery. The `brevitas` invocation named two documents in one
call, but that checker declares a single optional positional draft, so the call
exits 2 against any two paths, including the receipted originals; it is replaced
by one invocation per document, each of which exits 0. The `Files` list named
four created paths and forbade any divergence beyond two, but the step's own
requirement to pass a top-level directory forces both a fifth file and a third
divergence, so the field is restated to carry what the requirement actually
implies. No exit criterion is weakened: every command still has to exit 0, and
the two brevitas runs check the same bytes the single run intended to.

**Steps touched.** Step 1's exit and files.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: The guard is committed and green,
and its negative control proves the hostile configuration is genuinely hostile
and genuinely reached. All of the following exit 0:

```bash
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-2.json
/Users/kethcode/.local/bin/python3.14 -m unittest tests.test_disposable_fixture_signing -v
/Users/kethcode/.local/bin/python3.14 -m unittest tests.test_disposable_fixture_signing.NegativeControl -v
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
```

The committed generator produces a usable harness. All of these exit 0:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

```bash
test -s "$HOSTILE_DIR/hostile.gitconfig"
test -x "$HOSTILE_DIR/hostile-signer"
test ! -s "$HOSTILE_DIR/sentinel.log"
```

The fourth command above is the non-vacuity proof. `NegativeControl` builds a
disposable repository that declares no local signing policy, and asserts both
that its commit failed and that the sentinel recorded an invocation. It can
only pass when the hostile configuration was genuinely hostile and genuinely
reached, so its exit 0 is the evidence. Also required, and recorded in the
step's prose rather than as a command because it mutates the tree: neutering
the harness must make `NegativeControl` fail, and removing the local
declaration from the fixture builder must make the positive case fail. Both
mutations are reverted byte-identical before the step commits.

Complete replacement Files: Created:
`tests/test_disposable_fixture_signing.py` and
`tests/hostile_signing_harness.py`. Changed:
`docs/disposable-fixture-signing/runbook.md`, refreshed so the shipped copy
stays byte-identical to the receipted artefact after this amendment. No fixture
under test is changed in this step; the guard exercises repositories it
constructs itself, so both ends are green.

`tests/hostile_signing_harness.py` holds the harness the guard uses in-process
and a `--emit <dir>` entry point that writes `hostile.gitconfig` and the
executable `hostile-signer` into the named directory and truncates
`sentinel.log` beside them. The three filenames are fixed so a caller can name
them without parsing output. The guard imports the module rather than
duplicating the recipe, so the configuration every later step runs is the same
one the guard proves hostile. The emitted signer resolves its sentinel from its
own directory rather than from an environment variable, so a hostile directory
nested inside another records into its own file and the guard's deliberate
invocations cannot contaminate an outer sentinel that a later step asserts on.

**Why.** The replaced exit contained a refusal check that could not fail. It
ran the negative control, and on success chained through `&&` to an explicit
non-zero exit, while on failure `unittest` itself exited non-zero; both
outcomes therefore satisfied "exits non-zero", so the command proved nothing
about vacuity while appearing to. It was measured exiting 1 against a guard
that is demonstrably not vacuous. The replacement asserts the property
directly, since the negative control's own assertions are exactly the
non-vacuity claim. The files field gains the refreshed shipped copy, which this
amendment itself makes necessary.

**Steps touched.** Step 2's exit and files.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: No new test module.
`tests/test_disposable_fixture_signing.py` gains one enumeration entry per
suite, each naming a representative test that commits fixture history: for the
root suite a `GuardMutationTests` method, for Horos a `UniverseTests` method.
The representative must be one that commits, never one that verifies a
signature, because the enumeration's contract is exit 0 with an empty sentinel
and a verifying test reaches the hostile signer through `git verify-commit`
however correctly its fixtures declare the rule. Both existing suites keep their
counts; the root suite and the Horos suite must report the same number of tests
as at step 2's exit, plus whatever the enumeration itself adds.

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-3.json
```

Expected exact Elenchus result: `passed`. This delivery changes test files only,
and the classifier copies a commit's changed test files onto its parent before
running the declared command, so the fix travels with the guard and the parent
cannot fail. Record that value; it is not a finding. `unguarded` is not the
mechanical answer here and must not be recorded as one: the classifier reserves
it for a commit that changed no test files at all, which was measured against
`plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:281` during step 2's
audit. The acceptance evidence for this step is the pair of
hostile-configuration commands in the exit above, not an Elenchus verdict.

**Why.** The replaced field predicted `unguarded` on reasoning that was right
about the mechanism and wrong about the label. Step 2's audit ran the classifier
twice against exactly this shape of change and got `passed` both times, and
found the branch that returns `unguarded` is reached only when a commit changes
no test files. A step that instructs its auditor to record a value the tool does
not produce invites either a false record or a wasted investigation. The
representative-selection sentence is added because step 2's third round measured
a verifying suite reaching the signer through `git verify-commit`, which the
enumeration's contract cannot distinguish from a fixture signing itself.

**Steps touched.** Step 3's tests.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit
holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Goal: Apply the rule to the six
construction sites in the root and Horos suites, and extend the guard's
enumeration to both.

Complete replacement Files: Changed: `tests/test_boundary_currency.py` (the
`GuardMutationTests` setup at line 166), `plugins/horos/tests/test_scoped_entry.py`
(line 64), `plugins/horos/tests/test_demonstration.py` (line 53),
`plugins/horos/tests/test_universe.py` (lines 56, 134 and 195),
`tests/test_disposable_fixture_signing.py` (enumeration entries for both
suites), and `docs/disposable-fixture-signing/runbook.md`, refreshed so the
shipped copy stays byte-identical to the receipted artefact after the
amendments this run has recorded since step 2.

Each edit is one call, `git config --local commit.gpgsign false`, against the
fixture repository, placed immediately after the `git init` that created it and
before any other configuration. The three Horos modules each carry their own
byte-identical `git(root, *args)` helper; the line goes at each call site, not
into a shared module, per the study's section 3 non-goal. One comment per suite,
not per site, says why the line is there: fixture history is not signing
evidence, so inherited signing must not decide whether the repository can be
built. Suite means the discovery unit the exit commands name, so the root suite
takes one comment and the Horos suite takes one, placed at the first of its
three sites. Do not touch `tests/test_boundary_currency.py:140` or
`plugins/horos/tests/test_scoped_entry.py:140`; neither commits, and the study's
section 2b records them as out of scope. Do not declare at
`plugins/horos/tests/test_universe.py:247` either: it is a `worktree add` from
the repository line 56 creates, and step 2's audit measured that a linked
worktree inherits the declaration its source repository carries.

**Why.** The goal said five sites where its own files list names six and the
study's section 2b table records six; `test_universe.py` carries three. The
count was the only thing wrong, and no exit criterion moved, but a shipped
runbook that miscounts its own work is a defect in the document. The files list
gains the shipped runbook copy because three amendments have been recorded since
step 2 committed it, so the copy in `docs/` no longer matches the receipted
artefact and this is the step that brings it current. The two clarifying
sentences record what step 2's audit measured, so a later reader does not add a
seventh declaration to a worktree that does not need one.

**Steps touched.** Step 3's goal and files.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit
holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Files: Changed:
`tests/test_boundary_currency.py` (the `GuardMutationTests` setup at line 166),
`plugins/horos/tests/test_scoped_entry.py` (line 64),
`plugins/horos/tests/test_demonstration.py` (line 53),
`plugins/horos/tests/test_universe.py` (lines 56, 134 and 195),
`tests/test_disposable_fixture_signing.py` (enumeration entries for both
suites), and `docs/disposable-fixture-signing/runbook.md` and
`docs/disposable-fixture-signing/study.md`, refreshed so the shipped copies stay
byte-identical to the receipted artefacts after the amendments this run has
recorded since step 2.

Each edit is one call, `git config --local commit.gpgsign false`, against the
fixture repository, placed immediately after the `git init` that created it and
before any other configuration. The three Horos modules each carry their own
byte-identical `git(root, *args)` helper; the line goes at each call site, not
into a shared module, per the study's section 3 non-goal.

One comment per suite, not per site, says why the line is there: fixture history
is not signing evidence, so inherited signing must not decide whether the
repository can be built. Suite means the discovery unit the exit commands name,
so the root suite takes one comment and the Horos suite takes one. The Horos
comment sits in `plugins/horos/tests/test_universe.py`, the module carrying
three of that suite's five sites; `test_scoped_entry.py` and
`test_demonstration.py` carry a bare declaration, and a reader who meets one
reaches the reason through `git blame` on the line or through the opening
docstring of `tests/test_disposable_fixture_signing.py`, which states the rule
and its reason in full.

Do not touch `tests/test_boundary_currency.py:140` or
`plugins/horos/tests/test_scoped_entry.py:140`; neither commits, and the study's
section 2b records them as out of scope. Do not declare at
`plugins/horos/tests/test_universe.py:247` either: it is a `worktree add` inside
`CandidateBindingTests`, which spans lines 180 to 259, so the repository it
shares a config file with is the one site 10 creates at `:195`, and step 2's
audit measured that a linked worktree inherits the declaration its source
repository carries.

**Why.** The fourth amendment said the worktree at `:247` shares the repository
created at line 56. It does not: `UniverseTests` ends at line 120 and `:247`
sits in `CandidateBindingTests`, whose own construction is site 10 at `:195`.
That amendment inherited the error from the study's section 2 coverage note,
which has now been corrected by its own amendment; the built tree was always
right. The same amendment placed the Horos comment at "the first of its three
sites", which is unsatisfiable as written: the Horos suite has five sites across
three modules, and the comment sits in the module holding three of them, which
is the last of the three in discovery order. The files list gains the shipped
study copy for the same reason it already carried the runbook copy.

**Steps touched.** Step 3's files.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit
holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Goal: Apply the rule to the remaining
four construction sites, harden the two that already declare it, and extend the
guard's enumeration to both suites.

Complete replacement Tests: No new test module.
`tests/test_disposable_fixture_signing.py` gains one enumeration entry per
suite. Each representative must be a test that commits fixture history, never
one that verifies a signature. Step 2's third audit round measured
`plugins/hexaemeron/tests/test_issue_429_recovery.py` reaching the hostile
signer through `git verify-commit`, which the enumeration's contract of exit 0
with an empty sentinel cannot distinguish from a fixture signing itself, so a
verifying representative can never pass however correctly its fixtures declare
the rule. Confirm the chosen representative records a signing invocation rather
than a verifying one when its declaration is removed.

The signature-verification legs must be shown untouched: the Hexaemeron suite
reports the same test count as at step 3's exit plus nothing, and `git diff`
over `plugins/hexaemeron/tests/test_issue_429_recovery.py` is empty.

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-4.json
```

Expected exact Elenchus result: `passed`, for the reason step 3's amended tests
field gives. The classifier copies a commit's changed test files onto its parent
before running the declared command, so a test-only change carries its own fix
and the parent cannot fail. `unguarded` is not the mechanical answer for this
step's code change and must not be recorded as one: the classifier reserves it
for a commit that changed no test files at all, measured against
`plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:281`.

**Why.** The goal said five remaining sites. The study's section 2b table
records ten in total and step 3 declared six of them, leaving four: sites 2, 3,
4 and 5. The other two paths this step touches, at
`plugins/hexaemeron/tests/test_hexctl.py:55` and
`plugins/hexaemeron/tests/test_fiat_skill.py:1458`, already declare the rule and
are hardened for uniformity rather than repaired, which the files field already
says; counting them as remaining sites conflates repair with tidying. The tests
field predicted `unguarded` by pointing at step 3, whose own prediction has
since been corrected to `passed` by amendment, so the pointer now resolves to
the opposite of what it was written to mean. The representative-selection rule
is added because this is the step whose suites contain the verifying tests step
2's audit measured.

**Steps touched.** Step 4's goal and tests.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit
holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: Both remaining suites pass, and no
fixture construction in either reaches the signer. All of the following exit 0:

```bash
npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py'
/Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-4.json
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
```

And, under a hostile configuration this step generates for itself:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

```bash
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py' \
  > "$HOSTILE_DIR/hexaemeron.log" 2>&1 || true
grep -q 'Issue429RecoveryTests.test_composition_has_exact_parent_order_and_signed_header' "$HOSTILE_DIR/hexaemeron.log"
grep -qE 'FAILED \(errors=1' "$HOSTILE_DIR/hexaemeron.log"
grep -q -- '--verify' "$HOSTILE_SENTINEL"
! grep -q -- '-bsau' "$HOSTILE_SENTINEL"
```

The Hermes suite still exits 0 with nothing of its own in the sentinel. The
Hexaemeron suite does not, and cannot: `plugins/hexaemeron/tests/test_issue_429_recovery.py:154`
runs `git verify-commit` against this repository's own history, and the commit it
names carries a real signature header, so git consults the hostile
`gpg.program` to verify it and that program refuses by design. The remaining four
assertions state what the rule actually claims. The one error is exactly that
test and no other; the sentinel records a verification; and it records no
`-bsau`, which is the argument form git uses when it asks a program to *sign*.
No fixture construction in either suite reaches the signer.

**Why.** The replaced exit required the hostile Hexaemeron run to exit 0 with an
empty sentinel. Neither is reachable while the suite contains a
signature-verification test, and this step is forbidden to touch that file
because the study excludes signature-subject tests from the rule by design. The
criterion therefore demanded that an excluded test satisfy the rule it is
excluded from. Step 2's third audit round measured this exact behaviour and
recorded it as a lead for step 4; it arrived as predicted. Emptiness was the
wrong proxy: it conflates a fixture asking the signer to sign with a
verification test asking it to verify, and only the first is the defect under
repair. The replacement distinguishes them by argument form, which is the
distinction the rule has always rested on. No criterion is weakened: every
fixture site in both suites must still construct and commit without reaching the
signer, and that is now asserted directly rather than inferred from an empty
file.

**Steps touched.** Step 4's exit.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit
holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Files: Changed:
`plugins/hexaemeron/tests/test_elenchus_checker.py` (the `Fixture` constructor at
line 114), `plugins/hexaemeron/tests/test_kronos_scoreboard.py` (lines 664 and
759), `plugins/hermes/skills/hermes/scripts/test_hermes.py` (line 173),
`plugins/hexaemeron/tests/test_hexctl.py` and
`plugins/hexaemeron/tests/test_fiat_skill.py` for the scope hardening only, and
`tests/test_disposable_fixture_signing.py` (enumeration entries for both
suites).

Regenerated, not hand-edited:
`.agents/skills/promise-machine/runtime/plugins/hermes/skills/hermes/scripts/test_hermes.py`
and `.agents/skills/promise-machine/runtime/MANIFEST.json`, because the portable
runtime mirrors the Hermes test module and `tests/test_skills_sh_package.py`
fails until `scripts/portable_promise_machine.py sync` restores the mirror; and
`.horos/boundary.json` and `.horos/candidates.json`, because those mirrored
bytes drift the boundary and `tests/test_boundary_currency.py` fails until
`plugins/horos/skills/horos/scripts/horos.py scan . --write` restores it. Stage
before scanning, because the scan walks tracked files, and run it last, because
anything written afterwards invalidates it. The candidates file also gains the
two `audit/rounds/fiat-621-*` entries the earlier steps added.

The Kronos site at line 759 is a `git clone`, not a `git init`; the declaration
goes immediately after the clone, because the rule is stated at creation
whichever verb created the repository, and step 2's audit measured that a clone
inherits no local configuration from the repository it was cloned from. The
hardening at `plugins/hexaemeron/tests/test_hexctl.py:55` and
`plugins/hexaemeron/tests/test_fiat_skill.py:1458` adds the explicit `--local`
scope and moves the call to immediately after `init`; both are already correct
and neither is a defect, so this is uniformity, not repair. Do not change
`plugins/hexaemeron/tests/test_hexctl.py:1366` or `:1388`: both re-initialise
the repository `make_origin_checkout` already configured, and a re-init
preserves local config. Do not change
`plugins/hexaemeron/tests/test_issue_429_recovery.py` or the signature classes
of `plugins/hexaemeron/tests/test_hexctl.py`; the study's section 2b lists them
as excluded because signing is their subject.

**Why.** The files list named the six paths the step edits by hand and omitted
the four it must regenerate. Those four are not optional and not incidental: the
portable runtime mirrors one of the edited modules, the Horos boundary is
computed over the tracked tree, and a suite guards each, so a step that changed
the six and stopped would leave the repository red. Naming them, with the order
the regeneration has to run in, is what stops the next reader treating a
generated diff as an unexplained edit.

**Steps touched.** Step 4's files.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit
holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: Both remaining suites pass, and no
fixture construction in either reaches the signer. All of the following exit 0:

```bash
npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py'
/Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-4.json
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
```

And, under a hostile configuration this step generates for itself:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

```bash
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py' \
  > "$HOSTILE_DIR/hexaemeron.log" 2>&1 || true
grep -q 'Issue429RecoveryTests.test_composition_has_exact_parent_order_and_signed_header' "$HOSTILE_DIR/hexaemeron.log"
grep -qE 'FAILED \(errors=1\)' "$HOSTILE_DIR/hexaemeron.log"
grep -q -- '--verify' "$HOSTILE_SENTINEL"
! grep -q -- '-bsau' "$HOSTILE_SENTINEL"
```

The Hermes suite exits 0 with nothing of its own in the sentinel. The Hexaemeron
suite does not, and cannot: `plugins/hexaemeron/tests/test_issue_429_recovery.py:154`
runs `git verify-commit` against this repository's own history, and the commit it
names carries a real signature header, so git consults the hostile `gpg.program`
to verify it and that program refuses by design. The four assertions state what
the rule actually claims: the one error is exactly that test and no other, the
sentinel records a verification, and it records no `-bsau`, which is the argument
form git uses under this harness's openpgp arm when it asks a program to sign.

Two bounds on that last assertion, stated so nobody reads it as wider than it is.
`-bsau` discriminates signing from verification under the openpgp arm, which is
the arm `--emit` writes and the only one these commands run; every signing form
measured under it, including `git tag -s`, `git merge -S`, and a commit with an
empty signing key, carries `-bsau`, and verification never does. It is not the
discriminator under the ssh arm, where signing appears as `-Y sign`; that arm is
not reachable from these commands, and the emptiness criterion this replaces had
the identical bound.

Complete replacement Tests: No new test module.
`tests/test_disposable_fixture_signing.py` gains one enumeration entry per suite.
Each representative must be a test that commits fixture history, never one that
verifies a signature. Step 2's third audit round measured
`plugins/hexaemeron/tests/test_issue_429_recovery.py` reaching the hostile signer
through `git verify-commit`, which the enumeration's contract of exit 0 with an
empty sentinel cannot distinguish from a fixture signing itself, so a verifying
representative can never pass however correctly its fixtures declare the rule.
Confirm the chosen representative records a signing invocation rather than a
verifying one when its declaration is removed.

The signature-verification legs must be shown untouched: the Hexaemeron suite
reports the same test count as at step 3's exit plus nothing, and `git diff` over
`plugins/hexaemeron/tests/test_issue_429_recovery.py` is empty.

```text
test command: /Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-621-step-4.json
```

Expected exact Elenchus result: `guarded`. This step is not a test-only change.
Its files field requires four regenerated artefacts alongside the six hand
edits, and the classifier copies only a commit's changed *test* files onto the
parent, so `MANIFEST.json` and the two `.horos` files stay at their parent
state and the currency guards that watch them fail there: the committed-boundary
check and three `SkillsShPackageTests` cases. That is a real red-to-green guard,
which is what `guarded` names. It is not the signing guard, and the record should
say so rather than implying the fixture rule was proved by it.

**Why.** Two defects in the amendments this step already carries, both mine, both
found by its first audit round.

The error-count assertion was written `FAILED \(errors=1` with no closing paren,
so it accepts `errors=1`, `errors=10`, `errors=13` and `errors=100`. That band is
reachable rather than theoretical: dropping both kronos declarations makes that
module alone report fifteen errors with fifteen signing invocations, which the
pattern would have accepted. The fourth assertion still catches the signing
claim, so nothing false could have been recorded about the rule, but the "and no
other error" half was not being checked. The closing paren restores it.

The expected verdict said `passed` on the reasoning that a test-only change
carries its own fix. That reasoning was sound and its premise was not: the eighth
amendment had already established this step regenerates four non-test artefacts,
which is precisely what makes the classifier's copy incomplete and the parent
fail. The measured value is `guarded`, and it is the better outcome — but a
prediction that contradicts its own step's files field should never have been
written.

**Steps touched.** Step 4's exit and tests.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit
holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: Both remaining suites pass, and no
fixture construction in either reaches the signer. All of the following exit 0:

```bash
npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py'
/Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
/Users/kethcode/.local/bin/python3.14 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.14 tests/run_tests.py --elenchus-report .elenchus/fiat-621-step-4.json
/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
```

And, under a hostile configuration this step generates for itself:

```bash
HOSTILE_DIR="$(mktemp -d)"
/Users/kethcode/.local/bin/python3.14 tests/hostile_signing_harness.py --emit "$HOSTILE_DIR"
export HOSTILE_SENTINEL="$HOSTILE_DIR/sentinel.log"
```

```bash
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  /Users/kethcode/.local/bin/python3.14 plugins/hermes/skills/hermes/scripts/test_hermes.py
GIT_CONFIG_GLOBAL="$HOSTILE_DIR/hostile.gitconfig" GIT_CONFIG_SYSTEM=/dev/null \
  npx --yes --package=node@26.6.0 --call '/Users/kethcode/.local/bin/python3.14 plugins/hexaemeron/tests/run_tests.py' \
  > "$HOSTILE_DIR/hexaemeron.log" 2>&1 || true
grep -q 'Issue429RecoveryTests.test_composition_has_exact_parent_order_and_signed_header' "$HOSTILE_DIR/hexaemeron.log"
grep -qE 'FAILED \(errors=1[,)]' "$HOSTILE_DIR/hexaemeron.log"
grep -q -- '--verify' "$HOSTILE_SENTINEL"
! grep -q -- '-bsau' "$HOSTILE_SENTINEL"
```

The Hermes suite exits 0 with nothing of its own in the sentinel. The Hexaemeron
suite does not, and cannot: `plugins/hexaemeron/tests/test_issue_429_recovery.py:154`
runs `git verify-commit` against this repository's own history, and the commit it
names carries a real signature header, so git consults the hostile `gpg.program`
to verify it and that program refuses by design. The four assertions state what
the rule actually claims: the one error is exactly that test and no other, the
sentinel records a verification, and it records no `-bsau`, which is the argument
form git uses under this harness's openpgp arm when it asks a program to sign.

The error-count pattern ends `[,)]` rather than `\)` because the suite carries
one skip, so unittest prints `FAILED (errors=1, skipped=1)` and the closing paren
does not follow the digit. The character class anchors the digit boundary, which
is the whole point: it matches that line and the skip-free `FAILED (errors=1)`,
and rejects `errors=10`, `errors=13` and `errors=100`.

Two bounds on the `-bsau` assertion, stated so nobody reads it as wider than it
is. It discriminates signing from verification under the openpgp arm, which is
the arm `--emit` writes and the only one these commands run; every signing form
measured under it, including `git tag -s`, `git merge -S`, and a commit with an
empty signing key, carries `-bsau`, and verification never does. It is not the
discriminator under the ssh arm, where signing appears as `-Y sign`; that arm is
not reachable from these commands, and the emptiness criterion this replaces had
the identical bound.

Complete replacement Files: Changed:
`plugins/hexaemeron/tests/test_elenchus_checker.py` (the `Fixture` constructor at
line 114), `plugins/hexaemeron/tests/test_kronos_scoreboard.py` (lines 664 and
759), `plugins/hermes/skills/hermes/scripts/test_hermes.py` (line 173),
`plugins/hexaemeron/tests/test_hexctl.py` and
`plugins/hexaemeron/tests/test_fiat_skill.py` for the scope hardening only, and
`tests/test_disposable_fixture_signing.py` (enumeration entries for both
suites).

Refreshed: `docs/disposable-fixture-signing/runbook.md` and
`docs/disposable-fixture-signing/study.md`, so the shipped copies stay
byte-identical to the receipted artefacts. This step records several amendments
of its own, and each one moves the canonical runbook, so the refresh is the last
thing the step does rather than something it can do once and forget.

Regenerated, not hand-edited:
`.agents/skills/promise-machine/runtime/plugins/hermes/skills/hermes/scripts/test_hermes.py`
and `.agents/skills/promise-machine/runtime/MANIFEST.json`, because the portable
runtime mirrors the Hermes test module and `tests/test_skills_sh_package.py`
fails until `scripts/portable_promise_machine.py sync` restores the mirror; and
`.horos/boundary.json` and `.horos/candidates.json`, because those mirrored bytes
drift the boundary and `tests/test_boundary_currency.py` fails until
`plugins/horos/skills/horos/scripts/horos.py scan . --write` restores it. Stage
before scanning, because the scan walks tracked files, and run it last, because
anything written afterwards invalidates it.

The Kronos site at line 759 is a `git clone`, not a `git init`; the declaration
goes immediately after the clone, because the rule is stated at creation whichever
verb created the repository, and step 2's audit measured that a clone inherits no
local configuration from the repository it was cloned from. The hardening at
`plugins/hexaemeron/tests/test_hexctl.py:55` and
`plugins/hexaemeron/tests/test_fiat_skill.py:1458` adds the explicit `--local`
scope and moves the call to immediately after `init`; both are already correct and
neither is a defect, so this is uniformity, not repair. Do not change
`plugins/hexaemeron/tests/test_hexctl.py:1366` or `:1388`: both re-initialise the
repository `make_origin_checkout` already configured, and a re-init preserves
local config. Do not change
`plugins/hexaemeron/tests/test_issue_429_recovery.py` or the signature classes of
`plugins/hexaemeron/tests/test_hexctl.py`; the study's section 2b lists them as
excluded because signing is their subject.

**Why.** My correction to the error-count pattern overcorrected. Demanding
`errors=1\)` requires the closing paren to follow the digit, which it does not:
the suite carries one skip, so the real line reads `FAILED (errors=1, skipped=1)`
and the assertion failed on a correct tree, making the exit unsatisfiable. The
character class fixes the digit boundary without demanding the paren, and was
measured against the real line and against `errors=10`, `errors=13` and
`errors=100` before being written here. That is three revisions of one assertion,
which is worth recording plainly: the first was too loose, the second too strict,
and only the third was checked against the string it has to match before it was
committed to the spec.

The files field gains the two shipped copies. Step 3's amendment named them and
step 4's did not, and the consequence was exactly what that inconsistency
predicts: the shipped runbook fell 9288 bytes behind, step 1's byte-identity
criterion stopped passing, and the audit had to refresh it twice in one round.

**Steps touched.** Step 4's exit and files.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit
holds.
