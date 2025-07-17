from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os


def build_pdf(cell_id, cell_data, cycle_data, output_path=""):
    filename = os.path.join(output_path or "media", f"{cell_id}.pdf")
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Zn–Br Battery Report: {cell_id}")
    y -= 40

    # Draw start photo if exists
    if cell_data.start_photo and os.path.exists(cell_data.start_photo):
        try:
            img_width = 6 * cm
            img_height = 4.5 * cm
            c.drawImage(
                cell_data.start_photo,
                50,
                y - img_height,
                width=img_width,
                height=img_height,
            )
            y -= img_height + 20
        except Exception as e:
            c.setFont("Helvetica", 10)
            c.drawString(50, y, f"⚠️ Error loading start image: {str(e)}")
            y -= 20
    else:
        c.setFont("Helvetica", 10)
        c.drawString(50, y, "⚠️ No start photo available.")
        y -= 20

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
        line = f"Cycle {cycle.cycle_no} | CE%: {cycle.ce_pct} | ΔV: {cycle.delta_V} "
        c.drawString(60, y, line)
        y -= 15

        # Draw cycle photo if exists
        if cycle.photo_path and os.path.exists(cycle.photo_path):
            try:
                img_width = 6 * cm
                img_height = 4.5 * cm

                # If space is tight, go to next page
                if y < img_height + 60:
                    c.showPage()
                    y = height - 50

                c.drawImage(
                    cycle.photo_path,
                    60,
                    y - img_height,
                    width=img_width,
                    height=img_height,
                )
                y -= img_height + 10
            except Exception as e:
                c.drawString(60, y, f"⚠️ Error loading cycle image: {str(e)}")
                y -= 15

        # Add spacing between cycles
        y -= 10

        # Page break if needed
        if y < 100:
            c.showPage()
            y = height - 50

    c.save()
    return filename
