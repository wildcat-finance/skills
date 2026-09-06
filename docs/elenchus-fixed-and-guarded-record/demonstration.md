# Demonstration: the fixed-and-guarded record end to end

This is the run record for step 3 of the emission delivery. It runs the demo
path from the study's problem statement against a scratch repository with a
real defect in it, and states what each command printed and exited with.

Nothing below is reconstructed. Every exit code, digest, byte count and refusal
line is what the run printed on this host.

Host Darwin 25.5.0, the interpreter pinned in `.python-version`, git 2.50.1
(Apple Git-155). Entry state `a9eea7a9844dc2f969f92c64723d55fd436e4738`, which
is step 2's head and the tree both scripts were read from. Scratch repository
`/tmp/fixed-and-guarded-demo-BUz5vR`, made by `mktemp -d`. Nothing in this
checkout was written, and the run left no file behind outside that directory
and one more: `elenchus.py` stages its detached parent worktree under a
temporary directory of its own and removes it when the comparison ends.

The working directory throughout is that scratch repository, and `elenchus.py`
and `fixed_and_guarded.py` were named by absolute path into this checkout. Both
are written below as paths relative to this repository's root, which is the only
place the commands are not the literal argv.

## The repository the run builds

Five files at the base commit `20ded6d7b3416abc5d822509f22ad4fc49e55c47`:
`src/widget.py` holding the defect, `src/__init__.py`, `tests/__init__.py`, a
`.gitignore`, and `runner.py`, which runs the suite and writes the
`elenchus.unittest.v1` report the declared runner contract names. The repository
owns its runner because `elenchus.py` classifies from a report the runner writes
and never from an exit code.

The defect is one line out of order:

```python
class Widget:
    def __init__(self, width):
        self.width = width
        if width is None:
            raise ValueError("width is required")
```

`self.width = width` at `src/widget.py:6` runs before any bound is checked, so a
negative width is stored and reaches `area()`.

## 1. Reproduce

The guard is written into the working tree and left uncommitted, so it runs
against the defect first. A guard that never went red is not a guard.

```bash
python3 -m unittest tests.test_widget -v
```

Exit **1**. The 738 bytes it printed, stdout then stderr:

```
test_negative_width_is_refused (tests.test_widget.WidgetRegression.test_negative_width_is_refused) ... FAIL

======================================================================
FAIL: test_negative_width_is_refused (tests.test_widget.WidgetRegression.test_negative_width_is_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/fixed-and-guarded-demo-BUz5vR/tests/test_widget.py", line 8, in test_negative_width_is_refused
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
```

SHA-256 `40513c5ad0355ea25ee140001fc7506e531a2da136c03b89c347e025d1cd65d9`. That
digest covers a trace carrying the scratch repository's absolute path, so it
binds this run's output and not a constant another run could recompute.

## 2. Repair, and the commit that carries it

The check moves above the assignment, and the fix and its guard go into one
commit `08ad9798ae5e5df3bb34094c9b6bca5367e25870`:

```python
class Widget:
    def __init__(self, width):
        if width is None:
            raise ValueError("width is required")
        if width < 0:
            raise ValueError("width must not be negative")
        self.width = width
```

`git diff-tree --no-commit-id --name-only -r 08ad9798ae5e5df3bb34094c9b6bca5367e25870`
names `src/widget.py` and `tests/test_widget.py`.

## 3. Verify on the fixed tree

```bash
python3 -m unittest tests.test_widget -v          # exit 0
python3 runner.py .elenchus/fixed-tree.json       # exit 0
```

The report the second command wrote:

```json
{"schema": "elenchus.unittest.v1", "complete": true, "testsRun": 1, "failures": 0, "errors": 0, "skipped": 0, "expectedFailures": 0, "unexpectedSuccesses": 0}
```

Normalised the way `elenchus.py` normalises a unittest report, that is 1
executed, 0 assertion failures, 0 errors, 0 skipped.

## 4. The guard comparison against the detached parent

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py \
  --repo . --ref 08ad9798ae5e5df3bb34094c9b6bca5367e25870 \
  --test-command "python3 runner.py {report}" \
  --report-format unittest-json-v1 \
  --report-file .elenchus/parent.json \
  --format json > inputs/result.json
```

Exit **0**, and the result it printed, with its diagnostic `output` elided here
because the record never carries it:

```json
{
  "ref": "08ad9798ae5e5df3bb34094c9b6bca5367e25870",
  "status": "guarded",
  "tests": ["tests/test_widget.py"],
  "detail": "the runner report records a parent assertion failure",
  "report": {
    "complete": true, "executed": 1, "assertion_failures": 1,
    "errors": 0, "skipped": 0
  },
  "exit_code": 1
}
```

The guard was seen red on the parent and green on the fixed tree, which is the
comparison the verdict rests on.

## 5. Emit, and the record the checker accepts

Seven fields come from the operator's draft, `verdict` and `unfixed_parent`'s
report come from the result above without translation, and the parent commit
comes from the emitter's own
`git rev-parse 08ad9798ae5e5df3bb34094c9b6bca5367e25870^{commit}
08ad9798ae5e5df3bb34094c9b6bca5367e25870^`.

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --repo . --draft inputs/draft.json --result inputs/result.json \
  --out records/fixed-and-guarded.json
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --check records/fixed-and-guarded.json
```

| Position | Exit | Printed |
| --- | --- | --- |
| emit | 0 | `/private/tmp/fixed-and-guarded-demo-BUz5vR/records/fixed-and-guarded.json: written` |
| `--check` | 0 | `records/fixed-and-guarded.json: clean` |

The record holds `schema` and the nine evidence fields. Its `unfixed_parent`
names `20ded6d7b3416abc5d822509f22ad4fc49e55c47`, the base commit, which the
emitter re-derived rather than read from the draft. Its `reproduction` carries
the digest and the byte count from section 1 and none of those 738 bytes, so
the `AssertionError` line does not appear anywhere in the written file.

## 6. The three refusals

Each takes the accepted record above, changes one thing, and hands it back to
`--check` alone. Every one exited **1** and wrote nothing to stdout.

| Change | Code | Field named |
| --- | --- | --- |
| `guard` removed | F001 | `schema` |
| `verdict.status` set to `inconclusive` | F004 | `verdict.status` |
| `unfixed_parent.report.assertion_failures` set to 0 | F012 | `verdict.status` |

The exact stderr lines:

```
records/without-guard.json: F001 schema: must be one closed elenchus-fixed-and-guarded/v1 object holding exactly the nine evidence fields
records/verdict-inconclusive.json: F004 verdict.status: is inconclusive; the Boundary does not turn an inconclusive, zero-test or infrastructure-failed comparison into a guard
records/parent-never-failed.json: F012 verdict.status: is guarded while unfixed_parent.report records 0 assertion failures and 0 errors; the Refuses clause names a guard that never failed without the fix
```

Two things are worth reading off those lines rather than assumed.

F001 names the rule and the field `schema`, not the field that went missing. A
reader who removes `guard` is told the object is not the closed nine-field one,
and has to compare the key set themselves to learn which key it lost. That is
what the emitter does for every one of the nine, and the study's section 11
authorises the refusal without saying how it should name itself.

F012 is the third refusal because the first two do not reach the case that
matters most for a record arriving on its own. F001 and F004 refuse a record
that is malformed or that says outright it is not a guard. F012 refuses a record
that is well formed and claims `guarded` while its own carried parent report
says nothing failed. That is decided from two fields already in the record, with
nothing outside it read, and it is the class of refusal that makes `--check`
worth running on a record whose producer is not present.

## What this run does not establish

The record covers the reproduced failure and the named guard. It does not prove
the scratch repository defect-free, and the Boundary clause it is built from
does not turn an inconclusive, zero-test or infrastructure-failed comparison
into a guard.

`--check` reads only the fields the record carries. It re-runs no test, resolves
no commit and opens no repository, so it establishes that a record is internally
coherent and never that the runs it describes happened. A record whose counts
were invented but agree with each other passes `--check`.

The emit path adds four things `--check` cannot: it resolves the parent commit
from the repository instead of reading it from the draft, and it refuses a ref
that does not resolve to the commit the draft calls the repair, a `guard.file`
absent from the changed test files the comparison used, and a destination git
already tracks. Those four hold only for a record its own emitter wrote, and no
record carries evidence of which path produced it.

`guard.file` is the whole of the guard either path reads. Its sibling
`guard.test` names the regression test the record is about, and no rule on
either path binds that name to anything it could be wrong about: it is checked
for shape alone, so a draft naming a test that exists in no file is written at
exit 0 and read back `clean`.

The record carries no cross-record identifier by design, so nothing here says
this mechanism has been seen before or will be seen again. The reproduction
output survives as a digest and a byte count, so the record cannot be used to
read the failure back; it can only confirm that bytes offered later are the ones
it saw.

Both suite results in the record are the ones section 3 ran, in the scratch
repository. They say nothing about this repository's suites.

## Reproduced by the suite

`EndToEnd.test_the_demo_path_emits_a_record_and_refuses_the_ones_it_should` in
`plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py` drives the same
path: it builds the same scratch repository under `tempfile.mkdtemp`, reproduces
the failure, commits the repair, runs the same comparison, emits the record, and
asserts the acceptance and all three refusals above.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded
```

The case was checked against two mutations before it was kept. A repair that
leaves the mechanism in place fails it at the fixed-tree run, and a repair that
changes nothing fails it at the changed-file list.
