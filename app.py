import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import fsolve

# --- Page Configuration ---
st.set_page_config(page_title="VCE Overpressure Calculator", layout="wide")

st.title("💥 Vapour Cloud Explosion Calculator")
st.markdown("Estimate overpressure effects using the continuous **Kinney-Graham Surface Burst** equation.")

# --- Gas Database ---
GAS_DB = {
    "Hydrogen (H2)": {"density": 0.08988, "hoc": 141.58},
    "Propane (C3H8)": {"density": 2.0098, "hoc": 50.33},
    "Methane (CH4)": {"density": 0.68, "hoc": 50.0},
    "Custom": {"density": 1.0, "hoc": 46.0}
}

# --- Inputs ---
st.header("1. Define Explosion Parameters")
col1, col2, col3 = st.columns(3)

def get_vapour_inputs(suffix, default_gas, default_vol):
    gas_choice = st.selectbox(f"Gas Preset {suffix}", list(GAS_DB.keys()), index=list(GAS_DB.keys()).index(default_gas), key=f"gas{suffix}")
    is_custom = gas_choice == "Custom"
    
    input_mode = st.radio(f"Input Method {suffix}", ["Volume & Density", "Mass"], key=f"mode{suffix}", horizontal=True)
    if input_mode == "Volume & Density":
        v = st.number_input(f"Volume {suffix} (m³)", value=default_vol, step=0.01, format="%.5f", key=f"v{suffix}")
        d = st.number_input(f"Density {suffix} (kg/m³)", value=GAS_DB[gas_choice]["density"], disabled=not is_custom, format="%.5f", key=f"den{suffix}")
        m = v * d
        st.caption(f"Calculated Mass: **{m:.5f} kg**")
    else:
        m = st.number_input(f"Mass {suffix} (kg)", value=0.0, step=0.1, format="%.5f", key=f"m{suffix}")
            
    h = st.number_input(f"Heat of Combustion {suffix} (MJ/kg)", value=GAS_DB[gas_choice]["hoc"], disabled=not is_custom, key=f"h{suffix}")
    return m, h

with col1:
    st.subheader("Vapour 1")
    mass1, hoc1 = get_vapour_inputs("1", "Hydrogen (H2)", 0.0326)

with col2:
    st.subheader("Vapour 2")
    mass2, hoc2 = get_vapour_inputs("2", "Propane (C3H8)", 0.13363)

with col3:
    st.subheader("Site & Environment")
    yield_pct = st.number_input("TNT Yield Factor (%)", value=3.0, step=1.0) / 100.0
    p_ambient = st.number_input("Ambient Pressure (kPa)", value=101.3, step=0.1)

# --- TNT Equivalency Logic ---
TNT_ENERGY_DENSITY = 4.68  # MJ/kg

tnt_eq1 = (mass1 * hoc1 * yield_pct) / TNT_ENERGY_DENSITY if mass1 > 0 else 0
tnt_eq2 = (mass2 * hoc2 * yield_pct) / TNT_ENERGY_DENSITY if mass2 > 0 else 0
total_tnt_eq = tnt_eq1 + tnt_eq2
w_third = total_tnt_eq**(1/3) if total_tnt_eq > 0 else 0

# --- Kinney-Graham Pure Math Engine ---
def calc_scaled_pressure(z_surface):
    """Calculates scaled overpressure (Ps/Pa) for a surface burst using the doubled-mass assumption."""
    # Convert surface Z to an effective free-air Z by doubling the mass
    z_eff = z_surface / (2.0**(1/3))
    
    # Kinney-Graham formula
    term1 = 1 + (z_eff / 4.5)**2
    term2 = np.sqrt(1 + (z_eff / 0.048)**2)
    term3 = np.sqrt(1 + (z_eff / 0.32)**2)
    term4 = np.sqrt(1 + (z_eff / 1.35)**2)
    
    return 808 * (term1) / (term2 * term3 * term4)

def solve_for_z(target_p_scaled):
    """Uses SciPy to mathematically solve for Z given a target scaled pressure."""
    if target_p_scaled <= 0: return 0
    # Lambda function: find where calc_scaled_pressure(Z) - target_p_scaled = 0
    func = lambda z: calc_scaled_pressure(z) - target_p_scaled
    # Start the solver guessing at Z=10
    z_solution = fsolve(func, 10.0)[0]
    return z_solution

# --- UI Layout ---
st.divider()
st.header("2. Analysis Results")

m1, m2, m3 = st.columns(3)
m1.metric("Vapour 1 TNT Eq.", f"{tnt_eq1:.5f} kg")
m2.metric("Vapour 2 TNT Eq.", f"{tnt_eq2:.5f} kg")
m3.metric("TOTAL TNT Equivalent (W)", f"{total_tnt_eq:.5f} kg", delta_color="inverse")

st.write("") 

st.subheader("Spatial Separation Distances (Continuous Formula)")
st.markdown("Calculated using the Kinney-Graham surface burst equation and an algorithmic solver (no lookup tables).")

# Dynamic Threshold Calculations
thresholds_kpa = [70, 21, 7]
table_data = []

for p in thresholds_kpa:
    scaled_p = p / p_ambient
    
    # Let the solver find the exact Z value
    z_val = solve_for_z(scaled_p)
    r_val = z_val * w_third
    
    table_data.append({
        "Overpressure Threshold": f"{p} kPa",
        "Scaled Overpressure (Ps/Pa)": f"{scaled_p:.3f}",
        "Exact Z value (m/kg^1/3)": f"{z_val:.3f}",
        "Exact Separation Distance (m)": f"{r_val:.3f}"
    })

st.table(pd.DataFrame(table_data))
