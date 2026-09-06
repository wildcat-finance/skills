# Study: the interval collector run against two live providers

Assuming, unless corrected:

1. The exact interpreter in `.python-version`, 3.14.6, with the standard
   library and `unittest`. Alexandria adds no third-party dependency.
2. Two providers reachable from this machine on 2026-09-06 without any
   credential answer every read the run needs except `trace_filter`:
   Wildcat's staging gateway and the mevblocker relay's public RPC. Both were
   probed during this study with `eth_getBlockByNumber`, `eth_getLogs`,
   `eth_getStorageAt` and `eth_getCode` over the interval named below, and
   they agreed on every block hash and every log count. Their endpoints reach
   the collecting step through the controller's brief and the
   `ALEXANDRIA_COMPOUND_RPC_URL` variable only; no endpoint is written into
   this study, the runbook, a plan, a release, a test or a receipt.
3. No provider reachable without a credential serves `trace_filter`. The
   staging gateway answers `method is not available to public callers`, drpc's
   public tier cannot route it, publicnode gates it behind a personal token,
   and merkle answered a public-tier rate limit to every probe after the first
   two. The plan therefore declares which evidence classes it collects, and
   this run's plan omits `traces` and says so in every coverage gap. Handing
   the run a trace-serving endpoint later changes the plan, not the code.
4. The target is one market and one interval: the Ethereum mainnet Compound v3
   USDC Comet at proxy `0xc3d688b66703497daa19211eedff47f25384cdc3`, blocks
   25,903,935 to 25,905,934 inclusive, 2,000 blocks in four shards of 500. The
   interval was chosen because it contains the proxy's `Upgraded(address)` at
   block 25,904,935, so the epoch table has two epochs and two implementations
   whose code the release must preserve. Every identity in section 4's table
   was observed from both providers during this study; the live step
   re-observes them and pins what it observed, not what this study says.
5. The preserved capture is small enough to commit: the two providers returned
   93 logs in 59,371 bytes over the interval, and the four boundary headers,
   the opening reads and two 18,599-byte runtime code reads add roughly
   250,000 bytes. The staging journals are checked in as a new example; the
   demonstration rebuilds the release from them offline and compares the
   release identifier. Nothing large enough to need a digest-only pointer is
   produced.
6. Live network reads happen in exactly one runbook step, the one whose Exit
   names the two providers. Every other step, every test and both
   demonstrations open no socket, and the suite asserts it.
7. Alexandria's release contract is fixed: `release.py`, the manifest format
   and every shipped schema other than the interval schemas stay unchanged.
   The interval plan and receipt schemas gain fields; the `finalized` scope
   the release now carries is the one `_validate_scope` already accepts.
8. This run produces no Solidity, so the Pashov suite is waived by receipt and
   the phylax, ephoros and hypomnema lints plus the root suite carry the audit
   rounds.

## 1. Problem statement

`usdc_interval.py` collects a bounded Ethereum USDC Comet interval in shards,
resumes after a kill, reconciles a second transport and builds a release that
verifies offline. It has done all of that against injected fixtures only. Three
things follow from never having met a provider, and the ledger's held job names
all three: it has never run against a live provider; it reads each shard's end
block and never the interval's first, so every capture's scope carries finality
class `provider-reported` instead of the `finalized` policy the plan names; and
it preserves no implementation code, so an epoch's `implementation_code_sha256`
is a declared digest nobody can re-derive from the release.

This run closes the three. It is for the operator who wants a real, reproducible
Compound v3 USDC record and for Tabularium, whose Phase 1 mapping consumes
exactly this evidence. The kickoff entry it serves says what the member refuses
without it: describing any capture as a finalized interval, and being sole
evidence under a lender-facing "since block N".

A working prototype means:

- `collect` runs against Wildcat's staging gateway over the declared 2,000-block
  interval, binds the `finalized` boundary, walks four shards, and then reads
  the interval's first block, the EIP-1967 slot and block header at each epoch
  boundary and the runtime code of each implementation, journaling and
  checkpointing those reads like any shard;
- `reconcile` runs the finished interval and the opening reads past the
  mevblocker relay and records `agreed`;
- `build` discovers two code-hash-bound epochs from the preserved bytes alone,
  ships the runtime code as a component the epoch table names by digest, and
  emits every evidence capture with scope finality `finalized` carrying both
  `start_hash` and `end_hash`;
- `check` re-hashes the code bytes from the component and refuses a release
  whose epoch table names a digest the bytes do not carry;
- the preserved journals are checked in and an offline demonstration rebuilds
  the release from them to the pinned identifier with no socket.

**The demo path that proves it**, and the last runbook step:

```bash
python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py verify <directory>
```

`build` reads the checked-in staging tree the live step preserved, runs `build`
and `check` over it into a new directory, and records the summary. `verify`
re-derives the release identifier, the epoch count, the reconciliation status
and the two implementation code digests and compares them with `expected.json`.
Neither opens a socket, and a test asserts it. The synthetic `usdc-interval-v0`
demonstration stays as it is and keeps proving the kill-and-resume path.

Success criteria a command can check:

1. `python3 plugins/alexandria/scripts/usdc_interval.py check <release>` over
   the live release exits 0 and reports `epochs: 2`,
   `reconciliation: agreed`, `shard_statuses: {complete: 4}`.
2. Every evidence capture in the live release's manifest carries
   `scope.finality == "finalized"` and both `scope.interval.start_hash` and
   `scope.interval.end_hash`, and `alexandria.py verify` accepts it.
3. Editing one byte of the `implementation-code` component, or one hex digit
   of an epoch's `implementation_code_sha256`, makes `check` refuse by name.
4. The reconciliation record names the second provider's class, `compared`
   at least 8 and `disputed` empty.
5. The demonstration's `verify` exits 0 and the Alexandria suite runs it under
   a socket denial with zero skips.

## 2. Prior art

### In this repository

`plugins/alexandria/scripts/usdc_interval.py` is the collector this run
extends. `HttpsTransport` at line 80 is the one network path: an HTTPS endpoint
from `ALEXANDRIA_COMPOUND_RPC_URL`, a `Content-Type` header and nothing else,
no redirect, an explicit timeout, a read capped at
`MAX_RAW_COMPONENT_BYTES + 1`. `bind_finality` at 252 reads the plan's policy
tag and refuses unless the returned header's hash and number equal the plan's;
`_boundary_hash` and `_settle_start` at 286 to 327 re-read remembered
boundaries and rewind. `Reconciler` at 360 compares boundary hashes,
transaction order and log identities per shard and never settles a dispute.
`Builder._capture` at 708 writes the comment that this run retires: scope
finality is `provider-reported` and no scope hash is given because the first
block is never read. `_gaps` at 839 names the unread first block on every
evidence component. `check_interval` at 937 requires exactly eight components
and re-derives every shard's record counts from the journals.

`plugins/alexandria/scripts/alexandria_lib/interval.py` holds the plan
validator, which at line 122 requires the plan's evidence classes to equal the
module's fixed `("boundary-blocks", "logs", "traces")`; the `class-journals`
staging with its fsync-then-checkpoint rule and 16-entry rewind trail;
`discover_epochs` at 567, which takes ordered `Upgraded(address)` logs, slot
reads keyed by block, code reads keyed by implementation and block hashes, and
returns epochs carrying `implementation` and `implementation_code_sha256`, the
SHA-256 of the raw runtime bytes; and `validate_epochs` at 658. Nothing in it
opens a socket.

`plugins/alexandria/scripts/alexandria_lib/release.py` accepts scope finality
`finalized` for a `block-range` interval only when `end_hash` is present and
requires `start_hash` and `end_hash` together (`_validate_scope` at 375,
`_validate_optional_hash_pair` at 447). The release contract already admits
what this run will emit; the collector simply never had the start hash to give.

`plugins/alexandria/docs/usdc-interval-study.md` and
`usdc-interval-runbook.md` are the prior run's committed design records. The
runbook's design lock selected `class-journals` and its six steps landed as
pull requests `#1012`, `#1016`, `#1019`, `#1022` and their siblings. The study's
assumption 2 stated that no archive endpoint was reachable and that "every claim
about live behaviour in this run is a claim about that boundary, not about a
provider that answered". This study replaces that assumption with two providers
that answered.

`plugins/alexandria/docs/usdc-interval-collector.md` is the shipped collector
document. Its "Finality is operator policy" and "What this does not establish"
sections state the two gaps this run closes, in the collector's own words, and
are rewritten by the documentation step.

`plugins/alexandria/examples/usdc-interval-v0/` is the synthetic offline
demonstration: `demo.py` with `build` and `verify`, three fixtures, and
`expected.json` pinning release
`sha256:d286ba9f58a2ed6689957a763dfbd45decf54b3b6391db5aff37cf25dcfaa11d`.
Its fixture provider answers `eth_getBlockByNumber`, `eth_getLogs` and
`trace_filter` only, and its `epochs.json` supplies one synthetic slot read and
code read. `tests/test_usdc_interval_demo.py` fails rather than skips when a
fixture is absent. The new example follows the same shape over preserved bytes.

`plugins/alexandria/examples/compound-v3-phase0-v0/` is the method proof: 146
preserved requests against one endpoint, including `eth_getCode`,
`eth_getStorageAt` and a `finalized` header. `compound_phase0.py` names the
proxy and, at lines 37 to 46, the implementation addresses Phase 0 observed.
The two implementations this interval spans,
`0x83d491269720ce925f92c6bf9f66b7a0779a293a` before block 25,904,935 and
`0x63e749153baf1838f63ca22c275370bd2b1ceb15` from it, are newer than Phase 0's
capture and are pinned nowhere in the repository yet.

`plugins/alexandria/skills/alexandria/DEMONSTRATION.md` registers the
`credit-history-v0` record as the plugin's public demonstration and holds the
demo lane's own next job, "Preserve a real Ethereum USDC interval and
demonstrate the collector over it end to end." The record's rules in
`plugins/hexaemeron/skills/DEMONSTRATIONS.md` require `network.policy` `denied`
for a registered public record, so a live capture can never itself be the
registered demonstration; only the offline rebuild over preserved bytes can.
Section 3 states why the registration is left to a follow-up.

`plugins/alexandria/schemas/interval-plan-v1.schema.json` already declares
`evidence_classes` as a unique array of one to sixteen names; only the module
validator pins it to the fixed triple. `interval-receipt-v1.schema.json`
defines the epoch object this run keeps and the shard object it extends with
nothing.

`tests/test_marketplace_prose.py` requires every mutable `marketplace-context`
block in the plugin to carry the same `**Current frontier.**` line as the
landing README, and the README's single next-job line to keep the exact prefix
and suffix it declares. Twenty files under `plugins/alexandria/` carry the
frontier line today. `tests/test_version_propagation.py` binds the delivery
package version `0.5.0` across three manifests. `tests/check-map-v1.json`
routes an Alexandria change to the Alexandria suite and the repository lints.

### Last two merged pull requests touching the target

`#1330`, merged 2026-09-06, "Derive the public surface from the tree it
describes", touched `plugins/alexandria/README.md` and
`skills/alexandria/DEMONSTRATION.md`: it re-derived the registered
demonstration record against the Aave v4 source after a base sync and bound
the root README's front-door card to that record's digest. Its carryover block
names eleven items. Ten concern the front-door checker, the Elenchus runner,
the promise-machine PDF and the run's own controller state, and none touches
the collector; they stay with their filed issues. One does touch Alexandria:
`stale-example-coverage-prose`, filed as issue `#1329`, two sentences in
`examples/credit-history-v0/README.md` that the example's own summary
contradicts. This run does not change `credit-history-v0`, so `#1329` stays
open and is refused here by name: the front-door checker compares the record's
observations with command output rather than with that README, and the fix
belongs to whoever next owns that example's pinned digests.

`#1193`, merged 2026-09-04, "earn proof-backed-state by re-running Lazarus over
an embedded fixture", is the `alexandria-v1.5.0` generation row. It changed
`release.py` to earn `proof-backed-state` at `verify`, added
`proof_backed.py`, and carried nothing forward: its carryover block reads
`none | none | the wish is delivered whole`. Two of its choices bind this run:
`verify` still runs inside `ingest`, so a build that emits a scope
`release.py` refuses fails at build time rather than at check time; and
`check-map-v1.json` now runs the Alexandria suite on a Lazarus change, which
does not affect this run but explains a suite that runs when nothing here
changed.

The `#395` run's last pull request, `#1022`, was read for its own carryover.
It recorded the unread first block and the absent implementation code as the
open frontier rather than as follow-up items, and the ledger's next job is
where that carryover lives. Both are the content of this study.

### Audit record reading

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root and exited zero with every listed record reporting
`committed=match`, so the verified synopsis is the reading view for every
in-scope source. Three in-scope sources exist and there is no
`plugins/alexandria/audit/` directory; the root pair covers only the root
source and none of the three is reached through it.

`audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.synopsis.md`
was read, not its source. Twelve rounds across six steps. Every round logged
the eleven register ids, `torn-shard`, `silent-truncation`,
`coverage-inflation`, `reorg-rewind`, `epoch-gap`, `reconciliation-bias`,
`endpoint-leak`, `staging-path-escape`, `unbounded-response`, `skip-as-pass`
and `whole-battery-regression`, as `reviewed` or `not-applicable`. Not checked
in every round: x-ray, solidity-auditor and fizz, waived because the run ships
no Solidity. Elenchus verdicts: `inconclusive` three times, `guarded` three
times, null six times. Findings, all fixed unless stated: `S1-R1-01` medium, a
symlinked checkpoint read as absent; `S1-R1-02` low, a symlinked journal
raising a bare `FileExistsError`; `S1-R1-03` medium, `record()` unbounded while
`entries()` refused; `S1-R1-04` low, an understated checkpoint record count;
`S1-R1-05` info, an unused regex; `S1-R1-06` medium, an incomplete portable
mirror; `S1-R1-07` high, the mirror's file count over the skills CLI ceiling,
accepted for the run and closed since by `#949`, which moved the payload out of
this repository; `S2-R1-01` medium, an upgrade log's announced implementation
never compared with the slot read; `S2-R1-02` medium, the log's own
`blockHash` never compared with the preserved block; `S2-R1-03` low, a
checksummed code-read key; `S2-R1-04` info, a branch name in the runbook;
`S3-R1-01` high, an error receipt copying a transport's exception text;
`S3-R1-02` medium, the receipts directory accepting a symlink; `S3-R1-03`
medium, the finality bind and boundary re-read raising without a receipt;
`S4-R1-01` medium, reconciliation opening the tree with `resume`; `S4-R1-02`
medium, journal readers capped below the response ceiling; `S4-R1-03` low,
counts zeroed on an unreconciled interval; `S5-R1-01` high, `check` trusting
the receipt's record counts; `S5-R1-02` low, the first-block gap declared on
components that make no chain claim; `S5-R1-03` info, an unread parameter;
`S5-R1-04` medium, step 3's Exit naming an epoch table `collect` never took;
`S5-R1-05` medium, step 5's Exit claiming `check` establishes code-hash
binding when it only checks a digest is declared; `S6-R1-01` medium, an epoch
end hash and a shard end hash for the same block never compared; `S6-R1-02`
info, unused imports; `S6-R1-03` medium, a second payload ceiling, closed with
`S1-R1-07`. Leads not pursued, still open: two upgrade logs in the same block
refuse as unordered; `_topic_address` and `_implementation` carry the same
padding check twice; a caller-supplied transport's exception text still reaches
stderr; `_ask` catches `AlexandriaError` from a transport but not other
exceptions; `committed` and `resume` both validate the checkpoint; `check`
re-derives every count on every run. `S5-R1-05` is the finding this run answers
directly: after it, `check` will re-hash the preserved code and compare, which
is what "code-hash-bound" was claimed to mean.

`audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.synopsis.md`
was read, not its source. Three rounds, one step. Covered throughout:
`subject-binding`, `predicate-fidelity`, `untrusted-release`,
`output-confinement`, `partial-write`, `claim-inflation`, `schema-drift`,
`determinism`, each `reviewed`. Not checked: the waived Pashov pipelines,
DSSE signing, cosign, publisher identity, provider completeness, consensus
finality, canonical-chain proof, network and RPC behaviour, hostile concurrent
writers on the output directory, hosted CI. Elenchus verdicts `passed`,
`guarded`, null. Findings: `S1-R1-01` medium and `S1-R1-02` low, a descriptor
and a fresh report surviving a failed `os.fstat()`, fixed in `eb8dc5b3`;
`S1-R1-03` medium, an absolute report path compared against a resolved root
on macOS, fixed in `bac7e2ff`; `S1-R2-01` medium, a manifest under
Alexandria's control limit producing a statement above Ariadne's cap, fixed in
`775b151c`. Leads not pursued: a hostile writer racing the temporary name; a
directory-descriptor `close()` failure after a replacement; cross-field schema
equalities left to the emitter; non-UTF-8 filenames on macOS. The macOS
`/var/folders` alias in `S1-R1-03` still governs every temporary directory this
run's tests use.

`audit/rounds/fiat-391-unified-live-and-archive-collection.synopsis.md` was
read, not its source. Nine rounds across four steps, mostly Probitas. Covered
across rounds: `coverage-row-collapse`, `unrequested-network`,
`schema-refusal`, `release-id-figures`, `overlap-attribution`,
`gap-double-count`, `demo-receipt-drift`, `markdown-injection`. Not checked,
repeatedly: the Pashov pair. Elenchus verdicts: `unguarded`, null, `passed`,
`passed`, null, `guarded`, null, `passed`, null. Findings `S1-R1-01` low,
`S1-R1-02` info, `S2-R1-01` medium, `S2-R1-02` low, `S2-R1-03` info,
`S2-R2-01` medium, `S3-R1-01` medium, `S3-R1-02` low, `S3-R1-03` low,
`S4-R1-01` medium and `S4-R1-02` low, all fixed in the commits the synopsis
names. Leads not pursued, still open: coverage fields without a length ceiling;
`gate_2_coverage` trusting `render.load`; the archive-only unreached note and
the dropped coverage row in `#882`; the thin ledger citation. Two lessons are
carried into this run's register as before: `S2-R2-01`, a repair re-runs the
whole battery; `S4-R1-01`, a test that skips on a missing fixture is a silent
pass.

### Elsewhere in Wildcat Labs

Lazarus captures the finite historical state one test needs and replays it
behind a fail-closed boundary; Alexandria binds an interval to a dataset. The
root `AGENTS.md` keeps that separation and so does this run: no Lazarus fixture
or replay boundary is consumed or produced, and the preserved journals are
Alexandria staging bytes, not a Lazarus fixture. Tabularium's Compound v3
Phase 1 mapping is downstream and is not built here.

### Outside the organisation

The programme note of 5 September 2026 and the four surveys behind it, held by
the maintainer, fix the bounds this design sits inside: at most 128 components
of 64 MiB each per release, eight components from the shipped collector, every
log of the interval in one component, shards of up to 50,000 blocks and 4,096
shards, a `safe` or `finalized` boundary, checkpoint after fsync, rewind on a
changed hash, and reconciliation on
`(blockHash, transactionHash, logIndex, address, topics, data)`. Its section 8
step 2 is this job verbatim.

`compound-finance/comet` at `f766f51583c23acc33b2a7824654ef2029a96804`
supplies the `Upgraded(address)` event and the EIP-1967 implementation slot
`0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`. The
Ethereum JSON-RPC specification defines `eth_getBlockByNumber`, `eth_getLogs`,
`eth_getStorageAt`, `eth_getCode` and the `finalized` tag.

Provider behaviour observed on 2026-09-06, all reads by JSON-RPC over HTTPS with
no credential, is prior art for the transport design and is recorded here
because it is not written anywhere else:

| Provider | `finalized` header | historical `eth_getStorageAt` and `eth_getCode` | `eth_getLogs` on the proxy | `trace_filter` | Python default User-Agent |
| --- | --- | --- | --- | --- | --- |
| Wildcat staging gateway | yes | yes | yes, bounded range required, 10,000 blocks accepted, 20,000 refused | refused, `not available to public callers` | accepted |
| mevblocker relay | yes | yes | yes, 2,000 blocks accepted | HTTP 406 | HTTP 403 `1010` |
| drpc public tier | yes | yes | refused, `Can't route your request`, at 100, 500, 2,000 and 5,000 blocks | refused, cannot route | HTTP 403 `1010` |
| publicnode | yes | refused, `Archive requests require a personal token` | refused for every range tried, including 100 blocks behind the head | refused, same token gate | HTTP 403 `1010` |
| merkle | yes, once | one slot read answered, then HTTP 429 `1015` | HTTP 429 `1015` | `[]` once, then HTTP 429 `1015` | not tested |

Both chosen providers reported the same finalized block, 25,920,368, at the
same moment, the same hash `0x6651ba0eb4ba8675dcdc62ac00431b34e0032ee7cfc9f81736c2420a805760d5`
for block 25,919,986, and identical hashes and log counts for every block and
shard in section 4's table. Twelve back-to-back header reads on the mevblocker
relay all answered. drpc's `eth_getBlockReceipts` does answer, at 709,641 bytes
for one block of 243 receipts, and is rejected as a reconciliation route in
section 4.

## 3. Constraints and non-goals

**Starting ref.** Run branch
`fiat/1350-alexandria-1-interval-collector-run-against`, cut from `main` at
`f22de68086ad7265869636903554d09cf751e765`. `plugins/alexandria` is
byte-identical between that commit and today's `main`.

**Toolchain.** Python 3.14.6 exactly, standard library only. Alexandria's
delivery package is `0.5.0` in `plugins/alexandria/.claude-plugin/plugin.json`,
`plugins/alexandria/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`
and `DELIVERY_PACKAGE_VERSIONS` in `tests/test_version_propagation.py`; this
run advances it to `0.6.0`. `SKILL.md` frontmatter states `1.5.0`.

**Ledger.** `alexandria-v1.5.0`, status `open`, revision
`usdc-interval-live-boundaries`, frontier digest
`5e225140ccbe4328e07e733ec28f972ff42760f88685109d05a1acd626837372`. This is a
frontier run: it closes with one new row on the `evolution` axis, whose label
the versioning contract's arithmetic makes `alexandria-v2.5.0`, with a new
revision, a recomputed digest, and a next job that is either an open successor
with its acceptance condition or `None -- mature`, judged at the end against
the evidence. The row cites issue `#1350` and the committed study. The
`SOURCES.md` refresh the versioning contract names runs after the ledger row
and before the integration merge, through the maintainer-held tool; nobody
edits `SOURCES.md` by hand.

**Repository rules the runbook inherits.** Any tracked-file edit changes the
byte counts `HorosCensusCurrencyTests` checks, so every commit is preceded by
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and
`... scan . --census --write`. The commit gate in `.githooks` compares the
staged tree with the tree the root suite last passed on. `DEMONSTRATION.md`
pins source digests and is left alone by this run. The public front door
(`README.md`, `scripts/check_public_front_door.py`) refuses an unmarked
topology count; this run adds an example, not a plugin or skill, and marks
nothing.

**Ruled out by the request.** Nothing. The held job was re-read from the live
ledger. The kickoff entry adds the refusals the member owes without it, which
become success criteria 2 and 4.

**Ambiguities resolved, and why.**

- *Traces.* The job says "two live providers" and the plan validator says
  three evidence classes. No reachable provider serves `trace_filter`
  (assumption 3). This is an absence, not an ambiguity in the request, so it
  is resolved rather than asked: the plan declares its evidence classes, this
  run's plan declares `boundary-blocks` and `logs`, and every evidence
  component's coverage names `traces` as an uncollected class with the
  reason. The `trace-mandatory` candidate in the design record carries this
  as a failed gate rather than as prose. If the maintainer supplies a
  trace-serving endpoint before the live step, the plan adds `traces` and the
  runbook step's Exit gains one more journal; no code changes.
- *Which providers.* Primary is Wildcat's staging gateway: it answered every
  needed read at 90 to 400 ms, accepts bounded `eth_getLogs` ranges of at
  least 10,000 blocks, and answered without a token. Second transport is the
  mevblocker relay: it answered every needed read, agreed with the primary on
  every identity, and survived twelve back-to-back reads. drpc cannot answer
  `eth_getLogs` on its public tier, publicnode gates every historical read
  behind a token, and merkle rate-limited every probe after the first two.
  The release records provider classes, not operators: the plan's
  `provider.class` and the reconciliation's `provider_class` are the strings
  `archive gateway, public tier, no trace methods` and
  `public relay endpoint, archive logs and state, no trace methods`.
- *The interval.* A genesis sweep is not the point. The 2,000-block interval
  in assumption 4 was chosen because it straddles the proxy's most recent
  upgrade, so the run exercises two epochs, two slot reads, two code reads and
  a scope whose start and end hashes come from different implementations'
  reigns. Its 93 logs and four boundary headers fit in one commit.
- *How the first block is read.* By the collector itself, in an opening phase
  after the shard loop, journaled and checkpointed like a shard, and reconciled
  like one. The design record settles this against three other constructions.
- *Pinning a `finalized` boundary.* `bind_finality` today reads the
  `finalized` tag and refuses unless its hash equals the plan's. The tag moves
  every two epochs, so a plan written before the run and a resume after a
  pause both refuse. The rebind semantic this run adopts: read the plan's
  boundary block by number and require its hash to equal the plan's, then read
  the `finalized` tag and require its number to be at or above the plan's
  boundary. A plan is then stable for as long as its boundary block stays on
  the chain, which is what `finalized` promises.
- *Headers a provider requires.* Two of the five probed providers answer HTTP
  403 to Python's default `User-Agent`. The transport sends a constant
  `User-Agent: alexandria-usdc-interval/<package version>` beside the existing
  `Content-Type`. No header comes from the environment, so no header can carry
  a credential; a provider that requires one is out of scope.

**Non-goals.**

- No mapping, no credit event, no position observation. Tabularium's Phase 1.
- No second market, no second chain, no full-history harvest.
- No traces in the live release. Stated above and in every coverage gap.
- No credential support in the transport. A bearer token would be a second
  secret beside the endpoint and neither chosen provider needs one.
- No retry loop. A refused response leaves a receipt and a non-zero exit, as
  today; the operator reruns and the checkpoint resumes. A hidden retry would
  turn a rate limit into a silent delay.
- No change to `release.py`, the manifest format, or any schema outside
  `interval-plan-v1` and `interval-receipt-v1`.
- No registration of the live example as the plugin's public demonstration
  record and no front-door card change. Both re-derive a root `README.md`
  claim through `scripts/demonstrations.py` and the front-door checker, which
  is the ask-first tier. The demo lane's next job in `DEMONSTRATION.md` stays
  as written; the example this run ships is what that job will register.
- No fix to `#1329`, which belongs to `credit-history-v0`.
- No CI workflow for the Alexandria suite. Still `#882`'s repository-wide work.

## 4. Design options

The question the record settles is where the interval's opening reads live:
who reads the first block, the boundary slots and headers and each
implementation's runtime code, how those bytes are journaled and reconciled,
and how the release binds them. Everything else, the plan-declared evidence
classes, the finality rebind, the constant `User-Agent`, the code component
and the offline re-hash, is common to every candidate that survives.

### Option A: opening-reads-in-collect

`collect` gains an opening phase after the shard loop. It scans the staged
logs for `Upgraded(address)` records, then reads through the same transport,
in plan order: the header of the interval's first block, the EIP-1967 slot at
the first block and at each upgrade block, the header at each upgrade block
and at the block before it, and `eth_getCode` for each implementation at the
block its epoch opens. Each read is journaled under a fourth evidence class,
`epoch-evidence`, with request identifiers derived from a virtual shard index
past the plan's last, and the checkpoint commits it like a shard. `reconcile`
compares the opening reads too: the first block's hash, each slot word and
each code digest. `build` calls `discover_epochs` over the journal, writes
the code reads as an `implementation-code` component keyed by implementation
address, names that component's digest from the epoch table, and emits
`finalized` scopes with both hashes. `check` re-hashes the bytes. Its trade is
that `collect` does more after the last shard, so a kill in the opening phase
resumes into it rather than into a shard, and the checkpoint has to say so.

### Option B: epochs-subcommand

The same reads and journal, run by a third network command, `epochs`, between
`collect` and `reconcile`. `collect` is untouched. Its trade is a third socket
in the operator's hands and a third place a run can be left half-done; a
release built from a tree whose `epochs` never ran has to refuse rather than
fall back to operator evidence.

### Option C: operator-supplied-evidence

The shipped shape plus a code file: the operator reads the first block, the
slots and the code out of band and hands `build` an epoch table and the code
bytes; the release preserves and re-hashes the code. Its trade is that the
first block's hash and the code bytes are bound to nothing the collector
asked: the scope's `start_hash` would be the operator's word.

### Option D: trace-mandatory

Option A with the three evidence classes kept fixed. Its trade is that the
live run needs a `trace_filter` provider, and none is reachable without a
credential.

### What was measured

`.hexaemeron/design/build_design_evidence.py` reads each candidate's declared
artefact under `.hexaemeron/design/candidates/` and writes one report per cell,
so the record regenerates byte for byte. Five selection gates and two
comparative metrics:

| Candidate | start hash from a collector read | code read journaled | code re-hashed offline | reachable provider pair | resume-safe after a kill | network commands | new release components |
| --- | --- | --- | --- | --- | --- | ---: | ---: |
| opening-reads-in-collect | pass | pass | pass | pass | pass | 2 | 2 |
| epochs-subcommand | pass | pass | pass | pass | pass | 3 | 2 |
| operator-supplied-evidence | fail | fail | pass | pass | fail | 2 | 1 |
| trace-mandatory | pass | pass | pass | fail | pass | 2 | 2 |

Options C and D fail a selection gate and are removed before the frontier is
computed. Between the survivors, Option B costs one more network command for
the same component count, so Option A dominates it and the record selects
`opening-reads-in-collect` under `unique-frontier`.

What the comparison does not establish: it does not measure the opening phase's
wall clock against a provider, which section 10 leaves to the live step, and it
does not establish that Option A's resume-into-opening-phase path is correct,
which is the `opening-reads-resumable` conformance gate at step 3.

The closed record is `.hexaemeron/design-evidence.json`, SHA-256
`6af1a6bc04f8d019005d52a7ccc648767c48933de54f9bec82d0a244dfc37a8d`, and the
design-lock check exits zero against it. Its six conformance criteria stay
pending with exact resolvers and stop points:
`finality-rebinds-after-tag-advance` at `step:2`, `opening-reads-resumable`
at `step:3`, `scope-binds-both-hashes` and
`code-hash-rechecked-from-component` at `step:4`, `live-interval-reconciled`
at `step:5`, `demo-reproduces-live-release-id` at `integration`. Each is
produced by `python3 .hexaemeron/design/conformance.py <criterion>`, which
the scaffolding step creates.

### The interval, as observed from both providers

| Block | Role | Hash |
| --- | --- | --- |
| 25,903,935 | interval start, epoch 1 opens | `0xa4e35dad60b77815249c12cf22ad83056f2ad041ef9b6340dee03e83502d70f0` |
| 25,904,934 | epoch 1 closes, shard 1 ends | `0x9475b3665bc9ec6fbb9fa0f7739727af8ac212d93cce1788c1c494bb3aff20c2` |
| 25,904,935 | `Upgraded(address)` in transaction `0xd6cfe9b49e659649961f350721ea52b42107293e4b0eed2671259d7b328d33f3`, log index 524; epoch 2 opens | `0x37843adea4f9f24b07c4c2ae5b47bb30936aefae6718136eae13d278d7fa40f9` |
| 25,905,934 | interval end, shard 3 ends | `0xc0ac604f5eaf0b78ee147ed3cec4f5c5ab1f7d66d1607266cbf343d7bdc959bd` |
| 25,919,986 | finality boundary the plan pins | `0x6651ba0eb4ba8675dcdc62ac00431b34e0032ee7cfc9f81736c2420a805760d5` |

Shard log counts, both providers: 47, 25, 6, 15. Slot at 25,903,935 holds
`0x83d491269720ce925f92c6bf9f66b7a0779a293a`; at 25,904,935 it holds
`0x63e749153baf1838f63ca22c275370bd2b1ceb15`. Runtime code: 18,599 bytes for
each, SHA-256
`93ac04f8ffb0962157af92ee7cf7c1583937d013bde1b6d592ec2a726d624b79` for the
first and
`b942614560ef7218a52173cc501ce9198f74a558348edf957cda62a218aa20fe` for the
second; the second implementation had no code at block 25,904,934. These
observations bound the live step's expectations; the step pins what it sees.

## 5. Risk register seed

The exposure has moved. The prior run's concerns were about a collector that
never met a provider; this run's are about the first bytes from real providers
becoming a public claim of `finalized` and of code-hash binding. The three that
most deserve the audit loop are `finality-tag-drift`, because a plan pinned to
a moving tag is a run that refuses on resume; `code-digest-rebind`, because a
release whose epoch table and code component can disagree is the claim this
run exists to make checkable; and `preserved-bytes-identity`, because the
checked-in journals are the only evidence anyone will ever have that the live
run happened as described.

```risk-register
finality-tag-drift | the finality bind when the finalized tag has moved past the plan's boundary | the plan's boundary block is read by number and its hash compared, the current finalized number must be at or above it, and a plan whose boundary left the chain refuses by name
start-hash-source | the scope's start_hash on every evidence capture | it equals the hash in the collector's own preserved first-block read, never a value copied from the epoch table or supplied by the operator
code-digest-rebind | the epoch table's implementation_code_sha256 against the implementation-code component | check re-hashes the component's bytes and refuses a digest they do not carry, and refuses an implementation the component lacks
opening-phase-resume | the checkpoint after the last shard and before the opening reads are committed | a kill in the opening phase resumes into it, re-reads nothing committed and leaves journals byte-identical to a clean run
traces-omission-declared | a plan whose evidence classes omit traces | every evidence component's coverage names the uncollected class and its reason, and check refuses a release whose plan and journals disagree about the classes
header-leak | the request headers the transport sends | the User-Agent is a constant built from the package version, no header value comes from the environment, and no header reaches a file, receipt or message
endpoint-leak | the environment variable, error receipts, plan, release and committed example | no endpoint or credential reaches a file, a receipt, a test, a document or a log line, and the provider class strings carry no host
rate-limit-refusal | an HTTP 403, 429 or JSON-RPC error from either provider | it becomes an error receipt and a non-zero exit with no retry, and the resumed run continues from the checkpoint
opening-reads-reconciled | the second transport's answers for the first block, the slots and the code | a disagreement is recorded as a dispute with both byte sets kept and is never settled by either provider
preserved-bytes-identity | the checked-in staging tree of the live capture | the offline demonstration rebuilds the release to the identifier the live step pinned, and a changed journal byte changes the identifier
silent-truncation | the provider's response to a bounded range request | a page at the declared limit or a truncated envelope is refused rather than accepted as a complete shard
live-reads-confined | every step, test and demonstration other than the live step | no socket is opened, asserted by the suite's socket denial, and the live step's Exit names the reads it makes
skip-as-pass | the test suite when a preserved fixture is absent | a missing journal, plan or expectation fails rather than skips
whole-battery-regression | generated boundaries and censuses after any fix | a repair re-runs the Horos scan, the census, the lints and both suites, not only the test it touched
```

## 6. Glossary seeds

- **Opening reads.** The reads made after the shard loop that bind the
  interval's start and its epochs: the first block's header, the slot and
  header at each epoch boundary, and each implementation's runtime code.
- **Epoch evidence.** The journal class holding the opening reads, committed
  by the checkpoint like a shard and reconciled like one.
- **Implementation code.** The release component holding each implementation's
  runtime bytes, keyed by address, whose digest the epoch table names.
- **Finality rebind.** Reading the plan's boundary block by number, comparing
  its hash, and requiring the current `finalized` number to be at or above it.
- **Provider class.** The bounded string a plan and a reconciliation record
  carry instead of an operator or a host.
- **Declared evidence classes.** The subset of `boundary-blocks`, `logs` and
  `traces` a plan collects; an omitted class is a named coverage gap.
- **Live step.** The one runbook step whose Exit names network reads.
- **Preserved capture.** The live step's staging tree, checked in as an example
  and rebuilt offline by the demonstration.

## 7. Sources

- `plugins/alexandria/scripts/usdc_interval.py`, lines 80, 252, 286 to 327,
  360, 708, 839 and 937 as cited in section 2.
- `plugins/alexandria/scripts/alexandria_lib/interval.py`, lines 105, 122,
  567 and 658; `alexandria_lib/release.py`, lines 43, 375 and 447;
  `alexandria_lib/compound_phase0.py`, lines 29 to 46.
- `plugins/alexandria/docs/usdc-interval-study.md`,
  `usdc-interval-runbook.md`, `usdc-interval-collector.md` and
  `compound-v3-harvest.md`.
- `plugins/alexandria/examples/usdc-interval-v0/` and
  `examples/compound-v3-phase0-v0/`.
- `plugins/alexandria/schemas/interval-plan-v1.schema.json` and
  `interval-receipt-v1.schema.json`.
- `plugins/alexandria/skills/alexandria/EVOLUTION.md`,
  `DEMONSTRATION.md`, `plugins/hexaemeron/skills/VERSIONING.md` and
  `plugins/hexaemeron/skills/DEMONSTRATIONS.md`.
- `plugins/alexandria/AGENTS.md` and the root `AGENTS.md`.
- `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.synopsis.md`,
  `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.synopsis.md`
  and `audit/rounds/fiat-391-unified-live-and-archive-collection.synopsis.md`.
- Pull requests `#1330` and `#1193`; issues `#1350`, `#1329`, `#882`.
- `tests/test_marketplace_prose.py`, `tests/test_version_propagation.py`,
  `tests/check-map-v1.json`, `.githooks/pre-commit`.
- The programme note of 5 September 2026 and its four surveys, held by the
  maintainer.
- `compound-finance/comet` at `f766f51583c23acc33b2a7824654ef2029a96804`;
  EIP-1967; the Ethereum JSON-RPC specification.
- The provider probes of 2026-09-06 recorded in section 2's table, made from
  this machine with no credential.

## 8. Signals, and the questions behind them

The live step runs unattended for its duration and the collector is a command
an operator reruns. `plugins/hexaemeron/skills/ephoros/SKILL.md` owns what a
signal carries; these are the questions.

1. *Did it finish the shards, and did it finish the opening reads?* The
   checkpoint answers both without the process: it names the next shard, and
   after the last shard it names which opening reads are committed. The
   opening-phase step emits it and its tests read it back after a kill.
2. *Why did it stop?* One sanitised non-zero line on stderr naming the shard
   or the opening read and the reason, and an error receipt carrying the
   provider class, the code and the unresolved range or read. A rate limit is
   a receipt with its HTTP status, not a retry.
3. *Did the second provider agree about the opening reads as well as the
   shards?* The reconciliation record's `compared`, `matched` and `disputed`
   now count the first block's hash, each slot word and each code digest, with
   their kinds named.
4. *What does the release claim about finality and code?* Every evidence
   capture's scope carries `finalized` and both hashes, the epoch table names
   the code component's digest, and `check` prints the epoch count and the
   re-hashed digests.

No daemon and no telemetry: the signals are the files a run leaves behind and
its exit status.

## 9. Boundaries, per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` owns the boundary list and the
controls. Five are open here, and the audit loop was told to look hardest at
the first two.

- **The two transports.** Real providers now answer. Worth taking: their raw
  responses, unmodified. Controls: the existing byte ceiling before the write,
  bounded strict parsing, no redirect, an explicit timeout, refusal of a
  JSON-RPC error, a truncated envelope or a page at the declared limit; plus
  the constant `User-Agent`, whose value is built from the package version and
  never from the environment. A 403 or 429 is a receipt and an exit.
- **The endpoint and its credential.** Worth taking: nothing. Controls: the
  endpoint arrives only through `ALEXANDRIA_COMPOUND_RPC_URL`, reaches no file,
  receipt, message, test or document, and the plan and reconciliation record
  carry provider classes that name no host. No second environment variable and
  no `Authorization` header exist to leak.
- **The live step's network exit.** Worth taking: a step that opens a socket
  it did not declare. Control: exactly one runbook step's Exit names the reads
  it makes; every other step, both demonstrations and every test run under the
  suite's socket denial with zero skips.
- **The preserved capture as test input.** The checked-in journals are input
  to `build`, `check` and the demonstration. Controls: journal records are
  shape-checked before they are believed; `check` re-derives counts and code
  digests from bytes; a missing or edited file fails rather than skips.
- **The staging and output directories.** Unchanged from the prior run: the
  confinement `paths.py` provides, roots resolved before comparison, refusal
  to replace a different release.

## 10. The budget, or its absence

Two budgets. `plugins/hexaemeron/skills/metron/SKILL.md` owns how each is
checked.

The live step's `collect` and `reconcile` together, over the 2,000-block
interval against the two named providers, finish inside 120,000 ms of wall
clock. The figure comes from the probes: 24 reads at 90 to 400 ms each is
under 10,000 ms, and the budget leaves room for a provider ten times slower
without a retry. The measuring command is
`python3 .hexaemeron/design/conformance.py live-interval-reconciled`, which
wraps both commands and records elapsed milliseconds in its report.

The prior run's offline budget carries forward unchanged: a complete
collection of the synthetic fixture plus one interrupted-and-resumed collection
stays under 5,000 ms, measured by the existing test in
`plugins/alexandria/tests/test_usdc_interval.py`. The opening phase adds reads
to that path and the same test re-measures it.

No budget is claimed for the offline rebuild of the live release or for
`check`: each reads under 300 KB.

## 11. The fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` owns the triage order and the
guard rule. What stops the run:

- a plan boundary block whose hash the provider no longer reports, or a
  `finalized` number below the plan's boundary;
- a response that is truncated, oversized, malformed, rate-limited, or carries
  a JSON-RPC error, at any shard or opening read;
- a slot read that is not a left-padded address, a zero address, an empty or
  non-hex code read, or an upgrade log whose announced implementation or block
  hash disagrees with the preserved reads;
- an epoch table whose code digest the `implementation-code` component does
  not carry, or an implementation the component lacks;
- a plan and journals that disagree about the declared evidence classes;
- a scope with one boundary hash and not the other;
- a reconciliation disagreement, which stops the claim rather than the run:
  the shard or opening read is recorded disputed and both byte sets are kept.

The guard convention is the prior run's: every failure found in
implementation or in an audit round gets a minimal test that fails against the
parent commit and passes against the fix, in the plugin's own suite, and the
round records the exact Elenchus verdict the runner produced. The runner
contract for every step is
`python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, report file `.elenchus/alexandria-unittest.json`.

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which decisions earn a
record and where each lives.

- **Where the opening reads live.** Expensive to reverse once a live release
  carries an `epoch-evidence` journal. Home: `.hexaemeron/design-evidence.json`
  and section 4 of this study, committed under `plugins/alexandria/docs/`.
- **Plan-declared evidence classes.** A published plan format is a contract
  with every later plan. Home: `plugins/alexandria/schemas/interval-plan-v1.schema.json`,
  its entry in `schemas/README.md`, and the collector document.
- **The finality rebind.** Changes what a `finalized` plan promises. Home: the
  collector document's "Finality is operator policy" section, rewritten, and
  the plan schema's description of the boundary fields.
- **The constant User-Agent and the refusal of credential headers.** A
  transport property a provider's policy depends on. Home: the collector
  document and `plugins/alexandria/AGENTS.md`'s network paragraph.
- **Provider classes, not operators, in the release.** Home: the collector
  document, beside the endpoint rule it extends.
- **The preserved live interval as an example.** Once cited, its identifier is
  permanent. Home: `plugins/alexandria/examples/usdc-interval-live-v0/README.md`
  and `expected.json`.
- **The frontier advance.** Home: the one new row in
  `plugins/alexandria/skills/alexandria/EVOLUTION.md`, citing issue `#1350`
  and the committed study.

No separate ADR. `docs/decisions/` holds repository-wide decisions; every
decision above is Alexandria's own and has a home inside the plugin.
