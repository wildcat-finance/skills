"""Ordinary Hexaemeron discovery executes the exact checkpoint Ariadne cases."""
import importlib.util
from pathlib import Path

MODULE_NAME = "checkpoint_ariadne_cases"
PATH = Path(__file__).resolve().parents[2] / "ariadne/tests/test_checkpoint_authority.py"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(MODULE)
