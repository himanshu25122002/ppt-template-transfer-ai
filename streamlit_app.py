"""
streamlit_app.py
Streamlit dashboard for the PPT Template Transfer AI pipeline.
"""

import os
import sys
import json
import time
import tempfile

import streamlit as st
import pandas as pd

# ── Page config must be first Streamlit call ──────────────────────────────────
st.set_page_config(
    page_title="PPT Template Transfer AI",
    page_icon="📊",
    layout="wide",
)

from extractor import extract_presentation
from template_analyzer import analyze_all_templates
from template_selector import select_best_template
from ai_slide_classifier import classify_slides, check_gemini_status
from generator import generate_presentation


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATES_DIR = "templates"
OUTPUT_DIR = "output"
INPUT_DIR = "input"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_template_files() -> list[str]:
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        return []
    return [f for f in os.listdir(TEMPLATES_DIR) if f.lower().endswith(".pptx")]


def save_uploaded_file(uploaded_file) -> str:
    os.makedirs(INPUT_DIR, exist_ok=True)
    save_path = os.path.join(INPUT_DIR, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.title("⚙️ System Panel")
        st.divider()

        template_files = get_template_files()
        st.metric("Templates Detected", len(template_files))

        if template_files:
            with st.expander("📁 Template Files"):
                for t in template_files:
                    st.write(f"• {t}")
        else:
            st.warning("No templates found in `templates/` folder.")

        st.divider()

        gemini_status = check_gemini_status()
        if gemini_status["ready"]:
            st.success("🤖 Gemini API: Ready")
        else:
            st.error(f"🤖 Gemini API: {gemini_status['message']}")

        st.divider()

        st.subheader("🖥️ System Info")
        st.write(f"Python {sys.version.split()[0]}")
        st.write(f"Output dir: `{OUTPUT_DIR}/`")
        st.write(f"Templates dir: `{TEMPLATES_DIR}/`")

        st.divider()
        st.caption("PPT Template Transfer AI v1.0")


# ─────────────────────────────────────────────────────────────────────────────
# Main Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def main():
    render_sidebar()

    st.title("📊 PPT Template Transfer AI")
    st.markdown(
        "Automatically extract content from your presentation, "
        "score available templates, and rebuild a polished output."
    )
    st.divider()

    # ── Step 1: Upload ────────────────────────────────────────────────────────
    st.header("1️⃣  Upload Input PPTX")

    uploaded_file = st.file_uploader(
        "Upload your source presentation",
        type=["pptx"],
        help="This presentation's content will be extracted and transferred.",
    )

    if uploaded_file is None:
        st.info("Upload a PPTX file to begin.")
        st.stop()

    input_path = save_uploaded_file(uploaded_file)
    st.success(f"✅ Uploaded: `{uploaded_file.name}`")

    # ── Step 2: Detect Templates ──────────────────────────────────────────────
    st.header("2️⃣  Detected Templates")

    template_files = get_template_files()
    if not template_files:
        st.error("No PPTX templates found in `templates/`. Add at least one template to continue.")
        st.stop()

    template_df = pd.DataFrame({"Template File": template_files})
    st.dataframe(template_df, use_container_width=True)

    # ── Run Pipeline Button ───────────────────────────────────────────────────
    st.divider()
    run_button = st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True)

    if not run_button:
        st.stop()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Step 3: Extract Content ───────────────────────────────────────────────
    st.header("3️⃣  Extracting Slide Content")

    with st.spinner("Extracting slides from uploaded PPTX..."):
        progress = st.progress(0, text="Extracting slides…")
        slides_data = extract_presentation(input_path, OUTPUT_DIR)
        progress.progress(100, text="Extraction complete")
        time.sleep(0.3)
        progress.empty()

    st.success(f"✅ Extracted **{len(slides_data)}** slide(s).")

    # Show extracted content in a table
    rows = []
    for s in slides_data:
        rows.append({
            "Slide #": s["slide_number"],
            "Title": s.get("title") or "(no title)",
            "Body Lines": len(s.get("body", [])),
            "Bullets": len(s.get("bullets", [])),
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with st.expander("📄 Raw Extracted JSON"):
        st.json(slides_data)

    # ── Step 4: Gemini Classification ─────────────────────────────────────────
    st.header("4️⃣  AI Slide Classification (Gemini)")

    with st.spinner("Classifying slides with Gemini…"):
        progress = st.progress(0, text="Classifying…")
        classified_slides = classify_slides(slides_data, OUTPUT_DIR)
        progress.progress(100, text="Classification complete")
        time.sleep(0.3)
        progress.empty()

    gemini_status = check_gemini_status()
    method = "Gemini gemini-1.5-flash" if gemini_status["ready"] else "Heuristic fallback"
    st.info(f"Classification method: **{method}**")

    cls_rows = []
    for s in classified_slides:
        cls_rows.append({
            "Slide #": s["slide_number"],
            "Title": s.get("title") or "(no title)",
            "Classification": s.get("classification", "—"),
        })

    st.dataframe(pd.DataFrame(cls_rows), use_container_width=True)

    # Classification distribution chart
    cls_series = pd.Series([s["classification"] for s in classified_slides])
    cls_counts = cls_series.value_counts().reset_index()
    cls_counts.columns = ["Classification", "Count"]
    st.bar_chart(cls_counts.set_index("Classification"))

    # ── Step 5: Analyze Templates ─────────────────────────────────────────────
    st.header("5️⃣  Analyzing Templates")

    with st.spinner("Analyzing template structures…"):
        progress = st.progress(0, text="Analyzing templates…")
        templates_metadata = analyze_all_templates(TEMPLATES_DIR)
        progress.progress(100, text="Analysis complete")
        time.sleep(0.3)
        progress.empty()

    template_meta_rows = []
    for t in templates_metadata:
        template_meta_rows.append({
            "Template": t["template_name"],
            "Layouts": t["layout_count"],
            "Title Slide": "✅" if t["supports_title_slide"] else "❌",
            "Bullet Slide": "✅" if t["supports_bullet_slide"] else "❌",
            "Two Column":   "✅" if t["supports_two_column"] else "❌",
            "Table":        "✅" if t["supports_table"] else "❌",
        })

    st.dataframe(pd.DataFrame(template_meta_rows), use_container_width=True)

    # ── Step 6: Score Templates ───────────────────────────────────────────────
    st.header("6️⃣  Template Scores")

    with st.spinner("Scoring templates…"):
        best_template, all_scores = select_best_template(
            templates_metadata, slides_data, OUTPUT_DIR
        )

    score_rows = []
    for s in all_scores:
        row = {"Template": s["template_name"], "Total Score": s["total_score"]}
        row.update(s["breakdown"])
        score_rows.append(row)

    score_df = pd.DataFrame(score_rows)
    st.dataframe(score_df, use_container_width=True)

    # Bar chart of total scores
    chart_df = score_df[["Template", "Total Score"]].set_index("Template")
    st.bar_chart(chart_df)

    # ── Step 7: Best Template ─────────────────────────────────────────────────
    st.header("7️⃣  Selected Template")

    st.success(
        f"🏆 Best match: **{best_template['template_name']}** "
        f"— Score: **{best_template['total_score']}**"
    )

    with st.expander("Score Breakdown"):
        st.json(best_template["breakdown"])

    # ── Step 8: Generate Presentation ────────────────────────────────────────
    st.header("8️⃣  Generating Presentation")

    with st.spinner("Building final presentation…"):
        progress = st.progress(0, text="Generating slides…")
        output_path = generate_presentation(
            classified_slides,
            best_template["template_path"],
            OUTPUT_DIR,
        )
        progress.progress(100, text="Done!")
        time.sleep(0.3)
        progress.empty()

    st.success(f"✅ Presentation generated: `{output_path}`")

    # ── Step 9: Download ──────────────────────────────────────────────────────
    st.header("9️⃣  Download Final PPTX")

    with open(output_path, "rb") as f:
        pptx_bytes = f.read()

    st.download_button(
        label="⬇️ Download final_presentation.pptx",
        data=pptx_bytes,
        file_name="final_presentation.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        use_container_width=True,
        type="primary",
    )

    st.divider()
    st.balloons()
    st.success("🎉 Pipeline complete! Your presentation is ready.")


if __name__ == "__main__":
    main()
