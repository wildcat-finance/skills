# Aave v4 receipt inclusion delivery proof

## Authority and source boundary

This record covers Fiat issue 383, Step 5, `Ship and demonstrate the Aave v4
receipt proof`. Implementation started from signed parent
`c883ff1cb3e86080884175088cfba403146a6269` on
`fiat/383-prove-receipts-against-the-captured-header-s-step-4-carry-the-proof-through-release`.
The implementation branch is
`fiat/383-prove-receipts-against-the-captured-header-s-step-5-ship-and-demonstrate-the-goldfin`.

The controlling evidence for the final Files boundary is:

| Record | SHA-256 | Authority |
| --- | --- | --- |
| Study | `f8dd4bad531e8dbc236fec0bf0580d4a6a3a6284ce293a57a4d37af8555f9b79` | Design facts |
| Canonical runbook after the Step 5 amendments | `bcc4e6e752fea71c1df484db0f3a684936c52c3c6e3338317672d8f47c9ba12f` | Step contract |
| Effective Step 5 | `34e65f2a8f16d1ed502f036752e9810803d1f7bd14ba0dc3fe1d54c1944bfb50` | Current source packet |
| Implementation packet state | `be7ece5732424cd67ab5a9cbc7bcd38a40c51fa71e16ed1b7f265aadae12b9eb` | Implementation hand-off |
| Round 2 source packet state | `dd4b61c7218e2c62b71ef290cc5b4f753ac2ef5343bcc89efe3aa73b58daaa86` | Audit repair authority |
| Round 3 source packet state | `7c8e35954a1027cb95febfb8ed1fbe1f5210e5a98773cf29c8109395c84053f6` | Audit repair authority |
| Entry-repair amendment | `8df12aee81fc0b381793c659920314bb8124382fa8432c313e380c5607a8d015` | Entry repair |
| Lazarus marketplace-copy Files amendment | `508be2c58135a2b0c6aeb180343c7f9a4b2e56e3efe8adec4e24ad1feb453cb5` | Two prose copies |
| Manifest writer-selection Files amendment | `86ff0bd9c61febf3f087cb9da259902692f2805282afdbd8ea38150cbc8714d9` | Cause fix |
| Receipt fixture restamp Files amendment | `7ca1ee04ab6910d5f19769bd249156c31d0f02239dc79655bcb7b4de8d6e3544` | Version propagation |
| Preservation-guide Files amendment | `2423b45f020338cef35c7d6b234104ae7cb65a44a21533c10d4eadf820160880` | Governed context repair |
| Capture-command amendment | `d3bd6d19588cf55f321810e4e7381d10bd5f188b6cbde80548b7c502b913b5b8` | Split argv and tracked runbook |
| Truthful-builder amendment | `11cd6e4fcb860da76e6f655790049695a9c9f5c1e6e9c4a2f3d9e815913cc1d0` | Producer provenance and materialized mutations |

Each repair added only the paths named by its receipt. The Step 5 implementation
worker ran no controller command, network capture, push, publication, merge or
issue mutation. The Fiat orchestrator separately receipted the amendments,
implementation and this audit directive.

## Shipped artefacts and claims

The fixed fixture at `plugins/lazarus/examples/aave-v4-spoke-v1` verifies to:

| Field | Verified value | Evidence class |
| --- | --- | --- |
| Ethereum block | `0x18ac22c` | Header bound |
| Block hash | `0x11e9be2ff9ff6a04319af0b04c24b95f3f1117c2df79f44f94d208857d01af07` | Header bound |
| Receipts root | `0x7d3403cc37d77546db4005e06876a204372b0ef52a703cc88577a96dc4befb1a` | Recomputed |
| Ordered consensus receipts | 224 | Recomputed |
| Target trie index | `0x3f` | Receipt-trie proved |
| Target consensus logs | 110 | Receipt-trie proved |
| Filtered consensus-log projection | 5 | Receipt-trie proved |
| Receipt-trie-proved relations | 2 | Recomputed count |
| Evidence counts | `proof_backed=2`, `header_bound=1`, `recorded_rpc=5`, `receipt_trie_proved=2` | Recomputed inventory |
| Transaction-hash attribution | `recorded_rpc` | Recorded only |

The public fixture copies the six captured source components from
`plugins/lazarus/tests/fixtures/aave-v4-receipt-proof-v1` byte for byte: `anchors.jsonl`,
`header.json`, `plan.json`, `proofs.jsonl`, `receipt-witness.json` and
`rpc.jsonl`. Its own `demo.py` and manifest make the published demonstration a
separate deterministic fixture. Its offline builder verifies the pinned source
fixture, creates its private stage beneath the already opened output-parent
descriptor, writes those six components and the current demo bytes with
exclusive no-follow file creation, rechecks the output parent's directory
identity, builds and verifies the manifest, and publishes by an fd-relative
atomic no-replace rename only to a new destination. The demonstration
runs the statement's exact five-word producer argv in a temporary execution
root and captures the fixture at that argv's relative output path. The internal
manifest-v2 was restamped from writer 0.1.0 to 0.2.0 without changing any raw
source component.

| Artefact identity | SHA-256 | Digest scope |
| --- | --- | --- |
| Aave v4 v1 fixture digest | `1d2b6eab3d62ad57f9481e5c202efa83c8d423ccbd95b6086cef1f9b0c34cf1d` | Semantic manifest identity |
| Aave v4 v1 manifest file | `5c1ffc35c816a93dd4b95ceb891c883bf5b455ed7435bea08fe08159653ac211` | Raw file bytes |
| Ariadne state-fixture/v2 statement file | `67bf286eeebb03a3731f22f46bf35d6dcbc3d28bc8dcb060a3f0443080e515fd` | Raw file bytes |
| Aave v4 v1 release digest | `fceee6d3611d9a008ce3c8db84df29a177dffa58b578b301ddd5ebb351e2a973` | Semantic release identity |
| Aave v4 v1 release file | `dee99fcd27079f6c4636279f293d35607338f117e79c04642e49fda220e086fb` | Raw file bytes |
| Restamped internal receipt manifest file | `f9bd4a3e9192ec4d472b4b9127fd66871f87d5b60f75b34a3f82c7d6e1213558` | Raw file bytes |
| Restamped internal fixture digest | `a88218e27b979a67941bd66f04eec9e0d1208178697c0c3f59a245f22dba0eec` | Semantic manifest identity |

`aave-v4-spoke-v1-release` contains the exact fixture copy, the deterministic
state-fixture/v2 statement and release-v2 binding. The statement and release
carry `receipts_root` and the count of two scoped relations. They explicitly do
not claim that the receipt trie attributes a transaction hash, that the block
is canonical, or that the recorded providers are independent.

The historical Aave v4 release remains byte-identical:

| Historical identity | SHA-256 | Digest scope |
| --- | --- | --- |
| Aave v4 v0 fixture digest | `d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49` | Semantic manifest identity |
| Aave v4 v0 manifest file | `c37cd789e5386a1347abd4dff24c8b1db96cdab771df4eb4d63056ba56145fa9` | Raw file bytes |
| Aave v4 v0 statement file | `d8b262278ffd4db76e449a2bfce4629903a70e7f4ad7c1f3a6ebbfb1f112555e` | Raw file bytes |
| Aave v4 v0 release file | `ec5c9b8091286de8713b6daf6cfdeaa7e9cfa6177b96c10a2ed20ffd6654bcff` | Raw file bytes |

Writer 0.2.0 stamps new output. An exact deterministic rebuild of the existing
historical manifest-v1 preserves writer 0.1.0. Installable package versions are
Lazarus 1.1.2 and Ariadne 1.2.2. The governed skill labels are `lazarus-v2.2.0` and
`ariadne-v2.2.0`; those are separate version axes.

## Elenchus guards

Twenty-three observed failures were localised before the final run:

1. The index mutation failed while validated witness bytes were being written,
   before the helper's original verification-only exception boundary. That
   first repair accepted either construction or verification rejection; guard
   9 below closes the remaining evidence gap.
2. Raising the writer to 0.2.0 caused the unchanged Aave v4 v0 demo's
   byte-identical manifest rebuild to relabel manifest-v1. The first repair then
   selected writer 0.1.0 by schema and mislabeled fresh plan-v1 captures made by
   writer 0.2.0. Manifest construction now preserves writer 0.1.0 only for an
   exact existing historical rebuild; fresh manifest-v1 and manifest-v2 output
   use writer 0.2.0. Both demonstrations, a fresh plan-v1 capture and the v0/v1
   coexistence tests guard the distinction.
3. The first full Lazarus run found the Step 2/3 receipt fixture and capture
   digest still pinned to writer 0.1.0. The manifest-v2 and its exact capture
   digest pin moved together to 0.2.0; all six raw source components stayed
   byte-identical. The deterministic receipt rebuild and recapture tests guard
   the restamp.
4. Ariadne's documentation checks refused three cross-plugin relative links in
   the new receipt hand-off prose. The prose now names the Lazarus paths and
   command boundary without creating links outside Ariadne's plugin root. The
   existing documentation-link suite guards that ownership boundary.
5. The cold read omitted an unmarked marketplace context in the preservation
   guide. Its stale frontier and receipt claims remained public while the proof
   called a five-copy marker inventory complete. The guide now carries the
   governed current block, describes both release versions and passes the
   structural prose gate; the 165-file inventory includes its exact bytes.
6. The first Aave v4 v1 statement recorded `lazarus capture aave-v4-spoke-v1` as
   one argv element even though Ariadne requires one `--capture-command` per
   word. The first receipted repair split that vector; guard 8 below replaces
   the resulting fictitious command with the real producer.
7. This proof said four observed failures while enumerating five. Its count now
   agrees with the numbered guards, and the scaffold test holds both the count
   and final numbered entry.
8. The split `lazarus`, `capture`, `aave-v4-spoke-v1` vector still named no installed
   executable or implemented Aave v4 command. The shipped statement now
   records the exact five-word Python builder argv that materialized the
   byte-identical fixture from pinned local sources.
9. The demo caught `LazarusError` around mutation construction as well as
   verification. Its index mutator failed validation before writing, while its
   log mutator turned empty data into invalid hex; both were reported rejected
   without tampered fixture bytes. Mutation construction now completes before
   the rejection boundary, writes canonical raw JSON for intentional invalid
   structure, and flips one valid address byte. Tests prove every named fixture
   mutation changes canonical bytes before verification refuses it.
10. The whole-tree Ephoros gate interpreted the receipt witness's `address`
    field access in the log mutator and its guard as telemetry keyed by wallet
    address. Those reads alter and inspect local fixture evidence; they emit no
    telemetry. Reason-bearing exceptions state that boundary at each access,
    and the whole-tree gate now passes while the byte-level mutation guard
    remains intact.
11. The fixture builder created a missing output parent before it checked
    whether the destination was inside either source fixture. A refused build
    could therefore leave a new directory in pinned source evidence. The
    containment check now runs before any write and again after parent
    resolution; a copied-source guard proves refusal leaves no parent behind.
12. A staging `OSError` escaped the builder command as a traceback containing
    host detail and left a parent that the command had created. Staging failure
    now becomes a bounded `PathError`, failed builds remove their newly created
    empty parent, and the CLI emits one fixed refusal line. The guard injects a
    private error marker and proves it, the traceback, the destination and the
    parent are absent.
13. The offline guide introduced three verification and demonstration commands
    as “Neither command”. It now says none of those commands accepts an RPC URL
    or opens a connection, and the scaffold test refuses the old wording.
14. The builder resolved its output parent before staging but kept using the
    path after that check. Replacing the parent with a symlink during stage
    creation published the complete fixture inside the pinned source fixture.
    The builder now pins the parent's device and inode, resolves the stage,
    checks both against the pinned parent before any component write, and
    repeats the parent check before publication. The race guard proves the
    source tree is byte- and entry-identical after refusal.
15. The demonstration built an arbitrary temporary fixture in-process, then
    told Ariadne that the fixed five-word command ending in
    `tmp/aave-v4-spoke-v1-rebuild` had produced it. The command was runnable but was
    not the producer of the captured path. The demonstration now executes that
    exact argv in an isolated temporary root and hands Ariadne its named output;
    the guard compares the recorded argv, execution root and captured path.
16. A cleanup `OSError` from the private stage overrode the bounded build
    failure, escaped the public command with host detail and left the new parent
    and stage. Cleanup failure now becomes the fixed `fixture stage cleanup
    failed` refusal. The guard proves the private marker and traceback stay out
    of the command's diagnostic; an unremovable stage remains visible rather
    than being reported as removed.
17. Rebinding the output parent immediately after a bounded source read made
    the next stage write raise raw `FileNotFoundError`; checks around reads did
    not anchor the write or final rename. The builder now holds an outer stage
    and its fixture beneath open directory descriptors, reaches stage files
    through that anchored directory, performs the atomic no-replace rename
    relative to the open source and destination parents, and rolls back a
    completed rename if the requested parent changed. Guards swap the parent
    after a source read, immediately before a stage write and during finalisation;
    each gets a bounded refusal, leaves both source trees unchanged and removes
    the private stage and any rolled-back destination.
18. Renaming the output parent after path-based stage creation but before the
    builder resolved that stage produced a bounded refusal but stranded the
    private directory in the renamed parent. The builder now opens and checks
    the output parent before it creates the stage relative to that descriptor.
    The guard moves the parent at the creation boundary and proves the refusal
    removes the private stage without publishing a fixture.
19. A staged component symlink could redirect `Path.write_bytes` to an external
    file before later no-follow verification rejected the fixture. Component
    creation now uses exclusive no-follow opens relative to the pinned fixture
    descriptor. The guard plants that symlink and proves the external target
    stays byte-identical while the build refuses and cleans its stage.
20. Cleanup checked the stage inode and then recursively removed the same
    pathname. Replacing that name between the check and removal deleted an
    unowned tree. Cleanup now atomically quarantines the named tree, verifies
    the moved inode and restores an identity mismatch instead of deleting it.
    The guard proves both the expected displaced tree and its replacement
    survive the refusal.
21. The quarantine repair still passed its pathname to recursive removal after
    the last inode check. Replacing that name at the check boundary deleted a
    non-owned replacement while the owned stage survived elsewhere. Cleanup
    now opens the verified quarantine, clears its bounded contents through that
    descriptor and limits the remaining pathname operation to removing an
    empty directory. The guard substitutes a nonempty competitor and proves
    both that tree and the displaced owned directory survive the refusal.
22. Output-path inspection leaked raw `ValueError` for an embedded NUL and raw
    `OSError` with an absolute host path for an oversized basename. Resolution
    and existence checks now map those failures to fixed `PathError` messages.
    The guard exercises both the direct builder and bounded CLI surfaces and
    refuses a traceback or private path detail.
23. This public final-source ledger stopped at round 5 even though round 6
    changed source and completed a later final run. The cumulative ledger now
    records the round-6 entry, parent comparison and repaired run as well as the
    round-7 entry, parent comparison and final run. The scaffold test pins the
    missing round-6 rows and this final numbered guard.

The end-to-end demonstration independently rejects a one-byte consensus
receipt, index, consensus log, receipts root, evidence count and release
mutation. A coherent transaction-hash rewrite leaves the root and both proved
relations unchanged. A one-source rewrite is rejected as
`recorded RPC transaction hash disagreement`, without `root` or `proved` in the
diagnostic.

## Discipline evidence

**Phylax.** Step 5 performed no provider capture. It reused the fixed bounded
source captured under Step 3's request, byte, time, secret-union and atomic
controls. The builder verifies that pinned source, rereads each component
through a bounded no-follow descriptor, rechecks the copied claims, creates its
adjacent private stage relative to the pinned output-parent descriptor, writes
new components through exclusive no-follow descriptors, refuses source-contained
or existing destinations, and publishes with atomic no-replace. Cleanup first
quarantines and opens the expected inode, clears its bounded contents through
that descriptor and performs no recursive removal through the quarantine path;
a cleanup failure produces a fixed refusal and does not claim removal. Fixture
verification, statement capture, release build and release
verification accept local paths only. The demo runs the recorded producer argv,
patches both socket connection entry points to fail on use and reports
`network=denied`. No dependency changed. An independent
`strace -f -e trace=network` run observed no socket, connect, bind, listen,
accept, endpoint send/receive or socket-option syscall.

**Ephoros.** The demo emits one canonical JSON line with correlation ID
`aave-v4-spoke-v1-offline-demo`. It includes the safe block identity, root, bounded
counts, scoped relation, versions, digests and named mutation verdicts. Tests
refuse extra lines, require the byte-identical rebuild verdict, and scan the
event for topics, data, RPC URL forms, credentials and bearer material. Receipt
bodies and log payloads are absent.

**Metron.** No performance claim is made. The test durations below establish
only that the fixed offline checks completed in the locked environment; they do
not promise provider speed, replay throughput or a performance budget.

**Hypomnema.** ADR-037 holds the full ordered-witness decision and rejected
alternatives. `plugins/lazarus/docs/receipt-inclusion-proofs.md` holds the
operator boundary. Ariadne's state-fixture guide holds the statement boundary.
This proof holds the shipped evidence. The Lazarus and Ariadne evolution ledgers
each contain exactly one new row for their own version axis.

## Complete mutable marketplace inventory

The cold read used the same mutable marker boundary as
`tests/test_marketplace_prose.py`: every first-party Markdown file containing a
`marketplace-context` block, excluding historical audit records and the three
vendored Pashov skill roots. It also read the root collective README, both root
marketplace registries, every plugin's two host manifests, and every shipped
`agents/openai.yaml`. For each sorted path, inventory digest material is
`path`, a NUL byte, the file SHA-256 and a newline.

The 111 context-bearing Markdown paths are:

| Plugin | Count | Exact path set |
| --- | ---: | --- |
| Alexandria | 14 | `plugins/alexandria/{AGENTS.md,README.md,docs/{address-index.md,compound-v3-harvest.md,credit-view.md,data-dictionary.md,raw-releases.md,runbook.md,study.md},examples/{README.md,compound-v3-phase0-v0/README.md,credit-history-v0/README.md},schemas/README.md,skills/alexandria/SKILL.md}` |
| Ariadne | 14 | `plugins/ariadne/{AGENTS.md,README.md,docs/{capturing-a-dataset.md,capturing-a-release.md,capturing-a-state-fixture.md,conformance.md,dataset.md,design.md,solidity-release.md,state-fixture.md},examples/README.md,skills/ariadne/SKILL.md,tests/fixtures/{dataset-release/README.md,forge-project/README.md}}` |
| Berean | 9 | `plugins/berean/{AGENTS.md,README.md,docs/{answers.md,design.md,influences.md,release-policy.md,spec.md},examples/aave-v4-demo-v0/README.md,skills/berean/SKILL.md}` |
| Brevitas | 3 | `plugins/brevitas/{AGENTS.md,README.md,skills/brevitas/SKILL.md}` |
| Hermes | 4 | `plugins/hermes/{AGENTS.md,README.md,skills/hermes/{SKILL.md,references/optimisation-catalogue.md}}` |
| Hexaemeron | 6 | `plugins/hexaemeron/{AGENTS.md,README.md,agents/{mason.md,scribe.md,surveyor.md,warden.md}}` |
| Horos | 2 | `plugins/horos/{AGENTS.md,README.md}` |
| Janus | 3 | `plugins/janus/{AGENTS.md,README.md,skills/janus/SKILL.md}` |
| Lazarus | 6 | `plugins/lazarus/{AGENTS.md,README.md,docs/{preservation-release.md,runbook.md,study.md},skills/lazarus/SKILL.md}` |
| Lemma | 15 | `plugins/lemma/{AGENTS.md,INVARIANTS.md,README.md,baseline/{README.md,docs/{README.md,SUMMARY.md,concepts/{entries.md,fixed-point.md},reference/{contracts.md,errors.md},user-guide/{day-to-day-usage/{README.md,creating.md,retiring.md},troubleshooting.md}}},skills/lemma/SKILL.md}` |
| Pandects | 8 | `plugins/pandects/{AGENTS.md,README.md,adapters/medusa/README.md,docs/{applicability.md,design.md,writing-a-law.md},integrations/wildcat/APPLICABILITY.md,skills/pandects/SKILL.md}` |
| Probitas | 8 | `plugins/probitas/{AGENTS.md,README.md,assets/dossier-template.md,docs/{adding-a-venue.md,example-dossier.md},skills/probitas/{SKILL.md,references/{gates.md,venues.md}}}` |
| Sapheneia | 3 | `plugins/sapheneia/{AGENTS.md,README.md,skills/sapheneia/SKILL.md}` |
| Tabularium | 16 | `plugins/tabularium/{AGENTS.md,README.md,docs/{adding-an-adapter.md,compound-v3-preservation.md,euler-preservation-runbook.md,euler-preservation-study.md,release-policy.md},examples/{compound-v3-phase0-v0/{DATA-DICTIONARY.md,README.md},euler-v1-v0/{DATA-DICTIONARY.md,README.md},euler-v2-v0/{DATA-DICTIONARY.md,README.md},aave-v4-spoke-v0/{DATA-DICTIONARY.md,README.md}},skills/tabularium/SKILL.md}` |

The remaining exact path sets are `README.md`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`plugins/*/{.claude-plugin/plugin.json,.codex-plugin/plugin.json}`, and the 23
existing `plugins/*/skills/*/agents/openai.yaml` files. The complete inventory
therefore contains 165 files. Its final aggregate digest is
`5ab4e518211de5f4ae8b016dbb39ef1743595615c6c9ef2d7d100198e656cad7`;
the 114 context/root surfaces digest to
`30a559bd825b075f2153dad022e19faa30b65d46378032a5bc3a201d480dd1de`,
and the 51 host prose files digest to
`b643311cb5e533a50f9d662539b9770f974d219e3a0192483ad9abddebfb0d0b`.

Lazarus's six mutable context copies now carry the same completed frontier and
successor job. Ariadne retains its grounded-agent frontier text and digest byte
for byte; only its receipt-aware hand-off explanation and generation metadata
changed. Both host manifests and the Claude marketplace carry package versions
1.1.2 and 1.2.2. The Agents marketplace has no version or prose field for these
plugins and remained unchanged. All unrelated frontier claims remained
unchanged, and the marketplace-prose gate found no disagreement to file.

## Verification ledger

All Python commands ran from the final Step 5 worktree under
`uv run --offline --python 3.12.13 --with-requirements
plugins/lazarus/requirements.lock`, except the dependency-free repository
discipline scripts. The final exhaustive exits and counts are recorded here
after the final source bytes are fixed.

| Gate | Result | Evidence |
| --- | --- | --- |
| Exact Step 5 entry combined runner | exit 0, 1259 tests, 85.516 seconds | Entry report |
| Round 1 Warden source-bound entry runner | exit 0, 1,270 tests, 96.324 seconds | Report SHA-256 `410f723d860c7c3ae5ecd9e738fe9797ed6898b83a1a3fc115ea12e5411976a7` |
| Round 2 Warden source-bound entry runner | exit 0, 1,271 tests, 92.086 seconds | Report SHA-256 `217b368e207bac22d5fc81501a92e5bf47de5ff801a5d07b213d29d106fec68a` |
| Round 3 Warden source-bound entry runner | exit 0, 1,271 tests, 92.086 seconds | Report SHA-256 `217b368e207bac22d5fc81501a92e5bf47de5ff801a5d07b213d29d106fec68a` |
| Round 4 Warden source-bound entry runner | exit 0, 1,273 tests, 90.554 seconds | Report SHA-256 `3623123f4b314d75adbbfa660fea87584127ca40df40d4d999f00c800c930108` |
| Round 5 Warden source-bound entry runner | exit 0, 1,275 tests, 91.002 seconds | Report SHA-256 `5507771aeedf8c7d4157260981da713df7476e52e62bac14aa39ea555429eaab` |
| Round 6 Warden source-bound entry runner | exit 0, 1,281 tests, 93.810 seconds | Report SHA-256 `cfda950fd252d1bb9d054d408961415df452a54b13361c5e49b570ad568c26d1` |
| Round 7 Warden source-bound entry runner | exit 0, 1,284 tests, 95.083 seconds | Report SHA-256 `357b5a134a2da73b4b3a7fb2570dbb845796b9664975bf88cff97d4e3e83ff33` |
| New and legacy Aave v4/release/scaffold focus | exit 0, 64 tests | Focused unittest output |
| Marketplace, version, evolution and portable-skill focus | exit 0, 41 tests | Focused unittest output |
| Ariadne plugin suite | exit 0, 689 tests | Complete source-bound runner |
| Lazarus plugin suite | exit 0, 597 tests | Complete source-bound runner |
| Canonical round-2 Elenchus parent comparison | guarded, 1,271 tests, 5 assertion failures, 0 errors, 0 skips | Candidate `f3568e6`; all three changed test files copied to signed parent `c861b49305c45829d0bd938b68e7083d857eaeb8` |
| First round-3 Elenchus parent comparison | inconclusive, 1,273 tests, 9 assertion failures, 1 error, 0 skips | The parent lacked the new fixture-rebuild event key, so the guard indexed through the compatibility boundary |
| Canonical round-3 Elenchus parent comparison | guarded, 1,273 tests, 10 assertion failures, 0 errors, 0 skips | All three changed test files copied to signed entry `6f20c92aed7c07017f6a53f3195e42a159de0b57`; the compatibility guard uses `.get()` |
| Canonical round-4 Elenchus parent comparison | guarded, 1,275 tests, 6 assertion failures, 0 errors, 0 skips | All three changed test files copied to signed candidate `a5b3b068492a202a09ae00d62ae695a886ad3fb0` |
| First round-5 Elenchus parent comparison | guarded, 1,278 tests, 7 assertion failures, 0 errors, 0 skips | All three changed test files copied to signed candidate `79bb7aa98b4b32135bf5ed0fc46bc40a70be69d6` before the final parent-rebind reduction |
| Canonical round-5 Elenchus parent comparison | guarded, 1,281 tests, 10 assertion failures, 0 errors, 0 skips | All three changed test files copied to signed candidate `4e06d93f9ac8856cbe7ca7e724c1ba3dba4defc5` |
| Round 5 final combined receipt-delivery runner | exit 0, 1,281 tests, 93.810 seconds | Complete report SHA-256 `cfda950fd252d1bb9d054d408961415df452a54b13361c5e49b570ad568c26d1` |
| Canonical round-6 Elenchus parent comparison | guarded, 1,284 tests, 6 assertion failures, 0 errors, 0 skips | All three changed test files copied to signed candidate `8c0d414f9346d82c84002b50d586c897be2fb3e0` |
| Round 6 repaired combined receipt-delivery runner | exit 0, 1,284 tests, 94.280 seconds | Complete report SHA-256 `357b5a134a2da73b4b3a7fb2570dbb845796b9664975bf88cff97d4e3e83ff33` |
| Round 7 repaired precommit combined runner | exit 0, 1,286 tests, 94.902 seconds | Complete report SHA-256 `47fe6f0418e216a5b2c08786bf8b37536fd8ebdb60b12270ff7f63b23a1fb64b` |
| Canonical round-7 Elenchus parent comparison | guarded, 1,286 tests, 5 assertion failures, 0 errors, 0 skips | All three changed test files copied to signed candidate `91f519ca07f477c887db42b7a9a46829c53e8423` |
| Round 7 final combined receipt-delivery runner | exit 0, 1,286 tests | Complete report SHA-256 `47fe6f0418e216a5b2c08786bf8b37536fd8ebdb60b12270ff7f63b23a1fb64b` |
| Root suite | exit 0, 396 tests | Root unittest output; 1,258 inoculation cases, 0 crashes, 0 unexpected clean |
| Promise Machine, demonstrations, source lints and currency checks | exit 0 | Command exits; audit-record structural diagnostics are preserved in the round record |

The signed implementation and Warden commits plus the final clean-tree check are
the last evidence items; no push, publication or controller transition belongs
to this record.
