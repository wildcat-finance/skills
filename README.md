<p align="center">
  <img src="./assets/characters/shoggoth.png" width="1200">
</p>

# The Shoggoth

The Shoggoth is the Wildcat Labs agent-and-skill collective. It is not one
general assistant wearing a list of names. Each member owns a particular job,
states what its evidence can support, and stops where another member's work
begins.

The current distribution contains 15 plugins, 24 first-party skills, four
Fiat worker agents, one portable router, and five untouched skills from the
vendored Pashov security suite. Together they preserve source material, rebuild
credit records, check economic and hook boundaries, capture historical chain
state, test grounded agents, optimise Solidity gas, shape usable prose, and
carry repository work through a receipted delivery.

Any reference to Shoggoth, including a shortened, altered, or affectionate form
of the name, may mean the member currently speaking or the collective as a
whole. Context decides which. The complete convention lives in the
[Shoggoth identity contract](./SHOGGOTH.md); wording alone never activates a
skill or widens anyone's authority.

The [Shoggoth Interceptor](https://github.com/laurenceday/shoggoth-interceptor)
is the same collective operating through an external problem-solving harness.
It is an operating form, not another member, and it remains experimental.

New here? Start with [A child or a golden retriever](./docs/a-child-or-a-golden-retriever.md),
a five-minute primer for the Shoggoth, the Interceptor, Hex, and Fiat. It
includes two infographics, a [short printable PDF](./docs/pdf/a-child-or-a-golden-retriever.pdf),
and a [one-page quick-start](./docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf).

To install the whole collective through the Agent Skills convention, select
the one dependency-closed router:

```bash
npx skills add wildcat-finance/skills --skill promise-machine
```

The router verifies its local runtime before it selects a specialist. See the
[installation guide](./INSTALL.md#local-agents) for the non-interactive Codex
command and the boundary of that package.

## So, You Want To Build God?

Ask the Atlas for a number. Pick your harness. Finish what you start.

The [Shoggoth Wave Atlas](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/)
draws one random open issue from the full pool whose recorded hard dependencies
are closed. You do not choose a Wave. Pick one tested bootstrap below; that
single click asks the Atlas for a job and opens a new chat with its number,
issue URL, install request and Fiat request filled in.

[![OpenAI - ChatGPT web bootstrap](https://img.shields.io/badge/OpenAI-ChatGPT_web_bootstrap-10A37F?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/chatgpt)
[![Anthropic - Claude web bootstrap](https://img.shields.io/badge/Anthropic-Claude_web_bootstrap-D97757?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/claude)
[![Atlas - manual prompt](https://img.shields.io/badge/Atlas-Manual_prompt-3E68FF?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job)

The friendly hand-off looks like: **Aye, here you go - #123.**

> [!WARNING]
> Fiat now keeps its run in a dedicated worktree with durable, verified state,
> so the same local run can be resumed and reconstructed after context loss.
> Keep using the worktree and state path the controller prints. Do not move an
> unfinished run between machines, infer progress from chat, or accept a reused
> worker handle whose visible issue, step, or role belongs to an older run.

This route is for an external human contributor, not Shoggoth. Keep your own
Git author, valid signing identity and GitHub account. The required Shoggoth
provenance trailers supplement that authorship; they do not authorise use of
Shoggoth's private key or account. Confirm that the coding environment can sign
and publish as you before `hexctl init`; otherwise move the Atlas prompt to a
suitable local harness before the run starts.

The ChatGPT and Claude links are the Atlas routes covered by the current
launcher tests. They allocate a job and prefill its prompt; they do not prove
that a browser chat can complete a local Fiat run. The prompt tells the chat to
stop before `hexctl init` when it cannot work in the repository, sign as the
human contributor and publish through that contributor's GitHub account. Open
the repository in the local coding harness that will retain the run worktree.
[Codex](./INSTALL.md#codex) and [Claude Code](./INSTALL.md#claude-code) have
native Wildcat marketplace packages. GitHub Copilot, Cursor, Gemini CLI and
Windsurf use the [manual route](./docs/how-to-help-shoggoth.md#the-secondary-manual-route):
open the repository, read `AGENTS.md`, then paste the exact Atlas prompt. They
are not presented as tested one-click Atlas launchers. Cline and Roo Code are
not listed as launch options because this repository has no checked Atlas
hand-off for them.

Fiat keeps the bounded run in order: study, runbook, implementation, audit,
prose, push and integration. Code that looks finished is not the endpoint. The
run is complete when the controller says its required steps and checks are
complete and the contribution is ready for the normal GitHub pull-request
path. The [contributor guide](./docs/how-to-help-shoggoth.md) and
[printable PDF](./docs/pdf/how-to-help-shoggoth.pdf) show that route. If the
result is merged with your human authorship intact, GitHub includes you in the
repository's contributor history.

Fiat now checks the first half of that sentence and records the answer. It
stores, for every commit it pushes, the GitHub account the commit was matched
to and a digest of the author address, and it refuses to record a run as
integrated unless the base still carries each of those identities. Two
conditions are GitHub's rather than the repository's. The commit author address
has to be one GitHub can match to your account, and the list itself is GitHub's
to compute and publish on its own schedule. A run whose author address matches
no account records that plainly instead of guessing.

That record is one source for the contributor list.
[CONTRIBUTORS.md](./CONTRIBUTORS.md) ranks the humans with resolved commits here
and the humans who author merged pull requests in
`wildcat-finance/shoggoth-wave-atlas`. Skills commits are the first ordering
key; merged pull requests across both repositories are the tie-break. The thanks
at the foot of this file name the same people by handle. A daily job regenerates
both from the two repositories' public history, so nobody has to remember to add
anyone and there is nothing to ask for. Runtime host identities, the Shoggoth's
own account and the repository owner are excluded by name, each with its reason
shown in the generator's output.

## What Is It?

The identity contract records the current roster as 25 members: 16 domain agents and
9 phase agents. The repository topology is 24 first-party skills and four Fiat
worker agents. Synkrisis belongs to the roster now, with all four of its
comparison operations delivered. Hexaemeron is the
delivery plugin, while the Promise Machine and its portable router govern how
the suite is selected and composed.

The collective works alongside the vendored
[Pashov security suite](https://github.com/pashov/skills). That suite remains
Pashov's work under its upstream MIT licence. Its five shipped skill surfaces
are X-Ray, Solidity Auditor, Fizz, Fizz Convert, and Fizz Sync. They are
included without being renamed, rewritten, governed, or relicensed by Wildcat
Labs.

## The Promise Machine

Every first-party skill is governed by the
[Promise Machine](./PROMISE_MACHINE.md). A promise says what a successful
operation actually establishes, names the evidence behind it, and states what
the result still does not prove. A handoff may narrow that evidence or add new
evidence; it may not silently strengthen the claim.

Missing, stale, or mismatched evidence blocks only the transition that depends
on it. Inspection, repair, rerun, rollback, and safe exit remain available.
The machine checks the contracts, identities, installation copies, host
manifests, evidence coverage, and first-party licence boundary. It does not
turn a passing structural check into proof that a domain claim is true.

## Meet the Shoggoth

### Evidence, credit, and protocol specialists

- [Alexandria](./plugins/alexandria) preserves heterogeneous lending captures
  by digest and exposes narrow, source-bound credit views. Tabularium consumes
  those preserved records; Alexandria does not interpret them into a canonical
  history.
- [Tabularium](./plugins/tabularium) maps preserved venue-native records into a
  reproducible credit-event release with explicit coverage and provenance.
  Probitas can use that release, but Tabularium does not judge a borrower.
- [Probitas](./plugins/probitas) builds a sourced borrowing and repayment
  dossier from addresses the subject declared. Unknowns stay unknown and a
  person still makes the underwriting decision.
- [Lazarus](./plugins/lazarus) captures and replays the finite historical
  Ethereum state and exact RPC evidence one application test needs. It does
  not turn receipts, logs, calls, or traces into proved state.
- [Ariadne](./plugins/ariadne) binds a released artefact digest to the evidence
  that actually supports it through inspectable in-toto statements and gates.
  It records coverage; it does not certify every claim in the artefact.
- [Lemma](./plugins/lemma) turns Solidity compiler input or Markdown trees into
  validated, source-linked JSONL chunks. Berean may use such a corpus, but
  Lemma stops before embedding, indexing, retrieval, or evaluation.
- [Berean](./plugins/berean) releases and evaluates a grounded protocol agent
  against pinned document bytes and preserved chain reads. It does not preserve
  chain state or prepare the source chunks itself.
- [Pandects](./plugins/pandects) supplies executable credit laws, each paired
  with a broken specimen it is proved to catch. Its laws can constrain a Janus
  hook review or a fuzz campaign; they are not a whole-protocol audit.
- [Janus](./plugins/janus) checks the effects a contract hook may observe and
  cause before and after its host action. It tests host-specific permission
  boundaries rather than treating ABI compatibility as safety.
- [Hermes](./plugins/hermes) changes Solidity gas use one named optimisation
  class at a time, keeping only measured wins that preserve behaviour, storage
  layout, selectors, and required arithmetic evidence.
- [Horos](./plugins/horos) writes and verifies evidence-backed repository
  boundaries and skeleton maps for oriented reading. Its exclusions reduce cost;
  they never apply during security review.
- [Synkrisis](./plugins/synkrisis) owns the boundary for comparing validated
  run observations across one declared cohort. It builds the checked cohort,
  classifying every declared run under an operator-declared policy, infers
  bounded findings over it from a digest-bound rule catalogue, renders the
  fixed-template report, and verifies that all three recompute from the
  original inputs. A finding suggests one named owner and authorises no work.
- [Sapheneia](./plugins/sapheneia) shapes the collective's own replies and
  bounded audit records, issues, or comments for AuDHD readers without changing
  their protected evidence.
- [Brevitas](./plugins/brevitas) constrains the length and structure of
  engineering prose after the wording masks run, while preserving the evidence
  that controls a decision.

### Delivery controller and workers

[Hexaemeron](./plugins/hexaemeron) is the delivery plugin. Its controller and
workers are separate entities with separate authority:

- [Fiat](./plugins/hexaemeron/skills/fiat) is the explicit-only controller. It
  owns the dedicated worktree, durable state, receipt order, stacked pull
  requests, audit rounds, signed integration, and final report.
- **Surveyor** receives one source-bound study packet. It researches the target
  and writes the study; it cannot receipt the phase or steer the controller.
- **Mason** receives one exact runbook step and branch pair. It implements and
  tests that step; it cannot push, open a pull request, merge, or alter Fiat.
- **Warden** receives one exact audit-round packet. It runs the applicable
  security suite, preserves the audit record, fixes findings, and reports an
  Elenchus verdict; it cannot receipt its own round.
- **Scribe** receives the bounded prose diff and pull-request draft. It runs
  Imprimatur, applies Vulgate without changing content, reruns Imprimatur, and
  reports the files and skills used; it cannot invent an issue or publish.

Fiat can execute these packets inline when isolated workers are unavailable.
The packet and receipted artefacts remain the authority, never chat history.

### Phase disciplines and prose masks

- [Protasis](./plugins/hexaemeron/skills/protasis) decides whether a study and
  runbook are complete enough to build from. Fiat owns their receipts; Protasis
  owns their content contract.
- [Phylax](./plugins/hexaemeron/skills/phylax) hardens off-chain boundaries:
  external data, subprocesses, URLs, secrets, dependencies, paths, and model
  output. Solidity review stays with the security suite.
- [Ephoros](./plugins/hexaemeron/skills/ephoros) decides what unattended work
  must emit so an operator can explain it later: structured events, bounded
  metrics, correlation, traces, and useful alerts.
- [Metron](./plugins/hexaemeron/skills/metron) governs performance outside
  Solidity gas: baseline, one change, the same measurement again, then keep or
  revert. Hermes owns gas.
- [Elenchus](./plugins/hexaemeron/skills/elenchus) starts from a failure already
  in hand, reduces it to its cause, fixes that cause, and leaves a guard that
  fails without the fix.
- [Hypomnema](./plugins/hexaemeron/skills/hypomnema) decides what must be
  recorded and where it belongs: an ADR, an explanation of why, a runbook, an
  interface note, or a pointer to the one standing record.
- [Imprimatur](./plugins/hexaemeron/skills/imprimatur) is the executable prose
  gate for banned AI tells, unsupported terms of art, and repeated structural
  formulae. It diagnoses; it does not perform the rewrite.
- [Vulgate](./plugins/hexaemeron/skills/vulgate) is the content-preserving voice
  mask. It rewrites into a plain human register while holding facts,
  commitments, caveats, and links constant.
- [Kronos](./plugins/hexaemeron/skills/kronos) ranks eligible held frontier jobs
  and, only when explicitly asked, dispatches the highest unparked one through
  Fiat until the authorised field is exhausted. It never implements the job
  itself.

### Upstream security siblings

Hexaemeron also carries the untouched Pashov suite. **X-Ray** maps a Solidity
repository before audit; **Solidity Auditor** reviews its contracts; **Fizz**
builds a stateful fuzz harness; **Fizz Convert** turns recorded English
properties into assertions; and **Fizz Sync** reconciles that harness after the
source changes. Warden invokes the applicable upstream skills by path. Their
instructions, ownership, and MIT licence remain Pashov's.

## How the members fit together

The common credit path is Alexandria to Tabularium to Probitas: preserve,
interpret, then assemble a bounded dossier. Lemma prepares source-linked
material for a system such as Berean to evaluate. Lazarus preserves a test's
historical chain boundary, and Ariadne can bind the resulting release to that
evidence. Berean produces grounded-agent releases; Ariadne binds them without
rerunning the agent or regrading its evaluation. Pandects supplies economic
laws, Janus checks hook effects against a host boundary, and Hermes handles
measured gas changes.

Synkrisis compares validated observations from several completed runs after a
person declares them comparable. All four of its operations are operational:
it writes a checked cohort, bounded findings over it, a fixed-template report,
and a verification that recomputes all three from the original inputs. It
cannot steer Fiat. Ephoros, Metron, Elenchus, Protasis, Phylax, Horos, or
human review remain responsible for any later investigation or decision.

For delivery, Protasis shapes the study and runbook before Mason builds a step.
Phylax, Ephoros, and Metron govern its off-chain boundary, observable behaviour,
and non-gas performance. Warden applies the relevant security suite; Elenchus
handles failures and guards; Hypomnema decides what the work must record;
Imprimatur, Vulgate, and Brevitas shape the final prose. Fiat alone advances the
receipted loop. Kronos may choose which held frontier enters Fiat, but only on
an explicit Kronos request.

The Promise Machine is the shared law across every hand-off. A sibling receives
the evidence that exists, not a stronger story about it.

Installation, host-specific invocation, and publishing instructions live in
[INSTALL.md](./INSTALL.md).

## Use

### Requirements

Requirements apply only to the skills and operations named in the last column.
Checked-in examples and verification paths may need less.

[`pyproject.toml`](./pyproject.toml) declares the supported CPython minor, and
[`.python-version`](./.python-version) is the single source for the exact patch.
Run every Python-backed skill, repository check, and documented command with
that pin. [ADR-038](./docs/decisions/ADR-038-pin-the-python-suite-to-one-interpreter.md)
records the one-interpreter boundary, and
[ADR-042](./docs/decisions/ADR-042-advance-the-python-suite-to-3-14.md) records
the current minor transition.

| Requirement | Skills | When it is needed |
| --- | --- | --- |
| [Pinned CPython](./.python-version) | Every Python-backed skill and repository check | All supported Python execution; the minor contract lives in `pyproject.toml` |
| Git | Hermes, Hexaemeron | Worktree, diff, and receipt checks |
| GitHub CLI (`gh`) | Hexaemeron | Issue, pull request, and integration phases |
| Foundry | Hermes, Janus, Pandects; Ariadne and Hexaemeron when working with Foundry projects | Solidity builds, tests, measurements, and captures |
| `solc`, Docker, or Podman | Lemma | Solidity chunking only |
| Archive Ethereum RPC | Lazarus | Capture only; verification and replay are offline |
| No local runtime | Sapheneia | It changes the assistant's interaction rather than running a tool |

### Requests

Each line below is a complete starting request for one first-party skill.

```text
Use $alexandria to preserve this lending-data capture, derive its reviewed credit rows, and query the declared address without hiding coverage gaps.
Use $ariadne to capture this release in an evidence statement, run its gates, and report its signature state without checking signatures.
Use $berean to verify this release's citations, chain readings, and promotion record against its pinned corpus.
Use $brevitas to shorten this engineering review without dropping addresses, hashes, file-and-line references, numbers, counterexamples, or reproduction steps.
Use $hermes to optimise gas in this repository. Name the corpus rule each candidate implements, work one optimisation class at a time, and keep the complete verification record.
Use $fiat to take this issue from study to a merged delivery, one receipted phase at a time.
Use $kronos to rank the held frontier jobs and run the best eligible one through Fiat until none remain.
Use $protasis to decide whether this study and runbook are ready to build from.
Use $elenchus to find the cause of this failure, fix it, and leave a test that fails without the fix.
Use $phylax to harden the off-chain inputs, subprocesses, network calls, secrets, dependencies, and model-output boundary of this change.
Use $ephoros to decide which events, metrics, traces, and alerts this step must emit so an operator can explain it later.
Use $metron to measure this slow path, change one thing, measure it the same way, and keep or revert the change on the result.
Use $hypomnema to record this decision, its alternatives, and its consequences where the next person will find them.
Use $imprimatur to check this draft for banned wording and unsupported technical claims.
Use $vulgate to rewrite this draft in plain human language without changing what it says.
Use $horos to create or check an evidence-backed reading boundary for this repository; do not apply it during security review.
Use $janus to check this hook against a conformance manifest for what it may observe and change around a host action.
Use $lemma to turn this Solidity compiler input or Markdown tree into validated, source-linked JSONL chunks.
Use $lazarus to capture this finite historical fixture, verify its proof-backed state, and replay only its exact requests.
Use $pandects to check this credit protocol against the executable laws in the corpus.
Use $probitas to build a sourced dossier on this counterparty from the addresses they declared.
Use $sapheneia to shape your replies for an AuDHD reader throughout this task.
Use $synkrisis to build one checked cohort from declared run observations, diagnose it against the committed rule catalogue, and verify the report recomputes; do not treat a finding as a cause or an authority to act.
Use $tabularium to build or verify a reproducible release of sourced credit events without hiding coverage gaps.
```

Fiat remains explicit-only. Describing a delivery task does not start the
controller unless the user names Fiat or Hexaemeron and asks it to run.
The Pashov suite keeps its upstream invocation and operating instructions.

## Repository layout

```text
.claude-plugin/marketplace.json   one entry per plugin
.agents/plugins/marketplace.json  the same set, host-neutral
.agents/skills/promise-machine/   the sole host-neutral suite router
├── PORTABLE.md                   isolated-install path and refusal boundary
├── scripts/verify_runtime.py     installed byte-manifest check
└── runtime/                      generated dependency-closed fallback
plugins/<name>/
├── .claude-plugin/plugin.json    host manifests; discovery and installation only
├── .codex-plugin/plugin.json
├── AGENTS.md                     runtime contract and selection table
├── LICENSE                       first-party plugin licence
├── README.md                     landing page
├── tests/
└── skills/<skill>/SKILL.md       canonical instructions, one directory per skill
```

Hexaemeron also carries the Pashov suite as a vendored, upstream-owned set.
Those skill directories keep their own MIT `LICENSE` and `NOTICE.md`; the
first-party Apache licence does not replace or govern them.

Codex, Claude Code, and portable agents load the same canonical skill bytes.
Host manifests handle plugin discovery. A copy-mode Agent Skills install uses
the router's generated, manifested fallback because an installer copies only
the selected directory. The target repository's own instructions and the
active skill's checks still apply.

## Wildcat Commons

The [Wildcat Commons](https://wildcat.finance) is in the process of creating an
accessible, permanent repository of credit-related data. This suite supplies
the tools needed to preserve original inputs, create reproducible credit-event
records, state executable credit laws, preserve historical test fixtures,
assemble evidence-bounded dossiers, evaluate source-grounded assistants, test
Wildcat hook boundaries, and bind releases to their evidence.

Synkrisis holds a separate boundary for comparing validated observations
from several agent runs. Its current release lands the checked cohort, the
bounded diagnosis over it, the fixed-template report and the verification that
recomputes all three; the measured work budget is its one held runbook step.

The credit and evidence tools named here have all been produced:
[Alexandria](./plugins/alexandria),
[Tabularium](./plugins/tabularium), [Pandects](./plugins/pandects),
[Lazarus](./plugins/lazarus), [Probitas](./plugins/probitas),
[Berean](./plugins/berean), [Janus](./plugins/janus), and
[Ariadne](./plugins/ariadne). Their individual boundaries still apply; the
Commons description does not turn a recorded source into verified truth or a
dossier into a lending verdict.

## Licence

Wildcat Labs first-party work in this repository is licensed under
[Apache-2.0](./LICENSE). The vendored Pashov skill set is explicitly excluded
and remains under its upstream MIT licence and notices.

<!-- contributors:start -->

## Thanks

Thanks to @kethcode, @radup1337, @MunamWasi and @clawdina.

<!-- contributors:end -->
