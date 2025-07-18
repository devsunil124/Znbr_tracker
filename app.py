import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.base import engine, Cell, Cycle, Base   # Base for safety

# auto‑create tables if missing (safe no‑op otherwise)
Base.metadata.create_all(engine)

st.set_page_config(
    page_title="Zn‑Br Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Cycler Dashboard (8 channels)")
# in app.py sidebar
st.sidebar.page_link("pages/02_Select_Cell.py", label="🔍 Select Cell")


# ── fetch running cells & cycle stats ────────────────────────────
with Session(engine) as ses:
    running_cells = (
        ses.query(Cell).filter(Cell.status == "running").order_by(Cell.channel).all()
    )

    stats = {}
    for cell in running_cells:
        count, last_ts = ses.query(
            func.count(Cycle.id), func.max(Cycle.created_at)
        ).filter(Cycle.cell_id == cell.id).one()
        stats[cell.id] = {"count": count, "last": last_ts}

# ── build table data ─────────────────────────────────────────────
rows = []
for ch in range(1, 9):
    cell = next((c for c in running_cells if c.channel == ch), None)
    if cell:
        s = stats[cell.id]
        rows.append(
            {
                "Channel": ch,
                "Cell ID": cell.cell_id,
                "Cycles": s["count"],
                "Last update": s["last"].strftime("%Y‑%m‑%d %H:%M") if s["last"] else "—",
            }
        )
    else:
        rows.append(
            {"Channel": ch, "Cell ID": "—", "Cycles": "—", "Last update": "—"}
        )

df_dash = pd.DataFrame(rows)
st.dataframe(df_dash, hide_index=True, use_container_width=True)

# ── action buttons per channel ───────────────────────────────────
for ch in range(1, 9):
    row = df_dash.loc[df_dash["Channel"] == ch].iloc[0]
    col_lab, col_log, col_stop = st.columns([3, 1, 1])
    col_lab.write(f"**Channel {ch}** – {row['Cell ID']}")

    if row["Cell ID"] == "—":
        if col_log.button("Start", key=f"start_{ch}"):
            st.session_state["new_channel"] = ch
            st.switch_page("pages/01_Add_Cell.py")
    else:
        # Log cycle
        if col_log.button("Log", key=f"log_{ch}"):
            with Session(engine) as ses:
                cell = ses.query(Cell).filter(Cell.channel == ch, Cell.status == "running").first()
            st.session_state["log_cell_id"] = cell.id
            st.switch_page("pages/02_Log_Cycle.py")

        # Stop cell
        if col_stop.button("Stop", key=f"stop_{ch}"):
            with Session(engine) as ses:
                cell = (
                    ses.query(Cell)
                    .filter(Cell.channel == ch, Cell.status == "running")
                    .first()
                )
                if cell:
                    cell.status = "stopped"
                    ses.commit()
            st.rerun()
