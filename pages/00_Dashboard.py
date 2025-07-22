import streamlit as st
import pandas as pd

# --- 1. IMPORTS UPDATED ---
from database import get_db
from models.base import Cell
# --------------------------

st.header("📊 Cycler Dashboard (8 channels)")

# --- 2. SESSION HANDLING UPDATED & REFACTORED ---
# Fetch all necessary data from the database ONCE.
with get_db() as db:
    running_cells = (
        db.query(Cell)
        .filter(Cell.status == "running")
        .all()
    )
# Create a dictionary for quick lookups: {channel_number: cell_object}
running_cells_map = {cell.channel: cell for cell in running_cells}
# ------------------------------------------------

# Create a list of dictionaries for the main display DataFrame
running_data_list = [
    {
        "Channel": c.channel,
        "Cell ID": c.cell_id,
        "Chemistry": c.chemistry,
        "Asm Date": c.assembly_date.date() if c.assembly_date else None,
        "Rated Cap (mAh)": c.rated_capacity,
    }
    for c in running_cells
]

df_running = pd.DataFrame(running_data_list)

# Ensure the DataFrame has at least the merge key
if df_running.empty:
    df_running = pd.DataFrame(columns=["Channel"])

# Merge with a full channel list to show all 8 channels
dash = (
    pd.DataFrame({"Channel": range(1, 9)})
    .merge(df_running, how="left", on="Channel")
)

# Add any missing detail columns and fill with "—"
detail_cols = ["Cell ID", "Chemistry", "Asm Date", "Rated Cap (mAh)"]
for col in detail_cols:
    if col not in dash.columns:
        dash[col] = "—"
dash.fillna("—", inplace=True)

st.dataframe(dash, hide_index=True, use_container_width=True)

# ── 3. Action buttons per channel ─────────────────────────────────
for ch in range(1, 9):
    col_label, col_action1, col_action2 = st.columns([3, 1, 1])
    col_label.write(f"**Channel {ch}**")

    # Check if the channel is empty by looking in our map
    if ch not in running_cells_map:
        if col_action1.button("Start", key=f"start_{ch}"):
            st.session_state["new_channel"] = ch
            st.switch_page("pages/01_Add_Cell.py")
    else:
        # Get the cell object from our map (no new DB query needed)
        cell = running_cells_map[ch]

        # LOG button
        if col_action1.button("Log", key=f"log_{ch}"):
            st.session_state["log_cell_id"] = cell.id
            st.switch_page("pages/02_Log_Cycle.py")

        # STOP button
        if col_action2.button("Stop", key=f"stop_{ch}"):
            # This action MODIFIES the database, so it needs a new session
            with get_db() as db:
                cell_to_stop = db.query(Cell).filter(Cell.id == cell.id).first()
                if cell_to_stop:
                    cell_to_stop.status = "stopped"
                    db.commit()
            st.rerun()