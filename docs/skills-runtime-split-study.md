# Study: move the skills.sh payload to its own repository

Assuming, unless corrected:

1. The starting ref is `main` at `bc38cbae49be7e16dde4e3f54a1e1bc21c5c4fc8`, the
   merge that landed ADR-054.
2. The exact interpreter in `.python-version`, with stdlib `unittest`.
3. `wildcat-finance/skills` stays public, and the new repository is public too.
   A private destination cannot be cloned by the skills CLI without auth.
4. The destination is `wildcat-finance/skills-runtime`, named by the operator.
5. An hourly distribution lag is accepted. The operator stated this when
   reversing ADR-054.
6. The publishing account holds the `workflow` scope, so a workflow file can be
   pushed to the destination once by hand. The hourly job never rewrites one.

## 1. Problem statement

Issue #949 reverses ADR-054. The generated payload leaves this tree and is
rebuilt hourly in `wildcat-finance/skills-runtime`.

A working result is: `npx skills add wildcat-finance/skills-runtime --skill
promise-machine` installs a package that passes its own offline verification;
this repository's root suite passes from a fresh clone with the generated
payload absent; and the destination's workflow refuses to publish a package that
fails verification. The demo path is that install command run against the
published destination, followed by the package's own `verify_runtime.py`.

## 2. Prior art

**The record being reversed.** ADR-054, merged in
[#947](https://github.com/wildcat-finance/skills/pull/947) as `bc38cbae`, kept
the payload in tree. It refused relocation on two grounds and both were weaker
than stated. It said a separate repository breaks the grouping and the ref-less
install; that is true of this repository's grouping only, because a separate
repository carries its own `skills.sh.json` and its own address. It said the
arrangement needs a fine-grained token; that applies to a cross-repository push,
and the workflow can instead run in the destination and commit to itself.
Issue #949 records both corrections. ADR-040 remains the record that made the
payload dependency-closed, and its five rejected alternatives still stand
against the constructions they describe.

**What the previous run left.** #947's `Carried forward` names five items. Three
bind here: the sync coupling stays with #854; the footprint guard's ceilings
were never established as correctly sized; and the guard measures a tree that
this run empties, so it must move to the generated output or go. The other two,
the unasserted recorded figures and the ADR numbering collision surface #888
owns, are carried again rather than closed.

**The generator.** `scripts/portable_promise_machine.py` is 334 lines with two
actions, `check` and `sync`, and a suppressed `--root`. `TARGET` is the constant
`.agents/skills/promise-machine/runtime`, so the destination directory is
hardcoded rather than passed. `ROOT_FILES` is an explicit allowlist of 20 source
paths, and one of them is `.agents/skills/promise-machine/SKILL.md`: the
authored router is a source the generator copies, not generated output.

**Authored against generated.** Under `.agents/`, 995 tracked files sit beneath
`runtime/` and are generated. Exactly four do not:
`.agents/plugins/marketplace.json`,
`.agents/skills/promise-machine/PORTABLE.md`,
`.agents/skills/promise-machine/SKILL.md` and
`.agents/skills/promise-machine/scripts/verify_runtime.py`. Those four are
authored here.

**Why the four authored files stay put.** Their paths are depended on well
beyond packaging. `repo_contract.py` binds `CODEX_MARKETPLACE` and `ROUTER` to
two of them by constant. The root `PROMISE_MACHINE.md` names
`.agents/skills/promise-machine/SKILL.md` inside a closed quotable set in a
Promise contract, and that file is replicated in `plugins/tabularium/`,
`plugins/sapheneia/`, `plugins/ariadne/` and `plugins/horos/`. `AGENTS.md` names
it twice and passes it to a hypomnema command. `plugins/sapheneia/tests/test_sapheneia.py`
reads it. `README.md`, `INSTALL.md` and `.dead-code/baseline.json` reference it.
Relocating those four would be a Promise-contract change across five documents
for no packaging benefit, because they are small. Only `runtime/` is heavy.

**Why the router still works here without `runtime/`.** ADR-040 records that the
authored router "detects a real source checkout by the suite law and complete
plugin topology. Otherwise it loads an installed adapter". The generated runtime
exists to serve installs. In this checkout the router reads the real tree, so
removing `runtime/` does not disable it here. What it does break is an install
made against this repository, which is why this repository must stop advertising
the skill.

**Cross-repository sync prior art.** `.github/workflows/sync-skills-marketplace.yml`
runs in the destination on a cron and pulls from the public source, guarded by
`if: github.repository == '...'`. Its comments record why a full mirror needs a
token with Workflows write: GitHub refuses any push creating or updating a file
under `.github/workflows/` unless the token holds that permission, and
`GITHUB_TOKEN` never can. The payload here contains no workflow file, so a
destination job writing only the package can use `GITHUB_TOKEN`.

**The currency weakness to avoid inheriting.** Issue #836 records that nothing
verifies the marketplace mirror is current. A published payload that silently
stops rebuilding is the same failure. The destination must record the exact
source commit it built from so the question is answerable from the artefact.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 from the target root, so the committed synopses are the current reading
view. The root `audit/AUDIT.md` and `plugins/hexaemeron/audit/AUDIT.md` were
read that way, together with `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.md`,
which is this topic's immediate predecessor and was read as source. Its round 1
finding was a constant-naming collision, fixed; its round 2 was clean. Its
`Leads not pursued` carry the three leads named above. No finding id in any
in-scope record bears on the generator or the destination design.

## 3. Constraints and non-goals

Starting ref `bc38cbae49be7e16dde4e3f54a1e1bc21c5c4fc8`. Toolchain per
`.python-version`.

Non-goals:

- Fixing the sync ordering or the import-closure gap. #854 owns both, and they
  move with the generator rather than being resolved by the move.
- Changing what the payload contains, or the omission boundary ADR-040 fixed.
- Relocating the four authored files, for the reasons in section 2.
- Changing the Promise contract or any `PROMISE_MACHINE.md`.
- Touching the vendored Pashov skills.
- Proving the destination current at any instant. The lag is accepted; the
  recorded source commit makes currency checkable, not constant.

## 4. Design options

The question is where generation runs and what carries the result.

**A. Destination-run hourly job, source cloned public.** The destination holds a
scheduled workflow that clones the public source, runs the source's generator
into the destination working tree, verifies, and commits when bytes changed
using its own `GITHUB_TOKEN`. No secret, no cross-repository push. The
destination's own workflow file is authored here and pushed once by an account
holding `workflow` scope; the job never rewrites it, and can compare it against
the source copy and fail when they drift.

**B. Source-run push on merge.** This repository pushes the generated tree to
the destination on every merge. Needs a fine-grained token stored as a secret,
which the operator would have to create, and gives a shorter lag than the hour
already accepted. Rejected: it buys latency nobody asked for at the cost of a
credential.

**C. Release asset.** The destination publishes tarballs rather than a tree.
The skills CLI's archive path applies its 25 MiB and 1,000-file extract caps,
which the payload sits close to at 21,513,368 bytes and 994 files, and a
`github` source install would stop working. Rejected on both counts.

**D. Submodule from this repository.** Keeps one address but ordinary clones
still fetch the payload, so the per-clone cost this run exists to remove
largely survives. Rejected.

**Chosen: A.** It is the only option that needs no new credential, and it is the
shape already proven in this organisation by `sync-skills-marketplace.yml`. Its
trade is the hour of lag, which the operator accepted when reversing ADR-054,
and a workflow file that a human must push when it changes.

## 5. Risk register seed

The run adds a scheduled job in another repository that commits to itself, and
removes 995 files from this one. That is where the audit loop should look.

```risk-register
publish-unverified | the destination job between generation and commit | a package failing its own verification is never committed, and the job exits non-zero
stale-destination | the published package against its source | the destination records the exact source commit, so currency is answerable from the artefact
workflow-drift | the destination's workflow against the copy authored here | the job compares them and fails when they differ, rather than silently running an old one
token-scope | the destination job's GITHUB_TOKEN | the job writes no path under .github/workflows/, so it never needs a Workflows-scoped token
broken-install-window | the interval where neither address serves a working install | the destination publishes and is proven installable before this repository stops advertising the skill
authored-file-loss | the four authored files under .agents/ | they remain in this repository at their existing paths, and repo_contract.py, the Promise contract and the sapheneia test still resolve
generator-output-escape | the generator's new output directory argument | a caller-supplied path cannot escape its named root or follow a symlink out of it
suite-coverage-loss | the eight guarantees in tests/test_skills_sh_package.py | each still runs, against a tree generated into a temporary directory
```

## 6. Glossary seeds

- **Payload.** The 995 generated files under `.agents/skills/promise-machine/runtime/`.
- **Package.** What the destination publishes: the four authored files, the
  payload, and a grouping file.
- **Destination.** `wildcat-finance/skills-runtime`.
- **Source commit.** The exact `wildcat-finance/skills` commit a published
  package was generated from, recorded in the destination.
- **Lag.** The interval between a source merge and the destination rebuild, up
  to one hour by schedule.

## 7. Sources

- Issue #949; issue #854; issue #836; issue #888
- ADR-054 and ADR-040 under `docs/decisions/`
- [#947](https://github.com/wildcat-finance/skills/pull/947), and
  `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.md`
- `scripts/portable_promise_machine.py`; `tests/test_skills_sh_package.py`
- `.github/workflows/sync-skills-marketplace.yml`; `.github/workflows/repo.yml`
- `repo_contract.py`; `AGENTS.md`; `PROMISE_MACHINE.md`; `skills.sh.json`
- `vercel-labs/skills` at `src/add.ts`, `src/source-parser.ts`,
  `src/download-source.ts`, `src/blob.ts`, `src/git.ts`

## 8. Signals, and the questions behind them

The destination job runs unattended on a schedule, so it owes answers to two
questions asked at three in the morning.

Is the published package current, and if not, which source commit is it stuck
at? Answered by the source commit the destination records in every publish, and
by the job's own run history. Is the job failing silently? A scheduled workflow
that fails is visible in the destination's Actions tab and by email to the
repository watchers; the job exits non-zero rather than committing a package
that failed verification, so a red run means the last good package is still
published. Both are emitted by the step that adds the workflow.

The changes inside this repository emit nothing new. They are a generator
argument, tests, deletions and prose, none of which runs unattended.

## 9. Boundaries, per capability

The destination job is the boundary this run opens. It clones a URL, runs code
from that clone, and commits to its own repository with a token.

The clone is pinned to `https://github.com/wildcat-finance/skills.git` written
literally in the workflow, not taken from an input. The generator it runs comes
from that clone, which is the same trust boundary as the repository itself. The
token is the job's own `GITHUB_TOKEN` with `contents: write` and nothing else,
and the job writes no path under `.github/workflows/`, so it cannot alter what
runs next. The `if: github.repository ==` guard keeps the job from running in a
fork. Verification happens before the commit, so a failed generation publishes
nothing.

Inside this repository, the generator gains an output-directory argument, which
is a path from a caller. It must refuse a path that escapes its named root or
traverses a symlink out of it. That is the one new control the run adds here.

## 10. The budget, or its absence

None, and here is why. Nothing is changed in the name of speed, and no
performance claim is made. The hourly schedule is a distribution policy the
operator set, not a budget this run measures against. Removing 995 files makes
clones smaller, which is the point of the change rather than a target it has to
hit, and the study records the figures without asserting a threshold.

## 11. The fail-closed posture

The root suite is the stop condition here: `python3 -m unittest discover -s tests`
must exit zero from a fresh clone, and the required `invariants` check must be
green before the run integrates. In the destination the stop condition is the
job's own verification, which exits non-zero and publishes nothing rather than
committing a package it could not verify. A failure in either is worked under
Elenchus to its cause; an assertion is never relaxed to pass a step.

## 12. Decisions and their homes

Two decisions are expensive to reverse. The first is the reversal itself: the
payload leaves this tree. The second is the destination's address, because it
goes into a published install command that people copy. Both belong in one
record under `docs/decisions/` that supersedes ADR-054 explicitly, states the
accepted hourly lag, and states that a workflow change in the destination needs
a human push because `GITHUB_TOKEN` cannot write one.

The ADR number is picked before merge and is global, so a concurrent run can
take the same one. It is verified against the base at integration and corrected
there if it collided, which is the surface #888 owns.
