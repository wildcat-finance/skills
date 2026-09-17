# Study: horos-33, evidence files readable by rule

Task: [skills#1383](https://github.com/wildcat-finance/skills/issues/1383),
`kickoff/horos-33: evidence files readable by rule`, `Fiat-Required: 1`,
carryover row `prerequisite-1356 | duplicate | https://github.com/wildcat-finance/skills/issues/1356`.
Run branch `fiat/1383-horos-33-evidence-files-readable-by-rule`, cut from
`main` at `9599fa46e8e2c5436a0dae4327c8e5b72f5159a9`.

Assuming, unless corrected:

1. The toolchain is the interpreter pinned in `.python-version` (3.14.6) with
   stdlib `unittest` and the local `git`. No dependency is added.
2. "Readable" means no entry in a committed `.horos/boundary.json` covers the
   path, by exact path or by a directory entry ending in `/`. Candidates never
   bind. A file kept readable by rule is also left out of
   `.horos/candidates.json`. Readability establishes nothing about a file's
   content, its correctness or permission to distribute it (issue body and its
   comment of 2026-09-13).
3. The four families are four exact, case-sensitive basenames, one
   producer-fixed name each: `manifest.json` (an Alexandria release root),
   `statement.json` (named by the issue; Lazarus writes it into a release),
   `SHA256SUMS` (named by the issue) and `events.jsonl` (Tabularium's
   canonical-event output in its skill and all three examples). Other control
   names (`release.json`, `coverage.json`, `release-statement.json`,
   `SHA512SUMS`, case variants) get no built-in protection; a maintainer covers
   them with an explicit readable attribute.
4. **This assumption chose the design.** The target maintainer's
   `.gitattributes` decides first, in both directions. A linguist attribute
   that resolves set keeps a file excluded even when its name is a family name;
   one that resolves unset keeps any file readable. The family rule overrides
   only Horos's own heuristics. Reasons: the issue says "The target maintainer
   owns any explicit readable attribute"; #1356 says the repository maintainer
   owns the `.gitattributes` rule and that Horos never writes a rule on its own
   authority; "readable regardless of geometry" names geometry, not the
   maintainer's rule. If the maintainer wants the four names readable against
   their own set lines, candidate `family-names-first` is the reading instead,
   and because a receipted design record cannot be amended, that needs a new
   run.
5. The explicit readable attribute is Git's own negation of the two attributes
   Horos already reads: `-linguist-generated`, `-linguist-vendored`,
   `linguist-generated=false` and `linguist-vendored=false`.
   `!linguist-generated` and `!linguist-vendored` return a path to unspecified.
   No Horos-specific attribute name is added.
6. The declared target boundaries for this public run are the committed
   boundaries in this repository: the root, `plugins/horos/examples/fixture`,
   `plugins/horos/examples/scoped-entry` and the five frozen copies under
   `plugins/horos/docs/evidence/`. The private archive target delivered under
   #1356 keeps the retention check the maintainer holds; this run neither
   reruns nor names it. #1374 and #1389 are later integration samples, not
   prerequisites, as the issue says.
7. The change alters Horos classification, so under
   `plugins/hexaemeron/skills/VERSIONING.md` it is a generation, not a frontier
   advance: Horos stays `mature` and gains exactly one generation row,
   `horos-v12.4.3` against the starting ledger. The runbook declares it through
   a `version-relations` block so `done resolve-versions` checks it against the
   integration base. The plugin package version `0.1.1` does not move.
8. Root-suite exits are held on a clean detached worktree of the committed
   head. Inside a `tmp/fiat/` run worktree the root suite fails two
   `test_agent_instruction_corpus` tests because the prover reads the run's own
   `.hexaemeron/design-evidence.json` (skills#1228 history).

I will proceed on these unless corrected.

## 1. Problem statement

Horos marks which files an agent may leave unread. Release manifests,
statements, checksum lists and canonical-event ledgers are the files a reader
needs to verify a release, and they often look like the sinks Horos exists to
exclude: large, single-line, generated, sitting in a build directory beside
archive parts. The issue asks for readable-by-rule coverage of those four
families, with geometry and near-miss tests, green against every committed
boundary.

Measured at the starting commit, with reports under
`.hexaemeron/design-reports/`:

- Geometry alone never binds. A 64 MiB single-line `statement.json` classifies
  as a `blob` candidate in 0.14 ms. Two family files in this tree are already
  geometry candidates in `.horos/candidates.json`:
  `plugins/alexandria/examples/compound-v3-phase0-v0/release/manifest.json`
  (76,773 bytes, no newline) and
  `plugins/tabularium/examples/aave-v4-v0/events.jsonl` (mean line length above
  400). A candidate is an invitation to promote.
- A corroborated generated directory swallows the families. With three
  single-line bundles beside a 64 MiB family file in `out/`, the sample
  corroborates `out/` and one hard entry covers the family file. The starting
  classifier fails 8 of 36 family checks: four in that served directory and
  four under a maintainer's readable line (`guard-tests-only--family-cases-failing`).
- Horos ignores an explicit readable attribute. Under
  `releases/** linguist-generated` followed by a `-linguist-generated`,
  `linguist-generated=false`, `!linguist-generated` or nested unset line for
  one file, Horos excludes the whole `releases/` directory while
  `git check-attr` reports that file unset, false or unspecified: 5 of 5
  not-set probes. Across the design corpus the starting classifier contradicts
  Git for 8 of 44 paths (`guard-tests-only--git-attribute-mismatches`). Each
  such entry cites a Git attribute Git does not report, which the
  `horos-boundary-scan` promise refuses as an unevidenced hard exclusion.

The users are agents and contributors reading archive and serving repositories
under a Horos boundary, and the maintainers who own those repositories' rules.
The issue comment names Miskatonic contributors and reviewers at W02, W05 and
W12 as consumers.

A working prototype means:

1. For each family, a test that fails if the boundary excludes a 64 MiB
   geometry-shaped representative in three placements: a served generated
   directory (`out/` with three single-line bundles); under a maintainer's broad
   set pattern plus an explicit readable line for that file; and beside a
   neighbouring archive part `ledger.tar.part-aa` that a maintainer rule
   `*.part-* linguist-generated` excludes. In every placement the part and the
   siblings stay hard entries, and the near misses `manifest.jsonl`,
   `statements.json`, `SHA256SUMS.txt`, `events.json` and the case variants
   `Manifest.json`, `Statement.json`, `sha256sums`, `Events.jsonl` get no
   protection. The module is `plugins/horos/tests/test_readable_families.py`;
   at least 4 of its tests fail by assertion against the starting classifier
   (conformance cell `family-guards-failing-on-base`).
2. A maintainer's set attribute still excludes a family-named file, for all
   four names.
3. For the attribute cases (unset, `=false`, `!`, nested unset, an unset line
   before a later set line, a macro definition line), every tracked path's hard
   coverage equals the set state `git check-attr` reports.
4. No committed boundary in this repository covers a family-named file that
   Git does not resolve set: the root, fixture and scoped-entry boundaries by
   tracked path, and the five frozen copies by entry path. The module is
   `plugins/horos/tests/test_committed_family_retention.py`; conformance cell
   `committed-boundaries-covering-family-files` records 0.
5. Regenerating the root, fixture and scoped-entry boundaries changes no
   pre-existing hard entry and no boundary field; only the two family
   candidates named above leave the root `candidates.json` (measured 0 and 2).
6. The security-review exception is unchanged: `No reading boundary applies
   during security review.` stays in `plugins/horos/skills/horos/SKILL.md` and
   "never applies during security review" stays in the adoption stanza
   (conformance cell `security-review-exception-intact`).
7. The shipped example demonstrates both readable routes and one mutation that
   makes `check` fail by name.
8. `horos.py check .` exits 0 at every step exit, the Horos suite passes, and
   the root suite passes on a detached snapshot.

The demo path, from the repository root at the last step:

```bash
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
```

Then append one line setting `linguist-generated` on the fixture's
attribute-readable checksum file to
`plugins/horos/examples/fixture/.gitattributes`: `check` on the fixture exits
1 and names as drift the entry that now covers that file.
`git checkout -- plugins/horos/examples/fixture/.gitattributes` restores it and
the check exits 0. The root suite runs on a detached snapshot of the run head,
and the three conformance resolvers in section 4 write their reports before
integration.

## 2. Prior art

### 2.1 In this repository

Classification at the starting commit, read in
`plugins/horos/skills/horos/scripts/horos.py`:

- Directories are decided first. A directory named `build`, `dist`, `out` or
  `storybook-static` (generated), or `bower_components`, `node_modules`,
  `third_party`, `thirdparty`, `vendor` or `vendored` (vendored), becomes one
  hard entry when a package-manager structure or three quarters of its first
  eight sorted files corroborate it; otherwise it is an advisory candidate
  entry and is walked. A directory that a `.gitattributes` pattern matches
  becomes one hard entry.
- For each file a `.gitattributes` match comes first: innermost attribute file
  first, first matching line, set forms only (`attr` or `attr=true`);
  `-attr`, `attr=false` and `!attr` are ignored. `classify_file` follows: the
  digest of a store object's own bytes, lockfile names, SQL under `migrations`
  (candidate), then the 4,096-byte prefix (file signature, null byte as
  candidate, SVG as candidate, comment-led generator marker, sourcemap,
  geometry as candidate at 16,384 bytes or more), then two 2,048-byte windows
  for files over 65,536 bytes.
- Classification is fail-open, and only hard evidence reaches `boundary.json`.

Two further gaps in the same parser, measured and pre-existing. A macro
definition line such as `[attr]gen linguist-generated` is read as a pattern,
so a file named `agen` becomes a hard entry while Git leaves it unspecified,
and the macro is never expanded (`api.pb.go` marked `gen` stays readable while
Git sets it). Patterns go through `fnmatch`, which differs from Git's
wildmatch: `docs/*.md` binds `docs/api/x.md` in Horos but not in Git, and
`docs/**/GUIDE.md` binds `docs/GUIDE.md` in Git but not in Horos.

Committed boundaries: the root `.horos/boundary.json` (134 entries, five of
them directories, 3,836 files walked; `candidates.json` holds 163),
`plugins/horos/examples/fixture/.horos/boundary.json` (9 entries),
`plugins/horos/examples/scoped-entry/.horos/boundary.json` (2), and five frozen
copies under `plugins/horos/docs/evidence/`. The tree tracks 28 family-named
files (21 `manifest.json`, 5 `events.jsonl`, 2 `statement.json`, no
`SHA256SUMS`), and no hard entry covers any of them. At their marking commits,
`wildcat-finance/v2-protocol` `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`
(236 files) tracks no family-named file, and `wildcat-finance/wildcat-app-v2`
`9b8b6d5d6db06428c5b539f267623277b65315cd` (1,113 files) tracks one,
`public/manifest.json`, outside its only directory entry `storybook-static/`
(GitHub Git trees API, read 2026-09-17).

Producers: Alexandria reads `manifest.json` at a release root
(`plugins/alexandria/scripts/alexandria_lib/derivation.py`, line 233). Lazarus
fixes `STATEMENT_NAME = "statement.json"` and `RELEASE_NAME = "release.json"`
(`plugins/lazarus/scripts/lazarus_lib/release.py`, lines 54 and 57).
Tabularium's build writes `--out <release-dir>/events.jsonl`
(`plugins/tabularium/skills/tabularium/SKILL.md`, line 108). Ariadne's replay
takes a `<statement.json>` argument. No producer here writes `SHA256SUMS`.

The maintainer's specification `plugins/horos/docs/refinement/maintainer-spec.md`
grades a Git attribute as hard and a directory name, filename convention or
geometry heuristic alone as candidate, has maintainers promote candidates
through repository-specific rules, and keeps security reviews outside every
boundary. The studies under `plugins/horos/docs/content-addressed-objects/`,
`marker-self-exclusion/` and `scoped-entry/` set the design-record and
guard-test conventions reused here.

Pinned files the build must respect.
`plugins/horos/skills/horos/SKILL.md` is bound by whole-file SHA-256 in
`tests/fixtures/agent-instruction-v1/manifest.json` and in the
`horos-boundary-check` fixture (`compact.wai`, `model.json`,
`source-spans.json`), whose reviewed span is bytes 12,450 to 13,468 of the
15,297-byte file. `plugins/horos/tests/test_boundary.py` is pinned in
`tests/fixtures/promise-machine/runtime/horos-boundary-scan.json` and
`tests/promise_machine_coverage.json`. `horos.py` has no live digest pin
outside audit records, and no tracked file outside it calls
`parse_attribute_file`, `match_attribute_scopes` or `match_gitattributes`.

### 2.2 The last merged pull requests that changed Horos

The last two merged pull requests that changed Horos classification or its
tests are [skills#1469](https://github.com/wildcat-finance/skills/pull/1469)
and its revert [skills#1470](https://github.com/wildcat-finance/skills/pull/1470),
both merged 2026-09-08. #1470 removed every file #1469 added, so neither
leaves anything on the starting tree. #1469's carryover `horos-ci-in-app-v2`
stays with #1357, which is open. One measurement from #1469 carries into this
study: a classifier change that rewrites an evidence string drifts an adopting
repository's committed boundary, which is why section 4 measures
committed-boundary drift. The later merges touching `plugins/horos/`, #1153 and
#1638, changed only `plugins/horos/PROMISE_MACHINE.md`.

The last two Fiat runs that changed the classifier,
[skills#1231](https://github.com/wildcat-finance/skills/pull/1231) and
[skills#1257](https://github.com/wildcat-finance/skills/pull/1257), carried
these rows forward:

| Carryover | Issue on 2026-09-17 | Here |
| --- | --- | --- |
| `candidates-json-currency` | #1130 open | This run changes the root `candidates.json` and regenerates it in the same commit; the missing check stays open |
| `store-directory-entries` | #896 open | A split adds file entries without changing the matching rule; stays open |
| `boundary-and-tree-in-a-worktree`, `counts-in-currency-guard` | #842 open | Root checks run on a detached snapshot; stays open |
| `prover-reads-any-run-design-record` | #1228 closed | The in-worktree root-suite pair is still expected; exits use a detached snapshot |
| `census-has-no-currency-check` | #1253 closed | `HorosCensusCurrencyTests` guards it; the census is regenerated with every tracked change |
| `fixture-repin-carried-counts`, `before-span-repin-cost` | #1192 open | The `SKILL.md` edit sits before the reviewed span and re-pins with an offset delta |
| `horos-ci-workflow` | none | Not decided here |
| `results-files-carry-unread-rows`, `codeql-bad-html-filter-false-positive`, `elenchus-verdict-on-a-digest-rebind`, `deep-list-outline-cost` | outline work | Out of scope |

### 2.3 In the organisation

[skills#1483](https://github.com/wildcat-finance/skills/issues/1483) closed
2026-09-16T03:19:56Z and
[skills#1356](https://github.com/wildcat-finance/skills/issues/1356) closed
2026-09-16T09:55:03Z, both as completed. Their public maintainer comments
state that the maintainer adopted the exact archive-part classification rule,
SHA-256 `df4e446de062cd20d1575feb46951163c96fcfd7b0e378804b48da8996ab76fb`,
and approved retention of manifests, statements, checksums and canonical-event
JSONL; that canonical-ledger coverage remains synthetic because no tracked
ledger was present; that W00 identity remains unknown; that the accepted
case-mode, timeout, race and extractor limits remain; and that #1383 retains
the general readable-rule extension.

As the issue directs, the selected design was checked for overlap against the
private archive target delivered under #1356, held by the maintainer. The
design only adds readability, keeps a set archive-part rule excluding parts,
and contradicts neither the adopted rule nor the approved retention. Nothing
from that target is recorded here.
[skills#1374](https://github.com/wildcat-finance/skills/issues/1374)
(ariadne-24) and [skills#1389](https://github.com/wildcat-finance/skills/issues/1389)
(alexandria-39) are open. The served-directory case takes its shape from the
issue's own sentence about a served read-only artefact, not from either.

### 2.4 Outside

- Git's attributes documentation (`gitattributes(5)`): a later matching line
  in one file overrides an earlier one, a deeper `.gitattributes` overrides a
  shallower one, `-attr` unsets, `!attr` returns to unspecified, `attr=value`
  sets a value and `[attr]name` defines a macro. `git check-attr` is the oracle
  the design record uses.
- GitHub Linguist's `linguist-generated` and `linguist-vendored` attributes,
  which Horos already reads.
- GNU coreutils `sha256sum`, the source of the `SHA256SUMS` convention.
- The in-toto Statement v1 format that `statement.json` carries.

### 2.5 Audit history

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the run worktree root on 2026-09-17 and exited 0, with all 94 sources
`committed=match`.

| Source | Read | Why that view |
| --- | --- | --- |
| `audit/AUDIT.md`, the Horos runs (initial, live-evidence, rule-classes, outline, census, Go, C++, Solidity, refinement, marking, scoped entry) | Source, lines 934 to 1615 and 4824 to 5029 | `audit/AUDIT_SYNOPSIS.md` renders table findings only and drops list-form ones, such as S2-R1-01, S2-R1-02 and S3-R1-01 of the initial run |
| `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md` | Synopsis | Whole-set check passed; 4 of 4 table findings present |
| `audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md` | Synopsis | Whole-set check passed; 7 of 7 |
| `audit/rounds/fiat-ship-the-markdown-outline-extractor-the-census-n.md` | Synopsis | Whole-set check passed; 7 of 7 |
| `audit/rounds/fiat-854-stage-the-portable-sync-before-the-horos-sca.md` | Synopsis | Whole-set check passed; 2 of 2; a Promise Machine staging run whose Horos concern is boundary currency |

Findings and leads that bear on this run, with ids and statuses as recorded:

- Initial run: S1-R1-01 to S1-R1-03 low, fixed; S2-R1-01 medium, fixed (an
  unreadable file is counted skipped); S2-R1-02 low, fixed (`classify_file`
  refuses symlinks); S3-R1-01 low, fixed (per-process temporary name). Leads
  accepted: a stat-then-open race, and the parse memory a hand-crafted
  `boundary.json` costs.
- Refinement run: S2-R1-01 high, a receipt that claimed a green suite over a
  red one, corrected and recorded. The review held that geometry stays a
  candidate wherever it is found.
- Marking run: zero findings; candidates are promoted by `.gitattributes`
  lines inside each target's reviewed diff.
- Scoped entry: S1-R1-01 and S1-R1-02 low, fixed; S3-R1-01 medium, fixed (a
  count measured in a dirty checkout); S4-R1-01 medium, fixed (a symlink in the
  middle of a path escaped the worktree); S4-R2-01 medium, fixed (the benchmark
  measured nothing). Leads: a dropped directory is walked in full before the
  drop; `check_scope` slices an already scoped candidate list.
- Marker self-exclusion: S1-R1-01 low, accepted then fixed; S1-R2-01 medium,
  fixed (stale boundary); S2-R1-01 low, fixed. Leads: a CR-only line never binds
  in a window; a line starting exactly at a window offset is dropped.
- Content-addressed objects: S1-R1-01, S1-R1-03, S2-R1-01 and S4-R1-01 low,
  fixed; S1-R1-02 low, accepted (#1228). Elenchus verdict `unguarded` in four
  rounds.
- Markdown outline: S1-R1-01 medium, fixed (stale boundary); S2-R1-01 medium
  and S2-R1-02 low, fixed, `guarded`; S3-R1-01 low, fixed; S4-R1-01 and
  S4-R1-02 low, fixed, `guarded`; S4-R2-01 low, fixed, `inconclusive`. Lead:
  the `SKILL.md` description is left to a maintainer.
- fiat-854: S2-R1-01 medium and S3-R1-01 low, fixed, `guarded`. Lead:
  `files_walked` churn belongs to #842.
- Live-evidence, rule-classes, outline, census, Go, C++ and Solidity runs: zero
  findings; their leads concern `map`, `.svgz` assets or census stat counts.

The root-log sections carry `[missing legacy field: covered]`,
`[missing legacy field: not-checked]` and
`[missing legacy field: elenchus-verdict]`, which stay unknown. The newer
rounds keep `Covered`, `Not checked` and `Elenchus verdict` in their synopses,
not restated here. No record names an unresolved product failure that
implementation must guard before product work, so this study carries no
inventory of known failures. The #1228 pair is an environment condition that
detached-snapshot exits handle.

## 3. Constraints and non-goals

Constraints:

- Starting ref `main` at `9599fa46e8e2c5436a0dae4327c8e5b72f5159a9`; run
  branch `fiat/1383-horos-33-evidence-files-readable-by-rule`.
- Toolchain: `.python-version` 3.14.6, stdlib only, `git` on the path. Suite
  commands carry `NO_COLOR=1`, because this shell sets `FORCE_COLOR=3` and that
  reddens argparse tests, and
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`.
- Entry state, measured 2026-09-17: the Horos suite
  `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos` runs
  262 tests OK in 5.8 s, and `horos.py check .` exits 0.
- Boundary schema stays 2, and every evidence string that exists today stays
  byte-identical. The public helpers `parse_attribute_file`,
  `match_attribute_scopes`, `match_gitattributes` and `gitattributes_rules`
  keep their signatures and set-only results; resolution is added beside them.
  `classify_file` keeps its signature.
- `plugins/horos/tests/test_boundary.py` is not edited. The `SKILL.md` edit
  stays outside the `### horos-boundary-check` span, changes no promise's
  semantic fields (so `tests/promise_machine_id_history.json` raises no
  `PM104`), and re-pins the agent-instruction chain in the same commit.
- After any tracked-file change, run
  `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and
  `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
  then stage `.horos/boundary.json`, `.horos/candidates.json` and
  `.horos/census.json` together.
- Before naming a step's Files, grep the repository for the SHA-256 of every
  file the step changes, and for every test asserting a guarantee the step
  restates, including every `plugins/*/tests` directory; every hit joins Files.
- No committed file, pull request body or audit record identifies the private
  archive target delivered under #1356 beyond what #1356 and #1483 state
  publicly.

Boundary tiers:

- Always: both suites before a commit, the root suite on a detached snapshot;
  `horos.py check .` exit 0 at every step exit; the three `.horos` artefacts
  regenerated together; Imprimatur on every shipped document; Phylax, Ephoros
  and Hypomnema over changed paths; a recorded measurement before any cost
  claim.
- Ask first: adding or changing a family name; a Horos-specific attribute;
  expanding Git macros or replacing `fnmatch` with Git's wildmatch; changing
  the boundary schema or an existing evidence string; bumping the plugin
  package version; touching `.github/`.
- Never: hand-edit a `.horos` artefact; edit `plugins/horos/tests/test_boundary.py`;
  delete or skip a failing test; claim a command ran when it did not; let a
  family name override a maintainer's set attribute; write anything that
  identifies the private archive target.

Non-goals, each with its reason:

- Expanding macro attributes and matching Git's wildmatch dialect. Both gaps
  are pre-existing, measured in section 2.1, and would change classification
  well beyond the four families. The selected design only stops reading a
  macro definition line as a pattern.
- Git's `core.ignorecase=true` folding. Family names stay case-sensitive, in
  line with the case-mode limit #1356 accepted.
- `$GIT_DIR/info/attributes` and `core.attributesFile`. They are not read, so
  a committed boundary depends only on tracked files.
- A boundary counter for readable-by-rule files (section 8).
- Splitting an advisory candidate directory entry around a readable file.
  Candidate entries do not bind and stay as they are.
- Any content check on a family file.
- Runs against #1374 or #1389 samples, and any change to the private archive
  target.
- #1130, #896 and #842 (section 2.2).

## 4. Design options

The question is which rule keeps the four families readable while the
maintainer's rules and the neighbouring archive parts keep working. Four
candidates. The closed record `.hexaemeron/design-evidence.json` (SHA-256
`297d62d1d270f02ec7fac097c2878225e2cbdd8becb841e3a8e7a552a56002b1`) selects
one. Each resolved cell is a report written by
`python3 .hexaemeron/design-reports/resolve.py measure <candidate> <criterion> --out <path>`,
or for the four time cells by one interleaved run of
`python3 .hexaemeron/design-reports/resolve.py measure-all-time`, from
prototypes built on the starting commit's exact classifier source.
`resolve.py explain <candidate> <criterion>` prints the per-case detail and
writes nothing.

- `guard-tests-only`. Change no rule; add the per-family tests and a
  committed-boundary guard that pin today's behaviour. Trade: no behaviour
  change and no version row, but an explicit readable attribute stays ignored
  and a corroborated build directory still swallows evidence.
- `family-names-first`. The four exact names are readable against every rule,
  including a maintainer's set attribute; attribute parsing stays set-only,
  first match. Trade: protection in every target without anyone writing a
  line, at the cost of overriding the maintainer and keeping entries that cite
  attributes Git does not report.
- `git-attribute-readable`. Resolve the two linguist attributes as Git does; an
  explicit unset keeps any file readable and splits a hard directory around it;
  no built-in names. Trade: maintainer-owned and Git-faithful, but nothing
  protects the families until someone writes a line.
- `attribute-then-family`. Git resolution first, then the four names readable
  against every Horos heuristic unless an attribute resolves set; a hard
  directory holding a readable file is split into per-file entries. Trade: the
  most code, a larger boundary wherever a split happens, and `manifest.json` is
  a common name.

| Criterion | Concern | Form | Rule | guard-tests-only | family-names-first | git-attribute-readable | attribute-then-family |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `family-cases-failing` | correctness | gate | at most 0 | 8, fail | 0 | 4, fail | 0 |
| `git-attribute-mismatches` | correctness | gate | at most 0 | 8, fail | 8, fail | 0 | 0 |
| `committed-family-files-excluded` | correctness | gate | at most 0 | 0 | 0 | 0 | 0 |
| `repository-scan-ms` | time | gate | at most 1,000 ms | 444 | 425 | 468 | 466 |
| `served-boundary-bytes` | space | metric | minimise | 431 | 2,149 | 431 | 2,149 |
| `committed-hard-boundary-drift` | compatibility | gate | at most 0 | 0 | 0 | 0 | 0 |
| `committed-candidate-drift` | compatibility | metric | minimise | 0 | 2 | 0 | 2 |
| `silent-upgrade-changes` | recovery | gate | at most 0 | 0 | 0 | 0 | 0 |
| `family-guards-failing-on-base` | correctness | conformance gate | at least 4 | pending | pending | pending | pending |
| `committed-boundaries-covering-family-files` | compatibility | conformance gate | at most 0 | pending | pending | pending | pending |
| `security-review-exception-intact` | correctness | conformance gate | equals true | pending | pending | pending | pending |

How each was measured:

- `family-cases-failing`: 36 checks, nine per family, in three disposable
  repositories per family. Geometry: a 64 MiB representative and a
  same-shaped near miss beside `ledger.tar.part-aa` under
  `*.part-* linguist-generated`. Served: `out/` holding three single-line
  bundles, the representative and the near miss. Attribute:
  `releases/** linguist-generated`, then `releases/**/<name> -linguist-generated`.
  Each placement checks that the representative is uncovered, the part and
  siblings are covered, and the near miss gets no protection.
- `git-attribute-mismatches`: 44 tracked paths in 13 disposable repositories
  (per family, the attribute case and a maintainer-excludes case; for a
  non-family file, unset, `!`, `=false`, nested unset and unset before set).
  It counts paths whose hard coverage differs from the `git check-attr` set
  state.
- `committed-family-files-excluded`: the 28 tracked family-named files against
  the root, fixture and scoped-entry boundaries as each candidate regenerates
  them, plus the entry paths of the five frozen copies.
- `repository-scan-ms`: the median of 11 interleaved in-process `scan_tree`
  rounds over this tree, all four prototypes in one process, at a load average
  of 20.56. An earlier run of the starting classifier alone measured 175.8 ms,
  median of 7.
- `served-boundary-bytes`: the rendered boundary for one `out/` holding three
  bundles, the four representatives and the four near misses.
- `committed-hard-boundary-drift` and `committed-candidate-drift`:
  `diff_boundary_documents` and `diff_documents` between each committed root,
  fixture and scoped-entry document and the candidate's regeneration. The two
  candidate drifts are the Alexandria manifest and the Tabularium ledger named
  in section 1.
- `silent-upgrade-changes`: in 18 scenario repositories, a boundary written by
  the starting classifier is checked by the candidate. It counts coverage
  changes (0, 12, 8 and 12 by candidate) that no `drift:` line names by path or
  by covering directory.

Selection: the gates remove `guard-tests-only` (two gates),
`family-names-first` (Git parity) and `git-attribute-readable` (served cases).
`attribute-then-family` is the unique frontier; its space and candidate-drift
costs are recorded and do not decide.
`python3 <plugin_root>/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition design-lock`
exits 0 and consumes 32 reports.

The three pending cells block `integration` and run from the run worktree
root. Each resolver creates its report exclusively and refuses an existing
path, so a rerun cannot overwrite a consumed report.

- `python3 .hexaemeron/design-reports/resolve.py conformance attribute-then-family family-guards-failing-on-base --out .hexaemeron/design-reports/attribute-then-family--family-guards-failing-on-base.json`
  copies `plugins/horos/tests/test_readable_families.py` beside the starting
  classifier and counts failing tests; it needs at least 4.
- `python3 .hexaemeron/design-reports/resolve.py conformance attribute-then-family committed-boundaries-covering-family-files --out .hexaemeron/design-reports/attribute-then-family--committed-boundaries-covering-family-files.json`
  needs 0.
- `python3 .hexaemeron/design-reports/resolve.py conformance attribute-then-family security-review-exception-intact --out .hexaemeron/design-reports/attribute-then-family--security-review-exception-intact.json`
  needs true.

### What attribute-then-family builds

Precedence for one tracked file, in order:

1. Resolve `linguist-generated` and `linguist-vendored` over the tracked
   `.gitattributes` scopes. Within one file the last matching line decides; the
   innermost file that decides an attribute wins; `attr` and `attr=true` set
   it; `-attr` and `attr=false` unset it; `!attr` and any other value leave it
   unspecified; a line whose pattern starts with `[attr]` defines a macro and
   is skipped. Pattern matching stays as it is today.
2. If either attribute resolves set, the file is a hard entry whose evidence
   names the deciding line in today's format. If both resolve set, the entry
   reports the attribute decided in the innermost file, and within that file
   the one whose deciding line comes first.
3. Otherwise, if either resolves unset, the file is readable: no entry and no
   candidate.
4. Otherwise, if its basename is exactly `manifest.json`, `statement.json`,
   `SHA256SUMS` or `events.jsonl`, the file is readable. `classify_file` makes
   this check first, after its symlink refusal, so a direct caller gets the
   same answer.
5. Otherwise `classify_file` runs unchanged.

Directories:

- A corroborated generated or vendored directory stays one entry unless a
  tracked file beneath it is readable under steps 1 to 4, reading every nested
  `.gitattributes` beneath it under the same cap. Otherwise every other tracked
  file beneath becomes a hard entry: an attribute-set file keeps its attribute
  evidence, and the rest carry the directory evidence followed by
  `; split around readable <first readable path>`, plus ` and <n> more` when
  there are more.
- A directory that a set pattern matches stays one entry only when every
  tracked file beneath it resolves set; otherwise the walk enters it and
  decides file by file.
- Candidate directory entries do not change, and the census counts every file
  once, as today.

The macro-definition rule was not in the measured corpus; the step that builds
the classifier pins it with a test.

Files, by home. The runbook fixes the exact cases and counts.

- `plugins/horos/skills/horos/scripts/horos.py`: the resolution helpers, the
  family constant with a comment naming its reason and producers, the
  precedence in the walk and in `classify_file`, and the split.
- `plugins/horos/tests/test_readable_families.py`: the per-family guards,
  maintainer authority, the attribute cases and a scoped check over a split
  directory. It imports only the standard library and `horos` and refers to no
  name the starting classifier lacks, so each case fails by assertion against
  it.
- `plugins/horos/tests/test_committed_family_retention.py`: every
  `.horos/boundary.json` that `git ls-files` lists, plus the five frozen
  copies.
- `plugins/horos/examples/fixture/`: one family file inside a new corroborated
  generated directory, and one attribute-readable checksum file under a set
  pattern beside a set archive part, with existing entries and candidates
  byte-identical and the fixture's three artefacts regenerated.
  `plugins/horos/examples/README.md` documents both and the mutation;
  `plugins/horos/tests/test_discipline.py` changes only if its rule-class
  assertions need the new evidence.
- `plugins/horos/skills/horos/SKILL.md` (one sentence in rule 4, and the
  version), `plugins/horos/skills/horos/EVOLUTION.md` (the generation row),
  `plugins/horos/README.md` (the limits paragraph), and the re-pin set named in
  section 12.
- `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json` at
  every step.
- `plugins/horos/docs/readable-families/study.md` and `runbook.md`: the
  receipted copies.

Suggested step order: scaffold the copies; the classifier and family guards;
the committed-boundary guard and shipped example; documentation, generation
row and re-pin; the demonstration.

## 5. Risk register seed

The audit loop should look hardest at the split, because a sibling that turns
readable is the failure the issue comment names, and at maintainer authority,
because that is where the other reading of the issue would diverge.

```risk-register
maintainer-authority | a .gitattributes line that resolves set for a family-named path | the file stays a hard entry with the deciding line as evidence, and no family name overrides a set attribute
git-resolution-parity | last matching line in a file, innermost file first, -attr, attr=false, !attr and [attr] macro lines | every path in the attribute cases has hard coverage equal to the git check-attr set state, and the public set-only helpers return what they returned before
directory-split | a corroborated or pattern-matched directory holding a readable file | every other tracked file beneath stays a hard entry, the split evidence names the first readable path and the count, and no sibling or neighbouring archive part becomes readable
near-miss-names | suffix, case and archive-part variants of the four names | only exact case-sensitive basenames are readable; manifest.jsonl, statements.json, SHA256SUMS.txt, events.json and the case variants get no protection
committed-boundary-compatibility | the root, fixture and scoped-entry boundaries regenerated by the changed classifier | no pre-existing hard entry or boundary field changes, only the two family candidates leave candidates.json, and the five frozen copies stay byte-identical
nested-attribute-reads | .gitattributes files beneath a directory that would otherwise aggregate | each read stays capped at ATTRIBUTES_CAP, symlinked files are refused, and an unreadable file fails open
readable-cost | a large or binary file under a family name, or an unset line on a sink | accepted as reading cost only; the census still records the file's size and security review ignores the boundary
scoped-check | check on a descendant of a split directory | the scoped slice compares per-file entries and names drift in both directions
boundary-regeneration | .horos/boundary.json, candidates.json and census.json after any tracked change | regenerated together from a clean tree, and tests/test_boundary_currency.py and HorosCensusCurrencyTests pass on a detached snapshot
pinned-files | plugins/horos/tests/test_boundary.py and the SKILL.md digest chain | test_boundary.py is untouched, and the SKILL.md edit re-pins the agent-instruction chain and raises no PM104
generation-row | EVOLUTION.md, the SKILL.md version and the runbook version-relations block | exactly one generation row keeps the markdown-outline-extractor revision and frontier digest byte for byte, done resolve-versions passes, and the runbook names no concrete Horos label
security-review-exception | the SKILL.md rule text and ADOPTION_STANZA | both stay byte-identical and the conformance report records true
guard-capacity | test_readable_families.py run beside the starting classifier | at least 4 tests fail by assertion rather than by an import error
private-target-confidentiality | committed files, pull request bodies, audit records and evidence | nothing identifies the private archive target delivered under #1356 beyond what #1356 and #1483 state publicly
```

## 6. Glossary seeds

- Readable: no hard entry in the committed boundary covers the path. It says
  nothing about content.
- Evidence family: one of the four exact basenames `manifest.json`,
  `statement.json`, `SHA256SUMS` and `events.jsonl`.
- Resolved state: `set`, `unset` or `unspecified` for one linguist attribute
  on one path, decided as Git decides it.
- Deciding line: the last matching line, in the innermost attribute file that
  mentions the attribute, which fixes its state.
- Explicit readable attribute: `-linguist-generated`, `-linguist-vendored` or
  either `=false` form resolving for a path while neither attribute resolves
  set.
- Heuristic: any Horos rule other than a maintainer's attribute, that is
  directory names and their corroboration, lockfile names, markers, signatures,
  sourcemaps, migrations SQL and geometry.
- Split: per-file hard entries written in place of one directory entry because
  a readable file sits beneath it.
- Neighbouring archive part: a hand-split segment such as `ledger.tar.part-aa`
  beside a family file.
- Near miss: a name one edit away from a family name. It gets no protection.
- Served directory: a generated directory such as `out/` holding single-line
  bundles and release evidence.
- Frozen copy: a committed boundary under `plugins/horos/docs/evidence/`
  captured from another tree and checked by entry path only.
- Conformance report: a design report owed at `integration`, written by
  `resolve.py conformance`.

## 7. Sources

- [skills#1383](https://github.com/wildcat-finance/skills/issues/1383): body
  last edited 2026-09-08T12:14:14Z, and its comment of 2026-09-13T02:43:58Z.
- [skills#1356](https://github.com/wildcat-finance/skills/issues/1356) with
  its comments of 2026-09-13 and 2026-09-16, and
  [skills#1483](https://github.com/wildcat-finance/skills/issues/1483) with
  its comments of 2026-09-14 and 2026-09-16.
- Pull requests [skills#1469](https://github.com/wildcat-finance/skills/pull/1469),
  [skills#1470](https://github.com/wildcat-finance/skills/pull/1470),
  [skills#1231](https://github.com/wildcat-finance/skills/pull/1231) and
  [skills#1257](https://github.com/wildcat-finance/skills/pull/1257); issues
  #1130, #896, #842, #1228, #1253, #1192, #1357, #1374 and #1389.
- At the starting commit: `plugins/horos/skills/horos/scripts/horos.py`
  (attribute parsing at lines 202 to 269, classification at 298 to 453, the
  walk at 620 to 788); `plugins/horos/skills/horos/SKILL.md`;
  `plugins/horos/skills/horos/EVOLUTION.md`;
  `plugins/horos/docs/refinement/maintainer-spec.md`;
  `plugins/horos/docs/content-addressed-objects/study.md`;
  `plugins/horos/tests/test_classify.py`, `test_discipline.py`,
  `test_boundary.py`, `benchmark_scope.py` and `run_tests.py`;
  `tests/test_boundary_currency.py`; `tests/test_demonstrations.py`
  (`HorosCensusCurrencyTests`); `tests/test_version_propagation.py`;
  `tests/fixtures/agent-instruction-v1/manifest.json`;
  `tests/fixtures/promise-machine/runtime/horos-boundary-scan.json`;
  `tests/promise_machine_coverage.json`;
  `plugins/hexaemeron/skills/VERSIONING.md`.
- Producers: `plugins/alexandria/scripts/alexandria_lib/derivation.py`,
  `plugins/lazarus/scripts/lazarus_lib/release.py`,
  `plugins/tabularium/skills/tabularium/SKILL.md` and
  `plugins/ariadne/skills/ariadne/SKILL.md`.
- Audit: `audit/AUDIT.md` lines 934 to 1615 and 4824 to 5029, and the four
  synopses named in section 2.5.
- The GitHub Git trees API for `wildcat-finance/v2-protocol` at
  `c7be4039f8f383a9dda4e45f63331c17d63f9ed9` and `wildcat-finance/wildcat-app-v2`
  at `9b8b6d5d6db06428c5b539f267623277b65315cd`, read 2026-09-17.
- Git's `gitattributes(5)` and `git-check-attr(1)` documentation; GitHub
  Linguist's attribute documentation; GNU coreutils `sha256sum`; the in-toto
  Statement v1 specification.
- Run evidence: `.hexaemeron/design-evidence.json`,
  `.hexaemeron/design-reports/resolve.py` and the 32 reports beside it.

## 8. Signals, and the questions behind them

None for on-call, and here is why: Horos is a command an agent or a person
runs from a terminal or a test, and nothing this run ships runs unattended.
The questions a reader does ask are answered by outputs that exist or by the
evidence strings this design writes:

- Why is this family file readable? No entry covers it; the file's name or its
  resolved attribute is the reason, and
  `git check-attr linguist-generated linguist-vendored -- <path>` shows the
  attribute half.
- Why did a directory entry become per-file entries? Each split entry's
  evidence names the first readable file and how many more there are.
- Did upgrading Horos change a committed boundary? `check` names every coverage
  change as drift; 0 silent changes were measured across 18 scenarios.
- Did a step leave an artefact stale? `tests/test_boundary_currency.py` and
  `HorosCensusCurrencyTests` say so.

No counter is added to the boundary document, because a new `counts` key would
drift every adopting boundary that tracks a family-named file, such as
wildcat-app-v2's `public/manifest.json`.
[ephoros](https://github.com/wildcat-finance/skills/blob/9599fa46e8e2c5436a0dae4327c8e5b72f5159a9/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry.

## 9. Boundaries, per capability

- Attribute lines from an untrusted repository. Worth taking there: marking
  sinks readable to raise an agent's reading cost. A readable verdict can only
  reveal a file, never hide one, and security review ignores the boundary.
  Controls: attribute files are read under the existing 64 KiB cap, a symlinked
  attribute file is refused, undecodable bytes fail open, and nothing is
  executed.
- Family names in an untrusted tree. Worth taking there: a 64 MiB or binary
  file named `statement.json` stays readable. Accepted as reading cost; the
  census still records its size.
- Nested attribute files beneath an aggregating directory are now read.
  Controls: the same cap and symlink refusal, and only tracked files count.
- The split. Worth taking there: boundary growth, linear in the tracked files
  beneath a split directory; the served case measured 431 against 2,149 bytes.
  Control: a split happens only when a readable file sits beneath.
- The `git ls-files` subprocess in `resolve_universe` is unchanged. The product
  adds no subprocess, network access, secret or dependency. The new tests run
  `git` in temporary repositories with every `GIT_*` variable removed, as
  `tests/test_boundary_currency.py` does, so an index a hook exported cannot
  reach the outer repository.
- Publication. The private archive target delivered under #1356 stays out of
  every committed file and host body.

[phylax](https://github.com/wildcat-finance/skills/blob/9599fa46e8e2c5436a0dae4327c8e5b72f5159a9/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and the controls.

## 10. The budget, or its absence

- A whole-tree check stays at or under 1,000 ms, measured by
  `python3 plugins/horos/tests/benchmark_scope.py --root . --scope plugins/horos --runs 5`,
  field `full_tree_median_ms`. At study time the in-process scan measured
  444 ms for the starting classifier and 466 ms for the selected prototype,
  medians of 11 interleaved rounds at a load average of 20.56
  (`python3 .hexaemeron/design-reports/resolve.py measure-all-time`); an
  earlier run of the starting classifier alone measured 175.8 ms. The
  prototype enumerates an aggregating directory twice; an implementation that
  enumerates once costs no more.
- The Horos suite stays under 10 s: 5.8 s for 262 tests at entry. A 64 MiB
  representative writes in about 22 ms; the starting classifier reads at most
  8 KiB of it and the selected rule reads none.
- No step claims a speed-up.

[metron](https://github.com/wildcat-finance/skills/blob/9599fa46e8e2c5436a0dae4327c8e5b72f5159a9/plugins/hexaemeron/skills/metron/SKILL.md)
owns what a budget carries and how it is checked.

## 11. The fail-closed posture

What stops the run:

- a red Horos suite, or a red root suite on a detached snapshot of the
  committed head;
- `horos.py check .` exiting non-zero at a step exit, or
  `tests/test_boundary_currency.py` or `HorosCensusCurrencyTests` naming drift;
- `python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json`
  refusing, or `python3 scripts/promise_machine.py check` reporting `PM104`;
- Imprimatur, Phylax, Ephoros or Hypomnema exiting non-zero on changed paths;
- the design checker reporting `D008` at `integration`, which a failing
  conformance report causes; the record cannot be amended, so that halts the
  run;
- a committed file or host body that identifies the private archive target.

Guard convention: a fix ships with a test that fails without it, named for the
failure, in the module that owns the behaviour. The family guards are written
to fail by assertion against the starting classifier, which the
`family-guards-failing-on-base` report checks. The Elenchus runner is the
existing `python3 plugins/horos/tests/run_tests.py {report}`, report format
`unittest-json-v1`.
[elenchus](https://github.com/wildcat-finance/skills/blob/9599fa46e8e2c5436a0dae4327c8e5b72f5159a9/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

## 12. Decisions and their homes

- The precedence: a maintainer's attributes decide first in both directions,
  four exact family names then outrank Horos's heuristics, and a hard directory
  splits around a readable file. Reversing it is expensive: adopting
  repositories will write `-linguist-*` lines and rely on family readability,
  and every committed boundary regenerates under it. Home: the generation row
  in `plugins/horos/skills/horos/EVOLUTION.md`, whose evidence points at the
  committed study and runbook, with the reason in a comment above the
  precedence code in `horos.py` and one sentence in rule 4 of
  `plugins/horos/skills/horos/SKILL.md`. It gets no record under
  `docs/decisions/`, because the decision belongs to one governed skill.
- The four names and why each was chosen. Home: the same row and the comment
  above the family constant.
- The three refused candidates and their measured values. Home: section 4 of
  the committed study copy `plugins/horos/docs/readable-families/study.md`,
  which the row's evidence links.
- Keeping plugin package version `0.1.1` is not a new decision:
  `tests/test_version_propagation.py` records that a plugin's version is not
  its skills' version, and the last three Horos rows held it.

The generation row has axis `generation`, version `horos-v12.4.3` against the
starting ledger, resolved against the integration base through the runbook's
block row `horos | plugins/horos/skills/horos/EVOLUTION.md | next-generation-after-integration-base`.
It keeps frontier revision `markdown-outline-extractor` and frontier SHA-256
`7d19b7476565d3eb54bc2adb0118f1fde2d86f751819c6c5e43ba77ced7b1556` byte for
byte, status `mature` and next job `None -- mature`. The same commit moves the
`version:` in `plugins/horos/skills/horos/SKILL.md` and re-pins
`tests/fixtures/agent-instruction-v1/manifest.json`, the
`horos-boundary-check` fixture's `compact.wai`, `model.json` and
`source-spans.json`, `tests/fixtures/agent-instruction-v1/evidence/measurement.json`
and `parity.json`, and `tests/promise_machine_coverage.json`, with the offset
delta the rule 4 sentence introduces before the reviewed span.

[hypomnema](https://github.com/wildcat-finance/skills/blob/9599fa46e8e2c5436a0dae4327c8e5b72f5159a9/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record and where each lives.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | attribute-then-family
record | plugins/horos/skills/horos/EVOLUTION.md
```
