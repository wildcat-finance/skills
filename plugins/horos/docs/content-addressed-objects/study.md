# Study: ship the content-addressed object rule

Held job, verbatim from `plugins/horos/skills/horos/EVOLUTION.md`
(`horos-v10.3.3`, frontier revision `content-addressed-objects`): "Ship the
content-addressed object rule whose evidence is the digest a file's own bytes
produce."

Assuming, unless corrected:

1. The exact interpreter in `.python-version` (3.14.6) with stdlib
   `unittest`; no new runtime or test dependency, matching every other rule in
   `horos.py`.
2. "Ship" means: give the drafted rule (commit `5d5aba7`, merged in pull
   request 215 and adopted into the root boundary by pull request 242) the
   frontier run it still owes. Every other Horos job left a study, a runbook,
   an audit log and an evidence bundle; this rule left none. The run therefore
   adds evidence, guard tests and documentation. It does not change the rule's
   binding condition, because the draft's own comments record those decisions
   and section 4 measures the alternatives that would change them.
3. Regenerating `.horos/boundary.json`, `.horos/census.json` and
   `.horos/candidates.json` belongs to the same step as any change that moves
   them, because `tests/test_boundary_currency.py` holds the committed boundary
   to a fresh tracked scan. At the starting ref all three are current: a
   `scan . --write` changes no tracked byte.
4. The cold-read and reconciliation of all mutable first-party marketplace
   prose, the `horos-v11.3.3` ledger row and the matching `version:` in
   `plugins/horos/skills/horos/SKILL.md` land as the run's own late step,
   after the code step and before the demonstration, as
   `plugins/hexaemeron/skills/VERSIONING.md` ("What every frontier run owes")
   requires.
5. The run starts from `main` at
   `54730d3a2fe08fa0d0d93f8fa9bcc6d6c3cee27b`, and every entry state below
   means that commit.
6. The new row's next job is the Markdown outline extractor, as the
   `horos-v9.2.3` epoch row names it, not `mature`: the epoch row named three
   jobs and expected maturity only after the third.

I will proceed on these unless corrected.

## 1. Problem statement

Horos classifies the files an agent may leave unread and records the evidence
for each exclusion. Every rule but one rests on a name, a marker string, a
signature prefix or a directory convention, which a repository can write to
invite an exclusion. The content-addressed rule is the exception: a store that
names each file by the digest of its own bytes proves its own entries, because
the digest either matches the name or it does not. The rule exists as a draft
and already binds 78 files, 7,850,052 bytes, in this repository's committed
boundary. What it lacks is the record that lets someone else trust it: guard
tests for the cases the draft never pinned, documentation in the skill and the
example, an evidence bundle with measured figures, and the ledger row that
closes the held job.

The user is an agent entering a repository under a Horos boundary, and the
maintainer who has to defend that boundary. A working prototype means:

- The rule's central property is pinned by a test that fails without it:
  when one byte of a store object changes, `horos.py check` names that object
  as drift and exits 1. Measured on the drafted rule in a disposable
  repository, the drift line is exactly
  `drift: release/objects/sha256/aa/<digest>: in the boundary but no longer
  evidenced by the tree` and the exit is 1 (design report
  `harden-record-tamper-named-as-drift`).
- The four near misses the draft left untested stay readable and are pinned:
  an unreadable store object is counted skipped, a deeper shard path
  (`objects/sha256/ab/cd/<digest>`) stays readable, an uppercase algorithm
  segment (`objects/SHA256/`) stays readable, and a tampered object surfaces at
  `check`.
- `plugins/horos/skills/horos/SKILL.md` lists the digest among the hard
  evidence grades, `plugins/horos/examples/README.md` names the fixture's two
  store files and carries a second mutation that makes `check` fail by
  tampering one of them, and `plugins/horos/README.md` no longer says the rule
  "still owes its frontier run".
- An evidence bundle at `plugins/horos/docs/evidence/skills-content-addressed.md`
  records what the rule binds on this tree and what it costs, from commands a
  reader can rerun.
- The ledger carries `horos-v11.3.3`, SKILL.md carries `version: "11.3.3"`, and
  every mutable marketplace-context block agrees with the tree.

The proving demo path, run from the repository root at the last step:

```bash
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
printf x >> plugins/horos/examples/fixture/store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
git checkout -- plugins/horos/examples/fixture/store
python3 -m unittest discover -s tests
```

The first command exits 0 with `boundary matches the tree`. The second is
green at 239 tests (235 at entry plus the four named above). The fourth exits 1
and names the tampered object as drift. The last is green, which includes
`tests/test_boundary_currency.py` and `tests/test_marketplace_prose.py`.

## 2. Prior art

In this repository:

- The rule: `CONTENT_ADDRESSED_ALGORITHMS`, `CONTENT_ADDRESSED_PARENTS`,
  `DIGEST_CHUNK_BYTES`, `content_addressed_algorithm()`,
  `digest_matches_name()` and the first branch of `classify_file()` in
  `plugins/horos/skills/horos/scripts/horos.py` (lines 129 to 194 and 410 to
  418 at the starting ref). Drafted in commit `5d5aba7` (2026-08-19), merged
  through pull request 215 (merge `378e4755`, 2026-08-19) together with the
  `horos-v9.2.3` epoch row that named this job.
- The adoption: pull request 242 (merge `496f7a10`, 2026-08-20) regenerated
  the root boundary under the rule, moving 70 objects under
  `plugins/alexandria/examples/compound-v3-phase0-v0/release/objects/sha256/`
  plus the fixture's two store files from advisory blob geometry into hard
  evidence, and froze the marking bundle's live figure into
  `plugins/horos/docs/evidence/skills.boundary.json`. Its body leaves one lead
  open: aggregating a fully verified store into one directory entry, which
  "wants a second real store to design the partial-verification fallback
  against". That second store now exists (below), so section 4 measures the
  lead as a candidate rather than carrying it forward unexamined.
- Tests: `ContentAddressedTests` in `plugins/horos/tests/test_classify.py`
  (ten tests: both layouts, all four algorithms, digest mismatch, wrong shard,
  no store parent, git-style store, uppercase hex, wrong width, counts) and
  the rule-class coverage assertion in `plugins/horos/tests/test_discipline.py`
  (`content_addressed` in the hard categories, "digest of the file's own
  bytes" among the evidence families).
- Stores the rule binds at the starting ref, from `.horos/boundary.json`: 70
  objects, 7,844,877 bytes under the compound-v3 release; 6 objects, 5,081
  bytes under `plugins/alexandria/examples/proof-backed-state-v0` (added by
  commit `73523746`, 2026-09-04); 2 files, 94 bytes in
  `plugins/horos/examples/fixture/store/`. Total 78 entries, 7,850,052 bytes.
  The ledger's "Current frontier" line says 7,844,971 bytes; that figure was
  right when the `horos-v10.3.3` row was written (70 objects plus the fixture)
  and the difference, 5,081 bytes, is exactly the proof-backed-state store
  that landed afterwards. Both figures are right for their dates; the prose
  reconciliation carries whatever the tree holds at close.
- Alexandria writes these stores: `plugins/alexandria/docs/raw-releases.md`
  line 56 names the `objects/sha256/<first-two-hex>/<digest>` layout with a
  `manifest.json` beside it.
- The previous frontier run: `plugins/horos/docs/marker-self-exclusion/study.md`
  and `runbook.md`, audit log
  `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`,
  merged as pull request 664 (merge `812a63c3`, 2026-08-27). Its study's
  section 3 defers this rule by name and its section 12 records that the
  marketplace prose trailed the tree; its step 3 reconciled that prose to the
  7,844,971 figure.

The last two merged pull requests that touched `plugins/horos`: 1062 "Scan
the Horos boundary from a clean checkout" (merge `53fba06a`, 2026-08-31) and
961 "Repair the portable sync and Horos scan disagreement" (merge `646dbff7`,
2026-08-30). Both were read. Neither touches this rule. 1062 carries one
lesson this run keeps: a boundary scanned on a machine that holds generated
files a fresh checkout lacks fails `test_the_committed_boundary_matches_a_fresh_scan`,
so every regeneration here is done from a tree where `git status` is clean
apart from the run's own tracked changes. 961 carries nothing forward for
Horos; its `carryover` is closed by its own steps.

The last two merged pull requests that changed this rule are 215 and 242,
both read above. The body of pull request 664, the previous frontier run,
cannot be read: GitHub's GraphQL and REST endpoints both return "Not Found"
for that number on 2026-09-04, and the merge commit body carries only the
title. Its unfinished work is therefore recovered from two committed sources,
the run's study (section 3, non-goals) and its audit log, and each item is
answered here by name:

- The `horos.yml` CI workflow (open since pull requests 256 and 261; the
  audit log's scoped-entry rounds record it as ask-first). Stays open. This
  run does not touch `.github/`; the root `repo` workflow and
  `scripts/run_checks.py` already run the horos suite through
  `tests/check-map-v1.json` (`horos-suite`), which is the gate this run uses.
- Widening the boundary currency guard to compare counts as well as entries
  (open lead from the Hermes rule-corpus round, restated in issue 842).
  Already the case: `diff_boundary_documents` in `horos.py` compares the
  `counts` block alongside the entries, and
  `test_new_ordinary_records_without_a_refresh_are_count_drift` pins
  `.horos/boundary.json#counts` as drift when tracked files are added without
  a refresh. Issue 842's reservation still stands: `counts.files_walked`
  moves with the worktree while every entry stays identical, so the counts
  comparison can fail on a field that is not evidence. Nothing here changes
  the guard either way.
- A sibling README under `plugins/horos/docs/<job>/` explaining that the
  copies are verbatim (rounds 1 to 3 of step 1, "the controller's call").
  Refused here: three runs have now used the convention without one, and
  step 1 of the runbook names the two copies exactly as before.
- The CR-only window split and the one-byte read before a window offset
  (step 2 rounds). Not this rule; stay open as recorded.
- A census currency guard (step 2 rounds). Not built here; see issue 1130
  below for the same asymmetry on `candidates.json`. This run regenerates all
  three `.horos` artefacts in the same commit whenever one moves.

Audit records. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
was run from the target root on 2026-09-04 and exited 0 with every committed
synopsis matching its source, so synopsis views were read for the in-scope
records. Sources and what was read:

- `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`
  (source, 112 lines): read through its synopsis
  `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.synopsis.md`
  (8 lines, source digest
  `5cbc730c7a3ee97a3b331375d21f3ebe3e32936a3a9b964d2e793276e2fe6567`). Seven
  rounds. Every finding: S1-R1-01 low, dangling discipline links in the study
  copy, accepted in round 1 then fixed in round 2 (commit `6f36bee9`);
  S1-R2-01 medium, the committed boundary stale because the study copy
  self-excluded under the old marker rule, fixed by regeneration (commit
  `52b33a59`); S2-R1-01 low in `horos.py`, fixed. Elenchus verdicts: step 1
  round 1 null, round 2 passed, round 3 null; step 2 round 1 passed, round 2
  null; step 3 round 1 null; step 4 round 1 null. `Covered` lines carry nine
  register ids per round, all `not-applicable` in the step 1, 3 and 4 rounds
  except `comment-invited-exclusion` and `boundary-regeneration` (reviewed
  from step 1 round 2), and all `reviewed` in the step 2 rounds. `Not
  checked` in every round: the study's technical claims against
  `plugins/horos` source (gated by the code steps), and in steps 3 and 4 the
  classifier code beyond figure checks because those diffs touched prose only.
  `Leads not pursued`, all seven rounds, are the five items answered by name
  above plus two accepted as designed: candidate entries never gate the exit
  code, and the root suite's inoculation summary line is another plugin's
  telemetry. The step 3 lead about the epoch row's historical 7,844,877 figure
  is the same reading section 2 gives above.
- `audit/AUDIT.md` (source, 14,172 lines): the Horos rows were grepped in its
  synopsis `audit/AUDIT_SYNOPSIS.md` (426 lines, source digest
  `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`). The
  scoped-entry rounds (2026-08-20) record the `horos.yml` lead, and the
  Ephoros alert-runbook rounds (2026-08-21) record `E319-S2-R1-04` low, a
  boundary not regenerated after fixtures were added, resolved by regeneration.
  Several of those legacy rows print `[missing legacy field: ...]` for
  audit-schema, covered, not-checked and elenchus-verdict; those fields remain
  unknown here.
- `plugins/horos/audit/` does not exist; there is no per-plugin Horos audit
  file to read.

Open issues touching Horos, each read on 2026-09-04:

- 842 "the boundary and the tree disagree inside a run worktree" (open). This
  run works in a worktree under `tmp/fiat/`. Its two observations hold here:
  `.horos/boundary.json` has no `audit/` entry while synopsis files exist, and
  `counts.files_walked` follows the worktree. Neither is caused by this rule
  and neither is fixed here. The currency guard compares counts as well as
  entries (`diff_boundary_documents` in `horos.py`), so this run's
  regenerations are held to both, and step 1 met `.horos/boundary.json#counts`
  drift when it committed two files, which is why regeneration lands in the
  same commit as any change that moves the boundary. Refused by name.
- 896 "the boundary mixes file and directory entries without saying so"
  (open). The selected design adds no directory entry; the content-addressed
  entries stay per file, so an exact-path consumer finds every one of them.
  The aggregation candidate in section 4 would have added four directory
  entries hiding 78 files from exact match, which is the failure mode this
  issue names, and it is refused on that measurement. Stays open.
- 1130 "framework-77: .horos/candidates.json is tracked, written by the
  scanner and checked by nothing" (open). Not resolved here. This run
  regenerates `boundary.json`, `census.json` and `candidates.json` together
  whenever a step moves them, so it does not add to the drift, and the
  currency check the issue asks for is Protasis's call on which skill it
  upgrades, not this run's.
- 378, 379, 380 (horos-1, horos-2, horos-3 wishes; open). Generation work
  behind the frontier, untouched here. 380's verified exclusion list is the
  natural consumer of the property this run pins (a `check` that re-derives
  before it prints), and is noted as such in the evidence bundle, nothing
  more.

In the organisation's other repositories: the two censuses Horos holds,
`plugins/horos/docs/evidence/v2-protocol-census.json` (236 files) and
`wildcat-app-v2-census.json` (1,113 files), show `(no suffix)` rows of 3,983
and 782 bytes with no boundary bytes; neither tree holds a content-addressed
store, so the rule changes nothing there and no re-marking is owed.

Outside: the OCI image layout specification names `blobs/<alg>/<encoded>`,
the flat layout the draft accepts. Git's loose object store,
`objects/<xx>/<38 hex>`, names no algorithm and digests a
`<type> <size>\0` header the raw bytes do not carry; the draft refuses it in
a comment and a test, and this study does not reopen that. npm's cacache
lays out `content-v2/<algorithm>/<xx>/<yy>/<rest>`, where the name is the
digest with its first four hex characters moved into two shard directories;
section 4 measures it as a candidate widening.

## 3. Constraints and non-goals

Constraints:

- Starting ref: `main` at `54730d3a2fe08fa0d0d93f8fa9bcc6d6c3cee27b`, on a
  branch cut from it.
- Toolchain: the interpreter in `.python-version` (3.14.6), stdlib only;
  `pyproject.toml` declares the supported minor. No new dependency.
- Entry state, measured on 2026-09-04: `python3 -m unittest discover -s tests`
  1207 tests OK in 91.5 s; `python3 -m unittest discover -s plugins/horos/tests
  -t plugins/horos` 235 tests OK in 4.3 s; `horos.py check .` exits 0 with
  `boundary matches the tree`; `horos.py scan . --write` changes no tracked
  byte. The root boundary holds 2,519 files walked, 78 `content_addressed`
  entries and zero candidates.
- Host condition carried from the previous run: this machine sets
  `commit.gpgsign=true` globally and the suite helpers do not neutralise it,
  so every suite command in the runbook carries
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`.
  Both suites above were run with it.
- The repository's check rule (`AGENTS.md`, "Checks for changes to this
  repository"): `python3 scripts/run_checks.py` selects from the diff through
  `tests/check-map-v1.json` and refuses a changed path with no declared owner;
  `--full` runs every declared check. Every step exit names the root suite
  and the horos suite directly as well.
- Boundary schema stays 2. The rule's binding condition is unchanged: two
  layouts (`blobs/<algorithm>/<digest>` and
  `objects/<algorithm>/<shard>/<digest>` with the shard a proper prefix),
  four algorithms (`sha1`, `sha256`, `sha384`, `sha512`), lowercase hex of
  exactly the algorithm's width, shape gating the read, a chunked whole-file
  read at `DIGEST_CHUNK_BYTES`, and first position in `classify_file`. Each
  is a decision the draft records in a comment or a test.
- Evidence strings may not change, because the committed boundary and the
  discipline test quote them.
- `plugins/horos/AGENTS.md` holds: no network, no execution of inspected
  source, writes confined to the target's `.horos/`.
- Prose gates: `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`
  exit 0 on every shipped document; the marketplace-prose test
  `tests/test_marketplace_prose.py` on every mutable block.

Boundary tiers for the build:

- Always: both suites before a commit; the imprimatur lint on every shipped
  document; `horos.py check .` exit 0 at every step exit; regenerate the
  three `.horos` artefacts in the same commit as any change that moves one;
  record a measurement (section 10) before claiming any cost.
- Ask first: adding a dependency; changing the boundary schema, an evidence
  string or any CLI flag; adding a layout or an algorithm; touching
  `.github/`; changing `CONTENT_ADDRESSED_PARENTS` or `DIGEST_CHUNK_BYTES`.
- Never: hand-edit `.horos/boundary.json`; edit `plugins/horos/examples/`
  to dodge a failing test; delete a failing test; skip a test to hide a host
  condition rather than naming it; claim a command ran when it did not.

Non-goals, deferred past this prototype:

- Any new layout: npm cacache two-level shards, pnpm, cargo and nix stores,
  IPFS content identifiers, uppercase hex, git's loose objects. Section 4
  measures the first and refuses it; the rest have no witness store in any
  home tree either.
- Aggregating a verified store into one directory entry (pull request 242's
  lead). Measured and refused in section 4; the lead now points at issue
  896's resolution, which decides what a directory entry means before one
  more kind of them is added.
- A size cap on the digest read. The draft reads whole files by design and
  the largest object here is 6,452,358 bytes; the cost is measured in section
  10 and the concern is a risk-register line, not a change.
- The Markdown outline extractor (the next held job).
- A `horos.yml` workflow; a counts-comparing currency guard; a
  `candidates.json` or `census.json` currency check (issue 1130).
- Re-marking external repositories: neither holds a store.
- The `SOURCES.md` refresh: `VERSIONING.md` owes it for Alexandria,
  Tabularium, Lazarus and Probitas runs, not Horos.

## 4. Design options

The question is what shipping adds over the draft. Four candidates; the
closed record at `.hexaemeron/design-evidence.json` selects one, and every
result below is a report produced by
`python3 .hexaemeron/design-reports/resolve.py <candidate> <criterion>`
from the tree at the starting ref or from a disposable repository driven
through the real `horos.py`.

- `harden-record`. Keep the rule's binding condition unchanged. Add the four
  guard tests the draft lacks (tampered object named as drift at `check`;
  unreadable store object counted skipped; deeper shard stays readable;
  uppercase algorithm segment stays readable). Document the rule in
  `SKILL.md`, the fixture README (store paragraph plus a tamper mutation) and
  the plugin README. Write the evidence bundle, the committed study and
  runbook, the reconciled prose and the `horos-v11.3.3` row. Trade: no new
  bytes are bound anywhere; the run's whole value is evidence and pinning.
- `widen-layouts`. Everything in `harden-record` plus npm cacache's two-level
  shard layout, rebuilding the digest from the two shards and the remainder
  name. Trade: one more shape gate and a digest no longer equal to the name,
  for a layout no home tree holds.
- `aggregate-entries`. Everything in `harden-record` plus one directory entry
  per store whose every file verifies, with a per-file fallback for a partly
  verifying store. Trade: a boundary document one third the size, for four
  directory entries that hide 78 files from an exact-path lookup while issue
  896 is open.
- `record-only`. No code and no test change; only the documents, the prose
  reconciliation and the ledger row. Trade: the cheapest run, leaving the
  draft's central property unpinned.

Criteria, one per concern plus a second correctness gate, all at stage
`selection` and blocking `design-lock`:

| id | concern | form | rule | harden-record | widen-layouts | aggregate-entries | record-only |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `open-hardening-gaps` | correctness | gate | equals 0 | 0 | 0 | 0 | 4 (fail) |
| `added-layouts-unwitnessed` | correctness | gate | equals 0 | 0 | 1 (fail) | 0 | 0 |
| `exact-match-misses` | compatibility | gate | equals 0 | 0 | 0 | 78 (fail) | 0 |
| `boundary-document-bytes` | space | metric | minimise | 37,014 | 37,014 | 12,587 | 37,014 |
| `tamper-named-as-drift` | recovery | gate | equals 1 | 1 | 1 | 1 | 1 |
| `store-hash-ms` | time | gate | at most 250 | 5 | 4 | 4 | 5 |

How each was measured:

- `open-hardening-gaps` enumerates six gaps in the draft and verifies each is
  open on the tree by a grep that finds nothing: no test mentions a tampered
  object, no store test uses `chmod`, no test files a digest under
  `digest[2:4]`, no test uses `SHA256/`, the `SKILL.md` hard-evidence list
  names no digest, and the fixture README names no store path. The value is
  the number of those gaps a candidate's declared scope leaves open. That is
  derived from the candidate definition against verified data, and the
  derivation rule is written in `resolve.py` beside the data. `record-only`
  closes only the two documentation gaps.
- `added-layouts-unwitnessed` searches 2,550 paths (this tree's `git
  ls-files` plus every entry and candidate path in the v2-protocol and
  wildcat-app-v2 boundaries) for the shape each added layout would need.
  `widen-layouts` adds one layout and finds no witness.
- `exact-match-misses` builds the aggregated document from the committed
  boundary (four store roots: three real stores and the fixture's two) and
  counts store files no longer present as exact paths.
- `boundary-document-bytes` renders each candidate's document through
  `horos.render`.
- `tamper-named-as-drift` creates a git repository with one sharded object,
  scans it with `--write`, checks it (exit 0), overwrites the object's bytes
  and checks again: exit 1 and exactly one `drift:` line naming the object.
  All four candidates keep the rule that produces this.
- `store-hash-ms` hashes all 78 objects (7,850,052 bytes) through
  `digest_matches_name`, median of five runs.

Selection: three gates remove `record-only`, `widen-layouts` and
`aggregate-entries`; `harden-record` is the unique frontier.
`python3 <plugin_root>/skills/protasis/scripts/design_evidence.py
.hexaemeron/design-evidence.json --transition design-lock` exits 0. The
aggregation candidate's space advantage is real and recorded; it is refused
on the compatibility gate, not on size.

What `harden-record` builds, by home:

- `plugins/horos/tests/test_boundary.py` (or a new `test_content_addressed.py`
  if the boundary module is the wrong home): the tamper test on a disposable
  git repository and the unreadable-object test (skipped with a named reason
  when the suite runs as root, matching the existing unreadable-file test).
- `plugins/horos/tests/test_classify.py`, `ContentAddressedTests`: the deeper
  shard and uppercase algorithm segment near misses. Expected suite count
  239.
- `plugins/horos/skills/horos/SKILL.md`: the digest joins the hard-evidence
  list in rule 4, and one short paragraph says what the rule reads, why it
  runs first and what it refuses.
- `plugins/horos/examples/README.md`: the store files join the first
  paragraph; a second mutation section tampers an object.
- `plugins/horos/README.md`, "Start here": drop "The content-addressed-object
  rule still owes its frontier run".
- `plugins/horos/docs/evidence/skills-content-addressed.md`: the figures in
  sections 2 and 10, the drift demonstration, the refused candidates with
  their measured values, and the pointer to issue 380.
- `plugins/horos/docs/content-addressed-objects/study.md` and `runbook.md`:
  the receipted copies.
- `plugins/horos/skills/horos/EVOLUTION.md`, `plugins/horos/skills/horos/SKILL.md`
  frontmatter, and every marketplace-context block: section 12.

## 5. Risk register seed

The audit loop should look hardest at the whole-file read, because it is the
only rule that reads past a bounded prefix, and at the regeneration and
prose steps, because that is where the previous run's findings landed.

```risk-register
whole-file-read | the digest read in digest_matches_name over any shape-matching path | the read stays chunked at DIGEST_CHUNK_BYTES with no silent truncation, and the tree's largest object (6,452,358 bytes) hashes without being held in memory whole
shape-gate-first | content_addressed_algorithm before any read | a path outside blobs or objects plus an algorithm segment never reaches the hash; docs/sha256, deeper shards and uppercase segments are pinned readable
symlink-in-store | a link filed under objects/<algorithm> | classify_file refuses links before hashing so no read leaves the root
unreadable-object | a store file the scanner cannot open | the OSError propagates, the file is counted files_skipped_unreadable and is never classified, pinned by a test that skips with a named reason as root
tamper-as-drift | check against a store whose bytes changed | the changed object is named as drift and check exits 1, pinned by a test on a disposable repository
boundary-regeneration | .horos/boundary.json, census.json and candidates.json | regenerated together in the same commit as any change that moves one, from a clean tree, and tests/test_boundary_currency.py is green
evidence-wording | the evidence string the committed boundary quotes | unchanged byte for byte; the discipline test still finds "digest of the file's own bytes"
prose-reconciliation | every marketplace-context block, the plugin README and SKILL.md | every block agrees, none says the rule still owes its run, and tests/test_marketplace_prose.py is green
ledger-row | EVOLUTION.md and the SKILL.md version | horos-v11.3.3 with the digest hexctl computes over status, revision, frontier and next job; the next job is the Markdown outline extractor, not mature
self-witness | the fixture's two store files as the only flat-layout witness | the evidence bundle says the flat layout is witnessed by the OCI specification and the fixture only, never counting the fixture as a real store
```

## 6. Glossary seeds

- Content-addressed store: a directory whose files are named by the digest of
  their own bytes, under `blobs/<algorithm>/` or `objects/<algorithm>/`.
- Flat layout: `blobs/<algorithm>/<digest>`, as an OCI image lays out blobs.
- Sharded layout: `objects/<algorithm>/<shard>/<digest>`, the shard a proper
  prefix of the digest it files.
- Shape gate: the path test in `content_addressed_algorithm` that decides
  whether a file is worth hashing at all.
- Hard evidence: a grade that binds agents; the only grade that reaches
  `boundary.json`.
- Drift: a boundary entry the tree no longer evidences, or a sink the tree
  evidences that the boundary lacks; `check` prints one line per case.
- Tamper test: the guard that changes one object's bytes and expects `check`
  to name it.
- Evidence bundle: the committed record under `plugins/horos/docs/evidence/`
  with the figures a run measured and the commands that reproduce them.
- Frontier digest: SHA-256 over `status|revision|frontier|next_job` plus a
  newline, as `hexctl` computes it for the ledger's final row.

## 7. Sources

- `plugins/horos/skills/horos/scripts/horos.py` at the starting ref, lines
  129 to 194 and 410 to 418.
- `plugins/horos/tests/test_classify.py` lines 277 to 369;
  `plugins/horos/tests/test_discipline.py` lines 52 to 85.
- Commit `5d5aba71cc6c954af4acb8c36f261f3e3c71dc24`, "horos: draft a
  content-addressed object rule", 2026-08-19.
- Pull requests 215 (merge `378e4755`), 242 (merge `496f7a10`), 961 (merge
  `646dbff7`), 1062 (merge `53fba06a`) in `wildcat-finance/skills`; pull
  request 664 (merge `812a63c3`), body unavailable on 2026-09-04.
- `plugins/horos/skills/horos/EVOLUTION.md`, rows `horos-v9.2.3` to
  `horos-v10.3.3`; `plugins/hexaemeron/skills/VERSIONING.md`, "Frontier
  discipline" and "What every frontier run owes".
- `plugins/horos/docs/marker-self-exclusion/study.md` sections 3 and 12, and
  `runbook.md` steps 1 to 4.
- `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.synopsis.md`;
  `audit/AUDIT_SYNOPSIS.md`, Horos rows; the synopsis check output of
  2026-09-04.
- Issues 378, 379, 380, 842, 896, 1130 in `wildcat-finance/skills`.
- `.horos/boundary.json`, `.horos/census.json`,
  `plugins/horos/docs/evidence/v2-protocol-census.json`,
  `plugins/horos/docs/evidence/wildcat-app-v2-census.json`,
  `plugins/horos/docs/evidence/v2-protocol.boundary.json`,
  `plugins/horos/docs/evidence/wildcat-app-v2.boundary.v2.json`.
- `plugins/alexandria/docs/raw-releases.md` line 56.
- `AGENTS.md` "Checks for changes to this repository";
  `tests/check-map-v1.json` (`horos-suite`); `tests/test_boundary_currency.py`;
  `tests/test_marketplace_prose.py`.
- `.hexaemeron/design-reports/resolve.py` and the 24 reports beside it;
  `.hexaemeron/design-reports/root-suite-entry.txt`.
- OCI image layout specification (`image-layout.md` in the
  opencontainers/image-spec repository), the `blobs/<alg>/<encoded>` rule.

## 8. Signals, and the questions behind them

None for on-call, and here is why: Horos is a command an agent or a person
runs from a terminal, and nothing this run ships runs unattended. The
questions that do get asked are answered by exit codes and lines already
emitted: "does the committed boundary still match the tree?" is `check`'s
exit code and its `drift:` lines, now proven to fire on a tampered object;
"did a step leave the boundary stale?" is `tests/test_boundary_currency.py`;
"did the prose drift from the tree?" is `tests/test_marketplace_prose.py`.
[ephoros](../../../hexaemeron/skills/ephoros/SKILL.md) owns what a signal must
carry; none is added.

## 9. Boundaries, per capability

One boundary, already open in the draft: the scanner reads whole files whose
path is shaped like a store object, from a repository it does not trust.
Worth taking there: time, by planting a very large file under a store-shaped
path; a read outside the root, by a symlink filed as an object; a crash, by
an unreadable file. Controls: the shape gate runs before any read and the
name must already be exactly the algorithm's hex width; the read is chunked
at 1 MiB so memory stays bounded whatever the size; `classify_file` refuses
symlinks before statting; an `OSError` is counted as skipped, not classified.
The time cost of a hostile large file is accepted and named in the risk
register rather than capped, because a partial digest verifies nothing and a
cap would turn the one self-proving rule into a fail-open guess. No network,
no subprocess, no secret and no dependency is added.
[phylax](../../../hexaemeron/skills/phylax/SKILL.md) owns the boundary list
and the controls; the tamper test and the unreadable-object test are this
run's additions to them.

## 10. The budget, or its absence

Two budgets, both measured on this tree on 2026-09-04:

- Hashing every store object the boundary classifies (78 files, 7,850,052
  bytes) stays at or under 250 ms. Measured: 5 ms, median of five runs
  (design report `harden-record-store-hash-ms`). Command:
  `python3 .hexaemeron/design-reports/resolve.py harden-record store-hash-ms`.
- A whole-tree scan stays under 1 s. Measured: `/usr/bin/time -p python3
  plugins/horos/skills/horos/scripts/horos.py scan .` reports 0.15 s real,
  three runs; in-process `scan_tree` medians ranged 134 ms to 173 ms across
  the resolver's runs, with the rule's share inside the run-to-run noise.

The guard tests add one disposable git repository each; the horos suite is
expected to stay under 10 s (4.3 s at entry). No step may claim a cost or a
saving without rerunning the first command.
[metron](../../../hexaemeron/skills/metron/SKILL.md) owns what a budget
carries and how it is checked.

## 11. The fail-closed posture

What stops the run: a red root suite or horos suite; `horos.py check .`
exiting 1 at a step exit; `tests/test_boundary_currency.py` naming drift;
`tests/test_marketplace_prose.py` naming a block that disagrees;
`imprimatur.py` exiting non-zero on a shipped document; a design report
whose digest no longer matches the record. The guard convention: a fix
ships with a test that fails without it, named for the failure it pins, in
the module that owns the behaviour. The tamper test is the guard for the
rule's central property and the unreadable-object test the guard for its
fail-open edge; both are written before any document claims the property.
[elenchus](../../../hexaemeron/skills/elenchus/SKILL.md) owns the triage
order and the guard rule.

## 12. Decisions and their homes

[hypomnema](../../../hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each lives.

- Shipping the rule with its binding condition unchanged, and refusing the
  cacache widening and the aggregation on measured gates, is expensive to
  reverse: the next run that wants either must re-measure against the same
  record. Home: the closed design record
  `.hexaemeron/design-evidence.json` and its reports, the committed study and
  runbook copies at `plugins/horos/docs/content-addressed-objects/`, and the
  evidence bundle at `plugins/horos/docs/evidence/skills-content-addressed.md`.
- The whole-file read without a size cap is a decision a future reader will
  want reasons for. Home: the comment above `DIGEST_CHUNK_BYTES` in
  `horos.py` already carries it; the evidence bundle records the measured
  cost beside it.
- The ledger row. Home: `plugins/horos/skills/horos/EVOLUTION.md`, written by
  the run's prose step: `horos-v11.3.3`, axis `evolution`, frontier revision
  `markdown-outline-extractor`, status `open`, evidence linking the committed
  study and the evidence bundle, next job the Markdown outline extractor as
  the `horos-v9.2.3` epoch row names it, with maturity expected after it.
  `plugins/horos/skills/horos/SKILL.md` frontmatter moves to
  `version: "11.3.3"` in the same commit, and the frontier digest is the one
  `hexctl` computes over status, revision, frontier and next job.
- The marketplace-prose reconciliation. Cold-read findings at the starting
  ref: the "Current frontier" text in the ledger header, `plugins/horos/README.md`,
  `plugins/horos/AGENTS.md` and `plugins/horos/skills/horos/SKILL.md`
  says the drafted rule "still owes its own frontier run" and carries the
  7,844,971 figure; the plugin README's "Start here" repeats the debt. Home:
  the mutable blocks themselves, held by `tests/test_marketplace_prose.py`,
  with the decision recorded in the run's audit log.
