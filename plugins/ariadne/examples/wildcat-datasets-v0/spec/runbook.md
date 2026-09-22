# Wildcat dataset statements runbook

The accepted study is `.hexaemeron/study.md`. Deliver issue 1374 from
`104f6f82c390003fb61039d3023d07c1abe05086`, using Python 3.14.6 and the existing
stdlib toolchain. Both accepted Wildcat estates remain in scope. The selected
design binds every release file in one unsigned statement per estate.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 4a3752781473722557fb05ab13b5f20223dbf199e2d711e0a7e790fd5287f0bb
candidate | full-release
```

```version-relations
ariadne | plugins/ariadne/skills/ariadne/EVOLUTION.md | next-generation-after-integration-base
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/ariadne/tests/run_tests.py | report_target | 1f9daf1455d272c8deab3c5040dcbe5de80c0ec282203ac3de23cb14129363e5
```

The registered Ariadne runner is the existing reviewed source: its parser
accepts a single optional fresh Elenchus report path, confines that path to the
physical checkout, and discovers the Ariadne tests. Its source stays unchanged.
The final demonstration is reached by the example tests and also run directly
by the coordinator with both external releases. Interface validation alone is
never reported as execution. Test counts come from executed reports.

Inputs are the accepted own-run V1 and V2 rebuilds in
`.hexaemeron/input-evidence/rebuild-recovery.json`. The V2 archive recovery is
an input repair; it earns no code-fix or guard claim. Historical collection
commands remain provenance data. No step executes a statement's commands.

## Step 1: Preserve the specification and accepted input metadata

**Goal.** Ship the accepted design and exact input metadata, with the decisions
and example layout needed to implement the binding.

**Entry.** The run branch at the starting commit above, with the accepted study
and design lock. The executed Ariadne baseline has 902 tests: 888 passed and
14 skipped for their existing reasons.

**Exit.** Commit byte-preserving copies of the study, runbook, design evidence
and ten selection reports under plugins/ariadne/examples/wildcat-datasets-v0/spec/.
Preserve the observed probe record beside its reports. Commit accepted metadata
that names both release IDs, manifest hashes, original producer/source facts,
observed rebuild runtime and argv, plans, registries, staging manifests and
archives. No secret or host credential is copied. Keep full release trees and
archives outside Git. The README gives the input contract and says the binding
implementation is due in Step 2. The existing licence, Python pin and CI are
reused. Record the full-release choice, rejected manifest-only option and
conservative semantic-gap projection in the existing Ariadne ledger under a
plain decision section; the generation row is due with Step 2's delivered
behaviour. Metadata tests check identities, report digests and the exact
recorded input inventory without claiming external bytes were reverified by
those tests. `python3 plugins/ariadne/tests/run_tests.py` and
`python3 scripts/run_checks.py --base 104f6f82c390003fb61039d3023d07c1abe05086`
both exit 0.

**Files.** Create the example README, spec/ copies and input metadata under
`plugins/ariadne/examples/wildcat-datasets-v0/`. Add
`plugins/ariadne/tests/test_wildcat_datasets.py`. Add the decision section to
`plugins/ariadne/skills/ariadne/EVOLUTION.md`. Raise both Ariadne plugin manifest
patch versions for this shipped scaffold. Change `tests/check-map-v1.json` only
if new paths need ownership. Regenerate the portable installation copies and
Horos boundary and census through their source-owned tools where affected.

**Tests.** Check both expected release IDs and manifest hashes, plan/registry
and archive pins, immutable specification copies, all ten report digests and
the full-release selection. These checks establish metadata consistency;
external input verification remains the separately retained executed evidence.
Run the ordinary suite command in Exit. Elenchus command: `python3 plugins/ariadne/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-datasets-step-1.json`.

**Disciplines.** phylax: input metadata must retain access labels without secrets
or executable historical commands. ephoros: the provenance distinguishes
observed rebuilds from original collection and metadata checks from byte
verification. metron: the recorded probe's scope stays limited to listing time
and size, with no performance promise. elenchus: no known current code failure
is claimed; any reproduced implementation defect needs its own guard evidence.
hypomnema: full-release subjects and semantic-gap projection receive their
reason and rejected alternative in the existing ledger when this step ships.

## Step 2: Build and verify both unsigned dataset statements

**Goal.** Deliver the repeatable offline caller adapter and complete evidence
for both real Wildcat releases, using Ariadne's existing dataset interface.

**Entry.** Step 1's reviewed tree and accepted metadata; both external rebuilds
remain available and byte-identical to the accepted releases.

**Exit.** The example demo.py exposes build with a fresh output directory,
verify over a built output directory, and verify-preserved for committed
metadata and reports. The full build reads both accepted real release trees,
verifies their exact inventories, supplies counts through declared selectors,
and invokes the existing capture-dataset path. One statement binds 110 V1
files and one binds 128 V2 files, with exact producer, input and coverage
inventories. Both are unsigned, have a null baseline and explicit first-release
reason, and retain all seven verifier gate lines and three dataset checks.
Every source gap, unsupported collection, source ambiguity and evidence limit
survives. A whole-interval gap represents semantic omissions conservatively;
it does not say blocks were unread. The build records missing-gap,
missing-reason and outside-bound refusals using the real verifier. Existing
output, changed inputs and unsafe filesystem paths refuse before replacement.
Two full executions reproduce identical statement bytes and report contents.
Committed metadata verification identifies its narrower boundary and never
claims a fresh external rebuild. The README states exact invocation, external
input locations or variables, outputs, expected checks, unsigned status and
remaining limitations. Commit compact statements, inventories and complete
reports, with the generation row and matching skill metadata while all mature
frontier fields stay unchanged. `python3 plugins/ariadne/tests/run_tests.py`
and `python3 scripts/run_checks.py --base 104f6f82c390003fb61039d3023d07c1abe05086`
both exit 0. The coordinator also runs the documented build twice against the
actual external releases and verifies both outputs, retaining exact commands,
exit statuses and comparisons outside the release inputs.

**Files.** Add the example adapter and demonstration outputs under
`plugins/ariadne/examples/wildcat-datasets-v0/`; extend its README and metadata
where delivery adds observed evidence. Extend
`plugins/ariadne/tests/test_wildcat_datasets.py`. Update
`plugins/ariadne/skills/ariadne/EVOLUTION.md`, matching skill metadata and both
plugin manifests. Refresh generated installation copies and Horos artefacts
through their owners. Core dataset capture and predicate semantics stay within
the existing interface; any necessary change requires a specification amendment.

**Tests.** Use meaningful independent specimens for selector/count mismatch,
missing/extra/changed release files, wrong manifest/release identity, unsafe
paths, input/output alias, existing destination, incomplete output, modified
statement and forged gate report. The real verifier must reject each of the
three coverage mutations with the coverage check named. A Python no-socket
observation covers the local demo path but claims no operating-system sandbox.
Exercise verify-preserved without archive access and prove it cannot assert a
new rebuild. Full real-input demonstrations are mandatory delivery evidence,
not a silently skipped unit fixture. Elenchus command: `python3 plugins/ariadne/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-datasets-step-2.json`.

**Disciplines.** phylax: validate every supplied filesystem path, metadata value
and output destination; run only owned argv without a shell. ephoros: retain
complete gate outputs and distinguish the full build from metadata-only checks.
metron: stream digests and respect the source component cap; do not claim a
speedup or memory peak without measuring it. elenchus: reproduce any failure,
fix its cause and preserve parent-red/fixed-green guard evidence for a code fix.
hypomnema: reconcile the existing decision section with the implementation and
publish exact reproduction steps and evidence limitations.

### Amendment -- 2026-09-22

**What changed.**
Complete replacement Exit: Commit byte-preserving copies of the study, runbook, design evidence
and ten selection reports under plugins/ariadne/examples/wildcat-datasets-v0/spec/.
Preserve the observed probe record beside its reports. Commit accepted metadata
that names both release IDs, manifest hashes, original producer/source facts,
observed rebuild runtime and argv, plans, registries, staging manifests and
archives. No secret or host credential is copied. Keep full release trees and
archives outside Git. The README gives the input contract and says the binding
implementation is due in Step 2. The existing licence, Python pin and CI are
reused. Record the full-release choice, rejected manifest-only option and
conservative semantic-gap projection in the existing Ariadne ledger under a
plain decision section; the generation row is due with Step 2's delivered
behaviour. Metadata tests check identities, report digests and the exact
recorded input inventory without claiming external bytes were reverified by
those tests. `python3 plugins/ariadne/tests/run_tests.py` and
`python3 scripts/run_checks.py --base 104f6f82c390003fb61039d3023d07c1abe05086`
both exit 0. The complete portable package remains below its unchanged 25 MiB cap with 5 MiB reserve. Its manifest declares that this example requires a full source checkout. Retain only the example README in the portable copy; preserve every example file in the source repository and retain Ariadne capture, verifier and schema runtime files. The README uses source references for omitted evidence and explains that both its metadata verification and full demonstration need the full checkout.

Complete replacement Files: Create the example README, spec/ copies and input metadata under
`plugins/ariadne/examples/wildcat-datasets-v0/`. Add
`plugins/ariadne/tests/test_wildcat_datasets.py`. Add the decision section to
`plugins/ariadne/skills/ariadne/EVOLUTION.md`. Raise both Ariadne plugin manifest
patch versions for this shipped scaffold. Change `tests/check-map-v1.json` only
if new paths need ownership. Regenerate the portable installation copies and
Horos boundary and census through their source-owned tools where affected. Extend the exact example omission in scripts/portable_promise_machine.py and its tests in tests/test_portable_skills.py. Update .agents/skills/promise-machine/PORTABLE.md and append the bounded extension to docs/decisions/drafts/keep-wildcat-interval-demonstration-payloads-in-full-checkouts.md. Propagate package versions through both marketplace manifests and tests/test_version_propagation.py. Refresh dependent Promise Machine runtime-authority and coverage fixtures through their owner, and replay existing evaluation answers only when all prompt bytes and case identifiers are unchanged and every original result field except the tree binding remains identical. Record that replay as no new model observation.

Complete replacement Tests: Check both expected release IDs and manifest hashes, plan/registry
and archive pins, immutable specification copies, all ten report digests and
the full-release selection. These checks establish metadata consistency;
external input verification remains the separately retained executed evidence.
Run the ordinary suite command in Exit. Elenchus command: `python3 plugins/ariadne/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-datasets-step-1.json`. Add a focused portable test that omits this exact example subtree except README, retains unrelated examples and core Ariadne runtime, and checks the actual complete package including its manifest and wrapper against the unchanged budget. Preserve the original over-budget observation. Retain encoded and decoded digests for compressed metadata, check the stored digest before bounded decoding, and check decoded size and digest. Run version, authority, evaluation provenance and portable checks before the full suite; no historical result may be relabelled as a new execution.

Complete replacement Disciplines: phylax: input metadata must retain access labels without secrets
or executable historical commands. ephoros: the provenance distinguishes
observed rebuilds from original collection and metadata checks from byte
verification. metron: the recorded probe's scope stays limited to listing time
and size, with no performance promise. elenchus: no known current code failure
is claimed; any reproduced implementation defect needs its own guard evidence.
hypomnema: full-release subjects and semantic-gap projection receive their
reason and rejected alternative in the existing ledger when this step ships. The portable omission also applies Phylax to exact path selection, Ephoros to the declared omission boundary, and Hypomnema to the dated extension of the existing distribution decision. It does not change the selected dataset design or raise the package budget.

**Why.** The accepted base complete portable package is 20,945,776 bytes, leaving 25,744 bytes below the enforced 20,971,520-byte boundary. Lossless metadata compression alone cannot fit the source specification and demonstration into that allowance. This extends the existing full-checkout evidence policy to one exact Ariadne example while preserving the package cap, source bytes and core runtime.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.
