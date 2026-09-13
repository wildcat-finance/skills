# Runbook: the interval collector run against two live providers

Derived from the receipted study at `.hexaemeron/study.md`. Five steps, in
dependency order. Step 1 scaffolds; step 5 runs the demo path the problem
statement names. Every step's exit is proved by a command, and every step
leaves the Alexandria suite and the repository root suite green.

Two rules hold for every step. The Elenchus runner contract is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/reports/conformance/alexandria-unittest.json`. The design record's
conformance cells are produced by the step before the one they block, because
the controller runs the design checker at `step:N` immediately before opening
step N: step 1 produces the cell blocking `step:2`, and so on, with the
`integration` cell produced by step 5.

Only step 4 opens a socket. Its two endpoints arrive through the controller's
brief and reach the collector through `ALEXANDRIA_COMPOUND_RPC_URL` only; no
step writes an endpoint into a file, a receipt, a log line or a message. Every
other step, every test and both demonstrations run under the suite's socket
denial.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 6af1a6bc04f8d019005d52a7ccc648767c48933de54f9bec82d0a244dfc37a8d
candidate | opening-reads-in-collect
```

## Step 1: Scaffold the design records, rebind finality and declare the evidence classes

**Goal.** Commit this run's study, runbook, design record and conformance
script, and change the plan contract and the transport so a `finalized` plan
survives the tag advancing, a plan declares which evidence classes it collects,
and the request headers are constant.

**Entry.** `main` at `f22de68086ad7265869636903554d09cf751e765`.
`alexandria-v1.5.0`, frontier status `open`, revision
`usdc-interval-live-boundaries`, package `0.5.0`. `usdc_interval.py` binds
finality by reading the `finalized` tag and refusing unless its hash equals the
plan's, the plan validator requires exactly `boundary-blocks`, `logs` and
`traces`, and `HttpsTransport` sends `Content-Type` only.

**Exit.** The plan validator in
`plugins/alexandria/scripts/alexandria_lib/interval.py` accepts
`evidence_classes` as any non-empty ordered subset of `boundary-blocks`, `logs`
and `traces`, refusing an empty list, a duplicate or an unknown name by name;
`collect` requests only the declared classes and opens a journal for each.
`bind_finality` reads the plan's boundary block by number, refuses unless its
hash equals the plan's, then reads the `finalized` tag and refuses unless its
number is at or above the plan's boundary; a plan whose boundary block left the
chain refuses by name with an error receipt and no traceback. `HttpsTransport`
sends `User-Agent: alexandria-usdc-interval/<package version>` beside
`Content-Type`, the version read from the plugin manifest at import, and no
header value comes from the environment. The plan schema's descriptions of
`evidence_classes` and the boundary fields state the new contract. The
accepted study and this runbook are committed as
`plugins/alexandria/docs/usdc-interval-live-study.md` and
`plugins/alexandria/docs/usdc-interval-live-runbook.md`; the design record, its
generator, the four candidates and the 28 selection reports are committed under
`plugins/alexandria/docs/usdc-interval-live/` with the relative layout the
record uses, so
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py plugins/alexandria/docs/usdc-interval-live/design-evidence.json --transition design-lock`
exits zero over the committed copy. `.hexaemeron/design/conformance.py` exists,
takes one criterion id, runs that criterion's named tests or commands, writes
one closed `protasis-design-report/v1` object to
`.hexaemeron/reports/conformance/opening-reads-in-collect-<criterion>.json`
with a non-zero exit until the step that earns the criterion has landed, and is
committed byte for byte as
`plugins/alexandria/docs/usdc-interval-live/design/conformance.py`. The
conformance report
`.hexaemeron/reports/conformance/opening-reads-in-collect-finality-rebinds-after-tag-advance.json`
is produced by
`python3 .hexaemeron/design/conformance.py finality-rebinds-after-tag-advance`
and passes, which is what opens step 2; its copy is committed under
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/`. Prove the
exit with that conformance command;
`python3 scripts/run_checks.py --scope alexandria --scope root`;
`python3 scripts/promise_machine.py check`;
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/alexandria/docs/usdc-interval-live-study.md`;
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/alexandria/docs/usdc-interval-live-runbook.md`;
`cmp .hexaemeron/design/conformance.py plugins/alexandria/docs/usdc-interval-live/design/conformance.py`;
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` and
Brevitas over every changed prose file;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/alexandria`;
and `git diff --cached --check`.

**Files.** Create `plugins/alexandria/docs/usdc-interval-live-study.md`,
`plugins/alexandria/docs/usdc-interval-live-runbook.md`,
`plugins/alexandria/docs/usdc-interval-live/design-evidence.json`,
`plugins/alexandria/docs/usdc-interval-live/design/build_design_evidence.py`,
`plugins/alexandria/docs/usdc-interval-live/design/conformance.py`,
`plugins/alexandria/docs/usdc-interval-live/design/candidates/` (four files),
`plugins/alexandria/docs/usdc-interval-live/reports/selection/` (28 files),
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/opening-reads-in-collect-finality-rebinds-after-tag-advance.json`
and `.hexaemeron/design/conformance.py`. Update
`plugins/alexandria/scripts/usdc_interval.py`,
`plugins/alexandria/scripts/alexandria_lib/interval.py`,
`plugins/alexandria/schemas/interval-plan-v1.schema.json`,
`plugins/alexandria/schemas/README.md`,
`plugins/alexandria/tests/test_interval.py` and
`plugins/alexandria/tests/test_usdc_interval.py`. Before the commit, run
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and then
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
over the staged tree, because any tracked-file edit moves the byte counts
`HorosCensusCurrencyTests` checks; commit `.horos/` only if its generated bytes
change. `tests/promise_machine_coverage.json` binds Alexandria evidence by test
path and selector, none of which this step renames, so it stays unchanged;
`DEMONSTRATION.md` pins no file this step touches, so it stays unchanged.
`SOURCES.md` is never hand-edited. The committed study and runbook name
`Next Fiat job` rather than quoting it, because
`tests/test_marketplace_prose.py` reserves that label for the landing README.

**Tests.** Extend `test_interval.py` with cases for a plan declaring one, two
and three classes in either order, and for the empty, duplicate and unknown
refusals, each asserting the message names the class. Extend
`test_usdc_interval.py` with cases for a fixture provider whose `finalized`
tag has advanced past the plan's boundary and still binds; whose boundary
block by number carries a different hash and refuses with a receipt; whose
`finalized` number is below the plan's boundary and refuses; for `collect`
opening journals only for the declared classes and issuing no request for an
omitted one; and for the request headers being exactly `Content-Type` and the
constant `User-Agent` with the environment carrying a decoy header value that
never appears. Every case runs under the socket denial and a missing fixture
fails rather than skips. The Alexandria and root suites must exit zero; counts
are reported from their outputs rather than predicted. The Elenchus runner
contract is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/reports/conformance/alexandria-unittest.json`.

**Disciplines.** phylax: this step changes what the transport sends and what
the plan admits, so it carries the constant header rule, the proof that no
header comes from the environment, and the class refusals. ephoros: the
finality refusal is the study's second on-call question, so it leaves a receipt
naming the boundary and the reason rather than a traceback. metron: none, no
performance claim is made about a validator and two header reads. elenchus:
the `finality-tag-drift` guard is written here and fails against a parent that
refuses a plan whose tag has advanced. hypomnema: plan-declared evidence
classes and the finality rebind are the study's two contract decisions, so
their homes, the plan schema and its catalogue entry, ship here, and the
collector document's rewrite follows in step 5.

## Step 2: Read the interval's opening evidence inside collect and reconcile it

**Goal.** Give `collect` the opening phase the design lock selected, journaled
and checkpointed like a shard and resumable after a kill, and teach
`reconcile` to compare it.

**Entry.** Step 1's exit state, with the class-declaring validator, the
finality rebind and the constant headers in the tree, both suites green and
`.hexaemeron/reports/conformance/opening-reads-in-collect-finality-rebinds-after-tag-advance.json`
passing.

**Exit.** After the last shard commits, `collect` scans the staged logs for
`Upgraded(address)` records on the proxy and reads, through the same
transport and in plan order: the header of the interval's first block, the
EIP-1967 slot at the first block and at each upgrade block, the header at each
upgrade block and at the block before it, and `eth_getCode` for each
implementation at the block its epoch opens. Each read is one record in a
fourth journal class, `epoch-evidence`, whose request identifiers derive from a
virtual shard index one past the plan's last, and the checkpoint commits it
under the existing fields: the next-shard index equals that virtual index and
the journal's committed offset says how many opening reads are committed. A
run killed in the opening phase resumes into it, re-issues only the reads past
the committed offset, and leaves every journal byte-identical to a clean run.
A slot read that is not a left-padded address, a zero address, an empty or
non-hex code read, or an upgrade log whose announced implementation or
`blockHash` disagrees with the preserved reads refuses by name with a receipt.
`reconcile` compares the opening reads as well as the shards: the first
block's hash, each slot word and each code digest, counted under `compared`,
`matched` and `disputed` with their kinds named, and a disagreement is recorded
with both byte sets kept and never settled. The receipt schema gains the kinds.
The conformance report
`.hexaemeron/reports/conformance/opening-reads-in-collect-opening-reads-resumable.json`
is produced by
`python3 .hexaemeron/design/conformance.py opening-reads-resumable` and passes,
which is what opens step 3; its copy is committed under
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/`. Prove the
exit with that conformance command and the same command battery as step 1,
less the two Protasis commands.

**Files.** Update `plugins/alexandria/scripts/usdc_interval.py`,
`plugins/alexandria/scripts/alexandria_lib/interval.py`,
`plugins/alexandria/schemas/interval-receipt-v1.schema.json`,
`plugins/alexandria/schemas/README.md`,
`plugins/alexandria/tests/test_usdc_interval.py`,
`plugins/alexandria/tests/fixtures/usdc-interval-transport.json` and
`plugins/alexandria/tests/fixtures/usdc-interval-second-provider.json`, the
two fixture providers gaining answers for `eth_getStorageAt`, `eth_getCode`
and the first block's header. Create
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/opening-reads-in-collect-opening-reads-resumable.json`.
Run the Horos scan and census before the commit as step 1 states.
`tests/promise_machine_coverage.json` and `DEMONSTRATION.md` stay unchanged for
the reason step 1 gives. `SOURCES.md` is never hand-edited.

**Tests.** Add cases for a clean collection whose `epoch-evidence` journal
holds exactly the reads the plan order names for a one-upgrade interval; for a
kill after the last shard and before the first opening read, and a kill
between two opening reads, each asserting the resumed journals are
byte-identical to the clean run's and that no committed read is re-issued; for
each of the four opening-read refusals; for `reconcile` agreeing on the
opening reads and counting them by kind; and for a second provider that
disagrees on one slot word, asserting the dispute names the kind and keeps both
byte sets. Extend the existing kill-and-resume timing case so the opening
phase is inside the study's 5,000 ms offline budget. Every case runs under the
socket denial and a missing fixture fails rather than skips. The Alexandria
and root suites must exit zero. The Elenchus runner contract is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/reports/conformance/alexandria-unittest.json`.

**Disciplines.** phylax: the opening reads are untrusted provider output on
the same transport, so every slot word, code read and log field is
shape-checked before it is believed and the byte ceiling applies to a code
read. ephoros: the checkpoint after the last shard is the signal answering the
study's first on-call question, so its meaning during the opening phase is
settled here and its tests read it back after a kill. metron: the study's
5,000 ms offline budget is re-measured with the opening phase inside it.
elenchus: the `opening-phase-resume` guard is written here and fails against a
parent whose resume after the last shard re-issues a committed read.
hypomnema: none, the decision that the opening reads live in `collect` is the
design lock's and is already recorded in the committed record.

## Step 3: Build the code-bound release and recheck it offline

**Goal.** Make `build` discover the epochs from the preserved journal, ship
each implementation's runtime code as a component the epoch table names by
digest, and emit `finalized` scopes carrying both hashes, with `check`
re-hashing the bytes.

**Entry.** Step 2's exit state, with the opening phase and its reconciliation
in the tree, both suites green and
`.hexaemeron/reports/conformance/opening-reads-in-collect-opening-reads-resumable.json`
passing.

**Exit.** `build` no longer takes `--epochs`: it calls `discover_epochs` over
the `epoch-evidence` journal and refuses a staging tree whose journal is absent
or whose checkpoint has not committed the opening phase. It emits two new
components, `epoch-evidence` holding the journal and `implementation-code`
holding each implementation's runtime bytes keyed by address, and the epoch
table names the `implementation-code` component and each epoch's
`implementation_code_sha256`. Every evidence capture's scope carries finality
`finalized` with `start_hash` equal to the hash in the collector's own
first-block read and `end_hash` from the last shard, and `_gaps` names every
class the plan omitted with the reason, on evidence components only. `check`
requires exactly ten components, re-hashes each implementation's bytes from
the component and refuses by name a digest the bytes do not carry, an
implementation the component lacks, a scope with one hash and not the other,
and a plan and journals that disagree about the declared classes. The
synthetic `usdc-interval-v0` example keeps its role and its kill-and-resume
path: its fixture providers gain the opening-read answers `fixtures/epochs.json`
used to supply, that file is removed, and `expected.json` and the README are
re-pinned to the identifier the changed release now derives. The two
conformance reports
`.hexaemeron/reports/conformance/opening-reads-in-collect-scope-binds-both-hashes.json`
and
`.hexaemeron/reports/conformance/opening-reads-in-collect-code-hash-rechecked-from-component.json`
are produced by
`python3 .hexaemeron/design/conformance.py scope-binds-both-hashes` and
`python3 .hexaemeron/design/conformance.py code-hash-rechecked-from-component`
and pass, which is what opens step 4; their copies are committed under
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/`. Prove the
exit with those two conformance commands, the same command battery as step 2,
and
`python3 plugins/alexandria/examples/usdc-interval-v0/demo.py build --output <directory>`
followed by
`python3 plugins/alexandria/examples/usdc-interval-v0/demo.py verify <directory>`.

**Files.** Update `plugins/alexandria/scripts/usdc_interval.py`,
`plugins/alexandria/scripts/alexandria_lib/interval.py`,
`plugins/alexandria/schemas/interval-receipt-v1.schema.json`,
`plugins/alexandria/tests/test_usdc_interval.py`,
`plugins/alexandria/tests/test_usdc_interval_demo.py`,
`plugins/alexandria/examples/usdc-interval-v0/demo.py`,
`plugins/alexandria/examples/usdc-interval-v0/fixtures/primary.json`,
`plugins/alexandria/examples/usdc-interval-v0/fixtures/secondary.json`,
`plugins/alexandria/examples/usdc-interval-v0/expected.json` and
`plugins/alexandria/examples/usdc-interval-v0/README.md`. Delete
`plugins/alexandria/examples/usdc-interval-v0/fixtures/epochs.json`. Create
the two conformance report copies under
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/`. Run the
Horos scan and census before the commit as step 1 states.
`tests/promise_machine_coverage.json` binds no selector this step renames and
`DEMONSTRATION.md` pins `credit-history-v0` only, so both stay unchanged;
the re-pinned identifier lives in the example's own `expected.json`.
`SOURCES.md` is never hand-edited.

**Tests.** Add cases for a build over a reconciled tree whose manifest carries
ten components, `finalized` on every evidence scope and both hashes, with
`start_hash` asserted equal to the journal's first-block read; for a build
over a tree with no `epoch-evidence` journal being refused; for `check`
refusing one flipped byte in `implementation-code`, one changed hex digit in
an epoch's digest, an implementation missing from the component, a scope with
one hash, and a plan whose classes disagree with the journals, each by name
and separately; for a plan omitting `traces` naming the gap on every evidence
component and on no other; and for two builds over the same tree yielding one
identifier. Update the demo cases for the re-pinned identifier and for the
removed epoch fixture, keeping the rule that a missing fixture fails rather
than skips. The Alexandria and root suites must exit zero. The Elenchus runner
contract is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/reports/conformance/alexandria-unittest.json`.

**Disciplines.** phylax: the journal is now input to `build` and the release
is input to `check`, so records are shape-checked before they are believed
and the code component is re-hashed rather than trusted. ephoros: `check`
prints the epoch count and the re-hashed digests, which is the study's fourth
on-call question. metron: none, no performance claim is made about a build
over a tree under 300 KB. elenchus: the `code-digest-rebind` and
`start-hash-source` guards are written here and fail against a parent whose
`check` accepts a declared digest without re-hashing. hypomnema: the retired
`--epochs` argument and the two new components change the collector's public
commands, so the collector document's rewrite in step 5 records them; nothing
else here earns a record of its own.

## Step 4: Run the collector against two live providers and preserve the capture

**Goal.** Collect and reconcile the declared 2,000-block interval from the two
providers the study selected, and check the preserved bytes into the tree as
the example the offline demonstration will rebuild.

**Entry.** Step 3's exit state, with the code-bound `build` and `check` in the
tree, both suites green, the two step 3 conformance reports passing, and the
two endpoints in the controller's brief, primary first.

**Exit.** This is the only step that opens a socket, and these are its reads,
all JSON-RPC over HTTPS with no credential. With `ALEXANDRIA_COMPOUND_RPC_URL`
set to the primary endpoint, Wildcat's staging gateway,
`python3 plugins/alexandria/scripts/usdc_interval.py collect --plan plugins/alexandria/examples/usdc-interval-live-v0/plan.json --staging <staging>`
binds the `finalized` boundary, walks four shards of 500 blocks over
25,903,935 to 25,905,934 with `eth_getBlockByNumber` and `eth_getLogs`, and
makes the opening reads with `eth_getBlockByNumber`, `eth_getStorageAt` and
`eth_getCode`; the plan declares `boundary-blocks` and `logs`, provider class
`archive gateway, public tier, no trace methods`, and no `trace_filter` is
issued. With the variable set to the second endpoint, the mevblocker relay,
`python3 plugins/alexandria/scripts/usdc_interval.py reconcile --plan <plan> --staging <staging> --provider-class "public relay endpoint, archive logs and state, no trace methods"`
records `agreed` with `compared` at least 8 and `disputed` empty. The
variable is set for those two commands only and appears in no file, receipt,
log line, test, document, commit message or message to the controller. The
staging tree, about 250 KB of journals, checkpoint and receipts, is committed
as `plugins/alexandria/examples/usdc-interval-live-v0/staging/`, beside
`plan.json`, `registry.json`, `demo.py`, `README.md` and `expected.json`
pinning the release identifier, `epochs: 2`, `reconciliation: agreed`,
`shard_statuses: {complete: 4}`, the two implementation addresses and code
digests and the interval's start and end hashes as the collector observed
them. The release is checked offline afterwards:
`python3 plugins/alexandria/scripts/usdc_interval.py build --plan <plan> --staging plugins/alexandria/examples/usdc-interval-live-v0/staging --registry <registry> --created-at <timestamp> --output <release>`
and `python3 plugins/alexandria/scripts/usdc_interval.py check <release>`
exit zero and report those values, `python3 plugins/alexandria/scripts/alexandria.py verify <release>`
accepts it, and
`python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py build --output <directory>`
followed by `demo.py verify <directory>` rebuilds the release from the
committed staging tree to the pinned identifier with no socket. The
conformance report
`.hexaemeron/reports/conformance/opening-reads-in-collect-live-interval-reconciled.json`
is produced by
`python3 .hexaemeron/design/conformance.py live-interval-reconciled`, which
wraps the two network commands, records elapsed milliseconds against the
study's 120,000 ms budget and the reconciliation status, and passes, which is
what opens step 5; its copy is committed under
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/`. Prove the
exit with that conformance command, the offline commands above, the same
command battery as step 2, and
`grep -rIl "$ALEXANDRIA_COMPOUND_RPC_URL" plugins/alexandria .hexaemeron/reports`
returning nothing while the variable is still set.

**Files.** Create `plugins/alexandria/examples/usdc-interval-live-v0/plan.json`,
`plugins/alexandria/examples/usdc-interval-live-v0/registry.json`,
`plugins/alexandria/examples/usdc-interval-live-v0/staging/` (the preserved
journals, checkpoint and receipts, committed as collected),
`plugins/alexandria/examples/usdc-interval-live-v0/demo.py`,
`plugins/alexandria/examples/usdc-interval-live-v0/expected.json`,
`plugins/alexandria/examples/usdc-interval-live-v0/README.md`,
`plugins/alexandria/tests/test_usdc_interval_live_demo.py` and
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/opening-reads-in-collect-live-interval-reconciled.json`.
Update `plugins/alexandria/examples/README.md`. Run the Horos scan and census
before the commit as step 1 states; the journals are JSONL and the scan
classifies them. `tests/promise_machine_coverage.json` and `DEMONSTRATION.md`
stay unchanged for the reason step 1 gives; the live example is not registered
as the public demonstration record, which the study's section 3 leaves to a
follow-up. `SOURCES.md` is never hand-edited.

**Tests.** Create `test_usdc_interval_live_demo.py` with cases for `demo.py
build` rebuilding the release from the committed staging tree to the pinned
identifier with `epochs: 2`, `reconciliation: agreed` and four complete
shards; for `verify` comparing the identifier, the epoch count, the
reconciliation status and both code digests with `expected.json` and refusing
a tampered release; for one flipped byte in a committed journal changing the
identifier; for no socket being opened on either path; and for the committed
plan, staging tree and expectation containing no `https://` string. A missing
journal, plan, checkpoint or expectation fails rather than skips. The
Alexandria and root suites must exit zero. The Elenchus runner contract is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/reports/conformance/alexandria-unittest.json`.

**Disciplines.** phylax: this step opens the two transport boundaries for real
and the endpoint boundary, so it carries the endpoint suppression proof, the
constant headers, the no-retry refusal of a 403 or 429, and the rule that the
committed capture is shape-checked input. ephoros: this is the step that runs
unattended, so the checkpoint, the error receipts and the sanitised exit line
are its signals, and the reconciliation record answers the study's third
on-call question. metron: the study's 120,000 ms live budget is measured here
by the conformance command. elenchus: the `preserved-bytes-identity` guard is
written here and fails against a parent whose demonstration accepts an edited
journal. hypomnema: the preserved interval's identifier is permanent once
cited, so `expected.json` and the example README are its home.

## Step 5: Document the collector, reconcile the marketplace prose and advance the frontier

**Goal.** Ship the rewritten collector document, the reconciled marketplace
prose, the version advance and the one evolution row this frontier run owes,
then run the demo path.

**Entry.** Step 4's exit state, with the live example and its demonstration
in the tree, both suites green and
`.hexaemeron/reports/conformance/opening-reads-in-collect-live-interval-reconciled.json`
passing.

**Exit.** `plugins/alexandria/docs/usdc-interval-collector.md` states the
finality rebind in place of "Finality is operator policy", plan-declared
evidence classes, the constant `User-Agent` and the refusal of credential
headers, provider classes rather than operators, the opening reads and the two
new components, the retired `--epochs` argument, and what the collector still
does not establish: no publisher identity, no provider completeness, no
consensus finality, no canonical-chain membership, no traces, no mapping and
no market other than Ethereum USDC. `plugins/alexandria/AGENTS.md`'s network
paragraph names the constant header and the two live examples' socket rule,
and the plugin README and `AGENTS.md` are cold-read whole and reconciled with
the tree. The canonical `SKILL.md`, the runtime `AGENTS.md`, the plugin README
and every mutable `marketplace-context` block in the plugin carry the same
rewritten `**Current frontier.**` line, and the landing README's single
rolling next-job line keeps the exact prefix and suffix
`tests/test_marketplace_prose.py` declares; no other shipped document may
carry that label, which is why this committed copy names it rather than
quoting it. `EVOLUTION.md` carries exactly one new row on the `evolution`
axis, `alexandria-v2.5.0`, with a new frontier revision, a digest recomputed
over its own changed frontier line, evidence citing issue `#1350` and the
committed study, and a next job settled from the evidence at that point:
either an open successor with its acceptance condition or `None -- mature`
with status `mature`. `SKILL.md` frontmatter states `2.5.0`. The delivery
package advances from `0.5.0` to `0.6.0` in
`plugins/alexandria/.claude-plugin/plugin.json`,
`plugins/alexandria/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json` and `DELIVERY_PACKAGE_VERSIONS` in
`tests/test_version_propagation.py`. The conformance report
`.hexaemeron/reports/conformance/opening-reads-in-collect-demo-reproduces-live-release-id.json`
is produced by
`python3 .hexaemeron/design/conformance.py demo-reproduces-live-release-id`
and passes, which is what admits the completed stack to integration; its copy
is committed under
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/`. Prove the
exit with the demo path,
`python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py build --output <directory>`
then
`python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py verify <directory>`;
that conformance command; the same command battery as step 2; and
`python3 -m unittest tests.test_marketplace_prose tests.test_version_propagation tests.test_evolution_contract`.

**Files.** Update `plugins/alexandria/docs/usdc-interval-collector.md`,
`plugins/alexandria/docs/compound-v3-harvest.md`, `plugins/alexandria/AGENTS.md`,
`plugins/alexandria/README.md`, `plugins/alexandria/skills/alexandria/SKILL.md`,
`plugins/alexandria/skills/alexandria/agents/openai.yaml`,
`plugins/alexandria/skills/alexandria/EVOLUTION.md`,
`plugins/alexandria/.claude-plugin/plugin.json`,
`plugins/alexandria/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`
and `tests/test_version_propagation.py`. Update the `marketplace-context`
blocks, and only those blocks, in `plugins/alexandria/docs/address-index.md`,
`credit-view.md`, `data-dictionary.md`, `raw-releases.md`, `runbook.md`,
`study.md`, `usdc-interval-runbook.md`, `usdc-interval-study.md`,
`usdc-interval-live-study.md`, `usdc-interval-live-runbook.md`,
`plugins/alexandria/examples/README.md`,
`plugins/alexandria/examples/compound-v3-phase0-v0/README.md`,
`plugins/alexandria/examples/credit-history-v0/README.md`,
`plugins/alexandria/examples/proof-backed-state-v0/README.md`,
`plugins/alexandria/examples/usdc-interval-v0/README.md`,
`plugins/alexandria/examples/usdc-interval-live-v0/README.md` and
`plugins/alexandria/schemas/README.md`. Create
`plugins/alexandria/docs/usdc-interval-live/reports/conformance/opening-reads-in-collect-demo-reproduces-live-release-id.json`.
Leave `plugins/alexandria/skills/alexandria/DEMONSTRATION.md` alone: it pins
`credit-history-v0` sources this run does not touch, and the demo lane's next
job stays as written. Leave `tests/promise_machine_coverage.json` alone for
the reason step 1 gives. Run the Horos scan and census before the commit as
step 1 states. `SOURCES.md` is never hand-edited: the refresh
`plugins/hexaemeron/skills/VERSIONING.md` names runs after the ledger row and
before the integration merge through the tool the maintainer holds, and a
failed or unavailable check changes nothing.

**Tests.** No new test file. The marketplace-prose, version-propagation and
evolution-contract cases must pass against the reconciled tree, and the
Alexandria and root suites must exit zero with the live demonstration's cases
from step 4 unchanged. The Elenchus runner contract is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.hexaemeron/reports/conformance/alexandria-unittest.json`.

**Disciplines.** phylax: none, this step opens no boundary; it changes prose,
manifests and the ledger. ephoros: none, the demonstration is a command a
reader runs and watches, so its stdout and exit status are the whole signal.
metron: none, no performance claim is made about the demonstration or the
prose. elenchus: none, no failure is in hand; a failure found here follows
the study's guard convention in the plugin's own suite. hypomnema: the
collector document is the home the study named for the finality rebind, the
declared classes, the header rule and the provider-class rule, and the ledger
row is the home for the frontier advance.
