"""Put the plugin's scripts directory on the path for every test module."""

import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(PLUGIN_ROOT, "scripts")
REPO_ROOT = os.path.dirname(os.path.dirname(PLUGIN_ROOT))
LAZARUS_RECEIPT_FIXTURE = os.path.join(
    REPO_ROOT, "plugins", "lazarus", "tests", "fixtures", "receipt-proof-v1"
)

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
