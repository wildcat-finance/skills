#!/usr/bin/env python3
"""Keep recorded interval commands and imports working under their old name."""

import sys
import interval_collector as _collector

if __name__ == "__main__":
    raise SystemExit(_collector.main())

# Share module state so callers patching the old import affect the collector.
sys.modules[__name__] = _collector
