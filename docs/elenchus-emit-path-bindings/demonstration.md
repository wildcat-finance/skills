# Demonstration: both emit-path refusals end to end

This is the run record for step 3 of the emit-path bindings delivery. It runs
the demo path from the study's problem statement against a scratch repository
with a real repaired failure in it, and states what each command printed and
exited with.

Nothing below is reconstructed. Every exit code, digest, byte count and refusal
line is what the run printed on this host.

Host Darwin 25.5.0, the interpreter pinned in `.python-version`, git 2.50.1
(Apple Git-155). Entry state `3e6c0b6b`, which is step 2's head and the tree
both scripts were read from. Scratch repository
`/var/folders/2l/ft_wrtys7tj88xf2pkdjcflw0000gn/T/fixed-and-guarded-demo-3l5fd1to`,
made by `tempfile.mkdtemp`. Nothing in this checkout was written, and the run
left no file behind outside that directory and one more: `elenchus.py` stages
its detached parent worktree under a temporary directory of its own and
removes it when the comparison ends.

The working directory throughout is that scratch repository, so `--repo` takes
its default `.` and every input and output path is relative to it, which is the
argv the study's problem statement writes. `fixed_and_guarded.py` and
`elenchus.py` were named by absolute path into this checkout and are written
below relative to this repository's root.

## The record the refusals are measured against

The scratch repository is the one `EndToEnd` builds: base commit
`64f6e16cf2fd0a8a7f5a0f7cf00243ea8bbe527f` holding `src/widget.py` with the
defect, `src/__init__.py`, `tests/__init__.py`, a `.gitignore` and `runner.py`.
`docs/elenchus-fixed-and-guarded-record/demonstration.md` describes the defect
and the repair; this run repeats that path only to earn a genuine result and a
genuine draft, which is what makes the two hostile drafts below a change of
one field each rather than a construction.

1. Reproduce. `python3 -m unittest tests.test_widget -v` with the guard
   written but uncommitted exited **1**, printing 784 bytes whose SHA-256 is
   `0c7f74fcbec72d665a849a9776118cac39a7cfa400363b1e7e4f031d1336cef6`.
2. Repair. The fix and its guard went into one commit
   `37ba98070d043cb8583312ba0a9fc8289e3a9f23`, whose `git diff-tree` names
   `src/widget.py` and `tests/test_widget.py`.
3. Verify. `python3 -m unittest tests.test_widget -v` and
   `python3 runner.py .elenchus/fixed-tree.json` both exited **0**; the
   report normalises to 1 executed, 0 assertion failures, 0 errors.
4. Compare. `elenchus.py --repo . --ref 37ba9807… --test-command "python3
   runner.py {report}" --report-format unittest-json-v1 --report-file
   .elenchus/parent.json --format json` exited **0** with `status`
   `guarded`, `tests` `["tests/test_widget.py"]`, and a parent report of 1
   executed and 1 assertion failure. Its stdout is `inputs/result.json`.
5. Emit. The genuine draft, `guard.test`
   `WidgetRegression.test_negative_width_is_refused` and `repair.files` the
   two paths from step 2, emitted at exit **0**:
   `/private/var/folders/2l/ft_wrtys7tj88xf2pkdjcflw0000gn/T/fixed-and-guarded-demo-3l5fd1to/records/fixed-and-guarded.json: written`.

## The two refusals

Each hostile draft is the genuine draft with one field changed, handed to the
emitter with the same `inputs/result.json`. Both exited **1**, wrote nothing to
stdout, and left no file at `--out`; `records/` still holds only
`fixed-and-guarded.json` afterwards.

### `guard.test` naming a test the guard file never held

`guard.test` set to `NoSuchClass.test_this_test_does_not_exist_anywhere`, the
draft step 3 round 2 of the #1275 run emitted at exit 0.

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --draft inputs/guard-test-absent.json --result inputs/result.json \
  --out records/guard-test-absent.json
```

Exit **1**. The exact stderr:

```
fixed_and_guarded.py: F018 guard.test: NoSuchClass does not occur in tests/test_widget.py at 37ba98070d043cb8583312ba0a9fc8289e3a9f23; the Boundary's named guard is a test that file holds, and a name it never contains is not that guard
```

The line names the first absent segment, the guard file and the repair commit
whose blob was read. `NoSuchClass` is refused before
`test_this_test_does_not_exist_anywhere` is looked for, so one line reports one
segment.

### `repair.files` omitting a changed test file

`repair.files` set to `["src/widget.py"]`, omitting `tests/test_widget.py`,
the shape of finding S1-R6-02 from step 1 round 6 of the #1275 run.

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --draft inputs/repair-files-short.json --result inputs/result.json \
  --out records/repair-files-short.json
```

Exit **1**. The exact stderr, two lines:

```
fixed_and_guarded.py: F019 repair.files: omits tests/test_widget.py from result.tests; every changed test file the comparison used must be one the repair declares
fixed_and_guarded.py: F016 guard.file: tests/test_widget.py is absent from repair.files; the Boundary covers the named guard, and a guard the repair did not touch is not that guard
```

Two lines because the scratch repair changes exactly one test file, which is
also the guard file, so the one omission is both the changed test file `F019`
reads against `result.tests` and the guard file `F016` reads against
`repair.files`. `F019` is held and reported first; the record is composed and
`F016` found on it; the held refusal stops the emit before any write. The
#1275 finding declared two of three files and would meet `F019` alone. `F016`
is a carried-field rule, and it is the control the study names: `--check`
would refuse this record for `F016` had it been written, and never for
`F019`.

## The genuine record under `--check`

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --check records/fixed-and-guarded.json
```

Exit **0**, stdout `records/fixed-and-guarded.json: clean`, stderr empty.

## What this run does not establish

`clean` above says the nine carried fields cohere. It does not say the guard
names a test its file holds or that the repair declares every changed test
file, because `--check` runs none of the emit-path family, `F007`, `F010`,
`F018` and `F019`: each is decided against the result or the repository,
evidence the emitter holds only while it emits, and a record carries no trace
of them. `## Emit the result as a record` in
`plugins/hexaemeron/skills/elenchus/SKILL.md` states that boundary and what
`clean` therefore excludes. A record written by hand with an unbound
`guard.test` and a short `repair.files` reads `clean`;
`RecordRelations.test_check_still_accepts_an_unbound_guard_test_and_a_short_repair_files`
holds that as the stated boundary and not a defect.

The two refusals hold only for a draft that reaches the emit path with its
result and repository present. A record arriving on its own carries no evidence
of which path produced it.

`F018` reads whole-word occurrence of each segment of `guard.test` in the guard
file's blob at the repair commit. It does not parse a test definition, so a
name whose every segment occurs in the file as a comment or a string emits.

The reproduction digest binds a trace carrying the scratch repository's
absolute path, so it is this run's and not a constant another run recomputes.
Both suite results in the record ran in the scratch repository and say nothing
about this repository's suites.

## Reproduced by the suite

`EndToEnd.test_the_demo_path_emits_a_record_and_refuses_the_ones_it_should` in
`plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py` drives the same
path: it builds the scratch repository, reproduces the failure, commits the
repair, runs the comparison, emits the genuine record, and then runs the three
commands above through subprocesses from inside the scratch repository,
asserting exit 1 with `F018 guard.test` on stderr and no file, exit 1 with
`F019 repair.files` on stderr and no file, and exit 0 with
`records/fixed-and-guarded.json: clean` on stdout.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded
```

63 tests, OK, on the committed tree. The three demo-path assertions were added
to the existing case; no assertion it held before was removed.
