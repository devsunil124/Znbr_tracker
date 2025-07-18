# pages/02_Select_Cell.py  ───────────────────────────────────────
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from models.base import engine, Cell
from sqlalchemy import func             
from models.base import engine, Cell, Cycle


st.header("🔍 Select a Cell")

# 1. status filter + search box ----------------------------------
status_choice = st.radio("Show", ["Running", "Stopped", "All"], horizontal=True)
search_text   = st.text_input("Filter by ID or channel contains…", "")

with Session(engine) as ses:
    q = ses.query(Cell).order_by(Cell.cell_id)
    if status_choice != "All":
        q = q.filter(Cell.status == status_choice.lower())
    cells = q.all()

    # get cycle counts with a single query
    counts = dict(
        ses.query(Cycle.cell_id, func.count())
        .filter(Cycle.cell_id.in_([c.id for c in cells]))
        .group_by(Cycle.cell_id)
        .all()
    )

rows = [
    {
        "Cell ID": c.cell_id,
        "Channel": c.channel,
        "Status": c.status,
        "Chem": c.chemistry,
        "Cycles": counts.get(c.id, 0),   # no lazy load
    }
    for c in cells
    if search_text.lower() in c.cell_id.lower() or search_text in str(c.channel)
]

df = pd.DataFrame(rows)

st.dataframe(df, hide_index=True, use_container_width=True)

# 2. choose a row -------------------------------------------------
cell_ids = df["Cell ID"].tolist()
if cell_ids:
    picked = st.selectbox("Select cell ID ↓", cell_ids)
    picked_cell = next(c for c in cells if c.cell_id == picked)

    col_view, col_log = st.columns(2)
    # open in Cell Viewer
    if col_view.button("📂 Open history"):
        st.session_state["log_cell_id"] = picked_cell.id
        st.switch_page("pages/03_View_Cells.py")

    # only show Log button for running cells
    if picked_cell.status == "running":
        if col_log.button("✍️ Log new cycle"):
            st.session_state["log_cell_id"] = picked_cell.id
            st.switch_page("pages/02_Log_Cycle.py")
else:
    st.info("No cells match the current filter.")
