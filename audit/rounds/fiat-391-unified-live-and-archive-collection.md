## Step 1, round 1 -- 2026-08-28T20:47:48Z

Audit schema: fiat-audit-round/v2

Covered: coverage-row-collapse=not-applicable; unrequested-network=not-applicable; schema-refusal=not-applicable; release-id-figures=not-applicable; overlap-attribution=not-applicable; gap-double-count=not-applicable; demo-receipt-drift=not-applicable; markdown-injection=not-applicable

Not checked: every risk-register concern belongs to the collection code, and this step changed none of it. The Pashov pair did not run; the `security_suite` receipt waives it because nothing in scope is Solidity. The three bundled lints ran over the step's changed paths and each exited 0: phylax and ephoros over `plugins/probitas/tests/run_tests.py`, hypomnema over the two committed documents.

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/probitas/tests/run_tests.py | The new runner shipped with mode 100755 while every existing `run_tests.py` in the tree is 100644, and every documented invocation is `python3 <path>` rather than `./run_tests.py`. An execute bit nothing uses is an avoidable difference from the copy it was taken from. | fixed in f1903db1 |
| S1-R1-02 | info | plugins/probitas/tests/run_tests.py | The docstring claimed one copy of the file lives beside each plugin suite. Five of the fourteen plugin suites carry one, counting this file, so a reader who checked would find the claim false. | fixed in f1903db1 |

Leads not pursued: the fixes commit f1903db1 changed no test, so its Elenchus verdict is `unguarded` rather than `guarded`; a file mode and a docstring have no failing case to guard, and inventing one would be theatre. The runner is the sixth copy of one hardened file, so a later fix to its confinement logic will not reach the other five; study item 3 records consolidating them as a non-goal with the reason, and the run's pull request carries it forward. Confinement was exercised by hand rather than by a new test: a report path outside the worktree and an existing target were each refused by name. Nothing else is open.

## Step 1, round 2 -- 2026-08-28T20:52:36Z

Audit schema: fiat-audit-round/v2

Covered: coverage-row-collapse=not-applicable; unrequested-network=not-applicable; schema-refusal=not-applicable; release-id-figures=not-applicable; overlap-attribution=not-applicable; gap-double-count=not-applicable; demo-receipt-drift=not-applicable; markdown-injection=not-applicable

Not checked: nothing new. The same eight concerns still belong to collection code this step does not touch, and the Pashov pair remains waived by the `security_suite` receipt.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the round re-ran the three lints over the fixed tree and each exited 0 again, the Probitas suite reported 276 of 276, the root suite passed, and `portable_promise_machine.py check` and `git diff --check` both exited 0. It also read the two committed documents and the runner for an absolute local path or a checkout name, because this run is hosted in a clone outside the repository and its own paths would be worthless to a reader; none appears. S1-R1-01 and S1-R1-02 are fixed and stay fixed. The unguarded-verdict note under round 1 still stands.
