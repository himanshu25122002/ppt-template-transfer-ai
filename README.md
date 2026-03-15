# PPT Template Transfer AI

An automated pipeline that extracts content from a PowerPoint presentation,
scores a library of templates, and rebuilds the deck using the best-matched template.
Powered by Google Gemini for slide classification.

---

## Architecture

```
Input PPTX
    │
    ▼
extractor.py          → Extracts structured JSON content from each slide
    │
    ▼
ai_slide_classifier.py → Gemini classifies each slide (Title / Bullet / Content / Two Column)
    │
    ▼
template_analyzer.py  → Scans templates/ and builds metadata for each PPTX template
    │
    ▼
template_selector.py  → Scores templates against content profile, selects the best
    │
    ▼
generator.py          → Rebuilds presentation using the selected template
    │
    ▼
output/final_presentation.pptx
```

---

## Project Structure

```
project/
├── templates/           # Add any number of .pptx templates here
├── input/               # Place input PPTX files here (CLI mode)
├── output/              # All generated files written here
├── extractor.py
├── template_analyzer.py
├── template_selector.py
├── generator.py
├── ai_slide_classifier.py
├── streamlit_app.py
├── main.py
├── requirements.txt
└── README.md
```

---

## Template Scoring Logic

Each template is scored out of ~100 points across six factors:

| Factor                  | Max Points | Notes                                    |
|-------------------------|-----------|------------------------------------------|
| Title slide support     | 25        | Template has a title/subtitle layout     |
| Bullet/content support  | 25        | Template has a content placeholder       |
| Layout flexibility      | 20        | Normalized count of available layouts    |
| Two-column support      | 10        | Template has a two-content layout        |
| Subtitle support        | 10        | Template has subtitle placeholder        |
| Placeholder diversity   | 5         | Variety of placeholder types available   |
| Table support           | 5         | Template contains a table layout         |

The template with the highest score is automatically selected.

---

## Gemini AI Usage

- **Model:** `gemini-1.5-flash`
- **Purpose:** Classifies each slide into one of four types:
  - `Title Slide` — Cover or section heading with minimal body
  - `Bullet Slide` — Primarily bullet points or lists
  - `Content Slide` — Paragraphs or detailed text
  - `Two Column Slide` — Side-by-side content layout
- **Fallback:** If Gemini is unavailable, a rule-based heuristic classifier is used automatically.
- **Rate limiting:** A 0.5s delay between API calls prevents quota exhaustion.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Gemini API key (optional but recommended)

```bash
# Linux / macOS
export GEMINI_API_KEY="your_api_key_here"

# Windows (Command Prompt)
set GEMINI_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"
```

Get a free API key at: [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 3. Add templates

Place one or more `.pptx` template files into the `templates/` directory.
The system supports unlimited templates — just drop them in.

---

## Running

### CLI Mode

```bash
python main.py input/sample.pptx
```

With custom directories:

```bash
python main.py input/sample.pptx --templates templates/ --output output/
```

### Streamlit UI

```bash
streamlit run streamlit_app.py
```

Open your browser at `[localhost](http://localhost:8501)`.

---

## Output Files

| File                          | Description                              |
|-------------------------------|------------------------------------------|
| `output/extracted_content.json`  | Structured slide content from input PPTX |
| `output/classified_slides.json`  | Slides with Gemini classification labels |
| `output/selected_template.txt`   | Path to the winning template             |
| `output/final_presentation.pptx` | The rebuilt presentation                 |

---

## Adding Templates

Simply copy any `.pptx` file into the `templates/` folder.
Both the CLI and Streamlit UI detect templates automatically at runtime —
no configuration changes needed.

---

## Notes

- The generator removes blank placeholder slides from the template before building.
- Layout matching uses keyword search against layout names (e.g., "Title and Content").
  If your templates use non-English layout names, update `LAYOUT_PREFERENCE_MAP` in `generator.py`.
- For large presentations, Gemini API calls are rate-limited to 0.5s per slide.
  Adjust `time.sleep()` in `ai_slide_classifier.py` if needed.

## Running Example

Example command:

python main.py input/sample.pptx

Example Output:

output/final_presentation.pptx
