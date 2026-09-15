"""Peak traced allocation in bytes for one strategy over the specimen."""
import json
import sys
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategies import STRATEGIES
from specimen import build


def main(name):
    text = build()
    strategy = STRATEGIES[name]
    tracemalloc.start()
    strategy(text)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(json.dumps({"strategy": name, "bytes": len(text), "peak_bytes": peak}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
