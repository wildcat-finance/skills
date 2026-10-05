# Aave V3 Ethereum main-market interval capture

Topic: register the Aave V3 Ethereum main market as an Alexandria interval
venue, so its evidenced interval can be collected, reconciled, built and checked
through the same four commands the Compound and Wildcat captures use, then
collect, reconcile and preserve that interval the way #1731 did for Wildcat.

Task issue: https://github.com/wildcat-finance/skills/issues/1872

Starting ref: `d162d0952782f09659370b6a554c9cd4511b8db9` on `main`, synced with
`origin` on 2026-09-23. Every path, line and digest below is read at that commit
unless it says otherwise. Run branch: `fiat/1872-aave-v3-ethereum-interval-capture`.

## Assumptions

Proceeding on these unless corrected.

1. Python 3.14.6, the interpreter in `.python-version`, with stdlib `unittest`.
   No third-party dependency is added.
2. This is not a frontier run. Alexandria's held
   `transaction-index-reconciliation` job stays held, reconciliation's log
   comparison is not changed, and the delivery is a generation bump on the
   Alexandria ledger. Every step that touches `plugins/alexandria` owes its own
   package version rise over its base.
3. The security suite is waived: the run ships no Solidity and no Foundry or
   Hardhat project.
4. Scope is Ethereum mainnet only, under the 2026-09-23 ruling recorded in
   `docs/kickoff/1359/evidence/scope-ruling-1591.json`. Other chains, Aave V2
   and V4, and the Ethereum Horizon, Lido and EtherFi markets are named
   exclusions.
5. The merged `aave-v3` row of `docs/kickoff/1359/targets.json` and its three
   `-1591` evidence files are this run's source for the market, the interval
   start, the 22 listed contracts and the 356-subject set digest. The full
   records behind that row are held outside this repository, are to hand, and
   are bound by SHA-256 and byte count in the row itself. The Aave registry is
   generated from them and then checked against the in-repository row.
6. On 2026-09-23 the maintainer, Dr Laurence E. Day, ruled that every open
   scope question in this run resolves to whatever matches how the Wildcat V1
   and V2 captures were done in #1731 and pull request 1838. That covers the
   public and private split, which production evidence the run produces and
   where it lives, release and manifest shape, the reconciliation provider
   arrangement, the offline rebuild demonstration, the proof document,
   carryover handling and step structure. The study departs from that precedent
   only where Aave's contracts or volume force it, and item 3 names each
   departure with its evidence. So, as #1731 did, the run collects the
   production interval itself from the local archive node, reconciles it
   against the hosted second transport, keeps the staging trees outside this
   repository and commits their plans, manifests, rebuild records and pins.
   Endpoint credentials stay in the environment, and shared-store custody stays
   with #1373, as it did for Wildcat.
7. The Wildcat V1 and V2 captures are internal-only. The `public` and
   `permitted` component classes every interval release carries are the
   Builder's fixed labels at `plugins/alexandria/scripts/usdc_interval.py:2407`
   and `:2411`. They are not an export decision for Wildcat and would not be one
   for Aave.
8. The local archive node is read, never upgraded, restarted or reconfigured.
   The only reads this study made are listed in item 3 with their results.

Assumptions 5 and 6 change the design. Assumption 5 is why the registry can be
committed and checked without the full records in the tree. Assumption 6 is why
the runbook has a production collection step, as #1731 had two, rather than
handing the capture to a later issue.

## 1. Problem statement, user, and the proving path

The interval collector dispatches a plan through
`plugins/alexandria/scripts/alexandria_lib/venues/__init__.py`, which registers
`compound-v3`, `wildcat-v1` and `wildcat-v2` and nothing else. Three things stop
an Aave V3 capture today.

No venue. A plan naming `aave-v3` refuses by name, because no module owns that
venue's registry pin, subject set, epoch model or gaps.

The epoch model. Wildcat's model is `immutable-code`, and Compound's is one
EIP-1967 proxy. The Aave estate is neither: 172 of its 356 subjects are
`InitializableImmutableAdminUpgradeabilityProxy` instances (the Pool, the
PoolConfigurator and 170 reserve token proxies), and the other 184 are
implementations, strategies, libraries, the AddressesProvider and the
ACLManager, none of them a proxy. The shared position walk also refuses every
ordinary log a proxy emits inside its own upgrade transaction, at
`plugins/alexandria/scripts/alexandria_lib/interval.py:1005-1008`. Aave upgrades
its tokens with `upgradeToAndCall`, which emits `Upgraded` and then runs the new
implementation's `initialize`, so the refusal fires on real Aave history. The
receipt of transaction
`0x6f45f51fa5dd0246298f2e6284c43e0c57ef5e6b646ee1dfcd67f3f4f11dacd9` at block
22,839,362 carries 433 logs; 98 subjects are upgraded in it, every one of the 98
emits an ordinary log after its own `Upgraded`, and 2 also emit one before it.
Under today's rule that single transaction refuses the whole capture.

The volume. The interval runs from block 16,291,071 to 26,022,093, which is
9,731,023 blocks. The sample in item 3 puts its logs at about 19.6 million
records and 14.3 GB of response bytes, and its targeted traces at about 3.33
million transactions and 48.1 GB. One existing-format release holds at most
128 components of 64 MiB each, 8,589,934,592 bytes, so the capture cannot be one
release under the format this run inherits.

**Who this is for.** The capture maintainer, who authorises the collection and
keeps the staging bytes; issue
https://github.com/wildcat-finance/skills/issues/1373, which takes this RPC
capture as its input larger than 8 GiB; and Tabularium's later Aave mapping at
https://github.com/wildcat-finance/skills/issues/1395, which consumes
preserved bytes and is not built here.

**What a working prototype means here.** The same thing #1731 meant for each
Wildcat estate, with one release per segment instead of one per estate: an
`aave-v3` plan builds and checks through the existing CLI, the named refusals
fire, every segment of the ruled interval is collected from the local archive
node and reconciled against the second transport, every segment release
rebuilds offline from its preserved staging tree to its committed identifier,
and the Compound and Wildcat identities do not move.

**Success criteria.** Each is a command, run from the repository root. `<plan>`,
`<staging>`, `<registry>`, `<timestamp>` and `<output>` are the arguments the
owning step supplies.

1. A fixture `aave-v3` plan builds and checks.
   `python3 plugins/alexandria/scripts/usdc_interval.py build --plan <plan> --staging <staging> --registry <registry> --created-at <timestamp> --output <output>`
   prints a release identifier and
   `python3 plugins/alexandria/scripts/usdc_interval.py check <output>` exits 0.
2. The committed Aave registry reproduces the merged row: its 356 lowercase
   addresses hash to
   `289bbdf765e2e66f335f46706269dfbcc63600108d0ef5eb22ba814ecbcf8d64` under the
   form the row records, its role counts equal the row's `by_role`, and each of
   the 22 listed contracts matches the row's address, role, code length and code
   keccak.
3. Per-subject epochs derive from preserved evidence: a proxy created inside the
   interval opens at its creation block with the implementation its slot holds
   there; each `Upgraded` from that proxy opens a new epoch at its own block,
   transaction index and log index; an ordinary log in the upgrade transaction is
   owned by position; a subject created before the interval start opens at the
   start; an immutable subject has one epoch.
4. These refuse with exit 1 and install no release: a wrong chain, a wrong Pool
   or AddressesProvider, a changed registry pin, a changed source row, an
   upgrade in a subject's opening block, two upgrades of one subject in one
   block, a slot read that disagrees with the announced implementation, an
   implementation the registry does not record for that subject, a foreign
   emitter, an incomplete page, a missing or corrupt journal and a changed
   boundary hash.
5. A provider failure leaves a structured receipt and the interval
   `unreconciled`; a provider disagreement marks the shard disputed and keeps
   both providers' bytes; an interrupted collection resumes to byte-identical
   journals.
6. A second provider that differs from the first only in one log's
   `transactionIndex` still records `agreed`, the release says in its own
   coverage that agreement excludes transaction position, and `check` refuses a
   release that omits that sentence.
7. No bearer credential or endpoint appears in any journal, component, receipt
   or error string.
8. The segment table tiles blocks 16,291,071 to 26,022,093 with contiguous
   plans, each plan validates, each plan digest is pinned in reviewed code, and
   each segment's recorded estimate fits 40 component ranges per shard class at
   48 MiB and 128 components in all.
9. The preflight record counts every sampled window and every traced
   transaction, and the chosen shard width, split and concurrency derive from it.
10. Every segment in the table has a counted result or an explicit gap for
    every planned shard and evidence class, a reconciliation naming both
    providers' classes, a committed staging manifest binding its archive's
    SHA-256 and length and every staged file, and a rebuild record showing that
    a fresh extraction of that archive rebuilt the committed release identifier
    with Python sockets denied, then passed `check` and `verify`. Every
    component and journal is at most 67,108,864 bytes.
11. The Compound identifiers
    `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32` and
    `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`
    still rebuild, and both Wildcat examples' `verify-preserved` still pass
    against their committed pins for
    `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`
    and `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`.
12. The repository stays green:
    `python3 scripts/run_checks.py --base fiat/1872-aave-v3-ethereum-interval-capture --scope root --scope alexandria --format json`
    exits 0 at every step's exit.

**Proving demo path.** In the shape of `wildcat-v2-interval-v0` and
`wildcat-estates-interval-v0`: `plugins/alexandria/examples/aave-v3-interval-v0/`
commits the registry, the segment table, each segment's plan, staging manifest,
rebuild record and `expected.json`, and a `demo.py` whose `build` and `verify`
rebuild every segment release from the unpacked staging trees an environment
variable names, with Python socket construction denied, and refuse by name when
it is unset. Its `verify-preserved` needs neither the staging trees nor the
network and checks the committed metadata against the pins, returning
`rebuild_performed: false`. The constructed-fixture path of criteria 1 and 3 to
7 runs in the Alexandria suite, as the Wildcat fixtures do.
`plugins/alexandria/docs/aave-v3-interval/proof.md` records the executed
criteria in the table form `docs/wildcat-interval/proof.md` uses.

## 2. Prior art

### What #1591 landed, and what it does and does not establish

Issue https://github.com/wildcat-finance/skills/issues/1591 closed through pull
request https://github.com/wildcat-finance/skills/pull/1875, merged as
`97e49ce736fa8762eb2279dac3a61a99c9960e36` on 2026-09-23 with its content
commit `5d3af17aa1c4f249cb9e7f058b99def0575320c2`. The issue body of #1872 was
written while #1591 was open and says the Aave source row is blocked on it. That
is no longer true: this run consumes the landed slice.

Established in repository bytes:

- The `aave-v3` row is `resolved`, scoped by the ruling to the main market:
  Pool `0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2`, AddressesProvider
  `0x2f39d218133afab8f2b819b1066c7e434ad94e9e`, PoolConfigurator
  `0x64b761d848206f447fe2dd461b0c635ec39ebb27`, ACLManager
  `0xc2aacf6553d20d1e9d78e365aaba8032af9c85b0`.
- The interval start: `deployment.start_block` is 16,291,071, hash
  `0x158e948f1db260e95adf7d0a23685226c7081b0fb8a3d9c1e6d731f2dc34172c`, the
  AddressesProvider's creation in transaction
  `0x75fb6e6be55226712f896ae81bbfc86005b2521adb7555d28ce6fe8ab495ef73`. The same
  field records that the first subject code appears at block 16,291,009, the
  Pool proxy is created at 16,291,127 and the first reserve is initialised at
  16,496,792.
- The end: `deployment.observed_block` is 26,022,093, hash
  `0x1cfd09b6dfaa2af921e367d94f24e2b1e6b7f910a7a6f4276576f09aeb3f5cb9`.
- 22 listed contracts with code length and keccak at 26,022,093 and proven
  creation blocks, and the complete Pool (11 revisions) and PoolConfigurator
  (revisions 1 and 3 to 8, seven in all) epoch tables with their transactions.
- `full_subject_set`: 356 addresses, the digest above, the form "sha256 of the
  lowercase addresses of the full record's code array, sorted, newline-joined
  with a trailing newline", and the 14-role count.
- The address-book discovery pin: `aave-dao/aave-address-book` at
  `052099461ec3ec22e66187aee8c6d3c9c157f361`, `src/AaveV3Ethereum.sol`, 80,417
  bytes, SHA-256
  `bfffd1a5148baa79875cacfd9ea340811be16415ddb9222bd35fc942d6c0a18b`, recorded
  under `documentation` in `source-match-1591.json`. It equals the digest the
  issue quotes.
- Compiler and build inputs for the 21 source sets the 22 listed contracts use,
  and summary counts over all 135 sets: 294 addresses reproduce byte for byte
  modulo immutables, 62 except trailing CBOR metadata, none differ.
- Six periphery entries, ten addresses, recorded and not admitted as subjects: the price
  oracle, five pool data providers, the incentives controller proxy, a mock
  stable debt token, Umbrella and the treasury.

Established only in the full records to hand, bound by digest from the row: the
other 334 subject addresses, every creation block and transaction, the 489
token-proxy implementation epochs, the 191 strategy epochs, the library links
and the per-set source identities. The full records were re-hashed for this
study: `ethereum-mainnet-1591.json` is 505,575 bytes with SHA-256
`cb0cfc4ff5d89115a05510ead274b0ba81f71a6770aaff7d8dae62fa43c1e22c`, and
`source-match-1591.json` is 1,588,360 bytes with SHA-256
`de33df7240b4964faf9f95e7702b9c16bff39257cbf022dfe6fb041ecc571613`. Both match
the row. Recomputing the subject-set digest over the full record's `code` array
reproduces `289bbdf7…` exactly.

Not established by #1591: any log, trace or opening journal; any measurement of
volume; a pinned ABI file for any contract; historical code for subjects at any
block other than 26,022,093; and source identity for the 16 source sets whose
target sits in no public repository, the 4 sets with differing files, and the 7
addresses whose verified text is a bytecode-equivalent fork's. #1591 also leaves
one inconsistency: `0x102633152313c81cd80419b6ecf66d14ad68949a` is both a
subject (the WETH reserve's stable debt token proxy, created at block
16,496,792) and the `mock_stable_debt` periphery entry. This study keeps it as a
subject, because it is inside the digest-bound set, and item 12 lists the
question.

From the full record, the 356 subjects by role are 71 interest-rate
strategies, 70 libraries, 67 aToken proxies, 67 variable debt token proxies, 36
stable debt token proxies, 11 Pool implementations, 11 aToken implementations,
10 variable debt token implementations, 7 PoolConfigurator implementations, 2
stable debt token implementations, and one each of AddressesProvider,
ACLManager, Pool proxy and PoolConfigurator proxy. Eight subjects, all
libraries, were created before the interval start, at blocks 16,291,009 to
16,291,069. No subject was created after the end. The 172 proxies carry seven
distinct runtime codes. Their 489 token epochs are 170 openings read from the
implementation slot at the proxy's creation block and 319 `Upgraded`
announcements in six distinct transactions, the largest upgrading 120 proxies;
no proxy is upgraded twice in one block, and none in its creation block.

### The proxy mechanics the pinned source establishes

`aave/aave-v3-core` at `9630ab77a8ec77b39432ce0a4ff4816384fd4cbf`, the commit
the row records for Pool revision 1, in the repository the row names for both
market proxies, fixes three things this design relies on:

- `BaseUpgradeabilityProxy._upgradeTo` sets the EIP-1967 slot
  `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` and then
  emits `Upgraded(address indexed implementation)`, at lines 44 to 46.
- `BaseImmutableAdminUpgradeabilityProxy.upgradeToAndCall` calls `_upgradeTo`
  and only then delegatecalls the new implementation, at lines 69 to 77.
- `InitializableUpgradeabilityProxy.initialize` sets the slot without emitting
  `Upgraded`, at lines 20 to 25, which is why a token proxy's first
  implementation has to be read from the slot at its creation block.

So inside an upgrade transaction the slot changes at the moment `Upgraded` is
logged: a log from that proxy at a lower log index ran under the old
implementation, and one at a higher index ran under the new one. Log order is
execution order. That is the reviewed rule item 4 scopes to this venue. Each of
the seven proxy runtime codes must be tied to a source set with the same two
functions before the rule admits it; the one proxy whose verified text is a fork
path, `0x38c503a438185cde29b5cf4dc1442fd6f074f1cc`, is tied through its
Sourcify-verified runtime twin, as the full record states.

### In this repository

The venue table and its modules are the precedent this design extends:
`plugins/alexandria/scripts/alexandria_lib/venues/__init__.py`,
`venues/wildcat_v2.py` for a per-subject opening phase with `interval-start` and
`observed-block` openings, and `venues/compound_v3.py` for the collector's own
EIP-1967 reads. `alexandria_lib/interval.py` already carries the per-subject
receipt `alexandria-interval-receipt/v3`, the dictionary form of
`validate_epochs` at `:1058` whose per-subject tables may hold several epochs,
`proxy_log_positions` at `:927`, `MAX_EPOCHS` of 256 per subject at `:115`,
`MAX_SUBJECTS` of 4,096 at `:116`, `MAX_SHARDS` of 4,096 at `:67` and the
`shards_per_component` split at `:73`, which splits all three shard classes at
the same shard ranges (`component_ranges` at `:151`, `journal_names` at `:197`).
`alexandria_lib/release.py:56-57` sets 64 MiB per component and 128 components
per release. `usdc_interval.py:110-122` bounds one `collect` invocation at 3,600
seconds and 512 MiB, prefetch at 8, targeted traces at 16 and all RPC at 8.
`Collector._targeted_traces` at `usdc_interval.py:1499` traces each transaction
a shard's own logs name and keeps the frames `_matches_subjects` at `:3415`
admits. `log_identity` at `interval.py:1790` compares
`(blockHash, transactionHash, logIndex, address, topics, data)` and not
`transactionIndex`.

The Wildcat examples, `plugins/alexandria/examples/wildcat-v1-interval-v0/` and
`wildcat-v2-interval-v0/`, are the precedent for a production capture whose
staging lives outside the tree: the example commits plan, registry, staging
manifest and rebuild record, `build` needs the staging path in an environment
variable and refuses by name without it, and `verify-preserved` checks committed
metadata alone. The V2 plan uses 3,463 shards of 1,200 blocks at 87 shards per
component, which is 40 component ranges per shard class.

### The last two merged pull requests that changed the subject

Pull request 1875 is the #1591 delivery read above. Besides the row, it made
`wildcat_registry.py` pin the canonical bytes of the two Wildcat rows
(`ROW_PINS`) instead of the whole of `targets.json`, which is what lets this
run's registry step leave the Wildcat registries untouched. Its body has no
`carryover` block. Its prose leaves two items: moving the Wildcat V1 and V2
evidence the same way, which it names as
https://github.com/wildcat-finance/skills/issues/1874 and which is a non-goal
here, and capture parity with the Wildcat captures, which it leaves outside the
repository and which this run answers by collecting and preserving Aave the way
#1731 collected and preserved Wildcat.
Pull request 1833, merged 2026-09-22, touched only Alexandria's generated
`PROMISE_MACHINE.md` copy and version and is not a subject change.

Pull request 1838, merged 2026-09-22 as the #1731 delivery, built the venue
table, both Wildcat venues, targeted tracing, full-frame trace reconciliation,
bearer transport credentials, bounded concurrency and the journal split. Its
`carryover` block has 26 rows. The ones this run meets:

- `opening-only-dispute-build`, filed as
  https://github.com/wildcat-finance/skills/issues/1831: an opening-only
  dispute still cannot build. This run does not repair it and does not require
  it; an Aave opening-only dispute follows #1831, as the issue says.
- `transaction-index-reconciliation`, none: the held frontier. This run adds
  the transactionIndex-only specimen and a declared limitation, and leaves the
  comparison unchanged.
- `logless-transaction-traces`, none: carried unchanged; the Aave release
  declares it.
- `fiat-1350-boundary-leads`, none: the finality-boundary, header-by-hash and
  undeclared-journal leads stay open and are carried into the risk register.
- `resource-coverage-leads`, none: the "unprobed 4096-address provider filter"
  lead lands here, because the Aave filter is 356 addresses. The primary
  answered a 356-address filter in this study; the second provider was not
  probed, and item 3 schedules that probe.
- `network-confinement-boundary`, duplicate of
  https://github.com/wildcat-finance/skills/issues/1445: the demonstration
  denies Python socket construction, an observed Python boundary rather than
  operating-system isolation, and says so.
- `operator-provenance-assertions`, duplicate of
  https://github.com/wildcat-finance/skills/issues/1442: the Aave fixture
  deployment carries the constructed-staging gap in the release itself.

The other rows sit outside Alexandria's collector or are Wildcat-specific
source limits, and stay where 1838 left them.

### Audit history

The whole-set currency check ran from the target root and exited 0:
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
reported 105 sources, every one `committed=match`. There is no
`plugins/alexandria/audit` directory. Five sources are in scope:

| Source | View read | Why |
| --- | --- | --- |
| `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md` | source, by finding rows and each round's `Leads not pursued` and `Elenchus verdict` | the run that built the venue table this run extends |
| `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.synopsis.md` | not read beyond its header | 88 KB, larger than its 502-line source, so the source was the cheaper reading |
| `audit/rounds/fiat-1503-attribute-implementation-epochs-by-transact.md` | carried from the #1731 study | the v2 positional receipt; no round record changed since that study |
| `audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.md` | carried from the #1731 study | the live collector run; its three open leads are carried |
| `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.md` | carried from the #1731 study | the collector build; its open rows are receipted-prose divergences |

Only the fiat-1731 source was read in this study. The other three were read
in full by the #1731 study, whose item 2 records their findings, and none of
them has changed since: `git log` shows no commit touching any of the three
between that study's base, `b2f528e9bee8dc4bd4d1653f7f66fe6b1de93bc0`, and this
run's. Their content enters here as that study recorded it,
not as a fresh reading.

fiat-1731 holds 42 finding rows under 40 ids over 30 rounds. Every finding's
last row reads "fixed" except two. W7-R1-01 (medium) last reads "needs a runbook
amendment" for an Exit count on the receipted #1731 runbook and changes no code.
W8-R1-01 (low, the provider-class error-string overclaim) last reads that it
needs a runbook amendment; the final round's leads record it as corrected by
the dated erratum in `plugins/alexandria/docs/wildcat-interval/proof.md`, with
the historical record left intact. W1-R1-02 and W6-R4-01 each have an open row
followed by a fixed one. Elenchus verdicts: 14 rounds `inconclusive`, 5
`unguarded` and 11 `null`; none is upgraded here. The last round's `Leads not pursued` keeps open: targeted traces
exclude logless transactions; the local staging digest walk proves neither
concurrent-writer protection nor publisher identity; V1 opening-edge-case parity
and deploy-log-free market-list derivation; the three fiat-1350 leads;
unclosed `HTTPError` handling in `compound_phase0.py`; and the unchanged
transaction-index frontier.

**No known-failure inventory is required.** None of those findings or leads is
a failure that implementation must guard before product work starts: the open
rows are receipted-prose corrections, and the leads are declared coverage limits
or code paths this run does not touch. The study carries no inventory block and
the runbook carries no assignment record.

### Outside this repository

EIP-1967 at https://eips.ethereum.org/EIPS/eip-1967 fixes the implementation
slot and the `Upgraded(address)` event. The Aave proxy sources are cited above
at their pinned commit. The address book is a discovery input, not deployment
evidence; its revision is pinned, and it does not replace #1591's creation and
epoch evidence.

## 3. Constraints and non-goals

**Starting ref and toolchain.** `d162d0952782f09659370b6a554c9cd4511b8db9`,
Python 3.14.6, stdlib only. The Alexandria package version is `0.7.12` and the
skill ledger is `alexandria-v3.6.0`, frontier `open`, holding
`transaction-index-reconciliation`. The delivery is the next Alexandria
generation after the integration base; the runbook declares that relation rather
than a literal version, because concurrent runs pick versions independently.

**The merged records this run reads, at the base commit.**

| Input | Bytes | SHA-256 |
| --- | --- | --- |
| `docs/kickoff/1359/targets.json` | 400627 | `ccc5e89816258f537af532bf7ea5c34fd48fa05282dacc1e20341859a7c0b319` |
| `docs/kickoff/1359/evidence/ethereum-mainnet-1591.json` | 31732 | `d1cd76a480431eaab8de37fe1a88c4be1764225b68e284548822ffa009d63c48` |
| `docs/kickoff/1359/evidence/source-match-1591.json` | 44034 | `196aedae0fbc0aa4eefba13f1362c2cf4f95bd4a9c01fbcc11b6460b151c7324` |
| `docs/kickoff/1359/evidence/scope-ruling-1591.json` | 2137 | `1da729aba10d2a0d6d5affe9c98cffcb0fb27e82c8555feb1cd78069d912804e` |
| `plugins/alexandria/scripts/alexandria_lib/interval.py` | 95812 | `fe6b3cd499f42df532771a68804c2fb45ab4352c0611e357dc6a4abeda63bc31` |
| `plugins/alexandria/scripts/usdc_interval.py` | 173829 | `28d682da45fe61dd9be4d551e4b7c639e4d5ca5e2fb4532c4de64ae862c719db` |
| `plugins/alexandria/scripts/alexandria_lib/release.py` | 27102 | `b5749b475b0935bf73ee4150f54db97ca82cd41536d12b35f4a0b03055c51c31` |

The registry step pins whichever canonical bytes of the `aave-v3` row its own
base carries, the way `ROW_PINS` pins the two Wildcat rows, so a later edit to
another row does not break it.

**What was read from the chain for this study, and what it showed.** Every read
went to the local Reth archive node, `reth/v1.11.0-564ffa5/aarch64-apple-darwin`,
over loopback, and is recorded in `.hexaemeron/design/preflight-sample.json` and
`.hexaemeron/design/upgrade-transaction-specimen.json`, which Step 1 copies into
the tree.

- Boundaries. Block 26,022,093 returned hash `0x1cfd09b6…f5cb9`, matching the
  row, and the `finalized` tag stood at 26,029,429, above it. Block 16,291,071
  returned `0x158e948f…4172c`, matching the row. The AddressesProvider has no
  code at 16,291,070 and 9,846 bytes at 16,291,071; the earliest subject has no
  code at 16,291,008 and 15,118 bytes at 16,291,009. Archive state is therefore
  served at the interval start.
- Logs. Twelve 1,000-block windows, evenly spaced from the start to the last
  1,000 blocks before the end, each one `eth_getLogs` over the 356-address
  filter: 24,225 logs, 17,629,902 response bytes and 4,106 distinct
  transactions in 12,000 blocks, 32.26 seconds in all. Density grows over time,
  from 27 logs in the first window to 5,718 in the densest, at blocks
  23,367,450 to 23,368,449. The Pool emits the most in every window after the
  first.
- Traces. 72 `trace_transaction` calls over transactions from three 200-block
  windows: 2,486,187 raw bytes, 3,145 frames, of which the collector's
  `toAddress` rule keeps 1,392 in 1,040,063 bytes, 14,445 bytes per
  transaction; 47.53 seconds serially, 0.66 seconds per call.
- The upgrade transaction specimen described in item 1.

Extrapolated linearly over 9,731,023 blocks, which the growth in density makes
a rough figure rather than a forecast: 19,644,502 logs in 14,296,415,154
response bytes, 3,329,631 traced transactions in 48,097,593,584 filtered bytes,
62.4 GB of journal payload before the JSON-RPC envelope each entry carries, and
2,198,019 seconds of serial trace time on the primary alone. The second
provider repeats every trace for reconciliation. Wildcat's throughput figures in
`plugins/alexandria/docs/wildcat-interval/proof.md` are not used here.

**What bounds a segment.** The production capture is a table of contiguous
segment plans, and every segment meets all of these.

- At most 4,096 shards (`MAX_SHARDS`), each at most 50,000 blocks
  (`MAX_SHARD_WIDTH`) and at most the second transport's `eth_getLogs` range
  cap, which #1731 measured at a span of 29,999 and which the preflight
  re-reads.
- One `shards_per_component` for all three shard classes, giving at most 40
  ranges per class, so that three classes of 40 leave eight of the 128
  components for opening evidence, registry, implementation code and the rest.
- Each range of the densest class at most 48 MiB by the preflight's measured
  rate, three quarters of the 64 MiB ceiling, and every component and journal
  at most 67,108,864 bytes when built.
- At most `MAX_PAGE_LIMIT` records in any one `eth_getLogs` answer.

At the densest sampled window, traces run at 13,420 bytes per block, so one
48 MiB range holds about 3,750 blocks and 40 ranges hold 150,023 blocks, about
2.64 GB of journals. Uniform segments at that width would need 65 segments; the
preflight sets each segment's width from its own measured density, so the real
count is smaller, but no figure below 65 is claimed until it is measured.

**What bounds a collection.** Unchanged collector constants: one `collect`
invocation stops at 3,600 seconds or 512 MiB, and RPC concurrency is at most 8.
At the sampled volume that means at least 117 invocations by bytes and, if
trace calls scale linearly to eight at a time, about 76 hours of primary trace
time. Scaling past one concurrent trace was not measured; the preflight
measures it at 1, 4 and 8. Reconciliation repeats every targeted trace on the
second transport, about 3.33 million more `trace_transaction` calls against a
hosted, bearer-authenticated provider whose rate and latency for this load were
not measured here; the preflight measures them before the table is frozen.

**What this run produces, and where it lives.** Under the maintainer's ruling
the split is #1731's:

| Artefact | #1731 | This run |
| --- | --- | --- |
| Venue module, registry, epoch model, fixtures, refusal battery | in the tree | in the tree |
| Preflight measurement | recorded in the study from a retired attempt | Step 6, against both transports, committed as measurements only |
| Production plan and limits | one plan per estate, in the tree | one plan per segment and the pinned segment table, in the tree |
| Collection from the local archive node and reconciliation against the hosted transport | Steps 9 and 10 | Step 7 |
| Staging trees and their archives | outside the tree | outside the tree |
| Staging manifest, rebuild record, `expected.json` per capture | in the tree | in the tree, one set per segment |
| Offline rebuild with Python sockets denied | the combined demonstration | Step 8's demonstration |
| Shared-store upload, retrieval and a manifest joining releases | not done | not done; #1373 |

**Departures from that precedent, each forced.**

1. Several releases instead of one per estate. Evidence: the single-plan
   estimate of 62,394,008,738 bytes against the 8,589,934,592-byte format
   ceiling. Wildcat V2's largest component was 25,079,138 bytes and its release
   fit.
2. Shard width, split and concurrency chosen from a fresh Aave preflight, not
   inherited. Evidence: the densest sampled Aave window carries 5,718 logs and
   929 traced transactions per 1,000 blocks.
3. A per-subject EIP-1967 epoch model and a venue-scoped upgrade-transaction
   order rule, where Wildcat had one immutable epoch per subject. Evidence: the
   172 proxies and the specimen transaction in item 1.
4. A registry generated from records held outside the tree and checked against
   the in-tree row, where Wildcat's generators read merged repository records.
   Evidence: the merged row lists 22 of the 356 subjects and binds the rest by
   digest.

Every other part of the delivery follows #1731: the four commands, the
constructed-staging gap for any unadmitted deployment name, targeted traces
selected from subject logs, full-frame trace reconciliation, the bearer
credential read from the environment, the external staging with committed
manifests and rebuild records, `verify-preserved`, the proof document, and a
generation row on the Alexandria ledger. #1731's rebuild record recorded a
rebuild from a fresh extraction on the collecting host; the Aave rebuild records
do the same, and a download from a shared store stays with #1373.

**The credential rule.** No endpoint, header or bearer credential enters any
artefact this run produces, including the preflight record, as #1731 required.
The second transport's credential reaches the process through the environment
and its request-scoped Authorization header only. Each provider is named by
class.

**Boundaries.**

Always: both suites before a commit; the repository-wide checked runner at every
step's exit; the imprimatur lint on every shipped document; the Horos boundary
regenerated before the census, in the commit that changes the tracked tree; a
recorded measurement before any performance claim.

Ask first: adding a dependency; changing the interval plan, checkpoint or
receipt schema; changing `MAX_*` constants or the component split rule; widening
what the Aave registry pin admits; changing the Builder's access or
redistribution classes; touching CI; any RPC read outside the preflight of Step 6 and the collection
of Step 7; changing reconciliation's comparison tuple.

Never: commit an RPC endpoint, credential or key; name the private capture
pipeline or its repository in shipped prose; upgrade, restart or reconfigure the
local archive node; vendor Aave source into this repository; edit a vendored
directory; delete a failing test to make a suite pass; claim a command ran when
it did not; present constructed bytes as preserved chain evidence; describe an
interval release's `public` label as export authority.

**Non-goals.** No other chain, no Aave V2 or V4, no Horizon, Lido or EtherFi
market. No credit event, position observation or economic equivalence;
Tabularium owns that at #1395. No repair of #1831. No change to reconciliation's
tuple. No collection manifest across segment releases and no store retrieval;
#1373 owns both. No move of the Wildcat evidence; #1874 owns it. No completeness
claim for the market: the capture is what its frozen plans declare. The
periphery contracts are not subjects: the price oracle
`0x54586be62e3c3580375ae3723c145253060ca0c2`, the five pool data providers, the
incentives controller proxy `0x8164cc65827dcfe994ab23944cbc90e0aa80bfcb`,
Umbrella `0xd400fc38ed4732893174325693a63c30ee3881a8` and the treasury
`0x464c71f6c2f760dda6093dcb91c24c39e5d6e18c`. Admitting any of them would move
the subject set off the digest #1591 reviewed. Underlying reserve assets are not
subjects either: the address filter names only the 356, and a trace frame whose
recipient is an underlying token is dropped by `_matches_subjects`, so the
capture does not become an Ethereum-wide token scan. Logless transactions stay
outside trace coverage.

## 4. Design options

Four candidate constructions. The prose explains them; the selection is made in
`.hexaemeron/design-evidence.json` from the checked matrix. Every value in that
record is computed by `.hexaemeron/design/build_design_evidence.py` from
`model-observations.json` and `preflight-sample.json`, not typed in.

**`segmented-proxy-set-venue`.** A reviewed `venues/aave_v3.py` registered in
`_MODULES`; a committed Aave registry of the 356 subjects, generated from the
full records and pinned by SHA-256 in that module; a per-subject epoch model
keyed by registry role, EIP-1967 for the 172 proxies and one immutable epoch for
the other 184; the within-transaction order rule admitted by an opt-in parameter
the Aave module alone passes; and the interval frozen as a pinned table of
contiguous segment plans, each an ordinary plan and release. Trade: several
releases instead of one, a new join problem that #1373 owns, and a venue-scoped
branch inside the shared position walk.

**`single-interval-venue`.** The same venue, registry and rule, with one plan
over the whole interval. Trade: one release to reason about, but its estimated
62,394,008,738 bytes are seven times the 8,589,934,592-byte format ceiling, so
it cannot build without a format change this issue does not own.

**`log-discovered-subjects`.** Pin only the 22 listed contracts and discover
the token proxies, strategies and implementations from provider and
configurator events during collection. Trade: no out-of-tree generator input,
but the subject set is not frozen before the production run, which the issue
requires, and 334 subjects would rest on provider answers rather than a pin in
reviewed code.

**`global-transaction-order-rule`.** Remove the shared refusal of ordinary logs
inside an upgrade transaction for every venue. Trade: the smallest shared diff
for Aave's sake, but Compound and Wildcat would accept a shape their own pinned
sources never established, the positional demonstration's refusal probe and its
test would change, and the rule would stop being a reviewed claim about one
proxy family.

A fifth reading, keeping today's refusal for Aave, is not a candidate: the
specimen transaction in item 1 refuses under it, so no plan covering block
22,839,362 could build.

**The selection.** Four hard gates remove three candidates:
`single-interval-venue` fails `largest-release-within-ceiling`;
`log-discovered-subjects` fails `subject-set-frozen-before-collection` and
`subject-pin-in-reviewed-code`; `global-transaction-order-rule` fails
`upgrade-order-rule-venue-scoped`. `segmented-proxy-set-venue` passes all five
selection gates and is the unique survivor, so `unique-frontier` selects it
before the two metrics are compared. **The trade it makes:** more releases and a
join left to #1373, in exchange for a capture that builds under today's format,
a subject set pinned before anyone collects, and a rule scoped to the proxy
family whose source establishes it.

**The design record, in full.** `.hexaemeron/design-evidence.json` is not in
git until Step 1 copies it, so its whole content is restated here. Schema
`protasis-design-evidence/v1`; candidates in the order
`segmented-proxy-set-venue`, `single-interval-venue`, `log-discovered-subjects`,
`global-transaction-order-rule`; selection `segmented-proxy-set-venue` by
`unique-frontier`, `policy_ref` null. Every selection report is
`protasis-design-report/v1` with command
`python3 .hexaemeron/design/build_design_evidence.py` and exit 0, at
`reports/selection/<candidate>-<criterion>.json`.

Selection criteria, each blocking `design-lock`, with each candidate's value and
state in the candidate order above:

| Criterion | Concern | Kind, owner | Rule | Values |
| --- | --- | --- | --- | --- |
| `existing-build-check-path` | compatibility | gate, protasis | equals true | true pass; true pass; true pass; true pass |
| `subject-set-frozen-before-collection` | correctness | gate, protasis | equals true | true pass; true pass; false fail; true pass |
| `largest-release-within-ceiling` | space | gate, metron | bytes at most 8589934592 | 2638240682 pass; 62394008738 fail; 2638240682 pass; 2638240682 pass |
| `upgrade-order-rule-venue-scoped` | compatibility | gate, protasis | equals true | true pass; true pass; true pass; false fail |
| `subject-pin-in-reviewed-code` | recovery | gate, phylax | equals true | true pass; true pass; false fail; true pass |
| `shared-module-edit-sites` | time | metric, metron | minimise count | 3; 3; 5; 4 |
| `largest-release-estimate` | space | metric, metron | minimise bytes | 2638240682; 62394008738; 2638240682; 2638240682 |

The byte figures come from the preflight sample: the single-interval value is
the mean sampled rate of 6,411.87 bytes per block over 9,731,023 blocks, and
the segmented value is a uniform segment of 150,023 blocks at the densest
window's 17,585.57 bytes per block, where the densest class, traces at 13,420
bytes per block, fills 40 ranges of 48 MiB. The edit-site lists are in
`.hexaemeron/design/model-observations.json`.

Conformance criteria, each an equals-true boolean gate, pending for all four
candidates with resolver
`python3 .hexaemeron/design/conformance.py <criterion> --candidate <candidate>`
and future report `reports/conformance/<candidate>-<criterion>.json`. The
resolver carries test cases for the selected candidate only and refuses any
other.

| Criterion | Concern | Owner | Blocks | Test identifiers the resolver runs |
| --- | --- | --- | --- | --- |
| `registry-reproduces-recorded-subject-set` | correctness | protasis | `step:3` | `AaveRegistryConformanceTests` `test_registry_reproduces_the_recorded_subject_set_digest`, `test_listed_contracts_match_the_merged_row` |
| `registry-pin-change-refuses` | recovery | phylax | `step:3` | `AaveRegistryConformanceTests` `test_changed_registry_pin_refuses_by_name`, `test_changed_source_row_refuses_by_name` |
| `per-subject-proxy-epochs-derived` | correctness | protasis | `step:4` | `AaveEpochConformanceTests` `test_proxy_epochs_follow_upgrade_positions`, `test_pre_interval_subject_opens_at_interval_start`, `test_proxy_created_in_interval_opens_at_its_creation_block` |
| `unsupported-upgrade-shapes-refuse` | recovery | elenchus | `step:4` | `AaveUpgradeRefusalTests` `test_upgrade_in_opening_block_refuses`, `test_two_upgrades_of_one_subject_in_one_block_refuse`, `test_slot_disagreeing_with_announcement_refuses`, `test_unrecorded_implementation_refuses` |
| `other-venues-keep-upgrade-transaction-refusal` | compatibility | protasis | `step:4` | `OtherVenueCompatibilityTests` `test_compound_still_refuses_an_ordinary_log_in_its_upgrade_transaction`, `test_wildcat_venues_still_read_no_upgrade_topic` |
| `wrong-chain-or-market-refuses` | recovery | phylax | `step:5` | `AaveScopeRefusalTests` `test_wrong_chain_refuses`, `test_wrong_market_refuses` |
| `collection-refusal-battery` | recovery | elenchus | `step:5` | `AaveCollectionRefusalTests` `test_foreign_emitter_refuses`, `test_incomplete_page_refuses`, `test_missing_journal_refuses`, `test_corrupt_journal_refuses`, `test_provider_failure_records_a_receipt`, `test_provider_disagreement_is_disputed`, `test_interrupted_resume_is_byte_identical`, `test_changed_boundary_hash_refuses` |
| `transaction-index-only-disagreement-declared` | correctness | protasis | `step:5` | `TransactionIndexSpecimenTests` `test_index_only_difference_still_records_agreed`, `test_release_declares_the_positional_verification_limit`, `test_check_refuses_a_release_without_the_limit` |
| `credential-absent-from-artefacts` | recovery | phylax | `step:5` | `AaveCredentialTests` `test_bearer_credential_absent_from_every_artefact`, `test_transport_error_text_names_no_endpoint` |
| `segment-plans-tile-the-interval` | correctness | protasis | `step:7` | `SegmentTableTests` `test_segments_tile_the_ruled_interval`, `test_every_segment_plan_validates_and_is_pinned` |
| `segment-budget-within-ceilings` | space | metron | `step:7` | `SegmentBudgetTests` `test_every_segment_estimate_fits_its_component_ceiling`, `test_every_fixture_component_and_journal_is_under_the_ceiling` |
| `preflight-measurement-recorded` | time | metron | `step:7` | `PreflightRecordTests` `test_preflight_record_counts_every_sampled_window`, `test_shard_width_and_concurrency_derive_from_the_record` |
| `production-segments-preserved-and-rebuilt` | correctness | protasis | `step:8` | `PreservedArtefactsTests` `test_verify_preserved_passes_against_the_committed_artefacts`, `test_every_segment_rebuild_record_agrees_with_its_pin`, `test_every_segment_counts_every_shard_and_class` |
| `existing-release-identities-retained` | compatibility | protasis | `integration` | `test_usdc_interval_live_demo.DemoReproducesReleaseIdTests.test_the_rebuild_reproduces_the_pinned_identifier`, `test_epoch_positions_demo.LiteralOwnershipTests.test_the_live_rebuild_has_its_own_recorded_identifier`, and `PreservedArtefactsTests.test_verify_preserved_passes_against_the_committed_artefacts` in both `test_wildcat_v1_interval_demo` and `test_wildcat_v2_interval_demo` |
| `aave-fixture-rebuilds-offline-without-sockets` | correctness | protasis | `integration` | `OfflineDemoTests` `test_build_and_verify_agree_without_a_socket`, `test_fixture_release_declares_constructed_staging` |

The test classes live in `plugins/alexandria/tests/`:
`test_aave_v3_registry.py` for the first two rows, `test_aave_v3_venue.py` for
the next three, `test_aave_v3_collector.py` for the next four,
`test_aave_v3_segments.py` for the next three and `test_aave_v3_interval_demo.py`
for `PreservedArtefactsTests` and `OfflineDemoTests`. A `step:N` cell is checked
immediately before Step N opens, so each row's tests land in the step before the
one it blocks. The four compatibility identifiers already exist and passed on the
base commit when this study ran them.

**The epoch model, precisely.** Each subject's table opens at its opening block:
the later of the segment start and its creation block, recorded in the registry
from the full record. A proxy opens with the implementation its EIP-1967 slot
holds at the end of its opening block, read in the opening phase. Each
`Upgraded` log that proxy emits later opens a new epoch at its own block,
transaction index and log index, and the slot read at that block's end must
equal the announced implementation. An ordinary log from that proxy in the same
transaction is owned by position: before `Upgraded`, the old epoch; after, the
new one. Refused, by name: `Upgraded` in the subject's opening block; two
`Upgraded` from one subject in one block; a slot that disagrees with the
announcement; an implementation the registry does not record for that subject;
and a proxy whose runtime code is not one of the seven reviewed proxy codes. An
immutable subject has one epoch whose implementation is itself and whose code
digest is read at its opening block. `MAX_EPOCHS` bounds each subject, and the
largest recorded table is the Pool's 11.

**Contracts deployed before the interval.** The eight libraries created at
blocks 16,291,009 to 16,291,069 open at the interval start with `interval-start`
openings: runtime code read at 16,291,071, and the registry's recorded creation
block and transaction kept as recorded deployment evidence, not as collected
evidence. Their pre-interval activity is outside the capture and the release
says so. A segment after the first opens every subject already created at the
segment start the same way, so each segment release stands alone.

**What the segments share.** Every segment names all 356 subjects, the same
registry, the same evidence classes and the same finality boundary, block
26,022,093 under `finalized`. A subject created after a segment's end has no
epoch in that segment and is named as outside its interval. Boundaries between
segments are block edges: segment *k* ends at block *b* and segment *k+1*
starts at *b+1*.

**Where the production name is admitted.** As #1731 admitted
`wildcat-v2-hooksfactory` in `PRESERVED_DEPLOYMENTS` in the step that collected
it, Step 7 admits `aave-v3-ethereum-main` in the Aave module's
`PRESERVED_DEPLOYMENTS`. Every other deployment name, including the fixture's,
carries the constructed-staging gap on every evidence scope. Because the capture
is several plans rather than one, the module also pins the digest of every
segment plan in the table, and a plan under the production name whose digest is
not pinned refuses; that is the issue's freeze requirement enforced at build,
and it follows from departure 1 in item 3.

**Build order.** Eight steps, in #1731's shape, which the runbook derives:

1. Preserve the design records and scaffold the conformance harness.
2. Register the aave-v3 venue with its pinned 356-subject registry.
3. Derive per-subject proxy and immutable epochs under the venue-scoped
   upgrade-transaction order rule.
4. Carry an Aave plan through collect, reconcile, build and check over
   constructed fixtures, with the refusal battery, the transactionIndex
   specimen and the credential checks.
5. Refresh the 1374 capture record against the resolved aave-v3 row, which
   `docs/kickoff/1374/capture.json` still lists as blocked and without a
   deployment.
6. Measure the Aave preflight on both transports and freeze the segment table.
7. Collect and preserve every Aave segment from two transports.
8. Demonstrate the capture path offline, resolve the conformance cells and
   record the delivery on the Alexandria ledger.

**The positional verification limit.** Every Aave evidence scope that carries a
reconciliation declares, in its own gaps, that provider agreement over logs
excludes `transactionIndex`, so agreement is not a positional claim. The
declaration names the held frontier and goes away only when that job lands.
Agreeing secondary response bytes are not retained by the current collector;
this run makes no claim that the comparison can be repeated offline.

## 5. Risk register

The concerns the audit loop should look hardest at. The ids are how a round
cites them.

```risk-register
undeclared-venue | a plan naming aave-v3 before or without its module | build refuses by name and never falls back to another venue
wrong-chain-or-market | a plan whose chain, Pool or AddressesProvider is not the ruled main market | build and check refuse by name
registry-pin-bypass | the Aave registry digest constant | the pin lives in reviewed code and no plan field or operator document supplies it
registry-row-drift | the canonical bytes of the merged aave-v3 row | the registry validator pins them and refuses a changed row by name
subject-set-digest | the 356 addresses the registry declares | they reproduce the row's full_subject_set digest under its recorded form, and role counts match by_role
listed-contract-agreement | the 22 contracts the merged row lists | address, role, code length and code keccak equal the row's
out-of-tree-generator-input | the full records the registry generator reads | the generator refuses any input whose SHA-256 and byte count differ from the row's full_record pins
mock-stable-debt-overlap | 0x102633152313c81cd80419b6ecf66d14ad68949a, both subject and periphery in #1591 | it stays a subject and the release names the overlap rather than resolving it silently
periphery-exclusion | the nine periphery addresses outside the subject set and every underlying asset | none enters the address filter or the trace subject set
role-epoch-model | the role that selects EIP-1967 or immutable epochs per subject | an unrecognised role or a proxy runtime code outside the seven reviewed refuses
upgrade-order-rule-scope | the opt-in within-transaction order parameter | only the aave-v3 module passes it and Compound and Wildcat still refuse an ordinary log in an upgrade transaction
upgrade-order-rule-soundness | an ordinary log before or after Upgraded in one transaction | ownership follows log index, and the source lines that establish slot-then-emit-then-delegatecall are cited for each reviewed proxy code
proxy-opening-without-announcement | a token proxy created by initialize with no Upgraded | its first implementation is the slot at its creation block and an Upgraded in that block refuses
slot-announcement-mismatch | the slot read at an upgrade block | it equals the announced implementation or the build refuses
implementation-drift | an implementation the registry does not record for its subject | the build refuses by name rather than opening an epoch
pre-interval-subjects | the eight libraries created before 16291071 | they open at the interval start and the release names their pre-interval creation as recorded, not collected
segment-tiling | the pinned segment table | segments tile 16291071 to 26022093 with no gap or overlap and each plan digest is pinned
segment-budget | each segment's estimated and built bytes | 40 ranges per class at 48 MiB planned, 128 components and 67108864 bytes per component enforced by check
production-name-admission | the aave-v3-ethereum-main deployment name | only a plan whose digest is in the pinned table uses it and every other name carries the constructed-staging gap
constructed-staging-claim | the Aave fixture release | its own coverage names the construction, not only a sibling README
transaction-index-limit | an agreed reconciliation over logs | the release declares that agreement excludes transactionIndex and check refuses its omission
transaction-index-specimen | a second provider differing only in transactionIndex | the specimen still records agreed and the test fails if the limit sentence is dropped
foreign-emitter | a log from an address outside the 356 | it is refused rather than attributed
incomplete-page | an eth_getLogs answer at the page limit | the shard refuses rather than recording a truncated page
missing-or-corrupt-journal | a staging journal removed or altered | build and check refuse by name
provider-failure | the second provider failing mid-run | a structured receipt names code, shard and provider class and the interval stays unreconciled
interrupted-resume | a collect killed between shards | the resumed journals are byte-identical and the checkpoint binds them
boundary-hash-change | a remembered boundary hash that no longer matches | the run rewinds within its bounded trail or refuses
credential-in-artefact | a bearer credential or endpoint | neither appears in any journal, component, receipt, preflight record, test or committed byte
credential-in-error-text | a transport failure, HTTP status or redirect refusal | the message names no endpoint and no credential
preflight-read-scope | the Step 6 preflight against both transports | it makes only the declared bounded reads, records measurements rather than journals, and never reconfigures the local node
address-filter-cap | a 356-address eth_getLogs filter on the second provider | the preflight probes it before the table is frozen and a refusal changes the plan rather than the subject set
compatibility-identities | Compound and Wildcat release identifiers and demonstrations | all four identifiers still rebuild or verify and no shared default changes
public-label-reading | the Builder's public and permitted component classes | no Aave document describes them as export authority
opening-only-dispute | an opening-only dispute in an Aave segment | it follows #1831 and is not turned into success
carried-lead-bind-finality | the finality boundary comparison | fiat-1350's first unpursued lead is unchanged and stays open by name
carried-lead-opening-compare | the first-block header comparison by hash alone | fiat-1350's second unpursued lead is unchanged and stays open by name
carried-lead-undeclared-journal | a manifest journal for a class the plan did not declare | fiat-1350's third unpursued lead is unchanged and stays open by name
partial-release-write | the release directory during a long build | a killed build leaves no half-written release that verifies
```

## 6. Glossary seeds

**Main market.** The Aave V3 Ethereum market whose Pool is
`0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2` and whose AddressesProvider is
`0x2f39d218133afab8f2b819b1066c7e434ad94e9e`.

**Subject.** One of the 356 addresses the registry declares and the address
filter names.

**Proxy subject.** One of the 172 `InitializableImmutableAdminUpgradeabilityProxy`
subjects, whose epochs follow the EIP-1967 slot and `Upgraded` positions.

**Immutable subject.** One of the other 184, with one epoch.

**Opening block.** The later of the segment start and the subject's creation
block.

**Upgrade-transaction order rule.** Inside a transaction where a proxy subject
emits `Upgraded`, that subject's other logs belong to the old epoch below the
announcement's log index and to the new epoch above it.

**Reviewed proxy code.** One of the seven proxy runtime codes tied to a source
set whose `_upgradeTo` and `upgradeToAndCall` were reviewed.

**Periphery.** The six entries, ten addresses, #1591 recorded under `periphery_not_subjects`; nine of them are outside the subject set.

**Segment.** One contiguous block range of the interval, collected under its
own plan and built into its own release.

**Segment table.** The pinned list of segment plans and their digests that tiles
the interval.

**Preflight record.** The committed measurement of sampled log and trace volume,
timings and the choices derived from it.

**Positional verification limit.** The declared gap that log agreement excludes
`transactionIndex`.

**Constructed staging.** A staging tree whose journals were written, not
collected, and which says so in its release coverage.

## 7. Sources

Repository files, read at `d162d0952782f09659370b6a554c9cd4511b8db9`:

- `docs/kickoff/1359/targets.json`, the `aave-v3` row: `scope_ruling`,
  `source.deployed_source_epochs`, `source.build_inputs`, `deployment`
  including `start_block`, `observed_block`, `market`, `contracts` and
  `full_subject_set`.
- `docs/kickoff/1359/evidence/ethereum-mainnet-1591.json`, for `market.launch`,
  `code`, `provider_events`, both epoch tables, `creation`,
  `end_state_check`, `periphery_not_subjects` and `summary`.
- `docs/kickoff/1359/evidence/source-match-1591.json`, for `method`,
  `documentation`, `source_sets`, `source_state_gaps` and `full_record`.
- `docs/kickoff/1359/evidence/scope-ruling-1591.json`, for the ruling, its
  comment digest and the excluded markets.
- `plugins/alexandria/scripts/alexandria_lib/venues/__init__.py`,
  `venues/compound_v3.py`, `venues/wildcat_v2.py`.
- `plugins/alexandria/scripts/alexandria_lib/interval.py`, for the formats at
  `:35-47`, the caps at `:66-116`, `component_ranges` at `:151`,
  `journal_names` at `:197`, `validate_plan` at `:215`,
  `proxy_log_positions` at `:927` and its upgrade-transaction refusal at
  `:1005-1008`, `validate_epochs` at `:1058` and `log_identity` at `:1790`.
- `plugins/alexandria/scripts/usdc_interval.py`, for the collection bounds at
  `:110-133`, `Collector._spend` at `:1063`, `_targeted_traces` at `:1499`,
  `Builder` at `:2239` and its fixed component classes at `:2407` and `:2411`,
  `_gaps` at `:2597`, `check_interval` at `:2700`, and `_matches_subjects` and
  `subject_transaction_hashes` from `:3386`.
- `plugins/alexandria/scripts/alexandria_lib/release.py:56-60`.
- `plugins/alexandria/scripts/alexandria_lib/wildcat_registry.py`, for
  `ROW_PINS` at `:72`.
- `plugins/alexandria/examples/wildcat-v2-interval-v0/` and
  `wildcat-v1-interval-v0/`, for the plan, split and external-staging pattern.
- `plugins/alexandria/docs/wildcat-interval/study.md`, `proof.md` and
  `design/conformance.py`.
- `plugins/alexandria/skills/alexandria/SKILL.md`, `EVOLUTION.md` and
  `plugins/alexandria/AGENTS.md`.
- `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md`.

Full records to hand, outside the tree, bound by the row: the `-1591` observation
and source-match records, at the digests in item 2.

Pinned outside sources:

- https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol
- https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/protocol/libraries/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol
- https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol
- https://github.com/aave-dao/aave-address-book/blob/052099461ec3ec22e66187aee8c6d3c9c157f361/src/AaveV3Ethereum.sol
- https://eips.ethereum.org/EIPS/eip-1967

Issues and pull requests read: https://github.com/wildcat-finance/skills/issues/1872,
https://github.com/wildcat-finance/skills/issues/1591,
https://github.com/wildcat-finance/skills/issues/1373,
https://github.com/wildcat-finance/skills/issues/1831,
https://github.com/wildcat-finance/skills/pull/1875 and
https://github.com/wildcat-finance/skills/pull/1838, whose `carryover` block
was read in full.

Chain reads: `.hexaemeron/design/preflight-sample.json` and
`.hexaemeron/design/upgrade-transaction-specimen.json`, both from the local
archive node on 2026-09-23.

## 8. Signals, and the questions behind them

`plugins/hexaemeron/skills/ephoros/SKILL.md` owns what a signal must carry. The
capture runs unattended for days on the collecting host, so four questions.

**Which segment and shard is it on, and can it resume?** The checkpoint under
each segment's staging tree records `next_shard`, `last_accepted` and per-journal
offsets after fsync. This run adds no checkpoint field. The segment table adds
the one thing a single checkpoint cannot say: which segments are finished.
Each segment's committed rebuild record and release identifier is that signal,
and `verify-preserved` reports the count of segments that have one.

**Did a subject's upgrade shape refuse, and where?** New. The Aave module's
refusals name the subject, the block, transaction index and log index, and the
rule that fired, so a refusal three days in can be matched to one transaction
without re-reading the journals.

**Did the second provider answer, and did it agree?** The reconciliation record
carries `status`, `compared`, `matched`, `provider_class` and the disputes. The
positional verification limit makes the one thing agreement does not cover
readable from the release itself.

**Is a segment approaching its component ceiling?** `check` already compares
each component with 67,108,864 bytes. Step 6 records each segment's planned
bytes beside its measured density, and Step 7's rebuild records carry the built
sizes, so a segment that grew past its plan is visible from committed bytes.

## 9. Trust boundaries, per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` owns the boundary list and the
controls. Six boundaries this run opens or moves.

**The registry generator reads a file from outside the tree.** Worth taking:
the full records carry the 334 subjects the row does not list. The control is
that the generator takes the path as an argument, reads a bounded regular
non-symlink file, refuses unless its SHA-256 and byte count equal the row's
`full_record` pins, runs no subprocess and opens no socket, and that the
committed registry is itself pinned in reviewed code and checked against the
in-tree row by a test that needs no out-of-tree input.

**The plan's venue selects a new epoch model and a new rule.** The control is
the existing venue table, plus the order rule being a keyword argument the
shared walk defaults to off, passed by the Aave module alone and proved off for
the other three venues by test.

**A 356-address filter reaches two providers.** Each address is validated
against the registry before any request. The second provider's acceptance of a
filter that size was not probed; Step 6's preflight asks it before the table
is frozen and records only the answer's shape and timing.

**The preflight reads the chain.** It uses the existing `collect` path over
declared sample plans, so it adds no network code. Its record holds counts,
bytes and timings, never journals, endpoints or headers. It does not change the
node.

**A production deployment name is admitted in code.** The control is that
admission is bound to the pinned plan digests, not to the name alone.

**Private names could reach public prose.** The control is the Never boundary
in item 3 and a review of every shipped document for it.

## 10. The performance budget

`plugins/hexaemeron/skills/metron/SKILL.md` owns what a budget carries.

One hard budget, enforced by existing code: every release component and staging
journal at most 67,108,864 bytes and every release at most 128 components,
checked by `python3 plugins/alexandria/scripts/usdc_interval.py check <release>`
for each segment release and by the segment tests over each segment's
estimate. One planning budget, owned by the segment table: 40 ranges per shard
class, each at most 48 MiB at its measured density.

The whole-run figures in item 3 are recorded estimates, not budgets, and nothing
in this run claims a speed-up or a duration. Step 6 records, with the command
that produced each: bytes and records per shard class per sampled window, trace
latency at concurrency 1, 4 and 8 on the primary, the derived shard width,
`shards_per_component` and segment widths, and the request and storage totals
they imply. Wildcat's timings are not inherited.

## 11. The fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` owns the triage order and the
guard rule.

What stops the run: every failure in this subject is an `AlexandriaError`,
printed as `usdc-interval: <message>` with exit 1, and no release is installed.
An unregistered venue, a wrong chain or market, a changed registry or row pin,
an unrecognised role or proxy code, any refused upgrade shape, a foreign
emitter, an incomplete page, a missing or corrupt journal, a changed boundary
hash beyond the rewind trail, a component over its ceiling and a plan under the
production name whose digest is not pinned all stop rather than degrade. A
provider that cannot answer leaves the interval `unreconciled`; a disagreement
leaves it disputed with both providers' bytes. An opening-only dispute follows
#1831 and is not repaired here.

Guard convention: a fix claimed in an audit round is proved by a test that fails
without it, run through the step's declared Elenchus command with one `{report}`
argument, its report format and its report file named in the runbook step's
`Tests` field. The suite is `python3 plugins/alexandria/tests/run_tests.py`, and
new guards go in the four new modules `tests/test_aave_v3_registry.py`,
`tests/test_aave_v3_venue.py`, `tests/test_aave_v3_collector.py` and
`tests/test_aave_v3_segments.py`, plus `tests/test_aave_v3_interval_demo.py`.
The conformance resolver `.hexaemeron/design/conformance.py` names the exact
test identifiers each criterion needs and refuses until they exist and pass.

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which decisions earn a
record and where each lives. Five decisions here are expensive to reverse, and
they are one design, so they share one record, created as an unnumbered draft
in Step 1 at `docs/decisions/drafts/aave-v3-interval-venue.md` and numbered only
by the integration composer.

1. **An interval over the format ceiling is captured as a pinned table of
   contiguous segment plans, each an ordinary release.** Reversing it after
   Step 7 collects would orphan every segment staging tree. It uses the existing
   release format, as every Wildcat release does; #1373 keeps the collection
   manifest joining the releases, the store and retrieval.
2. **The upgrade-transaction order rule is scoped to a venue by an opt-in
   parameter.** Widening it later changes what Compound and Wildcat accept.
3. **Epoch model per subject by registry role and reviewed proxy code.**
   Reversing it changes every Aave epoch table and release identifier.
4. **The subject set is #1591's 356, and the periphery stays out.** Adding a
   subject changes every segment plan digest.
5. **The production deployment name is admitted in code, as Wildcat's was,
   and bound to the pinned plan digests.** Loosening it would let an unpinned
   plan claim preserved provenance.

The Alexandria evolution ledger gets a generation row for the delivery, in the
shape the #1731 row uses, and
`plugins/alexandria/docs/usdc-interval-collector.md` gains the Aave epoch rule.
The segment count, shard width and split are data, not decisions: they live in
the preflight record and the segment table.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | segmented-proxy-set-venue
record | docs/decisions/drafts/aave-v3-interval-venue.md
```

**Proposed carryover rows for the run-level pull request.** Each is a proposal
until the integration step checks it, and each follows the disposition #1838
gave the same item.

```text
segment-manifest-and-store | duplicate | https://github.com/wildcat-finance/skills/issues/1373
opening-only-dispute | duplicate | https://github.com/wildcat-finance/skills/issues/1831
aave-event-mapping | duplicate | https://github.com/wildcat-finance/skills/issues/1395
positional-reconciliation | none | the held transaction-index-reconciliation job owns it; this run declares the limit and adds the specimen
wildcat-evidence-move | duplicate | https://github.com/wildcat-finance/skills/issues/1874
logless-transaction-traces | none | targeted traces cover transactions with subject logs only, and the release says so
network-confinement-boundary | duplicate | https://github.com/wildcat-finance/skills/issues/1445
fiat-1350-boundary-leads | none | the finality-boundary, header-by-hash and undeclared-journal leads stay unconfirmed and unchanged by this run
```

**Open questions.** The maintainer's ruling in assumption 6 settles every scope
question this study raised. The #1591 overlap on
`0x102633152313c81cd80419b6ecf66d14ad68949a` follows the Wildcat collateral
precedent: a subject in the pinned registry is collected like every other, and
the release names the overlap. The Builder's `public` and `permitted` labels stay
as they are on the Wildcat releases. No question is left open.
