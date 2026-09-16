# Fiat #1660 demonstration: GitHub signature refusal

This record is the output of the Step 1 prover on the current step tree.

```text
candidate | precheck-signing-key
command | python3 tests/prove_signature_only_refusals.py --candidate precheck-signing-key --out .hexaemeron/step-1-signature-refusal-report.json
criterion | signature-refusal-preserved
exit | 0
schema | protasis-design-report/v1
unit | boolean
value | true
```

The prover checked three source-bound specimens: an unsigned commit, an empty-tree
object altered after signing while carrying the harvested signature, and GitHub
web-flow commit `77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883`. The web-flow object
reports `%GK` `B5690EEEBB952194`; the other known GitHub key is
`4AEE18F83AFDEB23`. Each specimen was refused with Fiat's existing signature
message, and the prover wrote the closed report at
`.hexaemeron/step-1-signature-refusal-report.json`.

The run used the current operator keyring. In this environment,
`git verify-commit 77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883` exits `0` and
reports `B5690EEEBB952194` as GitHub's key. That success is the regression
boundary: `verify_local_commit` reads `%GK` from the exact object before either
ordinary or native verification, so keyring trust cannot admit a GitHub rewrite
as a local commit. The prover skips GitHub-keyed commits while searching for a
local signer and leaves exit `3` with no report when that local signer
precondition cannot be established.

This evidence does not establish authorship or publication authority. GitHub's
verification remains separate platform evidence, and no GitHub key or trust
material was added by the demonstration.
