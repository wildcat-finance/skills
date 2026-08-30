# Study: assign ADR numbers at merge, not at authoring time

Issue: [wildcat-finance/skills#888](https://github.com/wildcat-finance/skills/issues/888)

Survey base: `main` at
`6e42389ef20c11c948b2c97a4915d4c592503ee8`, 30 August 2026.

## Revalidation

This copy revalidates the halted-run survey from
`c3f67148c2a880cbc8a2f2530fd050bdec1ea7b4`. The sole first-parent change is
[PR #993](https://github.com/wildcat-finance/skills/pull/993). Its eight paths
change collective-identity files, portable runtime copies, generated boundary
and baseline data, and identity tests. It changes no decision record,
decision-record test or workflow, Hypomnema or Fiat source, or audit source.
Issue #888 is unchanged, the audit-synopsis check remains current, and ruleset
`21830871` still reports `evaluate`, strict checks, the same three Actions
contexts, and no bypass. The problem, prior art, audit inventory, design, and
unmet external activation prerequisite therefore remain unchanged.

The repository can build and test the allocator now, but it cannot yet claim
that two concurrent pull requests are race-free in production. The live
`Required CI` ruleset, id `21830871`, has strict status checks but its
enforcement is `evaluate`. GitHub records results in that mode without blocking
a merge. Moving the ruleset to `active`, adding the base-owned assignment
context, and running a canary are separately authorised external operations.

## Assumptions

- Pull requests to `main` remain the only supported publication route for new
  decision records. A direct push is outside this design.
- Fiat keeps product mutation in signed contributor commits. `hexctl` may
  inspect, direct, and receipt the assignment, but it does not edit the tree.
- Existing numbered records and frozen numeric references remain valid bytes.
  The new form applies prospectively.
- The repository continues to use GitHub Actions integration `15368` for
  base-owned status contexts.
- Gaps are spent numbers. Allocation follows the greatest number in the exact
  base, never the smallest missing number.

## 1. Problem statement

The repository chooses an ADR number while a delivery is still being authored.
Other deliveries continue to merge before that branch enters `main`, so the
number can become stale without producing a Git conflict. Two files named
`ADR-050-a.md` and `ADR-050-b.md` coexist as different paths; the conflict
appears only in the repository invariant after both trees are composed.

The failure has happened more than once:

- The history behind issue #888 records two untracked drafts using ADR-050 and
  ADR-051 while issue #621 landed ADR-050 at merge
  `0698092d27871031b6d5521d77f6e8d8dc5dc937`.
- The Wave Delta branch duplicated ADR-024. Main stayed red until issue #582
  renumbered that group to ADR-028 through ADR-032.
- PR #736 moved its record from ADR-042 to ADR-043 after the base took 042. Its
  frozen study and runbook still contain eleven references to the old number.
- Root audit finding `S5-R1-01` records a planned ADR-017 becoming occupied by
  concurrent PR #521. The delivery renumbered to ADR-018 and amended every
  mutable copy.
- The current tree has ADR-060 but no ADR-059. Frozen issue #936 artefacts name
  ADR-059, so filling the visible hole could bind those bytes to another
  decision later.

`tests/test_decision_records.py` checks filename shape, duplicate numbers,
heading agreement, and a collision with a locally available default-branch
ref. It does not allocate. Its default-branch arm skips when no such ref exists,
while `.github/workflows/repo.yml` uses the default shallow
`actions/checkout@v4` configuration. Even with a complete fetch, comparing to
`main` before `done sync-run` leaves the same interval #888 rejects: the base
may advance again before merge.

A successful change must establish all of these properties:

1. An author writes an unnumbered record and cites one stable identity that does
   not change when the file is assigned.
2. The assigned number is derived from one exact integration-base commit, not
   from branch age, a local clock, a PR number, or a cached ref.
3. The final signed composition commit records the exact base, mapping, and
   transformed bytes.
4. If the base advances, the old composition cannot merge and a replacement
   recomputes the mapping.
5. Two candidates that initially choose the same number cannot both enter
   `main` with it.
6. Existing files, numeric references, and receipted artefacts are not rewritten.
7. A repository can demonstrate the local mechanism without pretending the
   production exclusion gate is active.

## 2. Prior art

### This repository

The latest two pull requests on current `main` that add decision records were
read in full:

- [PR #983](https://github.com/wildcat-finance/skills/pull/983), merged at
  `c48b8baca9bb632529bc0303defc5fae335c768a`, adds ADR-060. Its run had to
  avoid an in-flight ADR-059, and its audit swept local and remote refs before
  accepting 060.
- [PR #967](https://github.com/wildcat-finance/skills/pull/967), merged at
  `3b9a67f765be7256fa79a28fdfd4d4c33aeb7bad`, adds ADR-058. More usefully for
  this design, it separates a base-owned status implementation from later
  canary and ruleset activation. It does not claim the external gate before
  that second operation.

The last two merged deliveries that state the current allocation workaround
directly were also read:

- [PR #961](https://github.com/wildcat-finance/skills/pull/961) carries
  ADR-055. Its step audit says the number is checked at the branch cut and read
  again immediately before integration because main moves several times an
  hour.
- [PR #947](https://github.com/wildcat-finance/skills/pull/947) carries
  ADR-054 and proves it free at that cut. The proof is honest but does not close
  the cut-to-merge interval.

PRs [#736](https://github.com/wildcat-finance/skills/pull/736),
[#790](https://github.com/wildcat-finance/skills/pull/790),
[#922](https://github.com/wildcat-finance/skills/pull/922),
[#954](https://github.com/wildcat-finance/skills/pull/954), and
[#968](https://github.com/wildcat-finance/skills/pull/968) were read for the
earlier renumber, branch-cut, and signed-descendant cases. PR #968 permits an
honest descendant after a push receipt; it does not make an early ADR number
current.

The closest controller precedent is `docs/fiat-version-relations-study.md` and
`docs/fiat-version-relations/runbook.md`. They keep a symbolic relation in the
receipted runbook, resolve it against exact Git objects during integration,
record an append-only result, and replace a stale sync. They also establish an
important limit: GitHub's merge API can bind an expected head but has no
expected-base argument. ADR assignment therefore needs both exact-object replay
and an enforced up-to-date rule.

Hypomnema 4.6.0 owns the decision-record convention and H004 to H006. Fiat
5.43.1 owns signed integration composition, sync supersession, exact-head
verification, and receipts. The feature is a prospective generation change to
both skills; it does not move either held frontier.

### Audit evidence

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited 0 at the survey base. Every discovered source/synopsis pair was fresh,
committed, and matched its recorded SHA-256. The in-scope inventory is:

| Source | Relevant evidence | Disposition in this design |
| --- | --- | --- |
| `audit/AUDIT_SYNOPSIS.md` | Hypomnema's record-shape and source-reference rounds are clean after their fixes. Root `S5-R1-01` records an ADR-017/018 concurrent collision; the shared audit file itself also needed textual reconciliation between runs. | Preserve H004 to H006, add the stable reference form, and remove numeric references from mutable run artefacts. |
| `audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.synopsis.md` | All reported findings are fixed. The rounds cover exact base/head binding, replacement Git objects, inherited Git configuration, shallow history, object type, replay, reflog and base-move races. The remaining lead is that GitHub offers no atomic expected-base merge lock. | Reuse the exact-object and stale-sync rules. Add a separately enforced strict base gate; do not represent an API reread as a lock. |
| `audit/rounds/fiat-621-isolate-disposable-fixture-signing.synopsis.md` | The decision record moved from planned ADR-045 to ADR-046 after 045 landed. The audit required the record to explain why the frozen study used the former number. | Stable slug citations prevent this explanatory repair from being needed for future records. Signed-assignment verification inherits the existing signing boundary. |
| `audit/rounds/fiat-854-stage-the-portable-sync-before-the-horos-sca.synopsis.md` | The audit accepts ADR-055 only at the observed cut and explicitly requires a reread immediately before integration. | Replace the manual reread with a checked assignment in the active sync; still refuse if the base later moves. |
| `audit/rounds/fiat-904-grade-the-router-corpus-from-a-driver-rather.synopsis.md` | ADR-051 was free at the branch cut, and the audit points to the open collision surface rather than claiming merge safety. | Treat branch-cut freedom as diagnostic evidence, not authorisation. |
| `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.synopsis.md` | `adr-number-collision` was reviewed by proving ADR-054 absent from one observed `origin/main`. | Keep this as a fixture for the old check and show that an advanced base invalidates the result. |
| `audit/rounds/fiat-975-remove-the-child-or-golden-retriever-primer.synopsis.md` | ADR-060 was unique across the 90 refs present during audit, ADR-058 was the highest other record, and ADR-059 existed on an in-flight ref. A later round notes that no fetch moved those refs. | Allocate `max(base)+1`; never fill holes; bind the conclusion to an immutable base rather than a mutable ref sweep. |
| `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | F-01 fixed state fingerprinting and F-09 fixed a reserved receipt namespace. Concurrent `hexctl` access remains outside its single-driver contract. | Put assignment data in a versioned receipt namespace and rely on the repository merge gate, not concurrent controller writers, for inter-PR exclusion. |

Alexandria, Ariadne, Berean, Brevitas, Hermes, Horos, Janus, Lazarus, Lemma,
Pandects, Probitas, Sapheneia, and Tabularium audit sources were present and
fresh in the audit-synopsis check. They do not own an affected file,
decision-record interpretation, integration transition, or GitHub gate, so no
finding from them enters this packet.

### Organisation and outside precedent

The only other organisation repository found with the same convention was
`wildcat-finance/skills-braintrust`, under
`commercial-credit-sidecar/docs/decisions`. ADR-001 through ADR-005 entered in
one scaffold and ADR-006 followed in a later commit. There is no allocator or
parallel-authoring rule there; serial history is not evidence for this race.

Outside examples divide into four approaches:

- [Rust RFCs](https://github.com/rust-lang/rfcs) start with
  `text/0000-slug.md` and rename to the PR number after opening. The identity is
  unique, but it is allocated before acceptance and is not the next ADR number.
- The [Opinionated Digital Center ADR repository](https://github.com/opinionated-digital-center/architecture-decision-records)
  uses `XXXX-slug` while drafting, then rebases, assigns the next free number,
  force-pushes, and merges. That is the same authoring shape, but its manual
  pre-merge window is the gap this repository must close.
- [`adr-tools`](https://github.com/npryce/adr-tools/blob/master/src/adr-new)
  scans existing filenames and writes `max+1` when `adr new` runs. It is the
  current failure model when two branches run it independently.
- [MADR's numberless-heading decision](https://adr.github.io/madr/decisions/0002-do-not-use-numbers-in-headings.html)
  keeps a number out of the H1 to make pre-publication rename easier. This
  design instead retains the repository's numbered final H1 and makes its one
  change mechanical.
- [PEP 1](https://peps.python.org/pep-0001/) has a PEP editor assign the next
  available number before merge. A serialized human role works for that queue;
  it does not give concurrent Fiat runs a replayable lock.

GitHub documents `evaluate` as non-enforcing and `active` as enforcing. It also
documents that strict required status checks require the topic branch to be up
to date before merge. Those two statements are the external premise of the
race proof, not a property the repository code can manufacture:

- [Creating rulesets](https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)
- [Available rules for rulesets](https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

## 3. Constraints and non-goals

The implementation starts from Python 3.14.6 and the exact Git base named at
the top of this document. It uses only the standard library and native Git.
No dependency, service, database, long-lived allocator branch, or separate
numbering authority is introduced.

The file conventions are prospective:

- Draft: `docs/decisions/drafts/<slug>.md`, with H1
  `# Decision: <title>`.
- Stable reference: `adr/<slug>`, where the slug is lowercase ASCII kebab-case,
  at most 96 bytes.
- Final: `docs/decisions/ADR-NNN-<slug>.md`, with H1
  `# ADR-NNN: <title>`.
- Existing ADR filenames, headings, and numeric references remain accepted.

The assignment is bounded to 32 drafts in one composition and the existing
Hypomnema 1 MiB document read limit. Git path reads use NUL framing. Existing
Fiat byte, path, object, and sync-supersession ceilings remain unchanged.

The following work is outside the packet:

- renumbering existing ADRs or adding stable-reference text to their bodies;
- rewriting receipted studies, runbooks, audit records, comments, or commit
  messages;
- allocating numbers for other repositories or other document types;
- using PR numbers, issue numbers, timestamps, hashes, or a global service as
  ADR numbers;
- closing issue #889, changing its delivered check graph, or treating it as
  authority to edit the live ruleset;
- changing merge method, bypass actors, review policy, GitHub App permissions,
  or direct-push policy;
- performance improvement; and
- Solidity changes or claims. X-Ray, Solidity Auditor, Fizz, and Hermes do not
  apply to this document workflow.

The feature may land its repository code before activation, following PR #967's
bootstrap pattern. Until a separate canary and ruleset operation completes, it
is a tested allocator and validator, not an enforced no-collision guarantee.

## 4. Design options

### A. Reserve a number when authoring starts

A ledger or Git ref could reserve the next number. That gives drafts a literal
too early, needs abandoned-reservation policy, and conflicts with #888's stated
moment of assignment. Rejected.

### B. Use the issue or pull-request number

GitHub supplies a unique number without a lock. It is known before merge,
creates a sparse second namespace, and leaves accepted records numbered by an
unrelated queue. Rejected.

### C. Re-read main just before merge

This is the present ADR-055 practice. It reduces the window but cannot close
it: two branches can both read the same base before either merge. Rejected.

### D. Stop numbering new records

Stable slugs alone remove the collision. They also discard a running repository
convention when the issue asks to change allocation time, not remove numbers.
Rejected.

### E. Stable draft identity plus checked assignment in the active sync

Chosen. Authors and receipted artefacts use `adr/<slug>`. The final signed Fiat
sync assigns the number against its exact base, transforms the draft, and
records the mapping. A base-owned status validates the candidate without
executing candidate code. An active strict up-to-date rule serializes admission
to `main`.

The trade is explicit: the repository gains one stable reference form, one
bounded transform, a Fiat receipt extension, and a base-owned status context.
In return, number changes do not touch frozen prose and merge safety has a
testable external premise. This is less machinery than reservations or a
general expression language, and more honest than another last-second reread.

### Draft and reference contract

Hypomnema indexes both draft and final paths by their slug. `adr/<slug>` resolves
to exactly one record in the candidate tree. It refuses duplicate slugs, a
numbered file below `drafts/`, a draft outside that directory, a malformed or
oversized slug, a final filename whose slug differs, and a source comment whose
stable reference has no indexed target. Legacy `ADR-NNN` references keep their
current H002 and H006 treatment.

Runbook, study, audit, issue, and commit prose may cite `adr/<slug>` before and
after assignment. The assignment does not rewrite those bytes. A final record
keeps the slug in its filename, so repository search resolves the reference
without a redirect file on `main`.

### Deterministic assignment

Let `B` be the full immutable commit named as the integration base. Let `P` be
the signed product tip whose tree still contains the drafts. For every existing
top-level record in `B`, parse the three-digit number. Set `m` to the greatest
parsed number. Missing numbers below `m` are ignored.

Sort the new draft slugs by their ASCII bytes. Draft `k`, counted from one, is
assigned `m+k`. The assignment operation:

1. verifies `B` and `P` are commits, the repository is complete, and the active
   integration branch still names `B`;
2. reads draft and numbered paths from Git objects, not worktree glob output;
3. renames each draft to `ADR-NNN-<slug>.md`;
4. changes only the exact first heading from `# Decision: <title>` to
   `# ADR-NNN: <title>`;
5. preserves every other byte and file mode; and
6. emits a canonical `fiat-decision-assignments/v1` report with the base,
   product, result tree, ordered mapping, input/output blob ids, and limits.

The contributor composing the final sync applies that report and signs the
sync commit. `hexctl` verifies the Git objects and report before recording it.
It does not perform the rename. The signed commit message carries one
`ADR-Assignment-Base: <B>` trailer and one ordered
`ADR-Assignment: adr/<slug>=ADR-NNN` trailer per mapping. The receipt stores the
same data and the commit-message digest.

If `main` advances, Fiat's existing sync-supersession path builds a replacement
from the unchanged product tip and the new base. The stale sync is retained in
the append-only controller history but is not an ancestor of the active sync.
The replacement recomputes all numbers. `done integrate` verifies that the
active assignment-bearing sync is the exact PR head and an ancestor of the
recorded merge commit.

### Race-freedom argument

Assume the production ruleset is `active`, its required assignment status is
base-owned, strict up-to-date enforcement is true, and there is no bypass.
Take two candidate heads, `H1` and `H2`, built from the same base `B`. Both may
validly assign `N = max(B)+1` before either merges.

If `H1` merges first, `main` advances to `B1`, whose tree contains `N`.
`H2` is no longer up to date with `main`. Strict enforcement blocks `H2`; its
old green result cannot authorise a merge. To become eligible, `H2` must build a
new signed sync `H2'` against `B1`. The base-owned validator replays the
mapping and requires `max(B1)+1`, which is greater than `N`. If `H2` merges
first, the same argument applies symmetrically. GitHub serializes changes to
the branch, and the strict rule checks eligibility against the current branch,
so no serial order admits both mappings.

The proof fails if enforcement is `evaluate`, if strictness is disabled, if a
bypass or direct push exists, if the status is candidate-owned, or if the merge
service does not enforce the documented up-to-date rule at admission. The live
repository currently fails the first premise. A local test can prove stale-base
refusal, but only an authorised active-ruleset canary can establish the external
premise here.

### Base-owned validation and bootstrap

A new `pull_request_target` workflow checks out only the protected base and
runs the base-owned validator. Candidate commits are fetched into a fresh bare
repository as data; no candidate script, hook, configuration, or checkout is
executed. The status is written to the exact PR head under a distinct
`adr-assignments` context. The validator requires the PR head itself to be the
active assignment sync when the base-to-head delta adds a decision record.

The workflow first lands without being required. A separately authorised
maintainer then runs a signed canary, verifies the status comes from Actions
integration `15368` on the exact head, adds `adr-assignments` to ruleset
`21830871`, and changes enforcement from `evaluate` to `active`. The ruleset
must retain strict status checks and no bypass actors. None of those external
operations belongs to this study or to an implementation permission inferred
from it.

### Test design before implementation

The focused unit and integration fixtures must exist before the implementation
is kept:

- a base ending at ADR-060 with holes at 026, 027, and 059 assigns the first
  draft 061, never a hole;
- two slugs assign a contiguous batch in bytewise order regardless of filesystem
  enumeration;
- the draft-to-final transform changes only path and H1, and its report replays
  from Git objects;
- a missing, duplicate, malformed, non-ASCII, traversal, control-character, or
  oversized slug refuses;
- a shallow repository, replacement object, inherited repointing Git variable,
  wrong object type, mismatched blob, extra trailer, stale base, and moved PR
  head refuse before a receipt;
- legacy numbered ADRs and numeric comments remain clean;
- `adr/<slug>` resolves both draft and final forms and dangles visibly;
- a root-suite fixture starts two candidates at `B`, gives both 061, advances
  the fixture main with one, proves the other stale, then recomputes it as 062;
- reverting the base comparison makes the stale candidate pass and must be
  killed by the regression; and
- the base-owned workflow fixture proves candidate scripts and Git config are
  never executed.

The local prototype succeeds when those tests, the root suite, the Hexaemeron
suite, the decision-record validator, Hypomnema, Phylax, Ephoros, Imprimatur,
the Promise Machine checks, audit-synopsis currency, Horos boundary, and
`git diff --check` all pass under Python 3.14.6. Production success additionally
requires the authorised canary and live ruleset query to show
`enforcement=active`, `strict=true`, required contexts including
`adr-assignments`, and no bypass actors. That second success condition is not
met on 30 August 2026.

### The five discipline questions

**Elenchus.** The causal regression is the two-candidate fixture. The guard is
the base-owned stale-base check plus strict enforcement. Every audit fix uses
the configured runner and leaves a machine-readable report.

**Ephoros.** The operator needs the exact base SHA, head SHA, ordered mapping,
status context, enforcement mode, and refusal reason. The controller records
the first five durably; GitHub records the status and ruleset result.

**Phylax.** Trust boundaries are Git refs, Git objects, commit signatures,
candidate filenames and bytes, commit trailers, controller reports, GitHub
event fields, and live ruleset state. Candidate code is data to the privileged
workflow, never executable input.

**Hypomnema.** Stable reference syntax and draft/final placement live in the
Hypomnema contract. The expensive decision is recorded once in the new ADR;
Fiat records only the transition evidence.

**Metron.** There is no speed claim or performance change to keep. The bounded
record set is too small to justify a measurement programme; correctness and
resource ceilings decide acceptance.

## 5. Risk register seed

```risk-register
stale-base-window | assignment derived from a base that is no longer current | advance the fixture base after a green mapping and require refusal before receipt and merge
ruleset-not-enforcing | live Required CI ruleset remains evaluate instead of active | query ruleset 21830871 and withhold the production claim unless enforcement is active
strictness-disabled | a green old head remains mergeable after main advances | require strict required status checks in the live canary evidence
bypass-or-direct-push | a path enters main without the assignment status | require no bypass actors and keep direct push outside the supported publication route
candidate-owned-gate | candidate bytes weaken the validator that judges them | run the validator from pull_request_target on the protected base and never execute candidate code
shallow-or-stale-ref | local refs omit a record or name an old base | fetch exact event SHAs into a fresh bare repository and refuse unavailable complete history
hole-reuse | an absent historical number is rebound to another decision | assign greatest base number plus one and mutate the fixture to offer lower holes
slug-identity-drift | a draft and final file use different stable identities | derive both paths from one validated slug and replay the path and heading transform
batch-order-drift | filesystem order gives the same drafts different numbers | restrict slugs to ASCII and sort their bytes before allocation
assignment-byte-drift | merge-time editing changes decision content beyond the number | compare blob bytes after one exact H1 substitution and reject every other difference
unreceipted-mapping | the tree has a number but no immutable allocation evidence | require signed trailers and a matching fiat-decision-assignments/v1 receipt
superseded-sync-ancestry | a stale allocation remains in the final commit ancestry | require the active replacement sync as exact PR head and replay its ancestry at done integrate
historical-reference-rewrite | implementation repairs old numeric citations and changes frozen evidence | assert existing ADR and receipted artefact blobs are unchanged
git-object-substitution | replacement objects or wrong object types change the replayed tree | clear repointing variables and verify commit tree and blob types with native Git
controller-product-mutation | hexctl performs the rename it is meant to receipt | unit-test that the controller only verifies reports and that tree bytes are unchanged on refusal
status-head-mismatch | a status for one head is read as evidence for another | write and verify adr-assignments on the exact event head SHA
bootstrap-overclaim | code landing is described as enforced before the canary and ruleset change | keep local and production success criteria separate in the runbook PR body and receipt
```

## 6. Glossary seeds

**Stable ADR reference**
: `adr/<slug>`, the prospective identity used in prose before and after number
  assignment.

**Draft record**
: An otherwise complete decision record below `docs/decisions/drafts/` whose H1
  carries no number.

**Assignment base**
: The immutable default-branch commit whose final decision tree supplies the
  greatest allocated number.

**Assignment sync**
: The signed active Fiat sync commit that composes product and assignment base,
  performs only the deterministic draft transform, and carries mapping trailers.

**Active mapping**
: The ordered slug-to-number mapping attached to the active assignment sync.
  Superseded controller history is evidence, not an allocation in the final tree.

**Base-owned validator**
: Code read from the protected base and run in a privileged workflow while the
  candidate is treated only as bounded Git data.

**Strict up-to-date enforcement**
: GitHub's rule that a candidate must contain the current base before its
  required status results can admit the merge.

**Bootstrap state**
: The interval after repository code lands and before an authorised canary and
  active ruleset make the new status a production gate.

## 7. Sources

Primary repository sources read for this study:

- [Issue #888](https://github.com/wildcat-finance/skills/issues/888), live open
  issue body and labels on 30 August 2026.
- [Issue #889](https://github.com/wildcat-finance/skills/issues/889) and
  [PR #938](https://github.com/wildcat-finance/skills/pull/938), for the complete
  check graph and its later external ruleset operation.
- PRs [#983](https://github.com/wildcat-finance/skills/pull/983) and
  [#967](https://github.com/wildcat-finance/skills/pull/967), the last two
  main-merged PRs adding decision records at the survey base.
- PRs [#961](https://github.com/wildcat-finance/skills/pull/961) and
  [#947](https://github.com/wildcat-finance/skills/pull/947), the last two
  merged deliveries read that explicitly state branch-cut or immediate
  pre-integration allocation.
- PRs [#736](https://github.com/wildcat-finance/skills/pull/736),
  [#790](https://github.com/wildcat-finance/skills/pull/790),
  [#922](https://github.com/wildcat-finance/skills/pull/922),
  [#954](https://github.com/wildcat-finance/skills/pull/954), and
  [#968](https://github.com/wildcat-finance/skills/pull/968), for collision and
  integration-history precedents.
- `tests/test_decision_records.py`, `.github/workflows/repo.yml`,
  `docs/decisions/`, and Git history for commit
  `71a5961b7032a0670cca48ec1119ed27a84ae983`.
- `plugins/hexaemeron/skills/hypomnema/SKILL.md`, its checker, tests, and
  `EVOLUTION.md` at Hypomnema 4.6.0.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `hexctl.py`, tests,
  `EVOLUTION.md`, `docs/fiat-version-relations-study.md`, and
  `docs/fiat-version-relations/runbook.md` at Fiat 5.43.1.
- The eight in-scope audit sources enumerated in item 2, after the repository
  audit-synopsis currency check exited 0.
- Live ruleset `21830871`, read through the GitHub API on 30 August 2026:
  `name=Required CI`, `enforcement=evaluate`, strict required status checks,
  contexts `identity`, `invariants`, and `plugins`, with no bypass actors.
- `wildcat-finance/skills-braintrust` decision history under
  `commercial-credit-sidecar/docs/decisions`.
- The Rust RFC, Opinionated Digital Center, adr-tools, MADR, PEP 1, and GitHub
  documentation links in item 2.

No hidden issue was treated as live evidence. Issues #582 and #798 were not
readable without credentials that can see their author; their facts are used
only where the current issue, Git history, PR, or committed audit states them.

## 8. Signals, and the questions behind them

The operator-facing status for an ADR-bearing integration answers:

1. **Which immutable base and candidate are being judged?** Report the full
   base SHA, product SHA, assignment-sync SHA, result tree, and PR head SHA.
2. **What was assigned?** Report each stable slug, number, source blob, final
   blob, and final path in deterministic order.
3. **Why did it stop?** Use bounded reason codes such as `stale-base`,
   `mapping-mismatch`, `draft-remains`, `head-moved`, `gate-not-active`, or
   `history-incomplete`; do not infer an unobserved GitHub cause.
4. **Can this repository claim race freedom?** Report the live ruleset id,
   enforcement, strictness, required context, integration id, and bypass count.
5. **Was a previous mapping superseded?** Report the old and new sync SHAs and
   bases without calling the old mapping part of the final tree.

These belong in structured controller receipts and GitHub check output. Routine
success needs one concise summary; the full object inventory remains in the
receipt. No secret, installation token, author email, or key material is logged.

## 9. Boundaries, per capability

**Always:**

- keep draft references stable and numbers absent until the assignment sync;
- derive a contiguous batch from `max(exact base)+1`, never from gaps;
- verify full Git object types, ancestry, signatures, trailers, and exact bytes;
- keep the controller read-only over product files;
- run the base-owned validator on the exact PR head without executing candidate
  bytes;
- supersede and recompute after every base advance;
- keep root and Hexaemeron suites green, plus focused Hypomnema, Fiat,
  workflow, stale-base, signature, and non-vacuity tests;
- run Imprimatur on prose, Phylax on external-input code, Ephoros on unattended
  status behavior, Hypomnema on records and pointers, the audit-synopsis check,
  Promise Machine checks, Horos boundary check, and `git diff --check`; and
- use symbolic `next-generation-after-integration-base` runbook relations for
  both changed skill ledgers instead of early literal versions.

**Ask first:**

- create, change, activate, or delete a GitHub ruleset;
- add or remove a required context, bypass actor, review rule, or merge method;
- create the canary pull request or publish any branch, status, comment, issue,
  or PR;
- change workflow permissions or GitHub App installation scope;
- add a dependency or external allocator; and
- expand the feature to another repository or document namespace.

**Never:**

- claim that `evaluate` blocks a merge;
- treat an API reread, local ref, PR number, or wall-clock instant as a lock;
- fill ADR-026, ADR-027, ADR-059, or any later hole;
- rewrite historical decision records or frozen references to adopt the slug
  form;
- permit a draft or duplicate number in the final `main` tree;
- execute candidate code, hooks, aliases, or Git configuration in the
  privileged validator;
- allow `hexctl` to edit, commit, push, merge, or change GitHub policy; or
- waive a stale base, moved head, inactive production gate, signature failure,
  or malformed assignment report.

## 10. The budget, or its absence

There is no runtime performance claim. The survey base contains 57 numbered
decision files, and the implementation bounds one batch at 32 drafts and one
record at the existing 1 MiB read ceiling. A single bounded Git walk and one
deterministic transform are sufficient. No cache is added.

Correctness budgets are fixed instead:

- full 40-hex Git object ids in receipts;
- 96 ASCII bytes per slug;
- 32 drafts per assignment;
- one exact H1 substitution per draft;
- zero candidate programs executed by the base-owned workflow;
- zero drafts and zero duplicate numbers in a candidate admitted to `main`;
  and
- existing Fiat object, source-byte, path, and supersession ceilings unchanged.

If implementation measurements show the check threatens the existing hosted
workflow budget, Metron must record a baseline and repeat the same command after
one change. No result is kept or rejected on speed in this packet.

## 11. The fail-closed posture

The assignment operation refuses before tree or controller state mutation when
the base or product object is absent, shallow, replaced, wrong-typed, no longer
current, or outside the expected ancestry. It also refuses malformed paths,
ambiguous slugs, duplicate mappings, an exhausted three-digit namespace,
unbounded input, unexpected byte changes, an unsigned commit, trailer/report
disagreement, a dirty worktree, a moved PR head, or a draft left in the final
tree.

`done sync-run` records no decision-assignment receipt until the canonical
report replays from immutable objects and the repository remains unchanged
during evidence collection. Recovery either resumes the same pending evidence
or discards it before retry; it never guesses a mapping from partial state.
Supersession is append-only in controller evidence and replacement-only in the
active Git ancestry.

The hosted validator reports failure when it cannot read the event base/head,
fetch complete objects, verify the assignment, or write the exact-head status.
Absence of a status is not success. Before external activation, the runbook and
PR body must say that production enforcement is absent. After activation, a
live ruleset query is part of the completion evidence.

For each implementation fix, the Warden runs the configured Elenchus command:

```text
python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
```

The report format is `unittest-json-v1`; the runbook gives each round a private
path under `tmp/elenchus/`. A fix is guarded only when the relevant regression
fails against the parent without the fix and passes with it. The two-candidate
stale-base mutation is mandatory. A production claim additionally needs the
separately authorised live canary; no local mutation substitutes for it.

## 12. Decisions and their homes

| Decision or evidence | One durable home | Rule |
| --- | --- | --- |
| Stable `adr/<slug>` identity, draft directory, final filename, and H1 transform | `plugins/hexaemeron/skills/hypomnema/SKILL.md` and its next generation ledger row | Hypomnema owns record placement and reference interpretation. |
| Deterministic allocator and record validator | Hypomnema's bounded script plus its focused fixtures | The algorithm travels with the decision-record contract rather than a repository-only test. |
| Integration assignment, report schema, sync supersession, and receipt | `plugins/hexaemeron/skills/fiat/SKILL.md`, `hexctl.py`, and Fiat's next generation ledger row | Fiat owns the signed integration transition but does not mutate product files. |
| Repository invariant compatibility and legacy numeric behavior | `tests/test_decision_records.py` | Existing records and comments remain covered. |
| Base-owned exact-head validation | `.github/workflows/adr-assignments.yml` and base-owned workflow tests | Candidate code is data only. |
| Live required context, strictness, enforcement, and bypass set | GitHub ruleset `21830871` | This is external state and changes only under separate authority. |
| Chosen design and rejected options | `docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md`, assigned by this mechanism at integration | One cross-cutting ADR, no duplicate skill-ledger decision. |
| Study and executable steps | `docs/adr-merge-assignment/study.md` and `docs/adr-merge-assignment/runbook.md` | The tracked copies preserve the receipted design and exact commands. |
| Per-run mapping and supersession evidence | `.hexaemeron` state, ledger, and canonical assignment report | Controller evidence is not a second policy document. |
| External activation evidence | Authorised canary PR, exact Actions run/status, and ruleset API response | No repository commit is represented as proof of live enforcement. |

The runbook must use `next-generation-after-integration-base` rows for
Hypomnema and Fiat. It must stage the standing ADR as an unnumbered draft, then
exercise the allocator in the final active sync. If this bootstrap PR lands
before the status is required, its conclusion states that the local prototype
is complete while the production race-free criterion remains pending external
activation. That qualification survives into the PR body and final receipt.
