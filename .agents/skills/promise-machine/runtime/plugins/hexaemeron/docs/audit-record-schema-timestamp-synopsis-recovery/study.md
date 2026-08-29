# Study: recover issue 429 from pull request 552

Assumptions:

- The immutable product to recover is pull request #552 at
  `f11fe174161f46bf79080422169ad943214e1b4f`. GitHub reports its comparison
  base as `4b78dfa8b35efe4da794a200096682eb7495c3b3`; its merge base with the
  pinned recovery base is
  `ced4e6f439021b7509833ed5da66348c86d22f01`.
- The starting recovery base is `main` at
  `c4650f02a979e859ce36374779eac9cd70744288`, which publishes Hexaemeron
  1.6.0 and `fiat-v5.24.1`. A later base is composition work, not permission
  to rewrite the product.
- The old #429 controller ledger is gone. The signed Git history and the
  bytes reachable from #552 survive; old receipts do not. This run must earn
  new study, runbook, implementation, audit, prose, push and integration
  receipts.
- Live GitHub state and the target repository override recollections and old
  prose when they disagree.
- No dependency, storage format outside the audit records, public ABI, CI
  surface, trust boundary or pinned digest may change without an explicit
  runbook gate.

## 1. Problem statement

Issue [#429](https://github.com/wildcat-finance/skills/issues/429) asks Fiat to
give each audit round a strict schema and UTC timestamp, and to generate a
short synopsis beside every audit log without changing historical audit
entries. Pull request
[#552](https://github.com/wildcat-finance/skills/pull/552) contains a completed
three-step implementation, 29 audit records and a disposable controller proof,
but the run that produced it lost its ledger before final integration. The
pull request remains open while `main` has advanced by 225 commits from the
product's merge base.

This is for three readers:

- a Fiat operator who needs a recoverable, receipted route to integration;
- a maintainer who needs the current controller and audit topology preserved;
- an auditor who must be able to distinguish inherited signed product,
  recovery composition, and final integration evidence.

The prototype is the #552 head, not a prose reconstruction. Its 52 commits
outside the current base are all present on GitHub, locally signature-valid,
GitHub-verified with reason `valid`, and each carries exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one
`Wildcat-Origin: shoggoth` trailer. Recovery succeeds only if those commit
objects remain ancestors of the delivered head.

The working demonstration must prove all of the following from a clean clone:

1. A signed composition commit has #552 head as first parent and the exact
   starting base as second parent. If the base later moves, the existing Fiat
   sync contract performs a second signed product-first, base-second merge; no
   rebase or squash substitutes for either join.
2. All 52 inherited commits still verify locally and through GitHub, retain
   both provenance trailers exactly once, and are reachable from the recovery
   head.
3. The current-base versions of unrelated Fiat features remain present,
   including per-run audit paths, final integration checks and controller
   currency receipts.
4. The 574-line, 29-record #552 audit suffix is preserved byte for byte in a
   dedicated per-run audit source. Its SHA-256 remains
   `51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d`.
5. New Warden records use a strict schema and an actual UTC timestamp. The
   historical #552 `fiat-audit-round/v1` grammar remains readable; the current
   per-run grammar is named `fiat-audit-round/v2` rather than silently
   redefining v1.
6. Every supported audit source has one collision-free sibling synopsis,
   generated deterministically from the source, preserving unresolved leads,
   with a physical line count strictly less than 15 percent of the source's
   physical line count. Check the inherited v1 inequality without rounding:
   `100 * synopsis_lines < 15 * source_lines`.
7. The six legacy `AUDIT.md` locations keep the established
   `AUDIT_SYNOPSIS.md` name. A round log `audit/rounds/<run>.md` maps to
   `audit/rounds/<run>.synopsis.md`; synopsis files are never rediscovered as
   sources.
8. Refusal cases leave the repository and controller state unchanged: malformed
   records, non-UTC timestamps, duplicate or missing fields, stale synopses,
   output collisions, paths outside the repository, signature loss, wrong
   merge parents and stale release predecessors all fail closed.
9. The current full Hexaemeron and root suites, Promise Machine check, prose
   lints, version-propagation checks and `git diff --check` finish clean.
10. The final controller proof uses the checked-in controller in a disposable
    repository, creates and validates a real v2 round, proves v1 compatibility,
    proves two round files in one directory cannot collide, regenerates every
    synopsis exactly, and reports the exact released Fiat and package
    generations.

## 2. Prior art

### Repository and organisation history

The #552 product already chose strict Markdown over JSON sidecars: one Warden
write remains readable in the audit log, while an exact parser checks the
machine contract. It chose deterministic extractive synopses rather than model
summaries, kept unresolved leads verbatim, used per-file atomic replacement,
and guarded the pre-product byte prefix. Its three steps were:

1. publish the schema, timestamp writer and controller generation;
2. generate six sibling synopses and their tests;
3. run the checked-in controller in a disposable repository and publish the
   proof.

The product's old release names cannot be replayed. It intended
`fiat-v5.13.1` and Hexaemeron 1.5.6, but `main` already contains a different
`fiat-v5.13.1` and now publishes `fiat-v5.24.1` / 1.6.0. Recovery must allocate
the next live generations late and assert their immediate predecessors rather
than copy the old literals.

The last two merged pull requests that changed the directly relevant Fiat
delivery substrate are:

- [#602](https://github.com/wildcat-finance/skills/pull/602), which released
  `fiat-v5.23.1`, put new audit rounds under `audit/rounds/<run>.md`, and
  repaired a broken integration stack with exact branch and merge checks. It
  expressly says an already broken run cannot manufacture the receipts it
  lost.
- [#607](https://github.com/wildcat-finance/skills/pull/607), the pinned
  `c4650f0` release, which added controller-currency observation and published
  `fiat-v5.24.1` / Hexaemeron 1.6.0. Its seven audit records fixed four findings
  before clean terminal rounds.

Earlier recovery precedent also matters:

- [#562](https://github.com/wildcat-finance/skills/pull/562) preserved product
  evidence while superseding a failed integration sync.
- Issue [#546](https://github.com/wildcat-finance/skills/issues/546), ADR-021
  and the current `integration-revalidation` contract separate a product's
  evidence from later base-sync evidence.
- [#585](https://github.com/wildcat-finance/skills/pull/585) made runbook
  amendments the honest route when a live base changes an accepted plan.
- Issue [#557](https://github.com/wildcat-finance/skills/issues/557) remains
  open for controller-ledger durability. This recovery must not pretend to
  solve it.

### Audit topology measured at the pinned base

Current `main` has six legacy sources:

- `audit/AUDIT.md`;
- `plugins/ariadne/audit/AUDIT.md`;
- `plugins/hexaemeron/audit/AUDIT.md`;
- `plugins/pandects/audit/AUDIT.md`;
- `plugins/probitas/audit/AUDIT.md`;
- `plugins/tabularium/audit/AUDIT.md`.

It also has two committed per-run sources, for #576 and #594, in
`audit/rounds/`. The #552 generator maps every source directory to the constant
name `AUDIT_SYNOPSIS.md`; applying that rule to both round sources would make
them overwrite the same path. This is a release-blocking design constraint,
not a naming detail.

The root `audit/AUDIT.md` on `c4650f0` is not the old merge-base prefix: it
first differs at byte 494 and its intervening history contains 5,237 additions
and 550 deletions. The other five legacy logs retain their old prefixes.
Therefore the old six-prefix fixture is historical #552 evidence, not a valid
claim about the current root log. The recovery keeps the `c4650f0` root bytes
and relocates only the exact product suffix into a new per-run source.

### Audit record inventory and carried leads

Every one of the 29 product records was inspected:

- step 1 has rounds 1 through 12; rounds 1 through 11 found defects that the
  following signed commits addressed, and round 12 is clean;
- step 2 has rounds 1 through 15; rounds 1 through 14 found defects that the
  following signed commits addressed, and round 15 is clean;
- step 3 has two rounds; round 1's three low findings are fixed and round 2 is
  clean.

Those closed findings remain closed only if their tests and exact product bytes
survive composition. The product's open leads are carried by these stable
names:

- `report-commit-binding`: issue #453 still owns binding reported check bytes
  to the commit actually pushed;
- `protasis-consumption`: issue #369 still owns proving that later roles read
  the accepted plan rather than merely recording it;
- `delegated-identity`: issue #363 still owns delegated role identity;
- `post-final-check-race`: a file can change after a final local check;
- `multi-synopsis-atomicity`: writes are atomic per sibling, not across all
  synopsis files;
- `windows-path-hardening`: the original proof did not establish equivalent
  `dirfd` / no-follow controls on Windows;
- `disposable-proof-retention`: the historical temporary proof repository no
  longer exists, although its committed report and signed history do;
- `non-solidity-scope`: neither the old product nor this recovery changes
  Solidity, so the security suite is explicitly waived in favour of Warden's
  non-Solidity audit and repository checks.

All four #602 recovery audit records were inspected and are clean. Its
`retarget-drift` lead remains: GitHub base retargeting can move after a local
check, so final integration must re-read the live pull request and exact base.

The seven #607 records were also inspected: step 1 round 1 is clean; step 2
round 1 fixed mutable currency receipts and a missing-clone misclassification,
then round 2 is clean; step 3 rounds 1 and 2 fixed text-output injection and
Unicode handling, then round 3 is clean; step 4 round 1 is clean. These open
leads remain inherited and outside #429:

- `currency-registry-malformed`, `currency-commit-width`,
  `currency-install-path-authority`, `currency-probe-stdin` and
  `currency-clone-head` cover deliberately bounded probe cases;
- `currency-empty-fleet`, `currency-text-layout`,
  `currency-manual-only-fixtures`, `currency-unknown-exit` and
  `currency-homoglyph` cover display and incomplete fixture guards;
- `currency-package-semver`, `currency-repin-partiality`,
  `currency-refused-lock`, `currency-managed-route`,
  `currency-dynamic-version` and `currency-stale-installed-pin` cover release
  and operating limits.

Issue [#608](https://github.com/wildcat-finance/skills/issues/608) reports that
`integrate` reads `base_commit` while sync records `base_head`. This run's
state has `frontier: null`, so the known defect is not currently on its
frontier-row path. The ordinary terminal integration proof must still exercise
the actual checked-in controller. If #608 becomes causally involved, the run
stops for a scoped amendment; it does not fix that issue under #429.

### Outside prior art

Git's commit graph is the preservation mechanism: a merge commit records its
parents in order, `git verify-commit` checks the signed commit object, and a
non-fast-forward merge can join histories without replacing either side's
commits. GitHub's commit verification record supplies the separate hosted
identity observation. Neither observation substitutes for the other.

## 3. Constraints and non-goals

### Fixed constraints

- Work starts from `c4650f02a979e859ce36374779eac9cd70744288` and imports exactly
  `f11fe174161f46bf79080422169ad943214e1b4f`.
- The product range contains 52 locally and remotely verified commits. The
  recovery may add signed commits but may not amend, cherry-pick, squash or
  rebase those 52 objects.
- The composition has 31 product-touched paths, 205 upstream-touched paths,
  16 overlaps and 15 predicted textual conflicts. Each conflict needs an
  explicit resolution check; bulk `ours` or `theirs` is not evidence.
- The current controller is the checked-in `fiat-v5.24.1` implementation.
  Running an older controller from #552 would recreate stale assumptions.
- Existing `c4650f0` audit entries are immutable during recovery. The 574-line
  product suffix is copied exactly to a dedicated source rather than inserted
  into or used to replace current history.
- The current run's own Warden path remains the path recorded in state:
  `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md`.
- The target repository's `AGENTS.md`, Promise Machine contract and
  `.horos/boundary.json` govern every read and write. No classified Horos sink
  is needed for this packet.
- Use the repository's existing Python and Node toolchains and standard test
  entry points. Add no dependency.
- Every commit and merge created by the recovery must be signed and must carry
  the repository's exact provenance trailers.

### Non-goals

- Do not reconstruct, edit or claim the lost #429 ledger or its old receipts.
- Do not merge or close #552 until the replacement recovery is visibly landed;
  then close it only with a pointer to the landing commit that still contains
  its product commits.
- Do not solve #557, #608, #453, #369 or #363 in this packet.
- Do not rewrite old audit prose to fit v2, and do not relabel v1 bytes as v2.
- Do not promise one transaction across every synopsis file. Each destination
  is atomic; a final all-files check proves the set is coherent.
- Do not broaden the synopsis into a semantic security verdict. It is a short,
  deterministic reading aid that preserves the source's verdict and open
  leads.
- Do not change Solidity, public APIs, CI, marketplace trust, plugin install
  authority or credential handling.
- Do not claim that green bounded tests are a security review.

## 4. Design options

### Option A: replay the product as new commits on current main

Cherry-pick or reimplement the 31 changed paths, then resolve conflicts in a
linear branch. This produces an easy-to-read final diff, but it assigns new
object IDs to the old work and breaks the central requirement that the 52
signed product commits survive as the delivered ancestry. It would also turn
the missing receipts into an excuse to replace evidence that still exists.

**Trade:** cheapest Git shape, unacceptable provenance loss. Rejected.

### Option B: merge #552 unchanged and choose one side for conflicts

Create a product-first merge and use broad current-side resolutions for the
controller, versions and root audit log, or broad product-side resolutions for
the original #429 files. This preserves commit objects but either drops product
behaviour or rolls back 225 commits of controller evolution. The old constant
synopsis name also collides as soon as two `audit/rounds/*.md` files share a
directory. A clean merge is not a correct merge.

**Trade:** preserves history with little composition code, but hides semantic
loss in conflict choices. Rejected.

### Option C: product-first merge plus a named compatibility composition

Create one signed merge whose first parent is #552 head and whose second parent
is `c4650f0`. Resolve each overlapping path against a checked manifest. Keep
the current controller and current root audit bytes, then port the #429
behaviour deliberately:

- copy the exact 574 product audit lines into
  `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md` and pin its
  digest and 29 headings;
- retain `fiat-audit-round/v1` parsing for those topic-bearing records;
- introduce `fiat-audit-round/v2` for current per-run records, where the run
  path supplies identity and the heading remains `## Step <n>, round <r> --
  <UTC timestamp>`;
- validate every explicitly schema-tagged v1 or v2 record strictly while
  leaving older untagged historical prose readable;
- map legacy `AUDIT.md` to `AUDIT_SYNOPSIS.md`, and map every other source
  `<stem>.md` to `<stem>.synopsis.md` in the same directory;
- exclude `*.synopsis.md` from discovery, reject two sources mapping to one
  destination, and regenerate the complete synopsis set;
- retain the current controller's per-run audit path, currency receipt,
  integration-revalidation and final-visible-state behaviour;
- allocate the next Fiat and package generations only after checking the live
  immediate predecessors.

If `main` moves before final integration, compose the completed recovery head
with the exact new base using the current product-first sync contract and bind
the resulting integration-revalidation document to both parents and its
digest.

**Trade:** one deliberately complex merge and a dual-version parser in
exchange for intact signed ancestry, current controller behaviour and an
honest historical grammar boundary. Chosen. It is the cheapest design a reader
can verify correctly: old product, current base and the one compatibility join
remain distinct in the graph and in the files.

### Option D: publish the old product unchanged as an archival branch

Keep #552 open or tag its head, then implement #429 afresh elsewhere. This
preserves an archive but does not recover the product into the release and
duplicates review. Rejected.

## 5. Risk register seed

```risk-register
signed-lineage | inherited product commits | Verify all 52 commit signatures, exact trailers, hosted verification and reachability from the delivered head
receipt-provenance | lost controller ledger | Assert that every new phase has a new receipt and that no document describes the old receipts as recovered
merge-parent-order | composition DAG | Check the composition commit has f11fe174 as first parent and c4650f0 as second parent
base-drift | live main and pull request state | Re-read the live base and PR immediately before integration and use a receipted product-first sync if it moved
conflict-resolution | sixteen overlapping paths | Compare a checked path manifest and prove all fifteen textual conflicts retain both required behaviours
controller-regression | current Fiat behaviour | Run currency, per-run audit, integration-revalidation and final-visible-state guards on the composed tree
version-collision | release ledgers and plugin surfaces | Resolve the next live generations late and refuse a non-immediate predecessor or inconsistent surface
audit-prefix-divergence | root audit history | Keep c4650f0 root bytes unchanged and test the imported 574-line product suffix separately
audit-record-relocation | imported product evidence | Pin the imported line count, 29 headings, step-round distribution and SHA-256 digest
synopsis-name-collision | multiple round logs in one directory | Derive round outputs from source stems and reject duplicate destinations before writing
schema-topology | historical v1 and current v2 records | Validate both grammars by explicit schema name and refuse context-dependent reinterpretation
synopsis-drift | generated reading aids | Recompute every synopsis in check mode and compare exact bytes, source digest, verdict, leads, physical line counts and the strict inherited line-count inequality
partial-write | generated file set | Write each sibling atomically and require a final all-source check before commit or release
path-boundary | repository file writes | Reject symlinks, non-regular sources, path escapes and destinations outside the source directory
attribution-loss | commit authorship and trailers | Check local signature identity separately from GitHub author and verification metadata
scope-creep | neighbouring controller defects | Keep issues 557, 608, 453, 369 and 363 open unless a demonstrated causal blocker earns an amendment
integration-key-defect | non-frontier sync metadata | Exercise ordinary terminal integration and stop if issue 608 is encountered instead of repairing it inside 429
```

## 6. Glossary seeds

- **Product head:** immutable #552 commit
  `f11fe174161f46bf79080422169ad943214e1b4f`.
- **Pinned recovery base:** `main` commit
  `c4650f02a979e859ce36374779eac9cd70744288`.
- **Product range:** the 52 commits reachable from the product head and not
  from the pinned recovery base.
- **Composition commit:** the signed two-parent merge that joins product first
  and recovery base second, with compatibility resolutions in its tree.
- **Sync commit:** a later signed two-parent merge of the completed recovery
  product first and an advanced exact base second.
- **Product evidence:** signatures, trailers, tests, audits and bytes created by
  the original #552 commits.
- **Composition evidence:** new checks showing that old product and new base
  work together. It does not revise product evidence.
- **Final integration evidence:** live PR, exact parent, digest and visible-base
  checks performed at the last merge boundary.
- **Audit source:** a legacy `**/audit/AUDIT.md` file or a non-synopsis Markdown
  file directly under `audit/rounds/`.
- **v1 record:** the #552 topic-bearing `fiat-audit-round/v1` grammar preserved
  byte for byte.
- **v2 record:** the current per-run grammar whose path identifies the run and
  whose heading identifies step, round and UTC time.
- **Synopsis:** a deterministic sibling reading aid, not an audit verdict and
  not a replacement for its source.
- **Current generation:** the exact Fiat ledger and Hexaemeron package versions
  published immediately after the live predecessors at release time.
- **Receipt:** controller evidence for a new transition. A surviving Git commit
  is evidence, but is not a substitute for a lost controller receipt.

## 7. Sources

Primary repository and GitHub evidence, measured on 2026-08-25:

- Issue [#429](https://github.com/wildcat-finance/skills/issues/429), including
  acceptance criteria and the comments recording the lost run state.
- Pull request [#552](https://github.com/wildcat-finance/skills/pull/552), its
  live metadata, checks, commits and head tree at `f11fe174`.
- Product documents `docs/fiat-audit-record-study.md`,
  `docs/fiat-audit-record-runbook.md` and its committed controller-proof
  report at the #552 head.
- The 574 appended lines of `audit/AUDIT.md` at #552 head and all 29 records
  within them.
- Current `main` at `c4650f0`, including `AGENTS.md`, `.horos/boundary.json`,
  the root Promise Machine contract, `plugins/hexaemeron/AGENTS.md`, current
  Fiat skill, audit-loop and push-discipline references, controller, tests,
  EVOLUTION rows and ADRs 021, 025 and 033.
- Pull requests [#602](https://github.com/wildcat-finance/skills/pull/602),
  [#607](https://github.com/wildcat-finance/skills/pull/607),
  [#562](https://github.com/wildcat-finance/skills/pull/562) and
  [#585](https://github.com/wildcat-finance/skills/pull/585), with the directly
  applicable audit records described in item 2.
- Issues [#551](https://github.com/wildcat-finance/skills/issues/551),
  [#557](https://github.com/wildcat-finance/skills/issues/557),
  [#608](https://github.com/wildcat-finance/skills/issues/608),
  [#453](https://github.com/wildcat-finance/skills/issues/453),
  [#369](https://github.com/wildcat-finance/skills/issues/369) and
  [#363](https://github.com/wildcat-finance/skills/issues/363).
- Local graph, merge-tree, path-overlap, prefix, digest, signature and trailer
  measurements against the exact SHAs named above; hosted verification was
  checked independently through GitHub.
- The pinned Surveyor worker prompt and Protasis 4.7.0 contract under
  `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills-hexaemeron-1.6.0-c4650f0/`.
- Official Git documentation for
  [`git-merge`](https://git-scm.com/docs/git-merge),
  [`git-verify-commit`](https://git-scm.com/docs/git-verify-commit) and
  [`git-rev-list`](https://git-scm.com/docs/git-rev-list), plus GitHub's
  [commit verification object](https://docs.github.com/en/rest/commits/commits#get-a-commit).

## 8. Signals, and the questions behind them

The governing discipline is Ephoros at
`plugins/hexaemeron/skills/ephoros/SKILL.md`. This is a bounded CLI and file
generation path, not an unattended service, so it needs no new production
metrics, traces or alerts. It does need durable answers in receipts, audit
records and the final proof:

- **Which product and base were joined?** Record full product, base and
  composition SHAs, parent order and the integration-revalidation digest.
- **Did any signed identity disappear?** Record total, local-valid,
  hosted-valid, exact-trailer and reachable counts; all must be 52.
- **What did composition resolve?** Record the 16 overlap paths, 15 textual
  conflicts and the assertion attached to each resolution.
- **Which audit sources and outputs were checked?** Emit a deterministic row
  per source with source path, destination path, source digest, output digest,
  schema counts, source and synopsis physical line counts, line ratio, verdict
  and lead count.
- **Was anything written before a global refusal?** The generator reports its
  complete plan before writing and reports zero changed paths on every refusal
  fixture.
- **What is finally visible?** Record live PR head/base, task issue, released
  generation, merged commit, base visibility and controller verification.

Human text remains concise; exact rows belong in JSON proof artefacts and
controller receipts. A correlation key is the run slug
`fiat-429-recover-issue-429-from-pull-request-552`, carried with full commit
SHAs rather than replacing them.

## 9. Boundaries, per capability

The governing discipline is Phylax at
`plugins/hexaemeron/skills/phylax/SKILL.md`.

- **Repository reads:** audit Markdown and Git objects are untrusted bytes.
  Bound file size and record count, decode UTF-8 strictly, parse without code
  execution, and reject symlinks, devices, non-regular files and paths outside
  the repository.
- **Repository writes:** derive a destination only after source discovery is
  complete; require a one-to-one source/destination map; write a temporary
  sibling with restrictive permissions, flush it and replace atomically. Check
  mode writes nothing. Preserve the known cross-file atomicity limit.
- **Subprocesses:** invoke Git and tests with argument arrays, fixed working
  directories, bounded output and checked exits. Do not interpolate issue text,
  branch text or Markdown into a shell command.
- **GitHub:** live issue, PR and verification responses are external evidence.
  Pin owner, repository, pull request and full SHA; bound pagination; refuse a
  changed object set. Never print or persist a token.
- **Generated prose:** source audit text can contain markup and hostile links.
  Extract known fields as text, do not fetch links, do not interpret HTML, and
  never let prose select a path or command.
- **Version surfaces:** all five package/plugin surfaces and the Fiat EVOLUTION
  row form one checked set. Refuse partial writes or a predecessor that changed
  after resolution.
- **Authority:** no dependency, CI edit, issue mutation, merge, push or release
  is implied by a passing local proof. Those remain at their named Fiat gates.

## 10. The budget, or its absence

The governing discipline is Metron at
`plugins/hexaemeron/skills/metron/SKILL.md`. #429 makes no speed claim, so
runtime optimisation has no acceptance role. The useful budgets are structural
and reproducible:

- composition starts at 31 product paths, 205 upstream paths, 16 overlaps and
  15 textual conflicts;
- the pinned base has eight audit sources, and the final recovery is expected
  to have ten: six legacy, two existing round logs, one imported product log
  and this run's Warden log. Discovery, not a stale literal, remains the release
  authority;
- every synopsis satisfies
  `100 * synopsis_lines < 15 * source_lines`, using the inherited v1 physical
  line-count routine and no rounded percentage;
- every source byte length, output byte length and record count is bounded
  independently before allocation; these absolute safety caps do not define
  the 15 percent acceptance budget;
- the final proof records elapsed time and peak output size for diagnosis only,
  without promoting either to a release claim.

The repeatable measurement commands are:

```sh
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
```

If implementation work claims a parser or generator speed improvement, that is
a new Metron question: capture a fixed corpus and command, measure the unchanged
product version first, change one thing, and remeasure the same corpus. Without
that baseline the claim is omitted.

## 11. The fail-closed posture

The governing discipline is Elenchus at
`plugins/hexaemeron/skills/elenchus/SKILL.md`. A recovery error is evidence to
preserve, not a reason to choose a convenient side of a merge.

Stop before mutation when any of these occurs:

- the live product head, starting base, commit count, signature result,
  trailer count or hosted verification set differs from the pinned evidence;
- the composition parents are reversed or either parent is not exact;
- a conflict lacks a named retained-current and retained-product assertion;
- the imported suffix is not 574 lines, 29 headings with distribution
  12/15/2, or the pinned SHA-256;
- a schema-tagged record is malformed, duplicated, out of order or not UTC;
- source discovery maps two logs to one output, encounters a synopsis as a
  source, escapes the repository or observes a source change between plan and
  replace;
- a synopsis is stale, loses a verdict or unresolved lead, or fails
  `100 * synopsis_lines < 15 * source_lines`;
- the next release generation is not the immediate live successor on every
  version surface;
- any required suite, lint, proof or final controller verification fails.

Permanent guards must first be demonstrated red on the unfixed composed tree.
They cover the two-round collision, v1/v2 confusion, wrong parent order,
modified product suffix, lost signatures/trailers, stale outputs, strict
physical-line ratio, path escape, symlink input, partial refusal and
predecessor drift. The
final disposable proof runs the checked-in controller rather than a fixture
copy.

When `main` or a live pull request changes, preserve the observed SHAs and
output, amend the accepted runbook with the new boundary, then rerun. Never edit
a failing test away, weaken a digest, or report an unrun command as green.

## 12. Decisions and their homes

The governing discipline is Hypomnema at
`plugins/hexaemeron/skills/hypomnema/SKILL.md`.

The expensive decision is Option C: retain the signed product graph, introduce
a compatibility composition, preserve v1, add v2, relocate the exact product
audit suffix and derive unique round-synopsis names. Record that decision in
`docs/decisions/ADR-034-recover-signed-fiat-product-across-an-audit-topology-change.md`
if ADR-034 remains unused at implementation entry; otherwise allocate the next
unused ADR number and record that mechanical change in the runbook amendment.
The ADR names the rejected linear replay, broad conflict-choice and archival
alternatives.

Other homes are fixed by purpose:

- this accepted study and its runbook are published under `docs/` in the first
  implementation step so later roles read stable copies;
- v1 and v2 grammar, source discovery and output mapping live beside the
  synopsis/parser implementation, with comments explaining why the two
  grammars and two naming rules coexist;
- merge ancestry, suffix digest, schema, collision, atomicity and current
  controller behaviour live in executable tests rather than comments;
- exact product/base/composition SHAs, signature counts, conflict manifest,
  source/output digests and final versions live in the recovery proof artefact;
- operational parent order, live-base reread and sync commands live in the
  runbook and current Fiat references;
- each finding and carried lead lives in the per-run Warden audit log;
- the final pull request explains the three evidence layers and links #552;
  issue comments do not become the sole home of a decision;
- #557, #608, #453, #369 and #363 remain their own durable homes for work this
  recovery does not absorb.

Comments should explain only the non-obvious compatibility reasons. They must
not restate the parser or become a second schema.
