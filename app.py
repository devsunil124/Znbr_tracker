# app.py

import streamlit as st
from services.pdf import build_pdf
from services.excel import build_excel
from models.base import Cell, engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os


# Set up DB session
Session = sessionmaker(bind=engine)
session = Session()

# Streamlit app config
st.set_page_config(page_title="Zn–Br Tracker", layout="wide")
st.title("🧪 Add New Zn–Br Cell")

# Form layout
with st.form("add_cell_form"):
    # You can remove st.columns(2) to make it single-column
    col1, col2 = st.columns(2)

    cell_id = col1.text_input("Cell ID", placeholder="e.g. ZnBr_001")
    felt_type = col1.text_input("Carbon Felt Type")
    sealing_type = col2.text_input("Sealing Method (e.g. O-ring)")
    notes = st.text_area("Notes or Observations")
    photo = st.file_uploader("Upload Cell Start Photo", type=["jpg", "jpeg", "png"])

    submitted = st.form_submit_button("Save Cell")

    if submitted:
        if not cell_id:
            st.error("Cell ID is required.")
        else:
            folder = f"media/{cell_id}"
            os.makedirs(folder, exist_ok=True)

            photo_path = ""
            if photo:
                photo_path = os.path.join(folder, photo.name)
                with open(photo_path, "wb") as f:
                    f.write(photo.read())

            # Add new record
            new_cell = Cell(
                cell_id=cell_id,
                created_at=datetime.now(),
                felt_type=felt_type,
                sealing_type=sealing_type,
                notes=notes,
                start_photo=photo_path
            )
            session.add(new_cell)
            session.commit()

            st.success(f"✅ Cell '{cell_id}' added successfully!")


st.header("📈 Log Cycle Test Data")

# Get all existing cells
cell_options = session.query(Cell).all()
cell_map = {cell.cell_id: cell.id for cell in cell_options}

selected_cell = st.selectbox("Select Cell ID", list(cell_map.keys()))

with st.form("log_cycle"):
    cycle_no = st.number_input("Cycle Number", min_value=1, step=1)
    current_density = st.text_input("Current Density (mA/cm²)")
    charge_V = st.text_input("Charge Voltage (V)")
    discharge_V = st.text_input("Discharge Voltage (V)")
    capacity_mAh = st.text_input("Capacity (mAh)")
    pH = st.text_input("pH")
    observation = st.text_area("Observations (leakage, smell, color, etc.)")

    csv_file = st.file_uploader("Upload Test CSV", type=["csv"])
    cycle_photo = st.file_uploader("Upload Cycle Photo", type=["jpg", "jpeg", "png"])

    submitted2 = st.form_submit_button("Save Cycle")

    if submitted2:
        ce = ""
        delta_v = ""
        csv_path = ""
        photo_path = ""

        if charge_V and discharge_V:
            delta_v = float(charge_V) - float(discharge_V)

        if csv_file:
            csv_folder = f"media/{selected_cell}/"
            os.makedirs(csv_folder, exist_ok=True)
            csv_path = os.path.join(csv_folder, csv_file.name)
            with open(csv_path, "wb") as f:
                f.write(csv_file.read())
            # (Optional) Auto-calculate CE% from CSV

        if cycle_photo:
            photo_folder = f"media/{selected_cell}/"
            photo_path = os.path.join(photo_folder, cycle_photo.name)
            with open(photo_path, "wb") as f:
                f.write(cycle_photo.read())

        # Insert into DB
        from models.base import Cycle

        new_cycle = Cycle(
            cell_id=cell_map[selected_cell],
            cycle_no=cycle_no,
            current_density=current_density,
            charge_V=charge_V,
            discharge_V=discharge_V,
            capacity_mAh=capacity_mAh,
            pH=pH,
            ce_pct=ce,
            delta_V=delta_v,
            csv_path=csv_path,
            observation=observation,
            photo_path=photo_path
        )
        session.add(new_cycle)
        session.commit()
        st.success("✅ Cycle data saved!")


st.header("📄 Export Report")
report_cell = st.selectbox("Select Cell to Export", list(cell_map.keys()), key="report_cell")

from models.base import Cell, Cycle

selected_id = cell_map[report_cell]
cell_data = session.query(Cell).get(selected_id)
cycle_data = session.query(Cycle).filter(Cycle.cell_id == selected_id).all()

col_pdf, col_excel = st.columns(2)

with col_pdf:
    if st.button("Generate PDF Report"):
        pdf_path = build_pdf(report_cell, cell_data, cycle_data)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f.read(), file_name=f"{report_cell}_report.pdf")

with col_excel:
    if st.button("Generate Excel Report"):
        excel_path = build_excel(report_cell, cell_data, cycle_data)
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                st.download_button("📥 Download Excel", f.read(), file_name=f"{report_cell}_report.xlsx")
        else:
            st.error("Failed to create Excel report.")



