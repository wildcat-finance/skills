# Study: publish the ranked human contributor list

Task issue: https://github.com/wildcat-finance/skills/issues/515
Run branch: `fiat/515-publish-the-ranked-human-contributor-list`
Base: `main` at `dd23413ef6e9021bd80b930ad57e1766bf166f0b`

Assuming, unless corrected:

1. Python 3.9 and the standard library only, matching `scripts/promise_machine.py`
   and `scripts/run_observation.py`. The root CI matrix runs 3.9 through 3.13,
   so the generator has to hold at the floor.
2. Stdlib `unittest`, discovered by `python3 -m unittest discover -s tests`,
   matching every other root test.
3. The generator reads the GitHub REST API over HTTPS and the local git history.
   It writes no credential and needs no write scope of its own.
4. The repository owner is excluded from both outputs. This came from the
   Creator directly and is not derived from the repository.
5. The refresh runs weekly and on manual dispatch, not per merge. Also the
   Creator's decision.
6. GitHub Actions is the trigger host. The generated pull request touches only
   `CONTRIBUTORS.md` and `README.md`, so `GITHUB_TOKEN` suffices at run time.

## 1. Problem statement

`README.md:57` tells a prospective contributor that a merged job with their
authorship intact means "GitHub adds you to this repository's contributor list
automatically." That sentence is accurate about GitHub's Insights graph and
about nothing else. There is no `CONTRIBUTORS.md`, the graph is not ranked, and
the graph does not separate the humans who supplied judgement from the runtime
identities that produced most of the commits.

This run builds a generator that reads the repository's own history, ranks the
human contributors by merged work, and writes two artefacts from one
computation: a ranked `CONTRIBUTORS.md` at the repository root, and a block at
the bottom of `README.md` that thanks the same people by GitHub handle and
carries no other data. A weekly workflow reruns it and opens a pull request only
when the ranking changed.

A working prototype means this command, run in a clean checkout, reproduces the
committed files byte for byte and exits 0:

```bash
python3 scripts/contributors.py --check
```

and this one rewrites both artefacts in place:

```bash
python3 scripts/contributors.py --write
```

## 2. Prior art

**In this repository.**

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:2798` holds the mechanical
host-identity set that ADR-016 refers to: `HOST_IDENTITY_NAMES` with fourteen
entries, `HOST_IDENTITY_EMAILS` with two, `HOST_PR_LOGINS` with five, and
`is_host_identity(name, email)` over the first two. Fiat already uses it to
reject a host identity in a receipted commit range. This run consumes the same
set rather than writing a second one, because two sets that must agree and are
not checked against each other will stop agreeing.

`docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md` is the
governing decision. Three of its clauses control this design. Governed agent
work is authored by Shoggoth, so a host identity is never a contributor. Human
contributors keep human authorship, with Shoggoth provenance added rather than
substituted, so a human who ran Fiat is still a contributor. And the rule is
prospective: history was deliberately not rewritten, so 174 commits authored by
`Claude <noreply@anthropic.com>` remain in `main` and the generator meets them
every run.

ADR-016's consequences section names the gap this run inherits: "prose still
owns unfamiliar future host names until the mechanical set is extended." A host
GitHub adds next year is not in the frozensets, so the generator cannot classify
it. Item 11 says what it does instead.

`scripts/promise_machine.py` and `scripts/run_observation.py` establish the root
script conventions: `from __future__ import annotations`, `argparse`,
`pathlib`, stdlib only, and a `--check` mode separate from a writing mode.
`tests/test_shipped_prose_lints.py` and `tests/test_evolution_contract.py`
establish that a root test may read repository files and assert on them.

`.github/workflows/sync-skills-marketplace.yml` is the closest workflow. Its
comment block records the constraint this run has already hit: GitHub refuses
any push that creates or updates a file under `.github/workflows/` unless the
token holds the Workflows permission, and `GITHUB_TOKEN` can never hold it.
That workflow solves it with a fine-grained `MARKETPLACE_SYNC_TOKEN`. This run
does not need to, because its generated pull request touches no workflow file.
The constraint applies only to the human or agent committing the new workflow
file itself, once.

`.github/workflows/pandects.yml:30` pins the root matrix at Python 3.9 and 3.13
and runs `python3 -m unittest discover -s tests -v`.

**Unfinished work carried forward.** Issue #466, framework-7, is open and
adjacent. It binds contributor authorship *at integration time* so the evidence
is correct when it lands. This run consumes whatever evidence exists and does
not change how integration binds it. #466 is a stated dependency, not a
non-goal: until it lands, a merge strategy that discards authorship silently
reduces a contributor's rank, and this run cannot detect that. Recorded here and
in the issue rather than solved.

**Audit records.** `audit/AUDIT.md` is 11,454 lines and holds no finding about
a contributor list, contributor attribution, or `CONTRIBUTORS.md`. Its
attribution findings, S4-R1-01 and S5-R1-01, concern Janus effect attribution in
Solidity and do not bear on this. No prior round has judged this question, so
nothing is being reopened.

**Outside.** The `all-contributors` specification and its bot are the common
answer to this problem. They key on a manually curated JSON file and a bot
responding to comment commands, which is a second source of truth maintained by
hand. `github-contributors` style actions read the contributors API and render a
table, but none of them know about `Wildcat-Origin`, ADR-016, or the
distinction between a human running an agent and an agent running itself. The
GitHub REST endpoints in scope are `GET /repos/{owner}/{repo}/contributors`,
which resolves several author emails to one account, and
`GET /search/issues` for merged pull requests by author.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `main` at `dd23413ef6e9021bd80b930ad57e1766bf166f0b`. Entry tree
  is green: 192 root tests pass.
- Python 3.9 floor, standard library only. No new dependency, so no lockfile.
- Stdlib `unittest` under `tests/`, discovered from the repository root.
- The generator reads public repository metadata. It records no private account
  data, no email address, and no token.
- Both artefacts derive from one computation in one process, so they cannot
  disagree.
- The `README.md` block carries GitHub handles and nothing else: no counts, no
  ranks, no dates, no links to profiles beyond the handle itself.
- Deterministic output. Equal counts sort by a stated stable key, so a rerun
  that changes nothing produces an empty diff.

**Ruled out by the Creator.**

- The repository owner is not ranked and not thanked. Excluded from both files.
- Not triggered per merge to `main`. Most merges are Shoggoth's and would
  change nothing, so per-merge triggering is churn.
- Aggregate data in the `README.md` block.

**Non-goals.**

- Rewriting history so past attribution agrees. ADR-016 rejected this
  explicitly and the rule is prospective.
- Binding authorship at integration time. That is #466.
- Inferring a real-world identity, employer, or affiliation from an account.
- Ranking issue comments, reviews, or discussion. Commits and merged pull
  requests only, per the request.
- A payment, permission, or membership programme.

## 4. Design options

**Option A: consume the contributors API, corroborate with git.** Read
`GET /repos/{owner}/{repo}/contributors` for the identity-resolved commit
counts, read merged pull-request counts per login, drop every login and author
identity in the reused host set, drop the owner, rank. Read the local git log
only to corroborate that each surviving login has at least one commit whose
author is not a host identity. Closed issues are scanned once for human
participants and any human with issue activity but no ranked commits is
reported, not ranked.

Trade: depends on GitHub's own email-to-account resolution, so the tool cannot
run fully offline. In exchange it gets the one thing local git cannot do, which
is knowing that `dave@wildcat.finance` and a GitHub noreply address are one
person.

**Option B: pure local git log.** Parse `git log` for authors and trailers, and
merge author identities with a hand-maintained alias table. Trade: runs offline
and needs no token, but the alias table is a second source of truth that a new
contributor's second email silently defeats. Evidence against it is in this
repository already: `git log` splits one human into 21 and 8 commits under two
emails, which the contributors API reports correctly as 29.

**Option C: trailer-driven.** Rank by `Wildcat-Origin` and `Co-authored-by`
trailers. Trade: rejected on evidence. Every commit by both external human
contributors carries `Wildcat-Origin: shoggoth`, so this option ranks neither of
them, and 23 commits authored by `Claude <noreply@anthropic.com>` carry no
`Wildcat-Origin` trailer, so it ranks a runtime. The trailer records which tool
did the work, not who decided it.

**Option D: adopt `all-contributors`.** Trade: a maintained bot and a
convention many readers recognise, at the cost of a hand-curated JSON file that
nobody will update and that knows nothing about ADR-016.

**Chosen: Option A.** It is the only option that resolves one human's several
emails without a hand-maintained table, and identity resolution is the whole
problem. Option C is disproved by the repository's own history and is recorded
here so a later round does not reopen it. The cost accepted is a network read,
which the workflow already has and which `--check` degrades from rather than
depends on.

## 5. Risk register seed

The generator takes GitHub API responses, writes two tracked files, and runs
unattended in CI. The concerns are the response being untrusted text that reaches
Markdown, a partial write leaving one artefact updated and the other stale, and
a classification failure ranking a runtime as a person.

A GitHub login matches `[A-Za-z0-9-]{1,39}`, so a login can never carry Markdown
syntax. The display name can carry anything, which is why no output field uses
it.

```risk-register
untrusted-api-text | the JSON body returned by api.github.com | no response field except the login reaches either artefact, and the login is re-validated against the GitHub login grammar before it is written
markdown-injection | the generated README block and CONTRIBUTORS rows | a login failing the grammar check stops the run rather than being escaped or skipped
partial-write | CONTRIBUTORS.md and README.md during --write | both artefacts render fully in memory and are written through one temporary-file-and-replace each, so a killed run leaves neither half-written
unknown-host-identity | classification of an author absent from the reused host set | an author matching neither the host set nor a recognised human stops the run and names the identity, rather than being ranked
host-set-drift | the copy of the host identity set in scripts/contributors.py | a test compares it against hexctl.py's frozensets and fails when either side changes
owner-exclusion | the ranked list and the README block | the excluded owner login is asserted absent from both artefacts by test, not by review
network-absence | the API read in CI and on a developer machine | --check reports the network failure and exits non-zero without touching either artefact
token-leak | the workflow environment and generator output | the generator never reads a token from argv, never echoes an Authorization header, and CI passes GITHUB_TOKEN by env only
issue-scan-scope | the closed-issue read | it reads public issue metadata only, contributes no rank, and records no account data beyond the login
```

## 6. Glossary seeds

- **Host identity.** A runtime or model account that appears as a Git author or
  pull-request byline. Defined by the frozensets at `hexctl.py:2798`.
- **Governed work.** Agent work invoking a Wildcat domain or phase skill,
  authored by Shoggoth under ADR-016.
- **Ranked contributor.** A resolved human GitHub login with at least one
  commit in `main` whose author is not a host identity, excluding the owner.
- **Resolved identity.** A GitHub login that the contributors API reports for
  one or more Git author emails.
- **Thanks block.** The delimited region at the bottom of `README.md` holding
  handles only, rewritten whole by the generator.
- **No-op rerun.** A `--write` on an unchanged ranking, which must leave both
  files byte-identical.

## 7. Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:2798-2856`, the host
  identity set and `is_host_identity`.
- `docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md`.
- `docs/decisions/ADR-011-load-one-shoggoth-identity-contract.md`, superseded by
  ADR-016 but naming the earlier boundary.
- `README.md:57`, the recognition sentence this run makes concrete.
- `.github/workflows/sync-skills-marketplace.yml`, the Workflows-permission
  constraint recorded in its comments.
- `.github/workflows/pandects.yml:30-40`, the root Python matrix and runner.
- `scripts/promise_machine.py`, the root script conventions.
- Issue #466, framework-7, the integration-time authorship dependency.
- Issue #515, this run's task issue.
- `audit/AUDIT.md`, read for prior contributor findings; none exist.
- GitHub REST: repository contributors, and issue search for merged pull
  requests.
- Measured against `main` at `dd23413`: 718 non-merge commits, 566 carrying
  `Wildcat-Origin: shoggoth`, 197 authored by `Claude <noreply@anthropic.com>`
  of which 174 carry that trailer and 23 carry none, one `claude[bot]` commit
  which is a merge of #222, and one human split across two author emails.

## 8. Signals, and the questions behind them

Three questions someone will ask once the workflow runs unattended.

*Did the refresh actually run last week, or has it been failing quietly since
July?* The workflow's own run history answers this only if a no-op run is
distinguishable from a failed one. Step 4 emits one summary line per run to the
job summary carrying the ranking digest, the contributor count, and whether a
pull request was opened, so a no-op is visible as a success rather than as
nothing.

*Why is this person not on the list?* Step 2 emits, at `--check` and `--write`,
a per-identity classification line naming each author identity, its resolved
login where one exists, and the reason it was ranked, excluded as a host, or
excluded as the owner. Without that line the answer requires rerunning the tool
by hand with a debugger.

*Why did the run stop?* Step 2's failure modes each exit non-zero with the
identity or field that caused it, per item 11. A stop that names nothing is
indistinguishable from a crash.

[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what those signals must carry.

## 9. Boundaries, per capability

**The GitHub API read** (step 2). Worth taking: identity resolution across
several author emails, which nothing local can do. Control: responses are
treated as untrusted text, no field but the login reaches an artefact, and the
login is re-validated against `[A-Za-z0-9-]{1,39}` before it is written. HTTPS
only, no redirect to a non-GitHub host followed, bounded response size, bounded
timeout.

**The two tracked files** (step 3). Worth taking: the artefacts are the
deliverable. Control: each is rendered whole in memory and written by
temporary-file-and-replace within the repository, never appended to, and
`README.md` is edited only between the two block markers so no other section can
be damaged by a generator bug.

**The unattended CI run** (step 4). Worth taking: the automation is the point.
Control: `permissions` is set explicitly to the minimum, `contents: write` and
`pull-requests: write`, with no other scope; the job is guarded to the canonical
repository so a fork's schedule cannot open pull requests; concurrency is
grouped so two runs cannot race the same branch.

**The local git read** (step 2). Worth taking: corroboration that a ranked
login has non-host authored work. Control: `git log` is invoked with a fixed
argument vector and no shell, on a pinned ref, with bounded output.

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

## 10. The budget, or its absence

None, and here is why. The generator makes a small number of API calls and one
git log read on a repository with 718 non-merge commits, and it runs weekly. No
step in this run is made in the name of speed, so there is nothing for
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) to hold a before and after against. If a future
run adds a full closed-issue crawl over a repository large enough for
pagination to dominate, that run owns the budget; this one records its absence.

The one bound worth stating is not performance but courtesy to the API: the
generator must complete inside the unauthenticated rate limit when run without
a token, or say plainly that it needs one.

## 11. The fail-closed posture

The run stops, rather than producing a list, on each of these:

- An author identity matching neither the host set nor a resolvable human
  login. ADR-016 states the mechanical set does not cover unfamiliar future
  host names. Ranking an unknown identity would put a runtime in a file that
  thanks people, so an unknown identity is a stop that names the identity and
  asks for the set to be extended.
- A login failing the GitHub login grammar.
- A network or API failure during `--check` or `--write`.
- The host-set parity test failing, which means the copied set and
  `hexctl.py`'s frozensets have diverged.
- The owner login appearing in a rendered artefact.

Guard-test convention, following [elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md): each of the
five gets a test that fails without the guard, named
`test_stops_on_<condition>`, asserting the non-zero exit and the identity or
field named in the message. A test asserting only that an exception was raised
does not distinguish the guard from a crash.

## 12. Decisions and their homes

Two decisions here are expensive to reverse.

The first is that identity, not the `Wildcat-Origin` trailer, decides who is a
contributor, and that a human running Shoggoth keeps their credit. Reversing it
would empty the file and contradict ADR-016's "human contributors remain
visible". It gets `docs/decisions/ADR-017-rank-contributors-by-resolved-identity.md`,
recording the trailer option's rejection with the counts that disprove it, so a
later round does not reopen a question this study already settled.

The second is that the generated files are the single source of truth and are
never hand-edited. A hand edit that the next weekly run overwrites is worse than
no automation. That goes in a comment at the top of `CONTRIBUTORS.md` and in the
generator's docstring rather than an ADR, because it is a convention rather than
a choice between options.

The trigger cadence, the owner exclusion, and the handles-only rule came from
the Creator during this run. They are recorded in item 3 and in the assumptions
block, which is where a reader looks for what the request ruled out.
[hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where
each one lives.
