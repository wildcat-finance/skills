<p align="center">
  <img src="./assets/characters/shoggoth.png" width="1200" alt="The Shoggoth collective">
</p>

# The Shoggoth

The Shoggoth is the collective distributed by this repository as **Wildcat
Labs Skills**: small, specialised agents for crypto research and development.
It helps people investigate protocols, preserve evidence, build and test
software, review contracts, measure changes, and deliver work without quietly
turning uncertainty into fact.

It is not one all-purpose assistant with a theatrical cast list. Each member
owns a bounded job. A member must say what it checked, show the evidence behind
the result, and stop where another specialist or a person needs to take over.
That makes the tools useful on their own and safer to compose into larger jobs.

The current repository contains 16 plugins and 25 governed first-party skills,
plus four tightly scoped delivery workers, one portable router, and five
unchanged skills from the upstream Pashov security suite. The identity contract
describes those 26 members as 17 domain agents and 9 phase agents.

## What can it do today?

Here are five representative jobs. Credit research is one of them, not the
definition of the project.

### Reproduce a historical protocol failure

[Lazarus](./plugins/lazarus) can preserve the finite historical Ethereum state
and exact RPC exchange needed by a test. [Elenchus](./plugins/hexaemeron/skills/elenchus)
can reduce an observed failure to its cause and leave a regression guard.
[Ariadne](./plugins/ariadne) can then bind a released fixture or fix to the
evidence that supports it.

This does not prove that an RPC provider was canonical or that the rest of the
protocol is correct. It gives the next person a finite, checkable record of the
part that was actually tested.

### Review and improve a Solidity protocol

The upstream X-Ray and Solidity Auditor skills map and review the code. Fizz
builds a stateful fuzz harness. [Janus](./plugins/janus) checks what a Wildcat
v2.5 hook may observe and change around its host action.
[Pandects](./plugins/pandects) supplies executable credit laws with broken
specimens that prove the laws can catch their named failures.
[Hermes](./plugins/hermes) handles gas work separately, keeping only measured
wins that preserve behaviour, storage layout, selectors, and required
arithmetic checks.

These tools cover different questions. Running all of them is not a claim that
a protocol is safe.

### Build a checkable protocol assistant

[Horos](./plugins/horos) can bound an initial repository reading.
[Lemma](./plugins/lemma) can turn Solidity compiler input or Markdown into
validated, source-linked chunks. Lazarus can preserve the chain values an
answer depends on. [Berean](./plugins/berean) can bind answers and evaluations
to those exact document bytes and chain reads, while Ariadne can bind a
promoted release to its record.

The mechanism works today. The checked-in Berean release is still a
demonstration built from a small corpus and preserved Goldfinch reads; there is
not yet a live Wildcat reference assistant.

### Compare repeated agent runs

The [Promise Machine](./PROMISE_MACHINE.md) can validate and capture bounded run
observations. [Synkrisis](./plugins/synkrisis) can turn declared observations
into one checked cohort, apply deterministic rules, render a fixed report, and
recompute the path from the original inputs.

Its shipped rule catalogue has only been exercised on constructed records so
far. A finding is a lead for a named owner, not a diagnosis or permission to
act.

### Research an on-chain borrower

[Alexandria](./plugins/alexandria) preserves raw lending records by digest.
[Tabularium](./plugins/tabularium) interprets supported venue records into a
reproducible event release. [Probitas](./plugins/probitas) assembles a sourced
dossier from addresses the subject declared, leaving gaps and unattributable
activity visible for a human decision-maker.

That path is deliberately narrow. It does not discover every address, infer a
person behind an address, or make an underwriting decision.

## What is not built yet?

Some members are mature within a narrow promise. Others are useful but have an
obvious missing surface. A few are scaffolds for work that has not landed.

- [Dokimasia](./plugins/dokimasia) is the future home for the question a
  release spreadsheet cannot answer: which of an application's routes, actions
  and guards has no reviewed oracle. Its compile path has not shipped.
- [Homologia](./plugins/homologia) admits a closed manifest and evidence-classed
  expected integers into checked inputs. Mirror execution, integer comparison
  and a parity verdict still need to be built.
- Alexandria and Tabularium each have one Compound v3 Phase 0 witness, not a
  complete resumable Ethereum USDC collection and canonical adapter.
- Berean has no live Wildcat reference release. Synkrisis has no captured
  production cohort. Their machinery should not be confused with field proof.
- Janus has one host adapter. Hermes can select 62 of the 120 rules in its
  pinned optimisation corpus. Lemma does not independently validate ABI return
  types or state mutability.
- Fiat's checkpoints are local. They survive context loss on one machine; they
  are not a distributed continuation system.
- Passing a structural or security check proves only the named relation. The
  Promise Machine does not turn that result into proof that the underlying
  claim, design, or protocol is true.

[Futureproofing the Shoggoth](./FUTUREPROOFING.md) lists what every member ships,
what evidence is missing, and what a credible final form could look like. It
does not assign maturity scores or pretend that a roadmap item already exists.

## How the collective works

A **skill** is a set of instructions and checks for one kind of job. A
**plugin** is the package that installs one or more skills. The portable
**router** reads the request and loads one canonical skill; it does not perform
domain work itself.

The [Promise Machine contract](./PROMISE_MACHINE.md) is the shared law between
first-party skills. In plain language:

1. State exactly what a successful operation establishes.
2. Name the evidence needed to support that result.
3. Carry caveats forward when another skill consumes it.
4. Refuse only the dependent action when evidence is missing or stale.
5. Leave inspection, repair, rerun, rollback, and safe exit available.

The Promise Machine checks those relationships and the repository structure.
It does not certify the truth of a domain claim. The longer
[plain-language guide](./docs/the-promise-machine-explained-properly.md) walks
through an ordinary example before introducing the formal vocabulary.

The bounded [agent instruction language prototype](./docs/agent-instruction-language-v1.md)
adds one derived compact view over three reviewed source fragments. Its checked
demonstration preserves 15 source bindings and 14 hostile mutations, saves 77
bootstrap-inclusive tokens on the declared three-document cohort, and records
18 of 18 source-versus-compact answer pairs across two local model families. It
does not translate arbitrary English or establish Shoggoth readiness.

[Hexaemeron](./plugins/hexaemeron) is the delivery plugin.
[Fiat](./plugins/hexaemeron/skills/fiat) is its explicit-only controller for a
full repository change: study, runbook, implementation, audit, prose, push,
and integration. Each transition is recorded so that the run can be resumed
from durable state instead of reconstructed from chat. Naming a coding task
does not start Fiat; the user must ask for Fiat or Hexaemeron to run.

## Meet the collective

The short descriptions below say what each member owns. Follow a link for its
operations, examples, evidence contract, and current frontier.

### Sources, history, and checkable releases

- [Horos](./plugins/horos) decides what an agent does not initially read and
  verifies that boundary against repository drift. Its exclusions never apply
  during security review.
- [Lemma](./plugins/lemma) prepares source-linked Solidity or Markdown chunks.
  It stops before embeddings, retrieval, or answer generation.
- [Lazarus](./plugins/lazarus) preserves the finite historical chain state and
  exact RPC traffic needed by one application test.
- [Berean](./plugins/berean) checks a protocol agent's answers against pinned
  documents and block-bound chain reads, then records evaluation, promotion,
  and rollback.
- [Ariadne](./plugins/ariadne) binds a released artefact digest to inspectable
  evidence statements. It records coverage, not universal truth.
- [Synkrisis](./plugins/synkrisis) compares declared observations from several
  runs under one operator-declared policy and bounded rule catalogue.
- [Anamnesis](./plugins/anamnesis) keeps audit findings and the changes that
  answered them, admitted against an explicit rights basis. It releases
  read-only projections rather than lending its source material.

<p align="center">
  <a href="./plugins/anamnesis#character">
    <img src="./plugins/anamnesis/assets/characters/anamnesis.webp" width="960" alt="Anamnesis, keeper of the recalled record">
  </a><br>
  <a href="./plugins/anamnesis#character">Keeper of the recalled record</a>
</p>

### Protocol behaviour and Solidity

- [Janus](./plugins/janus) checks what a contract hook may observe and change
  before and after a host action.
- [Pandects](./plugins/pandects) maintains executable credit laws, each with a
  broken specimen it is proved to catch.
- [Hermes](./plugins/hermes) measures one named Solidity gas-optimisation class
  at a time and rejects unsafe or unproved savings.
- [Dokimasia](./plugins/dokimasia) compiles a frontend's routes, actions and
  guards into a coverage denominator and reconciles a reviewed workbook against
  it. Its compile path has not shipped.
- [Homologia](./plugins/homologia) admits one pinned pair and its declared
  vectors into deterministic checked inputs. Its mirror-execution and
  comparison path has not shipped.

The unchanged upstream Pashov suite sits alongside these specialists:
**X-Ray** maps a Solidity repository before review, **Solidity Auditor** reviews
the contracts, **Fizz** generates a stateful fuzz harness, **Fizz Convert**
turns recorded properties into assertions, and **Fizz Sync** reconciles a
harness after the source changes. Wildcat does not rename, rewrite, govern, or
relicense those five skills.

### Lending and credit records

- [Alexandria](./plugins/alexandria) preserves heterogeneous lending captures
  and exposes narrow, source-bound views.
- [Tabularium](./plugins/tabularium) maps supported venue-native records into a
  reproducible credit-event release with explicit coverage.
- [Probitas](./plugins/probitas) builds a declared-address borrowing and
  repayment dossier without hiding unknowns or making the decision for a
  person.

### Delivery and engineering disciplines

- [Fiat](./plugins/hexaemeron/skills/fiat) controls the complete, receipted
  delivery loop.
- [Protasis](./plugins/hexaemeron/skills/protasis) checks the study and runbook,
  then follows one closed design-evidence record through design lock, each
  implementation step, and integration. It refuses when a candidate was not
  compared against every declared criterion or evidence due at that transition
  is missing.
- [Phylax](./plugins/hexaemeron/skills/phylax) hardens off-chain inputs,
  subprocesses, URLs, secrets, dependencies, paths, and model output.
- [Ephoros](./plugins/hexaemeron/skills/ephoros) specifies the events, metrics,
  correlation, traces, and alerts needed to explain unattended work.
- [Metron](./plugins/hexaemeron/skills/metron) governs non-gas performance by
  comparing one change against one recorded baseline.
- [Elenchus](./plugins/hexaemeron/skills/elenchus) works a reproduced failure to
  its cause and leaves a guard that fails without the fix.
- [Hypomnema](./plugins/hexaemeron/skills/hypomnema) decides what needs a
  durable record and where that record belongs.
- [Imprimatur](./plugins/hexaemeron/skills/imprimatur) diagnoses banned AI
  writing habits and unsupported terms. It does not rewrite the draft.
- [Vulgate](./plugins/hexaemeron/skills/vulgate) rewrites prose into a plain
  human register while holding the facts, caveats, and commitments constant.
- [Kronos](./plugins/hexaemeron/skills/kronos) can rank eligible held frontier
  jobs and dispatch the best unparked one through Fiat, but only on an explicit
  Kronos request.
- [Sapheneia](./plugins/sapheneia) shapes replies and bounded durable records
  for AuDHD readers without changing their protected evidence.
- [Brevitas](./plugins/brevitas) constrains engineering prose after the wording
  passes while preserving details that control a decision.

The roster contains 26 members: 17 domain agents and
9 phase agents. The four named Fiat workers are bounded execution roles rather
than extra skills:

- **Surveyor** writes one source-bound study.
- **Mason** implements and tests one exact runbook step.
- **Warden** performs one audit round, preserves findings, and returns fixes
  and an Elenchus verdict.
- **Scribe** performs one bounded prose pass over the shipped change.

None of them may advance or receipt the controller, widen its packet, or claim
publication authority. Fiat may perform the same packet inline when an
isolated worker is unavailable; the packet and artefacts remain the authority.

## Try it

To install the dependency-closed router through the Agent Skills convention:

```bash
npx skills add wildcat-finance/skills-runtime --skill promise-machine
```

That package is generated from this repository and published hourly to
[wildcat-finance/skills-runtime](https://github.com/wildcat-finance/skills-runtime),
so an install can be up to an hour behind `main`. The router verifies its local
runtime before it selects a specialist. See the
[installation guide](./INSTALL.md#local-agents) for the non-interactive Codex
command, private organisation distribution, first-party licence boundary, and
the boundary of that package.

You can begin with a concrete request:

```text
Use $lazarus to capture the finite historical state and exact RPC exchange this failing test needs, then verify that it replays offline.

Use $janus to check this Wildcat v2.5 hook against a conformance manifest for what it may observe and change around the host action.

Use $lemma to turn this Markdown documentation tree into validated, source-linked JSONL chunks. Stop before embedding or retrieval.

Use $synkrisis to build and verify one cohort from these declared run observations. Treat each finding as a bounded lead, not a cause.

Use $vulgate to rewrite this release note in plain human language without changing its facts, qualifications, links, or commitments.
```

Homologia is intentionally absent from the working examples because its
substantive operations still refuse. Fiat also remains explicit-only: use
`$fiat` only when you want the complete controlled delivery loop.

## Contribute

You do not need to understand the whole collective before helping. Useful
contributions include:

- trying one shipped operation on a real repository and preserving the first
  reproducible failure;
- adding a source adapter, historical specimen, protocol host, corpus rule, or
  checked example where a member states that coverage is missing;
- improving an explanation or example without weakening its evidence boundary;
- implementing one member's recorded next frontier and its tests;
- reviewing a proposed promise, refusal path, or recovery path from the point
  of view of someone who will depend on it.

Start with [How to help build the Shoggoth](./docs/how-to-help-shoggoth.md).
It offers routes for small documentation and specimen work as well as the
fully controlled Atlas/Fiat path.

The [Shoggoth Wave Atlas](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/)
draws one unblocked open issue for contributors who want the system to choose
the work. A checked bootstrap can allocate the issue and prepare a prompt:

[![OpenAI - ChatGPT web bootstrap](https://img.shields.io/badge/OpenAI-ChatGPT_web_bootstrap-10A37F?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/chatgpt)
[![Anthropic - Claude web bootstrap](https://img.shields.io/badge/Anthropic-Claude_web_bootstrap-D97757?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/claude)
[![Atlas - manual prompt](https://img.shields.io/badge/Atlas-Manual_prompt-3E68FF?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job)

<!-- harness-roster:begin -->
<!-- Generated by scripts/render_harness_roster.py from docs/harness-classification.json, recorded on darwin-arm64 on 2026-09-04 against c0524f0cd1288cc35316ae9acec6c7d2a6bd4272. Change the roster in scripts/probe_harnesses.py, re-run the probe, then re-run the renderer. Nothing between these markers is edited by hand, and the README carries no harness name outside them. -->

No local harness holds a checked one-click Atlas launcher. A probe on darwin-arm64 read every client below on 2026-09-04, and the roster states what it found rather than what anybody hoped for:

- Manual route: GitHub Copilot, Cursor, Gemini CLI, Windsurf, Cline.
- Unsupported: Roo Code.

Each harness carries the exact reason it stopped there in [the harness table](./docs/how-to-help-shoggoth.md#local-harnesses) and in [`docs/harness-classification.json`](./docs/harness-classification.json), which both surfaces are generated from.
<!-- harness-roster:end -->

The Atlas is one contribution route, not the front door to every task. Its web
links allocate a job and prepare a hand-off; they do not prove that a browser
chat can edit, sign, or publish a local repository change. Keep the chosen
local harness open for the whole Fiat run.

Not every issue earns a run. An issue body declares `Fiat-Required: 1` when the
work needs one and `Fiat-Required: 0` when one independent pull request will do,
and it disposes of every item it leaves for somebody else in a `carryover`
block. `hexctl init` reads both from a GitHub task issue and refuses a `0`
before it creates any branch, so an allocated job that turns out to be a
one-line fix becomes a pull request rather than a runbook.
[AGENTS.md](./AGENTS.md) states the shape and
[ADR-067](./docs/decisions/ADR-067-gate-a-run-on-what-its-issue-filed.md) states
why.

You are the external contributor, not Shoggoth. Keep your own Git author,
signing identity, and GitHub account. Shoggoth provenance supplements that
authorship; it never authorises use of a private Shoggoth identity. Fiat stores
verified local checkpoints after completed steps, but unfinished runs must not
be inferred from chat or moved casually between machines.

Fiat records whether a pushed commit's author address matches a GitHub account
and whether integration preserves that identity. If the address matches no
account, the receipt says so instead of guessing. The remaining publication
conditions are GitHub's rather than the repository's. A daily job rebuilds
[`CONTRIBUTORS.md`](./CONTRIBUTORS.md) and the thanks below from public history;
that record does not change GitHub's own contributor view or schedule.

The contributor guide and [Fiat in plain English](./docs/fiat-in-plain-english.md)
explain the hand-off, receipts, recovery, and completion conditions. The
printable guide is available as a [PDF](./docs/pdf/how-to-help-shoggoth.pdf).

## Repository map

```text
.claude-plugin/marketplace.json   one entry per plugin
.agents/plugins/marketplace.json  the same set, host-neutral
.agents/skills/promise-machine/   authored router; runtime published separately
├── PORTABLE.md                   isolated-install path and refusal boundary
└── scripts/verify_runtime.py     installed byte-manifest check
plugins/<name>/
├── .claude-plugin/plugin.json    host discovery metadata
├── .codex-plugin/plugin.json
├── AGENTS.md                     plugin runtime and selection contract
├── README.md                     human landing page
├── tests/
└── skills/<skill>/SKILL.md       canonical instructions
```

[`pyproject.toml`](./pyproject.toml) declares the supported Python minor, while
[`.python-version`](./.python-version) pins the exact interpreter used by every
Python-backed skill and repository check. [ADR-038](./docs/decisions/ADR-038-pin-the-python-suite-to-one-interpreter.md)
records the one-interpreter rule; [ADR-042](./docs/decisions/ADR-042-advance-the-python-suite-to-3-14.md)
records the current minor transition. Individual plugin pages list their other requirements.
Common ones include Git, GitHub CLI, Foundry, a Solidity compiler or container
runtime, and an archive Ethereum RPC endpoint for Lazarus capture. Verification
and replay paths are often offline even when capture is not.

## Identity and authority

“Shoggoth” may mean the member currently speaking or the collective as a whole;
context decides which. The [identity contract](./SHOGGOTH.md) records the exact
addressing, portrait, authorship, and host-provenance rules. A name never
activates a skill or widens anyone's authority.

The [Shoggoth Interceptor](https://github.com/laurenceday/shoggoth-interceptor)
is the same collective operating through an experimental external
problem-solving harness. It is an operating form, not another member.

## Licence

Wildcat Labs first-party work in this repository is licensed under
[Apache-2.0](./LICENSE). The vendored Pashov skills are excluded from that
grant and retain their upstream MIT licence and notices.

<!-- contributors:start -->

## Thanks

Thanks to @kethcode, @radup1337, @MunamWasi and @clawdina.

<!-- contributors:end -->
