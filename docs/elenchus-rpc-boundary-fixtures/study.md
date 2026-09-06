# study: pin RPC-boundary failures into Lazarus fixtures

## assumptions

Assuming, unless corrected:

1. The run starts from `main` at
   `ab611eb96a6a9bddecb57bff2416641296e0a21e`; the run branch, local `main`
   and `origin/main` all resolved to that commit and the worktree was clean
   before this study was written.
2. Issue #387's "procedure, with one worked example" is met by one new
   section in the Elenchus skill file and one new test module that runs
   offline against the checked-in Aave v4 fixture through the Lazarus
   command line. No test performs a live capture; the capture half is written
   as procedure with its exact commands.
3. The wave peers the issue leans on have not landed. #383 (`lazarus-next`),
   #384 (`lazarus-1`, the Foundry replay profile) and #385 (`lazarus-2`, the
   recording proxy) are open, so the procedure uses what Lazarus ships at
   `lazarus-v1.2.0`: `capture` over plan v1 or v2, `validate`, `verify`,
   `replay` and the release pair. Nothing under `plugins/lazarus/` changes,
   and the Lazarus held frontier `receipt-inclusion-proofs` is not touched.
4. This is generation work on mature `elenchus-v1.2.0`. It records
   `elenchus-v1.3.0`, retains frontier revision
   `observed-failure-root-cause`, digest
   `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`, status
   `mature` and `Next Fiat job: None -- mature` byte for byte, and moves
   `SKILL.md` `metadata.version` to `1.3.0`. The Promise Machine contract
   section of the skill does not change.
5. The Hexaemeron package moves from `1.6.1` to `1.6.2` on its four manifest
   surfaces and the pin in `tests/test_version_propagation.py`, so an
   installed copy is offered the changed skill file rather than reported as
   already current.
6. `python3` here is CPython 3.12.13 without the Lazarus dependencies;
   `uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt`
   supplies them; `/usr/bin/python3` is 3.9.6 and can run neither Lazarus nor
   the Hexaemeron suite. The example skips by name where the dependencies are
   missing and runs where they are present, and the Hexaemeron suite gains no
   third-party import.
7. The Hexaemeron suite carries two environment pins on this machine. One
   Elenchus checker fixture asserts Node `v26.6.0` and the host has
   v22.22.3, so the demo path wraps the suite in
   `npx --yes --package=node@26.6.0 --call`, as the #493 proof did. One
   recovery test runs `git verify-commit` on the #429 composition commit
   `0fb3bcfb`, and this machine's keyring lacks public key
   `636EC19DE45DF10F3CE6206F57742DA1ABED6F46`, so that test errors at the
   base ref, identically in the operator checkout. Importing that key is a
   machine action for the operator, outside this run; until it happens the
   suite reports `1167/1168` with that one named error, and every Elenchus
   verdict over the whole suite is `inconclusive`, because an errored report
   classifies that way. The runbook reads both facts as environment evidence.
8. The committed copies of this study and the runbook go to
   `docs/elenchus-rpc-boundary-fixtures/`, the root location the two most
   recent receipted wish runs used, rather than `plugins/hexaemeron/docs/`
   where the two earlier Elenchus runs put theirs; the ledger row links the
   root path.

These readings describe one capability with one prose change and one test
module behind it. No module decomposition is needed. Assumptions 5 and 8 are
scope calls Fiat can veto in one line without changing the chosen design; the
rest are readings of the issue, the ledgers and the repository.

## 1. problem statement

Elenchus's Reproduce step demands that a failure be made to happen reliably,
and its Localise step names "the RPC or fixture boundary the data crossed" as
one of the five layers a failure can sit at. The skill then says nothing about
how those two meet. Its only word on the subject is the Environment bullet,
"whether an RPC or fixture is warm or cold". A test that reads an archive
endpoint fails when the provider answers slowly, answers differently, rate
limits, or is switched off, and none of those can be made to happen on
demand. Lazarus exists for exactly this: `capture` records the exact JSON-RPC
exchanges a plan names at one fixed block, `verify` checks the fixture
offline, and `replay` serves only the recorded answers over loopback and
returns error `-32070` with a capture-plan fragment for anything else. The
Elenchus skill does not point at it, so an agent working a red test at that
boundary reruns the live call and hopes.

The users are agents and engineers running Elenchus on a failure whose inputs
cross an RPC boundary, Mason when an implementation step breaks against a
provider, and Warden when it classifies a fix whose reproduction must be
deterministic to count.

A working prototype means:

- `plugins/hexaemeron/skills/elenchus/SKILL.md` carries one section, placed
  after the six triage steps, that says when a failure belongs behind a
  fixture and gives the procedure step by step against what Lazarus does
  today: name the exact exchange, write the plan with the request marked
  required or optional, capture with the endpoint URL held only in an
  environment variable, verify, point the guard at `replay` on loopback,
  treat a `-32070` miss as a failed test, commit the fixture and the test,
  and state what a fixture cannot pin.
- The Reproduce step's Environment bullet points at that section, and the
  "Before the fix is receipted" checklist gains one item for a failure that
  crossed an RPC boundary.
- `plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py` exists
  and is the worked example: it starts `lazarus replay` on
  `plugins/lazarus/examples/aave-v4-spoke-v0` as an argv-pinned subprocess on an
  ephemeral loopback port, asserts the recorded answer for storage slot `0x0`
  exactly, asserts that the uncaptured slot `0x1` and the spelling `0x00` are
  `-32070` misses carrying the method, the parameters and a plan fragment,
  asserts that a write method is refused, refuses to leave loopback, and
  stops the server. Where the Lazarus dependencies are not importable from
  the running interpreter it skips with a reason naming them and the `uv`
  command; it never passes without running.
- The same module holds stdlib-only tests that fail on the current tree and
  pass on the changed one: the skill file carries the section, the commands,
  the miss code and the checklist item.
- Nothing under `plugins/lazarus/` changes by one byte.
- The ledger records `elenchus-v1.3.0` as a generation row with the frontier
  fields retained, the skill frontmatter reads `1.3.0`, the package reads
  `1.6.2` on every surface, and the committed study and runbook sit under
  `docs/elenchus-rpc-boundary-fixtures/`.

The demo path is this ordered list, run from the repository root. Every
command exits zero, with one stated exception: the Hexaemeron suite command
exits zero on a machine whose keyring holds public key
`636EC19DE45DF10F3CE6206F57742DA1ABED6F46`, and on this machine reports
`1168` tests run, zero failures and exactly the one named error
`test_issue_429_recovery.Issue429RecoveryTests.test_composition_has_exact_parent_order_and_signed_header`,
which the runbook's exit text and the audit round carry as environment
evidence rather than as a green gate:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_rpc_boundary_fixture -v
uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python -m unittest plugins.hexaemeron.tests.test_elenchus_rpc_boundary_fixture -v
uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python plugins/lazarus/examples/aave-v4-spoke-v0/demo.py
npx --yes --package=node@26.6.0 --call 'uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py'
python3 -m unittest discover -s tests
python3 -m unittest tests.test_evolution_contract
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/elenchus-rpc-boundary-fixtures/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/elenchus-rpc-boundary-fixtures/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/elenchus-rpc-boundary-fixtures/study.md docs/elenchus-rpc-boundary-fixtures/runbook.md plugins/hexaemeron/skills/elenchus/SKILL.md plugins/hexaemeron/skills/elenchus/EVOLUTION.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/elenchus-rpc-boundary-fixtures/study.md docs/elenchus-rpc-boundary-fixtures/runbook.md plugins/hexaemeron/skills/elenchus/SKILL.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The first command runs the stdlib tests and prints the replay class as
skipped with its reason, because this interpreter lacks the dependencies. The
second runs every test in the module with nothing skipped, because the `uv`
command installs the exact pins before Python starts; the runbook's exit text
names the count and the absence of the word `skipped`.

Before any change, the root suite runs 396 OK; `tests.test_evolution_contract`
runs 9 OK; `scripts/promise_machine.py check` prints `clean: 14 plugin(s), 14
copy/copies` and `coverage --check` prints `clean: promises=71
coverage_rows=71 coverage_selected=71`; `audit_synopsis.py --check .` exits 0
with all fourteen pairs reporting `committed=match`; the Lazarus suite runs
414 OK in 34.7 seconds under `uv` and fails to import under plain `python3`
(91 tests collected, 15 errors, every one `ModuleNotFoundError`); the Aave v4
demo and `verify` exit 0 under `uv` at fixture digest
`d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49`. The
Hexaemeron suite under plain `python3` reports `1166/1168 tests passed` in
402 seconds: `NodeReports.test_fixture_exercised_the_declared_node_version`
fails on `'v26.6.0' != 'v22.22.3'`, and
`Issue429RecoveryTests.test_composition_has_exact_parent_order_and_signed_header`
errors because `git verify-commit 0fb3bcfb...` exits 1 with `gpg: Can't check
signature: No public key`. Under the Node 26 wrapper it reports `1167/1168`
in 405 seconds with only the key error left; under `/usr/bin/python3` it
reports 647/1153 and is not a gate here. These facts establish a green start
on every command the demo path uses except the two environment pins named,
and the absent procedure; they are not proof of the change.

## 2. prior art

### in this repository

- `plugins/hexaemeron/skills/elenchus/SKILL.md` holds the two rules this
  study joins. "### 1. Reproduce" says "Make it happen reliably, and record
  the exact invocation" and, under Environment, "whether an RPC or fixture is
  warm or cold". "### 2. Localise" lists "the RPC or fixture boundary the data
  crossed". "## Fallbacks hide failures" already states the posture the
  procedure inherits: "a missing fixture, an unverified digest, an RPC that
  answered with something unexpected. Each of those stops the run and says
  so." The mechanical subset and the `elenchus-fixed-and-guarded` promise are
  untouched by this change.
- `plugins/lazarus/scripts/lazarus.py` is the command line the procedure
  names. `capture` takes `--plan`, `--rpc-url`, repeated `--anchor-rpc-env
  SOURCE_ID=ENV_VAR` and `--out`; `replay` takes a fixture path and `--port`
  with default `8545`; `verify` prints the fixture digest, the block hash and
  the three evidence counts.
- `plugins/lazarus/scripts/lazarus_lib/capture.py` settles what a failing
  exchange becomes. In `_capture_requests`, a request whose provider outcome
  is an error raises `CaptureError("required RPC request failed: <name>")`
  when the plan marks it `required: true`, and the whole capture then removes
  its staging directory and leaves no fixture. When the plan marks it
  `required: false`, the record is written with `outcome: {"error": ...}` and
  its request key is listed in the manifest's `optional_failures`. A
  required proof or state read that fails, a header that differs between the
  opening and closing reads, a chain ID other than `0x1`, an exhausted limit
  or a secret found in the staged bytes all end the same way: no fixture.
- `plugins/lazarus/scripts/lazarus_lib/rpc.py` and `scrub.py` decide what an
  error record holds. `sanitised_rpc_error` keeps the provider's integer
  `code` when it has one and otherwise writes `-32000`, and always writes the
  message `provider request failed`. A transport failure, a non-JSON body, a
  redirect and an over-limit response raise `RpcTransportError`, which is a
  capture failure rather than a record. `provider_secrets` collects the URL,
  its user information, its query keys and values, authorization and cookie
  headers and bearer tokens, and `assert_no_secrets` scans every staged file
  for them before finalisation.
- `plugins/lazarus/scripts/lazarus_lib/replay.py` and `server.py` are the
  guard's other end. `MISS_ERROR = -32070`; a miss response carries
  `data.method`, `data.params` and `data.capture_plan_fragment` with
  `evidence: recorded-rpc`, a `replay-miss-<12 hex>` name, the method, the
  parameters and `required: true`. An unsupported or write method returns
  `-32601`. `make_server` refuses any host that is not an IPv4 loopback
  literal, accepts port `0`, verifies the fixture before binding, and
  `serve_fixture` prints `lazarus replay listening on
  http://127.0.0.1:<port>` and flushes before serving. The store is built
  once from `rpc.jsonl` after the manifest digests are rechecked.
- `plugins/lazarus/scripts/lazarus_lib/records.py` defines the request key
  as SHA-256 over canonical JSON of `{"method", "params"}` with sorted keys
  and compact separators, so object member order is irrelevant and every
  value is exact. `plugins/lazarus/scripts/lazarus_lib/verifier.py`
  `_verify_rpc_coverage` requires the records to cover the plan's requests
  exactly and the manifest's `optional_failures` to equal the recorded error
  keys, which is why a fixture cannot quietly drop a request.
- `plugins/lazarus/examples/aave-v4-spoke-v0/` is the offline material. Its plan
  names four required `recorded-rpc` requests at block `0x18ac22c`, hash
  `0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc`, and
  one proof target with slot `0x0`. `rpc.jsonl` holds the record
  `aave-spoke-slot-zero`, `eth_getStorageAt
  ["0x973a023a77420ba610f06b3858ad991df6d85a08","0x0","0x18ac22c"]`, request
  key `5552a66c5b132aaf501e0a8aed28909a7efabfb87273283d0b74c241c4e41e76`,
  result `0x` followed by sixty-two zeros and `01`. `optional_failures` is
  empty, so the fixture records no provider error. `demo.py` already treats
  slot `0x1` as the observed miss, and `plugins/lazarus/tests/test_aave_v4.py`
  pins the digest, the slot value and the miss code, while
  `test_no_network.py` patches `socket.socket.connect` to refuse any
  destination that is not loopback. The example test reuses those two idioms
  and adds nothing under `plugins/lazarus/`.
- `plugins/lazarus/docs/chain-anchors.md` shows the operator convention the
  procedure follows: the URL value comes from the shell environment, as
  `--rpc-url "$PRIMARY_RPC_URL"`, and anchor URLs never enter argv at all.
- `plugins/hexaemeron/tests/run_tests.py` discovers `test_*.py` beside it,
  prints `N/N tests passed` counting only failures and errors against the
  total, and writes the `elenchus.unittest.v1` report with a `skipped`
  counter when given a path. `plugins/hexaemeron/tests/test_elenchus_checker.py`
  `NodeReports.setUpClass` runs `node --version` and one test asserts the
  pinned `v26.6.0`; `test_evolution.py` and `tests/test_evolution_contract.py`
  hold the generation-row rules this ledger change must satisfy;
  `test_fiat_skill.py` `PhaseSkillInventoryTests` derives the README count
  of phase skills with a script and is unaffected.
- `tests/promise_machine_coverage.json` binds the five `elenchus-*` cases to
  selectors in `test_elenchus_checker.py` and the runtime digest to
  `elenchus.py`; none of those files changes, so no selector moves.
- `plugins/berean/scripts/berean_lib/reads.py` consumes read records "in the
  Lazarus preservation shape", recomputes the same request key and refuses
  an error outcome without `code` and `message`. It is the one consumer in
  the repository that already treats a Lazarus record as a fixed answer.
- Version surfaces: `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`
  read `1.6.1`, pinned by `tests/test_version_propagation.py`
  `DELIVERY_PACKAGE_VERSIONS` and `test_hexaemeron_version_reaches_both_marketplaces`.
  `plugins/hexaemeron/tests/test_issue_429_recovery.py` also names `1.6.1`,
  but as historical product constants compared against `git show` of a fixed
  commit, not against the live manifests, so a bump does not reach it. Three
  commits moved the package with a skill change: `9385328` to `1.5.5` with
  `elenchus-v1.2.0`, `69b8b42` to `1.6.0`, `c4d3d3c` to `1.6.1`; the Phylax
  wish delivery `3766c51` did not move it.

The last two merged pull requests that changed
`plugins/hexaemeron/skills/elenchus/` were read before the options below were
drawn, and the run that built the mechanical subset was read with them:

- PR #596, `docs: refresh the Shoggoth collective map`, merged 2026-08-24 at
  `8e64802`. Its one Elenchus commit, `43babf2`, changed `SKILL.md` by seven
  insertions and two deletions: the "Where this sits" paragraph now names
  Mason, Warden, the Pashov suite and Metron, and a `**Current state.**` line
  was added. Its body
  carries nothing forward; the five Pashov surfaces are named and unchanged.
  This study keeps both additions as they are.
- PR #493, `record Elenchus verdicts on Fiat audit fixes`, merged 2026-08-23
  at `ced4e6f`, landed `elenchus-v1.2.0`. Its carried-forward list, item by
  item: issue #429 (audit schema and synopsis) is now closed, delivered by
  the #552 recovery, and its rule that a consumer preserve the optional
  `elenchus_verdict` field is untouched here; issue #453 (report-byte binding
  and a production `guarded` gate) stays open and is refused by name, because
  this run records nothing new about how a verdict is bound; issue #369 (the
  study-source consumer) is closed, and its delivery is the Protasis 4.8.0
  synopsis rule this study read its audit sources under, so nothing is
  carried; issue #363 remains Fiat's held frontier and is not moved.
- PR #196, `Classify Elenchus guards from runner reports`, merged 2026-08-19
  at `0b1b71c`, built the report adapters. Its two audit findings, the
  inherited `ELENCHUS_REPORT_FILE` variable and the report-size race, were
  fixed in that run and are recorded closed. Nothing is open from it.

The in-scope audit records were read the same way.
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited 0 from the target root with all fourteen source and synopsis pairs at
`committed=match`, so a synopsis was an allowed reading view; where a synopsis
line carried `[missing legacy field: ...]` for the field this study needed,
the source was read instead and is named as such.

- `audit/AUDIT.md`, sections `Elenchus structured reports, step 1, round 1`
  and `round 2` (2026-08-19): source read, because the root synopsis line
  drops the two unnumbered medium findings' text. Round 1 found the report
  path exported through `ELENCHUS_REPORT_FILE` and the stat-then-read race
  on the 1 MiB report bound, both fixed; round 2 recorded zero findings and
  `Leads not pursued: none`.
- `audit/AUDIT.md`, sections `Elenchus audit-round verdict`, step 1 rounds
  1 to 3, step 2 round 1, step 3 rounds 1 to 3 (2026-08-22): source read.
  Findings S1-R1-01 (report containment, fixed, verdict `passed`), S1-R2-01
  and S1-R2-02 (descriptor rebinding and the unnamed missing primitive, fixed
  in `cc984ba`), S3-R1-01 and S3-R1-02 (proof hashes without retained bytes,
  trailer paragraphs, fixed in `d55da516`, verdict `unguarded`), S3-R2-01 and
  S3-R2-02 (proof depending on untracked state, trailer claim scope, fixed in
  `27f78d96`, verdict `unguarded`); every risk id disposed in each round.
  Leads not pursued that bear on this change: "Mechanical red-parent
  classification for an implementation under a test directory remains an
  evidence discrepancy; changing Elenchus's test-file boundary is outside
  step 1, and issue 453 owns the blocking policy." This study accepts that
  boundary and uses it: the new module sits under `plugins/hexaemeron/tests/`
  and its prose assertions are what fail on the parent.
- `audit/AUDIT.md`, sections `Aave v4 preservation release`, steps 1 to 5,
  twenty rounds (2026-08-19 to 2026-08-20): source read, because seventeen of
  the twenty synopsis lines carry `[missing legacy field: leads-not-pursued]`.
  L1-R1-01 (hollow identifier strings, fixed with `text.py`) is the one
  tabulated finding; the later rounds record their findings in prose, all
  fixed in the round that found them, and steps 4 and 5 establish the facts
  this example relies on: the shipped Aave v4 fixture verifies, releases,
  reads back and passes every drift guard, and both demonstrations exit 0.
  The leads not pursued concern a split earlier audit record and probes that
  missed their targets; none concerns replay.
- `audit/rounds/fiat-386-record-a-structured-multi-provider-chain-anc.md`
  and its `.synopsis.md` (2026-08-25): both read. Three rounds, zero
  findings, every changed path reviewed against that study's register; the
  step 3 round records Lazarus 414/414, Aave v4 at
  `d93cd09f...`, the anchored fixture at `188eb293...`, and `Leads not
  pursued: none`. Its step 1 and step 2 leads were owned by later steps of
  the same run and closed there.
- `plugins/hexaemeron/audit/AUDIT.md` and `AUDIT_SYNOPSIS.md`: both read.
  Findings F-01 to F-09 fixed with regression tests, F-10 accepted as
  documented escape hatches of `hook_gate.py`; leads not pursued were
  `os.replace` atomicity across filesystems, concurrent `hexctl` invocations
  and ANSI passthrough in `status --json`. None touches this change.
- `audit/AUDIT.md`, sections `Ariadne state-fixture predicate` (2026-08-19),
  name Lazarus fixtures as the subject Ariadne binds. They belong to a skill
  outside this run's scope; headings only were read.

This run's own record, `audit/rounds/fiat-387-pin-rpc-boundary-failures-into-lazarus-fixtu.md`,
does not exist yet; Fiat derives it at the first round with its synopsis
sibling.

Three ledger precedents shape the bookkeeping. `elenchus-v1.2.0` is the row
shape being followed: a generation row on the mature frontier whose evidence
column links the study and the runner fixture and whose change column names
what the run did and did not claim. `phylax-v1.3.0` is the mature-frontier
generation the model study `docs/phylax-unsafe-deserialization/study.md`
recorded; `berean-v0.2.0` in `docs/berean-question-spans/study.md` is the
most recent receipted wish run and the register this study mirrors.

### in the organisation

`gh search code --owner wildcat-finance` for `32070` and for `lazarus replay`
returns files in this repository only: the Lazarus plugin's own sources,
tests, docs and examples, and `plugins/berean/tests/test_reads.py`. No other
public repository starts `lazarus replay` or handles its miss code, so no
downstream guard test exists to copy from and none needs a migration note.
The search says nothing about private or unindexed repositories.

### outside the organisation

- The JSON-RPC 2.0 specification reserves `-32000` to `-32099` for
  implementation-defined server errors and fixes `-32601` as method not
  found. Lazarus's `-32070` sits inside the reserved range, which is why a
  client can tell a miss from a provider fault by code alone.
- VCR.py's record mode `none` raises `CannotOverwriteExistingCassetteException`
  when a request has no cassette match. That is the same stance as a Lazarus
  miss and the nearest widely used precedent for "an unrecorded exchange is a
  test failure, not a live call". It differs in what a cassette proves:
  nothing about the bytes, where Lazarus binds digests and proofs.
- Foundry's fork cache, as the Lazarus study records from `foundry-fork-db`,
  schedules a provider request on a miss and writes the answer back. That is
  the opposite stance, and it is the reason a guard test behind a fork cache
  does not satisfy Reproduce.
- Python's `unittest` counts a skipped test in `testsRun`, reports it
  separately and leaves `wasSuccessful()` true. That is why a dependency skip
  must name its reason, why the Hexaemeron runner's `N/N tests passed` line
  can read clean over a skip, and why the demo path runs the module under
  `uv`, where the skip cannot occur. `importlib.util.find_spec` locates a
  module without importing it, which is the probe the skip uses.
- EIP-1186 and EIP-1898 are the proof and block-selector standards the
  Lazarus study already cites; nothing here changes what a fixture proves.

## 3. constraints and non-goals

### constraints

- Start from `main` at `ab611eb96a6a9bddecb57bff2416641296e0a21e` and stay
  within issue #387.
- The Elenchus skill file stays one hosted instruction file: its frontmatter
  `name` and `description`, its `## Where this sits` paragraph with the
  `**Current state.**` line, its six triage steps, its mechanical subset and
  its Promise Machine contract section keep their current text. The new
  section, the one Environment sentence and the one checklist item are the
  whole prose change; `metadata.version` reads `1.3.0`.
- The procedure describes only what `lazarus-v1.2.0` does. Every command it
  prints exists in `plugins/lazarus/scripts/lazarus.py` today, every
  behaviour it states is one `capture.py`, `rpc.py`, `scrub.py`,
  `replay.py` or `server.py` implements, and the worked example runs against
  the checked-in `aave-v4-spoke-v0` fixture through that command line.
- Nothing under `plugins/lazarus/` changes: no source, test, schema, example,
  document or ledger byte. The Lazarus frontier `receipt-inclusion-proofs`
  and its held job are not moved.
- The example test module imports the standard library only. It spawns the
  Lazarus command line with `sys.executable`, a fixed argument list, no
  shell, the repository root as working directory and `--port 0`; it reads
  the bound port from the printed listening line; it patches
  `socket.socket.connect` to refuse any destination that is not loopback for
  the duration of its HTTP calls; and it terminates the server on class
  teardown with a bounded wait and a kill fallback.
- The dependency probe checks the import names `eth_hash`, `Crypto`,
  `jsonschema`, `rlp` and `trie` with `importlib.util.find_spec` in the
  interpreter that will run the subprocess, and skips the replay class with a
  reason that names every missing name and the exact `uv run` command. The
  probe installs nothing, reaches no network and never turns a missing
  dependency into a pass. The stdlib tests in the same module always run.
- The ledger records `elenchus-v1.3.0` as a generation row retaining
  `observed-failure-root-cause`, digest
  `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`, status
  `mature` and `Next Fiat job: None -- mature`; the row's evidence links the
  example module and the committed study; `tests/test_evolution_contract.py`
  and `plugins/hexaemeron/tests/test_evolution.py` pass unchanged.
- The package version reads `1.6.2` in
  `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`,
  with the pin in `tests/test_version_propagation.py` moved to match. The
  reason is `plugins/hexaemeron/skills/fiat/references/plugin-currency.md`:
  the git-backed installer copies a plugin only when its declared package
  version changed, and an installed `1.6.1` would keep an Elenchus that says
  nothing about fixtures while the repository's says otherwise. The Elenchus
  generation in `9385328` moved the package for the same reason; the Phylax
  wish did not because its change was a lint run from source.
- Committed copies of the receipted study and runbook live at
  `docs/elenchus-rpc-boundary-fixtures/study.md` and
  `docs/elenchus-rpc-boundary-fixtures/runbook.md`.
- The root suite runs green here on 3.9.6 and 3.12.13, and CI's janus,
  lazarus and pandects workflows run it on 3.9, 3.11 and 3.13 whenever
  `tests/**` changes, so the version pin, the ledger change and the skill
  file's prose lint are exercised there. The Hexaemeron suite has no
  workflow, so the example is exercised by the demo path and the audit
  rounds, not by CI. The new module therefore uses no syntax newer than 3.9.

### non-goals

- Performing a live capture in any test, fixture builder or demo. A capture
  needs a provider URL; the study describes the capture half as procedure
  with exact commands and demonstrates the offline half.
- Committing a new Lazarus fixture. The Aave v4 fixture already ships,
  verifies and carries the two outcomes the example needs; a synthetic
  fixture carrying a recorded provider error is option D below and is
  rejected there.
- Changing Lazarus: no new command, flag, output line, error code, schema,
  example or test, and no edit to its docs. The `-32070` payload, the
  listening line and `--port 0` are used as they are.
- Widening the `elenchus-fixed-and-guarded` promise. Its Evidence clause
  already demands "the reproduction command and output", which a replay-backed
  reproduction supplies; a Boundary clause about Lazarus evidence classes
  would make a claim Elenchus does not verify.
- Adding a CI workflow for the Hexaemeron suite, changing the three existing
  workflows, or adding a dependency to Hexaemeron.
- Pinning the Aave v4 fixture digest as an assertion in the example. The
  example asserts the recorded slot value and the miss, and names the digest
  in its docstring, so a Lazarus recapture that keeps those answers does not
  break the Hexaemeron suite; the reason is recorded in section 4.
- Changing the Hexaemeron README, the root README or the promise-machine
  router. The Elenchus frontier text they carry does not move, and the one
  line each gives the skill stays true.
- The held Lazarus frontier (#383), the Foundry replay profile (#384), the
  recording proxy (#385), issue #453's report-byte binding, and any other
  plugin.

### explicit unknowns

- Whether Fiat wants the package bump in this generation. Assumption 5 says
  yes for the reason above; a veto removes five one-line edits and nothing
  else.
- Whether the root `docs/` location or `plugins/hexaemeron/docs/` is wanted
  for the committed copies. Assumption 8 follows the two most recent wish
  runs; a veto moves two files and one ledger link.
- Whether the audit machine has `uv` and Node 26 available through `npx`. It
  does here; the runner contract in section 11 depends on both, and a Warden
  without them would see the replay class skip by name and the Node fixture
  fail, which the audit record would then carry as environment evidence.
- Whether the operator will import public key
  `636EC19DE45DF10F3CE6206F57742DA1ABED6F46` before the audit rounds. This
  study proceeds on the reading that the key stays absent: the runbook's exit
  text for the Hexaemeron suite reads `1168` run, zero failures and at most
  that one named error, and the Elenchus verdict Warden records over the
  whole suite is `inconclusive` with the cause named. If the key is imported
  the same commands exit zero and the verdict can be `guarded`; nothing else
  in the build changes.
- Private organisation repositories cannot be searched from here.

### operating boundaries

**Always.** Observe the stdlib prose tests red against the current skill file
before adding the section. Run the example module on both `python3` and
under `uv`, the Lazarus suite under `uv`, the Hexaemeron suite under the Node
26 wrapper, the root suite, `tests.test_evolution_contract`,
`scripts/promise_machine.py check` and `coverage --check`,
`audit_synopsis.py --check .`, the Protasis checks on both committed copies,
Imprimatur and Brevitas on every changed Markdown file, the Phylax, Ephoros
and Hypomnema tree lints, the Horos check and `git diff --check` before any
commit. Confirm `git status --porcelain -- plugins/lazarus` prints nothing.

**Ask first.** Change any byte under `plugins/lazarus/`; add a dependency to
Hexaemeron or a third-party import to its tests; touch CI; change a promise
clause, the frontmatter description or the `## Where this sits` paragraph;
change any frontier field of either ledger; move the package version anywhere
other than `1.6.2`; commit a fixture; put a URL in a test.

**Never.** Run a live capture from a test or a demo; put an endpoint URL, a
credential or a provider error string in a script, a fixture, a test or a
commit; turn a missing dependency into a pass or a `-32070` miss into a zero;
delete or skip a failing test to make a suite pass; edit a vendored directory;
claim a command ran when it did not.

Expected implementation and record paths are:

- `plugins/hexaemeron/skills/elenchus/SKILL.md` and
  `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`.
- `plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py`.
- The five version surfaces named above.
- `docs/elenchus-rpc-boundary-fixtures/study.md` and
  `docs/elenchus-rpc-boundary-fixtures/runbook.md`; the audit file Fiat
  derives under `audit/rounds/` with its synopsis; `.horos/boundary.json`
  only if its scan changes, which small text files do not cause.

## 4. design options

### option A: a section in the skill file and one guard test against the shipped fixture (chosen)

The procedure becomes a new second-level section of
`plugins/hexaemeron/skills/elenchus/SKILL.md`, placed after "### 6. Verify"
and before "## Three rounds, then stop", titled "Pin an RPC-boundary failure
into a fixture". It opens by saying when the section applies: Localise named
the RPC or fixture boundary, and the failure needs a live endpoint's answer to
appear, so Reproduce cannot be satisfied against that endpoint. It then gives
the steps, each against what Lazarus does:

1. Name the exact exchange: the JSON-RPC method and its parameters as the
   test sent them. Read them from the client's request, or run the test once
   against `lazarus replay` on any existing fixture and read the `-32070`
   error's `data.method`, `data.params` and `capture_plan_fragment`, which
   is a plan entry ready to paste.
2. Write the plan: `schema_version` 1 or 2, chain `0x1`, the fixed block
   `number`, `hash` and `hash_source`, the request with a name, the exact
   method and parameters, `evidence: recorded-rpc` unless a state read is
   also a proof target, and `required`. Mark it `required: true` when the
   test needs the provider's answer. Mark it `required: false` when the
   failure to pin is the provider's error itself, because Lazarus records a
   required request's error as a capture failure and leaves no fixture, and
   records an optional request's error as a sanitised record whose message is
   `provider request failed` and whose code is the provider's when it sent
   one and `-32000` otherwise. Declare `limits`, including
   `max_elapsed_seconds`.
3. Capture with the endpoint URL held in the shell environment and nowhere
   else, `python3 plugins/lazarus/scripts/lazarus.py capture --plan
   plan.json --rpc-url "$LAZARUS_RPC_URL" --out <fixture>`, and for plan v2
   one `--anchor-rpc-env SOURCE_ID=ENV_VAR` per declared source. The URL
   value passes through the shell into the capture process only; Lazarus
   scans every staged byte for it and every secret in it and refuses to
   finalise if any is found; any failure leaves no fixture.
4. Verify with `python3 plugins/lazarus/scripts/lazarus.py verify <fixture>`
   and record the printed digest in the guard's docstring.
5. Guard: start `python3 plugins/lazarus/scripts/lazarus.py replay <fixture>
   --port 0` as an argv-pinned subprocess, read `lazarus replay listening on
   http://127.0.0.1:<port>`, point the client at it, assert the recorded
   outcome exactly, result or sanitised error, treat `-32070` as a failed
   test and never as a zero, and stop the server when the test ends.
6. Commit the plan, the fixture and the test together. The test then runs
   with no provider wherever the Lazarus dependencies are installed, and
   skips by name where they are not.
7. Say what stays out of reach: a fixture holds one answer per request key,
   the one the capture saw, so a failure that exists only at the provider is
   pinned as that one recorded response and not as the provider's behaviour.
   A rate limit the provider answers as a JSON-RPC error object on an
   optional request becomes one sanitised record; an HTTP 5xx, a redirect, a
   timeout or a non-JSON body is a transport failure that ends the capture
   and is never a record; and values are exact, so `0x00` is a different
   request from `0x0`.

The section ends by naming the worked example,
`plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py`, and the
`uv` command that runs it in the marketplace checkout. The Reproduce step's
Environment bullet gains one sentence pointing at the section, and "Before
the fix is receipted" gains "A failure that crossed an RPC boundary was
reproduced from a verified fixture behind `lazarus replay`, and its guard
fails closed on a miss."

The worked example is one unittest module with three classes:

- `ProcedureTextTests`, standard library only, asserts the skill file carries
  the section heading, the `capture`, `verify` and `replay` commands, the
  `--port 0` spelling, the `-32070` code, the `required: false` rule, the
  `LAZARUS_RPC_URL` convention and the checklist item. Each assertion fails
  on the current tree, which is the red-then-green this generation owes, and
  the failing assertions are what Elenchus's parent overlay classifies as
  `guarded`.
- `LazarusDependencyGuardTests`, standard library only, exercises the probe
  helper with a fake finder and asserts the skip reason names every missing
  import name and the `uv run` command, so the skip path is itself tested
  on an interpreter that never takes it.
- `ReplayGuardExampleTests` probes the five import names in `setUpClass`
  and raises `unittest.SkipTest` with that reason when any is missing.
  Otherwise it spawns `[sys.executable,
  "plugins/lazarus/scripts/lazarus.py", "replay",
  "plugins/lazarus/examples/aave-v4-spoke-v0", "--port", "0"]` with the
  repository root as `cwd`, `stdin` closed, `stdout` and `stderr` piped,
  reads the first stdout line under a thirty-second deadline enforced by a
  timer that kills the process, and parses the port. Under a
  `socket.socket.connect` patch that refuses any non-loopback destination,
  its tests then assert: the answer to `eth_getStorageAt` for slot `0x0` at
  `0x18ac22c` equals the `outcome.result` of the matching `rpc.jsonl` record
  read with the standard library and equals the literal sixty-four hex
  digit word ending in `01`; slot `0x1` returns `error.code` `-32070`
  with `data.method`, `data.params` and a fragment whose `method`, `params`,
  `evidence` and `required` are the request's own and `recorded-rpc` and
  `true`, and no `result`; the spelling `0x00` for slot `0x0` is also a
  miss; `eth_sendRawTransaction` returns `-32601`; the argv carries no
  `://` and no `--rpc-url`; every observed connection went to loopback.
  `tearDownClass` terminates the process, waits ten seconds, kills it if it
  is still running, and closes the pipes.

The trade. The example demonstrates the offline half only: a recorded answer
asserted exactly and an uncaptured exchange refused. It does not demonstrate
a recorded provider error, because the shipped fixture carries none and this
study declines to fabricate one; that case is written as procedure and is
proved by Lazarus's own `test_capture.py`. The example depends on another
plugin's checked-in fixture and command line, so a Lazarus change to the
Aave v4 slot value or the miss payload would break a Hexaemeron test; the
coupling is kept to values Lazarus's own tests pin, and the fixture digest is
named in the docstring rather than asserted, so a recapture that keeps the
recorded answers keeps this test green. And the skill file grows by one
section of about forty lines, which is the cost of keeping the rule and the
procedure that satisfies it in one place.

### option B: a reference document beside the skill

Write the procedure as `plugins/hexaemeron/skills/elenchus/references/rpc-boundary-fixtures.md`
and have the skill file point at it. The skill file stays shorter, and the
loading rules already allow a linked reference. Rejected because the demand
the procedure answers, "make it happen reliably", sits in the Reproduce step,
and a reader who stops at the skill file would still not know that a live
endpoint cannot satisfy it; and because a second document about one rule is a
second place for the prose to go stale, which the frontier discipline in
`VERSIONING.md` names as the failure to avoid.

### option C: an example directory shipped inside the skill tree

Put the worked example under `plugins/hexaemeron/skills/elenchus/examples/`
so an installed copy of the skill carries it. Rejected because the example
needs the Lazarus command line and the Aave v4 fixture at a sibling path
that exists in this checkout and not in an installed plugin cache, where
Lazarus is a separate directory under its own version; a shipped example that
cannot run where it ships misleads. A file under the skill tree would also
need a second file under `tests/` to be exercised at all.

### option D: a synthetic committed fixture carrying a recorded provider error

Assemble a small fixture under `plugins/hexaemeron/tests/fixtures/`: the
Aave v4 header and schemas copied, a plan with one optional request, an
`rpc.jsonl` holding one `{"error": {"code": -32000, "message": "provider
request failed"}}` record, an empty `proofs.jsonl` and a manifest built with
`optional_failures`, plus a builder script and a regeneration test. It would
demonstrate the recorded-error case directly. Rejected because it commits
about thirty kilobytes of JSON whose provenance is a copy rather than a
capture, presents a fabricated failure as pinned evidence, couples the
Hexaemeron suite to Lazarus's manifest builder and schema bytes while that
plugin's frontier is open, and costs a builder, a regeneration guard and a
second verification path to audit. The recorded-error behaviour it would
show is already proved where it is implemented.

### option E: a fake provider and a capture round trip inside the test

Start a loopback fake JSON-RPC provider in the test, run `lazarus capture`
against it with a plan naming one optional failing request, then `verify` and
`replay` the result. It would exercise every step of the procedure offline.
Rejected because it puts a URL on a test's argv, doubles the example with a
second server that must satisfy capture's header bracketing and result-block
checks, and proves Lazarus's capture path, which `plugins/lazarus/tests/test_capture.py`
already proves with its own fake, rather than the Elenchus procedure.

Option A is the cheapest to comprehend that still meets the problem
statement: one section where the rule already sits, one test module that a
reader can copy into a project, both built from commands and payloads that
exist today. It gives up demonstrating a recorded provider error in exchange
for touching nothing under `plugins/lazarus/` and committing no new fixture
bytes.

Settled alongside the pick:

- The section title is `## Pin an RPC-boundary failure into a fixture`; it
  contains one fenced `bash` block with the `capture`, `verify` and `replay`
  commands and one fenced `json` block with a two-request plan fragment, one
  request `required: true` and one `required: false`.
- The skip reason is fixed text: `Lazarus dependencies are not importable
  from <sys.executable>: <names>; run under uv run --python 3.12.13
  --with-requirements plugins/lazarus/requirements.txt`. The probe does not
  read `plugins/lazarus/requirements.txt`; the five import names are a
  constant in the test, with a comment naming the four pins they come from.
- The listening line is parsed with the fixed prefix
  `lazarus replay listening on http://127.0.0.1:`; a first line that differs,
  or an empty read because the process exited, fails the class with the
  captured stderr in the message.
- The example's HTTP client is `http.client` on `127.0.0.1` with a five
  second timeout, one request per connection, as `demo.py` does.
- Every test in the replay class names the fixture digest
  `d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49` in the
  module docstring only.
- The generation row's change column says what the section and the example
  do, that the example demonstrates the offline half against the shipped
  Aave v4 fixture, that no Lazarus file changed, and that options B to E
  were rejected with their reasons summarised; its evidence column links
  `../../tests/test_elenchus_rpc_boundary_fixture.py` and
  `../../../../docs/elenchus-rpc-boundary-fixtures/study.md`, both
  relative to the ledger, so Hypomnema's H001 check resolves them.
- No ADR. The decision belongs to one governed skill, so the
  `elenchus-v1.3.0` ledger row is its standing record; section 12 has the
  detail.

## 5. risk register seed

```risk-register
replay-subprocess-argv | the argument list that starts lazarus replay from the example | the argv is a fixed list beginning with sys.executable with no shell no string command and no value read from the environment
replay-loopback-port | the address the replay subprocess binds and the address the example connects to | the server is started with --port 0 the port is parsed from the printed listening line and every observed connection destination is a loopback address
replay-teardown | the replay subprocess after the example ends | tearDownClass terminates waits with a bound kills on timeout closes the pipes and no server outlives the test run
provider-url-absent | the example test module and its subprocess argv | no URL no --rpc-url and no credential-named value appears in the module or the argv and Phylax P001 P002 and P004 report nothing
capture-credential-env | the documented capture command in the skill file | the endpoint URL is read from an environment variable only and the text says Lazarus scans staged bytes for it and refuses to finalise on a hit
dependency-guard-skip | the interpreter probe in setUpClass | each of the five import names is probed with find_spec the skip reason names every missing name and the uv command and no missing dependency produces a pass
recorded-response-exact | the eth_getStorageAt slot 0x0 assertion | the replayed result equals the rpc.jsonl record's outcome.result and the literal word and the comparison is on the exact string
miss-asserted-closed | the eth_getStorageAt slot 0x1 and 0x00 assertions | each response carries error.code -32070 with data.method data.params and a capture_plan_fragment and carries no result
write-method-refused | the eth_sendRawTransaction request in the example | the response is error.code -32601 and no write reaches the fixture
prose-guard-red-first | the ProcedureTextTests against the parent tree | every assertion fails on the unchanged skill file and passes on the changed one and the Elenchus overlay classifies the change guarded
no-lazarus-edits | every path under plugins/lazarus | git diff --stat against the base names nothing under that directory in any step
lazarus-frontier-untouched | plugins/lazarus/skills/lazarus/EVOLUTION.md | the file is byte-identical to the base and the held job text is unchanged
ledger-integrity | the elenchus-v1.3.0 generation row | revision and digest are byte-identical to v1.2.0 status stays mature the next job stays None -- mature and SKILL.md metadata.version matches
version-surfaces | the four package manifests and the propagation pin | every surface states 1.6.2 and test_version_propagation passes on 3.9.6 and 3.12.13
prose-matches-lazarus | every behavioural claim in the new skill section | each command flag output line error code and required-or-optional rule is checked against the lazarus.py capture.py rpc.py scrub.py replay.py and server.py sources at the base ref
error-text-is-data | the -32070 message and capture_plan_fragment the example reads | the payload is asserted and shown and no field of it is executed pasted into a command or written to a plan by the test
hexaemeron-stdlib-only | the import lines of the new test module | no third-party import appears at module level or inside the replay class and the module loads on 3.9.6 and 3.12.13
skip-visible-in-report | the elenchus.unittest.v1 report the runner writes | the skipped counter records the replay class when it skips and the demo path's uv run reports zero skipped
partial-run | an interrupted suite lint or replay subprocess | no receipt commit or clean claim rests on a command that did not exit zero and a killed replay leaves no listening socket
```

There is no funds arithmetic, upgrade path, signing key or persistent write in
this change. The one subprocess is the replay server, started from a fixed
argument list and stopped by the test; the one network path is loopback; the
one external input is the replay's JSON-RPC response, which the example
parses with `json` from a bounded body and treats as data. The audit should
look hardest at the four lines from `replay-subprocess-argv` to
`provider-url-absent`, because a test that starts a server is the boundary
Phylax exists for, and at `prose-matches-lazarus`, because a procedure that
misstates what `capture` does with a failing required request would send the
next agent to build a fixture that cannot exist.

## 6. glossary seeds

- `RPC-boundary failure`: a failure whose reproduction depends on what a
  live JSON-RPC endpoint answers, so it cannot be made to happen on demand
  against that endpoint.
- `exchange`: one JSON-RPC method with its exact parameters and the outcome
  the provider returned for it.
- `capture plan`: the Lazarus plan document naming the chain, the fixed
  block, each request with its `required` flag and evidence class, the proof
  targets and the limits.
- `required request`: a plan request whose provider error ends the capture
  with no fixture; `optional request`: one whose error is recorded as a
  sanitised error record and listed in the manifest's `optional_failures`.
- `sanitised error`: the record Lazarus keeps when an optional request is
  answered with a JSON-RPC error object: the provider's integer code or
  `-32000`, and the fixed message `provider request failed`. A transport
  failure is not sanitised into a record; it ends the capture.
- `request key`: SHA-256 over canonical JSON of the method and parameters;
  the exact lookup key replay uses, under which `0x00` and `0x0` differ.
- `replay miss`: the `-32070` error replay returns for a request key absent
  from the fixture, carrying the method, the parameters and a
  `capture_plan_fragment`.
- `capture-plan fragment`: the plan entry inside a miss, with
  `evidence: recorded-rpc`, a `replay-miss-` name, the method, the parameters
  and `required: true`, ready to be added to a plan.
- `listening line`: `lazarus replay listening on http://127.0.0.1:<port>`,
  the one line replay prints, after verification and before serving.
- `dependency guard`: the `find_spec` probe that skips the replay class by
  name when a Lazarus import is missing from the running interpreter.
- `generation row`: a ledger row that changes behaviour while retaining the
  frontier revision, digest, status and next job byte for byte.

## 7. sources and checks

- Task and base: issue #387,
  <https://github.com/wildcat-finance/skills/issues/387>, milestone `Wave 4
  -- historical fixtures and replay`, and `main` at
  `ab611eb96a6a9bddecb57bff2416641296e0a21e`. Peer issues #383, #384, #385
  open and #386 closed on 2026-08-25.
- Repository authority, Elenchus: `plugins/hexaemeron/skills/elenchus/SKILL.md`,
  `EVOLUTION.md`, `scripts/elenchus.py`, `agents/openai.yaml`;
  `plugins/hexaemeron/tests/test_elenchus_checker.py`, `run_tests.py`,
  `test_evolution.py`, `test_fiat_skill.py`; `tests/test_evolution_contract.py`,
  `tests/test_version_propagation.py`, `tests/test_shipped_prose_lints.py`,
  `tests/test_marketplace_prose.py`, `tests/test_boundary_currency.py`,
  `tests/promise_machine_coverage.json`.
- Repository authority, Lazarus: `plugins/lazarus/AGENTS.md`,
  `skills/lazarus/SKILL.md` and `EVOLUTION.md`, `README.md`,
  `docs/study.md`, `docs/runbook.md`, `docs/chain-anchors.md`,
  `requirements.txt`, `requirements.lock`, `schemas/plan-v1.json`,
  `plan-v2.json`, `rpc-record-v1.json`; `scripts/lazarus.py`,
  `scripts/lazarus_lib/capture.py`, `rpc.py`, `scrub.py`, `records.py`,
  `replay.py`, `server.py`, `verifier.py`, `manifest.py`, `canonical.py`;
  `examples/aave-v4-spoke-v0/` with `demo.py`, `plan.json`, `manifest.json`,
  `rpc.jsonl`, `README.md`; `tests/test_aave_v4.py`, `test_no_network.py`,
  `tests/run_tests.py`, `tests/support.py`.
- Contracts: `plugins/hexaemeron/skills/VERSIONING.md`,
  `plugins/hexaemeron/skills/fiat/references/plugin-currency.md`,
  `plugins/hexaemeron/skills/{ephoros,phylax,metron,elenchus,hypomnema}/SKILL.md`,
  root `AGENTS.md`, `plugins/hexaemeron/AGENTS.md`, `.horos/boundary.json`,
  `.github/workflows/{janus,lazarus,pandects}.yml`, and the Protasis contract
  at its installed path, version 4.8.0.
- Change history: merged PRs #596, #493 and #196; commits `43babf2`,
  `b8acf61`, `7411f8b`, `c981f30`, `9385328`, `69b8b42`, `c4d3d3c`,
  `3766c51`; `audit/AUDIT.md` sections `Elenchus structured reports`,
  `Elenchus audit-round verdict` and `Aave v4 preservation release`;
  `audit/rounds/fiat-386-record-a-structured-multi-provider-chain-anc.md`;
  `plugins/hexaemeron/audit/AUDIT.md`.
- Precedent studies and ledgers: `docs/berean-question-spans/study.md`,
  `docs/phylax-unsafe-deserialization/study.md`,
  `plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md` and
  `runbook.md`, `plugins/hexaemeron/docs/elenchus-structured-runner-reports/study.md`,
  `docs/lazarus-multi-provider-chain-anchor/study.md`,
  `plugins/hexaemeron/skills/phylax/EVOLUTION.md`,
  `plugins/berean/skills/berean/EVOLUTION.md`.
- Outside: the JSON-RPC 2.0 specification at
  <https://www.jsonrpc.org/specification>; VCR.py record modes at
  <https://vcrpy.readthedocs.io/en/latest/usage.html>; Python `unittest`
  skipping at
  <https://docs.python.org/3/library/unittest.html#skipping-tests-and-expected-failures>
  and `importlib.util.find_spec` at
  <https://docs.python.org/3/library/importlib.html#importlib.util.find_spec>;
  EIP-1186 and EIP-1898 as cited by the Lazarus study.

Checks run for this study:

- `git rev-parse HEAD`, `main` and `origin/main` each returned the base
  commit above; `git status --porcelain` was empty before this file was
  written; `git worktree list` showed the operator checkout and this run's
  worktree both at that commit.
- `python3 -m unittest discover -s tests` ran 396 OK;
  `tests.test_evolution_contract` ran 9 OK; `scripts/promise_machine.py check`
  printed `clean: 14 plugin(s), 14 copy/copies`; `coverage --check` printed
  `clean: promises=71 coverage_rows=71 coverage_selected=71`.
- `audit_synopsis.py --check .` exited 0 with fourteen pairs at
  `committed=match`.
- `uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt
  python -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus`
  ran 414 OK in 34.7 seconds; plain `python3` on the same discover collected
  91 tests and errored 15 times on `ModuleNotFoundError`; the Aave v4
  `demo.py` printed all eight lines including `slot 0x1 miss: -32070` and
  `verify` printed digest `d93cd09f...`, `proof-backed: 2`, `header-bound: 1`,
  `recorded-rpc: 4`, both under `uv`.
- `python3 plugins/hexaemeron/tests/run_tests.py` ran 402 seconds and
  reported `1166/1168 tests passed`, `FAILED (failures=1, errors=1)`. The
  failure is `NodeReports.test_fixture_exercised_the_declared_node_version`,
  `'v26.6.0' != 'v22.22.3'`, the host `node` being v22.22.3. The error is
  `Issue429RecoveryTests.test_composition_has_exact_parent_order_and_signed_header`:
  `git verify-commit 0fb3bcfba14a36c623f380105504d41d1eb66c86` exits 1 with
  `gpg: Signature made ... using EDDSA key
  636EC19DE45DF10F3CE6206F57742DA1ABED6F46` and `gpg: Can't check signature:
  No public key`; `git log --format=%G?` shows `E` for that commit; the same
  command exits 1 in the operator checkout. Under
  `npx --yes --package=node@26.6.0 --call` the suite reported `1167/1168`
  in 405 seconds with only that error. `/usr/bin/python3` reported 647/1153
  with 393 failures and 113 errors and is not a Hexaemeron gate.
  `/usr/bin/python3 -m unittest discover -s tests` printed `OK`.
- Under `uv`, `lazarus.py replay plugins/lazarus/examples/aave-v4-spoke-v0
  --port 0` printed `lazarus replay listening on http://127.0.0.1:51711`
  within 0.1 seconds; `eth_getStorageAt` slot `0x0` returned the sixty-four
  digit word ending in `01`; slot `0x1` returned `-32070` with the fragment
  named `replay-miss-98fb2cd56aae`; `eth_sendRawTransaction` returned
  `-32601`; an `eth_getLogs` object parameter with reordered keys matched;
  slot `0x00` was a miss; SIGTERM ended the process with status `-15` and
  empty stderr.
- Plain `python3 lazarus.py replay ...` and `verify` both fail at
  `lazarus_lib/schemas.py` line 11 with `ModuleNotFoundError: No module named
  'jsonschema'`; `importlib.util.find_spec` reports all five of `eth_hash`,
  `Crypto`, `jsonschema`, `rlp`, `trie` absent on `python3` and present
  under `uv`.
- The frontier line recomputed to
  `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`, the
  digest in the ledger's `elenchus-v1.1.0` and `elenchus-v1.2.0` rows.
- `gh search code --owner wildcat-finance` for `32070` and `lazarus replay`
  returned this repository only.
- The Protasis checker printed `clean` and Imprimatur and Brevitas exited 0
  on `docs/berean-question-spans/study.md`, the register this study mirrors;
  the installed `protasis.py` and `imprimatur.py` are byte-identical to the
  worktree copies.

These checks establish the current state, the absent procedure and a
buildable example. They do not establish that option A is implemented, that
its tests pass, or that a pinned fixture reproduces any particular project's
failure.

## 8. signals and the questions behind them

`plugins/hexaemeron/skills/ephoros/SKILL.md` adds no telemetry gate here.
Nothing in this change runs unattended: the skill file is read by an agent,
the example is a test that starts and stops a loopback server, and Lazarus's
own signals are not changed. The step keeps three signals that already exist
and tests two of them:

1. "Which exchange did the test need that the fixture lacks?" The `-32070`
   error's `data.method`, `data.params` and `capture_plan_fragment` answer
   it, and the example asserts all three for slot `0x1`.
2. "Did the guard talk to the fixture it was written against?" The
   listening line names the loopback address and port the test parsed, and
   `verify` prints the fixture digest the procedure tells the author to
   record; the example asserts the line's prefix and names the digest.
3. "Did the example run or skip?" The unittest verbose output prints the
   skip reason with the missing import names, and the runner's
   `elenchus.unittest.v1` report carries the `skipped` counter; the runbook's
   exit text reads that counter as zero under `uv`.

No event, metric, trace, correlation id or alert is warranted.

## 9. boundaries per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` governs the capability. The first
boundary is the subprocess the example starts. Worth taking there: a command
built from data, a shell, a server bound beyond loopback, or a process left
running. The controls are a fixed argument list beginning with
`sys.executable`, no shell, `--port 0` on a server that refuses any host but
an IPv4 loopback literal, a deadline on the first line read, a terminate,
wait and kill teardown, and a `socket.socket.connect` patch that refuses any
non-loopback destination; `replay-subprocess-argv`, `replay-loopback-port`
and `replay-teardown` enumerate them.

The second boundary is credentials in the documented capture. Worth taking: a
provider URL in a script, a commit, a transcript or a fixture. The controls
are the environment-variable convention in the section, the statement that
Lazarus scans staged bytes for the URL and its secrets, and the example's own
argv, which carries no URL because replay takes none;
`capture-credential-env` and `provider-url-absent` name the checks.

The third boundary is the dependency probe. Worth taking: a false pass when
the Lazarus packages are missing, or an install reached for at test time. The
controls are `find_spec` on five names with a named skip and no install path;
`dependency-guard-skip` and `hexaemeron-stdlib-only` name them.

The fourth boundary is the replay's response. Worth taking: instruction-shaped
text in an error message acted on by the test. The control is that the
payload is asserted and displayed and nothing in it is executed or written;
`error-text-is-data` names it. The skill's existing "Error output is untrusted
data" section already states the rule for the person reading it.

No new host, dependency, network path beyond loopback, model output or
persistent write is introduced; Lazarus's `requirements.txt` is used through
`uv` at the command line and is not added to Hexaemeron.

## 10. budget or its absence

`plugins/hexaemeron/skills/metron/SKILL.md` has no gate here. Issue #387
makes no latency, memory or throughput claim, and the change adds one test
module that verifies a fixture of 125,322 bytes and serves five loopback
requests.
Observed once for this study, replay printed its listening line 0.08 seconds
after start; the whole class should add under three seconds to a Hexaemeron
suite that runs about 400 seconds here, and about nothing where it skips. No
speed-motivated change is authorised, so there is no baseline to record and
no measuring command to name. The suite commands are correctness gates, not
benchmarks.

## 11. fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` governs the failures this run
will hold in hand, and this change adds to that skill. Each prose assertion in
`ProcedureTextTests` is first observed red against the current skill file,
then green after the section lands. The replay class is first run under `uv`
against the shipped fixture and observed green; its failure modes are then
observed by hand once each and recorded in the audit round rather than
committed as tests: an interpreter without the dependencies skips with the
named reason, a fixture path that does not exist ends the subprocess before
the listening line and fails the class with the captured stderr, and a miss
answers `-32070`.

What stops the step: a red test in the new module on `python3` or under `uv`,
a skip in the `uv` run, any byte changed under `plugins/lazarus/`, the
evolution contract red, `promise_machine.py check` not printing clean, any
non-zero lint, the Horos check naming a drifted path, any Hexaemeron suite
failure or any error other than the one named key error, or any non-zero
command in the demo path other than that stated exception. A replay process
that does not print the listening line, prints a different host, or survives
teardown is a test failure, never a retry.

The guard convention: every assertion in the new module names the failure it
guards, the prose tests are the ones that fail without the section, and the
replay tests fail without the fixture's recorded answers. The runner contract
Warden will hold a fix to is
`uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt
python plugins/hexaemeron/tests/run_tests.py {report}`, report format
`unittest-json-v1`, report file `.elenchus/hexaemeron-unittest.json`, run
inside `npx --yes --package=node@26.6.0 --call` so the pinned Node fixture
passes; the `uv` spelling is chosen over plain `python3` so the replay class
runs rather than skips in the report Warden reads. On the parent overlay the
prose assertions fail, which is the assertion failure `classify` reads as
`guarded`; a report with the replay class skipped still records executed
tests. `classify` returns `inconclusive` before it looks at assertion
failures whenever the report records an error, so while the key error above
stands on the audit machine every verdict over the whole suite is
`inconclusive` with that cause, and the round records it as such rather than
relabelling it. The guard is still observed red by hand on the parent and
green on the fixed tree, and the round records both runs.

## 12. decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` puts a decision about one
governed skill in that skill's ledger. The expensive-to-reverse decision here
is that Elenchus names Lazarus as the way an RPC-boundary failure is
reproduced, with the required-or-optional rule and the fail-closed miss as
the procedure's terms: once agents follow the section, a later change to
where the procedure sits or what it prescribes rewrites a working habit. Its
standing record is the `elenchus-v1.3.0` row in
`plugins/hexaemeron/skills/elenchus/EVOLUTION.md`, whose change column names
the section, the example, the offline-half boundary and the rejected
constructions, and whose evidence column links the example module and the
committed study that holds options B to E in full.

`SKILL.md` owns the procedure text and the checklist item; its
`metadata.version` moves to `1.3.0` with the ledger. The package bump and its
reason go in the step's commit message, which is where this repository
records what shipped, and in section 3 above. Lazarus's own documents are the
authority on what `capture`, `verify` and `replay` do and are not duplicated;
the section cites their commands and behaviour at `lazarus-v1.2.0`, and a
Lazarus change that alters them is that plugin's frontier run's
reconciliation obligation under `VERSIONING.md`.

No repository-wide ADR is warranted: the change adds no shared schema,
dependency, storage format or cross-plugin ownership decision, and the
existing records under `docs/decisions/` concern the Promise Machine, Fiat,
identity, release mechanics and the boundaries between skills, not the
internal procedure of one skill. Exact
committed copies of the receipted artefacts belong at
`docs/elenchus-rpc-boundary-fixtures/study.md` and
`docs/elenchus-rpc-boundary-fixtures/runbook.md`; the audit rounds go to the
file Fiat derives under `audit/rounds/`.

If implementation needs a change under `plugins/lazarus/`, a committed
fixture, a new dependency, a promise clause, a different package version or a
CI workflow, amend this study before code. A generation row cannot silently
widen a mature skill's claim or another skill's frontier.
