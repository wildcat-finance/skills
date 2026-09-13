"""Wall-clock milliseconds for one strategy over the stated specimen."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategies import STRATEGIES
from specimen import build


def main(name):
    text = build()
    strategy = STRATEGIES[name]
    start = time.perf_counter()
    sites = len(strategy(text))
    elapsed = (time.perf_counter() - start) * 1000.0
    print(json.dumps({"strategy": name, "bytes": len(text), "sites": sites,
                      "milliseconds": round(elapsed, 1)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
