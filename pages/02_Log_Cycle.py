# pages/02_Log_Cycle.py  ───────────────────────────────────────────
from pathlib import Path
import uuid
from datetime import datetime
import streamlit as st
from sqlalchemy.orm import Session

from models.base import engine, Cell, Cycle

# storage for any future attachments
MEDIA_ROOT = Path("media")
MEDIA_ROOT.mkdir(exist_ok=True, parents=True)

st.header("✍️ Log Cycle Data (manual)")

# ── 1. pick a running cell ───────────────────────────────────────
with Session(engine) as ses:
    running = (
        ses.query(Cell).filter(Cell.status == "running").order_by(Cell.cell_id).all()
    )

if not running:
    st.info("No cells are currently running. Start one on the Dashboard first.")
    st.stop()

cell_opts = {f"{c.cell_id} (Ch {c.channel})": c.id for c in running}
prefill_id = st.session_state.pop("log_cell_id", None)
options = list(cell_opts.keys())
if prefill_id and prefill_id in cell_opts.values():
    default_index = options.index(next(k for k, v in cell_opts.items() if v == prefill_id))
else:
    default_index = 0

cell_label = st.selectbox("Select running cell ▼", options, index=default_index)
cell_db_id = cell_opts[cell_label]

# ⭐ NEW: show next cycle number right away
with Session(engine) as ses:
    current_cnt = ses.query(Cycle).filter(Cycle.cell_id == cell_db_id).count()
next_cycle_no = current_cnt + 1
st.markdown(f"**Next cycle number:** {next_cycle_no}")
st.write("")  # tiny spacer


# ── 2. manual‑entry widgets (no form) ────────────────────────────
st.subheader("Enter cycle data")

if st.session_state.get("reset_cycle_form", False):
    st.session_state.update(
        {
            "charge_ah": 0.0,
            "discharge_ah": 0.0,
            "charge_V": 0.0,
            "discharge_V": 0.0,
            "j": 0.0,
            "obs": "",
        }
    )
    st.session_state.pop("att", None) 
    st.session_state["reset_cycle_form"] = False  # clear flag

c1, c2, c3 = st.columns(3)
charge_ah      = c1.number_input("Charge capacity (Ah)*",     min_value=0.0, step=0.0001, format="%.4f", key="charge_ah")
discharge_ah   = c1.number_input("Discharge capacity (Ah)*",  min_value=0.0, step=0.0001, format="%.4f", key="discharge_ah")

charge_V       = c2.number_input("Max charge voltage (V)*",   min_value=0.0, step=0.0001, format="%.4f", key="charge_V")
discharge_V    = c2.number_input("Min discharge voltage (V)*",min_value=0.0, step=0.0001, format="%.4f", key="discharge_V")

current_density = c3.number_input("Current density (mA/cm²)*", min_value=0.0, step=0.0001, format="%.4f", key="j")
observation    = st.text_area("Observations / issues", placeholder="Leaks, colour …", key="obs")
attachment     = st.file_uploader("Attach graph/photo (optional)", type=["png", "jpg", "csv", "xlsx"], key="att")

# only enable button when required fields > 0
required_ok = all(v > 0 for v in (charge_ah, discharge_ah, charge_V, discharge_V, current_density))
save_clicked = st.button(
    "💾 Save cycle",
    disabled=not required_ok,
    key="save_cycle_clicked"
)

# ── 3. save if user clicked button ───────────────────────────────
if save_clicked:
    ce_pct  = (discharge_ah / charge_ah) * 100
    delta_v = (charge_V - discharge_V)

    attach_path = None
    if attachment:
        suffix = Path(attachment.name).suffix
        attach_path = MEDIA_ROOT / f"{uuid.uuid4()}{suffix}"
        attach_path.write_bytes(attachment.getbuffer())

    with Session(engine) as ses:
        ses.add(                          # ← use next_cycle_no directly
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
        ses.commit()
        # ── DEBUG: did we really insert a row? ───────────────────
        with Session(engine) as dbg:
            total = dbg.query(Cycle).filter(Cycle.cell_id == cell_db_id).count()
            latest = (
                dbg.query(Cycle.delta_V, Cycle.ce_pct)
                .filter(Cycle.cell_id == cell_db_id)
                .order_by(Cycle.cycle_no.desc())
                .first()
            )
        st.info(f"DEBUG → cycles now in DB for this cell: {total}  "
                f"(last ΔV={latest.delta_V if latest else '—'})")
    st.success(
        f"Cycle {next_cycle_no} saved ✔ "
        f"CE % = {ce_pct} ΔV = {delta_v:.4f} V"
    )
    
    # Jump back to dashboard so counts refresh with baloons
    st.balloons()
    st.switch_page("app.py")
    
