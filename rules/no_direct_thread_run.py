# rule: do not call the run() method on a Thread directly; call start() to run it on a new thread

from rulesmith.parse import parse, find, span, node_text

RULE = "no-direct-thread-run"


def _thread_vars(method, src_bytes):
    """Names of locals/params whose declared type is exactly Thread."""
    names = set()
    for decl in find(method, "local_variable_declaration", "formal_parameter"):
        t = decl.child_by_field_name("type")
        if t is None or node_text(t, src_bytes) != "Thread":
            continue
        if decl.type == "formal_parameter":
            n = decl.child_by_field_name("name")
            if n is not None:
                names.add(node_text(n, src_bytes))
        else:
            for vd in find(decl, "variable_declarator"):
                n = vd.child_by_field_name("name")
                if n is not None:
                    names.add(node_text(n, src_bytes))
    return names


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    seen = set()

    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        tvars = _thread_vars(method, src_bytes)

        for inv in find(method, "method_invocation"):
            if inv.start_byte in seen:
                continue
            name = inv.child_by_field_name("name")
            if name is None or node_text(name, src_bytes) != "run":
                continue
            args = inv.child_by_field_name("arguments")
            if args is not None and node_text(args, src_bytes).strip() != "()":
                continue  # run() takes no args; anything else isn't Thread.run

            obj = inv.child_by_field_name("object")
            if obj is None:
                continue

            is_thread = False
            if obj.type == "object_creation_expression":
                ot = obj.child_by_field_name("type")
                if ot is not None and node_text(ot, src_bytes) == "Thread":
                    is_thread = True
            elif obj.type == "identifier":
                if node_text(obj, src_bytes) in tvars:
                    is_thread = True

            if not is_thread:
                continue

            seen.add(inv.start_byte)
            line, col, _, _ = span(inv)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Calling run() executes on the current thread, not a new one",
                    "note": f"run() invoked on a Thread at line {line}",
                    "help": "Call start() to run the Thread on a new thread",
                }
            )

    return findings
