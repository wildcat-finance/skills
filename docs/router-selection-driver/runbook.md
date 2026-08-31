# Runbook: grade the router corpus from a driver rather than by hand

Three steps. Step 1 commits the spec and the emitter, step 2 adds the tally
that writes the run block, step 3 demonstrates the whole path against the
corpus on disk. Each step is one pull request and leaves the root suite green.

## Step 1: Commit the spec and emit a leak-free packet

**Goal.** Ship `tests/router_selection_driver.py` with an `emit` command that
writes one prompt file per corpus case, plus a manifest, and carries no field
of a case other than its request.
**Entry.** The run branch `fiat/904-grade-the-router-corpus-from-a-driver-rather`
at its cut from `main` at `48b063c597ebf6aa1978c3c7048ba928d27e7fb5`.
**Exit.** The driver exists and emits; the committed study and runbook are in
the tree; the packet contains no forbidden field. Proved by:
`cd <repo> && python3 tests/router_selection_driver.py emit --out /tmp/pkt-1 && python3 -m unittest tests.test_router_selection_driver && python3 -m unittest discover -s tests -t .`
**Files.** `tests/router_selection_driver.py`,
`tests/test_router_selection_driver.py`,
`docs/router-selection-driver/study.md`,
`docs/router-selection-driver/runbook.md`.
**Tests.** `tests/test_router_selection_driver.py`, new: the emitted packet
reproduces the pinned template with exactly one request substituted; every
emitted byte across every case contains no `expect`, `deciding_sentence` or
`not_established` value; the manifest pins the corpus digest and the exact case
id set; an existing non-empty output directory refuses; a refused emit leaves
no file behind. Expect 8 to 12 cases. Elenchus runner contract: command
`python3 -m unittest tests.test_router_selection_driver 2>&1 | tee {report}`,
format plain unittest text, report file
`.elenchus/router-selection-driver-step-1.txt`.
**Disciplines.** phylax: this step opens the packet-write boundary and reads
the corpus, so its refusals are the controls item 9 names. ephoros: none, the
command runs in a terminal with a person watching, per study item 8. metron:
none, no performance claim. elenchus: none, no failure in hand at entry.
hypomnema: none, the decision record lands in step 3 with the demonstration
that justifies it.

## Step 2: Tally answers into a run block the checker accepts

**Goal.** Add a `tally` command that binds an answers file to a packet, scores
it against `expect`, and rewrites only the corpus `runs` key.
**Entry.** Step 1 merged into the run branch, its tests green.
**Exit.** A tally over a synthesised answers file writes a block the existing
checker accepts, and every binding refusal fires. Proved by:
`cd <repo> && python3 -m unittest tests.test_router_selection_driver && python3 -m unittest tests.test_router_selection && python3 -m unittest discover -s tests -t .`
**Files.** `tests/router_selection_driver.py`,
`tests/test_router_selection_driver.py`.
**Tests.** `tests/test_router_selection_driver.py`, extended: a tally over a
correct answers file produces a block `run_faults` accepts; a manifest whose
corpus digest no longer matches the corpus refuses; an answers file missing one
case refuses; an extra or duplicate case id refuses; an answer outside the
canonical names and the two refusal forms refuses; `cases` and `pairs` stay
byte-identical across the rewrite. Expect 10 to 14 further cases. Elenchus
runner contract: command
`python3 -m unittest tests.test_router_selection_driver 2>&1 | tee {report}`,
format plain unittest text, report file
`.elenchus/router-selection-driver-step-2.txt`.
**Disciplines.** phylax: the answers file is the only untrusted input in the
run, and this step opens it. ephoros: none, same reason as step 1. metron:
none. elenchus: none at entry. hypomnema: none, deferred to step 3 with the
record.

## Step 3: Demonstrate the path and record the decision

**Goal.** Run the demo path from the study's problem statement end to end and
land the decision record.
**Entry.** Step 2 merged into the run branch, its tests green.
**Exit.** The driver emits a packet from the corpus on disk, tallies the 38
answers this surface already recorded, and writes a `runs` block that leaves
`tests.test_router_selection` green, with the corpus otherwise byte-identical
to its state at entry. The decision record exists and the record lint passes.
Proved by:
`cd <repo> && python3 tests/router_selection_driver.py emit --out /tmp/pkt-3 && python3 tests/router_selection_driver.py tally --packet /tmp/pkt-3 --answers docs/router-selection-driver/demonstration-answers.json && python3 -m unittest tests.test_router_selection && git diff --stat tests/fixtures/router-selection/cases.json && python3 -m unittest discover -s tests -t .`
**Files.** `docs/router-selection-driver/demonstration-answers.json`,
`docs/decisions/ADR-<next>-grade-the-router-corpus-from-a-driver.md`,
`tests/router_selection_driver.py`,
`tests/test_router_selection_driver.py`.
**Tests.** `tests/test_router_selection_driver.py`, extended: the committed
demonstration answers tally to the run block currently recorded in the corpus,
so the driver reproduces a result a person produced by hand. Expect 2 to 4
further cases. Elenchus runner contract: command
`python3 -m unittest tests.test_router_selection_driver 2>&1 | tee {report}`,
format plain unittest text, report file
`.elenchus/router-selection-driver-step-3.txt`.
**Disciplines.** phylax: none new, both boundaries are already open and
controlled. ephoros: none. metron: none. elenchus: none at entry. hypomnema:
the decision to stop at the model boundary in both directions is expensive to
reverse and earns the record this step lands, per study item 12.
