import streamlit as st
import pandas as pd
from sqlalchemy import func
from zoneinfo import ZoneInfo # For timezone conversion

# Imports updated
from database import get_db
from models.base import Cell, Cycle

st.set_page_config(layout="wide")
st.header("📊 Cycler Dashboard")

# --- 1. ADVANCED QUERY TO GET ALL DATA AT ONCE ---
with get_db() as db:
    # Subquery to get cycle count and last update time for each cell
    cycle_agg = (
        db.query(
            Cycle.cell_id,
            func.count(Cycle.id).label("cycle_count"),
            func.max(Cycle.created_at).label("last_update")
        )
        .group_by(Cycle.cell_id)
        .subquery()
    )

    # Main query to join running cells with the aggregated cycle data
    results = (
        db.query(Cell, cycle_agg.c.cycle_count, cycle_agg.c.last_update)
        .outerjoin(cycle_agg, Cell.id == cycle_agg.c.cell_id)
        .filter(Cell.status == "running")
        .all()
    )

# --- 2. PROCESS RESULTS FOR DISPLAY ---
running_data_list = []
running_cells_map = {}
for cell, cycle_count, last_update in results:
    # Convert UTC time from DB to local time for display
    last_update_local = "—"
    if last_update:
        utc_time = last_update.replace(tzinfo=ZoneInfo("UTC"))
        local_time = utc_time.astimezone(ZoneInfo("Asia/Kolkata"))
        last_update_local = local_time.strftime("%d-%b-%Y %H:%M")

    running_data_list.append({
        "Channel": cell.channel,
        "Cell ID": cell.cell_id,
        "Cycles": cycle_count or 0,
        "Last Update": last_update_local,
        "Asm Date": cell.assembly_date.date() if cell.assembly_date else "—",
    })
    running_cells_map[cell.channel] = cell

df_running = pd.DataFrame(running_data_list)

# Ensure the DataFrame has at least the merge key
if df_running.empty:
    df_running = pd.DataFrame(columns=["Channel"])

# Merge with a full channel list to show all 8 channels
dash = (
    pd.DataFrame({"Channel": range(1, 9)})
    .merge(df_running, how="left", on="Channel")
)

# Define all columns to ensure they exist even if no cells are running
display_cols = ["Cell ID", "Cycles", "Last Update", "Asm Date"]
for col in display_cols:
    if col not in dash.columns:
        dash[col] = "—"
dash.fillna("—", inplace=True)

# Reorder columns for a better layout
final_cols = ["Channel", "Cell ID", "Cycles", "Last Update", "Asm Date"]
st.dataframe(dash[final_cols], hide_index=True, use_container_width=True)


# --- 3. ACTION BUTTONS (NO CHANGE IN LOGIC) ---
st.write("---")
for ch in range(1, 9):
    col_label, col_action1, col_action2 = st.columns([3, 1, 1])
    col_label.write(f"**Channel {ch}**")

    if ch not in running_cells_map:
        if col_action1.button("▶️ Start", key=f"start_{ch}"):
            st.session_state["new_channel"] = ch
            st.switch_page("pages/01_Add_Cell.py")
    else:
        cell = running_cells_map[ch]
        if col_action1.button("✍️ Log", key=f"log_{ch}"):
            st.session_state["log_cell_id"] = cell.id
            st.switch_page("pages/02_Log_Cycle.py")

        if col_action2.button("⏹️ Stop", key=f"stop_{ch}"):
            with get_db() as db:
                cell_to_stop = db.query(Cell).filter(Cell.id == cell.id).first()
                if cell_to_stop:
                    cell_to_stop.status = "stopped"
                    db.commit()
            st.rerun()
