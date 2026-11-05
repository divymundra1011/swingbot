import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def _sheet(wb, name, head, rows):
    ws = wb.create_sheet(name); ws.append(head)
    for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2B4BD8")
    for r in rows: ws.append(r)
    for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = max(12, max(len(str(c.value or "")) for c in col) + 2)

def excel(s, path):
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    _sheet(wb, "Calls", ["Stock","Tier","3d move %","Entry low","Entry high","Stop","Target","Qty","Amount","Risk","Verdict"],
           [[c["sym"],c["tier"],c["drop3d"],c["entry_lo"],c["entry_hi"],c["stop"],c["target"],c["qty"],c["size"],c["risk_amt"],"Take" if c["take"] else "Skip"] for c in s["calls"]])
    _sheet(wb, "Open positions", ["Stock","Opened","Entry","Qty","Stop","Target","Last","Days","Open P&L"],
           [[p["sym"],p["open_date"],p["entry"],p["qty"],p["stop"],p["target"],p["last"],p["days"],round((p["last"]-p["entry"])*p["qty"])] for p in s["positions"]])
    _sheet(wb, "Closed trades", ["Stock","Opened","Closed","Entry","Exit","Qty","P&L","Reason"],
           [[h["sym"],h["opened"],h["closed"],h["entry"],h["exit"],h["qty"],h["pnl"],h["why"]] for h in s["history"]])
    _sheet(wb, "Equity", ["Date","Account value"], s["equity_log"])
    wb.save(path)

def pdf(s, path, notes):
    st = getSampleStyleSheet(); doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    def tbl(head, rows):
        t = Table([head] + rows if rows else [head, ["none"] + [""]*(len(head)-1)], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2B4BD8")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),.25,colors.grey)])); return t
    eq = s["equity_log"][-1][1] if s["equity_log"] else s["capital"]
    el = [Paragraph(f"Swing Desk daily report, data as of {s['asof']} (PAPER MODE)", st["Title"]),
          Paragraph(f"Paper account value Rs {eq:,.0f} | realized P&L Rs {sum(h['pnl'] for h in s['history']):,.0f} | open positions {len(s['positions'])}", st["Normal"]), Spacer(1,8)]
    if notes: el += [Paragraph("Today: " + "; ".join(notes), st["Normal"]), Spacer(1,8)]
    el += [Paragraph("New calls for next session", st["Heading3"]), tbl(["Stock","Tier","3d %","Entry zone","Stop","Target","Qty","Amount","Risk","Verdict"],
           [[c["sym"],c["tier"],c["drop3d"],f"{c['entry_lo']}-{c['entry_hi']}",c["stop"],c["target"],c["qty"],c["size"],c["risk_amt"],"Take" if c["take"] else "Skip"] for c in s["calls"]]), Spacer(1,8),
           Paragraph("Open positions", st["Heading3"]), tbl(["Stock","Opened","Entry","Qty","Stop","Target","Last","Days","P&L"],
           [[p["sym"],p["open_date"],p["entry"],p["qty"],p["stop"],p["target"],p["last"],p["days"],round((p["last"]-p["entry"])*p["qty"])] for p in s["positions"]]), Spacer(1,8),
           Paragraph("Last 15 closed trades", st["Heading3"]), tbl(["Stock","Closed","Entry","Exit","Qty","P&L","Reason"],
           [[h["sym"],h["closed"],h["entry"],h["exit"],h["qty"],h["pnl"],h["why"]] for h in s["history"][-15:]]),
           Spacer(1,8), Paragraph("Strategy is unvalidated out-of-sample. Paper trading only.", st["Italic"])]
    doc.build(el)
