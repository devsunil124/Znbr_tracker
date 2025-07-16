from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

def build_pdf(cell_id, cell_data, cycle_data, output_path=""):
    filename = os.path.join(output_path or "media", f"{cell_id}.pdf")
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Zn–Br Battery Report: {cell_id}")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Felt Type: {cell_data.felt_type}")
    y -= 20
    c.drawString(50, y, f"Sealing Type: {cell_data.sealing_type}")
    y -= 20
    c.drawString(50, y, f"Notes: {cell_data.notes}")
    y -= 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Cycle Data")
    y -= 25
    c.setFont("Helvetica", 10)

    for cycle in cycle_data:
        line = f"Cycle {cycle.cycle_no} | CE%: {cycle.ce_pct} | ΔV: {cycle.delta_V} | pH: {cycle.pH}"
        c.drawString(60, y, line)
        y -= 15
        if y < 100:
            c.showPage()
            y = height - 50

    c.save()
    return filename
