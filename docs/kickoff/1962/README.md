# Wildcat V1 emitter declarations

Issue [#1962](https://github.com/wildcat-finance/skills/issues/1962) asks for
the V1 counterpart of the V2 emitter report from #1361. This directory holds
it:

- `emitters.json` is the table, source- and digest-bound.
- `emitters.md` is the same table rendered for a reader, byte-checked
  against the JSON.
- `scripts/emitter_declarations_v1.py` builds and checks it, and
  `tests/test_emitter_declarations_v1.py` holds its offline tests.

The V2 table in `docs/kickoff/1361/` is unchanged and still regenerates
byte for byte.

## Inputs

The scan reads every `.sol` file under `src/` in
`wildcat-finance/wildcat-protocol` at
`da74452aa7d1a0f024d99efd22cc6d950a8116b7`, the commit the registry row
`wildcat-v1-ethereum-mainnet` names. The emitter files are the two paths that
row lists, `src/libraries/MarketEvents.sol` (21 emitters) and
`src/spherex/SphereXProtectedEvents.sol` (5).

The builds are the six deployed V1 contracts the registry names, each read
as its Sourcify record on chain 1: the first market instance, the first
controller instance, the controller factory, the arch controller, the
sanctions sentinel and the lens. The factory, arch controller and sentinel
inputs equal the registry's pinned `build_inputs` digests, and the checker
refuses a build whose input differs. Each build keeps the source commit the
registry gives its component, so the sentinel (`6164ddd4`) and the lens
(`488b30d0`, best match) are not read as `da74452a` builds.

The market and controller builds are instance records, since Sourcify keeps
no separate record for the templates. `crosscheck` compiles the
registry-pinned factory input and shows their ABIs equal the ones that input
yields.

## Results

| Figure | Summary key | Value |
| --- | --- | --- |
| Emitters scanned | `emitters` | 26 |
| Rows (emitter and same-named declaration pairs) | `rows` | 37 |
| Rows checked against a deployed build's ABI | `abi_checked_rows` | 37 |
| Mismatch rows | `mismatch_rows` | 0 |
| Unreviewed entries | `unreviewed` | 0 |
| Rows no deployed build reaches | `unreached_rows` | 0 |
| Declarations with no assembly emitter | `declarations_without_emitter` | 33 |
| Declarations nothing under `src/` emits | `non_emitting_declarations` | 10 |
| Same-named declaration groups that disagree | `declaration_disagreements` | 4 |

Every scoped emitter agrees with every same-named declaration and with the
ABI of each build carrying that event. No assembly log site or `emit_`
function exists outside the two emitter files.

The findings are in the declarations, not the emitters.
`IWildcatArchController.sol` declares ten events that no contract under
`src/` emits, because the deployed arch controller does not inherit that
interface and emits its own declarations. Four of the ten disagree with the
declarations actually emitted:

| Event | Interface declaration | Emitted declaration |
| --- | --- | --- |
| `AssetBlacklisted` | `AssetBlacklisted()` | `AssetBlacklisted(address)` |
| `AssetPermitted` | `AssetPermitted()` | `AssetPermitted(address)` |
| `MarketAdded` | no indexed parameter | `controller` indexed |
| `ControllerAdded` | no indexed parameter | `controllerFactory` indexed |

A decoder built from `IWildcatArchController`'s ABI would compute the wrong
topic0 for the first two and the wrong topic layout for the other two. The
deployed arch controller's ABI carries only the emitted variants. The table
lists each group with what emits each variant and which builds' ABIs carry
it. The #1363 event catalogue already lists both `AssetPermitted` and
`AssetBlacklisted` signatures.

## Tools and commands

Run on 2026-09-28 with the interpreter `.python-version` pins, git, a clone of `wildcat-protocol`
fetched at the pin, and Sourcify's v2 API.

```sh
python3 scripts/emitter_declarations_v1.py build --from-git <clone> --out docs/kickoff/1962/emitters.json --markdown docs/kickoff/1962/emitters.md
python3 scripts/emitter_declarations_v1.py check --from-git <clone> --table docs/kickoff/1962/emitters.json --markdown docs/kickoff/1962/emitters.md
python3 scripts/emitter_declarations_v1.py check --from-https --table docs/kickoff/1962/emitters.json --markdown docs/kickoff/1962/emitters.md
python3 scripts/emitter_declarations_v1.py crosscheck --solc <solc 0.8.22>
python3 -m unittest tests.test_emitter_declarations_v1 tests.test_emitter_declarations
```

`build` wrote the table, and both `check` routes exited 0. `crosscheck` ran
solc `0.8.22+commit.4fc1097e` from `binaries.soliditylang.org`, binary
SHA-256 `8be0aeb74fc1b8213292a09a84cb524a403602526df87ecad5f5cd2a7ea7d089`,
the digest that site publishes. It exited 0: the factory input
`dbeb245c…` yields the market, controller, factory and sentinel ABIs the
builds carry, and the arch controller and sentinel inputs yield theirs. No
pinned input compiles the lens, and `crosscheck` says so. The two test
modules ran 95 tests offline, all passing.

## Rejection cases

The offline tests hold each rejection case on synthetic sources:

- `test_changed_source_is_refused_before_regeneration`
- `test_wrong_topic_is_a_preserved_mismatch_row`
- `test_wrong_arity_is_a_preserved_mismatch_row`
- `test_omitted_row_is_a_table_difference`

Neighbouring tests refuse a drifted Sourcify ABI, a Sourcify input the
registry does not pin, a registry emitter path the checker does not scan,
an added source file and a Markdown edit.

The same cases were also run against the real table, in a scratch clone of
`da74452a` with one commit per mutation:

| Mutation | Command | Result |
| --- | --- | --- |
| a line added to `IMarketEventsAndErrors.sol` | `check --ref <commit>` | exit 1, `source-drift` naming the file and both digests |
| `Deposit` topic0 literal changed | `build --ref <commit>` | row kept as a mismatch, classes `topic0` and `abi:WildcatMarket:topic0` |
| `emit_DebtRepaid` `log2` made `log3` | `build --ref <commit>` | row kept as a mismatch, classes `log-arity` and `abi:WildcatMarket:log-arity` |
| one row deleted from a copy of the table | `check` | exit 1, `table-difference` |
| none, sources at the sentinel's `6164ddd4` | `check --ref 6164ddd4` | exit 1, `source-drift` over 39 files |

## Limits

The table is a static comparison of source text, declarations and the ABI
Sourcify retains. It makes no runtime-fidelity, bytecode-identity,
capture-completeness or protocol-safety claim, and it answers no research
question. Runtime emitter fidelity is
[#1964](https://github.com/wildcat-finance/skills/issues/1964), which
consumes this table.

Reach is contract-level: an emitter counts as reached by a build when its
compilation target's inheritance chain calls it. Sub-word values written by
`mstore` get a note, not a grade, as in V2. Emit sites are attributed through
the emitting contract's inheritance chain, and a base outside `src/`, such as
Solady's `Ownable`, adds no declaration.
