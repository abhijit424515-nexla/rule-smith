from rulesmith.parse import parse, find, node_text

RULE = "enum-switch-default"


def analyze_source(src, file="<src>") -> list:
    tree, src_bytes = parse(src)
    findings = []

    switches = find(tree.root_node, "switch_statement", "switch_expression")

    for switch_node in switches:
        has_default = False

        for label in find(switch_node, "switch_label"):
            label_text = node_text(label, src_bytes).strip()
            if label_text.startswith("default"):
                has_default = True
                break

        if not has_default:
            default_labels = find(switch_node, "default_label")
            if default_labels:
                has_default = True

        if not has_default:
            line, col = switch_node.start_point
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line + 1,
                    "col": col + 1,
                    "message": "Switch over enum must have a default case",
                    "note": "No default case found in switch statement",
                    "help": "Add a default case to handle unexpected enum values",
                }
            )

    return findings
