# rule: flag tell-don't-ask: code that calls a getter on an object and then, based on that returned value, calls a mutating setter back on the same object — the decision should live inside the object, not outside it
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "tell-dont-ask"

GET_PREFIXES = ("get", "is", "has")


def _obj_name(inv, src):
    obj = inv.child_by_field_name("object")
    if obj is None or obj.type != "identifier":
        return None
    return node_text(obj, src)


def _mname(inv, src):
    n = inv.child_by_field_name("name")
    return node_text(n, src) if n is not None else ""


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        for iff in find(method, "if_statement"):
            cond = iff.child_by_field_name("condition")
            cons = iff.child_by_field_name("consequence")
            alt = iff.child_by_field_name("alternative")
            if cond is None or cons is None:
                continue
            # getters called on an object in the condition
            getters = {}
            for inv in find(cond, "method_invocation"):
                obj = _obj_name(inv, sb)
                m = _mname(inv, sb)
                if obj and any(m.startswith(p) for p in GET_PREFIXES):
                    getters.setdefault(obj, m)
            if not getters:
                continue
            # a setter on the SAME object inside a branch = tell-don't-ask smell
            bodies = [cons]
            if alt is not None:
                bodies.append(alt)
            hit = None
            for body in bodies:
                for inv in find(body, "method_invocation"):
                    obj = _obj_name(inv, sb)
                    m = _mname(inv, sb)
                    if obj in getters and m.startswith("set"):
                        hit = (obj, getters[obj], m)
                        break
                if hit:
                    break
            if hit:
                obj, g, s = hit
                ln, c = span(iff)[0], span(iff)[1]
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": ln,
                        "col": c,
                        "message": f"Tell-don't-ask: decide on {obj}.{g}() then {obj}.{s}() outside the object.",
                        "note": node_text(iff, sb)[:200],
                        "help": f"Move this get/check/set into a method on {obj}.",
                    }
                )
    return findings
