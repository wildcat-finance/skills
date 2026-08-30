# Runbook: site the generated skills.sh payload

Derived from `.hexaemeron/study.md`. The study chose option A: the generated
payload stays in this tree, and the run records that decision with the measured
cost and the discovery constraint that rules out relocation.

One step. The topic is a single capability: answer #940's question in a record
and keep its cost observable. Nothing in it could ship or be verified
separately. Step 1 is therefore both the scaffold fixed point, carrying the
committed copies of the study and runbook, and the demonstration fixed point,
proving the problem statement's demo path by running the root suite.

## Step 1: record the payload siting decision and guard its cost

**Goal.** Answer issue #940 with a decision record that keeps the payload
in-tree on stated evidence, and add one guard so the payload cannot grow
unobserved.

**Entry.** The run branch `fiat/940-site-the-generated-skills-sh-payload` at its
tip, cut from `main` at `7e97b5195d5b0e43146b4200f26cd41b89003413`. The tree is
clean and `python3 -m unittest discover -s tests` exits 0.

**Exit.** Five deliverables:

1. `docs/decisions/ADR-054-keep-the-generated-skills-sh-payload-in-tree.md`,
   recording the decision, the four options costed, the measured per-clone cost,
   the discovery constraint, and the sync ordering #854 established. It names
   ADR-040 as the record it extends, and ADR-040 gains a forward reference to it.
2. One guard in `tests/test_skills_sh_package.py` asserting the payload's tracked
   file count and total byte size against the figures the record states, failing
   with both expected and actual values.
3. Committed copies of the study and runbook under `docs/`.
4. `.horos/boundary.json` regenerated so a fresh scan of the staged tree
   reproduces it.
5. `INSTALL.md` and `README.md` install instructions verified against the command
   the CLI accepts for this repository, and corrected only where they disagree.

Proved by `python3 -m unittest discover -s tests` exiting 0 from the step branch,
and by `python3 plugins/horos/skills/horos/scripts/horos.py check .` exiting 0.

**Files.** Created: `docs/decisions/ADR-054-keep-the-generated-skills-sh-payload-in-tree.md`,
`docs/skills-sh-payload-siting-study.md`, `docs/skills-sh-payload-siting-runbook.md`.
Changed: `tests/test_skills_sh_package.py`, `.horos/boundary.json`,
`docs/decisions/ADR-040-package-one-dependency-closed-portable-router.md`, and
`INSTALL.md` or `README.md` only if they misstate the install command.

**Tests.** One new test method in `tests/test_skills_sh_package.py` asserting the
payload's tracked file count and total byte size, taking the suite in that module
so that module holds nine. No existing test is relaxed or removed.

Runner contract for an audit fix: the exact command is
`python3 -m unittest discover -s tests -v > {report} 2>&1`, run from the
repository root with one `{report}` argument. The report format is stdlib
`unittest` verbose text, not JSON; this repository ships no
`unittest-json-v1` runner, so a verdict read from it is textual. The report file
is `.hexaemeron/step-1-report.txt`.

**Disciplines.** phylax: none, the step opens no boundary. It adds no
dependency, accepts no untrusted input, fetches no URL, reads no credential and
spawns no new subprocess. ephoros: none, nothing this step produces runs
unattended; the guard executes only inside the root suite, which already reports
through the required `invariants` check. metron: none, no performance claim is
made and no speed-motivated change is included. elenchus: applies, because a red
root suite or a boundary mismatch is worked to its cause under the runner
contract above rather than by relaxing an assertion. hypomnema: applies, because
whether the payload stays in this tree is expensive to reverse and its record's
home is `docs/decisions/`.

**Ordering note.** The Horos boundary is regenerated last, and only after
`git add`, because the scan walks the tracked universe and a scan run before
staging describes the previous tree. The root suite is never run from a git hook
in this repository.
