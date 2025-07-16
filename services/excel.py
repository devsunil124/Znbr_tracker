import pandas as pd
import os

def build_excel(cell_id, cell_data, cycle_data, output_path=""):
    filename = os.path.join(output_path or "media", f"{cell_id}.xlsx")

    # Prepare the cycle data
    data = [{
        "Cycle No": c.cycle_no,
        "Current Density (mA/cm²)": c.current_density,
        "Charge Voltage (V)": c.charge_V,
        "Discharge Voltage (V)": c.discharge_V,
        "ΔV": c.delta_V,
        "CE (%)": c.ce_pct,
        "Capacity (mAh)": c.capacity_mAh,
        "pH": c.pH,
        "Observations": c.observation,
    } for c in cycle_data]

    df = pd.DataFrame(data)

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Cycle Data')

        # Add cell metadata on a separate sheet
        metadata = {
            "Cell ID": [cell_data.cell_id],
            "Felt Type": [cell_data.felt_type],
            "Sealing Type": [cell_data.sealing_type],
            "Notes": [cell_data.notes],
        }
        meta_df = pd.DataFrame(metadata)
        meta_df.to_excel(writer, index=False, sheet_name='Cell Info')

    return filename
