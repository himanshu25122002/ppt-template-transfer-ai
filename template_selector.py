"""
template_selector.py
Scores each analyzed template against the extracted slide content
and selects the best-matching template.
Saves the result to output/selected_template.txt.
"""

import os
import json
from typing import Optional


def compute_content_profile(slides_data: list[dict]) -> dict:
    """
    Derive a content requirement profile from the extracted slides.

    Returns a dict of required features and their weights.
    """
    profile = {
        "needs_title_slide": False,
        "needs_bullet_slide": False,
        "needs_two_column": False,
        "needs_table": False,
        "total_slides": len(slides_data),
        "avg_bullets_per_slide": 0.0,
        "has_body_content": False,
    }

    total_bullets = 0
    for slide in slides_data:
        bullets = slide.get("bullets", [])
        total_bullets += len(bullets)

        if slide.get("slide_number") == 1:
            profile["needs_title_slide"] = True

        if bullets:
            profile["needs_bullet_slide"] = True

        if slide.get("body"):
            profile["has_body_content"] = True

    if len(slides_data) > 0:
        profile["avg_bullets_per_slide"] = total_bullets / len(slides_data)

    return profile


def score_template(template_metadata: dict, content_profile: dict) -> dict:
    """
    Score a template against the content profile.

    Scoring factors (max 100 points):
        - Title slide support:       25 pts
        - Bullet/content support:    25 pts
        - Layout flexibility:        20 pts  (more layouts = better)
        - Two-column support:        10 pts
        - Table support:              5 pts
        - Subtitle support:          10 pts
        - Placeholder diversity:      5 pts
    """
    score = 0
    breakdown = {}

    # Title slide support
    if template_metadata.get("supports_title_slide"):
        pts = 25
        score += pts
        breakdown["title_slide_support"] = pts
    else:
        breakdown["title_slide_support"] = 0

    # Bullet / content placeholder support
    if template_metadata.get("supports_bullet_slide") and content_profile.get("needs_bullet_slide"):
        pts = 25
        score += pts
        breakdown["bullet_slide_support"] = pts
    elif template_metadata.get("supports_bullet_slide"):
        pts = 15
        score += pts
        breakdown["bullet_slide_support"] = pts
    else:
        breakdown["bullet_slide_support"] = 0

    # Layout flexibility — normalized to 20 pts, cap at 10 layouts
    layout_count = template_metadata.get("layout_count", 0)
    layout_score = min(layout_count / 10.0, 1.0) * 20
    score += layout_score
    breakdown["layout_flexibility"] = round(layout_score, 2)

    # Two-column layout
    if template_metadata.get("supports_two_column") and content_profile.get("needs_two_column"):
        pts = 10
        score += pts
        breakdown["two_column_support"] = pts
    elif template_metadata.get("supports_two_column"):
        pts = 5
        score += pts
        breakdown["two_column_support"] = pts
    else:
        breakdown["two_column_support"] = 0

    # Table support
    if template_metadata.get("supports_table") and content_profile.get("needs_table"):
        pts = 5
        score += pts
        breakdown["table_support"] = pts
    else:
        breakdown["table_support"] = 0

    # Subtitle support (good for title slides)
    subtitle_layouts = [
        l for l in template_metadata.get("layouts", [])
        if l.get("has_subtitle")
    ]
    if subtitle_layouts and content_profile.get("needs_title_slide"):
        pts = 10
        score += pts
        breakdown["subtitle_support"] = pts
    else:
        breakdown["subtitle_support"] = 0

    # Placeholder type diversity
    ph_types = template_metadata.get("total_placeholder_types", [])
    diversity_score = min(len(ph_types) / 5.0, 1.0) * 5
    score += diversity_score
    breakdown["placeholder_diversity"] = round(diversity_score, 2)

    return {
        "template_name": template_metadata["template_name"],
        "template_path": template_metadata["template_path"],
        "total_score": round(score, 2),
        "breakdown": breakdown,
    }


def select_best_template(
    templates_metadata: list[dict],
    slides_data: list[dict],
    output_dir: str = "output",
) -> dict:
    """
    Score all templates and return the one with the highest score.

    Also writes the selected template name to output/selected_template.txt.

    Args:
        templates_metadata: List of analyzed template metadata dicts.
        slides_data: Extracted slides content list.
        output_dir: Directory to write selected_template.txt.

    Returns:
        The scoring result dict for the best template.
    """
    os.makedirs(output_dir, exist_ok=True)

    content_profile = compute_content_profile(slides_data)
    scores = [score_template(t, content_profile) for t in templates_metadata]

    # Sort by descending score
    scores.sort(key=lambda x: x["total_score"], reverse=True)

    best = scores[0]

    output_path = os.path.join(output_dir, "selected_template.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(best["template_path"])

    print(f"\n[TemplateSelector] Scores:")
    for s in scores:
        print(f"  {s['template_name']}: {s['total_score']}")
    print(f"\n[TemplateSelector] Best template → {best['template_name']} (score: {best['total_score']})")

    return best, scores


if __name__ == "__main__":
    import json
    with open("output/extracted_content.json") as f:
        slides = json.load(f)
    from template_analyzer import analyze_all_templates
    templates = analyze_all_templates()
    best, all_scores = select_best_template(templates, slides)
    print(json.dumps(best, indent=2))
