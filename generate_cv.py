#!/usr/bin/env python3
import sys
import os
import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas

# Load environment variables
load_dotenv()

def scrape_job(url):
    """Scrape job posting from URL"""
    try:
        print(f"Scraping job posting from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        print(f"Successfully scraped {len(text)} characters")
        return text
    
    except Exception as e:
        print(f"Error scraping job posting: {e}")
        sys.exit(1)

def load_skills(filepath):
    """Load skills file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Loaded skills file: {filepath}")
        return content
    except Exception as e:
        print(f"Error loading skills file: {e}")
        sys.exit(1)

def generate_cv_with_groq(job_desc, skills):
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
                        'content': 'You are an expert CV writer. You create professional, ATS-friendly CVs tailored to job descriptions. Always respond with valid JSON only.'
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
        
        print(f"Generated CV data successfully")
        return cv_data
        
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

def create_pdf(cv_data, output_dir):
    """Create PDF from CV data"""
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        pdf_file = os.path.join(output_dir, "cv.pdf")
        
        print("Creating PDF...")
        
        # Create PDF
        doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                              topMargin=0.5*inch, bottomMargin=0.5*inch,
                              leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        # Container for PDF elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2C3E50',
            spaceAfter=6,
            alignment=TA_CENTER
        )
        
        contact_style = ParagraphStyle(
            'Contact',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#2C3E50',
            spaceAfter=6,
            spaceBefore=12,
            borderWidth=1,
            borderColor='#2C3E50',
            borderPadding=5
        )
        
        body_style = styles['Normal']
        body_style.fontSize = 10
        body_style.spaceAfter = 6
        
        # Add name
        elements.append(Paragraph(cv_data['name'], title_style))
        
        # Add contact info
        contact_info = f"{cv_data['email']} | {cv_data['phone']} | {cv_data['location']}"
        if cv_data.get('linkedin'):
            contact_info += f"<br/>{cv_data['linkedin']}"
        if cv_data.get('github'):
            contact_info += f" | {cv_data['github']}"
        elements.append(Paragraph(contact_info, contact_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Professional Summary
        elements.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
        elements.append(Paragraph(cv_data['summary'], body_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Skills
        if cv_data.get('skills'):
            elements.append(Paragraph("SKILLS", heading_style))
            skills_text = " • ".join(cv_data['skills'])
            elements.append(Paragraph(skills_text, body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        # Work Experience
        if cv_data.get('experience'):
            elements.append(Paragraph("WORK EXPERIENCE", heading_style))
            for exp in cv_data['experience']:
                job_title = f"<b>{exp['title']}</b> - {exp['company']}"
                elements.append(Paragraph(job_title, body_style))
                elements.append(Paragraph(f"<i>{exp['period']}</i>", body_style))
                for achievement in exp['achievements']:
                    elements.append(Paragraph(f"• {achievement}", body_style))
                elements.append(Spacer(1, 0.1*inch))
        
        # Education
        if cv_data.get('education'):
            elements.append(Paragraph("EDUCATION", heading_style))
            for edu in cv_data['education']:
                edu_text = f"<b>{edu['degree']}</b> - {edu['institution']}, {edu['year']}"
                elements.append(Paragraph(edu_text, body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        # Projects
        if cv_data.get('projects'):
            elements.append(Paragraph("PROJECTS", heading_style))
            for project in cv_data['projects']:
                project_text = f"<b>{project['name']}</b>: {project['description']}"
                elements.append(Paragraph(project_text, body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(elements)
        
        print(f"✓ PDF successfully generated: {pdf_file}")
        return pdf_file
        
    except Exception as e:
        print(f"Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_cv.py <job_url> [skills_file] [output_dir]")
        print("Example: python generate_cv.py https://example.com/job my-skills.md ./output")
        sys.exit(1)
    
    job_url = sys.argv[1]
    skills_file = sys.argv[2] if len(sys.argv) > 2 else "my-skills.md"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "./output"
    
    print("=" * 60)
    print("CV GENERATOR - Powered by Groq AI")
    print("=" * 60)
    
    # Step 1: Scrape job posting
    job_desc = scrape_job(job_url)
    
    # Step 2: Load your skills
    skills = load_skills(skills_file)
    
    # Step 3: Generate CV with AI
    cv_data = generate_cv_with_groq(job_desc, skills)
    
    # Step 4: Create PDF
    pdf_path = create_pdf(cv_data, output_dir)
    
    print("=" * 60)
    print("✓ CV GENERATION COMPLETE!")
    print(f"✓ PDF file: {pdf_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()