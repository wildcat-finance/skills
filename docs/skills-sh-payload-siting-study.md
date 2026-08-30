# Study: site the generated skills.sh payload

Assuming, unless corrected:

1. The starting ref is `main` at `7e97b5195d5b0e43146b4200f26cd41b89003413`, the
   tip when this run was cut.
2. The exact interpreter in `.python-version`, with stdlib `unittest`. The root
   suite is `python3 -m unittest discover -s tests`.
3. `wildcat-finance/skills` stays public and stays the repository the skills.sh
   listing points at.
4. Creating a new GitHub repository, or a new Actions secret, is the user's
   action rather than this run's. A design that needs either is blocked, not
   merely expensive.
5. The vendored Pashov skills stay untouched, per ADR-040.

## 1. Problem statement

`.agents/skills/promise-machine/` is a generated copy of this repository,
committed into this repository. At the starting ref it is 999 tracked files and
21,789,732 bytes, against a tracked tree of 3,102 files and 121,305,325 bytes:
32.2% of the files and 18.0% of the bytes. Every clone, worktree and cold read
carries the canonical tree and a second near-complete copy of it.

Issue #940 asks one question: should it stay there. The deliverable is a
decision record that answers it, names the options costed against it, and
supersedes or amends ADR-040 explicitly. Issue #940 states that retaining the
payload in-tree is a legitimate outcome provided the record carries the measured
cost and the sync ordering that #854 established.

A working result here is a record, not a relocation. It is proved by the root
suite passing from a fresh clone and by the record naming the measured figures
above and the constraint in section 4 that decides between the options.

## 2. Prior art

**The payload's origin.** PR #677, `codex/skills-sh-promise-machine`, merged
2026-08-27 as `f0e7a394`. It made the router a dependency-closed Agent Skills
install and added the generated runtime, byte manifest and installed Horos
boundary. `scripts/portable_promise_machine.py` has four commits since creation:
`f0e7a394` (creation), `0cedaa12`, `8e729ae0`, `ef110006`. Its pull request body
carries no `Carried forward` section, so it left no recorded unfinished work.

**The governing record.** ADR-040, accepted 2026-08-27, is the decision this run
must answer to. Its Alternatives section examined five constructions: leaving the
router source-relative, fetching contracts after installation, duplicating a
runtime under every canonical skill, copying the entire repository beneath the
router (~84 MB), and linking to files outside the router's directory. Each keeps
the payload inside this repository. Holding it outside was not among them.

Two of its rejections bind this study directly. Fetching contracts after
installation was rejected because it makes selection depend on mutable network
content and removes the offline policy boundary. Linking outside the router's
directory was rejected because copy-mode installers do not preserve that parent
layout. Any design that leaves a thin entrypoint on `main` and sources the
runtime elsewhere is one of those two under another name.

**The known coupling defect.** Issue #854 is open and carries no merged work. It
records two faults, both hit during skills#329: the portable sync writes files a
subsequent Horos scan cannot see unless staging happens between them, so the
committed boundary describes the previous tree and `horos check` agrees with it;
and `portable_promise_machine.py check` does not verify import closure, so a
mirror missing a file its own mirrored sources import still exits 0. The working
order stages between sync and scan, inside an alternation. This study does not
fix either; #854 owns them. It records that the coupling is real and unrepaired.

**Cross-repository sync prior art.** `.github/workflows/sync-skills-marketplace.yml`
mirrors this repository into `wildcat-finance/skills-marketplace` on a five-minute
cron, running in the destination and pulling from the public source. Its comments
record the cost that pattern carries: a full mirror needs a fine-grained token
with Contents and Workflows write, because GitHub refuses any push touching
`.github/workflows/` under `GITHUB_TOKEN`, and one rejected ref fails the whole
push. Issue #836 records the pattern's other weakness: nothing verifies that
mirror is current.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 from the target root, so the committed synopses are the current reading
view. The in-scope sources are the root `audit/AUDIT.md` and its sibling
`audit/AUDIT_SYNOPSIS.md`, read as the verified synopsis. `plugins/hexaemeron/audit/AUDIT.md`
was read the same way. Neither records a finding against the portable payload,
its generator, or `tests/test_skills_sh_package.py`. No finding id, status,
`Covered`, `Not checked`, `Elenchus verdict` or `Leads not pursued` field bears
on this topic, so none is carried forward.

**What binds to the payload today.** `tests/test_skills_sh_package.py` holds
eight tests: the skills.sh grouping, generator currency, manifest-to-source byte
binding, gitignore exclusion, contract reachability, link closure inside the
package, declared omissions, and isolated-copy operation. `scripts/dead_code.py`,
`scripts/promise_machine.py`, `tests/test_router_selection.py` and its driver
also read it. `.github/workflows/repo.yml` runs the whole root suite
unconditionally on every pull request as the required `invariants` check.

## 3. Constraints and non-goals

Starting ref `7e97b5195d5b0e43146b4200f26cd41b89003413` on `main`. Toolchain per
`.python-version`.

Non-goals:

- Fixing the sync/scan ordering or the import-closure gap. #854 owns both.
- Changing what the payload contains, or the omission boundary ADR-040 fixed.
- Touching the vendored Pashov skills.
- Creating a repository, an Actions secret, or a submodule.
- Re-auditing the router's behaviour. This run changes no routing code.

## 4. Design options

The constraint that decides between them is discovery. `skills.sh.json` sits at
the repository root and groups exactly `promise-machine`; the listing and a
ref-less `npx skills add wildcat-finance/skills` both resolve against the
default branch. `wildcat-finance/skills` is in neither `BLOB_ALLOWED_OWNERS`
(`vercel`, `vercel-labs`, `heygen-com`) nor `BLOB_ALLOWED_REPOS`, so the CLI
falls through to a `--depth=1` clone of the default branch and discovers skills
in that tree. Moving `.agents/skills/promise-machine/` off `main` therefore
breaks both the listing and the documented install.

**A. Keep the payload in-tree; record the decision.** Costs 999 files and
21,789,732 bytes in every clone, and keeps the sync coupling #854 describes.
Preserves discovery, dependency closure and the offline boundary exactly as
ADR-040 fixed them. Needs no new repository, secret or install command.

**B. Separate repository, pushed by CI on merge.** Removes the payload from this
tree. Breaks the root `skills.sh.json` grouping and the ref-less install, because
neither can name a skill that is not on the default branch. Needs a repository
and a fine-grained token secret, both blocked per assumption 4. Inherits #836:
nothing would verify the copy is current.

**C. Orphan distribution branch in this repository, generated by CI.** The CLI
accepts `owner/repo#ref` and clones `--branch <ref>`, and the payload carries no
`.github/workflows/` file, so `GITHUB_TOKEN` with `contents: write` could push
it. Needs no new repository or secret. Still breaks the root grouping and the
ref-less install, and changes the documented command to
`wildcat-finance/skills#dist`. Leaving a thin entrypoint on `main` to preserve
discovery reintroduces fetch-after-install, which ADR-040 rejected.

**D. Submodule.** Payload lives elsewhere but ordinary clone flows still fetch
it, so the per-clone saving is largely notional. Copy-mode installers do not
traverse submodules, which is ADR-040's link objection under another name.

**Chosen: A.** It is the only option that meets the problem statement without
reopening a constraint ADR-040 closed, and it is the cheapest to comprehend.
B and C are not merely expensive; they break discovery, which is the property
the payload exists to provide. The record must say that plainly, so the option
is not re-proposed on the size figure alone.

Retaining the payload is not the same as leaving the question unanswered. The
record carries the measured cost, names why relocation fails, and the run adds
the one guard that keeps the cost from growing unobserved.

## 5. Risk register seed

The run edits a decision record, a test module and installation prose. It runs
no network calls, spawns no subprocess beyond the existing generator invocation
the suite already makes, and holds no secret. The concerns below are what the
audit loop should enumerate.

```risk-register
stale-cost-figures | the measured counts written into the record and the guard | the figures match a fresh measurement of the tree at the merge commit
guard-brittleness | the payload size assertion in the root suite | ordinary plugin growth fails the guard loudly with the new figure, and never passes silently
adr-supersession | the relation between the new record and ADR-040 | exactly one record governs the payload's siting, and ADR-040 names its successor
adr-number-collision | the ADR number chosen before merge | the number is unused on the base at integration, or is corrected before the merge lands
install-prose-drift | INSTALL.md and README install instructions | the documented command matches the command the CLI actually accepts for this repository
boundary-currency | .horos/boundary.json after the step's edits | a fresh scan of the merged tree reproduces the committed boundary
```

## 6. Glossary seeds

- **Payload.** The generated tree at `.agents/skills/promise-machine/`.
- **Runtime.** The `runtime/` directory inside the payload; 994 manifested files.
- **Generator.** `scripts/portable_promise_machine.py`, with `sync` and `check`.
- **Manifest.** `runtime/MANIFEST.json`, binding every copied file to its source
  path, size and SHA-256.
- **Discovery.** How the skills.sh listing and `npx skills add` locate a skill:
  by walking the default branch of the named repository.
- **Distribution ref.** A branch carrying built output rather than source; the
  mechanism option C would need.

## 7. Sources

- `docs/decisions/ADR-040-package-one-dependency-closed-portable-router.md`
- Issue #940; issue #854; issue #836
- PR #677, merge commit `f0e7a394`
- `.github/workflows/repo.yml`, `.github/workflows/sync-skills-marketplace.yml`
- `tests/test_skills_sh_package.py`; `scripts/portable_promise_machine.py`
- `skills.sh.json`; `.agents/skills/promise-machine/runtime/MANIFEST.json`
- `vercel-labs/skills` at `src/add.ts`, `src/source-parser.ts`,
  `src/download-source.ts`, `src/blob.ts`, `src/git.ts`

## 8. Signals, and the questions behind them

None, and here is why. This run adds a decision record, a unit test and prose.
Nothing it produces runs unattended: the guard executes only inside the root
suite, which reports through the existing `invariants` check, and a failure there
is already surfaced by CI with the assertion text. There is no service, no
scheduled job and no on-call question this run creates.

## 9. Boundaries, per capability

The run opens no new boundary. It accepts no untrusted input, adds no
dependency, fetches no URL, reads no credential and spawns no new subprocess.
The one subprocess in scope is the existing `portable_promise_machine.py check`
invocation inside `tests/test_skills_sh_package.py`, which runs a fixed local
checker with a pinned argv and no shell; the run does not change it. The guard
added in step 1 reads tracked file metadata only.

## 10. The budget, or its absence

None, and here is why. The run changes no code on any measured path. The guard
walks the payload's tracked files once inside a suite that already walks them
for the manifest test, so it adds no measurable time to a one-to-two minute job.
No speed-motivated change is made, so Metron's before-and-after rule has nothing
to record.

## 11. The fail-closed posture

The root suite is the stop condition: `python3 -m unittest discover -s tests`
must exit zero from a fresh clone before the step is pushed, and the required
`invariants` check must be green before the run integrates. A failure is worked
under Elenchus to its cause rather than by relaxing the assertion. The guard
itself is written fail-closed: it asserts the measured figures and fails with
both the expected and actual values, so a payload that grows is refused with the
number needed to update the record rather than passing quietly.

## 12. Decisions and their homes

One decision is expensive to reverse: whether the generated payload stays in
this tree. Its home is a new record under `docs/decisions/`, superseding nothing
but extending ADR-040 with the option ADR-040 never considered and the discovery
constraint that rules it out. ADR-040 stays accepted; the new record is what a
later reader finds when they ask the size question again.

The ADR number is picked before merge and is global, so a concurrent run can
take the same one. The number is verified against the base at integration and
corrected there if it collided.
