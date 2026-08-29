"""Dev-time oracle for the Horos Solidity outliner. Never imported or
executed by the shipped plugin or its test suite: the differential corpus
run drives it by hand inside a scratchpad virtualenv holding `tree-sitter`
and `tree-sitter-solidity`, and only the recorded results are committed.

Usage: <venv-python> sol_oracle.py <file.sol> [...] > oracle.json

Emits, per file, the declarations tree-sitter sees at the declared
altitudes: contracts, interfaces and libraries; named functions, events,
errors, structs and enums at file and container depth. Constructors,
receive and fallback functions, modifiers, state variables, using-for and
user-defined value types are excluded by declaration, matching the
differential's declared comparison.
"""

import json
import sys

import tree_sitter_solidity
from tree_sitter import Language, Parser

PARSER = Parser(Language(tree_sitter_solidity.language()))

NAMED_NODES = {
    "contract_declaration": "container",
    "interface_declaration": "container",
    "library_declaration": "container",
    "function_definition": "function",
    "event_definition": "event",
    "error_declaration": "error",
    "struct_declaration": "struct",
    "enum_declaration": "enum",
}
SCOPE_NODES = {
    "source_file",
    "contract_declaration",
    "interface_declaration",
    "library_declaration",
    "contract_body",
}


def text_of(node, source):
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def collect(node, source, decls):
    for child in node.children:
        kind = NAMED_NODES.get(child.type)
        if kind is not None:
            name = child.child_by_field_name("name")
            if name is not None:
                decls.append(
                    {
                        "name": text_of(name, source),
                        "line": name.start_point[0] + 1,
                        "kind": kind,
                    }
                )
        if child.type in SCOPE_NODES:
            collect(child, source, decls)


def main():
    out = {}
    for path in sys.argv[1:]:
        with open(path, "rb") as handle:
            source = handle.read()
        tree = PARSER.parse(source)
        decls = []
        collect(tree.root_node, source, decls)
        unique = {(d["name"], d["line"]): d for d in decls}
        out[path] = {
            "decls": list(unique.values()),
            "parse_errors": bool(tree.root_node.has_error),
        }
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
