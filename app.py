import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="VCE Overpressure Calculator", layout="wide")

st.title("💥 Vapour Cloud Explosion (VCE) Calculator")
st.markdown("Estimate overpressure effects using TNT-Equivalent and Baker-Strehlow-Tang (BST) models. Inputs are combined to evaluate the total explosion energy.")

# --- Front and Centre Inputs ---
st.header("1. Define Explosion Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Vapour 1")
    input_mode1 = st.radio("Input Method", ["Mass", "Volume & Density"], key="mode1", horizontal=True)
    
    if input_mode1 == "Mass":
        mass1 = st.number_input("Mass (kg)", value=1000.0, step=100.0, key="m1")
    else:
        vol1 = st.number_input("Volume (m³)", value=500.0, step=10.0, key="v1")
        den1 = st.number_input("Density (kg/m³)", value=2.0, step=0.1, key="d1")
        mass1 = vol1 * den1
        st.caption(f"Calculated Mass: **{mass1:.1f} kg**")
        
    hoc1 = st.number_input("Heat of Combustion (MJ/kg)", value=46.0, key="h1")
    react1 = st.selectbox("Reactivity", ["Low", "Medium", "High"], index=1, key="r1")

with col2:
    st.subheader("Vapour 2 (Optional)")
    input_mode2 = st.radio("Input Method", ["Mass", "Volume & Density"], key="mode2", horizontal=True)
    
    if input_mode2 == "Mass":
        mass2 = st.number_input("Mass (kg)", value=0.0, step=100.0, key="m2")
    else:
        vol2 = st.number_input("Volume (m³)", value=0.0, step=10.0, key="v2")
        den2 = st.number_input("Density (kg/m³)", value=1.5, step=0.1, key="d2")
        mass2 = vol2 * den2
        st.caption(f"Calculated Mass: **{mass2:.1f} kg**")
        
    hoc2 = st.number_input("Heat of Combustion (MJ/kg)", value=50.0, key="h2")
    react2 = st.selectbox("Reactivity", ["Low", "Medium", "High"], index=0, key="r2")

with col3:
    st.subheader("Site & Environment")
    distance_target = st.number_input("Target Evaluation Distance (m)", value=50.0, step=1.0)
    congestion = st.selectbox("Obstacle Density / Congestion", ["Low", "Medium", "High"], index=1)
    yield_pct = st.slider("TNT Yield Factor (%)", 1, 20, 5) / 100.0

# --- Mixture Logic ---
total_mass = mass1 + mass2

if total_mass > 0:
    weighted_hoc = ((mass1 * hoc1) + (mass2 * hoc2)) / total_mass
else:
    weighted_hoc = 0

reactivity_levels = {"Low": 1, "Medium": 2, "High": 3}
max_react_val = max(reactivity_levels[react1] if mass1 > 0 else 0, 
                    reactivity_levels[react2] if mass2 > 0 else 0)

reverse_reactivity = {1: "Low", 2: "Medium", 3: "High", 0: "Low"}
overall_reactivity = reverse_reactivity[max_react_val]

# --- Calculation Engine ---
def calculate_metrics(d, m_total, h_avg, react, cong, y_pct):
    if m_total <= 0 or d <= 0:
        return 0, 0
        
    tnt_energy_density = 4.68  # MJ/kg
    p_atm = 101325  # Pa
    
    # 1. TNT Method
    energy_tnt_mj = m_total * h_avg * y_pct
    tnt_mass_eq = energy_tnt_mj / tnt_energy_density
    z = d / (tnt_mass_eq**(1/3)) if tnt_mass_eq > 0 else 0
    
    if z > 0:
        p_tnt = ((80.8 / z) + (114 / z**2) + (141 / z**3)) * 2 # Surface burst reflection
    else:
        p_tnt = 0

    # 2. BST Method
    energy_total_j = m_total * h_avg * 1e6
    sachs_r = d * (p_atm / energy_total_j)**(1/3) if energy_total_j > 0 else 0
    
    mach_map = {
        ("High", "High"): 5.2, ("High", "Medium"): 2.0, ("High", "Low"): 0.5,
        ("Medium", "High"): 1.6, ("Medium", "Medium"): 0.6, ("Medium", "Low"): 0.2,
        ("Low", "High"): 0.5, ("Low", "Medium"): 0.2, ("Low", "Low"): 0.1
    }
    mach = mach_map[(react, cong)]
    
    if sachs_r > 0:
        ratio = (0.15 * (mach**1.2)) / (sachs_r**1.1)
        max_ratio = (mach**2) * 1.5 
        ratio = min(ratio, max_ratio)
        p_bst = ratio * (p_atm / 1000) # Convert to kPa
    else:
        p_bst = 0
        
    return p_tnt, p_bst

# Generate arrays for plotting and threshold interpolation
calc_distances = np.
