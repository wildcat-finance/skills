## Architecture and assets

`Sound` exposes a compact accounting model implementing two imported observable interfaces, although those interface definitions are outside the supplied bytes and their full requirements cannot be established (`plugins/pandects/specimens/Sound.sol:L4-L5`, `plugins/pandects/specimens/Sound.sol:L38-L38`).

Visible state comprises:

- A synthetic, immutable asset identifier; no token contract or balance integration is shown (`plugins/pandects/specimens/Sound.sol:L62-L65`).
- An internal logical clock, held assets, principal debt, accrued interest, lender claims, protocol fees, and reserved assets (`plugins/pandects/specimens/Sound.sol:L67-L73`).
- Parallel dynamic arrays `owedAt` and `paidAt`, apparently representing withdrawal-queue observations, but their element semantics and synchronization are not visible (`plugins/pandects/specimens/Sound.sol:L75-L76`).

Inputs passed through `bounded` are reduced modulo `1e30`; this is not a saturating cap, so `1e30` maps to zero (`plugins/pandects/specimens/Sound.sol:L39-L39`, `plugins/pandects/specimens/Sound.sol:L78-L80`). Time-step and queue constants are `365 days` and `8`, respectively, but enforcement is outside the excerpt (`plugins/pandects/specimens/Sound.sol:L51-L60`).

## Observable boundaries and trust assumptions

The external read boundary exposes held assets, combined principal-plus-interest debt, lender claims, fees, reservations, available borrowing capacity, and the internal clock (`plugins/pandects/specimens/Sound.sol:L84-L113`). `borrowableAssets` derives availability as `max(held - reserved, 0)`, avoiding underflow and preventing reported availability when reservations exceed holdings (`plugins/pandects/specimens/Sound.sol:L104-L109`).

All accounting fields are internal, so callers must trust unseen mutation paths to maintain their relationships. The excerpt contains no access control, deposit, borrowing, repayment, accrual, reservation, or claim-payment implementation. The comments describe intended operations and simple, principal-only interest, but those descriptions are not executable evidence within this range (`plugins/pandects/specimens/Sound.sol:L12-L25`, `plugins/pandects/specimens/Sound.sol:L27-L34`).

The system also trusts its own `clock` rather than `block.timestamp`; who may advance it and whether advancement is monotonic cannot be established (`plugins/pandects/specimens/Sound.sol:L27-L30`, `plugins/pandects/specimens/Sound.sol:L67-L67`).

## Candidate invariants and attack surfaces

Candidate conservation law: `held + principal + interest == claims + fees`, based on the documented balance-sheet movements. This cannot be proven without initialization and mutation code (`plugins/pandects/specimens/Sound.sol:L18-L25`, `plugins/pandects/specimens/Sound.sol:L67-L73`).

Other candidate invariants are:

- `reserved <= held`, although the observable deliberately remains safe if violated.
- `borrowableAssets == held - reserved` when `held > reserved`, otherwise zero.
- `totalDebt == principal + interest`.
- Queue lengths remain at most `8`, and `owedAt`/`paidAt` remain structurally aligned.
- Clock advancement is monotonic and each increment is at most `365 days`.
- Interest is linear in elapsed time and calculated only from principal.

Visible arithmetic risks are limited but real: `principal + interest` can revert on overflow, while `held - reserved` is guarded (`plugins/pandects/specimens/Sound.sol:L88-L90`, `plugins/pandects/specimens/Sound.sol:L107-L109`). Modulo bounding can create discontinuities exploitable by callers if unseen operations treat bounded values as faithful user amounts.

## Establishment limits

No authorization model, payable or token-transfer boundary, event surface, constructor state, queue observation functions, or state-transition logic is supplied. Consequently, solvency, conservation, fee correctness, accrual path independence, queue liveness, claim payment safety, reentrancy resistance, and enforcement of `CEILING`, `MAX_STEP`, or `MAX_CLAIMS` cannot be established from this excerpt.