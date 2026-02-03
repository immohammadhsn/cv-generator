import json
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def generate_cv_with_groq(job_desc: str, skills: str) -> dict:
    """Generate CV using Groq API"""
    api_key = os.getenv('GROQ_API_KEY')

    if not api_key:
        print("Error: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    print("Generating CV with Groq AI...")

    prompt = f"""You are an expert CV writer. Analyze the job description carefully and create a TAILORED CV that highlights the candidate's most relevant skills and experience for THIS SPECIFIC JOB.

JOB DESCRIPTION:
{job_desc[:4000]}

CANDIDATE INFORMATION:
{skills}

CRITICAL INSTRUCTIONS:
1. READ the job description carefully and identify the TOP 5 key requirements
2. REORDER and EMPHASIZE the candidate's experience to match those requirements
3. ONLY include skills that are relevant to this job (not every skill the candidate has)
4. REWRITE achievement bullet points to use similar language and keywords from the job posting
5. Put the most relevant work experience FIRST, even if it's not chronological
6. If the job emphasizes certain technologies or skills, make sure they appear prominently
7. The professional summary must directly address what this specific job is looking for
8. Each achievement should tie back to a requirement in the job description

EXAMPLE OF GOOD TAILORING:
- If job wants "Python" and "machine learning", put those skills at the TOP of skills list
- If job wants "team leadership", emphasize leadership achievements in experience
- If job mentions "microservices", use that exact term in relevant experience bullets
- Mirror the job posting's language and terminology

OUTPUT REQUIREMENTS:
Return ONLY valid JSON in this exact structure (no markdown, no explanations):
{{
  "job_title": "Extract the job title from the job description",
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+20 123 456 7890",
  "location": "City, Country",
  "linkedin": "linkedin.com/in/profile",
  "github": "github.com/username",
  "summary": "2-3 sentence professional summary that directly addresses THIS job's requirements using keywords from the posting",
  "skills": ["List ONLY the 8-12 most relevant skills for THIS job, ordered by relevance"],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "period": "Month Year - Month Year",
      "achievements": ["Rewritten achievement that matches job requirements", "Another achievement using job posting keywords"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "University Name",
      "year": "Year"
    }}
  ],
  "projects": [
    {{
      "name": "Project Name (only include if relevant to THIS job)",
      "description": "Description highlighting relevant technologies mentioned in job posting"
    }}
  ]
}}

REMEMBER: This CV should look DIFFERENT for each job posting. Tailor everything!"""

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {
                        'role': 'system',
                        'content': (
                            'You are an expert CV writer. You create professional, '
                            'ATS-friendly CVs tailored to job descriptions. '
                            'Always respond with valid JSON only.'
                        )
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 4000
            },
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        content = result['choices'][0]['message']['content']

        # Clean up the response - remove markdown code blocks if present
        content = content.replace('```json', '').replace('```', '').strip()

        # Parse JSON
        cv_data = json.loads(content)

        print("Generated CV data successfully")
        return cv_data

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)
