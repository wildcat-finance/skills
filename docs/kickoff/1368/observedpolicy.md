# Protocol-observed disclosure and conclusion policy

Issue: https://github.com/wildcat-finance/skills/issues/1487, a prerequisite
child of https://github.com/wildcat-finance/skills/issues/1368.

Dr Laurence E. Day, maintainer, decided this policy on 2026-09-16 by answering
four structured questions in the delivery session. The
[decision comment](https://github.com/wildcat-finance/skills/issues/1487#issuecomment-5695677707)
reproduces each question, every option offered and the option selected. The
delivery session posted it from his account; it is not a separate GitHub
review. [`evidence/decision.json`](evidence/decision.json) preserves the same
answers and binds that comment's 4,900 bytes by SHA-256.

Shoggoth drafted the role matrix under Probitas. The reviewer is the
independent agent the decision-maker chose. Its reports, naming the digests
each reviewed, are in [`evidence/review.json`](evidence/review.json) and the
body of the pull request that adds this record. The selected option also set
the merge condition: the delivery session merges once the required
`invariants` check passes.
[`observedpolicy.json`](observedpolicy.json) carries this policy in a form #1368
can check, with the SHA-256 of every input cited below. Every path and line is
at `ce514a2edc790b3a13e19ed847da7716ea39de67`.

## Decisions

| Question | Selected | Recommended when asked |
| --- | --- | --- |
| Who may receive a dossier or finding that names a real protocol-observed address? | Public, address-level | Private; synthetic in public |
| Which protocol-observed roles may feed a conclusion? | Debtor of record only | Debtor of record only |
| What may name the entity in a dossier whose subjects are protocol-observed? | Neutral role label | Neutral role label |
| Who should the record name as its reviewer? | Independent agent | Independent agent |

**Audience.** Findings drawn from public chain logs may be published, including
in this repository, provided every prohibited claim stays out. The trade stated
when the option was chosen: a public credit dossier on an address that never
asked for one can read as Wildcat vetting borrowers, which Probitas says Wildcat
does not do (`plugins/probitas/skills/probitas/SKILL.md:254-256`).

**Conclusions.** Conclusion-bearing only where the venue's own log names the
address as the account whose debt changed, and only for that address's own
sourced events inside stated coverage. Every other role is recorded as context
and feeds no conclusion.

**Entity name.** The entity field is built from role and venue, for example
`Borrower of record, Wildcat market 0x...`. No organisation name is taken from
a market name, registry entry, ENS name or explorer label. An organisation name
appears only when it declares the address, which makes that address `declared`.

## Roles

| Role | Venue-native field at the source revision | Feeds a conclusion? |
| --- | --- | --- |
| Debtor of record | Wildcat market `borrower` (`wildcat.py:246`); Aave v4 `borrower` (`aave_v4.py:146`); Euler v1 `borrower` (`euler_v1.py:73`); Euler V2 EVC owner, sub-account XOR-checked (`euler.py:140-148`, `euler.py:387-392`); Midnight `seller` on `borrow` (`morpho_midnight.py:78-82`, `:696-699`), `on_behalf` on primary exits (`morpho_midnight.py:260`, `:706-707`), `borrower` on liquidation (`morpho_midnight.py:279`, `:710-711`) | Yes: that address's own sourced debt events, inside stated coverage only |
| Wrapper, router or vault | A debtor contract holding positions for other accounts | Yes about its own position; no about anyone behind it |
| Payer | Midnight `payer` (`morpho_midnight.py:236`, `:263`, `:279`) | No; never becomes a borrower |
| Caller or actor | Aave v4 `caller` (`aave_v4.py:147-148`); Midnight `caller` (`morpho_midnight.py:231`, `:259`, `:270`, `:279`); Euler V2 `actor` (`euler_v2.py:124-125`) | No |
| Liquidator, receiver, lender or counterparty | Euler v1 `liquidator` (`euler_v1.py:75-76`); Midnight `receiver` (`morpho_midnight.py:237`, `:265`, `:275`, `:279`) and `buyer` (`morpho_midnight.py:80`, `:234`); Euler V2 `counterparty` (`euler_v2.py:126-127`) | No |
| Registry or label | Registry entry, market name, ENS name, explorer tag | No; never names an entity or upgrades a tier |

`wildcat.py`, `euler.py` and `morpho_midnight.py` are under
`plugins/probitas/scripts/probitas_lib/adapters/`. `aave_v4.py`, `euler_v1.py`
and `euler_v2.py` are under `plugins/tabularium/scripts/tabularium_lib/adapters/`.

Reading, not a selection: of the two primary exits only `exit_borrow_primary`
changes debt. `exit_lend_primary` closes lender units
(`morpho_midnight.py:71`), so its `on_behalf` is not read as a debtor of
record.

Never, for any role: a person; the counterparty declaring or controlling the
address; a link between addresses from behaviour, funding or timing; default,
full repayment, a score or a Wildcat verdict; completeness beyond stated
coverage.

## Claims

Each claim concerns one protocol-observed address.

| Id | Claim | Verdict |
| --- | --- | --- |
| `debtor-role` | A venue's own log names the address as the account whose debt changed in a cited event. | permitted |
| `debtor-events` | The address's own sourced debt events inside stated coverage, as the venue recorded them. | permitted |
| `wrapper-own-position` | A debtor contract holding positions for other accounts: its own position. | permitted |
| `context-role` | A non-debtor role recorded beside its sourced event as context. | permitted |
| `publication` | Publishing a finding drawn from public chain logs, including in this repository, when it makes no prohibited claim. | permitted |
| `role-label-entity` | A dossier entity built from role and venue. | permitted |
| `person` | A person named or implied behind the address. | prohibited |
| `counterparty-control` | The counterparty declared or controls the address. | prohibited |
| `behavioural-link` | The address is linked to another address through behaviour, funding or timing. | prohibited |
| `verdict` | The address defaulted or repaid in full, or carries a score or a Wildcat verdict. | prohibited |
| `beyond-coverage` | The address's record is complete beyond stated coverage. | prohibited |
| `payer-as-borrower` | A payer is a borrower. | prohibited |
| `non-debtor-conclusion` | A conclusion drawn from a payer, caller, actor, liquidator, receiver, lender or counterparty role. | prohibited |
| `beneficiary` | A conclusion about anyone behind a wrapper, router or vault. | prohibited |
| `registry-identity` | A registry entry, market name, ENS name or explorer tag names the address's entity or upgrades its tier. | prohibited |
| `label-entity-name` | An organisation name for the dossier entity taken from a market name, registry entry, ENS name or explorer label. | prohibited |

In the JSON, each claim's `rests_on` names the selected decision, role or list
behind it.

## Source and coverage

Every observed address keeps: venue, chain id, contract, tx hash, block, log
index, event, the role field that names it, route (and release for archive),
and the coverage window.

## Probitas at the source revision

These are observations for #1368, not decisions.

1. `PROVENANCE_TIERS` holds `declared`, `linked` and `inferred`
   (`plugins/probitas/scripts/probitas_lib/evidence.py:22`). `collect` builds
   only `declared` and `inferred` addresses
   (`plugins/probitas/scripts/probitas.py:89-90`).
2. Gate 1 treats every tier except `inferred` as on the record
   (`plugins/probitas/scripts/probitas_lib/gates.py:91-96`), and `render`
   places records only for `declared`, `linked` and `inferred`
   (`plugins/probitas/scripts/probitas_lib/render.py:464-481`). An evidence file
   edited to carry `protocol-observed` renders with none of its 15 demo records
   and still passes all five gates (reproduction under Evidence). That defect is
   [#1693](https://github.com/wildcat-finance/skills/issues/1693), a child of
   #1487.
3. No record from Probitas's venue adapters keeps a log index, and no record
   from either route keeps the role field that names its address. `Record`
   holds venue, address, provenance, claim, values, source, source kind,
   observation time and block (`evidence.py:152-162`). The Euler adapters read
   a log index and drop it (`euler.py:407`, `:477-486`;
   `plugins/probitas/scripts/probitas_lib/adapters/euler_v1.py:250`,
   `:467-477`), and the Wildcat query requests none (`wildcat.py:64-65`).
   Archive-route Aave v4 records keep one only inside `values.source_identity`
   (`plugins/alexandria/scripts/alexandria_lib/mappings/aave_v4.py:174`,
   `:189`; `plugins/alexandria/scripts/alexandria_lib/probitas.py:150`).
   Midnight's parsed events carry the API event id, block and transaction hash
   (`morpho_midnight.py:713-719`), but its debt-event records keep the block and
   hash without the event id (`:1041-1056`). This repository does not document
   whether that id's suffix (`:101-103`) encodes a log index. Under the source
   requirement, an observation needs a log index and the role field recorded
   before it places an address in the tier.
4. Tabularium names `borrower` and `caller` for Aave v4, `borrower` and
   `liquidator` for Euler v1, and `owner`, `account`, `actor` and
   `counterparty` for Euler V2. None is `payer`.
5. The policy leaves these Probitas rules in place: one tier per address
   (`evidence.py:406-414`), a coverage row naming its route for every
   registered venue (`gates.py:167-273`), gaps ahead of any summary
   (`gates.py:376-417`), no value key naming a person (`evidence.py:78-83`,
   `:239-244`) and no rating without a rubric (`gates.py:420-439`).

## Not decided here

- Fields the decision was not shown, such as Tabularium's Euler V2 `account`
  (`euler_v2.py:122`) and Morpho Blue's `user`
  (`plugins/probitas/scripts/probitas_lib/adapters/morpho.py:174-176`). Each
  needs its own mapping to a role, with file and line, before it places an
  address in the tier.
- How a debtor contract is shown to hold positions for other accounts.
- Dossier layout for observed addresses, beyond keeping them apart from
  declared addresses as #1368 requires.

## Evidence

| Output | SHA-256 |
| --- | --- |
| [`observedpolicy.json`](observedpolicy.json) | `265060f490c82c613b3862d294fedcbb8cc95c9599c46418a7832ec58c7c2c02` |
| [`evidence/decision.json`](evidence/decision.json) | `0f823c3b8a55052c61b3fe6cb1f4eb72514caa0d2e32dae31c6f95bb34abfb43` |
| [Decision comment](https://github.com/wildcat-finance/skills/issues/1487#issuecomment-5695677707) body | `16ffcea67bbec46a2c7f100c730244dbfddc5190105870077ff1a0f1a359244a` |

The twenty-two inputs, with byte counts and digests, are listed under `inputs`
in the JSON. From the repository root, this recomputes them against the source
revision:

```bash
python3 - <<'PY'
import hashlib, json, subprocess
policy = json.load(open("docs/kickoff/1368/observedpolicy.json"))
rev = policy["source_revision"]
for item in policy["inputs"]:
    data = subprocess.run(["git", "show", f"{rev}:{item['path']}"], capture_output=True, check=True).stdout
    assert (len(data), hashlib.sha256(data).hexdigest()) == (item["bytes"], item["sha256"]), item["path"]
print(len(policy["inputs"]), "inputs match", rev)
PY
```

It printed `22 inputs match ce514a2edc790b3a13e19ed847da7716ea39de67` when this
record was written.

This reproduces observation 2 from the repository root:

```bash
out="$(mktemp -d)"
python3 plugins/probitas/scripts/probitas.py collect --entity "Acme Trading Ltd" \
  --address 0xa1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1 \
  --fixtures plugins/probitas/tests/fixtures/demo --run-id demo --out "$out/evidence.json"
python3 - "$out/evidence.json" <<'PY'
import json, sys
path = sys.argv[1]
payload = json.load(open(path))
for item in payload["subject"]["addresses"] + payload["records"]:
    item["provenance"] = "protocol-observed"
json.dump(payload, open(path, "w"), indent=2)
PY
python3 plugins/probitas/scripts/probitas.py render "$out/evidence.json" --out "$out/dossier.md"
python3 plugins/probitas/scripts/probitas.py verify "$out/dossier.md" "$out/evidence.json"
```

`collect` wrote 15 records. `render` and `verify` both exited 0, `verify`
printed `pass` for all five gates, and the dossier held no record rows and did
not show the address.
