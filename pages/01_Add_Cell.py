import streamlit as st
from datetime import datetime

# Imports updated
from database import get_db
from models.base import Cell

prefill = st.session_state.get("new_channel")
st.header("➕ Register New Cell")
if prefill:
    st.subheader(f"Assigning to Channel {prefill}")

with st.form("add_cell"):
    c1, c2 = st.columns(2)
    cell_id = c1.text_input("Cell ID (e.g. S-01)*")
    chemistry = c1.text_input("Chemistry*", value="Zn–Br")
    rated_capacity = c1.number_input("Rated Capacity (mAh)*", min_value=0.0)
    configuration = c1.text_input("Configuration", placeholder="e.g. 2×2 cm")
    asm_date = c2.date_input("Assembly Date", value=datetime.today())
    znbr_molarity = c2.number_input("ZnBr molarity (eg: 1M)*", min_value=0.0)
    teacl_molarity = c2.number_input("TEACl molarity (eg: 1M)*", min_value=0.0)
    notes = st.text_area("Notes", height=80)
    channel_pick = c2.selectbox("Cycler Channel", range(1, 9),
                                index=(prefill - 1) if prefill else 0)
    submitted = st.form_submit_button("Save & Start")

if submitted:
    # --- VALIDATION LOGIC RESTORED HERE ---
    with get_db() as db:
        # 🔍 1. Check for duplicate Cell ID
        exists = db.query(Cell).filter(Cell.cell_id == cell_id).first()
        if exists:
            st.error(
                f"Cell ID ‘{cell_id}’ already exists. "
                "Pick another ID or stop the existing cell first."
            )
            st.stop()

        # 🔍 2. Check if channel is already running
        busy = (
            db.query(Cell)
            .filter(Cell.channel == channel_pick, Cell.status == "running")
            .first()
        )
        if busy:
            st.error(
                f"Channel {channel_pick} already has running cell ‘{busy.cell_id}’. "
                "Stop it first or choose a different channel."
            )
            st.stop()

        # 3. All clear → create the cell
        db.add(
            Cell(
                cell_id=cell_id,
                chemistry=chemistry,
                rated_capacity=rated_capacity,
                configuration=configuration,
                znbr_molarity=znbr_molarity,
                teacl_molarity=teacl_molarity,
                assembly_date=datetime.combine(asm_date, datetime.min.time()),
                notes=notes,
                channel=channel_pick,
                status="running",
            )
        )
        db.commit()
    # --- END OF VALIDATION ---

    st.success(f"Cell {cell_id} assigned to Channel {channel_pick} ✅")
    st.session_state.pop("new_channel", None)
    st.switch_page("app.py")
