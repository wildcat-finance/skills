---
name: promise-machine
description: Route a Wildcat Labs request to the one canonical first-party or vendored skill that owns it, preserving the Promise Machine evidence boundary and every named sibling hand-off.
---

<p align="center">
  <img src="../../../assets/characters/promise-machine.png" width="1200">
</p>

# Promise Machine router

This is the host-neutral front door to Wildcat Labs Skills, the Shoggoth. It
is a switchboard, not another member: it has no behavioural version, performs
no specialist work, and owns no domain promise.

Choose the runtime before routing. In a full source checkout,
`../../../PROMISE_MACHINE.md` identifies `promise-machine/v1` and
`../../../plugins/` holds all sixteen plugin contracts; read the [root runtime
contract](../../../AGENTS.md) first. Otherwise this is an isolated Agent Skills
install: read `PORTABLE.md`, verify its local runtime, and use the installed-path
substitution it defines. A target repository's unrelated `AGENTS.md` never
counts as the suite contract. Do not select a canonical skill until one of
these two runtime paths has loaded the same law and the selected plugin
contract.

The router sees the complete collective. Fifteen first-party specialists live
in their own plugins. Hexaemeron contains Fiat, Kronos, six engineering phase
disciplines, two prose masks, four Fiat worker briefs, and the untouched Pashov
security suite. Together the distribution exposes 25 governed first-party
skills. The worker briefs are packets Fiat may delegate; they are not
canonical skills a user selects through this router.

## Select one runtime contract

Match the request to the narrowest row, read that runtime contract in full and
use its selection table to load exactly one canonical `SKILL.md`. Load another
canonical skill only when the selected workflow requires a named handoff.

| Request | Runtime contract | Canonical selection |
| --- | --- | --- |
| Preserve lending inputs or derive a reviewed credit view | [Alexandria](../../../plugins/alexandria/AGENTS.md) | `alexandria` |
| Bind a release digest to its evidence record | [Ariadne](../../../plugins/ariadne/AGENTS.md) | `ariadne` |
| Preserve audit findings and the changes that answered them | [Anamnesis](../../../plugins/anamnesis/AGENTS.md) | `anamnesis` |
| Verify a protocol agent against pinned corpora and chain reads | [Berean](../../../plugins/berean/AGENTS.md) | `berean` |
| Constrain the volume and structure of engineering prose | [Brevitas](../../../plugins/brevitas/AGENTS.md) | `brevitas` |
| Inspect or work on the planned frontend coverage boundary; substantive operations currently refuse | [Dokimasia](../../../plugins/dokimasia/AGENTS.md) | `dokimasia` |
| Measure one Solidity gas-optimisation class | [Hermes](../../../plugins/hermes/AGENTS.md) | `hermes` |
| Validate a Homologia manifest and evidence-classed expected integers, or inspect the later contract-to-mirror boundary; mirror execution and verdicts currently refuse | [Homologia](../../../plugins/homologia/AGENTS.md) | `homologia` |
| Classify evidenced reading sinks | [Horos](../../../plugins/horos/AGENTS.md) | `horos` |
| Check hook effects around a host action | [Janus](../../../plugins/janus/AGENTS.md) | `janus` |
| Preserve finite historical Ethereum state and exact RPC traffic | [Lazarus](../../../plugins/lazarus/AGENTS.md) | `lazarus` |
| Produce source-linked Solidity or Markdown chunks | [Lemma](../../../plugins/lemma/AGENTS.md) | `lemma` |
| Apply executable credit laws | [Pandects](../../../plugins/pandects/AGENTS.md) | `pandects` |
| Build a declared-address counterparty dossier | [Probitas](../../../plugins/probitas/AGENTS.md) | `probitas` |
| Shape the agent's own replies for an AuDHD reader, or shape durable agent-authored audit records and GitHub issue titles, bodies and comments | [Sapheneia](../../../plugins/sapheneia/AGENTS.md) | `sapheneia` |
| Compare validated run observations across runs, or inspect the cross-run comparison boundary | [Synkrisis](../../../plugins/synkrisis/AGENTS.md) | `synkrisis` |
| Build a venue-qualified credit-event release | [Tabularium](../../../plugins/tabularium/AGENTS.md) | `tabularium` |

Hexaemeron is one plugin with several distinct owners. Use the same runtime
contract, then select the named skill below.

| Request | Runtime contract | Canonical selection |
| --- | --- | --- |
| Run or resume the explicit receipted delivery loop | [Hexaemeron](../../../plugins/hexaemeron/AGENTS.md) | `fiat` |
| Rank eligible held frontier jobs, optionally repeating complete Fiat runs | Hexaemeron | `kronos` |
| Hold a study or runbook to its pre-build content contract | Hexaemeron | `protasis` |
| Work a reproduced failure to its cause and guard the fix | Hexaemeron | `elenchus` |
| Harden off-chain inputs, commands, fetches, secrets, dependencies, paths, or model output | Hexaemeron | `phylax` |
| Design events, metrics, correlation, traces, or alerts for unattended work | Hexaemeron | `ephoros` |
| Measure non-gas performance before and after one change | Hexaemeron | `metron` |
| Decide what explanation or decision record belongs where | Hexaemeron | `hypomnema` |
| Lint prose for banned AI tells and unsupported terms of art | Hexaemeron | `imprimatur` |
| Rewrite prose into a plain human register without changing its content | Hexaemeron | `vulgate` |
| Run audit-readiness, Solidity review, or stateful fuzzing | Hexaemeron | The named upstream Pashov skill |

Fiat may hand source-bound packets to Surveyor for one study, Mason for one
implementation step, Warden for one audit round, or Scribe for one prose pass.
They return evidence to Fiat; they never select themselves or receipt their own
work.

Synkrisis is outside Fiat's controller loop. Its four delivered operations
build a checked cohort, infer bounded findings, render a fixed report, and
verify the path from the original inputs. It cannot file an issue, mutate a
repository, or dispatch a Fiat run. A comparison result still requires a
person to choose the next owner and action.

## Preserve the selected promise

The canonical skill and its runtime contract are authoritative. Invocation
aliases change only how a request reaches that skill. They never strengthen an
evidence class, erase a refusal or recovery path, widen scope, or authorise a
more consequential transition.

If no row matches, stop at inspection and explain the uncovered boundary. Do
not improvise a new suite capability, collapse two siblings into a generalist,
or treat this router as permission to run Fiat, Kronos, a worker, or any
external action.

If two rows both match, name both rows and the boundary sentence that separates
them before selecting either. Select one row only when its boundary sentence
excludes what the other row claims. When neither sentence excludes the other,
stop at inspection and report which two rows matched and which sentence you
read. Never select both rows, widen one row until it covers the request, or
fall back to a third row that covers neither. A boundary sentence is one
sentence of the marketplace boundaries in the root runtime contract, or one
Request predicate from a table above. Two adjacent table rows are not one
sentence, and neither are two list items.
