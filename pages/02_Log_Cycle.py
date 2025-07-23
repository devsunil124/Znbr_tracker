# pages/02_Log_Cycle.py
from pathlib import Path
import uuid
from datetime import datetime
import streamlit as st
from sqlalchemy import func # <-- Import 'func'

# Imports updated
from database import get_db
from models.base import Cell, Cycle

# storage for any future attachments
MEDIA_ROOT = Path("media")
MEDIA_ROOT.mkdir(exist_ok=True, parents=True)

st.header("✍️ Log Cycle Data (manual)")

# Fetch all running cells in one go
with get_db() as db:
    running_cells = (
        db.query(Cell).filter(Cell.status == "running").order_by(Cell.cell_id).all()
    )

if not running_cells:
    st.info("No cells are currently running. Start one on the Dashboard first.")
    st.stop()

# Prepare options for the selectbox
cell_opts = {f"{c.cell_id} (Ch {c.channel})": c.id for c in running_cells}
options = list(cell_opts.keys())

# Determine the default selection based on session state
prefill_id = st.session_state.get("log_cell_id") # Use .get() instead of .pop()
default_index = 0
if prefill_id and prefill_id in cell_opts.values():
    prefilled_key = next((k for k, v in cell_opts.items() if v == prefill_id), None)
    if prefilled_key:
        default_index = options.index(prefilled_key)

cell_label = st.selectbox("Select running cell ▼", options, index=default_index)
cell_db_id = cell_opts[cell_label]

# --- LOGIC CORRECTED HERE ---
# Find the highest existing cycle number and add 1. This is more robust.
with get_db() as db:
    last_cycle_no = db.query(func.max(Cycle.cycle_no)).filter(Cycle.cell_id == cell_db_id).scalar()
next_cycle_no = (last_cycle_no or 0) + 1
# --- END OF CORRECTION ---

st.markdown(f"**Next cycle number:** {next_cycle_no}")
st.write("")  # tiny spacer

# --- Input widgets ---
st.subheader("Enter cycle data")
c1, c2, c3 = st.columns(3)
charge_ah = c1.number_input("Charge capacity (Ah)*", min_value=0.0, step=0.0001, format="%.4f", key="charge_ah")
discharge_ah = c1.number_input("Discharge capacity (Ah)*", min_value=0.0, step=0.0001, format="%.4f", key="discharge_ah")
charge_V = c2.number_input("Max charge voltage (V)*", min_value=0.0, step=0.0001, format="%.4f", key="charge_V")
discharge_V = c2.number_input("Min discharge voltage (V)*", min_value=0.0, step=0.0001, format="%.4f", key="discharge_V")
current_density = c3.number_input("Current density (mA/cm²)*", min_value=0.0, step=0.0001, format="%.4f", key="j")
observation = st.text_area("Observations / issues", placeholder="Leaks, colour …", key="obs")
attachment = st.file_uploader("Attach graph/photo (optional)", type=["png", "jpg", "csv", "xlsx"], key="att")

required_ok = all(v > 0 for v in (charge_ah, discharge_ah, charge_V, discharge_V, current_density))
save_clicked = st.button("💾 Save cycle", disabled=not required_ok, key="save_cycle_clicked")

if save_clicked:
    ce_pct = (discharge_ah / charge_ah) * 100 if charge_ah > 0 else 0
    delta_v = charge_V - discharge_V

    attach_path = None
    if attachment:
        suffix = Path(attachment.name).suffix
        attach_path = MEDIA_ROOT / f"{uuid.uuid4()}{suffix}"
        attach_path.write_bytes(attachment.getbuffer())

    with get_db() as db:
        db.add(
            Cycle(
                cell_id=cell_db_id,
                cycle_no=next_cycle_no,
                current_density=current_density,
                charge_V=charge_V,
                discharge_V=discharge_V,
                capacity_mAh=discharge_ah * 1000,
                csv_path=str(attach_path) if attach_path else None,
                ce_pct=ce_pct,
                delta_V=delta_v,
                observation=observation,
                created_at=datetime.utcnow(),
            )
        )
        db.commit()

    st.success(
        f"Cycle {next_cycle_no} saved ✔ "
        f"CE % = {ce_pct:.2f} | ΔV = {delta_v:.4f} V"
    )
    st.balloons()
    st.session_state.pop("log_cell_id", None) # Pop the key after using it
    st.switch_page("app.py")
