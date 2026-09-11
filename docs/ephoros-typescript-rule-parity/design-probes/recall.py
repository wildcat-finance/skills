"""Recall of interpolated log messages over the stated corpus."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategies import STRATEGIES

ROOT = Path(__file__).resolve().parents[2]
CLONE = ROOT / ".hexaemeron" / "validation" / "wildcat-app-v2"
DECOY = Path(__file__).resolve().parent / "corpus"


def main(name):
    strategy = STRATEGIES[name]
    files = sorted(p for p in CLONE.rglob("*")
                   if p.suffix in (".ts", ".tsx") and "node_modules" not in p.parts)
    files += sorted(p for p in DECOY.rglob("*.ts"))
    total = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        total += len(strategy(text))
    print(json.dumps({"strategy": name, "files": len(files), "sites": total}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
