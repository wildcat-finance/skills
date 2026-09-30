"""Standard-library implementation package for Alexandria."""

__version__ = "0.3.0"

from .errors import AlexandriaError
from .derivation import derive
from .index import rebuild
from .query import query, query_bytes
from .release import ingest, verify
from .statement import StatementPastSingleBounds, emit_statement, emit_statement_parts
from .compound_phase0 import check_phase0

__all__ = [
    "AlexandriaError", "StatementPastSingleBounds", "check_phase0", "derive",
    "emit_statement", "emit_statement_parts", "ingest", "query", "query_bytes",
    "rebuild", "verify"
]
