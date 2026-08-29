# Runbook: give the Kronos scoreboard and parked lane a durable home across ephemeral runners

Derived from [study.md](study.md). Three steps, dependency ordered. Step 1
scaffolds and commits the spec. Step 2 adds `pull` and `push` against a
dedicated git ref. Step 3 wires them into the skill, records the store
location, and runs the demo path.

The run branch is `fiat/462-give-the-kronos-scoreboard-and-parked-lane-a`, cut
from `main` at `2b6848b95e9d90f4bc9995b8cd89106d1807e9a9`. Both suites are
green at that ref: 310 root tests and 930 under the plugin. The Solidity
suite is waived for the run: no step produces Solidity.

Task issue: https://github.com/wildcat-finance/skills/issues/462

## Step 1: Commit the spec

**Goal.** Put the study and this runbook in the repository, where the next two
steps and any later reader can reach them.

**Entry.** The run branch
`fiat/462-give-the-kronos-scoreboard-and-parked-lane-a` at
`2b6848b95e9d90f4bc9995b8cd89106d1807e9a9`, tree clean, both suites green.

**Exit.** `docs/kronos-durable-home/study.md` and
`docs/kronos-durable-home/runbook.md` exist, with every relative link rewritten
for their new depth. Proved by:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/kronos-durable-home/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/kronos-durable-home/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/kronos-durable-home docs/decisions
python3 -m unittest discover -s tests -p "test_*.py"
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/kronos-durable-home/study.md`,
`docs/kronos-durable-home/runbook.md`.

**Tests.** None added. The two existing suites and the hypomnema link check
are the gate. Expected counts unchanged: 310 root, 930 Hexaemeron.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: elenchus.unittest.v1
report file:   tmp/elenchus/step-1.json
```

**Disciplines.** phylax: none, this step adds no boundary and runs no code.
ephoros: none, documents emit nothing. metron: none, no performance claim.
elenchus: none, no failure in hand at entry. hypomnema: this step is the
record, and the link check is what proves the pointers resolve from the new
depth.

## Step 2: Add pull and push against a dedicated state ref

**Goal.** Two subcommands that copy the working copy to and from
`refs/heads/kronos/state` through a throwaway clone, without dirtying the
scope tree Fiat inspects, and without teaching `record`, `park`, `unpark`,
`show` or `parked` to start a subprocess.

**Entry.** Step 1's exit state: the spec committed, both suites green.

**Exit.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py` supports
`pull --root <scope>` and `push --root <scope>`. Default ref
`refs/heads/kronos/state`. Default remote: `KRONOS_STATE_REMOTE` if that
name is already a configured remote, else `upstream` if that remote exists,
else `origin`. A missing ref on `pull` is an empty start (the two JSONL
files are absent afterwards). An existing ref that cannot be read refuses
with `K018` and leaves the working copy untouched. A non-fast-forward
`push` refuses with `K019` and leaves the local files untouched. A remote
that is a URL, or a name git does not list, refuses with `K020`. A git
child that cannot start, times out, or exceeds the output cap refuses with
`K021`. Git is invoked with a fixed argv list, no shell, a 30-second
timeout and a 2 MiB output cap; git stderr is not copied into Kronos
diagnostics. The throwaway clone lives under the system temp directory.
`record`, `park`, `unpark`, `show` and `parked` still start no subprocess.
K010 still refuses a symlink at `.kronos/` or at either JSONL path before
any copy. After `pull`, `record`, `park` and `push`, `git status --short`
in the scope is empty. Proved by
`python3 plugins/hexaemeron/tests/run_tests.py` passing with the new cases,
and by `python3 -m unittest discover -s tests -p "test_*.py"`.

**Files.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py`,
`plugins/hexaemeron/tests/test_kronos_scoreboard.py`.

**Tests.** New cases in `test_kronos_scoreboard.py`, using a local bare
repository as the remote, not the network:

- `pull` of a missing ref leaves both JSONL files absent and exits 0.
- after `park` and `record` on tree A, `push` then `pull` on a second tree
  that has never seen `.kronos/`, `parked` exits 3 with the same held-job
  hash and the same reason bytes, and `show` prints the pass.
- `show` on that second tree prints drift against a later pass whose
  held-job hash did not change.
- extra blobs in the state ref are ignored; only `scoreboard.jsonl` and
  `parked.jsonl` are copied.
- `pull` of an existing ref whose fetch fails refuses with `K018` and does
  not empty a standing park already on disk.
- a symlink at `.kronos/` or at either JSONL path still refuses with
  `K010` on `pull` and on `push`.
- a remote that looks like a URL, and a name git does not list, each refuse
  with `K020`.
- `KRONOS_STATE_REMOTE` naming a configured remote is used when `--remote`
  is absent.
- a non-fast-forward `push` refuses with `K019`; the local JSONL files are
  byte-identical to before the call.
- `record`, `park` and `parked` still succeed when `subprocess` is patched
  to raise, so those verbs stay subprocess-free.
- `git status --short` in the scope is empty after `pull`, `record`,
  `park` and `push`.
- a killed `pull` does not leave a truncated JSONL file that the next
  `record` would accept: the replace is the sibling-temporary then
  `os.replace` already used for the working copy, and a missing final
  newline still refuses with `K008`.

New refusal codes `K018` to `K021` keep `K000` to `K017` unchanged.
Expect the plugin suite above 930 by roughly fourteen cases.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: elenchus.unittest.v1
report file:   tmp/elenchus/step-2.json
```

**Disciplines.** phylax: this step opens the git subprocess and the remote-
name boundary, so argv lists, no shell, no credential flags, timeouts,
output caps and the URL refusal are the controls. ephoros: `pull` printing
the ref tip and whether the working copy was empty or replaced, and `push`
printing the new tip or naming the refusal, are the signals the study's
item 8 asked for. metron: none, no performance claim. elenchus: none at
entry; each new refusal has a case that fails on the unfixed tree.
hypomnema: the interface documentation sits with the script; the store
location and the generation row land in step 3.

## Step 3: Wire the durable home into Kronos, record the decision, and demonstrate

**Goal.** Make the sync verbs part of the loop: a pass starts with `pull`
and publishes with `push` after `record`, `park` or `unpark`; the version
moves to `0.6.0`; the ledger carries one generation row; and the store
location is recorded as the next numbered decision under `docs/decisions/`.

**Entry.** Step 2's exit state: `pull` and `push` shipped, both suites
green.

**Exit.** `SKILL.md` states the durable home, names `pull` and `push`, says
a missing ref is an empty start and an existing-ref pull failure is a
stop, and carries `version: "0.6.0"`. `EVOLUTION.md` carries one new
generation row `kronos-v0.6.0` retaining frontier revision
`terminal-goal-loop` and digest
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` byte for
byte, with status still `mature` and next job still `None -- mature`.
`docs/decisions/ADR-023-store-kronos-working-state-on-a-dedicated-git-ref.md`
records the chosen store and the three options the study rejected. The
field-drift guard still finds every `record` field named in the skill.
Proved by `python3 -m unittest discover -s tests -p "test_*.py"`, which is
where `test_evolution_contract.py` and `test_version_propagation.py` live,
by `python3 plugins/hexaemeron/tests/run_tests.py`, by
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions docs/kronos-durable-home plugins/hexaemeron/skills/kronos`,
and by the demo path:

```bash
# local bare remote, two temporary checkouts of this tree
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py park \
  --scoreboard-dir <A>/.kronos --skill alpha \
  --ledger <A>/alpha/EVOLUTION.md --reason "Waiting on a person." --root <A>
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py record \
  --scoreboard <A>/.kronos/scoreboard.jsonl --root <A> < pass.json
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py push --root <A>
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py pull --root <B>
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py parked \
  --scoreboard-dir <B>/.kronos --root <B>
# exits 3; same held-job hash; same reason bytes
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py show \
  --scoreboard <B>/.kronos/scoreboard.jsonl
git -C <B> status --short   # empty
```

**Files.** `plugins/hexaemeron/skills/kronos/SKILL.md`,
`plugins/hexaemeron/skills/kronos/EVOLUTION.md`,
`docs/decisions/ADR-023-store-kronos-working-state-on-a-dedicated-git-ref.md`.

**Tests.** No new test file. The root suite's evolution-contract and
version-propagation cases prove the ledger row and the version bump agree,
the field-drift guard proves the skill text still names every field the
script accepts, and the hypomnema check proves the ADR carries the dated
status and the five template sections. Counts stay at roughly 310 root and
944 Hexaemeron.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: elenchus.unittest.v1
report file:   tmp/elenchus/step-3.json
```

**Disciplines.** phylax: none, this step adds no boundary; it edits three
documents. ephoros: none beyond what step 2 emits; the skill text now says
when those two lines are printed. metron: none, no performance claim.
elenchus: none, no failure in hand. hypomnema: the two decisions the study
named as expensive to reverse are recorded here, the store location in
ADR-023 because harnesses will grow against it, and the generation row in
the skill ledger because Kronos stays mature.
