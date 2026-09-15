# Signature-only authorship demonstration

On 2026-09-14 (UTC) the built tree for
[skills#1135](https://github.com/wildcat-finance/skills/issues/1135) accepted a
signed commit authored by `Claude <noreply@anthropic.com>`, carrying no
provenance trailer and a `Generated with Claude Code` line. The same object
unsigned was refused with the message the base gives. GitHub's web-flow commit
`77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883` was refused through the GitHub key
branch under a keyring without GitHub's keys. `scripts/check_commit_identity.py`
accepted the host-authored commit and refused a malformed author.
`scripts/contributors.py --check` gave the same result at this tree and at the
base, one second apart, and runtime hosts stay out of the ranking. None of the 30 adopted paths asserts
a withdrawn rule once this step corrected one test docstring, and no code path
refuses on host identity or trailer count. The decision behind all of this is
`adr/accept-any-validly-signed-authorship`.

## What ran

| Item | Value |
| --- | --- |
| Tree under test | `9f1be94013b171da066e98567386a3bcf89e64d4`, the Step 5 head |
| Comparison tree | a detached worktree of `592390722f10df53658906623b15428dbfb88d8f`, the run's base |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | blob `aa9308dace6d55e0d05e2e12da4aaa658c2b8f66`; base `0f04c20b1ca7b97805f16dffef9fe6abbf020415` |
| `scripts/check_commit_identity.py` | blob `0c9bf7c903ac83e084c6a07ef7f834f60d4c96f9`; base `c0bdff8e09141a228bdc80877e787250085a234d` |
| `scripts/contributors.py` | blob `9633d62101bee69c4aa4913282aa7b5522bc11e5`; base `8ae19da1594d54a4385d2c8217e4938ae315cbc5` |
| `tests/prove_signature_only_refusals.py` | blob `ba39f00f4344a8fc4115919f1b0f7d312aa87553`; absent at base |
| Tools | Git `2.50.1`; GnuPG `2.2.41`, Git's configured signing program, for signing and the `%G?` reads; GnuPG `2.5.21` on `PATH` for the verifications `hexctl.py` and the prover pin; the `3.14.6` interpreter that `.python-version` pins |

The commit that adds this record also brings the runbook copy up to the
controller's bytes, where the study copy already matched, regenerates the Horos
boundary and census, and corrects one docstring in
`plugins/hexaemeron/tests/test_hexctl.py` together with the digest pins that
edit moves. It changes none of the four files in the table, so every result
below holds for that commit's tree as well.

Every command ran from the root of the tree its row names, with `NO_COLOR=1`.
Two keyrings appear. The GitHub-free keyring is a `GNUPGHOME` holding one public
key, `3BCD9EFDA6670A3F65AF679EB83B60AE16F5DD1A`, with its encryption subkey and
no secret key. The default keyring is this host's own. It holds the secret half
of that key and GitHub's web-flow keys `4AEE18F83AFDEB23` and
`B5690EEEBB952194`.

The specimens live in a disposable bare repository outside this checkout, on a
path with no symlink in it, because `check_commit_identity.py` refuses a
symlinked path. This record keeps no credential and no signature bytes. The
GitHub token reached `contributors.py` through its environment, taken from
`gh auth token`, and was never printed.

## Specimen objects

`SPECIMEN` is the bare repository and `MSG` a message file outside it. These
commands built all four objects, and the signing command used the default
keyring.

```sh
git init --bare --quiet "$SPECIMEN"
EMPTY=$(git --git-dir="$SPECIMEN" hash-object -t tree -w --stdin </dev/null)
export GIT_AUTHOR_DATE='1789430400 +0000' GIT_COMMITTER_DATE='1789430400 +0000'
BASE=$(GIT_AUTHOR_NAME='Specimen Base' GIT_AUTHOR_EMAIL=base@example.invalid \
  GIT_COMMITTER_NAME='Specimen Base' GIT_COMMITTER_EMAIL=base@example.invalid \
  git --git-dir="$SPECIMEN" commit-tree --no-gpg-sign -m 'Specimen base' "$EMPTY")
printf 'Synthetic runtime-host attribution specimen\n\nGenerated with Claude Code\n' >"$MSG"
export GIT_AUTHOR_NAME=Claude GIT_AUTHOR_EMAIL=noreply@anthropic.com
export GIT_COMMITTER_NAME='Signature Specimen' GIT_COMMITTER_EMAIL=specimen@example.invalid
SIGNED=$(git --git-dir="$SPECIMEN" commit-tree -S3BCD9EFDA6670A3F65AF679EB83B60AE16F5DD1A -p "$BASE" -F "$MSG" "$EMPTY")
UNSIGNED=$(git --git-dir="$SPECIMEN" commit-tree --no-gpg-sign -p "$BASE" -F "$MSG" "$EMPTY")
MALFORMED=$(printf 'tree %s\nparent %s\nauthor Malformed Specimen 1789430400 +0000\ncommitter Signature Specimen <specimen@example.invalid> 1789430400 +0000\n\nMalformed author identity specimen\n' "$EMPTY" "$BASE" \
  | git --git-dir="$SPECIMEN" hash-object -t commit -w --stdin --literally)
```

| Name | Object | What it is |
| --- | --- | --- |
| `BASE` | `0226c6156826d058c5bb1640be8efa9fe9379712` | unsigned empty-tree root, where the checked range starts |
| `SIGNED` | `f92d78c0918fa42f8ffabb0e2f70f197c66e9fc5` | author `Claude <noreply@anthropic.com>`, a synthetic committer, a message with a `Generated with Claude Code` line and no `Co-authored-by` or `Wildcat-Origin` line, signed with key `B83B60AE16F5DD1A` |
| `UNSIGNED` | `069ba7c1db07cd30f2b92aa9eb0c9286baf3406e` | the bytes of `SIGNED` without its `gpgsig` header |
| `MALFORMED` | `ff1e819cb28a2fab22026270cb08c2a6baf58748` | a child of `BASE` whose author line has no address |

`1789430400` is 2026-09-15T00:00:00Z. `BASE`, `UNSIGNED` and `MALFORMED` come
out the same on a rerun; `SIGNED` does not, because its signature carries a
creation time. `%G?` reads `U` for `SIGNED` under the GitHub-free keyring and
`G` under the default keyring.

## Local admission

Each row makes this call, with `KEYRING` set to the GitHub-free keyring and
`REPOSITORY`, `COMMIT` and `LABEL` as the row gives them:

```sh
GNUPGHOME="$KEYRING" python3 - "$REPOSITORY" "$COMMIT" "$LABEL" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("hexctl", "plugins/hexaemeron/skills/fiat/scripts/hexctl.py")
hexctl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hexctl)
print(hexctl.verify_local_commit(sys.argv[1], sys.argv[2], sys.argv[3]))
PY
```

| `REPOSITORY`, `COMMIT`, `LABEL` | Tree | Exit | Result |
| --- | --- | --- | --- |
| `$SPECIMEN`, `SIGNED`, `signed specimen` | `9f1be940` | 0 | accepted; printed `f92d78c0918fa42f8ffabb0e2f70f197c66e9fc5` |
| the same | `59239072` | 2 | refused: `hexctl: error: signed specimen commit f92d78c0918fa42f8ffabb0e2f70f197c66e9fc5 uses a runtime host as author; ...` |
| `$SPECIMEN`, `UNSIGNED`, `unsigned specimen` | `9f1be940` | 2 | refused: `hexctl: error: unsigned specimen commit 069ba7c1db07cd30f2b92aa9eb0c9286baf3406e has no valid local signature` |
| the same | `59239072` | 2 | refused with byte-identical standard error |
| `.`, `77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883`, `web-flow specimen` | `9f1be940` | 2 | refused: `hexctl: error: web-flow specimen commit 77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883 is signed by GitHub (key B5690EEEBB952194), not locally. ...`, ending `Do not import GitHub's public key to make this check pass; that removes the guarantee the check exists for.` |
| the same | `59239072` | 2 | refused with byte-identical standard error |

The base refuses the signed specimen under the host authorship ban this run
withdrew. The other four refusals are the signature gate, and its messages did
not change.

`77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883` is GitHub's merge of #1512. Under
the default keyring `git verify-commit` accepts it, so the GitHub key branch
cannot run there. The prover says so:

```sh
GNUPGHOME="$KEYRING" python3 tests/prove_signature_only_refusals.py --candidate retain-declaration --out .hexaemeron/design-reports/step6-demonstration-signature-refusal-preserved.json
python3 tests/prove_signature_only_refusals.py --candidate retain-declaration --out .hexaemeron/design-reports/step6-demonstration-default-keyring.json
```

| Keyring | Tree | Exit | Result |
| --- | --- | --- | --- |
| GitHub-free | `9f1be940` | 0 | `signature-refusal-preserved: unsigned, altered and web-flow commits are each still refused with hexctl's own message`, and the report was written |
| default | `9f1be940` | 3 | `unproven: this keyring validates GitHub web-flow key B5690EEEBB952194: git verify-commit accepts 77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883, so hexctl's GitHub-signed refusal cannot run here; rerun under a GNUPGHOME that holds no GitHub signing key` |

The report path sits in the run's controller directory, which Git ignores, so
the report is not shipped. It differs from the report Step 1 receipted only in
the `--out` path its `command` field names.

## Identity checker

Each row runs this command:

```sh
python3 scripts/check_commit_identity.py --repository "$SPECIMEN" --base "$BASE" --head "$HEAD" --pull-request-login "$LOGIN"
```

| `HEAD` | `LOGIN` | Tree | Exit | Result |
| --- | --- | --- | --- | --- |
| `SIGNED` | `claude[bot]` | `9f1be940` | 0 | `{"base":"0226c6156826d058c5bb1640be8efa9fe9379712","commit_count":1,"head":"f92d78c0918fa42f8ffabb0e2f70f197c66e9fc5","pull_request_login":"claude[bot]","schema":"wildcat-commit-identity-check/v1","status":"passed"}` |
| `SIGNED` | `claude[bot]` | `59239072` | 2 | `identity: pull request was opened by a runtime-host account` |
| `SIGNED` | `laurenceday` | `59239072` | 2 | `identity: commit f92d78c0918fa42f8ffabb0e2f70f197c66e9fc5 names a runtime host as author` |
| `MALFORMED` | `claude[bot]` | `9f1be940` | 2 | `identity: commit ff1e819cb28a2fab22026270cb08c2a6baf58748 has malformed author identity` |
| `MALFORMED` | `laurenceday` | `59239072` | 2 | refused with byte-identical standard error |

## Contributor ranking

```sh
GITHUB_TOKEN="$(gh auth token)" python3 scripts/contributors.py --check
python3 scripts/contributors.py --verify-host-set
python3 -m unittest tests.test_contributors.Ranking -v
```

| Command | Tree | Exit | Result |
| --- | --- | --- | --- |
| `--check`, 2026-09-14T23:35:04Z | `9f1be940` | 2 | `contributors.py: unknown identity: 'shoggoth-wildcat-labs[bot]' is a Bot that is not in the host set; extend HOST_PR_LOGINS in hexctl.py and here, then rerun` |
| `--check`, 2026-09-14T23:35:05Z | `59239072` | 2 | byte-identical standard error |
| `--verify-host-set` | `9f1be940` | 0 | `host set matches hexctl.py` |
| `--verify-host-set` | `59239072` | 0 | `host set matches hexctl.py` |
| `tests.test_contributors.Ranking` | `9f1be940` | 0 | 13 tests, `OK` |

Both trees stop on the same unclassified Bot before a ranking exists, so
neither run ranked live data. `exclusion_reason` still returns
`runtime host identity` for a host login before it classifies anything else
about the account (`scripts/contributors.py:325-328`). The
offline `Ranking` tests compute the ranking from recorded responses.
`test_ranks_only_the_human_contributors` ranks two human logins, and
`test_names_a_reason_for_every_exclusion` excludes `claude` and `claude[bot]`
as runtime hosts. The committed `CONTRIBUTORS.md` is unchanged from the base,
ranks four logins and names no member of the three host sets.

## The 30 adopted paths

Section 4 of [the study](study.md) names the 30 adopted paths among the 73 the
first run changed; the other 43 were reworked. Each adopted path was searched at `9f1be940` for the
vocabulary of both withdrawn rules and of the four answers below, and every
matching line was read in its context. The vocabulary covered runtime hosts
and their names, trailers, bylines, co-authors, the `HOST_*` names, the
identity checker and its status, lookalike identities, web-flow signing and the
contributor ranking. The Creator's answers of 2026-09-09:

1. `CONTRIBUTORS.md` keeps excluding runtime hosts, and the ranking promise
   stands as written.
2. `scripts/check_commit_identity.py` keeps its bounded-read rules under a
   narrower promise, without the trailer mandate or the host ban.
3. The ambiguous-Shoggoth refusals go.
4. Fiat keeps verifying signatures on commits it did not create, and refusing a
   GitHub-signed commit is expected.

| Path | Bytes | Reading |
| --- | --- | --- |
| `AGENTS.md` | Step 1 merge | Admission is signature-only and independent of author, committer, co-author, runtime, opener, byline and trailer (`:165-170`). |
| `INSTALL.md` | branch | `.claude/settings.json` is a presentation preference; Fiat accepts valid signed commits and records bylines or co-authors as attribution (`:125-126`). |
| `README.md` | Step 1 merge | Fiat admits valid signatures, not a named author, trailer, runtime or transport (`:52-53`); a daily job rebuilds `CONTRIBUTORS.md` (`:57`, answer 1). |
| `SHOGGOTH.md` | branch | Admission is signature-only and neither trailer is mandatory (`:70-75`); contributor recognition may still exclude non-human accounts without that becoming a Fiat refusal (`:82-84`, answer 1). |
| `audit/rounds/fiat-1135-retire-mandatory-shoggoth-co-signature-and.md` | branch | The first run's dated rounds of 2026-09-06 to 2026-09-08. Its Step 2 lead puts the checker's host refusals in a workflow that run meant to remove (`:64`), a plan answer 2 reversed. It states no rule in force. |
| `audit/rounds/fiat-1135-retire-mandatory-shoggoth-co-signature-and.synopsis.md` | branch | The synopsis of the same rounds. |
| `docs/how-to-help-shoggoth.md` | branch | Fiat admits a commit by its valid signature and host attribution is permitted (`:211-220`); the ranking excludes known non-human accounts (`:302-306`, answer 1). |
| `docs/shoggoth-signature-only-retirement-demonstration.md` | branch | The first run's dated demonstration. Its four specimens stay true under this design: two signed commits accepted, one unsigned and one altered commit refused. It records `tests.test_host_settings` as deleted (`:78`); this run's Step 4 restored that test. |
| `plugins/hexaemeron/AGENTS.md` | Step 1 merge | Receipts need verified signatures; attribution and trailers are recorded and do not decide admission (`:131-134`). |
| `plugins/hexaemeron/agents/mason.md` | branch | No provenance trailer is mandatory (`:69`). |
| `plugins/hexaemeron/agents/warden.md` | branch | No provenance trailer is mandatory (`:109`). |
| `plugins/hexaemeron/skills/fiat/SKILL.md` | branch | The push paragraph needs a valid local signature, makes neither trailer mandatory and treats attribution as evidence (`:590-593`); its other trailers are the ADR-assignment trailers (`:673-678`). |
| `plugins/hexaemeron/skills/fiat/references/push-discipline.md` | branch | Any repository-valid signing identity (`:35-37`); a range GitHub re-signed with its web-flow key is refused (`:357-364`, answer 4); recorded authors must survive the merge (`:695-700`), a rule this run keeps. |
| `plugins/hexaemeron/skills/fiat/references/wildcat-marketplace.md` | branch | No line matches the vocabulary. |
| `plugins/hexaemeron/tests/hexctl_harness.py` | branch | Fake `git` and `gh` modes such as `host-author`, `no-trailers` and `host-pr-byline` that feed the acceptance tests; it asserts nothing itself. |
| `plugins/hexaemeron/tests/host_identity_cases.py` | branch | Every local and platform host or trailer shape is accepted when verification is valid (`:7-18`, `:41-71`), and invalid evidence is still refused (`:20-32`). The class keeps the name `HostIdentityRefusalCases`. |
| `plugins/hexaemeron/tests/test_fiat_skill.py` | branch | Asserts that neither trailer is mandatory and that attribution is not an admission class (`:229-239`); the `BodyReadBackTests` docstring (`:696-704`) recounts a skills#617 refusal as history. |
| `plugins/hexaemeron/tests/test_hexctl.py` | this step | Accepts host pull-request authors and bylines (`:1366-1391`) and keeps the web-flow diagnosis (`:5516-5601`, answer 4). Its docstring at `:5571-5573` said a commit that verifies still goes on to author and trailer checks. This step rewrote those lines and changed no assertion. |
| `tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai` | branch | A compiled instruction fixture for Fiat's study and runbook phases, with no identity, trailer or host-admission content. |
| `tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json` | branch | The model of that fixture. |
| `tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json` | branch | The source spans of that fixture. |
| `tests/fixtures/agent-instruction-v1/manifest.json` | branch | Digests and bindings of the instruction fixtures. |
| `tests/fixtures/agent-instruction-v1/promise-machine-router-selection/compact.wai` | branch | A compiled instruction fixture for the router-selection promise, with no identity content. |
| `tests/fixtures/agent-instruction-v1/promise-machine-router-selection/model.json` | branch | The model of that fixture. |
| `tests/fixtures/agent-instruction-v1/promise-machine-router-selection/source-spans.json` | branch | The source spans of that fixture. |
| `tests/fixtures/ruleset-identity-retirement/postimage.json` | branch | Ruleset `21830871` requiring `invariants` alone: a recorded state, not a rule in code. |
| `tests/fixtures/ruleset-identity-retirement/preimage.json` | branch | The same ruleset requiring `identity` and `invariants`, before the first run changed it. |
| `tests/test_evolution_contract.py` | Step 5 | Asserts the Fiat history row names signature-only admission, the parity anchor and an unchanged web-flow refusal (`:369-372`). |
| `tests/test_marketplace_prose.py` | branch | Asserts that `README.md` and the contributor guide say Fiat admits valid signatures and keeps publication authority separate (`:356-367`). |
| `tests/test_shoggoth_identity.py` | branch | Pins the signature-only text of `SHOGGOTH.md`, with neither trailer mandatory (`:59-70`). |

"Branch" means the bytes of `d9114b653772dd6ba09a81d7af8ccc1943f23042`, and 25
of the 30 paths keep them at this step's commit. The next test in
`test_hexctl.py`, `test_the_signature_check_runs_before_anything_else`
(`:5589-5601`), still mocks `commit_author`, which `verify_local_commit` no
longer calls. That mock asserts no rule, and this step leaves it as it is.

## Nothing refuses on host identity or trailer count

Each count is a fixed-string search of one committed tree's code, with test
directories excluded:

```sh
git grep -c -F -e "$TOKEN" "$TREE" -- '*.py' '*.sh' '*.yml' '*.yaml' '.githooks/*' ':(exclude,glob)**/tests/**' ':(exclude,glob)tests/**'
```

Line numbers in the second column are those of study section 2, on
`59239072`.

| Token | Section 2 sites | `59239072` | `9f1be940` |
| --- | --- | --- | --- |
| `runtime host as` | Fiat's author, committer and co-author guards (`hexctl.py:12469`, `:12801`, `:12812`, `:12829`, `:13224`, `:13363`) and the checker's `:215` and `:259` | 8 | 0 |
| `names a runtime host` | `hexctl.py:12469`, `:13363`, `:13369`; checker `:215`, `:259` | 5 | 0 |
| `runtime host account` | the linked-account guard `hexctl.py:12424` and its cause text | 2 | 0 |
| `runtime-host byline` | the byline guards `hexctl.py:12834` and `:13236` | 2 | 0 |
| `runtime-host generated-by byline` | checker `:244` | 1 | 0 |
| `runtime-host account` | checker `:307` | 1 | 0 |
| `exact Shoggoth` | the trailer counts `hexctl.py:12841` and checker `:269` | 2 | 0 |
| `exact Wildcat-Origin` | `hexctl.py:12846` and checker `:273` | 2 | 0 |
| `ambiguous Shoggoth` | checker `:213` and `:265` | 2 | 0 |
| `is_host_identity` | the predicates `hexctl.py:12387` and `scripts/contributors.py:111`, and their callers | 11 | 2, both in `scripts/contributors.py` |
| `is_host_login` | `scripts/contributors.py:119` and its callers | 4 | 3, all in `scripts/contributors.py` |
| `HOST_BYLINE_RE` | `hexctl.py:12313` | 6 | 0 |
| `COAUTHOR_TRAILER` | `hexctl.py:12223` | 5 | 0 |
| `ORIGIN_TRAILER` | `hexctl.py:12224` | 4 | 0 |
| `CAUSE_HOST_` | the causes Fiat's host refusals printed | 17 | 0 |
| `SHOGGOTH_NAME` | the checker's lookalike test | 6 | 0 |
| `SHOGGOTH_EMAIL` | the checker's lookalike test | 6 | 0 |
| `Co-authored-by: Shoggoth` | the exact trailer both files counted | 2 | 0 |
| `Wildcat-Origin` | the same trailer pair | 5 | 1, the module docstring of `scripts/contributors.py` |
| `HOST_IDENTITY_NAMES` | `hexctl.py:12250`, `scripts/contributors.py:38` | 8 | 7: `hexctl.py` 1, `scripts/contributors.py` 6 |
| `HOST_IDENTITY_EMAILS` | `hexctl.py:12268`, `scripts/contributors.py:56` | 7 | 6: `hexctl.py` 1, `scripts/contributors.py` 5 |
| `HOST_PR_LOGINS` | `hexctl.py:12274`, `scripts/contributors.py:62` | 9 | 7: `hexctl.py` 1, `scripts/contributors.py` 6 |

`grep -c 'raise Refusal' scripts/check_commit_identity.py` gives 42 on
`59239072` and 34 on `9f1be940`. `hexctl.py` names each host set once, where it
declares it, under the comment that says why the sets stay
(`hexctl.py:12261-12266`). Every other reader of the sets is
`scripts/contributors.py`, which ranks contributors and checks parity with
`hexctl.py`. Beyond those declarations and `scripts/contributors.py`, a
case-insensitive search of the same code for runtime host, co-author,
`Wildcat-Origin`, generated-with and byline finds co-author parsing under its
ceilings in `hexctl.py` and the checker, Fiat's merge attribution check, two
comments about issue and pull-request bodies, and the Imprimatur corpus labels.
None of them refuses on host identity or trailer count.

## On-call questions

The study names three questions for the unattended `identity` workflow.

**A pull request went red on `identity`. Which rule refused, and do we still
keep it?** The checker prints `identity: <refusal>` to standard error and exits
2, naming the commit, as the malformed specimen shows. It carries 34 `raise
Refusal` sites, down from 42, and none of the withdrawn messages counted above
is left in it, so a red status names a rule the repository still keeps.

**Is the `identity` status still being published?** This step cannot see it.
The workflow runs under `pull_request_target` for pull requests to `main` and
runs the checker from the protected base, never from the candidate. Its file is
blob `437c98ebcbb2258324dd58ab56b6584032035098` at `59239072`, at `origin/main`
`b61f600e72fab94c6c71a4410cd5e6061d098762` and at `9f1be940`. That `origin/main`
still carries the base's checker, blob `c0bdff8e09141a228bdc80877e787250085a234d`,
and its `scripts/contributors.py`, blob
`8ae19da1594d54a4385d2c8217e4938ae315cbc5`. Until this run merges, `main`'s
base-owned copy judges every pull request, and this run's step pull requests
target step branches, which the workflow does not watch. A status readback on
the integration pull request is therefore an integration observation and not
an exit of this step.

**Which commits reached `main` unsigned?** The reads here answer part of it, at
`origin/main` `b61f600e72fab94c6c71a4410cd5e6061d098762`, 3,659 commits:

- Commit headers: 2,939 commits carry an OpenPGP signature, 719 an SSH
  signature and one carries none. That one is
  `a30209bdc3a0af307a8b993ce63658a210251885`, "Remove a duplicate audit log
  path test". It reached `main` as the second parent of
  `eeae3bb2a425c4fe837921146da65f1f1e0ae576`, GitHub's merge of #1194 on
  2026-09-04. GitHub's commit API reads it as `verified: false`, reason
  `unsigned`.
- Signature status: `git log --format='%G?' origin/main | sort | uniq -c` under
  the default keyring gives 2,088 `G`, 851 `U` and 720 `N`. The 720 are the
  unsigned commit and the 719 SSH signatures, which this host cannot check:
  the command printed
  `gpg.ssh.allowedSignersFile needs to be configured and exist for ssh signature verification`
  719 times.
- Rules readable on `main` at 2026-09-14T23:26Z: ruleset `21830871`
  (`Required CI`) runs in `evaluate` mode with one rule, the required status
  check `invariants`, and no bypass actors. It is the repository's only
  ruleset, and `rules/branches/main` returns no active rule. Classic branch
  protection requires `invariants`, strict, with `enforce_admins` on and
  `required_signatures` off. The organisation's rulesets returned HTTP 404,
  and `gh` reported that the call needs the `admin:org` scope, which the token
  lacks.

No read available here shows whether anything refuses an unsigned commit before
it lands. The organisation's rules stay unread, and history holds only what
landed, not what was turned away. That answer will live in
[skills#1514](https://github.com/wildcat-finance/skills/issues/1514).

The header count came from this command, which printed
`3659 {'PGP': 2939, 'SSH': 719, 'none': 1} ['a30209bdc3a0af307a8b993ce63658a210251885']`:

```sh
python3 - b61f600e72fab94c6c71a4410cd5e6061d098762 <<'PY'
import collections, subprocess, sys, threading
revs = subprocess.run(["git", "rev-list", sys.argv[1]], capture_output=True, check=True).stdout.split()
batch = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
def feed():
    batch.stdin.write(b"\n".join(revs) + b"\n")
    batch.stdin.close()
threading.Thread(target=feed).start()
kinds, unsigned = collections.Counter(), []
for sha in revs:
    size = int(batch.stdout.readline().split()[2])
    header = batch.stdout.read(size + 1).split(b"\n\n", 1)[0].split(b"\n")
    signature = [line for line in header if line.split(b" ", 1)[0] in (b"gpgsig", b"gpgsig-sha256")]
    kind = b"none" if not signature else signature[0].split(b"BEGIN ", 1)[-1].split(b" SIGNATURE", 1)[0]
    kinds[kind.decode()] += 1
    if not signature:
        unsigned.append(sha.decode())
print(len(revs), dict(kinds), unsigned)
PY
```

The GitHub reads were these, read-only:

```sh
gh api repos/wildcat-finance/skills/commits/a30209bdc3a0af307a8b993ce63658a210251885 --jq '{sha, verification: {verified: .commit.verification.verified, reason: .commit.verification.reason}}'
gh api repos/wildcat-finance/skills/rulesets/21830871
gh api 'repos/wildcat-finance/skills/rulesets?per_page=100'
gh api repos/wildcat-finance/skills/rules/branches/main
gh api repos/wildcat-finance/skills/branches/main/protection
gh api orgs/wildcat-finance/rulesets
```

## Budget

Step 3 timed the checker over one bare candidate of 19 commits, with
`--base 592390722f10df53658906623b15428dbfb88d8f --head d66356556f6450d13b71e642678c701d7d603f5f --pull-request-login laurenceday`.
One run each took 676.718 ms with the base's checker and 643.703 ms with the
narrowed one, and both exited 0. The job allows `timeout-minutes: 5`
(`.github/workflows/identity.yml:23`), which is 300 s, so each run used under
0.23% of it. The run's audit record also holds 41 interleaved pairs, with p95
at 1,067.71 ms and 939.365 ms. This step changes neither the checker nor the
workflow.

## Fail-closed posture

Three refusals keep a receipted range the range that was pushed: an unsigned
commit, a commit altered after signing and a commit GitHub signed with its
web-flow key. The prover exits 0 only while all three still fire with
`hexctl.py`'s own message. It exits 1 when one is accepted or refused with
something else, and 3, writing nothing, when it cannot establish a
precondition, such as a keyring that validates GitHub's keys. Study section 11
stops the run when any of the three stops firing. The study amendment of
2026-09-14 reads that stop under a keyring without GitHub's keys, which is the
keyring this step's exit names for the prover.

## What this does not establish

These results cover the named objects and commands on the named trees. The
specimens are local objects, and none was pushed. A valid signature says
nothing about who wrote a commit or who may publish it. Nothing here shows
future GitHub state, the merge of this run, or a rule in the organisation's
settings.
