# ADR-099: Accept any validly signed authorship

Stable identity: `adr/accept-any-validly-signed-authorship`.

## Status

Proposed, 2026-09-06; revised 2026-09-14. This record withdraws the
runtime-host authorship ban and the Shoggoth trailer mandate. The withdrawal
supersedes ADR-016's Decision paragraph and ADR-058's identity-script
paragraph, the second paragraph of ADR-058's Decision. Neither
[ADR-016](ADR-016-attribute-governed-agent-work-to-shoggoth.md) nor
[ADR-058](ADR-058-require-base-owned-identity-and-human-review.md) is
edited, and each remains evidence of the policy it set. ADR-058's requirement
for one approving review is not withdrawn.
[ADR-052](ADR-052-separate-governed-authorship-from-publication.md) stays
in force except for its runtime-host clauses: authorship and publication are
still recorded separately, while its sentence "A runtime host is accepted in
none of those roles" and Fiat's rejection of a known runtime host as author or
committer are part of the ban this record withdraws. The record takes its
number at integration.

## Context

Before this change, Fiat required exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one
`Wildcat-Origin: shoggoth` trailer on every commit in a receipted range. It
refused a known runtime host as author, committer, co-author, pull-request
opener, linked GitHub account or generated-by byline. ADR-058's base-owned
`identity` job applied the same host policy to pull requests to `main` through
`scripts/check_commit_identity.py`.

Those checks conflated three questions. Signature evidence establishes that a
named commit passed the verifier used at that transition. Authorship records
who is named as contributing the work. Publication authority decides who may
change a repository or its hosted settings. None establishes either of the
other two.

Issue [#1135](https://github.com/wildcat-finance/skills/issues/1135) and the
Creator's clarification of 2026-09-06 decided to withdraw both rules, leaving a
valid signature as the only identity requirement a commit has to meet. A first
run implemented that on branch
`fiat/1135-retire-mandatory-shoggoth-co-signature-and`. It merged four step
pull requests, [#1430](https://github.com/wildcat-finance/skills/pull/1430),
[#1455](https://github.com/wildcat-finance/skills/pull/1455),
[#1459](https://github.com/wildcat-finance/skills/pull/1459) and
[#1481](https://github.com/wildcat-finance/skills/pull/1481), into its run
branch, which stopped at `d9114b653772dd6ba09a81d7af8ccc1943f23042` and never
reached `main`. The Creator gave four answers on 2026-09-09 that this revision
follows.

## Decision

Accept any author, committer, co-author, pull-request opener or byline when the
commit-bearing transition has its required valid-signature evidence. Neither
provenance trailer is mandatory. Local Fiat-created commits still need a
successful `git verify-commit`. Pushed and GitHub-created commits still need
an exact platform readback with `verified: true` and `reason: valid`. These
checks say nothing about the signer's authorship or publication authority,
which repository instructions and explicit authority still govern.

Exact authenticated GitHub evidence from a connector has the same standing as
evidence from local authenticated tooling when it carries the fields a check
reads. Neither route's failure to return those fields counts as a successful
or empty result. The Fiat skill, `AGENTS.md` and `SHOGGOTH.md` state this rule.
The controller itself offers only the local route: every GitHub API read in
`hexctl.py` goes through `github_rest`, which calls `gh api`.

Remove the two ambiguous-Shoggoth refusals, deliberately. At `59239072` the
identity checker refused an author or committer whose name or address matched
Shoggoth's, ignoring case, without being Shoggoth's exact identity
(`scripts/check_commit_identity.py:213`), and a co-author trailer that did the
same without being the exact trailer (`:265`). Those refusals answered
impersonation, an identity imitating Shoggoth's, rather than attribution. The
Creator's third answer removes them, and
`test_a_lookalike_shoggoth_identity_is_accepted` in
`tests/test_commit_identity.py` now holds a lookalike author, committer and
co-author as accepted.

Salvage the first run's branch rather than rebuild it, as the Creator decided
on 2026-09-09. Against its merge base
`3cc0ad7f521985e46cf29f364a20e19fa99b64dd` the branch changed 73 files. This
run adopts 30 and reworks 43: 10 regenerated, 22 reverted to the bytes of
`59239072` and 11 rewritten, as section 4 of
`docs/signature-only-authorship/study.md` lists. Of the 30 adopted files, 25
keep the branch's bytes. In `AGENTS.md`, `README.md` and
`plugins/hexaemeron/AGENTS.md`, Step 1's merge combined the branch's changes
with those `main` made after that merge base; the revision of 2026-09-14
changed the assertions `tests/test_evolution_contract.py` makes on the latest
Fiat history row; and Step 6 corrected a docstring in
`plugins/hexaemeron/tests/test_hexctl.py` that still described the withdrawn
author and trailer checks, changing no assertion. The branch contradicted the Creator's answers in two places: it deleted
the identity checker, and it rewrote the contributor-ranking promise and cut
the parity check behind it.

Step 1 merged a local reconstruction of that branch, not `d9114b65` itself.
The first six commits keep their hashes. The last six carried neither
provenance trailer, and the controller receipting this run still requires both,
so they are re-signed with both added and keep their trees, authors, author
dates and messages. The four GitHub web-flow merges of #1430, #1455, #1459 and
#1481 are left out, and each has the tree of the step head it merged. The
reconstruction ends on the tree of `d9114b65`, which is not an ancestor of the
run branch. The old-to-new commit ids are in the message of
`928884056101bdc2b739c12bdbc2441b6647e30a`, and adopted records that still cite
`9a0a1bde`, `27a9622a`, `843d232d` and `155abea7` resolve through that map.

Keep `hexctl.py`'s three `HOST_*` frozensets, `HOST_IDENTITY_NAMES`,
`HOST_IDENTITY_EMAILS` and `HOST_PR_LOGINS`, as a parity anchor with no caller.
Nothing in `hexctl.py` reads them and Fiat refuses no commit on them.
`verify_host_set_parity` at `scripts/contributors.py:191` parses them from
`hexctl.py` and stops when its own copy differs, and the contributor-ranking
promise at `PROMISE_MACHINE.md:344` names that check as its evidence. The
Creator's first answer keeps that promise as written, so it is byte-identical
to `59239072` in all 19 copies, and `CONTRIBUTORS.md` still excludes runtime
hosts. The first run had kept the classification in `scripts/contributors.py`
alone; it is now declared in both files and checked for parity. It still
decides the ranking only. Excluding an account from `CONTRIBUTORS.md` does not
bar it from validly signed authorship, or from publication where it has
authority.

Narrow the identity checker's promise instead of retiring the checker.
`scripts/check_commit_identity.py` returns under the Creator's second answer
with 34 of the 42 refusals it had at `59239072`. The eight removed are the two
ambiguous-Shoggoth refusals, four runtime-host refusals (`:215`, `:244`,
`:259`, `:307`) and the two trailer counts (`:269`, `:273`). Its read ceilings
are unchanged. It no longer imports `contributors`, whose three uses were all
in removed refusals. Its module docstring limits the claim: a pass establishes
that the commits from the exact base to the exact head stayed inside
`COMMIT_COUNT_MAX`, `COMMIT_BYTES_MAX` and `COMMIT_TOTAL_BYTES_MAX` and that
each commit's author and committer identities parsed, and it establishes
nothing about who authored a commit. Its success record keeps the schema name
`wildcat-commit-identity-check/v1` and no longer counts authors:
`shoggoth_author_count` and `human_author_count` are gone, because the second
would count an accepted runtime host as human.
`.github/workflows/identity.yml` returns at the bytes of `59239072` and still
publishes the `identity` status. That status is advisory: ruleset `21830871`
no longer requires it, and this run's study read the ruleset on 2026-09-09
with `invariants` as its only required context.

Keep `.claude/settings.json`. The first run's Step 3 deleted it, with
`tests/test_host_settings.py`, in `27a9622a`. This run restores the file
byte-identical to `59239072` and the test narrowed. No Creator answer covers
the file, so keeping it is a reading. Its three values are presentation
preferences, still useful where a host's default trailer, footer or session
link is noise. `INSTALL.md`, adopted at the branch's bytes, documents the file
and would be false without it. Deleting it would change every contributor's
checkout, and the study keeps that deletion on its ask-first tier.
`tests/test_host_settings.py` pins the one `attribution` object, its three
keys, the `sessionUrl` value `false`, and only the types of `commit` and `pr`,
which must be strings, leaving their text free. The effect of
`sessionUrl: false` on a cloud session is documented, in `INSTALL.md` and
Anthropic's settings reference, but has not been observed here.

Read the GitHub web-flow refusal under a keyring that cannot validate GitHub's
keys. The Creator's fourth answer keeps Fiat's refusal of a commit signed with
GitHub's web-flow keys `4AEE18F83AFDEB23` and `B5690EEEBB952194` as expected
behaviour. The refusal is the `GITHUB_SIGNING_KEYS` branch of
`verify_local_commit` in `hexctl.py`, and it runs only after
`git verify-commit` fails. A keyring holding GitHub's keys accepts a web-flow
commit such as `77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883`, so the refusal never
runs there, and the refusal's own message says not to import GitHub's key.
This run changes neither the gate nor any keyring.
`tests/prove_signature_only_refusals.py` proves the unsigned,
altered-after-signing and web-flow refusals under a keyring holding only
`3BCD9EFDA6670A3F65AF679EB83B60AE16F5DD1A`. On a keyring that validates a
GitHub key it exits 3 and names the cause.

## Alternatives

- **Keep mandatory Shoggoth attribution and the runtime-host ban.** Collective
  attribution would stay consistent, but otherwise validly signed
  contributions would still be refused for a convention that no longer
  governs admission.
- **Delete signature and identity controls together.** This would be smaller,
  but it would admit unsigned or invalidly signed commits and discard the
  evidence this decision keeps.
- **Make the former attribution rules configurable.** This would ease a staged
  migration, but it would keep withdrawn policy available, add persistent
  state and turn one rule into a mode matrix.
- **Adopt the first run's branch as it stands (`inherit-landed`).** It keeps
  63 of the 73 changed files and retires the identity job, its checker and the
  settings file. It satisfies 2 of the Creator's 4 answers and removes the
  parity anchor, so it fails both selection gates.
- **Make `scripts/contributors.py` the only declaration (`single-owner`).** It
  keeps 50 of the 73 files, with no duplicated set and no unread code, but it
  rewrites a promise the Creator fixed as standing. It satisfies 3 of 4
  answers and fails the parity gate.
- **Give the sets a consumer (`record-attribution`).** A host-attribution
  field on Fiat's push receipt would make the three sets live code. It passes
  both gates but adds 1 new identifier and a receipt shape to keep, so the
  selected design, equal on every other measure, dominates it.
- **Rebuild from `main`.** This would avoid the ten-path merge, but it
  discards 16 merged commits and four audited step pull requests. The study's
  first pass proposed it, and the Creator reversed that on 2026-09-09.
- **Keep the two lookalike refusals.** They would still flag a name imitating
  Shoggoth's, but the Creator's third answer removes them, and with every other
  identity accepted they would be the only name-based admission rule left.
- **Delete `.claude/settings.json`, as the first run did.** This would remove
  a file Fiat no longer needs, but it makes `INSTALL.md` false and changes
  every contributor's checkout without a Creator answer.
- **Make the web-flow refusal independent of the keyring.** It would refuse
  a GitHub-signed commit whatever keyring verifies it, but it changes the
  signature gate, which this run leaves as it is. Step 1's audit raised it,
  and the question stays open.

## Consequences

Claude, Fable, Codex, another runtime host, a human or another account may
appear in authorship and pull-request surfaces without an identity refusal.
Each provenance trailer is optional. Missing or invalid required signature
evidence still stops the transition, and a valid signature grants no
publication authority.

An identity imitating Shoggoth's now passes like any other. Nothing mechanical
separates impersonation from attribution, so a name in an author field or
trailer proves nothing about who did the work.

Nothing in `hexctl.py` reads the three sets, so they look like dead code.
Deleting them makes `scripts/contributors.py --verify-host-set` refuse and
falsifies the ranking promise. A change to a set goes into both files
together, as the comment above the sets in `hexctl.py` says.

A red `identity` status blocks no merge, and a workflow that stops running
looks the same as one that passes. A pass says the range stayed bounded and
its identities parsed, and nothing about who authored it. Success records from
before this change carry the two author counts and later ones do not, under
the same schema name. An audit record that quotes those fields describes an
older record.

The settings file stays a presentation preference, not Fiat policy. If
`sessionUrl: false` does not suppress the session link in a cloud session, the
link appears and Fiat does not refuse the commit for it.

A controller released before this change still requires both trailers and
still refuses host attribution in the runs it receipts, which is why this
run's own commits carry both trailers.

Historical records and receipts keep describing the policy that applied when
they were written. The Interceptor's copy of the host rule is outside this
repository and this record does not change it.
