# CV Generator

CV Generator is a Python app that scrapes a job posting, combines it with your skills profile, and uses Groq AI to produce a tailored, ATS-friendly CV as a PDF. It includes both a CLI workflow and a small FastAPI-powered web UI.

## Features
- Scrapes job posting text from a URL.
- Tailors a CV using Groq’s Chat Completions API.
- Produces a clean, readable PDF with a job-title-based filename.
- CLI for quick generation.
- Web UI with job preview and one-click PDF download.

## Project Layout
- `generate_cv.py`: CLI entry point.
- `cv_generator/`: core services (scraper, Groq generation, PDF rendering).
- `web/`: static UI (HTML/CSS/JS).
- `scripts/install_deps.sh`: installs Python dependencies.
- `scripts/run_dev.sh`: runs the API + web UI locally.
- `my-skills.md`: sample skills file.
- `output/`: generated PDFs are saved here by default.

## Requirements
- Python 3
- A Groq API key

## Install
1. (Optional) Create and activate a virtual environment.
2. Install dependencies:

```bash
./scripts/install_deps.sh
```

3. Create a `.env` file in the repo root:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

## Run (CLI)
```bash
python generate_cv.py <job_url> [skills_file] [output_dir]
```

Example:
```bash
python generate_cv.py https://example.com/job my-skills.md ./output
```

Notes:
- The skills file should be plain text (e.g., `.md`, `.txt`, `.json`). Non-text formats (like PDF/DOCX) are not parsed.
- Output defaults to `./output` if not provided.

## Run (Web App)
Start the API + UI:

```bash
./scripts/run_dev.sh
```

Then open:
- `http://localhost:8000`

The UI lets you preview the job posting text and download the generated PDF.

## API Endpoints
- `POST /api/preview` — returns extracted job posting text.
- `POST /api/generate` — generates a CV PDF and returns a download URL.
- `GET /api/download/{filename}` — downloads the PDF.

## Configuration
- `GROQ_API_KEY`: required for generation.
- `ALLOWED_ORIGINS` (optional): comma-separated list for CORS in `api_prod`.

