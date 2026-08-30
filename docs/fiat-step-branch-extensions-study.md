# Study: honest step-branch extensions after push receipts

Issue: [wildcat-finance/skills#923](https://github.com/wildcat-finance/skills/issues/923)<br>
Topic: `honest step branch extensions after push receipts`<br>
Starting ref: `main` at `7e97b5195d5b0e43146b4200f26cd41b89003413`<br>
Study input state SHA-256: `0fc32c97385a2dc25557cc021186b98f666aa69ee95539546fac231cd26f73bd`

## Assumptions

Assuming, unless corrected:

1. This is an ordinary generation change to Fiat. It does not consume or
   alter the held `state-shape-validation` frontier job, issue #363. A derived
   runbook should declare `fiat |
   plugins/hexaemeron/skills/fiat/EVOLUTION.md |
   next-generation-after-integration-base` rather than pinning the version
   that happens to follow the current integration base.
2. A post-push step branch is eligible to continue only when the commit named
   by its push receipt is an ancestor of the branch's current remote tip.
   Ancestry establishes topology only. The existing merge-time
   `effective_push` repair remains responsible for the complete current
   range's local signatures, provenance trailers, GitHub verification, author
   and committer attribution.
3. The ancestry decision does not fetch. The expected extension was made in a
   checkout that already holds its commits. If the local native object graph
   cannot answer the relation, the result is unknown and integration refuses.
4. The issue-904 history is incident evidence and a proving fixture, not an
   instruction to alter that completed run's ledger, branches, pull requests,
   or issue.
5. The earlier halted Fiat #923 run,
   `fiat/923-allow-honest-step-branch-extensions-after-pu`, is prior work, not
   current controller evidence. Its study and runbook may be carried forward
   only where current-base reads reproduce their claims. None of its receipts
   or commits is imported into this fresh append-only run.
6. The topic is one capability. Topology classification and its evidence guard
   cannot ship independently, so one implementation step may own both after a
   first step commits the accepted study and runbook.

## 1. Problem statement

Fiat records the exact head of every step branch when `done push` receipts it.
During integration, `refuse_rewritten_stack` reads each still-waiting branch's
remote tip and compares it with that recorded head. Once a legacy abbreviated
head is resolved, every inequality is currently called a rewrite and attributed
to GitHub's native stack flow.

That conclusion is stronger than the evidence. A branch can move forward by
adding signed commits on top of the receipted head. The issue-904 run did so
after Step 1 needed a boundary-rescan repair. The repair commit was propagated
through Steps 2 and 3, so all three remote tips moved while every old head
remained in the new history. `done merge-step` nevertheless refused the stack,
and `done push` cannot re-receipt a branch after the run enters `integrate`.
The delivery halted and was finished by hand.

The user is a Fiat contributor bringing a signed step stack down in controller
order after a legitimate post-push repair. They need the controller to
distinguish “the receipted commit remains in this history” from “this branch no
longer contains the receipted commit,” without relaxing signature, trailer,
attribution, pull-request, merge-order, or final-integration gates.

A working prototype has four explicit outcomes:

- an unchanged full head passes with no additional relation call;
- a strict descendant passes the waiting-stack topology guard, then earns or
  refuses complete current-range evidence when that step is receipted;
- a tip that does not contain the recorded head refuses before another
  controller receipt; and
- an absent object, unreadable repository, timeout, or unexpected Git status
  refuses as unknown without claiming a rewrite mechanism.

The proving demo is a real Git fixture in
`plugins/hexaemeron/tests/test_step_branch_extensions.py`. It constructs
`P -> E`, records `P` as the push head, exposes `E` as a waiting branch tip,
shows that `next` still returns the ordered merge directive, then advances that
step through `done merge-step`. The merge receipt must contain a repaired
`effective_push` for the exact `pr_base..E` range, while the original push
receipt remains byte-for-byte unchanged. Sibling cases replace `E` with an
unrelated commit and an unavailable commit to prove the two refusal paths.

### Testable success criteria

| ID | Criterion | Command or demo path |
| --- | --- | --- |
| SC-1 | Equal full heads pass without invoking an ancestry subprocess. | `python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_step_branch_extensions.py' -v` |
| SC-2 | A strict descendant of every moved waiting head passes both the `next` and `done merge-step` waiting-stack checks in controller order. | The real `P -> E` cases under the SC-1 command. |
| SC-3 | Descendant topology never substitutes for evidence: the extended current step is checked over the full exact range, its merge receipt records `effective_push.repaired: true`, and its old push receipt is unchanged. | The end-to-end fixture plus the existing merge-time repair cases in `plugins/hexaemeron/tests/test_hexctl.py`. |
| SC-4 | A non-ancestor refuses at `next` and `done merge-step`, names the branch and both exact commits, does not allege an unobserved GitHub action, and leaves state and ledger bytes unchanged. | The unrelated-history cases under SC-1. |
| SC-5 | Git status 0 means ancestor, status 1 means non-ancestor, and every other outcome refuses as undetermined. | Focused helper tests for 0, 1, startup failure, timeout, cap, missing object, and unexpected status. |
| SC-6 | Legacy abbreviated receipts resolve before comparison; a resolved descendant passes, a resolved non-ancestor refuses, and an unresolvable receipt remains unreadable. | Extend `plugins/hexaemeron/tests/test_push_receipt_identity.py`; run `python3 plugins/hexaemeron/tests/test_push_receipt_identity.py -v`. |
| SC-7 | Current and already-merged steps remain outside the waiting scan; exact PR head/base, stack order, and unreceipted run-branch movement remain unchanged. | Focused skip cases and `python3 plugins/hexaemeron/tests/test_stack_topology.py -v`. |
| SC-8 | Native commit identity governs the relation: replacement refs and inherited `GIT_*` state cannot manufacture ancestry, fixed argv uses `--no-replace-objects`, no shell runs, and bounded failures refuse. | Real repository replacement-ref and hostile-environment cases under SC-1. |
| SC-9 | The three issue-904 receipted heads are ancestors of their observed tips and each named commit still reports valid local and GitHub verification. | The exact `merge-base`, `verify-commit`, and REST reads recorded in section 2. |
| SC-10 | Fiat's current v5.38.1 author/publisher split remains intact: any repaired range re-derives both author and committer records, and no descendant check selects a signer, committer, or publisher. | Existing attribution and publisher-separation tests plus the repaired-range assertions under SC-1. |
| SC-11 | The focused guard is red on the unfixed parent and green on the implementation commit through the source-bound Elenchus report. | `python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref HEAD --test-command "python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_step_branch_extensions.py" --report-format unittest-json-v1 --report-file .elenchus/fiat-923-step-2.json --require-guard`. |
| SC-12 | The focused modules, complete Hexaemeron suite, root suite, checked runner, portable runtime, Promise Machine, prose, evolution, and Horos gates all pass with non-zero test discovery. | `python3 plugins/hexaemeron/tests/run_tests.py`; `python3 -m unittest discover -s tests`; `python3 scripts/run_checks.py`; and the changed-surface checks selected by the runbook. |
| SC-13 | Shipped guidance distinguishes descendant, non-ancestor, and unknown relations, preserves ADR-021's genuine-rewrite recovery, and records the generation without changing the held frontier. | Hypomnema, Imprimatur, Brevitas, version, Promise Machine, portable-copy, and link checks named in the runbook. |

Study readiness authorises runbook derivation only. It does not establish an
implementation, passing test, audit clearance, signature, publication, or
delivery receipt.

## 2. Prior art

### Current repository behaviour

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` holds the relevant surfaces.
`refuse_rewritten_stack`, at the current starting tree's lines 6928-6996, skips
the current and already-merged steps, reads the exact remote tip, resolves an
unequal abbreviated legacy receipt, and treats every remaining inequality as a
rewrite. Both `next` and `done merge-step` call it, so preview and receipt must
share one classification.

`done_merge_step`, currently lines 6999-7088, already owns the evidence an
extended current branch needs. It requires the pull request head to equal the
remote branch tip. If the push receipt's local and GitHub commit lists are no
longer current at that tip, it verifies the complete exact range from the
recorded PR base, re-derives GitHub author and committer attribution, and stores
a repaired `effective_push` in the merge receipt. It does not edit the push
receipt.

`commit_is_ancestor`, currently lines 9604-9623, already distinguishes Git's
documented status 0, status 1, and every other status. Its existing callers are
final authorship checks. The new waiting-stack use has a hostile repository
boundary, so it must combine that three-way result with the native-object
sandbox already used by `_native_relation_git`: no replacement objects, no
inherited `GIT_*` substitution, no lazy fetch, no prompt, fixed argv, timeout,
and output cap.

The last two merged pull requests that changed this merge-step subject were
read from GitHub again on 2026-08-30:

1. [PR #813, “Compare push-receipt commit identities by resolution, not by string”](https://github.com/wildcat-finance/skills/pull/813),
   merged at `9e25b995bf4be01919559596d2af2ff65ba896a4`. It made new
   push receipts store resolved commit identities and made integration resolve
   older abbreviated receipts before comparison. This study retains its
   compatibility path and the equal full-SHA no-call path. Its carried
   documentation ambiguity was closed by
   [PR #853](https://github.com/wildcat-finance/skills/pull/853), so it is not
   reopened here.
2. [PR #602, “Bind a step merge to the pull request the directive names”](https://github.com/wildcat-finance/skills/pull/602),
   merged at `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`. It bound the
   merge receipt to the exact pull request, introduced unreceipted run-branch
   movement checks, and emitted the exact merge command. Its named retarget
   drift remains outside this topic: a waiting PR whose base changes is still
   detected at its own receipt rather than preflighted for every directive.
   Preventing a person from clicking or merging the wrong PR, and repairing a
   run branch after that happens, also remain outside this change.

[PR #593](https://github.com/wildcat-finance/skills/pull/593) is the original
incident line. Its manual finish exposed the wrong-merge gap later fixed by PR
#602, and commit `b934f9ba9502f083ce049ee6a4dd81bb1b2a1088` added the
waiting-tip equality refusal. [ADR-021](../docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md)
correctly preserves original signed commits when GitHub actually rewrites a
stack and rejects importing GitHub's web-flow key. Only its claim that every
unequal waiting tip proves a rewrite needs narrowing; its genuine-rewrite
landing rule remains in force.

[PR #922](https://github.com/wildcat-finance/skills/pull/922), merged for issue
#904, did not change this guard. Its `## Carried forward` section supplies the
live incident: a signed repair extended Step 1 and was merged forward through
Steps 2 and 3; all three tips moved, and Fiat halted because equality called
them rewrites. Its router-specific open work remains with issue #904: tree
binding for recorded grading blocks, refusal-reason semantics, rerun
repeatability, the 38-context cost, and ADR-number collision are not adopted by
this study.

### Recomputed incident evidence

The current starting tree contains all six named commits. Fresh local and REST
checks on 2026-08-30 produced:

| Step | Receipted head | Observed tip | Native ancestry | GitHub result for both commits |
| --- | --- | --- | --- | --- |
| 1 | `bf54296d96a7cc937757e2afaf467aeef8ff1f2b` | `a8af2b0fa87e3e964157f7d3c9f3d39439d3bc31` | exit 0; one added boundary-rescan commit | `verified: true`, `reason: valid` |
| 2 | `f01f476e15e0b9a33332d644c35413d47a9fbe8b` | `e13aaaa65e5cdd7dca052cfd7edd9cbc6f43a9d6` | exit 0; the repair plus one forward merge | `verified: true`, `reason: valid` |
| 3 | `c1171d9a5305b3e363a6a725139ceb54bff64422` | `133b39e467d087f22c6eee2c78fd20816a75cce1` | exit 0; both lower repairs plus one forward merge | `verified: true`, `reason: valid` |

Local `git verify-commit` reported `G` for the added tips. The REST commit
records reported author and committer `laurenceday` and valid verification for
all six exact commits. Those observations establish only these histories; they
do not prove that every future descendant is signed or authorised.

### Adjacent publication change, kept separate

The starting ref already carries Fiat v5.38.1 through commit
`c51565a555e49f1b37e207ebf499f5f1d5d7e2a5` and
[ADR-052](../docs/decisions/ADR-052-separate-governed-authorship-from-publication.md).
That generation separates Shoggoth authorship from an explicitly authorised
human committer, signer, and repository account, and records author and
committer separately. It repaired the publication boundary exposed by issues
[#903](https://github.com/wildcat-finance/skills/issues/903) and
[#906](https://github.com/wildcat-finance/skills/issues/906). It did not change
waiting-tip equality or classify descendants.

This distinction corrects one stale sentence in the earlier halted #923 run.
That run's halt receipt attributed GitHub's rejection to an “unregistered
Shoggoth signing key.” The later three-way test in issue #906 held author,
trees, and pusher constant and changed committer identity; only the human
committer address passed. The old halt sentence remains historical controller
evidence and is not rewritten, but its causal reading is refused here. This
run neither reopens publication policy nor changes ADR-052.

### Earlier Fiat #923 work

The preserved run
`fiat/923-allow-honest-step-branch-extensions-after-pu` produced a receipted
study at SHA-256
`2562dae84b2388e48b5bc912e67508ef0453badfa2e548473cf466cd7dccc0ab`, a
receipted amended runbook at SHA-256
`7bf3b9f7c3e69364f45e609c09b47e3d4445fef70e06a87d0d7901b218a4e0ef`,
and a clean documentation-only Step 1 audit. It halted before a Step 1 push or
pull request because its already-receipted commit could not be rewritten into
the newly established publication shape. The run is preserved intact.

This recovery carries forward its ancestry-versus-evidence design, issue-904
fixture, risk ids, and two-step decomposition because each was re-read against
the current base. It refuses its old starting SHA, concrete controller version,
publication-cause sentence, receipts, and local Step 1 commit. The current run
must re-receipt its own current-base artefacts and build from `7e97b519...`.

### Audit records

The whole-set synopsis command ran from the exact starting tree and exited 0:

```text
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

That verified every committed synopsis before any was used. The in-scope set
is:

- `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.synopsis.md`
  binds source SHA-256
  `ba74d5c959d0d06afc0e18ede1770d9b779cfb25f039ed375e6fa4b9a2e4801e`.
  Its nine legacy sections omit audit schema, Covered, Not checked, and
  Elenchus verdict; those fields remain unknown. Its integration lead says the
  wrong-PR merge was unrecoverable and filed separately. It contains no
  descendant-classification approval.
- `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.synopsis.md`
  binds source SHA-256
  `ef8b9ccc14580841ba8aff9613a3f6ffd6e40085c35b49bb54ae571dc648125c`.
  Four rounds report no findings. The same four legacy fields remain unknown.
  Its Step 3 retarget-drift lead was not pursued and remains a named non-goal.
- `audit/rounds/fiat-904-grade-the-router-corpus-from-a-driver-rather.synopsis.md`
  binds source SHA-256
  `665a08ed14c2432ae14fbbea0199408e487fee1965badb81355f11eb6e27cd88`.
  Five v2 rounds retain every Covered and Not checked disposition. Finding
  `S1-R1-01` (manifest-last ordering) and `S2-R1-01` (duplicate answer ids)
  were fixed and guarded; the other rounds found none. The record explicitly
  did not check controller integration or post-push movement, so it is incident
  context, not approval of this design.
- The verified root `audit/AUDIT_SYNOPSIS.md` binds source SHA-256
  `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`.
  Its “Fiat merged attribution” legacy view leaves schema, Covered, Not
  checked, and Elenchus verdict unknown, so the authoritative source passages
  at `audit/AUDIT.md:11649` and `audit/AUDIT.md:11728` were read directly.
  Step 2 findings `S2-R1-01` and `S2-R1-02` were fixed; its lead required a
  moved current branch to re-derive attribution beside its verified range.
  Step 3 closed that lead and fixed `S3-R1-01` and `S3-R1-02`, including stale
  repaired attribution and merge-carrier selection. This is the existing
  `effective_push` evidence path this design reuses.
- The earlier #923 Step 1 source record, outside the current Git tree, was read
  directly at its preserved run path. It records audit schema v2, all fifteen
  original risk dispositions, a null Elenchus verdict, no finding, no lead, and
  explicitly leaves Step 2 controller behavior and all publication work
  unchecked. Its source SHA-256 is
  `7104e2f447115f2dd16c0af96a5c0cb6ac57184d944001515196e960e8f19775`.

Searches over the verified synopsis set found no other record directly covering
waiting-step descendant classification. Unrelated controller audits are not
promoted into evidence for this decision.

### Organisation and external prior art

A fresh GitHub organisation code search for `refuse_rewritten_stack` and
`effective_push` found only this repository and the generated
`wildcat-finance/skills-marketplace` distribution mirror. The mirror is not an
independent implementation, so no separate organisation precedent was found.

Outside the organisation, Git documents
[`merge-base --is-ancestor`](https://git-scm.com/docs/git-merge-base) as the
commit relation primitive: 0 is ancestor, 1 is non-ancestor, and another status
is an error. GitHub's
[`stacked pull request` documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-multiple-branches/about-stacked-pull-requests)
describes its distinct server-managed stack behavior. GitHub's
[`commit REST schema`](https://docs.github.com/en/rest/commits/commits)
documents the later `verification.verified` and `reason` fields. Topology and
signature verification are separate facts in both the local design and the
upstream primitives.

## 3. Constraints and non-goals

### Constraints

- The exact starting ref is `main` at
  `7e97b5195d5b0e43146b4200f26cd41b89003413`. The run worktree was clean,
  its run branch and `origin/main` both resolved to that commit, and the current
  head includes PR #929's unrelated dead-code baseline.
- The checked toolchain is Python 3.14.6 (`.python-version` and the running
  interpreter), `requires-python ==3.14.*`, Git 2.50.1 (Apple Git-155), and
  GitHub CLI 2.96.0. The implementation stays in standard-library Python and
  existing Git/GitHub commands; no dependency or lockfile change is justified.
- State and ledger evidence are append-only. A push receipt is never edited.
  Newly earned current-range evidence belongs only in the merge receipt's
  `effective_push`.
- Equality remains the fast path. An ancestry subprocess runs only after two
  exact full commit identities differ.
- Relation inputs are the resolved receipt head and exact 40-hex remote tip.
  Git uses fixed argv, no shell, no replacement objects, a scrubbed Git
  environment, no lazy fetch or prompt, and the existing timeout/output caps.
  Status 0, status 1, and tool failure remain three distinct outcomes.
- Allowing a descendant cannot relax `verify_local_range`, exact trailers,
  GitHub valid verification, author/committer attribution, PR head/base,
  merge-step order, unreceipted run-branch movement, or final integration.
- Read-only `next` and mutating `done merge-step` classify the same waiting
  stack. Every mutation-path refusal occurs before state or ledger write.
- Exact issue-904 commits are historical evidence. Tests also construct an
  independent graph so they do not rely on those objects remaining reachable.
- Fiat v5.38.1's authorship/publication contract is an entry invariant. This
  generation may consume its attribution reader but may not change publisher
  authority, identities, address digests, or GitHub account routing.

### Non-goals

- No `done extend-push`, integrate-phase `done push`, re-receipt command,
  receipt or state schema, ledger rewrite, checkpoint migration, or historical
  run migration.
- No automatic fetch, remote object import, new GitHub endpoint, new host,
  credential, signer, publisher, or agent authority. A remote descendant absent
  locally refuses as unknown.
- No acceptance of a rebase, reset, cherry-pick, squash, force-push, or other
  tip that no longer contains the receipted head, even if its tree, author,
  trailers, or GitHub badge appear equivalent.
- No change to ADR-021's genuine-rewrite recovery and no trust in GitHub's
  web-flow key as a local signer.
- No repair for a wrong-PR merge, retarget drift, premature branch deletion,
  unreceipted run-branch movement, or an external merge already performed.
- No change to current-step skipping. Current-step movement still earns or
  refuses its evidence through merge-time repair.
- No rewrite or resumption of the earlier #923 run; no claim about how many
  other historical runs were affected; no closure of PR #922's router work.
- No change to ADR-052, issue #893's authority gate, the flagged-account
  diagnosis, commit authorship, committer selection, or PR publisher route.
- No CI/workflow, Solidity, storage layout, ABI, deployment, financial action,
  persistent telemetry, alert, or performance optimisation.

## 4. Design options

### Option A: classify unequal waiting tips by ancestry

Keep equality as the no-call pass. After legacy receipt resolution, ask whether
the recorded head is an ancestor of the exact remote tip. A yes admits topology
only. A no refuses because the receipted history is absent. An unanswered call
refuses as unknown. When the step becomes current, the existing exact-range
repair earns and records signatures, verification, author, and committer
evidence.

Trade: this adds at most one bounded local graph query per unequal waiting
branch, and the durable evidence arrives later at the existing merge-receipt
boundary. A current step can therefore be merged into the run branch before a
bad extension is refused by its receipt. The base remains untouched and Fiat
records no false success, but manual repair of the run branch may be required.

### Option B: add an integrate-phase re-receipt

Add `done extend-push`, or permit `done push` during integration, to verify and
append a new push record before another merge directive.

Trade: this adds a directive, state and receipt shapes, compatibility,
recovery, and operator ceremony for evidence that `effective_push` already
records. Two current-head records could disagree, and the issue does not need
the larger interface.

### Option C: preflight every effective range from `next`

Before emitting each merge directive, rerun local and GitHub verification over
every changed waiting range but keep the durable record in the later receipt.

Trade: it duplicates local and REST work without a receipt, then repeats it
after the external merge because the branch may change between preview and
receipt. It increases network failure surface and still does not close the
race.

### Option D: retain equality and fix only the wording

Keep refusing every moved branch but stop asserting that GitHub caused the
movement.

Trade: this removes the diagnostic overclaim but leaves the liveness failure.
A signed strict descendant still has no controller path, so it does not meet
the prototype definition.

### Choice

Choose Option A. It is the cheapest design to comprehend that asks the missing
question with Git's native relation and reuses the already-shipped
`effective_push` evidence path. Its trade is explicit: ancestry admits topology
before signatures and attribution are durably accepted, so merge-time repair
must remain mandatory and fail closed. Option B adds a second evidence model;
Option C repeats unreceipted work; Option D leaves issue #923 unresolved.

## 5. Risk register seed

```risk-register
descendant-is-not-verification | waiting branch topology versus signature, trailer, author, and committer evidence | status 0 admits topology only; the current step still owes full-range local and GitHub checks and a repaired effective-push receipt
nonancestor-accepted | receipted head versus current remote tip | construct unrelated native histories and require next and done-merge-step refusal before controller mutation
ancestry-unanswered | local object availability and Git status interpretation | accept only status 0 as ancestor and status 1 as non-ancestor; every other outcome is unknown and refuses
replacement-ref-substitution | native commit graph versus git replacement refs and inherited Git environment | scrub inherited GIT variables, disable lazy fetch and replacement objects, and prove a hostile replacement cannot manufacture acceptance
legacy-short-head | abbreviated historical receipt versus exact remote identity | resolve once before relation testing and cover descendant, non-ancestor, and unresolvable outcomes
post-merge-verification-window | external current-step merge versus the later controller receipt | preserve exact PR-head and remote-tip rereads, refuse failed effective ranges without a receipt, and state that the run branch may need manual repair
remote-tip-race | live branch and PR observations around an external merge | require the inspected PR head to equal the exact remote tip and never treat an earlier descendant observation as current evidence
state-mutation-on-refusal | next and done-merge-step controller boundary | compare state and ledger bytes across non-ancestor, unknown, local-verification, GitHub-verification, and attribution refusals
diagnostic-overclaim | observed relation versus claimed cause | report equal, descendant, non-ancestor, or unknown facts and name no GitHub mechanism without separate evidence
genuine-rewrite-recovery-regression | ADR-021 signed-stack boundary | keep non-ancestor refusal, original-commit landing guidance, and the prohibition on trusting the web-flow signer
effective-range-staleness | old push lists versus current pr-base-to-tip range | require repaired local and GitHub lists to be equal, non-empty, full-SHA, end at the current head, and live only in the merge receipt
current-step-scope-drift | waiting guard versus current and merged branches | preserve skip semantics and prove only still-waiting steps receive descendant classification
run-branch-topology-regression | waiting step movement versus separate unreceipted run-branch movement | run stack-topology tests and retain PR-602 wrong-merge and retarget behavior
publisher-separation-regression | repaired effective range versus Fiat v5.38.1 attribution | re-derive author and committer together, preserve address-digest and host refusals, and add no signer or publisher selection to ancestry
prior-run-cause-drift | halted #923 receipt text versus current ADR-052 evidence | preserve the historical receipt without repeating its key-cause claim or widening this generation into publication policy
performance-amplification | one graph query per unequal waiting branch | keep equality as the no-call path, keep subprocess bounds, and make no latency claim without a Metron baseline
historical-overclaim | one observed issue-904 run versus all Fiat history | cite only the three recomputed relations and leave the population of other affected runs unknown
```

## 6. Glossary seeds

- `Push receipt head`: the resolved commit recorded when `done push` accepted a
  step branch. It is immutable evidence about that push event.
- `Remote tip`: the one full SHA returned for the exact
  `refs/heads/<step-branch>` on `origin` by the bounded ref reader.
- `Unchanged`: receipt head and remote tip are the same commit. This is the
  zero-additional-relation-call path.
- `Strict descendant / honest extension candidate`: a different tip for which
  the receipt head is an ancestor. “Candidate” means topology has passed while
  signatures, trailers, attribution, and authority remain unestablished.
- `Non-ancestor movement`: a tip whose native history does not contain the
  receipted head. A rebase, reset, force-push, cherry-pick, squash, or unrelated
  replacement may cause it; topology alone does not identify which.
- `Unknown ancestry`: Git supplied neither its documented yes nor no answer,
  including absent objects, timeout, unreadable history, cap, or tool failure.
- `Waiting step`: a pushed step whose number is neither current nor already
  merged. Only these branches enter `refuse_rewritten_stack`.
- `Current step`: the lowest unmerged step named by the integrate directive.
  It earns current branch evidence at `done merge-step`.
- `Effective push`: the merge receipt's current local/GitHub verification and
  attribution record. It may reuse current push evidence or record a repaired
  full range; it never changes the push receipt.
- `Genuine rewritten stack`: a waiting stack whose remote history no longer
  contains at least one receipted head. ADR-021 owns its recovery.
- `Topology admission`: permission to continue ordered integration checks. It
  is not a signature, audit, merge, publication, or delivery receipt.
- `Author/publisher split`: Fiat v5.38.1's separate records for who contributed
  the work and who committed, signed, and published it. It is an invariant of
  this study, not its subject.

## 7. Sources

### Governing and local sources

- [Issue #923](https://github.com/wildcat-finance/skills/issues/923), live body,
  renumbering comment, state, and exact incident table read 2026-08-30.
- [PR #922](https://github.com/wildcat-finance/skills/pull/922), especially its
  `## Carried forward` issue-904 record.
- [PR #813](https://github.com/wildcat-finance/skills/pull/813) and
  [PR #853](https://github.com/wildcat-finance/skills/pull/853), resolved push
  identities and their full-SHA documentation.
- [PR #602](https://github.com/wildcat-finance/skills/pull/602),
  `plugins/hexaemeron/docs/fiat-bound-step-merge/study.md`, and
  `plugins/hexaemeron/tests/test_stack_topology.py`.
- [PR #593](https://github.com/wildcat-finance/skills/pull/593), commit
  `b934f9ba...`, and
  [ADR-021](../docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md).
- [Issues #903](https://github.com/wildcat-finance/skills/issues/903) and
  [#906](https://github.com/wildcat-finance/skills/issues/906), commit
  `c51565a5...`, and
  [ADR-052](../docs/decisions/ADR-052-separate-governed-authorship-from-publication.md),
  the adjacent publication fix kept outside this change.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, especially
  `refuse_rewritten_stack`, `done_merge_step`, `commit_is_ancestor`,
  `_native_relation_git`, `remote_branch_tip`, and `exact_commit_range` at the
  exact starting SHA.
- `plugins/hexaemeron/tests/test_push_receipt_identity.py`,
  `plugins/hexaemeron/tests/test_stack_topology.py`, and the existing
  merge-time repair/attribution cases in `test_hexctl.py`.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `EVOLUTION.md`,
  `references/push-discipline.md`, root `PROMISE_MACHINE.md`, Protasis, and the
  exact Surveyor packet.
- Preserved earlier run
  `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills-923/tmp/fiat/fiat-923-allow-honest-step-branch-extensions-after-pu`,
  read through its controller status plus exact study, runbook, and Step 1
  audit bytes; no receipt imported.

### Audit sources

- Verified `fiat-576`, `fiat-594`, and `fiat-904` synopses and the source
  digests recorded in section 2.
- Verified root `audit/AUDIT_SYNOPSIS.md` plus direct authoritative passages
  `audit/AUDIT.md:11649` and `audit/AUDIT.md:11728` for moved-head
  `effective_push` attribution.
- Direct preserved earlier-#923 Step 1 source record at SHA-256
  `7104e2f447115f2dd16c0af96a5c0cb6ac57184d944001515196e960e8f19775`.
- `audit_synopsis.py --check .`, zero exit on the exact starting tree.

### External authoritative sources

- Git, [`git merge-base --is-ancestor`](https://git-scm.com/docs/git-merge-base),
  for yes/no/error relation semantics.
- GitHub,
  [`About stacked pull requests`](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-multiple-branches/about-stacked-pull-requests),
  for the separate server stack behavior.
- GitHub,
  [`REST API endpoints for commits`](https://docs.github.com/en/rest/commits/commits),
  for later verification and attribution evidence.
- GitHub organisation code search on 2026-08-30 for
  `refuse_rewritten_stack` and `effective_push`, whose only hits were the
  source repository and its generated marketplace mirror.

## 8. Signals, and the questions behind them

No new persistent metric, trace, daemon, or alert is warranted. This is an
interactive bounded CLI check, not an unattended service. Existing diagnostics,
state, and receipts answer its operational questions. That is an explicit
no-new-telemetry answer under the
[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) contract.

| Operator question | Existing or changed signal | Boundary |
| --- | --- | --- |
| Is each waiting branch equal, a descendant, a non-ancestor, or unreadable? | `next` and `done merge-step` apply one closed classification and use exact step, branch, receipt head, and tip in refusals. | A passing descendant may stay quiet and proves no signature fact. |
| Why did integration stop? | Diagnostics distinguish “head is not an ancestor” from “ancestry could not be determined.” | They name no GitHub cause without separate evidence. |
| Did the descendant range earn complete evidence? | The later merge receipt's `effective_push.repaired`, `head`, commit lists, verification, author, and committer records. | The topology check itself emits no verified claim. |
| Did refusal alter controller evidence? | Byte-identical state and ledger assertions plus absence of a new ledger event. | This says nothing about an external merge already performed. |
| Which recovery applies? | Non-ancestor keeps ADR-021 recovery; unknown says to restore locally readable native objects and retry. | Existing signature, PR, and GitHub failures keep their own recovery. |

No secret, token, raw Git output, or unbounded value is added to diagnostics.
Warden must verify that each question has one evidence-bounded answer. An
Ephoros lint exit covers only its own parser rules, not this judgement.

## 9. Boundaries, per capability

This is an off-chain controller change, so the
[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) contract governs the
capability boundaries.

| Boundary | Input worth distrusting | Control and proof |
| --- | --- | --- |
| Controller state | receipt shape, `head_commit`, step number | Existing state-container checks and closed/full-SHA validation precede use; legacy abbreviation has one explicit resolution path; no state field is added. |
| Remote Git ref | `origin` answer for one named branch | Branch validation and fixed `ls-remote --refs origin refs/heads/<branch>` require one exact tab-separated full SHA under timeout and output cap. |
| Local commit graph | whether the receipt head reaches the tip | Fixed-argv native `merge-base --is-ancestor`, no shell, scrubbed `GIT_*`, no replacement object, no lazy fetch or prompt; only status 0/1 are answers. |
| Pull request and GitHub records | PR head/base/merge and commit verification payload | Existing bounded REST readers, exact PR head equals remote tip, `verified: true`, `reason: valid`, and checked attribution remain at the merge receipt. |
| Authorship and publication | author/committer records and publisher authority | Reuse v5.38.1's separate attribution containers; ancestry chooses no account, signer, email, or publisher and supplies no authority. |
| Controller mutation | an external merge occurs before receipt | All checks precede state/ledger commit. A refusal records nothing; the controller cannot roll back GitHub or the run branch, and that limit is explicit. |
| Diagnostic output | child stderr or attacker-shaped ref data | Child output is capped and not echoed; only validated branch names and full SHAs enter formatted diagnostics. |

The runbook must ask first before adding a dependency, fetch, endpoint,
environment-controlled relation, receipt/state field, signer/publisher route,
new authority, or write outside normal Fiat product paths. It must never build
a shell string from a ref, pass an unknown relation, treat a GitHub badge as a
local signature, expose a credential, or edit the ledger to recover.

## 10. The budget, or its absence

There is no performance budget and no performance claim. The observed defect is
wrong classification, not latency; the path is interactive and bounded. Under
the [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) contract, inventing a
threshold without a workload and baseline would establish nothing.

The structural cost bound is sufficient for this prototype: equal full SHAs
make no relation call; each unequal waiting branch makes one bounded local graph
query; no REST call or fetch is added. Focused tests record those call counts.
There is therefore no Metron command for this run. If measured latency later
becomes a problem, stop and create a separate Metron loop with the exact repo,
waiting-step count, cold/warm state, repetitions, aggregation, and before/after
command fixed before any speed-motivated edit.

## 11. The fail-closed posture

The controller admits only what the current boundary establishes:

- equal exact identities pass unchanged;
- status 0 admits topology and no signature claim;
- status 1 refuses because the remote history lacks the receipted head;
- every other status, absent object, unreadable branch, timeout, malformed
  value, PR mismatch, local signature/trailer failure, GitHub transport or
  verification failure, host-identity failure, or attribution failure refuses;
- a refusal appends no receipt and changes no state or ledger byte; and
- base integration remains unavailable until every ordinary merge-step and
  final promise succeeds.

Unknown is never converted to yes or no. Tree equality, author equality,
retained trailer text, or a GitHub badge never substitutes for reachability or
a valid local signature. No fetch hides missing evidence, no public key is
imported to make a check pass, and no stale push receipt is rewritten.

PR #922 preserves the concrete failure. Following the
[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) convention, Step 2
must reduce it to the smallest real `P -> E` graph, observe the focused guard
red on the unfixed parent, then green on the implementation. Its exact
source-bound runner is SC-11. A missing, stale, malformed, oversized, zero-test,
mixed infrastructure/assertion, timeout, or incomplete report is
`inconclusive`, not guarded.

Recovery is evidence-specific: make native objects readable and retry an
unknown; restore the original signed stack and follow ADR-021 for a
non-ancestor; repair and re-sign an invalid extension before retrying its
receipt; restore exact branch/PR topology for a live-ref mismatch. No recovery
rewrites controller history.

## 12. Decisions and their homes

The expensive-to-reverse decision is that a push receipt binds the continued
presence of one commit, not permanent equality with the branch tip. A strict
descendant may pass the waiting topology gate, while the complete current range
must still earn local and GitHub evidence in `effective_push`. Rejected designs
are a second re-receipt transition, unreceipted preflight verification, and
permanent equality refusal.

Under the
[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) placement rule, the
durable home is the new generation row in
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`. It records ancestry as the
topology distinction, later `effective_push` evidence as the trade, the
rejected options, issue/PR/commit links, and the unchanged issue-363 frontier.
The study and runbook are run artefacts, not the lasting decision record. The
runbook should use the relation in Assumption 1 so integration resolves the
actual next generation.

Existing homes need factual alignment rather than a competing record:

- ADR-021 continues to own genuine rewritten-stack landing and the refusal to
  trust GitHub's web-flow signer. Its equality sentence must narrow to
  non-ancestor movement without deleting the original decision.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md` owns operator
  guidance: descendants proceed to mandatory merge-time re-verification,
  non-ancestors keep ADR-021 recovery, and unknown stops.
- `plugins/hexaemeron/skills/fiat/SKILL.md` owns the runtime and Promise Machine
  boundary. Its integration evidence must name the current effective pushed
  range where needed and must not imply that an old receipt verifies new
  commits.
- `hexctl.py` owns the precise 0/1/error and topology-versus-evidence interface
  beside the code. The focused test module owns executable examples.
- ADR-052 remains the publication record and must not be edited into a
  descendant-topology decision. Its author/committer separation is preserved
  by tests and references only.
- Portable runtime copies, package manifests, marketplace records, Promise
  Machine coverage, and Horos are generated or checked consequences, not
  separate decision homes.

### Delivery boundaries for the derived runbook

**Always**

- Preserve full commit identities, equality's no-call path, Git's 0/1/error
  distinction, fixed argv, native no-replacement history, and subprocess caps.
- Keep topology admission separate from signature, GitHub, attribution, audit,
  and delivery evidence; reverify the exact current range at merge receipt.
- Leave push receipts immutable and put newly earned evidence only in
  `effective_push`.
- Keep v5.38.1 author/committer attribution and explicit publisher authority
  unchanged.
- Run focused red/green guards, identity and topology modules, complete
  Hexaemeron and root suites, `scripts/run_checks.py`, and every selected prose,
  version, Promise Machine, portable runtime, and Horos check.
- Carry or refuse by name the PR-602 retarget lead, PR-813/853 full-SHA work,
  ADR-021 recovery, PR-922 router work, ADR-052 publication boundary, and the
  earlier halted #923 run.

**Ask first**

- Add a dependency, command, endpoint, fetch, CI/workflow, persistent signal,
  receipt/state field, migration, signer/publisher route, authority, or write
  outside the runbook's paths.
- Accept tree or author equivalence, change when signatures are accepted, or
  alter genuine-rewrite recovery beyond the descendant distinction.
- Expand into retarget drift, wrong-PR recovery, historical-run repair,
  publication policy, router carryovers, or the held #363 frontier.

**Never**

- Accept a non-ancestor or unknown relation, call an unanswered query a
  rewrite, or claim GitHub caused movement without separate evidence.
- Treat ancestry, tree equality, retained trailers, author identity, or a
  GitHub badge as proof of a valid local signature or publication authority.
- Import GitHub's key, rewrite a push receipt or ledger, force-push a repair,
  reconstruct progress from chat, or describe an unrun or inconclusive check
  as green.
- Commit, push, merge, close, publish, deploy, or take a financial action
  without the distinct authority and receipt that owns it.
