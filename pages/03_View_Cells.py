# pages/03_View_Cells.py  ─────────────────────────────────────────

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import Session
from models.base import engine, Cell, Cycle

st.header("📂 Cell Viewer")

# ── 1. pick a cell ───────────────────────────────────────────────
with Session(engine) as ses:
    cells = ses.query(Cell).order_by(Cell.cell_id).all()

if not cells:
    st.info("No cells in the database yet. Add one from the Dashboard.")
    st.stop()

cell_map = {f"{c.cell_id} (Ch {c.channel or '—'})": c.id for c in cells}
chosen_label = st.selectbox("Select a cell ▼", list(cell_map.keys()))
cell_id = cell_map[chosen_label]

# ── 2. show cell metadata ────────────────────────────────────────
with Session(engine) as ses:
    cell = ses.query(Cell).get(cell_id)
    cycles = (
        ses.query(Cycle)
        .filter(Cycle.cell_id == cell_id)
        .order_by(Cycle.cycle_no)
        .all()
    )

st.subheader("📝 Cell details")
meta_cols = st.columns(4)
meta_cols[0].write(f"**Cell ID:** {cell.cell_id}")
meta_cols[1].write(f"**Chemistry:** {cell.chemistry}")
meta_cols[2].write(f"**ZnBr M:** {cell.znbr_molarity}")
meta_cols[3].write(f"**TEACl M:** {cell.teacl_molarity}")
meta_cols[0].write(f"**Rated Cap.:** {cell.rated_capacity} mAh")
meta_cols[1].write(f"**Config:** {cell.configuration}")
meta_cols[2].write(f"**Assembly Date:** {cell.assembly_date.date()}")
meta_cols[3].write(f"**Status:** {cell.status.capitalize()}")

st.markdown(f"**Notes**  \n{cell.notes or '—'}")

# ── 3. cycles table ──────────────────────────────────────────────
if not cycles:
    st.warning("No cycles logged for this cell yet.")
    st.stop()

df = pd.DataFrame(
    [
        {
            "Cycle #": c.cycle_no,
            "Current (mA/cm²)": c.current_density,
            "Charge V": c.charge_V,
            "Discharge V": c.discharge_V,
            "ΔV": c.delta_V,
            "CE %": c.ce_pct,
            "Cap. (mAh)": c.capacity_mAh,
            "Obs": (c.observation[:30] + "…") if c.observation else "",
        }
        for c in cycles
    ]
)

st.subheader("📊 Cycle table")
st.dataframe(df, use_container_width=True, hide_index=True)

# ── 4. quick plot ────────────────────────────────────────────────
st.subheader("🔎 Plot a metric")

metric = st.selectbox(
    "Y‑axis metric",
    ["Charge V", "Discharge V", "ΔV", "CE %", "Cap. (mAh)"],
    index=3,
)
fig = px.line(df, x="Cycle #", y=metric, markers=True)
st.plotly_chart(fig, use_container_width=True)
