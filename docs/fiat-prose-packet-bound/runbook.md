# Prose packet bound runbook

Derived from the receipted study in this directory. Two steps: the first
changes the packet builder and settles the digests that move with it, the
second propagates the version and runs the demo path.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The label is resolved against the integration base rather than written here,
because this repository takes merges in bursts and a label chosen at runbook
time collides with a concurrent run.

## Step 1: Select the prose packet by what a prose pass can act on

### Scope and exit

**Goal.** A step whose diff removes a large generated tree reaches its prose
phase, and the ceiling that remains is the prose packet's own.

**Entry.** The run branch cut from `main` at
`840d8dd3596fd6394901ba85a693bea00c69bf25`, with the study receipted.

**Exit.** `scribe_files` reads the step diff with deleted paths excluded at the
`git` invocation, bounds what remains by a constant of its own rather than by
`GIT_PATHS_MAX`, and refuses with a diagnostic naming the prose packet and what
the ceiling protects. The retained set still runs the existing UTF-8, absolute,
dot and `scoped_path` refusals. `GIT_PATHS_MAX` keeps its value and its two
remaining call sites. The constant block's comment no longer claims the prose
diff cannot grow with the work. The new focused module is registered in the
inherited-signing fixture matrix. Proved by
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_prose_packet_bounds`
exiting 0, `python3 plugins/hexaemeron/tests/run_tests.py` reporting no
failure or error beyond the environmental cases the study names, and
`python3 -m unittest discover -s tests` likewise. The committed study and
runbook pass `protasis.py` and report no `imprimatur.py` defect.

### Files and tests

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
`plugins/hexaemeron/tests/test_hexctl_prose_packet_bounds.py` created;
`plugins/hexaemeron/tests/test_disposable_git_signing.py` extended with the new
module; `docs/fiat-prose-packet-bound/study.md` and
`docs/fiat-prose-packet-bound/runbook.md` created as committed copies of the
receipted bytes. Four checked-in digests of the controller move with it and are
recomputed from this tree rather than replayed:
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/fiat/scripts/hexctl.py`
and `.agents/skills/promise-machine/runtime/MANIFEST.json` through
`python3 scripts/portable_promise_machine.py sync`;
`tests/promise_machine_coverage.json`; `INTEGRATED_CONTROLLER_SHA256` in
`plugins/hexaemeron/tests/test_issue_429_recovery.py`; and `.horos/boundary.json`
regenerated last, after the other artefacts are staged.

**Tests.** Add a focused module building a disposable repository whose step
branch deletes more than `GIT_PATHS_MAX` generated files beside one changed
Markdown artefact, then assert that `next` emits the `prose` directive and that
`brief.files` carries the Markdown path and none of the deleted ones. Add cases
for a rename surviving the filter, for an added path surviving it, for an
authored-prose diff above the new ceiling still refusing, for the refusal text
naming the prose packet, and for the two untouched `GIT_PATHS_MAX` call sites
keeping their bound. The Elenchus runner contract for this step is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.elenchus/fiat-prose-packet-bound-step-1.json`. Record actual final counts
rather than predicting them.

### Discipline routing

**Disciplines.** phylax: the builder consumes path names from a `git`
subprocess against a repository this process does not control, so the filter
goes on the read's argv and every existing grammar and scope refusal still runs
over the retained set. ephoros: the refusal string and the emitted `brief.files`
array are the two signals a contributor reads when this phase stops, and both
change in this step. metron: none, no performance claim is made. elenchus: any
failure surfaced in a round is reduced and guarded through the runner contract
above before Warden reruns it. hypomnema: none in this step; the decision record
belongs to step 2, which is where its number is claimed.

## Step 2: Propagate the version, record the decision, demonstrate

### Scope and exit

**Goal.** The ledger carries one new valid generation row, the decision has a
home, and the demo path from the study's problem statement runs.

**Entry.** Step 1 is green and merged into no branch; this step branches from
step 1.

**Exit.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new
row on the generation axis, retaining the prior frontier revision, frontier
digest and held next job byte for byte, with the header and the row naming the
same version. The numeric version in `plugins/hexaemeron/skills/fiat/SKILL.md`
frontmatter matches the ledger. The Hexaemeron plugin descriptors and both
marketplace manifests carry the moved package version. A decision record under
`docs/decisions/` states why the prose packet selects by what a prose pass can
act on and carries its own ceiling, and why the registry join and the extension
filter were rejected. The demo path from the study runs and exits 0. Proved by
`python3 -m unittest discover -s tests` and
`python3 plugins/hexaemeron/tests/run_tests.py` reporting no failure or error
beyond the environmental cases the study names, and by
`python3 tests/test_version_propagation.py` and
`python3 tests/test_evolution_contract.py` exiting 0.

### Files and tests

**Files.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, and one new record under
`docs/decisions/`. The portable mirror and its manifest, the coverage digests
and `.horos/boundary.json` are regenerated again in that order, because the
skill and controller bytes move in this step too.

**Tests.** No new behaviour test: this step changes metadata and prose, so the
existing version-propagation, evolution-contract, marketplace and boundary
guards are the regression net, together with the demo path from the study. The
Elenchus runner contract for this step is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.elenchus/fiat-prose-packet-bound-step-2.json`.

### Discipline routing

**Disciplines.** phylax: none, this step opens no execution boundary and adds no
input path. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: any guard that turns red under the moved version is
reduced and fixed through the runner contract above rather than by relaxing the
guard. hypomnema: the decision record created here owns the packet-selection
choice, and the ledger row owns the behaviour change it describes.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; `plugins/hexaemeron/tests/test_hexctl_prose_packet_bounds.py` created; `plugins/hexaemeron/tests/test_disposable_git_signing.py` extended with the new module; `docs/fiat-prose-packet-bound/study.md` and `docs/fiat-prose-packet-bound/runbook.md` created as published copies of the receipted bytes, with the study's five discipline-skill links rewritten from skill-relative to repository-relative form so they resolve from `docs/`, which the shipped-tree H001 lint requires. Four checked-in digests of the controller move with it and are recomputed from this tree rather than replayed: `.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and `.agents/skills/promise-machine/runtime/MANIFEST.json` through `python3 scripts/portable_promise_machine.py sync`; `tests/promise_machine_coverage.json`; `INTEGRATED_CONTROLLER_SHA256` in `plugins/hexaemeron/tests/test_issue_429_recovery.py`; and `.horos/boundary.json` regenerated last, after the other artefacts are staged.
**Why.** The published study carried the discipline-skill links in the form Protasis uses from inside a skill directory. Read from `docs/`, all five resolve to nothing, and `tests/test_shipped_tree_lints.py` refuses them as H001. The receipted bytes cannot be edited, so the published copy is no longer byte-identical and the original clause said it was.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.
