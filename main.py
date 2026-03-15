"""
main.py
CLI entry point — runs the full pipeline without Streamlit.

Usage:
    python main.py input/sample.pptx
"""

import sys
import os
import json
import argparse
import time


def run_pipeline(input_pptx: str, templates_dir: str = "templates", output_dir: str = "output"):
    """Execute the complete end-to-end pipeline."""

    print("=" * 60)
    print("  PPT Template Transfer AI — CLI Pipeline")
    print("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    # ── Step 1: Extract ───────────────────────────────────────────────────────
    print("\n[1/5] Extracting slide content...")
    t0 = time.time()
    from extractor import extract_presentation
    slides_data = extract_presentation(input_pptx, output_dir)
    print(f"      → {len(slides_data)} slides extracted ({time.time() - t0:.2f}s)")

    # ── Step 2: Classify ──────────────────────────────────────────────────────
    print("\n[2/5] Classifying slides with AI...")
    t0 = time.time()
    from ai_slide_classifier import classify_slides, check_gemini_status
    status = check_gemini_status()
    print(f"      → Gemini status: {status['message']}")
    classified_slides = classify_slides(slides_data, output_dir)
    print(f"      → Classification complete ({time.time() - t0:.2f}s)")

    # ── Step 3: Analyze Templates ─────────────────────────────────────────────
    print("\n[3/5] Analyzing templates...")
    t0 = time.time()
    from template_analyzer import analyze_all_templates
    templates_metadata = analyze_all_templates(templates_dir)
    print(f"      → {len(templates_metadata)} template(s) analyzed ({time.time() - t0:.2f}s)")

    # ── Step 4: Select Template ───────────────────────────────────────────────
    print("\n[4/5] Scoring and selecting best template...")
    t0 = time.time()
    from template_selector import select_best_template
    best_template, all_scores = select_best_template(templates_metadata, slides_data, output_dir)
    print(f"      → Selected: {best_template['template_name']} (score: {best_template['total_score']})")
    print(f"      → ({time.time() - t0:.2f}s)")

    # ── Step 5: Generate ──────────────────────────────────────────────────────
    print("\n[5/5] Generating final presentation...")
    t0 = time.time()
    from generator import generate_presentation
    output_path = generate_presentation(
        classified_slides,
        best_template["template_path"],
        output_dir,
    )
    print(f"      → Saved: {output_path} ({time.time() - t0:.2f}s)")

    print("\n" + "=" * 60)
    print("  ✅ Pipeline complete!")
    print(f"  Output: {output_path}")
    print("=" * 60 + "\n")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="PPT Template Transfer AI — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py input/sample.pptx
  python main.py input/sample.pptx --templates templates/ --output output/
        """,
    )
    parser.add_argument(
        "input_pptx",
        help="Path to the source PPTX file to process.",
    )
    parser.add_argument(
        "--templates",
        default="templates",
        help="Directory containing template PPTX files (default: templates/).",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Directory for output files (default: output/).",
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_pptx):
        print(f"Error: Input file not found: {args.input_pptx}")
        sys.exit(1)

    run_pipeline(
        input_pptx=args.input_pptx,
        templates_dir=args.templates,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
