# Supersede receipted commits and guard GitHub verification

Issue: [skills#2014](https://github.com/wildcat-finance/skills/issues/2014).
Starting ref: `main` resolved by Fiat to `685158cdc5407ca5559bf9ef4a021d664e764ece` at init.
The controller that drives this run is the pinned source at that commit; a later controller cannot be used as evidence for its own behaviour.

Assuming, unless corrected:

1. A supersession is permitted only before the step's push receipt. Once a push has been receipted, changing its head needs a separate governed repair path.
2. The repair targets a locally signed, already receipted implementation or audit fixes commit whose published successor cannot pass GitHub verification. Existing ledger events and state receipts remain historical evidence; an append-only supersession event supplies an effective projection.
3. The replacement history is a rewritten branch ancestry from the same step base. It contains no old GitHub-invalid commit in the pushed range, preserves each replaced commit's tree and order, and does not silently absorb unrelated commits.
4. Local signer key user IDs can be inspected without reading secret key material. A matching user ID is a necessary local preflight, while GitHub `verified: true` and `reason: valid` on the exact replacement SHA remains the platform gate. That gate needs the replacement SHA already published to a GitHub ref; the operator owns that separate publication step.
5. Python 3.14.6 and the repository's stdlib tests remain the toolchain. No new credential, external service, or Solidity change is part of the prototype.

## 1. Problem statement

Fiat receipts valid local signatures, then `done push` asks GitHub to verify the pushed commits. In run #1872 Step 7, three locally verified commits with committer `Shoggoth <shoggoth@wildcat.finance>` were signed by a key whose user ID names `laurence@wildcat.finance`. GitHub returned `verified: false`, `reason: no_user` for those SHAs. The round 2 fixes receipt pins `3a046f428`; rewriting the three commits changes their IDs, while checkpoint coverage and the last-local-commit reader still follow the old IDs. A branch with replacements appended above the originals still pushes the originals and fails.

For the controller operator, a working prototype has two independent outcomes. First, local admission at `done implement`, `audit-round` and `done audit` refuses a signed commit whose committer email is absent from the signing key's user IDs, naming the commit, email and key identity. `done prose` creates no commit and has no future SHA to check; it can check only the current receipted head, while `done push` must catch a prose commit created afterwards. Second, a before-push repair verb records one old-to-new map for implementation and audit-fixes commits, proves equal trees and ordered effective ancestry, verifies the replacements locally and through GitHub's exact SHA readback, and makes every downstream consumer use the effective projection. The original receipts stay intact.

The proving demo is a disposable signed run with one implementation commit and two audit rounds. It receipts a local-valid/platform-invalid commit, rewrites the branch with a tree-identical, locally and GitHub-verified replacement, records supersession, then shows `verify`, checkpoint coverage and `done push` accepting only the effective range. A changed-tree candidate, a wrong order, an old commit remaining in the pushed range, and a replacement lacking platform verification each refuse before a ledger write. A separate new run drives first-receipt refusal for the mismatched email. Live run #1872 and PR #2013 are acceptance targets after this product lands, not actions this study performs.

## 2. Prior art

In this repository, `verify_local_commit` and `verify_local_range` in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` accept native local signatures. `done_implement`, `audit_round`, `done_audit` and `done_prose` admit or consume those ranges. `done_push` calls `verify_github_commits` on its exact range. `last_local_commit` returns the last raw audit SHA. `plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/coverage.py` replays the exact implementation and audit receipt ranges and advances its head through `fixes_commit`. `verify` compares state fingerprints with hash-chained ledger entries. These readers must all agree on the effective head. The source also has a later push repair path for a changed live range; that is not a general receipt supersession.

The last two merged pull requests that changed `hexctl.py` are [#1957](https://github.com/wildcat-finance/skills/pull/1957) and [#1917](https://github.com/wildcat-finance/skills/pull/1917). #1957 added a Step 1 runner binding to push receipts and checkpoint restore; its Step 3 audit found a recovery admission drift and fixed it. Its remaining lead about a separate success-criteria restore admission drift stays outside #2014. #1917 changed framework issue number parsing; it supplies no commit-repair mechanism and carries forward #1812's title collision, which stays outside this issue. The #1135 signature-only retirement and [ADR-099](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/docs/decisions/ADR-099-accept-any-validly-signed-authorship.md) remove mandatory Shoggoth attribution. This work must not restore an author, host, or byline admission class.

There is a policy conflict to resolve in the product change. `AGENTS.md` and `SHOGGOTH.md` currently say Fiat admission is signature-only and independent of committer. #2014 explicitly asks a phase receipt to refuse when the committer email is absent from the signing key's user IDs. The runbook must update those instructions alongside the code: cryptographic signature admission remains independent of attribution, while a distinct GitHub-delivery readiness gate can refuse a receipt whose signed commit is known to be ineligible for the required platform check. That second gate checks the email/key relation, not whether the committer is Shoggoth, human or a host. It remains necessary but insufficient; GitHub's actual response decides platform verification. No changed source should ship with the old unqualified sentence still contradicting the new receipt rule.

The verified synopsis currency check exited zero for the whole set. For this scope I read `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` (source `plugins/hexaemeron/audit/AUDIT.md`), `audit/rounds/fiat-1135-retire-mandatory-shoggoth-co-signature-and.synopsis.md`, `audit/rounds/fiat-1135-retire-the-shoggoth-cosignature-and-host-au.synopsis.md`, `audit/rounds/fiat-1944-gate-commands-for-a-repository-with-no-runn.synopsis.md`, and `audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.synopsis.md`; their headers bind each source and digest. The plugin F-01 finding fixed ledger/state fingerprint verification, which an append-only repair must preserve. F-02 through F-09 are fixed and F-10's hook escape is accepted; none supplies supersession. The plugin's open concurrency lead remains outside a single-driver run. The #1135 records cover signature loss, historical record rewriting and authority confusion. Their `Not checked` fields leave live external host state or the named step's future behaviour unproved; their verdicts vary by round and do not constitute #2014 evidence. #1944's Step 3 findings and `guarded`/`inconclusive` verdicts concern runner binding custody and recovery, not commit supersession; its standing restore lead remains open. #861's signature-scope and native checkpoint records warn that a restored machine's keyring differs; this design does not claim cross-machine key availability. Findings, `Covered`, `Not checked`, verdicts and leads remain in those source-bound synopses; this study neither reclassifies nor closes them.

Outside the repository, [GitHub's GPG email troubleshooting](https://docs.github.com/en/authentication/troubleshooting-commit-signature-verification/using-a-verified-email-address-in-your-gpg-key) distinguishes the signing key's email identity and the user's verified email. [GitHub's commit REST response](https://docs.github.com/en/rest/git/commits) exposes `verification.verified` and `verification.reason`. Therefore a local user-ID match cannot predict GitHub acceptance; the platform readback remains a separate exact-object gate. The `no_user` observed on #1872 is not evidence that GitHub would return `bad_email` for every mismatch.

## 3. Constraints and non-goals

The source base is `685158cdc5407ca5559bf9ef4a021d664e764ece`, Python is pinned at 3.14.6 by `.python-version`, and the checked runner plus stdlib `unittest` govern changes. The implementation must retain existing receipts and their ledger hashes; any effective mapping is a new event with a bounded schema and deterministic replay. A platform query is tied to repository, exact SHA, `verified: true` and `reason: valid`; an offline or ambiguous response refuses the repair. GitHub cannot verify an unpublished object: the operator must first publish the candidate on a controlled temporary ref, then the controller reads back the exact SHA before appending supersession. Temporary-ref publication and cleanup require their own explicit steps and evidence; neither follows from a local signature. Secret key bytes and raw signatures do not enter the ledger. Rewriting the step branch or pushing a repaired PR history remains the operator's distinct action.

Non-goals: repairing an already receipted push, changing GitHub account email state, automatically rewriting commits, editing #1872's ledger by hand, changing PR #2013 in this run, adding a human identity or co-author rule, replacing the GitHub gate with a local prediction, or solving the unrelated #1957 and #861 audit leads.

The two requested capabilities are separable but both are required by #2014. Build the admission guard first, with a failing signed fixture and a passing matched fixture. Build append-only supersession next, with a disposable legacy receipt that the new guard would refuse. Close with a full checkpoint/push demonstration. Each step ends green before the next begins; the final step proves their composition.

Step 1 builds and tests the guard and its proof reporter, with the corresponding `AGENTS.md`, `SHOGGOTH.md` and Fiat skill wording, so the executable gate and public policy change together. The `uid-admission` design report is due at the entry to Step 2, after that runner exists. Step 2 builds append-only supersession, its effective ancestry proof, and the governed version ledger. The `effective-ancestry` report is due at the entry to Step 3, after the supersession code exists. Step 3 performs the full demonstration; its `platform-readback` report is due at integration. A review must confirm that the policy text does not claim a local UID match proves GitHub verification.

## 4. Design options

Candidate `append-only-map`: introduce a bounded supersession event referencing the original receipt and an ordered old-to-new commit mapping. Validate source receipts, equal trees, rewritten ancestry, local signature and exact GitHub verification before append. Recompute an effective view for last-local, audit closure, checkpoint coverage, verify, push and checkpoint export/restore. Trade: more readers require one central projection, but history is intact and failures are recoverable.

Candidate `rewrite-receipts`: replace old commit IDs inside the implementation and audit receipts, then rehash ledger/state history. Trade: fewer runtime projections, but it destroys the original receipt chain and makes prior checkpoint archives and audit evidence unverifiable. It fails the historical-integrity and compatibility gates.

The complete candidate-by-criterion record is `.hexaemeron/design-evidence.json`. Its twelve zero-exit reports are selection assessments of these declared constructions against six selection criteria covering all five Protasis concerns. They do not claim implementation conformance. Three more criteria are pending for each candidate: signer-email admission at `step:2`, effective ancestry at `step:3`, and platform readback at `integration`. Each names the future proof command and report path. The first two transitions occur after the step that creates their proof code; checking at the creating step's entry would refuse before that code exists. The rejected candidate's pending cells remain visible but do not block the selected path. `append-only-map` is the unique surviving candidate. Later runbook Exit commands must prove the actual controller behaviour, including the GitHub readback and failures named above.

## 5. Risk register seed

```risk-register
history-rewrite | hash-chained ledger and historical state receipts | supersession appends once and old event bytes and digests remain unchanged
tree-equivalence | each old and replacement commit object | Git tree IDs match pairwise, not merely final diff or patch text
ancestry-leak | rewritten step branch and push base-to-head range | old invalid SHAs are absent and replacement order and parent chain are exact
mapping-ambiguity | old-to-new map and repeated repair requests | duplicate, cycle, branch, step or receipt mismatch refuses without write
signature-identity | local signature and committer email metadata | valid signature and exact email in signing key user IDs; unrelated names do not decide admission
platform-identity | authenticated GitHub commit response | repository and exact SHA match verified true and reason valid; unavailable or conflicting evidence refuses
consumer-drift | last-local, audit close, verify, coverage, push and checkpoint readers | all resolve one effective projection, while raw historical receipt comparison remains intact
partial-write | state and ledger append boundary | interruption replays or refuses without half a supersession
checkpoint-relocation | archive and restore of a repaired run | mapping and Git objects survive, or restore refuses with a recoverable missing-object diagnosis
credential-boundary | local keyring and GitHub reader | no key material enters reports or receipts and query output is bounded
policy-contradiction | root signature-only instructions and the new receipt-readiness gate | code, AGENTS.md, SHOGGOTH.md and Fiat skill text distinguish the two gates and name GitHub readback as final
```

## 6. Glossary seeds

- Receipted commit: a SHA recorded in an existing implementation or audit fixes receipt.
- Replacement: a new commit with the same tree as one receipted commit, locally and GitHub verified.
- Supersession: the append-only ledger event pairing one or more old SHAs with their replacements.
- Effective projection: the deterministic view of commit IDs and ranges after applying validated supersession while retaining historical receipts.
- Platform eligible: GitHub's exact SHA response says `verified: true` and `reason: valid`; local checks alone do not establish it.

## 7. Sources

- [Issue #2014](https://github.com/wildcat-finance/skills/issues/2014), including #1872 Step 7's three SHAs and PR #2013 refusal.
- [Fiat source at starting commit](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/fiat/scripts/hexctl.py): `verify_local_commit`, `verify_local_range`, `last_local_commit`, `done_implement`, `audit_round`, `done_audit`, `done_prose`, `done_push`, `verify_github_commits`.
- [Checkpoint coverage at starting commit](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/coverage.py), implementation and audit-fixes range replay.
- [PR #1957](https://github.com/wildcat-finance/skills/pull/1957), [PR #1917](https://github.com/wildcat-finance/skills/pull/1917), and the audit synopsis paths in section 2.
- [Protasis source at starting commit](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/protasis/SKILL.md), design record and study contract.
- [GitHub GPG email guidance](https://docs.github.com/en/authentication/troubleshooting-commit-signature-verification/using-a-verified-email-address-in-your-gpg-key) and [REST commit verification fields](https://docs.github.com/en/rest/git/commits).

## 8. Signals and on-call questions

When the controller refuses or waits, the operator asks: Which original receipt and candidate SHA disagree? Did a tree, order, local signature or GitHub response fail? Which consumer still points to the old SHA? The supersession verb should report a bounded reason, the pair and step number, while `verify` and checkpoint coverage report the same effective mapping and blocked transition. No unattended service is introduced, so there is no alerting stream. [Ephoros](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal shape.

## 9. Trust boundaries

Git commit objects and metadata are untrusted inputs until exact no-replace-object reads and local signature validation succeed. GPG key user IDs are local, public identity data; their parse must be bounded and must not accept a display name as an email. GitHub's response is an external assertion bound to repository and SHA, not a substitute for Git object checks. The state and ledger are durable local authority only after shape, chain and state fingerprints verify; the append must be recoverable. Checkpoint archives carry those records and objects across machines, where keyring availability may differ. [Phylax](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/phylax/SKILL.md) owns controls at these boundaries.

## 10. Performance budget

No numeric latency budget is asserted for one explicit before-push repair. The implementation should cap map entries and verify each exact commit once per admission; its test command measures the largest allowed fixture under `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-performance.json`. A speed claim requires a separate Metron baseline and repeated measurement, so this study makes none. [Metron](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/metron/SKILL.md) owns that method.

## 11. Fail-closed posture

Missing old receipt, changed tree, invalid local signature, absent signer email UID, GitHub `no_user`/`bad_email`/unavailable response, ambiguous mapping, lingering old SHA in push ancestry, failed range replay, or interrupted append blocks only the dependent receipt or push. The original history remains inspectable; repair and rerun are available. Each bug fix gets a specimen that fails on the old source and passes on the fixed source, including a signed mismatched-email fixture and a changed-tree replacement. The full suite is still required for the release. [Elenchus](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/elenchus/SKILL.md) owns triage and guard convention.

## 12. Decisions and homes

The expensive choices are append-only supersession rather than receipt rewriting, the precise point before push at which a map may be receipted, and the separation between cryptographic signature admission, local GitHub-readiness preflight and actual platform verification. The standing home for this governed Fiat evolution is `plugins/hexaemeron/skills/fiat/EVOLUTION.md`; the runbook must add a generation row there and update `plugins/hexaemeron/skills/fiat/SKILL.md`, root `AGENTS.md` and root `SHOGGOTH.md` so policy and operator instructions agree with the new gate. No future row is yet written or cited as accepted. [Hypomnema](https://github.com/wildcat-finance/skills/blob/685158cdc5407ca5559bf9ef4a021d664e764ece/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns its home and review.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | append-only-map
record | plugins/hexaemeron/skills/fiat/EVOLUTION.md
```
