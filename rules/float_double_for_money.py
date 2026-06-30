# rule: float/double must not be used for monetary or other exact decimal values; use BigDecimal, int, or long.
# (authored by RuleSmith from the description above)

# rule: float/double must not be used for monetary or other exact decimal values; use BigDecimal, int, or long.
"""Flag float/double declarations whose name implies money or exact decimals."""

from rulesmith.parse import parse, find, span, node_text

RULE = "float-double-for-money"

_FLOATY = {"float", "double", "Float", "Double"}

# name fragments that imply money / exact decimal accounting
_MONEY = (
    "money",
    "price",
    "cost",
    "amount",
    "total",
    "balance",
    "salary",
    "payment",
    "fee",
    "tax",
    "discount",
    "currency",
    "cash",
    "dollar",
    "cent",
    "wage",
    "budget",
    "revenue",
    "profit",
    "refund",
    "charge",
    "fare",
    "invoice",
    "debit",
    "credit",
    "interest",
    "premium",
    "subtotal",
)


def _is_money_name(name):
    low = name.lower()
    return any(k in low for k in _MONEY)


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    seen = set()
    decls = find(
        tree.root_node,
        "local_variable_declaration",
        "field_declaration",
        "formal_parameter",
    )
    for d in decls:
        tnode = d.child_by_field_name("type")
        if tnode is None or node_text(tnode, src_b) not in _FLOATY:
            continue
        ftype = node_text(tnode, src_b)
        # formal_parameter has a direct name field; declarations carry declarators
        names = []
        pname = d.child_by_field_name("name")
        if pname is not None:
            names.append(pname)
        else:
            for vd in find(d, "variable_declarator"):
                nn = vd.child_by_field_name("name")
                if nn is not None:
                    names.append(nn)
        for nn in names:
            name = node_text(nn, src_b)
            if not _is_money_name(name):
                continue
            line, col, _, _ = span(nn)
            if (line, col) in seen:
                continue
            seen.add((line, col))
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"'{name}' is declared as {ftype}; monetary/exact-decimal values lose precision in binary floating point.",
                    "note": f"{ftype} {name}",
                    "help": "Use BigDecimal for exact decimals, or int/long of the smallest unit (e.g. cents).",
                }
            )
    return out
