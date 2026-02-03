from .services.job_scraper import scrape_job
from .services.skills_loader import load_skills
from .services.cv_generation import generate_cv_with_groq
from .services.pdf_renderer import create_pdf


def generate_cv(job_url: str, skills_file: str, output_dir: str) -> str:
    """Run the end-to-end CV generation flow."""
    # Step 1: Scrape job posting
    job_desc = scrape_job(job_url)

    # Step 2: Load your skills
    skills = load_skills(skills_file)

    # Step 3: Generate CV with AI
    cv_data = generate_cv_with_groq(job_desc, skills)

    # Step 4: Create PDF with job title in filename
    job_title = cv_data.get('job_title', 'Position')
    pdf_path = create_pdf(cv_data, output_dir, job_title)

    return job_title, pdf_path
