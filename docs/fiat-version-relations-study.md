# Study: resolve runbook target versions at integrate time

Assuming, unless corrected:

1. This is the ordinary-generation Fiat run for
   [skills#556](https://github.com/wildcat-finance/skills/issues/556). Its
   controller state has `frontier: null`, so the run does not pass
   `--frontier`, close or replace a held job, or increment an evolution
   counter.
2. The exact starting commit and integration-base observation is
   `8e6480230a5f43c57aef4f9a6c52f4c602d86790` on `main`. The isolated run
   branch is `fiat/556-resolve-runbook-target-versions-at-integrate`.
3. At that commit Fiat is `fiat-v5.22.1` and Protasis is
   `protasis-v4.7.0`. If no other generation lands first, this work would use
   `fiat-v5.23.1` and `protasis-v4.8.0`. Those two labels are projections from
   the pinned base, not reservations or runbook literals. The relation this
   study defines must recompute them against the integration base.
4. `VERSIONING.md` is authoritative. The three numeric positions are
   evolution, generation, and epoch; they are not Semantic Versioning. The
   relation is therefore named `next-generation-after-integration-base`, not
   “next minor”.
5. Only Fiat and Protasis change. Protasis owns the runbook declaration and
   structural check. Fiat owns the compatibility anchor, version-resolution
   receipt, controller state and ledger events, integration gate, delegated
   evidence, and recovery directions. Elenchus supplies the failure workflow
   and report reader but its contract does not change.
6. A declared relation is optional and closed. A runbook with no relation
   block retains its current literal behaviour, state shape, commands, and
   lack of remote version reads. A runbook may also leave one target out of
   the block when an exact literal is intentional.
7. The sole first relation is “increment the generation counter by one from
   the exact integration-base ledger row while retaining evolution, epoch,
   and the held frontier”. No range, highest-compatible, fallback list,
   reservation, arbitrary expression, or automatic evolution/epoch change is
   included.
8. `done runbook` captures the relation source and a compatibility anchor. It
   does not choose or reserve the final label. The final relation is resolved
   only in the integrate phase, after the last accepted step merge and after
   any active signed base-sync merge.
9. A concurrent generation is compatible only when the target's evolution,
   epoch, frontier status, frontier revision, frontier digest, current-frontier
   text, and next-job text still match the anchor. Its generation may move.
   Any other drift blocks automatic resolution. Green integration
   revalidation remains necessary because this tuple is a versioning boundary,
   not a claim that two implementations compose safely.
10. A version adjustment is a product-tree change. It may occur only in a
    normal audited step or, after the step stack has closed, in Fiat's existing
    signed two-parent `sync-run` composition followed by digest-bound
    integration revalidation. The controller never edits product files from a
    receipt command.
11. The current GitHub merge endpoint can bind the expected pull-request head
    SHA, but it does not offer a corresponding expected-base SHA. A bounded
    read/re-read can establish a coherent snapshot, not a lock. The final gate
    therefore detects and refuses a later base move; it does not claim to make
    that race impossible.
12. Python 3.14.6 is the observed local toolchain. The implementation remains
    compatible with the repository's supported Python 3 boundary and standard
    library. No dependency, CI, branch-protection, repository-ruleset, or state
    version change is assumed.
13. Elenchus has two exact names at separate boundaries. The CLI report format
    is `unittest-json-v1`; the JSON object written by the Hexaemeron test runner
    has schema `elenchus.unittest.v1`. A source-bound runbook must not put the
    schema string in the CLI format position.
14. This study and its later runbook belong only to issue #556 and this
    controller run. The halted #555 state, #429 branches, #557 recovery work,
    and earlier controller ledgers are evidence, not receipts imported into
    this run.
15. This is a self-hosted Fiat change. The active `fiat-v5.22.1` controller and
    `protasis-v4.7.0` checker were installed when the run started; the
    controller-currency contract says a rule shipped by this run governs the
    next run, not itself. Issue #556 may state the relation up front and use the
    existing signed sync/revalidation path if its projection is consumed, but
    it cannot claim that P006 or `fiat-version-resolution/v1` guarded its own
    terminal receipt. The final report names that bootstrap gap.

## 1. Problem statement

Fiat accepts a runbook before implementation and receipts its exact bytes.
When that runbook names a future skill version as a literal, it turns a value
that depends on the eventual integration base into a promise made against the
starting base. A concurrent run may publish that label after the runbook is
accepted but before the product integrates. The later run can neither publish
a duplicate ledger row nor satisfy its accepted literal.

The halted issue #555 run is the concrete red specimen. After its last legal
build-step runbook amendment, all steps completed and their audit evidence was
accepted. While it was working, issue #576 published `fiat-v5.22.1` on
`main`. The #555 runbook expressly forbade silent renumbering. When #555
reached integrate, a second amendment was unavailable because runbook
amendments are limited to active build steps. The controller halted with this
reason:

> `origin/main at 8e6480230a5f43c57aef4f9a6c52f4c602d86790 consumed fiat-v5.22.1 via issue #576 after step audit closure; the accepted #555 runbook requires an issue #554 runbook amendment or halt, and amend runbook is unavailable in integrate phase`

That halt was correct under the accepted runbook. It also shows why #554's
general amendment transition is not the answer here: version allocation has a
normal integrate-time input, and the input can change after the last point at
which an amendment is legal.

Issue #429 is the older specimen. Its step 3 named `fiat-v5.13.1`; the
repository later reached `fiat-v5.18.1` and beyond. Its preserved step-2 tip
and current controller state have other recovery problems, owned by #557, but
the stale literal is the same category of error. Re-running early version
guessing does not remove the race.

The missing capability is narrow: an accepted runbook can state a closed
relation for a governed skill version, Fiat can bind that relation to the
exact integration base and product head, and integration cannot finish unless
the checked product tree carries the one label that relation selects. The
relation changes the time at which the value becomes concrete; it does not
weaken the ledger rule or let the controller rewrite a completed product.

A working prototype has these observable results:

- Against a temporary base whose latest Fiat row is `fiat-v5.22.1`, a
  relation-target product carrying `fiat-v5.23.1` receives a resolution
  receipt and may proceed to the existing integration gates.
- If another valid Fiat generation is inserted before resolution, the same
  accepted runbook selects the next generation from that new exact base. The
  product must carry the recomputed label through an audited step or the
  signed sync/revalidation path before it receives a new receipt.
- If the base moves only by a compatible generation after a receipt, `next`
  marks the receipt stale and directs another bounded sync and resolution. If
  the frontier, evolution, or epoch moves, it halts instead of guessing.
- A literal-only legacy run produces byte-for-byte equivalent state and
  directives on this path and makes no new remote read.
- A base or run ref that changes during evidence collection, an unreadable Git
  object, a malformed ledger, a non-prefix history, a mismatched `SKILL.md`
  version, a partial multi-target result, or an exhausted receipt-history cap
  produces a named refusal without changing product bytes.

The demonstration belongs in focused temporary-repository tests rather than a
live GitHub run. It constructs the #555 topology, inserts a concurrent
generation, proves that the old literal fixture cannot finish, then proves
that the relation fixture resolves only after its product row and skill
metadata match the advanced base. A second fixture advances the frontier and
proves the relation refuses that change.

The capability cannot be split into unrelated deliveries. A Protasis block
without a Fiat receipt is advisory prose; a receipt without a closed Protasis
shape has no stable source; a resolution that is not a terminal integration
gate can become stale without consequence.

There is one explicit bootstrap limit. This run can ship and test the complete
capability, and its accepted runbook can authorise a concrete correction under
the relation rather than a silent renumber. Its installed controller cannot
earn the new receipt it is creating. If either pinned-base projection is
consumed before #556 lands, the only legal current-run choices are a concrete
correction in the existing signed `[product, base]` sync with covering
integration revalidation, or halt. The first later relation-bearing run under
the updated plugin is the first one whose controller can make the new Promise.

## 2. Prior art

The last two merged pull requests that changed the target controller or its
version surfaces were read first.

- [PR #585](https://github.com/wildcat-finance/skills/pull/585) shipped issue
  #554's append-only runbook amendments. It fixed the recovery available while
  build steps remain active and explicitly carried dynamic target-version
  resolution forward as #556. Its audit checked generation collision on its
  recorded base, which was the correct evidence for that run but did not
  remove later drift.
- [PR #593](https://github.com/wildcat-finance/skills/pull/593) gave each Fiat
  run its own audit record. During its integration, `main` consumed the label
  it had first projected. Its audit records say the final Fiat version row was
  knowable only against the real predecessor at sync, so its signed sync
  composition placed `fiat-v5.22.1` manually. That is useful operational
  precedent, but the authority and exact relation were not yet a reusable
  runbook contract.

Three audit histories were read for the design:

- Issue #554's rounds establish the exact-prefix amendment contract, durable
  subject-labelled recovery, and the distinction between Elenchus's CLI report
  format and JSON schema. They leave integrate-time version resolution out of
  scope by name.
- Issue #576's per-run audit log records the collision that moved its proposed
  label, the decision to wait for the real sync predecessor, the signed
  composition, and the global-identifier checks. It demonstrates that a
  concrete correction can travel in `sync-run` when revalidation covers it.
- The halted #555 audit log records two rounds, the final clean audit, and the
  accepted last amendment before `fiat-v5.22.1` was consumed. It is the red
  regression specimen. Its clean product audit does not authorise a later
  unreviewed search-and-replace.

Current repository contracts already supply most of the needed boundary:

- `plugins/hexaemeron/skills/VERSIONING.md` defines evolution, generation, and
  epoch arithmetic and says skill labels are not SemVer.
- `done_runbook` already binds the exact runbook path and SHA-256, while
  `receipted_source` refuses later byte drift.
- `_integrate_directive`, `done_sync_run`, and `done_integrate` already
  distinguish the completed product head, exact remote integration base,
  signed two-parent composition, affected paths, bounded green revalidation,
  and terminal integration receipt.
- `frontier_close_fault`, `ledger_version`, `ledger_rows`,
  `ledger_frontier_digest`, and the evolution suite already share the ledger
  spelling and arithmetic. Relation resolution must reuse that parser rather
  than invent another reading of a version row.
- ADR-024 binds exact observation prefixes to receipts. ADR-025 keeps each
  run's audit record separate. Neither decides when a future version becomes
  concrete, but both favour exact subjects and replayable digests.
- The Fiat frontier-row-attribution study reads exact ledger blobs from a
  recorded base and subtracts rows already published there. That is direct
  precedent for commit-and-path evidence rather than a mutable worktree read.
- The Fiat merged-attribution study records an integration-time manual
  renumber after concurrent runs consumed both a version and an ADR number.
  This issue takes only the version lesson. It does not create a general
  allocator for ADRs or other global identifiers.

[Issue #556](https://github.com/wildcat-finance/skills/issues/556) proposed a
relation such as “next minor above base at integration”. The repository's
versioning vocabulary changes that spelling to the exact generation relation
in this study. The issue moved from a base carrying `fiat-v5.18.1` to one
carrying `fiat-v5.19.1` within minutes of filing, which is itself evidence that
an early literal is observation, not allocation.

[Issue #429](https://github.com/wildcat-finance/skills/issues/429) and
[PR #542](https://github.com/wildcat-finance/skills/pull/542) were also read.
The lower step was merged into the wrong branch and the surviving step 3 is
still pinned to an obsolete literal. Issue #556 does not reland that stack,
repair its controller state, or reconstruct its missing ledger; #557 remains
the named home for that recovery.

Two outside interfaces sharpen the boundary without supplying the repository
rule:

- Cargo separates a dependency requirement from the exact version selected in
  a lockfile. That is a useful relation-versus-resolution analogy only. Wildcat
  skill labels keep their own non-SemVer arithmetic.
- GitHub's pull-request merge API accepts an expected head `sha`, while the
  request has no expected-base-SHA field. Repository rules require pull
  requests and signed commits but do not add a base compare-and-swap. This is
  why the receipt can prove one coherent snapshot and why a final re-read is
  still required.

Carried forward rather than absorbed here: #508's executable runbook-gate
validation, #555's misdirected step-merge repair, #557's lost-ledger recovery,
general transaction rewrites, automatic ADR-number allocation, and the held
Fiat and Protasis frontier jobs.

## 3. Constraints and non-goals

The work starts from exact commit
`8e6480230a5f43c57aef4f9a6c52f4c602d86790`, with Python 3 and the standard
library. The current repository projection is `fiat-v5.23.1` and
`protasis-v4.8.0`. The runbook must state the relation instead of either
projection, and integration must recompute the concrete rows from the exact
base it will join.

The runbook surface is one optional fenced block before `## Step 1`:

````markdown
```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
protasis | plugins/hexaemeron/skills/protasis/EVOLUTION.md | next-generation-after-integration-base
```
````

There may be at most one block and 32 rows. Every physical line inside it is
one row with exactly three pipe-separated fields: a kebab-case skill id, a
safe repository-relative `EVOLUTION.md` path, and the literal relation name
`next-generation-after-integration-base`. Blank rows, duplicate ids, duplicate
paths, comments, extra fields, unknown relations, absolute paths, `.` or `..`
segments, control characters, symlinks, non-regular Git objects, and a path
whose skill directory or current version prefix disagrees with the id are
refused. The source file and each referenced blob retain the existing 2 MiB
read cap.

The block gives each target a symbolic name for the rest of the runbook. A
step touching that target says that its final header, history row, and
`SKILL.md` metadata must equal the declared relation; it does not state a
concrete future label. Protasis P006 rejects a concrete
`<declared-skill>-v<evolution>.<generation>.<epoch>` token anywhere else in
that runbook, including examples, commands, and amendments. Starting values
belong in Fiat's source packet and receipt rather than the normative runbook.
This makes the distinction mechanical: omit the target row when a literal is
the intended contract.

Literal compatibility is exact:

- No `version-relations` block means today's runbook interpretation and
  receipt shape. The new code does not query a remote or infer a target.
- A block may name some governed skills and omit others. Omitted targets keep
  their literal runbook requirements.
- A declared target is relation-owned and its concrete label is forbidden in
  the rest of the runbook. A relation receipt cannot excuse an unrelated stale
  literal for an omitted target.
- Existing receipted runbooks and controller states that predate the optional
  keys remain readable and verifiable without migration.

At `done runbook`, Fiat resolves every declared ledger at the run's exact
starting commit and records one compatibility anchor. For each target, the
anchor includes the current version; evolution, generation, and epoch;
frontier status, revision, and digest; SHA-256 of the exact current-frontier
and next-job field values; the ledger blob SHA-256; and the matching
`SKILL.md` frontmatter version and blob SHA-256. A field-value digest covers
the exact UTF-8 bytes after its Markdown field prefix and before the line
ending. Fiat records the runbook and relation-block digests as their source.
This capture is all-or-nothing and is not a reservation.

The compatibility rule permits only generation drift between the anchor and
the integration base. Evolution and epoch must equal the anchor. Frontier
status, revision, digest, current-frontier field, and next-job field must
match. Every intervening row from the anchor through the base must be valid
under `VERSIONING.md`, and each generation row must retain the same frontier
revision and digest. A changed compatibility tuple blocks automatic
resolution even if the next numeric label would be easy to calculate.

Non-goals:

- No version server, lock service, queue, reservation branch, issue claim,
  tag, or mutable registry.
- No SemVer range syntax, comparison operator, wildcard, disjunction,
  “latest”, fallback sequence, or arbitrary expression evaluator.
- No automatic change to evolution or epoch, no frontier close or reopen, and
  no `--frontier` use by this run.
- No controller-authored edit, commit, merge, push, pull request, or GitHub
  mutation. Fiat checks and receipts; the existing signed delivery loop owns
  repository changes.
- No rewriting a completed step commit, no unaudited one-parent “version fix”,
  and no silent textual replacement of a label.
- No new state version. Optional relation and resolution containers fit the
  current version-1 additive compatibility rule.
- No weakening of signature, authorship, stacked-merge, affected-path,
  revalidation, Promise Machine, frontier-close, or final integration gates.
- No new dependency, network service, CI workflow, branch rule, or GitHub
  ruleset.
- No recovery of #429, #555, or another halted run. Those states cannot gain a
  new contract retroactively.
- No claim that issue #556 was guarded by controller code it had not yet
  shipped. Its manual adherence and integration revalidation are visible
  bootstrap evidence, not `fiat-version-resolution/v1`.
- No change to Elenchus's parser or schemas. Tests use its existing evidence
  interface exactly.
- No general allocator for ADR numbers, package versions, plugin releases,
  issue numbers, or any identifier other than governed skill generations.

The runbook derived from this study must permit each step's per-run audit log
as an append-only file. A narrow implementation list cannot exclude the audit
record Fiat requires before the step can close.

## 4. Design options

### A. Keep early literals and add reservations

A controller could reserve `fiat-v5.23.1` at `done runbook` in a branch, tag,
issue comment, or central registry. This would make the literal stable only if
every publisher shared one atomic allocator and every abandoned run released
its claim. The repository has no such authority or service. A Git ref used as
a lock also creates stale-claim cleanup and bypass questions, while an issue
comment is neither atomic nor part of the product history.

Rejected. It turns a local delivery tool into shared mutable infrastructure
and still needs a recovery rule when the reservation and final tree disagree.

### B. Keep literals and amend or halt on every collision

This is today's safe behaviour. It worked during active steps for #554, and
the #555 halt correctly refused to alter an accepted runbook during integrate.
It cannot solve the normal case because the version-defining input may change
after amendments close. Moving amendments into integrate would also reopen
completed entry, exit, audit, and source-packet contracts for far more than
version arithmetic.

Rejected as the default. Halt remains the recovery for incompatible drift or
an exhausted bounded history, but compatible generation drift should not
invalidate an otherwise accepted relation.

### C. Add a general expression language and edit the tree automatically

A runbook could carry expressions over ledger fields and let `hexctl` patch
matching files. This would need parsing, evaluation, path selection, text
rewrites, commit authorship, signing, conflict handling, and audit authority.
It would also make arbitrary runbook text an instruction to mutate the
repository.

Rejected. The requested behaviour needs one closed arithmetic relation and a
validator, not a programming language or a second builder.

### D. Resolve one closed relation against exact Git objects

Protasis defines the optional three-field block. Fiat captures a starting
compatibility anchor, then validates the final product against the exact
integration base and product head. A current product mismatch is repaired only
through the ordinary audited step path or the existing signed sync/revalidation
path. The resolution becomes a replayable, bounded receipt and a required
terminal gate.

Chosen. It gives compatible concurrent generations one safe path, leaves true
literal pins unchanged, and refuses every drift outside the named relation.
The trade is an extra integrate-phase transition and bounded Git/ref reads for
relation runs. It cannot prevent GitHub's post-check base race; it makes that
race visible and recoverable without claiming a lock.

### Exact resolution sequence

1. After `done runbook`, source packets carry the exact relation declaration,
   anchor, and current projection. The projection helps Mason build a candidate
   but is labelled provisional. Warden checks the declared relation and ledger
   invariants rather than treating that projection as a reserved result.
2. All step PRs merge into the run branch in controller order. The final
   recorded step merge is the immutable product head for existing Fiat
   receipts.
3. In integrate, Fiat reads the named remote base ref and run ref twice around
   all exact-object reads. The two observations for each ref must match. It
   fetches exact commits into bounded temporary refs or reads already available
   objects without changing the worktree, current branch, index, or
   `FETCH_HEAD`. An unavailable object or changed ref is a refusal, not a
   fallback to local branch state.
4. If the remote base has advanced beyond the product's starting base, the
   existing `sync-run` transition is required. Its signed merge has the final
   product head as first parent and that exact remote base as second parent.
   Any needed concrete version correction is part of that composition commit,
   its path appears in the affected-path set, and a green check covers it in
   `fiat-integration-revalidation/v1`.
5. `hexctl done resolve-versions` performs no product edit. It reads the exact
   base commit and the candidate head: the final product head when no sync was
   needed, otherwise the active signed sync head. It resolves all declared
   targets or none.
6. For each target, the base ledger must extend the anchor ledger history
   without rewrite, every row through the base must satisfy the versioning
   contract, and only compatible generation drift may have occurred. The
   resolved label increments the base row's generation by one while retaining
   evolution and epoch.
7. The head ledger must contain the base ledger rows as an exact prefix and
   exactly one new final row for this target. That row has axis `generation`,
   the resolved label, the anchored frontier revision and digest, and the
   evidence required by the existing versioning contract. This run's row names
   issue #556 or its tracked study/runbook. The ledger header and sibling
   `SKILL.md` metadata name the same resolved label. No other target row may be
   charged to this relation.
8. Once every target passes, Fiat appends one resolution receipt and
   `done:version-resolution` controller-ledger event. `_integrate_directive`
   withholds integration until the active receipt matches the current
   runbook, exact base ref, exact candidate head, and exact target blobs.
9. Immediately before asking GitHub to merge, `next` repeats the ref and
   object checks. Relation runs require a merge method whose resulting commit
   records the checked base and head as parents; a squash or rebase cannot
   prove that pair. The merge request pins the expected pull-request head.
10. `done integrate` re-reads the actual merge commit and remote base. It
    requires the checked integration base as first parent and resolved
    candidate head as second parent, replays the relation from those exact
    objects, then runs every existing final gate. If GitHub joined the head to
    another base after the last check, it refuses the terminal receipt and
    names the external transition. This final `[base, candidate]` parent order
    is distinct from `sync-run`'s `[product, base]` composition order.

The final pre-merge check narrows the race but is not atomic with GitHub's
base update. If the base advances before merge, the operator updates the run
PR, creates or supersedes the signed sync under the current eight-entry
composition-history cap, reruns affected-path revalidation, and resolves
again. If GitHub has already merged onto an unrecorded base, Fiat cannot undo
the external mutation. It records no successful integration receipt; a
maintainer must inspect and repair or revert through normal repository
authority.

### Receipt, state, and controller-ledger shape

`receipts.runbook.version_relations` is optional:

```json
{
  "schema": "fiat-version-relations/v1",
  "source_sha256": "<sha256 of the exact fenced block>",
  "anchor_commit": "<40-hex starting commit>",
  "targets": [
    {
      "skill": "fiat",
      "ledger": "plugins/hexaemeron/skills/fiat/EVOLUTION.md",
      "relation": "next-generation-after-integration-base",
      "anchor_version": "fiat-v5.22.1",
      "evolution": 5,
      "generation": 22,
      "epoch": 1,
      "frontier_status": "open",
      "frontier_revision": "state-shape-validation",
      "frontier_sha256": "e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa",
      "current_frontier_sha256": "<sha256>",
      "next_job_sha256": "<sha256>",
      "ledger_sha256": "<sha256>",
      "skill_sha256": "<sha256>",
      "skill_metadata_version": "5.22.1"
    }
  ]
}
```

Targets are sorted by skill id before persistence, even if the source block
uses another order. The receipt stores no full ledger, frontier prose, email
address, credential, remote response, or command output. The existing
`done:runbook` event gains the schema, source digest, anchor commit, and the
same bounded target records, so state/ledger verification can reconstruct it.

`integrate.version_resolutions` is an optional append-only list capped at
eight. A ninth observation halts; entries are not evicted or overwritten. Each
entry has this shape:

```json
{
  "schema": "fiat-version-resolution/v1",
  "runbook_sha256": "<sha256>",
  "relations_sha256": "<sha256>",
  "base_ref": "main",
  "base_commit": "<40-hex>",
  "head_commit": "<40-hex product or active sync head>",
  "targets": [
    {
      "skill": "fiat",
      "ledger": "plugins/hexaemeron/skills/fiat/EVOLUTION.md",
      "relation": "next-generation-after-integration-base",
      "anchor_version": "fiat-v5.22.1",
      "base_version": "<exact latest base row>",
      "resolved_version": "<exact next generation>",
      "base_ledger_sha256": "<sha256>",
      "head_ledger_sha256": "<sha256>",
      "row_sha256": "<sha256 of exact final row>",
      "skill_sha256": "<sha256>",
      "skill_metadata_version": "<numeric frontmatter value>"
    }
  ],
  "ts": "<UTC timestamp>"
}
```

Only the newest resolution entry can be active, and only while its runbook,
base, head, relations, and target digests still match. An older entry is never
revived merely because refs later return to its values.
`receipts.integrate.version_resolution` copies the active entry into the
terminal receipt. The `done:version-resolution` event contains its canonical
JSON SHA-256 plus the bounded fields needed to compare state and ledger. A
later base or head invalidates the entry but never deletes it. An attempted
all-target resolution writes no partial entry.

`done resolve-versions` joins the existing controller lock as a mutating
command and uses one ignored write-ahead file,
`.hexaemeron/version-resolution.pending.json`. Its closed schema is
`fiat-version-resolution-pending/v1` and binds the prior state fingerprint,
the complete bounded candidate receipt, and the candidate state fingerprint.
The file is durably replaced before the controller-ledger append. On retry,
Fiat either completes the matching state replace after an already durable
event, clears a marker whose matching state and event are both durable, or
visibly rolls back a marker when neither durable transition occurred. A
partial/corrupt ledger line, mismatched fingerprint, unrelated last event, or
different candidate refuses for inspection. Recovery never appends the same
event twice and never derives an old receipt from newly moved refs.

The shape is additive to state version 1. `load_state`, `verify`, `status`, and
packet reconstruction must distinguish absent legacy data, valid current
data, malformed data, stale data, and a full history. The new optional
containers have closed local schemas and refuse unknown fields or wrong types;
the version-1 root keeps its current treatment of unrelated extra keys while
still requiring its existing container spine.

## 5. Risk register seed

```risk-register
relation-block-shape | the optional runbook declaration | Protasis fixtures reject a second block, malformed row, duplicate target, unsafe path, unknown relation, blank line and fenced decoy
literal-compatibility | runbooks with exact pins or no block | golden legacy fixtures stay identical and a declared-target fixture rejects every concrete target token outside the relation block
anchor-substitution | the done-runbook compatibility anchor | tests change the worktree and ref after receipt and prove replay uses the recorded commit, runbook digest and exact Git blobs
generation-arithmetic | the base row to resolved label calculation | table tests cover carries, leading zeroes, malformed labels and the exact evolution-generation-epoch rule from VERSIONING.md
frontier-drift | compatibility between anchor and integration base | each status, revision, digest, frontier text, next-job, evolution and epoch mutation refuses while generation-only drift proceeds
ledger-history-rewrite | base and head history prefix checks | fixtures delete, reorder, edit and duplicate earlier rows and prove none can receive a resolution receipt
metadata-mismatch | the head ledger header and SKILL frontmatter | fixtures change either side independently and require exact resolved-label agreement before receipt
multi-target-partial | one block declaring more than one skill | one failing target leaves state and controller ledger unchanged and a later all-green retry records one sorted receipt
base-ref-race | remote base reads surrounding object inspection | a ref changed between the first and second read refuses with no use of either observation as a stable base
run-ref-race | run-head reads surrounding object inspection | a changed run ref or active sync head refuses and cannot reuse a receipt for the earlier head
post-check-race | GitHub base movement after the last local check | exact merge-parent verification blocks the terminal receipt and documentation states that no atomic base lock was established
remote-evidence-failure | bounded Git and GitHub reads | timeout, nonzero exit, oversized output, malformed JSON and missing object each return a stable refusal without raw response data
git-object-shape | runbook-selected ledger and skill paths | absolute, escaping, symlink, tree, submodule, absent and oversized objects are rejected before parsing
sync-carriage | version correction in a signed base composition | parent-order, signature, pushed-head and exact-base regressions fail and no one-parent fix is accepted
revalidation-coverage | changed target paths in sync-run | the affected set must include every changed ledger and SKILL path and at least one green integration check must cover each
resolution-staleness | a valid receipt followed by base, head or runbook drift | next and done-integrate recompute identities and withhold integration until a new append-only receipt is active
state-history-growth | repeated compatible base advances | eight receipts remain verifiable and the ninth refuses rather than evicting evidence or growing without bound
diagnostic-leak | failures parsing repository or remote-controlled text | messages name field, path and check but omit file contents, credentials, raw signatures and remote response bodies
promise-overclaim | the claim attached to version resolution | Promise text says exact objects satisfied one relation and does not claim reservation, semantic compatibility or race prevention
self-hosted-collision | this run's own Fiat and Protasis target rows | the final report names the old-controller gap and tests insert concurrent generations for either or both targets under the new controller
legacy-state | states and runbooks created before issue 556 | fixture states with no optional keys verify and proceed under their prior literal contract without migration
receipt-replay | state and controller ledger after process restart | verify reconstructs every digest and rejects altered order, target fields, active selection or terminal receipt copy
interrupted-resolution | pending marker, ledger append and state replace | interruption fixtures cover each write boundary and either complete one exact event or retain a named recoverable refusal without duplication
```

## 6. Glossary seeds

- **Anchor.** The exact starting-commit ledger and skill metadata captured when
  Fiat receipts a relation-bearing runbook.
- **Candidate head.** The final recorded product head when no base sync is
  needed, or the active signed `sync-run` head after composition.
- **Compatibility tuple.** Evolution, epoch, frontier status, revision, digest,
  current-frontier value, and next-job value. Generation is deliberately not
  part of the equality test.
- **Concrete correction.** A change to the product's ledger/header/metadata so
  they carry the relation's value. A receipt observes it; it does not make it.
- **Declared target.** One unique skill and ledger path in the runbook's
  `version-relations` block.
- **Generation drift.** One or more valid generation rows published after the
  anchor while the compatibility tuple stays fixed.
- **Integration base.** The exact commit on the named base branch that the
  candidate head is checked against and that the eventual merge commit must
  record as its base parent.
- **Literal pin.** A concrete version in a runbook whose target is not governed
  by a relation row. It keeps today's exact meaning.
- **Projection.** The label produced by applying the relation to a current
  observation before integration. It helps build a candidate but reserves
  nothing.
- **Resolution.** The all-target check that one exact candidate head carries
  the label selected from one exact integration base, recorded as
  `fiat-version-resolution/v1`.
- **Relation source.** The exact fenced runbook block and its SHA-256, already
  joined to the whole runbook digest.
- **Stale resolution.** A recorded resolution whose runbook, relation source,
  base commit, candidate head, or target blob no longer matches live evidence.
- **Versioning compatibility.** Permission to recompute the generation under
  the closed tuple rule. It is not a claim that source changes compose safely.

## 7. Sources

Repository sources, all read at the pinned base unless another ref is named:

- `AGENTS.md`, `.horos/boundary.json`, `PROMISE_MACHINE.md`, and the
  byte-identical Hexaemeron Promise Machine copy.
- `.agents/skills/promise-machine/SKILL.md` and
  `plugins/hexaemeron/AGENTS.md` for routing and repository authority.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, its complete `EVOLUTION.md`,
  `references/push-discipline.md`, `references/plugin-currency.md`, and
  `scripts/hexctl.py`, especially `done_runbook`, `receipted_source`,
  `_integrate_directive`, `done_sync_run`, `done_integrate`,
  `frontier_close_fault`, ledger parsing, and state validation.
- `plugins/hexaemeron/skills/protasis/SKILL.md`, its complete `EVOLUTION.md`,
  `scripts/protasis.py`, and its checker tests.
- `plugins/hexaemeron/skills/VERSIONING.md` and
  `tests/test_evolution_contract.py` for the governed label vocabulary,
  arithmetic, metadata match, and current pinned versions.
- `plugins/hexaemeron/skills/elenchus/SKILL.md`,
  `scripts/elenchus.py`, `tests/run_tests.py`, and
  `tests/test_elenchus_checker.py` for `unittest-json-v1` and
  `elenchus.unittest.v1`.
- `docs/decisions/ADR-006-skill-ledgers-are-not-semver.md`, ADR-024, and
  ADR-025.
- `docs/fiat-runbook-amendments-study.md` and its runbook and audit rounds.
- `plugins/hexaemeron/docs/fiat-frontier-row-attribution/study.md` for exact
  base-blob and already-published-row precedent.
- `plugins/hexaemeron/docs/fiat-merged-attribution/study.md` for the earlier
  integration-time global-identifier collision.
- `plugins/hexaemeron/docs/fiat-per-run-audit-log/` and
  `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md` for the
  sync-time `fiat-v5.22.1` correction and its audit trail.
- The halted issue #555 worktree's state, accepted amended runbook, controller
  ledger, and per-run audit log, read as a red specimen only.

Live repository history and issue sources, read on 2026-08-24:

- [Issue #556](https://github.com/wildcat-finance/skills/issues/556), its
  filing-time and comment-time base observations, labels, and proposed relation.
- [Issue #429](https://github.com/wildcat-finance/skills/issues/429),
  [PR #542](https://github.com/wildcat-finance/skills/pull/542), and their
  preserved step state.
- [PR #585](https://github.com/wildcat-finance/skills/pull/585) and
  [PR #593](https://github.com/wildcat-finance/skills/pull/593), including
  bodies, comments, commits, and carried-forward sections.
- The current `main` ref, open pull requests touching Fiat/Protasis, and the
  active GitHub rulesets. These observations prove present contention, not a
  promise that their values stay fixed.

Outside sources:

- [Cargo dependency specification](https://doc.rust-lang.org/stable/cargo/reference/specifying-dependencies.html)
  and [Cargo glossary](https://doc.rust-lang.org/cargo/appendix/glossary.html)
  for the limited requirement/resolution analogy.
- [GitHub pull-request merge API](https://docs.github.com/en/rest/pulls/pulls)
  for the expected-head `sha` input and absence of an expected-base-SHA input.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what later
implementation must emit. Fiat remains an operator-driven command, so state,
controller-ledger events, packets, status, and named refusals are the durable
signals. No metric, trace backend, unattended alert, or external log service is
added.

The signals answer these on-call questions:

- *What version rule did this runbook declare?* `status` shows the relation
  schema, source digest, target ids and paths, and anchor commit without dumping
  runbook or ledger contents.
- *Was a concrete label reserved?* It says `projection` before resolution and
  `resolved` only for an active exact base/head receipt. It never says
  `reserved`.
- *Why can the run not integrate?* The refusal distinguishes no resolution,
  malformed anchor, incompatible frontier/evolution/epoch drift, product label
  mismatch, changed base ref, changed run ref, stale receipt, uncovered sync
  path, history cap, and post-check merge-parent mismatch.
- *Which base and product did the result cover?* The active receipt and packet
  show exact 40-hex base and head commits, runbook digest, target versions, and
  blob digests.
- *Did another generation merely move the answer?* Status shows anchor version,
  current base version, projected result, and the unchanged compatibility
  tuple digests.
- *Was a prior result replaced silently?* The append-only resolution history
  and controller ledger show every earlier base/head pair and which last entry
  is active. No entry is mutated.
- *Did all declared skills resolve together?* One sorted target list appears in
  one receipt; there is no per-target success state.
- *Did a version correction travel through the checked composition?* The
  existing sync receipt and revalidation artefact name the changed ledger and
  `SKILL.md` paths and the green checks covering them.
- *Did GitHub move the base after the local check?* Terminal verification names
  the expected and actual merge-parent identities and refuses without calling
  the earlier receipt current.
- *Did issue #556 enforce the rule it shipped?* Its final report says no: the
  installed v5.22.1 controller governed that run. It separately names any
  signed sync correction and revalidation evidence, without labelling them a
  v1 version-resolution receipt.

Packets for Surveyor, Mason, Warden, and Scribe carry the same source-bound
relation and active receipt or explicit null. A compact human status precedes
the JSON packet. Values derived from a live ref are labelled with the observed
commit rather than presented as timeless current state.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns these boundaries and
controls.

- **Runbook-controlled paths.** Worth taking: governed skill `EVOLUTION.md`
  paths in the closed relation block. Controls: repository-relative lexical
  validation, no `.` or `..`, no control characters, exact expected basename,
  target-id/directory/version-prefix match, regular Git blob only, bounded
  bytes, and no worktree-followed symlink. Risks: `relation-block-shape`,
  `git-object-shape`.
- **Runbook-controlled relation text.** Worth taking: one exact identifier.
  Controls: no expression evaluation, no aliases, no partial match, at most one
  block and 32 unique targets. Risks: `relation-block-shape`,
  `generation-arithmetic`.
- **Historical repository text.** Worth taking: exact ledger and `SKILL.md`
  blobs at recorded commits. Controls: bounded argv-only Git reads, shared
  parsers, UTF-8 and shape checks, SHA-256 binding, exact history prefix, and
  content-free errors. Risks: `anchor-substitution`, `ledger-history-rewrite`,
  `metadata-mismatch`, `diagnostic-leak`.
- **Remote refs and GitHub merge evidence.** Worth taking: exact named base and
  run heads plus the resulting merge. Controls: bounded calls, timeouts,
  before/after ref reads, expected PR head, exact merge parents, no credentials
  or raw output in state, and refusal on unavailable or changing evidence.
  Risks: `base-ref-race`, `run-ref-race`, `post-check-race`,
  `remote-evidence-failure`.
- **Product-tree mutation.** Worth taking only through an already authorised
  Mason step or signed `sync-run`. The resolution command is read-only with
  respect to Git. Controls: exact parent order, signatures, remote verification,
  affected-path equality, green covering revalidation, and no one-parent
  correction. Risks: `sync-carriage`, `revalidation-coverage`.
- **Persisted controller state.** Worth taking: bounded anchors and resolution
  receipts. Controls: closed schemas, sorted targets, append-only history,
  eight-entry cap, controller lock, subject-labelled write-ahead recovery,
  state/ledger digest agreement, atomic all-target write, and legacy absence as
  a separate valid case. Risks: `multi-target-partial`,
  `state-history-growth`, `legacy-state`, `receipt-replay`,
  `interrupted-resolution`.
- **Delegated model output.** Worth taking: implementation and audit judgements
  under the existing Mason/Warden packets. Controls: the exact relation source,
  anchor and provisional/current status travel in the packet; controller code
  independently rechecks every mechanical fact. No model statement becomes a
  resolution receipt. Risks: `promise-overclaim`, `self-hosted-collision`.

**Always.** Resolve only after the step stack is complete; bind exact runbook,
base, head, ledger, row, and skill metadata evidence; keep all declared targets
atomic; use the signed sync and bounded revalidation path for a post-step tree
change; recheck before merge and at terminal receipt; preserve earlier receipts
and inherited gates.

**Ask first.** Any need for a second relation, a state-version bump, a new
dependency or service, CI or ruleset mutation, another repository, a general
identifier allocator, a ninth retained resolution, a non-merge integration
method, or recovery of an already halted run requires an amended study and
maintainer direction before implementation.

**Never.** Treat a projection as a reservation; call skill labels SemVer;
increment evolution or epoch automatically; use `--frontier`; rewrite an
earlier ledger row or receipt; mutate product bytes from `done
resolve-versions`; accept a partial target set; use mutable worktree files as
the evidence for a recorded commit; hide a ref race; claim GitHub supplied an
atomic expected-base check; or issue a terminal receipt for an unrecorded
base/head pair.

## 10. The budget, or its absence

None, and no performance claim is made. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md)
owns performance budgets and requires a recorded baseline before a
speed-motivated change. This work adds bounded integrate-time reads only for a
relation-bearing runbook: two observations of each relevant ref, exact ledger
and skill blobs for no more than 32 targets, and a history capped at eight.

The existing 2 MiB per-file input cap, bounded subprocess output, network
timeouts, 32-target cap, and eight-receipt cap are correctness and resource
boundaries, not performance targets. If implementation cannot stay inside
them, the study is amended rather than silently increasing them.

## 11. The fail-closed posture

The default outcome of absent, changing, unreadable, malformed, incompatible,
or contradictory evidence is no resolution receipt and no terminal
integration receipt. A failed attempt does not edit the worktree, index,
branch, product commit, earlier state receipt, or controller-ledger event. A
multi-target attempt commits its one state-and-ledger transition only after
every target passes.

Recovery follows the cause:

- A transient or changing ref is read again from the start; no mixed snapshot
  is retained.
- Compatible generation drift requires a new or superseding signed sync when
  the product value changes, fresh affected-path revalidation, and a new
  append-only version-resolution receipt.
- If the base did not advance and the completed product still carries the
  wrong label, there is no composition change to justify `sync-run`. The
  product is defective against its accepted relation and the run halts rather
  than manufacturing an integration-only edit.
- Evolution, epoch, or frontier drift requires a source-bound study amendment
  and complete runbook-field re-derivation while amendments are legal, or a
  halt. On successful `amend runbook`, Fiat preserves the former receipt and
  captures a fresh compatibility anchor for the unchanged target/relation
  block. A different target or relation needs a new run. Once integrate has
  begun and amendments are unavailable, the run halts and a new authorised run
  studies the changed premise.
- A malformed or rewritten ledger, mismatched metadata, missing Git object,
  bad signature, wrong sync parents, incomplete path coverage, failed check,
  or state/ledger disagreement is repaired at its owning boundary and then
  rerun. No “best effort” label is selected.
- A post-check GitHub merge onto an unrecorded base earns no receipt. The
  controller cannot undo it; a maintainer inspects the already-made repository
  transition and chooses a normal repair or revert.
- Reaching the eight-entry resolution cap halts. Evidence is not evicted to
  make room.
- An interrupted receipt transition reruns through its pending marker. It may
  complete the one exact ledger/state pair or roll back before either became
  durable; it never skips a corrupt tail, reuses changed ref evidence, or
  duplicates an event.
- In this self-hosted issue #556 run, the old controller cannot run the new
  receipt transition. A collision uses its already-governed signed sync and
  revalidation path or halts, and the final report records the version gap.
  Nobody constructs a v1 receipt by hand or treats test success as if the old
  controller had enforced it.

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns reproduction,
localisation, reduction, cause repair, and the regression. Every fix-bearing
audit round for this runbook uses this exact source contract:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
report file: tmp/elenchus/<step-and-round>.json
expected JSON schema: elenchus.unittest.v1
```

The `{report}` placeholder appears exactly once in the test command. The
runner writes a fresh file inside the worktree; Warden passes
`--report-format unittest-json-v1` and that path to Elenchus. Tests fail if the
runbook supplies `elenchus.unittest.v1` as the report format even though that
string is correct inside the JSON object.

The core regression matrix starts red on
`8e6480230a5f43c57aef4f9a6c52f4c602d86790` and goes green only after the
cause is fixed. It includes the exact #555 topology; no drift, one and several
compatible generation insertions; one incompatible change for every
compatibility field; one- and two-target declarations; legacy literal state;
every relation-block parse fault; history and metadata tampering; ref changes
between reads; missing and oversized objects; sync parent/signature/path/check
faults; stale and capped histories; process restart/replay; and a simulated
post-check base move whose merge parents do not match the receipt. Interruption
fixtures stop before and after the pending replace, ledger append, state
replace, and pending clear.

Acceptance commands for the derived runbook include:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_protasis_checker
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study .hexaemeron/study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py .hexaemeron/study.md
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

Each runbook step names its narrower red/green command and permits its
append-only per-run audit record. Whole-suite green is not a substitute for
the focused race, receipt, and legacy regressions.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns where durable
explanations live.

- **Runbook relation content contract:**
  `plugins/hexaemeron/skills/protasis/SKILL.md`. It defines the optional
  `version-relations` block, the single relation, symbolic-target rule, literal
  compatibility, and cold-review questions.
- **Runbook relation structural contract:**
  `plugins/hexaemeron/skills/protasis/scripts/protasis.py` and focused checker
  fixtures. New code P006 covers a present-but-malformed, duplicate, or unsafe
  closed block and a concrete token for a declared target without renumbering
  P000-P005. The checker establishes shape only; it does not claim that a
  chosen target or relation is suitable.
- **Compatibility, receipt, transition, packet, and recovery contract:**
  `plugins/hexaemeron/skills/fiat/SKILL.md`, its integration references,
  `scripts/hexctl.py`, and focused Fiat tests. They define anchor capture,
  `done resolve-versions`, stable-snapshot reads, all-target resolution,
  append-only state/ledger evidence, active-receipt selection, sync carriage,
  final merge-parent replay, and legacy behaviour.
- **Promise Machine declarations:** Protasis's
  `protasis-runbook-readiness` evidence and boundary gain the declared block
  and literal-compatibility rule. Fiat gains one consequence-2 promise for a
  successful `fiat-version-resolution/v1` receipt. `fiat-final-integration`
  requires that current receipt for relation-bearing runs and states that it
  proves one exact relation over one exact base/head pair, not reservation,
  semantic compatibility, or an atomic GitHub lock. Root/plugin Promise copies
  and coverage remain byte-identical and green.
- **Versioning decision:** add a dated issue-556 addendum to
  `docs/decisions/ADR-006-skill-ledgers-are-not-semver.md`. That record already
  owns the counter vocabulary; its addendum fixes “generation relation versus
  resolved label” without consuming another global ADR number during the race
  this issue addresses.
- **Tracked derivation:** a stable study and runbook under
  `plugins/hexaemeron/docs/` record the source-bound decision and discrete
  steps. This `.hexaemeron/study.md` remains the controller artefact for this
  run.
- **Fiat version:** one generation row in
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, retaining evolution 5, epoch 1,
  frontier revision `state-shape-validation`, digest
  `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`,
  current-frontier text, and issue #363 next job. From the pinned base its
  candidate is `fiat-v5.23.1`; the runbook records the relation and integration
  supplies the final label.
- **Protasis version:** one generation row in
  `plugins/hexaemeron/skills/protasis/EVOLUTION.md`, retaining evolution 4,
  epoch 0, frontier revision `amendment-block-check`, digest
  `1014071026a149d38e7d79c222dfcfc25dd061d825fac9e7813a3a46b184cd29`,
  current-frontier text, and its held amendment-block-check job. From the
  pinned base its candidate is `protasis-v4.8.0`; the same relation rule owns
  the final label.
- **Elenchus:** no skill or version change. Its existing CLI identifier,
  report schema, failure order, and guard rule are consumed exactly.
- **No package or marketplace version decision:** this issue changes two
  governed skill generations. It does not by itself assert a plugin package
  release number or install action.
- **Bootstrap disclosure:** this run's final report, under the existing Fiat
  Scribe contract, states that v5.22.1 drove the run and that P006 and the v1
  resolution Promise begin with a later run after plugin refresh. If a
  collision required a signed sync correction, it cites that exact composition
  and revalidation separately.

The runbook should divide these homes into discrete green steps: first the
Protasis declaration/check and its red fixtures; then Fiat anchor/state/Promise
capture and legacy fixtures; then integrate-time resolution, sync/race/final
gate and the #555 regression; then tracked explanation and the two relation-
resolved generation rows. Every step starts from the previous green commit,
permits its per-run audit append, names the exact tests above, and keeps product
changes separate from later base-sync composition evidence.

If implementation discovers that a second relation, state version 2, a new
dependency, a non-merge publication method, or a broader recovery transition
is necessary, this study is amended before code for that wider decision. The
current choice does not authorise it.

## Boundaries the study must state

**Always.** Preserve the exact held Fiat and Protasis frontiers; resolve all
declared targets from one stable exact integration base; keep literal-only
runbooks unchanged; carry product corrections only through an audited step or
signed sync with bounded green revalidation; retain every superseded receipt;
and rerun Protasis then Imprimatur on any study amendment.

**Ask first.** Widening the relation language, moving another version axis,
changing the state version, adding a service or dependency, altering GitHub
rules, using another integration method, evicting evidence, touching another
repository, or reviving a halted historical run all require new authority and
a re-derived runbook.

**Never.** Pass `--frontier`; reserve the pinned-base candidates; silently
renumber a literal; alter a held frontier, evolution, or epoch; rewrite a
ledger prefix or receipt; accept part of a multi-target result; let a receipt
command edit or commit product files; treat a ref read as an atomic lock; put
the Elenchus JSON schema in the CLI format field; or call the run integrated
when the recorded base/head pair is not the pair GitHub joined.
