# Optimisation catalogue

<!-- marketplace-context:start -->
> **Marketplace context: Hermes.** Hermes measures one Solidity gas optimisation class at a time and rejects the candidate when its Foundry evidence does not clear every gate. Use Pandects for credit-specific laws, or Hexaemeron's audit skills for a broader security review. **Current frontier:** Hermes's twelve optimisation classes name 62 of the corpus's 120 rules, so 58 documented rules cannot be selected as candidates.
<!-- marketplace-context:end -->

Use this list to nominate one Gate 2 class. Search for candidates, make a prediction, then let Hermes measure it. A plausible compiler story does not count as a result.

| Hermes class | Candidate idea | Usual risk | Checks before trying it |
| --- | --- | --- | --- |
| `storage-load-caching` | Hoist repeated `SLOAD`s into locals and reuse already-read struct fields | Low | Check that no call or state write between reads can change the value |
| `calldata-memory` | Change read-only external parameters from `memory` to `calldata`; avoid needless copies | Low | Confirm the public signature and selector stay unchanged |
| `custom-errors` | Replace revert strings with custom errors | Low | Find tests and callers that inspect revert data; record bytecode and runtime effects |
| `loop-arithmetic` | Cache `.length`, remove repeated indexing work, or hoist an invariant out of the body | Low-medium | Find real loops first; on 0.8.22 and later a canonical increment is already unchecked, which MYTH-02 in the corpus rejects wrapping again |
| `constants-immutables` | Move values from storage to `constant` or `immutable` | Medium | Expect a layout change; frozen contracts cannot take this class |
| `external-call-reduction` | Collapse duplicate calls or cache stable return data | Medium | Prove the target is unchanged across intervening calls, callbacks, and state writes |
| `event-packing` | Reduce event data or indexed arguments | Medium | Confirm indexers and off-chain consumers can take the event change |
| `storage-packing` | Narrow or reorder fields to share slots | High | Use only outside the frozen set; declare and record the layout difference |
| `unchecked-arithmetic` | Remove checked arithmetic where bounds prove wraparound impossible | High | Treat persistent state, asset accounting, permissions, external-call parameters, time and rounding as sensitive; run Gate 6 |
| `control-flow` | Reorder branches, remove duplicate predicates, or change `public` to `external` | Medium | Inspect selectors and measure every affected dispatch path; one function may get cheaper while another gets dearer |
| `hashing-encoding` | Remove duplicate encoding or hashing work and prefer fixed-width operations where semantics match | Medium | Compare exact bytes, collision assumptions, and downstream signature/domain use |
| `assembly` | Replace Solidity with a small assembly section | High | Keep this class separate from unchecked arithmetic; prove memory safety, returndata handling, and revert behaviour |

## Which rules name which class

Generated from the corpus and held to it by the Hermes suite. `verify` takes the rule id, and the rule decides the class.

<!-- corpus-index:start -->
- `assembly`: CTL-18, MEM-06, MEM-08, MEM-10, MEM-11, MEM-12, MEM-13, YUL-01, YUL-02, YUL-03, YUL-04, YUL-05, YUL-06, YUL-07, YUL-08, YUL-09, YUL-10, YUL-11, YUL-12, YUL-13, YUL-14
- `calldata-memory`: MEM-01, MEM-02, MEM-03, MEM-04, MEM-05, MEM-07, MEM-16
- `constants-immutables`: CTL-12, STO-15, STO-16
- `control-flow`: CTL-01, CTL-14, CTL-15, EXT-10, STO-13, STO-14, STO-21
- `custom-errors`: EXT-01, EXT-02, EXT-03
- `external-call-reduction`: EXT-04, EXT-09
- `event-packing`: EXT-11
- `hashing-encoding`: MEM-14
- `loop-arithmetic`: CTL-03, CTL-04, CTL-13, STO-11
- `storage-load-caching`: STO-05, STO-09, STO-10
- `storage-packing`: STO-01, STO-03, STO-04, STO-06, STO-07, STO-08, STO-17, STO-18
- `unchecked-arithmetic`: CTL-05, CTL-06

58 of the 120 rules name no class. They constrain how a run is conducted, or they are architecture, so no candidate implements them and `verify` refuses them with that reason. Every `CMP` and `DEP` rule is one of them, as is every `TRN` rule, because no class names transient state.
<!-- corpus-index:end -->

## Quick source searches

Run searches from the Foundry root and adapt names to the repository:

```bash
rg -n 'for\s*\(|while\s*\(' src
rg -n 'delegatecall|Clone|proxy|Proxy|hook|Hook|RoleProvider|factory|Factory' src
rg -n '\bunchecked\b|\bassembly\b' src test
rg -n 'memory' src
rg -n 'require\([^,]+,\s*"|revert\("' src
```

Repeated reads deserve a manual pass because source search cannot tell an `SLOAD` from a cached local. Trace the function and mark every external call or write between reads before hoisting anything.

## Pick in this order

Start with repeated storage reads, calldata copies, and custom errors. Move to loop mechanics or duplicate external calls once the easy measurements are exhausted. Leave storage packing, unchecked arithmetic, and assembly until the saving is worth their proof cost.

Check stateless libraries early. They cannot break an inherited storage layout, though their callers, arithmetic, ABI, and tests still go through every Hermes gate.

## Keep compiler settings separate

Treat a Solidity version change, `optimizer_runs`, `via_ir`, or EVM-version change as its own experiment from a clean baseline. It reprices too much code to share attribution with a source-level class. Run the gas diff, full tests, layout and method checks, and record deployed bytecode size with `forge build --sizes`.

## Noise and target selection

Pin the fuzz seed for comparable gas runs, then use the unpinned Gate 4 run to catch seed overfitting. Deterministic unit-test deltas may be small and still real. Gas deltas from `test/Fuzz.t.sol` or a named invariant test need another measurement when they move across repeated seeds.

Declare target expressions before the candidate is measured. An unexpected saving means the prediction was wrong; inspect it before acceptance. Hermes rejects every regression, including rows outside the declared target set.
