# Study: grade router selection, not just router resolution

Topic: [skills#499](https://github.com/wildcat-finance/skills/issues/499),
`framework-9 -- grade router selection, not just router resolution`, labelled
`origin:ai` and `observation`, milestone "Wave 2 -- orientation, routing and
contributor intent".

Starting ref: `2477db1352a4099445867216f6fd9a2e84963f3a` on
`wildcat-finance/skills`, the merge of
[PR #677](https://github.com/wildcat-finance/skills/pull/677).

The issue's review block of 26 August 2026 says to keep it as a framework
observation and states that "No current sibling clearly owns the whole gap",
so this study reassigns the work against the current router, ledgers and
repository contracts. Every measurement, path and line number in the original
filing was treated as unverified and reproduced here or marked as unverified.

## Assumptions

Assuming, unless corrected, and proceeding on these:

1. The interpreter contract is single and exact. At this ref `.python-version`
   holds `3.13.15` and `pyproject.toml` holds `requires-python = "==3.13.*"`,
   so CPython 3.13.15 is the only image this repository's suites run on. The
   two-interpreter convention the delivery packet carried, 3.12.13 beside
   `/usr/bin/python3` at 3.9.6, is stale here and is not a second target to
   keep green. The 3.9.6 interpreter cannot import `tomllib`, and
   `tests/test_python_contract.py` refuses every image but the pin. Every
   command in this study names the pin and nothing else; item 3 says how to
   obtain it.
2. The pin is installed on this machine and every suite below was run on it.
   One residual caveat, stated rather than assumed: the local image is uv's
   `cpython-3.13.15-macos-aarch64-none` distribution, and CI resolves the same
   pin through `actions/setup-python` with
   `python-version-file: ".python-version"`. The two agree on version and not
   necessarily on build.
3. The corpus is data and the checker is code. No part of the delivered
   artefact calls a model, reaches the network or shells out.
4. A recorded score is evidence about one model, one prompt template, one
   corpus digest and one date. It is never the suite's pass condition.
5. The run publishes under the human contributor's own Git and GitHub identity.
   Every commit carries exactly one `Co-authored-by: Shoggoth
   <shoggoth@wildcat.finance>` trailer and one `Wildcat-Origin: shoggoth`
   trailer and no runtime-host byline.
6. The security suite is waived for this run because it produces no Solidity.
   The `.sol` files in the tree are vendored fizz templates and test fixtures
   this run does not touch. Non-Solidity audit rounds run the Phylax, Ephoros
   and Hypomnema lints and review the risk register.

## 1. Problem statement

**What is being built.** A graded corpus of request phrasings paired with the
canonical skill each one should select, a deterministic checker that holds the
corpus to the router and boundary prose it claims to grade, and a root Promise
Machine promise that says exactly what a passing check establishes.

**For whom.** Two readers. An agent that reaches this repository through
`.agents/skills/promise-machine/SKILL.md` and has to choose one of 24 rows. A
maintainer who changes a sibling boundary sentence in `AGENTS.md` and wants the
suite, rather than a later reader, to notice that the corpus no longer matches.

**What a working prototype means here.** The repository can answer three
questions it cannot answer at `2477db13`: which requests the router is expected
to route where, whether the prose those expectations rest on still says what
the corpus quotes, and what one recorded grading run found. It does not mean
the router routes correctly. Nothing in this delivery can establish that.

**The demo path.** From the repository root:

```bash
python3.13 -m unittest discover -s tests
python3.13 tests/emit_router_selection_report.py
```

The second command prints the corpus's coverage table -- every router row, the
canonical selection it names, the number of cases that expect it, and the
contested pairs each hard case probes -- followed by the latest recorded run
block or the word `not-run`. The first command is the gate. The second is the
demonstration.

## 2. Prior art

### The state of the gap at `2477db13`, reproduced

`.agents/skills/promise-machine/SKILL.md` is 82 lines. Its two tables carry 24
rows: 13 first-party plugin rows at lines 36 to 48 and 11 Hexaemeron rows at
lines 55 to 65. Twenty-three rows name a canonical skill by name; the last
names "The named upstream Pashov skill". `AGENTS.md` line 5 names this file as
"the single portable router". The file carries no `## Promise Machine
contract` section; `grep -n "Promise Machine contract"` over it exits 1.

`tests/test_portable_skills.py` is 85 lines and holds five test methods:

- `test_plugin_manifests_name_the_public_repository` (line 19) reads
  `.claude-plugin/marketplace.json` and both host manifests per plugin.
- `test_promise_machine_is_the_only_portable_entrypoint` (line 37) asserts the
  router is the sole `*/SKILL.md` under `.agents/skills`, that its frontmatter
  name is `promise-machine`, that its description is non-empty, and that it
  declares no version.
- `test_router_reaches_each_plugin_runtime_contract_once` (line 45) resolves
  every Markdown link in the router and requires the set to equal the root
  `AGENTS.md` plus one `AGENTS.md` per plugin directory, each once.
- `test_plugin_runtime_contracts_resolve_every_canonical_skill` (line 57)
  requires each plugin's `AGENTS.md` to backtick-cite exactly its own set of
  canonical `SKILL.md` paths.
- `test_canonical_skill_names_match_parent_directories_and_are_unique`
  (line 71) reads each skill's frontmatter name and requires it to equal its
  directory name and to be globally unique.

Every one of the five is a check on resolution, naming or uniqueness. None
presents a request. None reads the `## Marketplace boundaries` section. None
reads the `Request` column of either router table. The filing's core claim
reproduces verbatim.

`scripts/promise_machine.py` adds more resolution checking, not less.
`check_routers` at line 2097 fixes the router path, refuses a second router
(PM040), refuses a `version:` line in its frontmatter (PM043, line 2129),
refuses any link that is not a confined root or plugin runtime contract
(PM042, line 2159), and requires exactly one link to each (PM041, PM042). The
commands run clean at this ref:

```text
python3.13 scripts/promise_machine.py check         -> clean: 14 plugin(s), 14 copy/copies            exit 0
python3.13 scripts/promise_machine.py coverage --check -> clean: promises=72 coverage_rows=72 coverage_selected=72  exit 0
python3.13 scripts/portable_promise_machine.py check   -> checked .agents/skills/promise-machine/runtime  exit 0
python3.13 plugins/horos/skills/horos/scripts/horos.py check . -> boundary matches the tree              exit 0
```

Two corrections to the filing. First, the router is not entirely without a
refusal: lines 79 to 82 tell an agent that finds no matching row to "stop at
inspection and explain the uncovered boundary". What has no rule is the case
where two rows both match. Second, the absence of a domain promise is partly
deliberate. `PROMISE_MACHINE.md` line 33 says routers "select that
implementation and establish no domain result of their own". The gap is that
nothing promises anything about **selection itself**, which is not a domain
result.

One thing has moved since the filing, and it widens rather than narrows the
gap. `tests/test_portable_skills.py` has not changed since commit `54bb584`
on 2026-08-20, while the router changed three times after it (`96acb17`,
`43babf2`, `f0e7a39`). PR #677 gave the router a second runtime path -- an
installed Agent Skills package that reads `PORTABLE.md` and a generated
`runtime/` mirror -- and no test presents a request against either path.

### The last two merged pull requests touching the subject

The repository squash-merges, so merge commits are not a usable index; each
commit was mapped to its pull request through the REST commits-to-pulls route.

Router (`.agents/skills/promise-machine/SKILL.md`), most recent first:

- [PR #677](https://github.com/wildcat-finance/skills/pull/677), "Package
  Promise Machine for skills.sh", merged 2026-08-27, merge commit `2477db13`,
  which is this run's base. Its body has three change bullets and three
  verification bullets and carries no carried-forward section, nothing not
  done, and no open item. Nothing to carry forward.
- [PR #596](https://github.com/wildcat-finance/skills/pull/596), "docs: refresh
  the Shoggoth collective map", merged 2026-08-24. Its only carve-out is its
  closing line, that the five Pashov skill surfaces are named and placed but
  their files are unchanged. This run does not touch them either, so that
  carve-out is carried forward as a non-goal. Its verification list reports
  "Promise Machine integrity and 71-row coverage checks", which is resolution
  coverage; it is named here because it is the exact evidence a reader could
  mistake for selection evidence.

Test file (`tests/test_portable_skills.py`), most recent first:

- [PR #286](https://github.com/wildcat-finance/skills/pull/286), "Establish one
  portable Promise Machine identity", merged 2026-08-20, which created both
  files. Its Audit section records three identity-parser failures and one
  router false positive, each stated as fixed and guarded. Nothing is deferred.
- [PR #279](https://github.com/wildcat-finance/skills/pull/279), the Janus
  build, merged 2026-08-20, which touched the test file only through a
  back-merge of `origin/main`. It does carry deferred work -- two accepted
  manifest limitations and a second host adapter -- and all of it is Janus's,
  not the router's. Refused by name: none of it is in scope here.

Issue 499 itself has zero comments, zero cross-references and no linked pull
request across its whole timeline. `gh issue list --search "routing eval
corpus"` returns nothing. No sibling issue owns a routing corpus.

### Audit records

`python3.13 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 and reports 23 source records, every one `budget=pass` and
`committed=match`. A verified synopsis is therefore the normal reading view.

In-scope sources, what was read, and why:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/AUDIT.md` | the source, directly | The whole-set check is clean, but four of the findings this design rests on are written in the `FINDING`/`END` block form, and `grep -c` over `audit/AUDIT_SYNOPSIS.md` returns 0 for `S6-R1-01`, `S6-R1-02`, `S7-R1-01`, `S7-R1-02` and `B5-R1-01`, against 3, 2, 1, 1 and 1 in the source. The synopsis is current and still drops them. |
| `plugins/hexaemeron/audit/AUDIT.md` | the source, directly | 71 lines; reading the source cost less than deciding whether its synopsis carried the routing material. It carries none. |
| `plugins/ariadne`, `plugins/pandects`, `plugins/probitas`, `plugins/tabularium` `audit/AUDIT.md` | synopsis, then a targeted source grep | The whole-set check is clean. A grep of each source for the router, routing, selection, misroute, evaluation corpus and `test_portable_skills` returned one hit, in `plugins/probitas/audit/AUDIT.md` at line 808, describing that plugin's now-deleted portable entrypoint. Nothing in scope. |
| The 17 files under `audit/rounds/` | synopsis, then a targeted source grep | Same check, same terms. Every hit is the literal token `Promise Machine` or `promise_machine.py` inside a mechanical-gate evidence line, plus three low findings about a stale `tests/promise_machine_coverage.json` digest in `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md` at lines 45, 259 and 314. None concerns selection. |

The four findings that govern this design, quoted from `audit/AUDIT.md`:

- Promise Machine, step 3, round 1, 2026-08-20, `Leads not pursued`, lines 5138
  to 5141: "Runtime contracts identify canonical paths in their selection
  prose, but the checker does not interpret natural-language request
  predicates. The sole router and plugin contracts remain agent instructions;
  exact semantic request routing is demonstrated manually rather than
  represented as a second policy language." That round's findings are
  `S3-R1-01` and `S3-R1-02` (high) and `S3-R1-03` (medium), all fixed and
  guarded. Round 2, line 5158, records zero findings and adds: "The
  natural-language routing boundary recorded in round 1 remains unchanged."
  This is the repository's own prior record of the gap issue 499 files, and it
  is why design option B below is refused rather than merely rejected.
- Promise Machine, step 6, round 1, finding `S6-R1-01` (high),
  `tests/promise_machine_coverage.json`: three judgement-held promises cited
  mechanical parser tests, so "The coverage map overstated what those tests
  established." Fixed by adding 15 labelled review cases "that record P/M/S/O/R
  judgements without presenting them as checked runtime proof." `S6-R1-02`
  (medium) added the validated optional `evidence_class` field because
  "Recorded judgement cases were indistinguishable from executable checks."
  Its `Leads not pursued`, lines 5293 to 5298: "Recorded review cases establish
  that each decision path has been named and kept inside its boundary; they do
  not turn a human review judgement into runtime proof."
- Promise Machine, step 7, round 1, `S7-R1-01` (high): Vulgate cases used an
  evidence class its promise does not accept, so "A recognised class could pass
  even when the owning promise excluded it." `S7-R1-02` (medium): evaluation
  corpora could use checkout-specific absolute paths, fixed by requiring
  "confined repository-relative corpus paths". Its `Leads not pursued`, lines
  5360 to 5363: "Labelled cases describe expected decisions and do not
  establish that a future model will follow them. The coverage rows name
  `not-run` wherever no model, campaign, conversion, sync, pre-audit or audit
  was executed."
- Berean, step 5, round 1, `B5-R1-01` (medium),
  `plugins/berean/scripts/berean_lib/promote.py`, fixed in `df5edc7`:
  "Promotion checked the pinned report's digests and counts but never graded,
  so a report claiming a clean pass would promote a release whose cases fail
  when graded today."

Every one of the four is carried forward into this design as content: `S7-R1-01`
into the promise's declared evidence classes, `S7-R1-02` into the corpus's
repository-relative paths, `S6-R1-01` and `S6-R1-02` into the split between the
deterministic gate and the recorded score, and `B5-R1-01` into the rule that a
recorded run whose digest disagrees with the corpus on disk is refused rather
than believed.

### Machinery that already exists

- `plugins/hexaemeron/tests/test_promise_evaluation_cases.py` (65 lines) and
  `plugins/sapheneia/tests/test_promise_machine_cases.py` (55 lines) both read
  a `promise-machine-labelled-cases/v1` JSON fixture and hold it to a fixed key
  set, a fixed disposition per category, and an `evaluation` block naming
  `model`, `prompt`, `corpus` and `disposition`. Eight and three promises
  respectively. Their fixtures record `"model": "not-run"` where nothing ran.
  This is the repository's established shape for a judgement-held promise, and
  it is the shape this design follows.
- `tests/promise_machine_coverage.json` binds 72 rows to 72 promises, plus
  three capability entries keyed `contributor_ranking`, `run_observation` and
  `run_observation_capture`, each naming a root-law promise id, a runtime path
  with its digest, a tests path with its selectors, fixtures and a versioned
  document. `tests/test_unique_identifiers.py` enforces all of it generically:
  `test_every_bound_capability_digest_matches_the_file_it_names` recomputes
  every digest "so a capability added later is bound by construction",
  `test_every_bound_capability_selector_exists_in_its_test_file` requires each
  selector to be a real `def`, and `test_every_contract_document_is_bound_to_evidence`
  requires any `docs/promise-machine/*-v[0-9]*.md` to be bound.
- `plugins/berean/scripts/berean_lib/evals.py` (277 lines) grades a pinned
  corpus with one grader per expectation and refuses to start when a pinned
  digest disagrees with the bytes on disk. Its digest-first discipline is
  borrowed. Its release, corpus and chain-read document shapes are not.
- `plugins/brevitas/skills/brevitas/scripts/run_evals.py` (65 lines) walks
  `evals/cases/*/` directories of `case.json`, `original.md` and `target.md`,
  pins each original by digest and asserts a compression or retention
  expectation. Three cases. Nothing in it concerns selection.
- `plugins/hexaemeron/skills/imprimatur/scripts/evaluate_labelled_corpus.py`
  (42,842 bytes) is the repository's one scored corpus with pre-registered
  gates, annotator agreement and a sealed holdout. Imprimatur's ledger records
  that labelled-prose-v1 failed those gates and that its holdout is spent. It
  is read here as a warning about weight, not as a template.
- `tests/test_marketplace_prose.py` line 415 states in a docstring that "the
  marketplace boundaries in `AGENTS.md` are where that routing belongs". It is
  the only place in `tests/` that mentions the section, and it mentions it to
  explain why a different paragraph was removed.

### The named boundaries, verified at this base

All fourteen plugins exist. The `## Marketplace boundaries` section runs from
`AGENTS.md` line 28 to line 49 and names every one of them. The filing's three
pairs are present, and the section supports more:

| Pair | The sentence that decides it, verbatim from `AGENTS.md` | Lines |
| --- | --- | --- |
| Alexandria against Tabularium and Probitas | "Alexandria preserves lending inputs; Tabularium interprets preserved venue records; Probitas assembles a counterparty dossier." | 32 to 33 |
| Berean against Lemma | "Berean holds a protocol agent's recorded answers to pinned corpora and preserved chain reads; it neither chunks documents nor preserves chain state itself." with "while Lemma stops after producing source-linked chunks" | 35 to 36, 39 to 40 |
| Berean against Lazarus | "Lazarus preserves the finite historical Ethereum state and exact RPC traffic a test needs", against the same Berean sentence | 33 to 34 |
| Pandects against Janus | "Janus checks what a contract hook may observe and change around a host action, where Pandects supplies the economic laws such a transition must preserve." | 41 to 43 |
| Pandects against Hermes | "Pandects supplies reviewed credit laws, Hermes measures a single gas-optimisation class named by a rule from its pinned corpus" | 37 to 39 |
| Lazarus against Ariadne | "while Ariadne binds a released artefact digest to its evidence" | 34 |
| Sapheneia against every other skill | "It does not change another skill's facts or gates." | 45 to 46 |
| Brevitas against Imprimatur and Vulgate | "Brevitas controls the volume and structure of engineering prose after vocabulary and register passes." | 46 to 47 |

The section closes, at lines 47 to 49: "If a request crosses one of those
boundaries, hand it to the named sibling rather than broadening the selected
skill."

Beyond the fourteen, the router's Hexaemeron table carries its own near
neighbours that the boundaries section does not cover: `elenchus` against
`metron`, `phylax` against the Pashov row, `imprimatur` against `vulgate`
against `brevitas`, and `protasis` against `fiat` against `hypomnema`. Each of
those rows carries its own `Request` predicate, and each predicate is a
selection claim nothing tests.

### The owner

The work upgrades no governed skill, and the study says so rather than
attaching it to a convenient ledger.

The evidence. `scripts/promise_machine.py` builds its promise universe in
`promise_records` at line 1332, which iterates `inventory.skills` -- plugin
canonical skills -- and then the vendored overlay, and nothing else. The
router is not in that set, so a `## Promise Machine contract` written into
`.agents/skills/promise-machine/SKILL.md` would be discovered by no checker,
required by no coverage row, and enforced by nothing. `grep -rn` over every
canonical `SKILL.md` for the router's path, "portable router" or "the router"
returns no match outside the generated mirror: no skill's contract mentions it.
The 28 canonical skills sit under `plugins/`; the router sits at the repository
root beside `AGENTS.md` and `PROMISE_MACHINE.md`.

The root law already holds four promises of its own --
`promise-machine-first-party-licence`,
`promise-machine-run-observation-structural-validation`,
`promise-machine-run-observation-capture` and
`promise-machine-contributor-ranking` -- and three of the four are bound by a
capability entry in `tests/promise_machine_coverage.json` rather than by a
coverage row. That is the shape a root capability takes, and it is the shape
this work takes.

**The ledger row the run owes: none.** `fiat-v4.7.1` states the rule in the
ledger itself: "Ordinary delivery passes no flag and owes no row." The run
starts without `hexctl init --frontier`, and `done integrate` therefore does
not demand a new row. Precedent supports this: of the framework-N issues that
have closed, `skills#436`, `skills#466` and `skills#617` each took a Fiat
generation row because each changed a Fiat surface, while `skills#370`,
`skills#434`, `skills#435`, `skills#447`, `skills#510`, `skills#540` and
`skills#541` appear in no ledger at all.

What the run owes instead, and this is the equivalent obligation:

1. one new `### promise-machine-router-selection` block in `PROMISE_MACHINE.md`
   with all nine required fields;
2. one new capability entry keyed `router_selection` in
   `tests/promise_machine_coverage.json`, naming that promise id, the corpus
   fixture with its digest, `tests/test_router_selection.py` with its
   selectors, and `docs/promise-machine/router-selection-v1.md` with its
   digest; and
3. one `python3.13 scripts/portable_promise_machine.py sync` in the same commit as
   any change to `PROMISE_MACHINE.md`, `AGENTS.md` or the router.

The one contingency, stated so a later phase does not have to guess: if the
run ends up editing a file under `plugins/hexaemeron/skills/fiat/`, it owes one
`fiat-v5.31.1` generation row retaining `state-shape-validation`, the digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, status
`open` and the held issue-363 job byte for byte. The design below does not edit
that directory, so the contingency is expected to stay closed.

## 3. Constraints and non-goals

**Starting ref.** `2477db1352a4099445867216f6fd9a2e84963f3a`, branch
`fiat/499-grade-router-selection-not-just-resolution` cut from `main`.

**Toolchain.** CPython 3.13.15 per `.python-version`, with
`requires-python = "==3.13.*"` in `pyproject.toml`, and nothing else. Standard
library only; the repository declares no runtime dependency for root tests.
The new checker may use any syntax 3.13 accepts. An earlier draft of this
study constrained it to 3.9 so a second suite run could stay green; that
constraint is void, because there is no second suite run.

Obtaining the pin, so a later reader reproduces it rather than guessing:

```bash
uv self update              # 0.12 or newer; 0.11.14's index stops at 3.13.13
uv python install 3.13.15
uv python find --no-project 3.13.15
```

The install puts a `python3.13` shim on the path, and every command below uses
it. `uv python find --no-project 3.13.15` prints the resolved binary, here
`~/.local/share/uv/python/cpython-3.13.15-macos-aarch64-none/bin/python3.13`;
that directory name carries the platform triple, so another machine's path
differs. `uv run --python 3.13.15 python ...` is the alternative form and is
what the Hexaemeron suite needs, because that suite wants Lazarus's
requirements. It writes an untracked `uv.lock` into the checkout, so a step
that uses it removes that file before committing or the tree is dirty.

**Observed baselines at this ref**, every one on CPython 3.13.15, so a later
run can tell a regression from a green tree:

| Command | Result | Exit |
| --- | --- | --- |
| `python3.13 -m unittest discover -s tests` | 438 of 438 in 32.1s | 0 |
| Hexaemeron suite, `uv run --python 3.13.15` under Node 26.6.0 | 1,379 of 1,379 in 422.1s | 0 |
| `python3.13 scripts/promise_machine.py check` | `clean: 14 plugin(s), 14 copy/copies` | 0 |
| `python3.13 scripts/promise_machine.py coverage --check` | `clean: promises=72 coverage_rows=72 coverage_selected=72` | 0 |
| `python3.13 scripts/portable_promise_machine.py check` | `checked .agents/skills/promise-machine/runtime` | 0 |
| `python3.13 plugins/horos/skills/horos/scripts/horos.py check .` | `boundary matches the tree` | 0 |
| `python3.13 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` | 23 records, every one `budget=pass` and `committed=match` | 0 |

The tree is green at this base. There is no known-red carve-out, so a step that
reports a suite pass reports a pass, and any red it sees belongs to the change
in front of it. The Hexaemeron count is the same 1,379 on the pin as on the
3.13.13 image an earlier draft recorded, so a runbook `Tests` field naming that
suite holds 1,379 either way; the figure above is the one measured on the pin.

**Commands that gate the change.**

```bash
python3.13 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call 'uv run --python 3.13.15 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py'
python3.13 scripts/promise_machine.py check
python3.13 scripts/promise_machine.py coverage --check
python3.13 scripts/portable_promise_machine.py check
python3.13 plugins/horos/skills/horos/scripts/horos.py check .
python3.13 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <changed prose>
python3.13 plugins/brevitas/skills/brevitas/scripts/brevitas.py <changed prose>
python3.13 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3.13 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3.13 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
rm -f uv.lock
```

**The mirror rule, established from the checker rather than from memory.**
`scripts/portable_promise_machine.py` computes an expected payload from three
sources: the 18 fixed paths in `ROOT_FILES` at lines 23 to 41, every
git-tracked file under `plugins/` that `_omitted` (line 109) does not drop, and
a generated `.horos/boundary.json`. `_omitted` drops a path only when
`parts[2]` is `.claude-plugin`, `.codex-plugin`, `audit` or `tests`, plus three
Alexandria example subtrees. `check` (line 230) then requires
`.agents/skills/promise-machine/runtime/` to be byte-identical to that payload
plus its `MANIFEST.json`. Three consequences this run depends on:

- `AGENTS.md`, `PROMISE_MACHINE.md` and the router `SKILL.md` are all in
  `ROOT_FILES`, so any edit to any of them needs a `sync` in the same commit.
- `plugins/<name>/tests/**` is omitted, but
  `plugins/<name>/skills/<skill>/tests/**` is not, because `parts[2]` is
  `skills` there. A fixture placed under a skill directory is mirrored.
- Root `tests/**` is neither in `ROOT_FILES` nor under `plugins/`, so it is not
  mirrored at all. The corpus and its checker therefore need no sync of their
  own.

**Router prose constraints.** `check_routers` refuses a `version:` line
(PM043). It also requires exactly one Markdown link to the root `AGENTS.md`
and one to each plugin's, and refuses every other link (PM041, PM042). New
prose in the router is allowed. A link from it to the corpus is refused.

**Non-goals.**

- Establishing that any agent routes correctly. The delivery measures and
  records; it does not prove.
- A rule engine that maps request text to a selection. `audit/AUDIT.md` lines
  5138 to 5141 already declined "a second policy language", and this run keeps
  that decision.
- Changing the boundaries themselves. The corpus quotes `AGENTS.md`; it does
  not rewrite it.
- Touching the vendored Pashov trees, the five surfaces PR #596 named and left
  unchanged.
- A gate on the recorded score. The score is recorded evidence with its
  failures named. Making it a gate would invite tuning the corpus to the model.
- Grading the installed Agent Skills path separately from the source path. The
  corpus grades selection, which is the same table on both paths.

## 4. Design options

**Option A, a recorded corpus with a deterministic prose-binding checker.**
A JSON corpus at `tests/fixtures/router-selection/cases.json` under a new
`promise-machine-router-selection/v1` schema. Each case carries an id, a
family, the request phrasing, an expectation (`select` with a canonical name,
or `refuse` with `ambiguous` or `uncovered`), the contested siblings for a hard
case, the deciding sentence quoted verbatim from `AGENTS.md` or a router row,
and the boundary the selection does not establish. A root test
`tests/test_router_selection.py` checks shape and id uniqueness, that every
expected canonical name is a real canonical skill, that every deciding sentence
still occurs verbatim in the section it names, that every router row's
canonical selection has at least one case, that every declared contested pair
has at least one case, and that any recorded run block carries a model, a date,
a corpus digest that recomputes, and named failures. The promise goes in
`PROMISE_MACHINE.md` and binds through a `router_selection` capability entry.
The trade: the suite never grades a model, so the gate establishes only that
the corpus has the shape its schema declares and still quotes sentences that
exist in the files it names. The grading itself stays recorded evidence about
one run.

**Option B, a deterministic selection engine.** Extract predicates from the
`Request` column and the boundaries prose into a matcher, run each request
through it, and score the matcher's answers against the corpus. The trade:
it produces a number every run, deterministically, with no model. It is
refused rather than merely rejected, because `audit/AUDIT.md` lines 5138 to
5141 already recorded the decision not to represent routing "as a second policy
language", and because a matcher that agrees with the corpus proves only that
two artefacts written by the same author agree. It would measure nothing about
the agent that actually routes.

**Option C, extend Berean's evaluation harness.** `berean_lib/evals.py`
already pins digests, refuses to grade a drifted corpus, and runs one grader
per expectation. The trade: real machinery reused instead of written. Rejected
on the boundary Berean itself declares. `AGENTS.md` line 35 scopes Berean to "a
protocol agent's recorded answers to pinned corpora and preserved chain reads",
and its `run` entry point requires a release document with a corpus manifest,
a corpus digest and optionally a chain id and block number. Routing has none of
those. Using it would broaden the selected skill across a boundary that lines
47 to 49 tell an agent to hand to a sibling instead -- and doing that inside
the delivery that grades boundary adherence would be its own joke.

**Option D, extend Brevitas's `run_evals.py`.** The trade: the lightest
existing runner, three cases, a directory per case. Rejected because its case
shape is `original.md` plus `target.md` graded by `lint_text`, with
`compress` and `retain-evidence` as its only expectations. Nothing in it
carries a selection, a canonical name or a sibling pair, so the reuse would be
the word `evals` and nothing else. It also lives under
`plugins/brevitas/skills/brevitas/`, which the mirror copies, so every corpus
edit would drag a `runtime/` resync.

**The pick: Option A.** It is the cheapest to comprehend, because it is the
shape two of this repository's own suites already use for a judgement-held
promise and the shape `tests/promise_machine_coverage.json` already binds. It
puts the corpus in root `tests/`, where the router's existing test already
lives and where no mirror sync follows an edit. Its checker is small enough to
read in one sitting and has one interpreter to satisfy. What it trades away is
a number on every run: a maintainer who wants to know whether routing improved
has to run the grading step deliberately and record what it found.

### The refusal, and what this run does about it

The filing's sharpest point is that a misroute produces no refusal, no recovery
path and no record. Splitting that three ways at this base:

- **No match.** Already has a rule. Router lines 79 to 82.
- **Two rows match.** Has no rule at all.
- **The wrong row is taken.** Has no record, because nothing writes down what
  the right row was.

This run ships the second and measures the third. The router gains a short
paragraph beside the existing no-match rule: when two rows both match, name
both and the boundary sentence that separates them; select only if one row's
boundary sentence excludes the other; otherwise stop at inspection and say
which two rows and which sentence. Six sentences of prose, no new link, no
version, one `sync`.

That paragraph is not scope creep beside the corpus; it is the corpus's
precondition. A case whose expectation is `refuse: ambiguous` cannot be graded
against a router that never says an ambiguous request should be refused. The
third item -- making a wrong selection produce a record at the moment it
happens -- is out of scope and stated as such, because it needs a runtime the
router does not have and one step cannot hold both.

### What a score establishes, and what would count as a pass

A recorded run block establishes: this model, given this prompt template, with
only the `request` field of this exact corpus digest visible, selected these
canonical skills on this date. Evidence class `measured`. It does not establish
that another model routes the same way, that the same model routes the same way
tomorrow, that the corpus is representative of real requests, or that a case
the model got right was got right for the boundary the case names. It is never
`proved`.

Re-runnable by a later run, exactly:

1. `python3.13 tests/emit_router_selection_report.py --requests` prints one
   request per line with its case id and nothing else.
2. Each request goes to a fresh agent context loaded with the router,
   `AGENTS.md` and the plugin runtime contracts, and with neither the corpus
   nor this study.
3. The selection it returns is written into a run block: `model`, `date`,
   `prompt_template_sha256`, `corpus_sha256`, `cases`, `passed`, `failed`, and
   `failures` as a list of case ids with the selection actually made.
4. `python3.13 -m unittest tests.test_router_selection` refuses a block whose
   `corpus_sha256` disagrees with the corpus on disk, which is `B5-R1-01`'s
   lesson applied here.

The reporting convention, which is not a gate: a run is worth reporting as a
pass when `failed` is 0 across the hard cases. A run with failures is recorded
with every failing case id, and the failure is read as evidence about the
prose, the corpus or the model, in that order.

## 5. Risk register seed

The corpus is data read by a test, so the classic Python risks here are the
filesystem and partial-write ones rather than subprocess or secret handling.
The prose-binding and overclaim concerns carry more weight than either, because
the whole artefact is a claim about what other prose says.

```risk-register
corpus-prose-drift | each case's deciding_sentence against AGENTS.md and the router | every quoted sentence still occurs verbatim in the named section, and a reworded boundary fails the suite rather than passing silently
grader-contamination | the corpus fields visible to a graded agent during a recorded run | the run block records the exact prompt template and its digest, and the graded context received the request field alone
score-overclaim | the promise text, the run block and every surface that cites a score | no surface calls a recorded score proved, and the block names its model, date and corpus digest
digest-selfreference | the recorded corpus_sha256 against the file that contains it | the digest covers the cases array alone, so recording a run does not change the value it pins
mirror-drift | .agents/skills/promise-machine/runtime after any ROOT_FILES or plugin change | scripts/portable_promise_machine.py check exits 0 in the same commit as the change
router-link-shape | Markdown links in .agents/skills/promise-machine/SKILL.md | the router still links to the root and the fourteen plugin runtime contracts exactly once each, so PM041 and PM042 stay clean
coverage-binding-gap | the router_selection entry in tests/promise_machine_coverage.json | every recorded digest recomputes, every named selector is a real def, and the promise id is unique across rows and capability keys
interpreter-split | the interpreter a contributor's ambient python3 resolves to against the 3.13.15 pin | every recorded suite result names the image it ran on, and a run on any other image is reported as no result rather than as a pass
boundary-currency | .horos/boundary.json after the corpus fixture lands | horos.py check . exits 0, or the boundary is regenerated in the same commit
case-coverage-decay | the corpus against a newly added plugin, skill or router row | a router row or canonical skill with no case fails the suite instead of being noticed later
partial-corpus-write | tests/fixtures/router-selection/cases.json during an edit | a truncated or non-UTF-8 corpus fails the checker by name rather than reading as an empty case set
```

## 6. Glossary seeds

- **Resolution.** A link or a name that points at a file which exists. What
  `tests/test_portable_skills.py` checks today.
- **Selection.** Choosing one of the router's 24 rows for a request. What
  nothing checks today.
- **Router row.** One line of either table in
  `.agents/skills/promise-machine/SKILL.md`, carrying a `Request` predicate, a
  runtime contract and a canonical selection.
- **Canonical selection.** The skill name a router row names, matching a
  `SKILL.md` frontmatter name under `plugins/`.
- **Hard case.** A corpus case whose `contested` list holds two or more
  siblings whose boundary the request sits near.
- **Deciding sentence.** The verbatim sentence from `AGENTS.md` or a router row
  that a case says settles it.
- **Run block.** One recorded grading run: model, date, prompt-template digest,
  corpus digest, counts and named failures.
- **Capability entry.** A top-level key in `tests/promise_machine_coverage.json`
  that binds a root-law promise to its runtime, tests, fixtures and document,
  as `contributor_ranking` and `run_observation` already do.
- **Portable runtime mirror.** `.agents/skills/promise-machine/runtime/`, the
  byte-identical generated copy `scripts/portable_promise_machine.py` owns.

## 7. Sources

- `.agents/skills/promise-machine/SKILL.md` at `2477db13`, 82 lines, the router
  under study.
- `.agents/skills/promise-machine/PORTABLE.md`, the installed-package runtime
  path added by PR #677.
- `tests/test_portable_skills.py` at `2477db13`, 85 lines, five tests.
- `AGENTS.md` at `2477db13`, 229 lines; `## Marketplace boundaries` at lines 28
  to 49, loading rules at 143 to 154, checks at 156 to 229.
- `PROMISE_MACHINE.md` at `2477db13`; scope at line 33, promise-declaration
  fields, evidence classes, and the four `promise-machine-*` blocks.
- `scripts/promise_machine.py`, 2,956 lines; `promise_records` at 1332,
  `check_coverage` at 1411, `check_routers` at 2097, `COVERAGE_CODES` at 75,
  `PROMPT_SKILLS` at 87.
- `scripts/portable_promise_machine.py`, 295 lines; `ROOT_FILES` at 23,
  `_omitted` at 109, `check` at 230.
- `tests/promise_machine_coverage.json`, 72 rows and three capability entries.
- `tests/test_unique_identifiers.py`, the generic capability-binding tests at
  lines 121 to 261.
- `plugins/hexaemeron/tests/test_promise_evaluation_cases.py` and its fixture
  `plugins/hexaemeron/tests/fixtures/promise-machine/evaluation-cases.json`
  (11,814 bytes, schema `promise-machine-labelled-cases/v1`).
- `plugins/sapheneia/tests/test_promise_machine_cases.py`.
- `plugins/berean/scripts/berean_lib/evals.py` and
  `plugins/berean/schemas/eval-case-v1.json`.
- `plugins/brevitas/skills/brevitas/scripts/run_evals.py` and its three cases
  under `plugins/brevitas/skills/brevitas/evals/cases/`.
- `plugins/hexaemeron/skills/VERSIONING.md`, the evolution contract.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `fiat-v5.30.1`, frontier
  `state-shape-validation`, status `open`, held job `skills#363`.
- `audit/AUDIT.md`, Promise Machine steps 2, 3, 6 and 7; Berean step 5; the
  Imprimatur labelled-prose step 1.
- `docs/decisions/ADR-040-package-one-dependency-closed-portable-router.md`,
  the newest decision record, accepted 2026-08-27.
- [skills#499](https://github.com/wildcat-finance/skills/issues/499), its
  26 August 2026 review block and its historical filing.
- PRs [#677](https://github.com/wildcat-finance/skills/pull/677),
  [#596](https://github.com/wildcat-finance/skills/pull/596),
  [#286](https://github.com/wildcat-finance/skills/pull/286) and
  [#279](https://github.com/wildcat-finance/skills/pull/279).

## 8. Signals, and the questions behind them

The delivered artefact is a corpus and a unit test. It runs from a terminal and
from CI, never unattended, so it has no three-in-the-morning on-call question
of its own. That is not the same as having no signals, because the corpus is
designed to answer questions a person will actually ask, and the report command
is where those answers appear.

Two questions, and where each is answered:

1. "Somebody reworded a boundary sentence in `AGENTS.md`. Which cases are now
   wrong?" Answered by the suite failing, by case id, with the sentence it
   could not find and the section it looked in. Step 2 emits it.
2. "What did the last grading run find, and against which model and corpus?"
   Answered by `python3.13 tests/emit_router_selection_report.py`, which prints
   the run block or the word `not-run`. Step 3 emits it.

`ephoros` owns what a signal must carry, and the failure messages above are
written to its rules: each names the subject, the exact path, and the action
that clears it, and none echoes the corpus payload back at the reader.

## 9. Boundaries, per capability

Three boundaries open, and this feeds item 5 rather than replacing it.
`phylax` owns the boundary list and the controls.

1. **Reading a JSON file from the repository into a test.** Worth taking: the
   corpus has to live somewhere a test can read. The control is that the path
   is a fixed repository-relative constant with no argument, no glob and no
   caller-supplied component, which is `S7-R1-02`'s fix applied here; a
   malformed or non-UTF-8 file fails by name rather than reading as empty.
   Register ids `partial-corpus-write` and `corpus-prose-drift`.
2. **Reading `AGENTS.md` and the router to check the quoted sentences.** Worth
   taking: it is the check that turns prose into evidence. The control is that
   the checker only searches for a substring inside a named section and never
   writes, so a hostile edit to either file makes the suite fail rather than
   making the checker do something.
3. **Recording a model's output into a committed file.** Worth taking: the
   score is the point. The control is that the recorded block carries no model
   prose, only a canonical skill name per failing case id, drawn from the
   closed set of names the corpus already validates. Register ids
   `grader-contamination` and `score-overclaim`.

No credential, no subprocess, no network call and no new dependency. The
run adds no `# phylax: allow` marker.

## 10. The budget, or its absence

None, and here is why. The delivery adds one JSON fixture in the low tens of
kilobytes and one test module that reads it plus two Markdown files. The root
suite currently runs 438 tests in about 32 seconds on the pin; a file read and
a substring search per case is not a measurable share of that. `metron` owns what a budget
carries, and there is no performance claim here to hold. The one number worth
watching is not a budget: `test_shipped_prose_lints.py` records that 134
subprocess launches once took the root suite from 0.12s to 7.1s, so the new
checker loads its inputs in process and shells out to nothing.

## 11. The fail-closed posture

What stops the run: any of the eleven gate commands in item 3 returning
non-zero. Specifically, the suite fails closed when a deciding sentence no
longer occurs in the file it names, when a router row or canonical skill has no
case, when a recorded `corpus_sha256` disagrees with the bytes on disk, when a
capability digest or selector does not resolve, when the portable mirror drifts,
or when the Horos boundary no longer describes the tree.

The guard convention: `elenchus` owns the triage order and the guard rule, and
every fix this run makes to a failure it reproduces lands with a test that
fails without the fix. Two guards are planned rather than reactive, because
both failures are the ones this artefact exists to catch and a check that
cannot fail is worth nothing: a fixture corpus whose deciding sentence has been
altered must fail the prose-binding check, and a fixture corpus missing a case
for one router row must fail the coverage check. `tests/test_boundary_currency.py`
states the same principle for the Horos boundary and is the local model for it.

The runner contract for any audit round claiming a fix on this run:

```text
python3.13 -m unittest discover -s tests 2>&1 | tee {report}
```

with a plain-text unittest report written to `{report}`. The interpreter is
named rather than left to `python3`, because an ambient `python3` on this
machine resolves to 3.12.13 and a report produced there says nothing about the
tree.

## 12. Decisions and their homes

`hypomnema` owns which decisions earn a record and where each one lives. Three
here are expensive to reverse, and one is not.

1. **Where a root capability's promise lives, and that a router gets none.**
   Home: `docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md`,
   the next free number after ADR-040. It records that `promise_records` cannot
   see the router, that the root law is where a non-skill promise goes, and
   that `PROMISE_MACHINE.md` line 33 already says routers establish no domain
   result. Expensive to reverse because moving a promise later invalidates
   every coverage digest bound to it.
2. **The corpus schema, `promise-machine-router-selection/v1`.** Home:
   `docs/promise-machine/router-selection-v1.md`, the versioned contract
   document, bound by the `router_selection` capability entry because
   `test_every_contract_document_is_bound_to_evidence` requires it. Expensive
   to reverse because a schema change invalidates every recorded run block.
3. **That the score is recorded, never gated.** Home: the `Boundary` field of
   the `promise-machine-router-selection` block in `PROMISE_MACHINE.md`, which
   is where a reader who cites the promise will look. It is one sentence there
   rather than a fourth document, and it points at the study for the reasoning.
4. **Where the corpus file sits.** Not expensive to reverse and gets no record:
   moving a fixture inside root `tests/` costs one path constant and one
   coverage digest.

The study and runbook are committed under `docs/router-selection/` in step 1
and are the change-control boundary for everything above.

## Boundaries this study states

**Always.** The root suite and the Hexaemeron suite before a commit, on CPython
3.13.15 and on no other image. `python3.13 scripts/portable_promise_machine.py
check` in the same commit as any change to a mirrored file. Imprimatur then
Brevitas on every shipped document. The three tree lints from the repository
root. A recorded run block re-verified against the corpus digest before it is
believed. `rm -f uv.lock` after any `uv run`.

**Ask first.** Editing `AGENTS.md` or the router `SKILL.md`. Adding a
dependency. Changing `tests/promise_machine_coverage.json`'s schema rather than
adding an entry to it. Touching CI. Adding a promise to `PROMISE_MACHINE.md`.
Regenerating `.horos/boundary.json`. Turning any recorded score into a gate.

**Never.** Weaken a case so a model passes it. Edit a vendored Pashov
directory. Delete a failing test to make a suite pass. Record a run block
whose grading was not actually performed. Call a recorded score `proved`.
Publish under the Shoggoth account or ask for its signing key. Quote a host
attribution specimen in a commit message or a pull-request body.

## Step shape

Three steps. Two would bundle the corpus's easy half with its hard half and the
router prose change; four would split step 1's binding work from the fixture it
binds, and neither half would be green alone.

- **Step 1, scaffold and bind.** Commit the study and runbook under
  `docs/router-selection/`. Add the corpus with its schema, its declared pair
  table and one case per router row. Add `tests/test_router_selection.py` with
  the shape, canonical-name and prose-binding checks, and
  `tests/emit_router_selection_report.py`. Declare
  `promise-machine-router-selection` in `PROMISE_MACHINE.md`, add
  `docs/promise-machine/router-selection-v1.md`, add the `router_selection`
  capability entry, and sync the mirror.
- **Step 2, the hard cases and the ambiguity rule.** Add a contested case for
  every pair the boundaries section names and for the intra-Hexaemeron near
  neighbours. Add the coverage checks and their two guards. Add the router's
  ambiguity paragraph and re-sync.
- **Step 3, grade it and record what it found.** Present every request to a
  fresh agent context, write one run block, and run the demo path from item 1.

The runbook phase owns the entry, exit, files, tests and disciplines of each.
