import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas

W, H = A4

BG      = colors.HexColor('#080c14')
SURFACE = colors.HexColor('#0d1520')
SURFACE2= colors.HexColor('#111d2e')
BORDER  = colors.HexColor('#0d1520')
ACCENT  = colors.HexColor('#00c8ff')
ACCENT2 = colors.HexColor('#0077ff')
WARN    = colors.HexColor('#ff6b35')
OK      = colors.HexColor('#00e5a0')
TEXT    = colors.HexColor('#cdd9e8')
MUTED   = colors.HexColor('#4a6580')
WHITE   = colors.HexColor('#ffffff')


def _wrap(c, text, max_width, font, size):
    c.setFont(font, size)
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if c.stringWidth(t, font, size) <= max_width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def generate_report(airport: str, arrival: str, departure: str,
                    layover: int, plan_text: str) -> bytes:

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    margin = 24
    cw = W - margin * 2

    def draw_bg():
        c.setFillColor(BG)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor('#0d1828'))
        c.setLineWidth(0.3)
        for x in range(0, int(W) + 28, 28):
            c.line(x, 0, x, H)
        for y in range(0, int(H) + 28, 28):
            c.line(0, y, W, y)

    draw_bg()

    # ── TOP BAR ──
    c.setFillColor(ACCENT2)
    c.rect(0, H - 8, W, 8, fill=1, stroke=0)

    # ── HEADER ──
    c.setFillColor(SURFACE)
    c.rect(0, H - 62, W, 54, fill=1, stroke=0)

    # Plane icon
    px, py = 28, H - 34
    c.setFillColor(ACCENT)
    c.rect(px, py - 3, 22, 6, fill=1, stroke=0)
    c.rect(px + 6, py - 10, 8, 20, fill=1, stroke=0)
    c.rect(px, py + 1, 5, 8, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(px + 22, py)
    p.lineTo(px + 30, py + 1)
    p.lineTo(px + 22, py + 3)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Logo
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(66, H - 36, "Layover")
    c.setFillColor(ACCENT)
    offset = c.stringWidth("Layover", "Helvetica-Bold", 18)
    c.drawString(66 + offset, H - 36, "AI")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawString(66, H - 50, "SMART TRANSIT PLANNER  —  PASSENGER REPORT")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawRightString(W - 24, H - 36, date.today().strftime("%B %d, %Y"))

    # ── ROUTE CARD ──
    cy = H - 118
    c.setFillColor(SURFACE2)
    c.roundRect(24, cy, W - 48, 44, 5, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.8)
    c.roundRect(24, cy, W - 48, 44, 5, fill=0, stroke=1)
    c.setFillColor(ACCENT)
    c.rect(24, cy, 4, 44, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(38, cy + 26, f"{airport}   {arrival}  ->  {departure}")

    h_ = layover // 60
    m_ = layover % 60
    dur = f"{h_}h {m_:02d}min" if h_ > 0 else f"{m_} min"

    if layover < 60:
        badge_col, urgency = WARN, "TIGHT"
    elif layover < 120:
        badge_col, urgency = ACCENT, "MANAGEABLE"
    else:
        badge_col, urgency = OK, "COMFORTABLE"

    bw = 90
    bx = W - 24 - bw - 8
    c.setFillColor(badge_col)
    c.roundRect(bx, cy + 8, bw, 28, 4, fill=1, stroke=0)
    c.setFillColor(BG)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(bx + bw / 2, cy + 22, urgency)
    c.setFont("Helvetica", 8)
    c.drawCentredString(bx + bw / 2, cy + 12, dur)

    # ── DIVIDER ──
    div_y = cy - 14
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(24, div_y, W - 24, div_y)

    # ── CONTENT ──
    y = div_y - 14
    left = 28
    cw = W - left - 24

    for raw in plan_text.split('\n'):
        line = raw.strip()

        if y < 36:
            c.showPage()
            draw_bg()
            y = H - 30

        if not line:
            y -= 5
            continue

        # H2 — blue bar + white text, no background
        if line.startswith('## '):
            text = line[3:].replace('**', '').strip()
            y -= 6
            c.setFillColor(ACCENT)
            c.rect(left - 4, y - 5, 3, 18, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(left + 4, y + 4, text)
            y -= 22

        # H3
        elif line.startswith('### '):
            text = line[4:].replace('**', '').strip()
            y -= 4
            c.setFillColor(ACCENT)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(left, y, text.upper())
            y -= 13

        # List item
        elif line.startswith('- ') or (len(line) > 2 and line[0].isdigit() and line[1] == '.'):
            text = line[2:].replace('**', '').strip() if line.startswith('- ') else line[3:].replace('**', '').strip()
            c.setFillColor(ACCENT)
            c.circle(left + 4, y - 2, 1.8, fill=1, stroke=0)
            c.setFillColor(TEXT)
            c.setFont("Helvetica", 8.5)
            for wl in _wrap(c, text, cw - 16, "Helvetica", 8.5):
                c.drawString(left + 12, y, wl)
                y -= 12
            y -= 2

        # Warning line
        elif any(kw in line.upper() for kw in ['TIGHT', 'URGENT', 'WARNING']):
            text = line.replace('**', '').replace('## ', '').strip()
            c.setFillColor(colors.HexColor('#1e1008'))
            c.roundRect(left - 4, y - 6, cw + 8, 16, 3, fill=1, stroke=0)
            c.setStrokeColor(WARN)
            c.setLineWidth(1.5)
            c.line(left - 4, y - 6, left - 4, y + 10)
            c.setFillColor(WARN)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(left + 4, y, text)
            y -= 22

        # Normal text
        else:
            text = line.replace('**', '').strip()
            if not text:
                continue
            c.setFillColor(TEXT)
            c.setFont("Helvetica", 8.5)
            for wl in _wrap(c, text, cw, "Helvetica", 8.5):
                c.drawString(left, y, wl)
                y -= 12

    # ── FOOTER ──
    c.setFillColor(SURFACE)
    c.rect(0, 0, W, 22, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.4)
    c.line(0, 22, W, 22)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 6.5)
    c.drawString(24, 8, "Generated by LayoverAI  —  AI-powered airport transit assistant")
    c.drawRightString(W - 24, 8, "For informational purposes only — verify details with airline staff")

    c.save()
    buf.seek(0)
    return buf.read()