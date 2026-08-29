## Architecture and assets

`Sound` is an observable-only bounded credit-state model. It stores a synthetic asset identifier, system clock, held assets, principal, interest, lender claims, fees, reserved assets, and two withdrawal-related timestamp arrays (`owedAt`, `paidAt`) ([`Sound.sol:L53-L66`](plugins/pandects/specimens/Sound.sol:L53-L66)).

The visible asset-side accounting is `held`; debt is represented as `principal + interest`; the claim-side state is split between `claims` and `fees`. The excerpt does not expose mutation functions, queue accessors, or initialization, so no live accounting transition can be verified.

## Observable boundaries and trust assumptions

External consumers can read total assets, total debt, lender claims, fees, reserved assets, borrowable assets, and the model-controlled clock ([`Sound.sol:L72-L101`](plugins/pandects/specimens/Sound.sol:L72-L101)). These are the explicit integration boundary; callers must trust their values as reports of internal state rather than token balances or timestamp-derived facts.

`asset` is a deterministic nonzero placeholder, not evidence of an ERC-20 integration or custody relationship ([`Sound.sol:L53-L55`](plugins/pandects/specimens/Sound.sol:L53-L55)). `observedAt()` reports `clock`, so time is trusted to whatever unseen functions mutate it rather than `block.timestamp` ([`Sound.sol:L57`](plugins/pandects/specimens/Sound.sol:L57), [`Sound.sol:L100-L102`](plugins/pandects/specimens/Sound.sol:L100-L102)).

## Candidate invariants and attack surfaces

The intended accounting model describes conservation: deposits pair held assets with claims; borrow/repay move value between held assets and debt; interest increases debt and claims; fees move value between claims and fees; reserve earmarks without moving value ([`Sound.sol:L14-L21`](plugins/pandects/specimens/Sound.sol:L14-L21)). Candidate invariants therefore include:

- `totalDebt() == principal + interest` and `totalAssets() == held`, directly enforced by their getters ([`Sound.sol:L72-L77`](plugins/pandects/specimens/Sound.sol:L72-L77)).
- `borrowableAssets() == max(held - reserved, 0)`, directly implemented rather than stored ([`Sound.sol:L91-L97`](plugins/pandects/specimens/Sound.sol:L91-L97)).
- Reserved assets should not exceed held assets in valid reachable states; the getter masks a violation by returning zero borrowable assets instead of reverting.
- Interest should be simple and path-independent according to the comments, but this cannot be established without the unseen accrual implementation ([`Sound.sol:L23-L28`](plugins/pandects/specimens/Sound.sol:L23-L28)).

The main visible attack surface is semantic: external systems may treat these getters as authoritative solvency, liquidity, or queue-status signals. A corrupted or incorrectly updated `reserved` value can suppress borrowing capacity; a malformed unseen writer could break the intended partitions while getters still return internally consistent individual fields.

`bounded(amount)` reduces inputs modulo `1e30` ([`Sound.sol:L31`](plugins/pandects/specimens/Sound.sol:L31), [`Sound.sol:L68-L70`](plugins/pandects/specimens/Sound.sol:L68-L70)). If used by unseen state-changing functions, it silently aliases large amounts rather than rejecting them; usage and authorization cannot be established here.

## Establishment limits

`RATE`, `RATE_SCALE`, `MAX_STEP = 365 days`, and `MAX_CLAIMS = 8` are declared limits ([`Sound.sol:L40-L51`](plugins/pandects/specimens/Sound.sol:L40-L51)), but the supplied range does not establish enforcement. It also cannot establish access control, reentrancy posture, asset transfers, repayment/deposit behavior, withdrawal ordering, array bounds, fee recipient handling, or whether any intended conservation invariant holds across transactions.