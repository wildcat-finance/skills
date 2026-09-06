"""The language registry Horos's map verb dispatches through.

One folder per language. An extractor exposes outline(path, source, out)
and returns an exit code; the registry maps file suffixes onto it. A suffix
absent here is refused by map, never guessed at.
"""

from .cpp import cpp
from .go import go
from .markdown import markdown
from .python import python
from .solidity import solidity
from .typescript import typescript

EXTRACTORS = {
    ".sol": solidity.outline,
    ".cc": cpp.outline,
    ".cpp": cpp.outline,
    ".cxx": cpp.outline,
    ".go": go.outline,
    ".h": cpp.outline,
    ".hh": cpp.outline,
    ".hpp": cpp.outline,
    ".md": markdown.outline,
    ".py": python.outline,
    ".ts": typescript.outline,
    ".tsx": typescript.outline,
}


def supported():
    return ", ".join(sorted(EXTRACTORS))
