<p align="center">
  <img src="./assets/characters/hexaemeron-overseer.png" width="1200">
</p>

# Hexaemeron runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Hexaemeron.** Fiat controls the explicit, receipted delivery; Surveyor, Mason, Warden and Scribe execute source-bound packets; six phase disciplines and two prose masks keep their own contracts; and the Pashov security suite remains upstream-owned. Use Hermes for Solidity gas, Pandects for credit laws, and Lemma for source-linked chunks. Synkrisis is the separate cross-run comparison boundary, delivered through verification; it cannot steer Fiat or a worker packet. **Current frontier:** load_state validates the version-1 state container spine in deterministic order before any command traverses it, with path-and-kind diagnostics shared by verify and mutations; delegated task identities can still expose an earlier issue when a collaboration handle is reused.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Hexaemeron contains several Agent Skills. Select from this table, then read the
chosen `SKILL.md` in full. Do not start `fiat` merely because another
Hexaemeron skill matches a task.

| Skill | Canonical instructions | Select when |
| --- | --- | --- |
| `fiat` | `skills/fiat/SKILL.md` | The user explicitly asks to start, resume, or report a Hexaemeron delivery run |
| `fizz` | `skills/fizz/SKILL.md` | Generate a stateful Solidity fuzz suite |
| `fizz-convert` | `skills/fizz/skills/fizz-convert/SKILL.md` | Turn pending `PROPERTIES.md` entries into Solidity assertions |
| `fizz-sync` | `skills/fizz/skills/fizz-sync/SKILL.md` | Reconcile an existing Fizz harness with changed source |
| `x-ray` | `skills/x-ray/SKILL.md` | Prepare a Solidity protocol for audit |
| `solidity-auditor` | `skills/solidity-auditor/SKILL.md` | Audit Solidity source for security findings |
| `imprimatur` | `skills/imprimatur/SKILL.md` | Lint shipped prose against the banned lexicon |
| `vulgate` | `skills/vulgate/SKILL.md` | Rewrite prose in a plain human register without changing its content |
| `kronos` | `skills/kronos/SKILL.md` | Repeatedly rank eligible skill frontiers and send the best held job through Fiat |
| `protasis` | `skills/protasis/SKILL.md` | Decide whether a study or runbook says enough to build from, before implementation starts |
| `elenchus` | `skills/elenchus/SKILL.md` | Find the cause of a failure that has already happened, and guard it with a test |
| `phylax` | `skills/phylax/SKILL.md` | Harden the off-chain surface: external input, subprocesses, fetched hosts, secrets, dependencies and model output |
| `ephoros` | `skills/ephoros/SKILL.md` | Choose the events, metrics, traces and alerts a step must emit to stay diagnosable |
| `metron` | `skills/metron/SKILL.md` | Baseline something slow, change one thing, re-measure, and keep or revert on the numbers |
| `hypomnema` | `skills/hypomnema/SKILL.md` | Record the reason behind a decision, and put each kind of record where it will be found |

## Vendored Promise Machine overlays

Before selecting `fizz`, `fizz-convert`, `fizz-sync`, `x-ray` or
`solidity-auditor`, read its declaration in [PROMISES.md](PROMISES.md) and
recompute the SHA-256 of the exact canonical `SKILL.md`. The path and digest
must match before the Wildcat promise is available. A mismatch blocks the
overlay and requires review of the upstream change; it never authorises an
edit to the vendored instruction.

From this distribution repository, check the complete binding with:

```bash
python3 scripts/promise_machine.py check --only contracts,overlays
```

A standalone installation without the repository checker performs the same
local path and digest comparison before it relies on an overlay. The overlay
states what the Wildcat suite accepts from the vendored operation; the
unchanged upstream file still controls how that operation runs.

All ten first-party skill directories in this plugin carry an `EVOLUTION.md`
ledger governed by `skills/VERSIONING.md`: Fiat, Kronos, Protasis, Elenchus,
Phylax, Ephoros, Metron, Hypomnema, Imprimatur, and Vulgate. Read the selected
skill's ledger before proposing a frontier run. A `mature` frontier is a hard
stop unless a maintainer has recorded an evidenced epoch reopening. Kronos is
terminal by design and excludes itself from its candidate set.

Each of those directories also carries a `DEMONSTRATION.md` governed by
`skills/DEMONSTRATIONS.md`. That is a separate lane with its own version, its
own held job, and its own digest: it records what the skill can show over
inputs a reader can check, never what the skill can do. Do not change an
`EVOLUTION.md` because a demonstration improved, and do not change a
`DEMONSTRATION.md` because behaviour advanced. One run may advance both, on
each lane's own evidence. Check the lane with
`python3 scripts/demonstrations.py check --root .`, and rank it read-only with
`python3 scripts/demonstrations.py frontier --root . --lane demo --dry-run`.

Surveyor, Mason, Warden, and Scribe are Fiat worker prompts under `agents/`,
not separately selectable skills. They execute the exact source-bound packet
Fiat supplies and return evidence to the controller without writing receipts.

## Translate tool names by capability

Some canonical skills were written for hosts that name their tools. A local
agent must map those names to equivalent capabilities:

| Instruction term | Required capability | Preserve |
| --- | --- | --- |
| `Read` | Read the named file completely or at the stated range | Named range and byte content |
| `Write` or `Edit` | Create or patch the named file | Intended path and patch scope |
| `Bash` | Execute the command in a shell and inspect its exit status | Argument order and exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern | Pattern and matched paths |
| `ToolSearch` | Inspect the runtime's available tools before choosing one | Available set and selection reason |
| `AskUserQuestion` | Ask the stated question through structured UI or concise text | Literal question and answer |
| `TodoWrite` | Maintain a durable plan with the same states and transitions | Step text and status |
| `Agent` or `Task` | Run the supplied role prompt in an isolated agent context | Role prompt and isolation boundary |
| background or parallel calls | Start independent work concurrently and wait at the named barrier | Arguments and wait barrier |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, wait barriers, output files, and stop conditions when
using an equivalent local tool.

If the runtime cannot select the named model family, use its configured model
and say that the requested family was unavailable. Omit unsupported model
arguments. Never claim that Sonnet, Opus, or another model ran when it did not.

If the runtime has no subagent facility, run each supplied role prompt
separately and save each raw result before synthesis. Keep roles separate and
finish every role named by the skill before crossing its wait barrier. Stop
when the requested workflow depends on isolation that the runtime cannot
preserve.

## Resolve placeholders

- `$SKILL_DIR` and `{SKILL_PATH}` mean the directory containing the active
  `SKILL.md`, unless that file defines them differently.
- `$PLUGIN_ROOT` means this `plugins/hexaemeron/` directory.
- `{PROJECT_ROOT}` means the user's target repository, not this plugin
  directory.
- `{SUITE_DIR}` and `{META_DIR}` are relative to `{PROJECT_ROOT}` unless the
  user supplied absolute paths.
- Names such as `hexaemeron:fizz` and `/hexaemeron:fiat` are logical skill
  aliases. Load the local canonical path from the table above.
- Fiat's controller path is relative to the exact active Fiat instruction
  file, never to `{PROJECT_ROOT}` or a GitHub URL.

## Side effects and truthfulness

Read the target repository's instructions before writing. Ask for any approval
the runtime or repository requires. Preserve every fail-closed check in the
canonical skill. If a command, audit role, lint, test, issue write, or push did
not happen, state that plainly and do not create its receipt.
Fiat directives carry source-bound delegation packets. Its commit-bearing
receipts require locally verified signatures and exact provenance trailers;
pushed ranges and GitHub merge SHAs also require GitHub `verified: true` with
`reason: valid`. Never copy raw signature material into state, ledgers, or
reports.
Every Fiat audit round declares `--audit-filter sapheneia:sapheneia`; this is a
checked operator declaration, not proof of the semantic pass. A bound task
issue's closing comment follows the repository's Sapheneia, Imprimatur,
Vulgate, Imprimatur order, is posted verbatim, and is read back before closure
is reported.
