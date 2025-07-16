import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.orm import Session

from models.base import engine, Cell, Cycle

# ──────────────────────────────────────────────────────────────────
MEDIA_ROOT = Path("media")
MEDIA_ROOT.mkdir(exist_ok=True, parents=True)

st.header("🔄 Log New Cycle Data")

# 1️⃣ Pick a running cell ──────────────────────────────────────────
with Session(engine) as ses:
    running = (
        ses.query(Cell).filter(Cell.status == "running").order_by(Cell.cell_id).all()
    )

if not running:
    st.info("No cells are currently running. Start one on the Dashboard first.")
    st.stop()

cell_opts = {f"{c.cell_id} (Ch {c.channel})": c.id for c in running}
cell_label = st.selectbox("Select running cell ▼", list(cell_opts.keys()))
cell_db_id = cell_opts[cell_label]

# 2️⃣ Upload file (CSV or XLSX) ────────────────────────────────────
uploaded = st.file_uploader("Upload cycle file (.csv / .xlsx)", ["csv", "xlsx"])

# helper ───────────────────────────────────────────────────────────
def load_cycle_file(file) -> pd.DataFrame:
    """Return a tidy DataFrame, numeric columns coerced to float."""
    raw_bytes = BytesIO(file.getbuffer())

    if file.name.lower().endswith(".csv"):
        df = pd.read_csv(raw_bytes)
    else:  # xlsx
        tmp = pd.read_excel(raw_bytes, header=None)

        # find the header row where first cell == 'Time'
        hdr_idx = tmp.index[tmp[0] == "Time"].tolist()
        if not hdr_idx:
            st.error("Could not locate a 'Time' header in the XLSX file.")
            st.stop()
        hdr = hdr_idx[0]

        # read again with that header row, drop the next row (units)
        df = pd.read_excel(raw_bytes, header=hdr)
        df = df.iloc[1:]  # remove units row beneath header

    # strip spaces/newlines from column names
    df.columns = df.columns.str.strip().str.replace("\n", "_", regex=False)

    # coerce numerics
    for col in df.columns:
        if col.lower() != "time":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────
if uploaded:
    df = load_cycle_file(uploaded)
    if df.empty:
        st.warning("The file has headers but no data rows.")
        st.stop()

    st.subheader("Preview")
    st.dataframe(df.head(), use_container_width=True)

    # 3️⃣ Column aliases (edit to match your headers) ──────────────
    col_map = {
        "charge_ah": ["Charge_Ah", "Charge(Ah)"],
        "discharge_ah": ["Discharge_Ah", "Discharge(Ah)"],
        "charge_v": ["Charge_V", "Charge(V)"],
        "discharge_v": ["Discharge_V", "Discharge(V)"],
        "current_density": ["Current_mAcm2", "Current(mA/cm2)"],
        "time_s": ["Time_s", "Time(s)", "Time"],
    }

    def find(col_list):
        for name in col_list:
            if name in df.columns:
                return name
        st.error(f"None of the columns {col_list} found in file.")
        st.stop()

    charge_ah_col = find(col_map["charge_ah"])
    discharge_ah_col = find(col_map["discharge_ah"])
    charge_v_col = find(col_map["charge_v"])
    discharge_v_col = find(col_map["discharge_v"])
    j_col = find(col_map["current_density"])
    t_col = find(col_map["time_s"])

    # 4️⃣ Metrics ─────────────────────────────────────────────────
    Qc = df[charge_ah_col].iloc[-1]
    Qd = df[discharge_ah_col].iloc[-1]
    ce_pct = round((Qd / Qc) * 100, 2)

    Vc = df[charge_v_col].max()
    Vd = df[discharge_v_col].min()
    delta_v = round(Vc - Vd, 3)

    st.markdown(
        f"""
        **Coulombic Efficiency:** {ce_pct} %  
        **ΔV (charge − discharge):** {delta_v} V
        """
    )

    # 5️⃣ Plot ────────────────────────────────────────────────────
    fig = px.line(
        df, x=t_col, y=[charge_v_col, discharge_v_col], title="Voltage profile"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 6️⃣ Extra inputs ────────────────────────────────────────────
    pH = st.number_input("pH (at end of cycle)", value=7.0, step=0.1)
    obs = st.text_area("Observations / issues", placeholder="Leaks, colour change…")

    # 7️⃣ Save ────────────────────────────────────────────────────
    if st.button("💾 Save cycle to DB"):
        # copy file into media/
        suffix = Path(uploaded.name).suffix
        dest = MEDIA_ROOT / f"{uuid.uuid4()}{suffix}"
        dest.write_bytes(uploaded.getbuffer())

        with Session(engine) as ses:
            next_no = ses.query(Cycle).filter(Cycle.cell_id == cell_db_id).count() + 1
            ses.add(
                Cycle(
                    cell_id=cell_db_id,
                    cycle_no=next_no,
                    current_density=df[j_col].iloc[0],
                    charge_V=Vc,
                    discharge_V=Vd,
                    capacity_mAh=Qd * 1000,
                    pH=pH,
                    csv_path=str(dest),
                    ce_pct=ce_pct,
                    delta_V=delta_v,
                    observation=obs,
                )
            )
            ses.commit()

        st.success(f"Cycle {next_no} saved ✔")
