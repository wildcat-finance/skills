# Runbook: make Protasis the study-amendment shape authority

The study fixes `protasis-v5.9.0` as the frontier-closing evolution. Fiat's
controller change is a generation update whose exact label is resolved from
the integration base rather than pinned here.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

## Step 1: Put study-amendment shape in the Protasis scanner

**Goal.** Extend the one bounded Protasis Markdown walk so study mode owns the
dated final four-field amendment shape under S008 while runbook mode keeps its
P005-specific replacement rules.

**Entry.** The controller-created run branch at
`9e25b995bf4be01919559596d2af2ff65ba896a4`, with the receipted study SHA-256
`92bd2041f75201295d896fb322584b668039f111b67c9a20de8df1a83700eead`, Python
3.14.6, and the 89-test Protasis baseline green.

**Exit.** The receipted study and this runbook are committed byte-for-byte at
`docs/protasis-amendment-block-check-{study,runbook}.md`. One parameterised
helper in `protasis.py` checks real amendment headings, calendar dates, final
placement, the ordered four fields, exact cardinality, and non-empty values.
Study mode reports S008 for a missing date and for each missing required field;
a complete amendment, a study without an amendment, and fenced examples are
clean. Runbook mode still reports P005 and retains every complete-replacement
and Exit-command guard. Diagnostics remain bounded and value-free. Prove this
with `mise exec python@3.14.6 -- python3 -m unittest
plugins.hexaemeron.tests.test_protasis_checker -v`, `mise exec
python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py
--study docs/protasis-amendment-block-check-study.md`, `mise exec
python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py
docs/protasis-amendment-block-check-runbook.md`, `mise exec python@3.14.6
node@26.6.0 -- python3 plugins/hexaemeron/tests/run_tests.py`, and `mise exec
python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py --base
9e25b995bf4be01919559596d2af2ff65ba896a4 --jobs 2`.

**Files.** `docs/protasis-amendment-block-check-study.md`,
`docs/protasis-amendment-block-check-runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/protasis.py`,
`plugins/hexaemeron/tests/test_protasis_checker.py`,
`plugins/hexaemeron/tests/fixtures/protasis/complete-amended-study.md`,
`plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-date-study.md`,
`plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-what-changed-study.md`,
`plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-why-study.md`,
`plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-steps-touched-study.md`,
`plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-still-holding-study.md`,
`.horos/boundary.json`, and `.horos/candidates.json`.

**Tests.** Preserve a parent-red command showing that the entry checker exits
clean for the missing-date fixture and each of the four missing-field fixtures.
Add focused cases for those five S008 failures, a complete fixture, the
existing no-amendment fixture, backtick and tilde fences, longer closing
fences, malformed calendar dates, duplicate and unexpected fields, non-final
sections, text/JSON parity, and unchanged P005 behavior. The Elenchus runner
contract is `mise exec python@3.14.6 node@26.6.0 -- python3
plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format
`unittest-json-v1`, report file
`.elenchus/protasis-amendment-block-step-1.json`. Record observed counts; do
not predict them.

**Disciplines.** phylax: applies because caller-named paths and untrusted
Markdown cross the bounded checker boundary. ephoros: applies only to preserve
the existing finding line, JSON fields, and exit-status signal; no unattended
service or new telemetry exists. metron: none, because the study makes no
performance claim. elenchus: applies to every parent-red omission guard and any
suite failure. hypomnema: applies because the committed study and runbook hold
the scanner-ownership decision until the standing skill and ledger are updated
in Step 2.

## Step 2: Make Fiat consume the verdict and publish the closed frontier

**Goal.** Put the bundled Protasis result before Fiat's durable amendment work,
remove the duplicate study-shape authority, and publish the governed skill and
package surfaces for the completed frontier.

**Entry.** The signed, audit-closed Step 1 head supplied as `branch_from` by the
controller, with its focused and affected checks green and no unreceipted study
or runbook drift.

**Exit.** `hexctl amend study` runs Protasis over the exact captured candidate
before deriving receipt data or writing a pending marker, canonical artefact,
state, or ledger event. Fiat retains exact-prefix discovery, step topology,
touched-step and unbuilt-step verdict checks, recovery, and receipts, but no
independent study date or four-field shape verdict. Malformed shape is refused
through the bounded Protasis result; complete shape reaches only the
controller-owned joins. Protasis documents S008, advances exactly once to
`protasis-v5.9.0`, closes the `amendment-block-check` frontier as mature, and
records `None -- mature` with the recomputed digest. Fiat records the one
generation row selected by the runbook relation while retaining its frontier
tuple byte-for-byte. Hexaemeron's installable package takes the smallest unused
patch successor on the then-current base, and all manifests, registries,
version guards, generated runtime files, Promise bindings, and Horos evidence
agree. A cold read covers every mutable first-party marketplace description;
affected claims are reconciled and unrelated descriptions remain unchanged.
Prove the behavior with `mise exec python@3.14.6 -- python3 -m unittest
plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_protasis_checker
-v`; prove the direct no-amendment demo with `mise exec python@3.14.6 --
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study
plugins/hexaemeron/tests/fixtures/protasis/complete-study.md`; then run `mise
exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/run_tests.py`,
`mise exec python@3.14.6 -- python3 -m unittest discover -s tests`, `mise exec
python@3.14.6 -- python3 scripts/portable_promise_machine.py check`, `mise exec
python@3.14.6 -- python3 scripts/promise_machine.py check`, and `mise exec
python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py --base
9e25b995bf4be01919559596d2af2ff65ba896a4 --jobs 2`. Run Imprimatur on every
changed prose file; run Phylax, Ephoros, and Hypomnema over the required trees;
regenerate and check Horos; validate Agent Skills frontmatter; and finish with
`git diff --check`.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`, `tests/test_evolution_contract.py`,
`tests/test_version_propagation.py`,
`tests/test_child_or_golden_retriever_primer.py`,
`scripts/build_child_or_golden_retriever_primer.py`,
`docs/a-child-or-a-golden-retriever-study.md`,
`docs/a-child-or-a-golden-retriever.pdf`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/fiat/SKILL.md`,
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/protasis/scripts/protasis.py`,
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/protasis/SKILL.md`,
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`.agents/skills/promise-machine/runtime/MANIFEST.json`,
`.horos/boundary.json`, and `.horos/candidates.json`. Mutable marketplace
descriptions in `README.md`, `plugins/hexaemeron/README.md`, `INSTALL.md`,
`docs/how-to-help-shoggoth.md`, the two plugin manifests, and the two marketplace
registries are a required read inventory; only the listed affected surfaces may
change.

**Tests.** Add a parent-red controller guard proving the entry implementation
constructs its amendment record before the bundled Protasis verdict. The fixed
guard must show the malformed candidate is rejected before pending/state/ledger
mutation and that a complete candidate still reaches the controller-only
prefix and verdict checks. Retain every existing study and runbook amendment,
interruption, recovery, fence, topology, and drift test. Add exact evolution
axis/frontier-digest, Fiat relation, package propagation, portable-copy,
Promise-digest, PDF rebuild, and marketplace-version guards where the existing
tests do not already cover them. The Elenchus runner contract is `mise exec
python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, report format `unittest-json-v1`, report file
`.elenchus/protasis-amendment-block-step-2.json`. Record all observed counts,
the final skill/package versions, the frontier digest, and the generated PDF
digest.

**Disciplines.** phylax: applies to the fixed-argv Protasis subprocess,
captured untrusted bytes, bounded output, temporary-file cleanup, and the
pre-mutation refusal boundary. ephoros: applies to preserving distinct bounded
operator diagnostics for Protasis shape rejection and controller-only joins.
metron: none, because no performance result is claimed. elenchus: applies to
the ordering guard and every regression found by the full gates. hypomnema:
applies because the canonical Protasis and Fiat ledgers and skills become the
standing homes for the ownership, S008, generation, and maturity decisions.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: `docs/protasis-amendment-block-check-study.md`, `docs/protasis-amendment-block-check-runbook.md`, `plugins/hexaemeron/skills/protasis/scripts/protasis.py`, `plugins/hexaemeron/tests/test_protasis_checker.py`, `plugins/hexaemeron/tests/fixtures/protasis/complete-amended-study.md`, `plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-date-study.md`, `plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-what-changed-study.md`, `plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-why-study.md`, `plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-steps-touched-study.md`, `plugins/hexaemeron/tests/fixtures/protasis/missing-amendment-still-holding-study.md`, `.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/protasis/scripts/protasis.py`, `.agents/skills/promise-machine/runtime/MANIFEST.json`, `.horos/boundary.json`, and `.horos/candidates.json`.
**Why.** The exact affected-scope runner passed Hexaemeron and every lint but
failed the root portable-runtime currency guards. Deterministic sync must copy
the changed canonical Protasis script and rebind the portable manifest before
Step 1 can reach its already-required green exit.
**Steps touched.** Step 1 only.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds.
