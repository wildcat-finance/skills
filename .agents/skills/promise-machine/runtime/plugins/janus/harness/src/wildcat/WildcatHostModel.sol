// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {IWildcatHook} from "./IWildcatHook.sol";

/// @dev A minimal ERC20 the model uses as its underlying asset, so deposits,
///      withdrawals and any hostile value redirection show up as real token
///      movements the recorder can observe.
contract MockAsset {
  mapping(address => uint256) public balanceOf;
  mapping(address => mapping(address => uint256)) public allowance;

  function mint(address to, uint256 amount) external {
    balanceOf[to] += amount;
  }

  function approve(address spender, uint256 amount) external returns (bool) {
    allowance[msg.sender][spender] = amount;
    return true;
  }

  function transfer(address to, uint256 amount) public returns (bool) {
    balanceOf[msg.sender] -= amount;
    balanceOf[to] += amount;
    return true;
  }

  function transferFrom(address from, address to, uint256 amount) external returns (bool) {
    uint256 allowed = allowance[from][msg.sender];
    if (allowed != type(uint256).max) allowance[from][msg.sender] = allowed - amount;
    balanceOf[from] -= amount;
    balanceOf[to] += amount;
    return true;
  }
}

/// @dev A faithful model of the Wildcat v2.5 market-to-hook seam. It is not the
///      whole protocol: it reproduces exactly the mechanics a hook conformance
///      suite depends on, each cited to the anchor commit 9716e78:
///
///      - the hook is called with all remaining gas and zero value, and its
///        revert bytes are bubbled unchanged (HooksConfig.sol:88-106);
///      - the hook runs before the action's effects are applied, on an
///        intermediate state (e.g. WildcatMarket.sol:72), and queueWithdrawal
///        sets pendingWithdrawalExpiry before the hook, the documented state
///        exception (WildcatMarketWithdrawals.sol:115-119);
///      - onSetAnnualInterestAndReserveRatioBips must return at least 0x40
///        bytes; the market masks each word to uint16 and applies it within
///        bounds (HooksConfig.sol:794-804, WildcatMarketConfig.sol:131-168);
///      - every entry point is nonReentrant on one global guard, so a hook
///        cannot re-enter any market action (ReentrancyGuard.sol);
///      - onExecuteWithdrawal is never enabled, so a queued withdrawal's
///        execution is not hook-gated: the exit the liveness gate depends on
///        (OpenTermHooks.sol:330-336 empty body, useOnExecuteWithdrawal false).
///
///      The hook calldata is built with ordinary ABI encoding rather than the
///      hand-rolled extraData tail; the semantics the gates test are identical.
contract WildcatHostModel {
  error Reentrancy();
  error NotBorrower();
  error BipsTooHigh();

  MockAsset public immutable asset;
  address public borrower;
  address public hook;

  mapping(address => uint256) public scaledBalanceOf;
  uint256 public scaledTotalSupply;
  uint256 public scaledPendingWithdrawals;
  mapping(uint32 => uint256) public batchScaledAmount;
  mapping(uint32 => mapping(address => uint256)) public queuedOf;
  uint32 public pendingWithdrawalExpiry;
  uint16 public annualInterestBips = 1000;
  uint16 public reserveRatioBips = 2000;
  bool public isClosed;

  /// @dev Gas consumed by the most recent hook call, for the gas-grief gate.
  uint256 public lastHookGasUsed;

  bool private _entered;

  modifier nonReentrant() {
    if (_entered) revert Reentrancy();
    _entered = true;
    _;
    _entered = false;
  }

  constructor(MockAsset asset_) {
    asset = asset_;
  }

  /// @dev Set once, to break the adapter/model construction cycle.
  function setBorrower(address borrower_) external {
    require(borrower == address(0), "borrower set");
    borrower = borrower_;
  }

  function setHook(address hook_) external {
    hook = hook_;
  }

  function _state() internal view returns (IWildcatHook.MarketState memory) {
    return
      IWildcatHook.MarketState({
        scaledTotalSupply: scaledTotalSupply,
        scaledPendingWithdrawals: scaledPendingWithdrawals,
        pendingWithdrawalExpiry: pendingWithdrawalExpiry,
        annualInterestBips: annualInterestBips,
        reserveRatioBips: reserveRatioBips,
        isClosed: isClosed
      });
  }

  // --------------------------------------------------------------------- //
  //                            Market actions                             //
  // --------------------------------------------------------------------- //

  function deposit(address lender, uint256 amount, bytes calldata extraData) external nonReentrant {
    // Hook first, on the pre-effect state, then the transfer and the mint.
    if (hook != address(0)) {
      _callHook(abi.encodeCall(IWildcatHook.onDeposit, (lender, amount, _state(), extraData)));
    }
    asset.transferFrom(lender, address(this), amount);
    scaledBalanceOf[lender] += amount;
    scaledTotalSupply += amount;
  }

  function queueWithdrawal(
    address lender,
    uint32 expiry,
    uint256 scaledAmount,
    bytes calldata extraData
  ) external nonReentrant {
    // The documented exception: expiry is assigned before the hook runs.
    pendingWithdrawalExpiry = expiry;
    if (hook != address(0)) {
      _callHook(
        abi.encodeCall(
          IWildcatHook.onQueueWithdrawal,
          (lender, expiry, scaledAmount, _state(), extraData)
        )
      );
    }
    scaledBalanceOf[lender] -= scaledAmount;
    scaledPendingWithdrawals += scaledAmount;
    batchScaledAmount[expiry] += scaledAmount;
    queuedOf[expiry][lender] += scaledAmount;
  }

  /// @dev No hook is called: onExecuteWithdrawal is never enabled by a template,
  ///      so this is the exit path a queued lender can always complete.
  function executeWithdrawal(address lender, uint32 expiry) external nonReentrant {
    uint256 amount = queuedOf[expiry][lender];
    queuedOf[expiry][lender] = 0;
    batchScaledAmount[expiry] -= amount;
    scaledPendingWithdrawals -= amount;
    asset.transfer(lender, amount);
  }

  function transfer(
    address from,
    address to,
    uint256 scaledAmount,
    bytes calldata extraData
  ) external nonReentrant {
    if (hook != address(0)) {
      _callHook(
        abi.encodeCall(IWildcatHook.onTransfer, (msg.sender, from, to, scaledAmount, _state(), extraData))
      );
    }
    scaledBalanceOf[from] -= scaledAmount;
    scaledBalanceOf[to] += scaledAmount;
  }

  function setAnnualInterestAndReserveRatioBips(
    uint16 apr,
    uint16 rr,
    bytes calldata extraData
  ) external nonReentrant {
    if (msg.sender != borrower) revert NotBorrower();
    uint16 newApr = apr;
    uint16 newRr = rr;
    if (hook != address(0)) {
      (newApr, newRr) = _callHookReturns(
        abi.encodeCall(
          IWildcatHook.onSetAnnualInterestAndReserveRatioBips,
          (apr, rr, _state(), extraData)
        )
      );
    }
    if (newApr > 10000 || newRr > 10000) revert BipsTooHigh();
    annualInterestBips = newApr;
    reserveRatioBips = newRr;
  }

  // --------------------------------------------------------------------- //
  //                             Hook calls                                //
  // --------------------------------------------------------------------- //

  /// @dev All remaining gas, zero value, revert bytes bubbled unchanged.
  ///      Mirrors LibHooksConfig._callHook (HooksConfig.sol:88-106).
  function _callHook(bytes memory data) private {
    address target = hook;
    uint256 g0 = gasleft();
    assembly {
      if iszero(call(gas(), target, 0, add(data, 0x20), mload(data), 0, 0)) {
        returndatacopy(0, 0, returndatasize())
        revert(0, returndatasize())
      }
    }
    lastHookGasUsed = g0 - gasleft();
  }

  /// @dev The value-returning path: at least 0x40 bytes of return data are
  ///      required, each word masked to uint16. The `or(lt(returndatasize,
  ///      0x40), iszero(call))` form depends on right-to-left argument
  ///      evaluation so returndatasize refers to this call, exactly as the
  ///      market does (HooksConfig.sol:794-804).
  function _callHookReturns(bytes memory data) private returns (uint16 a, uint16 r) {
    address target = hook;
    uint256 g0 = gasleft();
    assembly {
      if or(
        lt(returndatasize(), 0x40),
        iszero(call(gas(), target, 0, add(data, 0x20), mload(data), 0, 0x40))
      ) {
        returndatacopy(0, 0, returndatasize())
        revert(0, returndatasize())
      }
      a := and(mload(0), 0xffff)
      r := and(mload(0x20), 0xffff)
    }
    lastHookGasUsed = g0 - gasleft();
  }
}
