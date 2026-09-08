# Runbook: packaged payload byte-cap margin

Issue [#1467](https://github.com/wildcat-finance/skills/issues/1467),
`framework-109`. Derived from `.hexaemeron/study.md`. Run branch
`fiat/1467-packaged-payload-byte-cap-margin`, cut from `main` at
`12cbe2e6ed95decd6d9d355740f2dbd052956abe`.

Three steps. Step 1 commits the specification, step 2 makes the generator
change the study selected, step 3 installs the guard that holds the margin and
runs the demo path. The omission and the reference repair land in one step
because splitting them leaves 27 dangling references at a step boundary, which
the operator decision recorded in the study's section 3 refuses.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 53718d5865f6f7b4afd5a462fef2e9b387b25780f4f33e52710f855c19dc3fbb
candidate | omission-class-with-reference-repair
```

The study's demo path names the two resolvers at their controller paths under
`.hexaemeron/`, which is controller evidence and never committed. Step 1 commits
them to `docs/packaged-payload-byte-cap-margin/`, and steps 2 and 3 name that
committed location. The bytes are the same; only the path a reviewer types
differs.

## Step 1: Commit the specification and its draft decision record

**Goal.** Put the study, the design record, its 35 reports, the two resolvers
and the draft decision record in the tree, so every later step, auditor and
reviewer reads the same bytes.

**Entry.** `fiat/1467-packaged-payload-byte-cap-margin` at
`12cbe2e6ed95decd6d9d355740f2dbd052956abe`, working tree clean apart from the
untracked draft decision record the study phase wrote.

**Exit.** Every file below is committed, the draft decision record is the only
one of them that existed before this step, and
`python3 scripts/run_checks.py --full --format json --report tmp/checks/step-1.json`
exits 0. The census is current: `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
leaves `.horos/census.json` unchanged when run a second time.

**Files.**

- `docs/packaged-payload-byte-cap-margin/study.md`, the exact receipted bytes of `.hexaemeron/study.md`.
- `docs/packaged-payload-byte-cap-margin/runbook.md`, the exact receipted bytes of this file.
- `docs/packaged-payload-byte-cap-margin/design-evidence.json`, the exact receipted bytes, SHA-256 `53718d5865f6f7b4afd5a462fef2e9b387b25780f4f33e52710f855c19dc3fbb`.
- `docs/packaged-payload-byte-cap-margin/reports/*.json`, all 35.
- `docs/packaged-payload-byte-cap-margin/resolve_design.py` and `docs/packaged-payload-byte-cap-margin/measure_built_margin.py`.
- `docs/decisions/drafts/omit-decorative-assets-and-repair-their-packaged-references.md`, already written, committed here.
- `.horos/census.json`, whose byte counts move because tracked files are added.

**Tests.** No new test. The step is proved by the root suite, which owns the
`docs` and `root` scopes these paths select. Elenchus runner contract for any
fix admitted in this step's audit rounds: command
`python3 scripts/run_checks.py --full --format json --report {report}`, report
format `json`, report file `tmp/checks/step-1.json`.

**Disciplines.** phylax: two Python files enter the tree; both spawn the
generator with a fixed local argv and no shell, and the audit checks that
claim. ephoros: none, nothing in this step runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand. hypomnema: the draft
decision record lands here, and the study's `design-bridge` block names it as
the home of the selected design.

## Step 2: Omit the character portraits and repair their packaged references

**Goal.** Declare the ninth omission class, and in the packaged copy only,
replace every `<img>` tag whose target the package no longer carries.

**Entry.** Step 1's exit state.

**Exit.** All five hold, each by command:

1. `python3 scripts/portable_promise_machine.py package --out <dir>` writes a manifest whose `omissions` array carries the new class with its reason.
2. Exactly 32 paths leave the package against the base build, every one a character portrait: `python3 docs/packaged-payload-byte-cap-margin/resolve_design.py --candidate omission-class-with-reference-repair --criterion tracked-files-deleted` reports 0 and `git ls-files` reports the same 32 portrait paths tracked before and after.
3. `python3 docs/packaged-payload-byte-cap-margin/resolve_design.py --candidate omission-class-with-reference-repair --criterion dangling-image-references` reports 0.
4. `python3 docs/packaged-payload-byte-cap-margin/measure_built_margin.py --candidate omission-class-with-reference-repair` reports at least 5,242,880 bytes of headroom. This is the `built-payload-margin` conformance criterion, which blocks step 3.
5. `python3 scripts/run_checks.py --full --format json --report tmp/checks/step-2.json` exits 0.

**Files.**

- `scripts/portable_promise_machine.py`: a ninth entry in `OMISSIONS` covering `assets/characters/**` and `plugins/*/assets/characters/**`; the matching branch in `_omitted`; removal of `assets/characters/promise-machine.png` from `ROOT_FILES`; the reference repair inside `expected_files()`, which is the single place packaged bytes are produced; a `transform` field on each manifest row that carries one.
- `tests/test_skills_sh_package.py`: `EXPECTED_OMISSIONS` gains the new class and is still compared for equality, not containment; `test_manifest_binds_every_runtime_file_to_source_bytes` is restated so a row declaring a transform asserts that the transform applied to the source bytes yields the packaged bytes, rather than dropping the source binding; the packaged router `SKILL.md` equality at lines 205 to 210 is restated the same way; new cases for the omitted set being exactly the 32 portraits, for no `<img src=...>` in any of the 458 packaged Markdown documents resolving to an absent path, and for the rewritten-document count being exactly the expected one.
- `.horos/census.json`, refreshed.

**Tests.** Extended in `tests/test_skills_sh_package.py`. Six new or restated
assertions, listed under **Files**. Each transform case is built from a
constructed document rather than a real one, and compares the whole document
byte for byte, because a guard that counts replacements cannot see a transform
that ate the markup around one. Elenchus runner contract: command
`python3 scripts/run_checks.py --full --format json --report {report}`, report
format `json`, report file `tmp/checks/step-2.json`.

**Disciplines.** phylax: this step opens two boundaries the study's section 9
names, the generator altering a packaged document's bytes and the omission
predicate acting as a filter on published content, and the regex that parses an
HTML tag is the sharp edge in both directions. ephoros: the build emits the
rewritten-document count and each replacement's omitted target in normal output,
not only on failure, because the study's signal 3 asks which documents the build
rewrote. metron: none. The study's section 10 records that this repository's
build time cannot be measured to a useful precision on the hardware available,
and no speed claim is made; the byte budget is a correctness gate, checked in
exit 4. elenchus: none, no failure in hand at entry. hypomnema: none, the
decision record for this change landed in step 1 and this step adds no new
decision.

## Step 3: Hold the margin with a guard that fails before the cap

**Goal.** Move the byte assertion off the CLI's default onto a stated
repository threshold, so a delivery that closes the margin meets a red test with
the number in its failure text, and demonstrate the whole change.

**Entry.** Step 2's exit state, with `built-payload-margin` passed.

**Exit.** All four hold, each by command:

1. `python3 -m unittest tests.test_skills_sh_package -v` passes with the byte assertion held against a threshold below `MAX_BYTES`, and the guard's failure text prints the measured `total_bytes`, the threshold, and the remaining margin.
2. A test asserts the threshold's relationship to `MAX_BYTES` rather than only the current measurement, so raising the threshold to meet a grown payload trips the same guard the file cap's comment describes. It fails when that relationship is broken: prove it by breaking it in a scratch copy and recording the failure.
3. The demo path from the study's problem statement runs end to end: `python3 scripts/portable_promise_machine.py package --out <dir>`, then `python3 docs/packaged-payload-byte-cap-margin/measure_built_margin.py --candidate omission-class-with-reference-repair` reporting at least 5,242,880, then `python3 docs/packaged-payload-byte-cap-margin/resolve_design.py --candidate omission-class-with-reference-repair --criterion dangling-image-references` reporting 0, then the unittest module above.
4. `python3 scripts/run_checks.py --full --format json --report tmp/checks/step-3.json` exits 0.

**Files.**

- `tests/test_skills_sh_package.py`: the threshold constant with its stated derivation, the amended byte assertion and its failure text, the relationship guard, and an extension of the comment that has already reasoned four raises of the sibling constant in place.
- `docs/decisions/drafts/omit-decorative-assets-and-repair-their-packaged-references.md`: completed with the three decision sections the study's section 12 names, the 35.21 per cent measurement, the Horos classification, and the three cap facts from section 3. The number is allocated immediately before pushing, because this repository assigns decision-record numbers against the default branch at merge.
- `.horos/census.json`, refreshed.

**Tests.** Extended in `tests/test_skills_sh_package.py`: the amended byte
assertion, and the relationship guard, which is the test that fails without the
fix. Elenchus runner contract: command
`python3 scripts/run_checks.py --full --format json --report {report}`, report
format `json`, report file `tmp/checks/step-3.json`.

**Disciplines.** phylax: none, this step adds no boundary; it changes a
constant, an assertion and a document. ephoros: the guard's failure text is the
answer to the study's signal 1, so the measured bytes, the threshold and the
margin appear in CI output whether it passes or fails. metron: none, no
performance claim. elenchus: the relationship guard is the step's own guard rule
applied to itself, a test that fails without the change. hypomnema: the decision
record is completed here, carrying all three expensive decisions the study's
section 12 names, and the threshold value is recorded as the one thing in this
change that is cheap to reverse.

### Amendment -- 2026-09-08

**What changed.**

Complete replacement Files: `docs/packaged-payload-byte-cap-margin/study.md`, the receipted bytes of `.hexaemeron/study.md` with its five discipline links repointed from `../<name>/SKILL.md` to `../../plugins/hexaemeron/skills/<name>/SKILL.md` for ephoros, phylax, metron, elenchus and hypomnema; `docs/packaged-payload-byte-cap-margin/runbook.md`, the exact receipted bytes of this file; `docs/packaged-payload-byte-cap-margin/design-evidence.json`, the exact receipted bytes, SHA-256 `53718d5865f6f7b4afd5a462fef2e9b387b25780f4f33e52710f855c19dc3fbb`; `docs/packaged-payload-byte-cap-margin/reports/*.json`, all 35; `docs/packaged-payload-byte-cap-margin/resolve_design.py` and `docs/packaged-payload-byte-cap-margin/measure_built_margin.py`, each with a depth-independent repository root so both run from the committed location as well as the controller one; `docs/decisions/drafts/omit-decorative-assets-and-repair-their-packaged-references.md`, already written, committed here; `.horos/census.json` and `.horos/boundary.json`, both refreshed after staging, because this step adds 41 tracked files and each derives its universe from `git ls-files`.

Complete replacement Exit: Every file listed under Files is committed, the draft decision record is the only one of them that existed before this step, and `python3 scripts/run_checks.py --full --format json --report tmp/checks/step-1.json` reports every check green except the pre-existing `hexaemeron-suite` failure of `test_kronos_scoreboard.ScoreboardTest.test_no_governed_ledger_declares_anything_today`, which is already red at the run's base commit `12cbe2e6ed95decd6d9d355740f2dbd052956abe` before this step changes anything and is filed as https://github.com/wildcat-finance/skills/issues/1472. Both Horos artefacts are current: `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write` each leave their file unchanged when run a second time.

**Why.** Three causes, all found before the step changed anything. The receipted study's five discipline links resolve to nothing at every path the file occupies, including its controller path, and `lint-hypomnema` walks `docs` and returns five H001 findings against the committed copy; the repointed form is the convention every committed `docs/*/study.md` already uses. Both resolvers compute their repository root as the parent of their parent, which is correct only one level below the root, so the committed copies would find no generator and every step-2 and step-3 exit command that invokes them would fail. `.horos/boundary.json` counts files walked from `git ls-files` and this step adds 41 tracked files, so `tests/test_boundary_currency.py` reddens unless it is refreshed alongside the census. The named suite exception is a failure this run did not cause and cannot fix inside its own packet: kronos asserts that no governed ledger declares anything, and the anamnesis delivery merged as `12cbe2e6` made one declare.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-08

**What changed.**

Complete replacement Exit: All five hold, each by command. One, `python3 scripts/portable_promise_machine.py package --out <dir>` writes a manifest whose `omissions` array carries the new class with its reason. Two, exactly 32 paths leave the package against the base build, every one a character portrait: `python3 docs/packaged-payload-byte-cap-margin/resolve_design.py --candidate omission-class-with-reference-repair --criterion tracked-files-deleted` reports 0 and `git ls-files` reports the same 32 portrait paths tracked before and after. Three, `python3 docs/packaged-payload-byte-cap-margin/resolve_design.py --candidate omission-class-with-reference-repair --criterion dangling-image-references` reports 0. Four, `python3 docs/packaged-payload-byte-cap-margin/measure_built_margin.py --candidate omission-class-with-reference-repair` reports at least 5,242,880 bytes of headroom, which is the `built-payload-margin` conformance criterion blocking step 3. Five, `python3 scripts/run_checks.py --full --format json --report tmp/checks/step-2.json` reports every check green except the pre-existing `hexaemeron-suite` failure of `test_kronos_scoreboard.ScoreboardTest.test_no_governed_ledger_declares_anything_today`, red at the run's base commit `12cbe2e6ed95decd6d9d355740f2dbd052956abe` and filed as https://github.com/wildcat-finance/skills/issues/1472.

**Why.** The step's fifth exit demanded a clean root suite, and the run's base commit is already red on one test this run did not cause and cannot fix inside its own packet. Naming the exception keeps the exit checkable: any other failure still stops the step.

**Steps touched.** Step 2

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-08

**What changed.**

Complete replacement Exit: All four hold, each by command. One, `python3 -m unittest tests.test_skills_sh_package -v` passes with the byte assertion held against a threshold below `MAX_BYTES`, and the guard's failure text prints the measured `total_bytes`, the threshold, and the remaining margin. Two, a test asserts the threshold's relationship to `MAX_BYTES` rather than only the current measurement, so raising the threshold to meet a grown payload trips the same guard the file cap's comment describes; prove it fails when that relationship is broken by breaking it in a scratch copy and recording the failure. Three, the demo path from the study's problem statement runs end to end: `python3 scripts/portable_promise_machine.py package --out <dir>`, then `python3 docs/packaged-payload-byte-cap-margin/measure_built_margin.py --candidate omission-class-with-reference-repair` reporting at least 5,242,880, then `python3 docs/packaged-payload-byte-cap-margin/resolve_design.py --candidate omission-class-with-reference-repair --criterion dangling-image-references` reporting 0, then the unittest module above. Four, `python3 scripts/run_checks.py --full --format json --report tmp/checks/step-3.json` reports every check green except the pre-existing `hexaemeron-suite` failure of `test_kronos_scoreboard.ScoreboardTest.test_no_governed_ledger_declares_anything_today`, red at the run's base commit `12cbe2e6ed95decd6d9d355740f2dbd052956abe` and filed as https://github.com/wildcat-finance/skills/issues/1472.

**Why.** The step's fourth exit demanded a clean root suite, and the run's base commit is already red on one test this run did not cause and cannot fix inside its own packet. Naming the exception keeps the exit checkable: any other failure still stops the step.

**Steps touched.** Step 3

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
