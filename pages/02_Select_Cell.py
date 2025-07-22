import streamlit as st
import pandas as pd
from sqlalchemy import func

# --- 1. IMPORTS UPDATED ---
from database import get_db
from models.base import Cell, Cycle
# --------------------------

st.header("🔍 Select a Cell")

# 1. status filter + search box ----------------------------------
status_choice = st.radio("Show", ["Running", "Stopped", "All"], horizontal=True)
search_text = st.text_input("Filter by ID or channel contains…", "")

# --- 2. SESSION HANDLING UPDATED ---
with get_db() as db:
    q = db.query(Cell).order_by(Cell.cell_id)
    if status_choice != "All":
        q = q.filter(Cell.status == status_choice.lower())
    cells = q.all()

    # Get cycle counts with a single efficient query
    counts = {}
    if cells: # Only run this query if there are cells
        counts = dict(
            db.query(Cycle.cell_id, func.count())
            .filter(Cycle.cell_id.in_([c.id for c in cells]))
            .group_by(Cycle.cell_id)
            .all()
        )
# -----------------------------------

# Filter the results in Python based on the search text
rows = [
    {
        "Cell ID": c.cell_id,
        "Channel": c.channel,
        "Status": c.status,
        "Chem": c.chemistry,
        "Cycles": counts.get(c.id, 0),
    }
    for c in cells
    if not search_text or (search_text.lower() in c.cell_id.lower() or search_text in str(c.channel))
]

df = pd.DataFrame(rows)
st.dataframe(df, hide_index=True, use_container_width=True)

# 2. choose a row -------------------------------------------------
cell_ids = df["Cell ID"].tolist()
if cell_ids:
    picked = st.selectbox("Select cell ID ↓", cell_ids)
    # Find the full cell object from our initial list (no new DB query)
    picked_cell = next((c for c in cells if c.cell_id == picked), None)

    if picked_cell:
        col_view, col_log = st.columns(2)
        # Open in Cell Viewer
        if col_view.button("📂 Open history"):
            st.session_state["log_cell_id"] = picked_cell.id
            st.switch_page("pages/03_View_Cells.py")

        # Only show Log button for running cells
        if picked_cell.status == "running":
            if col_log.button("✍️ Log new cycle"):
                st.session_state["log_cell_id"] = picked_cell.id
                st.switch_page("pages/02_Log_Cycle.py")
else:
    st.info("No cells match the current filter.")