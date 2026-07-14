import json
import pandas as pd
import streamlit as st
from PIL import Image

from config import *
from materials import MATERIALS
from sections import build_section
from geometry import m_per_pixel_from_reference, member_length_m
from solver import (
    slenderness, euler_critical_load, euler_critical_stress,
    johnson_critical_stress, combined_stress, imperfection_knockdown,
    lambda_critical, recommend_regime,
)
from degradation import combined_degradation_factor
from risk import compute_risk_breakdown, aggregate_member_risks
from validation import validate_geometry, confidence_score
from report import build_report_markdown, results_to_csv_bytes
from export import export_project_json, import_project_json
from plotting import (
    overlay_members_on_image, make_stress_slenderness_plot,
    make_capacity_plot, make_risk_bar_plot,
)
from sample_data import DEFAULT_MEMBERS

try:
    from vision import detect_shelf_members, draw_detected_lines, convert_detected_lines_to_members
    VISION_AVAILABLE = True
except Exception:
    VISION_AVAILABLE = False

st.set_page_config(page_title=APP_NAME, layout="wide")
st.title(APP_NAME)
st.caption(f"Version {APP_VERSION} — photo-assisted shelf stability screening")

if "members" not in st.session_state:
    st.session_state.members = [dict(m) for m in DEFAULT_MEMBERS]
if "image" not in st.session_state:
    st.session_state.image = Image.new("RGB", (420, 520), "white")

with st.sidebar:
    st.header("Project")
    project_name = st.text_input("Project name", "Kitchen Shelf Assessment")
    st.info("This is a screening prototype, not a substitute for an on-site structural inspection.")

tabs = st.tabs([
    "1 Upload & Vision", "2 Geometry", "3 Material & Environment",
    "4 Loads & Analysis", "5 Results", "6 Report & Project"
])

with tabs[0]:
    uploaded = st.file_uploader("Upload front-view photo", type=["png", "jpg", "jpeg"])
    if uploaded:
        st.session_state.image = Image.open(uploaded).convert("RGB")

    st.image(st.session_state.image, caption="Input image", use_container_width=True)

    if VISION_AVAILABLE:
        if st.button("Detect candidate shelf members"):
            try:
                lines = detect_shelf_members(st.session_state.image)
                st.session_state.detected_lines = lines
                st.session_state.members = convert_detected_lines_to_members(lines[:12])
            except Exception as exc:
                st.error(f"Vision detection failed: {exc}")

        if "detected_lines" in st.session_state:
            st.image(
                draw_detected_lines(st.session_state.image, st.session_state.detected_lines),
                caption="Detected line candidates",
                use_container_width=True,
            )
            st.write(f"Detected candidates: {len(st.session_state.detected_lines)}")
    else:
        st.warning("OpenCV vision is unavailable. Manual member editing remains available.")

with tabs[1]:
    c1, c2 = st.columns(2)
    with c1:
        ref_pixels = st.number_input("Reference pixels", min_value=1.0, value=DEFAULT_REFERENCE_PIXELS)
    with c2:
        ref_length_m = st.number_input("Known reference length (m)", min_value=0.01, value=DEFAULT_REFERENCE_LENGTH_M)

    scale = m_per_pixel_from_reference(ref_pixels, ref_length_m)
    st.metric("Scale", f"{scale:.6f} m/pixel")

    member_count = st.number_input("Member count", 1, 20, len(st.session_state.members), 1)
    while len(st.session_state.members) < member_count:
        i = len(st.session_state.members) + 1
        st.session_state.members.append({"id": f"M{i}", "type": "beam", "x1": 40, "y1": 40*i, "x2": 300, "y2": 40*i})
    st.session_state.members = st.session_state.members[:member_count]

    edited = []
    for i, m in enumerate(st.session_state.members):
        with st.expander(f"{m.get('id', f'M{i+1}')} — {m.get('type', 'member')}", expanded=i < 4):
            c1, c2, c3 = st.columns(3)
            with c1:
                mid = st.text_input("ID", m.get("id", f"M{i+1}"), key=f"id{i}")
                typ = st.selectbox("Type", ["upright", "beam", "brace", "bracket"],
                                   index=["upright","beam","brace","bracket"].index(m.get("type","beam")),
                                   key=f"type{i}")
            with c2:
                x1 = st.number_input("x1", value=float(m.get("x1", 0)), key=f"x1{i}")
                y1 = st.number_input("y1", value=float(m.get("y1", 0)), key=f"y1{i}")
            with c3:
                x2 = st.number_input("x2", value=float(m.get("x2", 100)), key=f"x2{i}")
                y2 = st.number_input("y2", value=float(m.get("y2", 100)), key=f"y2{i}")
            edited.append({"id": mid, "type": typ, "x1": x1, "y1": y1, "x2": x2, "y2": y2})
    st.session_state.members = edited

with tabs[2]:
    material_name = st.selectbox("Material", list(MATERIALS))
    mat = MATERIALS[material_name]
    c1, c2, c3 = st.columns(3)
    with c1:
        E_GPa = st.number_input("E (GPa)", value=float(mat["E_GPa"]))
    with c2:
        yield_MPa = st.number_input("Yield/allowable stress (MPa)", value=float(mat["yield_MPa"]))
    with c3:
        density = st.number_input("Density (kg/m³)", value=float(mat["density"]))

    category = "wood" if material_name in {"Plywood", "MDF", "Particle Board"} else "metal"
    moisture = st.slider("Moisture severity", 0.0, 1.0, 0.2, 0.05)
    corrosion = st.slider("Corrosion severity", 0.0, 1.0, 0.1, 0.05)
    looseness = st.slider("Joint looseness severity", 0.0, 1.0, 0.1, 0.05)

    deg = combined_degradation_factor(corrosion, moisture, looseness, category)
    E_eff_GPa = E_GPa * deg["combined_factor"]
    yield_eff_MPa = yield_MPa * deg["combined_factor"]
    st.write(f"Effective E: **{E_eff_GPa:.2f} GPa**")
    st.write(f"Effective strength: **{yield_eff_MPa:.2f} MPa**")

    shape = st.selectbox("Section shape", ["rectangular", "circular", "hollow_circular"])
    if shape == "rectangular":
        c1, c2 = st.columns(2)
        with c1:
            width_m = st.number_input("Width b (m)", 0.001, value=0.02, step=0.001, format="%.4f")
        with c2:
            depth_m = st.number_input("Depth h (m)", 0.001, value=0.02, step=0.001, format="%.4f")
        section = build_section(shape, width_m=width_m, depth_m=depth_m)
    elif shape == "circular":
        diameter_m = st.number_input("Diameter d (m)", 0.001, value=0.02, step=0.001, format="%.4f")
        section = build_section(shape, diameter_m=diameter_m)
    else:
        c1, c2 = st.columns(2)
        with c1:
            outer_d_m = st.number_input("Outer D (m)", 0.002, value=0.025, step=0.001, format="%.4f")
        with c2:
            inner_d_m = st.number_input("Inner d (m)", 0.0, value=0.020, step=0.001, format="%.4f")
        if inner_d_m >= outer_d_m:
            st.error("Inner diameter must be less than outer diameter.")
            section = build_section("hollow_circular", outer_d_m=outer_d_m, inner_d_m=max(0.0, outer_d_m*0.5))
        else:
            section = build_section(shape, outer_d_m=outer_d_m, inner_d_m=inner_d_m)

    st.json({k: round(v, 8) if isinstance(v, float) else v for k, v in section.items()})

with tabs[3]:
    c1, c2, c3 = st.columns(3)
    with c1:
        K = st.number_input("Effective length factor K", 0.1, value=DEFAULT_K, step=0.1)
        imperf_mm = st.number_input("Initial imperfection (mm)", 0.0, value=DEFAULT_IMPERFECTION_MM, step=0.5)
    with c2:
        axial_load_N = st.number_input("Axial load per member (N)", 0.0, value=DEFAULT_AXIAL_LOAD_N, step=50.0)
        eccentricity_mm = st.number_input("Eccentricity (mm)", 0.0, value=DEFAULT_ECCENTRICITY_MM, step=1.0)
    with c3:
        extra_moment_Nm = st.number_input("Extra moment (N·m)", 0.0, value=DEFAULT_EXTRA_MOMENT_NM, step=0.5)
        geometry_conf = st.slider("Geometry confidence", 0.0, 1.0, 0.8, 0.05)

    if st.button("Run stability analysis", type="primary"):
        E_Pa = E_eff_GPa * 1e9
        sigma_y_Pa = yield_eff_MPa * 1e6
        lam_crit = lambda_critical(E_Pa, sigma_y_Pa)
        conf = confidence_score(geometry_conf, 0.9, 0.75, 0.65)

        records, all_messages = [], []
        for member in st.session_state.members:
            L_m = member_length_m(member, scale)
            lam = slenderness(K, L_m, section["r"])
            Pcr = euler_critical_load(E_Pa, section["I"], K, L_m)
            Pcr_adj, knock = imperfection_knockdown(Pcr, imperf_mm)
            total_moment = extra_moment_Nm + axial_load_N*(eccentricity_mm/1000)
            sigma, sigma_a, sigma_b = combined_stress(
                axial_load_N, section["A"], total_moment, section["c"], section["I"]
            )
            sigma_e = euler_critical_stress(Pcr_adj, section["A"])
            sigma_j = johnson_critical_stress(lam, E_Pa, sigma_y_Pa)
            positive_caps = [x for x in (sigma_e, sigma_j) if x > 0]
            governing_sigma = min(positive_caps) if positive_caps else sigma_y_Pa
            utilization = sigma / max(governing_sigma, 1e-9)
            buckling_util = axial_load_N / max(Pcr_adj, 1e-9)
            norm_stress = sigma / max(sigma_y_Pa, 1e-9)

            risk = compute_risk_breakdown(
                norm_stress, buckling_util, lam, imperf_mm,
                corrosion_level=corrosion, moisture_level=moisture,
                looseness_level=looseness, confidence_score=conf["score"],
            )
            messages = validate_geometry(L_m, section, E_Pa, sigma_y_Pa, lam, utilization, imperf_mm)
            all_messages.extend([{**m, "member_id": member["id"]} for m in messages])

            records.append({
                "id": member["id"], "type": member["type"], "length_m": L_m,
                "slenderness": lam, "working_stress_MPa": sigma/1e6,
                "normalized_stress": norm_stress,
                "euler_capacity_kN": Pcr/1000,
                "knockdown_capacity_kN": Pcr_adj/1000,
                "buckling_utilization": buckling_util,
                "utilization": utilization,
                "risk_score": risk["total_score"],
                "risk_band": risk["risk_band"],
                "dominant_risk": risk["dominant_component"],
                "regime": recommend_regime(lam, lam_crit, eccentricity_mm, imperf_mm),
            })

        st.session_state.results_df = pd.DataFrame(records)
        st.session_state.messages = all_messages
        st.session_state.summary = aggregate_member_risks(
            [{"id": r["id"], "total_score": r["risk_score"]} for r in records]
        )
        st.success("Analysis complete.")

with tabs[4]:
    df = st.session_state.get("results_df")
    if df is None:
        st.info("Run the analysis first.")
    else:
        st.dataframe(df, use_container_width=True)

        colors = [RISK_COLORS.get(x, "blue") for x in df["risk_band"]]
        c1, c2 = st.columns(2)
        with c1:
            st.image(
                overlay_members_on_image(st.session_state.image, st.session_state.members, colors),
                caption="Risk overlay",
                use_container_width=True,
            )
        with c2:
            st.pyplot(make_stress_slenderness_plot(df), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(make_capacity_plot(df), use_container_width=True)
        with c2:
            st.pyplot(make_risk_bar_plot(df), use_container_width=True)

        st.subheader("Shelf summary")
        st.json(st.session_state.summary)

        st.subheader("Validation")
        messages = st.session_state.get("messages", [])
        if not messages:
            st.success("No validation warnings.")
        for m in messages:
            text = f"{m['member_id']} — {m['message']}"
            if m["severity"] == "error":
                st.error(text)
            elif m["severity"] == "warning":
                st.warning(text)
            else:
                st.info(text)

with tabs[5]:
    df = st.session_state.get("results_df")
    if df is None:
        st.info("Run the analysis before exporting.")
    else:
        config = {
            "project_name": project_name,
            "material_name": material_name,
            "E_GPa_effective": E_eff_GPa,
            "yield_MPa_effective": yield_eff_MPa,
            "section": section,
            "K": K,
            "imperf_mm": imperf_mm,
            "axial_load_N": axial_load_N,
            "eccentricity_mm": eccentricity_mm,
            "extra_moment_Nm": extra_moment_Nm,
            "environment": {
                "moisture": moisture,
                "corrosion": corrosion,
                "looseness": looseness,
            },
        }
        project = {
            "config": config,
            "members": st.session_state.members,
            "results": df.to_dict(orient="records"),
            "summary": st.session_state.summary,
        }
        report_md = build_report_markdown(project_name, config, df, st.session_state.summary)
        st.download_button("Download Markdown report", report_md, "shelf_stability_report.md", "text/markdown")
        st.download_button("Download results CSV", results_to_csv_bytes(df), "shelf_results.csv", "text/csv")
        st.download_button("Download project JSON", export_project_json(project), "shelf_project.json", "application/json")

        uploaded_project = st.file_uploader("Import project JSON", type=["json"], key="project_import")
        if uploaded_project:
            try:
                imported = import_project_json(uploaded_project.read().decode("utf-8"))
                st.json(imported)
            except Exception as exc:
                st.error(f"Could not import project: {exc}")
