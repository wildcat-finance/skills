# Study: #435 capture-profile CARRYOVER-12 reconstruction

## 1. Problem

Issue #435 needs a bounded pre-persistence capture profile: hostile
run-observation inputs become an accepted descriptor-only record, a bounded
gap, or a refusal before durable output. This Fiat run starts from current main
`411d5131ecc8f4e50f3db57deee881a56605cd38` and applies the complete
CARRYOVER-12 packet before any product check.

The only reconstruction source is [#435 CARRYOVER-12](https://github.com/wildcat-finance/skills/issues/435#issuecomment-5390461150), SHA-256
`6954eaf4b5b0ce40d70bc3b5ffeae11f652c54b574dcc3d3d7b4283e90e921a7`.
It supersedes CARRYOVER-1 through CARRYOVER-11. Their partial trees and C11
audit outputs are not acceptance evidence.

## 2. Boundary

Included: the capture runtime and schema, redaction/fingerprint/writer
contracts, fixtures, source reporter, focused and inoculation tests, Promise
coverage, ADR-018, portable published study/runbook copies, and audit record.

Excluded: #436 receipt binding, #437 handover, #508 process work, live capture,
secret collection, databases, CI, dashboards, and Solidity. ADR-017 is existing
durable-agent-prose material and must remain byte-identical; ADR-018 is the
capture decision record.

## 3. Complete inoculation map

Mason must map these 25 IDs exactly once to an owner, current path, and guard
before any test, reporter, lint, diff, receipt, audit, or acceptance claim:

- C1-01 through C1-04: supported Promise coverage command, total reporter,
  complete ADR, and portable byte-identical receipt copies.
- R1-01 through R1-08: descriptor bounds, order-independent redactions,
  derived fingerprint eligibility, writer revalidation, confined reporter
  output, closed schema vocabulary, reporter coverage digest, and valid
  Elenchus report-format syntax.
- R2-01 through R10-01: cached/working diff checks; exact terminal newline and
  `5c 6e` detection; receipt digest equality; ADR allocation; current Promise
  coverage; detached receipt handling; immutable receipted sources; and common
  base identity.
- R11-01 and R11-02: a detached-parent receipt command must use a
  parent-runnable reporter or state its boundary; a test-only receipt repair
  keeps two red reproductions and records an honest structured `passed` result
  instead of inventing a parent assertion failure.

## 4. Chosen construction

1. Build the full 25-ID union once on this run's base. No intermediate
   carryover tree is verified or accepted.
2. Create receipted study/runbook sources once, then create only byte-identical
   published copies. Mason and Warden may inspect source bytes but never edit
   them after receipt.
3. Bind source, copy, and controller receipt SHA-256 values; require tail bytes
   `2e 0a` and reject literal `5c 6e` in authored study/runbook bytes.
4. Use a direct reporter with an absolute canonical descendant of the active
   worktree. Give Elenchus only a relative descendant declaration.
5. Run Elenchus on a causal repair. Runtime, schema, writer, or path repairs
   require `guarded`. A reporter or test-only repair may record `passed` only
   with two preserved red reproductions, a complete zero-error report, and an
   audit explanation of why the fixed test blob cannot fail in its parent.

## 5. Evidence and gates

Before every product command, prove the 25-ID map, full declared path set,
ADR-017 preservation, ADR-018 allocation, current base identity, source/copy
equality, terminal bytes, and absence of authored escapes. The Promise coverage
must contain `sapheneia-durable-record-shape`; `fiat-final-integration`,
`fiat-study-amendment`, and `fiat-receipted-delivery` must bind the current
`hexctl.py` digest recorded in this run's reconstructed tree.

The implemented tree must pass focused tests, the source reporter, valid and
invalid fixture checks, Promise sync/check/coverage, root tests, Phylax,
Ephoros, Hypomnema, per-file Imprimatur and Brevitas, Horos, JSON/Python syntax,
and cached plus working diff checks. A Warden reviews each risk below and adds
every finding, reproduction, remedy, guard, signed identity, and final result
to `audit/AUDIT.md`.

```risk-register
raw-descriptor | hostile capture fields reach persistence | validate and revalidate before output
report-path | caller controls report output | canonical confinement and descriptor-walk checks
receipt-drift | source, copy, or receipt bytes differ | compare recorded SHA-256 values
terminal-bytes | generated Markdown changes terminal newline | require exact `2e 0a`
authored-escape | prose contains byte `5c 6e` | scan exact bytes before receipt
partial-tree | a predecessor is omitted | assert complete 25-ID map before gates
adr-allocation | decision number already has an owner | preserve ADR-017 and allocate ADR-018
coverage-drift | Promise sources or hashes become stale | bind current files and selectors
receipt-mutation | receipted source bytes are edited | halt and start a new aggregate
detached-tree | parent lacks ignored receipt artefacts | narrow absent-receipt skip only
base-divergence | artefacts and controller use different starts | compare every declared identity
guard-evidence | test-only fix cannot earn a real parent failure | preserve red evidence and report honest verdict
```

## 6. Alternatives

1. Apply CARRYOVER packets one at a time and test each partial tree. Rejected:
   it creates misleading acceptance evidence and repeats work.
2. Edit C11's receipted source runbook to waive `--require-guard`. Rejected:
   that breaks the receipt relation.
3. Reconstruct one C12 tree and make the test-only Elenchus verdict explicit.
   Chosen: it preserves the failure evidence without fabricating a guard.

## 7. Disciplines and decision homes

Phylax covers hostile data and report paths. Ephoros covers bounded reporter
outcomes. Hypomnema covers ADR-018, receipts, carryover, and audit records.
Metron does not apply because no performance claim is made. Elenchus covers
red-first causal guards and the bounded test-only exception above. Sapheneia
shapes the new audit record without changing protected evidence.

## 8. Signals and questions

The source reporter answers whether the complete selected capture surface ran
without an error, failure, or skip. The direct report path check answers whether
the artifact stayed beneath the active worktree. The detached comparison answers
whether a causal repair has a real parent failure, an honest `passed` test-only
boundary, or an infrastructure refusal. The receipt checks answer whether the
same source, copy, and controller bytes were used. The audit record answers
which risk received evidence and what remains unknown.

## 9. Boundaries, per capability

The capture runtime may inspect only the bounded descriptor input and must not
persist raw candidate bytes. The writer accepts only revalidated accepted
results. The reporter may create one new confined output file below its current
worktree. Elenchus may create a relative descendant only in its detached tree.
The controller receives receipts and signed identities, not a claim that a
partial tree or an unrun external system succeeded.

## 10. The budget, or its absence

No performance budget applies. This run makes correctness, privacy, receipt,
and evidence claims only; it does not claim a timing, memory, gas, or throughput
improvement.

## 11. The fail-closed posture

Any malformed descriptor, raw field, unconfined report path, missing guard map,
stale coverage digest, receipt mismatch, incorrect tail byte, textual escape,
source mutation, base mismatch, failed gate, or unexplained reporter outcome
blocks the dependent transition. A test-only repair never invents a parent
assertion failure: it preserves red reproductions and states the structured
comparison verdict.

## 12. Decisions and their homes

ADR-018 holds the capture-profile decision. ADR-017 remains its unrelated
durable-agent-prose predecessor. This study and its runbook hold the one-tree,
receipt, base, and Elenchus construction rules. `audit/AUDIT.md` holds audit
findings and their evidence. CARRYOVER-12 holds cross-run aggregate prior art.

## 13. Carry-forward

At a configured final audit round with any finding, construct and post
`435-CARRYOVER-13.md` as a full aggregate of this packet, every new finding and
remediation, audit counts, signed fixed-tree identities, receipt digests,
unresolved leads, and check results. The next Mason applies that one aggregate
to one tree before every verification command.
