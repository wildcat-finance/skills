![Janus](./assets/characters/janus.png)

# JANUS

<!-- marketplace-context:start -->
## In one line

Janus checks a contract hook at the host threshold it crosses: the observations and changes the host permits before and after the action, plus the state it must never touch.

**Current frontier.** Janus ships the Wildcat v2.5 host adapter and its seven gates against modeled hooks, and no second host adapter yet shows the manifest format holds for another callback model.

**Next Fiat job.** Use /hexaemeron:fiat to ship a second host adapter for a different callback model, added only after the Wildcat adapter's suite passes, so the manifest format is shown host-neutral rather than asserted; accept it when the second adapter's honest hook passes, its hostile hooks are each caught, and the shared harness runs both adapters green. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## START HERE

Use Janus when a protocol lets hooks or callbacks run around a host action and
the ABI alone does not say what those modules may observe or change. A manifest
and host adapter turn that policy into seven bounded conformance gates and
Markdown or SARIF findings.

The current implementation is proved against the Wildcat v2.5 hook seam and
modelled hostile hooks. No second host adapter yet establishes that the same
manifest model generalises to another callback design, and a passing Janus run
is not a whole-protocol security verdict.

## PLACE IN THE COLLECTIVE

Janus owns the hook-to-host effect boundary. Pandects can supply economic laws
that the host transition must preserve; Hermes can measure a gas change inside
the implementation; and the Pashov suite can audit the contracts. Those
siblings do not decide which hook effects the host permits, and a passing Janus
manifest is not a whole-protocol security verdict.

Synkrisis compares validated run observations, and it does not carry Janus
conformance results into a wider safety claim. Its findings suggest one named
owner and cannot authorise a hook change.

A conformance suite for what a contract hook may observe and change around a
host action.

A host protocol calls a hook before and after an action, and the interface
says only which function runs. It does not say whether the hook may move value,
write host state, consume all remaining gas, change an authorisation result, or
leave a user unable to exit. That policy is otherwise spread across
implementation code, comments, and the assumptions of whoever wrote the first
hook. A new module can satisfy the ABI and still break the host's economic
contract.

## HOW IT WORKS

A host adapter exposes a host's actions, the state that matters, and its
economic roles. A manifest, JSON checked against a schema, declares what a hook
may observe and change at each threshold, its rollback rule, its gas budget,
and the liveness a user's exit depends on. A stateful Foundry harness drives
ordinary and hostile sequences, records the real storage writes, call targets,
value movements, and gas across each threshold, and fails when the observed
delta exceeds the manifest. A deterministic unit mode runs the same checks over
fixed sequences.

The gates read the manifest rather than a copy of it. A reader picks the
threshold by action name, never by position, and resolves each permitted call,
storage scope and value movement into concrete addresses through the host
adapter's own name table.

Three details of that resolution decide what a permit means. The account symbol
of a call target or an external slot is the text before the first `.`, and the
suffix is documentation; a value movement's names carry no suffix, so a dot
inside one is part of the name. Enforcement is account-granular, so a permit
written per slot or per function is enforced per account, and call kind is the
one dimension carried through. A `staticcall` entry admits nothing
state-changing, though its symbol must still resolve.

Resolution fails closed. A missing or duplicated action, an unresolvable
symbol, a blank account symbol, a zero address, and a name with more than one reading
each abort with a named error, because a permitted set that silently
lost an entry would reject everything and read as a passing gate.

## WHAT IT SHIPS

- the hook-manifest JSON schema and a stdlib Python validator;
- the Solidity host-adapter interface and the state-delta recorder;
- the stateful Foundry harness and the deterministic unit mode;
- five hostile reference hooks, one each for callback re-entry, gas grief,
  value redirection, storage mutation, and stale authorisation;
- the Wildcat host adapter, a faithful model of the v2.5 market-to-hook seam
  with an honest hook that passes every applicable gate; and
- human and SARIF reports linking each violation to a manifest rule and a trace.

## THE SEVEN GATES

1. Permitted effects are enumerated; an omitted write, call target, or value
   movement is forbidden rather than implicitly accepted.
2. Value conservation is checked from balances and claims, independent of what
   the calls return.
3. Exit gets a liveness property, tested after credential expiry, provider
   removal, sanctions changes, and hook failure.
4. Revert behaviour is part of conformance: state and value after nested or
   partial failure must match the host's declared rollback rule.
5. Gas grief is exercised with hooks that burn gas, expand return data, and
   build expensive callback paths.
6. Re-entry crosses actions: a callback enters a different host action, not
   only the one that invoked the hook.
7. A host adapter limits every result; passing the Wildcat suite makes no claim
   about another protocol's callback model.

## DAY TO DAY

**Developers.** A hook is written for a market and has to satisfy more than the
ABI. Declare the effects it is allowed in a manifest, run the harness, and see
whether the hook wrote a slot, called a target, moved value, or griefed gas
that the manifest did not permit, before the hook reaches an auditor.

**Security and audit.** A hook arrives for review beside lender funds and
borrower permissions. The host's suite tests that an honest hook works; Janus
tests the boundary the type system cannot express. Its hostile reference hooks
prove the gates catch callback re-entry, gas grief, value redirection, storage
mutation outside the declared slots, and stale authorisation, and the exit gate
shows a user can still leave after a credential lapses or a provider is removed.

## USE

Janus needs [Foundry](https://getfoundry.sh/) and the exact interpreter in the
suite [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
The harness has no external Solidity dependency, and the validator and reporter
use only the standard library. Ask:

```text
Use $janus to check this hook against a conformance manifest for what it may observe and change around a host action.
```

The gates, the manifest fields, and the refusals live in
[Janus's `SKILL.md`](./skills/janus/SKILL.md).
