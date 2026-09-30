# Commit supersession demonstration

Issue: [skills#2014](https://github.com/wildcat-finance/skills/issues/2014).

## Run

Run `python3 -m unittest plugins.hexaemeron.tests.test_fiat_commit_supersession -q` from the repository root. The suite creates disposable Git repositories and signed OpenPGP commits. The joined case is `EffectiveCommitTests.test_joined_disposable_verify_checkpoint_and_push`.

## Observed

The joined case records one implementation commit and two audit fixes commits whose committer email is absent from the signing key's user IDs. It builds a sibling chain with three different, pairwise identical Git trees and matching committer user IDs. A closed GitHub REST fixture answers for `wildcat-finance/skills` and each exact replacement SHA. It first returns `verified: false`, `reason: no_user`: the locally eligible replacement receives no supersession receipt. It then returns `verified: true`, `reason: valid` for all three replacements. The controller appends three supersession events without changing the original ledger prefix, passes `verify_run`, retains all six Git objects in checkpoint refs, and records `done push` with only the three replacement SHAs in its effective and GitHub-verified range. A second `verify_run` passes after the push receipt.

Other cases refuse an unequal tree, wrong parent or order, an old SHA still in the Step branch, a moved branch, an unverified replacement, a duplicate map and interrupted append. The fresh signed fixture refuses a mismatched committer at its first implementation receipt. Checkpoint bundle restoration preserves the old and replacement objects while coverage requires only the replacements.

## Boundary

The GitHub responses in this suite are fixtures. They prove exact repository and SHA binding in the controller path, not live platform eligibility. At integration, `fiat_commit_supersession_proof.py --candidate append-only-map --criterion platform-readback --report <path>` reruns the suite, verifies the controller, and asks GitHub about every SHA in the pushed final Step receipt before it writes a conformance report. That live report remains pending until the Step is published. A matching local key user ID is readiness evidence only; GitHub decides account and verified-email eligibility.
