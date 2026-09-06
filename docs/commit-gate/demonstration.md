# Demonstration: the gate on a clone that had never seen it

One run, on 2026-09-05, of the demo path the study sets out in section 1: clone
the repository into a fresh directory, run the suite and read the refusal, run
the one activation command, record a green, commit, then edit a file and watch
the next commit be refused. Every command below was run; every exit code below
was read from the shell that ran it. Where this record could not establish
something, or where the transcript leaves out a command the run made, the last
section says so rather than leaving the reader to notice.

## The clone

The branch is unpushed, so the clone was made from the run worktree that holds
it rather than from a URL:

| | |
| --- | --- |
| Source | `/Users/c0rtexzer0/Projects/wildcat-skills/.claude/worktrees/secretsauce-scrape-prevention-50be04/tmp/fiat/fiat-857-framework-16-the-commit-gate-lives-in-one-cl` |
| Branch | `fiat/857-framework-16-the-commit-gate-lives-in-one-cl-step-5-demonstrate-the-gate-on-a-clone` |
| Commit | `1ac5332b06d827ffe5ffa1628dbe36f119d7b1e1` |
| Destination | `tmp/commit-gate-demo/fresh`, which did not exist beforehand and is ignored by the repository it sits under |
| Machine | Darwin 25.5.0 arm64; git 2.50.1 (Apple Git-155); the interpreter `.python-version` pins, 3.14.6 |

Two settings were changed in the clone before anything was timed, and neither
is part of the gate. `commit.gpgsign` was set to false, so the wall times below
are unsigned commits and do not include the signer. `core.hooksPath` was left
unset until row 5 of the transcript, which is the point of the first two rows.

## The transcript

| # | Command | Exit | What it showed |
| --- | --- | --- | --- |
| 1 | `git clone --branch fiat/857-framework-16-the-commit-gate-lives-in-one-cl-step-5-demonstrate-the-gate-on-a-clone --single-branch /Users/c0rtexzer0/Projects/wildcat-skills/.claude/worktrees/secretsauce-scrape-prevention-50be04/tmp/fiat/fiat-857-framework-16-the-commit-gate-lives-in-one-cl fresh` | 0 | 214 MB checked out at `1ac5332b`. See the last section on where this code came from. |
| 2 | `git config --get core.hooksPath` | 1 | Nothing configured. Git installed no hook on clone, which is the whole premise. |
| 3 | `python3 -m unittest discover -s tests` | 1 | 1181 cases in 210.065 s: one failure, two skips. The failure is `ActivationTests.test_this_checkout_has_the_gate_activated` and its message carries the activation command. |
| 4 | `python3 -m unittest tests.test_commit_gate -v` | 1 | 49 cases, the same single failure. This is the command the study's acceptance table names. |
| 5 | `git config core.hooksPath .githooks` | 0 | Run once, and not run again. Every later row in this table ran under it. |
| 6 | `git add -A` | 0 | Staged one edit, an appended comment line in `.githooks/README.md`. |
| 7 | `.githooks/greenlight` | 0 | 1181 cases in 146.233 s, no failures, two skips. Recorded tree `54f30131bff16d3f5513ed56de6b3e82b501c5ad` in `.git/LAST_GREEN`. |
| 8 | `git commit -m "Demonstration: commit the tree greenlight recorded"` | 0 | Commit `ddb54b3c`. The gate admitted it because the staged tree was the recorded one. 162.27 ms, the first execution of the hook file in this clone. |
| 9 | `git commit -m "Demonstration: an edit no suite has passed on"` | 1 | Refused. Between this row and row 8 a second line was appended and staged with `git add -A`, neither of them numbered here; that moved the staged tree to `4a914f3fba45cf3732e6a28830a0560e5e48c788` while the record still named `54f30131`. Gap 8 below. 46.39 ms. |
| 10 | `FIAT_SKIP_PRECOMMIT=1 git commit -m "Demonstration: an edit no suite has passed on"` | 0 | Commit `cf80bf05`, whose tree is `4a914f3f` -- the same commit row 9 refused, admitted by the token alone. 29.84 ms. |
| 11 | `python3 -m unittest tests.test_commit_gate.GreenTreeTests -v` | 0 | 5 cases. |
| 12 | `python3 -m unittest tests.test_commit_gate.HookIndexMutationTests -v` | 0 | 14 cases. |
| 13 | `python3 -m unittest tests.test_decision_records -v` | 0 | 5 cases, one skipped for want of a default-branch ref. |
| 14 | `git grep -c FIAT_SKIP_PRECOMMIT -- .githooks` | 0 | `.githooks/README.md:1` and `.githooks/pre-commit:3`. |
| 15 | `git write-tree` | 0 | Used between timing samples to record a green by hand. The measurement section says why. |
| 16 | `ls docs/decisions/ADR-074-*.md` | 1 | No such file, by the run's own decision. Acceptance condition 1 below. |

Row 3 failed with this, which is the sentence acceptance condition 2 is about.
Both quotations below carry the wording the run printed, wrapped to fit:

```
AssertionError: the commit gate is not activated in this checkout:
core.hooksPath is unset, so git runs no tracked hook and a commit of a tree no
suite has passed on is admitted silently. Turn it on with `git config
core.hooksPath .githooks`, run from the top of this working tree. pre-commit
and greenlight are tracked in .githooks/, README.md says what each one does,
and FIAT_SKIP_PRECOMMIT=1 admits a commit you mean to make without a recorded
green.
```

Row 9 refused with this:

```
pre-commit: refused, the green record names tree
54f30131bff16d3f5513ed56de6b3e82b501c5ad, not the staged tree
4a914f3fba45cf3732e6a28830a0560e5e48c788; run .githooks/greenlight on the
staged tree, or commit with FIAT_SKIP_PRECOMMIT=1
```

## The five acceptance conditions

### Acceptance condition 1, where the gate lives

Answered, and not in the form the study wrote down. The study asks for
`docs/decisions/ADR-074-*.md`; row 16 shows no such file, and that absence is
deliberate. The runbook records the reading: run #856 is open on the same base
and claims the same number, `tests/test_decision_records.py` sees a collision
only once the other number reaches the default branch, and so the record ships
unnumbered as
`docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`
and takes its number at merge. What the condition asks for beyond the filename
-- a record naming the chosen home and stating what each rejected option lost
-- is held by `DecisionRecordTests` in `tests/test_commit_gate.py`, which ran
green inside rows 4 and 7, and by row 13, the command the study names. Row 13
skipped its collision check; the last section says why.

### Acceptance condition 2, survives a clone and absence is visible

Answered by rows 1 through 5. A clone that had never been activated failed the
root suite at row 3 and the module at row 4, both at exit 1, and the failure
message quoted above carries `git config core.hooksPath .githooks` verbatim.
One run of that command at row 5 was the whole of the activation, and row 7
then found the same suite green: the failure was the gate reporting its own
absence, not a broken clone.

### Acceptance condition 3, green tree against untested tree

Answered by rows 7, 8 and 9. Greenlight recorded tree `54f30131` after the
suite passed; a commit staging that exact tree succeeded at row 8; and moving
the tree by one line to `4a914f3f` was refused at row 9, with the refusal
naming both trees rather than saying no. Row 11 is the fixture-level version of
the same pair.

### Acceptance condition 4, deliberate escape hatch

Answered by rows 9, 10 and 14. Row 10 is the commit row 9 refused, unchanged
and re-attempted with the token: it landed as `cf80bf05` carrying tree
`4a914f3f`, the tree no suite had passed on. Row 14 shows the literal token in
the tracked gate, once in the README and three times in the hook, so a reader
can find it by grep rather than by asking.

### Acceptance condition 5, index-mutation regression on the hook path

Answered by row 12: 14 cases green in the clone. They run the gate with
`GIT_INDEX_FILE` and `GIT_PREFIX` pointing at an outer repository and hold that
repository's staged state byte-identical. The condition asks for the guard to
live beside the path it guards rather than only in the file whose defect
prompted it, and in this clone it did: row 12 names `tests/test_commit_gate.py`.

## What a commit costs

The study's budget is 200 milliseconds added to a commit whose tree is already
recorded green, scoped by its own amendment to steady state, once the hook file
has been executed at least once. **Measured here: 41.56 and 41.82 milliseconds
across two runs of twelve pairs, against a budget of 200.**

Each sample is one commit of a staged tree the green record already names, so
the gate takes its success path, and the two arms of a pair differ only by
whether `core.hooksPath` is set. The green was recorded by hand between
samples, because `.githooks/greenlight` runs the whole suite and the suite is
not the gate's per-commit cost:

```
printf '%s\n' "$payload" > demo-timing.txt
git add -A
git write-tree > "$(git rev-parse --git-dir)/LAST_GREEN"   # gated arm only
git commit -m "timing ..."                                  # timed
```

The arms alternated order every iteration so machine drift landed on both. The
driver is a scratchpad script, `metron_commit_overhead.py`, and is not shipped;
it exited zero on both runs with no failed sample.

| Run | Gated median | Gated range | Ungated median | Ungated range | Overhead |
| --- | --- | --- | --- | --- | --- |
| 1, 12 pairs | 81.94 ms | 76.93 to 92.15 | 40.38 ms | 38.60 to 45.82 | 41.56 ms |
| 2, 12 pairs | 77.74 ms | 74.14 to 81.36 | 35.91 ms | 35.30 to 38.24 | 41.82 ms |

The two runs agree to 0.26 ms, and the gap between the arms is several times
the spread inside either of them, so the difference is the gate rather than
noise. Gap 9 below records what a later pair of runs of the same method
measured, and what that leaves of the figure itself. It is not the same
comparison the study's 22 millisecond figure made:
this one is the shipped gate against no hook at all on the real repository,
where step 2 measured the shipped gate against a hook whose body does nothing,
on small fixture repositories. The larger index here is the likely difference,
and this run did not separate the two.

The first-execution cost the study's amendment describes recurred as it
predicted. Row 8, the first commit ever made in this clone, cost 162.27 ms
against a steady state of roughly 80. Rewriting the hook file and committing
again, three times, cost 300.16, 246.09 and 208.41 ms, with the next commit
after each landing at 67.72, 73.42 and 72.83. So the cost is paid per file
instance rather than once per machine, three of the four first executions
exceeded 200 ms, and none of them falls inside the budget clause, which excludes
them by its own terms.

## What this run did not establish

1. **It ran against `1ac5332b`, not the tip that ships.** This record and the
   three `DemonstrationRecordTests` cases were written after the clone was
   taken, so the cloned tree carried 49 cases in `tests/test_commit_gate.py`
   and 1181 in the root suite, where the branch tip carries 52 and 1184. The
   gate itself is byte-identical across that difference; the counts above are
   not the tip's counts.
2. **The clone came from a local worktree, not from GitHub.** The branch is
   unpushed, so no URL existed to clone. The objects are the same objects, but
   nothing here exercises the network path a contributor takes.
3. **`--single-branch` left the clone with no default-branch ref**, which is
   why two of the 1181 cases skipped in every suite run above: the collision
   check in `tests/test_decision_records.py` and its counterpart in
   `tests/test_unique_identifiers.py`. Both say so in their skip message. A
   clone that fetched `origin/main` would run them.
4. **Row 1's exit code came from a second execution.** The first clone's status
   was not captured in the shell that ran it. The identical command was run
   again into a directory used for nothing else and discarded, and 0 is that
   command's code.
5. **The decision record's final filename is not settled here.** It is a draft
   by design, and its number is assigned at merge, so no run on this branch can
   show the name it will carry.
6. **One machine, one git, one interpreter.** Every number above was taken on
   the machine named at the top, with other work running on it, and the study's
   own single-machine caveat carries over unchanged.
7. **The edited file was `.githooks/README.md`.** The suite makes two
   assertions about that file, both presence checks: that it names the
   activation command, and that it carries the literal bypass token. An
   appended comment leaves both green, which is why an edit there was safe;
   a deletion would not be. Adding a new path instead would have moved the
   reading boundary's file count and made row 7 fail for a reason that has
   nothing to do with the gate.
8. **The transcript numbers the commands the conditions turn on, not every
   command the run made.** The two edits are unnumbered, and so is the
   `git add -A` that staged the second one between rows 8 and 9. Following
   rows 1 to 16 in order therefore does not reproduce row 9: with the second
   edit unstaged the tree is still `54f30131`, git finds nothing to commit and
   exits 1 saying so, and the gate is never consulted. Step 5's audit round
   measured both halves in a fresh clone -- the empty-commit refusal from the
   rows as printed, and the gate's refusal naming both trees once the staging
   command is put back.
9. **The overhead figure is not a constant.** The two runs above agree to
   0.26 ms because they were taken minutes apart under one machine load, which
   is repeatability inside a session rather than stability of the quantity.
   Step 5's audit round ran the same method on the same machine against a
   clone of this branch and measured 26.68 and 28.27 ms, both arms lower in
   the same direction: gated medians 49.97 and 52.46 against 81.94 and 77.74
   above, ungated 23.29 and 24.19 against 40.38 and 35.91. All four overheads
   sit far inside the 200 ms budget, and in all four the gap between the arms
   is many times the spread inside either of them. What the measurements
   establish together is that the gate costs tens of milliseconds on this
   machine, not that it costs 41.
