#!/usr/bin/env python3
"""Build actions.json and linkage.json for #1963 from public Git objects.

    python3 docs/kickoff/1963/evidence/producers/build_linkage.py \\
        --protocol CLONE --denominator docs/kickoff/1963/denominator-inputs.json --out DIR

CLONE is wildcat-finance/wildcat-protocol with commits da74452a, 6164ddd4 and
488b30d0 present and the lib/solady and lib/openzeppelin-contracts submodules
checked out at the gitlinks da74452a records. Every source location below is
found by a unique text anchor in those objects; none is typed by hand. The
accepted private inputs are byte-identical to these objects for every file
this script cites.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

CORE = "da74452aa7d1a0f024d99efd22cc6d950a8116b7"
SENTINEL = "6164ddd4c75ef6da2181e5623b99795b9829e31c"
LENS = "488b30d08c73a93be3e4bf99128c774997411d3a"
F = "WildcatMarketControllerFactory"
A = "WildcatArchController"
S = "WildcatSanctionsSentinel"
L = "MarketLensMixed"
COMMIT_OF = {F: CORE, A: CORE, S: SENTINEL, L: LENS}
_cache: dict[tuple[str, str], list[str]] = {}
PROTOCOL = Path(".")


def lines(input_id: str, path: str) -> list[str]:
    key = (input_id, path)
    if key not in _cache:
        if path.startswith("lib/"):
            data = (PROTOCOL / path).read_bytes()
        else:
            data = subprocess.run(["git", "-C", str(PROTOCOL), "show", f"{COMMIT_OF[input_id]}:{path}"],
                                  capture_output=True, check=True).stdout
        _cache[key] = data.decode().splitlines()
    return _cache[key]


def at(input_id: str, path: str, anchor: str, nth: int | None = None, home: str | None = None) -> str:
    """Return [input@]path:line for the anchor; it must be unique unless nth picks one."""
    hits = [index + 1 for index, text in enumerate(lines(input_id, path)) if anchor in text]
    if nth is None:
        if len(hits) != 1:
            raise SystemExit(f"anchor {anchor!r} in {input_id}:{path} matched {len(hits)} lines")
        line = hits[0]
    else:
        line = hits[nth - 1]
    prefix = "" if home in (None, input_id) else f"{input_id}@"
    return f"{prefix}{path}:{line}"


MB = "src/market/WildcatMarketBase.sol"
MK = "src/market/WildcatMarket.sol"
MC = "src/market/WildcatMarketConfig.sol"
MT = "src/market/WildcatMarketToken.sol"
MW = "src/market/WildcatMarketWithdrawals.sol"
SX = "src/spherex/SphereXProtectedRegisteredBase.sol"
SC = "src/spherex/SphereXConfig.sol"
CT = "src/WildcatMarketController.sol"
FA = "src/WildcatMarketControllerFactory.sol"
AR = "src/WildcatArchController.sol"
SE = "src/WildcatSanctionsSentinel.sol"
ES = "src/WildcatSanctionsEscrow.sol"
OW = "lib/solady/src/auth/Ownable.sol"


def ev(signature, emitter, ref, relation="direct", condition=None):
    return {"event": signature, "emitter": emitter, "relation": relation, "source_ref": ref, "condition": condition}


SPHEREX = {"call": "ISphereXEngine(sphereXEngine()).sphereXValidatePre and sphereXValidatePost",
           "limit": "called only when the engine slot is nonzero; the engine is set at runtime by the SphereX "
                    "operator, may revert the action and emits its own events outside this map"}
TOKEN = {"call": "SafeTransferLib on the market's underlying asset",
         "limit": "the asset is an arbitrary ERC20 chosen at market deployment; its own Transfer events and "
                  "transfer semantics are outside this map"}
SANCTIONS_LIST = {"call": "IChainalysisSanctionsList(chainalysisSanctionsList).isSanctioned via the sentinel",
                  "limit": "an external oracle decides the sanctioned branch at execution time"}


def accrual(home, relation="direct", emitter="WildcatMarket", prefix=""):
    """Events _getUpdatedState can emit before an action's own logic. Event lists are unordered."""
    p = prefix
    return [
        ev("InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)", emitter,
           at(F, MB, "emit_InterestAndFeesAccrued(", 1, home), relation,
           p + "when an expired pending batch's expiry differs from lastInterestAccruedTimestamp; accrues up to the expiry"),
        ev("InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)", emitter,
           at(F, MB, "emit_InterestAndFeesAccrued(", 2, home), relation,
           p + "when block.timestamp differs from lastInterestAccruedTimestamp; accrues up to block.timestamp"),
        ev("WithdrawalBatchExpired(uint256,uint256,uint256,uint256)", emitter,
           at(F, MB, "emit_WithdrawalBatchExpired(", None, home), relation,
           p + "when the pending withdrawal batch has expired"),
        ev("WithdrawalBatchClosed(uint256)", emitter, at(F, MB, "emit_WithdrawalBatchClosed(expiry)", None, home),
           relation, p + "when that expired batch is fully paid"),
        ev("Transfer(address,address,uint256)", emitter, at(F, MB, "emit_Transfer(address(this), address(0)", None, home),
           relation, p + "when available reserves are nonzero and an expiring or pending batch still owes an amount, "
                         "at most once per state update; the payment may round to zero; from the market to address(0)"),
        ev("WithdrawalBatchPayment(uint256,uint256,uint256)", emitter,
           at(F, MB, "emit_WithdrawalBatchPayment(", None, home), relation,
           p + "when available reserves are nonzero and an expiring or pending batch still owes an amount, at most "
               "once per state update; the payment may round to zero"),
    ]


def written(home, relation="direct", emitter="WildcatMarket", condition=None):
    return ev("StateUpdated(uint256,bool)", emitter, at(F, MB, "emit_StateUpdated(", None, home), relation, condition)


TOTAL_ASSETS = {"call": "IERC20(asset).balanceOf(market) through totalAssets()",
                "limit": "a staticcall that reverts the action when the asset call fails or returns other than 32 bytes"}
SENTINEL_KEY = ("NewSanctionsEscrow and SanctionOverride name the market's borrower as their key, but the market's "
                "createEscrow call produced them; the borrower did not act, unlike overrideSanction, whose first field "
                "is its caller")


def blocked(home, relation="direct", condition_prefix="", emitter="WildcatMarket"):
    """Events _blockAccount can emit."""
    c = condition_prefix
    return [
        ev("AuthorizationStatusUpdated(address,uint8)", emitter,
           at(F, MB, "emit_AuthorizationStatusUpdated(accountAddress, AuthRole.Blocked)", None, home), relation,
           c + "when the account is not already blocked"),
        ev("NewSanctionsEscrow(address,address,address)", "WildcatSanctionsSentinel",
           at(S, SE, "emit NewSanctionsEscrow(", None, home), "transitive",
           c + "when the blocked account holds market tokens and no escrow exists yet for (borrower, account, market)"),
        ev("SanctionOverride(address,address)", "WildcatSanctionsSentinel",
           at(S, SE, "emit SanctionOverride(borrower, escrowContract)", None, home), "transitive",
           c + "with that new escrow"),
        ev("Transfer(address,address,uint256)", emitter, at(F, MB, "emit_Transfer(accountAddress, escrow", None, home),
           relation, c + "when the blocked account holds market tokens; from the account to its escrow"),
        ev("SanctionedAccountAssetsSentToEscrow(address,address,uint256)", emitter,
           at(F, MB, "emit_SanctionedAccountAssetsSentToEscrow(", None, home), relation,
           c + "when the blocked account holds market tokens"),
    ]


def guard_sx():
    return "sphereXGuardExternal: SphereX engine pre and post validation when an engine is set"


def row(identity, disposition, *, guards=(), effects=(), flows=(), events=(), callees=(), attribution=(), gaps=(),
        refs=(), reason):
    return {"id": identity["id"], "disposition": disposition, "guards": list(guards), "state_effects": list(effects),
            "value_flows": list(flows), "events": list(events), "dynamic_callees": list(callees),
            "attribution": list(attribution), "gaps": list(gaps),
            "source_refs": list(dict.fromkeys([identity["source_ref"], *refs])), "reason": reason}


def market_rows(ids):
    """WildcatMarket: 23 state-changing actions and its implicit creation path."""
    h = F
    out, fam = {}, {}
    get = lambda sig: ids[(F, "WildcatMarket", sig)]  # noqa: E731
    acc = accrual(h)
    ws = written(h)
    nr = "nonReentrant: ReentrancyGuard"

    i = get("constructor()")
    out[i["id"]] = row(i, "mapped", guards=["deployed by WildcatMarketController.deployMarket through create2 with the stored init code; no caller check of its own"],
        effects=["reads IWildcatMarketController(msg.sender).getMarketParameters() and IERC20Metadata(asset).decimals()",
                 "writes immutables, name, symbol and the initial MarketState (scaleFactor RAY, not closed)",
                 "sets the SphereX engine slot"],
        events=[ev("ChangedSpherexOperator(address,address)", "WildcatMarket", at(h, SX, "emit_ChangedSpherexOperator(address(0), _archController)")),
                ev("ChangedSpherexEngineAddress(address,address)", "WildcatMarket", at(h, SX, "emit_ChangedSpherexEngineAddress(address(0), engine)"))],
        callees=[{"call": "IWildcatMarketController(msg.sender).getMarketParameters and IERC20Metadata(asset).decimals",
                  "limit": "the deploying controller and asset answer at creation time"}],
        attribution=["the market's own address is the create2 result; the deploying controller emits MarketDeployed"],
        refs=[at(h, MB, "IWildcatMarketController(msg.sender).getMarketParameters()"), at(h, SX, "function __SphereXProtectedRegisteredBase_init")],
        reason="WildcatMarket has no ABI constructor row; the inherited WildcatMarketBase constructor runs and both SphereX initialisation events fire unconditionally")
    fam[i["id"]] = ["creation"]

    i = get("approve(address,uint256)")
    out[i["id"]] = row(i, "mapped", guards=[nr, guard_sx()], effects=["allowance[msg.sender][spender] = amount"],
        events=[ev("Approval(address,address,uint256)", "WildcatMarket", at(h, MT, "emit_Approval(approver, spender, amount)"))],
        callees=[SPHEREX], attribution=["owner is msg.sender"],
        refs=[at(h, MT, "function _approve(")], reason="_approve emits Approval on every successful call; no state accrual runs")
    fam[i["id"]] = ["transfer"]

    i = get("borrow(uint256)")
    out[i["id"]] = row(i, "conditional",
        guards=["onlyBorrower: msg.sender == borrower", nr, guard_sx(),
                "reverts when the sentinel reports the borrower flagged by Chainalysis", "reverts on a closed market",
                "reverts when amount exceeds borrowableAssets(totalAssets())"],
        effects=["accrues interest and processes batches through _getUpdatedState", "_writeState recomputes isDelinquent"],
        flows=["asset moves from the market to msg.sender (the borrower)"],
        events=[*acc, ws, ev("Borrow(uint256)", "WildcatMarket", at(h, MK, "emit_Borrow(amount)"))],
        callees=[SPHEREX, TOKEN, SANCTIONS_LIST],
        attribution=["Borrow carries only the amount; the borrower is the market's immutable borrower, not an event field"],
        refs=[at(h, MK, "isFlaggedByChainalysis(borrower)"), at(h, MK, "asset.safeTransfer(msg.sender, amount)")],
        reason="StateUpdated and Borrow always fire on success; accrual and batch events depend on elapsed time and pending batches")
    fam[i["id"]] = ["borrowing"]

    i = get("changeSphereXEngine(address)")
    out[i["id"]] = row(i, "mapped", guards=["spherexOnlyOperator: msg.sender == _archController"],
        effects=["writes the SphereX engine storage slot"],
        events=[ev("ChangedSpherexEngineAddress(address,address)", "WildcatMarket", at(h, SX, "emit_ChangedSpherexEngineAddress(oldEngine, newSphereXEngine)"))],
        attribution=["the arch controller is the only permitted caller"],
        reason="one unconditional event; the function is not itself SphereX-guarded")
    fam[i["id"]] = ["administration"]

    i = get("closeMarket()")
    out[i["id"]] = row(i, "conditional",
        guards=["onlyController: msg.sender == controller", nr, guard_sx(),
                "reverts while unpaidBatches is nonempty when the call starts; the check precedes _getUpdatedState(), "
                "so a pending batch whose expiry has passed but that no state update has processed yet is processed "
                "after the check; if it stays partly paid it joins unpaidBatches and the market closes with it unpaid"],
        effects=["annualInterestBips = 0, isClosed = true, reserveRatioBips = 10000, timeDelinquent = 0",
                 "an expired batch processed inside the call can stay in unpaidBatches; "
                 "repayAndProcessUnpaidWithdrawalBatches then reverts with RepayToClosedMarket, so its unpaid "
                 "remainder cannot be withdrawn"],
        flows=["when assets fall short of total debts, the shortfall moves from the borrower to the market by transferFrom",
               "when assets exceed total debts, the excess moves from the market to the borrower"],
        events=[*acc, ws, ev("MarketClosed(uint256)", "WildcatMarket", at(h, MK, "emit_MarketClosed(block.timestamp)"))],
        callees=[SPHEREX, TOKEN],
        attribution=["the borrower pays or receives the settlement; no market event names either transfer"],
        refs=[at(h, MK, "asset.safeTransferFrom(borrower, address(this), totalDebts - currentlyHeld)"),
              at(h, MK, "asset.safeTransfer(borrower, currentlyHeld - totalDebts)")],
        reason="StateUpdated and MarketClosed always fire; accrual events are conditional and the settlement transfers emit only asset-side events")
    fam[i["id"]] = ["closure", "repayment"]

    i = get("collectFees()")
    out[i["id"]] = row(i, "conditional",
        guards=[nr, guard_sx(), "reverts when accruedProtocolFees is zero", "reverts when withdrawableProtocolFees is zero",
                "reverts on arithmetic underflow when totalAssets() is below normalizedUnclaimedWithdrawals"],
        effects=["accruedProtocolFees -= withdrawableFees"], flows=["asset moves from the market to feeRecipient"],
        events=[*acc, ws, ev("FeesCollected(uint256)", "WildcatMarket", at(h, MK, "emit_FeesCollected(withdrawableFees)"))],
        callees=[SPHEREX, TOKEN], attribution=["any caller may trigger it; funds always go to the immutable feeRecipient"],
        refs=[at(h, MK, "asset.safeTransfer(feeRecipient, withdrawableFees)")],
        reason="StateUpdated and FeesCollected always fire; accrual events are conditional")
    fam[i["id"]] = ["fee"]

    authorize_first = ev("AuthorizationStatusUpdated(address,uint8)", "WildcatMarket",
        at(h, MB, "emit_AuthorizationStatusUpdated(accountAddress, AuthRole.DepositAndWithdraw)"), "direct",
        "on the unsanctioned branch, when the account has no role yet and the controller reports it an authorized lender")
    ordinary = [ev("Transfer(address,address,uint256)", "WildcatMarket", at(h, MK, "emit_Transfer(address(0), msg.sender, amount)"), "direct",
                   "on the unsanctioned branch; mint from address(0)"),
                ev("Deposit(address,uint256,uint256)", "WildcatMarket", at(h, MK, "emit_Deposit(msg.sender, amount, scaledAmount)"), "direct",
                   "on the unsanctioned branch")]
    deposit_guards = [guard_sx(), "nonReentrant on _depositUpTo",
                      "unsanctioned branch: requires DepositAndWithdraw via _getAccountWithRole, granting it when the controller lists msg.sender",
                      "unsanctioned branch: reverts on a closed market or a zero scaled amount",
                      "sanctioned branch (the sentinel reports msg.sender sanctioned for this borrower): no role, closed-market or amount check runs"]
    for sig, prefix, extra, reason in (
            ("depositUpTo(uint256)", "on the sanctioned branch, ", [],
             "Transfer, Deposit and StateUpdated fire on the unsanctioned branch; a sanctioned caller is blocked and escrowed "
             "instead, and the call succeeds returning 0, even on a closed market"),
            ("deposit(uint256)", "only when amount == 0 and the sentinel reports msg.sender sanctioned, ",
             ["reverts with MaxSupplyExceeded unless the accepted amount equals amount; the sanctioned branch accepts 0, "
              "so there only deposit(0) succeeds"],
             "Transfer, Deposit and StateUpdated fire on the unsanctioned branch; a sanctioned caller reverts unless amount "
             "is 0, and at amount 0 the caller is blocked and escrowed and the call persists")):
        i = get(sig)
        out[i["id"]] = row(i, "conditional", guards=deposit_guards + extra,
            effects=["accrues state",
                     "unsanctioned branch: scaledBalance and scaledTotalSupply grow by the scaled amount; a first-time lender gains DepositAndWithdraw",
                     "sanctioned branch: the caller becomes Blocked and its market tokens move to its escrow"],
            flows=["unsanctioned branch: asset moves from msg.sender to the market",
                   "sanctioned branch: the caller's market tokens move to its (borrower, caller, market) escrow"],
            events=[*acc, *blocked(h, condition_prefix=prefix), authorize_first, *ordinary, ws],
            callees=[SPHEREX, TOKEN, SANCTIONS_LIST,
                     {"call": "IWildcatMarketController(controller).isAuthorizedLender", "limit": "the controller's lender set decides first-time authorization"}],
            attribution=["on the unsanctioned branch, msg.sender is both payer and recipient of the minted tokens; "
                         "the sanctioned branch mints and pays nothing", SENTINEL_KEY],
            refs=[at(h, MK, "function _depositUpTo("), at(h, MK, "IWildcatSanctionsSentinel(sentinel).isSanctioned(borrower, msg.sender)")],
            reason=reason)
        fam[i["id"]] = ["funding", "sanctions"]

    execution_events = lambda loop: [*acc,  # noqa: E731
        *blocked(h, condition_prefix=("per sanctioned account, " if loop else "when the account is sanctioned, ")),
        ev("NewSanctionsEscrow(address,address,address)", "WildcatSanctionsSentinel", at(S, SE, "emit NewSanctionsEscrow(", None, h), "transitive",
           ("per sanctioned account, " if loop else "when the account is sanctioned, ") + "when no asset escrow exists yet for (borrower, account, asset)"),
        ev("SanctionOverride(address,address)", "WildcatSanctionsSentinel", at(S, SE, "emit SanctionOverride(borrower, escrowContract)", None, h), "transitive",
           ("per sanctioned account, " if loop else "when the account is sanctioned, ") + "with that new asset escrow"),
        ev("SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)", "WildcatMarket",
           at(h, MW, "emit_SanctionedAccountWithdrawalSentToEscrow("), "direct",
           ("per sanctioned account" if loop else "when the account is sanctioned")),
        ev("WithdrawalExecuted(uint256,address,uint256)", "WildcatMarket", at(h, MW, "emit_WithdrawalExecuted("), "direct",
           "once per executed withdrawal" if loop else None),
        ws]
    for sig, loop in (("executeWithdrawal(address,uint32)", False), ("executeWithdrawals(address[],uint32[])", True)):
        i = get(sig)
        out[i["id"]] = row(i, "conditional",
            guards=[nr, guard_sx(), "reverts unless expiry < block.timestamp", "reverts when the withdrawable amount is zero"]
                   + (["reverts when the two arrays differ in length"] if loop else []),
            effects=["accrues state", "records normalizedAmountWithdrawn for the account and expiry",
                     "reduces normalizedUnclaimedWithdrawals", "blocks a sanctioned account"],
            flows=["asset moves from the market to the account, or to its asset escrow when the account is sanctioned",
                   "sanctioned branch: an unblocked account's remaining market tokens move to its (borrower, account, market) escrow"],
            events=execution_events(loop), callees=[SPHEREX, TOKEN, SANCTIONS_LIST],
            attribution=["any caller may execute on the account's behalf; the account, not msg.sender, receives the assets",
                         SENTINEL_KEY],
            refs=[at(h, MW, "function _executeWithdrawal("), at(h, MW, "asset.safeTransfer(escrow, normalizedAmountWithdrawn)")],
            reason="WithdrawalExecuted and StateUpdated fire on success; the sanctions branch and accrual add conditional events"
                   + ("; an empty array executes nothing but still emits StateUpdated" if loop else ""))
        fam[i["id"]] = ["execution", "sanctions"]

    i = get("nukeFromOrbit(address)")
    out[i["id"]] = row(i, "conditional",
        guards=[nr, guard_sx(), "reverts with BadLaunchCode unless the sentinel reports the account sanctioned for this borrower"],
        effects=["accrues state", "sets the account to Blocked and moves its scaled balance to an escrow"],
        flows=["market tokens move from the account to its sentinel escrow"],
        events=[*acc, *blocked(h), ws], callees=[SPHEREX, SANCTIONS_LIST],
        attribution=["permissionless: any caller may block a sanctioned account", SENTINEL_KEY],
        refs=[at(h, MC, "_blockAccount(state, accountAddress)")],
        reason="StateUpdated always fires; the blocking and escrow events depend on the account's prior role and balance")
    fam[i["id"]] = ["sanctions"]

    i = get("queueWithdrawal(uint256)")
    out[i["id"]] = row(i, "conditional",
        guards=[nr, guard_sx(), "requires at least WithdrawOnly via _getAccountWithRole", "reverts on a zero scaled amount",
                "reverts when the scaled amount exceeds the caller's scaled balance"],
        effects=["accrues state", "moves the scaled amount from the account into the pending batch", "opens a batch when none is pending"],
        flows=["market tokens leave the account balance for the withdrawal batch; no asset moves here"],
        events=[*acc,
                ev("AuthorizationStatusUpdated(address,uint8)", "WildcatMarket", at(h, MB, "emit_AuthorizationStatusUpdated(accountAddress, AuthRole.DepositAndWithdraw)"),
                   "direct", "when the account has no role yet and the controller lists it"),
                ev("Transfer(address,address,uint256)", "WildcatMarket", at(h, MW, "emit_Transfer(msg.sender, address(this), amount)")),
                ev("WithdrawalBatchCreated(uint256)", "WildcatMarket", at(h, MW, "emit_WithdrawalBatchCreated(expiry)"), "direct", "when no batch is pending"),
                ev("WithdrawalQueued(uint256,address,uint256,uint256)", "WildcatMarket", at(h, MW, "emit_WithdrawalQueued(")),
                ev("Transfer(address,address,uint256)", "WildcatMarket", at(h, MB, "emit_Transfer(address(this), address(0)"), "direct",
                   "when available reserves are nonzero after queueing; the payment may round to zero"),
                ev("WithdrawalBatchPayment(uint256,uint256,uint256)", "WildcatMarket", at(h, MB, "emit_WithdrawalBatchPayment("), "direct",
                   "when available reserves are nonzero after queueing; the payment may round to zero"),
                ws],
        callees=[SPHEREX, {"call": "IWildcatMarketController(controller).isAuthorizedLender", "limit": "the controller's lender set decides first-time authorization"}],
        attribution=["msg.sender is the withdrawing lender"],
        refs=[at(h, MW, "_applyWithdrawalBatchPayment(batch, state, expiry, availableLiquidity)")],
        reason="Transfer, WithdrawalQueued and StateUpdated always fire; batch creation, payment and accrual are conditional")
    fam[i["id"]] = ["withdrawal-queue", "batch-funding"]

    repay_event = lambda anchor: ev("DebtRepaid(address,uint256)", "WildcatMarket", at(h, *anchor))  # noqa: E731
    i = get("repay(uint256)")
    out[i["id"]] = row(i, "conditional",
        guards=[nr, guard_sx(), "reverts on a zero amount", "reverts on a closed market after the transfer and event"],
        effects=["accrues state after the payment"], flows=["asset moves from msg.sender to the market"],
        events=[repay_event((MK, "emit_DebtRepaid(msg.sender, amount);", 2)), *acc, ws],
        callees=[SPHEREX, TOKEN],
        attribution=["DebtRepaid names the payer (msg.sender), not the debtor; the market's borrower is the debtor only by inference"],
        refs=[at(h, MK, "function repay(uint256 amount)")],
        reason="DebtRepaid and StateUpdated fire on success; accrual events are conditional. A closed market reverts the whole call, including DebtRepaid")
    fam[i["id"]] = ["repayment"]

    for sig, anchor, what in (("repayOutstandingDebt()", "state.totalDebts().satSub(totalAssets())", "outstanding debt"),
                              ("repayDelinquentDebt()", "state.liquidityRequired().satSub(totalAssets())", "delinquent debt")):
        i = get(sig)
        out[i["id"]] = row(i, "conditional",
            guards=[nr, guard_sx(), f"reverts with NullRepayAmount when the {what} is zero", "reverts on a closed market"],
            effects=["accrues state"], flows=[f"the {what} moves from msg.sender to the market"],
            events=[*acc, repay_event((MK, "emit_DebtRepaid(msg.sender, amount);", 1)), ws],
            callees=[SPHEREX, TOKEN],
            attribution=["DebtRepaid names the payer (msg.sender), not the debtor"],
            refs=[at(h, MK, anchor), at(h, MK, "function _repay(")],
            reason="DebtRepaid and StateUpdated fire on success; accrual events are conditional")
        fam[i["id"]] = ["repayment"]

    i = get("repayAndProcessUnpaidWithdrawalBatches(uint256,uint256)")
    out[i["id"]] = row(i, "conditional",
        guards=[nr, guard_sx(), "reverts on a closed market",
                "reverts when totalAssets() is below normalizedUnclaimedWithdrawals plus accruedProtocolFees"],
        effects=["accrues state", "pays up to maxBatches unpaid batches from available liquidity, oldest first",
                 "removes a fully paid batch from unpaidBatches"],
        flows=["when repayAmount > 0, asset moves from msg.sender to the market"],
        events=[ev("DebtRepaid(address,uint256)", "WildcatMarket", at(h, MW, "emit_DebtRepaid(msg.sender, repayAmount)"), "direct", "when repayAmount > 0"),
                *acc,
                ev("Transfer(address,address,uint256)", "WildcatMarket", at(h, MB, "emit_Transfer(address(this), address(0)"), "direct",
                   "per unpaid batch processed while available liquidity is nonzero; the payment may round to zero; "
                   "from the market to address(0)"),
                ev("WithdrawalBatchPayment(uint256,uint256,uint256)", "WildcatMarket", at(h, MB, "emit_WithdrawalBatchPayment("), "direct",
                   "per unpaid batch processed while available liquidity is nonzero; the payment may round to zero"),
                ev("WithdrawalBatchClosed(uint256)", "WildcatMarket", at(h, MW, "emit_WithdrawalBatchClosed(expiry)"), "direct",
                   "per unpaid batch that becomes fully paid"),
                ws],
        callees=[SPHEREX, TOKEN],
        attribution=["DebtRepaid names the payer (msg.sender), not the debtor"],
        refs=[at(h, MW, "function _processUnpaidWithdrawalBatch(")],
        reason="StateUpdated always fires; repayment and batch events depend on repayAmount, liquidity and unpaid batches")
    fam[i["id"]] = ["repayment", "batch-funding"]

    for sig, emit, what in (("setAnnualInterestBips(uint16)", ("AnnualInterestBipsUpdated(uint256)", "emit_AnnualInterestBipsUpdated("), "annualInterestBips"),
                            ("setMaxTotalSupply(uint256)", ("MaxTotalSupplyUpdated(uint256)", "emit_MaxTotalSupplyUpdated("), "maxTotalSupply"),
                            ("setReserveRatioBips(uint16)", ("ReserveRatioBipsUpdated(uint256)", "emit_ReserveRatioBipsUpdated("), "reserveRatioBips")):
        i = get(sig)
        extra = (["reverts when the old or new ratio leaves required liquidity above assets"] if what == "reserveRatioBips"
                 else ["reverts when the value exceeds uint128"] if what == "maxTotalSupply" else [])
        out[i["id"]] = row(i, "conditional", guards=["onlyController: msg.sender == controller", nr, guard_sx(), *extra],
            effects=["accrues state", f"sets {what}"], events=[*acc, ws, ev(emit[0], "WildcatMarket", at(h, MC, emit[1]))],
            callees=[SPHEREX], attribution=["only the market's controller may call; the borrower acts through it"],
            reason=f"StateUpdated and {emit[0].split('(')[0]} always fire; accrual events are conditional")
        fam[i["id"]] = ["administration"]

    i = get("stunningReversal(address)")
    out[i["id"]] = row(i, "mapped",
        guards=[nr, guard_sx(), "reverts while the sentinel still reports the account sanctioned", "reverts unless the account is Blocked"],
        effects=["sets the account role from Blocked to WithdrawOnly"],
        events=[ev("AuthorizationStatusUpdated(address,uint8)", "WildcatMarket", at(h, MC, "emit_AuthorizationStatusUpdated(accountAddress, account.approval)"))],
        callees=[SPHEREX, SANCTIONS_LIST], attribution=["permissionless: any caller may restore an unsanctioned blocked account"],
        reason="one unconditional event; no state accrual runs")
    fam[i["id"]] = ["sanctions"]

    for sig, anchor in (("transfer(address,uint256)", None), ("transferFrom(address,address,uint256)", "allowed != type(uint256).max")):
        i = get(sig)
        events = [*acc, ws, ev("Transfer(address,address,uint256)", "WildcatMarket", at(h, MT, "emit_Transfer(from, to, amount)"))]
        if anchor:
            events.insert(0, ev("Approval(address,address,uint256)", "WildcatMarket", at(h, MT, "emit_Approval(approver, spender, amount)"),
                                "direct", "unless the allowance is type(uint256).max"))
        out[i["id"]] = row(i, "conditional",
            guards=[nr, guard_sx(), "reverts when either account is Blocked", "reverts on a zero scaled amount",
                    "reverts when the scaled amount exceeds the sender's scaled balance"]
                   + (["reverts when the allowance is insufficient"] if anchor else []),
            effects=["accrues state", "moves scaled balance between accounts"] + (["reduces the allowance"] if anchor else []),
            flows=["market tokens move between accounts; no asset moves"],
            events=events, callees=[SPHEREX],
            attribution=["from and to need no lender role; only Blocked accounts are refused"],
            refs=[at(h, MT, "function _transfer(")], reason="Transfer and StateUpdated always fire; accrual events are conditional")
        fam[i["id"]] = ["transfer"]

    i = get("updateAccountAuthorizations(address[],bool)")
    out[i["id"]] = row(i, "conditional",
        guards=["onlyController: msg.sender == controller", nr, guard_sx(), "reverts when any listed account is Blocked"],
        effects=["accrues state", "authorize sets DepositAndWithdraw; deauthorize downgrades DepositAndWithdraw to WithdrawOnly"],
        events=[*acc, ev("AuthorizationStatusUpdated(address,uint8)", "WildcatMarket", at(h, MC, "emit_AuthorizationStatusUpdated(accounts[i], account.approval)"),
                         "direct", "once per listed account"), ws],
        callees=[SPHEREX], attribution=["the controller relays the borrower's or a permissionless sync request"],
        reason="StateUpdated always fires; one AuthorizationStatusUpdated per account, none for an empty list")
    fam[i["id"]] = ["administration"]

    i = get("updateState()")
    out[i["id"]] = row(i, "conditional", guards=[nr, guard_sx()],
        effects=["applies interest, fees and batch processing to stored state"], events=[*acc, ws], callees=[SPHEREX],
        attribution=["permissionless keeper action"], reason="StateUpdated always fires; accrual and batch events are conditional")
    fam[i["id"]] = ["batch-funding"]
    return out, fam


def sx_init(home, input_id, emitter, relation="direct", condition=None):
    return [ev("ChangedSpherexOperator(address,address)", emitter,
               at(input_id, SX, "emit_ChangedSpherexOperator(address(0), _archController)", None, home), relation, condition),
            ev("ChangedSpherexEngineAddress(address,address)", emitter,
               at(input_id, SX, "emit_ChangedSpherexEngineAddress(address(0), engine)", None, home), relation, condition)]


def allowed_sender(home, condition):
    return ev("NewAllowedSenderOnchain(address)", "WildcatArchController",
              at(A, SC, "emit_NewAllowedSenderOnchain(newSender)", None, home), "transitive" if home != A else "direct", condition)


ENGINE_ALLOW = {"call": "ISphereXEngine(sphereXEngine()).addAllowedSenderOnChain",
                "limit": "called only when the arch controller's engine slot is nonzero; the engine's own effects are outside this map"}


def market_side(home, what, emit_name, emit_anchor):
    """Events a controller-relayed market setter emits in the market."""
    return [*accrual(home, "transitive"), written(home, "transitive"),
            ev(emit_name, "WildcatMarket", at(F, MC, emit_anchor, None, home), "transitive", what)]


def controller_rows(ids):
    h = F
    out, fam = {}, {}
    get = lambda sig: ids[(F, "WildcatMarketController", sig)]  # noqa: E731
    borrower = "onlyBorrower: msg.sender == borrower"
    controlled = "onlyControlledMarket: market is in _controlledMarkets"
    market_guard = {"call": "each called market's own sphereXGuardExternal",
                    "limit": "the market's SphereX engine, when set, can revert the relayed call"}
    blocked_lender = "reverts with AccountBlocked when a listed lender is Blocked in a listed market"

    i = get("constructor()")
    out[i["id"]] = row(i, "mapped", guards=["deployed by WildcatMarketControllerFactory through create2 with stored init code"],
        effects=["controllerFactory = msg.sender", "reads getMarketControllerParameters() and writes the borrower, sentinel, init-code and constraint immutables",
                 "sets the SphereX engine slot"],
        events=sx_init(h, F, "WildcatMarketController"),
        callees=[{"call": "IWildcatMarketControllerFactory(msg.sender).getMarketControllerParameters", "limit": "the deploying factory answers at creation time"}],
        attribution=["the borrower comes from the factory's temporary parameter, set to the deploying caller"],
        refs=[at(h, CT, "getMarketControllerParameters();")],
        reason="both SphereX initialisation events fire unconditionally")
    fam[i["id"]] = ["creation"]

    # authorizeLenders precedes authorizeLendersAndUpdateMarkets in the file, but
    # deauthorizeLendersAndUpdateMarkets precedes deauthorizeLenders, so each emit site is picked explicitly.
    for sig, emit, nth, effect in (("authorizeLenders(address[])", "emit LenderAuthorized(lender);", 1,
                                    "adds each listed lender to _authorizedLenders"),
                                   ("deauthorizeLenders(address[])", "emit LenderDeauthorized(lender);", 2,
                                    "removes each listed lender from _authorizedLenders")):
        i = get(sig)
        name = "LenderAuthorized(address)" if emit.startswith("emit LenderAuthorized") else "LenderDeauthorized(address)"
        out[i["id"]] = row(i, "conditional", guards=[borrower, guard_sx()],
            effects=[effect],
            events=[ev(name, "WildcatMarketController", at(h, CT, emit, nth), "direct", "per listed lender whose membership changes")],
            callees=[SPHEREX], attribution=["the borrower decides lender membership; markets learn it lazily or through a sync"],
            reason="one event per lender whose membership actually changes; an unchanged or empty list emits nothing")
        fam[i["id"]] = ["administration"]

    for sig, emit, nth, verb, flag in (("authorizeLendersAndUpdateMarkets(address[],address[])", "emit LenderAuthorized(lender);", 2, "adds", "true"),
                                       ("deauthorizeLendersAndUpdateMarkets(address[],address[])", "emit LenderDeauthorized(lender);", 1, "removes", "false")):
        i = get(sig)
        name = "LenderAuthorized(address)" if verb == "adds" else "LenderDeauthorized(address)"
        out[i["id"]] = row(i, "conditional", guards=[borrower, guard_sx(), "reverts when any listed market is not controlled", blocked_lender],
            effects=[f"{verb} each listed lender " + ("to" if verb == "adds" else "from") + " _authorizedLenders",
                     f"calls updateAccountAuthorizations(lenders, {flag}) on every listed market"],
            events=[ev(name, "WildcatMarketController", at(h, CT, emit, nth), "direct", "per listed lender whose membership changes"),
                    *accrual(h, "transitive", prefix="per listed market, "),
                    ev("AuthorizationStatusUpdated(address,uint8)", "WildcatMarket", at(h, MC, "emit_AuthorizationStatusUpdated(accounts[i], account.approval)"),
                       "transitive", "per listed lender in each listed market"),
                    written(h, "transitive", condition="once per listed market")],
            callees=[SPHEREX, market_guard, {"call": "listed market's updateAccountAuthorizations through a low-level call", "limit": "restricted to controlled markets"}],
            attribution=["the borrower acts; the markets record the lenders' new roles"],
            refs=[at(h, CT, "WildcatMarketConfig.updateAccountAuthorizations.selector,", 1 if flag == "true" else 2)],
            reason="lender events depend on membership changes and market events on the listed markets")
        fam[i["id"]] = ["administration"]

    i = get("changeSphereXEngine(address)")
    out[i["id"]] = row(i, "mapped", guards=["spherexOnlyOperator: msg.sender == _archController"],
        effects=["writes the SphereX engine storage slot"],
        events=[ev("ChangedSpherexEngineAddress(address,address)", "WildcatMarketController", at(h, SX, "emit_ChangedSpherexEngineAddress(oldEngine, newSphereXEngine)"))],
        attribution=["the arch controller is the only permitted caller"], reason="one unconditional event")
    fam[i["id"]] = ["administration"]

    i = get("closeMarket(address)")
    out[i["id"]] = row(i, "conditional", guards=[borrower, controlled, guard_sx(), "reverts when the market is already closed",
                                                 "reverts with CloseMarketWithUnpaidWithdrawals while the market's "
                                                 "unpaidBatches is nonempty when the market call starts; a market batch "
                                                 "whose expiry has passed but that no state update has "
                                                 "processed yet is not checked"],
        effects=["closes the market through WildcatMarket.closeMarket"],
        flows=["the market settles with the borrower: a shortfall is pulled from the borrower, an excess is returned"],
        events=[*accrual(h, "transitive"), written(h, "transitive"),
                ev("MarketClosed(uint256)", "WildcatMarket", at(h, MK, "emit_MarketClosed(block.timestamp)"), "transitive")],
        callees=[SPHEREX, market_guard, TOKEN], attribution=["the controller emits nothing itself; the market's events carry the closure"],
        refs=[at(h, CT, "WildcatMarket(market).closeMarket();")],
        reason="MarketClosed and StateUpdated fire in the market; accrual is conditional")
    fam[i["id"]] = ["closure", "repayment"]

    i = get("deployMarket(address,string,string,uint128,uint16,uint16,uint32,uint16,uint32)")
    out[i["id"]] = row(i, "conditional",
        guards=[guard_sx(),
                "caller must be the controller's borrower, itself registered in the arch controller (else NotRegisteredBorrower), "
                "or the controller factory; any other caller reverts with CallerNotBorrowerOrControllerFactory",
                "reverts when the arch controller blacklists the asset",
                "enforceParameterConstraints refuses empty name or symbol prefixes and bounds the rate, delinquency fee, batch "
                "duration, reserve ratio and grace period; maxTotalSupply is unbounded",
                "reverts when a market already exists at the create2 address",
                "reverts with NotController unless this controller is registered in the arch controller (registerMarket is onlyController)"],
        effects=["deploys the market by create2 from stored init code", "registers it with the arch controller", "adds it to _controlledMarkets"],
        flows=["when the factory sets an origination fee, that fee asset moves from the borrower to the fee recipient"],
        events=[*sx_init(h, F, "WildcatMarket", "transitive"),
                allowed_sender(h, "when the arch controller has a SphereX engine"),
                ev("MarketAdded(address,address)", "WildcatArchController", at(A, AR, "emit MarketAdded(msg.sender, market);", None, h), "transitive"),
                ev("MarketDeployed(address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256)", "WildcatMarketController",
                   at(h, CT, "emit MarketDeployed("))],
        callees=[SPHEREX, {"call": "queryName and querySymbol on the asset", "limit": "the asset's metadata answers are outside this map"},
                 {"call": "IERC20Metadata(asset).decimals in the new market's constructor", "limit": "an asset without a working decimals() reverts the deployment"},
                 {"call": "originationFeeAsset.safeTransferFrom(borrower, feeRecipient, originationFeeAmount)", "limit": "only when the factory configures an origination fee asset; token events are outside this map"},
                 ENGINE_ALLOW],
        attribution=["the controller's immutable borrower is the market's borrower; MarketDeployed names the market, not the borrower"],
        refs=[at(h, CT, "LibStoredInitCode.create2WithStoredInitCode(marketInitCodeStorage, salt);"),
              at(h, CT, "IWildcatArchController(_archController).registerMarket(market);")],
        reason="MarketAdded, MarketDeployed and the market's SphereX initialisation events always fire; NewAllowedSenderOnchain depends on the arch controller's engine")
    fam[i["id"]] = ["creation", "fee", "administration"]

    i = get("resetReserveRatio(address)")
    out[i["id"]] = row(i, "conditional",
        guards=[guard_sx(), "reverts unless a temporary reserve ratio is recorded for the market", "reverts before that record's expiry",
                "no caller or controlled-market check: any caller may reset an expired record",
                "reverts with InsufficientReservesForOldLiquidityRatio while the market is delinquent under the ratio being lowered"],
        effects=["restores the original reserve ratio on the market", "deletes the temporary record"],
        events=[ev("TemporaryExcessReserveRatioExpired(address)", "WildcatMarketController", at(h, CT, "emit TemporaryExcessReserveRatioExpired(market);")),
                *market_side(h, None, "ReserveRatioBipsUpdated(uint256)", "emit_ReserveRatioBipsUpdated(")],
        callees=[SPHEREX, market_guard], attribution=["permissionless keeper action; only markets this controller recorded can have a record"],
        refs=[at(h, CT, "WildcatMarket(market).setReserveRatioBips(uint256(tmp.originalReserveRatioBips).toUint16());")],
        reason="the controller and market events always fire on success; market accrual is conditional")
    fam[i["id"]] = ["administration"]

    i = get("setAnnualInterestBips(address,uint16)")
    out[i["id"]] = row(i, "conditional",
        guards=[borrower, controlled, guard_sx(), "reverts on a closed market", "the rate must lie within the controller's bounds",
                "reverts when the market refuses the reserve-ratio change: lowering it while delinquent, or raising it into delinquency"],
        effects=["with no active temporary ratio, a rate below the market's current rate records the original rate and ratio and "
                 "sets a temporary reserve ratio no lower than the original, expiring at block.timestamp + 2 weeks",
                 "with an active temporary ratio, a rate below the recorded original rate recomputes it; the expiry renews only "
                 "when the new rate is below the market's current rate",
                 "with an active temporary ratio, a rate at or above the recorded original cancels it and restores the original ratio",
                 "sets the market's annual interest rate"],
        events=[ev("TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256)", "WildcatMarketController",
                   at(h, CT, "emit TemporaryExcessReserveRatioActivated("), "direct",
                   "when no temporary ratio is active and the new rate is below the market's current rate"),
                ev("TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256)", "WildcatMarketController",
                   at(h, CT, "emit TemporaryExcessReserveRatioUpdated("), "direct",
                   "when a temporary ratio is active and the new rate is below the recorded original rate"),
                ev("TemporaryExcessReserveRatioCanceled(address)", "WildcatMarketController",
                   at(h, CT, "emit TemporaryExcessReserveRatioCanceled(market);"), "direct",
                   "when a temporary ratio is active and the new rate is at or above the recorded original rate"),
                ev("ReserveRatioBipsUpdated(uint256)", "WildcatMarket", at(h, MC, "emit_ReserveRatioBipsUpdated("), "transitive",
                   "whenever one of the three temporary-ratio events fires"),
                written(h, "transitive", condition="a second StateUpdated, from the reserve-ratio call, whenever one of the "
                                                   "three temporary-ratio events fires"),
                *accrual(h, "transitive", prefix="from either market call, "), written(h, "transitive"),
                ev("AnnualInterestBipsUpdated(uint256)", "WildcatMarket", at(h, MC, "emit_AnnualInterestBipsUpdated("), "transitive")],
        callees=[SPHEREX, market_guard], attribution=["the borrower acts through the controller"],
        refs=[at(h, CT, "WildcatMarket(market).setAnnualInterestBips(annualInterestBips);")],
        reason="AnnualInterestBipsUpdated and StateUpdated always fire in the market; the temporary-ratio branch decides the rest")
    fam[i["id"]] = ["administration"]

    i = get("setMaxTotalSupply(address,uint256)")
    out[i["id"]] = row(i, "conditional", guards=[borrower, controlled, guard_sx(), "reverts on a closed market",
                                                 "reverts when maxTotalSupply exceeds uint128"],
        effects=["sets the market's maxTotalSupply"],
        events=market_side(h, None, "MaxTotalSupplyUpdated(uint256)", "emit_MaxTotalSupplyUpdated("),
        callees=[SPHEREX, market_guard], attribution=["the borrower acts through the controller"],
        refs=[at(h, CT, "WildcatMarket(market).setMaxTotalSupply(maxTotalSupply);")],
        reason="the market's setter events always fire; accrual is conditional")
    fam[i["id"]] = ["administration"]

    i = get("updateLenderAuthorization(address,address[])")
    out[i["id"]] = row(i, "conditional",
        guards=[guard_sx(), "reverts when any listed market is not controlled", "no caller check: any caller may sync one lender",
                blocked_lender],
        effects=["sets the lender's role in each listed market from the controller's current lender set"],
        events=[*accrual(h, "transitive", prefix="per listed market, "),
                ev("AuthorizationStatusUpdated(address,uint8)", "WildcatMarket", at(h, MC, "emit_AuthorizationStatusUpdated(accounts[i], account.approval)"),
                   "transitive", "once per listed market"),
                written(h, "transitive", condition="once per listed market")],
        callees=[SPHEREX, market_guard], attribution=["permissionless sync; the result follows the borrower's earlier authorization decision"],
        refs=[at(h, CT, "WildcatMarket(market).updateAccountAuthorizations(")],
        reason="market events fire once per listed market; an empty market list emits nothing")
    fam[i["id"]] = ["administration"]
    return out, fam


def factory_rows(ids):
    h = F
    out, fam = {}, {}
    get = lambda sig: ids[(F, "WildcatMarketControllerFactory", sig)]  # noqa: E731
    registered = "the caller must be a registered borrower in the arch controller"
    factory_registered = ("reverts with NotControllerFactory unless this factory is registered in the arch controller "
                          "(registerController is onlyControllerFactory)")

    i = get("constructor(address,address,(uint32,uint32,uint16,uint16,uint16,uint16,uint32,uint32,uint16,uint16))")
    out[i["id"]] = row(i, "mapped", guards=["reverts with InvalidConstraints on inconsistent or out-of-range bounds"],
        effects=["writes the arch controller, sentinel and constraint immutables",
                 "deploys two init-code storage contracts, one for the controller and one for the market",
                 "sets the SphereX engine slot from the arch controller's engine"],
        events=sx_init(h, F, "WildcatMarketControllerFactory"),
        callees=[{"call": "IWildcatArchController(archController_).sphereXEngine", "limit": "read once at deployment"}],
        attribution=["the two storage contracts are the registry's init-code storage entries; they emit nothing"],
        refs=[at(h, FA, "(controllerInitCodeStorage, controllerInitCodeHash) = _storeControllerInitCode();"),
              at(h, FA, "(marketInitCodeStorage, marketInitCodeHash) = _storeMarketInitCode();")],
        reason="both SphereX initialisation events fire unconditionally")
    fam[i["id"]] = ["creation"]

    i = get("changeSphereXEngine(address)")
    out[i["id"]] = row(i, "mapped", guards=["spherexOnlyOperator: msg.sender == _archController"],
        effects=["writes the SphereX engine storage slot"],
        events=[ev("ChangedSpherexEngineAddress(address,address)", "WildcatMarketControllerFactory", at(h, SX, "emit_ChangedSpherexEngineAddress(oldEngine, newSphereXEngine)"))],
        attribution=["the arch controller is the only permitted caller"], reason="one unconditional event")
    fam[i["id"]] = ["administration"]

    controller_events = [*sx_init(h, F, "WildcatMarketController", "transitive"),
                         allowed_sender(h, "when the arch controller has a SphereX engine"),
                         ev("ControllerAdded(address,address)", "WildcatArchController", at(A, AR, "emit ControllerAdded(msg.sender, controller);", None, h), "transitive"),
                         ev("NewController(address,address)", "WildcatMarketControllerFactory", at(h, FA, "emit NewController(msg.sender, controller);"))]
    i = get("deployController()")
    out[i["id"]] = row(i, "conditional", guards=[guard_sx(), registered, "reverts when the caller's controller already exists", factory_registered],
        effects=["deploys the caller's controller by create2 with salt = caller", "registers it with the arch controller", "adds it to _deployedControllers"],
        events=controller_events, callees=[SPHEREX, ENGINE_ALLOW],
        attribution=["NewController names the borrower (msg.sender) and the controller"],
        refs=[at(h, FA, "LibStoredInitCode.create2WithStoredInitCode(controllerInitCodeStorage, salt);")],
        reason="the creation and registration events always fire; NewAllowedSenderOnchain depends on the arch controller's engine")
    fam[i["id"]] = ["creation"]

    i = get("deployControllerAndMarket(string,string,address,uint128,uint16,uint16,uint32,uint16,uint32)")
    out[i["id"]] = row(i, "conditional",
        guards=[guard_sx(), registered, "reverts when the caller's controller already exists", factory_registered,
                "the new controller applies every deployMarket check; the factory is its permitted caller",
                "an origination fee is pulled by the new controller, so the borrower must have approved that controller's "
                "create2 address for the fee asset beforehand"],
        effects=["deploys and registers a controller, then a market through it"],
        flows=["when an origination fee is set, the fee asset moves from the borrower to the fee recipient"],
        events=[*controller_events, *sx_init(h, F, "WildcatMarket", "transitive"),
                ev("NewAllowedSenderOnchain(address)", "WildcatArchController", at(A, SC, "emit_NewAllowedSenderOnchain(newSender)", None, h), "transitive",
                   "again for the market, when the arch controller has a SphereX engine"),
                ev("MarketAdded(address,address)", "WildcatArchController", at(A, AR, "emit MarketAdded(msg.sender, market);", None, h), "transitive"),
                ev("MarketDeployed(address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256)", "WildcatMarketController",
                   at(h, CT, "emit MarketDeployed("), "transitive")],
        callees=[SPHEREX, ENGINE_ALLOW, {"call": "queryName, querySymbol and the origination-fee transferFrom on external tokens", "limit": "token behaviour is outside this map"},
                 {"call": "IERC20Metadata(asset).decimals in the new market's constructor", "limit": "an asset without a working decimals() reverts the deployment"}],
        attribution=["the caller becomes the controller's borrower and so the market's borrower"],
        refs=[at(h, FA, "market = IWildcatMarketController(controller).deployMarket(")],
        reason="the controller and market creation events always fire; the engine-dependent events are conditional")
    fam[i["id"]] = ["creation", "fee"]

    i = get("setProtocolFeeConfiguration(address,address,uint80,uint16)")
    out[i["id"]] = row(i, "mapped", guards=["onlyArchControllerOwner: msg.sender == arch controller owner()", guard_sx(),
                                            "reverts on an inconsistent recipient, origination asset or protocolFeeBips above 10000"],
        effects=["replaces _protocolFeeConfiguration for markets deployed afterwards"],
        events=[ev("UpdateProtocolFeeConfiguration(address,uint16,address,uint256)", "WildcatMarketControllerFactory", at(h, FA, "emit UpdateProtocolFeeConfiguration("))],
        callees=[SPHEREX], attribution=["existing markets keep their immutable feeRecipient and protocolFeeBips"],
        reason="one unconditional event")
    fam[i["id"]] = ["fee", "administration"]
    return out, fam


def arch_rows(ids):
    h = A
    out, fam = {}, {}
    get = lambda sig: ids[(A, "WildcatArchController", sig)]  # noqa: E731
    owner = "onlyOwner (solady Ownable): msg.sender == owner()"

    i = get("constructor()")
    out[i["id"]] = row(i, "mapped", guards=["deployer becomes owner and SphereX admin"],
        effects=["SphereX admin = deployer, operator and engine = address(0)", "owner = deployer"],
        events=[ev("SpherexAdminTransferCompleted(address,address)", "WildcatArchController", at(h, SC, "emit_SpherexAdminTransferCompleted(address(0), admin)")),
                ev("ChangedSpherexOperator(address,address)", "WildcatArchController", at(h, SC, "emit_ChangedSpherexOperator(address(0), operator)")),
                ev("ChangedSpherexEngineAddress(address,address)", "WildcatArchController", at(h, SC, "emit_ChangedSpherexEngineAddress(address(0), engine)")),
                ev("OwnershipTransferred(address,address)", "WildcatArchController", at(h, OW, "log3(0, 0, _OWNERSHIP_TRANSFERRED_EVENT_SIGNATURE, 0, newOwner)"))],
        attribution=["OwnershipTransferred is an assembly log in solady Ownable, outside the #1962 emitter table's src/ scope"],
        reason="four unconditional events")
    fam[i["id"]] = ["creation"]

    simple = {
        "addBlacklist(address)": ("AssetBlacklisted(address)", "emit AssetBlacklisted(asset);", owner, "adds the asset to _assetBlacklist", "reverts when already blacklisted"),
        "removeBlacklist(address)": ("AssetPermitted(address)", "emit AssetPermitted(asset);", owner, "removes the asset from _assetBlacklist", "reverts when not blacklisted"),
        "registerBorrower(address)": ("BorrowerAdded(address)", "emit BorrowerAdded(borrower);", owner, "adds the borrower", "reverts when already registered"),
        "removeBorrower(address)": ("BorrowerRemoved(address)", "emit BorrowerRemoved(borrower);", owner, "removes the borrower", "reverts when not registered"),
        "removeControllerFactory(address)": ("ControllerFactoryRemoved(address)", "emit ControllerFactoryRemoved(factory);", owner, "removes the factory", "reverts when not registered"),
        "removeController(address)": ("ControllerRemoved(address)", "emit ControllerRemoved(controller);", owner, "removes the controller", "reverts when not registered"),
        "removeMarket(address)": ("MarketRemoved(address)", "emit MarketRemoved(market);", owner, "removes the market", "reverts when not registered"),
    }
    # What each registry entry actually gates, from the only V1 call sites that read the arch controller.
    consequence = {
        "addBlacklist(address)": "affects only future deployMarket calls; existing markets on the asset are unaffected",
        "removeBlacklist(address)": "affects only future deployMarket calls; existing markets on the asset are unaffected",
        "registerBorrower(address)": "required for deployController and borrower-initiated deployMarket; the other "
                                     "deployment checks still apply",
        "removeBorrower(address)": "existing markets keep operating; new controllers and borrower-initiated deployMarket revert "
                                   "with NotRegisteredBorrower",
        "removeControllerFactory(address)": "this factory's deployController and deployControllerAndMarket then revert with "
                                            "NotControllerFactory; existing controllers and markets keep operating",
        "removeController(address)": "existing markets keep operating; this controller's deployMarket then reverts with NotController",
        "removeMarket(address)": "registry membership only; markets never read the registry, so the market keeps operating",
    }
    for sig, (name, emit, guard, effect, check) in simple.items():
        i = get(sig)
        out[i["id"]] = row(i, "mapped", guards=[guard, check], effects=[effect],
            events=[ev(name, "WildcatArchController", at(h, AR, emit))],
            attribution=[consequence[sig]],
            reason="one unconditional event")
        fam[i["id"]] = ["administration"]

    for sig, name, emit, guard, effect in (
            ("registerControllerFactory(address)", "ControllerFactoryAdded(address)", "emit ControllerFactoryAdded(factory);", owner, "adds the factory"),
            ("registerController(address)", "ControllerAdded(address,address)", "emit ControllerAdded(msg.sender, controller);",
             "onlyControllerFactory: msg.sender is a registered factory", "adds the controller"),
            ("registerMarket(address)", "MarketAdded(address,address)", "emit MarketAdded(msg.sender, market);",
             "onlyController: msg.sender is a registered controller", "adds the market")):
        i = get(sig)
        out[i["id"]] = row(i, "conditional", guards=[guard, "reverts when already registered"],
            effects=[effect, "allows it as an on-chain sender in the SphereX engine when one is set"],
            events=[allowed_sender(h, "when the SphereX engine is set"), ev(name, "WildcatArchController", at(h, AR, emit))],
            callees=[ENGINE_ALLOW],
            attribution=["the indexed first field names the registering factory or controller"] if name != "ControllerFactoryAdded(address)" else [],
            reason="the registration event always fires; NewAllowedSenderOnchain depends on the engine")
        fam[i["id"]] = ["administration"]

    for sig, name, anchor, guard, effect in (
            ("transferSphereXAdminRole(address)", "SpherexAdminTransferStarted(address,address)", "emit_SpherexAdminTransferStarted(sphereXAdmin(), newAdmin)",
             "onlySphereXAdmin", "sets the pending SphereX admin"),
            ("acceptSphereXAdminRole()", "SpherexAdminTransferCompleted(address,address)", "emit_SpherexAdminTransferCompleted(oldAdmin, msg.sender)",
             "msg.sender must be the pending SphereX admin", "makes the caller SphereX admin and clears the pending slot"),
            ("changeSphereXOperator(address)", "ChangedSpherexOperator(address,address)", "emit_ChangedSpherexOperator(oldSphereXOperator, newSphereXOperator)",
             "onlySphereXAdmin", "sets the SphereX operator")):
        i = get(sig)
        out[i["id"]] = row(i, "mapped", guards=[guard], effects=[effect],
            events=[ev(name, "WildcatArchController", at(h, SC, anchor))], reason="one unconditional event")
        fam[i["id"]] = ["administration"]

    i = get("changeSphereXEngine(address)")
    out[i["id"]] = row(i, "mapped", guards=["spherexOnlyOperator: msg.sender == sphereXOperator()",
                                            "reverts when a nonzero engine does not report the ISphereXEngine interface"],
        effects=["writes the arch controller's own engine slot; registered contracts keep theirs until updated"],
        events=[ev("ChangedSpherexEngineAddress(address,address)", "WildcatArchController", at(h, SC, "emit_ChangedSpherexEngineAddress(oldEngine, newSphereXEngine)"))],
        callees=[{"call": "ISphereXEngine(newSphereXEngine).supportsInterface",
                  "limit": "called only when the new engine is nonzero; the candidate engine answers the interface check"}],
        reason="one unconditional event")
    fam[i["id"]] = ["administration"]

    i = get("updateSphereXEngineOnRegisteredContracts(address[],address[],address[])")
    out[i["id"]] = row(i, "conditional", guards=["spherexOnlyOperatorOrAdmin", "reverts when any listed contract is not registered in its set"],
        effects=["sets each listed factory, controller and market's engine to the arch controller's engine"],
        events=[*[ev("ChangedSpherexEngineAddress(address,address)", emitter,
                     at(F, SX, "emit_ChangedSpherexEngineAddress(oldEngine, newSphereXEngine)", None, h), "transitive",
                     f"once per listed {what}") for emitter, what in (("WildcatMarketControllerFactory", "controller factory"),
                                                                      ("WildcatMarketController", "controller"),
                                                                      ("WildcatMarket", "market"))],
                ev("NewAllowedSenderOnchain(address)", "WildcatArchController", at(h, AR, "emit_NewAllowedSenderOnchain(account);"), "direct",
                   "once per listed contract when the engine is set")],
        callees=[{"call": "listed contracts' changeSphereXEngine through a low-level call",
                  "limit": "restricted to registered addresses; registerControllerFactory accepts any address, so a listed "
                           "factory may be non-V1 code whose effects are outside this map"}, ENGINE_ALLOW],
        attribution=["a listed V1 contract accepts the call only when its immutable _archController is this arch controller"],
        reason="events are per listed contract; empty lists emit nothing")
    fam[i["id"]] = ["administration"]

    ownership = {
        "transferOwnership(address)": ("reverts when newOwner is address(0)", "sets owner = newOwner", "log3(0, 0, _OWNERSHIP_TRANSFERRED_EVENT_SIGNATURE, sload(ownerSlot), newOwner)", "OwnershipTransferred(address,address)", owner),
        "renounceOwnership()": ("", "sets owner = address(0)", "log3(0, 0, _OWNERSHIP_TRANSFERRED_EVENT_SIGNATURE, sload(ownerSlot), newOwner)", "OwnershipTransferred(address,address)", owner),
        "completeOwnershipHandover(address)": ("reverts when the pending owner's handover is absent or expired", "clears the handover and sets owner = pendingOwner",
                                               "log3(0, 0, _OWNERSHIP_TRANSFERRED_EVENT_SIGNATURE, sload(ownerSlot), newOwner)", "OwnershipTransferred(address,address)", owner),
        "requestOwnershipHandover()": ("", "records a handover expiry for the caller", "log2(0, 0, _OWNERSHIP_HANDOVER_REQUESTED_EVENT_SIGNATURE, caller())",
                                       "OwnershipHandoverRequested(address)", "any caller"),
        "cancelOwnershipHandover()": ("", "clears the caller's handover", "log2(0, 0, _OWNERSHIP_HANDOVER_CANCELED_EVENT_SIGNATURE, caller())",
                                      "OwnershipHandoverCanceled(address)", "any caller"),
    }
    for sig, (check, effect, anchor, name, guard) in ownership.items():
        i = get(sig)
        out[i["id"]] = row(i, "mapped", guards=[g for g in (guard, "payable: any ETH sent stays in the arch controller", check) if g],
            effects=[effect], flows=["msg.value, if any, is retained by the arch controller"],
            events=[ev(name, "WildcatArchController", at(h, OW, anchor))],
            attribution=["solady Ownable emits this with an assembly log, outside the #1962 emitter table's src/ scope"],
            reason="one unconditional event")
        fam[i["id"]] = ["administration"]
    return out, fam


def sentinel_rows(ids):
    h = S
    out, fam = {}, {}
    get = lambda ctx, sig: ids[(S, ctx, sig)]  # noqa: E731

    i = get("WildcatSanctionsSentinel", "constructor(address,address)")
    out[i["id"]] = row(i, "eventless", effects=["writes archController and chainalysisSanctionsList", "sets tmpEscrowParams to placeholder values"],
        reason="the constructor emits no event and calls no contract")
    fam[i["id"]] = ["creation"]

    i = get("WildcatSanctionsSentinel", "createEscrow(address,address,address)")
    out[i["id"]] = row(i, "conditional", guards=["no caller check: any caller may create an escrow for any (borrower, account, asset)"],
        effects=["deploys a WildcatSanctionsEscrow by create2 when none exists", "sanctionOverrides[borrower][escrow] = true"],
        events=[ev("NewSanctionsEscrow(address,address,address)", "WildcatSanctionsSentinel", at(h, SE, "emit NewSanctionsEscrow("), "direct", "when no escrow exists yet"),
                ev("SanctionOverride(address,address)", "WildcatSanctionsSentinel", at(h, SE, "emit SanctionOverride(borrower, escrowContract)"), "direct", "when no escrow exists yet")],
        attribution=["the borrower argument is caller-supplied; it is not checked against any registry"],
        refs=[at(h, SE, "if (escrowContract.code.length != 0) return escrowContract;")],
        reason="an existing escrow returns early with no event")
    fam[i["id"]] = ["sanctions", "creation"]

    for sig, name, anchor, effect in (("overrideSanction(address)", "SanctionOverride(address,address)", "emit SanctionOverride(msg.sender, account);", "true"),
                                      ("removeSanctionOverride(address)", "SanctionOverrideRemoved(address,address)", "emit SanctionOverrideRemoved(msg.sender, account);", "false")):
        i = get("WildcatSanctionsSentinel", sig)
        out[i["id"]] = row(i, "mapped", guards=["no caller check: msg.sender acts as the borrower key"],
            effects=[f"sanctionOverrides[msg.sender][account] = {effect}"],
            events=[ev(name, "WildcatSanctionsSentinel", at(h, SE, anchor))],
            attribution=["the override applies only to markets whose borrower is msg.sender; the event's first field is that caller"],
            reason="one unconditional event")
        fam[i["id"]] = ["sanctions"]

    i = get("WildcatSanctionsEscrow", "constructor()")
    out[i["id"]] = row(i, "eventless", guards=["no guard: any deployer becomes the escrow's sentinel; estate escrows are created by the sentinel's createEscrow"],
        effects=["sentinel = msg.sender", "borrower, account and asset from the sentinel's tmpEscrowParams"],
        callees=[{"call": "IWildcatSanctionsSentinel(msg.sender).tmpEscrowParams", "limit": "read once at creation"}],
        reason="the constructor emits no event; the sentinel's NewSanctionsEscrow records the creation")
    fam[i["id"]] = ["creation", "sanctions"]

    i = get("WildcatSanctionsEscrow", "releaseEscrow()")
    out[i["id"]] = row(i, "conditional",
        guards=["no caller check", "reverts with CanNotReleaseEscrow while the sentinel reports the account sanctioned for the borrower",
                "for a market-token escrow, the market's transfer reverts with NullTransferAmount on a zero balance and with "
                "AccountBlocked while the account is still Blocked there"],
        effects=["sends the escrow's whole asset balance to the account"],
        flows=["the escrowed asset moves from the escrow to the account"],
        events=[*accrual(h, "transitive", prefix="when the escrowed asset is a Wildcat market token, "),
                written(h, "transitive", condition="when the escrowed asset is a Wildcat market token"),
                ev("Transfer(address,address,uint256)", "WildcatMarket", at(F, MT, "emit_Transfer(from, to, amount)", None, h), "transitive",
                   "when the escrowed asset is a Wildcat market token"),
                ev("EscrowReleased(address,address,uint256)", "WildcatSanctionsEscrow", at(h, ES, "emit EscrowReleased(_account, _asset, amount);"))],
        callees=[{"call": "asset.safeTransfer(account, balance)", "limit": "the asset is a market token or an arbitrary ERC20; a market refuses the transfer while the account is still Blocked there, so stunningReversal must run first"},
                 SANCTIONS_LIST,
                 {"call": "for a market-token escrow only: the market's underlying asset.balanceOf(market) through the market's totalAssets()",
                  "limit": "can revert the release; an ERC20 escrow never makes this call"}],
        attribution=["EscrowReleased names the account and asset; the caller may be anyone"],
        refs=[at(h, ES, "asset.safeTransfer(_account, amount);")],
        reason="EscrowReleased always fires on success; market-side events depend on which asset the escrow holds")
    fam[i["id"]] = ["escrow-release"]
    return out, fam


def lens_rows(ids):
    out, fam = {}, {}
    i = ids[(L, "MarketLens", "constructor(address)")]
    out[i["id"]] = row(i, "eventless", guards=["reverts unless the arch controller has exactly one registered controller factory"],
        effects=["writes the archController and controllerFactory immutables"],
        callees=[{"call": "WildcatArchController(_archController).getRegisteredControllerFactories", "limit": "read once at deployment"}],
        refs=[at(L, "src/lens/MarketLens.sol", "require(factories.length == 1")],
        reason="the lens is read-only after creation and its constructor emits no event")
    fam[i["id"]] = ["creation"]
    return out, fam


def main():
    global PROTOCOL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--denominator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    PROTOCOL = args.protocol
    denominator = json.loads(args.denominator.read_bytes())
    ids = {(r["input"], r["context"], r["signature"]): r for r in denominator["identities"]}
    links, families = {}, {}
    for builder in BUILDERS:
        rows, fam = builder(ids)
        links.update(rows)
        families.update(fam)
    for link in links.values():
        # totalAssets() runs inside every _writeState, so each state-updating row can revert on the asset call.
        scoped_call = any(callee["call"].startswith("for a market-token escrow only") for callee in link["dynamic_callees"])
        if (any(event["event"] == "StateUpdated(uint256,bool)" for event in link["events"])
                and TOTAL_ASSETS not in link["dynamic_callees"] and not scoped_call):
            link["dynamic_callees"].append(TOTAL_ASSETS)
    scoped = [r for r in denominator["identities"] if r["kind"] != "read"]
    missing = sorted(r["id"] for r in scoped if r["id"] not in links)
    if missing:
        raise SystemExit("unlinked scoped actions:\n" + "\n".join(missing))
    actions = []
    for r in denominator["identities"]:
        if r["kind"] == "read":
            fams, summary = ["read"], f"read path on {r['context']}, declared in {r['declared_in']}"
        else:
            fams, summary = families[r["id"]], SUMMARY.get(r["id"], f"{r['kind']} action on {r['context']}")
        actions.append({"id": r["id"], "input": r["input"], "context": r["context"], "kind": r["kind"],
                        "signature": r["signature"], "families": fams, "summary": summary,
                        "source_refs": [r["source_ref"]]})
    args.out.mkdir(parents=True, exist_ok=True)
    encode = lambda v: (json.dumps(v, indent=2, sort_keys=True) + "\n").encode()  # noqa: E731
    (args.out / "actions.json").write_bytes(encode({"schema": "issue-1963-actions/v1", "actions": actions}))
    (args.out / "linkage.json").write_bytes(encode({"schema": "issue-1963-linkage/v1",
                                                    "actions": [links[r["id"]] for r in scoped]}))
    print(len(actions), "actions;", len(links), "linkage rows")


SUMMARY: dict[str, str] = {}
BUILDERS = [market_rows, controller_rows, factory_rows, arch_rows, sentinel_rows, lens_rows]

if __name__ == "__main__":
    main()
