# Decision: Declare a held job's required inputs in the ledger

Stable identity: `adr/declare-a-held-jobs-inputs-in-the-ledger`.

## Status

Proposed, 2026-09-05.

## Context

An evolution ledger's `Next Fiat job` states what to build and what accepts it.
It never states what the job needs before it can start.

Kronos scores readiness of inputs and acceptance conditions on one axis capped
at 20 of 100. Acceptance conditions are stated in the ledger and can be read.
Inputs are stated nowhere, so half that axis is inferred from the job's prose
and the inference is not recorded.

Measured on the rank-only pass recorded at `refs/heads/kronos/state`
`b8bbaa62c28e636ba8608fa7794335c339c2729b`, over 21 candidates: `probitas`
scored 11 on a job requiring an attribution its current state refuses as
unattributable, `alexandria` 10 on a job requiring two live providers and their
credentials, and `imprimatur` 8 on a job requiring two fresh blind human
annotations at kappa 0.80. Each requirement is legible in the job's prose. None
of the three availabilities is stated anywhere, so each score is a guess about
whether the work can be started at all.

`show` already marks an axis that moved for a candidate whose held-job digest
did not. It detects the symptom and cannot supply what would prevent it.

## Decision

One optional fenced `declared-inputs` block in a governed ledger's frontier
section, placed after the last header bullet and before `## History`, with rows
of four pipe-separated fields `id | kind | availability | note`. `kind` is one
of `credential`, `endpoint`, `person`, `corpus`, `tool`. `availability` is one
of `available`, `absent`, `unknown`.

Three parts, which are one choice seen from three sides.

1. **`VERSIONING.md` owns the field; Kronos owns only the reader.** A reader
   Kronos does not own already parses these ledgers: `hexctl.py`'s
   version-relation path reads any governed ledger, including the mature ones
   Kronos never ranks. A badly placed block can split `_ledger_field_bytes`
   from `ledger_frontier_digest`, so a format with that reach cannot be defined
   inside a consumer that calls neither. 27 ledgers are governed and the
   recorded pass ranked 21; six carry a format defined for all of them. Kronos
   is also mature and terminal, and its ledger blocks work intended to improve
   Kronos: reading a field is a generation change to the consumer, while
   defining a field for 27 ledgers is not a change to Kronos at all.

2. **The declaration sits outside the four-field frontier digest.** The block
   adds no `- Name: value` line, so `{status}|{frontier revision}|{current
   frontier}|{next Fiat job}` is byte-identical and every existing ledger keeps
   the digest recorded in its own history row. The cost is stated rather than
   hidden: the ledger's own history cannot detect a declaration that changed.

3. **The scoreboard's per-pass declaration digest carries that detection
   instead.** `kronos.py` records a declaration digest beside the existing
   held-job hash, and `show` marks a declaration that moved under an unchanged
   held job, in the same way it already marks a moved axis.

The block is a claim its ledger's owner makes. It is checked for shape and
never for truth.

## Alternatives

- **A Kronos-owned sidecar, `EVOLUTION.inputs.json` beside the ledger.**
  Trivially digest-safe and machine-shaped. Rejected because the declaration
  leaves the ledger, which puts it outside the append-only surface a reviewer
  reads and makes a consumer that is not Kronos learn a second file to read one
  skill's frontier.
- **A `- Declared inputs:` header bullet joining the canonical line as a fifth
  digested field.** The strongest possible detection, because a changed
  declaration would move the ledger's own digest. Rejected on measurement: all
  27 governed ledgers stop matching their recorded history row.
- **The same header bullet left outside the digest.** The cheapest bytes and
  the fastest read. Rejected because it puts every input in one value, so an
  id, a kind, an availability and a note can only be recovered by splitting a
  value another field already holds, and a reader is left with five header
  bullets of which four are digested and one is not.

## Consequences

A readiness score can name what it read. A pass records `declared_inputs` as an
object where the ledger declared and `null` where it did not, so a later reader
can tell a read score from a guessed one, and the 21 rankable skills record
`null` today rather than recording nothing.

Every existing ledger is unaffected. The block is optional, no governed ledger
carries one at `5bc2494c`, and each recomputed frontier digest is byte-identical
to the value in its own history row. Kronos's stays
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1`. `hexctl.py`
needs no change.

A malformed block refuses a Kronos pass with `K022` and appends nothing, which
is the module's existing whole-or-nothing rule. `tests/test_evolution_contract.py`
refuses a malformed block on any governed ledger, so a mature ledger Kronos
never ranks is still caught by the marketplace gate.

Three things this does not do. It does not make a readiness score objective:
the block supplies the basis and the score stays the ranking agent's own work.
It does not verify that a declared input exists; nothing here reaches out to
check whether a declared endpoint answers or a declared person is available. It
does not stop a ledger declaring an input wrongly.

The closed `kind` and `availability` vocabularies and the 16-row cap are
extendable by an ordinary change to `VERSIONING.md`, and earn no record of their
own. Kronos's held `Next Fiat job`, its frontier revision and its frontier
digest are unchanged, and its frontier status stays `mature`.
