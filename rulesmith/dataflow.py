"""Data-flow primitives: escape analysis + def-use helpers.

Lightweight and conservative. escapes() over-approximates (favours NOT
flagging) so the leak rule errs toward false negatives, not noisy positives.
"""
from .parse import walk


def _ident_uses(root, name):
    return [n for n in walk(root) if n.type == "identifier"
            and n.text.decode("utf8", "replace") == name]


def _ancestor(node, *types):
    p = node.parent
    want = set(types)
    while p is not None:
        if p.type in want:
            return p
        p = p.parent
    return None


def escapes(method_ts, name):
    """True if local `name` escapes the method: returned, wrapped in a
    constructor, or assigned to another lvalue. Receiver position (name.foo())
    and its own declarator do NOT count as escape."""
    for n in _ident_uses(method_ts, name):
        p = n.parent
        if p is None:
            continue
        # own declaration: `T name = ...`
        if p.type == "variable_declarator" and p.child_by_field_name("name") is n:
            continue
        # passed to a constructor: `new Wrapper(name)` -- wrapper takes
        # ownership (closing it closes name). Plain method-call args are
        # transient use, NOT ownership transfer, so they don't escape.
        if p.type == "argument_list" and p.parent is not None \
                and p.parent.type == "object_creation_expression":
            return True
        # returned
        if _ancestor(n, "return_statement") is not None:
            return True
        # assigned to a different lvalue: `other = name`
        asg = _ancestor(n, "assignment_expression")
        if asg is not None:
            right = asg.child_by_field_name("right")
            left = asg.child_by_field_name("left")
            if right is not None and (right is n or n in list(walk(right))):
                if left is not None and left.text != n.text:
                    return True
    return False


def defs_uses(method_ts, name):
    """Minimal def-use: (defs, uses) ts nodes for a local `name`.
    def = declarator or assignment target; use = any other reference."""
    defs, uses = [], []
    for n in _ident_uses(method_ts, name):
        p = n.parent
        if p is not None and p.type == "variable_declarator" \
                and p.child_by_field_name("name") is n:
            defs.append(n)
        elif p is not None and p.type == "assignment_expression" \
                and p.child_by_field_name("left") is n:
            defs.append(n)
        else:
            uses.append(n)
    return defs, uses
