# Wildcat reproduction recovery

## Preserve custody

Preserve private execution custody before resetting the Fiat controller. Saved
admission requires the original checkout fingerprint, owned Python interpreter,
all frozen consumed source/runtime resources, unchanged original inputs, exact
receipts and the independent public [summary](reproduction-summary.json) anchor.
The local custody locator and external-preservation record identify the retained
root and every outer/verifier stream by byte count and digest. Those private
paths and payloads do not belong in Git.

Saved positive admission is bound to the original checkout fingerprint. If controller reset removes that worktree, retained custody remains inspectable but cannot transfer positive admission to another checkout. A new checkout or fingerprint requires a new actual four-input matrix, independent verification and public anchor.

A fresh clone can run ordinary public parser and custody refusal controls. It
cannot infer the four-input proof from constructed controls or a missing private
bundle. The registered `ReleaseReproductionTests` admits saved actual observations
without launching a CLI. Missing, stale or mismatched evidence yields named
`EvidenceUnavailable`, status 2, zero tests and one setup error; no scalar proof
or observations sidecar is emitted. `complete: true` in the fixed unittest JSON
describes unittest completion alone. Use a fresh report path for each attempt.

## Preparation failures

The actual matrix completed once with status 0; no failed domain attempt was
replaced. Preparation attempts retain separate verdicts and known limitations:

- Ordinary copied-fixture mutation controls first failed with `PermissionError`.
  An unchanged reobservation preserved full streams and UTC. The repair changes
  permissions only on temporary copies; original public and retained inputs stay
  unchanged. A subsequent fixture-serialization mismatch was repaired by writing
  that temporary negative fixture in the required canonical JSON form.
- A fixed-script absence probe using `-I` returned 1 at sibling-module import,
  before admission. The unchanged parser requires its script import path. Fresh
  `-E -S -B` probes returned 2 with named `EvidenceUnavailable`, zero tests and
  one error. Neither probe belongs to the 52-operation denominator.
- The first ordinary failure and the first isolated-script import failure lack
  original separately recorded UTC receipts. Their preserved outputs and later
  qualified records do not reconstruct those missing timestamps. Later attempts
  have full streams, actual UTC and separate verdicts.

On signed candidate `4887f5cd94bb12c1bea5555e533dc7713382d9e9`, the native
Exit wrapper returned 0 while its registered broad-check child returned 1; Exit
remained unsettled. Only the child's stdout byte count (290,519) and SHA-256
`d22f6c1497c4f8bef5c1217996ebaad1f9fafd49c415f68b43538b59914cb09a`
were retained. Its individual failing check and cause remain unknown.

A later unchanged direct broad run returned 1 with full outer streams: sixteen
checks passed, and the Tabularium suite ran 378 tests with two failures and no
errors. The guide's repository-relative summary link escaped the installable
plugin boundary. The public bundle inventory omitted `reproduction.md`,
`reproduction-summary.json` and `recovery.md`. Both existing guards failed twice
unchanged. The repair names the summary's repository path without a plugin-local
link and regenerates the closed public file inventory with exact bytes and
digests. Existing guards and all 62 consumed source files remain unchanged.
These later findings do not establish the original native child's cause. Fresh
focused tests, suites and signed-head Exit receipts determine subsequent
admission; the failed Exit is separate from the successful 52-operation matrix
and four-test saved-admission proof.

## Re-execution boundary

The initial execution plan omitted eagerly imported admission support and package
source. It was superseded before execution by a new create-only plan covering
all 62 consumed source files and 1,220 runtime resources; the old plan and its
unexecuted verification remain preserved. Preparation cache prefixes were empty
exclusive directories. Actual execution used fresh exclusive prefixes whose
leaves were absent before and after each process under `-B`; these policies are
recorded separately.

Do not edit frozen consumed bytes to recover positive admission. A relevant
source/resource, interpreter, input or checkout identity change requires a new actual four-input
matrix, independent verification and public anchor. Keep failed attempts and
their full streams rather than overwriting their reports. Python instrumentation
does not establish OS containment, host hermeticity or recorder/provider
authenticity. Use the [consumer guide](../../../plugins/tabularium/docs/wildcat-canonical.md)
for the fresh report command and the ordinary controls.
