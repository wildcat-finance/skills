# Action comparison

The union contains 271 concrete contract/signature contexts: 130 added, 2 removed, 93 changed and 46 unchanged. The deployed source has 141 actions; the candidate has 269. Inheritance creates several contexts for the same selector, so these counts do not describe deployments or newly introduced selectors.

| Disposition | Count | Meaning |
| --- | ---: | --- |
| Added | 130 | Candidate-only concrete runtime context or canonical signature |
| Removed | 2 | Old OpenTermHooks and FixedTermHooks `onExecuteWithdrawal` signatures |
| Changed | 93 | Reviewed access, state/effect, value-flow or named-callee/event semantics differ |
| Unchanged | 46 | Reviewed local behavior and relevant helper paths remain within the stated comparison boundary |

## Changes that affect consumers

The two removed withdrawal callbacks gain an expiry argument in the candidate. Their replacements appear as added signatures; this classification does not imply the withdrawal capability disappeared.

Existing market selectors also change. The candidate introduces operational borrower transfer and principal resolution, floors scaled amounts, checkpoints assets for settlement, and changes several event arguments. The new revolving runtime inherits common selectors while overriding accounting for drawn principal and commitment fees.

Hook authority, credential/provider handling, minimum-deposit enforcement and transfer admission change. PeriodicTermHooks adds window and delayed APR-reduction policy. The new provider contracts and factories supply additional concrete runtime contexts.

Factory and wrapper changes require caller/callee review. The wrapper moves market-token claims; it does not forward deposits or withdrawal queues as an underlying market action. Factory discovery events can follow constructor and creation-callback events in the same transaction. Registry principal changes do not automatically rewrite an existing market borrower or escrow namespace.

## Complete records and limits

[comparison.json](comparison.json) gives every union member its disposition, reason, selectors and citations. [linkage.json](linkage.json) preserves per-action access, effects, value flows, helper paths and local event conditions. [Cross-system links](evidence/cross-system-links.json) separate conditional named implementations from arbitrary configured addresses.

The [literal diff](entry-points.diff) compares the complete generated Markdown maps. Formatting, moved source lines and citation changes appear there even when a semantic row is unchanged.

## Comparison boundary

These records compare source semantics at the two immutable commits. They do not establish bytecode equivalence, deployed configuration, gas behavior, runtime trace equivalence, lender solvency or a release decision.
