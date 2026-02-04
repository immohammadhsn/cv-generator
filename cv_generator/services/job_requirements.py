import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


def extract_job_requirements(job_text: str) -> tuple[str, list[str]]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    prompt = f"""You are a hiring manager and recruiter. Extract the core job requirements from the posting below.

JOB POSTING:
{job_text[:4000]}

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON.
- Use this exact structure:
{{
  "job_title": "Short job title",
  "requirements": ["Short requirement 1", "Short requirement 2", "Short requirement 3"]
}}
- The job_title should be 3 to 10 words.
- Each requirement should be concise (6-16 words).
- Prefer must-have qualifications, skills, responsibilities, and tools.
- Keep 6 to 12 items. No extra keys.
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You extract job requirements from job postings. "
                            "Always respond with valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 800,
            },
            timeout=60,
        )

        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        requirements = parsed.get("requirements", [])
        job_title = parsed.get("job_title")
        job_title = job_title.strip() if isinstance(job_title, str) else ""
        cleaned_requirements = [
            req for req in requirements if isinstance(req, str) and req.strip()
        ]
        return job_title, cleaned_requirements
    except Exception as exc:
        print(f"Error extracting job requirements: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            print(f"Response: {exc.response.text}")
        sys.exit(1)
