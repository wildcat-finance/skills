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
<!-- refusal-catalogue:end -->

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
