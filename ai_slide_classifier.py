"""
ai_slide_classifier.py
Uses Google Gemini (gemini-1.5-flash) to classify each slide's
content type: Title Slide, Bullet Slide, Content Slide, Two Column Slide.
"""

import os
import json
import time
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


VALID_LABELS = {
    "Title Slide",
    "Bullet Slide",
    "Content Slide",
    "Two Column Slide",
}

CLASSIFICATION_PROMPT = """You are an expert presentation designer.

Analyze the following slide content and classify it into exactly ONE of these categories:
- Title Slide: A cover or section heading slide with minimal body text
- Bullet Slide: A slide primarily containing bullet points or lists
- Content Slide: A slide with paragraphs, descriptions, or detailed text content
- Two Column Slide: A slide that should be presented in two side-by-side columns

Slide content:
Title: {title}
Body: {body}
Bullets: {bullets}

Respond with ONLY the classification label (e.g., "Bullet Slide"). No explanation."""


def get_gemini_client() -> Optional[object]:
    """Initialize and return the Gemini generative model."""
    if not GEMINI_AVAILABLE:
        print("[Gemini] google-generativeai package not installed.")
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Gemini] GEMINI_API_KEY environment variable not set.")
        return None

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def classify_slide_with_gemini(model, slide: dict) -> str:
    """
    Send a single slide's content to Gemini for classification.

    Falls back to heuristic classification if Gemini is unavailable.
    """
    title = slide.get("title") or ""
    body = " | ".join(slide.get("body", []))
    bullets = " | ".join(slide.get("bullets", []))

    prompt = CLASSIFICATION_PROMPT.format(
        title=title,
        body=body[:500],   # Truncate to avoid token overflow
        bullets=bullets[:500],
    )

    try:
        response = model.generate_content(prompt)
        label = response.text.strip().strip('"').strip("'")

        # Validate the returned label
        if label in VALID_LABELS:
            return label

        # Partial match fallback
        for valid in VALID_LABELS:
            if valid.lower() in label.lower():
                return valid

        return "Content Slide"

    except Exception as e:
        print(f"  [Gemini] Error classifying slide {slide.get('slide_number')}: {e}")
        return heuristic_classify(slide)


def heuristic_classify(slide: dict) -> str:
    """
    Fallback rule-based slide classification when Gemini is unavailable.
    """
    slide_number = slide.get("slide_number", 1)
    title = slide.get("title") or ""
    body = slide.get("body", [])
    bullets = slide.get("bullets", [])

    if slide_number == 1 and not bullets:
        return "Title Slide"
    if len(bullets) >= 3:
        return "Bullet Slide"
    if len(body) >= 2 and len(bullets) < 2:
        return "Content Slide"
    return "Content Slide"


def classify_slides(
    slides_data: list[dict],
    output_dir: str = "output",
) -> list[dict]:
    """
    Classify all slides using Gemini with heuristic fallback.

    Args:
        slides_data: List of extracted slide dicts.
        output_dir: Directory for output JSON.

    Returns:
        List of slides with added 'classification' field.
    """
    os.makedirs(output_dir, exist_ok=True)

    model = get_gemini_client()
    use_gemini = model is not None

    if use_gemini:
        print(f"[Classifier] Using Gemini gemini-1.5-flash for classification.")
    else:
        print("[Classifier] Gemini unavailable — using heuristic classifier.")

    classified = []
    for slide in slides_data:
        slide_num = slide.get("slide_number")

        if use_gemini:
            label = classify_slide_with_gemini(model, slide)
            # Rate limit: avoid quota exhaustion
            time.sleep(0.5)
        else:
            label = heuristic_classify(slide)

        slide_copy = dict(slide)
        slide_copy["classification"] = label
        classified.append(slide_copy)
        print(f"  Slide {slide_num}: {label}")

    output_path = os.path.join(output_dir, "classified_slides.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(classified, f, indent=2, ensure_ascii=False)

    print(f"[Classifier] Saved → {output_path}")
    return classified


def check_gemini_status() -> dict:
    """
    Return a status dict indicating whether Gemini is configured and reachable.
    """
    status = {
        "package_installed": GEMINI_AVAILABLE,
        "api_key_set": bool(os.environ.get("GEMINI_API_KEY")),
        "ready": False,
        "message": "",
    }

    if not status["package_installed"]:
        status["message"] = "google-generativeai not installed"
    elif not status["api_key_set"]:
        status["message"] = "GEMINI_API_KEY not set"
    else:
        status["ready"] = True
        status["message"] = "Gemini ready"

    return status


if __name__ == "__main__":
    with open("output/extracted_content.json") as f:
        slides = json.load(f)
    classify_slides(slides)
