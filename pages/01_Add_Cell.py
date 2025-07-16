import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from models.base import engine, Cell

prefill = st.session_state.get("new_channel")
st.header("➕ Register New Cell")
if prefill:
    st.subheader(f"Assigning to Channel {prefill}")

with st.form("add_cell"):
    c1, c2 = st.columns(2)
    cell_id        = c1.text_input("Cell ID (e.g. S‑01)*")
    chemistry      = c1.text_input("Chemistry*", value="Zn–Br")
    rated_capacity = c1.number_input("Rated Capacity (mAh)*", min_value=0.0)
    configuration  = c1.text_input("Configuration", placeholder="e.g. 2×2 cm")
    asm_date       = c2.date_input("Assembly Date", value=datetime.today())
    notes          = st.text_area("Notes", height=80)
    channel_pick   = c2.selectbox("Cycler Channel", range(1, 9),
                                  index=(prefill - 1) if prefill else 0)
    submitted = st.form_submit_button("Save & Start")

if submitted:
    with Session(engine) as ses:
        ses.add(
            Cell(
                cell_id=cell_id,
                chemistry=chemistry,
                rated_capacity=rated_capacity,
                configuration=configuration,
                assembly_date=datetime.combine(asm_date, datetime.min.time()),
                notes=notes,
                channel=channel_pick,
                status="running",
            )
        )
        ses.commit()
    if "new_channel" in st.session_state:
        del st.session_state["new_channel"]
    st.success(f"Cell {cell_id} → Channel {channel_pick} ✅")
    st.switch_page("pages/00_Dashboard.py")
