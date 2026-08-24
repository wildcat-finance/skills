<p align="center">
  <img src="./assets/characters/shoggoth.png" width="1200">
</p>

# The Shoggoth

The Shoggoth is a collective of specialist assistants built by
[Wildcat Labs](https://wildcat.finance) to help crypto developers at both the
protocol and frontend level. Its members preserve evidence, test contracts,
measure gas, investigate failures, shape documentation, and carry engineering
work through a controlled delivery loop.

[Hexaemeron](./plugins/hexaemeron) has proved to be an effective engineer on
work that can be reduced to explicit steps, tests, audits, and receipts. That is
a claim about recorded repository work, not a claim that it is infallible or
ready to operate without supervision.

The illustrated [contributor guide](./docs/how-to-help-shoggoth.md), also
available as a [PDF](./docs/pdf/how-to-help-shoggoth.pdf), explains how a
Hexaemeron run moves from a named issue through study, implementation,
independent review, and a pull request with evidence a maintainer can inspect.
You do not need to understand the whole collective before taking one bounded
job through that process.

The [Shoggoth Interceptor](https://github.com/laurenceday/shoggoth-interceptor)
puts the same collective into a harness for tearing through issue queues in
external repositories. It is experimental and is not production-ready.

The name Shoggoth can refer to one agent or the collective. The full convention
lives in the [Shoggoth identity contract](./SHOGGOTH.md).

## So, You Want To Build God?

The [Shoggoth Wave Atlas](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/)
offers one open issue at a time: any issue in a wave whose recorded hard
dependencies are all closed. Choose an assistant below. The button asks the
Atlas for one issue, then opens a new chat with its number and a
checkpoint-aware install and Fiat request filled in. Read it, then send it.

[![OpenAI · ChatGPT](https://img.shields.io/badge/OpenAI-ChatGPT-10A37F?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/chatgpt)
[![Anthropic · Claude](https://img.shields.io/badge/Anthropic-Claude-D97757?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/claude)

You do not need to invent the work or choose among the whole backlog. The Atlas
already holds the list and offers an eligible issue. What the project needs
from you is the inference and judgement to understand that bounded problem and
move it forward at one checkpoint. You do not have to carry the whole issue to
the end. The job may be a missing regression test, an input a checker cannot
yet handle, a weak handoff, or support for another environment. Each accepted
piece makes the shared system more reliable, useful, or flexible for the next
developer.

The intended model lets you stop at a clean checkpoint and lets somebody else
resume from its receipts. Durable parking of the run's `.hexaemeron` state is
not finished yet, so reliable handover remains work in progress. The
[contributor guide](./docs/how-to-help-shoggoth.md) and its
[printable PDF](./docs/pdf/how-to-help-shoggoth.pdf) describe the route that
works today. If a completed job is merged with your authorship intact, GitHub
records you as a contributor, and a weekly job adds you to
[CONTRIBUTORS.md](./CONTRIBUTORS.md) and to the thanks at the foot of this file.
One condition sits outside this repository's control: a merge that discards
commit authorship, or a commit whose author email is linked to no account,
leaves nothing for either list to find.

## What Is It?

At the last recorded count, the Shoggoth had 24 members: 15 domain agents and
9 phase agents. They are independent specialists with separate jobs, evidence,
and refusal rules, but they can hand work to one another without pretending the
next agent knows more than the previous one established.

The collective works alongside the vendored
[Pashov security suite](https://github.com/pashov/skills). That suite remains
Pashov's work under its upstream MIT licence. It is included without being
renamed, governed, or relicensed by Wildcat Labs.

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

### Alexandria

[Alexandria](./plugins/alexandria) keeps original lending and credit data intact
and produces a smaller view whose sources and mapping choices can be checked.
It is the archive desk: it preserves what arrived before anybody interprets it.

### Ariadne

[Ariadne](./plugins/ariadne) ties a released file to the evidence behind it in
a receipt another person can inspect. It records what was built and checked;
it does not claim that every statement inside the file is true.

### Berean

[Berean](./plugins/berean) tests a protocol research assistant against fixed
source material and recorded questions. It checks whether citations point to
the claimed bytes and whether live values belong to the stated chain and block.

### Brevitas

[Brevitas](./plugins/brevitas) keeps engineering writing short enough to use
without throwing away addresses, numbers, counterexamples, reproduction steps,
or other evidence that changes the decision.

### Hermes

[Hermes](./plugins/hermes) reduces the gas used by Solidity code one kind of
change at a time. It measures the saving, reruns behaviour checks, and rejects
an optimisation when the proof of safety or improvement does not hold.

### Hexaemeron

[Hexaemeron](./plugins/hexaemeron) turns a request into a study, a runbook, an
implementation, repeated independent audits, clear prose, and a controlled
integration. Its phase agents each own one part of that process, while Fiat
keeps the receipts and decides what may happen next.

### Horos

[Horos](./plugins/horos) identifies generated files, vendored trees, large data
blobs, and other material an agent can usually leave unread. Every exclusion
needs evidence, and no exclusion is allowed during security review.

### Janus

[Janus](./plugins/janus) checks what a smart-contract hook is allowed to see or
change before and after a host action. It tests the real effects against a
written permission boundary instead of assuming that a matching interface is
safe.

### Lemma

[Lemma](./plugins/lemma) divides Solidity compiler input or Markdown documents
into source-linked JSONL records. Each record keeps quotation text separate
from text prepared for a model or search system.

### Lazarus

[Lazarus](./plugins/lazarus) preserves the finite slice of historical Ethereum
state and RPC traffic needed by one application test. It can verify and replay
that fixture later without quietly falling back to a live endpoint.

### Pandects

[Pandects](./plugins/pandects) turns important credit-accounting rules into
executable Solidity checks. Each rule comes with a deliberately broken example
that proves the test catches the failure it claims to catch.

### Probitas

[Probitas](./plugins/probitas) assembles a sourced picture of a counterparty's
borrowing and repayment history from addresses they declared. Gaps remain
visible, and the result is evidence for a human decision rather than a verdict.

### Sapheneia

[Sapheneia](./plugins/sapheneia) shapes an assistant's replies for an AuDHD
reader. It keeps the current action, boundaries, evidence, unknowns, and next
step visible across a long task without changing the underlying facts.

### Tabularium

[Tabularium](./plugins/tabularium) turns preserved source records into a
rebuildable history of credit events. It keeps the source, mapping, coverage,
and gaps beside the output so somebody else can reproduce it later.

## How the members fit together

The names are job boundaries, not personalities pasted onto the same general
assistant. Alexandria preserves source material; Tabularium interprets it;
Probitas uses it in a bounded dossier. Lemma prepares source-linked chunks;
Berean evaluates an assistant that uses a pinned corpus. Lazarus preserves the
historical state a test needs; Ariadne binds a finished release to its evidence.
Pandects supplies accounting laws, Janus checks hook effects, and Hermes changes
gas only against measurements and behavioural evidence.

Hexaemeron coordinates delivery but does not absorb those jobs. It hands a
task to the relevant specialist and records what came back. The Promise Machine
is the shared rulebook that prevents any handoff from becoming an excuse to
claim more.

Installation, host-specific invocation, and publishing instructions live in
[INSTALL.md](./INSTALL.md).

## Use

### Requirements

Requirements apply only to the skills and operations named in the last column.
Checked-in examples and verification paths may need less.

| Requirement | Skills | When it is needed |
| --- | --- | --- |
| Python 3 | Alexandria, Ariadne, Brevitas, Hermes, Hexaemeron, Horos, Janus, Pandects | Their standard-library tools and checks |
| Python 3.9 or later | Berean, Probitas, Tabularium | Their release, dossier, and verification tools |
| Python 3.10 or later | Lemma | All Lemma commands |
| Python 3.11 or later plus its pinned packages | Lazarus | Capture, verification, replay, and release |
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

Codex, Claude Code, and portable agents load the same canonical skill
directories. Host manifests handle discovery and installation only. The target
repository's own instructions and the active skill's checks still apply.

## Wildcat Commons

The [Wildcat Commons](https://wildcat.finance) is in the process of creating an
accessible, permanent repository of credit-related data. This suite supplies
the tools needed to preserve original inputs, create reproducible credit-event
records, state executable credit laws, preserve historical test fixtures,
assemble evidence-bounded dossiers, evaluate source-grounded assistants, test
Wildcat hook boundaries, and bind releases to their evidence.

Those tools have all been produced: [Alexandria](./plugins/alexandria),
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

Thanks to @kethcode and @radup1337.

<!-- contributors:end -->
