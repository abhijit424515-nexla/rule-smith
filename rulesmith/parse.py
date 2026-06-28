"""Phase 0 primitive: parse Java + query the AST. Emits facts, no verdicts."""
from tree_sitter import Language, Parser
import tree_sitter_java as tsj

JAVA = Language(tsj.language())


def parse(src: str):
    """Parse Java source. Returns (tree, src_bytes)."""
    src_b = src.encode("utf8")
    return Parser(JAVA).parse(src_b), src_b


def node_text(node, src_b) -> str:
    return src_b[node.start_byte:node.end_byte].decode("utf8", "replace")


def span(node):
    """1-based (start_line, start_col, end_line, end_col)."""
    sr, sc = node.start_point
    er, ec = node.end_point
    return (sr + 1, sc + 1, er + 1, ec + 1)


def walk(node):
    yield node
    for c in node.children:
        yield from walk(c)


def find(root, *types):
    """All descendant nodes whose type is in `types`."""
    want = set(types)
    return [n for n in walk(root) if n.type in want]


def query(root, pattern: str):
    """Run a tree-sitter query, return list of (capture_name, node).

    Normalizes the dict-vs-list captures API across tree-sitter versions.
    """
    caps = JAVA.query(pattern).captures(root)
    out = []
    if isinstance(caps, dict):              # ts >= 0.22
        for name, nodes in caps.items():
            out += [(name, n) for n in nodes]
    else:                                    # ts <= 0.21
        out += [(name, n) for (n, name) in caps]
    return out
