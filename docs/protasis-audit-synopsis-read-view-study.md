# Study: read the audit synopsis rather than the whole log after signing-key rotation

## Assumptions

Assuming, unless corrected:

1. The controller packet is authoritative for this run. Its target is
   `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills-fiat-coordinator/tmp/fiat/fiat-369-read-audit-synopsis-resigned`,
   its base is `main`, and its output is `.hexaemeron/study.md` in that target.
2. The clean construction starts from
   `1efec4de762e3b30c1d677371643c0e5e12667ed`. The target branch and both local
   and remote `main` resolved to that commit before this study was written.
3. Commit `c67c39b39b0e031c4f51ef32317e442d58785480` and every descendant are
   publication-ineligible. Its signing subkey
   `B0E32A70FA436DAF4D0A98A7CDBB57E6289F5C1B` was revoked as compromised after
   the implementation receipt. A later descendant signed by another key does
   not remove that ancestor.
4. Fiat 5.26.1 has no receipt-preserving transition that replaces a receipted
   implementation commit after its signature becomes invalid. The halted
   controller ledger therefore remains evidence of the refusal, not state that
   this run can resume or copy.
5. The current valid replacement signing subkey is
   `A0CC410C7BA3DEFC032B3FAA2C9B298EB3D5E57A`. The clean implementation is
   rebuilt from the base and committed under that subkey. No merge, rebase,
   cherry-pick, or other history operation may introduce the ineligible commit
   or one of its descendants into the new ancestry.
6. Issue 369's product boundary is unchanged: Protasis instructions, its
   focused contract test, its generation ledger entry, committed study and
   runbook copies, and generated records changed by the required repository
   checks. The synopsis renderer, audit schema, Fiat controller and receipts,
   append-only audit sources, issue 453 gate, and Protasis held frontier remain
   outside it.
7. The halted study, product diff, controller ledger, and signed audit commits
   may inform this study. Their contents do not authorise publication and no
   old receipt is claimed by the clean run.

## 1. Problem, user, prototype, and demonstration

The user is the Surveyor preparing a clean Fiat delivery for issue 369.
Protasis currently directs the Surveyor to read relevant authoritative audit
sources. It does not say when the deterministic synopsis is a safe normal read
view, how to fall back when that view is absent or stale, or which evidence a
shorter read must retain. The append-only root source is already 14,079 lines,
while its checked synopsis is 425 lines.

The first run produced the requested product, but its implementation commit is
now signed by a revoked compromised subkey. `git verify-commit
c67c39b39b0e031c4f51ef32317e442d58785480` exits 1. The known descendants
`eddf475a8e40bbc8b91ecbb24c6b7e5216bae2af` and
`bdaa71cc90a5efd694e37e5e02b7dfe098898df8` each verify under the replacement
subkey, yet they still descend from `c67c39b...`. Publication of that entire
ancestry is refused. Fiat 5.26.1 cannot replace the receipted implementation
while keeping its receipt, so this run constructs the product again from the
original base.

A working prototype has all of these properties:

1. Protasis item 2 keeps every discovered audit source authoritative and makes
   its mapped synopsis the normal view only after
   `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check
   <target-root>` exits zero for the discovered set.
2. It names both mappings: `**/audit/AUDIT.md` to the sibling
   `AUDIT_SYNOPSIS.md`, and a direct `audit/rounds/<run>.md` child to
   `<run>.synopsis.md`. A root view is never an umbrella for per-run or plugin
   records.
3. A missing, stale, unsupported, or unavailable view sends the reader to the
   authoritative source. The study records the source and reason. If the
   source is unavailable too, readiness stops.
4. The study preserves every finding id and status, `Covered`, `Not checked`,
   `Elenchus verdict`, and `Leads not pursued`. A literal
   `[missing legacy field: ...]` remains unknown.
5. The pre-receipt checklist names every in-scope source, which view or source
   was actually read, and the currency or fallback evidence. It never says a
   raw source was read when only a synopsis was read.
6. Protasis advances from `4.7.0` to `4.8.0` on the generation axis while its
   `amendment-block-check` frontier, next job, status, revision, and digest stay
   byte-identical.
7. The product commit is a fresh descendant of the exact base, has no
   `c67c39b...` descendant in its history, and verifies under replacement
   subkey `A0CC410C7BA3DEFC032B3FAA2C9B298EB3D5E57A` before any push.
8. The focused guard is observed red on the base and green on the new tree.
   The finished tree passes the required root and Hexaemeron suites and the
   repository checks that cover every changed path.

The proving path is one implementation step. It rebuilds the previously
reviewed text and guard by reading the base and the old diff, not by importing
the old commits. It then runs the synopsis check, both Protasis checks, focused
red/green guard, required suites, Promise checks, required prose and tree
checks, signature verification, and the ancestry refusal. The demonstration
reads item 2 and the checklist from the finished tree and traces one legacy
pair and one per-run pair through the rule.

## 2. Prior art, audit record, and open work

### Repository and organisation

`docs/protasis-audit-record-source-study.md` and its runbook chose Protasis
item 2 and the pre-receipt checklist as the home for audit-source discovery.
This change extends that home rather than adding a thirteenth study section or
a manifest.

`plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py` already owns source
discovery, deterministic rendering, both path mappings, the line budget, and
committed-byte currency. The Fiat audit-loop reference and Hexaemeron README
already state that sources are authoritative and synopses are derived views.
Protasis is the missing consumer contract.

The last two merged pull requests that changed the subject are:

- Pull request 593, **Give each Fiat run its own audit log path**, merged on 24
  August 2026. It retained the legacy root record, gave each new run a separate
  source, and rejected a generated umbrella index. Carry that decision: the
  root synopsis is not an umbrella either. Its merge-command binding lead was
  filed separately and stays outside issue 369.
- Pull request 619, **Recover #429/#552 and publish Fiat 5.26.1**, merged on 25
  August 2026 at this study's base. It recovered the deterministic renderer,
  v1/v2 records, collision-free view paths, stale-plan refusal, and rollback
  after caught failures. Carry its hard-termination limit and its separately
  owned issues 557, 608, 453, 369, and 363.

### Halted issue-369 construction

The halted run is useful prior art but not publishable history:

- Its receipted study has SHA-256
  `8ae2db174eb667a1e2acb83ceb3150d06bd599bba92a9fcc0f016533792f3fa7`.
- `c67c39b39b0e031c4f51ef32317e442d58785480` changed the intended seven
  product paths and reported focused 89/89, root 396/396, and Hexaemeron
  1,168/1,168. Those checks show what the patch did at that time; they are not
  delivery receipts for this run.
- Its Warden record contains one finding. `S1-R1-01` found that the Horos
  `files_walked` count was generated before the two new tracked documents
  entered the index. `eddf475a8e40bbc8b91ecbb24c6b7e5216bae2af` fixed the
  generated count. The next construction therefore stages the complete
  tracked file set before the final Horos write and requires a clean repeat.
- The record's Elenchus verdict is `unguarded` because the generated-record
  fix changed no tests. Its stated guard is the exact Horos write followed by
  a clean diff. Preserve that negative space.
- `bdaa71cc90a5efd694e37e5e02b7dfe098898df8` records the round under the
  valid replacement subkey, but it is still a descendant of `c67c39b...` and
  remains publication-ineligible.
- The halted controller's final event says the old implementation now fails
  verification because the subkey was revoked as compromised, Fiat 5.26.1 has
  no receipt-preserving replacement transition, and issue 369 must restart.

The clean construction may reproduce the old patch's behaviour and use its
audit lesson. It must not merge, cherry-pick, rebase, push, or publish the old
commit chain. A fresh signature on a copied tree does not make the old receipt
current; the new run owes its own implementation and audit receipts.

### Current audit record

The base's repository-wide synopsis check exits zero for eleven source/view
pairs. For this subject, the relevant authoritative records and their checked
views establish:

- The root audit's Protasis discipline and audit-source findings were fixed in
  their recorded rounds. Historical missing-field markers remain unknown.
- The issue-429 source carries 29 imported v1 rounds and leaves downstream
  synopsis consumption to issue 369.
- The issue-429 recovery source records `S1-R1-01` and `S2-R1-01` as fixed and
  guarded, followed by clean rounds. Its cross-file hard-termination limit and
  issues 557, 608, 453, 369, and 363 remain visible.
- The per-run audit-path source records `S2-R1-01`, `S2-R1-02`, `S3-R1-01`,
  `S3-R1-02`, and `S4-R1-01` as fixed, with clean following rounds.
- The Hexaemeron plugin audit records `F-01` through `F-09` as fixed and
  `F-10` as an accepted hook escape hatch. Concurrent controller use and an
  unusual cross-filesystem replacement remain outside this reading change.

No current base audit record reviews the clean implementation because it does
not yet exist. The old issue-369 round supplies a concrete pitfall and no
approval of the new tree.

### Outside the repository

Git's commit-graph is relevant precedent for the source/view distinction: the
graph is supplemental acceleration data, while the object database remains
the source. `git commit-graph verify` checks that view against repository
objects. `git verify-commit` is the corresponding local interface used here to
check commit signatures. These are analogies and tools, not imported product
code.

### Open work

- Carry issue 453 after this one. It owns the known-failure inventory schema,
  injected failures, and production report gate.
- Carry issues 557, 608, and 363 under their existing owners.
- Preserve held frontier issue 497 exactly. It owns the
  `amendment-block-check` job.
- Treat issues 327 and 429 as satisfied dependencies.
- Refuse renderer, schema, controller, receipt-transition, audit-source,
  generated-manifest, CI, and held-frontier work here.

## 3. Constraints, non-goals, and authority

The exact entry is `main` at
`1efec4de762e3b30c1d677371643c0e5e12667ed` on branch
`fiat/369-read-audit-synopsis-resigned`. The observed toolchain is Python
3.14.6, Apple Git 2.50.1, stdlib unittest, and the repository's existing lint
and checker scripts. No dependency is added.

The source/view relation is asymmetric. An audit Markdown source is the
record. A synopsis is a deterministic read view whose header binds the source
SHA-256 and whose committed bytes must equal a fresh render. Only a zero exit
from the existing whole-set currency command establishes the view claim. If
that command fails, every in-scope read uses its source; Protasis must not
invent a per-source verifier.

The signature relation is also asymmetric. The old commit's content can be
read as prior evidence, but a revoked signature cannot authorise publication.
Later valid signatures do not repair an invalid ancestor. The new history
must start at the exact base, contain only fresh commits, verify locally under
the replacement subkey, and pass the existing provenance gates before any
push. No private key, revocation certificate, exported key material, or raw
signature bytes enter the study, repository, controller state, test output, or
command line.

The change is a Protasis generation from `protasis-v4.7.0` to
`protasis-v4.8.0`. It retains byte-for-byte:

- frontier status `open`;
- frontier revision `amendment-block-check`;
- current frontier and next-job text; and
- frontier digest
  `1014071026a149d38e7d79c222dfcfc25dd061d825fac9e7813a3a46b184cd29`.

The non-goals are changing Fiat to support key replacement, rehabilitating or
publishing the halted ancestry, changing the renderer or audit schema, adding
editing audit sources, changing CI, adding a dependency, doing Solidity work,
or changing issue 453 or 497.

Authority is concrete:

- **Always:** rebuild from the exact base; run the currency check before a
  synopsis read; report actual source/view use; preserve audit negative space;
  stage the complete tracked set before the final Horos write; run every
  required check; verify every new commit and its ancestry before push.
- **Ask first:** any renderer, schema, controller, receipt, CI, dependency,
  public-interface, storage, trust-boundary, or third-party target change; any
  need to publish an old descendant; any different signing key.
- **Never:** accept a stale view; infer a legacy field; claim unread bytes were
  read; copy an old receipt; merge, rebase, or cherry-pick the ineligible
  ancestry; alter the held frontier; expose key material; call the controller
  from Surveyor.

## 4. Designs and choice

### A. Rebuild the reviewed product from the exact base

Read the old patch and audit as prior evidence, reapply the intended product
changes by hand on the clean base, include the Horos ordering lesson, run fresh
guards and required checks, then create a new signed commit under the
replacement subkey.

Trade: repeated implementation costs more than retaining the old receipt, and
the new run owes a new audit. It gives the new history a valid root-to-tip
signature story and keeps issue 369's product boundary intact.

### B. Cherry-pick the old product and sign the new commit

A cherry-pick could create a new commit without making `c67c39b...` its Git
ancestor.

Trade: it still treats the publication-ineligible implementation as the
construction transition, carries its pre-audit generated-record ordering, and
does not meet the Creator's clean-rebuild direction. Reject it.

### C. Rebase, merge, or continue the halted run

Keep the old controller state and place a validly signed descendant above it.

Trade: the old implementation remains an ancestor and Fiat 5.26.1 still has no
receipt-preserving replacement transition. This is explicitly
publication-ineligible. Reject it.

### D. Add a Fiat key-replacement transition first

Change the controller so a revoked receipted implementation can be superseded
in place, then recover the old run.

Trade: this changes Fiat state, receipts, recovery semantics, and tests. It is
a separate product and delays a small Protasis change. Reject it from issue
369.

Choose A. It is the least complex design that satisfies both the product and
signature boundary. One implementation step still fits: the instruction,
focused guard, ledger generation, committed evidence copies, generated records,
fresh signature, and demonstration form one reviewable change.

## 5. Risk register

```risk-register
revoked-ancestry | c67c39b and every descendant | fresh head starts at 1efec4de, merge-base reports the old commit is not an ancestor, and no old commit is pushed or published
receipt-reuse | halted Fiat 5.26.1 state and the clean run | new study, implementation, audit, and publication receipts are required; old receipts are cited only as prior evidence
replacement-key-drift | configured primary key and active signing subkey | every new commit verifies locally and reports A0CC410C7BA3DEFC032B3FAA2C9B298EB3D5E57A before push
key-disclosure | signing diagnostics, study, logs, and argv | record public fingerprints and verifier status only; no private key, revocation certificate, or raw signature material enters the run
source-view-confusion | authoritative audit source and derived synopsis | item 2 states source authority and the study names the actual read mode
umbrella-omission | root, per-run, and plugin audit sources | discovery enumerates every in-scope pair and says the root view covers only its root source
stale-view | committed synopsis and source digest | a synopsis is used only after the whole-set currency command exits zero; otherwise the source is read
fallback-overclaim | direct-source fallback and study report | record the source path and reason, and never claim a source or view read that did not happen
legacy-gap-inference | literal missing-field markers | retain each marker as unknown rather than clean, checked, guarded, null, or not applicable
decision-loss | findings and audit negative space | preserve finding ids and status, Covered, Not checked, Elenchus verdict, and Leads not pursued
frontier-drift | Protasis evolution ledger | add only protasis-v4.8.0 as a generation and assert the held fields and digest remain exact
generated-record-order | tracked documents and Horos records | stage the complete tracked set before the final Horos write, rerun it, and require a clean diff
scope-creep | renderer, controller, audit sources, CI, and issue 453 | changed-path review refuses anything outside the declared issue-369 product and required generated records
```

## 6. Glossary

- **Authoritative audit source:** an append-only `AUDIT.md` or direct per-run
  Markdown log from which the audit view is derived.
- **Verified synopsis:** a mapped committed synopsis in a target where the
  current whole-repository currency command exited zero.
- **Read mode:** the verified synopsis or authoritative source actually read,
  reported without implying both.
- **Publication-ineligible ancestry:** a commit chain that this delivery must
  not push, merge, or publish because it contains the revoked-signature
  implementation commit.
- **Clean construction:** fresh changes made from the exact base without an
  old product commit in the ancestry or an old receipt standing in for new
  evidence.
- **Replacement signing subkey:** the current valid public signing identity
  `A0CC410C7BA3DEFC032B3FAA2C9B298EB3D5E57A` used for new commits.
- **Unknown legacy field:** a literal `[missing legacy field: ...]` marker that
  absence leaves unknown.

## 7. Sources and repeatable evidence

### Clean run and signing evidence

- `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl` in this target bind
  topic, branch, base, issue 369, Fiat `5.26.1`, and the study phase. The packet
  state SHA-256 is
  `6d04f2d4c1625578a242fdc0282bf969d4fa5074cf5069bcb67021392f5df357`.
- `git rev-parse HEAD main origin/main` returned
  `1efec4de762e3b30c1d677371643c0e5e12667ed` for all three.
- The halted run's `.hexaemeron/state.json` and ledger final event record the
  compromised-subkey refusal and absence of a Fiat 5.26.1 replacement
  transition.
- `git verify-commit c67c39b39b0e031c4f51ef32317e442d58785480`
  exits 1 and names revoked subkey
  `B0E32A70FA436DAF4D0A98A7CDBB57E6289F5C1B` with compromise as the reason.
- `git verify-commit eddf475a8e40bbc8b91ecbb24c6b7e5216bae2af`
  and `git verify-commit bdaa71cc90a5efd694e37e5e02b7dfe098898df8`
  exit zero under
  `A0CC410C7BA3DEFC032B3FAA2C9B298EB3D5E57A`. Their parent chain still reaches
  `c67c39b...`, so those individual results do not authorise publication.
- `gpg --with-colons --fixed-list-mode --list-secret-keys
  636EC19DE45DF10F3CE6206F57742DA1ABED6F46` reports the old signing subkey
  revoked and the replacement signing subkey valid. Only public fingerprints
  and status are used here.

### Halted product and audit evidence

- Halted study:
  `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills-fiat-coordinator/tmp/fiat/fiat-369-read-the-audit-synopsis-rather-than-the-whol/.hexaemeron/study.md`,
  SHA-256
  `8ae2db174eb667a1e2acb83ceb3150d06bd599bba92a9fcc0f016533792f3fa7`.
- Product diff: `git diff
  1efec4de762e3b30c1d677371643c0e5e12667ed
  c67c39b39b0e031c4f51ef32317e442d58785480 -- <declared product paths>`.
- Authoritative old round:
  `bdaa71cc90a5efd694e37e5e02b7dfe098898df8:audit/rounds/fiat-369-read-the-audit-synopsis-rather-than-the-whol.md`.
  Its source SHA-256, bound by the sibling synopsis, is
  `eec6159d1d1630499102655fb3f6cc513a30f22023429e2396b11501bcfa2810`.
- Old synopsis:
  `bdaa71cc90a5efd694e37e5e02b7dfe098898df8:audit/rounds/fiat-369-read-the-audit-synopsis-rather-than-the-whol.synopsis.md`.
- The known finding, `S1-R1-01`, its fixed status, `Not checked`, unguarded
  Elenchus verdict, and lead were read from the authoritative source, not
  inferred from the commit subjects.

### Base audit sources and views

The command below exited zero on the clean base and found eleven current
pairs:

```text
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

The five subject sources were read through the checked view and relevant raw
records. No fallback was needed:

| Authoritative source | Read view and direct check | Source SHA-256 |
| --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md`; relevant Protasis records also read directly | `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa` |
| `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md` | sibling `.synopsis.md`; relevant records also read directly | `51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d` |
| `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md` | sibling `.synopsis.md`; all four records also read directly | `aedafae71bf2e254d2f5cc37a40fcf150f80a17fa478bfec4c7a2d2d39a40213` |
| `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md` | sibling `.synopsis.md`; all nine records also read directly | `ba74d5c959d0d06afc0e18ede1770d9b779cfb25f039ed375e6fa4b9a2e4801e` |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`; both records also read directly | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` |

The same successful discovery reported six current pairs outside the subject
evidence boundary:

| Source | Mapped view | Source SHA-256 |
| --- | --- | --- |
| `audit/rounds/fiat-331-bind-user-supplied-sentences-to-the-recorded.md` | sibling `.synopsis.md` | `f721f83237b4f270134f4ca7c876f4b05ad3b98ca846eb6e1f48079779e2bd29` |
| `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.md` | sibling `.synopsis.md` | `ef8b9ccc14580841ba8aff9613a3f6ffd6e40085c35b49bb54ae571dc648125c` |
| `plugins/ariadne/audit/AUDIT.md` | sibling `AUDIT_SYNOPSIS.md` | `d8d13eb238b6e270fb9f89ec11fea797b4a3aa27025b5a62a7f36ac2642617af` |
| `plugins/pandects/audit/AUDIT.md` | sibling `AUDIT_SYNOPSIS.md` | `66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9` |
| `plugins/probitas/audit/AUDIT.md` | sibling `AUDIT_SYNOPSIS.md` | `ba532815ae3abe13be3494b96044bf5d874cfb23842249d8e1cd867186e486c9` |
| `plugins/tabularium/audit/AUDIT.md` | sibling `AUDIT_SYNOPSIS.md` | `1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7` |

### Product, history, and test pointers

- Issue 369: `https://github.com/wildcat-finance/skills/issues/369`.
- Pull requests 593 and 619: the last two merged subject changes, read with
  their full bodies and file lists.
- `plugins/hexaemeron/skills/protasis/SKILL.md`, item 2 and the pre-receipt
  checklist: product contract.
- `plugins/hexaemeron/skills/protasis/EVOLUTION.md`: version and held frontier.
- `plugins/hexaemeron/skills/VERSIONING.md`: independent generation and
  frontier axes.
- `plugins/hexaemeron/tests/test_fiat_skill.py`: focused prose guard.
- `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`: source discovery,
  mapping, rendering, currency, and diagnostics.
- `docs/protasis-audit-record-source-study.md`, its runbook,
  `docs/decisions/ADR-034-recover-signed-fiat-product-across-an-audit-topology-change.md`,
  and the issue-429 recovery study: decisions this product consumes.
- `https://git-scm.com/docs/commit-graph` and
  `https://git-scm.com/docs/git-commit-graph`: supplemental-view and
  verification precedent.
- `https://git-scm.com/docs/git-verify-commit`: commit-signature verification
  interface.

## 8. Ephoros: questions and signals

The product does not run unattended, so it needs no production events,
metrics, traces, alert, or on-call runbook. The run-level questions are finite:

- Which base and commit ancestry were tested and signed?
- Which audit sources were in scope, and which source or view was read?
- Which focused and repository checks ran, and did each exit zero?

The answers are the Git ancestry and signature commands, synopsis diagnostics,
source table, focused guard output, suite and checker exits, single Elenchus
report, and final changed-path list. They are delivery evidence, not retained
service telemetry. This is the finite-work boundary described by
[`ephoros`](../plugins/hexaemeron/skills/ephoros/SKILL.md).

## 9. Phylax: trust boundaries and controls

The first boundary is repository input. Audit sources, views, and paths are
data. Existing synopsis discovery and currency own the audit controls. No
model text becomes a command or path.

The second boundary is signing custody. Public key status and fingerprints are
evidence; private key material is not. Signing remains in the configured local
GPG environment. Diagnostics record the verifier exit and public subkey only.
The old exported material, revocation certificate, secret key, and signature
packet bytes never enter context, files, argv, logs, or controller records.

The third boundary is the ineligible Git history. Reading a diff or blob is
allowed evidence. Merging, rebasing, cherry-picking, pushing, or publishing an
old descendant is refused. The fresh ancestry check and per-commit signature
verification close that boundary.

No dependency, network fetch, credential, new host, archive extraction,
or public interface is added. These controls apply the boundaries in
[`phylax`](../plugins/hexaemeron/skills/phylax/SKILL.md) without claiming a
whole-repository security result.

## 10. Metron: measurement and budget

This product changes a prose contract and one focused guard, not runtime
performance. No product latency, throughput, or memory budget applies, and the
study makes no performance claim. The way this Fiat run executes its checks is
not part of issue 369's product contract or shipped prose.

The existing synopsis line budget remains a correctness condition on the
derived view. The clean base passes the repository-wide currency check with a
14,079-line root source and a 425-line root synopsis. Issue 369 neither changes
that threshold nor treats shorter input as proof of faster or better review.
This is the explicit no-measurement boundary required by
[`metron`](../plugins/hexaemeron/skills/metron/SKILL.md).

## 11. Elenchus: failure, stop rules, and guard

The focused failure is present on the exact base: Protasis item 2 and its
checklist lack the verified-view gate, mappings, fallback, preservation list,
and honest read-mode report. The new focused test must be run on the base and
observed red before the product edit, then run on the finished tree and pass.
It guards both passages without pinning incidental wrapping.

The old Warden finding also has a concrete reproducer: generate Horos before
the new tracked documents enter the index and `files_walked` becomes stale.
The fix is ordering, not a hard-coded count. The clean step stages the complete
tracked set, runs Horos, stages its outputs, runs the same write again, and
requires `git diff --exit-code` over those generated paths.

Stop before receipt or publication if any of these occurs:

- `c67c39b...` or any descendant is in the new ancestry;
- a new commit fails verification or uses a subkey other than the named valid
  replacement;
- the old study, runbook, implementation, audit, or halt receipt is presented
  as a clean-run receipt;
- a synopsis is used after a nonzero currency check, or an in-scope source is
  missing from the read report;
- audit findings, negative space, verdicts, leads, or unknown markers are lost;
- the focused guard never went red on the base or is not green on the result;
- the generated records drift after their final write;
- a required checker, lint, Promise check, focused test, suite, or demonstration
  exits nonzero; or
- a changed path crosses the declared product boundary.

The source-bound Warden runner remains
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` with
format `unittest-json-v1` and a fresh `.elenchus` report path. Elenchus
classifies that complete runner-owned report. A failure is preserved and
worked under [`elenchus`](../plugins/hexaemeron/skills/elenchus/SKILL.md); it is
never turned green by dropping or weakening a test.

## 12. Hypomnema: decisions and durable homes

The product decision remains the Protasis consumer contract: authoritative
audit sources, checked synopses as the normal view, and direct source fallback.
Its standing home is the new `protasis-v4.8.0` generation row. Item 2 and the
pre-receipt checklist carry the operational wording; the focused test guards
both. The committed fresh study keeps the rejected raw-only, synopsis-required,
and manifest/controller alternatives.

The signing incident already has a durable home in the halted run's
hash-chained ledger and authoritative issue-369 audit record. This study points
to them and records the clean-rebuild consequence. It does not rewrite that
history, invent a Fiat replacement receipt, or add a repository ADR for local
key custody. A future Fiat receipt-replacement interface would be a separate,
expensive decision and would need its own study and record.

The held `amendment-block-check` frontier remains byte-identical because this
is a generation on another axis. The evolution tests, exact digest comparison,
and changed-path review guard that decision. These homes follow
[`hypomnema`](../plugins/hexaemeron/skills/hypomnema/SKILL.md) without copying
the same decision into a second standing record.

## Protasis study-readiness checklist

- [x] All twelve study items are present in order.
- [x] Items 8 through 12 each carry an answer and reason.
- [x] Pull requests 593 and 619 were read in full and their open work is
      carried, refused, or left with its named owner.
- [x] Every in-scope base audit record and the halted issue-369 source record
      were read before the design choice; source/view modes and digests are
      recorded.
- [x] The five discipline contracts are cited rather than restated as a claim
      of their complete core.
- [x] Assumptions precede the content they support, including the signing-key
      boundary.
- [x] Every success condition names a command, test, verifier, or demo path.
- [x] Four designs state their trade, and the chosen clean rebuild says what it
      gives up.
- [x] Always, ask-first, and never each have concrete entries.
- [x] The topic remains one product capability and supports one implementation
      step; no module decomposition is needed.
- [ ] Runbook step fields, discipline clauses, executable exits, temporary
      paths, command blocks, final demonstration, and dependency order are
      checked when the runbook is derived. They cannot pass from a study alone.

Study state: ready for a one-step runbook. This establishes study readiness,
not implementation, signature, suite, audit, receipt, or publication success.

### Amendment -- 2026-08-25

**What changed.** Assumption 5, working-prototype property 7, the signing
boundary, and every dependent verifier now select the Shoggoth primary key
`636EC19DE45DF10F3CE6206F57742DA1ABED6F46` itself. The exact OpenPGP selector
is that fingerprint followed by `!`; the previously named replacement signing
subkey is no longer the signing target for this run.

**Why.** After the study receipt, the Creator explicitly chose a signature by
the primary key rather than by its valid signing subkey.

**Steps touched.** Step 1's signing and signature-verification boundary.

**Still holding.** Step 1: entry holds; exit holds.
