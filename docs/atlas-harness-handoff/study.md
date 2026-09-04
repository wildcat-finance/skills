# Study: test the remaining Atlas hand-offs before adding README buttons

Issue [#856](https://github.com/wildcat-finance/skills/issues/856), framework-13.
Run branch `fiat/856-framework-13-test-the-remaining-atlas-hand-o`, cut from
`main` at `8dc3aca54adeca49387a2bdfc174cf6e72d02a11`.

## Assumptions

Proceeding on these unless corrected:

1. The issue's `Current review: 26 August 2026` header is the instruction. The
   `Original filing` block is evidence of what was true on 24 August 2026, and
   its client versions, measurements and host attribution are not instructions.
2. The target is `wildcat-finance/skills` at the base ref above. Changes to
   `wildcat-finance/shoggoth-wave-atlas` are out of this run's reach; the study
   reads that repository and records what it found, and any route work there is
   a separate delivery.
3. The prose surfaces the issue calls "README and PDF" are three files:
   `README.md`, `docs/how-to-help-shoggoth.md`, and the PDF that
   `scripts/build_contributor_guide.py` draws at
   `docs/pdf/how-to-help-shoggoth.pdf`. There is no PDF of `README.md`.
4. The six harnesses in scope are GitHub Copilot, Cursor, Gemini CLI, Windsurf,
   Cline and Roo Code. Codex and Claude Code keep the native-package status the
   24 August checks gave them, and `/go/chatgpt` and `/go/claude` keep theirs.
5. Python is the interpreter pinned in `.python-version`, with the standard
   library `unittest`. The repository suite is `python3 scripts/run_checks.py`.
6. No harness account, licence or seat will be created for this run. That
   assumption picks the design; if it is wrong, section 4 changes.

## 1. Problem statement

The repository tells contributors which AI coding harness can pick up an Atlas
job and how. Two web routes are described as checked, six local harnesses are
described in a table, and none of those six descriptions rests on a recorded
client run. The issue asks for the run first and the button second.

Built for: the maintainer who decides whether a harness earns a launch button,
and the external contributor who reads the roster and picks one.

A working prototype here is a repository that can state, per harness, what was
observed and by which command, and whose reader-facing wording is produced from
that record rather than typed next to it. It does not require that any harness
pass. It requires that the roster cannot say a harness passed unless a run is
recorded, and that a stale roster becomes visible instead of staying quiet.

Demo path, run from the repository root:

```bash
python3 scripts/probe_harnesses.py --out docs/harness-classification.json
python3 scripts/render_harness_roster.py --check
python3 scripts/build_contributor_guide.py
python3 -m unittest tests.test_harness_manifest -v
```

The first command re-establishes the record on the host it runs on. The second
fails when any of the three wording surfaces has drifted from the record. The
fourth is the binding suite. Success is those four commands at exit zero with
the tree clean afterwards.

## 2. Prior art

### In this repository

The harness roster exists three times, hand-written, with nothing binding the
copies to each other.

- `README.md` lines 313 to 324, inside `## Contribute`. Three shields.io badges:
  `/go/chatgpt`, `/go/claude`, and `/api/job` as a manual prompt. No table. Of
  the six harnesses in scope, `README.md` names none. Codex appears at line 273
  as an install pointer, not a launcher.
- `docs/how-to-help-shoggoth.md` lines 126 to 139, heading `### Local
  harnesses`. A three-column table, `Harness | Supported route | Checked limit`,
  with six rows: Codex, Claude Code, GitHub Copilot, Cursor, Gemini CLI,
  Windsurf. Every one of the six carries the identical `Checked limit` value,
  `No checked one-click Atlas launcher`, so the column separates nothing. Cline
  and Roo Code have no row and appear only in the exclusion sentence at lines
  137 to 139.
- `scripts/build_contributor_guide.py` lines 333 to 399. The two bootstrap
  buttons are hardcoded, and the manual harnesses are one hand-typed string,
  `"GitHub Copilot  /  Cursor  /  Gemini CLI  /  Windsurf"`, under a `Manual
  only` label.

No test reads any of it. `tests/test_marketplace_prose.py` line 323 opens
`README.md` and the guide but asserts only on identity wording.
`plugins/hexaemeron/tests/test_fiat_skill.py` class `HostGuidanceTests` reads
harness names out of the guide's byline paragraph, not the roster table. There
is no test for the badge URLs, the table rows, the generator, or either PDF.

The strings `go/copilot` and `tested local route` appear nowhere in the tree.

### The two merged pull requests that changed this subject

`docs/overhaul external contribution path`, commit `b7fc2cb9`, merged by
`6c98a728` as pull request #528 on 24 August 2026, introduced the badge block,
the harness table and the sentence separating checked web routes from manual
local ones. It also added `scripts/build_contributor_guide.py`. The pull request
itself returns HTTP 404 from the API; its merge commit message and diff are the
record that remains readable.

`docs: rewrite Shoggoth as a contributor-ready crypto R&D collective`, commit
`daa64e5f`, merged as pull request #1003 on 31 August 2026, rewrote the same
prose. Its body records boundaries and verification and carries no unfinished
work forward on this subject: `Root-Issue: none-recorded`. Nothing from either
pull request is left open here except the roster duplication itself, which
neither one closed and which this study answers in section 4.

That change also removed the PR #479 link from the contributor prose.
`tests/test_marketplace_prose.py` lines 331 and 332 now assert that `pull/479`
and `PR #479` are absent from `README.md` and the guide. Acceptance condition 2
asks the hand-off to retain "the link to PR #479"; a live test forbids that link
in the two documents. Reading chosen: condition 2 means the launcher must
preserve `job.prompt` byte for byte, and the enumerated items are checked
against the prompt's current content rather than against the August wording.
The current prompt carries the issue number and the checkpoint sentence and
carries no reference to pull request 479.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` ran
from the target root and exited zero, with all 62 records reporting
`budget=pass` and `committed=match`. The synopsis is therefore the admitted
reading view, and it was the view read for the 55 per-run records under
`audit/rounds/` and for the six plugin-local records. Three sources were read
directly rather than through a synopsis, because a search had to reach text the
condensed view drops: `audit/AUDIT.md`, `audit/rounds/fiat-859-reinstate-the-wave-delta-distributed-checkpo.md`,
and `audit/rounds/fiat-1057-record-an-open-issue-s-status-where-the-cen.md`.

No audit round in this repository has ever reached a verdict on an Atlas
hand-off, a launcher, or a per-harness route. The standing position is recorded
absence, not a pass:

- `audit/rounds/fiat-1057-...:7` reads `Not checked: the Atlas dependency extractor
  itself, which lives in another repository and was neither run nor read`.
- `audit/rounds/fiat-447-...:7` reads `Not checked: ... live Atlas, Kronos, Fiat,
  claim-comment, release-comment and GitHub publication behaviour`.
- `audit/AUDIT.md`, risk id `current-main-loss`, names the Atlas only as a base
  path that must survive a rewrite.
- `audit/rounds/fiat-859-...:227`, finding `S5-R1-01`, severity low, is about a
  packet naming two repositories, not about a launcher.
- `audit/AUDIT_SYNOPSIS.md` lines 356 to 363 carry `[missing legacy field:
  audit-schema]`, `[missing legacy field: covered]`, `[missing legacy field:
  not-checked]` and `[missing legacy field: elenchus-verdict]` for the
  fiat-434-era rounds. Those stay unknown.

Nothing is carried forward from the audit history, because nothing in it judged
this subject.

### The Atlas, read at `ce866e3d7e8b489fcb8b70c608f7af72d9b7a673`

`app/go/chatgpt/route.ts` and `app/go/claude/route.ts` each pick a random
eligible job, put `fiatPrompt(job)` into a `q` parameter and return HTTP 307
with `Cache-Control: no-store`. No job means HTTP 503. The Atlas `tests/`
directory holds six files and none covers either route, so the guide's claim at
line 117 that the two routes are "covered by the Atlas launcher tests" points at
tests that do not exist.

A live read confirmed the deployment answers: `GET /api/job` returned HTTP 200,
`read_from: live`, `source_revision` equal to this run's base ref, 119 eligible
jobs and a 1481-character `job.prompt`. `GET /go/claude` returned HTTP 307 to
`https://claude.ai/new` with the prompt in `q`.

### Outside both repositories

- GitHub documents `ghapp://session/new` with `repo`, `pr`, `branch`, `prompt`
  and `mode`, where `mode` takes `plan`, `interactive` or `autopilot`. The `plan`
  value is a read-only mode the August record did not have. The Copilot app
  reached general availability on 17 June 2026 and is offered on every Copilot
  plan, including Copilot Free, or with a caller-supplied model key.
- Cursor publishes no deep link. Its agent CLI takes `-p` for a prompt and
  `--mode=ask` or `--plan` for read-only work.
- Gemini CLI publishes no deep link. It takes `--prompt` or `-p` and
  `--approval-mode plan`.
- The Windsurf Cascade documentation URL now returns HTTP 307 to
  `docs.devin.ai/desktop/cascade/cascade`, which documents Cascade inside Devin
  Desktop under the Cognition and Devin brand. No prompt launcher is published.
- Cline publishes no deep link. It takes `-p` or `--plan` and `--auto-approve
  <boolean>`, and its positional-prompt form still defaults to act mode with
  auto-approval on, so the hazard the August record named is unchanged.
- `RooCodeInc/Roo-Code` reports `archived: true` with `pushed_at`
  `2026-05-15T18:08:47Z`. The organisation's other repositories are
  documentation, evaluation and JetBrains trees last pushed between June 2025
  and May 2026. No active successor client was found.

## 3. Constraints and non-goals

Starting ref `8dc3aca54adeca49387a2bdfc174cf6e72d02a11` on `main`. Interpreter
pinned by `.python-version`, standard-library `unittest`, root suite
`python3 scripts/run_checks.py`. Atlas read at
`ce866e3d7e8b489fcb8b70c608f7af72d9b7a673`. Host: darwin 25.5.0 on arm64.

### What this host can and cannot do, per harness

Each row was probed on 4 September 2026 by the commands named in
`.hexaemeron/design/harness-evidence.json`. Client absence and authentication
absence are recorded separately, because they are different findings.

| Harness | Client here | Auth configured | Published prompt launcher | Runnable here |
| --- | --- | --- | --- | --- |
| GitHub Copilot | No. Absent from `PATH`; no desktop app in `/Applications`; `gh copilot --version` prints `Copilot CLI not installed` | No. `gh api user/copilot_seat` returns HTTP 404 for the active account; the organisation reports zero seats, `seat_management_setting: unconfigured` and `cli: unconfigured` | Yes, `ghapp://session/new` | No |
| Cursor | No. `cursor` and `cursor-agent` absent from `PATH`; no app; no application-support directory | No. `~/.cursor/cli-config.json` holds settings keys only and no credential | No | No |
| Gemini CLI | No. Absent from `PATH`; the global `node_modules` root holds only `@anthropic-ai` and `npm` | No. No `~/.config/gcloud`; no `GEMINI_*` or `GOOGLE_*` variable | No | No |
| Windsurf | No. Absent from `PATH` and `/Applications`; no `~/.windsurf` or `~/.codeium` | Not applicable | No, and the product is now published as Cascade inside Devin Desktop | No |
| Cline | No. Absent from `PATH`, from global `node_modules`, and from `~/.vscode/extensions` | No. No configuration directory, so `cline auth` has never run here | No | No |
| Roo Code | Not applicable, the product is sunset | Not applicable | No | No |

`~/.cursor`, `~/.gemini` and `~/.copilot` all exist with a modification date of
24 August 2026 and hold settings and history but no client and no credential.
They are residue of the filing's own probe run, and reading them as a present
installation would be the error this table exists to prevent.

The consequence is stated plainly: acceptance conditions 2, 3 and 4 ask for
authenticated read-only client runs of five harnesses, and not one of the five
can be run on this host without either an organisation policy change or a new
account. The issue's own boundary forbids both. This run therefore delivers the
record and the machinery, and records five named blockers instead of five
passes.

### Non-goals

- No Atlas route is added, changed or tested in this run. `/go/copilot` is not
  created. The missing route tests for `/go/chatgpt` and `/go/claude` are a
  finding recorded against the other repository, not work done here.
- No harness earns a launch button in this run. The badge block keeps the two
  web routes it has.
- No claim about whether Fiat checkpointing is finished is revisited. The
  prompt's checkpoint sentence is read as bytes to preserve, not as a statement
  to verify.
- Codex and Claude Code are not re-probed. Their August result stands as
  recorded, and the manifest carries it with its recorded date.

### Always

Both suites before a commit. The Imprimatur lint on every shipped document. A
recorded measurement before any performance claim.

### Ask first

Adding a dependency. Enrolling any account in any harness plan, free or paid.
Changing an organisation policy setting. Touching CI. Editing a byte of any file
under `audit/`.

### Never

Store a harness credential, session token or model key anywhere in the tree, in
the manifest, or in a probe log. Record a harness as `tested local route` or
`Atlas launcher` without a recorded client run. Delete a failing test to green a
suite. Claim a command ran when it did not.

## 4. Design options

Three constructions were drawn. The record at
`.hexaemeron/design-evidence.json` selects one from checked gates; this prose
explains what they are.

**`hand-record`.** A maintainer writes the test record by hand and edits the
three wording surfaces to agree with it. It is the cheapest construction to
start and the only one that needs no new code. It trades away every guarantee
that the surfaces still agree a month later, and it can only be completed by
someone who can actually run all six clients.

**`probe-manifest`, selected.** One probe script records, per harness, whether
the client is present, its exact version when it is, whether an authentication
method is configured, and what the client's current published contract offers.
It writes one manifest. A renderer generates the README badge block, the guide
table and the PDF harness page from that manifest, and a test fails when any
surface drifts. It trades a build step and a schema for the property the issue
actually wants: a roster that cannot outrun its evidence. Harnesses that cannot
be run here are classified `manual route` and carry their exact blocker.

**`contract-manifest`.** The same generated surfaces, but the manifest is
maintained by hand from the published client contracts, with no machine probe.
It is simpler than `probe-manifest` and keeps the single source. It cannot
record a client version or an authentication state, because it never looks at
the host, so it cannot satisfy acceptance condition 1.

### How the record decided

Three gates were resolved at selection, each computed by
`python3 .hexaemeron/design/evaluate.py` from the recorded probe evidence and
the declared constructions.

| Candidate | `earned-class-only` | `per-harness-evidence` | `credential-free` | `hand-edit-sites` |
| --- | --- | --- | --- | --- |
| `hand-record` | pass | pass | **fail** | 3 |
| `probe-manifest` | pass | pass | pass | 1 |
| `contract-manifest` | pass | **fail** | pass | 1 |

`hand-record` is removed because it cannot be completed with the credentials
this host has: six harnesses need an authenticated client run and none has one.
`contract-manifest` is removed because it emits only the launcher contract and
never the client presence, version or authentication state that condition 1
names. `probe-manifest` is the one surviving candidate, so `unique-frontier`
holds.

`hand-edit-sites` counts each candidate's declared wording surfaces. It is a
count over a declaration in `.hexaemeron/design/candidates.json`, not a
measurement of a built tree, and it is reported that way rather than as an
observation. The three sites it counts for `hand-record` are the three that
exist in the tree today.

Three gates stay pending against later transitions. `roster-single-source` and
`wording-regen-budget` are due at `step:4`, the step that makes the surfaces
generated. `killed-probe-recovery` is due at `step:3`, the step that first
writes the manifest. Each names its resolver and its future report path in the
record.

### The one question this study does not answer

The Copilot desktop app is now offered on every Copilot plan, including Copilot
Free, which costs nothing. The issue's boundary forbids "signing up for paid
plans". Does that boundary also forbid enrolling the active account in Copilot
Free, which would make the `ghapp://session/new` hand-off testable here?

A yes leaves Copilot as `manual route` with its blocker recorded, which is what
the selected design builds. A no adds one step that runs the deep link in
`mode=plan` and can move Copilot to a tested class. The runbook is written for
yes and says so; a no is an amendment, not a rewrite.

## 5. Risk register seed

The probe reads a host, shells out to client binaries, parses their output and
writes a file that generates public prose. Every one of those is a place where a
wrong answer becomes a published claim. The register below is what the audit
loop enumerates; the ids are how a round cites a line.

The two that matter most are `unearned-class` and `credential-leak`. The first
is the issue's whole point: a roster that can say "tested" without a run is
worse than no roster, because a contributor trusts it. The second is the
boundary the issue draws in its own last paragraph, and a probe that prints a
client's diagnostic output is exactly how a token reaches a log.

```risk-register
unearned-class | the classifier that turns probe output into a roster class | no input path can produce `tested local route` or `Atlas launcher` without a recorded client run, and a test asserts it
credential-leak | the manifest, probe log and any captured client output | no token, key, cookie or session identifier reaches the manifest, the log or the tree, checked by a pattern test over both
probe-subprocess | the argv of each spawned harness client | argv is a fixed list with no shell, the binary is resolved from PATH by exact name, and no probe input comes from the manifest
absent-versus-unavailable | the per-harness record for a client that did not answer | absence from the host and a failed authentication are separate recorded fields and never collapse into one verdict
stale-manifest | the manifest's recorded date against the surfaces it generated | the renderer refuses a manifest whose recorded host or date does not match the run that produced the surfaces
partial-manifest-write | the manifest file during a probe that is killed | a killed probe leaves either the previous manifest or nothing, never a half-written file the renderer would accept
network-absent | the launcher-contract field for a client whose documentation could not be read | an unreadable contract is recorded as unread with its reason, and never as absent
roster-drift | the three generated wording surfaces against the manifest | the check mode fails when any surface differs from what the manifest renders
atlas-claim | the guide sentence claiming Atlas launcher tests cover the two web routes | the sentence is corrected to what the Atlas repository actually holds, which is no route test
pdf-nondeterminism | the generated PDF bytes across two runs of the builder | the harness page's text content is compared, not the whole PDF, so a timestamp does not fail the suite
```

## 6. Glossary seeds

- **Hand-off.** The path from an Atlas job to a harness holding that job's
  prompt, ending before any repository change.
- **Atlas launcher.** A route under `/go/` that allocates a job and opens a
  client with its prompt, proven by a recorded client run.
- **Tested local route.** A local client path proven by a recorded read-only
  client run against this repository.
- **Manual route.** A path a person follows by hand: open the repository, read
  `AGENTS.md`, paste the prompt. No launcher claim.
- **Unsupported.** No active product to test.
- **Manifest.** `docs/harness-classification.json`, the one record every roster
  surface is generated from.
- **Probe.** `scripts/probe_harnesses.py`, the re-runnable command that writes
  the manifest from what the host actually shows.
- **Blocker.** The exact named reason a harness could not reach a tested class,
  recorded beside its classification.
- **Residue.** A configuration directory left behind by a client that is no
  longer installed. Not evidence of a present client.

## 7. Sources

- Issue #856, `wildcat-finance/skills`, read 4 September 2026, including its
  26 August review header and its preserved original filing.
- `wildcat-finance/skills` at `8dc3aca54adeca49387a2bdfc174cf6e72d02a11`:
  `README.md` 313-324, `docs/how-to-help-shoggoth.md` 111-139 and 260,
  `scripts/build_contributor_guide.py` 30-35 and 333-399, `AGENTS.md` 1-15 and
  220-227, `.agents/skills/promise-machine/SKILL.md`,
  `tests/test_marketplace_prose.py` 322-332.
- Commits `b7fc2cb9` and `6c98a728` (pull request #528, API returns 404) and
  `daa64e5f` (pull request #1003).
- `audit/AUDIT.md`, `audit/AUDIT_SYNOPSIS.md`, and the 55 records under
  `audit/rounds/`, with `audit_synopsis.py --check .` at exit zero.
- `wildcat-finance/shoggoth-wave-atlas` at
  `ce866e3d7e8b489fcb8b70c608f7af72d9b7a673`: `app/go/chatgpt/route.ts`,
  `app/go/claude/route.ts`, `app/job.ts`, `app/api/job/route.ts`, `README.md`,
  `tests/`, `.github/workflows/release-verification.yml` line 39.
- Live Atlas at `https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site`,
  read 4 September 2026.
- GitHub Copilot deep links,
  `https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/github-copilot-app/open-with-deep-links`.
- GitHub Changelog, Copilot app generally available, 17 June 2026, and
  available to all, 7 July 2026.
- Cursor CLI, `https://cursor.com/docs/cli/overview`.
- Gemini CLI reference,
  `https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/cli-reference.md`.
- Cascade, `https://docs.windsurf.com/windsurf/cascade/cascade`, which returned
  HTTP 307 to `https://docs.devin.ai/desktop/cascade/cascade`.
- Cline CLI, `https://docs.cline.bot/usage/cli-overview`.
- `https://github.com/RooCodeInc/Roo-Code`, and the `RooCodeInc` repository
  listing.
- `.hexaemeron/design/harness-evidence.json`, which records every probe command
  and its result.

## 8. Signals, and the questions behind them

The probe is a command someone runs, so it has no unattended on-call life of its
own. The manifest it writes does, because generated prose keeps being served
long after the run that produced it. Two questions apply, and one does not.

**"Is the roster the site is showing still true?"** The manifest carries the
host, the date and the base ref of the run that wrote it. The renderer's
`--check` mode is the signal: it exits non-zero when a surface no longer matches
the manifest, and it is wired into the repository suite, so a drifted roster
fails a normal test run rather than waiting for a reader to notice. Emitted by
step 4.

**"Why did this harness get the class it got?"** Every manifest entry carries
the probe command, its observed result, and the blocker when there is one. A
reader asking why Copilot is `manual route` gets the seat check and the
organisation policy value, not an adjective. Emitted by steps 2 and 3.

No alert, no metric series and no trace. Nothing here runs unattended, so there
is nobody to page. [ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry.

## 9. Boundaries, per capability

Three boundaries open, and each is a line in section 5 as well.

**Spawning a harness client.** Worth taking because the issue's whole demand is
an observed client rather than a documented one. Closed by a fixed argv list
with no shell, an exact binary name resolved from `PATH`, no probe argument
sourced from the manifest, and a bounded timeout on every spawn. Line
`probe-subprocess`.

**Handling whatever that client prints.** Worth taking because a version string
is the only honest way to record a version. Closed by writing only fields the
schema names, never raw client output, and by a pattern test over the manifest
and the log for token, key, cookie and session shapes. Line `credential-leak`.

**Reading a client's published contract over the network.** Worth taking
because a launcher that no longer exists must not stay in the roster. Closed by
recording an unread contract as unread with its reason, never as absent, and by
never letting a fetched document decide a class on its own. Line
`network-absent`.

A fourth capability is deliberately not opened: the probe authenticates nothing
and stores nothing. [phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and the controls.

## 10. The budget, or its absence

One budget, because the probe and the renderer both land in the repository
suite and a slow check is a check people skip.

The whole regeneration path completes inside 60 seconds on this host, measured
by:

```bash
python3 .hexaemeron/design/time_wording_regen.py \
  --report .hexaemeron/reports/probe-manifest-wording-regen-budget.json
```

That is the resolver named for the `wording-regen-budget` gate, which blocks
`step:4`. The 60-second figure is a ceiling chosen against the existing
`scripts/build_contributor_guide.py` run, not a measured baseline; the resolver
produces the baseline at step 4 and the gate fails if the ceiling is wrong.

No budget applies to the probe itself, because it is a command a person runs
deliberately and its cost is dominated by client startup, which this repository
does not control.
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget
carries and how it is checked.

## 11. The fail-closed posture

The probe stops the run when it cannot tell what it saw. An unrecognised client
response, a spawn that times out, a schema violation, or a manifest write that
cannot complete all end the command at a non-zero exit with the previous
manifest untouched. It never falls back to a guessed class, and it never
downgrades a harness silently: a harness it could not read keeps its recorded
prior entry and gains an unread marker.

The renderer fails closed the other way. `--check` refuses to pass when a
surface differs from the manifest, when the manifest is missing, and when the
manifest's recorded run does not match the surfaces it is being checked
against.

A fix for any failure here follows the guard convention: reproduce, reduce to
the smallest case, fix the cause, and land a test that fails without the fix.
The runner contract each step's `Tests` field names is the exact command Warden
receives, with one `{report}` argument.
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage
order and the guard rule.

## 12. Decisions and their homes

Three decisions here are expensive to reverse, because other things get written
against them.

**The manifest schema.** Once `docs/harness-classification.json` generates
public prose and a suite binds to it, changing its field names is a change to
three surfaces and a test at once. Record: a new ADR under `docs/adr/`.

**The four classification names.** `Atlas launcher`, `tested local route`,
`manual route` and `unsupported` become the vocabulary of the roster, the tests
and every later harness discussion. Renaming one later rewrites history that
readers have already seen. Record: the same ADR.

**Reading acceptance condition 2 as "preserve `job.prompt` byte for byte", with
the PR #479 clause treated as stale.** This one resolves a direct conflict
between the issue and a live repository test, and a later reader who does not
know it was decided will re-open it. Record: the same ADR, with the test lines
cited.

Not recorded: which harness got which class in this run. That belongs in the
manifest, where it is regenerated, not in a decision record that would freeze
it. [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each one lives.

### Amendment -- 2026-09-04

**What changed.** The study now carries the explicit bridge from its selected
design to the standing record that holds it:

```design-bridge
schema | hypomnema-design-bridge/v1
decision | probe-manifest
record | docs/decisions/ADR-074-generate-the-harness-roster-from-one-probed-manifest.md
```

**Why.** Hypomnema study mode reports H008 against a shipped study whose chosen
design reaches no standing record by an exact declared identifier. Step 1 wrote
that record as ADR-074 and the prose names it, but nothing bound the two
mechanically, so a reader had to take the join on trust. The bridge states it.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Two corrections, both to checkable quantities the audit found
wrong. Neither changes a conclusion.

The Audit records paragraph in section 2 gives three figures and none is right.
Recomputed at this run's own base `8dc3aca54adeca49387a2bdfc174cf6e72d02a11`:
`audit/rounds/` holds 108 files, exactly half of them `.synopsis.md`, so there
are 54 per-run records and not 55. Five plugin trees carry an `audit/AUDIT.md`,
for ariadne, hexaemeron, pandects, probitas and tabularium, and not six. With
the root `audit/AUDIT.md` that is 54 plus 5 plus 1, so the synopsis check reports
60 records and not 62. The paragraph's own arithmetic disagreed with itself as
well: 55 and six make 61, which is neither figure it states.

Section 12 records the manifest schema's home as a new ADR under `docs/adr/`.
No such directory exists. Decision records live in `docs/decisions/`, which held
72 files at the base ref, 71 of them ADR-numbered. The record this run actually
wrote is `docs/decisions/ADR-076-generate-the-harness-roster-from-one-probed-manifest.md`.

**Why.** Three audit rounds each found a wrong checkable quantity in a document
whose lints were clean, because nothing in this repository asserts study or
decision-record prose against the facts it cites. The remaining claims in
sections 2 and 12 were then re-derived one by one rather than sampled. The
README badge block at lines 313 to 324 with its three badges, Codex at line 273,
the six-row guide table at lines 126 to 139 with its identical Checked limit
column, the exclusion sentence at lines 137 to 139, the builder's hardcoded
harness string at line 389 under the Manual only label at line 386, the prose
test at line 323 and its two assertions at lines 331 and 332, the guide's
launcher-test claim at line 117, and the absence of both `go/copilot` and
`tested local route` from the tree all hold as written. The two figures above
were the only defects.

One trap for anyone re-deriving the ADR renumber interval. The commit that wrote
the record has an author date of 00:25:51Z and a commit date of 00:45:16Z, and
`git show` prints the author date. Using it against the colliding merge at
01:40:30Z gives 74.65 minutes. The interval stated in ADR-076 is 55 minutes,
measured commit date to merge, which is the comparison that matches when each
tree actually existed.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** The previous amendment listed the section 2 sentence about
`go/copilot` and `tested local route` among claims that hold as written. That
was wrong, and this corrects it.

The sentence reads that both strings appear nowhere in the tree. It was true of
the tree it surveyed, at `8dc3aca54adeca49387a2bdfc174cf6e72d02a11`, where
neither string occurs in any tracked file. It is false of the tree that ships
it. This step committed the schema, the manifest tests, the decision record and
the pinned copies of these two artefacts, and those files use both strings as
their working vocabulary. The audit record for this run names them too.

Read the sentence as scoped to the surveyed ref. Every other claim the previous
amendment listed was checked against that same ref, and the amendment said so
for the recomputed figures; this one clause asserted the present tense instead,
which the step's own commits had already falsified.

**Why.** An amendment that corrects a document and introduces a false statement
while doing so is worse than the defect it corrects, because a reader who checks
it against the shipped tree finds it wrong at the point where the record claims
to have been verified. The audit raised it as a low finding and it is cheap to
answer, so it is answered rather than carried.

No quantity is restated here. Four wrong checkable quantities have been produced
in this document across four audit rounds, three of them inside a correction
rather than in the original work, and each restatement has been a fresh chance
to be wrong. Nothing in this repository asserts study or decision-record prose
against the facts it cites, which is the gap behind all four and is being
carried forward as its own item.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Section 3 now carries the known false reds of the root suite.
The runbook's shared preamble already attributes them to this study's
constraints, and section 3 did not state them. The pair is corrected as well,
because the version the runbook carries describes one red and this run met the
other.

A red reported as `WAI-E-ADAPTER.TIMEOUT` always arrives from a child, never
from the check harness. `scripts/run_checks.py` holds no `WAI-` string at all.
Every refusal carrying that code is raised in `scripts/agent_instruction.py`, at
lines 1376, 1408 and 1413, and it reaches a suite report through
`tests/test_agent_instruction.py`, which asserts on the code at line 2560 and is
discovered by `root-suite`. Under parallel load those adapter timeouts fire and
the code appears in the failure text. That red is load, and `--jobs 1` answers
it.

A suite that outruns its own per-check ceiling reports nothing of the kind. The
ceiling is `DEFAULT_TIMEOUT_SECONDS = 1_800` at `scripts/run_checks.py:51`, and
`hexaemeron-suite` inherits it, declaring no `timeout_seconds` of its own in
`tests/check-map-v1.json`. A breach is recorded with
`failure_class="command-failure"` and `reason="timeout"` at
`scripts/run_checks.py:2292`, and carries no `WAI-` code. This is the red step
2's first audit round met, as `hexaemeron-suite failed at 1800.4s` with that
suite alone green when run by itself.

The two are separable by the field the harness sets. A suite whose tests fail is
recorded `test-failure` at `scripts/run_checks.py:2316`, so `command-failure`
with `reason: timeout` on a `kind: suite` check is a ceiling breach rather than
a defect. Rerun the named suite on its own, or the root suite with `--jobs 1`.

The third constraint stands as the runbook states it. A Python pin check that
comes back one short is usually a stale sibling under `.claude/worktrees/`
rather than the diff.

**Why.** Step 2's first audit round found that the runbook's clause did not
cover the red this run hit, so a reader meeting a ceiling breach had no written
ground to call it load, and the clause they did have pointed at a subsystem that
was not running. That clause sits in the runbook's shared preamble, and
`hexctl amend runbook` replaces only a step's `Goal`, `Entry`, `Exit`, `Files`,
`Tests` or `Disciplines` field, so no amendment can reach the preamble. The
correction goes where the preamble already says the constraint lives. The
runbook's own narrower sentence stays as receipted, and that residue is carried
forward rather than reported as fixed.

**Steps touched.** Step 2, step 3, step 4, step 5.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** The decision record this run wrote is renumbered from
`docs/decisions/ADR-076-generate-the-harness-roster-from-one-probed-manifest.md`
to `docs/decisions/ADR-077-generate-the-harness-roster-from-one-probed-manifest.md`.

`origin/main` acquired a different `ADR-076-digest-neutral-measured-corpus.md`
in `530efcec`, which is not an ancestor of this run's branches, so the number
this run had held since `be5ded32` collided when that ref reached this clone.
`tests/test_decision_records.py` compares numbers against the default branch, so
the root suite turned red between step 2's second and third audit rounds with
nothing in the run having changed. On `origin/main` the numbered records run to
ADR-076, and no open pull request and no remote branch carries an ADR-077 file,
so ADR-077 is free as read today. Nothing reserves it, so it is rechecked
immediately before the step is pushed rather than trusted from this reading.

Two references to the superseded number cannot be corrected, and are recorded
here rather than left to look like oversights. The `design-bridge` block added by
the first amendment above names ADR-074, inside a fenced block an amendment can
only follow and never rewrite. Step 1's baseline `Exit` and `Files` fields in the
runbook name ADR-074 as well, and step 1 is complete, so `hexctl amend runbook`
refuses to touch them. Both keep a name no file in the tree carries. The path
this amendment states is the record's real one, and it is the path the schema,
the probe and the shipped copies are corrected to.

**Why.** The collision is the second one this run has taken on the same record,
and it arrives from outside: issue 888 is reconstructing ADR numbering to assign
at merge rather than at authoring, and until that lands any number held across a
run is a number that can be taken. Recording the renumber in the study matters
more than the number itself, because three wording surfaces are generated from
this record in the steps that follow, and a reader who finds ADR-076 in the
runbook's completed fields needs the reason stated somewhere reachable. The two
uncorrectable references are named for the same reason: an append-only amendment
mechanism cannot revise a baseline field of a finished step or the inside of a
fenced block, so the honest record is that they are stale and why.

**Steps touched.** Step 2, step 3, step 4, step 5.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
