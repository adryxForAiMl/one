from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


OUT = Path(__file__).resolve().parents[1] / "docs" / "KAVACH_Project_Deck.pptx"
OUT.parent.mkdir(parents=True, exist_ok=True)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

BG = RGBColor(5, 11, 22)
PANEL = RGBColor(12, 22, 40)
PANEL_2 = RGBColor(16, 31, 54)
WHITE = RGBColor(241, 245, 249)
MUTED = RGBColor(148, 163, 184)
CYAN = RGBColor(34, 211, 238)
BLUE = RGBColor(56, 189, 248)
PURPLE = RGBColor(167, 139, 250)
GREEN = RGBColor(52, 211, 153)
AMBER = RGBColor(251, 191, 36)
RED = RGBColor(248, 113, 113)


def fill_shape(shape, color, transparency=0):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.fill.transparency = transparency
    shape.line.fill.background()


def text_box(slide, text, x, y, w, h, size=18, color=WHITE, bold=False,
             align=PP_ALIGN.LEFT, font="Aptos", margin=0.08, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_bg(slide, section="KAVACH / ZERO-TRUST API SECURITY"):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG
    # Subtle grid and cyan accent line.
    for x in range(0, 14):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(0), Inches(0.006), Inches(7.5))
        fill_shape(line, RGBColor(10, 30, 50), 35)
    for y in range(0, 8):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(y), Inches(13.333), Inches(0.006))
        fill_shape(line, RGBColor(10, 30, 50), 35)
    text_box(slide, section, 0.55, 7.06, 6, 0.2, 8, CYAN, True, font="Aptos Mono")
    text_box(slide, f"{len(prs.slides):02d}", 12.15, 7.04, 0.55, 0.22, 8, MUTED, True, align=PP_ALIGN.RIGHT, font="Aptos Mono")


def title(slide, eyebrow, heading, subheading=None):
    text_box(slide, eyebrow.upper(), 0.7, 0.45, 5.5, 0.28, 10, CYAN, True, font="Aptos Mono")
    text_box(slide, heading, 0.65, 0.8, 12, 0.72, 30, WHITE, True)
    if subheading:
        text_box(slide, subheading, 0.7, 1.56, 11.5, 0.42, 12, MUTED)


def panel(slide, x, y, w, h, color=PANEL, line=RGBColor(30, 61, 86)):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    fill_shape(shape, color)
    shape.line.color.rgb = line
    shape.line.width = Pt(0.8)
    return shape


def pill(slide, label, x, y, w, color=CYAN):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(0.3))
    fill_shape(shape, color, 78)
    shape.line.color.rgb = color
    text_box(slide, label.upper(), x + 0.06, y + 0.025, w - 0.12, 0.22, 8, color, True, font="Aptos Mono", align=PP_ALIGN.CENTER)


def bullet_list(slide, items, x, y, w, line_h=0.42, size=14, color=WHITE, accent=CYAN):
    for i, item in enumerate(items):
        cy = y + i * line_h
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(cy + 0.11), Inches(0.09), Inches(0.09))
        fill_shape(dot, accent)
        text_box(slide, item, x + 0.2, cy, w - 0.2, line_h, size, color)


def arrow(slide, x1, y1, x2, y2, color=CYAN):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(2)
    conn.line.end_arrowhead = True
    return conn


def node(slide, label, sub, x, y, color=CYAN, w=1.65):
    panel(slide, x, y, w, 0.98, PANEL_2, color)
    text_box(slide, label, x + 0.1, y + 0.18, w - 0.2, 0.25, 13, color, True, align=PP_ALIGN.CENTER)
    text_box(slide, sub, x + 0.1, y + 0.51, w - 0.2, 0.25, 9, MUTED, align=PP_ALIGN.CENTER, font="Aptos Mono")


# 1. Cover
slide = prs.slides.add_slide(blank)
add_bg(slide, "KAVACH / ZERO-TRUST API SECURITY")
text_box(slide, "KAVACH", 0.8, 1.12, 7.5, 0.9, 50, WHITE, True)
text_box(slide, "Zero-Trust API Security Platform", 0.85, 2.02, 7.5, 0.48, 22, CYAN, True)
text_box(slide, "Discover. Verify. Explain. Protect.", 0.88, 2.65, 7.5, 0.4, 18, MUTED)
pill(slide, "Project showcase", 0.88, 3.45, 1.65, CYAN)
pill(slide, "AI security intelligence", 2.68, 3.45, 2.15, PURPLE)
# Radar-style visual
for r, alpha in [(2.45, 88), (1.85, 82), (1.25, 74), (0.65, 55)]:
    ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.2 - r / 2), Inches(3.65 - r / 2), Inches(r), Inches(r))
    ring.fill.background()
    ring.line.color.rgb = CYAN
    ring.line.transparency = alpha
    ring.line.width = Pt(1.2)
beam = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9.2), Inches(1.9), Inches(0.02), Inches(3.5))
fill_shape(beam, CYAN, 25)
text_box(slide, "API1:2023  /  CWE-639", 8.05, 5.55, 3.2, 0.3, 11, RED, True, align=PP_ALIGN.CENTER, font="Aptos Mono")
text_box(slide, "A practical security intelligence cockpit for authenticated API authorization testing.", 0.9, 5.95, 7.3, 0.48, 13, MUTED)

# 2. Problem
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "01 / THE PROBLEM", "Authentication is not authorization", "A valid token should not grant access to another user's object.")
panel(slide, 0.7, 2.2, 5.55, 3.75, PANEL)
pill(slide, "The failure mode", 1.0, 2.5, 1.45, RED)
text_box(slide, "Broken Object Level Authorization", 1.0, 3.0, 4.7, 0.5, 21, WHITE, True)
text_box(slide, "A caller is authenticated correctly, but the API forgets to enforce ownership at the object boundary.", 1.0, 3.62, 4.55, 0.72, 15, MUTED)
bullet_list(slide, ["User A requests Object #102", "Object #102 belongs to User B", "API returns HTTP 200 + private data"], 1.0, 4.55, 4.6, 0.38, 13, WHITE, RED)
panel(slide, 6.65, 2.2, 5.95, 3.75, PANEL_2, RGBColor(77, 29, 56))
pill(slide, "KAVACH response", 6.95, 2.5, 1.55, GREEN)
text_box(slide, "Prove the boundary failure", 6.95, 3.0, 5.1, 0.45, 21, WHITE, True)
text_box(slide, "KAVACH compares multiple authenticated identities, verifies ownership mismatches, fingerprints responses, and produces an explainable verdict.", 6.95, 3.62, 5.0, 0.78, 15, MUTED)
text_box(slide, "Deterministic evidence  /  Explainable risk  /  Actionable remediation", 6.95, 5.15, 5.05, 0.38, 12, CYAN, True, font="Aptos Mono")

# 3. Solution architecture
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "02 / THE PLATFORM", "One workflow from discovery to remediation", "The system turns a raw API URL into a traceable security decision.")
node(slide, "WEB CONSOLE", "React + TypeScript", 0.8, 3.0, CYAN, 1.8)
node(slide, "KAVACH CORE", "FastAPI engine", 3.1, 3.0, BLUE, 1.8)
node(slide, "NETRA", "OpenAPI discovery", 5.4, 2.2, PURPLE, 1.8)
node(slide, "RAKSHA", "BOLA testing", 5.4, 3.8, RED, 1.8)
node(slide, "DRISHTI", "Local ML risk", 8.1, 2.2, AMBER, 1.8)
node(slide, "PRAMAAN", "Evidence engine", 8.1, 3.8, GREEN, 1.8)
node(slide, "TRACE", "Attack path", 10.8, 2.2, CYAN, 1.8)
node(slide, "SURAKSHA", "Remediation", 10.8, 3.8, GREEN, 1.8)
arrow(slide, 2.6, 3.5, 3.1, 3.5)
arrow(slide, 4.9, 3.3, 5.35, 2.75, PURPLE)
arrow(slide, 4.9, 3.7, 5.35, 4.25, RED)
arrow(slide, 7.4, 2.7, 8.05, 2.7, AMBER)
arrow(slide, 7.4, 4.3, 8.05, 4.3, GREEN)
arrow(slide, 10.1, 2.7, 10.75, 2.7, CYAN)
arrow(slide, 10.1, 4.3, 10.75, 4.3, GREEN)

# 4. Pipeline
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "03 / VERIFICATION PIPELINE", "Seven stages, one auditable decision", "Every scan step leaves a visible state, signal, or evidence artifact.")
stages = [
    ("01", "TARGET", "Validate URL", CYAN),
    ("02", "NETRA", "Discover OpenAPI", PURPLE),
    ("03", "ACCESS", "Map identities", BLUE),
    ("04", "RAKSHA", "Test ownership", RED),
    ("05", "DRISHTI", "Score risk", AMBER),
    ("06", "PRAMAAN", "Capture proof", GREEN),
    ("07", "VERDICT", "Remediate", WHITE),
]
for i, (num, label, sub, color) in enumerate(stages):
    x = 0.75 + i * 1.78
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.53), Inches(2.55), Inches(0.62), Inches(0.62))
    fill_shape(circle, color, 72)
    circle.line.color.rgb = color
    text_box(slide, num, x + 0.53, 2.71, 0.62, 0.18, 10, color, True, align=PP_ALIGN.CENTER, font="Aptos Mono")
    if i < len(stages) - 1:
        arrow(slide, x + 1.17, 2.86, x + 1.73, 2.86, RGBColor(53, 82, 108))
    text_box(slide, label, x, 3.45, 1.7, 0.25, 11, color, True, align=PP_ALIGN.CENTER, font="Aptos Mono")
    text_box(slide, sub, x, 3.8, 1.7, 0.38, 11, MUTED, align=PP_ALIGN.CENTER)
panel(slide, 1.25, 4.8, 10.85, 1.0, PANEL)
text_box(slide, "Operator outcome", 1.55, 5.05, 1.55, 0.25, 10, CYAN, True, font="Aptos Mono")
text_box(slide, "A reproducible finding with request context, response proof, risk score, attack path, and developer fix guidance.", 3.15, 4.98, 8.45, 0.35, 15, WHITE, True)

# 5. Demo
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "04 / CONTROLLED DEMO", "The KAVACH Lab makes the risk visible", "An intentionally vulnerable API provides a safe, repeatable demonstration target.")
panel(slide, 0.75, 2.2, 5.6, 3.75, PANEL)
pill(slide, "Sandbox target", 1.05, 2.5, 1.35, CYAN)
text_box(slide, "http://127.0.0.1:8000", 1.05, 3.0, 4.8, 0.4, 20, WHITE, True, font="Aptos Mono")
bullet_list(slide, ["User A owns Order #101", "User B owns Order #102", "Both identities have valid tokens", "Object route returns foreign records"], 1.05, 3.75, 4.65, 0.4, 14, WHITE, CYAN)
panel(slide, 6.7, 2.2, 5.9, 3.75, PANEL_2, RGBColor(93, 38, 44))
pill(slide, "Verified result", 7.0, 2.5, 1.35, RED)
text_box(slide, "2 BOLA findings", 7.0, 3.0, 4.8, 0.45, 24, RED, True)
text_box(slide, "User A -> Order #102", 7.0, 3.72, 4.5, 0.32, 15, WHITE, True, font="Aptos Mono")
text_box(slide, "User B -> Order #101", 7.0, 4.2, 4.5, 0.32, 15, WHITE, True, font="Aptos Mono")
text_box(slide, "HTTP 200  /  ownership mismatch  /  CRITICAL", 7.0, 5.05, 4.9, 0.3, 11, AMBER, True, font="Aptos Mono")

# 6. AI
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "05 / DRISHTI INTELLIGENCE", "AI that explains the verdict", "Local inference keeps security signals inside the operator's environment.")
panel(slide, 0.75, 2.15, 4.0, 3.85, PANEL)
pill(slide, "Model", 1.05, 2.48, 0.85, PURPLE)
text_box(slide, "Random Forest", 1.05, 3.0, 3.1, 0.4, 22, WHITE, True)
text_box(slide, "Local scikit-learn inference", 1.05, 3.55, 3.2, 0.3, 13, PURPLE, True, font="Aptos Mono")
bullet_list(slide, ["11 behavioral features", "600 synthetic training samples", "Confidence + anomaly scores", "No external telemetry dependency"], 1.05, 4.15, 3.2, 0.4, 13, WHITE, PURPLE)
panel(slide, 5.05, 2.15, 7.55, 3.85, PANEL_2)
text_box(slide, "Risk signal composition", 5.4, 2.5, 3.5, 0.3, 12, MUTED, True, font="Aptos Mono")
metrics = [("Ownership mismatch", "100%", RED), ("Cross identity", "100%", CYAN), ("Successful access", "100%", AMBER), ("Response anomaly", "100%", PURPLE)]
for i, (label, value, color) in enumerate(metrics):
    y = 3.05 + i * 0.62
    text_box(slide, label, 5.4, y, 2.2, 0.25, 12, WHITE)
    bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.75), Inches(y + 0.03), Inches(3.65), Inches(0.18))
    fill_shape(bar, RGBColor(30, 48, 70))
    fill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.75), Inches(y + 0.03), Inches(3.65), Inches(0.18))
    fill_shape(fill, color)
    text_box(slide, value, 11.65, y - 0.03, 0.55, 0.25, 12, color, True, align=PP_ALIGN.RIGHT, font="Aptos Mono")
text_box(slide, "THREAT VERIFIED  /  IMMEDIATE REMEDIATION", 5.4, 5.48, 5.8, 0.28, 13, RED, True, font="Aptos Mono")

# 7. Trace
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "06 / TRACE WORKSPACE", "From finding to attack story", "Trace turns raw scanner output into an investigation a human can follow.")
trace_nodes = [("USER A", "identity", CYAN), ("TOKEN", "auth", PURPLE), ("GET /orders/102", "route", BLUE), ("OBJECT #102", "owner: User B", AMBER), ("HTTP 200", "foreign data", RED), ("BOLA", "verified", RED)]
for i, (label, sub, color) in enumerate(trace_nodes):
    x = 0.65 + i * 2.08
    node(slide, label, sub, x, 2.65, color, 1.75)
    if i < len(trace_nodes) - 1:
        arrow(slide, x + 1.76, 3.14, x + 2.03, 3.14, color)
panel(slide, 1.3, 4.45, 10.7, 1.15, PANEL)
text_box(slide, "Evidence Inspector", 1.65, 4.72, 1.8, 0.25, 11, CYAN, True, font="Aptos Mono")
text_box(slide, "Request  ->  Response  ->  Ownership mismatch  ->  Reasoning  ->  Remediation", 3.55, 4.68, 7.95, 0.35, 15, WHITE, True)
text_box(slide, "Every square is selectable. Every edge explains the security transition.", 1.65, 5.2, 8.8, 0.22, 11, MUTED)

# 8. Product UI
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "07 / PRODUCT EXPERIENCE", "A security cockpit, not a raw API console", "The UI is designed for scanning, investigation, and executive communication.")
features = [
    ("SCAN", "Target URL + identities", CYAN),
    ("SURFACE", "Endpoint inventory", BLUE),
    ("FINDINGS", "Risk-ranked evidence", RED),
    ("TRACE", "Attack path graph", PURPLE),
    ("REPORTS", "JSON / CSV / print", GREEN),
    ("LAB", "Controlled demo API", AMBER),
]
for i, (label, desc, color) in enumerate(features):
    x = 0.8 + (i % 3) * 4.1
    y = 2.25 + (i // 3) * 1.65
    panel(slide, x, y, 3.45, 1.2, PANEL, color)
    text_box(slide, label, x + 0.22, y + 0.23, 2.5, 0.22, 11, color, True, font="Aptos Mono")
    text_box(slide, desc, x + 0.22, y + 0.58, 2.9, 0.25, 15, WHITE, True)
text_box(slide, "Professional signal: the interface makes evidence, confidence, and next action visible at the same time.", 1.0, 5.7, 11.2, 0.35, 15, MUTED, align=PP_ALIGN.CENTER)

# 9. Results
slide = prs.slides.add_slide(blank)
add_bg(slide)
title(slide, "08 / LIVE RESULT", "A complete scan in one evidence chain", "The controlled demo returns a deterministic, explainable security verdict.")
result_cards = [("3", "Endpoints discovered", CYAN), ("1", "Object route tested", PURPLE), ("2", "BOLA findings", RED), ("100", "Risk score", AMBER)]
for i, (value, label, color) in enumerate(result_cards):
    x = 0.75 + i * 3.08
    panel(slide, x, 2.35, 2.65, 1.65, PANEL, color)
    text_box(slide, value, x + 0.18, 2.68, 2.25, 0.52, 29, color, True, align=PP_ALIGN.CENTER)
    text_box(slide, label, x + 0.18, 3.35, 2.25, 0.25, 11, MUTED, True, align=PP_ALIGN.CENTER)
panel(slide, 1.35, 4.65, 10.55, 0.95, PANEL_2, RGBColor(77, 29, 56))
text_box(slide, "THREAT VERIFIED", 1.7, 4.9, 2.1, 0.28, 14, RED, True, font="Aptos Mono")
text_box(slide, "Confidence 100%  /  Anomaly SEVERE  /  Priority IMMEDIATE REMEDIATION", 4.0, 4.88, 7.25, 0.3, 14, WHITE, True)

# 10. Roadmap / close
slide = prs.slides.add_slide(blank)
add_bg(slide, "KAVACH / NEXT HORIZON")
title(slide, "09 / NEXT HORIZON", "From strong demo to production platform", "The foundation is ready; the next step is operational maturity.")
roadmap = [
    ("NOW", "Deterministic BOLA proof", "OpenAPI discovery, multi-identity testing, Trace evidence", CYAN),
    ("NEXT", "Production operations", "Persistent scan history, RBAC, queues, rate limits, HTTPS", PURPLE),
    ("LATER", "Security intelligence", "Real-world training data, regression baselines, policy packs", AMBER),
]
for i, (tag, heading, desc, color) in enumerate(roadmap):
    x = 0.85 + i * 4.15
    panel(slide, x, 2.35, 3.5, 2.3, PANEL, color)
    pill(slide, tag, x + 0.25, 2.65, 0.72, color)
    text_box(slide, heading, x + 0.25, 3.22, 3.0, 0.35, 17, WHITE, True)
    text_box(slide, desc, x + 0.25, 3.82, 2.95, 0.55, 12, MUTED)
text_box(slide, "KAVACH", 0.85, 5.55, 2.2, 0.45, 24, CYAN, True)
text_box(slide, "Discover. Verify. Explain. Protect.", 3.05, 5.62, 5.5, 0.3, 15, WHITE, True)
text_box(slide, "Thank you", 10.4, 5.6, 2.0, 0.35, 18, MUTED, align=PP_ALIGN.RIGHT)

# Fix slide numbers after all slides are created.
for index, slide in enumerate(prs.slides, start=1):
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text == "00":
            shape.text_frame.paragraphs[0].runs[0].text = f"{index:02d}"

prs.save(OUT)
print(f"Created {OUT}")
