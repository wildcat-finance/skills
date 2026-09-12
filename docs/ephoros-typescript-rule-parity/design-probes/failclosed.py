"""Sites a strategy still reports in a file the shared lexer refuses."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategies import STRATEGIES, ephoros

REFUSED = "logger.debug(`unterminated ${market}\n"


def main(name):
    spans, errors = ephoros.lex(REFUSED)
    sites = len(STRATEGIES[name](REFUSED))
    print(json.dumps({"strategy": name, "lexer_errors": len(errors),
                      "sites_reported": sites}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
