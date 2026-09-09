# Study: retire the Shoggoth cosignature and the host authorship ban

Task issue: [skills#1135](https://github.com/wildcat-finance/skills/issues/1135)
(framework-79), body plus the Creator's comment of 2026-09-09 and the Creator's
starting-position decision of the same day.

## Assumptions

These are the readings this study proceeds on. Correct any of them and the
section that rests on it changes.

1. The interpreter is the one in `.python-version`, `3.14.6`, with stdlib
   `unittest`. No dependency is added.
2. The starting ref is `main` at `59239072`. Step 1 then merges branch
   `d9114b65` into the run branch, so every later step's entry state contains
   both trees.
3. The Creator's four answers of 2026-09-09 and the starting-position decision
   of the same day are fixed intent. This study satisfies them; it does not
   reopen them.
4. The live ruleset for `main` already dropped the `identity` required status on
   2026-09-08, and that state persists whatever this run does. Read back on
   2026-09-09: ruleset `21830871` (`Required CI`), `enforcement: evaluate`, one
   `required_status_checks` rule whose only context is `invariants`. Classic
   branch protection on `main` answers `Branch not protected`.
5. Organisation-level rulesets need `admin:org`, which the reading token does
   not hold. Whether an organisation rule requires signed commits could not be
   established from here, and this study does not assume either answer.
6. Branch `fiat/1135-retire-mandatory-shoggoth-co-signature-and` at `d9114b65`
   is material to salvage, not prior art to abandon. The Creator decided this on
   2026-09-09, reversing the reading the first pass of this study proceeded on.
   Its 73 changed files are adopted except where they contradict an answer.
7. The preserved-record glob `docs/*/study.md` names the hundred design records
   held in subdirectories of `docs/`. The prior run's records are top-level
   files, `docs/shoggoth-signature-only-retirement-study.md` and
   `-runbook.md`, so they fall outside that glob. This study reads them as
   amendable rather than frozen and appends to them rather than editing a line.
   Section 12 records the reading; it is the one open question in the hand-back.

The fate of `.claude/settings.json` has no Creator answer at all. Section 12
carries the reading this study proceeds on and says plainly that it is a
reading.

## 1. Problem statement

Two identity rules are withdrawn together, and after they go a verified
signature is the only identity requirement a commit has to meet.

The mandatory Shoggoth co-signature goes: `Co-authored-by: Shoggoth
<shoggoth@wildcat.finance>` and `Wildcat-Origin: shoggoth` stop being required
anywhere. Shoggoth may still author, sign and be credited where that is what
happened. The runtime-host authorship ban goes with it: a runtime host is no
longer refused as author, committer, co-author, pull-request opener, byline or
generated-by line.

The users are the people who publish into `wildcat-finance/skills`. Two groups
feel this differently. A contributor running Fiat through Claude Code, Codex,
Cursor or another harness currently has to strip the harness's own attribution
before every commit and add two trailers that describe nothing about their work.
A contributor opening a pull request without Fiat currently meets the same rules
through the `identity` status. After this lands, both sign and publish under
their own identity and nothing else is checked about who they are.

A working prototype here means the enforcement is gone from code rather than
from prose, that the signature gate that remains still refuses what it refused
before, and that the two rules the Creator kept still hold. Five specimens
settle it:

- A signed commit whose author is a runtime host, carrying no provenance
  trailer and a `Generated with Claude Code` line in its message, passes
  `hexctl` local range verification.
- The same commit unsigned is refused, with the same message the current
  controller gives.
- The same commit signed by GitHub's web-flow key is refused at
  `hexctl.py:12764`, which the Creator's answer 4 fixes as expected behaviour.
- `python3 scripts/contributors.py --check` still exits zero, still excludes
  runtime hosts from the ranking, and `--verify-host-set` still reads a
  declaration out of `hexctl.py`.
- `python3 scripts/check_commit_identity.py` accepts that same host-authored
  commit and still refuses a malformed author identity. The prior run deleted
  this file; answer 2 brings it back narrower, so it needs a specimen of its
  own rather than a claim.

The proving demo path is a final-step demonstration document recording those
five specimens against the built tree, each with its exact command, its exit
status and the commit object it ran on. The mechanical exit for that step is
`python3 scripts/run_checks.py` green on a clean tree, plus
`python3 plugins/hexaemeron/tests/run_tests.py`.

## 2. Prior art

### The prior run is the material this one starts from

A Fiat run against this same issue ran to Step 4 and merged four step pull
requests into its own run branch between 2026-09-07 and 2026-09-08:

| PR | Title | Merged into |
| --- | --- | --- |
| [#1430](https://github.com/wildcat-finance/skills/pull/1430) | Preserve the signature-only retirement specification | the run branch |
| [#1455](https://github.com/wildcat-finance/skills/pull/1455) | Make Fiat admission signature-only | the run branch |
| [#1459](https://github.com/wildcat-finance/skills/pull/1459) | Retire the hosted identity status | the run branch |
| [#1481](https://github.com/wildcat-finance/skills/pull/1481) | Demonstrate signature-only Fiat admission | the run branch |

The run branch is `fiat/1135-retire-mandatory-shoggoth-co-signature-and` at
`d9114b653772dd6ba09a81d7af8ccc1943f23042`. Its merge base with `main` is
`3cc0ad7f521985e46cf29f364a20e19fa99b64dd`; against that base it changes 73
files, `+1522 / -2183`. It is 149 commits behind `main` and 16 ahead, and it
was never merged into `main`.

The first pass of this study treated that branch as prior art to abandon and
proposed rebuilding its work from `main`. The Creator reversed that on
2026-09-09: salvage from it. So Step 1 merges `d9114b65` into a branch cut from
`main` at `59239072`, and the run reworks only what contradicts an answer.

`git merge-tree --write-tree --name-only main d9114b65` conflicts on exactly ten
paths, and every one is a regenerable artefact or a version pin:

| Conflicted path | What it is |
| --- | --- |
| `.agents/plugins/marketplace.json` | generated marketplace manifest |
| `.claude-plugin/marketplace.json` | generated marketplace manifest |
| `.horos/boundary.json` | generated reading boundary |
| `.horos/candidates.json` | generated boundary candidates |
| `.horos/census.json` | generated byte census |
| `plugins/hexaemeron/.claude-plugin/plugin.json` | plugin version pin |
| `plugins/hexaemeron/.codex-plugin/plugin.json` | plugin version pin |
| `plugins/hexaemeron/tests/test_phylax_model_proxy.py` | asserts the plugin version, `1.6.29` against the branch's `1.6.30` |
| `tests/promise_machine_coverage.json` | generated promise coverage map |
| `tests/test_version_propagation.py` | asserts the same version pin |

No substantive product file conflicts. Both version-pin conflicts are the
collision this repository has seen before: two runs pick a plugin version
independently and nothing reports it. They are resolved by re-pinning to the
version this run resolves at integration, not by choosing a side.

### The two places the branch contradicts an answer

Everything else the branch did is consistent with the Creator's answers. These
two are not, and each was read out of the branch's bytes.

**It deletes the identity checker.** `scripts/check_commit_identity.py` goes,
together with `.github/workflows/identity.yml` and `tests/test_commit_identity.py`.
Answer 2 keeps that policy alive under a narrower promise: the bounded-read
rules stay, and only the trailer mandate and the host ban come out. On
`59239072` the file carries 42 `raise Refusal` sites. Eight of them state a rule
that is being withdrawn:

| Line | Refusal |
| --- | --- |
| `:213` | ambiguous Shoggoth author or committer identity |
| `:215` | a runtime host as author or committer |
| `:244` | a runtime-host generated-by byline |
| `:259` | a runtime host as co-author |
| `:265` | ambiguous Shoggoth co-author identity |
| `:269` | fewer or more than one exact Shoggoth co-author trailer |
| `:273` | fewer or more than one exact `Wildcat-Origin` trailer |
| `:307` | a pull request opened by a runtime-host account |

The other 34 survive, and so do `COMMIT_COUNT_MAX`, `COMMIT_BYTES_MAX`,
`COMMIT_TOTAL_BYTES_MAX`, `GIT_OUTPUT_MAX` and `GIT_TIMEOUT_SECONDS`. One
consequence is worth stating before it is discovered: `contributors` is imported
at `:15` and used at exactly three sites, `:214`, `:258` and `:306`, all three of
which are in the removed set. The narrowed checker therefore stops importing
`contributors` at all, which removes a runtime coupling between a CI script and
a ranking script that had no other reason to exist.

**It rewrites the contributor ranking promise and severs the parity anchor.** In
`scripts/contributors.py` it renames `HOST_IDENTITY_NAMES`,
`HOST_IDENTITY_EMAILS` and `HOST_PR_LOGINS` to `NON_HUMAN_*`, deletes
`host_set_payload`, `frozensets_from_source` and `verify_host_set_parity`, and
drops the `--host-set` and `--verify-host-set` arguments. In `hexctl.py` it
deletes the three matching frozensets outright, so nothing is left to compare
against. In the promise text it changes `absent from the declared runtime-host
set` to `outside the local non-human set`, `non-host authorship` to
`human-only`, drops the `hexctl.py` parity check from the Evidence line, and
appends `Fiat admission ignores this ranking.` Answer 1 has that promise
standing as written and the exclusion surviving.

The promise appears in more copies than the packet named. A scan of
`59239072` for the promise opening finds it in 19 files: the root
`PROMISE_MACHINE.md` and 18 plugin mirrors, not 16. The branch rewrites the same
four fields and appends the same comment in every one of the 19; `git diff
--numstat` reports `5 4` for each. The contributor-ranking section is
byte-identical between the merge base and `main`, so restoring those four fields
restores each file exactly to `main`'s bytes.

**One inconsistency inside the branch itself.** The branch deletes
`.claude/settings.json`, and its own `INSTALL.md:109` still reads `The
repository carries .claude/settings.json with one object`. That line is
inherited unchanged; the branch edited only the paragraph below it. So the
branch ships documentation for a file it removed. Keeping the file makes the
branch's own adopted `INSTALL.md` true. That is evidence for the reading in
section 12, not a Creator answer.

**A test that has to invert.** The branch adds
`tests/test_ruleset_identity_retirement.py`. Its `RulesetComparatorTests` are
the ruleset evidence and are adopted whole. Its `RetiredSurfaceTests` assert
four absences that the answers reverse: `.github/workflows/identity.yml` and
`scripts/check_commit_identity.py` absent (`:96`, `:97`),
`.claude/settings.json` absent (`:100`), the five `HOST_*` and `is_host_*` names
absent from `contributors.py` (`:102`), and `"identity.yml"` absent from
`tests/test_python_contract.py` (`:112`). Each becomes a presence assertion.

### Carried forward from the last two merged pull requests

PR #1481 is the last pull request that run landed. Its body carries three open
items, and adoption changes what happens to two of them:

1. Final integration, version resolution and ADR assignment remain pending.
   Carried forward as content: this run owns integration, its own Fiat version
   row, and the superseding decision records in section 12. The two version-pin
   conflicts above are the same item surfacing as a merge conflict.
2. The external Interceptor repository is outside scope. Carried forward as a
   stated non-goal in section 3.
3. A complete checked-runner invocation was red on a stale census and a nested
   suite timeout, and was not counted as green. Carried forward as a risk:
   section 5 carries `census-currency`, and every step exit in the runbook names
   the root suite rather than a subset. Adoption makes this sharper, not
   softer: `.horos/census.json` is one of the ten conflicted paths, so the
   census is regenerated during Step 1 rather than inherited stale.

PR #1459 carries the ruleset evidence and no unfinished work of its own beyond
what #1481 restates. That evidence is now doubly sourced. The live read on
2026-09-09 returns `enforcement: evaluate` with `contexts: ["invariants"]`, and
the branch's own fixtures record the same transition: `preimage.json` holds both
`identity` and `invariants` under `integration_id` 15368, `postimage.json` holds
`invariants` alone, and both name ruleset `21830871` in
`wildcat-finance/skills`. Adopting the fixtures brings that evidence onto the
run branch instead of leaving it reachable only from an unmerged branch.

Two further pull requests reached `main` from that work under `codex/1135-*`
branch names, on a different subject. [#1499](https://github.com/wildcat-finance/skills/pull/1499)
taught the Hypomnema decision allocator to number an inherited draft whose bytes
did not change, and [#1500](https://github.com/wildcat-finance/skills/pull/1500)
used it to assign ADR-087. Both are on `main` at `59239072`. They matter here
because the branch's unnumbered draft at
`docs/decisions/drafts/accept-any-validly-signed-authorship.md` is adopted and
rewritten, and the allocator that numbers it at integration is the one those
pull requests fixed.

### What enforces the two rules, and what the merge already removes

Every line below was resolved against `59239072` on 2026-09-09. The issue's own
numbers were taken before recent merges and most of the `hexctl.py` ones have
moved. The third column says whether the merge in Step 1 has already removed
the site, so that later steps are not asked to delete something that is gone.

Trailer mandate, four sites:

| Site | Rule | After the merge |
| --- | --- | --- |
| `hexctl.py:12841` | exactly one `Co-authored-by: Shoggoth` line on every locally verified commit | removed |
| `hexctl.py:12846` | exactly one `Wildcat-Origin: shoggoth` line on the same | removed |
| `check_commit_identity.py:269` | the same pair, applied when the author is exactly Shoggoth | file deleted; returns without these |
| `check_commit_identity.py:273` | the `Wildcat-Origin` half of that pair | file deleted; returns without these |

The `hexctl.py` pair applies to every commit in a receipted range, human-authored
ones included. The issue named `hexctl.py:11258`; on this base it is two
statements at `:12841` and `:12846`.

Host ban in Fiat, ten guards, all removed by the merge:

| Site | Refuses |
| --- | --- |
| `hexctl.py:12424` | a host login on a GitHub-linked commit account |
| `hexctl.py:12469` | a host co-author trailer read from the GitHub payload |
| `hexctl.py:12801` | a host as local commit author |
| `hexctl.py:12812` | a host as local committer |
| `hexctl.py:12829` | a host co-author trailer read locally |
| `hexctl.py:12834` | a host generated-by byline in the commit message |
| `hexctl.py:13224` | a host account as pull-request opener |
| `hexctl.py:13236` | a host byline in the pull-request body |
| `hexctl.py:13363` | a host as author in the GitHub attribution record |
| `hexctl.py:13369` | a host as committer in the same record |

Two of the ten are the `HOST_BYLINE_RE` searches at `:12834` and `:13236`; the
rest go through `is_host_identity` at `hexctl.py:12387` or a direct
`HOST_PR_LOGINS` membership test. Twelve refusal sites in `hexctl.py` in total,
counting the two trailer statements. The first pass of this study put that
figure at fourteen and tabulated ten; the count above is the one the audit's
`residual-refusal` check compares against.

Host ban in CI, four sites: `check_commit_identity.py:215` (author or
committer), `:244` (generated-by byline), `:259` (co-author), `:307`
(pull-request opener). The merge deletes the file; the narrowed file returns
without them.

Ambiguous-Shoggoth refusals, two sites: `check_commit_identity.py:213` for an
author or committer identity that half-matches Shoggoth, and `:265` for a
co-author trailer that does. Answer 3 removes both, and the narrowed file
returns without them.

Declarations rather than refusals, which is what the selected design turns on:
`hexctl.py:12223` and `:12224` hold the two trailer constants, `:12250`,
`:12268` and `:12274` hold the three frozensets, `:12313` holds `HOST_BYLINE_RE`
and `:12387` holds `is_host_identity`. The merge deletes all of them.
`retain-declaration` restores exactly three: the frozensets. It does not restore
`is_host_identity`, `HOST_BYLINE_RE` or the trailer constants, because
`verify_host_set_parity` reads frozensets by AST and skips everything else, so
those four would be dead weight buying nothing.

Classification sets: `scripts/contributors.py:38`, `:56` and `:62`, with the
predicates at `:111` and `:119` and the source-read parity check at `:191`. The
parity check AST-parses `hexctl.py` and refuses when the two files' `HOST_*`
frozensets differ in either direction, or when either file grows a `HOST_*`
frozenset the other lacks. The merge renames all of it; the run reverts the
rename.

Trailer instructions in prose: `plugins/hexaemeron/agents/mason.md:69`,
`plugins/hexaemeron/agents/warden.md:110`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md:59`, and the push
paragraph of `plugins/hexaemeron/skills/fiat/SKILL.md:590` with its rule at
`:784`. All four files are adopted from the branch unchanged.

### Coupled surfaces

`SHOGGOTH.md` carries `contract=shoggoth-collective/v4` at line 3 on `main` and
states the host ban in prose in its `AUTHORSHIP AND HOST PROVENANCE` section.
The branch raises it to `shoggoth-collective/v5`, replaces that section with
`AUTHORSHIP AND SIGNATURES`, and re-pins the digest in
`tests/test_shoggoth_identity.py:11` from
`443791a7d70daaa89f3422069a725d52e64f007e20d07bbc4fa9046c8e49cbb1` to
`8fc95b7e33d0dddb07671a641cebaadc17afe977ea3afcb1c419b602304aad4a`. That second
value matches the branch's own bytes, checked by hashing them. The v5 text says
nothing about the identity checker and keeps human-contributor recognition as a
separate concern that may exclude non-human accounts, so it satisfies both
answers and is adopted unchanged, digest and all. The version bump is required
either way. `SHOGGOTH.md` is a portable root file at
`scripts/portable_promise_machine.py:43`; the runtime mirror directory
`.agents/skills/promise-machine/runtime` is absent from this base, so mirror
closure is checked by running `portable_promise_machine.py check` rather than by
editing a second copy by hand.

`PROMISE_MACHINE.md:344` is the contributor-ranking promise. Its Evidence field
names "the host-set parity check against `hexctl.py`'s declaration" and its
Refuses field names "a host set diverged from `hexctl.py` in either direction".
Answer 1 says that promise stands as written, which is the single constraint
that decides section 4: `hexctl.py` has to keep declaring the three frozensets
even after nothing in `hexctl.py` refuses on them.

`.github/workflows/identity.yml` publishes the `identity` status from base-owned
policy under `pull_request_target`, with a five-minute job timeout at line 23.
The merge deletes it; answer 2 brings it back, because a narrowed checker that
nothing runs is a narrowed promise nobody keeps.

`INSTALL.md:109` documents `.claude/settings.json`. The file is present on
`59239072` and deleted by the branch, while `INSTALL.md:109` survives the branch
unchanged.

ADR-016 and ADR-058 hold the two decisions. Both need superseding records rather
than edits; ADR-052 sits between them and is not withdrawn by this change.

### Audit records read

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 from the target root over all 78 source-and-view pairs, every one
reporting `committed=match`. A verified synopsis is therefore the normal reading
view for every in-scope source.

In-scope sources and what was read:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | whole-set check exits 0; the source is 425 `h2` sections and the view carries the ids and fields |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | same check, `budget=pass`, `committed=match` |
| `audit/rounds/fiat-617-runtime-host-reinstates-the-byline-the-ident.md` | its `.synopsis.md` | same check; this is the round that widened `HOST_BYLINE_RE` |
| `audit/rounds/fiat-621-isolate-disposable-fixture-signing.md` | its `.synopsis.md` | same check |
| `audit/rounds/fiat-857-framework-16-the-commit-gate-lives-in-one-cl.md` | its `.synopsis.md` | same check |
| `audit/rounds/fiat-1135-retire-mandatory-shoggoth-co-signature-and.md` | its `.synopsis.md`, read from `d9114b65` | not on `59239072`, so the branch blob is the source; Step 1 brings both files onto the run branch, where they become preserved records |

The synopsis was read, not the source, for every row above. No finding id or
status was dropped: the root synopsis carries `[missing legacy field: covered]`
and the other three legacy markers on its pre-`v2` rounds, and those stay
unknown rather than being filled in.

The round that bears directly on this change is `fiat-617`. Its Step 1 covered
ids include `byline-widening-scope`, `no-host-identity-accepted` and
`human-authorship-preserved`, all reviewed, Elenchus verdict `passed`. Its
`Leads not pursued` records that the widened `HOST_BYLINE_RE` searches
unanchored, so descriptive prose such as "the fixtures were generated with
Copilot's help" or "regenerated with Claude" in a governed commit or
pull-request body is refused beside the attribution line it was aimed at. That
lead was accepted and left open. The merge closes it by removing the byline
searches, and this study records that as a consequence rather than as new work.

Its Step 2 findings `S2-R1-01` and `S2-R1-02` are both prose repairs, both
recorded as fixed, and both live in files the branch already touched:
`docs/how-to-help-shoggoth.md` and
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`. Both are adopted
unchanged. Neither reopens.

The prior 1135 round's `Leads not pursued` fields carry nothing this run must
answer. The nearest is its Step 2 note that "Runtime-host refusals under
`scripts/check_commit_identity.py` belong to the hosted identity workflow that
Step 3 removes"; that reasoning is what the Creator's answer 2 overrules, and
section 4 answers it by bringing the file back narrower.

### Outside this repository

`git verify-commit` and `git log --pretty=%GK` are the whole of the surviving
signature check; Git's own documentation defines their exit statuses and the
`%GK` key field. GitHub's commit API `verification` object supplies `verified`
and `reason`, which `hexctl.py` compares at `:13345` and `:13347`. The
`Co-authored-by:` trailer is a GitHub convention over the `git interpret-trailers`
format, not a standard; nothing outside this repository requires it. GitHub's
web-flow signing keys `4AEE18F83AFDEB23` and `B5690EEEBB952194` are the public
identifiers `hexctl.py:12231` uses to explain a refusal.

### The named dependency this run does not absorb

[skills#1514](https://github.com/wildcat-finance/skills/issues/1514)
(framework-157) asks whether anything readable enforces the signed commits this
repository documents at `.github/workflows/contributors.yml:108`. This run does
not answer it. The decisive experiment that issue names, pushing an unsigned
commit to a throwaway branch, writes to the shared repository and is out of
scope here. Section 3 states the boundary and section 12 records where the
answer will live when #1514 produces it.

## 3. Constraints and non-goals

**Starting ref.** `main` at `59239072`. Branch
`fiat/1135-retire-the-shoggoth-cosignature-and-host-au`, cut from that ref.
Step 1 merges `d9114b65` into it and regenerates the ten conflicted artefacts.

**Toolchain.** Python `3.14.6` from `.python-version`, stdlib `unittest`, no new
dependency. Checks are `python3 scripts/run_checks.py` and
`python3 plugins/hexaemeron/tests/run_tests.py`. The Hexaemeron suite needs its
own parallel runner; `unittest discover` under that tree reports an import error
that reads as a clean suite.

**Fixed by the Creator, not open here.** The prior branch is salvaged rather
than rebuilt. `CONTRIBUTORS.md` keeps excluding runtime hosts.
`check_commit_identity.py` survives under a narrower promise. The
ambiguous-Shoggoth refusals go. Fiat keeps verifying signatures on commits it
did not create, and the GitHub-signed refusal at `hexctl.py:12764` is expected
behaviour.

**Preserved records.** These keep their bytes: `audit/rounds/*`, including the
prior run's own round record and synopsis once the merge brings them in;
ADR-016, ADR-019, ADR-058; every `docs/*/study.md` and `docs/*/runbook.md`
design record; the Hexaemeron `docs/*/proof.md` records; and
`plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/samples.jsonl`.
They record what was required when they were written.

**Non-goals.**

- The external Interceptor repository. It carries its own copy of the rule and
  is not in this tree.
- Issue #1514's question. Named as a dependency, not absorbed.
- Rewriting history. Every existing commit keeps its trailers and its author,
  and the prior branch's 16 commits are merged rather than replayed.
- Re-running the prior branch's four step pull requests. They are merged work,
  not work to redo.
- Changing what `CONTRIBUTORS.md` ranks or how it orders.
- Any further live mutation of repository or organisation configuration. The
  prior run's Step 3 already removed `identity` from ruleset `21830871`, and
  this run reads that state rather than changing it again.

**Always.** Both suites green before a commit. The Imprimatur lint on every
shipped document. `audit_synopsis.py --check .` exit 0 before a receipt.
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
after any tracked-file edit, because the census currency tests read byte counts.

**Ask first.** Any change to `.github/workflows/`. Any change to a ruleset or
branch protection. Deleting `.claude/settings.json`. Widening what
`check_commit_identity.py` reads. Bumping the `shoggoth-collective` contract
version beyond the `v5` the branch already sets. Resolving one of the ten
conflicted artefacts by editing it rather than regenerating it.

**Never.** Edit a preserved record's bytes. Take a merge conflict's resolution
from either side when the file is generated. Claim an organisation-level rule
exists without reading it. Delete a failing test to make a suite pass.

## 4. Design options

Four constructions were drawn. Every one of them now starts from the same
place, because the Creator fixed the starting position: the branch is merged in,
and the ten conflicted artefacts are regenerated. What separates the candidates
is what each one reverts or rewrites on top of that merge. The prose below
explains what each one is; the closed record at
`.hexaemeron/design-evidence.json` selects between them from checked results,
and section 4 does not choose in prose.

**`retain-declaration`.** Adopt the merge, then restore three surfaces.
`contributors.py` gets back its three `HOST_*` frozensets, both predicates,
`host_set_payload`, `frozensets_from_source`, `verify_host_set_parity` and the
two arguments that expose them. `hexctl.py` gets back its three frozensets and
nothing else, so `verify_host_set_parity` has a declaration to read and the
contributor-ranking promise at `PROMISE_MACHINE.md:344` returns byte-identical,
in that file and in all 18 mirrors.
`scripts/check_commit_identity.py` returns with its bounded reads, its 34
surviving refusals and no import of `contributors`, and
`.github/workflows/identity.yml` returns to publish an advisory status under
that narrower promise.
*The trade:* `hexctl.py` carries three frozensets that nothing in `hexctl.py`
reads. That is dead weight to a reader and to the dead-code analyser, bought so
the parity guarantee and the promise survive untouched.

**`record-attribution`.** As above, and `hexctl` additionally records a
host-attribution field on its push receipt, so the restored sets have a
behavioural consumer inside Fiat rather than existing only as a parity anchor.
*The trade:* the sets stay live, at the cost of a new receipt field, a new
identifier and a version-1 receipt shape that the run then has to keep.

**`single-owner`.** Adopt the merge's `hexctl.py` and its rewritten promise as
they stand, and restore only the identity checker. `contributors.py` gets its
`HOST_*` names back but not `verify_host_set_parity`, because there is nothing
left to compare against.
*The trade:* the cleanest end state, no duplicated declaration and no dead code,
and 20 more of the branch's files kept as they are, bought by rewriting a
promise the Creator fixed as standing.

**`inherit-landed`.** Adopt the branch as it stands, resolving only the ten
conflicted artefacts.
*The trade:* a complete audited implementation for almost nothing, against a
design that deletes the checker and rewrites the promise.

### What the record measures

Five resolved criteria and one pending one, covering all five concerns. Three
candidates are declarations resolved against the bytes at `59239072` and at
`d9114b65`; `inherit-landed` is read out of the branch tree itself with `git
show`. `.hexaemeron/design-probe.py` produces every report. It refuses rather
than scoring when a declared anchor is absent from the bytes, when the branch
did not do what the salvage story assumes, or when a candidate names a rework
path the branch never changed, so a declaration cannot credit itself with a site
or a file that does not exist.

| Criterion | Concern | Kind | Owner |
| --- | --- | --- | --- |
| `creator-answers-satisfied` | correctness | gate, at-least 4 | protasis |
| `host-set-parity-anchor` | compatibility | gate, equals true | hypomnema |
| `salvaged-audited-files` | time | metric, maximise | hypomnema |
| `new-identifiers-introduced` | space | metric, minimise | phylax |
| `surviving-set-declarations` | space | metric, minimise | phylax |
| `signature-refusal-preserved` | recovery | gate, equals true, at `step:2` | elenchus |

The resolved matrix:

| Candidate | answers | parity anchor | salvage | new ids | sets |
| --- | --- | --- | --- | --- | --- |
| `retain-declaration` | 4, pass | true, pass | 30 | 0 | 6 |
| `record-attribution` | 4, pass | true, pass | 30 | 1 | 6 |
| `single-owner` | 3, fail | false, fail | 50 | 0 | 3 |
| `inherit-landed` | 2, fail | false, fail | 63 | 0 | 3 |

`salvaged-audited-files` counts, of the 73 paths the branch changed, how many
the end state keeps at the branch's own bytes. The ten conflicted paths are
charged to every candidate, because the merge pays for them whatever the end
state is.

### What moved, and what did not

The selection did not move. `retain-declaration` still wins under
`unique-frontier`, and the two candidates that fail a selection gate are still
`single-owner` and `inherit-landed`, for the same two reasons. Of the two
survivors, `retain-declaration` is no worse on every metric and strictly better
on `new-identifiers-introduced`, so it dominates `record-attribution` and the
frontier holds one candidate.

Two things did move, and both are worth saying out loud.

The `time` criterion changed identity. The first pass measured
`merge-conflict-paths`, which scored 0 for the three declarations and 10 for
`inherit-landed`, because only that candidate proposed a merge. Once the
Creator fixed the merge as the shared starting position, that metric became a
constant 10 across all four candidates and stopped discriminating between them.
`salvaged-audited-files` replaces it. The ten conflicted paths have not stopped
mattering; they moved from the matrix to `merge-resolution` in section 5 and to
Step 1's exit, which is where a shared cost belongs.

Salvage and the Creator's answers point in opposite directions, and the gates
decide. `inherit-landed` keeps 63 of the branch's 73 files and `single-owner`
keeps 50, against 30 for either surviving candidate. On salvage alone the
ranking would invert completely. It does not, because both high-salvage
candidates fail `creator-answers-satisfied` and `host-set-parity-anchor`, which
are hard gates and remove a candidate before the frontier is computed. The
selected design is the most expensive of the four in rework and the only one
that satisfies every answer. That is the trade this run makes, stated rather
than hidden in a preference.

`signature-refusal-preserved` is the only pending cell. It blocks `step:2` and
its resolver is `python3 tests/prove_signature_only_refusals.py`, a tracked
prover that step creates. Nothing about the built code is predicted here: the
unsigned and tampered refusals are asserted at the transition that can check
them.

### The rework surface, named

`python3 .hexaemeron/design-probe.py --candidate retain-declaration --surface`
prints the three lists below out of the branch's own changed set.

**Regenerated, 10.** The ten conflicted paths above. Both marketplace manifests,
the three `.horos` records and `tests/promise_machine_coverage.json` are
regenerated by their own generators. The two plugin manifests and the two tests
that assert the plugin version are re-pinned to the version this run resolves.

**Reverted to `main`'s bytes, 22.** `PROMISE_MACHINE.md` and its 18 plugin
mirrors, restoring the four promise fields and dropping the appended comment.
`tests/test_python_contract.py`, restoring the two `"identity.yml"` rows.
`.github/workflows/identity.yml` and `.claude/settings.json`, both restored from
deletion.

**Rewritten, 11.** `scripts/check_commit_identity.py` and
`tests/test_commit_identity.py`, restored and then narrowed.
`tests/test_host_settings.py`, restored and then narrowed, because its docstring
cites ADR-016 and claims Fiat "refuses the host defaults by name", which stops
being true. `scripts/contributors.py` and `tests/test_contributors.py`,
reverting the rename and the parity removal, then updating the comments that
cite the withdrawn rule. `hexctl.py`, keeping the branch's refusal removals and
restoring only the three frozensets with a comment stating why they stay.
`tests/test_ruleset_identity_retirement.py`, keeping `RulesetComparatorTests`
whole and inverting the four `RetiredSurfaceTests`.
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`, for this run's version row.
`docs/decisions/drafts/accept-any-validly-signed-authorship.md`, for the revised
decision. `docs/shoggoth-signature-only-retirement-study.md` and `-runbook.md`,
by appended amendment only.

**Adopted unchanged, 30.** `AGENTS.md`, `INSTALL.md`, `README.md`, `SHOGGOTH.md`
and `plugins/hexaemeron/AGENTS.md`. Both prior-run audit records. The Fiat
skill, both agent files, both references and `docs/how-to-help-shoggoth.md`.
`docs/shoggoth-signature-only-retirement-demonstration.md`, whose four specimens
are all signature-gate specimens and stay true under the revised design.
`plugins/hexaemeron/tests/hexctl_harness.py`, `host_identity_cases.py`,
`test_fiat_skill.py` and `test_hexctl.py`, which the branch already rewrote for
a `hexctl.py` that does not refuse on host identity, which is what the selected
design also produces. Both `tests/fixtures/ruleset-identity-retirement` files,
the seven `tests/fixtures/agent-instruction-v1` files, and
`tests/test_evolution_contract.py`, `test_marketplace_prose.py` and
`test_shoggoth_identity.py`.

## 5. Risk register seed

The register below is what the audit loop enumerates. Three of these are the
reason the run exists rather than ordinary hygiene. `promise-bytes` is the
constraint that decided section 4, because a promise whose Evidence field names
a parity check stops being true the moment the thing it parses is deleted.
`parity-anchor-dead` is the price of keeping it: three frozensets in `hexctl.py`
with no caller, which a dead-code analyser is entitled to flag and a reader is
entitled to delete. The comment that explains why they stay carries the entire
reason, and its absence is a defect even though every check stays green.

`salvage-drift` is new with the Creator's decision and is the risk that adoption
creates. The branch changed 73 files and the run reverts or rewrites 43 of them.
An adopted file that quietly asserts a withdrawn rule is invisible: it makes no
check red, because the branch's own suite was green on the branch's own design.
The check has to enumerate the adopted 30 against the answers rather than wait
for a failure.

`residual-refusal` keeps its own note. Section 2 enumerates twelve refusal sites
in `hexctl.py` and eight in `check_commit_identity.py`, and the audit checks the
count rather than the reading: one guard left behind refuses one contributor's
commit for a rule the repository has said it withdrew, and the refusal text will
still cite ADR-016.

```risk-register
salvage-drift | the 30 branch files adopted unchanged | each one is read against the four answers and none asserts a withdrawn rule, enumerated rather than inferred from a green suite
merge-resolution | the ten conflicted paths at Step 1 | every one is regenerated by its own generator or re-pinned to this run's resolved version, and none carries a hand-merged hunk
residual-refusal | every host and trailer guard named in section 2 | no path refuses on host identity or trailer count, checked by grep count against the section 2 tables rather than by reading
promise-bytes | PROMISE_MACHINE.md:344 and its 18 plugin mirrors | the contributor-ranking promise paragraph is byte-identical to 59239072 in all 19 copies
parity-anchor-dead | hexctl.py's three HOST_* frozensets after the merge removed every refusal | verify_host_set_parity still reads them, the dead-code check stays green, and a comment states why they remain
checker-narrowing | the 34 surviving refusals in check_commit_identity.py | the eight withdrawn refusals are gone, the other 34 still fire, and the file no longer imports contributors
signature-gate | hexctl.py:12764 and its GitHub-key branch | an unsigned commit, a tampered commit and a GitHub web-flow-signed commit are each still refused with their current message
promise-overreach | the narrowed check_commit_identity.py promise | what the narrowed promise claims matches what the file still executes, with no clause about attribution
preserved-record-drift | audit/rounds including the two adopted from the branch, ADR-016, ADR-019, ADR-058, docs design records, the labelled-prose corpus | git diff --no-renames over the whole range reports none of them as changed after the merge that introduced them
record-append-only | the prior run's docs/shoggoth-signature-only-retirement study and runbook | every change to them is an appended dated amendment and no existing line moves
shoggoth-digest | SHOGGOTH.md at v5, its contract version and its SHA-256 pin | the adopted digest 8fc95b7e33d0dddb07671a641cebaadc17afe977ea3afcb1c419b602304aad4a still matches the file, and portable_promise_machine.py check exits 0
ambiguity-loss | commits claiming a lookalike Shoggoth trailer | the two refusals are removed deliberately, and their absence is recorded in the superseding decision rather than discovered later
live-configuration | ruleset 21830871 and branch protection on main | the run reads the live state and mutates nothing; any observed drift is reported, not corrected
settings-file | .claude/settings.json, INSTALL.md:109 and the restored tests/test_host_settings.py | the file and INSTALL.md agree, and no adopted test asserts the state the run did not choose
census-currency | .horos/census.json against every tracked edit | horos scan --census --write ran after the last edit and the census currency tests are green
enforcement-gap | commits Fiat never receipts | the run states plainly what checks them, names #1514, and promises nothing about an organisation rule it could not read
```

## 6. Glossary seeds

- **Runtime host.** The software identity that executed a piece of work, such as
  Claude Code or Codex, as against the actor who contributed it. Mechanically:
  membership in `HOST_IDENTITY_NAMES`, `HOST_IDENTITY_EMAILS` or
  `HOST_PR_LOGINS`.
- **Provenance trailer.** One of the two exact lines `Co-authored-by: Shoggoth
  <shoggoth@wildcat.finance>` and `Wildcat-Origin: shoggoth`. After this change
  they are permitted and never required.
- **Parity anchor.** A declaration that exists so another module's source-reading
  check has something to compare against, not because the declaring module uses
  it.
- **Salvage surface.** The branch-changed paths an end state keeps at the
  branch's own bytes. Its complement is the rework surface: what the run
  regenerates, reverts or rewrites after the merge.
- **Adopted unchanged.** A branch file the run neither reverts nor rewrites, so
  its bytes reach `main` exactly as the prior run's audit saw them.
- **Advisory status.** A published commit status that no ruleset requires, so a
  red result is visible and does not block a merge. `identity` is one on this
  base.
- **Base-owned policy.** Code checked out from the protected base SHA and run
  against a candidate's objects, so the candidate cannot change the rule that
  judges it. `identity.yml` works this way.
- **Bounded read.** A `git` metadata call with a fixed argv, an output ceiling
  and a timeout, so a hostile object database cannot exhaust the checker.
- **Narrower promise.** A Promise Machine promise whose claim is reduced to
  match what the code still does, rather than left overstating it.

## 7. Sources

- [skills#1135](https://github.com/wildcat-finance/skills/issues/1135), body and
  the comment of 2026-09-09 recording the Creator's four answers, plus the
  Creator's starting-position decision of 2026-09-09.
- [skills#1514](https://github.com/wildcat-finance/skills/issues/1514), the
  signed-commit enforcement question this run depends on and does not answer.
- Pull requests [#1430](https://github.com/wildcat-finance/skills/pull/1430),
  [#1455](https://github.com/wildcat-finance/skills/pull/1455),
  [#1459](https://github.com/wildcat-finance/skills/pull/1459),
  [#1481](https://github.com/wildcat-finance/skills/pull/1481), the prior run's
  four merged steps; [#1499](https://github.com/wildcat-finance/skills/pull/1499)
  and [#1500](https://github.com/wildcat-finance/skills/pull/1500), the
  inherited-draft numbering fix that reached `main`.
- Branch `fiat/1135-retire-mandatory-shoggoth-co-signature-and` at `d9114b65`,
  merge base `3cc0ad7f52`, and its audit record at
  `audit/rounds/fiat-1135-retire-mandatory-shoggoth-co-signature-and.md` on that
  branch.
- `git merge-tree --write-tree --name-only main d9114b65` for the ten conflicted
  paths; `git diff --name-status 3cc0ad7f52 d9114b65` for the 73; `git grep -l`
  over `59239072` for the 19 files carrying the ranking promise.
- `tests/fixtures/ruleset-identity-retirement/preimage.json` and
  `postimage.json` on `d9114b65`, the bounded ruleset evidence.
- `docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md`,
  `ADR-052-separate-governed-authorship-from-publication.md`,
  `ADR-058-require-base-owned-identity-and-human-review.md`.
- `SHOGGOTH.md` at `contract=shoggoth-collective/v4` on `59239072`, digest
  `443791a7d70daaa89f3422069a725d52e64f007e20d07bbc4fa9046c8e49cbb1`, and at
  `v5` on `d9114b65`, digest
  `8fc95b7e33d0dddb07671a641cebaadc17afe977ea3afcb1c419b602304aad4a`.
- `PROMISE_MACHINE.md:344`, the contributor-ranking promise.
- `scripts/check_commit_identity.py`, `scripts/contributors.py`,
  `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
  `.github/workflows/identity.yml`, `.github/workflows/contributors.yml:108`,
  `INSTALL.md:109`.
- `audit/AUDIT_SYNOPSIS.md`, `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` and the
  four round synopses named in section 2, all after
  `audit_synopsis.py --check .` exited 0.
- GitHub REST reads on 2026-09-09: `repos/wildcat-finance/skills/rulesets/21830871`
  and `repos/wildcat-finance/skills/branches/main/protection`.
- Git documentation for `verify-commit` and the `%GK` pretty format; GitHub's
  commit `verification` object.

## 8. Signals, and the questions behind them

The identity workflow runs unattended on every pull request to `main`. The merge
deletes it and the run restores it, so the first question below is about a
workflow that went away and came back.

1. *A pull request went red on `identity`. Which rule refused, and is that rule
   one we still keep?* `check_commit_identity.py` prints `identity: <refusal>`
   to stderr and exits 2, and each refusal names its subject commit. The
   restored file keeps that shape and carries only the 34 refusals that still
   correspond to a rule, so a red status cannot cite a withdrawn one.
2. *Is the `identity` status still being published at all?* It is advisory now,
   so a workflow that silently stops running looks the same as a workflow that
   passes, and this run removed and restored the file that publishes it. The
   step that restores it reads the status back on its own pull request head and
   records the state and its Actions run link, which is the same evidence
   ADR-058 required at bootstrap.
3. *Which commits reached `main` unsigned?* Nothing this repository can read
   answers that today, which is #1514's subject. The final step records the
   question and the reads that failed to answer it rather than emitting a signal
   that would imply an answer.

What each of those signals must carry belongs to Ephoros, at
`plugins/hexaemeron/skills/ephoros/SKILL.md`.

## 9. Boundaries, per capability

Three boundaries open here, and the change narrows rather than widens all three.

**Candidate object database.** `check_commit_identity.py` reads a bare
repository whose objects come from a pull request. Worth taking: the commit
metadata needed to bound the read. The controls that close it are the ones
answer 2 keeps: `_repository_path` refusing a symlinked or non-bare path, the
fixed argv through `_git` with `GIT_CONFIG_NOSYSTEM` and a devnull global
config, `GIT_TIMEOUT_SECONDS`, `GIT_OUTPUT_MAX`, `COMMIT_COUNT_MAX`,
`COMMIT_BYTES_MAX` and `COMMIT_TOTAL_BYTES_MAX`. Removing the trailer and host
rules removes eight of the file's 42 refusals, so the surface shrinks; every
ceiling stays. Restoring the file after the merge deleted it is the point at
which a ceiling could go missing without anything noticing, so the restore is
checked against `59239072`'s bytes rather than retyped.

**Privileged workflow.** `identity.yml` runs under `pull_request_target` with
base-owned bytes and never checks out the candidate. That property is the whole
of ADR-058's security argument and this change does not touch it. The step that
restores the workflow does not add a candidate checkout, a candidate import or a
candidate-supplied argument.

**Signature verification subprocess.** `hexctl.py:12764` runs `git verify-commit`
with `SIGNATURE_VERIFIER_CONFIG` pinning the four verifier programs through
command-scoped `-c` settings, so repository-local config cannot substitute a
program. The branch leaves that control alone, and answer 4 keeps the gate.

The boundary list and the controls belong to Phylax, at
`plugins/hexaemeron/skills/phylax/SKILL.md`. Section 5's register carries the
same three as ids the audit enumerates.

## 10. The budget, or its absence

One budget applies and it already exists. `.github/workflows/identity.yml:23`
sets `timeout-minutes: 5` on the identity job, and the job fetches a filtered
pull-request history before running the checker. The narrowed checker removes
eight refusals and adds none, so the budget must still hold and no regression is
expected.

Measured how: run the checker against a bounded local range before and after the
change and compare wall time.

```bash
python3 scripts/check_commit_identity.py \
  --repository <bare candidate> --base <base sha> --head <head sha> \
  --pull-request-login <login>
```

The before-measurement is taken on `59239072`, where the file still exists in
full, and the after-measurement on the same range once the narrowed file is
restored. Both are recorded. There is no other budget: `hexctl` verification is
already bounded by the commit range a run receipts, and `contributors.py` is
rate-limited by GitHub rather than by this change.
What a budget carries and how it is checked belongs to Metron, at
`plugins/hexaemeron/skills/metron/SKILL.md`.

## 11. The fail-closed posture

What stops the run:

- A preserved record's bytes change. Detected by `git diff --no-renames` over
  the whole range against the preserved list in section 3. The two audit records
  the merge introduces are covered from the merge commit onward.
- The contributor-ranking promise paragraph stops being byte-identical in any of
  the 19 copies. Detected by comparing each copy against `59239072`.
- `verify_host_set_parity` loses its anchor, so
  `python3 scripts/contributors.py --verify-host-set` refuses.
- Any of the three signature refusals stops firing.
- A conflicted artefact reaches a commit with a conflict marker or a
  hand-merged hunk in it. Detected by `git diff --check` and by re-running each
  generator and finding no diff.
- `audit_synopsis.py --check .` exits non-zero.
- `python3 scripts/run_checks.py` is red on a clean tree. A dirty tree reddens
  the dead-code check on its own, so the runner is invoked on a clean tree or
  its result is not a result.

Guard-test convention: a fix that answers an audit finding lands with a test
that fails on the parent commit and passes on the fix, in the module that owns
the behaviour, named for the behaviour rather than the finding id. Each runbook
step names the exact Elenchus runner command with one `{report}` argument, the
report format and the report file, because Warden may not infer a command from
the step's `Files`.
The triage order and the guard rule belong to Elenchus, at
`plugins/hexaemeron/skills/elenchus/SKILL.md`.

## 12. Decisions and their homes

Five decisions here are expensive to reverse, and each gets a record.

1. **Withdrawing the host authorship ban and the trailer mandate.** This
   supersedes ADR-016's Decision paragraph and the identity-script paragraph of
   ADR-058. Neither is edited. The record is the branch's own unnumbered draft
   at `docs/decisions/drafts/accept-any-validly-signed-authorship.md`, adopted
   and rewritten for the revised design, which the Hypomnema allocator numbers
   at integration through the path `hexctl.py:8133` expects. Its slug and first
   heading stay fixed, because
   `docs/shoggoth-signature-only-retirement-demonstration.md` cites
   `adr/accept-any-validly-signed-authorship` and that file is adopted
   unchanged. The draft must state the ambiguity-refusal removal explicitly,
   because that refusal answered impersonation rather than attribution and its
   loss is the least obvious consequence of the change.
2. **Salvaging from `d9114b65` rather than rebuilding it.** This is the
   Creator's decision of 2026-09-09 and it is the most expensive one here to
   reverse, because reversing it means discarding 16 merged commits and four
   audited step pull requests. It belongs in the same draft's Context, with the
   salvage figure from section 4: 30 of 73 files adopted, 43 reworked, and the
   two answers that forced the difference.
3. **Keeping `hexctl.py`'s frozensets as a parity anchor with no caller.** This
   is the design choice section 4 selected and the one a later reader is most
   likely to undo by tidying, particularly now that the merge deleted them once
   already. It belongs in the same draft's Consequences, naming
   `contributors.py:191` and `PROMISE_MACHINE.md:344` as the reason.
4. **Narrowing the `check_commit_identity.py` promise.** The narrowed claim
   lives in the file's module docstring and in the same decision record. It says
   what the file establishes: a bounded, well-formed commit range under stated
   ceilings, and nothing about who authored it. The record also states that the
   file no longer imports `contributors`, so a later reader does not restore the
   coupling while restoring a refusal.
5. **`.claude/settings.json`.** No Creator answer covers it. This study's
   reading is that it stays, for three reasons: suppressing a host's automatic
   trailer is still useful when the trailer is noise rather than a refusal;
   `INSTALL.md:109` documents it and survives the branch unchanged, so deleting
   the file leaves adopted documentation false; and the prior runbook's own
   Step 3 made the deletion conditional on the file existing "solely to suppress
   the withdrawn host attribution", which `sessionUrl: false` does not. Deleting
   it is a live change to every contributor's checkout and stays on the
   ask-first tier. The runbook records the choice in the same decision record.

Two records that are not decisions but need a home. The prior run's
`docs/shoggoth-signature-only-retirement-study.md` and `-runbook.md` describe a
design this run reverses in two places. They are adopted, and each gets an
appended dated amendment naming the two reversals and pointing at the decision
draft rather than restating it. No existing line in either file moves. Assumption
7 records that this study reads them as outside the preserved `docs/*/study.md`
glob; if that reading is wrong, both amendments become forbidden and this run
writes its own design records at fresh paths instead.

Issue #1514's answer, when it lands, belongs in its own record and not in this
one. Which decisions earn a record and where each one lives belongs to Hypomnema, at
`plugins/hexaemeron/skills/hypomnema/SKILL.md`.
