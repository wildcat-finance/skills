# Tell an unfetched merge commit from a broken attribution at integrate

Assuming, unless corrected:

1. Python 3 as pinned in `.python-version`, standard library only, `unittest`
   as the runner. No dependency is added.
2. The run starts at `840d8dd3`, the tip of `origin/main` when the run branch
   was cut.
3. This changes Fiat's behaviour, so it owes exactly one generation row at
   `fiat-v5.43.1`: the frontier revision `state-shape-validation` and its digest
   `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` are
   retained, and the held Next Fiat job, skills#363, is left untouched. This run
   is not that job.
4. The controller driving the run is `fiat-v5.41.1` while the repository carries
   `fiat-v5.42.1`, recorded in the `controller_version` receipt. The run does not
   use `amend study`, which is the one thing v5.42.1 changed.
5. An edit to `hexctl.py` cascades into the repository's digest bindings, and
   refreshing them is part of the work rather than an afterthought.

I will proceed on these unless corrected.

## 1. Problem statement

`done integrate` is the terminal receipt of a Fiat run. It is reached after
every gate has passed and after the merge has already landed on the base. At
that moment it can refuse with:

```
hexctl: error: merged attribution ancestry for <commit> could not be determined
```

when the only thing wrong is that the local clone has not fetched the merge
commit yet. The commit it names is an ordinary signed product commit that is an
ancestor of both the merge and `origin/main`. Nothing about the attribution has
failed.

The mechanism is exact. `merged_attribution` walks each recorded identity
through `commit_is_ancestor(base_dir, identity["commit"], merge_sha, ...)`, and
that helper runs `git merge-base --is-ancestor <candidate> <descendant>`. Git
answers 0 for yes and 1 for no, and returns 128 when an object named on the
command line is not in the repository. `commit_is_ancestor` is right to refuse
to read 128 as "no", and its docstring says why: "Reading an unexpected status
as no would turn a broken call into a finding about a person." Having refused,
it then reports the refusal as a fact about the candidate rather than about the
descendant that was missing.

So the guarantee the message appears to report on, that every recorded identity
stays reachable from the base, is the one thing a reader takes seriously at that
moment, and it is the one thing that has not actually been tested.

A working prototype means both of these:

- A clone that has not fetched the merge gets a refusal naming the absent
  object and the fetch that resolves it, and never names an innocent commit.
- A genuine attribution break still refuses, and its message is distinguishable
  from the first.

The demo path constructs both conditions over a temporary repository and shows
the two messages differ:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl_attribution_fetch -v
```

## 2. Prior art

**The controller already holds the discipline this run completes.**
`commit_is_ancestor` refuses to treat an unexpected exit status as an answer,
and explains the reasoning in its own docstring. The gap is not that the
controller trusts a broken call; it is that the diagnosis stops one step short
of naming what broke. The same distinction is drawn correctly elsewhere: a
GitHub read that never arrived "says so in its own words", per the entry skill.

**The issue's own observation.** The skills#556 integration merged as
`23d6bfdf` and the first `done integrate` refused over `77458260`, a commit that
was an ancestor of both the merge and `origin/main`. A `git fetch origin main`
and an identical retry succeeded.

**A second, independent reproduction, taken during this sequence of runs.**
The skills#854 integration merged as
`646dbff7c12202e8b9417ac51546d72b27dde5e3` on 2026-08-30. `done integrate`
refused with `merged attribution ancestry for
05c4477cf672e6ba108df45bf3666877c180a688 could not be determined`. That commit
is step 1's own product commit, authored by Shoggoth and GitHub-verified. A
`git fetch origin main` made the merge object local, `merge-base --is-ancestor`
began answering, and the identical retry receipted the run. Twelve identities
were recorded, and the walk died on the first. Two independent occurrences, two
different runs, same cause.

**The exit codes are measured, not assumed.** Against a constructed repository:
`merge-base --is-ancestor` returns 0 for a real ancestor, 1 for a real
non-ancestor, and 128 when the descendant names an object the repository does
not have. `rev-parse --verify <sha>^{commit}` returns 128 on the same absent
object, which is what makes a pre-resolution check able to tell the two apart.

**Audit records.** The synopsis view is current: `audit_synopsis.py --check .`
exits 0 from the repository root, so the committed synopses are the normal
reading view and were read as such. No finding in Fiat's own records bears on
this diagnostic; the attribution check itself arrived with skills#622 and its
records carry no open item about the absent-object case.

**The last two merged pull requests on `hexctl.py`.**
[PR#943](https://github.com/wildcat-finance/skills/pull/943) moved the Protasis
study-amendment shape check into the controller and is the `fiat-v5.42.1` row.
[PR#968](https://github.com/wildcat-finance/skills/pull/968) allowed honest
step-branch extensions after push receipts and is the `fiat-v5.41.1` row. Both
carry a `## Carried forward` section and neither names anything about
attribution or absent objects, so nothing is inherited here.

**No prior art for the remedy.** The controller's diagnostics never name a
`git fetch` today, checked by grepping the whole script. This run introduces
that, which is why item 12 gives it a record.

## 3. Constraints and non-goals

**Starting ref.** `840d8dd3`, the tip of `origin/main` when the run branch
`fiat/898-tell-an-unfetched-merge-commit-from-a-broken` was cut.

**Toolchain.** Python 3 as pinned, standard library only,
`python3 scripts/run_checks.py` as the entrypoint, and the root Elenchus runner
`tests/run_tests.py`.

**Version.** One generation row at `fiat-v5.43.1`. The frontier revision, its
digest and the held Next Fiat job are retained byte for byte.

**Non-goals.**

- Fetching on the run's behalf. A terminal receipt that silently mutates the
  clone's refs is a worse failure than a confusing message, and it cannot work
  in a handoff or offline context where the remedy has to be a human's.
- Rewriting every diagnostic in the controller that could name a remedy. This
  run fixes the one the issue names and leaves the pattern for others to follow.
- The delegation-identity work in skills#363, which is Fiat's held next job and
  is not this.
- Changing what attribution means or which mechanisms count. The check's
  semantics stay exactly as they are; only its ability to say what went wrong
  changes.

## 4. Design options

*Option A: resolve the merge commit once, before the walk.* At the top of
`merged_attribution`, resolve `merge_sha` as a commit object. If it does not
resolve, refuse with a message naming the absent object and the fetch. The
per-identity walk then only ever sees a descendant that is present, so a 128
from it is a genuine anomaly and keeps its existing wording. Trade: one extra
bounded git call per integrate, and it says nothing about a missing *candidate*.

*Option B: teach `commit_is_ancestor` to separate 128 from other statuses.*
More general, because both call sites benefit and a missing candidate is caught
too. Trade: the helper cannot tell which of its two arguments was missing
without another read, so its message either stays vague or costs the read
anyway; and it changes a helper the whole controller depends on rather than the
one function that has the context.

*Option C: fetch and retry on 128.* Rejected. See non-goals: a controller that
mutates refs inside a terminal receipt is worse than one that explains itself,
and the fix would not survive an offline handoff.

**Chosen: A, with one addition from B.** A puts the check where the context
lives: `merged_attribution` knows that `merge_sha` came from the operator's
`--merge-commit` argument and is the object most likely to be missing, because
it is the only one the local clone never created. The addition is that
`commit_is_ancestor`'s existing refusal names both commits rather than only the
candidate, so if the unexpected status ever fires again the reader can see which
pair the question was about. That is a one-line change to a message and does not
alter what the helper decides.

The cheapest thing that answers the problem statement is A alone. The addition
is included because leaving the helper naming one of two arguments is what
produced this issue in the first place, and the same reader will hit it next.

## 5. Risk register seed

The audit loop should look hardest at whether the new refusal can be made to
fire on a healthy run, because a terminal gate that refuses a correct
integration is worse than the message it replaces. It should also check that
the pre-resolution read cannot itself become the thing that breaks: it runs at
the end of a run, after the merge, when there is no path left to retry from.

```risk-register
false-refusal-on-healthy-run | the new pre-resolution check at the top of merged_attribution | a run whose merge commit is present resolves and proceeds, proved against a fixture where every identity is a real ancestor
absent-object-message | the refusal text a missing merge produces | it names the absent object and the fetch, and never names a recorded identity, so the reader is not sent to inspect an innocent commit
genuine-break-still-refuses | a squash or rebase merge that drops an identity | the existing refusal still fires and its message is distinguishable from the absent-object one
unbounded-read | the git call the pre-resolution check adds | it goes through the existing bounded git wrapper with a fixed argv and no shell, like every other read in the function
argument-ambiguity | commit_is_ancestor's unexpected-status refusal | the message names both the candidate and the descendant, so a future unexpected status says which pair it could not answer for
terminal-phase-safety | the moment the check runs, after the base merge has landed | a refusal leaves the run resumable by fetching and retrying, and changes no state or ledger byte on the way out
digest-cascade | the repository bindings that pin hexctl and its tests | every binding the edit invalidates is refreshed in the same change and the suites that read them pass
```

## 6. Glossary seeds

- **Candidate.** The recorded product commit whose reachability is being asked
  about.
- **Descendant.** The commit the candidate must be reachable from, here the
  integration merge.
- **Absent object.** A commit named on a git command line that the local
  repository does not hold, which makes git exit 128 rather than answer.
- **Attribution.** Fiat's check that every primary author its push receipts
  recorded remains reachable from the base after the merge.
- **Carrier.** The commit that carries an identity when ancestry alone does not,
  either as author or through a co-author trailer.

## 7. Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `commit_is_ancestor` at
  9940 and `merged_attribution` at 10500, at `840d8dd3`.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, the current frontier block and
  the `fiat-v5.41.1` and `fiat-v5.42.1` rows.
- `plugins/hexaemeron/skills/VERSIONING.md`, the generation axis rules.
- Issue [#898](https://github.com/wildcat-finance/skills/issues/898).
- Pull requests [#943](https://github.com/wildcat-finance/skills/pull/943) and
  [#968](https://github.com/wildcat-finance/skills/pull/968).
- The skills#854 integration of 2026-08-30, merge
  `646dbff7c12202e8b9417ac51546d72b27dde5e3`, for the second reproduction.

## 8. Signals, and the questions behind them

`hexctl` is a command a person runs and reads the exit code of, so the on-call
questions are about a refusal rather than a running system. Ephoros owns what a
signal must carry. Two questions matter here, and this run exists because the
first one currently has no answer.

- *What is actually missing, and what do I run?* The absent-object refusal names
  the object and the fetch. Step 2 emits this.
- *Did attribution really fail, or did the check fail?* The two refusals are
  worded so a reader can tell them apart without reading the source. Step 2
  emits both and step 3's tests hold them distinct.

## 9. Boundaries, per capability

Phylax owns the boundary list and the controls.

- **One added git read, opened by step 2.** It resolves an operator-supplied
  SHA that has already passed `require_full_sha`. The controls are the existing
  bounded git wrapper, a fixed argv, no shell, and the same base directory every
  other read in the function uses.
- **No other boundary is opened.** No network, no subprocess beyond that read,
  no credential, no filesystem write, no state or ledger mutation on the
  refusing path.
- **A boundary deliberately not opened.** The run does not fetch. That is
  stated here as a boundary rather than only as a non-goal, because fetching is
  the obvious convenience and the reason to refuse it is a control decision.

## 10. The budget, or its absence

None, and here is why. The change adds one bounded git call to a command that
already makes many, at the end of a run rather than in a loop, and it is not
made in the name of speed. Metron's refusal does not bite because no
performance claim is made and none is needed.

## 11. The fail-closed posture

Elenchus owns the triage order and the guard rule.

What stops the run: any failure of `python3 scripts/run_checks.py`, a non-zero
`portable_promise_machine.py check`, a non-zero `horos.py check .`, a stale
audit synopsis, or a `git diff --check` failure.

The guard convention: each fix arrives with a test that fails against the tree
before it and passes after. For this change that means two cases that cannot
both pass on the current controller, one asserting the absent-object refusal
names the object and the fetch, and one asserting a genuine attribution break
still refuses with different words.

What this run does not make safe, stated so nobody reads more into the fix than
is there: it does not make an unfetched clone able to complete an integration.
It makes the refusal say so. The remedy is still a human running `git fetch`.

## 12. Decisions and their homes

Hypomnema owns which decisions earn a record and where each one lives.

- **That a controller diagnostic may name a remedy.** No diagnostic in
  `hexctl.py` names a command to run today. Establishing that it may is a
  precedent every later diagnostic will be read against, and it is expensive to
  reverse once messages start carrying remedies. It earns a decision record
  under `docs/decisions/`, numbered immediately before merge.
- **That the controller refuses rather than fetches.** The same record carries
  it, because it is the same question about how much a terminal receipt is
  allowed to do on the operator's behalf.
- **Everything else stays in the code.** Which exit status means what, and why
  the pre-resolution read sits where it does, are explained by a comment at the
  site that needs them.

## Boundaries the study states

**Always.** The declared check entrypoint before a commit. The imprimatur lint
on every shipped document. A test that fails without the fix beside every fix.
The digest bindings refreshed in the same change that invalidates them.

**Ask first.** Adding a dependency. Making the controller fetch, or otherwise
mutate refs, on the operator's behalf. Changing what attribution means. Touching
CI. Changing the held Next Fiat job.

**Never.** Commit key material. Delete or weaken a failing test to make a suite
pass. Claim a command ran when it did not. Raise a numeric ceiling to get past a
gate. Edit ledger history to make a receipt fit.
