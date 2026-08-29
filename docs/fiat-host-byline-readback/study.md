# study: read the pull request back and name the host default a refusal came from

## assumptions

Assuming, unless corrected:

1. The run starts from `main` at
   `5489863196006d8e8b45799d74b56208cac65e4d`; the run branch, local `main`
   and `origin/main` all resolved to that commit and the worktree was clean
   before this study was written. The controller driving the run is
   Hexaemeron `1.6.2`, `fiat-v5.26.1`, and its `hexctl.py`, `protasis.py` and
   `imprimatur.py` are byte-identical to the copies checked in at that ref.
2. Issue #617 is a `framework-18` observation, so this study selects the
   owner. It selects Fiat, as a generation on the open `fiat-v5.26.1` ledger,
   plus two repository files no governed skill owns:
   `docs/how-to-help-shoggoth.md` and `INSTALL.md`. The run was initialised
   without `--frontier` (`state.frontier` is `null`), so `done integrate`
   will not demand the ledger row mechanically; the row is still owed under
   `VERSIONING.md`, is written by hand in the last step, and is pinned by
   `tests/test_evolution_contract.py`. It records `fiat-v5.27.1`, retains the
   frontier revision `state-shape-validation`, digest
   `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, status
   `open` and the held issue 363 job byte for byte, and moves `SKILL.md`
   `metadata.version` to `5.27.1`.
3. Widening `HOST_BYLINE_RE` so that it also reads `generated with <host>`
   counts as detection, which the issue asks for, and not as a relaxed gate.
   The measurement in section 1 shows the gate misses Claude Code's own
   default pull-request line today. A veto keeps the regex as it is and drops
   one row from the coverage test; nothing else in the design moves.
4. The five refusals the issue names, and the three sibling refusals that
   read the same identities out of GitHub's commit payload, keep every word
   a test asserts today and gain a cause clause and a recovery clause. What
   is refused does not change except for assumption 3. Exit codes, the
   `hexctl: error:` prefix and every receipt's shape stay as they are.
5. The run checks in `.claude/settings.json` holding exactly
   `{"attribution": {"commit": "", "pr": "", "sessionUrl": false}}`, the
   documented way to turn Claude Code's attribution off for every session
   that honours project settings, and a root test pins the file to that
   content. The repository has no `.claude/` directory today. A veto removes
   one file, one test and the sentences that describe them.
6. The Hexaemeron package moves from `1.6.2` to `1.6.3` on
   `plugins/hexaemeron/.claude-plugin/plugin.json`,
   `plugins/hexaemeron/.codex-plugin/plugin.json`,
   `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` and
   the pin in `tests/test_version_propagation.py`, so an installed controller
   is offered the new refusal text rather than reported as already current.
7. `python3` is CPython 3.12.13 and `/usr/bin/python3` is 3.9.6; both run
   the root suite. The Hexaemeron suite runs inside
   `npx --yes --package=node@26.6.0 --call` because one Elenchus fixture
   pins Node `v26.6.0` and the host has v22, and with
   `uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt`
   so its Lazarus-backed replay class runs rather than skips. Shoggoth's
   public key `636EC19DE45DF10F3CE6206F57742DA1ABED6F46` is in the keyring,
   so the #429 recovery test passes and the suite is fully green.
8. The committed copies of this study and the runbook go to
   `docs/fiat-host-byline-readback/study.md` and
   `docs/fiat-host-byline-readback/runbook.md`, the root `docs/` location the
   last three receipted runs used; the ledger row links the study.
9. The `Claude-Session: https://claude.ai/code/session_...` trailer a cloud
   session writes on its commits is not classified as a byline in this run.
   It names a host session, not an author, and ADR-016 speaks to authors,
   co-authors, bylines and generated-by footers. The question is recorded as
   a lead in section 12 and carried forward, not answered by a regex.
10. No documented switch was found that turns attribution off for Codex,
    Copilot, Cursor, Gemini CLI or Windsurf. The guidance says so and tells
    those contributors to remove the lines before the receipt, rather than
    naming a setting this study could not verify.

These readings describe one capability: a run that meets a host default at a
host-identity gate is told which default put the string there and how to
clear it, and reads its pull request back after creation. No module
decomposition is needed. Assumptions 3, 5, 6 and 9 are scope calls Fiat can
veto in one line without changing the chosen design; the rest are readings of
the issue, the controller, the documentation and the repository.

## 1. problem statement

Fiat refuses a runtime host as author, co-author or byline on every commit in
a receipted range, and as author or byline on the pull request it receipts.
The rule is ADR-016's, the mechanism is `hexctl.py`'s, and on 2026-08-25 the
mechanism met the defaults of the host most contributors run it through.
Claude Code's documentation and this repository's history show four such
defaults. Commits from its cloud sessions have reached `main` authored
`Claude <noreply@anthropic.com>`, most recently `8c5f9b7b` on 2026-08-25. It
instructs the model to end every commit message with
`Co-Authored-By: <model name> <noreply@anthropic.com>`, adds
`Generated with [Claude Code](https://claude.com/claude-code)`, led by a robot
emoji, to every pull-request description it writes, and from a cloud or Remote
Control session
appends a `Claude-Session` trailer to commits and a session link to the
pull-request description. Pull request #615, the issue reports, was drafted
without a byline and came back from GitHub carrying
`_Generated by [Claude Code](https://claude.ai/code/session_...)_`; a body
edit removed it and the removal held. Nothing in the loop had said to read the
body back, and had that pull request been a Fiat receipt, `done integrate`
would have refused with `pull request body carries a runtime-host byline` and
no word about where the string came from.

Measured against `hexctl.py` at the base ref, by importing the module and
applying its own expressions to the strings observed this week:

| Observed host default | Where seen | `COAUTHOR_RE` and `is_host_identity` | `HOST_BYLINE_RE` |
| --- | --- | --- | --- |
| author `Claude <noreply@anthropic.com>` | commit `8c5f9b7b` in #618, 223 commits in history | refused: name and address both match | not applicable |
| `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` | commit `8c5f9b7b` in #618 | refused: the address matches; the model-suffixed name does not | no match |
| `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` | this session's own host instruction | refused: the address matches | no match |
| `Generated with [Claude Code](https://claude.com/claude-code)`, after a robot emoji | Claude Code's documented default pull-request line | not a trailer | **no match** |
| `_Generated by [Claude Code](https://claude.ai/code/session_...)_` | #615 body before its edit, #495 body today | not a trailer | refused |
| `Claude-Session: https://claude.ai/code/session_...` | commit `8c5f9b7b` in #618 | not a trailer | no match |
| pull request opened by the Claude GitHub App | #506, #465, #221 to #227 | REST spells the author `claude[bot]`, in `HOST_PR_LOGINS` | not applicable |

Two things follow. The issue's account of the co-author trailer is wrong in
one detail: `HOST_BYLINE_RE` does not match `Co-Authored-By: Claude` a second
time, because the expression wants whitespace between `authored` and `by` and
the trailer has a hyphen; the co-author gate alone refuses it. And the byline
gate misses Claude Code's own default pull-request line, because the
expression reads `generated by` and the line says `generated with`. A run
through a terminal session whose operator followed the host instruction
instead of the repository rule would today clear the byline gate carrying the
one footer ADR-016 most plainly forbids. The web session link is caught; the
terminal default is not.

The users are a human contributor running Fiat through Claude Code in a
terminal or a cloud session, Shoggoth's own cloud runs that must hand off
before publication, and the maintainer reading a refusal six weeks later.

A working prototype means:

- Each of the eight refusal sites that name a runtime host in
  `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` keeps the words the
  present tests assert and adds one clause naming the host default that
  usually put the string there and one naming the recovery. Nothing from the
  commit or the body is echoed into the message.
- `HOST_BYLINE_RE` reads `generated with <host>` as well as `generated by
  <host>`, and a coverage test enumerates the strings in the table above with
  the expected answer for each, including the ones that must still pass.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md` tells the
  operator to read the body back over REST after `gh pr create` returns and
  before `hexctl done push`, says what to look for, gives the edit-and-reread
  recovery, and says the controller reads the same body at `done push`,
  `done merge-step` and `done integrate`. The Fiat `SKILL.md` push note
  points at it in one sentence.
- A lifecycle test in `plugins/hexaemeron/tests/test_hexctl.py` receipts
  `done push` against a clean body, then has the fake GitHub return the same
  pull request with a footer appended, and asserts that `done merge-step` and
  `done integrate` refuse, that the refusal names the host default, that no
  receipt was written, and that the same receipt passes once the footer is
  gone. The web spelling and the terminal spelling are both exercised.
- A table test asserts the cause and recovery text of every refusal site
  against the fake git and fake GitHub fixtures already in the suite.
- `.claude/settings.json` exists with exactly the attribution object in
  assumption 5, `tests/test_host_settings.py` pins it, and `INSTALL.md` says
  what the file does, what it does not do, and where the documented switch
  is. `docs/how-to-help-shoggoth.md` tells a contributor which three host
  defaults Fiat refuses, that the repository rule wins over the host's
  trailer instruction, and where the switch is for Claude Code.
- `HOST_IDENTITY_NAMES`, `HOST_IDENTITY_EMAILS` and `HOST_PR_LOGINS` are
  byte-identical to the base and `tests/test_contributors.py` still passes;
  no new `HOST_*` frozenset exists.
- The ledger records `fiat-v5.27.1` as a generation row with the frontier
  fields retained, the skill frontmatter reads `5.27.1`, the package reads
  `1.6.3` on every surface, the five `fiat-*` runtime digests in
  `tests/promise_machine_coverage.json` name the new `hexctl.py`, and the
  committed study and runbook sit under `docs/fiat-host-byline-readback/`.
- ADR-016 is unchanged by one byte.

The demo path is this ordered list, run from the repository root, every
command exiting zero:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl.TestCommitVerification plugins.hexaemeron.tests.test_hexctl.TestPublicationBindings -v
python3 -m unittest tests.test_host_settings tests.test_contributors tests.test_evolution_contract tests.test_version_propagation -v
npx --yes --package=node@26.6.0 --call 'uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py'
python3 -m unittest discover -s tests
/usr/bin/python3 -m unittest discover -s tests
python3 -m unittest tests.test_evolution_contract
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-host-byline-readback/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-host-byline-readback/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-host-byline-readback/study.md docs/fiat-host-byline-readback/runbook.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/push-discipline.md docs/how-to-help-shoggoth.md INSTALL.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-host-byline-readback/study.md docs/fiat-host-byline-readback/runbook.md plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The first command runs the two Hexaemeron test classes that hold the gate
tests and the new guards; the second runs the four root modules the change
touches directly; the third is the whole Hexaemeron suite with nothing
skipped. The Elenchus checker is not on the demo path because its verdict is
Warden's to record, per section 11.

Before any change, measured in this worktree at the base ref: the Hexaemeron
suite under the Node 26 wrapper with the `uv` dependencies reports `1285/1285
tests passed` in 7 minutes 4 seconds wall, exit 0; the root suite runs 396 OK
on 3.12.13 in 28.5 seconds and 396 OK on 3.9.6 in 39.4 seconds;
`tests.test_evolution_contract` runs 9 OK; `scripts/promise_machine.py check`
prints `clean: 14 plugin(s), 14 copy/copies` and `coverage --check` prints
`clean: promises=71 coverage_rows=71 coverage_selected=71`;
`audit_synopsis.py --check .` exits 0 with all sixteen pairs at
`committed=match`; the Phylax, Ephoros and Hypomnema lints print `clean`;
`horos.py check .` prints `boundary matches the tree` and exits 0, noting one
synopsis candidate it does not hard-classify; `git diff --check` is silent.
Those facts establish a green start and the two gaps named above; they are not
proof of the change.

## 2. prior art

### in this repository

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` holds three predicates
  and eight refusal sites. `HOST_IDENTITY_NAMES` (line 6085, fourteen names),
  `HOST_IDENTITY_EMAILS` (6103, two addresses), `HOST_PR_LOGINS` (6109, five
  logins), `COAUTHOR_RE` (6118) and `HOST_BYLINE_RE` (6140) are the
  constants; `is_host_identity` (6155) folds name and address. The local range
  gate `verify_local_commit` (6373 onward) refuses `uses a runtime host as
  author; use Shoggoth or preserve the human contributor` (6399), `uses a
  runtime host as co-author` (6414) and `carries a runtime-host byline`
  (6416), then requires exactly one of each provenance trailer.
  `inspect_pull_request` (6518) reads `repos/{owner}/{repo}/pulls/{n}` over
  REST and refuses `pull request uses a runtime host as author; hand off
  before publication` (6550) and `pull request body carries a runtime-host
  byline` (6559), reading a `null` body as empty. The GitHub-side view of the
  same commits refuses `links the commit to a runtime host account`
  (`checked_login`, 6193), `names a runtime host as co-author`
  (`message_coauthors`, 6238) and `names a runtime host as author`
  (`commit_attribution`, 6643). The issue counts five sites; the other three
  read the same identities from a second source, and the merged-attribution
  audit round of 2026-08-24 recorded that "a host identity in a trailer
  refuses on either view".
- `inspect_pull_request` is called from `done_push` (3696), `done_merge_step`
  (4270) and `done_integrate` (4567), so the live body is already read after
  creation at three receipts. The issue's second acceptance bullet, a body
  checked after creation and not only before, is met by the mechanism at the
  base ref; what is missing is that the operator is never told to read it
  before the receipt, that the refusal is mute about cause, and that no test
  drives a body that was clean at push and dirty later.
- `github_rest` (6032) and `github_unreachable` (6016) are the transport
  discipline from `fiat-v5.25.1`: a read that never arrived refuses as
  `GitHub read for <label> was not answered: GET <path> <detail>. This is a
  transport failure, not a verification result`, in a shape no verdict shares.
  A read-back that fails therefore cannot be mistaken for a clean body inside
  the controller; the procedure text has to say the same for the operator's
  own `gh` call.
- `checked_login` compares a commit's linked account against
  `HOST_PR_LOGINS` only. GitHub resolves `noreply@anthropic.com` commits to
  the User account `claude` (id 81847), which is not in that set, so the
  account predicate passes such a commit and the author predicate refuses it
  a line earlier. The refusal holds; the asymmetry is recorded as a lead in
  section 12 rather than fixed, because moving a `HOST_*` set is a
  parity-guarded change outside this issue.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md` already says
  the rule and half the procedure. Lines 42 to 44: a runtime host or model "is
  neither author nor co-author. Do not carry a host-generated byline into the
  commit or pull-request body." Lines 50 to 56 give the two exact trailers.
  Lines 57 to 62 say the controller "rejects a known runtime host as author
  or co-author". Lines 105 to 106: "Do not add a Claude, Codex, ChatGPT,
  Copilot, or other host-generated byline". Lines 120 to 128 are the label
  read-back: "Read the pull request back from GitHub and confirm that both
  markers persisted before receipting the push phase" and "Read it back,
  rather than trusting that `gh pr create` applied it". Lines 130 to 136, "A
  failed query is not an answer", already state that a failed `gh` call is
  not an absence. Nothing there mentions the body, the footer, or what to do
  when the platform writes one.
- `plugins/hexaemeron/skills/fiat/SKILL.md` lines 471 to 485 carry the push
  phase note: authorship follows the contributing actor, and "Claude, Codex,
  another runtime host, or its generated-by footer is not authorship for
  either case." `plugins/hexaemeron/agents/mason.md` line 58 and
  `warden.md` line 73 tell the workers to end every commit with the exact
  Shoggoth trailer.
- Tests. `plugins/hexaemeron/tests/test_hexctl.py` (296 test methods in the
  file plus the transport cases it builds from
  `github_transport_cases.py`) carries a fake `git` whose `host-author`,
  `host-coauthor` and `host-byline` modes return `Claude\0noreply@anthropic.com`,
  a `Co-authored-by: Claude <noreply@anthropic.com>` line and a `Generated by
  Claude Code` line, and a fake `gh` whose `host-pr-author` and
  `host-pr-byline` modes return `app/claude` and append
  `Generated by [Claude Code](https://claude.ai/code)` to the body.
  `test_local_fake_git_negative_matrix_is_fail_closed_and_secret_safe` asserts
  those modes refuse without echoing secrets;
  `test_pull_request_refuses_host_author_and_byline` asserts the two
  pull-request modes refuse and that stderr contains `runtime`;
  `test_attribution_negative_matrix_is_fail_closed_and_secret_safe` asserts
  `runtime host account`, `runtime host as author` and `runtime host as
  co-author` for the GitHub-side view. `TestPublicationBindings.to_push`,
  `to_merge_step` and `to_integrate` drive a run to each receipt with the
  fake tools, `fake_pr` builds a body reading `Delivery evidence.\n\n<!--
  wildcat-origin: shoggoth -->`, and `TestMergedState.integrate` shows how a
  fixture mode is switched between receipts. Every new guard in this study is
  a composition of those helpers.
- `plugins/hexaemeron/tests/test_fiat_skill.py` pins push-discipline prose:
  "Read the pull request back from GitHub", "same `gh pr create` command",
  "pre-existing human commit", "Read it back", "rather than trusting that `gh
  pr create` applied it", "A failed query is not an answer" and "Check the
  exit status separately from the match", all on whitespace-flattened text.
  `tests/test_marketplace_prose.py` pins `fiat/<issue>-` in push-discipline
  and, in `SKILL.md`, "validates the required version-1 container", `init
  --task-issue <url>` and `--audit-filter sapheneia:sapheneia`. Every edit
  keeps those strings.
- `tests/test_contributors.py` reads every `HOST_* = frozenset(...)` literal
  out of `hexctl.py`'s syntax tree and requires the set of names to equal
  exactly `HOST_IDENTITY_NAMES`, `HOST_IDENTITY_EMAILS` and `HOST_PR_LOGINS`,
  with contents equal to `scripts/contributors.py`'s copies. Audit finding
  S1-R2-01 of 2026-08-24 closed the discovery gap this way, and the same
  round records that a `HOST_*` name bound to something other than a
  frozenset is skipped. So this change adds no `HOST_*` frozenset, and names
  its cause-clause constants without that prefix so nobody has to know the
  exemption.
- `docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md`,
  accepted 2026-08-23, is the rule: "Runtime hosts and models are execution
  metadata, not Git authors, co-authors, pull-request bylines, or
  generated-by footers for that governed work", a human contributor keeps
  their own identity, and "Work outside the Interceptor that invokes no
  Wildcat domain or phase skill may retain ordinary Claude, Codex, or other
  host attribution." Its rejected alternative "Put the rule only in local
  Git configuration" lost because it "does not travel to cloud sessions,
  contributor machines, installations, or the Interceptor". A committed
  settings file travels with the clone; section 4 says what that does and
  does not buy. ADR-011 is superseded and unchanged.
- Ledger rows. `fiat-v5.13.1` (commit `49ffa06`, pull request #511,
  2026-08-23) introduced the gates with the package at `1.5.6`;
  `fiat-v5.15.1` added the attribution receipt and the GitHub-side refusals;
  `fiat-v5.25.1` moved every receipt read to REST. The package moved with
  v5.13.1, v5.15.1, v5.16.1, v5.24.1 and v5.26.1, and with `elenchus-v1.3.0`
  to `1.6.2`; v5.17.1 to v5.23.1 and v5.25.1 shipped without moving it and
  were carried by the next bump. This change is refusal text an installed
  controller shows an operator, so it moves the package.
- Repository history is the evidence that the defaults are live: 223 commits
  are authored `Claude <noreply@anthropic.com>`, 301 carry a `Co-Authored-By:
  Claude` trailer, one is authored `claude[bot]`. The newest, `8c5f9b7b` in
  #618 on 2026-08-25, carries the host author, `Co-Authored-By: Claude Opus 5
  <noreply@anthropic.com>` and `Claude-Session:
  https://claude.ai/code/session_01XFZztLwhhL4Pws4jvvRiM9`. It is a
  documentation change made outside Fiat, which ADR-016's last sentence
  permits, and it is a specimen of exactly what a governed run would be
  refused for. #615's one commit `5b1dadb5` is authored Shoggoth with the two
  trailers and is verified `true`/`valid`; its body carries a "Footer note"
  saying the byline was left out on purpose. Issue #495's body still ends
  with `_Generated by [Claude Code](https://claude.ai/code)_`, consistent with
  the issue's negative evidence that no `hexctl` check reads an issue body.
- `docs/how-to-help-shoggoth.md` tells a contributor to "Keep your own Git
  author, valid signing identity and GitHub account" and that "Fiat adds the
  required Shoggoth provenance without replacing you"; it says nothing about
  the harness's own attribution defaults. `INSTALL.md`'s Claude Code section
  lists the marketplace and plugin commands and says nothing about settings.
  `README.md` repeats the human-authorship rule. There is no `.claude/`
  directory in the repository; `tests/test_marketplace_prose.py` already
  lists `.claude` among the nested-checkout names its README sweep skips, so
  adding one does not disturb that test.
- Version surfaces: the four manifests and `DELIVERY_PACKAGE_VERSIONS` read
  `1.6.2`, pinned by `tests/test_version_propagation.py`. The five `fiat-*`
  runtime bindings in `tests/promise_machine_coverage.json` pin `hexctl.py`
  at SHA-256 `4850f689...`; every Fiat generation that touched the controller
  re-pinned them in the same commit, most recently `2610b68`.
- `.horos/boundary.json` records `counts.files_walked` (1600 today) and the
  root test compares classified entries, not counts, so new small text files
  pass the check; earlier runs regenerated the document anyway when the check
  named drift. The last step runs `horos.py check .` and regenerates only if
  it names a drifted entry.

### the last two merged pull requests

For `hexctl.py`, the last two merged pull requests were read in full.

- [PR #619](https://github.com/wildcat-finance/skills/pull/619), `Recover
  #429/#552 and publish Fiat 5.26.1`, merged 2026-08-25 at `1efec4de`. Its
  `## Carried forward` names issue #557 (ledger recovery when a clone is
  lost), issue #608 (`base_commit` versus `base_head` naming), issues #453,
  #369 and #363 as separately owned, cross-file crash atomicity of the
  synopsis generator, six Horos synopsis candidates, the inherited
  `ResourceWarning` output, and four things it did not check. None is an
  obligation of this run: #557, #608 and #453 stay open and owned elsewhere;
  #369 closed on 2026-08-25 and its Protasis 4.8.0 synopsis rule is the one
  this study read its audit sources under; #363 is the held frontier and is
  not moved; the generator limits belong to `audit_synopsis.py`, which this
  run does not touch. Each is refused by name here.
- [PR #615](https://github.com/wildcat-finance/skills/pull/615), `fix(fiat):
  read every GitHub receipt over REST and name a failed read as one`, merged
  2026-08-25 at `4f9a5b84`, closed #495 and recorded `fiat-v5.25.1`. It was
  not a Fiat run and carries no `## Carried forward` heading. It names two
  environmental failures in `test_elenchus_checker` (`forge` absent, Node v22
  against a fixture declaring v26); the Node one is why the demo path wraps
  the suite, and the `forge` one did not reproduce here, where the suite is
  1285/1285. Its "Footer note" is the first written trace of the collision
  this issue names, and its transport discipline is what the read-back
  inherits: the recovery text in this study spells the read as `gh api
  repos/<owner>/<repo>/pulls/<n>` rather than `gh pr view --json body`,
  because the latter goes over GraphQL and #495 was a proxy that served REST
  only.
- [PR #607](https://github.com/wildcat-finance/skills/pull/607), the
  controller currency guarantee, is the one before. Its sixteen carried
  items are all currency-gate leads; none touches identity or bylines.

For `push-discipline.md`, the last merged pull requests to change it were
#602 (`c6db32a`, the bound step-merge run, 2026-08-24) and the `fiat-v5.17.1`
to `fiat-v5.19.1` sync work merged the same day; before that, #511 wrote the
byline rule. For `docs/how-to-help-shoggoth.md`, #618 (2026-08-25) added who
closes a delivered issue, and `2ebfc35` (2026-08-24) clarified external
contributor identity; neither carries an open item about attribution.
`INSTALL.md` last changed in `c4694f1` on 2026-08-22.

### audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
was run from the target root before design options were drawn and exited 0
with all sixteen source and synopsis pairs at `committed=match`, so a
synopsis was an allowed reading view. Fiat is the one in-scope skill. Its
records were read as follows:

- `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md`, the
  last Fiat-owned run's record: source and synopsis both read. Four rounds
  under `fiat-audit-round/v2`; S1-R1-01 (medium, stale synopsis plan and
  rollback, fixed, verdict `guarded`), S2-R1-01 (medium, the recovery proof's
  two-record assumption, fixed, verdict `guarded`), two clean rounds with
  verdict `null`; every risk id disposed; leads not pursued name `origin/main`
  drift, the open issues above, generator crash atomicity, Horos candidates
  and the `ResourceWarning`. Nothing there touches identity.
- `audit/rounds/fiat-495*`: no such record exists. #615 was not a Fiat run
  and derived no audit file; its evidence is the body quoted above.
- `audit/AUDIT.md`, sections `Fiat merged attribution`, steps 1 to 4
  (2026-08-24): synopsis read for every round, and source read at lines
  11649 to 11690 for step 2 round 1, because the synopsis carries
  `[missing legacy field: covered]`, `[missing legacy field: not-checked]`
  and `[missing legacy field: elenchus-verdict]` on every round of that run
  and this study needed the risk-register disposition. Findings: S1-R1-01
  (low, an address quoted in the study, accepted); S1-R1-02 (low, ADR-017
  tense, fixed); S2-R1-01 (medium, `checked_login` read an object without a
  login as unlinked, fixed: "only a literal `null` records `null`"); S2-R1-02
  (medium, verification silently gated on the attribution reader, fixed:
  "verification keeps its own reader"); S3-R1-01 (high, the rewritten-merge
  fallback inspected only the base merge, fixed); S3-R1-02 (low, presence
  versus truthiness, fixed); S4-R1-01 (medium, a proof that could leave the
  checkout on an older controller, fixed); S4-R1-02 (low, an amendment
  naming a generator that did not exist on the branch, accepted). Its
  `attribution-coauthor-parse` disposition, "the trailer is parsed with the
  same expression the local range gate uses, so the two cannot disagree, and
  a host identity in a trailer refuses on either view", is why this study
  treats the GitHub-side refusals as the same three predicates and gives them
  the same cause clauses. Leads not pursued: the installed-controller split
  (the live run drove `fiat-v5.13.1`), carried through every round.
- `audit/AUDIT.md`, the contributor-list run of 2026-08-24 (`Step 1, round
  2` at line 12083, `Step 2, round 1` at 12142, `Step 4, round 1` at 12324):
  source read at those lines and at 12074. S1-R2-01 (medium, `HOST_*` set discovery by
  prefix, fixed) is the parity constraint above; S1-R1-03 (medium, the
  guard-order hazard for `claude[bot]` and `app/claude`, fixed) is why REST's
  `claude[bot]` spelling matters; S2-R1-05 (low, Hypomnema run without
  `docs` reporting `ADR-016` as missing, recorded) is why the demo path
  invokes `hypomnema.py` with `docs`; S4-R1-02 (low, no provenance trailers
  on the cron commits, fixed) confirms that a scheduled job is not governed
  work.
- `audit/AUDIT.md` `fiat-v5.13.1`: the gates landed in #511 by maintainer
  direction and left no audit round; the pull request body and ADR-016 are
  the record. The synopsis headings for `Fiat installed-path proof`,
  `Receipted lint rounds`, `Fiat delegation packets`, `Fiat state-shape
  validation`, `Fiat task-issue branch names` and `Fiat receipted study
  amendments` were read as headings; none concerns identity and their
  findings are not restated here.
- `plugins/hexaemeron/audit/AUDIT.md` and `AUDIT_SYNOPSIS.md`: both read.
  F-01 to F-09 fixed with regression tests, F-10 accepted as `hook_gate.py`'s
  documented escape hatch; leads not pursued were `os.replace` atomicity
  across filesystems, concurrent `hexctl` invocations and ANSI passthrough
  in `status --json`. None touches this change.

This run's own record,
`audit/rounds/fiat-617-runtime-host-reinstates-the-byline-the-ident.md`,
does not exist yet; Fiat derives it at the first round with its synopsis
sibling, and `state.config.audit.log_path` already names it.

### in the organisation

`laurenceday/shoggoth-interceptor` (head `23f9761a`, 2026-08-24) carries
`bin/authorship-gate.py`, "Refuse runtime-host authorship in one exact
Interceptor branch range". It copies `COAUTHOR_RE`, `HOST_BYLINE_RE`,
`HOST_NAMES` and `HOST_EMAILS` byte for byte from `hexctl.py`, inspects each
commit's author, trailers and body, and refuses `carries a runtime-host
byline` with the same expression. It reads no pull request body and names no
cause. It therefore shares the `generated with` gap measured above; that is
recorded in section 12 as a carried-forward item for that repository, because
this run touches no file outside `wildcat-finance/skills`. `gh search code
--owner wildcat-finance` cannot see private repositories; nothing else was
found.

### outside the organisation

- Claude Code's settings reference, read on 2026-08-26 from
  `https://code.claude.com/docs/en/settings-reference.md`, documents four
  keys under "Git and attribution", each with scope `Any file`, meaning
  `~/.claude/settings.json`, `.claude/settings.json`,
  `.claude/settings.local.json` and managed settings. `attribution` is "object
  with `commit` and `pr` strings and a `sessionUrl` Boolean", default
  "unset, so Claude Code uses the standard attribution shown under each
  sub-key", and "To hide all attribution, set `commit` and `pr` to empty
  strings and `sessionUrl` to `false`." `attribution.commit`: "Set the
  attribution text Claude Code adds to git commits, including any trailers.
  Set it to an empty string to hide commit attribution", default "unset, so
  Claude Code adds `Co-Authored-By: <model name> <noreply@anthropic.com>`,
  where the model name reflects the active model for the session, such as
  `Claude Sonnet 5`, or `Claude` alone when the session's model isn't a
  public model". `attribution.pr`: "Set it to an empty string to hide pull
  request attribution", default "unset, so Claude Code adds" a robot emoji
  and `Generated with [Claude Code](https://claude.com/claude-code)`.
  `attribution.sessionUrl`: "Choose whether Claude Code appends the claude.ai
  session link when it commits or opens a pull request from a cloud or Remote
  Control session. Claude Code adds the link as a `Claude-Session` trailer on
  commits and as a link in pull request descriptions. Set it to `false` to
  omit the link", default `true`. `includeCoAuthoredBy` is "Deprecated since
  v2.0.62, when `attribution` replaced it"; once `commit` or `pr` is set it
  is ignored. `includeGitInstructions: false` removes the built-in commit and
  pull-request instructions from the prompt entirely, and the git status
  snapshot with them; this study does not use it, because the repository
  wants its own rule enforced, not the host's advice removed. The
  `settings.md` page lists "Shared project settings (`.claude/settings.json`):
  settings your team checks into source control", and the web page says of
  cloud sessions: "To change settings for a cloud session, use environment
  variables or commit settings files to the repository."
- What the documentation does not say, and this study therefore does not
  claim: that the footer observed on #615 is the `sessionUrl` link rather
  than something the web product adds on its own. Its shape, a link into
  `claude.ai/code/session_...` in the description, matches the documented
  session link and matches no other documented default, so
  `attribution.sessionUrl: false` is the documented switch to try. Whether
  it suppresses that footer in a live cloud session was not verified from
  this terminal and is recorded as unverified in the guidance.
- No documented equivalent was found for Codex, Copilot, Cursor, Gemini CLI
  or Windsurf; the guidance says so.
- `git interpret-trailers` defines the trailer block the repository's two
  provenance lines and the host's `Co-Authored-By` line all live in, which is
  why a gate can count exact copies. GitHub's REST `pulls/{n}` endpoint
  returns `body: null` for an empty description, which `inspect_pull_request`
  already reads as empty; a body edit through `gh pr edit --body-file`
  replaces the description wholesale, which is why the recovery re-reads it.

## 3. constraints and non-goals

### constraints

- Start from `main` at `5489863196006d8e8b45799d74b56208cac65e4d` and stay
  within issue #617: detection and diagnosis where the platform puts a
  forbidden string back by itself.
- No gate is relaxed and no host identity becomes acceptable.
  `HOST_IDENTITY_NAMES`, `HOST_IDENTITY_EMAILS` and `HOST_PR_LOGINS` are
  byte-identical to the base; `tests/test_contributors.py` passes unchanged;
  no new `HOST_*` frozenset is added. The one predicate that changes,
  `HOST_BYLINE_RE`, refuses strictly more than before.
- No receipt changes shape. The `push`, `merge-step` and `integrate` receipt
  dictionaries keep exactly their present keys; the ledger arithmetic and the
  held issue 363 job are untouched; ADR-016 is unchanged.
- Every refusal message keeps the substrings the suite asserts today:
  `runtime host as author`, `runtime host as co-author`, `runtime-host
  byline`, `runtime host account`, `hand off before publication`, `runtime`.
  No message echoes commit bytes, body bytes, a URL taken from the payload or
  signature material; the cause and recovery clauses are fixed constants.
- The procedure edit keeps every string `test_fiat_skill.py` and
  `test_marketplace_prose.py` pin, listed in section 2.
- `.claude/settings.json` holds the attribution object and nothing else: no
  `permissions`, `hooks`, `env` or plugin keys, because a checked-in settings
  file runs on every contributor's machine and a hook there would be code the
  repository ships to every session. The root test pins the whole document.
- The ledger records `fiat-v5.27.1` as a generation row retaining
  `state-shape-validation`, its digest, `open` and the held job;
  `tests/test_evolution_contract.py::test_fiat_state_shape_frontier_holds_the_task_identity_successor`
  moves its latest and predecessor pins to `fiat-v5.27.1` and `fiat-v5.26.1`;
  `SKILL.md` frontmatter reads `5.27.1`; `plugins/hexaemeron/tests/test_evolution.py`
  passes unchanged.
- The package reads `1.6.3` on the four manifests and in
  `DELIVERY_PACKAGE_VERSIONS`. The five `fiat-*` runtime bindings in
  `tests/promise_machine_coverage.json` are re-pinned to the new `hexctl.py`
  digest in the same commit that changes the file, as `2610b68` and
  `5b1dadb` did.
- Root tests use no syntax newer than Python 3.9, because CI's janus,
  lazarus and pandects workflows run the root suite on 3.9, 3.11 and 3.13
  whenever `tests/**` changes. The Hexaemeron suite has no workflow and is
  exercised by the demo path and the audit rounds.
- Committed copies of the receipted study and runbook live at
  `docs/fiat-host-byline-readback/study.md` and
  `docs/fiat-host-byline-readback/runbook.md`.

### non-goals

- A controller that edits GitHub. Fiat's readers are bounded, argv-only and
  read-only, and stay so; the footer is removed by the operator with `gh pr
  edit`, and the controller only refuses until it is gone.
- A new `hexctl` subcommand, receipt field, directive field or exit code.
- Classifying the `Claude-Session` trailer as a byline (assumption 9), or
  adding the User login `claude` to `HOST_PR_LOGINS`; both are recorded
  leads.
- Reading issue bodies. #495's footer stays where it is; the issue's negative
  evidence stands.
- Changing `scripts/contributors.py`, ADR-016, ADR-019 or the Interceptor.
- Setting `includeGitInstructions: false`, or any settings key beyond
  `attribution`.
- Verifying the cloud footer's suppression in a live cloud session; the
  guidance labels it unverified.
- Rewriting history: the 223 host-authored commits and 301 host trailers
  already on `main` are ADR-016's "prospective" boundary and stay.

### explicit unknowns

- Whether Fiat wants the regex widened in this generation (assumption 3).
  A veto leaves Claude Code's default pull-request line undetected and this
  study records that as a known gap in the ledger row.
- Whether Fiat wants `.claude/settings.json` checked in (assumption 5). A
  veto leaves the switch documented at user scope in `INSTALL.md` and removes
  the root test.
- Whether `attribution.sessionUrl: false` removes the #615-style footer in a
  cloud session; documented as the switch, not observed from here.
- Whether the audit machine has `uv` and Node 26 through `npx`; it does
  here, and the runner contract in section 11 depends on both.
- Private organisation repositories cannot be searched from here.

### operating boundaries

**Always.** Observe every new guard red on the base tree before the change
lands: the cause-text table against the present messages, the coverage row
for `generated with` against the present regex, the footer-reappearance
lifecycle test against a controller that refuses without a cause. Run the
Hexaemeron suite under the Node 26 wrapper with the `uv` dependencies, the
root suite on both interpreters, `tests.test_evolution_contract`,
`scripts/promise_machine.py check` and `coverage --check`, `audit_synopsis.py
--check .`, the Protasis checks on both committed copies, Imprimatur and
Brevitas on every changed Markdown file, the Phylax, Ephoros and Hypomnema
tree lints with `docs` on the Hypomnema argv, `horos.py check .` and `git
diff --check` before any commit. Sign every commit and end it with the two
exact trailers and nothing else, which is the rule this change is about.

**Ask first.** Change any `HOST_*` set; add a `HOST_*` name of any kind;
change what any predicate other than `HOST_BYLINE_RE` refuses; add a receipt
field, directive field, subcommand or exit code; put any key other than
`attribution` in `.claude/settings.json`; change a frontier field of the
ledger; move the package anywhere other than `1.6.3`; touch CI, ADR-016,
`scripts/contributors.py` or any file in another repository; add a
dependency.

**Never.** Relax a refusal or make a host identity acceptable; echo a commit
message, a body, a payload URL or signature material into a refusal; treat a
`gh` call that failed as a clean body or an absent footer; read a failed
transport as a verdict; delete or skip a failing test; strip the footer by
having the controller write to GitHub; ask for or use the Shoggoth key or
account for a human contribution; claim a command ran when it did not.

Expected implementation and record paths are:

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
  `plugins/hexaemeron/tests/test_hexctl.py`,
  `tests/promise_machine_coverage.json`.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
  `plugins/hexaemeron/skills/fiat/SKILL.md`,
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
  `plugins/hexaemeron/tests/test_fiat_skill.py`,
  `tests/test_evolution_contract.py`.
- `docs/how-to-help-shoggoth.md`, `INSTALL.md`, `.claude/settings.json`,
  `tests/test_host_settings.py`.
- The five version surfaces named above.
- `docs/fiat-host-byline-readback/study.md` and `runbook.md`; the audit file
  Fiat derives at
  `audit/rounds/fiat-617-runtime-host-reinstates-the-byline-the-ident.md`
  with its synopsis; `.horos/boundary.json` only if `check` names drift.

## 4. design options

### option A: cause clauses in the controller, a read-back in the procedure, guards in the suite, and the switch at source (chosen)

Four parts, each landing where the thing it changes already lives.

**The controller names the cause.** Three cause constants and three recovery
constants join `hexctl.py` beside the predicates, named without the `HOST_`
prefix, and each of the eight refusal sites appends the pair that fits. The
texts settled here, with the present words kept in front:

| Site | Present text | Appended cause and recovery |
| --- | --- | --- |
| `verify_local_commit`, author | `uses a runtime host as author; use Shoggoth or preserve the human contributor` | `The usual cause is the host's default git identity, such as Claude <noreply@anthropic.com>; set git user.name and user.email to the contributing actor and recreate the commit.` |
| `verify_local_commit`, co-author | `uses a runtime host as co-author` | `The usual cause is the host's standing instruction to end every commit with a Co-Authored-By trailer naming itself; the repository rule wins: end the message with the two exact provenance trailers and nothing else, and recreate the commit.` |
| `verify_local_commit`, byline | `carries a runtime-host byline` | `The usual cause is the host's default attribution line (Generated with or by Claude Code, Codex or another host) or its session link in the message; remove it and recreate the commit.` |
| `inspect_pull_request`, author | `pull request uses a runtime host as author; hand off before publication` | `The pull request was opened under the host app's GitHub identity, such as claude[bot]; open it from the contributing actor's own account instead.` |
| `inspect_pull_request`, byline | `pull request body carries a runtime-host byline` | `The usual cause is the host appending its attribution line or claude.ai session link to the description after gh pr create returned; edit the body without it (gh pr edit <url> --body-file <file>), read it back over REST, and rerun this receipt.` |
| `checked_login` | `links the commit to a runtime host account` | `The commit was pushed under the host app's account; hand off before publication and push as the contributing actor.` |
| `message_coauthors` | `names a runtime host as co-author` | the co-author clause above |
| `commit_attribution` | `names a runtime host as author` | the author clause above |

`HOST_BYLINE_RE` becomes
`(?:generated\s+(?:by|with)|(?:co-)?authored\s+by)\s+` followed by the same
host alternation. Nothing that passed before is refused except a `generated
with <host>` line, which is Claude Code's documented default and the string
ADR-016 names.

**The procedure reads the body back.** `push-discipline.md` gains one section
after the label read-back, in the same voice, saying: the body is the second
thing to read back, because a host can append its attribution line or session
link after `gh pr create` returns; read it over REST with `gh api
repos/<owner>/<repo>/pulls/<n> --jq .body`, since `--json` forms go over
GraphQL and #495 was an environment that served REST only; a failed read is
not a clean body, by the same rule as the label; look for any line the
controller refuses, which the section lists; when one is there, `gh pr edit
<url> --body-file .hexaemeron/steps/<n>/pr.md`, the body the prose phase
stashed, and read it back again; then `hexctl done push`. It says the
controller reads the same body at `done push`, `done merge-step` and `done
integrate`, so a footer that reappears later is refused there with the cause
named and the same edit clears it. It says once, plainly, that the host's
`Co-Authored-By` instruction and the repository's two-trailer rule cannot both
be satisfied and the repository rule wins. The `SKILL.md` push note gains one
sentence pointing at the section. The same section carries the sentence about
`.claude/settings.json`: it turns the defaults off for Claude Code sessions
that honour project settings, and the read-back still runs, because a setting
is not evidence.

**The suite guards it.** Three additions to `test_hexctl.py`, all built from
the fixtures that exist. A cause-text table drives every refusal site through
its existing fake mode and asserts the cause and recovery substrings beside
the present ones. A byline-coverage table asserts `HOST_BYLINE_RE` against the
strings in section 1's table with the expected answer for each, including
`Generated with pytest` and `co-authored by a colleague` as strings that must
pass and the `Claude-Session` trailer as a string the regex does not read,
with a comment naming the lead. A lifecycle test drives
`TestPublicationBindings.to_merge_step`, appends the web footer to the fake
pull request's body, asserts `done merge-step` refuses with `carries a
runtime-host byline` and `after gh pr create returned`, asserts
`state.integrate.merges` is still empty, removes the footer and asserts the
same receipt passes; a second case does the same across `to_integrate` with
the run pull request; a third uses the terminal spelling, the robot emoji and
`Generated with [Claude Code](https://claude.com/claude-code)`.
`test_fiat_skill.py` pins the
new procedure sentences the way it pins the label ones.

**The switch at source.** `.claude/settings.json` with exactly the attribution
object, `tests/test_host_settings.py` asserting the parsed document equals
it, and prose in `INSTALL.md` and `docs/how-to-help-shoggoth.md` that says
what the file does, which sessions it reaches, that it is not verified
against the cloud footer, that other harnesses have no documented equivalent,
and that Fiat refuses the three defaults by name either way.

The trade. Eight refusal messages grow by a sentence or two, and the word
"usual" in them is a claim about causes this study established from one
week's evidence and one host's documentation; a future host with different
defaults will read a cause clause that is wrong for it, and the fixed text
says "usual" for that reason. Widening the regex refuses a body that passes
today, deliberately. The settings file is host-specific configuration in a
host-neutral repository, and its effect on the cloud footer is documented
rather than observed. The read-back is procedure: an operator who skips it
still meets the gate at the receipt, which is the floor this design keeps
rather than raises.

### option B: procedure only, no code

Write the read-back and the cause explanations into `push-discipline.md` and
leave `hexctl.py` alone. Cheapest to build. Rejected because the refusal an
operator actually sees stays mute, which is the first thing the issue asks
for; because the `generated with` gap stays open; and because a procedure the
controller does not test leaves no trace when skipped, the same reasoning
`fiat-v4.5.1` recorded for the label read-back.

### option C: a read-only `hexctl inspect-pr <url>` subcommand

Expose `inspect_pull_request` as a command the operator runs right after `gh
pr create`, so the same check that refuses at the receipt runs before it.
Attractive because it removes the gap between what the operator greps for and
what the controller refuses. Rejected for this generation because `done push`
already runs that exact check after creation and refuses with the cause once
option A lands, so the subcommand would duplicate a check that is one command
away; it adds a CLI surface to audit and document for a gain the procedure's
one `gh api` line already delivers. Recorded as the next step if the
procedure proves insufficient in practice.

### option D: the controller removes the footer

Have `done push` call `gh pr edit` when it finds a byline. Rejected: Fiat's
GitHub readers are bounded, read-only and argv-only by design, and a controller
that writes to GitHub on a refusal path has a new boundary and a new failure
mode for one convenience. The edit stays with the operator; the controller
says exactly what to run.

### option E: extend the host sets

Add model-suffixed names such as `Claude Opus 5` to `HOST_IDENTITY_NAMES` and
the User login `claude` to `HOST_PR_LOGINS`. Rejected: the address already
refuses every model-suffixed trailer observed, so the names add nothing; the
login is refused by the author predicate a line earlier; and each set is
parity-guarded with `scripts/contributors.py`, whose contributor ranking would
change meaning. Both are recorded leads.

Option A is the cheapest to comprehend that still meets the problem statement:
each change lands where a reader already looks for it, every test is a
composition of fixtures the suite has, and the one behavioural widening is
a two-token change to an expression whose coverage is then written down as a
table.

Settled alongside the pick:

- The new constants are named `CAUSE_HOST_AUTHOR`, `CAUSE_HOST_COAUTHOR`,
  `CAUSE_HOST_BYLINE`, `CAUSE_HOST_PR_AUTHOR`, `CAUSE_HOST_PR_BYLINE` and
  `CAUSE_HOST_ACCOUNT`, module-level strings, each ending with the recovery,
  each carrying a comment that cites ADR-016 and this study.
- The push-discipline section is titled `## Read the body back` and sits
  between the label read-back and "Verify the pull request URL after
  creation".
- The ledger row's change column names the eight sites, the widened
  expression with the `generated with` spelling, the read-back, the settings
  file, that no gate is relaxed and no receipt changes shape, and that the
  frontier is unchanged; its evidence column links
  `[skills#617](https://github.com/wildcat-finance/skills/issues/617)` and
  `[study and runbook](../../../../docs/fiat-host-byline-readback/)`, relative
  to the ledger so Hypomnema's H001 check resolves them.
- No ADR. Section 12 says why.
- The runbook is four steps: commit the study and runbook; the controller
  change with its tests and the re-pinned runtime digests; the procedure, the
  guidance, the settings file and its test; the ledger row, the version
  surfaces and the demonstration from section 1.

## 5. risk register seed

```risk-register
no-gate-relaxed | the three predicates and eight refusal sites in hexctl.py | every present fixture mode still refuses and the negative matrices and the pull-request gate test pass without edits to their assertions
byline-widening-scope | the HOST_BYLINE_RE alternation | the coverage table shows generated with <host> refused and Generated with pytest and co-authored by a colleague still passing and no other string changes answer
no-host-identity-accepted | HOST_IDENTITY_NAMES HOST_IDENTITY_EMAILS and HOST_PR_LOGINS | the three sets are byte-identical to the base and tests/test_contributors.py passes and no new HOST_ name exists in hexctl.py
cause-text-guarded | the appended cause and recovery clauses | a table test asserts each site's cause and recovery substrings beside the present ones and no message is asserted only by a human reading it
message-no-echo | every refusal message | no commit message body pull-request body payload URL or signature material appears in any message and the negative matrices still assert the secret markers are absent
readback-transport | the operator's gh api read and the controller's REST read | a read that failed timed out or returned a non-document is named a transport failure and never read as a clean body in code or in the procedure text
footer-reappearance | a body clean at done push and dirty at done merge-step or done integrate | the lifecycle test refuses at the later receipt with the cause named writes no receipt and passes once the footer is removed for both the web and the terminal spelling
no-receipt-shape-change | the push merge-step and integrate receipt dictionaries | the key sets are unchanged and the existing receipt tests pass without edits
procedure-rest-only | the read-back command in push-discipline.md | the command is spelled as gh api repos/<owner>/<repo>/pulls/<n> and the text says why --json is not used
prose-pins-kept | the strings test_fiat_skill.py and test_marketplace_prose.py assert | every pinned string is present after the edit and the new sentences are pinned the same way
human-authorship-preserved | the author gate and its cause clause | a human contributor's own identity passes as before and the cause text tells them to use their own identity not Shoggoth's
settings-file-shape | .claude/settings.json | the file parses as JSON and equals exactly the attribution object with empty commit empty pr and sessionUrl false and a root test pins the whole document
settings-file-scope | what the settings file is said to do | the prose says which sessions it reaches which host it is for that other harnesses have no documented switch and that the cloud footer suppression is unverified
prose-matches-docs | every statement about host behaviour in the five prose files | each statement traces to a sentence quoted in section 2 from the settings reference or to an observation named in section 1
ledger-integrity | the fiat-v5.27.1 row | revision and digest are byte-identical to v5.26.1 status stays open the held job is unchanged the frontmatter matches and the evolution-contract pins pass
version-surfaces | the four manifests and the propagation pin | every surface reads 1.6.3 and test_version_propagation passes on 3.9.6 and 3.12.13
runtime-digest-pins | the five fiat-* bindings in tests/promise_machine_coverage.json | promise_machine.py check prints clean after the hexctl.py change and the digests were moved in the same commit
partial-run | an interrupted suite edit or read-back | no receipt commit or clean claim rests on a command that did not exit zero and a footer found after done push is removed and re-read before merge-step
interceptor-drift | the copied expression in shoggoth-interceptor | the gap is named in the run's carried-forward section and no file in that repository is touched by this run
```

There is no funds arithmetic, upgrade path, signing key or persistent write
in this change. The one untrusted input is the pull-request body GitHub
returns, which the controller already searches with a fixed expression and
never echoes; the one new file the host executes is a JSON document with
three scalar values. The audit should look hardest at `no-gate-relaxed`,
`byline-widening-scope`, `message-no-echo` and `settings-file-shape`: the
first two are where a diagnosis change could quietly become a policy change,
the third is where a helpful message could leak what the gate exists to keep
out of the ledger, and the fourth is a file every contributor's harness will
read.

## 6. glossary seeds

- `host default`: a string a runtime host adds to a commit or pull request
  without being asked: its git identity, its `Co-Authored-By` trailer, its
  attribution line, its session link.
- `byline`: any line in a commit message or pull-request body that credits a
  runtime host as the work's author or generator; `HOST_BYLINE_RE` is its
  mechanical reading.
- `attribution line`: Claude Code's documented default pull-request text, a
  robot emoji and `Generated with [Claude Code](https://claude.com/claude-code)`.
- `session link`: the `claude.ai/code/session_...` URL a cloud or Remote
  Control session adds as a `Claude-Session` trailer on commits and as a link
  in pull-request descriptions; the footer seen on #615 has that shape.
- `cause clause`: the fixed sentence a refusal appends naming the host
  default that usually put the refused string there.
- `recovery clause`: the fixed sentence after it naming the command or edit
  that clears the refusal without touching the gate.
- `read-back`: reading a pull request from GitHub after `gh pr create`
  returned and before the receipt, over REST, and treating a failed read as
  no answer.
- `provenance trailers`: `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>`
  and `Wildcat-Origin: shoggoth`, exactly once each, on every Fiat-created
  commit.
- `host identity sets`: `HOST_IDENTITY_NAMES`, `HOST_IDENTITY_EMAILS` and
  `HOST_PR_LOGINS`, parity-guarded with `scripts/contributors.py`.
- `transport failure`: a GitHub read that never arrived, refused in
  `github_unreachable`'s shape, which says nothing about the work.
- `generation row`: a ledger row that changes behaviour while retaining the
  frontier revision, digest, status and next job byte for byte.

## 7. sources and checks

- Task and base: issue #617,
  <https://github.com/wildcat-finance/skills/issues/617>, `framework-18`,
  labels `observation` and `origin:ai`, milestone `Wave 2 -- orientation,
  routing and contributor intent`, Atlas verdict "Do now" checked against
  `ab611eb96a6a`; `main` at `5489863196006d8e8b45799d74b56208cac65e4d`.
- Repository authority, Fiat: `plugins/hexaemeron/skills/fiat/SKILL.md`,
  `EVOLUTION.md` (31 rows), `scripts/hexctl.py`, `references/push-discipline.md`,
  `references/prose-pass.md`, `references/plugin-currency.md`,
  `agents/openai.yaml`; `plugins/hexaemeron/agents/{mason,warden,scribe,surveyor}.md`;
  `plugins/hexaemeron/tests/test_hexctl.py`, `github_transport_cases.py`,
  `test_fiat_skill.py`, `test_evolution.py`, `run_tests.py`;
  `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` (`REPORT_FORMATS`).
- Repository authority, root: `AGENTS.md`, `plugins/hexaemeron/AGENTS.md`,
  `INSTALL.md`, `README.md`, `docs/how-to-help-shoggoth.md`,
  `docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md`,
  `ADR-011-load-one-shoggoth-identity-contract.md`, `ADR-019`, `ADR-033`;
  `scripts/contributors.py`; `tests/test_contributors.py`,
  `test_evolution_contract.py`, `test_marketplace_prose.py`,
  `test_version_propagation.py`, `test_shipped_prose_lints.py`,
  `test_boundary_currency.py`, `promise_machine_coverage.json`;
  `.horos/boundary.json`; `.github/workflows/{janus,lazarus,pandects}.yml`;
  the Protasis contract at its installed path, version 4.8.0.
- Change history: merged pull requests #619, #615, #607, #618, #602, #511;
  commits `49ffa06`, `5b1dadb`, `8c5f9b7b`, `c6db32a`, `2ebfc35`, `c4694f1`,
  `2610b68`, `f06294b`; `git log --format='%an <%ae>' | sort | uniq -c` and
  `git log -i --grep='Co-Authored-By: Claude'` over the whole history.
- Audit records: `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md`
  and `.synopsis.md`; `audit/AUDIT.md` lines 11649 to 11690, 12083, 12142,
  12324 and the `Fiat merged attribution` synopsis rows in
  `audit/AUDIT_SYNOPSIS.md`; `plugins/hexaemeron/audit/AUDIT.md` and
  `AUDIT_SYNOPSIS.md`.
- Precedent studies: `docs/elenchus-rpc-boundary-fixtures/study.md` (the
  last run), `docs/berean-question-spans/study.md`,
  `docs/fiat-controller-currency-study.md` (the last Fiat-owned study).
- Organisation: `laurenceday/shoggoth-interceptor` at `23f9761a`,
  `bin/authorship-gate.py` and `tests/test_authorship_gate.py`, read through
  the GitHub contents API.
- Outside: Claude Code settings reference
  <https://code.claude.com/docs/en/settings-reference> (raw Markdown
  downloaded 2026-08-26; sections `attribution`, `attribution.commit`,
  `attribution.pr`, `attribution.sessionUrl`, `includeCoAuthoredBy`,
  `includeGitInstructions`), <https://code.claude.com/docs/en/settings>
  (settings files and who they affect),
  <https://code.claude.com/docs/en/claude-code-on-the-web> (settings files
  committed to the repository apply to cloud sessions; credential proxy),
  <https://code.claude.com/docs/en/web-quickstart> (PR creation from a
  session; silent on attribution); GitHub REST `pulls/{n}` and
  `commits/{sha}` payloads read live for #615, #618, #506, `8c5f9b7b` and the
  accounts `claude` (User, id 81847) and `claude[bot]` (Bot, id 209825114);
  `git interpret-trailers`.

Checks run for this study:

- `git rev-parse HEAD`, `main` and `origin/main` each returned the base
  commit; `git status --short` was empty; `state.json` records
  `controller_currency.verdict: current` at pin `5489863...`, the task issue,
  a waived security suite and `frontier: null`.
- `cmp` of the installed `hexctl.py`, `protasis.py` and `imprimatur.py`
  against the checkout: identical.
- The Hexaemeron suite under `npx --yes --package=node@26.6.0 --call 'uv run
  --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt
  python plugins/hexaemeron/tests/run_tests.py'`: `1285/1285 tests passed`,
  7 minutes 3.66 seconds wall, exit 0.
- `python3 -m unittest discover -s tests`: 396 OK in 28.5 s;
  `/usr/bin/python3 -m unittest discover -s tests`: 396 OK in 39.4 s; both
  print the run-observation inoculation summary with `crashes: 0`.
- `python3 -m unittest tests.test_evolution_contract`: 9 OK.
- `python3 scripts/promise_machine.py check`: `clean: 14 plugin(s), 14
  copy/copies`; `coverage --check`: `clean: promises=71 coverage_rows=71
  coverage_selected=71`.
- `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check
  .`: exit 0, sixteen pairs, every one `committed=match`.
- `phylax.py plugins tests`, `ephoros.py plugins tests`, `hypomnema.py
  README.md AGENTS.md .agents plugins docs`: each `clean`; `horos.py check
  .`: `boundary matches the tree`, exit 0; `git diff --check`: silent.
- `HOST_BYLINE_RE`, `COAUTHOR_RE` and `is_host_identity` imported from the
  checked-in `hexctl.py` and applied to the nine strings in section 1's
  table; results as tabulated. `'claude' in HOST_PR_LOGINS` is `False`;
  `'app/claude'` is `True`.
- `gh api repos/wildcat-finance/skills/pulls?state=all` paginated: every
  non-User author is `claude[bot]`, type `Bot`; #615 and #618 are
  `laurenceday`, type `User`. `commits/8c5f9b7b`: `author.login` `claude`,
  type `User`, committer `Claude <noreply@anthropic.com>`.
- The Protasis checker printed `clean` and Imprimatur exited 0 on
  `docs/elenchus-rpc-boundary-fixtures/study.md`, the register this study
  mirrors.

These checks establish the current state, the two gaps and a buildable
change. They do not establish that option A is implemented, that its tests
pass, or that the settings file changes what a cloud session does.

## 8. signals and the questions behind them

`plugins/hexaemeron/skills/ephoros/SKILL.md` adds no telemetry gate here.
Nothing in this change runs unattended: the controller is invoked from a
terminal and its signals are exit status, stderr and the receipts it already
writes. Three questions the change answers with signals that exist or that
it adds:

1. "Which host default put the refused string there?" The cause clause on
   stderr, tested per site; before this change the answer was nowhere.
2. "Was the body read after creation, and what did it hold?" The `push`,
   `merge-step` and `integrate` receipts already record the `pull_request`
   topology and author login the REST read returned, and the ledger row
   carries the receipt; the procedure adds the operator's own read before it.
3. "Did the read arrive at all?" `github_unreachable`'s fixed shape on
   stderr, which no verdict shares, unchanged here and restated for the
   operator's `gh api` call.

No event, metric, trace, correlation id or alert is warranted.

## 9. boundaries per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` governs the capability. The first
boundary is the pull-request body GitHub returns: untrusted bytes an operator
did not write. Worth taking there: a body that steers the refusal text or the
recovery command. The controls are that the body is only ever searched with a
fixed expression, never echoed, and that every cause and recovery clause is a
constant; `message-no-echo` and `cause-text-guarded` name the checks.

The second boundary is the settings file: a JSON document the host reads on
every contributor's machine and in every cloud session of this repository.
Worth taking there: a key that runs code or grants permission. The controls
are that the file holds one object with three scalar values, that a root
test refuses any other key, and that the ask-first tier names every addition;
`settings-file-shape` names the check.

The third boundary is the read-back itself, one `gh api` call the operator
runs and one the controller already runs. Worth taking: a failed call read as
an empty body. The controls are the transport shape in the controller and the
"failed query is not an answer" rule in the procedure; `readback-transport`
names them.

No new subprocess, network path, dependency, model-output path or persistent
write is introduced by the controller. The settings file's effect is the
host's, documented and bounded to attribution text.

## 10. budget or its absence

`plugins/hexaemeron/skills/metron/SKILL.md` has no gate here. Issue #617
makes no latency, memory or throughput claim, the regex gains one alternation
over strings a few hundred bytes long, and the new tests add a handful of
subprocess-driven cases to a suite that ran 1285 tests in seven minutes
here. No speed-motivated change is authorised, so there is no baseline to
record and no measuring command to name. The suite commands are correctness
gates, not benchmarks.

## 11. fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` governs the failures this run
will hold in hand. Each guard is first observed red against the base tree:
the cause-text table fails because the present messages carry no cause; the
`generated with` coverage row fails because the present expression does not
read it; the footer-reappearance test fails because the present refusal
carries no cause string, and its recovery half passes on both trees, which
the test records by asserting the receipt on the clean body first. The
settings-file test fails because the file does not exist. Each is green on
the changed tree.

What stops the step: a red test in `test_hexctl.py`, `test_fiat_skill.py`,
`test_host_settings.py`, `test_contributors.py`, `test_evolution_contract.py`
or `test_version_propagation.py`; a Hexaemeron suite count below the total
or any error; the root suite red on either interpreter;
`promise_machine.py check` not printing `clean` after the digest re-pin; any
non-zero lint; `horos.py check .` naming a drifted entry that was not
regenerated; a diff to any `HOST_*` set; a receipt whose key set changed; a
refusal message found to contain body or message bytes; any non-zero command
on the demo path. In the loop itself, the posture the change installs is the
one the controller already has: a byline refuses the receipt and nothing is
written, and the new text says how to clear it.

The guard convention: every assertion names the failure it guards, the cause
assertions fail without the clauses, the coverage row fails without the
widened expression, and the lifecycle test fails without the refusal. The
runner contract Warden will hold a fix to is
`npx --yes --package=node@26.6.0 --call 'uv run --python 3.12.13
--with-requirements plugins/lazarus/requirements.txt python
plugins/hexaemeron/tests/run_tests.py {report}'`, report format
`unittest-json-v1`, report file `.elenchus/hexaemeron-unittest.json`; the
wrapper is chosen so the pinned Node fixture passes and the `uv` spelling so
the replay class runs rather than skips in the report Warden reads. The root
suite is an exit command of every step but is not the runner contract,
because it writes no report. On the parent overlay the new assertions fail,
which is the assertion failure `classify` reads as `guarded`; with the
Shoggoth key in the keyring and the wrapper in place the suite records no
error, so a verdict over the whole suite can be `guarded` rather than
`inconclusive`, and the round records which it was.

## 12. decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` puts a decision about one
governed skill in that skill's ledger. The expensive-to-reverse decisions here
are two. First, that a host-identity refusal names a probable cause in fixed
text: once operators and the contributor guide lean on those sentences, a
later change to what they claim rewrites a habit, and a wrong cause sends
someone to fix the wrong thing. Second, that `generated with <host>` is a
byline: once refused, bodies that carried it are gone from the receipted
record and a later narrowing would readmit them. Both go in the
`fiat-v5.27.1` row of `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, whose
change column names the sites, the spelling and the rejected constructions,
and whose evidence column links this study, which holds options B to E in
full.

The read-back procedure lives in `push-discipline.md`, the standing home of
what a run does before publishing, and the `SKILL.md` push note points at it;
the cause clauses in `hexctl.py` cite ADR-016 and this study in a comment,
which is the why-comment Hypomnema asks for. The settings file's explanation
lives in `INSTALL.md`'s Claude Code section, the page a contributor starts
from, citing ADR-016 for the rule and the settings reference for the keys,
and `docs/how-to-help-shoggoth.md` carries the one paragraph a contributor
needs at the front door.

ADR-016 stays unchanged, and no new ADR is written. The rule this change
serves is already recorded there, with the alternative "put the rule only in
local Git configuration" rejected for not travelling; a committed settings
file is not a new rule but a mechanism for the recorded one, it is reversed
by deleting a file, and it decides nothing across plugins. If the settings
file is vetoed, or if a later run wants host configuration for another
harness checked in, that broader question of host configuration in the
repository would earn a record then.

Leads this run records for the run-level pull request's `## Carried forward`
section, with where the evidence lives: whether a `Claude-Session` trailer on
a governed commit is a byline under ADR-016 (this study, assumption 9 and
section 1's table); `checked_login` reading `HOST_PR_LOGINS` only, so the
User login `claude` is refused by the author predicate rather than the
account predicate (section 2); the Interceptor's copied `HOST_BYLINE_RE`
sharing the `generated with` gap (section 2, organisation); the cloud footer's
suppression by `attribution.sessionUrl: false` being documented and not
observed (section 2, outside); and, if vetoed, the undetected terminal
attribution line. The audit rounds go to the file Fiat derives under
`audit/rounds/`, and the exact committed copies of the receipted artefacts
belong at `docs/fiat-host-byline-readback/study.md` and
`docs/fiat-host-byline-readback/runbook.md`.

If implementation needs a new receipt field, a subcommand, a change to a
`HOST_*` set, a settings key beyond `attribution`, a different package
version or a CI change, amend this study before code. A generation row
cannot silently widen the controller's claim or move the held frontier.

### Amendment -- 2026-08-26

**What changed.** The run also upgrades Hypomnema: H001 treats a relative
link inside an inline code span as a quoted specimen and passes over it, the
way H003 already treats a `runbook:` keyword there, recorded as generation
`hypomnema-v4.5.0` retaining `design-bridge-check`, its digest, status `open`
and the held job; the widened rule, its guards, the `SKILL.md` sentence and
the ledger row land in step 1. Step 1 also places the host-identity guards in
`plugins/hexaemeron/tests/host_identity_cases.py`, mixed into the two
`test_hexctl.py` classes, because the promise-machine inventory reads
`test_hexctl.py` under a 256 KiB bound, and re-pins the controller digest in
`plugins/hexaemeron/tests/test_issue_429_recovery.py` beside the six
bindings in `tests/promise_machine_coverage.json`.
**Why.** Line 805 of this study quotes the ledger row's relative link in
Markdown link syntax inside a code span. Committed at
`docs/fiat-host-byline-readback/study.md`, H001 resolves it from that
directory, reports `resolves to nothing`, and the two Hexaemeron tree-walk
tests fail with the lint. The receipted bytes cannot change, the committed
copy must stay exact, and a pragma is an edit; the one fix that makes both
green is the code-span rule H003 already has.
**Steps touched.** Step 1's Files and Tests. Step 2 is unchanged.
**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit holds.
