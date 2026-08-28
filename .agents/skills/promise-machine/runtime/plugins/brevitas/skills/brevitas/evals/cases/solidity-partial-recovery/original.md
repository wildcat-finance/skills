| S3-R1-02 | medium | `src/CoveredCDSFacility.sol` | A small partial default claim could round recovery down to zero, pay cash and leave all debt for later redemption. | fixed; non-final cumulative recovery rounds up against the claimant and a low-share regression covers the split |

Evidence:

- `audit/X-RAY.md`
- `audit/FIZZ.md`
- 36 Foundry tests, including directed regressions for all four fixed defects
- five stateful accounting properties at 128,000 calls each under the default profile
- CI fuzz properties at 1,000 runs and stateful properties at 32,768 calls each
- `script/release-gate.sh`: passed, including dependency, Markdown, raster, arithmetic and size checks
