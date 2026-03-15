"""
template_analyzer.py
Scans all PPTX templates in the templates/ folder and returns
structured metadata about layouts, placeholders, and capabilities.
"""

import os
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.text import PP_ALIGN


def analyze_layout(layout) -> dict:
    """Inspect a single slide layout for placeholder types and capabilities."""
    layout_info = {
        "layout_name": layout.name,
        "has_title": False,
        "has_content": False,
        "has_subtitle": False,
        "has_two_columns": False,
        "has_table": False,
        "placeholder_count": 0,
        "placeholder_types": [],
    }

    placeholders = list(layout.placeholders)
    layout_info["placeholder_count"] = len(placeholders)

    content_count = 0
    for ph in placeholders:
        try:
            ph_type = str(ph.placeholder_format.type).replace("PP_PLACEHOLDER.", "").lower()
        except Exception:
            ph_type = "unknown"

        layout_info["placeholder_types"].append({
            "idx": ph.placeholder_format.idx,
            "type": ph_type,
            "name": ph.name,
        })

        if ph_type in ("title", "center_title"):
            layout_info["has_title"] = True
        elif ph_type == "subtitle":
            layout_info["has_subtitle"] = True
        elif ph_type in ("body", "object", "text"):
            content_count += 1

    # Heuristic: two separate content areas side-by-side → two-column layout
    if content_count >= 2:
        layout_info["has_two_columns"] = True

    if content_count >= 1:
        layout_info["has_content"] = True

    # Check for table placeholders in layout shapes
    for shape in layout.shapes:
        if shape.shape_type == 19:  # MSO_SHAPE_TYPE.TABLE
            layout_info["has_table"] = True

    return layout_info


def analyze_template(template_path: str) -> dict:
    """
    Analyze a single PPTX template file.

    Returns:
        Dict containing template metadata and layout capabilities.
    """
    prs = Presentation(template_path)
    template_name = os.path.basename(template_path)

    metadata = {
        "template_name": template_name,
        "template_path": template_path,
        "slide_width": prs.slide_width.inches,
        "slide_height": prs.slide_height.inches,
        "layout_count": len(prs.slide_layouts),
        "layouts": [],
        "supports_title_slide": False,
        "supports_bullet_slide": False,
        "supports_two_column": False,
        "supports_table": False,
        "total_placeholder_types": set(),
    }

    for layout in prs.slide_layouts:
        layout_info = analyze_layout(layout)
        metadata["layouts"].append(layout_info)

        if layout_info["has_title"] and layout_info["has_subtitle"]:
            metadata["supports_title_slide"] = True
        if layout_info["has_title"] and layout_info["has_content"]:
            metadata["supports_bullet_slide"] = True
        if layout_info["has_two_columns"]:
            metadata["supports_two_column"] = True
        if layout_info["has_table"]:
            metadata["supports_table"] = True

        for ph in layout_info["placeholder_types"]:
            metadata["total_placeholder_types"].add(ph["type"])

    # Convert set to list for JSON serialization
    metadata["total_placeholder_types"] = list(metadata["total_placeholder_types"])

    return metadata


def analyze_all_templates(templates_dir: str = "templates") -> list[dict]:
    """
    Scan all PPTX files in the templates directory and analyze each.

    Args:
        templates_dir: Folder containing template PPTX files.

    Returns:
        List of template metadata dicts.
    """
    if not os.path.exists(templates_dir):
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    template_files = [
        os.path.join(templates_dir, f)
        for f in os.listdir(templates_dir)
        if f.lower().endswith(".pptx")
    ]

    if not template_files:
        raise ValueError(f"No PPTX templates found in: {templates_dir}")

    print(f"[TemplateAnalyzer] Found {len(template_files)} template(s).")
    results = []
    for path in template_files:
        print(f"  → Analyzing: {os.path.basename(path)}")
        metadata = analyze_template(path)
        results.append(metadata)

    return results


if __name__ == "__main__":
    templates = analyze_all_templates()
    for t in templates:
        print(f"\nTemplate: {t['template_name']}")
        print(f"  Layouts: {t['layout_count']}")
        print(f"  Title slide: {t['supports_title_slide']}")
        print(f"  Bullet slide: {t['supports_bullet_slide']}")
        print(f"  Two-column: {t['supports_two_column']}")
        print(f"  Table: {t['supports_table']}")
