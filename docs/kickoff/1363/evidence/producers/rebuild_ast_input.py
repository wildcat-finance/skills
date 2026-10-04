"""Rebuild one retained compiler input from a recovered source checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role",choices=("deployed","candidate"))
    parser.add_argument("source",type=Path)
    args=parser.parse_args()
    bundle=Path(__file__).resolve().parents[2]
    record=json.loads((bundle/f"evidence/{args.role}-ast-input-recovery.json").read_text())
    sources={}
    for path in record["source_paths"]:
        sources[path]={"content":(args.source/path).read_text()}
    value={"language":record["language"],"sources":sources,"settings":record["settings"]}
    raw=json.dumps(value,ensure_ascii=True,separators=(",",":")).encode()
    if hashlib.sha256(raw).hexdigest()!=record["input_sha256"]:
        raise SystemExit("Recovered compiler input differs from the recorded SHA-256")
    sys.stdout.buffer.write(raw)
if __name__=="__main__":main()

