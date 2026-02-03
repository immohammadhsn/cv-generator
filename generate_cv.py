#!/usr/bin/env python3
import sys
import os
import requests
from bs4 import BeautifulSoup
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

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
    
    prompt = f"""You are an expert CV writer and LaTeX specialist. Create a professional, ATS-friendly CV in LaTeX format.

JOB DESCRIPTION:
{job_desc[:4000]}

CANDIDATE INFORMATION:
{skills}

INSTRUCTIONS:
1. Analyze the job description and identify key requirements
2. Tailor the CV to highlight relevant skills and experience from the candidate's information
3. Use a clean, professional LaTeX template (moderncv or similar)
4. Include these sections: Contact Info, Professional Summary, Skills, Work Experience, Education, Projects
5. Emphasize achievements that match job requirements
6. Use action verbs and quantifiable results
7. Keep it to 1-2 pages maximum
8. Make it ATS-friendly (avoid complex formatting, use standard section names)

OUTPUT REQUIREMENTS:
- Return ONLY the complete LaTeX code
- Start with \\documentclass and end with \\end{{document}}
- Use the moderncv package or a clean article-based template
- Include all necessary packages
- Ensure the document compiles without errors
- Do NOT include any explanations or markdown, ONLY LaTeX code"""

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
                        'content': 'You are an expert CV writer specializing in LaTeX document generation. You create professional, ATS-friendly CVs tailored to job descriptions.'
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
        
        latex_content = result['choices'][0]['message']['content']
        
        # Clean up the response - remove markdown code blocks if present
        latex_content = latex_content.replace('```latex', '').replace('```', '').strip()
        
        print(f"Generated {len(latex_content)} characters of LaTeX code")
        return latex_content
        
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

def compile_latex(latex_content, output_dir):
    """Compile LaTeX to PDF"""
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        tex_file = os.path.join(output_dir, "cv.tex")
        pdf_file = os.path.join(output_dir, "cv.pdf")
        
        # Write LaTeX content to file
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"Saved LaTeX file: {tex_file}")
        
        # Compile LaTeX to PDF
        print("Compiling LaTeX to PDF...")
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Run twice to resolve references
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if os.path.exists(pdf_file):
            print(f"✓ PDF successfully generated: {pdf_file}")
            
            # Clean up auxiliary files
            for ext in ['.aux', '.log', '.out']:
                aux_file = os.path.join(output_dir, f"cv{ext}")
                if os.path.exists(aux_file):
                    os.remove(aux_file)
        else:
            print("Error: PDF compilation failed")
            print("LaTeX output:", result.stdout)
            print("LaTeX errors:", result.stderr)
            sys.exit(1)
            
    except subprocess.TimeoutExpired:
        print("Error: LaTeX compilation timed out")
        sys.exit(1)
    except Exception as e:
        print(f"Error compiling LaTeX: {e}")
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
    latex_cv = generate_cv_with_groq(job_desc, skills)
    
    # Step 4: Compile to PDF
    compile_latex(latex_cv, output_dir)
    
    print("=" * 60)
    print("✓ CV GENERATION COMPLETE!")
    print(f"✓ LaTeX file: {output_dir}/cv.tex")
    print(f"✓ PDF file: {output_dir}/cv.pdf")
    print("=" * 60)

if __name__ == "__main__":
    main()
