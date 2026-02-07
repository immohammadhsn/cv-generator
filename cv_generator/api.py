from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
import hashlib

from fastapi.responses import FileResponse, HTMLResponse

from .orchestrator import generate_cv
from .services.job_scraper import scrape_job
from .services.job_requirements import extract_job_requirements


APP_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = APP_ROOT / "web"
OUTPUT_DIR = APP_ROOT / "output"

app = FastAPI(title="CV Generator API")

def _assets_version() -> str:
    assets = [
        WEB_ROOT / "styles.css",
        WEB_ROOT / "app.js",
    ]
    hasher = hashlib.sha256()
    for asset in assets:
        if asset.exists():
            hasher.update(str(asset.stat().st_mtime).encode("utf-8"))
    return hasher.hexdigest()


def _inject_asset_version(html: str) -> str:
    version = _assets_version()
    html = html.replace("/assets/styles.css", f"/assets/styles.css?v={version}")
    html = html.replace("/assets/app.js", f"/assets/app.js?v={version}")
    return html


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    index_path = WEB_ROOT / "index.html"
    html = index_path.read_text(encoding="utf-8")
    return HTMLResponse(content=_inject_asset_version(html))


@app.get("/assets/{asset_name}")
def assets(asset_name: str) -> FileResponse:
    asset_path = WEB_ROOT / asset_name
    return FileResponse(asset_path)


@app.post("/api/generate")
def generate(
    job_url: str = Form(...),
    skills_file: UploadFile = File(...),
) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(skills_file.filename or "skills").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(skills_file.file.read())
        tmp_path = tmp_file.name

    job_title, pdf_path = generate_cv(job_url, tmp_path, str(OUTPUT_DIR))

    if not os.path.exists(pdf_path):
        raise RuntimeError("PDF generation failed.")

    filename = os.path.basename(pdf_path)
    return {
        "job_title": job_title,
        "pdf_filename": filename,
        "download_url": f"/api/download/{filename}",
    }


@app.get("/api/download/{filename}")
def download(filename: str) -> FileResponse:
    file_path = OUTPUT_DIR / filename
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


@app.head("/api/download/{filename}")
def download_head(filename: str) -> FileResponse:
    file_path = OUTPUT_DIR / filename
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


@app.post("/api/preview")
def preview(job_url: str = Form(...)) -> dict:
    try:
        job_text = scrape_job(job_url)
        job_title, requirements = extract_job_requirements(job_text)
        return {"job_title": job_title, "requirements": requirements}
    except SystemExit:
        from fastapi import HTTPException

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
