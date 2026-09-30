# Study: statements past the 8 MiB limit

Issue [wildcat-finance/skills#1892](https://github.com/wildcat-finance/skills/issues/1892).
Run branch `fiat/1892-statement-parts`, cut from `main` at
`150943da240837040478a76c3611d150fa04f2b6`. Controller `fiat-v6.76.1`
(hexaemeron 1.6.90). Design record `.hexaemeron/design-evidence.json`, SHA-256
`071dcdb20c28a46fdd18933b4dcf31975d787b7c5581f2f092e5ecf00b3c2459`, selects
`statement-parts`.

## Assumptions

I proceed on these unless corrected.

1. The base is `150943da240837040478a76c3611d150fa04f2b6`. The interpreter is
   Python 3.14.6 from `.python-version`, with stdlib `unittest`. No dependency
   is added.
2. Ariadne does not change. Its default reader bounds are the contract every
   emitted file must meet: 8,388,608 input bytes and depth 64
   (`plugins/ariadne/scripts/ariadne_lib/safejson.py:18-19`), and the
   structured-key scan budget of 4,096 characters a key and 262,144 in
   aggregate (`plugins/ariadne/scripts/ariadne_lib/core_predicate.py:31`,
   `:38`). Ariadne owns those bounds; widening one is an Ariadne change, and
   the design below needs none.
3. Ariadne keeps the Alexandria predicates unregistered, so gates 2 and 5 stay
   visibly unchecked on every statement this run emits, as they are today.
4. A signed statement travels as one DSSE envelope whose payload is the
   statement's base64 encoding. A file Alexandria emits should still be
   readable by Ariadne's defaults after that 4/3 expansion.
5. A release whose single statement fits 8,388,608 bytes but passes the
   262,144-character key budget moves to the part form, and `--output`
   refuses it by name. Today such a statement is written and Ariadne's
   `verify` refuses it on gates 4 and 7. No pinned release is in that band:
   the largest, Wildcat V2, has 127 components and 32,749 key characters.
   This reading is the one open Decision below.
6. The part form is a new explicit output mode, `--parts <directory>`.
   `--output <file>` keeps its contract for every release within both bounds.
7. #1888's release limits do not change: 16,384 components, 16,384 captures,
   134,217,728 manifest bytes and 2,000,000 manifest nodes.
8. The two preserved Wildcat releases named in section 3 stay on the
   collecting host until integration.
9. #1891 changes `usdc_interval.py` build and check and none of the files this
   run changes except the shared version surfaces, the Alexandria ledger and
   the Horos census.

**Decision for Laurence, still open.** Assumption 5 changes what `--output`
does for a release of roughly 1,017 to 1,790 components at Wildcat V1's rate
(1,017 to 5,000 at V2's): today it writes a statement Ariadne refuses to
verify; after this run it refuses and names `--parts`. It also means Step 3
edits one #1888 test, `check_statement_beyond_the_old_limits` in
`plugins/alexandria/tests/test_release_limits.py`, whose 6,500-component
"fits" release (5,272,102 bytes, 1,423,591 key characters) would now refuse.
The alternative keeps today's bytes for that band and files the verify
failure as its own issue. The design record does not depend on the choice.

## 1. Problem statement, user, and the proving path

**What is built.** A statement for every release #1888's limits admit.
`alexandria.py statement` projects a verified release into one unsigned
in-toto Statement v1 and refuses a statement above 8,388,608 bytes
(`plugins/alexandria/scripts/alexandria_lib/statement.py:27`, `:155-159`).
The statement grows with every component, so a release past about 1,790
components at Wildcat V1's 4,686 bytes a component gets none.

A second limit binds first and nobody has named it. Ariadne's gates 4 and 7
scan every object key in the predicate and every subject's digest object
(`plugins/ariadne/scripts/ariadne_lib/gates.py:340-354`, `:578`, `:697`), and
refuse a statement whose keys pass 262,144 characters. An Alexandria statement
spends 257.8 key characters a component for Wildcat V1, 257.9 for V2 and
253.5 for Aave V3, so `verify` fails at about 1,016 components whatever the
byte count. Measured at the base: a synthetic 2,000-component release gives a
1,622,602-byte statement with 438,091 key characters, which `statement`
writes and `ariadne.py verify --max-bytes 1622602` refuses with exit 1 on
gates 4 and 7.

The releases that need this exist. #1872's run split the Aave V3 interval into
twelve segment releases on the collecting host. Projected in memory from their
manifests:

| Segment | Components | Statement bytes | Key characters | Parts under the design |
| --- | --- | --- | --- | --- |
| 0 | 5,471 | 30,052,348 | 1,386,913 | 6 |
| 1 | 5,471 | 40,467,937 | 1,386,913 | 8 |
| 2 | 5,471 | 40,477,501 | 1,386,913 | 8 |
| 3 | 8,199 | 60,685,673 | 2,078,461 | 12 |
| 4 | 3,399 | 25,126,654 | 861,661 | 5 |
| 5 | 7,195 | 53,237,375 | 1,823,947 | 10 |
| 6 | 8,699 | 64,382,085 | 2,205,211 | 12 |
| 7 | 6,583 | 48,705,386 | 1,668,805 | 9 |
| 8 | 8,211 | 60,760,631 | 2,081,503 | 12 |
| 9 | 6,423 | 45,917,299 | 1,628,245 | 9 |
| 10 | 6,583 | 36,286,981 | 1,668,805 | 7 |
| 11 | 10,391 | 54,694,307 | 2,634,133 | 11 |

Every segment passes both bounds today. The densest costs 7,402 statement
bytes a component (segment 3).

**For whom.** The operator who releases a large interval and hands its
statement to a signing step, and the stranger who later checks that statement
with Ariadne and no other tool.

**The design, in one paragraph.** A release whose single statement stays
within 8,388,608 bytes and 262,144 key characters keeps today's statement,
byte for byte. Any other release gets a part set: a directory holding
`index.json` and `part-00000.json` onwards. Each part is an in-toto Statement
v1 of predicate type
`https://ariadne.wildcat.finance/alexandria-release-part/v1` whose subjects are
the release and a contiguous run of components, carrying those components and
every capture that names them. The index is a Statement v1 of type
`https://ariadne.wildcat.finance/alexandria-release-parts/v1` whose subjects
are the release and each part file by SHA-256. Every part stays within
6,225,920 bytes and 262,144 key characters, so Ariadne verifies each file with
its defaults, bare or inside an unsigned DSSE envelope.

**The new limit.** A part holds at most 6,225,920 bytes and 262,144 key
characters.

- 6,225,920 is 6 MiB less 64 KiB. Its base64 encoding is 8,301,228 bytes,
  which leaves 87,380 bytes of an 8,388,608-byte envelope for the envelope's
  own fields and its signatures. A bare statement cannot pass the bound a
  signed one would miss.
- 262,144 is Ariadne's aggregate key budget. The emitter counts key characters
  exactly as gates 4 and 7 scan them: every object key under the predicate,
  plus every key of each subject's digest object.
- A part holds at least one component with all its captures. A component
  whose own part would pass either bound refuses by name, and nothing is
  written. That is the "statement past the new limit" the issue asks to keep
  refusing. The index holds at most 16,385 subjects, one release and one per
  part, since no part is empty. At 16,385 subjects it measures 1,950,336 bytes
  and 98,405 key characters, inside both bounds for every release #1888
  admits.

**Working prototype.** On a 16,384-component, 16,384-capture release at the
densest measured rate, `statement --parts` writes 20 parts and an index, and
`ariadne.py verify` exits 0 on all 21 files with its defaults.

**Success criteria.** Each is checked by a command.

1. *Acceptance fixture.* A synthetic release of 16,384 components whose single
   statement passes 8,388,608 bytes gets a part set, and `ariadne.py verify`
   exits 0 on the index and on every part with default bounds, bare and as an
   unsigned DSSE envelope. Test
   `tests.test_statement_parts.StatementPartProjectionTests.test_a_release_past_the_limit_projects_into_parts_ariadne_verifies`.
2. *Completeness.* Every component and capture lands in exactly one part, in
   manifest order, with the capture in the part that holds its component, and
   the index names every part by SHA-256. Tests
   `test_every_component_and_capture_lands_in_exactly_one_part_in_order` and
   `test_the_index_binds_every_part_by_digest` in the same class.
3. *Byte identity.* The eleven pinned statements in section 3 keep their
   SHA-256: `python3 .hexaemeron/design/conformance.py
   pinned-statements-keep-bytes --candidate statement-parts` exits 0.
4. *Refusal past the new limit.* A component whose own part would pass
   6,225,920 bytes or 262,144 key characters refuses by name, naming the
   component and the bound, and writes nothing. `--output` on a release past
   the single bounds refuses and names `--parts`; the byte refusal keeps its
   text, `release statement encodes to N bytes, above Ariadne's
   8388608-byte input limit`. Tests in
   `tests.test_statement_parts.StatementPartsCommandTests`.
5. *Recovery.* An interrupted or failed `--parts` run leaves no output
   directory, an existing target is refused unchanged, and a target inside the
   release or through a symlink into it is refused. Tests in the same class.
6. *Limits unchanged.* `ManifestLimitTests.PUBLISHED` in
   `plugins/alexandria/tests/test_release_limits.py` still holds every #1888
   value, and `MAX_STATEMENT_BYTES` stays 8,388,608.

**The proving demo path.** Build the heavy synthetic release, run
`python3 plugins/alexandria/scripts/alexandria.py statement <release> --parts
<directory>`, run `python3 plugins/ariadne/scripts/ariadne.py verify` on
`index.json` and each part, and compare each part's SHA-256 with the index
subject of the same name. Step 4 records that run in `proof.md`.

## 2. Prior art

### In this repository, verified at the base commit

- `plugins/alexandria/scripts/alexandria_lib/statement.py`: `statement_for`
  (`:67-129`) projects the manifest; `validate_projection` (`:132-138`)
  refuses a projection that is not exact; `emit_statement` (`:141-167`)
  verifies, encodes and refuses above `MAX_STATEMENT_BYTES` (`:27`, which is
  `MAX_CONTROL_BYTES`); `_prepare_output` and `_write_statement`
  (`:200-422`) confine and atomically install one regular file, re-verifying
  the release before the rename.
- `plugins/alexandria/scripts/alexandria.py:54-60` declares `statement
  <release> --output <file>`.
- `plugins/alexandria/docs/release-statements.md:17-19` promises that every
  successful output stays directly readable by Ariadne.
- `plugins/alexandria/schemas/release-statement-v1.schema.json` is closed;
  `SchemaDriftTests` in `plugins/alexandria/tests/test_statement.py` holds it
  to the emitter's field sets.
- `test_statement_limit_tracks_ariadne_bounded_reader` in
  `plugins/alexandria/tests/test_statement.py` reads Ariadne's
  `DEFAULT_MAX_BYTES` with `runpy` and requires `MAX_STATEMENT_BYTES` to
  equal it. The new bounds follow the same pattern against
  `MAX_STRUCTURED_KEY_CHARACTERS_TOTAL`.
- `plugins/alexandria/tests/test_release_limits.py` builds synthetic
  releases (`synthetic_manifest`, `write_synthetic_release`) and pins the
  byte refusal's exact text in `check_statement_beyond_the_old_limits`.
  `OutputBoundaryTests.near_limit_release` in `test_statement.py` builds one
  component carrying 33 captures of 256 gaps of 983 characters, the shape
  that exceeds any part.
- Ariadne reads one document per file: `load_document`
  (`plugins/ariadne/scripts/ariadne.py:52-78`) bounds the file, then
  `envelope.read` bounds the outer document and the decoded payload with the
  same loader. `--max-bytes` and `--max-depth` (`:459-472`) take any positive
  value, but the key budget has no flag.

### The last two merged pull requests that changed the subject

- [#1905](https://github.com/wildcat-finance/skills/pull/1905), merged
  2026-09-24 at `7b43f814f`, delivered #1888 and left the statement limit
  unchanged by decision. Its carryover row `release-statement-limit` filed
  this issue. Its other rows: `bounded-memory-build-and-check` is #1891, run in
  parallel; `check-reads-verified-bytes` is #1902; `durable-store-retrieval`
  is #1373; the six `none` rows concern that run's own records and resolver.
  None assigns work here.
- [#653](https://github.com/wildcat-finance/skills/pull/653), merged
  2026-08-26 at `f1458dcef`, delivered the statement emitter (#407). It
  carried forward: Ariadne does not register the Alexandria predicate, so
  gates 2 and 5 stay unchecked; statements are unsigned and publisher identity
  is not authenticated; provider completeness, finality and canonical-chain
  membership are not proved; hostile writers with permission on the output
  directory stay outside the boundary; JSON Schema proves shape, not the
  digest and count equalities. Each still holds for the part form and is
  restated in section 9 rather than reopened.

### Audit history

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root and exited 0 with 113 of 113 views
`committed=match`. The verified synopses were the reading view, searched for
statement, input-limit, key-budget and reader terms.

| Source | View read | Source SHA-256 prefix | Findings |
| --- | --- | --- | --- |
| `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.md` | its `.synopsis.md` | `ce1d705337f3f53c` | 4, all fixed: S1-R1-01, S1-R1-02, S1-R1-03, S1-R2-01 |
| `audit/rounds/fiat-1888-epoch-table-split-and-release-caps.md` | its `.synopsis.md` | `204e233e8c62aa14` | 17 rows, 14 fixed, 3 open (S1-R1-01, S1-R3-01, S1-R3-02, each "the repair belongs in `.hexaemeron/design/resolve.py`") |
| `audit/rounds/fiat-402-implement-the-grounded-agent-predicate.md` | its `.synopsis.md` | `a17f7237e7c87a04` | 76 rows, 65 fixed, 11 open, all in grounded-agent capture |
| `plugins/ariadne/audit/AUDIT.md` | `AUDIT_SYNOPSIS.md` | `d8d13eb238b6e270` | 43, all fixed |

What bears on this run:

- 407 S1-R2-01 (medium, fixed) is why the 8 MiB limit exists: an
  8,390,343-byte statement installed successfully and Ariadne `inspect`
  exited 2. The part bound keeps that fix's promise instead of relaxing it.
- 402 S1-R18-02 (medium, fixed in `b0d8cc39`) is why the key budget exists:
  one 300,000-character U+FDFA key of 900,000 bytes expanded eighteenfold under NFKC and drove gates 4 and 7 to
  475,824,128 bytes of resident memory inside the 8 MiB parser cap. Raising
  the budget would reopen that finding, which is the main cost of the raised
  limit below.
- 1888's three open findings sit in that run's design resolver. The lesson
  applied here: this run's resolver refuses a moved base tree, writes reports
  only to fresh paths and is linted with Phylax before Step 1 commits it.
- 1888's `statement-limit` risk was reviewed or marked not applicable in every
  round, since no statement reached 8,388,608 bytes at 128 components.
- 402's eleven open findings concern `capture-grounded-agent` and
  `tree.files`, which this run does not touch. Ariadne's own 43 are fixed.

No audit record assigns a failure to this run, so no known-failure inventory
is carried.

### Concurrent work

- #1872's stacked branches claim Alexandria up to 0.7.33 and leave
  `statement.py`, `test_statement.py` and `test_release_limits.py` equal to
  the base. Its segment releases are the real case above.
- #1891 (bounded-memory `build` and `check`) starts at the same base. Its
  branch has no commit yet. This run plans no edit to `usdc_interval.py`.

### Outside this repository

- in-toto Statement v1 sets no size bound; the limits are the reader's:
  <https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md>.
- DSSE signs the pre-authentication encoding of the payload bytes and carries
  them as base64:
  <https://github.com/secure-systems-lab/dsse/blob/master/envelope.md>, with
  base64 from RFC 4648: <https://www.rfc-editor.org/rfc/rfc4648>.
- The in-toto attestation bundle puts several envelopes in one JSON Lines
  file: <https://github.com/in-toto/attestation/blob/main/spec/v1/bundle.md>.
  Ariadne reads one document per file, so a bundle would need an Ariadne
  change; separate files do not.

## 3. Constraints and non-goals

**Starting point and tools.** Base `150943da240837040478a76c3611d150fa04f2b6`
on `main`; run branch `fiat/1892-statement-parts`; Python
3.14.6; controller `fiat-v6.76.1`. Run every gate with `NO_COLOR=1` and
`FORCE_COLOR` unset.

**Byte identity.** Every statement the base emits keeps its bytes. Measured at
the base with `alexandria.py statement`:

| Release | Identifier | Components | Statement bytes | Statement SHA-256 |
| --- | --- | --- | --- | --- |
| test fixture (`tests/fixtures/capture-plan.json`) | `sha256:e86550e59baba75258093ed4b67c144d1dd520c68f0411d23ba59af050f3fed6` | 2 | 2,570 | `041c699bdefc8be359c88d738a8c5b45002e044b6226534d52bace7c09796c43` |
| `credit-history-v0` raw | `sha256:6117658c59c96e9ca32594ffe09e994d478dc7d9f2d3799c64bb25050c7fe0e2` | 2 | 2,792 | `d4846fd64852e5a8e34615679a252a7729976d1278b3be1ec177e1bc2da92fd2` |
| `credit-history-v0` derived | `sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec` | 2 | 2,792 | `3b12aa332fcf45cff14fb9a7d1c5f379852d3858c6cf56dcea57c26fc78523e6` |
| `usdc-interval-v0` | `sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa` | 10 | 11,026 | `c92e6cbb3b953acc3ad11e456cf5ca4715b5b2e8dbc98872a15e0c7c455716cf` |
| `usdc-interval-live-v0` | `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32` | 9 | 10,302 | `64df112deab0c91fe3da1aef1196a3a9226adee0cebc977468b3a609b4bc921f` |
| `usdc-interval-epochs-v0` synthetic | `sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036` | 10 | 11,026 | `656e225fbd67321230f58ff943a9dea3fc6ac265af8dc88beacbae2ba8b81bdd` |
| `usdc-interval-epochs-v0` live (current Compound) | `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a` | 9 | 10,303 | `76334510a1434645e0f249f4015c0c5d0065c17d0eea5f9814a7c9d12cc53527` |
| Compound Phase 0 (committed) | `sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab` | 70 | 71,339 | `4ebe969c40dbe77eacbe8848e530454596ecbb8ba9a07b3e6c49b11b41ca7a93` |
| proof-backed state (committed) | `sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f` | 6 | 3,689 | `faaff30f38025379781f35a7289af80cb0e15c9c0ff9c3efd0b9c09f1c77efa5` |
| Wildcat V1 | `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69` | 109 | 510,772 | `679277a2a3367d16a4cb462a12c805c6580291bbaaf7c3a6aa5b4d4e177c00ca` |
| Wildcat V2 | `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3` | 127 | 213,104 | `c891c9d510da6cf02136b082766792d520823beb98b79781c4f8cbcbaec7feae` |

The largest key count among them is Wildcat V2's 32,749, so all eleven stay on
the unchanged single path. `.hexaemeron/design/conformance.py
pinned-statements-keep-bytes` re-emits all eleven and passed at the base.

**External dependencies.** The two Wildcat releases are the preserved builds
under
`/Users/c0rtexzer0/Projects/wildcat-skills/tmp/fiat-evidence/fiat-1731-venue-agnostic-interval-capture-for-both-wi/`,
directories `step11-cli-v1-release` and `step11-cli-v2-release`, named through
`ALEXANDRIA_WILDCAT_V1_RELEASE` and `ALEXANDRIA_WILDCAT_V2_RELEASE`. Neither
the selection cell nor the integration cell rebuilds a Wildcat staging tree.

**Known red on main, not this run's.** With `ALEXANDRIA_WILDCAT_V1_STAGING`
and `ALEXANDRIA_WILDCAT_V2_STAGING` set, four staged Wildcat V2 rebuild tests
in the Alexandria suite fail with "Wildcat V2 registry bytes do not match the
pinned registry": #1960 made `build` refuse the pre-#1880 registry that the
preserved V2 staging carries. It is filed as
[#2023](https://github.com/wildcat-finance/skills/issues/2023). At `09f2169c`,
before #1960, the staged suite passed 1,190 of 1,190. Without the two
variables those tests skip, so step Exits run the Alexandria suite without
them; a staged run that shows exactly those four failures is not a finding of
this run.

**Versions.** The required `invariants` check runs `scripts/plugin_release.py`,
so every step raises Alexandria's package version over its own base in four
places: `plugins/alexandria/.claude-plugin/plugin.json`,
`plugins/alexandria/.codex-plugin/plugin.json`, the Alexandria entry in
`.claude-plugin/marketplace.json`, and the pin in
`tests/test_version_propagation.py`. `.agents/plugins/marketplace.json`
carries no version. Main is 0.7.31; #1872's branches claim up to 0.7.33; #1891
will claim its own. Each step picks a version above every `origin` ref's claim
and re-checks it immediately before push. Ariadne does not change, so it keeps
1.3.6. The skill generation moves once, through the runbook's
`version-relations` block, and the last step writes the row in
`plugins/alexandria/skills/alexandria/EVOLUTION.md` and the frontmatter version
in its `SKILL.md`.

**Digests the tree pins.** Checked by grepping each file's SHA-256 and git
blob id across the tree: `statement.py`, `test_statement.py`,
`test_release_limits.py`, `release-statements.md`,
`release-statement-v1.schema.json`, the Alexandria `SKILL.md`,
`EVOLUTION.md`, `AGENTS.md` and `README.md` are pinned nowhere.
`plugins/alexandria/scripts/alexandria.py` is pinned by
`plugins/ariadne/examples/wildcat-datasets-v0/` and
`docs/kickoff/1374/evidence/sources.json` and `docs/kickoff/1389/evidence/sources.json`
at the historical revision `104f6f82`, which read no working file, so editing it
moves nothing there. New tests go in the new module
`plugins/alexandria/tests/test_statement_parts.py`.

**Horos.** Every step regenerates `.horos/boundary.json` with
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, then
`.horos/census.json` with `... scan . --census --write`, and stages both.

**Package budget.** Two schemas and a committed design folder join the
portable runtime. Its file and byte headroom was not measured at this base;
Step 1 measures it with `python3 -m unittest tests.test_skills_sh_package`
before committing the design folder.

**Non-goals.**

- Changing Ariadne: its reader bounds, key budget, registry or any gate.
- Registering an Alexandria predicate in Ariadne, or checking gates 2 and 5.
- Signing, a DSSE writer in Alexandria, or cosign.
- Changing #1888's release limits or the single statement's wire format.
- A statement-set checker command. The stranger's check is Ariadne `verify`
  on each file plus a SHA-256 comparison with the index; a holder of the
  release can also re-run `--parts` and compare bytes.
- Bounded-memory `statement` emission. It holds the manifest and its
  projection in memory, as today.

**Carried forward.** The issue's carryover is `none`. Candidates for the
run-level block, disposition settled at integration:

- `key-budget-band`: the Decision above. If Laurence keeps today's bytes for
  the band, the verify failure is filed as its own issue.
- `statement-set-checker`: none; the index plus `sha256` is the check.

**Boundaries.**

- Always: the root and Alexandria suites and `scripts/run_checks.py` before a
  commit; Imprimatur on every shipped document; the Horos pair regenerated in
  the commit that changes the tree; a version rise in every step.
- Ask first: adding a dependency; changing a published statement byte;
  changing any file under `plugins/ariadne/`; widening a bound past section
  1's numbers; touching CI.
- Never: rewrite a pinned statement, release, audit record or historical
  study; commit a staging tree, endpoint or credential; delete or weaken a
  failing test; claim a demonstration ran when it did not.

## 4. Design options

### What was measured

Each candidate was prototyped in `.hexaemeron/design/resolve.py` from the
base's own `statement_for` and canonical encoder, and read by the base's
Ariadne. Two synthetic releases stand in for the cap, both 16,384 components
and 16,384 captures, written as real releases that pass the base `verify`:

- `light` has one short gap a capture: 13,288,026 single-statement bytes, 811
  a component, and 3,588,187 key characters, 219.0 a component.
- `heavy` has seven 941-character gaps a capture: 121,356,890 bytes, 7,407 a
  component, at least segment 3's 7,402.

Host: Apple M5 Max, 18 CPUs, 137,438,953,472 bytes of memory.

### The candidates

**`statement-parts`** (selected). The design in section 1: today's statement
within both bounds, otherwise an index and greedy parts in manifest order,
each within 6,225,920 bytes and 262,144 key characters. Light: 14 parts,
largest 970,641 bytes and 262,057 key characters. Heavy: 20 parts, largest
6,222,563 bytes bare and 8,296,840 as an unsigned DSSE envelope, 184,093 key
characters. The trade: a reader checks up to 21 files instead of one, and
completeness rests on the index's digests rather than on one file.

**`per-component-statements`.** The same part and index shapes with exactly
one component a part. No packing rule, so nothing in Alexandria mirrors
Ariadne's key accounting beyond the per-file refusal. The trade: 16,385 files
at the cap, 16,385 signatures to make and 16,385 `verify` runs to check, and
the largest file is the 1,950,336-byte index.

**`raised-limit-matched-reader`.** One statement up to 134,217,728 bytes, the
manifest limit, read with `--max-bytes 134217728`, and Ariadne's key budget
raised with the bound (prototyped as 8,388,608 characters, a sixteenth of the
bytes). The trade: one file, but every reader must know the flag, a signed
heavy statement is a 161,809,276-byte envelope, and the key budget that closed
402 S1-R18-02 grows 32-fold, which is an Ariadne change this run may not make.

**`compact-projection`.** Today's statement within 8 MiB, otherwise one
`alexandria-release/v2` statement whose components and captures are arrays
rather than objects. The trade: it saves little, because gap text is most of
a heavy capture (118,719,066 bytes against 121,356,890), and it keeps every
scope and coverage key. Hiding those keys too would take verdict-bearing
structure out of gate 4's sight, which is the gate's purpose. It refuses both
fixtures.

### The checked record

`.hexaemeron/design-evidence.json` carries 4 candidates, 9 criteria and all 36
cells. The five selection cells were resolved by the resolver above; every
report is below `.hexaemeron/design/reports/selection/`.

| Criterion | Concern | Kind | statement-parts | per-component | raised-limit | compact |
| --- | --- | --- | --- | --- | --- | --- |
| `cap-release-verifies` | correctness | gate, equals true | pass | pass | pass | fail |
| `default-reader-verifies` | compatibility | gate, equals true | pass | pass | fail | fail |
| `pinned-statements-stay-single` | compatibility | gate, equals true | pass | pass | pass | pass |
| `statement-set-bytes` | space | metric, minimise | 121,372,939 | 134,458,292 | 121,356,890 | 118,719,066 |
| `set-verify-milliseconds` | time | metric, minimise | 6,495 | 1,594,382 | 3,890 | 1,915 |

- `cap-release-verifies` runs Ariadne as each candidate's own reader would
  (the raised candidate with its flag and budget) on both fixtures, and
  requires every file to verify and the set to project every component and
  capture exactly once.
- `default-reader-verifies` requires every file to verify with Ariadne's
  unmodified defaults, bare and inside an unsigned DSSE envelope. It holds the
  promise in `release-statements.md:17-19` and 407 S1-R2-01's fix.
- `pinned-statements-stay-single` requires each candidate's routing to emit
  the base bytes for all eleven releases in section 3.
- `statement-set-bytes` totals the files each candidate's encoding produces
  for the heavy fixture, whether or not its own limit admits them.
- `set-verify-milliseconds` times one `ariadne.py verify` process per file,
  in sequence, over the heavy fixture: what a stranger pays. The two single
  files are read with `--max-bytes 134217728`; the compact one still fails
  gates 4 and 7, and its time is recorded all the same.

Two gates remove the raised limit and the compact projection. Of the two
survivors, `statement-parts` is smaller (121,372,939 bytes against
134,458,292) and verifies in 6.5 seconds across 21 files against 26.6
minutes across 16,385, so it is the unique frontier and the record selects it under `unique-frontier`. Peak reader
memory is not a criterion: both survivors keep every file under Ariadne's
default input bound, which is already the ceiling on what one read may cost.

Four conformance cells stay pending for the selected candidate, each resolved
by `.hexaemeron/design/conformance.py`:

| Criterion | Concern | Blocks | Test cases or check |
| --- | --- | --- | --- |
| `part-projection-verifies` | correctness | `step:3` | five `StatementPartProjectionTests` cases |
| `past-limit-refuses-by-name` | correctness | `step:4` | three `StatementPartsCommandTests` cases |
| `killed-emit-leaves-no-set` | recovery | `step:4` | three `StatementPartsCommandTests` cases |
| `pinned-statements-keep-bytes` | compatibility | `integration` | re-emits the eleven pinned statements |

The exact test identifiers, which Steps 2 and 3 must create under these names:

```text
tests.test_statement_parts.StatementPartProjectionTests.test_a_release_past_the_limit_projects_into_parts_ariadne_verifies
tests.test_statement_parts.StatementPartProjectionTests.test_every_component_and_capture_lands_in_exactly_one_part_in_order
tests.test_statement_parts.StatementPartProjectionTests.test_each_part_stays_within_the_part_limit_and_key_budget
tests.test_statement_parts.StatementPartProjectionTests.test_the_index_binds_every_part_by_digest
tests.test_statement_parts.StatementPartProjectionTests.test_a_release_within_both_bounds_keeps_one_statement
tests.test_statement_parts.StatementPartsCommandTests.test_a_component_past_the_part_limit_refuses_by_name
tests.test_statement_parts.StatementPartsCommandTests.test_output_refuses_a_release_past_the_single_bounds_naming_parts
tests.test_statement_parts.StatementPartsCommandTests.test_parts_refuses_a_release_that_fits_one_statement
tests.test_statement_parts.StatementPartsCommandTests.test_an_interrupted_write_leaves_no_output_directory
tests.test_statement_parts.StatementPartsCommandTests.test_an_existing_output_is_refused_unchanged
tests.test_statement_parts.StatementPartsCommandTests.test_output_inside_or_through_a_symlink_into_the_release_is_refused
```

### The selected wire shapes

Both new statements use Alexandria's canonical encoding: sorted keys, compact
separators, UTF-8, one trailing newline.

A part, `part-<k>.json` with `k` zero-padded to five digits:

- `subject`: `release/<release-name>` with the release digest, then
  `component/<name>` for each component in the part, in manifest order.
- `predicate.release`: the format and release digest, as today.
- `predicate.part`: `index` (`k`), `first_component` (the manifest position of
  its first component), `components` and `captures` (its counts).
- `predicate.components` and `predicate.captures`: today's objects, unchanged,
  for the part's components and every capture naming one of them, in manifest
  order.
- `predicate.claims`: today's one passed offline-verification claim on the
  release digest. `predicate.commands`: `[]`.

The index, `index.json`:

- `subject`: the release, then `part/part-<k>.json` with the SHA-256 of that
  part's bytes, in part order.
- `predicate.release`, `predicate.claims` and `predicate.commands` as in a part.
- `predicate.parts`: `count`, and the release's total `components` and
  `captures`.

Packing is greedy in manifest order: a part closes before the component whose
subject, component object and captures would carry it past either bound. Two
closed schemas, `release-statement-part-v1.schema.json` and
`release-statement-parts-v1.schema.json`, ship beside the existing one.

The command: `statement <release> --parts <directory>` writes the set into a
fresh sibling temporary directory, fsyncs every file and the directory,
re-verifies the release, and renames it into place. The target must be absent.
`--parts` on a release within both single bounds refuses and names `--output`,
so each release has exactly one statement form. `--output` and `--parts` are
mutually exclusive.

## 5. Risk register seed

```risk-register
part-completeness | the part set and its index | every component and capture lands in exactly one part in manifest order, each capture with its component, and the index binds every part by SHA-256
reader-bound | each emitted file against Ariadne's defaults | no part passes 6,225,920 bytes or 262,144 key characters, the index stays inside both, and each file verifies bare and as an unsigned DSSE envelope
key-accounting | the emitter's key count against Ariadne's gates 4 and 7 | the count covers predicate keys and subject digest keys exactly, and a test ties the bound to MAX_STRUCTURED_KEY_CHARACTERS_TOTAL
single-path-bytes | statement --output on a release within both bounds | all eleven pinned statements keep their SHA-256 and the byte refusal keeps its exact text
band-routing | a release under 8,388,608 bytes but over the key budget | --output refuses by name and --parts emits, and the edited 1888 test keeps its node-limit purpose
oversize-component | one component whose own part passes a bound | the refusal names the component and the bound, and nothing is written
partial-set | the output directory during a killed or failed emit | no output directory appears unless every file and the index were written and the release re-verified, and the temporary sibling is removed
output-confinement | the --parts target path | a target inside the release, through a symlink, or already present refuses without change
release-change-race | the release between verification and install | the release is re-verified before the rename, and a changed release installs nothing
ariadne-boundary | Ariadne's reader, gates and registry | no file under plugins/ariadne changes
version-collision | the four version surfaces | each step's version is above every origin ref's claim when pushed
overlap-1891 | files shared with issue 1891 | only version surfaces, the Alexandria ledger and the Horos census are shared, and whoever integrates second syncs
resolver-defects | the committed design resolvers | each refuses a moved base tree, writes only fresh report paths and passes Phylax
```

## 6. Glossary seeds

- **Single statement.** Today's `alexandria-release/v1` statement, emitted by
  `--output` for a release within both single bounds.
- **Single bounds.** 8,388,608 bytes and 262,144 key characters.
- **Part set.** The directory `--parts` writes: `index.json` and
  `part-00000.json` onwards.
- **Part.** One `alexandria-release-part/v1` statement over a contiguous run
  of components.
- **Index.** The `alexandria-release-parts/v1` statement binding every part
  by SHA-256.
- **Part bound.** 6,225,920 bytes and 262,144 key characters.
- **Key characters.** The characters in every object key Ariadne's gates 4 and
  7 scan: all predicate keys and each subject's digest keys.
- **Band.** Releases whose single statement is within 8,388,608 bytes but
  past 262,144 key characters.

## 7. Sources

- Issue #1892, #1888, #1891, #2023: <https://github.com/wildcat-finance/skills/issues/1892>,
  <https://github.com/wildcat-finance/skills/issues/1888>,
  <https://github.com/wildcat-finance/skills/issues/1891>,
  <https://github.com/wildcat-finance/skills/issues/2023>.
- Pull requests #1905 and #653:
  <https://github.com/wildcat-finance/skills/pull/1905>,
  <https://github.com/wildcat-finance/skills/pull/653>.
- At the base commit:
  - `plugins/alexandria/scripts/alexandria_lib/statement.py`
  - `plugins/alexandria/scripts/alexandria_lib/canonical.py`
  - `plugins/alexandria/scripts/alexandria_lib/release.py`
  - `plugins/alexandria/scripts/alexandria.py`
  - `plugins/alexandria/docs/release-statements.md`
  - `plugins/alexandria/schemas/release-statement-v1.schema.json`
  - `plugins/alexandria/tests/test_statement.py`
  - `plugins/alexandria/tests/test_release_limits.py`
  - `plugins/alexandria/docs/epoch-table-split/study.md`
  - `plugins/ariadne/scripts/ariadne.py`
  - `plugins/ariadne/scripts/ariadne_lib/safejson.py`
  - `plugins/ariadne/scripts/ariadne_lib/envelope.py`
  - `plugins/ariadne/scripts/ariadne_lib/gates.py`
  - `plugins/ariadne/scripts/ariadne_lib/core_predicate.py`
- The audit sources and synopses in section 2.
- in-toto Statement v1, DSSE, RFC 4648 and the in-toto bundle, linked in
  section 2.
- The design resolvers and reports: `.hexaemeron/design/resolve.py`,
  `.hexaemeron/design/conformance.py`, `.hexaemeron/design/reports/`.

## 8. Signals, and the questions behind them

None unattended, and here is why: `statement` is an operator command run once
per release, after `verify`, and it runs no daemon, schedule or retry. Its
signals are the ones an operator reads at the terminal.

- *Why did this release get no statement?* The refusal names the bound
  (bytes or key characters), its value and, for a part, the component. Steps 2
  and 3 emit it.
- *Is this part set complete?* The index's `parts.count`, `components` and
  `captures`, and one subject digest a part. The `--parts` receipt reports
  the release id, part count, component and capture counts, predicate types
  and the absolute output path. Step 3 emits it.

## 9. Boundaries, per capability

- **The release directory**, an untrusted input. `statement` already runs the
  complete offline `verify` and re-reads the manifest under the manifest
  limits before projecting; the part form reuses that path unchanged.
- **The `--parts` output directory**, a new write boundary. Worth taking: a
  write into the release, through a symlink, over an existing directory, or a
  half-written set that looks complete. Controls: the confined parent checks
  `_prepare_output` already makes; an absent target; a fresh
  temporary sibling directory made with `mkdir` under the confined parent
  descriptor; every file fsynced; the
  release re-verified before the rename; the temporary directory removed on
  any failure. Hostile writers with permission on the output parent stay
  outside the promise, as #653 carried forward.
- **Ariadne's reader bounds**, the boundary this run must not widen. Controls:
  the part bound and key budget above, tied by test to Ariadne's constants,
  and the `ariadne-boundary` risk.
- **No new subprocess, network or secret.** The command reaches no network.
  The tests and resolvers start only fixed-argv Python and git children.

## 10. The budget, or its absence

No new budget, and here is why: the reader's cost is already bounded by
Ariadne's default input bound, which every file must meet, and emission runs
once per release after a `verify` that reads every component. Measured with
`/usr/bin/time -l` on the heavy fixture at the base:

| Command | Seconds | Peak resident bytes |
| --- | --- | --- |
| `alexandria.py verify` on the release | 2.37 | 846,938,112 |
| `ariadne.py verify` on the largest part, 6,222,563 bytes | 0.28 | 53,297,152 |
| the same part inside an unsigned DSSE envelope | 0.42 | 71,892,992 |
| `ariadne.py verify --max-bytes 134217728` on the 121,356,890-byte single statement (refused on gates 4 and 7) | 2.12 | 448,774,144 |

Step 4 records `/usr/bin/time -l` for `statement --parts` on the heavy fixture
in `proof.md` as an observation, with no threshold.

## 11. The fail-closed posture

Stop the run on: any file past the part bound or the single bounds; a
component whose own part passes a bound; a release that changes during
emission; any existing output; a projection that does not equal
`statement_for`; any refusal from `verify`. A refusal writes nothing and
exits 1 with one `alexandria:` line and no traceback, as today. Guard
convention: each fix lands with a test in
`plugins/alexandria/tests/test_statement_parts.py` that fails on the parent
commit and passes on the fix, run by the step's Elenchus command in the
runbook. The known red in section 3 is not this run's and gets no guard here.

## 12. Decisions and their homes

- **Split a statement past the single bounds into an index and parts.** The
  two predicate types and the part file layout become a published wire format
  that signing steps and readers depend on, so changing them later means a
  new version. Home: `docs/decisions/drafts/split-a-release-statement-into-parts.md`,
  which Step 1 creates with the options above and their trades.
- **The part bound, 6,225,920 bytes and 262,144 key characters.** Tied to
  Ariadne's defaults and to DSSE's base64 expansion. Home: the same draft.
- **Routing the band to parts.** The open Decision under the assumptions.
  Home: the same draft, and the Alexandria generation row in
  `plugins/alexandria/skills/alexandria/EVOLUTION.md`.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | statement-parts
record | plugins/alexandria/skills/alexandria/EVOLUTION.md
```

### Step decomposition hint

Four steps, each one pull request, sized for the audit loop.

1. **Scaffold.** Commit this study, the runbook, the design record, its
   reports and both resolvers under `plugins/alexandria/docs/statement-parts/`;
   create the decision draft; raise the version; regenerate Horos.
2. **Projection.** Add the part and index projection, the packing rule, the
   key count and its Ariadne-tied bounds, and the two closed schemas, without
   changing `emit_statement`. Create `StatementPartProjectionTests`. Cell
   `part-projection-verifies`.
3. **Command.** Add `--parts` with the confined directory writer and its
   receipt; route `--output` refusals; edit `check_statement_beyond_the_old_limits`
   per the Decision. Create `StatementPartsCommandTests`. Cells
   `past-limit-refuses-by-name` and `killed-emit-leaves-no-set`.
4. **Demonstrate.** Update `release-statements.md`, the Alexandria `SKILL.md`,
   `AGENTS.md` and its promise contract; record the heavy-fixture run in
   `proof.md`; write the generation row. Cell `pinned-statements-keep-bytes` at
   integration.

Every step's Files carry the four version surfaces and `.horos/census.json`,
and `.horos/boundary.json` when a classified file changes. Every Exit names
`python3 -m unittest discover -s tests` and
`python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria`,
both with `NO_COLOR=1` and without the Wildcat staging variables.
