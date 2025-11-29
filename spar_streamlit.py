import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Wing Spar Quick Sizer", layout="wide")

# ---------------------------
# Physics functions
# ---------------------------

def root_bending_moment(mass_kg, span_m, load_factor, g=9.81):
    W = mass_kg * g
    L = W * load_factor
    M = L * span_m / 8.0  # uniform lift assumption
    return W, L, M, M * 1000  # return N·m and N·mm versions

def tube_section(D, d):
    I = math.pi / 64 * (D**4 - d**4)
    c = D / 2
    S = I / c
    return I, S

def compute_tube(mass, span, g_load, D, d, strength):
    W, L, M, Mmm = root_bending_moment(mass, span, g_load)
    I, S = tube_section(D, d)
    stress = Mmm / S       # MPa
    SF = strength / stress
    return stress, SF


# ---------------------------
# UI - Sidebar
# ---------------------------

st.title("Wing Spar Sizing Tool (Streamlit Demo)")
st.caption("Compute bending stress + safety factor for carbon tube spars")

with st.sidebar:
    st.header("Inputs")

    mass = st.number_input("Aircraft Mass (kg)", value=5.0, min_value=0.1)
    span = st.number_input("Wingspan (m)", value=2.0, min_value=0.1)
    g_load = st.number_input("Load Factor (g)", value=3.0, min_value=0.1)
    strength = st.number_input("Material Allowable Strength (MPa)", value=600.0, min_value=10.0)
    target_SF = st.number_input("Target Safety Factor", value=2.0, min_value=0.1)

    st.subheader("Candidate Tubes (outer, inner mm)")
    text_default = "8,6\n10,8\n12,8\n14,10\n16,12\n18,14"
    tube_text = st.text_area("Edit tube list", value=text_default, height=150)

    run_btn = st.button("Compute")


# ---------------------------
# Calculate
# ---------------------------

def parse_candidates(text):
    tubes = []
    lines = text.strip().split("\n")
    for line in lines:
        parts = line.replace(" ", "").split(",")
        if len(parts) == 2:
            try:
                D = float(parts[0])
                d = float(parts[1])
                if d < D:
                    tubes.append((D, d))
            except:
                pass
    return tubes

if run_btn:
    tubes = parse_candidates(tube_text)

    if not tubes:
        st.error("No valid tubes! Use format: 12,8 on each line.")
        st.stop()

    W, L, M, Mmm = root_bending_moment(mass, span, g_load)

    st.subheader("Wing Bending Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Weight (N)", f"{W:.2f}")
    col2.metric("Lift at Load (N)", f"{L:.2f}")
    col3.metric("Root Moment (N·m)", f"{M:.2f}")

    results = []
    for D, d in tubes:
        stress, SF = compute_tube(mass, span, g_load, D, d, strength)
        results.append({
            "Outer (mm)": D,
            "Inner (mm)": d,
            "Stress (MPa)": stress,
            "Safety Factor": SF,
            "Pass": SF >= target_SF
        })

    df = pd.DataFrame(results).sort_values("Outer (mm)")
    st.subheader("Results Table")
    st.dataframe(df.style.format({"Stress (MPa)": "{:.1f}", "Safety Factor": "{:.2f}"}))

    good = df[df["Pass"] == True]
    if not good.empty:
        best = good.iloc[0]
        st.success(f"Recommended: {int(best['Outer (mm)'])} x {int(best['Inner (mm)'])} mm  "
                   f"(SF={best['Safety Factor']:.2f})")
    else:
        st.error("No tube meets the target safety factor!")

    # Plot SF vs Diameter
    st.subheader("Safety Factor vs Tube Diameter")
    fig, ax = plt.subplots(figsize=(6,3))
    ax.plot(df["Outer (mm)"], df["Safety Factor"], marker="o")
    ax.axhline(target_SF, color="red", linestyle="--", label="Target SF")
    ax.set_xlabel("Outer Diameter (mm)")
    ax.set_ylabel("Safety Factor")
    ax.grid(True, linestyle=":")
    ax.legend()
    st.pyplot(fig)

else:
    st.info("Enter values in the sidebar and click **Compute**.")
