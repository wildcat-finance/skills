# Skill demonstration contract

A governed skill says what it can do. This contract says what it can *show*,
over inputs a reader can check, on a machine with no network.

Every governed first-party skill keeps one `DEMONSTRATION.md` beside its
`SKILL.md` and `EVOLUTION.md`. Discovery is the registry: there is no global
inventory file to fall out of date. `scripts/demonstrations.py check --root .`
finds the same directories as `scripts/shoggoth_topology.py` and requires
exactly one record in each.

This lane is independent of the behaviour lane in
[VERSIONING.md](VERSIONING.md). A demonstration ledger never changes an
`EVOLUTION.md` digest, held job, or version, and an evolution ledger never
decides a demonstration status. One Fiat run may advance both, but each ledger
has to satisfy its own contract on its own evidence.

## The file

`DEMONSTRATION.md` is human Markdown carrying one fenced JSON object tagged
`shoggoth-demonstration`. The prose above the fence is for a reader. The object
is the record. Its closed machine contract is
[`shoggoth-demonstration-v1.json`](../../../schemas/shoggoth-demonstration-v1.json);
the checker loads that committed schema and validates every record against it.
An unknown key or a key missing from the schema's required set is therefore a
refusal, not an ignored extension.

A ledger opens with a heading, a link to this contract, and five bullets: the
current demonstration version, the demo frontier status, the demo frontier
revision, the current demonstration in one checkable sentence, and the one next
demonstration job. The fenced `shoggoth-demonstration` object follows those
bullets. A `## History` table closes the file with the columns `Version`,
`Axis`, `Demo frontier revision`, `Demo frontier SHA-256`, `Evidence`, and
`Change`.

The history table follows the same axes as the behaviour ledger: `baseline`,
`evolution`, `generation`, `epoch`. Its digest covers this exact UTF-8 line,
including its final newline:

```text
{status}|{demo frontier revision}|{current demonstration}|{next demonstration job}
```

Version labels are `{skill}-demo-v{evolution}.{generation}.{epoch}`. They are
not SemVer, and they are not the skill's behaviour version. A skill may sit at
`horos-v10.3.3` and `horos-demo-v0.1.0` at the same time; the two counters
never move together by rule.

## Status

Five values, closed. Status is decided by the material inputs, never by how
good the example reads.

- `real-data` -- every material input is a preserved real-world source, and
  the registered offline path reproduces the named result.
- `mixed` -- at least one real-world source is present, but a constructed or
  target-mismatched component is material to the result.
- `constructed` -- the whole executable example is built from fixtures or
  model records created for the example.
- `absent` -- no complete executable demonstration exists yet.
- `not-applicable` -- the owner gives a checked reason why a real-world input
  would not make sense for this skill. This is not a synonym for unfinished.

A material input is one the named result depends on. If removing it changes
the observation, it is material. One material constructed input is enough to
stop a record being `real-data`; the honest value is then `mixed`.

## The record

```json
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "horos",
  "plugin": "horos",
  "status": "constructed",
  "claim_id": "horos-boundary-currency",
  "claim": "What a reader may conclude when the commands exit as named.",
  "non_claim": "What this demonstration does not establish.",
  "network": {"policy": "denied"},
  "timeout_seconds": 300,
  "sources": [
    {
      "id": "skills-tree",
      "class": "repository",
      "path": ".horos/boundary.json",
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
    }
  ],
  "commands": [
    {
      "id": "scan",
      "argv": ["python3", "plugins/horos/skills/horos/scripts/horos.py", "check", "."],
      "expect_exit": 0
    }
  ],
  "observations": [
    "One statement per line, each checkable against the command output."
  ],
  "frontier": {
    "version": "horos-demo-v0.1.0",
    "status": "open",
    "revision": "boundary-over-an-external-tree",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "current": "The current demonstration, repeated from the ledger prose.",
    "next": "The one held demo job, repeated from the ledger prose."
  }
}
```

Field rules, all enforced by the checker:

- The object is strict JSON with no duplicate keys, no unknown top-level keys,
  and no missing required key.
- `skill` and `plugin` match the directory the record was found in.
- `claim_id` is unique across all records and matches `[a-z][a-z0-9-]{0,63}`.
  It is the only join between a public card and this record.
- `claim` and `non_claim` are non-empty. A record with no non-claim is refused:
  a demonstration that admits no boundary is an advertisement.
- `network.policy` is `denied` or `allowlisted`. An `allowlisted` policy names
  `endpoints` and may name `secret_env`; it never records a secret's value.
- `timeout_seconds` is an integer between 1 and 3600, and it applies per
  command.
- Every source carries an `id`, a `class` from `chain`, `protocol`,
  `repository`, `audit`, `production-run`, `fixture`, or `model-record`, and
  its identity: a repository-relative `path` with a `sha256`, or a `chain`
  with a `block` and an `anchor`.
- Every command carries an `id`, a strict `argv` array of non-empty strings,
  and an integer `expect_exit`. There is no shell string form, no `cwd`
  outside the repository, and no interpolation.
- A `real-data` record carries at least one source and one command, and no
  source whose class is `fixture` or `model-record`.
- A `mixed` record carries at least one source of each kind: one preserved
  real-world class, and one `fixture` or `model-record`.
- An `absent` or `not-applicable` record carries no sources and no commands,
  and its `claim` states the reason.

## Refusal catalogue

These are the exact refusal conditions enforced by the current checker. The
stable code is part of the diagnostic surface; one code can add context but
cannot silently change the boundary it names.

<!-- refusal-catalogue:start -->
- `D001` -- a ledger is absent, oversized, non-regular, symlinked, or changes during its bounded read.
- `D002` -- a ledger is not UTF-8.
- `D003` -- a ledger does not contain exactly one complete record fence.
- `D004` -- record JSON is invalid, duplicated by key, too deeply nested, or not an object.
- `D005` -- the top-level record has an unknown key or omits a schema-required key.
- `D006` -- the record does not name `shoggoth-demonstration/v1`.
- `D007` -- the record's skill or plugin does not match its discovered owner.
- `D008` -- status is absent as text or is outside the closed five.
- `D009` -- claim identity, claim text, or non-claim text is malformed.
- `D010` -- network policy or the denied-network object is malformed.
- `D011` -- an allowlisted network omits safe HTTPS endpoints or names an invalid secret environment variable.
- `D012` -- the per-command timeout is not an integer from 1 through 3600 seconds.
- `D013` -- sources, commands, or observations are not lists or exceed their caps.
- `D014` -- an observation is empty, untrimmed, non-text, or oversized.
- `D015` -- an executable status lacks a source, command, or observation.
- `D016` -- an absent or not-applicable status carries an executable source, command, or observation.
- `D017` -- a real-data record carries a fixture or model-record source.
- `D018` -- a mixed record lacks either a preserved source or a synthetic source.
- `D019` -- a constructed record carries a source outside fixture and model-record.
- `D020` -- a source object, source id, or source identity is malformed.
- `D021` -- a source class is outside the closed source-class set.
- `D022` -- a chain source lacks its chain, block, or 32-byte anchor, or also names a file.
- `D023` -- a file source lacks its path or digest, or also names a chain identity.
- `D024` -- a declared source path is absolute or traverses above the repository.
- `D025` -- a source is absent, oversized, non-regular, symlinked, unreadable, or changes during its bounded read.
- `D026` -- a source's observed SHA-256 differs from its declaration.
- `D027` -- source ids collide within a record.
- `D028` -- bounded source reads together exceed the whole-run byte budget.
- `D030` -- a command object or command id is malformed.
- `D031` -- argv is absent, empty, oversized, non-text, or contains a control character.
- `D032` -- expected exit is not an integer from 0 through 255.
- `D033` -- command ids collide within a record.
- `D040` -- the demo version or frontier object does not belong to the skill.
- `D041` -- frontier status is outside `open` and `mature`.
- `D042` -- frontier revision, current demonstration, or next job text is malformed.
- `D043` -- a mature frontier still names a job, or an open frontier says it is mature.
- `D044` -- the demo frontier digest does not match its exact canonical line.
- `D045` -- an absent demonstration claims its demo frontier is mature.
- `D050` -- two governed ledgers claim the same public claim id.
- `D060` -- the committed schema is unreadable, open, malformed, or does not validate the record.
- `D070` -- a run's selection resolves to zero executable records.
- `D071` -- a registered public demonstration has no ledger or is not `real-data`, or a named directory is not governed.
- `D072` -- a command names a program other than `python3`, gives the interpreter no work, or its program file is absent or cannot start.
- `D073` -- the running interpreter is not the version `.python-version` pins, or no pin can be read.
- `D074` -- a child opened or resolved a socket, removed the armed network marker, or was given an interpreter option word whose letters turn the socket hook off, including a bundle such as `-Sc`, or the record allowlists a network this run does not admit.
- `D075` -- a command's exit status differs from its declared `expect_exit`.
- `D076` -- a command passed its timeout and its process group was killed.
- `D077` -- a command wrote past the output cap and was truncated.
- `D078` -- an observation is prose, names an unknown command, or is outside the checkable grammar.
- `D079` -- a checkable observation did not hold against the command's stdout.
- `D080` -- the report path traverses, resolves outside the output root, or already exists.
- `D081` -- the report's parent is no longer confined below the output root, or the report could not be published atomically; no partial object was left under its name.
- `D082` -- the public set passed its aggregate ceiling.
- `D083` -- the private work root could not be created or prepared.
- `D084` -- a registered public demonstration runs a program no source declares, the program's bytes differ from the digest its source declared, or a command puts an option word outside the closed interpreter grammar where its program belongs.
- `D085` -- a command left a process holding its pipes after its process group was killed, so something it started is outside the runner's teardown.
<!-- refusal-catalogue:end -->

## Observations are checkable, not prose

A record that the runner executes carries observations in one of two forms,
each naming the command it reads:

```text
run: line "1. two fresh builds agree on 079ed18d... across 7 components"
run: json relation.receipt_count 224
```

`line` holds when that exact line, given as one JSON string, appears on the
command's stdout. `json` holds when the command's last stdout line parses as a
JSON document and the dotted path, with integer segments indexing lists, equals
the JSON value. A sentence such as "the command exits in about a second" is
not evidence: the runner refuses it with `D078` before any command starts. A
duration is recorded in the report as an observation of the run, never
declared in the record as a thing to assert.

## Running the public set

`scripts/demonstrations.py run` executes either one governed record named by
`--record <directory>` or the closed public set named by `--public-set`, and
nothing else. The public set is the fixed claim-id list `PUBLIC_SET` in the
runner; a member whose ledger is absent or whose status is no longer
`real-data` fails the run rather than being skipped. A selection that resolves
to zero executable records is a refusal, never a clean pass.

Before anything executes, the runner reads `.python-version` and refuses an
interpreter that differs from it, checks that the `--report` path traverses
nothing and resolves below the declared output root (`--output-root`,
defaulting to `--root`) to a name that does not yet exist, loads every ledger
through `check`, so every declared source digest is verified, and parses each
selected record's observations. A file source is recorded in the report as
verified; a chain anchor is recorded as declared, because the runner has no
chain and proves nothing about one.

Each command's argv runs without a shell, and `python3` is the only program a
record may name: anything else would be resolved through `PATH` and would run
outside every control described here, so it is refused with `D072` before the
run starts. The named interpreter is replaced by the running, pinned one. The
only substitution inside an argv element is the reserved `{work}` token, which
expands to a private `0700` directory beneath a fresh temporary root that is
removed when the run ends; every other brace is passed literally. The child
sees an allowlisted environment (`PATH`, `HOME`, `TMPDIR`, `LANG`, `LC_ALL`,
`LC_CTYPE`) plus a `PYTHONPATH` naming only the runner's site hook, so
credential and Git keys are stripped by never being copied. The hook replaces
the socket constructors and resolvers in the Python child with a function that
records the attempt in a marker file and raises; a child that opens or resolves
a socket is refused even when it swallows the exception and exits 0. The marker
is armed as an empty file before each command and its identity is pinned, so a
child that unlinks or replaces the marker to hide the attempt is refused for
that removal. `-S`, `-E` and `-I` would leave the child outside the hook
entirely, by skipping `site` or ignoring `PYTHONPATH`, and are refused with
`D074`. This is a process-level denial inside one Python process, not a kernel
sandbox. Two routes stay outside what the hook can see: a child that reaches
the kernel's socket call directly, through `ctypes` or another extension, and a
child that starts a further process without the hook's `PYTHONPATH`, which gets
an unhooked interpreter. A run establishes that no denied Python socket call
went unrecorded; it never establishes that no network call was made. No capture
exception is declared, so a record that allowlists a network is refused.

Each command is bounded by its record's `timeout_seconds`, further clipped by
the public set's aggregate ceiling of 600,000 milliseconds. A command that
passes its budget is killed with its whole process group, and the group is torn
down on every path, so a command that exits 0 after forking leaves nothing
behind it. The recorded duration ends when the command's own process is reaped,
so teardown is never charged to it. A grandchild that leaves the group, by
calling `setsid` or equivalent, is beyond a process-group teardown: it is
detected by the grip it keeps on the command's pipes and refused with `D085`,
not silently allowed to survive. Stdout and stderr
are each capped at one mebibyte; a command that writes past the cap is
truncated and refused. Exit status, observations, durations, output digests
and bounded output tails are recorded per command and per repetition;
`--repeat` runs each record up to ten times so a three-repetition baseline can
be recorded without claiming an improvement.

The run publishes one `shoggoth-demonstration-report/v1` object to the report
path: the body lands in a sibling `.partial` file and is linked in under the
final name without replacing anything, so the target is either complete or
absent. Publication does not travel the pathname again. The report's parent is
reopened by walking down from the output root with each component opened
without following a symlink, and both the partial write and the link run
against that descriptor, so a component swapped during the run refuses with
`D081` instead of publishing outside the root. The report repeats each record's
claim, non-claim, record digest and
sources, and its `status` is `verified` only when every selected record
verified; the process exits 0 in that case and 2 otherwise. A report is
evidence of one run on one machine and promotes nothing a record's non-claim
withholds.

Each record's `programs` array says what the run established about the program
each command ran, which `sources` alone never covered. A registered public
demonstration declares its program as a source, so the program is digested
before execution like every other input and its entry reads `verified`. Any
other record's program is proved to exist and not digested, and its entry
reads `found`. The distinction is the point: `verified` names bytes checked
against a declared digest, `found` names a file that was there. A program
reached through `-c`, `-m`, standard input or a `{work}` path is not a
committed file, so it carries no entry and no digest at all. Which word is the
program is read from a closed interpreter grammar rather than from position:
flag bundles such as `-u` and `-OO`, the argument-taking `-W` and `-X`, and a
closing `--` are walked past to the program they precede, so an option word
cannot carry a committed file past the declaration gate or the digest re-read.
An option word the grammar cannot place is refused with `D084`.

The runner emits `demonstration.selected` with the record count,
`demonstration.started` per command, `demonstration.verified` or
`demonstration.refused` per record, and `demonstration.report` with the
published digest, all carrying one correlation id. A ledger, schema or topology
refusal reached during a run emits `demonstration.refused` under that same
correlation id, so no failed run is visible only as stderr prose.

## What the checker establishes

`check` reads the discovered tree, committed schema, ledgers, and declared
local source bytes. It performs bounded, no-follow regular-file reads, rejects
duplicate JSON keys and excess nesting, applies one whole-run source budget,
and starts no command. It establishes that every governed skill has exactly
one record, that each record is structurally valid, that claim ids do not
collide, and that every declared local source path has the declared digest.

It does not establish that a command passes, that an observation is true, or
that a status is deserved beyond the structural rules above. Running the
commands is a separate operation, and its report is separate evidence.

## The demo frontier

`scripts/demonstrations.py frontier --root . --lane demo --dry-run` ranks the
records whose demo frontier is open and prints the one it would take next. It
reads only `DEMONSTRATION.md`. It never reads, ranks, or writes an
`EVOLUTION.md`.

The demo lane is read-only in this generation. It does not file an issue,
dispatch Fiat, advance either ledger, or write `.kronos/`. `{skill}-demo` and
`demo-frontier` are governed title and label conventions for a demo job; a
name in that shape is a convention, not evidence that an issue exists. When
one issue can satisfy both a behaviour and a demo acceptance set, the ledgers
point at that one issue rather than filing a second.

The separate-lane decision, the co-delivery rule, and the issue-reuse rule are
recorded in `adr/govern-real-data-demonstrations-separately`.
