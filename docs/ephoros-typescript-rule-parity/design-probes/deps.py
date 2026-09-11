"""Runtime packages outside the standard library that a strategy needs."""
import importlib.util
import json
import sys

NEEDED = {"span-index": [], "unmasked-regex": [], "forward-scan": []}


def main(name):
    missing = [m for m in NEEDED[name] if importlib.util.find_spec(m) is None]
    print(json.dumps({"strategy": name, "external": len(NEEDED[name]),
                      "unavailable": missing}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
