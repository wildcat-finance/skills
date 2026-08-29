# Study: give the Kronos scoreboard and parked lane a durable home across ephemeral runners

Assuming, unless corrected:

1. Python 3.11 or later and stdlib `unittest`, matching the rest of this
   plugin. Git is already required for Fiat. No new dependency.
2. This is generation-axis work. Kronos stays mature. The held frontier
   revision `terminal-goal-loop` and digest
   `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` are
   retained byte for byte. The run does not pass `--frontier`.
3. `record`, `park`, `unpark`, `show` and `parked` stay filesystem-only. They
   start no subprocess and open no socket. Sync verbs are a separate surface.
4. A dedicated git ref that holds only Kronos working state is not a target
   skill. Kronos's first hard rule still forbids editing, implementing,
   auditing or rewriting a ranked skill; Fiat still owns that work.
5. One Kronos loop writes the remote ref at a time. A non-fast-forward push
   refuses rather than rewriting history.
6. The run starts from `2b6848b95e9d90f4bc9995b8cd89106d1807e9a9` on `main`
   (`origin` is the contributor fork, `upstream` is
   `wildcat-finance/skills`). The Solidity suite is waived: this run will not
   produce Solidity.

## 1. Problem statement

Kronos already records each ranking pass in `.kronos/scoreboard.jsonl` and
each park in `.kronos/parked.jsonl`. Both files are gitignored on purpose.
v0.3.0 recorded the cost: "the record lives on the machine that ran the
loop." That was true when the machine lasted. The collective now runs in
remote sessions whose containers are recycled between runs. Every fresh
runner therefore starts with an empty scoreboard and an empty parked lane.

A park is released by a person, never by infrastructure. Today the recycler
releases it. The drift check over axis scores is inert because there is no
history to read back. With dozens of open jobs across many ledgers, those two
files are the only memory the loop has between passes.

What is built: a durable home for the existing JSONL files that is not "commit
the gitignored file in the working tree as part of the pass." Local
`record` / `park` / `unpark` behaviour is unchanged. A park recorded on one
runner still stands on a fresh runner until a person runs `unpark`. `show`
reads scoreboard history that survived the previous runner.

A working prototype means all of this holds, measured by command:

- `python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py pull --root
  <scope>` copies `scoreboard.jsonl` and `parked.jsonl` from the named git
  ref into `<scope>/.kronos/` without dirtying `git status --short`.
- After `park` on runner A and `push`, a second tree that has never seen
  `.kronos/` runs `pull` then `parked` and exits 3 with the same held-job
  hash and the same reason bytes.
- `show` on that second tree prints the earlier pass, including drift against
  a later pass whose held-job hash did not change.
- A missing remote ref is an empty start, not a block. A failed pull when the
  ref exists refuses rather than pretending there are no parks.
- A symlink at `.kronos/` or at either JSONL path still refuses (K010), as
  [skills#244](https://github.com/wildcat-finance/skills/pull/244) already
  requires.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes, carrying the new
  cases.
- The demo path: a local bare remote, two temporary checkouts, park and
  record on the first, pull on the second, `parked` exits 3 and `show` prints
  the pass.

## 2. Prior art

**In this skill.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py`
already implements `record`, `show`, `park`, `unpark` and `parked`. The
trust boundary is stdin and the argument list. The module docstring states
that nothing here starts a subprocess or opens a socket. `append_line`
creates `.kronos/.gitignore` containing `*` so git never sees the files.
`checked_path` refuses a symlink at the file or its directory (audit finding
S2-R1-01 on the scoreboard run). Standing parks replay `park` / `unpark`
events in order. Staleness is the held-job identity hash from
`VERSIONING.md`, never memory.

**Last two merged pull requests that changed this target.**
[skills#254](https://github.com/wildcat-finance/skills/pull/254) (rank-only
mode, `kronos-v0.5.0`) and
[skills#250](https://github.com/wildcat-finance/skills/pull/250) (parked
lane, `kronos-v0.4.0`). Neither carried a durable home across machines.
#254 accepted that an ungoverned list is not deduplicated. #250 accepted
that a halt reason may carry terminal control characters, because stripping
them would make the printed reason differ from the recorded one. Both stay
open as stated non-goals here.

**Carried forward from those runs' bodies.** The 16 MiB scoreboard read cap
remains a stop rather than a truncated append. Phase-only mode inherits
scoreboard read-back from steps 3-7 rather than restating it. Neither run
named ephemeral runners.

**Audit records.** `audit/AUDIT.md` sections "record each Kronos ranking
pass in a durable scoreboard", "park a blocked Kronos job instead of
stalling the loop", and "add a rank-only reporting mode to Kronos". The
finding that still constrains this design is S2-R1-01: a symlinked `.kronos/`
was written through, putting the `*` gitignore and the scoreboard in a
directory the caller never named. Where the link pointed somewhere git
watches, that was the dirty-tree failure option C was rejected for. A
volume that is a symlink is therefore not a home.

**Fiat dirty-tree and worktrees.** Fiat still refuses a dirty target tree at
`init`. Gitignored files do not appear in `git status --short`. A *tracked*
scoreboard that Kronos appends would stop the next Fiat iteration. Fiat now
also isolates each run in `tmp/fiat/<flattened run branch>`
([skills#439](https://github.com/wildcat-finance/skills/issues/439)); that
does not keep `.kronos/` alive across recycled containers.

**Kronos-1's rejected option C.**
`docs/kronos-ranking-scoreboard/study.md` rejected committing the
scoreboard into the working tree: an uncommitted tracked file dirties the
tree, and having Kronos commit, branch or push *that tree* would break the
first hard rule. Issue #462 quotes that reasoning and says it stands. The
home cannot be "commit the gitignored file as part of the pass."

**Outside.** JSON Lines stay the record format. Git refs as a small
side store are ordinary (GitHub pages sources, `gh-pages`, notes). This
run uses a dedicated branch, not git notes, because notes are harder to
test and to inspect.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `2b6848b95e9d90f4bc9995b8cd89106d1807e9a9` on `main`.
- Python 3.11 or later, stdlib only. Git is invoked with a fixed argv list
  and no shell.
- Ranking, the four axes and caps, the tie-break, park semantics, held-job
  hash staleness and Fiat ownership of target-skill work are unchanged.
- Kronos stays mature. Generation moves; evolution, epoch, frontier
  revision and digest do not.
- `tests/test_version_propagation.py` requires `SKILL.md` frontmatter and
  the ledger's current version to agree, so the bump and the row land
  together.
- Existing K000-K017 codes keep their meaning. New refusals take the next
  free codes.
- The Solidity suite stays waived.

**Non-goals.**

- No scoring, no change to axes, caps, tie-break or park replay.
- No committing `.kronos/` into `main` or into a Fiat run branch.
- No symlink or bind-mount as the durability mechanism.
- No GitHub Issues, gists, Actions caches or object stores.
- No automatic merge of concurrent writers. Non-fast-forward push refuses.
- No rewrite of history on `kronos/state`.
- No Shoggoth provenance trailers on state-ref commits; they are operator
  git commits of Kronos working state, not Fiat-governed product commits.
- No raising of the 16 MiB cap. No stripping of control characters from
  park reasons. No ungoverned-list deduplication.

## 4. Design options

**A. File export and import only.** `export` writes the two JSONL files to a
caller path; `import` copies them back. Cheapest. Trades away the acceptance
condition: a park recorded on one runner still stands on a fresh runner
*without a person carrying the files*. A forgotten import looks exactly like
an empty lane, which is the defect.

**B. Operator-supplied real directory (`KRONOS_STATE_DIR`).** Point
`.kronos` at a volume that outlives the container. Trades away the
environment this issue names: recycled cloud runners do not mount such a
volume unless the harness is changed, and a symlink there is already
refused (S2-R1-01). A real directory still dies with the VM disk.

**C. Tracked files under `docs/kronos/` or similar, committed by Fiat.**
Shared history. Trades away the loop: Kronos would dirty a tracked file
before Fiat `init`, or would have to commit, which v0.3.0 forbade for the
target tree. Also makes ranking require a product pull request.

**D. Dedicated git ref, throwaway clone, `pull` / `push` verbs.** Default
ref `refs/heads/kronos/state`. Default remote: `KRONOS_STATE_REMOTE` if
set, else `upstream` if that remote exists, else `origin`. `pull` fetches
into a temporary clone under the system temp directory, copies the two
JSONL files into `<scope>/.kronos/` through a real directory (K010 still
applies), and treats a missing ref as empty. `push` copies the local files
into a throwaway clone, commits, and fast-forwards the ref. `record` /
`park` / `unpark` stay subprocess-free. Trades away: network and git
credentials on the sync verbs; a contributor without push access to the
canonical remote can still pull and can still rank, but their parks stay
local until someone who can push does so.

**Chosen: D.** It is the cheapest construction that meets "a park recorded
on one runner still stands on a fresh runner, and only a person releases
it" without committing into the working tree Fiat inspects. A is not a
durable home unless a person remembers. B is not available on the runners
the issue describes. C is the option v0.3.0 already rejected. D's cost is
a new subprocess surface, named in item 9 rather than hidden.

The generation row and, because the store location is expensive to reverse,
one decision record under `docs/decisions/` both land in the close step.

## 5. Risk register seed

```risk-register
symlink-escape | a `.kronos` path or JSONL file that is a symlink | K010 still refuses before any copy or append; pull never writes through a link
dirty-tree | files the next Fiat `init` would see | `.kronos/.gitignore` still holds `*`; the state ref is not the run branch; `git status --short` in the scope stays empty after pull, record, park and push
partial-write | a killed pull or push leaving half a JSONL file | pull writes to a sibling temporary then replaces; a missing final newline still refuses (K008) before the next append
subprocess-git | `git` argv, remote URL and credentials | fixed argv, no shell; remote is an existing git remote name or `KRONOS_STATE_REMOTE`; no credential flags; stderr from git is not copied into Kronos diagnostics
empty-as-cleared | a failed pull presented as no parks | missing ref is empty; an existing ref that cannot be read refuses with a new code; `parked` and `record` do not treat that refusal as an empty lane
concurrent-push | two runners pushing the same ref | non-fast-forward refuses; local files stay; ranking verbs already succeeded
remote-url-fetch | a caller-supplied fetch URL | refuse a URL that is not a configured remote name unless it is the env default already resolved from `git remote`
state-commit-identity | author on the state ref | uses the operator git identity already configured; no extra trailers
```

## 6. Glossary seeds

- **Working copy.** `<scope>/.kronos/scoreboard.jsonl` and `parked.jsonl`,
  gitignored, same format as today.
- **State ref.** `refs/heads/kronos/state` on the chosen remote, containing
  only those two files at the tree root.
- **Pull.** Replace the working copy from the state ref, or start empty if
  the ref does not exist.
- **Push.** Fast-forward the state ref from the working copy.
- **Throwaway clone.** A temporary git directory under the system temp
  path, never inside the Fiat worktree or the scope working tree.

## 7. Sources

- Issue [skills#462](https://github.com/wildcat-finance/skills/issues/462).
- `plugins/hexaemeron/skills/kronos/SKILL.md`, hard rules and parked-lane
  steps.
- `plugins/hexaemeron/skills/kronos/EVOLUTION.md`, `kronos-v0.5.0`, mature,
  digest `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1`.
- `plugins/hexaemeron/skills/kronos/scripts/kronos.py`.
- `plugins/hexaemeron/tests/test_kronos_scoreboard.py`.
- `docs/kronos-ranking-scoreboard/study.md`, option C and the dirty-tree
  interaction.
- `docs/kronos-parked-lane/study.md`, park replay and the person-only
  unpark rule.
- `audit/AUDIT.md`, Kronos scoreboard S2-R1-01 (symlink), parked-lane
  S2-R1-01 (reason newline), rank-only S2-R1-01 (ungoverned overlap).
- [skills#254](https://github.com/wildcat-finance/skills/pull/254) and
  [skills#250](https://github.com/wildcat-finance/skills/pull/250).
- `plugins/hexaemeron/skills/VERSIONING.md`, generation on a mature skill.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, dirty-tree stop and run
  worktrees.
- [phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md)
- [ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md)
- [metron](../../plugins/hexaemeron/skills/metron/SKILL.md)
- [elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md)
- [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md)

## 8. Signals, and the questions behind them

The loop already asks `parked` at the end of a pass. Durability adds two
questions once a runner is gone:

- *Did this runner see the parks the last runner recorded?* Answered by
  `pull` printing the ref tip and whether the working copy was empty or
  replaced, then by `parked` exiting 3 or 0. Emitted at the start of every
  pass.
- *Did this runner's park or pass reach the ref another runner will read?*
  Answered by `push` printing the new tip, or a refusal naming
  non-fast-forward or missing credentials. Emitted after `record`, `park`
  and `unpark`. Ranking still completes if push refuses; the local files
  remain.

No metric, no alert. [ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry. Stdout stays the operator surface those two
questions read; git stderr does not become Kronos diagnostic text.

## 9. Boundaries, per capability

- **Reading the state ref.** Worth taking: a missing ref, a hostile remote,
  a tree that is not the two JSONL files. Control: missing ref is empty;
  any other fetch failure refuses; only `scoreboard.jsonl` and
  `parked.jsonl` are copied; extra blobs in the ref are ignored.
- **Writing the working copy.** Worth taking: symlink, partial file, path
  escape. Control: existing K010 and K008; copy via a sibling temporary
  in a real directory under the named root.
- **Invoking git.** Worth taking: shell injection, credential leakage,
  caller-supplied URL. Control: argv list, no shell, remote name from git
  config or one env var, no `--token` / `GIT_ASKPASS` plumbing in this
  script; timeouts and output caps on the child.
- **Pushing.** Worth taking: overwritten parks from a concurrent writer.
  Control: fast-forward only; refuse otherwise and keep local files.

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary
list and the controls.

## 10. The budget, or its absence

None. A Kronos pass is bounded by a Fiat delivery that takes hours. Pull and
push move two small JSONL files. No performance claim is made, so
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) has nothing to
measure.

## 11. The fail-closed posture

Ranking verbs keep today's rule: a refusal exits non-zero and appends
nothing. Sync verbs:

- Missing state ref: pull succeeds with empty working copy.
- Existing ref, fetch or copy failure: pull exits 1 with a new code.
  `record` and `parked` are not then pointed at a silently empty lane by
  the skill text; the loop stops and names the pull refusal.
- Push non-fast-forward or no credentials: push exits 1; local files stay;
  the pass already recorded locally is not rolled back.
- Symlink, malformed JSONL tail, path outside root: existing K010 / K008 /
  K007.

Guard-test convention: each new refusal has a case in
`plugins/hexaemeron/tests/test_kronos_scoreboard.py` that fails on the
unfixed tree, following
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md). Tests use a
local bare repository as the remote, not the network.

## 12. Decisions and their homes

Two decisions here are expensive to reverse.

- Durability is a dedicated git ref plus throwaway clone, not a committed
  working-tree file and not a person-carried export. That is a store
  location other skills and harnesses will grow against. It belongs in
  `docs/decisions/` as the next numbered record, per
  [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md).
- Kronos stays mature; this is a generation row. That belongs in
  `plugins/hexaemeron/skills/kronos/EVOLUTION.md`, same as kronos-1 through
  kronos-3.

The study is a run artefact. The close step writes those two records rather
than treating this file as their home.

## Boundaries

**Always.** Both suites before a commit: `python3 -m unittest discover -s
tests` and `python3 plugins/hexaemeron/tests/run_tests.py`. The imprimatur
lint on every shipped document. Kronos's held frontier revision and digest
retained byte for byte in any ledger edit. `git status --short` in the
scope empty after pull, record, park and push.

**Ask first.** Adding a dependency. Changing the four axes or their caps.
Writing anywhere git can see on `main`. Touching CI. A remote URL that is
not a configured git remote.

**Never.** Commit `.kronos/` into a Fiat run branch or into `main`. Follow a
symlink at the working copy. Rewrite `kronos/state`. Unpark without a
person. Change the held `Next Fiat job` or reopen the mature frontier.
Edit a vendored skill. Delete a failing test to make a suite pass. Claim a
lint or a suite ran when it did not.
