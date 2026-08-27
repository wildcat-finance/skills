[Medium] A small partial default claim could pay cash while rounding recovery debt to zero.
Location: `src/CoveredCDSFacility.sol:249-264`
Mechanism: Per-claim floor rounding let split claims leave debt for later redemption; non-final cumulative recovery must round up against the claimant.
Impact: Claim splitting could change debt recovery despite equal total cash payouts.
Fix: Use cumulative rounded-up allocation and keep the low-share regression; `audit/X-RAY.md`, `audit/FIZZ.md`, 36 Foundry tests, 128,000 calls per stateful accounting property, CI fuzz at 1,000 runs, stateful checks at 32,768 calls, and `script/release-gate.sh` passed.
