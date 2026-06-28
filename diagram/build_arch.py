"""Build ARCHITECTURE.excalidraw (editable) + ARCHITECTURE.svg (export) from one
source. Avoids a headless renderer; both files stay in sync by construction."""
import json

# box: id, x, y, w, h, label, fill
BOXES = [
    # core pipeline (y=300)
    ("J",  40, 300, 150, 92, "Java\nsource", "#c3fae8"),
    ("P",  230, 300, 175, 92, "Parse\n(tree-sitter)", "#a5d8ff"),
    ("PR", 445, 300, 200, 92, "Primitives\nCFG · dominance\n· escape", "#a5d8ff"),
    ("RU", 685, 300, 175, 92, "Rules\ndetective +\nprescriptive", "#fff3bf"),
    ("RE", 900, 300, 175, 92, "Report\ndiagnostic +\nevidence", "#b2f2bb"),
    ("FX", 1115, 300, 185, 92, "Fix / CI gate\ntry-with-resources\nexit 1", "#b2f2bb"),
    # authoring loop (y=120)
    ("AD", 230, 120, 175, 80, 'add\n"<english>"', "#d0bfff"),
    ("CG", 445, 120, 200, 80, "claude -p\ncodegen", "#d0bfff"),
    ("GT", 685, 120, 175, 80, "fixture gate\n(verify)", "#d0bfff"),
    # judgment (y=505)
    ("JU", 685, 505, 200, 92, "Judgment\nclaude -p · cached\nfilters false positives", "#ffd8a8"),
]
B = {b[0]: b for b in BOXES}

# arrows: x1,y1,x2,y2,label
def cx(b): return b[1] + b[3] / 2
def cy(b): return b[2] + b[4] / 2
def right(b): return (b[1] + b[3], cy(b))
def left(b): return (b[1], cy(b))
def top(b): return (cx(b), b[2])
def bot(b): return (cx(b), b[2] + b[4])

ARROWS = [
    (*right(B["J"]),  *left(B["P"]),  ""),
    (*right(B["P"]),  *left(B["PR"]), ""),
    (*right(B["PR"]), *left(B["RU"]), ""),
    (*right(B["RU"]), *left(B["RE"]), ""),
    (*right(B["RE"]), *left(B["FX"]), ""),
    (*right(B["AD"]), *left(B["CG"]), ""),
    (*right(B["CG"]), *left(B["GT"]), ""),
    (B["GT"][1]+90, B["GT"][2]+80, B["GT"][1]+90, 300, "install"),
    (B["RU"][1]+55, 392, B["RU"][1]+55, 505, "hybrid"),
    (B["JU"][1]+200, cy(B["JU"]), B["RE"][1]+88, 392, "kept"),
]

TITLE = "RuleSmith — architecture"
SUB = "deterministic primitives decide; Claude adjudicates only the residual"
NOTE = "claude -p = your own Claude Code session, no API key"


# ---------- excalidraw ----------
def excalidraw():
    els = []
    els.append({"type": "text", "id": "title", "x": 40, "y": 30, "width": 520, "height": 32,
                "text": TITLE, "fontSize": 28, "fontFamily": 1, "strokeColor": "#1e1e1e",
                "originalText": TITLE, "autoResize": True})
    els.append({"type": "text", "id": "sub", "x": 40, "y": 70, "width": 700, "height": 22,
                "text": SUB, "fontSize": 16, "fontFamily": 1, "strokeColor": "#495057",
                "originalText": SUB, "autoResize": True})
    for bid, x, y, w, h, label, fill in BOXES:
        els.append({"type": "rectangle", "id": bid, "x": x, "y": y, "width": w, "height": h,
                    "roundness": {"type": 3}, "backgroundColor": fill, "fillStyle": "solid",
                    "strokeColor": "#1e1e1e", "strokeWidth": 2, "roughness": 0,
                    "boundElements": [{"id": "t_" + bid, "type": "text"}]})
        els.append({"type": "text", "id": "t_" + bid, "x": x + 8, "y": y + 12,
                    "width": w - 16, "height": h - 24, "text": label, "fontSize": 16,
                    "fontFamily": 1, "strokeColor": "#1e1e1e", "textAlign": "center",
                    "verticalAlign": "middle", "containerId": bid,
                    "originalText": label, "autoResize": True})
    for i, (x1, y1, x2, y2, lbl) in enumerate(ARROWS):
        aid = "a%d" % i
        a = {"type": "arrow", "id": aid, "x": x1, "y": y1,
             "width": x2 - x1, "height": y2 - y1, "points": [[0, 0], [x2 - x1, y2 - y1]],
             "endArrowhead": "arrow", "strokeColor": "#343a40", "strokeWidth": 2,
             "roughness": 0}
        if lbl:
            a["boundElements"] = [{"id": "t_" + aid, "type": "text"}]
        els.append(a)
        if lbl:
            els.append({"type": "text", "id": "t_" + aid, "x": (x1+x2)/2 - 20, "y": (y1+y2)/2 - 10,
                        "width": 60, "height": 18, "text": lbl, "fontSize": 14,
                        "fontFamily": 1, "strokeColor": "#343a40", "textAlign": "center",
                        "verticalAlign": "middle", "containerId": aid,
                        "originalText": lbl, "autoResize": True})
    els.append({"type": "text", "id": "note", "x": 445, "y": 215, "width": 420, "height": 18,
                "text": NOTE, "fontSize": 14, "fontFamily": 1, "strokeColor": "#e8590c",
                "originalText": NOTE, "autoResize": True})
    return {"type": "excalidraw", "version": 2, "source": "rulesmith",
            "elements": els, "appState": {"viewBackgroundColor": "#ffffff"}}


# ---------- svg ----------
def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def _lines_svg(label, x, y, w, h):
    lines = label.split("\n")
    lh = 19
    total = lh * len(lines)
    sy = y + h / 2 - total / 2 + 14
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<text x="{x + w/2:.0f}" y="{sy + i*lh:.0f}" font-size="16" '
                   f'font-family="Helvetica,Arial,sans-serif" text-anchor="middle" '
                   f'fill="#1e1e1e">{esc(ln)}</text>')
    return "\n".join(out)


def svg():
    W, H = 1320, 640
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         '<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="3" '
         'orient="auto" markerUnits="strokeWidth">'
         '<path d="M0,0 L8,3 L0,6 z" fill="#343a40"/></marker></defs>',
         f'<text x="40" y="48" font-size="28" font-weight="bold" fill="#1e1e1e">{esc(TITLE)}</text>',
         f'<text x="40" y="78" font-size="16" fill="#495057">{esc(SUB)}</text>',
         f'<text x="445" y="270" font-size="14" fill="#e8590c">{esc(NOTE)}</text>']
    for bid, x, y, w, h, label, fill in BOXES:
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" '
                 f'fill="{fill}" stroke="#1e1e1e" stroke-width="2"/>')
        p.append(_lines_svg(label, x, y, w, h))
    for x1, y1, x2, y2, lbl in ARROWS:
        p.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                 f'stroke="#343a40" stroke-width="2" marker-end="url(#ah)"/>')
        if lbl:
            mx, my = (x1+x2)/2, (y1+y2)/2
            p.append(f'<rect x="{mx-26:.0f}" y="{my-11:.0f}" width="52" height="18" '
                     f'fill="#ffffff" opacity="0.9"/>')
            p.append(f'<text x="{mx:.0f}" y="{my+3:.0f}" font-size="13" '
                     f'text-anchor="middle" fill="#343a40">{esc(lbl)}</text>')
    p.append('</svg>')
    return "\n".join(p)


json.dump(excalidraw(), open("ARCHITECTURE.excalidraw", "w"), indent=1)
open("ARCHITECTURE.svg", "w").write(svg())
print("wrote ARCHITECTURE.excalidraw + ARCHITECTURE.svg")
