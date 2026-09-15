// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {
  emit_Transfer,
  emit_MaxTotalSupplyUpdated
} from "../src/vendor/libraries/MarketEvents.sol";
import {SphereXConfig} from "../src/vendor/spherex/SphereXConfig.sol";
import {MarketState} from "../src/vendor/libraries/MarketState.sol";

/// @dev A wrapper the smoke test calls from outside, so the fetched free
///      functions and the abstract SphereX configuration are reached through
///      real external calls rather than compiled and never linked.
contract ClosureProbe is SphereXConfig {
  constructor() SphereXConfig(address(this), address(this), address(0)) {}

  function transfer(address from, address to, uint256 value) external {
    emit_Transfer(from, to, value);
  }

  function maxTotalSupply(uint256 assets) external {
    emit_MaxTotalSupplyUpdated(assets);
  }
}

/// @dev Step 2 smoke test: the pinned closure compiles under this harness's
///      profile and is reachable from a test contract. It compares no emitter;
///      the differential cases arrive in step 3.
contract ClosureTest {
  ClosureProbe internal probe;

  function setUp() public {
    probe = new ClosureProbe();
  }

  function test_closure_is_reachable_through_an_external_wrapper() external {
    probe.transfer(address(1), address(2), 3);
    probe.maxTotalSupply(4);
  }

  function test_spherex_config_declaration_is_reachable() external view {
    require(probe.sphereXAdmin() == address(probe), "admin is the probe");
    require(probe.sphereXOperator() == address(probe), "operator is the probe");
    require(probe.sphereXEngine() == address(0), "engine is unset");
  }

  function test_market_state_struct_is_reachable() external pure {
    MarketState memory state;
    state.maxTotalSupply = 5;
    require(state.maxTotalSupply == 5, "struct field round-trips");
  }
}
