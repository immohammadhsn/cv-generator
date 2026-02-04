from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, AnyHttpUrl, ValidationError

from .orchestrator import generate_cv
from .services.job_scraper import scrape_job
from .services.job_requirements import extract_job_requirements

APP_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = APP_ROOT / "web"
OUTPUT_DIR = APP_ROOT / "output"

logger = logging.getLogger("cv_generator.api")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


class JobRequest(BaseModel):
    job_url: AnyHttpUrl

    @classmethod
    def as_form(cls, job_url: str = Form(...)) -> "JobRequest":
        try:
            return cls(job_url=job_url)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _load_allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="CV Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_load_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    index_path = WEB_ROOT / "index.html"
    html = index_path.read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.get("/assets/{asset_name}")
def assets(asset_name: str) -> FileResponse:
    asset_path = WEB_ROOT / asset_name
    return FileResponse(asset_path)


@app.post("/api/generate")
def generate(
    job_request: JobRequest = Depends(JobRequest.as_form),
    skills_file: UploadFile = File(...),
) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename = skills_file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx", ".md", ".json", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use PDF, DOCX, MD, JSON, or TXT.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(skills_file.file.read())
        tmp_path = tmp_file.name

    job_title, pdf_path = generate_cv(job_request.job_url, tmp_path, str(OUTPUT_DIR))

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF generation failed.")

    pdf_filename = os.path.basename(pdf_path)
    return {
        "job_title": job_title,
        "pdf_filename": pdf_filename,
        "download_url": f"/api/download/{pdf_filename}",
    }


@app.get("/api/download/{filename}")
def download(filename: str) -> FileResponse:
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


@app.head("/api/download/{filename}")
def download_head(filename: str) -> FileResponse:
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


@app.post("/api/preview")
def preview(job_request: JobRequest = Depends(JobRequest.as_form)) -> dict:
    try:
        job_text = scrape_job(job_request.job_url)
        job_title, requirements = extract_job_requirements(job_text)
        return {"job_title": job_title, "requirements": requirements}
    except SystemExit:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch job offer preview. The URL may require login or block scraping.",
        )


@app.get("/api/dev-assets-hash")
def dev_assets_hash() -> dict:
    assets = [
        WEB_ROOT / "index.html",
        WEB_ROOT / "styles.css",
        WEB_ROOT / "app.js",
    ]
    hasher = hashlib.sha256()
    for asset in assets:
        if asset.exists():
            hasher.update(str(asset.stat().st_mtime).encode("utf-8"))
    return {"hash": hasher.hexdigest()}
