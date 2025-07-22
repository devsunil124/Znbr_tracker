import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. IMPORTS UPDATED ---
from database import get_db
from models.base import Cell, Cycle
# --------------------------

st.header("📂 Cell Viewer")

# --- 2. HELPER FUNCTION UPDATED ---
# This function now uses the correct session handling
def update_cycles_in_db(orig: pd.DataFrame, edited: pd.DataFrame, cell_id: int) -> bool:
    """Save all changed cells for this cell_id; returns True if anything updated."""
    orig_filled = orig.fillna("")
    edited_filled = edited.fillna("")
    diff_mask = edited_filled.ne(orig_filled)

    if not diff_mask.any().any():
        return False

    col_map = {
        "Current (mA/cm²)": "current_density",
        "Charge V": "charge_V",
        "Discharge V": "discharge_V",
        "ΔV": "delta_V",
        "CE %": "ce_pct",
        "Cap. (mAh)": "capacity_mAh",
        "Obs": "observation",
    }

    with get_db() as db:
        for row_idx, row in diff_mask.iterrows():
            if not row.any():
                continue

            cycle_no = int(edited.loc[row_idx, "Cycle #"])
            cycle = (
                db.query(Cycle)
                .filter(Cycle.cell_id == cell_id, Cycle.cycle_no == cycle_no)
                .first()
            )
            if not cycle:
                continue

            # Apply every changed column in this row
            for col_name, changed in row.items():
                if changed and col_name in col_map:
                    new_val = edited.loc[row_idx, col_name]
                    # Handle pandas converting empty text to None
                    if col_map[col_name] == "observation" and pd.isna(new_val):
                        new_val = ""
                    setattr(cycle, col_map[col_name], new_val)
        db.commit()
    return True

# --- 3. DATA FETCHING UPDATED ---
# Get all cells for the dropdown selector
with get_db() as db:
    all_cells = db.query(Cell).order_by(Cell.cell_id).all()

if not all_cells:
    st.info("No cells in the database yet. Add one from the Dashboard.")
    st.stop()

# Prepare the selectbox options
cell_map = {f"{c.cell_id} (Ch {c.channel or '—'})": c.id for c in all_cells}
cell_keys = list(cell_map.keys())

# Determine the default selection
prefill_id = st.session_state.pop("log_cell_id", None)
default_idx = 0
if prefill_id and prefill_id in cell_map.values():
    prefilled_key = next((k for k, v in cell_map.items() if v == prefill_id), None)
    if prefilled_key:
        default_idx = cell_keys.index(prefilled_key)

chosen_label = st.selectbox("Select a cell ▼", cell_keys, index=default_idx)
cell_id = cell_map[chosen_label]

# --- 4. FETCH DETAILS FOR THE CHOSEN CELL ---
with get_db() as db:
    cell = db.query(Cell).get(cell_id)
    cycles = (
        db.query(Cycle)
        .filter(Cycle.cell_id == cell_id)
        .order_by(Cycle.cycle_no)
        .all()
    )

# --- Display logic (no changes needed here) ---
st.subheader("📝 Cell details")
meta_cols = st.columns(4)
meta_cols[0].write(f"**Cell ID:** {cell.cell_id}")
meta_cols[1].write(f"**Chemistry:** {cell.chemistry}")
meta_cols[2].write(f"**ZnBr M:** {cell.znbr_molarity}")
meta_cols[3].write(f"**TEACl M:** {cell.teacl_molarity}")
meta_cols[0].write(f"**Rated Cap.:** {cell.rated_capacity} mAh")
meta_cols[1].write(f"**Config:** {cell.configuration}")
meta_cols[2].write(f"**Assembly Date:** {cell.assembly_date.date()}")
meta_cols[3].write(f"**Status:** {cell.status.capitalize()}")
st.markdown(f"**Notes** \n{cell.notes or '—'}")

if not cycles:
    st.warning("No cycles logged for this cell yet.")
    st.stop()

# --- DataFrame and Plotting logic (no changes needed here) ---
orig_df = pd.DataFrame(
    [
        {
            "Cycle #": c.cycle_no,
            "Current (mA/cm²)": c.current_density,
            "Charge V": c.charge_V,
            "Discharge V": c.discharge_V,
            "ΔV": c.delta_V,
            "CE %": c.ce_pct,
            "Cap. (mAh)": c.capacity_mAh,
            "Obs": c.observation or "",
        }
        for c in cycles
    ]
)

st.subheader("📊 Cycle table (click to edit)")
edited_df = st.data_editor(
    orig_df,
    use_container_width=True,
    num_rows="dynamic",
    key="cycle_editor",
)

if st.button("💾 Save changes", disabled=edited_df.equals(orig_df)):
    if update_cycles_in_db(orig_df, edited_df, cell.id):
        st.success("Changes saved to database.")
        st.rerun()
    else:
        st.info("No changes detected.")

st.subheader("🔎 Plot a metric")
metric = st.selectbox(
    "Y-axis metric",
    ["Charge V", "Discharge V", "ΔV", "CE %", "Cap. (mAh)"],
    index=3,
)
fig = px.line(edited_df, x="Cycle #", y=metric, markers=True)
st.plotly_chart(fig, use_container_width=True)