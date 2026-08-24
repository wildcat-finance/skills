# Promise Machine contract

<!-- promise-machine: contract=promise-machine/v1; canonical=PROMISE_MACHINE.md; copies=generated -->

This document is the normative contract for every skill distributed as part of
Wildcat Labs Skills. Plugin-local files with this name are generated,
byte-identical installation copies. They are not separate laws.

## Contract identity

The shared contract identity is `promise-machine/v1`. It identifies this law's
format and semantics. It is neither a plugin package version nor a skill
evolution version.

## Governing principle

> No skill may claim more than its evidence establishes, or authorise a more
> consequential transition than that evidence warrants.

This principle applies to every answer, artefact, repository change,
publication, deployment and external action produced through the suite. A
passing check establishes only the promise that names it. It does not establish
the skill's general correctness, the truth of its inputs or any neighbouring
claim.

## Scope

The contract applies to first-party skills, nested skills, vendored skills,
routers, runtime contracts, generated copies and evidence handoffs. Each
logical skill has one canonical implementation. Routers select that
implementation and establish no domain result of their own.

Vendored instructions remain upstream-owned and byte-for-byte unmodified. A
first-party overlay may bind a vendored operation to this contract when it
names the upstream digest, the bounded promise and the Wildcat-owned evidence.

## Vocabulary

| Term | Meaning | Required binding | Nearest refusal |
| --- | --- | --- | --- |
| Promise | A bounded claim made by one skill operation | Stable promise id and canonical skill | An adjacent claim |
| Promise boundary | The subject, scope and nearby conclusions the promise does not support | Subject and scope | Unexplained scope widening |
| Promise check | Identified evidence evaluated to decide whether a promise holds | Evidence identity and result | Unchecked evidence |
| Authorised transition | The representation or action a satisfied promise permits | Consequence level | A more consequential action |
| Refusal | Denial of the dependent transition when the promise is not established | Blocked transition | Continuing after failure |
| Recovery | Inspection, cure, rerun, rollback or safe exit left available after refusal | Actionable recovery path | Global halt or no exit |
| Exception | An attributed, scoped and recorded decision to waive or narrow one gate | Authority, scope, record and expiry | Silent waiver |
| Evidence inheritance | A consumer may narrow evidence or add separately identified evidence | Producer, consumer and original class | Unexplained strengthening |
| Bounded conformance | Observed behaviour stayed inside a declared boundary for named inputs, adapter, recorder and search | Inputs, adapter, recorder and search | Safety proof or unobserved executions |

## Evidence classes

Evidence classes describe relations, not a universal strength ordering:

| Class | Establishes | Does not establish |
| --- | --- | --- |
| `checked` | An identified deterministic rule or schema accepted the subject | Truth or completeness outside that rule |
| `recomputed` | A result was derived again from identified inputs and method | Authority beyond those inputs and method |
| `proved` | A named formal, cryptographic or defined proof relation accepted the subject | Any claim outside that proof relation |
| `measured` | A value was observed under a recorded method and environment | Universal performance or causation |
| `recorded` | Bytes or a statement were preserved from an identified source | Truth of the source assertion |
| `attested` | An identified actor or system made the statement | Independent truth of the statement |
| `inferred` | A conclusion follows under a stated rule from named evidence | Direct observation or proof |
| `unknown` | The matter was not established | Any positive transition |

A domain may refine a class, such as `proved: EIP-1186 account proof`, while
keeping the base class recognisable. A consumer records any change of class and
the evidence that supports it. Absence, ambiguity and `unknown` never pass.

## Promise declarations

Every governed first-party canonical skill has exactly one `## Promise Machine
contract` section. It contains one or more stable `### <promise-id>` blocks.
Each block carries these fields exactly once:

- `Promise`
- `Evidence`
- `Evidence classes`
- `Boundary`
- `Authorises`
- `Consequence`
- `Refuses`
- `Recovery`
- `Exceptions`

The promise id is stable within the skill. Operations whose claims or
authorised transitions differ use separate promise ids. Evidence names the
command, record, test, proof relation or observation that supports the claim.
The boundary names the nearest tempting overclaim. Refusal names the transition
that stops. Recovery remains usable when refusal occurs.

`Exceptions: none` is explicit. A supported exception follows the rules below.

## Consequence levels

The consequence belongs to the authorised transition, not to the skill as a
whole:

| Level | Transition | Minimum enforcement |
| --- | --- | --- |
| 0 | Response or presentation only | Preserve scope, content and uncertainty |
| 1 | Derived artefact | Validate structure, provenance and visible gaps |
| 2 | Repository or durable-data mutation | Tests, negative evidence and recoverable change |
| 3 | Publication, deployment, external action, security or financial conclusion | Fail-closed gate, recorded authority and independently inspectable evidence |

A skill with operations at different levels declares separate promises. A
level-3 transition cannot rest only on model judgement, unrecorded operator
memory, an unchecked receipt or evidence whose subject does not match.

## Composition

Composition preserves the producer's boundary. A handoff records the producing
skill, consuming skill, subject, scope, evidence class, time domain and any
transformation. The consumer can add separately identified evidence. It must not
rename narrow evidence into a stronger class or drop a conflict, gap, refusal
or recovery path.

In particular:

- Lemma chunks remain source-linked retrieval material; they do not establish
  answer truth.
- Lazarus recorded RPC evidence remains recorded unless its named proof check
  established a narrower proved relation.
- Berean citations, evaluations and promotion records establish their declared
  release gates; they do not establish factual truth or model quality.
- Janus results remain bound to the named host adapter, manifest, recorder and
  bounded search; they do not establish hook safety, complete liveness or
  cross-host conformance.
- Ariadne binds an artefact digest to declared evidence; without an external
  signature verifier it does not establish author identity.

Any unexplained strengthening is a conformance failure.

## Refusal and recovery

Missing, stale, malformed, mismatched or insufficient evidence fails closed.
Failure blocks the dependent transition and no broader one. Inspection,
diagnosis, repair, rerun, rollback and safe exit remain available unless the
promise explains why a particular recovery cannot exist.

A refusal report names the promise id, failed field or evidence, consequence
level, blocked transition and recovery action. A checker never deletes,
rewrites or quarantines the failing source merely to produce a passing result.

## Exceptions

An exception is evidence, not silence. It names:

- the person or policy with authority;
- the promise id and exact gate being waived or narrowed;
- the affected subject and scope;
- the durable record holding the reason;
- the expiry, or why expiry cannot apply; and
- the recovery or revocation path.

An exception cannot claim that missing evidence exists, strengthen an evidence
class, erase a recorded conflict or authorise a transition beyond the named
scope. Unattributed, unrecorded, expired or over-broad exceptions fail closed.

## Conformance

Structural conformance establishes that the declarations, identities, copies
and coverage records have the required shape and agree. It does not establish
that a domain promise is true. Behavioural conformance comes from the named
domain tests, negative specimens, proof checks, measurements and manual
demonstrations.

The checker discovers the governed universe from repository manifests and
skill paths. A hand-maintained coverage file may classify discovered entries;
it may not define the universe or remove an entry from it. Empty discovery,
unclassified skills, duplicate logical identities, missing declarations,
divergent copies and unbound vendored instructions are failures.

Checker output names a stable finding code, fault class, path, promise id when
known and the action that clears it. JSON and text reports describe the same
findings. The checker reaches no network and executes no evidence command.

## First-party licence promise

### promise-machine-first-party-licence

- Promise: A successful `check --only licences` establishes that the root and every first-party plugin carry the same Apache-2.0 licence bytes, and that both host manifests name Apache-2.0 and Wildcat Labs.
- Evidence: The fixed root `LICENSE`, discovered first-party plugin set, byte comparisons, and parsed Claude and Codex plugin manifests.
- Evidence classes: checked, recomputed
- Boundary: The check does not establish copyright ownership, provide legal advice, or inspect, govern, or relicense vendored work; the Pashov skill trees retain their upstream MIT licence and notices.
- Authorises: Publishing the discovered first-party plugin surfaces with the repository's Apache-2.0 and Wildcat Labs licence declaration.
- Consequence: 3
- Refuses: A missing, unsafe, oversized, or divergent licence, an inconsistent host manifest, or any claim that the first-party licence covers a vendored skill.
- Recovery: Restore the canonical root licence and first-party copies, correct the host manifests, leave vendored licences untouched, and rerun the licence check.
- Exceptions: none

## Run observation promise

### promise-machine-run-observation-structural-validation

- Promise: A successful `python3 scripts/run_observation.py check <path>` establishes that the named regular JSON Lines file conforms to `promise-machine-run-observation/v1` under the validator's closed shapes, limits, lifecycle, backward-reference, evidence-binding, unknown-fact, optional-token, Unicode-path and final-snapshot rules.
- Evidence: The exact input path and validated bytes, one bounded final named-path reread with matching digest and file identity, v1 schema, standard-library validator, stable finding report, valid and refusing fixtures, focused tests and zero command exit.
- Evidence classes: checked
- Boundary: Validation does not capture a run, prove that the record is complete or externally true, establish cause or model quality, bind a Fiat receipt, make a security conclusion, authorise mutation, or prevent a writer changing the path after the final reread.
- Authorises: Treating only the named bytes as structurally conforming and passing that bounded result to a consumer that preserves its subject, scope, time domain, evidence class, unknowns and refusal boundary.
- Consequence: 1
- Refuses: Unsafe or unbounded input, a final byte or identity mismatch, malformed or duplicate-key JSON, an open event shape, missing identity, invalid order or lifecycle, a forward or cross-run reference, unbound or strengthened evidence, hidden reasoning, raw payloads, non-scalar, non-NFC, control-bearing, bidirectional or otherwise unsafe repository paths, placeholder host facts, invalid token counts or a non-zero finding report.
- Recovery: Inspect the stable finding code, repair the source record without having the checker mutate it, preserve unknowns and evidence boundaries, then rerun the same command.
- Exceptions: none

## Contributor ranking promise

### promise-machine-contributor-ranking

- Promise: A successful `python3 scripts/contributors.py --check` establishes that every contributor row GitHub returned for the named repository was placed in exactly one of ranked, excluded with a named reason, or refused; that each ranked login is a valid GitHub login absent from the declared runtime-host set, is neither the Shoggoth's account nor the repository owner, and had at least one commit in a bounded sample authored by a non-host identity; that the order is merged commits, then merged pull requests, then login; and that `CONTRIBUTORS.md` and the marked region of `README.md` match that one computation byte for byte.
- Evidence: The recorded contributors, merged-pull-request and commit-authorship reads, the host-set parity check against `hexctl.py`'s declaration, the login grammar check, the per-identity classification lines, the ranking digest, the byte comparison of both artefacts and zero command exit.
- Evidence classes: checked, recorded
- Boundary: Ranking does not establish that the counts fairly measure contribution, that a commit carried judgement, who wrote which line, anything about a person beyond the account they committed under, or that GitHub's resolution of author emails to accounts is correct. It does not detect a merge that discarded commit authorship before the commit reached the default branch, and its authorship corroboration samples at most twenty commits per account rather than all of them.
- Authorises: Writing `CONTRIBUTORS.md` and the marked region of `README.md` and nothing outside those two targets, and reporting the ranking without strengthening what the counts mean.
- Consequence: 1
- Refuses: An account type other than User or Bot, a Bot absent from the declared host set, a login failing the GitHub login grammar, a repository argument carrying query syntax, any failed API read including a rate limit, a host set diverged from `hexctl.py` in either direction, an excluded login reaching the ranked output, a `README.md` that is absent or not UTF-8, and a read that would silently truncate.
- Recovery: Read the stop, which names the identity or field at fault; extend the host set in `hexctl.py` and `scripts/contributors.py` together for an unknown host, set a token or wait for the named reset for a rate limit, and rerun with `--write` for a stale artefact. The generator never repairs an input.
- Exceptions: none

## Installation copies

The root `PROMISE_MACHINE.md` is the authored source. Each
`plugins/<plugin>/PROMISE_MACHINE.md` is written only by
`scripts/promise_machine.py sync`. The destination is fixed, writes are atomic,
symlinks and paths outside the repository are refused, and `sync --check`
rejects a missing or byte-divergent copy.

Standalone plugin runtime contracts load their local copy. Repository-wide
work loads this root file. Both surfaces therefore read the same contract
bytes under the same identity.
