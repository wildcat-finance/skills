# Study: the resumable Ethereum USDC interval collector

Assuming, unless corrected:

1. The exact interpreter in `.python-version`, 3.14.6, with the standard
   library and `unittest`. Alexandria adds no third-party dependency.
2. No archive RPC endpoint is reachable from this run. `ALEXANDRIA_COMPOUND_RPC_URL`
   is unset here, and the contributor cannot be asked for a credential, so the
   live path ships behind the same environment-variable boundary Phase 0 uses
   and is proved against an injected transport rather than against a provider.
   Every claim about live behaviour in this run is a claim about that boundary,
   not about a provider that answered.
3. The target is one market: the Ethereum mainnet Compound v3 USDC Comet at
   proxy `0xc3d688b66703497daa19211eedff47f25384cdc3`, the market Phase 0
   already pinned. The other 27 registry entries stay out of scope.
4. A working prototype collects a bounded interval, not the market's whole
   history. The held job says "the first resumable interval collector"; a
   complete Ethereum USDC harvest is a separate operation run against this
   machinery.
5. Alexandria's existing release contract is fixed. The collector emits a
   capture plan the current `ingest` accepts and the current `verify` passes;
   it does not change `release.py`, the manifest format or the schemas that
   already ship.
6. This run produces no Solidity, so the Pashov suite is waived by receipt and
   the three bundled lints carry the audit rounds.

## 1. Problem statement

Alexandria can preserve a capture somebody else produced, and Phase 0 proved
that one public Ethereum endpoint answers the eleven JSON-RPC methods a
Compound v3 harvest needs. Nothing between those two facts exists: there is no
command that walks a block interval, keeps what it collects, survives being
killed, and hands the result to `ingest`. `docs/compound-v3-harvest.md`
specifies that harvester in detail and its opening sentence says it is not
built.

This builds it, for the operator who wants a reproducible Compound v3 USDC
record and for Tabularium, whose own held job is Phase 1 mapping over exactly
this evidence.

A working prototype here is one command. It collects a declared block
interval of the Ethereum USDC Comet in bounded shards, from a transport it is
given, and can be killed at any point and resumed to a byte-identical result;
it discovers the implementation epochs covering that interval from chain
evidence rather than assuming one; it runs the completed interval past a second
provider and records agreement or a dispute; it binds its end boundary to a
named finality policy; and the release it produces passes Alexandria's existing
offline verification plus a new interval-level check.

**The demo path that proves it**, and the last runbook step:

```bash
python3 plugins/alexandria/examples/usdc-interval-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/usdc-interval-v0/demo.py verify <directory>
```

`build` runs the collector against the checked-in fixture provider, kills and
resumes it, reconciles it against the second fixture provider, ingests the
release and verifies it offline. `verify` re-derives the release identifier and
compares it with the one the example records. Both are offline and neither
touches a network socket.

## 2. Prior art

### In this repository

`plugins/alexandria/scripts/alexandria_lib/release.py` is the release contract:
`ingest` reads a `alexandria-capture-plan/v1` document plus the confined local
files it names, copies each component's bytes unchanged into a digest-derived
object path, writes a canonical manifest and installs the directory atomically.
`verify` re-reads it offline and refuses an undeclared release entry. Three
limits in that file shape everything below: `MAX_COMPONENTS = 128`,
`MAX_CAPTURES = 1024` and `MAX_RAW_COMPONENT_BYTES = 64 * 1024 * 1024`.
`_validate_coverage_against_bytes` resolves each declared coverage collection's
JSON pointer against the component's own bytes and refuses a declared count
that the payload does not carry, so a coverage figure cannot be asserted.

`plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` and its CLI
`scripts/compound_v3_phase0.py` are the closest prior art. Phase 0 captures a
fixed 27-request corpus from one HTTPS endpoint named only by
`ALEXANDRIA_COMPOUND_RPC_URL`, never records the endpoint or its headers, caps
the capture at 300 seconds and 128 MiB, ingests the result through the same
`ingest`, and checks a bounded set of relationships offline. It establishes
that the measured endpoint serves `trace_filter`, `trace_transaction`,
`debug_traceTransaction` in call, prestate and opcode modes, archive
`eth_getStorageAt`, `eth_getCode` and a `finalized` header, and refuses
`rpc_modules` with `-32601`. That is the method proof this collector consumes;
it is not an interval and claims none.

`plugins/alexandria/scripts/alexandria_lib/compound_registry.py` pins the
Comet registry at `compound-finance/comet` commit
`f766f51583c23acc33b2a7824654ef2029a96804`, 28 markets across 10 chains, and
supplies the `roots.json`, `configuration.json`, `deploy.ts` and `relations.ts`
bytes for a deployment.

`plugins/alexandria/docs/compound-v3-harvest.md` is the production collection
plan and the specification this delivery is measured against. Its "Ranges,
checkpoints and reorgs" section names the seven-step loop, the checkpoint's
exact fields and the rewind rule; "Provider reconciliation and errors" names
the identity tuple `(blockHash, transactionHash, logIndex, address, topics,
data)` and forbids deciding a disagreement by majority or by which endpoint
answered first; "Acceptance" lists eleven conditions. That document was written
before any of it existed and is treated here as the requirement, not as
description.

`plugins/alexandria/examples/credit-history-v0/` is the shape a checked-in
offline demonstration takes: a `demo.py` with `build` and `verify`, a pinned
plan, and expected digests a test asserts. The Compound Phase 0 example under
`examples/compound-v3-phase0-v0/` is the shape a preserved release takes, with
`input/requests/`, `input/responses/` and a digest-keyed `release/objects/`
tree.

`tests/test_marketplace_prose.py` enforces the prose reconciliation this
frontier run owes. Every mutable `marketplace-context` block in the plugin must
carry the same `**Current frontier.**` line as the plugin's landing README, the
single rolling next-job line must keep the exact prefix and suffix that file
declares, and no other shipped document may carry that label at all. This
committed copy therefore names it rather than quoting it.

### Last two merged pull requests touching the target

`#1003`, merged 31 August 2026, rewrote the Shoggoth contributor prose and
touched `plugins/alexandria/PROMISE_MACHINE.md`, `README.md` and
`skills/alexandria/SKILL.md`. Its stated boundary is that it edits no audit,
ledger, historical study or runbook. It carries nothing forward for this run.

`#776`, merged before it, changed `examples/credit-history-v0/expected-probitas.json`
and `tests/test_demo.py` while restoring Morpho Midnight coverage in Probitas.
`#764` before that is the issue-391 unified-collection run, the change the
`alexandria-v0.4.0` ledger row cites.

Both `#776` and `#764` return 404 from the GitHub REST and GraphQL APIs for
this account, so their pull-request bodies and the "Carried forward" sections
in them could not be read. What #764 left behind was published separately as
issue `#882`, "Remnants of the issue 391 unified-collection run", which is
readable and was read in full. Four of its items touch Alexandria:

- The Alexandria test suite runs in no CI workflow. `repo.yml` runs `tests/`
  only, so Alexandria's suite has only ever run on a contributor's machine.
  Carried forward again here as a stated non-goal, in item 3: closing it needs
  a workflow file plus entries in `PYTHON_WORKFLOWS` and
  `PLUGIN_WORKFLOW_PATHS` in `tests/test_python_contract.py`, which is
  repository-wide work rather than this collector's.
- The archive-only route's unreached coverage note drops the registry's
  description of a venue. It belongs to a change that owns the demonstration's
  pinned digests. This run creates a new demonstration and does not alter
  `credit-history-v0`, so it stays open.
- `_collect_alexandria` silently drops a coverage row for a venue the index
  holds and the registry does not know. Unchanged by this run and still open.
- The `alexandria-v0.4.0` ledger row cites only its issue where its Probitas
  sibling also cites a committed study. This run's row cites both the issue and
  the study committed in step 1, which answers the observation for the row it
  writes without rewriting history.

The model-proxy `MP407` symlink refusal on macOS in the same issue is a
platform fault outside this plugin. It is recorded here because this run is
hosted on macOS and `TMPDIR` sits under `/var/folders`: any temporary directory
this collector's tests use has the same alias, and the Phase 0 audit already
found and fixed one instance of it, S1-R1-03 in the `#407` record. The
collector's own path confinement has to resolve its root before comparing.

### Audit record reading

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root and exited zero, with every listed record reporting
`committed=match`, so the verified synopsis is the reading view for every
in-scope source. Two in-scope sources exist; there is no
`plugins/alexandria/audit/` directory, so the root pair covers only the root
source and neither record is reached through it.

`audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.synopsis.md` was
read, not its source. Three rounds, one step. Covered:
`subject-binding=reviewed; predicate-fidelity=reviewed;
untrusted-release=reviewed; output-confinement=reviewed; partial-write=reviewed;
claim-inflation=reviewed; schema-drift=reviewed; determinism=reviewed`
throughout. Not checked: the waived Pashov pipelines, DSSE signing, cosign,
publisher identity, provider completeness, consensus finality, canonical-chain
proof, network and RPC behaviour, hostile concurrent writers holding permission
on the output directory, and hosted CI. Elenchus verdicts `passed`, `guarded`,
then null. Findings: `S1-R1-01` medium, a temporary-file descriptor and
directory entry surviving a failed post-open `os.fstat()`, fixed in
`eb8dc5b3`; `S1-R1-02` low, the report writer leaving a fresh report behind
after the same failure, fixed in `eb8dc5b3`; `S1-R1-03` medium, an absolute
report path compared against a resolved worktree root, so macOS `/var/folders`
against `/private/var/folders` made the runner refuse its own contained report,
fixed in `bac7e2ff`; `S1-R2-01` medium, a verified manifest under Alexandria's
8,388,608-byte control limit producing a statement above Ariadne's identical
input cap, fixed in `775b151c`. Leads not pursued: a hostile process already
able to write the output directory can race the temporary name, which the step
does not promise against; a directory-descriptor `close()` failure after a
successful replacement cannot safely roll back; cross-field schema equalities
remain emitter and verifier checks rather than standalone JSON Schema proofs;
and non-UTF-8 output filenames were not reproducible on macOS.

`audit/rounds/fiat-391-unified-live-and-archive-collection.synopsis.md` was
read, not its source. Nine rounds across four steps, mostly Probitas. Covered
concerns across its rounds: `coverage-row-collapse`, `unrequested-network`,
`schema-refusal`, `release-id-figures`, `overlap-attribution`,
`gap-double-count`, `demo-receipt-drift`, `markdown-injection`, each either
`reviewed` or `not-applicable` per round. Not checked, repeatedly: the Pashov
pair, waived because nothing in scope is Solidity. Elenchus verdicts:
`unguarded`, null, `passed`, `passed`, null, `guarded`, null, `passed`, null.
Findings `S1-R1-01` low and `S1-R1-02` info on a test runner's file mode and
docstring, fixed in `f1903db1`; `S2-R1-01` medium, a gate sorting a venue set
that raised `TypeError` on a null venue instead of reporting a breached gate,
`S2-R1-02` low, `list()` accepting a mapping's keys as provenance, and
`S2-R1-03` info, an untested empty archive row, all fixed in `b094ff2e`;
`S2-R2-01` medium, a repair that regenerated neither the portable mirror nor
the Horos boundary and would have landed main red, fixed in `a36a3a39`;
`S3-R1-01` medium, a composed coverage note dropping the registry's venue
description, `S3-R1-02` low, a default asserting a route had run, and
`S3-R1-03` low, indexing `routes[0]`, all fixed in `ff45fbf4`; `S4-R1-01`
medium, a test class skipping when Alexandria's demonstration was absent and
turning the run's only end-to-end proof into a silent pass, and `S4-R1-02` low,
a promise overstating one row per venue and route, both fixed in `e2a70493`.
Leads not pursued, all still open: the coverage fields carry no length ceiling;
`gate_2_coverage` trusts `render.load` to have checked its input's shape; the
archive-only unreached note and the silently dropped coverage row named in
`#882`; and the thin ledger citation. Two of its lessons are taken directly
into this run's risk register: `S2-R2-01`, that a repair must re-run the whole
battery rather than the suite it touched, and `S4-R1-01`, that a test which
skips on a missing fixture reports a pass for a capability nobody exercised.

### Elsewhere in Wildcat Labs

Lazarus preserves the finite historical Ethereum state and the exact JSON-RPC
traffic one application test needs, with a fail-closed local replay boundary. It
is the neighbouring specialist and it is not this. Lazarus binds a fixture to
one test; Alexandria binds an interval to a dataset. The root `AGENTS.md`
marketplace boundary states that separation, and this run keeps it: no Lazarus
format, fixture or replay boundary is consumed or produced.

Tabularium's held job, issue `#398`, is Compound v3 Phase 1 built from
Alexandria raw evidence. It is downstream of this one and its mapping is
explicitly not built here.

### Outside the organisation

The Comet source pin, `compound-finance/comet` at
`f766f51583c23acc33b2a7824654ef2029a96804`, supplies `ERC1967Upgrade.sol` for
the `Upgraded(address)` event and the EIP-1967 implementation slot
`0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`,
`CometProxyAdmin.sol` for the deploy-and-upgrade path, and `relations.ts`,
which reads the same slot. `CometExt.version()` returns the constant string `0`
in the pinned source and is not an implementation identity, so an epoch is
bound by runtime code hash instead. EIP-1967 defines the slot; the Ethereum
JSON-RPC specification defines `eth_getLogs`, `eth_getBlockByNumber` and the
`finalized` and `safe` block tags.

## 3. Constraints and non-goals

**Starting ref.** Run branch `fiat/395-resumable-ethereum-usdc-interval-collector`,
cut from `main` at `1c1137898bce9086c34310bd29b5cf8a889f800c`, which is
`origin/main` fast-forwarded and clean at run start.

**Toolchain.** Python 3.14.6 exactly, as `.python-version` records and
`pyproject.toml` pins with `requires-python = "==3.14.*"`. Standard library
only. Alexandria's package version is `0.3.1` across
`plugins/alexandria/.claude-plugin/plugin.json`,
`plugins/alexandria/.codex-plugin/plugin.json` and
`.claude-plugin/marketplace.json`, and `tests/test_version_propagation.py`
binds the three together.

**Ledger.** `alexandria-v0.4.0`, frontier status `open`, frontier revision
`usdc-interval-collector`, frontier digest
`d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff`. This is a
frontier run, so it closes with exactly one new evolution row,
`alexandria-v1.0.0`, whose next job is either a successor with its acceptance
condition or `None -- mature`. The versioning contract, not this study, decides
which; the judgement is made against the evidence at the end of the run.

**Ruled out by the request.** Nothing in the held job was ruled out by the
contributor; the job text is the whole instruction and it was re-read from the
live ledger at run start rather than from issue `#395`, whose own review block
says to do exactly that.

**Ambiguity resolved, and why.** The held job bundles five properties, and
Protasis asks whether a bundle is several topics. It is not decomposed here.
Each property could be built separately, but none of them can be *verified*
separately: epoch discovery without shards has no interval to cover,
reconciliation without a collected interval has nothing to compare, and the
release verification is the only check that any of them happened. The
acceptance condition in the ledger is one release that carries all five, so
cutting one leaves the job unmet rather than smaller. The five become ordered
runbook steps instead, which is where a bundle that shares one deliverable
belongs.

**Non-goals.**

- No mapping. No credit event, position observation or derived release. The
  harvest document assigns that to a separate reviewed mapping and
  Tabularium's `#398` holds it.
- No second market and no second chain. The registry pin's other 27 entries
  are named as gaps in coverage, not collected.
- No full-history harvest. The prototype collects a declared bounded interval.
- No change to `release.py`, the manifest format, or any shipped schema. The
  collector adds schemas; it alters none.
- No signing, no DSSE, no publisher identity. `statement` already draws that
  line and this run does not move it.
- No CI workflow for the Alexandria suite. Issue `#882` carries it and it is
  repository-wide work.
- No live provider run. Assumption 2 states why, and the exit conditions are
  written so that no claim depends on one.

## 4. Design options

The question the record settles is how collected bytes are held between the
transport and `ingest`: what is written when, what a checkpoint contains, what
resume does, and what the release's components end up being. Everything else in
the collector is the same across the three.

### Option A: shard-components

Every preserved request and response is written as its own file and declared as
its own release component; the checkpoint is a shard index. Provenance is at its
simplest, because one component is exactly one JSON-RPC exchange and a consumer
can accept or reject it alone. Its trade is arithmetic: the release contract
allows 128 components, and a 100-shard interval over three evidence classes
needs 607.

### Option B: class-journals

One append-only JSONL journal per evidence class. Each record carries the
request bytes, the response bytes and the shard they belong to. After a shard's
records are flushed and fsynced, the checkpoint records each journal's committed
byte offset; resume truncates every journal back to those offsets and continues
from the next shard. The release declares one component per class. Its trade is
that a consumer accepts a class at a time rather than an exchange at a time, and
that embedding raw JSON inside a JSON envelope costs escaping overhead.

### Option C: request-cache-replay

No checkpoint at all. Request and response bytes go into a content-addressed
cache keyed by the request digest, with an index recording shard, class and both
digests. Resume replays the entire shard plan and skips any request the cache
already holds. Its trade is that resume is proportional to the whole interval
rather than to what is left, and that recovering the plan order is the index's
job rather than the file's.

### What was measured

`.hexaemeron/design/probe.py` stages the same synthetic 100-shard plan through
the same synthetic transport for all three, preserving the same information in
each, and measures a clean collection plus an interrupted-and-resumed one. The
interruption is mid-shard, after a partial write and before its checkpoint.
Timing is the best of three rounds.

| Candidate | Components | Largest component | Resume identical | Collect and resume |
| --- | ---: | ---: | --- | ---: |
| shard-components | 607 | 12,846 B | true | 354 ms |
| class-journals | 10 | 1,394,518 B | true | 190 ms |
| request-cache-replay | 10 | 1,300,728 B | true | 410 ms |

Option A fails the `component-ceiling` gate at 607 against 128 and is removed
before the frontier is computed. Between the survivors, the only comparative
metric is resume cost, where Option B is 2.2 times faster on a 100-shard
fixture and the gap widens with the interval, because Option C re-walks
everything it already has. The record selects `class-journals` under
`unique-frontier`.

Two things this comparison does not establish. It does not establish that
`class-journals` is fastest against a real provider, where transport time
dominates local staging; the metric is deliberately the local cost of resuming,
which is the part the staging shape controls. And it does not establish that
the fixture's response sizes match the market's. They are modelled on a Comet
shard's shape, not measured from one, because no provider was available.

Staging footprint was measured and left out of the record: the spread between
the survivors is 1,634,440 against 1,572,554 bytes, four percent, and it is
escaping overhead rather than a property worth choosing on. The constraint that
binds is the per-component ceiling, which is a gate both survivors pass by more
than a factor of forty.

The closed record is `.hexaemeron/design-evidence.json`, SHA-256
`f093d15016055f60d8fcc28f3895459dbc28ef138c2c64cfb16807a86b1d2e75`. Its five
conformance criteria stay pending with their exact resolvers and stop points:
`epoch-contiguity` at `step:3`, `resume-rewinds-on-reorg` at `step:4`,
`reconciliation-refuses-mismatch` at `step:5`, `release-verifies-offline` at
`step:6`, `demo-reproduces-release-id` at `integration`.

## 5. Risk register seed

The collector's exposure is not Solidity. It takes bytes from a provider nobody
in this repository controls, writes them to disk for a long time, and claims
afterwards that what it wrote is what it saw over an interval it names. Each
concern below is a place that claim can be false while every test still passes.

The three that most deserve the audit loop's time are `torn-shard`,
`silent-truncation` and `coverage-inflation`. A torn shard is the failure this
whole design exists to survive, so a resume that quietly loses a record is
worse than one that refuses. Silent truncation is the provider-side version of
the same thing: `eth_getLogs` responses are capped by result-size limits at
every public endpoint, and a page that came back short without saying so turns
a gap into an assertion of completeness. Coverage inflation is where those two
become a public claim, because `_validate_coverage_against_bytes` checks that a
declared count matches the payload, not that the payload covers the interval.

```risk-register
torn-shard | the staging journals during an interrupted write | a kill between the write and the checkpoint leaves no record that resume keeps, and the resumed release is byte-identical to a clean one
silent-truncation | the provider's response to a bounded range request | a truncated or result-capped page is refused rather than accepted as a complete shard
coverage-inflation | the emitted capture plan's coverage counts and interval | declared record counts and the declared block interval are derived from the preserved bytes, never asserted
reorg-rewind | the boundary hash re-read on resume | a changed boundary hash rewinds to the last matching checkpoint instead of continuing across a fork
epoch-gap | the implementation epoch table over the interval | epochs are contiguous, code-hash-bound and refuse an unknown boundary rather than assuming the current implementation
reconciliation-bias | the comparison of two providers over one interval | a disagreement is recorded as a dispute rather than resolved by majority or by which endpoint answered first
endpoint-leak | the environment variable, request headers and error receipts | no endpoint, credential or header reaches a file, a receipt or a log line
staging-path-escape | the staging and output directories the operator names | absolute paths, traversal and symlinks are refused, and the worktree root is resolved before comparison
unbounded-response | the bytes read from the transport | a response above the component ceiling is refused before it is written, and total staging is bounded
skip-as-pass | the test suite when a fixture is absent | a missing fixture fails rather than skips, so the end-to-end proof cannot report a silent pass
whole-battery-regression | generated mirrors and boundaries after any fix | a repair re-runs the portable Promise Machine check and the Horos boundary, not only the suite it touched
```

## 6. Glossary seeds

- **Shard.** One bounded block range within the interval, the unit a request
  covers and a checkpoint commits.
- **Epoch.** A maximal block range over which the proxy's implementation
  address and its runtime code hash are constant.
- **Boundary block.** The last block of a shard, whose hash the next shard's
  request is checked against.
- **Finality policy.** The named rule that fixed the interval's end: `finalized`,
  `safe`, or a stated confirmation depth. Operator policy, recorded as such.
- **Checkpoint.** Working state naming the next shard, the last accepted block
  and hash, and each journal's committed byte offset. Not release truth.
- **Reconciliation.** The comparison of a completed interval against a second
  provider over the identity tuple the harvest document names.
- **Dispute.** A recorded disagreement between providers. Both responses are
  preserved and the affected interval is marked partial or failed.
- **Error receipt.** The sanitised record of a failed, truncated or disputed
  request, carrying its provider class and status without its endpoint.

## 7. Sources

- `plugins/alexandria/docs/compound-v3-harvest.md`, the production collection
  plan this delivery is measured against.
- `plugins/alexandria/scripts/alexandria_lib/release.py`, the release and
  coverage contract, and its three limits.
- `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py` and
  `scripts/compound_v3_phase0.py`, the method proof and the network boundary
  pattern.
- `plugins/alexandria/scripts/alexandria_lib/compound_registry.py`, the pinned
  registry.
- `plugins/alexandria/schemas/capture-plan-v1.schema.json` and
  `coverage-v1.schema.json`.
- `plugins/alexandria/examples/credit-history-v0/` and
  `examples/compound-v3-phase0-v0/`, the two demonstration shapes.
- `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.synopsis.md`
  and `audit/rounds/fiat-391-unified-live-and-archive-collection.synopsis.md`.
- Issue `#882`, the carried-forward record of the `#391` run.
- Issue `#395`, the held-job filing, whose review block directs a reader to the
  live ledger.
- `plugins/alexandria/skills/alexandria/EVOLUTION.md` and
  `plugins/hexaemeron/skills/VERSIONING.md`.
- `tests/test_marketplace_prose.py`, the prose reconciliation this run owes.
- `compound-finance/comet` at `f766f51583c23acc33b2a7824654ef2029a96804`:
  `contracts/vendor/proxy/ERC1967/ERC1967Upgrade.sol`,
  `contracts/CometProxyAdmin.sol`, `deployments/relations.ts`,
  `contracts/CometExt.sol`.
- EIP-1967, the proxy storage slots. The Ethereum JSON-RPC specification for
  `eth_getLogs`, `eth_getBlockByNumber` and the `finalized` and `safe` tags.

## 8. Signals, and the questions behind them

A long collection runs unattended and the operator is not watching it.
`plugins/hexaemeron/skills/ephoros/SKILL.md`
owns what a signal carries; these are the questions it has to answer here.

1. *How far did it get before it stopped?* The checkpoint answers it without
   the process: it names the next shard, the last accepted block and hash, and
   each journal's committed offset. Step 3 emits it and step 3's tests read it
   back after a kill.
2. *Why did it stop?* Every refusal exits non-zero with one sanitised line
   naming the shard and the reason, and every failed or truncated request also
   leaves an error receipt in the staging tree carrying its provider class and
   status. Steps 3 and 4 emit these.
3. *Did the second provider agree, and about what exactly?* The reconciliation
   receipt records the compared identity tuples, the count that matched, and
   each disputed identity. Step 4 emits it.
4. *What does the finished release actually cover?* The shard receipt and the
   capture plan's coverage carry the contiguous interval, the epochs, the
   record counts derived from the bytes, and every gap. Steps 5 and 6 emit
   them.

No daemon, no metrics endpoint and no telemetry service: this is a command an
operator runs, so its signals are files it leaves behind and its exit status.

## 9. Boundaries, per capability

`plugins/hexaemeron/skills/phylax/SKILL.md`
owns the boundary list and the controls. Four are opened here.

- **The transport.** The collector accepts bytes from a provider it does not
  control. Worth taking: the raw response, unmodified. The control is a byte
  ceiling checked before the write, strict JSON parsing with a node bound
  before the bytes are accepted, no redirect following, an explicit timeout,
  and a refusal for any response that is truncated or carries a JSON-RPC error.
  Step 3.
- **The endpoint and its credential.** Worth taking: nothing. The control is
  that the endpoint arrives only through an environment variable, never reaches
  a file, a receipt, an error message or a log line, and that the capture plan
  names a provider class instead. Phase 0 already draws this line and step 3
  keeps it.
- **The staging and output directories.** The operator names both and a
  previous run may have left something in them. The control is the confinement
  `paths.py` already provides, with the root resolved before comparison so a
  macOS `/var/folders` alias does not refuse a contained path, plus a refusal
  to replace a directory holding a different release. Steps 3 and 5.
- **The fixture provider in tests.** Test fixtures are input too. The control
  is that the fixture transport is injected rather than discovered, that the
  suite asserts no socket is opened on any offline path, and that an absent
  fixture fails rather than skips. Steps 3 and 6.

## 10. The budget, or its absence

One budget, and it is about resuming rather than collecting.
`plugins/hexaemeron/skills/metron/SKILL.md`
owns how it is checked. A complete collection of the 100-shard fixture interval
plus one interrupted-and-resumed collection of the same interval, excluding
transport time, stays under 5,000 ms. The measuring command is
`python3 .hexaemeron/design/probe.py` for the design comparison, and step 3's
own test carries the same measurement forward against the delivered collector.
The selected design measured 190 ms against that budget.

No budget is claimed for a live collection: its cost is the provider's, this
run cannot measure it, and a number nobody measured is worse than none.

## 11. The fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md`
owns the triage order and the guard rule. What stops the run:

- a response that is truncated, oversized, malformed, or carries a JSON-RPC
  error;
- a boundary hash that does not match the previous shard's, before the rewind
  path is entered;
- an implementation epoch boundary whose code hash cannot be bound;
- a coverage count that the preserved bytes do not carry;
- a staging or output path outside its resolved root;
- a reconciliation disagreement, which stops the *claim* rather than the run:
  the interval is recorded partial or failed and preserved either way.

The guard convention: every failure found in implementation or in an audit
round gets a minimal test that fails against the parent commit and passes
against the fix, in the plugin's own suite, and the round records the exact
Elenchus verdict the runner produced. The runner contract for every step is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, report file `.elenchus/alexandria-unittest.json`.

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md`
owns which decisions earn a record and where each lives.

- **The staging shape.** Expensive to reverse once a release exists in it.
  Home: `.hexaemeron/design-evidence.json`, the checked record, plus the design
  section of this study committed under `plugins/alexandria/docs/`.
- **The checkpoint and receipt schemas.** A published schema is a contract with
  whoever reads a release. Home: `plugins/alexandria/schemas/`, indexed in
  `schemas/README.md`, which is where every other Alexandria contract lives.
- **The finality policy.** Operator policy that the harvest document explicitly
  refuses to attribute to Compound. Home: the collector's own document,
  `plugins/alexandria/docs/usdc-interval-collector.md`, and the recorded
  finality class on every capture.
- **The frontier advance.** Home: the one new row in
  `plugins/alexandria/skills/alexandria/EVOLUTION.md`, citing both issue `#395`
  and the committed study.

No separate ADR. The repository keeps ADRs under `docs/decisions/` for
repository-wide decisions; every decision above is Alexandria's own and has a
home inside the plugin already.
