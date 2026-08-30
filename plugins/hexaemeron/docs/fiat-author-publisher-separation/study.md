# Fiat author and publisher separation study

Assuming, unless corrected:

1. Shoggoth remains the Git author of governed agent work under `SHOGGOTH.md` and ADR-016.
2. A maintainer may explicitly authorise a human publication route without transferring authorship of the work.
3. For this delivery, the authorised committer, signer, pusher and pull-request account is `laurenceday`, using key `B83B60AE16F5DD1A` and `laurence@wildcat.finance`.
4. GitHub support ticket 4711052 may restore the Shoggoth account later, but delivery cannot depend on when or how that happens.
5. Issue #893 owns repository-wide author policy and approval enforcement. This change must expose truthful evidence for that later gate without trying to install it here.
6. The starting ref is `main` at `d427e750de6b4b728cead9f7bdce1328e5eaa62d`.

## 1. Problem statement

GitHub now refuses every new commit whose committer address is `shoggoth@wildcat.finance`, even when a registered, locally valid key signs it. The same tree and author push successfully when Laurence Day is the committer and signer. Fiat's prose still requires Shoggoth's signer and GitHub account whenever Shoggoth is the author, so its only documented recovery is unavailable.

The prototype must keep `Shoggoth <shoggoth@wildcat.finance>` as author, permit an explicitly authorised human to commit, sign and publish the same work, reject a runtime host as either author or committer, and record the GitHub-resolved author and committer separately without storing either address. A live branch pushed by `laurenceday` and reported by GitHub as `verified: true`, `reason: valid` is the final demonstration.

## 2. Prior art

ADR-016 correctly separates the contributing actor from the runtime host, but its publication paragraph couples author, signer and GitHub account. ADR-018 records author attribution at push and checks that authorship reaches the base; it does not record the committer. Pull request #853 already used the necessary split in production: Shoggoth authored the commit, Laurence committed and signed it, and GitHub accepted it. Issue #906 then isolated the committer address as the decisive variable in a three-way push test. Issue #903 records the earlier outage observation and its corrected signer evidence.

The last merged pull requests touching the target were read before design. Pull request #905 moved the Hexaemeron test harness without changing identity behaviour and carried forward only the bounded-reader recurrence. Pull request #832 documented that `HOST_PR_LOGINS` contains runtime hosts, not delivery agents, and carried nothing forward. Pull request #853 changed the Fiat publication prose and explicitly recorded the same author/committer split this study now makes durable.

The whole audit synopsis set was verified current with `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`. The in-scope sources are `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, `audit/AUDIT_SYNOPSIS.md`, and `audit/rounds/fiat-617-runtime-host-reinstates-the-byline-the-ident.synopsis.md`. The plugin synopsis retains legacy unknown fields and ten fixed controller findings; it has no open publisher-specific finding. The root synopsis records the earlier repository/publication identity separation finding as fixed by repository and pull-request topology checks. The issue-617 synopsis is the directly relevant record: all four rounds preserve human authorship, reject runtime-host authors and bylines, and leave live GitHub behaviour outside their test evidence. Its two fixed prose findings and its carried-forward byline gaps are not reopened by this change.

## 3. Constraints and non-goals

The implementation uses Python's standard library and the existing bounded `git` and `gh` readers. It keeps the existing author attribution shape backward compatible and adds a nested committer record. It does not store an email address, private key, signature body or token. It does not infer who pushed a Git ref because the commits endpoint does not establish that fact. It does not make local signature verification stand in for GitHub's verification response.

The controller behaviour change advances Fiat's generation from `fiat-v5.37.1` to `fiat-v5.38.1` while retaining the `state-shape-validation` frontier and issue #363 held job byte for byte. The installable Hexaemeron package advances from `1.6.11` to `1.6.12` across both plugin manifests and both marketplace manifests so a host can actually receive the repaired controller.

The existing final integration continuity check remains scoped to each pushed commit's primary author. The committer stays in the push receipt as publication evidence and is removed from the author-only view used by the merge check. That separation prevents an authorised publisher from becoming a contributor merely because they signed the commit object.

This change does not reinstate the flagged account, alter an organisation ruleset, install required checks, decide the approval count, or close #893. It does not make every human committer authorised by itself: the user's explicit publication instruction remains the authority, while the controller records the identities GitHub returned and states that boundary. It does not rewrite historical receipts; an absent committer field remains legacy evidence, not a refusal.

Always: run focused identity tests, the root suite, the complete Hexaemeron suite with `TMPDIR=/private/tmp`, the Promise Machine checks, prose lints and `git diff --check` before publication. Ask first: adding an account to a repository policy, changing GitHub rulesets, or changing the author identity. Never: request or copy the Shoggoth private key, store an address in `.hexaemeron`, accept a runtime host as committer, or report a GitHub-valid signature without the exact API response.

## 4. Design options

**A. Wait for GitHub support.** This preserves the existing prose but leaves every delivery blocked for an unbounded external interval. Rejected because the working author/committer split is already demonstrated.

**B. Reauthor governed work as Laurence.** GitHub accepts the commits, but the result erases the contributing actor and contradicts ADR-016. Rejected.

**C. Keep Shoggoth as author and make an authorised human the publisher.** Extend local verification to read and reject host committers, extend GitHub attribution with a separately checked committer account/name/address digest, and update the identity and Fiat contracts to say exactly what this establishes. Chosen because it is the smallest construction that preserves authorship and restores a verifiable publication route.

**D. Add a new publisher allow-list and `hexctl init` flag now.** This could bind an account before work begins, but a controller flag is still an operator declaration and does not prove the human authority behind it. It also entangles this outage repair with #893's repository policy. Deferred to #893, which owns enforceable allowed identities and approval.

The chosen trade is that the controller records a verified committer but does not prove the pusher or the human authority. It says both plainly instead of turning an operator-supplied name into stronger evidence.

## 5. Risk register seed

```risk-register
authorship-erasure | author and committer are different Git fields | tests keep Shoggoth as author while Laurence is recorded only as committer
host-committer | local and GitHub committer identities are untrusted inputs | known runtime-host names emails and accounts refuse before a receipt
receipt-privacy | GitHub returns author and committer addresses | receipts keep only names account logins and lowercased-address digests
legacy-receipts | older push receipts have author attribution only | readers continue to accept absent nested committer evidence without inventing it
verification-overclaim | local and GitHub signature checks establish different relations | docs and tests keep local validity separate from verified true reason valid
publication-authority | an observed committer is not proof of human authorisation | the contract records the boundary and leaves policy enforcement to issue 893
generated-copy-drift | the portable runtime mirrors canonical Fiat files | the generator and Promise Machine checks require byte and digest parity
secret-handling | signing and GitHub operations touch keys and tokens | commands expose no secret material and receipts retain none
```

## 6. Glossary seeds

Author: the contributing actor recorded in Git's author fields.

Committer: the actor who creates and signs the commit object.

Publisher: the authorised actor who carries work across the repository's publication boundary; the observable fields may include committer and pull-request author, while the Git ref pusher remains outside this receipt.

Runtime host: execution infrastructure such as Codex or Claude, never a governed author or publisher.

Attribution record: the login, name and address digest GitHub returns for author or committer, without the address itself.

## 7. Sources

- `SHOGGOTH.md`; ADR-016 and ADR-018.
- Issues [#906](https://github.com/wildcat-finance/skills/issues/906) and [#903](https://github.com/wildcat-finance/skills/issues/903), including their correction comments.
- Merged pull requests [#905](https://github.com/wildcat-finance/skills/pull/905), [#853](https://github.com/wildcat-finance/skills/pull/853), and [#832](https://github.com/wildcat-finance/skills/pull/832).
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, and their identity tests.
- Verified current audit views named in section 2.
- GitHub commit and pull-request REST responses read during the live demonstration.

## 8. Signals, and the questions behind them

No new unattended service is introduced. The existing controller and ledger answer the relevant questions: which commit was checked, whether local verification passed, whether GitHub returned `verified: true` and `reason: valid`, which account GitHub matched as author, and which account it matched as committer. Ephoros is otherwise not applicable because this step adds no daemon, metric or alert surface.

## 9. Boundaries, per capability

Phylax applies to two existing external-input boundaries. Git object fields come from bounded argv-only `git` calls with native replacement objects disabled. GitHub payload fields come from bounded REST reads and pass closed type, length, login and host-identity checks before any receipt is written. No new network endpoint, dependency or secret store is added.

## 10. The budget, or its absence

Metron is not applicable. This is an identity and evidence-shape change with no performance claim. The existing one-request-per-commit test guards against accidentally doubling GitHub reads when committer attribution is added to the already fetched payload.

## 11. The fail-closed posture

Elenchus applies. A missing, malformed or host committer refuses the current receipt, names the failed identity field without echoing an address or signature, and leaves the phase retryable. A valid human committer paired with a Shoggoth author must pass. Guard tests cover both directions and the exact receipt shape. GitHub verification failure remains the existing independent stop.

## 12. Decisions and their homes

Hypomnema places the expensive-to-reverse identity decision in `docs/decisions/ADR-051-separate-governed-authorship-from-publication.md`. The suite-wide identity wording remains in `SHOGGOTH.md`; Fiat procedure stays in `plugins/hexaemeron/skills/fiat/SKILL.md` and `references/push-discipline.md`; mechanical evidence stays in `hexctl.py` and its tests. The study and runbook remain under `plugins/hexaemeron/docs/fiat-author-publisher-separation/`. Fiat's generation row records the behavioural change without moving its frontier, and the package manifests expose the installable update.
