# Instructions for local agents

This repository distributes agent skills. Do not treat a skill as active merely
because its files are present in context. Match the user's request through the
single portable router at `.agents/skills/promise-machine/SKILL.md`, then read
the selected plugin runtime contract and the one canonical `SKILL.md` it names.

## Collective identity

Before interpreting any reference to Shoggoth, including a shortened, altered,
or affectionate form of the name, read the shared
[Shoggoth collective identity](SHOGGOTH.md). That language affects how people
address the agents and skills. It does not activate a skill, grant authority,
or weaken the Promise Machine and target-repository instructions.

## Promise Machine contract

Before selecting or running a skill, read the suite-wide
[Promise Machine contract](PROMISE_MACHINE.md). Its identity is
`promise-machine/v1`. Each result authorises only the transition declared by
its canonical skill; missing, stale or insufficient evidence blocks that
dependent transition while leaving inspection, repair, rerun and safe exit
available.

The root law is authored once. Plugin-local `PROMISE_MACHINE.md` files are
generated installation copies and must remain byte-identical to it.

## Marketplace boundaries

The fifteen plugins form one marketplace, not fifteen competing descriptions
of the same job. Alexandria preserves lending inputs; Tabularium interprets
preserved venue records; Probitas assembles a counterparty dossier. Lazarus
preserves the finite historical Ethereum state and exact RPC traffic a test
needs, while Ariadne binds a released artefact digest to its evidence. Berean
holds a protocol agent's recorded answers to pinned corpora and preserved
chain reads; it neither chunks documents nor preserves chain state itself.
Pandects supplies reviewed credit laws, Hermes measures a single
gas-optimisation class named by a rule from its pinned corpus,
Hexaemeron controls a receipted delivery loop and holds each of its phases to a
named skill, while Lemma stops after producing
source-linked chunks. Horos decides what an agent does not read. Janus checks
what a contract hook may observe and change around a host action, where
Pandects supplies the economic laws such a transition must preserve. Synkrisis
owns the cross-run comparison boundary: it builds one checked cohort from
declared run observations and infers only bounded relations between named
events, and any operation whose runbook step has not landed refuses by name
rather than guessing. Its findings stay bounded inferences: capture,
redaction, receipt binding, causal triage, and every decision to act stay
with their owners. Sapheneia
shapes the agent's replies for AuDHD readers and has one bounded operation for
durable audit, issue, and comment prose. It does not change another skill's
facts or gates. Brevitas controls the volume and structure of engineering prose
after vocabulary and register passes. If a request crosses one of those
boundaries, hand it to the named sibling rather than broadening the selected
skill.

## Issue queues

Work arrives from four places and each is told apart by its issue title prefix,
so a reader knows which queue a thing came from without opening it.

- `{skill}-next`, labelled `held-job`. A ledger's held frontier job. The system
  named it; closing one increments an evolution counter.
- `{skill}-N`, labelled `wish`. The closed set from a one-off generated
  wishlist, #317 to #334. Exogenous nice-to-haves. Nothing mints another.
- `{skill}-wish`, no queue label. Something a Fiat run noticed about one skill
  and had no authority to fix inside its own packet.
- `framework-N`, labelled `observation`. Something a run noticed about the
  system as a whole. Its body opens by stating that Protasis decides which
  skill or skills it upgrades, because the filer is the wrong party to guess.

`{skill}` is the skill's own governed name rather than its plugin's, so Lemma's
is `lemma`. The reasoning, the alternatives and the two questions still open are
in [ADR-009](docs/decisions/ADR-009-four-issue-queues-and-their-titles.md).
Filing an issue merely to satisfy a workflow remains forbidden; these
conventions say how to title one that was worth filing.

Closing a delivered issue belongs to whoever merges its pull request. The
Atlas draws from open issues alone, so one whose delivery has merged keeps
being allocated until it is closed, and a contributor working from a fork
cannot close it.

## Issue and comment publication

Before an agent publishes a GitHub issue title and body or a GitHub issue
comment for this repository, use this sequence on the complete candidate:

1. freeze the required title prefix, body opening and protected evidence inventory;
2. apply `sapheneia-durable-record-shape`;
3. run Imprimatur and clear every reported defect without dropping protected content;
4. apply Vulgate to the surface only and compare its content with the source; and
5. re-run Imprimatur on the exact publishable bytes.

The four frozen title forms are `{skill}-next`, `{skill}-N`, `{skill}-wish`, and
`framework-N`. Keep every queue-specific body rule from the section above.
The protected inventory includes claims, qualifications, unknowns, negative
evidence, identifiers, paths, `file:line` locations, hashes, addresses,
selectors, numbers, dates, links, quotations, severities, verdicts, status, and
required host structure. Do not publish after a failed check, changed prefix or
body opening, missing protected item, or content mismatch.
GitHub does not enforce this repository rule; it governs agents working from
these instructions.

## Repository map

- Alexandria is under `plugins/alexandria/`. Read
  `plugins/alexandria/AGENTS.md` before running its skill or changing that
  plugin.
- Ariadne is under `plugins/ariadne/`. Read `plugins/ariadne/AGENTS.md` before
  running its skill or changing that plugin.
- Berean is under `plugins/berean/`. Read `plugins/berean/AGENTS.md` before
  running its skill or changing that plugin.
- Brevitas is under `plugins/brevitas/`. Read `plugins/brevitas/AGENTS.md`
  before running its skill or changing that plugin.
- Hermes is under `plugins/hermes/`. Read `plugins/hermes/AGENTS.md` before
  running its skill or changing that plugin.
- Hexaemeron is under `plugins/hexaemeron/`. Read
  `plugins/hexaemeron/AGENTS.md` before running one of its skills or changing
  that plugin.
- Horos is under `plugins/horos/`. Read `plugins/horos/AGENTS.md` before
  running its skill or changing that plugin.
- Janus is under `plugins/janus/`. Read `plugins/janus/AGENTS.md` before
  running its skill or changing that plugin.
- Lemma is under `plugins/lemma/`. Read `plugins/lemma/AGENTS.md` before
  running its skill or changing that plugin.
- Lazarus is under `plugins/lazarus/`. Read `plugins/lazarus/AGENTS.md` before
  running its skill or changing that plugin.
- Pandects is under `plugins/pandects/`. Read `plugins/pandects/AGENTS.md`
  before running its skill or changing that plugin.
- Probitas is under `plugins/probitas/`. Read `plugins/probitas/AGENTS.md`
  before running its skill or changing that plugin.
- Sapheneia is under `plugins/sapheneia/`. Read
  `plugins/sapheneia/AGENTS.md` before running its skill or changing that
  plugin.
- Synkrisis is under `plugins/synkrisis/`. Read
  `plugins/synkrisis/AGENTS.md` before running its skill or changing that
  plugin.
- Tabularium is under `plugins/tabularium/`. Read
  `plugins/tabularium/AGENTS.md` before running its skill or changing that
  plugin.
- `.claude-plugin/` and `.codex-plugin/` files install the same canonical skill
  directories on their named hosts. They do not change the meaning of a skill.
- `.agents/skills/promise-machine/SKILL.md` is the sole host-neutral entrypoint
  for agents that implement the Agent Skills discovery convention. It carries
  no behavioural version or domain promise. It routes through this root
  contract and one plugin runtime contract to one canonical `SKILL.md`. Its
  generated `runtime/` fallback makes a copy-mode Agent Skills install
  dependency-closed; regenerate it with
  `python3 scripts/portable_promise_machine.py sync` after a copied source
  changes.

## Loading rules

1. Read the selected `SKILL.md` in full before acting.
2. Resolve paths relative to the directory containing that `SKILL.md`, unless
   the file defines another base explicitly.
3. Load linked references only when the selected skill directs you to them.
4. Treat slash commands, dollar-prefixed names, and plugin-qualified names as
   invocation aliases. They are not shell syntax.
5. Keep the user's target repository separate from this distribution
   repository. Run a skill's commands in the target named by the user.
6. Obey the target repository's own instructions and permission rules before
   any write or external side effect.

## Checks for changes to this repository

The checked runner is the entrypoint. It reads the declared ownership graph
at `tests/check-map-v1.json`, unions any requested scope with every actual
changed path, closes that set over the declared dependencies, and executes
the selected checks from a disposable snapshot under one process budget
(ADR-041).

```bash
python3 scripts/run_checks.py            # select from the current diff and run
python3 scripts/run_checks.py --plan     # show the selection without running
python3 scripts/run_checks.py --full     # run every declared check
```

A plan or run refuses when a changed path has no declared owner, a command in
the map is stale, or the map is malformed; fix `tests/check-map-v1.json` in
the same change. Hosted CI is unchanged by this entrypoint. The suites below
are the inventory the map declares, and each remains directly runnable.

Every `python3` command below means the exact interpreter recorded in
[`.python-version`](.python-version). The supported minor is declared in
[`pyproject.toml`](pyproject.toml); do not substitute a different ambient
interpreter.

### Suites

```bash
python3 scripts/portable_promise_machine.py check
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean
python3 -m unittest discover -s plugins/brevitas/tests -t plugins/brevitas
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
python3 plugins/lemma/tests/test_markdown.py
python3 plugins/lemma/tests/test_solidity.py
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
python3 -m unittest discover -s plugins/pandects/tests -t plugins/pandects
python3 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
python3 -m unittest discover -s plugins/sapheneia/tests -t plugins/sapheneia
python3 -m unittest discover -s plugins/synkrisis/tests -t plugins/synkrisis
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
```

### Solidity

Pandects also carries Solidity. From `plugins/pandects/`:

```bash
forge build
forge test
```

### Lints

Prose that ships goes through the lexicon lint and then the structural one.
The three skill lints read a tree rather than a diff, so they run from the root
and must exit clean:

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <changed prose>
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <changed prose>
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
```

Validate every changed skill directory against the Agent Skills frontmatter
rules. Keep `SKILL.md` names equal to their parent directory names and keep
descriptions precise enough to select the skill without reading its body.

## Reading boundary

Before reading this repository broadly, consult `.horos/boundary.json`.
Every path listed there is a classified token sink carrying the evidence
that earned its entry; leave those paths unread unless the task demands
one. The boundary is fail-open: what it omits is merely unproven. It never
applies during security review; during any audit, review or incident work,
read as if no boundary exists.

The root suite checks that this file's boundary still describes the tracked
tree, so a change that adds or alters a classified file fails it until the
boundary is regenerated:

```bash
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
```
