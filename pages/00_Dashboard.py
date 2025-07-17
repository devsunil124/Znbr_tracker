import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from models.base import engine, Cell

st.header("📊 Cycler Dashboard (8 channels)")

# ── 1. fetch running cells ────────────────────────────────────────
with Session(engine) as ses:
    running = (
        ses.query(Cell)
        .filter(Cell.status == "running")
        .order_by(Cell.channel)
        .all()
    )

df_running = pd.DataFrame(
    [
        {
            "Channel": c.channel,
            "Cell ID": c.cell_id,
            "Chemistry": c.chemistry,
            "Asm Date": c.assembly_date.date() if c.assembly_date else None,
            "Rated Cap (mAh)": c.rated_capacity,
        }
        for c in running
    ]
)

# ensure the DataFrame has *at least* the merge key
if df_running.empty:
    df_running = pd.DataFrame(columns=["Channel"])

# ── 2. merge with full channel list ───────────────────────────────
dash = (
    pd.DataFrame({"Channel": range(1, 9)})
    .merge(df_running, how="left", on="Channel")
)

# add any missing detail columns and fill with "—"
detail_cols = ["Cell ID", "Chemistry", "Asm Date", "Rated Cap (mAh)"]
for col in detail_cols:
    if col not in dash.columns:
        dash[col] = "—"

dash.fillna("—", inplace=True)

st.dataframe(dash, hide_index=True, use_container_width=True)

# ── 3. action buttons per channel ─────────────────────────────────
for ch in range(1, 9):
    col_label, col_log, col_stop = st.columns([3, 1, 1])
    col_label.write(f"**Channel {ch}**")

    row = dash.loc[dash["Channel"] == ch]
    is_empty = row["Cell ID"].iloc[0] == "—"

    if is_empty:
        if col_log.button("Start", key=f"start_{ch}"):
            st.session_state["new_channel"] = ch
            st.switch_page("pages/01_Add_Cell.py")
    else:
       # look up the running cell once
        with Session(engine) as ses:
            cell = (
                ses.query(Cell)
                .filter(Cell.channel == ch, Cell.status == "running")
                .first()
            )

        # LOG button → pre‑select this cell on Log‑Cycle page
        if col_log.button("Log", key=f"log_{ch}"):
            st.session_state["log_cell_id"] = cell.id
            st.switch_page("pages/02_Log_Cycle.py")

        # STOP button
        if col_stop.button("Stop", key=f"stop_{ch}"):
            with Session(engine) as ses:
                cell.status = "stopped"
                ses.commit()
            st.rerun()