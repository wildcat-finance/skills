# Runbook: Ship the Hypomnema design-bridge check

This runbook derives from `.hexaemeron/study.md`. It ships the selected
`closed-bridge-block` construction as one audited boundary because the parser,
its refusal fixtures, the public contract, the portable copy, and the frontier
row are one compatibility surface. Splitting the row from the checked command
would leave either an unclaimed implementation or a ledger claim with no
product behind it.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 8c14e49edd44fa76a5af9307bdcb53532fdb99142a31e9d2a1e53dbdf3dc1463
candidate | closed-bridge-block
```

## Step 1: Check and ship one design bridge

**Goal.** Add one explicit Hypomnema check that binds the candidate selected by
the supplied Protasis record to exactly one declared ADR or governed-skill
ledger, then ship its fixtures, contract, portable copy, study, runbook, and
single frontier transition together.

**Entry.** Start from the clean run branch at
`51fb586e41f67bff1cd53bed8414e3fc63ff48cb`, with the receipted study and design
record unchanged, the current H000 through H007 meanings intact, the existing
project toolchain, CI and licence retained, and the focused Hypomnema,
Hexaemeron, root, portable-copy, and repository-selected checks green.

**Exit.** The established Hypomnema command has an explicit study-check mode
for one caller-named study, strict Protasis design record, and repository root.
One closed `hypomnema-design-bridge/v1` block binds its `decision` row to the
checked selected candidate and its `record` row to one existing ordinary file
in an established ADR or governed-skill-ledger home. H008 refuses an absent or
malformed declaration, mismatched selection, unsafe or unstable path, wrong or
dangling home, symlink or special file, and duplicate homes; valid ADR and
governed-ledger bridges pass. The ordinary walk remains byte-compatible in
meaning for H000 through H007. The exact receipted study and runbook are
committed, all mutable first-party marketplace prose is cold-read and only
stale descriptions are reconciled, the portable runtime is synchronised, and
the Hypomnema frontier advances exactly once under `VERSIONING.md`, with an
evidenced successor or a mature close. Prove the exit with
`python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_checker`,
`python3 plugins/hexaemeron/tests/run_tests.py`,
`python3 -m unittest discover -s tests`,
`python3 scripts/portable_promise_machine.py check`,
`python3 scripts/run_checks.py`, and `git diff --check`; every command exits
zero on the final tree.

**Files.** Change
`plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`,
`plugins/hexaemeron/tests/test_hypomnema_checker.py`, the smallest dedicated
tree below `plugins/hexaemeron/tests/fixtures/hypomnema/`,
`plugins/hexaemeron/skills/hypomnema/SKILL.md`, and
`plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`. Add
`plugins/hexaemeron/docs/hypomnema-design-bridge-check/study.md` and
`plugins/hexaemeron/docs/hypomnema-design-bridge-check/runbook.md` as exact
copies of the receipted artefacts. Cold-read `README.md`, `AGENTS.md`,
`.agents/skills/promise-machine/SKILL.md`, `plugins/hexaemeron/README.md`,
`plugins/hexaemeron/AGENTS.md`, and the first-party Hexaemeron worker and skill
contracts that describe Hypomnema; change only a surface made stale by H008.
Regenerate the generated Promise Machine runtime copies and their manifest with
the repository synchroniser. Change `.horos/boundary.json` only if the required
Horos scan proves its classified-tree evidence changed.

**Tests.** Add direct acceptance fixtures for a valid ADR bridge and a valid
governed-ledger bridge. Add refusal fixtures for no block, a dangling record,
an ADR-plus-ledger duplicate, repeated and malformed rows or blocks, a selected
candidate mismatch, absolute and escaping paths, control and backslash
segments, wrong homes, symlinks, special files, oversized or duplicate-key
design JSON, and unstable reads. Keep direct regression guards for H000 through
H007 and the default walk. Demonstrate every new causal guard failing on the
entry parent before accepting its green result. The Warden-owned Elenchus
runner contract is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`;
report file `tmp/elenchus/fiat-461-step-1.json`. The `{report}` placeholder
occurs exactly once. Record exact final counts rather than predicting them.

**Disciplines.** phylax: the new mode admits caller paths, strict JSON, and one
record path, so lexical containment, bounded ordinary-file reads, duplicate-key
rejection, no symlink following, and stable rereads are step gates. ephoros:
none, this is a synchronous terminal lint and its stable H008 result already
answers the operator questions. metron: none, the step makes no latency or
throughput claim. elenchus: the manual bridge gap and every audit defect receive
a parent-red, fixed-tree-green causal guard through the declared runner.
hypomnema: the selected parser design and rejected inference design belong in
the one new Hypomnema evolution row, never a second ADR.
