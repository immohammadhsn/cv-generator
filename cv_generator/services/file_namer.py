
def generate_filename(job_title: str) -> str:
    """Generate a safe filename from a job title"""
    # Clean the job title for use in filename
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in job_title)
    safe_title = safe_title.strip().replace(' ', '_')[:50]  # Limit length
    return f"CV_{safe_title}.pdf"
